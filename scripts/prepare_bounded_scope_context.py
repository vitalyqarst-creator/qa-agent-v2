from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.source_preparation import (  # noqa: E402
    SourcePreparationError,
    prepare_bounded_scope_context,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Build or reuse one hash-bound bounded scope context and source-row baseline."
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context-template", type=Path, required=True)
    result.add_argument("--cache-dir", type=Path, default=Path(".codex-temp/source-preparation-cache"))
    result.add_argument("--output-context", type=Path, required=True)
    result.add_argument("--output-baseline", type=Path, required=True)
    result.add_argument("--allow-overwrite", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = prepare_bounded_scope_context(
            repo_root=args.repo_root,
            context_template=args.context_template,
            cache_dir=args.cache_dir,
            output_context=args.output_context,
            output_baseline=args.output_baseline,
            allow_overwrite=args.allow_overwrite,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, SourcePreparationError) as exc:
        print(
            json.dumps(
                {"status": "blocked", "error_type": type(exc).__name__, "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
