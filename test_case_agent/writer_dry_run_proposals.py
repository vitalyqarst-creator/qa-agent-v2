from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.test_case_update_plan import (
    TestCaseUpdatePlan,
    UpdatePlanItem,
    load_test_case_update_plan,
)
from test_case_agent.writer_package_tasks import (
    WriterPackageTask,
    WriterPackageTasksReport,
    load_writer_package_tasks,
)

CREATED_BY_TOOL = "test_case_agent.writer_dry_run_proposals"
PROPOSAL_PREFIX = "writer-dry-run-proposal"
DEFAULT_ALLOWED_PACKAGE_ID = "WPKG-000003"

ProposalStatus = Literal["pass", "pass-with-warnings", "blocked"]
RiskLevel = Literal["low", "medium", "high"]

TC_HEADING_RE = re.compile(r"^(#{2,6})\s+(TC-[A-Za-z0-9][A-Za-z0-9_-]*)\b")


@dataclass
class WriterDryRunProposal:
    package_id: str
    file_path: str | None
    affected_test_case_ids: list[str]
    source_plan_item_ids: list[str]
    source_impact_ids: list[str]
    source_change_ids: list[str]
    proposal_status: ProposalStatus
    risk_level: RiskLevel
    manual_review_required: bool
    proposed_changes: list[dict[str, Any]]
    rationale: list[str]
    missing_information: list[str]
    original_tc_blocks: dict[str, str]
    proposed_tc_blocks: dict[str, str]
    unified_diff_preview: str
    sha256_before: str | None
    sha256_after: str | None
    input_paths: dict[str, str | None]
    created_at_utc: str
    created_by_tool: str
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "file_path": self.file_path,
            "affected_test_case_ids": self.affected_test_case_ids,
            "source_plan_item_ids": self.source_plan_item_ids,
            "source_impact_ids": self.source_impact_ids,
            "source_change_ids": self.source_change_ids,
            "proposal_status": self.proposal_status,
            "risk_level": self.risk_level,
            "manual_review_required": self.manual_review_required,
            "proposed_changes": self.proposed_changes,
            "rationale": self.rationale,
            "missing_information": self.missing_information,
            "original_tc_blocks": self.original_tc_blocks,
            "proposed_tc_blocks": self.proposed_tc_blocks,
            "unified_diff_preview": self.unified_diff_preview,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "input_paths": self.input_paths,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriterDryRunProposal":
        return cls(
            package_id=str(data["package_id"]),
            file_path=data.get("file_path"),
            affected_test_case_ids=list(data.get("affected_test_case_ids") or []),
            source_plan_item_ids=list(data.get("source_plan_item_ids") or []),
            source_impact_ids=list(data.get("source_impact_ids") or []),
            source_change_ids=list(data.get("source_change_ids") or []),
            proposal_status=data["proposal_status"],
            risk_level=data["risk_level"],
            manual_review_required=bool(data["manual_review_required"]),
            proposed_changes=list(data.get("proposed_changes") or []),
            rationale=list(data.get("rationale") or []),
            missing_information=list(data.get("missing_information") or []),
            original_tc_blocks=dict(data.get("original_tc_blocks") or {}),
            proposed_tc_blocks=dict(data.get("proposed_tc_blocks") or {}),
            unified_diff_preview=str(data.get("unified_diff_preview") or ""),
            sha256_before=data.get("sha256_before"),
            sha256_after=data.get("sha256_after"),
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def build_writer_dry_run_proposal(
    *,
    package_id: str,
    writer_package_tasks_path: Path,
    test_cases_dir: Path,
    update_plan_path: Path | None = None,
    writer_package_task_path: Path | None = None,
    manual_update_packages_path: Path | None = None,
    impact_report_path: Path | None = None,
    requirements_diff_path: Path | None = None,
    workspace_root: Path | None = None,
    allowed_package_id: str = DEFAULT_ALLOWED_PACKAGE_ID,
    created_by_tool: str = CREATED_BY_TOOL,
) -> WriterDryRunProposal:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    writer_package_tasks_path = Path(writer_package_tasks_path)
    test_cases_dir = Path(test_cases_dir)
    optional_input_paths = {
        "writer_package_task_path": writer_package_task_path,
        "manual_update_packages_path": manual_update_packages_path,
        "impact_report_path": impact_report_path,
        "requirements_diff_path": requirements_diff_path,
        "update_plan_path": update_plan_path,
    }
    input_paths = _input_paths(
        writer_package_tasks_path=writer_package_tasks_path,
        test_cases_dir=test_cases_dir,
        **optional_input_paths,
    )

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    task_report: WriterPackageTasksReport | None = None
    task: WriterPackageTask | None = None
    update_plan: TestCaseUpdatePlan | None = None

    if package_id != allowed_package_id:
        blocking_reasons.append(
            f"package_id={package_id} is not allowed for this dry-run; expected {allowed_package_id}."
        )

    if not writer_package_tasks_path.exists():
        blocking_reasons.append(f"writer package tasks file is missing: {writer_package_tasks_path}")
    else:
        try:
            task_report = load_writer_package_tasks(writer_package_tasks_path)
        except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
            blocking_reasons.append(f"writer package tasks file cannot be parsed: {writer_package_tasks_path}: {exc}")

    for name, path in optional_input_paths.items():
        if path is not None and not Path(path).exists():
            blocking_reasons.append(f"{name} is missing: {path}")

    if task_report is not None:
        task = _find_task(task_report, package_id)
        if task is None:
            blocking_reasons.append(f"writer package task not found for package_id={package_id}.")
        else:
            warnings.extend(task.warnings)
            blocking_reasons.extend(_task_gate_reasons(task))

    if update_plan_path is not None and Path(update_plan_path).exists():
        try:
            update_plan = load_test_case_update_plan(Path(update_plan_path))
        except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
            blocking_reasons.append(f"test-case update plan cannot be parsed: {update_plan_path}: {exc}")

    if blocking_reasons or task is None:
        return _blocked_proposal(
            package_id=package_id,
            task=task,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    resolved_tc_file = _resolve_task_file(task.file_path, workspace_root)
    resolved_test_cases_dir = _resolve_task_file(str(test_cases_dir), workspace_root)
    if not _is_relative_to(resolved_tc_file, resolved_test_cases_dir):
        blocking_reasons.append(f"task file_path is outside test_cases_dir: {task.file_path}")
        return _blocked_proposal(
            package_id=package_id,
            task=task,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    if not resolved_tc_file.exists():
        blocking_reasons.append(f"task file_path is missing: {task.file_path}")
        return _blocked_proposal(
            package_id=package_id,
            task=task,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    sha_before = compute_file_sha256(resolved_tc_file)
    text = resolved_tc_file.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    block_index = _index_tc_blocks(lines)
    listed_blocks, block_reasons = _extract_listed_blocks(
        lines=lines,
        block_index=block_index,
        affected_test_case_ids=task.affected_test_case_ids,
    )
    if block_reasons:
        sha_after = compute_file_sha256(resolved_tc_file)
        return _blocked_proposal(
            package_id=package_id,
            task=task,
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(block_reasons),
            created_by_tool=created_by_tool,
            sha256_before=sha_before,
            sha256_after=sha_after,
            original_tc_blocks={tc_id: block.text for tc_id, block in listed_blocks.items()},
        )

    plan_items, missing_plan_items = _select_plan_items(update_plan, task.plan_item_ids)
    missing_information = list(missing_plan_items)
    proposed_blocks = {tc_id: block.text for tc_id, block in listed_blocks.items()}
    proposed_changes: list[dict[str, Any]] = []
    rationale = list(task.execution_notes)

    for item in plan_items:
        item_changes, item_missing = _propose_traceability_changes(item, proposed_blocks)
        proposed_changes.extend(item_changes)
        missing_information.extend(item_missing)
        rationale.extend(item.rationale)
        warnings.extend(item.warnings)

    proposed_file_lines = _replace_listed_blocks(lines, listed_blocks, proposed_blocks)
    unified_diff_preview = "".join(
        difflib.unified_diff(
            lines,
            proposed_file_lines,
            fromfile=f"a/{task.file_path}",
            tofile=f"b/{task.file_path}",
        )
    )
    sha_after = compute_file_sha256(resolved_tc_file)
    warnings = _unique(warnings)
    missing_information = _unique(missing_information)
    proposed_changes = _changes_for_listed_tcs(proposed_changes, task.affected_test_case_ids)
    proposal_status = _proposal_status(
        blocking_reasons=[],
        proposed_changes=proposed_changes,
        missing_information=missing_information,
        warnings=warnings,
    )
    risk_level = _risk_level(
        proposal_status=proposal_status,
        proposed_changes=proposed_changes,
        missing_information=missing_information,
    )
    return WriterDryRunProposal(
        package_id=package_id,
        file_path=task.file_path,
        affected_test_case_ids=task.affected_test_case_ids,
        source_plan_item_ids=task.plan_item_ids,
        source_impact_ids=task.impact_ids,
        source_change_ids=task.change_ids,
        proposal_status=proposal_status,
        risk_level=risk_level,
        manual_review_required=True,
        proposed_changes=proposed_changes,
        rationale=_unique(rationale),
        missing_information=missing_information,
        original_tc_blocks={tc_id: block.text for tc_id, block in listed_blocks.items()},
        proposed_tc_blocks=proposed_blocks,
        unified_diff_preview=unified_diff_preview,
        sha256_before=sha_before,
        sha256_after=sha_after,
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        warnings=warnings,
        blocking_reasons=[],
    )


def write_writer_dry_run_proposal(
    proposal: WriterDryRunProposal,
    out_dir: Path,
) -> tuple[Path, Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{PROPOSAL_PREFIX}-{proposal.package_id}.json"
    markdown_path = out_dir / f"{PROPOSAL_PREFIX}-{proposal.package_id}.md"
    patch_path = out_dir / f"{PROPOSAL_PREFIX}-{proposal.package_id}.patch"
    json_path.write_text(
        json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_writer_dry_run_proposal_markdown(proposal),
        encoding="utf-8",
        newline="\n",
    )
    patch_path.write_text(
        _patch_preview_text(proposal),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path, patch_path


def load_writer_dry_run_proposal(path: Path) -> WriterDryRunProposal:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Writer dry-run proposal root must be a JSON object.")
    return WriterDryRunProposal.from_dict(payload)


def render_writer_dry_run_proposal_markdown(proposal: WriterDryRunProposal) -> str:
    lines = [
        f"# Writer Dry-Run Proposal {proposal.package_id}",
        "",
        "## Summary",
        "",
        f"- Proposal status: `{proposal.proposal_status}`",
        f"- File path: `{proposal.file_path or 'n/a'}`",
        f"- Affected TC IDs: `{', '.join(proposal.affected_test_case_ids) or 'n/a'}`",
        f"- Proposed changes: `{len(proposal.proposed_changes)}`",
        f"- Risk level: `{proposal.risk_level}`",
        f"- Manual review required: `{str(proposal.manual_review_required).lower()}`",
        f"- SHA-256 before: `{proposal.sha256_before or 'n/a'}`",
        f"- SHA-256 after: `{proposal.sha256_after or 'n/a'}`",
        "",
        "## Proposed Changes",
        "",
    ]
    if proposal.proposed_changes:
        for change in proposal.proposed_changes:
            lines.append(
                "- "
                f"`{change.get('test_case_id')}` "
                f"`{change.get('plan_item_id')}` "
                f"{change.get('old_ref')} -> {change.get('new_ref')}"
            )
    else:
        lines.append("- none")
    if proposal.missing_information:
        lines.extend(["", "## Missing Information", ""])
        for item in proposal.missing_information:
            lines.append(f"- {item}")
    if proposal.blocking_reasons:
        lines.extend(["", "## Blocking Reasons", ""])
        for reason in proposal.blocking_reasons:
            lines.append(f"- {reason}")
    lines.extend(["", "## Rationale", ""])
    _append_list(lines, proposal.rationale)
    lines.extend(["", "## Original TC Blocks", ""])
    _append_blocks(lines, proposal.original_tc_blocks)
    lines.extend(["", "## Proposed TC Blocks", ""])
    _append_blocks(lines, proposal.proposed_tc_blocks)
    lines.extend(["", "## Unified Diff Preview", ""])
    if proposal.unified_diff_preview:
        lines.extend(["```diff", proposal.unified_diff_preview.rstrip(), "```"])
    else:
        lines.append("- none")
    lines.extend(["", "## Safety", ""])
    lines.append("- Preview only; patch is not applied.")
    lines.append("- Do not edit canonical test-case files in Stage 7C.")
    lines.append("- Do not create new test-case files in Stage 7C.")
    lines.append("- Do not run `--apply`.")
    return "\n".join(lines).rstrip() + "\n"


def compute_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class _TcBlock:
    tc_id: str
    start: int
    end: int
    text: str


def _find_task(report: WriterPackageTasksReport, package_id: str) -> WriterPackageTask | None:
    for task in report.tasks:
        if task.package_id == package_id:
            return task
    return None


def _task_gate_reasons(task: WriterPackageTask) -> list[str]:
    reasons: list[str] = []
    if task.file_path is None:
        reasons.append("writer task is unlinked; dry-run proposal supports only file-bound tasks.")
    if not task.affected_test_case_ids:
        reasons.append("writer task has no affected_test_case_ids.")
    if task.large_package:
        reasons.append("writer task is a large package; split before dry-run proposal.")
    if not task.safe_to_try_first:
        reasons.append("writer task is not marked safe_to_try_first.")
    if task.package_type == "create_new_candidate" or "create_new_candidate" in task.actions:
        reasons.append("writer task is create_new_candidate; canonical file proposal is not allowed.")
    return reasons


def _index_tc_blocks(lines: list[str]) -> dict[str, list[_TcBlock]]:
    headings: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line)
        if match:
            headings.append((match.group(2), index))
    result: dict[str, list[_TcBlock]] = {}
    for offset, (tc_id, start) in enumerate(headings):
        end = headings[offset + 1][1] if offset + 1 < len(headings) else len(lines)
        result.setdefault(tc_id, []).append(
            _TcBlock(
                tc_id=tc_id,
                start=start,
                end=end,
                text="".join(lines[start:end]),
            )
        )
    return result


def _extract_listed_blocks(
    *,
    lines: list[str],
    block_index: dict[str, list[_TcBlock]],
    affected_test_case_ids: list[str],
) -> tuple[dict[str, _TcBlock], list[str]]:
    del lines
    blocks: dict[str, _TcBlock] = {}
    reasons: list[str] = []
    for tc_id in affected_test_case_ids:
        matches = block_index.get(tc_id, [])
        if not matches:
            reasons.append(f"listed TC block not found: {tc_id}")
            continue
        if len(matches) > 1:
            reasons.append(f"duplicate listed TC block found: {tc_id}")
            continue
        blocks[tc_id] = matches[0]
    return blocks, reasons


def _select_plan_items(
    update_plan: TestCaseUpdatePlan | None,
    plan_item_ids: list[str],
) -> tuple[list[UpdatePlanItem], list[str]]:
    if update_plan is None:
        return [], ["test-case update plan is unavailable; cannot derive exact old/new refs."]
    by_id = {item.plan_item_id: item for item in update_plan.plan_items}
    items: list[UpdatePlanItem] = []
    missing: list[str] = []
    for plan_item_id in plan_item_ids:
        item = by_id.get(plan_item_id)
        if item is None:
            missing.append(f"plan item not found in update plan: {plan_item_id}")
        else:
            items.append(item)
    return items, missing


def _propose_traceability_changes(
    item: UpdatePlanItem,
    proposed_blocks: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    changes: list[dict[str, Any]] = []
    missing: list[str] = []
    if item.test_case_id is None or item.test_case_id not in proposed_blocks:
        missing.append(
            f"plan item {item.plan_item_id} targets TC outside listed blocks: {item.test_case_id or 'n/a'}"
        )
        return changes, missing
    if item.action != "traceability_update_only":
        missing.append(f"plan item {item.plan_item_id} action={item.action} is not traceability_update_only.")
        return changes, missing
    if len(item.old_refs) != len(item.new_refs):
        missing.append(f"plan item {item.plan_item_id} old_refs/new_refs length mismatch.")
        return changes, missing

    block = proposed_blocks[item.test_case_id]
    for old_ref, new_ref in zip(item.old_refs, item.new_refs):
        if old_ref == new_ref:
            continue
        if old_ref not in block:
            missing.append(
                f"plan item {item.plan_item_id}: old ref `{old_ref}` not found in {item.test_case_id}; "
                f"new ref `{new_ref}` was not inserted automatically."
            )
            continue
        block = block.replace(old_ref, new_ref)
        changes.append({
            "plan_item_id": item.plan_item_id,
            "impact_id": item.impact_id,
            "change_id": item.change_id,
            "test_case_id": item.test_case_id,
            "change_type": "traceability_ref_replace",
            "old_ref": old_ref,
            "new_ref": new_ref,
            "status": "proposed",
        })
    proposed_blocks[item.test_case_id] = block
    return changes, missing


def _replace_listed_blocks(
    lines: list[str],
    listed_blocks: dict[str, _TcBlock],
    proposed_blocks: dict[str, str],
) -> list[str]:
    result = list(lines)
    for tc_id, block in sorted(listed_blocks.items(), key=lambda item: item[1].start, reverse=True):
        result[block.start:block.end] = proposed_blocks[tc_id].splitlines(keepends=True)
    return result


def _changes_for_listed_tcs(
    changes: list[dict[str, Any]],
    affected_test_case_ids: list[str],
) -> list[dict[str, Any]]:
    allowed = set(affected_test_case_ids)
    return [change for change in changes if change.get("test_case_id") in allowed]


def _proposal_status(
    *,
    blocking_reasons: list[str],
    proposed_changes: list[dict[str, Any]],
    missing_information: list[str],
    warnings: list[str],
) -> ProposalStatus:
    if blocking_reasons:
        return "blocked"
    if missing_information or warnings or not proposed_changes:
        return "pass-with-warnings"
    return "pass"


def _risk_level(
    *,
    proposal_status: ProposalStatus,
    proposed_changes: list[dict[str, Any]],
    missing_information: list[str],
) -> RiskLevel:
    if proposal_status == "blocked":
        return "high"
    if missing_information:
        return "medium"
    if proposed_changes:
        return "low"
    return "medium"


def _blocked_proposal(
    *,
    package_id: str,
    task: WriterPackageTask | None,
    input_paths: dict[str, str | None],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
    sha256_before: str | None = None,
    sha256_after: str | None = None,
    original_tc_blocks: dict[str, str] | None = None,
) -> WriterDryRunProposal:
    return WriterDryRunProposal(
        package_id=package_id,
        file_path=task.file_path if task is not None else None,
        affected_test_case_ids=task.affected_test_case_ids if task is not None else [],
        source_plan_item_ids=task.plan_item_ids if task is not None else [],
        source_impact_ids=task.impact_ids if task is not None else [],
        source_change_ids=task.change_ids if task is not None else [],
        proposal_status="blocked",
        risk_level="high",
        manual_review_required=True,
        proposed_changes=[],
        rationale=[],
        missing_information=[],
        original_tc_blocks=original_tc_blocks or {},
        proposed_tc_blocks={},
        unified_diff_preview="",
        sha256_before=sha256_before,
        sha256_after=sha256_after,
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        warnings=_unique(warnings),
        blocking_reasons=_unique(blocking_reasons),
    )


def _patch_preview_text(proposal: WriterDryRunProposal) -> str:
    header = [
        f"# Preview-only patch for {proposal.package_id}.",
        "# This patch was not applied.",
    ]
    if proposal.unified_diff_preview:
        return "\n".join(header) + "\n" + proposal.unified_diff_preview
    return "\n".join([*header, "# No changes proposed."]) + "\n"


def _input_paths(
    *,
    writer_package_tasks_path: Path,
    test_cases_dir: Path,
    update_plan_path: Path | None,
    writer_package_task_path: Path | None,
    manual_update_packages_path: Path | None,
    impact_report_path: Path | None,
    requirements_diff_path: Path | None,
) -> dict[str, str | None]:
    return {
        "writer_package_tasks_path": str(writer_package_tasks_path),
        "writer_package_task_path": str(writer_package_task_path) if writer_package_task_path is not None else None,
        "manual_update_packages_path": str(manual_update_packages_path) if manual_update_packages_path is not None else None,
        "update_plan_path": str(update_plan_path) if update_plan_path is not None else None,
        "impact_report_path": str(impact_report_path) if impact_report_path is not None else None,
        "requirements_diff_path": str(requirements_diff_path) if requirements_diff_path is not None else None,
        "test_cases_dir": str(test_cases_dir),
    }


def _resolve_task_file(path: str | Path | None, workspace_root: Path) -> Path:
    if path is None:
        return workspace_root
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


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


def _append_blocks(lines: list[str], blocks: dict[str, str]) -> None:
    if not blocks:
        lines.append("- none")
        return
    for tc_id, block in blocks.items():
        lines.extend([f"### {tc_id}", "", "```markdown", block.rstrip(), "```", ""])


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
