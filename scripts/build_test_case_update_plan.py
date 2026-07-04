from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.test_case_update_plan import (  # noqa: E402
    build_test_case_update_plan,
    write_test_case_update_plan,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build test-case update plan artifacts from an impact report."
    )
    parser.add_argument("--impact-report", required=True, type=Path, help="impact-report.<old>-to-<new>.json")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="fts/<ft-slug>/test-cases directory")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for update plan artifacts.")
    parser.add_argument("--impact-summary", type=Path, help="Optional impact-report-summary JSON path.")
    args = parser.parse_args()

    plan = build_test_case_update_plan(
        impact_report_path=args.impact_report,
        impact_summary_path=args.impact_summary,
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_test_case_update_plan.py",
    )
    plan_path, summary_path, markdown_path = write_test_case_update_plan(plan, args.out_dir)
    payload = {
        "test_case_update_plan_path": str(plan_path),
        "test_case_update_plan_summary_path": str(summary_path),
        "test_case_update_plan_markdown_path": str(markdown_path),
        "plan_status": plan.summary["plan_status"],
        "plan_items_total": plan.summary["plan_items_total"],
        "safe_auto_candidates_count": plan.summary["safe_auto_candidates_count"],
        "manual_only_count": plan.summary["manual_only_count"],
        "blocked_items_count": plan.summary["blocked_items_count"],
        "warnings_count": len(plan.warnings),
        "blocking_reasons_count": len(plan.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
