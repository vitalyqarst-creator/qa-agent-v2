from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.agent_decision_validation import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_agent_decision_validation_report,
    write_agent_decision_validation_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage 9D.8 agent decision resolution and harden Stage 9E gate.")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID)
    args = parser.parse_args()

    dirty = _git_status(args.test_cases_dir)
    if dirty:
        print(
            json.dumps(
                {
                    "validation_status": "blocked",
                    "blocking_reasons": [
                        "canonical test-cases directory is dirty; run dirty attribution before Stage 9D.9"
                    ],
                    "dirty_files": dirty,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    work_dir = args.work_dir
    package_id = args.package_id
    report = build_agent_decision_validation_report(
        package_id=package_id,
        resolution_path=work_dir / f"agent-decision-resolution-{package_id}.json",
        matrix_path=work_dir / f"manual-decision-matrix-{package_id}.json",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{package_id}.json",
        draft_proposal_path=work_dir / f"new-tc-draft-proposal-{package_id}.json",
        decision_pack_path=work_dir / f"new-tc-revision-decision-pack-{package_id}.json",
        residual_analysis_path=work_dir / f"residual-source-grounding-gap-analysis-{package_id}.json",
        created_by_tool="scripts/validate_agent_decision_resolution.py",
    )
    json_path, md_path = write_agent_decision_validation_report(report, work_dir)
    payload = {
        "validation_path": str(json_path),
        "validation_markdown_path": str(md_path),
        "validation_status": report.validation_status,
        "stage_9e_allowed": report.stage_9e_gate_hardened.get("stage_9e_allowed"),
        "validated_stage_9e_scope": report.validated_stage_9e_scope,
        "rejected_stage_9e_scope": report.rejected_stage_9e_scope,
        "canonical_write_allowed": report.canonical_write_allowed,
        "manual_review_required": report.manual_review_required,
        "warnings_count": len(report.warnings),
        "blocking_reasons": report.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


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
