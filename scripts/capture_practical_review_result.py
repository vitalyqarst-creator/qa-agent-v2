"""Copy a reviewer JSON submission byte-for-byte into immutable route evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def capture(*, submission: Path, output: Path) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(f"review result already exists: {output}")
    raw = submission.read_bytes()
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("reviewer submission must be one JSON object")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(raw)
    if output.read_bytes() != raw:
        raise RuntimeError("captured review result differs from reviewer submission")
    return {
        "status": "captured",
        "submission": submission.resolve().as_posix(),
        "output": output.resolve().as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = capture(submission=args.submission, output=args.output)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "blocked", "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "captured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
