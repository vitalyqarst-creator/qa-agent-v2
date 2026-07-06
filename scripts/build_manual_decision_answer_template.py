from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.manual_decision_answer_validation import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_manual_decision_answer_template,
    write_manual_decision_answer_template,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a reviewer answer template from a manual decision matrix.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing Stage 9D artifacts.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to process.")
    args = parser.parse_args()

    work_dir = args.work_dir
    template = build_manual_decision_answer_template(
        package_id=args.package_id,
        matrix_path=work_dir / f"manual-decision-matrix-{args.package_id}.json",
        created_by_tool="scripts/build_manual_decision_answer_template.py",
    )
    json_path, markdown_path = write_manual_decision_answer_template(template, work_dir)
    payload = {
        "answer_template_path": str(json_path),
        "answer_template_markdown_path": str(markdown_path),
        "answer_template_status": template.template_status,
        "package_id": template.package_id,
        "answer_rows_total": len(template.reviewer_rows),
        "canonical_write_allowed": template.canonical_write_allowed,
        "manual_review_required": template.manual_review_required,
        "stage_9e_authorized": template.stage_9e_authorized,
        "warnings_count": len(template.warnings),
        "blocking_reasons": template.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
