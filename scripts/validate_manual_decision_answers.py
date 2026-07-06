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
    validate_manual_decision_answers,
    write_manual_decision_answer_validation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate reviewer answers for a manual decision matrix.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing Stage 9D artifacts.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to process.")
    parser.add_argument(
        "--answers",
        type=Path,
        default=None,
        help="Optional reviewer answers JSON path. Defaults to work-dir/manual-decision-reviewer-answers-<package>.json.",
    )
    args = parser.parse_args()

    work_dir = args.work_dir
    answers_path = args.answers or work_dir / f"manual-decision-reviewer-answers-{args.package_id}.json"
    validation = validate_manual_decision_answers(
        package_id=args.package_id,
        matrix_path=work_dir / f"manual-decision-matrix-{args.package_id}.json",
        answers_path=answers_path,
        created_by_tool="scripts/validate_manual_decision_answers.py",
    )
    json_path, markdown_path = write_manual_decision_answer_validation(validation, work_dir)
    payload = {
        "answer_validation_path": str(json_path),
        "answer_validation_markdown_path": str(markdown_path),
        "validation_status": validation.validation_status,
        "package_id": validation.package_id,
        "answer_rows_total": validation.answer_rows_total,
        "answer_rows_valid": validation.answer_rows_valid,
        "answer_rows_missing": validation.answer_rows_missing,
        "answer_rows_rejected": validation.answer_rows_rejected,
        "unsafe_answers_count": len(validation.unsafe_answers),
        "stage_9e_allowed": validation.stage_9e_gate.stage_9e_allowed,
        "can_prepare_stage_9e_draft_only": validation.readiness_after_answers.can_prepare_stage_9e_draft_only,
        "canonical_write_allowed": validation.canonical_write_allowed,
        "manual_review_required": validation.manual_review_required,
        "warnings_count": len(validation.warnings),
        "blocking_reasons": validation.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
