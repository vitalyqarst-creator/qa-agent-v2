from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.traceability_mismatch_diagnostics import (  # noqa: E402
    build_traceability_mismatch_diagnostics,
    write_traceability_mismatch_diagnostics,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect traceability mismatches between writer proposals, update plan, and current TC traceability."
    )
    parser.add_argument(
        "--proposal",
        action="append",
        required=True,
        type=Path,
        help="writer-dry-run-proposal-<package-id>.json; repeatable.",
    )
    parser.add_argument("--writer-package-tasks", required=True, type=Path)
    parser.add_argument("--manual-update-packages", required=True, type=Path)
    parser.add_argument("--update-plan", required=True, type=Path)
    parser.add_argument("--impact-report", required=True, type=Path)
    parser.add_argument("--requirements-diff", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    report = build_traceability_mismatch_diagnostics(
        proposal_paths=args.proposal,
        writer_package_tasks_path=args.writer_package_tasks,
        manual_update_packages_path=args.manual_update_packages,
        update_plan_path=args.update_plan,
        impact_report_path=args.impact_report,
        requirements_diff_path=args.requirements_diff,
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/inspect_traceability_mismatches.py",
    )
    json_path, markdown_path = write_traceability_mismatch_diagnostics(report, args.out_dir)
    payload = {
        "traceability_mismatch_diagnostics_json_path": str(json_path),
        "traceability_mismatch_diagnostics_markdown_path": str(markdown_path),
        "diagnostic_status": report.summary["diagnostic_status"],
        "mismatches_total": report.summary["mismatches_total"],
        "packages_analyzed": report.summary["packages_analyzed"],
        "test_cases_analyzed": report.summary["test_cases_analyzed"],
        "mismatch_type_counts": report.summary["mismatch_type_counts"],
        "old_ref_type_counts": report.summary["old_ref_type_counts"],
        "tc_ref_type_counts": report.summary["tc_ref_type_counts"],
        "blocking_reasons_count": len(report.blocking_reasons),
        "warnings_count": len(report.warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
