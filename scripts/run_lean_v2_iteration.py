from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.lean_v2 import LeanV2ContractError, run_lean_v2_iteration
from test_case_agent.lean_v2.backend import CodexExecStageBackend


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Run the deterministic-first lean-v2 test-case iteration over an "
            "already localized, hash-bound source packet."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--source-packet", type=Path, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--prepare-only", action="store_true")
    result.add_argument("--writer-response", type=Path)
    result.add_argument("--reviewer-response", type=Path)
    result.add_argument("--codex-command")
    result.add_argument(
        "--model-timeout-seconds",
        type=float,
        help="Optional explicit model deadline; omitted means no application-level timeout.",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    backend = CodexExecStageBackend(
        codex_command=args.codex_command,
        timeout_seconds=args.model_timeout_seconds,
    )
    try:
        result = run_lean_v2_iteration(
            repo_root=args.repo_root,
            source_packet=args.source_packet,
            output_dir=args.output_dir,
            prepare_only=args.prepare_only,
            writer_response=args.writer_response,
            reviewer_response=args.reviewer_response,
            backend=backend,
        )
    except LeanV2ContractError as exc:
        print(json.dumps({"status": "blocked-contract", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(
        json.dumps(
            {
                "status": result.status,
                "summary": str(result.summary_path),
                "draft": str(result.draft_path) if result.draft_path else None,
                "test_case_count": result.test_case_count,
            },
            ensure_ascii=False,
        )
    )
    return 0 if result.status in {"prepared", "accepted-shadow"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
