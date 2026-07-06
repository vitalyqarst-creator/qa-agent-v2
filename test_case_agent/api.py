from __future__ import annotations

from pathlib import Path

from test_case_agent.chunking import split_section
from test_case_agent.document_loader import load_sections as load_sections_from_source
from test_case_agent.models import Section, SectionChunk
from test_case_agent.ooxml_loader import (
    OoxmlCoverageAudit,
    OoxmlSource,
    OOXMLTableCellContext,
    SourceNode,
    extract_ooxml_source_nodes,
    inspect_ooxml_coverage,
    load_ooxml_source,
    table_context_from_anchor,
)
from test_case_agent.source_manifest import (
    SourceFileEntry,
    SourceManifest,
    build_source_manifest,
    compute_file_sha256,
    load_source_manifest,
    write_source_manifest,
)
from test_case_agent.requirements_registry import (
    RequirementRegistry,
    RequirementRegistryEntry,
    SourceAnchor,
    build_requirements_registry,
    compute_requirement_text_hash,
    load_requirements_registry,
    load_requirements_registry_jsonl,
    make_entry_uid,
    make_req_uid,
    write_requirements_registry,
)
from test_case_agent.requirements_diff import (
    RequirementsDiff,
    RequirementsDiffEntry,
    build_requirements_diff,
    compute_text_similarity,
    load_requirements_diff,
    match_requirement_entries,
    write_requirements_diff,
)
from test_case_agent.impact_analysis import (
    ImpactEntry,
    ImpactReport,
    TestCaseLink,
    build_impact_report,
    link_diff_to_test_cases,
    load_impact_report,
    parse_test_cases,
    write_impact_report,
)
from test_case_agent.test_case_update_plan import (
    TestCaseUpdatePlan,
    UpdatePlanItem,
    build_test_case_update_plan,
    load_test_case_update_plan,
    write_test_case_update_plan,
)
from test_case_agent.test_case_update_apply import (
    ApplyReport,
    ApplyResultItem,
    apply_test_case_update_plan,
    load_test_case_update_apply_report,
    write_test_case_update_apply_report,
)
from test_case_agent.manual_update_packages import (
    ManualUpdatePackage,
    ManualUpdatePackagesReport,
    build_manual_update_packages,
    load_manual_update_packages,
    write_manual_update_packages,
)
from test_case_agent.writer_package_tasks import (
    WriterPackageTask,
    WriterPackageTasksReport,
    build_writer_package_tasks,
    load_writer_package_tasks,
    write_writer_package_tasks,
)
from test_case_agent.writer_dry_run_proposals import (
    WriterDryRunProposal,
    build_writer_dry_run_proposal,
    load_writer_dry_run_proposal,
    write_writer_dry_run_proposal,
)
from test_case_agent.traceability_mismatch_diagnostics import (
    TraceabilityMismatch,
    TraceabilityMismatchDiagnosticsReport,
    build_traceability_mismatch_diagnostics,
    load_traceability_mismatch_diagnostics,
    write_traceability_mismatch_diagnostics,
)
from test_case_agent.traceability_repair_strategy import (
    TraceabilityRepairItem,
    TraceabilityRepairStrategyReport,
    build_traceability_repair_strategy,
    load_traceability_repair_strategy,
    write_traceability_repair_strategy,
)
from test_case_agent.traceability_backfill_proposals import (
    TraceabilityBackfillChange,
    TraceabilityBackfillProposal,
    build_traceability_backfill_proposal,
    load_traceability_backfill_proposal,
    write_traceability_backfill_proposal,
)
from test_case_agent.traceability_backfill_review import (
    TraceabilityBackfillReviewCheck,
    TraceabilityBackfillReviewReport,
    build_traceability_backfill_review,
    load_traceability_backfill_review,
    write_traceability_backfill_review,
)
from test_case_agent.traceability_backfill_apply import (
    TraceabilityBackfillApplyChange,
    TraceabilityBackfillApplyReport,
    apply_traceability_backfill_proposal,
    load_traceability_backfill_apply_report,
    write_traceability_backfill_apply_report,
)
from test_case_agent.writer_proposal_review import (
    WriterProposalReviewCheck,
    WriterProposalReviewReport,
    build_writer_proposal_review,
    load_writer_proposal_review,
    write_writer_proposal_review,
)
from test_case_agent.writer_traceability_update_apply import (
    WriterTraceabilityUpdateApplyChange,
    WriterTraceabilityUpdateApplyReport,
    apply_writer_traceability_update_proposal,
    load_writer_traceability_update_apply_report,
    write_writer_traceability_update_apply_report,
)
from test_case_agent.writer_traceability_post_apply_validation import (
    WriterTraceabilityPostApplyValidationCheck,
    WriterTraceabilityPostApplyValidationReport,
    build_writer_traceability_post_apply_validation,
    load_writer_traceability_post_apply_validation,
    write_writer_traceability_post_apply_validation,
)
from test_case_agent.completed_package_regression import (
    CompletedPackageRegressionCheck,
    CompletedPackageRegressionReport,
    build_completed_package_regression,
    load_completed_package_regression,
    write_completed_package_regression,
)
from test_case_agent.create_new_tc_context_bundle import (
    CandidateGroup,
    CandidateRequirement,
    CreateNewTcContextBundle,
    EnrichedSourceFacts,
    ExistingTcSimilarity,
    RecommendedDraftTarget,
    SourceAnchorContext,
    TableSourceContext,
    build_create_new_tc_context_bundle,
    load_create_new_tc_context_bundle,
    write_create_new_tc_context_bundle,
)
from test_case_agent.new_tc_draft_proposals import (
    DeferredGroup,
    DraftTestCaseCandidate,
    DuplicateRiskDecision,
    NewTcDraftProposal,
    SourceGroundingProfile,
    build_new_tc_draft_proposal,
    load_new_tc_draft_proposal,
    write_new_tc_draft_proposal,
)
from test_case_agent.new_tc_draft_review import (
    DraftTestCaseReview,
    NewTcDraftReviewCheck,
    NewTcDraftReviewReport,
    build_new_tc_draft_review,
    load_new_tc_draft_review,
    write_new_tc_draft_review,
)
from test_case_agent.new_tc_draft_revision_plan import (
    DraftRevisionItem,
    DuplicateRiskAction,
    NewTcDraftRevisionPlan,
    SourceGroundingAction,
    build_new_tc_draft_revision_plan,
    load_new_tc_draft_revision_plan,
    write_new_tc_draft_revision_plan,
)
from test_case_agent.new_tc_revision_decision_pack import (
    AgentCapabilityFinding,
    DraftDecision,
    DuplicateRiskCluster,
    ExistingTcComparison,
    NewTcRevisionDecisionPack,
    ReplacementStrategy,
    RevisedDraftReadiness,
    SourceGroundingResolution,
    build_new_tc_revision_decision_pack,
    load_new_tc_revision_decision_pack,
    write_new_tc_revision_decision_pack,
)
from test_case_agent.agent_capability_improvement_plan import (
    AgentCapabilityImprovementPlan,
    CapabilityFindingSummary,
    CodeUpdatePlan,
    ImprovementItem,
    InstructionUpdatePlan,
    SafetyPreservationPlan,
    TestUpdatePlan,
    build_agent_capability_improvement_plan,
    load_agent_capability_improvement_plan,
    write_agent_capability_improvement_plan,
)
from test_case_agent.residual_source_grounding_gap_analysis import (
    DraftGroundingGapAnalysis,
    RecommendedAgentImprovement,
    RequirementGroundingGapAnalysis,
    ResidualSourceGroundingGapAnalysis,
    build_residual_source_grounding_gap_analysis,
    load_residual_source_grounding_gap_analysis,
    write_residual_source_grounding_gap_analysis,
)
from test_case_agent.manual_decision_matrix import (
    DecisionOption,
    ManualDecisionCluster,
    ManualDecisionMatrix,
    ReadinessImpact,
    ReviewerDecisionRow,
    build_manual_decision_matrix,
    load_manual_decision_matrix,
    write_manual_decision_matrix,
)
from test_case_agent.manual_decision_answer_validation import (
    ManualDecisionAnswerTemplate,
    ManualDecisionAnswerValidation,
    ReadinessAfterAnswers,
    ReviewerAnswerPlaceholder,
    ReviewerAnswerTemplateRow,
    Stage9EGate,
    ValidatedReviewerAnswer,
    build_manual_decision_answer_template,
    load_manual_decision_answer_template,
    load_manual_decision_answer_validation,
    validate_manual_decision_answers,
    write_manual_decision_answer_template,
    write_manual_decision_answer_validation,
)
from test_case_agent.manual_decision_answer_pack import (
    ManualDecisionAnswerPack,
    ManualDecisionAnswerPackImportReport,
    ReviewerAnswerPackRow,
    build_manual_decision_answer_pack,
    import_manual_decision_answer_pack,
    load_manual_decision_answer_pack,
    load_manual_decision_answer_pack_import_report,
    write_manual_decision_answer_pack,
    write_manual_decision_answer_pack_import_report,
)
from test_case_agent.source_quality import SourceQualityIssue, analyze_sections

DEFAULT_MAX_CHARS = 12000


class InvalidSourceError(FileNotFoundError):
    """Raised when the requirements document path is missing."""


class NoMatchingSectionsError(ValueError):
    """Raised when section filters exclude the whole document."""


def _ensure_source_exists(source: Path) -> Path:
    source = Path(source)
    if not source.exists():
        raise InvalidSourceError(f"File does not exist: {source}")
    return source


def load_sections(source: Path) -> list[Section]:
    source = _ensure_source_exists(source)
    return load_sections_from_source(source)


def resolve_sections(
    source: Path,
    section_prefix: str | None = None,
    max_sections: int | None = None,
) -> list[Section]:
    sections = load_sections(source)
    filtered = [section for section in sections if section.section_id != "preface"]

    if section_prefix:
        section_prefix_lower = section_prefix.lower()
        filtered = [
            section
            for section in filtered
            if section.section_id.lower().startswith(section_prefix_lower)
            or section_prefix_lower in section.title.lower()
            or section_prefix_lower in section.full_title.lower()
        ]

    if max_sections is not None:
        filtered = filtered[:max_sections]

    return filtered


def preview_chunks(
    source: Path,
    section_prefix: str | None = None,
    max_sections: int | None = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[SectionChunk]:
    sections = resolve_sections(source, section_prefix=section_prefix, max_sections=max_sections)
    if not sections:
        raise NoMatchingSectionsError("No sections matched the selected filters.")

    chunks: list[SectionChunk] = []
    for section in sections:
        chunks.extend(split_section(section, max_chars=max_chars))
    return chunks


def inspect_source_quality(
    source: Path,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[SourceQualityIssue]:
    sections = load_sections(source)
    return analyze_sections(sections, max_chars=max_chars)


__all__ = [
    "DEFAULT_MAX_CHARS",
    "ApplyReport",
    "ApplyResultItem",
    "AgentCapabilityFinding",
    "AgentCapabilityImprovementPlan",
    "CapabilityFindingSummary",
    "CodeUpdatePlan",
    "InvalidSourceError",
    "ImpactEntry",
    "ImpactReport",
    "ImprovementItem",
    "InstructionUpdatePlan",
    "ManualUpdatePackage",
    "ManualUpdatePackagesReport",
    "DecisionOption",
    "ManualDecisionCluster",
    "ManualDecisionMatrix",
    "ManualDecisionAnswerTemplate",
    "ManualDecisionAnswerValidation",
    "ManualDecisionAnswerPack",
    "ManualDecisionAnswerPackImportReport",
    "NoMatchingSectionsError",
    "OoxmlCoverageAudit",
    "OoxmlSource",
    "OOXMLTableCellContext",
    "RequirementRegistry",
    "RequirementRegistryEntry",
    "RequirementsDiff",
    "RequirementsDiffEntry",
    "SafetyPreservationPlan",
    "Section",
    "SectionChunk",
    "SourceAnchor",
    "SourceFileEntry",
    "SourceManifest",
    "SourceNode",
    "SourceQualityIssue",
    "TestCaseLink",
    "TestCaseUpdatePlan",
    "TestUpdatePlan",
    "TraceabilityMismatch",
    "TraceabilityMismatchDiagnosticsReport",
    "TraceabilityBackfillChange",
    "TraceabilityBackfillProposal",
    "TraceabilityBackfillApplyChange",
    "TraceabilityBackfillApplyReport",
    "TraceabilityBackfillReviewCheck",
    "TraceabilityBackfillReviewReport",
    "TraceabilityRepairItem",
    "TraceabilityRepairStrategyReport",
    "WriterProposalReviewCheck",
    "WriterProposalReviewReport",
    "WriterTraceabilityUpdateApplyChange",
    "WriterTraceabilityUpdateApplyReport",
    "WriterTraceabilityPostApplyValidationCheck",
    "WriterTraceabilityPostApplyValidationReport",
    "CompletedPackageRegressionCheck",
    "CompletedPackageRegressionReport",
    "CandidateGroup",
    "CandidateRequirement",
    "CreateNewTcContextBundle",
    "EnrichedSourceFacts",
    "DeferredGroup",
    "DraftTestCaseReview",
    "DraftTestCaseCandidate",
    "DraftRevisionItem",
    "DraftDecision",
    "DuplicateRiskDecision",
    "DuplicateRiskAction",
    "DuplicateRiskCluster",
    "ExistingTcComparison",
    "ExistingTcSimilarity",
    "NewTcDraftReviewCheck",
    "NewTcDraftReviewReport",
    "NewTcDraftRevisionPlan",
    "NewTcRevisionDecisionPack",
    "NewTcDraftProposal",
    "ReplacementStrategy",
    "RecommendedDraftTarget",
    "RecommendedAgentImprovement",
    "ReadinessImpact",
    "ReadinessAfterAnswers",
    "RevisedDraftReadiness",
    "RequirementGroundingGapAnalysis",
    "ResidualSourceGroundingGapAnalysis",
    "ReviewerDecisionRow",
    "ReviewerAnswerPlaceholder",
    "ReviewerAnswerTemplateRow",
    "ReviewerAnswerPackRow",
    "SourceAnchorContext",
    "SourceGroundingResolution",
    "SourceGroundingProfile",
    "SourceGroundingAction",
    "TableSourceContext",
    "DraftGroundingGapAnalysis",
    "WriterPackageTask",
    "WriterPackageTasksReport",
    "WriterDryRunProposal",
    "UpdatePlanItem",
    "Stage9EGate",
    "ValidatedReviewerAnswer",
    "extract_ooxml_source_nodes",
    "inspect_ooxml_coverage",
    "inspect_source_quality",
    "build_source_manifest",
    "build_agent_capability_improvement_plan",
    "build_requirements_registry",
    "build_requirements_diff",
    "build_impact_report",
    "build_test_case_update_plan",
    "build_traceability_mismatch_diagnostics",
    "build_traceability_backfill_proposal",
    "build_traceability_backfill_review",
    "build_traceability_repair_strategy",
    "build_manual_update_packages",
    "build_writer_package_tasks",
    "build_writer_dry_run_proposal",
    "build_writer_proposal_review",
    "apply_writer_traceability_update_proposal",
    "build_writer_traceability_post_apply_validation",
    "build_completed_package_regression",
    "build_create_new_tc_context_bundle",
    "build_new_tc_draft_proposal",
    "build_new_tc_draft_review",
    "build_new_tc_draft_revision_plan",
    "build_new_tc_revision_decision_pack",
    "build_residual_source_grounding_gap_analysis",
    "build_manual_decision_matrix",
    "build_manual_decision_answer_template",
    "build_manual_decision_answer_pack",
    "compute_file_sha256",
    "compute_requirement_text_hash",
    "compute_text_similarity",
    "load_requirements_diff",
    "load_impact_report",
    "load_agent_capability_improvement_plan",
    "load_test_case_update_plan",
    "load_traceability_mismatch_diagnostics",
    "load_traceability_backfill_proposal",
    "load_traceability_backfill_apply_report",
    "load_traceability_backfill_review",
    "load_traceability_repair_strategy",
    "load_manual_update_packages",
    "load_writer_package_tasks",
    "load_writer_dry_run_proposal",
    "load_writer_proposal_review",
    "load_writer_traceability_update_apply_report",
    "load_writer_traceability_post_apply_validation",
    "load_completed_package_regression",
    "load_create_new_tc_context_bundle",
    "load_new_tc_draft_proposal",
    "load_new_tc_draft_review",
    "load_new_tc_draft_revision_plan",
    "load_new_tc_revision_decision_pack",
    "load_residual_source_grounding_gap_analysis",
    "load_manual_decision_matrix",
    "load_manual_decision_answer_template",
    "load_manual_decision_answer_validation",
    "load_manual_decision_answer_pack",
    "load_manual_decision_answer_pack_import_report",
    "load_requirements_registry",
    "load_requirements_registry_jsonl",
    "load_source_manifest",
    "load_ooxml_source",
    "table_context_from_anchor",
    "load_sections",
    "make_entry_uid",
    "make_req_uid",
    "match_requirement_entries",
    "link_diff_to_test_cases",
    "parse_test_cases",
    "preview_chunks",
    "resolve_sections",
    "write_requirements_diff",
    "write_agent_capability_improvement_plan",
    "write_impact_report",
    "write_test_case_update_plan",
    "write_traceability_mismatch_diagnostics",
    "write_traceability_backfill_proposal",
    "write_traceability_backfill_apply_report",
    "write_traceability_backfill_review",
    "write_traceability_repair_strategy",
    "write_manual_update_packages",
    "write_writer_package_tasks",
    "write_writer_dry_run_proposal",
    "write_writer_proposal_review",
    "write_writer_traceability_update_apply_report",
    "write_writer_traceability_post_apply_validation",
    "write_completed_package_regression",
    "write_create_new_tc_context_bundle",
    "write_new_tc_draft_proposal",
    "write_new_tc_draft_review",
    "write_new_tc_draft_revision_plan",
    "write_new_tc_revision_decision_pack",
    "write_residual_source_grounding_gap_analysis",
    "write_manual_decision_matrix",
    "write_manual_decision_answer_template",
    "write_manual_decision_answer_validation",
    "write_manual_decision_answer_pack",
    "write_manual_decision_answer_pack_import_report",
    "write_requirements_registry",
    "write_source_manifest",
    "validate_manual_decision_answers",
    "import_manual_decision_answer_pack",
    "apply_test_case_update_plan",
    "apply_traceability_backfill_proposal",
    "load_test_case_update_apply_report",
    "write_test_case_update_apply_report",
]
