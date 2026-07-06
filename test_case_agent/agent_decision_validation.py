from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.agent_decision_resolver import (
    AgentDecision,
    AgentDecisionResolution,
    load_agent_decision_resolution,
)
from test_case_agent.manual_decision_matrix import load_manual_decision_matrix

CREATED_BY_TOOL = "test_case_agent.agent_decision_validation"
AGENT_DECISION_VALIDATION_PREFIX = "agent-decision-validation"
DEFAULT_PACKAGE_ID = "WPKG-000001"

ValidationStatus = Literal["pass", "pass-with-warnings", "blocked", "rejected"]
ValidationResult = Literal["valid", "valid-with-warnings", "rejected", "unsafe", "human-review-required", "deferred"]

STAGE_9E_ACTIONS = {"revise_draft", "replace_draft", "split_candidate", "extend_existing_tc"}


@dataclass(frozen=True)
class AgentDecisionValidationResult:
    row_id: str
    cluster_id: str
    selected_allowed_next_action: str
    original_decision_status: str
    original_confidence: str
    original_confidence_score: float
    original_requires_human_review: bool
    validation_result: ValidationResult
    stage_9e_eligible: bool
    validated_stage_9e_action: str | None
    required_evidence_checks: list[dict[str, Any]]
    confidence_checks: list[dict[str, Any]]
    safety_checks: list[dict[str, Any]]
    traceability_checks: list[dict[str, Any]]
    coverage_checks: list[dict[str, Any]]
    duplicate_risk_checks: list[dict[str, Any]]
    split_candidate_checks: list[dict[str, Any]]
    existing_tc_evidence_checks: list[dict[str, Any]]
    reasoning: str
    blocking_reasons: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDecisionValidationResult":
        return cls(
            row_id=str(data["row_id"]),
            cluster_id=str(data["cluster_id"]),
            selected_allowed_next_action=str(data["selected_allowed_next_action"]),
            original_decision_status=str(data["original_decision_status"]),
            original_confidence=str(data["original_confidence"]),
            original_confidence_score=float(data.get("original_confidence_score") or 0),
            original_requires_human_review=bool(data.get("original_requires_human_review")),
            validation_result=data["validation_result"],
            stage_9e_eligible=bool(data.get("stage_9e_eligible")),
            validated_stage_9e_action=data.get("validated_stage_9e_action"),
            required_evidence_checks=list(data.get("required_evidence_checks") or []),
            confidence_checks=list(data.get("confidence_checks") or []),
            safety_checks=list(data.get("safety_checks") or []),
            traceability_checks=list(data.get("traceability_checks") or []),
            coverage_checks=list(data.get("coverage_checks") or []),
            duplicate_risk_checks=list(data.get("duplicate_risk_checks") or []),
            split_candidate_checks=list(data.get("split_candidate_checks") or []),
            existing_tc_evidence_checks=list(data.get("existing_tc_evidence_checks") or []),
            reasoning=str(data.get("reasoning") or ""),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class AgentDecisionValidationReport:
    package_id: str
    validation_status: ValidationStatus
    source_resolution_path: str
    source_artifacts: dict[str, str | None]
    validation_checks: list[dict[str, Any]]
    decision_validation_results: list[AgentDecisionValidationResult]
    validated_stage_9e_scope: dict[str, Any]
    rejected_stage_9e_scope: dict[str, Any]
    human_review_scope: dict[str, Any]
    deferred_scope: dict[str, Any]
    gate_hardening_summary: dict[str, Any]
    stage_9e_gate_hardened: dict[str, Any]
    readiness_after_validation: dict[str, Any]
    safety_summary: dict[str, Any]
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
            "source_resolution_path": self.source_resolution_path,
            "source_artifacts": self.source_artifacts,
            "validation_checks": self.validation_checks,
            "decision_validation_results": [item.to_dict() for item in self.decision_validation_results],
            "validated_stage_9e_scope": self.validated_stage_9e_scope,
            "rejected_stage_9e_scope": self.rejected_stage_9e_scope,
            "human_review_scope": self.human_review_scope,
            "deferred_scope": self.deferred_scope,
            "gate_hardening_summary": self.gate_hardening_summary,
            "stage_9e_gate_hardened": self.stage_9e_gate_hardened,
            "readiness_after_validation": self.readiness_after_validation,
            "safety_summary": self.safety_summary,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDecisionValidationReport":
        return cls(
            package_id=str(data["package_id"]),
            validation_status=data["validation_status"],
            source_resolution_path=str(data.get("source_resolution_path") or ""),
            source_artifacts=dict(data.get("source_artifacts") or {}),
            validation_checks=list(data.get("validation_checks") or []),
            decision_validation_results=[
                AgentDecisionValidationResult.from_dict(item)
                for item in data.get("decision_validation_results", [])
            ],
            validated_stage_9e_scope=dict(data.get("validated_stage_9e_scope") or {}),
            rejected_stage_9e_scope=dict(data.get("rejected_stage_9e_scope") or {}),
            human_review_scope=dict(data.get("human_review_scope") or {}),
            deferred_scope=dict(data.get("deferred_scope") or {}),
            gate_hardening_summary=dict(data.get("gate_hardening_summary") or {}),
            stage_9e_gate_hardened=dict(data.get("stage_9e_gate_hardened") or {}),
            readiness_after_validation=dict(data.get("readiness_after_validation") or {}),
            safety_summary=dict(data.get("safety_summary") or {}),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_agent_decision_validation_report(
    *,
    package_id: str,
    resolution_path: Path,
    matrix_path: Path,
    context_bundle_path: Path,
    draft_proposal_path: Path | None = None,
    decision_pack_path: Path | None = None,
    residual_analysis_path: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> AgentDecisionValidationReport:
    input_paths = {
        "resolution_path": str(resolution_path),
        "matrix_path": str(matrix_path),
        "context_bundle_path": str(context_bundle_path),
        "draft_proposal_path": str(draft_proposal_path) if draft_proposal_path else None,
        "decision_pack_path": str(decision_pack_path) if decision_pack_path else None,
        "residual_analysis_path": str(residual_analysis_path) if residual_analysis_path else None,
    }
    now = _utc_now()
    missing = _missing_paths(
        resolution_path=resolution_path,
        matrix_path=matrix_path,
        context_bundle_path=context_bundle_path,
    )
    if missing:
        return _blocked_report(package_id, str(resolution_path), input_paths, missing, now, created_by_tool)

    resolution = load_agent_decision_resolution(resolution_path)
    matrix = load_manual_decision_matrix(matrix_path)
    context_bundle = _read_json(context_bundle_path)
    draft_proposal = _read_json(draft_proposal_path) if draft_proposal_path and Path(draft_proposal_path).exists() else {}

    validation_checks = _top_level_checks(package_id, resolution, matrix)
    blocking_reasons = [check["message"] for check in validation_checks if check["status"] == "failed"]
    if blocking_reasons:
        return _blocked_report(
            package_id,
            str(resolution_path),
            input_paths,
            blocking_reasons,
            now,
            created_by_tool,
            source_artifacts=resolution.source_artifacts,
            validation_checks=validation_checks,
        )

    req_context = {str(item.get("req_uid")): item for item in context_bundle.get("candidate_requirements", []) if item.get("req_uid")}
    draft_ids = {
        str(item.get("draft_id"))
        for item in draft_proposal.get("draft_test_cases", [])
        if item.get("draft_id")
    }
    results = [_validate_decision(decision, req_context, draft_ids) for decision in resolution.agent_decisions]
    validated_scope = _scope_for(results, "valid", stage_only=True)
    valid_with_warnings_scope = _scope_for(results, "valid-with-warnings", stage_only=True)
    validated_scope = _merge_scopes(validated_scope, valid_with_warnings_scope)
    rejected_scope = _scope_for(results, "rejected", original_stage_candidates=True)
    human_scope = _scope_for(results, "human-review-required")
    deferred_scope = _scope_for(results, "deferred")
    gate = _hardened_gate(results, validated_scope, rejected_scope)
    warnings = []
    if rejected_scope["row_ids"]:
        warnings.append("Some original Stage 9E candidate rows were rejected by hardened validation.")
    if human_scope["row_ids"] or deferred_scope["row_ids"]:
        warnings.append("Some rows remain outside validated agent-driven scope.")
    status: ValidationStatus = "pass"
    if not gate["stage_9e_allowed"] and resolution.stage_9e_gate.get("stage_9e_allowed"):
        status = "rejected"
    elif warnings:
        status = "pass-with-warnings"
    if any(result.validation_result == "unsafe" for result in results):
        status = "rejected"
    return AgentDecisionValidationReport(
        package_id=package_id,
        validation_status=status,
        source_resolution_path=str(resolution_path),
        source_artifacts=resolution.source_artifacts,
        validation_checks=validation_checks,
        decision_validation_results=results,
        validated_stage_9e_scope=validated_scope,
        rejected_stage_9e_scope=rejected_scope,
        human_review_scope=human_scope,
        deferred_scope=deferred_scope,
        gate_hardening_summary={
            "original_stage_9e_allowed": resolution.stage_9e_gate.get("stage_9e_allowed"),
            "original_stage_9e_scope": resolution.stage_9e_gate.get("stage_9e_allowed_scope"),
            "validated_stage_9e_rows": len(validated_scope["row_ids"]),
            "rejected_stage_9e_rows": len(rejected_scope["row_ids"]),
        },
        stage_9e_gate_hardened=gate,
        readiness_after_validation={
            "can_prepare_stage_9e_draft_only": gate["stage_9e_allowed"],
            "required_next_action": (
                "build_stage_9e_revised_draft_proposal"
                if gate["stage_9e_allowed"]
                else "stop_before_stage_9e_and_fix_rejected_agent_decisions"
            ),
        },
        safety_summary={
            "canonical_write_allowed": False,
            "any_decision_creates_or_edits_canonical_tc": any(
                decision.creates_or_edits_canonical_tc for decision in resolution.agent_decisions
            ),
            "existing_tc_used_only_as_coverage_evidence": all(
                decision.duplicate_risk_assessment.existing_tc_used_only_as_coverage_evidence
                for decision in resolution.agent_decisions
            ),
            "unsafe_rows": [result.row_id for result in results if result.validation_result == "unsafe"],
        },
        canonical_write_allowed=False,
        manual_review_required=bool(human_scope["row_ids"] or deferred_scope["row_ids"] or rejected_scope["row_ids"]),
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=[],
        created_at_utc=now,
        created_by_tool=created_by_tool,
    )


def write_agent_decision_validation_report(report: AgentDecisionValidationReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{AGENT_DECISION_VALIDATION_PREFIX}-{report.package_id}.json"
    markdown_path = out_dir / f"{AGENT_DECISION_VALIDATION_PREFIX}-{report.package_id}.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    markdown_path.write_text(render_agent_decision_validation_markdown(report), encoding="utf-8-sig", newline="\n")
    return json_path, markdown_path


def load_agent_decision_validation_report(path: Path) -> AgentDecisionValidationReport:
    return AgentDecisionValidationReport.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def render_agent_decision_validation_markdown(report: AgentDecisionValidationReport) -> str:
    gate = report.stage_9e_gate_hardened
    lines = [
        f"# Agent Decision Validation {report.package_id}",
        "",
        "This is Stage 9D.9 hardened validation for agent_decision_resolution. It is not reviewer approval.",
        "",
        "## Summary",
        "",
        f"- validation_status: `{report.validation_status}`",
        f"- hardened_stage_9e_allowed: `{gate.get('stage_9e_allowed')}`",
        f"- validated rows: `{', '.join(report.validated_stage_9e_scope.get('row_ids', [])) or '-'}`",
        f"- rejected rows: `{', '.join(report.rejected_stage_9e_scope.get('row_ids', [])) or '-'}`",
        f"- canonical_write_allowed: `{report.canonical_write_allowed}`",
        "",
        "## Hardened Gate",
        "",
        f"- stage_9e_allowed: `{gate.get('stage_9e_allowed')}`",
        f"- blockers: `{'; '.join(gate.get('stage_9e_blockers', [])) or '-'}`",
        f"- warnings: `{'; '.join(gate.get('stage_9e_warnings', [])) or '-'}`",
        "",
        "## Decision Results",
        "",
        "| Row | Action | Original status | Validation result | Eligible | Reasoning | Blockers |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in report.decision_validation_results:
        lines.append(
            f"| {result.row_id} | `{result.selected_allowed_next_action}` | `{result.original_decision_status}` | `{result.validation_result}` | `{result.stage_9e_eligible}` | {_md(_short(result.reasoning, 180))} | {_md('; '.join(result.blocking_reasons) or '-')} |"
        )
    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "Validation does not create Stage 9E output by itself, does not create reviewer answers JSON, does not edit canonical test-cases, and keeps canonical writes disabled.",
        ]
    )
    return "\n".join(lines) + "\n"


def _validate_decision(
    decision: AgentDecision,
    req_context: dict[str, dict[str, Any]],
    draft_ids: set[str],
) -> AgentDecisionValidationResult:
    required_evidence_checks = [
        _check("source_object", decision.source_fact_coverage.has_source_backed_object, "source-backed object exists"),
        _check("source_action", decision.source_fact_coverage.has_source_backed_action, "source-backed action exists"),
        _check("source_oracle", decision.source_fact_coverage.has_source_backed_oracle, "source-backed observable oracle exists"),
        _check("source_refs", bool(decision.source_evidence_refs), "source refs are present"),
    ]
    confidence_checks = [
        _check("confidence_threshold", decision.confidence_score >= 0.70, "confidence score is >= 0.70"),
        _check("not_low_confidence", decision.confidence != "low", "confidence is not low"),
    ]
    safety_checks = [
        _check("canonical_write_disabled", not decision.creates_or_edits_canonical_tc, "decision does not imply canonical writes"),
        _check("no_safety_warnings", not decision.safety_warnings, "decision has no safety warnings"),
        _check("no_human_review_in_scope", not decision.requires_human_review, "decision does not require human review"),
    ]
    traceability_checks = [
        _check("row_id_present", bool(decision.row_id), "row id is present"),
        _check("affected_requirements_present", bool(decision.affected_requirements), "affected requirements are listed"),
    ]
    coverage_checks = [
        _check(
            "candidate_requirements_in_context",
            all(req_uid in req_context for req_uid in decision.affected_requirements),
            "affected requirements are present in context bundle",
        )
    ]
    duplicate_risk_checks = [
        _check(
            "no_high_duplicate_risk",
            decision.duplicate_risk_assessment.risk_level != "high",
            "duplicate risk is not high",
        ),
        _check(
            "existing_tc_coverage_only",
            decision.duplicate_risk_assessment.existing_tc_used_only_as_coverage_evidence
            and all(not item.get("used_as_business_rule_source") for item in decision.existing_tc_coverage_evidence),
            "existing TC evidence is coverage-only",
        ),
    ]
    split_candidate_checks = _split_candidate_checks(decision, draft_ids)
    existing_tc_evidence_checks = [
        _check(
            "existing_tc_not_business_source",
            all(not item.get("used_as_business_rule_source") for item in decision.existing_tc_coverage_evidence),
            "existing TC is not used as business source",
        )
    ]
    all_checks = (
        required_evidence_checks
        + confidence_checks
        + safety_checks
        + traceability_checks
        + coverage_checks
        + duplicate_risk_checks
        + split_candidate_checks
        + existing_tc_evidence_checks
    )
    blockers = [check["message"] for check in all_checks if check["status"] == "failed"]
    is_original_candidate = decision.enables_stage_9e_draft_only or decision.selected_allowed_next_action in STAGE_9E_ACTIONS
    if decision.decision_status == "unsafe":
        result: ValidationResult = "unsafe"
    elif decision.decision_status == "deferred":
        result = "deferred"
    elif decision.decision_status == "needs_human_review":
        result = "human-review-required"
    elif is_original_candidate and blockers:
        result = "rejected"
    elif is_original_candidate:
        result = "valid-with-warnings" if any(check["status"] == "warning" for check in all_checks) else "valid"
    else:
        result = "valid" if not blockers else "human-review-required"
    eligible = result in {"valid", "valid-with-warnings"} and decision.selected_allowed_next_action in STAGE_9E_ACTIONS
    if decision.row_id == "MDR-000012":
        if eligible:
            reasoning = "MDR-000012 passed hardened gate."
        else:
            reasoning = "MDR-000012 rejected from Stage 9E scope: " + "; ".join(blockers)
    elif eligible:
        reasoning = "Decision passed hardened Stage 9E validation."
    elif blockers:
        reasoning = "Decision is not Stage 9E eligible: " + "; ".join(blockers)
    else:
        reasoning = "Decision remains outside Stage 9E scope by status/action."
    return AgentDecisionValidationResult(
        row_id=decision.row_id,
        cluster_id=decision.cluster_id,
        selected_allowed_next_action=decision.selected_allowed_next_action,
        original_decision_status=decision.decision_status,
        original_confidence=decision.confidence,
        original_confidence_score=decision.confidence_score,
        original_requires_human_review=decision.requires_human_review,
        validation_result=result,
        stage_9e_eligible=eligible,
        validated_stage_9e_action=decision.selected_allowed_next_action if eligible else None,
        required_evidence_checks=required_evidence_checks,
        confidence_checks=confidence_checks,
        safety_checks=safety_checks,
        traceability_checks=traceability_checks,
        coverage_checks=coverage_checks,
        duplicate_risk_checks=duplicate_risk_checks,
        split_candidate_checks=split_candidate_checks,
        existing_tc_evidence_checks=existing_tc_evidence_checks,
        reasoning=reasoning,
        blocking_reasons=blockers,
        warnings=[],
    )


def _split_candidate_checks(decision: AgentDecision, draft_ids: set[str]) -> list[dict[str, Any]]:
    if decision.selected_allowed_next_action != "split_candidate":
        return [_check("split_candidate_not_applicable", True, "not a split_candidate row")]
    return [
        _check(
            "split_has_multiple_requirements",
            len(decision.affected_requirements) > 1,
            "split_candidate has multiple affected requirements",
            "split_candidate must reference multiple affected requirements",
        ),
        _check(
            "split_has_affected_drafts",
            bool(decision.affected_drafts),
            "split_candidate has affected drafts listed",
            "split_candidate does not list affected drafts",
        ),
        _check(
            "split_drafts_exist",
            bool(decision.affected_drafts) and all(draft_id in draft_ids for draft_id in decision.affected_drafts),
            "split_candidate affected drafts exist in source proposal",
            "split_candidate affected drafts are missing from source proposal",
        ),
        _check(
            "split_boundaries_source_backed",
            decision.source_fact_coverage.has_real_table_context
            and bool(decision.affected_requirements)
            and not decision.source_fact_coverage.facts_missing,
            "split boundaries are source-backed by table context and complete source facts",
            "split boundaries are not fully source-backed by table context and complete source facts",
        ),
    ]


def _top_level_checks(package_id: str, resolution: AgentDecisionResolution, matrix: Any) -> list[dict[str, Any]]:
    resolution_rows = {decision.row_id for decision in resolution.agent_decisions}
    matrix_rows = {row.row_id for row in matrix.reviewer_decision_rows}
    return [
        _check("package_id_match", resolution.package_id == package_id == matrix.package_id, "package_id matches"),
        _check("canonical_write_disabled", not resolution.canonical_write_allowed, "resolution canonical writes disabled"),
        _check("agent_decisions_present", bool(resolution.agent_decisions), "resolution has agent decisions"),
        _check("row_ids_match_matrix", resolution_rows == matrix_rows, "decision row ids match matrix row ids"),
        _check(
            "decision_source_agent_resolution",
            all(decision.decision_source == "agent_resolution" for decision in resolution.agent_decisions),
            "all decisions use decision_source=agent_resolution",
        ),
        _check(
            "no_reviewer_terminology_source",
            all(
                decision.decision_source not in {"reviewer_answers", "human_decision", "approved"}
                for decision in resolution.agent_decisions
            ),
            "decisions do not use reviewer/human approval terminology as source",
        ),
    ]


def _hardened_gate(
    results: list[AgentDecisionValidationResult],
    validated_scope: dict[str, Any],
    rejected_scope: dict[str, Any],
) -> dict[str, Any]:
    blockers = []
    if not validated_scope["row_ids"]:
        blockers.append("no validated Stage 9E eligible rows")
    return {
        "stage_9e_allowed": bool(validated_scope["row_ids"] and not blockers),
        "stage_9e_allowed_scope": validated_scope,
        "stage_9e_rejected_scope": rejected_scope,
        "stage_9e_blockers": blockers,
        "stage_9e_warnings": [
            warning
            for result in results
            for warning in result.warnings
            if result.stage_9e_eligible
        ],
        "stage_9e_safety_conditions": [
            "draft-only output",
            "agent_decision row traceability required",
            "validation traceability required",
            "no human-review rows in scope",
            "no deferred rows in scope",
            "no low-confidence rows in scope",
            "no unclassified warnings in scope",
            "canonical_write_allowed=false",
        ],
        "canonical_write_allowed": False,
        "requires_draft_only_output": True,
        "requires_agent_decision_traceability": True,
        "requires_validation_traceability": True,
        "requires_no_human_review_rows_in_scope": True,
        "requires_no_deferred_rows_in_scope": True,
        "requires_no_low_confidence_rows_in_scope": True,
        "requires_no_unclassified_warnings_in_scope": True,
    }


def _scope_for(
    results: list[AgentDecisionValidationResult],
    validation_result: str,
    *,
    stage_only: bool = False,
    original_stage_candidates: bool = False,
) -> dict[str, Any]:
    selected = []
    for result in results:
        if result.validation_result != validation_result:
            continue
        if stage_only and not result.stage_9e_eligible:
            continue
        if original_stage_candidates and result.selected_allowed_next_action not in STAGE_9E_ACTIONS:
            continue
        selected.append(result)
    return {
        "row_ids": [result.row_id for result in selected],
        "actions": sorted({result.selected_allowed_next_action for result in selected}),
    }


def _merge_scopes(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_ids": first.get("row_ids", []) + second.get("row_ids", []),
        "actions": sorted(set(first.get("actions", [])) | set(second.get("actions", []))),
    }


def _check(check_id: str, passed: bool, message: str, failure_message: str | None = None) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if passed else "failed",
        "message": message if passed or not failure_message else failure_message,
    }


def _missing_paths(**paths: Path | None) -> list[str]:
    reasons = []
    for name, path in paths.items():
        if path is None or not Path(path).exists():
            reasons.append(f"{name} is missing: {path}")
    return reasons


def _blocked_report(
    package_id: str,
    resolution_path: str,
    input_paths: dict[str, str | None],
    blocking_reasons: list[str],
    created_at_utc: str,
    created_by_tool: str,
    *,
    source_artifacts: dict[str, str | None] | None = None,
    validation_checks: list[dict[str, Any]] | None = None,
) -> AgentDecisionValidationReport:
    return AgentDecisionValidationReport(
        package_id=package_id,
        validation_status="blocked",
        source_resolution_path=resolution_path,
        source_artifacts=source_artifacts or {},
        validation_checks=validation_checks or [],
        decision_validation_results=[],
        validated_stage_9e_scope={"row_ids": [], "actions": []},
        rejected_stage_9e_scope={"row_ids": [], "actions": []},
        human_review_scope={"row_ids": [], "actions": []},
        deferred_scope={"row_ids": [], "actions": []},
        gate_hardening_summary={},
        stage_9e_gate_hardened={
            "stage_9e_allowed": False,
            "stage_9e_allowed_scope": {"row_ids": [], "actions": []},
            "stage_9e_rejected_scope": {"row_ids": [], "actions": []},
            "stage_9e_blockers": blocking_reasons,
            "canonical_write_allowed": False,
            "requires_draft_only_output": True,
            "requires_agent_decision_traceability": True,
            "requires_validation_traceability": True,
            "requires_no_human_review_rows_in_scope": True,
            "requires_no_deferred_rows_in_scope": True,
            "requires_no_low_confidence_rows_in_scope": True,
            "requires_no_unclassified_warnings_in_scope": True,
        },
        readiness_after_validation={
            "can_prepare_stage_9e_draft_only": False,
            "required_next_action": "fix_blocking_inputs",
        },
        safety_summary={"canonical_write_allowed": False},
        canonical_write_allowed=False,
        manual_review_required=True,
        input_paths=input_paths,
        warnings=[],
        blocking_reasons=blocking_reasons,
        created_at_utc=created_at_utc,
        created_by_tool=created_by_tool,
    )


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _md(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _short(value: str, limit: int) -> str:
    value = " ".join(str(value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"
