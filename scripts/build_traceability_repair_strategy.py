from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.traceability_repair_strategy import (  # noqa: E402
    build_traceability_repair_strategy,
    write_traceability_repair_strategy,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a traceability repair strategy from Stage 7D mismatch diagnostics."
    )
    parser.add_argument("--diagnostics", required=True, type=Path)
    parser.add_argument(
        "--proposal",
        action="append",
        required=True,
        type=Path,
        help="writer-dry-run-proposal-<package-id>.json; repeatable.",
    )
    parser.add_argument("--update-plan", required=True, type=Path)
    parser.add_argument("--impact-report", required=True, type=Path)
    parser.add_argument("--requirements-diff", required=True, type=Path)
    parser.add_argument("--old-registry", required=True, type=Path)
    parser.add_argument("--new-registry", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    report = build_traceability_repair_strategy(
        diagnostics_path=args.diagnostics,
        proposal_paths=args.proposal,
        update_plan_path=args.update_plan,
        impact_report_path=args.impact_report,
        requirements_diff_path=args.requirements_diff,
        old_registry_path=args.old_registry,
        new_registry_path=args.new_registry,
        created_by_tool="scripts/build_traceability_repair_strategy.py",
    )
    json_path, markdown_path = write_traceability_repair_strategy(report, args.out_dir)
    payload = {
        "traceability_repair_strategy_json_path": str(json_path),
        "traceability_repair_strategy_markdown_path": str(markdown_path),
        "strategy_status": report.strategy_status,
        "recommended_strategy": report.recommended_strategy,
        "automatic_replacement_allowed": report.automatic_replacement_allowed,
        "backfill_recommended": report.backfill_recommended,
        "source_req_id_fallback_recommended": report.source_req_id_fallback_recommended,
        "repair_items_total": report.summary["repair_items_total"],
        "confidence_counts": report.summary["confidence_counts"],
        "allowed_next_action_counts": report.summary["allowed_next_action_counts"],
        "blocking_reasons_count": len(report.blocking_reasons),
        "warnings_count": len(report.warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
