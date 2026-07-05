from __future__ import annotations

from pathlib import Path

from test_case_agent.chunking import split_section
from test_case_agent.document_loader import load_sections as load_sections_from_source
from test_case_agent.models import Section, SectionChunk
from test_case_agent.ooxml_loader import (
    OoxmlCoverageAudit,
    OoxmlSource,
    SourceNode,
    extract_ooxml_source_nodes,
    inspect_ooxml_coverage,
    load_ooxml_source,
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
    "InvalidSourceError",
    "ImpactEntry",
    "ImpactReport",
    "ManualUpdatePackage",
    "ManualUpdatePackagesReport",
    "NoMatchingSectionsError",
    "OoxmlCoverageAudit",
    "OoxmlSource",
    "RequirementRegistry",
    "RequirementRegistryEntry",
    "RequirementsDiff",
    "RequirementsDiffEntry",
    "Section",
    "SectionChunk",
    "SourceAnchor",
    "SourceFileEntry",
    "SourceManifest",
    "SourceNode",
    "SourceQualityIssue",
    "TestCaseLink",
    "TestCaseUpdatePlan",
    "TraceabilityMismatch",
    "TraceabilityMismatchDiagnosticsReport",
    "WriterPackageTask",
    "WriterPackageTasksReport",
    "WriterDryRunProposal",
    "UpdatePlanItem",
    "extract_ooxml_source_nodes",
    "inspect_ooxml_coverage",
    "inspect_source_quality",
    "build_source_manifest",
    "build_requirements_registry",
    "build_requirements_diff",
    "build_impact_report",
    "build_test_case_update_plan",
    "build_traceability_mismatch_diagnostics",
    "build_manual_update_packages",
    "build_writer_package_tasks",
    "build_writer_dry_run_proposal",
    "compute_file_sha256",
    "compute_requirement_text_hash",
    "compute_text_similarity",
    "load_requirements_diff",
    "load_impact_report",
    "load_test_case_update_plan",
    "load_traceability_mismatch_diagnostics",
    "load_manual_update_packages",
    "load_writer_package_tasks",
    "load_writer_dry_run_proposal",
    "load_requirements_registry",
    "load_requirements_registry_jsonl",
    "load_source_manifest",
    "load_ooxml_source",
    "load_sections",
    "make_entry_uid",
    "make_req_uid",
    "match_requirement_entries",
    "link_diff_to_test_cases",
    "parse_test_cases",
    "preview_chunks",
    "resolve_sections",
    "write_requirements_diff",
    "write_impact_report",
    "write_test_case_update_plan",
    "write_traceability_mismatch_diagnostics",
    "write_manual_update_packages",
    "write_writer_package_tasks",
    "write_writer_dry_run_proposal",
    "write_requirements_registry",
    "write_source_manifest",
    "apply_test_case_update_plan",
    "load_test_case_update_apply_report",
    "write_test_case_update_apply_report",
]
