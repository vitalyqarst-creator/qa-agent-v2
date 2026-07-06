from __future__ import annotations

import posixpath
import re
import zipfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Literal

from lxml import etree

ValueType = Literal["text", "tail", "attribute", "aggregate"]

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NS_PREFIXES = {
    W_NS: "w",
    R_NS: "r",
    WP_NS: "wp",
    PKG_REL_NS: "rel",
}

WHITESPACE_RE = re.compile(r"\s+")
EXTRACTION_METHOD = "native_ooxml_zip_lxml"
PARSER_MODE_STRICT = "strict"
PARSER_MODE_TOLERANT = "tolerant"


@dataclass(frozen=True)
class SourceNode:
    node_id: str
    source_path: str
    part: str
    xpath: str
    node_type: str
    value_type: ValueType
    value: str
    attribute_name: str | None = None
    relationship_id: str | None = None
    target_part: str | None = None
    target_url: str | None = None
    flags: tuple[str, ...] = ()
    aggregate_kind: str | None = None
    aggregate_confidence: str | None = None
    aggregate_warning: str | None = None

    @property
    def text(self) -> str:
        return self.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "source_path": self.source_path,
            "part": self.part,
            "xpath": self.xpath,
            "node_type": self.node_type,
            "value_type": self.value_type,
            "text": self.value,
            "value": self.value,
            "attribute_name": self.attribute_name,
            "relationship_id": self.relationship_id,
            "target_part": self.target_part,
            "target_url": self.target_url,
            "flags": list(self.flags),
            "aggregate_kind": self.aggregate_kind,
            "aggregate_confidence": self.aggregate_confidence,
            "aggregate_warning": self.aggregate_warning,
        }


@dataclass(frozen=True)
class OoxmlCoverageAudit:
    source_path: str
    zip_entries_seen: list[str]
    xml_parts_seen: list[str]
    xml_parts_extracted: list[str]
    rels_parts_extracted: list[str]
    binary_parts_seen: list[str]
    binary_parts_extracted: list[str]
    extraction_warnings: list[str]
    comments_count: int
    footnotes_count: int
    endnotes_count: int
    headers_count: int
    footers_count: int
    hyperlinks_count: int
    images_count: int
    hidden_text_count: int
    tracked_insert_count: int
    tracked_delete_count: int
    textboxes_count: int
    custom_xml_parts_count: int
    parser_mode: str
    extraction_method: str = EXTRACTION_METHOD

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "zip_entries_seen": self.zip_entries_seen,
            "xml_parts_seen": self.xml_parts_seen,
            "xml_parts_extracted": self.xml_parts_extracted,
            "rels_parts_extracted": self.rels_parts_extracted,
            "binary_parts_seen": self.binary_parts_seen,
            "binary_parts_extracted": self.binary_parts_extracted,
            "extraction_warnings": self.extraction_warnings,
            "comments_count": self.comments_count,
            "footnotes_count": self.footnotes_count,
            "endnotes_count": self.endnotes_count,
            "headers_count": self.headers_count,
            "footers_count": self.footers_count,
            "hyperlinks_count": self.hyperlinks_count,
            "images_count": self.images_count,
            "hidden_text_count": self.hidden_text_count,
            "tracked_insert_count": self.tracked_insert_count,
            "tracked_delete_count": self.tracked_delete_count,
            "textboxes_count": self.textboxes_count,
            "custom_xml_parts_count": self.custom_xml_parts_count,
            "parser_mode": self.parser_mode,
            "extraction_method": self.extraction_method,
        }


@dataclass(frozen=True)
class OoxmlSource:
    source_path: str
    source_nodes: list[SourceNode]
    coverage_audit: OoxmlCoverageAudit
    relationships_by_part: dict[str, dict[str, "RelationshipTarget"]] = field(default_factory=dict)

    @property
    def nodes(self) -> list[SourceNode]:
        return self.source_nodes

    @property
    def coverage(self) -> OoxmlCoverageAudit:
        return self.coverage_audit

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "coverage_audit": self.coverage_audit.to_dict(),
            "source_nodes": [node.to_dict() for node in self.source_nodes],
        }


@dataclass(frozen=True)
class RelationshipTarget:
    relationship_id: str
    relationship_type: str | None
    target: str
    target_mode: str | None
    target_part: str | None = None
    target_url: str | None = None


@dataclass(frozen=True)
class OOXMLTableCellContext:
    source_path: str
    source_version: str | None
    part: str
    table_index: int | None
    row_index: int | None
    column_index: int | None
    cell_text: str | None
    row_cells: list[str]
    header_cells: list[str]
    previous_row_cells: list[str]
    next_row_cells: list[str]
    table_caption: str | None
    table_heading_context: str | None
    xpath: str
    node_id: str | None
    confidence: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_version": self.source_version,
            "part": self.part,
            "table_index": self.table_index,
            "row_index": self.row_index,
            "column_index": self.column_index,
            "cell_text": self.cell_text,
            "row_cells": self.row_cells,
            "header_cells": self.header_cells,
            "previous_row_cells": self.previous_row_cells,
            "next_row_cells": self.next_row_cells,
            "table_caption": self.table_caption,
            "table_heading_context": self.table_heading_context,
            "xpath": self.xpath,
            "node_id": self.node_id,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OOXMLTableCellContext":
        return cls(
            source_path=str(data["source_path"]),
            source_version=data.get("source_version"),
            part=str(data["part"]),
            table_index=_optional_int(data.get("table_index")),
            row_index=_optional_int(data.get("row_index")),
            column_index=_optional_int(data.get("column_index")),
            cell_text=data.get("cell_text"),
            row_cells=list(data.get("row_cells") or []),
            header_cells=list(data.get("header_cells") or []),
            previous_row_cells=list(data.get("previous_row_cells") or []),
            next_row_cells=list(data.get("next_row_cells") or []),
            table_caption=data.get("table_caption"),
            table_heading_context=data.get("table_heading_context"),
            xpath=str(data.get("xpath") or ""),
            node_id=data.get("node_id"),
            confidence=str(data.get("confidence") or "low"),
            warnings=list(data.get("warnings") or []),
        )


def load_ooxml_source(source: Path, *, parser_mode: str = PARSER_MODE_STRICT) -> OoxmlSource:
    source = Path(source)
    if parser_mode not in {PARSER_MODE_STRICT, PARSER_MODE_TOLERANT}:
        raise ValueError(f"Unsupported OOXML parser mode: {parser_mode}")

    parsed_parts: dict[str, etree._Element] = {}
    warnings: list[str] = []
    with zipfile.ZipFile(source) as archive:
        zip_infos = [info for info in archive.infolist() if not info.is_dir()]
        zip_entries_seen = sorted(info.filename for info in zip_infos)
        xml_parts_seen = sorted(name for name in zip_entries_seen if _is_xml_part(name))
        rels_parts_seen = sorted(name for name in zip_entries_seen if _is_rels_part(name))
        binary_parts_seen = sorted(
            name for name in zip_entries_seen if not _is_xml_part(name) and not _is_rels_part(name)
        )

        if parser_mode == PARSER_MODE_TOLERANT:
            warnings.append("Tolerant OOXML XML parser mode enabled: recover=True")

        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            recover=parser_mode == PARSER_MODE_TOLERANT,
        )

        for part in [*xml_parts_seen, *rels_parts_seen]:
            try:
                parsed_parts[part] = etree.fromstring(archive.read(part), parser=parser)
            except etree.XMLSyntaxError as exc:
                warnings.append(f"XML part not extracted: {part}: {exc}")

    xml_parts_extracted = sorted(part for part in parsed_parts if _is_xml_part(part))
    rels_parts_extracted = sorted(part for part in parsed_parts if _is_rels_part(part))

    for part in binary_parts_seen:
        warnings.append(f"Binary part seen but not content-extracted: {part}")

    relationships_by_part = _build_relationships(parsed_parts)
    list_style_ids = _list_style_ids(parsed_parts.get("word/styles.xml"))
    source_nodes = _extract_source_nodes(source, parsed_parts, relationships_by_part, list_style_ids)
    coverage_audit = _build_coverage_audit(
        source=source,
        zip_entries_seen=zip_entries_seen,
        xml_parts_seen=xml_parts_seen,
        xml_parts_extracted=xml_parts_extracted,
        rels_parts_extracted=rels_parts_extracted,
        binary_parts_seen=binary_parts_seen,
        warnings=warnings,
        parser_mode=parser_mode,
        parsed_parts=parsed_parts,
        source_nodes=source_nodes,
    )
    return OoxmlSource(
        source_path=str(source),
        source_nodes=source_nodes,
        coverage_audit=coverage_audit,
        relationships_by_part=relationships_by_part,
    )


def inspect_ooxml_coverage(source: Path) -> OoxmlCoverageAudit:
    return load_ooxml_source(source).coverage_audit


def extract_ooxml_source_nodes(source: Path) -> list[SourceNode]:
    return load_ooxml_source(source).source_nodes


def table_context_from_anchor(
    *,
    source_path: str | Path,
    part: str,
    xpath: str,
    source_version: str | None = None,
    node_id: str | None = None,
) -> OOXMLTableCellContext:
    source = Path(source_path)
    warnings: list[str] = []
    table_index = _xpath_index(xpath, "tbl")
    row_index = _xpath_index(xpath, "tr")
    column_index = _xpath_index(xpath, "tc")
    if table_index is None:
        warnings.append("source anchor xpath does not contain w:tbl[n].")
    if row_index is None:
        warnings.append("source anchor xpath does not contain w:tr[n].")
    if column_index is None:
        warnings.append("source anchor xpath does not contain w:tc[n].")
    if not source.exists():
        warnings.append(f"OOXML source document is missing: {source}")
        return _empty_table_cell_context(source, part, xpath, source_version, node_id, table_index, row_index, column_index, warnings)
    try:
        tables = _table_structures(str(source), part)
    except Exception as exc:  # noqa: BLE001 - caller needs diagnostic warning, not exception.
        warnings.append(f"OOXML table context cannot be extracted: {exc}")
        return _empty_table_cell_context(source, part, xpath, source_version, node_id, table_index, row_index, column_index, warnings)
    if table_index is None or row_index is None:
        return _empty_table_cell_context(source, part, xpath, source_version, node_id, table_index, row_index, column_index, warnings)
    if table_index < 1 or table_index > len(tables):
        warnings.append(f"table index out of range: {table_index}")
        return _empty_table_cell_context(source, part, xpath, source_version, node_id, table_index, row_index, column_index, warnings)
    table = tables[table_index - 1]
    rows: list[list[str]] = table["rows"]
    if row_index < 1 or row_index > len(rows):
        warnings.append(f"row index out of range: {row_index}")
        return _empty_table_cell_context(source, part, xpath, source_version, node_id, table_index, row_index, column_index, warnings)
    row_cells = rows[row_index - 1]
    cell_text = None
    if column_index is not None:
        if 1 <= column_index <= len(row_cells):
            cell_text = row_cells[column_index - 1] or None
        else:
            warnings.append(f"column index out of range: {column_index}")
    header_cells: list[str] = []
    if row_index > 1 and rows and any(rows[0]) and rows[0] != row_cells:
        header_cells = rows[0]
    else:
        warnings.append("header row not available or not distinguishable from data row.")
    previous_row_cells = rows[row_index - 2] if row_index > 1 else []
    next_row_cells = rows[row_index] if row_index < len(rows) else []
    confidence = "high" if row_cells and header_cells and cell_text else "medium" if row_cells else "low"
    return OOXMLTableCellContext(
        source_path=str(source),
        source_version=source_version,
        part=part,
        table_index=table_index,
        row_index=row_index,
        column_index=column_index,
        cell_text=cell_text,
        row_cells=row_cells,
        header_cells=header_cells,
        previous_row_cells=previous_row_cells,
        next_row_cells=next_row_cells,
        table_caption=table.get("caption"),
        table_heading_context=table.get("heading_context"),
        xpath=xpath,
        node_id=node_id,
        confidence=confidence,
        warnings=warnings,
    )


def _build_relationships(
    parsed_parts: dict[str, etree._Element],
) -> dict[str, dict[str, RelationshipTarget]]:
    relationships_by_part: dict[str, dict[str, RelationshipTarget]] = {}
    for rels_part, root in parsed_parts.items():
        if not _is_rels_part(rels_part):
            continue
        source_part = _source_part_for_rels(rels_part)
        relationships_by_part.setdefault(source_part, {})
        for element in root.iter():
            if _local_name(element.tag) != "Relationship":
                continue
            relationship_id = element.get("Id")
            target = element.get("Target")
            if not relationship_id or not target:
                continue
            target_mode = element.get("TargetMode")
            target_part = None
            target_url = None
            if target_mode == "External":
                target_url = target
            else:
                target_part = _resolve_relationship_target(source_part, target)
            relationships_by_part[source_part][relationship_id] = RelationshipTarget(
                relationship_id=relationship_id,
                relationship_type=element.get("Type"),
                target=target,
                target_mode=target_mode,
                target_part=target_part,
                target_url=target_url,
            )
    return relationships_by_part


@lru_cache(maxsize=32)
def _table_structures(source_path: str, part: str) -> tuple[dict[str, Any], ...]:
    source = Path(source_path)
    parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
    with zipfile.ZipFile(source) as archive:
        root = etree.fromstring(archive.read(part), parser=parser)
    tables: list[dict[str, Any]] = []
    preceding_paragraphs: list[str] = []
    for element in root.iter():
        if _is_w(element, "p"):
            text = _aggregate_text(element)
            if text:
                preceding_paragraphs.append(text)
                preceding_paragraphs = preceding_paragraphs[-5:]
            continue
        if not _is_w(element, "tbl"):
            continue
        rows: list[list[str]] = []
        for row in element:
            if not _is_w(row, "tr"):
                continue
            cells: list[str] = []
            for cell in row:
                if _is_w(cell, "tc"):
                    cells.append(_aggregate_text(cell))
            if any(cells):
                rows.append(cells)
        heading_context = _last_meaningful(preceding_paragraphs)
        tables.append(
            {
                "rows": rows,
                "caption": heading_context,
                "heading_context": heading_context,
            }
        )
    return tuple(tables)


def _empty_table_cell_context(
    source: Path,
    part: str,
    xpath: str,
    source_version: str | None,
    node_id: str | None,
    table_index: int | None,
    row_index: int | None,
    column_index: int | None,
    warnings: list[str],
) -> OOXMLTableCellContext:
    return OOXMLTableCellContext(
        source_path=str(source),
        source_version=source_version,
        part=part,
        table_index=table_index,
        row_index=row_index,
        column_index=column_index,
        cell_text=None,
        row_cells=[],
        header_cells=[],
        previous_row_cells=[],
        next_row_cells=[],
        table_caption=None,
        table_heading_context=None,
        xpath=xpath,
        node_id=node_id,
        confidence="low",
        warnings=warnings,
    )


def _xpath_index(xpath: str, tag: str) -> int | None:
    match = re.search(rf"w:{re.escape(tag)}\[(\d+)\]", xpath)
    if not match:
        return None
    return int(match.group(1))


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _last_meaningful(values: list[str]) -> str | None:
    for value in reversed(values):
        if value and len(value) > 2:
            return value
    return None


def _extract_source_nodes(
    source: Path,
    parsed_parts: dict[str, etree._Element],
    relationships_by_part: dict[str, dict[str, RelationshipTarget]],
    list_style_ids: set[str],
) -> list[SourceNode]:
    nodes: list[SourceNode] = []
    source_path = str(source)

    def add_node(
        *,
        part: str,
        element: etree._Element,
        xpath: str,
        node_type: str,
        value_type: ValueType,
        value: str | None,
        attribute_name: str | None = None,
        relationship_id: str | None = None,
        target_part: str | None = None,
        target_url: str | None = None,
        flags: set[str] | None = None,
        aggregate_kind: str | None = None,
        aggregate_confidence: str | None = None,
        aggregate_warning: str | None = None,
    ) -> None:
        normalized = _normalize_text(value)
        if not normalized:
            return
        node_id = f"ooxml-node-{len(nodes) + 1:06d}"
        nodes.append(
            SourceNode(
                node_id=node_id,
                source_path=source_path,
                part=part,
                xpath=xpath,
                node_type=node_type,
                value_type=value_type,
                value=normalized,
                attribute_name=attribute_name,
                relationship_id=relationship_id,
                target_part=target_part,
                target_url=target_url,
                flags=tuple(sorted(flags or set())),
                aggregate_kind=aggregate_kind,
                aggregate_confidence=aggregate_confidence,
                aggregate_warning=aggregate_warning,
            )
        )

    for part, root in sorted(parsed_parts.items()):
        tree = root.getroottree()
        for element in root.iter():
            xpath = _safe_xpath(tree, element)
            node_type = _local_name(element.tag)
            base_flags = _flags_for_element(part, element, list_style_ids)

            relationship_id, target_part, target_url = _relationship_context(
                part,
                element,
                None,
                relationships_by_part,
            )

            add_node(
                part=part,
                element=element,
                xpath=f"{xpath}/text()",
                node_type=node_type,
                value_type="text",
                value=element.text,
                relationship_id=relationship_id,
                target_part=target_part,
                target_url=target_url,
                flags=base_flags,
            )
            add_node(
                part=part,
                element=element,
                xpath=f"{xpath}/tail()",
                node_type=node_type,
                value_type="tail",
                value=element.tail,
                relationship_id=relationship_id,
                target_part=target_part,
                target_url=target_url,
                flags=base_flags,
            )

            for attribute_key, attribute_value in sorted(element.attrib.items()):
                attribute_name = _display_qname(attribute_key)
                attr_relationship_id, attr_target_part, attr_target_url = _relationship_context(
                    part,
                    element,
                    attribute_key,
                    relationships_by_part,
                )
                attr_flags = set(base_flags)
                if _local_name(element.tag) == "Relationship":
                    attr_relationship_id = element.get("Id")
                    if attribute_name == "Target":
                        target = _relationship_target_for_element(part, element)
                        attr_target_part = target.target_part if target else None
                        attr_target_url = target.target_url if target else None
                if _local_name(element.tag) == "docPr" and attribute_name in {"descr", "title"}:
                    attr_flags.add("image_alt_or_title")
                if attr_target_url or _relationship_type_contains(element, "hyperlink"):
                    attr_flags.add("hyperlink")

                add_node(
                    part=part,
                    element=element,
                    xpath=f"{xpath}/@{attribute_name}",
                    node_type=node_type,
                    value_type="attribute",
                    value=attribute_value,
                    attribute_name=attribute_name,
                    relationship_id=attr_relationship_id,
                    target_part=attr_target_part,
                    target_url=attr_target_url,
                    flags=attr_flags,
                )

            aggregate_kind = _aggregate_kind(element)
            if aggregate_kind is not None:
                aggregate_flags = set(base_flags)
                aggregate_node_type = aggregate_kind
                aggregate_relationship_id, aggregate_target_part, aggregate_target_url = _relationship_context(
                    part,
                    element,
                    None,
                    relationships_by_part,
                )
                if aggregate_kind == "hyperlink":
                    aggregate_flags.add("hyperlink")
                add_node(
                    part=part,
                    element=element,
                    xpath=f"{xpath}/aggregate::{aggregate_kind}",
                    node_type=aggregate_node_type,
                    value_type="aggregate",
                    value=_aggregate_text(element),
                    relationship_id=aggregate_relationship_id,
                    target_part=aggregate_target_part,
                    target_url=aggregate_target_url,
                    flags=aggregate_flags,
                    aggregate_kind=aggregate_kind,
                    aggregate_confidence="derived",
                    aggregate_warning=(
                        "Derived aggregate text may join distinct runs or tracked-change text; "
                        "prefer direct text and attribute nodes when possible."
                    ),
                )

    return nodes


def _build_coverage_audit(
    *,
    source: Path,
    zip_entries_seen: list[str],
    xml_parts_seen: list[str],
    xml_parts_extracted: list[str],
    rels_parts_extracted: list[str],
    binary_parts_seen: list[str],
    warnings: list[str],
    parser_mode: str,
    parsed_parts: dict[str, etree._Element],
    source_nodes: list[SourceNode],
) -> OoxmlCoverageAudit:
    comments_count = _count_elements(
        parsed_parts,
        lambda part, element: _is_comment_part(part) and _is_w(element, "comment"),
    )
    footnotes_count = _count_elements(
        parsed_parts,
        lambda part, element: part == "word/footnotes.xml" and _is_w(element, "footnote"),
    )
    endnotes_count = _count_elements(
        parsed_parts,
        lambda part, element: part == "word/endnotes.xml" and _is_w(element, "endnote"),
    )
    return OoxmlCoverageAudit(
        source_path=str(source),
        zip_entries_seen=zip_entries_seen,
        xml_parts_seen=xml_parts_seen,
        xml_parts_extracted=xml_parts_extracted,
        rels_parts_extracted=rels_parts_extracted,
        binary_parts_seen=binary_parts_seen,
        binary_parts_extracted=[],
        extraction_warnings=warnings,
        comments_count=comments_count,
        footnotes_count=footnotes_count,
        endnotes_count=endnotes_count,
        headers_count=sum(1 for part in xml_parts_extracted if _is_header_part(part)),
        footers_count=sum(1 for part in xml_parts_extracted if _is_footer_part(part)),
        hyperlinks_count=_count_elements(parsed_parts, lambda _part, element: _is_w(element, "hyperlink")),
        images_count=_count_elements(parsed_parts, lambda _part, element: _local_name(element.tag) == "docPr"),
        hidden_text_count=_count_flag(source_nodes, "hidden_text"),
        tracked_insert_count=_count_elements(parsed_parts, lambda _part, element: _is_w(element, "ins")),
        tracked_delete_count=_count_elements(parsed_parts, lambda _part, element: _is_w(element, "del")),
        textboxes_count=_count_elements(parsed_parts, lambda _part, element: _is_w(element, "txbxContent")),
        custom_xml_parts_count=sum(1 for part in xml_parts_extracted if part.startswith("customXml/")),
        parser_mode=parser_mode,
    )


def _is_xml_part(part: str) -> bool:
    return part.endswith(".xml")


def _is_rels_part(part: str) -> bool:
    return part.endswith(".rels")


def _is_header_part(part: str) -> bool:
    return bool(re.fullmatch(r"word/header[^/]*\.xml", part))


def _is_footer_part(part: str) -> bool:
    return bool(re.fullmatch(r"word/footer[^/]*\.xml", part))


def _is_comment_part(part: str) -> bool:
    return bool(re.fullmatch(r"word/comments[^/]*\.xml", part))


def _source_part_for_rels(rels_part: str) -> str:
    if rels_part == "_rels/.rels":
        return ""
    marker = "/_rels/"
    if marker not in rels_part:
        return ""
    prefix, filename = rels_part.split(marker, 1)
    if filename.endswith(".rels"):
        filename = filename[: -len(".rels")]
    return f"{prefix}/{filename}" if prefix else filename


def _resolve_relationship_target(source_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    base = posixpath.dirname(source_part)
    if base:
        return posixpath.normpath(posixpath.join(base, target))
    return posixpath.normpath(target)


def _relationship_target_for_element(part: str, element: etree._Element) -> RelationshipTarget | None:
    if _local_name(element.tag) != "Relationship":
        return None
    relationship_id = element.get("Id")
    target = element.get("Target")
    if not relationship_id or not target:
        return None
    target_mode = element.get("TargetMode")
    if target_mode == "External":
        return RelationshipTarget(
            relationship_id=relationship_id,
            relationship_type=element.get("Type"),
            target=target,
            target_mode=target_mode,
            target_url=target,
        )
    return RelationshipTarget(
        relationship_id=relationship_id,
        relationship_type=element.get("Type"),
        target=target,
        target_mode=target_mode,
        target_part=_resolve_relationship_target(_source_part_for_rels(part), target),
    )


def _relationship_context(
    part: str,
    element: etree._Element,
    attribute_key: str | None,
    relationships_by_part: dict[str, dict[str, RelationshipTarget]],
) -> tuple[str | None, str | None, str | None]:
    relationship_id: str | None = None
    if attribute_key is not None and _namespace_uri(attribute_key) == R_NS and _local_name(attribute_key) == "id":
        relationship_id = element.get(attribute_key)
    else:
        hyperlink = _nearest_ancestor_or_self(element, W_NS, "hyperlink")
        if hyperlink is not None:
            relationship_id = hyperlink.get(f"{{{R_NS}}}id")

    if not relationship_id:
        return None, None, None

    target = relationships_by_part.get(part, {}).get(relationship_id)
    if target is None:
        return relationship_id, None, None
    return relationship_id, target.target_part, target.target_url


def _relationship_type_contains(element: etree._Element, token: str) -> bool:
    value = element.get("Type")
    return bool(value and token in value)


def _aggregate_kind(element: etree._Element) -> str | None:
    if _is_w(element, "p"):
        return "paragraph"
    if _is_w(element, "tc"):
        return "table_cell"
    if _is_w(element, "txbxContent"):
        return "textbox"
    if _is_w(element, "hyperlink"):
        return "hyperlink"
    return None


def _aggregate_text(element: etree._Element) -> str:
    return _normalize_text("".join(element.itertext()))


def _flags_for_element(part: str, element: etree._Element, list_style_ids: set[str]) -> set[str]:
    flags: set[str] = set()
    if _is_header_part(part):
        flags.add("header")
    if _is_footer_part(part):
        flags.add("footer")
    if part == "word/footnotes.xml":
        flags.add("footnote")
    if part == "word/endnotes.xml":
        flags.add("endnote")
    if _is_comment_part(part):
        flags.add("comment")
    if part.startswith("docProps/"):
        flags.add("docprop")
    if part.startswith("customXml/"):
        flags.add("custom_xml")
    if _has_ancestor_or_self(element, W_NS, "tbl") or _has_ancestor_or_self(element, W_NS, "tc"):
        flags.add("table")
    if _has_ancestor_or_self(element, W_NS, "txbxContent"):
        flags.add("textbox")
    if _has_ancestor_or_self(element, W_NS, "hyperlink"):
        flags.add("hyperlink")
    if _has_ancestor_or_self(element, W_NS, "ins"):
        flags.add("tracked_insert")
    if _has_ancestor_or_self(element, W_NS, "del") or _is_w(element, "delText"):
        flags.add("tracked_delete")
    if _is_hidden_text(element):
        flags.add("hidden_text")
    if _is_in_numbered_paragraph(element, list_style_ids):
        flags.add("list")
    return flags


def _is_hidden_text(element: etree._Element) -> bool:
    run = _nearest_ancestor_or_self(element, W_NS, "r")
    if run is None:
        return False
    for descendant in run.iterdescendants():
        if _is_w(descendant, "vanish") or _is_w(descendant, "specVanish"):
            return True
    return False


def _is_in_numbered_paragraph(element: etree._Element, list_style_ids: set[str]) -> bool:
    paragraph = _nearest_ancestor_or_self(element, W_NS, "p")
    if paragraph is None:
        return False
    for descendant in paragraph.iterdescendants():
        if _is_w(descendant, "numPr"):
            return True
    style_id = _paragraph_style_id(paragraph)
    if style_id and style_id in list_style_ids:
        return True
    return False


def _paragraph_style_id(paragraph: etree._Element) -> str | None:
    for descendant in paragraph.iterdescendants():
        if _is_w(descendant, "pStyle"):
            return descendant.get(f"{{{W_NS}}}val") or descendant.get("val")
    return None


def _list_style_ids(styles_root: etree._Element | None) -> set[str]:
    if styles_root is None:
        return set()
    style_ids: set[str] = set()
    for style in styles_root.iter():
        if not _is_w(style, "style"):
            continue
        if not any(_is_w(descendant, "numPr") for descendant in style.iterdescendants()):
            continue
        style_id = style.get(f"{{{W_NS}}}styleId") or style.get("styleId")
        if style_id:
            style_ids.add(style_id)
    return style_ids


def _has_ancestor_or_self(element: etree._Element, namespace: str, local_name: str) -> bool:
    return _nearest_ancestor_or_self(element, namespace, local_name) is not None


def _nearest_ancestor_or_self(
    element: etree._Element,
    namespace: str,
    local_name: str,
) -> etree._Element | None:
    current: etree._Element | None = element
    while current is not None:
        if _namespace_uri(current.tag) == namespace and _local_name(current.tag) == local_name:
            return current
        current = current.getparent()
    return None


def _count_elements(
    parsed_parts: dict[str, etree._Element],
    predicate: Callable[[str, etree._Element], bool],
) -> int:
    count = 0
    for part, root in parsed_parts.items():
        for element in root.iter():
            if predicate(part, element):
                count += 1
    return count


def _count_flag(source_nodes: list[SourceNode], flag: str) -> int:
    return sum(1 for node in source_nodes if flag in node.flags)


def _safe_xpath(tree: etree._ElementTree, element: etree._Element) -> str:
    try:
        return tree.getpath(element)
    except ValueError:
        return f"//{_local_name(element.tag)}"


def _is_w(element: etree._Element, local_name: str) -> bool:
    return _namespace_uri(element.tag) == W_NS and _local_name(element.tag) == local_name


def _namespace_uri(qname: str) -> str | None:
    if qname.startswith("{") and "}" in qname:
        return qname[1:].split("}", 1)[0]
    return None


def _local_name(qname: str) -> str:
    if qname.startswith("{") and "}" in qname:
        return qname.split("}", 1)[1]
    return qname


def _display_qname(qname: str) -> str:
    namespace = _namespace_uri(qname)
    local_name = _local_name(qname)
    prefix = NS_PREFIXES.get(namespace or "")
    if prefix:
        return f"{prefix}:{local_name}"
    return local_name


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return WHITESPACE_RE.sub(" ", value).strip()
