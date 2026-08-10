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
import os
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import practical_review_preflight as review_preflight  # noqa: E402


TASK_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
# A controller subagent is not an independent review session.  Older v1
# receipts remain readable as historical evidence, but this dispatcher creates
# only the current separate-session protocol.
EXECUTION_SURFACES = {"codex-thread"}


def controller_identity_issues(
    launch: dict[str, Any],
    *,
    controller_task_id: str,
    reviewer_task_id: str,
) -> list[str]:
    """Prove that the controller, rather than a prior reviewer, dispatched review.

    The controller session persists its durable Codex thread id in every active
    workflow before it launches a reviewer.  The dispatch command reads the
    actual running task id from ``CODEX_THREAD_ID``; it does not accept a
    caller-supplied override.  This closes the reviewer -> reviewer chain that
    could otherwise look like independent review in an artifact alone.
    """

    issues: list[str] = []
    controller_task_id = controller_task_id.strip()
    if not TASK_ID_RE.fullmatch(controller_task_id):
        return ["controller CODEX_THREAD_ID is missing or is not a durable Codex thread id"]
    if controller_task_id.casefold() == reviewer_task_id.strip().casefold():
        issues.append("controller task id must differ from reviewer task id")

    required = ("ft_package_root", "scope_ids")
    if not all(launch.get(field) for field in required):
        # Minimal historical/test receipts remain readable.  Current practical
        # receipts always provide these fields and therefore use the strict path.
        return issues

    try:
        descriptors, descriptor_issues = review_preflight.scope_descriptors(
            Path(str(launch["ft_package_root"])),
            [str(value) for value in launch["scope_ids"]],
        )
    except (TypeError, ValueError, OSError) as exc:
        return [f"cannot verify controller session provenance: {exc}"]
    issues.extend(descriptor_issues)
    workflow_ids: set[str] = set()
    for descriptor in descriptors:
        try:
            state = review_preflight.artifact_validator.parse_workflow_state(
                descriptor.workflow_path
            )
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            issues.append(
                f"scope {descriptor.scope_id}: cannot read controller session provenance: {exc}"
            )
            continue
        workflow_id = str(state.get("controller_task_or_session") or "").strip()
        if not TASK_ID_RE.fullmatch(workflow_id):
            issues.append(
                f"scope {descriptor.scope_id}: controller_task_or_session is missing or invalid"
            )
            continue
        workflow_ids.add(workflow_id.casefold())
        if workflow_id.casefold() != controller_task_id.casefold():
            issues.append(
                f"scope {descriptor.scope_id}: controller_task_or_session differs from CODEX_THREAD_ID"
            )
    if len(workflow_ids) > 1:
        issues.append("active scopes do not share one controller_task_or_session")
    return issues


def current_controller_state_issues(
    launch_receipt: Path,
    launch: dict[str, Any],
) -> list[str]:
    """Reject dispatch when controller state changed after launch preflight.

    A reviewer task is created before its durable task id is known.  Checking
    the frozen controller state while writing its dispatch receipt moves a
    stale-summary failure to the controller, before it sends the reviewer the
    operational prompt.  Minimal legacy receipts remain readable in tests and
    historical evidence, but current receipts always contain this contract.
    """

    required = ("repo_root", "ft_package_root", "summary_path", "scope_ids", "review_mode")
    if not all(launch.get(field) for field in required):
        return []
    try:
        scope_ids = [str(value) for value in launch["scope_ids"]]
        current = review_preflight.build_preflight(
            repo_root=Path(str(launch["repo_root"])),
            ft_package_root=Path(str(launch["ft_package_root"])),
            summary_path=Path(str(launch["summary_path"])),
            scope_ids=scope_ids,
            review_mode=str(launch["review_mode"]),
        )
    except (KeyError, TypeError, ValueError, OSError) as exc:
        return [f"cannot verify controller state before reviewer dispatch: {exc}"]
    return review_preflight.verify_receipt(launch_receipt, current)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_dispatch_receipt(
    *,
    launch_receipt: Path,
    reviewer_task_id: str,
    reviewer_execution_surface: str,
    controller_task_id: str = "",
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
    if not errors:
        errors.extend(current_controller_state_issues(launch_receipt, launch))
    if not errors:
        errors.extend(
            controller_identity_issues(
                launch,
                controller_task_id=controller_task_id,
                reviewer_task_id=task_id,
            )
        )

    return {
        "schema_version": 3,
        "status": "dispatched" if not errors else "blocked",
        "allowed": not errors,
        "launch_receipt": launch_receipt.as_posix(),
        "launch_receipt_sha256": sha256_file(launch_receipt) if launch_receipt.is_file() else "",
        "reviewer_task_or_session": task_id,
        "reviewer_execution_surface": surface,
        "reviewer_thread_url_or_id": task_id,
        "controller_task_or_session": controller_task_id.strip(),
        "controller_execution_surface": "codex-thread",
        "controller_identity_verified": not errors,
        "controller_state_verified": not errors,
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
        controller_task_id=os.environ.get("CODEX_THREAD_ID", ""),
    )
    if result["allowed"]:
        output = args.output.resolve()
        if output.exists():
            result["allowed"] = False
            result["status"] = "blocked"
            result["controller_identity_verified"] = False
            result["controller_state_verified"] = False
            result["blocking_reasons"].append(
                "review dispatch receipt already exists; do not replace a prior review attempt"
            )
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
