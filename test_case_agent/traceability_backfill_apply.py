from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.traceability_backfill_proposals import (
    TraceabilityBackfillChange,
    TraceabilityBackfillProposal,
    load_traceability_backfill_proposal,
)
from test_case_agent.traceability_backfill_review import (
    TraceabilityBackfillReviewReport,
    load_traceability_backfill_review,
)
from test_case_agent.traceability_mismatch_diagnostics import LEGACY_REF_RE, REQ_UID_RE
from test_case_agent.writer_dry_run_proposals import TC_HEADING_RE, TRACEABILITY_LABELS, compute_file_sha256

CREATED_BY_TOOL = "test_case_agent.traceability_backfill_apply"
APPLY_PREFIX = "traceability-backfill-apply"

BackfillApplyStatus = Literal["previewed", "applied", "skipped", "blocked", "failed"]


@dataclass(frozen=True)
class TraceabilityBackfillApplyChange:
    repair_item_id: str
    test_case_id: str
    added_req_uids: list[str]
    old_traceability_line: str
    new_traceability_line: str
    status: Literal["previewed", "applied", "skipped"]
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repair_item_id": self.repair_item_id,
            "test_case_id": self.test_case_id,
            "added_req_uids": self.added_req_uids,
            "old_traceability_line": self.old_traceability_line,
            "new_traceability_line": self.new_traceability_line,
            "status": self.status,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityBackfillApplyChange":
        return cls(
            repair_item_id=str(data["repair_item_id"]),
            test_case_id=str(data["test_case_id"]),
            added_req_uids=list(data.get("added_req_uids") or []),
            old_traceability_line=str(data.get("old_traceability_line") or ""),
            new_traceability_line=str(data.get("new_traceability_line") or ""),
            status=data["status"],
            rationale=list(data.get("rationale") or []),
        )


@dataclass
class TraceabilityBackfillApplyReport:
    package_id: str
    apply_status: BackfillApplyStatus
    dry_run: bool
    file_path: str | None
    affected_test_case_ids: list[str]
    applied_changes: list[TraceabilityBackfillApplyChange]
    previewed_changes: list[TraceabilityBackfillApplyChange]
    skipped_changes: list[TraceabilityBackfillApplyChange]
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
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityBackfillApplyReport":
        return cls(
            package_id=str(data["package_id"]),
            apply_status=data["apply_status"],
            dry_run=bool(data["dry_run"]),
            file_path=data.get("file_path"),
            affected_test_case_ids=list(data.get("affected_test_case_ids") or []),
            applied_changes=[
                TraceabilityBackfillApplyChange.from_dict(item)
                for item in data.get("applied_changes", [])
            ],
            previewed_changes=[
                TraceabilityBackfillApplyChange.from_dict(item)
                for item in data.get("previewed_changes", [])
            ],
            skipped_changes=[
                TraceabilityBackfillApplyChange.from_dict(item)
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


def apply_traceability_backfill_proposal(
    *,
    package_id: str,
    backfill_proposal_path: Path,
    backfill_review_path: Path,
    test_cases_dir: Path,
    out_dir: Path,
    dry_run: bool = True,
    ack_warnings: bool = False,
    workspace_root: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> TraceabilityBackfillApplyReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    backfill_proposal_path = Path(backfill_proposal_path)
    backfill_review_path = Path(backfill_review_path)
    test_cases_dir = Path(test_cases_dir)
    out_dir = Path(out_dir)
    input_paths = {
        "backfill_proposal_path": str(backfill_proposal_path),
        "backfill_review_path": str(backfill_review_path),
        "test_cases_dir": str(test_cases_dir),
        "out_dir": str(out_dir),
    }

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    proposal: TraceabilityBackfillProposal | None = None
    review: TraceabilityBackfillReviewReport | None = None

    if not backfill_proposal_path.exists():
        blocking_reasons.append(f"traceability backfill proposal is missing: {backfill_proposal_path}")
    else:
        try:
            proposal = load_traceability_backfill_proposal(backfill_proposal_path)
            warnings.extend(proposal.warnings)
            blocking_reasons.extend(proposal.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"traceability backfill proposal cannot be parsed: {backfill_proposal_path}: {exc}")

    if not backfill_review_path.exists():
        blocking_reasons.append(f"traceability backfill review is missing: {backfill_review_path}")
    else:
        try:
            review = load_traceability_backfill_review(backfill_review_path)
            warnings.extend(review.warnings)
            blocking_reasons.extend(review.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"traceability backfill review cannot be parsed: {backfill_review_path}: {exc}")

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
    validation_reasons: list[str] = []
    if current_content and not blocking_reasons:
        proposed_content, validation_reasons = _build_proposed_content(
            current_content=current_content,
            proposal=proposal,
        )
        blocking_reasons.extend(validation_reasons)

    blocking_reasons = _unique(blocking_reasons)
    warnings = _unique(warnings)
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

    skipped_changes = [
        _apply_change_from_backfill(change, "skipped")
        for change in proposal.backfill_changes
        if change.status != "proposed"
    ]
    proposed_changes = [
        _apply_change_from_backfill(change, "previewed" if dry_run else "applied")
        for change in proposal.backfill_changes
        if change.status == "proposed"
    ]
    if not proposed_changes and not skipped_changes:
        return TraceabilityBackfillApplyReport(
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
        return TraceabilityBackfillApplyReport(
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
            return TraceabilityBackfillApplyReport(
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
        return TraceabilityBackfillApplyReport(
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
    except Exception as exc:  # noqa: BLE001 - controlled apply reports all write failures.
        if backup_path is not None and resolved_file.exists():
            try:
                _write_file_text(resolved_file, current_content)
            except Exception:  # noqa: BLE001 - original exception is the useful failure.
                pass
        after_sha = compute_file_sha256(resolved_file) if resolved_file.exists() else None
        return TraceabilityBackfillApplyReport(
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


def write_traceability_backfill_apply_report(
    report: TraceabilityBackfillApplyReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{APPLY_PREFIX}-{report.package_id}.json"
    markdown_path = out_dir / f"{APPLY_PREFIX}-{report.package_id}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_traceability_backfill_apply_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_traceability_backfill_apply_report(path: Path) -> TraceabilityBackfillApplyReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Traceability backfill apply report root must be a JSON object.")
    return TraceabilityBackfillApplyReport.from_dict(payload)


def render_traceability_backfill_apply_markdown(report: TraceabilityBackfillApplyReport) -> str:
    lines = [
        f"# Traceability Backfill Apply {report.package_id}",
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
    lines.append("- Structured proposal data is used; patch files are not applied.")
    lines.append("- Only listed TC blocks and traceability lines are eligible for change.")
    lines.append("- Real writes require explicit `--apply`; warning-approved reviews also require `--ack-warnings`.")
    return "\n".join(lines).rstrip() + "\n"


def _metadata_gate_reasons(
    proposal: TraceabilityBackfillProposal,
    review: TraceabilityBackfillReviewReport,
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
    proposal: TraceabilityBackfillProposal,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    lines = current_content.splitlines(keepends=True)
    block_index = _index_tc_blocks(lines)
    listed_blocks: dict[str, _TcBlock] = {}
    affected = set(proposal.affected_test_case_ids)
    if set(proposal.original_tc_blocks) != affected or set(proposal.proposed_tc_blocks) != affected:
        reasons.append("proposal original/proposed TC block keys must exactly match affected_test_case_ids.")
    change_tcs = {change.test_case_id for change in proposal.backfill_changes}
    if not change_tcs.issubset(affected):
        reasons.append("proposal backfill_changes contain TC IDs outside affected_test_case_ids.")
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
    old_legacy = set(_legacy_refs(original_trace[0])) if len(original_trace) == 1 else set()
    new_legacy = set(_legacy_refs(proposed_trace[0])) if len(proposed_trace) == 1 else set()
    if not old_legacy.issubset(new_legacy):
        reasons.append(f"TC {tc_id} does not preserve legacy refs.")
    new_req_counts = Counter(_req_uids(proposed_trace[0])) if len(proposed_trace) == 1 else Counter()
    duplicates = [req_uid for req_uid, count in new_req_counts.items() if count > 1]
    if duplicates:
        reasons.append(f"TC {tc_id} has duplicate REQ refs: {', '.join(sorted(duplicates))}")
    return reasons


def _change_safety_reasons(proposal: TraceabilityBackfillProposal) -> list[str]:
    reasons: list[str] = []
    for change in proposal.backfill_changes:
        if change.status == "blocked":
            reasons.append(f"backfill change is blocked: {change.repair_item_id}")
            continue
        if change.status != "proposed":
            continue
        for req_uid in change.added_req_uids:
            if req_uid not in _req_uids(change.new_traceability_line):
                reasons.append(f"added REQ uid missing from new traceability line: {change.repair_item_id} {req_uid}")
        old_legacy = set(_legacy_refs(change.old_traceability_line))
        new_legacy = set(_legacy_refs(change.new_traceability_line))
        if not old_legacy.issubset(new_legacy):
            reasons.append(f"change does not preserve legacy refs: {change.repair_item_id}")
    return reasons


def _post_apply_validation(
    *,
    before_content: str,
    after_content: str,
    proposal: TraceabilityBackfillProposal,
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
        end = headings[offset + 1][1] if offset + 1 < len(lines) and offset + 1 < len(headings) else len(lines)
        if offset + 1 < len(headings):
            end = headings[offset + 1][1]
        result.setdefault(tc_id, []).append(_TcBlock(tc_id=tc_id, start=start, end=end, text="".join(lines[start:end])))
    return result


def _traceability_lines(block_text: str) -> list[str]:
    return [
        line.strip()
        for line in block_text.splitlines()
        if _is_traceability_line(line)
    ]


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


def _apply_change_from_backfill(
    change: TraceabilityBackfillChange,
    status: Literal["previewed", "applied", "skipped"],
) -> TraceabilityBackfillApplyChange:
    return TraceabilityBackfillApplyChange(
        repair_item_id=change.repair_item_id,
        test_case_id=change.test_case_id,
        added_req_uids=change.added_req_uids,
        old_traceability_line=change.old_traceability_line,
        new_traceability_line=change.new_traceability_line,
        status=status,
        rationale=change.rationale,
    )


def _create_backup(
    *,
    target_file: Path,
    original_content: str,
    out_dir: Path,
    package_id: str,
) -> Path:
    backup_dir = out_dir / "backups" / f"traceability-backfill-{package_id}"
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
    proposal: TraceabilityBackfillProposal | None = None,
    sha256_before: str | None = None,
    sha256_after: str | None = None,
) -> TraceabilityBackfillApplyReport:
    return TraceabilityBackfillApplyReport(
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
    changes: list[TraceabilityBackfillApplyChange],
) -> None:
    lines.append(f"### {title}")
    lines.append("")
    if not changes:
        lines.append("- none")
        return
    for change in changes:
        lines.append(
            f"- `{change.test_case_id}` `{change.repair_item_id}` "
            f"REQ: `{', '.join(change.added_req_uids) or 'none'}`"
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
