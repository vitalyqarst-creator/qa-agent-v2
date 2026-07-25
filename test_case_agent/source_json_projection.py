from __future__ import annotations

import hashlib
import json
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


SOURCE_JSON_PROJECTION_VERSION = 1


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
        if p_pr is None or p_pr.numPr is None:
            return None
        num_id_node = p_pr.numPr.numId
        if num_id_node is None:
            return None
        num_id = num_id_node.val
        ilvl_node = p_pr.numPr.ilvl
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


def _paragraph_text_with_numbering(
    paragraph: Paragraph,
    numbering: _NumberingResolver,
) -> str:
    prefix = numbering.prefix_for(paragraph)
    text = normalize_text(paragraph.text)
    if not text:
        return ""
    if prefix and not text.startswith(prefix):
        return normalize_text(f"{prefix} {text}")
    return text


def _cell_text_with_numbering(
    cell: _Cell,
    numbering: _NumberingResolver,
) -> str:
    parts = [
        text
        for paragraph in cell.paragraphs
        if (text := _paragraph_text_with_numbering(paragraph, numbering))
    ]
    return normalize_text(" ".join(parts))


def _table_row_cells(table: Table, row_index: int, numbering: _NumberingResolver) -> list[str]:
    row = table.rows[row_index]
    return [
        _cell_text_with_numbering(_Cell(tc, table), numbering)
        for tc in row._tr.tc_lst
    ]


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
    block: dict[str, Any] = {
        "block_id": f"DOCX-BLOCK-{index:06d}",
        "block_index": index,
        "kind": kind,
        "locator": f"/blocks/{index}",
        "section_path": list(section_path),
        "text": normalized,
    }
    if extra:
        block.update(extra)
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

    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            text = _paragraph_text_with_numbering(block, numbering)
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
                        "heading_level": level,
                        "section_id": detect_section_id(text),
                        "style_name": style_name,
                    },
                )
                continue
            _append_block(
                blocks,
                kind="paragraph",
                text=text,
                section_path=[item[1] for item in heading_stack],
                extra={"style_name": style_name},
            )
            continue

        if isinstance(block, Table):
            table_index += 1
            for row_index in range(len(block.rows)):
                cells = _table_row_cells(block, row_index, numbering)
                if not any(cells):
                    continue
                _append_block(
                    blocks,
                    kind="table-row",
                    text=" | ".join(cell or "-" for cell in cells),
                    section_path=[item[1] for item in heading_stack],
                    extra={
                        "table_index": table_index,
                        "row_index": row_index + 1,
                        "cells": cells,
                    },
                )

    projection = {
        "version": SOURCE_JSON_PROJECTION_VERSION,
        "source_type": "docx-json-projection",
        "source_path": _repository_relative_path(path, repo_root),
        "source_sha256": _sha256_file(path),
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
    if payload.get("version") != SOURCE_JSON_PROJECTION_VERSION:
        raise SourceJsonProjectionError("unsupported source JSON projection version")
    if payload.get("source_type") != "docx-json-projection":
        raise SourceJsonProjectionError("unsupported source JSON projection type")
    blocks = payload.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise SourceJsonProjectionError("source JSON projection has no blocks")
    return payload
