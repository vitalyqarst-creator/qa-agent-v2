from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.completed_package_regression import (  # noqa: E402
    build_completed_package_regression,
    write_completed_package_regression,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate completed small package traceability updates without applying changes."
    )
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--update-plan", required=True, type=Path)
    parser.add_argument("--old-registry", required=True, type=Path)
    parser.add_argument("--new-registry", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--package-id", action="append", default=None, help="Completed package id. Repeatable.")
    args = parser.parse_args()

    report = build_completed_package_regression(
        work_dir=args.work_dir,
        test_cases_dir=args.test_cases_dir,
        update_plan_path=args.update_plan,
        old_registry_path=args.old_registry,
        new_registry_path=args.new_registry,
        package_ids=args.package_id,
        created_by_tool="scripts/validate_completed_package_regression.py",
    )
    json_path, markdown_path = write_completed_package_regression(report, args.out_dir)
    payload = {
        "completed_package_regression_json_path": str(json_path),
        "completed_package_regression_markdown_path": str(markdown_path),
        "regression_status": report.regression_status,
        "completed_packages_count": len(report.completed_packages),
        "validated_test_cases_count": len(report.validated_test_cases),
        "final_state_valid_count": report.final_state_valid_count,
        "safe_for_next_stage_count": report.safe_for_next_stage_count,
        "old_refs_absent": report.old_refs_absent,
        "new_refs_present": report.new_refs_present,
        "duplicate_req_refs_found": report.duplicate_req_refs_found,
        "regressions_found": report.regressions_found,
        "failed_checks": report.failed_checks,
        "warnings_count": len(report.warnings),
        "blocking_reasons": report.blocking_reasons,
        "changed_test_case_files": report.git_state_summary.get("changed_test_case_files", []),
        "cached_diff_empty": report.git_state_summary.get("cached_diff_empty"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
