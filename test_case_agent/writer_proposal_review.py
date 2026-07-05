from __future__ import annotations

import difflib
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.test_case_update_plan import TestCaseUpdatePlan, load_test_case_update_plan
from test_case_agent.traceability_mismatch_diagnostics import LEGACY_REF_RE, REQ_UID_RE
from test_case_agent.writer_dry_run_proposals import (
    TC_HEADING_RE,
    TRACEABILITY_LABELS,
    WriterDryRunProposal,
    compute_file_sha256,
    load_writer_dry_run_proposal,
)

CREATED_BY_TOOL = "test_case_agent.writer_proposal_review"
REVIEW_PREFIX = "writer-proposal-review"

ReviewStatus = Literal["approved", "approved-with-warnings", "rejected", "blocked"]
ReviewRiskLevel = Literal["low", "medium", "high"]
CheckStatus = Literal["pass", "warning", "failed", "blocked"]

REQ_AUTOFIN_RE = re.compile(r"\bREQ-AUTOFIN-[A-Z0-9]+\b")


@dataclass(frozen=True)
class WriterProposalReviewCheck:
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
    def from_dict(cls, data: dict[str, Any]) -> "WriterProposalReviewCheck":
        return cls(
            check_id=str(data["check_id"]),
            status=data["status"],
            message=str(data["message"]),
            details=dict(data.get("details") or {}),
        )


@dataclass
class WriterProposalReviewReport:
    package_id: str
    review_status: ReviewStatus
    safe_for_controlled_apply: bool
    risk_level: ReviewRiskLevel
    checks: list[WriterProposalReviewCheck]
    failed_checks: list[str]
    warnings: list[str]
    blocking_reasons: list[str]
    reviewer_recommendation: str
    input_paths: dict[str, Any]
    created_at_utc: str
    created_by_tool: str
    git_state: dict[str, Any] = field(default_factory=dict)

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
            "git_state": self.git_state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriterProposalReviewReport":
        return cls(
            package_id=str(data["package_id"]),
            review_status=data["review_status"],
            safe_for_controlled_apply=bool(data["safe_for_controlled_apply"]),
            risk_level=data["risk_level"],
            checks=[
                WriterProposalReviewCheck.from_dict(check)
                for check in data.get("checks", [])
            ],
            failed_checks=list(data.get("failed_checks") or []),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            reviewer_recommendation=str(data.get("reviewer_recommendation") or ""),
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            git_state=dict(data.get("git_state") or {}),
        )


def build_writer_proposal_review(
    *,
    package_id: str,
    writer_proposal_path: Path,
    writer_proposal_markdown_path: Path | None = None,
    writer_proposal_patch_path: Path | None = None,
    update_plan_path: Path,
    impact_report_path: Path,
    requirements_diff_path: Path,
    old_registry_path: Path,
    new_registry_path: Path,
    test_cases_dir: Path,
    workspace_root: Path | None = None,
    expected_affected_test_case_ids: list[str] | None = None,
    record_git_state: bool = True,
    created_by_tool: str = CREATED_BY_TOOL,
) -> WriterProposalReviewReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    writer_proposal_path = Path(writer_proposal_path)
    update_plan_path = Path(update_plan_path)
    impact_report_path = Path(impact_report_path)
    requirements_diff_path = Path(requirements_diff_path)
    old_registry_path = Path(old_registry_path)
    new_registry_path = Path(new_registry_path)
    test_cases_dir = Path(test_cases_dir)
    input_paths = {
        "writer_proposal_path": str(writer_proposal_path),
        "writer_proposal_markdown_path": str(writer_proposal_markdown_path) if writer_proposal_markdown_path else None,
        "writer_proposal_patch_path": str(writer_proposal_patch_path) if writer_proposal_patch_path else None,
        "update_plan_path": str(update_plan_path),
        "impact_report_path": str(impact_report_path),
        "requirements_diff_path": str(requirements_diff_path),
        "old_registry_path": str(old_registry_path),
        "new_registry_path": str(new_registry_path),
        "test_cases_dir": str(test_cases_dir),
    }

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    checks: list[WriterProposalReviewCheck] = []
    proposal: WriterDryRunProposal | None = None
    update_plan: TestCaseUpdatePlan | None = None
    old_registry_req_uids: set[str] = set()
    new_registry_req_uids: set[str] = set()

    required_paths = [
        ("writer dry-run proposal", writer_proposal_path),
        ("test-case update plan", update_plan_path),
        ("impact report", impact_report_path),
        ("requirements diff", requirements_diff_path),
        ("old requirements registry", old_registry_path),
        ("new requirements registry", new_registry_path),
        ("test-cases dir", test_cases_dir),
    ]
    optional_paths = [
        ("writer dry-run proposal markdown", writer_proposal_markdown_path),
        ("writer dry-run proposal patch", writer_proposal_patch_path),
    ]
    for label, path in required_paths:
        if not Path(path).exists():
            blocking_reasons.append(f"{label} is missing: {path}")
    for label, path in optional_paths:
        if path is not None and not Path(path).exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    if writer_proposal_path.exists():
        try:
            proposal = load_writer_dry_run_proposal(writer_proposal_path)
            warnings.extend(proposal.warnings)
            blocking_reasons.extend(proposal.blocking_reasons)
        except Exception as exc:  # noqa: BLE001 - review reports parse failures.
            blocking_reasons.append(f"writer dry-run proposal cannot be parsed: {writer_proposal_path}: {exc}")

    if update_plan_path.exists():
        try:
            update_plan = load_test_case_update_plan(update_plan_path)
            warnings.extend(update_plan.warnings)
            blocking_reasons.extend(update_plan.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"test-case update plan cannot be parsed: {update_plan_path}: {exc}")

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

    resolved_file: Path | None = None
    current_text = ""
    current_blocks: dict[str, _TcBlock] = {}
    current_traceability_lines: dict[str, str] = {}
    git_state: dict[str, Any] = {}
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
            if record_git_state:
                git_state = _collect_git_state(workspace_root, resolved_file)

    if proposal is None or update_plan is None or blocking_reasons:
        return _report(
            package_id=package_id,
            checks=checks,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            input_paths=input_paths,
            git_state=git_state,
            created_by_tool=created_by_tool,
        )

    checks.extend(_proposal_metadata_checks(proposal, package_id))
    checks.extend(_scope_checks(proposal, expected_tc_ids=expected_affected_test_case_ids))
    checks.extend(_current_file_state_checks(
        proposal=proposal,
        resolved_file=resolved_file,
        current_blocks=current_blocks,
        current_traceability_lines=current_traceability_lines,
    ))
    checks.extend(_line_safety_checks(proposal))
    checks.extend(_traceability_replacement_checks(proposal))
    checks.extend(_registry_checks(proposal, old_registry_req_uids, new_registry_req_uids))
    checks.extend(_update_plan_checks(proposal, update_plan))
    checks.extend(_diff_consistency_checks(proposal, current_text))
    if record_git_state:
        checks.append(_git_state_check(git_state))

    return _report(
        package_id=package_id,
        checks=checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        input_paths=input_paths,
        git_state=git_state,
        created_by_tool=created_by_tool,
    )


def write_writer_proposal_review(
    report: WriterProposalReviewReport,
    out_dir: Path,
    *,
    artifact_suffix: str | None = None,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = _artifact_suffix(artifact_suffix)
    json_path = out_dir / f"{REVIEW_PREFIX}-{report.package_id}{suffix}.json"
    markdown_path = out_dir / f"{REVIEW_PREFIX}-{report.package_id}{suffix}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_writer_proposal_review_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_writer_proposal_review(path: Path) -> WriterProposalReviewReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Writer proposal review root must be a JSON object.")
    return WriterProposalReviewReport.from_dict(payload)


def render_writer_proposal_review_markdown(report: WriterProposalReviewReport) -> str:
    lines = [
        f"# Writer Proposal Review {report.package_id}",
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
    lines.extend(["", "## Git State", ""])
    if report.git_state:
        lines.append(f"- status output empty: `{str(report.git_state.get('status_short_empty')).lower()}`")
        lines.append(f"- diff output empty: `{str(report.git_state.get('diff_empty')).lower()}`")
        lines.append(f"- cached diff output empty: `{str(report.git_state.get('cached_diff_empty')).lower()}`")
    else:
        lines.append("- not recorded")
    lines.extend(["", "## Safety", ""])
    lines.append("- Review only; canonical test-case files are not modified.")
    lines.append("- Preview patch is not applied.")
    lines.append("- `--apply` is not used.")
    return "\n".join(lines).rstrip() + "\n"


def _proposal_metadata_checks(
    proposal: WriterDryRunProposal,
    package_id: str,
) -> list[WriterProposalReviewCheck]:
    return [
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
            "has_proposed_changes",
            bool(proposal.proposed_changes),
            f"proposed_changes count is {len(proposal.proposed_changes)}.",
        ),
        _check(
            "missing_information_empty",
            not proposal.missing_information,
            f"missing_information count is {len(proposal.missing_information)}.",
        ),
        _check(
            "manual_review_required",
            proposal.manual_review_required is True,
            f"manual_review_required is {proposal.manual_review_required}.",
        ),
        _check(
            "proposal_risk_low_or_medium",
            proposal.risk_level in {"low", "medium"},
            f"proposal risk_level is {proposal.risk_level}.",
        ),
    ]


def _scope_checks(
    proposal: WriterDryRunProposal,
    *,
    expected_tc_ids: list[str] | None,
) -> list[WriterProposalReviewCheck]:
    affected = set(proposal.affected_test_case_ids)
    original_keys = set(proposal.original_tc_blocks)
    proposed_keys = set(proposal.proposed_tc_blocks)
    change_tcs = {str(change.get("test_case_id")) for change in proposal.proposed_changes}
    unlisted = sorted((original_keys | proposed_keys | change_tcs) - affected)
    missing = sorted(affected - (original_keys & proposed_keys))
    checks = [
        _check(
            "proposal_is_file_bound",
            bool(proposal.file_path),
            f"proposal file_path is {proposal.file_path or 'n/a'}.",
        ),
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
    if expected_tc_ids is not None:
        checks.append(_check(
            "affected_tc_ids_match_expected_scope",
            sorted(affected) == sorted(expected_tc_ids),
            "affected TC IDs match the expected package scope.",
            {"expected": expected_tc_ids, "actual": sorted(affected)},
        ))
    return checks


def _current_file_state_checks(
    *,
    proposal: WriterDryRunProposal,
    resolved_file: Path | None,
    current_blocks: dict[str, "_TcBlock"],
    current_traceability_lines: dict[str, str],
) -> list[WriterProposalReviewCheck]:
    checks = [
        _check(
            "current_file_exists",
            resolved_file is not None and resolved_file.exists(),
            f"current file exists: {resolved_file}",
        )
    ]
    stale: list[str] = []
    for tc_id, original_block in proposal.original_tc_blocks.items():
        current = current_blocks.get(tc_id)
        if current is None or current.text != original_block:
            stale.append(tc_id)
    checks.append(_check(
        "proposal_original_blocks_match_current_file",
        not stale,
        "proposal original TC blocks match current canonical file.",
        {"stale_or_missing_tc_ids": stale},
    ))

    missing_legacy: list[dict[str, Any]] = []
    missing_old_req: list[dict[str, Any]] = []
    for tc_id, original_block in proposal.original_tc_blocks.items():
        current_line = current_traceability_lines.get(tc_id, "")
        original_line = _single_traceability_line(original_block)
        for legacy_ref in _legacy_refs(original_line):
            if not _contains_ref(current_line, legacy_ref):
                missing_legacy.append({"test_case_id": tc_id, "legacy_ref": legacy_ref})
        for old_ref in _proposal_old_refs_for_tc(proposal, tc_id):
            if not _contains_ref(current_line, old_ref):
                missing_old_req.append({"test_case_id": tc_id, "old_ref": old_ref})
    checks.extend([
        _check(
            "current_traceability_contains_legacy_refs",
            not missing_legacy,
            "current traceability line contains legacy refs from proposal original block.",
            {"missing_legacy_refs": missing_legacy},
        ),
        _check(
            "current_traceability_contains_old_req_refs",
            not missing_old_req,
            "current traceability line contains old REQ refs required by proposal.",
            {"missing_old_req_refs": missing_old_req},
            blocked=True,
        ),
    ])
    return checks


def _line_safety_checks(proposal: WriterDryRunProposal) -> list[WriterProposalReviewCheck]:
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
        _check("no_steps_changed", not non_trace_changes, "no steps changed.", {"non_traceability_changes": non_trace_changes[:10]}),
        _check("no_expected_result_changed", not non_trace_changes, "no expected result changed.", {"non_traceability_changes": non_trace_changes[:10]}),
        _check("no_test_data_changed", not non_trace_changes, "no test data changed.", {"non_traceability_changes": non_trace_changes[:10]}),
        _check("no_headings_changed", not non_trace_changes, "no headings changed.", {"non_traceability_changes": non_trace_changes[:10]}),
        _check("no_package_metadata_changed", not non_trace_changes, "no package_id or metadata outside traceability changed.", {"non_traceability_changes": non_trace_changes[:10]}),
        _check(
            "listed_tc_blocks_have_changes",
            not unchanged_tcs,
            "all listed TC blocks have a proposed traceability change.",
            {"unchanged_tc_ids": unchanged_tcs},
            warning=True,
        ),
    ]


def _traceability_replacement_checks(proposal: WriterDryRunProposal) -> list[WriterProposalReviewCheck]:
    missing_old_before: list[dict[str, Any]] = []
    missing_new_after: list[dict[str, Any]] = []
    old_still_after: list[dict[str, Any]] = []
    missing_legacy: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for tc_id, original_block in proposal.original_tc_blocks.items():
        proposed_block = proposal.proposed_tc_blocks.get(tc_id, "")
        original_line = _single_traceability_line(original_block)
        proposed_line = _single_traceability_line(proposed_block)
        for change in _proposal_changes_for_tc(proposal, tc_id):
            old_ref = str(change.get("old_ref") or "")
            new_ref = str(change.get("new_ref") or "")
            if not _contains_ref(original_line, old_ref):
                missing_old_before.append({"test_case_id": tc_id, "old_ref": old_ref})
            if not _contains_ref(proposed_line, new_ref):
                missing_new_after.append({"test_case_id": tc_id, "new_ref": new_ref})
            if old_ref != new_ref and _contains_ref(proposed_line, old_ref):
                old_still_after.append({"test_case_id": tc_id, "old_ref": old_ref})
        proposed_refs = _req_refs(proposed_line)
        for ref, count in Counter(proposed_refs).items():
            if count > 1:
                duplicates.append({"test_case_id": tc_id, "req_uid": ref, "count": count})
        for legacy_ref in _legacy_refs(original_line):
            if not _contains_ref(proposed_line, legacy_ref):
                missing_legacy.append({"test_case_id": tc_id, "legacy_ref": legacy_ref})
    return [
        _check(
            "old_req_refs_present_before_replacement",
            not missing_old_before,
            "old REQ refs are present before replacement.",
            {"missing_old_refs": missing_old_before},
        ),
        _check(
            "new_req_refs_present_after_replacement",
            not missing_new_after,
            "new REQ refs are present after replacement.",
            {"missing_new_refs": missing_new_after},
        ),
        _check(
            "old_req_refs_removed_after_replacement",
            not old_still_after,
            "old REQ refs are removed from the proposed traceability line.",
            {"old_refs_still_present": old_still_after},
        ),
        _check(
            "legacy_refs_preserved",
            not missing_legacy,
            "legacy refs are preserved in the proposed traceability line.",
            {"missing_legacy_refs": missing_legacy},
        ),
        _check(
            "no_duplicate_req_refs_after_replacement",
            not duplicates,
            "proposed traceability line has no duplicate REQ refs.",
            {"duplicates": duplicates},
        ),
    ]


def _registry_checks(
    proposal: WriterDryRunProposal,
    old_registry_req_uids: set[str],
    new_registry_req_uids: set[str],
) -> list[WriterProposalReviewCheck]:
    missing: list[str] = []
    invalid: list[str] = []
    registry_hits: dict[str, str] = {}
    for req_uid in _proposal_old_new_refs(proposal):
        if not REQ_AUTOFIN_RE.fullmatch(req_uid):
            invalid.append(req_uid)
        in_old = req_uid in old_registry_req_uids
        in_new = req_uid in new_registry_req_uids
        if not in_old and not in_new:
            missing.append(req_uid)
        else:
            registry_hits[req_uid] = "old+new" if in_old and in_new else ("old" if in_old else "new")
    return [
        _check(
            "req_refs_have_valid_autofin_format",
            not invalid,
            "old/new REQ refs are valid REQ-AUTOFIN-* IDs.",
            {"invalid_req_uids": invalid},
        ),
        _check(
            "old_new_req_refs_exist_in_registry",
            not missing,
            "old/new REQ refs exist in old or new requirements registry.",
            {"missing_req_uids": missing, "registry_hits": registry_hits},
        ),
    ]


def _update_plan_checks(
    proposal: WriterDryRunProposal,
    update_plan: TestCaseUpdatePlan,
) -> list[WriterProposalReviewCheck]:
    plan_by_id = {item.plan_item_id: item for item in update_plan.plan_items}
    mismatches: list[dict[str, Any]] = []
    missing_items: list[str] = []
    mappings: list[dict[str, str]] = []
    for change in proposal.proposed_changes:
        plan_item_id = str(change.get("plan_item_id") or "")
        item = plan_by_id.get(plan_item_id)
        if item is None:
            missing_items.append(plan_item_id)
            continue
        old_ref = _normalize_ref(str(change.get("old_ref") or ""))
        new_ref = _normalize_ref(str(change.get("new_ref") or ""))
        pair_found = any(
            _normalize_ref(old) == old_ref and _normalize_ref(new) == new_ref
            for old, new in zip(item.old_refs, item.new_refs)
        )
        metadata_matches = (
            item.impact_id == change.get("impact_id")
            and item.change_id == change.get("change_id")
            and item.test_case_id == change.get("test_case_id")
            and item.action == "traceability_update_only"
        )
        mappings.append({"old_ref": old_ref, "new_ref": new_ref})
        if not pair_found or not metadata_matches:
            mismatches.append({
                "plan_item_id": plan_item_id,
                "old_ref": old_ref,
                "new_ref": new_ref,
                "pair_found": pair_found,
                "metadata_matches": metadata_matches,
            })
    return [_check(
        "update_plan_mapping_matches",
        not missing_items and not mismatches,
        "proposal old/new REQ mapping matches test-case update plan.",
        {
            "missing_plan_item_ids": missing_items,
            "mismatches": mismatches,
            "mappings": mappings,
        },
    )]


def _diff_consistency_checks(
    proposal: WriterDryRunProposal,
    current_text: str,
) -> list[WriterProposalReviewCheck]:
    if not current_text or not proposal.file_path:
        return [_failed("unified_diff_matches_structured_blocks", "current file text is unavailable.")]
    lines = current_text.splitlines(keepends=True)
    current_blocks = _single_tc_blocks(lines)
    proposed_lines = list(lines)
    missing_blocks: list[str] = []
    for tc_id, proposed_block in sorted(
        proposal.proposed_tc_blocks.items(),
        key=lambda item: current_blocks[item[0]].start if item[0] in current_blocks else -1,
        reverse=True,
    ):
        block = current_blocks.get(tc_id)
        if block is None:
            missing_blocks.append(tc_id)
            continue
        proposed_lines[block.start:block.end] = proposed_block.splitlines(keepends=True)
    expected = "".join(difflib.unified_diff(
        lines,
        proposed_lines,
        fromfile=f"a/{proposal.file_path}",
        tofile=f"b/{proposal.file_path}",
    ))
    ok = not missing_blocks and expected == proposal.unified_diff_preview
    return [_check(
        "unified_diff_matches_structured_blocks",
        ok,
        "unified diff preview matches structured original/proposed TC blocks.",
        {
            "missing_blocks": missing_blocks,
            "expected_length": len(expected),
            "actual_length": len(proposal.unified_diff_preview),
        },
    )]


def _git_state_check(git_state: dict[str, Any]) -> WriterProposalReviewCheck:
    ok = (
        bool(git_state)
        and git_state.get("status_short_returncode") == 0
        and git_state.get("diff_returncode") == 0
        and git_state.get("cached_diff_returncode") == 0
    )
    return _check(
        "git_state_recorded",
        ok,
        "git status/diff/cached-diff summary was recorded for the target file.",
        git_state,
        warning=True,
    )


def _report(
    *,
    package_id: str,
    checks: list[WriterProposalReviewCheck],
    warnings: list[str],
    blocking_reasons: list[str],
    input_paths: dict[str, Any],
    git_state: dict[str, Any],
    created_by_tool: str,
) -> WriterProposalReviewReport:
    warnings = _unique(warnings)
    blocked_checks = [check.check_id for check in checks if check.status == "blocked"]
    blocking_reasons = _unique([*blocking_reasons, *blocked_checks])
    failed_checks = [check.check_id for check in checks if check.status == "failed"]
    if blocking_reasons:
        review_status: ReviewStatus = "blocked"
    elif failed_checks:
        review_status = "rejected"
    elif warnings or any(check.status == "warning" for check in checks):
        review_status = "approved-with-warnings"
    else:
        review_status = "approved"
    return WriterProposalReviewReport(
        package_id=package_id,
        review_status=review_status,
        safe_for_controlled_apply=review_status in {"approved", "approved-with-warnings"},
        risk_level=_review_risk_level(review_status),
        checks=checks,
        failed_checks=failed_checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        reviewer_recommendation=_reviewer_recommendation(review_status),
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        git_state=git_state,
    )


def _review_risk_level(status: ReviewStatus) -> ReviewRiskLevel:
    if status in {"blocked", "rejected"}:
        return "high"
    if status == "approved-with-warnings":
        return "medium"
    return "low"


def _reviewer_recommendation(status: ReviewStatus) -> str:
    if status == "approved":
        return "safe for controlled traceability update apply; review found traceability-line-only replacement."
    if status == "approved-with-warnings":
        return "safe for controlled apply only after acknowledging warnings; replacement remains traceability-line-only."
    if status == "rejected":
        return "do not apply; fix failed checks and rebuild/review the writer proposal."
    return "review is blocked; current file or required artifacts are not in the expected state."


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


def _current_traceability_lines(current_blocks: dict[str, _TcBlock], tc_ids: list[str]) -> dict[str, str]:
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
    matcher = difflib.SequenceMatcher(None, original_lines, proposed_lines)
    changed: list[str] = []
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


def _single_traceability_line(block_text: str) -> str:
    lines = _traceability_lines(block_text)
    return lines[0] if len(lines) == 1 else ""


def _is_traceability_line(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(label) for label in TRACEABILITY_LABELS)


def _legacy_refs(line: str) -> list[str]:
    return _unique(match.group(0).upper().replace("  ", " ") for match in LEGACY_REF_RE.finditer(line))


def _req_refs(line: str) -> list[str]:
    return [match.group(0).upper() for match in REQ_UID_RE.finditer(line)]


def _proposal_changes_for_tc(proposal: WriterDryRunProposal, tc_id: str) -> list[dict[str, Any]]:
    return [change for change in proposal.proposed_changes if change.get("test_case_id") == tc_id]


def _proposal_old_refs_for_tc(proposal: WriterDryRunProposal, tc_id: str) -> list[str]:
    return _unique(
        _normalize_ref(str(change.get("old_ref") or ""))
        for change in _proposal_changes_for_tc(proposal, tc_id)
        if change.get("old_ref")
    )


def _proposal_old_new_refs(proposal: WriterDryRunProposal) -> list[str]:
    return _unique(
        _normalize_ref(str(value))
        for change in proposal.proposed_changes
        for value in (change.get("old_ref"), change.get("new_ref"))
        if value
    )


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
    return expected in {_normalize_ref(ref) for ref in [*_legacy_refs(line), *_req_refs(line)]}


def _collect_git_state(workspace_root: Path, target_file: Path) -> dict[str, Any]:
    try:
        rel_path = target_file.resolve().relative_to(workspace_root.resolve())
        git_path = str(rel_path).replace("\\", "/")
    except ValueError:
        git_path = str(target_file)
    status = _run_git(workspace_root, ["status", "--short", "--", git_path])
    diff = _run_git(workspace_root, ["diff", "--", git_path])
    cached = _run_git(workspace_root, ["diff", "--cached", "--", git_path])
    return {
        "target_file": git_path,
        "status_short": status["stdout"],
        "status_short_stderr": status["stderr"],
        "status_short_returncode": status["returncode"],
        "status_short_empty": status["stdout"] == "",
        "diff": diff["stdout"],
        "diff_stderr": diff["stderr"],
        "diff_returncode": diff["returncode"],
        "diff_empty": diff["stdout"] == "",
        "cached_diff": cached["stdout"],
        "cached_diff_stderr": cached["stderr"],
        "cached_diff_returncode": cached["returncode"],
        "cached_diff_empty": cached["stdout"] == "",
    }


def _run_git(workspace_root: Path, args: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=workspace_root,
            check=False,
            text=True,
            capture_output=True,
        )
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
) -> WriterProposalReviewCheck:
    if ok:
        status: CheckStatus = "pass"
    elif blocked:
        status = "blocked"
    elif warning:
        status = "warning"
    else:
        status = "failed"
    return WriterProposalReviewCheck(
        check_id=check_id,
        status=status,
        message=message,
        details=details or {},
    )


def _failed(check_id: str, message: str) -> WriterProposalReviewCheck:
    return WriterProposalReviewCheck(check_id=check_id, status="failed", message=message, details={})


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
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _artifact_suffix(value: str | None) -> str:
    if not value:
        return ""
    suffix = str(value).strip()
    if not suffix:
        return ""
    return suffix if suffix.startswith("-") else f"-{suffix}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
