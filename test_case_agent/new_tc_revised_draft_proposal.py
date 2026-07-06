from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.agent_decision_resolver import load_agent_decision_resolution
from test_case_agent.agent_decision_validation import load_agent_decision_validation_report

CREATED_BY_TOOL = "test_case_agent.new_tc_revised_draft_proposal"
REVISED_PROPOSAL_PREFIX = "new-tc-revised-draft-proposal"
DEFAULT_PACKAGE_ID = "WPKG-000001"

ProposalStatus = Literal["pass", "pass-with-warnings", "blocked"]
CandidateStatus = Literal["draft-ready", "draft-with-warnings", "blocked"]

GENERIC_PLACEHOLDER_PATTERNS = (
    "tbd",
    "уточнить",
    "проверить корректность",
    "open the screen or section identified by the source anchors",
    "set up the source-backed condition",
)


@dataclass(frozen=True)
class RevisedDraftCandidate:
    draft_id: str
    proposed_tc_id: str
    source_agent_decision_row_id: str
    source_validation_result_id: str
    source_action: str
    source_draft_ids: list[str]
    candidate_status: CandidateStatus
    title: str
    preconditions: list[str]
    steps: list[str]
    expected_results: list[str]
    traceability_refs: list[str]
    source_req_ids: list[str]
    req_uids: list[str]
    source_evidence_refs: list[str]
    source_fact_summary: dict[str, Any]
    agent_decision_rationale: str
    validation_rationale: str
    duplicate_risk_notes: list[str]
    existing_tc_coverage_notes: list[str]
    draft_quality_flags: list[str]
    manual_review_notes: list[str]
    creates_or_edits_canonical_tc: bool = False

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RevisedDraftCandidate":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            source_agent_decision_row_id=str(data["source_agent_decision_row_id"]),
            source_validation_result_id=str(data["source_validation_result_id"]),
            source_action=str(data["source_action"]),
            source_draft_ids=list(data.get("source_draft_ids") or []),
            candidate_status=data["candidate_status"],
            title=str(data["title"]),
            preconditions=list(data.get("preconditions") or []),
            steps=list(data.get("steps") or []),
            expected_results=list(data.get("expected_results") or []),
            traceability_refs=list(data.get("traceability_refs") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            req_uids=list(data.get("req_uids") or []),
            source_evidence_refs=list(data.get("source_evidence_refs") or []),
            source_fact_summary=dict(data.get("source_fact_summary") or {}),
            agent_decision_rationale=str(data.get("agent_decision_rationale") or ""),
            validation_rationale=str(data.get("validation_rationale") or ""),
            duplicate_risk_notes=list(data.get("duplicate_risk_notes") or []),
            existing_tc_coverage_notes=list(data.get("existing_tc_coverage_notes") or []),
            draft_quality_flags=list(data.get("draft_quality_flags") or []),
            manual_review_notes=list(data.get("manual_review_notes") or []),
            creates_or_edits_canonical_tc=bool(data.get("creates_or_edits_canonical_tc")),
        )


@dataclass(frozen=True)
class NewTcRevisedDraftProposal:
    package_id: str
    proposal_status: ProposalStatus
    source_validation_path: str
    source_agent_decision_resolution_path: str
    source_artifacts: dict[str, str | None]
    revised_draft_candidates: list[RevisedDraftCandidate]
    excluded_decisions: list[dict[str, Any]]
    deferred_decisions: list[dict[str, Any]]
    human_review_required_decisions: list[dict[str, Any]]
    traceability_map: dict[str, Any]
    source_evidence_map: dict[str, Any]
    stage_9e_scope: dict[str, Any]
    safety_summary: dict[str, Any]
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
            "proposal_status": self.proposal_status,
            "source_validation_path": self.source_validation_path,
            "source_agent_decision_resolution_path": self.source_agent_decision_resolution_path,
            "source_artifacts": self.source_artifacts,
            "revised_draft_candidates": [item.to_dict() for item in self.revised_draft_candidates],
            "excluded_decisions": self.excluded_decisions,
            "deferred_decisions": self.deferred_decisions,
            "human_review_required_decisions": self.human_review_required_decisions,
            "traceability_map": self.traceability_map,
            "source_evidence_map": self.source_evidence_map,
            "stage_9e_scope": self.stage_9e_scope,
            "safety_summary": self.safety_summary,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcRevisedDraftProposal":
        return cls(
            package_id=str(data["package_id"]),
            proposal_status=data["proposal_status"],
            source_validation_path=str(data.get("source_validation_path") or ""),
            source_agent_decision_resolution_path=str(data.get("source_agent_decision_resolution_path") or ""),
            source_artifacts=dict(data.get("source_artifacts") or {}),
            revised_draft_candidates=[
                RevisedDraftCandidate.from_dict(item)
                for item in data.get("revised_draft_candidates", [])
            ],
            excluded_decisions=list(data.get("excluded_decisions") or []),
            deferred_decisions=list(data.get("deferred_decisions") or []),
            human_review_required_decisions=list(data.get("human_review_required_decisions") or []),
            traceability_map=dict(data.get("traceability_map") or {}),
            source_evidence_map=dict(data.get("source_evidence_map") or {}),
            stage_9e_scope=dict(data.get("stage_9e_scope") or {}),
            safety_summary=dict(data.get("safety_summary") or {}),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_new_tc_revised_draft_proposal(
    *,
    package_id: str,
    validation_path: Path,
    resolution_path: Path,
    matrix_path: Path | None = None,
    draft_proposal_path: Path,
    draft_review_path: Path | None = None,
    draft_revision_plan_path: Path | None = None,
    decision_pack_path: Path | None = None,
    context_bundle_path: Path,
    residual_analysis_path: Path | None = None,
    test_cases_dir: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> NewTcRevisedDraftProposal:
    input_paths = _input_paths(
        validation_path=validation_path,
        resolution_path=resolution_path,
        matrix_path=matrix_path,
        draft_proposal_path=draft_proposal_path,
        draft_review_path=draft_review_path,
        draft_revision_plan_path=draft_revision_plan_path,
        decision_pack_path=decision_pack_path,
        context_bundle_path=context_bundle_path,
        residual_analysis_path=residual_analysis_path,
        test_cases_dir=test_cases_dir,
    )
    now = _utc_now()
    warnings: list[str] = []
    blocking_reasons = _missing_paths(
        validation_path=validation_path,
        resolution_path=resolution_path,
        draft_proposal_path=draft_proposal_path,
        context_bundle_path=context_bundle_path,
    )
    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"Stage 9E is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if test_cases_dir is not None and (not Path(test_cases_dir).exists() or not Path(test_cases_dir).is_dir()):
        blocking_reasons.append(f"test_cases_dir is missing: {test_cases_dir}")

    if blocking_reasons:
        return _blocked_proposal(package_id, input_paths, warnings, blocking_reasons, now, created_by_tool)

    validation = load_agent_decision_validation_report(validation_path)
    resolution = load_agent_decision_resolution(resolution_path)
    source_draft_proposal = _read_json(draft_proposal_path)
    draft_review = _read_json(draft_review_path)
    draft_revision_plan = _read_json(draft_revision_plan_path)
    decision_pack = _read_json(decision_pack_path)
    context_bundle = _read_json(context_bundle_path)

    if validation.package_id != package_id:
        blocking_reasons.append(f"validation package_id mismatch: {validation.package_id} != {package_id}")
    if resolution.package_id != package_id:
        blocking_reasons.append(f"resolution package_id mismatch: {resolution.package_id} != {package_id}")
    if not validation.stage_9e_gate_hardened.get("stage_9e_allowed"):
        blocking_reasons.append("hardened Stage 9D.9 gate does not allow Stage 9E")
    if validation.canonical_write_allowed or resolution.canonical_write_allowed:
        blocking_reasons.append("canonical writes must be disabled before Stage 9E")
    if blocking_reasons:
        return _blocked_proposal(package_id, input_paths, warnings, blocking_reasons, now, created_by_tool)

    valid_results = {
        item.row_id: item
        for item in validation.decision_validation_results
        if item.stage_9e_eligible and item.validation_result in {"valid", "valid-with-warnings"}
    }
    allowed_rows = set(validation.validated_stage_9e_scope.get("row_ids") or [])
    decisions_by_row = {decision.row_id: decision for decision in resolution.agent_decisions}
    source_drafts_by_id = {
        str(item.get("draft_id")): item
        for item in source_draft_proposal.get("draft_test_cases") or []
        if item.get("draft_id")
    }
    context_by_req = {
        str(item.get("req_uid")): item
        for item in context_bundle.get("candidate_requirements") or []
        if item.get("req_uid")
    }
    review_by_draft = _index_by_draft(draft_review.get("draft_reviews"))
    revision_by_draft = _index_by_draft(draft_revision_plan.get("revision_items"))
    decision_pack_by_draft = _index_by_draft(decision_pack.get("draft_decisions"))

    candidates: list[RevisedDraftCandidate] = []
    excluded: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    human_review: list[dict[str, Any]] = []

    for decision in resolution.agent_decisions:
        if decision.row_id in allowed_rows and decision.row_id in valid_results:
            candidates.extend(
                _candidates_for_decision(
                    decision=decision,
                    validation_result=valid_results[decision.row_id],
                    source_drafts_by_id=source_drafts_by_id,
                    context_by_req=context_by_req,
                    review_by_draft=review_by_draft,
                    revision_by_draft=revision_by_draft,
                    decision_pack_by_draft=decision_pack_by_draft,
                )
            )
        elif decision.decision_status in {"deferred"}:
            deferred.append(_decision_ref(decision, "deferred"))
        elif decision.decision_status in {"needs_human_review", "unsafe"} or decision.requires_human_review:
            human_review.append(_decision_ref(decision, "requires human review or unsafe"))
        else:
            excluded.append(_decision_ref(decision, "not in hardened validated Stage 9E scope"))

    candidate_ids = [candidate.draft_id for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        warnings.append("revised draft candidate ids are not unique")
    if not candidates:
        blocking_reasons.append("no revised draft candidates were created from hardened validated scope")
    if any(candidate.candidate_status == "blocked" for candidate in candidates):
        warnings.append("one or more revised draft candidates are blocked because source-backed facts are incomplete")

    status: ProposalStatus = "pass"
    if warnings or any(candidate.candidate_status != "draft-ready" for candidate in candidates):
        status = "pass-with-warnings"
    if blocking_reasons:
        status = "blocked"

    return NewTcRevisedDraftProposal(
        package_id=package_id,
        proposal_status=status,
        source_validation_path=str(validation_path),
        source_agent_decision_resolution_path=str(resolution_path),
        source_artifacts={
            "validation_status": validation.validation_status,
            "resolution_status": resolution.resolution_status,
            "source_draft_proposal_status": str(source_draft_proposal.get("proposal_status")),
            "source_draft_review_status": str(draft_review.get("review_status")) if draft_review else None,
        },
        revised_draft_candidates=candidates,
        excluded_decisions=excluded,
        deferred_decisions=deferred,
        human_review_required_decisions=human_review,
        traceability_map=_traceability_map(candidates),
        source_evidence_map=_source_evidence_map(candidates),
        stage_9e_scope={
            "row_ids": sorted(allowed_rows),
            "actions": list(validation.validated_stage_9e_scope.get("actions") or []),
            "candidate_count": len(candidates),
        },
        safety_summary={
            "canonical_write_allowed": False,
            "creates_or_edits_canonical_tc": False,
            "reviewer_answers_json_created": False,
            "uses_only_hardened_validated_scope": True,
            "unvalidated_rows_included": [],
            "source_draft_ids_exist": all(
                source_id in source_drafts_by_id
                for candidate in candidates
                for source_id in candidate.source_draft_ids
            ),
        },
        canonical_write_allowed=False,
        manual_review_required=True,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=now,
        created_by_tool=created_by_tool,
    )


def write_new_tc_revised_draft_proposal(
    proposal: NewTcRevisedDraftProposal,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REVISED_PROPOSAL_PREFIX}-{proposal.package_id}.json"
    markdown_path = out_dir / f"{REVISED_PROPOSAL_PREFIX}-{proposal.package_id}.md"
    json_path.write_text(json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_new_tc_revised_draft_proposal_markdown(proposal), encoding="utf-8-sig", newline="\n")
    return json_path, markdown_path


def load_new_tc_revised_draft_proposal(path: Path) -> NewTcRevisedDraftProposal:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("New TC revised draft proposal root must be a JSON object.")
    return NewTcRevisedDraftProposal.from_dict(payload)


def render_new_tc_revised_draft_proposal_markdown(proposal: NewTcRevisedDraftProposal) -> str:
    lines = [
        f"# New TC Revised Draft Proposal {proposal.package_id}",
        "",
        "## Summary",
        "",
        f"- Proposal status: `{proposal.proposal_status}`",
        f"- Hardened scope rows: `{', '.join(proposal.stage_9e_scope.get('row_ids', [])) or '-'}`",
        f"- Revised draft candidates: `{len(proposal.revised_draft_candidates)}`",
        f"- Blocked candidates: `{sum(1 for item in proposal.revised_draft_candidates if item.candidate_status == 'blocked')}`",
        f"- Canonical write allowed: `{proposal.canonical_write_allowed}`",
        f"- Manual review required: `{proposal.manual_review_required}`",
        "",
        "## Revised Draft Candidates",
        "",
    ]
    for candidate in proposal.revised_draft_candidates:
        lines.extend(
            [
                f"### {candidate.draft_id} / {candidate.proposed_tc_id}",
                "",
                f"- Source row: `{candidate.source_agent_decision_row_id}`",
                f"- Source action: `{candidate.source_action}`",
                f"- Status: `{candidate.candidate_status}`",
                f"- Source drafts: `{', '.join(candidate.source_draft_ids)}`",
                f"- Req UIDs: `{', '.join(candidate.req_uids)}`",
                f"- Title: {candidate.title}",
                "",
                "**Steps**",
                "",
                *[f"{index}. {step}" for index, step in enumerate(candidate.steps, start=1)],
                "",
                "**Expected Results**",
                "",
                *[f"- {result}" for result in candidate.expected_results],
                "",
            ]
        )
    lines.extend(
        [
            "## Safety Summary",
            "",
            *[f"- {key}: `{value}`" for key, value in proposal.safety_summary.items()],
            "",
            "## Warnings / Blocking Reasons",
            "",
        ]
    )
    if proposal.warnings:
        lines.extend(f"- warning: {warning}" for warning in proposal.warnings)
    if proposal.blocking_reasons:
        lines.extend(f"- blocker: {reason}" for reason in proposal.blocking_reasons)
    if not proposal.warnings and not proposal.blocking_reasons:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _candidates_for_decision(
    *,
    decision: Any,
    validation_result: Any,
    source_drafts_by_id: dict[str, dict[str, Any]],
    context_by_req: dict[str, dict[str, Any]],
    review_by_draft: dict[str, dict[str, Any]],
    revision_by_draft: dict[str, dict[str, Any]],
    decision_pack_by_draft: dict[str, dict[str, Any]],
) -> list[RevisedDraftCandidate]:
    candidates = []
    for source_draft_id in decision.affected_drafts:
        source_draft = source_drafts_by_id.get(source_draft_id)
        if not source_draft:
            candidates.append(_blocked_candidate(decision, validation_result, source_draft_id, "source draft id is absent from source proposal"))
            continue
        req_uids = _req_uids_for_source_draft(source_draft, decision)
        profiles = _profiles_for_req_uids(source_draft, req_uids)
        for req_uid in req_uids:
            profile = profiles.get(req_uid) or {}
            context = context_by_req.get(req_uid) or {}
            candidates.append(
                _candidate_from_source(
                    decision=decision,
                    validation_result=validation_result,
                    source_draft=source_draft,
                    source_draft_id=source_draft_id,
                    req_uid=req_uid,
                    profile=profile,
                    context=context,
                    review=review_by_draft.get(source_draft_id, {}),
                    revision=revision_by_draft.get(source_draft_id, {}),
                    decision_pack_item=decision_pack_by_draft.get(source_draft_id, {}),
                )
            )
    return candidates


def _candidate_from_source(
    *,
    decision: Any,
    validation_result: Any,
    source_draft: dict[str, Any],
    source_draft_id: str,
    req_uid: str,
    profile: dict[str, Any],
    context: dict[str, Any],
    review: dict[str, Any],
    revision: dict[str, Any],
    decision_pack_item: dict[str, Any],
) -> RevisedDraftCandidate:
    source_fact = _source_fact(profile, context)
    object_text = source_fact["object"]
    action = source_fact["action"]
    oracle = source_fact["oracle"]
    condition = source_fact["condition"]
    warnings = []
    if not object_text:
        warnings.append("missing source-backed object")
    if not action:
        warnings.append("missing source-backed action")
    if not oracle:
        warnings.append("missing source-backed oracle")
    if _has_generic_placeholder([object_text, action, oracle, condition]):
        warnings.append("generic placeholder detected")

    status: CandidateStatus = "draft-ready" if not warnings else "blocked"
    preconditions = []
    if condition:
        preconditions.append(f"Источник ФТ задает условие: {condition}")
    steps = [f"Выполнить действие, указанное в ФТ для `{req_uid}`: {action}"] if action else []
    expected_results = [f"Система должна выполнить наблюдаемое поведение из ФТ для `{req_uid}`: {oracle}"] if oracle else []
    if not steps or not expected_results:
        status = "blocked"

    title_object = object_text or source_draft.get("title") or req_uid
    title = "Проверка требования: " + _short(title_object, 120)
    revised_id = f"REV-{validation_result.row_id}-{source_draft_id}-{req_uid[-6:]}"
    proposed_tc_id = f"{source_draft.get('proposed_tc_id') or 'DRAFT-TC'}-{validation_result.row_id}"
    source_req_ids = _unique([profile.get("source_req_id"), context.get("source_req_id"), *source_draft.get("source_req_ids", [])])
    source_evidence_refs = _source_evidence_refs(req_uid, profile, context)
    draft_flags = _unique([*source_draft.get("draft_quality_flags", []), *warnings])
    manual_notes = _unique(
        [
            *source_draft.get("manual_questions", []),
            *profile.get("manual_questions", []),
            *review.get("required_fixes", []),
            *revision.get("blocking_questions", []),
        ]
    )
    return RevisedDraftCandidate(
        draft_id=revised_id,
        proposed_tc_id=proposed_tc_id,
        source_agent_decision_row_id=decision.row_id,
        source_validation_result_id=validation_result.row_id,
        source_action=decision.selected_allowed_next_action,
        source_draft_ids=[source_draft_id],
        candidate_status=status,
        title=title,
        preconditions=preconditions,
        steps=steps,
        expected_results=expected_results,
        traceability_refs=_unique([req_uid, *source_req_ids]),
        source_req_ids=source_req_ids,
        req_uids=[req_uid],
        source_evidence_refs=source_evidence_refs,
        source_fact_summary=source_fact,
        agent_decision_rationale=decision.rationale,
        validation_rationale=validation_result.reasoning,
        duplicate_risk_notes=_unique([*source_draft.get("duplicate_risk_notes", []), str(decision.duplicate_risk_assessment.coverage_overlap_summary or "")]),
        existing_tc_coverage_notes=[
            str(item.get("test_case_id") or item.get("file_path") or item)
            for item in decision.existing_tc_coverage_evidence
        ],
        draft_quality_flags=draft_flags,
        manual_review_notes=manual_notes,
        creates_or_edits_canonical_tc=False,
    )


def _blocked_candidate(decision: Any, validation_result: Any, source_draft_id: str, reason: str) -> RevisedDraftCandidate:
    return RevisedDraftCandidate(
        draft_id=f"REV-{validation_result.row_id}-{source_draft_id}-BLOCKED",
        proposed_tc_id=f"DRAFT-TC-{validation_result.row_id}-BLOCKED",
        source_agent_decision_row_id=decision.row_id,
        source_validation_result_id=validation_result.row_id,
        source_action=decision.selected_allowed_next_action,
        source_draft_ids=[source_draft_id],
        candidate_status="blocked",
        title="Blocked revised draft candidate",
        preconditions=[],
        steps=[],
        expected_results=[],
        traceability_refs=[],
        source_req_ids=[],
        req_uids=[],
        source_evidence_refs=[],
        source_fact_summary={},
        agent_decision_rationale=decision.rationale,
        validation_rationale=validation_result.reasoning,
        duplicate_risk_notes=[],
        existing_tc_coverage_notes=[],
        draft_quality_flags=[reason],
        manual_review_notes=[reason],
        creates_or_edits_canonical_tc=False,
    )


def _source_fact(profile: dict[str, Any], context: dict[str, Any]) -> dict[str, str]:
    enriched = context.get("enriched_source_facts") or {}
    table_contexts = profile.get("table_source_contexts") or context.get("table_source_contexts") or []
    first_table = table_contexts[0] if table_contexts else {}
    return {
        "object": _first_text(profile, context, enriched, first_table, keys=("object", "field_name", "source_text")),
        "condition": _first_text(profile, context, enriched, first_table, keys=("condition",)),
        "action": _first_text(profile, context, enriched, first_table, keys=("user_action", "action", "action_candidates")),
        "oracle": _first_text(
            profile,
            context,
            enriched,
            first_table,
            keys=("observable_expected_behavior", "expected_behavior", "expected_behavior_candidates", "source_text"),
        ),
    }


def _first_text(*sources: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        for source in sources:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, list) and value and str(value[0]).strip():
                return str(value[0]).strip()
    return ""


def _req_uids_for_source_draft(source_draft: dict[str, Any], decision: Any) -> list[str]:
    reqs = _unique(
        [
            *source_draft.get("source_requirement_uids", []),
            *source_draft.get("candidate_req_uids", []),
            *source_draft.get("traceability_refs", []),
        ]
    )
    decision_reqs = set(decision.affected_requirements)
    reqs = [req for req in reqs if req in decision_reqs and req.startswith("REQ-")]
    if not reqs:
        reqs = [
            str(profile.get("req_uid"))
            for profile in source_draft.get("source_grounding_profiles") or []
            if str(profile.get("req_uid") or "") in decision_reqs
        ]
    return _unique(reqs)


def _profiles_for_req_uids(source_draft: dict[str, Any], req_uids: list[str]) -> dict[str, dict[str, Any]]:
    profiles = {}
    for profile in source_draft.get("source_grounding_profiles") or []:
        req_uid = str(profile.get("req_uid") or "")
        if req_uid in req_uids:
            profiles[req_uid] = profile
    return profiles


def _source_evidence_refs(req_uid: str, profile: dict[str, Any], context: dict[str, Any]) -> list[str]:
    refs = [req_uid]
    for anchor in [*profile.get("source_anchors", []), *context.get("source_anchors", [])]:
        refs.extend([anchor.get("node_id"), anchor.get("xpath")])
    for anchor_context in [*profile.get("source_anchor_contexts", []), *context.get("source_anchor_contexts", [])]:
        refs.extend([anchor_context.get("anchor_id"), anchor_context.get("source_location")])
    return _unique(refs)


def _traceability_map(candidates: list[RevisedDraftCandidate]) -> dict[str, Any]:
    return {
        candidate.draft_id: {
            "source_agent_decision_row_id": candidate.source_agent_decision_row_id,
            "source_validation_result_id": candidate.source_validation_result_id,
            "source_draft_ids": candidate.source_draft_ids,
            "req_uids": candidate.req_uids,
            "source_evidence_refs": candidate.source_evidence_refs,
        }
        for candidate in candidates
    }


def _source_evidence_map(candidates: list[RevisedDraftCandidate]) -> dict[str, Any]:
    by_req: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        for req_uid in candidate.req_uids:
            by_req.setdefault(req_uid, []).append(
                {
                    "draft_id": candidate.draft_id,
                    "source_fact_summary": candidate.source_fact_summary,
                    "source_evidence_refs": candidate.source_evidence_refs,
                }
            )
    return by_req


def _decision_ref(decision: Any, reason: str) -> dict[str, Any]:
    return {
        "row_id": decision.row_id,
        "cluster_id": decision.cluster_id,
        "action": decision.selected_allowed_next_action,
        "decision_status": decision.decision_status,
        "reason": reason,
    }


def _index_by_draft(items: Any) -> dict[str, dict[str, Any]]:
    return {str(item.get("draft_id")): item for item in items or [] if item.get("draft_id")}


def _input_paths(**paths: Path | None) -> dict[str, str | None]:
    return {name: str(path) if path is not None else None for name, path in paths.items()}


def _missing_paths(**paths: Path | None) -> list[str]:
    reasons = []
    for name, path in paths.items():
        if path is None:
            reasons.append(f"{name} is required")
        elif not Path(path).exists():
            reasons.append(f"{name} is missing: {path}")
    return reasons


def _blocked_proposal(
    package_id: str,
    input_paths: dict[str, str | None],
    warnings: list[str],
    blocking_reasons: list[str],
    created_at_utc: str,
    created_by_tool: str,
) -> NewTcRevisedDraftProposal:
    return NewTcRevisedDraftProposal(
        package_id=package_id,
        proposal_status="blocked",
        source_validation_path=input_paths.get("validation_path") or "",
        source_agent_decision_resolution_path=input_paths.get("resolution_path") or "",
        source_artifacts={},
        revised_draft_candidates=[],
        excluded_decisions=[],
        deferred_decisions=[],
        human_review_required_decisions=[],
        traceability_map={},
        source_evidence_map={},
        stage_9e_scope={"row_ids": [], "actions": [], "candidate_count": 0},
        safety_summary={"canonical_write_allowed": False},
        canonical_write_allowed=False,
        manual_review_required=True,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=created_at_utc,
        created_by_tool=created_by_tool,
    )


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _has_generic_placeholder(values: list[str]) -> bool:
    text = "\n".join(str(value or "").casefold() for value in values)
    return any(pattern in text for pattern in GENERIC_PLACEHOLDER_PATTERNS)


def _short(value: str, limit: int) -> str:
    value = " ".join(str(value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
