from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.manual_decision_answer_validation import (
    ANSWER_SCHEMA_VERSION,
    ManualDecisionAnswerTemplate,
    load_manual_decision_answer_template,
)
from test_case_agent.manual_decision_matrix import ManualDecisionMatrix, load_manual_decision_matrix

CREATED_BY_TOOL = "test_case_agent.manual_decision_answer_pack"
PACK_PREFIX = "manual-decision-reviewer-answer-pack"
ANSWERS_PREFIX = "manual-decision-reviewer-answers"
DEFAULT_PACKAGE_ID = "WPKG-000001"

PackStatus = Literal["pass", "pass-with-warnings", "blocked"]
ImportStatus = Literal["pass", "pass-with-warnings", "blocked"]

CSV_COLUMNS = [
    "row_id",
    "cluster_id",
    "priority",
    "reviewer_role",
    "affected_drafts",
    "affected_requirements",
    "decision_required",
    "evidence_summary",
    "allowed_option_ids",
    "allowed_option_labels",
    "requires_source_evidence",
    "requires_existing_tc_review",
    "required_fields",
    "selected_option_id",
    "reviewer_rationale",
    "source_evidence",
    "existing_tc_review_notes",
    "business_clarification",
    "no_new_tc_rationale",
    "defer_reason",
    "split_guidance",
    "answered_by",
    "answered_at_utc",
]

EDITABLE_COLUMNS = CSV_COLUMNS[CSV_COLUMNS.index("selected_option_id") :]


@dataclass(frozen=True)
class ReviewerAnswerPackRow:
    row_id: str
    cluster_id: str
    priority: str
    reviewer_role: str
    affected_drafts: list[str]
    affected_requirements: list[str]
    decision_required: str
    evidence_summary: str
    allowed_option_ids: list[str]
    allowed_option_labels: list[str]
    requires_source_evidence: bool
    requires_existing_tc_review: bool
    required_fields: list[str]
    selected_option_id: str
    reviewer_rationale: str
    source_evidence: str
    existing_tc_review_notes: str
    business_clarification: str
    no_new_tc_rationale: str
    defer_reason: str
    split_guidance: str
    answered_by: str
    answered_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewerAnswerPackRow":
        return cls(
            row_id=str(data["row_id"]),
            cluster_id=str(data["cluster_id"]),
            priority=str(data.get("priority") or ""),
            reviewer_role=str(data.get("reviewer_role") or ""),
            affected_drafts=list(data.get("affected_drafts") or []),
            affected_requirements=list(data.get("affected_requirements") or []),
            decision_required=str(data.get("decision_required") or ""),
            evidence_summary=str(data.get("evidence_summary") or ""),
            allowed_option_ids=list(data.get("allowed_option_ids") or []),
            allowed_option_labels=list(data.get("allowed_option_labels") or []),
            requires_source_evidence=bool(data.get("requires_source_evidence")),
            requires_existing_tc_review=bool(data.get("requires_existing_tc_review")),
            required_fields=list(data.get("required_fields") or []),
            selected_option_id=str(data.get("selected_option_id") or ""),
            reviewer_rationale=str(data.get("reviewer_rationale") or ""),
            source_evidence=str(data.get("source_evidence") or ""),
            existing_tc_review_notes=str(data.get("existing_tc_review_notes") or ""),
            business_clarification=str(data.get("business_clarification") or ""),
            no_new_tc_rationale=str(data.get("no_new_tc_rationale") or ""),
            defer_reason=str(data.get("defer_reason") or ""),
            split_guidance=str(data.get("split_guidance") or ""),
            answered_by=str(data.get("answered_by") or ""),
            answered_at_utc=str(data.get("answered_at_utc") or ""),
        )


@dataclass
class ManualDecisionAnswerPack:
    package_id: str
    pack_status: PackStatus
    source_template_path: str
    source_matrix_path: str
    answer_schema_version: str
    reviewer_rows: list[ReviewerAnswerPackRow]
    csv_columns: list[str]
    allowed_options_catalog: dict[str, dict[str, Any]]
    instructions_for_reviewer: list[str]
    safety_rules: list[str]
    import_instructions: list[str]
    canonical_write_allowed: bool
    manual_review_required: bool
    stage_9e_authorized: bool
    input_paths: dict[str, str | None]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "pack_status": self.pack_status,
            "source_template_path": self.source_template_path,
            "source_matrix_path": self.source_matrix_path,
            "answer_schema_version": self.answer_schema_version,
            "reviewer_rows": [row.to_dict() for row in self.reviewer_rows],
            "csv_columns": self.csv_columns,
            "allowed_options_catalog": self.allowed_options_catalog,
            "instructions_for_reviewer": self.instructions_for_reviewer,
            "safety_rules": self.safety_rules,
            "import_instructions": self.import_instructions,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "stage_9e_authorized": self.stage_9e_authorized,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualDecisionAnswerPack":
        return cls(
            package_id=str(data["package_id"]),
            pack_status=data["pack_status"],
            source_template_path=str(data.get("source_template_path") or ""),
            source_matrix_path=str(data.get("source_matrix_path") or ""),
            answer_schema_version=str(data.get("answer_schema_version") or ANSWER_SCHEMA_VERSION),
            reviewer_rows=[ReviewerAnswerPackRow.from_dict(row) for row in data.get("reviewer_rows", [])],
            csv_columns=list(data.get("csv_columns") or []),
            allowed_options_catalog=dict(data.get("allowed_options_catalog") or {}),
            instructions_for_reviewer=list(data.get("instructions_for_reviewer") or []),
            safety_rules=list(data.get("safety_rules") or []),
            import_instructions=list(data.get("import_instructions") or []),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            stage_9e_authorized=bool(data.get("stage_9e_authorized")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data.get("created_at_utc") or ""),
            created_by_tool=str(data.get("created_by_tool") or ""),
        )


@dataclass
class ManualDecisionAnswerPackImportReport:
    package_id: str
    import_status: ImportStatus
    source_csv_path: str
    source_pack_path: str
    answers_output_path: str | None
    rows_total: int
    rows_with_answers: int
    rows_without_answers: int
    imported_answers_count: int
    unknown_row_ids: list[str]
    duplicate_row_ids: list[str]
    invalid_option_rows: list[dict[str, Any]]
    empty_required_identity_rows: list[int]
    warnings: list[str]
    blocking_reasons: list[str]
    canonical_write_allowed: bool
    stage_9e_authorized: bool
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualDecisionAnswerPackImportReport":
        return cls(
            package_id=str(data["package_id"]),
            import_status=data["import_status"],
            source_csv_path=str(data.get("source_csv_path") or ""),
            source_pack_path=str(data.get("source_pack_path") or ""),
            answers_output_path=data.get("answers_output_path"),
            rows_total=int(data.get("rows_total") or 0),
            rows_with_answers=int(data.get("rows_with_answers") or 0),
            rows_without_answers=int(data.get("rows_without_answers") or 0),
            imported_answers_count=int(data.get("imported_answers_count") or 0),
            unknown_row_ids=list(data.get("unknown_row_ids") or []),
            duplicate_row_ids=list(data.get("duplicate_row_ids") or []),
            invalid_option_rows=list(data.get("invalid_option_rows") or []),
            empty_required_identity_rows=list(data.get("empty_required_identity_rows") or []),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            stage_9e_authorized=bool(data.get("stage_9e_authorized")),
            created_at_utc=str(data.get("created_at_utc") or ""),
            created_by_tool=str(data.get("created_by_tool") or ""),
        )


def build_manual_decision_answer_pack(
    *,
    package_id: str,
    template_path: Path,
    matrix_path: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ManualDecisionAnswerPack:
    input_paths = {"template_path": str(template_path), "matrix_path": str(matrix_path)}
    blocking_reasons: list[str] = []
    warnings: list[str] = []
    template = _load_template(template_path, blocking_reasons)
    matrix = _load_matrix(matrix_path, blocking_reasons)
    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"answer pack is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if template and template.package_id != package_id:
        blocking_reasons.append(f"template package_id mismatch: {template.package_id} != {package_id}")
    if matrix and matrix.package_id != package_id:
        blocking_reasons.append(f"matrix package_id mismatch: {matrix.package_id} != {package_id}")
    if blocking_reasons or template is None or matrix is None:
        return _answer_pack(
            package_id=package_id,
            pack_status="blocked",
            source_template_path=str(template_path),
            source_matrix_path=str(matrix_path),
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    cluster_priority = {cluster.cluster_id: cluster.priority for cluster in matrix.decision_clusters}
    matrix_rows = {row.row_id: row for row in matrix.reviewer_decision_rows}
    rows: list[ReviewerAnswerPackRow] = []
    for template_row in template.reviewer_rows:
        matrix_row = matrix_rows.get(template_row.row_id)
        allowed_ids = [str(option.get("option_id")) for option in template_row.allowed_options]
        allowed_labels = [str(option.get("label")) for option in template_row.allowed_options]
        rows.append(
            ReviewerAnswerPackRow(
                row_id=template_row.row_id,
                cluster_id=template_row.cluster_id,
                priority=cluster_priority.get(template_row.cluster_id, ""),
                reviewer_role=template_row.reviewer_role,
                affected_drafts=template_row.affected_drafts,
                affected_requirements=template_row.affected_requirements,
                decision_required=template_row.decision_required,
                evidence_summary=template_row.evidence_summary,
                allowed_option_ids=allowed_ids,
                allowed_option_labels=allowed_labels,
                requires_source_evidence=template_row.requires_source_evidence,
                requires_existing_tc_review=template_row.requires_existing_tc_review,
                required_fields=template_row.required_answer_fields,
                selected_option_id="",
                reviewer_rationale="",
                source_evidence="",
                existing_tc_review_notes="",
                business_clarification="",
                no_new_tc_rationale="",
                defer_reason="",
                split_guidance="",
                answered_by="",
                answered_at_utc="",
            )
        )
        if matrix_row is None:
            warnings.append(f"template row not found in matrix: {template_row.row_id}")
    warnings.append("Editable answer fields are intentionally empty; reviewer must fill them.")
    return _answer_pack(
        package_id=package_id,
        pack_status="pass-with-warnings" if warnings else "pass",
        source_template_path=str(template_path),
        source_matrix_path=str(matrix_path),
        reviewer_rows=rows,
        allowed_options_catalog=template.allowed_option_catalog,
        input_paths=input_paths,
        warnings=_unique(warnings),
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_manual_decision_answer_pack(pack: ManualDecisionAnswerPack, out_dir: Path) -> tuple[Path, Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{PACK_PREFIX}-{pack.package_id}.md"
    csv_path = out_dir / f"{PACK_PREFIX}-{pack.package_id}.csv"
    schema_path = out_dir / f"{PACK_PREFIX}-{pack.package_id}.schema.json"
    md_path.write_text(render_manual_decision_answer_pack_markdown(pack), encoding="utf-8", newline="\n")
    _write_pack_csv(pack, csv_path)
    schema_path.write_text(json.dumps(_schema(pack), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return md_path, csv_path, schema_path


def import_manual_decision_answer_pack(
    *,
    package_id: str,
    pack: ManualDecisionAnswerPack,
    filled_csv_path: Path,
    answers_output_path: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ManualDecisionAnswerPackImportReport:
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    if package_id != pack.package_id:
        blocking_reasons.append(f"pack package_id mismatch: {pack.package_id} != {package_id}")
    if not Path(filled_csv_path).exists():
        blocking_reasons.append(f"filled CSV is missing: {filled_csv_path}")
        return _import_report(
            package_id=package_id,
            import_status="blocked",
            source_csv_path=str(filled_csv_path),
            source_pack_path=pack.source_template_path,
            answers_output_path=None,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
        )
    rows = _read_csv_rows(filled_csv_path, blocking_reasons)
    if blocking_reasons:
        return _import_report(
            package_id=package_id,
            import_status="blocked",
            source_csv_path=str(filled_csv_path),
            source_pack_path=pack.source_template_path,
            answers_output_path=None,
            rows_total=len(rows),
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )
    pack_rows = {row.row_id: row for row in pack.reviewer_rows}
    seen: set[str] = set()
    duplicate_row_ids: set[str] = set()
    unknown_row_ids: list[str] = []
    invalid_option_rows: list[dict[str, Any]] = []
    empty_required_identity_rows: list[int] = []
    answers: list[dict[str, Any]] = []
    rows_with_answers = 0
    for index, row in enumerate(rows, start=2):
        row_id = str(row.get("row_id") or "").strip()
        cluster_id = str(row.get("cluster_id") or "").strip()
        selected_option_id = str(row.get("selected_option_id") or "").strip()
        if not row_id or not cluster_id:
            empty_required_identity_rows.append(index)
            continue
        if row_id in seen:
            duplicate_row_ids.add(row_id)
        seen.add(row_id)
        pack_row = pack_rows.get(row_id)
        if pack_row is None:
            unknown_row_ids.append(row_id)
            continue
        if not selected_option_id:
            continue
        rows_with_answers += 1
        if selected_option_id not in pack_row.allowed_option_ids:
            invalid_option_rows.append({"row_id": row_id, "selected_option_id": selected_option_id})
            continue
        answers.append(
            {
                "row_id": row_id,
                "cluster_id": cluster_id,
                "selected_option_id": selected_option_id,
                "reviewer_rationale": _trim(row.get("reviewer_rationale")),
                "source_evidence": _split_multi(row.get("source_evidence")),
                "existing_tc_review_notes": _split_multi(row.get("existing_tc_review_notes")),
                "business_clarification": _trim(row.get("business_clarification")),
                "no_new_tc_rationale": _trim(row.get("no_new_tc_rationale")),
                "defer_reason": _trim(row.get("defer_reason")),
                "split_guidance": _trim(row.get("split_guidance")),
                "answered_by": _trim(row.get("answered_by")),
                "answered_at_utc": _trim(row.get("answered_at_utc")),
            }
        )
    blockers = []
    if unknown_row_ids:
        blockers.append("filled CSV contains unknown row_id values")
    if duplicate_row_ids:
        blockers.append("filled CSV contains duplicate row_id values")
    if invalid_option_rows:
        blockers.append("filled CSV contains selected options not allowed for their rows")
    if empty_required_identity_rows:
        blockers.append("filled CSV contains rows without row_id or cluster_id")
    if blockers:
        return _import_report(
            package_id=package_id,
            import_status="blocked",
            source_csv_path=str(filled_csv_path),
            source_pack_path=pack.source_template_path,
            answers_output_path=None,
            rows_total=len(rows),
            rows_with_answers=rows_with_answers,
            rows_without_answers=max(0, len(rows) - rows_with_answers),
            imported_answers_count=0,
            unknown_row_ids=_unique(unknown_row_ids),
            duplicate_row_ids=sorted(duplicate_row_ids),
            invalid_option_rows=invalid_option_rows,
            empty_required_identity_rows=empty_required_identity_rows,
            warnings=warnings,
            blocking_reasons=blockers,
            created_by_tool=created_by_tool,
        )
    if not answers:
        warnings.append("filled CSV contains no selected options; empty answers JSON was created.")
    payload = {
        "package_id": package_id,
        "source_matrix_path": pack.source_matrix_path,
        "answer_schema_version": pack.answer_schema_version,
        "answers": answers,
        "answered_by": _first_non_empty(answer.get("answered_by") for answer in answers),
        "answered_at_utc": _first_non_empty(answer.get("answered_at_utc") for answer in answers),
        "review_notes": [
            "Imported from reviewer answer pack CSV.",
            "Import performs mechanical checks only; rerun Stage 9D.7 validation before Stage 9E.",
        ],
    }
    answers_output_path.parent.mkdir(parents=True, exist_ok=True)
    answers_output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return _import_report(
        package_id=package_id,
        import_status="pass-with-warnings" if warnings else "pass",
        source_csv_path=str(filled_csv_path),
        source_pack_path=pack.source_template_path,
        answers_output_path=str(answers_output_path),
        rows_total=len(rows),
        rows_with_answers=rows_with_answers,
        rows_without_answers=max(0, len(rows) - rows_with_answers),
        imported_answers_count=len(answers),
        warnings=warnings,
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_manual_decision_answer_pack_import_report(
    report: ManualDecisionAnswerPackImportReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{ANSWERS_PREFIX}-{report.package_id}.import-report.json"
    md_path = out_dir / f"{ANSWERS_PREFIX}-{report.package_id}.import-report.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text(render_manual_decision_answer_pack_import_report_markdown(report), encoding="utf-8", newline="\n")
    return json_path, md_path


def load_manual_decision_answer_pack(path: Path) -> ManualDecisionAnswerPack:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manual decision answer pack root must be a JSON object.")
    return ManualDecisionAnswerPack.from_dict(payload)


def load_manual_decision_answer_pack_import_report(path: Path) -> ManualDecisionAnswerPackImportReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manual decision answer pack import report root must be a JSON object.")
    return ManualDecisionAnswerPackImportReport.from_dict(payload)


def render_manual_decision_answer_pack_markdown(pack: ManualDecisionAnswerPack) -> str:
    lines = [
        f"# Manual Decision Reviewer Answer Pack {pack.package_id}",
        "",
        "## Summary",
        "",
        f"- Pack status: `{pack.pack_status}`",
        f"- Reviewer rows: `{len(pack.reviewer_rows)}`",
        f"- Stage 9E authorized: `{pack.stage_9e_authorized}`",
        f"- Canonical write allowed: `{pack.canonical_write_allowed}`",
        "",
        "## Safety Rules",
        "",
    ]
    _append_list(lines, pack.safety_rules)
    lines.extend(["", "## How To Fill Answers", ""])
    _append_list(lines, pack.instructions_for_reviewer)
    lines.extend(["", "## Allowed Option Catalog", ""])
    for option_id, option in sorted(pack.allowed_options_catalog.items()):
        lines.append(f"- `{option_id}`: {option.get('label')} -> `{option.get('allowed_next_action')}`")
    lines.extend(
        [
            "",
            "## Reviewer Answer Table",
            "",
            "| Row ID | Priority | Role | Affected drafts | Affected requirements | Decision required | Allowed options | Required evidence | Editable fields to fill |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in pack.reviewer_rows:
        required = []
        if row.requires_source_evidence:
            required.append("source evidence")
        if row.requires_existing_tc_review:
            required.append("existing TC coverage notes")
        lines.append(
            f"| `{row.row_id}` | `{row.priority}` | `{row.reviewer_role}` | {_md_join(row.affected_drafts)} | "
            f"{_md_join(row.affected_requirements)} | {_escape(row.decision_required)} | "
            f"{_escape('; '.join(row.allowed_option_ids))} | {_escape('; '.join(required) or 'rationale')} | "
            f"{_escape('; '.join(EDITABLE_COLUMNS))} |"
        )
    lines.extend(["", "## Required Evidence Rules", ""])
    _append_list(
        lines,
        [
            "Source evidence should cite req uid, source req id, source artifact, or explicit analyst clarification.",
            "Existing TC notes must state that existing TC is coverage evidence only.",
            "No-new-TC, defer and split options require their specific rationale fields.",
        ],
    )
    lines.extend(["", "## Import Instructions", ""])
    _append_list(lines, pack.import_instructions)
    lines.extend(["", "## Stage 9E Warning", "", "Answering this pack does not itself create or authorize Stage 9E. Rerun Stage 9D.7 validation first.", "", "## Warnings", ""])
    _append_list(lines, pack.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, pack.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def render_manual_decision_answer_pack_import_report_markdown(report: ManualDecisionAnswerPackImportReport) -> str:
    lines = [
        f"# Manual Decision Answer Pack Import Report {report.package_id}",
        "",
        "## Summary",
        "",
        f"- Import status: `{report.import_status}`",
        f"- Rows total: `{report.rows_total}`",
        f"- Rows with answers: `{report.rows_with_answers}`",
        f"- Rows without answers: `{report.rows_without_answers}`",
        f"- Imported answers: `{report.imported_answers_count}`",
        f"- Answers output: `{report.answers_output_path or 'none'}`",
        f"- Stage 9E authorized: `{report.stage_9e_authorized}`",
        f"- Canonical write allowed: `{report.canonical_write_allowed}`",
        "",
        "## Import Findings",
        "",
        f"- Unknown row ids: `{', '.join(report.unknown_row_ids) or 'none'}`",
        f"- Duplicate row ids: `{', '.join(report.duplicate_row_ids) or 'none'}`",
        f"- Invalid option rows: `{len(report.invalid_option_rows)}`",
        f"- Empty identity rows: `{len(report.empty_required_identity_rows)}`",
        "",
        "## Safety",
        "",
        "- This artifact does not create or edit canonical test cases.",
        "- Existing TC may be used only as coverage evidence.",
        "- Stage 9E requires separate validation.",
        "",
        "## Warnings",
        "",
    ]
    _append_list(lines, report.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, report.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _answer_pack(
    *,
    package_id: str,
    pack_status: PackStatus,
    source_template_path: str,
    source_matrix_path: str,
    reviewer_rows: list[ReviewerAnswerPackRow] | None = None,
    allowed_options_catalog: dict[str, dict[str, Any]] | None = None,
    input_paths: dict[str, str | None] | None = None,
    warnings: list[str] | None = None,
    blocking_reasons: list[str] | None = None,
    created_by_tool: str,
) -> ManualDecisionAnswerPack:
    return ManualDecisionAnswerPack(
        package_id=package_id,
        pack_status=pack_status,
        source_template_path=source_template_path,
        source_matrix_path=source_matrix_path,
        answer_schema_version=ANSWER_SCHEMA_VERSION,
        reviewer_rows=reviewer_rows or [],
        csv_columns=list(CSV_COLUMNS),
        allowed_options_catalog=allowed_options_catalog or {},
        instructions_for_reviewer=[
            "Fill only editable fields from selected_option_id onward.",
            "Select at most one allowed option per row.",
            "Leave selected_option_id empty if the row is not answered yet.",
            "Use '; ' to separate multiple source evidence or existing TC notes.",
            "After import, rerun Stage 9D.7 validation before any future Stage 9E.",
        ],
        safety_rules=[
            "This artifact does not create or edit canonical test cases.",
            "Existing TC may be used only as coverage evidence.",
            "Stage 9E requires separate validation.",
            "Do not run --apply, git apply, or external patch from this pack.",
        ],
        import_instructions=[
            f"Save the filled CSV as `{PACK_PREFIX}-{package_id}.filled.csv` in the work directory.",
            "Run scripts/import_manual_decision_answer_pack.py to convert filled CSV into reviewer answers JSON.",
            "Run Stage 9D.7 validation after import.",
        ],
        canonical_write_allowed=False,
        manual_review_required=True,
        stage_9e_authorized=False,
        input_paths=input_paths or {},
        warnings=warnings or [],
        blocking_reasons=blocking_reasons or [],
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _import_report(
    *,
    package_id: str,
    import_status: ImportStatus,
    source_csv_path: str,
    source_pack_path: str,
    answers_output_path: str | None,
    rows_total: int = 0,
    rows_with_answers: int = 0,
    rows_without_answers: int = 0,
    imported_answers_count: int = 0,
    unknown_row_ids: list[str] | None = None,
    duplicate_row_ids: list[str] | None = None,
    invalid_option_rows: list[dict[str, Any]] | None = None,
    empty_required_identity_rows: list[int] | None = None,
    warnings: list[str] | None = None,
    blocking_reasons: list[str] | None = None,
    created_by_tool: str,
) -> ManualDecisionAnswerPackImportReport:
    return ManualDecisionAnswerPackImportReport(
        package_id=package_id,
        import_status=import_status,
        source_csv_path=source_csv_path,
        source_pack_path=source_pack_path,
        answers_output_path=answers_output_path,
        rows_total=rows_total,
        rows_with_answers=rows_with_answers,
        rows_without_answers=rows_without_answers,
        imported_answers_count=imported_answers_count,
        unknown_row_ids=unknown_row_ids or [],
        duplicate_row_ids=duplicate_row_ids or [],
        invalid_option_rows=invalid_option_rows or [],
        empty_required_identity_rows=empty_required_identity_rows or [],
        warnings=warnings or [],
        blocking_reasons=blocking_reasons or [],
        canonical_write_allowed=False,
        stage_9e_authorized=False,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _write_pack_csv(pack: ManualDecisionAnswerPack, path: Path) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in pack.reviewer_rows:
            writer.writerow(_row_to_csv(row))


def _row_to_csv(row: ReviewerAnswerPackRow) -> dict[str, str]:
    return {
        "row_id": row.row_id,
        "cluster_id": row.cluster_id,
        "priority": row.priority,
        "reviewer_role": row.reviewer_role,
        "affected_drafts": _join_multi(row.affected_drafts),
        "affected_requirements": _join_multi(row.affected_requirements),
        "decision_required": row.decision_required,
        "evidence_summary": row.evidence_summary,
        "allowed_option_ids": _join_multi(row.allowed_option_ids),
        "allowed_option_labels": _join_multi(row.allowed_option_labels),
        "requires_source_evidence": str(row.requires_source_evidence).lower(),
        "requires_existing_tc_review": str(row.requires_existing_tc_review).lower(),
        "required_fields": _join_multi(row.required_fields),
        "selected_option_id": "",
        "reviewer_rationale": "",
        "source_evidence": "",
        "existing_tc_review_notes": "",
        "business_clarification": "",
        "no_new_tc_rationale": "",
        "defer_reason": "",
        "split_guidance": "",
        "answered_by": "",
        "answered_at_utc": "",
    }


def _read_csv_rows(path: Path, blocking_reasons: list[str]) -> list[dict[str, str]]:
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != CSV_COLUMNS:
                blocking_reasons.append("filled CSV columns do not match expected answer-pack columns")
                return []
            return [dict(row) for row in reader]
    except Exception as exc:  # noqa: BLE001 - import report should capture CSV errors.
        blocking_reasons.append(f"filled CSV cannot be read: {path}: {exc}")
        return []


def _schema(pack: ManualDecisionAnswerPack) -> dict[str, Any]:
    return {
        "package_id": pack.package_id,
        "answer_schema_version": pack.answer_schema_version,
        "csv_columns": pack.csv_columns,
        "editable_columns": list(EDITABLE_COLUMNS),
        "allowed_options_by_row": {row.row_id: row.allowed_option_ids for row in pack.reviewer_rows},
        "required_evidence_by_row": {
            row.row_id: {
                "requires_source_evidence": row.requires_source_evidence,
                "requires_existing_tc_review": row.requires_existing_tc_review,
                "required_fields": row.required_fields,
            }
            for row in pack.reviewer_rows
        },
        "safety_restrictions": pack.safety_rules,
        "output_json_shape": {
            "package_id": "string",
            "source_matrix_path": "string",
            "answer_schema_version": ANSWER_SCHEMA_VERSION,
            "answers": [
                {
                    "row_id": "string",
                    "cluster_id": "string",
                    "selected_option_id": "string",
                    "reviewer_rationale": "string",
                    "source_evidence": ["string"],
                    "existing_tc_review_notes": ["string"],
                    "business_clarification": "string",
                    "no_new_tc_rationale": "string",
                    "defer_reason": "string",
                    "split_guidance": "string",
                    "answered_by": "string",
                    "answered_at_utc": "string",
                }
            ],
        },
    }


def _load_template(path: Path, blocking_reasons: list[str]) -> ManualDecisionAnswerTemplate | None:
    if not Path(path).exists():
        blocking_reasons.append(f"answer template is missing: {path}")
        return None
    try:
        return load_manual_decision_answer_template(Path(path))
    except Exception as exc:  # noqa: BLE001 - export report should capture parse errors.
        blocking_reasons.append(f"answer template cannot be parsed: {path}: {exc}")
        return None


def _load_matrix(path: Path, blocking_reasons: list[str]) -> ManualDecisionMatrix | None:
    if not Path(path).exists():
        blocking_reasons.append(f"manual decision matrix is missing: {path}")
        return None
    try:
        return load_manual_decision_matrix(Path(path))
    except Exception as exc:  # noqa: BLE001 - export report should capture parse errors.
        blocking_reasons.append(f"manual decision matrix cannot be parsed: {path}: {exc}")
        return None


def _join_multi(values: list[str]) -> str:
    return "; ".join(str(value) for value in values if str(value))


def _split_multi(value: Any) -> list[str]:
    text = _trim(value)
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def _trim(value: Any) -> str:
    return str(value or "").strip()


def _first_non_empty(values: Any) -> str:
    for value in values:
        text = _trim(value)
        if text:
            return text
    return ""


def _md_join(values: list[str]) -> str:
    return _escape(", ".join(values) if values else "none")


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


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
        if value in (None, ""):
            continue
        text = str(value)
        if text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
