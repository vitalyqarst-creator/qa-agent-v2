from __future__ import annotations

import json
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
    compute_file_sha256,
    load_writer_dry_run_proposal,
)
from test_case_agent.writer_proposal_review import (
    WriterProposalReviewReport,
    load_writer_proposal_review,
)

CREATED_BY_TOOL = "test_case_agent.writer_traceability_update_apply"
APPLY_PREFIX = "writer-traceability-update-apply"

WriterTraceabilityApplyStatus = Literal["previewed", "applied", "skipped", "blocked", "failed"]


@dataclass(frozen=True)
class WriterTraceabilityUpdateApplyChange:
    plan_item_id: str
    impact_id: str
    change_id: str
    test_case_id: str
    old_ref: str
    new_ref: str
    old_traceability_line: str
    new_traceability_line: str
    status: Literal["previewed", "applied", "skipped"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_item_id": self.plan_item_id,
            "impact_id": self.impact_id,
            "change_id": self.change_id,
            "test_case_id": self.test_case_id,
            "old_ref": self.old_ref,
            "new_ref": self.new_ref,
            "old_traceability_line": self.old_traceability_line,
            "new_traceability_line": self.new_traceability_line,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriterTraceabilityUpdateApplyChange":
        return cls(
            plan_item_id=str(data["plan_item_id"]),
            impact_id=str(data["impact_id"]),
            change_id=str(data["change_id"]),
            test_case_id=str(data["test_case_id"]),
            old_ref=str(data["old_ref"]),
            new_ref=str(data["new_ref"]),
            old_traceability_line=str(data.get("old_traceability_line") or ""),
            new_traceability_line=str(data.get("new_traceability_line") or ""),
            status=data["status"],
        )


@dataclass
class WriterTraceabilityUpdateApplyReport:
    package_id: str
    apply_status: WriterTraceabilityApplyStatus
    dry_run: bool
    file_path: str | None
    affected_test_case_ids: list[str]
    applied_changes: list[WriterTraceabilityUpdateApplyChange]
    previewed_changes: list[WriterTraceabilityUpdateApplyChange]
    skipped_changes: list[WriterTraceabilityUpdateApplyChange]
    backup_path: str | None
    sha256_before: str | None
    sha256_after: str | None
    files_changed_count: int
    input_paths: dict[str, Any]
    created_at_utc: str
    created_by_tool: str
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "apply_status": self.apply_status,
            "dry_run": self.dry_run,
            "file_path": self.file_path,
            "affected_test_case_ids": self.affected_test_case_ids,
            "applied_changes": [change.to_dict() for change in self.applied_changes],
            "previewed_changes": [change.to_dict() for change in self.previewed_changes],
            "skipped_changes": [change.to_dict() for change in self.skipped_changes],
            "backup_path": self.backup_path,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "files_changed_count": self.files_changed_count,
            "input_paths": self.input_paths,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriterTraceabilityUpdateApplyReport":
        return cls(
            package_id=str(data["package_id"]),
            apply_status=data["apply_status"],
            dry_run=bool(data["dry_run"]),
            file_path=data.get("file_path"),
            affected_test_case_ids=list(data.get("affected_test_case_ids") or []),
            applied_changes=[
                WriterTraceabilityUpdateApplyChange.from_dict(item)
                for item in data.get("applied_changes", [])
            ],
            previewed_changes=[
                WriterTraceabilityUpdateApplyChange.from_dict(item)
                for item in data.get("previewed_changes", [])
            ],
            skipped_changes=[
                WriterTraceabilityUpdateApplyChange.from_dict(item)
                for item in data.get("skipped_changes", [])
            ],
            backup_path=data.get("backup_path"),
            sha256_before=data.get("sha256_before"),
            sha256_after=data.get("sha256_after"),
            files_changed_count=int(data.get("files_changed_count") or 0),
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def apply_writer_traceability_update_proposal(
    *,
    package_id: str,
    writer_proposal_path: Path,
    writer_review_path: Path,
    test_cases_dir: Path,
    out_dir: Path,
    dry_run: bool = True,
    ack_warnings: bool = False,
    artifact_suffix: str | None = None,
    workspace_root: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> WriterTraceabilityUpdateApplyReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    writer_proposal_path = Path(writer_proposal_path)
    writer_review_path = Path(writer_review_path)
    test_cases_dir = Path(test_cases_dir)
    out_dir = Path(out_dir)
    input_paths = {
        "writer_proposal_path": str(writer_proposal_path),
        "writer_review_path": str(writer_review_path),
        "test_cases_dir": str(test_cases_dir),
        "out_dir": str(out_dir),
    }

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    proposal: WriterDryRunProposal | None = None
    review: WriterProposalReviewReport | None = None

    if not writer_proposal_path.exists():
        blocking_reasons.append(f"writer dry-run proposal is missing: {writer_proposal_path}")
    else:
        try:
            proposal = load_writer_dry_run_proposal(writer_proposal_path)
            warnings.extend(proposal.warnings)
            blocking_reasons.extend(proposal.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"writer dry-run proposal cannot be parsed: {writer_proposal_path}: {exc}")

    if not writer_review_path.exists():
        blocking_reasons.append(f"writer proposal review is missing: {writer_review_path}")
    else:
        try:
            review = load_writer_proposal_review(writer_review_path)
            warnings.extend(review.warnings)
            blocking_reasons.extend(review.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"writer proposal review cannot be parsed: {writer_review_path}: {exc}")

    if not test_cases_dir.exists() or not test_cases_dir.is_dir():
        blocking_reasons.append(f"test-cases dir is missing: {test_cases_dir}")

    if proposal is None or review is None or blocking_reasons:
        return _blocked_report(
            package_id=package_id,
            dry_run=dry_run,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
            proposal=proposal,
        )

    blocking_reasons.extend(_metadata_gate_reasons(proposal, review, package_id, dry_run, ack_warnings))
    file_path = proposal.file_path
    resolved_file: Path | None = None
    current_content = ""
    current_sha: str | None = None
    if file_path:
        resolved_file = _resolve_file(file_path, workspace_root)
        resolved_test_cases_dir = _resolve_file(test_cases_dir, workspace_root)
        if not _is_relative_to(resolved_file, resolved_test_cases_dir):
            blocking_reasons.append(f"target file is outside test-cases dir: {file_path}")
        elif not resolved_file.exists():
            blocking_reasons.append(f"target file is missing: {file_path}")
        else:
            current_content = resolved_file.read_text(encoding="utf-8")
            current_sha = compute_file_sha256(resolved_file)
            if proposal.sha256_before != current_sha:
                blocking_reasons.append(
                    "current file SHA differs from proposal sha256_before: "
                    f"{current_sha} != {proposal.sha256_before}"
                )
    else:
        blocking_reasons.append("proposal file_path is empty.")

    proposed_content = current_content
    if current_content and not blocking_reasons:
        proposed_content, validation_reasons = _build_proposed_content(
            current_content=current_content,
            proposal=proposal,
        )
        blocking_reasons.extend(validation_reasons)

    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    if blocking_reasons or resolved_file is None:
        return _blocked_report(
            package_id=package_id,
            dry_run=dry_run,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
            proposal=proposal,
            sha256_before=current_sha,
            sha256_after=current_sha,
        )

    preview_or_apply_status: Literal["previewed", "applied"] = "previewed" if dry_run else "applied"
    proposed_changes = [
        _apply_change_from_proposal(change, proposal, preview_or_apply_status)
        for change in proposal.proposed_changes
        if change.get("status", "proposed") == "proposed"
    ]
    skipped_changes = [
        _apply_change_from_proposal(change, proposal, "skipped")
        for change in proposal.proposed_changes
        if change.get("status", "proposed") != "proposed"
    ]
    if not proposed_changes and not skipped_changes:
        return WriterTraceabilityUpdateApplyReport(
            package_id=package_id,
            apply_status="skipped",
            dry_run=dry_run,
            file_path=file_path,
            affected_test_case_ids=proposal.affected_test_case_ids,
            applied_changes=[],
            previewed_changes=[],
            skipped_changes=[],
            backup_path=None,
            sha256_before=current_sha,
            sha256_after=current_sha,
            files_changed_count=0,
            input_paths=input_paths,
            created_at_utc=_utc_now_iso(),
            created_by_tool=created_by_tool,
            warnings=warnings,
            blocking_reasons=[],
        )

    if dry_run:
        return WriterTraceabilityUpdateApplyReport(
            package_id=package_id,
            apply_status="previewed",
            dry_run=True,
            file_path=file_path,
            affected_test_case_ids=proposal.affected_test_case_ids,
            applied_changes=[],
            previewed_changes=proposed_changes,
            skipped_changes=skipped_changes,
            backup_path=None,
            sha256_before=current_sha,
            sha256_after=compute_file_sha256(resolved_file),
            files_changed_count=0,
            input_paths=input_paths,
            created_at_utc=_utc_now_iso(),
            created_by_tool=created_by_tool,
            warnings=warnings,
            blocking_reasons=[],
        )

    backup_path: Path | None = None
    try:
        backup_path = _create_backup(
            target_file=resolved_file,
            original_content=current_content,
            out_dir=out_dir,
            package_id=package_id,
            artifact_suffix=artifact_suffix,
        )
        _write_file_text(resolved_file, proposed_content)
        after_sha = compute_file_sha256(resolved_file)
        post_reasons = _post_apply_validation(
            before_content=current_content,
            after_content=resolved_file.read_text(encoding="utf-8"),
            proposal=proposal,
        )
        if post_reasons:
            _write_file_text(resolved_file, current_content)
            restored_sha = compute_file_sha256(resolved_file)
            return WriterTraceabilityUpdateApplyReport(
                package_id=package_id,
                apply_status="failed",
                dry_run=False,
                file_path=file_path,
                affected_test_case_ids=proposal.affected_test_case_ids,
                applied_changes=[],
                previewed_changes=[],
                skipped_changes=skipped_changes,
                backup_path=str(backup_path),
                sha256_before=current_sha,
                sha256_after=restored_sha,
                files_changed_count=0 if restored_sha == current_sha else 1,
                input_paths=input_paths,
                created_at_utc=_utc_now_iso(),
                created_by_tool=created_by_tool,
                warnings=warnings,
                blocking_reasons=post_reasons,
            )
        return WriterTraceabilityUpdateApplyReport(
            package_id=package_id,
            apply_status="applied",
            dry_run=False,
            file_path=file_path,
            affected_test_case_ids=proposal.affected_test_case_ids,
            applied_changes=proposed_changes,
            previewed_changes=[],
            skipped_changes=skipped_changes,
            backup_path=str(backup_path),
            sha256_before=current_sha,
            sha256_after=after_sha,
            files_changed_count=1 if after_sha != current_sha else 0,
            input_paths=input_paths,
            created_at_utc=_utc_now_iso(),
            created_by_tool=created_by_tool,
            warnings=warnings,
            blocking_reasons=[],
        )
    except Exception as exc:  # noqa: BLE001
        if backup_path is not None and resolved_file.exists():
            try:
                _write_file_text(resolved_file, current_content)
            except Exception:  # noqa: BLE001
                pass
        after_sha = compute_file_sha256(resolved_file) if resolved_file.exists() else None
        return WriterTraceabilityUpdateApplyReport(
            package_id=package_id,
            apply_status="failed",
            dry_run=False,
            file_path=file_path,
            affected_test_case_ids=proposal.affected_test_case_ids,
            applied_changes=[],
            previewed_changes=[],
            skipped_changes=skipped_changes,
            backup_path=str(backup_path) if backup_path else None,
            sha256_before=current_sha,
            sha256_after=after_sha,
            files_changed_count=0 if after_sha == current_sha else 1,
            input_paths=input_paths,
            created_at_utc=_utc_now_iso(),
            created_by_tool=created_by_tool,
            warnings=warnings,
            blocking_reasons=[f"apply failed: {exc}"],
        )


def write_writer_traceability_update_apply_report(
    report: WriterTraceabilityUpdateApplyReport,
    out_dir: Path,
    *,
    artifact_suffix: str | None = None,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = _artifact_suffix(artifact_suffix)
    json_path = out_dir / f"{APPLY_PREFIX}-{report.package_id}{suffix}.json"
    markdown_path = out_dir / f"{APPLY_PREFIX}-{report.package_id}{suffix}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_writer_traceability_update_apply_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_writer_traceability_update_apply_report(path: Path) -> WriterTraceabilityUpdateApplyReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Writer traceability update apply report root must be a JSON object.")
    return WriterTraceabilityUpdateApplyReport.from_dict(payload)


def render_writer_traceability_update_apply_markdown(report: WriterTraceabilityUpdateApplyReport) -> str:
    lines = [
        f"# Writer Traceability Update Apply {report.package_id}",
        "",
        "## Summary",
        "",
        f"- Apply status: `{report.apply_status}`",
        f"- Dry run: `{str(report.dry_run).lower()}`",
        f"- File path: `{report.file_path or 'n/a'}`",
        f"- Affected TC IDs: `{', '.join(report.affected_test_case_ids) or 'n/a'}`",
        f"- Applied changes: `{len(report.applied_changes)}`",
        f"- Previewed changes: `{len(report.previewed_changes)}`",
        f"- Skipped changes: `{len(report.skipped_changes)}`",
        f"- Files changed count: `{report.files_changed_count}`",
        f"- Backup path: `{report.backup_path or 'n/a'}`",
        f"- SHA-256 before: `{report.sha256_before or 'n/a'}`",
        f"- SHA-256 after: `{report.sha256_after or 'n/a'}`",
        "",
        "## Changes",
        "",
    ]
    _append_changes(lines, "Applied", report.applied_changes)
    _append_changes(lines, "Previewed", report.previewed_changes)
    _append_changes(lines, "Skipped", report.skipped_changes)
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in report.warnings:
            lines.append(f"- {warning}")
    if report.blocking_reasons:
        lines.extend(["", "## Blocking Reasons", ""])
        for reason in report.blocking_reasons:
            lines.append(f"- {reason}")
    lines.extend(["", "## Safety", ""])
    lines.append("- Structured writer proposal data is used; patch files are not applied.")
    lines.append("- Only listed TC blocks and traceability lines are eligible for change.")
    lines.append("- Real writes require explicit `--apply`; warning-approved reviews also require `--ack-warnings`.")
    return "\n".join(lines).rstrip() + "\n"


def _metadata_gate_reasons(
    proposal: WriterDryRunProposal,
    review: WriterProposalReviewReport,
    package_id: str,
    dry_run: bool,
    ack_warnings: bool,
) -> list[str]:
    reasons: list[str] = []
    if proposal.package_id != package_id:
        reasons.append(f"proposal package_id mismatch: {proposal.package_id} != {package_id}")
    if review.package_id != package_id:
        reasons.append(f"review package_id mismatch: {review.package_id} != {package_id}")
    if not review.safe_for_controlled_apply:
        reasons.append("review.safe_for_controlled_apply is false.")
    if review.review_status not in {"approved", "approved-with-warnings"}:
        reasons.append(f"review_status is not approved: {review.review_status}")
    if review.failed_checks:
        reasons.append(f"review failed_checks is not empty: {', '.join(review.failed_checks)}")
    if proposal.proposal_status == "blocked":
        reasons.append("proposal.proposal_status is blocked.")
    if proposal.sha256_before != proposal.sha256_after:
        reasons.append("proposal sha256_before/sha256_after differ; proposal build did not prove canonical file stability.")
    if not dry_run and review.review_status == "approved-with-warnings" and not ack_warnings:
        reasons.append("review_status=approved-with-warnings requires --ack-warnings for real apply.")
    return reasons


@dataclass(frozen=True)
class _TcBlock:
    tc_id: str
    start: int
    end: int
    text: str


def _build_proposed_content(
    *,
    current_content: str,
    proposal: WriterDryRunProposal,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    lines = current_content.splitlines(keepends=True)
    block_index = _index_tc_blocks(lines)
    listed_blocks: dict[str, _TcBlock] = {}
    affected = set(proposal.affected_test_case_ids)
    if set(proposal.original_tc_blocks) != affected or set(proposal.proposed_tc_blocks) != affected:
        reasons.append("proposal original/proposed TC block keys must exactly match affected_test_case_ids.")
    change_tcs = {str(change.get("test_case_id")) for change in proposal.proposed_changes}
    if not change_tcs.issubset(affected):
        reasons.append("proposal proposed_changes contain TC IDs outside affected_test_case_ids.")
    for tc_id in proposal.affected_test_case_ids:
        matches = block_index.get(tc_id, [])
        if not matches:
            reasons.append(f"listed TC block not found: {tc_id}")
            continue
        if len(matches) > 1:
            reasons.append(f"duplicate TC block found: {tc_id}")
            continue
        current_block = matches[0]
        listed_blocks[tc_id] = current_block
        if proposal.original_tc_blocks.get(tc_id) != current_block.text:
            reasons.append(f"current TC block differs from proposal.original_tc_blocks: {tc_id}")
            continue
        proposed_block = proposal.proposed_tc_blocks.get(tc_id)
        if proposed_block is None:
            reasons.append(f"proposal.proposed_tc_blocks missing listed TC: {tc_id}")
            continue
        reasons.extend(_block_safety_reasons(tc_id, current_block.text, proposed_block))
    reasons.extend(_change_safety_reasons(proposal))
    if reasons:
        return current_content, _unique(reasons)
    proposed_lines = list(lines)
    for tc_id, block in sorted(listed_blocks.items(), key=lambda item: item[1].start, reverse=True):
        proposed_lines[block.start:block.end] = proposal.proposed_tc_blocks[tc_id].splitlines(keepends=True)
    return "".join(proposed_lines), []


def _block_safety_reasons(tc_id: str, original_block: str, proposed_block: str) -> list[str]:
    reasons: list[str] = []
    original_trace = _traceability_lines(original_block)
    proposed_trace = _traceability_lines(proposed_block)
    if len(original_trace) != 1 or len(proposed_trace) != 1:
        reasons.append(f"TC {tc_id} must have exactly one traceability line before and after.")
    non_trace_changes = [
        line
        for line in _changed_lines(original_block, proposed_block)
        if not _is_traceability_line(line)
    ]
    if non_trace_changes:
        reasons.append(f"TC {tc_id} changes non-traceability lines.")
    if len(original_trace) == 1 and len(proposed_trace) == 1:
        old_legacy = set(_legacy_refs(original_trace[0]))
        new_legacy = set(_legacy_refs(proposed_trace[0]))
        if not old_legacy.issubset(new_legacy):
            reasons.append(f"TC {tc_id} does not preserve legacy refs.")
        new_req_counts = Counter(_req_uids(proposed_trace[0]))
        duplicates = [req_uid for req_uid, count in new_req_counts.items() if count > 1]
        if duplicates:
            reasons.append(f"TC {tc_id} has duplicate REQ refs: {', '.join(sorted(duplicates))}")
    return reasons


def _change_safety_reasons(proposal: WriterDryRunProposal) -> list[str]:
    reasons: list[str] = []
    for change in proposal.proposed_changes:
        if change.get("status", "proposed") != "proposed":
            continue
        tc_id = str(change.get("test_case_id") or "")
        original_line = _single_traceability_line(proposal.original_tc_blocks.get(tc_id, ""))
        proposed_line = _single_traceability_line(proposal.proposed_tc_blocks.get(tc_id, ""))
        old_ref = str(change.get("old_ref") or "")
        new_ref = str(change.get("new_ref") or "")
        if not _contains_ref(original_line, old_ref):
            reasons.append(f"current traceability line for {tc_id} does not contain old ref: {old_ref}")
        if not _contains_ref(proposed_line, new_ref):
            reasons.append(f"proposed traceability line for {tc_id} does not contain new ref: {new_ref}")
        if old_ref != new_ref and _contains_ref(proposed_line, old_ref):
            reasons.append(f"proposed traceability line for {tc_id} still contains old ref: {old_ref}")
    return reasons


def _post_apply_validation(
    *,
    before_content: str,
    after_content: str,
    proposal: WriterDryRunProposal,
) -> list[str]:
    expected_content, reasons = _build_proposed_content(current_content=before_content, proposal=proposal)
    if reasons:
        return reasons
    if after_content != expected_content:
        return ["post-apply file content does not match structured proposal output."]
    return []


def _index_tc_blocks(lines: list[str]) -> dict[str, list[_TcBlock]]:
    headings: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line)
        if match:
            headings.append((match.group(2), index))
    result: dict[str, list[_TcBlock]] = {}
    for offset, (tc_id, start) in enumerate(headings):
        end = headings[offset + 1][1] if offset + 1 < len(headings) else len(lines)
        result.setdefault(tc_id, []).append(_TcBlock(tc_id=tc_id, start=start, end=end, text="".join(lines[start:end])))
    return result


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


def _legacy_refs(line: str) -> list[str]:
    return _unique(match.group(0).upper().replace("  ", " ") for match in LEGACY_REF_RE.finditer(line))


def _req_uids(line: str) -> list[str]:
    return [match.group(0).upper() for match in REQ_UID_RE.finditer(line)]


def _contains_ref(line: str, expected_ref: str | None) -> bool:
    if not expected_ref:
        return False
    expected = _normalize_ref(expected_ref)
    return expected in {_normalize_ref(ref) for ref in [*_legacy_refs(line), *_req_uids(line)]}


def _apply_change_from_proposal(
    change: dict[str, Any],
    proposal: WriterDryRunProposal,
    status: Literal["previewed", "applied", "skipped"],
) -> WriterTraceabilityUpdateApplyChange:
    tc_id = str(change.get("test_case_id") or "")
    return WriterTraceabilityUpdateApplyChange(
        plan_item_id=str(change.get("plan_item_id") or ""),
        impact_id=str(change.get("impact_id") or ""),
        change_id=str(change.get("change_id") or ""),
        test_case_id=tc_id,
        old_ref=str(change.get("old_ref") or ""),
        new_ref=str(change.get("new_ref") or ""),
        old_traceability_line=_single_traceability_line(proposal.original_tc_blocks.get(tc_id, "")),
        new_traceability_line=_single_traceability_line(proposal.proposed_tc_blocks.get(tc_id, "")),
        status=status,
    )


def _create_backup(
    *,
    target_file: Path,
    original_content: str,
    out_dir: Path,
    package_id: str,
    artifact_suffix: str | None,
) -> Path:
    backup_dir = out_dir / "backups" / f"writer-traceability-update-{package_id}{_artifact_suffix(artifact_suffix)}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{target_file.name}.bak"
    backup_path.write_text(original_content, encoding="utf-8", newline="\n")
    return backup_path


def _write_file_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _blocked_report(
    *,
    package_id: str,
    dry_run: bool,
    input_paths: dict[str, Any],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
    proposal: WriterDryRunProposal | None = None,
    sha256_before: str | None = None,
    sha256_after: str | None = None,
) -> WriterTraceabilityUpdateApplyReport:
    return WriterTraceabilityUpdateApplyReport(
        package_id=package_id,
        apply_status="blocked",
        dry_run=dry_run,
        file_path=proposal.file_path if proposal is not None else None,
        affected_test_case_ids=proposal.affected_test_case_ids if proposal is not None else [],
        applied_changes=[],
        previewed_changes=[],
        skipped_changes=[],
        backup_path=None,
        sha256_before=sha256_before,
        sha256_after=sha256_after,
        files_changed_count=0,
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        warnings=_unique(warnings),
        blocking_reasons=_unique(blocking_reasons),
    )


def _append_changes(
    lines: list[str],
    title: str,
    changes: list[WriterTraceabilityUpdateApplyChange],
) -> None:
    lines.append(f"### {title}")
    lines.append("")
    if not changes:
        lines.append("- none")
        return
    for change in changes:
        lines.append(
            f"- `{change.test_case_id}` `{change.plan_item_id}` "
            f"`{change.old_ref}` -> `{change.new_ref}`"
        )


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
