from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from docx.oxml.ns import qn
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from test_case_agent.document_loader import (
    detect_section_id,
    iter_block_items,
    normalize_text,
    paragraph_style_level,
)


SOURCE_JSON_PROJECTION_VERSION = 2
SUPPORTED_SOURCE_JSON_PROJECTION_VERSIONS = {1, SOURCE_JSON_PROJECTION_VERSION}
REQUIREMENT_CODE_RE = re.compile(
    r"\b(?:BSR|GSR|REQ|DIT)\s*[-]?\s*\d+(?:[A-Za-z0-9._/-]+)?\b",
    flags=re.IGNORECASE,
)


class SourceJsonProjectionError(ValueError):
    """A deterministic DOCX to source JSON projection violation."""


class _NumberingResolver:
    def __init__(self, document: Any):
        self._levels: dict[tuple[str, str], tuple[str, int]] = {}
        self._num_to_abstract: dict[str, str] = {}
        self._counters: dict[tuple[str, int], int] = {}
        numbering_part = getattr(document.part, "numbering_part", None)
        if numbering_part is None:
            return
        root = numbering_part.element
        for abstract in root.findall(qn("w:abstractNum")):
            abstract_id = abstract.get(qn("w:abstractNumId"))
            if not abstract_id:
                continue
            for level in abstract.findall(qn("w:lvl")):
                ilvl = level.get(qn("w:ilvl"))
                if ilvl is None:
                    continue
                lvl_text_node = level.find(qn("w:lvlText"))
                start_node = level.find(qn("w:start"))
                lvl_text = (
                    lvl_text_node.get(qn("w:val"))
                    if lvl_text_node is not None
                    else ""
                )
                start = 1
                if start_node is not None:
                    try:
                        start = int(start_node.get(qn("w:val")) or "1")
                    except ValueError:
                        start = 1
                if lvl_text:
                    self._levels[(abstract_id, ilvl)] = (lvl_text, start)
        for num in root.findall(qn("w:num")):
            num_id = num.get(qn("w:numId"))
            abstract_node = num.find(qn("w:abstractNumId"))
            abstract_id = (
                abstract_node.get(qn("w:val"))
                if abstract_node is not None
                else None
            )
            if num_id and abstract_id:
                self._num_to_abstract[num_id] = abstract_id

    @staticmethod
    def _paragraph_num_pr(paragraph: Paragraph) -> tuple[str, str] | None:
        p_pr = paragraph._p.pPr
        num_pr = p_pr.numPr if p_pr is not None else None
        if num_pr is None:
            style = paragraph.style
            style_element = style.element if style is not None else None
            style_p_pr = style_element.pPr if style_element is not None else None
            num_pr = style_p_pr.numPr if style_p_pr is not None else None
        if num_pr is None:
            return None
        num_id_node = num_pr.numId
        if num_id_node is None:
            return None
        num_id = num_id_node.val
        ilvl_node = num_pr.ilvl
        ilvl = ilvl_node.val if ilvl_node is not None else 0
        return str(num_id), str(ilvl)

    def prefix_for(self, paragraph: Paragraph) -> str:
        num_pr = self._paragraph_num_pr(paragraph)
        if num_pr is None:
            return ""
        num_id, ilvl = num_pr
        abstract_id = self._num_to_abstract.get(num_id)
        if abstract_id is None:
            return ""
        level = self._levels.get((abstract_id, ilvl))
        if level is None:
            return ""
        lvl_text, start = level
        level_index = int(ilvl)
        counter_key = (num_id, level_index)
        current = self._counters.get(counter_key, start - 1) + 1
        self._counters[counter_key] = current
        for lower_level in tuple(self._counters):
            if lower_level[0] == num_id and lower_level[1] > level_index:
                self._counters.pop(lower_level, None)
        label = lvl_text
        for index in range(1, 10):
            value = self._counters.get((num_id, index - 1), 0)
            label = label.replace(f"%{index}", str(value))
        return label.strip()


def _repository_relative_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    root = repo_root.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise SourceJsonProjectionError(
            f"source path must be under repo root: {path}"
        ) from exc
    return PurePosixPath(*relative.parts).as_posix()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _block_hash(block: Mapping[str, Any]) -> str:
    payload = {
        key: value
        for key, value in block.items()
        if key not in {"block_id", "block_hash"}
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _requirement_codes(text: str) -> list[str]:
    return list(
        dict.fromkeys(
            normalize_text(match.group(0)).upper()
            for match in REQUIREMENT_CODE_RE.finditer(text)
        )
    )


def _structural_hash(block: Mapping[str, Any]) -> str:
    payload = {
        "kind": block.get("kind"),
        "docx_locator": block.get("docx_locator"),
        "section_path": block.get("section_path"),
        "table_index": block.get("table_index"),
        "row_index": block.get("row_index"),
        "cell_indices": block.get("cell_indices"),
        "cell_merge_metadata": block.get("cell_merge_metadata"),
        "numbering_labels": block.get("numbering_labels"),
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _semantic_hash(block: Mapping[str, Any]) -> str:
    payload = {
        "section_path": block.get("section_path"),
        "text": block.get("text"),
        "requirement_codes": block.get("requirement_codes"),
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _paragraph_text_and_numbering(
    paragraph: Paragraph,
    numbering: _NumberingResolver,
) -> tuple[str, str]:
    prefix = numbering.prefix_for(paragraph)
    text = normalize_text(paragraph.text)
    if not text:
        return "", prefix
    if prefix and not text.startswith(prefix):
        return normalize_text(f"{prefix} {text}"), prefix
    return text, prefix


def _cell_text_with_numbering(
    cell: _Cell,
    numbering: _NumberingResolver,
) -> tuple[str, list[str]]:
    parts: list[str] = []
    labels: list[str] = []
    pending_prefix = ""
    for paragraph in cell.paragraphs:
        prefix = numbering.prefix_for(paragraph)
        text = normalize_text(paragraph.text)
        if not text:
            if prefix:
                pending_prefix = prefix
            continue
        if pending_prefix:
            if not text.startswith(pending_prefix):
                text = normalize_text(f"{pending_prefix} {text}")
            labels.append(pending_prefix)
            pending_prefix = ""
        elif prefix and not text.startswith(prefix):
            text = normalize_text(f"{prefix} {text}")
            labels.append(prefix)
        elif prefix:
            labels.append(prefix)
        parts.append(text)
    return normalize_text(" ".join(parts)), labels


def _cell_merge_metadata(tc: Any, *, cell_index: int) -> dict[str, Any]:
    tc_pr = tc.tcPr
    grid_span = 1
    vertical_merge = "none"
    if tc_pr is not None:
        grid_span_node = tc_pr.find(qn("w:gridSpan"))
        if grid_span_node is not None:
            try:
                grid_span = int(grid_span_node.get(qn("w:val")) or "1")
            except ValueError:
                grid_span = 1
        vertical_merge_node = tc_pr.find(qn("w:vMerge"))
        if vertical_merge_node is not None:
            vertical_merge = vertical_merge_node.get(qn("w:val")) or "continue"
    return {
        "cell_index": cell_index,
        "grid_span": grid_span,
        "vertical_merge": vertical_merge,
    }


def _table_row_cells(
    table: Table,
    row_index: int,
    numbering: _NumberingResolver,
    *,
    row_locator: str,
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    row = table.rows[row_index]
    cells: list[str] = []
    cell_blocks: list[dict[str, Any]] = []
    row_numbering_labels: list[str] = []
    for cell_index, tc in enumerate(row._tr.tc_lst, start=1):
        text, labels = _cell_text_with_numbering(_Cell(tc, table), numbering)
        cells.append(text)
        row_numbering_labels.extend(labels)
        merge_metadata = _cell_merge_metadata(tc, cell_index=cell_index)
        cell_blocks.append(
            {
                "kind": "cell",
                "cell_index": cell_index,
                "docx_locator": f"{row_locator}/w:tc[{cell_index}]",
                "text": text,
                "exact_text": text,
                "requirement_codes": _requirement_codes(text),
                "numbering_labels": labels,
                "merge_metadata": merge_metadata,
            }
        )
    return cells, cell_blocks, row_numbering_labels


def _append_block(
    blocks: list[dict[str, Any]],
    *,
    kind: str,
    text: str,
    section_path: Sequence[str],
    extra: Mapping[str, Any] | None = None,
) -> None:
    normalized = normalize_text(text)
    if not normalized:
        return
    index = len(blocks) + 1
    docx_locator = (
        str(extra.get("docx_locator"))
        if extra is not None and extra.get("docx_locator")
        else f"/blocks/{index}"
    )
    block: dict[str, Any] = {
        "block_id": f"DOCX-BLOCK-{index:06d}",
        "block_index": index,
        "kind": kind,
        "locator": docx_locator,
        "docx_locator": docx_locator,
        "section_path": list(section_path),
        "text": normalized,
        "exact_text": normalized,
        "requirement_codes": _requirement_codes(normalized),
        "numbering_labels": [],
    }
    if extra:
        block.update(extra)
    block.setdefault("docx_locator", block["locator"])
    block.setdefault("exact_text", normalized)
    block.setdefault("requirement_codes", _requirement_codes(normalized))
    block.setdefault("numbering_labels", [])
    block["structural_hash"] = _structural_hash(block)
    block["semantic_hash"] = _semantic_hash(block)
    block["block_hash"] = _block_hash(block)
    blocks.append(block)


def build_docx_source_json(
    docx_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Build a deterministic machine-readable JSON projection from a DOCX file.

    The projection is intentionally source-like, not requirement-aware: it
    preserves document order, visible paragraph/table-row text, section context
    and table row cell boundaries.  It can be compared with the current XHTML
    projection before being accepted as a production extraction source.
    """

    from docx import Document

    path = Path(docx_path)
    if path.suffix.lower() != ".docx":
        raise SourceJsonProjectionError("source JSON projection requires .docx input")
    if not path.is_file():
        raise SourceJsonProjectionError(f"DOCX file is missing: {path}")

    document = Document(path)
    numbering = _NumberingResolver(document)
    blocks: list[dict[str, Any]] = []
    heading_stack: list[tuple[int, str]] = []
    table_index = 0

    source_sha256 = _sha256_file(path)
    for source_block_index, block in enumerate(iter_block_items(document), start=1):
        if isinstance(block, Paragraph):
            text, numbering_label = _paragraph_text_and_numbering(block, numbering)
            if not text:
                continue
            level = paragraph_style_level(block)
            style_name = block.style.name if block.style else ""
            if level is not None:
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, text))
                _append_block(
                    blocks,
                    kind=f"heading-{level}",
                    text=text,
                    section_path=[item[1] for item in heading_stack],
                    extra={
                        "docx_locator": (
                            f"/word/document.xml/body/block[{source_block_index}]/w:p"
                        ),
                        "heading_level": level,
                        "section_id": detect_section_id(text),
                        "style_name": style_name,
                        "numbering_labels": [numbering_label]
                        if numbering_label
                        else [],
                    },
                )
                continue
            _append_block(
                blocks,
                kind="list-item" if numbering_label else "paragraph",
                text=text,
                section_path=[item[1] for item in heading_stack],
                extra={
                    "docx_locator": (
                        f"/word/document.xml/body/block[{source_block_index}]/w:p"
                    ),
                    "style_name": style_name,
                    "numbering_labels": [numbering_label]
                    if numbering_label
                    else [],
                },
            )
            continue

        if isinstance(block, Table):
            table_index += 1
            for row_index in range(len(block.rows)):
                row_locator = (
                    f"/word/document.xml/body/block[{source_block_index}]"
                    f"/w:tbl[{table_index}]/w:tr[{row_index + 1}]"
                )
                cells, cell_blocks, numbering_labels = _table_row_cells(
                    block,
                    row_index,
                    numbering,
                    row_locator=row_locator,
                )
                if not any(cells):
                    continue
                _append_block(
                    blocks,
                    kind="table-row",
                    text=" | ".join(cell or "-" for cell in cells),
                    section_path=[item[1] for item in heading_stack],
                    extra={
                        "docx_locator": row_locator,
                        "table_index": table_index,
                        "row_index": row_index + 1,
                        "cell_indices": list(range(1, len(cells) + 1)),
                        "cells": cells,
                        "cell_blocks": cell_blocks,
                        "cell_merge_metadata": [
                            item["merge_metadata"] for item in cell_blocks
                        ],
                        "numbering_labels": numbering_labels,
                    },
                )

    projection = {
        "version": SOURCE_JSON_PROJECTION_VERSION,
        "schema": "source-json-v2",
        "source_type": "docx-json-projection",
        "projection_kind": "source.compact",
        "document_id": f"DOCX-{source_sha256[:16]}",
        "source_path": _repository_relative_path(path, repo_root),
        "source_sha256": source_sha256,
        "source_hash": source_sha256,
        "excluded_metadata_classes": [
            "author-metadata",
            "decorative-formatting",
            "spellcheck",
            "theme",
        ],
        "block_count": len(blocks),
        "blocks": blocks,
    }
    projection["projection_sha256"] = hashlib.sha256(
        _canonical_json_bytes(
            {
                key: value
                for key, value in projection.items()
                if key != "projection_sha256"
            }
        )
    ).hexdigest()
    return projection


def write_docx_source_json(
    docx_path: Path,
    *,
    repo_root: Path,
    output_path: Path,
) -> None:
    projection = build_docx_source_json(docx_path, repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(projection, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_docx_source_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise SourceJsonProjectionError("source JSON projection must be an object")
    if payload.get("version") not in SUPPORTED_SOURCE_JSON_PROJECTION_VERSIONS:
        raise SourceJsonProjectionError("unsupported source JSON projection version")
    if payload.get("source_type") != "docx-json-projection":
        raise SourceJsonProjectionError("unsupported source JSON projection type")
    blocks = payload.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise SourceJsonProjectionError("source JSON projection has no blocks")
    return payload
