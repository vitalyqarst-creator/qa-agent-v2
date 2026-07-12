from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence


REQUIRED_EXEC_HELP_FLAGS = (
    "--sandbox",
    "--cd",
    "--json",
    "--output-schema",
    "--output-last-message",
)

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


class DispatcherError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecCapability:
    command: str
    available: bool
    verified: bool
    returncode: int | None
    duration_ms: int
    missing_flags: tuple[str, ...]
    error: str = ""


@dataclass(frozen=True)
class BackendSelection:
    requested_backend: str
    selected_backend: str
    contract_version: int
    fallback_used: bool
    fallback_reason: str
    capability: ExecCapability


def default_exec_candidates() -> tuple[str, ...]:
    candidates: list[str] = []
    configured = os.environ.get("CODEX_EXEC_COMMAND", "").strip()
    if configured:
        candidates.append(configured)
    home = Path.home()
    candidates.append(str(home / ".codex" / "plugins" / ".plugin-appserver" / "codex.exe"))
    discovered = shutil.which("codex")
    if discovered:
        candidates.append(discovered)
    return tuple(dict.fromkeys(candidates))


def resolve_exec_command(explicit: str | None = None) -> str:
    candidates = (explicit,) if explicit else default_exec_candidates()
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file() or shutil.which(candidate):
            return str(path if path.is_file() else candidate)
    return str(candidates[0]) if candidates else "codex"


def probe_exec_capability(command: str, *, timeout_seconds: int = 15) -> ExecCapability:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [command, "exec", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ExecCapability(
            command=command,
            available=False,
            verified=False,
            returncode=None,
            duration_ms=int((time.monotonic() - started) * 1000),
            missing_flags=REQUIRED_EXEC_HELP_FLAGS,
            error=str(exc),
        )
    help_text = f"{completed.stdout}\n{completed.stderr}"
    missing = tuple(flag for flag in REQUIRED_EXEC_HELP_FLAGS if flag not in help_text)
    return ExecCapability(
        command=command,
        available=completed.returncode == 0,
        verified=completed.returncode == 0 and not missing,
        returncode=completed.returncode,
        duration_ms=int((time.monotonic() - started) * 1000),
        missing_flags=missing,
        error="" if completed.returncode == 0 else help_text[-1000:].strip(),
    )


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
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def summarize_exec_cycle(cycle_dir: Path, *, validator_budget: int = 5) -> dict[str, Any]:
    metric_records: list[dict[str, Any]] = []
    ledger = cycle_dir / "stage-metrics.ndjson"
    if ledger.exists():
        for raw in ledger.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                metric_records.append(json.loads(raw))
    validator_reports = tuple(cycle_dir.glob("attempts/*/*/runner-output/validator.json"))
    events_path = cycle_dir / "runner-events.ndjson"
    events: list[dict[str, Any]] = []
    if events_path.exists():
        for raw in events_path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                events.append(json.loads(raw))
    stage_attribution: list[dict[str, Any]] = []
    for event_file in sorted(cycle_dir.glob("attempts/*/*/runner-output/events.ndjson")):
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
    uncached_values = [
        max(
            0,
            int(item.get("input_tokens") or 0)
            - int(item.get("cached_input_tokens") or 0),
        )
        for item in metric_records
        if item.get("input_tokens") is not None
    ]
    report = {
        "version": 1,
        "backend": "exec",
        "cycle_dir": cycle_dir.as_posix(),
        "stage_count": len(metric_records),
        "duration_ms_total": sum(int(item.get("duration_ms") or 0) for item in metric_records),
        "total_tokens": sum(int(item.get("total_tokens") or 0) for item in metric_records)
        if any(item.get("total_tokens") is not None for item in metric_records)
        else None,
        "uncached_input_tokens_total": sum(uncached_values) if uncached_values else None,
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


def runner_command(
    selected_backend: str,
    config: dict[str, Any],
    *,
    repo_root: Path,
    exec_command: str,
) -> list[str]:
    python = repo_root / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = Path(sys.executable)
    if selected_backend == "exec":
        args = normalize_runner_args(config.get("exec_runner_args") or [])
        if not args:
            raise DispatcherError("exec_runner_args are required for exec execution")
        if "--codex-command" not in args:
            args.extend(("--codex-command", exec_command))
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
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    command = resolve_exec_command(args.codex_command)
    capability = probe_exec_capability(command)
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
                "requested_backend": args.backend,
                "selected_backend": "",
                "capability": asdict(capability),
                "blocking_reason": str(exc),
            },
        )
        print(str(exc), file=sys.stderr)
        return 2
    payload = {"version": 1, "status": "selected", **asdict(selection)}
    write_json(args.selection_output, payload)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.config is None:
        raise DispatcherError("--config is required unless --dry-run is used")
    config = load_config(args.config)
    command_line = runner_command(
        selection.selected_backend,
        config,
        repo_root=repo_root,
        exec_command=capability.command,
    )
    completed = subprocess.run(command_line, cwd=repo_root, check=False)
    if selection.selected_backend == "exec" and args.performance_output:
        cycle_dir_value = config.get("cycle_dir")
        if not isinstance(cycle_dir_value, str) or not cycle_dir_value:
            raise DispatcherError("cycle_dir is required to write exec performance metrics")
        cycle_dir = Path(cycle_dir_value)
        if not cycle_dir.is_absolute():
            cycle_dir = repo_root / cycle_dir
        performance = summarize_exec_cycle(cycle_dir)
        performance["cycle_dir"] = Path(cycle_dir_value).as_posix()
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
