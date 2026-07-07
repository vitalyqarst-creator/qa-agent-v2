from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.new_tc_revised_draft_proposal import (
    RevisedDraftCandidate,
    load_new_tc_revised_draft_proposal,
)
from test_case_agent.new_tc_revised_draft_review import (
    RevisedDraftReview,
    load_new_tc_revised_draft_review,
)

CREATED_BY_TOOL = "test_case_agent.new_tc_create_apply_dry_run"
CREATE_APPLY_DRY_RUN_PREFIX = "new-tc-create-apply-dry-run"
DEFAULT_PACKAGE_ID = "WPKG-000001"

DryRunStatus = Literal["pass", "pass-with-warnings", "blocked"]
PlannedOperation = Literal["create_new_file", "append_to_existing_file", "blocked"]
DryRunDecision = Literal["dry_run_allowed", "dry_run_allowed_with_warnings", "blocked"]

TC_HEADING_RE = re.compile(r"^(#{2,6})\s+(TC-[A-Za-z0-9][A-Za-z0-9_-]*)\b[:\-\s]*(.*)$")
AGGREGATE_FILE_MARKERS = (
    "assembled_from",
    "test_case_count",
    "aggregate",
    "порядок сборки",
    "source files assembled",
)


@dataclass(frozen=True)
class CreateApplyDryRunItem:
    dry_run_item_id: str
    source_revised_draft_id: str
    proposed_tc_id: str
    target_file_path: str
    target_section: str
    planned_operation: PlannedOperation
    dry_run_decision: DryRunDecision
    generated_markdown_preview: str
    traceability_refs: list[str]
    req_uids: list[str]
    source_req_ids: list[str]
    source_evidence_refs: list[str]
    source_agent_decision_row_id: str
    source_validation_result_id: str
    review_result: str
    review_warnings: list[str]
    collision_risks: list[str]
    format_warnings: list[str]
    safety_warnings: list[str]
    creates_or_edits_canonical_tc: bool = False

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreateApplyDryRunItem":
        return cls(
            dry_run_item_id=str(data["dry_run_item_id"]),
            source_revised_draft_id=str(data["source_revised_draft_id"]),
            proposed_tc_id=str(data["proposed_tc_id"]),
            target_file_path=str(data["target_file_path"]),
            target_section=str(data.get("target_section") or ""),
            planned_operation=data["planned_operation"],
            dry_run_decision=data["dry_run_decision"],
            generated_markdown_preview=str(data.get("generated_markdown_preview") or ""),
            traceability_refs=list(data.get("traceability_refs") or []),
            req_uids=list(data.get("req_uids") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            source_evidence_refs=list(data.get("source_evidence_refs") or []),
            source_agent_decision_row_id=str(data.get("source_agent_decision_row_id") or ""),
            source_validation_result_id=str(data.get("source_validation_result_id") or ""),
            review_result=str(data.get("review_result") or ""),
            review_warnings=list(data.get("review_warnings") or []),
            collision_risks=list(data.get("collision_risks") or []),
            format_warnings=list(data.get("format_warnings") or []),
            safety_warnings=list(data.get("safety_warnings") or []),
            creates_or_edits_canonical_tc=bool(data.get("creates_or_edits_canonical_tc")),
        )


@dataclass(frozen=True)
class NewTcCreateApplyDryRunReport:
    package_id: str
    dry_run_status: DryRunStatus
    source_revised_proposal_path: str
    source_revised_review_path: str
    dry_run_items: list[CreateApplyDryRunItem]
    excluded_candidates: list[dict[str, Any]]
    target_file_plan: dict[str, Any]
    tc_id_plan: dict[str, Any]
    traceability_plan: dict[str, Any]
    collision_checks: list[dict[str, Any]]
    format_checks: list[dict[str, Any]]
    safety_checks: list[dict[str, Any]]
    rollback_plan: dict[str, Any]
    stage_9h_readiness: dict[str, Any]
    canonical_write_allowed: bool
    real_apply_authorized: bool
    input_paths: dict[str, str | None]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "dry_run_status": self.dry_run_status,
            "source_revised_proposal_path": self.source_revised_proposal_path,
            "source_revised_review_path": self.source_revised_review_path,
            "dry_run_items": [item.to_dict() for item in self.dry_run_items],
            "excluded_candidates": self.excluded_candidates,
            "target_file_plan": self.target_file_plan,
            "tc_id_plan": self.tc_id_plan,
            "traceability_plan": self.traceability_plan,
            "collision_checks": self.collision_checks,
            "format_checks": self.format_checks,
            "safety_checks": self.safety_checks,
            "rollback_plan": self.rollback_plan,
            "stage_9h_readiness": self.stage_9h_readiness,
            "canonical_write_allowed": self.canonical_write_allowed,
            "real_apply_authorized": self.real_apply_authorized,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcCreateApplyDryRunReport":
        return cls(
            package_id=str(data["package_id"]),
            dry_run_status=data["dry_run_status"],
            source_revised_proposal_path=str(data.get("source_revised_proposal_path") or ""),
            source_revised_review_path=str(data.get("source_revised_review_path") or ""),
            dry_run_items=[CreateApplyDryRunItem.from_dict(item) for item in data.get("dry_run_items", [])],
            excluded_candidates=list(data.get("excluded_candidates") or []),
            target_file_plan=dict(data.get("target_file_plan") or {}),
            tc_id_plan=dict(data.get("tc_id_plan") or {}),
            traceability_plan=dict(data.get("traceability_plan") or {}),
            collision_checks=list(data.get("collision_checks") or []),
            format_checks=list(data.get("format_checks") or []),
            safety_checks=list(data.get("safety_checks") or []),
            rollback_plan=dict(data.get("rollback_plan") or {}),
            stage_9h_readiness=dict(data.get("stage_9h_readiness") or {}),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            real_apply_authorized=bool(data.get("real_apply_authorized")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_new_tc_create_apply_dry_run(
    *,
    package_id: str,
    revised_proposal_path: Path,
    revised_review_path: Path,
    validation_path: Path | None = None,
    resolution_path: Path | None = None,
    matrix_path: Path | None = None,
    context_bundle_path: Path | None = None,
    test_cases_dir: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> NewTcCreateApplyDryRunReport:
    now = _utc_now()
    test_cases_dir = Path(test_cases_dir)
    input_paths = {
        "revised_proposal_path": str(revised_proposal_path),
        "revised_review_path": str(revised_review_path),
        "validation_path": str(validation_path) if validation_path else None,
        "resolution_path": str(resolution_path) if resolution_path else None,
        "matrix_path": str(matrix_path) if matrix_path else None,
        "context_bundle_path": str(context_bundle_path) if context_bundle_path else None,
        "test_cases_dir": str(test_cases_dir),
    }
    blocking_reasons = _missing_paths(
        revised_proposal_path=revised_proposal_path,
        revised_review_path=revised_review_path,
        test_cases_dir=test_cases_dir,
    )
    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"Stage 9G is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if blocking_reasons:
        return _blocked_report(package_id, revised_proposal_path, revised_review_path, input_paths, blocking_reasons, now, created_by_tool)

    proposal = load_new_tc_revised_draft_proposal(revised_proposal_path)
    review = load_new_tc_revised_draft_review(revised_review_path)
    blocking_reasons = []
    if proposal.package_id != package_id:
        blocking_reasons.append(f"proposal package_id mismatch: {proposal.package_id} != {package_id}")
    if review.package_id != package_id:
        blocking_reasons.append(f"review package_id mismatch: {review.package_id} != {package_id}")
    if review.review_status not in {"approved", "approved-with-warnings"}:
        blocking_reasons.append(f"Stage 9F review is not approved for Stage 9G: {review.review_status}")
    if proposal.canonical_write_allowed or review.canonical_write_allowed:
        blocking_reasons.append("upstream artifacts unexpectedly allow canonical writes")
    if blocking_reasons:
        return _blocked_report(package_id, revised_proposal_path, revised_review_path, input_paths, blocking_reasons, now, created_by_tool)

    existing = _scan_existing_test_cases(test_cases_dir)
    reviews_by_draft = {item.draft_id: item for item in review.draft_reviews}
    candidates_by_id = {item.draft_id: item for item in proposal.revised_draft_candidates}
    duplicate_draft_ids = _duplicates([item.draft_id for item in proposal.revised_draft_candidates])
    duplicate_proposed_tc_ids = _duplicates([item.proposed_tc_id for item in proposal.revised_draft_candidates])

    items: list[CreateApplyDryRunItem] = []
    excluded: list[dict[str, Any]] = []
    for candidate in proposal.revised_draft_candidates:
        item_review = reviews_by_draft.get(candidate.draft_id)
        if item_review is None:
            excluded.append(_excluded(candidate, "candidate has no Stage 9F review"))
            continue
        if item_review.review_result not in {"approved", "approved-with-warnings"}:
            excluded.append(_excluded(candidate, f"review result is {item_review.review_result}"))
            continue
        if _has_failed_safety_check(item_review):
            excluded.append(_excluded(candidate, "Stage 9F safety check failed"))
            continue
        items.append(
            _build_item(
                candidate=candidate,
                review=item_review,
                test_cases_dir=test_cases_dir,
                existing=existing,
                duplicate_draft_ids=duplicate_draft_ids,
                duplicate_proposed_tc_ids=duplicate_proposed_tc_ids,
            )
        )

    collision_checks = _collision_checks(items, existing, duplicate_draft_ids, duplicate_proposed_tc_ids)
    format_checks = _format_checks(items)
    safety_checks = _safety_checks(items, excluded)
    warnings = _unique(
        [
            *(proposal.warnings or []),
            *(review.warnings or []),
            *[warning for item in items for warning in item.review_warnings],
            *[warning for item in items for warning in item.format_warnings],
            *[warning for item in items for warning in item.safety_warnings],
            *[risk for item in items for risk in item.collision_risks],
        ]
    )
    blocked_count = sum(1 for item in items if item.dry_run_decision == "blocked")
    if not items:
        blocking_reasons.append("no approved revised candidates are available for Stage 9G dry-run design")
    if any(check["status"] == "failed" for check in safety_checks):
        blocking_reasons.append("one or more Stage 9G safety checks failed")

    status: DryRunStatus = "pass"
    if warnings or blocked_count or excluded:
        status = "pass-with-warnings"
    if blocking_reasons:
        status = "blocked"

    return NewTcCreateApplyDryRunReport(
        package_id=package_id,
        dry_run_status=status,
        source_revised_proposal_path=str(revised_proposal_path),
        source_revised_review_path=str(revised_review_path),
        dry_run_items=items,
        excluded_candidates=excluded,
        target_file_plan=_target_file_plan(items),
        tc_id_plan=_tc_id_plan(items, existing),
        traceability_plan=_traceability_plan(items),
        collision_checks=collision_checks,
        format_checks=format_checks,
        safety_checks=safety_checks,
        rollback_plan={
            "required_for_stage_9g": False,
            "backups_created": False,
            "rationale": "Stage 9G is preview-only and does not write canonical files.",
            "future_stage_9h_requirement": "A future real apply must create backups before writing.",
        },
        stage_9h_readiness={
            "stage_9h_design_recommended": status in {"pass", "pass-with-warnings"} and blocked_count == 0,
            "real_apply_authorized": False,
            "requires_explicit_user_approval": True,
            "requires_clean_git_status": True,
            "requires_no_blocked_dry_run_items": True,
            "requires_review_of_warnings": True,
            "required_next_action": (
                "Review Stage 9G warnings and request a separate Stage 9H design/dry-run; Stage 9G does not authorize real apply."
                if blocked_count == 0
                else "Resolve blocked dry-run items before designing Stage 9H."
            ),
        },
        canonical_write_allowed=False,
        real_apply_authorized=False,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=_unique(blocking_reasons),
        created_at_utc=now,
        created_by_tool=created_by_tool,
    )


def write_new_tc_create_apply_dry_run(report: NewTcCreateApplyDryRunReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{CREATE_APPLY_DRY_RUN_PREFIX}-{report.package_id}.json"
    md_path = out_dir / f"{CREATE_APPLY_DRY_RUN_PREFIX}-{report.package_id}.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text(render_new_tc_create_apply_dry_run_markdown(report), encoding="utf-8-sig", newline="\n")
    return json_path, md_path


def load_new_tc_create_apply_dry_run(path: Path) -> NewTcCreateApplyDryRunReport:
    return NewTcCreateApplyDryRunReport.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def render_new_tc_create_apply_dry_run_markdown(report: NewTcCreateApplyDryRunReport) -> str:
    counts = Counter(item.dry_run_decision for item in report.dry_run_items)
    lines = [
        f"# New TC Create Apply Dry-Run {report.package_id}",
        "",
        "## Summary",
        "",
        f"- dry_run_status: `{report.dry_run_status}`",
        f"- dry_run_items: `{len(report.dry_run_items)}`",
        f"- dry_run_allowed: `{counts.get('dry_run_allowed', 0)}`",
        f"- dry_run_allowed_with_warnings: `{counts.get('dry_run_allowed_with_warnings', 0)}`",
        f"- blocked: `{counts.get('blocked', 0)}`",
        f"- canonical_write_allowed: `{report.canonical_write_allowed}`",
        f"- real_apply_authorized: `{report.real_apply_authorized}`",
        "",
        "## Dry-Run Item Table",
        "",
        "| Item | Draft | TC ID | Operation | Decision | Target |",
        "|---|---|---|---|---|---|",
    ]
    for item in report.dry_run_items:
        lines.append(
            f"| `{item.dry_run_item_id}` | `{item.source_revised_draft_id}` | `{item.proposed_tc_id}` | "
            f"`{item.planned_operation}` | `{item.dry_run_decision}` | `{item.target_file_path}` |"
        )
    lines.extend(["", "## Target File Plan", "", "```json", json.dumps(report.target_file_plan, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## TC ID Plan", "", "```json", json.dumps(report.tc_id_plan, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## Collision Checks", ""])
    lines.extend(_checks_markdown(report.collision_checks))
    lines.extend(["", "## Format Checks", ""])
    lines.extend(_checks_markdown(report.format_checks))
    lines.extend(["", "## Safety Checks", ""])
    lines.extend(_checks_markdown(report.safety_checks))
    lines.extend(["", "## Rollback Plan", "", "```json", json.dumps(report.rollback_plan, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## Stage 9H Readiness", "", "```json", json.dumps(report.stage_9h_readiness, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## Preview Snippets", ""])
    for item in report.dry_run_items:
        lines.extend([f"### {item.dry_run_item_id}", "", "```markdown", item.generated_markdown_preview, "```", ""])
    lines.extend(["", "## Warnings / Blocking Reasons", ""])
    if report.warnings:
        lines.extend(f"- warning: {warning}" for warning in report.warnings)
    if report.blocking_reasons:
        lines.extend(f"- blocker: {reason}" for reason in report.blocking_reasons)
    if not report.warnings and not report.blocking_reasons:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _build_item(
    *,
    candidate: RevisedDraftCandidate,
    review: RevisedDraftReview,
    test_cases_dir: Path,
    existing: dict[str, Any],
    duplicate_draft_ids: set[str],
    duplicate_proposed_tc_ids: set[str],
) -> CreateApplyDryRunItem:
    target_file = _target_file_for_candidate(test_cases_dir, candidate)
    collision_risks: list[str] = []
    format_warnings: list[str] = []
    safety_warnings: list[str] = []

    if candidate.draft_id in duplicate_draft_ids:
        collision_risks.append(f"duplicate revised candidate id: {candidate.draft_id}")
    if candidate.proposed_tc_id in duplicate_proposed_tc_ids:
        collision_risks.append(f"duplicate proposed TC id in dry-run: {candidate.proposed_tc_id}")
    if candidate.proposed_tc_id in existing["tc_ids"]:
        collision_risks.append(f"existing TC id collision: {candidate.proposed_tc_id}")
    if target_file.exists():
        collision_risks.append(f"target file already exists: {target_file}")
    if _is_aggregate_path(target_file) or _looks_like_aggregate_file(target_file):
        collision_risks.append(f"target file is aggregate/index-like: {target_file}")
    if not candidate.source_req_ids:
        format_warnings.append("source_req_ids are absent; req_uids and source evidence refs are retained without fabrication")
    if review.warnings:
        format_warnings.extend(review.warnings)
    if candidate.manual_review_notes:
        format_warnings.extend(candidate.manual_review_notes)
    if candidate.creates_or_edits_canonical_tc:
        safety_warnings.append("candidate unexpectedly declares canonical write")
    if _uses_existing_tc_as_business_source(candidate):
        safety_warnings.append("candidate appears to use existing TC as business source")
    if not candidate.source_agent_decision_row_id:
        safety_warnings.append("missing source agent decision row id")
    if not candidate.source_validation_result_id:
        safety_warnings.append("missing source validation result id")
    if not candidate.source_draft_ids:
        safety_warnings.append("missing source draft ids")
    if not candidate.req_uids:
        safety_warnings.append("missing req_uids")
    if not candidate.source_evidence_refs:
        safety_warnings.append("missing source evidence refs")
    if _has_failed_safety_check(review):
        safety_warnings.append("Stage 9F safety check failed")

    planned_operation: PlannedOperation = "create_new_file"
    if collision_risks or safety_warnings:
        planned_operation = "blocked"
    decision: DryRunDecision = "dry_run_allowed"
    if planned_operation == "blocked":
        decision = "blocked"
    elif format_warnings or review.review_result == "approved-with-warnings":
        decision = "dry_run_allowed_with_warnings"

    return CreateApplyDryRunItem(
        dry_run_item_id=f"CDRY-{len(candidate.draft_id) % 1000:03d}-{_slug(candidate.draft_id)[-24:]}",
        source_revised_draft_id=candidate.draft_id,
        proposed_tc_id=candidate.proposed_tc_id,
        target_file_path=str(target_file),
        target_section="new standalone test case file",
        planned_operation=planned_operation,
        dry_run_decision=decision,
        generated_markdown_preview=_markdown_preview(candidate),
        traceability_refs=_unique(candidate.traceability_refs),
        req_uids=_unique(candidate.req_uids),
        source_req_ids=_unique(candidate.source_req_ids),
        source_evidence_refs=_unique(candidate.source_evidence_refs),
        source_agent_decision_row_id=candidate.source_agent_decision_row_id,
        source_validation_result_id=candidate.source_validation_result_id,
        review_result=review.review_result,
        review_warnings=_unique(review.warnings),
        collision_risks=_unique(collision_risks),
        format_warnings=_unique(format_warnings),
        safety_warnings=_unique(safety_warnings),
        creates_or_edits_canonical_tc=False,
    )


def _target_file_for_candidate(test_cases_dir: Path, candidate: RevisedDraftCandidate) -> Path:
    suffix = _slug(candidate.proposed_tc_id)
    return Path(test_cases_dir) / f"new-tc-{suffix}.md"


def _markdown_preview(candidate: RevisedDraftCandidate) -> str:
    lines = [
        f"## {candidate.proposed_tc_id} - {candidate.title}",
        "",
        "**Safety note:** dry-run preview only. Do not write this block to canonical test-cases from Stage 9G.",
        "",
        "**Preconditions:**",
        "",
    ]
    lines.extend(f"- {item}" for item in candidate.preconditions or ["No explicit source-backed precondition."])
    lines.extend(["", "**Steps:**", ""])
    lines.extend(f"{index}. {step}" for index, step in enumerate(candidate.steps, start=1))
    lines.extend(["", "**Expected Results:**", ""])
    lines.extend(f"- {item}" for item in candidate.expected_results)
    lines.extend(
        [
            "",
            f"**Traceability:** {', '.join(candidate.traceability_refs)}",
            f"**Source evidence refs:** {', '.join(candidate.source_evidence_refs)}",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _scan_existing_test_cases(test_cases_dir: Path) -> dict[str, Any]:
    tc_ids: dict[str, str] = {}
    files: list[str] = []
    aggregate_files: list[str] = []
    for path in sorted(Path(test_cases_dir).rglob("*.md")):
        files.append(str(path))
        if _looks_like_aggregate_file(path):
            aggregate_files.append(str(path))
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            match = TC_HEADING_RE.match(line)
            if match:
                tc_ids.setdefault(match.group(2), str(path))
    return {"tc_ids": tc_ids, "files": files, "aggregate_files": aggregate_files}


def _collision_checks(
    items: list[CreateApplyDryRunItem],
    existing: dict[str, Any],
    duplicate_draft_ids: set[str],
    duplicate_proposed_tc_ids: set[str],
) -> list[dict[str, Any]]:
    checks = [
        _check("duplicate_revised_candidate_ids", not duplicate_draft_ids, f"duplicates: {sorted(duplicate_draft_ids)}"),
        _check("duplicate_proposed_tc_ids", not duplicate_proposed_tc_ids, f"duplicates: {sorted(duplicate_proposed_tc_ids)}"),
        _check(
            "existing_tc_id_collisions",
            not [item for item in items if item.proposed_tc_id in existing["tc_ids"]],
            "no existing TC id collisions",
            failure_message="existing TC id collision detected",
        ),
        _check(
            "target_file_collisions",
            not [item for item in items if any("target file already exists" in risk for risk in item.collision_risks)],
            "no target file collisions",
            failure_message="target file collision detected",
        ),
        _check(
            "aggregate_target_risks",
            not [item for item in items if any("aggregate" in risk for risk in item.collision_risks)],
            "no aggregate target risks",
            failure_message="aggregate target risk detected",
        ),
    ]
    return checks


def _format_checks(items: list[CreateApplyDryRunItem]) -> list[dict[str, Any]]:
    return [
        _check("markdown_preview_present", all(item.generated_markdown_preview for item in items), "missing markdown preview"),
        _check("target_file_path_present", all(item.target_file_path for item in items), "missing target file path"),
        _check("source_req_ids_present", all(item.source_req_ids for item in items), "one or more items have no source_req_ids", warning=True),
        _check("review_warnings_captured", True, "review warnings are captured in item fields"),
    ]


def _safety_checks(items: list[CreateApplyDryRunItem], excluded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("canonical_write_allowed_false", True, "Stage 9G canonical writes are disabled"),
        _check("real_apply_authorized_false", True, "Stage 9G never authorizes real apply"),
        _check("no_apply_report_created", True, "Stage 9G writes only dry-run artifacts"),
        _check("no_patch_file_created", True, "Stage 9G does not create patch files"),
        _check("no_candidate_declares_canonical_write", not any(item.creates_or_edits_canonical_tc for item in items), "item declares canonical write"),
        _check("no_existing_tc_business_source", not any("business source" in " ".join(item.safety_warnings).casefold() for item in items), "existing TC used as business source"),
        _check("source_decision_traceability_present", all(item.source_agent_decision_row_id for item in items), "missing source decision traceability"),
        _check("validation_traceability_present", all(item.source_validation_result_id for item in items), "missing validation traceability"),
        _check("stage_9f_safety_checks_passed", not any("Stage 9F safety check failed" in item.safety_warnings for item in items), "Stage 9F safety failure"),
        _check("no_aggregate_targets", not any(any("aggregate" in risk for risk in item.collision_risks) for item in items), "aggregate target detected"),
        _check("excluded_candidates_recorded", True, f"excluded candidates: {len(excluded)}"),
    ]


def _target_file_plan(items: list[CreateApplyDryRunItem]) -> dict[str, Any]:
    return {
        "planned_strategy_counts": dict(Counter(item.planned_operation for item in items)),
        "targets": [
            {
                "dry_run_item_id": item.dry_run_item_id,
                "proposed_tc_id": item.proposed_tc_id,
                "target_file_path": item.target_file_path,
                "planned_operation": item.planned_operation,
                "target_section": item.target_section,
                "collision_risks": item.collision_risks,
            }
            for item in items
        ],
    }


def _tc_id_plan(items: list[CreateApplyDryRunItem], existing: dict[str, Any]) -> dict[str, Any]:
    duplicate_tc_ids = sorted(_duplicates([item.proposed_tc_id for item in items]))
    existing_collisions = sorted(item.proposed_tc_id for item in items if item.proposed_tc_id in existing["tc_ids"])
    return {
        "proposed_tc_ids_total": len(items),
        "unique_proposed_tc_ids_total": len({item.proposed_tc_id for item in items}),
        "duplicate_proposed_tc_ids": duplicate_tc_ids,
        "existing_tc_id_collisions": existing_collisions,
        "existing_tc_id_collision_count": len(existing_collisions),
    }


def _traceability_plan(items: list[CreateApplyDryRunItem]) -> dict[str, Any]:
    return {
        "items_with_req_uids": sum(1 for item in items if item.req_uids),
        "items_with_source_req_ids": sum(1 for item in items if item.source_req_ids),
        "items_with_source_evidence_refs": sum(1 for item in items if item.source_evidence_refs),
        "missing_source_req_ids_count": sum(1 for item in items if not item.source_req_ids),
        "traceability_by_item": {
            item.dry_run_item_id: {
                "req_uids": item.req_uids,
                "source_req_ids": item.source_req_ids,
                "source_evidence_refs": item.source_evidence_refs,
            }
            for item in items
        },
    }


def _excluded(candidate: RevisedDraftCandidate, reason: str) -> dict[str, Any]:
    return {
        "source_revised_draft_id": candidate.draft_id,
        "proposed_tc_id": candidate.proposed_tc_id,
        "reason": reason,
    }


def _blocked_report(
    package_id: str,
    revised_proposal_path: Path,
    revised_review_path: Path,
    input_paths: dict[str, str | None],
    blocking_reasons: list[str],
    created_at_utc: str,
    created_by_tool: str,
) -> NewTcCreateApplyDryRunReport:
    return NewTcCreateApplyDryRunReport(
        package_id=package_id,
        dry_run_status="blocked",
        source_revised_proposal_path=str(revised_proposal_path),
        source_revised_review_path=str(revised_review_path),
        dry_run_items=[],
        excluded_candidates=[],
        target_file_plan={},
        tc_id_plan={},
        traceability_plan={},
        collision_checks=[],
        format_checks=[],
        safety_checks=[],
        rollback_plan={"required_for_stage_9g": False, "backups_created": False},
        stage_9h_readiness={
            "stage_9h_design_recommended": False,
            "real_apply_authorized": False,
            "requires_explicit_user_approval": True,
            "requires_clean_git_status": True,
            "requires_no_blocked_dry_run_items": True,
            "requires_review_of_warnings": True,
            "required_next_action": "Resolve Stage 9G blockers before any Stage 9H design.",
        },
        canonical_write_allowed=False,
        real_apply_authorized=False,
        input_paths=input_paths,
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


def _looks_like_aggregate_file(path: Path) -> bool:
    if not path.exists() or path.suffix.lower() != ".md":
        return False
    try:
        first_lines = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:80]).casefold()
    except OSError:
        return False
    return any(marker in first_lines for marker in AGGREGATE_FILE_MARKERS)


def _is_aggregate_path(path: Path) -> bool:
    name = path.name.casefold()
    return name in {"14-application-card.md", "index.md"} or "aggregate" in name


def _has_failed_safety_check(review: RevisedDraftReview) -> bool:
    return any(check.get("area") == "safety" and check.get("status") in {"failed", "blocked"} for check in review.checks)


def _uses_existing_tc_as_business_source(candidate: RevisedDraftCandidate) -> bool:
    text = "\n".join([candidate.agent_decision_rationale, *candidate.existing_tc_coverage_notes]).casefold()
    return "existing tc" in text and "business source" in text


def _check(
    check_id: str,
    passed: bool,
    message: str,
    *,
    warning: bool = False,
    failure_message: str | None = None,
) -> dict[str, Any]:
    if passed:
        status = "pass"
    else:
        status = "warning" if warning else "failed"
    return {"check_id": check_id, "status": status, "message": message if passed else (failure_message or message)}


def _checks_markdown(checks: list[dict[str, Any]]) -> list[str]:
    if not checks:
        return ["- none"]
    return [f"- `{check['check_id']}`: `{check['status']}` - {check.get('message', '')}" for check in checks]


def _duplicates(values: list[str]) -> set[str]:
    counts = Counter(values)
    return {value for value, count in counts.items() if value and count > 1}


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()
    return slug or "new-test-case"


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
