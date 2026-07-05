from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.traceability_backfill_proposals import (
    TraceabilityBackfillProposal,
    load_traceability_backfill_proposal,
)
from test_case_agent.traceability_mismatch_diagnostics import LEGACY_REF_RE, REQ_UID_RE
from test_case_agent.traceability_mismatch_diagnostics import SOURCE_REQ_ID_RE as FULL_SOURCE_REQ_ID_RE
from test_case_agent.traceability_mismatch_diagnostics import load_traceability_mismatch_diagnostics
from test_case_agent.traceability_repair_strategy import (
    TraceabilityRepairItem,
    load_traceability_repair_strategy,
)
from test_case_agent.writer_dry_run_proposals import TC_HEADING_RE, TRACEABILITY_LABELS, compute_file_sha256

CREATED_BY_TOOL = "test_case_agent.traceability_backfill_review"
REVIEW_PREFIX = "traceability-backfill-review"

ReviewStatus = Literal["approved", "approved-with-warnings", "rejected", "blocked"]
ReviewRiskLevel = Literal["low", "medium", "high"]
CheckStatus = Literal["pass", "warning", "failed", "blocked"]


@dataclass(frozen=True)
class TraceabilityBackfillReviewCheck:
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
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityBackfillReviewCheck":
        return cls(
            check_id=str(data["check_id"]),
            status=data["status"],
            message=str(data["message"]),
            details=dict(data.get("details") or {}),
        )


@dataclass
class TraceabilityBackfillReviewReport:
    package_id: str
    review_status: ReviewStatus
    safe_for_controlled_apply: bool
    risk_level: ReviewRiskLevel
    checks: list[TraceabilityBackfillReviewCheck]
    failed_checks: list[str]
    warnings: list[str]
    blocking_reasons: list[str]
    reviewer_recommendation: str
    input_paths: dict[str, Any]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "review_status": self.review_status,
            "safe_for_controlled_apply": self.safe_for_controlled_apply,
            "risk_level": self.risk_level,
            "checks": [check.to_dict() for check in self.checks],
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "reviewer_recommendation": self.reviewer_recommendation,
            "input_paths": self.input_paths,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityBackfillReviewReport":
        return cls(
            package_id=str(data["package_id"]),
            review_status=data["review_status"],
            safe_for_controlled_apply=bool(data["safe_for_controlled_apply"]),
            risk_level=data["risk_level"],
            checks=[
                TraceabilityBackfillReviewCheck.from_dict(check)
                for check in data.get("checks", [])
            ],
            failed_checks=list(data.get("failed_checks") or []),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            reviewer_recommendation=str(data.get("reviewer_recommendation") or ""),
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_traceability_backfill_review(
    *,
    package_id: str,
    backfill_proposal_path: Path,
    repair_strategy_path: Path,
    diagnostics_path: Path,
    old_registry_path: Path,
    new_registry_path: Path,
    test_cases_dir: Path,
    workspace_root: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> TraceabilityBackfillReviewReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    backfill_proposal_path = Path(backfill_proposal_path)
    repair_strategy_path = Path(repair_strategy_path)
    diagnostics_path = Path(diagnostics_path)
    old_registry_path = Path(old_registry_path)
    new_registry_path = Path(new_registry_path)
    test_cases_dir = Path(test_cases_dir)
    input_paths = {
        "backfill_proposal_path": str(backfill_proposal_path),
        "repair_strategy_path": str(repair_strategy_path),
        "diagnostics_path": str(diagnostics_path),
        "old_registry_path": str(old_registry_path),
        "new_registry_path": str(new_registry_path),
        "test_cases_dir": str(test_cases_dir),
    }

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    checks: list[TraceabilityBackfillReviewCheck] = []
    proposal: TraceabilityBackfillProposal | None = None
    repair_items_by_id: dict[str, TraceabilityRepairItem] = {}
    old_registry_req_uids: set[str] = set()
    new_registry_req_uids: set[str] = set()

    for label, path in [
        ("traceability backfill proposal", backfill_proposal_path),
        ("traceability repair strategy", repair_strategy_path),
        ("traceability mismatch diagnostics", diagnostics_path),
        ("old requirements registry", old_registry_path),
        ("new requirements registry", new_registry_path),
        ("test-cases dir", test_cases_dir),
    ]:
        if not path.exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    if backfill_proposal_path.exists():
        try:
            proposal = load_traceability_backfill_proposal(backfill_proposal_path)
            warnings.extend(proposal.warnings)
            blocking_reasons.extend(proposal.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"traceability backfill proposal cannot be parsed: {backfill_proposal_path}: {exc}")

    if repair_strategy_path.exists():
        try:
            strategy = load_traceability_repair_strategy(repair_strategy_path)
            warnings.extend(strategy.warnings)
            repair_items_by_id = {item.repair_item_id: item for item in strategy.repair_items}
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"traceability repair strategy cannot be parsed: {repair_strategy_path}: {exc}")

    if diagnostics_path.exists():
        try:
            diagnostics = load_traceability_mismatch_diagnostics(diagnostics_path)
            warnings.extend(diagnostics.warnings)
            blocking_reasons.extend(diagnostics.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"traceability mismatch diagnostics cannot be parsed: {diagnostics_path}: {exc}")

    if old_registry_path.exists():
        try:
            old_registry_req_uids = _load_registry_req_uids(old_registry_path)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"old requirements registry cannot be parsed: {old_registry_path}: {exc}")
    if new_registry_path.exists():
        try:
            new_registry_req_uids = _load_registry_req_uids(new_registry_path)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"new requirements registry cannot be parsed: {new_registry_path}: {exc}")

    current_text = ""
    current_blocks: dict[str, _TcBlock] = {}
    current_traceability_lines: dict[str, str] = {}
    if proposal is not None and proposal.file_path:
        resolved_file = _resolve_file(proposal.file_path, workspace_root)
        resolved_test_cases_dir = _resolve_file(test_cases_dir, workspace_root)
        if not _is_relative_to(resolved_file, resolved_test_cases_dir):
            blocking_reasons.append(f"proposal file_path is outside test-cases dir: {proposal.file_path}")
        elif not resolved_file.exists():
            blocking_reasons.append(f"proposal file_path is missing: {proposal.file_path}")
        else:
            current_text = resolved_file.read_text(encoding="utf-8")
            current_blocks = _single_tc_blocks(current_text.splitlines(keepends=True))
            current_traceability_lines = _current_traceability_lines(current_blocks, proposal.affected_test_case_ids)

    if proposal is None or blocking_reasons:
        return _report(
            package_id=package_id,
            checks=checks,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            input_paths=input_paths,
            created_by_tool=created_by_tool,
        )

    checks.extend(_proposal_metadata_checks(proposal, package_id))
    checks.extend(_sha_checks(proposal, workspace_root))
    checks.extend(_listed_scope_checks(proposal))
    checks.extend(_block_current_match_checks(proposal, current_blocks))
    checks.extend(_line_safety_checks(proposal))
    checks.extend(_legacy_ref_checks(proposal))
    checks.extend(_duplicate_req_checks(proposal))
    checks.extend(_registry_checks(proposal, old_registry_req_uids, new_registry_req_uids))
    checks.extend(_candidate_checks(proposal, repair_items_by_id))
    checks.extend(_supporting_source_checks(proposal, current_traceability_lines))
    checks.extend(_diff_consistency_checks(proposal, current_text))

    return _report(
        package_id=package_id,
        checks=checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        input_paths=input_paths,
        created_by_tool=created_by_tool,
    )


def write_traceability_backfill_review(
    report: TraceabilityBackfillReviewReport,
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
        render_traceability_backfill_review_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_traceability_backfill_review(path: Path) -> TraceabilityBackfillReviewReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Traceability backfill review root must be a JSON object.")
    return TraceabilityBackfillReviewReport.from_dict(payload)


def render_traceability_backfill_review_markdown(report: TraceabilityBackfillReviewReport) -> str:
    lines = [
        f"# Traceability Backfill Review {report.package_id}",
        "",
        "## Summary",
        "",
        f"- Review status: `{report.review_status}`",
        f"- Safe for controlled apply: `{str(report.safe_for_controlled_apply).lower()}`",
        f"- Risk level: `{report.risk_level}`",
        f"- Failed checks: `{', '.join(report.failed_checks) or 'none'}`",
        f"- Warnings count: `{len(report.warnings)}`",
        f"- Blocking reasons count: `{len(report.blocking_reasons)}`",
        f"- Reviewer recommendation: {report.reviewer_recommendation}",
        "",
        "## Checks",
        "",
    ]
    for check in report.checks:
        lines.append(f"- `{check.status}` `{check.check_id}`: {check.message}")
    if report.failed_checks:
        lines.extend(["", "## Failed Checks", ""])
        for check_id in report.failed_checks:
            lines.append(f"- `{check_id}`")
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in report.warnings:
            lines.append(f"- {warning}")
    if report.blocking_reasons:
        lines.extend(["", "## Blocking Reasons", ""])
        for reason in report.blocking_reasons:
            lines.append(f"- {reason}")
    lines.extend(["", "## Safety", ""])
    lines.append("- Review only; canonical test-case files are not modified.")
    lines.append("- Preview patch is not applied.")
    lines.append("- `--apply` is not used.")
    return "\n".join(lines).rstrip() + "\n"


def _proposal_metadata_checks(
    proposal: TraceabilityBackfillProposal,
    package_id: str,
) -> list[TraceabilityBackfillReviewCheck]:
    checks = [
        _check(
            "proposal_package_matches",
            proposal.package_id == package_id,
            f"proposal package_id is {proposal.package_id}.",
            {"expected_package_id": package_id, "actual_package_id": proposal.package_id},
        ),
        _check(
            "proposal_status_not_blocked",
            proposal.proposal_status != "blocked",
            f"proposal_status is {proposal.proposal_status}.",
        ),
        _check(
            "manual_review_required",
            proposal.manual_review_required is True,
            f"manual_review_required is {proposal.manual_review_required}.",
        ),
        _check(
            "has_backfill_changes",
            bool(proposal.backfill_changes),
            f"backfill_changes count is {len(proposal.backfill_changes)}.",
        ),
    ]
    blocked_changes = [change.repair_item_id for change in proposal.backfill_changes if change.status == "blocked"]
    checks.append(_check(
        "no_blocked_backfill_changes",
        not blocked_changes,
        "backfill changes do not contain blocked items.",
        {"blocked_change_repair_item_ids": blocked_changes},
    ))
    return checks


def _sha_checks(
    proposal: TraceabilityBackfillProposal,
    workspace_root: Path,
) -> list[TraceabilityBackfillReviewCheck]:
    if not proposal.file_path:
        return [_failed("canonical_sha_unchanged", "proposal has no file_path.")]
    resolved_file = _resolve_file(proposal.file_path, workspace_root)
    current_sha = compute_file_sha256(resolved_file) if resolved_file.exists() else None
    expected = (
        bool(proposal.sha256_before)
        and proposal.sha256_before == proposal.sha256_after
        and proposal.sha256_before == current_sha
    )
    return [_check(
        "canonical_sha_unchanged",
        expected,
        "proposal SHA before/after matches the current canonical file.",
        {
            "sha256_before": proposal.sha256_before,
            "sha256_after": proposal.sha256_after,
            "current_sha256": current_sha,
        },
    )]


def _listed_scope_checks(proposal: TraceabilityBackfillProposal) -> list[TraceabilityBackfillReviewCheck]:
    affected = set(proposal.affected_test_case_ids)
    original_keys = set(proposal.original_tc_blocks)
    proposed_keys = set(proposal.proposed_tc_blocks)
    change_tcs = {change.test_case_id for change in proposal.backfill_changes}
    unlisted = sorted((original_keys | proposed_keys | change_tcs) - affected)
    missing = sorted(affected - (original_keys & proposed_keys))
    return [
        _check(
            "patch_changes_only_listed_tc_blocks",
            not unlisted and not missing,
            "proposal block keys and change TC IDs are limited to affected_test_case_ids.",
            {
                "affected_test_case_ids": sorted(affected),
                "unlisted_tc_ids": unlisted,
                "missing_affected_tc_ids": missing,
            },
        ),
        _check(
            "no_unrelated_tc_ids_touched",
            not unlisted,
            "no unrelated TC IDs are present in proposal changes.",
            {"unlisted_tc_ids": unlisted},
        ),
    ]


def _block_current_match_checks(
    proposal: TraceabilityBackfillProposal,
    current_blocks: dict[str, "_TcBlock"],
) -> list[TraceabilityBackfillReviewCheck]:
    stale: list[str] = []
    for tc_id, original_block in proposal.original_tc_blocks.items():
        current = current_blocks.get(tc_id)
        if current is None or current.text != original_block:
            stale.append(tc_id)
    return [_check(
        "proposal_original_blocks_match_current_file",
        not stale,
        "proposal original TC blocks match current canonical file.",
        {"stale_or_missing_tc_ids": stale},
    )]


def _line_safety_checks(proposal: TraceabilityBackfillProposal) -> list[TraceabilityBackfillReviewCheck]:
    non_trace_changes: list[dict[str, Any]] = []
    traceability_count_errors: list[str] = []
    unchanged_tcs: list[str] = []
    for tc_id, original_block in proposal.original_tc_blocks.items():
        proposed_block = proposal.proposed_tc_blocks.get(tc_id)
        if proposed_block is None:
            continue
        original_trace_count = len(_traceability_lines(original_block))
        proposed_trace_count = len(_traceability_lines(proposed_block))
        if original_trace_count != 1 or proposed_trace_count != 1:
            traceability_count_errors.append(tc_id)
        changed_lines = _changed_lines(original_block, proposed_block)
        if not changed_lines:
            unchanged_tcs.append(tc_id)
        for line in changed_lines:
            if not _is_traceability_line(line):
                non_trace_changes.append({"test_case_id": tc_id, "line": line})
    return [
        _check(
            "exactly_one_traceability_line_per_changed_tc",
            not traceability_count_errors,
            "each changed TC block has exactly one traceability line before and after proposal.",
            {"tc_ids": traceability_count_errors},
        ),
        _check(
            "patch_changes_only_traceability_lines",
            not non_trace_changes,
            "all changed lines are traceability lines.",
            {"non_traceability_changes": non_trace_changes[:10]},
        ),
        _check(
            "no_steps_expected_test_data_headings_changed",
            not non_trace_changes,
            "no non-traceability content changed.",
            {"non_traceability_changes": non_trace_changes[:10]},
        ),
        _check(
            "listed_tc_blocks_have_changes",
            not unchanged_tcs,
            "all listed TC blocks have a proposed traceability change.",
            {"unchanged_tc_ids": unchanged_tcs},
            warning=True,
        ),
    ]


def _legacy_ref_checks(proposal: TraceabilityBackfillProposal) -> list[TraceabilityBackfillReviewCheck]:
    missing_legacy: list[dict[str, Any]] = []
    for change in proposal.backfill_changes:
        old_refs = _legacy_refs(change.old_traceability_line)
        new_refs = set(_legacy_refs(change.new_traceability_line))
        missing = [ref for ref in old_refs if ref not in new_refs]
        if missing:
            missing_legacy.append({"test_case_id": change.test_case_id, "repair_item_id": change.repair_item_id, "missing": missing})
    return [_check(
        "legacy_refs_preserved",
        not missing_legacy,
        "legacy refs from the old traceability line are preserved.",
        {"missing_legacy_refs": missing_legacy},
    )]


def _duplicate_req_checks(proposal: TraceabilityBackfillProposal) -> list[TraceabilityBackfillReviewCheck]:
    duplicates: list[dict[str, Any]] = []
    actual_mismatches: list[dict[str, Any]] = []
    for tc_id, changes in _changes_by_tc(proposal.backfill_changes).items():
        old_line = changes[0].old_traceability_line
        new_line = changes[0].new_traceability_line
        old_reqs = set(_req_uids(old_line))
        new_req_counts = Counter(_req_uids(new_line))
        declared = sorted({req for change in changes for req in change.added_req_uids})
        actual_added = sorted(set(new_req_counts) - old_reqs)
        for req_uid in declared:
            if new_req_counts.get(req_uid, 0) != 1 or req_uid in old_reqs:
                duplicates.append({
                    "test_case_id": tc_id,
                    "req_uid": req_uid,
                    "old_count": 1 if req_uid in old_reqs else 0,
                    "new_count": new_req_counts.get(req_uid, 0),
                })
        if declared != actual_added:
            actual_mismatches.append({
                "test_case_id": tc_id,
                "declared_added_req_uids": declared,
                "actual_added_req_uids": actual_added,
            })
    return [
        _check(
            "added_req_refs_not_duplicated",
            not duplicates,
            "added REQ-* refs are not duplicated and were absent from old traceability line.",
            {"duplicates": duplicates},
        ),
        _check(
            "declared_added_req_refs_match_traceability_delta",
            not actual_mismatches,
            "declared added REQ-* refs match the actual traceability-line delta.",
            {"mismatches": actual_mismatches},
        ),
    ]


def _registry_checks(
    proposal: TraceabilityBackfillProposal,
    old_registry_req_uids: set[str],
    new_registry_req_uids: set[str],
) -> list[TraceabilityBackfillReviewCheck]:
    missing: list[str] = []
    registry_hits: dict[str, str] = {}
    for req_uid in _proposal_added_req_uids(proposal):
        in_old = req_uid in old_registry_req_uids
        in_new = req_uid in new_registry_req_uids
        if not in_old and not in_new:
            missing.append(req_uid)
        else:
            registry_hits[req_uid] = "old+new" if in_old and in_new else ("old" if in_old else "new")
    return [_check(
        "added_req_refs_exist_in_registry",
        not missing,
        "added REQ-* refs exist in old or new requirements registry.",
        {"missing_req_uids": missing, "registry_hits": registry_hits},
    )]


def _candidate_checks(
    proposal: TraceabilityBackfillProposal,
    repair_items_by_id: dict[str, TraceabilityRepairItem],
) -> list[TraceabilityBackfillReviewCheck]:
    missing_items: list[str] = []
    not_candidates: list[dict[str, Any]] = []
    for change in proposal.backfill_changes:
        item = repair_items_by_id.get(change.repair_item_id)
        if item is None:
            missing_items.append(change.repair_item_id)
            continue
        candidates = {_normalize_ref(req_uid) for req_uid in item.candidate_req_uids_to_backfill}
        extra = [req_uid for req_uid in change.added_req_uids if _normalize_ref(req_uid) not in candidates]
        if extra:
            not_candidates.append({"repair_item_id": change.repair_item_id, "extra_req_uids": extra})
    return [_check(
        "added_req_refs_match_repair_strategy_candidates",
        not missing_items and not not_candidates,
        "added REQ-* refs match candidate_req_uids_to_backfill from repair strategy.",
        {"missing_repair_item_ids": missing_items, "not_candidate_req_uids": not_candidates},
    )]


def _supporting_source_checks(
    proposal: TraceabilityBackfillProposal,
    current_traceability_lines: dict[str, str],
) -> list[TraceabilityBackfillReviewCheck]:
    missing: list[dict[str, Any]] = []
    for change in proposal.backfill_changes:
        current_line = current_traceability_lines.get(change.test_case_id, "")
        for source_req_id in change.supporting_source_req_ids:
            if not _contains_ref(current_line, source_req_id):
                missing.append({
                    "test_case_id": change.test_case_id,
                    "repair_item_id": change.repair_item_id,
                    "source_req_id": source_req_id,
                })
    return [_check(
        "supporting_source_req_ids_present_in_current_traceability",
        not missing,
        "supporting source_req_id refs are present in current traceability lines.",
        {"missing_supporting_source_req_ids": missing},
    )]


def _diff_consistency_checks(
    proposal: TraceabilityBackfillProposal,
    current_text: str,
) -> list[TraceabilityBackfillReviewCheck]:
    if not current_text or not proposal.file_path:
        return [_failed("unified_diff_matches_structured_blocks", "current file text is unavailable.")]
    lines = current_text.splitlines(keepends=True)
    current_blocks = _single_tc_blocks(lines)
    proposed_lines = list(lines)
    for tc_id, proposed_block in sorted(
        proposal.proposed_tc_blocks.items(),
        key=lambda item: current_blocks[item[0]].start if item[0] in current_blocks else -1,
        reverse=True,
    ):
        block = current_blocks.get(tc_id)
        if block is None:
            continue
        proposed_lines[block.start:block.end] = proposed_block.splitlines(keepends=True)
    import difflib

    expected = "".join(difflib.unified_diff(
        lines,
        proposed_lines,
        fromfile=f"a/{proposal.file_path}",
        tofile=f"b/{proposal.file_path}",
    ))
    ok = expected == proposal.unified_diff_preview
    return [_check(
        "unified_diff_matches_structured_blocks",
        ok,
        "unified diff preview matches structured original/proposed TC blocks.",
        {
            "expected_length": len(expected),
            "actual_length": len(proposal.unified_diff_preview),
        },
    )]


def _report(
    *,
    package_id: str,
    checks: list[TraceabilityBackfillReviewCheck],
    warnings: list[str],
    blocking_reasons: list[str],
    input_paths: dict[str, Any],
    created_by_tool: str,
) -> TraceabilityBackfillReviewReport:
    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    failed_checks = [check.check_id for check in checks if check.status == "failed"]
    if blocking_reasons:
        review_status: ReviewStatus = "blocked"
    elif failed_checks:
        review_status = "rejected"
    elif warnings or any(check.status == "warning" for check in checks):
        review_status = "approved-with-warnings"
    else:
        review_status = "approved"
    safe_for_controlled_apply = review_status in {"approved", "approved-with-warnings"}
    risk_level = _review_risk_level(review_status)
    return TraceabilityBackfillReviewReport(
        package_id=package_id,
        review_status=review_status,
        safe_for_controlled_apply=safe_for_controlled_apply,
        risk_level=risk_level,
        checks=checks,
        failed_checks=failed_checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        reviewer_recommendation=_reviewer_recommendation(review_status),
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _review_risk_level(status: ReviewStatus) -> ReviewRiskLevel:
    if status in {"blocked", "rejected"}:
        return "high"
    if status == "approved-with-warnings":
        return "medium"
    return "low"


def _reviewer_recommendation(status: ReviewStatus) -> str:
    if status == "approved":
        return "safe for controlled apply of traceability-line-only backfill, with manual review retained."
    if status == "approved-with-warnings":
        return "safe for controlled apply only after acknowledging warnings; changes remain traceability-line-only."
    if status == "rejected":
        return "do not apply; fix failed checks and rebuild/review the proposal."
    return "review is blocked; rebuild or provide missing artifacts before any apply step."


@dataclass(frozen=True)
class _TcBlock:
    tc_id: str
    start: int
    end: int
    text: str


def _single_tc_blocks(lines: list[str]) -> dict[str, _TcBlock]:
    indexed: dict[str, list[_TcBlock]] = {}
    headings: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line)
        if match:
            headings.append((match.group(2), index))
    for offset, (tc_id, start) in enumerate(headings):
        end = headings[offset + 1][1] if offset + 1 < len(headings) else len(lines)
        indexed.setdefault(tc_id, []).append(_TcBlock(tc_id=tc_id, start=start, end=end, text="".join(lines[start:end])))
    return {tc_id: blocks[0] for tc_id, blocks in indexed.items() if len(blocks) == 1}


def _current_traceability_lines(
    current_blocks: dict[str, _TcBlock],
    tc_ids: list[str],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for tc_id in tc_ids:
        block = current_blocks.get(tc_id)
        if block is None:
            continue
        lines = _traceability_lines(block.text)
        if len(lines) == 1:
            result[tc_id] = lines[0]
    return result


def _changed_lines(original_block: str, proposed_block: str) -> list[str]:
    original_lines = original_block.splitlines()
    proposed_lines = proposed_block.splitlines()
    import difflib

    changed: list[str] = []
    matcher = difflib.SequenceMatcher(None, original_lines, proposed_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        changed.extend(original_lines[i1:i2])
        changed.extend(proposed_lines[j1:j2])
    return changed


def _traceability_lines(block_text: str) -> list[str]:
    return [
        line.strip()
        for line in block_text.splitlines()
        if _is_traceability_line(line)
    ]


def _is_traceability_line(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(label) for label in TRACEABILITY_LABELS)


def _legacy_refs(line: str) -> list[str]:
    return _unique(match.group(0).upper().replace("  ", " ") for match in LEGACY_REF_RE.finditer(line))


def _req_uids(line: str) -> list[str]:
    return [match.group(0).upper() for match in REQ_UID_RE.finditer(line)]


def _proposal_added_req_uids(proposal: TraceabilityBackfillProposal) -> list[str]:
    return _unique(
        _normalize_ref(req_uid)
        for change in proposal.backfill_changes
        for req_uid in change.added_req_uids
    )


def _changes_by_tc(changes: list[Any]) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for change in changes:
        result.setdefault(change.test_case_id, []).append(change)
    return result


def _load_registry_req_uids(path: Path) -> set[str]:
    result: set[str] = set()
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError(f"registry line {line_number} is not a JSON object")
        req_uid = data.get("req_uid")
        if req_uid:
            result.add(_normalize_ref(str(req_uid)))
    return result


def _contains_ref(line: str, expected_ref: str | None) -> bool:
    if not expected_ref:
        return False
    expected = _normalize_ref(expected_ref)
    candidates = [
        *(_normalize_ref(match.group(0)) for match in FULL_SOURCE_REQ_ID_RE.finditer(line)),
        *(_normalize_ref(match.group(0)) for match in REQ_UID_RE.finditer(line)),
    ]
    return expected in set(candidates)


def _check(
    check_id: str,
    ok: bool,
    message: str,
    details: dict[str, Any] | None = None,
    *,
    warning: bool = False,
) -> TraceabilityBackfillReviewCheck:
    if ok:
        status: CheckStatus = "pass"
    elif warning:
        status = "warning"
    else:
        status = "failed"
    return TraceabilityBackfillReviewCheck(
        check_id=check_id,
        status=status,
        message=message,
        details=details or {},
    )


def _failed(check_id: str, message: str) -> TraceabilityBackfillReviewCheck:
    return TraceabilityBackfillReviewCheck(check_id=check_id, status="failed", message=message, details={})


def _resolve_file(path: str | Path, workspace_root: Path) -> Path:
    value = Path(str(path).replace("\\", "/"))
    if value.is_absolute():
        return value.resolve()
    return (workspace_root / value).resolve()


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _normalize_ref(ref: str) -> str:
    return " ".join(str(ref).strip().upper().split())


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
