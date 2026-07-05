from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.traceability_backfill_review import (  # noqa: E402
    build_traceability_backfill_review,
    write_traceability_backfill_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a preview-only traceability backfill proposal before controlled apply."
    )
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--backfill-proposal", required=True, type=Path)
    parser.add_argument("--repair-strategy", required=True, type=Path)
    parser.add_argument("--diagnostics", required=True, type=Path)
    parser.add_argument("--old-registry", required=True, type=Path)
    parser.add_argument("--new-registry", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    report = build_traceability_backfill_review(
        package_id=args.package_id,
        backfill_proposal_path=args.backfill_proposal,
        repair_strategy_path=args.repair_strategy,
        diagnostics_path=args.diagnostics,
        old_registry_path=args.old_registry,
        new_registry_path=args.new_registry,
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/review_traceability_backfill_proposal.py",
    )
    json_path, markdown_path = write_traceability_backfill_review(report, args.out_dir)
    payload = {
        "traceability_backfill_review_json_path": str(json_path),
        "traceability_backfill_review_markdown_path": str(markdown_path),
        "package_id": report.package_id,
        "review_status": report.review_status,
        "safe_for_controlled_apply": report.safe_for_controlled_apply,
        "failed_checks": report.failed_checks,
        "warnings_count": len(report.warnings),
        "risk_level": report.risk_level,
        "blocking_reasons_count": len(report.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
