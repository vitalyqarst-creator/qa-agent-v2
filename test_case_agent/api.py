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
    "InvalidSourceError",
    "NoMatchingSectionsError",
    "OoxmlCoverageAudit",
    "OoxmlSource",
    "Section",
    "SectionChunk",
    "SourceFileEntry",
    "SourceManifest",
    "SourceNode",
    "SourceQualityIssue",
    "extract_ooxml_source_nodes",
    "inspect_ooxml_coverage",
    "inspect_source_quality",
    "build_source_manifest",
    "compute_file_sha256",
    "load_source_manifest",
    "load_ooxml_source",
    "load_sections",
    "preview_chunks",
    "resolve_sections",
    "write_source_manifest",
]
