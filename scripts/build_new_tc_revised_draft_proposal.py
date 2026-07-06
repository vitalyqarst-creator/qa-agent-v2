from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.new_tc_revised_draft_proposal import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_new_tc_revised_draft_proposal,
    write_new_tc_revised_draft_proposal,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 9E revised draft proposal artifacts.")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID)
    args = parser.parse_args()

    dirty = _git_status(args.test_cases_dir)
    if dirty:
        print(
            json.dumps(
                {
                    "proposal_status": "blocked",
                    "blocking_reasons": ["canonical test-cases directory is dirty"],
                    "dirty_files": dirty,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    work_dir = args.work_dir
    package_id = args.package_id
    proposal = build_new_tc_revised_draft_proposal(
        package_id=package_id,
        validation_path=work_dir / f"agent-decision-validation-{package_id}.json",
        resolution_path=work_dir / f"agent-decision-resolution-{package_id}.json",
        matrix_path=work_dir / f"manual-decision-matrix-{package_id}.json",
        draft_proposal_path=work_dir / f"new-tc-draft-proposal-{package_id}.json",
        draft_review_path=work_dir / f"new-tc-draft-review-{package_id}.json",
        draft_revision_plan_path=work_dir / f"new-tc-draft-revision-plan-{package_id}.json",
        decision_pack_path=work_dir / f"new-tc-revision-decision-pack-{package_id}.json",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{package_id}.json",
        residual_analysis_path=work_dir / f"residual-source-grounding-gap-analysis-{package_id}.json",
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_new_tc_revised_draft_proposal.py",
    )
    json_path, markdown_path = write_new_tc_revised_draft_proposal(proposal, work_dir)
    payload = {
        "proposal_path": str(json_path),
        "proposal_markdown_path": str(markdown_path),
        "proposal_status": proposal.proposal_status,
        "package_id": proposal.package_id,
        "stage_9e_scope": proposal.stage_9e_scope,
        "revised_draft_candidates_count": len(proposal.revised_draft_candidates),
        "blocked_draft_candidates_count": sum(
            1 for item in proposal.revised_draft_candidates if item.candidate_status == "blocked"
        ),
        "canonical_write_allowed": proposal.canonical_write_allowed,
        "manual_review_required": proposal.manual_review_required,
        "warnings_count": len(proposal.warnings),
        "blocking_reasons": proposal.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if proposal.proposal_status != "blocked" else 1


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
