from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.writer_dry_run_proposals import (  # noqa: E402
    build_writer_dry_run_proposal,
    write_writer_dry_run_proposal,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build one preview-only writer dry-run proposal from a writer package task."
    )
    parser.add_argument("--package-id", required=True, help="Allowed target package id, e.g. WPKG-000003.")
    parser.add_argument("--writer-package-task", required=True, type=Path, help="writer-package-task-<id>.md")
    parser.add_argument("--writer-package-tasks", required=True, type=Path, help="writer-package-tasks.<old>-to-<new>.json")
    parser.add_argument("--manual-update-packages", required=True, type=Path, help="manual-update-packages.<old>-to-<new>.json")
    parser.add_argument("--update-plan", required=True, type=Path, help="test-case-update-plan.<old>-to-<new>.json")
    parser.add_argument("--impact-report", required=True, type=Path, help="impact-report.<old>-to-<new>.json")
    parser.add_argument("--requirements-diff", required=True, type=Path, help="requirements-diff.<old>-to-<new>.json")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory.")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for proposal artifacts.")
    args = parser.parse_args()

    proposal = build_writer_dry_run_proposal(
        package_id=args.package_id,
        writer_package_tasks_path=args.writer_package_tasks,
        writer_package_task_path=args.writer_package_task,
        manual_update_packages_path=args.manual_update_packages,
        update_plan_path=args.update_plan,
        impact_report_path=args.impact_report,
        requirements_diff_path=args.requirements_diff,
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_writer_dry_run_proposal.py",
    )
    json_path, markdown_path, patch_path = write_writer_dry_run_proposal(proposal, args.out_dir)
    payload = {
        "writer_dry_run_proposal_json_path": str(json_path),
        "writer_dry_run_proposal_markdown_path": str(markdown_path),
        "writer_dry_run_proposal_patch_path": str(patch_path),
        "package_id": proposal.package_id,
        "proposal_status": proposal.proposal_status,
        "file_path": proposal.file_path,
        "affected_test_case_ids": proposal.affected_test_case_ids,
        "proposed_changes_count": len(proposal.proposed_changes),
        "risk_level": proposal.risk_level,
        "manual_review_required": proposal.manual_review_required,
        "sha256_before": proposal.sha256_before,
        "sha256_after": proposal.sha256_after,
        "warnings_count": len(proposal.warnings),
        "blocking_reasons_count": len(proposal.blocking_reasons),
        "missing_information_count": len(proposal.missing_information),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
