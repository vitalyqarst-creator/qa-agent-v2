from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.prepared_compiler import (  # noqa: E402
    COMPILER_CONTRACT_VERSION,
    load_workflow_state,
    markdown_tables,
)
from test_case_agent.review_cycle.runtime import StageRuntimeError  # noqa: E402


CANONICAL_COLUMNS = (
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
)
LEGACY_COLUMNS = {
    "obligation_id",
    "dimension",
    "source_ref",
    "linked_atom",
    "coverage_status",
    "linked_tc_or_gap",
    "rationale",
}


def _within(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise StageRuntimeError(f"{label} escapes {root}: {resolved}") from exc
    return resolved


def _render_table(rows: list[dict[str, str]]) -> str:
    header = "| " + " | ".join(CANONICAL_COLUMNS) + " |"
    separator = "| " + " | ".join("---" for _ in CANONICAL_COLUMNS) + " |"
    body = [
        "| " + " | ".join(row[column] for column in CANONICAL_COLUMNS) + " |"
        for row in rows
    ]
    return "# Coverage Obligation Table\n\n" + "\n".join((header, separator, *body)) + "\n"


def _atomic_replace(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.prepared-contract-migration.tmp")
    if temporary.exists():
        raise StageRuntimeError(f"migration temporary file already exists: {temporary}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _state_with_contract(
    text: str, *, obligation_relative: str
) -> str:
    lines = text.splitlines()
    if not any(line.startswith("prepared_compiler_contract_version:") for line in lines):
        ft_index = next(
            (index for index, line in enumerate(lines) if line.startswith("ft_slug:")), None
        )
        if ft_index is None:
            raise StageRuntimeError("compiler input has no ft_slug")
        lines.insert(ft_index + 1, f"prepared_compiler_contract_version: {COMPILER_CONTRACT_VERSION}")
    if not any(line.strip().startswith("coverage_obligation_table:") for line in lines):
        ledger_index = next(
            (
                index
                for index, line in enumerate(lines)
                if line.strip().startswith("atomic_requirements_ledger:")
            ),
            None,
        )
        if ledger_index is None:
            raise StageRuntimeError("compiler input has no latest_artifacts.atomic_requirements_ledger")
        indent = lines[ledger_index][: len(lines[ledger_index]) - len(lines[ledger_index].lstrip())]
        lines.insert(
            ledger_index + 1,
            f"{indent}coverage_obligation_table: {obligation_relative}",
        )
    return "\n".join(lines).rstrip() + "\n"


def migrate(
    *,
    workflow_state: Path,
    repo_root: Path,
    expected_ft_slug: str,
    write: bool,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    ft_root = (repo_root / "fts" / expected_ft_slug).resolve()
    workflow_state = _within(workflow_state, ft_root, "compiler input")
    state = load_workflow_state(workflow_state)
    if state.get("ft_slug") != expected_ft_slug:
        raise StageRuntimeError(
            f"compiler input ft_slug mismatch: expected {expected_ft_slug}, found {state.get('ft_slug')}"
        )
    latest = state.get("latest_artifacts")
    if not isinstance(latest, dict):
        raise StageRuntimeError("compiler input latest_artifacts map is required")
    ledger_value = latest.get("atomic_requirements_ledger")
    if not isinstance(ledger_value, str):
        raise StageRuntimeError("latest_artifacts.atomic_requirements_ledger is required")
    ledger_path = _within(ft_root / ledger_value, ft_root, "atomic ledger")
    obligation_value = latest.get("coverage_obligation_table")
    obligation_path = (
        _within(ft_root / str(obligation_value), ft_root, "coverage obligation table")
        if obligation_value
        else ledger_path.with_name("coverage-obligation-table.md")
    )
    if not obligation_path.is_file():
        raise StageRuntimeError(
            "semantic migration required: coverage-obligation-table.md is missing; "
            "the migrator will not invent obligations from atoms"
        )
    tables = markdown_tables(obligation_path)
    table = next((item for item in tables if item), None)
    if table is None:
        raise StageRuntimeError("coverage obligation table is empty or unparseable")
    columns = set(table[0])
    migrated_rows: list[dict[str, str]] | None = None
    if set(CANONICAL_COLUMNS) <= columns:
        migration_kind = "already-canonical"
    elif LEGACY_COLUMNS <= columns:
        ledger = next(
            (
                item
                for item in markdown_tables(ledger_path)
                if item and {"atom_id", "atomic_statement"} <= set(item[0])
            ),
            None,
        )
        if ledger is None:
            raise StageRuntimeError("atomic ledger is missing canonical atom columns")
        atoms = {row["atom_id"]: row for row in ledger}
        migrated_rows = []
        for position, row in enumerate(table, 1):
            linked_atom = row["linked_atom"]
            if linked_atom not in atoms:
                raise StageRuntimeError(
                    "semantic migration required: legacy obligation row has no single known atom: "
                    f"row {position}, {linked_atom}"
                )
            old_id = row["obligation_id"]
            suffix = old_id.split("-", 1)[1] if "-" in old_id else f"{position:03d}"
            migrated_rows.append(
                {
                    "obligation_id": f"OBL-{suffix}",
                    "package_id": atoms[linked_atom].get("package_id") or "WP-01",
                    "source_property_id": row["source_ref"],
                    "linked_atom_id": linked_atom,
                    "property_type": row["dimension"],
                    "obligation_class": row["dimension"],
                    "required_behavior": atoms[linked_atom]["atomic_statement"],
                    "source_ref": row["source_ref"],
                    "planned_tc_or_gap": row["linked_tc_or_gap"],
                    "status": row["coverage_status"],
                    "review_notes": row["rationale"],
                }
            )
        migration_kind = "legacy-alias-table"
    else:
        raise StageRuntimeError(
            "semantic migration required: unsupported coverage obligation columns: "
            + ", ".join(sorted(columns))
        )

    obligation_relative = obligation_path.relative_to(ft_root).as_posix()
    state_text = workflow_state.read_text(encoding="utf-8")
    migrated_state = _state_with_contract(
        state_text, obligation_relative=obligation_relative
    )
    changed = migrated_rows is not None or migrated_state != state_text
    if write and changed:
        if migrated_rows is not None:
            _atomic_replace(obligation_path, _render_table(migrated_rows))
        _atomic_replace(workflow_state, migrated_state)
    return {
        "status": "migrated" if changed else "already-current",
        "write": write,
        "migration_kind": migration_kind,
        "workflow_state": workflow_state.relative_to(repo_root).as_posix(),
        "coverage_obligation_table": obligation_path.relative_to(repo_root).as_posix(),
        "rows": len(migrated_rows if migrated_rows is not None else table),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Migrate a prepared compiler input to contract version 2"
    )
    result.add_argument("--workflow-state", required=True)
    result.add_argument("--expected-ft-slug", required=True)
    result.add_argument("--repo-root", default=".")
    result.add_argument("--write", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        result = migrate(
            workflow_state=repo_root / args.workflow_state,
            repo_root=repo_root,
            expected_ft_slug=args.expected_ft_slug,
            write=args.write,
        )
    except (OSError, StageRuntimeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
