"""Preflight one raw reviewer JSON submission before it is sent to controller."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capture_practical_review_result import (
    MAX_COMPACT_REVIEW_SUBMISSION_BYTES,
    max_bytes_from_manifest,
)


def validate_submission(*, manifest: Path, submission: Path) -> dict[str, object]:
    max_bytes = max_bytes_from_manifest(manifest)
    raw = submission.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError(
            f"reviewer submission exceeds manifest limit: {len(raw)} > {max_bytes} bytes"
        )
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("reviewer submission must be one JSON object")
    return {
        "status": "valid",
        "submission": submission.resolve().as_posix(),
        "bytes": len(raw),
        "max_bytes": max_bytes,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = validate_submission(manifest=args.manifest, submission=args.submission)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "blocked", "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
