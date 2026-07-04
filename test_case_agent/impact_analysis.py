from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.requirements_diff import (
    RequirementsDiff,
    RequirementsDiffEntry,
    load_requirements_diff,
)

CREATED_BY_TOOL = "test_case_agent.impact_analysis"
IMPACT_PREFIX = "impact-report"
IMPACT_SUMMARY_PREFIX = "impact-report-summary"
REQUIREMENTS_DIFF_SUMMARY_PREFIX = "requirements-diff-summary"

Action = Literal[
    "no_action",
    "update_existing",
    "create_new",
    "mark_deprecated",
    "manual_review",
    "traceability_update_only",
    "blocked_unlinked",
]
Priority = Literal["high", "medium", "low"]
ImpactStatus = Literal["pass", "pass-with-warnings", "blocked"]

TC_HEADING_RE = re.compile(r"^(##|###)\s+(TC-[A-Za-z0-9_-]+)\b[:\-\s]*(.*)$")
TITLE_RE = re.compile(r"\*\*Название:\*\*\s*(.+)")
TRACEABILITY_RE = re.compile(r"\*\*Трассировка:\*\*\s*(.*)")
REQ_UID_RE = re.compile(r"\bREQ-[A-Z0-9-]+\b")
ATOM_ID_RE = re.compile(r"\bATOM-[A-Z0-9-]+\b")
SOURCE_REQ_ID_RE = re.compile(
    r"\b(?:BSR\s+\d+|GSR\s+\d+|REQ[- ]?\d+|ID\s+\d+)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TestCaseLink:
    test_case_id: str
    file_path: str
    title: str | None
    linked_req_uids: list[str]
    linked_atom_ids: list[str]
    linked_source_req_ids: list[str]
    raw_traceability: str
    parse_warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_case_id": self.test_case_id,
            "file_path": self.file_path,
            "title": self.title,
            "linked_req_uids": self.linked_req_uids,
            "linked_atom_ids": self.linked_atom_ids,
            "linked_source_req_ids": self.linked_source_req_ids,
            "raw_traceability": self.raw_traceability,
            "parse_warnings": self.parse_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestCaseLink":
        return cls(
            test_case_id=str(data["test_case_id"]),
            file_path=str(data["file_path"]),
            title=data.get("title"),
            linked_req_uids=list(data.get("linked_req_uids") or []),
            linked_atom_ids=list(data.get("linked_atom_ids") or []),
            linked_source_req_ids=list(data.get("linked_source_req_ids") or []),
            raw_traceability=str(data.get("raw_traceability") or ""),
            parse_warnings=list(data.get("parse_warnings") or []),
        )


@dataclass(frozen=True)
class ImpactEntry:
    impact_id: str
    change_id: str
    change_type: str
    old_req_uid: str | None
    new_req_uid: str | None
    old_source_req_id: str | None
    new_source_req_id: str | None
    affected_test_cases: list[TestCaseLink]
    action: Action
    priority: Priority
    rationale: list[str]
    requires_manual_review: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "impact_id": self.impact_id,
            "change_id": self.change_id,
            "change_type": self.change_type,
            "old_req_uid": self.old_req_uid,
            "new_req_uid": self.new_req_uid,
            "old_source_req_id": self.old_source_req_id,
            "new_source_req_id": self.new_source_req_id,
            "affected_test_cases": [test_case.to_dict() for test_case in self.affected_test_cases],
            "action": self.action,
            "priority": self.priority,
            "rationale": self.rationale,
            "requires_manual_review": self.requires_manual_review,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImpactEntry":
        return cls(
            impact_id=str(data["impact_id"]),
            change_id=str(data["change_id"]),
            change_type=str(data["change_type"]),
            old_req_uid=data.get("old_req_uid"),
            new_req_uid=data.get("new_req_uid"),
            old_source_req_id=data.get("old_source_req_id"),
            new_source_req_id=data.get("new_source_req_id"),
            affected_test_cases=[
                TestCaseLink.from_dict(item)
                for item in data.get("affected_test_cases", [])
            ],
            action=data["action"],
            priority=data["priority"],
            rationale=list(data.get("rationale") or []),
            requires_manual_review=bool(data["requires_manual_review"]),
            warnings=list(data.get("warnings") or []),
        )


@dataclass
class ImpactReport:
    ft_slug: str
    old_source_version: str
    new_source_version: str
    requirements_diff_path: str
    test_cases_dir: str
    created_at_utc: str
    created_by_tool: str
    impact_entries: list[ImpactEntry]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ft_slug": self.ft_slug,
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "requirements_diff_path": self.requirements_diff_path,
            "test_cases_dir": self.test_cases_dir,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "impact_entries": [entry.to_dict() for entry in self.impact_entries],
            "summary": self.summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImpactReport":
        return cls(
            ft_slug=str(data["ft_slug"]),
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            requirements_diff_path=str(data["requirements_diff_path"]),
            test_cases_dir=str(data["test_cases_dir"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            impact_entries=[
                ImpactEntry.from_dict(entry)
                for entry in data.get("impact_entries", [])
            ],
            summary=dict(data.get("summary") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


@dataclass(frozen=True)
class ParsedTestCases:
    test_cases: list[TestCaseLink]
    files_scanned: int
    warnings: list[str]
    blocking_reasons: list[str]


def build_impact_report(
    *,
    requirements_diff_path: Path,
    test_cases_dir: Path,
    requirements_diff_summary_path: Path | None = None,
    allow_empty_test_cases: bool = False,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ImpactReport:
    requirements_diff_path = Path(requirements_diff_path)
    test_cases_dir = Path(test_cases_dir)
    requirements_diff_summary_path = (
        Path(requirements_diff_summary_path)
        if requirements_diff_summary_path is not None
        else _infer_diff_summary_path(requirements_diff_path)
    )

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    diff: RequirementsDiff | None = None
    diff_summary = _load_optional_summary(requirements_diff_summary_path, warnings)

    if not requirements_diff_path.exists():
        blocking_reasons.append(f"requirements diff file is missing: {requirements_diff_path}")
    else:
        try:
            diff = load_requirements_diff(requirements_diff_path)
        except Exception as exc:  # noqa: BLE001 - report must expose parse blockers.
            blocking_reasons.append(f"requirements diff file cannot be parsed: {requirements_diff_path}: {exc}")

    if _diff_status(diff_summary) == "blocked":
        blocking_reasons.append(f"requirements diff summary is blocked: {requirements_diff_summary_path}")
    if diff is not None and _diff_status(diff.summary) == "blocked":
        blocking_reasons.append("requirements diff object summary is blocked.")

    parsed = parse_test_cases(test_cases_dir)
    warnings.extend(parsed.warnings)
    blocking_reasons.extend(parsed.blocking_reasons)
    if not parsed.test_cases and not allow_empty_test_cases:
        blocking_reasons.append("no test cases parsed; pass allow_empty_test_cases only for source-only dry runs.")

    old_source_version = diff.old_source_version if diff else _version_pair(requirements_diff_path)[0]
    new_source_version = diff.new_source_version if diff else _version_pair(requirements_diff_path)[1]
    ft_slug = _infer_ft_slug(test_cases_dir)

    if blocking_reasons:
        return _make_report(
            ft_slug=ft_slug,
            old_source_version=old_source_version,
            new_source_version=new_source_version,
            requirements_diff_path=requirements_diff_path,
            test_cases_dir=test_cases_dir,
            impact_entries=[],
            test_case_links=parsed.test_cases,
            test_case_files_scanned=parsed.files_scanned,
            diff_entries_total=len(diff.entries) if diff else 0,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
        )

    impact_entries = link_diff_to_test_cases(diff.entries, parsed.test_cases)
    warnings.extend(_impact_warnings(impact_entries))
    return _make_report(
        ft_slug=ft_slug,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        requirements_diff_path=requirements_diff_path,
        test_cases_dir=test_cases_dir,
        impact_entries=impact_entries,
        test_case_links=parsed.test_cases,
        test_case_files_scanned=parsed.files_scanned,
        diff_entries_total=len(diff.entries),
        warnings=warnings,
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_impact_report(report: ImpactReport, out_dir: Path) -> tuple[Path, Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = _report_path(out_dir, report.old_source_version, report.new_source_version)
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
        render_impact_report_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return report_path, summary_path, markdown_path


def load_impact_report(path: Path) -> ImpactReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Impact report root must be a JSON object.")
    return ImpactReport.from_dict(payload)


def parse_test_cases(test_cases_dir: Path) -> ParsedTestCases:
    test_cases_dir = Path(test_cases_dir)
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    test_cases: list[TestCaseLink] = []
    files_scanned = 0

    if not test_cases_dir.exists() or not test_cases_dir.is_dir():
        return ParsedTestCases(
            test_cases=[],
            files_scanned=0,
            warnings=[],
            blocking_reasons=[f"test-cases dir is missing: {test_cases_dir}"],
        )

    for file_path in sorted(test_cases_dir.glob("*.md")):
        files_scanned += 1
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - parser must report unreadable files.
            blocking_reasons.append(f"test-case file cannot be read: {file_path}: {exc}")
            continue
        file_cases = _parse_test_case_file(file_path, content)
        test_cases.extend(file_cases)
        for test_case in file_cases:
            warnings.extend(f"{test_case.test_case_id}: {warning}" for warning in test_case.parse_warnings)

    duplicates = _duplicate_tc_ids(test_cases)
    if duplicates:
        blocking_reasons.append(f"duplicate TC ids detected: {', '.join(duplicates)}")

    return ParsedTestCases(
        test_cases=test_cases,
        files_scanned=files_scanned,
        warnings=sorted(set(warnings)),
        blocking_reasons=blocking_reasons,
    )


def link_diff_to_test_cases(
    diff_entries: list[RequirementsDiffEntry],
    test_cases: list[TestCaseLink],
) -> list[ImpactEntry]:
    entries: list[ImpactEntry] = []
    for diff_entry in diff_entries:
        linked = _linked_test_cases(diff_entry, test_cases)
        action, priority, rationale, warnings = _impact_decision(diff_entry, linked)
        requires_manual_review = _impact_requires_manual_review(diff_entry, action, linked)
        entries.append(
            ImpactEntry(
                impact_id=f"IMP-{len(entries) + 1:06d}",
                change_id=diff_entry.change_id,
                change_type=diff_entry.change_type,
                old_req_uid=diff_entry.old_req_uid,
                new_req_uid=diff_entry.new_req_uid,
                old_source_req_id=diff_entry.old_source_req_id,
                new_source_req_id=diff_entry.new_source_req_id,
                affected_test_cases=linked,
                action=action,
                priority=priority,
                rationale=rationale,
                requires_manual_review=requires_manual_review,
                warnings=sorted(set([*diff_entry.warnings, *warnings])),
            )
        )
    return entries


def render_impact_report_markdown(report: ImpactReport) -> str:
    lines = [
        "# Impact Report",
        "",
        "## Summary",
        "",
        f"- FT slug: `{report.ft_slug}`",
        f"- Source versions: `{report.old_source_version}` -> `{report.new_source_version}`",
        f"- Impact status: `{report.summary['impact_status']}`",
        f"- Impact entries: `{report.summary['impact_entries_total']}`",
        f"- Requires manual review: `{report.summary['requires_manual_review_count']}`",
        "",
        "## Actions by Type",
        "",
    ]
    for action, count in report.summary["actions"].items():
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(["", "## Affected Test Cases", ""])
    affected = [
        entry for entry in report.impact_entries
        if entry.affected_test_cases and entry.action not in {"create_new", "no_action"}
    ]
    _append_entry_lines(lines, affected, include_cases=True)
    lines.extend(["", "## Requirements Needing New TC", ""])
    _append_entry_lines(lines, [entry for entry in report.impact_entries if entry.action == "create_new"])
    lines.extend(["", "## Deprecated Candidates", ""])
    _append_entry_lines(lines, [entry for entry in report.impact_entries if entry.action == "mark_deprecated"], include_cases=True)
    lines.extend(["", "## Manual Review Required", ""])
    _append_entry_lines(lines, [entry for entry in report.impact_entries if entry.requires_manual_review], include_cases=True)
    lines.extend(["", "## Unlinked Changes", ""])
    _append_entry_lines(lines, [entry for entry in report.impact_entries if not entry.affected_test_cases])
    lines.extend(["", "## Parser Warnings", ""])
    if report.summary["warnings"]:
        for warning in report.summary["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _parse_test_case_file(file_path: Path, content: str) -> list[TestCaseLink]:
    lines = content.splitlines()
    headings: list[tuple[int, str, str, str]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line.strip())
        if match:
            headings.append((index, match.group(1), match.group(2), match.group(3).strip()))

    test_cases: list[TestCaseLink] = []
    for heading_index, (start, level, test_case_id, heading_tail) in enumerate(headings):
        end = headings[heading_index + 1][0] if heading_index + 1 < len(headings) else len(lines)
        block_lines = lines[start:end]
        parse_warnings: list[str] = []
        if level == "###":
            parse_warnings.append("legacy TC heading level detected")
        title = _extract_title(block_lines) or heading_tail or None
        raw_traceability = _extract_traceability(block_lines)
        if not raw_traceability:
            parse_warnings.append("missing traceability")
        test_cases.append(
            TestCaseLink(
                test_case_id=test_case_id,
                file_path=str(file_path),
                title=title,
                linked_req_uids=sorted(set(REQ_UID_RE.findall(raw_traceability.upper()))),
                linked_atom_ids=sorted(set(ATOM_ID_RE.findall(raw_traceability.upper()))),
                linked_source_req_ids=_source_req_ids(raw_traceability),
                raw_traceability=raw_traceability,
                parse_warnings=parse_warnings,
            )
        )
    return test_cases


def _extract_title(lines: list[str]) -> str | None:
    for line in lines:
        match = TITLE_RE.search(line)
        if match:
            return match.group(1).strip()
    return None


def _extract_traceability(lines: list[str]) -> str:
    collected: list[str] = []
    collecting = False
    for line in lines:
        match = TRACEABILITY_RE.search(line)
        if match:
            collecting = True
            if match.group(1).strip():
                collected.append(match.group(1).strip())
            continue
        if collecting:
            if line.startswith("**") and ":**" in line:
                break
            if TC_HEADING_RE.match(line.strip()):
                break
            if line.strip():
                collected.append(line.strip())
    return " ".join(collected).strip()


def _source_req_ids(text: str) -> list[str]:
    values: list[str] = []
    for match in SOURCE_REQ_ID_RE.finditer(text):
        values.append(re.sub(r"\s+", " ", match.group(0).upper()).strip())
    return sorted(set(values))


def _linked_test_cases(
    diff_entry: RequirementsDiffEntry,
    test_cases: list[TestCaseLink],
) -> list[TestCaseLink]:
    req_uids = {value for value in [diff_entry.old_req_uid, diff_entry.new_req_uid] if value}
    atom_ids = {value for value in [diff_entry.old_atom_id, diff_entry.new_atom_id] if value}
    source_req_ids = {
        value.upper()
        for value in [diff_entry.old_source_req_id, diff_entry.new_source_req_id]
        if value
    }
    linked: list[TestCaseLink] = []
    for test_case in test_cases:
        if req_uids & set(test_case.linked_req_uids):
            linked.append(test_case)
            continue
        if atom_ids & set(test_case.linked_atom_ids):
            linked.append(test_case)
            continue
        if source_req_ids & {value.upper() for value in test_case.linked_source_req_ids}:
            linked.append(test_case)
    return sorted(linked, key=lambda item: (item.file_path, item.test_case_id))


def _impact_decision(
    diff_entry: RequirementsDiffEntry,
    linked: list[TestCaseLink],
) -> tuple[Action, Priority, list[str], list[str]]:
    warnings: list[str] = []
    rationale = [f"change_type={diff_entry.change_type}"]
    has_links = bool(linked)

    if diff_entry.change_type == "unchanged":
        return "no_action", "low", rationale + ["requirement unchanged"], warnings
    if diff_entry.change_type in {"text_changed_no_behavior_change", "source_anchor_changed"}:
        if not has_links:
            warnings.append("traceability-only change has no linked test cases.")
        return "traceability_update_only", "low", rationale + ["behavior unchanged; traceability should be reviewed"], warnings
    if diff_entry.change_type == "renumbered":
        if not has_links:
            warnings.append("renumbered requirement has no linked test cases.")
        return "traceability_update_only", "medium", rationale + ["requirement appears renumbered"], warnings
    if diff_entry.change_type == "behavior_modified":
        if has_links:
            return "update_existing", "high", rationale + ["linked test cases need review/update"], warnings
        warnings.append("behavior_modified change has no linked test cases; create new coverage candidate.")
        return "create_new", "high", rationale + ["no linked test case found"], warnings
    if diff_entry.change_type == "added":
        if has_links:
            return "manual_review", "high", rationale + ["added requirement already has linked test cases"], warnings
        return "create_new", "high", rationale + ["new requirement needs coverage candidate"], warnings
    if diff_entry.change_type == "deleted":
        if has_links:
            return "mark_deprecated", "high", rationale + ["linked test cases target deleted requirement"], warnings
        warnings.append("deleted requirement has no linked test cases.")
        return "no_action", "low", rationale + ["no linked test case found"], warnings
    if diff_entry.change_type in {"split", "merged"}:
        if not has_links:
            warnings.append(f"{diff_entry.change_type} change has no linked test cases.")
        return "manual_review", "high", rationale + ["split/merged candidate requires human decision"], warnings
    if diff_entry.change_type == "unclear_match":
        if not has_links:
            warnings.append("unclear diff match has no linked test cases.")
        return "manual_review", "medium", rationale + ["unclear match requires human decision"], warnings
    return "manual_review", "medium", rationale + ["unrecognized change type fallback"], warnings


def _impact_requires_manual_review(
    diff_entry: RequirementsDiffEntry,
    action: Action,
    linked: list[TestCaseLink],
) -> bool:
    if diff_entry.requires_manual_review:
        return True
    if diff_entry.change_type in {"behavior_modified", "split", "merged", "unclear_match"}:
        return True
    if action in {"manual_review", "update_existing", "mark_deprecated"}:
        return True
    if any(test_case.parse_warnings for test_case in linked):
        return True
    return False


def _make_report(
    *,
    ft_slug: str,
    old_source_version: str,
    new_source_version: str,
    requirements_diff_path: Path,
    test_cases_dir: Path,
    impact_entries: list[ImpactEntry],
    test_case_links: list[TestCaseLink],
    test_case_files_scanned: int,
    diff_entries_total: int,
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
) -> ImpactReport:
    warnings = sorted(set(warnings))
    summary = _summary(
        diff_entries_total=diff_entries_total,
        impact_entries=impact_entries,
        test_case_links=test_case_links,
        test_case_files_scanned=test_case_files_scanned,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )
    return ImpactReport(
        ft_slug=ft_slug,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        requirements_diff_path=str(requirements_diff_path),
        test_cases_dir=str(test_cases_dir),
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        impact_entries=impact_entries,
        summary=summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def _summary(
    *,
    diff_entries_total: int,
    impact_entries: list[ImpactEntry],
    test_case_links: list[TestCaseLink],
    test_case_files_scanned: int,
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    actions = Counter(entry.action for entry in impact_entries)
    affected_ids = {
        test_case.test_case_id
        for entry in impact_entries
        for test_case in entry.affected_test_cases
    }
    unlinked_change_count = sum(1 for entry in impact_entries if not entry.affected_test_cases)
    parse_warnings_count = sum(len(test_case.parse_warnings) for test_case in test_case_links)
    if blocking_reasons:
        impact_status: ImpactStatus = "blocked"
    elif warnings or any(entry.requires_manual_review for entry in impact_entries):
        impact_status = "pass-with-warnings"
    else:
        impact_status = "pass"
    action_keys = [
        "no_action",
        "update_existing",
        "create_new",
        "mark_deprecated",
        "manual_review",
        "traceability_update_only",
        "blocked_unlinked",
    ]
    return {
        "impact_status": impact_status,
        "diff_entries_total": diff_entries_total,
        "impact_entries_total": len(impact_entries),
        "test_cases_scanned": len(test_case_links),
        "test_case_files_scanned": test_case_files_scanned,
        "affected_test_cases_count": len(affected_ids),
        "actions": {key: actions.get(key, 0) for key in action_keys},
        "requires_manual_review_count": sum(1 for entry in impact_entries if entry.requires_manual_review),
        "unlinked_change_count": unlinked_change_count,
        "parse_warnings_count": parse_warnings_count,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
    }


def _impact_warnings(entries: list[ImpactEntry]) -> list[str]:
    warnings: list[str] = []
    for entry in entries:
        warnings.extend(entry.warnings)
    return sorted(set(warnings))


def _append_entry_lines(
    lines: list[str],
    entries: list[ImpactEntry],
    *,
    include_cases: bool = False,
) -> None:
    if not entries:
        lines.append("- none")
        return
    for entry in entries:
        lines.append(f"- `{entry.impact_id}` `{entry.action}` `{entry.change_id}` `{entry.change_type}`")
        if include_cases:
            for test_case in entry.affected_test_cases:
                lines.append(f"  - `{test_case.test_case_id}` {test_case.file_path}")


def _duplicate_tc_ids(test_cases: list[TestCaseLink]) -> list[str]:
    counts = Counter(test_case.test_case_id for test_case in test_cases)
    return sorted(test_case_id for test_case_id, count in counts.items() if count > 1)


def _load_optional_summary(path: Path, warnings: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report can still use diff object summary.
        warnings.append(f"requirements diff summary could not be read: {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        warnings.append(f"requirements diff summary root is not a JSON object: {path}")
        return {}
    return payload


def _diff_status(summary: dict[str, Any]) -> str | None:
    status = summary.get("diff_status")
    return str(status) if status is not None else None


def _infer_diff_summary_path(diff_path: Path) -> Path:
    old_version, new_version = _version_pair(diff_path)
    if old_version != "unknown" and new_version != "unknown":
        return diff_path.with_name(f"{REQUIREMENTS_DIFF_SUMMARY_PREFIX}.{old_version}-to-{new_version}.json")
    return diff_path.with_name(f"{diff_path.stem}-summary.json")


def _version_pair(path: Path) -> tuple[str, str]:
    name = path.name
    if name.startswith("requirements-diff.") and name.endswith(".json"):
        middle = name[len("requirements-diff.") : -len(".json")]
        if "-to-" in middle:
            old_version, new_version = middle.split("-to-", 1)
            return old_version, new_version
    return "unknown", "unknown"


def _infer_ft_slug(test_cases_dir: Path) -> str:
    parts = Path(test_cases_dir).parts
    if "fts" in parts:
        index = parts.index("fts")
        if index + 1 < len(parts):
            return parts[index + 1]
    parent = Path(test_cases_dir).parent
    return parent.name if parent.name else "unknown"


def _report_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return Path(out_dir) / f"{IMPACT_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _summary_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return Path(out_dir) / f"{IMPACT_SUMMARY_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _markdown_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return Path(out_dir) / f"{IMPACT_PREFIX}.{old_source_version}-to-{new_source_version}.md"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
