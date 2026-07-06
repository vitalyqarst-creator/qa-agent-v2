from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.new_tc_draft_review import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_new_tc_draft_review,
    write_new_tc_draft_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a draft-only new TC proposal.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing pipeline artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory, read-only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to review.")
    parser.add_argument("--old-version", default="autofin-prefinal", help="Old source version slug.")
    parser.add_argument("--new-version", default="autofin-final", help="New source version slug.")
    args = parser.parse_args()

    work_dir = args.work_dir
    pair = f"{args.old_version}-to-{args.new_version}"
    report = build_new_tc_draft_review(
        package_id=args.package_id,
        draft_proposal_path=work_dir / f"new-tc-draft-proposal-{args.package_id}.json",
        draft_proposal_markdown_path=work_dir / f"new-tc-draft-proposal-{args.package_id}.md",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.json",
        context_bundle_markdown_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.md",
        manual_update_packages_path=work_dir / f"manual-update-packages.{pair}.json",
        writer_package_tasks_path=work_dir / f"writer-package-tasks.{pair}.json",
        update_plan_path=work_dir / f"test-case-update-plan.{pair}.json",
        impact_report_path=work_dir / f"impact-report.{pair}.json",
        requirements_diff_path=work_dir / f"requirements-diff.{pair}.json",
        old_registry_path=work_dir / f"requirements.{args.old_version}.jsonl",
        new_registry_path=work_dir / f"requirements.{args.new_version}.jsonl",
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/review_new_tc_draft_proposal.py",
    )
    json_path, markdown_path = write_new_tc_draft_review(report, work_dir)
    payload = {
        "review_path": str(json_path),
        "review_markdown_path": str(markdown_path),
        "review_status": report.review_status,
        "safe_for_controlled_create_apply": report.safe_for_controlled_create_apply,
        "canonical_write_allowed": report.canonical_write_allowed,
        "manual_review_required": report.manual_review_required,
        "drafts_total": report.drafts_total,
        "approved_drafts_count": report.approved_drafts_count,
        "drafts_requiring_revision_count": report.drafts_requiring_revision_count,
        "deferred_drafts_count": report.deferred_drafts_count,
        "rejected_drafts_count": report.rejected_drafts_count,
        "duplicate_risk_summary": report.duplicate_risk_summary,
        "failed_checks": report.failed_checks,
        "warnings_count": len(report.warnings),
        "blocking_reasons": report.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
