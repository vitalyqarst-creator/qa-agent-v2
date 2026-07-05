from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.manual_update_packages import (
    ManualUpdatePackage,
    ManualUpdatePackagesReport,
    load_manual_update_packages,
)

CREATED_BY_TOOL = "test_case_agent.writer_package_tasks"
TASKS_PREFIX = "writer-package-tasks"
TASKS_SUMMARY_PREFIX = "writer-package-tasks-summary"
TASK_FILE_PREFIX = "writer-package-task"
LARGE_PACKAGE_PLAN_ITEMS_THRESHOLD = 50

TaskStatus = Literal["pass", "pass-with-warnings", "blocked"]

FILE_BOUND_SCOPE_INSTRUCTION = "Update only listed TC, do not rewrite entire file."
CREATE_NEW_SCOPE_INSTRUCTION = "Propose drafts only, do not write canonical files."
UNLINKED_SCOPE_INSTRUCTION = "Analyze and classify, do not edit files."
LARGE_PACKAGE_RECOMMENDATION = "Recommend splitting before writer execution."


@dataclass(frozen=True)
class WriterPackageTask:
    package_id: str
    task_file_name: str
    package_type: str
    file_path: str | None
    affected_test_case_ids: list[str]
    plan_item_ids: list[str]
    impact_ids: list[str]
    change_ids: list[str]
    actions: list[str]
    plan_items_count: int
    large_package: bool
    safe_to_try_first: bool
    allowed_operations: list[str]
    forbidden_operations: list[str]
    scope_instruction: str
    execution_notes: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "task_file_name": self.task_file_name,
            "package_type": self.package_type,
            "file_path": self.file_path,
            "affected_test_case_ids": self.affected_test_case_ids,
            "plan_item_ids": self.plan_item_ids,
            "impact_ids": self.impact_ids,
            "change_ids": self.change_ids,
            "actions": self.actions,
            "plan_items_count": self.plan_items_count,
            "large_package": self.large_package,
            "safe_to_try_first": self.safe_to_try_first,
            "allowed_operations": self.allowed_operations,
            "forbidden_operations": self.forbidden_operations,
            "scope_instruction": self.scope_instruction,
            "execution_notes": self.execution_notes,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriterPackageTask":
        return cls(
            package_id=str(data["package_id"]),
            task_file_name=str(data["task_file_name"]),
            package_type=str(data["package_type"]),
            file_path=data.get("file_path"),
            affected_test_case_ids=list(data.get("affected_test_case_ids") or []),
            plan_item_ids=list(data.get("plan_item_ids") or []),
            impact_ids=list(data.get("impact_ids") or []),
            change_ids=list(data.get("change_ids") or []),
            actions=list(data.get("actions") or []),
            plan_items_count=int(data.get("plan_items_count") or 0),
            large_package=bool(data.get("large_package")),
            safe_to_try_first=bool(data.get("safe_to_try_first")),
            allowed_operations=list(data.get("allowed_operations") or []),
            forbidden_operations=list(data.get("forbidden_operations") or []),
            scope_instruction=str(data["scope_instruction"]),
            execution_notes=list(data.get("execution_notes") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass
class WriterPackageTasksReport:
    ft_slug: str
    old_source_version: str
    new_source_version: str
    manual_update_packages_path: str
    created_at_utc: str
    created_by_tool: str
    tasks: list[WriterPackageTask]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ft_slug": self.ft_slug,
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "manual_update_packages_path": self.manual_update_packages_path,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "tasks": [task.to_dict() for task in self.tasks],
            "summary": self.summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WriterPackageTasksReport":
        return cls(
            ft_slug=str(data["ft_slug"]),
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            manual_update_packages_path=str(data["manual_update_packages_path"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            tasks=[WriterPackageTask.from_dict(task) for task in data.get("tasks", [])],
            summary=dict(data.get("summary") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def build_writer_package_tasks(
    *,
    manual_update_packages_path: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> WriterPackageTasksReport:
    manual_update_packages_path = Path(manual_update_packages_path)
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    packages_report: ManualUpdatePackagesReport | None = None

    if not manual_update_packages_path.exists():
        blocking_reasons.append(f"manual update packages file is missing: {manual_update_packages_path}")
    else:
        try:
            packages_report = load_manual_update_packages(manual_update_packages_path)
        except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
            blocking_reasons.append(
                f"manual update packages file cannot be parsed: {manual_update_packages_path}: {exc}"
            )

    if packages_report is None:
        ft_slug = "unknown"
        old_source_version, new_source_version = _infer_versions_from_packages_path(manual_update_packages_path)
    else:
        ft_slug = packages_report.ft_slug
        old_source_version = packages_report.old_source_version
        new_source_version = packages_report.new_source_version
        warnings.extend(packages_report.warnings)
        warnings.extend(packages_report.summary.get("warnings") or [])
        if packages_report.summary.get("package_status") == "blocked":
            blocking_reasons.append("manual update packages summary is blocked.")
        blocking_reasons.extend(packages_report.blocking_reasons)

    tasks: list[WriterPackageTask] = []
    if packages_report is not None and not blocking_reasons:
        tasks = [_task_from_package(package) for package in packages_report.packages]
        if not tasks:
            blocking_reasons.append("no manual update packages available for writer task generation.")
        blocking_reasons.extend(_duplicate_task_reasons(tasks))
        if blocking_reasons:
            tasks = []

    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    summary = _summary(tasks=tasks, warnings=warnings, blocking_reasons=blocking_reasons)
    return WriterPackageTasksReport(
        ft_slug=ft_slug,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        manual_update_packages_path=str(manual_update_packages_path),
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        tasks=tasks,
        summary=summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def write_writer_package_tasks(
    report: WriterPackageTasksReport,
    out_dir: Path,
) -> tuple[Path, Path, list[Path]]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = _tasks_path(out_dir, report.old_source_version, report.new_source_version)
    summary_path = _summary_path(out_dir, report.old_source_version, report.new_source_version)

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

    task_paths: list[Path] = []
    for task in report.tasks:
        task_path = out_dir / task.task_file_name
        task_path.write_text(
            render_writer_package_task_markdown(task),
            encoding="utf-8",
            newline="\n",
        )
        task_paths.append(task_path)
    return report_path, summary_path, task_paths


def load_writer_package_tasks(path: Path) -> WriterPackageTasksReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Writer package tasks report root must be a JSON object.")
    return WriterPackageTasksReport.from_dict(payload)


def render_writer_package_task_markdown(task: WriterPackageTask) -> str:
    lines = [
        f"# Writer Package Task {task.package_id}",
        "",
        "## Scope",
        "",
        f"- Package ID: `{task.package_id}`",
        f"- Package type: `{task.package_type}`",
        f"- File path: `{task.file_path or 'n/a'}`",
        f"- Affected TC IDs: `{', '.join(task.affected_test_case_ids) or 'n/a'}`",
        f"- Plan item IDs: `{', '.join(task.plan_item_ids) or 'n/a'}`",
        f"- Impact IDs: `{', '.join(task.impact_ids) or 'n/a'}`",
        f"- Change IDs: `{', '.join(task.change_ids) or 'n/a'}`",
        f"- Actions: `{', '.join(task.actions) or 'n/a'}`",
        f"- Plan items count: `{task.plan_items_count}`",
        f"- Large package: `{str(task.large_package).lower()}`",
        "",
        "## Instruction",
        "",
        task.scope_instruction,
    ]
    if task.large_package:
        lines.append(LARGE_PACKAGE_RECOMMENDATION)
    lines.extend(["", "## Allowed Operations", ""])
    _append_list(lines, task.allowed_operations)
    lines.extend(["", "## Forbidden Operations", ""])
    _append_list(lines, task.forbidden_operations)
    if task.execution_notes:
        lines.extend(["", "## Execution Notes", ""])
        _append_list(lines, task.execution_notes)
    if task.warnings:
        lines.extend(["", "## Warnings", ""])
        _append_list(lines, task.warnings)
    return "\n".join(lines).rstrip() + "\n"


def _task_from_package(package: ManualUpdatePackage) -> WriterPackageTask:
    large_package = package.plan_items_count > LARGE_PACKAGE_PLAN_ITEMS_THRESHOLD
    file_bound_with_tcs = bool(package.file_path and package.test_case_ids)
    create_new_candidate = package.package_type == "create_new_candidate" or "create_new_candidate" in package.actions
    unlinked = package.file_path is None
    scope_instruction = _scope_instruction(
        package=package,
        create_new_candidate=create_new_candidate,
        file_bound_with_tcs=file_bound_with_tcs,
        unlinked=unlinked,
    )
    forbidden_operations = _forbidden_operations(
        package=package,
        create_new_candidate=create_new_candidate,
        unlinked=unlinked,
        file_bound_with_tcs=file_bound_with_tcs,
    )
    execution_notes = _execution_notes(
        package=package,
        create_new_candidate=create_new_candidate,
        unlinked=unlinked,
        file_bound_with_tcs=file_bound_with_tcs,
        large_package=large_package,
    )
    safe_to_try_first = bool(
        file_bound_with_tcs
        and not large_package
        and package.plan_items_count <= 10
        and package.package_type != "mixed"
    )
    return WriterPackageTask(
        package_id=package.package_id,
        task_file_name=_task_file_name(package.package_id),
        package_type=package.package_type,
        file_path=package.file_path,
        affected_test_case_ids=package.test_case_ids,
        plan_item_ids=package.plan_item_ids,
        impact_ids=package.impact_ids,
        change_ids=package.change_ids,
        actions=package.actions,
        plan_items_count=package.plan_items_count,
        large_package=large_package,
        safe_to_try_first=safe_to_try_first,
        allowed_operations=package.writer_allowed_operations,
        forbidden_operations=forbidden_operations,
        scope_instruction=scope_instruction,
        execution_notes=execution_notes,
        warnings=package.warnings,
    )


def _scope_instruction(
    *,
    package: ManualUpdatePackage,
    create_new_candidate: bool,
    file_bound_with_tcs: bool,
    unlinked: bool,
) -> str:
    if create_new_candidate:
        return CREATE_NEW_SCOPE_INSTRUCTION
    if file_bound_with_tcs:
        return FILE_BOUND_SCOPE_INSTRUCTION
    if unlinked:
        return UNLINKED_SCOPE_INSTRUCTION
    return "Analyze listed package scope before editing; do not edit files until scope is explicit."


def _forbidden_operations(
    *,
    package: ManualUpdatePackage,
    create_new_candidate: bool,
    unlinked: bool,
    file_bound_with_tcs: bool,
) -> list[str]:
    forbidden = list(package.writer_forbidden_operations)
    if file_bound_with_tcs:
        forbidden.extend(["Do not touch unlisted TC", "Do not rewrite entire file"])
    if create_new_candidate:
        forbidden.extend(["Do not write canonical files", "Do not create new TC files in this stage"])
    if unlinked and not create_new_candidate:
        forbidden.extend(["Do not edit files"])
    return _unique(forbidden)


def _execution_notes(
    *,
    package: ManualUpdatePackage,
    create_new_candidate: bool,
    unlinked: bool,
    file_bound_with_tcs: bool,
    large_package: bool,
) -> list[str]:
    notes: list[str] = []
    if file_bound_with_tcs:
        notes.append("Limit review and proposed edits to the listed TC IDs.")
    if create_new_candidate:
        notes.append("Prepare candidate draft content outside canonical test-case files.")
    elif unlinked:
        notes.append("Classify the package before assigning it to a concrete file or TC.")
    if large_package:
        notes.append(LARGE_PACKAGE_RECOMMENDATION)
    if package.rationale:
        notes.extend(package.rationale)
    return _unique(notes)


def _summary(
    *,
    tasks: list[WriterPackageTask],
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    largest_task_plan_items_count = max((task.plan_items_count for task in tasks), default=0)
    large_package_tasks = [task.package_id for task in tasks if task.large_package]
    summary_warnings = _unique([
        *warnings,
        *(
            warning
            for task in tasks
            for warning in task.warnings
        ),
    ])
    if blocking_reasons:
        task_status: TaskStatus = "blocked"
    elif summary_warnings or large_package_tasks:
        task_status = "pass-with-warnings"
    else:
        task_status = "pass"
    return {
        "task_status": task_status,
        "tasks_total": len(tasks),
        "file_bound_tasks": sum(1 for task in tasks if task.file_path is not None),
        "unlinked_tasks": sum(1 for task in tasks if task.file_path is None),
        "create_new_candidate_tasks": sum(
            1
            for task in tasks
            if task.package_type == "create_new_candidate" or "create_new_candidate" in task.actions
        ),
        "large_package_tasks": len(large_package_tasks),
        "large_package_task_ids": large_package_tasks,
        "largest_task_plan_items_count": largest_task_plan_items_count,
        "safe_to_try_first_task_ids": [
            task.package_id
            for task in tasks
            if task.safe_to_try_first
        ],
        "warnings": summary_warnings,
        "blocking_reasons": blocking_reasons,
    }


def _duplicate_task_reasons(tasks: list[WriterPackageTask]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for task in tasks:
        if task.package_id in seen:
            duplicates.append(f"duplicate writer task package_id detected: {task.package_id}")
        seen.add(task.package_id)
    return duplicates


def _tasks_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{TASKS_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _summary_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{TASKS_SUMMARY_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _task_file_name(package_id: str) -> str:
    return f"{TASK_FILE_PREFIX}-{package_id}.md"


def _infer_versions_from_packages_path(path: Path) -> tuple[str, str]:
    stem = path.stem
    prefix = "manual-update-packages."
    if stem.startswith(prefix):
        version_part = stem[len(prefix):]
        if "-to-" in version_part:
            old_version, new_version = version_part.split("-to-", 1)
            return old_version or "unknown-old", new_version or "unknown-new"
    return "unknown-old", "unknown-new"


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


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
