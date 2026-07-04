from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.test_case_update_plan import (
    TestCaseUpdatePlan,
    UpdatePlanItem,
    load_test_case_update_plan,
)

CREATED_BY_TOOL = "test_case_agent.test_case_update_apply"
APPLY_PREFIX = "test-case-update-apply"
APPLY_SUMMARY_PREFIX = "test-case-update-apply-summary"

ApplyStatus = Literal[
    "previewed",
    "skipped_noop",
    "applied",
    "skipped_manual_only",
    "skipped_blocked",
    "skipped_unsafe",
    "failed",
]
ReportStatus = Literal["pass", "pass-with-warnings", "blocked"]

TC_HEADING_RE = re.compile(r"^(##|###)\s+(TC-[A-Za-z0-9_-]+)\b")
TRACEABILITY_LABELS = (
    "**Трассировка:**",
    "**РўСЂР°СЃСЃРёСЂРѕРІРєР°:**",
    "**Traceability:**",
)
REQUIRED_TRACEABILITY_CHANGE = ["update traceability refs only"]
TRACEABILITY_FORBIDDEN_CHANGES = {
    "Do not change steps",
    "Do not change expected result",
    "Do not change test data",
}


@dataclass(frozen=True)
class ApplyResultItem:
    apply_item_id: str
    plan_item_id: str
    impact_id: str
    change_id: str
    test_case_id: str | None
    file_path: str | None
    action: str
    apply_mode: str
    apply_status: ApplyStatus
    before_sha256: str | None
    after_sha256: str | None
    backup_path: str | None
    changed_lines: list[int]
    applied_changes: list[str]
    skipped_reason: str | None
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_item_id": self.apply_item_id,
            "plan_item_id": self.plan_item_id,
            "impact_id": self.impact_id,
            "change_id": self.change_id,
            "test_case_id": self.test_case_id,
            "file_path": self.file_path,
            "action": self.action,
            "apply_mode": self.apply_mode,
            "apply_status": self.apply_status,
            "before_sha256": self.before_sha256,
            "after_sha256": self.after_sha256,
            "backup_path": self.backup_path,
            "changed_lines": self.changed_lines,
            "applied_changes": self.applied_changes,
            "skipped_reason": self.skipped_reason,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApplyResultItem":
        return cls(
            apply_item_id=str(data["apply_item_id"]),
            plan_item_id=str(data["plan_item_id"]),
            impact_id=str(data["impact_id"]),
            change_id=str(data["change_id"]),
            test_case_id=data.get("test_case_id"),
            file_path=data.get("file_path"),
            action=str(data["action"]),
            apply_mode=str(data["apply_mode"]),
            apply_status=data["apply_status"],
            before_sha256=data.get("before_sha256"),
            after_sha256=data.get("after_sha256"),
            backup_path=data.get("backup_path"),
            changed_lines=list(data.get("changed_lines") or []),
            applied_changes=list(data.get("applied_changes") or []),
            skipped_reason=data.get("skipped_reason"),
            warnings=list(data.get("warnings") or []),
        )


@dataclass
class ApplyReport:
    ft_slug: str
    old_source_version: str
    new_source_version: str
    update_plan_path: str
    test_cases_dir: str
    created_at_utc: str
    created_by_tool: str
    dry_run: bool
    apply_items: list[ApplyResultItem]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ft_slug": self.ft_slug,
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "update_plan_path": self.update_plan_path,
            "test_cases_dir": self.test_cases_dir,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "dry_run": self.dry_run,
            "apply_items": [item.to_dict() for item in self.apply_items],
            "summary": self.summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApplyReport":
        return cls(
            ft_slug=str(data["ft_slug"]),
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            update_plan_path=str(data["update_plan_path"]),
            test_cases_dir=str(data["test_cases_dir"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            dry_run=bool(data["dry_run"]),
            apply_items=[
                ApplyResultItem.from_dict(item)
                for item in data.get("apply_items", [])
            ],
            summary=dict(data.get("summary") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


@dataclass
class _FileState:
    original_content: str
    current_content: str
    backup_path: Path | None = None


def apply_test_case_update_plan(
    *,
    update_plan_path: Path,
    test_cases_dir: Path,
    out_dir: Path,
    update_plan_summary_path: Path | None = None,
    backup_dir: Path | None = None,
    dry_run: bool = True,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ApplyReport:
    update_plan_path = Path(update_plan_path)
    test_cases_dir = Path(test_cases_dir)
    out_dir = Path(out_dir)
    backup_root = Path(backup_dir) if backup_dir is not None else out_dir / "backups"
    inferred_old, inferred_new = _infer_versions_from_plan_path(update_plan_path)

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    plan: TestCaseUpdatePlan | None = None

    if not update_plan_path.exists():
        blocking_reasons.append(f"update plan file is missing: {update_plan_path}")
    else:
        try:
            plan = load_test_case_update_plan(update_plan_path)
        except Exception as exc:  # noqa: BLE001 - controlled apply must report parse failures.
            blocking_reasons.append(f"update plan file cannot be parsed: {update_plan_path}: {exc}")

    if plan is not None:
        ft_slug = plan.ft_slug
        old_source_version = plan.old_source_version
        new_source_version = plan.new_source_version
        plan_items_total = len(plan.plan_items)
        warnings.extend(plan.warnings)
        warnings.extend(plan.summary.get("warnings") or [])
        if plan.summary.get("plan_status") == "blocked":
            blocking_reasons.append("update plan summary is blocked.")
        blocking_reasons.extend(plan.blocking_reasons)
    else:
        ft_slug = "unknown"
        old_source_version = inferred_old
        new_source_version = inferred_new
        plan_items_total = 0

    summary_path = (
        Path(update_plan_summary_path)
        if update_plan_summary_path is not None
        else _infer_plan_summary_path(update_plan_path, old_source_version, new_source_version)
    )
    plan_summary = _load_optional_summary(
        summary_path,
        explicit=update_plan_summary_path is not None,
        warnings=warnings,
    )
    if plan_summary and plan_summary.get("plan_status") == "blocked":
        blocking_reasons.append(f"update plan summary is blocked: {summary_path}")
        blocking_reasons.extend(str(reason) for reason in plan_summary.get("blocking_reasons") or [])

    if not test_cases_dir.exists() or not test_cases_dir.is_dir():
        blocking_reasons.append(f"test-cases dir is missing: {test_cases_dir}")

    if plan is not None:
        blocking_reasons.extend(_conflicting_safe_update_reasons(plan.plan_items, test_cases_dir))

    if blocking_reasons or plan is None:
        blocking_reasons = _unique(blocking_reasons)
        warnings = _unique(warnings)
        return _make_report(
            ft_slug=ft_slug,
            old_source_version=old_source_version,
            new_source_version=new_source_version,
            update_plan_path=update_plan_path,
            test_cases_dir=test_cases_dir,
            dry_run=dry_run,
            plan_items_total=plan_items_total,
            apply_items=[],
            files_changed=[],
            backups_created=[],
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
        )

    apply_items, file_states = _build_apply_preview(
        plan.plan_items,
        test_cases_dir=test_cases_dir,
        dry_run=dry_run,
    )

    files_changed: list[str] = []
    backups_created: list[str] = []
    if not dry_run:
        writable_paths = [
            path for path, state in file_states.items()
            if state.current_content != state.original_content
        ]
        try:
            backup_paths = _create_backups(
                writable_paths,
                file_states=file_states,
                test_cases_dir=test_cases_dir,
                backup_root=backup_root,
            )
        except Exception as exc:  # noqa: BLE001 - failed backup blocks all writes.
            blocking_reasons = [f"backup creation failed: {exc}"]
            warnings = _unique([*warnings, *_apply_item_warnings(apply_items)])
            return _make_report(
                ft_slug=ft_slug,
                old_source_version=old_source_version,
                new_source_version=new_source_version,
                update_plan_path=update_plan_path,
                test_cases_dir=test_cases_dir,
                dry_run=dry_run,
                plan_items_total=plan_items_total,
                apply_items=[],
                files_changed=[],
                backups_created=[],
                warnings=warnings,
                blocking_reasons=blocking_reasons,
                created_by_tool=created_by_tool,
            )
        backups_created = [str(path) for path in backup_paths.values()]
        apply_items = _attach_backup_paths(apply_items, backup_paths)
        apply_items, files_changed = _write_changed_files(apply_items, file_states)

    warnings = _unique([*warnings, *_apply_item_warnings(apply_items)])
    return _make_report(
        ft_slug=ft_slug,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        update_plan_path=update_plan_path,
        test_cases_dir=test_cases_dir,
        dry_run=dry_run,
        plan_items_total=plan_items_total,
        apply_items=apply_items,
        files_changed=files_changed,
        backups_created=backups_created,
        warnings=warnings,
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_test_case_update_apply_report(report: ApplyReport, out_dir: Path) -> tuple[Path, Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = _apply_path(out_dir, report.old_source_version, report.new_source_version)
    summary_path = _summary_path(out_dir, report.old_source_version, report.new_source_version)
    markdown_path = _markdown_path(out_dir, report.old_source_version, report.new_source_version)

    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary_path.write_text(
        json.dumps(report.summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_test_case_update_apply_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return report_path, summary_path, markdown_path


def load_test_case_update_apply_report(path: Path) -> ApplyReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Test case update apply report root must be a JSON object.")
    return ApplyReport.from_dict(payload)


def render_test_case_update_apply_markdown(report: ApplyReport) -> str:
    lines = [
        "# Test Case Update Apply Report",
        "",
        "## Summary",
        "",
        f"- FT slug: `{report.ft_slug}`",
        f"- Source versions: `{report.old_source_version}` -> `{report.new_source_version}`",
        f"- Apply status: `{report.summary['apply_status']}`",
        f"- Dry run: `{report.dry_run}`",
        f"- Apply items: `{report.summary['apply_items_total']}`",
        f"- Previewed: `{report.summary['previewed']}`",
        f"- Applied: `{report.summary['applied']}`",
        "",
        "## Previewed / Applied Changes",
        "",
    ]
    _append_apply_lines(
        lines,
        [item for item in report.apply_items if item.apply_status in {"previewed", "applied"}],
    )
    lines.extend(["", "## Skipped No-op", ""])
    _append_apply_lines(lines, [item for item in report.apply_items if item.apply_status == "skipped_noop"])
    lines.extend(["", "## Skipped Manual-only", ""])
    _append_apply_lines(lines, [item for item in report.apply_items if item.apply_status == "skipped_manual_only"])
    lines.extend(["", "## Skipped Unsafe", ""])
    _append_apply_lines(lines, [item for item in report.apply_items if item.apply_status == "skipped_unsafe"])
    lines.extend(["", "## Failed Items", ""])
    _append_apply_lines(lines, [item for item in report.apply_items if item.apply_status == "failed"])
    if report.blocking_reasons:
        for reason in report.blocking_reasons:
            lines.append(f"- apply blocked: {reason}")
    lines.extend(["", "## Files Changed", ""])
    if report.summary["files_changed"]:
        for file_path in report.summary["files_changed"]:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Backups", ""])
    if report.summary["backups_created"]:
        for backup_path in report.summary["backups_created"]:
            lines.append(f"- `{backup_path}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _build_apply_preview(
    plan_items: list[UpdatePlanItem],
    *,
    test_cases_dir: Path,
    dry_run: bool,
) -> tuple[list[ApplyResultItem], dict[Path, _FileState]]:
    apply_items: list[ApplyResultItem] = []
    file_states: dict[Path, _FileState] = {}

    for index, plan_item in enumerate(plan_items, start=1):
        apply_item_id = f"APPLY-{index:06d}"
        if plan_item.action == "keep":
            apply_items.append(_skip_noop_item(apply_item_id, plan_item, test_cases_dir, file_states))
            continue
        if plan_item.apply_mode == "blocked" or plan_item.action == "blocked":
            apply_items.append(
                _skipped_item(
                    apply_item_id,
                    plan_item,
                    "skipped_blocked",
                    "plan item is blocked",
                    test_cases_dir,
                    file_states,
                )
            )
            continue
        if plan_item.apply_mode == "manual_only":
            apply_items.append(
                _skipped_item(
                    apply_item_id,
                    plan_item,
                    "skipped_manual_only",
                    "plan item requires manual handling",
                    test_cases_dir,
                    file_states,
                )
            )
            continue
        safety_reason = _unsafe_reason(plan_item)
        if safety_reason is not None:
            apply_items.append(
                _skipped_item(
                    apply_item_id,
                    plan_item,
                    "skipped_unsafe",
                    safety_reason,
                    test_cases_dir,
                    file_states,
                    warnings=[safety_reason],
                )
            )
            continue
        apply_items.append(
            _preview_traceability_update(
                apply_item_id,
                plan_item,
                test_cases_dir=test_cases_dir,
                file_states=file_states,
                dry_run=dry_run,
            )
        )

    return apply_items, file_states


def _preview_traceability_update(
    apply_item_id: str,
    plan_item: UpdatePlanItem,
    *,
    test_cases_dir: Path,
    file_states: dict[Path, _FileState],
    dry_run: bool,
) -> ApplyResultItem:
    if plan_item.file_path is None or plan_item.test_case_id is None:
        return _skipped_item(
            apply_item_id,
            plan_item,
            "skipped_unsafe",
            "safe traceability update requires test_case_id and file_path",
            test_cases_dir,
            file_states,
            warnings=["safe traceability update requires test_case_id and file_path"],
        )
    file_path = _resolve_item_file_path(plan_item.file_path, test_cases_dir)
    if not file_path.exists() or not file_path.is_file():
        return _skipped_item(
            apply_item_id,
            plan_item,
            "skipped_unsafe",
            f"test-case file is missing: {file_path}",
            test_cases_dir,
            file_states,
            warnings=[f"test-case file is missing: {file_path}"],
        )

    state = _file_state(file_path, file_states)
    before_content = state.current_content
    before_sha = _sha256_text(before_content)
    patch = _patch_traceability_line(before_content, plan_item)
    if patch["status"] != "ok":
        warning = str(patch["reason"])
        return ApplyResultItem(
            apply_item_id=apply_item_id,
            plan_item_id=plan_item.plan_item_id,
            impact_id=plan_item.impact_id,
            change_id=plan_item.change_id,
            test_case_id=plan_item.test_case_id,
            file_path=str(file_path),
            action=plan_item.action,
            apply_mode=plan_item.apply_mode,
            apply_status="skipped_unsafe",
            before_sha256=before_sha,
            after_sha256=before_sha,
            backup_path=None,
            changed_lines=[],
            applied_changes=[],
            skipped_reason=warning,
            warnings=_unique([*plan_item.warnings, warning]),
        )

    after_content = str(patch["content"])
    after_sha = _sha256_text(after_content)
    if after_content == before_content:
        return ApplyResultItem(
            apply_item_id=apply_item_id,
            plan_item_id=plan_item.plan_item_id,
            impact_id=plan_item.impact_id,
            change_id=plan_item.change_id,
            test_case_id=plan_item.test_case_id,
            file_path=str(file_path),
            action=plan_item.action,
            apply_mode=plan_item.apply_mode,
            apply_status="skipped_noop",
            before_sha256=before_sha,
            after_sha256=after_sha,
            backup_path=None,
            changed_lines=[],
            applied_changes=[],
            skipped_reason="traceability refs already match",
            warnings=list(plan_item.warnings),
        )

    state.current_content = after_content
    return ApplyResultItem(
        apply_item_id=apply_item_id,
        plan_item_id=plan_item.plan_item_id,
        impact_id=plan_item.impact_id,
        change_id=plan_item.change_id,
        test_case_id=plan_item.test_case_id,
        file_path=str(file_path),
        action=plan_item.action,
        apply_mode=plan_item.apply_mode,
        apply_status="previewed" if dry_run else "applied",
        before_sha256=before_sha,
        after_sha256=after_sha,
        backup_path=None,
        changed_lines=list(patch["changed_lines"]),
        applied_changes=list(patch["applied_changes"]),
        skipped_reason=None,
        warnings=list(plan_item.warnings),
    )


def _patch_traceability_line(content: str, plan_item: UpdatePlanItem) -> dict[str, Any]:
    lines = content.splitlines(keepends=True)
    blocks = _find_test_case_blocks(lines, plan_item.test_case_id or "")
    if len(blocks) > 1:
        return {"status": "unsafe", "reason": f"multiple TC blocks found for {plan_item.test_case_id}"}
    if not blocks:
        return {"status": "unsafe", "reason": f"TC block not found: {plan_item.test_case_id}"}

    start, end = blocks[0]
    traceability_indexes = [
        index for index in range(start, end)
        if _is_traceability_line(lines[index])
    ]
    if len(traceability_indexes) != 1:
        return {
            "status": "unsafe",
            "reason": f"expected exactly one traceability line in {plan_item.test_case_id}, found {len(traceability_indexes)}",
        }

    line_index = traceability_indexes[0]
    original_line = lines[line_index]
    patched_line, applied_changes = _replace_refs(original_line, plan_item.old_refs, plan_item.new_refs)
    if not applied_changes:
        return {
            "status": "unsafe",
            "reason": "no old refs found in traceability line; refusing to append blindly",
        }
    if patched_line == original_line:
        return {
            "status": "ok",
            "content": content,
            "changed_lines": [],
            "applied_changes": [],
        }

    patched_lines = list(lines)
    patched_lines[line_index] = patched_line
    return {
        "status": "ok",
        "content": "".join(patched_lines),
        "changed_lines": [line_index + 1],
        "applied_changes": applied_changes,
    }


def _find_test_case_blocks(lines: list[str], test_case_id: str) -> list[tuple[int, int]]:
    heading_indexes: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line)
        if match:
            heading_indexes.append((index, match.group(2)))

    blocks: list[tuple[int, int]] = []
    for index, (start, current_id) in enumerate(heading_indexes):
        if current_id != test_case_id:
            continue
        end = heading_indexes[index + 1][0] if index + 1 < len(heading_indexes) else len(lines)
        blocks.append((start, end))
    return blocks


def _is_traceability_line(line: str) -> bool:
    return any(line.startswith(label) for label in TRACEABILITY_LABELS)


def _replace_refs(line: str, old_refs: list[str], new_refs: list[str]) -> tuple[str, list[str]]:
    patched = line
    applied_changes: list[str] = []
    for old_ref, new_ref in zip(old_refs, new_refs):
        if not old_ref or not new_ref:
            continue
        patched, replacements = _replace_ref(patched, old_ref, new_ref)
        if replacements:
            applied_changes.append(f"replace `{old_ref}` -> `{new_ref}`")
    return patched, applied_changes


def _replace_ref(line: str, old_ref: str, new_ref: str) -> tuple[str, int]:
    pattern = re.compile(
        rf"(?<![A-Za-zА-Яа-я0-9_-]){re.escape(old_ref)}(?![A-Za-zА-Яа-я0-9_-])"
    )
    return pattern.subn(new_ref, line)


def _unsafe_reason(plan_item: UpdatePlanItem) -> str | None:
    if plan_item.action != "traceability_update_only":
        return f"unsafe action for controlled apply: {plan_item.action}"
    if plan_item.apply_mode != "safe_auto_candidate":
        return f"unsafe apply_mode for controlled apply: {plan_item.apply_mode}"
    if plan_item.warnings:
        return "safe traceability item has warnings"
    if plan_item.test_case_id is None or plan_item.file_path is None:
        return "safe traceability item is missing test_case_id or file_path"
    if plan_item.required_changes != REQUIRED_TRACEABILITY_CHANGE:
        return "safe traceability item has unexpected required_changes"
    if not TRACEABILITY_FORBIDDEN_CHANGES.issubset(set(plan_item.forbidden_changes)):
        return "safe traceability item is missing required forbidden_changes guardrails"
    return None


def _skip_noop_item(
    apply_item_id: str,
    plan_item: UpdatePlanItem,
    test_cases_dir: Path,
    file_states: dict[Path, _FileState],
) -> ApplyResultItem:
    before_sha = None
    resolved_path = None
    if plan_item.file_path:
        resolved_path = _resolve_item_file_path(plan_item.file_path, test_cases_dir)
        if resolved_path.exists() and resolved_path.is_file():
            before_sha = _sha256_text(_file_state(resolved_path, file_states).current_content)
    return ApplyResultItem(
        apply_item_id=apply_item_id,
        plan_item_id=plan_item.plan_item_id,
        impact_id=plan_item.impact_id,
        change_id=plan_item.change_id,
        test_case_id=plan_item.test_case_id,
        file_path=str(resolved_path) if resolved_path is not None else plan_item.file_path,
        action=plan_item.action,
        apply_mode=plan_item.apply_mode,
        apply_status="skipped_noop",
        before_sha256=before_sha,
        after_sha256=before_sha,
        backup_path=None,
        changed_lines=[],
        applied_changes=[],
        skipped_reason="keep/no-op item",
        warnings=list(plan_item.warnings),
    )


def _skipped_item(
    apply_item_id: str,
    plan_item: UpdatePlanItem,
    apply_status: ApplyStatus,
    skipped_reason: str,
    test_cases_dir: Path,
    file_states: dict[Path, _FileState],
    *,
    warnings: list[str] | None = None,
) -> ApplyResultItem:
    before_sha = None
    resolved_path = None
    if plan_item.file_path:
        resolved_path = _resolve_item_file_path(plan_item.file_path, test_cases_dir)
        if resolved_path.exists() and resolved_path.is_file():
            before_sha = _sha256_text(_file_state(resolved_path, file_states).current_content)
    return ApplyResultItem(
        apply_item_id=apply_item_id,
        plan_item_id=plan_item.plan_item_id,
        impact_id=plan_item.impact_id,
        change_id=plan_item.change_id,
        test_case_id=plan_item.test_case_id,
        file_path=str(resolved_path) if resolved_path is not None else plan_item.file_path,
        action=plan_item.action,
        apply_mode=plan_item.apply_mode,
        apply_status=apply_status,
        before_sha256=before_sha,
        after_sha256=before_sha,
        backup_path=None,
        changed_lines=[],
        applied_changes=[],
        skipped_reason=skipped_reason,
        warnings=_unique([*plan_item.warnings, *(warnings or [])]),
    )


def _create_backups(
    writable_paths: list[Path],
    *,
    file_states: dict[Path, _FileState],
    test_cases_dir: Path,
    backup_root: Path,
) -> dict[Path, Path]:
    backup_paths: dict[Path, Path] = {}
    for file_path in writable_paths:
        relative_path = _relative_file_path(file_path, test_cases_dir)
        backup_path = backup_root / f"{relative_path}.bak"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(
            file_states[file_path].original_content,
            encoding="utf-8",
            newline="",
        )
        file_states[file_path].backup_path = backup_path
        backup_paths[file_path] = backup_path
    return backup_paths


def _attach_backup_paths(
    apply_items: list[ApplyResultItem],
    backup_paths: dict[Path, Path],
) -> list[ApplyResultItem]:
    updated: list[ApplyResultItem] = []
    for item in apply_items:
        if item.apply_status != "applied" or item.file_path is None:
            updated.append(item)
            continue
        backup_path = backup_paths.get(Path(item.file_path))
        updated.append(
            ApplyResultItem(
                **{
                    **item.to_dict(),
                    "backup_path": str(backup_path) if backup_path is not None else None,
                }
            )
        )
    return updated


def _write_changed_files(
    apply_items: list[ApplyResultItem],
    file_states: dict[Path, _FileState],
) -> tuple[list[ApplyResultItem], list[str]]:
    failed_files: dict[Path, str] = {}
    files_changed: list[str] = []
    for file_path, state in file_states.items():
        if state.current_content == state.original_content:
            continue
        try:
            file_path.write_text(state.current_content, encoding="utf-8", newline="")
            files_changed.append(str(file_path))
        except Exception as exc:  # noqa: BLE001 - per-file write failure must be reported.
            failed_files[file_path] = str(exc)

    if not failed_files:
        return apply_items, files_changed

    updated: list[ApplyResultItem] = []
    for item in apply_items:
        file_path = Path(item.file_path) if item.file_path else None
        if item.apply_status == "applied" and file_path in failed_files:
            updated.append(
                ApplyResultItem(
                    **{
                        **item.to_dict(),
                        "apply_status": "failed",
                        "skipped_reason": f"file write failed: {failed_files[file_path]}",
                        "warnings": _unique([*item.warnings, f"file write failed: {failed_files[file_path]}"]),
                    }
                )
            )
        else:
            updated.append(item)
    return updated, files_changed


def _file_state(file_path: Path, file_states: dict[Path, _FileState]) -> _FileState:
    file_path = file_path.resolve()
    if file_path not in file_states:
        content = file_path.read_text(encoding="utf-8")
        file_states[file_path] = _FileState(original_content=content, current_content=content)
    return file_states[file_path]


def _resolve_item_file_path(file_path: str, test_cases_dir: Path) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path.resolve()
    candidate = test_cases_dir / path
    if candidate.exists():
        return candidate.resolve()
    name_candidate = test_cases_dir / path.name
    if name_candidate.exists():
        return name_candidate.resolve()
    return candidate.resolve()


def _relative_file_path(file_path: Path, test_cases_dir: Path) -> Path:
    try:
        return file_path.resolve().relative_to(test_cases_dir.resolve())
    except ValueError:
        return Path(file_path.name)


def _conflicting_safe_update_reasons(
    plan_items: list[UpdatePlanItem],
    test_cases_dir: Path,
) -> list[str]:
    groups: dict[tuple[str | None, str], set[tuple[str, ...]]] = {}
    ids: dict[tuple[str | None, str], list[str]] = {}
    for item in plan_items:
        if (
            item.action != "traceability_update_only"
            or item.apply_mode != "safe_auto_candidate"
        ):
            continue
        file_key = str(_resolve_item_file_path(item.file_path, test_cases_dir)) if item.file_path else ""
        key = (item.test_case_id, file_key)
        groups.setdefault(key, set()).add(tuple(item.new_refs))
        ids.setdefault(key, []).append(item.plan_item_id)

    reasons: list[str] = []
    for (test_case_id, file_key), new_ref_sets in groups.items():
        if len(new_ref_sets) > 1:
            reasons.append(
                "conflicting safe traceability updates target "
                f"test_case_id={test_case_id} file_path={file_key}: {', '.join(ids[(test_case_id, file_key)])}"
            )
    return reasons


def _make_report(
    *,
    ft_slug: str,
    old_source_version: str,
    new_source_version: str,
    update_plan_path: Path,
    test_cases_dir: Path,
    dry_run: bool,
    plan_items_total: int,
    apply_items: list[ApplyResultItem],
    files_changed: list[str],
    backups_created: list[str],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
) -> ApplyReport:
    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    summary = _summary(
        dry_run=dry_run,
        plan_items_total=plan_items_total,
        apply_items=apply_items,
        files_changed=files_changed,
        backups_created=backups_created,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )
    return ApplyReport(
        ft_slug=ft_slug,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        update_plan_path=str(update_plan_path),
        test_cases_dir=str(test_cases_dir),
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        dry_run=dry_run,
        apply_items=apply_items,
        summary=summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def _summary(
    *,
    dry_run: bool,
    plan_items_total: int,
    apply_items: list[ApplyResultItem],
    files_changed: list[str],
    backups_created: list[str],
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    counts = Counter(item.apply_status for item in apply_items)
    status_keys = [
        "applied",
        "previewed",
        "skipped_noop",
        "skipped_manual_only",
        "skipped_blocked",
        "skipped_unsafe",
        "failed",
    ]
    if blocking_reasons:
        apply_status: ReportStatus = "blocked"
    elif warnings or counts.get("failed", 0) or counts.get("skipped_unsafe", 0) or counts.get("skipped_blocked", 0):
        apply_status = "pass-with-warnings"
    else:
        apply_status = "pass"
    return {
        "apply_status": apply_status,
        "dry_run": dry_run,
        "plan_items_total": plan_items_total,
        "apply_items_total": len(apply_items),
        **{key: counts.get(key, 0) for key in status_keys},
        "files_changed_count": len(files_changed),
        "files_changed": files_changed,
        "backups_created": backups_created,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
    }


def _append_apply_lines(lines: list[str], items: list[ApplyResultItem]) -> None:
    if not items:
        lines.append("- none")
        return
    for item in items:
        target = item.test_case_id or "new/unlinked"
        path = item.file_path or "n/a"
        lines.append(
            f"- `{item.apply_item_id}` `{item.apply_status}` `{item.action}` "
            f"for `{target}` ({path}), plan `{item.plan_item_id}`"
        )
        if item.changed_lines:
            lines.append(f"  - changed lines: {', '.join(str(line) for line in item.changed_lines)}")
        if item.applied_changes:
            lines.append(f"  - changes: {'; '.join(item.applied_changes)}")
        if item.skipped_reason:
            lines.append(f"  - reason: {item.skipped_reason}")


def _apply_item_warnings(items: list[ApplyResultItem]) -> list[str]:
    warnings: list[str] = []
    for item in items:
        warnings.extend(item.warnings)
    return warnings


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value)
        if text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _load_optional_summary(
    path: Path,
    *,
    explicit: bool,
    warnings: list[str],
) -> dict[str, Any] | None:
    if not path.exists():
        if explicit:
            warnings.append(f"update plan summary file is missing: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - optional summary is diagnostic context.
        warnings.append(f"update plan summary file cannot be parsed: {path}: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"update plan summary root must be a JSON object: {path}")
        return None
    return payload


def _infer_versions_from_plan_path(path: Path) -> tuple[str, str]:
    stem = path.stem
    prefix = "test-case-update-plan."
    if stem.startswith(prefix):
        version_part = stem[len(prefix):]
        if "-to-" in version_part:
            old_version, new_version = version_part.split("-to-", 1)
            return old_version or "unknown-old", new_version or "unknown-new"
    return "unknown-old", "unknown-new"


def _infer_plan_summary_path(path: Path, old_source_version: str, new_source_version: str) -> Path:
    return path.with_name(f"test-case-update-plan-summary.{old_source_version}-to-{new_source_version}.json")


def _apply_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{APPLY_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _summary_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{APPLY_SUMMARY_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _markdown_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{APPLY_PREFIX}.{old_source_version}-to-{new_source_version}.md"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
