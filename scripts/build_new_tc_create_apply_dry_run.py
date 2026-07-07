from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.new_tc_create_apply_dry_run import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_new_tc_create_apply_dry_run,
    write_new_tc_create_apply_dry_run,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 9G controlled create apply dry-run design.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing pipeline artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory, read-only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to process.")
    args = parser.parse_args()

    dirty = _git_status(args.test_cases_dir)
    if dirty:
        print(
            json.dumps(
                {
                    "dry_run_status": "blocked",
                    "blocking_reasons": ["canonical test-cases directory is dirty"],
                    "git_status_test_cases": dirty,
                    "recommended_next_action": "Run dirty attribution before Stage 9G.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    work_dir = args.work_dir
    report = build_new_tc_create_apply_dry_run(
        package_id=args.package_id,
        revised_proposal_path=work_dir / f"new-tc-revised-draft-proposal-{args.package_id}.json",
        revised_review_path=work_dir / f"new-tc-revised-draft-review-{args.package_id}.json",
        validation_path=work_dir / f"agent-decision-validation-{args.package_id}.json",
        resolution_path=work_dir / f"agent-decision-resolution-{args.package_id}.json",
        matrix_path=work_dir / f"manual-decision-matrix-{args.package_id}.json",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.json",
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_new_tc_create_apply_dry_run.py",
    )
    json_path, markdown_path = write_new_tc_create_apply_dry_run(report, work_dir)
    counts = _decision_counts(report)
    print(
        json.dumps(
            {
                "dry_run_path": str(json_path),
                "dry_run_markdown_path": str(markdown_path),
                "dry_run_status": report.dry_run_status,
                "dry_run_items_total": len(report.dry_run_items),
                **counts,
                "target_file_plan_summary": report.target_file_plan.get("planned_strategy_counts", {}),
                "tc_id_collision_summary": {
                    "duplicate_proposed_tc_ids": report.tc_id_plan.get("duplicate_proposed_tc_ids", []),
                    "existing_tc_id_collision_count": report.tc_id_plan.get("existing_tc_id_collision_count", 0),
                },
                "aggregate_file_target_risks": [
                    check for check in report.collision_checks if check.get("check_id") == "aggregate_target_risks"
                ],
                "stage_9h_readiness": report.stage_9h_readiness,
                "real_apply_authorized": report.real_apply_authorized,
                "canonical_write_allowed": report.canonical_write_allowed,
                "warnings_count": len(report.warnings),
                "blocking_reasons": report.blocking_reasons,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report.dry_run_status != "blocked" else 2


def _decision_counts(report) -> dict[str, int]:
    counts: dict[str, int] = {
        "dry_run_allowed_count": 0,
        "dry_run_allowed_with_warnings_count": 0,
        "blocked_count": 0,
    }
    for item in report.dry_run_items:
        key = f"{item.dry_run_decision}_count"
        counts[key] = counts.get(key, 0) + 1
    return counts


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
