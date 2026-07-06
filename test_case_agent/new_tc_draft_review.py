from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.create_new_tc_context_bundle import (
    CreateNewTcContextBundle,
    load_create_new_tc_context_bundle,
)
from test_case_agent.new_tc_draft_proposals import (
    DraftTestCaseCandidate,
    NewTcDraftProposal,
    load_new_tc_draft_proposal,
)

CREATED_BY_TOOL = "test_case_agent.new_tc_draft_review"
REVIEW_PREFIX = "new-tc-draft-review"
DEFAULT_PACKAGE_ID = "WPKG-000001"

ReviewStatus = Literal["approved", "approved-with-warnings", "rejected", "blocked"]
DraftReviewStatus = Literal["approved_for_create_proposal", "needs_revision", "defer", "reject"]
QualityScore = Literal["low", "medium", "high"]
CheckStatus = Literal["pass", "warning", "failed", "blocked"]
AreaStatus = Literal["pass", "warning", "failed"]

REQ_RE = re.compile(r"\bREQ-[A-Z0-9-]+\b")
FINAL_TC_RE = re.compile(r"^TC-[A-Za-z0-9][A-Za-z0-9_-]*$")
GENERIC_STEP_PATTERNS = [
    "open the screen or section identified by the source anchors",
    "set up the source-backed condition",
    "perform the user action needed to observe",
]
COMPLETED_PACKAGE_IDS = {"WPKG-000002", "WPKG-000003"}
OUT_OF_SCOPE_PACKAGE_IDS = {"WPKG-000004", "WPKG-000005"}


@dataclass(frozen=True)
class NewTcDraftReviewCheck:
    check_id: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcDraftReviewCheck":
        return cls(
            check_id=str(data["check_id"]),
            status=data["status"],
            message=str(data["message"]),
            details=dict(data.get("details") or {}),
        )


@dataclass(frozen=True)
class DraftTestCaseReview:
    draft_id: str
    proposed_tc_id: str
    review_status: DraftReviewStatus
    quality_score: QualityScore
    duplicate_risk_level: str
    traceability_status: AreaStatus
    source_grounding_status: AreaStatus
    test_design_status: AreaStatus
    format_status: AreaStatus
    issues: list[str]
    required_fixes: list[str]
    review_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "proposed_tc_id": self.proposed_tc_id,
            "review_status": self.review_status,
            "quality_score": self.quality_score,
            "duplicate_risk_level": self.duplicate_risk_level,
            "traceability_status": self.traceability_status,
            "source_grounding_status": self.source_grounding_status,
            "test_design_status": self.test_design_status,
            "format_status": self.format_status,
            "issues": self.issues,
            "required_fixes": self.required_fixes,
            "review_notes": self.review_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DraftTestCaseReview":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            review_status=data["review_status"],
            quality_score=data["quality_score"],
            duplicate_risk_level=str(data["duplicate_risk_level"]),
            traceability_status=data["traceability_status"],
            source_grounding_status=data["source_grounding_status"],
            test_design_status=data["test_design_status"],
            format_status=data["format_status"],
            issues=list(data.get("issues") or []),
            required_fixes=list(data.get("required_fixes") or []),
            review_notes=list(data.get("review_notes") or []),
        )


@dataclass
class NewTcDraftReviewReport:
    package_id: str
    review_status: ReviewStatus
    safe_for_controlled_create_apply: bool
    canonical_write_allowed: bool
    manual_review_required: bool
    drafts_total: int
    approved_drafts_count: int
    drafts_requiring_revision_count: int
    deferred_drafts_count: int
    rejected_drafts_count: int
    duplicate_risk_summary: dict[str, Any]
    checks: list[NewTcDraftReviewCheck]
    draft_reviews: list[DraftTestCaseReview]
    failed_checks: list[str]
    warnings: list[str]
    blocking_reasons: list[str]
    reviewer_recommendation: str
    input_paths: dict[str, str | None]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "review_status": self.review_status,
            "safe_for_controlled_create_apply": self.safe_for_controlled_create_apply,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "drafts_total": self.drafts_total,
            "approved_drafts_count": self.approved_drafts_count,
            "drafts_requiring_revision_count": self.drafts_requiring_revision_count,
            "deferred_drafts_count": self.deferred_drafts_count,
            "rejected_drafts_count": self.rejected_drafts_count,
            "duplicate_risk_summary": self.duplicate_risk_summary,
            "checks": [check.to_dict() for check in self.checks],
            "draft_reviews": [review.to_dict() for review in self.draft_reviews],
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "reviewer_recommendation": self.reviewer_recommendation,
            "input_paths": self.input_paths,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcDraftReviewReport":
        return cls(
            package_id=str(data["package_id"]),
            review_status=data["review_status"],
            safe_for_controlled_create_apply=bool(data["safe_for_controlled_create_apply"]),
            canonical_write_allowed=bool(data["canonical_write_allowed"]),
            manual_review_required=bool(data["manual_review_required"]),
            drafts_total=int(data.get("drafts_total") or 0),
            approved_drafts_count=int(data.get("approved_drafts_count") or 0),
            drafts_requiring_revision_count=int(data.get("drafts_requiring_revision_count") or 0),
            deferred_drafts_count=int(data.get("deferred_drafts_count") or 0),
            rejected_drafts_count=int(data.get("rejected_drafts_count") or 0),
            duplicate_risk_summary=dict(data.get("duplicate_risk_summary") or {}),
            checks=[NewTcDraftReviewCheck.from_dict(item) for item in data.get("checks", [])],
            draft_reviews=[DraftTestCaseReview.from_dict(item) for item in data.get("draft_reviews", [])],
            failed_checks=list(data.get("failed_checks") or []),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            reviewer_recommendation=str(data.get("reviewer_recommendation") or ""),
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_new_tc_draft_review(
    *,
    package_id: str,
    draft_proposal_path: Path,
    context_bundle_path: Path,
    test_cases_dir: Path,
    draft_proposal_markdown_path: Path | None = None,
    context_bundle_markdown_path: Path | None = None,
    manual_update_packages_path: Path | None = None,
    writer_package_tasks_path: Path | None = None,
    update_plan_path: Path | None = None,
    impact_report_path: Path | None = None,
    requirements_diff_path: Path | None = None,
    old_registry_path: Path | None = None,
    new_registry_path: Path | None = None,
    workspace_root: Path | None = None,
    record_git_state: bool = True,
    created_by_tool: str = CREATED_BY_TOOL,
) -> NewTcDraftReviewReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    input_paths = _input_paths(
        draft_proposal_path=draft_proposal_path,
        draft_proposal_markdown_path=draft_proposal_markdown_path,
        context_bundle_path=context_bundle_path,
        context_bundle_markdown_path=context_bundle_markdown_path,
        manual_update_packages_path=manual_update_packages_path,
        writer_package_tasks_path=writer_package_tasks_path,
        update_plan_path=update_plan_path,
        impact_report_path=impact_report_path,
        requirements_diff_path=requirements_diff_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
        test_cases_dir=test_cases_dir,
    )
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    checks: list[NewTcDraftReviewCheck] = []
    proposal: NewTcDraftProposal | None = None
    bundle: CreateNewTcContextBundle | None = None

    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"this review is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    for label, path in {
        "draft proposal": draft_proposal_path,
        "context bundle": context_bundle_path,
        "test-cases dir": test_cases_dir,
    }.items():
        if label == "test-cases dir":
            if not Path(path).exists() or not Path(path).is_dir():
                blocking_reasons.append(f"{label} is missing: {path}")
        elif not Path(path).exists():
            blocking_reasons.append(f"{label} is missing: {path}")
    for label, path in {
        "draft proposal markdown": draft_proposal_markdown_path,
        "context bundle markdown": context_bundle_markdown_path,
    }.items():
        if path is not None and not Path(path).exists():
            warnings.append(f"{label} is missing: {path}")

    if Path(draft_proposal_path).exists():
        try:
            proposal = load_new_tc_draft_proposal(Path(draft_proposal_path))
        except Exception as exc:  # noqa: BLE001 - review reports parse failures.
            blocking_reasons.append(f"draft proposal cannot be parsed: {draft_proposal_path}: {exc}")
    if Path(context_bundle_path).exists():
        try:
            bundle = load_create_new_tc_context_bundle(Path(context_bundle_path))
        except Exception as exc:  # noqa: BLE001 - review reports parse failures.
            blocking_reasons.append(f"context bundle cannot be parsed: {context_bundle_path}: {exc}")

    git_state = _git_state(workspace_root, Path(test_cases_dir)) if record_git_state else {}
    if proposal is None or bundle is None or blocking_reasons:
        return _report(
            package_id=package_id,
            proposal=proposal,
            draft_reviews=[],
            checks=checks,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            input_paths=input_paths,
            duplicate_risk_summary={},
            created_by_tool=created_by_tool,
        )

    warnings.extend(proposal.warnings)
    checks.extend(_artifact_checks(package_id, proposal, bundle))
    checks.extend(_scope_checks(proposal))
    checks.extend(_safety_checks(proposal, git_state))
    draft_reviews = [
        _review_draft(draft, bundle)
        for draft in proposal.draft_test_cases
    ]
    checks.extend(_coverage_checks(proposal, bundle, draft_reviews))
    duplicate_risk_summary = _duplicate_risk_summary(proposal, draft_reviews)
    checks.extend(_duplicate_risk_checks(proposal, draft_reviews))

    if any(review.review_status == "needs_revision" for review in draft_reviews):
        warnings.append("one or more draft TC candidates require revision before controlled create proposal.")
    if duplicate_risk_summary.get("medium", 0) or duplicate_risk_summary.get("high", 0):
        warnings.append("duplicate risk decisions require reviewer confirmation before canonical TC creation.")

    return _report(
        package_id=package_id,
        proposal=proposal,
        draft_reviews=draft_reviews,
        checks=checks,
        warnings=warnings,
        blocking_reasons=[],
        input_paths=input_paths,
        duplicate_risk_summary=duplicate_risk_summary,
        created_by_tool=created_by_tool,
    )


def write_new_tc_draft_review(
    report: NewTcDraftReviewReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REVIEW_PREFIX}-{report.package_id}.json"
    markdown_path = out_dir / f"{REVIEW_PREFIX}-{report.package_id}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_new_tc_draft_review_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_new_tc_draft_review(path: Path) -> NewTcDraftReviewReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("New TC draft review root must be a JSON object.")
    return NewTcDraftReviewReport.from_dict(payload)


def render_new_tc_draft_review_markdown(report: NewTcDraftReviewReport) -> str:
    lines = [
        f"# New TC Draft Review {report.package_id}",
        "",
        "## Summary",
        "",
        f"- Review status: `{report.review_status}`",
        f"- Safe for controlled create apply: `{str(report.safe_for_controlled_create_apply).lower()}`",
        f"- Canonical write allowed: `{str(report.canonical_write_allowed).lower()}`",
        f"- Manual review required: `{str(report.manual_review_required).lower()}`",
        f"- Drafts total: `{report.drafts_total}`",
        f"- Approved drafts: `{report.approved_drafts_count}`",
        f"- Drafts requiring revision: `{report.drafts_requiring_revision_count}`",
        f"- Deferred drafts: `{report.deferred_drafts_count}`",
        f"- Rejected drafts: `{report.rejected_drafts_count}`",
        f"- Failed checks: `{', '.join(report.failed_checks) or 'none'}`",
        f"- Blocking reasons: `{len(report.blocking_reasons)}`",
        f"- Reviewer recommendation: {report.reviewer_recommendation}",
        "",
        "## Duplicate Risk Summary",
        "",
    ]
    for key, value in sorted(report.duplicate_risk_summary.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Draft Reviews", ""])
    if report.draft_reviews:
        for review in report.draft_reviews:
            lines.append(
                f"- `{review.draft_id}` `{review.proposed_tc_id}`: `{review.review_status}`, "
                f"quality `{review.quality_score}`, duplicate risk `{review.duplicate_risk_level}`"
            )
            if review.issues:
                lines.append(f"  - issues: {'; '.join(review.issues)}")
            if review.required_fixes:
                lines.append(f"  - required fixes: {'; '.join(review.required_fixes)}")
    else:
        lines.append("- none")
    lines.extend(["", "## Checks", ""])
    for check in report.checks:
        lines.append(f"- `{check.status}` `{check.check_id}`: {check.message}")
    lines.extend(["", "## Warnings", ""])
    _append_list(lines, report.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, report.blocking_reasons)
    lines.extend(["", "## Safety Statement", ""])
    lines.append("- Review-only artifact.")
    lines.append("- No canonical TC was created.")
    lines.append("- No canonical TC was edited.")
    lines.append("- `--apply` was not used.")
    return "\n".join(lines).rstrip() + "\n"


def _artifact_checks(
    package_id: str,
    proposal: NewTcDraftProposal,
    bundle: CreateNewTcContextBundle,
) -> list[NewTcDraftReviewCheck]:
    return [
        _check("proposal_package_matches", proposal.package_id == package_id, f"proposal package_id is {proposal.package_id}."),
        _check("bundle_package_matches", bundle.package_id == package_id, f"bundle package_id is {bundle.package_id}."),
        _check("proposal_package_type_create_new", proposal.package_type == "create_new_candidate", f"proposal package_type is {proposal.package_type}."),
        _check("bundle_package_type_create_new", bundle.package_type == "create_new_candidate", f"bundle package_type is {bundle.package_type}."),
        _check("proposal_not_blocked", proposal.proposal_status != "blocked", f"proposal_status is {proposal.proposal_status}.", blocked=True),
        _check("proposal_blocking_reasons_empty", not proposal.blocking_reasons, f"proposal blockers count is {len(proposal.blocking_reasons)}.", {"blocking_reasons": proposal.blocking_reasons}, blocked=True),
        _check("bundle_blocking_reasons_empty", not bundle.blocking_reasons, f"bundle blockers count is {len(bundle.blocking_reasons)}.", {"blocking_reasons": bundle.blocking_reasons}, blocked=True),
        _check("manual_review_required_true", proposal.manual_review_required is True, f"manual_review_required is {proposal.manual_review_required}."),
        _check("canonical_write_allowed_false", proposal.canonical_write_allowed is False, f"canonical_write_allowed is {proposal.canonical_write_allowed}."),
    ]


def _scope_checks(proposal: NewTcDraftProposal) -> list[NewTcDraftReviewCheck]:
    refs_text = json.dumps(proposal.to_dict(), ensure_ascii=False)
    wrong_packages = sorted((COMPLETED_PACKAGE_IDS | OUT_OF_SCOPE_PACKAGE_IDS) & set(re.findall(r"WPKG-\d{6}", refs_text)))
    non_draft_ids = [
        draft.proposed_tc_id
        for draft in proposal.draft_test_cases
        if not draft.proposed_tc_id.startswith(f"DRAFT-TC-{proposal.package_id}-")
    ]
    final_ids = [draft.proposed_tc_id for draft in proposal.draft_test_cases if FINAL_TC_RE.fullmatch(draft.proposed_tc_id)]
    canonical_targets = [
        draft.target_file_path
        for draft in proposal.draft_test_cases
        if draft.requires_new_file is False and "test-cases" in draft.target_file_path.replace("\\", "/")
    ]
    return [
        _check("only_wpkg_000001_scope", proposal.package_id == DEFAULT_PACKAGE_ID, f"proposal scope is {proposal.package_id}."),
        _check("no_completed_or_large_package_refs", not wrong_packages, "proposal does not reference completed or out-of-scope package ids.", {"wrong_package_ids": wrong_packages}),
        _check("proposed_tc_ids_are_draft_only", not non_draft_ids and not final_ids, "all proposed TC IDs are draft-only.", {"non_draft_ids": non_draft_ids, "final_ids": final_ids}),
        _check("no_claim_to_modify_existing_canonical_tc", not canonical_targets, "drafts do not claim to modify existing canonical TC files.", {"canonical_targets": canonical_targets}, warning=True),
    ]


def _safety_checks(proposal: NewTcDraftProposal, git_state: dict[str, Any]) -> list[NewTcDraftReviewCheck]:
    return [
        _check("canonical_write_allowed_is_false", proposal.canonical_write_allowed is False, "proposal forbids canonical writes."),
        _check("manual_review_required_is_true", proposal.manual_review_required is True, "proposal requires manual review."),
        _check("test_cases_git_status_clean", git_state.get("status_short_empty", True), "test-cases git status is clean.", git_state, warning=True),
        _check("test_cases_git_diff_empty", git_state.get("diff_empty", True), "test-cases git diff is empty.", git_state, warning=True),
    ]


def _review_draft(draft: DraftTestCaseCandidate, bundle: CreateNewTcContextBundle) -> DraftTestCaseReview:
    candidate_by_req = {
        candidate.req_uid: candidate
        for candidate in bundle.candidate_requirements
        if candidate.req_uid
    }
    issues: list[str] = []
    required_fixes: list[str] = []
    notes: list[str] = []

    traceability_status: AreaStatus = "pass"
    if not draft.source_requirement_uids or not any(REQ_RE.fullmatch(ref) for ref in draft.source_requirement_uids):
        traceability_status = "failed"
        issues.append("draft is missing generated REQ-* traceability.")
        required_fixes.append("Add source requirement REQ-* refs from context bundle.")
    unknown_req_uids = [req_uid for req_uid in draft.source_requirement_uids if req_uid not in candidate_by_req]
    if unknown_req_uids:
        traceability_status = "failed"
        issues.append(f"draft references unknown req_uid values: {', '.join(unknown_req_uids)}.")
        required_fixes.append("Remove unknown refs or rebuild proposal from the context bundle.")
    if not draft.plan_item_ids or not draft.impact_ids or not draft.change_ids:
        traceability_status = "failed"
        issues.append("draft is missing plan_item_id, impact_id or change_id.")
        required_fixes.append("Preserve plan/impact/change ids from the context bundle.")

    source_grounding_status: AreaStatus = "pass"
    candidate_text = " ".join(
        " ".join(str(value or "") for value in [
            candidate_by_req[req_uid].source_text,
            candidate_by_req[req_uid].normalized_text,
            candidate_by_req[req_uid].expected_behavior,
            candidate_by_req[req_uid].condition,
            candidate_by_req[req_uid].object,
        ])
        for req_uid in draft.source_requirement_uids
        if req_uid in candidate_by_req
    ).casefold()
    draft_text = " ".join([
        draft.title,
        draft.coverage_intent,
        " ".join(draft.steps),
        " ".join(draft.expected_results),
    ]).casefold()
    if any(_is_generic_placeholder(step) for step in draft.steps):
        source_grounding_status = "warning"
        issues.append("draft steps are mostly generic placeholders.")
        required_fixes.append("Replace generic navigation/action placeholders with source-backed concrete steps.")
    if getattr(draft, "contains_generic_placeholders", False):
        source_grounding_status = "warning"
        issues.append("draft contains generic placeholders.")
        required_fixes.append("Remove generic placeholders; defer or ask manual questions if source facts are incomplete.")
    if not getattr(draft, "is_executable_draft", True):
        source_grounding_status = "warning"
        issues.append("draft is not executable from current source grounding.")
        required_fixes.append("Resolve source-grounding manual questions before treating draft as executable.")
    for profile in getattr(draft, "source_grounding_profiles", []) or []:
        if not profile.has_user_action:
            source_grounding_status = "warning"
            issues.append(f"missing source-backed user action for {profile.req_uid}.")
            required_fixes.append(f"Add source-backed action or keep {profile.req_uid} deferred/manual-only.")
        if not profile.has_observable_expected_behavior:
            source_grounding_status = "warning"
            issues.append(f"missing observable expected behavior for {profile.req_uid}.")
            required_fixes.append(f"Add observable source-backed expected result or keep {profile.req_uid} deferred/manual-only.")
        if not profile.has_concrete_object:
            source_grounding_status = "warning"
            issues.append(f"missing concrete object/screen/field for {profile.req_uid}.")
            required_fixes.append(f"Add concrete source-backed object/screen/field or keep {profile.req_uid} deferred/manual-only.")
    if not _has_meaningful_overlap(candidate_text, draft_text):
        source_grounding_status = "warning"
        issues.append("draft text has weak overlap with candidate requirement source context.")
        required_fixes.append("Ground title, action and oracle in source_text/expected_behavior/condition.")
    if any("aggregate" in warning.casefold() for warning in draft.warnings):
        source_grounding_status = "warning"
        notes.append("aggregate source context must be manually verified.")

    test_design_status: AreaStatus = "pass"
    if draft.duplicate_risk_level == "high":
        test_design_status = "failed"
        issues.append("high duplicate risk should be deferred before drafting.")
        required_fixes.append("Defer or justify unique behavior before creating a draft.")
    elif draft.duplicate_risk_level == "medium":
        test_design_status = "warning"
        notes.append("medium duplicate risk requires differentiation from similar TC.")
    if len(draft.source_requirement_uids) > 1 and not draft.coverage_intent:
        test_design_status = "warning"
        issues.append("multi-requirement draft lacks explicit grouping rationale.")

    format_status: AreaStatus = "pass"
    missing_format = []
    for field_name in [
        "draft_id",
        "proposed_tc_id",
        "target_file_path",
        "title",
        "traceability_line",
        "preconditions",
        "test_data",
        "steps",
        "expected_results",
        "duplicate_risk_notes",
    ]:
        value = getattr(draft, field_name)
        if not value:
            missing_format.append(field_name)
    if missing_format:
        format_status = "failed"
        issues.append(f"draft is missing required fields: {', '.join(missing_format)}.")
        required_fixes.append("Populate all required draft review fields.")
    if not draft.proposed_tc_id.startswith(f"DRAFT-TC-{DEFAULT_PACKAGE_ID}-"):
        format_status = "failed"
        issues.append("proposed_tc_id is not draft-only.")
        required_fixes.append("Use DRAFT-TC-WPKG-000001-* ids only.")

    if "failed" in {traceability_status, source_grounding_status, test_design_status, format_status}:
        review_status: DraftReviewStatus = "reject"
    elif draft.duplicate_risk_level == "high":
        review_status = "defer"
    elif issues or source_grounding_status == "warning" or test_design_status == "warning":
        review_status = "needs_revision"
    else:
        review_status = "approved_for_create_proposal"
    quality = _quality_score(traceability_status, source_grounding_status, test_design_status, format_status, issues)
    return DraftTestCaseReview(
        draft_id=draft.draft_id,
        proposed_tc_id=draft.proposed_tc_id,
        review_status=review_status,
        quality_score=quality,
        duplicate_risk_level=draft.duplicate_risk_level,
        traceability_status=traceability_status,
        source_grounding_status=source_grounding_status,
        test_design_status=test_design_status,
        format_status=format_status,
        issues=_unique(issues),
        required_fixes=_unique(required_fixes),
        review_notes=_unique(notes),
    )


def _coverage_checks(
    proposal: NewTcDraftProposal,
    bundle: CreateNewTcContextBundle,
    draft_reviews: list[DraftTestCaseReview],
) -> list[NewTcDraftReviewCheck]:
    bundle_req_uids = {
        candidate.req_uid
        for candidate in bundle.candidate_requirements
        if candidate.req_uid
    }
    drafted = {
        req_uid
        for draft in proposal.draft_test_cases
        for req_uid in draft.source_requirement_uids
    }
    deferred = {
        req_uid
        for group in proposal.deferred_groups
        for req_uid in group.candidate_req_uids
    }
    disappeared = sorted(bundle_req_uids - drafted - deferred)
    group_draft_explanation = (
        proposal.coverage_summary.get("candidate_groups_total") != len(proposal.draft_test_cases)
        and proposal.coverage_summary.get("draft_test_cases_total") == len(proposal.draft_test_cases)
    )
    return [
        _check("all_candidate_requirements_accounted_for", not disappeared, "all candidate requirements are drafted or deferred.", {"missing_req_uids": disappeared}),
        _check("drafts_map_to_candidate_requirements", all(review.traceability_status != "failed" for review in draft_reviews), "each draft maps to context bundle candidate requirements."),
        _check("group_draft_count_mismatch_explained", group_draft_explanation or proposal.coverage_summary.get("candidate_groups_total") == len(proposal.draft_test_cases), "candidate group count vs draft count is explained by coverage summary.", {"coverage_summary": proposal.coverage_summary}, warning=True),
    ]


def _duplicate_risk_checks(
    proposal: NewTcDraftProposal,
    draft_reviews: list[DraftTestCaseReview],
) -> list[NewTcDraftReviewCheck]:
    maybe_extend = [
        decision.to_dict()
        for decision in proposal.duplicate_risk_decisions
        if decision.decision == "maybe_extend_existing_tc"
    ]
    high_approved = [
        review.draft_id
        for review in draft_reviews
        if review.duplicate_risk_level == "high" and review.review_status == "approved_for_create_proposal"
    ]
    probable_duplicates = [
        review.draft_id
        for review in draft_reviews
        if review.duplicate_risk_level in {"medium", "high"}
        and review.review_status == "approved_for_create_proposal"
    ]
    return [
        _check("medium_duplicate_risk_visible", True, "duplicate risk notes are visible in draft reviews."),
        _check("high_duplicate_risk_not_approved", not high_approved, "high duplicate risk drafts are not approved.", {"draft_ids": high_approved}),
        _check("maybe_extend_existing_tc_not_approved", not maybe_extend, "maybe_extend_existing_tc decisions are not approved for create.", {"decisions": maybe_extend}, warning=bool(maybe_extend)),
        _check("probable_duplicates_not_approved", not probable_duplicates, "probable duplicates are not approved for create.", {"draft_ids": probable_duplicates}, warning=bool(probable_duplicates)),
    ]


def _duplicate_risk_summary(
    proposal: NewTcDraftProposal,
    draft_reviews: list[DraftTestCaseReview],
) -> dict[str, Any]:
    risk_counts = Counter(decision.risk for decision in proposal.duplicate_risk_decisions)
    decision_counts = Counter(decision.decision for decision in proposal.duplicate_risk_decisions)
    draft_risk_counts = Counter(review.duplicate_risk_level for review in draft_reviews)
    return {
        "low": risk_counts.get("low", 0),
        "medium": risk_counts.get("medium", 0),
        "high": risk_counts.get("high", 0),
        "decision_counts": dict(sorted(decision_counts.items())),
        "draft_risk_counts": dict(sorted(draft_risk_counts.items())),
    }


def _report(
    *,
    package_id: str,
    proposal: NewTcDraftProposal | None,
    draft_reviews: list[DraftTestCaseReview],
    checks: list[NewTcDraftReviewCheck],
    warnings: list[str],
    blocking_reasons: list[str],
    input_paths: dict[str, str | None],
    duplicate_risk_summary: dict[str, Any],
    created_by_tool: str,
) -> NewTcDraftReviewReport:
    failed_checks = [check.check_id for check in checks if check.status == "failed"]
    blocked_checks = [check.check_id for check in checks if check.status == "blocked"]
    blocking_reasons = _unique([*blocking_reasons, *blocked_checks])
    warnings = _unique([
        *warnings,
        *(check.check_id for check in checks if check.status == "warning"),
    ])
    safety_failed = any(
        check_id in failed_checks
        for check_id in {
            "canonical_write_allowed_false",
            "canonical_write_allowed_is_false",
            "proposed_tc_ids_are_draft_only",
            "no_completed_or_large_package_refs",
        }
    )
    if blocking_reasons:
        review_status: ReviewStatus = "blocked"
    elif safety_failed:
        review_status = "rejected"
    elif failed_checks:
        review_status = "approved-with-warnings"
    elif warnings or any(review.review_status != "approved_for_create_proposal" for review in draft_reviews):
        review_status = "approved-with-warnings"
    else:
        review_status = "approved"

    approved = sum(1 for review in draft_reviews if review.review_status == "approved_for_create_proposal")
    needs_revision = sum(1 for review in draft_reviews if review.review_status == "needs_revision")
    deferred = sum(1 for review in draft_reviews if review.review_status == "defer")
    if proposal is not None:
        deferred += len(proposal.deferred_groups)
    rejected = sum(1 for review in draft_reviews if review.review_status == "reject")
    safe_for_create = bool(
        proposal
        and review_status in {"approved", "approved-with-warnings"}
        and draft_reviews
        and approved == len(draft_reviews)
        and not failed_checks
        and not blocking_reasons
    )
    return NewTcDraftReviewReport(
        package_id=package_id,
        review_status=review_status,
        safe_for_controlled_create_apply=safe_for_create,
        canonical_write_allowed=False,
        manual_review_required=True,
        drafts_total=len(draft_reviews),
        approved_drafts_count=approved,
        drafts_requiring_revision_count=needs_revision,
        deferred_drafts_count=deferred,
        rejected_drafts_count=rejected,
        duplicate_risk_summary=duplicate_risk_summary,
        checks=checks,
        draft_reviews=draft_reviews,
        failed_checks=failed_checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        reviewer_recommendation=_recommendation(review_status, safe_for_create, needs_revision, deferred, rejected),
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _recommendation(
    review_status: ReviewStatus,
    safe_for_create: bool,
    needs_revision: int,
    deferred: int,
    rejected: int,
) -> str:
    if review_status == "blocked":
        return "Review is blocked; fix missing or inconsistent artifacts before any draft decision."
    if review_status == "rejected":
        return "Do not proceed; safety violations must be fixed before any create proposal."
    if safe_for_create:
        return "Drafts are review-approved for a later controlled create proposal; canonical apply is still not authorized here."
    return (
        "Proposal is safe as draft-only, but not ready for controlled create apply; "
        f"revise drafts requiring revision={needs_revision}, deferred={deferred}, rejected={rejected}."
    )


def _quality_score(
    traceability: AreaStatus,
    source_grounding: AreaStatus,
    test_design: AreaStatus,
    format_status: AreaStatus,
    issues: list[str],
) -> QualityScore:
    statuses = {traceability, source_grounding, test_design, format_status}
    if "failed" in statuses or len(issues) >= 3:
        return "low"
    if "warning" in statuses or issues:
        return "medium"
    return "high"


def _is_generic_placeholder(step: str) -> bool:
    lowered = step.casefold()
    return any(pattern in lowered for pattern in GENERIC_STEP_PATTERNS) or any(
        pattern in lowered
        for pattern in [
            "behavior is observed",
            "expected result requires manual source-grounding",
            "resolve manual source-grounding questions before drafting executable steps",
        ]
    )


def _has_meaningful_overlap(source: str, draft: str) -> bool:
    source_tokens = _tokens(source)
    draft_tokens = _tokens(draft)
    if not source_tokens:
        return False
    return len(source_tokens & draft_tokens) >= min(3, len(source_tokens))


def _tokens(value: str) -> set[str]:
    stop = {"the", "and", "or", "for", "with", "source", "draft", "candidate", "behavior"}
    return {token for token in re.findall(r"[A-Za-zА-Яа-яЁё0-9]{4,}", value.casefold()) if token not in stop}


def _git_state(workspace_root: Path, test_cases_dir: Path) -> dict[str, Any]:
    try:
        git_path = str(test_cases_dir.resolve().relative_to(workspace_root.resolve())).replace("\\", "/")
    except ValueError:
        git_path = str(test_cases_dir)
    status = _run_git(workspace_root, ["status", "--short", "--", git_path])
    diff = _run_git(workspace_root, ["diff", "--stat", "--", git_path])
    return {
        "target": git_path,
        "status_short": status["stdout"],
        "status_returncode": status["returncode"],
        "status_short_empty": status["stdout"] == "",
        "diff_stat": diff["stdout"],
        "diff_returncode": diff["returncode"],
        "diff_empty": diff["stdout"] == "",
    }


def _run_git(cwd: Path, args: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    except OSError as exc:
        return {"stdout": "", "stderr": str(exc), "returncode": 1}
    return {
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def _check(
    check_id: str,
    ok: bool,
    message: str,
    details: dict[str, Any] | None = None,
    *,
    warning: bool = False,
    blocked: bool = False,
) -> NewTcDraftReviewCheck:
    if ok:
        status: CheckStatus = "pass"
    elif blocked:
        status = "blocked"
    elif warning:
        status = "warning"
    else:
        status = "failed"
    return NewTcDraftReviewCheck(check_id=check_id, status=status, message=message, details=details or {})


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
