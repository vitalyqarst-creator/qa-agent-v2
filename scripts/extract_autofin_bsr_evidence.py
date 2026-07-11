"""Extract bounded BSR evidence from matching AutoFin DOCX/XHTML/PDF sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Sequence

from docx import Document
from lxml import etree
from pypdf import PdfReader


def normalize(value: str) -> str:
    return " ".join(value.split())


def code_pattern(codes: Sequence[int]) -> re.Pattern[str]:
    alternatives = "|".join(str(code) for code in sorted(set(codes)))
    return re.compile(rf"\bBSR\s*(?:{alternatives})\b", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_docx(
    path: Path,
    pattern: re.Pattern[str],
    xhtml_anchors: set[str],
) -> list[dict[str, Any]]:
    document = Document(path)
    matches: list[dict[str, Any]] = []
    for table_index, table in enumerate(document.tables):
        for row_index, row in enumerate(table.rows):
            cells = [normalize(cell.text) for cell in row.cells]
            text = " | ".join(cells)
            if pattern.search(text) or (cells and cells[0] in xhtml_anchors):
                matches.append(
                    {
                        "table_index": table_index,
                        "row_index": row_index,
                        "anchor": cells[0],
                        "text": text,
                    }
                )
    return matches


def extract_xhtml(path: Path, pattern: re.Pattern[str]) -> list[dict[str, Any]]:
    parser = etree.XMLParser(recover=True, huge_tree=True)
    document = etree.parse(str(path), parser)
    matches: list[dict[str, Any]] = []
    for row_index, row in enumerate(document.xpath("//*[local-name()='tr']")):
        cells = [
            normalize(" ".join(cell.itertext()))
            for cell in row.xpath("./*[local-name()='td' or local-name()='th']")
        ]
        text = normalize(" ".join(row.itertext()))
        if pattern.search(text):
            matches.append(
                {
                    "row_index": row_index,
                    "anchor": cells[0] if cells else "",
                    "text": text,
                }
            )
    return matches


def extract_pdf(path: Path, pattern: re.Pattern[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for page_number, page in enumerate(PdfReader(str(path)).pages, start=1):
        text = normalize(page.extract_text() or "")
        page_matches = list(pattern.finditer(text))
        if page_matches:
            snippets = []
            for match in page_matches:
                start = max(0, match.start() - 180)
                end = min(len(text), match.end() + 520)
                snippets.append(text[start:end])
            matches.append({"page_number": page_number, "snippets": snippets})
    return matches


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--source-stem", required=True)
    parser.add_argument("--codes", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pattern = code_pattern(args.codes)
    docx_path = args.source_dir / f"{args.source_stem}.docx"
    xhtml_path = args.source_dir / f"{args.source_stem}.xhtml"
    pdf_path = args.source_dir / f"{args.source_stem}.pdf"
    xhtml_matches = extract_xhtml(xhtml_path, pattern)
    xhtml_anchors = {item["anchor"] for item in xhtml_matches if item["anchor"]}
    payload = {
        "source_stem": args.source_stem,
        "codes": sorted(set(args.codes)),
        "source_sha256": {
            "docx": sha256_file(docx_path),
            "xhtml": sha256_file(xhtml_path),
            "pdf": sha256_file(pdf_path),
        },
        "docx": extract_docx(docx_path, pattern, xhtml_anchors),
        "xhtml": xhtml_matches,
        "pdf": extract_pdf(pdf_path, pattern),
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
