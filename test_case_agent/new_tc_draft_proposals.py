from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.create_new_tc_context_bundle import (
    CreateNewTcContextBundle,
    load_create_new_tc_context_bundle,
)

CREATED_BY_TOOL = "test_case_agent.new_tc_draft_proposals"
PROPOSAL_PREFIX = "new-tc-draft-proposal"
DEFAULT_PACKAGE_ID = "WPKG-000001"

ProposalStatus = Literal["pass", "pass-with-warnings", "blocked"]
RiskLevel = Literal["low", "medium", "high"]
DraftConfidence = Literal["low", "medium", "high"]
DuplicateDecision = Literal["draft_with_warning", "defer", "maybe_extend_existing_tc", "needs_manual_review"]


@dataclass(frozen=True)
class SourceGroundingProfile:
    req_uid: str | None
    source_req_id: str | None
    object: str | None
    condition: str | None
    user_action: str | None
    observable_expected_behavior: str | None
    source_text: str | None
    normalized_text: str | None
    source_anchors: list[dict[str, Any]]
    has_concrete_object: bool
    has_concrete_condition: bool
    has_user_action: bool
    has_observable_expected_behavior: bool
    can_support_executable_steps: bool
    can_support_observable_expected_result: bool
    missing_facts: list[str]
    grounding_confidence: DraftConfidence
    manual_questions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_uid": self.req_uid,
            "source_req_id": self.source_req_id,
            "object": self.object,
            "condition": self.condition,
            "user_action": self.user_action,
            "observable_expected_behavior": self.observable_expected_behavior,
            "source_text": self.source_text,
            "normalized_text": self.normalized_text,
            "source_anchors": self.source_anchors,
            "has_concrete_object": self.has_concrete_object,
            "has_concrete_condition": self.has_concrete_condition,
            "has_user_action": self.has_user_action,
            "has_observable_expected_behavior": self.has_observable_expected_behavior,
            "can_support_executable_steps": self.can_support_executable_steps,
            "can_support_observable_expected_result": self.can_support_observable_expected_result,
            "missing_facts": self.missing_facts,
            "grounding_confidence": self.grounding_confidence,
            "manual_questions": self.manual_questions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceGroundingProfile":
        return cls(
            req_uid=data.get("req_uid"),
            source_req_id=data.get("source_req_id"),
            object=data.get("object"),
            condition=data.get("condition"),
            user_action=data.get("user_action"),
            observable_expected_behavior=data.get("observable_expected_behavior"),
            source_text=data.get("source_text"),
            normalized_text=data.get("normalized_text"),
            source_anchors=list(data.get("source_anchors") or []),
            has_concrete_object=bool(data.get("has_concrete_object")),
            has_concrete_condition=bool(data.get("has_concrete_condition")),
            has_user_action=bool(data.get("has_user_action")),
            has_observable_expected_behavior=bool(data.get("has_observable_expected_behavior")),
            can_support_executable_steps=bool(data.get("can_support_executable_steps")),
            can_support_observable_expected_result=bool(data.get("can_support_observable_expected_result")),
            missing_facts=list(data.get("missing_facts") or []),
            grounding_confidence=data.get("grounding_confidence") or "low",
            manual_questions=list(data.get("manual_questions") or []),
        )


@dataclass(frozen=True)
class DraftTestCaseCandidate:
    draft_id: str
    proposed_tc_id: str
    target_file_path: str
    target_section: str | None
    requires_new_file: bool
    title: str
    source_requirement_uids: list[str]
    source_req_ids: list[str]
    change_ids: list[str]
    impact_ids: list[str]
    plan_item_ids: list[str]
    coverage_intent: str
    preconditions: list[str]
    test_data: list[str]
    steps: list[str]
    expected_results: list[str]
    traceability_refs: list[str]
    traceability_line: str
    duplicate_risk_level: RiskLevel
    duplicate_risk_notes: list[str]
    draft_confidence: DraftConfidence
    requires_manual_review: bool
    warnings: list[str]
    source_grounding_profiles: list[SourceGroundingProfile] = field(default_factory=list)
    grounding_confidence: DraftConfidence = "low"
    manual_questions: list[str] = field(default_factory=list)
    contains_generic_placeholders: bool = False
    draft_quality_flags: list[str] = field(default_factory=list)
    is_executable_draft: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "proposed_tc_id": self.proposed_tc_id,
            "target_file_path": self.target_file_path,
            "target_section": self.target_section,
            "requires_new_file": self.requires_new_file,
            "title": self.title,
            "source_requirement_uids": self.source_requirement_uids,
            "source_req_ids": self.source_req_ids,
            "change_ids": self.change_ids,
            "impact_ids": self.impact_ids,
            "plan_item_ids": self.plan_item_ids,
            "coverage_intent": self.coverage_intent,
            "preconditions": self.preconditions,
            "test_data": self.test_data,
            "steps": self.steps,
            "expected_results": self.expected_results,
            "traceability_refs": self.traceability_refs,
            "traceability_line": self.traceability_line,
            "duplicate_risk_level": self.duplicate_risk_level,
            "duplicate_risk_notes": self.duplicate_risk_notes,
            "draft_confidence": self.draft_confidence,
            "requires_manual_review": self.requires_manual_review,
            "warnings": self.warnings,
            "source_grounding_profiles": [profile.to_dict() for profile in self.source_grounding_profiles],
            "grounding_confidence": self.grounding_confidence,
            "manual_questions": self.manual_questions,
            "contains_generic_placeholders": self.contains_generic_placeholders,
            "draft_quality_flags": self.draft_quality_flags,
            "is_executable_draft": self.is_executable_draft,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DraftTestCaseCandidate":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            target_file_path=str(data["target_file_path"]),
            target_section=data.get("target_section"),
            requires_new_file=bool(data.get("requires_new_file")),
            title=str(data["title"]),
            source_requirement_uids=list(data.get("source_requirement_uids") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            change_ids=list(data.get("change_ids") or []),
            impact_ids=list(data.get("impact_ids") or []),
            plan_item_ids=list(data.get("plan_item_ids") or []),
            coverage_intent=str(data["coverage_intent"]),
            preconditions=list(data.get("preconditions") or []),
            test_data=list(data.get("test_data") or []),
            steps=list(data.get("steps") or []),
            expected_results=list(data.get("expected_results") or []),
            traceability_refs=list(data.get("traceability_refs") or []),
            traceability_line=str(data["traceability_line"]),
            duplicate_risk_level=data["duplicate_risk_level"],
            duplicate_risk_notes=list(data.get("duplicate_risk_notes") or []),
            draft_confidence=data["draft_confidence"],
            requires_manual_review=bool(data.get("requires_manual_review")),
            warnings=list(data.get("warnings") or []),
            source_grounding_profiles=[
                SourceGroundingProfile.from_dict(item)
                for item in data.get("source_grounding_profiles", [])
            ],
            grounding_confidence=data.get("grounding_confidence") or data.get("draft_confidence") or "low",
            manual_questions=list(data.get("manual_questions") or []),
            contains_generic_placeholders=bool(data.get("contains_generic_placeholders")),
            draft_quality_flags=list(data.get("draft_quality_flags") or []),
            is_executable_draft=bool(data.get("is_executable_draft")),
        )


@dataclass(frozen=True)
class DeferredGroup:
    group_id: str
    candidate_req_uids: list[str]
    reason: str
    required_manual_decision: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "candidate_req_uids": self.candidate_req_uids,
            "reason": self.reason,
            "required_manual_decision": self.required_manual_decision,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeferredGroup":
        return cls(
            group_id=str(data["group_id"]),
            candidate_req_uids=list(data.get("candidate_req_uids") or []),
            reason=str(data["reason"]),
            required_manual_decision=str(data["required_manual_decision"]),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class DuplicateRiskDecision:
    candidate_req_uid: str | None
    similar_tc_id: str
    similar_file_path: str
    risk: RiskLevel
    decision: DuplicateDecision
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_req_uid": self.candidate_req_uid,
            "similar_tc_id": self.similar_tc_id,
            "similar_file_path": self.similar_file_path,
            "risk": self.risk,
            "decision": self.decision,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DuplicateRiskDecision":
        return cls(
            candidate_req_uid=data.get("candidate_req_uid"),
            similar_tc_id=str(data["similar_tc_id"]),
            similar_file_path=str(data["similar_file_path"]),
            risk=data["risk"],
            decision=data["decision"],
            rationale=str(data["rationale"]),
        )


@dataclass
class NewTcDraftProposal:
    package_id: str
    proposal_status: ProposalStatus
    package_type: str | None
    source_bundle_path: str
    draft_test_cases: list[DraftTestCaseCandidate]
    deferred_groups: list[DeferredGroup]
    duplicate_risk_decisions: list[DuplicateRiskDecision]
    coverage_summary: dict[str, Any]
    recommended_review_focus: list[str]
    manual_review_required: bool
    canonical_write_allowed: bool
    input_paths: dict[str, str]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "proposal_status": self.proposal_status,
            "package_type": self.package_type,
            "source_bundle_path": self.source_bundle_path,
            "draft_test_cases": [item.to_dict() for item in self.draft_test_cases],
            "deferred_groups": [item.to_dict() for item in self.deferred_groups],
            "duplicate_risk_decisions": [item.to_dict() for item in self.duplicate_risk_decisions],
            "coverage_summary": self.coverage_summary,
            "recommended_review_focus": self.recommended_review_focus,
            "manual_review_required": self.manual_review_required,
            "canonical_write_allowed": self.canonical_write_allowed,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcDraftProposal":
        return cls(
            package_id=str(data["package_id"]),
            proposal_status=data["proposal_status"],
            package_type=data.get("package_type"),
            source_bundle_path=str(data["source_bundle_path"]),
            draft_test_cases=[
                DraftTestCaseCandidate.from_dict(item)
                for item in data.get("draft_test_cases", [])
            ],
            deferred_groups=[
                DeferredGroup.from_dict(item)
                for item in data.get("deferred_groups", [])
            ],
            duplicate_risk_decisions=[
                DuplicateRiskDecision.from_dict(item)
                for item in data.get("duplicate_risk_decisions", [])
            ],
            coverage_summary=dict(data.get("coverage_summary") or {}),
            recommended_review_focus=list(data.get("recommended_review_focus") or []),
            manual_review_required=bool(data.get("manual_review_required")),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_new_tc_draft_proposal(
    *,
    package_id: str,
    context_bundle_path: Path,
    test_cases_dir: Path,
    manual_update_packages_path: Path | None = None,
    writer_package_tasks_path: Path | None = None,
    update_plan_path: Path | None = None,
    impact_report_path: Path | None = None,
    requirements_diff_path: Path | None = None,
    old_registry_path: Path | None = None,
    new_registry_path: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> NewTcDraftProposal:
    input_paths = _input_paths(
        context_bundle_path=context_bundle_path,
        test_cases_dir=test_cases_dir,
        manual_update_packages_path=manual_update_packages_path,
        writer_package_tasks_path=writer_package_tasks_path,
        update_plan_path=update_plan_path,
        impact_report_path=impact_report_path,
        requirements_diff_path=requirements_diff_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
    )
    warnings: list[str] = []
    blocking_reasons: list[str] = []

    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"this draft proposal builder is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if not Path(context_bundle_path).exists():
        blocking_reasons.append(f"context bundle file is missing: {context_bundle_path}")
    for label, path in input_paths.items():
        if label in {"context_bundle_path", "test_cases_dir"}:
            continue
        if path and not Path(path).exists():
            warnings.append(f"optional input artifact is missing: {path}")
    if not Path(test_cases_dir).exists() or not Path(test_cases_dir).is_dir():
        blocking_reasons.append(f"test-cases dir is missing: {test_cases_dir}")

    bundle: CreateNewTcContextBundle | None = None
    if Path(context_bundle_path).exists():
        try:
            bundle = load_create_new_tc_context_bundle(Path(context_bundle_path))
        except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
            blocking_reasons.append(f"context bundle cannot be parsed: {context_bundle_path}: {exc}")

    if bundle is not None:
        if bundle.package_id != package_id:
            blocking_reasons.append(f"context bundle package_id mismatch: {bundle.package_id} != {package_id}")
        if bundle.package_type != "create_new_candidate":
            blocking_reasons.append(f"context bundle package_type must be create_new_candidate: {bundle.package_type}")
        if bundle.blocking_reasons:
            blocking_reasons.extend(f"context bundle blocker: {reason}" for reason in bundle.blocking_reasons)
        warnings.extend(bundle.warnings)

    if blocking_reasons or bundle is None:
        return _proposal(
            package_id=package_id,
            package_type=bundle.package_type if bundle else None,
            source_bundle_path=str(context_bundle_path),
            input_paths=input_paths,
            warnings=_unique(warnings),
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    duplicate_decisions = _duplicate_risk_decisions(bundle)
    drafts: list[DraftTestCaseCandidate] = []
    deferred: list[DeferredGroup] = []
    targets_by_group = {
        group.group_id: target
        for group, target in zip(bundle.candidate_groups, bundle.recommended_draft_targets)
    }
    candidates_by_req = {
        candidate.req_uid: candidate
        for candidate in bundle.candidate_requirements
        if candidate.req_uid
    }
    decisions_by_req = _decisions_by_req(duplicate_decisions)

    for group in bundle.candidate_groups:
        group_decisions = [
            decision
            for req_uid in group.candidate_req_uids
            for decision in decisions_by_req.get(req_uid, [])
        ]
        high_risk = any(decision.risk == "high" for decision in group_decisions)
        missing_candidates = [
            req_uid for req_uid in group.candidate_req_uids
            if req_uid not in candidates_by_req
        ]
        group_candidates = [
            candidates_by_req[req_uid]
            for req_uid in group.candidate_req_uids
            if req_uid in candidates_by_req
        ]
        if not group.draft_allowed:
            deferred.append(_deferred(group, "context bundle marks draft_allowed=false"))
            continue
        if missing_candidates:
            deferred.append(_deferred(group, f"candidate requirements missing from bundle: {', '.join(missing_candidates)}"))
            continue
        if high_risk:
            deferred.append(_deferred(group, "high duplicate risk requires manual decision before drafting"))
            continue
        if not group_candidates:
            deferred.append(_deferred(group, "group has no candidate requirements"))
            continue
        draft_count = max(1, int(group.suggested_tc_count or 1))
        split_candidates = group_candidates if draft_count > 1 else [None]
        for split_candidate in split_candidates:
            candidate_subset = [split_candidate] if split_candidate is not None else group_candidates
            target = targets_by_group.get(group.group_id)
            drafts.append(
                _draft_candidate(
                    index=len(drafts) + 1,
                    package_id=package_id,
                    group=group,
                    candidates=candidate_subset,
                    target=target,
                    duplicate_decisions=group_decisions,
                )
            )

    proposal_warnings = _unique(
        [
            *warnings,
            *(
                warning
                for draft in drafts
                for warning in draft.warnings
            ),
            *(
                warning
                for group in deferred
                for warning in group.warnings
            ),
        ]
    )
    if duplicate_decisions:
        proposal_warnings.append("duplicate risk decisions require reviewer confirmation before canonical TC creation.")
    if drafts:
        proposal_warnings.append("draft TC candidates are not canonical and must not be applied without review.")

    return _proposal(
        package_id=package_id,
        package_type=bundle.package_type,
        source_bundle_path=str(context_bundle_path),
        draft_test_cases=drafts,
        deferred_groups=deferred,
        duplicate_risk_decisions=duplicate_decisions,
        coverage_summary=_coverage_summary(bundle, drafts, deferred),
        recommended_review_focus=_review_focus(bundle, drafts, deferred, duplicate_decisions),
        input_paths=input_paths,
        warnings=_unique(proposal_warnings),
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_new_tc_draft_proposal(
    proposal: NewTcDraftProposal,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{PROPOSAL_PREFIX}-{proposal.package_id}.json"
    markdown_path = out_dir / f"{PROPOSAL_PREFIX}-{proposal.package_id}.md"
    json_path.write_text(
        json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_new_tc_draft_proposal_markdown(proposal),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_new_tc_draft_proposal(path: Path) -> NewTcDraftProposal:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("New TC draft proposal root must be a JSON object.")
    return NewTcDraftProposal.from_dict(payload)


def render_new_tc_draft_proposal_markdown(proposal: NewTcDraftProposal) -> str:
    lines = [
        f"# New TC Draft Proposal {proposal.package_id}",
        "",
        "## Summary",
        "",
        f"- Proposal status: `{proposal.proposal_status}`",
        f"- Package type: `{proposal.package_type}`",
        f"- Draft test cases: `{len(proposal.draft_test_cases)}`",
        f"- Deferred groups: `{len(proposal.deferred_groups)}`",
        f"- Duplicate risk decisions: `{len(proposal.duplicate_risk_decisions)}`",
        f"- Manual review required: `{str(proposal.manual_review_required).lower()}`",
        f"- Canonical write allowed: `{str(proposal.canonical_write_allowed).lower()}`",
        "",
        "## Safety Statement",
        "",
        "- Draft-only artifact.",
        "- No canonical TC was created.",
        "- No canonical TC was edited.",
        "- Manual review is required before any canonical create/apply stage.",
        "",
        "## Draft TC Candidates",
        "",
    ]
    if proposal.draft_test_cases:
        for draft in proposal.draft_test_cases:
            lines.extend(_draft_markdown_lines(draft))
    else:
        lines.append("- none")

    lines.extend(["", "## Deferred Groups", ""])
    if proposal.deferred_groups:
        for group in proposal.deferred_groups:
            lines.append(f"- `{group.group_id}` `{group.required_manual_decision}`: {group.reason}")
            lines.append(f"  - candidate reqs: {', '.join(group.candidate_req_uids) or 'n/a'}")
    else:
        lines.append("- none")

    lines.extend(["", "## Duplicate Risk Decisions", ""])
    if proposal.duplicate_risk_decisions:
        for decision in proposal.duplicate_risk_decisions:
            lines.append(
                f"- `{decision.candidate_req_uid or 'n/a'}` -> `{decision.similar_tc_id}` "
                f"`{decision.risk}` `{decision.decision}`: {decision.rationale}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Review Focus Checklist", ""])
    _append_list(lines, proposal.recommended_review_focus)
    lines.extend(["", "## Warnings", ""])
    _append_list(lines, proposal.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, proposal.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _draft_markdown_lines(draft: DraftTestCaseCandidate) -> list[str]:
    lines = [
        f"### {draft.proposed_tc_id}",
        "",
        f"- Draft ID: `{draft.draft_id}`",
        f"- Target file recommendation: `{draft.target_file_path}`",
        f"- Target section: `{draft.target_section or 'n/a'}`",
        f"- Requires new file: `{str(draft.requires_new_file).lower()}`",
        f"- Duplicate risk: `{draft.duplicate_risk_level}`",
        f"- Draft confidence: `{draft.draft_confidence}`",
        "",
        f"**Название:** {draft.title}",
        f"**Трассировка:** {draft.traceability_line}",
        "",
        f"**Coverage intent:** {draft.coverage_intent}",
        "",
        "**Preconditions:**",
    ]
    _append_list(lines, draft.preconditions)
    lines.extend(["", "**Test data:**"])
    _append_list(lines, draft.test_data)
    lines.extend(["", "**Steps:**"])
    for index, step in enumerate(draft.steps, start=1):
        lines.append(f"{index}. {step}")
    lines.extend(["", "**Expected results:**"])
    _append_list(lines, draft.expected_results)
    lines.extend(["", "**Duplicate risk notes:**"])
    _append_list(lines, draft.duplicate_risk_notes)
    if draft.warnings:
        lines.extend(["", "**Warnings:**"])
        _append_list(lines, draft.warnings)
    lines.append("")
    return lines


def _draft_candidate(
    *,
    index: int,
    package_id: str,
    group: Any,
    candidates: list[Any],
    target: Any | None,
    duplicate_decisions: list[DuplicateRiskDecision],
) -> DraftTestCaseCandidate:
    req_uids = _unique(candidate.req_uid for candidate in candidates if candidate.req_uid)
    source_req_ids = _unique(candidate.source_req_id for candidate in candidates if candidate.source_req_id)
    change_ids = _unique(candidate.diff_entry_id for candidate in candidates if candidate.diff_entry_id)
    impact_ids = _unique(candidate.impact_id for candidate in candidates if candidate.impact_id)
    plan_item_ids = _unique(candidate.plan_item_id for candidate in candidates if candidate.plan_item_id)
    traceability_refs = _unique([*req_uids, *source_req_ids])
    duplicate_risk_level = _max_risk([decision.risk for decision in duplicate_decisions])
    grounding_profiles = [_source_grounding_profile(candidate) for candidate in candidates]
    is_executable = bool(grounding_profiles) and all(
        profile.can_support_executable_steps and profile.can_support_observable_expected_result
        for profile in grounding_profiles
    )
    grounding_confidence = _grounding_confidence(grounding_profiles)
    manual_questions = _unique(question for profile in grounding_profiles for question in profile.manual_questions)
    draft_quality_flags: list[str] = []
    if not is_executable:
        draft_quality_flags.append("not_executable_without_manual_source_grounding")
    if any(not profile.has_user_action for profile in grounding_profiles):
        draft_quality_flags.append("missing_user_action")
    if any(not profile.has_observable_expected_behavior for profile in grounding_profiles):
        draft_quality_flags.append("missing_observable_expected_behavior")
    if any(not profile.has_concrete_object for profile in grounding_profiles):
        draft_quality_flags.append("missing_concrete_object")
    warnings = _unique([
        *group.warnings,
        *(
            warning
            for candidate in candidates
            for warning in candidate.warnings
        ),
    ])
    warnings.extend(f"manual source-grounding question: {question}" for question in manual_questions)
    if duplicate_risk_level in {"medium", "high"}:
        warnings.append(f"{duplicate_risk_level} duplicate risk requires reviewer confirmation.")
    if any(candidate.confidence == "low" for candidate in candidates):
        draft_confidence: DraftConfidence = "low"
    elif warnings or duplicate_risk_level == "medium":
        draft_confidence = "medium"
    else:
        draft_confidence = "high"

    title_base = _first_text(
        [candidate.object for candidate in candidates]
        + [candidate.expected_behavior for candidate in candidates]
        + [group.suggested_tc_theme]
    )
    steps = _draft_steps(grounding_profiles, is_executable)
    expected_results = _draft_expected_results(grounding_profiles, is_executable)
    contains_placeholders = any(_is_generic_placeholder(step) for step in steps) or any(
        _is_generic_placeholder(result) for result in expected_results
    )
    if contains_placeholders:
        draft_quality_flags.append("contains_generic_placeholders")

    return DraftTestCaseCandidate(
        draft_id=f"DRAFT-{index:06d}",
        proposed_tc_id=f"DRAFT-TC-{package_id}-{index:03d}",
        target_file_path=target.target_file_path if target else f"draft-only/{package_id}/{group.group_id}.md",
        target_section=target.target_section if target else group.suggested_tc_theme,
        requires_new_file=bool(target.requires_new_file) if target else True,
        title=f"Draft review candidate: {title_base[:160]}",
        source_requirement_uids=req_uids,
        source_req_ids=source_req_ids,
        change_ids=change_ids,
        impact_ids=impact_ids,
        plan_item_ids=plan_item_ids,
        coverage_intent=_coverage_intent(candidates),
        preconditions=_draft_preconditions(grounding_profiles, is_executable),
        test_data=[
            _test_data_note(candidates),
        ],
        steps=steps,
        expected_results=expected_results,
        traceability_refs=traceability_refs,
        traceability_line=", ".join(traceability_refs),
        duplicate_risk_level=duplicate_risk_level,
        duplicate_risk_notes=[
            f"{decision.risk}: possible overlap with {decision.similar_tc_id} in {decision.similar_file_path}"
            for decision in duplicate_decisions[:10]
        ],
        draft_confidence=draft_confidence,
        requires_manual_review=True,
        warnings=_unique(warnings),
        source_grounding_profiles=grounding_profiles,
        grounding_confidence=grounding_confidence,
        manual_questions=manual_questions,
        contains_generic_placeholders=contains_placeholders,
        draft_quality_flags=_unique(draft_quality_flags),
        is_executable_draft=is_executable and not contains_placeholders,
    )


def _duplicate_risk_decisions(bundle: CreateNewTcContextBundle) -> list[DuplicateRiskDecision]:
    decisions: list[DuplicateRiskDecision] = []
    for risk in bundle.duplicate_risks:
        risk_level = risk.get("risk", "medium")
        if risk_level == "high":
            decision: DuplicateDecision = "defer"
            rationale = "High duplicate risk: existing TC may already cover the requirement."
        elif risk_level == "medium":
            decision = "draft_with_warning"
            rationale = "Medium duplicate risk: draft is allowed only with clear differentiation and manual review."
        else:
            decision = "draft_with_warning"
            rationale = "Low duplicate risk: draft allowed, still requires review."
        decisions.append(
            DuplicateRiskDecision(
                candidate_req_uid=risk.get("candidate_req_uid"),
                similar_tc_id=str(risk.get("similar_tc_id") or "unknown"),
                similar_file_path=str(risk.get("similar_file_path") or "unknown"),
                risk=risk_level,
                decision=decision,
                rationale=rationale,
            )
        )
    return decisions


def _source_grounding_profile(candidate: Any) -> SourceGroundingProfile:
    user_action = _derive_user_action(candidate)
    missing: list[str] = []
    has_object = bool(candidate.object)
    has_condition = bool(candidate.condition)
    has_action = bool(user_action)
    has_expected = bool(candidate.expected_behavior)
    if not has_object:
        missing.append("specific object/screen/field")
    if not has_condition:
        missing.append("source-backed condition")
    if not has_action:
        missing.append("source-backed user action")
    if not has_expected:
        missing.append("observable expected behavior")
    manual_questions = [
        f"Provide {fact} for {candidate.req_uid or candidate.source_req_id or 'candidate requirement'}."
        for fact in missing
    ]
    can_steps = has_object and has_action
    can_expected = has_expected
    if can_steps and can_expected:
        confidence: DraftConfidence = "high" if candidate.confidence == "high" else "medium"
    elif can_steps or can_expected:
        confidence = "medium"
    else:
        confidence = "low"
    return SourceGroundingProfile(
        req_uid=candidate.req_uid,
        source_req_id=candidate.source_req_id,
        object=candidate.object,
        condition=candidate.condition,
        user_action=user_action,
        observable_expected_behavior=candidate.expected_behavior,
        source_text=candidate.source_text,
        normalized_text=candidate.normalized_text,
        source_anchors=list(candidate.source_anchors or []),
        has_concrete_object=has_object,
        has_concrete_condition=has_condition,
        has_user_action=has_action,
        has_observable_expected_behavior=has_expected,
        can_support_executable_steps=can_steps,
        can_support_observable_expected_result=can_expected,
        missing_facts=missing,
        grounding_confidence=confidence,
        manual_questions=manual_questions,
    )


def _derive_user_action(candidate: Any) -> str | None:
    for value in [candidate.condition, candidate.source_text, candidate.normalized_text]:
        text = str(value or "").strip()
        if not text:
            continue
        lowered = text.casefold()
        if any(
            marker in lowered
            for marker in [
                "user ",
                "пользователь ",
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
        ):
            return text
    return None


def _draft_preconditions(
    profiles: list[SourceGroundingProfile],
    is_executable: bool,
) -> list[str]:
    if not is_executable:
        return [
            "Draft is not executable until manual source-grounding questions are resolved.",
            "Do not convert this draft to canonical TC without source-backed action and expected result.",
        ]
    objects = _unique(profile.object for profile in profiles if profile.object)
    return [f"Source-backed object/screen/field is in scope: {', '.join(objects)}."]


def _draft_steps(
    profiles: list[SourceGroundingProfile],
    is_executable: bool,
) -> list[str]:
    if not is_executable:
        questions = _unique(question for profile in profiles for question in profile.manual_questions)
        return [f"Resolve manual source-grounding question before drafting steps: {question}" for question in questions] or [
            "Resolve manual source-grounding questions before drafting executable steps."
        ]
    steps: list[str] = []
    for profile in profiles:
        if profile.user_action:
            steps.append(f"Perform the source-backed action: {profile.user_action}.")
    return _unique(steps)


def _draft_expected_results(
    profiles: list[SourceGroundingProfile],
    is_executable: bool,
) -> list[str]:
    if not is_executable:
        missing = _unique(
            fact
            for profile in profiles
            for fact in profile.missing_facts
            if fact == "observable expected behavior"
        )
        if missing:
            return ["Expected result is not draftable until observable expected behavior is source-backed."]
    results = [
        f"Observable expected behavior: {profile.observable_expected_behavior}."
        for profile in profiles
        if profile.observable_expected_behavior
    ]
    return _unique(results) or ["Expected result requires manual source-grounding before executable draft."]


def _grounding_confidence(profiles: list[SourceGroundingProfile]) -> DraftConfidence:
    if profiles and all(profile.grounding_confidence == "high" for profile in profiles):
        return "high"
    if profiles and any(profile.grounding_confidence in {"high", "medium"} for profile in profiles):
        return "medium"
    return "low"


def _is_generic_placeholder(value: str) -> bool:
    lowered = value.casefold()
    return any(
        pattern in lowered
        for pattern in [
            "open the screen or section identified by the source anchors",
            "set up the source-backed condition",
            "perform the user action needed to observe",
            "behavior is observed",
        ]
    )


def _deferred(group: Any, reason: str) -> DeferredGroup:
    return DeferredGroup(
        group_id=group.group_id,
        candidate_req_uids=list(group.candidate_req_uids),
        reason=reason,
        required_manual_decision="decide whether to draft new TC, extend existing TC, or mark no-new-TC rationale",
        warnings=list(group.warnings),
    )


def _coverage_summary(
    bundle: CreateNewTcContextBundle,
    drafts: list[DraftTestCaseCandidate],
    deferred: list[DeferredGroup],
) -> dict[str, Any]:
    drafted_req_uids = {
        req_uid
        for draft in drafts
        for req_uid in draft.source_requirement_uids
    }
    deferred_req_uids = {
        req_uid
        for group in deferred
        for req_uid in group.candidate_req_uids
    }
    total_req_uids = {
        candidate.req_uid
        for candidate in bundle.candidate_requirements
        if candidate.req_uid
    }
    return {
        "candidate_requirements_total": len(bundle.candidate_requirements),
        "candidate_groups_total": len(bundle.candidate_groups),
        "draft_test_cases_total": len(drafts),
        "deferred_groups_total": len(deferred),
        "drafted_req_uids_count": len(drafted_req_uids),
        "deferred_req_uids_count": len(deferred_req_uids),
        "undecided_req_uids": sorted(total_req_uids - drafted_req_uids - deferred_req_uids),
        "executable_drafts_count": sum(1 for draft in drafts if draft.is_executable_draft),
        "generic_placeholder_drafts_count": sum(1 for draft in drafts if draft.contains_generic_placeholders),
        "unresolved_source_grounding_drafts_count": sum(1 for draft in drafts if not draft.is_executable_draft),
        "canonical_write_allowed": False,
        "manual_review_required": True,
    }


def _review_focus(
    bundle: CreateNewTcContextBundle,
    drafts: list[DraftTestCaseCandidate],
    deferred: list[DeferredGroup],
    decisions: list[DuplicateRiskDecision],
) -> list[str]:
    focus = [
        "Confirm each draft covers one source-backed behavior and does not invent UI reactions.",
        "Confirm draft IDs are not treated as canonical TC IDs.",
        "Review duplicate risks before approving any canonical create stage.",
        "Confirm traceability refs match candidate requirements, plan items, impacts and diff changes.",
    ]
    if any("aggregate" in warning.casefold() for warning in bundle.warnings):
        focus.append("Review aggregate source context and verify direct source rows before canonical drafting.")
    if any(decision.risk in {"medium", "high"} for decision in decisions):
        focus.append("Differentiate new behavior from similar existing TC coverage.")
    if deferred:
        focus.append("Resolve deferred groups before controlled create apply.")
    if drafts:
        focus.append("Replace generic setup/test data placeholders with source-backed fixtures before canonicalization.")
    return _unique(focus)


def _proposal(
    *,
    package_id: str,
    package_type: str | None,
    source_bundle_path: str,
    input_paths: dict[str, str],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
    draft_test_cases: list[DraftTestCaseCandidate] | None = None,
    deferred_groups: list[DeferredGroup] | None = None,
    duplicate_risk_decisions: list[DuplicateRiskDecision] | None = None,
    coverage_summary: dict[str, Any] | None = None,
    recommended_review_focus: list[str] | None = None,
) -> NewTcDraftProposal:
    drafts = draft_test_cases or []
    deferred = deferred_groups or []
    decisions = duplicate_risk_decisions or []
    if blocking_reasons:
        status: ProposalStatus = "blocked"
    elif warnings or deferred or decisions or any(draft.requires_manual_review for draft in drafts):
        status = "pass-with-warnings"
    else:
        status = "pass"
    return NewTcDraftProposal(
        package_id=package_id,
        proposal_status=status,
        package_type=package_type,
        source_bundle_path=source_bundle_path,
        draft_test_cases=drafts,
        deferred_groups=deferred,
        duplicate_risk_decisions=decisions,
        coverage_summary=coverage_summary or {
            "draft_test_cases_total": len(drafts),
            "deferred_groups_total": len(deferred),
            "canonical_write_allowed": False,
            "manual_review_required": True,
        },
        recommended_review_focus=recommended_review_focus or [],
        manual_review_required=True,
        canonical_write_allowed=False,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _input_paths(**paths: Path | None) -> dict[str, str]:
    return {
        key: str(value)
        for key, value in paths.items()
        if value is not None
    }


def _decisions_by_req(decisions: list[DuplicateRiskDecision]) -> dict[str, list[DuplicateRiskDecision]]:
    grouped: dict[str, list[DuplicateRiskDecision]] = {}
    for decision in decisions:
        if not decision.candidate_req_uid:
            continue
        grouped.setdefault(decision.candidate_req_uid, []).append(decision)
    return grouped


def _max_risk(risks: list[RiskLevel]) -> RiskLevel:
    if "high" in risks:
        return "high"
    if "medium" in risks:
        return "medium"
    return "low"


def _coverage_intent(candidates: list[Any]) -> str:
    parts = _unique(
        candidate.expected_behavior or candidate.normalized_text or candidate.source_text
        for candidate in candidates
    )
    return "Cover source-backed behavior: " + "; ".join(part[:240] for part in parts if part)


def _test_data_note(candidates: list[Any]) -> str:
    source_req_ids = _unique(candidate.source_req_id for candidate in candidates if candidate.source_req_id)
    if source_req_ids:
        return "Use source-backed data for " + ", ".join(source_req_ids) + "; exact fixtures require review."
    return "Exact test data is not explicit in the bundle; reviewer must supply source-backed fixture values."


def _expected_result(candidates: list[Any]) -> str:
    behaviors = _unique(
        candidate.expected_behavior or candidate.normalized_text or candidate.source_text
        for candidate in candidates
    )
    if behaviors:
        return "Observable result matches the source-backed behavior: " + "; ".join(value[:300] for value in behaviors)
    return "Observable result is unclear; defer or record a coverage gap before canonical TC creation."


def _first_text(values: list[str | None]) -> str:
    for value in values:
        if value:
            return str(value)
    return "new source-backed requirement"


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
