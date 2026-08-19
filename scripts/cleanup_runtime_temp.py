from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

try:
    from scripts.runtime_io import configure_utf8_stdio
except ModuleNotFoundError:  # Direct invocation
    from runtime_io import configure_utf8_stdio


SAFE_PREFIX = "ft-runtime-"


def cleanup(paths: list[Path]) -> tuple[list[str], list[str]]:
    temp_root = Path(tempfile.gettempdir()).resolve()
    removed: list[str] = []
    errors: list[str] = []
    for raw_path in paths:
        target = raw_path.resolve()
        try:
            target.relative_to(temp_root)
        except ValueError:
            errors.append(f"temporary path is outside system temp: {target}")
            continue
        if target == temp_root or not target.name.startswith(SAFE_PREFIX):
            errors.append(f"temporary path is not an isolated {SAFE_PREFIX} directory: {target}")
            continue
        if not target.exists() and not target.is_symlink():
            continue
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
        removed.append(str(target))
    return removed, errors


def main() -> int:
    configure_utf8_stdio()
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Safely remove isolated FT runtime artifacts from the system temporary directory."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    removed, errors = cleanup(args.paths)
    print(json.dumps({"valid": not errors, "removed": removed, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
