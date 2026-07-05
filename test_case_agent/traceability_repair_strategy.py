from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.impact_analysis import ImpactEntry, load_impact_report
from test_case_agent.requirements_diff import RequirementsDiffEntry, load_requirements_diff
from test_case_agent.test_case_update_plan import UpdatePlanItem, load_test_case_update_plan
from test_case_agent.traceability_mismatch_diagnostics import (
    LEGACY_REF_RE,
    REQ_UID_RE,
    SOURCE_REQ_ID_RE,
    TraceabilityMismatch,
    load_traceability_mismatch_diagnostics,
)
from test_case_agent.writer_dry_run_proposals import WriterDryRunProposal, load_writer_dry_run_proposal

CREATED_BY_TOOL = "test_case_agent.traceability_repair_strategy"
STRATEGY_PREFIX = "traceability-repair-strategy"

StrategyStatus = Literal["pass", "pass-with-warnings", "blocked"]
RecommendedStrategy = Literal[
    "no_auto_repair",
    "source_req_id_fallback",
    "req_uid_backfill_proposal",
    "manual_review_only",
    "mixed",
]
RepairConfidence = Literal["high", "medium", "low"]
AllowedNextAction = Literal[
    "create_backfill_proposal",
    "use_source_req_id_fallback",
    "manual_review_only",
    "no_action",
]


@dataclass(frozen=True)
class TraceabilityRepairItem:
    repair_item_id: str
    package_id: str
    test_case_id: str
    file_path: str
    mismatch_type: str
    current_traceability_line: str | None
    legacy_refs_present: list[str]
    missing_req_uids: list[str]
    candidate_req_uids_to_backfill: list[str]
    source_req_ids_supporting_candidate: list[str]
    confidence: RepairConfidence
    requires_manual_validation: bool
    allowed_next_action: AllowedNextAction
    rationale: list[str]
    warnings: list[str]
    plan_item_id: str
    impact_id: str
    change_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "repair_item_id": self.repair_item_id,
            "package_id": self.package_id,
            "test_case_id": self.test_case_id,
            "file_path": self.file_path,
            "mismatch_type": self.mismatch_type,
            "current_traceability_line": self.current_traceability_line,
            "legacy_refs_present": self.legacy_refs_present,
            "missing_req_uids": self.missing_req_uids,
            "candidate_req_uids_to_backfill": self.candidate_req_uids_to_backfill,
            "source_req_ids_supporting_candidate": self.source_req_ids_supporting_candidate,
            "confidence": self.confidence,
            "requires_manual_validation": self.requires_manual_validation,
            "allowed_next_action": self.allowed_next_action,
            "rationale": self.rationale,
            "warnings": self.warnings,
            "plan_item_id": self.plan_item_id,
            "impact_id": self.impact_id,
            "change_id": self.change_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityRepairItem":
        return cls(
            repair_item_id=str(data["repair_item_id"]),
            package_id=str(data["package_id"]),
            test_case_id=str(data["test_case_id"]),
            file_path=str(data["file_path"]),
            mismatch_type=str(data["mismatch_type"]),
            current_traceability_line=data.get("current_traceability_line"),
            legacy_refs_present=list(data.get("legacy_refs_present") or []),
            missing_req_uids=list(data.get("missing_req_uids") or []),
            candidate_req_uids_to_backfill=list(data.get("candidate_req_uids_to_backfill") or []),
            source_req_ids_supporting_candidate=list(data.get("source_req_ids_supporting_candidate") or []),
            confidence=data["confidence"],
            requires_manual_validation=bool(data["requires_manual_validation"]),
            allowed_next_action=data["allowed_next_action"],
            rationale=list(data.get("rationale") or []),
            warnings=list(data.get("warnings") or []),
            plan_item_id=str(data["plan_item_id"]),
            impact_id=str(data["impact_id"]),
            change_id=str(data["change_id"]),
        )


@dataclass
class TraceabilityRepairStrategyReport:
    old_source_version: str
    new_source_version: str
    created_at_utc: str
    created_by_tool: str
    input_paths: dict[str, Any]
    strategy_status: StrategyStatus
    recommended_strategy: RecommendedStrategy
    automatic_replacement_allowed: bool
    backfill_recommended: bool
    source_req_id_fallback_recommended: bool
    affected_packages: list[str]
    affected_test_cases: list[str]
    repair_items: list[TraceabilityRepairItem]
    summary: dict[str, Any]
    recommendations: list[str]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "input_paths": self.input_paths,
            "strategy_status": self.strategy_status,
            "recommended_strategy": self.recommended_strategy,
            "automatic_replacement_allowed": self.automatic_replacement_allowed,
            "backfill_recommended": self.backfill_recommended,
            "source_req_id_fallback_recommended": self.source_req_id_fallback_recommended,
            "affected_packages": self.affected_packages,
            "affected_test_cases": self.affected_test_cases,
            "repair_items": [item.to_dict() for item in self.repair_items],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceabilityRepairStrategyReport":
        return cls(
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            input_paths=dict(data.get("input_paths") or {}),
            strategy_status=data["strategy_status"],
            recommended_strategy=data["recommended_strategy"],
            automatic_replacement_allowed=bool(data["automatic_replacement_allowed"]),
            backfill_recommended=bool(data["backfill_recommended"]),
            source_req_id_fallback_recommended=bool(data["source_req_id_fallback_recommended"]),
            affected_packages=list(data.get("affected_packages") or []),
            affected_test_cases=list(data.get("affected_test_cases") or []),
            repair_items=[
                TraceabilityRepairItem.from_dict(item)
                for item in data.get("repair_items", [])
            ],
            summary=dict(data.get("summary") or {}),
            recommendations=list(data.get("recommendations") or []),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


def build_traceability_repair_strategy(
    *,
    diagnostics_path: Path,
    proposal_paths: list[Path],
    update_plan_path: Path,
    impact_report_path: Path,
    requirements_diff_path: Path,
    old_registry_path: Path,
    new_registry_path: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> TraceabilityRepairStrategyReport:
    diagnostics_path = Path(diagnostics_path)
    proposal_paths = [Path(path) for path in proposal_paths]
    update_plan_path = Path(update_plan_path)
    impact_report_path = Path(impact_report_path)
    requirements_diff_path = Path(requirements_diff_path)
    old_registry_path = Path(old_registry_path)
    new_registry_path = Path(new_registry_path)

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    diagnostics = None
    update_plan = None
    impact_report = None
    diff_report = None
    proposals: list[WriterDryRunProposal] = []
    old_registry_by_req_uid: dict[str, list[dict[str, Any]]] = {}
    new_registry_by_req_uid: dict[str, list[dict[str, Any]]] = {}

    for label, path in [
        ("traceability mismatch diagnostics", diagnostics_path),
        ("test-case update plan", update_plan_path),
        ("impact report", impact_report_path),
        ("requirements diff", requirements_diff_path),
        ("old requirements registry", old_registry_path),
        ("new requirements registry", new_registry_path),
    ]:
        if not path.exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    if diagnostics_path.exists():
        try:
            diagnostics = load_traceability_mismatch_diagnostics(diagnostics_path)
            warnings.extend(diagnostics.warnings)
            blocking_reasons.extend(diagnostics.blocking_reasons)
        except Exception as exc:  # noqa: BLE001 - strategy report must surface artifact parse failures.
            blocking_reasons.append(f"traceability mismatch diagnostics cannot be parsed: {diagnostics_path}: {exc}")

    for path in proposal_paths:
        if not path.exists():
            blocking_reasons.append(f"writer dry-run proposal is missing: {path}")
            continue
        try:
            proposal = load_writer_dry_run_proposal(path)
            proposals.append(proposal)
            warnings.extend(proposal.warnings)
            blocking_reasons.extend(proposal.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"writer dry-run proposal cannot be parsed: {path}: {exc}")

    if update_plan_path.exists():
        try:
            update_plan = load_test_case_update_plan(update_plan_path)
            warnings.extend(update_plan.warnings)
            blocking_reasons.extend(update_plan.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"test-case update plan cannot be parsed: {update_plan_path}: {exc}")

    if impact_report_path.exists():
        try:
            impact_report = load_impact_report(impact_report_path)
            warnings.extend(impact_report.warnings)
            blocking_reasons.extend(impact_report.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"impact report cannot be parsed: {impact_report_path}: {exc}")

    if requirements_diff_path.exists():
        try:
            diff_report = load_requirements_diff(requirements_diff_path)
            warnings.extend(diff_report.warnings)
            blocking_reasons.extend(diff_report.blocking_reasons)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"requirements diff cannot be parsed: {requirements_diff_path}: {exc}")

    if old_registry_path.exists():
        try:
            old_registry_by_req_uid = _load_registry_by_req_uid(old_registry_path)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"old requirements registry cannot be inspected: {old_registry_path}: {exc}")
    if new_registry_path.exists():
        try:
            new_registry_by_req_uid = _load_registry_by_req_uid(new_registry_path)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"new requirements registry cannot be inspected: {new_registry_path}: {exc}")

    old_source_version, new_source_version = _infer_versions(
        diagnostics=diagnostics,
        update_plan=update_plan,
        diff_report=diff_report,
    )
    proposals_by_package = {proposal.package_id: proposal for proposal in proposals}
    plan_items_by_id = {
        item.plan_item_id: item
        for item in update_plan.plan_items
    } if update_plan is not None else {}
    impact_by_id = {
        entry.impact_id: entry
        for entry in impact_report.impact_entries
    } if impact_report is not None else {}
    diff_by_id = {
        entry.change_id: entry
        for entry in diff_report.entries
    } if diff_report is not None else {}

    repair_items: list[TraceabilityRepairItem] = []
    if diagnostics is not None:
        for index, mismatch in enumerate(diagnostics.mismatches, start=1):
            repair_items.append(_repair_item(
                index=index,
                mismatch=mismatch,
                proposal=proposals_by_package.get(mismatch.package_id),
                plan_item=plan_items_by_id.get(mismatch.plan_item_id),
                impact=impact_by_id.get(mismatch.impact_id),
                diff=diff_by_id.get(mismatch.change_id),
                old_registry_by_req_uid=old_registry_by_req_uid,
                new_registry_by_req_uid=new_registry_by_req_uid,
            ))

    blocking_reasons = _unique(blocking_reasons)
    warnings = _unique(warnings)
    summary = _summary(
        repair_items=repair_items,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )
    recommendations = _recommendations(repair_items, blocking_reasons)
    return TraceabilityRepairStrategyReport(
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        input_paths={
            "diagnostics_path": str(diagnostics_path),
            "proposal_paths": [str(path) for path in proposal_paths],
            "update_plan_path": str(update_plan_path),
            "impact_report_path": str(impact_report_path),
            "requirements_diff_path": str(requirements_diff_path),
            "old_registry_path": str(old_registry_path),
            "new_registry_path": str(new_registry_path),
        },
        strategy_status=summary["strategy_status"],
        recommended_strategy=summary["recommended_strategy"],
        automatic_replacement_allowed=summary["automatic_replacement_allowed"],
        backfill_recommended=summary["backfill_recommended"],
        source_req_id_fallback_recommended=summary["source_req_id_fallback_recommended"],
        affected_packages=summary["affected_packages"],
        affected_test_cases=summary["affected_test_cases"],
        repair_items=repair_items,
        summary=summary,
        recommendations=recommendations,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def write_traceability_repair_strategy(
    report: TraceabilityRepairStrategyReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{STRATEGY_PREFIX}.{report.old_source_version}-to-{report.new_source_version}.json"
    markdown_path = out_dir / f"{STRATEGY_PREFIX}.{report.old_source_version}-to-{report.new_source_version}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_traceability_repair_strategy_markdown(report),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_traceability_repair_strategy(path: Path) -> TraceabilityRepairStrategyReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Traceability repair strategy root must be a JSON object.")
    return TraceabilityRepairStrategyReport.from_dict(payload)


def render_traceability_repair_strategy_markdown(report: TraceabilityRepairStrategyReport) -> str:
    lines = [
        "# Traceability Repair Strategy",
        "",
        "## Summary",
        "",
        f"- Strategy status: `{report.strategy_status}`",
        f"- Recommended strategy: `{report.recommended_strategy}`",
        f"- Automatic replacement allowed: `{str(report.automatic_replacement_allowed).lower()}`",
        f"- Backfill recommended: `{str(report.backfill_recommended).lower()}`",
        f"- Source req id fallback recommended: `{str(report.source_req_id_fallback_recommended).lower()}`",
        f"- Repair items total: `{report.summary['repair_items_total']}`",
        f"- Confidence counts: `{json.dumps(report.summary['confidence_counts'], ensure_ascii=False)}`",
        f"- Allowed next action counts: `{json.dumps(report.summary['allowed_next_action_counts'], ensure_ascii=False)}`",
        f"- Affected packages: `{', '.join(report.affected_packages) or 'none'}`",
        f"- Affected test cases: `{', '.join(report.affected_test_cases) or 'none'}`",
        "",
        "## Recommendations",
        "",
    ]
    for recommendation in report.recommendations:
        lines.append(f"- {recommendation}")
    lines.extend(["", "## Repair Items", ""])
    if not report.repair_items:
        lines.append("- none")
    for item in report.repair_items:
        lines.extend([
            f"### {item.repair_item_id}: {item.package_id} / {item.test_case_id}",
            "",
            f"- File: `{item.file_path}`",
            f"- Plan/impact/change: `{item.plan_item_id}` / `{item.impact_id}` / `{item.change_id}`",
            f"- Mismatch type: `{item.mismatch_type}`",
            f"- Current traceability line: `{item.current_traceability_line or 'n/a'}`",
            f"- Legacy refs present: `{', '.join(item.legacy_refs_present) or 'none'}`",
            f"- Missing req_uids: `{', '.join(item.missing_req_uids) or 'none'}`",
            f"- Candidate req_uids to backfill: `{', '.join(item.candidate_req_uids_to_backfill) or 'none'}`",
            f"- Supporting source_req_ids: `{', '.join(item.source_req_ids_supporting_candidate) or 'none'}`",
            f"- Confidence: `{item.confidence}`",
            f"- Requires manual validation: `{str(item.requires_manual_validation).lower()}`",
            f"- Allowed next action: `{item.allowed_next_action}`",
            "",
            "Rationale:",
        ])
        _append_list(lines, item.rationale)
        if item.warnings:
            lines.append("")
            lines.append("Warnings:")
            _append_list(lines, item.warnings)
        lines.append("")
    if report.blocking_reasons:
        lines.extend(["## Blocking Reasons", ""])
        _append_list(lines, report.blocking_reasons)
    lines.extend(["## Safety", ""])
    lines.append("- Strategy only; canonical test-case files are not read or modified.")
    lines.append("- Backfill is recommended only as a preview-only next step.")
    lines.append("- Patches are not applied.")
    lines.append("- `--apply` is not used.")
    return "\n".join(lines).rstrip() + "\n"


def _repair_item(
    *,
    index: int,
    mismatch: TraceabilityMismatch,
    proposal: WriterDryRunProposal | None,
    plan_item: UpdatePlanItem | None,
    impact: ImpactEntry | None,
    diff: RequirementsDiffEntry | None,
    old_registry_by_req_uid: dict[str, list[dict[str, Any]]],
    new_registry_by_req_uid: dict[str, list[dict[str, Any]]],
) -> TraceabilityRepairItem:
    legacy_refs = _legacy_refs(mismatch.parsed_refs_from_traceability_line)
    missing_req_uids = _req_uids(mismatch.missing_old_refs)
    supporting_source_req_ids = _supporting_source_req_ids(
        mismatch=mismatch,
        impact=impact,
        parsed_refs=mismatch.parsed_refs_from_traceability_line,
    )
    concrete_link = plan_item is not None and impact is not None and diff is not None
    file_bound_listed = _is_file_bound_listed(proposal, mismatch)
    registry_support = _registry_supports(
        mismatch=mismatch,
        missing_req_uids=missing_req_uids,
        supporting_source_req_ids=supporting_source_req_ids,
        old_registry_by_req_uid=old_registry_by_req_uid,
        new_registry_by_req_uid=new_registry_by_req_uid,
    )
    can_backfill = (
        bool(missing_req_uids)
        and concrete_link
        and file_bound_listed
        and bool(supporting_source_req_ids)
    )
    candidate_req_uids = missing_req_uids if can_backfill else []
    confidence = _confidence(
        can_backfill=can_backfill,
        registry_support=registry_support,
        supporting_source_req_ids=supporting_source_req_ids,
    )
    allowed_next_action = _allowed_next_action(
        can_backfill=can_backfill,
        confidence=confidence,
        supporting_source_req_ids=supporting_source_req_ids,
    )
    warnings = _repair_warnings(
        concrete_link=concrete_link,
        file_bound_listed=file_bound_listed,
        supporting_source_req_ids=supporting_source_req_ids,
        missing_req_uids=missing_req_uids,
    )
    return TraceabilityRepairItem(
        repair_item_id=f"TRPAIR-{index:06d}",
        package_id=mismatch.package_id,
        test_case_id=mismatch.test_case_id,
        file_path=mismatch.file_path,
        mismatch_type=mismatch.mismatch_type,
        current_traceability_line=mismatch.current_traceability_line,
        legacy_refs_present=legacy_refs,
        missing_req_uids=missing_req_uids,
        candidate_req_uids_to_backfill=candidate_req_uids,
        source_req_ids_supporting_candidate=supporting_source_req_ids,
        confidence=confidence,
        requires_manual_validation=True,
        allowed_next_action=allowed_next_action,
        rationale=_repair_rationale(
            mismatch=mismatch,
            can_backfill=can_backfill,
            registry_support=registry_support,
            supporting_source_req_ids=supporting_source_req_ids,
            allowed_next_action=allowed_next_action,
        ),
        warnings=warnings,
        plan_item_id=mismatch.plan_item_id,
        impact_id=mismatch.impact_id,
        change_id=mismatch.change_id,
    )


def _summary(
    *,
    repair_items: list[TraceabilityRepairItem],
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    confidence_counts = Counter(item.confidence for item in repair_items)
    action_counts = Counter(item.allowed_next_action for item in repair_items)
    affected_packages = sorted({item.package_id for item in repair_items})
    affected_test_cases = sorted({item.test_case_id for item in repair_items})
    automatic_replacement_allowed = False
    backfill_recommended = action_counts.get("create_backfill_proposal", 0) > 0
    source_req_id_fallback_recommended = any(
        item.source_req_ids_supporting_candidate and item.missing_req_uids
        for item in repair_items
    )
    recommended_strategy = _recommended_strategy(
        repair_items=repair_items,
        backfill_recommended=backfill_recommended,
        source_req_id_fallback_recommended=source_req_id_fallback_recommended,
    )
    if blocking_reasons:
        strategy_status: StrategyStatus = "blocked"
    elif warnings or repair_items:
        strategy_status = "pass-with-warnings"
    else:
        strategy_status = "pass"
    return {
        "strategy_status": strategy_status,
        "recommended_strategy": recommended_strategy,
        "automatic_replacement_allowed": automatic_replacement_allowed,
        "backfill_recommended": backfill_recommended,
        "source_req_id_fallback_recommended": source_req_id_fallback_recommended,
        "repair_items_total": len(repair_items),
        "affected_packages": affected_packages,
        "affected_test_cases": affected_test_cases,
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "allowed_next_action_counts": dict(sorted(action_counts.items())),
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
    }


def _recommended_strategy(
    *,
    repair_items: list[TraceabilityRepairItem],
    backfill_recommended: bool,
    source_req_id_fallback_recommended: bool,
) -> RecommendedStrategy:
    if not repair_items:
        return "no_auto_repair"
    manual_only_count = sum(1 for item in repair_items if item.allowed_next_action == "manual_review_only")
    if manual_only_count == len(repair_items):
        return "manual_review_only"
    if backfill_recommended and source_req_id_fallback_recommended:
        return "mixed"
    if backfill_recommended:
        return "req_uid_backfill_proposal"
    if source_req_id_fallback_recommended:
        return "source_req_id_fallback"
    return "no_auto_repair"


def _recommendations(
    repair_items: list[TraceabilityRepairItem],
    blocking_reasons: list[str],
) -> list[str]:
    if blocking_reasons:
        return [
            "strategy is blocked until required input artifacts can be loaded.",
            "do not run automatic traceability replacement while repair strategy is blocked.",
            "next safe step: fix or rebuild the missing/invalid diagnostic artifacts.",
        ]
    if not repair_items:
        return [
            "no traceability repair items were found for the analyzed diagnostics.",
            "automatic replacement remains allowed only for writer proposals whose old refs already exist in the TC traceability line.",
            "next safe step: continue writer dry-run proposals for additional small file-bound packages.",
        ]
    backfill_count = sum(1 for item in repair_items if item.allowed_next_action == "create_backfill_proposal")
    manual_count = sum(1 for item in repair_items if item.allowed_next_action == "manual_review_only")
    fallback_supported = sum(1 for item in repair_items if item.source_req_ids_supporting_candidate)
    return [
        "automatic traceability replacement must remain disabled: generated REQ-* old refs are absent from the current TC traceability lines.",
        (
            "source_req_id-aware fallback is useful as evidence for mapping, but it should not silently rewrite traceability "
            f"because {fallback_supported} repair items still require manual validation."
        ),
        (
            "req_uid backfill proposal is the safest next step for file-bound packages with legacy source_req_id support; "
            f"{backfill_count} repair items are eligible for preview-only backfill proposal generation."
        ),
        (
            "low-confidence mappings must stay manual-only; "
            f"{manual_count} repair items currently require manual review only."
        ),
        "do not change canonical test-case files until a separate preview-only backfill proposal is reviewed.",
    ]


def _legacy_refs(refs: list[str]) -> list[str]:
    return _unique([
        ref
        for ref in refs
        if _ref_type(ref) != "req_uid" and LEGACY_REF_RE.search(ref)
    ])


def _req_uids(refs: list[str]) -> list[str]:
    return _unique([
        match.group(0).upper()
        for ref in refs
        for match in REQ_UID_RE.finditer(ref)
    ])


def _supporting_source_req_ids(
    *,
    mismatch: TraceabilityMismatch,
    impact: ImpactEntry | None,
    parsed_refs: list[str],
) -> list[str]:
    candidates: list[str] = []
    if mismatch.old_source_req_id:
        candidates.append(mismatch.old_source_req_id)
    if mismatch.new_source_req_id:
        candidates.append(mismatch.new_source_req_id)
    for ref in mismatch.old_refs + mismatch.new_refs:
        if SOURCE_REQ_ID_RE.fullmatch(ref.strip()):
            candidates.append(ref)
    if impact is not None:
        for test_case in impact.affected_test_cases:
            if test_case.test_case_id != mismatch.test_case_id:
                continue
            candidates.extend(test_case.linked_source_req_ids)
    return _unique([
        _normalize_ref(candidate)
        for candidate in candidates
        if _contains_ref(parsed_refs, candidate)
    ])


def _registry_supports(
    *,
    mismatch: TraceabilityMismatch,
    missing_req_uids: list[str],
    supporting_source_req_ids: list[str],
    old_registry_by_req_uid: dict[str, list[dict[str, Any]]],
    new_registry_by_req_uid: dict[str, list[dict[str, Any]]],
) -> bool:
    if not missing_req_uids or not supporting_source_req_ids:
        return False
    support_set = {_normalize_ref(ref) for ref in supporting_source_req_ids}
    old_support = any(
        _entry_source_req_id_supported(entry, support_set)
        for req_uid in missing_req_uids
        for entry in old_registry_by_req_uid.get(_normalize_ref(req_uid), [])
    )
    if not old_support:
        return False
    if not mismatch.new_req_uid:
        return True
    if not mismatch.new_req_uid:
        return True
    new_entries = new_registry_by_req_uid.get(_normalize_ref(mismatch.new_req_uid), [])
    if not new_entries:
        return True
    return any(
        _entry_source_req_id_supported(entry, support_set)
        for entry in new_entries
    )


def _entry_source_req_id_supported(entry: dict[str, Any], support_set: set[str]) -> bool:
    source_req_id = entry.get("source_req_id")
    return bool(source_req_id and _normalize_ref(str(source_req_id)) in support_set)


def _confidence(
    *,
    can_backfill: bool,
    registry_support: bool,
    supporting_source_req_ids: list[str],
) -> RepairConfidence:
    if not can_backfill:
        return "low"
    if registry_support and supporting_source_req_ids:
        return "high"
    return "medium"


def _allowed_next_action(
    *,
    can_backfill: bool,
    confidence: RepairConfidence,
    supporting_source_req_ids: list[str],
) -> AllowedNextAction:
    if can_backfill and confidence in {"high", "medium"}:
        return "create_backfill_proposal"
    if supporting_source_req_ids and confidence != "low":
        return "use_source_req_id_fallback"
    if confidence == "low":
        return "manual_review_only"
    return "no_action"


def _repair_warnings(
    *,
    concrete_link: bool,
    file_bound_listed: bool,
    supporting_source_req_ids: list[str],
    missing_req_uids: list[str],
) -> list[str]:
    warnings: list[str] = []
    if not concrete_link:
        warnings.append("repair item is missing a concrete plan/impact/diff link.")
    if not file_bound_listed:
        warnings.append("repair item is not backed by a file-bound listed writer proposal.")
    if missing_req_uids and not supporting_source_req_ids:
        warnings.append("missing REQ-* refs have no supporting legacy source_req_id in the current traceability line.")
    return warnings


def _repair_rationale(
    *,
    mismatch: TraceabilityMismatch,
    can_backfill: bool,
    registry_support: bool,
    supporting_source_req_ids: list[str],
    allowed_next_action: AllowedNextAction,
) -> list[str]:
    rationale = [
        "automatic replacement is unsafe because the old generated REQ-* ref is not present in the current TC traceability line.",
        f"mismatch type is {mismatch.mismatch_type}.",
    ]
    if supporting_source_req_ids:
        rationale.append(
            "current TC traceability still contains supporting legacy source_req_id refs: "
            + ", ".join(supporting_source_req_ids)
            + "."
        )
    if registry_support:
        rationale.append("requirements registry contains source_req_id support for the missing req_uid mapping.")
    if can_backfill:
        rationale.append("candidate req_uid backfill is allowed only as a preview-only next action with manual validation.")
    if allowed_next_action == "manual_review_only":
        rationale.append("mapping confidence is low, so no automated repair proposal should be generated.")
    return rationale


def _is_file_bound_listed(proposal: WriterDryRunProposal | None, mismatch: TraceabilityMismatch) -> bool:
    if proposal is None or proposal.file_path is None:
        return False
    return mismatch.test_case_id in proposal.affected_test_case_ids


def _load_registry_by_req_uid(path: Path) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError(f"registry line {line_number} is not a JSON object")
        req_uid = data.get("req_uid")
        if req_uid:
            result.setdefault(_normalize_ref(str(req_uid)), []).append(data)
    return result


def _infer_versions(
    *,
    diagnostics: Any,
    update_plan: Any,
    diff_report: Any,
) -> tuple[str, str]:
    if diagnostics is not None:
        return diagnostics.old_source_version, diagnostics.new_source_version
    if update_plan is not None:
        return update_plan.old_source_version, update_plan.new_source_version
    if diff_report is not None:
        return diff_report.old_source_version, diff_report.new_source_version
    return "unknown-old", "unknown-new"


def _ref_type(ref: str) -> str:
    normalized = _normalize_ref(ref)
    if normalized.startswith("REQ-"):
        return "req_uid"
    return "legacy"


def _contains_ref(refs: list[str], expected_ref: str | None) -> bool:
    if not expected_ref:
        return False
    expected = _normalize_ref(expected_ref)
    return expected in {_normalize_ref(ref) for ref in refs}


def _normalize_ref(ref: str) -> str:
    return " ".join(str(ref).strip().upper().split())


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
