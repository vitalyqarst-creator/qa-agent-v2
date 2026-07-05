from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.test_case_update_plan import (
    TestCaseUpdatePlan,
    UpdatePlanItem,
    load_test_case_update_plan,
)

CREATED_BY_TOOL = "test_case_agent.manual_update_packages"
PACKAGES_PREFIX = "manual-update-packages"
PACKAGES_SUMMARY_PREFIX = "manual-update-packages-summary"

PackageType = Literal[
    "update_existing",
    "create_new_candidate",
    "mark_deprecated_candidate",
    "manual_review",
    "mixed",
]
PackagePriority = Literal["high", "medium", "low"]
PackageStatus = Literal["pass", "pass-with-warnings", "blocked"]

BASE_FORBIDDEN_OPERATIONS = [
    "Do not touch unlisted TC",
    "Do not rewrite entire file",
    "Do not reorder unrelated TC",
    "Do not change unrelated traceability",
    "Do not delete TC silently",
]


@dataclass(frozen=True)
class ManualUpdatePackage:
    package_id: str
    package_type: PackageType
    file_path: str | None
    test_case_ids: list[str]
    plan_item_ids: list[str]
    impact_ids: list[str]
    change_ids: list[str]
    actions: list[str]
    priority: PackagePriority
    requires_manual_review: bool
    writer_allowed_operations: list[str]
    writer_forbidden_operations: list[str]
    rationale: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "package_type": self.package_type,
            "file_path": self.file_path,
            "test_case_ids": self.test_case_ids,
            "plan_item_ids": self.plan_item_ids,
            "impact_ids": self.impact_ids,
            "change_ids": self.change_ids,
            "actions": self.actions,
            "priority": self.priority,
            "requires_manual_review": self.requires_manual_review,
            "writer_allowed_operations": self.writer_allowed_operations,
            "writer_forbidden_operations": self.writer_forbidden_operations,
            "rationale": self.rationale,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualUpdatePackage":
        return cls(
            package_id=str(data["package_id"]),
            package_type=data["package_type"],
            file_path=data.get("file_path"),
            test_case_ids=list(data.get("test_case_ids") or []),
            plan_item_ids=list(data.get("plan_item_ids") or []),
            impact_ids=list(data.get("impact_ids") or []),
            change_ids=list(data.get("change_ids") or []),
            actions=list(data.get("actions") or []),
            priority=data["priority"],
            requires_manual_review=bool(data["requires_manual_review"]),
            writer_allowed_operations=list(data.get("writer_allowed_operations") or []),
            writer_forbidden_operations=list(data.get("writer_forbidden_operations") or []),
            rationale=list(data.get("rationale") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass
class ManualUpdatePackagesReport:
    ft_slug: str
    old_source_version: str
    new_source_version: str
    update_plan_path: str
    created_at_utc: str
    created_by_tool: str
    packages: list[ManualUpdatePackage]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ft_slug": self.ft_slug,
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "update_plan_path": self.update_plan_path,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "packages": [package.to_dict() for package in self.packages],
            "summary": self.summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualUpdatePackagesReport":
        return cls(
            ft_slug=str(data["ft_slug"]),
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            update_plan_path=str(data["update_plan_path"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            packages=[
                ManualUpdatePackage.from_dict(package)
                for package in data.get("packages", [])
            ],
            summary=dict(data.get("summary") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def build_manual_update_packages(
    *,
    update_plan_path: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ManualUpdatePackagesReport:
    update_plan_path = Path(update_plan_path)
    inferred_old, inferred_new = _infer_versions_from_plan_path(update_plan_path)
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    plan: TestCaseUpdatePlan | None = None

    if not update_plan_path.exists():
        blocking_reasons.append(f"update plan file is missing: {update_plan_path}")
    else:
        try:
            plan = load_test_case_update_plan(update_plan_path)
        except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
            blocking_reasons.append(f"update plan file cannot be parsed: {update_plan_path}: {exc}")

    if plan is not None:
        ft_slug = plan.ft_slug
        old_source_version = plan.old_source_version
        new_source_version = plan.new_source_version
        warnings.extend(plan.warnings)
        warnings.extend(plan.summary.get("warnings") or [])
        if plan.summary.get("plan_status") == "blocked":
            blocking_reasons.append("update plan summary is blocked.")
        blocking_reasons.extend(plan.blocking_reasons)
    else:
        ft_slug = "unknown"
        old_source_version = inferred_old
        new_source_version = inferred_new

    packages: list[ManualUpdatePackage] = []
    if not blocking_reasons and plan is not None:
        packages = _packages_from_plan_items(plan.plan_items)
        if not packages:
            blocking_reasons.append("no manual update items or candidates require work packages.")
        blocking_reasons.extend(_duplicate_package_id_reasons(packages))
        blocking_reasons.extend(_conflicting_package_target_reasons(packages))
        if blocking_reasons:
            packages = []

    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    summary = _summary(
        packages=packages,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )
    return ManualUpdatePackagesReport(
        ft_slug=ft_slug,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        update_plan_path=str(update_plan_path),
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        packages=packages,
        summary=summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def write_manual_update_packages(
    report: ManualUpdatePackagesReport,
    out_dir: Path,
) -> tuple[Path, Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = _packages_path(out_dir, report.old_source_version, report.new_source_version)
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
        render_manual_update_packages_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return report_path, summary_path, markdown_path


def load_manual_update_packages(path: Path) -> ManualUpdatePackagesReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manual update packages report root must be a JSON object.")
    return ManualUpdatePackagesReport.from_dict(payload)


def render_manual_update_packages_markdown(report: ManualUpdatePackagesReport) -> str:
    lines = [
        "# Manual Update Work Packages",
        "",
        "## Summary",
        "",
        f"- FT slug: `{report.ft_slug}`",
        f"- Source versions: `{report.old_source_version}` -> `{report.new_source_version}`",
        f"- Package status: `{report.summary['package_status']}`",
        f"- Packages total: `{report.summary['packages_total']}`",
        f"- Files affected: `{report.summary['files_affected_count']}`",
        f"- Test cases affected: `{report.summary['test_cases_affected_count']}`",
        "",
        "## Packages by File",
        "",
    ]
    _append_package_lines(lines, [package for package in report.packages if package.file_path])
    lines.extend(["", "## New TC Candidates", ""])
    _append_package_lines(lines, [package for package in report.packages if package.package_type == "create_new_candidate"])
    lines.extend(["", "## Deprecated Candidates", ""])
    _append_package_lines(
        lines,
        [
            package
            for package in report.packages
            if package.package_type == "mark_deprecated_candidate"
            or "mark_deprecated_candidate" in package.actions
        ],
    )
    lines.extend(["", "## Manual Review Packages", ""])
    _append_package_lines(
        lines,
        [
            package
            for package in report.packages
            if package.package_type == "manual_review" or "manual_review" in package.actions
        ],
    )
    if report.blocking_reasons:
        lines.extend(["", "## Blocking Reasons", ""])
        for reason in report.blocking_reasons:
            lines.append(f"- package generation blocked: {reason}")
    lines.extend(["", "## Do Not Touch Rules", ""])
    for rule in BASE_FORBIDDEN_OPERATIONS:
        lines.append(f"- {rule}")
    lines.append("- Do not edit canonical test-case files in Stage 7A.")
    lines.append("- Do not create new test-case files in Stage 7A.")
    lines.append("- Do not mark test cases deprecated in Stage 7A.")
    return "\n".join(lines).rstrip() + "\n"


def _packages_from_plan_items(plan_items: list[UpdatePlanItem]) -> list[ManualUpdatePackage]:
    manual_items = [
        item
        for item in plan_items
        if item.apply_mode == "manual_only" and item.action != "keep"
    ]
    groups: dict[tuple[str, str], list[UpdatePlanItem]] = defaultdict(list)
    for item in manual_items:
        groups[_group_key(item)].append(item)

    packages: list[ManualUpdatePackage] = []
    for index, key in enumerate(sorted(groups), start=1):
        packages.append(_make_package(index, groups[key]))
    return packages


def _group_key(item: UpdatePlanItem) -> tuple[str, str]:
    if item.file_path:
        return ("file", item.file_path)
    if item.action == "create_new_candidate":
        return ("action", "create_new_candidate")
    if item.action == "manual_review":
        return ("unlinked", "manual_review")
    return ("unlinked", item.action)


def _make_package(index: int, items: list[UpdatePlanItem]) -> ManualUpdatePackage:
    actions = sorted(_unique(item.action for item in items))
    package_type = _package_type(actions)
    return ManualUpdatePackage(
        package_id=f"WPKG-{index:06d}",
        package_type=package_type,
        file_path=_single_file_path(items),
        test_case_ids=_unique(item.test_case_id for item in items if item.test_case_id),
        plan_item_ids=_unique(item.plan_item_id for item in items),
        impact_ids=_unique(item.impact_id for item in items),
        change_ids=_unique(item.change_id for item in items),
        actions=actions,
        priority=_priority(actions),
        requires_manual_review=any(item.requires_manual_review for item in items),
        writer_allowed_operations=_allowed_operations(actions),
        writer_forbidden_operations=_forbidden_operations(items),
        rationale=_unique(
            rationale
            for item in items
            for rationale in item.rationale
        ),
        warnings=_unique(
            warning
            for item in items
            for warning in item.warnings
        ),
    )


def _package_type(actions: list[str]) -> PackageType:
    if len(actions) > 1:
        return "mixed"
    action = actions[0] if actions else "manual_review"
    if action in {"update_existing", "create_new_candidate", "mark_deprecated_candidate", "manual_review"}:
        return action  # type: ignore[return-value]
    return "manual_review"


def _priority(actions: list[str]) -> PackagePriority:
    if set(actions) & {"update_existing", "create_new_candidate", "mark_deprecated_candidate", "manual_review"}:
        return "high"
    if "traceability_update_only" in actions:
        return "medium"
    return "low"


def _allowed_operations(actions: list[str]) -> list[str]:
    operations: list[str] = []
    for action in actions:
        if action == "update_existing":
            operations.extend([
                "update listed TC only",
                "review steps",
                "review expected result",
                "update traceability",
            ])
        elif action == "create_new_candidate":
            operations.extend([
                "propose new TC drafts",
                "do not write into canonical test-case files yet",
            ])
        elif action == "mark_deprecated_candidate":
            operations.extend([
                "propose deprecated marking",
                "do not edit files yet",
            ])
        elif action == "manual_review":
            operations.extend([
                "analyze ambiguity",
                "do not apply automatic changes",
            ])
        elif action == "traceability_update_only":
            operations.extend([
                "update listed TC only",
                "review traceability only",
                "update traceability",
            ])
    return _unique(operations)


def _forbidden_operations(items: list[UpdatePlanItem]) -> list[str]:
    return _unique([
        *BASE_FORBIDDEN_OPERATIONS,
        *(
            operation
            for item in items
            for operation in item.forbidden_changes
        ),
    ])


def _single_file_path(items: list[UpdatePlanItem]) -> str | None:
    values = _unique(item.file_path for item in items if item.file_path)
    return values[0] if len(values) == 1 else None


def _duplicate_package_id_reasons(packages: list[ManualUpdatePackage]) -> list[str]:
    counts = Counter(package.package_id for package in packages)
    return [
        f"duplicate package_id detected: {package_id}"
        for package_id, count in sorted(counts.items())
        if count > 1
    ]


def _conflicting_package_target_reasons(packages: list[ManualUpdatePackage]) -> list[str]:
    targets: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for package in packages:
        if package.file_path is None:
            continue
        for test_case_id in package.test_case_ids:
            for action in package.actions:
                targets[(test_case_id, package.file_path, action)].append(package.package_id)

    reasons: list[str] = []
    for (test_case_id, file_path, action), package_ids in sorted(targets.items()):
        if len(set(package_ids)) <= 1:
            continue
        reasons.append(
            "conflicting packages for "
            f"test_case_id={test_case_id} file_path={file_path} action={action}: "
            f"{', '.join(sorted(set(package_ids)))}"
        )
    return reasons


def _summary(
    *,
    packages: list[ManualUpdatePackage],
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    package_types = Counter(package.package_type for package in packages)
    files = {package.file_path for package in packages if package.file_path}
    test_cases = {
        test_case_id
        for package in packages
        for test_case_id in package.test_case_ids
    }
    summary_warnings = _unique([
        *warnings,
        *(
            warning
            for package in packages
            for warning in package.warnings
        ),
    ])
    if blocking_reasons:
        package_status: PackageStatus = "blocked"
    elif summary_warnings or any(package.requires_manual_review for package in packages):
        package_status = "pass-with-warnings"
    else:
        package_status = "pass"
    return {
        "package_status": package_status,
        "packages_total": len(packages),
        "files_affected_count": len(files),
        "test_cases_affected_count": len(test_cases),
        "create_new_candidate_count": package_types.get("create_new_candidate", 0),
        "mark_deprecated_candidate_count": package_types.get("mark_deprecated_candidate", 0),
        "update_existing_count": package_types.get("update_existing", 0),
        "manual_review_count": package_types.get("manual_review", 0),
        "mixed_package_count": package_types.get("mixed", 0),
        "warnings": summary_warnings,
        "blocking_reasons": blocking_reasons,
    }


def _append_package_lines(lines: list[str], packages: list[ManualUpdatePackage]) -> None:
    if not packages:
        lines.append("- none")
        return
    for package in packages:
        target = package.file_path or "unlinked/candidate"
        tests = ", ".join(package.test_case_ids) if package.test_case_ids else "n/a"
        lines.append(
            f"- `{package.package_id}` `{package.package_type}` `{package.priority}` "
            f"for `{target}`; TC: `{tests}`; actions: `{', '.join(package.actions)}`"
        )
        lines.append(f"  - plan items: {', '.join(package.plan_item_ids)}")
        lines.append(f"  - allowed: {', '.join(package.writer_allowed_operations) or 'none'}")
        lines.append(f"  - forbidden: {', '.join(package.writer_forbidden_operations)}")


def _infer_versions_from_plan_path(path: Path) -> tuple[str, str]:
    stem = path.stem
    prefix = "test-case-update-plan."
    if stem.startswith(prefix):
        version_part = stem[len(prefix):]
        if "-to-" in version_part:
            old_version, new_version = version_part.split("-to-", 1)
            return old_version or "unknown-old", new_version or "unknown-new"
    return "unknown-old", "unknown-new"


def _packages_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{PACKAGES_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _summary_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{PACKAGES_SUMMARY_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _markdown_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return out_dir / f"{PACKAGES_PREFIX}.{old_source_version}-to-{new_source_version}.md"


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
