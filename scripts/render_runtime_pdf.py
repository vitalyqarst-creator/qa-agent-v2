from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

import fitz

try:
    from scripts.cleanup_runtime_temp import cleanup
except ModuleNotFoundError:  # Direct invocation: python scripts/render_runtime_pdf.py
    from cleanup_runtime_temp import cleanup


TEMP_PREFIX = "ft-runtime-pdf-visual-"


def parse_pages(spec: str, page_count: int) -> list[int]:
    if page_count < 1:
        raise ValueError("PDF has no pages")
    normalized = spec.strip().casefold()
    if normalized == "all":
        return list(range(page_count))
    selected: set[int] = set()
    for token in (part.strip() for part in spec.split(",")):
        if not token:
            raise ValueError("page selection contains an empty item")
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            if not start_text.isdigit() or not end_text.isdigit():
                raise ValueError(f"invalid page range: {token}")
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"page range is reversed: {token}")
            selected.update(range(start, end + 1))
        elif token.isdigit():
            selected.add(int(token))
        else:
            raise ValueError(f"invalid page number: {token}")
    if not selected:
        raise ValueError("at least one page must be selected")
    invalid = [page for page in sorted(selected) if page < 1 or page > page_count]
    if invalid:
        raise ValueError(f"page numbers are outside 1..{page_count}: {invalid}")
    return [page - 1 for page in sorted(selected)]


def _contact_sheet(
    document: fitz.Document,
    page_indexes: list[int],
    output: Path,
    columns: int,
    thumbnail_width: int,
    gutter: int = 12,
) -> None:
    sizes: list[tuple[int, int]] = []
    for index in page_indexes:
        page = document.load_page(index)
        scale = thumbnail_width / page.rect.width
        sizes.append((thumbnail_width, max(1, round(page.rect.height * scale))))
    rows = math.ceil(len(page_indexes) / columns)
    row_heights = [
        max(height for _, height in sizes[row * columns : (row + 1) * columns])
        for row in range(rows)
    ]
    width = columns * thumbnail_width + (columns + 1) * gutter
    height = sum(row_heights) + (rows + 1) * gutter
    canvas = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), False)
    canvas.clear_with(255)
    y = gutter
    for row in range(rows):
        x = gutter
        for column in range(columns):
            item = row * columns + column
            if item >= len(page_indexes):
                break
            page = document.load_page(page_indexes[item])
            scale = thumbnail_width / page.rect.width
            thumbnail = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            canvas.copy(thumbnail, fitz.IRect(x, y, x + thumbnail.width, y + thumbnail.height))
            x += thumbnail_width + gutter
        y += row_heights[row] + gutter
    canvas.save(output)


def render_pdf(
    pdf_path: Path,
    page_spec: str,
    dpi: int = 120,
    contact_columns: int = 4,
    contact_page_limit: int = 40,
) -> dict[str, Any]:
    source = pdf_path.resolve()
    if not source.is_file():
        raise ValueError(f"PDF does not exist: {source}")
    if dpi < 36 or dpi > 300:
        raise ValueError("dpi must be between 36 and 300")
    if contact_columns < 1 or contact_columns > 8:
        raise ValueError("contact columns must be between 1 and 8")
    if contact_page_limit < 1 or contact_page_limit > 100:
        raise ValueError("contact page limit must be between 1 and 100")

    output_dir = Path(tempfile.mkdtemp(prefix=TEMP_PREFIX)).resolve()
    try:
        with fitz.open(source) as document:
            selected = parse_pages(page_spec, document.page_count)
            rendered_pages: list[str] = []
            for page_index in selected:
                output = output_dir / f"page-{page_index + 1:04d}.png"
                document.load_page(page_index).get_pixmap(dpi=dpi, alpha=False).save(output)
                rendered_pages.append(str(output))

            contact_sheets: list[str] = []
            for start in range(0, len(selected), contact_page_limit):
                chunk = selected[start : start + contact_page_limit]
                output = output_dir / f"contact-sheet-{len(contact_sheets) + 1:02d}.png"
                _contact_sheet(document, chunk, output, contact_columns, thumbnail_width=240)
                contact_sheets.append(str(output))

            return {
                "valid": True,
                "source": str(source),
                "page_count": document.page_count,
                "selected_pages": [index + 1 for index in selected],
                "output_dir": str(output_dir),
                "rendered_pages": rendered_pages,
                "contact_sheets": contact_sheets,
            }
    except Exception:
        cleanup([output_dir])
        raise


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Render a PDF with Unicode paths into an isolated system temp directory."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", default="all", help="1-based pages: all, 8-17 or 8,10-12")
    parser.add_argument("--dpi", type=int, default=120)
    parser.add_argument("--contact-columns", type=int, default=4)
    parser.add_argument("--contact-page-limit", type=int, default=40)
    args = parser.parse_args()
    try:
        result = render_pdf(
            args.pdf,
            args.pages,
            args.dpi,
            args.contact_columns,
            args.contact_page_limit,
        )
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
