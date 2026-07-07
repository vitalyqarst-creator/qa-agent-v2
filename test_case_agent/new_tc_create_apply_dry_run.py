from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CreateApplyDryRunItem:
    dry_run_item_id: str
    source_revised_draft_id: str
    proposed_tc_id: str
    target_file_path: str
    target_section: str
    planned_operation: str
    dry_run_decision: str
    generated_markdown_preview: str
    traceability_refs: list[str]
    req_uids: list[str]
    source_req_ids: list[str]
    source_evidence_refs: list[str]
    source_agent_decision_row_id: str
    source_validation_result_id: str
    review_result: str
    review_warnings: list[str]
    collision_risks: list[str]
    format_warnings: list[str]
    safety_warnings: list[str]
    creates_or_edits_canonical_tc: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreateApplyDryRunItem":
        return cls(
            dry_run_item_id=str(data.get("dry_run_item_id") or ""),
            source_revised_draft_id=str(data.get("source_revised_draft_id") or ""),
            proposed_tc_id=str(data.get("proposed_tc_id") or ""),
            target_file_path=str(data.get("target_file_path") or ""),
            target_section=str(data.get("target_section") or ""),
            planned_operation=str(data.get("planned_operation") or ""),
            dry_run_decision=str(data.get("dry_run_decision") or ""),
            generated_markdown_preview=str(data.get("generated_markdown_preview") or ""),
            traceability_refs=list(data.get("traceability_refs") or []),
            req_uids=list(data.get("req_uids") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            source_evidence_refs=list(data.get("source_evidence_refs") or []),
            source_agent_decision_row_id=str(data.get("source_agent_decision_row_id") or ""),
            source_validation_result_id=str(data.get("source_validation_result_id") or ""),
            review_result=str(data.get("review_result") or ""),
            review_warnings=list(data.get("review_warnings") or []),
            collision_risks=list(data.get("collision_risks") or []),
            format_warnings=list(data.get("format_warnings") or []),
            safety_warnings=list(data.get("safety_warnings") or []),
            creates_or_edits_canonical_tc=bool(data.get("creates_or_edits_canonical_tc")),
        )

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class NewTcCreateApplyDryRunReport:
    package_id: str
    dry_run_status: str
    dry_run_items: list[CreateApplyDryRunItem]
    target_file_plan: dict[str, Any]
    tc_id_plan: dict[str, Any]
    aggregate_target_risk_review: dict[str, Any]
    safety_checks: list[dict[str, Any]]
    stage_9h_readiness: dict[str, Any]
    canonical_write_allowed: bool
    real_apply_authorized: bool
    warnings: list[str]
    blocking_reasons: list[str]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewTcCreateApplyDryRunReport":
        return cls(
            package_id=str(data.get("package_id") or ""),
            dry_run_status=str(data.get("dry_run_status") or ""),
            dry_run_items=[CreateApplyDryRunItem.from_dict(item) for item in data.get("dry_run_items", [])],
            target_file_plan=dict(data.get("target_file_plan") or {}),
            tc_id_plan=dict(data.get("tc_id_plan") or {}),
            aggregate_target_risk_review=dict(data.get("aggregate_target_risk_review") or {}),
            safety_checks=list(data.get("safety_checks") or []),
            stage_9h_readiness=dict(data.get("stage_9h_readiness") or {}),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            real_apply_authorized=bool(data.get("real_apply_authorized")),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            raw=dict(data),
        )

    def to_dict(self) -> dict[str, Any]:
        return dict(self.raw)


def load_new_tc_create_apply_dry_run(path: Path) -> NewTcCreateApplyDryRunReport:
    return NewTcCreateApplyDryRunReport.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def write_new_tc_create_apply_dry_run(report: NewTcCreateApplyDryRunReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"new-tc-create-apply-dry-run-{report.package_id}.json"
    md_path = out_dir / f"new-tc-create-apply-dry-run-{report.package_id}.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text("# New TC Create Apply Dry-Run\n", encoding="utf-8-sig", newline="\n")
    return json_path, md_path
