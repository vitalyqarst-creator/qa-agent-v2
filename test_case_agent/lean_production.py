from __future__ import annotations

import json
import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from test_case_agent.review_cycle.metrics import StageMetrics
from test_case_agent.review_cycle.runtime import StageRuntimeError


SCHEMA_VERSION = 1
TARGET_WALL_MS = 300_000
HARD_WALL_MS = 480_000
MEASUREMENT_MODE_SLO = "slo"
MEASUREMENT_MODE_OBSERVATIONAL = "observational"
OBSERVATION_CONTRACT_VERSION = 1
TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "total_tokens")
_MODEL_STAGE_ID = re.compile(r"(writer|reviewer)-r[1-9][0-9]*")
_MODEL_ATTEMPT_ID = re.compile(r"attempt-([0-9]{3})")
ROOT_TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)

BASELINE_PROCESS_PHASES = (
    "routing-preflight",
    "source-selection",
    "source-preparation",
    "scope-analysis",
    "semantic-design",
    "scope-materialization",
    "source-review",
    "compile-preflight",
    "writer-reviewer",
    "promotion",
    "final-reporting",
)

OPTIONAL_PROCESS_PHASES = (
    "diagnostics-recovery",
    "code-remediation",
    "offline-verification",
    "retry-backoff",
    "cycle-preparation",
    "cross-scope-evaluation",
    "incremental-update",
    "final-reconciliation",
)

# Registry of valid top-level phases. Optional recovery/development phases are
# deliberately not reported as missing in a clean production observation.
FULL_PROCESS_PHASES = BASELINE_PROCESS_PHASES[:-1] + OPTIONAL_PROCESS_PHASES + (
    BASELINE_PROCESS_PHASES[-1],
)

ROUTING_PREFLIGHT_COMPONENTS = (
    "request-metadata-read",
    "instruction-loading",
    "environment-probe",
    "workspace-check",
    "ft-config-selection",
    "source-registry-check",
    "hash-verification",
    "command-preparation",
    "external-backend-wait",
    "other-orchestration",
)


class LeanProductionError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def epoch_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def utc_from_epoch_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temp.replace(path)


def load_run(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LeanProductionError(f"cannot read workflow timer: {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise LeanProductionError("unsupported workflow timer schema")
    if not isinstance(payload.get("phases"), list):
        raise LeanProductionError("workflow timer phases must be an array")
    return payload


def start_run(
    path: Path,
    *,
    ft_slug: str,
    scope_slug: str,
    baseline_label: str | None = None,
    baseline_wall_ms: int | None = None,
    profile: str = "lean-production",
    request_started_epoch_ms: int | None = None,
    measurement_mode: str = MEASUREMENT_MODE_SLO,
    request_start_source: str | None = None,
    request_start_precision_ms: int = 1,
    codex_turn_id: str | None = None,
    end_anchor: str = "workflow-terminal",
    initial_phase: str | None = None,
) -> dict[str, Any]:
    if path.exists():
        raise LeanProductionError(f"workflow timer already exists: {path}")
    now_ms = epoch_ms()
    started_ms = now_ms if request_started_epoch_ms is None else request_started_epoch_ms
    if type(started_ms) is not int or started_ms < 0:
        raise LeanProductionError("request_started_epoch_ms must be a non-negative integer")
    if started_ms > now_ms:
        raise LeanProductionError("request_started_epoch_ms cannot be in the future")
    if not profile.strip():
        raise LeanProductionError("profile must be non-empty")
    if measurement_mode not in {MEASUREMENT_MODE_SLO, MEASUREMENT_MODE_OBSERVATIONAL}:
        raise LeanProductionError("measurement_mode must be 'slo' or 'observational'")
    if (
        type(request_start_precision_ms) is not int
        or request_start_precision_ms <= 0
    ):
        raise LeanProductionError("request_start_precision_ms must be a positive integer")
    if request_start_source is not None and not request_start_source.strip():
        raise LeanProductionError("request_start_source must be non-empty when provided")
    if not end_anchor.strip():
        raise LeanProductionError("end_anchor must be non-empty")
    if initial_phase is not None and not initial_phase.strip():
        raise LeanProductionError("initial_phase must be non-empty when provided")
    observational = measurement_mode == MEASUREMENT_MODE_OBSERVATIONAL
    start_source = (
        request_start_source
        if request_started_epoch_ms is not None
        else "recorder-clock"
    ) or "caller-declared"
    start_kind = "request-received" if request_started_epoch_ms is not None else "timer-start"
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "ft_slug": ft_slug,
        "scope_slug": scope_slug,
        "status": "running",
        "started_at_utc": utc_from_epoch_ms(started_ms),
        "started_epoch_ms": started_ms,
        "timer_started_at_utc": utc_from_epoch_ms(now_ms),
        "timer_started_epoch_ms": now_ms,
        "measurement_coverage": (
            "request-received" if request_started_epoch_ms is not None else "timer-start"
        ),
        "finished_at_utc": None,
        "finished_epoch_ms": None,
        "full_user_wall_ms": None,
        "observed_window_ms": None,
        "target_wall_ms": None if observational else TARGET_WALL_MS,
        "hard_wall_ms": None if observational else HARD_WALL_MS,
        "slo_status": "not-evaluated" if observational else "running",
        "baseline": {
            "label": baseline_label,
            "full_user_wall_ms": baseline_wall_ms,
        },
        "phases": [],
        "persistent_artifacts": None,
        "test_case_count": None,
    }
    if observational:
        confidence = (
            "verified"
            if request_start_source == "codex-request-metadata"
            else "declared"
            if request_started_epoch_ms is not None
            else "verified"
        )
        payload["observation"] = {
            "contract_version": OBSERVATION_CONTRACT_VERSION,
            "mode": MEASUREMENT_MODE_OBSERVATIONAL,
            "run_id": str(uuid.uuid4()),
            "limits_applied": False,
            "codex_turn_id": codex_turn_id,
            "anchors": {
                "start": {
                    "kind": start_kind,
                    "epoch_ms": started_ms,
                    "source": start_source,
                    "precision_ms": request_start_precision_ms,
                    "confidence": confidence,
                },
                "timer_start": {
                    "kind": "timer-start",
                    "epoch_ms": now_ms,
                    "source": "recorder-clock",
                    "precision_ms": 1,
                    "confidence": "verified",
                },
                "end": None,
            },
            "requested_end_anchor": end_anchor,
            "coverage": {
                "label": (
                    f"declared-request-to-{end_anchor}"
                    if request_started_epoch_ms is not None
                    else f"{start_kind}-to-{end_anchor}"
                ),
                "includes": ["all recorded phases", "inter-phase orchestration"],
                "excludes": ["final response submit and UI render"],
                "claimable_as_full_user_wall": False,
            },
            "totals": None,
            "external_observations": [],
        }
    if initial_phase is not None:
        payload["phases"].append(
            {
                "span_id": str(uuid.uuid4()),
                "phase": initial_phase,
                "status": "running",
                "started_at_utc": utc_from_epoch_ms(started_ms),
                "started_epoch_ms": started_ms,
                "finished_at_utc": None,
                "finished_epoch_ms": None,
                "duration_ms": None,
                "metrics": {},
            }
        )
    _write_json_atomic(path, payload)
    return payload


def start_phase(
    path: Path,
    *,
    phase: str,
    input_artifact_roots: Iterable[Path] = (),
) -> dict[str, Any]:
    payload = load_run(path)
    if payload.get("status") != "running":
        raise LeanProductionError("cannot start a phase after terminal status")
    if any(item.get("status") == "running" for item in payload["phases"]):
        raise LeanProductionError("another workflow phase is already running")
    roots = tuple(input_artifact_roots)
    started_ms = epoch_ms()
    payload["phases"].append(
        {
            "span_id": str(uuid.uuid4()),
            "phase": phase,
            "status": "running",
            "started_at_utc": utc_from_epoch_ms(started_ms),
            "started_epoch_ms": started_ms,
            "finished_at_utc": None,
            "finished_epoch_ms": None,
            "duration_ms": None,
            "metrics": (
                {"input_artifacts": artifact_inventory(roots)} if roots else {}
            ),
        }
    )
    _write_json_atomic(path, payload)
    return payload


def finish_phase(
    path: Path,
    *,
    phase: str,
    status: str,
    metrics: Mapping[str, Any] | None = None,
    input_artifact_roots: Iterable[Path] = (),
    output_artifact_roots: Iterable[Path] = (),
) -> dict[str, Any]:
    payload = load_run(path)
    candidates = [
        item
        for item in payload["phases"]
        if item.get("phase") == phase and item.get("status") == "running"
    ]
    if len(candidates) != 1:
        raise LeanProductionError(f"expected one running phase {phase!r}")
    item = candidates[0]
    input_roots = tuple(input_artifact_roots)
    output_roots = tuple(output_artifact_roots)
    merged_metrics = {
        **dict(item.get("metrics") or {}),
        **dict(metrics or {}),
    }
    if input_roots:
        merged_metrics["input_artifacts"] = artifact_inventory(input_roots)
    if output_roots:
        merged_metrics["output_artifacts"] = artifact_inventory(output_roots)
    finished_ms = epoch_ms()
    item.update(
        {
            "status": status,
            "finished_at_utc": utc_from_epoch_ms(finished_ms),
            "finished_epoch_ms": finished_ms,
            "duration_ms": finished_ms - int(item["started_epoch_ms"]),
            "metrics": merged_metrics,
        }
    )
    _write_json_atomic(path, payload)
    return payload


def transition_phase(
    path: Path,
    *,
    phase: str,
    status: str,
    next_phase: str,
    metrics: Mapping[str, Any] | None = None,
    input_artifact_roots: Iterable[Path] = (),
    output_artifact_roots: Iterable[Path] = (),
    next_input_artifact_roots: Iterable[Path] = (),
) -> dict[str, Any]:
    """Finish one sequential phase and start the next at one shared boundary."""

    payload = load_run(path)
    if payload.get("status") != "running":
        raise LeanProductionError("cannot transition a phase after terminal status")
    candidates = [
        item
        for item in payload["phases"]
        if item.get("phase") == phase and item.get("status") == "running"
    ]
    if len(candidates) != 1:
        raise LeanProductionError(f"expected one running phase {phase!r}")
    input_roots = tuple(input_artifact_roots)
    output_roots = tuple(output_artifact_roots)
    next_input_roots = tuple(next_input_artifact_roots)
    merged_metrics = {
        **dict(candidates[0].get("metrics") or {}),
        **dict(metrics or {}),
    }
    if input_roots:
        merged_metrics["input_artifacts"] = artifact_inventory(input_roots)
    if output_roots:
        merged_metrics["output_artifacts"] = artifact_inventory(output_roots)
    next_metrics: dict[str, Any] = {}
    if next_input_roots:
        next_metrics["input_artifacts"] = artifact_inventory(next_input_roots)
    boundary_ms = epoch_ms()
    candidates[0].update(
        {
            "status": status,
            "finished_at_utc": utc_from_epoch_ms(boundary_ms),
            "finished_epoch_ms": boundary_ms,
            "duration_ms": boundary_ms - int(candidates[0]["started_epoch_ms"]),
            "metrics": merged_metrics,
        }
    )
    payload["phases"].append(
        {
            "span_id": str(uuid.uuid4()),
            "phase": next_phase,
            "status": "running",
            "started_at_utc": utc_from_epoch_ms(boundary_ms),
            "started_epoch_ms": boundary_ms,
            "finished_at_utc": None,
            "finished_epoch_ms": None,
            "duration_ms": None,
            "metrics": next_metrics,
        }
    )
    _write_json_atomic(path, payload)
    return payload


def artifact_inventory(roots: Iterable[Path]) -> dict[str, Any]:
    root_items = tuple(roots)
    files: dict[str, Path] = {}
    missing_roots: list[str] = []
    for root in root_items:
        resolved = root.resolve()
        if resolved.is_file():
            files[str(resolved)] = resolved
        elif resolved.is_dir():
            for path in resolved.rglob("*"):
                if path.is_file():
                    files[str(path.resolve())] = path.resolve()
        else:
            missing_roots.append(str(resolved))
    return {
        "root_count": len(root_items),
        "file_count": len(files),
        "bytes": sum(path.stat().st_size for path in files.values()),
        "missing_roots": missing_roots,
    }


def _phase_timing_totals(
    payload: Mapping[str, Any],
    *,
    start_ms: int,
    end_ms: int,
) -> dict[str, Any]:
    intervals: list[tuple[int, int, str]] = []
    clock_anomalies: list[str] = []
    phase_sum_ms = 0
    for index, item in enumerate(payload.get("phases", [])):
        raw_started = item.get("started_epoch_ms")
        raw_finished = item.get("finished_epoch_ms")
        if type(raw_started) is not int or type(raw_finished) is not int:
            continue
        if raw_finished < raw_started:
            clock_anomalies.append(f"phase[{index}] clock moved backwards")
            continue
        interval_start = max(start_ms, raw_started)
        interval_end = min(end_ms, raw_finished)
        if interval_end < interval_start:
            continue
        phase_sum_ms += interval_end - interval_start
        intervals.append((interval_start, interval_end, str(item.get("phase", "unknown"))))

    intervals.sort(key=lambda item: (item[0], item[1], item[2]))
    merged: list[tuple[int, int]] = []
    for interval_start, interval_end, _ in intervals:
        if not merged or interval_start > merged[-1][1]:
            merged.append((interval_start, interval_end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], interval_end))
    phase_union_ms = sum(interval_end - interval_start for interval_start, interval_end in merged)
    observed_window_ms = max(0, end_ms - start_ms)

    gaps: list[dict[str, Any]] = []
    cursor = start_ms
    previous = "observation-start"
    for interval_start, interval_end, phase in intervals:
        if interval_start > cursor:
            gaps.append(
                {
                    "after": previous,
                    "before": phase,
                    "started_epoch_ms": cursor,
                    "finished_epoch_ms": interval_start,
                    "duration_ms": interval_start - cursor,
                }
            )
        if interval_end > cursor:
            cursor = interval_end
            previous = phase
    if cursor < end_ms:
        gaps.append(
            {
                "after": previous,
                "before": "observation-end",
                "started_epoch_ms": cursor,
                "finished_epoch_ms": end_ms,
                "duration_ms": end_ms - cursor,
            }
        )

    present_phases = {
        str(item.get("phase")) for item in payload.get("phases", []) if item.get("phase")
    }
    return {
        "observed_window_ms": observed_window_ms,
        "phase_sum_ms": phase_sum_ms,
        "phase_union_ms": phase_union_ms,
        "phase_overlap_ms": max(0, phase_sum_ms - phase_union_ms),
        "unattributed_ms": max(0, observed_window_ms - phase_union_ms),
        "explicit_interphase_overlap_ms": max(0, phase_sum_ms - phase_union_ms),
        "reconciled_observed_window_ms": (
            phase_sum_ms
            - max(0, phase_sum_ms - phase_union_ms)
            + max(0, observed_window_ms - phase_union_ms)
        ),
        "reconciliation_delta_ms": (
            observed_window_ms
            - (
                phase_sum_ms
                - max(0, phase_sum_ms - phase_union_ms)
                + max(0, observed_window_ms - phase_union_ms)
            )
        ),
        "reconciliation_formula": (
            "observed_window_ms = phase_sum_ms - "
            "explicit_interphase_overlap_ms + unattributed_ms"
        ),
        "phase_coverage_percent": (
            round(phase_union_ms * 100 / observed_window_ms, 2)
            if observed_window_ms
            else 100.0
        ),
        "gaps": gaps,
        "clock_anomalies": clock_anomalies,
        "missing_full_process_phases": [
            phase for phase in BASELINE_PROCESS_PHASES if phase not in present_phases
        ],
        "available_optional_phases": list(OPTIONAL_PROCESS_PHASES),
    }


def _slo_status(wall_ms: int) -> str:
    if wall_ms <= TARGET_WALL_MS:
        return "within-target"
    if wall_ms <= HARD_WALL_MS:
        return "within-hard-limit"
    return "breached"


def _finalize_payload(
    payload: dict[str, Any],
    *,
    status: str,
    finished_ms: int,
    test_case_count: int,
    inventory: Mapping[str, Any],
    end_anchor_override: str | None = None,
) -> None:
    started_ms = int(payload["started_epoch_ms"])
    timer_started_ms = int(payload.get("timer_started_epoch_ms", started_ms))
    wall_ms = finished_ms - started_ms
    if wall_ms < 0:
        raise LeanProductionError("workflow clock moved backwards")
    observational = (
        isinstance(payload.get("observation"), Mapping)
        and payload["observation"].get("mode") == MEASUREMENT_MODE_OBSERVATIONAL
    )
    payload.update(
        {
            "status": status,
            "finished_at_utc": utc_from_epoch_ms(finished_ms),
            "finished_epoch_ms": finished_ms,
            "observed_window_ms": wall_ms,
            "full_user_wall_ms": None if observational else wall_ms,
            "instrumented_wall_ms": finished_ms - timer_started_ms,
            "pre_timer_wall_ms": timer_started_ms - started_ms,
            "slo_status": "not-evaluated" if observational else _slo_status(wall_ms),
            "persistent_artifacts": dict(inventory),
            "test_case_count": test_case_count,
        }
    )
    if not observational:
        return
    observation = payload["observation"]
    end_kind = end_anchor_override or str(
        observation.get("requested_end_anchor") or "workflow-terminal"
    )
    observation["anchors"]["end"] = {
        "kind": end_kind,
        "epoch_ms": finished_ms,
        "source": "recorder-clock",
        "precision_ms": 1,
        "confidence": "verified",
    }
    totals = _phase_timing_totals(payload, start_ms=started_ms, end_ms=finished_ms)
    totals["pre_instrumentation_ms"] = timer_started_ms - started_ms
    observation["totals"] = totals
    start_anchor = observation["anchors"]["start"]
    if (
        start_anchor.get("source") == "codex-request-metadata"
        and start_anchor.get("kind") == "request-received"
    ):
        label = f"host-request-to-{end_kind}"
    elif start_anchor.get("kind") == "request-received":
        label = f"declared-request-to-{end_kind}"
    else:
        label = f"timer-start-to-{end_kind}"
    observation["coverage"].update(
        {
            "label": label,
            "claimable_as_full_user_wall": False,
            "excludes": ["final response submit and UI render"],
        }
    )


def finish_run(
    path: Path,
    *,
    status: str,
    test_case_count: int,
    artifact_roots: Iterable[Path] = (),
    active_phase: str | None = None,
    phase_status: str = "completed",
    phase_metrics: Mapping[str, Any] | None = None,
    phase_input_artifact_roots: Iterable[Path] = (),
    phase_output_artifact_roots: Iterable[Path] = (),
) -> dict[str, Any]:
    payload = load_run(path)
    if payload.get("status") != "running":
        raise LeanProductionError("cannot finish a terminal workflow timer")
    running = [item for item in payload["phases"] if item.get("status") == "running"]
    if active_phase is None and running:
        raise LeanProductionError("cannot finish while a phase is running")
    if active_phase is not None and (
        len(running) != 1 or running[0].get("phase") != active_phase
    ):
        raise LeanProductionError(f"expected one running phase {active_phase!r}")
    roots = tuple(artifact_roots)
    phase_input_roots = tuple(phase_input_artifact_roots)
    phase_output_roots = tuple(phase_output_artifact_roots)
    inventory = artifact_inventory(roots)
    phase_input_inventory = (
        artifact_inventory(phase_input_roots) if phase_input_roots else None
    )
    phase_output_inventory = (
        artifact_inventory(phase_output_roots) if phase_output_roots else None
    )
    finished_ms = epoch_ms()
    if active_phase is not None:
        item = running[0]
        merged_metrics = {
            **dict(item.get("metrics") or {}),
            **dict(phase_metrics or {}),
        }
        if phase_input_inventory is not None:
            merged_metrics["input_artifacts"] = phase_input_inventory
        if phase_output_inventory is not None:
            merged_metrics["output_artifacts"] = phase_output_inventory
        item.update(
            {
                "status": phase_status,
                "finished_at_utc": utc_from_epoch_ms(finished_ms),
                "finished_epoch_ms": finished_ms,
                "duration_ms": finished_ms - int(item["started_epoch_ms"]),
                "metrics": merged_metrics,
            }
        )
    _finalize_payload(
        payload,
        status=status,
        finished_ms=finished_ms,
        test_case_count=test_case_count,
        inventory=inventory,
    )
    _write_json_atomic(path, payload)
    return payload


def terminalize_run(
    path: Path,
    *,
    status: str,
    error_type: str,
    error: str,
    test_case_count: int = 0,
    artifact_roots: Iterable[Path] = (),
    finished_epoch_ms: int | None = None,
) -> dict[str, Any]:
    """Close every running phase and the run with one terminal timestamp.

    ``finished_epoch_ms`` is reserved for recovery after an external root-turn
    failure.  It lets a later session bind the terminal boundary to the exact
    ``task_complete`` timestamp instead of incorrectly extending the failed run
    until recovery happens.
    """

    payload = load_run(path)
    if payload.get("status") != "running":
        return payload
    roots = tuple(artifact_roots)
    inventory = artifact_inventory(roots)
    if finished_epoch_ms is None:
        finished_ms = epoch_ms()
    else:
        if type(finished_epoch_ms) is not int:
            raise LeanProductionError("finished_epoch_ms must be an integer")
        finished_ms = finished_epoch_ms
    started_ms = int(payload["started_epoch_ms"])
    latest_phase_start = max(
        (
            int(item["started_epoch_ms"])
            for item in payload["phases"]
            if type(item.get("started_epoch_ms")) is int
        ),
        default=started_ms,
    )
    if finished_ms < max(started_ms, latest_phase_start):
        raise LeanProductionError(
            "finished_epoch_ms cannot precede the workflow or an active phase"
        )
    finished_at = utc_from_epoch_ms(finished_ms)
    for item in payload["phases"]:
        if item.get("status") != "running":
            continue
        item.update(
            {
                "status": "terminal-failed",
                "finished_at_utc": finished_at,
                "finished_epoch_ms": finished_ms,
                "duration_ms": finished_ms - int(item["started_epoch_ms"]),
                "metrics": {
                    **dict(item.get("metrics") or {}),
                    "terminal_error_type": error_type,
                    "terminal_error": error,
                },
            }
        )
    _finalize_payload(
        payload,
        status=status,
        finished_ms=finished_ms,
        test_case_count=test_case_count,
        inventory=inventory,
        end_anchor_override="workflow-terminal",
    )
    payload["terminal"] = {
        "error_type": error_type,
        "error": error,
    }
    _write_json_atomic(path, payload)
    return payload


def _stage_metric_records(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        if (
            isinstance(value.get("stage_id"), str)
            and isinstance(value.get("role"), str)
            and type(value.get("duration_ms")) is int
        ):
            records.append(dict(value))
        else:
            for child in value.values():
                records.extend(_stage_metric_records(child))
    elif isinstance(value, list):
        for child in value:
            records.extend(_stage_metric_records(child))
    return records


def _usage_records(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        usage = value.get("usage")
        if isinstance(usage, Mapping) and any(field in usage for field in TOKEN_FIELDS):
            # A direct usage record is the authoritative aggregate for this subtree.
            # Recursing into child shard/attempt summaries would count the same tokens
            # again when a phase publishes both aggregate and detailed usage.
            return [dict(usage)]
        for key, child in value.items():
            if key != "usage":
                records.extend(_usage_records(child))
    elif isinstance(value, list):
        for child in value:
            records.extend(_usage_records(child))
    return records


def _sum_optional(records: Iterable[Mapping[str, Any]], field: str) -> int | None:
    values = [
        int(item[field])
        for item in records
        if type(item.get(field)) is int and int(item[field]) >= 0
    ]
    return sum(values) if values else None


def _deduplicate_metric_records(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        key = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(record))
    return unique


def _runner_model_stage_records(
    value: Mapping[str, Any],
    *,
    phase: str,
) -> list[dict[str, Any]]:
    """Project standard runner summaries into reportable model-stage records.

    Standard scope/semantic runners publish lifecycle and usage summaries rather
    than review-cycle ``StageMetrics``.  Prefer leaf shard summaries over their
    aggregate parent so tokens and attempts are not counted twice.
    """

    role_by_phase = {
        "scope-analysis": "scope-analyzer",
        "semantic-design": "semantic-design-author",
        "source-review": "source-reviewer",
    }

    def inventory(
        node: Mapping[str, Any],
        inherited: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Mapping[str, Any]]:
        result = dict(inherited)
        for direction in ("input", "output"):
            candidate = node.get(f"{direction}_artifacts")
            if isinstance(candidate, Mapping):
                result[direction] = candidate
        return result

    def visit(
        node: Mapping[str, Any],
        inherited_inventory: Mapping[str, Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        current_inventory = inventory(node, inherited_inventory)
        stage_summary = node.get("stage_summary")
        if isinstance(stage_summary, Mapping):
            return visit(stage_summary, current_inventory)
        sharding = node.get("sharding")
        shards = sharding.get("shards") if isinstance(sharding, Mapping) else None
        if isinstance(shards, list):
            records: list[dict[str, Any]] = []
            for shard in shards:
                if isinstance(shard, Mapping):
                    records.extend(visit(shard, current_inventory))
            return records
        if node.get("model_invoked") is not True or type(node.get("duration_ms")) is not int:
            return []
        usage = node.get("usage")
        lifecycle = node.get("lifecycle")
        if not isinstance(usage, Mapping):
            return []
        attempt_count = (
            int(lifecycle["runner_attempt_count"])
            if isinstance(lifecycle, Mapping)
            and type(lifecycle.get("runner_attempt_count")) is int
            and int(lifecycle["runner_attempt_count"]) > 0
            else 1
        )
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = (
            int(input_tokens) + int(output_tokens)
            if type(input_tokens) is int and type(output_tokens) is int
            else None
        )
        stage_id = str(
            node.get("shard_id")
            or node.get("stage_id")
            or node.get("execution_route")
            or f"{phase}-model-stage"
        )
        record: dict[str, Any] = {
            "stage_id": stage_id,
            "attempt_id": (
                "attempt-001" if attempt_count == 1 else "aggregate-attempts"
            ),
            "role": str(node.get("role") or role_by_phase.get(phase) or phase),
            "duration_ms": int(node["duration_ms"]),
            "attempt_count": attempt_count,
            "input_tokens": input_tokens,
            "cached_input_tokens": usage.get("cached_input_tokens"),
            "output_tokens": output_tokens,
            "reasoning_tokens": usage.get(
                "reasoning_tokens", usage.get("reasoning_output_tokens")
            ),
            "total_tokens": total_tokens,
        }
        for direction in ("input", "output"):
            artifact = current_inventory.get(direction, {})
            record[f"{direction}_artifact_count"] = artifact.get("file_count")
            record[f"{direction}_artifact_bytes"] = artifact.get("bytes")
        return [record]

    return _deduplicate_metric_records(visit(value, {}))


def _inventory_from_metrics(
    metrics: Mapping[str, Any],
    *,
    direction: str,
    stages: list[dict[str, Any]],
) -> dict[str, int | None]:
    explicit = metrics.get(f"{direction}_artifacts")
    if isinstance(explicit, Mapping):
        return {
            "file_count": (
                int(explicit["file_count"])
                if type(explicit.get("file_count")) is int
                else None
            ),
            "bytes": int(explicit["bytes"]) if type(explicit.get("bytes")) is int else None,
        }
    count_field = f"{direction}_artifact_count"
    bytes_field = f"{direction}_artifact_bytes"
    if stages:
        return {
            "file_count": _sum_optional(stages, count_field),
            "bytes": _sum_optional(stages, bytes_field),
        }
    fallback_count = metrics.get(
        count_field,
        metrics.get(f"{direction}_file_count"),
    )
    fallback_bytes = metrics.get(bytes_field, metrics.get(f"{direction}_bytes"))
    return {
        "file_count": int(fallback_count) if type(fallback_count) is int else None,
        "bytes": int(fallback_bytes) if type(fallback_bytes) is int else None,
    }


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_projection_identity(
    value: Mapping[str, Any],
    *,
    expected_cycle_id: str,
) -> tuple[tuple[str, str, str], int] | None:
    try:
        stage = StageMetrics.from_dict(value)
    except (StageRuntimeError, TypeError):
        return None
    stage_match = _MODEL_STAGE_ID.fullmatch(stage.stage_id)
    attempt_match = _MODEL_ATTEMPT_ID.fullmatch(stage.attempt_id)
    if not (
        stage.cycle_id == expected_cycle_id
        and stage.role in {"writer", "reviewer"}
        and stage_match is not None
        and stage_match.group(1) == stage.role
        and attempt_match is not None
        and int(attempt_match.group(1)) > 0
    ):
        return None
    return (stage.stage_id, stage.attempt_id, stage.role), int(attempt_match.group(1))


def _canonical_evidence_identity(value: Any) -> tuple[str, str, str] | None:
    if not isinstance(value, Mapping) or set(value) != {
        "stage_id",
        "attempt_id",
        "role",
    }:
        return None
    stage_id = value.get("stage_id")
    attempt_id = value.get("attempt_id")
    role = value.get("role")
    if not all(isinstance(item, str) for item in (stage_id, attempt_id, role)):
        return None
    stage_match = _MODEL_STAGE_ID.fullmatch(stage_id)
    attempt_match = _MODEL_ATTEMPT_ID.fullmatch(attempt_id)
    if not (
        role in {"writer", "reviewer"}
        and stage_match is not None
        and stage_match.group(1) == role
        and attempt_match is not None
        and int(attempt_match.group(1)) > 0
    ):
        return None
    return stage_id, attempt_id, role


def _canonical_snapshot_evidence(
    value: Any,
) -> dict[tuple[str, str, str], dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    records: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, Mapping) or set(item) != {"identity", "path", "digest"}:
            return None
        identity = _canonical_evidence_identity(item.get("identity"))
        if (
            identity is None
            or identity in records
            or not isinstance(item.get("path"), str)
            or not item["path"].strip()
            or not _is_sha256(item.get("digest"))
        ):
            return None
        records[identity] = {
            "identity": {
                "stage_id": identity[0],
                "attempt_id": identity[1],
                "role": identity[2],
            },
            "path": item["path"],
            "digest": item["digest"],
        }
    return records


def _snapshot_evidence_digest(
    records: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> str:
    serialized = json.dumps(
        [dict(records[identity]) for identity in sorted(records)],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _projection_evidence(
    projection: Mapping[str, Any],
) -> tuple[
    dict[tuple[str, str, str], dict[str, Any]],
    dict[tuple[str, str, str], dict[str, Any]],
    set[tuple[str, str, str]],
] | None:
    evidence = projection.get("evidence")
    if not isinstance(evidence, Mapping):
        return None
    preexisting = _canonical_snapshot_evidence(evidence.get("pre_writer_snapshot"))
    current = _canonical_snapshot_evidence(evidence.get("post_writer_snapshot"))
    current_run_raw = evidence.get("current_run_identities")
    if (
        preexisting is None
        or current is None
        or not isinstance(current_run_raw, list)
        or type(evidence.get("ignored_preexisting_metric_count")) is not int
        or evidence.get("ignored_preexisting_metric_count") != len(preexisting)
        or evidence.get("pre_writer_snapshot_digest")
        != _snapshot_evidence_digest(preexisting)
    ):
        return None
    if not set(preexisting).issubset(current):
        return None
    if any(preexisting[identity] != current[identity] for identity in preexisting):
        return None
    current_run: set[tuple[str, str, str]] = set()
    for item in current_run_raw:
        identity = _canonical_evidence_identity(item)
        if identity is None or identity in current_run:
            return None
        current_run.add(identity)
    if current_run != set(current) - set(preexisting):
        return None
    return preexisting, current, current_run


def _writer_reviewer_current_run_projection(
    metrics: Mapping[str, Any],
) -> tuple[str, list[dict[str, Any]], dict[str, int | None], Mapping[str, Any] | None]:
    """Return only model metrics explicitly bound to the current lean invocation."""

    unknown_tokens = {field: None for field in TOKEN_FIELDS}
    projection = metrics.get("current_run_projection")
    if not isinstance(projection, Mapping):
        return "unknown", [], unknown_tokens, None
    if not (
        projection.get("contract_version") == 1
        and type(projection.get("contract_version")) is int
        and projection.get("kind") == "writer-reviewer-current-run"
        and isinstance(projection.get("cycle_id"), str)
        and projection.get("cycle_id")
    ):
        return "unknown", [], unknown_tokens, projection
    status = projection.get("status")
    raw_stages = projection.get("stage_metrics")
    if status == "measured":
        if not isinstance(raw_stages, list) or not raw_stages:
            return "unknown", [], unknown_tokens, projection
        evidence = _projection_evidence(projection)
        if evidence is None:
            return "unknown", [], unknown_tokens, projection
        current_run_identities = evidence[2]
        stages: list[dict[str, Any]] = []
        stage_identities: set[tuple[str, str, str]] = set()
        expected_retry_count = 0
        for item in raw_stages:
            if not isinstance(item, Mapping):
                return "unknown", [], unknown_tokens, projection
            parsed_identity = _canonical_projection_identity(
                item,
                expected_cycle_id=str(projection["cycle_id"]),
            )
            if parsed_identity is None or parsed_identity[0] in stage_identities:
                return "unknown", [], unknown_tokens, projection
            stage_identities.add(parsed_identity[0])
            expected_retry_count += parsed_identity[1] > 1
            stages.append(dict(item))
        if (
            stage_identities != current_run_identities
            or type(projection.get("attempt_count")) is not int
            or projection.get("attempt_count") != len(stages)
            or type(projection.get("retry_count")) is not int
            or projection.get("retry_count") != expected_retry_count
        ):
            return "unknown", [], unknown_tokens, projection
        token_usage = {
            field: (
                sum(int(item[field]) for item in stages)
                if all(type(item.get(field)) is int for item in stages)
                else None
            )
            for field in TOKEN_FIELDS
        }
        if token_usage["total_tokens"] is None:
            input_tokens = token_usage["input_tokens"]
            output_tokens = token_usage["output_tokens"]
            if input_tokens is not None and output_tokens is not None:
                token_usage["total_tokens"] = input_tokens + output_tokens
        return "measured", stages, token_usage, projection
    if status == "reused":
        token_usage = projection.get("token_usage")
        receipt = projection.get("reuse_receipt")
        receipt_tokens = receipt.get("token_usage") if isinstance(receipt, Mapping) else None
        evidence = _projection_evidence(projection)
        canonical_zero = (
            isinstance(raw_stages, list)
            and not raw_stages
            and type(projection.get("attempt_count")) is int
            and projection.get("attempt_count") == 0
            and type(projection.get("retry_count")) is int
            and projection.get("retry_count") == 0
            and isinstance(token_usage, Mapping)
            and set(token_usage) == set(TOKEN_FIELDS)
            and all(
                type(token_usage.get(field)) is int and token_usage.get(field) == 0
                for field in TOKEN_FIELDS
            )
            and isinstance(receipt, Mapping)
            and receipt.get("contract_version") == 1
            and type(receipt.get("contract_version")) is int
            and receipt.get("kind") == "writer-reviewer-current-run-reuse"
            and receipt.get("status") == "reused"
            and receipt.get("cycle_id") == projection.get("cycle_id")
            and type(receipt.get("attempt_count")) is int
            and receipt.get("attempt_count") == 0
            and type(receipt.get("retry_count")) is int
            and receipt.get("retry_count") == 0
            and isinstance(receipt_tokens, Mapping)
            and set(receipt_tokens) == set(TOKEN_FIELDS)
            and all(
                type(receipt_tokens.get(field)) is int
                and receipt_tokens.get(field) == 0
                for field in TOKEN_FIELDS
            )
            and isinstance(receipt.get("pre_writer_snapshot_digest"), str)
            and len(receipt["pre_writer_snapshot_digest"]) == 64
            and all(
                character in "0123456789abcdef"
                for character in receipt["pre_writer_snapshot_digest"]
            )
            and evidence is not None
            and not evidence[2]
            and evidence[0] == evidence[1]
            and receipt.get("pre_writer_snapshot_digest")
            == _snapshot_evidence_digest(evidence[0])
            and all(
                isinstance(projection.get(f"{direction}_artifacts"), Mapping)
                and projection[f"{direction}_artifacts"].get("file_count") == 0
                and type(
                    projection[f"{direction}_artifacts"].get("file_count")
                ) is int
                and projection[f"{direction}_artifacts"].get("bytes") == 0
                and type(projection[f"{direction}_artifacts"].get("bytes")) is int
                for direction in ("input", "output")
            )
        )
        if canonical_zero:
            return "reused", [], {field: 0 for field in TOKEN_FIELDS}, projection
    return "unknown", [], unknown_tokens, projection


def _phase_report(item: Mapping[str, Any]) -> dict[str, Any]:
    metrics = item.get("metrics") if isinstance(item.get("metrics"), Mapping) else {}
    measurement_status: str | None = None
    inventory_metrics: Mapping[str, Any] = metrics
    if item.get("phase") == "writer-reviewer":
        (
            measurement_status,
            stages,
            token_usage,
            current_projection,
        ) = _writer_reviewer_current_run_projection(metrics)
        if measurement_status == "measured":
            inventory_metrics = {
                f"{direction}_artifacts": {
                    "file_count": sum(
                        int(stage[f"{direction}_artifact_count"])
                        for stage in stages
                    ),
                    "bytes": sum(
                        int(stage[f"{direction}_artifact_bytes"])
                        for stage in stages
                    ),
                }
                for direction in ("input", "output")
            }
        elif measurement_status == "reused":
            inventory_metrics = {
                f"{direction}_artifacts": {"file_count": 0, "bytes": 0}
                for direction in ("input", "output")
            }
        else:
            inventory_metrics = {
                f"{direction}_artifacts": {"file_count": None, "bytes": None}
                for direction in ("input", "output")
            }
    else:
        stages = _deduplicate_metric_records(_stage_metric_records(metrics))
        if not stages:
            stages = _runner_model_stage_records(
                metrics,
                phase=str(item.get("phase") or "unknown"),
            )
        usage_records = stages or _deduplicate_metric_records(_usage_records(metrics))
        token_usage = {
            field: _sum_optional(usage_records, field) for field in TOKEN_FIELDS
        }
        if token_usage["total_tokens"] is None:
            input_tokens = token_usage["input_tokens"]
            output_tokens = token_usage["output_tokens"]
            if input_tokens is not None and output_tokens is not None:
                token_usage["total_tokens"] = input_tokens + output_tokens
    routing_breakdown = None
    if item.get("phase") == "routing-preflight":
        routing_breakdown = _routing_preflight_breakdown(
            metrics,
            phase_duration_ms=(
                int(item["duration_ms"])
                if type(item.get("duration_ms")) is int
                else None
            ),
        )
    cache_classification = None
    if item.get("phase") == "source-preparation":
        source_preparation = metrics.get("source_preparation")
        if isinstance(source_preparation, Mapping):
            candidate = source_preparation.get("cache_classification")
            if candidate in {
                "cold-cache",
                "warm-cache",
                "cache-status-unavailable",
            }:
                cache_classification = candidate
            elif source_preparation.get("cache_hit") is True:
                cache_classification = "warm-cache"
            elif source_preparation.get("cache_hit") is False:
                cache_classification = "cold-cache"
            else:
                cache_classification = "cache-status-unavailable"
    stage_attempt_count = sum(
        int(stage.get("attempt_count", 1))
        if type(stage.get("attempt_count", 1)) is int
        else 1
        for stage in stages
    ) if stages else (
        metrics.get("attempt_count") if type(metrics.get("attempt_count")) is int else 0
    )
    return {
        "span_id": item.get("span_id"),
        "phase": item.get("phase"),
        "status": item.get("status"),
        "started_at_utc": item.get("started_at_utc"),
        "finished_at_utc": item.get("finished_at_utc"),
        "duration_ms": item.get("duration_ms"),
        "input_artifacts": _inventory_from_metrics(
            inventory_metrics, direction="input", stages=stages
        ),
        "output_artifacts": _inventory_from_metrics(
            inventory_metrics, direction="output", stages=stages
        ),
        "token_usage": token_usage,
        "model_stages": stages,
        "model_attempt_count": stage_attempt_count,
        "model_measurement_status": measurement_status,
        "routing_preflight_breakdown": routing_breakdown,
        "cache_classification": cache_classification,
        "raw_metrics": dict(metrics),
    }


def _routing_preflight_breakdown(
    metrics: Mapping[str, Any],
    *,
    phase_duration_ms: int | None,
) -> dict[str, Any]:
    raw = metrics.get("routing_preflight_breakdown", [])
    records: dict[str, dict[str, Any]] = {}
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            component = item.get("component")
            duration = item.get("duration_ms")
            if (
                component in ROUTING_PREFLIGHT_COMPONENTS
                and component not in records
                and (
                    (type(duration) is int and duration >= 0)
                    or duration == "unavailable"
                )
            ):
                records[str(component)] = {
                    "component": component,
                    "duration_ms": duration,
                    "status": str(item.get("status") or "measured"),
                    "notes": item.get("notes"),
                }
    ordered = [
        records.get(
            component,
            {
                "component": component,
                "duration_ms": "unavailable",
                "status": "unavailable",
                "notes": "component timing was not emitted by this run",
            },
        )
        for component in ROUTING_PREFLIGHT_COMPONENTS
    ]
    measured_sum = sum(
        int(item["duration_ms"])
        for item in ordered
        if type(item.get("duration_ms")) is int
    )
    residual: int | None = None
    if phase_duration_ms is not None:
        residual = phase_duration_ms - measured_sum
        other = next(
            item for item in ordered if item["component"] == "other-orchestration"
        )
        if residual >= 0 and other["duration_ms"] == "unavailable":
            other.update(
                {
                    "duration_ms": residual,
                    "status": "residual-measured",
                    "notes": "phase duration minus explicitly measured components",
                }
            )
            measured_sum += residual
            residual = 0
    return {
        "components": ordered,
        "phase_duration_ms": phase_duration_ms,
        "component_sum_ms": measured_sum,
        "reconciliation_delta_ms": (
            phase_duration_ms - measured_sum if phase_duration_ms is not None else None
        ),
        "reconciled": phase_duration_ms is not None and phase_duration_ms == measured_sum,
    }


def _model_stage_summaries(
    stages: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for stage in stages:
        key = (
            str(stage.get("parent_phase") or "unknown"),
            str(stage.get("role") or "unknown"),
            str(stage.get("stage_id") or "unknown"),
        )
        grouped.setdefault(key, []).append(stage)
    summaries: list[dict[str, Any]] = []
    for (parent_phase, role, stage_id), attempts in sorted(grouped.items()):
        def optional_sum(field: str) -> int | str:
            values = [item.get(field) for item in attempts]
            return (
                sum(int(value) for value in values)
                if all(type(value) is int for value in values)
                else "unavailable"
            )

        summaries.append(
            {
                "parent_phase": parent_phase,
                "role": role,
                "stage_id": stage_id,
                "attempt_count": sum(
                    int(item.get("attempt_count", 1))
                    if type(item.get("attempt_count", 1)) is int
                    else 1
                    for item in attempts
                ),
                "wall_time_ms": optional_sum("duration_ms"),
                "input_tokens": optional_sum("input_tokens"),
                "cached_input_tokens": optional_sum("cached_input_tokens"),
                "output_tokens": optional_sum("output_tokens"),
                "reasoning_tokens": optional_sum("reasoning_tokens"),
                "total_tokens": optional_sum("total_tokens"),
                "input_artifact_count": optional_sum("input_artifact_count"),
                "input_artifact_bytes": optional_sum("input_artifact_bytes"),
                "output_artifact_count": optional_sum("output_artifact_count"),
                "output_artifact_bytes": optional_sum("output_artifact_bytes"),
                "attempt_ids": [str(item.get("attempt_id") or "unavailable") for item in attempts],
            }
        )
    return summaries


def build_timing_report(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a compact human/reporting projection without changing the timer record."""

    phases = [_phase_report(item) for item in payload.get("phases", [])]
    total_token_records = [
        phase["token_usage"]
        for phase in phases
        if phase["token_usage"].get("total_tokens") is not None
    ]
    observation = payload.get("observation")
    observation_payload = dict(observation) if isinstance(observation, Mapping) else None
    totals = observation_payload.get("totals") if observation_payload else None
    external = observation_payload.get("external_observations", []) if observation_payload else []
    root_token_records = [
        item.get("root_agent_token_usage")
        for item in external
        if isinstance(item, Mapping) and isinstance(item.get("root_agent_token_usage"), Mapping)
    ]
    model_stages = [
        {"parent_phase": phase["phase"], **stage}
        for phase in phases
        for stage in phase["model_stages"]
    ]
    return {
        "schema_version": 1,
        "run_id": observation_payload.get("run_id") if observation_payload else None,
        "profile": payload.get("profile"),
        "measurement_mode": (
            observation_payload.get("mode") if observation_payload else MEASUREMENT_MODE_SLO
        ),
        "ft_slug": payload.get("ft_slug"),
        "scope_slug": payload.get("scope_slug"),
        "status": payload.get("status"),
        "measurement_coverage": (
            observation_payload.get("coverage")
            if observation_payload
            else {"label": payload.get("measurement_coverage")}
        ),
        "observed_window_ms": payload.get(
            "observed_window_ms", payload.get("full_user_wall_ms")
        ),
        "full_user_wall_ms": payload.get("full_user_wall_ms"),
        "instrumented_wall_ms": payload.get("instrumented_wall_ms"),
        "pre_instrumentation_ms": payload.get("pre_timer_wall_ms"),
        "phase_totals": totals,
        "phases": phases,
        "model_stages": model_stages,
        "model_stage_summaries": _model_stage_summaries(model_stages),
        "known_token_usage": {
            field: _sum_optional(total_token_records, field) for field in TOKEN_FIELDS
        },
        "phases_with_token_data": len(total_token_records),
        "persistent_artifacts": payload.get("persistent_artifacts"),
        "test_case_count": payload.get("test_case_count"),
        "external_observations": list(external),
        "root_agent_token_usage": (
            root_token_records[-1]
            if root_token_records
            else {
                "availability": "unavailable",
                "reason": "Codex root-agent token metadata was not available for reconciliation",
                "total": {field: "unavailable" for field in ROOT_TOKEN_FIELDS},
                "by_phase": {},
            }
        ),
    }


def _format_duration_ms(value: Any) -> str:
    if type(value) is not int:
        return "н/д"
    hours, remainder = divmod(value, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    return f"{minutes:d}:{seconds:02d}.{milliseconds:03d}"


def render_timing_markdown(report: Mapping[str, Any]) -> str:
    coverage = report.get("measurement_coverage")
    coverage_label = coverage.get("label") if isinstance(coverage, Mapping) else coverage
    lines = [
        "# Наблюдение полного времени задачи",
        "",
        f"- Статус: `{report.get('status')}`",
        f"- Покрытие: `{coverage_label}`",
        f"- Наблюдаемое окно: `{_format_duration_ms(report.get('observed_window_ms'))}`",
        f"- Полное пользовательское время: `{_format_duration_ms(report.get('full_user_wall_ms'))}`",
        "",
        "## Этапы",
        "",
        "| Этап | Статус | Время | Входы, файлов/байт | Выходы, файлов/байт | Токены |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for phase in report.get("phases", []):
        inputs = phase["input_artifacts"]
        outputs = phase["output_artifacts"]
        input_text = f"{inputs.get('file_count')}/{inputs.get('bytes')}"
        output_text = f"{outputs.get('file_count')}/{outputs.get('bytes')}"
        total_tokens = phase["token_usage"].get("total_tokens")
        lines.append(
            "| "
            + " | ".join(
                (
                    str(phase.get("phase")),
                    str(phase.get("status")),
                    _format_duration_ms(phase.get("duration_ms")),
                    input_text.replace("None", "н/д"),
                    output_text.replace("None", "н/д"),
                    str(total_tokens) if total_tokens is not None else "н/д",
                )
            )
            + " |"
        )
    source_preparation_phase = next(
        (
            phase
            for phase in report.get("phases", [])
            if phase.get("phase") == "source-preparation"
        ),
        None,
    )
    if isinstance(source_preparation_phase, Mapping):
        lines.extend(
            [
                "",
                "- Классификация source-preparation cache: "
                f"`{source_preparation_phase.get('cache_classification') or 'unavailable'}`.",
            ]
        )
    totals = report.get("phase_totals")
    if isinstance(totals, Mapping):
        lines.extend(
            [
                "",
                "## Покрытие таймером",
                "",
                f"- Сумма длительностей этапов: `{_format_duration_ms(totals.get('phase_sum_ms'))}`",
                f"- Объединённое время этапов: `{_format_duration_ms(totals.get('phase_union_ms'))}`",
                f"- Неатрибутированное время: `{_format_duration_ms(totals.get('unattributed_ms'))}`",
                f"- Покрытие окна этапами: `{totals.get('phase_coverage_percent')}%`",
            ]
        )
    model_stages = report.get("model_stages", [])
    if model_stages:
        lines.extend(
            [
                "",
                "## Модельные стадии",
                "",
                "| Роль | Stage | Попытка | Время | Input tokens | Cached | Output tokens | Reasoning | Total | Inputs files/bytes | Outputs files/bytes |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for stage in model_stages:
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(stage.get("role") or "н/д"),
                        str(stage.get("stage_id") or "н/д"),
                        str(stage.get("attempt_id") or "н/д"),
                        _format_duration_ms(stage.get("duration_ms")),
                        str(stage.get("input_tokens"))
                        if stage.get("input_tokens") is not None
                        else "н/д",
                        str(stage.get("cached_input_tokens"))
                        if stage.get("cached_input_tokens") is not None
                        else "н/д",
                        str(stage.get("output_tokens"))
                        if stage.get("output_tokens") is not None
                        else "н/д",
                        str(stage.get("reasoning_tokens"))
                        if stage.get("reasoning_tokens") is not None
                        else "unavailable",
                        str(stage.get("total_tokens"))
                        if stage.get("total_tokens") is not None
                        else "н/д",
                        f"{stage.get('input_artifact_count', 'н/д')}/{stage.get('input_artifact_bytes', 'н/д')}",
                        f"{stage.get('output_artifact_count', 'н/д')}/{stage.get('output_artifact_bytes', 'н/д')}",
                    )
                )
                + " |"
            )
    routing = next(
        (
            phase.get("routing_preflight_breakdown")
            for phase in report.get("phases", [])
            if phase.get("phase") == "routing-preflight"
        ),
        None,
    )
    if isinstance(routing, Mapping):
        lines.extend(
            [
                "",
                "## Декомпозиция routing-preflight",
                "",
                "| Компонент | Статус | Время |",
                "| --- | --- | ---: |",
            ]
        )
        for component in routing.get("components", []):
            duration = component.get("duration_ms")
            lines.append(
                f"| {component.get('component')} | {component.get('status')} | "
                f"{_format_duration_ms(duration) if type(duration) is int else 'unavailable'} |"
            )
    external_observations = report.get("external_observations", [])
    if external_observations:
        lines.extend(["", "## Внешняя сверка", ""])
        for item in external_observations:
            lines.append(
                "- "
                f"`{item.get('source')}` / `{item.get('endpoint')}`: "
                f"`{_format_duration_ms(item.get('elapsed_ms'))}`; "
                "разница с внутренним окном "
                f"`{_format_duration_ms(item.get('apparent_delta_ms'))}`."
            )
    root_agent_tokens = report.get("root_agent_token_usage")
    if isinstance(root_agent_tokens, Mapping):
        lines.extend(
            [
                "",
                "## Токены root-agent по фазам",
                "",
                "| Фаза | Events | Input | Cached input | Output | Reasoning output | Total |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        by_phase = root_agent_tokens.get("by_phase", {})
        if not isinstance(by_phase, Mapping) or not by_phase:
            lines.append(
                "| unavailable | unavailable | unavailable | unavailable | "
                "unavailable | unavailable | unavailable |"
            )
            by_phase = {}
        for phase, usage in by_phase.items():
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(phase),
                        str(usage.get("event_count", "н/д")),
                        str(usage.get("input_tokens", "н/д")),
                        str(usage.get("cached_input_tokens", "н/д")),
                        str(usage.get("output_tokens", "н/д")),
                        str(usage.get("reasoning_output_tokens", "н/д")),
                        str(usage.get("total_tokens", "н/д")),
                    )
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def reconcile_external_elapsed(
    path: Path,
    *,
    elapsed_ms: int,
    source: str,
    endpoint: str,
    precision_ms: int = 1,
    turn_id: str | None = None,
    note: str | None = None,
    extra: Mapping[str, Any] | None = None,
    claim_full_user_wall: bool = False,
) -> dict[str, Any]:
    if type(elapsed_ms) is not int or elapsed_ms < 0:
        raise LeanProductionError("elapsed_ms must be a non-negative integer")
    if type(precision_ms) is not int or precision_ms <= 0:
        raise LeanProductionError("precision_ms must be a positive integer")
    if not source.strip() or not endpoint.strip():
        raise LeanProductionError("source and endpoint must be non-empty")
    payload = load_run(path)
    if payload.get("status") == "running":
        raise LeanProductionError("external elapsed can be reconciled only after terminal status")
    observation = payload.get("observation")
    if not isinstance(observation, dict):
        raise LeanProductionError("external elapsed requires an observational timer")
    recorded_turn_id = observation.get("codex_turn_id")
    if turn_id is not None and recorded_turn_id and turn_id != recorded_turn_id:
        raise LeanProductionError("external observation turn_id does not match the timer")
    internal_ms = payload.get("observed_window_ms")
    apparent_delta = elapsed_ms - internal_ms if type(internal_ms) is int else None
    internal_endpoint = observation.get("anchors", {}).get("end", {}).get("kind")
    comparable = internal_endpoint == endpoint
    reasons: list[str] = []
    if not comparable:
        reasons.append("endpoint-mismatch")
    if apparent_delta is not None and apparent_delta < 0:
        reasons.append("external-duration-shorter-than-internal-window")
    if claim_full_user_wall:
        if endpoint not in {"task-complete", "ui-final"}:
            raise LeanProductionError(
                "only task-complete or ui-final may be claimed as full user wall"
            )
        if apparent_delta is not None and apparent_delta < 0:
            raise LeanProductionError(
                "external full user wall cannot be shorter than the internal window"
            )
        if source == "codex-rollout-task-complete" and (
            not turn_id or not recorded_turn_id or turn_id != recorded_turn_id
        ):
            raise LeanProductionError(
                "Codex task-complete claim requires the timer's exact turn_id"
            )
    record = {
        "captured_at_utc": utc_now(),
        "elapsed_ms": elapsed_ms,
        "source": source,
        "endpoint": endpoint,
        "precision_ms": precision_ms,
        "turn_id": turn_id,
        "note": note,
        "internal_observed_window_ms": internal_ms,
        "apparent_delta_ms": apparent_delta,
        "comparable": comparable,
        "comparison_reasons": reasons,
        "unaccounted_ms": apparent_delta if comparable and apparent_delta is not None else None,
        "claim_full_user_wall": claim_full_user_wall,
        **dict(extra or {}),
    }
    existing = observation.setdefault("external_observations", [])
    duplicate = next(
        (
            item
            for item in existing
            if item.get("elapsed_ms") == elapsed_ms
            and item.get("source") == source
            and item.get("endpoint") == endpoint
            and item.get("turn_id") == turn_id
            and item.get("claim_full_user_wall") is claim_full_user_wall
        ),
        None,
    )
    if duplicate is None:
        existing.append(record)
    claimable = [item for item in existing if item.get("claim_full_user_wall") is True]
    if not claimable:
        _write_json_atomic(path, payload)
        return payload
    primary = min(
        claimable,
        key=lambda item: (
            int(item.get("precision_ms", 1_000_000)),
            0 if item.get("source") == "codex-rollout-task-complete" else 1,
        ),
    )
    payload["full_user_wall_ms"] = int(primary["elapsed_ms"])
    observation["coverage"].update(
        {
            "external_label": (
                f"{primary.get('source')}-request-to-{primary.get('endpoint')}"
            ),
            "external_source": primary.get("source"),
            "claimable_as_full_user_wall": True,
        }
    )
    _write_json_atomic(path, payload)
    return payload


def _iso_epoch_ms(value: str) -> int:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LeanProductionError(f"invalid Codex event timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise LeanProductionError("Codex event timestamp must include timezone")
    return int(parsed.timestamp() * 1000)


def _codex_root_token_events(rollout: Path, *, turn_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    active = False
    with rollout.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not active and turn_id not in line:
                continue
            candidate = json.loads(line)
            payload = candidate.get("payload")
            if candidate.get("type") != "event_msg" or not isinstance(payload, Mapping):
                continue
            if payload.get("type") == "task_started" and payload.get("turn_id") == turn_id:
                active = True
                continue
            if not active:
                continue
            if payload.get("type") == "task_complete" and payload.get("turn_id") == turn_id:
                break
            if payload.get("type") != "token_count":
                continue
            info = payload.get("info")
            usage = info.get("last_token_usage") if isinstance(info, Mapping) else None
            timestamp = candidate.get("timestamp")
            if not isinstance(usage, Mapping) or not isinstance(timestamp, str):
                continue
            normalized = {
                field: int(usage[field])
                for field in ROOT_TOKEN_FIELDS
                if type(usage.get(field)) is int and int(usage[field]) >= 0
            }
            if normalized:
                events.append(
                    {
                        "timestamp_utc": timestamp,
                        "epoch_ms": _iso_epoch_ms(timestamp),
                        "usage": normalized,
                    }
                )
    return events


def _attribute_root_token_events(
    payload: Mapping[str, Any],
    events: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    phases = [
        item
        for item in payload.get("phases", [])
        if type(item.get("started_epoch_ms")) is int
        and type(item.get("finished_epoch_ms")) is int
    ]
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    all_usage: list[Mapping[str, Any]] = []
    observation_end = payload.get("finished_epoch_ms")
    for event in events:
        event_ms = event.get("epoch_ms")
        usage = event.get("usage")
        if type(event_ms) is not int or not isinstance(usage, Mapping):
            continue
        all_usage.append(usage)
        matching = [
            item
            for item in phases
            if int(item["started_epoch_ms"]) <= event_ms <= int(item["finished_epoch_ms"])
        ]
        if matching:
            label = str(matching[-1].get("phase") or "unknown-phase")
        elif type(observation_end) is int and event_ms > observation_end:
            label = "post-recorder-to-task-complete"
        else:
            label = "unattributed-root-agent"
        grouped.setdefault(label, []).append(usage)

    def summarize(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        records_tuple = tuple(records)
        return {
            "event_count": len(records_tuple),
            **{field: _sum_optional(records_tuple, field) for field in ROOT_TOKEN_FIELDS},
        }

    return {
        "attribution_method": "token-count completion timestamp within phase interval",
        "total": summarize(all_usage),
        "by_phase": {
            phase: summarize(records) for phase, records in sorted(grouped.items())
        },
    }


def find_codex_task_complete(sessions_root: Path, *, turn_id: str) -> dict[str, Any]:
    if not turn_id.strip():
        raise LeanProductionError("turn_id must be non-empty")
    if not sessions_root.is_dir():
        raise LeanProductionError(f"Codex sessions root does not exist: {sessions_root}")
    matches: list[dict[str, Any]] = []
    for rollout in sessions_root.rglob("*.jsonl"):
        try:
            with rollout.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if turn_id not in line or "task_complete" not in line:
                        continue
                    candidate = json.loads(line)
                    payload = candidate.get("payload")
                    if (
                        candidate.get("type") != "event_msg"
                        or not isinstance(payload, Mapping)
                        or payload.get("type") != "task_complete"
                        or payload.get("turn_id") != turn_id
                    ):
                        continue
                    duration_ms = payload.get("duration_ms")
                    if type(duration_ms) is not int or duration_ms < 0:
                        raise LeanProductionError("Codex task_complete has invalid duration_ms")
                    matches.append(
                        {
                            "turn_id": turn_id,
                            "duration_ms": duration_ms,
                            "started_at": payload.get("started_at"),
                            "completed_at": payload.get("completed_at"),
                            "time_to_first_token_ms": payload.get("time_to_first_token_ms"),
                            "rollout_path": str(rollout.resolve()),
                        }
                    )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LeanProductionError(f"cannot inspect Codex rollout {rollout}: {exc}") from exc
    unique = {
        (item["duration_ms"], item.get("started_at"), item.get("completed_at")): item
        for item in matches
    }
    if not unique:
        raise LeanProductionError(f"Codex task_complete is not available for turn {turn_id}")
    if len(unique) != 1:
        raise LeanProductionError(f"conflicting Codex task_complete records for turn {turn_id}")
    result = next(iter(unique.values()))
    result["root_agent_token_events"] = _codex_root_token_events(
        Path(result["rollout_path"]), turn_id=turn_id
    )
    return result


def reconcile_codex_turn(
    path: Path,
    *,
    sessions_root: Path,
    turn_id: str | None = None,
) -> dict[str, Any]:
    payload = load_run(path)
    observation = payload.get("observation")
    if not isinstance(observation, Mapping):
        raise LeanProductionError("Codex reconciliation requires an observational timer")
    recorded_turn_id = observation.get("codex_turn_id")
    selected_turn_id = turn_id or recorded_turn_id
    if not isinstance(selected_turn_id, str) or not selected_turn_id.strip():
        raise LeanProductionError("turn_id is required for Codex reconciliation")
    if recorded_turn_id and recorded_turn_id != selected_turn_id:
        raise LeanProductionError("turn_id does not match the observational timer")
    completion = find_codex_task_complete(sessions_root, turn_id=selected_turn_id)
    root_agent_tokens = _attribute_root_token_events(
        payload, completion.get("root_agent_token_events", [])
    )
    return reconcile_external_elapsed(
        path,
        elapsed_ms=int(completion["duration_ms"]),
        source="codex-rollout-task-complete",
        endpoint="task-complete",
        precision_ms=1,
        turn_id=selected_turn_id,
        claim_full_user_wall=True,
        extra={
            "time_to_first_token_ms": completion.get("time_to_first_token_ms"),
            "rollout_path": completion.get("rollout_path"),
            "root_agent_token_usage": root_agent_tokens,
        },
    )


FORBIDDEN_SUCCESS_NAMES = {
    "scope-agent-final.md",
    "scope-execution-options.md",
    "exec-backend-config.json",
    "exec-backend-config-reviewer-rebind.json",
}


def audit_handoff(path: Path) -> dict[str, Any]:
    files = tuple(item for item in path.rglob("*") if item.is_file())
    forbidden: list[str] = []
    for item in files:
        relative = item.relative_to(path).as_posix()
        name = item.name
        if (
            name in FORBIDDEN_SUCCESS_NAMES
            or name.endswith("-session-log.md")
            or "session-log." in name
            or name.startswith("agent-decision-log")
            or relative.startswith("artifact-write/")
            or relative.startswith("reviewer-schema-probe-")
        ):
            forbidden.append(relative)
    required = {
        "workflow-state.yaml",
        "source-selection.md",
        "scope-contract.md",
        "scope-coverage-gaps.md",
        "source-row-extraction-spec.json",
        "source-row-baseline.json",
        "source-row-inventory.md",
        "source-assertions.json",
        "atomic-requirements-ledger.md",
        "coverage-obligation-table.md",
        "package-test-design-plan.md",
        "test-design-applicability-matrix.md",
    }
    present = {item.name for item in files}
    return {
        "profile": "lean-production",
        "path": str(path.resolve()),
        "file_count": len(files),
        "bytes": sum(item.stat().st_size for item in files),
        "missing_required": sorted(required - present),
        "forbidden_success_artifacts": sorted(forbidden),
        "status": "pass" if not (required - present) and not forbidden else "fail",
    }
