from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XHTML_NS = "http://www.w3.org/1999/xhtml"
W = f"{{{WORD_NS}}}"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def word_text(element: ET.Element) -> str:
    parts: list[str] = []
    for child in element.iter():
        name = local_name(child.tag)
        if name == "t" and child.text:
            parts.append(child.text)
        elif name == "tab":
            parts.append("\t")
        elif name in {"br", "cr"}:
            parts.append("\n")
    return "".join(parts)


def paragraph_tag(paragraph: ET.Element) -> str:
    style = paragraph.find(f"./{W}pPr/{W}pStyle")
    value = style.get(f"{W}val", "") if style is not None else ""
    match = re.search(r"(?:heading|заголовок)\s*([1-6])", value, re.IGNORECASE)
    return f"h{match.group(1)}" if match else "p"


def append_paragraph(parent: ET.Element, paragraph: ET.Element) -> None:
    target = ET.SubElement(parent, paragraph_tag(paragraph))
    target.text = word_text(paragraph)
    numbering = paragraph.find(f"./{W}pPr/{W}numPr")
    if numbering is not None:
        level = numbering.find(f"./{W}ilvl")
        number = numbering.find(f"./{W}numId")
        if level is not None:
            target.set("data-list-level", level.get(f"{W}val", "0"))
        if number is not None:
            target.set("data-list-id", number.get(f"{W}val", ""))


def append_table(parent: ET.Element, table: ET.Element) -> None:
    output_table = ET.SubElement(parent, "table")
    for row in table.findall(f"./{W}tr"):
        output_row = ET.SubElement(output_table, "tr")
        for cell in row.findall(f"./{W}tc"):
            output_cell = ET.SubElement(output_row, "td")
            paragraphs = cell.findall(f"./{W}p")
            for index, paragraph in enumerate(paragraphs):
                if index:
                    ET.SubElement(output_cell, "br")
                text = word_text(paragraph)
                if index == 0:
                    output_cell.text = text
                else:
                    output_cell[-1].tail = text


def normalize_docx(source: Path, destination: Path, overwrite: bool = False) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if source.suffix.casefold() != ".docx":
        raise ValueError("canonical source must be a .docx file")
    if not source.is_file():
        raise ValueError(f"canonical source does not exist: {source}")
    if destination.suffix.casefold() not in {".xhtml", ".xml"}:
        raise ValueError("normalized destination must use .xhtml or .xml")
    if destination.exists() and not overwrite:
        raise ValueError(f"normalized destination already exists: {destination}")

    try:
        with zipfile.ZipFile(source) as archive:
            document = ET.fromstring(archive.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError(f"cannot read DOCX document.xml: {exc}") from exc

    html = ET.Element("html", {"xmlns": XHTML_NS, "lang": "ru"})
    head = ET.SubElement(html, "head")
    ET.SubElement(head, "meta", {"charset": "utf-8"})
    ET.SubElement(head, "meta", {"name": "generator", "content": "scripts/normalize_ft_source.py"})
    ET.SubElement(
        head,
        "meta",
        {"name": "source-sha256", "content": hashlib.sha256(source.read_bytes()).hexdigest()},
    )
    ET.SubElement(head, "title").text = source.name
    body = ET.SubElement(html, "body")
    word_body = document.find(f"./{W}body")
    if word_body is None:
        raise ValueError("DOCX document.xml has no body")
    for child in word_body:
        name = local_name(child.tag)
        if name == "p":
            append_paragraph(body, child)
        elif name == "tbl":
            append_table(body, child)

    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(html).write(destination, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create deterministic XHTML extraction from a canonical DOCX FT.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        normalize_docx(args.source, args.destination, overwrite=args.force)
    except ValueError as exc:
        parser.error(str(exc))
    print(args.destination.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
