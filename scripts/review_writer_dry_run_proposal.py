from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.writer_proposal_review import (  # noqa: E402
    build_writer_proposal_review,
    write_writer_proposal_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a writer dry-run traceability update proposal before controlled apply."
    )
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--writer-proposal", required=True, type=Path)
    parser.add_argument("--writer-proposal-md", type=Path)
    parser.add_argument("--writer-proposal-patch", type=Path)
    parser.add_argument("--update-plan", required=True, type=Path)
    parser.add_argument("--impact-report", required=True, type=Path)
    parser.add_argument("--requirements-diff", required=True, type=Path)
    parser.add_argument("--old-registry", required=True, type=Path)
    parser.add_argument("--new-registry", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--artifact-suffix", help="Optional filename suffix, e.g. after-backfill.")
    parser.add_argument("--expected-tc-id", action="append", default=None, help="Expected affected TC id. Repeatable.")
    args = parser.parse_args()

    report = build_writer_proposal_review(
        package_id=args.package_id,
        writer_proposal_path=args.writer_proposal,
        writer_proposal_markdown_path=args.writer_proposal_md,
        writer_proposal_patch_path=args.writer_proposal_patch,
        update_plan_path=args.update_plan,
        impact_report_path=args.impact_report,
        requirements_diff_path=args.requirements_diff,
        old_registry_path=args.old_registry,
        new_registry_path=args.new_registry,
        test_cases_dir=args.test_cases_dir,
        expected_affected_test_case_ids=args.expected_tc_id,
        created_by_tool="scripts/review_writer_dry_run_proposal.py",
    )
    json_path, markdown_path = write_writer_proposal_review(
        report,
        args.out_dir,
        artifact_suffix=args.artifact_suffix,
    )
    payload = {
        "writer_proposal_review_json_path": str(json_path),
        "writer_proposal_review_markdown_path": str(markdown_path),
        "package_id": report.package_id,
        "review_status": report.review_status,
        "safe_for_controlled_apply": report.safe_for_controlled_apply,
        "failed_checks": report.failed_checks,
        "warnings_count": len(report.warnings),
        "risk_level": report.risk_level,
        "blocking_reasons_count": len(report.blocking_reasons),
        "git_status_short_empty": report.git_state.get("status_short_empty"),
        "git_diff_empty": report.git_state.get("diff_empty"),
        "git_cached_diff_empty": report.git_state.get("cached_diff_empty"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
