from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.bounded_scope_materializer import (  # noqa: E402
    materialize_bounded_scope,
)


def _load(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object expected: {path}")
    return payload


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Materialize one legacy v1 detailed bounded scope decision into compiler-v3 "
            "inputs; compact v2 requires a semantic-design author stage first."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--decision", type=Path, required=True)
    result.add_argument("--handoff-dir", type=Path, required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    try:
        context_path = args.context if args.context.is_absolute() else root / args.context
        decision_path = args.decision if args.decision.is_absolute() else root / args.decision
        handoff = args.handoff_dir if args.handoff_dir.is_absolute() else root / args.handoff_dir
        result = materialize_bounded_scope(
            repo_root=root,
            context=_load(context_path.resolve()),
            decision=_load(decision_path.resolve()),
            handoff_dir=handoff,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001 - terminal CLI boundary.
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
