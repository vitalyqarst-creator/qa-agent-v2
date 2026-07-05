from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.traceability_mismatch_diagnostics import (
    REQ_UID_RE,
    SOURCE_REQ_ID_RE,
    load_traceability_mismatch_diagnostics,
)
from test_case_agent.traceability_repair_strategy import (
    TraceabilityRepairItem,
    load_traceability_repair_strategy,
)
from test_case_agent.writer_dry_run_proposals import (
    TC_HEADING_RE,
    TRACEABILITY_LABELS,
    WriterDryRunProposal,
    compute_file_sha256,
    load_writer_dry_run_proposal,
)

CREATED_BY_TOOL = "test_case_agent.traceability_backfill_proposals"
BACKFILL_PREFIX = "traceability-backfill-proposal"

BackfillProposalStatus = Literal["pass", "pass-with-warnings", "blocked"]
BackfillRiskLevel = Literal["low", "medium", "high"]
BackfillChangeStatus = Literal["proposed", "skipped", "blocked"]


@dataclass(frozen=True)
class TraceabilityBackfillChange:
    repair_item_id: str
    test_case_id: str
    added_req_uids: list[str]
    supporting_source_req_ids: list[str]
    old_traceability_line: str
    new_traceability_line: str
    status: BackfillChangeStatus
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repair_item_id": self.repair_item_id,
            "test_case_id": self.test_case_id,
            "added_req_uids": self.added_req_uids,
            "supporting_source_req_ids": self.supporting_source_req_ids,
            "old_traceability_line": self.old_traceability_line,
            "new_traceability_line": self.new_traceability_line,
            "status": self.status,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityBackfillChange":
        return cls(
            repair_item_id=str(data["repair_item_id"]),
            test_case_id=str(data["test_case_id"]),
            added_req_uids=list(data.get("added_req_uids") or []),
            supporting_source_req_ids=list(data.get("supporting_source_req_ids") or []),
            old_traceability_line=str(data.get("old_traceability_line") or ""),
            new_traceability_line=str(data.get("new_traceability_line") or ""),
            status=data["status"],
            rationale=list(data.get("rationale") or []),
        )


@dataclass
class TraceabilityBackfillProposal:
    package_id: str
    proposal_status: BackfillProposalStatus
    file_path: str | None
    affected_test_case_ids: list[str]
    repair_item_ids: list[str]
    backfill_changes: list[TraceabilityBackfillChange]
    original_tc_blocks: dict[str, str]
    proposed_tc_blocks: dict[str, str]
    unified_diff_preview: str
    sha256_before: str | None
    sha256_after: str | None
    manual_review_required: bool
    risk_level: BackfillRiskLevel
    input_paths: dict[str, Any]
    created_at_utc: str
    created_by_tool: str
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "proposal_status": self.proposal_status,
            "file_path": self.file_path,
            "affected_test_case_ids": self.affected_test_case_ids,
            "repair_item_ids": self.repair_item_ids,
            "backfill_changes": [change.to_dict() for change in self.backfill_changes],
            "original_tc_blocks": self.original_tc_blocks,
            "proposed_tc_blocks": self.proposed_tc_blocks,
            "unified_diff_preview": self.unified_diff_preview,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "manual_review_required": self.manual_review_required,
            "risk_level": self.risk_level,
            "input_paths": self.input_paths,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityBackfillProposal":
        return cls(
            package_id=str(data["package_id"]),
            proposal_status=data["proposal_status"],
            file_path=data.get("file_path"),
            affected_test_case_ids=list(data.get("affected_test_case_ids") or []),
            repair_item_ids=list(data.get("repair_item_ids") or []),
            backfill_changes=[
                TraceabilityBackfillChange.from_dict(item)
                for item in data.get("backfill_changes", [])
            ],
            original_tc_blocks=dict(data.get("original_tc_blocks") or {}),
            proposed_tc_blocks=dict(data.get("proposed_tc_blocks") or {}),
            unified_diff_preview=str(data.get("unified_diff_preview") or ""),
            sha256_before=data.get("sha256_before"),
            sha256_after=data.get("sha256_after"),
            manual_review_required=bool(data["manual_review_required"]),
            risk_level=data["risk_level"],
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def build_traceability_backfill_proposal(
    *,
    package_id: str,
    repair_strategy_path: Path,
    diagnostics_path: Path,
    proposal_paths: list[Path],
    test_cases_dir: Path,
    workspace_root: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> TraceabilityBackfillProposal:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    repair_strategy_path = Path(repair_strategy_path)
    diagnostics_path = Path(diagnostics_path)
    proposal_paths = [Path(path) for path in proposal_paths]
    test_cases_dir = Path(test_cases_dir)
    input_paths = {
        "repair_strategy_path": str(repair_strategy_path),
        "diagnostics_path": str(diagnostics_path),
        "proposal_paths": [str(path) for path in proposal_paths],
        "test_cases_dir": str(test_cases_dir),
    }
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    repair_strategy = None
    writer_proposals: list[WriterDryRunProposal] = []

    if not repair_strategy_path.exists():
        blocking_reasons.append(f"traceability repair strategy is missing: {repair_strategy_path}")
    else:
        try:
            repair_strategy = load_traceability_repair_strategy(repair_strategy_path)
            warnings.extend(repair_strategy.warnings)
        except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
            blocking_reasons.append(f"traceability repair strategy cannot be parsed: {repair_strategy_path}: {exc}")

    if not diagnostics_path.exists():
        blocking_reasons.append(f"traceability mismatch diagnostics is missing: {diagnostics_path}")
    else:
        try:
            diagnostics = load_traceability_mismatch_diagnostics(diagnostics_path)
            warnings.extend(diagnostics.warnings)
            blocking_reasons.extend(diagnostics.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"traceability mismatch diagnostics cannot be parsed: {diagnostics_path}: {exc}")

    for path in proposal_paths:
        if not path.exists():
            blocking_reasons.append(f"writer dry-run proposal is missing: {path}")
            continue
        try:
            proposal = load_writer_dry_run_proposal(path)
            writer_proposals.append(proposal)
            warnings.extend(proposal.warnings)
            blocking_reasons.extend(proposal.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"writer dry-run proposal cannot be parsed: {path}: {exc}")

    if not test_cases_dir.exists():
        blocking_reasons.append(f"test-cases dir is missing: {test_cases_dir}")

    if blocking_reasons or repair_strategy is None:
        return _blocked_proposal(
            package_id=package_id,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
        )

    repair_items, item_reasons = _eligible_repair_items(repair_strategy.repair_items, package_id)
    warnings.extend(item_reasons)
    if not repair_items:
        blocking_reasons.append(f"no eligible repair items for package_id={package_id}.")
        return _blocked_proposal(
            package_id=package_id,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
        )

    writer_proposal = _writer_proposal_for_package(writer_proposals, package_id)
    if writer_proposal is None:
        blocking_reasons.append(f"writer dry-run proposal not found for package_id={package_id}.")
    else:
        blocking_reasons.extend(_writer_proposal_gate_reasons(writer_proposal, repair_items))

    file_paths = _unique(item.file_path for item in repair_items if item.file_path)
    if len(file_paths) != 1:
        blocking_reasons.append(
            f"backfill proposal supports exactly one target file per package; found {len(file_paths)}."
        )
    file_path = file_paths[0] if file_paths else None
    affected_test_case_ids = sorted({item.test_case_id for item in repair_items})
    if not all(affected_test_case_ids):
        blocking_reasons.append("all repair items must have concrete test_case_id.")

    if blocking_reasons or file_path is None:
        return _blocked_proposal(
            package_id=package_id,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
            file_path=file_path,
            affected_test_case_ids=affected_test_case_ids,
            repair_item_ids=[item.repair_item_id for item in repair_items],
        )

    resolved_tc_file = _resolve_file(file_path, workspace_root)
    resolved_test_cases_dir = _resolve_file(test_cases_dir, workspace_root)
    if not _is_relative_to(resolved_tc_file, resolved_test_cases_dir):
        blocking_reasons.append(f"target file is outside test-cases dir: {file_path}")
    if not resolved_tc_file.exists():
        blocking_reasons.append(f"target test-case file is missing: {file_path}")
    if blocking_reasons:
        return _blocked_proposal(
            package_id=package_id,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
            file_path=file_path,
            affected_test_case_ids=affected_test_case_ids,
            repair_item_ids=[item.repair_item_id for item in repair_items],
        )

    sha_before = compute_file_sha256(resolved_tc_file)
    original_text = resolved_tc_file.read_text(encoding="utf-8")
    original_lines = original_text.splitlines(keepends=True)
    block_index = _index_tc_blocks(original_lines)
    listed_blocks, block_reasons = _extract_listed_blocks(block_index, affected_test_case_ids)
    if block_reasons:
        sha_after = compute_file_sha256(resolved_tc_file)
        return _blocked_proposal(
            package_id=package_id,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=[*blocking_reasons, *block_reasons],
            created_by_tool=created_by_tool,
            file_path=file_path,
            affected_test_case_ids=affected_test_case_ids,
            repair_item_ids=[item.repair_item_id for item in repair_items],
            sha256_before=sha_before,
            sha256_after=sha_after,
            original_tc_blocks={tc_id: block.text for tc_id, block in listed_blocks.items()},
        )

    original_tc_blocks = {tc_id: block.text for tc_id, block in listed_blocks.items()}
    proposed_tc_blocks = dict(original_tc_blocks)
    changes: list[TraceabilityBackfillChange] = []
    items_by_tc = _items_by_test_case(repair_items)
    for tc_id in affected_test_case_ids:
        tc_changes, change_block, change_reasons = _propose_tc_backfill(items_by_tc[tc_id], proposed_tc_blocks[tc_id])
        changes.extend(tc_changes)
        if any(change.status == "blocked" for change in tc_changes):
            blocking_reasons.extend(change_reasons)
        elif any(change.status == "skipped" for change in tc_changes):
            warnings.extend(change_reasons)
        else:
            proposed_tc_blocks[tc_id] = change_block

    proposed_lines = _replace_listed_blocks(original_lines, listed_blocks, proposed_tc_blocks)
    unified_diff_preview = "".join(
        difflib.unified_diff(
            original_lines,
            proposed_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
    )
    sha_after = compute_file_sha256(resolved_tc_file)
    blocking_reasons = _unique(blocking_reasons)
    warnings = _unique(warnings)
    status = _proposal_status(blocking_reasons, changes, warnings)
    return TraceabilityBackfillProposal(
        package_id=package_id,
        proposal_status=status,
        file_path=file_path,
        affected_test_case_ids=affected_test_case_ids,
        repair_item_ids=[item.repair_item_id for item in repair_items],
        backfill_changes=changes,
        original_tc_blocks=original_tc_blocks,
        proposed_tc_blocks=proposed_tc_blocks,
        unified_diff_preview=unified_diff_preview,
        sha256_before=sha_before,
        sha256_after=sha_after,
        manual_review_required=True,
        risk_level=_risk_level(status, changes, warnings),
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def write_traceability_backfill_proposal(
    proposal: TraceabilityBackfillProposal,
    out_dir: Path,
) -> tuple[Path, Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{BACKFILL_PREFIX}-{proposal.package_id}.json"
    markdown_path = out_dir / f"{BACKFILL_PREFIX}-{proposal.package_id}.md"
    patch_path = out_dir / f"{BACKFILL_PREFIX}-{proposal.package_id}.patch"
    json_path.write_text(
        json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_traceability_backfill_proposal_markdown(proposal),
        encoding="utf-8",
        newline="\n",
    )
    patch_path.write_text(
        _patch_preview_text(proposal),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path, patch_path


def load_traceability_backfill_proposal(path: Path) -> TraceabilityBackfillProposal:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Traceability backfill proposal root must be a JSON object.")
    return TraceabilityBackfillProposal.from_dict(payload)


def render_traceability_backfill_proposal_markdown(proposal: TraceabilityBackfillProposal) -> str:
    lines = [
        f"# Traceability Backfill Proposal {proposal.package_id}",
        "",
        "## Summary",
        "",
        f"- Proposal status: `{proposal.proposal_status}`",
        f"- File path: `{proposal.file_path or 'n/a'}`",
        f"- Affected TC IDs: `{', '.join(proposal.affected_test_case_ids) or 'n/a'}`",
        f"- Backfill changes: `{len(proposal.backfill_changes)}`",
        f"- Proposed changes: `{sum(1 for change in proposal.backfill_changes if change.status == 'proposed')}`",
        f"- Risk level: `{proposal.risk_level}`",
        f"- Manual review required: `{str(proposal.manual_review_required).lower()}`",
        f"- SHA-256 before: `{proposal.sha256_before or 'n/a'}`",
        f"- SHA-256 after: `{proposal.sha256_after or 'n/a'}`",
        "",
        "## Backfill Changes",
        "",
    ]
    if not proposal.backfill_changes:
        lines.append("- none")
    for change in proposal.backfill_changes:
        lines.extend([
            f"### {change.repair_item_id} / {change.test_case_id}",
            "",
            f"- Status: `{change.status}`",
            f"- Added REQ UIDs: `{', '.join(change.added_req_uids) or 'none'}`",
            f"- Supporting source_req_ids: `{', '.join(change.supporting_source_req_ids) or 'none'}`",
            f"- Old traceability line: `{change.old_traceability_line}`",
            f"- New traceability line: `{change.new_traceability_line}`",
            "",
            "Rationale:",
        ])
        _append_list(lines, change.rationale)
        lines.append("")
    if proposal.warnings:
        lines.extend(["## Warnings", ""])
        _append_list(lines, proposal.warnings)
    if proposal.blocking_reasons:
        lines.extend(["## Blocking Reasons", ""])
        _append_list(lines, proposal.blocking_reasons)
    lines.extend(["## Unified Diff Preview", ""])
    if proposal.unified_diff_preview:
        lines.extend(["```diff", proposal.unified_diff_preview.rstrip(), "```"])
    else:
        lines.append("- none")
    lines.extend(["", "## Safety", ""])
    lines.append("- Preview only; canonical test-case files are not modified.")
    lines.append("- Legacy refs are preserved.")
    lines.append("- Patch file is not applied.")
    lines.append("- `--apply` is not used.")
    return "\n".join(lines).rstrip() + "\n"


def _eligible_repair_items(
    repair_items: list[TraceabilityRepairItem],
    package_id: str,
) -> tuple[list[TraceabilityRepairItem], list[str]]:
    selected: list[TraceabilityRepairItem] = []
    reasons: list[str] = []
    for item in repair_items:
        if item.package_id != package_id:
            continue
        item_reasons = _repair_item_gate_reasons(item)
        if item_reasons:
            reasons.extend(f"{item.repair_item_id}: {reason}" for reason in item_reasons)
            continue
        selected.append(item)
    return selected, reasons


def _repair_item_gate_reasons(item: TraceabilityRepairItem) -> list[str]:
    reasons: list[str] = []
    if item.allowed_next_action != "create_backfill_proposal":
        reasons.append(f"allowed_next_action={item.allowed_next_action} is not create_backfill_proposal.")
    if item.confidence not in {"high", "medium"}:
        reasons.append(f"confidence={item.confidence} is not high/medium.")
    if not item.requires_manual_validation:
        reasons.append("requires_manual_validation must be true.")
    if not item.candidate_req_uids_to_backfill:
        reasons.append("candidate_req_uids_to_backfill is empty.")
    if not item.file_path:
        reasons.append("file_path is empty.")
    if not item.test_case_id:
        reasons.append("test_case_id is empty.")
    return reasons


def _writer_proposal_for_package(
    proposals: list[WriterDryRunProposal],
    package_id: str,
) -> WriterDryRunProposal | None:
    for proposal in proposals:
        if proposal.package_id == package_id:
            return proposal
    return None


def _writer_proposal_gate_reasons(
    proposal: WriterDryRunProposal,
    repair_items: list[TraceabilityRepairItem],
) -> list[str]:
    reasons: list[str] = []
    if proposal.file_path is None:
        reasons.append(f"writer proposal {proposal.package_id} is unlinked.")
    else:
        proposal_file_path = _portable_path(proposal.file_path)
        for item in repair_items:
            if _portable_path(item.file_path) != proposal_file_path:
                reasons.append(
                    f"repair item {item.repair_item_id} targets file not used by writer proposal: {item.file_path}"
                )
    affected = set(proposal.affected_test_case_ids)
    for item in repair_items:
        if item.test_case_id not in affected:
            reasons.append(
                f"repair item {item.repair_item_id} targets TC not listed in writer proposal: {item.test_case_id}"
            )
    return reasons


@dataclass(frozen=True)
class _TcBlock:
    tc_id: str
    start: int
    end: int
    text: str


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


def _extract_listed_blocks(
    block_index: dict[str, list[_TcBlock]],
    affected_test_case_ids: list[str],
) -> tuple[dict[str, _TcBlock], list[str]]:
    result: dict[str, _TcBlock] = {}
    reasons: list[str] = []
    for tc_id in affected_test_case_ids:
        matches = block_index.get(tc_id, [])
        if not matches:
            reasons.append(f"listed TC block not found: {tc_id}")
            continue
        if len(matches) > 1:
            reasons.append(f"duplicate listed TC block found: {tc_id}")
            continue
        result[tc_id] = matches[0]
    return result, reasons


def _items_by_test_case(repair_items: list[TraceabilityRepairItem]) -> dict[str, list[TraceabilityRepairItem]]:
    result: dict[str, list[TraceabilityRepairItem]] = {}
    for item in repair_items:
        result.setdefault(item.test_case_id, []).append(item)
    return result


def _propose_tc_backfill(
    items: list[TraceabilityRepairItem],
    block_text: str,
) -> tuple[list[TraceabilityBackfillChange], str, list[str]]:
    test_case_id = items[0].test_case_id
    traceability_result = _find_single_traceability_line(block_text, test_case_id)
    if traceability_result["blocking_reasons"]:
        line = str(traceability_result.get("traceability_line") or "")
        reasons = list(traceability_result["blocking_reasons"])
        return (
            [
                _change(
                    item=item,
                    old_line=line,
                    new_line=line,
                    added_req_uids=[],
                    status="blocked",
                    rationale=reasons,
                )
                for item in items
            ],
            block_text,
            reasons,
        )

    block_lines = list(traceability_result["block_lines"])
    line_index = int(traceability_result["line_index"])
    old_line = block_lines[line_index]
    if not _has_recognizable_refs(old_line):
        reason = f"traceability line for {test_case_id} has no recognizable refs; REQ backfill was not added automatically."
        return (
            [
                _change(
                    item=item,
                    old_line=old_line.rstrip("\r\n"),
                    new_line=old_line.rstrip("\r\n"),
                    added_req_uids=[],
                    status="blocked",
                    rationale=[reason],
                )
                for item in items
            ],
            block_text,
            [reason],
        )

    existing_req_uids = {_normalize_ref(ref) for ref in REQ_UID_RE.findall(old_line)}
    all_added_req_uids = _unique([
        _normalize_ref(req_uid)
        for item in items
        for req_uid in item.candidate_req_uids_to_backfill
        if _normalize_ref(req_uid) not in existing_req_uids
    ])
    if not all_added_req_uids:
        reason = f"candidate REQ refs are already present in traceability line for {test_case_id}."
        return (
            [
                _change(
                    item=item,
                    old_line=old_line.rstrip("\r\n"),
                    new_line=old_line.rstrip("\r\n"),
                    added_req_uids=[],
                    status="skipped",
                    rationale=[reason],
                )
                for item in items
            ],
            block_text,
            [reason],
        )

    new_line = _append_req_uids(old_line, all_added_req_uids)
    block_lines[line_index] = new_line
    new_block = "".join(block_lines)
    changes: list[TraceabilityBackfillChange] = []
    for item in items:
        item_added = [
            _normalize_ref(req_uid)
            for req_uid in item.candidate_req_uids_to_backfill
            if _normalize_ref(req_uid) in set(all_added_req_uids)
        ]
        item_added = _unique(item_added)
        if item_added:
            changes.append(_change(
                item=item,
                old_line=old_line.rstrip("\r\n"),
                new_line=new_line.rstrip("\r\n"),
                added_req_uids=item_added,
                status="proposed",
                rationale=[
                    "missing generated REQ-* refs are appended at the end of the existing traceability line.",
                    "legacy refs are preserved.",
                    "proposal is preview-only and requires manual validation.",
                ],
            ))
        else:
            changes.append(_change(
                item=item,
                old_line=old_line.rstrip("\r\n"),
                new_line=new_line.rstrip("\r\n"),
                added_req_uids=[],
                status="skipped",
                rationale=[f"candidate REQ refs are already present in traceability line for {test_case_id}."],
            ))
    return (
        changes,
        new_block,
        [],
    )


def _find_single_traceability_line(block_text: str, test_case_id: str) -> dict[str, Any]:
    block_lines = block_text.splitlines(keepends=True)
    indexes = [
        index
        for index, line in enumerate(block_lines)
        if _is_traceability_line(line)
    ]
    if not indexes:
        return {
            "block_lines": block_lines,
            "line_index": -1,
            "traceability_line": "",
            "blocking_reasons": [f"traceability line not found in {test_case_id}"],
        }
    if len(indexes) > 1:
        return {
            "block_lines": block_lines,
            "line_index": -1,
            "traceability_line": block_lines[indexes[0]].rstrip("\r\n"),
            "blocking_reasons": [f"multiple traceability lines found in {test_case_id}; no backfill was proposed."],
        }
    return {
        "block_lines": block_lines,
        "line_index": indexes[0],
        "traceability_line": block_lines[indexes[0]],
        "blocking_reasons": [],
    }


def _is_traceability_line(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(label) for label in TRACEABILITY_LABELS)


def _has_recognizable_refs(line: str) -> bool:
    return bool(REQ_UID_RE.search(line) or SOURCE_REQ_ID_RE.search(line))


def _append_req_uids(line: str, req_uids: list[str]) -> str:
    newline = ""
    body = line
    if body.endswith("\r\n"):
        body = body[:-2]
        newline = "\r\n"
    elif body.endswith("\n"):
        body = body[:-1]
        newline = "\n"
    stripped = body.rstrip()
    trailing = body[len(stripped):]
    return f"{stripped}; REQ: {', '.join(req_uids)}{trailing}{newline}"


def _replace_listed_blocks(
    lines: list[str],
    listed_blocks: dict[str, _TcBlock],
    proposed_blocks: dict[str, str],
) -> list[str]:
    result = list(lines)
    for tc_id, block in sorted(listed_blocks.items(), key=lambda item: item[1].start, reverse=True):
        result[block.start:block.end] = proposed_blocks[tc_id].splitlines(keepends=True)
    return result


def _change(
    *,
    item: TraceabilityRepairItem,
    old_line: str,
    new_line: str,
    added_req_uids: list[str],
    status: BackfillChangeStatus,
    rationale: list[str],
) -> TraceabilityBackfillChange:
    return TraceabilityBackfillChange(
        repair_item_id=item.repair_item_id,
        test_case_id=item.test_case_id,
        added_req_uids=added_req_uids,
        supporting_source_req_ids=item.source_req_ids_supporting_candidate,
        old_traceability_line=old_line,
        new_traceability_line=new_line,
        status=status,
        rationale=rationale,
    )


def _proposal_status(
    blocking_reasons: list[str],
    changes: list[TraceabilityBackfillChange],
    warnings: list[str],
) -> BackfillProposalStatus:
    if blocking_reasons:
        return "blocked"
    if warnings or any(change.status == "skipped" for change in changes) or not any(
        change.status == "proposed" for change in changes
    ):
        return "pass-with-warnings"
    return "pass"


def _risk_level(
    status: BackfillProposalStatus,
    changes: list[TraceabilityBackfillChange],
    warnings: list[str],
) -> BackfillRiskLevel:
    if status == "blocked":
        return "high"
    if warnings or any(change.status == "skipped" for change in changes):
        return "medium"
    return "low"


def _blocked_proposal(
    *,
    package_id: str,
    input_paths: dict[str, Any],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
    file_path: str | None = None,
    affected_test_case_ids: list[str] | None = None,
    repair_item_ids: list[str] | None = None,
    sha256_before: str | None = None,
    sha256_after: str | None = None,
    original_tc_blocks: dict[str, str] | None = None,
) -> TraceabilityBackfillProposal:
    return TraceabilityBackfillProposal(
        package_id=package_id,
        proposal_status="blocked",
        file_path=file_path,
        affected_test_case_ids=affected_test_case_ids or [],
        repair_item_ids=repair_item_ids or [],
        backfill_changes=[],
        original_tc_blocks=original_tc_blocks or {},
        proposed_tc_blocks={},
        unified_diff_preview="",
        sha256_before=sha256_before,
        sha256_after=sha256_after,
        manual_review_required=True,
        risk_level="high",
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        warnings=_unique(warnings),
        blocking_reasons=_unique(blocking_reasons),
    )


def _patch_preview_text(proposal: TraceabilityBackfillProposal) -> str:
    header = [
        f"# Preview-only traceability backfill patch for {proposal.package_id}.",
        "# This patch was not applied.",
    ]
    if proposal.unified_diff_preview:
        return "\n".join(header) + "\n" + proposal.unified_diff_preview
    return "\n".join([*header, "# No changes proposed."]) + "\n"


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


def _portable_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").rstrip("/")


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


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
