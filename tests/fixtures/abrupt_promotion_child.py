from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from test_case_agent.review_cycle.promotion import build_validate_promote_review_cycle


ABRUPT_EXIT_CODE = 97


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--cycle-dir", type=Path, required=True)
    parser.add_argument("--basis-path", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    args = parser.parse_args()

    def terminate(phase: str) -> None:
        if phase == args.phase:
            os._exit(ABRUPT_EXIT_CODE)

    build_validate_promote_review_cycle(
        repo_root=args.repo_root,
        cycle_dir=args.cycle_dir,
        basis_path=args.basis_path,
        fault_injector=terminate,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
