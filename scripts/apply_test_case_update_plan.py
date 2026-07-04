from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.test_case_update_apply import (  # noqa: E402
    apply_test_case_update_plan,
    write_test_case_update_apply_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or apply safe traceability-only updates from a test-case update plan."
    )
    parser.add_argument("--update-plan", required=True, type=Path, help="test-case-update-plan.<old>-to-<new>.json")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="fts/<ft-slug>/test-cases directory")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for apply report artifacts.")
    parser.add_argument("--update-plan-summary", type=Path, help="Optional test-case-update-plan-summary JSON path.")
    parser.add_argument("--backup-dir", type=Path, help="Optional backup directory. Defaults to <out-dir>/backups.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write safe traceability-only updates. Omit for dry-run preview.",
    )
    args = parser.parse_args()

    report = apply_test_case_update_plan(
        update_plan_path=args.update_plan,
        update_plan_summary_path=args.update_plan_summary,
        test_cases_dir=args.test_cases_dir,
        out_dir=args.out_dir,
        backup_dir=args.backup_dir,
        dry_run=not args.apply,
        created_by_tool="scripts/apply_test_case_update_plan.py",
    )
    report_path, summary_path, markdown_path = write_test_case_update_apply_report(report, args.out_dir)
    payload = {
        "test_case_update_apply_report_path": str(report_path),
        "test_case_update_apply_summary_path": str(summary_path),
        "test_case_update_apply_markdown_path": str(markdown_path),
        "apply_status": report.summary["apply_status"],
        "dry_run": report.dry_run,
        "apply_items_total": report.summary["apply_items_total"],
        "previewed": report.summary["previewed"],
        "applied": report.summary["applied"],
        "skipped_noop": report.summary["skipped_noop"],
        "skipped_manual_only": report.summary["skipped_manual_only"],
        "skipped_blocked": report.summary["skipped_blocked"],
        "skipped_unsafe": report.summary["skipped_unsafe"],
        "failed": report.summary["failed"],
        "files_changed_count": report.summary["files_changed_count"],
        "warnings_count": len(report.warnings),
        "blocking_reasons_count": len(report.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
