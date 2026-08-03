from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write a Markdown artifact from UTF-8 section files. This helper avoids "
            "passing large Markdown bodies through shell arguments, PowerShell "
            "here-strings, or inline generator commands."
        )
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help=(
            "UTF-8 JSON manifest with target path and ordered section content files. "
            "Relative paths are resolved from the manifest directory."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate manifest and print the target path without writing.",
    )
    return parser.parse_args()


def resolve_manifest_path(manifest_path: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return manifest_path.parent / path


def read_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ValueError("Manifest root must be a JSON object.")
    return manifest


def require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`{field_name}` must be a non-empty string.")
    return value


def require_level(value: Any) -> int:
    if not isinstance(value, int) or value < 1 or value > 6:
        raise ValueError("Section `level` must be an integer from 1 to 6.")
    return value


def render_heading(level: int, heading: str) -> str:
    return f"{'#' * level} {heading.strip()}"


def read_optional_file(manifest_path: Path, raw_path: Any, field_name: str) -> str:
    if raw_path in (None, "", "-"):
        return ""
    file_path = resolve_manifest_path(manifest_path, require_string(raw_path, field_name))
    return file_path.read_text(encoding="utf-8").strip("\n")


def render_artifact(manifest_path: Path, manifest: dict[str, Any]) -> tuple[Path, str]:
    target_path = resolve_manifest_path(
        manifest_path,
        require_string(manifest.get("target_path"), "target_path"),
    )

    sections = manifest.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("`sections` must be a non-empty list.")

    parts: list[str] = []
    preamble = read_optional_file(manifest_path, manifest.get("preamble_file"), "preamble_file")
    if preamble:
        parts.append(preamble)

    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            raise ValueError(f"Section #{index} must be a JSON object.")
        level = require_level(section.get("level", 2))
        heading = require_string(section.get("heading"), f"sections[{index}].heading")
        content = read_optional_file(
            manifest_path,
            section.get("content_file"),
            f"sections[{index}].content_file",
        )
        section_text = render_heading(level, heading)
        if content:
            section_text = f"{section_text}\n\n{content}"
        parts.append(section_text)

    return target_path, "\n\n".join(parts).rstrip("\n") + "\n"


def main() -> int:
    args = parse_args()
    try:
        manifest_path = args.manifest.resolve()
        manifest = read_manifest(manifest_path)
        target_path, content = render_artifact(manifest_path, manifest)
        if args.dry_run:
            print(f"validated {target_path}")
            return 0
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {target_path}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should report all manifest errors.
        print(f"write_artifact_sections.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
