from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.requirements_diff import (  # noqa: E402
    build_requirements_diff,
    write_requirements_diff,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build requirements diff artifacts for two Requirements Registry JSONL files."
    )
    parser.add_argument("--old-registry", required=True, type=Path, help="Old requirements.<version>.jsonl.")
    parser.add_argument("--new-registry", required=True, type=Path, help="New requirements.<version>.jsonl.")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for diff artifacts.")
    parser.add_argument("--old-summary", type=Path, help="Optional old requirements-summary.<version>.json.")
    parser.add_argument("--new-summary", type=Path, help="Optional new requirements-summary.<version>.json.")
    parser.add_argument(
        "--allow-duplicate-req-uid",
        action="store_true",
        help="Allow duplicate req_uid values after manual review.",
    )
    args = parser.parse_args()

    diff = build_requirements_diff(
        old_registry_path=args.old_registry,
        new_registry_path=args.new_registry,
        old_summary_path=args.old_summary,
        new_summary_path=args.new_summary,
        allow_duplicate_req_uid=args.allow_duplicate_req_uid,
        created_by_tool="scripts/build_requirements_diff.py",
    )
    diff_path, summary_path = write_requirements_diff(diff, args.out_dir)
    payload = {
        "diff_path": str(diff_path),
        "summary_path": str(summary_path),
        "diff_status": diff.summary["diff_status"],
        "entries_total": diff.summary["entries_total"],
        "requires_manual_review_count": diff.summary["requires_manual_review_count"],
        "warnings_count": len(diff.warnings),
        "blocking_reasons_count": len(diff.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
