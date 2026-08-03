from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.exec_backend import (
    ExecCapability,
    ExecCapabilityResolution,
    PLUGIN_ISOLATION_DISABLE_FEATURES,
    REQUIRED_EXEC_HELP_FLAGS,
    default_exec_candidates,
    probe_exec_capability,
    resolve_exec_command,
    resolve_verified_exec_capability,
)


RUN_PROFILES = ("production", "benchmark")

RUNNER_OPTION_VALUE_FLAGS = frozenset(
    {
        "--sandbox-flag",
        "--working-directory-flag",
        "--json-flag",
        "--output-last-message-flag",
        "--output-schema-flag",
        "--extra-arg",
    }
)

CANONICAL_RUNNER_FLAG_BINDINGS = {
    "--sandbox-flag": "--sandbox",
    "--working-directory-flag": "--cd",
    "--json-flag": "--json",
    "--output-last-message-flag": "--output-last-message",
    "--output-schema-flag": "--output-schema",
}


class DispatcherError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackendSelection:
    requested_backend: str
    selected_backend: str
    contract_version: int
    fallback_used: bool
    fallback_reason: str
    capability: ExecCapability

def select_backend(
    requested_backend: str,
    capability: ExecCapability,
    *,
    allow_sdk_fallback: bool,
) -> BackendSelection:
    if requested_backend == "sdk":
        return BackendSelection("sdk", "sdk", 1, False, "", capability)
    if capability.verified:
        return BackendSelection(requested_backend, "exec", 2, False, "", capability)
    reason = capability.error or (
        "missing exec flags: " + ", ".join(capability.missing_flags)
        if capability.missing_flags
        else "codex exec capability probe failed"
    )
    if requested_backend == "auto" and allow_sdk_fallback:
        return BackendSelection("auto", "sdk", 1, True, reason, capability)
    raise DispatcherError(f"blocked-exec-runtime: {reason}")


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise DispatcherError("dispatcher config version must be 1")
    for key in ("exec_runner_args", "sdk_runner_args"):
        value = payload.get(key, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise DispatcherError(f"{key} must be a string array")
    cycle_dir = payload.get("cycle_dir")
    if not isinstance(cycle_dir, str) or not cycle_dir:
        raise DispatcherError("cycle_dir must be a non-empty string")
    exec_args = payload.get("exec_runner_args") or []
    declared_cycle_dirs = [
        exec_args[index + 1]
        for index, item in enumerate(exec_args[:-1])
        if item == "--cycle-dir"
    ]
    if exec_args and declared_cycle_dirs != [cycle_dir]:
        raise DispatcherError(
            "cycle_dir must exactly match one --cycle-dir value in exec_runner_args"
        )
    return payload


def preflight_exec_runner(command_line: Sequence[str], *, repo_root: Path) -> int:
    started = time.monotonic()
    preflight = list(command_line)
    if "--validate-only" not in preflight:
        preflight.append("--validate-only")
    completed = subprocess.run(
        preflight,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode == 0:
        return int((time.monotonic() - started) * 1000)
    detail = (completed.stdout or completed.stderr or "runner preflight failed").strip()
    raise DispatcherError(f"blocked-configuration-preflight: {detail[-2000:]}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def build_timing_breakdown(
    *,
    capability_probe_ms: int,
    runner_preflight_ms: int,
    runner_wall_ms: int,
    stage_execution_ms: int,
    reporting_ms: int,
    dispatcher_wall_ms: int,
) -> dict[str, int]:
    return {
        "capability_probe_ms": capability_probe_ms,
        "runner_preflight_ms": runner_preflight_ms,
        "runner_wall_ms": runner_wall_ms,
        "stage_execution_ms": stage_execution_ms,
        "runner_orchestration_overhead_ms": max(
            0, runner_wall_ms - stage_execution_ms
        ),
        "reporting_ms": reporting_ms,
        "dispatcher_wall_ms": dispatcher_wall_ms,
    }


def summarize_exec_cycle(
    cycle_dir: Path,
    *,
    validator_budget: int = 5,
    run_profile: str = "benchmark",
) -> dict[str, Any]:
    if run_profile not in RUN_PROFILES:
        raise DispatcherError(f"run_profile must be one of {RUN_PROFILES}")
    benchmark_details = run_profile == "benchmark"
    metric_records: list[dict[str, Any]] = []
    ledger = cycle_dir / "stage-metrics.ndjson"
    if ledger.exists():
        for raw in ledger.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                metric_records.append(json.loads(raw))
    validator_reports = tuple(cycle_dir.glob("attempts/*/*/runner-output/validator.json"))
    events_path = cycle_dir / "runner-events.ndjson"
    events: list[dict[str, Any]] = []
    # Session ids are production audit evidence, not benchmark-only telemetry.
    # Keep expensive per-attempt event/context scans behind benchmark_details,
    # but always read the small runner lifecycle ledger when it exists.
    if events_path.exists():
        for raw in events_path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                events.append(json.loads(raw))
    stage_attribution: list[dict[str, Any]] = []
    event_files = (
        sorted(cycle_dir.glob("attempts/*/*/runner-output/events.ndjson"))
        if benchmark_details
        else ()
    )
    for event_file in event_files:
        counts = {
            "turns_started": 0,
            "agent_messages": 0,
            "command_executions": 0,
            "file_changes": 0,
        }
        if event_file.exists():
            for raw in event_file.read_text(encoding="utf-8").splitlines():
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "turn.started":
                    counts["turns_started"] += 1
                item = event.get("item")
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type in {"agent_message", "message"}:
                    counts["agent_messages"] += 1
                elif item_type == "command_execution":
                    counts["command_executions"] += 1
                elif item_type == "file_change":
                    counts["file_changes"] += 1
        relative = event_file.relative_to(cycle_dir)
        stage_attribution.append(
            {
                "stage_id": relative.parts[1],
                "attempt_id": relative.parts[2],
                **counts,
            }
        )
    context_records: list[dict[str, Any]] = []
    context_paths = (
        sorted(cycle_dir.glob("attempts/*/*/runner-output/context-budget.json"))
        if benchmark_details
        else ()
    )
    for context_path in context_paths:
        try:
            payload = json.loads(context_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            context_records.append(payload)
    obligation_reports = sorted(
        cycle_dir.glob("attempts/writer-r1/*/runner-output/obligation-gate.json")
    )
    test_case_count = 0
    testable_obligations = 0
    if obligation_reports:
        try:
            obligation_report = json.loads(obligation_reports[-1].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            obligation_report = {}
        if isinstance(obligation_report, dict):
            test_case_count = int(obligation_report.get("test_case_count") or 0)
            testable_obligations = int(obligation_report.get("testable_obligations") or 0)
    uncached_values = [
        max(
            0,
            int(item.get("input_tokens") or 0)
            - int(item.get("cached_input_tokens") or 0),
        )
        for item in metric_records
        if item.get("input_tokens") is not None
    ]
    uncached_total = sum(uncached_values) if uncached_values else None
    command_total = sum(item["command_executions"] for item in stage_attribution)
    file_change_total = sum(item["file_changes"] for item in stage_attribution)
    report = {
        "version": 2,
        "backend": "exec",
        "run_profile": run_profile,
        "benchmark_details_included": benchmark_details,
        "cycle_dir": cycle_dir.as_posix(),
        "stage_count": len(metric_records),
        "duration_ms_total": sum(int(item.get("duration_ms") or 0) for item in metric_records),
        "total_tokens": sum(int(item.get("total_tokens") or 0) for item in metric_records)
        if any(item.get("total_tokens") is not None for item in metric_records)
        else None,
        "uncached_input_tokens_total": uncached_total,
        "input_artifact_bytes_total": sum(int(item.get("input_artifact_bytes") or 0) for item in metric_records),
        "output_artifact_bytes_total": sum(int(item.get("output_artifact_bytes") or 0) for item in metric_records),
        "validator_invocations": len(validator_reports),
        "validator_budget": validator_budget,
        "validator_budget_passed": len(validator_reports) <= validator_budget,
        "backend_session_ids": [
            str(item.get("backend_session_id"))
            for item in events
            if item.get("event") == "stage_process_finished" and item.get("backend_session_id")
        ],
        "stage_metrics": metric_records,
        "stage_attribution": stage_attribution,
        "context_efficiency": {
            "primary_context_bytes_total": sum(
                int(item.get("primary_context_bytes") or 0) for item in context_records
            ),
            "prompt_bytes_total": sum(
                int(item.get("prompt_bytes") or 0) for item in context_records
            ),
            "instruction_bytes_total": sum(
                int(item.get("instruction_bytes") or 0) for item in context_records
            ),
            "instruction_artifact_count_total": sum(
                int(item.get("instruction_artifact_count") or 0)
                for item in context_records
            ),
            "command_executions_total": command_total,
            "file_changes_total": file_change_total,
            "test_case_count": test_case_count,
            "testable_obligations": testable_obligations,
            "uncached_tokens_per_obligation": (
                round(uncached_total / testable_obligations, 2)
                if uncached_total is not None and testable_obligations
                else None
            ),
            "commands_per_test_case": (
                round(command_total / test_case_count, 2) if test_case_count else None
            ),
        },
    }
    return report


def normalize_runner_args(args: Sequence[str]) -> list[str]:
    """Bind option-looking values so the child argparse parser does not consume them as flags."""
    normalized: list[str] = []
    index = 0
    while index < len(args):
        item = args[index]
        if item in RUNNER_OPTION_VALUE_FLAGS and index + 1 < len(args):
            value = args[index + 1]
            if value.startswith("--"):
                normalized.append(f"{item}={value}")
                index += 2
                continue
        normalized.append(item)
        index += 1
    return normalized


def _option_values(args: Sequence[str], option: str) -> list[str]:
    values: list[str] = []
    index = 0
    prefix = option + "="
    while index < len(args):
        item = args[index]
        if item.startswith(prefix):
            values.append(item[len(prefix):])
            index += 1
            continue
        if item == option:
            if index + 1 >= len(args):
                raise DispatcherError(f"{option} requires a value")
            values.append(args[index + 1])
            index += 2
            continue
        index += 1
    return values


def _without_option(args: Sequence[str], option: str) -> list[str]:
    result: list[str] = []
    index = 0
    prefix = option + "="
    while index < len(args):
        item = args[index]
        if item.startswith(prefix):
            index += 1
            continue
        if item == option:
            if index + 1 >= len(args):
                raise DispatcherError(f"{option} requires a value")
            index += 2
            continue
        result.append(item)
        index += 1
    return result


def _path_identity(value: str, *, repo_root: Path) -> str:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (repo_root / path).resolve()
    return os.path.normcase(str(resolved))


def validate_exec_runner_contract_args(
    args: Sequence[str],
    *,
    selected_executable: str,
    repo_root: Path,
) -> None:
    configured_commands = _option_values(args, "--codex-command")
    if any(
        _path_identity(value, repo_root=repo_root)
        != _path_identity(selected_executable, repo_root=repo_root)
        for value in configured_commands
    ):
        raise DispatcherError(
            "exec_runner_args --codex-command differs from the verified executable"
        )
    for option, expected in CANONICAL_RUNNER_FLAG_BINDINGS.items():
        values = _option_values(args, option)
        if any(value != expected for value in values):
            raise DispatcherError(
                f"exec_runner_args {option} must be bound to {expected}"
            )
    if _option_values(args, "--extra-arg"):
        raise DispatcherError(
            "config-owned --extra-arg is not capability-bound; dispatcher owns exec extras"
        )


def runner_command(
    selected_backend: str,
    config: dict[str, Any],
    *,
    repo_root: Path,
    exec_command: str,
    exec_extra_args: Sequence[str] = (),
) -> list[str]:
    python = repo_root / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = Path(sys.executable)
    if selected_backend == "exec":
        args = list(config.get("exec_runner_args") or [])
        if not args:
            raise DispatcherError("exec_runner_args are required for exec execution")
        validate_exec_runner_contract_args(
            args,
            selected_executable=exec_command,
            repo_root=repo_root,
        )
        args = _without_option(args, "--codex-command")
        for value in exec_extra_args:
            args.extend(("--extra-arg", value))
        args.extend(("--codex-command", exec_command))
        args = normalize_runner_args(args)
        if "--cli-contract-verified" not in args:
            args.append("--cli-contract-verified")
        return [str(python), str(repo_root / "scripts" / "codex_exec_review_cycle_runner.py"), *args]
    args = list(config.get("sdk_runner_args") or [])
    if not args:
        raise DispatcherError("sdk_runner_args are required for SDK execution")
    return [str(python), str(repo_root / "scripts" / "codex_review_cycle_runner.py"), *args]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Select and run the review-cycle backend explicitly.")
    parser.add_argument("--backend", choices=("auto", "exec", "sdk"), default="auto")
    parser.add_argument("--allow-sdk-fallback", action="store_true")
    parser.add_argument("--codex-command")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--selection-output", type=Path, required=True)
    parser.add_argument("--performance-output", type=Path)
    parser.add_argument("--run-profile", choices=RUN_PROFILES, default="production")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    dispatcher_started = time.monotonic()
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    config: dict[str, Any] | None = None
    if not args.dry_run:
        if args.config is None:
            raise DispatcherError("--config is required unless --dry-run is used")
        config = load_config(args.config)
        if args.run_profile == "benchmark" and args.performance_output is None:
            raise DispatcherError(
                "--performance-output is required for run-profile benchmark"
            )
    if args.backend == "sdk":
        resolution = ExecCapabilityResolution(
            requested_command=args.codex_command or "",
            probes=(),
            selected=None,
        )
        capability = ExecCapability(
            command=args.codex_command or "",
            available=False,
            verified=False,
            returncode=None,
            duration_ms=0,
            missing_flags=(),
            error="exec capability probe skipped for explicit sdk backend",
        )
    else:
        resolution = resolve_verified_exec_capability(
            args.codex_command,
            required_disable_features=PLUGIN_ISOLATION_DISABLE_FEATURES,
            probe=probe_exec_capability,
        )
        capability = resolution.selection_capability()
    try:
        selection = select_backend(
            args.backend,
            capability,
            allow_sdk_fallback=args.allow_sdk_fallback,
        )
    except DispatcherError as exc:
        write_json(
            args.selection_output,
            {
                "version": 1,
                "status": "blocked-exec-runtime",
                "run_profile": args.run_profile,
                "requested_backend": args.backend,
                "selected_backend": "",
                "capability": asdict(capability),
                "capability_probes": [asdict(item) for item in resolution.probes],
                "capability_probe_total_ms": resolution.total_duration_ms,
                "blocking_reason": str(exc),
            },
        )
        print(str(exc), file=sys.stderr)
        return 2
    if args.dry_run:
        payload = {
            "version": 1,
            "status": "selected",
            "run_profile": args.run_profile,
            "capability_probes": [asdict(item) for item in resolution.probes],
            "capability_probe_total_ms": resolution.total_duration_ms,
            **asdict(selection),
        }
        write_json(args.selection_output, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    assert config is not None
    command_line = runner_command(
        selection.selected_backend,
        config,
        repo_root=repo_root,
        exec_command=(
            resolution.selected_executable
            or capability.resolved_command
            or capability.command
        ),
        exec_extra_args=resolution.disable_args,
    )
    preflight_ms = 0
    if selection.selected_backend == "exec":
        preflight_ms = preflight_exec_runner(command_line, repo_root=repo_root)
    payload = {
        "version": 1,
        "status": "selected",
        "run_profile": args.run_profile,
        "capability_probes": [asdict(item) for item in resolution.probes],
        "capability_probe_total_ms": resolution.total_duration_ms,
        **asdict(selection),
    }
    write_json(args.selection_output, payload)
    runner_started = time.monotonic()
    completed = subprocess.run(command_line, cwd=repo_root, check=False)
    runner_wall_ms = int((time.monotonic() - runner_started) * 1000)
    if selection.selected_backend == "exec" and args.performance_output:
        cycle_dir_value = config.get("cycle_dir")
        if not isinstance(cycle_dir_value, str) or not cycle_dir_value:
            raise DispatcherError("cycle_dir is required to write exec performance metrics")
        cycle_dir = Path(cycle_dir_value)
        if not cycle_dir.is_absolute():
            cycle_dir = repo_root / cycle_dir
        reporting_started = time.monotonic()
        performance = summarize_exec_cycle(
            cycle_dir,
            run_profile=args.run_profile,
        )
        performance["cycle_dir"] = Path(cycle_dir_value).as_posix()
        stage_execution_ms = int(performance["duration_ms_total"])
        performance["timing_breakdown"] = build_timing_breakdown(
            capability_probe_ms=resolution.total_duration_ms,
            runner_preflight_ms=preflight_ms,
            runner_wall_ms=runner_wall_ms,
            stage_execution_ms=stage_execution_ms,
            reporting_ms=int((time.monotonic() - reporting_started) * 1000),
            dispatcher_wall_ms=int(
                (time.monotonic() - dispatcher_started) * 1000
            ),
        )
        write_json(args.performance_output, performance)
        if not performance["validator_budget_passed"]:
            return 3
    return completed.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DispatcherError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
