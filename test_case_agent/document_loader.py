from __future__ import annotations

import re
import warnings
import xml.etree.ElementTree as ET
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
XHTML_HEADING_RE = re.compile(r"^h([1-6])$")
XHTML_TABLE_CELL_TAGS = {"td", "th"}


def _xhtml_local_name(tag: object) -> str:
    """Return a lowercase local name while keeping non-element nodes harmless."""

    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].casefold()


def _xhtml_is_decorative(element: ET.Element) -> bool:
    """Identify converter-only list markers that are not requirement text."""

    classes = set(element.attrib.get("class", "").split())
    return any(item.startswith("ListLabel_") for item in classes) or "odfLiEnd" in classes


def _xhtml_contains_heading(element: ET.Element) -> bool:
    return any(
        descendant is not element
        and XHTML_HEADING_RE.fullmatch(_xhtml_local_name(descendant.tag))
        for descendant in element.iter()
    )


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


def _xhtml_text(
    element: ET.Element,
    *,
    exclude_descendants: set[str] | None = None,
    include_decorative: bool = False,
) -> str:
    """Extract visible XHTML text, excluding nested structural blocks when needed."""

    excluded = exclude_descendants or set()
    parts: list[str] = []

    def visit(node: ET.Element) -> None:
        if node.text:
            parts.append(node.text)
        for child in node:
            if (
                _xhtml_local_name(child.tag) not in excluded
                and (include_decorative or not _xhtml_is_decorative(child))
            ):
                visit(child)
            if child.tail:
                parts.append(child.tail)

    visit(element)
    return normalize_text(" ".join(parts))


def _xhtml_table_row_to_text(row: ET.Element) -> str:
    cells = [
        _xhtml_text(cell)
        for cell in row
        if _xhtml_local_name(cell.tag) in XHTML_TABLE_CELL_TAGS
    ]
    if cells:
        return "| " + " | ".join(cell or "-" for cell in cells) + " |"
    return _xhtml_text(row)


def _xhtml_has_ancestor(
    element: ET.Element,
    parents: dict[ET.Element, ET.Element],
    tag_names: set[str],
) -> bool:
    current = parents.get(element)
    while current is not None:
        if _xhtml_local_name(current.tag) in tag_names:
            return True
        current = parents.get(current)
    return False


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


def load_xhtml_sections(path: Path) -> list[Section]:
    """Load XHTML into sections without treating comments as source text or nodes.

    Main FT XHTML is a mandatory machine-readable source.  The XML parser is
    configured to discard comments explicitly, so converter comments cannot
    alter section detection or leak into a requirement inventory.
    """

    try:
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=False))
        root = ET.fromstring(path.read_bytes(), parser=parser)
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"Cannot parse XHTML source {path}: {exc}") from exc

    parents = {child: parent for parent in root.iter() for child in parent}
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

    for element in root.iter():
        tag = _xhtml_local_name(element.tag)
        heading_match = XHTML_HEADING_RE.fullmatch(tag)
        if heading_match:
            # LibreOffice exports the visible section number in a ListLabel
            # span.  It is decorative for list text but structural for a
            # heading, so retain it here for stable section IDs.
            text = _xhtml_text(element, include_decorative=True)
            if not text:
                continue
            level = int(heading_match.group(1))
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, text))
            section_id = detect_section_id(text) or f"section-{untitled_counter}"
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

        if tag == "tr":
            text = _xhtml_table_row_to_text(element)
        elif tag == "li":
            if _xhtml_contains_heading(element):
                continue
            text = _xhtml_text(element, exclude_descendants={"ol", "ul"})
            if text:
                text = f"- {text}"
        elif tag == "p":
            if _xhtml_has_ancestor(element, parents, {"li", "td", "th"}):
                continue
            text = _xhtml_text(element)
        else:
            continue

        if text:
            current.content_blocks.append(text)

    return finalize_sections(sections)


def load_sections(path: Path) -> list[Section]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return load_docx_sections(path)
    if suffix == ".pdf":
        return load_pdf_sections(path)
    if suffix in {".xhtml", ".html"}:
        return load_xhtml_sections(path)
    raise ValueError(f"Unsupported document type: {path.suffix}")
