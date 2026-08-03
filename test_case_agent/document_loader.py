from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Iterator

from docx import Document
from docx.document import Document as DocumentType
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from test_case_agent.models import Section

HEADING_RE = re.compile(r"^\d+(?:\.\d+)*")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def detect_section_id(title: str) -> str | None:
    match = HEADING_RE.match(title.strip())
    if match:
        return match.group(0).rstrip(".")
    return None


def slugify(value: str) -> str:
    clean = re.sub(r"[^0-9A-Za-zА-Яа-яЁё]+", "-", value.strip(), flags=re.UNICODE)
    clean = clean.strip("-").lower()
    return clean or "section"


def iter_block_items(parent: DocumentType | _Cell) -> Iterator[Paragraph | Table]:
    if isinstance(parent, DocumentType):
        parent_element = parent.element.body
    else:
        parent_element = parent._tc

    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def paragraph_style_level(paragraph: Paragraph) -> int | None:
    style_name = paragraph.style.name if paragraph.style else ""
    match = re.match(r"Heading (\d+)$", style_name)
    if match:
        return int(match.group(1))
    return None


def table_to_text(table: Table) -> str:
    lines: list[str] = []
    for row in table.rows:
        cells = [normalize_text(cell.text) or "-" for cell in row.cells]
        if any(cell != "-" for cell in cells):
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines).strip()


def finalize_sections(sections: list[Section]) -> list[Section]:
    return [section for section in sections if section.text]


def load_docx_sections(path: Path) -> list[Section]:
    document = Document(path)
    sections: list[Section] = []
    heading_stack: list[tuple[int, str]] = []
    untitled_counter = 1
    current = Section(
        section_id="preface",
        title="Preface",
        level=0,
        path=["Preface"],
        source_path=path,
    )
    sections.append(current)

    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            text = normalize_text(block.text)
            if not text:
                continue

            level = paragraph_style_level(block)
            if level is not None:
                section_id = detect_section_id(text)
                if section_id is None and text.lower().startswith(("рисунок ", "таблица ")):
                    current.content_blocks.append(text)
                    continue

                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, text))
                section_id = section_id or f"section-{untitled_counter}"
                untitled_counter += 1
                current = Section(
                    section_id=section_id,
                    title=text,
                    level=level,
                    path=[title for _, title in heading_stack],
                    source_path=path,
                )
                sections.append(current)
                continue

            current.content_blocks.append(text)
            continue

        table_text = table_to_text(block)
        if table_text:
            current.content_blocks.append(table_text)

    return finalize_sections(sections)


def load_pdf_sections(path: Path) -> list[Section]:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="ARC4 has been moved", category=Warning)
        from pypdf import PdfReader

    reader = PdfReader(str(path))
    content_blocks: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        if text:
            content_blocks.append(f"[Page {page_number}] {text}")

    section = Section(
        section_id="pdf-document",
        title=path.stem,
        level=1,
        path=[path.stem],
        source_path=path,
        content_blocks=content_blocks,
    )
    return finalize_sections([section])


def load_sections(path: Path) -> list[Section]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return load_docx_sections(path)
    if suffix == ".pdf":
        return load_pdf_sections(path)
    raise ValueError(f"Unsupported document type: {path.suffix}")
