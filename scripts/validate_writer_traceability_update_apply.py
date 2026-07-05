from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.writer_traceability_post_apply_validation import (  # noqa: E402
    build_writer_traceability_post_apply_validation,
    write_writer_traceability_post_apply_validation,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the result of a controlled writer traceability update apply."
    )
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--apply-report", required=True, type=Path)
    parser.add_argument("--writer-proposal", required=True, type=Path)
    parser.add_argument("--writer-review", required=True, type=Path)
    parser.add_argument("--update-plan", required=True, type=Path)
    parser.add_argument("--old-registry", required=True, type=Path)
    parser.add_argument("--new-registry", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--artifact-suffix", help="Optional filename suffix, e.g. after-backfill.")
    args = parser.parse_args()

    report = build_writer_traceability_post_apply_validation(
        package_id=args.package_id,
        apply_report_path=args.apply_report,
        writer_proposal_path=args.writer_proposal,
        writer_review_path=args.writer_review,
        update_plan_path=args.update_plan,
        old_registry_path=args.old_registry,
        new_registry_path=args.new_registry,
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/validate_writer_traceability_update_apply.py",
    )
    json_path, markdown_path = write_writer_traceability_post_apply_validation(
        report,
        args.out_dir,
        artifact_suffix=args.artifact_suffix,
    )
    payload = {
        "writer_traceability_post_apply_validation_json_path": str(json_path),
        "writer_traceability_post_apply_validation_markdown_path": str(markdown_path),
        "package_id": report.package_id,
        "validation_status": report.validation_status,
        "safe_to_commit": report.safe_to_commit,
        "file_path": report.file_path,
        "affected_test_case_ids": report.affected_test_case_ids,
        "failed_checks": report.failed_checks,
        "warnings_count": len(report.warnings),
        "blocking_reasons": report.blocking_reasons,
        "changed_test_case_files_count": len(report.git_state.get("changed_test_case_files", [])),
        "changed_test_case_files": report.git_state.get("changed_test_case_files", []),
        "target_diff_hunk_count": report.git_state.get("target_diff_hunk_count"),
        "cached_diff_empty": report.git_state.get("cached_diff_empty"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
