from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.source_row_baseline import (  # noqa: E402
    build_source_row_baseline,
    load_extraction_spec,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Build the deterministic source-row baseline from one bounded XHTML extraction spec."
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--extraction-spec", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    return result


def _under(root: Path, value: Path, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes repository root: {path}") from exc
    return path


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    try:
        spec_path = _under(root, args.extraction_spec, "extraction spec")
        output = _under(root, args.output, "output")
        if output.exists():
            raise ValueError(f"output already exists: {output}")
        baseline = build_source_row_baseline(
            repo_root=root,
            spec=load_extraction_spec(spec_path),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(baseline.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(
            json.dumps(
                {
                    "status": "built",
                    "candidate_count": baseline.candidate_count,
                    "baseline_digest": baseline.digest,
                    "output": output.relative_to(root).as_posix(),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
