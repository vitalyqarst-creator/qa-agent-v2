from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .prepared_package import (
    EvidenceInput,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
    PreparedPackageBuilder,
    StageInstructionConfig,
)
from .runtime import StageRuntimeError


TOKEN = re.compile(r"\b(?:ATOM|GAP|DICT|SRC)-[A-Za-z0-9_.-]+\b|\bGSR\s+\d+\b")
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
            if row.get("status", "").lower() in {"closed", "resolved", "not-applicable"}:
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
        if applicability not in {"yes", "unclear", "unclear-limited"}:
            raise StageRuntimeError(
                "test-design applicability must be yes, no or unclear: "
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
        if dimension in FAST_DIMENSIONS:
            continue
        normalized = DIMENSION_GROUPS.get(
            dimension, re.sub(r"[^a-z0-9_.-]+", "-", dimension).strip("-")
        )
        unsupported.add(normalized or "unclassified-dimension")
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
    plan_path = _artifact(ft_root, state, "package_test_design_plan")
    applicability_path = _artifact(ft_root, state, "test_design_applicability_matrix")
    gaps_path = _artifact(ft_root, state, "coverage_gaps", required=False)
    dictionary_path = _artifact(ft_root, state, "dictionary_inventory", required=False)
    assert (
        source_selection_path is not None
        and ledger_path is not None
        and plan_path is not None
        and applicability_path is not None
    )
    execution_profile, unsupported_dimensions = _execution_route(applicability_path)
    ledger = _table_with(ledger_path, {"atom_id", "atomic_statement", "coverage_status"})
    plan = _table_with(plan_path, {"linked_atoms", "planned_check", "single_expected_behavior"})
    plan_by_atom: dict[str, list[dict[str, str]]] = {}
    for row in plan:
        for atom in TOKEN.findall(row.get("linked_atoms", "")):
            if atom.startswith("ATOM-"):
                plan_by_atom.setdefault(atom, []).append(row)
    known_gaps = _gap_sections(gaps_path)
    dictionary_rows: dict[str, dict[str, str]] = {}
    if dictionary_path is not None:
        for row in _table_with(dictionary_path, {"dictionary_id", "active_values"}):
            if not row["active_values"].strip():
                raise StageRuntimeError(
                    f"semantic degradation: {row['dictionary_id']} has no active values"
                )
            if row["dictionary_id"] in dictionary_rows:
                raise StageRuntimeError(
                    f"semantic degradation: duplicate dictionary {row['dictionary_id']}"
                )
            dictionary_rows[row["dictionary_id"]] = row

    obligations: list[PreparedObligation] = []
    used_gaps: set[str] = set()
    used_dicts: set[str] = set()
    evidence_rows: list[str] = ["# Compiled Prepared Evidence", ""]
    for row in ledger:
        atom_id = row["atom_id"]
        status_raw = row["coverage_status"].lower()
        linked = plan_by_atom.get(atom_id, [])
        constraint_gap_tokens = list(
            dict.fromkeys(TOKEN.findall(row.get("constraint_gap_ids", "")))
        )
        if any(not item.startswith("GAP-") for item in constraint_gap_tokens):
            raise StageRuntimeError(
                f"semantic degradation: {atom_id} constraint_gap_ids must contain only GAP ids"
            )
        gap_tokens = list(
            dict.fromkeys(item for item in TOKEN.findall(" ".join(row.values())) if item.startswith("GAP-"))
        )
        dict_tokens = list(
            dict.fromkeys(item for item in TOKEN.findall(" ".join(row.values())) if item.startswith("DICT-"))
        )
        source_tokens = [
            item
            for item in TOKEN.findall(" ".join(row.values()))
            if item.startswith("SRC-") or item.startswith("GSR")
        ]
        if status_raw in {"covered", "testable"}:
            coverage_status = "testable"
        elif status_raw in {"unclear", "gap", "not-applicable"}:
            coverage_status = status_raw
        else:
            raise StageRuntimeError(
                f"semantic degradation: {atom_id} has unsupported coverage_status {status_raw}"
            )
        if coverage_status == "testable":
            viable = [item for item in linked if item.get("status", "covered").lower() in {"covered", "testable", "planned"}]
            if not viable:
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no testable design-plan row")
            oracle = "; ".join(dict.fromkeys(item["single_expected_behavior"] for item in viable))
            intent = "; ".join(dict.fromkeys(item["planned_check"] for item in viable))
            if not oracle or "none_required" in oracle.lower():
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no observable plan oracle")
            for constraint_gap_id in constraint_gap_tokens:
                if constraint_gap_id not in known_gaps:
                    raise StageRuntimeError(
                        "semantic degradation: constraint gap is missing from coverage-gaps.md: "
                        f"{constraint_gap_id}"
                    )
                used_gaps.add(constraint_gap_id)
            gap_id = ""
        elif coverage_status in {"gap", "unclear"}:
            if len(set(gap_tokens)) != 1:
                raise StageRuntimeError(f"semantic degradation: {atom_id} must link exactly one GAP id")
            gap_id = gap_tokens[0]
            used_gaps.add(gap_id)
            if gap_id in known_gaps and known_gaps[gap_id].source_refs == (gap_id,):
                raise StageRuntimeError(
                    f"semantic degradation: {gap_id} has no exact source reference"
                )
            oracle = ""
            intent = linked[0]["planned_check"] if linked else "Не создавать исполнимое покрытие до закрытия gap."
        else:
            gap_id = ""
            oracle = ""
            intent = "Не создавать отдельный тест-кейс для metadata-only утверждения."
        for dictionary_id in dict_tokens:
            if dictionary_id not in dictionary_rows:
                raise StageRuntimeError(f"semantic degradation: {atom_id} references missing {dictionary_id}")
            used_dicts.add(dictionary_id)
        source_refs = tuple(dict.fromkeys(source_tokens + dict_tokens))
        if not source_refs:
            source_ref = row.get("source_ref") or row.get("source_property_id")
            if not source_ref:
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no source reference")
            source_refs = (source_ref,)
        obligations.append(
            PreparedObligation(
                obligation_id=atom_id,
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
            )
        )
        evidence_rows.extend([f"## {atom_id}", "", " | ".join(row.values()), ""])
        for item in linked:
            evidence_rows.extend([f"- plan: {' | '.join(item.values())}", ""])
    gaps: list[PreparedGap] = []
    orphan_gaps = sorted(set(known_gaps) - used_gaps)
    if orphan_gaps:
        raise StageRuntimeError(
            "semantic degradation: coverage gaps are not linked from the atomic ledger: "
            + ", ".join(orphan_gaps)
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
    for dictionary_id in sorted(used_dicts):
        evidence_rows.extend(
            [f"## {dictionary_id}", "", " | ".join(dictionary_rows[dictionary_id].values()), ""]
        )

    evidence_text = "\n".join(evidence_rows).rstrip() + "\n"
    if len(evidence_text.encode("utf-8")) > 32768:
        raise StageRuntimeError("blocked-package-budget: compiled evidence exceeds 32768 bytes")
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
        builder.build(
            output_root=output_root,
            package_id=package_id,
            ft_slug=ft_slug,
            scope_slug=scope_slug,
            section_id=section_id,
            source_registry=_source_registry(ft_root, source_selection_path),
            evidence_inputs=[EvidenceInput(temp_evidence, "Compiled fidelity projection", include_full=True, max_bytes=32768)],
            obligations=obligation_set,
            instructions=StageInstructionConfig(
                role="writer",
                scenario="writer.session_prepared_initial_draft",
                output_path=(attempt_root / "stage-output" / "draft.md").relative_to(repo_root).as_posix(),
                attempt_root=attempt_root.relative_to(repo_root).as_posix(),
                sandbox_policy="workspace_write",
                timeout_seconds=180,
                idle_timeout_seconds=60,
                command_budget=12,
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
