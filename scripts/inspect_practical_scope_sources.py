"""Read-only, deterministic source inspection for one practical v0.9 scope."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent import load_sections


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect one FT scope in XHTML, DOCX and optional PDF without writing artifacts."
    )
    parser.add_argument("--section", required=True, help="Section ID, for example 9.3.2.")
    parser.add_argument("--xhtml", type=Path, required=True)
    parser.add_argument("--docx", type=Path)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument(
        "--fallback-title",
        help="Optional title fragment for DOCX/PDF when the section number is absent or malformed.",
    )
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument(
        "--pdf-content-start-page",
        type=int,
        default=4,
        help="First physical PDF page eligible for a scope anchor; skips typical front matter.",
    )
    parser.add_argument(
        "--pdf-context-pages",
        type=int,
        default=1,
        help="Number of following PDF pages included after an anchor page.",
    )
    return parser.parse_args(argv)


def selected_sections(
    source: Path, section_id: str, fallback_title: str | None, max_chars: int
) -> list[dict[str, Any]]:
    if not source.is_file():
        raise ValueError(f"source does not exist: {source}")
    title_needle = (fallback_title or "").casefold().strip()
    result: list[dict[str, Any]] = []
    for section in load_sections(source):
        by_id = section.section_id == section_id or section.section_id.startswith(section_id + ".")
        by_title = bool(title_needle) and title_needle in section.full_title.casefold()
        if not (by_id or by_title):
            continue
        result.append({
            "section_id": section.section_id,
            "title": section.full_title,
            "level": section.level,
            "text": section.text[:max_chars],
            "truncated": len(section.text) > max_chars,
        })
    return result


def selected_pdf_pages(
    source: Path,
    section_id: str,
    fallback_title: str | None,
    max_chars: int,
    content_start_page: int,
    context_pages: int,
) -> list[dict[str, Any]]:
    if not source.is_file():
        raise ValueError(f"source does not exist: {source}")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF structural cross-check") from exc

    pages = [page.extract_text() or "" for page in PdfReader(source).pages]
    eligible_pages = range(max(1, content_start_page), len(pages) + 1)
    section_needle = section_id.casefold()
    anchor_pages = [
        page_number
        for page_number in eligible_pages
        if section_needle in pages[page_number - 1].casefold()
    ]
    if not anchor_pages and fallback_title:
        title_needle = fallback_title.casefold()
        anchor_pages = [
            page_number
            for page_number in eligible_pages
            if title_needle in pages[page_number - 1].casefold()
        ]

    selected_pages: dict[int, str] = {}
    for anchor_page in anchor_pages:
        selected_pages[anchor_page] = "anchor"
        for page_number in range(anchor_page + 1, min(len(pages), anchor_page + context_pages) + 1):
            selected_pages.setdefault(page_number, "following-context")

    matches: list[dict[str, Any]] = []
    for page_number, match_kind in sorted(selected_pages.items()):
        text = pages[page_number - 1]
        if match_kind == "anchor":
            offset = text.casefold().find(section_needle)
            if offset < 0 and fallback_title:
                offset = text.casefold().find(fallback_title.casefold())
            start = max(0, offset - max_chars // 4) if offset >= 0 else 0
            excerpt = text[start:start + max_chars]
        else:
            excerpt = text[:max_chars]
        matches.append({
            "page": page_number,
            "match_kind": match_kind,
            "text": excerpt,
            "truncated": len(excerpt) < len(text),
        })
    return matches


def inspect_sources(args: argparse.Namespace) -> dict[str, Any]:
    if args.max_chars <= 0 or args.pdf_content_start_page <= 0 or args.pdf_context_pages < 0:
        raise ValueError("--max-chars and --pdf-content-start-page must be positive; --pdf-context-pages must be non-negative")
    payload: dict[str, Any] = {
        "section": args.section,
        "fallback_title": args.fallback_title,
        "sources": [
            {
                "kind": "xhtml",
                "path": args.xhtml.as_posix(),
                "matches": selected_sections(
                    args.xhtml, args.section, args.fallback_title, args.max_chars
                ),
            }
        ],
    }
    if args.docx is not None:
        payload["sources"].append({
            "kind": "docx",
            "path": args.docx.as_posix(),
            "matches": selected_sections(
                args.docx, args.section, args.fallback_title, args.max_chars
            ),
        })
    if args.pdf is not None:
        payload["sources"].append({
            "kind": "pdf-cross-check",
            "path": args.pdf.as_posix(),
            "matches": selected_pdf_pages(
                args.pdf,
                args.section,
                args.fallback_title,
                args.max_chars,
                args.pdf_content_start_page,
                args.pdf_context_pages,
            ),
        })
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = inspect_sources(args)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
