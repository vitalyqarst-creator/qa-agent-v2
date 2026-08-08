"""Bind a practical review launch to the reviewer task created by controller.

The launch preflight is intentionally created before ``create_thread`` and
therefore cannot contain the reviewer task id.  This controller-owned receipt
is written immediately after task creation.  Review artifacts refer to the
receipt instead of claiming an id that the reviewer has to type manually.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


TASK_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
# A controller subagent is not an independent review session.  Older v1
# receipts remain readable as historical evidence, but this dispatcher creates
# only the current separate-session protocol.
EXECUTION_SURFACES = {"codex-thread"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_dispatch_receipt(
    *,
    launch_receipt: Path,
    reviewer_task_id: str,
    reviewer_execution_surface: str,
) -> dict[str, Any]:
    launch_receipt = launch_receipt.resolve()
    errors: list[str] = []
    try:
        launch = json.loads(launch_receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        launch = {}
        errors.append(f"cannot read launch receipt: {exc}")

    task_id = reviewer_task_id.strip()
    surface = reviewer_execution_surface.strip().casefold()
    if launch.get("allowed") is not True:
        errors.append("launch receipt is not allowed")
    if not TASK_ID_RE.fullmatch(task_id):
        errors.append("reviewer session id is not a durable Codex thread id")
    if surface not in EXECUTION_SURFACES:
        errors.append("reviewer execution surface must be codex-thread (a separate Codex session)")

    return {
        "schema_version": 2,
        "status": "dispatched" if not errors else "blocked",
        "allowed": not errors,
        "launch_receipt": launch_receipt.as_posix(),
        "launch_receipt_sha256": sha256_file(launch_receipt) if launch_receipt.is_file() else "",
        "reviewer_task_or_session": task_id,
        "reviewer_execution_surface": surface,
        "reviewer_thread_url_or_id": task_id,
        "blocking_reasons": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create controller-owned reviewer dispatch receipt for practical route."
    )
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument(
        "--reviewer-session-id",
        "--reviewer-task-id",
        dest="reviewer_session_id",
        required=True,
    )
    parser.add_argument(
        "--reviewer-execution-surface",
        choices=sorted(EXECUTION_SURFACES),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_dispatch_receipt(
        launch_receipt=args.launch_receipt,
        reviewer_task_id=args.reviewer_session_id,
        reviewer_execution_surface=args.reviewer_execution_surface,
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
