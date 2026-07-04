from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.impact_analysis import ImpactEntry, ImpactReport, TestCaseLink, load_impact_report

CREATED_BY_TOOL = "test_case_agent.test_case_update_plan"
PLAN_PREFIX = "test-case-update-plan"
PLAN_SUMMARY_PREFIX = "test-case-update-plan-summary"

PlanAction = Literal[
    "keep",
    "update_existing",
    "traceability_update_only",
    "create_new_candidate",
    "mark_deprecated_candidate",
    "manual_review",
    "blocked",
]
ApplyMode = Literal["manual_only", "safe_auto_candidate", "blocked"]
PlanStatus = Literal["pass", "pass-with-warnings", "blocked"]


@dataclass(frozen=True)
class UpdatePlanItem:
    plan_item_id: str
    impact_id: str
    change_id: str
    test_case_id: str | None
    file_path: str | None
    action: PlanAction
    apply_mode: ApplyMode
    old_refs: list[str]
    new_refs: list[str]
    required_changes: list[str]
    forbidden_changes: list[str]
    rationale: list[str]
    requires_manual_review: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_item_id": self.plan_item_id,
            "impact_id": self.impact_id,
            "change_id": self.change_id,
            "test_case_id": self.test_case_id,
            "file_path": self.file_path,
            "action": self.action,
            "apply_mode": self.apply_mode,
            "old_refs": self.old_refs,
            "new_refs": self.new_refs,
            "required_changes": self.required_changes,
            "forbidden_changes": self.forbidden_changes,
            "rationale": self.rationale,
            "requires_manual_review": self.requires_manual_review,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UpdatePlanItem":
        return cls(
            plan_item_id=str(data["plan_item_id"]),
            impact_id=str(data["impact_id"]),
            change_id=str(data["change_id"]),
            test_case_id=data.get("test_case_id"),
            file_path=data.get("file_path"),
            action=data["action"],
            apply_mode=data["apply_mode"],
            old_refs=list(data.get("old_refs") or []),
            new_refs=list(data.get("new_refs") or []),
            required_changes=list(data.get("required_changes") or []),
            forbidden_changes=list(data.get("forbidden_changes") or []),
            rationale=list(data.get("rationale") or []),
            requires_manual_review=bool(data["requires_manual_review"]),
            warnings=list(data.get("warnings") or []),
        )


@dataclass
class TestCaseUpdatePlan:
    ft_slug: str
    old_source_version: str
    new_source_version: str
    impact_report_path: str
    test_cases_dir: str
    created_at_utc: str
    created_by_tool: str
    plan_items: list[UpdatePlanItem]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ft_slug": self.ft_slug,
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "impact_report_path": self.impact_report_path,
            "test_cases_dir": self.test_cases_dir,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "plan_items": [item.to_dict() for item in self.plan_items],
            "summary": self.summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestCaseUpdatePlan":
        return cls(
            ft_slug=str(data["ft_slug"]),
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            impact_report_path=str(data["impact_report_path"]),
            test_cases_dir=str(data["test_cases_dir"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            plan_items=[
                UpdatePlanItem.from_dict(item)
                for item in data.get("plan_items", [])
            ],
            summary=dict(data.get("summary") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def build_test_case_update_plan(
    *,
    impact_report_path: Path,
    test_cases_dir: Path,
    impact_summary_path: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> TestCaseUpdatePlan:
    impact_report_path = Path(impact_report_path)
    test_cases_dir = Path(test_cases_dir)
    inferred_old, inferred_new = _infer_versions_from_impact_path(impact_report_path)
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    report: ImpactReport | None = None

    if not impact_report_path.exists():
        blocking_reasons.append(f"impact report file is missing: {impact_report_path}")
    else:
        try:
            report = load_impact_report(impact_report_path)
        except Exception as exc:  # noqa: BLE001 - artifact builder reports parse failures.
            blocking_reasons.append(f"impact report file cannot be parsed: {impact_report_path}: {exc}")

    if report is not None:
        ft_slug = report.ft_slug
        old_source_version = report.old_source_version
        new_source_version = report.new_source_version
        impact_entries_total = len(report.impact_entries)
        warnings.extend(report.warnings)
        warnings.extend(report.summary.get("warnings") or [])
        if report.summary.get("impact_status") == "blocked":
            blocking_reasons.append("impact report summary is blocked.")
        blocking_reasons.extend(report.blocking_reasons)
    else:
        ft_slug = "unknown"
        old_source_version = inferred_old
        new_source_version = inferred_new
        impact_entries_total = 0

    summary_path = (
        Path(impact_summary_path)
        if impact_summary_path is not None
        else _infer_impact_summary_path(impact_report_path, old_source_version, new_source_version)
    )
    impact_summary = _load_optional_summary(
        summary_path,
        explicit=impact_summary_path is not None,
        warnings=warnings,
    )
    if impact_summary and impact_summary.get("impact_status") == "blocked":
        blocking_reasons.append(f"impact summary is blocked: {summary_path}")
        blocking_reasons.extend(str(reason) for reason in impact_summary.get("blocking_reasons") or [])

    if not test_cases_dir.exists() or not test_cases_dir.is_dir():
        blocking_reasons.append(f"test-cases dir is missing: {test_cases_dir}")

    if report is not None and test_cases_dir.exists():
        blocking_reasons.extend(_missing_linked_file_reasons(report.impact_entries, test_cases_dir))

    plan_items: list[UpdatePlanItem] = []
    if not blocking_reasons and report is not None:
        plan_items = _plan_items_from_impact_entries(report.impact_entries)
        duplicate_reasons = _inconsistent_duplicate_plan_item_reasons(plan_items)
        if duplicate_reasons:
            blocking_reasons.extend(duplicate_reasons)
            plan_items = []

    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    summary = _summary(
        impact_entries_total=impact_entries_total,
        plan_items=plan_items,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )
    return TestCaseUpdatePlan(
        ft_slug=ft_slug,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        impact_report_path=str(impact_report_path),
        test_cases_dir=str(test_cases_dir),
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        plan_items=plan_items,
        summary=summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def write_test_case_update_plan(plan: TestCaseUpdatePlan, out_dir: Path) -> tuple[Path, Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = _plan_path(out_dir, plan.old_source_version, plan.new_source_version)
    summary_path = _summary_path(out_dir, plan.old_source_version, plan.new_source_version)
    markdown_path = _markdown_path(out_dir, plan.old_source_version, plan.new_source_version)

    plan_path.write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary_path.write_text(
        json.dumps(plan.summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_test_case_update_plan_markdown(plan),
        encoding="utf-8",
        newline="\n",
    )
    return plan_path, summary_path, markdown_path


def load_test_case_update_plan(path: Path) -> TestCaseUpdatePlan:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Test case update plan root must be a JSON object.")
    return TestCaseUpdatePlan.from_dict(payload)


def render_test_case_update_plan_markdown(plan: TestCaseUpdatePlan) -> str:
    lines = [
        "# Test Case Update Plan",
        "",
        "## Summary",
        "",
        f"- FT slug: `{plan.ft_slug}`",
        f"- Source versions: `{plan.old_source_version}` -> `{plan.new_source_version}`",
        f"- Plan status: `{plan.summary['plan_status']}`",
        f"- Plan items: `{plan.summary['plan_items_total']}`",
        f"- Safe auto candidates: `{plan.summary['safe_auto_candidates_count']}`",
        f"- Manual only: `{plan.summary['manual_only_count']}`",
        f"- Blocked items: `{plan.summary['blocked_items_count']}`",
        "",
        "## Safe Auto Candidates",
        "",
    ]
    _append_plan_lines(lines, [item for item in plan.plan_items if item.apply_mode == "safe_auto_candidate"])
    lines.extend(["", "## Manual Updates Required", ""])
    _append_plan_lines(lines, [item for item in plan.plan_items if item.apply_mode == "manual_only"])
    lines.extend(["", "## New TC Candidates", ""])
    _append_plan_lines(lines, [item for item in plan.plan_items if item.action == "create_new_candidate"])
    lines.extend(["", "## Deprecated Candidates", ""])
    _append_plan_lines(lines, [item for item in plan.plan_items if item.action == "mark_deprecated_candidate"])
    lines.extend(["", "## Traceability-only Updates", ""])
    _append_plan_lines(lines, [item for item in plan.plan_items if item.action == "traceability_update_only"])
    lines.extend(["", "## Blocked Items", ""])
    _append_plan_lines(lines, [item for item in plan.plan_items if item.apply_mode == "blocked"])
    if plan.blocking_reasons:
        for reason in plan.blocking_reasons:
            lines.append(f"- plan blocked: {reason}")
    lines.extend(["", "## Do Not Touch", ""])
    keep_items = [item for item in plan.plan_items if item.action == "keep"]
    _append_plan_lines(lines, keep_items)
    lines.extend(
        [
            "",
            "Stage 6A writes only plan artifacts. It must not edit, create, rewrite, or deprecate test-case files.",
            "",
        ]
    )
    return "\n".join(lines)


def _plan_items_from_impact_entries(impact_entries: list[ImpactEntry]) -> list[UpdatePlanItem]:
    items: list[UpdatePlanItem] = []
    for entry in impact_entries:
        linked_cases = entry.affected_test_cases or [None]
        if entry.action == "create_new":
            linked_cases = [None]
        for test_case in linked_cases:
            items.append(_make_plan_item(len(items) + 1, entry, test_case))
    return items


def _make_plan_item(
    index: int,
    entry: ImpactEntry,
    test_case: TestCaseLink | None,
) -> UpdatePlanItem:
    action = _plan_action(entry.action)
    apply_mode = _apply_mode(action, entry, test_case)
    warnings = _unique([*entry.warnings, *(test_case.parse_warnings if test_case is not None else [])])
    requires_manual_review = _requires_manual_review(action, apply_mode, entry, test_case)
    return UpdatePlanItem(
        plan_item_id=f"PLAN-{index:06d}",
        impact_id=entry.impact_id,
        change_id=entry.change_id,
        test_case_id=test_case.test_case_id if test_case is not None else None,
        file_path=test_case.file_path if test_case is not None else None,
        action=action,
        apply_mode=apply_mode,
        old_refs=_refs(entry.old_req_uid, entry.old_source_req_id),
        new_refs=_refs(entry.new_req_uid, entry.new_source_req_id),
        required_changes=_required_changes(action),
        forbidden_changes=_forbidden_changes(action),
        rationale=_unique([f"impact action={entry.action}", *entry.rationale]),
        requires_manual_review=requires_manual_review,
        warnings=warnings,
    )


def _plan_action(impact_action: str) -> PlanAction:
    mapping: dict[str, PlanAction] = {
        "no_action": "keep",
        "update_existing": "update_existing",
        "traceability_update_only": "traceability_update_only",
        "create_new": "create_new_candidate",
        "mark_deprecated": "mark_deprecated_candidate",
        "manual_review": "manual_review",
        "blocked_unlinked": "blocked",
    }
    return mapping.get(impact_action, "manual_review")


def _apply_mode(
    action: PlanAction,
    entry: ImpactEntry,
    test_case: TestCaseLink | None,
) -> ApplyMode:
    if action == "blocked":
        return "blocked"
    if action == "keep":
        return "safe_auto_candidate"
    if action == "traceability_update_only":
        if (
            test_case is not None
            and not test_case.parse_warnings
            and not entry.requires_manual_review
        ):
            return "safe_auto_candidate"
        return "manual_only"
    return "manual_only"


def _required_changes(action: PlanAction) -> list[str]:
    if action == "keep":
        return []
    if action == "traceability_update_only":
        return ["update traceability refs only"]
    if action == "update_existing":
        return ["review steps", "review expected result", "update traceability"]
    if action == "create_new_candidate":
        return ["create new TC candidate in later writer stage"]
    if action == "mark_deprecated_candidate":
        return ["mark linked TC as deprecated candidate in later writer stage"]
    if action == "manual_review":
        return ["manual review required before any test-case update"]
    return ["resolve blocking reason before planning updates"]


def _forbidden_changes(action: PlanAction) -> list[str]:
    if action == "keep":
        return ["Do not rewrite steps", "Do not rewrite expected result"]
    if action == "traceability_update_only":
        return ["Do not change steps", "Do not change expected result", "Do not change test data"]
    if action == "create_new_candidate":
        return ["Do not create TC in Stage 6A"]
    if action == "mark_deprecated_candidate":
        return ["Do not edit TC in Stage 6A"]
    if action == "blocked":
        return ["Do not update test cases while blocked"]
    return ["Do not auto-apply changes"]


def _requires_manual_review(
    action: PlanAction,
    apply_mode: ApplyMode,
    entry: ImpactEntry,
    test_case: TestCaseLink | None,
) -> bool:
    if entry.requires_manual_review or action in {
        "update_existing",
        "create_new_candidate",
        "mark_deprecated_candidate",
        "manual_review",
        "blocked",
    }:
        return True
    if action == "traceability_update_only" and apply_mode != "safe_auto_candidate":
        return True
    if test_case is not None and test_case.parse_warnings:
        return True
    return False


def _missing_linked_file_reasons(
    impact_entries: list[ImpactEntry],
    test_cases_dir: Path,
) -> list[str]:
    reasons: list[str] = []
    for entry in impact_entries:
        for test_case in entry.affected_test_cases:
            if not _linked_file_exists(test_case.file_path, test_cases_dir):
                reasons.append(
                    f"affected test-case file is missing for {test_case.test_case_id}: {test_case.file_path}"
                )
    return _unique(reasons)


def _linked_file_exists(file_path: str, test_cases_dir: Path) -> bool:
    path = Path(file_path)
    if path.exists():
        return True
    if not path.is_absolute():
        if (test_cases_dir / path).exists():
            return True
        if (test_cases_dir / path.name).exists():
            return True
    return False


def _inconsistent_duplicate_plan_item_reasons(items: list[UpdatePlanItem]) -> list[str]:
    groups: dict[tuple[str | None, str | None, PlanAction], list[UpdatePlanItem]] = defaultdict(list)
    for item in items:
        groups[(item.test_case_id, item.file_path, item.action)].append(item)

    reasons: list[str] = []
    for (test_case_id, file_path, action), group in groups.items():
        if len(group) <= 1:
            continue
        signatures = {
            (
                item.apply_mode,
                tuple(item.required_changes),
                tuple(item.forbidden_changes),
                item.requires_manual_review,
            )
            for item in group
        }
        if len(signatures) > 1:
            ids = ", ".join(item.plan_item_id for item in group)
            reasons.append(
                "inconsistent duplicate plan items for "
                f"test_case_id={test_case_id} file_path={file_path} action={action}: {ids}"
            )
    return reasons


def _summary(
    *,
    impact_entries_total: int,
    plan_items: list[UpdatePlanItem],
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    actions = Counter(item.action for item in plan_items)
    apply_modes = Counter(item.apply_mode for item in plan_items)
    action_keys = [
        "keep",
        "update_existing",
        "traceability_update_only",
        "create_new_candidate",
        "mark_deprecated_candidate",
        "manual_review",
        "blocked",
    ]
    apply_mode_keys = ["manual_only", "safe_auto_candidate", "blocked"]
    if blocking_reasons:
        plan_status: PlanStatus = "blocked"
    elif warnings or any(item.requires_manual_review or item.apply_mode == "blocked" for item in plan_items):
        plan_status = "pass-with-warnings"
    else:
        plan_status = "pass"
    return {
        "plan_status": plan_status,
        "impact_entries_total": impact_entries_total,
        "plan_items_total": len(plan_items),
        "actions": {key: actions.get(key, 0) for key in action_keys},
        "apply_modes": {key: apply_modes.get(key, 0) for key in apply_mode_keys},
        "safe_auto_candidates_count": apply_modes.get("safe_auto_candidate", 0),
        "manual_only_count": apply_modes.get("manual_only", 0),
        "blocked_items_count": apply_modes.get("blocked", 0),
        "requires_manual_review_count": sum(1 for item in plan_items if item.requires_manual_review),
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
    }


def _append_plan_lines(lines: list[str], items: list[UpdatePlanItem]) -> None:
    if not items:
        lines.append("- none")
        return
    for item in items:
        target = item.test_case_id or "new/unlinked"
        path = item.file_path or "n/a"
        lines.append(
            f"- `{item.plan_item_id}` `{item.action}` `{item.apply_mode}` "
            f"for `{target}` ({path}), impact `{item.impact_id}` / change `{item.change_id}`"
        )
        if item.required_changes:
            lines.append(f"  - required: {', '.join(item.required_changes)}")
        if item.forbidden_changes:
            lines.append(f"  - forbidden: {', '.join(item.forbidden_changes)}")
        if item.warnings:
            lines.append(f"  - warnings: {'; '.join(item.warnings)}")


def _refs(*values: str | None) -> list[str]:
    return _unique(str(value) for value in values if value)


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
            warnings.append(f"impact summary file is missing: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - optional summary is diagnostic context.
        warnings.append(f"impact summary file cannot be parsed: {path}: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"impact summary root must be a JSON object: {path}")
        return None
    return payload


def _infer_versions_from_impact_path(path: Path) -> tuple[str, str]:
    stem = path.stem
    prefix = "impact-report."
    if stem.startswith(prefix):
        version_part = stem[len(prefix):]
        if "-to-" in version_part:
            old_version, new_version = version_part.split("-to-", 1)
            return old_version or "unknown-old", new_version or "unknown-new"
    return "unknown-old", "unknown-new"


def _infer_impact_summary_path(path: Path, old_source_version: str, new_source_version: str) -> Path:
    return path.with_name(f"impact-report-summary.{old_source_version}-to-{new_source_version}.json")


def _plan_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{PLAN_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _summary_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{PLAN_SUMMARY_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _markdown_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{PLAN_PREFIX}.{old_source_version}-to-{new_source_version}.md"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
