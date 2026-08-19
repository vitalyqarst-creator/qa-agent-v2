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
    r"\b([A-ZА-ЯЁ][A-ZА-ЯЁ0-9]{0,15})([._-])(\d+)\s*[-–—]\s*"
    r"(?:([A-ZА-ЯЁ][A-ZА-ЯЁ0-9]{0,15})([._-]))?(\d+)\b"
)
SEPARATED_CODE_RE = re.compile(
    r"\b([A-ZА-ЯЁ][A-ZА-ЯЁ0-9]{0,15})([._-])(\d+(?:[._-]\d+)*)\b"
)
SPACE_CODE_RE = re.compile(r"\b([A-ZА-ЯЁ]{2,10})\s+(\d+(?:\.\d+)*)\b")
TABLE_RE = re.compile(
    r"\bтаблиц(?:а|ы|е|у|ей)\s*(\d+)"
    r"(?:\s*[,;/]\s*строк(?:а|и|е|у)(?:\s+первого\s+столбца)?\s*"
    r"[`\"'«]?([^`\"'»;|\n.]+)[`\"'»]?)?",
    re.IGNORECASE,
)
SECTION_RE = re.compile(
    r"\b(?:раздел|подраздел|пункт)\s+([0-9]+(?:\.[0-9]+)*)\b",
    re.IGNORECASE,
)
QUOTED_STRUCTURAL_TEXT_RE = re.compile(
    r"\b(?:абзац|пункт|элемент\s+списка|строка)\s+(?:«([^»\n]{3,})»|`([^`\n]{3,})`)",
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


def diagnose_markdown_table(content: str, required_headers: tuple[str, ...]) -> str | None:
    """Explain a malformed expected table without exposing validator internals."""

    lines = content.splitlines()
    for index, line in enumerate(lines):
        header = cells(line)
        if not all(name in header for name in required_headers):
            continue
        if index + 1 >= len(lines):
            return f"table with headers {list(required_headers)!r} has no separator row"
        separator = cells(lines[index + 1])
        if len(separator) != len(header):
            return (
                f"table with headers {list(required_headers)!r} has {len(header)} header columns "
                f"but {len(separator)} separator columns"
            )
        if not all(re.fullmatch(r":?-{3,}:?", item) for item in separator):
            return f"table with headers {list(required_headers)!r} has an invalid separator row"
        for row_number, candidate in enumerate(lines[index + 2 :], start=1):
            if not candidate.strip().startswith("|"):
                break
            row = cells(candidate)
            if len(row) != len(header):
                return (
                    f"table with headers {list(required_headers)!r} row {row_number} has "
                    f"{len(row)} cells instead of {len(header)}"
                )
        return None
    return f"required table headers are absent: {list(required_headers)!r}"


def normalize_label(value: str) -> str:
    value = re.sub(r"[`\"«»]", "", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def extract_anchors(value: str) -> set[str]:
    anchors: set[str] = set()
    for prefix, separator, start_raw, repeated_prefix, repeated_separator, end_raw in RANGE_RE.findall(
        value.upper()
    ):
        end_prefix = repeated_prefix or prefix
        end_separator = repeated_separator or separator
        start = int(start_raw)
        end = int(end_raw)
        if (
            prefix == end_prefix
            and separator == end_separator
            and prefix not in PROCESS_PREFIXES
            and 0 <= end - start <= 500
        ):
            anchors.update(f"CODE:{prefix}{separator}{number}" for number in range(start, end + 1))
    for prefix, separator, number in SEPARATED_CODE_RE.findall(value.upper()):
        if prefix not in PROCESS_PREFIXES:
            anchors.add(f"CODE:{prefix}{separator}{number}")
    # Keep the original case here. Uppercasing prose turns ordinary phrases such
    # as "не более 40 МБ" into fake requirement codes ("БОЛЕЕ 40"). Genuine
    # space-separated project codes are already written in uppercase by the
    # source and are matched by SPACE_CODE_RE as-is.
    for prefix, number in SPACE_CODE_RE.findall(value):
        if prefix not in PROCESS_PREFIXES:
            anchors.add(f"CODE:{prefix} {number}")
    for table_number, row_label in TABLE_RE.findall(value):
        if row_label.strip():
            anchors.add(f"TABLE:{table_number}:{normalize_label(row_label)}")
        else:
            anchors.add(f"TABLE:{table_number}")
    anchors.update(f"SECTION:{number}" for number in SECTION_RE.findall(value))
    for left_quote, backtick_quote in QUOTED_STRUCTURAL_TEXT_RE.findall(value):
        anchors.add(f"TEXT:{normalize_label(left_quote or backtick_quote)}")
    return anchors


def anchor_label(anchor: str) -> str:
    if anchor.startswith("CODE:"):
        return anchor.removeprefix("CODE:")
    if anchor.startswith("TABLE:"):
        parts = anchor.split(":", 2)
        if len(parts) == 3:
            return f"Таблица {parts[1]}, строка «{parts[2]}»"
        return f"Таблица {parts[1]}"
    if anchor.startswith("SECTION:"):
        return f"Раздел {anchor.removeprefix('SECTION:')}"
    if anchor.startswith("TEXT:"):
        return f"фрагмент «{anchor.removeprefix('TEXT:')}»"
    return anchor
