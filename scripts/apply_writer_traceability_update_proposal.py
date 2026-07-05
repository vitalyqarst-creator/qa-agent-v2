from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.writer_traceability_update_apply import (  # noqa: E402
    apply_writer_traceability_update_proposal,
    write_writer_traceability_update_apply_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Controlled apply for reviewed writer traceability update proposals."
    )
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--writer-proposal", required=True, type=Path)
    parser.add_argument("--writer-review", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--artifact-suffix", help="Optional filename/backup suffix, e.g. after-backfill.")
    parser.add_argument("--apply", action="store_true", help="Actually write canonical test-case files.")
    parser.add_argument(
        "--ack-warnings",
        action="store_true",
        help="Required for real apply when review_status=approved-with-warnings.",
    )
    args = parser.parse_args()

    report = apply_writer_traceability_update_proposal(
        package_id=args.package_id,
        writer_proposal_path=args.writer_proposal,
        writer_review_path=args.writer_review,
        test_cases_dir=args.test_cases_dir,
        out_dir=args.out_dir,
        dry_run=not args.apply,
        ack_warnings=args.ack_warnings,
        artifact_suffix=args.artifact_suffix,
        created_by_tool="scripts/apply_writer_traceability_update_proposal.py",
    )
    json_path, markdown_path = write_writer_traceability_update_apply_report(
        report,
        args.out_dir,
        artifact_suffix=args.artifact_suffix,
    )
    payload = {
        "writer_traceability_update_apply_json_path": str(json_path),
        "writer_traceability_update_apply_markdown_path": str(markdown_path),
        "package_id": report.package_id,
        "apply_status": report.apply_status,
        "dry_run": report.dry_run,
        "file_path": report.file_path,
        "affected_test_case_ids": report.affected_test_case_ids,
        "applied_changes_count": len(report.applied_changes),
        "previewed_changes_count": len(report.previewed_changes),
        "skipped_changes_count": len(report.skipped_changes),
        "files_changed_count": report.files_changed_count,
        "backup_path": report.backup_path,
        "sha256_before": report.sha256_before,
        "sha256_after": report.sha256_after,
        "blocking_reasons": report.blocking_reasons,
        "warnings_count": len(report.warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
