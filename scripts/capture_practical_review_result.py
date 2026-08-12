"""Copy a reviewer JSON submission byte-for-byte into immutable route evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MAX_COMPACT_REVIEW_SUBMISSION_BYTES = 24 * 1024

def capture(
    *, submission: Path, output: Path, max_bytes: int = MAX_COMPACT_REVIEW_SUBMISSION_BYTES
) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(f"review result already exists: {output}")
    raw = submission.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError(
            f"reviewer submission exceeds compact receipt limit: {len(raw)} > {max_bytes} bytes"
        )
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
        "bytes": len(raw),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, default=MAX_COMPACT_REVIEW_SUBMISSION_BYTES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = capture(
            submission=args.submission,
            output=args.output,
            max_bytes=args.max_bytes,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "blocked", "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "captured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
