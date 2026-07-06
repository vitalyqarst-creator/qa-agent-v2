from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

CREATED_BY_TOOL = "test_case_agent.manual_decision_matrix"
MATRIX_PREFIX = "manual-decision-matrix"
DEFAULT_PACKAGE_ID = "WPKG-000001"
DEFAULT_BENCHMARK_NAME = "AutoFin WPKG-000001 manual decision benchmark"

MatrixStatus = Literal["pass", "pass-with-warnings", "blocked"]
ClusterType = Literal[
    "duplicate_risk",
    "source_grounding",
    "replacement_strategy",
    "defer_or_no_new_tc",
    "mixed",
]
Priority = Literal["P0", "P1", "P2", "P3"]
RiskLevel = Literal["low", "medium", "high"]
AllowedNextAction = Literal[
    "revise_draft",
    "replace_draft",
    "extend_existing_tc",
    "defer",
    "no_new_tc_with_rationale",
    "request_source_clarification",
    "split_candidate",
    "keep_manual_only",
]


@dataclass(frozen=True)
class DecisionOption:
    option_id: str
    label: str
    meaning: str
    allowed_next_action: AllowedNextAction
    requires_source_evidence: bool
    requires_existing_tc_review: bool
    creates_or_edits_canonical_tc: bool
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecisionOption":
        return cls(
            option_id=str(data["option_id"]),
            label=str(data["label"]),
            meaning=str(data["meaning"]),
            allowed_next_action=data["allowed_next_action"],
            requires_source_evidence=bool(data.get("requires_source_evidence")),
            requires_existing_tc_review=bool(data.get("requires_existing_tc_review")),
            creates_or_edits_canonical_tc=bool(data.get("creates_or_edits_canonical_tc")),
            notes=list(data.get("notes") or []),
        )


@dataclass(frozen=True)
class ManualDecisionCluster:
    cluster_id: str
    cluster_type: ClusterType
    priority: Priority
    affected_draft_ids: list[str]
    affected_proposed_tc_ids: list[str]
    affected_req_uids: list[str]
    source_req_ids: list[str]
    similar_existing_tc_refs: list[str]
    evidence: list[str]
    root_cause: str
    reviewer_question: str
    allowed_decisions: list[DecisionOption]
    recommended_default: str | None
    blocked_until_answered: bool
    safety_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_type": self.cluster_type,
            "priority": self.priority,
            "affected_draft_ids": self.affected_draft_ids,
            "affected_proposed_tc_ids": self.affected_proposed_tc_ids,
            "affected_req_uids": self.affected_req_uids,
            "source_req_ids": self.source_req_ids,
            "similar_existing_tc_refs": self.similar_existing_tc_refs,
            "evidence": self.evidence,
            "root_cause": self.root_cause,
            "reviewer_question": self.reviewer_question,
            "allowed_decisions": [item.to_dict() for item in self.allowed_decisions],
            "recommended_default": self.recommended_default,
            "blocked_until_answered": self.blocked_until_answered,
            "safety_notes": self.safety_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualDecisionCluster":
        return cls(
            cluster_id=str(data["cluster_id"]),
            cluster_type=data["cluster_type"],
            priority=data["priority"],
            affected_draft_ids=list(data.get("affected_draft_ids") or []),
            affected_proposed_tc_ids=list(data.get("affected_proposed_tc_ids") or []),
            affected_req_uids=list(data.get("affected_req_uids") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            similar_existing_tc_refs=list(data.get("similar_existing_tc_refs") or []),
            evidence=list(data.get("evidence") or []),
            root_cause=str(data["root_cause"]),
            reviewer_question=str(data["reviewer_question"]),
            allowed_decisions=[DecisionOption.from_dict(item) for item in data.get("allowed_decisions", [])],
            recommended_default=data.get("recommended_default"),
            blocked_until_answered=bool(data.get("blocked_until_answered")),
            safety_notes=list(data.get("safety_notes") or []),
        )


@dataclass(frozen=True)
class ReviewerDecisionRow:
    row_id: str
    cluster_id: str
    decision_required: str
    reviewer_prompt: str
    decision_options: list[DecisionOption]
    option_effects: list[str]
    affected_drafts: list[str]
    affected_requirements: list[str]
    evidence_summary: str
    source_evidence_refs: list[str]
    existing_tc_evidence_refs: list[str]
    risk_level: RiskLevel
    required_reviewer_role: str
    is_blocking_for_revised_draft: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "cluster_id": self.cluster_id,
            "decision_required": self.decision_required,
            "reviewer_prompt": self.reviewer_prompt,
            "decision_options": [item.to_dict() for item in self.decision_options],
            "option_effects": self.option_effects,
            "affected_drafts": self.affected_drafts,
            "affected_requirements": self.affected_requirements,
            "evidence_summary": self.evidence_summary,
            "source_evidence_refs": self.source_evidence_refs,
            "existing_tc_evidence_refs": self.existing_tc_evidence_refs,
            "risk_level": self.risk_level,
            "required_reviewer_role": self.required_reviewer_role,
            "is_blocking_for_revised_draft": self.is_blocking_for_revised_draft,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewerDecisionRow":
        return cls(
            row_id=str(data["row_id"]),
            cluster_id=str(data["cluster_id"]),
            decision_required=str(data["decision_required"]),
            reviewer_prompt=str(data["reviewer_prompt"]),
            decision_options=[DecisionOption.from_dict(item) for item in data.get("decision_options", [])],
            option_effects=list(data.get("option_effects") or []),
            affected_drafts=list(data.get("affected_drafts") or []),
            affected_requirements=list(data.get("affected_requirements") or []),
            evidence_summary=str(data["evidence_summary"]),
            source_evidence_refs=list(data.get("source_evidence_refs") or []),
            existing_tc_evidence_refs=list(data.get("existing_tc_evidence_refs") or []),
            risk_level=data["risk_level"],
            required_reviewer_role=str(data["required_reviewer_role"]),
            is_blocking_for_revised_draft=bool(data.get("is_blocking_for_revised_draft")),
        )


@dataclass(frozen=True)
class ReadinessImpact:
    current_needs_manual_decision_count: int
    current_ready_for_revised_draft_proposal: bool
    matrix_rows_count: int
    blocking_rows_count: int
    estimated_reviewer_questions_reduction: int
    remaining_blockers_after_matrix: list[str]
    can_proceed_to_stage_9e_without_answers: bool
    why_not_ready: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReadinessImpact":
        return cls(
            current_needs_manual_decision_count=int(data.get("current_needs_manual_decision_count") or 0),
            current_ready_for_revised_draft_proposal=bool(data.get("current_ready_for_revised_draft_proposal")),
            matrix_rows_count=int(data.get("matrix_rows_count") or 0),
            blocking_rows_count=int(data.get("blocking_rows_count") or 0),
            estimated_reviewer_questions_reduction=int(data.get("estimated_reviewer_questions_reduction") or 0),
            remaining_blockers_after_matrix=list(data.get("remaining_blockers_after_matrix") or []),
            can_proceed_to_stage_9e_without_answers=bool(data.get("can_proceed_to_stage_9e_without_answers")),
            why_not_ready=str(data["why_not_ready"]),
        )


@dataclass
class ManualDecisionMatrix:
    package_id: str
    matrix_status: MatrixStatus
    benchmark_name: str
    source_artifacts: dict[str, str | None]
    summary: dict[str, Any]
    decision_clusters: list[ManualDecisionCluster]
    reviewer_decision_rows: list[ReviewerDecisionRow]
    compressed_manual_questions: list[dict[str, Any]]
    duplicate_risk_decision_groups: list[dict[str, Any]]
    source_grounding_decision_groups: list[dict[str, Any]]
    replacement_decision_groups: list[dict[str, Any]]
    defer_decision_groups: list[dict[str, Any]]
    readiness_impact: ReadinessImpact
    expected_reviewer_outputs: list[str]
    safety_statement: str
    canonical_write_allowed: bool
    manual_review_required: bool
    ready_for_revised_draft_proposal_after_matrix: bool
    input_paths: dict[str, str | None]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "matrix_status": self.matrix_status,
            "benchmark_name": self.benchmark_name,
            "source_artifacts": self.source_artifacts,
            "summary": self.summary,
            "decision_clusters": [item.to_dict() for item in self.decision_clusters],
            "reviewer_decision_rows": [item.to_dict() for item in self.reviewer_decision_rows],
            "compressed_manual_questions": self.compressed_manual_questions,
            "duplicate_risk_decision_groups": self.duplicate_risk_decision_groups,
            "source_grounding_decision_groups": self.source_grounding_decision_groups,
            "replacement_decision_groups": self.replacement_decision_groups,
            "defer_decision_groups": self.defer_decision_groups,
            "readiness_impact": self.readiness_impact.to_dict(),
            "expected_reviewer_outputs": self.expected_reviewer_outputs,
            "safety_statement": self.safety_statement,
            "canonical_write_allowed": self.canonical_write_allowed,
            "manual_review_required": self.manual_review_required,
            "ready_for_revised_draft_proposal_after_matrix": self.ready_for_revised_draft_proposal_after_matrix,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualDecisionMatrix":
        return cls(
            package_id=str(data["package_id"]),
            matrix_status=data["matrix_status"],
            benchmark_name=str(data.get("benchmark_name") or ""),
            source_artifacts=dict(data.get("source_artifacts") or {}),
            summary=dict(data.get("summary") or {}),
            decision_clusters=[ManualDecisionCluster.from_dict(item) for item in data.get("decision_clusters", [])],
            reviewer_decision_rows=[
                ReviewerDecisionRow.from_dict(item) for item in data.get("reviewer_decision_rows", [])
            ],
            compressed_manual_questions=list(data.get("compressed_manual_questions") or []),
            duplicate_risk_decision_groups=list(data.get("duplicate_risk_decision_groups") or []),
            source_grounding_decision_groups=list(data.get("source_grounding_decision_groups") or []),
            replacement_decision_groups=list(data.get("replacement_decision_groups") or []),
            defer_decision_groups=list(data.get("defer_decision_groups") or []),
            readiness_impact=ReadinessImpact.from_dict(data["readiness_impact"]),
            expected_reviewer_outputs=list(data.get("expected_reviewer_outputs") or []),
            safety_statement=str(data.get("safety_statement") or ""),
            canonical_write_allowed=bool(data.get("canonical_write_allowed")),
            manual_review_required=bool(data.get("manual_review_required")),
            ready_for_revised_draft_proposal_after_matrix=bool(
                data.get("ready_for_revised_draft_proposal_after_matrix")
            ),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data.get("created_at_utc") or ""),
            created_by_tool=str(data.get("created_by_tool") or ""),
        )


def build_manual_decision_matrix(
    *,
    package_id: str,
    decision_pack_path: Path,
    residual_analysis_path: Path,
    improvement_plan_path: Path,
    draft_proposal_path: Path,
    draft_review_path: Path,
    draft_revision_plan_path: Path,
    context_bundle_path: Path,
    final_registry_path: Path,
    requirements_diff_path: Path,
    impact_report_path: Path,
    update_plan_path: Path,
    test_cases_dir: Path,
    benchmark_name: str = DEFAULT_BENCHMARK_NAME,
    created_by_tool: str = CREATED_BY_TOOL,
) -> ManualDecisionMatrix:
    input_paths = _input_paths(
        decision_pack_path=decision_pack_path,
        residual_analysis_path=residual_analysis_path,
        improvement_plan_path=improvement_plan_path,
        draft_proposal_path=draft_proposal_path,
        draft_review_path=draft_review_path,
        draft_revision_plan_path=draft_revision_plan_path,
        context_bundle_path=context_bundle_path,
        final_registry_path=final_registry_path,
        requirements_diff_path=requirements_diff_path,
        impact_report_path=impact_report_path,
        update_plan_path=update_plan_path,
        test_cases_dir=test_cases_dir,
    )
    warnings: list[str] = []
    blocking_reasons: list[str] = []

    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"manual decision matrix is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")

    required_inputs = {
        "decision pack": decision_pack_path,
        "residual source-grounding analysis": residual_analysis_path,
        "agent capability improvement plan": improvement_plan_path,
        "draft proposal": draft_proposal_path,
        "draft review": draft_review_path,
        "draft revision plan": draft_revision_plan_path,
        "context bundle": context_bundle_path,
    }
    for label, path in required_inputs.items():
        if not Path(path).exists():
            blocking_reasons.append(f"{label} is missing: {path}")

    decision_pack = _load_json_object(decision_pack_path, "decision pack", warnings, blocking_reasons, required=True)
    residual = _load_json_object(residual_analysis_path, "residual source-grounding analysis", warnings, blocking_reasons, required=True)
    improvement_plan = _load_json_object(improvement_plan_path, "agent capability improvement plan", warnings, blocking_reasons, required=True)
    proposal = _load_json_object(draft_proposal_path, "draft proposal", warnings, blocking_reasons, required=True)
    review = _load_json_object(draft_review_path, "draft review", warnings, blocking_reasons, required=True)
    revision_plan = _load_json_object(draft_revision_plan_path, "draft revision plan", warnings, blocking_reasons, required=True)
    context_bundle = _load_json_object(context_bundle_path, "context bundle", warnings, blocking_reasons, required=True)
    requirements_diff = _load_json_object(requirements_diff_path, "requirements diff", warnings, [], required=False)
    impact_report = _load_json_object(impact_report_path, "impact report", warnings, [], required=False)
    update_plan = _load_json_object(update_plan_path, "test-case update plan", warnings, [], required=False)

    final_registry_count = _registry_count(final_registry_path, warnings)
    for label, artifact in {
        "decision pack": decision_pack,
        "residual analysis": residual,
        "improvement plan": improvement_plan,
        "draft proposal": proposal,
        "draft review": review,
        "draft revision plan": revision_plan,
        "context bundle": context_bundle,
    }.items():
        if artifact is not None and str(artifact.get("package_id")) != package_id:
            blocking_reasons.append(f"{label} package_id mismatch: {artifact.get('package_id')} != {package_id}")

    if blocking_reasons or decision_pack is None or residual is None:
        return _empty_matrix(
            package_id=package_id,
            matrix_status="blocked",
            benchmark_name=benchmark_name,
            input_paths=input_paths,
            warnings=_unique(warnings),
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    raw_questions = _raw_manual_questions(decision_pack, residual, review, revision_plan)
    draft_by_id = _index_by_key(decision_pack.get("draft_decisions"), "draft_id")
    req_to_source = _req_to_source_id(context_bundle, residual)
    source_artifacts = {
        "decision_pack_status": str(decision_pack.get("decision_pack_status")),
        "residual_analysis_status": str(residual.get("analysis_status")),
        "improvement_plan_status": str(improvement_plan.get("plan_status")) if improvement_plan else None,
        "draft_review_status": str(review.get("review_status")) if review else None,
        "final_registry_entries": str(final_registry_count) if final_registry_count is not None else None,
        "requirements_diff_status": str((requirements_diff or {}).get("diff_status")),
        "impact_report_status": str((impact_report or {}).get("impact_status")),
        "update_plan_status": str((update_plan or {}).get("plan_status")),
    }

    duplicate_groups, duplicate_clusters = _duplicate_risk_groups(decision_pack, req_to_source)
    source_groups, source_clusters = _source_grounding_groups(residual, decision_pack, req_to_source)
    replacement_groups, replacement_clusters = _replacement_groups(decision_pack, draft_by_id)
    defer_groups, defer_clusters = _defer_groups(decision_pack, draft_by_id)
    clusters = [*duplicate_clusters, *source_clusters, *replacement_clusters, *defer_clusters]
    clusters = _dedupe_clusters(clusters)
    rows = [_row_from_cluster(index, cluster) for index, cluster in enumerate(clusters, start=1)]
    blocking_rows = [row for row in rows if row.is_blocking_for_revised_draft]
    current_needs_manual = int(
        ((decision_pack.get("revised_draft_readiness") or {}).get("needs_manual_decision_count"))
        or len(decision_pack.get("manual_decisions_required") or [])
    )
    estimated_reduction = max(0, len(raw_questions) - len(rows))
    readiness = ReadinessImpact(
        current_needs_manual_decision_count=current_needs_manual,
        current_ready_for_revised_draft_proposal=bool(
            (decision_pack.get("revised_draft_readiness") or {}).get("ready_for_revised_draft_proposal")
        ),
        matrix_rows_count=len(rows),
        blocking_rows_count=len(blocking_rows),
        estimated_reviewer_questions_reduction=estimated_reduction,
        remaining_blockers_after_matrix=[
            "Reviewer decisions are not supplied or validated in Stage 9D.6.",
            "Duplicate-risk and no-new-TC choices require explicit human answer.",
            "Matrix is an input to a future revised-draft stage, not readiness evidence by itself.",
        ],
        can_proceed_to_stage_9e_without_answers=False,
        why_not_ready=(
            "Stage 9D.6 compresses manual decisions into reviewer rows only; it does not answer them "
            "and does not authorize revised draft proposal generation."
        ),
    )
    summary = {
        "raw_manual_findings_count": len(raw_questions),
        "decision_clusters_count": len(clusters),
        "reviewer_rows_count": len(rows),
        "blocking_rows_count": len(blocking_rows),
        "estimated_reviewer_questions_reduction": estimated_reduction,
        "estimated_reviewer_questions_reduction_ratio": _ratio(estimated_reduction, len(raw_questions)),
        "duplicate_risk_groups_count": len(duplicate_groups),
        "source_grounding_groups_count": len(source_groups),
        "replacement_groups_count": len(replacement_groups),
        "defer_groups_count": len(defer_groups),
        "manual_decision_flow_status_after_matrix": _manual_flow_status(len(raw_questions), len(rows), rows),
        "canonical_write_allowed": False,
        "manual_review_required": True,
        "ready_for_revised_draft_proposal_after_matrix": False,
        "can_proceed_to_stage_9e_without_answers": False,
    }
    status: MatrixStatus = "pass-with-warnings" if rows or warnings else "pass"
    matrix_warnings = list(warnings)
    if rows:
        matrix_warnings.append("manual decisions are compressed but still require reviewer answers before Stage 9E.")
    return ManualDecisionMatrix(
        package_id=package_id,
        matrix_status=status,
        benchmark_name=benchmark_name,
        source_artifacts=source_artifacts,
        summary=summary,
        decision_clusters=clusters,
        reviewer_decision_rows=rows,
        compressed_manual_questions=raw_questions,
        duplicate_risk_decision_groups=duplicate_groups,
        source_grounding_decision_groups=source_groups,
        replacement_decision_groups=replacement_groups,
        defer_decision_groups=defer_groups,
        readiness_impact=readiness,
        expected_reviewer_outputs=_expected_reviewer_outputs(),
        safety_statement=_safety_statement(),
        canonical_write_allowed=False,
        manual_review_required=True,
        ready_for_revised_draft_proposal_after_matrix=False,
        input_paths=input_paths,
        warnings=_unique(matrix_warnings),
        blocking_reasons=[],
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def write_manual_decision_matrix(matrix: ManualDecisionMatrix, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{MATRIX_PREFIX}-{matrix.package_id}.json"
    markdown_path = out_dir / f"{MATRIX_PREFIX}-{matrix.package_id}.md"
    json_path.write_text(json.dumps(matrix.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_manual_decision_matrix_markdown(matrix), encoding="utf-8", newline="\n")
    return json_path, markdown_path


def load_manual_decision_matrix(path: Path) -> ManualDecisionMatrix:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manual decision matrix root must be a JSON object.")
    return ManualDecisionMatrix.from_dict(payload)


def render_manual_decision_matrix_markdown(matrix: ManualDecisionMatrix) -> str:
    summary = matrix.summary
    lines = [
        f"# Manual Decision Matrix {matrix.package_id}",
        "",
        "## Summary",
        "",
        f"- Matrix status: `{matrix.matrix_status}`",
        f"- Benchmark: `{matrix.benchmark_name}`",
        f"- Raw manual findings: `{summary.get('raw_manual_findings_count', 0)}`",
        f"- Decision clusters: `{len(matrix.decision_clusters)}`",
        f"- Reviewer decision rows: `{len(matrix.reviewer_decision_rows)}`",
        f"- Estimated reduction: `{summary.get('estimated_reviewer_questions_reduction', 0)}`",
        f"- Canonical write allowed: `{matrix.canonical_write_allowed}`",
        f"- Manual review required: `{matrix.manual_review_required}`",
        f"- Ready for revised draft after matrix: `{matrix.ready_for_revised_draft_proposal_after_matrix}`",
        "",
        "## Compression Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Raw manual findings | `{summary.get('raw_manual_findings_count', 0)}` |",
        f"| Decision clusters | `{len(matrix.decision_clusters)}` |",
        f"| Reviewer rows | `{len(matrix.reviewer_decision_rows)}` |",
        f"| Estimated reduction | `{summary.get('estimated_reviewer_questions_reduction', 0)}` |",
        f"| Duplicate-risk groups | `{len(matrix.duplicate_risk_decision_groups)}` |",
        f"| Source-grounding groups | `{len(matrix.source_grounding_decision_groups)}` |",
        f"| Replacement groups | `{len(matrix.replacement_decision_groups)}` |",
        f"| Defer/no-new-TC groups | `{len(matrix.defer_decision_groups)}` |",
        "",
        "## Reviewer Decision Matrix",
        "",
        "| Row ID | Cluster | Priority | Affected drafts | Affected requirements | Decision required | Options | Evidence summary | Blocking for Stage 9E? |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    clusters_by_id = {cluster.cluster_id: cluster for cluster in matrix.decision_clusters}
    for row in matrix.reviewer_decision_rows:
        cluster = clusters_by_id.get(row.cluster_id)
        priority = cluster.priority if cluster else "P2"
        options = "<br>".join(option.label for option in row.decision_options)
        lines.append(
            f"| `{row.row_id}` | `{row.cluster_id}` | `{priority}` | "
            f"{_md_join(row.affected_drafts)} | {_md_join(row.affected_requirements)} | "
            f"{_escape(row.decision_required)} | {_escape(options)} | {_escape(row.evidence_summary)} | "
            f"`{row.is_blocking_for_revised_draft}` |"
        )
    if not matrix.reviewer_decision_rows:
        lines.append("| none | none | none | none | none | none | none | none | false |")
    _groups_section(lines, "Duplicate-Risk Decision Groups", matrix.duplicate_risk_decision_groups)
    _groups_section(lines, "Source-Grounding Decision Groups", matrix.source_grounding_decision_groups)
    _groups_section(lines, "Replacement/Defer Groups", [*matrix.replacement_decision_groups, *matrix.defer_decision_groups])
    lines.extend(["", "## Required Reviewer Outputs", ""])
    _append_list(lines, matrix.expected_reviewer_outputs)
    lines.extend(
        [
            "",
            "## Readiness Impact",
            "",
            f"- Current needs manual decision count: `{matrix.readiness_impact.current_needs_manual_decision_count}`",
            f"- Matrix rows count: `{matrix.readiness_impact.matrix_rows_count}`",
            f"- Blocking rows count: `{matrix.readiness_impact.blocking_rows_count}`",
            f"- Can proceed to Stage 9E without answers: `{matrix.readiness_impact.can_proceed_to_stage_9e_without_answers}`",
            f"- Why not ready: {matrix.readiness_impact.why_not_ready}",
            "",
            "## Safety Statement",
            "",
            matrix.safety_statement,
            "",
            "## Warnings",
            "",
        ]
    )
    _append_list(lines, matrix.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, matrix.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _duplicate_risk_groups(
    decision_pack: dict[str, Any],
    req_to_source: dict[str, str],
) -> tuple[list[dict[str, Any]], list[ManualDecisionCluster]]:
    groups: list[dict[str, Any]] = []
    clusters: list[ManualDecisionCluster] = []
    for index, item in enumerate(decision_pack.get("duplicate_risk_clusters") or [], start=1):
        reqs = _unique(item.get("candidate_req_uids") or [])
        similar_refs = _similar_refs(item.get("similar_tc_ids") or [], item.get("similar_file_paths") or [])
        source_ids = _unique(req_to_source.get(req) for req in reqs)
        group_id = str(item.get("cluster_id") or f"DUP-{index:06d}")
        evidence = _unique(
            [
                f"risk={item.get('risk')}",
                f"cluster_action={item.get('cluster_action')}",
                str(item.get("rationale") or ""),
                *[f"similar_tc={ref}" for ref in similar_refs[:10]],
            ]
        )
        group = {
            "group_id": group_id,
            "risk": item.get("risk"),
            "affected_draft_ids": _unique(item.get("draft_ids") or []),
            "affected_req_uids": reqs,
            "source_req_ids": source_ids,
            "similar_existing_tc_refs": similar_refs,
            "recommended_review": "Decide whether candidate behavior is already covered, should extend an existing TC, needs a separate new TC, or should be deferred.",
        }
        groups.append(group)
        clusters.append(
            ManualDecisionCluster(
                cluster_id=group_id,
                cluster_type="duplicate_risk",
                priority="P0" if item.get("risk") == "high" else "P1",
                affected_draft_ids=group["affected_draft_ids"],
                affected_proposed_tc_ids=[],
                affected_req_uids=reqs,
                source_req_ids=source_ids,
                similar_existing_tc_refs=similar_refs,
                evidence=evidence,
                root_cause="Potential overlap with existing test cases blocks automatic create-new decision.",
                reviewer_question="Is this candidate already covered, an extension of an existing TC, a separate new TC, or deferred?",
                allowed_decisions=_options_for("duplicate_risk"),
                recommended_default=None,
                blocked_until_answered=True,
                safety_notes=[
                    "Existing TC is coverage evidence only, not a source of business rules.",
                    "No canonical TC is created or edited by this matrix.",
                ],
            )
        )
    return groups, clusters


def _source_grounding_groups(
    residual: dict[str, Any],
    decision_pack: dict[str, Any],
    req_to_source: dict[str, str],
) -> tuple[list[dict[str, Any]], list[ManualDecisionCluster]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for item in residual.get("requirement_gap_analyses") or []:
        classification = str(item.get("gap_classification") or "unknown")
        if classification == "duplicate_risk_prevents_decision":
            continue
        missing = item.get("missing_facts") or ["manual business decision"]
        key = (classification, _missing_fact_bucket(missing))
        group = grouped.setdefault(
            key,
            {
                "classification": classification,
                "missing_fact_bucket": key[1],
                "affected_req_uids": [],
                "source_req_ids": [],
                "evidence": [],
                "available_context": Counter(),
            },
        )
        req_uid = str(item.get("req_uid") or "")
        if req_uid:
            group["affected_req_uids"].append(req_uid)
        source_req_id = item.get("source_req_id") or req_to_source.get(req_uid)
        if source_req_id:
            group["source_req_ids"].append(str(source_req_id))
        group["evidence"].extend(_unique([*(item.get("available_source_fragments") or [])[:3], *(item.get("registry_evidence") or [])[:3]]))
        if item.get("has_object"):
            group["available_context"]["object"] += 1
        if item.get("has_condition"):
            group["available_context"]["condition"] += 1
        if item.get("has_user_action"):
            group["available_context"]["user_action"] += 1
        if item.get("has_expected_behavior"):
            group["available_context"]["expected_behavior"] += 1

    for resolution in decision_pack.get("source_grounding_resolutions") or []:
        missing = resolution.get("missing_source_facts") or []
        if not missing:
            continue
        key = ("source_grounding_resolution", _missing_fact_bucket(missing))
        group = grouped.setdefault(
            key,
            {
                "classification": key[0],
                "missing_fact_bucket": key[1],
                "affected_req_uids": [],
                "source_req_ids": [],
                "affected_draft_ids": [],
                "evidence": [],
                "available_context": Counter(),
            },
        )
        group.setdefault("affected_draft_ids", []).append(str(resolution.get("draft_id") or ""))
        req_uid = str(resolution.get("req_uid") or "")
        if req_uid:
            group["affected_req_uids"].append(req_uid)
        if resolution.get("source_req_id"):
            group["source_req_ids"].append(str(resolution.get("source_req_id")))
        group["evidence"].extend((resolution.get("usable_source_facts") or [])[:5])

    groups: list[dict[str, Any]] = []
    clusters: list[ManualDecisionCluster] = []
    for index, ((classification, bucket), group) in enumerate(sorted(grouped.items()), start=1):
        reqs = _unique(group.get("affected_req_uids") or [])
        drafts = _unique(group.get("affected_draft_ids") or [])
        source_ids = _unique(group.get("source_req_ids") or [])
        evidence = _unique(group.get("evidence") or [])[:12]
        context_counter = group.get("available_context") or Counter()
        group_id = f"SRC-{index:06d}"
        group_payload = {
            "group_id": group_id,
            "classification": classification,
            "missing_fact_bucket": bucket,
            "affected_draft_ids": drafts,
            "affected_req_uids": reqs,
            "source_req_ids": source_ids,
            "available_context_counts": dict(context_counter),
            "evidence_sample": evidence[:5],
            "recommended_review": "Confirm source-backed action/oracle/object or request clarification; do not infer from existing TC.",
        }
        groups.append(group_payload)
        clusters.append(
            ManualDecisionCluster(
                cluster_id=group_id,
                cluster_type="source_grounding",
                priority="P1",
                affected_draft_ids=drafts,
                affected_proposed_tc_ids=[],
                affected_req_uids=reqs,
                source_req_ids=source_ids,
                similar_existing_tc_refs=[],
                evidence=evidence,
                root_cause=f"Residual source-grounding issue: {classification}; missing {bucket}.",
                reviewer_question="Which source-backed fact or clarification resolves this missing action/oracle/object/condition group?",
                allowed_decisions=_options_for("source_grounding"),
                recommended_default=None,
                blocked_until_answered=True,
                safety_notes=[
                    "Table/anchor context can support a choice, but the matrix does not choose business behavior.",
                    "If source evidence is still ambiguous, choose clarification or defer.",
                ],
            )
        )
    return groups, clusters


def _replacement_groups(
    decision_pack: dict[str, Any],
    draft_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[ManualDecisionCluster]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in decision_pack.get("replacement_strategies") or []:
        mode = str(item.get("replacement_mode") or "unknown")
        grouped[mode].append(item)
    groups: list[dict[str, Any]] = []
    clusters: list[ManualDecisionCluster] = []
    for index, (mode, items) in enumerate(sorted(grouped.items()), start=1):
        drafts = _unique(item.get("draft_id") for item in items)
        proposed = _unique(item.get("proposed_tc_id") for item in items)
        reqs = _unique(req for item in items for req in item.get("candidate_req_uids") or [])
        evidence = _unique(
            value
            for item in items
            for value in [
                item.get("reason_for_replacement"),
                *(item.get("required_source_facts") or [])[:3],
                *(item.get("replacement_guidance") or [])[:3],
            ]
        )
        group_id = f"REP-{index:06d}"
        groups.append(
            {
                "group_id": group_id,
                "replacement_mode": mode,
                "affected_draft_ids": drafts,
                "affected_proposed_tc_ids": proposed,
                "affected_req_uids": reqs,
                "recommended_review": "Choose rewrite from source, split, extend existing TC, defer, or no-new-TC.",
            }
        )
        clusters.append(
            ManualDecisionCluster(
                cluster_id=group_id,
                cluster_type="replacement_strategy",
                priority="P2",
                affected_draft_ids=drafts,
                affected_proposed_tc_ids=proposed,
                affected_req_uids=reqs,
                source_req_ids=_source_ids_for_drafts(drafts, draft_by_id),
                similar_existing_tc_refs=[],
                evidence=evidence[:12],
                root_cause=f"Rejected or weak draft requires replacement strategy `{mode}`.",
                reviewer_question="Should the rejected draft be rewritten from source, split, routed to existing TC extension, deferred, or closed as no-new-TC?",
                allowed_decisions=_options_for("replacement_strategy"),
                recommended_default=None,
                blocked_until_answered=True,
                safety_notes=["Do not patch rejected draft content in place; future revision must be source-backed."],
            )
        )
    return groups, clusters


def _defer_groups(
    decision_pack: dict[str, Any],
    draft_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[ManualDecisionCluster]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in decision_pack.get("draft_decisions") or []:
        decision = str(item.get("decision") or "")
        if decision in {"defer", "maybe_extend_existing_tc", "needs_manual_decision"}:
            grouped[decision].append(item)
    groups: list[dict[str, Any]] = []
    clusters: list[ManualDecisionCluster] = []
    for index, (decision, items) in enumerate(sorted(grouped.items()), start=1):
        drafts = _unique(item.get("draft_id") for item in items)
        proposed = _unique(item.get("proposed_tc_id") for item in items)
        reqs = _unique(req for item in items for req in item.get("candidate_req_uids") or [])
        source_ids = _unique(source for item in items for source in item.get("source_req_ids") or [])
        evidence = _unique(item.get("decision_reason") for item in items)[:12]
        group_id = f"DEF-{index:06d}"
        groups.append(
            {
                "group_id": group_id,
                "decision": decision,
                "affected_draft_ids": drafts,
                "affected_proposed_tc_ids": proposed,
                "affected_req_uids": reqs,
                "source_req_ids": source_ids,
                "recommended_review": "Choose defer, no-new-TC with rationale, request clarification, or keep manual-only.",
            }
        )
        clusters.append(
            ManualDecisionCluster(
                cluster_id=group_id,
                cluster_type="defer_or_no_new_tc",
                priority="P2",
                affected_draft_ids=drafts,
                affected_proposed_tc_ids=proposed,
                affected_req_uids=reqs,
                source_req_ids=source_ids or _source_ids_for_drafts(drafts, draft_by_id),
                similar_existing_tc_refs=[],
                evidence=evidence,
                root_cause=f"Draft decision remains `{decision}` and needs explicit reviewer disposition.",
                reviewer_question="Should this candidate be deferred, closed as no-new-TC, clarified, split, or kept manual-only?",
                allowed_decisions=_options_for("defer_or_no_new_tc"),
                recommended_default=None,
                blocked_until_answered=True,
                safety_notes=["No defer/no-new-TC choice modifies canonical files in this stage."],
            )
        )
    return groups, clusters


def _row_from_cluster(index: int, cluster: ManualDecisionCluster) -> ReviewerDecisionRow:
    risk = "high" if cluster.priority in {"P0", "P1"} else "medium"
    return ReviewerDecisionRow(
        row_id=f"MDR-{index:06d}",
        cluster_id=cluster.cluster_id,
        decision_required=cluster.reviewer_question,
        reviewer_prompt=cluster.reviewer_question,
        decision_options=cluster.allowed_decisions,
        option_effects=[_option_effect(option) for option in cluster.allowed_decisions],
        affected_drafts=cluster.affected_draft_ids,
        affected_requirements=cluster.affected_req_uids,
        evidence_summary="; ".join(cluster.evidence[:4])[:700] if cluster.evidence else cluster.root_cause,
        source_evidence_refs=cluster.source_req_ids or cluster.affected_req_uids,
        existing_tc_evidence_refs=cluster.similar_existing_tc_refs,
        risk_level=risk,
        required_reviewer_role=_reviewer_role(cluster.cluster_type),
        is_blocking_for_revised_draft=cluster.blocked_until_answered,
    )


def _options_for(cluster_type: ClusterType) -> list[DecisionOption]:
    if cluster_type == "duplicate_risk":
        return [
            _option("OPT-SEPARATE", "Create separate new TC", "Reviewer confirms source-backed behavior is distinct.", "revise_draft", True, True),
            _option("OPT-EXTEND", "Extend existing TC", "Future stage may propose extension to listed TC, still under review.", "extend_existing_tc", True, True),
            _option("OPT-NO-NEW", "No new TC - existing coverage sufficient", "Close candidate with rationale; no canonical write here.", "no_new_tc_with_rationale", True, True),
            _option("OPT-DEFER", "Defer", "Keep candidate out of Stage 9E until evidence improves.", "defer", False, False),
        ]
    if cluster_type == "source_grounding":
        return [
            _option("OPT-CLARIFY", "Request source clarification", "Ask analyst/product owner for missing source fact.", "request_source_clarification", True, False),
            _option("OPT-REVISE", "Revise from provided source fact", "Use only reviewer-supplied source-backed fact in future Stage 9E.", "revise_draft", True, False),
            _option("OPT-SPLIT", "Split candidate", "Separate mixed requirement into smaller source-backed drafts.", "split_candidate", True, False),
            _option("OPT-DEFER", "Defer", "Do not draft until source evidence is sufficient.", "defer", False, False),
        ]
    if cluster_type == "replacement_strategy":
        return [
            _option("OPT-REPLACE", "Rewrite from source", "Discard weak draft text and build future proposal from source facts.", "replace_draft", True, False),
            _option("OPT-SPLIT", "Split candidate", "Replace one weak draft with multiple smaller draft candidates later.", "split_candidate", True, False),
            _option("OPT-EXTEND", "Extend existing TC", "Route behavior to an existing TC extension proposal later.", "extend_existing_tc", True, True),
            _option("OPT-DEFER", "Defer", "Keep rejected draft out of revised proposal.", "defer", False, False),
        ]
    return [
        _option("OPT-NO-NEW", "No new TC with rationale", "Close candidate without canonical creation.", "no_new_tc_with_rationale", False, False),
        _option("OPT-CLARIFY", "Request source clarification", "Ask for the missing source or business decision.", "request_source_clarification", True, False),
        _option("OPT-MANUAL", "Keep manual-only", "Leave item outside automated revised drafting.", "keep_manual_only", False, False),
        _option("OPT-DEFER", "Defer", "Postpone until a later package or decision.", "defer", False, False),
    ]


def _option(
    option_id: str,
    label: str,
    meaning: str,
    action: AllowedNextAction,
    requires_source: bool,
    requires_existing_tc: bool,
) -> DecisionOption:
    return DecisionOption(
        option_id=option_id,
        label=label,
        meaning=meaning,
        allowed_next_action=action,
        requires_source_evidence=requires_source,
        requires_existing_tc_review=requires_existing_tc,
        creates_or_edits_canonical_tc=False,
        notes=[
            "This option records reviewer intent only.",
            "It does not create or edit canonical test cases in Stage 9D.6.",
        ],
    )


def _raw_manual_questions(
    decision_pack: dict[str, Any],
    residual: dict[str, Any],
    review: dict[str, Any] | None,
    revision_plan: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, values in [
        ("decision_pack.manual_decisions_required", decision_pack.get("manual_decisions_required") or []),
        ("residual.manual_decision_findings", residual.get("manual_decision_findings") or []),
        ("residual.duplicate_risk_blockers", residual.get("duplicate_risk_blockers") or []),
    ]:
        for index, item in enumerate(values, start=1):
            rows.append({"source": source, "id": str(item.get("id") or item.get("req_uid") or index), "question": str(item.get("question") or item.get("recommended_action") or item.get("classification") or item)})
    for draft_review in (review or {}).get("draft_reviews") or []:
        for index, value in enumerate([*(draft_review.get("issues") or []), *(draft_review.get("required_fixes") or [])], start=1):
            rows.append({"source": "draft_review", "id": f"{draft_review.get('draft_id')}-{index}", "question": str(value)})
    for item in (revision_plan or {}).get("revision_items") or []:
        for index, value in enumerate(item.get("manual_review_notes") or item.get("warnings") or [], start=1):
            rows.append({"source": "draft_revision_plan", "id": f"{item.get('draft_id')}-{index}", "question": str(value)})
    return _dedupe_dicts(rows)


def _req_to_source_id(context_bundle: dict[str, Any] | None, residual: dict[str, Any] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for candidate in (context_bundle or {}).get("candidate_requirements") or []:
        req_uid = candidate.get("req_uid")
        source_req_id = candidate.get("source_req_id")
        if req_uid and source_req_id:
            result[str(req_uid)] = str(source_req_id)
    for item in (residual or {}).get("requirement_gap_analyses") or []:
        req_uid = item.get("req_uid")
        source_req_id = item.get("source_req_id")
        if req_uid and source_req_id:
            result[str(req_uid)] = str(source_req_id)
    return result


def _source_ids_for_drafts(draft_ids: list[str], draft_by_id: dict[str, dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for draft_id in draft_ids:
        item = draft_by_id.get(draft_id) or {}
        values.extend(item.get("source_req_ids") or [])
    return _unique(values)


def _similar_refs(tc_ids: list[Any], file_paths: list[Any]) -> list[str]:
    refs: list[str] = []
    files = [str(value) for value in file_paths if value]
    for tc_id in tc_ids:
        if files:
            for file_path in files:
                refs.append(f"{tc_id} ({file_path})")
        else:
            refs.append(str(tc_id))
    return _unique(refs)


def _missing_fact_bucket(missing: list[Any]) -> str:
    text = " ".join(str(value).casefold() for value in missing)
    labels: list[str] = []
    if any(marker in text for marker in ["action", "user", "navigation", "step"]):
        labels.append("user_action")
    if any(marker in text for marker in ["expected", "observable", "oracle", "result"]):
        labels.append("observable_expected_behavior")
    if any(marker in text for marker in ["object", "field", "screen"]):
        labels.append("object_screen_field")
    if "condition" in text:
        labels.append("condition")
    return "+".join(labels or ["manual_business_decision"])


def _manual_flow_status(raw_count: int, row_count: int, rows: list[ReviewerDecisionRow]) -> str:
    if raw_count == 0 and row_count == 0:
        return "works"
    if row_count and row_count < raw_count and all(row.decision_options for row in rows):
        return "partial"
    return "gap"


def _option_effect(option: DecisionOption) -> str:
    return f"{option.label}: enables `{option.allowed_next_action}` in a later reviewed stage; canonical writes remain disabled here."


def _reviewer_role(cluster_type: ClusterType) -> str:
    if cluster_type == "source_grounding":
        return "analyst"
    if cluster_type == "duplicate_risk":
        return "qa"
    if cluster_type == "replacement_strategy":
        return "mixed"
    return "product_owner"


def _expected_reviewer_outputs() -> list[str]:
    return [
        "One selected option per reviewer decision row.",
        "Source citation or clarification text for options that require source evidence.",
        "Explicit rationale for no-new-TC, defer, or extend-existing-TC choices.",
        "Confirmation that existing TC text was used only as coverage evidence.",
    ]


def _safety_statement() -> str:
    return (
        "This matrix is a read-only reviewer artifact. It does not create revised drafts, create canonical test cases, "
        "edit existing test cases, run apply, or authorize Stage 9E readiness without validated reviewer answers."
    )


def _empty_matrix(
    *,
    package_id: str,
    matrix_status: MatrixStatus,
    benchmark_name: str,
    input_paths: dict[str, str | None],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
) -> ManualDecisionMatrix:
    readiness = ReadinessImpact(
        current_needs_manual_decision_count=0,
        current_ready_for_revised_draft_proposal=False,
        matrix_rows_count=0,
        blocking_rows_count=0,
        estimated_reviewer_questions_reduction=0,
        remaining_blockers_after_matrix=blocking_reasons,
        can_proceed_to_stage_9e_without_answers=False,
        why_not_ready="Matrix is blocked and reviewer answers are not available.",
    )
    return ManualDecisionMatrix(
        package_id=package_id,
        matrix_status=matrix_status,
        benchmark_name=benchmark_name,
        source_artifacts={},
        summary={
            "raw_manual_findings_count": 0,
            "decision_clusters_count": 0,
            "reviewer_rows_count": 0,
            "estimated_reviewer_questions_reduction": 0,
            "can_proceed_to_stage_9e_without_answers": False,
        },
        decision_clusters=[],
        reviewer_decision_rows=[],
        compressed_manual_questions=[],
        duplicate_risk_decision_groups=[],
        source_grounding_decision_groups=[],
        replacement_decision_groups=[],
        defer_decision_groups=[],
        readiness_impact=readiness,
        expected_reviewer_outputs=_expected_reviewer_outputs(),
        safety_statement=_safety_statement(),
        canonical_write_allowed=False,
        manual_review_required=True,
        ready_for_revised_draft_proposal_after_matrix=False,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _groups_section(lines: list[str], title: str, groups: list[dict[str, Any]]) -> None:
    lines.extend(["", f"## {title}", ""])
    if not groups:
        lines.append("- none")
        return
    for group in groups:
        lines.append(f"- `{group.get('group_id')}`: {group.get('recommended_review') or group.get('classification') or group.get('decision')}")


def _md_join(values: list[str]) -> str:
    return _escape(", ".join(values[:8]) if values else "none")


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _index_by_key(items: Any, key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items or []:
        if isinstance(item, dict) and item.get(key):
            result[str(item[key])] = item
    return result


def _input_paths(**paths: Path | None) -> dict[str, str | None]:
    return {key: (str(value) if value is not None else None) for key, value in paths.items()}


def _load_json_object(
    path: Path | None,
    label: str,
    warnings: list[str],
    blocking_reasons: list[str] | None = None,
    *,
    required: bool = False,
) -> dict[str, Any] | None:
    if path is None:
        return None
    if not Path(path).exists():
        message = f"{label} is missing: {path}"
        if required and blocking_reasons is not None:
            blocking_reasons.append(message)
        else:
            warnings.append(message)
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - matrix reports parse failures.
        message = f"{label} cannot be parsed: {path}: {exc}"
        if required and blocking_reasons is not None:
            blocking_reasons.append(message)
        else:
            warnings.append(message)
        return None
    if not isinstance(payload, dict):
        message = f"{label} root is not a JSON object: {path}"
        if required and blocking_reasons is not None:
            blocking_reasons.append(message)
        else:
            warnings.append(message)
        return None
    return payload


def _registry_count(path: Path, warnings: list[str]) -> int | None:
    if not Path(path).exists():
        warnings.append(f"final registry is missing: {path}")
        return None
    count = 0
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                count += 1
    except Exception as exc:  # noqa: BLE001 - diagnostic report should continue.
        warnings.append(f"final registry cannot be read: {path}: {exc}")
        return None
    return count


def _dedupe_clusters(clusters: list[ManualDecisionCluster]) -> list[ManualDecisionCluster]:
    seen: set[tuple[str, str]] = set()
    result: list[ManualDecisionCluster] = []
    for cluster in clusters:
        key = (cluster.cluster_id, cluster.cluster_type)
        if key not in seen:
            seen.add(key)
            result.append(cluster)
    return result


def _dedupe_dicts(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for value in values:
        key = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


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
