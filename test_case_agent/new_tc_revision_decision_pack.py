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
    load_new_tc_draft_proposal,
)
from test_case_agent.new_tc_draft_review import (
    DraftTestCaseReview,
    NewTcDraftReviewReport,
    load_new_tc_draft_review,
)
from test_case_agent.new_tc_draft_revision_plan import (
    DraftRevisionItem,
    NewTcDraftRevisionPlan,
    load_new_tc_draft_revision_plan,
)

CREATED_BY_TOOL = "test_case_agent.new_tc_revision_decision_pack"
DECISION_PACK_PREFIX = "new-tc-revision-decision-pack"
DEFAULT_PACKAGE_ID = "WPKG-000001"

DecisionPackStatus = Literal["pass", "pass-with-warnings", "blocked"]
DraftDecisionName = Literal[
    "revise_ready",
    "replace_ready",
    "defer",
    "maybe_extend_existing_tc",
    "needs_manual_decision",
]
GroundingStatus = Literal["resolved", "partially_resolved", "unresolved"]
RiskLevel = Literal["low", "medium", "high"]
ClusterAction = Literal["differentiate", "maybe_extend_existing_tc", "defer", "no_action"]
ComparisonDecision = Literal[
    "separate_new_tc_possible",
    "likely_duplicate",
    "maybe_extend_existing_tc",
    "insufficient_info",
]
ReplacementMode = Literal["rewrite_from_source", "split_into_multiple_drafts", "defer", "maybe_extend_existing_tc"]
CapabilityArea = Literal[
    "duplicate_risk_handling",
    "source_grounding",
    "draft_quality",
    "replacement_strategy",
    "manual_decision_flow",
    "safety_gate",
]
CapabilityStatus = Literal["works", "partial", "gap"]

TC_HEADING_RE = re.compile(r"^(#{2,6})\s+(TC-[A-Za-z0-9][A-Za-z0-9_-]*)\b[:\-\s]*(.*)$")
REF_RE = re.compile(
    r"\b(?:REQ-[A-Z0-9-]+|ATOM-[A-Z0-9-]+|BSR\s+\d+|GSR\s+\d+|SRC-[A-Z0-9-]+|GAP-\d+|DICT-[A-Z0-9-]+|WP-\d+)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]{4,}")
AGGREGATE_MARKERS = [
    "assembled_from",
    "test_case_count",
    "aggregate",
    "порядок сборки",
    "source files assembled",
]


@dataclass(frozen=True)
class DraftDecision:
    draft_id: str
    proposed_tc_id: str
    current_review_status: str
    revision_plan_target: str
    decision: DraftDecisionName
    decision_reason: str
    candidate_req_uids: list[str]
    source_req_ids: list[str]
    duplicate_risk_cluster_ids: list[str]
    source_grounding_status: GroundingStatus
    duplicate_risk_status: GroundingStatus
    revision_instruction: str
    replacement_instruction: str | None
    manual_questions: list[str]
    acceptance_criteria: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "proposed_tc_id": self.proposed_tc_id,
            "current_review_status": self.current_review_status,
            "revision_plan_target": self.revision_plan_target,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "candidate_req_uids": self.candidate_req_uids,
            "source_req_ids": self.source_req_ids,
            "duplicate_risk_cluster_ids": self.duplicate_risk_cluster_ids,
            "source_grounding_status": self.source_grounding_status,
            "duplicate_risk_status": self.duplicate_risk_status,
            "revision_instruction": self.revision_instruction,
            "replacement_instruction": self.replacement_instruction,
            "manual_questions": self.manual_questions,
            "acceptance_criteria": self.acceptance_criteria,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DraftDecision":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            current_review_status=str(data["current_review_status"]),
            revision_plan_target=str(data["revision_plan_target"]),
            decision=data["decision"],
            decision_reason=str(data["decision_reason"]),
            candidate_req_uids=list(data.get("candidate_req_uids") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            duplicate_risk_cluster_ids=list(data.get("duplicate_risk_cluster_ids") or []),
            source_grounding_status=data["source_grounding_status"],
            duplicate_risk_status=data["duplicate_risk_status"],
            revision_instruction=str(data["revision_instruction"]),
            replacement_instruction=data.get("replacement_instruction"),
            manual_questions=list(data.get("manual_questions") or []),
            acceptance_criteria=list(data.get("acceptance_criteria") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class DuplicateRiskCluster:
    cluster_id: str
    cluster_reason: str
    draft_ids: list[str]
    candidate_req_uids: list[str]
    similar_tc_ids: list[str]
    similar_file_paths: list[str]
    risk: RiskLevel
    cluster_action: ClusterAction
    rationale: str
    manual_decision_required: bool
    comparison_required: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_reason": self.cluster_reason,
            "draft_ids": self.draft_ids,
            "candidate_req_uids": self.candidate_req_uids,
            "similar_tc_ids": self.similar_tc_ids,
            "similar_file_paths": self.similar_file_paths,
            "risk": self.risk,
            "cluster_action": self.cluster_action,
            "rationale": self.rationale,
            "manual_decision_required": self.manual_decision_required,
            "comparison_required": self.comparison_required,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DuplicateRiskCluster":
        return cls(
            cluster_id=str(data["cluster_id"]),
            cluster_reason=str(data["cluster_reason"]),
            draft_ids=list(data.get("draft_ids") or []),
            candidate_req_uids=list(data.get("candidate_req_uids") or []),
            similar_tc_ids=list(data.get("similar_tc_ids") or []),
            similar_file_paths=list(data.get("similar_file_paths") or []),
            risk=data["risk"],
            cluster_action=data["cluster_action"],
            rationale=str(data["rationale"]),
            manual_decision_required=bool(data.get("manual_decision_required")),
            comparison_required=bool(data.get("comparison_required")),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class ExistingTcComparison:
    comparison_id: str
    draft_id: str | None
    candidate_req_uid: str | None
    similar_tc_id: str
    similar_file_path: str
    candidate_behavior: str
    existing_tc_summary: str
    overlap_points: list[str]
    difference_points: list[str]
    decision: ComparisonDecision
    rationale: str
    manual_questions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "draft_id": self.draft_id,
            "candidate_req_uid": self.candidate_req_uid,
            "similar_tc_id": self.similar_tc_id,
            "similar_file_path": self.similar_file_path,
            "candidate_behavior": self.candidate_behavior,
            "existing_tc_summary": self.existing_tc_summary,
            "overlap_points": self.overlap_points,
            "difference_points": self.difference_points,
            "decision": self.decision,
            "rationale": self.rationale,
            "manual_questions": self.manual_questions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExistingTcComparison":
        return cls(
            comparison_id=str(data["comparison_id"]),
            draft_id=data.get("draft_id"),
            candidate_req_uid=data.get("candidate_req_uid"),
            similar_tc_id=str(data["similar_tc_id"]),
            similar_file_path=str(data["similar_file_path"]),
            candidate_behavior=str(data["candidate_behavior"]),
            existing_tc_summary=str(data["existing_tc_summary"]),
            overlap_points=list(data.get("overlap_points") or []),
            difference_points=list(data.get("difference_points") or []),
            decision=data["decision"],
            rationale=str(data["rationale"]),
            manual_questions=list(data.get("manual_questions") or []),
        )


@dataclass(frozen=True)
class SourceGroundingResolution:
    draft_id: str
    req_uid: str
    source_req_id: str | None
    usable_source_facts: list[str]
    missing_source_facts: list[str]
    resolved_instruction: str
    can_support_executable_steps: bool
    can_support_observable_expected_result: bool
    manual_question: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "req_uid": self.req_uid,
            "source_req_id": self.source_req_id,
            "usable_source_facts": self.usable_source_facts,
            "missing_source_facts": self.missing_source_facts,
            "resolved_instruction": self.resolved_instruction,
            "can_support_executable_steps": self.can_support_executable_steps,
            "can_support_observable_expected_result": self.can_support_observable_expected_result,
            "manual_question": self.manual_question,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceGroundingResolution":
        return cls(
            draft_id=str(data["draft_id"]),
            req_uid=str(data["req_uid"]),
            source_req_id=data.get("source_req_id"),
            usable_source_facts=list(data.get("usable_source_facts") or []),
            missing_source_facts=list(data.get("missing_source_facts") or []),
            resolved_instruction=str(data["resolved_instruction"]),
            can_support_executable_steps=bool(data.get("can_support_executable_steps")),
            can_support_observable_expected_result=bool(data.get("can_support_observable_expected_result")),
            manual_question=data.get("manual_question"),
        )


@dataclass(frozen=True)
class ReplacementStrategy:
    draft_id: str
    proposed_tc_id: str
    reason_for_replacement: str
    candidate_req_uids: list[str]
    replacement_allowed: bool
    replacement_mode: ReplacementMode
    replacement_guidance: list[str]
    required_source_facts: list[str]
    manual_questions: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "proposed_tc_id": self.proposed_tc_id,
            "reason_for_replacement": self.reason_for_replacement,
            "candidate_req_uids": self.candidate_req_uids,
            "replacement_allowed": self.replacement_allowed,
            "replacement_mode": self.replacement_mode,
            "replacement_guidance": self.replacement_guidance,
            "required_source_facts": self.required_source_facts,
            "manual_questions": self.manual_questions,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplacementStrategy":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            reason_for_replacement=str(data["reason_for_replacement"]),
            candidate_req_uids=list(data.get("candidate_req_uids") or []),
            replacement_allowed=bool(data.get("replacement_allowed")),
            replacement_mode=data["replacement_mode"],
            replacement_guidance=list(data.get("replacement_guidance") or []),
            required_source_facts=list(data.get("required_source_facts") or []),
            manual_questions=list(data.get("manual_questions") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class RevisedDraftReadiness:
    ready_for_revised_draft_proposal: bool
    revise_ready_count: int
    replace_ready_count: int
    defer_count: int
    maybe_extend_existing_count: int
    needs_manual_decision_count: int
    unresolved_duplicate_risk_count: int
    unresolved_source_grounding_count: int
    blocking_question_count: int
    readiness_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready_for_revised_draft_proposal": self.ready_for_revised_draft_proposal,
            "revise_ready_count": self.revise_ready_count,
            "replace_ready_count": self.replace_ready_count,
            "defer_count": self.defer_count,
            "maybe_extend_existing_count": self.maybe_extend_existing_count,
            "needs_manual_decision_count": self.needs_manual_decision_count,
            "unresolved_duplicate_risk_count": self.unresolved_duplicate_risk_count,
            "unresolved_source_grounding_count": self.unresolved_source_grounding_count,
            "blocking_question_count": self.blocking_question_count,
            "readiness_reason": self.readiness_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RevisedDraftReadiness":
        return cls(
            ready_for_revised_draft_proposal=bool(data.get("ready_for_revised_draft_proposal")),
            revise_ready_count=int(data.get("revise_ready_count") or 0),
            replace_ready_count=int(data.get("replace_ready_count") or 0),
            defer_count=int(data.get("defer_count") or 0),
            maybe_extend_existing_count=int(data.get("maybe_extend_existing_count") or 0),
            needs_manual_decision_count=int(data.get("needs_manual_decision_count") or 0),
            unresolved_duplicate_risk_count=int(data.get("unresolved_duplicate_risk_count") or 0),
            unresolved_source_grounding_count=int(data.get("unresolved_source_grounding_count") or 0),
            blocking_question_count=int(data.get("blocking_question_count") or 0),
            readiness_reason=str(data["readiness_reason"]),
        )


@dataclass(frozen=True)
class AgentCapabilityFinding:
    finding_id: str
    capability_area: CapabilityArea
    status: CapabilityStatus
    evidence: dict[str, Any]
    recommendation: str
    should_update_agent_instructions: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "capability_area": self.capability_area,
            "status": self.status,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "should_update_agent_instructions": self.should_update_agent_instructions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentCapabilityFinding":
        return cls(
            finding_id=str(data["finding_id"]),
            capability_area=data["capability_area"],
            status=data["status"],
            evidence=dict(data.get("evidence") or {}),
            recommendation=str(data["recommendation"]),
            should_update_agent_instructions=bool(data.get("should_update_agent_instructions")),
        )


@dataclass
class NewTcRevisionDecisionPack:
    package_id: str
    decision_pack_status: DecisionPackStatus
    source_revision_plan_path: str
    source_review_path: str
    source_proposal_path: str
    draft_decisions: list[DraftDecision]
    duplicate_risk_clusters: list[DuplicateRiskCluster]
    existing_tc_comparisons: list[ExistingTcComparison]
    source_grounding_resolutions: list[SourceGroundingResolution]
    replacement_strategies: list[ReplacementStrategy]
    manual_decisions_required: list[dict[str, Any]]
    revised_draft_readiness: RevisedDraftReadiness
    agent_capability_findings: list[AgentCapabilityFinding]
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
            "decision_pack_status": self.decision_pack_status,
            "source_revision_plan_path": self.source_revision_plan_path,
            "source_review_path": self.source_review_path,
            "source_proposal_path": self.source_proposal_path,
            "draft_decisions": [item.to_dict() for item in self.draft_decisions],
            "duplicate_risk_clusters": [item.to_dict() for item in self.duplicate_risk_clusters],
            "existing_tc_comparisons": [item.to_dict() for item in self.existing_tc_comparisons],
            "source_grounding_resolutions": [item.to_dict() for item in self.source_grounding_resolutions],
            "replacement_strategies": [item.to_dict() for item in self.replacement_strategies],
            "manual_decisions_required": self.manual_decisions_required,
            "revised_draft_readiness": self.revised_draft_readiness.to_dict(),
            "agent_capability_findings": [item.to_dict() for item in self.agent_capability_findings],
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcRevisionDecisionPack":
        return cls(
            package_id=str(data["package_id"]),
            decision_pack_status=data["decision_pack_status"],
            source_revision_plan_path=str(data["source_revision_plan_path"]),
            source_review_path=str(data["source_review_path"]),
            source_proposal_path=str(data["source_proposal_path"]),
            draft_decisions=[DraftDecision.from_dict(item) for item in data.get("draft_decisions", [])],
            duplicate_risk_clusters=[
                DuplicateRiskCluster.from_dict(item) for item in data.get("duplicate_risk_clusters", [])
            ],
            existing_tc_comparisons=[
                ExistingTcComparison.from_dict(item) for item in data.get("existing_tc_comparisons", [])
            ],
            source_grounding_resolutions=[
                SourceGroundingResolution.from_dict(item)
                for item in data.get("source_grounding_resolutions", [])
            ],
            replacement_strategies=[
                ReplacementStrategy.from_dict(item) for item in data.get("replacement_strategies", [])
            ],
            manual_decisions_required=list(data.get("manual_decisions_required") or []),
            revised_draft_readiness=RevisedDraftReadiness.from_dict(data["revised_draft_readiness"]),
            agent_capability_findings=[
                AgentCapabilityFinding.from_dict(item) for item in data.get("agent_capability_findings", [])
            ],
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


@dataclass(frozen=True)
class ParsedTcBlock:
    test_case_id: str
    file_path: str
    title: str | None
    traceability_line: str | None
    refs: list[str]
    steps_summary: str
    expected_result_summary: str
    text: str


def build_new_tc_revision_decision_pack(
    *,
    package_id: str,
    revision_plan_path: Path,
    draft_review_path: Path,
    draft_proposal_path: Path,
    context_bundle_path: Path,
    test_cases_dir: Path,
    revision_plan_markdown_path: Path | None = None,
    draft_review_markdown_path: Path | None = None,
    draft_proposal_markdown_path: Path | None = None,
    context_bundle_markdown_path: Path | None = None,
    requirements_diff_path: Path | None = None,
    impact_report_path: Path | None = None,
    update_plan_path: Path | None = None,
    old_registry_path: Path | None = None,
    new_registry_path: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> NewTcRevisionDecisionPack:
    input_paths = _input_paths(
        revision_plan_path=revision_plan_path,
        revision_plan_markdown_path=revision_plan_markdown_path,
        draft_review_path=draft_review_path,
        draft_review_markdown_path=draft_review_markdown_path,
        draft_proposal_path=draft_proposal_path,
        draft_proposal_markdown_path=draft_proposal_markdown_path,
        context_bundle_path=context_bundle_path,
        context_bundle_markdown_path=context_bundle_markdown_path,
        requirements_diff_path=requirements_diff_path,
        impact_report_path=impact_report_path,
        update_plan_path=update_plan_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
        test_cases_dir=test_cases_dir,
    )
    warnings: list[str] = []
    blocking_reasons: list[str] = []

    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"this decision pack is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    for label, path in {
        "revision plan": revision_plan_path,
        "draft review": draft_review_path,
        "draft proposal": draft_proposal_path,
        "context bundle": context_bundle_path,
        "test-cases dir": test_cases_dir,
    }.items():
        path = Path(path)
        if label == "test-cases dir":
            if not path.exists() or not path.is_dir():
                blocking_reasons.append(f"{label} is missing: {path}")
        elif not path.exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    plan = _load_optional(revision_plan_path, load_new_tc_draft_revision_plan, "revision plan", blocking_reasons)
    review = _load_optional(draft_review_path, load_new_tc_draft_review, "draft review", blocking_reasons)
    proposal = _load_optional(draft_proposal_path, load_new_tc_draft_proposal, "draft proposal", blocking_reasons)
    bundle = _load_optional(context_bundle_path, load_create_new_tc_context_bundle, "context bundle", blocking_reasons)

    if plan is not None and plan.package_id != package_id:
        blocking_reasons.append(f"revision plan package_id mismatch: {plan.package_id} != {package_id}")
    if review is not None and review.package_id != package_id:
        blocking_reasons.append(f"draft review package_id mismatch: {review.package_id} != {package_id}")
    if proposal is not None and proposal.package_id != package_id:
        blocking_reasons.append(f"draft proposal package_id mismatch: {proposal.package_id} != {package_id}")
    if bundle is not None and bundle.package_id != package_id:
        blocking_reasons.append(f"context bundle package_id mismatch: {bundle.package_id} != {package_id}")
    if proposal is not None and proposal.package_type != "create_new_candidate":
        blocking_reasons.append(f"draft proposal package_type must be create_new_candidate; got {proposal.package_type}.")

    for label, artifact in {
        "revision plan": plan,
        "draft review": review,
        "draft proposal": proposal,
        "context bundle": bundle,
    }.items():
        if artifact is not None:
            artifact_blockers = list(getattr(artifact, "blocking_reasons", []) or [])
            if artifact_blockers:
                blocking_reasons.append(f"{label} has blocking reasons: {'; '.join(artifact_blockers)}")

    if blocking_reasons or plan is None or review is None or proposal is None or bundle is None:
        return _pack(
            package_id=package_id,
            source_revision_plan_path=str(revision_plan_path),
            source_review_path=str(draft_review_path),
            source_proposal_path=str(draft_proposal_path),
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    warnings.extend(plan.warnings)
    warnings.extend(review.warnings)
    warnings.extend(proposal.warnings)
    warnings.extend(bundle.warnings)

    candidate_by_req = {candidate.req_uid: candidate for candidate in bundle.candidate_requirements if candidate.req_uid}
    draft_by_id = {draft.draft_id: draft for draft in proposal.draft_test_cases}
    review_by_draft = {item.draft_id: item for item in review.draft_reviews}
    plan_item_by_draft = {item.draft_id: item for item in plan.revision_items}
    clusters = _duplicate_risk_clusters(plan, draft_by_id, candidate_by_req)
    cluster_ids_by_draft = _cluster_ids_by_draft(clusters)
    tc_blocks, tc_warnings = _read_referenced_tc_blocks(clusters, Path(test_cases_dir))
    warnings.extend(tc_warnings)
    comparisons = _existing_tc_comparisons(plan, draft_by_id, candidate_by_req, tc_blocks)
    source_resolutions = _source_grounding_resolutions(plan, candidate_by_req)
    source_resolutions_by_draft = _source_resolutions_by_draft(source_resolutions)
    comparisons_by_draft = _comparisons_by_draft(comparisons)
    replacement_strategies = _replacement_strategies(
        plan,
        draft_by_id,
        candidate_by_req,
        source_resolutions_by_draft,
        comparisons_by_draft,
    )
    replacements_by_draft = {strategy.draft_id: strategy for strategy in replacement_strategies}
    draft_decisions = [
        _draft_decision(
            draft=draft,
            review=review_by_draft.get(draft.draft_id),
            plan_item=plan_item_by_draft.get(draft.draft_id),
            cluster_ids=cluster_ids_by_draft.get(draft.draft_id, []),
            clusters=clusters,
            source_resolutions=source_resolutions_by_draft.get(draft.draft_id, []),
            comparisons=comparisons_by_draft.get(draft.draft_id, []),
            replacement=replacements_by_draft.get(draft.draft_id),
        )
        for draft in proposal.draft_test_cases
    ]
    manual_decisions = _manual_decisions(draft_decisions, clusters, comparisons, source_resolutions, replacement_strategies)

    if len(draft_decisions) != len(proposal.draft_test_cases):
        blocking_reasons.append("draft decision count does not match proposal draft count.")

    return _pack(
        package_id=package_id,
        source_revision_plan_path=str(revision_plan_path),
        source_review_path=str(draft_review_path),
        source_proposal_path=str(draft_proposal_path),
        draft_decisions=draft_decisions,
        duplicate_risk_clusters=clusters,
        existing_tc_comparisons=comparisons,
        source_grounding_resolutions=source_resolutions,
        replacement_strategies=replacement_strategies,
        manual_decisions_required=manual_decisions,
        input_paths=input_paths,
        warnings=_unique(warnings),
        blocking_reasons=_unique(blocking_reasons),
        created_by_tool=created_by_tool,
    )


def write_new_tc_revision_decision_pack(
    pack: NewTcRevisionDecisionPack,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{DECISION_PACK_PREFIX}-{pack.package_id}.json"
    markdown_path = out_dir / f"{DECISION_PACK_PREFIX}-{pack.package_id}.md"
    json_path.write_text(json.dumps(pack.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_new_tc_revision_decision_pack_markdown(pack), encoding="utf-8", newline="\n")
    return json_path, markdown_path


def load_new_tc_revision_decision_pack(path: Path) -> NewTcRevisionDecisionPack:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("New TC revision decision pack root must be a JSON object.")
    return NewTcRevisionDecisionPack.from_dict(payload)


def render_new_tc_revision_decision_pack_markdown(pack: NewTcRevisionDecisionPack) -> str:
    readiness = pack.revised_draft_readiness
    lines = [
        f"# New TC Revision Decision Pack {pack.package_id}",
        "",
        "## Summary",
        "",
        f"- Decision pack status: `{pack.decision_pack_status}`",
        f"- Draft decisions: `{len(pack.draft_decisions)}`",
        f"- Duplicate-risk clusters: `{len(pack.duplicate_risk_clusters)}`",
        f"- Existing TC comparisons: `{len(pack.existing_tc_comparisons)}`",
        f"- Source grounding resolutions: `{len(pack.source_grounding_resolutions)}`",
        f"- Replacement strategies: `{len(pack.replacement_strategies)}`",
        f"- Agent capability findings: `{len(pack.agent_capability_findings)}`",
        f"- Ready for revised draft proposal: `{str(readiness.ready_for_revised_draft_proposal).lower()}`",
        f"- Canonical write allowed: `{str(pack.canonical_write_allowed).lower()}`",
        f"- Manual review required: `{str(pack.manual_review_required).lower()}`",
        f"- Warnings: `{len(pack.warnings)}`",
        f"- Blocking reasons: `{len(pack.blocking_reasons)}`",
        "",
        "## Safety Statement",
        "",
        "- Read-only decision-pack artifact.",
        "- No canonical TC was created.",
        "- No canonical TC was edited.",
        "- No revised draft proposal was created.",
        "- No apply command or patch application is authorized.",
        "",
        "## Revised Draft Readiness",
        "",
        f"- Revise ready: `{readiness.revise_ready_count}`",
        f"- Replace ready: `{readiness.replace_ready_count}`",
        f"- Defer: `{readiness.defer_count}`",
        f"- Maybe extend existing: `{readiness.maybe_extend_existing_count}`",
        f"- Needs manual decision: `{readiness.needs_manual_decision_count}`",
        f"- Unresolved duplicate risks: `{readiness.unresolved_duplicate_risk_count}`",
        f"- Unresolved source grounding: `{readiness.unresolved_source_grounding_count}`",
        f"- Blocking questions: `{readiness.blocking_question_count}`",
        f"- Reason: {readiness.readiness_reason}",
        "",
        "## Draft Decisions",
        "",
        "| Draft | Proposed TC | Review | Target | Decision | Source | Duplicate |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for decision in pack.draft_decisions:
        lines.append(
            f"| `{decision.draft_id}` | `{decision.proposed_tc_id}` | `{decision.current_review_status}` | "
            f"`{decision.revision_plan_target}` | `{decision.decision}` | "
            f"`{decision.source_grounding_status}` | `{decision.duplicate_risk_status}` |"
        )
    lines.extend(["", "## Duplicate Risk Clusters", ""])
    for cluster in pack.duplicate_risk_clusters:
        lines.append(
            f"- `{cluster.cluster_id}` risk `{cluster.risk}` action `{cluster.cluster_action}` "
            f"drafts `{', '.join(cluster.draft_ids)}` similar TC `{', '.join(cluster.similar_tc_ids)}`"
        )
    if not pack.duplicate_risk_clusters:
        lines.append("- none")
    lines.extend(["", "## Existing TC Comparisons", ""])
    for comparison in pack.existing_tc_comparisons[:50]:
        lines.append(
            f"- `{comparison.comparison_id}` `{comparison.draft_id or 'n/a'}` vs "
            f"`{comparison.similar_tc_id}`: `{comparison.decision}` - {comparison.rationale}"
        )
    if len(pack.existing_tc_comparisons) > 50:
        lines.append(f"- ... {len(pack.existing_tc_comparisons) - 50} more comparisons in JSON")
    if not pack.existing_tc_comparisons:
        lines.append("- none")
    lines.extend(["", "## Replacement Strategies", ""])
    for strategy in pack.replacement_strategies:
        lines.append(
            f"- `{strategy.draft_id}` `{strategy.replacement_mode}` allowed "
            f"`{str(strategy.replacement_allowed).lower()}`: {strategy.reason_for_replacement}"
        )
    if not pack.replacement_strategies:
        lines.append("- none")
    lines.extend(["", "## Agent Capability Findings", ""])
    lines.append("| Area | Status | Update Instructions | Recommendation |")
    lines.append("| --- | --- | --- | --- |")
    for finding in pack.agent_capability_findings:
        lines.append(
            f"| `{finding.capability_area}` | `{finding.status}` | "
            f"`{str(finding.should_update_agent_instructions).lower()}` | {finding.recommendation} |"
        )
        lines.append("")
        lines.append(f"Evidence for `{finding.finding_id}`:")
        for key, value in finding.evidence.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    if not pack.agent_capability_findings:
        lines.append("- none")
    lines.extend(["", "## Manual Decisions Required", ""])
    for decision in pack.manual_decisions_required:
        lines.append(f"- `{decision.get('scope')}` `{decision.get('id')}`: {decision.get('question')}")
    if not pack.manual_decisions_required:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    _append_list(lines, pack.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, pack.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _duplicate_risk_clusters(
    plan: NewTcDraftRevisionPlan,
    draft_by_id: dict[str, DraftTestCaseCandidate],
    candidate_by_req: dict[str, CandidateRequirement],
) -> list[DuplicateRiskCluster]:
    grouped: dict[tuple[str, str, str, str], list[Any]] = defaultdict(list)
    for action in plan.duplicate_risk_actions:
        candidate = candidate_by_req.get(action.candidate_req_uid or "")
        object_key = _norm_key(candidate.object if candidate else "")
        behavior_key = _norm_key(candidate.expected_behavior or candidate.normalized_text if candidate else "")
        source_key = _norm_key(candidate.source_req_id if candidate else "")
        draft_key = action.draft_id or ""
        key = (draft_key, action.candidate_req_uid or "", source_key, object_key or behavior_key)
        grouped[key].append(action)

    clusters: list[DuplicateRiskCluster] = []
    for index, (_key, actions) in enumerate(sorted(grouped.items(), key=lambda item: item[0]), start=1):
        risks = [action.risk for action in actions]
        risk = _max_risk(risks)
        action_names = [action.action for action in actions]
        cluster_action = _cluster_action(risk, action_names)
        draft_ids = _unique(action.draft_id for action in actions if action.draft_id)
        candidate_req_uids = _unique(action.candidate_req_uid for action in actions if action.candidate_req_uid)
        warnings: list[str] = []
        for draft_id in draft_ids:
            if draft_id not in draft_by_id:
                warnings.append(f"draft not found in proposal: {draft_id}")
        clusters.append(
            DuplicateRiskCluster(
                cluster_id=f"DRC-{index:06d}",
                cluster_reason="Grouped by draft, candidate requirement, source id and candidate behavior; similar TCs are aggregated for compact review.",
                draft_ids=draft_ids,
                candidate_req_uids=candidate_req_uids,
                similar_tc_ids=_unique(action.similar_tc_id for action in actions),
                similar_file_paths=_unique(action.similar_file_path for action in actions),
                risk=risk,
                cluster_action=cluster_action,
                rationale="; ".join(_unique(action.rationale for action in actions))[:1000],
                manual_decision_required=cluster_action in {"differentiate", "maybe_extend_existing_tc", "defer"},
                comparison_required=risk in {"medium", "high"},
                warnings=warnings,
            )
        )
    return clusters


def _existing_tc_comparisons(
    plan: NewTcDraftRevisionPlan,
    draft_by_id: dict[str, DraftTestCaseCandidate],
    candidate_by_req: dict[str, CandidateRequirement],
    tc_blocks: dict[tuple[str, str], ParsedTcBlock],
) -> list[ExistingTcComparison]:
    comparisons: list[ExistingTcComparison] = []
    seen: set[tuple[str | None, str | None, str, str]] = set()
    for action in plan.duplicate_risk_actions:
        key = (action.draft_id, action.candidate_req_uid, action.similar_file_path, action.similar_tc_id)
        if key in seen:
            continue
        seen.add(key)
        candidate = candidate_by_req.get(action.candidate_req_uid or "")
        block = tc_blocks.get((_path_key(action.similar_file_path), action.similar_tc_id))
        comparisons.append(_compare_existing_tc(len(comparisons) + 1, action, candidate, block))
    return comparisons


def _compare_existing_tc(
    index: int,
    action: Any,
    candidate: CandidateRequirement | None,
    block: ParsedTcBlock | None,
) -> ExistingTcComparison:
    candidate_behavior = _candidate_behavior(candidate)
    if block is None:
        return ExistingTcComparison(
            comparison_id=f"ETC-{index:06d}",
            draft_id=action.draft_id,
            candidate_req_uid=action.candidate_req_uid,
            similar_tc_id=action.similar_tc_id,
            similar_file_path=action.similar_file_path,
            candidate_behavior=candidate_behavior,
            existing_tc_summary="TC block could not be read from the referenced file.",
            overlap_points=[],
            difference_points=[],
            decision="insufficient_info",
            rationale="Referenced similar TC is unavailable for read-only comparison.",
            manual_questions=["Confirm whether the referenced existing TC already covers this candidate requirement."],
        )
    candidate_terms = _keywords(candidate_behavior)
    existing_text = " ".join([block.title or "", block.traceability_line or "", block.steps_summary, block.expected_result_summary])
    existing_terms = _keywords(existing_text)
    overlap_terms = sorted(candidate_terms & existing_terms)
    difference_terms = sorted(candidate_terms - existing_terms)
    source_ref_overlap = bool(candidate and candidate.source_req_id and candidate.source_req_id.upper() in block.refs)
    if source_ref_overlap and not difference_terms:
        decision: ComparisonDecision = "likely_duplicate"
        rationale = "Existing TC traceability and text overlap the candidate behavior."
    elif source_ref_overlap or len(overlap_terms) >= 3:
        decision = "maybe_extend_existing_tc"
        rationale = "Existing TC overlaps materially; manual decision is needed before creating a separate TC."
    elif difference_terms and len(overlap_terms) <= 1 and candidate and candidate.expected_behavior:
        decision = "separate_new_tc_possible"
        rationale = "Candidate has source-backed behavior that is not apparent in the existing TC summary."
    else:
        decision = "insufficient_info"
        rationale = "The artifacts do not prove whether this is distinct or duplicate coverage."
    manual_questions = [] if decision == "separate_new_tc_possible" else [
        "Decide whether to create a separate new TC or extend/defer due to existing coverage overlap."
    ]
    return ExistingTcComparison(
        comparison_id=f"ETC-{index:06d}",
        draft_id=action.draft_id,
        candidate_req_uid=action.candidate_req_uid,
        similar_tc_id=action.similar_tc_id,
        similar_file_path=action.similar_file_path,
        candidate_behavior=candidate_behavior,
        existing_tc_summary=_existing_summary(block),
        overlap_points=overlap_terms[:20] + (["source_req_id traceability overlap"] if source_ref_overlap else []),
        difference_points=difference_terms[:20],
        decision=decision,
        rationale=rationale,
        manual_questions=manual_questions,
    )


def _source_grounding_resolutions(
    plan: NewTcDraftRevisionPlan,
    candidate_by_req: dict[str, CandidateRequirement],
) -> list[SourceGroundingResolution]:
    resolutions: list[SourceGroundingResolution] = []
    seen: set[tuple[str, str]] = set()
    for action in plan.source_grounding_actions:
        key = (action.draft_id, action.req_uid)
        if key in seen:
            continue
        seen.add(key)
        candidate = candidate_by_req.get(action.req_uid)
        usable = _candidate_usable_facts(candidate) if candidate else list(action.usable_facts)
        missing = _candidate_missing_facts(candidate) if candidate else ["candidate requirement is missing from context bundle"]
        can_steps = not any(item in missing for item in ["source-backed navigation/action condition", "specific object/field/screen"])
        can_expected = "observable expected behavior" not in missing
        manual_question = None
        if not can_steps or not can_expected:
            manual_question = (
                f"Provide missing source facts for {action.req_uid}: {', '.join(missing)}."
            )
        resolutions.append(
            SourceGroundingResolution(
                draft_id=action.draft_id,
                req_uid=action.req_uid,
                source_req_id=candidate.source_req_id if candidate else None,
                usable_source_facts=usable,
                missing_source_facts=missing,
                resolved_instruction=_resolved_instruction(candidate, missing),
                can_support_executable_steps=can_steps,
                can_support_observable_expected_result=can_expected,
                manual_question=manual_question,
            )
        )
    return resolutions


def _replacement_strategies(
    plan: NewTcDraftRevisionPlan,
    draft_by_id: dict[str, DraftTestCaseCandidate],
    candidate_by_req: dict[str, CandidateRequirement],
    source_resolutions_by_draft: dict[str, list[SourceGroundingResolution]],
    comparisons_by_draft: dict[str, list[ExistingTcComparison]],
) -> list[ReplacementStrategy]:
    strategies: list[ReplacementStrategy] = []
    for item in plan.revision_items:
        if item.target_revision_status != "replace":
            continue
        draft = draft_by_id.get(item.draft_id)
        resolutions = source_resolutions_by_draft.get(item.draft_id, [])
        comparisons = comparisons_by_draft.get(item.draft_id, [])
        grounded = bool(resolutions) and all(
            resolution.can_support_executable_steps and resolution.can_support_observable_expected_result
            for resolution in resolutions
        )
        maybe_duplicate = any(comparison.decision in {"likely_duplicate", "maybe_extend_existing_tc"} for comparison in comparisons)
        if maybe_duplicate:
            allowed = False
            mode: ReplacementMode = "maybe_extend_existing_tc"
            questions = ["Confirm whether existing TC should be extended instead of replacing this draft."]
        elif grounded:
            allowed = True
            mode = "rewrite_from_source"
            questions = []
        else:
            allowed = False
            mode = "defer"
            questions = [
                "Replacement requires source facts that are currently missing; resolve grounding before revised draft."
            ]
        candidate_req_uids = list(draft.source_requirement_uids if draft else [])
        required_facts = []
        for req_uid in candidate_req_uids:
            candidate = candidate_by_req.get(req_uid)
            required_facts.extend(_candidate_usable_facts(candidate))
        strategies.append(
            ReplacementStrategy(
                draft_id=item.draft_id,
                proposed_tc_id=item.proposed_tc_id,
                reason_for_replacement="; ".join(item.required_fixes[:3]) or "Stage 9C rejected this draft.",
                candidate_req_uids=candidate_req_uids,
                replacement_allowed=allowed,
                replacement_mode=mode,
                replacement_guidance=[
                    "Do not edit the rejected draft in place.",
                    "Build the replacement from source facts and review findings only.",
                    "Keep canonical writes disabled until a later controlled create stage.",
                ],
                required_source_facts=_unique(required_facts),
                manual_questions=questions,
                warnings=item.warnings,
            )
        )
    return strategies


def _draft_decision(
    *,
    draft: DraftTestCaseCandidate,
    review: DraftTestCaseReview | None,
    plan_item: DraftRevisionItem | None,
    cluster_ids: list[str],
    clusters: list[DuplicateRiskCluster],
    source_resolutions: list[SourceGroundingResolution],
    comparisons: list[ExistingTcComparison],
    replacement: ReplacementStrategy | None,
) -> DraftDecision:
    current_status = review.review_status if review else "missing_review"
    target = plan_item.target_revision_status if plan_item else "missing_plan"
    source_status = _source_status(source_resolutions)
    duplicate_status = _duplicate_status(cluster_ids, clusters, comparisons)
    manual_questions = []
    if plan_item:
        manual_questions.extend(plan_item.blocking_questions)
    manual_questions.extend(resolution.manual_question for resolution in source_resolutions if resolution.manual_question)
    for comparison in comparisons:
        manual_questions.extend(comparison.manual_questions)
    if target == "replace" and replacement is not None:
        manual_questions.extend(replacement.manual_questions)

    if source_status == "unresolved":
        decision: DraftDecisionName = "needs_manual_decision"
        reason = "Source facts do not support executable steps or observable expected result."
    elif duplicate_status == "unresolved":
        decision = "needs_manual_decision"
        reason = "Duplicate risk remains unresolved after read-only comparison."
    elif any(comparison.decision == "likely_duplicate" for comparison in comparisons):
        decision = "maybe_extend_existing_tc"
        reason = "Existing TC appears to cover the candidate behavior."
    elif target == "replace":
        if replacement and replacement.replacement_allowed:
            decision = "replace_ready"
            reason = "Rejected draft has valid source grounding and no blocking duplicate comparison."
        elif replacement and replacement.replacement_mode == "maybe_extend_existing_tc":
            decision = "maybe_extend_existing_tc"
            reason = "Replacement overlaps existing TC and needs extension decision."
        else:
            decision = "defer"
            reason = "Replacement is not safe from current source facts."
    elif target == "defer":
        decision = "defer"
        reason = "Revision plan explicitly deferred this draft."
    elif current_status == "needs_revision" and source_status == "resolved" and duplicate_status == "resolved":
        decision = "revise_ready"
        reason = "Source grounding and duplicate differentiation are sufficient for a revised draft proposal."
    elif duplicate_status == "partially_resolved":
        decision = "needs_manual_decision"
        reason = "Duplicate risk has partial evidence only; manual differentiation is still required."
    else:
        decision = "needs_manual_decision"
        reason = "Manual decision is required before revised draft proposal."

    return DraftDecision(
        draft_id=draft.draft_id,
        proposed_tc_id=draft.proposed_tc_id,
        current_review_status=current_status,
        revision_plan_target=target,
        decision=decision,
        decision_reason=reason,
        candidate_req_uids=list(draft.source_requirement_uids),
        source_req_ids=list(draft.source_req_ids),
        duplicate_risk_cluster_ids=cluster_ids,
        source_grounding_status=source_status,
        duplicate_risk_status=duplicate_status,
        revision_instruction=_revision_instruction(draft, source_resolutions, decision),
        replacement_instruction=(
            "; ".join(replacement.replacement_guidance) if replacement is not None else None
        ),
        manual_questions=_unique(manual_questions),
        acceptance_criteria=plan_item.acceptance_criteria if plan_item else _default_acceptance_criteria(),
        warnings=_unique([*draft.warnings, *((review.issues if review else []) or []), *((plan_item.warnings if plan_item else []) or [])]),
    )


def _pack(
    *,
    package_id: str,
    source_revision_plan_path: str,
    source_review_path: str,
    source_proposal_path: str,
    input_paths: dict[str, str | None],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
    draft_decisions: list[DraftDecision] | None = None,
    duplicate_risk_clusters: list[DuplicateRiskCluster] | None = None,
    existing_tc_comparisons: list[ExistingTcComparison] | None = None,
    source_grounding_resolutions: list[SourceGroundingResolution] | None = None,
    replacement_strategies: list[ReplacementStrategy] | None = None,
    manual_decisions_required: list[dict[str, Any]] | None = None,
) -> NewTcRevisionDecisionPack:
    draft_decisions = draft_decisions or []
    duplicate_risk_clusters = duplicate_risk_clusters or []
    existing_tc_comparisons = existing_tc_comparisons or []
    source_grounding_resolutions = source_grounding_resolutions or []
    replacement_strategies = replacement_strategies or []
    manual_decisions_required = manual_decisions_required or []
    readiness = _readiness(draft_decisions, duplicate_risk_clusters, source_grounding_resolutions)
    canonical_write_allowed = False
    manual_review_required = True
    agent_capability_findings = _agent_capability_findings(
        draft_decisions=draft_decisions,
        duplicate_risk_clusters=duplicate_risk_clusters,
        existing_tc_comparisons=existing_tc_comparisons,
        source_grounding_resolutions=source_grounding_resolutions,
        replacement_strategies=replacement_strategies,
        manual_decisions_required=manual_decisions_required,
        readiness=readiness,
        canonical_write_allowed=canonical_write_allowed,
        manual_review_required=manual_review_required,
    )
    if blocking_reasons:
        status: DecisionPackStatus = "blocked"
    elif warnings or not readiness.ready_for_revised_draft_proposal or manual_decisions_required:
        status = "pass-with-warnings"
    else:
        status = "pass"
    return NewTcRevisionDecisionPack(
        package_id=package_id,
        decision_pack_status=status,
        source_revision_plan_path=source_revision_plan_path,
        source_review_path=source_review_path,
        source_proposal_path=source_proposal_path,
        draft_decisions=draft_decisions,
        duplicate_risk_clusters=duplicate_risk_clusters,
        existing_tc_comparisons=existing_tc_comparisons,
        source_grounding_resolutions=source_grounding_resolutions,
        replacement_strategies=replacement_strategies,
        manual_decisions_required=manual_decisions_required,
        revised_draft_readiness=readiness,
        agent_capability_findings=agent_capability_findings,
        canonical_write_allowed=canonical_write_allowed,
        manual_review_required=manual_review_required,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _readiness(
    draft_decisions: list[DraftDecision],
    clusters: list[DuplicateRiskCluster],
    source_resolutions: list[SourceGroundingResolution],
) -> RevisedDraftReadiness:
    counts = Counter(decision.decision for decision in draft_decisions)
    unresolved_duplicate = sum(
        1 for cluster in clusters if cluster.manual_decision_required and cluster.cluster_action != "no_action"
    )
    unresolved_source = sum(
        1
        for resolution in source_resolutions
        if not resolution.can_support_executable_steps or not resolution.can_support_observable_expected_result
    )
    blocking_questions = sum(len(decision.manual_questions) for decision in draft_decisions)
    allowed_decisions = {"revise_ready", "replace_ready", "defer", "maybe_extend_existing_tc"}
    ready = (
        bool(draft_decisions)
        and all(decision.decision in allowed_decisions for decision in draft_decisions)
        and counts.get("needs_manual_decision", 0) == 0
        and unresolved_duplicate == 0
        and unresolved_source == 0
        and blocking_questions == 0
    )
    if ready:
        reason = "All draft decisions are explicit and no unresolved duplicate/source questions remain."
    else:
        reason = (
            "Not ready: unresolved manual decisions, duplicate-risk clusters, or source-grounding questions remain."
        )
    return RevisedDraftReadiness(
        ready_for_revised_draft_proposal=ready,
        revise_ready_count=counts.get("revise_ready", 0),
        replace_ready_count=counts.get("replace_ready", 0),
        defer_count=counts.get("defer", 0),
        maybe_extend_existing_count=counts.get("maybe_extend_existing_tc", 0),
        needs_manual_decision_count=counts.get("needs_manual_decision", 0),
        unresolved_duplicate_risk_count=unresolved_duplicate,
        unresolved_source_grounding_count=unresolved_source,
        blocking_question_count=blocking_questions,
        readiness_reason=reason,
    )


def _agent_capability_findings(
    *,
    draft_decisions: list[DraftDecision],
    duplicate_risk_clusters: list[DuplicateRiskCluster],
    existing_tc_comparisons: list[ExistingTcComparison],
    source_grounding_resolutions: list[SourceGroundingResolution],
    replacement_strategies: list[ReplacementStrategy],
    manual_decisions_required: list[dict[str, Any]],
    readiness: RevisedDraftReadiness,
    canonical_write_allowed: bool,
    manual_review_required: bool,
) -> list[AgentCapabilityFinding]:
    raw_duplicate_actions_count = len(existing_tc_comparisons)
    cluster_count = len(duplicate_risk_clusters)
    draft_count = len(draft_decisions)
    needs_manual_count = readiness.needs_manual_decision_count

    if raw_duplicate_actions_count and cluster_count >= raw_duplicate_actions_count:
        duplicate_status: CapabilityStatus = "gap"
        duplicate_recommendation = "Improve duplicate-risk clustering; current grouping does not reduce review load."
    elif draft_count and needs_manual_count >= max(1, int(draft_count * 0.8)):
        duplicate_status = "partial"
        duplicate_recommendation = (
            "Keep clustering, but add stronger comparison heuristics or human-answer capture before revised drafting."
        )
    else:
        duplicate_status = "works"
        duplicate_recommendation = "Retain clustered duplicate review as a precondition for revised drafting."

    source_total = len(source_grounding_resolutions)
    unresolved_source = readiness.unresolved_source_grounding_count
    if source_total and unresolved_source == 0:
        source_status: CapabilityStatus = "works"
        source_recommendation = "Source grounding can support revised draft instructions; keep source-only constraints."
    elif source_total and unresolved_source < source_total:
        source_status = "partial"
        source_recommendation = "Capture missing source facts as explicit manual questions before draft revision."
    else:
        source_status = "gap"
        source_recommendation = "Improve source extraction before creating revised drafts; current facts are insufficient."

    ready_like_count = readiness.revise_ready_count + readiness.replace_ready_count
    if draft_count and ready_like_count > draft_count / 2:
        quality_status: CapabilityStatus = "works"
        quality_recommendation = "Draft quality is sufficient for most candidates after revision gating."
    elif draft_count and needs_manual_count == draft_count:
        quality_status = "gap"
        quality_recommendation = "Update draft-generation instructions to avoid generic placeholders and require source-backed steps/oracles."
    else:
        quality_status = "partial"
        quality_recommendation = "Draft-only safety works, but substantial revision is still needed before create apply."

    replacement_total = len(replacement_strategies)
    replacement_allowed = sum(1 for strategy in replacement_strategies if strategy.replacement_allowed)
    replacement_modes = Counter(strategy.replacement_mode for strategy in replacement_strategies)
    if replacement_total == 0:
        replacement_status: CapabilityStatus = "works"
        replacement_recommendation = "No rejected drafts require replacement strategy."
    elif replacement_allowed == replacement_total:
        replacement_status = "works"
        replacement_recommendation = "Rejected drafts have source-grounded replacement paths."
    elif replacement_allowed > 0 or replacement_total:
        replacement_status = "partial"
        replacement_recommendation = "Keep replacement strategies explicit; resolve duplicate/source questions before rewriting rejected drafts."
    else:
        replacement_status = "gap"
        replacement_recommendation = "Rejected drafts cannot be safely replaced from current source facts."

    manual_count = len(manual_decisions_required)
    if manual_count == 0:
        manual_status: CapabilityStatus = "works"
        manual_recommendation = "No manual decisions remain before revised drafting."
    elif draft_count and manual_count <= draft_count * 2:
        manual_status = "works"
        manual_recommendation = "Manual decisions are compact enough for direct reviewer action."
    elif draft_count and manual_count <= draft_count * 12:
        manual_status = "partial"
        manual_recommendation = "Manual decisions are actionable but still numerous; summarize them by cluster before handing to a human."
    else:
        manual_status = "gap"
        manual_recommendation = "Manual decision volume is too high; add more aggregation before reviewer handoff."

    unsafe = canonical_write_allowed or (
        not manual_review_required
        or (readiness.ready_for_revised_draft_proposal and (manual_count or needs_manual_count))
    )
    if unsafe:
        safety_status: CapabilityStatus = "gap"
        safety_recommendation = "Fix safety gate: unresolved decisions must block readiness and canonical writes."
    else:
        safety_status = "works"
        safety_recommendation = "Safety gate correctly keeps canonical writes disabled and requires review while decisions remain."

    return [
        AgentCapabilityFinding(
            finding_id="ACF-000001",
            capability_area="duplicate_risk_handling",
            status=duplicate_status,
            evidence={
                "raw_duplicate_risk_actions_count": raw_duplicate_actions_count,
                "duplicate_risk_clusters_count": cluster_count,
                "unresolved_duplicate_risk_count": readiness.unresolved_duplicate_risk_count,
                "needs_manual_decision_count": needs_manual_count,
            },
            recommendation=duplicate_recommendation,
            should_update_agent_instructions=duplicate_status != "works",
        ),
        AgentCapabilityFinding(
            finding_id="ACF-000002",
            capability_area="source_grounding",
            status=source_status,
            evidence={
                "source_grounding_resolutions_count": source_total,
                "unresolved_source_grounding_count": unresolved_source,
                "can_support_all_ready_candidates": unresolved_source == 0,
            },
            recommendation=source_recommendation,
            should_update_agent_instructions=source_status == "gap",
        ),
        AgentCapabilityFinding(
            finding_id="ACF-000003",
            capability_area="draft_quality",
            status=quality_status,
            evidence={
                "draft_decisions_count": draft_count,
                "revise_ready_count": readiness.revise_ready_count,
                "replace_ready_count": readiness.replace_ready_count,
                "needs_manual_decision_count": needs_manual_count,
            },
            recommendation=quality_recommendation,
            should_update_agent_instructions=quality_status != "works",
        ),
        AgentCapabilityFinding(
            finding_id="ACF-000004",
            capability_area="replacement_strategy",
            status=replacement_status,
            evidence={
                "replacement_strategies_count": replacement_total,
                "replacement_allowed_count": replacement_allowed,
                "replacement_modes": dict(replacement_modes),
            },
            recommendation=replacement_recommendation,
            should_update_agent_instructions=replacement_status == "gap",
        ),
        AgentCapabilityFinding(
            finding_id="ACF-000005",
            capability_area="manual_decision_flow",
            status=manual_status,
            evidence={
                "manual_decisions_required_count": manual_count,
                "draft_decisions_count": draft_count,
            },
            recommendation=manual_recommendation,
            should_update_agent_instructions=manual_status != "works",
        ),
        AgentCapabilityFinding(
            finding_id="ACF-000006",
            capability_area="safety_gate",
            status=safety_status,
            evidence={
                "canonical_write_allowed": canonical_write_allowed,
                "manual_review_required": manual_review_required,
                "ready_for_revised_draft_proposal": readiness.ready_for_revised_draft_proposal,
                "unresolved_decisions_present": bool(manual_count or needs_manual_count),
            },
            recommendation=safety_recommendation,
            should_update_agent_instructions=safety_status != "works",
        ),
    ]


def _read_referenced_tc_blocks(
    clusters: list[DuplicateRiskCluster],
    test_cases_dir: Path,
) -> tuple[dict[tuple[str, str], ParsedTcBlock], list[str]]:
    warnings: list[str] = []
    needed: dict[str, set[str]] = defaultdict(set)
    for cluster in clusters:
        for file_path in cluster.similar_file_paths:
            for tc_id in cluster.similar_tc_ids:
                needed[file_path].add(tc_id)
    blocks: dict[tuple[str, str], ParsedTcBlock] = {}
    for file_path, tc_ids in sorted(needed.items()):
        path = _resolve_tc_path(test_cases_dir, file_path)
        if path is None:
            warnings.append(f"referenced similar TC file is outside or missing: {file_path}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - diagnostic pack should continue.
            warnings.append(f"similar TC file could not be read: {path}: {exc}")
            continue
        if _is_aggregate_file(content):
            warnings.append(f"similar TC file skipped as aggregate: {path}")
            continue
        for block in _parse_tc_blocks(path, content):
            if block.test_case_id in tc_ids:
                blocks[(_path_key(file_path), block.test_case_id)] = block
                blocks[(_path_key(str(path)), block.test_case_id)] = block
    return blocks, warnings


def _parse_tc_blocks(file_path: Path, content: str) -> list[ParsedTcBlock]:
    lines = content.splitlines()
    headings: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line.strip())
        if match:
            headings.append((index, match.group(2), match.group(3).strip()))
    blocks: list[ParsedTcBlock] = []
    for index, (start, test_case_id, heading_tail) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
        block_lines = lines[start:end]
        block_text = "\n".join(block_lines)
        title = _title(block_lines) or heading_tail or None
        blocks.append(
            ParsedTcBlock(
                test_case_id=test_case_id,
                file_path=str(file_path),
                title=title,
                traceability_line=_traceability_line(block_lines),
                refs=sorted(set(ref.upper() for ref in REF_RE.findall(block_text))),
                steps_summary=_section_summary(block_lines, ["steps", "шаг"]),
                expected_result_summary=_section_summary(block_lines, ["expected", "ожида"]),
                text=block_text,
            )
        )
    return blocks


def _traceability_line(lines: list[str]) -> str | None:
    for line in lines:
        lowered = line.casefold()
        if "traceability" in lowered or "трассиров" in lowered:
            return line.strip()
    return None


def _title(lines: list[str]) -> str | None:
    for line in lines:
        lowered = line.casefold()
        if "title" in lowered or "название" in lowered:
            if ":**" in line:
                return line.split(":**", 1)[1].strip()
            if ":" in line:
                return line.split(":", 1)[1].strip()
    return None


def _section_summary(lines: list[str], markers: list[str]) -> str:
    collected: list[str] = []
    capture = False
    for line in lines:
        stripped = line.strip()
        lowered = stripped.casefold()
        if any(marker in lowered for marker in markers):
            capture = True
            collected.append(stripped)
            continue
        if capture and stripped.startswith("**") and not any(marker in lowered for marker in markers):
            break
        if capture and stripped:
            collected.append(stripped)
        if len(" ".join(collected)) > 500:
            break
    return " ".join(collected)[:700]


def _resolve_tc_path(test_cases_dir: Path, file_path: str) -> Path | None:
    candidate = Path(file_path)
    candidates = []
    if candidate.is_absolute():
        candidates.append(candidate)
    candidates.extend([test_cases_dir / file_path, test_cases_dir / candidate.name])
    try:
        root = test_cases_dir.resolve()
    except FileNotFoundError:
        return None
    for path in candidates:
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            continue
        if not resolved.exists():
            continue
        if root == resolved or root in resolved.parents:
            return resolved
    return None


def _is_aggregate_file(content: str) -> bool:
    head = "\n".join(content.splitlines()[:80]).casefold()
    return any(marker in head for marker in AGGREGATE_MARKERS)


def _source_resolutions_by_draft(
    resolutions: list[SourceGroundingResolution],
) -> dict[str, list[SourceGroundingResolution]]:
    grouped: dict[str, list[SourceGroundingResolution]] = defaultdict(list)
    for resolution in resolutions:
        grouped[resolution.draft_id].append(resolution)
    return grouped


def _comparisons_by_draft(comparisons: list[ExistingTcComparison]) -> dict[str, list[ExistingTcComparison]]:
    grouped: dict[str, list[ExistingTcComparison]] = defaultdict(list)
    for comparison in comparisons:
        if comparison.draft_id:
            grouped[comparison.draft_id].append(comparison)
    return grouped


def _cluster_ids_by_draft(clusters: list[DuplicateRiskCluster]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for cluster in clusters:
        for draft_id in cluster.draft_ids:
            grouped[draft_id].append(cluster.cluster_id)
    return grouped


def _manual_decisions(
    draft_decisions: list[DraftDecision],
    clusters: list[DuplicateRiskCluster],
    comparisons: list[ExistingTcComparison],
    resolutions: list[SourceGroundingResolution],
    replacements: list[ReplacementStrategy],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for draft in draft_decisions:
        for index, question in enumerate(draft.manual_questions, start=1):
            decisions.append({"scope": "draft", "id": f"{draft.draft_id}-Q{index:03d}", "question": question})
    for cluster in clusters:
        if cluster.manual_decision_required:
            decisions.append(
                {
                    "scope": "duplicate_risk_cluster",
                    "id": cluster.cluster_id,
                    "question": "Confirm separate new TC, extend existing TC, or defer this cluster.",
                }
            )
    for comparison in comparisons:
        for index, question in enumerate(comparison.manual_questions, start=1):
            decisions.append(
                {"scope": "existing_tc_comparison", "id": f"{comparison.comparison_id}-Q{index:03d}", "question": question}
            )
    for resolution in resolutions:
        if resolution.manual_question:
            decisions.append({"scope": "source_grounding", "id": f"{resolution.draft_id}-{resolution.req_uid}", "question": resolution.manual_question})
    for replacement in replacements:
        for index, question in enumerate(replacement.manual_questions, start=1):
            decisions.append({"scope": "replacement", "id": f"{replacement.draft_id}-Q{index:03d}", "question": question})
    return _dedupe_decision_dicts(decisions)


def _source_status(resolutions: list[SourceGroundingResolution]) -> GroundingStatus:
    if not resolutions:
        return "unresolved"
    full = [
        resolution.can_support_executable_steps and resolution.can_support_observable_expected_result
        for resolution in resolutions
    ]
    if all(full):
        return "resolved"
    if any(full):
        return "partially_resolved"
    return "unresolved"


def _duplicate_status(
    cluster_ids: list[str],
    clusters: list[DuplicateRiskCluster],
    comparisons: list[ExistingTcComparison],
) -> GroundingStatus:
    if not cluster_ids:
        return "resolved"
    related = [cluster for cluster in clusters if cluster.cluster_id in set(cluster_ids)]
    if any(cluster.cluster_action in {"defer", "maybe_extend_existing_tc"} for cluster in related):
        return "unresolved"
    if comparisons and all(comparison.decision == "separate_new_tc_possible" for comparison in comparisons):
        return "resolved"
    if comparisons and any(comparison.decision == "separate_new_tc_possible" for comparison in comparisons):
        return "partially_resolved"
    return "unresolved" if any(cluster.manual_decision_required for cluster in related) else "resolved"


def _cluster_action(risk: str, actions: list[str]) -> ClusterAction:
    if risk == "high" or "defer" in actions:
        return "defer"
    if "maybe_extend_existing" in actions:
        return "maybe_extend_existing_tc"
    if risk == "medium" or "differentiate" in actions:
        return "differentiate"
    return "no_action"


def _max_risk(risks: list[str]) -> RiskLevel:
    if "high" in risks:
        return "high"
    if "medium" in risks:
        return "medium"
    return "low"


def _candidate_behavior(candidate: CandidateRequirement | None) -> str:
    if candidate is None:
        return "candidate requirement missing from context bundle"
    parts = [
        f"object={candidate.object}" if candidate.object else "",
        f"condition={candidate.condition}" if candidate.condition else "",
        f"expected_behavior={candidate.expected_behavior}" if candidate.expected_behavior else "",
        f"source_text={candidate.source_text or candidate.normalized_text}" if candidate.source_text or candidate.normalized_text else "",
        f"source_req_id={candidate.source_req_id}" if candidate.source_req_id else "",
    ]
    return "; ".join(part for part in parts if part)


def _existing_summary(block: ParsedTcBlock) -> str:
    return "; ".join(
        part
        for part in [
            f"title={block.title}" if block.title else "",
            f"traceability={block.traceability_line}" if block.traceability_line else "",
            f"steps={block.steps_summary}" if block.steps_summary else "",
            f"expected={block.expected_result_summary}" if block.expected_result_summary else "",
        ]
        if part
    )


def _candidate_usable_facts(candidate: CandidateRequirement | None) -> list[str]:
    if candidate is None:
        return []
    facts: list[str] = []
    if candidate.object:
        facts.append(f"object: {candidate.object}")
    if candidate.condition:
        facts.append(f"condition: {candidate.condition}")
    if candidate.expected_behavior:
        facts.append(f"expected_behavior: {candidate.expected_behavior}")
    if candidate.source_text:
        facts.append(f"source_text: {candidate.source_text}")
    if candidate.normalized_text:
        facts.append(f"normalized_text: {candidate.normalized_text}")
    if candidate.source_req_id:
        facts.append(f"source_req_id: {candidate.source_req_id}")
    return _unique(facts)


def _candidate_missing_facts(candidate: CandidateRequirement | None) -> list[str]:
    if candidate is None:
        return ["candidate requirement is missing from context bundle"]
    missing: list[str] = []
    if not candidate.condition:
        missing.append("source-backed navigation/action condition")
    if not candidate.expected_behavior:
        missing.append("observable expected behavior")
    if not candidate.object:
        missing.append("specific object/field/screen")
    return missing


def _resolved_instruction(candidate: CandidateRequirement | None, missing: list[str]) -> str:
    if candidate is None:
        return "Do not draft until the candidate requirement is restored in the context bundle."
    facts = _candidate_usable_facts(candidate)
    if missing:
        return "Use available source facts only and keep unresolved facts as manual questions: " + "; ".join(facts)
    return "Use these source facts for revised title, preconditions, action and expected result: " + "; ".join(facts)


def _revision_instruction(
    draft: DraftTestCaseCandidate,
    resolutions: list[SourceGroundingResolution],
    decision: DraftDecisionName,
) -> str:
    if decision in {"defer", "maybe_extend_existing_tc", "needs_manual_decision"}:
        return "Do not create revised draft text until manual decisions in this pack are resolved."
    facts = []
    for resolution in resolutions:
        facts.extend(resolution.usable_source_facts)
    return (
        f"Revise {draft.draft_id} from source facts only; replace placeholder steps and expected results. "
        f"Source facts: {'; '.join(_unique(facts))}"
    )


def _default_acceptance_criteria() -> list[str]:
    return [
        "Draft remains proposal-only.",
        "Steps and expected result are source-backed.",
        "Duplicate risk has an explicit decision.",
        "Canonical write remains disabled.",
    ]


def _keywords(text: str) -> set[str]:
    stop = {"with", "from", "that", "this", "для", "при", "как", "или", "the", "and"}
    return {word.casefold() for word in WORD_RE.findall(text or "") if word.casefold() not in stop}


def _norm_key(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()[:120]


def _path_key(value: str) -> str:
    return str(value).replace("\\", "/").casefold()


def _input_paths(**paths: Path | None) -> dict[str, str | None]:
    return {key: (str(value) if value is not None else None) for key, value in paths.items()}


def _load_optional(path: Path, loader: Any, label: str, blocking_reasons: list[str]) -> Any:
    if not Path(path).exists():
        return None
    try:
        return loader(Path(path))
    except Exception as exc:  # noqa: BLE001 - decision pack reports parse failures.
        blocking_reasons.append(f"{label} cannot be parsed: {path}: {exc}")
        return None


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


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


def _dedupe_decision_dicts(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for decision in decisions:
        key = (str(decision.get("scope")), str(decision.get("id")), str(decision.get("question")))
        if key not in seen:
            seen.add(key)
            result.append(decision)
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
