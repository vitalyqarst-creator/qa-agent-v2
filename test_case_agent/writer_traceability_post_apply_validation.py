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

from test_case_agent.traceability_mismatch_diagnostics import LEGACY_REF_RE, REQ_UID_RE
from test_case_agent.writer_dry_run_proposals import (
    TC_HEADING_RE,
    TRACEABILITY_LABELS,
    WriterDryRunProposal,
    load_writer_dry_run_proposal,
)
from test_case_agent.writer_proposal_review import WriterProposalReviewReport, load_writer_proposal_review
from test_case_agent.writer_traceability_update_apply import (
    WriterTraceabilityUpdateApplyReport,
    load_writer_traceability_update_apply_report,
)

CREATED_BY_TOOL = "test_case_agent.writer_traceability_post_apply_validation"
VALIDATION_PREFIX = "writer-traceability-post-apply-validation"

ValidationStatus = Literal["pass", "pass-with-warnings", "failed", "blocked"]
CheckStatus = Literal["pass", "warning", "failed", "blocked"]


@dataclass(frozen=True)
class WriterTraceabilityPostApplyValidationCheck:
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
    def from_dict(cls, data: dict[str, Any]) -> "WriterTraceabilityPostApplyValidationCheck":
        return cls(
            check_id=str(data["check_id"]),
            status=data["status"],
            message=str(data["message"]),
            details=dict(data.get("details") or {}),
        )


@dataclass
class WriterTraceabilityPostApplyValidationReport:
    package_id: str
    validation_status: ValidationStatus
    safe_to_commit: bool
    file_path: str | None
    affected_test_case_ids: list[str]
    checks: list[WriterTraceabilityPostApplyValidationCheck]
    failed_checks: list[str]
    warnings: list[str]
    blocking_reasons: list[str]
    git_state: dict[str, Any]
    input_paths: dict[str, Any]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "validation_status": self.validation_status,
            "safe_to_commit": self.safe_to_commit,
            "file_path": self.file_path,
            "affected_test_case_ids": self.affected_test_case_ids,
            "checks": [check.to_dict() for check in self.checks],
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "git_state": self.git_state,
            "input_paths": self.input_paths,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriterTraceabilityPostApplyValidationReport":
        return cls(
            package_id=str(data["package_id"]),
            validation_status=data["validation_status"],
            safe_to_commit=bool(data["safe_to_commit"]),
            file_path=data.get("file_path"),
            affected_test_case_ids=list(data.get("affected_test_case_ids") or []),
            checks=[
                WriterTraceabilityPostApplyValidationCheck.from_dict(check)
                for check in data.get("checks", [])
            ],
            failed_checks=list(data.get("failed_checks") or []),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            git_state=dict(data.get("git_state") or {}),
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_writer_traceability_post_apply_validation(
    *,
    package_id: str,
    apply_report_path: Path,
    writer_proposal_path: Path,
    writer_review_path: Path,
    update_plan_path: Path,
    old_registry_path: Path,
    new_registry_path: Path,
    test_cases_dir: Path,
    workspace_root: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> WriterTraceabilityPostApplyValidationReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    apply_report_path = Path(apply_report_path)
    writer_proposal_path = Path(writer_proposal_path)
    writer_review_path = Path(writer_review_path)
    update_plan_path = Path(update_plan_path)
    old_registry_path = Path(old_registry_path)
    new_registry_path = Path(new_registry_path)
    test_cases_dir = Path(test_cases_dir)
    input_paths = {
        "apply_report_path": str(apply_report_path),
        "writer_proposal_path": str(writer_proposal_path),
        "writer_review_path": str(writer_review_path),
        "update_plan_path": str(update_plan_path),
        "old_registry_path": str(old_registry_path),
        "new_registry_path": str(new_registry_path),
        "test_cases_dir": str(test_cases_dir),
    }

    checks: list[WriterTraceabilityPostApplyValidationCheck] = []
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    apply_report: WriterTraceabilityUpdateApplyReport | None = None
    proposal: WriterDryRunProposal | None = None
    review: WriterProposalReviewReport | None = None
    old_registry_req_uids: set[str] = set()
    new_registry_req_uids: set[str] = set()

    for label, path in [
        ("writer traceability update apply report", apply_report_path),
        ("writer dry-run proposal", writer_proposal_path),
        ("writer proposal review", writer_review_path),
        ("test-case update plan", update_plan_path),
        ("old requirements registry", old_registry_path),
        ("new requirements registry", new_registry_path),
        ("test-cases dir", test_cases_dir),
    ]:
        if not Path(path).exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    if apply_report_path.exists():
        try:
            apply_report = load_writer_traceability_update_apply_report(apply_report_path)
            warnings.extend(apply_report.warnings)
            blocking_reasons.extend(apply_report.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"apply report cannot be parsed: {apply_report_path}: {exc}")

    if writer_proposal_path.exists():
        try:
            proposal = load_writer_dry_run_proposal(writer_proposal_path)
            warnings.extend(proposal.warnings)
            blocking_reasons.extend(proposal.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"writer proposal cannot be parsed: {writer_proposal_path}: {exc}")

    if writer_review_path.exists():
        try:
            review = load_writer_proposal_review(writer_review_path)
            warnings.extend(review.warnings)
            blocking_reasons.extend(review.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"writer proposal review cannot be parsed: {writer_review_path}: {exc}")

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

    file_path = apply_report.file_path if apply_report is not None else None
    affected_test_case_ids = apply_report.affected_test_case_ids if apply_report is not None else []
    resolved_file: Path | None = None
    current_text = ""
    backup_text = ""
    git_state: dict[str, Any] = {}
    if apply_report is not None and file_path:
        resolved_file = _resolve_file(file_path, workspace_root)
        resolved_test_cases_dir = _resolve_file(test_cases_dir, workspace_root)
        if not _is_relative_to(resolved_file, resolved_test_cases_dir):
            blocking_reasons.append(f"target file is outside test-cases dir: {file_path}")
        elif not resolved_file.exists():
            blocking_reasons.append(f"target file is missing: {file_path}")
        else:
            current_text = resolved_file.read_text(encoding="utf-8")
            git_state = _collect_git_state(workspace_root, resolved_test_cases_dir, resolved_file)
        if apply_report.backup_path:
            backup_path = _resolve_file(apply_report.backup_path, workspace_root)
            if backup_path.exists():
                backup_text = backup_path.read_text(encoding="utf-8")
    elif apply_report is not None:
        blocking_reasons.append("apply report file_path is empty.")

    if apply_report is None or proposal is None or review is None or blocking_reasons:
        return _report(
            package_id=package_id,
            file_path=file_path,
            affected_test_case_ids=affected_test_case_ids,
            checks=checks,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            git_state=git_state,
            input_paths=input_paths,
            created_by_tool=created_by_tool,
        )

    expected_file_path = proposal.file_path
    expected_tc_ids = proposal.affected_test_case_ids
    old_refs = _proposal_old_refs(proposal)
    new_refs = _proposal_new_refs(proposal)
    legacy_refs = _legacy_refs(_first_old_traceability_line(apply_report))
    if not legacy_refs:
        legacy_refs = _legacy_refs(_single_traceability_line(next(iter(proposal.original_tc_blocks.values()), "")))

    checks.extend(_apply_report_checks(apply_report, package_id))
    checks.extend(_scope_checks(
        apply_report=apply_report,
        expected_file_path=expected_file_path,
        expected_tc_ids=expected_tc_ids,
        git_state=git_state,
    ))
    checks.extend(_git_diff_checks(
        git_state=git_state,
        file_path=file_path or "",
        current_text=current_text,
        affected_tc_ids=affected_test_case_ids,
    ))
    checks.extend(_traceability_content_checks(
        current_text=current_text,
        affected_tc_ids=affected_test_case_ids,
        legacy_refs=legacy_refs,
        old_refs=old_refs,
        new_refs=new_refs,
    ))
    checks.extend(_registry_checks(
        old_refs=old_refs,
        new_refs=new_refs,
        old_registry_req_uids=old_registry_req_uids,
        new_registry_req_uids=new_registry_req_uids,
    ))
    checks.extend(_backup_checks(
        apply_report=apply_report,
        backup_text=backup_text,
        current_text=current_text,
        affected_tc_ids=affected_test_case_ids,
        old_refs=old_refs,
        new_refs=new_refs,
    ))

    return _report(
        package_id=package_id,
        file_path=file_path,
        affected_test_case_ids=affected_test_case_ids,
        checks=checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        git_state=git_state,
        input_paths=input_paths,
        created_by_tool=created_by_tool,
    )


def write_writer_traceability_post_apply_validation(
    report: WriterTraceabilityPostApplyValidationReport,
    out_dir: Path,
    *,
    artifact_suffix: str | None = None,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = _artifact_suffix(artifact_suffix)
    json_path = out_dir / f"{VALIDATION_PREFIX}-{report.package_id}{suffix}.json"
    markdown_path = out_dir / f"{VALIDATION_PREFIX}-{report.package_id}{suffix}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_writer_traceability_post_apply_validation_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_writer_traceability_post_apply_validation(path: Path) -> WriterTraceabilityPostApplyValidationReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Writer traceability post-apply validation root must be a JSON object.")
    return WriterTraceabilityPostApplyValidationReport.from_dict(payload)


def render_writer_traceability_post_apply_validation_markdown(
    report: WriterTraceabilityPostApplyValidationReport,
) -> str:
    lines = [
        f"# Writer Traceability Post-Apply Validation {report.package_id}",
        "",
        "## Summary",
        "",
        f"- Validation status: `{report.validation_status}`",
        f"- Safe to commit: `{str(report.safe_to_commit).lower()}`",
        f"- File path: `{report.file_path or 'n/a'}`",
        f"- Affected TC IDs: `{', '.join(report.affected_test_case_ids) or 'n/a'}`",
        f"- Failed checks: `{', '.join(report.failed_checks) or 'none'}`",
        f"- Warnings count: `{len(report.warnings)}`",
        f"- Blocking reasons count: `{len(report.blocking_reasons)}`",
        "",
        "## Git State",
        "",
        f"- Changed test-case files: `{len(report.git_state.get('changed_test_case_files', []))}`",
        f"- Staged changes empty: `{str(report.git_state.get('cached_diff_empty')).lower()}`",
        f"- Target diff hunks: `{report.git_state.get('target_diff_hunk_count', 0)}`",
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
    lines.append("- Validation is read-only.")
    lines.append("- No `--apply` is run.")
    lines.append("- No preview patch is applied.")
    return "\n".join(lines).rstrip() + "\n"


def _apply_report_checks(
    apply_report: WriterTraceabilityUpdateApplyReport,
    package_id: str,
) -> list[WriterTraceabilityPostApplyValidationCheck]:
    return [
        _check("apply_report_package_matches", apply_report.package_id == package_id, f"apply report package_id is {apply_report.package_id}."),
        _check("apply_status_applied", apply_report.apply_status == "applied", f"apply_status is {apply_report.apply_status}."),
        _check("apply_dry_run_false", apply_report.dry_run is False, f"dry_run is {apply_report.dry_run}."),
        _check("apply_blocking_reasons_empty", not apply_report.blocking_reasons, f"apply blocking reasons count is {len(apply_report.blocking_reasons)}."),
        _check("applied_changes_count_expected", len(apply_report.applied_changes) == 2, f"applied changes count is {len(apply_report.applied_changes)}.", {"expected": 2}),
        _check("files_changed_count_expected", apply_report.files_changed_count == 1, f"files_changed_count is {apply_report.files_changed_count}.", {"expected": 1}),
        _check("backup_path_present", bool(apply_report.backup_path), f"backup_path is {apply_report.backup_path or 'n/a'}."),
    ]


def _scope_checks(
    *,
    apply_report: WriterTraceabilityUpdateApplyReport,
    expected_file_path: str | None,
    expected_tc_ids: list[str],
    git_state: dict[str, Any],
) -> list[WriterTraceabilityPostApplyValidationCheck]:
    changed_files = list(git_state.get("changed_test_case_files") or [])
    expected_changed_file = str(git_state.get("target_file") or apply_report.file_path or "").replace("\\", "/")
    return [
        _check(
            "affected_file_expected",
            apply_report.file_path == expected_file_path,
            "affected file matches writer proposal.",
            {"expected": expected_file_path, "actual": apply_report.file_path},
        ),
        _check(
            "affected_tc_ids_expected",
            apply_report.affected_test_case_ids == expected_tc_ids,
            "affected TC IDs match writer proposal.",
            {"expected": expected_tc_ids, "actual": apply_report.affected_test_case_ids},
        ),
        _check(
            "only_expected_test_case_file_changed",
            changed_files == [expected_changed_file],
            "only expected test-case file has unstaged changes.",
            {"changed_test_case_files": changed_files},
        ),
        _check(
            "no_staged_changes",
            bool(git_state) and git_state.get("cached_diff_empty") is True,
            "no staged changes are present for test-cases.",
            {"cached_diff": git_state.get("cached_diff", "")},
        ),
    ]


def _git_diff_checks(
    *,
    git_state: dict[str, Any],
    file_path: str,
    current_text: str,
    affected_tc_ids: list[str],
) -> list[WriterTraceabilityPostApplyValidationCheck]:
    diff_text = str(git_state.get("target_diff") or "")
    changed_lines = _changed_lines_from_unified_diff(diff_text)
    changed_tcs = _changed_tcs_for_line_numbers(current_text, [line["new_lineno"] for line in changed_lines if line.get("new_lineno")])
    non_trace_changes = [line for line in changed_lines if not _is_traceability_line(str(line.get("text") or ""))]
    return [
        _check(
            "git_diff_has_one_hunk",
            int(git_state.get("target_diff_hunk_count") or 0) == 1,
            "target git diff contains exactly one changed hunk.",
            {"hunk_count": git_state.get("target_diff_hunk_count")},
        ),
        _check(
            "git_diff_changed_tc_expected",
            sorted(changed_tcs) == sorted(affected_tc_ids),
            "changed git diff lines are inside expected TC IDs.",
            {"changed_tc_ids": changed_tcs, "affected_test_case_ids": affected_tc_ids},
        ),
        _check(
            "git_diff_changes_only_traceability_line",
            bool(changed_lines) and not non_trace_changes,
            "git diff changes only traceability lines.",
            {"changed_lines": changed_lines, "non_trace_changes": non_trace_changes},
        ),
        _check(
            "git_diff_no_non_traceability_content_changed",
            not non_trace_changes,
            "no headings, steps, expected result, test data, or unrelated TC content changed.",
            {"file_path": file_path, "non_trace_changes": non_trace_changes},
        ),
    ]


def _traceability_content_checks(
    *,
    current_text: str,
    affected_tc_ids: list[str],
    legacy_refs: list[str],
    old_refs: list[str],
    new_refs: list[str],
) -> list[WriterTraceabilityPostApplyValidationCheck]:
    current_lines = _current_traceability_lines(current_text, affected_tc_ids)
    missing_legacy: list[dict[str, str]] = []
    missing_new: list[dict[str, str]] = []
    old_still_present: list[dict[str, str]] = []
    duplicates: list[dict[str, Any]] = []
    for tc_id in affected_tc_ids:
        line = current_lines.get(tc_id, "")
        for ref in legacy_refs:
            if not _contains_ref(line, ref):
                missing_legacy.append({"test_case_id": tc_id, "ref": ref})
        for ref in new_refs:
            if not _contains_ref(line, ref):
                missing_new.append({"test_case_id": tc_id, "ref": ref})
        for ref in old_refs:
            if _contains_ref(line, ref):
                old_still_present.append({"test_case_id": tc_id, "ref": ref})
        for req_uid, count in Counter(_req_uids(line)).items():
            if count > 1:
                duplicates.append({"test_case_id": tc_id, "req_uid": req_uid, "count": count})
    return [
        _check("current_traceability_legacy_refs_preserved", not missing_legacy, "current traceability line contains required legacy refs.", {"missing_legacy_refs": missing_legacy}),
        _check("current_traceability_new_req_refs_present", not missing_new, "current traceability line contains new REQ refs.", {"missing_new_refs": missing_new}),
        _check("current_traceability_old_req_refs_absent", not old_still_present, "current traceability line no longer contains old REQ refs.", {"old_refs_still_present": old_still_present}),
        _check("current_traceability_no_duplicate_req_refs", not duplicates, "current traceability line has no duplicate REQ refs.", {"duplicates": duplicates}),
    ]


def _registry_checks(
    *,
    old_refs: list[str],
    new_refs: list[str],
    old_registry_req_uids: set[str],
    new_registry_req_uids: set[str],
) -> list[WriterTraceabilityPostApplyValidationCheck]:
    missing_old = [ref for ref in old_refs if ref not in old_registry_req_uids and ref not in new_registry_req_uids]
    missing_new = [ref for ref in new_refs if ref not in old_registry_req_uids and ref not in new_registry_req_uids]
    return [
        _check("old_req_refs_exist_in_registry", not missing_old, "old REQ refs exist in old or new requirements registry.", {"missing_old_req_refs": missing_old}),
        _check("new_req_refs_exist_in_registry", not missing_new, "new REQ refs exist in old or new requirements registry.", {"missing_new_req_refs": missing_new}),
    ]


def _backup_checks(
    *,
    apply_report: WriterTraceabilityUpdateApplyReport,
    backup_text: str,
    current_text: str,
    affected_tc_ids: list[str],
    old_refs: list[str],
    new_refs: list[str],
) -> list[WriterTraceabilityPostApplyValidationCheck]:
    backup_exists = bool(apply_report.backup_path) and bool(backup_text)
    backup_lines = _current_traceability_lines(backup_text, affected_tc_ids)
    current_lines = _current_traceability_lines(current_text, affected_tc_ids)
    missing_old_in_backup: list[dict[str, str]] = []
    unexpected_new_in_backup: list[dict[str, str]] = []
    for tc_id in affected_tc_ids:
        line = backup_lines.get(tc_id, "")
        for ref in old_refs:
            if not _contains_ref(line, ref):
                missing_old_in_backup.append({"test_case_id": tc_id, "ref": ref})
        for ref in new_refs:
            if _contains_ref(line, ref):
                unexpected_new_in_backup.append({"test_case_id": tc_id, "ref": ref})
    backup_diff_lines = _changed_lines_between_texts(backup_text, current_text)
    non_trace_backup_changes = [line for line in backup_diff_lines if not _is_traceability_line(str(line.get("text") or ""))]
    backup_changed_tcs = _changed_tcs_for_line_numbers(current_text, [line["new_lineno"] for line in backup_diff_lines if line.get("new_lineno")])
    return [
        _check("backup_exists", backup_exists, f"backup exists: {apply_report.backup_path or 'n/a'}."),
        _check("backup_contains_old_traceability_refs", not missing_old_in_backup and not unexpected_new_in_backup, "backup contains old traceability line before replacement.", {"missing_old_refs": missing_old_in_backup, "unexpected_new_refs": unexpected_new_in_backup}),
        _check("backup_current_diff_only_expected_traceability_line", bool(backup_diff_lines) and not non_trace_backup_changes and sorted(backup_changed_tcs) == sorted(affected_tc_ids), "current file differs from backup only in the expected traceability line.", {"changed_tc_ids": backup_changed_tcs, "backup_diff_lines": backup_diff_lines, "non_trace_changes": non_trace_backup_changes, "current_traceability_lines": current_lines}),
    ]


def _report(
    *,
    package_id: str,
    file_path: str | None,
    affected_test_case_ids: list[str],
    checks: list[WriterTraceabilityPostApplyValidationCheck],
    warnings: list[str],
    blocking_reasons: list[str],
    git_state: dict[str, Any],
    input_paths: dict[str, Any],
    created_by_tool: str,
) -> WriterTraceabilityPostApplyValidationReport:
    warnings = _unique(warnings)
    blocked_checks = [check.check_id for check in checks if check.status == "blocked"]
    blocking_reasons = _unique([*blocking_reasons, *blocked_checks])
    failed_checks = [check.check_id for check in checks if check.status == "failed"]
    if blocking_reasons:
        validation_status: ValidationStatus = "blocked"
    elif failed_checks:
        validation_status = "failed"
    elif warnings or any(check.status == "warning" for check in checks):
        validation_status = "pass-with-warnings"
    else:
        validation_status = "pass"
    safe_to_commit = _safe_to_commit(
        validation_status=validation_status,
        failed_checks=failed_checks,
        blocking_reasons=blocking_reasons,
        git_state=git_state,
        file_path=file_path,
        checks=checks,
    )
    return WriterTraceabilityPostApplyValidationReport(
        package_id=package_id,
        validation_status=validation_status,
        safe_to_commit=safe_to_commit,
        file_path=file_path,
        affected_test_case_ids=affected_test_case_ids,
        checks=checks,
        failed_checks=failed_checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        git_state=git_state,
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _safe_to_commit(
    *,
    validation_status: ValidationStatus,
    failed_checks: list[str],
    blocking_reasons: list[str],
    git_state: dict[str, Any],
    file_path: str | None,
    checks: list[WriterTraceabilityPostApplyValidationCheck],
) -> bool:
    if validation_status not in {"pass", "pass-with-warnings"} or failed_checks or blocking_reasons:
        return False
    expected = str(file_path or "").replace("\\", "/")
    expected = str(git_state.get("target_file") or expected)
    changed_files = list(git_state.get("changed_test_case_files") or [])
    required_passes = {
        "only_expected_test_case_file_changed",
        "no_staged_changes",
        "git_diff_has_one_hunk",
        "git_diff_changed_tc_expected",
        "git_diff_changes_only_traceability_line",
        "backup_current_diff_only_expected_traceability_line",
    }
    statuses = {check.check_id: check.status for check in checks}
    return (
        changed_files == [expected]
        and git_state.get("cached_diff_empty") is True
        and all(statuses.get(check_id) == "pass" for check_id in required_passes)
    )


def _collect_git_state(workspace_root: Path, test_cases_dir: Path, target_file: Path) -> dict[str, Any]:
    target_git_path = _git_relative_path(workspace_root, target_file)
    test_cases_git_path = _git_relative_path(workspace_root, test_cases_dir)
    status = _run_git(workspace_root, ["status", "--short", "--", test_cases_git_path])
    target_diff = _run_git(workspace_root, ["diff", "--", target_git_path])
    cached_diff = _run_git(workspace_root, ["diff", "--cached", "--", test_cases_git_path])
    changed_files = _changed_files_from_status(status["stdout"])
    return {
        "target_file": target_git_path,
        "test_cases_dir": test_cases_git_path,
        "status_short": status["stdout"],
        "status_short_stderr": status["stderr"],
        "status_short_returncode": status["returncode"],
        "changed_test_case_files": changed_files,
        "target_diff": target_diff["stdout"],
        "target_diff_stderr": target_diff["stderr"],
        "target_diff_returncode": target_diff["returncode"],
        "target_diff_hunk_count": _hunk_count(target_diff["stdout"]),
        "cached_diff": cached_diff["stdout"],
        "cached_diff_stderr": cached_diff["stderr"],
        "cached_diff_returncode": cached_diff["returncode"],
        "cached_diff_empty": cached_diff["stdout"] == "",
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
        "stdout": completed.stdout.rstrip("\n"),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def _changed_files_from_status(status: str) -> list[str]:
    result: list[str] = []
    for line in status.splitlines():
        if not line.strip():
            continue
        value = line[3:] if len(line) > 3 else line.strip()
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        result.append(value.replace("\\", "/"))
    return result


def _hunk_count(diff_text: str) -> int:
    return sum(1 for line in diff_text.splitlines() if line.startswith("@@ "))


def _changed_lines_from_unified_diff(diff_text: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    old_lineno = 0
    new_lineno = 0
    hunk_re = re.compile(r"@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")
    for line in diff_text.splitlines():
        match = hunk_re.match(line)
        if match:
            old_lineno = int(match.group("old"))
            new_lineno = int(match.group("new"))
            continue
        if line.startswith(("diff --git", "index ", "--- ", "+++ ")) or not line:
            continue
        if line.startswith("-"):
            result.append({"side": "old", "old_lineno": old_lineno, "new_lineno": None, "text": line[1:]})
            old_lineno += 1
        elif line.startswith("+"):
            result.append({"side": "new", "old_lineno": None, "new_lineno": new_lineno, "text": line[1:]})
            new_lineno += 1
        elif line.startswith(" "):
            old_lineno += 1
            new_lineno += 1
    return result


def _changed_lines_between_texts(old_text: str, new_text: str) -> list[dict[str, Any]]:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    result: list[dict[str, Any]] = []
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        for offset, line in enumerate(old_lines[old_start:old_end], start=old_start + 1):
            result.append({"side": "old", "old_lineno": offset, "new_lineno": None, "text": line})
        for offset, line in enumerate(new_lines[new_start:new_end], start=new_start + 1):
            result.append({"side": "new", "old_lineno": None, "new_lineno": offset, "text": line})
    return result


def _changed_tcs_for_line_numbers(text: str, line_numbers: list[int]) -> list[str]:
    lines = text.splitlines()
    headings: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        match = TC_HEADING_RE.match(line)
        if match:
            headings.append((index, match.group(2)))
    result: list[str] = []
    for line_number in line_numbers:
        current: str | None = None
        for start, tc_id in headings:
            if start <= line_number:
                current = tc_id
            else:
                break
        if current and current not in result:
            result.append(current)
    return result


def _current_traceability_lines(text: str, tc_ids: list[str]) -> dict[str, str]:
    blocks = _single_tc_blocks(text.splitlines(keepends=True))
    result: dict[str, str] = {}
    for tc_id in tc_ids:
        line = _single_traceability_line(blocks.get(tc_id, _TcBlock(tc_id, 0, 0, "")).text)
        if line:
            result[tc_id] = line
    return result


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


def _single_traceability_line(block_text: str) -> str:
    lines = [
        line.strip()
        for line in block_text.splitlines()
        if _is_traceability_line(line)
    ]
    return lines[0] if len(lines) == 1 else ""


def _first_old_traceability_line(apply_report: WriterTraceabilityUpdateApplyReport) -> str:
    if apply_report.applied_changes:
        return apply_report.applied_changes[0].old_traceability_line
    return ""


def _proposal_old_refs(proposal: WriterDryRunProposal) -> list[str]:
    return _unique(_normalize_ref(change.get("old_ref")) for change in proposal.proposed_changes if change.get("old_ref"))


def _proposal_new_refs(proposal: WriterDryRunProposal) -> list[str]:
    return _unique(_normalize_ref(change.get("new_ref")) for change in proposal.proposed_changes if change.get("new_ref"))


def _is_traceability_line(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(label) for label in TRACEABILITY_LABELS)


def _legacy_refs(line: str) -> list[str]:
    return _unique(match.group(0).upper().replace("  ", " ") for match in LEGACY_REF_RE.finditer(line))


def _req_uids(line: str) -> list[str]:
    return [match.group(0).upper() for match in REQ_UID_RE.finditer(line)]


def _contains_ref(line: str, expected_ref: str | None) -> bool:
    if not expected_ref:
        return False
    expected = _normalize_ref(expected_ref)
    return expected in {_normalize_ref(ref) for ref in [*_legacy_refs(line), *_req_uids(line)]}


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


def _check(
    check_id: str,
    ok: bool,
    message: str,
    details: dict[str, Any] | None = None,
    *,
    warning: bool = False,
    blocked: bool = False,
) -> WriterTraceabilityPostApplyValidationCheck:
    if ok:
        status: CheckStatus = "pass"
    elif blocked:
        status = "blocked"
    elif warning:
        status = "warning"
    else:
        status = "failed"
    return WriterTraceabilityPostApplyValidationCheck(
        check_id=check_id,
        status=status,
        message=message,
        details=details or {},
    )


def _resolve_file(path: str | Path, workspace_root: Path) -> Path:
    value = Path(str(path).replace("\\", "/"))
    if value.is_absolute():
        return value.resolve()
    return (workspace_root / value).resolve()


def _git_relative_path(workspace_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace_root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _normalize_ref(ref: Any) -> str:
    return " ".join(str(ref).strip().upper().split())


def _artifact_suffix(value: str | None) -> str:
    if not value:
        return ""
    suffix = str(value).strip()
    if not suffix:
        return ""
    return suffix if suffix.startswith("-") else f"-{suffix}"


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
