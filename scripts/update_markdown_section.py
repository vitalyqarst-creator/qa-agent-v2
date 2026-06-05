from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Upsert one Markdown section without passing the full section body "
            "as a command-line argument."
        )
    )
    parser.add_argument("path", type=Path, help="Markdown file to update.")
    parser.add_argument(
        "--heading",
        required=True,
        help="Exact heading title, without leading # characters.",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=2,
        choices=range(1, 7),
        metavar="1-6",
        help="Markdown heading level to replace or append. Default: 2.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--content-file",
        type=Path,
        help="UTF-8 file containing the new section body.",
    )
    source.add_argument(
        "--stdin",
        action="store_true",
        dest="read_stdin",
        help="Read the new section body from stdin.",
    )
    return parser.parse_args()


def read_content(args: argparse.Namespace) -> str:
    if args.content_file is not None:
        return args.content_file.read_text(encoding="utf-8")
    return sys.stdin.read()


def section_bounds(text: str, level: int, heading: str) -> tuple[int, int] | None:
    target_match: re.Match[str] | None = None
    normalized_heading = heading.strip()

    for match in HEADING_RE.finditer(text):
        marker, title = match.groups()
        if len(marker) == level and title.strip() == normalized_heading:
            target_match = match
            break

    if target_match is None:
        return None

    for match in HEADING_RE.finditer(text, target_match.end()):
        marker = match.group(1)
        if len(marker) <= level:
            return target_match.start(), match.start()

    return target_match.start(), len(text)


def render_section(level: int, heading: str, content: str) -> str:
    prefix = "#" * level
    body = content.strip("\n")
    if body:
        return f"{prefix} {heading.strip()}\n\n{body}\n"
    return f"{prefix} {heading.strip()}\n"


def upsert_section(text: str, level: int, heading: str, content: str) -> str:
    section = render_section(level, heading, content).rstrip("\n")
    bounds = section_bounds(text, level, heading)

    if bounds is None:
        base = text.rstrip("\n")
        if base:
            return f"{base}\n\n{section}\n"
        return f"{section}\n"

    start, end = bounds
    before = text[:start].rstrip("\n")
    after = text[end:].lstrip("\n").rstrip("\n")
    parts = [part for part in (before, section, after) if part]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    args = parse_args()
    content = read_content(args)
    current = args.path.read_text(encoding="utf-8") if args.path.exists() else ""
    updated = upsert_section(current, args.level, args.heading, content)

    args.path.parent.mkdir(parents=True, exist_ok=True)
    args.path.write_text(updated, encoding="utf-8", newline="\n")
    print(f"updated {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
