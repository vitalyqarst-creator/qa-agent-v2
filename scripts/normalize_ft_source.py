from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from dataclasses import dataclass
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


def word_value(element: ET.Element | None, child_name: str) -> str | None:
    if element is None:
        return None
    child = element.find(f"./{W}{child_name}")
    return child.get(f"{W}val") if child is not None else None


def paragraph_style_id(paragraph: ET.Element) -> str | None:
    style = paragraph.find(f"./{W}pPr/{W}pStyle")
    return style.get(f"{W}val") if style is not None else None


def paragraph_tag(paragraph: ET.Element, style_names: dict[str, str]) -> str:
    style_id = paragraph_style_id(paragraph) or ""
    value = " ".join(filter(None, (style_id, style_names.get(style_id, ""))))
    match = re.search(r"(?:heading|заголовок)\s*([1-6])", value, re.IGNORECASE)
    return f"h{match.group(1)}" if match else "p"


def alphabetic_number(value: int, upper: bool = False) -> str:
    result = ""
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        result = chr(ord("A" if upper else "a") + remainder) + result
    return result


def roman_number(value: int, upper: bool = False) -> str:
    numerals = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    result: list[str] = []
    for amount, symbol in numerals:
        while value >= amount:
            result.append(symbol)
            value -= amount
    rendered = "".join(result)
    return rendered if upper else rendered.casefold()


def formatted_number(value: int, number_format: str) -> str:
    if number_format == "lowerLetter":
        return alphabetic_number(value)
    if number_format == "upperLetter":
        return alphabetic_number(value, upper=True)
    if number_format == "lowerRoman":
        return roman_number(value)
    if number_format == "upperRoman":
        return roman_number(value, upper=True)
    return str(value)


@dataclass(frozen=True)
class NumberingLevel:
    level: int
    start: int
    number_format: str
    level_text: str
    paragraph_style: str | None = None


class NumberingResolver:
    def __init__(self, styles: ET.Element | None, numbering: ET.Element | None) -> None:
        self.style_names: dict[str, str] = {}
        self.style_bases: dict[str, str] = {}
        self.style_numbering: dict[str, tuple[str, int | None]] = {}
        self.instances: dict[str, str] = {}
        self.levels: dict[str, dict[int, NumberingLevel]] = {}
        self.instance_starts: dict[tuple[str, int], int] = {}
        self.counters: dict[str, dict[int, int]] = {}
        if styles is not None:
            self._load_styles(styles)
        if numbering is not None:
            self._load_numbering(numbering)

    @staticmethod
    def _numbering_properties(element: ET.Element | None) -> tuple[str, int | None] | None:
        if element is None:
            return None
        number_id = word_value(element, "numId")
        if not number_id or number_id == "0":
            return None
        raw_level = word_value(element, "ilvl")
        return number_id, int(raw_level) if raw_level is not None else None

    def _load_styles(self, styles: ET.Element) -> None:
        for style in styles.findall(f"./{W}style"):
            style_id = style.get(f"{W}styleId")
            if not style_id:
                continue
            name = word_value(style, "name")
            base = word_value(style, "basedOn")
            properties = self._numbering_properties(style.find(f"./{W}pPr/{W}numPr"))
            if name:
                self.style_names[style_id] = name
            if base:
                self.style_bases[style_id] = base
            if properties:
                self.style_numbering[style_id] = properties

    def _load_numbering(self, numbering: ET.Element) -> None:
        for abstract in numbering.findall(f"./{W}abstractNum"):
            abstract_id = abstract.get(f"{W}abstractNumId")
            if not abstract_id:
                continue
            abstract_levels: dict[int, NumberingLevel] = {}
            for level in abstract.findall(f"./{W}lvl"):
                raw_level = level.get(f"{W}ilvl", "0")
                start = int(word_value(level, "start") or "1")
                abstract_levels[int(raw_level)] = NumberingLevel(
                    level=int(raw_level),
                    start=start,
                    number_format=word_value(level, "numFmt") or "decimal",
                    level_text=word_value(level, "lvlText") or "",
                    paragraph_style=word_value(level, "pStyle"),
                )
            self.levels[abstract_id] = abstract_levels
        for instance in numbering.findall(f"./{W}num"):
            number_id = instance.get(f"{W}numId")
            abstract_id = word_value(instance, "abstractNumId")
            if number_id and abstract_id:
                self.instances[number_id] = abstract_id
                for override in instance.findall(f"./{W}lvlOverride"):
                    raw_level = override.get(f"{W}ilvl", "0")
                    start_override = word_value(override, "startOverride")
                    if start_override is None:
                        continue
                    level_number = int(raw_level)
                    self.instance_starts[(number_id, level_number)] = int(start_override)

    def _style_properties(self, style_id: str | None) -> tuple[str, int | None] | None:
        visited: set[str] = set()
        while style_id and style_id not in visited:
            visited.add(style_id)
            if style_id in self.style_numbering:
                return self.style_numbering[style_id]
            style_id = self.style_bases.get(style_id)
        return None

    def _paragraph_properties(self, paragraph: ET.Element) -> tuple[str, int] | None:
        direct = self._numbering_properties(paragraph.find(f"./{W}pPr/{W}numPr"))
        style_id = paragraph_style_id(paragraph)
        properties = direct or self._style_properties(style_id)
        if not properties:
            return None
        number_id, level = properties
        abstract_id = self.instances.get(number_id)
        available_levels = self.levels.get(abstract_id or "", {})
        if level is None:
            matching = [item.level for item in available_levels.values() if item.paragraph_style == style_id]
            level = matching[0] if matching else 0
        if level not in available_levels:
            return None
        return number_id, level

    def render_prefix(self, paragraph: ET.Element) -> tuple[str, str | None, int | None]:
        properties = self._paragraph_properties(paragraph)
        if not properties:
            return "", None, None
        number_id, level_number = properties
        abstract_id = self.instances[number_id]
        levels = self.levels[abstract_id]
        level = levels[level_number]
        counters = self.counters.setdefault(number_id, {})
        start = self.instance_starts.get((number_id, level_number), level.start)
        counters[level_number] = counters.get(level_number, start - 1) + 1
        for deeper_level in [item for item in counters if item > level_number]:
            del counters[deeper_level]
        for parent_level in range(level_number):
            if parent_level not in counters and parent_level in levels:
                counters[parent_level] = levels[parent_level].start

        def replace(match: re.Match[str]) -> str:
            referenced_level = int(match.group(1)) - 1
            referenced = levels.get(referenced_level)
            value = counters.get(referenced_level)
            if referenced is None or value is None:
                return match.group(0)
            return formatted_number(value, referenced.number_format)

        prefix = re.sub(r"%([1-9])", replace, level.level_text)
        if level.number_format == "none":
            prefix = ""
        if prefix and not prefix[-1].isspace():
            prefix += " "
        return prefix, number_id, level_number


def append_paragraph(parent: ET.Element, paragraph: ET.Element, resolver: NumberingResolver) -> None:
    target = ET.SubElement(parent, paragraph_tag(paragraph, resolver.style_names))
    prefix, number_id, level = resolver.render_prefix(paragraph)
    target.text = prefix + word_text(paragraph)
    if number_id is not None:
        target.set("data-list-id", number_id)
    if level is not None:
        target.set("data-list-level", str(level))


def append_table(parent: ET.Element, table: ET.Element, resolver: NumberingResolver) -> None:
    output_table = ET.SubElement(parent, "table")
    for row in table.findall(f"./{W}tr"):
        output_row = ET.SubElement(output_table, "tr")
        for cell in row.findall(f"./{W}tc"):
            output_cell = ET.SubElement(output_row, "td")
            append_blocks(output_cell, cell, resolver)


def append_blocks(parent: ET.Element, container: ET.Element, resolver: NumberingResolver) -> None:
    for child in container:
        name = local_name(child.tag)
        if name == "p":
            append_paragraph(parent, child, resolver)
        elif name == "tbl":
            append_table(parent, child, resolver)
        elif name in {"customXml", "sdt", "sdtContent"}:
            append_blocks(parent, child, resolver)


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
            styles = ET.fromstring(archive.read("word/styles.xml")) if "word/styles.xml" in archive.namelist() else None
            numbering = (
                ET.fromstring(archive.read("word/numbering.xml"))
                if "word/numbering.xml" in archive.namelist()
                else None
            )
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
    resolver = NumberingResolver(styles, numbering)
    word_body = document.find(f"./{W}body")
    if word_body is None:
        raise ValueError("DOCX document.xml has no body")
    append_blocks(body, word_body, resolver)

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
