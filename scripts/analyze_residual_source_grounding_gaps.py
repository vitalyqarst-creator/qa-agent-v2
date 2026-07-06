from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.residual_source_grounding_gap_analysis import (  # noqa: E402
    DEFAULT_BENCHMARK_NAME,
    DEFAULT_PACKAGE_ID,
    build_residual_source_grounding_gap_analysis,
    write_residual_source_grounding_gap_analysis,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze residual source-grounding gaps after Stage 9D.3.")
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing Stage 9 artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory, read-only.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to analyze.")
    parser.add_argument("--benchmark-name", default=DEFAULT_BENCHMARK_NAME, help="Benchmark label.")
    parser.add_argument("--old-version", default="autofin-prefinal", help="Old source version slug.")
    parser.add_argument("--new-version", default="autofin-final", help="New source version slug.")
    args = parser.parse_args()

    work_dir = args.work_dir
    pair = f"{args.old_version}-to-{args.new_version}"
    analysis = build_residual_source_grounding_gap_analysis(
        package_id=args.package_id,
        draft_proposal_path=work_dir / f"new-tc-draft-proposal-{args.package_id}.json",
        draft_review_path=work_dir / f"new-tc-draft-review-{args.package_id}.json",
        draft_revision_plan_path=work_dir / f"new-tc-draft-revision-plan-{args.package_id}.json",
        decision_pack_path=work_dir / f"new-tc-revision-decision-pack-{args.package_id}.json",
        improvement_plan_path=work_dir / f"agent-capability-improvement-plan-{args.package_id}.json",
        context_bundle_path=work_dir / f"create-new-tc-context-bundle-{args.package_id}.json",
        old_registry_path=work_dir / f"requirements.{args.old_version}.jsonl",
        new_registry_path=work_dir / f"requirements.{args.new_version}.jsonl",
        requirements_diff_path=work_dir / f"requirements-diff.{pair}.json",
        impact_report_path=work_dir / f"impact-report.{pair}.json",
        update_plan_path=work_dir / f"test-case-update-plan.{pair}.json",
        old_source_manifest_path=work_dir / f"source-manifest.{args.old_version}.json",
        new_source_manifest_path=work_dir / f"source-manifest.{args.new_version}.json",
        test_cases_dir=args.test_cases_dir,
        benchmark_name=args.benchmark_name,
        created_by_tool="scripts/analyze_residual_source_grounding_gaps.py",
    )
    json_path, markdown_path = write_residual_source_grounding_gap_analysis(analysis, work_dir)
    payload = {
        "analysis_path": str(json_path),
        "analysis_markdown_path": str(markdown_path),
        "analysis_status": analysis.analysis_status,
        "package_id": analysis.package_id,
        "draft_gap_analyses_count": len(analysis.draft_gap_analyses),
        "requirement_gap_analyses_count": len(analysis.requirement_gap_analyses),
        "gap_classification_counts": analysis.summary.get("gap_classification_counts", {}),
        "extractor_gap_findings_count": len(analysis.extractor_gap_findings),
        "source_absence_findings_count": len(analysis.source_absence_findings),
        "aggregate_context_findings_count": len(analysis.aggregate_context_findings),
        "duplicate_risk_blockers_count": len(analysis.duplicate_risk_blockers),
        "manual_decision_findings_count": len(analysis.manual_decision_findings),
        "recommended_agent_improvements_count": len(analysis.recommended_agent_improvements),
        "next_stage_recommendation": analysis.next_stage_recommendation,
        "canonical_write_allowed": analysis.canonical_write_allowed,
        "manual_review_required": analysis.manual_review_required,
        "warnings_count": len(analysis.warnings),
        "blocking_reasons": analysis.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
