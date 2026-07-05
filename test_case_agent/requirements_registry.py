from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.ooxml_loader import PARSER_MODE_STRICT, SourceNode, load_ooxml_source
from test_case_agent.source_manifest import SourceManifest, compute_file_sha256, load_source_manifest

REGISTRY_VERSION = "1.0"
CREATED_BY_TOOL = "test_case_agent.requirements_registry"
REQUIREMENTS_PREFIX = "requirements"
REQUIREMENTS_SUMMARY_PREFIX = "requirements-summary"
SINGLE_LETTER_TABLE_MARKER_WARNING = (
    "Single-letter table marker requires row/header context before promotion to active requirement."
)
DUPLICATE_REQ_UID_WARNING = (
    "Duplicate req_uid values detected; review source anchors before using registry for diff."
)
SOURCE_ONLY_DIFF_EXCLUSION_REASON = (
    "source_only entries are excluded from requirements diff by default"
)
CONTEXT_MISSING_WARNING = "No source-backed semantic context was extracted for diff-eligible entry."

RequirementStatus = Literal["active", "gap", "unclear", "source_only"]
RequirementConfidence = Literal["high", "medium", "low"]
RegistryStatus = Literal["pass", "pass-with-warnings", "blocked"]

SOURCE_REQ_ID_RE = re.compile(
    r"\b(?:BSR\s+\d+|GSR\s+\d+|REQ[- ]?\d+|ID\s+\d+|[A-ZА-Я]{2,}-\d+)\b",
    re.IGNORECASE,
)
SECTION_ID_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\b")
WHITESPACE_RE = re.compile(r"\s+")
SERVICE_FLAG_NAMES = {
    "comment",
    "custom_xml",
    "docprop",
    "endnote",
    "footnote",
    "header",
    "footer",
    "hidden_text",
    "tracked_delete",
}


@dataclass(frozen=True)
class SourceAnchor:
    source_doc: str
    source_version: str
    part: str
    xpath: str
    node_id: str
    value_type: str
    flags: list[str]
    aggregate_kind: str | None
    aggregate_confidence: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_doc": self.source_doc,
            "source_version": self.source_version,
            "part": self.part,
            "xpath": self.xpath,
            "node_id": self.node_id,
            "value_type": self.value_type,
            "flags": self.flags,
            "aggregate_kind": self.aggregate_kind,
            "aggregate_confidence": self.aggregate_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceAnchor":
        return cls(
            source_doc=str(data["source_doc"]),
            source_version=str(data["source_version"]),
            part=str(data["part"]),
            xpath=str(data["xpath"]),
            node_id=str(data["node_id"]),
            value_type=str(data["value_type"]),
            flags=list(data.get("flags") or []),
            aggregate_kind=data.get("aggregate_kind"),
            aggregate_confidence=data.get("aggregate_confidence"),
        )


@dataclass(frozen=True)
class RequirementRegistryEntry:
    req_uid: str
    entry_uid: str
    atom_id: str
    source_version: str
    ft_slug: str
    source_req_id: str | None
    source_row_id: str | None
    section_id: str | None
    scope_slug: str | None
    package_id: str | None
    requirement_type: str
    object: str | None
    condition: str | None
    expected_behavior: str | None
    source_text: str
    normalized_text: str
    context_text: str | None
    context_hash: str | None
    context_source: str | None
    source_anchors: list[SourceAnchor]
    semantic_fingerprint: str
    text_hash: str
    status: RequirementStatus
    diff_eligible: bool
    diff_exclusion_reason: str | None
    context_warnings: list[str]
    confidence: RequirementConfidence
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_uid": self.req_uid,
            "entry_uid": self.entry_uid,
            "atom_id": self.atom_id,
            "source_version": self.source_version,
            "ft_slug": self.ft_slug,
            "source_req_id": self.source_req_id,
            "source_row_id": self.source_row_id,
            "section_id": self.section_id,
            "scope_slug": self.scope_slug,
            "package_id": self.package_id,
            "requirement_type": self.requirement_type,
            "object": self.object,
            "condition": self.condition,
            "expected_behavior": self.expected_behavior,
            "source_text": self.source_text,
            "normalized_text": self.normalized_text,
            "context_text": self.context_text,
            "context_hash": self.context_hash,
            "context_source": self.context_source,
            "source_anchors": [anchor.to_dict() for anchor in self.source_anchors],
            "semantic_fingerprint": self.semantic_fingerprint,
            "text_hash": self.text_hash,
            "status": self.status,
            "diff_eligible": self.diff_eligible,
            "diff_exclusion_reason": self.diff_exclusion_reason,
            "context_warnings": self.context_warnings,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementRegistryEntry":
        source_anchors = [
            SourceAnchor.from_dict(anchor)
            for anchor in data.get("source_anchors", [])
        ]
        status = data["status"]
        diff_eligible = bool(data.get("diff_eligible", _is_diff_eligible_status(status)))
        diff_exclusion_reason = data.get("diff_exclusion_reason")
        if not diff_eligible and diff_exclusion_reason is None:
            diff_exclusion_reason = SOURCE_ONLY_DIFF_EXCLUSION_REASON if status == "source_only" else None
        return cls(
            req_uid=str(data["req_uid"]),
            entry_uid=str(data.get("entry_uid") or make_entry_uid(
                str(data["ft_slug"]),
                str(data["source_version"]),
                str(data["normalized_text"]),
                source_anchors,
            )),
            atom_id=str(data["atom_id"]),
            source_version=str(data["source_version"]),
            ft_slug=str(data["ft_slug"]),
            source_req_id=data.get("source_req_id"),
            source_row_id=data.get("source_row_id"),
            section_id=data.get("section_id"),
            scope_slug=data.get("scope_slug"),
            package_id=data.get("package_id"),
            requirement_type=str(data["requirement_type"]),
            object=data.get("object"),
            condition=data.get("condition"),
            expected_behavior=data.get("expected_behavior"),
            source_text=str(data["source_text"]),
            normalized_text=str(data["normalized_text"]),
            context_text=data.get("context_text"),
            context_hash=data.get("context_hash"),
            context_source=data.get("context_source"),
            source_anchors=source_anchors,
            semantic_fingerprint=str(data["semantic_fingerprint"]),
            text_hash=str(data["text_hash"]),
            status=status,
            diff_eligible=diff_eligible,
            diff_exclusion_reason=diff_exclusion_reason,
            context_warnings=list(data.get("context_warnings") or []),
            confidence=data["confidence"],
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class RequirementContext:
    context_text: str | None
    context_hash: str | None
    context_source: str | None
    object_value: str | None
    condition: str | None
    warnings: list[str]


@dataclass
class RequirementRegistry:
    ft_slug: str
    source_version: str
    registry_version: str
    created_at_utc: str
    created_by_tool: str
    source_manifest_path: str
    source_manifest_sha256: str | None
    coverage_audit_path: str | None
    entries: list[RequirementRegistryEntry]
    extraction_summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ft_slug": self.ft_slug,
            "source_version": self.source_version,
            "registry_version": self.registry_version,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "source_manifest_path": self.source_manifest_path,
            "source_manifest_sha256": self.source_manifest_sha256,
            "coverage_audit_path": self.coverage_audit_path,
            "entries": [entry.to_dict() for entry in self.entries],
            "extraction_summary": self.extraction_summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }


def build_requirements_registry(
    source_manifest_path: Path,
    *,
    created_by_tool: str = CREATED_BY_TOOL,
) -> RequirementRegistry:
    source_manifest_path = Path(source_manifest_path)
    manifest_sha256: str | None = None
    if not source_manifest_path.exists():
        return _blocked_registry(
            source_manifest_path=source_manifest_path,
            source_manifest_sha256=None,
            coverage_audit_path=None,
            ft_slug="unknown",
            source_version="unknown",
            created_by_tool=created_by_tool,
            blocking_reasons=[f"source manifest is missing: {source_manifest_path}"],
        )

    manifest_sha256 = compute_file_sha256(source_manifest_path)
    manifest = load_source_manifest(source_manifest_path)
    blocking_reasons = _manifest_blocking_reasons(manifest, source_manifest_path)
    if blocking_reasons:
        return _blocked_registry(
            source_manifest_path=source_manifest_path,
            source_manifest_sha256=manifest_sha256,
            coverage_audit_path=manifest.ooxml_coverage_audit_path,
            ft_slug=manifest.ft_slug,
            source_version=manifest.source_version,
            created_by_tool=created_by_tool,
            blocking_reasons=blocking_reasons,
            warnings=list(manifest.warnings),
        )

    coverage_path = Path(str(manifest.ooxml_coverage_audit_path))
    primary_docx = Path(str(manifest.primary_docx))
    blocking_reasons.extend(_required_file_blockers(coverage_path, primary_docx))
    if blocking_reasons:
        return _blocked_registry(
            source_manifest_path=source_manifest_path,
            source_manifest_sha256=manifest_sha256,
            coverage_audit_path=manifest.ooxml_coverage_audit_path,
            ft_slug=manifest.ft_slug,
            source_version=manifest.source_version,
            created_by_tool=created_by_tool,
            blocking_reasons=blocking_reasons,
            warnings=list(manifest.warnings),
        )

    try:
        _read_coverage_audit_json(coverage_path)
        ooxml_source = load_ooxml_source(primary_docx, parser_mode=manifest.parser_mode or PARSER_MODE_STRICT)
    except Exception as exc:  # noqa: BLE001 - registry must report source blockers.
        return _blocked_registry(
            source_manifest_path=source_manifest_path,
            source_manifest_sha256=manifest_sha256,
            coverage_audit_path=manifest.ooxml_coverage_audit_path,
            ft_slug=manifest.ft_slug,
            source_version=manifest.source_version,
            created_by_tool=created_by_tool,
            blocking_reasons=[f"requirements registry source read failed: {exc}"],
            warnings=list(manifest.warnings),
        )

    entries = _extract_entries(manifest, ooxml_source.nodes)
    warnings = _registry_warnings(manifest, entries)
    extraction_summary = _extraction_summary(
        manifest=manifest,
        entries=entries,
        candidates_seen=len(ooxml_source.nodes),
        source_manifest_path=source_manifest_path,
        registry_path=None,
        warnings=warnings,
        blocking_reasons=[],
        source_manifest_sha256=manifest_sha256,
        coverage_audit_path=manifest.ooxml_coverage_audit_path,
        created_by_tool=created_by_tool,
    )
    return RequirementRegistry(
        ft_slug=manifest.ft_slug,
        source_version=manifest.source_version,
        registry_version=REGISTRY_VERSION,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        source_manifest_path=str(source_manifest_path),
        source_manifest_sha256=manifest_sha256,
        coverage_audit_path=manifest.ooxml_coverage_audit_path,
        entries=entries,
        extraction_summary=extraction_summary,
        warnings=warnings,
        blocking_reasons=[],
    )


def write_requirements_registry(
    registry: RequirementRegistry,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    registry_path = _registry_path(out_dir, registry.source_version)
    summary_path = _summary_path(out_dir, registry.source_version)

    registry_path.write_text(
        "".join(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n" for entry in registry.entries),
        encoding="utf-8",
        newline="\n",
    )
    registry.extraction_summary = _extraction_summary(
        manifest=None,
        entries=registry.entries,
        candidates_seen=registry.extraction_summary.get("source_nodes_seen", 0),
        source_manifest_path=Path(registry.source_manifest_path),
        registry_path=registry_path,
        warnings=registry.warnings,
        blocking_reasons=registry.blocking_reasons,
        ft_slug=registry.ft_slug,
        source_version=registry.source_version,
        source_manifest_sha256=registry.source_manifest_sha256,
        coverage_audit_path=registry.coverage_audit_path,
        created_by_tool=registry.created_by_tool,
    )
    summary_path.write_text(
        json.dumps(registry.extraction_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return registry_path, summary_path


def load_requirements_registry_jsonl(path: Path) -> list[RequirementRegistryEntry]:
    entries: list[RequirementRegistryEntry] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError("Requirements registry JSONL line must be a JSON object.")
        entries.append(RequirementRegistryEntry.from_dict(payload))
    return entries


def load_requirements_registry(
    registry_path: Path,
    summary_path: Path | None = None,
) -> RequirementRegistry:
    registry_path = Path(registry_path)
    entries = load_requirements_registry_jsonl(registry_path)
    summary_path = Path(summary_path) if summary_path is not None else _infer_summary_path(registry_path)
    summary: dict[str, Any] = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not isinstance(summary, dict):
            raise ValueError("Requirements summary root must be a JSON object.")

    ft_slug = str(summary.get("ft_slug") or (entries[0].ft_slug if entries else "unknown"))
    source_version = str(summary.get("source_version") or (entries[0].source_version if entries else "unknown"))
    return RequirementRegistry(
        ft_slug=ft_slug,
        source_version=source_version,
        registry_version=str(summary.get("registry_version") or REGISTRY_VERSION),
        created_at_utc=str(summary.get("created_at_utc") or ""),
        created_by_tool=str(summary.get("created_by_tool") or CREATED_BY_TOOL),
        source_manifest_path=str(summary.get("source_manifest_path") or ""),
        source_manifest_sha256=summary.get("source_manifest_sha256"),
        coverage_audit_path=summary.get("coverage_audit_path"),
        entries=entries,
        extraction_summary=summary,
        warnings=list(summary.get("warnings") or []),
        blocking_reasons=list(summary.get("blocking_reasons") or []),
    )


def compute_requirement_text_hash(normalized_text: str) -> str:
    digest = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def make_req_uid(
    ft_slug: str,
    normalized_text: str,
    source_req_id: str | None = None,
    requirement_type: str | None = None,
    object_value: str | None = None,
    condition: str | None = None,
    context_hash: str | None = None,
) -> str:
    slug = _uid_slug(ft_slug)
    values = [
        _normalize_text(normalized_text),
        source_req_id or "",
        requirement_type or "",
    ]
    if object_value is not None or condition is not None or context_hash is not None:
        values.extend(
            [
                _normalize_text(object_value),
                _normalize_text(condition),
                context_hash or "",
            ]
        )
    fingerprint = "|".join(values)
    short_hash = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12].upper()
    return f"REQ-{slug}-{short_hash}"


def make_entry_uid(
    ft_slug: str,
    source_version: str,
    normalized_text: str,
    source_anchors: list[SourceAnchor],
) -> str:
    slug = _uid_slug(ft_slug)
    anchor = source_anchors[0] if source_anchors else None
    fingerprint = "|".join(
        [
            slug,
            source_version,
            anchor.part if anchor else "",
            anchor.xpath if anchor else "",
            anchor.node_id if anchor else "",
            anchor.value_type if anchor else "",
            compute_requirement_text_hash(normalized_text),
        ]
    )
    short_hash = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16].upper()
    return f"ENTRY-{slug}-{short_hash}"


def _extract_entries(
    manifest: SourceManifest,
    nodes: list[SourceNode],
) -> list[RequirementRegistryEntry]:
    context_index = _build_context_index(nodes)
    direct_values = {
        (node.part, _normalize_text(node.value))
        for node in nodes
        if node.value_type in {"text", "attribute"} and _normalize_text(node.value)
    }
    candidates = [
        node
        for node in nodes
        if _is_registry_candidate(node, direct_values)
    ]

    entries: list[RequirementRegistryEntry] = []
    seen: set[tuple[str, str, str, str]] = set()
    for node in candidates:
        normalized_text = _normalize_text(node.value)
        dedupe_key = (node.part, node.xpath, node.value_type, normalized_text)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        source_req_id = _detect_source_req_id(normalized_text)
        requirement_type = _detect_requirement_type(normalized_text, node.flags)
        warnings = _node_warnings(node, normalized_text)
        status = _entry_status(node, requirement_type, normalized_text)
        confidence = _entry_confidence(node, requirement_type, status)
        diff_eligible = _is_diff_eligible_status(status)
        diff_exclusion_reason = None if diff_eligible else SOURCE_ONLY_DIFF_EXCLUSION_REASON
        context = _context_for_node(node, normalized_text, context_index) if diff_eligible else _empty_context()
        context_warnings = list(context.warnings)
        if diff_eligible and context.context_text is None:
            context_warnings.append(CONTEXT_MISSING_WARNING)
        warnings.extend(context_warnings)
        expected_behavior = normalized_text if status == "active" else None
        semantic_fingerprint = _semantic_fingerprint(
            requirement_type=requirement_type,
            object_value=context.object_value,
            condition=context.condition,
            expected_behavior=expected_behavior,
            normalized_text=normalized_text,
            context_text=context.context_text if diff_eligible else None,
        )
        atom_id = f"ATOM-{len(entries) + 1:06d}"
        source_anchors = [
            SourceAnchor(
                source_doc=node.source_path,
                source_version=manifest.source_version,
                part=node.part,
                xpath=node.xpath,
                node_id=node.node_id,
                value_type=node.value_type,
                flags=list(node.flags),
                aggregate_kind=node.aggregate_kind,
                aggregate_confidence=node.aggregate_confidence,
            )
        ]
        entry = RequirementRegistryEntry(
            req_uid=make_req_uid(
                manifest.ft_slug,
                normalized_text,
                source_req_id=source_req_id,
                requirement_type=requirement_type,
                object_value=context.object_value if diff_eligible else None,
                condition=context.condition if diff_eligible else None,
                context_hash=context.context_hash if diff_eligible else None,
            ),
            entry_uid=make_entry_uid(
                manifest.ft_slug,
                manifest.source_version,
                normalized_text,
                source_anchors,
            ),
            atom_id=atom_id,
            source_version=manifest.source_version,
            ft_slug=manifest.ft_slug,
            source_req_id=source_req_id,
            source_row_id=None,
            section_id=_detect_section_id(normalized_text),
            scope_slug=None,
            package_id=None,
            requirement_type=requirement_type,
            object=context.object_value,
            condition=context.condition,
            expected_behavior=expected_behavior,
            source_text=node.value,
            normalized_text=normalized_text,
            context_text=context.context_text,
            context_hash=context.context_hash,
            context_source=context.context_source,
            source_anchors=source_anchors,
            semantic_fingerprint=semantic_fingerprint,
            text_hash=compute_requirement_text_hash(normalized_text),
            status=status,
            diff_eligible=diff_eligible,
            diff_exclusion_reason=diff_exclusion_reason,
            context_warnings=context_warnings,
            confidence=confidence,
            warnings=warnings,
        )
        entries.append(entry)
    return entries


def _is_registry_candidate(
    node: SourceNode,
    direct_values: set[tuple[str, str]],
) -> bool:
    value = _normalize_text(node.value)
    if not value:
        return False
    if "[Content_Types].xml" == node.part:
        return False
    if node.part.endswith(".rels"):
        return bool(node.target_url and node.attribute_name == "Target")
    if node.value_type == "tail":
        return False
    if node.value_type == "aggregate" and (node.part, value) in direct_values:
        return False
    if node.value_type == "attribute" and _is_technical_attribute(node):
        return False
    if _is_service_value(value) and _detect_requirement_type(value, node.flags) == "metadata/source_only":
        return False
    return True


def _empty_context() -> RequirementContext:
    return RequirementContext(
        context_text=None,
        context_hash=None,
        context_source="none",
        object_value=None,
        condition=None,
        warnings=[],
    )


def _build_context_index(nodes: list[SourceNode]) -> dict[str, Any]:
    table_rows: dict[tuple[str, str], list[SourceNode]] = {}
    table_cells: dict[tuple[str, str, int], list[SourceNode]] = {}
    paragraphs: dict[str, list[SourceNode]] = {}

    for node in nodes:
        if node.value_type == "tail":
            continue
        if not _normalize_text(node.value):
            continue
        row_key = _table_row_key(node.xpath)
        if row_key:
            table_rows.setdefault((node.part, row_key), []).append(node)
            cell_key = _table_cell_key(node.xpath)
            if cell_key:
                cell_path, cell_index = cell_key
                table_cells.setdefault((node.part, cell_path, cell_index), []).append(node)
            continue
        paragraph_key = _paragraph_key(node.xpath)
        if paragraph_key and node.value_type == "aggregate" and node.aggregate_kind == "paragraph":
            paragraphs.setdefault(node.part, []).append(node)

    return {
        "table_rows": {
            key: sorted(value, key=lambda item: _xpath_sort_key(item.xpath))
            for key, value in table_rows.items()
        },
        "table_cells": {
            key: sorted(value, key=lambda item: _xpath_sort_key(item.xpath))
            for key, value in table_cells.items()
        },
        "paragraphs": {
            part: sorted(value, key=lambda item: _xpath_sort_key(item.xpath))
            for part, value in paragraphs.items()
        },
    }


def _context_for_node(
    node: SourceNode,
    normalized_text: str,
    context_index: dict[str, Any],
) -> RequirementContext:
    table_context = _table_context_for_node(node, normalized_text, context_index)
    if table_context.context_text:
        return table_context
    paragraph_context = _paragraph_context_for_node(node, context_index)
    if paragraph_context.context_text:
        return paragraph_context
    return _empty_context()


def _table_context_for_node(
    node: SourceNode,
    normalized_text: str,
    context_index: dict[str, Any],
) -> RequirementContext:
    row_key = _table_row_key(node.xpath)
    cell_key = _table_cell_key(node.xpath)
    if not row_key:
        return _empty_context()

    row_nodes = context_index["table_rows"].get((node.part, row_key), [])
    row_text = _join_context_values(
        candidate.value
        for candidate in row_nodes
        if candidate.value_type in {"text", "attribute", "aggregate"}
    )
    if not row_text:
        return _empty_context()

    object_value: str | None = None
    if cell_key:
        _cell_path, cell_index = cell_key
        object_value = _object_from_left_cell(
            node.part,
            row_key,
            cell_index,
            normalized_text,
            context_index,
        )

    return RequirementContext(
        context_text=row_text,
        context_hash=compute_context_hash(row_text),
        context_source="table_row",
        object_value=object_value,
        condition=None,
        warnings=[],
    )


def _object_from_left_cell(
    part: str,
    row_key: str,
    cell_index: int,
    normalized_text: str,
    context_index: dict[str, Any],
) -> str | None:
    for candidate_index in range(cell_index - 1, 0, -1):
        cell_path = f"{row_key}/w:tc[{candidate_index}]"
        cell_nodes = context_index["table_cells"].get((part, cell_path, candidate_index), [])
        cell_text = _join_context_values(
            node.value
            for node in cell_nodes
            if node.value_type in {"text", "attribute", "aggregate"}
        )
        if not cell_text:
            continue
        if _normalize_text(cell_text).casefold() == normalized_text.casefold():
            continue
        if len(_normalize_text(cell_text)) <= 2:
            continue
        return cell_text
    return None


def _paragraph_context_for_node(
    node: SourceNode,
    context_index: dict[str, Any],
) -> RequirementContext:
    paragraph_key = _paragraph_key(node.xpath)
    if not paragraph_key:
        return _empty_context()
    paragraphs = context_index["paragraphs"].get(node.part, [])
    index = next(
        (
            position
            for position, paragraph in enumerate(paragraphs)
            if paragraph.xpath.startswith(f"{paragraph_key}/")
            or paragraph.xpath == f"{paragraph_key}/aggregate::paragraph"
        ),
        None,
    )
    if index is None:
        return _empty_context()
    neighbors = paragraphs[max(0, index - 1) : index + 2]
    context_text = _join_context_values(paragraph.value for paragraph in neighbors)
    if not context_text:
        return _empty_context()
    return RequirementContext(
        context_text=context_text,
        context_hash=compute_context_hash(context_text),
        context_source="paragraph_neighbors",
        object_value=None,
        condition=None,
        warnings=[],
    )


def compute_context_hash(context_text: str) -> str:
    digest = hashlib.sha256(_normalize_text(context_text).casefold().encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _join_context_values(values: Any) -> str:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = _normalize_text(value)
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return " | ".join(result)


def _table_row_key(xpath: str) -> str | None:
    match = re.match(r"^(.*?/w:tr\[\d+\])(?:/|$)", xpath)
    return match.group(1) if match else None


def _table_cell_key(xpath: str) -> tuple[str, int] | None:
    match = re.match(r"^(.*?/w:tr\[\d+\]/w:tc\[(\d+)\])(?:/|$)", xpath)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def _paragraph_key(xpath: str) -> str | None:
    match = re.match(r"^(.*?/w:p(?:\[\d+\])?)(?:/|$)", xpath)
    return match.group(1) if match else None


def _xpath_sort_key(xpath: str) -> tuple[int, ...]:
    numbers = [int(value) for value in re.findall(r"\[(\d+)\]", xpath)]
    return tuple(numbers)


def _is_technical_attribute(node: SourceNode) -> bool:
    if node.attribute_name in {"id", "w:id", "r:id", "name", "w:val", "val"}:
        return True
    if node.attribute_name in {"Type", "TargetMode"}:
        return True
    return False


def _is_service_value(value: str) -> bool:
    if len(value) < 3 and not re.fullmatch(r"[ОOРP]", value):
        return True
    if re.fullmatch(r"\d+", value):
        return True
    return False


def _node_warnings(node: SourceNode, normalized_text: str) -> list[str]:
    warnings: list[str] = []
    if node.value_type == "aggregate":
        warnings.append(
            "Derived aggregate source node used; verify direct source nodes if behavior is critical."
        )
    if "tracked_delete" in node.flags:
        warnings.append("Tracked deletion text; may represent removed requirement.")
    if "hidden_text" in node.flags:
        warnings.append("Hidden text source node; verify whether it is intended requirement text.")
    if "comment" in node.flags:
        warnings.append("Comment source node; not treated as active requirement by default.")
    if "custom_xml" in node.flags:
        warnings.append("customXml source node; verify whether it is intended requirement text.")
    if "footnote" in node.flags:
        warnings.append("Footnote source node; verify traceability before using as requirement.")
    if "endnote" in node.flags:
        warnings.append("Endnote source node; verify traceability before using as requirement.")
    if "docprop" in node.flags:
        warnings.append("Document property source node; treated as metadata unless manually promoted.")
    if _is_single_letter_table_marker(normalized_text) and not _has_row_header_context(node.flags):
        warnings.append(SINGLE_LETTER_TABLE_MARKER_WARNING)
    if node.aggregate_warning and node.aggregate_warning not in warnings:
        warnings.append(node.aggregate_warning)
    return warnings


def _entry_status(
    node: SourceNode,
    requirement_type: str,
    normalized_text: str,
) -> RequirementStatus:
    flags = set(node.flags)
    if "tracked_delete" in flags:
        return "source_only"
    if "comment" in flags or "docprop" in flags:
        return "source_only"
    if requirement_type == "metadata/source_only":
        if _looks_like_unclear_requirement(normalized_text):
            return "unclear"
        return "source_only"
    if _is_single_letter_table_marker(normalized_text) and not _has_row_header_context(node.flags):
        return "unclear"
    if not _has_expected_behavior_signal(normalized_text, requirement_type):
        return "unclear"
    return "active"


def _entry_confidence(
    node: SourceNode,
    requirement_type: str,
    status: RequirementStatus,
) -> RequirementConfidence:
    if status in {"source_only", "unclear", "gap"}:
        return "low"
    if node.value_type == "aggregate":
        return "medium"
    if set(node.flags) & SERVICE_FLAG_NAMES:
        return "medium"
    if requirement_type == "metadata/source_only":
        return "low"
    return "medium"


def _detect_requirement_type(text: str, flags: tuple[str, ...] | list[str] = ()) -> str:
    folded = text.casefold()
    if "обязател" in folded or "required" in folded:
        return "requiredness"
    if _is_requiredness_marker(text, flags):
        return "requiredness"
    if any(token in folded for token in ["отображ", "видим", "скрыт", "показыв"]):
        return "visibility"
    if "редакт" in folded or "доступно для редактирования" in folded:
        return "editability"
    if _is_editability_marker(text, flags):
        return "editability"
    if any(token in folded for token in ["не принимает", "недопуст", "только", "формат", "маска", "длина"]):
        return "validation"
    if any(token in folded for token in ["справочник", "значения", "перечень", "dict"]):
        return "dictionary"
    if any(token in folded for token in ["кнопка", "переход", "нажать", "действие"]):
        return "navigation/action"
    if any(token in folded for token in ["расчет", "вычисляется", "формула"]):
        return "calculation"
    if any(token in folded for token in ["печатная форма", "pdf", "шаблон", "тег"]):
        return "generated_document"
    return "metadata/source_only"


def _detect_source_req_id(text: str) -> str | None:
    match = SOURCE_REQ_ID_RE.search(text)
    if not match:
        return None
    return WHITESPACE_RE.sub(" ", match.group(0).upper().replace("-", "-")).strip()


def _detect_section_id(text: str) -> str | None:
    match = SECTION_ID_RE.match(text)
    if not match:
        return None
    return match.group(1)


def _has_expected_behavior_signal(text: str, requirement_type: str) -> bool:
    if requirement_type == "metadata/source_only":
        return False
    if re.fullmatch(r"[ОOРP]", text):
        return False
    if len(text) < 4:
        return False
    return True


def _is_requiredness_marker(text: str, flags: tuple[str, ...] | list[str]) -> bool:
    return _is_marker_text(text, "ОO") or (_has_table_context(flags) and _is_marker_text(text, "ОO"))


def _is_editability_marker(text: str, flags: tuple[str, ...] | list[str]) -> bool:
    return _is_marker_text(text, "РP") or (_has_table_context(flags) and _is_marker_text(text, "РP"))


def _is_single_letter_table_marker(text: str) -> bool:
    return bool(re.fullmatch(r"[ОOРP]", _normalize_text(text)))


def _is_marker_text(text: str, letters: str) -> bool:
    return bool(re.fullmatch(f"[{letters}]", _normalize_text(text), re.IGNORECASE))


def _has_table_context(flags: tuple[str, ...] | list[str]) -> bool:
    return "table" in set(flags)


def _has_row_header_context(flags: tuple[str, ...] | list[str]) -> bool:
    return bool(set(flags) & {"table_header", "header_row", "row_header", "table_row_header"})


def _looks_like_unclear_requirement(text: str) -> bool:
    folded = text.casefold()
    return any(token in folded for token in ["уточнить", "todo", "tbd", "неясно", "вопрос"])


def _semantic_fingerprint(
    *,
    requirement_type: str,
    object_value: str | None,
    condition: str | None,
    expected_behavior: str | None,
    normalized_text: str,
    context_text: str | None = None,
) -> str:
    values = [
        requirement_type,
        object_value or "",
        condition or "",
        expected_behavior or normalized_text,
        context_text or "",
    ]
    return "|".join(_normalize_text(value).casefold() for value in values)


def _manifest_blocking_reasons(
    manifest: SourceManifest,
    source_manifest_path: Path,
) -> list[str]:
    blockers: list[str] = []
    if manifest.ingestion_status == "blocked":
        blockers.append("source manifest ingestion_status is blocked.")
        blockers.extend(manifest.blocking_reasons)
    clean_run_status = str(manifest.clean_run_audit.get("clean_run_status") or "unknown")
    if clean_run_status != "clean":
        blockers.append(
            f"source manifest clean_run_status is {clean_run_status}; requirements registry extraction is blocked."
        )
    if not manifest.coverage_audit_created:
        blockers.append("source manifest did not create coverage audit.")
    if not manifest.primary_docx:
        blockers.append("source manifest primary_docx is missing.")
    if not manifest.ooxml_coverage_audit_path:
        blockers.append("source manifest ooxml_coverage_audit_path is missing.")
    if not source_manifest_path.is_file():
        blockers.append(f"source manifest is not a file: {source_manifest_path}")
    return blockers


def _required_file_blockers(coverage_path: Path, primary_docx: Path) -> list[str]:
    blockers: list[str] = []
    if not coverage_path.exists():
        blockers.append(f"coverage audit file is missing: {coverage_path}")
    if not primary_docx.exists():
        blockers.append(f"primary DOCX file is missing: {primary_docx}")
    return blockers


def _read_coverage_audit_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Coverage audit root must be a JSON object.")
    return payload


def _registry_warnings(
    manifest: SourceManifest,
    entries: list[RequirementRegistryEntry],
) -> list[str]:
    warnings = list(manifest.warnings)
    if manifest.ingestion_status == "pass-with-warnings":
        warnings.append("Source manifest ingestion_status=pass-with-warnings; review registry warnings before use.")
    for entry in entries:
        warnings.extend(entry.warnings)
    if _duplicate_req_uids(entries):
        warnings.append(DUPLICATE_REQ_UID_WARNING)
    return sorted(set(warnings))


def _blocked_registry(
    *,
    source_manifest_path: Path,
    source_manifest_sha256: str | None,
    coverage_audit_path: str | None,
    ft_slug: str,
    source_version: str,
    created_by_tool: str,
    blocking_reasons: list[str],
    warnings: list[str] | None = None,
) -> RequirementRegistry:
    warnings = list(warnings or [])
    extraction_summary = _extraction_summary(
        manifest=None,
        entries=[],
        candidates_seen=0,
        source_manifest_path=source_manifest_path,
        registry_path=None,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        ft_slug=ft_slug,
        source_version=source_version,
        source_manifest_sha256=source_manifest_sha256,
        coverage_audit_path=coverage_audit_path,
        created_by_tool=created_by_tool,
    )
    return RequirementRegistry(
        ft_slug=ft_slug,
        source_version=source_version,
        registry_version=REGISTRY_VERSION,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        source_manifest_path=str(source_manifest_path),
        source_manifest_sha256=source_manifest_sha256,
        coverage_audit_path=coverage_audit_path,
        entries=[],
        extraction_summary=extraction_summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def _extraction_summary(
    *,
    manifest: SourceManifest | None,
    entries: list[RequirementRegistryEntry],
    candidates_seen: int,
    source_manifest_path: Path,
    registry_path: Path | None,
    warnings: list[str],
    blocking_reasons: list[str],
    ft_slug: str | None = None,
    source_version: str | None = None,
    source_manifest_sha256: str | None = None,
    coverage_audit_path: str | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> dict[str, Any]:
    status_counts = Counter(entry.status for entry in entries)
    by_requirement_type = Counter(entry.requirement_type for entry in entries)
    duplicate_req_uids = _duplicate_req_uids(entries)
    duplicate_req_uid_diff_eligible = _duplicate_req_uids(
        [entry for entry in entries if entry.diff_eligible]
    )
    duplicate_req_uid_source_only = _duplicate_req_uids(
        [entry for entry in entries if not entry.diff_eligible]
    )
    duplicate_entry_uids = _duplicate_entry_uids(entries)
    diff_eligible_entries = sum(1 for entry in entries if entry.diff_eligible)
    diff_excluded_entries = len(entries) - diff_eligible_entries
    context_filled_count = sum(1 for entry in entries if entry.diff_eligible and entry.context_text)
    context_missing_entries = [
        entry for entry in entries if entry.diff_eligible and not entry.context_text
    ]
    context_sources = Counter(
        entry.context_source or "none"
        for entry in entries
        if entry.diff_eligible
    )
    top_context_missing_requirement_types = Counter(
        entry.requirement_type for entry in context_missing_entries
    )
    summary_warnings = list(warnings)
    if duplicate_req_uids and DUPLICATE_REQ_UID_WARNING not in summary_warnings:
        summary_warnings.append(DUPLICATE_REQ_UID_WARNING)
    by_part = Counter(
        anchor.part
        for entry in entries
        for anchor in entry.source_anchors
    )
    summary_blocking_reasons = list(blocking_reasons)
    if duplicate_entry_uids:
        summary_blocking_reasons.append("Duplicate entry_uid values detected; registry row identity is not unique.")
    registry_status: RegistryStatus
    if summary_blocking_reasons:
        registry_status = "blocked"
    elif summary_warnings:
        registry_status = "pass-with-warnings"
    else:
        registry_status = "pass"
    return {
        "ft_slug": ft_slug or (manifest.ft_slug if manifest else "unknown"),
        "source_version": source_version or (manifest.source_version if manifest else "unknown"),
        "registry_version": REGISTRY_VERSION,
        "created_at_utc": _utc_now_iso(),
        "created_by_tool": created_by_tool,
        "source_manifest_path": str(source_manifest_path),
        "source_manifest_sha256": source_manifest_sha256
        if source_manifest_sha256 is not None
        else (compute_file_sha256(source_manifest_path) if source_manifest_path.exists() else None),
        "coverage_audit_path": coverage_audit_path
        if coverage_audit_path is not None
        else (manifest.ooxml_coverage_audit_path if manifest else None),
        "registry_path": str(registry_path) if registry_path else None,
        "registry_status": registry_status,
        "entries_total": len(entries),
        "diff_eligible_entries": diff_eligible_entries,
        "diff_excluded_entries": diff_excluded_entries,
        "active": status_counts.get("active", 0),
        "gap": status_counts.get("gap", 0),
        "unclear": status_counts.get("unclear", 0),
        "source_only": status_counts.get("source_only", 0),
        "by_requirement_type": dict(sorted(by_requirement_type.items())),
        "by_part": dict(sorted(by_part.items())),
        "duplicate_req_uid_count": len(duplicate_req_uids),
        "duplicate_req_uids": duplicate_req_uids,
        "duplicate_req_uid_diff_eligible_count": len(duplicate_req_uid_diff_eligible),
        "duplicate_req_uid_diff_eligible_uids": duplicate_req_uid_diff_eligible,
        "duplicate_req_uid_diff_eligible_count_after_context": len(duplicate_req_uid_diff_eligible),
        "duplicate_req_uid_source_only_count": len(duplicate_req_uid_source_only),
        "duplicate_req_uid_source_only_uids": duplicate_req_uid_source_only,
        "duplicate_entry_uid_count": len(duplicate_entry_uids),
        "duplicate_entry_uids": duplicate_entry_uids,
        "context_filled_count": context_filled_count,
        "context_missing_count": len(context_missing_entries),
        "context_sources": dict(sorted(context_sources.items())),
        "top_context_missing_requirement_types": dict(
            top_context_missing_requirement_types.most_common(10)
        ),
        "source_nodes_seen": candidates_seen,
        "warnings": summary_warnings,
        "blocking_reasons": summary_blocking_reasons,
    }


def _duplicate_req_uids(entries: list[RequirementRegistryEntry]) -> list[str]:
    counts = Counter(entry.req_uid for entry in entries)
    return sorted(req_uid for req_uid, count in counts.items() if count > 1)


def _duplicate_entry_uids(entries: list[RequirementRegistryEntry]) -> list[str]:
    counts = Counter(entry.entry_uid for entry in entries)
    return sorted(entry_uid for entry_uid, count in counts.items() if count > 1)


def _is_diff_eligible_status(status: str) -> bool:
    return status in {"active", "gap", "unclear"}


def _registry_path(out_dir: Path, source_version: str) -> Path:
    return Path(out_dir) / f"{REQUIREMENTS_PREFIX}.{source_version}.jsonl"


def _summary_path(out_dir: Path, source_version: str) -> Path:
    return Path(out_dir) / f"{REQUIREMENTS_SUMMARY_PREFIX}.{source_version}.json"


def _infer_summary_path(registry_path: Path) -> Path:
    name = registry_path.name
    if name.startswith(f"{REQUIREMENTS_PREFIX}.") and name.endswith(".jsonl"):
        source_version = name[len(f"{REQUIREMENTS_PREFIX}.") : -len(".jsonl")]
        return registry_path.with_name(f"{REQUIREMENTS_SUMMARY_PREFIX}.{source_version}.json")
    return registry_path.with_name(f"{registry_path.stem}-summary.json")


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return WHITESPACE_RE.sub(" ", value).strip()


def _uid_slug(ft_slug: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "", ft_slug).upper()
    return slug or "FT"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
