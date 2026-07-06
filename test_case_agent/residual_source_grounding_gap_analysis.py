from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.create_new_tc_context_bundle import (
    CandidateRequirement,
    CreateNewTcContextBundle,
    load_create_new_tc_context_bundle,
)
from test_case_agent.new_tc_draft_proposals import (
    DraftTestCaseCandidate,
    NewTcDraftProposal,
    SourceGroundingProfile,
    load_new_tc_draft_proposal,
)
from test_case_agent.new_tc_draft_review import load_new_tc_draft_review
from test_case_agent.new_tc_draft_revision_plan import load_new_tc_draft_revision_plan
from test_case_agent.new_tc_revision_decision_pack import (
    NewTcRevisionDecisionPack,
    load_new_tc_revision_decision_pack,
)

CREATED_BY_TOOL = "test_case_agent.residual_source_grounding_gap_analysis"
ANALYSIS_PREFIX = "residual-source-grounding-gap-analysis"
DEFAULT_PACKAGE_ID = "WPKG-000001"
DEFAULT_BENCHMARK_NAME = "AutoFin WPKG-000001 residual source grounding benchmark"

AnalysisStatus = Literal["pass", "pass-with-warnings", "blocked"]
GapClassification = Literal[
    "source_fact_absent",
    "source_fact_present_not_extracted",
    "source_fact_ambiguous",
    "aggregate_context_only",
    "table_or_anchor_context_needed",
    "duplicate_risk_prevents_decision",
    "manual_business_decision_required",
    "draft_generation_rule_gap",
    "unknown",
]
CapabilityArea = Literal[
    "source_grounding",
    "draft_quality",
    "duplicate_risk_handling",
    "manual_decision_flow",
    "requirement_registry",
    "impact_mapping",
]
Priority = Literal["P0", "P1", "P2", "P3"]

ACTION_MARKERS = [
    "user ",
    "пользователь",
    "наж",
    "выбер",
    "откр",
    "перей",
    "ввод",
    "заполн",
    "установ",
    "click",
    "select",
    "open",
    "enter",
    "set ",
]
TABLE_MARKERS = ["таблиц", "строк", "колон"]
TABLE_WORD_RE = re.compile(r"\b(?:table|row|cell|xpath|grid)\b", re.IGNORECASE)
AGGREGATE_MARKERS = ["aggregate", "assembled_from", "test_case_count", "source files assembled"]


@dataclass(frozen=True)
class DraftGroundingGapAnalysis:
    draft_id: str
    proposed_tc_id: str
    is_executable_draft: bool
    contains_generic_placeholders: bool
    source_grounding_status: str
    duplicate_risk_status: str
    candidate_req_uids: list[str]
    source_req_ids: list[str]
    missing_facts: list[str]
    available_facts: list[str]
    gap_classification: GapClassification
    root_cause: str
    evidence: list[str]
    recommended_action: str
    manual_questions: list[str]
    can_be_fixed_by_extractor: bool
    can_be_fixed_by_instruction_update: bool
    requires_human_decision: bool
    should_defer: bool

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DraftGroundingGapAnalysis":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            is_executable_draft=bool(data.get("is_executable_draft")),
            contains_generic_placeholders=bool(data.get("contains_generic_placeholders")),
            source_grounding_status=str(data.get("source_grounding_status") or "unknown"),
            duplicate_risk_status=str(data.get("duplicate_risk_status") or "unknown"),
            candidate_req_uids=list(data.get("candidate_req_uids") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            missing_facts=list(data.get("missing_facts") or []),
            available_facts=list(data.get("available_facts") or []),
            gap_classification=data.get("gap_classification") or "unknown",
            root_cause=str(data.get("root_cause") or ""),
            evidence=list(data.get("evidence") or []),
            recommended_action=str(data.get("recommended_action") or ""),
            manual_questions=list(data.get("manual_questions") or []),
            can_be_fixed_by_extractor=bool(data.get("can_be_fixed_by_extractor")),
            can_be_fixed_by_instruction_update=bool(data.get("can_be_fixed_by_instruction_update")),
            requires_human_decision=bool(data.get("requires_human_decision")),
            should_defer=bool(data.get("should_defer")),
        )


@dataclass(frozen=True)
class RequirementGroundingGapAnalysis:
    req_uid: str
    source_req_id: str | None
    source_text: str | None
    normalized_text: str | None
    object: str | None
    condition: str | None
    expected_behavior: str | None
    source_anchors: list[dict[str, Any]]
    has_object: bool
    has_condition: bool
    has_user_action: bool
    has_expected_behavior: bool
    missing_facts: list[str]
    available_source_fragments: list[str]
    registry_evidence: list[str]
    diff_evidence: list[str]
    impact_evidence: list[str]
    gap_classification: GapClassification
    recommended_action: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementGroundingGapAnalysis":
        return cls(
            req_uid=str(data["req_uid"]),
            source_req_id=data.get("source_req_id"),
            source_text=data.get("source_text"),
            normalized_text=data.get("normalized_text"),
            object=data.get("object"),
            condition=data.get("condition"),
            expected_behavior=data.get("expected_behavior"),
            source_anchors=list(data.get("source_anchors") or []),
            has_object=bool(data.get("has_object")),
            has_condition=bool(data.get("has_condition")),
            has_user_action=bool(data.get("has_user_action")),
            has_expected_behavior=bool(data.get("has_expected_behavior")),
            missing_facts=list(data.get("missing_facts") or []),
            available_source_fragments=list(data.get("available_source_fragments") or []),
            registry_evidence=list(data.get("registry_evidence") or []),
            diff_evidence=list(data.get("diff_evidence") or []),
            impact_evidence=list(data.get("impact_evidence") or []),
            gap_classification=data.get("gap_classification") or "unknown",
            recommended_action=str(data.get("recommended_action") or ""),
        )


@dataclass(frozen=True)
class RecommendedAgentImprovement:
    improvement_id: str
    capability_area: CapabilityArea
    priority: Priority
    problem: str
    evidence: list[str]
    proposed_change: str
    target_files: list[str]
    acceptance_criteria: list[str]
    expected_metric_change: str
    ready_for_implementation: bool

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendedAgentImprovement":
        return cls(
            improvement_id=str(data["improvement_id"]),
            capability_area=data["capability_area"],
            priority=data["priority"],
            problem=str(data["problem"]),
            evidence=list(data.get("evidence") or []),
            proposed_change=str(data["proposed_change"]),
            target_files=list(data.get("target_files") or []),
            acceptance_criteria=list(data.get("acceptance_criteria") or []),
            expected_metric_change=str(data.get("expected_metric_change") or ""),
            ready_for_implementation=bool(data.get("ready_for_implementation")),
        )


@dataclass
class ResidualSourceGroundingGapAnalysis:
    package_id: str
    analysis_status: AnalysisStatus
    benchmark_name: str
    source_artifacts: dict[str, str | None]
    summary: dict[str, Any]
    draft_gap_analyses: list[DraftGroundingGapAnalysis]
    requirement_gap_analyses: list[RequirementGroundingGapAnalysis]
    extractor_gap_findings: list[dict[str, Any]]
    source_absence_findings: list[dict[str, Any]]
    manual_decision_findings: list[dict[str, Any]]
    aggregate_context_findings: list[dict[str, Any]]
    duplicate_risk_blockers: list[dict[str, Any]]
    recommended_agent_improvements: list[RecommendedAgentImprovement]
    recommended_manual_questions: list[str]
    next_stage_recommendation: str
    canonical_write_allowed: bool
    manual_review_required: bool
    input_paths: dict[str, str | None]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "analysis_status": self.analysis_status,
            "benchmark_name": self.benchmark_name,
            "source_artifacts": self.source_artifacts,
            "summary": self.summary,
            "draft_gap_analyses": [item.to_dict() for item in self.draft_gap_analyses],
            "requirement_gap_analyses": [item.to_dict() for item in self.requirement_gap_analyses],
            "extractor_gap_findings": self.extractor_gap_findings,
            "source_absence_findings": self.source_absence_findings,
            "manual_decision_findings": self.manual_decision_findings,
            "aggregate_context_findings": self.aggregate_context_findings,
            "duplicate_risk_blockers": self.duplicate_risk_blockers,
            "recommended_agent_improvements": [item.to_dict() for item in self.recommended_agent_improvements],
            "recommended_manual_questions": self.recommended_manual_questions,
            "next_stage_recommendation": self.next_stage_recommendation,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResidualSourceGroundingGapAnalysis":
        return cls(
            package_id=str(data["package_id"]),
            analysis_status=data["analysis_status"],
            benchmark_name=str(data.get("benchmark_name") or ""),
            source_artifacts=dict(data.get("source_artifacts") or {}),
            summary=dict(data.get("summary") or {}),
            draft_gap_analyses=[
                DraftGroundingGapAnalysis.from_dict(item)
                for item in data.get("draft_gap_analyses", [])
            ],
            requirement_gap_analyses=[
                RequirementGroundingGapAnalysis.from_dict(item)
                for item in data.get("requirement_gap_analyses", [])
            ],
            extractor_gap_findings=list(data.get("extractor_gap_findings") or []),
            source_absence_findings=list(data.get("source_absence_findings") or []),
            manual_decision_findings=list(data.get("manual_decision_findings") or []),
            aggregate_context_findings=list(data.get("aggregate_context_findings") or []),
            duplicate_risk_blockers=list(data.get("duplicate_risk_blockers") or []),
            recommended_agent_improvements=[
                RecommendedAgentImprovement.from_dict(item)
                for item in data.get("recommended_agent_improvements", [])
            ],
            recommended_manual_questions=list(data.get("recommended_manual_questions") or []),
            next_stage_recommendation=str(data.get("next_stage_recommendation") or ""),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data.get("created_at_utc") or ""),
            created_by_tool=str(data.get("created_by_tool") or ""),
        )


def build_residual_source_grounding_gap_analysis(
    *,
    package_id: str,
    draft_proposal_path: Path,
    draft_review_path: Path,
    draft_revision_plan_path: Path,
    decision_pack_path: Path,
    improvement_plan_path: Path,
    context_bundle_path: Path,
    old_registry_path: Path,
    new_registry_path: Path,
    requirements_diff_path: Path,
    impact_report_path: Path,
    update_plan_path: Path,
    test_cases_dir: Path,
    old_source_manifest_path: Path | None = None,
    new_source_manifest_path: Path | None = None,
    benchmark_name: str = DEFAULT_BENCHMARK_NAME,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ResidualSourceGroundingGapAnalysis:
    input_paths = _input_paths(
        draft_proposal_path=draft_proposal_path,
        draft_review_path=draft_review_path,
        draft_revision_plan_path=draft_revision_plan_path,
        decision_pack_path=decision_pack_path,
        improvement_plan_path=improvement_plan_path,
        context_bundle_path=context_bundle_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
        requirements_diff_path=requirements_diff_path,
        impact_report_path=impact_report_path,
        update_plan_path=update_plan_path,
        test_cases_dir=test_cases_dir,
        old_source_manifest_path=old_source_manifest_path,
        new_source_manifest_path=new_source_manifest_path,
    )
    warnings: list[str] = []
    blocking_reasons: list[str] = []

    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"analysis is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")

    for label, path in {
        "draft proposal": draft_proposal_path,
        "draft review": draft_review_path,
        "draft revision plan": draft_revision_plan_path,
        "decision pack": decision_pack_path,
        "improvement plan": improvement_plan_path,
        "context bundle": context_bundle_path,
    }.items():
        if not Path(path).exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    proposal = _load_optional(draft_proposal_path, load_new_tc_draft_proposal, "draft proposal", blocking_reasons)
    _review = _load_optional(draft_review_path, load_new_tc_draft_review, "draft review", blocking_reasons)
    _revision_plan = _load_optional(draft_revision_plan_path, load_new_tc_draft_revision_plan, "draft revision plan", blocking_reasons)
    decision_pack = _load_optional(decision_pack_path, load_new_tc_revision_decision_pack, "decision pack", blocking_reasons)
    improvement_plan = _load_json_object(improvement_plan_path, "improvement plan", warnings, blocking_reasons)
    bundle = _load_optional(context_bundle_path, load_create_new_tc_context_bundle, "context bundle", blocking_reasons)

    for label, artifact in {
        "draft proposal": proposal,
        "decision pack": decision_pack,
        "context bundle": bundle,
    }.items():
        if artifact is not None and getattr(artifact, "package_id", None) != package_id:
            blocking_reasons.append(f"{label} package_id mismatch: {getattr(artifact, 'package_id', None)} != {package_id}")

    old_registry = _load_registry(old_registry_path, warnings)
    new_registry = _load_registry(new_registry_path, warnings)
    requirements_diff = _load_json_object(requirements_diff_path, "requirements diff", warnings, [])
    impact_report = _load_json_object(impact_report_path, "impact report", warnings, [])
    update_plan = _load_json_object(update_plan_path, "test-case update plan", warnings, [])
    old_manifest = _load_json_object(old_source_manifest_path, "old source manifest", warnings, [], required=False)
    new_manifest = _load_json_object(new_source_manifest_path, "new source manifest", warnings, [], required=False)

    if blocking_reasons or proposal is None or decision_pack is None or bundle is None:
        return _analysis(
            package_id=package_id,
            analysis_status="blocked",
            benchmark_name=benchmark_name,
            source_artifacts=_source_artifacts(old_manifest, new_manifest),
            input_paths=input_paths,
            warnings=_unique(warnings),
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    candidate_by_req = {candidate.req_uid: candidate for candidate in bundle.candidate_requirements if candidate.req_uid}
    registry_by_req = _registry_by_req([*old_registry, *new_registry])
    diff_by_change = _index_by_any(requirements_diff.get("entries") if requirements_diff else [], ["change_id", "diff_entry_id"])
    impact_by_id = _index_by_any(impact_report.get("impact_entries") if impact_report else [], ["impact_id"])
    decision_by_draft = {decision.draft_id: decision for decision in decision_pack.draft_decisions}
    duplicate_risks_by_req = _duplicate_risks_by_req(bundle, decision_pack)

    draft_analyses = [
        _draft_gap_analysis(
            draft=draft,
            decision=decision_by_draft.get(draft.draft_id),
            candidate_by_req=candidate_by_req,
            registry_by_req=registry_by_req,
            duplicate_risks_by_req=duplicate_risks_by_req,
        )
        for draft in proposal.draft_test_cases
    ]
    requirement_analyses = [
        _requirement_gap_analysis(
            candidate=candidate,
            profile=_profile_for_req(proposal.draft_test_cases, candidate.req_uid),
            registry_entry=registry_by_req.get(str(candidate.req_uid)),
            diff_entry=diff_by_change.get(str(candidate.diff_entry_id)),
            impact_entry=impact_by_id.get(str(candidate.impact_id)),
            duplicate_risk=duplicate_risks_by_req.get(str(candidate.req_uid)),
        )
        for candidate in bundle.candidate_requirements
        if candidate.req_uid
    ]
    finding_groups = _finding_groups(draft_analyses, requirement_analyses, decision_pack, improvement_plan, update_plan)
    improvements = _recommended_improvements(draft_analyses, requirement_analyses, finding_groups)
    classification_counts = Counter(item.gap_classification for item in [*draft_analyses, *requirement_analyses])
    summary = {
        "draft_gap_analyses_count": len(draft_analyses),
        "requirement_gap_analyses_count": len(requirement_analyses),
        "executable_drafts_count": sum(1 for item in draft_analyses if item.is_executable_draft),
        "non_executable_drafts_count": sum(1 for item in draft_analyses if not item.is_executable_draft),
        "generic_placeholder_drafts_count": sum(1 for item in draft_analyses if item.contains_generic_placeholders),
        "table_context_available_count": _table_context_available_count(bundle, proposal),
        "table_context_used_count": _table_context_used_count(proposal),
        "real_table_context_available_count": _real_table_context_available_count(bundle, proposal),
        "real_table_context_used_count": _real_table_context_used_count(proposal),
        "fallback_table_context_count": _fallback_table_context_count(bundle, proposal),
        "header_cells_available_count": _header_cells_available_count(bundle, proposal),
        "row_cells_available_count": _row_cells_available_count(bundle, proposal),
        "neighboring_rows_available_count": _neighboring_rows_available_count(bundle, proposal),
        "table_context_ambiguous_count": _table_context_ambiguous_count(requirement_analyses),
        "table_context_missing_count": _table_context_missing_count(requirement_analyses),
        "anchor_context_available_count": _anchor_context_available_count(bundle, proposal),
        "anchor_context_used_count": _anchor_context_used_count(proposal),
        "source_fact_ambiguous_count": classification_counts.get("source_fact_ambiguous", 0),
        "source_fact_present_not_extracted_count": classification_counts.get("source_fact_present_not_extracted", 0),
        "source_fact_absent_count": classification_counts.get("source_fact_absent", 0),
        "gap_classification_counts": dict(sorted(classification_counts.items())),
        "source_grounding_unresolved_count": decision_pack.revised_draft_readiness.unresolved_source_grounding_count,
        "needs_manual_decision_count": decision_pack.revised_draft_readiness.needs_manual_decision_count,
        "ready_for_revised_draft_proposal": decision_pack.revised_draft_readiness.ready_for_revised_draft_proposal,
        "canonical_write_allowed": False,
        "manual_review_required": True,
        "metric_note": _metric_note(proposal, decision_pack),
    }
    analysis_status: AnalysisStatus = "pass-with-warnings" if warnings or finding_groups["manual_decision_findings"] else "pass"
    return _analysis(
        package_id=package_id,
        analysis_status=analysis_status,
        benchmark_name=benchmark_name,
        source_artifacts=_source_artifacts(old_manifest, new_manifest),
        summary=summary,
        draft_gap_analyses=draft_analyses,
        requirement_gap_analyses=requirement_analyses,
        extractor_gap_findings=finding_groups["extractor_gap_findings"],
        source_absence_findings=finding_groups["source_absence_findings"],
        manual_decision_findings=finding_groups["manual_decision_findings"],
        aggregate_context_findings=finding_groups["aggregate_context_findings"],
        duplicate_risk_blockers=finding_groups["duplicate_risk_blockers"],
        recommended_agent_improvements=improvements,
        recommended_manual_questions=_manual_questions(draft_analyses, decision_pack),
        next_stage_recommendation=_next_stage_recommendation(improvements, requirement_analyses),
        input_paths=input_paths,
        warnings=_unique(warnings),
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_residual_source_grounding_gap_analysis(
    analysis: ResidualSourceGroundingGapAnalysis,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{ANALYSIS_PREFIX}-{analysis.package_id}.json"
    markdown_path = out_dir / f"{ANALYSIS_PREFIX}-{analysis.package_id}.md"
    json_path.write_text(json.dumps(analysis.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_residual_source_grounding_gap_analysis_markdown(analysis), encoding="utf-8", newline="\n")
    return json_path, markdown_path


def load_residual_source_grounding_gap_analysis(path: Path) -> ResidualSourceGroundingGapAnalysis:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Residual source grounding gap analysis root must be a JSON object.")
    return ResidualSourceGroundingGapAnalysis.from_dict(payload)


def render_residual_source_grounding_gap_analysis_markdown(analysis: ResidualSourceGroundingGapAnalysis) -> str:
    summary = analysis.summary
    lines = [
        f"# Residual Source Grounding Gap Analysis {analysis.package_id}",
        "",
        "## Summary",
        "",
        f"- Analysis status: `{analysis.analysis_status}`",
        f"- Draft gap analyses: `{len(analysis.draft_gap_analyses)}`",
        f"- Requirement gap analyses: `{len(analysis.requirement_gap_analyses)}`",
        f"- Extractor gap findings: `{len(analysis.extractor_gap_findings)}`",
        f"- Source absence findings: `{len(analysis.source_absence_findings)}`",
        f"- Aggregate/table/anchor findings: `{len(analysis.aggregate_context_findings)}`",
        f"- Duplicate-risk blockers: `{len(analysis.duplicate_risk_blockers)}`",
        f"- Manual decision findings: `{len(analysis.manual_decision_findings)}`",
        f"- Recommended improvements: `{len(analysis.recommended_agent_improvements)}`",
        f"- Next stage recommendation: {analysis.next_stage_recommendation}",
        f"- Canonical write allowed: `{str(analysis.canonical_write_allowed).lower()}`",
        f"- Manual review required: `{str(analysis.manual_review_required).lower()}`",
        "",
        "## Stage 9D.3 Metrics",
        "",
        f"- Draft test cases: `{summary.get('draft_gap_analyses_count', 0)}`",
        f"- Executable drafts: `{summary.get('executable_drafts_count', 0)}`",
        f"- Non-executable drafts: `{summary.get('non_executable_drafts_count', 0)}`",
        f"- Generic placeholder drafts: `{summary.get('generic_placeholder_drafts_count', 0)}`",
        f"- Table context available: `{summary.get('table_context_available_count', 0)}`",
        f"- Table context used: `{summary.get('table_context_used_count', 0)}`",
        f"- Real table context available: `{summary.get('real_table_context_available_count', 0)}`",
        f"- Real table context used: `{summary.get('real_table_context_used_count', 0)}`",
        f"- Fallback table context: `{summary.get('fallback_table_context_count', 0)}`",
        f"- Header cells available: `{summary.get('header_cells_available_count', 0)}`",
        f"- Row cells available: `{summary.get('row_cells_available_count', 0)}`",
        f"- Neighboring rows available: `{summary.get('neighboring_rows_available_count', 0)}`",
        f"- Table context ambiguous: `{summary.get('table_context_ambiguous_count', 0)}`",
        f"- Table context missing: `{summary.get('table_context_missing_count', 0)}`",
        f"- Anchor context available: `{summary.get('anchor_context_available_count', 0)}`",
        f"- Anchor context used: `{summary.get('anchor_context_used_count', 0)}`",
        f"- Source fact ambiguous: `{summary.get('source_fact_ambiguous_count', 0)}`",
        f"- Source fact present-not-extracted: `{summary.get('source_fact_present_not_extracted_count', 0)}`",
        f"- Source fact absent: `{summary.get('source_fact_absent_count', 0)}`",
        f"- Source grounding unresolved count: `{summary.get('source_grounding_unresolved_count', 0)}`",
        f"- Needs manual decision count: `{summary.get('needs_manual_decision_count', 0)}`",
        f"- Ready for revised draft proposal: `{str(summary.get('ready_for_revised_draft_proposal')).lower()}`",
        f"- Metric note: {summary.get('metric_note', '')}",
        "",
        "## Residual Gap Breakdown",
        "",
    ]
    for key, value in (summary.get("gap_classification_counts") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    if not summary.get("gap_classification_counts"):
        lines.append("- none")
    lines.extend([
        "",
        "## Draft-Level Gap Table",
        "",
        "| Draft | Executable | Source | Duplicate | Classification | Missing facts | Action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for item in analysis.draft_gap_analyses:
        lines.append(
            f"| `{item.draft_id}` | `{str(item.is_executable_draft).lower()}` | "
            f"`{item.source_grounding_status}` | `{item.duplicate_risk_status}` | "
            f"`{item.gap_classification}` | {', '.join(item.missing_facts) or 'none'} | {item.recommended_action} |"
        )
    lines.extend([
        "",
        "## Requirement-Level Gap Table",
        "",
        "| Req UID | Source Req ID | Object | Condition | Action | Expected | Classification |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for item in analysis.requirement_gap_analyses:
        lines.append(
            f"| `{item.req_uid}` | `{item.source_req_id or ''}` | `{str(item.has_object).lower()}` | "
            f"`{str(item.has_condition).lower()}` | `{str(item.has_user_action).lower()}` | "
            f"`{str(item.has_expected_behavior).lower()}` | `{item.gap_classification}` |"
        )
    _section(lines, "Root Cause Categories", _root_cause_lines(analysis))
    _section(lines, "Extractor Gaps", _finding_lines(analysis.extractor_gap_findings))
    _section(lines, "Source Absence Findings", _finding_lines(analysis.source_absence_findings))
    _section(lines, "Aggregate/Table/Anchor Context Findings", _finding_lines(analysis.aggregate_context_findings))
    _section(lines, "Duplicate-Risk Blockers", _finding_lines(analysis.duplicate_risk_blockers))
    _section(lines, "Manual Decision Findings", _finding_lines(analysis.manual_decision_findings))
    lines.extend(["", "## Recommended Agent Improvements", ""])
    for item in analysis.recommended_agent_improvements:
        lines.append(f"- `{item.improvement_id}` `{item.priority}` `{item.capability_area}`: {item.proposed_change}")
    if not analysis.recommended_agent_improvements:
        lines.append("- none")
    _section(lines, "Recommended Manual Questions", analysis.recommended_manual_questions)
    lines.extend([
        "",
        "## Next Stage Recommendation",
        "",
        f"- {analysis.next_stage_recommendation}",
        "",
        "## Safety Statement",
        "",
        "- Diagnostic artifact only.",
        "- No canonical TC was created.",
        "- No canonical TC was edited.",
        "- No revised draft proposal was created.",
        "- No apply command, git apply, or patch application is authorized.",
    ])
    if analysis.warnings:
        _section(lines, "Warnings", analysis.warnings)
    if analysis.blocking_reasons:
        _section(lines, "Blocking Reasons", analysis.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _draft_gap_analysis(
    *,
    draft: DraftTestCaseCandidate,
    decision: Any,
    candidate_by_req: dict[str, CandidateRequirement],
    registry_by_req: dict[str, dict[str, Any]],
    duplicate_risks_by_req: dict[str, str],
) -> DraftGroundingGapAnalysis:
    profile_missing = _unique(fact for profile in draft.source_grounding_profiles for fact in profile.missing_facts)
    missing = profile_missing or _missing_from_candidates(draft.source_requirement_uids, candidate_by_req)
    available = _available_from_draft(draft, candidate_by_req)
    evidence = [
        f"is_executable_draft={draft.is_executable_draft}",
        f"contains_generic_placeholders={draft.contains_generic_placeholders}",
    ]
    if decision:
        evidence.append(f"decision={decision.decision}")
    classification = _classify_draft_gap(draft, missing, candidate_by_req, registry_by_req, duplicate_risks_by_req)
    duplicate_status = getattr(decision, "duplicate_risk_status", "unknown") if decision else _duplicate_status(draft, duplicate_risks_by_req)
    source_status = getattr(decision, "source_grounding_status", "resolved" if draft.is_executable_draft else "unresolved") if decision else ("resolved" if draft.is_executable_draft else "unresolved")
    return DraftGroundingGapAnalysis(
        draft_id=draft.draft_id,
        proposed_tc_id=draft.proposed_tc_id,
        is_executable_draft=draft.is_executable_draft,
        contains_generic_placeholders=draft.contains_generic_placeholders,
        source_grounding_status=source_status,
        duplicate_risk_status=duplicate_status,
        candidate_req_uids=list(draft.source_requirement_uids),
        source_req_ids=list(draft.source_req_ids),
        missing_facts=missing,
        available_facts=available,
        gap_classification=classification,
        root_cause=_root_cause_for_classification(classification),
        evidence=evidence,
        recommended_action=_recommended_action_for_classification(classification),
        manual_questions=_unique(draft.manual_questions),
        can_be_fixed_by_extractor=classification in {"source_fact_present_not_extracted", "table_or_anchor_context_needed"},
        can_be_fixed_by_instruction_update=classification in {"draft_generation_rule_gap", "source_fact_present_not_extracted"},
        requires_human_decision=classification in {"manual_business_decision_required", "duplicate_risk_prevents_decision", "source_fact_absent"},
        should_defer=classification in {"manual_business_decision_required", "source_fact_absent", "unknown"},
    )


def _requirement_gap_analysis(
    *,
    candidate: CandidateRequirement,
    profile: SourceGroundingProfile | None,
    registry_entry: dict[str, Any] | None,
    diff_entry: dict[str, Any] | None,
    impact_entry: dict[str, Any] | None,
    duplicate_risk: str | None,
) -> RequirementGroundingGapAnalysis:
    source_text = profile.source_text if profile and profile.source_text is not None else candidate.source_text
    normalized_text = profile.normalized_text if profile and profile.normalized_text is not None else candidate.normalized_text
    object_value = profile.object if profile and profile.object is not None else candidate.object
    condition = profile.condition if profile and profile.condition is not None else candidate.condition
    expected = profile.observable_expected_behavior if profile and profile.observable_expected_behavior is not None else candidate.expected_behavior
    anchors = list((profile.source_anchors if profile else None) or candidate.source_anchors or [])
    has_object = bool(object_value)
    has_condition = bool(condition)
    has_action = bool(profile.user_action if profile else None) or _has_user_action([condition, source_text, normalized_text])
    has_expected = bool(expected)
    missing: list[str] = []
    if not has_object:
        missing.append("specific object/field/screen")
    if not has_condition:
        missing.append("source-backed condition")
    if not has_action:
        missing.append("source-backed user action")
    if not has_expected:
        missing.append("observable expected behavior")
    registry_evidence = _artifact_evidence(registry_entry, ["req_uid", "source_req_id", "source_text", "normalized_text", "object", "condition", "expected_behavior"])
    diff_evidence = _artifact_evidence(diff_entry, ["change_id", "change_type", "old_req_uid", "new_req_uid", "source_req_id"])
    impact_evidence = _artifact_evidence(impact_entry, ["impact_id", "action", "change_id", "requirement_refs"])
    classification = _classify_requirement_gap(
        missing=missing,
        candidate=candidate,
        registry_entry=registry_entry,
        anchors=anchors,
        duplicate_risk=duplicate_risk,
    )
    return RequirementGroundingGapAnalysis(
        req_uid=str(candidate.req_uid),
        source_req_id=candidate.source_req_id,
        source_text=source_text,
        normalized_text=normalized_text,
        object=object_value,
        condition=condition,
        expected_behavior=expected,
        source_anchors=anchors,
        has_object=has_object,
        has_condition=has_condition,
        has_user_action=has_action,
        has_expected_behavior=has_expected,
        missing_facts=missing,
        available_source_fragments=_available_fragments(candidate, profile),
        registry_evidence=registry_evidence,
        diff_evidence=diff_evidence,
        impact_evidence=impact_evidence,
        gap_classification=classification,
        recommended_action=_recommended_action_for_classification(classification),
    )


def _classify_draft_gap(
    draft: DraftTestCaseCandidate,
    missing: list[str],
    candidate_by_req: dict[str, CandidateRequirement],
    registry_by_req: dict[str, dict[str, Any]],
    duplicate_risks_by_req: dict[str, str],
) -> GapClassification:
    if draft.contains_generic_placeholders:
        return "draft_generation_rule_gap"
    if any(duplicate_risks_by_req.get(req_uid) in {"medium", "high"} for req_uid in draft.source_requirement_uids):
        return "duplicate_risk_prevents_decision"
    if not missing and draft.is_executable_draft:
        return "manual_business_decision_required"
    if _has_table_or_anchor_context_for_reqs(draft.source_requirement_uids, candidate_by_req):
        return "table_or_anchor_context_needed"
    if _registry_has_missing_fact(draft.source_requirement_uids, registry_by_req, missing):
        return "source_fact_present_not_extracted"
    if any(_has_aggregate_context(candidate_by_req.get(req_uid)) for req_uid in draft.source_requirement_uids):
        return "aggregate_context_only"
    if missing:
        return "source_fact_absent"
    return "unknown"


def _classify_requirement_gap(
    *,
    missing: list[str],
    candidate: CandidateRequirement,
    registry_entry: dict[str, Any] | None,
    anchors: list[dict[str, Any]],
    duplicate_risk: str | None,
) -> GapClassification:
    if duplicate_risk in {"medium", "high"}:
        return "duplicate_risk_prevents_decision"
    if _has_real_table_context(candidate, anchors) and missing:
        return "source_fact_ambiguous"
    if _has_table_or_anchor_context(candidate, anchors):
        return "table_or_anchor_context_needed"
    if _registry_has_any_missing_fact(registry_entry, missing):
        return "source_fact_present_not_extracted"
    if _has_aggregate_context(candidate):
        return "aggregate_context_only"
    if missing:
        source_values = [candidate.source_text, candidate.normalized_text, candidate.condition, candidate.expected_behavior]
        if any(_ambiguous(str(value or "")) for value in source_values):
            return "source_fact_ambiguous"
        return "source_fact_absent"
    return "manual_business_decision_required" if duplicate_risk else "unknown"


def _finding_groups(
    draft_analyses: list[DraftGroundingGapAnalysis],
    requirement_analyses: list[RequirementGroundingGapAnalysis],
    decision_pack: NewTcRevisionDecisionPack,
    improvement_plan: dict[str, Any] | None,
    update_plan: dict[str, Any] | None,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "extractor_gap_findings": [],
        "source_absence_findings": [],
        "manual_decision_findings": [],
        "aggregate_context_findings": [],
        "duplicate_risk_blockers": [],
    }
    for item in requirement_analyses:
        record = {
            "req_uid": item.req_uid,
            "source_req_id": item.source_req_id,
            "classification": item.gap_classification,
            "missing_facts": item.missing_facts,
            "recommended_action": item.recommended_action,
        }
        if item.gap_classification == "source_fact_present_not_extracted":
            groups["extractor_gap_findings"].append(record)
        elif item.gap_classification == "source_fact_absent":
            groups["source_absence_findings"].append(record)
        elif item.gap_classification in {"aggregate_context_only", "table_or_anchor_context_needed"}:
            groups["aggregate_context_findings"].append(record)
        elif item.gap_classification == "duplicate_risk_prevents_decision":
            groups["duplicate_risk_blockers"].append(record)
        if item.gap_classification in {"manual_business_decision_required", "source_fact_absent", "duplicate_risk_prevents_decision"}:
            groups["manual_decision_findings"].append(record)
    for decision in decision_pack.manual_decisions_required:
        groups["manual_decision_findings"].append(
            {
                "scope": decision.get("scope"),
                "id": decision.get("id"),
                "question": decision.get("question"),
                "classification": "manual_business_decision_required",
            }
        )
    if improvement_plan and improvement_plan.get("blocking_reasons"):
        groups["manual_decision_findings"].append(
            {
                "scope": "improvement_plan",
                "classification": "manual_business_decision_required",
                "question": "Resolve upstream improvement plan blockers before revised drafting.",
            }
        )
    if update_plan and update_plan.get("plan_status") == "blocked":
        groups["manual_decision_findings"].append(
            {
                "scope": "update_plan",
                "classification": "manual_business_decision_required",
                "question": "Resolve blocked update plan before using create-new diagnostics.",
            }
        )
    return {key: _dedupe_dicts(value) for key, value in groups.items()}


def _recommended_improvements(
    draft_analyses: list[DraftGroundingGapAnalysis],
    requirement_analyses: list[RequirementGroundingGapAnalysis],
    finding_groups: dict[str, list[dict[str, Any]]],
) -> list[RecommendedAgentImprovement]:
    improvements: list[RecommendedAgentImprovement] = []
    if finding_groups["extractor_gap_findings"]:
        improvements.append(
            RecommendedAgentImprovement(
                improvement_id="RSFG-IMP-001",
                capability_area="source_grounding",
                priority="P1",
                problem="Source facts appear present in artifacts but are not promoted into source-grounding profiles.",
                evidence=[f"{len(finding_groups['extractor_gap_findings'])} present-not-extracted findings"],
                proposed_change="Enrich extraction from registry/source anchors before draft generation.",
                target_files=["test_case_agent/new_tc_draft_proposals.py", "test_case_agent/create_new_tc_context_bundle.py"],
                acceptance_criteria=["present source facts populate grounding profiles", "manual questions decrease without invented behavior"],
                expected_metric_change="Reduce unresolved_source_grounding_drafts_count.",
                ready_for_implementation=True,
            )
        )
    if finding_groups["aggregate_context_findings"]:
        improvements.append(
            RecommendedAgentImprovement(
                improvement_id="RSFG-IMP-002",
                capability_area="requirement_registry",
                priority="P1",
                problem="Some requirements need table or source-anchor context before executable drafting.",
                evidence=[f"{len(finding_groups['aggregate_context_findings'])} aggregate/table/anchor findings"],
                proposed_change="Carry structured table row/header/anchor context into candidate requirements.",
                target_files=["test_case_agent/requirements_registry.py", "test_case_agent/create_new_tc_context_bundle.py"],
                acceptance_criteria=["table-derived requirements expose row/header context", "single-cell markers are not drafted without row context"],
                expected_metric_change="Increase executable_drafts_count only when table context is sufficient.",
                ready_for_implementation=True,
            )
        )
    if any(item.contains_generic_placeholders for item in draft_analyses):
        improvements.append(
            RecommendedAgentImprovement(
                improvement_id="RSFG-IMP-003",
                capability_area="draft_quality",
                priority="P0",
                problem="Generic placeholders remain in draft outputs.",
                evidence=["contains_generic_placeholders detected"],
                proposed_change="Keep placeholder guardrail strict and block executable draft status.",
                target_files=["test_case_agent/new_tc_draft_proposals.py", "test_case_agent/new_tc_draft_review.py"],
                acceptance_criteria=["generic_placeholder_drafts_count is zero"],
                expected_metric_change="Generic placeholder draft count stays at zero.",
                ready_for_implementation=True,
            )
        )
    if finding_groups["duplicate_risk_blockers"]:
        improvements.append(
            RecommendedAgentImprovement(
                improvement_id="RSFG-IMP-004",
                capability_area="duplicate_risk_handling",
                priority="P2",
                problem="Duplicate-risk decisions keep otherwise grounded drafts manual-only.",
                evidence=[f"{len(finding_groups['duplicate_risk_blockers'])} duplicate-risk blockers"],
                proposed_change="Compress duplicate-risk manual decisions into shared clusters with explicit differentiation criteria.",
                target_files=["test_case_agent/new_tc_revision_decision_pack.py"],
                acceptance_criteria=["manual decision count groups duplicate decisions without weakening review"],
                expected_metric_change="Reduce needs_manual_decision_count by clustering repeated duplicate questions.",
                ready_for_implementation=True,
            )
        )
    if not improvements and any(item.gap_classification == "source_fact_absent" for item in requirement_analyses):
        improvements.append(
            RecommendedAgentImprovement(
                improvement_id="RSFG-IMP-005",
                capability_area="manual_decision_flow",
                priority="P2",
                problem="Source facts are absent or too ambiguous for safe executable drafting.",
                evidence=["source_fact_absent findings remain"],
                proposed_change="Generate a compact human clarification matrix before revised drafting.",
                target_files=["test_case_agent/residual_source_grounding_gap_analysis.py"],
                acceptance_criteria=["manual questions are grouped by missing fact and source anchor"],
                expected_metric_change="No unsafe automatic drafting; manual questions become actionable.",
                ready_for_implementation=False,
            )
        )
    return improvements


def _next_stage_recommendation(
    improvements: list[RecommendedAgentImprovement],
    requirement_analyses: list[RequirementGroundingGapAnalysis],
) -> str:
    if any(item.capability_area in {"source_grounding", "requirement_registry"} and item.priority == "P1" for item in improvements):
        return "Stage 9D.5 - Implement Source Fact Extraction Improvements"
    if any(item.gap_classification == "source_fact_absent" for item in requirement_analyses):
        return "Stage 9D.5 - Manual Decision Matrix Compression"
    return "Stop and require human clarification"


def _metric_note(proposal: NewTcDraftProposal, decision_pack: NewTcRevisionDecisionPack) -> str:
    executable = sum(1 for draft in proposal.draft_test_cases if draft.is_executable_draft)
    unresolved = decision_pack.revised_draft_readiness.unresolved_source_grounding_count
    if executable and unresolved == len(proposal.draft_test_cases):
        return (
            "Source-grounding readiness is draft-decision based: executable draft mechanics can exist, "
            "while duplicate/manual decision status keeps all source grounding resolutions unresolved."
        )
    return "Source-grounding readiness is based on decision-pack unresolved resolution counts."


def _table_context_available_count(bundle: CreateNewTcContextBundle, proposal: NewTcDraftProposal) -> int:
    reqs = {
        candidate.req_uid
        for candidate in bundle.candidate_requirements
        if candidate.req_uid and getattr(candidate, "table_source_contexts", [])
    }
    for draft in proposal.draft_test_cases:
        for profile in draft.source_grounding_profiles:
            if profile.req_uid and profile.table_source_contexts:
                reqs.add(profile.req_uid)
    return len(reqs)


def _table_context_used_count(proposal: NewTcDraftProposal) -> int:
    return sum(
        1
        for draft in proposal.draft_test_cases
        for profile in draft.source_grounding_profiles
        if "table_source_context" in profile.available_fact_sources
    )


def _real_table_context_available_count(bundle: CreateNewTcContextBundle, proposal: NewTcDraftProposal) -> int:
    reqs = {
        candidate.req_uid
        for candidate in bundle.candidate_requirements
        if candidate.req_uid and any(_is_real_table_context(context) for context in getattr(candidate, "table_source_contexts", []) or [])
    }
    for draft in proposal.draft_test_cases:
        for profile in draft.source_grounding_profiles:
            if profile.req_uid and any(_is_real_table_context_dict(context) for context in profile.table_source_contexts):
                reqs.add(profile.req_uid)
    return len(reqs)


def _real_table_context_used_count(proposal: NewTcDraftProposal) -> int:
    return sum(
        1
        for draft in proposal.draft_test_cases
        for profile in draft.source_grounding_profiles
        if any(_is_real_table_context_dict(context) for context in profile.table_source_contexts)
    )


def _fallback_table_context_count(bundle: CreateNewTcContextBundle, proposal: NewTcDraftProposal) -> int:
    reqs = {
        candidate.req_uid
        for candidate in bundle.candidate_requirements
        if candidate.req_uid and any(_is_fallback_table_context(context) for context in getattr(candidate, "table_source_contexts", []) or [])
    }
    for draft in proposal.draft_test_cases:
        for profile in draft.source_grounding_profiles:
            if profile.req_uid and any(_is_fallback_table_context_dict(context) for context in profile.table_source_contexts):
                reqs.add(profile.req_uid)
    return len(reqs)


def _header_cells_available_count(bundle: CreateNewTcContextBundle, proposal: NewTcDraftProposal) -> int:
    return _table_context_field_available_count(bundle, proposal, "header_cells")


def _row_cells_available_count(bundle: CreateNewTcContextBundle, proposal: NewTcDraftProposal) -> int:
    return _table_context_field_available_count(bundle, proposal, "row_cells")


def _neighboring_rows_available_count(bundle: CreateNewTcContextBundle, proposal: NewTcDraftProposal) -> int:
    return _table_context_field_available_count(bundle, proposal, "neighboring_rows")


def _table_context_field_available_count(
    bundle: CreateNewTcContextBundle,
    proposal: NewTcDraftProposal,
    field_name: str,
) -> int:
    reqs = {
        candidate.req_uid
        for candidate in bundle.candidate_requirements
        if candidate.req_uid and any(getattr(context, field_name, None) for context in getattr(candidate, "table_source_contexts", []) or [])
    }
    for draft in proposal.draft_test_cases:
        for profile in draft.source_grounding_profiles:
            if profile.req_uid and any(context.get(field_name) for context in profile.table_source_contexts):
                reqs.add(profile.req_uid)
    return len(reqs)


def _table_context_ambiguous_count(requirements: list[RequirementGroundingGapAnalysis]) -> int:
    return sum(1 for item in requirements if item.gap_classification == "source_fact_ambiguous")


def _table_context_missing_count(requirements: list[RequirementGroundingGapAnalysis]) -> int:
    return sum(1 for item in requirements if item.gap_classification == "table_or_anchor_context_needed")


def _anchor_context_available_count(bundle: CreateNewTcContextBundle, proposal: NewTcDraftProposal) -> int:
    reqs = {
        candidate.req_uid
        for candidate in bundle.candidate_requirements
        if candidate.req_uid and getattr(candidate, "source_anchor_contexts", [])
    }
    for draft in proposal.draft_test_cases:
        for profile in draft.source_grounding_profiles:
            if profile.req_uid and profile.source_anchor_contexts:
                reqs.add(profile.req_uid)
    return len(reqs)


def _anchor_context_used_count(proposal: NewTcDraftProposal) -> int:
    return sum(
        1
        for draft in proposal.draft_test_cases
        for profile in draft.source_grounding_profiles
        if "source_anchor_context" in profile.available_fact_sources
    )


def _analysis(
    *,
    package_id: str,
    analysis_status: AnalysisStatus,
    benchmark_name: str,
    source_artifacts: dict[str, str | None] | None = None,
    summary: dict[str, Any] | None = None,
    draft_gap_analyses: list[DraftGroundingGapAnalysis] | None = None,
    requirement_gap_analyses: list[RequirementGroundingGapAnalysis] | None = None,
    extractor_gap_findings: list[dict[str, Any]] | None = None,
    source_absence_findings: list[dict[str, Any]] | None = None,
    manual_decision_findings: list[dict[str, Any]] | None = None,
    aggregate_context_findings: list[dict[str, Any]] | None = None,
    duplicate_risk_blockers: list[dict[str, Any]] | None = None,
    recommended_agent_improvements: list[RecommendedAgentImprovement] | None = None,
    recommended_manual_questions: list[str] | None = None,
    next_stage_recommendation: str = "Stop and require human clarification",
    input_paths: dict[str, str | None] | None = None,
    warnings: list[str] | None = None,
    blocking_reasons: list[str] | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ResidualSourceGroundingGapAnalysis:
    return ResidualSourceGroundingGapAnalysis(
        package_id=package_id,
        analysis_status=analysis_status,
        benchmark_name=benchmark_name,
        source_artifacts=source_artifacts or {},
        summary=summary or {},
        draft_gap_analyses=draft_gap_analyses or [],
        requirement_gap_analyses=requirement_gap_analyses or [],
        extractor_gap_findings=extractor_gap_findings or [],
        source_absence_findings=source_absence_findings or [],
        manual_decision_findings=manual_decision_findings or [],
        aggregate_context_findings=aggregate_context_findings or [],
        duplicate_risk_blockers=duplicate_risk_blockers or [],
        recommended_agent_improvements=recommended_agent_improvements or [],
        recommended_manual_questions=recommended_manual_questions or [],
        next_stage_recommendation=next_stage_recommendation,
        canonical_write_allowed=False,
        manual_review_required=True,
        input_paths=input_paths or {},
        warnings=warnings or [],
        blocking_reasons=blocking_reasons or [],
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _profile_for_req(drafts: list[DraftTestCaseCandidate], req_uid: str | None) -> SourceGroundingProfile | None:
    for draft in drafts:
        for profile in draft.source_grounding_profiles:
            if profile.req_uid == req_uid:
                return profile
    return None


def _available_from_draft(draft: DraftTestCaseCandidate, candidate_by_req: dict[str, CandidateRequirement]) -> list[str]:
    facts: list[str] = []
    for profile in draft.source_grounding_profiles:
        facts.extend(_available_from_profile(profile))
    for req_uid in draft.source_requirement_uids:
        candidate = candidate_by_req.get(req_uid)
        if candidate:
            facts.extend(_available_from_candidate(candidate))
    return _unique(facts)


def _available_from_profile(profile: SourceGroundingProfile) -> list[str]:
    facts: list[str] = []
    for label, value in [
        ("object", profile.object),
        ("condition", profile.condition),
        ("user_action", profile.user_action),
        ("expected_behavior", profile.observable_expected_behavior),
        ("source_req_id", profile.source_req_id),
    ]:
        if value:
            facts.append(f"{label}: {value}")
    return facts


def _available_from_candidate(candidate: CandidateRequirement) -> list[str]:
    facts: list[str] = []
    for label, value in [
        ("object", candidate.object),
        ("condition", candidate.condition),
        ("expected_behavior", candidate.expected_behavior),
        ("source_req_id", candidate.source_req_id),
    ]:
        if value:
            facts.append(f"{label}: {value}")
    return facts


def _available_fragments(candidate: CandidateRequirement, profile: SourceGroundingProfile | None) -> list[str]:
    values = [
        candidate.object,
        candidate.condition,
        candidate.expected_behavior,
        candidate.source_text,
        candidate.normalized_text,
    ]
    if profile:
        values.extend([profile.object, profile.condition, profile.user_action, profile.observable_expected_behavior])
    return _unique(value for value in values if value)


def _missing_from_candidates(req_uids: list[str], candidate_by_req: dict[str, CandidateRequirement]) -> list[str]:
    missing: list[str] = []
    for req_uid in req_uids:
        candidate = candidate_by_req.get(req_uid)
        if not candidate:
            missing.append("candidate requirement")
            continue
        if not candidate.object:
            missing.append("specific object/field/screen")
        if not candidate.condition:
            missing.append("source-backed condition")
        if not _has_user_action([candidate.condition, candidate.source_text, candidate.normalized_text]):
            missing.append("source-backed user action")
        if not candidate.expected_behavior:
            missing.append("observable expected behavior")
    return _unique(missing)


def _duplicate_status(draft: DraftTestCaseCandidate, duplicate_risks_by_req: dict[str, str]) -> str:
    risks = {duplicate_risks_by_req.get(req_uid) for req_uid in draft.source_requirement_uids}
    if "high" in risks or "medium" in risks:
        return "unresolved"
    return "resolved"


def _duplicate_risks_by_req(bundle: CreateNewTcContextBundle, decision_pack: NewTcRevisionDecisionPack) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in bundle.duplicate_risks:
        req_uid = item.get("candidate_req_uid") or item.get("req_uid")
        if req_uid:
            result[str(req_uid)] = str(item.get("risk") or "medium")
    for cluster in decision_pack.duplicate_risk_clusters:
        for req_uid in cluster.candidate_req_uids:
            result[str(req_uid)] = cluster.risk
    return result


def _has_table_or_anchor_context_for_reqs(req_uids: list[str], candidate_by_req: dict[str, CandidateRequirement]) -> bool:
    return any(_has_table_or_anchor_context(candidate_by_req.get(req_uid), None) for req_uid in req_uids)


def _has_table_or_anchor_context(candidate: CandidateRequirement | None, anchors: list[dict[str, Any]] | None) -> bool:
    values = []
    if candidate:
        values.extend([candidate.source_text, candidate.normalized_text, candidate.condition])
        anchors = anchors or candidate.source_anchors
    values.extend(json.dumps(anchor, ensure_ascii=False) for anchor in anchors or [])
    text = " ".join(str(value or "").casefold() for value in values)
    return bool(TABLE_WORD_RE.search(text)) or any(marker in text for marker in TABLE_MARKERS)


def _has_real_table_context(candidate: CandidateRequirement | None, anchors: list[dict[str, Any]] | None) -> bool:
    if candidate and any(_is_real_table_context(context) for context in getattr(candidate, "table_source_contexts", []) or []):
        return True
    return False


def _is_real_table_context(context: Any) -> bool:
    warnings = [str(value).casefold() for value in getattr(context, "warnings", []) or []]
    return bool(getattr(context, "row_cells", None)) and not any("fallback" in warning for warning in warnings)


def _is_real_table_context_dict(context: dict[str, Any]) -> bool:
    warnings = [str(value).casefold() for value in context.get("warnings") or []]
    return bool(context.get("row_cells")) and not any("fallback" in warning for warning in warnings)


def _is_fallback_table_context(context: Any) -> bool:
    return any("fallback" in str(value).casefold() for value in getattr(context, "warnings", []) or [])


def _is_fallback_table_context_dict(context: dict[str, Any]) -> bool:
    return any("fallback" in str(value).casefold() for value in context.get("warnings") or [])


def _has_aggregate_context(candidate: CandidateRequirement | None) -> bool:
    if not candidate:
        return False
    text = " ".join(
        [
            str(candidate.source_text or ""),
            str(candidate.normalized_text or ""),
            json.dumps(candidate.source_anchors, ensure_ascii=False),
        ]
    ).casefold()
    return any(marker in text for marker in AGGREGATE_MARKERS)


def _registry_has_missing_fact(req_uids: list[str], registry_by_req: dict[str, dict[str, Any]], missing: list[str]) -> bool:
    return any(_registry_has_any_missing_fact(registry_by_req.get(req_uid), missing) for req_uid in req_uids)


def _registry_has_any_missing_fact(entry: dict[str, Any] | None, missing: list[str]) -> bool:
    if not entry or not missing:
        return False
    values = [entry.get("object"), entry.get("condition"), entry.get("expected_behavior"), entry.get("source_text"), entry.get("normalized_text")]
    if "source-backed user action" in missing and _has_user_action(values):
        return True
    if "observable expected behavior" in missing and any(entry.get(key) for key in ["expected_behavior", "expected_result", "observable_expected_behavior"]):
        return True
    if "source-backed condition" in missing and entry.get("condition"):
        return True
    if "specific object/field/screen" in missing and entry.get("object"):
        return True
    return False


def _has_user_action(values: list[Any]) -> bool:
    text = " ".join(str(value or "").casefold() for value in values)
    return any(marker in text for marker in ACTION_MARKERS)


def _ambiguous(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in ["unclear", "ambiguous", "неоднознач", "уточнить", "manual"])


def _root_cause_for_classification(classification: GapClassification) -> str:
    return {
        "source_fact_absent": "Required executable-test facts are not visible in the checked artifacts.",
        "source_fact_present_not_extracted": "A source fact appears in registry/source text but was not promoted into grounding fields.",
        "source_fact_ambiguous": "Source text exists but does not define a safe executable action or oracle.",
        "aggregate_context_only": "The current artifact points to aggregate context without enough atomic source facts.",
        "table_or_anchor_context_needed": "The requirement depends on table row/header or anchor context not represented in the draft model.",
        "duplicate_risk_prevents_decision": "Duplicate-risk review blocks create-new readiness even if source facts are partly available.",
        "manual_business_decision_required": "A human decision is still required before creating a new canonical test case.",
        "draft_generation_rule_gap": "Draft generation emitted output that should remain blocked by quality rules.",
        "unknown": "The artifacts do not provide enough evidence for a narrower classification.",
    }[classification]


def _recommended_action_for_classification(classification: GapClassification) -> str:
    return {
        "source_fact_absent": "Ask a human clarification question or defer; do not invent executable steps.",
        "source_fact_present_not_extracted": "Improve extraction/promotion of source facts before revised drafting.",
        "source_fact_ambiguous": "Ask for manual business clarification.",
        "aggregate_context_only": "Resolve aggregate source into atomic source facts before drafting.",
        "table_or_anchor_context_needed": "Carry table row/header/anchor context into candidate requirements.",
        "duplicate_risk_prevents_decision": "Resolve duplicate-risk differentiation or maybe-extend decision.",
        "manual_business_decision_required": "Keep draft manual-only until decision is recorded.",
        "draft_generation_rule_gap": "Tighten draft generation and review guardrails.",
        "unknown": "Investigate manually before moving to revised draft proposal.",
    }[classification]


def _manual_questions(draft_analyses: list[DraftGroundingGapAnalysis], decision_pack: NewTcRevisionDecisionPack) -> list[str]:
    questions: list[str] = []
    for item in draft_analyses:
        questions.extend(item.manual_questions)
    for item in decision_pack.manual_decisions_required:
        question = item.get("question")
        if question:
            questions.append(str(question))
    return _unique(questions)


def _root_cause_lines(analysis: ResidualSourceGroundingGapAnalysis) -> list[str]:
    counts = Counter(item.root_cause for item in analysis.draft_gap_analyses)
    return [f"`{count}` - {cause}" for cause, count in counts.items()]


def _finding_lines(findings: list[dict[str, Any]]) -> list[str]:
    return [
        f"`{item.get('classification', item.get('scope', 'finding'))}` "
        f"{item.get('req_uid', item.get('id', ''))}: {item.get('recommended_action', item.get('question', ''))}"
        for item in findings
    ] or ["none"]


def _section(lines: list[str], title: str, values: list[str]) -> None:
    lines.extend(["", f"## {title}", ""])
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


def _artifact_evidence(entry: dict[str, Any] | None, keys: list[str]) -> list[str]:
    if not entry:
        return []
    evidence = []
    for key in keys:
        value = entry.get(key)
        if value not in (None, "", []):
            evidence.append(f"{key}: {value}")
    return evidence


def _registry_by_req(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        for key in ["req_uid", "old_req_uid", "new_req_uid"]:
            value = entry.get(key)
            if value:
                result[str(value)] = entry
    return result


def _index_by_any(items: Any, keys: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for key in keys:
            value = item.get(key)
            if value:
                result[str(value)] = item
    return result


def _load_registry(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    if not Path(path).exists():
        warnings.append(f"registry is missing: {path}")
        return []
    entries: list[dict[str, Any]] = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if isinstance(item, dict):
                    entries.append(item)
    except Exception as exc:  # noqa: BLE001 - diagnostic artifact should report parse failures.
        warnings.append(f"registry cannot be parsed: {path}: {exc}")
    return entries


def _load_json_object(
    path: Path | None,
    label: str,
    warnings: list[str],
    blocking_reasons: list[str] | None = None,
    *,
    required: bool = False,
) -> dict[str, Any] | None:
    if path is None:
        return None
    if not Path(path).exists():
        message = f"{label} is missing: {path}"
        if required and blocking_reasons is not None:
            blocking_reasons.append(message)
        else:
            warnings.append(message)
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - diagnostic artifact should report parse failures.
        message = f"{label} cannot be parsed: {path}: {exc}"
        if required and blocking_reasons is not None:
            blocking_reasons.append(message)
        else:
            warnings.append(message)
        return None
    if not isinstance(payload, dict):
        warnings.append(f"{label} root is not a JSON object: {path}")
        return None
    return payload


def _load_optional(path: Path, loader: Any, label: str, blocking_reasons: list[str]) -> Any:
    if not Path(path).exists():
        return None
    try:
        return loader(Path(path))
    except Exception as exc:  # noqa: BLE001 - diagnostic artifact should report parse failures.
        blocking_reasons.append(f"{label} cannot be parsed: {path}: {exc}")
        return None


def _source_artifacts(old_manifest: dict[str, Any] | None, new_manifest: dict[str, Any] | None) -> dict[str, str | None]:
    return {
        "old_source_manifest_status": (old_manifest or {}).get("manifest_status"),
        "new_source_manifest_status": (new_manifest or {}).get("manifest_status"),
    }


def _input_paths(**paths: Path | None) -> dict[str, str | None]:
    return {key: (str(value) if value is not None else None) for key, value in paths.items()}


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _dedupe_dicts(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for value in values:
        key = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            result.append(value)
            seen.add(key)
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
