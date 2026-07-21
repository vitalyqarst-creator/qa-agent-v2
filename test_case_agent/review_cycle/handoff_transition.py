from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


TOP_LEVEL_SCALAR_RE = re.compile(
    r"(?m)^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*?)[ \t]*$"
)


class ReviewHandoffTransitionError(RuntimeError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewHandoffTransitionError(f"cannot load {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise ReviewHandoffTransitionError(f"{label} must be a JSON object: {path}")
    return payload


def _top_level_scalars(text: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip().strip("'\"")
        for match in TOP_LEVEL_SCALAR_RE.finditer(text)
    }


def _replace_top_level_scalar(
    text: str,
    *,
    key: str,
    expected: str,
    replacement: str,
) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}:[ \t]*(.*?)[ \t]*$")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ReviewHandoffTransitionError(
            f"workflow-state must contain exactly one top-level {key}"
        )
    actual = matches[0].group(1).strip().strip("'\"")
    if actual != expected:
        raise ReviewHandoffTransitionError(
            f"workflow-state {key} mismatch: expected={expected} actual={actual}"
        )
    return pattern.sub(f"{key}: {replacement}", text, count=1)


def _write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def transition_accepted_cycle_to_reviewer_handoff(
    *,
    repo_root: Path,
    cycle_dir: Path,
    handoff_dir: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cycle_dir = cycle_dir.resolve()
    handoff_dir = handoff_dir.resolve()
    try:
        cycle_relative = cycle_dir.relative_to(repo_root)
        handoff_relative = handoff_dir.relative_to(repo_root)
    except ValueError as exc:
        raise ReviewHandoffTransitionError(
            "cycle and handoff must be inside the repository"
        ) from exc
    if "work" not in cycle_relative.parts or "review-cycles" not in cycle_relative.parts:
        raise ReviewHandoffTransitionError("cycle_dir is not a review-cycle path")
    if "work" not in handoff_relative.parts or "stage-handoffs" not in handoff_relative.parts:
        raise ReviewHandoffTransitionError("handoff_dir is not a stage-handoff path")

    workflow_path = handoff_dir / "workflow-state.yaml"
    cycle_state_path = cycle_dir / "cycle-state.yaml"
    review_result_path = cycle_dir / "review-result.json"
    promotion_seed_path = cycle_dir / "promotion-basis.seed.json"
    writer_output = cycle_dir / "attempts" / "writer-r1" / "attempt-001" / "runner-output"
    reviewer_output = cycle_dir / "attempts" / "reviewer-r1" / "attempt-001" / "runner-output"
    required_paths = (
        workflow_path,
        cycle_state_path,
        review_result_path,
        promotion_seed_path,
        writer_output / "writer-gate-aggregate.json",
        writer_output / "evidence-access-report.json",
        reviewer_output / "evidence-access-report.json",
    )
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise ReviewHandoffTransitionError(
            "required accepted-cycle artifacts are missing: " + ", ".join(missing)
        )

    cycle_text = cycle_state_path.read_text(encoding="utf-8")
    cycle_state = _top_level_scalars(cycle_text)
    expected_cycle = {
        "workflow_status": "accepted-not-promoted",
        "stage_status": "accepted-not-promoted",
        "writer_stage_status": "completed",
        "reviewer_stage_status": "accepted",
        "accepted_terminal_state": "true",
        "final_promoted": "false",
    }
    cycle_mismatches = {
        key: {"expected": expected, "actual": cycle_state.get(key)}
        for key, expected in expected_cycle.items()
        if cycle_state.get(key) != expected
    }
    if cycle_mismatches:
        raise ReviewHandoffTransitionError(
            f"cycle is not accepted-not-promoted: {cycle_mismatches}"
        )

    review = _read_json(review_result_path, "normalized review result")
    if review.get("decision") != "accepted" or review.get("findings") not in ([], None):
        raise ReviewHandoffTransitionError(
            "normalized review result is not an accepted zero-finding result"
        )
    seed = _read_json(promotion_seed_path, "promotion seed")
    if not isinstance(seed.get("scope_slug"), str) or not seed.get("scope_slug"):
        raise ReviewHandoffTransitionError("promotion seed has no scope_slug")
    prompt_binding = (seed.get("available_builder_inputs") or {}).get("handoff_prompt")
    prompt_path = handoff_dir / "prompt.reviewer-to-ui-prep.md"
    if not isinstance(prompt_binding, dict) or not prompt_path.is_file():
        raise ReviewHandoffTransitionError("promotion seed has no bound handoff prompt")
    if prompt_binding.get("path") != prompt_path.relative_to(repo_root).as_posix():
        raise ReviewHandoffTransitionError("promotion seed points to another handoff")
    if prompt_binding.get("sha256") != _sha256_bytes(prompt_path.read_bytes()):
        raise ReviewHandoffTransitionError("bound handoff prompt hash mismatch")

    for label, path in (
        ("writer gate aggregate", writer_output / "writer-gate-aggregate.json"),
        ("writer evidence access", writer_output / "evidence-access-report.json"),
        ("reviewer evidence access", reviewer_output / "evidence-access-report.json"),
    ):
        report = _read_json(path, label)
        if report.get("passed") is not True:
            raise ReviewHandoffTransitionError(f"{label} did not pass")

    before = workflow_path.read_bytes()
    workflow_text = before.decode("utf-8")
    workflow = _top_level_scalars(workflow_text)
    if workflow.get("scope_slug") != seed.get("scope_slug"):
        raise ReviewHandoffTransitionError("workflow-state scope mismatch")
    receipt_path = cycle_dir / "review-handoff-transition.json"
    if (
        workflow.get("current_stage") == "ft-test-case-iteration"
        and workflow.get("stage_status") == "ready-for-review"
        and workflow.get("next_skill") == "ft-test-case-reviewer"
    ):
        if not receipt_path.is_file():
            raise ReviewHandoffTransitionError(
                "workflow-state is already reviewer-ready without a transition receipt"
            )
        receipt = _read_json(receipt_path, "review handoff transition receipt")
        if receipt.get("after_sha256") != _sha256_bytes(before):
            raise ReviewHandoffTransitionError("transition receipt is stale")
        return {**receipt, "status": "reused"}

    expected_before = {
        "current_stage": "ft-test-case-iteration",
        "stage_status": "ready-for-next-stage",
        "next_skill": "ft-test-case-iteration",
    }
    mismatches = {
        key: {"expected": expected, "actual": workflow.get(key)}
        for key, expected in expected_before.items()
        if workflow.get(key) != expected
    }
    if mismatches:
        raise ReviewHandoffTransitionError(
            f"workflow-state is not an eligible iteration handoff: {mismatches}"
        )

    after_text = _replace_top_level_scalar(
        workflow_text,
        key="stage_status",
        expected="ready-for-next-stage",
        replacement="ready-for-review",
    )
    after_text = _replace_top_level_scalar(
        after_text,
        key="next_skill",
        expected="ft-test-case-iteration",
        replacement="ft-test-case-reviewer",
    )
    after = after_text.encode("utf-8")
    receipt: dict[str, Any] = {
        "version": 1,
        "status": "transitioned",
        "validator": "accepted-cycle-review-handoff-transition-v1",
        "cycle_dir": cycle_relative.as_posix(),
        "workflow_state": handoff_relative.joinpath("workflow-state.yaml").as_posix(),
        "before_sha256": _sha256_bytes(before),
        "after_sha256": _sha256_bytes(after),
        "review_result_sha256": _sha256_bytes(review_result_path.read_bytes()),
        "promotion_seed_sha256": _sha256_bytes(promotion_seed_path.read_bytes()),
        "transition": {
            "stage_status": ["ready-for-next-stage", "ready-for-review"],
            "next_skill": ["ft-test-case-iteration", "ft-test-case-reviewer"],
        },
    }
    # Persist the receipt first. If the workflow write is interrupted, the next
    # invocation still sees the eligible pre-state and can safely repeat both
    # writes. The reverse order could leave a reviewer-ready state without the
    # receipt required by the idempotent path.
    _write_atomic(
        receipt_path,
        (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    _write_atomic(workflow_path, after)
    return receipt
