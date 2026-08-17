from __future__ import annotations

import re
from dataclasses import dataclass


PROCESS_PREFIXES = {
    "ATOM",
    "BAQ",
    "CLR",
    "FIX",
    "FX",
    "GAP",
    "ID",
    "M",
    "OBL",
    "PDF",
    "FIGURE",
    "PAGE",
    "ROW",
    "SECTION",
    "SETUP",
    "SRC",
    "SR",
    "TABLE",
    "TC",
    "UCLR",
    "РАЗДЕЛ",
    "РИСУНОК",
    "СТРАНИЦА",
    "СТРОКА",
    "ТАБЛИЦА",
}
RANGE_RE = re.compile(
    r"\b([A-ZА-ЯЁ][A-ZА-ЯЁ0-9_-]{0,15})\.(\d+)\s*[-–—]\s*(?:([A-ZА-ЯЁ][A-ZА-ЯЁ0-9_-]{0,15})\.)?(\d+)\b"
)
DOT_CODE_RE = re.compile(r"\b([A-ZА-ЯЁ][A-ZА-ЯЁ0-9_-]{0,15})\.(\d+(?:\.\d+)*)\b")
SPACE_CODE_RE = re.compile(r"\b([A-ZА-ЯЁ]{2,10})\s+(\d+(?:\.\d+)*)\b")
TABLE_RE = re.compile(
    r"\bтаблиц(?:а|ы|е|у|ей)\s*(\d+)"
    r"(?:\s*[,;/]\s*строк(?:а|и|е|у)\s*[`\"«]?([^`\"»;|\n]+)[`\"»]?)?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MarkdownTable:
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def index(self, name: str) -> int:
        return self.header.index(name)


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def find_markdown_table(content: str, required_headers: tuple[str, ...]) -> MarkdownTable | None:
    lines = content.splitlines()
    for index, line in enumerate(lines[:-1]):
        header = cells(line)
        if not all(name in header for name in required_headers):
            continue
        separator = cells(lines[index + 1])
        if len(separator) != len(header) or not all(re.fullmatch(r":?-{3,}:?", item) for item in separator):
            continue
        rows: list[tuple[str, ...]] = []
        for candidate in lines[index + 2 :]:
            if not candidate.strip().startswith("|"):
                break
            row = cells(candidate)
            if len(row) == len(header):
                rows.append(tuple(row))
        return MarkdownTable(tuple(header), tuple(rows))
    return None


def normalize_label(value: str) -> str:
    value = re.sub(r"[`\"«»]", "", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def extract_anchors(value: str) -> set[str]:
    anchors: set[str] = set()
    for prefix, start_raw, repeated_prefix, end_raw in RANGE_RE.findall(value.upper()):
        end_prefix = repeated_prefix or prefix
        start = int(start_raw)
        end = int(end_raw)
        if prefix == end_prefix and prefix not in PROCESS_PREFIXES and 0 <= end - start <= 500:
            anchors.update(f"CODE:{prefix}.{number}" for number in range(start, end + 1))
    for prefix, number in DOT_CODE_RE.findall(value.upper()):
        if prefix not in PROCESS_PREFIXES:
            anchors.add(f"CODE:{prefix}.{number}")
    for prefix, number in SPACE_CODE_RE.findall(value.upper()):
        if prefix not in PROCESS_PREFIXES:
            anchors.add(f"CODE:{prefix} {number}")
    for table_number, row_label in TABLE_RE.findall(value):
        if row_label.strip():
            anchors.add(f"TABLE:{table_number}:{normalize_label(row_label)}")
        else:
            anchors.add(f"TABLE:{table_number}")
    return anchors


def anchor_label(anchor: str) -> str:
    if anchor.startswith("CODE:"):
        return anchor.removeprefix("CODE:")
    if anchor.startswith("TABLE:"):
        parts = anchor.split(":", 2)
        if len(parts) == 3:
            return f"Таблица {parts[1]}, строка «{parts[2]}»"
        return f"Таблица {parts[1]}"
    return anchor
