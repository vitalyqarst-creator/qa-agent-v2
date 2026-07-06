from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.new_tc_draft_revision_plan import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_new_tc_draft_revision_plan,
    write_new_tc_draft_revision_plan,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a planning-only new TC draft revision plan.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing pipeline artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory, read-only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to plan.")
    parser.add_argument("--old-version", default="autofin-prefinal", help="Old source version slug.")
    parser.add_argument("--new-version", default="autofin-final", help="New source version slug.")
    args = parser.parse_args()

    work_dir = args.work_dir
    pair = f"{args.old_version}-to-{args.new_version}"
    plan = build_new_tc_draft_revision_plan(
        package_id=args.package_id,
        draft_proposal_path=work_dir / f"new-tc-draft-proposal-{args.package_id}.json",
        draft_proposal_markdown_path=work_dir / f"new-tc-draft-proposal-{args.package_id}.md",
        draft_review_path=work_dir / f"new-tc-draft-review-{args.package_id}.json",
        draft_review_markdown_path=work_dir / f"new-tc-draft-review-{args.package_id}.md",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.json",
        context_bundle_markdown_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.md",
        requirements_diff_path=work_dir / f"requirements-diff.{pair}.json",
        impact_report_path=work_dir / f"impact-report.{pair}.json",
        update_plan_path=work_dir / f"test-case-update-plan.{pair}.json",
        old_registry_path=work_dir / f"requirements.{args.old_version}.jsonl",
        new_registry_path=work_dir / f"requirements.{args.new_version}.jsonl",
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_new_tc_draft_revision_plan.py",
    )
    json_path, markdown_path = write_new_tc_draft_revision_plan(plan, work_dir)
    payload = {
        "revision_plan_path": str(json_path),
        "revision_plan_markdown_path": str(markdown_path),
        "plan_status": plan.plan_status,
        "package_id": plan.package_id,
        "revision_items_total": plan.revision_summary.get("revision_items_total", 0),
        "revise_count": plan.revision_summary.get("revise_count", 0),
        "replace_count": plan.revision_summary.get("replace_count", 0),
        "defer_count": plan.revision_summary.get("defer_count", 0),
        "keep_rejected_count": plan.revision_summary.get("keep_rejected_count", 0),
        "duplicate_risk_actions_count": plan.revision_summary.get("duplicate_risk_actions_count", 0),
        "source_grounding_actions_count": plan.revision_summary.get("source_grounding_actions_count", 0),
        "ready_for_revised_draft_proposal": plan.ready_for_revised_draft_proposal,
        "canonical_write_allowed": plan.canonical_write_allowed,
        "manual_review_required": plan.manual_review_required,
        "warnings_count": len(plan.warnings),
        "blocking_reasons": plan.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
