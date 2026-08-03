from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.prepared_compiler import (
    _expected_source_assertion_rows,
    _table_with,
    _validate_source_assertion_chain,
    _validate_source_row_baseline_binding,
    _validate_source_selection_manifest_binding,
)
from test_case_agent.review_cycle.source_assertions import (
    load_source_assertion_manifest,
)
from test_case_agent.review_cycle.source_gate import (
    build_passed_source_gate_receipt,
    utc_now,
)


def under(root: Path, value: Path, *, label: str) -> Path:
    root = root.resolve()
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay under repository root: {path}") from exc
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the canonical one-invocation deterministic source assertion gate."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    parser.add_argument("--ft-root", type=Path, required=True)
    parser.add_argument("--source-row-inventory", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-selection", type=Path, required=True)
    parser.add_argument("--source-row-extraction-spec", type=Path, required=True)
    parser.add_argument("--source-row-baseline", type=Path, required=True)
    parser.add_argument("--atomic-requirements-ledger", type=Path, required=True)
    parser.add_argument("--coverage-obligation-table", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    started = utc_now()
    output = under(root, args.output, label="output")
    if output.exists():
        print("source gate output already exists", file=sys.stderr)
        return 2
    try:
        ft_root = under(root, args.ft_root, label="ft_root")
        inventory = under(root, args.source_row_inventory, label="inventory")
        manifest_path = under(root, args.manifest, label="manifest")
        selection = under(root, args.source_selection, label="source_selection")
        extraction_spec = under(
            root, args.source_row_extraction_spec, label="extraction_spec"
        )
        baseline = under(root, args.source_row_baseline, label="baseline")
        ledger = under(
            root, args.atomic_requirements_ledger, label="atomic_requirements_ledger"
        )
        obligations = under(
            root, args.coverage_obligation_table, label="coverage_obligation_table"
        )
        expected_rows = _expected_source_assertion_rows(inventory)
        manifest = load_source_assertion_manifest(
            manifest_path,
            root,
            expected_source_rows=expected_rows,
        )
        selected = _validate_source_selection_manifest_binding(
            repo_root=root,
            ft_root=ft_root,
            source_selection=selection,
            manifest=manifest,
        )
        selected_xhtml = next(
            item for item in selected if item.source_selection_role == "main-ft-xhtml"
        )
        completeness = _validate_source_row_baseline_binding(
            repo_root=root,
            extraction_spec_path=extraction_spec,
            baseline_path=baseline,
            manifest=manifest,
            scope_slug=manifest.scope_slug,
            selected_xhtml=selected_xhtml,
        )
        ledger_rows = _table_with(
            ledger,
            {
                "atom_id",
                "atomic_statement",
                "coverage_status",
                "source_row_id",
                "requirement_codes",
            },
        )
        obligation_rows = _table_with(
            obligations,
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
                "source_row_id",
                "requirement_codes",
            },
        )
        assertion_by_atom, assertion_by_obligation = _validate_source_assertion_chain(
            manifest=manifest,
            ledger_by_atom={row["atom_id"]: row for row in ledger_rows},
            obligation_rows=obligation_rows,
        )
        payload = build_passed_source_gate_receipt(
            manifest=manifest,
            started_at_utc=started,
            finished_at_utc=utc_now(),
            actual_source_row_count=len(expected_rows),
            actual_candidate_count=completeness.candidate_count,
            actual_assertion_count=len(assertion_by_atom),
            actual_authenticated_testable_obligation_count=len(
                assertion_by_obligation
            ),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001 - one gate invocation, no retry.
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "started_at_utc": started,
                    "finished_at_utc": utc_now(),
                    "status": "failed",
                    "validation_invocation_count": 1,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
