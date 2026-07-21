from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.stage_failure_contract import (
    StageFailureEnvelope,
    StageFailureWriteError,
    write_stage_failure_exclusive,
)
from test_case_agent.bounded_scope_boundary import (
    BoundedScopeBoundaryError,
    CANONICAL_GAP_TYPES,
    declared_dictionary_values as _canonical_declared_dictionary_values,
    dictionary_has_inline_values as _canonical_dictionary_has_inline_values,
    external_dynamic_dictionary_bindings as _canonical_external_dynamic_dictionary_bindings,
    expected_dependency_inventory as _canonical_expected_dependency_inventory,
    is_global_type_definition_row as _canonical_is_global_type_definition_row,
    normalize_entity as _canonical_normalize_entity,
    validate_bounded_scope_context as _canonical_validate_scope_context,
    validate_boundary_decision_v2 as _canonical_validate_decision,
    validate_source_cache_binding as _canonical_validate_source_cache_binding,
)
from test_case_agent.review_cycle.exec_backend import (
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
    ExecCapabilityResolution,
    resolve_verified_exec_capability,
)
from test_case_agent.review_cycle.exec_events import TOOL_EVENT_ITEM_TYPES
from test_case_agent.scope_execution_profile import (
    LEAN_PROFILE,
    STANDARD_PROFILE,
    ScopeExecutionProfile,
    ScopeExecutionProfileError,
    select_scope_execution_profile,
)
from test_case_agent.semantic_design_bridge import (
    load_approved_clarifications,
    normalize_semantic_design_transport,
    semantic_design_allows_canonical_transport_binding,
    semantic_design_minimum_obligation_count,
    semantic_design_output_schema,
    semantic_design_prompt,
    validate_bridge_boundary,
    validate_semantic_input_preflight,
    validate_semantic_design_binding,
)
from scripts.openai_strict_output_schema import (
    validate_openai_strict_output_instance,
)


class ScopeAnalyzerError(ValueError):
    pass


class BackendRuntimeError(RuntimeError):
    pass


class BackendProtocolError(RuntimeError):
    pass


class PromptTransportError(RuntimeError):
    pass


class ResultMissingError(RuntimeError):
    pass


class StreamTransportError(RuntimeError):
    pass


class StreamingExecRuntimeError(RuntimeError):
    pass


class ToolContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class StreamingExecResult:
    return_code: int
    timed_out: bool
    tool_event_count: int
    event_line_count: int
    usage: dict[str, Any]
    process_spawn_ms: int | None = None
    process_spawn_count: int = 0
    process_exit_ms: int | None = None
    thread_started_ms: int | None = None
    thread_started_sequence: int | None = None
    thread_id: str | None = None
    thread_started_count: int = 0
    turn_started_ms: int | None = None
    turn_started_sequence: int | None = None
    turn_started_count: int = 0
    model_result_received_ms: int | None = None
    model_result_sequence: int | None = None
    model_result_count: int = 0
    turn_completed_ms: int | None = None
    turn_completed_sequence: int | None = None
    turn_completed_count: int = 0
    duration_ms: int = 0
    prompt_transport_error: str = ""
    stream_transport_error: str = ""
    stream_complete: bool = True
    cleanup_timed_out: bool = False
    cleanup_timeout_seconds: float | None = None
    runner_error_stage: str = ""
    runner_error_type: str = ""
    runner_error: str = ""
    lifecycle_violations: tuple[str, ...] = ()


def _normalize_entity(value: str) -> str:
    return _canonical_normalize_entity(value)


def _declared_dictionary_values(context: Mapping[str, Any]) -> set[str]:
    return _canonical_declared_dictionary_values(context)


def _dictionary_has_inline_values(name: str, source_texts: Sequence[str]) -> bool:
    return _canonical_dictionary_has_inline_values(name, source_texts)


def analyze_dependency_gaps(context: Mapping[str, Any]) -> dict[str, Any]:
    """Find source dependencies that cannot be bound without inference."""

    if context.get("dependency_gap_gate") is False:
        return {"version": 1, "status": "pass", "gaps": [], "blocking_gap_count": 0}
    rows = [item for item in context.get("source_rows", []) if isinstance(item, Mapping)]
    declared_fields = {
        _normalize_entity(str(item.get("field_or_action", "")))
        for item in rows
        if str(item.get("field_or_action", "")).strip()
    }
    for value in context.get("declared_fields", []):
        if isinstance(value, str) and value.strip():
            declared_fields.add(_normalize_entity(value))
    aliases: dict[str, str] = {}
    raw_aliases = context.get("dependency_aliases")
    if isinstance(raw_aliases, Mapping):
        aliases = {
            _normalize_entity(str(source)): _normalize_entity(str(target))
            for source, target in raw_aliases.items()
        }
    field_references: dict[str, dict[str, Any]] = {}
    dictionary_references: dict[str, dict[str, Any]] = {}
    source_texts = [str(item.get("bounded_source_text", "")) for item in rows]
    declared_dictionary_values = _declared_dictionary_values(context)
    external_dictionary_names = set(
        _canonical_external_dynamic_dictionary_bindings(context)
    )
    for row in rows:
        text = str(row.get("bounded_source_text", ""))
        row_id = str(row.get("source_row_id", "unknown"))
        source_ref = str(row.get("source_ref", row_id))
        # Document-global type-definition rows use generic examples such as
        # `поле "Дата"` and `поле «Дата и время»`.  They constrain
        # declared fields by data type; they are not references to concrete UI
        # entities that must themselves be declared in the selected scope.
        # Other global rows can still carry real cross-field dependencies, so
        # only the explicitly classified `Ограничение типа ...` rows are
        # exempt. Scope-local, ancestor and other global rows remain fail-closed.
        if not _canonical_is_global_type_definition_row(row):
            for match in re.finditer(
                r"\bпол(?:е|я|ем)\s+[«\"]([^»\"]+)[»\"]",
                text,
                flags=re.IGNORECASE,
            ):
                name = match.group(1).strip()
                normalized = _normalize_entity(name)
                if normalized in declared_fields:
                    continue
                alias_target = aliases.get(normalized)
                if alias_target and alias_target in declared_fields:
                    continue
                entry = field_references.setdefault(
                    normalized,
                    {
                        "gap_type": "undeclared-field-reference",
                        "referenced_entity": name,
                        "source_row_ids": [],
                        "source_refs": [],
                        "exact_fragments": [],
                        "blocking": True,
                        "reason": "Referenced field is not declared in the bounded scope and has no approved alias.",
                        "required_resolution": "Add the defining source row or an approved clarification alias.",
                    },
                )
                entry["source_row_ids"].append(row_id)
                entry["source_refs"].append(source_ref)
                entry["exact_fragments"].append(match.group(0))
        for match in re.finditer(
            r"справочник(?:а|у|ом|е)?\s+[«\"]([^»\"]+)[»\"]",
            text,
            flags=re.IGNORECASE,
        ):
            name = match.group(1).strip()
            normalized = _normalize_entity(name)
            if normalized in declared_dictionary_values:
                continue
            if normalized in external_dictionary_names:
                continue
            if _dictionary_has_inline_values(name, source_texts):
                continue
            entry = dictionary_references.setdefault(
                normalized,
                {
                    "gap_type": "missing-dictionary-values",
                    "referenced_entity": name,
                    "source_row_ids": [],
                    "source_refs": [],
                    "exact_fragments": [],
                    "blocking": True,
                    "reason": "A fixed dictionary is referenced but its values are absent from bounded evidence.",
                    "required_resolution": "Add the dictionary values or the authoritative dictionary source.",
                },
            )
            entry["source_row_ids"].append(row_id)
            entry["source_refs"].append(source_ref)
            entry["exact_fragments"].append(match.group(0))
    rows_by_id = {
        str(item.get("source_row_id", "")): item
        for item in rows
    }
    for dependency in _canonical_expected_dependency_inventory(context):
        if dependency.get("kind") != "dictionary":
            continue
        name = str(dependency.get("name", "")).strip()
        normalized = _normalize_entity(name)
        if normalized in declared_dictionary_values:
            continue
        if normalized in external_dictionary_names:
            continue
        if _dictionary_has_inline_values(name, source_texts):
            continue
        entry = dictionary_references.setdefault(
            normalized,
            {
                "gap_type": "missing-dictionary-values",
                "referenced_entity": name,
                "source_row_ids": [],
                "source_refs": [],
                "exact_fragments": [],
                "blocking": True,
                "reason": (
                    "A referenced dictionary is missing its values and authoritative "
                    "dictionary source from bounded evidence."
                ),
                "required_resolution": (
                    "Add the dictionary values or the authoritative dictionary source."
                ),
            },
        )
        for row_id in map(str, dependency.get("source_row_ids", [])):
            row = rows_by_id.get(row_id)
            if row is None:
                continue
            entry["source_row_ids"].append(row_id)
            entry["source_refs"].append(str(row.get("source_ref", row_id)))
        entry["exact_fragments"].extend(
            map(str, dependency.get("exact_source_fragments", []))
        )
    gaps = []
    for index, item in enumerate(
        [*field_references.values(), *dictionary_references.values()], start=1
    ):
        gaps.append(
            {
                "gap_id": f"GAP-PREFLIGHT-{index:03d}",
                **item,
                "source_row_ids": list(dict.fromkeys(item["source_row_ids"])),
                "source_refs": list(dict.fromkeys(item["source_refs"])),
                "exact_fragments": list(dict.fromkeys(item["exact_fragments"])),
            }
        )
    blocking_count = sum(item["blocking"] is True for item in gaps)
    return {
        "version": 1,
        "status": "blocked-input" if blocking_count else "pass",
        "gaps": gaps,
        "blocking_gap_count": blocking_count,
    }


def _expected_dependency_inventory(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    try:
        return _canonical_expected_dependency_inventory(context)
    except BoundedScopeBoundaryError as exc:
        raise ScopeAnalyzerError(str(exc)) from exc


def _validate_source_cache_binding(
    context: Mapping[str, Any],
    *,
    required: bool = False,
) -> None:
    try:
        _canonical_validate_source_cache_binding(context, required=required)
    except BoundedScopeBoundaryError as exc:
        raise ScopeAnalyzerError(str(exc)) from exc


def _validate_scope_context(context: Mapping[str, Any]) -> None:
    try:
        _canonical_validate_scope_context(context, require_source_cache=True)
    except BoundedScopeBoundaryError as exc:
        raise ScopeAnalyzerError(str(exc)) from exc


def _validate_legacy_scope_context(context: Mapping[str, Any]) -> None:
    rows = context.get("source_rows")
    if not isinstance(rows, list) or not rows:
        raise ScopeAnalyzerError("context.source_rows must be a non-empty array")
    row_ids: list[str] = []
    for index, item in enumerate(rows):
        if not isinstance(item, Mapping):
            raise ScopeAnalyzerError(f"context.source_rows[{index}] must be an object")
        row_id = item.get("source_row_id")
        if not isinstance(row_id, str) or not row_id.strip():
            raise ScopeAnalyzerError(
                f"context.source_rows[{index}].source_row_id is required"
            )
        row_ids.append(row_id)
        for key in ("field_or_action", "source_ref", "bounded_source_text"):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ScopeAnalyzerError(f"{row_id}.{key} must be non-empty text")
    if len(row_ids) != len(set(row_ids)):
        raise ScopeAnalyzerError("context source_row_id values must be unique")


def _terminate_process(
    process: subprocess.Popen[str],
    *,
    timeout_seconds: float = 5,
) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(0.1, timeout_seconds),
                check=False,
            )
            if completed.returncode == 0:
                return
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        process.kill()
    except OSError:
        pass


def run_exec_streaming(
    command: Sequence[str],
    *,
    prompt: str,
    cwd: Path,
    events_path: Path,
    stderr_path: Path,
    timeout_seconds: float | None,
    env: Mapping[str, str],
    stage_started_ns: int | None = None,
    cleanup_timeout_seconds: float = 5.0,
) -> StreamingExecResult:
    """Run Codex while flushing stdout/stderr so timeout evidence survives."""

    execution_started = time.perf_counter_ns()
    stage_origin = execution_started if stage_started_ns is None else stage_started_ns

    def elapsed_ms() -> int:
        return (time.perf_counter_ns() - stage_origin) // 1_000_000

    events_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    usage: dict[str, Any] = {}
    tool_event_count = 0
    event_line_count = 0
    process_spawn_ms: int | None = None
    process_spawn_count = 0
    process_exit_ms: int | None = None
    thread_started_ms: int | None = None
    thread_started_sequence: int | None = None
    thread_id: str | None = None
    thread_started_count = 0
    turn_started_ms: int | None = None
    turn_started_sequence: int | None = None
    turn_started_count = 0
    model_result_received_ms: int | None = None
    model_result_sequence: int | None = None
    model_result_count = 0
    turn_completed_ms: int | None = None
    turn_completed_sequence: int | None = None
    turn_completed_count = 0
    prompt_transport_error = ""
    stream_errors: list[str] = []
    runner_error_stage = ""
    runner_error_type = ""
    runner_error = ""
    metrics_lock = threading.Lock()
    process: subprocess.Popen[str] | None = None
    threads: list[threading.Thread] = []
    started_threads: list[threading.Thread] = []
    timed_out = False
    if cleanup_timeout_seconds <= 0:
        raise ValueError("cleanup_timeout_seconds must be positive")
    cleanup_timeout_applied: float | None = None
    cleanup_deadline: float | None = None
    cleanup_timed_out = False
    cleanup_done = False

    def start_bounded_cleanup() -> None:
        nonlocal cleanup_deadline, cleanup_timeout_applied
        if cleanup_deadline is None:
            cleanup_timeout_applied = cleanup_timeout_seconds
            cleanup_deadline = time.monotonic() + cleanup_timeout_seconds

    def cleanup_remaining() -> float:
        if cleanup_deadline is None:
            return cleanup_timeout_seconds
        return max(0.01, cleanup_deadline - time.monotonic())

    def cleanup_spawned_process() -> None:
        nonlocal cleanup_done, cleanup_timed_out, process_exit_ms
        nonlocal prompt_transport_error
        if cleanup_done or process is None:
            return
        cleanup_done = True
        # Cleanup is always bounded, including after a clean process exit.  A
        # broken pipe reader must never extend the user-visible stage forever.
        start_bounded_cleanup()
        try:
            process_running = process.poll() is None
        except Exception as exc:  # pragma: no cover - defensive process boundary
            process_running = True
            with metrics_lock:
                stream_errors.append(f"process-poll:{type(exc).__name__}:{exc}")
        if process_running:
            try:
                _terminate_process(process, timeout_seconds=cleanup_remaining())
            except Exception as exc:  # pragma: no cover - defensive process boundary
                with metrics_lock:
                    stream_errors.append(f"process-terminate:{type(exc).__name__}:{exc}")
                try:
                    process.kill()
                except Exception as kill_exc:
                    with metrics_lock:
                        stream_errors.append(
                            f"process-kill:{type(kill_exc).__name__}:{kill_exc}"
                        )
            try:
                process.wait(timeout=cleanup_remaining())
            except subprocess.TimeoutExpired:
                cleanup_timed_out = True
            except Exception as exc:  # pragma: no cover - defensive process boundary
                with metrics_lock:
                    stream_errors.append(f"cleanup-wait:{type(exc).__name__}:{exc}")
        if getattr(process, "returncode", None) is not None:
            process_exit_ms = elapsed_ms()
        try:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
        except (OSError, ValueError) as exc:
            if not prompt_transport_error:
                prompt_transport_error = f"{type(exc).__name__}: {exc}"
        for thread in started_threads:
            thread.join(timeout=max(0.0, cleanup_deadline - time.monotonic()))
        live_threads = [thread for thread in started_threads if thread.is_alive()]
        if live_threads:
            cleanup_timed_out = True
            with metrics_lock:
                stream_errors.append("cleanup:drain-thread-deadline-exceeded")
            return
        for stream_name, stream in (
            ("stdout", process.stdout),
            ("stderr", process.stderr),
        ):
            try:
                stream.close()
            except (OSError, ValueError) as exc:
                with metrics_lock:
                    stream_errors.append(
                        f"{stream_name}-close:{type(exc).__name__}:{exc}"
                    )
    events_handle = events_path.open("w", encoding="utf-8", newline="\n")
    try:
        stderr_handle = stderr_path.open("w", encoding="utf-8", newline="\n")
    except Exception:
        events_handle.close()
        raise
    try:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=dict(env),
        )
        process_spawn_ms = elapsed_ms()
        process_spawn_count = 1
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None

        def drain_stdout() -> None:
            nonlocal usage, tool_event_count, event_line_count
            nonlocal thread_started_ms, thread_started_sequence
            nonlocal thread_id, thread_started_count
            nonlocal turn_started_ms, turn_started_sequence, turn_started_count
            nonlocal model_result_received_ms, model_result_sequence
            nonlocal model_result_count
            nonlocal turn_completed_ms, turn_completed_sequence
            nonlocal turn_completed_count
            try:
                for line in process.stdout:
                    observed_ms = elapsed_ms()
                    events_handle.write(line)
                    events_handle.flush()
                    with metrics_lock:
                        event_line_count += 1
                        observed_sequence = event_line_count
                        found_tools, found_usage = _parse_events(line)
                        tool_event_count += found_tools
                        if found_usage:
                            usage = found_usage
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(event, Mapping):
                            continue
                        event_type = event.get("type")
                        if event_type == "thread.started":
                            thread_started_count += 1
                            if thread_started_ms is None:
                                thread_started_ms = observed_ms
                                thread_started_sequence = observed_sequence
                                value = event.get("thread_id")
                                thread_id = value if isinstance(value, str) else None
                        elif event_type == "turn.started":
                            turn_started_count += 1
                            if turn_started_ms is None:
                                turn_started_ms = observed_ms
                                turn_started_sequence = observed_sequence
                        elif event_type == "item.completed":
                            item = event.get("item")
                            if isinstance(item, Mapping) and item.get("type") == "agent_message":
                                model_result_count += 1
                                if model_result_received_ms is None:
                                    model_result_received_ms = observed_ms
                                    model_result_sequence = observed_sequence
                        elif event_type == "turn.completed":
                            turn_completed_count += 1
                            if turn_completed_ms is None:
                                turn_completed_ms = observed_ms
                                turn_completed_sequence = observed_sequence
            except Exception as exc:  # pragma: no cover - platform pipe failures
                with metrics_lock:
                    stream_errors.append(f"stdout:{type(exc).__name__}:{exc}")

        def drain_stderr() -> None:
            try:
                for line in process.stderr:
                    stderr_handle.write(line)
                    stderr_handle.flush()
            except Exception as exc:  # pragma: no cover - platform pipe failures
                with metrics_lock:
                    stream_errors.append(f"stderr:{type(exc).__name__}:{exc}")

        threads = [
            threading.Thread(target=drain_stdout, daemon=True),
            threading.Thread(target=drain_stderr, daemon=True),
        ]
        for thread in threads:
            thread.start()
            started_threads.append(thread)

        try:
            try:
                process.stdin.write(prompt)
                process.stdin.close()
            except (OSError, ValueError) as exc:
                prompt_transport_error = f"{type(exc).__name__}: {exc}"
            if prompt_transport_error:
                start_bounded_cleanup()
            elif timeout_seconds is None:
                process.wait()
            else:
                process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            start_bounded_cleanup()
        except Exception as exc:  # pragma: no cover - defensive process API boundary
            runner_error_stage = "process-wait"
            runner_error_type = type(exc).__name__
            runner_error = str(exc)
            start_bounded_cleanup()
        finally:
            cleanup_spawned_process()
    except Exception as exc:
        if process is None:
            raise
        runner_error_stage = "post-spawn-setup"
        runner_error_type = type(exc).__name__
        runner_error = str(exc)
        cleanup_spawned_process()
    finally:
        for handle_name, handle in (
            ("events-output", events_handle),
            ("stderr-output", stderr_handle),
        ):
            try:
                handle.close()
            except (OSError, ValueError) as exc:
                with metrics_lock:
                    stream_errors.append(
                        f"{handle_name}-close:{type(exc).__name__}:{exc}"
                    )

    lifecycle_violations: list[str] = []
    milestones = (
        ("thread.started", thread_started_sequence),
        ("turn.started", turn_started_sequence),
        ("model-result", model_result_sequence),
        ("turn.completed", turn_completed_sequence),
    )
    previous_name: str | None = None
    previous_sequence: int | None = None
    for name, observed_sequence in milestones:
        if observed_sequence is None:
            continue
        if previous_sequence is not None and observed_sequence < previous_sequence:
            lifecycle_violations.append(
                f"{name}-before-{previous_name}"
            )
        previous_name = name
        previous_sequence = observed_sequence
    if turn_started_ms is not None and thread_started_ms is None:
        lifecycle_violations.append("turn-started-without-thread-started")
    if model_result_received_ms is not None and turn_started_ms is None:
        lifecycle_violations.append("model-result-without-turn-started")
    if turn_completed_ms is not None and turn_started_ms is None:
        lifecycle_violations.append("turn-completed-without-turn-started")

    stream_complete = (
        all(not thread.is_alive() for thread in threads)
        and not stream_errors
        and getattr(process, "returncode", None) is not None
    )
    return StreamingExecResult(
        return_code=process.returncode if process.returncode is not None else -1,
        timed_out=timed_out,
        tool_event_count=tool_event_count,
        event_line_count=event_line_count,
        usage=dict(usage),
        process_spawn_ms=process_spawn_ms,
        process_spawn_count=process_spawn_count,
        process_exit_ms=process_exit_ms,
        thread_started_ms=thread_started_ms,
        thread_started_sequence=thread_started_sequence,
        thread_id=thread_id,
        thread_started_count=thread_started_count,
        turn_started_ms=turn_started_ms,
        turn_started_sequence=turn_started_sequence,
        turn_started_count=turn_started_count,
        model_result_received_ms=model_result_received_ms,
        model_result_sequence=model_result_sequence,
        model_result_count=model_result_count,
        turn_completed_ms=turn_completed_ms,
        turn_completed_sequence=turn_completed_sequence,
        turn_completed_count=turn_completed_count,
        duration_ms=(time.perf_counter_ns() - execution_started) // 1_000_000,
        prompt_transport_error=prompt_transport_error,
        stream_transport_error="; ".join(stream_errors),
        stream_complete=stream_complete,
        cleanup_timed_out=cleanup_timed_out,
        cleanup_timeout_seconds=cleanup_timeout_applied,
        runner_error_stage=runner_error_stage,
        runner_error_type=runner_error_type,
        runner_error=runner_error,
        lifecycle_violations=tuple(lifecycle_violations),
    )


def _publish_terminal_receipt(
    path: Path | None,
    *,
    stage: str,
    return_code: int,
    error_type: str,
    error: str,
) -> str | None:
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        write_stage_failure_exclusive(
            path,
            StageFailureEnvelope.create(
                stage=stage,
                return_code=return_code,
                error_type=error_type,
                error=error,
                source="scripts/codex_exec_bounded_scope_analyzer.py",
            ),
        )
    except StageFailureWriteError as exc:
        return str(exc)
    return None


def _array(items: Mapping[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": dict(items)}


def _string_array() -> dict[str, Any]:
    return _array({"type": "string"})


def legacy_detailed_output_schema(source_row_ids: Sequence[str]) -> dict[str, Any]:
    binding = {
        "type": "object",
        "additionalProperties": False,
        "required": ["requirement_code", "source_row_id", "exact_source_fragment"],
        "properties": {
            "requirement_code": {"type": "string"},
            "source_row_id": {"type": "string", "enum": list(source_row_ids)},
            "exact_source_fragment": {"type": "string"},
        },
    }
    clause_binding = {
        "type": "object",
        "additionalProperties": False,
        "required": ["clause_kind", "clause_index", "source_row_id", "exact_source_fragment"],
        "properties": {
            "clause_kind": {"type": "string", "enum": ["condition", "action", "oracle"]},
            "clause_index": {"type": "integer"},
            "source_row_id": {"type": "string", "enum": list(source_row_ids)},
            "exact_source_fragment": {"type": "string"},
        },
    }
    assertion = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "assertion_id",
            "canonical_statement",
            "polarity",
            "semantic_disposition",
            "execution_readiness",
            "execution_readiness_rationale",
            "risk",
            "condition_clauses",
            "action_clauses",
            "oracle_clauses",
            "requirement_codes",
            "requirement_code_evidence",
            "clause_evidence",
            "atom_id",
            "obligation_ids",
            "disposition_rationale",
            "source_property_id",
            "field_or_block",
            "source_reference",
        ],
        "properties": {
            "assertion_id": {"type": "string"},
            "canonical_statement": {"type": "string"},
            "polarity": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            "semantic_disposition": {"type": "string", "enum": ["testable", "not-applicable"]},
            "execution_readiness": {"type": "string", "enum": ["ready", "not-applicable"]},
            "execution_readiness_rationale": {"type": "string"},
            "risk": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "condition_clauses": _string_array(),
            "action_clauses": _string_array(),
            "oracle_clauses": _string_array(),
            "requirement_codes": _string_array(),
            "requirement_code_evidence": _array(binding),
            "clause_evidence": _array(clause_binding),
            "atom_id": {"type": "string"},
            "obligation_ids": _string_array(),
            "disposition_rationale": {"type": "string"},
            "source_property_id": {"type": "string"},
            "field_or_block": {"type": "string"},
            "source_reference": {"type": "string"},
        },
    }
    source_decision = {
        "type": "object",
        "additionalProperties": False,
        "required": ["source_row_id", "scope_disposition", "requirement_codes", "assertions"],
        "properties": {
            "source_row_id": {"type": "string", "enum": list(source_row_ids)},
            "scope_disposition": {"type": "string", "enum": ["yes", "no"]},
            "requirement_codes": _string_array(),
            "assertions": _array(assertion),
        },
    }
    obligation = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "obligation_id",
            "linked_atom_id",
            "source_property_id",
            "property_type",
            "obligation_class",
            "required_behavior",
            "source_ref",
            "planned_tc_id",
            "review_notes",
            "design_dimension",
            "planned_check",
            "check_type",
            "coverage_class",
            "input_class",
            "single_expected_behavior",
            "oracle_source",
        ],
        "properties": {
            "obligation_id": {"type": "string"},
            "linked_atom_id": {"type": "string"},
            "source_property_id": {"type": "string"},
            "property_type": {"type": "string"},
            "obligation_class": {"type": "string"},
            "required_behavior": {"type": "string"},
            "source_ref": {"type": "string"},
            "planned_tc_id": {"type": "string"},
            "review_notes": {"type": "string"},
            "design_dimension": {"type": "string"},
            "planned_check": {"type": "string"},
            "check_type": {"type": "string"},
            "coverage_class": {"type": "string"},
            "input_class": {"type": "string"},
            "single_expected_behavior": {"type": "string"},
            "oracle_source": {"type": "string"},
        },
    }
    applicability = {
        "type": "object",
        "additionalProperties": False,
        "required": ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases"],
        "properties": {
            "dimension": {"type": "string"},
            "applicable": {"type": "string", "enum": ["yes", "no"]},
            "source_ref": {"type": "string"},
            "reason": {"type": "string"},
            "linked_atoms": _string_array(),
            "linked_test_cases": _string_array(),
        },
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "version",
            "status",
            "blocking_reason",
            "scope_summary",
            "included",
            "excluded",
            "mockup_locators",
            "source_decisions",
            "obligations",
            "applicability",
        ],
        "properties": {
            "version": {"type": "integer", "enum": [1]},
            "status": {"type": "string", "enum": ["ready", "blocked"]},
            "blocking_reason": {"type": "string"},
            "scope_summary": {"type": "string"},
            "included": _string_array(),
            "excluded": _string_array(),
            "mockup_locators": _string_array(),
            "source_decisions": _array(source_decision),
            "obligations": _array(obligation),
            "applicability": _array(applicability),
        },
    }


def _legacy_detailed_prompt(context: Mapping[str, Any]) -> str:
    return """You are the bounded FT scope semantic analyzer. Work only from the inline JSON and attached images.
Do not call tools, shell, web, MCP, or read any workspace files. Return only JSON matching the supplied schema.

Quality contract:
- DOCX statements in bounded evidence are semantic source of truth; XHTML rows provide exact text and locators; PDF is parity only; mockups only refine visible action locators.
- Account for every source_row_id exactly once. Context/global/header rows are explicit not-applicable assertions, never silently dropped.
- A testable assertion must contain one condition/action/oracle chain and exact evidence fragments copied from the declared bounded source rows. Do not invent behavior.
- Keep independent behavior atomic. Every testable assertion has one ATOM and at least one OBL; every OBL is represented once in obligations.
- This v1 fast path supports no coverage gaps. If source ambiguity prevents a deterministic executable obligation, return status=blocked and a substantive blocking_reason.
- For ready status, blocking_reason is exactly none_required. For not-applicable assertions use execution_readiness=not-applicable, execution_readiness_rationale=none_required, no obligations, and a substantive disposition_rationale.
- For testable assertions use execution_readiness=ready, execution_readiness_rationale=none_required, disposition_rationale=none_required.
- requirement_code_evidence and clause_evidence fragments must be literal substrings of the referenced row text.
- When a source row declares expected_assertion_ids/expected_atom_ids, use those exact identifiers. When id_policy declares obligations and planned test cases, preserve them exactly.
- Produce applicability rows for exactly these dimensions: conditional-visibility, scenario-use-case, traceability, accessibility-ui, role-permission, status-lifecycle, equivalence, boundary, table-list, integration, async, persistence, security.
- Mark a dimension yes only when the bounded source defines a concrete check for it. A visible UI control alone is not accessibility-ui evidence; accessibility-ui requires an explicit accessibility property or criterion. An empty/default initial state alone is not a boundary class; boundary requires a source-defined limit, edge, partition, or distinct empty-versus-nonempty input class. Never mark a dimension yes while the reason says that its requirements are absent.
- Every yes row must link at least one known testable ATOM and planned TC. Every no row must have empty linked_atoms and linked_test_cases. scenario-use-case and traceability normally apply to an executable coded UI action; other dimensions need their own explicit source-backed property.

Inline bounded context:
""" + json.dumps(context, ensure_ascii=False, indent=2)


def _parse_events(raw: str) -> tuple[int, dict[str, Any]]:
    tool_events = 0
    usage: dict[str, Any] = {}
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item")
        if isinstance(item, Mapping) and item.get("type") in TOOL_EVENT_ITEM_TYPES:
            tool_events += 1
        candidate = event.get("usage")
        if isinstance(candidate, Mapping):
            usage = dict(candidate)
    return tool_events, usage


def _validate_legacy_detailed_decision(payload: Mapping[str, Any], context: Mapping[str, Any]) -> None:
    expected_rows = [str(item["source_row_id"]) for item in context["source_rows"]]
    decisions = payload.get("source_decisions")
    if not isinstance(decisions, list):
        raise ScopeAnalyzerError("source_decisions must be an array")
    actual_rows = [item.get("source_row_id") for item in decisions if isinstance(item, Mapping)]
    if len(actual_rows) != len(set(actual_rows)) or set(actual_rows) != set(expected_rows):
        raise ScopeAnalyzerError("source_decisions must account for every source row exactly once")
    assertions = [
        assertion
        for item in decisions
        if isinstance(item, Mapping)
        for assertion in item.get("assertions", [])
        if isinstance(assertion, Mapping)
    ]
    assertion_ids = [item.get("assertion_id") for item in assertions]
    atom_ids = [item.get("atom_id") for item in assertions]
    if len(assertion_ids) != len(set(assertion_ids)) or len(atom_ids) != len(set(atom_ids)):
        raise ScopeAnalyzerError("assertion_id and atom_id values must be unique")
    for assertion in assertions:
        if assertion.get("execution_readiness") != "dependency-blocked" and (
            assertion.get("execution_readiness_rationale") != "none_required"
        ):
            raise ScopeAnalyzerError(
                "ready/not-applicable execution_readiness_rationale must equal none_required"
            )
    decisions_by_row = {
        str(item.get("source_row_id")): item
        for item in decisions
        if isinstance(item, Mapping)
    }
    for source_row in context["source_rows"]:
        source_row_id = str(source_row["source_row_id"])
        row_assertions = decisions_by_row[source_row_id].get("assertions", [])
        if not isinstance(row_assertions, list) or not row_assertions:
            raise ScopeAnalyzerError(f"{source_row_id} requires at least one assertion")
        for key, assertion_key in (
            ("expected_assertion_ids", "assertion_id"),
            ("expected_atom_ids", "atom_id"),
        ):
            expected_ids = source_row.get(key)
            if expected_ids is None:
                continue
            actual_ids = [
                item.get(assertion_key)
                for item in row_assertions
                if isinstance(item, Mapping)
            ]
            if actual_ids != expected_ids:
                raise ScopeAnalyzerError(
                    f"{source_row_id} {assertion_key} values must match {key} exactly"
                )
    expected_obligations = {
        obligation_id
        for item in assertions
        if item.get("semantic_disposition") == "testable"
        for obligation_id in item.get("obligation_ids", [])
    }
    obligations = payload.get("obligations")
    actual_obligations = {
        item.get("obligation_id")
        for item in obligations
        if isinstance(item, Mapping)
    } if isinstance(obligations, list) else set()
    if expected_obligations != actual_obligations:
        raise ScopeAnalyzerError("testable assertion obligations do not match design obligations")
    id_policy = context.get("id_policy")
    if isinstance(id_policy, Mapping):
        expected_obligation_ids = set(id_policy.get("obligation_ids", []))
        if expected_obligation_ids and actual_obligations != expected_obligation_ids:
            raise ScopeAnalyzerError("obligation ids must match context.id_policy")
        expected_tc_ids = set(id_policy.get("planned_tc_ids", []))
        actual_tc_ids = {
            item.get("planned_tc_id")
            for item in obligations
            if isinstance(item, Mapping)
        } if isinstance(obligations, list) else set()
        if expected_tc_ids and actual_tc_ids != expected_tc_ids:
            raise ScopeAnalyzerError("planned test case ids must match context.id_policy")
    applicability = payload.get("applicability", [])
    rows = [item for item in applicability if isinstance(item, Mapping)]
    dimensions = [item.get("dimension") for item in rows]
    expected_dimensions = {
        "conditional-visibility", "scenario-use-case", "traceability", "accessibility-ui",
        "role-permission", "status-lifecycle", "equivalence", "boundary", "table-list",
        "integration", "async", "persistence", "security",
    }
    if len(dimensions) != len(expected_dimensions) or set(dimensions) != expected_dimensions:
        raise ScopeAnalyzerError("applicability must contain the exact 13-dimension set")
    known_atoms = {
        str(item.get("atom_id"))
        for item in assertions
        if item.get("semantic_disposition") == "testable"
    }
    known_test_cases = {
        str(item.get("planned_tc_id"))
        for item in obligations
        if isinstance(item, Mapping) and item.get("planned_tc_id")
    } if isinstance(obligations, list) else set()
    obligation_dimensions = {
        re.sub(r"[^a-z0-9]+", "-", str(item.get("design_dimension", "")).lower()).strip("-")
        for item in obligations
        if isinstance(item, Mapping)
    } if isinstance(obligations, list) else set()
    obligation_property_types = {
        re.sub(r"[^a-z0-9]+", "-", str(item.get("property_type", "")).lower()).strip("-")
        for item in obligations
        if isinstance(item, Mapping)
    } if isinstance(obligations, list) else set()
    for item in rows:
        dimension = str(item.get("dimension"))
        applicable = item.get("applicable")
        linked_atoms = item.get("linked_atoms")
        linked_test_cases = item.get("linked_test_cases")
        if not isinstance(linked_atoms, list) or not isinstance(linked_test_cases, list):
            raise ScopeAnalyzerError(f"{dimension} applicability links must be arrays")
        if applicable == "yes":
            if not linked_atoms or not linked_test_cases:
                raise ScopeAnalyzerError(
                    f"applicable dimension {dimension} requires linked ATOM and TC ids"
                )
            if set(map(str, linked_atoms)) - known_atoms:
                raise ScopeAnalyzerError(f"{dimension} links unknown or non-testable ATOM ids")
            if set(map(str, linked_test_cases)) - known_test_cases:
                raise ScopeAnalyzerError(f"{dimension} links unknown planned TC ids")
            if dimension == "accessibility-ui" and not any(
                "accessib" in value
                for value in obligation_dimensions | obligation_property_types
            ):
                raise ScopeAnalyzerError(
                    "accessibility-ui requires an explicit accessibility obligation"
                )
            if dimension == "boundary" and not any(
                marker in value
                for value in obligation_dimensions | obligation_property_types
                for marker in (
                    "boundary", "equivalence", "numeric", "length", "range",
                    "minimum", "maximum", "format-mask", "date-time",
                )
            ):
                raise ScopeAnalyzerError(
                    "boundary requires an explicit boundary/equivalence obligation"
                )
        elif applicable == "no":
            if linked_atoms or linked_test_cases:
                raise ScopeAnalyzerError(
                    f"non-applicable dimension {dimension} must not link ATOM or TC ids"
                )
        else:
            raise ScopeAnalyzerError(f"{dimension} applicability must be yes or no")


def output_schema(source_row_ids: Sequence[str]) -> dict[str, Any]:
    row_id = {"type": "string", "enum": list(source_row_ids)}
    source_decision = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "source_row_id",
            "disposition",
            "requirement_codes",
            "rationale",
        ],
        "properties": {
            "source_row_id": row_id,
            "disposition": {
                "type": "string",
                "enum": ["included", "context", "excluded"],
            },
            "requirement_codes": _string_array(),
            "rationale": {"type": "string"},
        },
    }
    dependency = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "dependency_id",
            "kind",
            "name",
            "source_row_ids",
            "resolution",
            "target_source_row_ids",
            "exact_source_fragments",
            "gap_ids",
            "blocking",
            "rationale",
        ],
        "properties": {
            "dependency_id": {"type": "string"},
            "kind": {
                "type": "string",
                "enum": [
                    "field",
                    "dictionary",
                    "external-requirement",
                    "integration",
                    "other",
                ],
            },
            "name": {"type": "string"},
            "source_row_ids": _array(row_id),
            "resolution": {
                "type": "string",
                "enum": [
                    "declared",
                    "approved-alias",
                    "source-provided",
                    "external-dynamic",
                    "scope-excluded",
                    "missing",
                ],
            },
            "target_source_row_ids": _array(row_id),
            "exact_source_fragments": _string_array(),
            "gap_ids": _string_array(),
            "blocking": {"type": "boolean"},
            "rationale": {"type": "string"},
        },
    }
    gap = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "gap_id",
            "gap_type",
            "source_row_ids",
            "source_refs",
            "exact_source_fragments",
            "blocking",
            "clarification_question",
            "downstream_handling",
        ],
        "properties": {
            "gap_id": {"type": "string"},
            "gap_type": {"type": "string", "enum": list(CANONICAL_GAP_TYPES)},
            "source_row_ids": _array(row_id),
            "source_refs": _string_array(),
            "exact_source_fragments": _string_array(),
            "blocking": {"type": "boolean"},
            "clarification_question": {"type": "string"},
            "downstream_handling": {
                "type": "string",
                "enum": ["block-writer", "carry-to-source-model", "none-required"],
            },
        },
    }
    scope_boundary = {
        "type": "object",
        "additionalProperties": False,
        "required": ["target", "include", "exclude"],
        "properties": {
            "target": {"type": "string"},
            "include": _string_array(),
            "exclude": _string_array(),
        },
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "version",
            "status",
            "blocking_reason",
            "scope_summary",
            "scope_boundary",
            "source_decisions",
            "dependencies",
            "gaps",
            "mockup_locators",
        ],
        "properties": {
            "version": {"type": "integer", "enum": [2]},
            "status": {"type": "string", "enum": ["ready", "blocked"]},
            "blocking_reason": {"type": "string"},
            "scope_summary": {"type": "string"},
            "scope_boundary": scope_boundary,
            "source_decisions": _array(source_decision),
            "dependencies": _array(dependency),
            "gaps": _array(gap),
            "mockup_locators": _string_array(),
        },
    }


def _scope_projection(context: Mapping[str, Any]) -> dict[str, Any]:
    projection: dict[str, Any] = {}
    for key in (
        "version",
        "ft_slug",
        "scope_slug",
        "section_id",
        "package_id",
        "request_summary",
        "scope_boundary",
        "sources",
        "mockups",
        "mockup_locators",
        "parity",
        "bounded_evidence_inline",
        "dependency_aliases",
        "dictionary_inventory",
        "external_dictionary_bindings",
    ):
        if key in context:
            projection[key] = context[key]
    rows = []
    for item in context.get("source_rows", []):
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                key: item[key]
                for key in (
                    "source_row_id",
                    "field_or_action",
                    "source_ref",
                    "source_path",
                    "source_locator",
                    "bounded_source_text",
                    "context_relation_required",
                    "source_context_class",
                    "requirement_codes_hint",
                    "in_scope_hint",
                )
                if key in item
            }
        )
    projection["source_rows"] = rows
    projection["expected_dependency_inventory"] = _expected_dependency_inventory(context)
    source_cache = context.get("source_cache")
    if isinstance(source_cache, Mapping) and isinstance(
        source_cache.get("component_digests"), Mapping
    ):
        projection["source_evidence_digests"] = source_cache["component_digests"]
    return projection


def _prompt(context: Mapping[str, Any]) -> str:
    return """You are the bounded FT scope analyzer. Work only from the inline JSON and attached images.
Do not call tools, shell, web, MCP, or read workspace files. Return only JSON matching the schema.

This is a scope-only decision. Do not create assertions, ATOM/OBL identifiers, test cases,
test-design obligations, applicability matrices, or writer instructions.

Contract:
- DOCX inline evidence is semantic source of truth; XHTML rows provide exact extraction text
  and locators; PDF is structural/code parity only; mockups refine visible locators only.
- Preserve scope_boundary exactly and account for every source_row_id exactly once, in input
  order, as included, context, or excluded.
- in_scope_hint is the authoritative pre-fixed membership: yes means included; no means either
  context or excluded. Ambiguous membership must be resolved before this experimental call.
- A row with context_relation_required=true must be context and its exact expected dependency
  relation must be preserved; it cannot be excluded or treated as an executable owner row.
- Copy requirement_codes_hint exactly. These codes are already bound to XHTML text or the
  authenticated DOCX/PDF parity evidence by deterministic source preparation.
- Account for every item in expected_dependency_inventory exactly once and add no other
  dependencies. Never infer an alias from similar names or values.
- source_row_ids are the inventory rows containing the literal reference. target_source_row_ids
  are the rows that define or bind the referenced entity.
- If an inventory item supplies resolution and target_source_row_ids, copy both exactly.
- declared requires every target row's normalized field_or_action to equal the dependency name.
  approved-alias requires an exact dependency_aliases mapping to every target row's
  field_or_action. scope-excluded requires no targets and the normalized dependency name to
  occur in a scope_boundary.exclude entry.
  source-provided is for a source-defined dictionary or a non-field dependency with bound
  source targets; it is never valid for kind=field. external-dynamic is only for a dictionary
  whose exact HTTPS/query contract and user-confirmed authority are supplied in
  external_dictionary_bindings; it never uses source-row targets as a substitute for values.
  missing requires a blocking gap. Do not use another resolution to bypass these bindings.
- Bind every dependency to literal source fragments. A dependency explicitly delegated to an
  excluded external FT may use scope-excluded only when the current observable result remains
  self-contained. A missing dependency must link a blocking gap.
- If an included row's only required system effect is an internal model, persistence or
  integration-field update and the registered sources provide no authorized observation
  interface, keep the row included and keep its source-defined dependency resolution. Add one
  non-blocking missing-observation-interface gap with carry-to-source-model handling and literal
  evidence for the complete unobservable effect, and link that gap from each resolved dependency
  whose source effect it constrains. Do not invent an API, database query, model
  inspector or generic artifact. Use this gap only for a whole unobservable effect; visible
  behavior in the same row remains included and independently testable.
- Gap evidence fragments must be literal substrings of the linked source rows.
- ready requires no blocking gap or missing blocking dependency and blocking_reason=none_required.
- blocked requires a substantive blocking_reason. Partial source analysis never authorizes writer.
- Mockups refine only visible locators; they do not create business rules. Return only locators
  explicitly declared in mockup_locators.

Inline bounded context:
""" + json.dumps(_scope_projection(context), ensure_ascii=False, indent=2)


def _validate_decision(payload: Mapping[str, Any], context: Mapping[str, Any]) -> None:
    """Compatibility wrapper around the canonical boundary-v2 validator."""

    try:
        _canonical_validate_decision(context, payload)
    except BoundedScopeBoundaryError as exc:
        raise ScopeAnalyzerError(str(exc)) from exc

def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_empty(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _event_state(observed_ms: int | None, execution: StreamingExecResult | None) -> str:
    if observed_ms is not None:
        return "observed"
    if execution is None or execution.stream_complete:
        return "not-observed"
    return "unknown"


def _model_invocation_state(
    execution: StreamingExecResult | None,
    *,
    runner_attempt_count: int,
    result_parsed: bool = False,
) -> str:
    if result_parsed or (
        execution is not None
        and (
            execution.turn_started_count
            or execution.model_result_count
            or execution.turn_completed_count
        )
    ):
        return "yes"
    if runner_attempt_count == 0 or execution is None or execution.stream_complete:
        return "no"
    return "unknown"


def _lifecycle_payload(
    execution: StreamingExecResult | None,
    *,
    runner_attempt_count: int,
    result_parsed: bool = False,
    result_parsed_ms: int | None = None,
    result_validated: bool = False,
) -> dict[str, Any]:
    model_state = _model_invocation_state(
        execution,
        runner_attempt_count=runner_attempt_count,
        result_parsed=result_parsed,
    )
    event_result_observed = bool(
        execution and execution.model_result_received_ms is not None
    )
    result_state = (
        "observed"
        if event_result_observed or result_parsed
        else _event_state(None, execution)
    )
    process_state = (
        "observed"
        if execution is not None and execution.process_spawn_count
        else ("not-observed" if runner_attempt_count else "not-attempted")
    )
    model_observed_ms: int | None = result_parsed_ms
    model_evidence: str | None = (
        "decision-output-file-after-exit" if result_parsed else None
    )
    if execution is not None:
        for observed_ms, evidence in (
            (execution.turn_started_ms, "turn.started"),
            (execution.model_result_received_ms, "item.completed:agent_message"),
            (execution.turn_completed_ms, "turn.completed"),
        ):
            if observed_ms is not None:
                model_observed_ms = observed_ms
                model_evidence = evidence
                break
    process_spawn_count = execution.process_spawn_count if execution is not None else 0
    return {
        "contract_version": 1,
        "runner_attempt_count": runner_attempt_count,
        "runner_retry_count": max(0, runner_attempt_count - 1),
        "process_spawn_count": process_spawn_count,
        "process_spawned": {
            "state": process_state,
            "observed_after_stage_start_ms": (
                execution.process_spawn_ms if execution is not None else None
            ),
            "evidence": (
                "subprocess-popen-returned"
                if execution is not None and execution.process_spawn_count > 0
                else None
            ),
        },
        "process_exited": {
            "state": _event_state(
                execution.process_exit_ms if execution is not None else None,
                execution,
            ),
            "observed_after_stage_start_ms": (
                execution.process_exit_ms if execution is not None else None
            ),
            "evidence": (
                "subprocess-returncode-observed"
                if execution is not None and execution.process_exit_ms is not None
                else None
            ),
        },
        "thread_started": {
            "state": _event_state(
                execution.thread_started_ms if execution is not None else None,
                execution,
            ),
            "observed_after_stage_start_ms": (
                execution.thread_started_ms if execution is not None else None
            ),
            "observed_sequence": (
                execution.thread_started_sequence if execution is not None else None
            ),
            "count": execution.thread_started_count if execution is not None else 0,
            "thread_id": execution.thread_id if execution is not None else None,
            "evidence": "thread.started" if execution and execution.thread_started_ms is not None else None,
        },
        "turn_started": {
            "state": _event_state(
                execution.turn_started_ms if execution is not None else None,
                execution,
            ),
            "observed_after_stage_start_ms": (
                execution.turn_started_ms if execution is not None else None
            ),
            "observed_sequence": (
                execution.turn_started_sequence if execution is not None else None
            ),
            "count": execution.turn_started_count if execution is not None else 0,
            "evidence": "turn.started" if execution and execution.turn_started_ms is not None else None,
        },
        "model_invoked": {
            "state": model_state,
            "observed_after_stage_start_ms": (
                model_observed_ms
                if model_state == "yes"
                else None
            ),
            "evidence": model_evidence if model_state == "yes" else None,
        },
        "model_result_received": {
            "state": result_state,
            "observed_after_stage_start_ms": (
                execution.model_result_received_ms
                if event_result_observed and execution is not None
                else result_parsed_ms
            ),
            "observed_sequence": (
                execution.model_result_sequence
                if event_result_observed and execution is not None
                else None
            ),
            "count": execution.model_result_count if execution is not None else 0,
            "evidence": (
                "item.completed:agent_message"
                if event_result_observed
                else ("decision-output-file-after-exit" if result_parsed else None)
            ),
        },
        "turn_completed": {
            "state": _event_state(
                execution.turn_completed_ms if execution is not None else None,
                execution,
            ),
            "observed_after_stage_start_ms": (
                execution.turn_completed_ms if execution is not None else None
            ),
            "observed_sequence": (
                execution.turn_completed_sequence if execution is not None else None
            ),
            "count": execution.turn_completed_count if execution is not None else 0,
            "evidence": (
                "turn.completed"
                if execution and execution.turn_completed_ms is not None
                else None
            ),
        },
        "stream_complete": execution.stream_complete if execution is not None else None,
        "cleanup": {
            "timed_out": execution.cleanup_timed_out if execution is not None else False,
            "timeout_seconds": (
                execution.cleanup_timeout_seconds if execution is not None else None
            ),
            "secondary_stream_error": (
                execution.stream_transport_error if execution is not None else ""
            ),
        },
        "runner_error": {
            "stage": execution.runner_error_stage if execution is not None else "",
            "type": execution.runner_error_type if execution is not None else "",
            "message": execution.runner_error if execution is not None else "",
        },
        "lifecycle_violations": (
            list(execution.lifecycle_violations) if execution is not None else []
        ),
        "backend_reentry_observed": bool(
            execution
            and (
                execution.thread_started_count > 1
                or execution.turn_started_count > 1
                or execution.model_result_count > 1
                or execution.turn_completed_count > 1
            )
        ),
        "result_parsed": result_parsed,
        "result_validated": result_validated,
    }


def _model_invoked_projection(lifecycle: Mapping[str, Any]) -> bool | None:
    state = lifecycle["model_invoked"]["state"]
    if state == "yes":
        return True
    if state == "no":
        return False
    return None


def _backend_protocol_errors(
    execution: StreamingExecResult,
) -> tuple[str, ...]:
    event_counts = {
        "thread.started": execution.thread_started_count,
        "turn.started": execution.turn_started_count,
        "model-result": execution.model_result_count,
        "turn.completed": execution.turn_completed_count,
    }
    return (
        *(
            f"duplicate {name}={count}"
            for name, count in event_counts.items()
            if count > 1
        ),
        *execution.lifecycle_violations,
    )


def _resolution_payload(resolution: ExecCapabilityResolution) -> dict[str, Any]:
    return {
        "verified": resolution.verified,
        "selected_executable": resolution.selected_executable or None,
        "selected_version": (
            resolution.selected.version if resolution.selected is not None else None
        ),
        "total_duration_ms": resolution.total_duration_ms,
        "disable_features": list(resolution.disable_features),
        "probes": [asdict(item) for item in resolution.probes],
    }


def _error_category(
    exc: BaseException,
    *,
    error_stage: str,
    execution: StreamingExecResult | None,
) -> str:
    if isinstance(exc, BackendRuntimeError):
        return "backend-bootstrap"
    if isinstance(exc, PromptTransportError):
        return "prompt-transport"
    if isinstance(exc, StreamTransportError):
        return "stream-transport"
    if isinstance(exc, StreamingExecRuntimeError):
        return "process-runtime"
    if isinstance(exc, BackendProtocolError):
        return "backend-protocol"
    if isinstance(exc, ToolContractError):
        return "tool-contract"
    if isinstance(exc, ResultMissingError):
        return "result-missing"
    if isinstance(exc, subprocess.TimeoutExpired) or isinstance(exc, TimeoutError):
        if execution is not None and (
            execution.model_result_count or execution.turn_completed_count
        ):
            return "post-result-process-exit-timeout"
        if execution is not None and execution.turn_started_count:
            return "model-result-wait-timeout"
        return "stage-timeout-before-turn"
    if error_stage == "process-spawn" and isinstance(exc, OSError):
        return "process-spawn"
    if error_stage == "process-exit":
        return "process-exit"
    if error_stage == "result-validate":
        return "result-contract"
    if error_stage in {
        "input-load",
        "dependency-preflight",
        "context-binding",
        "profile-route",
        "context-validation",
        "scope-boundary-binding",
        "clarification-binding",
        "semantic-input-preflight",
    }:
        return "input-contract"
    if isinstance(exc, json.JSONDecodeError):
        return "result-parse"
    if isinstance(exc, OSError):
        return "artifact-io"
    return "internal"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run one isolated tool-free bounded scope semantic model call.")
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--decision-output", type=Path, required=True)
    result.add_argument("--events-output", type=Path, required=True)
    result.add_argument("--stderr-output", type=Path, required=True)
    result.add_argument("--summary-output", type=Path, required=True)
    result.add_argument("--schema-output", type=Path, required=True)
    result.add_argument("--preflight-output", type=Path)
    result.add_argument("--terminal-receipt-output", type=Path)
    result.add_argument("--contract-version", type=int, choices=(1, 2), default=1)
    result.add_argument(
        "--scope-boundary-decision",
        type=Path,
        help=(
            "authoritative ready v2 scope decision; enables the standard-production "
            "semantic-design author route for contract version 1"
        ),
    )
    result.add_argument(
        "--scope-execution-profile",
        choices=("auto", LEAN_PROFILE, STANDARD_PROFILE),
        default="auto",
    )
    result.add_argument("--scope-execution-profile-output", type=Path)
    result.add_argument("--backend-selection-output", type=Path)
    result.add_argument("--image", action="append", type=Path, default=[])
    result.add_argument("--codex-command")
    result.add_argument(
        "--measurement-mode",
        choices=("production", "observational"),
        default="production",
    )
    timeout = result.add_mutually_exclusive_group()
    timeout.add_argument("--timeout-seconds", type=int)
    timeout.add_argument("--no-timeout", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    started = time.perf_counter_ns()
    execution: StreamingExecResult | None = None
    resolution: ExecCapabilityResolution | None = None
    profile: ScopeExecutionProfile | None = None
    context: dict[str, Any] | None = None
    boundary: dict[str, Any] | None = None
    clarifications: tuple[dict[str, Any], ...] = ()
    bridge_receipt: dict[str, Any] | None = None
    preflight: dict[str, Any] | None = None
    bridge_mode = args.scope_boundary_decision is not None
    execution_route = (
        "standard-semantic-design-author"
        if bridge_mode
        else (
            "legacy-detailed-v1"
            if args.contract_version == 1
            else "bounded-scope-v2"
        )
    )
    runner_attempt_count = 0
    result_parsed = False
    result_parsed_ms: int | None = None
    result_validated = False
    deterministic_repairs: dict[str, Any] | None = None
    error_stage = "input-load"
    timeout_seconds: int | None = None
    timeout_mode = "default"
    backend_probe_timeout_seconds: float | None = 15
    try:
        if not repo_root.is_dir():
            raise ScopeAnalyzerError("repo-root must resolve to an existing directory")
        protected_inputs = [args.context, *args.image]
        if args.scope_boundary_decision is not None:
            protected_inputs.append(args.scope_boundary_decision)
        decision_target = args.decision_output.resolve()
        if any(path.resolve() == decision_target for path in protected_inputs):
            raise ScopeAnalyzerError(
                "decision-output must be distinct from every input artifact"
            )
        if args.decision_output.exists():
            if not args.decision_output.is_file():
                raise ScopeAnalyzerError("decision-output exists and is not a file")
            args.decision_output.unlink()
        if args.measurement_mode == "observational" and args.timeout_seconds is not None:
            raise ScopeAnalyzerError(
                "observational measurement cannot use timeout-seconds"
            )
        if args.timeout_seconds is not None and args.timeout_seconds <= 0:
            raise ScopeAnalyzerError("timeout-seconds must be positive")
        if args.no_timeout or args.measurement_mode == "observational":
            timeout_seconds = None
            timeout_mode = "none"
        elif args.timeout_seconds is not None:
            timeout_seconds = args.timeout_seconds
            timeout_mode = "explicit"
        else:
            timeout_seconds = 150 if args.contract_version == 1 else 120
            timeout_mode = "default"
        backend_probe_timeout_seconds = (
            None if timeout_mode == "none" else 15
        )
        execution_policy = {
            "timeout_mode": timeout_mode,
            "timeout_seconds": timeout_seconds,
            "backend_probe_timeout_seconds": backend_probe_timeout_seconds,
            "runner_retry_mode": "disabled",
            "runner_max_attempts": 1,
        }
        missing_images = [str(path) for path in args.image if not path.is_file()]
        if missing_images:
            raise ScopeAnalyzerError("image input is missing: " + ", ".join(missing_images))
        context = json.loads(args.context.read_text(encoding="utf-8"))
        if not isinstance(context, dict) or not isinstance(context.get("source_rows"), list):
            raise ScopeAnalyzerError("context must be an object with source_rows")
        error_stage = "dependency-preflight"
        preflight = analyze_dependency_gaps(context)
        if args.preflight_output is not None:
            _write_json(args.preflight_output, preflight)
        if preflight["status"] == "blocked-input":
            _write_empty(args.events_output)
            _write_empty(args.stderr_output)
            duration_ms = (time.perf_counter_ns() - started) // 1_000_000
            error = (
                f"deterministic dependency gate found {preflight['blocking_gap_count']} "
                "blocking source gap(s)"
            )
            receipt_error = _publish_terminal_receipt(
                args.terminal_receipt_output,
                stage="scope-dependency-gap-gate",
                return_code=3,
                error_type="BlockedInput",
                error=error,
            )
            lifecycle = _lifecycle_payload(None, runner_attempt_count=0)
            summary = {
                "status": "blocked-input",
                "decision": "not-run",
                "contract_version": args.contract_version,
                "execution_route": execution_route,
                "duration_ms": duration_ms,
                "error_category": "blocked-input",
                "error_stage": "dependency-preflight",
                "model_invoked": _model_invoked_projection(lifecycle),
                "source_row_count": len(context["source_rows"]),
                "preflight": preflight,
                "tool_event_count": 0,
                "event_line_count": 0,
                "usage": None,
                "execution_policy": execution_policy,
                "lifecycle": lifecycle,
                "terminal_receipt": (
                    "published" if args.terminal_receipt_output and not receipt_error else None
                ),
                "terminal_receipt_error": receipt_error,
            }
            _write_json(args.summary_output, summary)
            print(json.dumps(summary, ensure_ascii=False))
            return 3

        error_stage = "context-binding"
        _validate_source_cache_binding(context, required=True)
        error_stage = "profile-route"
        profile = select_scope_execution_profile(
            context,
            requested_profile=args.scope_execution_profile,
            contract_version=args.contract_version,
        )
        if args.scope_execution_profile_output is not None:
            _write_json(args.scope_execution_profile_output, profile.to_dict())
        if bridge_mode:
            if args.contract_version != 1:
                raise ScopeAnalyzerError(
                    "semantic-design bridge requires contract-version 1"
                )
            if profile.selected_profile != STANDARD_PROFILE:
                raise ScopeAnalyzerError(
                    "semantic-design bridge requires standard-production profile"
                )
        if (
            profile.selected_profile == STANDARD_PROFILE
            and args.contract_version == 1
            and not bridge_mode
        ):
            _write_empty(args.events_output)
            _write_empty(args.stderr_output)
            error = (
                "standard-production scope cannot run the monolithic detailed-v1 "
                "contract; semantic-design bridge routing is required"
            )
            receipt_error = _publish_terminal_receipt(
                args.terminal_receipt_output,
                stage="scope-execution-profile-gate",
                return_code=4,
                error_type="RouteRequired",
                error=error,
            )
            lifecycle = _lifecycle_payload(None, runner_attempt_count=0)
            summary = {
                "status": "route-required",
                "decision": "not-run",
                "contract_version": args.contract_version,
                "execution_route": execution_route,
                "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
                "error_category": "route-required",
                "error_stage": "profile-route",
                "error": error,
                "model_invoked": _model_invoked_projection(lifecycle),
                "source_row_count": len(context["source_rows"]),
                "scope_execution_profile": profile.to_dict(),
                "preflight": preflight,
                "tool_event_count": 0,
                "event_line_count": 0,
                "usage": None,
                "execution_policy": execution_policy,
                "lifecycle": lifecycle,
                "terminal_receipt": (
                    "published" if args.terminal_receipt_output and not receipt_error else None
                ),
                "terminal_receipt_error": receipt_error,
            }
            _write_json(args.summary_output, summary)
            print(json.dumps(summary, ensure_ascii=False))
            return 4

        error_stage = "context-validation"
        if bridge_mode:
            _validate_scope_context(context)
            _validate_legacy_scope_context(context)
            error_stage = "scope-boundary-binding"
            assert args.scope_boundary_decision is not None
            boundary_payload = json.loads(
                args.scope_boundary_decision.read_text(encoding="utf-8")
            )
            if not isinstance(boundary_payload, dict):
                raise ScopeAnalyzerError(
                    "scope-boundary-decision must be a JSON object"
                )
            boundary = boundary_payload
            _validate_decision(boundary, context)
            validate_bridge_boundary(context, boundary)
            error_stage = "clarification-binding"
            clarifications = load_approved_clarifications(repo_root, context)
            error_stage = "semantic-input-preflight"
            assert preflight is not None
            try:
                semantic_input_preflight = validate_semantic_input_preflight(
                    context,
                    boundary,
                    clarifications,
                )
            except (TypeError, ValueError) as exc:
                preflight["semantic_input"] = {
                    "version": 1,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                if args.preflight_output is not None:
                    _write_json(args.preflight_output, preflight)
                raise
            preflight["semantic_input"] = semantic_input_preflight
            if args.preflight_output is not None:
                _write_json(args.preflight_output, preflight)
        elif args.contract_version == 2:
            _validate_scope_context(context)
        else:
            _validate_legacy_scope_context(context)
        row_ids = [str(item["source_row_id"]) for item in context["source_rows"]]
        if bridge_mode:
            assert boundary is not None
            # A ready v2 boundary plus the deterministic semantic preflight is a
            # release-design input. Source ambiguities are carried as gaps and
            # calibration candidates instead of discarding the entire scope.
            assert semantic_input_preflight is not None
            schema = semantic_design_output_schema(
                row_ids,
                require_ready=True,
                allow_canonical_clarification_binding=(
                    semantic_design_allows_canonical_transport_binding(
                        clarifications
                    )
                ),
                expected_minimum_obligation_count=semantic_design_minimum_obligation_count(
                    semantic_input_preflight,
                    boundary,
                ),
                # Transport normalization materializes omitted scope-excluded
                # bindings before strict schema validation, so schema cardinality
                # must cover the complete authoritative dependency registry.
                expected_dependency_count=sum(
                    isinstance(item, dict)
                    for item in boundary.get("dependencies", [])
                ),
                expected_dictionary_count=len(
                    semantic_input_preflight["dictionary_registry"]
                ),
                expected_negative_signal_count=semantic_input_preflight[
                    "negative_signal_count"
                ],
                expected_requiredness_signal_count=semantic_input_preflight[
                    "requiredness_signal_count"
                ],
            )
            prompt_text = semantic_design_prompt(
                context,
                boundary,
                clarifications,
                semantic_input_preflight=semantic_input_preflight,
            )
            validator = None
        elif args.contract_version == 1:
            schema = legacy_detailed_output_schema(row_ids)
            prompt_text = _legacy_detailed_prompt(context)
            validator = _validate_legacy_detailed_decision
        else:
            schema = output_schema(row_ids)
            prompt_text = _prompt(context)
            validator = _validate_decision
        schema_text = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
        args.schema_output.parent.mkdir(parents=True, exist_ok=True)
        args.schema_output.write_text(schema_text, encoding="utf-8", newline="\n")
        args.decision_output.parent.mkdir(parents=True, exist_ok=True)

        error_stage = "backend-probe"
        additional_flags = [
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--color",
        ]
        if args.image:
            additional_flags.append("--image")
        resolution = resolve_verified_exec_capability(
            args.codex_command,
            total_timeout_seconds=backend_probe_timeout_seconds,
            additional_required_flags=tuple(additional_flags),
            required_disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
        )
        if args.backend_selection_output is not None:
            _write_json(args.backend_selection_output, _resolution_payload(resolution))
        if not resolution.verified:
            capability = resolution.selection_capability()
            raise BackendRuntimeError(
                "no verified codex exec backend: "
                + (capability.error or ", ".join(capability.missing_flags))
            )
        command = [
            resolution.selected_executable,
            "exec",
            *resolution.disable_args,
            "--sandbox", "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--json",
            "--output-schema", str(args.schema_output.resolve()),
            "--output-last-message", str(args.decision_output.resolve()),
            "--color", "never",
        ]
        for image in args.image:
            command.extend(("--image", str(image.resolve())))
        command.append("-")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        with tempfile.TemporaryDirectory(prefix="bounded-scope-") as raw_cwd:
            command[2:2] = ["--cd", raw_cwd]
            runner_attempt_count = 1
            error_stage = "process-spawn"
            execution = run_exec_streaming(
                command,
                prompt=prompt_text,
                cwd=Path(raw_cwd),
                events_path=args.events_output,
                stderr_path=args.stderr_output,
                timeout_seconds=timeout_seconds,
                env=env,
                stage_started_ns=started,
            )
        error_stage = "process-wait"
        if execution.prompt_transport_error:
            error_stage = "prompt-send"
            raise PromptTransportError(execution.prompt_transport_error)
        if execution.runner_error:
            error_stage = execution.runner_error_stage or "process-wait"
            raise StreamingExecRuntimeError(
                f"{execution.runner_error_type}: {execution.runner_error}"
            )
        if execution.timed_out:
            if execution.model_result_count or execution.turn_completed_count:
                error_stage = "post-result-process-exit"
            elif execution.turn_started_count:
                error_stage = "model-result-wait"
            else:
                error_stage = "turn-start-wait"
            raise TimeoutError(f"scope analyzer timed out after {timeout_seconds}s")
        if execution.stream_transport_error or not execution.stream_complete:
            error_stage = "stream"
            raise StreamTransportError(
                execution.stream_transport_error or "codex event stream did not reach EOF"
            )
        protocol_errors = _backend_protocol_errors(execution)
        if protocol_errors:
            error_stage = "stream"
            raise BackendProtocolError("; ".join(protocol_errors))
        if execution.return_code != 0:
            error_stage = "process-exit"
            raise ScopeAnalyzerError(f"codex exec exited with code {execution.return_code}")
        if execution.tool_event_count:
            error_stage = "tool-contract"
            raise ToolContractError(
                f"tool-free scope analyzer emitted {execution.tool_event_count} tool events"
            )
        error_stage = "result-load"
        if not args.decision_output.is_file() or not args.decision_output.stat().st_size:
            raise ResultMissingError("codex exec completed without a scope decision output")
        decision = json.loads(args.decision_output.read_text(encoding="utf-8"))
        result_parsed = True
        result_parsed_ms = (time.perf_counter_ns() - started) // 1_000_000
        error_stage = "result-validate"
        if not isinstance(decision, dict):
            raise ScopeAnalyzerError("scope decision must be a JSON object")
        strict_instance_schema = {
            key: value for key, value in schema.items() if key != "$schema"
        }
        validate_openai_strict_output_instance(decision, strict_instance_schema)
        if bridge_mode:
            assert boundary is not None
            normalized_decision, deterministic_repairs = (
                normalize_semantic_design_transport(
                    decision,
                    context=context,
                    boundary=boundary,
                )
            )
            if deterministic_repairs["repair_count"]:
                raw_output = args.decision_output.with_name(
                    f"{args.decision_output.stem}.model-output.json"
                )
                _write_json(raw_output, decision)
                decision = normalized_decision
                validate_openai_strict_output_instance(decision, strict_instance_schema)
                _write_json(args.decision_output, decision)
                deterministic_repairs["raw_model_output"] = raw_output.name
                deterministic_repairs["normalized_output"] = args.decision_output.name
            bridge_receipt = validate_semantic_design_binding(
                context,
                boundary,
                decision,
                clarifications=clarifications,
                require_ready=True,
            )
        else:
            assert validator is not None
            validator(decision, context)
        result_validated = True
        duration_ms = (time.perf_counter_ns() - started) // 1_000_000
        lifecycle = _lifecycle_payload(
            execution,
            runner_attempt_count=runner_attempt_count,
            result_parsed=result_parsed,
            result_parsed_ms=result_parsed_ms,
            result_validated=result_validated,
        )
        summary = {
            "status": "completed",
            "decision": decision.get("status"),
            "contract_version": args.contract_version,
            "execution_route": execution_route,
            "duration_ms": duration_ms,
            "model_invoked": _model_invoked_projection(lifecycle),
            "tool_event_count": execution.tool_event_count,
            "event_line_count": execution.event_line_count,
            "source_row_count": len(row_ids),
            "prompt_bytes": len(prompt_text.encode("utf-8")),
            "schema_bytes": len(schema_text.encode("utf-8")),
            "usage": execution.usage,
            "preflight": preflight,
            "scope_execution_profile": profile.to_dict(),
            "execution_policy": execution_policy,
            "lifecycle": lifecycle,
            "backend": _resolution_payload(resolution),
            "deterministic_repairs": deterministic_repairs,
        }
        if bridge_mode:
            assert bridge_receipt is not None
            summary.update(
                {
                    "semantic_design_bridge": bridge_receipt,
                    "assertion_count": bridge_receipt["assertion_count"],
                    "testable_assertion_count": bridge_receipt[
                        "testable_assertion_count"
                    ],
                    "obligation_count": bridge_receipt["obligation_count"],
                    "planned_test_case_count": bridge_receipt[
                        "planned_test_case_count"
                    ],
                    "dictionary_count": bridge_receipt["dictionary_count"],
                    "approved_clarification_count": bridge_receipt[
                        "approved_clarification_count"
                    ],
                }
            )
        elif args.contract_version == 1:
            summary.update(
                {
                    "assertion_count": sum(
                        len(item["assertions"]) for item in decision["source_decisions"]
                    ),
                    "obligation_count": len(decision["obligations"]),
                }
            )
        else:
            disposition_counts = {"included": 0, "context": 0, "excluded": 0}
            for item in decision["source_decisions"]:
                disposition_counts[str(item["disposition"])] += 1
            summary.update(
                {
                    "source_disposition_counts": disposition_counts,
                    "dependency_count": len(decision["dependencies"]),
                    "gap_count": len(decision["gaps"]),
                    "blocking_gap_count": sum(
                        item["blocking"] is True for item in decision["gaps"]
                    ),
                }
            )
        _write_json(args.summary_output, summary)
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    except (
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        TimeoutError,
    ) as exc:
        return_code = 2
        receipt_error = _publish_terminal_receipt(
            args.terminal_receipt_output,
            stage=(
                "semantic-design-author"
                if bridge_mode
                else "bounded-scope-analyzer"
            ),
            return_code=return_code,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        lifecycle = _lifecycle_payload(
            execution,
            runner_attempt_count=runner_attempt_count,
            result_parsed=result_parsed,
            result_parsed_ms=result_parsed_ms,
            result_validated=result_validated,
        )
        summary = {
            "status": "terminal-failed",
            "contract_version": args.contract_version,
            "execution_route": execution_route,
            "error_category": _error_category(
                exc,
                error_stage=error_stage,
                execution=execution,
            ),
            "error_stage": error_stage,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
            "model_invoked": _model_invoked_projection(lifecycle),
            "tool_event_count": execution.tool_event_count if execution else None,
            "event_line_count": execution.event_line_count if execution else None,
            "usage": execution.usage if execution else None,
            "execution_policy": {
                "timeout_mode": timeout_mode,
                "timeout_seconds": timeout_seconds,
                "backend_probe_timeout_seconds": backend_probe_timeout_seconds,
                "runner_retry_mode": "disabled",
                "runner_max_attempts": 1,
            },
            "lifecycle": lifecycle,
            "scope_execution_profile": profile.to_dict() if profile else None,
            "preflight": preflight,
            "backend": _resolution_payload(resolution) if resolution else None,
            "partial_events_preserved": bool(
                args.events_output.is_file() and args.events_output.stat().st_size
            ),
            "partial_stderr_preserved": bool(
                args.stderr_output.is_file() and args.stderr_output.stat().st_size
            ),
            "terminal_receipt": (
                "published" if args.terminal_receipt_output and not receipt_error else None
            ),
            "terminal_receipt_error": receipt_error,
            "deterministic_repairs": deterministic_repairs,
        }
        _write_json(args.summary_output, summary)
        print(json.dumps(summary, ensure_ascii=False), file=sys.stderr)
        return return_code


if __name__ == "__main__":
    raise SystemExit(main())
