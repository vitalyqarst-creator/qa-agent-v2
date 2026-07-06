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
    import_manual_decision_answer_pack,
    write_manual_decision_answer_pack_import_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import filled reviewer answer pack CSV into Stage 9D.7 answers JSON.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing Stage 9D artifacts.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to import.")
    parser.add_argument(
        "--filled-csv",
        type=Path,
        default=None,
        help="Filled reviewer CSV path. Defaults to work-dir/manual-decision-reviewer-answer-pack-<package>.filled.csv.",
    )
    args = parser.parse_args()

    work_dir = args.work_dir
    filled_csv = args.filled_csv or work_dir / f"manual-decision-reviewer-answer-pack-{args.package_id}.filled.csv"
    pack = build_manual_decision_answer_pack(
        package_id=args.package_id,
        template_path=work_dir / f"manual-decision-answer-template-{args.package_id}.json",
        matrix_path=work_dir / f"manual-decision-matrix-{args.package_id}.json",
        created_by_tool="scripts/import_manual_decision_answer_pack.py",
    )
    report = import_manual_decision_answer_pack(
        package_id=args.package_id,
        pack=pack,
        filled_csv_path=filled_csv,
        answers_output_path=work_dir / f"manual-decision-reviewer-answers-{args.package_id}.json",
        created_by_tool="scripts/import_manual_decision_answer_pack.py",
    )
    report_json, report_md = write_manual_decision_answer_pack_import_report(report, work_dir)
    payload = {
        "import_status": report.import_status,
        "package_id": report.package_id,
        "report_path": str(report_json),
        "report_markdown_path": str(report_md),
        "answers_output_path": report.answers_output_path,
        "rows_total": report.rows_total,
        "rows_with_answers": report.rows_with_answers,
        "rows_without_answers": report.rows_without_answers,
        "imported_answers_count": report.imported_answers_count,
        "canonical_write_allowed": report.canonical_write_allowed,
        "stage_9e_authorized": report.stage_9e_authorized,
        "warnings_count": len(report.warnings),
        "blocking_reasons": report.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
