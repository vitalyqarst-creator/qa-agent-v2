from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent import inspect_source_quality, preview_chunks, resolve_sections


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Internal helper that demonstrates the public test_case_agent Python API."
    )
    parser.add_argument("source", type=Path, help="Path to the requirements document.")
    parser.add_argument("--section", help="Section prefix filter, for example 2.2.3.")
    parser.add_argument(
        "--max-sections",
        type=int,
        default=None,
        help="Limit number of selected sections.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=12000,
        help="Maximum chunk size for preview mode.",
    )
    parser.add_argument(
        "--mode",
        choices=("sections", "chunks", "quality"),
        default="sections",
        help="Show sections, chunk preview, or source quality warnings.",
    )
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "sections":
        sections = resolve_sections(args.source, args.section, args.max_sections)
        for section in sections:
            print(f"{section.section_id}\tL{section.level}\t{section.size}\t{section.full_title}")
        return

    if args.mode == "quality":
        issues = inspect_source_quality(args.source, max_chars=args.max_chars)
        if not issues:
            print("OK\tNo source quality issues detected.")
            return
        for issue in issues:
            print(f"{issue.severity}\t{issue.issue_id}\t{issue.details}\t{'; '.join(issue.evidence)}")
        return

    for chunk in preview_chunks(
        args.source,
        section_prefix=args.section,
        max_sections=args.max_sections,
        max_chars=args.max_chars,
    ):
        print(
            f"{chunk.chunk_id}\t{chunk.section_id}\t{len(chunk.text)}\t"
            f"{' > '.join(chunk.path)}"
        )


if __name__ == "__main__":
    main()


