from __future__ import annotations

import hashlib
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
    "extract_semantic_compiler_projection",
]
