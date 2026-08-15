"""Copy a reviewer JSON submission byte-for-byte into immutable route evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import COMPACT_REVIEWER_RECEIPT_MAX_BYTES


MAX_COMPACT_REVIEW_SUBMISSION_BYTES = COMPACT_REVIEWER_RECEIPT_MAX_BYTES


def max_bytes_from_manifest(manifest: Path) -> int:
    """Read the reviewer-visible byte bound from one immutable manifest."""
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    contract = payload.get("reviewer_receipt_contract")
    if not isinstance(contract, dict):
        return MAX_COMPACT_REVIEW_SUBMISSION_BYTES
    max_bytes = contract.get("max_bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 < max_bytes <= MAX_COMPACT_REVIEW_SUBMISSION_BYTES:
        raise ValueError(
            "reviewer_receipt_contract.max_bytes must be a positive integer "
            f"not greater than {MAX_COMPACT_REVIEW_SUBMISSION_BYTES}"
        )
    return max_bytes

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
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--manifest", type=Path)
    source.add_argument("--max-bytes", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        max_bytes = (
            max_bytes_from_manifest(args.manifest)
            if args.manifest is not None
            else args.max_bytes or MAX_COMPACT_REVIEW_SUBMISSION_BYTES
        )
        result = capture(
            submission=args.submission,
            output=args.output,
            max_bytes=max_bytes,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "blocked", "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "captured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
