from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.new_tc_draft_proposals import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_new_tc_draft_proposal,
    write_new_tc_draft_proposal,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a draft-only new TC proposal from a create-new-TC context bundle."
    )
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing pipeline artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory, read-only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to draft.")
    parser.add_argument("--old-version", default="autofin-prefinal", help="Old source version slug.")
    parser.add_argument("--new-version", default="autofin-final", help="New source version slug.")
    args = parser.parse_args()

    work_dir = args.work_dir
    pair = f"{args.old_version}-to-{args.new_version}"
    proposal = build_new_tc_draft_proposal(
        package_id=args.package_id,
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.json",
        test_cases_dir=args.test_cases_dir,
        manual_update_packages_path=work_dir / f"manual-update-packages.{pair}.json",
        writer_package_tasks_path=work_dir / f"writer-package-tasks.{pair}.json",
        update_plan_path=work_dir / f"test-case-update-plan.{pair}.json",
        impact_report_path=work_dir / f"impact-report.{pair}.json",
        requirements_diff_path=work_dir / f"requirements-diff.{pair}.json",
        old_registry_path=work_dir / f"requirements.{args.old_version}.jsonl",
        new_registry_path=work_dir / f"requirements.{args.new_version}.jsonl",
        created_by_tool="scripts/build_new_tc_draft_proposal.py",
    )
    json_path, markdown_path = write_new_tc_draft_proposal(proposal, work_dir)
    payload = {
        "proposal_path": str(json_path),
        "proposal_markdown_path": str(markdown_path),
        "proposal_status": proposal.proposal_status,
        "package_id": proposal.package_id,
        "package_type": proposal.package_type,
        "draft_test_case_count": len(proposal.draft_test_cases),
        "deferred_group_count": len(proposal.deferred_groups),
        "duplicate_risk_decision_count": len(proposal.duplicate_risk_decisions),
        "manual_review_required": proposal.manual_review_required,
        "canonical_write_allowed": proposal.canonical_write_allowed,
        "warnings_count": len(proposal.warnings),
        "blocking_reasons": proposal.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
