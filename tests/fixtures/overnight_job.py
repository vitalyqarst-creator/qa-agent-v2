from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument(
        "--classification",
        choices=(
            "completed",
            "transient",
            "scope-blocker",
            "infrastructure",
            "global-source-corruption",
            "global-repository-defect",
        ),
        required=True,
    )
    parser.add_argument("--reason", default="fixture outcome")
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=0)
    args = parser.parse_args()
    if args.sleep_seconds:
        time.sleep(args.sleep_seconds)
    args.attempt_dir.mkdir(parents=True, exist_ok=True)
    (args.attempt_dir / "attempt-result.json").write_text(
        json.dumps(
            {
                "classification": args.classification,
                "reason": args.reason,
                "result_links": [str(args.attempt_dir / "result.txt")],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (args.attempt_dir / "result.txt").write_text(
        args.classification + "\n", encoding="utf-8", newline="\n"
    )
    return args.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
