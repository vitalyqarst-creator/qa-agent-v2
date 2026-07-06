from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.new_tc_revised_draft_proposal import (
    NewTcRevisedDraftProposal,
    RevisedDraftCandidate,
    load_new_tc_revised_draft_proposal,
)

CREATED_BY_TOOL = "test_case_agent.new_tc_revised_draft_review"
REVISED_REVIEW_PREFIX = "new-tc-revised-draft-review"
DEFAULT_PACKAGE_ID = "WPKG-000001"

ReviewStatus = Literal["approved", "approved-with-warnings", "needs-revision", "rejected", "blocked"]
DraftReviewResult = Literal["approved", "approved-with-warnings", "needs-revision", "rejected"]
CheckStatus = Literal["pass", "warning", "failed", "blocked"]
AreaResult = Literal["pass", "warning", "failed"]

REQ_RE = re.compile(r"\bREQ-[A-Z0-9-]+\b")
GENERIC_PLACEHOLDER_PATTERNS = (
    "tbd",
    "уточнить",
    "проверить корректность",
    "open the screen or section identified by the source anchors",
    "set up the source-backed condition",
)


@dataclass(frozen=True)
class RevisedDraftReview:
    draft_id: str
    proposed_tc_id: str
    review_result: DraftReviewResult
    checks: list[dict[str, Any]]
    source_grounding_result: AreaResult
    format_result: AreaResult
    traceability_result: AreaResult
    duplicate_risk_result: AreaResult
    safety_result: AreaResult
    issues: list[str]
    required_fixes: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RevisedDraftReview":
        return cls(
            draft_id=str(data["draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            review_result=data["review_result"],
            checks=list(data.get("checks") or []),
            source_grounding_result=data["source_grounding_result"],
            format_result=data["format_result"],
            traceability_result=data["traceability_result"],
            duplicate_risk_result=data["duplicate_risk_result"],
            safety_result=data["safety_result"],
            issues=list(data.get("issues") or []),
            required_fixes=list(data.get("required_fixes") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class NewTcRevisedDraftReviewReport:
    package_id: str
    review_status: ReviewStatus
    source_revised_proposal_path: str
    draft_reviews: list[RevisedDraftReview]
    traceability_checks: list[dict[str, Any]]
    source_grounding_checks: list[dict[str, Any]]
    duplicate_risk_checks: list[dict[str, Any]]
    format_checks: list[dict[str, Any]]
    safety_checks: list[dict[str, Any]]
    stage_9g_readiness: dict[str, Any]
    canonical_write_allowed: bool
    manual_review_required: bool
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "review_status": self.review_status,
            "source_revised_proposal_path": self.source_revised_proposal_path,
            "draft_reviews": [item.to_dict() for item in self.draft_reviews],
            "traceability_checks": self.traceability_checks,
            "source_grounding_checks": self.source_grounding_checks,
            "duplicate_risk_checks": self.duplicate_risk_checks,
            "format_checks": self.format_checks,
            "safety_checks": self.safety_checks,
            "stage_9g_readiness": self.stage_9g_readiness,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcRevisedDraftReviewReport":
        return cls(
            package_id=str(data["package_id"]),
            review_status=data["review_status"],
            source_revised_proposal_path=str(data.get("source_revised_proposal_path") or ""),
            draft_reviews=[RevisedDraftReview.from_dict(item) for item in data.get("draft_reviews", [])],
            traceability_checks=list(data.get("traceability_checks") or []),
            source_grounding_checks=list(data.get("source_grounding_checks") or []),
            duplicate_risk_checks=list(data.get("duplicate_risk_checks") or []),
            format_checks=list(data.get("format_checks") or []),
            safety_checks=list(data.get("safety_checks") or []),
            stage_9g_readiness=dict(data.get("stage_9g_readiness") or {}),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_new_tc_revised_draft_review(
    *,
    package_id: str,
    revised_proposal_path: Path,
    validation_path: Path,
    source_draft_proposal_path: Path,
    test_cases_dir: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> NewTcRevisedDraftReviewReport:
    now = _utc_now()
    blocking_reasons = _missing_paths(
        revised_proposal_path=revised_proposal_path,
        validation_path=validation_path,
        source_draft_proposal_path=source_draft_proposal_path,
    )
    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"Stage 9F is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if test_cases_dir is not None and (not Path(test_cases_dir).exists() or not Path(test_cases_dir).is_dir()):
        blocking_reasons.append(f"test_cases_dir is missing: {test_cases_dir}")
    if blocking_reasons:
        return _blocked_report(package_id, revised_proposal_path, blocking_reasons, now, created_by_tool)

    proposal = load_new_tc_revised_draft_proposal(revised_proposal_path)
    validation = _read_json(validation_path)
    source_draft_proposal = _read_json(source_draft_proposal_path)
    source_draft_ids = {
        str(item.get("draft_id"))
        for item in source_draft_proposal.get("draft_test_cases") or []
        if item.get("draft_id")
    }
    validated_rows = set((validation.get("validated_stage_9e_scope") or {}).get("row_ids") or [])
    warnings = list(proposal.warnings)
    blocking_reasons = []
    if proposal.package_id != package_id:
        blocking_reasons.append(f"proposal package_id mismatch: {proposal.package_id} != {package_id}")
    if proposal.proposal_status == "blocked":
        blocking_reasons.extend(proposal.blocking_reasons or ["Stage 9E proposal is blocked"])
    if proposal.canonical_write_allowed:
        blocking_reasons.append("Stage 9E proposal unexpectedly allows canonical writes")

    draft_reviews = [
        _review_candidate(candidate, validated_rows, source_draft_ids)
        for candidate in proposal.revised_draft_candidates
    ]
    all_checks = [check for review in draft_reviews for check in review.checks]
    traceability_checks = [check for check in all_checks if check["area"] == "traceability"]
    source_grounding_checks = [check for check in all_checks if check["area"] == "source_grounding"]
    duplicate_risk_checks = [check for check in all_checks if check["area"] == "duplicate_risk"]
    format_checks = [check for check in all_checks if check["area"] == "format"]
    safety_checks = [check for check in all_checks if check["area"] == "safety"]

    if any(review.review_result == "rejected" for review in draft_reviews):
        warnings.append("one or more revised draft candidates were rejected")
    if any(review.review_result == "needs-revision" for review in draft_reviews):
        warnings.append("one or more revised draft candidates need revision")
    if not draft_reviews and not blocking_reasons:
        blocking_reasons.append("Stage 9E proposal has no revised draft candidates")

    counts = Counter(review.review_result for review in draft_reviews)
    status = _review_status(blocking_reasons, counts, warnings)
    return NewTcRevisedDraftReviewReport(
        package_id=package_id,
        review_status=status,
        source_revised_proposal_path=str(revised_proposal_path),
        draft_reviews=draft_reviews,
        traceability_checks=traceability_checks,
        source_grounding_checks=source_grounding_checks,
        duplicate_risk_checks=duplicate_risk_checks,
        format_checks=format_checks,
        safety_checks=safety_checks,
        stage_9g_readiness={
            "recommended": status in {"approved", "approved-with-warnings"},
            "recommendation": (
                "Stage 9G - Controlled Create Apply Dry-Run Design"
                if status in {"approved", "approved-with-warnings"}
                else "Resolve revised draft review findings before Stage 9G"
            ),
            "authorizes_real_apply": False,
            "canonical_tc_created": False,
            "canonical_tc_modified": False,
        },
        canonical_write_allowed=False,
        manual_review_required=True,
        warnings=_unique(warnings),
        blocking_reasons=_unique(blocking_reasons),
        created_at_utc=now,
        created_by_tool=created_by_tool,
    )


def write_new_tc_revised_draft_review(
    report: NewTcRevisedDraftReviewReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REVISED_REVIEW_PREFIX}-{report.package_id}.json"
    markdown_path = out_dir / f"{REVISED_REVIEW_PREFIX}-{report.package_id}.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_new_tc_revised_draft_review_markdown(report), encoding="utf-8-sig", newline="\n")
    return json_path, markdown_path


def load_new_tc_revised_draft_review(path: Path) -> NewTcRevisedDraftReviewReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("New TC revised draft review root must be a JSON object.")
    return NewTcRevisedDraftReviewReport.from_dict(payload)


def render_new_tc_revised_draft_review_markdown(report: NewTcRevisedDraftReviewReport) -> str:
    counts = Counter(review.review_result for review in report.draft_reviews)
    lines = [
        f"# New TC Revised Draft Review {report.package_id}",
        "",
        "## Summary",
        "",
        f"- Review status: `{report.review_status}`",
        f"- Drafts total: `{len(report.draft_reviews)}`",
        f"- Approved: `{counts.get('approved', 0)}`",
        f"- Approved with warnings: `{counts.get('approved-with-warnings', 0)}`",
        f"- Needs revision: `{counts.get('needs-revision', 0)}`",
        f"- Rejected: `{counts.get('rejected', 0)}`",
        f"- Stage 9G readiness recommended: `{report.stage_9g_readiness.get('recommended')}`",
        f"- Canonical write allowed: `{report.canonical_write_allowed}`",
        "",
        "## Draft Reviews",
        "",
    ]
    for review in report.draft_reviews:
        lines.extend(
            [
                f"- `{review.draft_id}` `{review.proposed_tc_id}`: `{review.review_result}`",
                f"  - issues: `{'; '.join(review.issues) or '-'}`",
                f"  - warnings: `{'; '.join(review.warnings) or '-'}`",
            ]
        )
    lines.extend(["", "## Warnings / Blocking Reasons", ""])
    if report.warnings:
        lines.extend(f"- warning: {warning}" for warning in report.warnings)
    if report.blocking_reasons:
        lines.extend(f"- blocker: {reason}" for reason in report.blocking_reasons)
    if not report.warnings and not report.blocking_reasons:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _review_candidate(
    candidate: RevisedDraftCandidate,
    validated_rows: set[str],
    source_draft_ids: set[str],
) -> RevisedDraftReview:
    checks = [
        _check("traceability", "source_agent_decision_row", bool(candidate.source_agent_decision_row_id), "source agent decision row id exists"),
        _check("traceability", "validation_traceability", bool(candidate.source_validation_result_id), "validation traceability exists"),
        _check("traceability", "row_in_validated_scope", candidate.source_agent_decision_row_id in validated_rows, "candidate row is in hardened validated scope"),
        _check("traceability", "source_draft_ids_exist", bool(candidate.source_draft_ids) and all(item in source_draft_ids for item in candidate.source_draft_ids), "source draft ids exist in original proposal"),
        _check("traceability", "req_uids_present", bool(candidate.req_uids) and all(REQ_RE.match(item) for item in candidate.req_uids), "req_uids exist"),
        _check("traceability", "source_evidence_refs_present", bool(candidate.source_evidence_refs), "source evidence refs exist"),
        _check("source_grounding", "steps_source_backed", bool(candidate.steps), "steps are present and source-backed"),
        _check("source_grounding", "expected_results_source_backed", bool(candidate.expected_results), "expected results are present and source-backed"),
        _check("source_grounding", "no_missing_action_or_oracle", candidate.candidate_status != "blocked", "candidate has no missing source-backed action/oracle"),
        _check("format", "no_generic_placeholders", not _has_generic_placeholder([*candidate.steps, *candidate.expected_results, candidate.title]), "no generic placeholders"),
        _check("format", "proposed_tc_id_present", bool(candidate.proposed_tc_id), "proposed TC id is present"),
        _check("duplicate_risk", "duplicate_risk_notes_present", bool(candidate.duplicate_risk_notes), "duplicate risk notes are present"),
        _check("safety", "no_direct_canonical_write", not candidate.creates_or_edits_canonical_tc, "candidate does not create/edit canonical TC"),
        _check("safety", "no_existing_tc_business_source", not _uses_existing_tc_as_business_source(candidate), "existing TC is not used as business source"),
    ]
    issues = [check["message"] for check in checks if check["status"] in {"failed", "blocked"}]
    warnings = []
    if candidate.manual_review_notes:
        warnings.append("manual review notes are present")
    if candidate.candidate_status == "draft-with-warnings":
        warnings.append("candidate is draft-with-warnings")
    if issues:
        result: DraftReviewResult = "rejected" if any(check["area"] == "safety" for check in checks if check["status"] == "failed") else "needs-revision"
    elif warnings:
        result = "approved-with-warnings"
    else:
        result = "approved"
    return RevisedDraftReview(
        draft_id=candidate.draft_id,
        proposed_tc_id=candidate.proposed_tc_id,
        review_result=result,
        checks=checks,
        source_grounding_result=_area_result(checks, "source_grounding"),
        format_result=_area_result(checks, "format"),
        traceability_result=_area_result(checks, "traceability"),
        duplicate_risk_result=_area_result(checks, "duplicate_risk"),
        safety_result=_area_result(checks, "safety"),
        issues=issues,
        required_fixes=issues,
        warnings=warnings,
    )


def _review_status(blockers: list[str], counts: Counter, warnings: list[str]) -> ReviewStatus:
    if blockers:
        return "blocked"
    if counts.get("rejected", 0):
        return "rejected"
    if counts.get("needs-revision", 0):
        return "needs-revision"
    if warnings or counts.get("approved-with-warnings", 0):
        return "approved-with-warnings"
    return "approved"


def _area_result(checks: list[dict[str, Any]], area: str) -> AreaResult:
    selected = [check for check in checks if check["area"] == area]
    if any(check["status"] == "failed" for check in selected):
        return "failed"
    if any(check["status"] == "warning" for check in selected):
        return "warning"
    return "pass"


def _check(area: str, check_id: str, passed: bool, message: str) -> dict[str, Any]:
    return {
        "area": area,
        "check_id": check_id,
        "status": "pass" if passed else "failed",
        "message": message if passed else f"failed: {message}",
    }


def _uses_existing_tc_as_business_source(candidate: RevisedDraftCandidate) -> bool:
    text = "\n".join([candidate.agent_decision_rationale, *candidate.existing_tc_coverage_notes]).casefold()
    return "existing tc" in text and "business source" in text


def _has_generic_placeholder(values: list[str]) -> bool:
    text = "\n".join(str(value or "").casefold() for value in values)
    return any(pattern in text for pattern in GENERIC_PLACEHOLDER_PATTERNS)


def _blocked_report(
    package_id: str,
    revised_proposal_path: Path,
    blocking_reasons: list[str],
    created_at_utc: str,
    created_by_tool: str,
) -> NewTcRevisedDraftReviewReport:
    return NewTcRevisedDraftReviewReport(
        package_id=package_id,
        review_status="blocked",
        source_revised_proposal_path=str(revised_proposal_path),
        draft_reviews=[],
        traceability_checks=[],
        source_grounding_checks=[],
        duplicate_risk_checks=[],
        format_checks=[],
        safety_checks=[],
        stage_9g_readiness={
            "recommended": False,
            "recommendation": "Review is blocked.",
            "authorizes_real_apply": False,
            "canonical_tc_created": False,
            "canonical_tc_modified": False,
        },
        canonical_write_allowed=False,
        manual_review_required=True,
        warnings=[],
        blocking_reasons=blocking_reasons,
        created_at_utc=created_at_utc,
        created_by_tool=created_by_tool,
    )


def _missing_paths(**paths: Path | None) -> list[str]:
    reasons = []
    for name, path in paths.items():
        if path is None:
            reasons.append(f"{name} is required")
        elif not Path(path).exists():
            reasons.append(f"{name} is missing: {path}")
    return reasons


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
