from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from test_case_agent.coverage_graph import PropertyDerivation
from test_case_agent.coverage_io import PropertyDerivationDocument
from test_case_agent.persistence_safety import (
    has_commit_or_transition_after_mutation,
    persistence_claim,
    split_action_contract,
)
from test_case_agent.review_cycle.prepared_package import (
    PreparedObligation,
    PreparedObligationSet,
)
from test_case_agent.review_cycle.source_assertions import (
    SourceAssertion,
    SourceAssertionManifest,
)
from test_case_agent.semantic_design_bridge import (
    semantic_source_signal_registry_from_rows,
)
from test_case_agent.source_constraint_taxonomy import (
    exact_numeric_length_representatives,
    restricted_symbol_classes,
)


SEMANTIC_PROJECTION_CONTRACT = "semantic-design-compiler-projection-v1"
_HEADING = "## Immutable semantic-design bridge projection"
_TYPED_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_PLACEHOLDER_FIXTURES = {"", "-", "n/a", "none", "none_required"}
_PROJECTION_FIELDS = {
    "contract",
    "semantic_design_artifact",
    "scope_boundary_artifact",
    "bridge_receipt_artifact",
    "bridge_receipt",
    "boundary_gaps",
    "obligations",
    "dependency_bindings",
    "negative_oracles",
    "requiredness_oracles",
    "oracle_inventories",
}
_GAP_ID = re.compile(r"\bGAP-[A-Za-z0-9._-]+\b")
_REQUIREDNESS_MARKER_ACTION = re.compile(
    r"(?:проверить\s+обязательност|признак\s+обязательност|"
    r"check\s+requiredness)",
    re.IGNORECASE,
)
_DATE_NOT_FUTURE_TEXT = re.compile(
    r"(?:не\s+может\s+быть\s+больше\s+текущ|не\s+больше\s+текущ|"
    r"больше\s+текущ\w*\s+дат\w*\s+не\s+допуска)",
    re.IGNORECASE,
)


class DerivationCompilationError(ValueError):
    """Accepted source/design evidence cannot produce a safe typed derivation."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class CompiledPropertyDerivations:
    document: PropertyDerivationDocument
    registered_artifacts: tuple[Path, ...]
    subject_labels: Mapping[str, str]
    condition_preconditions: Mapping[str, str]
    scope_title: str
    base_preconditions: tuple[str, ...]
    registered_artifact_snapshots: tuple[tuple[Path, str, int], ...]


def _fail(code: str, message: str) -> None:
    raise DerivationCompilationError(code, message)


def _unique_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate-json-key", f"duplicate key {key!r}")
        result[key] = value
    return result


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail("invalid-object", f"{label} must be an object")
    return value


def _array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        _fail("invalid-array", f"{label} must be an array")
    return value


def _text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or "\n" in value
        or "\r" in value
        or (not allow_empty and not value)
    ):
        _fail("invalid-text", f"{label} must be trimmed single-line text")
    return value


def _typed(value: Any, label: str) -> str:
    result = _text(value, label)
    if _TYPED_KEY.fullmatch(result) is None:
        _fail("invalid-typed-key", f"{label} must be a stable typed key")
    return result


def _sha(value: Any, label: str) -> str:
    result = _text(value, label)
    if _SHA256.fullmatch(result) is None:
        _fail("invalid-sha256", f"{label} must be a lowercase SHA-256")
    return result


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def extract_semantic_compiler_projection(evidence_text: str) -> Mapping[str, Any]:
    """Extract exactly one compiler-owned semantic projection from evidence."""

    if not isinstance(evidence_text, str):
        _fail("invalid-evidence", "source evidence must be text")
    headings = [match.start() for match in re.finditer(re.escape(_HEADING), evidence_text)]
    if len(headings) != 1:
        _fail(
            "semantic-projection-count",
            f"source evidence must contain exactly one {_HEADING!r} section",
        )
    tail = evidence_text[headings[0] + len(_HEADING) :]
    match = re.match(r"\s*```json\s*\n(?P<body>.*?)\n```", tail, re.DOTALL)
    if match is None:
        _fail(
            "semantic-projection-format",
            "semantic projection must be the immediate fenced JSON block",
        )
    try:
        payload = json.loads(
            match.group("body"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: _fail(
                "non-finite-json-number", f"unsupported constant {value}"
            ),
        )
    except DerivationCompilationError:
        raise
    except json.JSONDecodeError as exc:
        _fail("invalid-semantic-projection-json", str(exc))
    projection = _object(payload, "semantic projection")
    if set(projection) != _PROJECTION_FIELDS:
        _fail(
            "semantic-projection-fields",
            "semantic projection fields differ: "
            f"missing={sorted(_PROJECTION_FIELDS - set(projection))}, "
            f"unknown={sorted(set(projection) - _PROJECTION_FIELDS)}",
        )
    if projection.get("contract") != SEMANTIC_PROJECTION_CONTRACT:
        _fail("semantic-projection-contract", "unsupported semantic projection")
    return projection


def extract_optional_semantic_compiler_projection(
    evidence_text: str,
) -> Mapping[str, Any] | None:
    """Extract a semantic projection when the source evidence explicitly has one.

    Schema-v2 source-first runs no longer require the standard semantic bridge.
    A present projection remains strict and hash-bound; an absent projection is
    handled by the source-first derivation compiler.
    """

    if not isinstance(evidence_text, str):
        _fail("invalid-evidence", "source evidence must be text")
    count = len(
        [match.start() for match in re.finditer(re.escape(_HEADING), evidence_text)]
    )
    if count == 0:
        return None
    return extract_semantic_compiler_projection(evidence_text)


def _repo_artifact(
    repo_root: Path,
    payload: Any,
    label: str,
) -> tuple[Path, Mapping[str, Any], bytes]:
    item = _object(payload, label)
    path_text = _text(item.get("path"), f"{label}.path")
    posix = PurePosixPath(path_text)
    if (
        posix.is_absolute()
        or "\\" in path_text
        or any(part in {"", ".", ".."} for part in posix.parts)
        or posix.as_posix() != path_text
    ):
        _fail("unsafe-artifact-path", f"{label}.path is not repo-relative")
    path = (repo_root / Path(*posix.parts)).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError:
        _fail("unsafe-artifact-path", f"{label}.path escapes repository")
    if not path.is_file():
        _fail("missing-artifact", f"{label}.path is missing: {path_text}")
    expected = _sha(item.get("sha256"), f"{label}.sha256")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _fail("artifact-read-error", f"{label} cannot be read: {exc}")
    if hashlib.sha256(raw).hexdigest() != expected:
        _fail("artifact-hash-mismatch", f"{label} changed: {path_text}")
    return path, item, raw


def _read_json_object_bytes(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: _fail(
                "non-finite-json-number", f"unsupported constant {value}"
            ),
        )
    except DerivationCompilationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail("invalid-artifact-json", f"{label}: {exc}")
    return _object(payload, label)


def _semantic_assertions(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    source_designs = _array(payload.get("source_designs"), "semantic source_designs")
    assertions: dict[str, Mapping[str, Any]] = {}
    for design_index, raw_design in enumerate(source_designs):
        design = _object(raw_design, f"source_designs[{design_index}]")
        for assertion_index, raw_assertion in enumerate(
            _array(design.get("assertions"), f"source_designs[{design_index}].assertions")
        ):
            assertion = _object(
                raw_assertion,
                f"source_designs[{design_index}].assertions[{assertion_index}]",
            )
            assertion_id = _typed(assertion.get("assertion_id"), "assertion_id")
            if assertion_id in assertions:
                _fail("duplicate-semantic-assertion", assertion_id)
            assertions[assertion_id] = assertion
    return assertions


def _validate_assertion_projection(
    accepted: SourceAssertion,
    semantic: Mapping[str, Any],
    *,
    require_bound_subject: bool,
) -> str:
    exact_fields: tuple[tuple[str, Any], ...] = (
        ("canonical_statement", accepted.canonical_statement),
        ("polarity", accepted.polarity),
        ("semantic_disposition", accepted.semantic_disposition),
        ("execution_readiness", accepted.execution_readiness),
        ("risk", accepted.risk),
        ("condition_clauses", list(accepted.condition_clauses)),
        ("action_clauses", list(accepted.action_clauses)),
        ("oracle_clauses", list(accepted.oracle_clauses)),
        ("requirement_codes", list(accepted.requirement_codes)),
        ("atom_id", accepted.atom_id),
        ("obligation_ids", list(accepted.obligation_ids)),
    )
    for field, expected in exact_fields:
        if semantic.get(field) != expected:
            _fail(
                "semantic-assertion-drift",
                f"{accepted.assertion_id}.{field} differs from accepted source",
            )
    label = _text(semantic.get("field_or_block"), f"{accepted.assertion_id}.field_or_block")
    evidence = " ".join(
        (
            accepted.exact_source_text,
            accepted.canonical_statement,
            *accepted.condition_clauses,
            *accepted.action_clauses,
            *accepted.oracle_clauses,
        )
    )

    def token_bounded(source: str, fragment: str) -> bool:
        source_text = " ".join(source.casefold().split())
        fragment_text = " ".join(fragment.casefold().split())
        start = 0
        while fragment_text:
            index = source_text.find(fragment_text, start)
            if index < 0:
                return False
            end = index + len(fragment_text)
            left_cut = (
                index > 0
                and source_text[index - 1].isalnum()
                and fragment_text[0].isalnum()
            )
            right_cut = (
                end < len(source_text)
                and source_text[end].isalnum()
                and fragment_text[-1].isalnum()
            )
            if not left_cut and not right_cut:
                return True
            start = index + 1
        return False

    if require_bound_subject and not token_bounded(evidence, label):
        # The semantic bridge may use a convenient composite field label (for
        # example, "additional field for Other") that is not literal source
        # wording.  It remains metadata, but must not enter the production
        # projection as accepted wording.  Fall back to the exact accepted
        # canonical statement instead of attempting a linguistic abbreviation.
        return accepted.canonical_statement
    return label


def _dictionary_fixtures(obligation: PreparedObligation) -> tuple[str, ...]:
    values: list[str] = []
    for requirement in obligation.dictionary_requirements:
        source_values = (
            requirement.fixture_values
            if requirement.coverage_mode == "reference-only"
            else requirement.required_values
        )
        values.extend(item.value for item in source_values)
    return tuple(dict.fromkeys(values))


def _validate_non_testable_prepared_context(
    obligation: PreparedObligation,
    assertions_by_atom: Mapping[str, SourceAssertion],
) -> None:
    assertion = assertions_by_atom.get(obligation.traceability_atom_id)
    if (
        assertion is None
        or assertion.semantic_disposition == "testable"
        or obligation.coverage_status != "not-applicable"
        or obligation.observable_oracle
        or obligation.gap_id
        or obligation.dictionary_refs
        or obligation.dictionary_requirements
        or obligation.calibration_status != "none"
        or obligation.planned_test_case_id
        or assertion.source_row_id not in obligation.source_refs
    ):
        _fail(
            "unsafe-non-testable-obligation",
            f"{obligation.obligation_id} is not a closed context projection",
        )


def _fixture_values(
    semantic: Mapping[str, Any], obligation: PreparedObligation
) -> tuple[str, ...]:
    dictionary_values = _dictionary_fixtures(obligation)
    if obligation.dictionary_refs:
        if not dictionary_values:
            _fail(
                "dictionary-values-missing",
                f"{obligation.obligation_id} has no compiled dictionary values",
            )
        return dictionary_values
    raw_value = semantic.get("test_data", "")
    if not isinstance(raw_value, str) or "\n" in raw_value or "\r" in raw_value:
        _fail(
            "invalid-text",
            f"{obligation.obligation_id}.test_data must be single-line text",
        )
    # Markdown materialization trims cell-edge whitespace.  Apply that same
    # transport-only normalization before checking the compiled intent.
    raw = raw_value.strip()
    if raw.casefold() in _PLACEHOLDER_FIXTURES:
        return ()
    if raw not in obligation.test_intent:
        _fail(
            "fixture-not-compiled",
            f"{obligation.obligation_id}.test_data is absent from compiled intent",
        )
    # Keep the prepared field byte-for-byte.  Splitting free text here would be
    # another inference layer and could silently change a composite fixture.
    return (raw,)


def _needs_validation_trigger_calibration(
    *,
    polarity: str,
    oracle: str,
    action: str,
) -> bool:
    """Fail safe when a save outcome has no source-backed validation action.

    Entering a value alone cannot prove either positive or negative persistence.
    This narrow guard only downgrades such a case to calibration; it never
    manufactures a save/submit action.
    """

    del polarity  # persistence safety is independent of positive/negative polarity
    if persistence_claim(oracle) is None:
        return False
    return not has_commit_or_transition_after_mutation(
        split_action_contract(action)
    )


def _needs_requiredness_calibration(
    *,
    property_type: str,
    action: str,
) -> bool:
    if property_type not in {"requiredness", "optionalness"}:
        return False
    if has_commit_or_transition_after_mutation(split_action_contract(action)):
        return False
    return bool(_REQUIREDNESS_MARKER_ACTION.search(action))


def _needs_date_boundary_calibration(
    *,
    property_type: str,
    coverage_class: str,
    statement: str,
    oracle: str,
    action: str,
) -> bool:
    if property_type != "date-boundary" or coverage_class != "not-future":
        return False
    source_text = " ".join((statement, oracle))
    if not _DATE_NOT_FUTURE_TEXT.search(source_text):
        return False
    # A field input action proves the value used, but not the exact rejection
    # trigger or UI reaction for the future-date boundary.
    return not has_commit_or_transition_after_mutation(split_action_contract(action))


def _date_boundary_fixture_values() -> tuple[str, str, str]:
    return (
        "текущая дата - 1 день",
        "текущая дата",
        "текущая дата + 1 день",
    )


def _safe_property_kind(
    semantic: Mapping[str, Any],
    fixtures: Sequence[str],
    *,
    force_writer_for_complex_condition: bool = False,
) -> str:
    property_type = _typed(semantic.get("property_type"), "property_type").casefold()
    coverage_class = _typed(
        semantic.get("coverage_class"), "coverage_class"
    ).casefold()
    if force_writer_for_complex_condition:
        return "source-complex-condition-" + property_type
    if property_type == "visibility":
        return "visibility"
    if property_type == "dictionary" and fixtures:
        return "dictionary"
    if property_type == "default-template" and len(fixtures) == 1:
        return "default"
    if (
        property_type == "format"
        and coverage_class == "allowed-class"
        and len(fixtures) == 1
    ):
        return "positive-input"
    # All other shapes remain writer cards.  In particular, requiredness and
    # invalid-input must not become deterministic until an exact validation
    # trigger exists; editability needs two distinct values.
    return "source-" + property_type


def _effective_validation_trigger(*, property_kind: str, action_contract: str) -> str:
    """Keep initial defaults observational even if preparation invented focus."""

    return "" if property_kind == "default" else action_contract


def _calibration_outcome(polarity: str) -> str:
    return "его отклонение" if polarity == "negative" else "его принятие"


def _condition_binding(assertion: SourceAssertion) -> tuple[str, str, bool]:
    """Return a stable condition identity and an exact accepted precondition.

    One atomic condition can be rendered deterministically.  Multiple condition
    clauses are not silently joined with an invented AND/OR relationship: they
    force a writer card, and the exact accepted canonical statement is retained
    as the runner-owned context while the graph keeps every individual clause.
    """

    clauses = tuple(assertion.condition_clauses)
    if not clauses:
        return "always", "", False
    if len(clauses) == 1:
        evidence = clauses[0]
        digest_basis: Any = {"condition_clause": evidence}
        complex_condition = False
    else:
        evidence = assertion.canonical_statement
        digest_basis = {"condition_clauses": list(clauses)}
        complex_condition = True
    condition_key = "condition:" + _canonical_sha256(digest_basis)[:16]
    return condition_key, evidence, complex_condition


def _oracle_bindings(
    projection: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    oracle_ids: dict[str, str] = {}
    questions: dict[str, str] = {}
    for collection in ("negative_oracles", "requiredness_oracles"):
        for index, raw in enumerate(_array(projection.get(collection), collection)):
            item = _object(raw, f"{collection}[{index}]")
            obligation_id = _typed(
                item.get("linked_obligation_id"),
                f"{collection}[{index}].linked_obligation_id",
            )
            if obligation_id in oracle_ids:
                _fail("duplicate-obligation-oracle", obligation_id)
            oracle_id = _typed(
                item.get("scope_obligation_id"),
                f"{collection}[{index}].scope_obligation_id",
            )
            if not oracle_id.startswith("SO-"):
                _fail("invalid-source-oracle", oracle_id)
            oracle_ids[obligation_id] = oracle_id
            question = _text(
                item.get("analyst_question", ""),
                f"{collection}[{index}].analyst_question",
                allow_empty=True,
            )
            if question.casefold() not in _PLACEHOLDER_FIXTURES:
                questions[obligation_id] = question
    return oracle_ids, questions


def _semantic_source_signal_registry(
    manifest: SourceAssertionManifest,
) -> dict[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    code_registry: dict[str, list[str]] = {}
    source_rows = tuple(getattr(manifest, "source_rows", ()) or ())
    if not source_rows:
        return {}
    for row in source_rows:
        codes = list(row.requirement_codes)
        rows.append(
            {
                "source_row_id": row.source_row_id,
                "source_ref": "; ".join(codes) if codes else row.source_row_id,
                "field_or_action": row.source_row_id,
                "bounded_source_text": row.bounded_source_text,
            }
        )
        code_registry[row.source_row_id] = codes
    return semantic_source_signal_registry_from_rows(rows, code_registry)


def _coverage_gap_artifact_ids(
    *,
    repo_root: Path,
    manifest: SourceAssertionManifest,
) -> set[str]:
    artifact = manifest.coverage_gaps_artifact
    path_text = artifact.path
    posix = PurePosixPath(path_text)
    if (
        posix.is_absolute()
        or "\\" in path_text
        or any(part in {"", ".", ".."} for part in posix.parts)
        or posix.as_posix() != path_text
    ):
        _fail("unsafe-coverage-gap-path", "coverage gap artifact path is unsafe")
    path = (repo_root / Path(*posix.parts)).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError:
        _fail("unsafe-coverage-gap-path", "coverage gap artifact escapes repository")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _fail("coverage-gap-artifact-read-error", str(exc))
    if hashlib.sha256(raw).hexdigest() != artifact.sha256:
        _fail("coverage-gap-artifact-drift", "coverage gap artifact hash mismatch")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        _fail("coverage-gap-artifact-utf8", str(exc))
    return set(_GAP_ID.findall(text))


def _signal_refs(signal: Mapping[str, Any]) -> set[str]:
    refs = {str(signal.get("source_row_id", ""))}
    refs.update(map(str, signal.get("requirement_codes", []) or []))
    refs.discard("")
    return refs


def _signal_has_registered_gap(
    *,
    signal: Mapping[str, Any],
    obligation_set: PreparedObligationSet,
    materialized_gap_ids: set[str],
) -> bool:
    refs = _signal_refs(signal)
    for gap in obligation_set.coverage_gaps:
        if (
            gap.gap_id in materialized_gap_ids
            and refs.intersection(gap.source_refs)
        ):
            return True
    return False


def _signal_can_be_format_calibration(signal: Mapping[str, Any]) -> bool:
    return (
        str(signal.get("source_binding", ""))
        == "exclusive-symbol-class-restriction"
        or str(signal.get("restriction_type", "")) == "numeric"
    )


def _matching_format_obligation_id(
    *,
    signal: Mapping[str, Any],
    manifest: SourceAssertionManifest,
    semantic_obligations: Mapping[str, Mapping[str, Any]],
) -> str | None:
    if not _signal_can_be_format_calibration(signal):
        return None
    signal_row_id = str(signal.get("source_row_id", ""))
    signal_codes = set(map(str, signal.get("requirement_codes", []) or []))
    for assertion in manifest.assertions:
        if (
            assertion.semantic_disposition != "testable"
            or assertion.source_row_id != signal_row_id
        ):
            continue
        owner_codes = set(map(str, assertion.requirement_codes))
        if signal_codes and not signal_codes.issubset(owner_codes):
            continue
        for obligation_id in assertion.obligation_ids:
            semantic = semantic_obligations.get(obligation_id)
            if semantic is None:
                continue
            if (
                str(semantic.get("property_type", "")).casefold() == "format"
                and str(semantic.get("coverage_class", "")).casefold()
                == "allowed-class"
            ):
                return obligation_id
    return None


def _projection_oracles_by_signal(
    projection: Mapping[str, Any],
    collection: str,
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(_array(projection.get(collection), collection)):
        item = _object(raw, f"{collection}[{index}]")
        signal_id = _typed(item.get("signal_id"), f"{collection}[{index}].signal_id")
        if signal_id in result:
            _fail("duplicate-source-signal-oracle", signal_id)
        result[signal_id] = item
    return result


def _validate_source_signal_accounting(
    *,
    repo_root: Path,
    manifest: SourceAssertionManifest,
    obligation_set: PreparedObligationSet,
    projection: Mapping[str, Any],
    expected_obligations: set[str],
    semantic_obligations: Mapping[str, Mapping[str, Any]],
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    registry = _semantic_source_signal_registry(manifest)
    if not registry:
        return {}
    materialized_gap_ids = _coverage_gap_artifact_ids(
        repo_root=repo_root,
        manifest=manifest,
    )
    projection_oracles = {
        "negative": _projection_oracles_by_signal(projection, "negative_oracles"),
        "requiredness": _projection_oracles_by_signal(
            projection,
            "requiredness_oracles",
        ),
    }
    findings: list[str] = []
    format_calibration_signals: dict[str, list[Mapping[str, Any]]] = {}
    for signal_kind, signals in registry.items():
        for signal in signals:
            signal_id = str(signal.get("signal_id", ""))
            oracle = projection_oracles[signal_kind].get(signal_id)
            if oracle is not None:
                linked_obligation = _typed(
                    oracle.get("linked_obligation_id"),
                    f"{signal_id}.linked_obligation_id",
                )
                if linked_obligation not in expected_obligations:
                    findings.append(
                        f"{signal_id}: linked obligation {linked_obligation} is "
                        "not in the accepted testable source assertion set"
                    )
                continue
            if _signal_has_registered_gap(
                signal=signal,
                obligation_set=obligation_set,
                materialized_gap_ids=materialized_gap_ids,
            ):
                continue
            format_obligation_id = _matching_format_obligation_id(
                signal=signal,
                manifest=manifest,
                semantic_obligations=semantic_obligations,
            )
            if format_obligation_id is not None:
                format_calibration_signals.setdefault(
                    format_obligation_id,
                    [],
                ).append(signal)
                continue
            signal_description = str(signal.get("restriction_type", signal_kind))
            negative_class = str(signal.get("negative_class", "")).strip()
            representative = str(
                signal.get("representative_invalid_value", "")
            ).strip()
            if negative_class:
                signal_description += f"/{negative_class}"
            if representative:
                signal_description += f" example={representative!r}"
            findings.append(
                f"{signal_id}: {signal_description} from "
                f"{signal.get('source_row_id', '')} is not represented by a "
                "semantic oracle or registered source-bound GAP"
            )
    if findings:
        _fail(
            "source-semantic-signal-uncovered",
            "schema-v2 source semantics lost before writer: "
            + "; ".join(findings),
        )
    return {
        obligation_id: tuple(signals)
        for obligation_id, signals in format_calibration_signals.items()
    }


_SOURCE_FIRST_RUNTIME_LABEL = re.compile(
    r"`([^`\r\n]{1,160})`|«([^»\r\n]{1,160})»|В«([^В»\r\n]{1,160})В»"
)
_SOURCE_FIRST_DEFAULT_SUBJECT = re.compile(
    r"(?:по умолчанию|default)[^`«\r\n]{0,80}(?:для|for)\s*"
    r"(?:`([^`\r\n]{1,160})`|«([^»\r\n]{1,160})»|В«([^В»\r\n]{1,160})В»)",
    re.IGNORECASE,
)
_SOURCE_FIRST_DEFAULT_VALUE = re.compile(
    r"(?:имеет\s+значение|имеют\s+значение|равно|equals|default\s+value\s*(?:is|=))"
    r"[^`«\r\n]{0,80}"
    r"(?:`([^`\r\n]{1,160})`|«([^»\r\n]{1,160})»|В«([^В»\r\n]{1,160})В»)",
    re.IGNORECASE,
)
_SOURCE_FIRST_EN_FIELD = re.compile(
    r"\b(?:the\s+)?([A-Za-z][A-Za-z0-9 _/-]{1,100}\s+"
    r"(?:field|block|button|list|section|tab))\b",
    re.IGNORECASE,
)
_SOURCE_FIRST_ROW_METADATA = re.compile(
    r"\s+(?:Да|Нет)\b|\s+(?:BSR|GSR|DIT)\s+[A-Za-z0-9._/-]+\b|"
    r"\s+(?:Поле|Переключатель|Выпадающий|Справочник|Текст|Дата)\b",
    re.IGNORECASE,
)
_SOURCE_FIRST_TEST_DATA = re.compile(
    r"(?:^|;\s*)Test data:\s*(?P<value>.*?)(?=$|;\s*[A-Za-z][A-Za-z ]+ contract:)",
    re.IGNORECASE,
)
_SOURCE_FIRST_ACTION_LIKE_TEST_DATA = re.compile(
    r"^(?:попытаться|ввести|выбрать|оставить|нажать|инициировать|проверить)\b",
    re.IGNORECASE,
)
_SOURCE_FIRST_DADATA_FIXTURE = re.compile(r"\bFX-DADATA-[A-Z0-9_-]+\b")
_SOURCE_FIRST_SCOPE_PREFIX_MARKER = re.compile(
    r"(?<![A-Za-zА-ЯЁа-яё])(?:блок\w*|раздел\w*|block|section)"
    r"(?![A-Za-zА-ЯЁа-яё])",
    re.IGNORECASE,
)
_SOURCE_FIRST_SUBJECT_PREFIXES = (
    "поле",
    "поля",
    "полю",
    "блок",
    "блока",
    "блоке",
    "кнопк",
    "переключател",
    "признак",
    "спис",
    "раздел",
    "вкладк",
    "field",
    "block",
    "button",
    "list",
    "section",
    "tab",
)
_SOURCE_FIRST_VALUE_LABEL_PREFIXES = (
    "сообщен",
    "текст",
    "подсказ",
    "значени",
    "например",
    "example",
    "message",
    "value",
)


def _source_first_text(*values: str) -> str:
    return " ".join(value for value in values if value).casefold()


def _source_first_runtime_labels_with_prefix(
    value: str,
) -> tuple[tuple[str, str], ...]:
    labels: list[tuple[str, str]] = []
    for match in _SOURCE_FIRST_RUNTIME_LABEL.finditer(value):
        label = next(group for group in match.groups() if group is not None).strip()
        prefix = value[max(0, match.start() - 80) : match.start()].casefold()
        if label:
            labels.append((label, prefix))
    return tuple(labels)


def _source_first_label_is_runtime_value(prefix: str) -> bool:
    return any(marker in prefix for marker in _SOURCE_FIRST_VALUE_LABEL_PREFIXES)


def _source_first_default_subject_label(value: str) -> str:
    match = _SOURCE_FIRST_DEFAULT_SUBJECT.search(value)
    if match is None:
        return ""
    return next(group for group in match.groups() if group is not None).strip()


def _source_first_default_fixture_values(*values: str) -> tuple[str, ...]:
    evidence = " ".join(value for value in values if value)
    labels: list[str] = []
    for match in _SOURCE_FIRST_DEFAULT_VALUE.finditer(evidence):
        label = next(group for group in match.groups() if group is not None).strip()
        if label.casefold() not in _PLACEHOLDER_FIXTURES:
            labels.append(label)
    if labels:
        return tuple(dict.fromkeys(labels))
    for label, prefix in _source_first_runtime_labels_with_prefix(evidence):
        if (
            _source_first_label_is_runtime_value(prefix)
            and label.casefold() not in _PLACEHOLDER_FIXTURES
        ):
            return (label,)
    return ()


def _source_first_row_subject_label(value: str) -> str:
    cleaned = " ".join(value.split())
    match = _SOURCE_FIRST_ROW_METADATA.search(cleaned)
    if match is None:
        return ""
    label = cleaned[: match.start()].strip(" .:-")
    if 1 < len(label) <= 120:
        return label
    return ""


def _source_first_subject_label(
    assertion: SourceAssertion,
    obligations: Sequence[PreparedObligation],
) -> str:
    default_subject = _source_first_default_subject_label(
        assertion.canonical_statement
    )
    if default_subject:
        return default_subject
    evidence_groups = (
        (assertion.canonical_statement,),
        assertion.action_clauses,
        tuple(item.atomic_statement for item in obligations),
        tuple(item.test_intent for item in obligations),
        assertion.oracle_clauses,
        tuple(item.observable_oracle for item in obligations),
        (assertion.exact_source_text,),
        assertion.condition_clauses,
    )
    for group in evidence_groups:
        evidence = " ".join(group)
        for label, prefix in _source_first_runtime_labels_with_prefix(evidence):
            if _source_first_label_is_runtime_value(prefix):
                continue
            if any(marker in prefix for marker in _SOURCE_FIRST_SUBJECT_PREFIXES):
                return label
    evidence = " ".join(" ".join(group) for group in evidence_groups)
    match = _SOURCE_FIRST_EN_FIELD.search(evidence)
    if match is not None:
        return match.group(1).strip()
    row_subject = _source_first_row_subject_label(assertion.exact_source_text)
    if row_subject:
        return row_subject
    # Safe fallback: the accepted canonical statement is already source-bound
    # and passes design-context validation, even if it is less readable.
    return assertion.canonical_statement.strip()


def _source_first_section_card_label(
    repo_root: Path,
    source_manifest: SourceAssertionManifest,
) -> str:
    section_match = re.match(r"^(\d+)-(\d+)(?:-|$)", source_manifest.scope_slug)
    if section_match is None:
        return ""
    section = f"{section_match.group(1)}.{section_match.group(2)}"
    source_paths = tuple(
        dict.fromkeys(assertion.source_path for assertion in source_manifest.assertions)
    )
    for source_path in source_paths:
        path = (repo_root / source_path).resolve()
        try:
            path.relative_to(repo_root)
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError):
            continue
        plain = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        text = " ".join(plain.split())
        pattern = re.compile(
            rf"\b{re.escape(section)}\.\s*(?:Карточка|Форма|Экран|Раздел)\s+"
            r"[«\"]([^»\"\r\n]{1,120})[»\"]",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match is not None:
            return match.group(1).strip()
    return ""


def _source_first_scope_title(
    repo_root: Path,
    source_manifest: SourceAssertionManifest,
) -> str:
    block_title = ""
    for assertion in source_manifest.assertions:
        evidence = " ".join(
            (
                assertion.canonical_statement,
                *assertion.condition_clauses,
                *assertion.action_clauses,
                *assertion.oracle_clauses,
                assertion.exact_source_text,
            )
        )
        for label, prefix in _source_first_runtime_labels_with_prefix(evidence):
            if _SOURCE_FIRST_SCOPE_PREFIX_MARKER.search(prefix) is not None:
                block_title = label
                break
        if block_title:
            break
    card_title = _source_first_section_card_label(repo_root, source_manifest)
    if card_title and block_title:
        return f"Карточка «{card_title}» / Блок «{block_title}»"
    if block_title:
        return block_title
    if card_title:
        return f"Карточка «{card_title}»"
    return source_manifest.scope_slug


def _source_first_dadata_verification_path(
    repo_root: Path,
    fixture_id: str,
) -> Path | None:
    search_root = repo_root / "fts"
    if not search_root.is_dir():
        search_root = repo_root
    matches = sorted(search_root.rglob(f"{fixture_id}.verification.json"))
    return matches[0] if matches else None


def _source_first_dadata_fixture_values(
    repo_root: Path,
    obligation: PreparedObligation,
) -> tuple[str, ...]:
    fixture_ids = tuple(
        dict.fromkeys(_SOURCE_FIRST_DADATA_FIXTURE.findall(obligation.test_intent))
    )
    for fixture_id in fixture_ids:
        path = _source_first_dadata_verification_path(repo_root, fixture_id)
        if path is None:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if (
            not isinstance(payload, Mapping)
            or payload.get("fixture_id") != fixture_id
            or payload.get("status") != "verified"
        ):
            continue
        request = payload.get("request")
        expected = payload.get("expected_response")
        if not isinstance(request, Mapping) or not isinstance(expected, Mapping):
            continue
        parameters = request.get("parameters")
        if not isinstance(parameters, Mapping):
            continue

        values: list[str] = [fixture_id]
        query = parameters.get("query")
        if isinstance(query, (str, int, float)) and not isinstance(query, bool):
            values.append(str(query))
        suggestion = expected.get("exact_suggestion")
        if isinstance(suggestion, (str, int, float)) and not isinstance(
            suggestion, bool
        ):
            values.append(str(suggestion))
        components = expected.get("exact_components")
        if isinstance(components, Mapping):
            for key in (
                "code",
                "name",
                "region_code",
                "type",
                "postal_code",
                "region",
                "city",
                "street",
                "house",
                "flat",
            ):
                value = components.get(key)
                if isinstance(value, (str, int, float)) and not isinstance(
                    value, bool
                ):
                    values.append(str(value))
        if expected.get("suggestions") == []:
            values.append("suggestions=[]")
        return tuple(dict.fromkeys(value for value in values if value))
    return ()


def _source_first_fixture_values(
    repo_root: Path,
    obligation: PreparedObligation,
) -> tuple[str, ...]:
    dictionary_values = _dictionary_fixtures(obligation)
    if obligation.dictionary_refs:
        if not dictionary_values:
            _fail(
                "dictionary-values-missing",
                f"{obligation.obligation_id} has no compiled dictionary values",
            )
        return dictionary_values
    dadata_values = _source_first_dadata_fixture_values(repo_root, obligation)
    if dadata_values:
        return dadata_values
    match = _SOURCE_FIRST_TEST_DATA.search(obligation.test_intent)
    if match is None:
        return ()
    raw = match.group("value").strip()
    if raw.casefold() in _PLACEHOLDER_FIXTURES:
        return ()
    labels = tuple(
        dict.fromkeys(
            label
            for label, _prefix in _source_first_runtime_labels_with_prefix(raw)
            if label.casefold() not in _PLACEHOLDER_FIXTURES
        )
    )
    if labels:
        return labels
    representative = _source_first_representative_fixture(raw, obligation)
    if representative:
        return (representative,)
    if _SOURCE_FIRST_ACTION_LIKE_TEST_DATA.search(raw):
        return ()
    return (raw,) if raw else ()


def _source_first_representative_fixture(
    raw: str,
    obligation: PreparedObligation,
) -> str:
    text = _source_first_text(
        raw,
        obligation.atomic_statement,
        obligation.observable_oracle,
        obligation.test_intent,
    )
    if "одинаков" in text:
        if any(token in text for token in ("шесть", "шести", "6")):
            return "111111"
        if any(token in text for token in ("три", "трех", "трёх", "3")):
            return "111"
    if "14-лет" in text and any(token in text for token in ("раньше", "меньше")):
        return "дата 14-летия - 1 день"
    if "20-лет" in text and "20-летия + 90" in text:
        return "дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 91 день"
    if "45-лет" in text and "45-летия + 90" in text:
        return "дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 91 день"
    if "45 лет или позже" in text or ("45-лет" in text and "бессроч" in text):
        return "дата выдачи = дата 45-летия"
    if (
        "шесть циф" in text
        or "6 циф" in text
        or "xxx-xxx" in text
    ):
        return "123456"
    return ""


def _source_first_date_window_fixture_values(
    *values: str,
) -> tuple[str, ...]:
    text = _source_first_text(*values)
    if "14-лет" in text and any(token in text for token in ("раньше", "меньше")):
        return ("дата 14-летия", "дата 14-летия - 1 день")
    if "20-лет" in text and "20-летия + 90" in text:
        return (
            "дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 90 дней",
            "дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 91 день",
        )
    if "45-лет" in text and "45-летия + 90" in text:
        return (
            "дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 90 дней",
            "дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 91 день",
        )
    return ()


def _source_first_digits_only_fixture_values(*values: str) -> tuple[str, ...]:
    restricted = restricted_symbol_classes(_source_first_text(*values))
    return tuple(
        dict.fromkeys(
            item.representative_invalid_value
            for item in restricted
            if item.restriction_type == "numeric"
            and item.negative_class
            not in {"length-n-minus-one", "length-n-plus-one"}
        )
    )


def _source_first_has_explicit_validation_action(action: str) -> bool:
    text = _source_first_text(action)
    return any(
        token in text
        for token in (
            "инициировать проверку",
            "запустить проверку",
            "проверку сохранения",
            "проверить срок",
            "проверить значение",
        )
    )


def _source_first_positive_date_window_question(
    *,
    subject_label: str,
    fixtures: Sequence[str],
    fallback: str,
) -> str:
    fixture_text = ", ".join(f"`{value}`" for value in fixtures) or "граничного условия"
    target = subject_label.strip("«»") or "проверяемого элемента"
    return (
        "Какой конкретный наблюдаемый UI-артефакт подтверждает допустимость "
        f"{fixture_text} для элемента «{target}» без опоры на внутреннюю "
        f"классификацию системы? {fallback}".strip()
    )


def _source_first_kind_and_variant(
    *,
    assertion: SourceAssertion,
    obligation: PreparedObligation,
    fixtures: Sequence[str],
    complex_condition: bool,
) -> tuple[str, str]:
    del fixtures
    text = _source_first_text(
        assertion.canonical_statement,
        *assertion.action_clauses,
        *assertion.oracle_clauses,
        obligation.atomic_statement,
        obligation.observable_oracle,
        obligation.test_intent,
    )
    if complex_condition:
        return "source-complex-condition-runtime", "runtime"
    if obligation.dictionary_refs or obligation.dictionary_requirements:
        return "dictionary", "dictionary"
    if any(token in text for token in ("по умолчанию", "default")):
        return "default", "default"
    if any(
        token in text
        for token in (
            "обязател",
            "пустым",
            "пустое",
            "пустой",
            "пустого",
            "пустую",
            "required",
            "empty",
            "выберите значение",
            "введите дату",
        )
    ):
        if any(token in text for token in ("не обязатель", "optional", "optionalness")):
            return "source-optionalness", "optional-empty"
        return "source-requiredness", "required-empty"
    if any(
        token in text
        for token in ("будущ", "больше текущ", "future date", "not-future")
    ):
        return "source-date-boundary", "not-future"
    if any(
        token in text
        for token in (
            "14-лет",
            "20-лет",
            "45-лет",
            "срока действия",
            "раньше даты",
        )
    ):
        return "source-date-boundary", "date-window"
    if any(
        token in text
        for token in (
            "нечислов",
            "только циф",
            "цифр",
            "символ",
            "длин",
            "повтор",
            "numeric",
            "digit",
            "length",
            "format",
        )
    ):
        if any(token in text for token in ("текстов", "латини", "пробел", "hyphen")):
            return "source-format", "allowed-class"
        if any(token in text for token in ("нечислов", "numeric", "digit")):
            return "source-format", "digits-only"
        if any(token in text for token in ("повтор", "одинаков")):
            return "source-format", "repeated-digits"
        if any(token in text for token in ("длин", "length")):
            return "source-format", "length-limit"
        return "source-format", "format"
    if any(token in text for token in ("видим", "отображ", "visible", "displayed")):
        return "visibility", "visible"
    if any(token in text for token in ("редакт", "editable", "editability")):
        return "source-editability", "editable"
    return "source-runtime", "runtime"


_SOURCE_FIRST_ACTION_BOUND_CONDITION_KINDS = frozenset(
    {
        "source-requiredness",
        "source-optionalness",
        "source-format",
        "source-date-boundary",
    }
)


def _source_first_effective_condition_binding(
    assertion: SourceAssertion,
    *,
    property_kind: str,
    action_contract: str,
    base_condition_key: str,
    base_condition_precondition: str,
) -> tuple[str, str]:
    if (
        property_kind in _SOURCE_FIRST_ACTION_BOUND_CONDITION_KINDS
        and action_contract
    ):
        digest_basis: Any = {
            "condition_clauses": list(assertion.condition_clauses),
            "action_clauses": list(assertion.action_clauses),
            "property_kind": property_kind,
        }
        return (
            "condition:" + _canonical_sha256(digest_basis)[:16],
            base_condition_precondition,
        )
    return base_condition_key, base_condition_precondition


def compile_source_first_property_derivations(
    *,
    repo_root: Path,
    ft_slug: str,
    source_manifest: SourceAssertionManifest,
    obligation_set: PreparedObligationSet,
) -> CompiledPropertyDerivations:
    """Produce typed derivations directly from accepted source-first contracts.

    This is the production default for schema-v2 prepared runs.  It does not
    parse raw FT prose and does not require semantic-design bridge artifacts.
    It only projects the already accepted source assertion manifest plus the
    compiler-v3 prepared obligations into the technical coverage graph format.
    """

    repo_root = Path(repo_root).resolve()
    if not repo_root.is_dir():
        _fail("missing-repo-root", str(repo_root))
    ft_slug = _typed(ft_slug, "ft_slug")
    obligation_set.validate()

    prepared_by_id = {
        item.obligation_id: item for item in obligation_set.obligations
    }
    expected_obligations = {
        obligation_id
        for assertion in source_manifest.assertions
        if assertion.semantic_disposition == "testable"
        for obligation_id in assertion.obligation_ids
    }
    missing_prepared = expected_obligations - set(prepared_by_id)
    if missing_prepared:
        _fail(
            "obligation-set-mismatch",
            "prepared obligations are missing " + ", ".join(sorted(missing_prepared)),
        )
    assertions_by_atom = {
        assertion.atom_id: assertion for assertion in source_manifest.assertions
    }
    if len(assertions_by_atom) != len(source_manifest.assertions):
        _fail("duplicate-accepted-atom", "accepted assertions repeat an ATOM id")
    for extra_id in sorted(set(prepared_by_id) - expected_obligations):
        _validate_non_testable_prepared_context(
            prepared_by_id[extra_id], assertions_by_atom
        )

    derivations: list[PropertyDerivation] = []
    subject_labels: dict[str, str] = {}
    condition_preconditions: dict[str, str] = {}
    for assertion in source_manifest.assertions:
        if assertion.semantic_disposition != "testable":
            continue
        assertion_obligations = tuple(
            prepared_by_id[obligation_id]
            for obligation_id in assertion.obligation_ids
        )
        subject_label = _source_first_subject_label(assertion, assertion_obligations)
        if not subject_label:
            _fail("subject-label-missing", assertion.assertion_id)
        subject_key = "subject:" + hashlib.sha256(
            " ".join(subject_label.casefold().split()).encode("utf-8")
        ).hexdigest()[:16]
        existing_label = subject_labels.get(subject_key)
        if existing_label is not None and (
            " ".join(existing_label.casefold().split())
            != " ".join(subject_label.casefold().split())
        ):
            _fail(
                "subject-key-collision",
                f"{assertion.assertion_id} collides with a different subject label",
            )
        subject_labels.setdefault(subject_key, subject_label)
        base_condition_key, base_condition_precondition, complex_condition = (
            _condition_binding(assertion)
        )

        variants: dict[str, str] = {}
        source_oracles: dict[str, str] = {}
        fixtures_by_obligation: dict[str, tuple[str, ...]] = {}
        questions: dict[str, str] = {}
        property_kinds: set[str] = set()
        action_contract = "; ".join(assertion.action_clauses)
        expected_oracle = "; ".join(assertion.oracle_clauses)
        for obligation_id in assertion.obligation_ids:
            prepared = prepared_by_id[obligation_id]
            if prepared.traceability_atom_id != assertion.atom_id:
                _fail(
                    "obligation-chain-drift",
                    f"{obligation_id} is outside its accepted ASSERT/ATOM chain",
                )
            if prepared.observable_oracle != expected_oracle:
                _fail(
                    "prepared-oracle-drift",
                    f"{obligation_id} oracle differs from accepted source clauses",
                )
            fixtures = _source_first_fixture_values(repo_root, prepared)
            property_kind, variant = _source_first_kind_and_variant(
                assertion=assertion,
                obligation=prepared,
                fixtures=fixtures,
                complex_condition=complex_condition,
            )
            if property_kind == "source-format" and variant == "length-limit":
                exact_length_values = exact_numeric_length_representatives(
                    _source_first_text(
                        assertion.exact_source_text,
                        assertion.canonical_statement,
                        *assertion.action_clauses,
                        *assertion.oracle_clauses,
                        prepared.atomic_statement,
                        prepared.observable_oracle,
                        prepared.test_intent,
                    )
                )
                if exact_length_values:
                    fixtures = exact_length_values
                    if len(exact_length_values) >= 3 and not expected_oracle:
                        source_oracles[obligation_id] = "SO-CAL-" + hashlib.sha256(
                            obligation_id.encode("utf-8")
                        ).hexdigest()[:16].upper()
                        questions[obligation_id] = (
                            expected_oracle or prepared.atomic_statement
                        )
            if property_kind == "source-format" and variant == "digits-only":
                digit_class_values = _source_first_digits_only_fixture_values(
                    assertion.exact_source_text,
                    assertion.canonical_statement,
                    *assertion.action_clauses,
                    *assertion.oracle_clauses,
                    prepared.atomic_statement,
                    prepared.observable_oracle,
                    prepared.test_intent,
                )
                if digit_class_values:
                    fixtures = digit_class_values
            if property_kind == "source-date-boundary" and variant == "date-window":
                date_window_text = _source_first_text(
                    assertion.exact_source_text,
                    assertion.canonical_statement,
                    *assertion.condition_clauses,
                    *assertion.action_clauses,
                    *assertion.oracle_clauses,
                    prepared.atomic_statement,
                    prepared.observable_oracle,
                    prepared.test_intent,
                )
                date_window_values = _source_first_date_window_fixture_values(
                    date_window_text,
                )
                if date_window_values:
                    fixtures = date_window_values
                    source_oracles[obligation_id] = "SO-CAL-" + hashlib.sha256(
                        obligation_id.encode("utf-8")
                    ).hexdigest()[:16].upper()
                    questions[obligation_id] = (
                        _source_first_positive_date_window_question(
                            subject_label=subject_label,
                            fixtures=date_window_values[:1],
                            fallback=prepared.atomic_statement,
                        )
                    )
                if any(
                    token in date_window_text
                    for token in ("бессроч", "не применяется")
                ):
                    source_oracles.setdefault(
                        obligation_id,
                        "SO-CAL-" + hashlib.sha256(
                            obligation_id.encode("utf-8")
                        ).hexdigest()[:16].upper(),
                    )
                    questions[obligation_id] = _source_first_positive_date_window_question(
                        subject_label=subject_label,
                        fixtures=fixtures,
                        fallback=prepared.atomic_statement,
                    )
                elif not expected_oracle:
                    source_oracles[obligation_id] = "SO-CAL-" + hashlib.sha256(
                        obligation_id.encode("utf-8")
                    ).hexdigest()[:16].upper()
                    questions[obligation_id] = (
                        expected_oracle or prepared.atomic_statement
                    )
            if property_kind == "source-date-boundary" and variant == "not-future":
                fixtures = _date_boundary_fixture_values()
            if property_kind == "default":
                default_values = _source_first_default_fixture_values(
                    expected_oracle,
                    prepared.observable_oracle,
                    assertion.canonical_statement,
                    prepared.atomic_statement,
                )
                if default_values:
                    fixtures = default_values
            variants[obligation_id] = variant
            if fixtures:
                fixtures_by_obligation[obligation_id] = fixtures
            property_kinds.add(property_kind)
            if (
                prepared.calibration_status == "ui-calibration-required"
                and obligation_id not in source_oracles
            ):
                source_oracles[obligation_id] = "SO-CAL-" + hashlib.sha256(
                    obligation_id.encode("utf-8")
                ).hexdigest()[:16].upper()
                question = expected_oracle or prepared.atomic_statement
                if not question:
                    _fail("calibration-question-missing", obligation_id)
                questions[obligation_id] = question
            elif _needs_validation_trigger_calibration(
                polarity=assertion.polarity,
                oracle=expected_oracle,
                action=action_contract,
            ) and not _source_first_has_explicit_validation_action(action_contract):
                source_oracles[obligation_id] = "SO-CAL-" + hashlib.sha256(
                    obligation_id.encode("utf-8")
                ).hexdigest()[:16].upper()
                questions[obligation_id] = expected_oracle or prepared.atomic_statement
        if len(property_kinds) != 1:
            _fail(
                "mixed-property-kind",
                f"{assertion.assertion_id} maps incompatible obligation kinds",
            )
        property_kind = next(iter(property_kinds))
        condition_key, condition_precondition = (
            _source_first_effective_condition_binding(
                assertion,
                property_kind=property_kind,
                action_contract=action_contract,
                base_condition_key=base_condition_key,
                base_condition_precondition=base_condition_precondition,
            )
        )
        if condition_key != "always":
            existing_condition = condition_preconditions.get(condition_key)
            if (
                existing_condition is not None
                and existing_condition != condition_precondition
            ):
                _fail(
                    "condition-key-collision",
                    f"{assertion.assertion_id} collides with a different condition",
                )
            condition_preconditions.setdefault(
                condition_key, condition_precondition
            )
        derivations.append(
            PropertyDerivation(
                source_manifest_digest=source_manifest.digest,
                obligation_set_digest=obligation_set.digest,
                assertion_id=assertion.assertion_id,
                source_row_id=assertion.source_row_id,
                atom_id=assertion.atom_id,
                source_text_sha256=hashlib.sha256(
                    assertion.exact_source_text.encode("utf-8")
                ).hexdigest(),
                property_key=f"property:{assertion.assertion_id}",
                subject_key=subject_key,
                property_kind=property_kind,
                obligation_variants=variants,
                condition_key=condition_key,
                validation_trigger=_effective_validation_trigger(
                    property_kind=property_kind,
                    action_contract=action_contract,
                ),
                cleanup_strategy="",
                source_oracle_ids=source_oracles or None,
                fixture_values=fixtures_by_obligation or None,
                calibration_questions=questions or None,
            )
        )

    document = PropertyDerivationDocument(
        schema_version=1,
        ft_slug=ft_slug,
        scope_slug=source_manifest.scope_slug,
        source_manifest_digest=source_manifest.digest,
        obligation_set_digest=obligation_set.digest,
        derivations=tuple(derivations),
    )
    _canonical_sha256(document.to_dict())
    return CompiledPropertyDerivations(
        document=document,
        registered_artifacts=(),
        subject_labels=dict(sorted(subject_labels.items())),
        condition_preconditions=dict(sorted(condition_preconditions.items())),
        scope_title=_source_first_scope_title(repo_root, source_manifest),
        base_preconditions=(),
        registered_artifact_snapshots=(),
    )


def compile_property_derivations(
    *,
    repo_root: Path,
    ft_slug: str,
    source_manifest: SourceAssertionManifest,
    obligation_set: PreparedObligationSet,
    semantic_projection: Mapping[str, Any],
) -> CompiledPropertyDerivations:
    """Produce typed derivations from the compiler's hash-bound semantic handoff.

    This function never parses FT prose into new behavior.  It checks the
    semantic artifact against the independently accepted source manifest and
    projects only already compiled field labels, fixtures, dictionaries and
    calibration ownership.
    """

    repo_root = Path(repo_root).resolve()
    if not repo_root.is_dir():
        _fail("missing-repo-root", str(repo_root))
    ft_slug = _typed(ft_slug, "ft_slug")
    obligation_set.validate()
    if semantic_projection.get("contract") != SEMANTIC_PROJECTION_CONTRACT:
        _fail("semantic-projection-contract", "unsupported semantic projection")

    semantic_path, semantic_spec, semantic_raw = _repo_artifact(
        repo_root,
        semantic_projection.get("semantic_design_artifact"),
        "semantic_design_artifact",
    )
    boundary_path, _, boundary_raw = _repo_artifact(
        repo_root,
        semantic_projection.get("scope_boundary_artifact"),
        "scope_boundary_artifact",
    )
    receipt_path, _, receipt_raw = _repo_artifact(
        repo_root,
        semantic_projection.get("bridge_receipt_artifact"),
        "bridge_receipt_artifact",
    )
    semantic_payload = _read_json_object_bytes(semantic_raw, "semantic design")
    if (
        semantic_payload.get("version") != 4
        or semantic_payload.get("contract") != "semantic-design-bridge-v2"
        or semantic_payload.get("status") != "ready"
    ):
        _fail("semantic-design-status", "semantic design is not ready v4")
    receipt_payload = _read_json_object_bytes(
        receipt_raw, "semantic bridge receipt"
    )
    projection_receipt = _object(
        semantic_projection.get("bridge_receipt"), "projection bridge_receipt"
    )
    if receipt_payload != projection_receipt:
        _fail("bridge-receipt-drift", "embedded receipt differs from its artifact")
    if (
        receipt_payload.get("status") != "verified"
        or receipt_payload.get("source_assertion_manifest_digest")
        != source_manifest.digest
        or receipt_payload.get("semantic_design_artifact_sha256")
        != semantic_spec.get("sha256")
        or receipt_payload.get("semantic_design_decision_sha256")
        != semantic_spec.get("decision_sha256")
    ):
        _fail(
            "bridge-receipt-binding",
            "semantic receipt is not bound to the accepted manifest/artifact",
        )

    raw_semantic_obligations = _array(
        semantic_payload.get("obligations"), "semantic design obligations"
    )
    if raw_semantic_obligations != semantic_projection.get("obligations"):
        _fail(
            "semantic-obligation-drift",
            "embedded obligations differ from the hash-bound semantic artifact",
        )
    raw_by_obligation: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(raw_semantic_obligations):
        item = _object(raw, f"semantic obligations[{index}]")
        obligation_id = _typed(item.get("obligation_id"), "obligation_id")
        if obligation_id in raw_by_obligation:
            _fail("duplicate-semantic-obligation", obligation_id)
        raw_by_obligation[obligation_id] = item

    prepared_by_id = {
        item.obligation_id: item for item in obligation_set.obligations
    }
    expected_obligations = {
        obligation_id
        for assertion in source_manifest.assertions
        if assertion.semantic_disposition == "testable"
        for obligation_id in assertion.obligation_ids
    }
    if set(raw_by_obligation) != expected_obligations:
        _fail(
            "obligation-set-mismatch",
            "semantic obligation set must equal accepted testable assertions",
        )
    format_calibration_signals = _validate_source_signal_accounting(
        repo_root=repo_root,
        manifest=source_manifest,
        obligation_set=obligation_set,
        projection=semantic_projection,
        expected_obligations=expected_obligations,
        semantic_obligations=raw_by_obligation,
    )
    missing_prepared = expected_obligations - set(prepared_by_id)
    if missing_prepared:
        _fail(
            "obligation-set-mismatch",
            "prepared obligations are missing " + ", ".join(sorted(missing_prepared)),
        )
    assertions_by_atom = {
        assertion.atom_id: assertion for assertion in source_manifest.assertions
    }
    if len(assertions_by_atom) != len(source_manifest.assertions):
        _fail("duplicate-accepted-atom", "accepted assertions repeat an ATOM id")
    for extra_id in sorted(set(prepared_by_id) - expected_obligations):
        _validate_non_testable_prepared_context(
            prepared_by_id[extra_id], assertions_by_atom
        )

    semantic_assertions = _semantic_assertions(semantic_payload)
    accepted_assertions = {
        item.assertion_id: item for item in source_manifest.assertions
    }
    if set(semantic_assertions) != set(accepted_assertions):
        _fail(
            "assertion-set-mismatch",
            "semantic assertion set differs from accepted source manifest",
        )
    labels = {
        assertion_id: _validate_assertion_projection(
            assertion,
            semantic_assertions[assertion_id],
            require_bound_subject=assertion.semantic_disposition == "testable",
        )
        for assertion_id, assertion in accepted_assertions.items()
    }
    block_assertion_ids = {
        assertions_by_atom[str(item.get("linked_atom_id", ""))].assertion_id
        for item in raw_by_obligation.values()
        if str(item.get("property_type", "")).casefold()
        in {"structure", "block-structure"}
        and str(item.get("linked_atom_id", "")) in assertions_by_atom
    }
    if len(block_assertion_ids) == 1:
        block_assertion_id = next(iter(block_assertion_ids))
        scope_title = _text(
            semantic_assertions[block_assertion_id].get("field_or_block"),
            f"{block_assertion_id}.field_or_block",
        )
        base_preconditions = tuple(
            accepted_assertions[block_assertion_id].condition_clauses
        )
    else:
        # Scope slug is non-behavioral identity and cannot inject UI semantics.
        scope_title = source_manifest.scope_slug
        base_preconditions = ()
    oracle_ids, oracle_questions = _oracle_bindings(semantic_projection)
    unknown_oracle_obligations = set(oracle_ids) - expected_obligations
    if unknown_oracle_obligations:
        _fail(
            "unknown-obligation-oracle",
            ", ".join(sorted(unknown_oracle_obligations)),
        )

    registered_artifacts: list[Path] = [
        semantic_path,
        boundary_path,
        receipt_path,
    ]
    registered_snapshots: list[tuple[Path, str, int]] = [
        (
            semantic_path,
            hashlib.sha256(semantic_raw).hexdigest(),
            len(semantic_raw),
        ),
        (
            boundary_path,
            hashlib.sha256(boundary_raw).hexdigest(),
            len(boundary_raw),
        ),
        (
            receipt_path,
            hashlib.sha256(receipt_raw).hexdigest(),
            len(receipt_raw),
        ),
    ]
    for index, raw_inventory in enumerate(
        _array(semantic_projection.get("oracle_inventories"), "oracle_inventories")
    ):
        inventory = _object(raw_inventory, f"oracle_inventories[{index}]")
        path, _, inventory_raw = _repo_artifact(
            repo_root, inventory, f"oracle_inventories[{index}]"
        )
        try:
            text = inventory_raw.decode("utf-8")
        except UnicodeError as exc:
            _fail("invalid-oracle-inventory-utf8", f"{path}: {exc}")
        if text != inventory.get("utf8_text"):
            _fail("oracle-inventory-drift", str(path))
        registered_artifacts.append(path)
        registered_snapshots.append(
            (path, hashlib.sha256(inventory_raw).hexdigest(), len(inventory_raw))
        )

    derivations: list[PropertyDerivation] = []
    subject_labels: dict[str, str] = {}
    condition_preconditions: dict[str, str] = {}
    for assertion in source_manifest.assertions:
        if assertion.semantic_disposition != "testable":
            continue
        semantic_assertion = semantic_assertions[assertion.assertion_id]
        subject_label = labels[assertion.assertion_id]
        subject_key = "subject:" + hashlib.sha256(
            " ".join(subject_label.casefold().split()).encode("utf-8")
        ).hexdigest()[:16]
        existing_label = subject_labels.get(subject_key)
        if existing_label is not None and (
            " ".join(existing_label.casefold().split())
            != " ".join(subject_label.casefold().split())
        ):
            _fail(
                "subject-key-collision",
                f"{assertion.assertion_id} collides with a different subject label",
            )
        subject_labels.setdefault(subject_key, subject_label)
        condition_key, condition_precondition, complex_condition = (
            _condition_binding(assertion)
        )
        if condition_key != "always":
            existing_condition = condition_preconditions.get(condition_key)
            if (
                existing_condition is not None
                and existing_condition != condition_precondition
            ):
                _fail(
                    "condition-key-collision",
                    f"{assertion.assertion_id} collides with a different condition",
                )
            condition_preconditions.setdefault(
                condition_key, condition_precondition
            )
        variants: dict[str, str] = {}
        source_oracles: dict[str, str] = {}
        fixtures_by_obligation: dict[str, tuple[str, ...]] = {}
        questions: dict[str, str] = {}
        property_kinds: set[str] = set()
        action_contract = "; ".join(assertion.action_clauses)
        for obligation_id in assertion.obligation_ids:
            prepared = prepared_by_id[obligation_id]
            semantic = raw_by_obligation[obligation_id]
            if (
                semantic.get("linked_atom_id") != assertion.atom_id
                or prepared.traceability_atom_id != assertion.atom_id
                or semantic.get("package_id") != obligation_set.package_id
            ):
                _fail(
                    "obligation-chain-drift",
                    f"{obligation_id} is outside its accepted ASSERT/ATOM/package chain",
                )
            expected_oracle = "; ".join(assertion.oracle_clauses)
            if prepared.observable_oracle != expected_oracle:
                _fail(
                    "prepared-oracle-drift",
                    f"{obligation_id} oracle differs from accepted source clauses",
                )
            fixtures = _fixture_values(semantic, prepared)
            derived_signals = format_calibration_signals.get(obligation_id, ())
            if derived_signals:
                derived_values = tuple(
                    dict.fromkeys(
                        str(signal.get("representative_invalid_value", "")).strip()
                        for signal in derived_signals
                        if str(
                            signal.get("representative_invalid_value", "")
                        ).strip()
                    )
                )
                fixtures = tuple(dict.fromkeys((*fixtures, *derived_values)))
            variant = _typed(
                semantic.get("coverage_class"),
                f"{obligation_id}.coverage_class",
            )
            variants[obligation_id] = variant
            if fixtures:
                fixtures_by_obligation[obligation_id] = fixtures
            property_kinds.add(
                _safe_property_kind(
                    semantic,
                    fixtures,
                    force_writer_for_complex_condition=complex_condition,
                )
            )
            if obligation_id in oracle_ids:
                source_oracles[obligation_id] = oracle_ids[obligation_id]
            if derived_signals:
                signal_ids = tuple(
                    str(signal.get("signal_id", ""))
                    for signal in derived_signals
                )
                source_oracles[obligation_id] = (
                    "SO-CAL-SIGNAL-"
                    + hashlib.sha256(
                        "\u001f".join((obligation_id, *signal_ids)).encode("utf-8")
                    ).hexdigest()[:12].upper()
                )
                negative_classes = ", ".join(
                    str(signal.get("negative_class", "")).strip()
                    or str(signal.get("restriction_type", "")).strip()
                    for signal in derived_signals
                )
                invalid_values = ", ".join(f"«{value}»" for value in derived_values)
                questions[obligation_id] = (
                    "Какой точный UI-отклик подтверждает, что для "
                    f"«{subject_label.strip('«»')}» недопустимые классы "
                    f"{negative_classes} со значениями {invalid_values} "
                    "не принимаются по правилу ФТ?"
                )
            if prepared.calibration_status == "ui-calibration-required":
                if obligation_id not in source_oracles:
                    if (
                        semantic.get("obligation_class")
                        != "candidate-ui-calibration"
                        or semantic.get("oracle_source") != "not_found"
                        or semantic.get("scope_obligation_ids") != []
                    ):
                        _fail(
                            "unbound-direct-calibration",
                            f"{obligation_id} has no explicit direct candidate contract",
                        )
                    # Direct candidates intentionally have no NEG/REQ oracle
                    # inventory row.  Give their already explicit calibration
                    # ownership a deterministic typed identity; this is an ID,
                    # not an invented product oracle.
                    source_oracles[obligation_id] = "SO-CAL-" + hashlib.sha256(
                        obligation_id.encode("utf-8")
                    ).hexdigest()[:16].upper()
                question = oracle_questions.get(obligation_id) or expected_oracle
                if not question:
                    _fail("calibration-question-missing", obligation_id)
                questions[obligation_id] = question
            elif (
                obligation_id in oracle_questions
                and semantic.get("oracle_source") == "not_found"
            ):
                _fail(
                    "unexpected-calibration-question",
                    f"{obligation_id} has a question without calibration status",
                )
            elif _needs_validation_trigger_calibration(
                polarity=assertion.polarity,
                oracle=expected_oracle,
                action=action_contract,
            ):
                # Never invent a Save, Continue or blur trigger.  Preserve the
                # requirement in the same suite as a calibration candidate.
                source_oracles.setdefault(
                    obligation_id,
                    "SO-CAL-"
                    + hashlib.sha256(obligation_id.encode("utf-8"))
                    .hexdigest()[:16]
                    .upper(),
                )
                target = f"элемента «{subject_label.strip('«»')}»"
                value = fixtures[0] if fixtures else "указанного значения"
                outcome = _calibration_outcome(assertion.polarity)
                questions[obligation_id] = (
                    "Какое точное действие запускает проверку значения "
                    f"«{value}» для {target} и какой точный наблюдаемый "
                    f"UI-отклик подтверждает {outcome}?"
                )
            elif _needs_requiredness_calibration(
                property_type=str(semantic.get("property_type", "")).casefold(),
                action=action_contract,
            ):
                source_oracles.setdefault(
                    obligation_id,
                    "SO-CAL-"
                    + hashlib.sha256(obligation_id.encode("utf-8"))
                    .hexdigest()[:16]
                    .upper(),
                )
                if not fixtures:
                    fixtures = ("пустое значение",)
                    fixtures_by_obligation[obligation_id] = fixtures
                target = f"элемента «{subject_label.strip('«»')}»"
                questions[obligation_id] = (
                    "Какое точное действие запускает проверку пустого значения "
                    f"для {target} и какой точный наблюдаемый UI-отклик "
                    "подтверждает обязательность или необязательность?"
                )
            elif _needs_date_boundary_calibration(
                property_type=str(semantic.get("property_type", "")).casefold(),
                coverage_class=variant.casefold(),
                statement=prepared.atomic_statement,
                oracle=expected_oracle,
                action=action_contract,
            ):
                source_oracles.setdefault(
                    obligation_id,
                    "SO-CAL-"
                    + hashlib.sha256(obligation_id.encode("utf-8"))
                    .hexdigest()[:16]
                    .upper(),
                )
                fixtures = _date_boundary_fixture_values()
                fixtures_by_obligation[obligation_id] = fixtures
                target = f"элемента «{subject_label.strip('«»')}»"
                questions[obligation_id] = (
                    "Какой точный UI-отклик подтверждает, что для "
                    f"{target} значение `текущая дата + 1 день` не "
                    "принимается, и какое действие запускает эту проверку?"
                )
        if len(property_kinds) != 1:
            _fail(
                "mixed-property-kind",
                f"{assertion.assertion_id} maps incompatible obligation kinds",
            )
        property_kind = next(iter(property_kinds))
        derivations.append(
            PropertyDerivation(
                source_manifest_digest=source_manifest.digest,
                obligation_set_digest=obligation_set.digest,
                assertion_id=assertion.assertion_id,
                source_row_id=assertion.source_row_id,
                atom_id=assertion.atom_id,
                source_text_sha256=hashlib.sha256(
                    assertion.exact_source_text.encode("utf-8")
                ).hexdigest(),
                property_key=f"property:{assertion.assertion_id}",
                subject_key=subject_key,
                property_kind=property_kind,
                obligation_variants=variants,
                condition_key=condition_key,
                # A default is observed in the accepted initial condition.
                # Treating a generated focus/click action as its trigger changes
                # the state being specified and contradicts "по умолчанию".
                validation_trigger=_effective_validation_trigger(
                    property_kind=property_kind,
                    action_contract=action_contract,
                ),
                cleanup_strategy="",
                source_oracle_ids=source_oracles or None,
                fixture_values=fixtures_by_obligation or None,
                calibration_questions=questions or None,
            )
        )

    document = PropertyDerivationDocument(
        schema_version=1,
        ft_slug=ft_slug,
        scope_slug=source_manifest.scope_slug,
        source_manifest_digest=source_manifest.digest,
        obligation_set_digest=obligation_set.digest,
        derivations=tuple(derivations),
    )
    # Force the same deterministic serializer used by persisted coverage inputs.
    _canonical_sha256(document.to_dict())
    for path, expected_hash, expected_size in registered_snapshots:
        try:
            current = path.read_bytes()
        except OSError as exc:
            _fail("artifact-drift", f"registered artifact disappeared: {path}: {exc}")
        if (
            len(current) != expected_size
            or hashlib.sha256(current).hexdigest() != expected_hash
        ):
            _fail(
                "artifact-drift",
                f"registered artifact changed during compilation: {path}",
            )
    return CompiledPropertyDerivations(
        document=document,
        registered_artifacts=tuple(dict.fromkeys(registered_artifacts)),
        subject_labels=dict(sorted(subject_labels.items())),
        condition_preconditions=dict(sorted(condition_preconditions.items())),
        scope_title=scope_title,
        base_preconditions=base_preconditions,
        registered_artifact_snapshots=tuple(registered_snapshots),
    )


__all__ = [
    "CompiledPropertyDerivations",
    "DerivationCompilationError",
    "SEMANTIC_PROJECTION_CONTRACT",
    "compile_property_derivations",
    "compile_source_first_property_derivations",
    "extract_optional_semantic_compiler_projection",
    "extract_semantic_compiler_projection",
]
