from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.handoff_transition import (
    ReviewHandoffTransitionError,
    transition_accepted_cycle_to_reviewer_handoff,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transition one accepted cycle handoff to reviewer-ready state."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--cycle-dir", required=True)
    parser.add_argument("--handoff-dir", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        result = transition_accepted_cycle_to_reviewer_handoff(
            repo_root=repo_root,
            cycle_dir=repo_root / args.cycle_dir,
            handoff_dir=repo_root / args.handoff_dir,
        )
    except ReviewHandoffTransitionError as exc:
        print(json.dumps({"status": "blocked-input", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
