"""Public library API for the FT Test Case Agent."""

from test_case_agent.api import (
    DEFAULT_MAX_CHARS,
    InvalidSourceError,
    NoMatchingSectionsError,
    OoxmlCoverageAudit,
    OoxmlSource,
    inspect_source_quality,
    extract_ooxml_source_nodes,
    inspect_ooxml_coverage,
    load_ooxml_source,
    load_sections,
    preview_chunks,
    resolve_sections,
    SourceNode,
)
from test_case_agent.models import Section, SectionChunk
from test_case_agent.source_quality import (
    SourceQualityIssue,
    analyze_sections,
    classify_source_quality_issue,
)

__all__ = [
    "DEFAULT_MAX_CHARS",
    "InvalidSourceError",
    "NoMatchingSectionsError",
    "OoxmlCoverageAudit",
    "OoxmlSource",
    "Section",
    "SectionChunk",
    "SourceNode",
    "SourceQualityIssue",
    "analyze_sections",
    "classify_source_quality_issue",
    "extract_ooxml_source_nodes",
    "inspect_ooxml_coverage",
    "inspect_source_quality",
    "load_ooxml_source",
    "load_sections",
    "preview_chunks",
    "resolve_sections",
]
