from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.manual_decision_matrix import (
    DecisionOption,
    ManualDecisionMatrix,
    ReviewerDecisionRow,
    load_manual_decision_matrix,
)

CREATED_BY_TOOL = "test_case_agent.manual_decision_answer_validation"
ANSWER_TEMPLATE_PREFIX = "manual-decision-answer-template"
ANSWER_VALIDATION_PREFIX = "manual-decision-answer-validation"
ANSWER_SCHEMA_VERSION = "manual-decision-answers/v1"
DEFAULT_PACKAGE_ID = "WPKG-000001"

TemplateStatus = Literal["pass", "pass-with-warnings", "blocked"]
ValidationStatus = Literal["awaiting_reviewer_answers", "pass", "pass-with-warnings", "blocked", "rejected"]
AnswerValidationStatus = Literal["valid", "valid-with-warnings", "invalid", "unsafe"]


@dataclass(frozen=True)
class ReviewerAnswerPlaceholder:
    selected_option_id: None
    reviewer_rationale: str
    source_evidence: list[str]
    existing_tc_review_notes: list[str]
    business_clarification: str
    no_new_tc_rationale: str
    defer_reason: str
    split_guidance: str
    answered_by: str
    answered_at_utc: str

    @classmethod
    def empty(cls) -> "ReviewerAnswerPlaceholder":
        return cls(
            selected_option_id=None,
            reviewer_rationale="",
            source_evidence=[],
            existing_tc_review_notes=[],
            business_clarification="",
            no_new_tc_rationale="",
            defer_reason="",
            split_guidance="",
            answered_by="",
            answered_at_utc="",
        )

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class ReviewerAnswerTemplateRow:
    row_id: str
    cluster_id: str
    decision_required: str
    affected_drafts: list[str]
    affected_requirements: list[str]
    allowed_options: list[dict[str, Any]]
    requires_source_evidence: bool
    requires_existing_tc_review: bool
    required_answer_fields: list[str]
    evidence_summary: str
    reviewer_role: str
    answer_placeholder: ReviewerAnswerPlaceholder

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "cluster_id": self.cluster_id,
            "decision_required": self.decision_required,
            "affected_drafts": self.affected_drafts,
            "affected_requirements": self.affected_requirements,
            "allowed_options": self.allowed_options,
            "requires_source_evidence": self.requires_source_evidence,
            "requires_existing_tc_review": self.requires_existing_tc_review,
            "required_answer_fields": self.required_answer_fields,
            "evidence_summary": self.evidence_summary,
            "reviewer_role": self.reviewer_role,
            "answer_placeholder": self.answer_placeholder.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewerAnswerTemplateRow":
        placeholder = data.get("answer_placeholder") or {}
        return cls(
            row_id=str(data["row_id"]),
            cluster_id=str(data["cluster_id"]),
            decision_required=str(data["decision_required"]),
            affected_drafts=list(data.get("affected_drafts") or []),
            affected_requirements=list(data.get("affected_requirements") or []),
            allowed_options=list(data.get("allowed_options") or []),
            requires_source_evidence=bool(data.get("requires_source_evidence")),
            requires_existing_tc_review=bool(data.get("requires_existing_tc_review")),
            required_answer_fields=list(data.get("required_answer_fields") or []),
            evidence_summary=str(data.get("evidence_summary") or ""),
            reviewer_role=str(data.get("reviewer_role") or ""),
            answer_placeholder=ReviewerAnswerPlaceholder(
                selected_option_id=None,
                reviewer_rationale=str(placeholder.get("reviewer_rationale") or ""),
                source_evidence=list(placeholder.get("source_evidence") or []),
                existing_tc_review_notes=list(placeholder.get("existing_tc_review_notes") or []),
                business_clarification=str(placeholder.get("business_clarification") or ""),
                no_new_tc_rationale=str(placeholder.get("no_new_tc_rationale") or ""),
                defer_reason=str(placeholder.get("defer_reason") or ""),
                split_guidance=str(placeholder.get("split_guidance") or ""),
                answered_by=str(placeholder.get("answered_by") or ""),
                answered_at_utc=str(placeholder.get("answered_at_utc") or ""),
            ),
        )


@dataclass
class ManualDecisionAnswerTemplate:
    package_id: str
    template_status: TemplateStatus
    source_matrix_path: str
    reviewer_rows: list[ReviewerAnswerTemplateRow]
    answer_schema_version: str
    instructions_for_reviewer: list[str]
    allowed_option_catalog: dict[str, dict[str, Any]]
    required_evidence_rules: list[str]
    safety_rules: list[str]
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
            "template_status": self.template_status,
            "source_matrix_path": self.source_matrix_path,
            "reviewer_rows": [row.to_dict() for row in self.reviewer_rows],
            "answer_schema_version": self.answer_schema_version,
            "instructions_for_reviewer": self.instructions_for_reviewer,
            "allowed_option_catalog": self.allowed_option_catalog,
            "required_evidence_rules": self.required_evidence_rules,
            "safety_rules": self.safety_rules,
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
    def from_dict(cls, data: dict[str, Any]) -> "ManualDecisionAnswerTemplate":
        return cls(
            package_id=str(data["package_id"]),
            template_status=data["template_status"],
            source_matrix_path=str(data.get("source_matrix_path") or ""),
            reviewer_rows=[ReviewerAnswerTemplateRow.from_dict(row) for row in data.get("reviewer_rows", [])],
            answer_schema_version=str(data.get("answer_schema_version") or ANSWER_SCHEMA_VERSION),
            instructions_for_reviewer=list(data.get("instructions_for_reviewer") or []),
            allowed_option_catalog=dict(data.get("allowed_option_catalog") or {}),
            required_evidence_rules=list(data.get("required_evidence_rules") or []),
            safety_rules=list(data.get("safety_rules") or []),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            stage_9e_authorized=bool(data.get("stage_9e_authorized")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data.get("created_at_utc") or ""),
            created_by_tool=str(data.get("created_by_tool") or ""),
        )


@dataclass(frozen=True)
class ValidatedReviewerAnswer:
    row_id: str
    cluster_id: str
    selected_option_id: str | None
    selected_allowed_next_action: str | None
    validation_status: AnswerValidationStatus
    reviewer_rationale: str
    source_evidence: list[str]
    existing_tc_review_notes: list[str]
    normalized_effect: str
    affected_drafts: list[str]
    affected_requirements: list[str]
    enables_revised_draft_action: bool
    enables_no_new_tc: bool
    enables_defer: bool
    requires_followup: bool
    warnings: list[str]
    blocking_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidatedReviewerAnswer":
        return cls(
            row_id=str(data["row_id"]),
            cluster_id=str(data.get("cluster_id") or ""),
            selected_option_id=data.get("selected_option_id"),
            selected_allowed_next_action=data.get("selected_allowed_next_action"),
            validation_status=data["validation_status"],
            reviewer_rationale=str(data.get("reviewer_rationale") or ""),
            source_evidence=list(data.get("source_evidence") or []),
            existing_tc_review_notes=list(data.get("existing_tc_review_notes") or []),
            normalized_effect=str(data.get("normalized_effect") or ""),
            affected_drafts=list(data.get("affected_drafts") or []),
            affected_requirements=list(data.get("affected_requirements") or []),
            enables_revised_draft_action=bool(data.get("enables_revised_draft_action")),
            enables_no_new_tc=bool(data.get("enables_no_new_tc")),
            enables_defer=bool(data.get("enables_defer")),
            requires_followup=bool(data.get("requires_followup")),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


@dataclass(frozen=True)
class ReadinessAfterAnswers:
    all_blocking_rows_answered: bool
    all_answers_valid: bool
    unsafe_answers_count: int
    missing_answers_count: int
    valid_revise_or_replace_count: int
    valid_extend_existing_count: int
    valid_no_new_tc_count: int
    valid_defer_count: int
    valid_clarification_count: int
    remaining_manual_rows: list[str]
    can_prepare_stage_9e_draft_only: bool
    why_not_ready: str
    required_next_action: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReadinessAfterAnswers":
        return cls(
            all_blocking_rows_answered=bool(data.get("all_blocking_rows_answered")),
            all_answers_valid=bool(data.get("all_answers_valid")),
            unsafe_answers_count=int(data.get("unsafe_answers_count") or 0),
            missing_answers_count=int(data.get("missing_answers_count") or 0),
            valid_revise_or_replace_count=int(data.get("valid_revise_or_replace_count") or 0),
            valid_extend_existing_count=int(data.get("valid_extend_existing_count") or 0),
            valid_no_new_tc_count=int(data.get("valid_no_new_tc_count") or 0),
            valid_defer_count=int(data.get("valid_defer_count") or 0),
            valid_clarification_count=int(data.get("valid_clarification_count") or 0),
            remaining_manual_rows=list(data.get("remaining_manual_rows") or []),
            can_prepare_stage_9e_draft_only=bool(data.get("can_prepare_stage_9e_draft_only")),
            why_not_ready=str(data.get("why_not_ready") or ""),
            required_next_action=str(data.get("required_next_action") or ""),
        )


@dataclass(frozen=True)
class Stage9EGate:
    stage_9e_allowed: bool
    stage_9e_allowed_scope: list[str]
    stage_9e_blockers: list[str]
    stage_9e_safety_conditions: list[str]
    canonical_write_allowed: bool
    requires_draft_only_output: bool
    requires_reviewer_answer_traceability: bool

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Stage9EGate":
        return cls(
            stage_9e_allowed=bool(data.get("stage_9e_allowed")),
            stage_9e_allowed_scope=list(data.get("stage_9e_allowed_scope") or []),
            stage_9e_blockers=list(data.get("stage_9e_blockers") or []),
            stage_9e_safety_conditions=list(data.get("stage_9e_safety_conditions") or []),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            requires_draft_only_output=bool(data.get("requires_draft_only_output")),
            requires_reviewer_answer_traceability=bool(data.get("requires_reviewer_answer_traceability")),
        )


@dataclass
class ManualDecisionAnswerValidation:
    package_id: str
    validation_status: ValidationStatus
    source_matrix_path: str
    source_answers_path: str | None
    answer_rows_total: int
    answer_rows_valid: int
    answer_rows_missing: int
    answer_rows_rejected: int
    validated_answers: list[ValidatedReviewerAnswer]
    missing_answers: list[dict[str, Any]]
    invalid_answers: list[dict[str, Any]]
    unsafe_answers: list[dict[str, Any]]
    normalized_reviewer_decisions: list[dict[str, Any]]
    readiness_after_answers: ReadinessAfterAnswers
    stage_9e_gate: Stage9EGate
    canonical_write_allowed: bool
    manual_review_required: bool
    input_paths: dict[str, str | None]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "validation_status": self.validation_status,
            "source_matrix_path": self.source_matrix_path,
            "source_answers_path": self.source_answers_path,
            "answer_rows_total": self.answer_rows_total,
            "answer_rows_valid": self.answer_rows_valid,
            "answer_rows_missing": self.answer_rows_missing,
            "answer_rows_rejected": self.answer_rows_rejected,
            "validated_answers": [answer.to_dict() for answer in self.validated_answers],
            "missing_answers": self.missing_answers,
            "invalid_answers": self.invalid_answers,
            "unsafe_answers": self.unsafe_answers,
            "normalized_reviewer_decisions": self.normalized_reviewer_decisions,
            "readiness_after_answers": self.readiness_after_answers.to_dict(),
            "stage_9e_gate": self.stage_9e_gate.to_dict(),
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualDecisionAnswerValidation":
        return cls(
            package_id=str(data["package_id"]),
            validation_status=data["validation_status"],
            source_matrix_path=str(data.get("source_matrix_path") or ""),
            source_answers_path=data.get("source_answers_path"),
            answer_rows_total=int(data.get("answer_rows_total") or 0),
            answer_rows_valid=int(data.get("answer_rows_valid") or 0),
            answer_rows_missing=int(data.get("answer_rows_missing") or 0),
            answer_rows_rejected=int(data.get("answer_rows_rejected") or 0),
            validated_answers=[ValidatedReviewerAnswer.from_dict(item) for item in data.get("validated_answers", [])],
            missing_answers=list(data.get("missing_answers") or []),
            invalid_answers=list(data.get("invalid_answers") or []),
            unsafe_answers=list(data.get("unsafe_answers") or []),
            normalized_reviewer_decisions=list(data.get("normalized_reviewer_decisions") or []),
            readiness_after_answers=ReadinessAfterAnswers.from_dict(data["readiness_after_answers"]),
            stage_9e_gate=Stage9EGate.from_dict(data["stage_9e_gate"]),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data.get("created_at_utc") or ""),
            created_by_tool=str(data.get("created_by_tool") or ""),
        )


def build_manual_decision_answer_template(
    *,
    package_id: str,
    matrix_path: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ManualDecisionAnswerTemplate:
    input_paths = {"matrix_path": str(matrix_path)}
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    matrix = _load_matrix(matrix_path, blocking_reasons)
    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"answer template is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if matrix and matrix.package_id != package_id:
        blocking_reasons.append(f"matrix package_id mismatch: {matrix.package_id} != {package_id}")
    if blocking_reasons or matrix is None:
        return _answer_template(
            package_id=package_id,
            template_status="blocked",
            source_matrix_path=str(matrix_path),
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    rows = [_template_row(row) for row in matrix.reviewer_decision_rows]
    warnings.append("Reviewer answers are not preselected; this template must be filled manually.")
    return _answer_template(
        package_id=package_id,
        template_status="pass-with-warnings" if rows else "pass",
        source_matrix_path=str(matrix_path),
        reviewer_rows=rows,
        allowed_option_catalog=_allowed_option_catalog(matrix.reviewer_decision_rows),
        input_paths=input_paths,
        warnings=_unique(warnings),
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def validate_manual_decision_answers(
    *,
    package_id: str,
    matrix_path: Path,
    answers_path: Path | None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ManualDecisionAnswerValidation:
    input_paths = {
        "matrix_path": str(matrix_path),
        "answers_path": str(answers_path) if answers_path is not None else None,
    }
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    matrix = _load_matrix(matrix_path, blocking_reasons)
    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"answer validation is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if matrix and matrix.package_id != package_id:
        blocking_reasons.append(f"matrix package_id mismatch: {matrix.package_id} != {package_id}")
    if blocking_reasons or matrix is None:
        return _validation(
            package_id=package_id,
            validation_status="blocked",
            source_matrix_path=str(matrix_path),
            source_answers_path=str(answers_path) if answers_path else None,
            input_paths=input_paths,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    rows_by_id = {row.row_id: row for row in matrix.reviewer_decision_rows}
    blocking_row_ids = {row.row_id for row in matrix.reviewer_decision_rows if row.is_blocking_for_revised_draft}
    if answers_path is None or not Path(answers_path).exists():
        missing = [_missing_answer(row) for row in matrix.reviewer_decision_rows if row.row_id in blocking_row_ids]
        readiness, gate = _readiness_and_gate(
            matrix=matrix,
            answers_exist=False,
            validated=[],
            missing_answers=missing,
            invalid_answers=[],
            unsafe_answers=[],
        )
        return _validation(
            package_id=package_id,
            validation_status="awaiting_reviewer_answers",
            source_matrix_path=str(matrix_path),
            source_answers_path=str(answers_path) if answers_path else None,
            answer_rows_total=len(matrix.reviewer_decision_rows),
            answer_rows_missing=len(missing),
            missing_answers=missing,
            readiness_after_answers=readiness,
            stage_9e_gate=gate,
            input_paths=input_paths,
            warnings=["Reviewer answers file is missing; fill the answer template before Stage 9E."],
            created_by_tool=created_by_tool,
        )

    answers_payload = _load_json_object(answers_path, "reviewer answers", warnings, blocking_reasons)
    if answers_payload is None:
        return _validation(
            package_id=package_id,
            validation_status="blocked",
            source_matrix_path=str(matrix_path),
            source_answers_path=str(answers_path),
            answer_rows_total=len(matrix.reviewer_decision_rows),
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )
    if str(answers_payload.get("package_id")) != package_id:
        return _validation(
            package_id=package_id,
            validation_status="blocked",
            source_matrix_path=str(matrix_path),
            source_answers_path=str(answers_path),
            answer_rows_total=len(matrix.reviewer_decision_rows),
            input_paths=input_paths,
            blocking_reasons=[f"answers package_id mismatch: {answers_payload.get('package_id')} != {package_id}"],
            created_by_tool=created_by_tool,
        )

    answer_items = answers_payload.get("answers") or []
    if not isinstance(answer_items, list):
        return _validation(
            package_id=package_id,
            validation_status="blocked",
            source_matrix_path=str(matrix_path),
            source_answers_path=str(answers_path),
            answer_rows_total=len(matrix.reviewer_decision_rows),
            input_paths=input_paths,
            blocking_reasons=["answers root field must be a list."],
            created_by_tool=created_by_tool,
        )
    duplicate_row_ids = _duplicates(str(item.get("row_id")) for item in answer_items if isinstance(item, dict))
    unknown_answers = [
        {"row_id": item.get("row_id"), "reason": "unknown row_id"}
        for item in answer_items
        if isinstance(item, dict) and str(item.get("row_id")) not in rows_by_id
    ]
    invalid_answers: list[dict[str, Any]] = []
    unsafe_answers: list[dict[str, Any]] = []
    validated: list[ValidatedReviewerAnswer] = []
    answers_by_row: dict[str, dict[str, Any]] = {}
    for item in answer_items:
        if isinstance(item, dict) and str(item.get("row_id")) in rows_by_id and str(item.get("row_id")) not in answers_by_row:
            answers_by_row[str(item.get("row_id"))] = item

    for row_id in duplicate_row_ids:
        invalid_answers.append({"row_id": row_id, "reason": "duplicate answer for row_id"})
    invalid_answers.extend(unknown_answers)

    for row_id, row in rows_by_id.items():
        answer = answers_by_row.get(row_id)
        if answer is None:
            continue
        result = _validate_answer(row, answer)
        validated.append(result)
        if result.validation_status == "unsafe":
            unsafe_answers.append({"row_id": row_id, "reasons": result.blocking_reasons})
        elif result.validation_status == "invalid":
            invalid_answers.append({"row_id": row_id, "reasons": result.blocking_reasons})

    missing = [_missing_answer(row) for row_id, row in rows_by_id.items() if row_id in blocking_row_ids and row_id not in answers_by_row]
    readiness, gate = _readiness_and_gate(
        matrix=matrix,
        answers_exist=True,
        validated=validated,
        missing_answers=missing,
        invalid_answers=invalid_answers,
        unsafe_answers=unsafe_answers,
    )
    valid_count = sum(1 for answer in validated if answer.validation_status in {"valid", "valid-with-warnings"})
    rejected_count = len(invalid_answers) + len(unsafe_answers)
    status: ValidationStatus
    if unsafe_answers:
        status = "rejected"
    elif invalid_answers or missing:
        status = "rejected"
    elif warnings:
        status = "pass-with-warnings"
    else:
        status = "pass"
    return _validation(
        package_id=package_id,
        validation_status=status,
        source_matrix_path=str(matrix_path),
        source_answers_path=str(answers_path),
        answer_rows_total=len(matrix.reviewer_decision_rows),
        answer_rows_valid=valid_count,
        answer_rows_missing=len(missing),
        answer_rows_rejected=rejected_count,
        validated_answers=validated,
        missing_answers=missing,
        invalid_answers=invalid_answers,
        unsafe_answers=unsafe_answers,
        normalized_reviewer_decisions=[_normalized_decision(answer) for answer in validated if answer.validation_status in {"valid", "valid-with-warnings"}],
        readiness_after_answers=readiness,
        stage_9e_gate=gate,
        input_paths=input_paths,
        warnings=warnings,
        created_by_tool=created_by_tool,
    )


def write_manual_decision_answer_template(template: ManualDecisionAnswerTemplate, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{ANSWER_TEMPLATE_PREFIX}-{template.package_id}.json"
    md_path = out_dir / f"{ANSWER_TEMPLATE_PREFIX}-{template.package_id}.md"
    json_path.write_text(json.dumps(template.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text(render_manual_decision_answer_template_markdown(template), encoding="utf-8", newline="\n")
    return json_path, md_path


def write_manual_decision_answer_validation(validation: ManualDecisionAnswerValidation, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{ANSWER_VALIDATION_PREFIX}-{validation.package_id}.json"
    md_path = out_dir / f"{ANSWER_VALIDATION_PREFIX}-{validation.package_id}.md"
    json_path.write_text(json.dumps(validation.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text(render_manual_decision_answer_validation_markdown(validation), encoding="utf-8", newline="\n")
    return json_path, md_path


def load_manual_decision_answer_template(path: Path) -> ManualDecisionAnswerTemplate:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manual decision answer template root must be a JSON object.")
    return ManualDecisionAnswerTemplate.from_dict(payload)


def load_manual_decision_answer_validation(path: Path) -> ManualDecisionAnswerValidation:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manual decision answer validation root must be a JSON object.")
    return ManualDecisionAnswerValidation.from_dict(payload)


def render_manual_decision_answer_template_markdown(template: ManualDecisionAnswerTemplate) -> str:
    lines = [
        f"# Manual Decision Answer Template {template.package_id}",
        "",
        "## Summary",
        "",
        f"- Template status: `{template.template_status}`",
        f"- Reviewer rows: `{len(template.reviewer_rows)}`",
        f"- Stage 9E authorized: `{template.stage_9e_authorized}`",
        f"- Canonical write allowed: `{template.canonical_write_allowed}`",
        "",
        "## Instructions For Reviewer",
        "",
    ]
    _append_list(lines, template.instructions_for_reviewer)
    lines.extend(["", "## Safety Rules", ""])
    _append_list(lines, template.safety_rules)
    lines.extend(
        [
            "",
            "## Answer Table",
            "",
            "| Row ID | Cluster | Decision required | Allowed options | Required fields | Evidence summary |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in template.reviewer_rows:
        options = ", ".join(str(option.get("option_id")) for option in row.allowed_options)
        lines.append(
            f"| `{row.row_id}` | `{row.cluster_id}` | {_escape(row.decision_required)} | "
            f"{_escape(options)} | {_escape(', '.join(row.required_answer_fields))} | {_escape(row.evidence_summary)} |"
        )
    lines.extend(["", "## Allowed Options Catalog", ""])
    for option_id, option in sorted(template.allowed_option_catalog.items()):
        lines.append(f"- `{option_id}`: {option.get('label')} -> `{option.get('allowed_next_action')}`")
    lines.extend(["", "## Required Evidence Rules", ""])
    _append_list(lines, template.required_evidence_rules)
    lines.extend(["", "## Empty Answer Placeholders", ""])
    for row in template.reviewer_rows:
        lines.append(f"- `{row.row_id}`: selected_option_id=`null`; reviewer_rationale empty")
    lines.extend(["", "## Warnings", ""])
    _append_list(lines, template.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, template.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def render_manual_decision_answer_validation_markdown(validation: ManualDecisionAnswerValidation) -> str:
    lines = [
        f"# Manual Decision Answer Validation {validation.package_id}",
        "",
        "## Summary",
        "",
        f"- Validation status: `{validation.validation_status}`",
        f"- Answer rows total: `{validation.answer_rows_total}`",
        f"- Answer rows valid: `{validation.answer_rows_valid}`",
        f"- Answer rows missing: `{validation.answer_rows_missing}`",
        f"- Answer rows rejected: `{validation.answer_rows_rejected}`",
        f"- Unsafe answers: `{len(validation.unsafe_answers)}`",
        f"- Stage 9E allowed: `{validation.stage_9e_gate.stage_9e_allowed}`",
        f"- Can prepare Stage 9E draft-only: `{validation.readiness_after_answers.can_prepare_stage_9e_draft_only}`",
        f"- Canonical write allowed: `{validation.canonical_write_allowed}`",
        "",
        "## Missing Answers",
        "",
    ]
    _append_dicts(lines, validation.missing_answers)
    lines.extend(["", "## Invalid Answers", ""])
    _append_dicts(lines, validation.invalid_answers)
    lines.extend(["", "## Unsafe Answers", ""])
    _append_dicts(lines, validation.unsafe_answers)
    lines.extend(
        [
            "",
            "## Validated Answers",
            "",
            "| Row ID | Option | Action | Status | Effect |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for answer in validation.validated_answers:
        lines.append(
            f"| `{answer.row_id}` | `{answer.selected_option_id}` | `{answer.selected_allowed_next_action}` | "
            f"`{answer.validation_status}` | {_escape(answer.normalized_effect)} |"
        )
    lines.extend(["", "## Normalized Reviewer Decisions", ""])
    _append_dicts(lines, validation.normalized_reviewer_decisions)
    lines.extend(
        [
            "",
            "## Stage 9E Gate",
            "",
            f"- Stage 9E allowed: `{validation.stage_9e_gate.stage_9e_allowed}`",
            f"- Allowed scope: `{', '.join(validation.stage_9e_gate.stage_9e_allowed_scope) or 'none'}`",
            "- Blockers:",
        ]
    )
    _append_list(lines, validation.stage_9e_gate.stage_9e_blockers)
    lines.extend(
        [
            "",
            "## Required Next Action",
            "",
            validation.readiness_after_answers.required_next_action,
            "",
            "## Safety Statement",
            "",
            "This validation is read-only. It does not create revised drafts, create canonical test cases, edit existing test cases, run apply, or authorize canonical writes.",
            "",
            "## Warnings",
            "",
        ]
    )
    _append_list(lines, validation.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, validation.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _template_row(row: ReviewerDecisionRow) -> ReviewerAnswerTemplateRow:
    option_dicts = [option.to_dict() for option in row.decision_options]
    requires_source = any(option.requires_source_evidence for option in row.decision_options)
    requires_existing = any(option.requires_existing_tc_review for option in row.decision_options)
    fields = ["row_id", "cluster_id", "selected_option_id", "reviewer_rationale"]
    if requires_source:
        fields.append("source_evidence")
    if requires_existing:
        fields.append("existing_tc_review_notes")
    fields.extend(["no_new_tc_rationale when selected option is no_new_tc_with_rationale", "defer_reason when selected option is defer", "split_guidance when selected option is split_candidate"])
    return ReviewerAnswerTemplateRow(
        row_id=row.row_id,
        cluster_id=row.cluster_id,
        decision_required=row.decision_required,
        affected_drafts=row.affected_drafts,
        affected_requirements=row.affected_requirements,
        allowed_options=option_dicts,
        requires_source_evidence=requires_source,
        requires_existing_tc_review=requires_existing,
        required_answer_fields=fields,
        evidence_summary=row.evidence_summary,
        reviewer_role=row.required_reviewer_role,
        answer_placeholder=ReviewerAnswerPlaceholder.empty(),
    )


def _validate_answer(row: ReviewerDecisionRow, answer: dict[str, Any]) -> ValidatedReviewerAnswer:
    warnings: list[str] = []
    blockers: list[str] = []
    selected_option_id = str(answer.get("selected_option_id") or "")
    option = _option_by_id(row, selected_option_id)
    rationale = str(answer.get("reviewer_rationale") or "").strip()
    source_evidence = _string_list(answer.get("source_evidence"))
    existing_notes = _string_list(answer.get("existing_tc_review_notes"))
    all_text = " ".join(
        [
            selected_option_id,
            rationale,
            " ".join(source_evidence),
            " ".join(existing_notes),
            str(answer.get("business_clarification") or ""),
            str(answer.get("no_new_tc_rationale") or ""),
            str(answer.get("defer_reason") or ""),
            str(answer.get("split_guidance") or ""),
        ]
    )
    if option is None:
        blockers.append(f"selected option is not allowed for row: {selected_option_id}")
    if not rationale:
        blockers.append("reviewer_rationale is required")
    if option and option.requires_source_evidence and not _valid_source_evidence(source_evidence):
        blockers.append("source_evidence is required and must cite req/source/analyst clarification")
    if option and option.requires_existing_tc_review and not _valid_existing_tc_notes(existing_notes):
        blockers.append("existing_tc_review_notes must state existing TC was used only as coverage evidence")
    action = option.allowed_next_action if option else None
    if action == "no_new_tc_with_rationale" and not str(answer.get("no_new_tc_rationale") or "").strip():
        blockers.append("no_new_tc_rationale is required")
    if action == "defer" and not str(answer.get("defer_reason") or "").strip():
        blockers.append("defer_reason is required")
    if action == "split_candidate" and not str(answer.get("split_guidance") or "").strip():
        blockers.append("split_guidance is required")
    unsafe_reasons = _unsafe_reasons(all_text)
    blockers.extend(unsafe_reasons)
    status: AnswerValidationStatus = "valid"
    if unsafe_reasons:
        status = "unsafe"
    elif blockers:
        status = "invalid"
    elif action == "extend_existing_tc":
        warnings.append("extend_existing_tc is valid only as future-stage review, not direct edit.")
        status = "valid-with-warnings"
    return ValidatedReviewerAnswer(
        row_id=row.row_id,
        cluster_id=row.cluster_id,
        selected_option_id=selected_option_id or None,
        selected_allowed_next_action=action,
        validation_status=status,
        reviewer_rationale=rationale,
        source_evidence=source_evidence,
        existing_tc_review_notes=existing_notes,
        normalized_effect=_normalized_effect(row, option),
        affected_drafts=row.affected_drafts,
        affected_requirements=row.affected_requirements,
        enables_revised_draft_action=action in {"revise_draft", "replace_draft", "split_candidate"},
        enables_no_new_tc=action == "no_new_tc_with_rationale",
        enables_defer=action == "defer",
        requires_followup=action in {"request_source_clarification", "keep_manual_only", "defer"},
        warnings=warnings,
        blocking_reasons=blockers,
    )


def _readiness_and_gate(
    *,
    matrix: ManualDecisionMatrix,
    answers_exist: bool,
    validated: list[ValidatedReviewerAnswer],
    missing_answers: list[dict[str, Any]],
    invalid_answers: list[dict[str, Any]],
    unsafe_answers: list[dict[str, Any]],
) -> tuple[ReadinessAfterAnswers, Stage9EGate]:
    valid = [answer for answer in validated if answer.validation_status in {"valid", "valid-with-warnings"}]
    invalid_count = len(invalid_answers)
    unsafe_count = len(unsafe_answers)
    missing_count = len(missing_answers)
    valid_actions = [answer.selected_allowed_next_action for answer in valid]
    has_revised_action = any(action in {"revise_draft", "replace_draft", "split_candidate"} for action in valid_actions)
    all_blocking_answered = missing_count == 0
    all_valid = invalid_count == 0 and unsafe_count == 0 and bool(answers_exist)
    allowed = bool(answers_exist and all_blocking_answered and all_valid and has_revised_action)
    blockers: list[str] = []
    if not answers_exist:
        blockers.append("reviewer answers file is missing")
    if missing_count:
        blockers.append("not all blocking reviewer rows are answered")
    if invalid_count:
        blockers.append("some answers are invalid")
    if unsafe_count:
        blockers.append("some answers are unsafe")
    if answers_exist and not has_revised_action:
        blockers.append("no valid answer enables revise/replace/split draft-only action")
    if not blockers and not allowed:
        blockers.append("Stage 9E remains blocked by unresolved validation state")
    readiness = ReadinessAfterAnswers(
        all_blocking_rows_answered=all_blocking_answered,
        all_answers_valid=all_valid,
        unsafe_answers_count=unsafe_count,
        missing_answers_count=missing_count,
        valid_revise_or_replace_count=sum(1 for action in valid_actions if action in {"revise_draft", "replace_draft", "split_candidate"}),
        valid_extend_existing_count=sum(1 for action in valid_actions if action == "extend_existing_tc"),
        valid_no_new_tc_count=sum(1 for action in valid_actions if action == "no_new_tc_with_rationale"),
        valid_defer_count=sum(1 for action in valid_actions if action == "defer"),
        valid_clarification_count=sum(1 for action in valid_actions if action == "request_source_clarification"),
        remaining_manual_rows=[str(item.get("row_id")) for item in missing_answers],
        can_prepare_stage_9e_draft_only=allowed,
        why_not_ready="; ".join(blockers) if blockers else "",
        required_next_action="Fill and validate reviewer answers." if not allowed else "Proceed only to draft-only Stage 9E using validated answer traceability.",
    )
    gate = Stage9EGate(
        stage_9e_allowed=allowed,
        stage_9e_allowed_scope=sorted({draft for answer in valid if answer.enables_revised_draft_action for draft in answer.affected_drafts}) if allowed else [],
        stage_9e_blockers=blockers,
        stage_9e_safety_conditions=[
            "Stage 9E output must be draft-only.",
            "canonical_write_allowed remains false.",
            "Reviewer answer row_id and selected option must be traceable in future draft artifacts.",
            "Existing TC evidence must remain coverage/comparison evidence only.",
        ],
        canonical_write_allowed=False,
        requires_draft_only_output=True,
        requires_reviewer_answer_traceability=True,
    )
    return readiness, gate


def _answer_template(
    *,
    package_id: str,
    template_status: TemplateStatus,
    source_matrix_path: str,
    reviewer_rows: list[ReviewerAnswerTemplateRow] | None = None,
    allowed_option_catalog: dict[str, dict[str, Any]] | None = None,
    input_paths: dict[str, str | None] | None = None,
    warnings: list[str] | None = None,
    blocking_reasons: list[str] | None = None,
    created_by_tool: str,
) -> ManualDecisionAnswerTemplate:
    return ManualDecisionAnswerTemplate(
        package_id=package_id,
        template_status=template_status,
        source_matrix_path=source_matrix_path,
        reviewer_rows=reviewer_rows or [],
        answer_schema_version=ANSWER_SCHEMA_VERSION,
        instructions_for_reviewer=[
            "Select exactly one allowed option per row.",
            "Provide reviewer_rationale for every answer.",
            "Provide source_evidence when the selected option requires source evidence.",
            "Provide existing_tc_review_notes when the selected option requires existing TC review.",
            "Do not authorize canonical file writes in this artifact.",
        ],
        allowed_option_catalog=allowed_option_catalog or {},
        required_evidence_rules=[
            "Source evidence must cite req uid, source req id, source artifact, or explicit analyst/product clarification.",
            "Existing TC notes must explicitly say the TC was used only as coverage evidence.",
            "No-new-TC, defer and split choices require their specific rationale fields.",
        ],
        safety_rules=[
            "Do not create or edit canonical test cases.",
            "Do not use existing TC text as a source of business rules.",
            "Do not run apply, git apply, or patch.",
            "Stage 9E is not authorized by this template.",
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


def _validation(
    *,
    package_id: str,
    validation_status: ValidationStatus,
    source_matrix_path: str,
    source_answers_path: str | None,
    answer_rows_total: int = 0,
    answer_rows_valid: int = 0,
    answer_rows_missing: int = 0,
    answer_rows_rejected: int = 0,
    validated_answers: list[ValidatedReviewerAnswer] | None = None,
    missing_answers: list[dict[str, Any]] | None = None,
    invalid_answers: list[dict[str, Any]] | None = None,
    unsafe_answers: list[dict[str, Any]] | None = None,
    normalized_reviewer_decisions: list[dict[str, Any]] | None = None,
    readiness_after_answers: ReadinessAfterAnswers | None = None,
    stage_9e_gate: Stage9EGate | None = None,
    input_paths: dict[str, str | None] | None = None,
    warnings: list[str] | None = None,
    blocking_reasons: list[str] | None = None,
    created_by_tool: str,
) -> ManualDecisionAnswerValidation:
    readiness = readiness_after_answers or ReadinessAfterAnswers(
        all_blocking_rows_answered=False,
        all_answers_valid=False,
        unsafe_answers_count=len(unsafe_answers or []),
        missing_answers_count=answer_rows_missing,
        valid_revise_or_replace_count=0,
        valid_extend_existing_count=0,
        valid_no_new_tc_count=0,
        valid_defer_count=0,
        valid_clarification_count=0,
        remaining_manual_rows=[],
        can_prepare_stage_9e_draft_only=False,
        why_not_ready="Validation is blocked.",
        required_next_action="Resolve validation blockers.",
    )
    gate = stage_9e_gate or Stage9EGate(
        stage_9e_allowed=False,
        stage_9e_allowed_scope=[],
        stage_9e_blockers=blocking_reasons or ["validation is not pass"],
        stage_9e_safety_conditions=[
            "Stage 9E output must be draft-only.",
            "canonical_write_allowed remains false.",
            "Reviewer answer traceability is required.",
        ],
        canonical_write_allowed=False,
        requires_draft_only_output=True,
        requires_reviewer_answer_traceability=True,
    )
    return ManualDecisionAnswerValidation(
        package_id=package_id,
        validation_status=validation_status,
        source_matrix_path=source_matrix_path,
        source_answers_path=source_answers_path,
        answer_rows_total=answer_rows_total,
        answer_rows_valid=answer_rows_valid,
        answer_rows_missing=answer_rows_missing,
        answer_rows_rejected=answer_rows_rejected,
        validated_answers=validated_answers or [],
        missing_answers=missing_answers or [],
        invalid_answers=invalid_answers or [],
        unsafe_answers=unsafe_answers or [],
        normalized_reviewer_decisions=normalized_reviewer_decisions or [],
        readiness_after_answers=readiness,
        stage_9e_gate=gate,
        canonical_write_allowed=False,
        manual_review_required=True,
        input_paths=input_paths or {},
        warnings=warnings or [],
        blocking_reasons=blocking_reasons or [],
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _allowed_option_catalog(rows: list[ReviewerDecisionRow]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        for option in row.decision_options:
            result.setdefault(option.option_id, option.to_dict())
    return result


def _option_by_id(row: ReviewerDecisionRow, option_id: str) -> DecisionOption | None:
    for option in row.decision_options:
        if option.option_id == option_id:
            return option
    return None


def _valid_source_evidence(values: list[str]) -> bool:
    text = " ".join(values).casefold()
    markers = ["req-", "bsr", "gsr", "src-", "source", "artifact", "analyst", "product", "clarification", "треб", "источник", "аналит"]
    return bool(values) and any(marker in text for marker in markers)


def _valid_existing_tc_notes(values: list[str]) -> bool:
    text = " ".join(values).casefold()
    return bool(values) and "coverage evidence" in text and "only" in text


def _unsafe_reasons(text: str) -> list[str]:
    lowered = text.casefold()
    reasons: list[str] = []
    if any(marker in lowered for marker in ["create canonical", "edit canonical", "write canonical", "apply directly", "--apply", "git apply", "patch file", "modify test-case"]):
        reasons.append("answer implies direct canonical create/edit/apply")
    if any(marker in lowered for marker in ["existing tc as business source", "existing tc is business source", "use existing tc as requirement", "derive business rule from existing tc"]):
        reasons.append("answer uses existing TC as a source of business rules")
    return reasons


def _normalized_effect(row: ReviewerDecisionRow, option: DecisionOption | None) -> str:
    if option is None:
        return "No normalized effect; selected option is invalid."
    return (
        f"Future-stage `{option.allowed_next_action}` may be prepared for {', '.join(row.affected_drafts) or row.row_id}; "
        "canonical writes remain disabled."
    )


def _normalized_decision(answer: ValidatedReviewerAnswer) -> dict[str, Any]:
    return {
        "row_id": answer.row_id,
        "cluster_id": answer.cluster_id,
        "allowed_next_action": answer.selected_allowed_next_action,
        "affected_drafts": answer.affected_drafts,
        "affected_requirements": answer.affected_requirements,
        "source_evidence": answer.source_evidence,
        "existing_tc_review_notes": answer.existing_tc_review_notes,
        "reviewer_rationale": answer.reviewer_rationale,
        "canonical_write_allowed": False,
    }


def _missing_answer(row: ReviewerDecisionRow) -> dict[str, Any]:
    return {
        "row_id": row.row_id,
        "cluster_id": row.cluster_id,
        "decision_required": row.decision_required,
        "reason": "blocking reviewer row has no answer",
    }


def _load_matrix(path: Path, blocking_reasons: list[str]) -> ManualDecisionMatrix | None:
    if not Path(path).exists():
        blocking_reasons.append(f"manual decision matrix is missing: {path}")
        return None
    try:
        return load_manual_decision_matrix(Path(path))
    except Exception as exc:  # noqa: BLE001 - validation reports parse failures.
        blocking_reasons.append(f"manual decision matrix cannot be parsed: {path}: {exc}")
        return None


def _load_json_object(
    path: Path,
    label: str,
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any] | None:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validation reports parse failures.
        blocking_reasons.append(f"{label} cannot be parsed: {path}: {exc}")
        return None
    if not isinstance(payload, dict):
        blocking_reasons.append(f"{label} root must be a JSON object: {path}")
        return None
    return payload


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _duplicates(values: Any) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        text = str(value)
        if text in seen:
            dupes.add(text)
        seen.add(text)
    return sorted(dupes)


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


def _append_dicts(lines: list[str], values: list[dict[str, Any]]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- `{value.get('row_id', value.get('id', 'item'))}`: {_escape(value.get('reason') or value.get('reasons') or value)}")


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


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
