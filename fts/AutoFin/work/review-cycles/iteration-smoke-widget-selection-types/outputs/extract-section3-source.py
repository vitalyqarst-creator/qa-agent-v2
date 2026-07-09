from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document


ROOT = Path(__file__).resolve().parents[6]
FT_ROOT = ROOT / "fts" / "AutoFin"
DOCX_PATH = FT_ROOT / "source" / "FT4AutoFinFinal.docx"
XHTML_PATH = FT_ROOT / "source" / "FT4AutoFinFinal.xhtml"
OUT_PATH = Path(__file__).with_name("source-excerpt.writer-r1.md")


def iter_docx_blocks(document: Document):
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            texts = [node.text for node in child.iter() if node.tag.rsplit("}", 1)[-1] == "t" and node.text]
            text = "".join(texts).strip()
            if text:
                yield ("paragraph", text)
        elif tag == "tbl":
            rows = []
            for row in child.iter():
                if row.tag.rsplit("}", 1)[-1] != "tr":
                    continue
                cells = []
                for cell in row.iter():
                    if cell.tag.rsplit("}", 1)[-1] != "tc":
                        continue
                    texts = [node.text for node in cell.iter() if node.tag.rsplit("}", 1)[-1] == "t" and node.text]
                    value = " ".join("".join(texts).split())
                    cells.append(value)
                if cells:
                    rows.append(cells)
            if rows:
                yield ("table", rows)


def docx_section3_excerpt() -> list[str]:
    document = Document(str(DOCX_PATH))
    lines = []
    for block_type, value in iter_docx_blocks(document):
        if block_type == "paragraph":
            text = value
            if text.startswith("По умолчанию значения в виджетах"):
                lines.append(f"- DOCX paragraph: `{text}`")
        else:
            rows = value
            for row in rows:
                joined = " | ".join(row)
                if len(row) == 2 and row[0] in {"Список", "Список с множественным выбором"}:
                    lines.append(f"- DOCX table row: `{joined}`")
    return lines


def xhtml_excerpt() -> list[str]:
    soup = BeautifulSoup(XHTML_PATH.read_text(encoding="utf-8"), "html.parser")
    lines = []
    for row in soup.find_all("tr"):
        cells = [" ".join(cell.get_text(" ", strip=True).split()) for cell in row.find_all(["td", "th"])]
        if cells and len(cells) == 2 and cells[0] in {"Список", "Список с множественным выбором"}:
            lines.append(f"- XHTML table row: `{' | '.join(cells)}`")
    for text in soup.stripped_strings:
        normalized = " ".join(text.split())
        if normalized.startswith("По умолчанию значения в виджетах"):
            lines.append(f"- XHTML paragraph/text: `{normalized}`")
    return lines


def main() -> None:
    body = [
        "# Source Excerpt Writer R1",
        "",
        "## DOCX Section 3",
        "",
        *docx_section3_excerpt(),
        "",
        "## XHTML Section 3",
        "",
        *xhtml_excerpt(),
        "",
    ]
    OUT_PATH.write_text("\n".join(body), encoding="utf-8", newline="\n")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
