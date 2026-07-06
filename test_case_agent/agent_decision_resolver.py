from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.draft_mapping import (
    build_req_to_draft_map,
    draft_ids_for_req_uids,
    draft_mapping_entries_for_req_uids,
)
from test_case_agent.manual_decision_matrix import DecisionOption, ManualDecisionMatrix, load_manual_decision_matrix

CREATED_BY_TOOL = "test_case_agent.agent_decision_resolver"
AGENT_DECISION_RESOLUTION_PREFIX = "agent-decision-resolution"
DEFAULT_PACKAGE_ID = "WPKG-000001"
DEFAULT_BENCHMARK_NAME = "AutoFin WPKG-000001 agent decision benchmark"

ResolutionStatus = Literal["pass", "pass-with-warnings", "blocked"]
DecisionStatus = Literal["resolved", "resolved-with-warnings", "needs_human_review", "deferred", "rejected", "unsafe"]
Confidence = Literal["high", "medium", "low"]

STAGE_9E_ACTIONS = {"revise_draft", "replace_draft", "split_candidate", "extend_existing_tc"}
NON_STAGE_9E_ACTIONS = {"no_new_tc_with_rationale", "defer", "request_source_clarification", "keep_manual_only"}
SOURCE_BUSINESS_RULE_RE = re.compile(r"existing\s+tc.*business\s+(?:rule|source)|business\s+(?:rule|source).*existing\s+tc", re.I)


@dataclass(frozen=True)
class SourceFactCoverage:
    has_source_backed_object: bool
    has_source_backed_action: bool
    has_source_backed_oracle: bool
    has_source_backed_condition: bool
    has_table_or_anchor_evidence: bool
    has_real_table_context: bool
    facts_used: list[str]
    facts_missing: list[str]
    facts_ambiguous: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceFactCoverage":
        return cls(
            has_source_backed_object=bool(data.get("has_source_backed_object")),
            has_source_backed_action=bool(data.get("has_source_backed_action")),
            has_source_backed_oracle=bool(data.get("has_source_backed_oracle")),
            has_source_backed_condition=bool(data.get("has_source_backed_condition")),
            has_table_or_anchor_evidence=bool(data.get("has_table_or_anchor_evidence")),
            has_real_table_context=bool(data.get("has_real_table_context")),
            facts_used=list(data.get("facts_used") or []),
            facts_missing=list(data.get("facts_missing") or []),
            facts_ambiguous=list(data.get("facts_ambiguous") or []),
        )


@dataclass(frozen=True)
class DuplicateRiskAssessment:
    risk_level: str
    similar_existing_tc_refs: list[str]
    coverage_overlap_summary: str
    source_backed_difference: str | None
    existing_tc_used_only_as_coverage_evidence: bool
    recommended_resolution: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DuplicateRiskAssessment":
        return cls(
            risk_level=str(data.get("risk_level") or "low"),
            similar_existing_tc_refs=list(data.get("similar_existing_tc_refs") or []),
            coverage_overlap_summary=str(data.get("coverage_overlap_summary") or ""),
            source_backed_difference=data.get("source_backed_difference"),
            existing_tc_used_only_as_coverage_evidence=bool(
                data.get("existing_tc_used_only_as_coverage_evidence")
            ),
            recommended_resolution=str(data.get("recommended_resolution") or "needs_human_review"),
        )


@dataclass(frozen=True)
class AgentDecision:
    row_id: str
    cluster_id: str
    cluster_type: str
    selected_option_id: str
    selected_allowed_next_action: str
    decision_source: str
    decision_status: DecisionStatus
    confidence: Confidence
    confidence_score: float
    confidence_reasons: list[str]
    evidence: list[str]
    source_evidence_refs: list[str]
    source_fact_coverage: SourceFactCoverage
    existing_tc_coverage_evidence: list[dict[str, Any]]
    duplicate_risk_assessment: DuplicateRiskAssessment
    missing_facts: list[str]
    rationale: str
    normalized_effect: str
    affected_drafts: list[str]
    affected_requirements: list[str]
    draft_mapping_evidence: list[dict[str, Any]]
    requires_human_review: bool
    enables_stage_9e_draft_only: bool
    creates_or_edits_canonical_tc: bool
    safety_warnings: list[str]
    blocking_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "cluster_id": self.cluster_id,
            "cluster_type": self.cluster_type,
            "selected_option_id": self.selected_option_id,
            "selected_allowed_next_action": self.selected_allowed_next_action,
            "decision_source": self.decision_source,
            "decision_status": self.decision_status,
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "confidence_reasons": self.confidence_reasons,
            "evidence": self.evidence,
            "source_evidence_refs": self.source_evidence_refs,
            "source_fact_coverage": self.source_fact_coverage.to_dict(),
            "existing_tc_coverage_evidence": self.existing_tc_coverage_evidence,
            "duplicate_risk_assessment": self.duplicate_risk_assessment.to_dict(),
            "missing_facts": self.missing_facts,
            "rationale": self.rationale,
            "normalized_effect": self.normalized_effect,
            "affected_drafts": self.affected_drafts,
            "affected_requirements": self.affected_requirements,
            "draft_mapping_evidence": self.draft_mapping_evidence,
            "requires_human_review": self.requires_human_review,
            "enables_stage_9e_draft_only": self.enables_stage_9e_draft_only,
            "creates_or_edits_canonical_tc": self.creates_or_edits_canonical_tc,
            "safety_warnings": self.safety_warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDecision":
        return cls(
            row_id=str(data["row_id"]),
            cluster_id=str(data["cluster_id"]),
            cluster_type=str(data["cluster_type"]),
            selected_option_id=str(data["selected_option_id"]),
            selected_allowed_next_action=str(data["selected_allowed_next_action"]),
            decision_source=str(data["decision_source"]),
            decision_status=data["decision_status"],
            confidence=data["confidence"],
            confidence_score=float(data.get("confidence_score") or 0),
            confidence_reasons=list(data.get("confidence_reasons") or []),
            evidence=list(data.get("evidence") or []),
            source_evidence_refs=list(data.get("source_evidence_refs") or []),
            source_fact_coverage=SourceFactCoverage.from_dict(data.get("source_fact_coverage") or {}),
            existing_tc_coverage_evidence=list(data.get("existing_tc_coverage_evidence") or []),
            duplicate_risk_assessment=DuplicateRiskAssessment.from_dict(
                data.get("duplicate_risk_assessment") or {}
            ),
            missing_facts=list(data.get("missing_facts") or []),
            rationale=str(data["rationale"]),
            normalized_effect=str(data["normalized_effect"]),
            affected_drafts=list(data.get("affected_drafts") or []),
            affected_requirements=list(data.get("affected_requirements") or []),
            draft_mapping_evidence=list(data.get("draft_mapping_evidence") or []),
            requires_human_review=bool(data.get("requires_human_review")),
            enables_stage_9e_draft_only=bool(data.get("enables_stage_9e_draft_only")),
            creates_or_edits_canonical_tc=bool(data.get("creates_or_edits_canonical_tc")),
            safety_warnings=list(data.get("safety_warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


@dataclass(frozen=True)
class AgentDecisionResolution:
    package_id: str
    resolution_status: ResolutionStatus
    benchmark_name: str
    source_artifacts: dict[str, str | None]
    agent_decisions: list[AgentDecision]
    decision_summary: dict[str, Any]
    stage_9e_candidate_scope: dict[str, Any]
    deferred_or_human_review_scope: dict[str, Any]
    evidence_quality_summary: dict[str, Any]
    safety_summary: dict[str, Any]
    readiness_after_agent_resolution: dict[str, Any]
    stage_9e_gate: dict[str, Any]
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
            "resolution_status": self.resolution_status,
            "benchmark_name": self.benchmark_name,
            "source_artifacts": self.source_artifacts,
            "agent_decisions": [item.to_dict() for item in self.agent_decisions],
            "decision_summary": self.decision_summary,
            "stage_9e_candidate_scope": self.stage_9e_candidate_scope,
            "deferred_or_human_review_scope": self.deferred_or_human_review_scope,
            "evidence_quality_summary": self.evidence_quality_summary,
            "safety_summary": self.safety_summary,
            "readiness_after_agent_resolution": self.readiness_after_agent_resolution,
            "stage_9e_gate": self.stage_9e_gate,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDecisionResolution":
        return cls(
            package_id=str(data["package_id"]),
            resolution_status=data["resolution_status"],
            benchmark_name=str(data.get("benchmark_name") or ""),
            source_artifacts=dict(data.get("source_artifacts") or {}),
            agent_decisions=[AgentDecision.from_dict(item) for item in data.get("agent_decisions", [])],
            decision_summary=dict(data.get("decision_summary") or {}),
            stage_9e_candidate_scope=dict(data.get("stage_9e_candidate_scope") or {}),
            deferred_or_human_review_scope=dict(data.get("deferred_or_human_review_scope") or {}),
            evidence_quality_summary=dict(data.get("evidence_quality_summary") or {}),
            safety_summary=dict(data.get("safety_summary") or {}),
            readiness_after_agent_resolution=dict(data.get("readiness_after_agent_resolution") or {}),
            stage_9e_gate=dict(data.get("stage_9e_gate") or {}),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_agent_decision_resolution(
    *,
    package_id: str,
    matrix_path: Path,
    answer_template_path: Path | None = None,
    answer_validation_path: Path | None = None,
    decision_pack_path: Path | None = None,
    residual_analysis_path: Path | None = None,
    draft_proposal_path: Path | None = None,
    draft_review_path: Path | None = None,
    draft_revision_plan_path: Path | None = None,
    context_bundle_path: Path | None = None,
    improvement_plan_path: Path | None = None,
    benchmark_name: str = DEFAULT_BENCHMARK_NAME,
    created_by_tool: str = CREATED_BY_TOOL,
) -> AgentDecisionResolution:
    input_paths = _input_paths(
        matrix_path=matrix_path,
        answer_template_path=answer_template_path,
        answer_validation_path=answer_validation_path,
        decision_pack_path=decision_pack_path,
        residual_analysis_path=residual_analysis_path,
        draft_proposal_path=draft_proposal_path,
        draft_review_path=draft_review_path,
        draft_revision_plan_path=draft_revision_plan_path,
        context_bundle_path=context_bundle_path,
        improvement_plan_path=improvement_plan_path,
    )
    blocking_reasons = _missing_required_paths(
        matrix_path=matrix_path,
        decision_pack_path=decision_pack_path,
        residual_analysis_path=residual_analysis_path,
        draft_proposal_path=draft_proposal_path,
        draft_review_path=draft_review_path,
        draft_revision_plan_path=draft_revision_plan_path,
        context_bundle_path=context_bundle_path,
        improvement_plan_path=improvement_plan_path,
    )
    now = _utc_now()
    if blocking_reasons:
        return _blocked_resolution(
            package_id=package_id,
            benchmark_name=benchmark_name,
            input_paths=input_paths,
            blocking_reasons=blocking_reasons,
            created_at_utc=now,
            created_by_tool=created_by_tool,
        )

    matrix = load_manual_decision_matrix(Path(matrix_path))
    if matrix.package_id != package_id:
        blocking_reasons.append(f"package_id mismatch: expected {package_id}, got {matrix.package_id}")
    if matrix.canonical_write_allowed:
        blocking_reasons.append("manual decision matrix unexpectedly allows canonical writes")
    if blocking_reasons:
        return _blocked_resolution(
            package_id=package_id,
            benchmark_name=benchmark_name,
            input_paths=input_paths,
            blocking_reasons=blocking_reasons,
            created_at_utc=now,
            created_by_tool=created_by_tool,
        )

    context_bundle = _read_optional_json(context_bundle_path)
    decision_pack = _read_optional_json(decision_pack_path)
    residual = _read_optional_json(residual_analysis_path)
    draft_proposal = _read_optional_json(draft_proposal_path)
    draft_review = _read_optional_json(draft_review_path)
    draft_revision_plan = _read_optional_json(draft_revision_plan_path)
    improvement_plan = _read_optional_json(improvement_plan_path)

    req_context = _requirement_context(context_bundle)
    draft_context = _draft_context(draft_proposal, draft_review, draft_revision_plan, decision_pack)
    req_to_draft_map = build_req_to_draft_map(
        draft_proposal=draft_proposal,
        decision_pack=decision_pack,
        draft_review=draft_review,
        draft_revision_plan=draft_revision_plan,
        context_bundle=context_bundle,
    )
    residual_context = _residual_context(residual)
    cluster_by_id = {cluster.cluster_id: cluster for cluster in matrix.decision_clusters}

    decisions = [
        _resolve_row(
            row=row,
            cluster=cluster_by_id.get(row.cluster_id),
            req_context=req_context,
            draft_context=draft_context,
            req_to_draft_map=req_to_draft_map,
            residual_context=residual_context,
        )
        for row in matrix.reviewer_decision_rows
    ]

    decision_summary = _decision_summary(decisions, req_to_draft_map)
    stage_scope = _stage_9e_candidate_scope(decisions)
    deferred_scope = _deferred_or_human_review_scope(decisions)
    evidence_summary = _evidence_quality_summary(decisions)
    safety_summary = _safety_summary(decisions)
    readiness = _readiness(decisions)
    gate = _stage_9e_gate(decisions)
    warnings = _warnings(decisions, improvement_plan)
    status: ResolutionStatus = "pass"
    if warnings or any(dec.decision_status in {"needs_human_review", "deferred"} for dec in decisions):
        status = "pass-with-warnings"
    if any(dec.decision_status == "unsafe" for dec in decisions):
        status = "blocked"
    return AgentDecisionResolution(
        package_id=package_id,
        resolution_status=status,
        benchmark_name=benchmark_name,
        source_artifacts=dict(matrix.source_artifacts),
        agent_decisions=decisions,
        decision_summary=decision_summary,
        stage_9e_candidate_scope=stage_scope,
        deferred_or_human_review_scope=deferred_scope,
        evidence_quality_summary=evidence_summary,
        safety_summary=safety_summary,
        readiness_after_agent_resolution=readiness,
        stage_9e_gate=gate,
        canonical_write_allowed=False,
        manual_review_required=bool(deferred_scope["row_ids"] or any(dec.requires_human_review for dec in decisions)),
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=[],
        created_at_utc=now,
        created_by_tool=created_by_tool,
    )


def write_agent_decision_resolution(resolution: AgentDecisionResolution, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{AGENT_DECISION_RESOLUTION_PREFIX}-{resolution.package_id}.json"
    markdown_path = out_dir / f"{AGENT_DECISION_RESOLUTION_PREFIX}-{resolution.package_id}.md"
    json_path.write_text(json.dumps(resolution.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    markdown_path.write_text(render_agent_decision_resolution_markdown(resolution), encoding="utf-8-sig", newline="\n")
    return json_path, markdown_path


def load_agent_decision_resolution(path: Path) -> AgentDecisionResolution:
    return AgentDecisionResolution.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def render_agent_decision_resolution_markdown(resolution: AgentDecisionResolution) -> str:
    summary = resolution.decision_summary
    gate = resolution.stage_9e_gate
    lines = [
        f"# Agent Decision Resolution {resolution.package_id}",
        "",
        "Этот артефакт содержит agent_decision, а не reviewer answers и не human approval.",
        "",
        "## Summary",
        "",
        f"| Field | Value |",
        "| --- | --- |",
        f"| Resolution status | `{resolution.resolution_status}` |",
        f"| Rows total | `{summary.get('rows_total', 0)}` |",
        f"| Resolved | `{summary.get('resolved_rows', 0)}` |",
        f"| Resolved with warnings | `{summary.get('resolved_with_warnings_rows', 0)}` |",
        f"| Needs human review | `{summary.get('needs_human_review_rows', 0)}` |",
        f"| Deferred | `{summary.get('deferred_rows', 0)}` |",
        f"| Unsafe | `{summary.get('unsafe_rows', 0)}` |",
        f"| Stage 9E candidate rows | `{summary.get('stage_9e_candidate_rows', 0)}` |",
        f"| Req-to-draft mapped req_uids | `{summary.get('req_to_draft_map_count', 0)}` |",
        f"| Rows fixed by draft mapping | `{', '.join(summary.get('fixed_rows', [])) or '-'}` |",
        f"| Rows still missing affected drafts | `{', '.join(summary.get('rows_with_missing_affected_drafts', [])) or '-'}` |",
        f"| Stage 9E allowed | `{gate.get('stage_9e_allowed')}` |",
        f"| Canonical write allowed | `{resolution.canonical_write_allowed}` |",
        "",
        "## Decision Policy Used",
        "",
        "- Existing TC is coverage/comparison evidence only, never a source of business rules.",
        "- Stage 9E candidates must be draft-only, source-backed, confidence >= 0.70, and free of safety blockers.",
        "- Low-confidence, ambiguous, missing-action, or missing-oracle rows are routed to human review/defer.",
        "- Canonical TC creation/editing remains disabled.",
        "",
        "## Decision Summary Table",
        "",
        "| Total rows | Resolved | Needs human review | Deferred | Unsafe | Stage 9E candidate rows |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| `{summary.get('rows_total', 0)}` | `{summary.get('resolved_rows', 0) + summary.get('resolved_with_warnings_rows', 0)}` "
            f"| `{summary.get('needs_human_review_rows', 0)}` | `{summary.get('deferred_rows', 0)}` "
            f"| `{summary.get('unsafe_rows', 0)}` | `{summary.get('stage_9e_candidate_rows', 0)}` |"
        ),
        "",
        "## Agent Decision Table",
        "",
        "| Row ID | Cluster | Selected action | Decision status | Confidence | Affected drafts | Affected requirements | Rationale | Stage 9E candidate? | Human review required? |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for decision in resolution.agent_decisions:
        lines.append(
            "| {row} | {cluster} | `{action}` | `{status}` | `{score:.2f}` {confidence} | {drafts} | {reqs} | {rationale} | `{candidate}` | `{human}` |".format(
                row=decision.row_id,
                cluster=decision.cluster_type,
                action=decision.selected_allowed_next_action,
                status=decision.decision_status,
                score=decision.confidence_score,
                confidence=decision.confidence,
                drafts=", ".join(decision.affected_drafts) or "-",
                reqs=", ".join(decision.affected_requirements) or "-",
                rationale=_md_escape(_short(decision.rationale, 220)),
                candidate=decision.enables_stage_9e_draft_only,
                human=decision.requires_human_review,
            )
        )
    _decision_section(lines, "Duplicate-Risk Decisions", resolution.agent_decisions, "duplicate_risk")
    _decision_section(lines, "Source-Grounding Decisions", resolution.agent_decisions, "source_grounding")
    _decision_section(lines, "Defer/Human-Review Decisions", [
        decision
        for decision in resolution.agent_decisions
        if decision.decision_status in {"needs_human_review", "deferred"}
    ])
    lines.extend(
        [
            "## Stage 9E Gate",
            "",
            f"- stage_9e_allowed: `{gate.get('stage_9e_allowed')}`",
            f"- allowed rows: `{', '.join(gate.get('stage_9e_allowed_scope', {}).get('row_ids', [])) or '-'}`",
            f"- blockers: `{'; '.join(gate.get('stage_9e_blockers', [])) or '-'}`",
            "- safety conditions:",
        ]
    )
    for condition in gate.get("stage_9e_safety_conditions", []):
        lines.append(f"  - {condition}")
    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "No canonical test-cases are created or edited by this resolver. It does not produce reviewer answers JSON, does not create Stage 9E artifacts, and does not run apply.",
            "",
            "## Warnings / Blocking Reasons",
            "",
        ]
    )
    if resolution.warnings:
        lines.extend(f"- warning: {warning}" for warning in resolution.warnings)
    if resolution.blocking_reasons:
        lines.extend(f"- blocker: {reason}" for reason in resolution.blocking_reasons)
    if not resolution.warnings and not resolution.blocking_reasons:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _resolve_row(
    *,
    row: Any,
    cluster: Any,
    req_context: dict[str, dict[str, Any]],
    draft_context: dict[str, dict[str, Any]],
    req_to_draft_map: dict[str, list[dict[str, Any]]],
    residual_context: dict[str, dict[str, Any]],
) -> AgentDecision:
    cluster_type = str(getattr(cluster, "cluster_type", "mixed") if cluster else "mixed")
    options = list(row.decision_options)
    evidence = [row.evidence_summary]
    if cluster:
        evidence.extend(list(cluster.evidence or []))
    affected_drafts, draft_mapping_evidence, draft_mapping_warnings = _affected_drafts_for_row(row, req_to_draft_map)
    evidence.extend(_draft_mapping_evidence_lines(draft_mapping_evidence, draft_mapping_warnings))
    coverage = _source_fact_coverage(row.affected_requirements, affected_drafts, req_context, draft_context, residual_context)
    duplicate = _duplicate_risk_assessment(row, cluster)
    safety_warnings = _safety_warnings(row, cluster, evidence)
    selected = _select_option(row, cluster_type, coverage, duplicate, options, safety_warnings)
    status, score, reasons, rationale = _decision_status_and_confidence(
        selected=selected,
        cluster_type=cluster_type,
        coverage=coverage,
        duplicate=duplicate,
        safety_warnings=safety_warnings,
        row=row,
    )
    stage_mapping_blockers = _stage_9e_mapping_blockers(
        action=selected.allowed_next_action,
        req_uids=list(row.affected_requirements),
        affected_drafts=affected_drafts,
        req_to_draft_map=req_to_draft_map,
        row_had_affected_drafts=bool(row.affected_drafts),
    )
    if stage_mapping_blockers:
        score = min(score, 0.69)
        status = "needs_human_review"
        reasons = _unique([*reasons, *stage_mapping_blockers])
        rationale = rationale + " Stage 9E draft-only scope is disabled because draft mapping is incomplete."
    confidence = _confidence_label(score)
    if selected.allowed_next_action in STAGE_9E_ACTIONS and score < 0.70:
        status = "needs_human_review"
        rationale = (
            rationale
            + " Stage 9E draft-only scope is disabled because confidence is below 0.70 or source facts are incomplete."
        )
    enables_stage_9e = (
        selected.allowed_next_action in STAGE_9E_ACTIONS
        and status in {"resolved", "resolved-with-warnings"}
        and score >= 0.70
        and not safety_warnings
    )
    blocking_reasons = list(safety_warnings) if status == "unsafe" else []
    return AgentDecision(
        row_id=row.row_id,
        cluster_id=row.cluster_id,
        cluster_type=cluster_type,
        selected_option_id=selected.option_id,
        selected_allowed_next_action=selected.allowed_next_action,
        decision_source="agent_resolution",
        decision_status=status,
        confidence=confidence,
        confidence_score=round(score, 2),
        confidence_reasons=reasons,
        evidence=evidence,
        source_evidence_refs=list(row.source_evidence_refs or row.affected_requirements),
        source_fact_coverage=coverage,
        existing_tc_coverage_evidence=_existing_tc_evidence(row),
        duplicate_risk_assessment=duplicate,
        missing_facts=sorted(set(coverage.facts_missing)),
        rationale=rationale,
        normalized_effect=_normalized_effect(selected.allowed_next_action),
        affected_drafts=affected_drafts,
        affected_requirements=list(row.affected_requirements),
        draft_mapping_evidence=draft_mapping_evidence,
        requires_human_review=status in {"needs_human_review", "deferred", "unsafe"} or score < 0.85,
        enables_stage_9e_draft_only=enables_stage_9e,
        creates_or_edits_canonical_tc=False,
        safety_warnings=safety_warnings,
        blocking_reasons=blocking_reasons,
    )


def _select_option(
    row: Any,
    cluster_type: str,
    coverage: SourceFactCoverage,
    duplicate: DuplicateRiskAssessment,
    options: list[DecisionOption],
    safety_warnings: list[str],
) -> DecisionOption:
    by_action = {option.allowed_next_action: option for option in options}
    if safety_warnings:
        return _fallback_option(options, ("defer", "request_source_clarification", "keep_manual_only"))
    if cluster_type == "duplicate_risk":
        if duplicate.risk_level == "low" and _source_complete(coverage):
            if not duplicate.similar_existing_tc_refs and "revise_draft" in by_action:
                return by_action["revise_draft"]
            if "no_new_tc_with_rationale" in by_action and duplicate.similar_existing_tc_refs:
                return by_action["no_new_tc_with_rationale"]
            if "revise_draft" in by_action:
                return by_action["revise_draft"]
        return _fallback_option(options, ("defer", "keep_manual_only", "request_source_clarification"))
    if cluster_type == "source_grounding":
        if _source_complete(coverage):
            if len(row.affected_requirements) > 1 and "split_candidate" in by_action:
                return by_action["split_candidate"]
            if "revise_draft" in by_action:
                return by_action["revise_draft"]
        return _fallback_option(options, ("request_source_clarification", "defer", "keep_manual_only"))
    if cluster_type == "replacement_strategy":
        if _source_complete(coverage):
            if len(row.affected_requirements) > 1 and "split_candidate" in by_action:
                return by_action["split_candidate"]
            if "replace_draft" in by_action:
                return by_action["replace_draft"]
        return _fallback_option(options, ("defer", "request_source_clarification", "keep_manual_only"))
    if cluster_type == "defer_or_no_new_tc":
        return _fallback_option(options, ("keep_manual_only", "defer", "request_source_clarification"))
    return _fallback_option(options, ("defer", "keep_manual_only", "request_source_clarification"))


def _affected_drafts_for_row(
    row: Any,
    req_to_draft_map: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    row_drafts = _unique(row.affected_drafts)
    mapping_entries = draft_mapping_entries_for_req_uids(row.affected_requirements, req_to_draft_map, min_confidence="medium")
    if row_drafts:
        return row_drafts, mapping_entries, _draft_mapping_warnings(row.affected_requirements, req_to_draft_map)
    mapped_drafts = draft_ids_for_req_uids(row.affected_requirements, req_to_draft_map, min_confidence="medium")
    return (
        mapped_drafts,
        [{**entry, "used_to_fill_missing_affected_drafts": True} for entry in mapping_entries],
        _draft_mapping_warnings(row.affected_requirements, req_to_draft_map),
    )


def _draft_mapping_warnings(
    req_uids: list[str],
    req_to_draft_map: dict[str, list[dict[str, Any]]],
) -> list[str]:
    warnings = []
    for req_uid in req_uids:
        if not draft_mapping_entries_for_req_uids([req_uid], req_to_draft_map, min_confidence="medium"):
            warnings.append(f"draft_mapping_missing: {req_uid}")
    return warnings


def _draft_mapping_evidence_lines(mapping_entries: list[dict[str, Any]], warnings: list[str]) -> list[str]:
    lines = [
        "draft_mapping: "
        + str(entry.get("draft_id"))
        + " from "
        + str(entry.get("source"))
        + " confidence="
        + str(entry.get("confidence"))
        for entry in mapping_entries
    ]
    lines.extend(warnings)
    return _unique(lines)


def _stage_9e_mapping_blockers(
    *,
    action: str,
    req_uids: list[str],
    affected_drafts: list[str],
    req_to_draft_map: dict[str, list[dict[str, Any]]],
    row_had_affected_drafts: bool,
) -> list[str]:
    if action not in STAGE_9E_ACTIONS:
        return []
    if row_had_affected_drafts:
        return []
    blockers = []
    if not affected_drafts:
        blockers.append("Stage 9E candidate has no high/medium req-to-draft mapping")
    unmapped = [
        req_uid
        for req_uid in req_uids
        if not draft_mapping_entries_for_req_uids([req_uid], req_to_draft_map, min_confidence="medium")
    ]
    if unmapped:
        blockers.append("Stage 9E candidate has unmapped affected requirements: " + ", ".join(unmapped))
    return blockers


def _decision_status_and_confidence(
    *,
    selected: DecisionOption,
    cluster_type: str,
    coverage: SourceFactCoverage,
    duplicate: DuplicateRiskAssessment,
    safety_warnings: list[str],
    row: Any,
) -> tuple[DecisionStatus, float, list[str], str]:
    if selected.creates_or_edits_canonical_tc:
        return (
            "unsafe",
            0.0,
            ["selected option would create or edit canonical TC"],
            "Agent marked this row unsafe because selected option implies canonical TC writes.",
        )
    if safety_warnings:
        return (
            "unsafe",
            0.49,
            safety_warnings,
            "Agent marked this row unsafe because safety policy would be violated.",
        )

    score = 0.58
    reasons: list[str] = []
    if coverage.has_source_backed_object:
        score += 0.08
        reasons.append("source-backed object present")
    if coverage.has_source_backed_action:
        score += 0.10
        reasons.append("source-backed action present")
    if coverage.has_source_backed_oracle:
        score += 0.12
        reasons.append("source-backed observable oracle present")
    if coverage.has_table_or_anchor_evidence:
        score += 0.04
        reasons.append("source anchor/table evidence present")
    if coverage.has_real_table_context:
        score += 0.04
        reasons.append("real table context present")
    if coverage.facts_missing:
        score = min(score, 0.69)
        reasons.append("missing facts cap confidence")
    if duplicate.risk_level == "high":
        score = min(score, 0.69)
        reasons.append("high duplicate risk caps confidence")
    elif duplicate.risk_level == "medium" and selected.allowed_next_action in STAGE_9E_ACTIONS:
        score = min(score, 0.76)
        reasons.append("medium duplicate risk caps draft-only confidence")
    if selected.allowed_next_action == "no_new_tc_with_rationale":
        if duplicate.similar_existing_tc_refs and duplicate.risk_level in {"low", "medium"} and not coverage.facts_missing:
            score = max(score, 0.80)
            reasons.append("coverage evidence supports no-new-TC resolution")
        else:
            score = min(score, 0.69)
            reasons.append("no-new-TC lacks strong coverage evidence")
    if selected.allowed_next_action in {"defer", "request_source_clarification", "keep_manual_only"}:
        score = min(score, 0.69)
    score = max(0.0, min(1.0, score))

    if selected.allowed_next_action == "defer":
        return (
            "deferred",
            score,
            reasons or ["deferred by conservative policy"],
            "Agent deferred this row because source/duplicate evidence is insufficient for a safe autonomous decision.",
        )
    if selected.allowed_next_action in {"request_source_clarification", "keep_manual_only"}:
        return (
            "needs_human_review",
            score,
            reasons or ["manual judgment required"],
            "Agent requires human review because the row needs clarification or manual judgment not derivable from source artifacts.",
        )
    if selected.allowed_next_action in STAGE_9E_ACTIONS and score >= 0.70:
        status: DecisionStatus = "resolved-with-warnings" if score < 0.85 else "resolved"
        return (
            status,
            score,
            reasons,
            f"Agent can route this row to draft-only {selected.allowed_next_action} with source-backed traceability and no canonical writes.",
        )
    if selected.allowed_next_action == "no_new_tc_with_rationale" and score >= 0.80:
        return (
            "resolved",
            score,
            reasons,
            "Agent resolved this row as no-new-TC because existing TC evidence appears sufficient coverage-only evidence.",
        )
    return (
        "needs_human_review",
        min(score, 0.69),
        reasons or ["confidence below Stage 9E threshold"],
        "Agent did not resolve this row because confidence is below the safe autonomous threshold.",
    )


def _source_fact_coverage(
    req_uids: list[str],
    draft_ids: list[str],
    req_context: dict[str, dict[str, Any]],
    draft_context: dict[str, dict[str, Any]],
    residual_context: dict[str, dict[str, Any]],
) -> SourceFactCoverage:
    facts_used: list[str] = []
    facts_missing: list[str] = []
    facts_ambiguous: list[str] = []
    has_object = False
    has_action = False
    has_oracle = False
    has_condition = False
    has_anchor = False
    has_table = False

    for req_uid in req_uids:
        req = req_context.get(req_uid) or {}
        residual = residual_context.get(req_uid) or {}
        source_text = _first_text(req, ("source_text", "normalized_text", "expected_behavior", "object"))
        if _first_text(req, ("field_name", "object")) or source_text:
            has_object = True
            facts_used.append(f"{req_uid}: object/source text")
        if _first_text(req, ("user_action", "action")) or _looks_actionable(source_text):
            has_action = True
            facts_used.append(f"{req_uid}: action")
        if _first_text(req, ("expected_behavior", "source_text", "normalized_text")):
            has_oracle = True
            facts_used.append(f"{req_uid}: oracle")
        if _first_text(req, ("condition",)):
            has_condition = True
            facts_used.append(f"{req_uid}: condition")
        if req.get("source_anchors"):
            has_anchor = True
        if req.get("table_source_contexts"):
            has_table = True
        facts_missing.extend(str(item) for item in residual.get("missing_facts", []) if item)
        facts_ambiguous.extend(str(item) for item in residual.get("facts_ambiguous", []) if item)

    for draft_id in draft_ids:
        draft = draft_context.get(draft_id) or {}
        if draft.get("coverage_intent"):
            has_oracle = True
            facts_used.append(f"{draft_id}: coverage intent")
        for missing in draft.get("missing_facts", []):
            facts_missing.append(str(missing))
        for warning in draft.get("warnings", []):
            if "ambiguous" in str(warning).casefold():
                facts_ambiguous.append(str(warning))

    normalized_missing = _normalize_missing_facts(facts_missing)
    if any(_missing_action(item) for item in normalized_missing):
        has_action = False
    if any(_missing_oracle(item) for item in normalized_missing):
        has_oracle = False
    return SourceFactCoverage(
        has_source_backed_object=has_object,
        has_source_backed_action=has_action,
        has_source_backed_oracle=has_oracle,
        has_source_backed_condition=has_condition,
        has_table_or_anchor_evidence=has_anchor or has_table,
        has_real_table_context=has_table,
        facts_used=sorted(set(facts_used)),
        facts_missing=normalized_missing,
        facts_ambiguous=sorted(set(facts_ambiguous)),
    )


def _duplicate_risk_assessment(row: Any, cluster: Any) -> DuplicateRiskAssessment:
    similar_refs = list(row.existing_tc_evidence_refs or [])
    risk = "low"
    if cluster and getattr(cluster, "similar_existing_tc_refs", None):
        similar_refs = list(cluster.similar_existing_tc_refs or similar_refs)
    if cluster and getattr(cluster, "cluster_type", "") == "duplicate_risk":
        risk = _risk_from_evidence(list(getattr(cluster, "evidence", []) or []) + [str(row.evidence_summary)])
    elif similar_refs:
        risk = "medium"
    if "high" in risk:
        recommended = "needs_human_review"
    elif similar_refs:
        recommended = "no_new_tc_with_rationale"
    else:
        recommended = "separate_new_tc"
    return DuplicateRiskAssessment(
        risk_level=risk,
        similar_existing_tc_refs=similar_refs,
        coverage_overlap_summary=(
            "Similar existing TC refs are available as coverage-only evidence."
            if similar_refs
            else "No similar existing TC refs are present."
        ),
        source_backed_difference=None,
        existing_tc_used_only_as_coverage_evidence=True,
        recommended_resolution=recommended,
    )


def _risk_from_evidence(evidence: list[str]) -> str:
    text = " ".join(evidence).casefold()
    if "risk=high" in text or "risk: high" in text:
        return "high"
    if "risk=medium" in text or "risk: medium" in text:
        return "medium"
    if "risk=low" in text or "risk: low" in text:
        return "low"
    return "medium"


def _existing_tc_evidence(row: Any) -> list[dict[str, Any]]:
    return [
        {
            "ref": ref,
            "evidence_role": "coverage_comparison_only",
            "used_as_business_rule_source": False,
        }
        for ref in row.existing_tc_evidence_refs
    ]


def _safety_warnings(row: Any, cluster: Any, evidence: list[str]) -> list[str]:
    warnings = []
    text = " ".join(evidence)
    if SOURCE_BUSINESS_RULE_RE.search(text):
        warnings.append("existing TC evidence appears to be used as a business-rule source")
    for option in row.decision_options:
        if option.creates_or_edits_canonical_tc:
            warnings.append(f"row option {option.option_id} would create or edit canonical TC")
    return warnings


def _source_complete(coverage: SourceFactCoverage) -> bool:
    return (
        coverage.has_source_backed_object
        and coverage.has_source_backed_action
        and coverage.has_source_backed_oracle
        and not coverage.facts_missing
        and not coverage.facts_ambiguous
    )


def _fallback_option(options: list[DecisionOption], preferred_actions: tuple[str, ...]) -> DecisionOption:
    by_action = {option.allowed_next_action: option for option in options}
    for action in preferred_actions:
        if action in by_action:
            return by_action[action]
    return options[-1]


def _requirement_context(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for item in bundle.get("candidate_requirements") or []:
        req_uid = item.get("req_uid")
        if not req_uid:
            continue
        enriched = item.get("enriched_source_facts") or {}
        table_contexts = item.get("table_source_contexts") or []
        first_table = table_contexts[0] if table_contexts else {}
        row_cells = first_table.get("row_cells") or []
        result[str(req_uid)] = {
            **item,
            "field_name": row_cells[0] if row_cells else item.get("object"),
            "user_action": enriched.get("user_action") or _first_from(first_table.get("action_candidates")),
            "condition": item.get("condition") or enriched.get("condition") or _first_from(first_table.get("condition_candidates")),
            "expected_behavior": item.get("expected_behavior")
            or enriched.get("expected_behavior")
            or _first_from(first_table.get("expected_behavior_candidates")),
        }
    return result


def _draft_context(
    proposal: dict[str, Any],
    review: dict[str, Any],
    revision_plan: dict[str, Any],
    decision_pack: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for draft in proposal.get("draft_test_cases") or []:
        draft_id = draft.get("draft_id")
        if draft_id:
            result[str(draft_id)] = {
                "coverage_intent": draft.get("coverage_intent"),
                "warnings": list(draft.get("warnings") or []),
                "missing_facts": _draft_missing_facts(draft),
            }
    for item in review.get("draft_reviews") or []:
        result.setdefault(str(item.get("draft_id")), {}).setdefault("warnings", []).extend(item.get("issues") or [])
        result.setdefault(str(item.get("draft_id")), {}).setdefault("missing_facts", []).extend(item.get("required_fixes") or [])
    for item in revision_plan.get("revision_items") or []:
        result.setdefault(str(item.get("draft_id")), {}).setdefault("warnings", []).extend(item.get("warnings") or [])
    for item in decision_pack.get("source_grounding_resolutions") or []:
        draft_id = item.get("draft_id")
        if draft_id:
            result.setdefault(str(draft_id), {}).setdefault("missing_facts", []).extend(
                item.get("missing_source_facts") or item.get("missing_facts") or []
            )
    return {key: value for key, value in result.items() if key and key != "None"}


def _residual_context(residual: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in residual.get("requirement_gap_analyses") or []:
        req_uid = item.get("req_uid")
        if req_uid:
            result[str(req_uid)] = {
                "missing_facts": item.get("missing_facts") or [],
                "facts_ambiguous": item.get("ambiguous_facts") or [],
            }
    return result


def _draft_missing_facts(draft: dict[str, Any]) -> list[str]:
    missing = []
    for profile in draft.get("source_grounding_profiles") or []:
        missing.extend(profile.get("missing_facts") or [])
    missing.extend(draft.get("manual_questions") or [])
    return [str(item) for item in missing if item]


def _normalize_missing_facts(values: list[str]) -> list[str]:
    normalized = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        lowered = text.casefold()
        if "not executable until" in lowered:
            continue
        if "populate all required draft review fields" in lowered:
            continue
        normalized.append(text)
    return sorted(set(normalized))


def _missing_action(value: str) -> bool:
    lowered = value.casefold()
    return "action" in lowered or "user action" in lowered


def _missing_oracle(value: str) -> bool:
    lowered = value.casefold()
    return "oracle" in lowered or "expected" in lowered or "observable expected" in lowered


def _first_text(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _first_from(values: Any) -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    if isinstance(values, str):
        return values
    return ""


def _looks_actionable(value: str) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in ("при нажат", "нажать", "выбрать", "ввести", "открыть", "проверить"))


def _confidence_label(score: float) -> Confidence:
    if score >= 0.85:
        return "high"
    if score >= 0.70:
        return "medium"
    return "low"


def _normalized_effect(action: str) -> str:
    if action in STAGE_9E_ACTIONS:
        return "may_prepare_stage_9e_draft_only"
    if action == "no_new_tc_with_rationale":
        return "close_candidate_without_new_tc"
    if action == "request_source_clarification":
        return "request_source_clarification"
    if action == "keep_manual_only":
        return "needs_human_review"
    return action


def _decision_summary(
    decisions: list[AgentDecision],
    req_to_draft_map: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    status_counts = Counter(dec.decision_status for dec in decisions)
    rows_with_missing_affected_drafts = [
        decision.row_id for decision in decisions if decision.affected_requirements and not decision.affected_drafts
    ]
    unmapped_req_uids = sorted(
        {
            req_uid
            for decision in decisions
            for req_uid in decision.affected_requirements
            if not draft_mapping_entries_for_req_uids([req_uid], req_to_draft_map, min_confidence="medium")
        }
    )
    fixed_rows = sorted(
        {
            decision.row_id
            for decision in decisions
            if any(entry.get("used_to_fill_missing_affected_drafts") for entry in decision.draft_mapping_evidence)
        }
    )
    return {
        "rows_total": len(decisions),
        "resolved_rows": status_counts.get("resolved", 0),
        "resolved_with_warnings_rows": status_counts.get("resolved-with-warnings", 0),
        "needs_human_review_rows": status_counts.get("needs_human_review", 0),
        "deferred_rows": status_counts.get("deferred", 0),
        "rejected_rows": status_counts.get("rejected", 0),
        "unsafe_rows": status_counts.get("unsafe", 0),
        "stage_9e_candidate_rows": sum(1 for decision in decisions if decision.enables_stage_9e_draft_only),
        "selected_action_counts": dict(Counter(dec.selected_allowed_next_action for dec in decisions)),
        "draft_mapping_diagnostics": {
            "req_to_draft_map_count": len(req_to_draft_map),
            "req_to_draft_entry_count": sum(len(entries) for entries in req_to_draft_map.values()),
            "unmapped_req_uids": unmapped_req_uids,
            "rows_with_missing_affected_drafts": rows_with_missing_affected_drafts,
            "fixed_rows": fixed_rows,
        },
        "req_to_draft_map_count": len(req_to_draft_map),
        "unmapped_req_uids": unmapped_req_uids,
        "rows_with_missing_affected_drafts": rows_with_missing_affected_drafts,
        "fixed_rows": fixed_rows,
    }


def _stage_9e_candidate_scope(decisions: list[AgentDecision]) -> dict[str, Any]:
    candidates = [decision for decision in decisions if decision.enables_stage_9e_draft_only]
    return {
        "row_ids": [decision.row_id for decision in candidates],
        "draft_ids": sorted({draft for decision in candidates for draft in decision.affected_drafts}),
        "requirement_uids": sorted({req for decision in candidates for req in decision.affected_requirements}),
        "allowed_actions": sorted({decision.selected_allowed_next_action for decision in candidates}),
        "requires_draft_only_output": True,
    }


def _deferred_or_human_review_scope(decisions: list[AgentDecision]) -> dict[str, Any]:
    rows = [decision for decision in decisions if decision.decision_status in {"needs_human_review", "deferred", "unsafe"}]
    return {
        "row_ids": [decision.row_id for decision in rows],
        "draft_ids": sorted({draft for decision in rows for draft in decision.affected_drafts}),
        "requirement_uids": sorted({req for decision in rows for req in decision.affected_requirements}),
        "status_counts": dict(Counter(decision.decision_status for decision in rows)),
    }


def _evidence_quality_summary(decisions: list[AgentDecision]) -> dict[str, Any]:
    return {
        "rows_with_source_object": sum(1 for decision in decisions if decision.source_fact_coverage.has_source_backed_object),
        "rows_with_source_action": sum(1 for decision in decisions if decision.source_fact_coverage.has_source_backed_action),
        "rows_with_source_oracle": sum(1 for decision in decisions if decision.source_fact_coverage.has_source_backed_oracle),
        "rows_with_table_or_anchor_evidence": sum(
            1 for decision in decisions if decision.source_fact_coverage.has_table_or_anchor_evidence
        ),
        "rows_with_missing_facts": sum(1 for decision in decisions if decision.source_fact_coverage.facts_missing),
        "coverage_only_existing_tc_evidence": all(
            evidence.get("evidence_role") == "coverage_comparison_only"
            for decision in decisions
            for evidence in decision.existing_tc_coverage_evidence
        ),
    }


def _safety_summary(decisions: list[AgentDecision]) -> dict[str, Any]:
    return {
        "canonical_write_allowed": False,
        "any_decision_creates_or_edits_canonical_tc": any(
            decision.creates_or_edits_canonical_tc for decision in decisions
        ),
        "unsafe_rows": [decision.row_id for decision in decisions if decision.decision_status == "unsafe"],
        "safety_warnings_count": sum(len(decision.safety_warnings) for decision in decisions),
        "existing_tc_used_only_as_coverage_evidence": all(
            decision.duplicate_risk_assessment.existing_tc_used_only_as_coverage_evidence for decision in decisions
        ),
    }


def _readiness(decisions: list[AgentDecision]) -> dict[str, Any]:
    stage_rows = [decision for decision in decisions if decision.enables_stage_9e_draft_only]
    blockers = []
    if not stage_rows:
        blockers.append("no safe agent_decision rows enable draft-only Stage 9E")
    unsafe = [decision.row_id for decision in decisions if decision.decision_status == "unsafe"]
    if unsafe:
        blockers.append(f"unsafe rows present: {', '.join(unsafe)}")
    return {
        "rows_total": len(decisions),
        "resolved_rows": sum(1 for decision in decisions if decision.decision_status == "resolved"),
        "resolved_with_warnings_rows": sum(1 for decision in decisions if decision.decision_status == "resolved-with-warnings"),
        "needs_human_review_rows": sum(1 for decision in decisions if decision.decision_status == "needs_human_review"),
        "deferred_rows": sum(1 for decision in decisions if decision.decision_status == "deferred"),
        "unsafe_rows": len(unsafe),
        "stage_9e_candidate_rows": len(stage_rows),
        "stage_9e_candidate_drafts": sorted({draft for decision in stage_rows for draft in decision.affected_drafts}),
        "can_prepare_stage_9e_draft_only": bool(stage_rows and not unsafe),
        "why_not_ready": blockers,
        "required_next_action": "prepare_stage_9e_draft_only_for_allowed_scope" if stage_rows and not unsafe else "resolve_human_review_or_deferred_rows",
    }


def _stage_9e_gate(decisions: list[AgentDecision]) -> dict[str, Any]:
    stage_scope = _stage_9e_candidate_scope(decisions)
    blockers = []
    stage_decisions = [decision for decision in decisions if decision.enables_stage_9e_draft_only]
    if not stage_decisions:
        blockers.append("no stage_9e_candidate_rows")
    if any(decision.confidence_score < 0.70 for decision in stage_decisions):
        blockers.append("stage_9e candidate below confidence threshold")
    if any(decision.safety_warnings for decision in stage_decisions):
        blockers.append("stage_9e candidate has safety warnings")
    if any(not decision.source_evidence_refs for decision in stage_decisions):
        blockers.append("stage_9e candidate lacks source evidence refs")
    return {
        "stage_9e_allowed": bool(stage_decisions and not blockers),
        "stage_9e_allowed_scope": stage_scope,
        "stage_9e_blockers": blockers,
        "stage_9e_safety_conditions": [
            "draft-only output",
            "agent_decision row traceability required",
            "canonical_write_allowed=false",
            "no low-confidence rows in Stage 9E scope",
            "no reviewer answer artifact is implied",
        ],
        "canonical_write_allowed": False,
        "requires_draft_only_output": True,
        "requires_agent_decision_traceability": True,
        "requires_no_low_confidence_rows": True,
    }


def _unique(values: Any) -> list[str]:
    result = []
    seen = set()
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _warnings(decisions: list[AgentDecision], improvement_plan: dict[str, Any]) -> list[str]:
    warnings = []
    if any(decision.decision_status in {"needs_human_review", "deferred"} for decision in decisions):
        warnings.append("Some rows remain outside agent-resolved safe scope and require human review or defer handling.")
    if any(decision.decision_status == "unsafe" for decision in decisions):
        warnings.append("Unsafe rows were detected; Stage 9E must not proceed until resolved.")
    if improvement_plan.get("plan_status") == "pass-with-warnings":
        warnings.append("Agent capability improvement plan still has warnings; resolver remains conservative.")
    return warnings


def _blocked_resolution(
    *,
    package_id: str,
    benchmark_name: str,
    input_paths: dict[str, str | None],
    blocking_reasons: list[str],
    created_at_utc: str,
    created_by_tool: str,
) -> AgentDecisionResolution:
    return AgentDecisionResolution(
        package_id=package_id,
        resolution_status="blocked",
        benchmark_name=benchmark_name,
        source_artifacts={},
        agent_decisions=[],
        decision_summary={
            "rows_total": 0,
            "resolved_rows": 0,
            "resolved_with_warnings_rows": 0,
            "needs_human_review_rows": 0,
            "deferred_rows": 0,
            "unsafe_rows": 0,
            "stage_9e_candidate_rows": 0,
        },
        stage_9e_candidate_scope={"row_ids": [], "draft_ids": [], "requirement_uids": []},
        deferred_or_human_review_scope={"row_ids": [], "draft_ids": [], "requirement_uids": []},
        evidence_quality_summary={},
        safety_summary={"canonical_write_allowed": False},
        readiness_after_agent_resolution={
            "rows_total": 0,
            "stage_9e_candidate_rows": 0,
            "can_prepare_stage_9e_draft_only": False,
            "why_not_ready": blocking_reasons,
            "required_next_action": "fix_blocking_inputs",
        },
        stage_9e_gate={
            "stage_9e_allowed": False,
            "stage_9e_allowed_scope": {"row_ids": [], "draft_ids": [], "requirement_uids": []},
            "stage_9e_blockers": blocking_reasons,
            "canonical_write_allowed": False,
            "requires_draft_only_output": True,
            "requires_agent_decision_traceability": True,
            "requires_no_low_confidence_rows": True,
        },
        canonical_write_allowed=False,
        manual_review_required=True,
        input_paths=input_paths,
        warnings=[],
        blocking_reasons=blocking_reasons,
        created_at_utc=created_at_utc,
        created_by_tool=created_by_tool,
    )


def _missing_required_paths(**paths: Path | None) -> list[str]:
    required = {
        "matrix_path",
        "decision_pack_path",
        "residual_analysis_path",
        "draft_proposal_path",
        "draft_review_path",
        "draft_revision_plan_path",
        "context_bundle_path",
        "improvement_plan_path",
    }
    reasons = []
    for name, path in paths.items():
        if name not in required:
            continue
        if path is None:
            reasons.append(f"{name} is required")
        elif not Path(path).exists():
            reasons.append(f"{name} is missing: {path}")
    return reasons


def _input_paths(**paths: Path | None) -> dict[str, str | None]:
    return {name: str(path) if path is not None else None for name, path in paths.items()}


def _read_optional_json(path: Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _decision_section(lines: list[str], title: str, decisions: list[AgentDecision], cluster_type: str | None = None) -> None:
    selected = [decision for decision in decisions if cluster_type is None or decision.cluster_type == cluster_type]
    lines.extend(["", f"## {title}", ""])
    if not selected:
        lines.append("- none")
        return
    for decision in selected:
        lines.append(
            f"- `{decision.row_id}`: `{decision.selected_allowed_next_action}` / `{decision.decision_status}` / confidence `{decision.confidence_score:.2f}`. {_short(decision.rationale, 260)}"
        )


def _md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _short(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"
