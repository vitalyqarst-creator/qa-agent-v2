from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.agent_decision_resolver import (  # noqa: E402
    DEFAULT_BENCHMARK_NAME,
    DEFAULT_PACKAGE_ID,
    build_agent_decision_resolution,
    write_agent_decision_resolution,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 9D.8 agent decision resolution artifacts.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing Stage 9D artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory for preflight only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to resolve.")
    parser.add_argument("--benchmark-name", default=DEFAULT_BENCHMARK_NAME, help="Benchmark label.")
    args = parser.parse_args()

    dirty = _git_status(args.test_cases_dir)
    if dirty:
        payload = {
            "resolution_status": "blocked",
            "blocking_reasons": ["canonical test-cases directory is dirty; rerun Stage 9D.2a before Stage 9D.8"],
            "dirty_files": dirty,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    work_dir = args.work_dir
    package_id = args.package_id
    resolution = build_agent_decision_resolution(
        package_id=package_id,
        matrix_path=work_dir / f"manual-decision-matrix-{package_id}.json",
        answer_template_path=work_dir / f"manual-decision-answer-template-{package_id}.json",
        answer_validation_path=work_dir / f"manual-decision-answer-validation-{package_id}.json",
        decision_pack_path=work_dir / f"new-tc-revision-decision-pack-{package_id}.json",
        residual_analysis_path=work_dir / f"residual-source-grounding-gap-analysis-{package_id}.json",
        draft_proposal_path=work_dir / f"new-tc-draft-proposal-{package_id}.json",
        draft_review_path=work_dir / f"new-tc-draft-review-{package_id}.json",
        draft_revision_plan_path=work_dir / f"new-tc-draft-revision-plan-{package_id}.json",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{package_id}.json",
        improvement_plan_path=work_dir / f"agent-capability-improvement-plan-{package_id}.json",
        benchmark_name=args.benchmark_name,
        created_by_tool="scripts/build_agent_decision_resolution.py",
    )
    json_path, markdown_path = write_agent_decision_resolution(resolution, work_dir)
    summary = resolution.decision_summary
    payload = {
        "resolution_path": str(json_path),
        "resolution_markdown_path": str(markdown_path),
        "resolution_status": resolution.resolution_status,
        "package_id": resolution.package_id,
        "rows_total": summary.get("rows_total", 0),
        "resolved_rows": summary.get("resolved_rows", 0),
        "resolved_with_warnings_rows": summary.get("resolved_with_warnings_rows", 0),
        "needs_human_review_rows": summary.get("needs_human_review_rows", 0),
        "deferred_rows": summary.get("deferred_rows", 0),
        "unsafe_rows": summary.get("unsafe_rows", 0),
        "stage_9e_candidate_rows": summary.get("stage_9e_candidate_rows", 0),
        "stage_9e_allowed": resolution.stage_9e_gate.get("stage_9e_allowed"),
        "stage_9e_allowed_scope": resolution.stage_9e_gate.get("stage_9e_allowed_scope"),
        "canonical_write_allowed": resolution.canonical_write_allowed,
        "manual_review_required": resolution.manual_review_required,
        "warnings_count": len(resolution.warnings),
        "blocking_reasons": resolution.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if resolution.resolution_status != "blocked" else 1


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
