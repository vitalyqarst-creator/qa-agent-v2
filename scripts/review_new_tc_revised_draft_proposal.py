from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.new_tc_revised_draft_review import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_new_tc_revised_draft_review,
    write_new_tc_revised_draft_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a Stage 9E revised draft-only new TC proposal.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing pipeline artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory, read-only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to review.")
    args = parser.parse_args()

    dirty = _git_status(args.test_cases_dir)
    if dirty:
        print(
            json.dumps(
                {
                    "review_status": "blocked",
                    "blocking_reasons": ["canonical test-cases directory is dirty"],
                    "git_status_test_cases": dirty,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    work_dir = args.work_dir
    report = build_new_tc_revised_draft_review(
        package_id=args.package_id,
        revised_proposal_path=work_dir / f"new-tc-revised-draft-proposal-{args.package_id}.json",
        validation_path=work_dir / f"agent-decision-validation-{args.package_id}.json",
        source_draft_proposal_path=work_dir / f"new-tc-draft-proposal-{args.package_id}.json",
        created_by_tool="scripts/review_new_tc_revised_draft_proposal.py",
    )
    json_path, markdown_path = write_new_tc_revised_draft_review(report, work_dir)
    counts = _review_counts(report)
    print(
        json.dumps(
            {
                "review_path": str(json_path),
                "review_markdown_path": str(markdown_path),
                "review_status": report.review_status,
                "draft_reviews_total": len(report.draft_reviews),
                **counts,
                "canonical_write_allowed": report.canonical_write_allowed,
                "manual_review_required": report.manual_review_required,
                "stage_9g_readiness": report.stage_9g_readiness,
                "warnings_count": len(report.warnings),
                "blocking_reasons": report.blocking_reasons,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report.review_status != "blocked" else 2


def _review_counts(report) -> dict[str, int]:
    counts: dict[str, int] = {}
    for review in report.draft_reviews:
        key = f"{review.review_result}_count".replace("-", "_")
        counts[key] = counts.get(key, 0) + 1
    for key in (
        "approved_count",
        "approved_with_warnings_count",
        "needs_revision_count",
        "rejected_count",
    ):
        counts.setdefault(key, 0)
    return counts


def _git_status(path: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--", str(path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return [result.stderr.strip() or "git status failed"]
    return [line for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
