from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.agent_capability_improvement_plan import (  # noqa: E402
    DEFAULT_BENCHMARK_NAME,
    DEFAULT_PACKAGE_ID,
    build_agent_capability_improvement_plan,
    write_agent_capability_improvement_plan,
)


INSTRUCTION_SURFACES = [
    "references/agent/controlled-traceability-update-workflow.md",
    "references/agent/controlled-traceability-update-checklist.md",
    "references/agent/new-tc-revision-decision-pack-format.md",
    "references/agent/new-tc-draft-proposal-format.md",
    "references/agent/new-tc-draft-review-format.md",
    "references/agent/new-tc-draft-revision-plan-format.md",
    "references/agent/create-new-tc-context-bundle-format.md",
    "references/agent/instruction-loading-manifest.md",
    "references/agent/instruction-contract-index.md",
    "references/qa/test-case-format.md",
    "references/qa/test-case-runtime-format.md",
    "references/qa/traceability-rules.md",
    "references/agent/writer-runtime-contract.md",
    "references/agent/writer-runtime-workflow.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an agent capability improvement plan from decision-pack findings.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing benchmark artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory, read-only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to analyze.")
    parser.add_argument("--benchmark-name", default=DEFAULT_BENCHMARK_NAME, help="Benchmark label.")
    args = parser.parse_args()

    work_dir = args.work_dir
    plan = build_agent_capability_improvement_plan(
        package_id=args.package_id,
        benchmark_name=args.benchmark_name,
        decision_pack_path=work_dir / f"new-tc-revision-decision-pack-{args.package_id}.json",
        draft_revision_plan_path=work_dir / f"new-tc-draft-revision-plan-{args.package_id}.json",
        draft_review_path=work_dir / f"new-tc-draft-review-{args.package_id}.json",
        draft_proposal_path=work_dir / f"new-tc-draft-proposal-{args.package_id}.json",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.json",
        test_cases_dir=args.test_cases_dir,
        instruction_surface_paths=[ROOT_DIR / path for path in INSTRUCTION_SURFACES],
        created_by_tool="scripts/build_agent_capability_improvement_plan.py",
    )
    json_path, markdown_path = write_agent_capability_improvement_plan(plan, work_dir)
    priority_counts: dict[str, int] = {}
    for item in plan.improvement_items:
        priority_counts[item.priority] = priority_counts.get(item.priority, 0) + 1
    payload = {
        "improvement_plan_path": str(json_path),
        "improvement_plan_markdown_path": str(markdown_path),
        "plan_status": plan.plan_status,
        "package_id": plan.package_id,
        "benchmark_name": plan.benchmark_name,
        "capability_findings_summary_count": len(plan.capability_findings_summary),
        "improvement_items_count": len(plan.improvement_items),
        "priority_counts": priority_counts,
        "instruction_update_plan_count": len(plan.instruction_update_plan),
        "code_update_plan_count": len(plan.code_update_plan),
        "test_update_plan_count": len(plan.test_update_plan),
        "safety_preservation_plan_count": len(plan.safety_preservation_plan),
        "expected_next_stage": plan.expected_next_stage,
        "warnings_count": len(plan.warnings),
        "blocking_reasons": plan.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
