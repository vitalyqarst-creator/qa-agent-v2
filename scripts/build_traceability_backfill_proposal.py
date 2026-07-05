from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.traceability_backfill_proposals import (  # noqa: E402
    build_traceability_backfill_proposal,
    write_traceability_backfill_proposal,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a preview-only traceability backfill proposal for one writer package."
    )
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--repair-strategy", required=True, type=Path)
    parser.add_argument("--diagnostics", required=True, type=Path)
    parser.add_argument(
        "--proposal",
        action="append",
        required=True,
        type=Path,
        help="writer-dry-run-proposal-<package-id>.json; repeatable.",
    )
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    proposal = build_traceability_backfill_proposal(
        package_id=args.package_id,
        repair_strategy_path=args.repair_strategy,
        diagnostics_path=args.diagnostics,
        proposal_paths=args.proposal,
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_traceability_backfill_proposal.py",
    )
    json_path, markdown_path, patch_path = write_traceability_backfill_proposal(proposal, args.out_dir)
    payload = {
        "traceability_backfill_proposal_json_path": str(json_path),
        "traceability_backfill_proposal_markdown_path": str(markdown_path),
        "traceability_backfill_proposal_patch_path": str(patch_path),
        "package_id": proposal.package_id,
        "proposal_status": proposal.proposal_status,
        "file_path": proposal.file_path,
        "affected_test_case_ids": proposal.affected_test_case_ids,
        "backfill_changes_count": len(proposal.backfill_changes),
        "added_req_uids": sorted({
            req_uid
            for change in proposal.backfill_changes
            for req_uid in change.added_req_uids
        }),
        "risk_level": proposal.risk_level,
        "manual_review_required": proposal.manual_review_required,
        "sha256_before": proposal.sha256_before,
        "sha256_after": proposal.sha256_after,
        "blocking_reasons_count": len(proposal.blocking_reasons),
        "warnings_count": len(proposal.warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
