from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
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

CREATED_BY_TOOL = "test_case_agent.new_tc_draft_revision_plan"
REVISION_PLAN_PREFIX = "new-tc-draft-revision-plan"
DEFAULT_PACKAGE_ID = "WPKG-000001"

PlanStatus = Literal["pass", "pass-with-warnings", "blocked"]
TargetRevisionStatus = Literal["revise", "replace", "defer", "keep_rejected"]
Priority = Literal["high", "medium", "low"]
DuplicateRiskActionName = Literal["differentiate", "defer", "maybe_extend_existing", "no_action"]


@dataclass(frozen=True)
class DraftRevisionItem:
    draft_id: str
    proposed_tc_id: str
    current_review_status: str
    target_revision_status: TargetRevisionStatus
    priority: Priority
    required_fixes: list[str]
    source_facts_to_use: list[str]
    concrete_step_guidance: list[str]
    expected_result_guidance: list[str]
    test_data_guidance: list[str]
    traceability_guidance: list[str]
    duplicate_risk_guidance: list[str]
    acceptance_criteria: list[str]
    blocking_questions: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "proposed_tc_id": self.proposed_tc_id,
            "current_review_status": self.current_review_status,
            "target_revision_status": self.target_revision_status,
            "priority": self.priority,
            "required_fixes": self.required_fixes,
            "source_facts_to_use": self.source_facts_to_use,
            "concrete_step_guidance": self.concrete_step_guidance,
            "expected_result_guidance": self.expected_result_guidance,
            "test_data_guidance": self.test_data_guidance,
            "traceability_guidance": self.traceability_guidance,
            "duplicate_risk_guidance": self.duplicate_risk_guidance,
            "acceptance_criteria": self.acceptance_criteria,
            "blocking_questions": self.blocking_questions,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DraftRevisionItem":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            current_review_status=str(data["current_review_status"]),
            target_revision_status=data["target_revision_status"],
            priority=data["priority"],
            required_fixes=list(data.get("required_fixes") or []),
            source_facts_to_use=list(data.get("source_facts_to_use") or []),
            concrete_step_guidance=list(data.get("concrete_step_guidance") or []),
            expected_result_guidance=list(data.get("expected_result_guidance") or []),
            test_data_guidance=list(data.get("test_data_guidance") or []),
            traceability_guidance=list(data.get("traceability_guidance") or []),
            duplicate_risk_guidance=list(data.get("duplicate_risk_guidance") or []),
            acceptance_criteria=list(data.get("acceptance_criteria") or []),
            blocking_questions=list(data.get("blocking_questions") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class DuplicateRiskAction:
    draft_id: str | None
    candidate_req_uid: str | None
    similar_tc_id: str
    similar_file_path: str
    risk: str
    action: DuplicateRiskActionName
    rationale: str
    required_manual_decision: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "candidate_req_uid": self.candidate_req_uid,
            "similar_tc_id": self.similar_tc_id,
            "similar_file_path": self.similar_file_path,
            "risk": self.risk,
            "action": self.action,
            "rationale": self.rationale,
            "required_manual_decision": self.required_manual_decision,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DuplicateRiskAction":
        return cls(
            draft_id=data.get("draft_id"),
            candidate_req_uid=data.get("candidate_req_uid"),
            similar_tc_id=str(data["similar_tc_id"]),
            similar_file_path=str(data["similar_file_path"]),
            risk=str(data["risk"]),
            action=data["action"],
            rationale=str(data["rationale"]),
            required_manual_decision=str(data["required_manual_decision"]),
        )


@dataclass(frozen=True)
class SourceGroundingAction:
    draft_id: str
    req_uid: str
    source_text: str | None
    condition: str | None
    expected_behavior: str | None
    usable_facts: list[str]
    missing_facts: list[str]
    revision_instruction: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "req_uid": self.req_uid,
            "source_text": self.source_text,
            "condition": self.condition,
            "expected_behavior": self.expected_behavior,
            "usable_facts": self.usable_facts,
            "missing_facts": self.missing_facts,
            "revision_instruction": self.revision_instruction,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceGroundingAction":
        return cls(
            draft_id=str(data["draft_id"]),
            req_uid=str(data["req_uid"]),
            source_text=data.get("source_text"),
            condition=data.get("condition"),
            expected_behavior=data.get("expected_behavior"),
            usable_facts=list(data.get("usable_facts") or []),
            missing_facts=list(data.get("missing_facts") or []),
            revision_instruction=str(data["revision_instruction"]),
        )


@dataclass
class NewTcDraftRevisionPlan:
    package_id: str
    plan_status: PlanStatus
    source_review_path: str
    source_proposal_path: str
    revision_items: list[DraftRevisionItem]
    duplicate_risk_actions: list[DuplicateRiskAction]
    source_grounding_actions: list[SourceGroundingAction]
    coverage_actions: list[dict[str, Any]]
    deferred_or_rejected_actions: list[dict[str, Any]]
    revision_summary: dict[str, Any]
    ready_for_revised_draft_proposal: bool
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
            "plan_status": self.plan_status,
            "source_review_path": self.source_review_path,
            "source_proposal_path": self.source_proposal_path,
            "revision_items": [item.to_dict() for item in self.revision_items],
            "duplicate_risk_actions": [item.to_dict() for item in self.duplicate_risk_actions],
            "source_grounding_actions": [item.to_dict() for item in self.source_grounding_actions],
            "coverage_actions": self.coverage_actions,
            "deferred_or_rejected_actions": self.deferred_or_rejected_actions,
            "revision_summary": self.revision_summary,
            "ready_for_revised_draft_proposal": self.ready_for_revised_draft_proposal,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcDraftRevisionPlan":
        return cls(
            package_id=str(data["package_id"]),
            plan_status=data["plan_status"],
            source_review_path=str(data["source_review_path"]),
            source_proposal_path=str(data["source_proposal_path"]),
            revision_items=[DraftRevisionItem.from_dict(item) for item in data.get("revision_items", [])],
            duplicate_risk_actions=[
                DuplicateRiskAction.from_dict(item) for item in data.get("duplicate_risk_actions", [])
            ],
            source_grounding_actions=[
                SourceGroundingAction.from_dict(item) for item in data.get("source_grounding_actions", [])
            ],
            coverage_actions=list(data.get("coverage_actions") or []),
            deferred_or_rejected_actions=list(data.get("deferred_or_rejected_actions") or []),
            revision_summary=dict(data.get("revision_summary") or {}),
            ready_for_revised_draft_proposal=bool(data.get("ready_for_revised_draft_proposal")),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_new_tc_draft_revision_plan(
    *,
    package_id: str,
    draft_proposal_path: Path,
    draft_review_path: Path,
    context_bundle_path: Path,
    test_cases_dir: Path,
    draft_proposal_markdown_path: Path | None = None,
    draft_review_markdown_path: Path | None = None,
    context_bundle_markdown_path: Path | None = None,
    requirements_diff_path: Path | None = None,
    impact_report_path: Path | None = None,
    update_plan_path: Path | None = None,
    old_registry_path: Path | None = None,
    new_registry_path: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> NewTcDraftRevisionPlan:
    input_paths = _input_paths(
        draft_proposal_path=draft_proposal_path,
        draft_proposal_markdown_path=draft_proposal_markdown_path,
        draft_review_path=draft_review_path,
        draft_review_markdown_path=draft_review_markdown_path,
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
        blocking_reasons.append(f"this revision plan is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    for label, path in {
        "draft proposal": draft_proposal_path,
        "draft review": draft_review_path,
        "context bundle": context_bundle_path,
        "test-cases dir": test_cases_dir,
    }.items():
        path = Path(path)
        if label == "test-cases dir":
            if not path.exists() or not path.is_dir():
                blocking_reasons.append(f"{label} is missing: {path}")
        elif not path.exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    proposal = _load_optional(draft_proposal_path, load_new_tc_draft_proposal, "draft proposal", blocking_reasons)
    review = _load_optional(draft_review_path, load_new_tc_draft_review, "draft review", blocking_reasons)
    bundle = _load_optional(context_bundle_path, load_create_new_tc_context_bundle, "context bundle", blocking_reasons)

    if proposal is not None and proposal.package_id != package_id:
        blocking_reasons.append(f"draft proposal package_id mismatch: {proposal.package_id} != {package_id}")
    if review is not None and review.package_id != package_id:
        blocking_reasons.append(f"draft review package_id mismatch: {review.package_id} != {package_id}")
    if bundle is not None and bundle.package_id != package_id:
        blocking_reasons.append(f"context bundle package_id mismatch: {bundle.package_id} != {package_id}")

    if blocking_reasons or proposal is None or review is None or bundle is None:
        return _plan(
            package_id=package_id,
            source_review_path=str(draft_review_path),
            source_proposal_path=str(draft_proposal_path),
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    warnings.extend(review.warnings)
    warnings.extend(proposal.warnings)
    candidate_by_req = {
        candidate.req_uid: candidate
        for candidate in bundle.candidate_requirements
        if candidate.req_uid
    }
    review_by_draft = {item.draft_id: item for item in review.draft_reviews}
    decisions_by_req = _duplicate_decisions_by_req(proposal)

    revision_items = [
        _revision_item(draft, review_by_draft.get(draft.draft_id), candidate_by_req, decisions_by_req)
        for draft in proposal.draft_test_cases
    ]
    duplicate_risk_actions = _duplicate_risk_actions(proposal, revision_items)
    source_grounding_actions = _source_grounding_actions(proposal, candidate_by_req)
    coverage_actions = _coverage_actions(bundle, proposal, revision_items)
    deferred_or_rejected_actions = _deferred_or_rejected_actions(proposal, review, revision_items)

    if len(revision_items) != len(proposal.draft_test_cases):
        blocking_reasons.append("revision item count does not match draft test case count.")
    accounted = {
        req_uid
        for item in revision_items
        for req_uid in _draft_req_uids(proposal, item.draft_id)
    }
    bundle_reqs = {candidate.req_uid for candidate in bundle.candidate_requirements if candidate.req_uid}
    missing = sorted(bundle_reqs - accounted)
    if missing:
        warnings.append(f"candidate requirements not mapped to revision items: {', '.join(missing)}")

    return _plan(
        package_id=package_id,
        source_review_path=str(draft_review_path),
        source_proposal_path=str(draft_proposal_path),
        revision_items=revision_items,
        duplicate_risk_actions=duplicate_risk_actions,
        source_grounding_actions=source_grounding_actions,
        coverage_actions=coverage_actions,
        deferred_or_rejected_actions=deferred_or_rejected_actions,
        input_paths=input_paths,
        warnings=_unique(warnings),
        blocking_reasons=_unique(blocking_reasons),
        created_by_tool=created_by_tool,
    )


def write_new_tc_draft_revision_plan(
    plan: NewTcDraftRevisionPlan,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REVISION_PLAN_PREFIX}-{plan.package_id}.json"
    markdown_path = out_dir / f"{REVISION_PLAN_PREFIX}-{plan.package_id}.md"
    json_path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_new_tc_draft_revision_plan_markdown(plan), encoding="utf-8", newline="\n")
    return json_path, markdown_path


def load_new_tc_draft_revision_plan(path: Path) -> NewTcDraftRevisionPlan:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("New TC draft revision plan root must be a JSON object.")
    return NewTcDraftRevisionPlan.from_dict(payload)


def render_new_tc_draft_revision_plan_markdown(plan: NewTcDraftRevisionPlan) -> str:
    lines = [
        f"# New TC Draft Revision Plan {plan.package_id}",
        "",
        "## Summary",
        "",
        f"- Plan status: `{plan.plan_status}`",
        f"- Revision items: `{len(plan.revision_items)}`",
        f"- Ready for revised draft proposal: `{str(plan.ready_for_revised_draft_proposal).lower()}`",
        f"- Canonical write allowed: `{str(plan.canonical_write_allowed).lower()}`",
        f"- Manual review required: `{str(plan.manual_review_required).lower()}`",
        f"- Warnings: `{len(plan.warnings)}`",
        f"- Blocking reasons: `{len(plan.blocking_reasons)}`",
        "",
        "## Safety Statement",
        "",
        "- Planning-only artifact.",
        "- No canonical TC was created.",
        "- No canonical TC was edited.",
        "- No apply command or patch application is authorized.",
        "",
        "## Revision Items",
        "",
        "| Draft | Proposed TC | Current | Target | Priority | Fixes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in plan.revision_items:
        lines.append(
            f"| `{item.draft_id}` | `{item.proposed_tc_id}` | `{item.current_review_status}` | "
            f"`{item.target_revision_status}` | `{item.priority}` | {len(item.required_fixes)} |"
        )
    lines.extend(["", "## Per-Draft Revision Details", ""])
    for item in plan.revision_items:
        lines.append(f"### {item.draft_id} / {item.proposed_tc_id}")
        lines.append(f"- Target: `{item.target_revision_status}`")
        lines.append(f"- Priority: `{item.priority}`")
        lines.append("- Required fixes:")
        _append_list(lines, item.required_fixes)
        lines.append("- Source facts to use:")
        _append_list(lines, item.source_facts_to_use)
        lines.append("- Concrete step guidance:")
        _append_list(lines, item.concrete_step_guidance)
        lines.append("- Expected result guidance:")
        _append_list(lines, item.expected_result_guidance)
        lines.append("- Blocking questions:")
        _append_list(lines, item.blocking_questions)
        lines.append("")
    lines.extend(["## Source Grounding Actions", ""])
    for action in plan.source_grounding_actions:
        lines.append(f"- `{action.draft_id}` `{action.req_uid}`: {action.revision_instruction}")
    if not plan.source_grounding_actions:
        lines.append("- none")
    lines.extend(["", "## Duplicate Risk Actions", ""])
    for action in plan.duplicate_risk_actions:
        lines.append(
            f"- `{action.draft_id or 'n/a'}` `{action.candidate_req_uid or 'n/a'}` -> "
            f"`{action.similar_tc_id}` `{action.risk}` `{action.action}`: {action.required_manual_decision}"
        )
    if not plan.duplicate_risk_actions:
        lines.append("- none")
    lines.extend(["", "## Deferred / Rejected Actions", ""])
    for action in plan.deferred_or_rejected_actions:
        lines.append(f"- `{action.get('draft_id')}` `{action.get('target_revision_status')}`: {action.get('reason')}")
    if not plan.deferred_or_rejected_actions:
        lines.append("- none")
    lines.extend(["", "## Acceptance Criteria For Revised Draft Proposal", ""])
    for criterion in _global_acceptance_criteria():
        lines.append(f"- {criterion}")
    lines.extend(["", "## Warnings", ""])
    _append_list(lines, plan.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, plan.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _revision_item(
    draft: DraftTestCaseCandidate,
    review: DraftTestCaseReview | None,
    candidate_by_req: dict[str, CandidateRequirement],
    decisions_by_req: dict[str, list[Any]],
) -> DraftRevisionItem:
    current_status = review.review_status if review else "missing_review"
    if current_status == "needs_revision":
        target: TargetRevisionStatus = "revise"
    elif current_status == "reject":
        if _has_valid_source_mapping(draft, candidate_by_req):
            target = "replace"
        else:
            target = "keep_rejected"
    elif current_status == "defer":
        target = "defer"
    else:
        target = "revise"
    warnings = _unique([*draft.warnings, *((review.issues if review else []) or [])])
    blocking_questions = _blocking_questions(draft, candidate_by_req)
    facts = _source_facts(draft, candidate_by_req)
    duplicate_guidance = _duplicate_guidance(draft, decisions_by_req)
    if duplicate_guidance:
        blocking_questions.append("Resolve duplicate risk: confirm separate behavior, maybe extend existing TC, or defer.")
    return DraftRevisionItem(
        draft_id=draft.draft_id,
        proposed_tc_id=draft.proposed_tc_id,
        current_review_status=current_status,
        target_revision_status=target,
        priority=_priority(target, review, duplicate_guidance, blocking_questions),
        required_fixes=_required_fixes(review, target),
        source_facts_to_use=facts,
        concrete_step_guidance=_step_guidance(draft, candidate_by_req),
        expected_result_guidance=_expected_result_guidance(draft, candidate_by_req),
        test_data_guidance=_test_data_guidance(draft, candidate_by_req),
        traceability_guidance=_traceability_guidance(draft, candidate_by_req),
        duplicate_risk_guidance=duplicate_guidance,
        acceptance_criteria=_item_acceptance_criteria(target),
        blocking_questions=_unique(blocking_questions),
        warnings=warnings,
    )


def _duplicate_risk_actions(
    proposal: NewTcDraftProposal,
    revision_items: list[DraftRevisionItem],
) -> list[DuplicateRiskAction]:
    draft_by_req: dict[str, str] = {}
    for draft in proposal.draft_test_cases:
        for req_uid in draft.source_requirement_uids:
            draft_by_req[req_uid] = draft.draft_id
    actions: list[DuplicateRiskAction] = []
    for decision in proposal.duplicate_risk_decisions:
        if decision.risk == "high":
            action: DuplicateRiskActionName = "defer"
            manual = "Decide whether existing TC already covers the requirement before any rewrite."
        elif decision.decision == "maybe_extend_existing_tc":
            action = "maybe_extend_existing"
            manual = "Compare similar TC and decide whether extending it is better than creating a new TC draft."
        elif decision.risk == "medium":
            action = "differentiate"
            manual = "Confirm the revised draft has behavior not already covered by the similar TC."
        else:
            action = "no_action"
            manual = "No duplicate-risk action beyond normal review."
        actions.append(
            DuplicateRiskAction(
                draft_id=draft_by_req.get(decision.candidate_req_uid or ""),
                candidate_req_uid=decision.candidate_req_uid,
                similar_tc_id=decision.similar_tc_id,
                similar_file_path=decision.similar_file_path,
                risk=decision.risk,
                action=action,
                rationale=decision.rationale,
                required_manual_decision=manual,
            )
        )
    return actions


def _source_grounding_actions(
    proposal: NewTcDraftProposal,
    candidate_by_req: dict[str, CandidateRequirement],
) -> list[SourceGroundingAction]:
    actions: list[SourceGroundingAction] = []
    for draft in proposal.draft_test_cases:
        for req_uid in draft.source_requirement_uids:
            candidate = candidate_by_req.get(req_uid)
            if candidate is None:
                actions.append(
                    SourceGroundingAction(
                        draft_id=draft.draft_id,
                        req_uid=req_uid,
                        source_text=None,
                        condition=None,
                        expected_behavior=None,
                        usable_facts=[],
                        missing_facts=["candidate requirement is missing from context bundle"],
                        revision_instruction="Do not revise from this draft until the missing candidate context is restored.",
                    )
                )
                continue
            usable = _candidate_usable_facts(candidate)
            missing = _candidate_missing_facts(candidate)
            actions.append(
                SourceGroundingAction(
                    draft_id=draft.draft_id,
                    req_uid=req_uid,
                    source_text=candidate.source_text,
                    condition=candidate.condition,
                    expected_behavior=candidate.expected_behavior,
                    usable_facts=usable,
                    missing_facts=missing,
                    revision_instruction=_source_revision_instruction(candidate, missing),
                )
            )
    return actions


def _coverage_actions(
    bundle: CreateNewTcContextBundle,
    proposal: NewTcDraftProposal,
    revision_items: list[DraftRevisionItem],
) -> list[dict[str, Any]]:
    drafted = {
        req_uid
        for draft in proposal.draft_test_cases
        for req_uid in draft.source_requirement_uids
    }
    item_by_draft = {item.draft_id: item for item in revision_items}
    result: list[dict[str, Any]] = []
    for candidate in bundle.candidate_requirements:
        result.append(
            {
                "req_uid": candidate.req_uid,
                "source_req_id": candidate.source_req_id,
                "accounted_for": candidate.req_uid in drafted,
                "linked_revision_items": [
                    item.draft_id
                    for draft in proposal.draft_test_cases
                    if candidate.req_uid in draft.source_requirement_uids
                    for item in [item_by_draft.get(draft.draft_id)]
                    if item is not None
                ],
                "required_action": "revise_or_replace_draft" if candidate.req_uid in drafted else "add_or_defer_in_revised_proposal",
            }
        )
    return result


def _deferred_or_rejected_actions(
    proposal: NewTcDraftProposal,
    review: NewTcDraftReviewReport,
    items: list[DraftRevisionItem],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in items:
        if item.target_revision_status in {"replace", "defer", "keep_rejected"}:
            actions.append(
                {
                    "draft_id": item.draft_id,
                    "proposed_tc_id": item.proposed_tc_id,
                    "current_review_status": item.current_review_status,
                    "target_revision_status": item.target_revision_status,
                    "reason": "; ".join(item.required_fixes[:3]) or "review status requires explicit handling",
                    "required_manual_decision": "Revise by replacement, defer, or keep rejected; do not silently approve.",
                }
            )
    for group in proposal.deferred_groups:
        actions.append(
            {
                "draft_id": None,
                "group_id": group.group_id,
                "target_revision_status": "defer",
                "reason": group.reason,
                "required_manual_decision": group.required_manual_decision,
            }
        )
    return actions


def _plan(
    *,
    package_id: str,
    source_review_path: str,
    source_proposal_path: str,
    input_paths: dict[str, str | None],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
    revision_items: list[DraftRevisionItem] | None = None,
    duplicate_risk_actions: list[DuplicateRiskAction] | None = None,
    source_grounding_actions: list[SourceGroundingAction] | None = None,
    coverage_actions: list[dict[str, Any]] | None = None,
    deferred_or_rejected_actions: list[dict[str, Any]] | None = None,
) -> NewTcDraftRevisionPlan:
    revision_items = revision_items or []
    duplicate_risk_actions = duplicate_risk_actions or []
    source_grounding_actions = source_grounding_actions or []
    coverage_actions = coverage_actions or []
    deferred_or_rejected_actions = deferred_or_rejected_actions or []
    counts = Counter(item.target_revision_status for item in revision_items)
    unresolved_count = (
        counts.get("defer", 0)
        + counts.get("keep_rejected", 0)
        + sum(1 for item in revision_items if item.blocking_questions)
        + sum(1 for action in duplicate_risk_actions if action.action in {"differentiate", "defer", "maybe_extend_existing"})
    )
    ready = bool(revision_items) and unresolved_count == 0
    revision_summary = {
        "revision_items_total": len(revision_items),
        "revise_count": counts.get("revise", 0),
        "replace_count": counts.get("replace", 0),
        "defer_count": counts.get("defer", 0),
        "keep_rejected_count": counts.get("keep_rejected", 0),
        "duplicate_risk_actions_count": len(duplicate_risk_actions),
        "source_grounding_actions_count": len(source_grounding_actions),
        "coverage_actions_count": len(coverage_actions),
        "deferred_or_rejected_actions_count": len(deferred_or_rejected_actions),
        "unresolved_manual_decisions_count": unresolved_count,
    }
    if blocking_reasons:
        status: PlanStatus = "blocked"
    elif warnings or not ready or counts.get("replace", 0) or counts.get("defer", 0) or counts.get("keep_rejected", 0):
        status = "pass-with-warnings"
    else:
        status = "pass"
    return NewTcDraftRevisionPlan(
        package_id=package_id,
        plan_status=status,
        source_review_path=source_review_path,
        source_proposal_path=source_proposal_path,
        revision_items=revision_items,
        duplicate_risk_actions=duplicate_risk_actions,
        source_grounding_actions=source_grounding_actions,
        coverage_actions=coverage_actions,
        deferred_or_rejected_actions=deferred_or_rejected_actions,
        revision_summary=revision_summary,
        ready_for_revised_draft_proposal=ready,
        canonical_write_allowed=False,
        manual_review_required=True,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _required_fixes(review: DraftTestCaseReview | None, target: TargetRevisionStatus) -> list[str]:
    fixes = list(review.required_fixes if review else ["Recover missing draft review before revision."])
    if target == "replace":
        fixes.append("Replace this draft with a new draft candidate; do not patch the rejected draft in place.")
    if target == "defer":
        fixes.append("Defer until duplicate/source ambiguity is resolved.")
    return _unique(fixes)


def _source_facts(
    draft: DraftTestCaseCandidate,
    candidate_by_req: dict[str, CandidateRequirement],
) -> list[str]:
    facts: list[str] = []
    for req_uid in draft.source_requirement_uids:
        candidate = candidate_by_req.get(req_uid)
        if not candidate:
            continue
        facts.extend(_candidate_usable_facts(candidate))
    return _unique(facts)


def _candidate_usable_facts(candidate: CandidateRequirement) -> list[str]:
    facts: list[str] = []
    if candidate.object:
        facts.append(f"object: {candidate.object}")
    if candidate.condition:
        facts.append(f"condition: {candidate.condition}")
    if candidate.expected_behavior:
        facts.append(f"expected_behavior: {candidate.expected_behavior}")
    if candidate.source_text:
        facts.append(f"source_text: {candidate.source_text}")
    if candidate.source_req_id:
        facts.append(f"source_req_id: {candidate.source_req_id}")
    return facts


def _candidate_missing_facts(candidate: CandidateRequirement) -> list[str]:
    missing: list[str] = []
    if not candidate.condition:
        missing.append("source-backed navigation/action condition")
    if not candidate.expected_behavior:
        missing.append("observable expected behavior")
    if not candidate.object:
        missing.append("specific object/field/screen")
    return missing


def _step_guidance(draft: DraftTestCaseCandidate, candidate_by_req: dict[str, CandidateRequirement]) -> list[str]:
    guidance = ["Replace generic placeholder steps with user-visible actions backed by source facts."]
    for req_uid in draft.source_requirement_uids:
        candidate = candidate_by_req.get(req_uid)
        if candidate and candidate.condition:
            guidance.append(f"Use condition as setup/action basis for {req_uid}: {candidate.condition}")
        if candidate and candidate.object:
            guidance.append(f"Name the concrete object/field/screen for {req_uid}: {candidate.object}")
    return _unique(guidance)


def _expected_result_guidance(draft: DraftTestCaseCandidate, candidate_by_req: dict[str, CandidateRequirement]) -> list[str]:
    guidance: list[str] = []
    for req_uid in draft.source_requirement_uids:
        candidate = candidate_by_req.get(req_uid)
        if candidate and candidate.expected_behavior:
            guidance.append(f"Use observable expected behavior for {req_uid}: {candidate.expected_behavior}")
        elif candidate and candidate.normalized_text:
            guidance.append(f"Derive only observable result from normalized source text for {req_uid}: {candidate.normalized_text}")
    if not guidance:
        guidance.append("Need source-backed expected behavior before creating canonical TC.")
    return _unique(guidance)


def _test_data_guidance(draft: DraftTestCaseCandidate, candidate_by_req: dict[str, CandidateRequirement]) -> list[str]:
    guidance = ["Use exact source-backed values only; otherwise keep test data as a blocking question."]
    for req_uid in draft.source_requirement_uids:
        candidate = candidate_by_req.get(req_uid)
        if candidate and candidate.source_req_id:
            guidance.append(f"Trace test data decision to {candidate.source_req_id}.")
    return _unique(guidance)


def _traceability_guidance(draft: DraftTestCaseCandidate, candidate_by_req: dict[str, CandidateRequirement]) -> list[str]:
    refs: list[str] = []
    for req_uid in draft.source_requirement_uids:
        candidate = candidate_by_req.get(req_uid)
        refs.append(req_uid)
        if candidate and candidate.source_req_id:
            refs.append(candidate.source_req_id)
    return [f"Preserve draft traceability refs: {', '.join(_unique(refs))}."]


def _duplicate_guidance(draft: DraftTestCaseCandidate, decisions_by_req: dict[str, list[Any]]) -> list[str]:
    guidance: list[str] = []
    for req_uid in draft.source_requirement_uids:
        for decision in decisions_by_req.get(req_uid, []):
            guidance.append(
                f"{decision.risk} duplicate risk vs {decision.similar_tc_id} in {decision.similar_file_path}: {decision.rationale}"
            )
    return _unique(guidance)


def _blocking_questions(
    draft: DraftTestCaseCandidate,
    candidate_by_req: dict[str, CandidateRequirement],
) -> list[str]:
    questions: list[str] = []
    for req_uid in draft.source_requirement_uids:
        candidate = candidate_by_req.get(req_uid)
        if candidate is None:
            questions.append(f"Need context bundle candidate requirement for {req_uid}.")
            continue
        missing = _candidate_missing_facts(candidate)
        if "source-backed navigation/action condition" in missing:
            questions.append(f"Need source-backed navigation/action details before creating canonical TC for {req_uid}.")
        if "observable expected behavior" in missing:
            questions.append(f"Need observable expected result before creating canonical TC for {req_uid}.")
    return _unique(questions)


def _source_revision_instruction(candidate: CandidateRequirement, missing: list[str]) -> str:
    if missing:
        return "Use available source facts, but keep draft blocked on missing facts: " + ", ".join(missing)
    return "Use these source facts to make title, setup, action and expected result concrete."


def _priority(
    target: TargetRevisionStatus,
    review: DraftTestCaseReview | None,
    duplicate_guidance: list[str],
    blocking_questions: list[str],
) -> Priority:
    if target in {"replace", "defer", "keep_rejected"} or blocking_questions:
        return "high"
    if duplicate_guidance or (review and review.quality_score == "medium"):
        return "medium"
    return "low"


def _item_acceptance_criteria(target: TargetRevisionStatus) -> list[str]:
    criteria = [
        "Draft remains draft-only and does not use authoritative canonical TC ID.",
        "Traceability includes req_uid plus source_req_id when available.",
        "Steps are concrete user-visible actions, not placeholders.",
        "Expected result is observable and source-backed.",
        "Duplicate risk is resolved or explicitly deferred.",
    ]
    if target == "replace":
        criteria.append("Replacement draft addresses all rejected-draft required fixes.")
    if target == "defer":
        criteria.append("Deferred reason and required manual decision remain visible.")
    return criteria


def _global_acceptance_criteria() -> list[str]:
    return [
        "No canonical test-case file is created or edited.",
        "Original Stage 9B proposal remains unchanged.",
        "All 16 candidate requirements are revised, replaced, or explicitly deferred.",
        "No draft is marked ready for controlled create apply without duplicate-risk resolution.",
        "Each revised draft has source-backed steps, test data and observable expected result.",
    ]


def _has_valid_source_mapping(
    draft: DraftTestCaseCandidate,
    candidate_by_req: dict[str, CandidateRequirement],
) -> bool:
    return any(req_uid in candidate_by_req for req_uid in draft.source_requirement_uids)


def _duplicate_decisions_by_req(proposal: NewTcDraftProposal) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for decision in proposal.duplicate_risk_decisions:
        if decision.candidate_req_uid:
            grouped[decision.candidate_req_uid].append(decision)
    return grouped


def _draft_req_uids(proposal: NewTcDraftProposal, draft_id: str) -> list[str]:
    for draft in proposal.draft_test_cases:
        if draft.draft_id == draft_id:
            return list(draft.source_requirement_uids)
    return []


def _load_optional(path: Path, loader: Any, label: str, blocking_reasons: list[str]) -> Any:
    if not Path(path).exists():
        return None
    try:
        return loader(Path(path))
    except Exception as exc:  # noqa: BLE001 - plan reports artifact parse failures.
        blocking_reasons.append(f"{label} cannot be parsed: {path}: {exc}")
        return None


def _input_paths(**paths: Path | None) -> dict[str, str | None]:
    return {key: (str(value) if value is not None else None) for key, value in paths.items()}


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
