from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

from test_case_agent.review_cycle.contracts import StageInputManifest, ensure_new_session_id
from test_case_agent.review_cycle.runtime import BackendStageExecution, StageRuntimeError, utc_timestamp


class SdkThread(Protocol):
    id: str


class SdkClient(Protocol):
    def thread_start(self, **kwargs: Any) -> SdkThread:
        ...

    def close(self) -> None:
        ...


def start_fresh_sdk_thread(
    client: SdkClient,
    *,
    cwd: str,
    sandbox: Any,
    approval_mode: Any,
    model: str | None,
) -> SdkThread:
    """Start a stage thread without exposing resume or previous-thread inputs."""

    thread = client.thread_start(
        cwd=cwd,
        sandbox=sandbox,
        approval_mode=approval_mode,
        model=model,
    )
    thread_id = str(getattr(thread, "id", "") or "")
    if not thread_id:
        raise StageRuntimeError("SDK thread_start returned no thread id")
    return thread


TurnExecutor = Callable[[SdkThread, str, StageInputManifest, Path], Any]


@dataclass
class FreshThreadSdkBackend:
    client_factory: Callable[[], SdkClient]
    turn_executor: TurnExecutor
    sandbox_resolver: Callable[[str], Any] = lambda value: value
    approval_mode: Any = "never"
    model: str | None = None
    name: str = "sdk-fresh-thread"
    _seen_session_ids: list[str] = field(default_factory=list, init=False)

    def execute(
        self,
        manifest: StageInputManifest,
        *,
        prompt: str,
        cwd: Path,
    ) -> BackendStageExecution:
        manifest.validate()
        started_at = utc_timestamp()
        started_monotonic = time.monotonic()
        client = self.client_factory()
        thread: SdkThread | None = None
        try:
            thread = start_fresh_sdk_thread(
                client,
                cwd=str(cwd.resolve()),
                sandbox=self.sandbox_resolver(manifest.sandbox_policy),
                approval_mode=self.approval_mode,
                model=self.model,
            )
            backend_session_id = str(thread.id)
            ensure_new_session_id(backend_session_id, self._seen_session_ids)
            turn = self.turn_executor(thread, prompt, manifest, cwd.resolve())
            self._seen_session_ids.append(backend_session_id)
            response = str(getattr(turn, "final_response", "") or "")
            turn_id = str(getattr(turn, "id", "") or "")
            turn_status = _enum_value(getattr(turn, "status", ""))
            execution = BackendStageExecution(
                backend=self.name,
                backend_session_id=backend_session_id,
                started_at=started_at,
                finished_at=utc_timestamp(),
                duration_ms=_duration_ms(turn, started_monotonic),
                exit_code=None,
                stdout=response,
                events=_events(backend_session_id, turn_id, turn_status),
                usage=_usage(turn),
            )
            execution.validate()
            return execution
        except Exception as exc:
            execution = BackendStageExecution(
                backend=self.name,
                backend_session_id=str(getattr(thread, "id", "") or ""),
                started_at=started_at,
                finished_at=utc_timestamp(),
                duration_ms=max(0, round((time.monotonic() - started_monotonic) * 1000)),
                exit_code=None,
                stderr=f"{type(exc).__name__}: {exc}",
                launch_error=thread is None,
            )
            execution.validate()
            return execution
        finally:
            client.close()


def _events(thread_id: str, turn_id: str, turn_status: str) -> str:
    return "".join(
        (
            json.dumps({"type": "thread.started", "thread_id": thread_id}, sort_keys=True) + "\n",
            json.dumps(
                {
                    "type": "turn.finished",
                    "thread_id": thread_id,
                    "turn_id": turn_id,
                    "turn_status": turn_status,
                },
                sort_keys=True,
            )
            + "\n",
        )
    )


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value) or "")


def _duration_ms(turn: Any, started_monotonic: float) -> int:
    value = getattr(turn, "duration_ms", None)
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return max(0, round((time.monotonic() - started_monotonic) * 1000))


def _usage(turn: Any) -> dict[str, int] | None:
    usage = getattr(turn, "usage", None)
    if usage is None:
        return None
    result: dict[str, int] = {}
    aliases = {
        "input_tokens": ("input_tokens",),
        "cached_input_tokens": ("cached_input_tokens",),
        "output_tokens": ("output_tokens",),
        "total_tokens": ("total_tokens",),
        "reasoning_tokens": ("reasoning_tokens", "reasoning_output_tokens"),
    }
    for key, candidates in aliases.items():
        value = next(
            (getattr(usage, candidate, None) for candidate in candidates if getattr(usage, candidate, None) is not None),
            None,
        )
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result[key] = value
    return result or None
