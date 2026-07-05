from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.impact_analysis import ImpactEntry, load_impact_report
from test_case_agent.requirements_diff import RequirementsDiffEntry, load_requirements_diff
from test_case_agent.test_case_update_plan import UpdatePlanItem, load_test_case_update_plan
from test_case_agent.writer_dry_run_proposals import (
    TRACEABILITY_LABELS,
    TC_HEADING_RE,
    WriterDryRunProposal,
    load_writer_dry_run_proposal,
)
from test_case_agent.writer_package_tasks import load_writer_package_tasks

CREATED_BY_TOOL = "test_case_agent.traceability_mismatch_diagnostics"
DIAGNOSTICS_PREFIX = "traceability-mismatch-diagnostics"

DiagnosticStatus = Literal["pass", "pass-with-warnings", "blocked"]
MismatchType = Literal[
    "old_req_uid_not_present_in_tc",
    "source_req_id_not_present_in_tc",
    "tc_has_legacy_refs_only",
    "tc_has_no_traceability_refs",
    "impact_linked_by_tc_but_refs_absent",
    "req_uid_generated_after_tc_creation",
    "unknown",
]

REQ_UID_RE = re.compile(r"\bREQ-[A-Z0-9-]+\b")
SOURCE_REQ_ID_RE = re.compile(r"\b(?:BSR\s+\d+|GSR\s+\d+|SRC-\d+|ATOM-\d+|GAP-\d+|DICT-[A-Z0-9-]+|WP-\d+|ID\s+\d+)\b", re.IGNORECASE)
LEGACY_REF_RE = re.compile(r"\b(?:BSR\s+\d+|GSR\s+\d+|SRC-\d+|ATOM-\d+|GAP-\d+|DICT-[A-Z0-9-]+|WP-\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class TraceabilityMismatch:
    package_id: str
    test_case_id: str
    file_path: str
    plan_item_id: str
    impact_id: str
    change_id: str
    action: str
    old_refs: list[str]
    new_refs: list[str]
    current_traceability_line: str | None
    parsed_refs_from_traceability_line: list[str]
    missing_old_refs: list[str]
    refs_present_in_tc_but_not_in_plan: list[str]
    old_source_req_id: str | None
    new_source_req_id: str | None
    old_req_uid: str | None
    new_req_uid: str | None
    impact_change_type: str | None
    diff_change_type: str | None
    mismatch_type: MismatchType
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "test_case_id": self.test_case_id,
            "file_path": self.file_path,
            "plan_item_id": self.plan_item_id,
            "impact_id": self.impact_id,
            "change_id": self.change_id,
            "action": self.action,
            "old_refs": self.old_refs,
            "new_refs": self.new_refs,
            "current_traceability_line": self.current_traceability_line,
            "parsed_refs_from_traceability_line": self.parsed_refs_from_traceability_line,
            "missing_old_refs": self.missing_old_refs,
            "refs_present_in_tc_but_not_in_plan": self.refs_present_in_tc_but_not_in_plan,
            "old_source_req_id": self.old_source_req_id,
            "new_source_req_id": self.new_source_req_id,
            "old_req_uid": self.old_req_uid,
            "new_req_uid": self.new_req_uid,
            "impact_change_type": self.impact_change_type,
            "diff_change_type": self.diff_change_type,
            "mismatch_type": self.mismatch_type,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityMismatch":
        return cls(
            package_id=str(data["package_id"]),
            test_case_id=str(data["test_case_id"]),
            file_path=str(data["file_path"]),
            plan_item_id=str(data["plan_item_id"]),
            impact_id=str(data["impact_id"]),
            change_id=str(data["change_id"]),
            action=str(data["action"]),
            old_refs=list(data.get("old_refs") or []),
            new_refs=list(data.get("new_refs") or []),
            current_traceability_line=data.get("current_traceability_line"),
            parsed_refs_from_traceability_line=list(data.get("parsed_refs_from_traceability_line") or []),
            missing_old_refs=list(data.get("missing_old_refs") or []),
            refs_present_in_tc_but_not_in_plan=list(data.get("refs_present_in_tc_but_not_in_plan") or []),
            old_source_req_id=data.get("old_source_req_id"),
            new_source_req_id=data.get("new_source_req_id"),
            old_req_uid=data.get("old_req_uid"),
            new_req_uid=data.get("new_req_uid"),
            impact_change_type=data.get("impact_change_type"),
            diff_change_type=data.get("diff_change_type"),
            mismatch_type=data["mismatch_type"],
            notes=list(data.get("notes") or []),
        )


@dataclass
class TraceabilityMismatchDiagnosticsReport:
    old_source_version: str
    new_source_version: str
    created_at_utc: str
    created_by_tool: str
    input_paths: dict[str, Any]
    mismatches: list[TraceabilityMismatch]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "input_paths": self.input_paths,
            "mismatches": [mismatch.to_dict() for mismatch in self.mismatches],
            "summary": self.summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityMismatchDiagnosticsReport":
        return cls(
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            input_paths=dict(data.get("input_paths") or {}),
            mismatches=[TraceabilityMismatch.from_dict(item) for item in data.get("mismatches", [])],
            summary=dict(data.get("summary") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def build_traceability_mismatch_diagnostics(
    *,
    proposal_paths: list[Path],
    writer_package_tasks_path: Path,
    manual_update_packages_path: Path | None,
    update_plan_path: Path,
    impact_report_path: Path,
    requirements_diff_path: Path,
    test_cases_dir: Path,
    workspace_root: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> TraceabilityMismatchDiagnosticsReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    proposal_paths = [Path(path) for path in proposal_paths]
    writer_package_tasks_path = Path(writer_package_tasks_path)
    update_plan_path = Path(update_plan_path)
    impact_report_path = Path(impact_report_path)
    requirements_diff_path = Path(requirements_diff_path)
    test_cases_dir = Path(test_cases_dir)
    manual_update_packages_path = Path(manual_update_packages_path) if manual_update_packages_path is not None else None

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    proposals: list[WriterDryRunProposal] = []
    tasks_report = None
    update_plan = None
    impact_report = None
    diff_report = None

    for path in proposal_paths:
        if not path.exists():
            blocking_reasons.append(f"writer dry-run proposal is missing: {path}")
            continue
        try:
            proposal = load_writer_dry_run_proposal(path)
            proposals.append(proposal)
            warnings.extend(proposal.warnings)
        except Exception as exc:  # noqa: BLE001 - diagnostics report parse failures.
            blocking_reasons.append(f"writer dry-run proposal cannot be parsed: {path}: {exc}")

    if not writer_package_tasks_path.exists():
        blocking_reasons.append(f"writer package tasks file is missing: {writer_package_tasks_path}")
    else:
        try:
            tasks_report = load_writer_package_tasks(writer_package_tasks_path)
            warnings.extend(tasks_report.warnings)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"writer package tasks file cannot be parsed: {writer_package_tasks_path}: {exc}")

    for label, path in [
        ("manual update packages file", manual_update_packages_path),
        ("test-case update plan file", update_plan_path),
        ("impact report file", impact_report_path),
        ("requirements diff file", requirements_diff_path),
    ]:
        if path is not None and not path.exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    if update_plan_path.exists():
        try:
            update_plan = load_test_case_update_plan(update_plan_path)
            warnings.extend(update_plan.warnings)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"test-case update plan cannot be parsed: {update_plan_path}: {exc}")

    if impact_report_path.exists():
        try:
            impact_report = load_impact_report(impact_report_path)
            warnings.extend(impact_report.warnings)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"impact report cannot be parsed: {impact_report_path}: {exc}")

    if requirements_diff_path.exists():
        try:
            diff_report = load_requirements_diff(requirements_diff_path)
            warnings.extend(diff_report.warnings)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"requirements diff cannot be parsed: {requirements_diff_path}: {exc}")

    old_source_version, new_source_version = _infer_versions(
        proposals=proposals,
        tasks_report=tasks_report,
        update_plan=update_plan,
    )

    mismatches: list[TraceabilityMismatch] = []
    if not blocking_reasons and update_plan is not None and impact_report is not None and diff_report is not None:
        plan_items_by_id = {item.plan_item_id: item for item in update_plan.plan_items}
        impact_by_id = {entry.impact_id: entry for entry in impact_report.impact_entries}
        diff_by_id = {entry.change_id: entry for entry in diff_report.entries}
        for proposal in proposals:
            proposal_blockers = _proposal_blocking_reasons(proposal)
            if proposal_blockers:
                blocking_reasons.extend(proposal_blockers)
                continue
            mismatches.extend(
                _diagnose_proposal(
                    proposal=proposal,
                    plan_items_by_id=plan_items_by_id,
                    impact_by_id=impact_by_id,
                    diff_by_id=diff_by_id,
                    test_cases_dir=test_cases_dir,
                    workspace_root=workspace_root,
                )
            )

    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    summary = _summary(
        mismatches=mismatches,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )
    return TraceabilityMismatchDiagnosticsReport(
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        input_paths={
            "proposal_paths": [str(path) for path in proposal_paths],
            "writer_package_tasks_path": str(writer_package_tasks_path),
            "manual_update_packages_path": str(manual_update_packages_path) if manual_update_packages_path is not None else None,
            "update_plan_path": str(update_plan_path),
            "impact_report_path": str(impact_report_path),
            "requirements_diff_path": str(requirements_diff_path),
            "test_cases_dir": str(test_cases_dir),
        },
        mismatches=mismatches,
        summary=summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def write_traceability_mismatch_diagnostics(
    report: TraceabilityMismatchDiagnosticsReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{DIAGNOSTICS_PREFIX}.{report.old_source_version}-to-{report.new_source_version}.json"
    markdown_path = out_dir / f"{DIAGNOSTICS_PREFIX}.{report.old_source_version}-to-{report.new_source_version}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_traceability_mismatch_diagnostics_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_traceability_mismatch_diagnostics(path: Path) -> TraceabilityMismatchDiagnosticsReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Traceability mismatch diagnostics root must be a JSON object.")
    return TraceabilityMismatchDiagnosticsReport.from_dict(payload)


def render_traceability_mismatch_diagnostics_markdown(report: TraceabilityMismatchDiagnosticsReport) -> str:
    lines = [
        "# Traceability Mismatch Diagnostics",
        "",
        "## Summary",
        "",
        f"- Diagnostic status: `{report.summary['diagnostic_status']}`",
        f"- Mismatches total: `{report.summary['mismatches_total']}`",
        f"- Packages analyzed: `{', '.join(report.summary['packages_analyzed']) or 'none'}`",
        f"- Test cases analyzed: `{', '.join(report.summary['test_cases_analyzed']) or 'none'}`",
        f"- Mismatch type counts: `{json.dumps(report.summary['mismatch_type_counts'], ensure_ascii=False)}`",
        f"- Old ref type counts: `{json.dumps(report.summary['old_ref_type_counts'], ensure_ascii=False)}`",
        f"- TC ref type counts: `{json.dumps(report.summary['tc_ref_type_counts'], ensure_ascii=False)}`",
        "",
        "## Recommendations",
        "",
    ]
    for recommendation in report.summary["recommendations"]:
        lines.append(f"- {recommendation}")
    lines.extend(["", "## Mismatches", ""])
    if not report.mismatches:
        lines.append("- none")
    for mismatch in report.mismatches:
        lines.extend([
            f"### {mismatch.package_id} / {mismatch.test_case_id} / {mismatch.plan_item_id}",
            "",
            f"- File: `{mismatch.file_path}`",
            f"- Action: `{mismatch.action}`",
            f"- Change: `{mismatch.change_id}` / `{mismatch.impact_change_type or mismatch.diff_change_type or 'unknown'}`",
            f"- Old refs: `{', '.join(mismatch.old_refs) or 'none'}`",
            f"- New refs: `{', '.join(mismatch.new_refs) or 'none'}`",
            f"- Traceability line: `{mismatch.current_traceability_line or 'n/a'}`",
            f"- Parsed refs: `{', '.join(mismatch.parsed_refs_from_traceability_line) or 'none'}`",
            f"- Missing old refs: `{', '.join(mismatch.missing_old_refs) or 'none'}`",
            f"- Extra TC refs: `{', '.join(mismatch.refs_present_in_tc_but_not_in_plan) or 'none'}`",
            f"- old_source_req_id/new_source_req_id: `{mismatch.old_source_req_id or 'n/a'}` / `{mismatch.new_source_req_id or 'n/a'}`",
            f"- old_req_uid/new_req_uid: `{mismatch.old_req_uid or 'n/a'}` / `{mismatch.new_req_uid or 'n/a'}`",
            f"- mismatch_type: `{mismatch.mismatch_type}`",
            "",
        ])
    if report.blocking_reasons:
        lines.extend(["## Blocking Reasons", ""])
        for reason in report.blocking_reasons:
            lines.append(f"- {reason}")
    lines.extend(["## Safety", ""])
    lines.append("- Diagnostic only; canonical test-case files are not modified.")
    lines.append("- Patches are not applied.")
    lines.append("- `--apply` is not used.")
    return "\n".join(lines).rstrip() + "\n"


def _diagnose_proposal(
    *,
    proposal: WriterDryRunProposal,
    plan_items_by_id: dict[str, UpdatePlanItem],
    impact_by_id: dict[str, ImpactEntry],
    diff_by_id: dict[str, RequirementsDiffEntry],
    test_cases_dir: Path,
    workspace_root: Path,
) -> list[TraceabilityMismatch]:
    if proposal.file_path is None:
        return []
    tc_file = _resolve_task_file(proposal.file_path, workspace_root)
    test_cases_root = _resolve_task_file(test_cases_dir, workspace_root)
    if not _is_relative_to(tc_file, test_cases_root) or not tc_file.exists():
        return []
    content = tc_file.read_text(encoding="utf-8")
    block_index = _index_tc_blocks(content.splitlines(keepends=True))
    result: list[TraceabilityMismatch] = []
    for plan_item_id in proposal.source_plan_item_ids:
        plan_item = plan_items_by_id.get(plan_item_id)
        if plan_item is None or plan_item.test_case_id is None:
            continue
        if plan_item.test_case_id not in proposal.affected_test_case_ids:
            continue
        blocks = block_index.get(plan_item.test_case_id, [])
        block_text = blocks[0].text if len(blocks) == 1 else proposal.original_tc_blocks.get(plan_item.test_case_id, "")
        traceability_lines = _traceability_lines(block_text)
        current_traceability_line = traceability_lines[0] if traceability_lines else None
        parsed_refs = _parse_refs(current_traceability_line or "")
        missing_old_refs = [
            ref for ref in plan_item.old_refs
            if ref and not _contains_ref(parsed_refs, ref)
        ]
        if not missing_old_refs:
            continue
        impact = impact_by_id.get(plan_item.impact_id)
        diff = diff_by_id.get(plan_item.change_id)
        old_source_req_id = _first_non_empty(
            getattr(impact, "old_source_req_id", None) if impact else None,
            getattr(diff, "old_source_req_id", None) if diff else None,
        )
        new_source_req_id = _first_non_empty(
            getattr(impact, "new_source_req_id", None) if impact else None,
            getattr(diff, "new_source_req_id", None) if diff else None,
        )
        old_req_uid = _first_non_empty(
            getattr(impact, "old_req_uid", None) if impact else None,
            getattr(diff, "old_req_uid", None) if diff else None,
        )
        new_req_uid = _first_non_empty(
            getattr(impact, "new_req_uid", None) if impact else None,
            getattr(diff, "new_req_uid", None) if diff else None,
        )
        refs_present_in_tc_but_not_in_plan = [
            ref for ref in parsed_refs
            if ref not in plan_item.old_refs and ref not in plan_item.new_refs
        ]
        mismatch_type = _classify_mismatch(
            old_refs=plan_item.old_refs,
            parsed_refs=parsed_refs,
            current_traceability_line=current_traceability_line,
            missing_old_refs=missing_old_refs,
            old_source_req_id=old_source_req_id,
            old_req_uid=old_req_uid,
            impact=impact,
        )
        result.append(TraceabilityMismatch(
            package_id=proposal.package_id,
            test_case_id=plan_item.test_case_id,
            file_path=proposal.file_path,
            plan_item_id=plan_item.plan_item_id,
            impact_id=plan_item.impact_id,
            change_id=plan_item.change_id,
            action=plan_item.action,
            old_refs=plan_item.old_refs,
            new_refs=plan_item.new_refs,
            current_traceability_line=current_traceability_line,
            parsed_refs_from_traceability_line=parsed_refs,
            missing_old_refs=missing_old_refs,
            refs_present_in_tc_but_not_in_plan=refs_present_in_tc_but_not_in_plan,
            old_source_req_id=old_source_req_id,
            new_source_req_id=new_source_req_id,
            old_req_uid=old_req_uid,
            new_req_uid=new_req_uid,
            impact_change_type=getattr(impact, "change_type", None) if impact else None,
            diff_change_type=getattr(diff, "change_type", None) if diff else None,
            mismatch_type=mismatch_type,
            notes=_notes_for_mismatch(
                parsed_refs=parsed_refs,
                old_refs=plan_item.old_refs,
                old_source_req_id=old_source_req_id,
                old_req_uid=old_req_uid,
            ),
        ))
    return result


def _summary(
    *,
    mismatches: list[TraceabilityMismatch],
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    mismatch_type_counts = Counter(mismatch.mismatch_type for mismatch in mismatches)
    old_ref_type_counts = Counter(
        _ref_type(ref)
        for mismatch in mismatches
        for ref in mismatch.old_refs
    )
    tc_ref_type_counts = Counter(
        _ref_type(ref)
        for mismatch in mismatches
        for ref in mismatch.parsed_refs_from_traceability_line
    )
    recommendations = _recommendations(mismatches)
    if blocking_reasons:
        diagnostic_status: DiagnosticStatus = "blocked"
    elif warnings or mismatches:
        diagnostic_status = "pass-with-warnings"
    else:
        diagnostic_status = "pass"
    return {
        "diagnostic_status": diagnostic_status,
        "mismatches_total": len(mismatches),
        "packages_analyzed": sorted({mismatch.package_id for mismatch in mismatches}),
        "test_cases_analyzed": sorted({mismatch.test_case_id for mismatch in mismatches}),
        "mismatch_type_counts": dict(sorted(mismatch_type_counts.items())),
        "old_ref_type_counts": dict(sorted(old_ref_type_counts.items())),
        "tc_ref_type_counts": dict(sorted(tc_ref_type_counts.items())),
        "recommendations": recommendations,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
    }


def _classify_mismatch(
    *,
    old_refs: list[str],
    parsed_refs: list[str],
    current_traceability_line: str | None,
    missing_old_refs: list[str],
    old_source_req_id: str | None,
    old_req_uid: str | None,
    impact: ImpactEntry | None,
) -> MismatchType:
    if current_traceability_line is not None and not parsed_refs:
        return "tc_has_no_traceability_refs"
    if old_source_req_id and not _contains_ref(parsed_refs, old_source_req_id):
        return "source_req_id_not_present_in_tc"
    if old_req_uid and not _contains_ref(parsed_refs, old_req_uid):
        if _contains_legacy_refs_only(parsed_refs) and any(_ref_type(ref) == "req_uid" for ref in old_refs):
            if _impact_link_has_source_req_id(impact, parsed_refs):
                return "req_uid_generated_after_tc_creation"
            return "tc_has_legacy_refs_only"
        return "old_req_uid_not_present_in_tc"
    if _contains_legacy_refs_only(parsed_refs) and any(_ref_type(ref) == "req_uid" for ref in missing_old_refs):
        return "tc_has_legacy_refs_only"
    if parsed_refs and missing_old_refs:
        return "impact_linked_by_tc_but_refs_absent"
    return "unknown"


def _recommendations(mismatches: list[TraceabilityMismatch]) -> list[str]:
    if not mismatches:
        return [
            "automatic traceability replacement is possible only for proposals whose old refs are already present in the TC traceability line.",
            "no backfill is required for the analyzed proposals.",
            "keep update plan ref strategy unchanged until a mismatch appears.",
            "impact linking is explainable for the analyzed proposals.",
            "next safe step: run writer dry-run proposals normally for additional small file-bound packages.",
        ]
    types = Counter(mismatch.mismatch_type for mismatch in mismatches)
    req_uid_missing = sum(
        1 for mismatch in mismatches
        if any(_ref_type(ref) == "req_uid" for ref in mismatch.missing_old_refs)
    )
    source_present = sum(
        1 for mismatch in mismatches
        if mismatch.old_source_req_id and _contains_ref(mismatch.parsed_refs_from_traceability_line, mismatch.old_source_req_id)
    )
    return [
        "automatic traceability replacement is not safe for these mismatches because generated old req_uid refs are absent from current TC traceability lines.",
        (
            "backfill existing TC traceability with req_uid before automatic replacement: recommended "
            f"for {req_uid_missing} mismatch entries, after manual validation of source anchors."
        ),
        (
            "update plan should include source_req_id-aware fallback for legacy TC traceability; "
            f"{source_present} mismatch entries still contain the old source_req_id in TC traceability."
        ),
        "impact linking should expose the exact matched TC refs, because current plan refs and current TC refs can differ while the TC is still correctly linked.",
        "next safe step: generate a dedicated traceability backfill proposal for small file-bound packages, or manually review these packages before any automatic replacement.",
        f"mismatch type distribution: {dict(sorted(types.items()))}.",
    ]


def _proposal_blocking_reasons(proposal: WriterDryRunProposal) -> list[str]:
    if proposal.proposal_status == "blocked":
        return [
            f"proposal {proposal.package_id} is blocked: {reason}"
            for reason in proposal.blocking_reasons
        ] or [f"proposal {proposal.package_id} is blocked."]
    return []


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


def _traceability_lines(block_text: str) -> list[str]:
    return [
        line.strip()
        for line in block_text.splitlines()
        if _is_traceability_line(line)
    ]


def _is_traceability_line(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(label) for label in TRACEABILITY_LABELS)


def _parse_refs(line: str) -> list[str]:
    return _unique([
        *REQ_UID_RE.findall(line),
        *(match.group(0).upper().replace("  ", " ") for match in SOURCE_REQ_ID_RE.finditer(line)),
    ])


def _contains_ref(refs: list[str], expected_ref: str | None) -> bool:
    if not expected_ref:
        return False
    return _normalize_ref(expected_ref) in {_normalize_ref(ref) for ref in refs}


def _contains_legacy_refs_only(refs: list[str]) -> bool:
    return bool(refs) and all(_ref_type(ref) != "req_uid" for ref in refs)


def _impact_link_has_source_req_id(impact: ImpactEntry | None, parsed_refs: list[str]) -> bool:
    if impact is None:
        return False
    return any(
        _contains_ref(parsed_refs, source_req_id)
        for test_case in impact.affected_test_cases
        for source_req_id in test_case.linked_source_req_ids
    )


def _notes_for_mismatch(
    *,
    parsed_refs: list[str],
    old_refs: list[str],
    old_source_req_id: str | None,
    old_req_uid: str | None,
) -> list[str]:
    notes: list[str] = []
    if old_req_uid and not _contains_ref(parsed_refs, old_req_uid):
        notes.append("old generated req_uid is absent from current TC traceability.")
    if old_source_req_id and _contains_ref(parsed_refs, old_source_req_id):
        notes.append("current TC traceability still contains the old source_req_id.")
    if any(_ref_type(ref) == "req_uid" for ref in old_refs) and _contains_legacy_refs_only(parsed_refs):
        notes.append("TC traceability appears to use legacy refs rather than generated req_uid.")
    return notes


def _ref_type(ref: str) -> str:
    normalized = _normalize_ref(ref)
    if normalized.startswith("REQ-"):
        return "req_uid"
    if normalized.startswith("BSR "):
        return "bsr"
    if normalized.startswith("GSR "):
        return "gsr"
    if normalized.startswith("ATOM-"):
        return "atom"
    if normalized.startswith("SRC-"):
        return "src"
    if normalized.startswith("GAP-"):
        return "gap"
    if normalized.startswith("DICT-"):
        return "dict"
    if normalized.startswith("WP-"):
        return "work_package"
    return "other"


def _normalize_ref(ref: str) -> str:
    return re.sub(r"\s+", " ", str(ref).strip().upper())


def _infer_versions(
    *,
    proposals: list[WriterDryRunProposal],
    tasks_report: Any,
    update_plan: Any,
) -> tuple[str, str]:
    if tasks_report is not None:
        return tasks_report.old_source_version, tasks_report.new_source_version
    if update_plan is not None:
        return update_plan.old_source_version, update_plan.new_source_version
    for proposal in proposals:
        path = proposal.input_paths.get("update_plan_path")
        if path:
            stem = Path(path).stem
            prefix = "test-case-update-plan."
            if stem.startswith(prefix) and "-to-" in stem:
                return tuple(stem[len(prefix):].split("-to-", 1))  # type: ignore[return-value]
    return "unknown-old", "unknown-new"


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _resolve_task_file(path: str | Path, workspace_root: Path) -> Path:
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
