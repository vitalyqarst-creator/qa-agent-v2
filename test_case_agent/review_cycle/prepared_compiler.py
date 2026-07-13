from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .prepared_package import (
    EvidenceInput,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
    PreparedStateChange,
    PreparedPackageBuilder,
    StageInstructionConfig,
    FAST_EVIDENCE_MAX_BYTES,
    STANDARD_ROUTING_EVIDENCE_MAX_BYTES,
)
from .runtime import StageRuntimeError


TOKEN = re.compile(
    r"\b(?:ATOM|OBL|GAP|DICT|SRC)-[A-Za-z0-9_.-]+\b|\b(?:GSR|BSR|DIT)\s+\d+\b"
)
TC_TOKEN = re.compile(r"\bTC-[A-Za-z0-9_.-]+\b")
FIXTURE_TOKEN = re.compile(r"\bFIX-[A-Za-z0-9_.-]+\b")
COMPILER_CONTRACT_VERSION = 2
SECTION_PREFIX = re.compile(r"^(?P<section>(?:section-)?\d+(?:[-.]\d+)*)-")
FAST_PROFILE = "simple-field-property"
STANDARD_PROFILE = "standard-required"
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


def _normalized_design_value(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


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
        columns = [_clean_cell(item) for item in header.strip("|").split("|")]
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = [_clean_cell(item) for item in lines[index].strip().strip("|").split("|")]
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


def _gap_sections(path: Path | None) -> dict[str, PreparedGap]:
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
        result[match.group(1)] = PreparedGap(
            gap_id=match.group(1),
            source_refs=refs or (match.group(1),),
            problem=problem_text,
            handling=handling_text,
            blocking=(
                bool(impact and "non-blocking" not in impact.group(1).lower())
                or status_text in {"blocking", "blocked"}
            ),
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
            result[gap_id] = PreparedGap(
                gap_id=gap_id,
                source_refs=refs or (gap_id,),
                problem=problem,
                handling=handling,
                blocking=(
                    "blocking" in blocking_text
                    and "non-blocking" not in blocking_text
                    or re.search(r"\byes\b", blocking_text) is not None
                ),
            )
    return result


def _within(path: Path, root: Path, label: str) -> Path:
    path = path.resolve()
    root = root.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise StageRuntimeError(f"{label} escapes {root}: {path}") from exc
    return path


def _source_registry(ft_root: Path, source_selection: Path) -> list[tuple[Path, str, str]]:
    rows = _table_with(source_selection, {"path", "role"})
    role_map = {
        "main-ft-docx": ("source-of-truth", {".docx"}),
        "main-ft-xhtml": ("machine-readable", {".xhtml", ".html"}),
        "main-ft-pdf": ("structural-cross-check", {".pdf"}),
    }
    selected: dict[str, Path] = {}
    for row in rows:
        source_role = row["role"]
        if source_role not in role_map:
            continue
        if source_role in selected:
            raise StageRuntimeError(f"source-selection has duplicate {source_role} rows")
        raw_path = PurePosixPath(row["path"])
        if raw_path.is_absolute():
            raise StageRuntimeError(f"source-selection path must be FT-relative: {row['path']}")
        path = _within(ft_root / Path(*raw_path.parts), ft_root, "selected source")
        expected_role, suffixes = role_map[source_role]
        if path.suffix.lower() not in suffixes:
            raise StageRuntimeError(f"{source_role} has invalid extension: {row['path']}")
        if not path.is_file():
            raise StageRuntimeError(f"selected source is missing: {row['path']}")
        selected[source_role] = path
    for required in ("main-ft-docx", "main-ft-xhtml"):
        if required not in selected:
            raise StageRuntimeError(f"source-selection requires exactly one {required} source")
    if selected["main-ft-docx"].stem != selected["main-ft-xhtml"].stem:
        raise StageRuntimeError("selected DOCX and XHTML/HTML must have the same base name")
    if (
        "main-ft-pdf" in selected
        and selected["main-ft-docx"].stem != selected["main-ft-pdf"].stem
    ):
        raise StageRuntimeError("selected DOCX and PDF must have the same base name")
    text = source_selection.read_text(encoding="utf-8")
    if not re.search(r"xhtml_available:\s*`?yes`?", text, re.IGNORECASE):
        raise StageRuntimeError("source-selection does not confirm xhtml_available: yes")
    if not re.search(r"xhtml_matches_main_ft:\s*`?yes`?", text, re.IGNORECASE):
        raise StageRuntimeError("source-selection does not confirm xhtml_matches_main_ft: yes")
    registry: list[tuple[Path, str, str]] = []
    for source_role in ("main-ft-docx", "main-ft-xhtml", "main-ft-pdf"):
        if source_role in selected:
            target_role = role_map[source_role][0]
            registry.append((selected[source_role], target_role, f"pinned by {source_selection.name}"))
    return registry


def _execution_route(applicability_matrix: Path) -> tuple[str, tuple[str, ...]]:
    rows = _table_with(applicability_matrix, {"dimension", "applicable"})
    unsupported: set[str] = set()
    for row in rows:
        applicability = row["applicable"].lower()
        if applicability == "no":
            continue
        evidence_qualified = applicability.startswith("yes_with_")
        if applicability not in {"yes", "unclear", "unclear-limited"} and not evidence_qualified:
            raise StageRuntimeError(
                "test-design applicability must be yes, no, unclear or yes_with_*: "
                f"{row['dimension']}={row['applicable']}"
            )
        dimension = re.sub(r"[^a-z0-9_.-]+", "-", row["dimension"].lower()).strip("-")
        if applicability == "unclear":
            if not any(token.startswith("GAP-") for token in TOKEN.findall(" ".join(row.values()))):
                raise StageRuntimeError(
                    f"unclear test-design dimension must link a GAP id: {row['dimension']}"
                )
            continue
        if applicability == "unclear-limited":
            unsupported.add("limited-default-oracle")
            continue
        if evidence_qualified:
            qualifier = applicability.removeprefix("yes_with_").replace("_", "-")
            unsupported.add(f"evidence-qualified-{qualifier}")
        if dimension in FAST_DIMENSIONS:
            continue
        normalized = DIMENSION_GROUPS.get(
            dimension, re.sub(r"[^a-z0-9_.-]+", "-", dimension).strip("-")
        )
        unsupported.add(normalized or "unclassified-dimension")
    if unsupported:
        return STANDARD_PROFILE, tuple(sorted(unsupported))
    return FAST_PROFILE, ()


def _route_obligation_dimensions(
    rows: Sequence[Mapping[str, str]],
    unsupported_dimensions: Sequence[str],
) -> tuple[str, tuple[str, ...]]:
    unsupported = set(unsupported_dimensions)
    for row in rows:
        if row.get("status", "").lower() != "covered":
            continue
        property_type = re.sub(
            r"[^a-z0-9_.-]+", "-", row.get("property_type", "").lower()
        ).strip("-")
        mapped = OBLIGATION_DIMENSION_GROUPS.get(property_type)
        if mapped:
            unsupported.add(mapped)
    if unsupported:
        return STANDARD_PROFILE, tuple(sorted(unsupported))
    return FAST_PROFILE, ()


@dataclass(frozen=True)
class CompileResult:
    stage_package: Path
    obligation_count: int
    gap_count: int
    dictionary_ref_count: int
    section_id: str
    execution_profile: str
    unsupported_dimensions: tuple[str, ...]


def compile_workflow_package(
    *,
    workflow_state: Path,
    repo_root: Path,
    output_root: Path,
    package_id: str,
    attempt_root: Path,
    expected_ft_slug: str,
    section_id: str | None = None,
) -> CompileResult:
    repo_root = repo_root.resolve()
    workflow_state = workflow_state.resolve()
    output_root = output_root.resolve()
    attempt_root = attempt_root.resolve()
    expected_ft_root = (repo_root / "fts" / expected_ft_slug).resolve()
    if not expected_ft_root.is_dir():
        raise StageRuntimeError(f"expected FT package is missing: fts/{expected_ft_slug}")
    _within(workflow_state, expected_ft_root, "workflow-state")
    state = load_workflow_state(workflow_state)
    contract_version = state.get("prepared_compiler_contract_version")
    if contract_version != COMPILER_CONTRACT_VERSION:
        raise StageRuntimeError(
            "workflow-state prepared_compiler_contract_version must be "
            f"{COMPILER_CONTRACT_VERSION}; run scripts/migrate_prepared_compiler_contract.py"
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
    if len(output_relative.parts) < 3 or output_relative.parts[1] != "prepared-input":
        raise StageRuntimeError("prepared output must be under <cycle>/prepared-input/<package-id>")
    if len(attempt_relative.parts) < 4 or attempt_relative.parts[1] != "attempts":
        raise StageRuntimeError("attempt root must be under <cycle>/attempts/<stage>/<attempt-id>")

    source_selection_path = _artifact(ft_root, state, "source_selection")
    ledger_path = _artifact(ft_root, state, "atomic_requirements_ledger")
    obligations_path = _artifact(ft_root, state, "coverage_obligation_table")
    plan_path = _artifact(ft_root, state, "package_test_design_plan")
    applicability_path = _artifact(ft_root, state, "test_design_applicability_matrix")
    decision_path = _artifact(
        ft_root, state, "test_design_decision_table", required=False
    )
    gaps_path = _artifact(ft_root, state, "coverage_gaps", required=False)
    dictionary_path = _artifact(ft_root, state, "dictionary_inventory", required=False)
    assert (
        source_selection_path is not None
        and ledger_path is not None
        and obligations_path is not None
        and plan_path is not None
        and applicability_path is not None
    )
    execution_profile, unsupported_dimensions = _execution_route(applicability_path)
    ledger = _table_with(ledger_path, {"atom_id", "atomic_statement", "coverage_status"})
    obligation_rows = _table_with(
        obligations_path,
        {
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
        },
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
    fixture_contracts = {fixture_id: text for fixture_id, text in fixture_contract_lines}
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
    plan_by_atom: dict[str, list[dict[str, str]]] = {}
    for row in plan:
        for atom in TOKEN.findall(row.get("linked_atoms", "")):
            if atom.startswith("ATOM-"):
                plan_by_atom.setdefault(atom, []).append(row)
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
    known_gaps = _gap_sections(gaps_path)
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
    if fixture_contract_lines:
        evidence_rows.extend(
            [
                "## Portable fixture contracts",
                "",
                *dict.fromkeys(text for _, text in fixture_contract_lines),
                "",
            ]
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
        row = ledger_by_atom[atom_id]
        status_raw = row["coverage_status"].lower()
        obligation_status = obligation_row["status"].lower()
        linked = plan_by_atom.get(atom_id, [])
        constraint_gap_tokens = list(
            dict.fromkeys(TOKEN.findall(row.get("constraint_gap_ids", "")))
        )
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
        if obligation_status == "covered":
            if atom_coverage_status in {"gap", "unclear", "not-applicable"}:
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} cannot cover {atom_coverage_status} {atom_id}"
                )
            coverage_status = "testable"
            if not obligation_row["planned_tc_or_gap"].startswith("TC-"):
                raise StageRuntimeError(
                    f"semantic degradation: {obligation_id} covered row must link a TC id"
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
            planned_tc_id = obligation_row["planned_tc_or_gap"]
            mapped_viable = [
                item
                for item in viable
                if planned_tc_id in TC_TOKEN.findall(item.get("planned_tc_or_gap", ""))
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
            intent_parts = [item["planned_check"] for item in mapped_viable]
            if state_change is not None:
                intent_parts = [
                    state_change.initial_state_capture,
                    state_change.changed_state_setup,
                    "Before the target action verify: "
                    + state_change.pre_action_state_oracle,
                    *intent_parts,
                ]
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
        source_refs = tuple(dict.fromkeys(source_tokens + dict_tokens))
        if not source_refs:
            source_ref = obligation_row.get("source_ref") or row.get("source_ref") or row.get("source_property_id")
            if not source_ref:
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no source reference")
            source_refs = (source_ref,)
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
                        " Non-blocking constraints: " + ", ".join(constraint_gap_tokens) + "."
                        if constraint_gap_tokens
                        else ""
                    )
                ),
                constraint_gap_ids=tuple(constraint_gap_tokens),
                planned_test_case_id=(
                    obligation_row["planned_tc_or_gap"]
                    if coverage_status == "testable"
                    else ""
                ),
                execution_semantics=(
                    RESET_EXECUTION_SEMANTICS
                    if state_change is not None
                    else "direct"
                ),
                state_change=state_change,
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
    unsupported_dimensions = tuple(sorted(routed_unsupported_dimensions))
    execution_profile = STANDARD_PROFILE if unsupported_dimensions else FAST_PROFILE
    gaps: list[PreparedGap] = []
    orphan_gaps = sorted(set(known_gaps) - used_gaps)
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

    evidence_text = "\n".join(evidence_rows).rstrip() + "\n"
    evidence_max_bytes = (
        FAST_EVIDENCE_MAX_BYTES
        if execution_profile == FAST_PROFILE
        else STANDARD_ROUTING_EVIDENCE_MAX_BYTES
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
        builder = PreparedPackageBuilder(repo_root)
        standard_route = execution_profile == STANDARD_PROFILE
        builder.build(
            output_root=output_root,
            package_id=package_id,
            ft_slug=ft_slug,
            scope_slug=scope_slug,
            section_id=section_id,
            source_registry=_source_registry(ft_root, source_selection_path),
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
        )
    finally:
        temp_evidence.unlink(missing_ok=True)
    return CompileResult(
        stage_package=output_root / "stage-package.json",
        obligation_count=len(obligations),
        gap_count=len(gaps),
        dictionary_ref_count=len(used_dicts),
        section_id=section_id,
        execution_profile=execution_profile,
        unsupported_dimensions=unsupported_dimensions,
    )
