from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.codex_exec_review_cycle_runner import main as review_cycle_main  # noqa: E402
from scripts.codex_exec_source_assertion_reviewer import (  # noqa: E402
    DEFAULT_MAX_ASSERTIONS_PER_SHARD as SOURCE_REVIEW_MAX_ASSERTIONS_PER_SHARD,
    DEFAULT_MAX_PROMPT_BYTES as SOURCE_REVIEW_MAX_PROMPT_BYTES,
    DEFAULT_MAX_REVIEW_SHARDS as SOURCE_REVIEW_MAX_SHARDS,
    DEFAULT_SHARD_TARGET_PROMPT_BYTES as SOURCE_REVIEW_SHARD_TARGET_PROMPT_BYTES,
    main as source_review_main,
)
from scripts.promote_review_cycle import main as promote_main  # noqa: E402
from scripts.validate_source_assertion_gate import main as source_gate_main  # noqa: E402
from test_case_agent.lean_production import (  # noqa: E402
    LeanProductionError,
    artifact_inventory,
    finish_phase,
    finish_run,
    load_run,
    start_phase,
    terminalize_run,
)
from test_case_agent.review_cycle.prepared_compiler import (  # noqa: E402
    compile_workflow_package,
    load_workflow_state,
    resolve_workflow_compiler_inputs,
)
from test_case_agent.review_cycle.exec_backend import (  # noqa: E402
    ExecCapabilityResolution,
    PLUGIN_ISOLATION_DISABLE_FEATURES,
    resolve_verified_exec_capability,
)
from test_case_agent.review_cycle.metrics import StageMetrics  # noqa: E402
from test_case_agent.review_cycle.runtime import StageRuntimeError  # noqa: E402
from test_case_agent.review_cycle.source_model_adequacy import (  # noqa: E402
    evaluate_pre_review_source_model_adequacy,
)


LEAN_PREPARED_STANDARD_WRITER_CONTEXT_MAX_BYTES = 128 * 1024
LEAN_PREPARED_TARGETED_REPAIR_WRITER_CONTEXT_MAX_BYTES = 192 * 1024


def _under(root: Path, value: str | Path, *, label: str) -> Path:
    path = (Path(value) if Path(value).is_absolute() else root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise LeanProductionError(f"{label} escapes repository root: {path}") from exc
    return path


_STABLE_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def _validate_runtime_boundaries(
    *,
    repo_root: Path,
    workflow_state: Path,
    cycle_dir: Path,
    final_artifact: Path,
    ft_slug: str,
) -> Path:
    if _STABLE_SEGMENT.fullmatch(ft_slug) is None:
        raise LeanProductionError("workflow-state ft_slug must be one stable path segment")
    fts_root = (repo_root / "fts").resolve()
    ft_root = (fts_root / ft_slug).resolve()
    _under(fts_root, ft_root, label="ft-root")
    if not ft_root.is_dir():
        raise LeanProductionError(f"workflow FT package is missing: fts/{ft_slug}")
    _under(ft_root, workflow_state, label="workflow-state")

    review_cycles_root = (ft_root / "work" / "review-cycles").resolve()
    normalized_cycle = _under(review_cycles_root, cycle_dir, label="cycle-dir")
    if (
        normalized_cycle.parent != review_cycles_root
        or _STABLE_SEGMENT.fullmatch(normalized_cycle.name) is None
    ):
        raise LeanProductionError(
            "cycle-dir must equal <ft-root>/work/review-cycles/<cycle-id>"
        )

    test_cases_root = (ft_root / "test-cases").resolve()
    normalized_final = _under(test_cases_root, final_artifact, label="final-artifact")
    if (
        normalized_final.parent != test_cases_root
        or normalized_final.suffix != ".md"
        or normalized_final.name.casefold() == "readme.md"
    ):
        raise LeanProductionError(
            "final-artifact must be one Markdown file directly under <ft-root>/test-cases"
        )
    return ft_root


def _latest_path(
    *,
    repo_root: Path,
    ft_root: Path,
    latest: Mapping[str, Any],
    key: str,
) -> Path:
    raw = latest.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise LeanProductionError(f"workflow latest_artifacts.{key} is required")
    path = _under(ft_root, raw, label=key)
    if key not in {"source_gate_validation", "source_assertion_review"} and not path.is_file():
        raise LeanProductionError(f"workflow artifact is missing: {raw}")
    return path


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LeanProductionError(f"JSON object expected: {path}")
    return payload


def _write_immutable_json(path: Path, payload: Mapping[str, Any]) -> None:
    rendered = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise LeanProductionError(
                f"immutable preflight artifact conflicts with existing file: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(rendered)


_STAGE_ATTEMPT_ID = re.compile(r"attempt-([0-9]{3})")
_MODEL_STAGE_ID = re.compile(r"(writer|reviewer)-r[1-9][0-9]*")
_MODEL_STAGE_ROLES = {"writer", "reviewer"}
LEAN_PREPARED_STANDARD_REVIEWER_CONTEXT_MAX_BYTES = 512 * 1024
PRODUCTION_SOURCE_REVIEW_TIMEOUT_SECONDS = 900
PRODUCTION_WRITER_TIMEOUT_SECONDS = 600
PRODUCTION_REVIEWER_TIMEOUT_SECONDS = 600
_MODEL_TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "total_tokens",
)


class PhaseExecutionError(LeanProductionError):
    def __init__(self, message: str, *, phase_metrics: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.phase_metrics = dict(phase_metrics)


def _required_current_run_model_roles(
    *,
    validate_only: bool,
    iteration_completed: bool,
    reviewer_rebind: bool,
) -> frozenset[str]:
    if validate_only or not iteration_completed:
        return frozenset()
    if reviewer_rebind:
        return frozenset({"reviewer"})
    return frozenset({"writer", "reviewer"})


def _stage_metric_identity(
    payload: Mapping[str, Any],
    *,
    path: Path,
    cycle_dir: Path,
) -> tuple[str, str, str]:
    try:
        metrics = StageMetrics.from_dict(payload)
    except StageRuntimeError as exc:
        raise LeanProductionError(f"invalid stage metric {path}: {exc}") from exc
    identity = (metrics.stage_id, metrics.attempt_id, metrics.role)
    if metrics.role not in _MODEL_STAGE_ROLES:
        raise LeanProductionError(f"stage metric role must be writer or reviewer: {path}")
    stage_match = _MODEL_STAGE_ID.fullmatch(metrics.stage_id)
    if stage_match is None or stage_match.group(1) != metrics.role:
        raise LeanProductionError(
            f"stage metric role does not match stage_id: {path}"
        )
    attempt_match = _STAGE_ATTEMPT_ID.fullmatch(metrics.attempt_id)
    if attempt_match is None or int(attempt_match.group(1)) == 0:
        raise LeanProductionError(f"stage metric attempt_id is not canonical: {path}")
    if metrics.cycle_id != cycle_dir.name:
        raise LeanProductionError(f"stage metric cycle_id does not match cycle: {path}")
    if path.parent.name != metrics.attempt_id or path.parent.parent.name != metrics.stage_id:
        raise LeanProductionError(
            "stage metric identity does not match "
            f"attempts/<stage_id>/<attempt_id>/metrics.json: {path}"
        )
    return identity


def _snapshot_writer_reviewer_metrics(
    cycle_dir: Path,
) -> tuple[dict[tuple[str, str, str], dict[str, Any]] | None, str | None]:
    """Capture immutable metric identity/path/content before or after one invocation."""

    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in sorted(cycle_dir.glob("attempts/*/*/metrics.json")):
        try:
            payload = _json(path)
            identity = _stage_metric_identity(
                payload,
                path=path,
                cycle_dir=cycle_dir,
            )
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError, json.JSONDecodeError, LeanProductionError) as exc:
            return None, str(exc)
        if identity in result:
            return None, f"duplicate stage metric identity: {identity!r}"
        result[identity] = {
            "identity": {
                "stage_id": identity[0],
                "attempt_id": identity[1],
                "role": identity[2],
            },
            "path": str(path.resolve()),
            "digest": digest,
            "payload": payload,
        }
    return result, None


def _published_metric_snapshot(
    snapshot: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "identity": dict(snapshot[identity]["identity"]),
            "path": snapshot[identity]["path"],
            "digest": snapshot[identity]["digest"],
        }
        for identity in sorted(snapshot)
    ]


def _metric_snapshot_digest(
    snapshot: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> str:
    serialized = json.dumps(
        _published_metric_snapshot(snapshot),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _empty_current_run_projection(*, cycle_id: str, reason: str) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "kind": "writer-reviewer-current-run",
        "cycle_id": cycle_id,
        "status": "unknown",
        "attempt_count": None,
        "retry_count": None,
        "token_usage": {field: None for field in _MODEL_TOKEN_FIELDS},
        "input_artifacts": {"file_count": None, "bytes": None},
        "output_artifacts": {"file_count": None, "bytes": None},
        "stage_metrics": [],
        "measurement_error": reason,
        "evidence": {},
    }


def _canonical_reuse_receipt(
    receipt: Mapping[str, Any],
    *,
    cycle_dir: Path,
    snapshot_digest: str,
) -> bool:
    token_usage = receipt.get("token_usage")
    return (
        receipt.get("contract_version") == 1
        and type(receipt.get("contract_version")) is int
        and receipt.get("kind") == "writer-reviewer-current-run-reuse"
        and receipt.get("status") == "reused"
        and receipt.get("cycle_id") == cycle_dir.name
        and type(receipt.get("attempt_count")) is int
        and receipt.get("attempt_count") == 0
        and type(receipt.get("retry_count")) is int
        and receipt.get("retry_count") == 0
        and receipt.get("pre_writer_snapshot_digest") == snapshot_digest
        and isinstance(token_usage, Mapping)
        and set(token_usage) == set(_MODEL_TOKEN_FIELDS)
        and all(
            type(token_usage.get(field)) is int and token_usage.get(field) == 0
            for field in _MODEL_TOKEN_FIELDS
        )
    )


def _project_current_run_stage_metrics(
    *,
    cycle_dir: Path,
    preexisting: Mapping[tuple[str, str, str], Mapping[str, Any]] | None,
    current: Mapping[tuple[str, str, str], Mapping[str, Any]] | None,
    preexisting_error: str | None = None,
    current_error: str | None = None,
    required_roles: frozenset[str] = frozenset(),
    explicit_reuse_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project only immutable metrics first observed during this invocation."""

    if preexisting is None or current is None:
        projection = _empty_current_run_projection(
            cycle_id=cycle_dir.name,
            reason=(
                preexisting_error
                or current_error
                or "writer/reviewer metric snapshot is unavailable"
            )
        )
        projection["evidence"] = {
            "pre_writer_snapshot": [],
            "post_writer_snapshot": [],
        }
        return projection

    pre_snapshot = _published_metric_snapshot(preexisting)
    post_snapshot = _published_metric_snapshot(current)
    evidence: dict[str, Any] = {
        "pre_writer_snapshot": pre_snapshot,
        "post_writer_snapshot": post_snapshot,
        "pre_writer_snapshot_digest": _metric_snapshot_digest(preexisting),
        "ignored_preexisting_metric_count": len(preexisting),
    }
    deleted = set(preexisting) - set(current)
    overwritten = {
        identity
        for identity in set(preexisting) & set(current)
        if (
            preexisting[identity].get("path") != current[identity].get("path")
            or preexisting[identity].get("digest") != current[identity].get("digest")
        )
    }
    if deleted or overwritten:
        projection = _empty_current_run_projection(
            cycle_id=cycle_dir.name,
            reason=(
                "preexisting stage metrics were deleted or overwritten during "
                "the writer-reviewer invocation"
            )
        )
        evidence["deleted_identities"] = [list(item) for item in sorted(deleted)]
        evidence["overwritten_identities"] = [
            list(item) for item in sorted(overwritten)
        ]
        projection["evidence"] = evidence
        return projection

    fresh_ids = set(current) - set(preexisting)
    evidence["current_run_identities"] = [
        dict(current[identity]["identity"]) for identity in sorted(fresh_ids)
    ]
    if explicit_reuse_receipt is not None:
        if fresh_ids:
            projection = _empty_current_run_projection(
                cycle_id=cycle_dir.name,
                reason="explicit reuse receipt conflicts with fresh stage metrics"
            )
            projection["evidence"] = evidence
            return projection
        if not _canonical_reuse_receipt(
            explicit_reuse_receipt,
            cycle_dir=cycle_dir,
            snapshot_digest=evidence["pre_writer_snapshot_digest"],
        ):
            projection = _empty_current_run_projection(
                cycle_id=cycle_dir.name,
                reason="writer/reviewer reuse receipt is not canonical or snapshot-bound"
            )
            projection["evidence"] = evidence
            return projection
        return {
            "contract_version": 1,
            "kind": "writer-reviewer-current-run",
            "cycle_id": cycle_dir.name,
            "status": "reused",
            "attempt_count": 0,
            "retry_count": 0,
            "token_usage": {field: 0 for field in _MODEL_TOKEN_FIELDS},
            "input_artifacts": {"file_count": 0, "bytes": 0},
            "output_artifacts": {"file_count": 0, "bytes": 0},
            "stage_metrics": [],
            "reuse_receipt": dict(explicit_reuse_receipt),
            "evidence": evidence,
        }

    if not fresh_ids:
        projection = _empty_current_run_projection(
            cycle_id=cycle_dir.name,
            reason=(
                "no fresh writer/reviewer stage metrics and no explicit "
                "current-run reuse receipt"
            )
        )
        projection["evidence"] = evidence
        return projection

    roles = {identity[2] for identity in fresh_ids}
    if not required_roles.issubset(roles):
        projection = _empty_current_run_projection(
            cycle_id=cycle_dir.name,
            reason="current-run stage metrics do not cover the required model roles"
        )
        evidence["required_roles"] = sorted(required_roles)
        evidence["observed_roles"] = sorted(roles)
        projection["evidence"] = evidence
        return projection

    stage_metrics = [
        dict(current[identity]["payload"]) for identity in sorted(fresh_ids)
    ]
    token_usage = {
        field: (
            sum(int(item[field]) for item in stage_metrics)
            if all(type(item.get(field)) is int for item in stage_metrics)
            else None
        )
        for field in _MODEL_TOKEN_FIELDS
    }
    if token_usage["total_tokens"] is None:
        input_tokens = token_usage["input_tokens"]
        output_tokens = token_usage["output_tokens"]
        if input_tokens is not None and output_tokens is not None:
            token_usage["total_tokens"] = input_tokens + output_tokens
    retry_count = sum(
        int(identity[1].removeprefix("attempt-")) > 1 for identity in fresh_ids
    )
    return {
        "contract_version": 1,
        "kind": "writer-reviewer-current-run",
        "cycle_id": cycle_dir.name,
        "status": "measured",
        "attempt_count": len(fresh_ids),
        "retry_count": retry_count,
        "token_usage": token_usage,
        "input_artifacts": {
            "file_count": sum(
                int(item["input_artifact_count"]) for item in stage_metrics
            ),
            "bytes": sum(int(item["input_artifact_bytes"]) for item in stage_metrics),
        },
        "output_artifacts": {
            "file_count": sum(
                int(item["output_artifact_count"]) for item in stage_metrics
            ),
            "bytes": sum(int(item["output_artifact_bytes"]) for item in stage_metrics),
        },
        "stage_metrics": stage_metrics,
        "evidence": evidence,
    }


def _source_review_reuse_receipt(
    *,
    source_assertion_review: Path,
    persisted_summary: Path,
) -> dict[str, Any]:
    summary_exists = persisted_summary.is_file()
    return {
        "version": 1,
        "status": "reused",
        "attempt_count": 0,
        "retry_count": 0,
        "reuse_evidence": {
            "source_assertion_review": {
                "path": str(source_assertion_review.resolve()),
                "sha256": hashlib.sha256(
                    source_assertion_review.read_bytes()
                ).hexdigest(),
            },
            "persisted_summary": {
                "path": str(persisted_summary.resolve()),
                "sha256": (
                    hashlib.sha256(persisted_summary.read_bytes()).hexdigest()
                    if summary_exists
                    else None
                ),
            },
        },
    }


def _persist_source_review_reuse_receipt(
    *,
    source_assertion_review: Path,
    persisted_summary: Path,
) -> dict[str, Any]:
    receipt = _source_review_reuse_receipt(
        source_assertion_review=source_assertion_review,
        persisted_summary=persisted_summary,
    )
    if not persisted_summary.is_file():
        _write_immutable_json(persisted_summary, receipt)
    return receipt


def _backend_metrics(resolution: ExecCapabilityResolution) -> dict[str, Any]:
    selected = resolution.selected
    return {
        "selected_executable": resolution.selected_executable,
        "selected_version": selected.version if selected is not None else "",
        "capability_probe_total_ms": resolution.total_duration_ms,
        "capability_probe_count": len(resolution.probes),
        "disable_features": list(resolution.disable_features),
    }


def _register_source_review_audit_artifacts(
    *,
    workflow_state: Path,
    ft_root: Path,
    session_log: Path,
    decision_log: Path,
) -> None:
    """Atomically link standard-profile source-review audit artifacts."""

    for label, path in (
        ("source reviewer session log", session_log),
        ("source reviewer decision log", decision_log),
    ):
        if not path.is_file():
            raise LeanProductionError(f"{label} was not published: {path}")
    updates = {
        "source_assertion_reviewer_session_log": session_log.resolve()
        .relative_to(ft_root.resolve())
        .as_posix(),
        "source_assertion_reviewer_decision_log": decision_log.resolve()
        .relative_to(ft_root.resolve())
        .as_posix(),
    }
    lines = workflow_state.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("latest_artifacts:")
    except ValueError as exc:
        raise LeanProductionError("workflow-state misses latest_artifacts") from exc
    end = len(lines)
    existing: dict[str, str] = {}
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith(" "):
            end = index
            break
        if line.startswith("  ") and ":" in line:
            key, value = line.strip().split(":", 1)
            if key in updates:
                if key in existing:
                    raise LeanProductionError(
                        f"duplicate workflow-state latest_artifacts key: {key}"
                    )
                existing[key] = value.strip()
    mismatches = {
        key: (existing.get(key), value)
        for key, value in updates.items()
        if key in existing and existing[key] != value
    }
    if mismatches:
        raise LeanProductionError(
            "workflow-state source-review audit link mismatch: " + repr(mismatches)
        )
    additions = [
        f"  {key}: {value}" for key, value in updates.items() if key not in existing
    ]
    if not additions:
        return
    rendered = [*lines[:end], *additions, *lines[end:]]
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{workflow_state.name}.", suffix=".tmp", dir=workflow_state.parent
    )
    temporary = Path(raw_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(rendered) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, workflow_state)
    finally:
        temporary.unlink(missing_ok=True)


def _write_pre_promotion_workflow_state(path: Path) -> None:
    """Advance only the canonical top-level handoff fields after reviewer acceptance."""

    updates = {
        "current_stage": "ft-test-case-iteration",
        "stage_status": "ready-for-review",
        "next_skill": "ft-test-case-reviewer",
        "blocking_reasons": "[]",
    }
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    rendered: list[str] = []
    for line in lines:
        if line.startswith(" ") or ":" not in line:
            rendered.append(line)
            continue
        key = line.split(":", 1)[0]
        if key in updates:
            if key in seen:
                raise LeanProductionError(f"duplicate workflow-state key: {key}")
            rendered.append(f"{key}: {updates[key]}")
            seen.add(key)
        else:
            rendered.append(line)
    missing = set(updates) - seen
    if missing:
        raise LeanProductionError(
            "workflow-state misses pre-promotion keys: " + ", ".join(sorted(missing))
        )
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(rendered) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _phase(
    timer: Path | None,
    name: str,
    action: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    if timer is not None:
        start_phase(timer, phase=name)
    started = time.perf_counter_ns()
    try:
        metrics = action()
    except Exception as exc:
        failure_metrics = getattr(exc, "phase_metrics", {})
        if not isinstance(failure_metrics, Mapping):
            failure_metrics = {}
        if timer is not None:
            finish_phase(
                timer,
                phase=name,
                status="failed",
                metrics={
                    "wall_ms": (time.perf_counter_ns() - started) // 1_000_000,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    **dict(failure_metrics),
                },
            )
        raise
    metrics = {"wall_ms": (time.perf_counter_ns() - started) // 1_000_000, **metrics}
    if timer is not None:
        finish_phase(timer, phase=name, status="completed", metrics=metrics)
    return metrics


def _run_or_fail(label: str, main: Callable[[Sequence[str] | None], int], argv: list[str]) -> None:
    result = main(argv)
    if result != 0:
        raise LeanProductionError(f"{label} exited with code {result}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Run source review, compile, writer, independent reviewer and controlled "
            "promotion without saved dispatcher config or user pauses."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--workflow-state", type=Path, required=True)
    result.add_argument("--cycle-dir", type=Path, required=True)
    result.add_argument("--final-artifact", type=Path, required=True)
    result.add_argument("--package-id", default="WP-01")
    result.add_argument("--timer", type=Path)
    result.add_argument(
        "--defer-timer-finish",
        action="store_true",
        help="Leave the caller-owned timer running so final reporting is measured outside this runner.",
    )
    result.add_argument("--codex-command")
    result.add_argument(
        "--measurement-mode",
        choices=("observational", "production"),
        default="production",
    )
    result.add_argument(
        "--workflow-profile",
        choices=("lean-production", "standard-production"),
        default="lean-production",
        help="Controls profile-specific audit artifacts without changing model semantics.",
    )
    result.add_argument(
        "--model-timeout-seconds",
        type=int,
        help="Deprecated all-stage override; 0 disables the hard timeout.",
    )
    result.add_argument("--source-review-timeout-seconds", type=int)
    result.add_argument("--writer-timeout-seconds", type=int)
    result.add_argument("--reviewer-timeout-seconds", type=int)
    result.add_argument("--allow-overwrite", action="store_true")
    result.add_argument("--prepared-repair-draft", type=Path)
    result.add_argument("--prepared-repair-findings", type=Path)
    result.add_argument("--prepared-reviewer-rebind-draft", type=Path)
    result.add_argument("--source-first-terminal-handoff-dir", type=Path)
    result.add_argument("--validate-only", action="store_true")
    return result


def _effective_stage_timeouts(args: argparse.Namespace) -> dict[str, int]:
    defaults = (
        {"source_review": 0, "writer": 0, "reviewer": 0}
        if args.measurement_mode == "observational"
        else {
            "source_review": PRODUCTION_SOURCE_REVIEW_TIMEOUT_SECONDS,
            "writer": PRODUCTION_WRITER_TIMEOUT_SECONDS,
            "reviewer": PRODUCTION_REVIEWER_TIMEOUT_SECONDS,
        }
    )
    if args.model_timeout_seconds is not None:
        defaults = {key: args.model_timeout_seconds for key in defaults}
    overrides = {
        "source_review": args.source_review_timeout_seconds,
        "writer": args.writer_timeout_seconds,
        "reviewer": args.reviewer_timeout_seconds,
    }
    for key, value in overrides.items():
        if value is not None:
            defaults[key] = value
    if any(type(value) is not int or value < 0 for value in defaults.values()):
        raise LeanProductionError("model stage timeouts must be non-negative integers")
    return defaults


def _write_failure_diagnostic(
    *,
    cycle_dir: Path,
    timer: Path | None,
    error: Exception,
    stage_timeouts: Mapping[str, int],
    measurement_mode: str,
) -> Path | None:
    cycle_dir.mkdir(parents=True, exist_ok=True)
    path = cycle_dir / "failure-diagnostic.json"
    if path.exists():
        return None
    timer_payload: Mapping[str, Any] | None = None
    if timer is not None and timer.is_file():
        try:
            timer_payload = load_run(timer)
        except Exception:  # noqa: BLE001 - diagnostic must not mask root failure.
            timer_payload = None
    payload = {
        "version": 1,
        "status": "failed",
        "recorded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "error_type": type(error).__name__,
        "error": str(error),
        "measurement_mode": measurement_mode,
        "stage_timeouts_seconds": dict(stage_timeouts),
        "timer": str(timer) if timer is not None else None,
        "failed_phase": (
            timer_payload.get("phases", [])[-1].get("phase")
            if isinstance(timer_payload, Mapping)
            and isinstance(timer_payload.get("phases"), list)
            and timer_payload["phases"]
            and isinstance(timer_payload["phases"][-1], Mapping)
            else None
        ),
        "continuation_policy": (
            "Do not resume this cycle after a model attempt. Fix infrastructure or "
            "configuration outside the benchmark and start a fresh immutable cycle."
        ),
    }
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    stage_timeouts = _effective_stage_timeouts(args)
    repo_root = args.repo_root.resolve()
    workflow_state = _under(repo_root, args.workflow_state, label="workflow-state")
    cycle_dir = _under(repo_root, args.cycle_dir, label="cycle-dir")
    final_artifact = _under(repo_root, args.final_artifact, label="final-artifact")
    timer = _under(repo_root, args.timer, label="timer") if args.timer else None
    terminal_artifact_roots: tuple[Path, ...] = ()
    try:
        state = load_workflow_state(workflow_state)
        ft_slug = str(state.get("ft_slug", ""))
        scope_slug = str(state.get("scope_slug", ""))
        section_id = str(state.get("section_id", "")).strip('"')
        if not ft_slug or not scope_slug or not section_id:
            raise LeanProductionError("workflow-state requires ft_slug, scope_slug and section_id")
        ft_root = _validate_runtime_boundaries(
            repo_root=repo_root,
            workflow_state=workflow_state,
            cycle_dir=cycle_dir,
            final_artifact=final_artifact,
            ft_slug=ft_slug,
        )
        if (args.prepared_repair_draft is None) != (
            args.prepared_repair_findings is None
        ):
            raise LeanProductionError(
                "targeted repair requires both --prepared-repair-draft and "
                "--prepared-repair-findings"
            )
        prepared_repair_draft = (
            _under(
                ft_root,
                _under(
                    repo_root,
                    args.prepared_repair_draft,
                    label="prepared-repair-draft",
                ),
                label="prepared-repair-draft",
            )
            if args.prepared_repair_draft is not None
            else None
        )
        prepared_repair_findings = (
            _under(
                ft_root,
                _under(
                    repo_root,
                    args.prepared_repair_findings,
                    label="prepared-repair-findings",
                ),
                label="prepared-repair-findings",
            )
            if args.prepared_repair_findings is not None
            else None
        )
        prepared_reviewer_rebind_draft = (
            _under(
                ft_root,
                _under(
                    repo_root,
                    args.prepared_reviewer_rebind_draft,
                    label="prepared-reviewer-rebind-draft",
                ),
                label="prepared-reviewer-rebind-draft",
            )
            if args.prepared_reviewer_rebind_draft is not None
            else None
        )
        source_first_terminal_handoff_dir = (
            _under(
                ft_root,
                _under(
                    repo_root,
                    args.source_first_terminal_handoff_dir,
                    label="source-first-terminal-handoff-dir",
                ),
                label="source-first-terminal-handoff-dir",
            )
            if args.source_first_terminal_handoff_dir is not None
            else None
        )
        promotion_workflow_state = workflow_state
        if source_first_terminal_handoff_dir is not None:
            handoff_root = (ft_root / "work" / "stage-handoffs").resolve()
            try:
                relative_handoff = source_first_terminal_handoff_dir.relative_to(
                    handoff_root
                )
            except ValueError as exc:
                raise LeanProductionError(
                    "source-first terminal handoff must be under "
                    "ft_root/work/stage-handoffs"
                ) from exc
            if len(relative_handoff.parts) != 1 or re.fullmatch(
                r"[0-9]+-[A-Za-z0-9_.-]+", relative_handoff.name
            ) is None:
                raise LeanProductionError(
                    "source-first terminal handoff must be one direct numbered directory"
                )
            promotion_workflow_state = (
                source_first_terminal_handoff_dir / "workflow-state.yaml"
            )
            if not promotion_workflow_state.is_file():
                raise LeanProductionError(
                    "source-first terminal handoff is missing workflow-state.yaml"
                )
            promotion_state = load_workflow_state(promotion_workflow_state)
            if (
                promotion_state.get("ft_slug") != ft_slug
                or promotion_state.get("scope_slug") != scope_slug
                or str(promotion_state.get("section_id", "")).strip('"')
                != section_id
            ):
                raise LeanProductionError(
                    "source-first terminal workflow identity does not match the input workflow"
                )
        if (
            prepared_reviewer_rebind_draft is not None
            and prepared_repair_draft is not None
        ):
            raise LeanProductionError(
                "reviewer rebind and targeted repair are mutually exclusive"
            )
        terminal_artifact_roots = (promotion_workflow_state.parent, cycle_dir)
        latest = state.get("latest_artifacts")
        if not isinstance(latest, Mapping):
            raise LeanProductionError("workflow-state latest_artifacts must be a mapping")

        paths = {
            key: _latest_path(repo_root=repo_root, ft_root=ft_root, latest=latest, key=key)
            for key in (
                "source_selection",
                "source_row_inventory",
                "source_row_extraction_spec",
                "source_row_baseline",
                "source_assertions",
                "source_gate_validation",
                "source_assertion_review",
                "atomic_requirements_ledger",
                "coverage_obligation_table",
                "package_test_design_plan",
                "test_design_applicability_matrix",
            )
        }
        prompt_key = (
            "source_assertion_review_prompt"
            if latest.get("source_assertion_review_prompt")
            else "active_transition_prompt"
        )
        review_prompt = _latest_path(
            repo_root=repo_root,
            ft_root=ft_root,
            latest=latest,
            key=prompt_key,
        )
        dictionary_inventory = (
            _latest_path(
                repo_root=repo_root,
                ft_root=ft_root,
                latest=latest,
                key="dictionary_inventory",
            )
            if latest.get("dictionary_inventory")
            else None
        )
        source_model_adequacy_path = cycle_dir / "source-model-adequacy.json"

        def source_model_adequacy_phase() -> dict[str, Any]:
            report = evaluate_pre_review_source_model_adequacy(
                paths["source_assertions"],
                coverage_obligation_table=paths["coverage_obligation_table"],
                package_test_design_plan=paths["package_test_design_plan"],
                dictionary_inventory=dictionary_inventory,
            )
            _write_immutable_json(source_model_adequacy_path, report)
            if report["passed"] is not True:
                exact_length = report["exact_length"]
                failed = [
                    f"{item['source_row_id']}:{','.join(item['missing_classes'])}"
                    for item in exact_length["rules"]
                    if item["passed"] is not True
                ]
                failed.extend(
                    f"{item['assertion_id']}:{','.join(item['conflicting_literals'])}"
                    for item in report["reference_fixture_actions"]["conflicts"]
                )
                raise LeanProductionError(
                    "pre-review source model adequacy failed: "
                    + "; ".join(failed)
                )
            return {
                "validator": report["validator"],
                "exact_length_rule_count": report["exact_length"]["rule_count"],
                "reference_fixture_assertion_count": report[
                    "reference_fixture_actions"
                ]["checked_assertion_count"],
                "conflict_count": report["reference_fixture_actions"][
                    "conflict_count"
                ],
                "output_artifacts": artifact_inventory(
                    (source_model_adequacy_path,)
                ),
            }

        source_model_adequacy_metrics = _phase(
            timer,
            "source-model-adequacy",
            source_model_adequacy_phase,
        )
        backend_resolution = resolve_verified_exec_capability(
            args.codex_command,
            additional_required_flags=(
                "--ephemeral",
                "--ignore-user-config",
                "--color",
            ),
            required_disable_features=PLUGIN_ISOLATION_DISABLE_FEATURES,
        )
        backend_capability = backend_resolution.selection_capability()
        if not backend_resolution.verified:
            raise LeanProductionError(
                "no verified codex exec backend for lean production: "
                + (
                    backend_capability.error
                    or ", ".join(backend_capability.missing_flags)
                )
            )
        selected_codex = backend_resolution.selected_executable

        runtime = cycle_dir / "_runtime" / "source-review"
        source_summary = cycle_dir / "source-review-summary.json"
        source_review_session_log = (
            workflow_state.parent / "reviewer-session-log.source-assertion.md"
        )
        source_review_decision_log = (
            workflow_state.parent / "agent-decision-log.source-assertion-review.md"
        )
        source_review_audit_required = args.workflow_profile == "standard-production"
        bounded_extracts = [
            _under(ft_root, value, label=key)
            for key, value in latest.items()
            if key.startswith("bounded_evidence_")
            and not key.endswith("_selection")
            and isinstance(value, str)
        ]
        source_review_preexisting = {
            "source_gate_validation": paths["source_gate_validation"].is_file(),
            "source_assertion_review": paths["source_assertion_review"].is_file(),
            "source_summary": source_summary.is_file(),
            "source_review_session_log": source_review_session_log.is_file(),
            "source_review_decision_log": source_review_decision_log.is_file(),
        }

        def source_review_phase() -> dict[str, Any]:
            if not paths["source_gate_validation"].is_file():
                _run_or_fail(
                    "source gate",
                    source_gate_main,
                    [
                        "--repo-root", str(repo_root),
                        "--ft-root", str(ft_root),
                        "--source-row-inventory", str(paths["source_row_inventory"]),
                        "--manifest", str(paths["source_assertions"]),
                        "--source-selection", str(paths["source_selection"]),
                        "--source-row-extraction-spec", str(paths["source_row_extraction_spec"]),
                        "--source-row-baseline", str(paths["source_row_baseline"]),
                        "--atomic-requirements-ledger", str(paths["atomic_requirements_ledger"]),
                        "--coverage-obligation-table", str(paths["coverage_obligation_table"]),
                        "--output", str(paths["source_gate_validation"]),
                    ],
                )
            if not paths["source_assertion_review"].is_file():
                source_args = [
                    "--repo-root", str(repo_root),
                    "--manifest", str(paths["source_assertions"]),
                    "--source-gate-receipt", str(paths["source_gate_validation"]),
                    "--review-prompt", str(review_prompt),
                    "--source-row-inventory", str(paths["source_row_inventory"]),
                    "--source-row-extraction-spec", str(paths["source_row_extraction_spec"]),
                    "--source-row-baseline", str(paths["source_row_baseline"]),
                    "--receipt-output", str(paths["source_assertion_review"]),
                    "--events-output", str(runtime / "events.ndjson"),
                    "--stderr-output", str(runtime / "stderr.txt"),
                    "--summary-output", str(source_summary),
                    "--schema-output", str(runtime / "output-schema.json"),
                    "--context-output", str(runtime / "context.json"),
                    "--codex-command", selected_codex,
                    "--timeout-seconds", str(stage_timeouts["source_review"]),
                    "--max-prompt-bytes", str(SOURCE_REVIEW_MAX_PROMPT_BYTES),
                    "--max-review-shards", str(SOURCE_REVIEW_MAX_SHARDS),
                    "--shard-target-prompt-bytes",
                    str(SOURCE_REVIEW_SHARD_TARGET_PROMPT_BYTES),
                    "--max-assertions-per-shard",
                    str(SOURCE_REVIEW_MAX_ASSERTIONS_PER_SHARD),
                ]
                for extract in bounded_extracts:
                    source_args.extend(("--bounded-extract", str(extract)))
                if source_review_audit_required:
                    source_args.extend(
                        (
                            "--session-log-output",
                            str(source_review_session_log),
                            "--decision-log-output",
                            str(source_review_decision_log),
                            "--audit-ft-slug",
                            ft_slug,
                        )
                    )
                result = source_review_main(source_args)
                if result != 0:
                    summary = _json(source_summary) if source_summary.is_file() else {}
                    attempt_count = summary.get("attempt_count")
                    duration_ms = summary.get("duration_ms")
                    failure_inputs = [
                        paths[key]
                        for key in (
                            "source_selection",
                            "source_row_inventory",
                            "source_row_extraction_spec",
                            "source_row_baseline",
                            "source_assertions",
                            "source_gate_validation",
                            "atomic_requirements_ledger",
                            "coverage_obligation_table",
                        )
                    ]
                    failure_inputs.extend((review_prompt, *bounded_extracts))
                    failure_outputs = tuple(
                        path
                        for path in (
                            paths["source_assertion_review"],
                            source_summary,
                            runtime / "events.ndjson",
                            runtime / "stderr.txt",
                            runtime / "output-schema.json",
                            runtime / "context.json",
                            source_review_session_log,
                            source_review_decision_log,
                        )
                        if path.exists()
                    )
                    failure_metrics: dict[str, Any] = {
                        "summary": summary,
                        "model_attempt_evidence_complete": (
                            type(attempt_count) is int and attempt_count >= 0
                        ),
                        "runtime_configuration": {
                            "measurement_mode": args.measurement_mode,
                            "model_timeout_seconds": stage_timeouts["source_review"],
                            "max_prompt_bytes": SOURCE_REVIEW_MAX_PROMPT_BYTES,
                            "shard_target_prompt_bytes": (
                                SOURCE_REVIEW_SHARD_TARGET_PROMPT_BYTES
                            ),
                            "max_assertions_per_shard": (
                                SOURCE_REVIEW_MAX_ASSERTIONS_PER_SHARD
                            ),
                            "max_review_shards": SOURCE_REVIEW_MAX_SHARDS,
                        },
                        "input_artifacts": artifact_inventory(failure_inputs),
                        "output_artifacts": artifact_inventory(failure_outputs),
                    }
                    if type(duration_ms) is int and type(attempt_count) is int:
                        failure_metrics["model_stage"] = {
                            "stage_id": "source-review",
                            "role": "source-reviewer",
                            "duration_ms": duration_ms,
                            "attempt_count": attempt_count,
                        }
                    raise PhaseExecutionError(
                        f"source assertion reviewer exited with code {result}",
                        phase_metrics=failure_metrics,
                    )
            if (
                source_review_audit_required
                and source_review_preexisting["source_assertion_review"]
                and not (
                    source_review_preexisting["source_review_session_log"]
                    and source_review_preexisting["source_review_decision_log"]
                )
            ):
                raise LeanProductionError(
                    "standard-production cannot reuse a source review without its "
                    "reviewer session and decision audit logs"
                )
            summary = (
                _persist_source_review_reuse_receipt(
                    source_assertion_review=paths["source_assertion_review"],
                    persisted_summary=source_summary,
                )
                if source_review_preexisting["source_assertion_review"]
                else _json(source_summary)
            )
            if source_review_audit_required:
                _register_source_review_audit_artifacts(
                    workflow_state=workflow_state,
                    ft_root=ft_root,
                    session_log=source_review_session_log,
                    decision_log=source_review_decision_log,
                )
            entry_inputs = [
                paths[key]
                for key in (
                    "source_selection",
                    "source_row_inventory",
                    "source_row_extraction_spec",
                    "source_row_baseline",
                    "source_assertions",
                    "atomic_requirements_ledger",
                    "coverage_obligation_table",
                )
            ]
            entry_inputs.extend((review_prompt, *bounded_extracts))
            reused_inputs = [
                paths[key]
                for key in ("source_gate_validation", "source_assertion_review")
                if source_review_preexisting[key]
            ]
            if source_review_preexisting["source_summary"]:
                reused_inputs.append(source_summary)
            if source_review_audit_required:
                for key, path in (
                    ("source_review_session_log", source_review_session_log),
                    ("source_review_decision_log", source_review_decision_log),
                ):
                    if source_review_preexisting[key]:
                        reused_inputs.append(path)
            produced_outputs = [
                paths[key]
                for key in ("source_gate_validation", "source_assertion_review")
                if not source_review_preexisting[key]
            ]
            if not source_review_preexisting["source_summary"]:
                produced_outputs.append(source_summary)
            if source_review_audit_required:
                for key, path in (
                    ("source_review_session_log", source_review_session_log),
                    ("source_review_decision_log", source_review_decision_log),
                ):
                    if not source_review_preexisting[key]:
                        produced_outputs.append(path)
            return {
                "summary": summary,
                "runtime_configuration": {
                    "measurement_mode": args.measurement_mode,
                    "model_timeout_seconds": stage_timeouts["source_review"],
                    "max_prompt_bytes": SOURCE_REVIEW_MAX_PROMPT_BYTES,
                    "shard_target_prompt_bytes": SOURCE_REVIEW_SHARD_TARGET_PROMPT_BYTES,
                    "max_assertions_per_shard": SOURCE_REVIEW_MAX_ASSERTIONS_PER_SHARD,
                    "max_review_shards": SOURCE_REVIEW_MAX_SHARDS,
                    "exec_backend": _backend_metrics(backend_resolution),
                },
                "input_artifacts": artifact_inventory((*entry_inputs, *reused_inputs)),
                "reused_artifacts": artifact_inventory(reused_inputs),
                "output_artifacts": artifact_inventory(produced_outputs),
                "workflow_audit_links_registered": source_review_audit_required,
            }

        source_metrics = _phase(timer, "source-review", source_review_phase)

        prepared_root = cycle_dir / "prepared-input" / args.package_id
        attempt_root = cycle_dir / "attempts" / "writer-r1" / "attempt-001"

        def compile_phase() -> dict[str, Any]:
            compiler_inputs = resolve_workflow_compiler_inputs(
                workflow_state=workflow_state,
                repo_root=repo_root,
                expected_ft_slug=ft_slug,
            )
            input_inventory = artifact_inventory(tuple(compiler_inputs.values()))
            compiled = compile_workflow_package(
                workflow_state=workflow_state,
                repo_root=repo_root,
                output_root=prepared_root,
                package_id=args.package_id,
                attempt_root=attempt_root,
                expected_ft_slug=ft_slug,
                section_id=section_id,
                reuse_if_current=True,
            )
            return {
                "obligation_count": compiled.obligation_count,
                "gap_count": compiled.gap_count,
                "cache_reused": compiled.cache_reused,
                "input_roles": sorted(compiler_inputs),
                "input_artifacts": input_inventory,
                "output_artifacts": artifact_inventory((prepared_root,)),
            }

        compile_metrics = _phase(timer, "compile-preflight", compile_phase)
        stage_package = prepared_root / "stage-package.json"
        writer_shard_size = 14
        writer_max_shards = max(
            1,
            (int(compile_metrics["obligation_count"]) + writer_shard_size - 1)
            // writer_shard_size,
        )
        writer_max_concurrency = 1
        writer_context_max_bytes = (
            LEAN_PREPARED_TARGETED_REPAIR_WRITER_CONTEXT_MAX_BYTES
            if prepared_repair_draft is not None
            else LEAN_PREPARED_STANDARD_WRITER_CONTEXT_MAX_BYTES
        )

        runner_args = [
            "--ft-root", str(ft_root),
            "--cycle-dir", str(cycle_dir),
            "--final-artifact", str(final_artifact),
            "--prepared-package", str(stage_package),
            "--prepared-standard-writer-mode", "structured",
            "--codex-command", selected_codex,
            "--sandbox-flag=--sandbox",
            "--writer-sandbox", "workspace-write",
            "--reviewer-sandbox", "read-only",
            "--working-directory-flag=--cd",
            "--json-flag=--json",
            "--output-last-message-flag=--output-last-message",
            "--output-schema-flag=--output-schema",
            "--cli-contract-verified",
            "--writer-timeout-seconds", str(stage_timeouts["writer"]),
            "--reviewer-timeout-seconds", str(stage_timeouts["reviewer"]),
            "--prepared-reviewer-timeout-seconds", str(stage_timeouts["reviewer"]),
            "--writer-idle-timeout-seconds", "90",
            "--reviewer-idle-timeout-seconds", "90",
            "--prepared-standard-reviewer-idle-timeout-seconds", "90",
            "--writer-command-budget", "1",
            "--reviewer-command-budget", "1",
            "--prepared-reviewer-command-budget", "1",
            "--prepared-standard-writer-context-max-bytes",
            str(writer_context_max_bytes),
            "--prepared-standard-reviewer-context-max-bytes",
            str(LEAN_PREPARED_STANDARD_REVIEWER_CONTEXT_MAX_BYTES),
            "--prepared-structured-writer-single-session-tc-limit", "14",
            "--prepared-structured-writer-shard-size", str(writer_shard_size),
            "--prepared-structured-writer-max-shards", str(writer_max_shards),
            "--prepared-structured-writer-max-concurrency", str(writer_max_concurrency),
            "--prepared-structured-reviewer-obligation-limit", "192",
        ]
        if prepared_repair_draft is not None and prepared_repair_findings is not None:
            runner_args.extend(
                (
                    "--prepared-repair-draft",
                    str(prepared_repair_draft.relative_to(repo_root)),
                    "--prepared-repair-findings",
                    str(prepared_repair_findings.relative_to(repo_root)),
                )
            )
        if prepared_reviewer_rebind_draft is not None:
            runner_args.extend(
                (
                    "--prepared-reviewer-rebind-draft",
                    str(prepared_reviewer_rebind_draft.relative_to(repo_root)),
                )
            )
        if source_first_terminal_handoff_dir is not None:
            runner_args.extend(
                (
                    "--source-first-terminal-handoff-dir",
                    str(source_first_terminal_handoff_dir.relative_to(repo_root)),
                )
            )
        runner_args.extend(
            f"--extra-arg={value}" for value in backend_resolution.disable_args
        )
        if args.validate_only:
            runner_args.append("--validate-only")

        def iteration_phase() -> dict[str, Any]:
            (
                preexisting_stage_metrics,
                preexisting_stage_metrics_error,
            ) = _snapshot_writer_reviewer_metrics(cycle_dir)
            result = review_cycle_main(runner_args)
            current_stage_metrics, current_stage_metrics_error = (
                _snapshot_writer_reviewer_metrics(cycle_dir)
            )
            cycle_state_path = cycle_dir / "cycle-state.yaml"
            cycle_state = (
                load_workflow_state(cycle_state_path)
                if cycle_state_path.is_file()
                else {}
            )
            accepted_not_promoted = (
                cycle_state.get("accepted_terminal_state") is True
                and cycle_state.get("final_promoted") is False
                and cycle_state.get("workflow_status")
                in {
                    "accepted-not-promoted",
                    "accepted-promotion-ready-not-promoted",
                }
            )
            current_run_projection = _project_current_run_stage_metrics(
                cycle_dir=cycle_dir,
                preexisting=preexisting_stage_metrics,
                current=current_stage_metrics,
                preexisting_error=preexisting_stage_metrics_error,
                current_error=current_stage_metrics_error,
                required_roles=_required_current_run_model_roles(
                    validate_only=args.validate_only,
                    iteration_completed=result == 0 or accepted_not_promoted,
                    reviewer_rebind=prepared_reviewer_rebind_draft is not None,
                ),
            )
            if result != 0:
                if not accepted_not_promoted:
                    raise LeanProductionError(
                        f"writer-reviewer runner exited with code {result}"
                    )
            performance = cycle_dir / "performance.json"
            result_metrics: dict[str, Any] = {
                "current_run_projection": current_run_projection,
                "stage_metrics": list(current_run_projection["stage_metrics"]),
                "input_artifacts": dict(current_run_projection["input_artifacts"]),
                "output_artifacts": dict(current_run_projection["output_artifacts"]),
                "model_attempt_evidence": {
                    key: current_run_projection.get(key)
                    for key in (
                        "contract_version",
                        "kind",
                        "cycle_id",
                        "status",
                        "attempt_count",
                        "retry_count",
                        "token_usage",
                        "measurement_error",
                    )
                    if key in current_run_projection
                },
            }
            if performance.is_file():
                result_metrics["excluded_historical_performance"] = {
                    "path": str(performance.resolve()),
                    "digest": hashlib.sha256(performance.read_bytes()).hexdigest(),
                    "excluded_from_current_run_projection": True,
                }
            else:
                result_metrics.update({
                    "accepted_not_promoted": True,
                    "cycle_state": str(cycle_dir / "cycle-state.yaml"),
                })
            result_metrics["runtime_configuration"] = {
                "measurement_mode": args.measurement_mode,
                "writer_timeout_seconds": stage_timeouts["writer"],
                "reviewer_timeout_seconds": stage_timeouts["reviewer"],
                "writer_idle_timeout_seconds": 90,
                "reviewer_idle_timeout_seconds": 90,
                "writer_max_concurrency": writer_max_concurrency,
                "writer_context_max_bytes": writer_context_max_bytes,
                "writer_command_budget": 1,
                "reviewer_command_budget": 1,
                "exec_backend": _backend_metrics(backend_resolution),
            }
            result_metrics["historical_cycle_inventory"] = {
                "authoritative_for_current_run": False,
                **artifact_inventory((cycle_dir,)),
            }
            return result_metrics

        iteration_metrics = _phase(timer, "writer-reviewer", iteration_phase)
        if args.validate_only:
            final_timer = None
            if timer is not None and not args.defer_timer_finish:
                final_timer = finish_run(
                    timer,
                    status="validated",
                    test_case_count=0,
                    artifact_roots=terminal_artifact_roots,
                )
            elif timer is not None:
                deferred = load_run(timer)
                final_timer = {
                    "status": deferred.get("status"),
                    "timer_deferred": True,
                    "phase_count": len(deferred.get("phases", [])),
                }
            print(
                json.dumps(
                    {
                        "status": "validated",
                        "source_review": source_metrics,
                        "compile": compile_metrics,
                        "iteration": iteration_metrics,
                        "full_workflow": final_timer,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        cycle_state = load_workflow_state(cycle_dir / "cycle-state.yaml")
        if not (
            cycle_state.get("accepted_terminal_state") is True
            and cycle_state.get("reviewer_stage_status") == "accepted"
            and cycle_state.get("final_promoted") is False
        ):
            raise LeanProductionError(
                "writer-reviewer cycle is not an accepted pre-promotion terminal state"
            )
        _write_pre_promotion_workflow_state(promotion_workflow_state)

        def promotion_phase() -> dict[str, Any]:
            input_inventory = artifact_inventory((cycle_dir,))
            promotion_args = [
                "--repo-root", str(repo_root),
                "--cycle-dir", str(cycle_dir),
                "--target-slo-ms", "15000",
                "--hard-slo-ms", "30000",
            ]
            if args.allow_overwrite:
                promotion_args.append("--allow-overwrite")
            _run_or_fail("controlled promotion", promote_main, promotion_args)
            metrics_files = sorted(cycle_dir.glob("promotion/*/promotion-metrics.json"))
            result_metrics = (
                {"promotion": _json(metrics_files[-1])} if metrics_files else {}
            )
            result_metrics["input_artifacts"] = input_inventory
            result_metrics["output_artifacts"] = artifact_inventory(
                (final_artifact, cycle_dir / "promotion")
            )
            return result_metrics

        promotion_metrics = _phase(timer, "promotion", promotion_phase)
        tc_count = 0
        if final_artifact.is_file():
            tc_count = sum(
                line.startswith("## TC-")
                for line in final_artifact.read_text(encoding="utf-8").splitlines()
            )
        final_timer = None
        if timer is not None and not args.defer_timer_finish:
            final_timer = finish_run(
                timer,
                status="signed-off",
                test_case_count=tc_count,
                artifact_roots=(
                    promotion_workflow_state.parent,
                    cycle_dir,
                    final_artifact,
                ),
            )
        elif timer is not None:
            deferred = load_run(timer)
            final_timer = {
                "status": deferred.get("status"),
                "timer_deferred": True,
                "phase_count": len(deferred.get("phases", [])),
            }
        print(
            json.dumps(
                {
                    "status": "signed-off",
                    "final_artifact": final_artifact.relative_to(repo_root).as_posix(),
                    "test_case_count": tc_count,
                    "source_model_adequacy": source_model_adequacy_metrics,
                    "source_review": source_metrics,
                    "compile": compile_metrics,
                    "iteration": iteration_metrics,
                    "promotion": promotion_metrics,
                    "full_workflow": final_timer,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - terminal one-command boundary.
        if timer is not None and timer.is_file() and not args.defer_timer_finish:
            try:
                terminalize_run(
                    timer,
                    status="blocked",
                    error_type=type(exc).__name__,
                    error=str(exc),
                    test_case_count=0,
                    artifact_roots=terminal_artifact_roots,
                )
            except Exception:
                pass
        try:
            _write_failure_diagnostic(
                cycle_dir=cycle_dir,
                timer=timer,
                error=exc,
                stage_timeouts=stage_timeouts,
                measurement_mode=args.measurement_mode,
            )
        except Exception:
            pass
        print(
            json.dumps(
                {"status": "blocked", "error_type": type(exc).__name__, "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
