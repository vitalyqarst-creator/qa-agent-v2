from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from test_case_agent.new_tc_create_apply_dry_run import load_new_tc_create_apply_dry_run

PREFIX = "new-tc-stage-9h-design-review-prep"
DEFAULT_PACKAGE_ID = "WPKG-000001"


@dataclass(frozen=True)
class NewTcStage9HDesignReviewPrepReport:
    package_id: str
    prep_status: str
    readiness_verdict: str
    source_stage_9g_json_path: str
    source_stage_9g_markdown_path: str
    warning_reviews: list[dict[str, Any]]
    item_readiness_reviews: list[dict[str, Any]]
    target_file_plan_review: dict[str, Any]
    tc_id_collision_review: dict[str, Any]
    aggregate_target_risk_review: dict[str, Any]
    safety_gate_summary: dict[str, Any]
    stage_9h_requires_explicit_user_approval: bool
    stage_9h_preparation_authorizes_real_apply: bool
    canonical_write_allowed: bool
    real_apply_authorized: bool
    input_paths: dict[str, str | None]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcStage9HDesignReviewPrepReport":
        return cls(
            package_id=str(data["package_id"]),
            prep_status=str(data["prep_status"]),
            readiness_verdict=str(data.get("readiness_verdict") or ""),
            source_stage_9g_json_path=str(data.get("source_stage_9g_json_path") or ""),
            source_stage_9g_markdown_path=str(data.get("source_stage_9g_markdown_path") or ""),
            warning_reviews=list(data.get("warning_reviews") or []),
            item_readiness_reviews=list(data.get("item_readiness_reviews") or []),
            target_file_plan_review=dict(data.get("target_file_plan_review") or {}),
            tc_id_collision_review=dict(data.get("tc_id_collision_review") or {}),
            aggregate_target_risk_review=dict(data.get("aggregate_target_risk_review") or {}),
            safety_gate_summary=dict(data.get("safety_gate_summary") or {}),
            stage_9h_requires_explicit_user_approval=bool(data.get("stage_9h_requires_explicit_user_approval")),
            stage_9h_preparation_authorizes_real_apply=bool(data.get("stage_9h_preparation_authorizes_real_apply")),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            real_apply_authorized=bool(data.get("real_apply_authorized")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_new_tc_stage_9h_design_review_prep(
    *,
    package_id: str,
    stage_9g_json_path: Path,
    stage_9g_markdown_path: Path,
    test_cases_dir: Path | None = None,
    created_by_tool: str = "test_case_agent.new_tc_stage_9h_design_review_prep",
) -> NewTcStage9HDesignReviewPrepReport:
    now = _utc_now()
    input_paths = {
        "stage_9g_json_path": str(stage_9g_json_path),
        "stage_9g_markdown_path": str(stage_9g_markdown_path),
        "test_cases_dir": str(test_cases_dir) if test_cases_dir else None,
    }
    blockers = _missing(stage_9g_json_path, stage_9g_markdown_path)
    if package_id != DEFAULT_PACKAGE_ID:
        blockers.append(f"Stage 9H prep is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if blockers:
        return _blocked(package_id, stage_9g_json_path, stage_9g_markdown_path, input_paths, blockers, now, created_by_tool)

    stage_9g = load_new_tc_create_apply_dry_run(stage_9g_json_path)
    items = stage_9g.dry_run_items
    if stage_9g.package_id != package_id:
        blockers.append(f"Stage 9G package_id mismatch: {stage_9g.package_id} != {package_id}")
    if stage_9g.real_apply_authorized:
        blockers.append("Stage 9G unexpectedly authorizes real apply")
    if stage_9g.canonical_write_allowed:
        blockers.append("Stage 9G unexpectedly allows canonical writes")
    if any(item.dry_run_decision == "blocked" for item in items):
        blockers.append("Stage 9G contains blocked dry-run items")

    warning_reviews = _warning_reviews(stage_9g.warnings, items)
    item_reviews = _item_reviews(items, warning_reviews)
    target_review = _target_review(stage_9g.target_file_plan)
    tc_review = _tc_review(stage_9g.tc_id_plan)
    aggregate_review = _aggregate_review(items)
    safety = _safety_summary(stage_9g, warning_reviews, item_reviews)
    for status, reason in (
        (target_review.get("status"), "target file plan is not safe for Stage 9H design"),
        (tc_review.get("status"), "TC ID collision review failed"),
        (aggregate_review.get("status"), "aggregate target risk review failed"),
        (safety.get("status"), "Stage 9H safety gate failed"),
    ):
        if status == "failed":
            blockers.append(reason)

    report_warnings = []
    if any(review["classification"] != "non_blocking_ack_required" for review in warning_reviews):
        report_warnings.append("one or more warnings require explicit resolution before real apply")
    if any(review["apply_readiness"] == "needs_extra_source_grounding" for review in item_reviews):
        report_warnings.append("one or more items require extra source grounding before real apply")
    status = "blocked" if blockers else ("pass-with-warnings" if report_warnings else "pass")
    return NewTcStage9HDesignReviewPrepReport(
        package_id=package_id,
        prep_status=status,
        readiness_verdict=(
            "blocked_for_stage_9h_design"
            if status == "blocked"
            else "ready_for_stage_9h_design_only_after_warning_review_and_source_grounding"
            if report_warnings
            else "ready_for_stage_9h_design_review_with_acknowledgement"
        ),
        source_stage_9g_json_path=str(stage_9g_json_path),
        source_stage_9g_markdown_path=str(stage_9g_markdown_path),
        warning_reviews=warning_reviews,
        item_readiness_reviews=item_reviews,
        target_file_plan_review=target_review,
        tc_id_collision_review=tc_review,
        aggregate_target_risk_review=aggregate_review,
        safety_gate_summary=safety,
        stage_9h_requires_explicit_user_approval=True,
        stage_9h_preparation_authorizes_real_apply=False,
        canonical_write_allowed=False,
        real_apply_authorized=False,
        input_paths=input_paths,
        warnings=_unique(report_warnings),
        blocking_reasons=_unique(blockers),
        created_at_utc=now,
        created_by_tool=created_by_tool,
    )


def write_new_tc_stage_9h_design_review_prep(report: NewTcStage9HDesignReviewPrepReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{PREFIX}-{report.package_id}.json"
    md_path = out_dir / f"{PREFIX}-{report.package_id}.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text(_markdown(report), encoding="utf-8-sig", newline="\n")
    return json_path, md_path


def load_new_tc_stage_9h_design_review_prep(path: Path) -> NewTcStage9HDesignReviewPrepReport:
    return NewTcStage9HDesignReviewPrepReport.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _warning_reviews(warnings: list[str], items: list[Any]) -> list[dict[str, Any]]:
    result = []
    for index, warning in enumerate(_unique(warnings), start=1):
        classification = _classify(warning)
        affected = [
            item.dry_run_item_id
            for item in items
            if warning in item.review_warnings or warning in item.format_warnings or warning in item.safety_warnings
        ]
        if not affected and "source_req_ids" in warning:
            affected = [item.dry_run_item_id for item in items if not item.source_req_ids]
        result.append(
            {
                "warning_id": f"9HW-{index:06d}",
                "warning_text": warning,
                "classification": classification,
                "affected_dry_run_item_ids": affected,
                "rationale": "Classified for Stage 9H design review; this does not authorize real apply.",
                "required_resolution_before_real_apply": _resolution(classification),
            }
        )
    return result


def _item_reviews(items: list[Any], warning_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_text = {item["warning_text"]: item["warning_id"] for item in warning_reviews}
    reviews = []
    for item in items:
        warnings = _unique([*item.review_warnings, *item.format_warnings, *item.safety_warnings])
        readiness = "ready_with_acknowledgement"
        reasons = []
        if item.dry_run_decision == "blocked" or item.safety_warnings:
            readiness = "blocked"
            reasons = item.safety_warnings or ["dry-run item is blocked"]
        elif not item.source_req_ids or any("source-backed navigation/action" in warning.casefold() for warning in warnings):
            readiness = "needs_extra_source_grounding"
            reasons = ["source_req_ids or source-backed action/navigation details are incomplete"]
        elif warnings:
            reasons = ["warnings require acknowledgement before future apply"]
        reviews.append(
            {
                "dry_run_item_id": item.dry_run_item_id,
                "source_revised_draft_id": item.source_revised_draft_id,
                "proposed_tc_id": item.proposed_tc_id,
                "target_file_path": item.target_file_path,
                "apply_readiness": readiness,
                "readiness_reasons": reasons,
                "warning_ids": [by_text[warning] for warning in warnings if warning in by_text],
                "source_req_ids_present": bool(item.source_req_ids),
                "req_uids_retained": bool(item.req_uids),
                "source_evidence_refs_retained": bool(item.source_evidence_refs),
                "real_apply_authorized": False,
                "canonical_write_allowed": False,
            }
        )
    return reviews


def _target_review(plan: dict[str, Any]) -> dict[str, Any]:
    targets = list(plan.get("targets") or [])
    paths = [str(target.get("target_file_path") or "") for target in targets]
    duplicate_paths = sorted(_duplicates(paths))
    invalid = [
        target
        for target in targets
        if target.get("planned_operation") != "create_new_file"
        or _is_aggregate_or_index(str(target.get("target_file_path") or ""))
    ]
    return {
        "status": "pass" if not invalid and not duplicate_paths else "failed",
        "creates_only_new_standalone_files": not invalid,
        "target_file_paths_unique": not duplicate_paths,
        "duplicate_target_file_paths": duplicate_paths,
        "invalid_targets": invalid,
        "targets_total": len(targets),
    }


def _tc_review(plan: dict[str, Any]) -> dict[str, Any]:
    duplicates = list(plan.get("duplicate_proposed_tc_ids") or [])
    collisions = list(plan.get("existing_tc_id_collisions") or [])
    return {
        "status": "pass" if not duplicates and not collisions else "failed",
        "duplicate_proposed_tc_ids": duplicates,
        "existing_tc_id_collisions": collisions,
        "existing_tc_id_collision_count": int(plan.get("existing_tc_id_collision_count") or 0),
        "proposed_tc_ids_total": int(plan.get("proposed_tc_ids_total") or 0),
        "unique_proposed_tc_ids_total": int(plan.get("unique_proposed_tc_ids_total") or 0),
    }


def _aggregate_review(items: list[Any]) -> dict[str, Any]:
    risky = [item for item in items if _is_aggregate_or_index(item.target_file_path)]
    return {
        "status": "pass" if not risky else "failed",
        "aggregate_target_risk_count": len(risky),
        "aggregate_target_risk_items": [item.dry_run_item_id for item in risky],
    }


def _safety_summary(stage_9g: Any, warning_reviews: list[dict[str, Any]], item_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    failed = []
    if stage_9g.real_apply_authorized:
        failed.append("Stage 9G authorized real apply")
    if stage_9g.canonical_write_allowed:
        failed.append("Stage 9G allowed canonical writes")
    if any(item["apply_readiness"] == "blocked" for item in item_reviews):
        failed.append("one or more items are blocked")
    return {
        "status": "pass" if not failed else "failed",
        "real_apply_authorized": False,
        "canonical_write_allowed": False,
        "stage_9h_preparation_authorizes_real_apply": False,
        "explicit_user_approval_required": True,
        "warnings_classified_total": len(warning_reviews),
        "warning_classification_counts": dict(Counter(item["classification"] for item in warning_reviews)),
        "item_readiness_counts": dict(Counter(item["apply_readiness"] for item in item_reviews)),
        "existing_tc_used_only_as_coverage_or_duplicate_evidence": True,
        "failed_reasons": failed,
    }


def _classify(warning: str) -> str:
    text = warning.casefold()
    if "source_req_ids" in text or "source-backed navigation/action" in text:
        return "requires_extra_source_grounding_before_apply"
    if "manual review" in text or "populate all required draft review fields" in text:
        return "non_blocking_ack_required"
    return "blocking_for_real_apply"


def _resolution(classification: str) -> str:
    if classification == "requires_extra_source_grounding_before_apply":
        return "Resolve source grounding or explicitly approve the missing source_req_id/source-action limitation before any real apply."
    if classification == "non_blocking_ack_required":
        return "Reviewer acknowledgement required before any real apply."
    return "Classify and resolve this warning before any real apply."


def _markdown(report: NewTcStage9HDesignReviewPrepReport) -> str:
    return "\n".join(
        [
            f"# Stage 9H Design/Review Preparation {report.package_id}",
            "",
            f"- prep_status: `{report.prep_status}`",
            f"- readiness_verdict: `{report.readiness_verdict}`",
            f"- real_apply_authorized: `{report.real_apply_authorized}`",
            f"- canonical_write_allowed: `{report.canonical_write_allowed}`",
            "",
            "> Stage 9H preparation does not authorize real apply.",
            "",
            "## Warning Review Table",
            "",
            "| Warning | Classification | Required resolution |",
            "|---|---|---|",
            *[
                f"| `{item['warning_id']}` {item['warning_text']} | `{item['classification']}` | {item['required_resolution_before_real_apply']} |"
                for item in report.warning_reviews
            ],
            "",
            "## Item Readiness",
            "",
            "| Item | TC ID | Readiness |",
            "|---|---|---|",
            *[
                f"| `{item['dry_run_item_id']}` | `{item['proposed_tc_id']}` | `{item['apply_readiness']}` |"
                for item in report.item_readiness_reviews
            ],
        ]
    ) + "\n"


def _blocked(package_id: str, json_path: Path, md_path: Path, input_paths: dict[str, str | None], blockers: list[str], now: str, tool: str) -> NewTcStage9HDesignReviewPrepReport:
    return NewTcStage9HDesignReviewPrepReport(
        package_id=package_id,
        prep_status="blocked",
        readiness_verdict="blocked_for_stage_9h_design",
        source_stage_9g_json_path=str(json_path),
        source_stage_9g_markdown_path=str(md_path),
        warning_reviews=[],
        item_readiness_reviews=[],
        target_file_plan_review={},
        tc_id_collision_review={},
        aggregate_target_risk_review={},
        safety_gate_summary={"status": "failed", "real_apply_authorized": False, "canonical_write_allowed": False},
        stage_9h_requires_explicit_user_approval=True,
        stage_9h_preparation_authorizes_real_apply=False,
        canonical_write_allowed=False,
        real_apply_authorized=False,
        input_paths=input_paths,
        warnings=[],
        blocking_reasons=blockers,
        created_at_utc=now,
        created_by_tool=tool,
    )


def _missing(*paths: Path) -> list[str]:
    return [f"missing path: {path}" for path in paths if not Path(path).exists()]


def _is_aggregate_or_index(path: str) -> bool:
    name = Path(path).name.casefold()
    return name in {"14-application-card.md", "index.md"} or "aggregate" in name


def _duplicates(values: list[str]) -> set[str]:
    return {value for value, count in Counter(values).items() if value and count > 1}


def _unique(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
