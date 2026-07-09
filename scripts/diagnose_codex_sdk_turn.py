#!/usr/bin/env python
"""Standalone diagnostics for Codex SDK thread/turn hangs.

This script intentionally runs outside the review-cycle mutation path. It writes
diagnostic artifacts only, and never touches cycle-state.yaml, runner locks,
session maps, snapshots, or reviewer/writer outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_ROOT = Path("evals") / "sdk-turn-diagnostics"


class DiagnosticError(RuntimeError):
    pass


def utc_timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def enum_value(value: Any) -> str:
    return str(getattr(value, "value", value or ""))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_output_dir(path: str | None) -> Path:
    output_dir = Path(path) if path else DEFAULT_OUTPUT_ROOT / utc_timestamp()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def append_event(output_dir: Path, event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        "ts_epoch": int(time.time()),
        **fields,
    }
    event_path = output_dir / "events.ndjson"
    with event_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def load_openai_codex_runtime(*, required: tuple[str, ...] = ("Codex",)) -> Any:
    try:
        module = __import__("openai_codex", fromlist=list(required))
    except ImportError as exc:
        raise DiagnosticError(
            "openai-codex is not installed in this Python environment "
            f"({sys.executable})"
        ) from exc
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        raise DiagnosticError(
            "openai-codex runtime is incomplete in this Python environment "
            f"({sys.executable}); missing: {', '.join(missing)}"
        )
    return module


def sdk_sandbox(policy: str) -> Any:
    Sandbox = load_openai_codex_runtime(required=("Sandbox",)).Sandbox
    if policy == "read_only":
        return Sandbox.read_only
    if policy == "workspace_write":
        return Sandbox.workspace_write
    if policy == "full_access":
        return Sandbox.full_access
    raise DiagnosticError(f"Unsupported SDK sandbox policy: {policy}")


def sdk_approval_mode(name: str) -> Any:
    ApprovalMode = load_openai_codex_runtime(required=("ApprovalMode",)).ApprovalMode
    if name == "auto_review":
        if hasattr(ApprovalMode, "auto_review"):
            return ApprovalMode.auto_review
        return ApprovalMode.AUTO_REVIEW
    if name == "deny_all":
        if hasattr(ApprovalMode, "deny_all"):
            return ApprovalMode.deny_all
        return ApprovalMode.DENY_ALL
    raise DiagnosticError(f"Unsupported approval mode: {name}")


def prompt_from_args(args: argparse.Namespace) -> tuple[str, str]:
    if bool(args.prompt_file) == bool(args.prompt_text):
        raise DiagnosticError("Provide exactly one of --prompt-file or --prompt-text")
    if args.prompt_file:
        path = Path(args.prompt_file)
        return path.read_text(encoding="utf-8"), str(path)
    return str(args.prompt_text), "inline"


def write_run_json(output_dir: Path, payload: dict[str, Any]) -> None:
    (output_dir / "run.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_events(output_dir: Path) -> list[dict[str, Any]]:
    event_path = output_dir / "events.ndjson"
    if not event_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in event_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def timeout_diagnostics(output_dir: Path) -> dict[str, Any]:
    thread_id = ""
    thread_started_epoch = ""
    turn_started_epoch = ""
    for event in read_events(output_dir):
        event_name = str(event.get("event") or "")
        if event_name == "thread_started":
            thread_id = str(event.get("thread_id") or thread_id)
            thread_started_epoch = event.get("ts_epoch") or thread_started_epoch
        elif event_name == "turn_started":
            thread_id = str(event.get("thread_id") or thread_id)
            turn_started_epoch = event.get("ts_epoch") or turn_started_epoch
    if turn_started_epoch:
        phase = "sdk-turn-timeout-after-turn-started"
    elif thread_started_epoch:
        phase = "sdk-session-timeout-after-thread-started"
    else:
        phase = "child-process-timeout-before-thread-started"
    return {
        "thread_id": thread_id,
        "thread_started_epoch": thread_started_epoch,
        "turn_started_epoch": turn_started_epoch,
        "timeout_phase": phase,
    }


def blocked_status_from_failure_text(text: str) -> str | None:
    normalized = text.lower()
    if "openai-codex is not installed" in normalized or "openai-codex runtime is incomplete" in normalized:
        return "blocked-sdk-runtime"
    if (
        "authentication" in normalized
        or "unauthorized" in normalized
        or "invalid api key" in normalized
        or "api key" in normalized
        or "auth failed" in normalized
        or "auth error" in normalized
    ):
        return "blocked-sdk-auth"
    return None


def base_run_payload(
    *,
    cwd: str,
    prompt: str,
    prompt_source: str,
    sandbox_policy: str,
    approval_mode: str,
    model: str | None,
    timeout_seconds: int,
    output_dir: Path,
) -> dict[str, Any]:
    return {
        "version": 1,
        "status": "started",
        "cwd": str(Path(cwd).resolve()),
        "python": sys.executable,
        "prompt_source": prompt_source,
        "prompt_chars": len(prompt),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "prompt_sha256": sha256_text(prompt),
        "sandbox_policy": sandbox_policy,
        "approval_mode": approval_mode,
        "model": model or "",
        "timeout_seconds": timeout_seconds,
        "output_dir": str(output_dir),
        "started_at_epoch": int(time.time()),
    }


def run_diagnostic(
    *,
    cwd: str,
    prompt: str,
    prompt_source: str,
    sandbox_policy: str,
    approval_mode: str,
    model: str | None,
    timeout_seconds: int,
    output_dir: Path,
) -> dict[str, Any]:
    run_payload = base_run_payload(
        cwd=cwd,
        prompt=prompt,
        prompt_source=prompt_source,
        sandbox_policy=sandbox_policy,
        approval_mode=approval_mode,
        model=model,
        timeout_seconds=timeout_seconds,
        output_dir=output_dir,
    )
    write_run_json(output_dir, run_payload)
    prompt_path = output_dir / "prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_run-child",
        "--cwd",
        cwd,
        "--prompt-file",
        str(prompt_path),
        "--sandbox-policy",
        sandbox_policy,
        "--approval-mode",
        approval_mode,
        "--output-dir",
        str(output_dir),
    ]
    if model:
        command.extend(["--model", model])

    append_event(output_dir, "thread_start", cwd=str(Path(cwd).resolve()))
    started = time.monotonic()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", "child process did not exit after kill"
        elapsed_ms = int((time.monotonic() - started) * 1000)
        diag = timeout_diagnostics(output_dir)
        append_event(
            output_dir,
            "turn_timeout",
            timeout_seconds=timeout_seconds,
            elapsed_ms=elapsed_ms,
            stdout_tail=(stdout or "")[-1000:],
            stderr_tail=(stderr or "")[-1000:],
            **diag,
        )
        timeout_text = "\n".join(
            [
                "# Codex SDK turn timeout",
                "",
                f"timeout_seconds: {timeout_seconds}",
                f"elapsed_ms: {elapsed_ms}",
                f"timeout_phase: {diag['timeout_phase']}",
                f"thread_id: {diag['thread_id']}",
                f"thread_started_epoch: {diag['thread_started_epoch']}",
                f"turn_started_epoch: {diag['turn_started_epoch']}",
                "",
                "## stdout tail",
                "",
                stdout or "",
                "",
                "## stderr tail",
                "",
                stderr or "",
                "",
            ]
        )
        (output_dir / "timeout.md").write_text(timeout_text, encoding="utf-8")
        run_payload.update(
            {
                "status": "timeout",
                "elapsed_ms": elapsed_ms,
                "thread_id": diag["thread_id"],
                "timeout_phase": diag["timeout_phase"],
                "completed_at_epoch": int(time.time()),
            }
        )
        write_run_json(output_dir, run_payload)
        return run_payload

    elapsed_ms = int((time.monotonic() - started) * 1000)
    result_path = output_dir / "result.json"
    result: dict[str, Any] = {}
    if result_path.exists():
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result = {"status": "invalid-result-json"}

    if process.returncode != 0:
        failure_text = "\n".join(
            [
                stdout or "",
                stderr or "",
                (output_dir / "exception.md").read_text(encoding="utf-8", errors="replace")
                if (output_dir / "exception.md").exists()
                else "",
            ]
        )
        run_payload.update(
            {
                "status": blocked_status_from_failure_text(failure_text) or "exception",
                "returncode": process.returncode,
                "elapsed_ms": elapsed_ms,
                "stdout_tail": (stdout or "")[-1000:],
                "stderr_tail": (stderr or "")[-1000:],
                "completed_at_epoch": int(time.time()),
            }
        )
        write_run_json(output_dir, run_payload)
        return run_payload

    run_payload.update(
        {
            "status": "completed",
            "elapsed_ms": elapsed_ms,
            "thread_id": result.get("thread_id") or "",
            "turn_id": result.get("turn_id") or "",
            "turn_status": result.get("turn_status") or "",
            "completed_at_epoch": int(time.time()),
        }
    )
    write_run_json(output_dir, run_payload)
    return run_payload


def write_prompt_diagnostic(
    *,
    cwd: str,
    prompt: str,
    prompt_source: str,
    sandbox_policy: str,
    approval_mode: str,
    model: str | None,
    timeout_seconds: int,
    output_dir: Path,
) -> dict[str, Any]:
    payload = base_run_payload(
        cwd=cwd,
        prompt=prompt,
        prompt_source=prompt_source,
        sandbox_policy=sandbox_policy,
        approval_mode=approval_mode,
        model=model,
        timeout_seconds=timeout_seconds,
        output_dir=output_dir,
    )
    payload.update({"status": "rendered-prompt", "completed_at_epoch": int(time.time())})
    (output_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    write_run_json(output_dir, payload)
    append_event(output_dir, "prompt_rendered", prompt_sha256=payload["prompt_sha256"])
    return payload


def child_main(args: argparse.Namespace) -> int:
    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    codex_module = load_openai_codex_runtime(required=("Codex",))
    codex = codex_module.Codex()
    thread = None
    started = time.monotonic()
    try:
        thread = codex.thread_start(
            cwd=args.cwd,
            sandbox=sdk_sandbox(args.sandbox_policy),
            approval_mode=sdk_approval_mode(args.approval_mode),
            model=args.model,
        )
        try:
            thread.set_name("sdk-turn-diagnostic")
        except Exception:
            pass
        thread_id = str(getattr(thread, "id", "") or "")
        append_event(output_dir, "thread_started", thread_id=thread_id)
        append_event(output_dir, "turn_started", thread_id=thread_id)
        turn = thread.run(
            prompt,
            cwd=args.cwd,
            sandbox=sdk_sandbox(args.sandbox_policy),
            approval_mode=sdk_approval_mode(args.approval_mode),
            model=args.model,
        )
        final_response = str(getattr(turn, "final_response", "") or "")
        (output_dir / "response.md").write_text(final_response, encoding="utf-8")
        result = {
            "thread_id": thread_id,
            "turn_id": str(getattr(turn, "id", "") or ""),
            "turn_status": enum_value(getattr(turn, "status", "")),
            "duration_ms": getattr(turn, "duration_ms", "") or int((time.monotonic() - started) * 1000),
        }
        (output_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        append_event(output_dir, "turn_finished", **result)
        return 0
    except Exception as exc:
        thread_id = str(getattr(thread, "id", "") or "") if thread is not None else ""
        trace = traceback.format_exc()
        (output_dir / "exception.md").write_text(trace, encoding="utf-8")
        append_event(
            output_dir,
            "turn_exception",
            thread_id=thread_id,
            error=type(exc).__name__,
        )
        return 2
    finally:
        try:
            codex.close()
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose standalone Codex SDK turns")
    subparsers = parser.add_subparsers(dest="command")

    child = subparsers.add_parser("_run-child", help=argparse.SUPPRESS)
    child.add_argument("--cwd", required=True, help=argparse.SUPPRESS)
    child.add_argument("--prompt-file", required=True, help=argparse.SUPPRESS)
    child.add_argument("--sandbox-policy", required=True, help=argparse.SUPPRESS)
    child.add_argument("--approval-mode", required=True, help=argparse.SUPPRESS)
    child.add_argument("--model", help=argparse.SUPPRESS)
    child.add_argument("--output-dir", required=True, help=argparse.SUPPRESS)
    child.set_defaults(func=child_main)

    parser.add_argument("--cwd", default=str(Path.cwd()), help="Working directory for the SDK thread")
    prompt = parser.add_mutually_exclusive_group()
    prompt.add_argument("--prompt-file", help="UTF-8 prompt file to send to the SDK")
    prompt.add_argument("--prompt-text", help="Prompt text to send to the SDK")
    parser.add_argument(
        "--sandbox-policy",
        choices=("read_only", "workspace_write", "full_access"),
        default="read_only",
        help="SDK sandbox policy. Default: read_only.",
    )
    parser.add_argument(
        "--approval-mode",
        choices=("auto_review", "deny_all"),
        default="auto_review",
        help="SDK approval mode. Default: auto_review.",
    )
    parser.add_argument("--model", help="Optional SDK model override")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="Parent process timeout")
    parser.add_argument("--output-dir", help="Diagnostic output directory")
    parser.set_defaults(func=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "_run-child":
            return args.func(args)
        prompt, prompt_source = prompt_from_args(args)
        output_dir = ensure_output_dir(args.output_dir)
        payload = run_diagnostic(
            cwd=args.cwd,
            prompt=prompt,
            prompt_source=prompt_source,
            sandbox_policy=args.sandbox_policy,
            approval_mode=args.approval_mode,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
            output_dir=output_dir,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except DiagnosticError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
