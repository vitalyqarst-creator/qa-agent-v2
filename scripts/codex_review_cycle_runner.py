"""Session-based writer/reviewer cycle runner.

This script validates and dry-runs the new Codex SDK orchestration contract for
test-case writer/reviewer work. It intentionally keeps domain decisions in
skills and references; the runner only enforces lifecycle gates, snapshots
artifacts, and selects the next session prompt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNNER_LOCK_FILE = "runner.lock.yaml"
RUNNER_EVENTS_FILE = "runner-events.ndjson"
COMPLETION_MANIFEST_SUFFIX = "-completion.yaml"
DEFAULT_STALE_LOCK_SECONDS = 1800
HEARTBEAT_INTERVAL_SECONDS = 30
TERMINAL_STATUSES = {"signed-off", "round-cap-reached", "blocked-input"}
PROGRESS_ACCEPTED_TURN_STATUSES = {"interrupted"}
CHAIN_ACCEPTED_SESSION_STATUSES = {"completed", "completed-with-progress"}
PROGRESS_STATE_KEYS = (
    "current_stage",
    "stage_status",
    "semantic_round",
    "active_transition_prompt",
)
PRE_WRITER_STATUSES = {
    "scope-ready-for-gap-review",
    "scope-gap-review-passed",
    "scope-ready-for-writer",
}
ALLOWED_STATUSES = {
    *PRE_WRITER_STATUSES,
    "writer-draft-ready",
    "structure-preflight-blocked",
    "semantic-review-ready",
    "semantic-revision-needed",
    "semantic-review-passed",
    "format-review-ready",
    "format-revision-needed",
    "final-regression-ready",
    *TERMINAL_STATUSES,
}


@dataclass(frozen=True)
class NextSession:
    stage: str
    role: str
    scenario: str
    prompt_path: str
    sandbox_policy: str


class RunnerError(RuntimeError):
    pass


def resolve_instruction_context_for_scenario(scenario: str) -> dict[str, Any]:
    script_path = Path(__file__).resolve().with_name("resolve_instruction_context.py")
    root = script_path.parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--scenario",
            scenario,
            "--json",
            "--fail-on-budget",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RunnerError(
            f"Instruction context resolution failed for {scenario}: {detail}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RunnerError(
            f"Instruction context resolver returned invalid JSON for {scenario}"
        ) from exc
    missing = payload.get("missing") or []
    if missing:
        raise RunnerError(
            f"Instruction context for {scenario} has missing files: {', '.join(missing)}"
        )
    return payload


def instruction_context_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario": payload.get("scenario"),
        "budget": payload.get("budget", {}),
        "files": [
            {
                "path": item.get("path"),
                "group": item.get("group"),
                "category": item.get("category"),
            }
            for item in payload.get("files", [])
        ],
    }


def render_instruction_context_contract(scenario: str, payload: dict[str, Any]) -> str:
    files = payload.get("files", [])
    budget = payload.get("budget", {})
    lines = [
        "Instruction loading contract:",
        f"- Before domain work, run: python scripts/resolve_instruction_context.py --scenario {scenario} --budget-report --fail-on-budget",
        "- Read every selected required file listed below before making writer/reviewer decisions.",
        "- If the resolver fails, a selected required file cannot be read, or budget status is not pass, do not sign off; record the blocker in the stage output.",
        "- In the session log, record the resolver command, budget status, and selected files under inputs read.",
        f"- Resolved now: {len(files)} files, budget {budget.get('status')} ({budget.get('total_kib')} / {budget.get('limit_kib')} KiB).",
        "- Selected required files:",
    ]
    for item in files:
        lines.append(f"  - {item['path']} (group={item['group']})")
    return "\n".join(lines)


class RunnerFileLock:
    def __init__(
        self,
        state_path: Path,
        *,
        command: str,
        stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
        recover_stale_lock: bool = False,
    ) -> None:
        self.state_path = state_path
        self.path = state_path.parent / RUNNER_LOCK_FILE
        self.command = command
        try:
            normalized_stale_lock_seconds = int(stale_lock_seconds)
        except (TypeError, ValueError):
            normalized_stale_lock_seconds = DEFAULT_STALE_LOCK_SECONDS
        self.stale_lock_seconds = max(1, normalized_stale_lock_seconds)
        self.recover_stale_lock = recover_stale_lock
        self.pid = os.getpid()
        self._stop = threading.Event()
        self._mutex = threading.Lock()
        self._thread: threading.Thread | None = None
        self.data: dict[str, Any] = {}

    def __enter__(self) -> "RunnerFileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.release()

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        now = int(time.time())
        self.data = {
            "version": 1,
            "pid": self.pid,
            "command": self.command,
            "state": str(self.state_path),
            "started_at_epoch": now,
            "last_heartbeat_epoch": now,
            "stage": "",
            "scenario": "",
            "thread_id": "",
            "status": "running",
        }
        while True:
            try:
                fd = os.open(
                    str(self.path),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                with os.fdopen(fd, "w", encoding="utf-8") as file:
                    file.write(render_simple_yaml(self.data))
                break
            except FileExistsError:
                existing = read_lock_file(self.path)
                if self.is_stale(existing):
                    diagnostics = lock_diagnostics(
                        self.state_path,
                        stale_lock_seconds=self.stale_lock_seconds,
                        lock_data=existing,
                    )
                    if not self.recover_stale_lock:
                        append_runner_event(
                            self.path.parent,
                            "lock_blocked",
                            lock_state="stale",
                            pid=existing.get("pid") or "",
                            pid_alive=diagnostics.get("pid_alive"),
                            stage=existing.get("stage") or "",
                            thread_id=existing.get("thread_id") or "",
                        )
                        raise RunnerError(
                            self.describe_existing_lock(existing, stale=True)
                            + "; rerun with --recover-stale-lock only after confirming no runner is still active"
                        )
                    if diagnostics.get("pid_alive") is not False:
                        append_runner_event(
                            self.path.parent,
                            "lock_recovery_blocked",
                            pid=existing.get("pid") or "",
                            pid_alive=diagnostics.get("pid_alive"),
                            stage=existing.get("stage") or "",
                            thread_id=existing.get("thread_id") or "",
                        )
                        raise RunnerError(
                            self.describe_existing_lock(existing, stale=True)
                            + "; stale lock recovery refused because the recorded PID is alive or could not be checked"
                        )
                    self.archive_stale_lock(existing)
                    continue
                append_runner_event(
                    self.path.parent,
                    "lock_blocked",
                    lock_state="active",
                    pid=existing.get("pid") or "",
                    pid_alive=process_alive(existing.get("pid")),
                    stage=existing.get("stage") or "",
                    thread_id=existing.get("thread_id") or "",
                )
                raise RunnerError(self.describe_existing_lock(existing, stale=False))
        append_runner_event(
            self.path.parent,
            "lock_acquired",
            pid=self.pid,
            command=self.command,
            state=str(self.state_path),
        )
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()

    def release(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        try:
            existing = read_lock_file(self.path)
        except RunnerError:
            return
        if int(existing.get("pid") or -1) == self.pid:
            self.path.unlink(missing_ok=True)
            append_runner_event(
                self.path.parent,
                "lock_released",
                pid=self.pid,
                command=self.command,
            )

    def update(self, **fields: Any) -> None:
        with self._mutex:
            self.data.update(fields)
            self.data["last_heartbeat_epoch"] = int(time.time())
            self._write()

    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(HEARTBEAT_INTERVAL_SECONDS):
            with self._mutex:
                self.data["last_heartbeat_epoch"] = int(time.time())
                self._write()

    def _write(self) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(render_simple_yaml(self.data), encoding="utf-8")
        tmp_path.replace(self.path)

    def is_stale(self, data: dict[str, Any]) -> bool:
        last_heartbeat = int(data.get("last_heartbeat_epoch") or data.get("started_at_epoch") or 0)
        return int(time.time()) - last_heartbeat > self.stale_lock_seconds

    def archive_stale_lock(self, data: dict[str, Any]) -> None:
        now = int(time.time())
        archive = self.path.with_name(f"{self.path.stem}.recovered-{now}.yaml")
        self.path.replace(archive)
        thread_id = str(data.get("thread_id") or "")
        stage = str(data.get("stage") or "")
        if stage or thread_id:
            append_session_record(
                self.state_path.parent / "codex-session-map.yaml",
                load_simple_yaml(self.state_path),
                {
                    "stage": stage or "unknown",
                    "role": "",
                    "scenario": str(data.get("scenario") or ""),
                    "thread_id": thread_id,
                    "turn_id": "",
                    "turn_status": "aborted",
                    "sandbox": "",
                    "approval_mode": "",
                    "model": "",
                    "prompt": "",
                    "input_snapshot": "",
                    "output_snapshot": "",
                    "final_response": "",
                    "started_at_epoch": data.get("started_at_epoch") or "",
                    "completed_at_epoch": now,
                    "duration_ms": "",
                    "status": "aborted",
                    "abort_reason": "stale runner lock recovered",
                    "recovered_lock": str(archive),
                    "recovered_pid": data.get("pid") or "",
                    "recovered_command": data.get("command") or "",
                    "recovered_status": data.get("status") or "",
                    "recovered_last_heartbeat_epoch": data.get("last_heartbeat_epoch") or "",
                },
            )
        append_runner_event(
            self.path.parent,
            "lock_recovered",
            pid=data.get("pid") or "",
            command=data.get("command") or "",
            stage=stage,
            thread_id=thread_id,
            recovered_lock=str(archive),
        )

    def describe_existing_lock(self, data: dict[str, Any], *, stale: bool) -> str:
        state = "stale" if stale else "active"
        return (
            f"{state} runner lock exists at {self.path}; "
            f"pid={data.get('pid')}; command={data.get('command')}; "
            f"pid_alive={process_alive(data.get('pid'))}; "
            f"stage={data.get('stage')}; thread_id={data.get('thread_id')}; "
            f"last_heartbeat_epoch={data.get('last_heartbeat_epoch')}"
        )


def render_simple_yaml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append("  -")
                    for sub_key, sub_value in item.items():
                        lines.append(f"    {sub_key}: {format_yaml_scalar(sub_value)}")
                else:
                    lines.append(f"  - {format_yaml_scalar(item)}")
        else:
            lines.append(f"{key}: {format_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def read_lock_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RunnerError(f"Runner lock does not exist: {path}")
    return load_simple_yaml(path)


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value in {"[]", "null", "None"}:
        return [] if value == "[]" else None
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Load the small YAML subset used by cycle-state.yaml.

    The project does not currently require PyYAML, so this parser supports only
    top-level scalar keys and top-level lists. That is enough for runner state
    validation and keeps the script dependency-free.
    """

    result: dict[str, Any] = {}
    current_list_key: str | None = None

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith((" ", "\t")):
            if current_list_key is None or not stripped.startswith("- "):
                raise RunnerError(f"Unsupported YAML shape at {path}:{line_no}")
            result.setdefault(current_list_key, []).append(parse_scalar(stripped[2:]))
            continue

        if stripped.startswith("- "):
            if current_list_key is None:
                raise RunnerError(f"Unsupported YAML line at {path}:{line_no}")
            result.setdefault(current_list_key, []).append(parse_scalar(stripped[2:]))
            continue

        current_list_key = None
        if ":" not in line:
            raise RunnerError(f"Unsupported YAML line at {path}:{line_no}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise RunnerError(f"Empty YAML key at {path}:{line_no}")
        if raw_value == "":
            result[key] = []
            current_list_key = key
        else:
            result[key] = parse_scalar(raw_value)

    return result


def write_simple_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(render_simple_yaml(data), encoding="utf-8")


def format_yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if not text or any(ch in text for ch in ":#[]{}\n\r\t") or text != text.strip():
        return json.dumps(text, ensure_ascii=False)
    return text


def append_runner_event(cycle_dir: Path, event: str, **fields: Any) -> None:
    cycle_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ts_epoch": int(time.time()),
        "event": event,
    }
    payload.update(fields)
    event_path = cycle_dir / RUNNER_EVENTS_FILE
    with event_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def process_alive(pid_value: Any) -> bool | None:
    try:
        pid = int(pid_value)
    except (TypeError, ValueError):
        return None
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.returncode == 0
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def lock_diagnostics(
    state_path: Path,
    *,
    stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
    lock_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lock_path = state_path.parent / RUNNER_LOCK_FILE
    if lock_data is None:
        if not lock_path.exists():
            return {"exists": False, "path": str(lock_path)}
        lock_data = read_lock_file(lock_path)
    try:
        normalized_stale_lock_seconds = max(1, int(stale_lock_seconds))
    except (TypeError, ValueError):
        normalized_stale_lock_seconds = DEFAULT_STALE_LOCK_SECONDS
    last_heartbeat = int(
        lock_data.get("last_heartbeat_epoch") or lock_data.get("started_at_epoch") or 0
    )
    age_seconds = max(0, int(time.time()) - last_heartbeat)
    is_stale = age_seconds > normalized_stale_lock_seconds
    pid_alive = process_alive(lock_data.get("pid"))
    return {
        "exists": True,
        "path": str(lock_path),
        "pid": lock_data.get("pid") or "",
        "pid_alive": pid_alive,
        "command": lock_data.get("command") or "",
        "stage": lock_data.get("stage") or "",
        "scenario": lock_data.get("scenario") or "",
        "thread_id": lock_data.get("thread_id") or "",
        "status": lock_data.get("status") or "",
        "started_at_epoch": lock_data.get("started_at_epoch") or "",
        "last_heartbeat_epoch": last_heartbeat,
        "heartbeat_age_seconds": age_seconds,
        "stale_after_seconds": normalized_stale_lock_seconds,
        "stale": is_stale,
        "safe_to_recover": is_stale and pid_alive is False,
    }


def last_runner_event(cycle_dir: Path) -> dict[str, Any] | None:
    event_path = cycle_dir / RUNNER_EVENTS_FILE
    if not event_path.exists():
        return None
    lines = [line for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"event": "invalid-json", "raw": lines[-1]}


def infer_ft_root(state_path: Path) -> Path:
    for parent in state_path.resolve().parents:
        if parent.name == "work":
            return parent.parent
    return state_path.resolve().parent


def resolve_artifact_path(path_text: str | None, ft_root: Path) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ft_root / path


def relative_or_name(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def required_state_fields() -> set[str]:
    return {
        "cycle_id",
        "ft_slug",
        "scope_slug",
        "canonical_test_cases",
        "current_stage",
        "stage_status",
        "semantic_round",
        "max_semantic_rounds",
    }


def validate_state(state: dict[str, Any], state_path: Path) -> None:
    missing = sorted(required_state_fields() - set(state))
    if missing:
        raise RunnerError(f"Missing required cycle-state fields: {', '.join(missing)}")

    status = str(state["stage_status"])
    if status not in ALLOWED_STATUSES:
        raise RunnerError(f"Unsupported stage_status: {status}")

    semantic_round = int(state.get("semantic_round") or 0)
    max_rounds = int(state.get("max_semantic_rounds") or 0)
    if max_rounds != 2:
        raise RunnerError("max_semantic_rounds must be 2 for the current contract")
    if semantic_round < 0 or semantic_round > max_rounds:
        raise RunnerError("semantic_round must be between 0 and max_semantic_rounds")

    ft_root = infer_ft_root(state_path)
    canonical = resolve_artifact_path(str(state["canonical_test_cases"]), ft_root)
    if canonical is None:
        raise RunnerError(f"Canonical test-case file does not exist: {canonical}")
    if "test-cases" not in canonical.parts:
        raise RunnerError("canonical_test_cases must point to the FT test-cases directory")
    if "versions" in canonical.parts:
        raise RunnerError("canonical_test_cases must not point to a version snapshot")
    if status not in PRE_WRITER_STATUSES and not canonical.exists():
        raise RunnerError(f"Canonical test-case file does not exist: {canonical}")

    if status not in TERMINAL_STATUSES:
        prompt_path = state.get("active_transition_prompt")
        prompt = resolve_artifact_path(str(prompt_path), ft_root) if prompt_path else None
        if prompt is None or not prompt.exists():
            raise RunnerError(f"active_transition_prompt does not exist: {prompt_path}")


def next_session_for_state(state: dict[str, Any]) -> NextSession | None:
    status = str(state["stage_status"])
    prompt_path = str(state.get("active_transition_prompt") or "")
    semantic_round = int(state.get("semantic_round") or 0)
    max_rounds = int(state.get("max_semantic_rounds") or 2)

    if status in TERMINAL_STATUSES:
        return None
    if status == "scope-ready-for-gap-review":
        return NextSession(
            stage="scope-gap-review",
            role="reviewer",
            scenario="reviewer.scope_gap_review",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status in {"scope-gap-review-passed", "scope-ready-for-writer"}:
        return NextSession(
            stage="writer-r1",
            role="writer",
            scenario="writer.session_initial_draft",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status == "writer-draft-ready":
        return NextSession(
            stage="structure-preflight-r1",
            role="reviewer",
            scenario="reviewer.structure_preflight",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status == "structure-preflight-blocked":
        return NextSession(
            stage="writer-structure-r1",
            role="writer",
            scenario="writer.remediation.style",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status == "semantic-review-ready":
        round_no = max(semantic_round, 1)
        return NextSession(
            stage=f"semantic-review-r{round_no}",
            role="reviewer",
            scenario="reviewer.semantic_traceability_test_design",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status == "semantic-revision-needed":
        if semantic_round >= max_rounds:
            raise RunnerError("semantic round cap reached; do not start writer-r3")
        return NextSession(
            stage=f"writer-r{semantic_round + 1}",
            role="writer",
            scenario="writer.session_semantic_revision",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status in {"semantic-review-passed", "format-review-ready"}:
        return NextSession(
            stage="format-review-final",
            role="reviewer",
            scenario="reviewer.structure_format_final",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status == "format-revision-needed":
        return NextSession(
            stage="writer-format-final",
            role="writer",
            scenario="writer.session_format_revision",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    if status == "final-regression-ready":
        return NextSession(
            stage="semantic-regression-final",
            role="reviewer",
            scenario="reviewer.semantic_regression",
            prompt_path=prompt_path,
            sandbox_policy="workspace_write",
        )
    raise RunnerError(f"No transition defined for status: {status}")


def copy_file_for_snapshot(source: Path, snapshot_dir: Path, ft_root: Path) -> dict[str, Any]:
    relative = relative_or_name(source, ft_root)
    destination = snapshot_dir / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    data = destination.read_bytes()
    return {
        "source": str(source),
        "snapshot_path": relative,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def collect_snapshot_files(state: dict[str, Any], state_path: Path) -> list[Path]:
    ft_root = infer_ft_root(state_path)
    files: list[Path] = [state_path]

    canonical = resolve_artifact_path(str(state["canonical_test_cases"]), ft_root)
    if canonical and canonical.exists():
        files.append(canonical)

    session_map = state_path.parent / "codex-session-map.yaml"
    if session_map.exists():
        files.append(session_map)

    runner_events = state_path.parent / RUNNER_EVENTS_FILE
    if runner_events.exists():
        files.append(runner_events)

    test_design_dir = resolve_artifact_path(str(state.get("test_design_dir") or ""), ft_root)
    if test_design_dir and test_design_dir.exists():
        files.extend(path for path in sorted(test_design_dir.rglob("*")) if path.is_file())

    outputs_dir = state_path.parent / "outputs"
    if outputs_dir.exists():
        files.extend(path for path in sorted(outputs_dir.rglob("*")) if path.is_file())

    latest_artifacts = state.get("latest_artifacts")
    if isinstance(latest_artifacts, list):
        for artifact in latest_artifacts:
            artifact_path = resolve_artifact_path(str(artifact), ft_root)
            if artifact_path and artifact_path.exists() and artifact_path.is_file():
                files.append(artifact_path)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return deduped


def snapshot_state(state_path: Path, snapshot_id: str) -> dict[str, Any]:
    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    ft_root = infer_ft_root(state_path)
    snapshot_dir = state_path.parent / "versions" / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    files = [
        copy_file_for_snapshot(path, snapshot_dir, ft_root)
        for path in collect_snapshot_files(state, state_path)
    ]
    manifest = {
        "version": 1,
        "snapshot_id": snapshot_id,
        "cycle_id": state.get("cycle_id"),
        "stage_status": state.get("stage_status"),
        "files": files,
    }
    write_simple_yaml(snapshot_dir / "snapshot-manifest.yaml", manifest)
    return manifest


def build_dry_run_payload(state: dict[str, Any], state_path: Path) -> dict[str, Any]:
    next_session = next_session_for_state(state)
    if next_session is None:
        return {
            "action": "none",
            "reason": f"No runnable next session for status {state['stage_status']}",
            "state": str(state_path),
        }

    ft_root = infer_ft_root(state_path)
    prompt = resolve_artifact_path(next_session.prompt_path, ft_root)
    instruction_context = resolve_instruction_context_for_scenario(next_session.scenario)
    return {
        "action": "start-session",
        "cycle_id": state["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "prompt_path": str(prompt),
        "sandbox_policy": next_session.sandbox_policy,
        "instruction_context": instruction_context_summary(instruction_context),
        "state": str(state_path),
    }


def enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def classify_session_status(turn_status: str | None, *, state_advanced: bool) -> str:
    if turn_status == "completed":
        return "completed"
    if state_advanced and turn_status in PROGRESS_ACCEPTED_TURN_STATUSES:
        return "completed-with-progress"
    return "failed"


def sdk_sandbox(policy: str) -> Any:
    from openai_codex import Sandbox

    if policy == "read_only":
        return Sandbox.read_only
    if policy == "workspace_write":
        return Sandbox.workspace_write
    if policy == "full_access":
        return Sandbox.full_access
    raise RunnerError(f"Unsupported SDK sandbox policy: {policy}")


def sdk_approval_mode(name: str) -> Any:
    from openai_codex import ApprovalMode

    if name == "auto_review":
        return ApprovalMode.auto_review
    if name == "deny_all":
        return ApprovalMode.deny_all
    raise RunnerError(f"Unsupported approval mode: {name}")


def append_session_record(session_map: Path, state: dict[str, Any], record: dict[str, Any]) -> None:
    session_map.parent.mkdir(parents=True, exist_ok=True)
    if session_map.exists():
        content = session_map.read_text(encoding="utf-8")
        if "sessions: []" in content:
            content = content.replace("sessions: []", "sessions:\n")
        elif "sessions:" not in content:
            content = content.rstrip() + "\nsessions:\n"
    else:
        content = (
            "version: 1\n"
            f"ft_slug: {format_yaml_scalar(state.get('ft_slug'))}\n"
            f"scope_slug: {format_yaml_scalar(state.get('scope_slug'))}\n"
            "sessions:\n"
        )

    lines = [content.rstrip("\n")]
    lines.append(f"  - stage: {format_yaml_scalar(record['stage'])}")
    for key, value in record.items():
        if key == "stage":
            continue
        lines.append(f"    {key}: {format_yaml_scalar(value)}")
    session_map.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prompt_text_for_session(state: dict[str, Any], state_path: Path, next_session: NextSession) -> str:
    ft_root = infer_ft_root(state_path)
    prompt_path = resolve_artifact_path(next_session.prompt_path, ft_root)
    if prompt_path is None or not prompt_path.exists():
        raise RunnerError(f"Prompt file does not exist: {next_session.prompt_path}")
    prompt = prompt_path.read_text(encoding="utf-8")
    instruction_context = resolve_instruction_context_for_scenario(next_session.scenario)
    return "\n".join(
        [
            "Session-based review-cycle stage.",
            f"cycle_id: {state.get('cycle_id')}",
            f"stage: {next_session.stage}",
            f"role: {next_session.role}",
            f"instruction_scenario: {next_session.scenario}",
            f"cycle_state: {state_path.resolve()}",
            f"ft_root: {ft_root.resolve()}",
            f"canonical_test_cases: {resolve_artifact_path(str(state.get('canonical_test_cases')), ft_root)}",
            "",
            "Runner state contract:",
            "- cycle-state.yaml is the source of truth for this automated chain.",
            "- Before ending the session, update cycle-state.yaml to the next lifecycle status, semantic round and active transition prompt according to session-based-review-cycle-format.md.",
            "- If the active prompt below mentions workflow-state.yaml, update it only as compatibility; do not leave cycle-state.yaml stale.",
            "- Use session-based stage_status values from cycle-state.yaml, not legacy workflow-state.yaml status names.",
            "- Do not edit codex-session-map.yaml; it is owned by the SDK runner.",
            "",
            render_instruction_context_contract(next_session.scenario, instruction_context),
            "",
            "Use the prompt below as the active transition prompt. Do not rely on prior chat history.",
            "",
            prompt,
        ]
    )


def write_session_output(cycle_dir: Path, stage: str, final_response: str | None) -> Path:
    output_dir = cycle_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{stage}-final-response.md"
    output_path.write_text(final_response or "", encoding="utf-8")
    return output_path


def write_completion_manifest(
    state_path: Path,
    *,
    state_before: dict[str, Any],
    state_after: dict[str, Any],
    next_session: NextSession,
    thread_id: str,
    turn_id: str,
    turn_status: str | None,
    session_status: str,
    state_advanced: bool,
    input_snapshot: str,
    output_snapshot: str,
    final_response: Path,
    started_at_epoch: int,
    completed_at_epoch: int,
    duration_ms: Any,
) -> Path:
    ft_root = infer_ft_root(state_path)
    output_dir = state_path.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{next_session.stage}{COMPLETION_MANIFEST_SUFFIX}"
    next_after = next_session_for_state(state_after)
    manifest = {
        "version": 1,
        "cycle_id": state_before.get("cycle_id"),
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "thread_id": thread_id,
        "turn_id": turn_id,
        "turn_status": turn_status or "",
        "session_status": session_status,
        "state_advanced": state_advanced,
        "state_before_marker": "|".join(state_progress_marker(state_before)),
        "state_after_marker": "|".join(state_progress_marker(state_after)),
        "stage_status_before": state_before.get("stage_status") or "",
        "stage_status_after": state_after.get("stage_status") or "",
        "next_stage": next_after.stage if next_after else "",
        "terminal_after": str(state_after.get("stage_status") or "") in TERMINAL_STATUSES,
        "input_snapshot": input_snapshot,
        "output_snapshot": output_snapshot,
        "final_response": relative_or_name(final_response, ft_root),
        "started_at_epoch": started_at_epoch,
        "completed_at_epoch": completed_at_epoch,
        "duration_ms": duration_ms or "",
    }
    write_simple_yaml(path, manifest)
    return path


def run_real_session(
    state: dict[str, Any],
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    runner_lock: RunnerFileLock | None = None,
) -> dict[str, Any]:
    try:
        from openai_codex import Codex
    except ImportError as exc:
        raise RunnerError("openai-codex is not installed in this Python environment") from exc

    next_session = next_session_for_state(state)
    if next_session is None:
        raise RunnerError(f"No runnable next session for status {state['stage_status']}")
    append_runner_event(
        state_path.parent,
        "session_preparing",
        cycle_id=state.get("cycle_id") or "",
        stage=next_session.stage,
        scenario=next_session.scenario,
        stage_status=state.get("stage_status") or "",
    )
    if runner_lock is not None:
        runner_lock.update(
            stage=next_session.stage,
            scenario=next_session.scenario,
            status="starting-session",
        )

    ft_root = infer_ft_root(state_path)
    run_cwd = cwd or str(Path.cwd())
    prompt = prompt_text_for_session(state, state_path, next_session)
    before_snapshot_id = f"before-{next_session.stage}"
    after_snapshot_id = f"after-{next_session.stage}"
    before_manifest = snapshot_state(state_path, before_snapshot_id)
    append_runner_event(
        state_path.parent,
        "input_snapshot_created",
        stage=next_session.stage,
        snapshot_id=before_snapshot_id,
    )

    started_at = int(time.time())
    codex = Codex()
    thread = None
    try:
        thread = codex.thread_start(
            cwd=run_cwd,
            sandbox=sdk_sandbox(next_session.sandbox_policy),
            approval_mode=sdk_approval_mode(approval_mode),
            model=model,
        )
        try:
            thread.set_name(f"{state.get('cycle_id')}:{next_session.stage}")
        except Exception:
            pass
        append_runner_event(
            state_path.parent,
            "thread_started",
            stage=next_session.stage,
            scenario=next_session.scenario,
            thread_id=thread.id,
        )
        if runner_lock is not None:
            runner_lock.update(
                stage=next_session.stage,
                scenario=next_session.scenario,
                thread_id=thread.id,
                status="running-session",
            )
        append_session_record(
            state_path.parent / "codex-session-map.yaml",
            state,
            {
                "stage": next_session.stage,
                "role": next_session.role,
                "scenario": next_session.scenario,
                "thread_id": thread.id,
                "turn_id": "",
                "turn_status": "",
                "sandbox": next_session.sandbox_policy,
                "approval_mode": approval_mode,
                "model": model or "",
                "prompt": next_session.prompt_path,
                "input_snapshot": relative_or_name(
                    state_path.parent / "versions" / before_snapshot_id, ft_root
                ),
                "output_snapshot": "",
                "final_response": "",
                "started_at_epoch": started_at,
                "completed_at_epoch": "",
                "duration_ms": "",
                "status": "started",
            },
        )
        try:
            append_runner_event(
                state_path.parent,
                "turn_started",
                stage=next_session.stage,
                thread_id=thread.id,
            )
            turn = thread.run(
                prompt,
                cwd=run_cwd,
                sandbox=sdk_sandbox(next_session.sandbox_policy),
                approval_mode=sdk_approval_mode(approval_mode),
                model=model,
            )
        except Exception as exc:
            append_runner_event(
                state_path.parent,
                "turn_exception",
                stage=next_session.stage,
                thread_id=thread.id,
                error=type(exc).__name__,
            )
            append_session_record(
                state_path.parent / "codex-session-map.yaml",
                state,
                {
                    "stage": next_session.stage,
                    "role": next_session.role,
                    "scenario": next_session.scenario,
                    "thread_id": thread.id,
                    "turn_id": "",
                    "turn_status": "exception",
                    "sandbox": next_session.sandbox_policy,
                    "approval_mode": approval_mode,
                    "model": model or "",
                    "prompt": next_session.prompt_path,
                    "input_snapshot": relative_or_name(
                        state_path.parent / "versions" / before_snapshot_id, ft_root
                    ),
                    "output_snapshot": "",
                    "final_response": "",
                    "started_at_epoch": started_at,
                    "completed_at_epoch": int(time.time()),
                    "duration_ms": "",
                    "status": "failed",
                    "error": type(exc).__name__,
                },
            )
            raise
    finally:
        codex.close()

    output_path = write_session_output(state_path.parent, next_session.stage, turn.final_response)
    updated_state = load_simple_yaml(state_path)
    validate_state(updated_state, state_path)
    state_advanced = state_progress_marker(updated_state) != state_progress_marker(state)
    turn_status = enum_value(turn.status)
    session_status = classify_session_status(turn_status, state_advanced=state_advanced)
    completed_at = int(time.time())
    input_snapshot = relative_or_name(
        state_path.parent / "versions" / before_snapshot_id, ft_root
    )
    output_snapshot = relative_or_name(
        state_path.parent / "versions" / after_snapshot_id, ft_root
    )
    append_runner_event(
        state_path.parent,
        "turn_finished",
        stage=next_session.stage,
        thread_id=thread.id,
        turn_id=turn.id,
        turn_status=turn_status or "",
        session_status=session_status,
        state_advanced=state_advanced,
    )
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state,
        state_after=updated_state,
        next_session=next_session,
        thread_id=thread.id,
        turn_id=turn.id,
        turn_status=turn_status,
        session_status=session_status,
        state_advanced=state_advanced,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=output_path,
        started_at_epoch=started_at,
        completed_at_epoch=completed_at,
        duration_ms=turn.duration_ms,
    )
    record = {
        "role": next_session.role,
        "scenario": next_session.scenario,
        "thread_id": thread.id,
        "turn_id": turn.id,
        "turn_status": turn_status,
        "sandbox": next_session.sandbox_policy,
        "approval_mode": approval_mode,
        "model": model or "",
        "prompt": next_session.prompt_path,
        "input_snapshot": input_snapshot,
        "output_snapshot": output_snapshot,
        "final_response": relative_or_name(output_path, ft_root),
        "completion_manifest": relative_or_name(completion_manifest_path, ft_root),
        "started_at_epoch": started_at,
        "completed_at_epoch": completed_at,
        "duration_ms": turn.duration_ms or "",
        "state_advanced": state_advanced,
        "status": session_status,
    }
    append_session_record(state_path.parent / "codex-session-map.yaml", state, {"stage": next_session.stage, **record})
    append_runner_event(
        state_path.parent,
        "stage_completed",
        stage=next_session.stage,
        thread_id=thread.id,
        turn_id=turn.id,
        session_status=session_status,
        output_snapshot=after_snapshot_id,
        completion_manifest=relative_or_name(completion_manifest_path, ft_root),
    )
    after_manifest = snapshot_state(state_path, after_snapshot_id)

    return {
        "action": "completed-session",
        "cycle_id": state["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "thread_id": thread.id,
        "turn_id": turn.id,
        "turn_status": turn_status,
        "session_status": session_status,
        "state_advanced": state_advanced,
        "final_response": str(output_path),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_manifest["snapshot_id"],
        "output_snapshot": after_manifest["snapshot_id"],
    }


def state_progress_marker(state: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(state.get(key) or "") for key in PROGRESS_STATE_KEYS)


def run_until_terminal(
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    max_sessions: int,
    runner_lock: RunnerFileLock | None = None,
) -> dict[str, Any]:
    if max_sessions < 1:
        raise RunnerError("max_sessions must be at least 1")

    completed_sessions: list[dict[str, Any]] = []
    for _ in range(max_sessions):
        state = load_simple_yaml(state_path)
        validate_state(state, state_path)
        status = str(state["stage_status"])
        next_session = next_session_for_state(state)
        if next_session is None:
            return {
                "action": "completed-chain" if status in TERMINAL_STATUSES else "stopped-chain",
                "state": str(state_path),
                "final_status": status,
                "terminal": status in TERMINAL_STATUSES,
                "sessions_started": len(completed_sessions),
                "sessions": completed_sessions,
            }

        before_marker = state_progress_marker(state)
        payload = run_real_session(
            state,
            state_path,
            cwd=cwd,
            approval_mode=approval_mode,
            model=model,
            runner_lock=runner_lock,
        )
        completed_sessions.append(payload)
        updated_state = load_simple_yaml(state_path)
        validate_state(updated_state, state_path)
        state_advanced = state_progress_marker(updated_state) != before_marker
        if not state_advanced:
            raise RunnerError(
                f"cycle-state.yaml did not advance after {payload.get('stage')}; stopping to avoid repeating the same stage"
            )
        session_status = payload.get("session_status")
        if session_status is None:
            session_status = classify_session_status(
                str(payload.get("turn_status") or ""),
                state_advanced=state_advanced,
            )
        if session_status not in CHAIN_ACCEPTED_SESSION_STATUSES:
            raise RunnerError(
                f"Stage {payload.get('stage')} finished with turn_status={payload.get('turn_status')}; stopping chain"
            )

    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    status = str(state.get("stage_status") or "")
    next_session = next_session_for_state(state)
    if status in TERMINAL_STATUSES or next_session is None:
        return {
            "action": "completed-chain" if status in TERMINAL_STATUSES else "stopped-chain",
            "state": str(state_path),
            "final_status": status,
            "terminal": status in TERMINAL_STATUSES,
            "sessions_started": len(completed_sessions),
            "sessions": completed_sessions,
        }
    raise RunnerError(
        f"max_sessions={max_sessions} reached before terminal status; current stage_status={status}"
    )


def next_session_summary(state: dict[str, Any]) -> dict[str, Any] | None:
    try:
        next_session = next_session_for_state(state)
    except RunnerError as exc:
        return {"error": str(exc)}
    if next_session is None:
        return None
    return {
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "prompt_path": next_session.prompt_path,
        "sandbox_policy": next_session.sandbox_policy,
    }


def build_doctor_payload(
    state_path: Path,
    *,
    stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
) -> dict[str, Any]:
    cycle_dir = state_path.parent
    ft_root = infer_ft_root(state_path)
    payload: dict[str, Any] = {
        "action": "doctor",
        "state": str(state_path),
        "cycle_dir": str(cycle_dir),
    }
    state: dict[str, Any] | None = None
    try:
        state = load_simple_yaml(state_path)
        validate_state(state, state_path)
        payload.update(
            {
                "state_valid": True,
                "cycle_id": state.get("cycle_id") or "",
                "ft_slug": state.get("ft_slug") or "",
                "scope_slug": state.get("scope_slug") or "",
                "current_stage": state.get("current_stage") or "",
                "stage_status": state.get("stage_status") or "",
                "semantic_round": state.get("semantic_round") or "",
                "next": next_session_summary(state),
            }
        )
    except RunnerError as exc:
        payload.update(
            {
                "state_valid": False,
                "state_error": str(exc),
                "next": None,
            }
        )

    lock = lock_diagnostics(state_path, stale_lock_seconds=stale_lock_seconds)
    payload["lock"] = lock

    event_path = cycle_dir / RUNNER_EVENTS_FILE
    payload["events"] = {
        "path": str(event_path),
        "exists": event_path.exists(),
        "last_event": last_runner_event(cycle_dir),
    }

    output_dir = cycle_dir / "outputs"
    manifests = sorted(output_dir.glob(f"*{COMPLETION_MANIFEST_SUFFIX}")) if output_dir.exists() else []
    payload["completion_manifests"] = [relative_or_name(path, ft_root) for path in manifests]

    status = str(payload.get("stage_status") or "")
    if not payload["state_valid"]:
        recommendation = "fix-state-before-running"
    elif lock.get("exists"):
        if lock.get("safe_to_recover"):
            recommendation = "resume-with---recover-stale-lock"
        elif lock.get("stale"):
            recommendation = "inspect-lock-pid-before-recovery"
        else:
            recommendation = "wait-for-active-runner-or-investigate-lock"
    elif status in TERMINAL_STATUSES:
        recommendation = "no-action-terminal-status"
    elif payload.get("next") is None:
        recommendation = "no-runnable-next-stage"
    elif isinstance(payload.get("next"), dict) and payload["next"].get("error"):
        recommendation = "fix-transition-before-running"
    else:
        recommendation = "run-next-stage"
    payload["recommendation"] = recommendation
    return payload


def ensure_resume_lock_is_safe(
    state_path: Path,
    *,
    stale_lock_seconds: int,
    recover_stale_lock: bool,
) -> None:
    diagnostics = lock_diagnostics(state_path, stale_lock_seconds=stale_lock_seconds)
    if not diagnostics.get("exists"):
        return
    if not diagnostics.get("stale"):
        raise RunnerError(
            "active runner lock exists; run doctor and do not resume until the active run finishes or the lock becomes stale"
        )
    if diagnostics.get("pid_alive") is not False:
        raise RunnerError(
            "stale runner lock exists, but the recorded PID is alive or could not be checked; inspect the process before recovery"
        )
    if not recover_stale_lock:
        raise RunnerError(
            "stale runner lock with dead PID exists; rerun resume with --recover-stale-lock to archive it deliberately"
        )


def cmd_validate(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    payload = {
        "valid": True,
        "state": str(state_path),
        "next": build_dry_run_payload(state, state_path),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    manifest = snapshot_state(Path(args.state), args.snapshot_id)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    payload = build_doctor_payload(
        Path(args.state),
        stale_lock_seconds=args.stale_lock_seconds,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_start_or_continue(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    if args.dry_run:
        print(json.dumps(build_dry_run_payload(state, state_path), ensure_ascii=False, indent=2))
        return 0
    with RunnerFileLock(
        state_path,
        command=args.command,
        stale_lock_seconds=args.stale_lock_seconds,
        recover_stale_lock=args.recover_stale_lock,
    ) as runner_lock:
        payload = run_real_session(
            state,
            state_path,
            cwd=args.cwd,
            approval_mode=args.approval_mode,
            model=args.model,
            runner_lock=runner_lock,
        )
    if not payload.get("state_advanced"):
        raise RunnerError(
            f"cycle-state.yaml did not advance after {payload.get('stage')}; stopping to avoid repeating the same stage"
        )
    if payload.get("session_status") not in CHAIN_ACCEPTED_SESSION_STATUSES:
        raise RunnerError(
            f"Stage {payload.get('stage')} finished with turn_status={payload.get('turn_status')}; stopping chain"
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_run_until_terminal(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    if args.dry_run:
        payload = {
            "action": "dry-run-chain",
            "state": str(state_path),
            "max_sessions": args.max_sessions,
            "next": build_dry_run_payload(state, state_path),
            "note": (
                "Dry-run validates only the first runnable stage because later stages "
                "depend on cycle-state.yaml updates made by completed sessions."
            ),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    with RunnerFileLock(
        state_path,
        command=args.command,
        stale_lock_seconds=args.stale_lock_seconds,
        recover_stale_lock=args.recover_stale_lock,
    ) as runner_lock:
        payload = run_until_terminal(
            state_path,
            cwd=args.cwd,
            approval_mode=args.approval_mode,
            model=args.model,
            max_sessions=args.max_sessions,
            runner_lock=runner_lock,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    if args.dry_run:
        payload = build_doctor_payload(
            state_path,
            stale_lock_seconds=args.stale_lock_seconds,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    ensure_resume_lock_is_safe(
        state_path,
        stale_lock_seconds=args.stale_lock_seconds,
        recover_stale_lock=args.recover_stale_lock,
    )
    with RunnerFileLock(
        state_path,
        command=args.command,
        stale_lock_seconds=args.stale_lock_seconds,
        recover_stale_lock=args.recover_stale_lock,
    ) as runner_lock:
        payload = run_until_terminal(
            state_path,
            cwd=args.cwd,
            approval_mode=args.approval_mode,
            model=args.model,
            max_sessions=args.max_sessions,
            runner_lock=runner_lock,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the session-based Codex review cycle")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate cycle-state.yaml")
    validate.add_argument("--state", required=True, help="Path to cycle-state.yaml")
    validate.set_defaults(func=cmd_validate)

    snapshot = subparsers.add_parser("snapshot", help="Snapshot current cycle artifacts")
    snapshot.add_argument("--state", required=True, help="Path to cycle-state.yaml")
    snapshot.add_argument("--snapshot-id", required=True, help="Snapshot directory id")
    snapshot.set_defaults(func=cmd_snapshot)

    doctor = subparsers.add_parser("doctor", help="Inspect runner state, lock and completion evidence")
    doctor.add_argument("--state", required=True, help="Path to cycle-state.yaml")
    doctor.add_argument(
        "--stale-lock-seconds",
        type=int,
        default=DEFAULT_STALE_LOCK_SECONDS,
        help=f"Seconds without heartbeat before a runner lock is considered stale. Default: {DEFAULT_STALE_LOCK_SECONDS}.",
    )
    doctor.set_defaults(func=cmd_doctor)

    for command in ("start", "continue"):
        sub = subparsers.add_parser(command, help=f"{command} the next Codex session")
        sub.add_argument("--state", required=True, help="Path to cycle-state.yaml")
        sub.add_argument("--dry-run", action="store_true", help="Print the next session only")
        sub.add_argument("--cwd", help="Working directory for the Codex session")
        sub.add_argument("--model", help="Optional Codex model override")
        sub.add_argument(
            "--approval-mode",
            choices=("auto_review", "deny_all"),
            default="auto_review",
            help="Codex SDK approval mode. Default: auto_review.",
        )
        sub.add_argument(
            "--stale-lock-seconds",
            type=int,
            default=DEFAULT_STALE_LOCK_SECONDS,
            help=f"Seconds without heartbeat before a runner lock is considered stale. Default: {DEFAULT_STALE_LOCK_SECONDS}.",
        )
        sub.add_argument(
            "--recover-stale-lock",
            action="store_true",
            help="Archive a stale runner lock and append an aborted session-map record before starting.",
        )
        sub.set_defaults(func=cmd_start_or_continue)

    run_all = subparsers.add_parser(
        "run-until-terminal",
        help="Run Codex sessions until signed-off, round-cap-reached, blocked-input or a non-runnable status",
    )
    run_all.add_argument("--state", required=True, help="Path to cycle-state.yaml")
    run_all.add_argument("--dry-run", action="store_true", help="Validate and print the first session only")
    run_all.add_argument("--cwd", help="Working directory for the Codex sessions")
    run_all.add_argument("--model", help="Optional Codex model override")
    run_all.add_argument(
        "--approval-mode",
        choices=("auto_review", "deny_all"),
        default="auto_review",
        help="Codex SDK approval mode. Default: auto_review.",
    )
    run_all.add_argument(
        "--max-sessions",
        type=int,
        default=12,
        help="Safety limit for automatically started sessions. Default: 12.",
    )
    run_all.add_argument(
        "--stale-lock-seconds",
        type=int,
        default=DEFAULT_STALE_LOCK_SECONDS,
        help=f"Seconds without heartbeat before a runner lock is considered stale. Default: {DEFAULT_STALE_LOCK_SECONDS}.",
    )
    run_all.add_argument(
        "--recover-stale-lock",
        action="store_true",
        help="Archive a stale runner lock and append an aborted session-map record before starting.",
    )
    run_all.set_defaults(func=cmd_run_until_terminal)

    resume = subparsers.add_parser(
        "resume",
        help="Resume the chain after diagnostics; stale lock recovery requires an explicit flag and dead PID",
    )
    resume.add_argument("--state", required=True, help="Path to cycle-state.yaml")
    resume.add_argument("--dry-run", action="store_true", help="Print doctor diagnostics and do not start a session")
    resume.add_argument("--cwd", help="Working directory for the Codex sessions")
    resume.add_argument("--model", help="Optional Codex model override")
    resume.add_argument(
        "--approval-mode",
        choices=("auto_review", "deny_all"),
        default="auto_review",
        help="Codex SDK approval mode. Default: auto_review.",
    )
    resume.add_argument(
        "--max-sessions",
        type=int,
        default=12,
        help="Safety limit for automatically started sessions. Default: 12.",
    )
    resume.add_argument(
        "--stale-lock-seconds",
        type=int,
        default=DEFAULT_STALE_LOCK_SECONDS,
        help=f"Seconds without heartbeat before a runner lock is considered stale. Default: {DEFAULT_STALE_LOCK_SECONDS}.",
    )
    resume.add_argument(
        "--recover-stale-lock",
        action="store_true",
        help="Archive a stale runner lock only when doctor can confirm the recorded PID is dead.",
    )
    resume.set_defaults(func=cmd_resume)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except RunnerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
