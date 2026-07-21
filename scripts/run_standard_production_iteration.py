from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_lean_production_iteration import main as downstream_main  # noqa: E402
from scripts.run_standard_scope_bridge import (  # noqa: E402
    load_published_handoff_receipt,
    main as bridge_main,
)
from test_case_agent.bounded_scope_boundary import (  # noqa: E402
    BoundedScopeBoundaryError,
    validate_stable_path_segment,
)
from test_case_agent.semantic_design_bridge import (  # noqa: E402
    prepared_context_sha256,
)
from test_case_agent.review_cycle.prepared_compiler import (  # noqa: E402
    load_workflow_state,
)


class StandardProductionIterationError(ValueError):
    pass


def _under(root: Path, value: Path, *, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise StandardProductionIterationError(
            f"{label} escapes repository root: {path}"
        ) from exc
    return path


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StandardProductionIterationError(
            f"cannot read {label}: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise StandardProductionIterationError(
            f"{label} must be a JSON object: {path}"
        )
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _print_best_effort(payload: Mapping[str, Any], *, error: bool = False) -> None:
    try:
        print(
            json.dumps(payload, ensure_ascii=False, indent=2),
            file=sys.stderr if error else sys.stdout,
        )
    except Exception:
        pass


def _option(args: list[str], name: str, value: str | Path | None) -> None:
    if value is not None:
        args.extend((name, str(value)))


def _context_package_id(context: Path) -> str:
    payload = _load_json(context, label="prepared context")
    package_id = payload.get("package_id")
    if (
        not isinstance(package_id, str)
        or not package_id.strip()
        or package_id != package_id.strip()
    ):
        raise StandardProductionIterationError(
            "prepared context.package_id must be a non-empty exact string"
        )
    return package_id


def _verify_materialized_package_id(
    semantic_design: Path,
    *,
    expected: str,
) -> None:
    payload = _load_json(semantic_design, label="materialized semantic design")
    obligations = payload.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        raise StandardProductionIterationError(
            "materialized semantic design must contain obligations before downstream"
        )
    package_ids: set[str] = set()
    for index, obligation in enumerate(obligations):
        if not isinstance(obligation, Mapping):
            raise StandardProductionIterationError(
                f"materialized semantic design obligations[{index}] must be an object"
            )
        package_id = obligation.get("package_id")
        if not isinstance(package_id, str) or not package_id.strip():
            raise StandardProductionIterationError(
                "materialized semantic design obligation misses package_id: "
                f"index {index}"
            )
        package_ids.add(package_id)
    if package_ids != {expected}:
        raise StandardProductionIterationError(
            "materialized semantic design package_id mismatch: "
            f"context={expected!r}, materialized={sorted(package_ids)!r}"
        )


def _workflow_artifact_path(
    workflow_state: Path,
    *,
    ft_root: Path,
    key: str,
) -> Path:
    state = load_workflow_state(workflow_state)
    latest = state.get("latest_artifacts")
    if not isinstance(latest, Mapping):
        raise StandardProductionIterationError(
            "materialized workflow-state latest_artifacts must be a mapping"
        )
    raw = latest.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise StandardProductionIterationError(
            f"materialized workflow-state latest_artifacts.{key} is required"
        )
    return _under(ft_root, Path(raw), label=f"workflow artifact {key}")


_MODEL_PHASES = ("scope-analysis", "semantic-design")
_DOWNSTREAM_PHASES = (
    "source-review",
    "compile-preflight",
    "writer-reviewer",
    "promotion",
)
_STAGE_ATTEMPT_ID = re.compile(r"attempt-[0-9]{3}")
_MODEL_STAGE_ID = re.compile(r"(writer|reviewer)-r[1-9][0-9]*")
_MODEL_STAGE_ROLES = {"writer", "reviewer"}


def _count_pair(payload: Mapping[str, Any]) -> tuple[int, int] | None:
    attempt_count = payload.get("attempt_count")
    retry_count = payload.get("retry_count")
    if (
        type(attempt_count) is int
        and attempt_count >= 0
        and type(retry_count) is int
        and retry_count >= 0
        and retry_count <= attempt_count
    ):
        return attempt_count, retry_count
    return None


def _phase_count_pair(payload: Mapping[str, Any]) -> tuple[int, int] | None:
    lifecycle = payload.get("lifecycle")
    if not isinstance(lifecycle, Mapping):
        return None
    return _count_pair(
        {
            "attempt_count": lifecycle.get("runner_attempt_count"),
            "retry_count": lifecycle.get("runner_retry_count"),
        }
    )


def _phase_can_continue(payload: Mapping[str, Any]) -> bool | None:
    if "status" not in payload and "decision" not in payload:
        return None
    return payload.get("status") == "completed" and payload.get("decision") == "ready"


def _timer_phase_counts(
    timer: Path | None,
    *,
    invocation_started_epoch_ms: int,
    preexisting_phase_digests: Sequence[str] | None,
    preexisting_phase_snapshot_error: str | None,
) -> tuple[
    dict[str, tuple[int, int]],
    set[str],
    dict[str, bool | None],
    str | None,
]:
    if preexisting_phase_digests is None:
        return {}, set(), {}, (
            preexisting_phase_snapshot_error
            or "bridge timer phase snapshot is unavailable"
        )
    if timer is None or not timer.is_file():
        return {}, set(), {}, "caller-owned timer is unavailable after bridge"
    try:
        payload = json.loads(timer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, set(), {}, "caller-owned timer is unreadable after bridge"
    if not isinstance(payload, Mapping) or not isinstance(
        payload.get("phases"), list
    ):
        return {}, set(), {}, "caller-owned timer has no phase array after bridge"
    phase_items = payload["phases"]
    if len(phase_items) < len(preexisting_phase_digests):
        return {}, set(), {}, "caller-owned timer lost pre-bridge phases"
    for index, expected_digest in enumerate(preexisting_phase_digests):
        item = phase_items[index]
        if not isinstance(item, Mapping):
            return {}, set(), {}, f"caller-owned timer phase[{index}] is not an object"
        actual_digest = hashlib.sha256(
            json.dumps(
                item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        if actual_digest != expected_digest:
            return {}, set(), {}, f"caller-owned timer rewrote pre-bridge phase[{index}]"
    result: dict[str, tuple[int, int]] = {}
    observed: set[str] = set()
    continuation: dict[str, bool | None] = {}
    for item in phase_items[len(preexisting_phase_digests):]:
        if not isinstance(item, Mapping):
            continue
        phase = item.get("phase")
        started_epoch_ms = item.get("started_epoch_ms")
        if (
            phase not in _MODEL_PHASES
            or type(started_epoch_ms) is not int
            or started_epoch_ms < invocation_started_epoch_ms
        ):
            continue
        if phase in observed:
            return {}, set(), {}, f"duplicate current bridge timer phase: {phase}"
        observed.add(str(phase))
        metrics = item.get("metrics")
        if not isinstance(metrics, Mapping):
            continue
        stage_summary = metrics.get("stage_summary")
        if isinstance(stage_summary, Mapping):
            continuation[str(phase)] = _phase_can_continue(stage_summary)
        counts = (
            _phase_count_pair(stage_summary)
            if isinstance(stage_summary, Mapping)
            else _phase_count_pair({"lifecycle": metrics.get("lifecycle")})
        )
        if counts is not None:
            result[str(phase)] = counts
    return result, observed, continuation, None


def _recover_lifecycle_counts(
    *,
    runtime_dir: Path,
    timer: Path | None,
    bridge_summary: Mapping[str, Any],
    handoff_appeared: bool,
    phase_summary_absent_before: Mapping[str, bool],
    invocation_started_epoch_ms: int,
    preexisting_timer_phase_digests: Sequence[str] | None,
    preexisting_timer_phase_snapshot_error: str | None,
) -> tuple[tuple[int, int] | None, dict[str, Any]]:
    counts_by_phase: dict[str, tuple[int, int]] = {}
    observed_phases: set[str] = set()
    sources: dict[str, str] = {}
    continuation: dict[str, bool | None] = {}
    for phase in _MODEL_PHASES:
        path = runtime_dir / phase / "summary.json"
        if not phase_summary_absent_before.get(phase, False) or not path.is_file():
            continue
        observed_phases.add(phase)
        try:
            payload = _load_json(path, label=f"{phase} recovery summary")
        except StandardProductionIterationError:
            continue
        continuation[phase] = _phase_can_continue(payload)
        counts = _phase_count_pair(payload)
        if counts is not None:
            counts_by_phase[phase] = counts
            sources[phase] = "phase-summary"

    (
        timer_counts,
        timer_observed,
        timer_continuation,
        timer_evidence_error,
    ) = _timer_phase_counts(
        timer,
        invocation_started_epoch_ms=invocation_started_epoch_ms,
        preexisting_phase_digests=preexisting_timer_phase_digests,
        preexisting_phase_snapshot_error=preexisting_timer_phase_snapshot_error,
    )
    observed_phases.update(timer_observed)
    for phase, can_continue in timer_continuation.items():
        continuation.setdefault(phase, can_continue)
    for phase, counts in timer_counts.items():
        if phase not in counts_by_phase:
            counts_by_phase[phase] = counts
            sources[phase] = "timer"

    stopped_after = bridge_summary.get("stopped_after")
    if handoff_appeared or stopped_after in {
        "semantic-design",
        "scope-materialization",
    }:
        required_phases = set(_MODEL_PHASES)
    elif stopped_after == "scope-analysis":
        required_phases = {"scope-analysis"}
    elif "semantic-design" in observed_phases:
        required_phases = set(_MODEL_PHASES)
    elif "scope-analysis" in observed_phases:
        required_phases = (
            {"scope-analysis"}
            if continuation.get("scope-analysis") is False
            else set(_MODEL_PHASES)
        )
    else:
        required_phases = set()

    missing_phases = sorted(required_phases - counts_by_phase.keys())
    evidence = {
        "status": "unknown",
        "source": "unavailable",
        "required_phases": sorted(required_phases),
        "observed_phases": sorted(observed_phases),
        "missing_phases": missing_phases,
        **(
            {"timer_evidence_error": timer_evidence_error}
            if timer_evidence_error
            else {}
        ),
    }
    if not required_phases or missing_phases:
        return None, evidence
    attempt_count = sum(counts_by_phase[item][0] for item in required_phases)
    retry_count = sum(counts_by_phase[item][1] for item in required_phases)
    evidence.update(
        {
            "status": "recovered",
            "source": "authoritative-phase-evidence",
            "phase_sources": {
                phase: sources[phase] for phase in sorted(required_phases)
            },
        }
    )
    return (attempt_count, retry_count), evidence


def _source_review_count_pair(payload: Mapping[str, Any]) -> tuple[int, int] | None:
    """Read one current source-review invocation without inventing retries.

    Current bounded-sharded reviews use multiple fresh sessions and zero retries.
    Legacy one-shot v1 summaries predate the shared retry field, so their missing
    retry_count remains derivable from attempt_count.
    """

    attempt_count = payload.get("attempt_count")
    if type(attempt_count) is not int or attempt_count < 0:
        return None
    retry_count = payload.get("retry_count")
    if payload.get("execution_route") == "bounded-sharded":
        shard_count = payload.get("review_shard_count")
        if (
            type(retry_count) is not int
            or retry_count != 0
            or type(shard_count) is not int
            or shard_count < 2
            or attempt_count != shard_count
            or payload.get("model_session_count") != shard_count
        ):
            return None
        return attempt_count, retry_count
    if retry_count is None:
        retry_count = max(0, attempt_count - 1)
    if (
        type(retry_count) is not int
        or retry_count < 0
        or retry_count != max(0, attempt_count - 1)
    ):
        return None
    return attempt_count, retry_count


def _snapshot_json_file(
    path: Path,
    *,
    label: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return {
            "path": str(path.resolve()),
            "exists": False,
            "sha256": None,
            "payload": None,
        }, None
    if not path.is_file():
        return None, f"{label} is not a file: {path}"
    try:
        payload = _load_json(path, label=label)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, StandardProductionIterationError) as exc:
        return None, str(exc)
    return {
        "path": str(path.resolve()),
        "exists": True,
        "sha256": digest,
        "payload": payload,
    }, None


def _source_reuse_receipt_is_canonical(
    payload: Mapping[str, Any],
    *,
    persisted_summary_snapshot: Mapping[str, Any],
    preexisting_review_snapshot: Mapping[str, Any],
    current_review_snapshot: Mapping[str, Any],
) -> bool:
    if not (
        payload.get("version") == 1
        and type(payload.get("version")) is int
        and payload.get("status") == "reused"
        and type(payload.get("attempt_count")) is int
        and payload.get("attempt_count") == 0
        and type(payload.get("retry_count")) is int
        and payload.get("retry_count") == 0
    ):
        return False
    reuse_evidence = payload.get("reuse_evidence")
    if not isinstance(reuse_evidence, Mapping):
        return False
    review_evidence = reuse_evidence.get("source_assertion_review")
    summary_evidence = reuse_evidence.get("persisted_summary")
    if not isinstance(review_evidence, Mapping) or not isinstance(
        summary_evidence, Mapping
    ):
        return False
    review_path = review_evidence.get("path")
    review_digest = review_evidence.get("sha256")
    if not (
        isinstance(review_path, str)
        and review_path.strip()
        and isinstance(review_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", review_digest)
    ):
        return False
    review_unchanged = (
        preexisting_review_snapshot.get("exists") is True
        and current_review_snapshot.get("exists") is True
        and preexisting_review_snapshot.get("path")
        == current_review_snapshot.get("path")
        and preexisting_review_snapshot.get("sha256")
        == current_review_snapshot.get("sha256")
    )
    if not review_unchanged:
        return False
    return (
        review_path == current_review_snapshot.get("path")
        and review_digest == current_review_snapshot.get("sha256")
        and summary_evidence.get("path")
        == persisted_summary_snapshot.get("path")
        and summary_evidence.get("sha256")
        == persisted_summary_snapshot.get("sha256")
    )


def _stage_metric_identity(
    item: Mapping[str, Any],
    *,
    label: str,
) -> tuple[str, str, str]:
    stage_id = item.get("stage_id")
    attempt_id = item.get("attempt_id")
    role = item.get("role")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (stage_id, attempt_id, role)
    ):
        raise StandardProductionIterationError(
            f"{label} misses stage/attempt/role identity"
        )
    if role not in _MODEL_STAGE_ROLES:
        raise StandardProductionIterationError(
            f"{label}.role must be writer or reviewer"
        )
    stage_match = _MODEL_STAGE_ID.fullmatch(str(stage_id))
    if stage_match is None or stage_match.group(1) != role:
        raise StandardProductionIterationError(
            f"{label} role/stage_id identity is inconsistent"
        )
    attempt_match = _STAGE_ATTEMPT_ID.fullmatch(str(attempt_id))
    if (
        attempt_match is None
        or not 1 <= int(str(attempt_id).removeprefix("attempt-")) <= 999
    ):
        raise StandardProductionIterationError(
            f"{label}.attempt_id is not canonical"
        )
    return str(stage_id), str(attempt_id), str(role)


def _snapshot_writer_reviewer_metrics(
    cycle_dir: Path,
) -> tuple[dict[tuple[str, str, str], dict[str, Any]] | None, str | None]:
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in sorted(cycle_dir.glob("attempts/*/*/metrics.json")):
        try:
            payload = _load_json(path, label="writer/reviewer stage metric")
            identity = _stage_metric_identity(
                payload, label=f"stage metric {path}"
            )
            stage_id, attempt_id, _role = identity
            if (
                path.parent.name != attempt_id
                or path.parent.parent.name != stage_id
            ):
                raise StandardProductionIterationError(
                    "stage metric payload identity does not match its "
                    f"attempts/<stage_id>/<attempt_id> path: {path}"
                )
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError, StandardProductionIterationError) as exc:
            return None, str(exc)
        if identity in result:
            return None, f"duplicate writer/reviewer metric identity: {identity!r}"
        result[identity] = {
            "path": str(path.resolve()),
            "sha256": digest,
            "payload": payload,
        }
    return result, None


def _writer_reviewer_count_pair(
    stage_metrics: Any,
    *,
    require_both_roles: bool,
    preexisting_metrics: Mapping[tuple[str, str, str], Mapping[str, Any]],
    current_metrics: Mapping[tuple[str, str, str], Mapping[str, Any]],
    explicit_reuse: bool,
) -> tuple[tuple[int, int] | None, dict[str, Any]]:
    if stage_metrics is None and explicit_reuse:
        # Reuse is accepted only after the immutable pre/post snapshots below
        # prove that no current metric appeared or changed.
        stage_metrics = []
    if not isinstance(stage_metrics, list):
        return None, {"error": "stage_metrics is missing"}
    identities: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for index, item in enumerate(stage_metrics):
        if not isinstance(item, Mapping):
            return None, {"error": f"stage_metrics[{index}] is not an object"}
        try:
            identity = _stage_metric_identity(
                item, label=f"stage_metrics[{index}]"
            )
        except StandardProductionIterationError as exc:
            return None, {"error": str(exc)}
        previous = identities.get(identity)
        if previous is not None and dict(previous) != dict(item):
            return None, {"error": f"conflicting duplicate stage metric: {identity!r}"}
        identities[identity] = item
    overwritten = [
        identity
        for identity in preexisting_metrics.keys() & current_metrics.keys()
        if (
            preexisting_metrics[identity].get("path")
            != current_metrics[identity].get("path")
            or preexisting_metrics[identity].get("sha256")
            != current_metrics[identity].get("sha256")
        )
    ]
    deleted = set(preexisting_metrics) - set(current_metrics)
    if deleted:
        return None, {
            "error": "preexisting stage metric identity was deleted",
            "deleted_identities": [list(item) for item in sorted(deleted)],
        }
    if overwritten:
        return None, {
            "error": "preexisting stage metric identity was overwritten",
            "conflicting_identities": [list(item) for item in sorted(overwritten)],
        }
    fresh_ids = set(current_metrics) - set(preexisting_metrics)
    unbacked_ids = set(identities) - set(current_metrics)
    missing_timer_ids = fresh_ids - set(identities)
    if unbacked_ids or missing_timer_ids:
        return None, {
            "error": "timer and current cycle metric identities disagree",
            "unbacked_timer_identities": [list(item) for item in sorted(unbacked_ids)],
            "fresh_identities_missing_from_timer": [
                list(item) for item in sorted(missing_timer_ids)
            ],
        }
    for identity in set(identities) & set(current_metrics):
        if dict(identities[identity]) != dict(current_metrics[identity]["payload"]):
            return None, {
                "error": "timer metric conflicts with the persisted metric",
                "conflicting_identity": list(identity),
            }
    identities = {
        identity: payload
        for identity, payload in identities.items()
        if identity in fresh_ids
    }
    if explicit_reuse and identities:
        return None, {"error": "explicit reuse conflicts with fresh stage metrics"}
    if not identities:
        if explicit_reuse:
            return (0, 0), {"reuse_status": "explicit-current-phase-reuse"}
        return None, {"error": "stage_metrics contains only preexisting identities"}
    roles = {identity[2] for identity in identities}
    if require_both_roles and not {"writer", "reviewer"}.issubset(roles):
        return None, {
            "error": "completed writer-reviewer phase misses writer or reviewer metrics",
            "observed_roles": sorted(roles),
        }
    retry_count = sum(
        int(attempt_id.removeprefix("attempt-")) > 1
        for _stage_id, attempt_id, _role in identities
    )
    return (len(identities), retry_count), {
        "stage_metric_identities": [
            {"stage_id": stage, "attempt_id": attempt, "role": role}
            for stage, attempt, role in sorted(identities)
        ],
        "observed_roles": sorted(roles),
        "ignored_preexisting_identity_count": len(
            set(preexisting_metrics) & set(current_metrics)
        ),
    }


def _current_downstream_timer_phases(
    timer: Path | None,
    *,
    invocation_started_epoch_ms: int,
    preexisting_phase_digests: Sequence[str] | None,
    preexisting_phase_snapshot_error: str | None,
) -> tuple[dict[str, Mapping[str, Any]] | None, str | None]:
    if preexisting_phase_digests is None:
        return None, preexisting_phase_snapshot_error or "timer phase snapshot is unavailable"
    if timer is None or not timer.is_file():
        return None, "caller-owned timer is unavailable"
    try:
        payload = json.loads(timer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "caller-owned timer is unreadable"
    if not isinstance(payload, Mapping) or not isinstance(payload.get("phases"), list):
        return None, "caller-owned timer has no phase array"
    phase_items = payload["phases"]
    if len(phase_items) < len(preexisting_phase_digests):
        return None, "caller-owned timer lost preexisting phases"
    for index, expected_digest in enumerate(preexisting_phase_digests):
        item = phase_items[index]
        if not isinstance(item, Mapping):
            return None, f"caller-owned timer phase[{index}] is not an object"
        actual_digest = hashlib.sha256(
            json.dumps(
                item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        if actual_digest != expected_digest:
            return None, f"caller-owned timer rewrote preexisting phase[{index}]"
    result: dict[str, Mapping[str, Any]] = {}
    for item in phase_items[len(preexisting_phase_digests):]:
        if not isinstance(item, Mapping):
            continue
        phase = item.get("phase")
        started_epoch_ms = item.get("started_epoch_ms")
        if (
            phase not in _DOWNSTREAM_PHASES
            or type(started_epoch_ms) is not int
            or started_epoch_ms < invocation_started_epoch_ms
        ):
            continue
        if phase in result:
            return None, f"multiple current timer phases named {phase!r}"
        result[str(phase)] = item
    return result, None


def _snapshot_timer_phases(
    timer: Path | None,
) -> tuple[list[str] | None, str | None]:
    if timer is None:
        return None, "caller-owned timer is not configured"
    if not timer.is_file():
        return [], None
    try:
        payload = json.loads(timer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "caller-owned timer is unreadable before downstream"
    if not isinstance(payload, Mapping) or not isinstance(payload.get("phases"), list):
        return None, "caller-owned timer has no phase array before downstream"
    digests: list[str] = []
    for index, item in enumerate(payload["phases"]):
        if not isinstance(item, Mapping):
            return None, f"caller-owned timer phase[{index}] is not an object"
        digests.append(
            hashlib.sha256(
                json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        )
    return digests, None


def _recover_downstream_lifecycle_counts(
    *,
    timer: Path | None,
    cycle_dir: Path,
    invocation_started_epoch_ms: int,
    downstream_return_code: int | None,
    preexisting_source_summary: Mapping[str, Any] | None,
    preexisting_source_summary_error: str | None,
    expected_source_assertion_review: Path,
    preexisting_source_assertion_review: Mapping[str, Any] | None,
    preexisting_source_assertion_review_error: str | None,
    preexisting_stage_metrics: Mapping[
        tuple[str, str, str], Mapping[str, Any]
    ] | None,
    preexisting_stage_metrics_error: str | None,
    preexisting_timer_phase_digests: Sequence[str] | None,
    preexisting_timer_phase_snapshot_error: str | None,
) -> tuple[tuple[int, int] | None, dict[str, Any]]:
    phases, timer_error = _current_downstream_timer_phases(
        timer,
        invocation_started_epoch_ms=invocation_started_epoch_ms,
        preexisting_phase_digests=preexisting_timer_phase_digests,
        preexisting_phase_snapshot_error=preexisting_timer_phase_snapshot_error,
    )
    evidence: dict[str, Any] = {
        "status": "unknown",
        "source": "caller-owned-timer",
        "observed_phases": sorted(phases) if phases is not None else [],
        "stage_counts": {},
    }
    if phases is None:
        evidence["missing_evidence"] = [timer_error or "timer evidence unavailable"]
        return None, evidence
    if not phases:
        evidence["missing_evidence"] = [
            "downstream returned without a fresh instrumented phase"
        ]
        return None, evidence

    current_source_summary, current_source_summary_error = _snapshot_json_file(
        cycle_dir / "source-review-summary.json",
        label="current source-review summary",
    )
    if preexisting_source_summary is None or current_source_summary is None:
        evidence["missing_evidence"] = [
            preexisting_source_summary_error
            or current_source_summary_error
            or "source-review summary snapshot is unavailable"
        ]
        return None, evidence
    (
        current_source_assertion_review,
        current_source_assertion_review_error,
    ) = _snapshot_json_file(
        expected_source_assertion_review,
        label="current expected source-assertion review",
    )
    if (
        preexisting_source_assertion_review is None
        or current_source_assertion_review is None
    ):
        evidence["missing_evidence"] = [
            preexisting_source_assertion_review_error
            or current_source_assertion_review_error
            or "source-assertion review snapshot is unavailable"
        ]
        return None, evidence

    current_stage_metrics, current_stage_metrics_error = (
        _snapshot_writer_reviewer_metrics(cycle_dir)
    )
    if preexisting_stage_metrics is None or current_stage_metrics is None:
        evidence["missing_evidence"] = [
            preexisting_stage_metrics_error
            or current_stage_metrics_error
            or "writer/reviewer metric snapshot is unavailable"
        ]
        return None, evidence
    fresh_stage_metric_ids = set(current_stage_metrics) - set(
        preexisting_stage_metrics
    )

    missing: list[str] = []
    source_counts: tuple[int, int] | None = None
    source_phase = phases.get("source-review")
    if source_phase is not None:
        metrics = source_phase.get("metrics")
        source_summary = (
            metrics.get("summary") if isinstance(metrics, Mapping) else None
        )
        source_unchanged = (
            preexisting_source_summary.get("exists")
            == current_source_summary.get("exists")
            and preexisting_source_summary.get("sha256")
            == current_source_summary.get("sha256")
        )
        source_fresh = (
            preexisting_source_summary.get("exists") is False
            and current_source_summary.get("exists") is True
        )
        source_phase_status = source_phase.get("status")
        if isinstance(source_summary, Mapping):
            if (
                source_unchanged
                and _source_reuse_receipt_is_canonical(
                    source_summary,
                    persisted_summary_snapshot=current_source_summary,
                    preexisting_review_snapshot=(
                        preexisting_source_assertion_review
                    ),
                    current_review_snapshot=current_source_assertion_review,
                )
            ):
                source_counts = (0, 0)
            elif (
                source_fresh
                and dict(source_summary)
                == dict(current_source_summary.get("payload") or {})
            ):
                candidate_counts = _source_review_count_pair(source_summary)
                if (
                    source_phase_status == "completed"
                    and source_summary.get("status") == "completed"
                    and candidate_counts is not None
                    and candidate_counts[0] >= 1
                ):
                    source_counts = candidate_counts
                elif (
                    source_phase_status == "failed"
                    and source_summary.get("status") == "failed"
                    and isinstance(metrics, Mapping)
                    and metrics.get("model_attempt_evidence_complete") is True
                    and candidate_counts is not None
                ):
                    source_counts = candidate_counts
        if source_counts is None:
            missing.append("source-review attempt/retry evidence")
        else:
            evidence["stage_counts"]["source-review"] = {
                "attempt_count": source_counts[0],
                "retry_count": source_counts[1],
                "source": (
                    "current-phase-explicit-reuse"
                    if isinstance(source_summary, Mapping)
                    and source_summary.get("status") == "reused"
                    else (
                        "fresh-timer-stage-summary"
                        if source_fresh
                        else "fresh-source-review-summary"
                    )
                ),
            }
    elif any(name in phases for name in ("compile-preflight", "writer-reviewer", "promotion")):
        missing.append("source-review phase evidence")

    writer_counts: tuple[int, int] | None = None
    writer_phase = phases.get("writer-reviewer")
    if writer_phase is not None:
        metrics = writer_phase.get("metrics")
        stage_metrics = metrics.get("stage_metrics") if isinstance(metrics, Mapping) else None
        if stage_metrics is None and isinstance(metrics, Mapping):
            performance = metrics.get("performance")
            if isinstance(performance, Mapping):
                stage_metrics = performance.get("stage_metrics")
        reuse_receipt = (
            metrics.get("model_attempt_evidence")
            if isinstance(metrics, Mapping)
            else None
        )
        explicit_reuse = (
            isinstance(reuse_receipt, Mapping)
            and reuse_receipt.get("status") == "reused"
            and type(reuse_receipt.get("attempt_count")) is int
            and reuse_receipt.get("attempt_count") == 0
            and type(reuse_receipt.get("retry_count")) is int
            and reuse_receipt.get("retry_count") == 0
        )
        phase_completed = writer_phase.get("status") == "completed"
        writer_counts, writer_details = _writer_reviewer_count_pair(
            stage_metrics,
            require_both_roles=phase_completed or downstream_return_code == 0,
            preexisting_metrics=preexisting_stage_metrics,
            current_metrics=current_stage_metrics,
            explicit_reuse=explicit_reuse,
        )
        # On a failed orchestration phase the returned metrics cannot prove that
        # the failing model attempt itself was persisted.  A future runner may
        # assert completeness explicitly; until then the aggregate is unknown.
        if not phase_completed and not (
            isinstance(metrics, Mapping)
            and metrics.get("model_attempt_evidence_complete") is True
        ):
            writer_counts = None
            writer_details.setdefault(
                "error", "failed writer-reviewer phase has no completeness receipt"
            )
        if writer_counts is None:
            missing.append(str(writer_details.get("error", "writer-reviewer evidence")))
        else:
            evidence["stage_counts"]["writer-reviewer"] = {
                "attempt_count": writer_counts[0],
                "retry_count": writer_counts[1],
                "source": (
                    "current-phase-explicit-reuse"
                    if writer_details.get("reuse_status")
                    else "deduplicated-current-stage-metrics"
                ),
                **writer_details,
            }
    elif (
        downstream_return_code == 0
        or "promotion" in phases
        or bool(fresh_stage_metric_ids)
    ):
        missing.append(
            "downstream progression requires writer-reviewer phase evidence"
        )

    if downstream_return_code == 0:
        if source_phase is None:
            missing.append("successful downstream misses source-review phase evidence")
        if source_phase is not None and source_phase.get("status") != "completed":
            missing.append("successful downstream has non-completed source-review phase")
        if writer_phase is not None and writer_phase.get("status") != "completed":
            missing.append("successful downstream has non-completed writer-reviewer phase")

    if missing:
        evidence["missing_evidence"] = sorted(set(missing))
        return None, evidence
    components = [pair for pair in (source_counts, writer_counts) if pair is not None]
    if not components:
        evidence["missing_evidence"] = ["no downstream model lifecycle evidence"]
        return None, evidence
    counts = (
        sum(pair[0] for pair in components),
        sum(pair[1] for pair in components),
    )
    evidence.update(
        {
            "status": "recovered",
            "source": "fresh-downstream-stage-evidence",
        }
    )
    return counts, evidence


def _apply_total_lifecycle_counts(
    summary: dict[str, Any],
    *,
    downstream_invoked: bool,
) -> None:
    bridge = (
        summary.get("bridge_attempt_count"),
        summary.get("bridge_retry_count"),
    )
    downstream = (
        summary.get("downstream_attempt_count"),
        summary.get("downstream_retry_count"),
    )
    bridge_evidence = summary.get("bridge_lifecycle_count_evidence", {})
    downstream_evidence = summary.get("downstream_lifecycle_count_evidence", {})
    if not downstream_invoked:
        summary["attempt_count"], summary["retry_count"] = bridge
        summary["lifecycle_count_evidence"] = dict(bridge_evidence)
        return
    if not all(type(value) is int and value >= 0 for value in (*bridge, *downstream)):
        summary["attempt_count"] = None
        summary["retry_count"] = None
        summary["lifecycle_count_evidence"] = {
            "status": "unknown",
            "source": "bridge-and-downstream-components",
            "components": {
                "bridge": dict(bridge_evidence),
                "downstream": dict(downstream_evidence),
            },
        }
        return
    summary["attempt_count"] = int(bridge[0]) + int(downstream[0])
    summary["retry_count"] = int(bridge[1]) + int(downstream[1])
    statuses = {
        bridge_evidence.get("status"),
        downstream_evidence.get("status"),
    }
    summary["lifecycle_count_evidence"] = {
        "status": "verified" if statuses == {"verified"} else "recovered",
        "source": "bridge-and-downstream-components",
        "components": {
            "bridge": dict(bridge_evidence),
            "downstream": dict(downstream_evidence),
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Run the standard scope bridge and, only after its successful atomic "
            "handoff, the existing writer-reviewer production iteration once."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--runtime-dir", type=Path, required=True)
    result.add_argument("--handoff-dir", type=Path, required=True)
    result.add_argument("--cycle-dir", type=Path, required=True)
    result.add_argument("--final-artifact", type=Path, required=True)
    result.add_argument("--timer", type=Path)
    result.add_argument("--image", action="append", type=Path, default=[])
    result.add_argument("--codex-command")
    result.add_argument(
        "--measurement-mode",
        choices=("production", "observational"),
        default="observational",
    )
    result.add_argument(
        "--semantic-sharding",
        choices=("off", "auto", "on"),
        default="off",
    )
    result.add_argument("--semantic-shard-max-included-rows", type=int, default=12)
    result.add_argument("--semantic-shard-max-source-rows", type=int, default=18)
    result.add_argument("--semantic-shard-max-shards", type=int, default=8)
    result.add_argument("--semantic-shard-max-weight", type=int, default=0)
    return result


def main(
    argv: Sequence[str] | None = None,
    *,
    bridge_runner: Callable[[Sequence[str] | None], int] = bridge_main,
    downstream_runner: Callable[[Sequence[str] | None], int] = downstream_main,
) -> int:
    args = parser().parse_args(argv)
    started = time.perf_counter_ns()
    invocation_started_epoch_ms = time.time_ns() // 1_000_000
    summary: dict[str, Any] = {
        "version": 1,
        "route": "standard-production-iteration",
        "status": "running",
        "measurement_mode": args.measurement_mode,
        "attempt_count": 0,
        "retry_count": 0,
        "bridge_attempt_count": 0,
        "bridge_retry_count": 0,
        "downstream_attempt_count": 0,
        "downstream_retry_count": 0,
        "bridge_lifecycle_count_evidence": {
            "status": "verified",
            "source": "bridge-not-invoked",
        },
        "downstream_lifecycle_count_evidence": {
            "status": "verified",
            "source": "downstream-not-invoked",
        },
        "lifecycle_count_evidence": {
            "status": "verified",
            "source": "bridge-not-invoked",
        },
        "fallback_count": 0,
        "bridge": {"status": "not-run"},
        "downstream": {"status": "not-run"},
    }
    combined_summary_path: Path | None = None
    combined_summary_safe = False

    def add_reporting_error(
        stage: str,
        *,
        error_type: str,
        error: str,
        **details: Any,
    ) -> None:
        errors = summary.setdefault("reporting_errors", [])
        assert isinstance(errors, list)
        errors.append(
            {
                "stage": stage,
                "error_type": error_type,
                "error": error,
                **details,
            }
        )

    def finish(*, status: str, return_code: int) -> int:
        summary.update(
            {
                "status": status,
                "return_code": return_code,
                "duration_ms": (
                    time.perf_counter_ns() - started
                ) // 1_000_000,
            }
        )
        if combined_summary_path is not None and combined_summary_safe:
            try:
                _write_json_atomic(combined_summary_path, summary)
            except Exception as exc:  # noqa: BLE001 - final reporting boundary.
                add_reporting_error(
                    "combined-summary",
                    error_type=type(exc).__name__,
                    error=str(exc),
                    summary_output=str(combined_summary_path),
                )
        _print_best_effort(summary, error=return_code != 0)
        return return_code

    try:
        repo_root = args.repo_root.resolve()
        runtime_dir = _under(repo_root, args.runtime_dir, label="runtime-dir")
        combined_summary_path = (
            runtime_dir / "standard-production-iteration-summary.json"
        )
        bridge_summary_path = runtime_dir / "standard-scope-bridge-summary.json"
        context = _under(repo_root, args.context, label="context")
        handoff_dir = _under(repo_root, args.handoff_dir, label="handoff-dir")
        cycle_dir = _under(repo_root, args.cycle_dir, label="cycle-dir")
        final_artifact = _under(
            repo_root, args.final_artifact, label="final-artifact"
        )
        timer = (
            _under(repo_root, args.timer, label="timer") if args.timer else None
        )
        images = tuple(
            _under(repo_root, image, label="image") for image in args.image
        )
        workflow_state = handoff_dir / "workflow-state.yaml"
        semantic_design = handoff_dir / "semantic-design.json"
        if handoff_dir.exists():
            raise StandardProductionIterationError(
                f"handoff-dir must not exist before bridge invocation: {handoff_dir}"
            )
        handoff_absent_before_bridge = True
        if not context.is_file():
            raise StandardProductionIterationError(
                f"prepared context is missing: {context}"
            )
        context_payload = _load_json(context, label="prepared context")
        try:
            ft_slug = validate_stable_path_segment(
                context_payload.get("ft_slug"), label="prepared context.ft_slug"
            )
        except BoundedScopeBoundaryError as exc:
            raise StandardProductionIterationError(str(exc)) from exc
        expected_ft_root = (repo_root / "fts" / ft_slug).resolve()
        try:
            handoff_dir.relative_to(expected_ft_root)
        except ValueError as exc:
            raise StandardProductionIterationError(
                "handoff-dir must stay inside the FT package named by "
                "prepared context.ft_slug"
            ) from exc
        expected_context_digest = prepared_context_sha256(context_payload)
        publication_owner_token = str(uuid.uuid4())
        summary["publication_owner_token"] = publication_owner_token
        combined_summary_safe = True
        bridge_args = [
            "--repo-root", str(repo_root),
            "--context", str(context),
            "--runtime-dir", str(runtime_dir),
            "--handoff-dir", str(handoff_dir),
            "--summary-output", str(bridge_summary_path),
            "--publication-owner-token", publication_owner_token,
            "--measurement-mode", args.measurement_mode,
            "--semantic-sharding", args.semantic_sharding,
            "--semantic-shard-max-included-rows", str(args.semantic_shard_max_included_rows),
            "--semantic-shard-max-source-rows", str(args.semantic_shard_max_source_rows),
            "--semantic-shard-max-shards", str(args.semantic_shard_max_shards),
            "--semantic-shard-max-weight", str(args.semantic_shard_max_weight),
        ]
        _option(bridge_args, "--timer", timer)
        for image in images:
            _option(bridge_args, "--image", image)
        _option(bridge_args, "--codex-command", args.codex_command)
        phase_summary_absent_before = {
            phase: not (runtime_dir / phase / "summary.json").exists()
            for phase in _MODEL_PHASES
        }
        (
            preexisting_bridge_timer_phase_digests,
            preexisting_bridge_timer_phase_snapshot_error,
        ) = _snapshot_timer_phases(timer)

        summary["bridge"] = {"status": "running"}
        bridge_invocation_error: Exception | None = None
        try:
            bridge_code = bridge_runner(bridge_args)
        except Exception as exc:  # noqa: BLE001 - publication may be committed.
            bridge_code = 2
            bridge_invocation_error = exc
        bridge_summary: dict[str, Any] = {}
        bridge_reporting_error: Exception | None = None
        if bridge_summary_path.is_file():
            try:
                bridge_summary = _load_json(
                    bridge_summary_path, label="scope bridge summary"
                )
            except Exception as exc:  # noqa: BLE001 - handoff may be committed.
                bridge_reporting_error = exc
        handoff_appeared_during_bridge = (
            handoff_absent_before_bridge and handoff_dir.is_dir()
        )
        bridge_counts = (
            _count_pair(bridge_summary)
            if bridge_summary.get("publication_owner_token")
            == publication_owner_token
            else None
        )
        if bridge_counts is not None:
            summary["bridge_attempt_count"], summary["bridge_retry_count"] = bridge_counts
            summary["bridge_lifecycle_count_evidence"] = {
                "status": "verified",
                "source": "owned-bridge-summary",
            }
        else:
            recovered_counts, count_evidence = _recover_lifecycle_counts(
                runtime_dir=runtime_dir,
                timer=timer,
                bridge_summary=bridge_summary,
                handoff_appeared=handoff_appeared_during_bridge,
                phase_summary_absent_before=phase_summary_absent_before,
                invocation_started_epoch_ms=invocation_started_epoch_ms,
                preexisting_timer_phase_digests=(
                    preexisting_bridge_timer_phase_digests
                ),
                preexisting_timer_phase_snapshot_error=(
                    preexisting_bridge_timer_phase_snapshot_error
                ),
            )
            if recovered_counts is None:
                summary["bridge_attempt_count"] = None
                summary["bridge_retry_count"] = None
            else:
                summary["bridge_attempt_count"], summary["bridge_retry_count"] = (
                    recovered_counts
                )
            summary["bridge_lifecycle_count_evidence"] = count_evidence
            if bridge_summary and (
                bridge_summary.get("publication_owner_token")
                != publication_owner_token
            ):
                add_reporting_error(
                    "scope-bridge-summary-ownership",
                    error_type="BridgeReportingError",
                    error=(
                        "scope bridge summary is not owned by the current "
                        "production invocation"
                    ),
                )
        _apply_total_lifecycle_counts(summary, downstream_invoked=False)
        if not handoff_appeared_during_bridge:
            summary["bridge"] = {
                "status": "completed" if bridge_code == 0 else "failed",
                "return_code": bridge_code,
                "summary": bridge_summary,
            }
            if bridge_invocation_error is not None:
                raise bridge_invocation_error
            if bridge_reporting_error is not None:
                raise bridge_reporting_error
            if bridge_code != 0:
                return finish(
                    status=(
                        "blocked-input" if bridge_code == 3 else "terminal-failed"
                    ),
                    return_code=bridge_code,
                )
            raise StandardProductionIterationError(
                "scope bridge returned success without publishing the handoff: "
                f"{handoff_dir}"
            )
        try:
            bridge_receipt = load_published_handoff_receipt(
                repo_root,
                handoff_dir,
                expected_prepared_context_sha256=expected_context_digest,
                expected_publication_owner_token=publication_owner_token,
            )
        except Exception:
            summary["bridge"] = {
                "status": "failed",
                "return_code": bridge_code,
                "summary": bridge_summary,
            }
            raise
        if bridge_invocation_error is not None:
            add_reporting_error(
                "scope-bridge",
                error_type=type(bridge_invocation_error).__name__,
                error=str(bridge_invocation_error),
                reported_return_code=bridge_code,
            )
        elif bridge_code != 0:
            add_reporting_error(
                "scope-bridge",
                error_type="BridgeReportingError",
                error=(
                    "scope bridge returned a non-zero code after publishing an "
                    "authoritative handoff"
                ),
                reported_return_code=bridge_code,
            )
        if bridge_reporting_error is not None:
            add_reporting_error(
                "scope-bridge-summary",
                error_type=type(bridge_reporting_error).__name__,
                error=str(bridge_reporting_error),
            )
        elif bridge_summary.get("status") != "completed":
            add_reporting_error(
                "scope-bridge-summary",
                error_type="BridgeReportingError",
                error=(
                    "scope bridge summary was absent or non-completed; recovered "
                    "from authoritative handoff receipt"
                ),
            )
        summary["bridge"] = {
            "status": "completed",
            "return_code": bridge_code,
            "summary": bridge_summary,
            "publication": dict(bridge_receipt["publication"]),
            "downstream_evidence_readiness": dict(
                bridge_receipt["downstream_evidence_readiness"]
            ),
        }

        package_id = _context_package_id(context)
        _verify_materialized_package_id(semantic_design, expected=package_id)
        if not workflow_state.is_file():
            raise StandardProductionIterationError(
                "scope bridge succeeded without materialized workflow-state: "
                f"{workflow_state}"
            )
        expected_source_assertion_review = _workflow_artifact_path(
            workflow_state,
            ft_root=expected_ft_root,
            key="source_assertion_review",
        )
        summary["package_id"] = package_id

        downstream_args = [
            "--repo-root", str(repo_root),
            "--workflow-state", str(workflow_state),
            "--cycle-dir", str(cycle_dir),
            "--final-artifact", str(final_artifact),
            "--package-id", package_id,
            "--measurement-mode", args.measurement_mode,
        ]
        if timer is not None:
            _option(downstream_args, "--timer", timer)
            downstream_args.append("--defer-timer-finish")
        _option(downstream_args, "--codex-command", args.codex_command)

        summary["downstream"] = {
            "status": "running",
            "workflow_state": str(workflow_state),
        }
        summary["downstream_attempt_count"] = None
        summary["downstream_retry_count"] = None
        summary["downstream_lifecycle_count_evidence"] = {
            "status": "unknown",
            "source": "downstream-running",
        }
        _apply_total_lifecycle_counts(summary, downstream_invoked=True)
        downstream_invocation_started_epoch_ms = time.time_ns() // 1_000_000
        (
            preexisting_source_summary,
            preexisting_source_summary_error,
        ) = _snapshot_json_file(
            cycle_dir / "source-review-summary.json",
            label="preexisting source-review summary",
        )
        (
            preexisting_source_assertion_review,
            preexisting_source_assertion_review_error,
        ) = _snapshot_json_file(
            expected_source_assertion_review,
            label="preexisting expected source-assertion review",
        )
        (
            preexisting_stage_metrics,
            preexisting_stage_metrics_error,
        ) = _snapshot_writer_reviewer_metrics(cycle_dir)
        (
            preexisting_timer_phase_digests,
            preexisting_timer_phase_snapshot_error,
        ) = _snapshot_timer_phases(timer)
        downstream_code: int | None = None
        downstream_invocation_error: Exception | None = None
        try:
            downstream_code = downstream_runner(downstream_args)
        except Exception as exc:  # noqa: BLE001 - retain lifecycle evidence.
            downstream_invocation_error = exc
        downstream_counts, downstream_count_evidence = (
            _recover_downstream_lifecycle_counts(
                timer=timer,
                cycle_dir=cycle_dir,
                invocation_started_epoch_ms=downstream_invocation_started_epoch_ms,
                downstream_return_code=downstream_code,
                preexisting_source_summary=preexisting_source_summary,
                preexisting_source_summary_error=preexisting_source_summary_error,
                expected_source_assertion_review=(
                    expected_source_assertion_review
                ),
                preexisting_source_assertion_review=(
                    preexisting_source_assertion_review
                ),
                preexisting_source_assertion_review_error=(
                    preexisting_source_assertion_review_error
                ),
                preexisting_stage_metrics=preexisting_stage_metrics,
                preexisting_stage_metrics_error=preexisting_stage_metrics_error,
                preexisting_timer_phase_digests=preexisting_timer_phase_digests,
                preexisting_timer_phase_snapshot_error=(
                    preexisting_timer_phase_snapshot_error
                ),
            )
        )
        if downstream_counts is None:
            summary["downstream_attempt_count"] = None
            summary["downstream_retry_count"] = None
        else:
            (
                summary["downstream_attempt_count"],
                summary["downstream_retry_count"],
            ) = downstream_counts
        summary["downstream_lifecycle_count_evidence"] = downstream_count_evidence
        _apply_total_lifecycle_counts(summary, downstream_invoked=True)
        if downstream_invocation_error is not None:
            raise downstream_invocation_error
        assert downstream_code is not None
        summary["downstream"] = {
            "status": "completed" if downstream_code == 0 else "failed",
            "return_code": downstream_code,
            "workflow_state": str(workflow_state),
        }
        if downstream_code != 0:
            return finish(status="terminal-failed", return_code=downstream_code)
        if not final_artifact.is_file():
            summary["downstream"]["status"] = "failed"
            raise StandardProductionIterationError(
                "downstream returned success without the final artifact: "
                f"{final_artifact}"
            )

        summary["final_artifact"] = str(final_artifact)
        return finish(status="completed", return_code=0)
    except Exception as exc:  # noqa: BLE001 - terminal one-command boundary.
        for phase in ("bridge", "downstream"):
            state = summary.get(phase)
            if isinstance(state, dict) and state.get("status") == "running":
                state["status"] = "failed"
        summary.update(
            {
                "status": "terminal-failed",
                "return_code": 2,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "duration_ms": (
                    time.perf_counter_ns() - started
                ) // 1_000_000,
            }
        )
        return finish(status="terminal-failed", return_code=2)


if __name__ == "__main__":
    raise SystemExit(main())
