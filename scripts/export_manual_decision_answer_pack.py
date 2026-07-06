from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.manual_decision_answer_pack import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_manual_decision_answer_pack,
    write_manual_decision_answer_pack,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a reviewer-friendly manual decision answer pack.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing Stage 9D artifacts.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to export.")
    args = parser.parse_args()

    work_dir = args.work_dir
    pack = build_manual_decision_answer_pack(
        package_id=args.package_id,
        template_path=work_dir / f"manual-decision-answer-template-{args.package_id}.json",
        matrix_path=work_dir / f"manual-decision-matrix-{args.package_id}.json",
        created_by_tool="scripts/export_manual_decision_answer_pack.py",
    )
    markdown_path, csv_path, schema_path = write_manual_decision_answer_pack(pack, work_dir)
    payload = {
        "answer_pack_status": pack.pack_status,
        "package_id": pack.package_id,
        "reviewer_rows_count": len(pack.reviewer_rows),
        "csv_path": str(csv_path),
        "markdown_path": str(markdown_path),
        "schema_path": str(schema_path),
        "xlsx_created": False,
        "canonical_write_allowed": pack.canonical_write_allowed,
        "manual_review_required": pack.manual_review_required,
        "stage_9e_authorized": pack.stage_9e_authorized,
        "warnings_count": len(pack.warnings),
        "blocking_reasons": pack.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
