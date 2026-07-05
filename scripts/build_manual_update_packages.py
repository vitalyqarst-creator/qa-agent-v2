from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.manual_update_packages import (  # noqa: E402
    build_manual_update_packages,
    write_manual_update_packages,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build manual update work packages from a test-case update plan."
    )
    parser.add_argument("--update-plan", required=True, type=Path, help="test-case-update-plan.<old>-to-<new>.json")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for package artifacts.")
    args = parser.parse_args()

    report = build_manual_update_packages(
        update_plan_path=args.update_plan,
        created_by_tool="scripts/build_manual_update_packages.py",
    )
    report_path, summary_path, markdown_path = write_manual_update_packages(report, args.out_dir)
    payload = {
        "manual_update_packages_path": str(report_path),
        "manual_update_packages_summary_path": str(summary_path),
        "manual_update_packages_markdown_path": str(markdown_path),
        "package_status": report.summary["package_status"],
        "packages_total": report.summary["packages_total"],
        "files_affected_count": report.summary["files_affected_count"],
        "test_cases_affected_count": report.summary["test_cases_affected_count"],
        "create_new_candidate_count": report.summary["create_new_candidate_count"],
        "mark_deprecated_candidate_count": report.summary["mark_deprecated_candidate_count"],
        "update_existing_count": report.summary["update_existing_count"],
        "manual_review_count": report.summary["manual_review_count"],
        "mixed_package_count": report.summary["mixed_package_count"],
        "warnings_count": len(report.warnings),
        "blocking_reasons_count": len(report.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
