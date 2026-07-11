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
    matches = list(re.finditer(r"^#{2,4}\s+(GAP-[A-Za-z0-9_.-]+)\s*$", text, re.MULTILINE))
    result: dict[str, PreparedGap] = {}
    for pos, match in enumerate(matches):
        block = text[match.end() : matches[pos + 1].start() if pos + 1 < len(matches) else len(text)]
        refs = tuple(dict.fromkeys(token for token in TOKEN.findall(block) if not token.startswith("GAP-")))
        impact = re.search(r"\*\*Impact:\*\*\s*`?([^`\n]+)", block, re.IGNORECASE)
        handling = re.search(r"\*\*Handling:\*\*\s*([^\n]+)", block, re.IGNORECASE)
        problem = re.search(r"\*\*(?:Problem|FT Reference):\*\*\s*([^\n]+)", block, re.IGNORECASE)
        result[match.group(1)] = PreparedGap(
            gap_id=match.group(1),
            source_refs=refs or (match.group(1),),
            problem=_clean_cell(problem.group(1)) if problem else "Неопределённость зафиксирована в coverage gaps.",
            handling=_clean_cell(handling.group(1)) if handling else "Сохранить как coverage gap.",
            blocking=bool(impact and "non-blocking" not in impact.group(1).lower()),
        )
    return result


def _source_registry(ft_root: Path) -> list[tuple[Path, str, str]]:
    source_root = ft_root / "source"
    docx = sorted(source_root.glob("*.docx"))
    xhtml = sorted([*source_root.glob("*.xhtml"), *source_root.glob("*.html")])
    if len(docx) != 1 or len(xhtml) != 1:
        selection_files = sorted((ft_root / "work" / "stage-handoffs").glob("**/source-selection.md"))
        selected_text = "\n".join(item.read_text(encoding="utf-8") for item in selection_files)
        docx = [item for item in docx if item.relative_to(ft_root).as_posix() in selected_text]
        xhtml = [item for item in xhtml if item.relative_to(ft_root).as_posix() in selected_text]
    if len(docx) != 1 or len(xhtml) != 1:
        raise StageRuntimeError(
            "prepared compiler requires exactly one selected DOCX and one selected XHTML/HTML source"
        )
    return [
        (docx[0], "source-of-truth", "selected FT source"),
        (xhtml[0], "machine-readable", "selected FT extraction source"),
    ]


@dataclass(frozen=True)
class CompileResult:
    stage_package: Path
    obligation_count: int
    gap_count: int
    dictionary_ref_count: int
    section_id: str


def compile_workflow_package(
    *,
    workflow_state: Path,
    repo_root: Path,
    output_root: Path,
    package_id: str,
    attempt_root: Path,
    section_id: str | None = None,
) -> CompileResult:
    repo_root = repo_root.resolve()
    workflow_state = workflow_state.resolve()
    output_root = output_root.resolve()
    attempt_root = attempt_root.resolve()
    state = load_workflow_state(workflow_state)
    ft_slug = str(state.get("ft_slug", ""))
    scope_slug = str(state.get("scope_slug", ""))
    if not ft_slug or not scope_slug:
        raise StageRuntimeError("workflow-state requires ft_slug and scope_slug")
    ft_root = workflow_state
    while ft_root != repo_root and ft_root.name != ft_slug:
        ft_root = ft_root.parent
    if ft_root.name != ft_slug:
        raise StageRuntimeError("workflow-state path does not belong to its ft_slug")

    ledger_path = _artifact(ft_root, state, "atomic_requirements_ledger")
    plan_path = _artifact(ft_root, state, "package_test_design_plan")
    gaps_path = _artifact(ft_root, state, "coverage_gaps", required=False)
    dictionary_path = _artifact(ft_root, state, "dictionary_inventory", required=False)
    assert ledger_path is not None and plan_path is not None
    ledger = _table_with(ledger_path, {"atom_id", "statement", "coverage_status"})
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
            dictionary_rows[row["dictionary_id"]] = row

    obligations: list[PreparedObligation] = []
    used_gaps: set[str] = set()
    used_dicts: set[str] = set()
    evidence_rows: list[str] = ["# Compiled Prepared Evidence", ""]
    for row in ledger:
        atom_id = row["atom_id"]
        status_raw = row["coverage_status"].lower()
        linked = plan_by_atom.get(atom_id, [])
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
        coverage_status = (
            "testable" if status_raw in {"covered", "testable"}
            else "unclear" if status_raw == "unclear"
            else "gap" if status_raw == "gap"
            else "not-applicable"
        )
        if coverage_status == "testable":
            viable = [item for item in linked if item.get("status", "covered").lower() in {"covered", "testable", "planned"}]
            if not viable:
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no testable design-plan row")
            oracle = "; ".join(dict.fromkeys(item["single_expected_behavior"] for item in viable))
            intent = "; ".join(dict.fromkeys(item["planned_check"] for item in viable))
            if not oracle or "none_required" in oracle.lower():
                raise StageRuntimeError(f"semantic degradation: {atom_id} has no observable plan oracle")
            gap_id = ""
        elif coverage_status in {"gap", "unclear"}:
            if len(set(gap_tokens)) != 1:
                raise StageRuntimeError(f"semantic degradation: {atom_id} must link exactly one GAP id")
            gap_id = gap_tokens[0]
            used_gaps.add(gap_id)
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
                atomic_statement=row["statement"],
                observable_oracle=oracle,
                test_intent=intent,
                coverage_status=coverage_status,
                gap_id=gap_id,
                dictionary_refs=tuple(dict_tokens),
                notes="Compiled from workflow-state canonical design artifacts.",
            )
        )
        evidence_rows.extend([f"## {atom_id}", "", " | ".join(row.values()), ""])
        for item in linked:
            evidence_rows.extend([f"- plan: {' | '.join(item.values())}", ""])
    gaps: list[PreparedGap] = []
    for gap_id in sorted(used_gaps):
        if gap_id not in known_gaps:
            raise StageRuntimeError(f"semantic degradation: linked gap is missing from coverage-gaps.md: {gap_id}")
        gaps.append(known_gaps[gap_id])
        evidence_rows.extend([f"## {gap_id}", "", known_gaps[gap_id].problem, known_gaps[gap_id].handling, ""])
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
            source_registry=_source_registry(ft_root),
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
            execution_profile="simple-field-property",
            unsupported_dimensions=(),
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
    )
