from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.new_tc_stage_9h_design_review_prep import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_new_tc_stage_9h_design_review_prep,
    write_new_tc_stage_9h_design_review_prep,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 9H design/review preparation report.")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID)
    args = parser.parse_args()

    dirty = _git_status(args.test_cases_dir)
    if dirty:
        print(json.dumps({"prep_status": "blocked", "git_status_test_cases": dirty}, ensure_ascii=False, indent=2))
        return 2

    report = build_new_tc_stage_9h_design_review_prep(
        package_id=args.package_id,
        stage_9g_json_path=args.work_dir / f"new-tc-create-apply-dry-run-{args.package_id}.json",
        stage_9g_markdown_path=args.work_dir / f"new-tc-create-apply-dry-run-{args.package_id}.md",
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_new_tc_stage_9h_design_review_prep.py",
    )
    json_path, md_path = write_new_tc_stage_9h_design_review_prep(report, args.work_dir)
    print(
        json.dumps(
            {
                "prep_path": str(json_path),
                "prep_markdown_path": str(md_path),
                "prep_status": report.prep_status,
                "readiness_verdict": report.readiness_verdict,
                "warning_reviews_total": len(report.warning_reviews),
                "item_readiness_total": len(report.item_readiness_reviews),
                "target_file_plan_review_status": report.target_file_plan_review.get("status"),
                "tc_id_collision_review_status": report.tc_id_collision_review.get("status"),
                "aggregate_target_risk_review_status": report.aggregate_target_risk_review.get("status"),
                "safety_gate_status": report.safety_gate_summary.get("status"),
                "real_apply_authorized": report.real_apply_authorized,
                "canonical_write_allowed": report.canonical_write_allowed,
                "blocking_reasons": report.blocking_reasons,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report.prep_status != "blocked" else 2


def _git_status(path: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--", str(path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return [result.stderr.strip() or "git status failed"]
    return [line for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
