from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from test_case_agent.coverage_graph import (
    CoverageCase,
    CoverageGap,
    CoverageGraph,
    CoverageGraphError,
    CoverageObligation,
    CoverageProperty,
    PropertyDerivation,
    validate_coverage_graph,
)
from test_case_agent.test_design import (
    DesignContext,
    DesignError,
    validate_design_context_for_graph,
)


ARTIFACT_SCHEMA_VERSION = 1

_SHA256 = re.compile(r"[0-9a-f]{64}")
_TYPED_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")
_ARTIFACT_KINDS = {
    "coverage-derivations",
    "coverage-graph",
    "coverage-design-context",
}
_ENVELOPE_FIELDS = {
    "schema_version",
    "artifact_kind",
    "payload_sha256",
    "payload",
}


class CoverageIoError(ValueError):
    """A persisted coverage artifact violates its closed, digest-bound contract."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return the only byte representation used for artifact payload digests."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CoverageIoError("invalid-json-value", str(exc)) from exc


def payload_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _duplicate_rejecting_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoverageIoError("duplicate-json-key", f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise CoverageIoError("non-finite-json-number", f"unsupported constant {value}")


def _read_json(path: Path) -> Any:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CoverageIoError("artifact-read-failed", f"{path}: {exc}") from exc
    try:
        return json.loads(
            source,
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_non_finite,
        )
    except CoverageIoError:
        raise
    except json.JSONDecodeError as exc:
        raise CoverageIoError(
            "invalid-json",
            f"{path}:{exc.lineno}:{exc.colno}: {exc.msg}",
        ) from exc


def _object(value: Any, path: str, fields: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CoverageIoError("schema-type", f"{path} must be an object")
    actual = set(value)
    if actual != fields:
        raise CoverageIoError(
            "schema-fields",
            f"{path}: missing={sorted(fields - actual)}, unknown={sorted(actual - fields)}",
        )
    return value


def _array(value: Any, path: str) -> list[Any]:
    # JSON decoding always produces ``list``. ``tuple`` is accepted only so the
    # same parser can validate frozen dataclass payloads before writing them.
    if not isinstance(value, (list, tuple)):
        raise CoverageIoError("schema-type", f"{path} must be an array")
    return list(value)


def _integer(value: Any, path: str, *, expected: int | None = None) -> int:
    if type(value) is not int:
        raise CoverageIoError("schema-type", f"{path} must be an integer")
    if expected is not None and value != expected:
        raise CoverageIoError(
            "unsupported-schema-version",
            f"{path} must equal {expected}, got {value}",
        )
    return value


def _text(
    value: Any,
    path: str,
    *,
    allow_empty: bool = False,
    single_line: bool = False,
    trimmed: bool = False,
) -> str:
    if not isinstance(value, str):
        raise CoverageIoError("schema-type", f"{path} must be text")
    if not allow_empty and not value:
        raise CoverageIoError("schema-value", f"{path} must not be empty")
    if single_line and ("\n" in value or "\r" in value):
        raise CoverageIoError("schema-value", f"{path} must be single-line text")
    if trimmed and value != value.strip():
        raise CoverageIoError("schema-value", f"{path} must be trimmed")
    return value


def _typed_key(value: Any, path: str) -> str:
    result = _text(value, path, single_line=True, trimmed=True)
    if _TYPED_KEY.fullmatch(result) is None:
        raise CoverageIoError("schema-value", f"{path} must be a stable typed key")
    return result


def _digest(value: Any, path: str) -> str:
    result = _text(value, path, single_line=True)
    if _SHA256.fullmatch(result) is None:
        raise CoverageIoError(
            "schema-value", f"{path} must be a lowercase SHA-256 digest"
        )
    return result


def _string_array(
    value: Any,
    path: str,
    *,
    allow_empty: bool = True,
    unique: bool = True,
) -> tuple[str, ...]:
    raw = _array(value, path)
    if not allow_empty and not raw:
        raise CoverageIoError("schema-value", f"{path} must not be empty")
    result = tuple(
        _text(item, f"{path}[{index}]", single_line=True, trimmed=True)
        for index, item in enumerate(raw)
    )
    if unique and len(result) != len(set(result)):
        raise CoverageIoError("duplicate-array-value", f"{path} contains duplicates")
    return result


def _string_map(
    value: Any,
    path: str,
    *,
    nullable: bool = False,
    typed_keys: bool = True,
) -> dict[str, str] | None:
    if value is None and nullable:
        return None
    if not isinstance(value, Mapping):
        raise CoverageIoError("schema-type", f"{path} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        parsed_key = (
            _typed_key(key, f"{path} key")
            if typed_keys
            else _text(key, f"{path} key", single_line=True, trimmed=True)
        )
        result[parsed_key] = _text(
            item,
            f"{path}[{key!r}]",
            single_line=True,
            trimmed=True,
        )
    return result


def _string_array_map(
    value: Any,
    path: str,
    *,
    nullable: bool = False,
) -> dict[str, tuple[str, ...]] | None:
    if value is None and nullable:
        return None
    if not isinstance(value, Mapping):
        raise CoverageIoError("schema-type", f"{path} must be an object")
    return {
        _typed_key(key, f"{path} key"): _string_array(
            item,
            f"{path}[{key!r}]",
            allow_empty=True,
        )
        for key, item in value.items()
    }


def _read_envelope(path: Path, expected_kind: str) -> tuple[Mapping[str, Any], str]:
    root = _object(_read_json(path), "$", _ENVELOPE_FIELDS)
    _integer(root["schema_version"], "$.schema_version", expected=ARTIFACT_SCHEMA_VERSION)
    kind = _text(root["artifact_kind"], "$.artifact_kind", single_line=True)
    if kind not in _ARTIFACT_KINDS or kind != expected_kind:
        raise CoverageIoError(
            "artifact-kind",
            f"expected {expected_kind!r}, got {kind!r}",
        )
    expected_digest = _digest(root["payload_sha256"], "$.payload_sha256")
    payload = root["payload"]
    if not isinstance(payload, Mapping):
        raise CoverageIoError("schema-type", "$.payload must be an object")
    actual_digest = payload_sha256(payload)
    if actual_digest != expected_digest:
        raise CoverageIoError(
            "payload-digest-mismatch",
            f"expected {expected_digest}, got {actual_digest}",
        )
    return payload, actual_digest


def _write_envelope(path: Path, artifact_kind: str, payload: Mapping[str, Any]) -> str:
    if artifact_kind not in _ARTIFACT_KINDS:
        raise CoverageIoError("artifact-kind", f"unsupported kind {artifact_kind!r}")
    digest = payload_sha256(payload)
    envelope = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_kind": artifact_kind,
        "payload_sha256": digest,
        "payload": payload,
    }
    encoded = canonical_json_bytes(envelope) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(encoded)
        temporary.replace(path)
    except OSError as exc:
        raise CoverageIoError("artifact-write-failed", f"{path}: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return digest


@dataclass(frozen=True)
class PropertyDerivationDocument:
    schema_version: int
    ft_slug: str
    scope_slug: str
    source_manifest_digest: str
    obligation_set_digest: str
    derivations: tuple[PropertyDerivation, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def digest(self) -> str:
        return payload_sha256(self.to_dict())


@dataclass(frozen=True)
class DesignContextDocument:
    schema_version: int
    ft_slug: str
    scope_slug: str
    coverage_graph_digest: str
    context: DesignContext

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def digest(self) -> str:
        return payload_sha256(self.to_dict())


_DERIVATION_FIELDS = {
    "source_manifest_digest",
    "obligation_set_digest",
    "assertion_id",
    "source_row_id",
    "atom_id",
    "source_text_sha256",
    "property_key",
    "subject_key",
    "property_kind",
    "obligation_variants",
    "condition_key",
    "validation_trigger",
    "cleanup_strategy",
    "source_oracle_ids",
    "fixture_values",
    "calibration_questions",
}
_DERIVATION_DOCUMENT_FIELDS = {
    "schema_version",
    "ft_slug",
    "scope_slug",
    "source_manifest_digest",
    "obligation_set_digest",
    "derivations",
}


def _property_derivation(value: Any, path: str) -> PropertyDerivation:
    item = _object(value, path, _DERIVATION_FIELDS)
    variants = _string_map(item["obligation_variants"], f"{path}.obligation_variants")
    assert variants is not None
    if not variants:
        raise CoverageIoError(
            "schema-value", f"{path}.obligation_variants must not be empty"
        )
    source_oracles = _string_map(
        item["source_oracle_ids"],
        f"{path}.source_oracle_ids",
        nullable=True,
    )
    fixtures = _string_array_map(
        item["fixture_values"],
        f"{path}.fixture_values",
        nullable=True,
    )
    questions = _string_map(
        item["calibration_questions"],
        f"{path}.calibration_questions",
        nullable=True,
    )
    optional_maps: tuple[tuple[str, Mapping[str, Any] | None], ...] = (
        ("source_oracle_ids", source_oracles),
        ("fixture_values", fixtures),
        ("calibration_questions", questions),
    )
    for label, values in optional_maps:
        unknown = set(values or ()) - set(variants)
        if unknown:
            raise CoverageIoError(
                "derivation-reference",
                f"{path}.{label} has unknown obligations {sorted(unknown)}",
            )
    for obligation_id, oracle_id in (source_oracles or {}).items():
        if not oracle_id.startswith("SO-"):
            raise CoverageIoError(
                "schema-value",
                f"{path}.source_oracle_ids[{obligation_id!r}] must use an SO-* id",
            )
    derivation = PropertyDerivation(
        source_manifest_digest=_digest(
            item["source_manifest_digest"], f"{path}.source_manifest_digest"
        ),
        obligation_set_digest=_digest(
            item["obligation_set_digest"], f"{path}.obligation_set_digest"
        ),
        assertion_id=_typed_key(item["assertion_id"], f"{path}.assertion_id"),
        source_row_id=_typed_key(item["source_row_id"], f"{path}.source_row_id"),
        atom_id=_typed_key(item["atom_id"], f"{path}.atom_id"),
        source_text_sha256=_digest(
            item["source_text_sha256"], f"{path}.source_text_sha256"
        ),
        property_key=_typed_key(item["property_key"], f"{path}.property_key"),
        subject_key=_typed_key(item["subject_key"], f"{path}.subject_key"),
        property_kind=_typed_key(item["property_kind"], f"{path}.property_kind"),
        obligation_variants=variants,
        condition_key=_typed_key(item["condition_key"], f"{path}.condition_key"),
        validation_trigger=_text(
            item["validation_trigger"],
            f"{path}.validation_trigger",
            allow_empty=True,
            single_line=True,
            trimmed=True,
        ),
        cleanup_strategy=_text(
            item["cleanup_strategy"],
            f"{path}.cleanup_strategy",
            allow_empty=True,
            single_line=True,
            trimmed=True,
        ),
        source_oracle_ids=source_oracles,
        fixture_values=fixtures,
        calibration_questions=questions,
    )
    try:
        derivation.validate()
    except CoverageGraphError as exc:
        raise CoverageIoError("invalid-derivation", f"{path}: {exc}") from exc
    return derivation


def _derivation_document(payload: Mapping[str, Any]) -> PropertyDerivationDocument:
    root = _object(payload, "$.payload", _DERIVATION_DOCUMENT_FIELDS)
    raw = _array(root["derivations"], "$.payload.derivations")
    derivations = tuple(
        _property_derivation(item, f"$.payload.derivations[{index}]")
        for index, item in enumerate(raw)
    )
    assertion_ids = [item.assertion_id for item in derivations]
    property_keys = [item.property_key for item in derivations]
    obligation_ids = [
        obligation_id
        for item in derivations
        for obligation_id in item.obligation_variants
    ]
    for label, values in (
        ("assertion_id", assertion_ids),
        ("property_key", property_keys),
        ("obligation owner", obligation_ids),
    ):
        if len(values) != len(set(values)):
            raise CoverageIoError("duplicate-derivation-key", f"duplicate {label}")
    document = PropertyDerivationDocument(
        schema_version=_integer(
            root["schema_version"],
            "$.payload.schema_version",
            expected=ARTIFACT_SCHEMA_VERSION,
        ),
        ft_slug=_typed_key(root["ft_slug"], "$.payload.ft_slug"),
        scope_slug=_typed_key(root["scope_slug"], "$.payload.scope_slug"),
        source_manifest_digest=_digest(
            root["source_manifest_digest"], "$.payload.source_manifest_digest"
        ),
        obligation_set_digest=_digest(
            root["obligation_set_digest"], "$.payload.obligation_set_digest"
        ),
        derivations=derivations,
    )
    for item in document.derivations:
        if item.source_manifest_digest != document.source_manifest_digest:
            raise CoverageIoError(
                "artifact-binding",
                f"{item.assertion_id} source manifest digest does not match document",
            )
        if item.obligation_set_digest != document.obligation_set_digest:
            raise CoverageIoError(
                "artifact-binding",
                f"{item.assertion_id} obligation set digest does not match document",
            )
    return document


def write_property_derivations(
    path: Path, document: PropertyDerivationDocument
) -> str:
    if not isinstance(document, PropertyDerivationDocument):
        raise CoverageIoError(
            "schema-type", "document must be PropertyDerivationDocument"
        )
    normalized = _derivation_document(document.to_dict())
    return _write_envelope(path, "coverage-derivations", normalized.to_dict())


def load_property_derivations(
    path: Path,
    *,
    expected_source_manifest_digest: str | None = None,
    expected_obligation_set_digest: str | None = None,
) -> PropertyDerivationDocument:
    payload, _ = _read_envelope(Path(path), "coverage-derivations")
    document = _derivation_document(payload)
    if (
        expected_source_manifest_digest is not None
        and document.source_manifest_digest
        != _digest(expected_source_manifest_digest, "expected_source_manifest_digest")
    ):
        raise CoverageIoError(
            "artifact-binding", "source manifest digest does not match"
        )
    if (
        expected_obligation_set_digest is not None
        and document.obligation_set_digest
        != _digest(expected_obligation_set_digest, "expected_obligation_set_digest")
    ):
        raise CoverageIoError(
            "artifact-binding", "obligation set digest does not match"
        )
    return document


_PROPERTY_FIELDS = {
    "property_id",
    "assertion_id",
    "property_key",
    "subject_key",
    "property_kind",
    "source_row_id",
    "source_path",
    "source_locator",
    "source_text_sha256",
    "canonical_statement",
    "requirement_codes",
    "disposition",
    "condition_clauses",
    "polarity",
}
_OBLIGATION_FIELDS = {
    "obligation_id",
    "property_id",
    "atom_id",
    "coverage_variant",
    "condition_key",
    "atomic_statement",
    "observable_oracle",
    "coverage_status",
    "requirement_codes",
    "gap_id",
    "calibration_status",
    "validation_trigger",
    "cleanup_strategy",
    "source_oracle_id",
    "fixture_values",
    "calibration_question",
}
_CASE_FIELDS = {"case_key", "tc_id", "obligation_ids", "status"}
_GAP_FIELDS = {"gap_id", "property_ids", "obligation_ids", "reason"}
_GRAPH_FIELDS = {
    "schema_version",
    "ft_slug",
    "scope_slug",
    "source_manifest_digest",
    "obligation_set_digest",
    "properties",
    "obligations",
    "cases",
    "gaps",
}


def _coverage_property(value: Any, path: str) -> CoverageProperty:
    item = _object(value, path, _PROPERTY_FIELDS)
    return CoverageProperty(
        property_id=_typed_key(item["property_id"], f"{path}.property_id"),
        assertion_id=_typed_key(item["assertion_id"], f"{path}.assertion_id"),
        property_key=_typed_key(item["property_key"], f"{path}.property_key"),
        subject_key=_typed_key(item["subject_key"], f"{path}.subject_key"),
        property_kind=_typed_key(item["property_kind"], f"{path}.property_kind"),
        source_row_id=_typed_key(item["source_row_id"], f"{path}.source_row_id"),
        source_path=_text(
            item["source_path"], f"{path}.source_path", single_line=True, trimmed=True
        ),
        source_locator=_text(
            item["source_locator"],
            f"{path}.source_locator",
            single_line=True,
            trimmed=True,
        ),
        source_text_sha256=_digest(
            item["source_text_sha256"], f"{path}.source_text_sha256"
        ),
        canonical_statement=_text(
            item["canonical_statement"], f"{path}.canonical_statement"
        ),
        requirement_codes=_string_array(
            item["requirement_codes"], f"{path}.requirement_codes"
        ),
        disposition=_text(
            item["disposition"], f"{path}.disposition", single_line=True, trimmed=True
        ),
        condition_clauses=_string_array(
            item["condition_clauses"], f"{path}.condition_clauses"
        ),
        polarity=_text(
            item["polarity"], f"{path}.polarity", single_line=True, trimmed=True
        ),
    )


def _coverage_obligation(value: Any, path: str) -> CoverageObligation:
    item = _object(value, path, _OBLIGATION_FIELDS)
    return CoverageObligation(
        obligation_id=_typed_key(item["obligation_id"], f"{path}.obligation_id"),
        property_id=_typed_key(item["property_id"], f"{path}.property_id"),
        atom_id=_typed_key(item["atom_id"], f"{path}.atom_id"),
        coverage_variant=_typed_key(
            item["coverage_variant"], f"{path}.coverage_variant"
        ),
        condition_key=_typed_key(item["condition_key"], f"{path}.condition_key"),
        atomic_statement=_text(
            item["atomic_statement"], f"{path}.atomic_statement"
        ),
        observable_oracle=_text(
            item["observable_oracle"],
            f"{path}.observable_oracle",
            allow_empty=True,
        ),
        coverage_status=_text(
            item["coverage_status"],
            f"{path}.coverage_status",
            single_line=True,
            trimmed=True,
        ),
        requirement_codes=_string_array(
            item["requirement_codes"], f"{path}.requirement_codes"
        ),
        gap_id=_text(
            item["gap_id"],
            f"{path}.gap_id",
            allow_empty=True,
            single_line=True,
            trimmed=True,
        ),
        calibration_status=_text(
            item["calibration_status"],
            f"{path}.calibration_status",
            single_line=True,
            trimmed=True,
        ),
        validation_trigger=_text(
            item["validation_trigger"],
            f"{path}.validation_trigger",
            allow_empty=True,
            single_line=True,
            trimmed=True,
        ),
        cleanup_strategy=_text(
            item["cleanup_strategy"],
            f"{path}.cleanup_strategy",
            allow_empty=True,
            single_line=True,
            trimmed=True,
        ),
        source_oracle_id=_text(
            item["source_oracle_id"],
            f"{path}.source_oracle_id",
            allow_empty=True,
            single_line=True,
            trimmed=True,
        ),
        fixture_values=_string_array(
            item["fixture_values"], f"{path}.fixture_values"
        ),
        calibration_question=_text(
            item["calibration_question"],
            f"{path}.calibration_question",
            allow_empty=True,
            single_line=True,
            trimmed=True,
        ),
    )


def _coverage_case(value: Any, path: str) -> CoverageCase:
    item = _object(value, path, _CASE_FIELDS)
    return CoverageCase(
        case_key=_text(
            item["case_key"], f"{path}.case_key", single_line=True, trimmed=True
        ),
        tc_id=_typed_key(item["tc_id"], f"{path}.tc_id"),
        obligation_ids=_string_array(
            item["obligation_ids"], f"{path}.obligation_ids", allow_empty=False
        ),
        status=_text(item["status"], f"{path}.status", single_line=True, trimmed=True),
    )


def _coverage_gap(value: Any, path: str) -> CoverageGap:
    item = _object(value, path, _GAP_FIELDS)
    properties = _string_array(item["property_ids"], f"{path}.property_ids")
    obligations = _string_array(item["obligation_ids"], f"{path}.obligation_ids")
    if not properties and not obligations:
        raise CoverageIoError(
            "schema-value", f"{path} must reference a property or obligation"
        )
    return CoverageGap(
        gap_id=_typed_key(item["gap_id"], f"{path}.gap_id"),
        property_ids=properties,
        obligation_ids=obligations,
        reason=_text(item["reason"], f"{path}.reason"),
    )


def _validate_graph_integrity(graph: CoverageGraph) -> None:
    try:
        findings = validate_coverage_graph(graph)
    except Exception as exc:  # pragma: no cover - defensive adapter boundary
        raise CoverageIoError("coverage-graph-validation", str(exc)) from exc
    errors = [item for item in findings if item.severity == "error"]
    if errors:
        raise CoverageIoError(
            "coverage-graph-validation",
            "; ".join(f"{item.finding_id}: {item.message}" for item in errors),
        )


def _coverage_graph(payload: Mapping[str, Any]) -> CoverageGraph:
    root = _object(payload, "$.payload", _GRAPH_FIELDS)
    graph = CoverageGraph(
        schema_version=_integer(
            root["schema_version"],
            "$.payload.schema_version",
            expected=ARTIFACT_SCHEMA_VERSION,
        ),
        ft_slug=_typed_key(root["ft_slug"], "$.payload.ft_slug"),
        scope_slug=_typed_key(root["scope_slug"], "$.payload.scope_slug"),
        source_manifest_digest=_digest(
            root["source_manifest_digest"], "$.payload.source_manifest_digest"
        ),
        obligation_set_digest=_digest(
            root["obligation_set_digest"], "$.payload.obligation_set_digest"
        ),
        properties=tuple(
            _coverage_property(item, f"$.payload.properties[{index}]")
            for index, item in enumerate(_array(root["properties"], "$.payload.properties"))
        ),
        obligations=tuple(
            _coverage_obligation(item, f"$.payload.obligations[{index}]")
            for index, item in enumerate(
                _array(root["obligations"], "$.payload.obligations")
            )
        ),
        cases=tuple(
            _coverage_case(item, f"$.payload.cases[{index}]")
            for index, item in enumerate(_array(root["cases"], "$.payload.cases"))
        ),
        gaps=tuple(
            _coverage_gap(item, f"$.payload.gaps[{index}]")
            for index, item in enumerate(_array(root["gaps"], "$.payload.gaps"))
        ),
    )
    _validate_graph_integrity(graph)
    return graph


def write_coverage_graph(path: Path, graph: CoverageGraph) -> str:
    if not isinstance(graph, CoverageGraph):
        raise CoverageIoError("schema-type", "graph must be CoverageGraph")
    normalized = _coverage_graph(graph.to_dict())
    return _write_envelope(path, "coverage-graph", normalized.to_dict())


def load_coverage_graph(
    path: Path,
    *,
    expected_source_manifest_digest: str | None = None,
    expected_obligation_set_digest: str | None = None,
) -> CoverageGraph:
    payload, envelope_digest = _read_envelope(Path(path), "coverage-graph")
    graph = _coverage_graph(payload)
    if graph.digest != envelope_digest:
        raise CoverageIoError(
            "payload-digest-mismatch", "normalized graph digest differs from envelope"
        )
    if (
        expected_source_manifest_digest is not None
        and graph.source_manifest_digest
        != _digest(expected_source_manifest_digest, "expected_source_manifest_digest")
    ):
        raise CoverageIoError("artifact-binding", "source manifest digest does not match")
    if (
        expected_obligation_set_digest is not None
        and graph.obligation_set_digest
        != _digest(expected_obligation_set_digest, "expected_obligation_set_digest")
    ):
        raise CoverageIoError("artifact-binding", "obligation set digest does not match")
    return graph


_DESIGN_CONTEXT_FIELDS = {
    "package_id",
    "scope_title",
    "base_preconditions",
    "subject_labels",
    "condition_preconditions",
    "priorities",
}
_DESIGN_DOCUMENT_FIELDS = {
    "schema_version",
    "ft_slug",
    "scope_slug",
    "coverage_graph_digest",
    "context",
}


def _design_context(value: Any, path: str) -> DesignContext:
    item = _object(value, path, _DESIGN_CONTEXT_FIELDS)
    priorities = _string_map(
        item["priorities"], f"{path}.priorities", nullable=True, typed_keys=False
    )
    context = DesignContext(
        package_id=_typed_key(item["package_id"], f"{path}.package_id"),
        scope_title=_text(item["scope_title"], f"{path}.scope_title", trimmed=True),
        base_preconditions=_string_array(
            item["base_preconditions"],
            f"{path}.base_preconditions",
            allow_empty=True,
            unique=False,
        ),
        subject_labels=_string_map(
            item["subject_labels"], f"{path}.subject_labels"
        )
        or {},
        condition_preconditions=_string_map(
            item["condition_preconditions"], f"{path}.condition_preconditions"
        )
        or {},
        priorities=priorities,
    )
    try:
        context.validate()
    except DesignError as exc:
        raise CoverageIoError("invalid-design-context", f"{path}: {exc}") from exc
    return context


def _design_document(payload: Mapping[str, Any]) -> DesignContextDocument:
    root = _object(payload, "$.payload", _DESIGN_DOCUMENT_FIELDS)
    return DesignContextDocument(
        schema_version=_integer(
            root["schema_version"],
            "$.payload.schema_version",
            expected=ARTIFACT_SCHEMA_VERSION,
        ),
        ft_slug=_typed_key(root["ft_slug"], "$.payload.ft_slug"),
        scope_slug=_typed_key(root["scope_slug"], "$.payload.scope_slug"),
        coverage_graph_digest=_digest(
            root["coverage_graph_digest"], "$.payload.coverage_graph_digest"
        ),
        context=_design_context(root["context"], "$.payload.context"),
    )


def validate_design_context_binding(
    document: DesignContextDocument, graph: CoverageGraph
) -> None:
    if document.ft_slug != graph.ft_slug or document.scope_slug != graph.scope_slug:
        raise CoverageIoError(
            "artifact-binding", "design context FT/scope does not match coverage graph"
        )
    if document.coverage_graph_digest != graph.digest:
        raise CoverageIoError(
            "artifact-binding", "design context coverage graph digest does not match"
        )
    try:
        validate_design_context_for_graph(graph, document.context)
    except DesignError as exc:
        raise CoverageIoError("design-context-coverage", str(exc)) from exc


def write_design_context(
    path: Path,
    document: DesignContextDocument,
    *,
    graph: CoverageGraph | None = None,
) -> str:
    if not isinstance(document, DesignContextDocument):
        raise CoverageIoError(
            "schema-type", "document must be DesignContextDocument"
        )
    normalized = _design_document(document.to_dict())
    if graph is not None:
        validate_design_context_binding(normalized, graph)
    return _write_envelope(path, "coverage-design-context", normalized.to_dict())


def load_design_context(
    path: Path, *, graph: CoverageGraph | None = None
) -> DesignContextDocument:
    payload, _ = _read_envelope(Path(path), "coverage-design-context")
    document = _design_document(payload)
    if graph is not None:
        validate_design_context_binding(document, graph)
    return document
