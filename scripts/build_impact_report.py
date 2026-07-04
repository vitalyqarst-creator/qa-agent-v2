from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.impact_analysis import (  # noqa: E402
    build_impact_report,
    write_impact_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build impact report artifacts from a requirements diff and existing test cases."
    )
    parser.add_argument("--requirements-diff", required=True, type=Path, help="requirements-diff.<old>-to-<new>.json")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="fts/<ft-slug>/test-cases directory")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for impact artifacts.")
    parser.add_argument("--requirements-diff-summary", type=Path, help="Optional requirements-diff-summary JSON path.")
    parser.add_argument(
        "--allow-empty-test-cases",
        action="store_true",
        help="Allow building a source-only report when no TC blocks are parsed.",
    )
    args = parser.parse_args()

    report = build_impact_report(
        requirements_diff_path=args.requirements_diff,
        requirements_diff_summary_path=args.requirements_diff_summary,
        test_cases_dir=args.test_cases_dir,
        allow_empty_test_cases=args.allow_empty_test_cases,
        created_by_tool="scripts/build_impact_report.py",
    )
    report_path, summary_path, markdown_path = write_impact_report(report, args.out_dir)
    payload = {
        "impact_report_path": str(report_path),
        "impact_summary_path": str(summary_path),
        "impact_markdown_path": str(markdown_path),
        "impact_status": report.summary["impact_status"],
        "impact_entries_total": report.summary["impact_entries_total"],
        "affected_test_cases_count": report.summary["affected_test_cases_count"],
        "requires_manual_review_count": report.summary["requires_manual_review_count"],
        "warnings_count": len(report.warnings),
        "blocking_reasons_count": len(report.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
