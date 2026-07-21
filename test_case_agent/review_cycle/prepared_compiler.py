from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .prepared_package import (
    EvidenceInput,
    PreparedGap,
    PreparedExecutionDependency,
    PreparedReleaseStatus,
    PreparedDictionaryRequirement,
    PreparedDictionaryValue,
    PreparedObligation,
    PreparedObligationSet,
    PreparedStateChange,
    PreparedPackageBuilder,
    StageInstructionConfig,
    FAST_EVIDENCE_MAX_BYTES,
    STANDARD_ROUTING_EVIDENCE_MAX_BYTES,
)
from .coverage_accounting import (
    ASSERTION_COVERAGE_FLOOR,
    CRITICAL_COVERAGE_FLOOR,
    OVERALL_COVERAGE_FLOOR,
    CoverageObligationMetadata,
    evaluate_coverage_accounting,
)
from .dimension_bindings import (
    ReviewerDimensionSourceBindings,
    render_reviewer_dimension_source_bindings,
)
from .runtime import StageRuntimeError
from .source_assertions import (
    SourceAssertionContractError,
    SourceAssertionManifest,
    SourceRow,
    load_source_assertion_manifest,
    load_source_assertion_review_receipt,
    render_embedded_source_assertion_contract,
)
from .source_row_baseline import (
    SourceRowBaselineValidationError,
    SourceRowCandidateMapping,
    SourceRowCompletenessResult,
    load_extraction_spec,
    validate_source_row_completeness,
)


TOKEN = re.compile(
    r"\b(?:ATOM|OBL|GAP|DICT|SRC)-[A-Za-z0-9_.-]+\b|\b(?:GSR|BSR|DIT)\s+\d+\b"
)
DEPENDENCY_ID = re.compile(r"DEP-[A-Za-z0-9._-]+")
TC_TOKEN = re.compile(r"\bTC-[A-Za-z0-9_.-]+\b")
CANDIDATE_SCOPE_OBLIGATION = re.compile(
    r"^candidate:(SO-(?:NEG|REQ)-[A-Za-z0-9_.-]+)$",
    flags=re.IGNORECASE,
)
FIXTURE_TOKEN = re.compile(r"\b(?:FX|FIX)-[A-Za-z0-9_.-]+\b")
PORTABLE_FIXTURE_FIELD = re.compile(
    r"\b(?P<key>request_parameters|expected_response|response_sha256|status|"
    r"runtime_api_call|product_input)=`(?P<value>[^`]*)`"
)
ACTION_LITERAL = re.compile(r"«(?P<guillemet>[^»]+)»|`(?P<backtick>[^`]+)`")
BYTE_VALUE = re.compile(
    r"\b\d[\d\s.,_]*\s*(?:байт(?:а|ов)?|bytes?)\b", flags=re.IGNORECASE
)
COMPILER_CONTRACT_VERSION = 3
SUPPORTED_COMPILER_CONTRACT_VERSIONS = {2, COMPILER_CONTRACT_VERSION}
SECTION_PREFIX = re.compile(r"^(?P<section>(?:section-)?\d+(?:[-.]\d+)*)-")
FAST_PROFILE = "simple-field-property"
STANDARD_PROFILE = "standard-required"
SOURCE_FIRST_IMMUTABLE_EVIDENCE_MAX_BYTES = 2 * 1024 * 1024
SOURCE_FIRST_PACKAGE_MAX_BYTES = 3 * 1024 * 1024
RELEASE_OUTPUT_MODE = "release"
DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE = "draft-with-blocking-gaps"
OUTPUT_MODES = {RELEASE_OUTPUT_MODE, DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE}
_DRAFT_PERMITTED_RELEASE_ONLY_FINDINGS = {
    OVERALL_COVERAGE_FLOOR,
    ASSERTION_COVERAGE_FLOOR,
    CRITICAL_COVERAGE_FLOOR,
}
FAST_DIMENSIONS = {
    "default-state",
    "default-value",
    "dictionary",
    "editability",
    "field-property",
    "list-or-dictionary-composition",
    "other",
    "positive-acceptance",
    "requiredness",
    "selection-cardinality",
    "table-list",
}
DIMENSION_GROUPS = {
    "conditional-visibility": "dependency-state",
    "date-time": "numeric-boundaries",
    "dependency": "dependency-state",
    "equivalence": "input-boundaries",
    "format": "input-boundaries",
    "integration": "integration-persistence",
    "length": "numeric-boundaries",
    "numeric": "numeric-boundaries",
    "persistence": "integration-persistence",
    "state": "dependency-state",
    "table-parity": "table-parity",
}
OBLIGATION_DIMENSION_GROUPS = {
    "action-confirmation": "dependency-state",
    "action-navigation": "state-transition-or-navigation",
    "async": "integration-persistence",
    "calculation": "numeric-boundaries",
    "conditional-visibility": "dependency-state",
    "dependency": "dependency-state",
    "exact-length": "numeric-boundaries",
    "file-upload": "file-upload",
    "format-mask": "numeric-boundaries",
    "generated-document": "generated-document",
    "integration": "integration-persistence",
    "numeric-format": "numeric-boundaries",
    "persistence": "integration-persistence",
    "print-form-output": "generated-document",
    "repeatable-block": "repeatable-lifecycle",
}

ABSTRACT_INPUT_CLASSES = {
    "input",
    "text",
    "string",
    "valid-input",
    "valid-text",
    "valid-string",
    "valid-value",
    "invalid-input",
    "invalid-text",
    "invalid-string",
    "invalid-value",
}
INPUT_ACTION = re.compile(
    r"\b(?:enter|fill|input|type|ввести|ввод|заполнить|указать)\b",
    flags=re.IGNORECASE,
)
CONCRETE_INLINE_VALUE = re.compile(r"`[^`\r\n]+`")
GENERIC_FIXTURE_VALUE = re.compile(
    r"(?:"
    r"валидн\w*\s+заявк\w*|"
    r"значени\w*\s+заявк\w*\s+необходим\w*\s+для\s+сохран|"
    r"подсказк\w*\s+фио\s+с\s+пол\w*|"
    r"дат\w*\s+в\s+допустим\w*\s+диапазон\w*|"
    r"(?:остальн|ин)\w*(?:\s+\w+){0,4}\s+"
    r"(?:required\s+controls?|обязательн\w*\s+(?:пол\w*|контрол\w*))|"
    r"all\s+other\s+required\s+(?:fields?|controls?)|"
    r"valid\s+application|values?\s+(?:needed|required)\s+to\s+save"
    r")",
    flags=re.IGNORECASE,
)
ENVIRONMENT_BOUND_FIXTURE = re.compile(
    r"(?:"
    r"stand-accepted|stand-registered|environment-registered|"
    r"стендов\w*\s+(?:id|идентификатор|запис\w*|заявк\w*)|"
    r"заранее\s+зарегистрирован\w*\s+(?:на\s+)?стенд\w*"
    r")",
    flags=re.IGNORECASE,
)
UNDEFINED_EXECUTION_ACTION = re.compile(
    r"(?:"
    r"(?:попытаться|попытк\w*|продолжить)\s+(?:дальнейш\w*\s+)?сценар\w*|"
    r"attempt(?:\s+to)?\s+(?:continue|proceed)\s+(?:the\s+)?scenario"
    r")",
    flags=re.IGNORECASE,
)
UNKNOWN_REQUIREDNESS_ORACLE = re.compile(
    r"(?:точн\w*|конкретн\w*)\s+ui[- ]реакц\w*\s+"
    r"(?:не\s+определ\w*|подлежит\s+калибровк\w*)",
    flags=re.IGNORECASE,
)
EVIDENCE_CAPTURE = re.compile(
    r"зафиксир\w*|записать\s+фактич\w*|"
    r"скриншот|доказательств\w*|evidence|capture|record\s+the\s+actual",
    flags=re.IGNORECASE,
)
RESET_EXECUTION_SEMANTICS = "reset-to-captured-initial"
STATE_CHANGE_RELATION = "different-from-captured-initial"
STATE_CHANGE_PLAN_FIELDS = (
    "initial_state_capture",
    "changed_state_setup",
    "pre_action_state_oracle",
    "state_relation",
)
SOURCE_CONDITION_STATE_BINDING = re.compile(
    r"source-condition:(?P<index>0|[1-9][0-9]*)\Z",
    flags=re.IGNORECASE,
)
DICTIONARY_COVERAGE_MODES = {
    "reference-only",
    "all-leaf-values",
    "full-hierarchy",
}
LEGACY_DICTIONARY_COVERAGE_BY_CLASS = {
    "dictionary-hierarchy-shown": "full-hierarchy",
    "dictionary-values-shown": "all-leaf-values",
    "value-has-checkbox": "all-leaf-values",
}


def _normalized_design_value(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def _external_dynamic_dictionary_dependencies_by_obligation(
    semantic_projection: Mapping[str, Any] | None,
) -> dict[str, tuple[str, ...]]:
    """Project authoritative external-dynamic dictionary bindings into writer inputs."""

    if semantic_projection is None:
        return {}
    bindings = semantic_projection.get("dependency_bindings")
    if not isinstance(bindings, list):
        raise StageRuntimeError(
            "semantic compiler projection dependency_bindings are invalid"
        )
    result: dict[str, list[str]] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping):
            raise StageRuntimeError("semantic dependency binding must be an object")
        if (
            binding.get("kind") != "dictionary"
            or binding.get("resolution") != "external-dynamic"
        ):
            continue
        dependency_id = str(binding.get("dependency_id", ""))
        if not DEPENDENCY_ID.fullmatch(dependency_id):
            raise StageRuntimeError(
                "external-dynamic dictionary dependency must have a stable DEP-* id"
            )
        obligation_ids = binding.get("linked_obligation_ids")
        if not isinstance(obligation_ids, list) or not obligation_ids:
            raise StageRuntimeError(
                f"external-dynamic dictionary dependency {dependency_id} must link obligations"
            )
        for obligation_id in obligation_ids:
            if not isinstance(obligation_id, str) or not obligation_id:
                raise StageRuntimeError(
                    f"external-dynamic dictionary dependency {dependency_id} has an invalid obligation id"
                )
            result.setdefault(obligation_id, []).append(dependency_id)
    return {
        obligation_id: tuple(dict.fromkeys(dependency_ids))
        for obligation_id, dependency_ids in result.items()
    }


def _dictionary_coverage_mode(obligation_row: Mapping[str, str]) -> str:
    explicit = obligation_row.get("dictionary_coverage", "").strip().lower()
    if explicit:
        if explicit not in DICTIONARY_COVERAGE_MODES:
            raise StageRuntimeError(
                "semantic degradation: dictionary_coverage must be one of "
                + ", ".join(sorted(DICTIONARY_COVERAGE_MODES))
            )
        return explicit
    obligation_class = _normalized_design_value(
        obligation_row.get("obligation_class", "")
    )
    return LEGACY_DICTIONARY_COVERAGE_BY_CLASS.get(
        obligation_class,
        "reference-only",
    )


def _dedicated_exhaustive_dictionary_ids(
    obligation_rows: Sequence[Mapping[str, str]],
) -> frozenset[str]:
    """Return dictionaries whose exhaustive coverage has a dedicated obligation."""

    result: set[str] = set()
    for row in obligation_rows:
        property_type = _normalized_design_value(row.get("property_type", ""))
        obligation_class = _normalized_design_value(
            row.get("obligation_class", "")
        )
        if not (
            property_type == "dictionary"
            or obligation_class in {
                "dictionary-values",
                "dictionary-values-shown",
                "dictionary-hierarchy-shown",
            }
        ):
            continue
        if _dictionary_coverage_mode(row) == "reference-only":
            continue
        references = " ".join(
            (row.get("dictionary_refs", ""), row.get("source_ref", ""))
        )
        result.update(
            token for token in TOKEN.findall(references) if token.startswith("DICT-")
        )
    return frozenset(result)


def _effective_dictionary_coverage_mode(
    obligation_row: Mapping[str, str],
    *,
    dictionary_id: str,
    dedicated_exhaustive_dictionary_ids: frozenset[str],
) -> str:
    mode = _dictionary_coverage_mode(obligation_row)
    property_type = _normalized_design_value(
        obligation_row.get("property_type", "")
    )
    obligation_class = _normalized_design_value(
        obligation_row.get("obligation_class", "")
    )
    is_dedicated_dictionary_obligation = (
        property_type == "dictionary"
        or obligation_class
        in {
            "dictionary-values",
            "dictionary-values-shown",
            "dictionary-hierarchy-shown",
        }
    )
    if (
        mode != "reference-only"
        and not is_dedicated_dictionary_obligation
        and dictionary_id in dedicated_exhaustive_dictionary_ids
    ):
        return "reference-only"
    return mode


def _compile_dictionary_requirement(
    *,
    dictionary_id: str,
    coverage_mode: str,
    dictionary_rows: Mapping[str, Mapping[str, str]],
    dictionary_active_values: Mapping[str, tuple[str, ...]],
    reference_fixture_text: str = "",
) -> PreparedDictionaryRequirement:
    values: list[PreparedDictionaryValue] = []

    def visit(current_id: str, path: tuple[str, ...], visiting: frozenset[str]) -> None:
        if current_id in visiting:
            raise StageRuntimeError(
                f"semantic degradation: cyclic dictionary hierarchy at {current_id}"
            )
        next_visiting = visiting | {current_id}
        for raw_value in dictionary_active_values[current_id]:
            if raw_value.startswith("none_required:"):
                continue
            if raw_value.startswith("DICT-"):
                if raw_value not in dictionary_rows:
                    raise StageRuntimeError(
                        f"semantic degradation: {current_id} references missing child {raw_value}"
                    )
                child_path = (*path, raw_value)
                if coverage_mode in {"full-hierarchy", "reference-only"}:
                    child_name = dictionary_rows[raw_value].get(
                        "dictionary_name", ""
                    ).strip()
                    if not child_name:
                        raise StageRuntimeError(
                            f"semantic degradation: {raw_value} has no dictionary_name"
                        )
                    values.append(
                        PreparedDictionaryValue(child_path, "group", child_name)
                    )
                visit(raw_value, child_path, next_visiting)
                continue
            values.append(PreparedDictionaryValue(path, "leaf", raw_value))

    visit(dictionary_id, (dictionary_id,), frozenset())
    if coverage_mode == "reference-only":
        normalized_fixture = reference_fixture_text.casefold()

        def fixture_contains(value: str) -> bool:
            normalized_value = value.casefold().strip()
            if not normalized_value:
                return False
            return (
                re.search(
                    rf"(?<!\w){re.escape(normalized_value)}(?!\w)",
                    normalized_fixture,
                )
                is not None
            )

        matched_group_paths = {
            item.hierarchy_path
            for item in values
            if item.value_kind == "group"
            and (
                item.hierarchy_path[-1].casefold() in normalized_fixture
                or fixture_contains(item.value)
            )
        }
        fixture_values = tuple(
            item
            for item in values
            if (
                item.value_kind == "group"
                and item.hierarchy_path in matched_group_paths
            )
            or (
                item.value_kind == "leaf"
                and fixture_contains(item.value)
                and (
                    not matched_group_paths
                    or item.hierarchy_path in matched_group_paths
                )
            )
        )
        return PreparedDictionaryRequirement(
            dictionary_id=dictionary_id,
            coverage_mode=coverage_mode,
            fixture_values=fixture_values,
        )
    if not values:
        raise StageRuntimeError(
            f"semantic degradation: exhaustive {dictionary_id} projection has no values"
        )
    return PreparedDictionaryRequirement(
        dictionary_id=dictionary_id,
        coverage_mode=coverage_mode,
        required_values=tuple(values),
    )


def _unbound_reference_fixture_action_literals(
    source_assertion: Any,
    dictionary_requirements: Sequence[PreparedDictionaryRequirement],
) -> tuple[str, ...]:
    """Find synthetic action literals that conflict with curated fixtures.

    Source assertions may use synthetic literals for ordinary boundary design, but a
    reference-only external dictionary must not carry a different invented value into
    the writer alongside its verified fixture. Source-backed UI labels remain allowed.
    """

    fixture_values = tuple(
        item.value
        for requirement in dictionary_requirements
        if requirement.coverage_mode == "reference-only"
        for item in requirement.fixture_values
        if item.value_kind == "leaf"
    )
    if not fixture_values:
        return ()

    def field(name: str, default: Any) -> Any:
        if isinstance(source_assertion, Mapping):
            return source_assertion.get(name, default)
        return getattr(source_assertion, name, default)

    source_evidence = " ".join(
        (
            str(field("exact_source_text", "")),
            *map(str, field("exact_source_fragments", ())),
            *(
                str(
                    binding.get("exact_source_fragment", "")
                    if isinstance(binding, Mapping)
                    else getattr(binding, "exact_source_fragment", "")
                )
                for binding in field("clause_evidence_bindings", ())
            ),
            *(
                str(
                    binding.get("exact_source_fragment", "")
                    if isinstance(binding, Mapping)
                    else getattr(binding, "exact_source_fragment", "")
                )
                for binding in field("supporting_source_bindings", ())
            ),
        )
    )

    def normalized(value: str) -> str:
        return _normalize_assertion_contract_text(value).casefold()

    normalized_source = normalized(source_evidence)
    normalized_fixtures = tuple(
        value for value in map(normalized, fixture_values) if value
    )
    conflicts: list[str] = []
    for action in field("action_clauses", ()):
        for match in ACTION_LITERAL.finditer(str(action)):
            literal = next(value for value in match.groups() if value is not None)
            normalized_literal = normalized(literal)
            if not normalized_literal or normalized_literal in normalized_source:
                continue
            fixture_bound = any(
                normalized_literal == fixture
                or (
                    min(len(normalized_literal), len(fixture)) >= 8
                    and (
                        normalized_literal in fixture
                        or fixture in normalized_literal
                    )
                )
                for fixture in normalized_fixtures
            )
            if not fixture_bound and literal not in conflicts:
                conflicts.append(literal)
    return tuple(conflicts)


REFERENCE_FIXTURE_ACTION_VALIDATOR = "reference-fixture-action-adequacy-v1"


def evaluate_reference_fixture_action_adequacy(
    manifest_value: Path | Mapping[str, Any],
    *,
    coverage_obligation_table: Path,
    package_test_design_plan: Path,
    dictionary_inventory: Path | None,
) -> dict[str, Any]:
    """Batch-detect reference-only fixture conflicts before model review.

    The compiler retains the same fail-closed check as defense in depth.  This
    pre-review projection deliberately reports every conflicting assertion in one
    deterministic pass so a model review is not spent discovering them serially.
    """

    if isinstance(manifest_value, Path):
        payload = json.loads(manifest_value.read_text(encoding="utf-8"))
    else:
        payload = manifest_value
    if not isinstance(payload, Mapping) or not isinstance(
        payload.get("assertions"), list
    ):
        raise StageRuntimeError(
            "reference fixture action adequacy requires a source assertion manifest"
        )
    obligation_rows = _table_with(
        coverage_obligation_table,
        {
            "obligation_id",
            "linked_atom_id",
            "required_behavior",
            "property_type",
            "obligation_class",
            "source_ref",
            "dictionary_refs",
            "dictionary_coverage",
        },
    )
    obligation_by_id = {row["obligation_id"]: row for row in obligation_rows}
    plan_rows = _table_with(
        package_test_design_plan,
        {"linked_atoms", "status", "test_data", "input_class"},
    )
    plan_by_atom: dict[str, list[dict[str, str]]] = {}
    for row in plan_rows:
        for atom_id in dict.fromkeys(
            token
            for token in TOKEN.findall(row.get("linked_atoms", ""))
            if token.startswith("ATOM-")
        ):
            plan_by_atom.setdefault(atom_id, []).append(row)

    referenced_dictionary_ids = {
        token
        for row in obligation_rows
        for token in TOKEN.findall(" ".join(row.values()))
        if token.startswith("DICT-")
    }
    if referenced_dictionary_ids and dictionary_inventory is None:
        raise StageRuntimeError(
            "reference fixture action adequacy requires dictionary_inventory "
            "when coverage obligations reference DICT-*"
        )
    dictionary_rows: dict[str, dict[str, str]] = {}
    dictionary_active_values: dict[str, tuple[str, ...]] = {}
    if dictionary_inventory is not None:
        for row in _table_with(
            dictionary_inventory, {"dictionary_id", "active_values"}
        ):
            dictionary_id = row["dictionary_id"]
            if dictionary_id in dictionary_rows:
                raise StageRuntimeError(
                    f"semantic degradation: duplicate dictionary {dictionary_id}"
                )
            dictionary_rows[dictionary_id] = row
            dictionary_active_values[dictionary_id] = _parse_dictionary_active_values(
                row["active_values"], dictionary_id=dictionary_id
            )

    dedicated_exhaustive_dictionary_ids = _dedicated_exhaustive_dictionary_ids(
        obligation_rows
    )
    conflicts: list[dict[str, Any]] = []
    checked_assertions: set[str] = set()
    for assertion in payload["assertions"]:
        if not isinstance(assertion, Mapping):
            continue
        assertion_id = str(assertion.get("assertion_id", ""))
        atom_id = str(assertion.get("atom_id", ""))
        for obligation_id in assertion.get("obligation_ids", []):
            if not isinstance(obligation_id, str):
                continue
            obligation_row = obligation_by_id.get(obligation_id)
            if obligation_row is None:
                continue
            dictionary_ids = list(
                dict.fromkeys(
                    token
                    for token in TOKEN.findall(" ".join(obligation_row.values()))
                    if token.startswith("DICT-")
                )
            )
            if not dictionary_ids:
                continue
            checked_assertions.add(assertion_id)
            viable_plan_rows = [
                row
                for row in plan_by_atom.get(atom_id, [])
                if row.get("status", "covered").strip().casefold()
                in {"covered", "testable", "planned"}
                or row.get("status", "").strip().casefold().startswith(
                    "covered_with_"
                )
            ]
            reference_fixture_text = " ".join(
                (
                    obligation_row.get("required_behavior", ""),
                    *(row.get("test_data", "") for row in viable_plan_rows),
                    *(row.get("input_class", "") for row in viable_plan_rows),
                )
            )
            requirements: list[PreparedDictionaryRequirement] = []
            for dictionary_id in dictionary_ids:
                if dictionary_id not in dictionary_rows:
                    raise StageRuntimeError(
                        "reference fixture action adequacy cannot resolve "
                        f"{dictionary_id}"
                    )
                requirements.append(
                    _compile_dictionary_requirement(
                        dictionary_id=dictionary_id,
                        coverage_mode=_effective_dictionary_coverage_mode(
                            obligation_row,
                            dictionary_id=dictionary_id,
                            dedicated_exhaustive_dictionary_ids=(
                                dedicated_exhaustive_dictionary_ids
                            ),
                        ),
                        dictionary_rows=dictionary_rows,
                        dictionary_active_values=dictionary_active_values,
                        reference_fixture_text=reference_fixture_text,
                    )
                )
            conflicting_literals = _unbound_reference_fixture_action_literals(
                assertion, requirements
            )
            if conflicting_literals:
                conflicts.append(
                    {
                        "assertion_id": assertion_id,
                        "atom_id": atom_id,
                        "obligation_id": obligation_id,
                        "dictionary_ids": dictionary_ids,
                        "conflicting_literals": list(conflicting_literals),
                    }
                )
    return {
        "version": 1,
        "validator": REFERENCE_FIXTURE_ACTION_VALIDATOR,
        "passed": not conflicts,
        "checked_assertion_count": len(checked_assertions),
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }


def _requires_changed_prestate(
    obligation_row: Mapping[str, str],
    plan_rows: Sequence[Mapping[str, str]],
) -> bool:
    classified_values = (
        obligation_row.get("property_type", ""),
        obligation_row.get("obligation_class", ""),
        *(row.get("coverage_class", "") for row in plan_rows),
    )
    return any(
        normalized == "reset"
        or normalized.startswith("reset-")
        or normalized.endswith("-reset")
        for normalized in map(_normalized_design_value, classified_values)
    )


def _compile_state_change(
    *,
    obligation_row: Mapping[str, str],
    plan_rows: Sequence[Mapping[str, str]],
    plan_path: Path,
    repo_root: Path,
) -> PreparedStateChange | None:
    if not _requires_changed_prestate(obligation_row, plan_rows):
        return None
    findings: list[dict[str, object]] = []
    for row in plan_rows:
        missing = [field for field in STATE_CHANGE_PLAN_FIELDS if not row.get(field, "").strip()]
        relation = row.get("state_relation", "").strip()
        if relation and relation != STATE_CHANGE_RELATION:
            missing.append("state_relation=different-from-captured-initial")
        if missing:
            findings.append(
                {
                    "kind": "state-change-precondition-incomplete",
                    "obligation_id": obligation_row.get("obligation_id", ""),
                    "atom_id": obligation_row.get("linked_atom_id", ""),
                    "missing_or_invalid_fields": missing,
                    **_artifact_anchor(
                        plan_path,
                        row.get("design_item_id")
                        or obligation_row.get("linked_atom_id", ""),
                        repo_root,
                    ),
                }
            )
    if findings:
        raise PreparedCompilerDiagnostic(
            "state-change-precondition-incomplete",
            "semantic degradation: reset design-plan rows must prove a state "
            "different from captured initial state before the target action",
            details=findings,
        )
    values_by_field = {
        field: tuple(dict.fromkeys(row[field].strip() for row in plan_rows))
        for field in STATE_CHANGE_PLAN_FIELDS
    }
    inconsistent = {
        field: list(values)
        for field, values in values_by_field.items()
        if len(values) != 1
    }
    if inconsistent:
        raise PreparedCompilerDiagnostic(
            "state-change-precondition-conflict",
            "semantic degradation: one obligation maps to conflicting state-change contracts",
            details=(
                {
                    "kind": "state-change-precondition-conflict",
                    "obligation_id": obligation_row.get("obligation_id", ""),
                    "atom_id": obligation_row.get("linked_atom_id", ""),
                    "conflicting_fields": inconsistent,
                    **_artifact_anchor(
                        plan_path,
                        obligation_row.get("linked_atom_id", ""),
                        repo_root,
                    ),
                },
            ),
        )
    return PreparedStateChange(
        initial_state_capture=values_by_field["initial_state_capture"][0],
        changed_state_setup=values_by_field["changed_state_setup"][0],
        pre_action_state_oracle=values_by_field["pre_action_state_oracle"][0],
        relation=values_by_field["state_relation"][0],
    )


def _resolve_source_first_state_change(
    *,
    state_change: PreparedStateChange | None,
    source_assertion: Any,
    obligation_id: str,
    atom_id: str,
    plan_path: Path,
    plan_rows: Sequence[Mapping[str, str]],
    repo_root: Path,
) -> PreparedStateChange | None:
    """Resolve a typed initial checkpoint from a reviewed source condition.

    The initial observation happens before the state-changing setup.  Therefore
    an action or post-action oracle cannot authorize it, and free plan prose is
    not a deterministic binding. Source-first reset plans name the zero-based
    condition index; the compiler owns the exact text copied into the package.
    """

    if state_change is None:
        return None
    binding = state_change.initial_state_capture.strip()
    match = SOURCE_CONDITION_STATE_BINDING.fullmatch(binding)
    detail = {
        "obligation_id": obligation_id,
        "atom_id": atom_id,
        "initial_state_capture": binding,
        "source_assertion_id": source_assertion.assertion_id,
        **_artifact_anchor(
            plan_path,
            plan_rows[0].get("design_item_id") or atom_id,
            repo_root,
        ),
    }
    if match is None:
        raise PreparedCompilerDiagnostic(
            "source-first-state-change-initial-binding-required",
            "semantic degradation: source-first reset initial_state_capture must "
            "use the typed source-condition:<index> binding",
            details=(
                {
                    "kind": "source-first-state-change-initial-binding-required",
                    **detail,
                },
            ),
        )
    condition_index = int(match.group("index"))
    if condition_index >= len(source_assertion.condition_clauses):
        raise PreparedCompilerDiagnostic(
            "source-first-state-change-initial-binding-invalid",
            "semantic degradation: source-first reset initial-state binding refers "
            "to a missing reviewed condition clause",
            details=(
                {
                    "kind": "source-first-state-change-initial-binding-invalid",
                    "condition_index": condition_index,
                    "condition_count": len(source_assertion.condition_clauses),
                    **detail,
                },
            ),
        )
    return PreparedStateChange(
        initial_state_capture=source_assertion.condition_clauses[condition_index],
        changed_state_setup=state_change.changed_state_setup,
        pre_action_state_oracle=state_change.pre_action_state_oracle,
        relation=state_change.relation,
    )


def _plan_requires_concrete_fixture(row: Mapping[str, str]) -> bool:
    input_class = row.get("input_class", "").strip().lower()
    if input_class in ABSTRACT_INPUT_CLASSES:
        return True
    return bool(INPUT_ACTION.search(row.get("planned_check", "")))


def _plan_generic_fixture_values(row: Mapping[str, str]) -> tuple[str, ...]:
    candidates = [
        row.get(key, "").strip()
        for key in ("fixture_id", "fixture", "test_data", "test_data_ref", "input_class")
    ]
    return tuple(value for value in candidates if value and GENERIC_FIXTURE_VALUE.search(value))


def _plan_has_concrete_fixture(row: Mapping[str, str]) -> bool:
    if _plan_generic_fixture_values(row):
        return False
    for key in ("fixture_id", "fixture", "test_data", "test_data_ref"):
        value = row.get(key, "").strip()
        if value and value.lower() not in {"n/a", "none", "none_required", "-"}:
            return True
    input_class = row.get("input_class", "").strip()
    if ":" in input_class and input_class.split(":", 1)[1].strip():
        return True
    return bool(
        CONCRETE_INLINE_VALUE.search(
            " ".join(
                (
                    row.get("planned_check", ""),
                    row.get("single_expected_behavior", ""),
                )
            )
        )
    )


def _environment_bound_fixture_lines(plan_path: Path) -> tuple[tuple[int, str], ...]:
    return tuple(
        (line_no, text.strip())
        for line_no, text in enumerate(
            plan_path.read_text(encoding="utf-8").splitlines(), 1
        )
        if ENVIRONMENT_BOUND_FIXTURE.search(text)
    )


def _fixture_contract_lines(plan_path: Path) -> tuple[tuple[str, str], ...]:
    contracts: list[tuple[str, str]] = []
    for text in plan_path.read_text(encoding="utf-8").splitlines():
        stripped = text.strip()
        fixture_ids = FIXTURE_TOKEN.findall(stripped)
        if stripped.startswith("-") and fixture_ids and ":" in stripped:
            contracts.extend((fixture_id, stripped) for fixture_id in fixture_ids)
    return tuple(contracts)


def _mapped_plan_intent_context(
    row: Mapping[str, str],
    fixture_contracts: Mapping[str, Sequence[str]],
) -> tuple[str, ...]:
    referenced_fixture_ids = tuple(
        dict.fromkeys(
            fixture_id
            for value in row.values()
            for fixture_id in FIXTURE_TOKEN.findall(value)
        )
    )
    fixture_context = tuple(
        "Fixture contract: " + contract
        for fixture_id in referenced_fixture_ids
        for contract in fixture_contracts.get(fixture_id, ())
    )
    test_data = row.get("test_data", "").strip()
    concrete_test_data = (
        test_data
        if test_data
        and test_data.casefold() not in {"n/a", "none", "none_required", "-"}
        and not GENERIC_FIXTURE_VALUE.search(test_data)
        and not FIXTURE_TOKEN.fullmatch(test_data.strip("`"))
        else ""
    )
    check_type = row.get("check_type", "").strip().casefold()
    check_type_context = (
        f"Check type: {check_type}"
        if check_type in {"positive", "negative"}
        else ""
    )
    return (
        *((check_type_context,) if check_type_context else ()),
        *fixture_context,
        *((f"Test data: {concrete_test_data}",) if concrete_test_data else ()),
    )


def _compile_portable_fixture_requirements(
    plan_rows: Sequence[Mapping[str, str]],
    fixture_contracts: Mapping[str, Sequence[str]],
) -> tuple[PreparedDictionaryRequirement, ...]:
    """Compile verified inline fixture contracts into enforceable requirements.

    External dynamic dictionaries need exact stored literals, but do not always
    have a project DICT-* inventory.  The package plan's portable contract is
    already hash/source validated by materialization; this independent compiler
    pass validates its executable fields again and projects them through the
    existing reference-only fixture gate.
    """

    fixture_ids = tuple(
        dict.fromkeys(
            fixture_id
            for row in plan_rows
            for value in row.values()
            for fixture_id in FIXTURE_TOKEN.findall(value)
        )
    )
    requirements: list[PreparedDictionaryRequirement] = []
    for fixture_id in fixture_ids:
        for contract in fixture_contracts.get(fixture_id, ()):
            fields = {
                match.group("key"): match.group("value")
                for match in PORTABLE_FIXTURE_FIELD.finditer(contract)
            }
            if set(fields) != {
                "request_parameters",
                "expected_response",
                "response_sha256",
                "status",
                "runtime_api_call",
                "product_input",
            }:
                continue
            if (
                fields["status"] != "verified"
                or fields["runtime_api_call"] != "prohibited"
                or fields["product_input"] != "stored_literals"
                or re.fullmatch(r"[0-9a-f]{64}", fields["response_sha256"])
                is None
            ):
                continue
            try:
                request = json.loads(fields["request_parameters"])
                expected = json.loads(fields["expected_response"])
            except json.JSONDecodeError:
                continue
            if not isinstance(request, Mapping) or not isinstance(expected, Mapping):
                continue
            dictionary_id = "DICT-" + fixture_id.removeprefix("FX-")
            def fixture_path(label: str) -> tuple[str, ...]:
                normalized_label = re.sub(
                    r"[^A-Za-z0-9._-]+", "-", label
                ).strip("-")
                return (
                    dictionary_id,
                    f"{dictionary_id}-{normalized_label.upper()}",
                )

            values: list[tuple[tuple[str, ...], str]] = [
                (fixture_path("fixture-id"), fixture_id)
            ]
            query = request.get("query")
            exact_suggestion = expected.get("exact_suggestion")
            exact_components = expected.get("exact_components")
            if (
                fixture_id.startswith("FX-DADATA-FMS-")
                and isinstance(query, str)
                and query
                and isinstance(exact_suggestion, str)
                and exact_suggestion
                and isinstance(exact_components, Mapping)
            ):
                values.extend(
                    (
                        (fixture_path("query"), query),
                        (
                            fixture_path("exact-suggestion"),
                            exact_suggestion,
                        ),
                    )
                )
                for key in ("code", "name", "region_code", "type"):
                    value = exact_components.get(key)
                    if isinstance(value, (str, int, float)):
                        values.append(
                            (
                                fixture_path(f"exact-component-{key}"),
                                str(value),
                            )
                        )
            else:
                values.extend(
                    (
                        (
                            fixture_path("request-parameters"),
                            json.dumps(
                                request,
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                        ),
                        (
                            fixture_path("expected-response"),
                            json.dumps(
                                expected,
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                        ),
                    )
                )
            values.append(
                (
                    fixture_path("response-sha256"),
                    fields["response_sha256"],
                )
            )
            requirement = PreparedDictionaryRequirement(
                dictionary_id=dictionary_id,
                coverage_mode="reference-only",
                fixture_values=tuple(
                    PreparedDictionaryValue(path, "leaf", value)
                    for path, value in values
                ),
            )
            requirement.validate()
            requirements.append(requirement)
            break
    return tuple(requirements)


def _portable_dictionary_evidence_record(
    requirement: PreparedDictionaryRequirement,
    *,
    package_plan_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Project one portable fixture requirement into immutable evidence."""

    requirement.validate()
    active_values = list(
        dict.fromkeys(
            item.value.strip()
            for item in requirement.fixture_values
            if item.value_kind == "leaf" and item.value.strip()
        )
    )
    if not active_values:
        raise StageRuntimeError(
            "portable fixture dictionary has no exact active values: "
            + requirement.dictionary_id
        )
    return {
        "dictionary_id": requirement.dictionary_id,
        "dictionary_name": (
            "Verified portable fixture " + requirement.dictionary_id
        ),
        "source_file": package_plan_path.relative_to(repo_root).as_posix(),
        "source_location": "Portable Fixture Contracts",
        "extraction_status": "verified-portable-fixture",
        "active_values": active_values,
        "archived_values": "",
        "used_by_source_properties": "",
        "gap_id": "",
        "notes": "Runtime API call prohibited; stored literals only.",
    }


def _validate_planned_test_case_groups(
    *,
    obligation_rows: Sequence[Mapping[str, str]],
    plan_rows: Sequence[Mapping[str, str]],
    obligations_path: Path,
    plan_path: Path,
    repo_root: Path,
) -> None:
    groups: dict[str, list[Mapping[str, str]]] = {}
    for row in obligation_rows:
        if row.get("status", "").lower() != "covered":
            continue
        tc_ids = TC_TOKEN.findall(row.get("planned_tc_or_gap", ""))
        if len(set(tc_ids)) == 1:
            groups.setdefault(tc_ids[0], []).append(row)
    for tc_id, group in groups.items():
        if len(group) < 2:
            continue
        atom_ids = {
            token
            for row in group
            for token in TOKEN.findall(row.get("linked_atom_id", ""))
            if token.startswith("ATOM-")
        }
        linked_plan_rows = [
            row
            for row in plan_rows
            if tc_id in TC_TOKEN.findall(row.get("planned_tc_or_gap", ""))
        ]
        shared_plan_rows = [
            row
            for row in linked_plan_rows
            if {
                token
                for token in TOKEN.findall(row.get("linked_atoms", ""))
                if token.startswith("ATOM-")
            }
            == atom_ids
        ]
        package_ids = {row.get("package_id", "").strip() for row in group}
        property_roots = {
            row.get("source_property_id", "").split(".P", 1)[0].strip()
            for row in group
        }
        justification = " ".join(
            [row.get("review_notes", "") for row in group]
            + [row.get("grouping_justification", "") for row in shared_plan_rows]
        ).lower()
        cross_boundary = len(package_ids) != 1 or len(property_roots) != 1
        valid = (
            len(linked_plan_rows) == 1
            and len(shared_plan_rows) == 1
            and (not cross_boundary or "grouping-justification:" in justification)
        )
        if valid:
            continue
        reason = (
            "cross-field or cross-package group has no grouping-justification"
            if cross_boundary and "grouping-justification:" not in justification
            else "group must have exactly one shared design-plan row linking all atoms"
        )
        raise PreparedCompilerDiagnostic(
            "invalid-planned-test-case-group",
            f"semantic degradation: {tc_id} {reason}",
            details=(
                {
                    "kind": "invalid-planned-test-case-group",
                    "planned_test_case_id": tc_id,
                    "atom_ids": sorted(atom_ids),
                    "package_ids": sorted(package_ids),
                    "source_property_roots": sorted(property_roots),
                    "reason": reason,
                    **_artifact_anchor(obligations_path, tc_id, repo_root),
                    "plan_artifact": _artifact_anchor(plan_path, tc_id, repo_root),
                },
            ),
        )


def _canonical_planned_test_case_id(
    row: Mapping[str, str],
) -> str:
    """Resolve a writer-facing TC id without losing candidate lifecycle identity."""

    raw = row.get("planned_tc_or_gap", "").strip()
    tc_ids = list(dict.fromkeys(TC_TOKEN.findall(raw)))
    if len(tc_ids) == 1:
        return tc_ids[0]
    calibration_status = row.get("calibration_status", "").strip().casefold()
    candidate = CANDIDATE_SCOPE_OBLIGATION.fullmatch(raw)
    if calibration_status != "ui-calibration-required" or candidate is None:
        return ""
    scope_obligation_id = candidate.group(1).upper()
    declared_scope_ids = {
        token.upper()
        for token in re.findall(
            r"\bSO-(?:NEG|REQ)-[A-Za-z0-9_.-]+\b",
            row.get("scope_obligation_ids", ""),
            flags=re.IGNORECASE,
        )
    }
    if scope_obligation_id not in declared_scope_ids:
        return ""
    return "TC-" + scope_obligation_id.removeprefix("SO-")


def _validate_execution_dependency_group_isolation(
    *,
    obligation_rows: Sequence[Mapping[str, str]],
    plan_rows: Sequence[Mapping[str, str]],
    blocked_obligation_ids: set[str],
    blocked_atom_ids: set[str],
    obligations_path: Path,
    plan_path: Path,
    repo_root: Path,
) -> None:
    """Fail closed when one planned TC/design row straddles ready and blocked chains."""

    if not blocked_obligation_ids:
        return
    obligation_by_id = {
        row.get("obligation_id", ""): row for row in obligation_rows
    }
    for tc_id in sorted(
        {
            tc_id
            for row in obligation_rows
            for tc_id in TC_TOKEN.findall(row.get("planned_tc_or_gap", ""))
        }
    ):
        grouped_ids = {
            row.get("obligation_id", "")
            for row in obligation_rows
            if tc_id in TC_TOKEN.findall(row.get("planned_tc_or_gap", ""))
        }
        blocked_ids = grouped_ids & blocked_obligation_ids
        ready_ids = grouped_ids - blocked_obligation_ids
        if blocked_ids and ready_ids:
            raise PreparedCompilerDiagnostic(
                "execution-dependency-crosses-test-case-group",
                f"planned test case {tc_id} mixes ready and execution-blocked obligations",
                details=(
                    {
                        "kind": "execution-dependency-crosses-test-case-group",
                        "planned_test_case_id": tc_id,
                        "ready_obligation_ids": sorted(ready_ids),
                        "blocked_obligation_ids": sorted(blocked_ids),
                        "ready_atom_ids": sorted(
                            {
                                token
                                for obligation_id in ready_ids
                                for token in TOKEN.findall(
                                    obligation_by_id[obligation_id].get(
                                        "linked_atom_id", ""
                                    )
                                )
                                if token.startswith("ATOM-")
                            }
                        ),
                        "blocked_atom_ids": sorted(
                            {
                                token
                                for obligation_id in blocked_ids
                                for token in TOKEN.findall(
                                    obligation_by_id[obligation_id].get(
                                        "linked_atom_id", ""
                                    )
                                )
                                if token.startswith("ATOM-")
                            }
                        ),
                        **_artifact_anchor(obligations_path, tc_id, repo_root),
                    },
                ),
            )
    all_atom_ids = {
        token
        for row in obligation_rows
        for token in TOKEN.findall(row.get("linked_atom_id", ""))
        if token.startswith("ATOM-")
    }
    ready_atom_ids = all_atom_ids - blocked_atom_ids
    for row in plan_rows:
        linked_atom_ids = {
            token
            for token in TOKEN.findall(row.get("linked_atoms", ""))
            if token.startswith("ATOM-")
        }
        if linked_atom_ids & blocked_atom_ids and linked_atom_ids & ready_atom_ids:
            selector = row.get("planned_tc_or_gap", "") or row.get(
                "design_item_id", ""
            )
            raise PreparedCompilerDiagnostic(
                "execution-dependency-crosses-design-plan-row",
                "one design-plan row mixes ready and execution-blocked ATOM chains",
                details=(
                    {
                        "kind": "execution-dependency-crosses-design-plan-row",
                        "ready_atom_ids": sorted(linked_atom_ids & ready_atom_ids),
                        "blocked_atom_ids": sorted(
                            linked_atom_ids & blocked_atom_ids
                        ),
                        **_artifact_anchor(plan_path, selector, repo_root),
                    },
                ),
            )


def _test_case_mapping_by_atom(
    rows: Sequence[Mapping[str, str]],
    *,
    atom_field: str,
    mapping_field: str,
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for row in rows:
        atom_ids = {
            token
            for token in TOKEN.findall(row.get(atom_field, ""))
            if token.startswith("ATOM-")
        }
        tc_ids = set(TC_TOKEN.findall(row.get(mapping_field, "")))
        for atom_id in atom_ids:
            result.setdefault(atom_id, set()).update(tc_ids)
    return result


def _validate_test_case_mapping_consistency(
    *,
    ledger_rows: Sequence[Mapping[str, str]],
    obligation_rows: Sequence[Mapping[str, str]],
    plan_rows: Sequence[Mapping[str, str]],
    ledger_path: Path,
    obligations_path: Path,
    plan_path: Path,
    decision_rows: Sequence[Mapping[str, str]] | None,
    decision_path: Path | None,
    repo_root: Path,
) -> None:
    if not ledger_rows or "covered_by_tc" not in ledger_rows[0]:
        return
    ledger_mapping = _test_case_mapping_by_atom(
        ledger_rows,
        atom_field="atom_id",
        mapping_field="covered_by_tc",
    )
    compared = [
        (
            "coverage-obligation-table",
            _test_case_mapping_by_atom(
                obligation_rows,
                atom_field="linked_atom_id",
                mapping_field="planned_tc_or_gap",
            ),
            obligations_path,
        ),
        (
            "package-test-design-plan",
            _test_case_mapping_by_atom(
                plan_rows,
                atom_field="linked_atoms",
                mapping_field="planned_tc_or_gap",
            ),
            plan_path,
        ),
    ]
    if decision_rows is not None and decision_path is not None:
        compared.append(
            (
                "test-design-decision-table",
                _test_case_mapping_by_atom(
                    decision_rows,
                    atom_field="linked_atom_id",
                    mapping_field="planned_tc_or_gap",
                ),
                decision_path,
            )
        )
    findings: list[dict[str, object]] = []
    known_atoms = {row.get("atom_id", "") for row in ledger_rows}
    for artifact_kind, actual_mapping, artifact_path in compared:
        for atom_id in sorted(known_atoms | set(actual_mapping)):
            expected = sorted(ledger_mapping.get(atom_id, set()))
            actual = sorted(actual_mapping.get(atom_id, set()))
            if expected == actual:
                continue
            findings.append(
                {
                    "kind": "tc-mapping-inconsistency",
                    "atom_id": atom_id,
                    "mapping_artifact_kind": artifact_kind,
                    "expected_test_case_ids": expected,
                    "actual_test_case_ids": actual,
                    "ledger_artifact": _artifact_anchor(
                        ledger_path, atom_id, repo_root
                    ),
                    "mapping_artifact": _artifact_anchor(
                        artifact_path, atom_id, repo_root
                    ),
                }
            )
    if findings:
        raise PreparedCompilerDiagnostic(
            "tc-mapping-inconsistency",
            "semantic degradation: TC mappings differ between the atomic ledger "
            "and prepared design artifacts",
            details=findings,
        )


class PreparedCompilerDiagnostic(StageRuntimeError):
    """Machine-readable compiler failure with bounded artifact anchors."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Sequence[Mapping[str, object]] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = tuple(dict(item) for item in details)


def _artifact_anchor(path: Path, token: str, repo_root: Path) -> dict[str, object]:
    line = next(
        (
            line_no
            for line_no, text in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            )
            if token in text
        ),
        None,
    )
    try:
        artifact = path.relative_to(repo_root).as_posix()
    except ValueError:
        artifact = path.as_posix()
    return {"id": token, "artifact": artifact, "line": line}


def _scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value in {"[]", "null"}:
        return [] if value == "[]" else None
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def load_workflow_state(path: Path) -> dict[str, Any]:
    """Load the conservative YAML subset used by workflow-state.yaml.

    Only top-level scalars/lists and one-level scalar maps are accepted. This
    keeps the compiler dependency-free and rejects ambiguous YAML constructs.
    """

    result: dict[str, Any] = {}
    parent: str | None = None
    parent_indent = 0
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0:
            parent = None
            if ":" not in stripped:
                raise StageRuntimeError(f"unsupported workflow YAML at {path}:{line_no}")
            key, value = stripped.split(":", 1)
            if key in result:
                raise StageRuntimeError(f"duplicate workflow YAML key at {path}:{line_no}: {key}")
            if value.strip():
                result[key] = _scalar(value)
            else:
                result[key] = {}
                parent = key
                parent_indent = indent
            continue
        if parent is None or indent <= parent_indent:
            raise StageRuntimeError(f"unsupported workflow YAML indentation at {path}:{line_no}")
        if stripped.startswith("- "):
            if not isinstance(result[parent], (dict, list)):
                raise StageRuntimeError(f"invalid workflow list at {path}:{line_no}")
            if isinstance(result[parent], dict) and not result[parent]:
                result[parent] = []
            if not isinstance(result[parent], list):
                raise StageRuntimeError(f"mixed workflow collection at {path}:{line_no}")
            result[parent].append(_scalar(stripped[2:]))
            continue
        if ":" not in stripped or not isinstance(result[parent], dict):
            raise StageRuntimeError(f"unsupported nested workflow YAML at {path}:{line_no}")
        key, value = stripped.split(":", 1)
        if key in result[parent]:
            raise StageRuntimeError(
                f"duplicate workflow YAML key at {path}:{line_no}: {parent}.{key}"
            )
        if not value.strip():
            raise StageRuntimeError(f"nested workflow maps must be scalar at {path}:{line_no}")
        result[parent][key] = _scalar(value)
    return result


def _clean_cell(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    return value.replace("<br>", "; ").strip()


def _split_markdown_table_row(value: str) -> list[str]:
    """Split one pipe table row without treating ``\|`` as a delimiter."""

    raw = value.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        raw = raw[:-1]
    cells: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(raw):
        character = raw[index]
        if character == "\\" and index + 1 < len(raw) and raw[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if character == "|":
            cells.append(_clean_cell("".join(current)))
            current = []
        else:
            current.append(character)
        index += 1
    cells.append(_clean_cell("".join(current)))
    return cells


def _parse_dictionary_active_values(value: str, *, dictionary_id: str) -> tuple[str, ...]:
    """Parse the canonical semicolon-delimited inventory cell exactly once.

    ``_clean_cell`` removes the first and last Markdown backticks from a full
    cell.  For a canonical cell such as `` `A`; `B` ``, that intentionally
    leaves ``A`; `B``.  Splitting on the canonical delimiter before trimming
    only boundary backticks preserves both values without treating the
    separator punctuation as a value.
    """
    raw_parts = re.split(r"\s*;\s*", value.strip())
    if not value.strip() or not raw_parts or any(not item.strip() for item in raw_parts):
        raise StageRuntimeError(
            f"semantic degradation: {dictionary_id} has malformed active values"
        )
    parsed: list[str] = []
    for raw in raw_parts:
        item = raw.strip()
        if item.startswith("`"):
            item = item[1:]
        if item.endswith("`"):
            item = item[:-1]
        item = item.strip()
        if "`" in item or not item or not any(character.isalnum() for character in item):
            raise StageRuntimeError(
                f"semantic degradation: {dictionary_id} has malformed active values"
            )
        parsed.append(item)
    if len(parsed) != len(set(parsed)):
        raise StageRuntimeError(
            f"semantic degradation: {dictionary_id} has duplicate active values"
        )
    return tuple(parsed)


def markdown_tables(path: Path) -> list[list[dict[str, str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    tables: list[list[dict[str, str]]] = []
    index = 0
    while index + 1 < len(lines):
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not (header.startswith("|") and separator.startswith("|") and "---" in separator):
            index += 1
            continue
        columns = _split_markdown_table_row(header)
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = _split_markdown_table_row(lines[index])
            if len(cells) == len(columns):
                rows.append(dict(zip(columns, cells)))
            index += 1
        tables.append(rows)
    return tables


def _table_with(path: Path, required: set[str]) -> list[dict[str, str]]:
    for table in markdown_tables(path):
        if table and required <= set(table[0]):
            return table
    raise StageRuntimeError(f"required Markdown table {sorted(required)} is missing: {path}")


def _artifact(ft_root: Path, state: Mapping[str, Any], key: str, *, required: bool = True) -> Path | None:
    latest = state.get("latest_artifacts")
    value = latest.get(key) if isinstance(latest, Mapping) else None
    if not value:
        if required:
            raise StageRuntimeError(f"workflow-state latest_artifacts.{key} is required")
        return None
    path = (ft_root / str(value)).resolve()
    try:
        path.relative_to(ft_root.resolve())
    except ValueError as exc:
        raise StageRuntimeError(f"workflow artifact escapes FT root: {value}") from exc
    if not path.is_file():
        raise StageRuntimeError(f"workflow artifact is missing: {value}")
    return path


_BASE_COMPILER_ARTIFACTS = (
    "source_selection",
    "atomic_requirements_ledger",
    "coverage_obligation_table",
    "package_test_design_plan",
    "test_design_applicability_matrix",
)
_SOURCE_FIRST_COMPILER_ARTIFACTS = (
    "source_row_inventory",
    "source_row_extraction_spec",
    "source_row_baseline",
    "source_assertions",
    "source_assertion_review",
)
_OPTIONAL_COMPILER_ARTIFACTS = (
    "test_design_decision_table",
    "coverage_gaps",
    "dictionary_inventory",
    "source_to_package_fidelity",
)
_SEMANTIC_COMPILER_ARTIFACTS = (
    "semantic_design",
    "scope_boundary_decision",
    "semantic_design_bridge_receipt",
    "negative_oracle_inventory",
    "requiredness_oracle_inventory",
)


def _resolve_declared_compiler_artifacts(
    *,
    ft_root: Path,
    state: Mapping[str, Any],
    source_first_contract: bool,
) -> dict[str, Path | None]:
    result: dict[str, Path | None] = {
        key: _artifact(ft_root, state, key) for key in _BASE_COMPILER_ARTIFACTS
    }
    result.update(
        {
            key: (
                _artifact(ft_root, state, key)
                if source_first_contract
                else None
            )
            for key in _SOURCE_FIRST_COMPILER_ARTIFACTS
        }
    )
    result.update(
        {
            key: _artifact(ft_root, state, key, required=False)
            for key in _OPTIONAL_COMPILER_ARTIFACTS
        }
    )
    result.update(
        {
            key: (
                _artifact(ft_root, state, key, required=False)
                if source_first_contract
                else None
            )
            for key in _SEMANTIC_COMPILER_ARTIFACTS
        }
    )
    if result["semantic_design"] is None and any(
        result[key] is not None
        for key in (
            "scope_boundary_decision",
            "semantic_design_bridge_receipt",
            "negative_oracle_inventory",
            "requiredness_oracle_inventory",
        )
    ):
        raise StageRuntimeError(
            "semantic bridge artifacts require latest_artifacts.semantic_design"
        )
    if result["semantic_design"] is not None:
        missing = [
            key
            for key in (
                "scope_boundary_decision",
                "semantic_design_bridge_receipt",
            )
            if result[key] is None
        ]
        if missing:
            raise StageRuntimeError(
                "semantic design requires hash-bound bridge artifacts: "
                + ", ".join(f"latest_artifacts.{key}" for key in missing)
            )
    return result


def resolve_workflow_compiler_inputs(
    *,
    workflow_state: Path,
    repo_root: Path,
    expected_ft_slug: str,
) -> dict[str, Path]:
    """Resolve every filesystem input the compiler will read.

    This is shared with wall-clock instrumentation so compile metrics cannot silently
    omit semantic bridge artifacts or count unrelated source-review outputs.
    """

    repo_root = repo_root.resolve()
    workflow_state = workflow_state.resolve()
    ft_root = (repo_root / "fts" / expected_ft_slug).resolve()
    if not ft_root.is_dir():
        raise StageRuntimeError(f"expected FT package is missing: fts/{expected_ft_slug}")
    _within(workflow_state, ft_root, "workflow-state")
    state = load_workflow_state(workflow_state)
    if state.get("ft_slug") != expected_ft_slug:
        raise StageRuntimeError(
            "workflow-state ft_slug mismatch: "
            f"expected {expected_ft_slug}, found {state.get('ft_slug', '')}"
        )
    contract_version = state.get("prepared_compiler_contract_version")
    if contract_version not in SUPPORTED_COMPILER_CONTRACT_VERSIONS:
        raise StageRuntimeError(
            "workflow-state prepared_compiler_contract_version must be one of "
            f"{sorted(SUPPORTED_COMPILER_CONTRACT_VERSIONS)}"
        )
    source_first_contract = contract_version == COMPILER_CONTRACT_VERSION
    declared = _resolve_declared_compiler_artifacts(
        ft_root=ft_root,
        state=state,
        source_first_contract=source_first_contract,
    )
    resolved: dict[str, Path] = {"workflow_state": workflow_state}
    resolved.update(
        {key: path for key, path in declared.items() if path is not None}
    )
    source_selection = declared["source_selection"]
    assert source_selection is not None
    entries = _selected_source_entries(
        repo_root=repo_root,
        ft_root=ft_root,
        source_selection=source_selection,
        require_manifest_binding=source_first_contract,
    )
    for index, entry in enumerate(entries, start=1):
        if entry.manifest_binding != "not-used":
            resolved[f"selected_source_{index:03d}"] = entry.path
    package_notes = ft_root / "AGENT-NOTES.md"
    if package_notes.is_file():
        resolved["package_agent_notes"] = package_notes
    return resolved


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_utf8_json_object(
    path: Path,
    *,
    label: str,
) -> tuple[Mapping[str, Any], bytes, str]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StageRuntimeError(
            f"{label} artifact is not valid UTF-8 JSON: {path}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise StageRuntimeError(f"{label} artifact root must be an object")
    return payload, raw, hashlib.sha256(raw).hexdigest()


def _semantic_string_array(
    payload: Mapping[str, Any],
    key: str,
    *,
    label: str,
) -> tuple[str, ...]:
    raw = payload.get(key)
    if (
        not isinstance(raw, list)
        or any(not isinstance(item, str) or not item.strip() for item in raw)
        or len(raw) != len(set(raw))
    ):
        raise StageRuntimeError(
            f"semantic design {label}.{key} must be a duplicate-free string array"
        )
    return tuple(raw)


def _load_semantic_compiler_projection(
    *,
    repo_root: Path,
    package_id: str,
    semantic_design_path: Path,
    scope_boundary_path: Path,
    bridge_receipt_path: Path,
    negative_inventory_path: Path | None,
    requiredness_inventory_path: Path | None,
) -> dict[str, Any]:
    payload, _, semantic_sha256 = _read_utf8_json_object(
        semantic_design_path,
        label="semantic design",
    )
    boundary, _, boundary_sha256 = _read_utf8_json_object(
        scope_boundary_path,
        label="scope boundary decision",
    )
    receipt, _, receipt_sha256 = _read_utf8_json_object(
        bridge_receipt_path,
        label="semantic design bridge receipt",
    )
    if (
        payload.get("version") != 4
        or payload.get("contract") != "semantic-design-bridge-v2"
        or payload.get("status") != "ready"
    ):
        raise StageRuntimeError(
            "semantic design compiler projection requires ready semantic-design-bridge-v2 v4"
        )
    if (
        boundary.get("version") != 2
        or boundary.get("status") != "ready"
        or boundary.get("blocking_reason") != "none_required"
    ):
        raise StageRuntimeError(
            "semantic design compiler projection requires a ready v2 scope boundary decision"
        )
    expected_receipt_identity = {
        "version": 1,
        "status": "verified",
        "contract": "scope-v2-to-semantic-design-v1",
        "materialization_status": "materialized",
    }
    for key, expected in expected_receipt_identity.items():
        if receipt.get(key) != expected:
            raise StageRuntimeError(
                f"semantic design bridge receipt {key} must equal {expected!r}"
            )
    if receipt.get("prepared_context_sha256") != payload.get(
        "prepared_context_sha256"
    ):
        raise StageRuntimeError(
            "semantic design bridge receipt prepared_context_sha256 does not match the design"
        )
    publication = receipt.get("publication")
    if not isinstance(publication, Mapping) or publication.get("status") != "atomic-renamed":
        raise StageRuntimeError(
            "semantic design bridge receipt requires atomic-renamed publication evidence"
        )
    declared_handoff = publication.get("final_handoff")
    if not isinstance(declared_handoff, str) or not declared_handoff.strip():
        raise StageRuntimeError(
            "semantic design bridge receipt publication.final_handoff is required"
        )
    declared_handoff_path = PurePosixPath(declared_handoff)
    if (
        declared_handoff_path.is_absolute()
        or declared_handoff_path.as_posix() != declared_handoff
        or any(part in {"", ".", ".."} for part in declared_handoff_path.parts)
        or repo_root.joinpath(*declared_handoff_path.parts).resolve()
        != bridge_receipt_path.parent.resolve()
    ):
        raise StageRuntimeError(
            "semantic design bridge receipt publication.final_handoff does not name "
            "the published receipt directory"
        )
    readiness = receipt.get("downstream_evidence_readiness")
    if not isinstance(readiness, Mapping) or (
        readiness.get("status") != "passed"
        or readiness.get("canonical_preflight")
        != "source-reviewer.prepare_evidence_set"
    ):
        raise StageRuntimeError(
            "semantic design bridge receipt requires passed canonical downstream evidence preflight"
        )
    semantic_decision_sha256 = _canonical_json_sha256(payload)
    boundary_decision_sha256 = _canonical_json_sha256(boundary)
    receipt_hashes = {
        "semantic_design_artifact_sha256": semantic_sha256,
        "scope_boundary_artifact_sha256": boundary_sha256,
        "semantic_design_decision_sha256": semantic_decision_sha256,
        "scope_boundary_decision_sha256": boundary_decision_sha256,
    }
    for key, expected in receipt_hashes.items():
        if receipt.get(key) != expected:
            raise StageRuntimeError(
                f"semantic design bridge receipt {key} does not match its artifact"
            )
    if payload.get("scope_boundary_decision_sha256") != boundary_decision_sha256:
        raise StageRuntimeError(
            "semantic design scope_boundary_decision_sha256 does not match the declared boundary"
        )
    scope_boundary = boundary.get("scope_boundary")
    if not isinstance(scope_boundary, Mapping):
        raise StageRuntimeError("scope boundary decision scope_boundary must be an object")
    for semantic_key, boundary_value in (
        ("scope_summary", boundary.get("scope_summary")),
        ("included", scope_boundary.get("include")),
        ("excluded", scope_boundary.get("exclude")),
        ("mockup_locators", boundary.get("mockup_locators")),
    ):
        if payload.get(semantic_key) != boundary_value:
            raise StageRuntimeError(
                f"semantic design {semantic_key} drifted from the hash-bound scope boundary"
            )
    collections: dict[str, list[Mapping[str, Any]]] = {}
    for key in (
        "source_designs",
        "obligations",
        "dependency_bindings",
        "dictionaries",
        "negative_oracles",
        "requiredness_oracles",
        "applicability",
    ):
        raw = payload.get(key)
        if not isinstance(raw, list) or any(not isinstance(item, Mapping) for item in raw):
            raise StageRuntimeError(f"semantic design {key} must be an object array")
        collections[key] = list(raw)
    obligation_ids: list[str] = []
    planned_tc_ids: list[str] = []
    for obligation in collections["obligations"]:
        obligation_id = str(obligation.get("obligation_id", ""))
        if not obligation_id:
            raise StageRuntimeError("semantic design obligations require obligation_id")
        obligation_ids.append(obligation_id)
        if obligation.get("package_id") != package_id:
            raise StageRuntimeError(
                f"semantic design {obligation_id or 'obligation'} package_id must equal "
                "the compiled package_id"
            )
        planned_tc_id = str(obligation.get("planned_tc_id", ""))
        if not planned_tc_id:
            raise StageRuntimeError(
                f"semantic design {obligation_id} requires planned_tc_id"
            )
        planned_tc_ids.append(planned_tc_id)
    if len(obligation_ids) != len(set(obligation_ids)):
        raise StageRuntimeError(
            "semantic design obligations require unique obligation_id values"
        )
    if len(planned_tc_ids) != len(set(planned_tc_ids)):
        raise StageRuntimeError(
            "semantic design obligations require unique planned_tc_id values"
        )
    dependency_ids = [
        str(item.get("dependency_id", ""))
        for item in collections["dependency_bindings"]
    ]
    if any(not value for value in dependency_ids) or len(dependency_ids) != len(
        set(dependency_ids)
    ):
        raise StageRuntimeError(
            "semantic design dependency_bindings require unique dependency_id values"
        )
    signal_ids = [
        str(item.get("signal_id", ""))
        for key in ("negative_oracles", "requiredness_oracles")
        for item in collections[key]
    ]
    if any(not value for value in signal_ids) or len(signal_ids) != len(set(signal_ids)):
        raise StageRuntimeError(
            "semantic design oracle inventories require unique signal_id values"
        )

    boundary_dependencies = boundary.get("dependencies")
    if (
        not isinstance(boundary_dependencies, list)
        or any(not isinstance(item, Mapping) for item in boundary_dependencies)
    ):
        raise StageRuntimeError("scope boundary decision dependencies must be an object array")
    if len(boundary_dependencies) != len(collections["dependency_bindings"]):
        raise StageRuntimeError(
            "semantic design dependency_bindings must cover the hash-bound boundary dependencies exactly"
        )
    copied_dependency_fields = (
        "dependency_id",
        "kind",
        "name",
        "source_row_ids",
        "resolution",
        "target_source_row_ids",
        "exact_source_fragments",
        "gap_ids",
        "blocking",
        "rationale",
    )
    for authoritative, binding in zip(
        boundary_dependencies,
        collections["dependency_bindings"],
        strict=True,
    ):
        dependency_id = str(authoritative.get("dependency_id", "")) or "dependency"
        for field in copied_dependency_fields:
            if binding.get(field) != authoritative.get(field):
                raise StageRuntimeError(
                    f"semantic design {dependency_id}.{field} drifted from the hash-bound boundary"
                )

    receipt_counts = {
        "obligation_count": len(collections["obligations"]),
        "dependency_binding_count": len(collections["dependency_bindings"]),
        "planned_test_case_count": len(planned_tc_ids),
        "dictionary_count": len(collections["dictionaries"]),
        "negative_oracle_count": len(collections["negative_oracles"]),
        "requiredness_oracle_count": len(collections["requiredness_oracles"]),
    }
    for key, expected in receipt_counts.items():
        if receipt.get(key) != expected:
            raise StageRuntimeError(
                f"semantic design bridge receipt {key} must equal {expected}"
            )

    inventory_specs = (
        ("negative", "negative_oracles", negative_inventory_path),
        ("requiredness", "requiredness_oracles", requiredness_inventory_path),
    )
    rendered_inventories: list[dict[str, Any]] = []
    for kind, collection_key, inventory_path in inventory_specs:
        rows = collections[collection_key]
        if rows and inventory_path is None:
            raise StageRuntimeError(
                f"semantic design {collection_key} requires its declared Markdown inventory"
            )
        if inventory_path is None:
            continue
        try:
            inventory_raw = inventory_path.read_bytes()
            text = inventory_raw.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise StageRuntimeError(
                f"{kind} oracle inventory is not valid UTF-8: {inventory_path}"
            ) from exc
        for item in rows:
            for identity_key in ("signal_id", "scope_obligation_id"):
                identity = str(item.get(identity_key, ""))
                if not identity or not _contains_exact_trace_token(text, identity):
                    raise StageRuntimeError(
                        f"{kind} oracle inventory does not preserve {identity_key}={identity}"
                    )
        rendered_inventories.append(
            {
                "kind": kind,
                "path": inventory_path.relative_to(repo_root).as_posix(),
                "sha256": hashlib.sha256(inventory_raw).hexdigest(),
                "utf8_text": text,
            }
        )
    return {
        "contract": "semantic-design-compiler-projection-v1",
        "semantic_design_artifact": {
            "path": semantic_design_path.relative_to(repo_root).as_posix(),
            "sha256": semantic_sha256,
            "decision_sha256": semantic_decision_sha256,
        },
        "scope_boundary_artifact": {
            "path": scope_boundary_path.relative_to(repo_root).as_posix(),
            "sha256": boundary_sha256,
            "decision_sha256": boundary_decision_sha256,
        },
        "bridge_receipt_artifact": {
            "path": bridge_receipt_path.relative_to(repo_root).as_posix(),
            "sha256": receipt_sha256,
        },
        "bridge_receipt": dict(receipt),
        "boundary_gaps": list(boundary.get("gaps", [])),
        "obligations": collections["obligations"],
        "dependency_bindings": collections["dependency_bindings"],
        "negative_oracles": collections["negative_oracles"],
        "requiredness_oracles": collections["requiredness_oracles"],
        "oracle_inventories": rendered_inventories,
    }


def _coverage_gap_affected_atom_sets(path: Path) -> dict[str, set[str]]:
    text = path.read_text(encoding="utf-8")
    matches = list(
        re.finditer(
            r"^#{2,4}\s+(GAP-[A-Za-z0-9_.-]+)(?:\s+[-—].*)?$",
            text,
            re.MULTILINE,
        )
    )
    result: dict[str, set[str]] = {}
    for index, match in enumerate(matches):
        gap_id = match.group(1)
        block = text[
            match.end() : (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )
        ]
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = _split_markdown_table_row(line)
            if len(cells) == 2 and cells[0].lower() not in {"field", "---"}:
                fields[cells[0].strip().casefold()] = cells[1]
        result[gap_id] = set(
            re.findall(
                r"ATOM-[A-Za-z0-9_.-]+",
                fields.get("affected_atom_id", ""),
            )
        )
    return result


def _validate_semantic_projection_graph(
    *,
    projection: Mapping[str, Any],
    manifest: SourceAssertionManifest,
    ledger_by_atom: Mapping[str, Mapping[str, str]],
    obligation_rows: Sequence[Mapping[str, str]],
    coverage_gaps_path: Path,
) -> dict[str, tuple[str, ...]]:
    receipt = projection.get("bridge_receipt")
    if not isinstance(receipt, Mapping):
        raise StageRuntimeError("semantic compiler projection is missing its bridge receipt")
    expected_receipt_bindings = {
        "source_assertion_manifest_digest": manifest.digest,
        "source_row_count": len(manifest.source_rows),
        "assertion_count": len(manifest.assertions),
        "testable_assertion_count": sum(
            assertion.semantic_disposition == "testable"
            for assertion in manifest.assertions
        ),
        "approved_clarification_count": len(manifest.clarifications),
    }
    for key, expected in expected_receipt_bindings.items():
        if receipt.get(key) != expected:
            raise StageRuntimeError(
                f"semantic design bridge receipt {key} does not match the accepted source manifest"
            )
    readiness = receipt.get("downstream_evidence_readiness")
    assert isinstance(readiness, Mapping)
    if readiness.get("published_manifest_digest") != manifest.digest:
        raise StageRuntimeError(
            "semantic design bridge receipt downstream preflight manifest digest does not "
            "match the accepted source manifest"
        )

    testable_assertions = tuple(
        assertion
        for assertion in manifest.assertions
        if assertion.semantic_disposition == "testable"
    )
    assertion_by_id = {
        assertion.assertion_id: assertion for assertion in testable_assertions
    }
    all_assertion_by_id = {
        assertion.assertion_id: assertion for assertion in manifest.assertions
    }
    expected_obligation_ids = tuple(
        obligation_id
        for assertion in testable_assertions
        for obligation_id in assertion.obligation_ids
    )
    semantic_obligations = projection.get("obligations")
    if not isinstance(semantic_obligations, list) or any(
        not isinstance(item, Mapping) for item in semantic_obligations
    ):
        raise StageRuntimeError("semantic compiler projection obligations are invalid")
    actual_obligation_ids = tuple(
        str(item.get("obligation_id", "")) for item in semantic_obligations
    )
    if (
        len(actual_obligation_ids) != len(set(actual_obligation_ids))
        or set(actual_obligation_ids) != set(expected_obligation_ids)
    ):
        raise StageRuntimeError(
            "semantic obligation set must equal the accepted testable source manifest: "
            f"expected={list(expected_obligation_ids)}, actual={list(actual_obligation_ids)}"
        )
    semantic_obligation_by_id = {
        str(item["obligation_id"]): item for item in semantic_obligations
    }
    materialized_by_id = {
        str(row.get("obligation_id", "")): row for row in obligation_rows
    }
    if len(materialized_by_id) != len(obligation_rows):
        raise StageRuntimeError(
            "semantic projection validation found duplicate materialized obligations"
        )
    assertion_by_obligation = {
        obligation_id: assertion
        for assertion in testable_assertions
        for obligation_id in assertion.obligation_ids
    }
    obligation_field_bindings = {
        "package_id": "package_id",
        "linked_atom_id": "linked_atom_id",
        "source_property_id": "source_property_id",
        "property_type": "property_type",
        "obligation_class": "obligation_class",
        "required_behavior": "required_behavior",
        "source_ref": "source_ref",
        "planned_tc_id": "planned_tc_or_gap",
        "review_notes": "review_notes",
    }
    for obligation_id, semantic_obligation in semantic_obligation_by_id.items():
        materialized = materialized_by_id.get(obligation_id)
        if materialized is None:
            raise StageRuntimeError(
                f"semantic obligation {obligation_id} is missing from materialized obligations"
            )
        for semantic_key, materialized_key in obligation_field_bindings.items():
            if str(semantic_obligation.get(semantic_key, "")) != str(
                materialized.get(materialized_key, "")
            ):
                raise StageRuntimeError(
                    f"semantic obligation {obligation_id}.{semantic_key} drifted from "
                    "the materialized coverage obligation"
                )
        owner = assertion_by_obligation[obligation_id]
        if semantic_obligation.get("linked_atom_id") != owner.atom_id:
            raise StageRuntimeError(
                f"semantic obligation {obligation_id} does not preserve its accepted ASSERT->ATOM chain"
            )
        if owner.atom_id not in ledger_by_atom:
            raise StageRuntimeError(
                f"semantic obligation {obligation_id} references missing ledger atom {owner.atom_id}"
            )

    dependency_bindings = projection.get("dependency_bindings")
    if not isinstance(dependency_bindings, list):
        raise StageRuntimeError("semantic compiler projection dependency_bindings are invalid")
    gap_bound_dependency_atoms: dict[str, set[str]] = {}
    for binding in dependency_bindings:
        if not isinstance(binding, Mapping):
            raise StageRuntimeError("semantic dependency binding must be an object")
        dependency_id = str(binding.get("dependency_id", "")) or "dependency"
        linked_assertion_ids = _semantic_string_array(
            binding,
            "linked_assertion_ids",
            label=dependency_id,
        )
        linked_atom_ids = _semantic_string_array(
            binding,
            "linked_atom_ids",
            label=dependency_id,
        )
        linked_obligation_ids = _semantic_string_array(
            binding,
            "linked_obligation_ids",
            label=dependency_id,
        )
        disposition = binding.get("semantic_disposition")
        resolution = binding.get("resolution")
        if disposition == "not-applicable":
            if resolution != "scope-excluded" or any(
                (linked_assertion_ids, linked_atom_ids, linked_obligation_ids)
            ):
                raise StageRuntimeError(
                    f"semantic dependency {dependency_id} has an invalid not-applicable graph"
                )
            continue
        if disposition == "gap-bound":
            gap_ids = _semantic_string_array(
                binding,
                "gap_ids",
                label=dependency_id,
            )
            if (
                resolution == "scope-excluded"
                or not gap_ids
                or not linked_assertion_ids
                or linked_obligation_ids
            ):
                raise StageRuntimeError(
                    f"semantic dependency {dependency_id} has an invalid gap-bound graph"
                )
            try:
                linked_assertions = tuple(
                    all_assertion_by_id[assertion_id]
                    for assertion_id in linked_assertion_ids
                )
            except KeyError as exc:
                raise StageRuntimeError(
                    f"semantic dependency {dependency_id} references an unknown assertion"
                ) from exc
            expected_atoms = tuple(
                assertion.atom_id for assertion in linked_assertions
            )
            if (
                linked_atom_ids != expected_atoms
                or any(
                    assertion.semantic_disposition == "testable"
                    or assertion.obligation_ids
                    for assertion in linked_assertions
                )
                or any(atom_id not in ledger_by_atom for atom_id in expected_atoms)
            ):
                raise StageRuntimeError(
                    f"semantic dependency {dependency_id} must preserve a non-testable "
                    "ASSERT->ATOM gap chain without obligations"
                )
            dependency_rows = set(
                _semantic_string_array(
                    binding,
                    "source_row_ids",
                    label=dependency_id,
                )
            ) | set(
                _semantic_string_array(
                    binding,
                    "target_source_row_ids",
                    label=dependency_id,
                )
            )
            for assertion in linked_assertions:
                assertion_rows = {
                    assertion.source_row_id,
                    *(
                        item.source_row_id
                        for item in assertion.supporting_source_bindings
                    ),
                }
                if not dependency_rows.intersection(assertion_rows):
                    raise StageRuntimeError(
                        f"semantic dependency {dependency_id} has no accepted "
                        f"source-row relation to {assertion.assertion_id}"
                    )
            for gap_id in gap_ids:
                gap_bound_dependency_atoms.setdefault(gap_id, set()).update(
                    expected_atoms
                )
            continue
        if disposition != "bound" or resolution == "scope-excluded":
            raise StageRuntimeError(
                f"semantic dependency {dependency_id} must be bound to an in-scope assertion graph"
            )
        if not linked_assertion_ids:
            raise StageRuntimeError(
                f"semantic dependency {dependency_id} requires a testable assertion chain"
            )
        try:
            linked_assertions = tuple(
                assertion_by_id[assertion_id]
                for assertion_id in linked_assertion_ids
            )
        except KeyError as exc:
            raise StageRuntimeError(
                f"semantic dependency {dependency_id} references an unknown/non-testable assertion"
            ) from exc
        expected_atoms = tuple(assertion.atom_id for assertion in linked_assertions)
        expected_obligations = tuple(
            obligation_id
            for assertion in linked_assertions
            for obligation_id in assertion.obligation_ids
        )
        if linked_atom_ids != expected_atoms or linked_obligation_ids != expected_obligations:
            raise StageRuntimeError(
                f"semantic dependency {dependency_id} must preserve the full ASSERT->ATOM->OBL chain"
            )
        if any(atom_id not in ledger_by_atom for atom_id in expected_atoms):
            raise StageRuntimeError(
                f"semantic dependency {dependency_id} references an unknown ledger atom"
            )
        if any(
            obligation_id not in semantic_obligation_by_id
            or obligation_id not in materialized_by_id
            for obligation_id in expected_obligations
        ):
            raise StageRuntimeError(
                f"semantic dependency {dependency_id} references an unknown obligation"
            )
        dependency_rows = set(
            _semantic_string_array(
                binding,
                "source_row_ids",
                label=dependency_id,
            )
        ) | set(
            _semantic_string_array(
                binding,
                "target_source_row_ids",
                label=dependency_id,
            )
        )
        for assertion in linked_assertions:
            assertion_rows = {
                assertion.source_row_id,
                *(item.source_row_id for item in assertion.supporting_source_bindings),
            }
            if not dependency_rows.intersection(assertion_rows):
                raise StageRuntimeError(
                    f"semantic dependency {dependency_id} has no accepted source-row relation "
                    f"to {assertion.assertion_id}"
                )

    scope_ids_by_obligation: dict[str, list[str]] = {
        obligation_id: [] for obligation_id in semantic_obligation_by_id
    }
    boundary_gaps = projection.get("boundary_gaps")
    if not isinstance(boundary_gaps, list) or any(
        not isinstance(item, Mapping) for item in boundary_gaps
    ):
        raise StageRuntimeError("semantic compiler projection boundary_gaps are invalid")
    boundary_gap_by_id = {
        str(item.get("gap_id", "")): item for item in boundary_gaps
    }
    if (
        any(not gap_id for gap_id in boundary_gap_by_id)
        or len(boundary_gap_by_id) != len(boundary_gaps)
        or any(item.get("blocking") is not False for item in boundary_gaps)
    ):
        raise StageRuntimeError(
            "ready semantic compiler projection requires unique non-blocking boundary gaps"
        )
    seen_scope_ids: set[str] = set()
    oracle_owner_by_obligation: dict[str, str] = {}
    # Some source restrictions require more than one independent calibration
    # class (for example N-1 and N+1) while the source-signal registry owns a
    # single generic oracle slot. The materializer preserves those additional
    # direct candidates through the semantic obligation marker, so the compiler
    # must reconstruct the same ownership instead of silently downgrading their
    # explicit calibration status to `none`.
    direct_candidate_obligation_ids = {
        obligation_id
        for obligation_id, obligation in semantic_obligation_by_id.items()
        if "candidate-ui-calibration"
        in str(obligation.get("review_notes", "")).casefold()
        and not obligation.get("scope_obligation_ids")
    }
    candidate_obligation_ids: set[str] = set(direct_candidate_obligation_ids)
    for collection_name, scope_prefix, signal_prefix in (
        ("negative_oracles", "SO-NEG-", "SIG-NEG-"),
        ("requiredness_oracles", "SO-REQ-", "SIG-REQ-"),
    ):
        collection = projection.get(collection_name)
        if not isinstance(collection, list):
            raise StageRuntimeError(
                f"semantic compiler projection {collection_name} is invalid"
            )
        for oracle in collection:
            if not isinstance(oracle, Mapping):
                raise StageRuntimeError(f"semantic {collection_name} entry must be an object")
            signal_id = str(oracle.get("signal_id", "")) or collection_name
            scope_id = str(oracle.get("scope_obligation_id", ""))
            obligation_id = str(oracle.get("linked_obligation_id", ""))
            atom_id = str(oracle.get("linked_atom_id", ""))
            source_row_id = str(oracle.get("source_row_id", ""))
            expected_scope_id = "SO-" + signal_id.removeprefix("SIG-")
            if (
                not signal_id.startswith(signal_prefix)
                or not scope_id.startswith(scope_prefix)
                or scope_id != expected_scope_id
                or scope_id in seen_scope_ids
                or obligation_id not in semantic_obligation_by_id
                or obligation_id not in materialized_by_id
            ):
                raise StageRuntimeError(
                    f"semantic oracle {signal_id} does not name one unique known scope/OBL chain"
                )
            seen_scope_ids.add(scope_id)
            semantic_obligation = semantic_obligation_by_id[obligation_id]
            materialized = materialized_by_id[obligation_id]
            if (
                atom_id != semantic_obligation.get("linked_atom_id")
                or atom_id != materialized.get("linked_atom_id")
                or atom_id not in ledger_by_atom
            ):
                raise StageRuntimeError(
                    f"semantic oracle {signal_id} does not preserve its materialized ATOM/OBL chain"
                )
            owner = assertion_by_obligation[obligation_id]
            allowed_source_rows = {
                owner.source_row_id,
                *(item.source_row_id for item in owner.supporting_source_bindings),
            }
            if source_row_id not in allowed_source_rows:
                raise StageRuntimeError(
                    f"semantic oracle {signal_id} source row is outside its accepted assertion evidence chain"
                )
            previous_scope_id = oracle_owner_by_obligation.get(obligation_id)
            if previous_scope_id is not None:
                raise StageRuntimeError(
                    f"semantic oracles {previous_scope_id} and {scope_id} collapse into {obligation_id}"
                )
            oracle_owner_by_obligation[obligation_id] = scope_id
            decision = oracle.get("decision")
            planned_target = oracle.get("planned_tc_or_gap")
            calibration_status = str(
                materialized.get("calibration_status", "")
            ).strip()
            ledger_status = str(
                ledger_by_atom[atom_id].get("coverage_status", "")
            ).strip().lower()
            if decision == "executable_tc":
                if planned_target != semantic_obligation.get("planned_tc_id"):
                    raise StageRuntimeError(
                        f"semantic oracle {signal_id} does not preserve its materialized planned TC"
                    )
                if calibration_status != "none":
                    raise StageRuntimeError(
                        f"semantic executable oracle {signal_id} requires explicit "
                        "materialized calibration_status=none"
                    )
            elif decision == "candidate_tc_required":
                if planned_target != f"candidate:{scope_id}":
                    raise StageRuntimeError(
                        f"semantic oracle {signal_id} does not preserve its candidate identity"
                    )
                if calibration_status != "ui-calibration-required":
                    raise StageRuntimeError(
                        f"semantic candidate oracle {signal_id} requires materialized "
                        "calibration_status=ui-calibration-required"
                    )
                if ledger_status != "covered_with_ui_calibration":
                    raise StageRuntimeError(
                        f"semantic candidate oracle {signal_id} requires its ATOM "
                        "coverage_status=covered_with_ui_calibration"
                    )
                candidate_obligation_ids.add(obligation_id)
                parent_gap_id = str(oracle.get("gap_id", ""))
                if parent_gap_id in boundary_gap_by_id:
                    materialized_constraints = set(
                        re.findall(
                            r"GAP-[A-Za-z0-9_.-]+",
                            str(
                                ledger_by_atom[atom_id].get(
                                    "constraint_gap_ids", ""
                                )
                            ),
                        )
                    )
                    if parent_gap_id not in materialized_constraints:
                        raise StageRuntimeError(
                            f"semantic candidate oracle {signal_id} parent gap "
                            f"{parent_gap_id} is missing from materialized ATOM constraints"
                        )
            else:
                raise StageRuntimeError(
                    f"ready semantic oracle {signal_id} has non-runnable decision {decision!r}"
                )
            scope_ids_by_obligation[obligation_id].append(scope_id)

    for obligation_id in sorted(direct_candidate_obligation_ids):
        semantic_obligation = semantic_obligation_by_id[obligation_id]
        materialized = materialized_by_id[obligation_id]
        atom_id = str(semantic_obligation.get("linked_atom_id", ""))
        if str(semantic_obligation.get("oracle_source", "")).strip() != "not_found":
            raise StageRuntimeError(
                f"direct semantic candidate {obligation_id} requires oracle_source=not_found"
            )
        if str(materialized.get("calibration_status", "")).strip() != (
            "ui-calibration-required"
        ):
            raise StageRuntimeError(
                f"direct semantic candidate {obligation_id} requires materialized "
                "calibration_status=ui-calibration-required"
            )
        if str(ledger_by_atom[atom_id].get("coverage_status", "")).strip().lower() != (
            "covered_with_ui_calibration"
        ):
            raise StageRuntimeError(
                f"direct semantic candidate {obligation_id} requires its ATOM "
                "coverage_status=covered_with_ui_calibration"
            )

    for obligation_id, materialized in materialized_by_id.items():
        if obligation_id not in semantic_obligation_by_id:
            continue
        expected_calibration = (
            "ui-calibration-required"
            if obligation_id in candidate_obligation_ids
            else "none"
        )
        if str(materialized.get("calibration_status", "")).strip() != expected_calibration:
            raise StageRuntimeError(
                f"semantic obligation {obligation_id} must materialize explicit "
                f"calibration_status={expected_calibration}"
            )

    oracle_atoms_by_gap: dict[str, set[str]] = {}
    for collection_name in ("negative_oracles", "requiredness_oracles"):
        for oracle in projection[collection_name]:
            assert isinstance(oracle, Mapping)
            gap_id = str(oracle.get("gap_id", ""))
            if gap_id in boundary_gap_by_id:
                oracle_atoms_by_gap.setdefault(gap_id, set()).add(
                    str(oracle.get("linked_atom_id", ""))
                )
    assertions_by_row: dict[str, set[str]] = {}
    testable_atom_ids: set[str] = set()
    primary_atoms_by_gap: dict[str, set[str]] = {}
    for assertion in manifest.assertions:
        assertions_by_row.setdefault(assertion.source_row_id, set()).add(
            assertion.atom_id
        )
        if assertion.semantic_disposition == "testable":
            testable_atom_ids.add(assertion.atom_id)
        if assertion.primary_gap_id is not None:
            primary_atoms_by_gap.setdefault(assertion.primary_gap_id, set()).add(
                assertion.atom_id
            )
    actual_affected_atoms = _coverage_gap_affected_atom_sets(
        coverage_gaps_path
    )
    expected_atoms_by_gap: dict[str, set[str]] = {}
    for gap_id, gap in boundary_gap_by_id.items():
        oracle_atoms = oracle_atoms_by_gap.get(gap_id, set())
        dependency_atoms = gap_bound_dependency_atoms.get(gap_id, set())
        primary_atoms = primary_atoms_by_gap.get(gap_id, set())
        row_atoms = {
            atom_id
            for source_row_id in gap.get("source_row_ids", [])
            for atom_id in assertions_by_row.get(str(source_row_id), set())
        }
        expected_atoms = (
            set(oracle_atoms)
            if oracle_atoms
            else set(dependency_atoms)
            if dependency_atoms
            else set(primary_atoms)
            if primary_atoms
            else set(actual_affected_atoms.get(gap_id, set()))
            if gap.get("gap_type") == "missing-source-definition"
            else row_atoms
        )
        if not expected_atoms:
            raise StageRuntimeError(
                f"authoritative boundary gap {gap_id} has no accepted affected ATOM"
            )
        if not expected_atoms.issubset(row_atoms):
            raise StageRuntimeError(
                f"authoritative boundary gap {gap_id} affects an ATOM outside its "
                f"source rows: {sorted(expected_atoms - row_atoms)}"
            )
        if (
            gap.get("gap_type") == "missing-source-definition"
            and not (oracle_atoms or dependency_atoms or primary_atoms)
            and any(
                atom_id in testable_atom_ids
                for atom_id in expected_atoms
            )
        ):
            raise StageRuntimeError(
                f"missing-source-definition gap {gap_id} cannot use an executable "
                "ATOM as its inferred affected chain"
            )
        expected_atoms_by_gap[gap_id] = expected_atoms

    actual_constraint_atoms_by_gap: dict[str, set[str]] = {
        gap_id: set() for gap_id in boundary_gap_by_id
    }
    for atom_id, row in ledger_by_atom.items():
        for gap_id in re.findall(
            r"GAP-[A-Za-z0-9_.-]+", str(row.get("constraint_gap_ids", ""))
        ):
            if gap_id in actual_constraint_atoms_by_gap:
                actual_constraint_atoms_by_gap[gap_id].add(atom_id)

    non_executable_gap_ids_by_atom: dict[str, set[str]] = {}
    for gap_id, expected_atoms in expected_atoms_by_gap.items():
        affected_atoms = actual_affected_atoms.get(gap_id, set())
        if affected_atoms != expected_atoms:
            raise StageRuntimeError(
                f"authoritative boundary gap {gap_id} affected ATOM set drifted: "
                f"expected={sorted(expected_atoms)}, actual={sorted(affected_atoms)}"
            )
        expected_constraint_atoms = expected_atoms & testable_atom_ids
        actual_constraint_atoms = actual_constraint_atoms_by_gap[gap_id]
        if actual_constraint_atoms != expected_constraint_atoms:
            raise StageRuntimeError(
                f"authoritative boundary gap {gap_id} constraint ATOM set drifted: "
                f"expected={sorted(expected_constraint_atoms)}, "
                f"actual={sorted(actual_constraint_atoms)}"
            )
        for atom_id in expected_atoms - testable_atom_ids:
            non_executable_gap_ids_by_atom.setdefault(atom_id, set()).add(
                gap_id
            )

    for gap_id, dependency_atoms in gap_bound_dependency_atoms.items():
        expected_atoms = expected_atoms_by_gap.get(gap_id)
        if expected_atoms is None or not dependency_atoms.issubset(expected_atoms):
            raise StageRuntimeError(
                f"gap-bound semantic dependency for {gap_id} is outside the "
                "authoritative affected ATOM set"
            )

    for obligation_id, semantic_obligation in semantic_obligation_by_id.items():
        expected_scope_ids = tuple(scope_ids_by_obligation[obligation_id])
        actual_scope_ids = _semantic_string_array(
            semantic_obligation,
            "scope_obligation_ids",
            label=obligation_id,
        )
        if actual_scope_ids != expected_scope_ids:
            raise StageRuntimeError(
                f"semantic obligation {obligation_id}.scope_obligation_ids does not match its oracle graph"
            )
        materialized_scope_cell = materialized_by_id[obligation_id].get(
            "scope_obligation_ids"
        )
        if materialized_scope_cell is not None:
            materialized_scope_ids = tuple(
                re.findall(r"SO-(?:NEG|REQ)-[A-Za-z0-9_.-]+", materialized_scope_cell)
            )
            if materialized_scope_ids != expected_scope_ids:
                raise StageRuntimeError(
                    f"semantic obligation {obligation_id}.scope_obligation_ids drifted from "
                    "the materialized coverage obligation"
                )
    return {
        atom_id: tuple(sorted(gap_ids))
        for atom_id, gap_ids in non_executable_gap_ids_by_atom.items()
    }


def _expected_source_assertion_rows(path: Path) -> tuple[SourceRow, ...]:
    rows = _table_with(
        path,
        {
            "source_row_id",
            "in_scope",
            "source_path",
            "source_locator",
            "bounded_source_text",
            "source_context_class",
            "requirement_codes",
            "candidate_id",
        },
    )
    expected: list[SourceRow] = []
    for row in rows:
        disposition = row["in_scope"].strip().lower()
        if disposition in {"no", "false", "out-of-scope", "not-applicable"}:
            scope_disposition = "no"
        elif disposition in {"yes", "true"}:
            scope_disposition = "yes"
        elif disposition in {"unclear", "ambiguous"}:
            scope_disposition = "unclear"
        else:
            raise StageRuntimeError(
                "source-row-inventory in_scope must be yes, unclear or no: "
                f"{row['source_row_id']}={row['in_scope']}"
            )
        source_row_id = row["source_row_id"].strip()
        if not re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", source_row_id):
            raise StageRuntimeError(
                f"invalid source assertion row id: {source_row_id}"
            )
        requirement_codes = _explicit_contract_values(
            row["requirement_codes"],
            label=f"source-row-inventory {source_row_id}.requirement_codes",
        )
        raw_candidate_id = row["candidate_id"].strip().strip("`").strip()
        candidate_id = None if raw_candidate_id == "none_required" else raw_candidate_id
        if candidate_id is not None and not candidate_id:
            raise StageRuntimeError(
                "source-row-inventory candidate_id must be explicit or none_required: "
                + source_row_id
            )
        expected.append(
            SourceRow.from_dict(
                {
                    "source_row_id": source_row_id,
                    "source_path": row["source_path"],
                    "source_locator": row["source_locator"],
                    "bounded_source_text": row["bounded_source_text"],
                    "source_context_class": row["source_context_class"],
                    "scope_disposition": scope_disposition,
                    "requirement_codes": list(requirement_codes),
                    "candidate_id": candidate_id,
                }
            )
        )
    if not expected:
        raise StageRuntimeError("source-row-inventory contains no in-scope source rows")
    if len(expected) != len({item.source_row_id for item in expected}):
        raise StageRuntimeError("source-row-inventory contains duplicate source_row_id values")
    return tuple(expected)


def _normalize_assertion_contract_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def _contains_exact_trace_token(context: str, value: str) -> bool:
    """Match one trace value without accepting identifier-prefix collisions."""

    normalized = _normalize_assertion_contract_text(value)
    if not normalized:
        return False
    return (
        re.search(
            rf"(?<![A-Za-z0-9_.-]){re.escape(normalized)}(?![A-Za-z0-9_.-])",
            _normalize_assertion_contract_text(context),
        )
        is not None
    )


def _explicit_contract_values(value: str, *, label: str) -> tuple[str, ...]:
    """Parse one mandatory semicolon-delimited contract cell without text scanning."""

    raw = value.strip()
    if raw == "none_required":
        return ()
    if raw.startswith("none_required:"):
        raise StageRuntimeError(
            f"{label} rejects qualified none_required sentinels; use exact none_required"
        )
    if not raw:
        raise StageRuntimeError(f"{label} must be explicit or none_required")
    if raw.casefold() in {"none", "not-applicable", "-"}:
        raise StageRuntimeError(
            f"{label} rejects placeholder sentinel {raw!r}; use none_required"
        )
    values = tuple(item.strip().strip("`").strip() for item in raw.split(";"))
    if any(not item for item in values):
        raise StageRuntimeError(f"{label} contains an empty value")
    if len(values) != len(set(values)):
        raise StageRuntimeError(f"{label} contains duplicate values")
    return values


def _validate_source_assertion_chain(
    *,
    manifest: SourceAssertionManifest,
    ledger_by_atom: Mapping[str, Mapping[str, str]],
    obligation_rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    assertion_by_atom = {item.atom_id: item for item in manifest.assertions}
    missing_atoms = sorted(set(ledger_by_atom) - set(assertion_by_atom))
    unknown_atoms = sorted(set(assertion_by_atom) - set(ledger_by_atom))
    if missing_atoms or unknown_atoms:
        raise StageRuntimeError(
            "source assertion to ledger ATOM set mismatch: "
            f"missing={missing_atoms}, unknown={unknown_atoms}"
        )

    obligation_by_id: dict[str, Mapping[str, str]] = {}
    rows_by_atom: dict[str, list[Mapping[str, str]]] = {}
    for row in obligation_rows:
        obligation_id = row.get("obligation_id", "").strip()
        if obligation_id in obligation_by_id:
            raise StageRuntimeError(
                f"source assertion chain found duplicate obligation {obligation_id}"
            )
        obligation_by_id[obligation_id] = row
        atom_ids = {
            token
            for token in TOKEN.findall(row.get("linked_atom_id", ""))
            if token.startswith("ATOM-")
        }
        if len(atom_ids) != 1:
            raise StageRuntimeError(
                f"source assertion chain requires exactly one ATOM for {obligation_id}"
            )
        rows_by_atom.setdefault(next(iter(atom_ids)), []).append(row)

    assertion_by_obligation: dict[str, Any] = {}
    for assertion in manifest.assertions:
        ledger_row = ledger_by_atom[assertion.atom_id]
        ledger_source_property_id = ledger_row.get("source_property_id", "").strip()
        if not ledger_source_property_id:
            raise StageRuntimeError(
                f"{assertion.assertion_id} ledger source_property_id is missing"
            )
        actual_statement = _normalize_assertion_contract_text(
            ledger_row.get("atomic_statement", "")
        )
        expected_statement = _normalize_assertion_contract_text(
            assertion.canonical_statement
        )
        if actual_statement != expected_statement:
            raise StageRuntimeError(
                "source assertion canonical statement mismatch: "
                f"{assertion.assertion_id} -> {assertion.atom_id}"
            )
        ledger_source_row_id = ledger_row.get("source_row_id", "").strip()
        if ledger_source_row_id != assertion.source_row_id:
            raise StageRuntimeError(
                f"{assertion.assertion_id} ledger source_row_id mismatch: "
                f"expected={assertion.source_row_id}, actual={ledger_source_row_id or 'missing'}"
            )
        ledger_requirement_codes = _explicit_contract_values(
            ledger_row.get("requirement_codes", ""),
            label=f"{assertion.atom_id}.requirement_codes",
        )
        if ledger_requirement_codes != assertion.requirement_codes:
            raise StageRuntimeError(
                f"{assertion.assertion_id} ledger requirement_codes mismatch: "
                f"expected={assertion.requirement_codes}, actual={ledger_requirement_codes}"
            )
        atom_rows = rows_by_atom.get(assertion.atom_id, [])
        for atom_row in atom_rows:
            obligation_id = atom_row.get("obligation_id", "").strip()
            obligation_source_property_id = atom_row.get(
                "source_property_id", ""
            ).strip()
            if obligation_source_property_id != ledger_source_property_id:
                raise StageRuntimeError(
                    f"{assertion.assertion_id} {obligation_id} source_property_id "
                    "mismatch: "
                    f"expected={ledger_source_property_id}, "
                    f"actual={obligation_source_property_id or 'missing'}"
                )
            obligation_source_row_id = atom_row.get("source_row_id", "").strip()
            if obligation_source_row_id != assertion.source_row_id:
                raise StageRuntimeError(
                    f"{assertion.assertion_id} {obligation_id} source_row_id mismatch: "
                    f"expected={assertion.source_row_id}, "
                    f"actual={obligation_source_row_id or 'missing'}"
                )
            obligation_requirement_codes = _explicit_contract_values(
                atom_row.get("requirement_codes", ""),
                label=f"{obligation_id}.requirement_codes",
            )
            if obligation_requirement_codes != assertion.requirement_codes:
                raise StageRuntimeError(
                    f"{assertion.assertion_id} {obligation_id} requirement_codes mismatch: "
                    f"expected={assertion.requirement_codes}, "
                    f"actual={obligation_requirement_codes}"
                )
        if assertion.semantic_disposition == "ambiguous":
            constraint_gap_ids = {
                token
                for token in TOKEN.findall(
                    ledger_row.get("constraint_gap_ids", "")
                )
                if token.startswith("GAP-")
            }
            if constraint_gap_ids:
                raise StageRuntimeError(
                    "constraint_gap_ids are allowed only on testable source assertions: "
                    f"{assertion.assertion_id} declares {sorted(constraint_gap_ids)}"
                )
            actual_primary_gap_ids: set[str] = set()
            for atom_row in atom_rows:
                if atom_row.get("status", "").strip().lower() not in {
                    "gap",
                    "unclear",
                    "blocked",
                }:
                    continue
                row_gap_ids = {
                    token
                    for token in TOKEN.findall(
                        " ".join(str(value) for value in atom_row.values())
                    )
                    if token.startswith("GAP-")
                } - constraint_gap_ids
                if len(row_gap_ids) != 1:
                    raise StageRuntimeError(
                        "ambiguous source assertion requires exactly one non-constraint "
                        "primary gap per ATOM/OBL chain: "
                        f"{assertion.assertion_id} found {sorted(row_gap_ids)}"
                    )
                actual_primary_gap_ids.update(row_gap_ids)
            expected_primary_gap_ids = {assertion.primary_gap_id}
            if actual_primary_gap_ids != expected_primary_gap_ids:
                raise StageRuntimeError(
                    "source assertion primary gap does not equal the actual non-constraint "
                    "ATOM/OBL gap: "
                    f"{assertion.assertion_id} declares {assertion.primary_gap_id}, "
                    f"actual={sorted(actual_primary_gap_ids)}"
                )

        row_ids = {row.get("obligation_id", "") for row in atom_rows}
        declared_ids = set(assertion.obligation_ids)
        if assertion.semantic_disposition == "testable":
            if declared_ids != row_ids:
                raise StageRuntimeError(
                    f"{assertion.assertion_id} obligation set mismatch: "
                    f"declared={sorted(declared_ids)}, actual={sorted(row_ids)}"
                )
            expected_obligation_status = (
                "blocked"
                if assertion.execution_readiness == "dependency-blocked"
                else "covered"
            )
            ledger_status = ledger_row.get("coverage_status", "").strip().lower()
            expected_ledger_status = (
                "blocked"
                if assertion.execution_readiness == "dependency-blocked"
                else "covered"
            )
            ledger_status_matches = (
                ledger_status == expected_ledger_status
                or (
                    expected_ledger_status == "covered"
                    and ledger_status.startswith("covered_with_")
                )
            )
            if not ledger_status_matches:
                raise StageRuntimeError(
                    f"testable source assertion {assertion.assertion_id} with "
                    f"execution_readiness={assertion.execution_readiness} requires "
                    f"ledger coverage_status={expected_ledger_status}, got "
                    f"{ledger_status or 'missing'}"
                )
            for obligation_id in assertion.obligation_ids:
                row = obligation_by_id[obligation_id]
                actual_obligation_status = row.get("status", "").strip().lower()
                if actual_obligation_status != expected_obligation_status:
                    raise StageRuntimeError(
                        f"testable source assertion {assertion.assertion_id} maps to "
                        f"{actual_obligation_status or 'missing'} {obligation_id}; "
                        f"expected {expected_obligation_status}"
                    )
                if expected_obligation_status == "blocked":
                    row_gap_ids = {
                        token
                        for token in TOKEN.findall(
                            " ".join(str(value) for value in row.values())
                        )
                        if token.startswith("GAP-")
                    }
                    declared_execution_gaps = set(
                        assertion.execution_dependency_gap_ids
                    )
                    if (
                        not row_gap_ids
                        or not row_gap_ids.issubset(declared_execution_gaps)
                    ):
                        raise StageRuntimeError(
                            "dependency-blocked source assertion must route every "
                            f"blocked obligation only through its declared execution "
                            f"gaps: {assertion.assertion_id} -> {obligation_id}, "
                            f"row={sorted(row_gap_ids)}, "
                            f"declared={sorted(declared_execution_gaps)}"
                        )
                assertion_by_obligation[obligation_id] = assertion
        else:
            executable_rows = [
                row.get("obligation_id", "")
                for row in atom_rows
                if row.get("status", "").strip().lower() == "covered"
            ]
            if executable_rows:
                raise StageRuntimeError(
                    f"{assertion.semantic_disposition} source assertion "
                    f"{assertion.assertion_id} maps to executable obligations: "
                    + ", ".join(executable_rows)
                )
    unknown_obligation_atoms = sorted(set(rows_by_atom) - set(assertion_by_atom))
    if unknown_obligation_atoms:
        raise StageRuntimeError(
            "obligation rows reference ATOMs absent from source assertions: "
            + ", ".join(unknown_obligation_atoms)
        )
    return assertion_by_atom, assertion_by_obligation


def _explicit_design_polarity(value: str) -> str:
    """Classify only explicit structured polarity vocabulary.

    Free text is deliberately ignored: this is a schema invariant, not a
    language heuristic.  Prefix/suffix forms cover canonical values such as
    ``negative-input`` and ``valid-value-positive``.
    """

    normalized = _normalized_design_value(value)
    if not normalized:
        return ""
    if (
        normalized == "negative"
        or normalized.startswith(("negative-", "invalid-", "reject-"))
        or normalized.endswith("-negative")
    ):
        return "negative"
    if (
        normalized == "positive"
        or normalized.startswith(("positive-", "valid-", "accept-"))
        or normalized.endswith("-positive")
    ):
        return "positive"
    return ""


def _row_explicit_polarities(
    row: Mapping[str, str],
    fields: Sequence[str],
) -> dict[str, str]:
    return {
        field: polarity
        for field in fields
        if (polarity := _explicit_design_polarity(row.get(field, "")))
    }


def _validate_source_assertion_design_alignment(
    *,
    manifest: SourceAssertionManifest,
    obligation_rows: Sequence[Mapping[str, str]],
    plan_by_atom: Mapping[str, Sequence[Mapping[str, str]]],
    obligations_path: Path,
    plan_path: Path,
    repo_root: Path,
) -> None:
    """Reject structured negative design inherited by a positive assertion.

    A positive assertion may not silently acquire a negative equivalence or
    input partition through cloned OBL/plan rows.  The check intentionally
    relies only on typed columns.  Neutral/unclassified values remain legal,
    and source-statement text is never guessed with regexes.
    """

    obligation_by_id = {
        row.get("obligation_id", "").strip(): row for row in obligation_rows
    }
    findings: list[dict[str, object]] = []
    for assertion in manifest.assertions:
        if (
            assertion.semantic_disposition != "testable"
            or assertion.polarity != "positive"
        ):
            continue
        declared_rows = [
            obligation_by_id[obligation_id]
            for obligation_id in assertion.obligation_ids
            if obligation_id in obligation_by_id
        ]
        planned_targets = {
            row.get("planned_tc_or_gap", "").strip() for row in declared_rows
        }
        for row in declared_rows:
            explicit = _row_explicit_polarities(
                row,
                ("property_type", "obligation_class"),
            )
            if "negative" not in explicit.values():
                continue
            obligation_id = row.get("obligation_id", "").strip()
            findings.append(
                {
                    "kind": "positive-assertion-negative-obligation",
                    "assertion_id": assertion.assertion_id,
                    "atom_id": assertion.atom_id,
                    "obligation_id": obligation_id,
                    "classified_fields": explicit,
                    **_artifact_anchor(
                        obligations_path,
                        obligation_id,
                        repo_root,
                    ),
                }
            )
        for row in plan_by_atom.get(assertion.atom_id, ()):
            if row.get("planned_tc_or_gap", "").strip() not in planned_targets:
                continue
            explicit = _row_explicit_polarities(
                row,
                ("check_type", "coverage_class", "input_class"),
            )
            if "negative" not in explicit.values():
                continue
            design_item_id = row.get("design_item_id", "").strip()
            findings.append(
                {
                    "kind": "positive-assertion-negative-plan",
                    "assertion_id": assertion.assertion_id,
                    "atom_id": assertion.atom_id,
                    "design_item_id": design_item_id,
                    "classified_fields": explicit,
                    **_artifact_anchor(
                        plan_path,
                        design_item_id or assertion.atom_id,
                        repo_root,
                    ),
                }
            )
    if findings:
        raise PreparedCompilerDiagnostic(
            "source-assertion-polarity-design-mismatch",
            "semantic degradation: a positive source assertion inherits an "
            "explicitly negative obligation or design partition; rematerialize "
            "the assertion-specific OBL/plan mapping",
            details=findings,
        )


def _validate_source_to_package_fidelity(
    *,
    path: Path,
    scope_slug: str,
    ledger_by_atom: Mapping[str, Mapping[str, str]],
    obligation_rows: Sequence[Mapping[str, str]],
    plan_by_atom: Mapping[str, Sequence[Mapping[str, str]]],
    known_gaps: Mapping[str, PreparedGap],
    repo_root: Path,
) -> tuple[dict[str, object], ...]:
    """Validate explicit high-risk source-to-package fidelity bindings.

    This contract is intentionally narrow.  It proves preservation of named
    literal/unit statements; it is not a general semantic equivalence checker.
    """

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StageRuntimeError(f"invalid source-to-package fidelity JSON: {path}") from exc
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise StageRuntimeError("source-to-package fidelity version must be 1")
    if raw.get("scope_slug") != scope_slug:
        raise StageRuntimeError(
            "source-to-package fidelity scope_slug must match workflow-state"
        )
    bindings = raw.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise StageRuntimeError("source-to-package fidelity bindings must be non-empty")

    obligations_by_id = {
        row.get("obligation_id", ""): row for row in obligation_rows
    }
    seen_ids: set[str] = set()
    normalized: list[dict[str, object]] = []
    allowed_targets = {
        "atomic_statement",
        "required_behavior",
        "single_expected_behavior",
    }
    for item in bindings:
        if not isinstance(item, dict):
            raise StageRuntimeError("source-to-package fidelity binding must be an object")
        binding_id = str(item.get("binding_id", "")).strip()
        kind = str(item.get("binding_kind", "")).strip()
        source_ref = str(item.get("source_ref", "")).strip()
        source_text = str(item.get("source_text", "")).strip()
        atom_id = str(item.get("atom_id", "")).strip()
        obligation_id = str(item.get("obligation_id", "")).strip()
        handling = str(item.get("handling", "")).strip()
        if not re.fullmatch(r"FID-[A-Za-z0-9_.-]+", binding_id):
            raise StageRuntimeError(f"invalid source fidelity binding id: {binding_id}")
        if binding_id in seen_ids:
            raise StageRuntimeError(f"duplicate source fidelity binding id: {binding_id}")
        seen_ids.add(binding_id)
        if not source_ref or not source_text:
            raise StageRuntimeError(f"{binding_id} requires source_ref and source_text")
        if atom_id not in ledger_by_atom:
            raise StageRuntimeError(f"{binding_id} references unknown atom {atom_id}")
        obligation = obligations_by_id.get(obligation_id)
        if obligation is None:
            raise StageRuntimeError(
                f"{binding_id} references unknown obligation {obligation_id}"
            )
        linked_atoms = {
            token
            for token in TOKEN.findall(obligation.get("linked_atom_id", ""))
            if token.startswith("ATOM-")
        }
        if linked_atoms != {atom_id}:
            raise StageRuntimeError(
                f"{binding_id} obligation {obligation_id} does not link {atom_id}"
            )

        targets_raw = item.get("required_targets", [])
        if not isinstance(targets_raw, list) or any(
            not isinstance(target, str) for target in targets_raw
        ):
            raise StageRuntimeError(f"{binding_id} required_targets must be a string list")
        targets = tuple(dict.fromkeys(targets_raw))
        unknown_targets = sorted(set(targets) - allowed_targets)
        if unknown_targets:
            raise StageRuntimeError(
                f"{binding_id} has unknown required_targets: {', '.join(unknown_targets)}"
            )

        target_values: dict[str, tuple[str, ...]] = {
            "atomic_statement": (
                ledger_by_atom[atom_id].get("atomic_statement", ""),
            ),
            "required_behavior": (obligation.get("required_behavior", ""),),
            "single_expected_behavior": tuple(
                row.get("single_expected_behavior", "")
                for row in plan_by_atom.get(atom_id, ())
            ),
        }
        if kind == "literal":
            if handling not in {"preserve", "locator-only"}:
                raise StageRuntimeError(
                    f"{binding_id} literal handling must be preserve or locator-only"
                )
            if handling == "locator-only":
                if targets:
                    raise StageRuntimeError(
                        f"{binding_id} locator-only binding cannot require projection targets"
                    )
                if not str(item.get("decision_reason", "")).strip():
                    raise StageRuntimeError(
                        f"{binding_id} locator-only binding requires decision_reason"
                    )
            elif not targets:
                raise StageRuntimeError(
                    f"{binding_id} preserve binding requires projection targets"
                )
        elif kind == "unit":
            if handling not in {
                "coverage-gap",
                "source-unit-only",
                "decimal-bytes",
                "binary-bytes",
            }:
                raise StageRuntimeError(f"{binding_id} has invalid unit handling")
            unit_value = item.get("unit_value")
            unit_symbol = str(item.get("unit_symbol", "")).strip()
            if not isinstance(unit_value, int) or unit_value <= 0 or not unit_symbol:
                raise StageRuntimeError(
                    f"{binding_id} unit binding requires positive unit_value and unit_symbol"
                )
            if not re.search(
                rf"(?<!\d){unit_value}\s*{re.escape(unit_symbol)}(?!\w)",
                source_text,
                flags=re.IGNORECASE,
            ):
                raise StageRuntimeError(
                    f"{binding_id} source_text must contain unit_value and unit_symbol"
                )
            if not targets:
                raise StageRuntimeError(
                    f"{binding_id} unit binding requires projection targets"
                )
            if handling in {"decimal-bytes", "binary-bytes"}:
                if not str(item.get("policy_source_ref", "")).strip():
                    raise StageRuntimeError(
                        f"{binding_id} byte conversion requires policy_source_ref"
                    )
                byte_offset = item.get("byte_offset")
                if not isinstance(byte_offset, int):
                    raise StageRuntimeError(
                        f"{binding_id} byte conversion requires integer byte_offset"
                    )
                base = 1_000_000 if handling == "decimal-bytes" else 1_048_576
                expected_bytes = unit_value * base + byte_offset
                byte_values = [
                    int(re.sub(r"\D", "", match.group()))
                    for values in target_values.values()
                    for value in values
                    for match in BYTE_VALUE.finditer(value)
                ]
                if not byte_values or any(
                    value != expected_bytes for value in byte_values
                ):
                    raise PreparedCompilerDiagnostic(
                        "source-fidelity-byte-conversion-mismatch",
                        "semantic degradation: exact byte projection does not match "
                        "the declared unit policy and offset",
                        details=(
                            {
                                "kind": "source-fidelity-byte-conversion-mismatch",
                                "binding_id": binding_id,
                                "atom_id": atom_id,
                                "obligation_id": obligation_id,
                                "expected_bytes": expected_bytes,
                                "actual_byte_values": sorted(set(byte_values)),
                                **_artifact_anchor(path, binding_id, repo_root),
                            },
                        ),
                    )
            else:
                byte_hits = [
                    value
                    for values in target_values.values()
                    for value in values
                    if BYTE_VALUE.search(value)
                ]
                if byte_hits:
                    raise PreparedCompilerDiagnostic(
                        "source-fidelity-unit-conversion-without-policy",
                        "semantic degradation: source unit was converted to exact bytes "
                        "without a source-backed policy",
                        details=(
                            {
                                "kind": "source-fidelity-unit-conversion-without-policy",
                                "binding_id": binding_id,
                                "atom_id": atom_id,
                                "obligation_id": obligation_id,
                                **_artifact_anchor(path, binding_id, repo_root),
                            },
                        ),
                    )
            if handling == "coverage-gap":
                gap_id = str(item.get("gap_id", "")).strip()
                ledger_status = ledger_by_atom[atom_id].get("coverage_status", "").lower()
                obligation_status = obligation.get("status", "").lower()
                linked_gap_tokens = {
                    token
                    for value in (
                        ledger_by_atom[atom_id].get("covered_by_tc", ""),
                        obligation.get("planned_tc_or_gap", ""),
                    )
                    for token in TOKEN.findall(value)
                    if token.startswith("GAP-")
                }
                if (
                    gap_id not in known_gaps
                    or ledger_status not in {"gap", "unclear"}
                    or obligation_status not in {"gap", "unclear"}
                    or linked_gap_tokens != {gap_id}
                ):
                    raise PreparedCompilerDiagnostic(
                        "source-fidelity-unit-gap-mismatch",
                        "semantic degradation: unresolved source unit must remain an "
                        "explicit linked coverage gap",
                        details=(
                            {
                                "kind": "source-fidelity-unit-gap-mismatch",
                                "binding_id": binding_id,
                                "atom_id": atom_id,
                                "obligation_id": obligation_id,
                                "gap_id": gap_id,
                                **_artifact_anchor(path, binding_id, repo_root),
                            },
                        ),
                    )
        else:
            raise StageRuntimeError(f"{binding_id} has invalid binding_kind: {kind}")

        if handling != "locator-only":
            missing_targets = [
                target
                for target in targets
                if not target_values[target]
                or any(source_text not in value for value in target_values[target])
            ]
            if missing_targets:
                raise PreparedCompilerDiagnostic(
                    "source-fidelity-literal-missing",
                    "semantic degradation: source literal is missing from required "
                    "prepared projection targets",
                    details=(
                        {
                            "kind": "source-fidelity-literal-missing",
                            "binding_id": binding_id,
                            "atom_id": atom_id,
                            "obligation_id": obligation_id,
                            "missing_targets": missing_targets,
                            **_artifact_anchor(path, binding_id, repo_root),
                        },
                    ),
                )
        normalized.append(
            {
                key: item[key]
                for key in sorted(item)
            }
        )
    return tuple(normalized)


def _explicit_gap_blocking(
    *,
    gap_id: str,
    labels: Sequence[str],
    boolean_labels: Sequence[str],
) -> bool:
    classifications: list[bool] = []
    for value in labels:
        normalized = value.strip().lower().replace("_", "-")
        if not normalized:
            continue
        if "non-blocking" in normalized:
            classifications.append(False)
        elif re.search(r"(?<!non-)\bblocking\b", normalized):
            classifications.append(True)
    for value in boolean_labels:
        normalized = value.strip().lower().replace("_", "-")
        if not normalized:
            continue
        if normalized in {"no", "false", "non-blocking"}:
            classifications.append(False)
        elif normalized in {"yes", "true", "blocking", "blocked"}:
            classifications.append(True)
    if not classifications:
        raise StageRuntimeError(
            f"source-first gap {gap_id} requires explicit blocking/non-blocking classification"
        )
    if len(set(classifications)) != 1:
        raise StageRuntimeError(
            f"source-first gap {gap_id} has conflicting blocking classifications"
        )
    return classifications[0]


def _gap_sections(
    path: Path | None,
    *,
    require_explicit_classification: bool = False,
) -> dict[str, PreparedGap]:
    if path is None:
        return {}
    text = path.read_text(encoding="utf-8")
    matches = list(
        re.finditer(
            r"^#{2,4}\s+(GAP-[A-Za-z0-9_.-]+)(?:\s+[-—].*)?$",
            text,
            re.MULTILINE,
        )
    )
    result: dict[str, PreparedGap] = {}
    for pos, match in enumerate(matches):
        block = text[match.end() : matches[pos + 1].start() if pos + 1 < len(matches) else len(text)]
        refs = tuple(dict.fromkeys(token for token in TOKEN.findall(block) if not token.startswith("GAP-")))
        field_values: dict[str, str] = {}
        for line in block.splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [_clean_cell(item) for item in line.strip().strip("|").split("|")]
            if len(cells) == 2 and cells[0].lower() not in {"field", "---"}:
                field_values[cells[0].lower()] = cells[1]
        impact = re.search(r"\*\*Impact:\*\*\s*`?([^`\n]+)", block, re.IGNORECASE)
        handling = re.search(r"\*\*Handling:\*\*\s*([^\n]+)", block, re.IGNORECASE)
        problem = re.search(r"\*\*(?:Problem|FT Reference):\*\*\s*([^\n]+)", block, re.IGNORECASE)
        source_ref = field_values.get("source") or field_values.get("source_ref")
        if not refs and source_ref:
            refs = (source_ref,)
        problem_text = (
            _clean_cell(problem.group(1))
            if problem
            else field_values.get("statement")
            or field_values.get("missing_artifact")
            or "Неопределённость зафиксирована в coverage gaps."
        )
        handling_text = (
            _clean_cell(handling.group(1))
            if handling
            else field_values.get("handling")
            or "Сохранить как coverage gap."
        )
        status_text = field_values.get("status", "").lower()
        if status_text.startswith(("closed", "resolved", "not-applicable")):
            continue
        gap_id = match.group(1)
        legacy_blocking = (
            bool(impact and "non-blocking" not in impact.group(1).lower())
            or status_text in {"blocking", "blocked"}
        )
        blocking = (
            _explicit_gap_blocking(
                gap_id=gap_id,
                labels=(
                    impact.group(1) if impact else "",
                    field_values.get("impact", ""),
                    field_values.get("severity", ""),
                    field_values.get("status", ""),
                ),
                boolean_labels=(
                    field_values.get("blocking", ""),
                    field_values.get("blocking_ready_for_review", ""),
                    field_values.get("blocks_ready_for_review", ""),
                    field_values.get("blocks_writer_draft", ""),
                ),
            )
            if require_explicit_classification
            else legacy_blocking
        )
        result[gap_id] = PreparedGap(
            gap_id=gap_id,
            source_refs=refs or (match.group(1),),
            problem=problem_text,
            handling=handling_text,
            blocking=blocking,
        )
    for table in markdown_tables(path):
        if not table or "gap_id" not in table[0]:
            continue
        for row in table:
            gap_id = row.get("gap_id", "")
            if not gap_id.startswith("GAP-") or gap_id in result:
                continue
            if row.get("status", "").lower().startswith(
                ("closed", "resolved", "not-applicable")
            ):
                continue
            refs = tuple(
                dict.fromkeys(
                    token
                    for token in TOKEN.findall(" ".join(row.values()))
                    if not token.startswith("GAP-")
                )
            )
            blocking_text = " ".join(
                row.get(key, "")
                for key in (
                    "impact",
                    "severity",
                    "blocking_ready_for_review",
                    "blocks_ready_for_review",
                    "blocks_writer_draft",
                )
            ).lower()
            problem = next(
                (
                    row[key]
                    for key in (
                        "gap_statement",
                        "description",
                        "missing_behavior",
                        "reason",
                    )
                    if row.get(key)
                ),
                "Неопределённость зафиксирована в coverage gaps.",
            )
            handling = next(
                (
                    row[key]
                    for key in ("downstream_handling", "temporary_handling", "handling")
                    if row.get(key)
                ),
                "Сохранить как coverage gap.",
            )
            legacy_blocking = (
                "blocking" in blocking_text
                and "non-blocking" not in blocking_text
                or re.search(r"\byes\b", blocking_text) is not None
            )
            blocking = (
                _explicit_gap_blocking(
                    gap_id=gap_id,
                    labels=tuple(
                        row.get(key, "")
                        for key in ("impact", "severity", "status")
                    ),
                    boolean_labels=tuple(
                        row.get(key, "")
                        for key in (
                            "blocking",
                            "blocking_ready_for_review",
                            "blocks_ready_for_review",
                            "blocks_writer_draft",
                        )
                    ),
                )
                if require_explicit_classification
                else legacy_blocking
            )
            result[gap_id] = PreparedGap(
                gap_id=gap_id,
                source_refs=refs or (gap_id,),
                problem=problem,
                handling=handling,
                blocking=blocking,
            )
    return result


def _resolved_gap_ids(path: Path | None) -> set[str]:
    """Return resolved GAP ids for orphan accounting, without making them active.

    ``_gap_sections`` deliberately excludes resolved records from ``PreparedGap``
    output.  They still belong to the current hash-bound registry and therefore
    must not disappear from integrity checks.  Only a manifest-validated approved
    clarification may exempt an exact resolved id later in compilation.
    """

    if path is None:
        return set()
    text = path.read_text(encoding="utf-8")
    matches = list(
        re.finditer(
            r"^#{2,4}\s+(GAP-[A-Za-z0-9_.-]+)(?:\s+[-—].*)?$",
            text,
            re.MULTILINE,
        )
    )
    resolved: set[str] = set()
    for position, match in enumerate(matches):
        block = text[
            match.end() : (
                matches[position + 1].start()
                if position + 1 < len(matches)
                else len(text)
            )
        ]
        bold_status = re.search(
            r"\*\*Status:\*\*\s*`?([^`\n]+)",
            block,
            re.IGNORECASE,
        )
        if (
            bold_status is not None
            and bold_status.group(1).strip().casefold() == "resolved"
        ):
            resolved.add(match.group(1))
            continue
        for line in block.splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [
                _clean_cell(item)
                for item in line.strip().strip("|").split("|")
            ]
            if (
                len(cells) == 2
                and cells[0].strip().casefold().replace(" ", "_") == "status"
                and cells[1].strip().casefold() == "resolved"
            ):
                resolved.add(match.group(1))
                break
    for table in markdown_tables(path):
        if not table or "gap_id" not in table[0] or "status" not in table[0]:
            continue
        resolved.update(
            row["gap_id"]
            for row in table
            if row.get("gap_id", "").startswith("GAP-")
            and row.get("status", "").strip().casefold() == "resolved"
        )
    return resolved


def _within(path: Path, root: Path, label: str) -> Path:
    path = path.resolve()
    root = root.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise StageRuntimeError(f"{label} escapes {root}: {path}") from exc
    return path


@dataclass(frozen=True)
class _SelectedSourceEntry:
    path: Path
    repo_relative_path: str
    source_selection_role: str
    manifest_binding: str | None
    sha256: str | None


_SOURCE_SELECTION_MANIFEST_BINDINGS = {
    "approved-clarification",
    "assertion-source",
    "semantic-source-of-truth",
    "structural-visual-parity",
    "supporting-material",
    "mockup",
    "not-used",
}

_SOURCE_SELECTION_ROLE_COMPATIBILITY = {
    "approved-clarification": {"approved-clarification", "not-used"},
    "main-ft-xhtml": {"assertion-source"},
    "main-ft-docx": {"semantic-source-of-truth"},
    "main-ft-pdf": {"structural-visual-parity", "not-used"},
    "support": {"supporting-material", "not-used"},
    "mandatory-package-context": {"supporting-material", "not-used"},
    "external-vendor-reference": {"supporting-material", "not-used"},
    "mockup": {"mockup", "not-used"},
}

_SOURCE_SELECTION_ROLE_SUFFIXES = {
    "approved-clarification": {".md"},
    "main-ft-xhtml": {".xhtml", ".html"},
    "main-ft-docx": {".docx"},
    "main-ft-pdf": {".pdf"},
}

_PREPARED_SOURCE_ROLES = {
    "main-ft-docx": "source-of-truth",
    "main-ft-xhtml": "machine-readable",
    "main-ft-pdf": "structural-cross-check",
}


def _selected_source_entries(
    *,
    repo_root: Path,
    ft_root: Path,
    source_selection: Path,
    require_manifest_binding: bool,
) -> tuple[_SelectedSourceEntry, ...]:
    repo_root = repo_root.resolve()
    ft_root = ft_root.resolve()
    required_columns = (
        {"path", "role", "sha256", "manifest_binding"}
        if require_manifest_binding
        else {"path", "role"}
    )
    candidate_tables = [
        table
        for table in markdown_tables(source_selection)
        if table and required_columns <= set(table[0])
    ]
    if not candidate_tables:
        raise StageRuntimeError(
            "source-selection requires a Markdown source registry with "
            + ", ".join(sorted(required_columns))
        )

    entries: list[_SelectedSourceEntry] = []
    selected_paths: set[str] = set()
    main_role_counts: dict[str, int] = {}
    for table in candidate_tables:
        for row in table:
            source_role = row["role"].strip()
            manifest_binding: str | None = None
            if require_manifest_binding:
                manifest_binding = row["manifest_binding"].strip()
                if manifest_binding not in _SOURCE_SELECTION_MANIFEST_BINDINGS:
                    raise StageRuntimeError(
                        "source-selection uses an unsupported manifest_binding: "
                        + manifest_binding
                    )
                allowed_bindings = _SOURCE_SELECTION_ROLE_COMPATIBILITY.get(
                    source_role
                )
                if allowed_bindings is None:
                    if manifest_binding != "not-used":
                        raise StageRuntimeError(
                            "unknown source-selection role requires "
                            f"manifest_binding=not-used: {source_role}"
                        )
                elif manifest_binding not in allowed_bindings:
                    raise StageRuntimeError(
                        "source-selection role/manifest_binding mismatch: "
                        f"{source_role} cannot use {manifest_binding}"
                    )
            elif source_role not in _PREPARED_SOURCE_ROLES:
                continue
            raw_path = PurePosixPath(row["path"])
            if raw_path.is_absolute():
                raise StageRuntimeError(
                    f"source-selection path must be FT-relative: {row['path']}"
                )
            path = _within(
                ft_root / Path(*raw_path.parts),
                ft_root,
                "selected source",
            )
            if not path.is_file():
                raise StageRuntimeError(f"selected source is missing: {row['path']}")
            repo_relative_path = path.relative_to(repo_root).as_posix()
            if repo_relative_path in selected_paths:
                raise StageRuntimeError(
                    "source-selection contains a path with multiple or duplicate roles: "
                    + repo_relative_path
                )
            selected_paths.add(repo_relative_path)

            suffixes = _SOURCE_SELECTION_ROLE_SUFFIXES.get(source_role)
            if suffixes is not None and path.suffix.lower() not in suffixes:
                raise StageRuntimeError(
                    f"{source_role} has invalid extension: {row['path']}"
                )
            if source_role.startswith("main-ft-"):
                main_role_counts[source_role] = main_role_counts.get(source_role, 0) + 1

            declared_sha = row.get("sha256", "").strip()
            if require_manifest_binding and re.fullmatch(r"[0-9a-f]{64}", declared_sha) is None:
                raise StageRuntimeError(
                    "source-selection manifest-bound rows require lowercase SHA-256: "
                    + repo_relative_path
                )
            entries.append(
                _SelectedSourceEntry(
                    path=path,
                    repo_relative_path=repo_relative_path,
                    source_selection_role=source_role,
                    manifest_binding=manifest_binding,
                    sha256=declared_sha or None,
                )
            )

    for required in ("main-ft-docx", "main-ft-xhtml"):
        if main_role_counts.get(required) != 1:
            raise StageRuntimeError(
                f"source-selection requires exactly one {required} source"
            )
    if main_role_counts.get("main-ft-pdf", 0) > 1:
        raise StageRuntimeError("source-selection allows at most one main-ft-pdf source")

    selected_by_role = {
        item.source_selection_role: item.path
        for item in entries
        if item.source_selection_role.startswith("main-ft-")
        and item.manifest_binding != "not-used"
    }
    if selected_by_role["main-ft-docx"].stem != selected_by_role["main-ft-xhtml"].stem:
        raise StageRuntimeError("selected DOCX and XHTML/HTML must have the same base name")
    if (
        "main-ft-pdf" in selected_by_role
        and selected_by_role["main-ft-docx"].stem
        != selected_by_role["main-ft-pdf"].stem
    ):
        raise StageRuntimeError("selected DOCX and PDF must have the same base name")

    text = source_selection.read_text(encoding="utf-8")
    if not re.search(r"xhtml_available:\s*`?yes`?", text, re.IGNORECASE):
        raise StageRuntimeError("source-selection does not confirm xhtml_available: yes")
    if not re.search(r"xhtml_matches_main_ft:\s*`?yes`?", text, re.IGNORECASE):
        raise StageRuntimeError("source-selection does not confirm xhtml_matches_main_ft: yes")
    return tuple(entries)


def _validate_source_selection_manifest_binding(
    *,
    repo_root: Path,
    ft_root: Path,
    source_selection: Path,
    manifest: SourceAssertionManifest,
) -> tuple[_SelectedSourceEntry, ...]:
    entries = _selected_source_entries(
        repo_root=repo_root,
        ft_root=ft_root,
        source_selection=source_selection,
        require_manifest_binding=True,
    )
    expected_sources: set[tuple[str, str]] = set()
    expected_evidence: set[tuple[str, str, str]] = set()
    expected_mockups: set[tuple[str, str]] = set()
    for item in entries:
        assert item.sha256 is not None
        assert item.manifest_binding is not None
        if item.manifest_binding == "not-used":
            continue
        if item.manifest_binding == "assertion-source":
            expected_sources.add((item.repo_relative_path, item.sha256))
        elif item.manifest_binding in {
            "approved-clarification",
            "semantic-source-of-truth",
            "structural-visual-parity",
            "supporting-material",
        }:
            expected_evidence.add(
                (item.repo_relative_path, item.sha256, item.manifest_binding)
            )
        else:
            expected_mockups.add((item.repo_relative_path, item.sha256))

    actual_sources = {(item.path, item.sha256) for item in manifest.sources}
    actual_evidence = {
        (item.path, item.sha256, item.role) for item in manifest.evidence_sources
    }
    actual_mockups = {(item.path, item.sha256) for item in manifest.mockups}
    mismatches = []
    for label, expected, actual in (
        ("sources", expected_sources, actual_sources),
        ("evidence_sources", expected_evidence, actual_evidence),
        ("mockups", expected_mockups, actual_mockups),
    ):
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        if missing or unexpected:
            mismatches.append(
                f"{label}: missing={missing or 'none'}, unexpected={unexpected or 'none'}"
            )
    if mismatches:
        raise StageRuntimeError(
            "source-selection manifest registry mismatch: " + "; ".join(mismatches)
        )
    return entries


def _validate_source_row_baseline_binding(
    *,
    repo_root: Path,
    extraction_spec_path: Path,
    baseline_path: Path,
    manifest: SourceAssertionManifest,
    scope_slug: str,
    selected_xhtml: _SelectedSourceEntry,
) -> SourceRowCompletenessResult:
    mappings = tuple(
        SourceRowCandidateMapping(
            source_row_id=row.source_row_id,
            source_path=row.source_path,
            source_locator=row.source_locator,
            bounded_source_text=row.bounded_source_text,
            source_context_class=row.source_context_class,
            candidate_id=row.candidate_id,
        )
        for row in manifest.source_rows
    )
    try:
        extraction_spec = load_extraction_spec(extraction_spec_path)
        if extraction_spec.scope_slug != scope_slug:
            raise SourceRowBaselineValidationError(
                "extraction-spec-scope-mismatch",
                "source-row extraction spec.scope_slug must match workflow-state",
            )
        selected = extraction_spec.selected_xhtml
        if (
            selected.relative_path != selected_xhtml.repo_relative_path
            or selected.sha256 != selected_xhtml.sha256
        ):
            raise SourceRowBaselineValidationError(
                "extraction-spec-source-selection-mismatch",
                "source-row extraction spec.selected_xhtml must match the exact "
                "main-ft-xhtml source-selection row",
            )
        result = validate_source_row_completeness(
            repo_root=repo_root,
            extraction_spec_path=extraction_spec_path,
            baseline_path=baseline_path,
            source_row_mappings=mappings,
        )
    except SourceRowBaselineValidationError as exc:
        raise StageRuntimeError(
            f"source-row baseline contract failed: {exc}"
        ) from exc

    mismatches: list[str] = []
    for field_name, expected, actual in (
        (
            "source_row_extraction_spec_digest",
            manifest.source_row_extraction_spec_digest,
            result.source_row_extraction_spec_digest,
        ),
        (
            "source_row_baseline_digest",
            manifest.source_row_baseline_digest,
            result.source_row_baseline_digest,
        ),
        (
            "source_row_candidate_count",
            manifest.source_row_candidate_count,
            result.candidate_count,
        ),
    ):
        if expected != actual:
            mismatches.append(
                f"{field_name}: manifest={expected}, baseline={actual}"
            )
    if mismatches:
        raise StageRuntimeError(
            "source-row baseline manifest binding mismatch: "
            + "; ".join(mismatches)
        )
    return result


def _source_registry(
    repo_root: Path,
    ft_root: Path,
    source_selection: Path,
    *,
    require_manifest_binding: bool,
) -> list[tuple[Path, str, str]]:
    entries = _selected_source_entries(
        repo_root=repo_root,
        ft_root=ft_root,
        source_selection=source_selection,
        require_manifest_binding=require_manifest_binding,
    )
    return [
        (
            item.path,
            _PREPARED_SOURCE_ROLES[item.source_selection_role],
            f"pinned by {source_selection.name}",
        )
        for item in entries
        if item.source_selection_role in _PREPARED_SOURCE_ROLES
        and item.manifest_binding != "not-used"
    ]


def _applicability_review_dimensions(row: Mapping[str, str]) -> tuple[str, ...]:
    applicability = row["applicable"].lower()
    if applicability == "no":
        return ()
    evidence_qualified = applicability.startswith("yes_with_")
    if applicability not in {"yes", "unclear", "unclear-limited"} and not evidence_qualified:
        raise StageRuntimeError(
            "test-design applicability must be yes, no, unclear or yes_with_*: "
            f"{row['dimension']}={row['applicable']}"
        )
    dimension = re.sub(
        r"[^a-z0-9_.-]+", "-", row["dimension"].lower()
    ).strip("-")
    if applicability == "unclear":
        if not any(
            token.startswith("GAP-") for token in TOKEN.findall(" ".join(row.values()))
        ):
            raise StageRuntimeError(
                f"unclear test-design dimension must link a GAP id: {row['dimension']}"
            )
        return ()
    if applicability == "unclear-limited":
        return ("limited-default-oracle",)
    routed: list[str] = []
    if evidence_qualified:
        qualifier = applicability.removeprefix("yes_with_").replace("_", "-")
        routed.append(f"evidence-qualified-{qualifier}")
    if dimension not in FAST_DIMENSIONS:
        normalized = DIMENSION_GROUPS.get(
            dimension, re.sub(r"[^a-z0-9_.-]+", "-", dimension).strip("-")
        )
        routed.append(normalized or "unclassified-dimension")
    return tuple(dict.fromkeys(routed))


def _execution_route(applicability_matrix: Path) -> tuple[str, tuple[str, ...]]:
    rows = _table_with(applicability_matrix, {"dimension", "applicable"})
    unsupported = {
        dimension
        for row in rows
        for dimension in _applicability_review_dimensions(row)
    }
    if unsupported:
        return STANDARD_PROFILE, tuple(sorted(unsupported))
    return FAST_PROFILE, ()


def _obligation_review_dimension(row: Mapping[str, str]) -> str:
    if row.get("status", "").lower() != "covered":
        return ""
    property_type = re.sub(
        r"[^a-z0-9_.-]+", "-", row.get("property_type", "").lower()
    ).strip("-")
    return OBLIGATION_DIMENSION_GROUPS.get(property_type, "")


def _route_obligation_dimensions(
    rows: Sequence[Mapping[str, str]],
    unsupported_dimensions: Sequence[str],
) -> tuple[str, tuple[str, ...]]:
    unsupported = set(unsupported_dimensions)
    for row in rows:
        mapped = _obligation_review_dimension(row)
        if mapped:
            unsupported.add(mapped)
    if unsupported:
        return STANDARD_PROFILE, tuple(sorted(unsupported))
    return FAST_PROFILE, ()


def _source_ref_cell_values(value: str) -> tuple[str, ...]:
    refs: list[str] = []
    for raw in re.split(r"\s*;\s*", value.strip()):
        ref = raw.strip().strip("`").strip()
        normalized = ref.lower()
        if not ref or normalized in {"-", "n/a", "not-applicable"}:
            continue
        if normalized.startswith(("none_required:", "not_covered:", "unclear:")):
            continue
        refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _source_first_dimension_bindings(
    *,
    applicability_rows: Sequence[Mapping[str, str]],
    obligation_rows: Sequence[Mapping[str, str]],
    obligations: Sequence[PreparedObligation],
    ledger_by_atom: Mapping[str, Mapping[str, str]],
    routed_dimensions: Sequence[str],
) -> ReviewerDimensionSourceBindings:
    binding_values: dict[str, list[str]] = {
        dimension: [] for dimension in routed_dimensions
    }

    def bind(dimension: str, source_refs: Sequence[str]) -> None:
        if dimension not in binding_values:
            raise StageRuntimeError(
                f"reviewer dimension binding references unrouted dimension {dimension}"
            )
        for source_ref in source_refs:
            if source_ref not in binding_values[dimension]:
                binding_values[dimension].append(source_ref)

    for row in applicability_rows:
        dimensions = _applicability_review_dimensions(row)
        if not dimensions:
            continue
        refs = _source_ref_cell_values(row.get("source_ref", ""))
        for dimension in dimensions:
            bind(dimension, refs)

    compiled_by_id = {item.obligation_id: item for item in obligations}
    for row in obligation_rows:
        obligation = compiled_by_id.get(row["obligation_id"])
        if obligation is None:
            raise StageRuntimeError(
                "reviewer dimension binding cannot find compiled obligation "
                + row["obligation_id"]
            )
        mapped = _obligation_review_dimension(row)
        if mapped:
            bind(mapped, obligation.source_refs)
        ledger_row = ledger_by_atom[obligation.traceability_atom_id]
        coverage_status = ledger_row.get("coverage_status", "").lower()
        if coverage_status.startswith("covered_with_"):
            qualifier = coverage_status.removeprefix("covered_with_").replace("_", "-")
            bind(f"evidence-qualified-{qualifier}", obligation.source_refs)

    missing = sorted(
        dimension for dimension, source_refs in binding_values.items() if not source_refs
    )
    if missing:
        raise StageRuntimeError(
            "source-first routed dimensions require deterministic source_ref bindings: "
            + ", ".join(missing)
        )
    return ReviewerDimensionSourceBindings.create(binding_values)


@dataclass(frozen=True)
class CompileResult:
    stage_package: Path
    obligation_count: int
    gap_count: int
    dictionary_ref_count: int
    section_id: str
    execution_profile: str
    unsupported_dimensions: tuple[str, ...]
    output_mode: str
    release_eligible: bool
    blocking_gap_ids: tuple[str, ...]
    release_blocking_finding_codes: tuple[str, ...]
    execution_dependency_count: int
    excluded_execution_obligation_ids: tuple[str, ...]
    cache_reused: bool


def compile_workflow_package(
    *,
    workflow_state: Path,
    repo_root: Path,
    output_root: Path,
    package_id: str,
    attempt_root: Path,
    expected_ft_slug: str,
    section_id: str | None = None,
    reuse_if_current: bool = False,
    output_mode: str = RELEASE_OUTPUT_MODE,
) -> CompileResult:
    repo_root = repo_root.resolve()
    workflow_state = workflow_state.resolve()
    output_root = output_root.resolve()
    attempt_root = attempt_root.resolve()
    output_existed = output_root.exists()
    if output_mode not in OUTPUT_MODES:
        raise StageRuntimeError(
            "output_mode must be one of " + ", ".join(sorted(OUTPUT_MODES))
        )
    expected_ft_root = (repo_root / "fts" / expected_ft_slug).resolve()
    if not expected_ft_root.is_dir():
        raise StageRuntimeError(f"expected FT package is missing: fts/{expected_ft_slug}")
    _within(workflow_state, expected_ft_root, "workflow-state")
    state = load_workflow_state(workflow_state)
    contract_version = state.get("prepared_compiler_contract_version")
    if contract_version not in SUPPORTED_COMPILER_CONTRACT_VERSIONS:
        raise StageRuntimeError(
            "workflow-state prepared_compiler_contract_version must be one of "
            f"{sorted(SUPPORTED_COMPILER_CONTRACT_VERSIONS)}; "
            "run scripts/migrate_prepared_compiler_contract.py"
        )
    source_first_contract = contract_version == COMPILER_CONTRACT_VERSION
    if (
        output_mode == DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE
        and not source_first_contract
    ):
        raise StageRuntimeError(
            "draft-with-blocking-gaps output requires source-first compiler contract v3"
        )
    ft_slug = str(state.get("ft_slug", ""))
    scope_slug = str(state.get("scope_slug", ""))
    if not ft_slug or not scope_slug:
        raise StageRuntimeError("workflow-state requires ft_slug and scope_slug")
    if ft_slug != expected_ft_slug:
        raise StageRuntimeError(
            f"workflow-state ft_slug mismatch: expected {expected_ft_slug}, found {ft_slug}"
        )
    ft_root = expected_ft_root
    review_cycles_root = ft_root / "work" / "review-cycles"
    output_relative = _within(output_root, review_cycles_root, "prepared output").relative_to(
        review_cycles_root
    )
    attempt_relative = _within(attempt_root, review_cycles_root, "attempt root").relative_to(
        review_cycles_root
    )
    if not output_relative.parts or not attempt_relative.parts:
        raise StageRuntimeError("prepared output and attempt root require a cycle id")
    if output_relative.parts[0] != attempt_relative.parts[0]:
        raise StageRuntimeError("prepared output and attempt root must belong to the same cycle")
    if (
        len(output_relative.parts) != 3
        or output_relative.parts[1] != "prepared-input"
        or output_relative.parts[2] != package_id
    ):
        raise StageRuntimeError("prepared output must be under <cycle>/prepared-input/<package-id>")
    if len(attempt_relative.parts) != 4 or attempt_relative.parts[1] != "attempts":
        raise StageRuntimeError("attempt root must be under <cycle>/attempts/<stage>/<attempt-id>")

    compiler_artifacts = _resolve_declared_compiler_artifacts(
        ft_root=ft_root,
        state=state,
        source_first_contract=source_first_contract,
    )
    source_selection_path = compiler_artifacts["source_selection"]
    ledger_path = compiler_artifacts["atomic_requirements_ledger"]
    obligations_path = compiler_artifacts["coverage_obligation_table"]
    plan_path = compiler_artifacts["package_test_design_plan"]
    applicability_path = compiler_artifacts["test_design_applicability_matrix"]
    decision_path = compiler_artifacts["test_design_decision_table"]
    gaps_path = compiler_artifacts["coverage_gaps"]
    dictionary_path = compiler_artifacts["dictionary_inventory"]
    source_fidelity_path = compiler_artifacts["source_to_package_fidelity"]
    source_row_inventory_path = compiler_artifacts["source_row_inventory"]
    source_row_extraction_spec_path = compiler_artifacts[
        "source_row_extraction_spec"
    ]
    source_row_baseline_path = compiler_artifacts["source_row_baseline"]
    source_assertions_path = compiler_artifacts["source_assertions"]
    source_assertion_review_path = compiler_artifacts["source_assertion_review"]
    semantic_design_path = compiler_artifacts["semantic_design"]
    scope_boundary_decision_path = compiler_artifacts["scope_boundary_decision"]
    semantic_bridge_receipt_path = compiler_artifacts[
        "semantic_design_bridge_receipt"
    ]
    negative_oracle_inventory_path = compiler_artifacts[
        "negative_oracle_inventory"
    ]
    requiredness_oracle_inventory_path = compiler_artifacts[
        "requiredness_oracle_inventory"
    ]
    assert (
        source_selection_path is not None
        and ledger_path is not None
        and obligations_path is not None
        and plan_path is not None
        and applicability_path is not None
    )
    semantic_projection = (
        _load_semantic_compiler_projection(
            repo_root=repo_root,
            package_id=package_id,
            semantic_design_path=semantic_design_path,
            scope_boundary_path=scope_boundary_decision_path,
            bridge_receipt_path=semantic_bridge_receipt_path,
            negative_inventory_path=negative_oracle_inventory_path,
            requiredness_inventory_path=requiredness_oracle_inventory_path,
        )
        if semantic_design_path is not None
        else None
    )
    external_dynamic_dependencies_by_obligation = (
        _external_dynamic_dictionary_dependencies_by_obligation(
            semantic_projection
        )
    )
    execution_profile, unsupported_dimensions = _execution_route(applicability_path)
    ledger_required_columns = {
        "atom_id",
        "atomic_statement",
        "coverage_status",
    }
    if source_first_contract:
        ledger_required_columns.update({"source_row_id", "requirement_codes"})
    ledger = _table_with(ledger_path, ledger_required_columns)
    obligation_required_columns = {
        "obligation_id",
        "package_id",
        "source_property_id",
        "linked_atom_id",
        "property_type",
        "obligation_class",
        "required_behavior",
        "source_ref",
        "planned_tc_or_gap",
        "status",
        "review_notes",
    }
    if source_first_contract:
        obligation_required_columns.update({"source_row_id", "requirement_codes"})
    obligation_rows = _table_with(
        obligations_path,
        obligation_required_columns,
    )
    execution_profile, unsupported_dimensions = _route_obligation_dimensions(
        obligation_rows, unsupported_dimensions
    )
    routed_unsupported_dimensions = set(unsupported_dimensions)
    environment_bound_fixtures = _environment_bound_fixture_lines(plan_path)
    if environment_bound_fixtures:
        raise PreparedCompilerDiagnostic(
            "environment-bound-fixture",
            "semantic degradation: FT-first package requires an environment-bound fixture; "
            "use a portable synthetic, relative-date or runtime-selected fixture and defer "
            "stand binding to UI automation preparation",
            details=tuple(
                {
                    "kind": "environment-bound-fixture",
                    "artifact": plan_path.relative_to(repo_root).as_posix(),
                    "line": line_no,
                    "text": text,
                }
                for line_no, text in environment_bound_fixtures
            ),
        )
    fixture_contract_lines = _fixture_contract_lines(plan_path)
    generic_fixture_contract_lines = tuple(
        (fixture_id, text)
        for fixture_id, text in fixture_contract_lines
        if GENERIC_FIXTURE_VALUE.search(text)
    )
    if generic_fixture_contract_lines:
        raise PreparedCompilerDiagnostic(
            "generic-execution-fixture",
            "semantic degradation: an inline named fixture contract must enumerate "
            "its executable controls and values instead of referring to unnamed "
            "other required controls",
            details=tuple(
                {
                    "kind": "generic-execution-fixture",
                    "fixture_id": fixture_id,
                    "value": text,
                    **_artifact_anchor(plan_path, fixture_id, repo_root),
                }
                for fixture_id, text in generic_fixture_contract_lines
            ),
        )
    fixture_contracts: dict[str, tuple[str, ...]] = {}
    for fixture_id, text in fixture_contract_lines:
        fixture_contracts[fixture_id] = tuple(
            dict.fromkeys((*fixture_contracts.get(fixture_id, ()), text))
        )
    plan = _table_with(plan_path, {"linked_atoms", "planned_check", "single_expected_behavior"})
    referenced_fixtures = {
        fixture_id
        for row in plan
        for value in row.values()
        for fixture_id in FIXTURE_TOKEN.findall(value)
    }
    missing_fixture_contracts = sorted(referenced_fixtures - fixture_contracts.keys())
    if missing_fixture_contracts:
        raise PreparedCompilerDiagnostic(
            "missing-fixture-contract",
            "semantic degradation: named fixture is referenced without an inline portable "
            "contract in the design plan",
            details=tuple(
                {
                    "kind": "missing-fixture-contract",
                    "fixture_id": fixture_id,
                    **_artifact_anchor(plan_path, fixture_id, repo_root),
                }
                for fixture_id in missing_fixture_contracts
            ),
        )
    decision_rows = (
        _table_with(decision_path, {"linked_atom_id", "planned_tc_or_gap"})
        if decision_path is not None
        else None
    )
    ledger_by_atom: dict[str, dict[str, str]] = {}
    for row in ledger:
        atom_id = row["atom_id"]
        if not re.fullmatch(r"ATOM-[A-Za-z0-9_.-]+", atom_id):
            raise StageRuntimeError(f"semantic degradation: invalid atom id {atom_id}")
        if atom_id in ledger_by_atom:
            raise StageRuntimeError(f"semantic degradation: duplicate atom {atom_id}")
        ledger_by_atom[atom_id] = row
    source_assertion_manifest: SourceAssertionManifest | None = None
    source_assertion_review = None
    source_assertion_by_atom: dict[str, Any] = {}
    source_assertion_by_obligation: dict[str, Any] = {}
    source_first_testable_completeness: dict[str, object] | None = None
    execution_dependency_registry: tuple[dict[str, object], ...] = ()
    dependency_blocked_obligation_ids: set[str] = set()
    dependency_blocked_atom_ids: set[str] = set()
    execution_dependency_gap_ids: set[str] = set()
    semantic_non_executable_boundary_gap_ids_by_atom: dict[
        str, tuple[str, ...]
    ] = {}
    if source_first_contract:
        assert source_row_inventory_path is not None
        assert source_row_extraction_spec_path is not None
        assert source_row_baseline_path is not None
        assert source_assertions_path is not None
        assert source_assertion_review_path is not None
        try:
            expected_source_assertion_rows = _expected_source_assertion_rows(
                source_row_inventory_path
            )
            source_assertion_manifest = load_source_assertion_manifest(
                source_assertions_path,
                repo_root,
                expected_source_rows=expected_source_assertion_rows,
            )
            if source_assertion_manifest.scope_slug != scope_slug:
                raise StageRuntimeError(
                    "source assertion manifest scope_slug must match workflow-state"
                )
            if gaps_path is None:
                raise StageRuntimeError(
                    "source-first compiler requires the hash-bound coverage_gaps artifact"
                )
            expected_coverage_gaps_path = gaps_path.relative_to(repo_root).as_posix()
            if (
                source_assertion_manifest.coverage_gaps_artifact.path
                != expected_coverage_gaps_path
            ):
                raise StageRuntimeError(
                    "source assertion manifest coverage_gaps_artifact path must match "
                    "workflow-state latest_artifacts.coverage_gaps"
                )
            selected_source_entries = _validate_source_selection_manifest_binding(
                repo_root=repo_root,
                ft_root=ft_root,
                source_selection=source_selection_path,
                manifest=source_assertion_manifest,
            )
            selected_xhtml = next(
                item
                for item in selected_source_entries
                if item.source_selection_role == "main-ft-xhtml"
            )
            _validate_source_row_baseline_binding(
                repo_root=repo_root,
                extraction_spec_path=source_row_extraction_spec_path,
                baseline_path=source_row_baseline_path,
                manifest=source_assertion_manifest,
                scope_slug=scope_slug,
                selected_xhtml=selected_xhtml,
            )
            source_assertion_review = load_source_assertion_review_receipt(
                source_assertion_review_path,
                source_assertion_manifest,
                require_accepted=True,
            )
        except SourceAssertionContractError as exc:
            raise StageRuntimeError(
                f"source-first compiler contract failed: {exc}"
            ) from exc
        (
            source_assertion_by_atom,
            source_assertion_by_obligation,
        ) = _validate_source_assertion_chain(
            manifest=source_assertion_manifest,
            ledger_by_atom=ledger_by_atom,
            obligation_rows=obligation_rows,
        )
        if semantic_projection is not None:
            semantic_non_executable_boundary_gap_ids_by_atom = (
                _validate_semantic_projection_graph(
                    projection=semantic_projection,
                    manifest=source_assertion_manifest,
                    ledger_by_atom=ledger_by_atom,
                    obligation_rows=obligation_rows,
                    coverage_gaps_path=gaps_path,
                )
            )
        accepted_testable_assertions = tuple(
            item
            for item in source_assertion_manifest.assertions
            if item.semantic_disposition == "testable"
        )
        accepted_testable_obligation_ids = {
            obligation_id
            for item in accepted_testable_assertions
            for obligation_id in item.obligation_ids
        }
        source_first_testable_completeness = {
            "contract": "accepted-testable-completeness-v1",
            "status": "pass",
            "coverage_ratio": 1.0,
            "accepted_testable_assertion_count": len(
                accepted_testable_assertions
            ),
            "accepted_testable_obligation_count": len(
                accepted_testable_obligation_ids
            ),
            "compiled_testable_obligation_count": len(
                source_assertion_by_obligation
            ),
            "manifest_digest": source_assertion_manifest.digest,
            "review_receipt_version": source_assertion_review.version,
            "basis": (
                "exact independently reviewed ASSERT->ATOM->covered OBL set; "
                "determinacy ratio is descriptive only"
            ),
        }
        dependency_blocked_assertions = tuple(
            item
            for item in source_assertion_manifest.assertions
            if item.semantic_disposition == "testable"
            and item.execution_readiness == "dependency-blocked"
        )
        execution_dependency_registry = tuple(
            {
                "assertion_id": item.assertion_id,
                "source_row_id": item.source_row_id,
                "atom_id": item.atom_id,
                "obligation_ids": list(item.obligation_ids),
                "gap_ids": list(item.execution_dependency_gap_ids),
                "risk": item.risk,
                "rationale": item.execution_readiness_rationale,
                "route": "excluded-from-ready-subset",
            }
            for item in dependency_blocked_assertions
        )
        dependency_blocked_obligation_ids = {
            obligation_id
            for item in dependency_blocked_assertions
            for obligation_id in item.obligation_ids
        }
        dependency_blocked_atom_ids = {
            item.atom_id for item in dependency_blocked_assertions
        }
        execution_dependency_gap_ids = {
            gap_id
            for item in dependency_blocked_assertions
            for gap_id in item.execution_dependency_gap_ids
        }
        if dependency_blocked_assertions and output_mode == RELEASE_OUTPUT_MODE:
            raise PreparedCompilerDiagnostic(
                "source-execution-dependency-blocked",
                "source semantics are testable, but execution dependencies remain "
                "unresolved: "
                + ", ".join(
                    item.assertion_id for item in dependency_blocked_assertions
                ),
                details=tuple(
                    {
                        "kind": "source-execution-dependency-blocked",
                        "assertion_id": item.assertion_id,
                        "source_row_id": item.source_row_id,
                        "atom_id": item.atom_id,
                        "obligation_ids": list(item.obligation_ids),
                        "gap_ids": list(item.execution_dependency_gap_ids),
                        "risk": item.risk,
                        "rationale": item.execution_readiness_rationale,
                    }
                    for item in dependency_blocked_assertions
                ),
            )
    plan_by_atom: dict[str, list[dict[str, str]]] = {}
    for row in plan:
        for atom in TOKEN.findall(row.get("linked_atoms", "")):
            if atom.startswith("ATOM-"):
                plan_by_atom.setdefault(atom, []).append(row)
    if source_assertion_manifest is not None:
        _validate_source_assertion_design_alignment(
            manifest=source_assertion_manifest,
            obligation_rows=obligation_rows,
            plan_by_atom=plan_by_atom,
            obligations_path=obligations_path,
            plan_path=plan_path,
            repo_root=repo_root,
        )
    _validate_execution_dependency_group_isolation(
        obligation_rows=obligation_rows,
        plan_rows=plan,
        blocked_obligation_ids=dependency_blocked_obligation_ids,
        blocked_atom_ids=dependency_blocked_atom_ids,
        obligations_path=obligations_path,
        plan_path=plan_path,
        repo_root=repo_root,
    )
    _validate_test_case_mapping_consistency(
        ledger_rows=ledger,
        obligation_rows=obligation_rows,
        plan_rows=plan,
        ledger_path=ledger_path,
        obligations_path=obligations_path,
        plan_path=plan_path,
        decision_rows=decision_rows,
        decision_path=decision_path,
        repo_root=repo_root,
    )
    _validate_planned_test_case_groups(
        obligation_rows=obligation_rows,
        plan_rows=plan,
        obligations_path=obligations_path,
        plan_path=plan_path,
        repo_root=repo_root,
    )
    known_gaps = _gap_sections(
        gaps_path,
        require_explicit_classification=source_first_contract,
    )
    resolved_clarification_gap_ids = (
        {
            item.gap_id
            for item in source_assertion_manifest.clarifications
        }
        if source_assertion_manifest is not None
        else set()
    )
    source_fidelity_bindings: tuple[dict[str, object], ...] = ()
    if source_fidelity_path is not None:
        source_fidelity_bindings = _validate_source_to_package_fidelity(
            path=source_fidelity_path,
            scope_slug=scope_slug,
            ledger_by_atom=ledger_by_atom,
            obligation_rows=tuple(
                row
                for row in obligation_rows
                if row["obligation_id"]
                not in dependency_blocked_obligation_ids
            ),
            plan_by_atom=plan_by_atom,
            known_gaps=known_gaps,
            repo_root=repo_root,
        )
    dictionary_rows: dict[str, dict[str, str]] = {}
    dictionary_active_values: dict[str, tuple[str, ...]] = {}
    if dictionary_path is not None:
        for row in _table_with(dictionary_path, {"dictionary_id", "active_values"}):
            if row["dictionary_id"] in dictionary_rows:
                raise StageRuntimeError(
                    f"semantic degradation: duplicate dictionary {row['dictionary_id']}"
                )
            dictionary_rows[row["dictionary_id"]] = row
            dictionary_active_values[row["dictionary_id"]] = (
                _parse_dictionary_active_values(
                    row["active_values"], dictionary_id=row["dictionary_id"]
                )
            )

    obligations: list[PreparedObligation] = []
    used_gaps: set[str] = set()
    used_dicts: set[str] = set()
    portable_dictionary_requirements: dict[
        str, PreparedDictionaryRequirement
    ] = {}
    used_atoms: set[str] = set()
    seen_obligation_ids: set[str] = set()
    emitted_atom_evidence: set[str] = set()
    emitted_plan_evidence: set[str] = set()
    evidence_rows: list[str] = ["# Compiled Prepared Evidence", ""]
    package_notes_path = ft_root / "AGENT-NOTES.md"
    if package_notes_path.is_file():
        package_notes = package_notes_path.read_text(encoding="utf-8").strip()
        evidence_rows.extend(
            [
                "## Mandatory package context",
                "",
                f"source_path: {package_notes_path.relative_to(repo_root).as_posix()}",
                "",
                package_notes,
                "",
            ]
        )
    if source_assertion_manifest is not None:
        assert source_assertion_review is not None
        evidence_rows.extend(
            render_embedded_source_assertion_contract(
                source_assertion_manifest,
                source_assertion_review,
            ).split("\n")
        )
    if fixture_contract_lines:
        evidence_rows.extend(
            [
                "## Portable fixture contracts",
                "",
                *dict.fromkeys(text for _, text in fixture_contract_lines),
                "",
            ]
        )
    if source_fidelity_bindings:
        evidence_rows.extend(
            [
                "## Source-to-package fidelity bindings",
                "",
                "```json",
                json.dumps(
                    source_fidelity_bindings,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "```",
                "",
            ]
        )
    if semantic_projection is not None:
        evidence_rows.extend(
            [
                "## Immutable semantic-design bridge projection",
                "",
                "```json",
                json.dumps(
                    semantic_projection,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "```",
                "",
            ]
        )
    source_first_evidence_prefix_length = len(evidence_rows)
    dedicated_exhaustive_dictionary_ids = _dedicated_exhaustive_dictionary_ids(
        obligation_rows
    )
    for obligation_row in obligation_rows:
        obligation_id = obligation_row["obligation_id"]
        if not re.fullmatch(r"OBL-[A-Za-z0-9_.-]+", obligation_id):
            raise PreparedCompilerDiagnostic(
                "invalid-obligation-id",
                f"semantic degradation: invalid coverage obligation id {obligation_id}",
                details=(
                    {
                        "kind": "invalid-obligation-id",
                        **_artifact_anchor(obligations_path, obligation_id, repo_root),
                    },
                ),
            )
        if obligation_id in seen_obligation_ids:
            raise PreparedCompilerDiagnostic(
                "duplicate-obligation-id",
                f"semantic degradation: duplicate coverage obligation {obligation_id}",
                details=(
                    {
                        "kind": "duplicate-obligation-id",
                        **_artifact_anchor(obligations_path, obligation_id, repo_root),
                    },
                ),
            )
        seen_obligation_ids.add(obligation_id)
        atom_tokens = [
            token
            for token in TOKEN.findall(obligation_row["linked_atom_id"])
            if token.startswith("ATOM-")
        ]
        if len(set(atom_tokens)) != 1:
            raise StageRuntimeError(
                f"semantic degradation: {obligation_id} must link exactly one ATOM id"
            )
        atom_id = atom_tokens[0]
        if atom_id not in ledger_by_atom:
            raise PreparedCompilerDiagnostic(
                "obligation-references-unknown-atom",
                f"semantic degradation: {obligation_id} references unknown atom {atom_id}",
                details=(
                    {
                        "kind": "obligation-references-unknown-atom",
                        "obligation_id": obligation_id,
                        **_artifact_anchor(obligations_path, atom_id, repo_root),
                    },
                ),
            )
        used_atoms.add(atom_id)
        if obligation_id in dependency_blocked_obligation_ids:
            if atom_id not in dependency_blocked_atom_ids:
                raise StageRuntimeError(
                    "execution dependency registry obligation/ATOM mismatch: "
                    f"{obligation_id} -> {atom_id}"
                )
            continue
        row = ledger_by_atom[atom_id]
        source_assertion = source_assertion_by_obligation.get(obligation_id)
        status_raw = row["coverage_status"].lower()
        obligation_status = obligation_row["status"].lower()
        linked = plan_by_atom.get(atom_id, [])
        constraint_gap_tokens = list(
            dict.fromkeys(TOKEN.findall(row.get("constraint_gap_ids", "")))
        )
        prepared_constraint_gap_tokens = list(constraint_gap_tokens)
        if any(not item.startswith("GAP-") for item in constraint_gap_tokens):
            raise StageRuntimeError(
                f"semantic degradation: {atom_id} constraint_gap_ids must contain only GAP ids"
            )
        atom_gap_tokens = list(
            dict.fromkeys(
                item
                for item in TOKEN.findall(" ".join(row.values()))
                if item.startswith("GAP-") and item not in constraint_gap_tokens
            )
        )
        obligation_gap_tokens = list(
            dict.fromkeys(
                item
                for item in TOKEN.findall(" ".join(obligation_row.values()))
                if item.startswith("GAP-")
            )
        )
        dict_tokens = list(
            dict.fromkeys(
                item
                for item in TOKEN.findall(" ".join(row.values()) + " " + " ".join(obligation_row.values()))
                if item.startswith("DICT-")
            )
        )
        source_tokens = [
            item
            for item in TOKEN.findall(" ".join(row.values()) + " " + " ".join(obligation_row.values()))
            if item.startswith(("SRC-", "GSR ", "BSR ", "DIT "))
        ]
        mapped_viable: list[dict[str, str]] = []
        if status_raw in {"covered", "testable"} or status_raw.startswith("covered_with_"):
            atom_coverage_status = "testable"
            if status_raw.startswith("covered_with_"):
                qualifier = status_raw.removeprefix("covered_with_").replace("_", "-")
                routed_unsupported_dimensions.add(f"evidence-qualified-{qualifier}")
        elif status_raw in {"unclear", "gap", "not-applicable"}:
            atom_coverage_status = status_raw
        else:
            raise StageRuntimeError(
                f"semantic degradation: {atom_id} has unsupported coverage_status {status_raw}"
            )
        non_executable_boundary_gap_tokens = (
            semantic_non_executable_boundary_gap_ids_by_atom.get(atom_id, ())
        )
        if non_executable_boundary_gap_tokens:
            source_disposition = (
                next(
                    (
                        assertion.semantic_disposition
                        for assertion in source_assertion_manifest.assertions
                        if assertion.atom_id == atom_id
                    ),
                    None,
                )
                if source_assertion_manifest is not None
                else None
            )
            allowed_non_executable_statuses = (
                {"gap", "unclear"}
                if source_disposition == "ambiguous"
                else {"not-applicable"}
            )
            if atom_coverage_status not in allowed_non_executable_statuses:
                raise StageRuntimeError(
                    "semantic degradation: non-executable boundary gap evidence "
                    f"does not match {source_disposition or 'unknown'} ATOM status: "
                    f"{atom_id}={atom_coverage_status}"
                )
            for boundary_gap_id in non_executable_boundary_gap_tokens:
                if boundary_gap_id not in known_gaps:
                    raise StageRuntimeError(
                        "semantic degradation: non-executable boundary gap is missing "
                        f"from coverage-gaps.md: {boundary_gap_id}"
                    )
                if known_gaps[boundary_gap_id].blocking:
                    raise PreparedCompilerDiagnostic(
                        "blocking-constraint-gap",
                        "non-executable source evidence gaps must be explicitly "
                        f"non-blocking: {boundary_gap_id}",
                        details=(
                            {
                                "kind": "blocking-constraint-gap",
                                "atom_id": atom_id,
                                "obligation_id": obligation_id,
                                "gap_id": boundary_gap_id,
                                **(
                                    _artifact_anchor(
                                        gaps_path,
                                        boundary_gap_id,
                                        repo_root,
                                    )
                                    if gaps_path is not None
                                    else {}
                                ),
                            },
                        ),
                    )
                if source_disposition != "ambiguous":
                    prepared_constraint_gap_tokens.append(boundary_gap_id)
                used_gaps.add(boundary_gap_id)
        if obligation_status == "covered":
            if atom_coverage_status in {"gap", "unclear", "not-applicable"}:
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} cannot cover {atom_coverage_status} {atom_id}"
                )
            coverage_status = "testable"
            planned_tc_id = _canonical_planned_test_case_id(obligation_row)
            if not planned_tc_id:
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} covered row must link a TC id "
                    "or a bound UI-calibration candidate"
                )
            viable = [
                item
                for item in linked
                if item.get("status", "covered").lower()
                in {"covered", "testable", "planned"}
                or item.get("status", "").lower().startswith("covered_with_")
            ]
            if not viable:
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no testable design-plan row")
            raw_planned_target = obligation_row["planned_tc_or_gap"].strip()
            mapped_viable = [
                item
                for item in viable
                if planned_tc_id in TC_TOKEN.findall(item.get("planned_tc_or_gap", ""))
                or item.get("planned_tc_or_gap", "").strip() == raw_planned_target
            ]
            if not mapped_viable:
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} TC link is absent from the design plan"
                )
            generic_fixture_rows = [
                (item, _plan_generic_fixture_values(item))
                for item in mapped_viable
                if _plan_generic_fixture_values(item)
            ]
            if generic_fixture_rows:
                raise PreparedCompilerDiagnostic(
                    "generic-execution-fixture",
                    "semantic degradation: generic fixture text is not a reproducible "
                    f"execution contract: {atom_id}",
                    details=tuple(
                        {
                            "kind": "generic-execution-fixture",
                            "atom_id": atom_id,
                            "values": list(values),
                            **_artifact_anchor(
                                plan_path,
                                item.get("design_item_id") or atom_id,
                                repo_root,
                            ),
                        }
                        for item, values in generic_fixture_rows
                    ),
                )
            undefined_action_rows = [
                item
                for item in mapped_viable
                if UNDEFINED_EXECUTION_ACTION.search(item.get("planned_check", ""))
            ]
            if undefined_action_rows:
                raise PreparedCompilerDiagnostic(
                    "undefined-execution-action",
                    "semantic degradation: design-plan action names a scenario placeholder "
                    f"instead of an executable action: {atom_id}",
                    details=tuple(
                        {
                            "kind": "undefined-execution-action",
                            "atom_id": atom_id,
                            **_artifact_anchor(
                                plan_path,
                                item.get("design_item_id") or atom_id,
                                repo_root,
                            ),
                        }
                        for item in undefined_action_rows
                    ),
                )
            missing_dictionary_group_locators: list[tuple[dict[str, str], str]] = []
            for item in mapped_viable:
                planned_check = item.get("planned_check", "")
                executable_locator_context = " ".join(
                    (
                        planned_check,
                        *(
                            source_assertion.condition_clauses
                            if source_assertion is not None
                            else ()
                        ),
                        *(
                            source_assertion.action_clauses
                            if source_assertion is not None
                            else ()
                        ),
                    )
                )
                for dictionary_id in dict.fromkeys(
                    token
                    for token in TOKEN.findall(item.get("test_data", ""))
                    if token.startswith("DICT-") and token in dictionary_rows
                ):
                    dictionary_name = dictionary_rows[dictionary_id].get(
                        "dictionary_name", ""
                    ).strip()
                    if dictionary_id in executable_locator_context or (
                        dictionary_name
                        and dictionary_name.casefold()
                        in executable_locator_context.casefold()
                    ):
                        continue
                    missing_dictionary_group_locators.append((item, dictionary_id))
            if missing_dictionary_group_locators:
                raise PreparedCompilerDiagnostic(
                    "dictionary-group-locator-not-preserved",
                    "semantic degradation: design-plan test_data names a dictionary group "
                    f"that is absent from the executable action: {atom_id}",
                    details=tuple(
                        {
                            "kind": "dictionary-group-locator-not-preserved",
                            "atom_id": atom_id,
                            "dictionary_id": dictionary_id,
                            **_artifact_anchor(
                                plan_path,
                                item.get("design_item_id") or atom_id,
                                repo_root,
                            ),
                        }
                        for item, dictionary_id in missing_dictionary_group_locators
                    ),
                )
            fixtureless = [
                item
                for item in mapped_viable
                if _plan_requires_concrete_fixture(item)
                and not _plan_has_concrete_fixture(item)
            ]
            if fixtureless:
                raise PreparedCompilerDiagnostic(
                    "input-fixture-required",
                    "semantic degradation: input-based design-plan rows require a concrete "
                    f"fixture before live execution: {atom_id}",
                    details=tuple(
                        {
                            "kind": "input-fixture-required",
                            "atom_id": atom_id,
                            **_artifact_anchor(
                                plan_path,
                                item.get("design_item_id") or atom_id,
                                repo_root,
                            ),
                        }
                        for item in fixtureless
                    ),
                )
            oracle = obligation_row["required_behavior"]
            state_change = _compile_state_change(
                obligation_row=obligation_row,
                plan_rows=mapped_viable,
                plan_path=plan_path,
                repo_root=repo_root,
            )
            if source_first_contract:
                if source_assertion is None:
                    raise StageRuntimeError(
                        f"source-first compiler contract has no assertion for {obligation_id}"
                    )
                state_change = _resolve_source_first_state_change(
                    state_change=state_change,
                    source_assertion=source_assertion,
                    obligation_id=obligation_id,
                    atom_id=atom_id,
                    plan_path=plan_path,
                    plan_rows=mapped_viable,
                    repo_root=repo_root,
                )
            intent_parts = [item["planned_check"] for item in mapped_viable]
            if state_change is not None:
                intent_parts = [
                    state_change.initial_state_capture,
                    state_change.changed_state_setup,
                    "Before the target action verify: "
                    + state_change.pre_action_state_oracle,
                    *intent_parts,
                ]
            intent_parts.extend(
                context
                for item in mapped_viable
                for context in _mapped_plan_intent_context(item, fixture_contracts)
            )
            intent = "; ".join(dict.fromkeys(intent_parts))
            if not oracle or "none_required" in oracle.lower():
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no observable plan oracle")
            if (
                obligation_row.get("property_type", "").strip().lower()
                in {"requiredness", "dependency"}
                and UNKNOWN_REQUIREDNESS_ORACLE.search(oracle)
                and not EVIDENCE_CAPTURE.search(oracle)
            ):
                raise PreparedCompilerDiagnostic(
                    "non-observable-execution-oracle",
                    "semantic degradation: calibration-required obligation must define "
                    f"an observable evidence-capture oracle: {obligation_id}",
                    details=(
                        {
                            "kind": "non-observable-execution-oracle",
                            "atom_id": atom_id,
                            "obligation_id": obligation_id,
                            **_artifact_anchor(
                                obligations_path,
                                obligation_id,
                                repo_root,
                            ),
                        },
                    ),
                )
            for constraint_gap_id in constraint_gap_tokens:
                if constraint_gap_id not in known_gaps:
                    raise StageRuntimeError(
                        "semantic degradation: constraint gap is missing from coverage-gaps.md: "
                        f"{constraint_gap_id}"
                    )
                if source_first_contract and known_gaps[constraint_gap_id].blocking:
                    raise PreparedCompilerDiagnostic(
                        "blocking-constraint-gap",
                        "source-first constraint gaps must be explicitly non-blocking: "
                        f"{constraint_gap_id}",
                        details=(
                            {
                                "kind": "blocking-constraint-gap",
                                "atom_id": atom_id,
                                "obligation_id": obligation_id,
                                "gap_id": constraint_gap_id,
                                **(
                                    _artifact_anchor(
                                        gaps_path,
                                        constraint_gap_id,
                                        repo_root,
                                    )
                                    if gaps_path is not None
                                    else {}
                                ),
                            },
                        ),
                    )
                used_gaps.add(constraint_gap_id)
            gap_id = ""
        elif obligation_status in {"gap", "unclear", "blocked"}:
            state_change = None
            coverage_status = "gap" if obligation_status == "gap" else "unclear"
            if atom_coverage_status == "not-applicable":
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} cannot attach a gap to not-applicable {atom_id}"
                )
            if len(set(obligation_gap_tokens)) != 1:
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} must link exactly one GAP id"
                )
            if atom_coverage_status in {"gap", "unclear"} and (
                len(set(atom_gap_tokens)) != 1
                or atom_gap_tokens[0] != obligation_gap_tokens[0]
            ):
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} and {atom_id} link different GAP ids"
                )
            gap_id = obligation_gap_tokens[0]
            if atom_coverage_status == "testable" and gap_id not in atom_gap_tokens:
                raise StageRuntimeError(
                    f"semantic degradation: partial {obligation_id} gap is absent from {atom_id}"
                )
            used_gaps.add(gap_id)
            if gap_id in known_gaps and known_gaps[gap_id].source_refs == (gap_id,):
                raise StageRuntimeError(
                    f"semantic degradation: {gap_id} has no exact source reference"
                )
            oracle = ""
            intent = obligation_row["required_behavior"]
        else:
            state_change = None
            if obligation_status not in {"not-applicable", "n/a"}:
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} has unsupported status {obligation_status}"
                )
            if atom_coverage_status != "not-applicable":
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} cannot skip applicable {atom_id}"
                )
            coverage_status = "not-applicable"
            gap_id = ""
            oracle = ""
            intent = obligation_row["required_behavior"]
        for dictionary_id in dict_tokens:
            if dictionary_id not in dictionary_rows:
                raise StageRuntimeError(f"semantic degradation: {atom_id} references missing {dictionary_id}")
            used_dicts.add(dictionary_id)
        reference_fixture_text = " ".join(
            (
                intent,
                *(item.get("test_data", "") for item in mapped_viable),
                *(item.get("input_class", "") for item in mapped_viable),
            )
        )
        dictionary_requirements = tuple(
            _compile_dictionary_requirement(
                dictionary_id=dictionary_id,
                coverage_mode=_effective_dictionary_coverage_mode(
                    obligation_row,
                    dictionary_id=dictionary_id,
                    dedicated_exhaustive_dictionary_ids=(
                        dedicated_exhaustive_dictionary_ids
                    ),
                ),
                dictionary_rows=dictionary_rows,
                dictionary_active_values=dictionary_active_values,
                reference_fixture_text=reference_fixture_text,
            )
            for dictionary_id in dict_tokens
        )
        external_dynamic_dependency_refs = (
            external_dynamic_dependencies_by_obligation.get(obligation_id, ())
        )
        if external_dynamic_dependency_refs and not dictionary_requirements:
            dictionary_requirements = _compile_portable_fixture_requirements(
                mapped_viable,
                fixture_contracts,
            )
            dict_tokens.extend(
                requirement.dictionary_id
                for requirement in dictionary_requirements
                if requirement.dictionary_id not in dict_tokens
            )
        for requirement in dictionary_requirements:
            if requirement.dictionary_id in dictionary_rows:
                continue
            existing = portable_dictionary_requirements.get(
                requirement.dictionary_id
            )
            if existing is not None and existing != requirement:
                raise StageRuntimeError(
                    "portable fixture dictionary has conflicting projections: "
                    + requirement.dictionary_id
                )
            portable_dictionary_requirements[
                requirement.dictionary_id
            ] = requirement
        conflicting_action_literals = (
            _unbound_reference_fixture_action_literals(
                source_assertion,
                dictionary_requirements,
            )
            if source_first_contract and source_assertion is not None
            else ()
        )
        if conflicting_action_literals:
            assert source_assertions_path is not None
            raise PreparedCompilerDiagnostic(
                "source-action-reference-fixture-conflict",
                "source assertion action contains an unbound synthetic literal that "
                "conflicts with the curated reference-only fixture",
                details=(
                    {
                        "kind": "source-action-reference-fixture-conflict",
                        "assertion_id": source_assertion.assertion_id,
                        "obligation_id": obligation_id,
                        "dictionary_ids": [
                            item.dictionary_id for item in dictionary_requirements
                        ],
                        "conflicting_literals": list(conflicting_action_literals),
                        **_artifact_anchor(
                            source_assertions_path,
                            source_assertion.assertion_id,
                            repo_root,
                        ),
                    },
                ),
            )
        source_refs = tuple(dict.fromkeys(source_tokens + dict_tokens))
        if not source_refs:
            source_ref = obligation_row.get("source_ref") or row.get("source_ref") or row.get("source_property_id")
            if not source_ref:
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no source reference")
            source_refs = (source_ref,)
        if source_first_contract and coverage_status == "testable":
            if source_assertion is None:
                raise StageRuntimeError(
                    f"source-first compiler contract has no assertion for {obligation_id}"
                )
            condition_contract = "; ".join(source_assertion.condition_clauses)
            action_contract = "; ".join(source_assertion.action_clauses)
            source_intent = "; ".join(
                part
                for part in (
                    (
                        f"Field/block: {row['field_or_block']}"
                        if row.get("field_or_block")
                        else ""
                    ),
                    f"Condition contract: {condition_contract}"
                    if condition_contract
                    else "",
                    f"Action contract: {action_contract}",
                    f"Design fixture: {intent}" if intent else "",
                )
                if part
            )
            intent = source_intent
            oracle = "; ".join(source_assertion.oracle_clauses)
            source_refs = tuple(
                dict.fromkeys(
                    (
                        source_assertion.source_row_id,
                        *source_assertion.requirement_codes,
                        *(
                            binding.clarification_id
                            for binding in source_assertion.clarification_clause_bindings
                        ),
                        *dict_tokens,
                    )
                )
            )
        if external_dynamic_dependency_refs:
            if not dictionary_requirements:
                raise PreparedCompilerDiagnostic(
                    "external-dynamic-fixture-binding-missing",
                    "external-dynamic dictionary obligations require a curated "
                    f"reference-only fixture before writer: {obligation_id}",
                    details=(
                        {
                            "kind": "external-dynamic-fixture-binding-missing",
                            "obligation_id": obligation_id,
                            "dependency_ids": list(external_dynamic_dependency_refs),
                            **_artifact_anchor(
                                obligations_path,
                                obligation_id,
                                repo_root,
                            ),
                        },
                    ),
                )
            has_external_fixture_projection = any(
                requirement.coverage_mode == "reference-only"
                and requirement.fixture_values
                for requirement in dictionary_requirements
            )
            if not has_external_fixture_projection:
                raise PreparedCompilerDiagnostic(
                    "external-dynamic-fixture-values-missing",
                    "external-dynamic dictionaries require exact reference-only "
                    f"fixture values before writer: {obligation_id}",
                    details=(
                        {
                            "kind": "external-dynamic-fixture-values-missing",
                            "obligation_id": obligation_id,
                            "dictionary_ids": [
                                requirement.dictionary_id
                                for requirement in dictionary_requirements
                            ],
                            "dependency_ids": list(external_dynamic_dependency_refs),
                            **_artifact_anchor(
                                obligations_path,
                                obligation_id,
                                repo_root,
                            ),
                        },
                    ),
                )
        source_refs = tuple(
            dict.fromkeys((*source_refs, *external_dynamic_dependency_refs))
        )
        calibration_raw = obligation_row.get("calibration_status", "").strip()
        if calibration_raw not in {"", "none", "ui-calibration-required"}:
            raise StageRuntimeError(
                f"semantic degradation: unsupported calibration_status for {obligation_id}: "
                f"{calibration_raw}"
            )
        obligations.append(
            PreparedObligation(
                obligation_id=obligation_id,
                atom_id=atom_id,
                source_refs=source_refs,
                atomic_statement=row["atomic_statement"],
                observable_oracle=oracle,
                test_intent=intent,
                coverage_status=coverage_status,
                gap_id=gap_id,
                dictionary_refs=tuple(dict_tokens),
                notes=(
                    "Compiled from workflow-state canonical design artifacts."
                    + (
                        " Source assertion: "
                        + source_assertion.assertion_id
                        + "."
                        if source_assertion is not None
                        else ""
                    )
                    + (
                        " Non-blocking constraints: "
                        + ", ".join(prepared_constraint_gap_tokens)
                        + "."
                        if prepared_constraint_gap_tokens
                        else ""
                    )
                    + (
                        " External-dynamic dictionary dependency: "
                        + ", ".join(external_dynamic_dependency_refs)
                        + "."
                        if external_dynamic_dependency_refs
                        else ""
                    )
                ),
                constraint_gap_ids=tuple(prepared_constraint_gap_tokens),
                planned_test_case_id=(
                    planned_tc_id
                    if coverage_status == "testable"
                    else ""
                ),
                execution_semantics=(
                    RESET_EXECUTION_SEMANTICS
                    if state_change is not None
                    else "direct"
                ),
                state_change=state_change,
                dictionary_requirements=dictionary_requirements,
                calibration_status=(
                    "ui-calibration-required"
                    if calibration_raw == "ui-calibration-required"
                    or (
                        not calibration_raw
                        and status_raw == "covered_with_ui_calibration"
                    )
                    else "none"
                ),
            )
        )
        evidence_rows.extend(
            [
                f"- {obligation_id}: "
                + " | ".join(
                    (
                        f"property={obligation_row['source_property_id']}",
                        f"source={obligation_row['source_ref']}",
                        "required="
                        + (
                            "same-as-atom"
                            if obligation_row["required_behavior"] == row["atomic_statement"]
                            else obligation_row["required_behavior"]
                        ),
                        f"planned={obligation_row['planned_tc_or_gap']}",
                        f"status={obligation_row['status']}",
                    )
                ),
            ]
        )
        if atom_id not in emitted_atom_evidence:
            emitted_atom_evidence.add(atom_id)
            atom_source = "; ".join(
                dict.fromkeys(
                    value
                    for key in (
                        "source_refs",
                        "source_property_id",
                        "req_id",
                        "source_row_id",
                    )
                    if (value := row.get(key, ""))
                )
            )
            evidence_rows.extend(
                [
                    "- atom: "
                    + " | ".join(
                        (
                            atom_id,
                            f"source={atom_source}",
                            f"statement={row['atomic_statement']}",
                            f"coverage={row['coverage_status']}",
                        )
                    ),
                    "",
                ]
            )
            for item in linked:
                plan_id = item.get("design_item_id") or "|".join(
                    (
                        item.get("linked_atoms", ""),
                        item.get("planned_tc_or_gap", ""),
                        item.get("planned_check", ""),
                    )
                )
                if plan_id in emitted_plan_evidence:
                    continue
                emitted_plan_evidence.add(plan_id)
                evidence_rows.extend(
                    [
                        "- plan: "
                        + " | ".join(
                            (
                                item.get("design_item_id", "design-item"),
                                f"atoms={item.get('linked_atoms', atom_id)}",
                                f"check={item['planned_check']}",
                                "expected="
                                + (
                                    "same-as-check"
                                    if item["single_expected_behavior"] == item["planned_check"]
                                    else item["single_expected_behavior"]
                                ),
                                f"planned={item.get('planned_tc_or_gap', '')}",
                                f"status={item.get('status', '')}",
                                *(
                                    (
                                        "state_relation=" + item["state_relation"],
                                        "initial_capture=" + item["initial_state_capture"],
                                        "changed_setup=" + item["changed_state_setup"],
                                        "pre_action_oracle=" + item["pre_action_state_oracle"],
                                    )
                                    if item.get("state_relation")
                                    else ()
                                ),
                            )
                        ),
                        "",
                    ]
                )
    if source_first_contract:
        if (
            output_mode == DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE
            and not any(item.coverage_status == "testable" for item in obligations)
        ):
            raise PreparedCompilerDiagnostic(
                "draft-no-ready-execution-assertions",
                "draft-with-blocking-gaps has no ready testable assertions to run",
                details=(
                    {
                        "kind": "draft-no-ready-execution-assertions",
                        "excluded_assertion_ids": [
                            item["assertion_id"]
                            for item in execution_dependency_registry
                        ],
                        "excluded_obligation_ids": sorted(
                            dependency_blocked_obligation_ids
                        ),
                    },
                ),
            )
        dimension_bindings = _source_first_dimension_bindings(
            applicability_rows=_table_with(
                applicability_path, {"dimension", "applicable"}
            ),
            obligation_rows=tuple(
                row
                for row in obligation_rows
                if row["obligation_id"]
                not in dependency_blocked_obligation_ids
            ),
            obligations=obligations,
            ledger_by_atom=ledger_by_atom,
            routed_dimensions=tuple(sorted(routed_unsupported_dimensions)),
        )
        evidence_rows = evidence_rows[:source_first_evidence_prefix_length]
        evidence_rows.extend(
            [
                "## Compiled obligation routing index",
                "",
                "```json",
                json.dumps(
                    [
                        {
                            "obligation_id": item.obligation_id,
                            "atom_id": item.traceability_atom_id,
                            "source_refs": list(item.source_refs),
                            "coverage_status": item.coverage_status,
                            "planned_test_case_id": item.planned_test_case_id,
                            "gap_id": item.gap_id,
                            "constraint_gap_ids": list(item.constraint_gap_ids),
                            "dictionary_refs": list(item.dictionary_refs),
                        }
                        for item in obligations
                    ],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "```",
                "",
                "## Reviewer dimension source bindings",
                "",
                render_reviewer_dimension_source_bindings(
                    dimension_bindings
                ),
                "",
            ]
        )
    missing_obligation_atoms = sorted(set(ledger_by_atom) - used_atoms)
    if missing_obligation_atoms:
        raise PreparedCompilerDiagnostic(
            "atom-without-obligation",
            "semantic degradation: atomic ledger rows have no coverage obligation: "
            + ", ".join(missing_obligation_atoms),
            details=tuple(
                {
                    "kind": "atom-without-obligation",
                    **_artifact_anchor(ledger_path, atom_id, repo_root),
                }
                for atom_id in missing_obligation_atoms
            ),
        )
    coverage_accounting = None
    draft_guard_accounting = None
    blocking_gap_ids: tuple[str, ...] = ()
    release_blocking_finding_codes: tuple[str, ...] = (
        ()
        if source_assertion_manifest is not None
        else ("legacy-source-contract",)
    )
    release_eligible = (
        source_assertion_manifest is not None
        and output_mode == RELEASE_OUTPUT_MODE
    )
    if source_assertion_manifest is not None:
        linked_gap_ids = {
            gap_id
            for obligation in obligations
            for gap_id in (
                *((obligation.gap_id,) if obligation.gap_id else ()),
                *obligation.constraint_gap_ids,
            )
        }
        linked_gap_ids.update(execution_dependency_gap_ids)
        missing_linked_gap_ids = tuple(sorted(linked_gap_ids - set(known_gaps)))
        if missing_linked_gap_ids:
            raise PreparedCompilerDiagnostic(
                "linked-gap-missing",
                "source-first ATOM/OBL chains reference gaps absent from "
                "coverage-gaps.md: " + ", ".join(missing_linked_gap_ids),
                details=tuple(
                    {
                        "kind": "linked-gap-missing",
                        "gap_id": gap_id,
                    }
                    for gap_id in missing_linked_gap_ids
                ),
            )
        blocking_gap_ids = tuple(
            sorted(
                execution_dependency_gap_ids
                | {
                    obligation.gap_id
                    for obligation in obligations
                    if obligation.gap_id
                    and known_gaps[obligation.gap_id].blocking
                }
            )
        )
        if (
            output_mode == DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE
            and not blocking_gap_ids
        ):
            raise PreparedCompilerDiagnostic(
                "draft-without-blockers",
                "draft-with-blocking-gaps requires at least one hash-bound blocking gap",
                details=(
                    {
                        "kind": "draft-without-blockers",
                        "output_mode": output_mode,
                    },
                ),
            )
        if blocking_gap_ids and output_mode == RELEASE_OUTPUT_MODE:
            raise PreparedCompilerDiagnostic(
                "blocking-source-first-gap",
                "source-first compilation cannot proceed with blocking coverage gaps: "
                + ", ".join(blocking_gap_ids),
                details=tuple(
                    {
                        "kind": "blocking-source-first-gap",
                        "gap_id": gap_id,
                        **(
                            _artifact_anchor(gaps_path, gap_id, repo_root)
                            if gaps_path is not None
                            else {}
                        ),
                    }
                    for gap_id in blocking_gap_ids
                ),
            )
        compiled_by_atom: dict[str, list[PreparedObligation]] = {}
        for obligation in obligations:
            compiled_by_atom.setdefault(
                obligation.traceability_atom_id, []
            ).append(obligation)
        coverage_metadata: dict[str, CoverageObligationMetadata] = {}
        assertion_coverage: dict[str, str] = {}
        for assertion in source_assertion_manifest.assertions:
            if assertion.atom_id in dependency_blocked_atom_ids:
                continue
            compiled = compiled_by_atom.get(assertion.atom_id, [])
            statuses = {item.coverage_status for item in compiled}
            if assertion.semantic_disposition == "testable":
                expected_statuses = {"testable"}
            elif assertion.semantic_disposition == "ambiguous":
                expected_statuses = {"gap", "unclear"}
            else:
                expected_statuses = {"not-applicable"}
            if not compiled or not statuses <= expected_statuses:
                raise StageRuntimeError(
                    "source assertion semantic disposition mismatch: "
                    f"{assertion.assertion_id} declares "
                    f"{assertion.semantic_disposition}, compiled={sorted(statuses)}"
                )
            if assertion.semantic_disposition == "testable":
                assertion_coverage[assertion.assertion_id] = "testable"
            elif assertion.semantic_disposition == "ambiguous":
                assertion_coverage[assertion.assertion_id] = (
                    "unclear" if "unclear" in statuses else "gap"
                )
            else:
                assertion_coverage[assertion.assertion_id] = "not-applicable"
            for obligation in compiled:
                linked_gap = known_gaps.get(obligation.gap_id)
                coverage_metadata[obligation.obligation_id] = (
                    CoverageObligationMetadata(
                        critical=assertion.risk == "critical",
                        risk=assertion.risk,
                        gap_blocking=(
                            linked_gap.blocking if linked_gap is not None else None
                        ),
                        assertion_count=1,
                    )
                )
        coverage_accounting = evaluate_coverage_accounting(
            obligations,
            metadata=coverage_metadata,
            assertion_coverage=assertion_coverage,
            constraint_gap_blocking={
                gap_id: known_gaps[gap_id].blocking
                for obligation in obligations
                for gap_id in obligation.constraint_gap_ids
            },
        )
        release_blocking_finding_codes = tuple(
            dict.fromkeys(
                (
                    *(("blocking-source-first-gap",) if blocking_gap_ids else ()),
                    *(
                        ("source-execution-dependency-blocked",)
                        if execution_dependency_registry
                        else ()
                    ),
                    *coverage_accounting.blocking_finding_codes,
                )
            )
        )
        if (
            output_mode == RELEASE_OUTPUT_MODE
            and not coverage_accounting.passed
        ):
            raise PreparedCompilerDiagnostic(
                "coverage-accounting-failed",
                "source-first coverage accounting blocks compilation: "
                + ", ".join(coverage_accounting.blocking_finding_codes),
                details=tuple(coverage_accounting.to_dict()["findings"]),
            )
        if output_mode == DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE:
            non_floor_findings = tuple(
                item
                for item in coverage_accounting.findings
                if item.blocking
                and item.code not in _DRAFT_PERMITTED_RELEASE_ONLY_FINDINGS
            )
            if non_floor_findings:
                raise PreparedCompilerDiagnostic(
                    "coverage-accounting-failed",
                    "draft coverage guardrails block compilation: "
                    + ", ".join(dict.fromkeys(item.code for item in non_floor_findings)),
                    details=tuple(item.to_dict() for item in non_floor_findings),
                )

            blocking_obligation_ids = {
                item.obligation_id
                for item in obligations
                if item.gap_id in blocking_gap_ids
            }
            blocking_atom_ids = {
                item.traceability_atom_id
                for item in obligations
                if item.obligation_id in blocking_obligation_ids
            }
            assertion_atom_by_id = {
                item.assertion_id: item.atom_id
                for item in source_assertion_manifest.assertions
            }
            residual_obligations = tuple(
                item
                for item in obligations
                if item.obligation_id not in blocking_obligation_ids
            )
            residual_assertion_coverage = {
                assertion_id: status
                for assertion_id, status in assertion_coverage.items()
                if assertion_atom_by_id[assertion_id] not in blocking_atom_ids
            }
            draft_guard_accounting = evaluate_coverage_accounting(
                residual_obligations,
                metadata={
                    obligation_id: metadata
                    for obligation_id, metadata in coverage_metadata.items()
                    if obligation_id not in blocking_obligation_ids
                },
                assertion_coverage=residual_assertion_coverage,
                constraint_gap_blocking={
                    gap_id: known_gaps[gap_id].blocking
                    for obligation in residual_obligations
                    for gap_id in obligation.constraint_gap_ids
                },
            )
            if not draft_guard_accounting.passed:
                raise PreparedCompilerDiagnostic(
                    "coverage-accounting-failed",
                    "non-blocking draft coverage guardrails block compilation: "
                    + ", ".join(draft_guard_accounting.blocking_finding_codes),
                    details=tuple(draft_guard_accounting.to_dict()["findings"]),
                )
            release_eligible = False

    structured_execution_dependencies = tuple(
        PreparedExecutionDependency(
            assertion_id=str(item["assertion_id"]),
            source_row_id=str(item["source_row_id"]),
            atom_id=str(item["atom_id"]),
            obligation_ids=tuple(str(value) for value in item["obligation_ids"]),
            gap_ids=tuple(str(value) for value in item["gap_ids"]),
            risk=str(item["risk"]),
            rationale=str(item["rationale"]),
            route=str(item["route"]),
        )
        for item in execution_dependency_registry
    )
    unsigned_status = (
        "blocked-execution-dependencies"
        if structured_execution_dependencies
        else (
            "blocked-source-gaps"
            if output_mode == DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE
            else (
                "blocked-source-contract"
                if source_assertion_manifest is None
                else "none"
            )
        )
    )
    package_release_status = PreparedReleaseStatus(
        contract="prepared-package-release-status-v1",
        output_mode=output_mode,
        release_eligible=release_eligible,
        blocking_gap_ids=blocking_gap_ids,
        execution_dependency_registry=structured_execution_dependencies,
        excluded_execution_obligation_ids=tuple(
            sorted(dependency_blocked_obligation_ids)
        ),
        unsigned_status=unsigned_status,
        release_blocking_finding_codes=release_blocking_finding_codes,
    )
    package_release_status.validate()
    diagnostic_release_status = {
        **package_release_status.to_dict(),
        "derived_from": "stage-package.json#/release_status",
        "coverage_accounting": (
            coverage_accounting.to_dict()
            if coverage_accounting is not None
            else None
        ),
        "draft_guard_accounting": (
            draft_guard_accounting.to_dict()
            if draft_guard_accounting is not None
            else None
        ),
        "source_first_testable_completeness": source_first_testable_completeness,
    }
    evidence_rows.extend(
        [
            "## Compiler release status",
            "",
            "```json",
            json.dumps(
                diagnostic_release_status,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "```",
            "",
        ]
    )
    unsupported_dimensions = tuple(sorted(routed_unsupported_dimensions))
    execution_profile = STANDARD_PROFILE if unsupported_dimensions else FAST_PROFILE
    gaps: list[PreparedGap] = []
    orphan_gaps = sorted(
        (set(known_gaps) | _resolved_gap_ids(gaps_path))
        - used_gaps
        - execution_dependency_gap_ids
        - resolved_clarification_gap_ids
    )
    if orphan_gaps:
        raise PreparedCompilerDiagnostic(
            "gap-without-obligation",
            "semantic degradation: coverage gaps are not linked from the atomic ledger: "
            + ", ".join(orphan_gaps),
            details=tuple(
                {
                    "kind": "gap-without-obligation",
                    **_artifact_anchor(gaps_path, gap_id, repo_root),
                }
                for gap_id in orphan_gaps
            )
            if gaps_path is not None
            else (),
        )
    for gap_id in sorted(used_gaps):
        if gap_id not in known_gaps:
            raise StageRuntimeError(f"semantic degradation: linked gap is missing from coverage-gaps.md: {gap_id}")
        gaps.append(known_gaps[gap_id])
        evidence_rows.extend(
            [
                f"## {gap_id}",
                "",
                "source_refs: " + "; ".join(known_gaps[gap_id].source_refs),
                known_gaps[gap_id].problem,
                known_gaps[gap_id].handling,
                "",
            ]
        )
    pending_dictionary_ids = list(used_dicts)
    while pending_dictionary_ids:
        parent_id = pending_dictionary_ids.pop()
        for child_id in (
            token
            for token in TOKEN.findall(dictionary_rows[parent_id]["active_values"])
            if token.startswith("DICT-")
        ):
            if child_id not in dictionary_rows:
                raise StageRuntimeError(
                    f"semantic degradation: {parent_id} references missing child {child_id}"
                )
            if child_id not in used_dicts:
                used_dicts.add(child_id)
                pending_dictionary_ids.append(child_id)
    for dictionary_id in sorted(used_dicts):
        record = dictionary_rows[dictionary_id]
        structured_record = {
            "dictionary_id": dictionary_id,
            "dictionary_name": record.get("dictionary_name", ""),
            "source_file": record.get("source_file", ""),
            "source_location": record.get("source_location", ""),
            "extraction_status": record.get("extraction_status", ""),
            "active_values": list(dictionary_active_values[dictionary_id]),
            "archived_values": record.get("archived_values", ""),
        }
        evidence_rows.extend(
            [
                f"## {dictionary_id}",
                "",
                "```json",
                json.dumps(structured_record, ensure_ascii=False, separators=(",", ":")),
                "```",
                "",
            ]
        )
    for dictionary_id in sorted(portable_dictionary_requirements):
        structured_record = _portable_dictionary_evidence_record(
            portable_dictionary_requirements[dictionary_id],
            package_plan_path=plan_path,
            repo_root=repo_root,
        )
        evidence_rows.extend(
            [
                f"## {dictionary_id}",
                "",
                "```json",
                json.dumps(
                    structured_record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "```",
                "",
            ]
        )

    evidence_text = "\n".join(evidence_rows).rstrip() + "\n"
    evidence_max_bytes = (
        SOURCE_FIRST_IMMUTABLE_EVIDENCE_MAX_BYTES
        if source_first_contract
        else (
            FAST_EVIDENCE_MAX_BYTES
            if execution_profile == FAST_PROFILE
            else STANDARD_ROUTING_EVIDENCE_MAX_BYTES
        )
    )
    evidence_bytes = len(evidence_text.encode("utf-8"))
    if evidence_bytes > evidence_max_bytes:
        raise StageRuntimeError(
            "blocked-package-budget: compiled evidence exceeds "
            f"{evidence_max_bytes} bytes for {execution_profile}: actual={evidence_bytes}"
        )
    temp_evidence = output_root.parent / f".{output_root.name}.compiled-evidence.md"
    if temp_evidence.exists():
        raise StageRuntimeError(f"compiler temporary evidence already exists: {temp_evidence}")
    temp_evidence.parent.mkdir(parents=True, exist_ok=True)
    temp_evidence.write_text(evidence_text, encoding="utf-8")
    try:
        obligation_set = PreparedObligationSet.create(
            package_id=package_id,
            obligations=obligations,
            coverage_gaps=gaps,
            evidence_text=evidence_text,
        )
        if section_id is None:
            canonical = str(state.get("canonical_test_cases", ""))
            match = SECTION_PREFIX.match(PurePosixPath(canonical).name)
            if not match:
                raise StageRuntimeError("section_id cannot be derived from workflow canonical_test_cases")
            section_id = match.group("section").removeprefix("section-").replace("-", ".")
        builder = PreparedPackageBuilder(
            repo_root,
            max_package_bytes=(
                SOURCE_FIRST_PACKAGE_MAX_BYTES
                if source_first_contract
                else 512000
            ),
        )
        standard_route = execution_profile == STANDARD_PROFILE
        builder.build(
            output_root=output_root,
            package_id=package_id,
            ft_slug=ft_slug,
            scope_slug=scope_slug,
            section_id=section_id,
            source_registry=_source_registry(
                repo_root,
                ft_root,
                source_selection_path,
                require_manifest_binding=source_first_contract,
            ),
            evidence_inputs=[
                EvidenceInput(
                    temp_evidence,
                    "Compiled fidelity projection",
                    include_full=True,
                    max_bytes=evidence_max_bytes,
                )
            ],
            obligations=obligation_set,
            instructions=StageInstructionConfig(
                role="writer",
                scenario=(
                    "writer.session_initial_draft"
                    if standard_route
                    else "writer.session_prepared_initial_draft"
                ),
                output_path=(attempt_root / "stage-output" / "draft.md").relative_to(repo_root).as_posix(),
                attempt_root=attempt_root.relative_to(repo_root).as_posix(),
                sandbox_policy="read_only",
                timeout_seconds=900 if standard_route else 180,
                idle_timeout_seconds=180 if standard_route else 60,
                command_budget=0,
            ),
            execution_profile=execution_profile,
            unsupported_dimensions=unsupported_dimensions,
            forbidden_evidence_roots=(
                (ft_root / "test-cases").relative_to(repo_root).as_posix(),
                (ft_root / "work" / "review-cycles").relative_to(repo_root).as_posix(),
            ),
            reuse_if_current=reuse_if_current,
            allow_blocking_primary_gaps=(
                output_mode == DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE
            ),
            release_status=package_release_status,
            immutable_evidence_max_bytes=(
                SOURCE_FIRST_IMMUTABLE_EVIDENCE_MAX_BYTES
                if source_first_contract
                else None
            ),
        )
    finally:
        temp_evidence.unlink(missing_ok=True)
    return CompileResult(
        stage_package=output_root / "stage-package.json",
        obligation_count=len(obligations),
        gap_count=len(gaps),
        dictionary_ref_count=len(
            used_dicts | set(portable_dictionary_requirements)
        ),
        section_id=section_id,
        execution_profile=execution_profile,
        unsupported_dimensions=unsupported_dimensions,
        output_mode=output_mode,
        release_eligible=release_eligible,
        blocking_gap_ids=blocking_gap_ids,
        release_blocking_finding_codes=release_blocking_finding_codes,
        execution_dependency_count=len(execution_dependency_registry),
        excluded_execution_obligation_ids=tuple(
            sorted(dependency_blocked_obligation_ids)
        ),
        cache_reused=output_existed and reuse_if_current,
    )
