from __future__ import annotations

from pathlib import Path


def find_runtime_root(start: Path) -> Path | None:
    candidate = start.resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for current in (candidate, *candidate.parents):
        if (current / "AGENTS.md").is_file() and (current / "scripts").is_dir():
            return current
    return None


def validate_no_repository_temp(start: Path) -> list[str]:
    root = find_runtime_root(start)
    if root is None:
        return []
    temporary_root = root / "tmp"
    if not temporary_root.is_dir():
        return []
    files = sorted(path for path in temporary_root.rglob("*") if path.is_file())
    return [
        "repository-local temporary file is forbidden; use scripts/render_runtime_pdf.py "
        f"and the system temporary directory: {path.relative_to(root).as_posix()}"
        for path in files
    ]
