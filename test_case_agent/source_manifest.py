from __future__ import annotations

import hashlib
import json
import mimetypes
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from lxml import etree

from test_case_agent.ooxml_loader import (
    EXTRACTION_METHOD,
    PARSER_MODE_STRICT,
    OoxmlCoverageAudit,
    load_ooxml_source,
)

MANIFEST_VERSION = "1.0"
CREATED_BY_TOOL = "test_case_agent.source_manifest"
SOURCE_MANIFEST_PREFIX = "source-manifest"
SOURCE_COVERAGE_AUDIT_PREFIX = "source-coverage-audit"
FORBIDDEN_NAME_PATTERNS = [
    "expected",
    "private",
    "golden",
    "answer",
    "solution",
    "bundle",
]

SourceFileRole = Literal["main_docx", "main_pdf", "main_xhtml", "support", "mockup", "other"]
IngestionStatus = Literal["pass", "pass-with-warnings", "blocked"]


@dataclass
class SourceFileEntry:
    path: str
    role: SourceFileRole
    exists: bool
    size_bytes: int | None
    sha256: str | None
    modified_time_utc: str | None
    file_suffix: str
    media_type: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "modified_time_utc": self.modified_time_utc,
            "file_suffix": self.file_suffix,
            "media_type": self.media_type,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceFileEntry":
        return cls(
            path=str(data["path"]),
            role=data["role"],
            exists=bool(data["exists"]),
            size_bytes=data.get("size_bytes"),
            sha256=data.get("sha256"),
            modified_time_utc=data.get("modified_time_utc"),
            file_suffix=str(data.get("file_suffix") or ""),
            media_type=data.get("media_type"),
            notes=list(data.get("notes") or []),
        )


@dataclass
class SourceManifest:
    ft_slug: str
    source_version: str
    manifest_version: str
    created_at_utc: str
    created_by_tool: str
    source_files: list[SourceFileEntry]
    primary_docx: str | None
    primary_pdf: str | None
    primary_xhtml: str | None
    ooxml_coverage_audit_path: str | None
    coverage_audit_created: bool
    ooxml_summary: dict[str, Any]
    ingestion_status: IngestionStatus
    blocking_reasons: list[str]
    warnings: list[str]
    clean_run_audit: dict[str, Any]
    extraction_method: str | None
    parser_mode: str
    ooxml_coverage_audit: OoxmlCoverageAudit | None = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "ft_slug": self.ft_slug,
            "source_version": self.source_version,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "source_files": [entry.to_dict() for entry in self.source_files],
            "primary_docx": self.primary_docx,
            "primary_pdf": self.primary_pdf,
            "primary_xhtml": self.primary_xhtml,
            "ooxml_coverage_audit_path": self.ooxml_coverage_audit_path,
            "coverage_audit_created": self.coverage_audit_created,
            "ooxml_summary": self.ooxml_summary,
            "ingestion_status": self.ingestion_status,
            "blocking_reasons": self.blocking_reasons,
            "warnings": self.warnings,
            "clean_run_audit": self.clean_run_audit,
            "extraction_method": self.extraction_method,
            "parser_mode": self.parser_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceManifest":
        return cls(
            manifest_version=str(data["manifest_version"]),
            ft_slug=str(data["ft_slug"]),
            source_version=str(data["source_version"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            source_files=[
                SourceFileEntry.from_dict(entry)
                for entry in data.get("source_files", [])
            ],
            primary_docx=data.get("primary_docx"),
            primary_pdf=data.get("primary_pdf"),
            primary_xhtml=data.get("primary_xhtml"),
            ooxml_coverage_audit_path=data.get("ooxml_coverage_audit_path"),
            coverage_audit_created=bool(data.get("coverage_audit_created")),
            ooxml_summary=dict(data.get("ooxml_summary") or {}),
            ingestion_status=data["ingestion_status"],
            blocking_reasons=list(data.get("blocking_reasons") or []),
            warnings=list(data.get("warnings") or []),
            clean_run_audit=dict(data.get("clean_run_audit") or {}),
            extraction_method=data.get("extraction_method"),
            parser_mode=str(data.get("parser_mode") or PARSER_MODE_STRICT),
        )


def compute_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_source_manifest(
    *,
    ft_slug: str,
    source_version: str,
    docx: Path | None,
    pdf: Path | None = None,
    xhtml: Path | None = None,
    support_files: list[Path] | None = None,
    mockup_files: list[Path] | None = None,
    other_files: list[Path] | None = None,
    out_dir: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
    parser_mode: str = PARSER_MODE_STRICT,
    allow_tolerant: bool = False,
) -> SourceManifest:
    source_files = _collect_source_file_entries(
        docx=docx,
        pdf=pdf,
        xhtml=xhtml,
        support_files=support_files or [],
        mockup_files=mockup_files or [],
        other_files=other_files or [],
    )
    coverage_path = _coverage_audit_path(out_dir, source_version) if out_dir else None
    blocking_reasons: list[str] = []
    warnings: list[str] = []
    coverage_audit: OoxmlCoverageAudit | None = None

    if docx is None:
        blocking_reasons.append("primary_docx is required.")
    elif not Path(docx).exists():
        blocking_reasons.append(f"primary_docx is missing: {docx}")

    if parser_mode != PARSER_MODE_STRICT and not allow_tolerant:
        blocking_reasons.append(
            f'parser_mode "{parser_mode}" requires an explicit tolerant flag.'
        )

    if docx is not None and Path(docx).exists() and not blocking_reasons:
        try:
            ooxml_source = load_ooxml_source(Path(docx), parser_mode=parser_mode)
            coverage_audit = ooxml_source.coverage
            warnings.extend(_warnings_from_coverage(coverage_audit))
            blocking_reasons.extend(_critical_coverage_blockers(coverage_audit))
        except zipfile.BadZipFile as exc:
            blocking_reasons.append(f"DOCX is not readable as ZIP: {docx}: {exc}")
        except etree.XMLSyntaxError as exc:
            blocking_reasons.append(f"DOCX XML parsing failed: {docx}: {exc}")
        except Exception as exc:  # noqa: BLE001 - manifest must report ingestion blockers.
            blocking_reasons.append(f"DOCX OOXML coverage audit failed: {docx}: {exc}")

    if coverage_audit is None and docx is not None and Path(docx).exists() and not blocking_reasons:
        blocking_reasons.append("coverage audit was not created.")

    ingestion_status = _ingestion_status(blocking_reasons, warnings)
    return SourceManifest(
        ft_slug=ft_slug,
        source_version=source_version,
        manifest_version=MANIFEST_VERSION,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        source_files=source_files,
        primary_docx=str(docx) if docx is not None else None,
        primary_pdf=str(pdf) if pdf is not None else None,
        primary_xhtml=str(xhtml) if xhtml is not None else None,
        ooxml_coverage_audit_path=str(coverage_path) if coverage_path else None,
        coverage_audit_created=coverage_audit is not None,
        ooxml_summary=_ooxml_summary(coverage_audit),
        ingestion_status=ingestion_status,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
        clean_run_audit=_build_clean_run_audit(docx, source_files),
        extraction_method=coverage_audit.extraction_method if coverage_audit else None,
        parser_mode=coverage_audit.parser_mode if coverage_audit else parser_mode,
        ooxml_coverage_audit=coverage_audit,
    )


def write_source_manifest(
    manifest: SourceManifest,
    out_dir: Path,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    coverage_path = _coverage_audit_path(out_dir, manifest.source_version)
    manifest_path = _manifest_path(out_dir, manifest.source_version)

    manifest.ooxml_coverage_audit_path = str(coverage_path)
    if manifest.ooxml_coverage_audit is not None:
        coverage_path.write_text(
            json.dumps(manifest.ooxml_coverage_audit.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest.coverage_audit_created = True
    else:
        if "coverage audit was not created." not in manifest.blocking_reasons:
            manifest.blocking_reasons.append("coverage audit was not created.")
        manifest.ingestion_status = "blocked"
        manifest.coverage_audit_created = False

    manifest_path.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest_path


def load_source_manifest(path: Path) -> SourceManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Source manifest root must be a JSON object.")
    return SourceManifest.from_dict(data)


def _collect_source_file_entries(
    *,
    docx: Path | None,
    pdf: Path | None,
    xhtml: Path | None,
    support_files: list[Path],
    mockup_files: list[Path],
    other_files: list[Path],
) -> list[SourceFileEntry]:
    entries: list[SourceFileEntry] = []
    for path, role in [
        (docx, "main_docx"),
        (pdf, "main_pdf"),
        (xhtml, "main_xhtml"),
    ]:
        if path is not None:
            entries.append(_source_file_entry(Path(path), role))
    for path in support_files:
        entries.append(_source_file_entry(Path(path), "support"))
    for path in mockup_files:
        entries.append(_source_file_entry(Path(path), "mockup"))
    for path in other_files:
        entries.append(_source_file_entry(Path(path), "other"))
    return entries


def _source_file_entry(path: Path, role: SourceFileRole) -> SourceFileEntry:
    path = Path(path)
    exists = path.exists() and path.is_file()
    media_type, _encoding = mimetypes.guess_type(str(path))
    if not exists:
        return SourceFileEntry(
            path=str(path),
            role=role,
            exists=False,
            size_bytes=None,
            sha256=None,
            modified_time_utc=None,
            file_suffix=path.suffix.lower(),
            media_type=media_type,
            notes=["missing file"],
        )

    stat = path.stat()
    return SourceFileEntry(
        path=str(path),
        role=role,
        exists=True,
        size_bytes=stat.st_size,
        sha256=compute_file_sha256(path),
        modified_time_utc=_utc_from_timestamp(stat.st_mtime),
        file_suffix=path.suffix.lower(),
        media_type=media_type,
        notes=[],
    )


def _warnings_from_coverage(coverage: OoxmlCoverageAudit) -> list[str]:
    warnings = list(coverage.extraction_warnings)
    if coverage.comments_count:
        warnings.append(
            f"Comments present and extracted separately: {coverage.comments_count}"
        )
    if coverage.footnotes_count:
        warnings.append(
            f"Footnotes present and extracted separately: {coverage.footnotes_count}"
        )
    if coverage.endnotes_count:
        warnings.append(
            f"Endnotes present and extracted separately: {coverage.endnotes_count}"
        )
    if coverage.custom_xml_parts_count:
        warnings.append(
            f"customXml parts present and extracted separately: {coverage.custom_xml_parts_count}"
        )
    if coverage.hidden_text_count:
        warnings.append(f"Hidden text nodes detected: {coverage.hidden_text_count}")
    if coverage.tracked_insert_count:
        warnings.append(
            f"Tracked insertion elements detected: {coverage.tracked_insert_count}"
        )
    if coverage.tracked_delete_count:
        warnings.append(
            f"Tracked deletion elements detected: {coverage.tracked_delete_count}"
        )
    return warnings


def _critical_coverage_blockers(coverage: OoxmlCoverageAudit) -> list[str]:
    blockers: list[str] = []
    if "[Content_Types].xml" not in coverage.xml_parts_extracted:
        blockers.append("critical XML part was not extracted: [Content_Types].xml")
    if "word/document.xml" not in coverage.xml_parts_extracted:
        blockers.append("critical XML part was not extracted: word/document.xml")
    if "_rels/.rels" not in coverage.rels_parts_extracted:
        blockers.append("critical relationships part was not extracted: _rels/.rels")
    return blockers


def _ooxml_summary(coverage: OoxmlCoverageAudit | None) -> dict[str, Any]:
    if coverage is None:
        return {}
    return {
        "zip_entries_seen": len(coverage.zip_entries_seen),
        "xml_parts_extracted": len(coverage.xml_parts_extracted),
        "rels_parts_extracted": len(coverage.rels_parts_extracted),
        "binary_parts_seen": len(coverage.binary_parts_seen),
        "extraction_warnings": len(coverage.extraction_warnings),
        "comments_count": coverage.comments_count,
        "footnotes_count": coverage.footnotes_count,
        "endnotes_count": coverage.endnotes_count,
        "headers_count": coverage.headers_count,
        "footers_count": coverage.footers_count,
        "hidden_text_count": coverage.hidden_text_count,
        "tracked_insert_count": coverage.tracked_insert_count,
        "tracked_delete_count": coverage.tracked_delete_count,
        "custom_xml_parts_count": coverage.custom_xml_parts_count,
    }


def _build_clean_run_audit(
    docx: Path | None,
    source_files: list[SourceFileEntry],
) -> dict[str, Any]:
    files_read = sorted(entry.path for entry in source_files if entry.exists and entry.sha256)
    forbidden_files_detected_nearby = _detect_forbidden_files_nearby(docx)
    forbidden_files_in_inputs = sorted(
        entry.path for entry in source_files if _is_forbidden_name(Path(entry.path))
    )
    forbidden_files_read = sorted(
        entry.path
        for entry in source_files
        if entry.exists and entry.sha256 and _is_forbidden_name(Path(entry.path))
    )
    if forbidden_files_read:
        clean_run_status = "contaminated"
    elif forbidden_files_detected_nearby:
        clean_run_status = "contaminated-risk"
    else:
        clean_run_status = "clean"
    return {
        "files_read": files_read,
        "forbidden_name_patterns": FORBIDDEN_NAME_PATTERNS,
        "forbidden_files_detected_nearby": forbidden_files_detected_nearby,
        "forbidden_files_in_inputs": forbidden_files_in_inputs,
        "forbidden_files_read": forbidden_files_read,
        "clean_run_claim": clean_run_status == "clean",
        "clean_run_status": clean_run_status,
    }


def _detect_forbidden_files_nearby(docx: Path | None) -> list[str]:
    if docx is None:
        return []
    parent = Path(docx).parent
    if not parent.exists():
        return []
    source_name = Path(docx).name.lower()
    detected: list[str] = []
    for candidate in parent.iterdir():
        if not candidate.is_file():
            continue
        if candidate.name.lower() == source_name:
            continue
        if _is_forbidden_name(candidate):
            detected.append(str(candidate))
    return sorted(detected)


def _is_forbidden_name(path: Path) -> bool:
    return any(pattern in path.name.lower() for pattern in FORBIDDEN_NAME_PATTERNS)


def _ingestion_status(
    blocking_reasons: list[str],
    warnings: list[str],
) -> IngestionStatus:
    if blocking_reasons:
        return "blocked"
    if warnings:
        return "pass-with-warnings"
    return "pass"


def _manifest_path(out_dir: Path, source_version: str) -> Path:
    return Path(out_dir) / f"{SOURCE_MANIFEST_PREFIX}.{source_version}.json"


def _coverage_audit_path(out_dir: Path, source_version: str) -> Path:
    return Path(out_dir) / f"{SOURCE_COVERAGE_AUDIT_PREFIX}.{source_version}.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")
