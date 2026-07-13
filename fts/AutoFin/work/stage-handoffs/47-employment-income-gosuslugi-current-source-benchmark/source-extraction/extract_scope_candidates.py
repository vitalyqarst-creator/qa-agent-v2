from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from docx import Document
from lxml import etree
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_case_agent import resolve_sections


def normalize(value: str) -> str:
    return " ".join(value.split())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matches(value: str, terms: list[str]) -> bool:
    folded = value.casefold()
    return any(term.casefold() in folded for term in terms)


def select_table_rows(rows: list[dict[str, Any]], terms: list[str]) -> list[dict[str, Any]]:
    """Keep matched rows and a matched block's bounded row range, never the whole table."""
    selected_indexes: set[int] = {0} if rows else set()
    for position, row in enumerate(rows):
        cells = row["cells"]
        row_text = " | ".join(cells)
        if not matches(row_text, terms):
            continue
        selected_indexes.add(position)
        first_cell = cells[0].casefold() if cells else ""
        if not first_cell.startswith("блок "):
            continue
        boundary = len(rows)
        for candidate in range(position + 1, len(rows)):
            candidate_cells = rows[candidate]["cells"]
            if candidate_cells and candidate_cells[0].casefold().startswith("блок "):
                boundary = candidate
                break
        selected_indexes.update(range(position, boundary))
    return [row for position, row in enumerate(rows) if position in selected_indexes]


def extract_docx(path: Path, terms: list[str]) -> dict[str, Any]:
    sections = []
    for section in resolve_sections(path):
        if matches(section.text, terms) or matches(section.full_title, terms):
            lines = [line for line in section.text.splitlines() if matches(line, terms)]
            sections.append(
                {
                    "section_id": section.section_id,
                    "title": section.title,
                    "full_title": section.full_title,
                    "matching_lines": lines,
                }
            )

    document = Document(path)
    tables = []
    for table_index, table in enumerate(document.tables):
        rows = []
        table_match = False
        for row_index, row in enumerate(table.rows):
            cells = [normalize(cell.text) for cell in row.cells]
            text = " | ".join(cells)
            if matches(text, terms):
                table_match = True
            rows.append({"row_index": row_index, "cells": cells})
        if table_match:
            tables.append({"table_index": table_index, "rows": select_table_rows(rows, terms)})
    return {"sections": sections, "tables": tables}


def extract_xhtml(path: Path, terms: list[str]) -> dict[str, Any]:
    parser = etree.XMLParser(recover=True, huge_tree=True)
    document = etree.parse(str(path), parser)
    all_tables = document.xpath("//*[local-name()='table']")
    selected = []
    for table_index, table in enumerate(all_tables):
        text = normalize(" ".join(table.itertext()))
        if not matches(text, terms):
            continue
        rows = []
        for row_index, row in enumerate(table.xpath(".//*[local-name()='tr']")):
            cells = [
                normalize(" ".join(cell.itertext()))
                for cell in row.xpath("./*[local-name()='td' or local-name()='th']")
            ]
            rows.append({"row_index": row_index, "cells": cells})
        selected.append({"table_index": table_index, "rows": select_table_rows(rows, terms)})

    paragraphs = []
    for node in document.xpath("//*[local-name()='p']"):
        text = normalize(" ".join(node.itertext()))
        if text and len(text.encode("utf-8")) <= 2048 and matches(text, terms):
            paragraphs.append(text)
    return {"tables": selected, "matching_text": list(dict.fromkeys(paragraphs))}


def extract_pdf(path: Path, terms: list[str]) -> list[dict[str, Any]]:
    reader = PdfReader(str(path))
    texts = [normalize(page.extract_text() or "") for page in reader.pages]
    matched = {index + 1 for index, text in enumerate(texts) if matches(text, terms)}
    selected = {
        page_number
        for match_page in matched
        for page_number in range(max(1, match_page - 1), min(len(texts), match_page + 1) + 1)
    }
    return [
        {
            "page_number": page_number,
            "matched_query": page_number in matched,
            "text": texts[page_number - 1],
        }
        for page_number in sorted(selected)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--source-stem", required=True)
    parser.add_argument("--query", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    terms = json.loads(args.query.read_text(encoding="utf-8"))["terms"]
    paths = {
        suffix: args.source_dir / f"{args.source_stem}.{suffix}"
        for suffix in ("docx", "xhtml", "pdf")
    }
    payload = {
        "source_stem": args.source_stem,
        "terms": terms,
        "source_sha256": {key: sha256_file(path) for key, path in paths.items()},
        "docx": extract_docx(paths["docx"], terms),
        "xhtml": extract_xhtml(paths["xhtml"], terms),
        "pdf": extract_pdf(paths["pdf"], terms),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "docx_sections": len(payload["docx"]["sections"]),
        "docx_tables": len(payload["docx"]["tables"]),
        "xhtml_tables": len(payload["xhtml"]["tables"]),
        "pdf_pages": [item["page_number"] for item in payload["pdf"]],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
