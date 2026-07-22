from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from test_case_agent.review_cycle.exec_backend import (
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
    resolve_verified_exec_capability,
)
from test_case_agent.review_cycle.exec_events import TOOL_EVENT_ITEM_TYPES
from test_case_agent.strict_output_schema import (
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)


class StageBackendError(RuntimeError):
    """A model stage could not complete through the isolated execution backend."""


@dataclass(frozen=True)
class StageResult:
    payload: dict[str, Any]
    receipt: dict[str, Any]


def _usage_from_events(text: str) -> dict[str, Any] | str:
    candidates: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            usage = value.get("usage")
            if isinstance(usage, Mapping):
                candidates.append(dict(usage))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for line in text.splitlines():
        try:
            visit(json.loads(line))
        except json.JSONDecodeError:
            continue
    return candidates[-1] if candidates else "unavailable"


def _tool_event_count(text: str) -> int:
    count = 0
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        item = event.get("item")
        if isinstance(item, Mapping) and item.get("type") in TOOL_EVENT_ITEM_TYPES:
            count += 1
    return count


class CodexExecStageBackend:
    """Fresh, tool-free Codex process per stage; no model timeout by default."""

    def __init__(
        self,
        *,
        codex_command: str | None = None,
        timeout_seconds: float | None = None,
        probe_timeout_seconds: float = 15,
    ) -> None:
        self.codex_command = codex_command
        self.timeout_seconds = timeout_seconds
        self.probe_timeout_seconds = probe_timeout_seconds

    def run_stage(
        self,
        *,
        stage: str,
        prompt: str,
        schema: Mapping[str, Any],
        artifact_dir: Path,
    ) -> StageResult:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        schema_path = artifact_dir / f"{stage}-output-schema.json"
        output_path = artifact_dir / f"{stage}-response.json"
        events_path = artifact_dir / f"{stage}-events.jsonl"
        stderr_path = artifact_dir / f"{stage}-stderr.txt"
        try:
            validate_openai_strict_output_schema(schema)
        except ValueError as exc:
            raise StageBackendError(f"{stage} output schema is invalid: {exc}") from exc
        schema_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        schema_bytes = schema_path.stat().st_size
        prompt_bytes = len(prompt.encode("utf-8"))
        resolution = resolve_verified_exec_capability(
            self.codex_command,
            total_timeout_seconds=self.probe_timeout_seconds,
            additional_required_flags=(
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-user-config",
                "--color",
            ),
            required_disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
        )
        if not resolution.verified:
            capability = resolution.selection_capability()
            raise StageBackendError(
                "no verified codex exec backend: "
                + (capability.error or ", ".join(capability.missing_flags))
            )
        started = time.perf_counter_ns()
        with tempfile.TemporaryDirectory(prefix=f"stage-{stage}-") as raw_cwd:
            command = [
                resolution.selected_executable,
                "exec",
                "--cd",
                raw_cwd,
                *resolution.disable_args,
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-user-config",
                "--json",
                "--output-schema",
                str(schema_path.resolve()),
                "--output-last-message",
                str(output_path.resolve()),
                "--color",
                "never",
                "-",
            ]
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=raw_cwd,
                    env=env,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise StageBackendError(
                    f"{stage} exceeded explicit timeout {self.timeout_seconds}s"
                ) from exc
            except (OSError, subprocess.SubprocessError) as exc:
                raise StageBackendError(f"{stage} process failed: {exc}") from exc
        duration_ms = (time.perf_counter_ns() - started) // 1_000_000
        events_path.write_text(completed.stdout, encoding="utf-8", newline="\n")
        stderr_path.write_text(completed.stderr, encoding="utf-8", newline="\n")
        tool_events = _tool_event_count(completed.stdout)
        if completed.returncode != 0:
            raise StageBackendError(
                f"{stage} codex exec exited with code {completed.returncode}: "
                f"{completed.stderr[-1000:]}"
            )
        if tool_events:
            raise StageBackendError(f"{stage} emitted {tool_events} forbidden tool events")
        if not output_path.is_file() or not output_path.stat().st_size:
            raise StageBackendError(f"{stage} completed without structured output")
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StageBackendError(f"{stage} output is not JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise StageBackendError(f"{stage} output must be a JSON object")
        try:
            validate_openai_strict_output_instance(payload, schema)
        except ValueError as exc:
            raise StageBackendError(
                f"{stage} output failed strict schema validation: {exc}"
            ) from exc
        return StageResult(
            payload=payload,
            receipt={
                "stage": stage,
                "backend": "codex-exec-tool-free",
                "attempts": 1,
                "duration_ms": duration_ms,
                "capability_probe_ms": resolution.duration_ms,
                "tokens": _usage_from_events(completed.stdout),
                "tool_event_count": tool_events,
                "codex_version": resolution.selected.version if resolution.selected else "",
                "timeout_seconds": self.timeout_seconds,
                "input_artifacts": {"count": 2, "bytes": prompt_bytes + schema_bytes},
                "output_artifacts": {
                    "count": 3,
                    "bytes": (
                        output_path.stat().st_size
                        + events_path.stat().st_size
                        + stderr_path.stat().st_size
                    ),
                },
            },
        )
