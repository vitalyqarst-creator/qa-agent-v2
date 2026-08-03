from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


SCHEMA_VERSION = 1
WORK_STATES = frozenset(
    {
        "pending",
        "running",
        "completed",
        "deferred-transient",
        "blocked-scope",
        "failed-infrastructure",
    }
)
RETRYABLE_STATES = frozenset({"pending", "deferred-transient"})
RESULT_CLASSIFICATIONS = frozenset(
    {
        "completed",
        "transient",
        "scope-blocker",
        "infrastructure",
        "global-source-corruption",
        "global-repository-defect",
    }
)
TERMINAL_JOB_STATES = frozenset(
    {"completed", "blocked-scope", "failed-infrastructure"}
)
_JOB_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}")


class ControllerError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ControllerError(f"invalid UTC timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ControllerError(f"timestamp has no timezone: {value}")
    return parsed.astimezone(timezone.utc)


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ControllerError(f"cannot read overnight state {path}: {exc}") from exc
    if isinstance(payload, dict) and payload.get("schema_version") == SCHEMA_VERSION:
        queue = payload.get("queue")
        if isinstance(queue, list):
            for job in queue:
                if isinstance(job, dict):
                    job.setdefault("timeout_seconds", None)
                    job.setdefault("timeout_classification", "infrastructure")
                    job.setdefault("retry_exhausted", False)
    _validate_state(payload, state_path=path)
    return payload


def _validate_state(payload: Any, *, state_path: Path) -> None:
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ControllerError("unsupported overnight-state schema")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ControllerError("overnight-state run_id must be non-empty")
    if not isinstance(payload.get("goal"), str) or not payload["goal"].strip():
        raise ControllerError("overnight-state goal must be non-empty")
    queue = payload.get("queue")
    if not isinstance(queue, list):
        raise ControllerError("overnight-state queue must be an array")
    seen: set[str] = set()
    for job in queue:
        _validate_job(job)
        job_id = str(job["job_id"])
        if job_id in seen:
            raise ControllerError(f"duplicate overnight job id: {job_id}")
        seen.add(job_id)
    for job in queue:
        unknown = set(job["depends_on"]) - seen
        if unknown:
            raise ControllerError(
                f"job {job['job_id']} has unknown dependencies: {sorted(unknown)}"
            )
    current = payload.get("current_work")
    if current is not None and current not in seen:
        raise ControllerError("overnight-state current_work does not identify a job")
    if not isinstance(payload.get("actions"), list):
        raise ControllerError("overnight-state actions must be an array")
    expected_root = state_path.resolve().parent
    recorded_root = payload.get("run_dir")
    if not isinstance(recorded_root, str) or Path(recorded_root).resolve() != expected_root:
        raise ControllerError("overnight-state run_dir does not match its directory")


def _validate_job(job: Any) -> None:
    if not isinstance(job, dict):
        raise ControllerError("overnight queue items must be objects")
    job_id = job.get("job_id")
    if not isinstance(job_id, str) or _JOB_ID.fullmatch(job_id) is None:
        raise ControllerError(f"invalid overnight job id: {job_id!r}")
    state = job.get("state")
    if state not in WORK_STATES:
        raise ControllerError(f"invalid state for {job_id}: {state!r}")
    command = job.get("command")
    if not (
        isinstance(command, list)
        and command
        and all(isinstance(item, str) and item for item in command)
    ):
        raise ControllerError(f"job {job_id} command must be a non-empty string array")
    depends_on = job.get("depends_on")
    if not isinstance(depends_on, list) or not all(
        isinstance(item, str) and item for item in depends_on
    ):
        raise ControllerError(f"job {job_id} depends_on must be a string array")
    max_attempts = job.get("max_attempts")
    if type(max_attempts) is not int or max_attempts < 1:
        raise ControllerError(f"job {job_id} max_attempts must be positive")
    backoff = job.get("retry_backoff_seconds")
    if type(backoff) is not int or backoff < 0:
        raise ControllerError(f"job {job_id} retry_backoff_seconds must be non-negative")
    timeout_seconds = job.get("timeout_seconds")
    if timeout_seconds is not None and (
        type(timeout_seconds) is not int or timeout_seconds < 1
    ):
        raise ControllerError(f"job {job_id} timeout_seconds must be positive or null")
    if job.get("timeout_classification") not in RESULT_CLASSIFICATIONS - {"completed"}:
        raise ControllerError(f"job {job_id} has invalid timeout_classification")
    if not isinstance(job.get("attempts"), list):
        raise ControllerError(f"job {job_id} attempts must be an array")
    policy = job.get("failure_policy")
    if not isinstance(policy, dict):
        raise ControllerError(f"job {job_id} failure_policy must be an object")
    default = policy.get("default")
    if default not in RESULT_CLASSIFICATIONS - {"completed"}:
        raise ControllerError(f"job {job_id} has invalid default failure classification")


def _normalized_job(raw: Mapping[str, Any], *, repo_root: Path) -> dict[str, Any]:
    job_id = raw.get("job_id")
    if not isinstance(job_id, str) or _JOB_ID.fullmatch(job_id) is None:
        raise ControllerError(f"invalid overnight job id: {job_id!r}")
    command = raw.get("command")
    if not (
        isinstance(command, list)
        and command
        and all(isinstance(item, str) and item for item in command)
    ):
        raise ControllerError(f"job {job_id} command must be a non-empty string array")
    cwd_raw = raw.get("cwd", ".")
    if not isinstance(cwd_raw, str) or not cwd_raw:
        raise ControllerError(f"job {job_id} cwd must be text")
    cwd = (repo_root / cwd_raw).resolve() if not Path(cwd_raw).is_absolute() else Path(cwd_raw).resolve()
    try:
        cwd.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ControllerError(f"job {job_id} cwd escapes repository root") from exc
    failure_policy = dict(raw.get("failure_policy") or {})
    default_failure = failure_policy.get("default", "infrastructure")
    if default_failure not in RESULT_CLASSIFICATIONS - {"completed"}:
        raise ControllerError(f"job {job_id} has invalid default failure classification")
    exit_codes = failure_policy.get("exit_codes", {})
    if not isinstance(exit_codes, dict):
        raise ControllerError(f"job {job_id} failure_policy.exit_codes must be an object")
    normalized_exit_codes: dict[str, str] = {}
    for raw_code, classification in exit_codes.items():
        try:
            code = str(int(raw_code))
        except (TypeError, ValueError) as exc:
            raise ControllerError(f"job {job_id} has invalid failure exit code") from exc
        if classification not in RESULT_CLASSIFICATIONS - {"completed"}:
            raise ControllerError(f"job {job_id} has invalid exit-code classification")
        normalized_exit_codes[code] = str(classification)
    max_attempts = raw.get("max_attempts", 1)
    retry_backoff_seconds = raw.get("retry_backoff_seconds", 0)
    if type(max_attempts) is not int or max_attempts < 1:
        raise ControllerError(f"job {job_id} max_attempts must be positive")
    if type(retry_backoff_seconds) is not int or retry_backoff_seconds < 0:
        raise ControllerError(f"job {job_id} retry_backoff_seconds must be non-negative")
    timeout_seconds = raw.get("timeout_seconds")
    if timeout_seconds is not None and (
        type(timeout_seconds) is not int or timeout_seconds < 1
    ):
        raise ControllerError(f"job {job_id} timeout_seconds must be positive or null")
    timeout_classification = raw.get("timeout_classification", "infrastructure")
    if timeout_classification not in RESULT_CLASSIFICATIONS - {"completed"}:
        raise ControllerError(f"job {job_id} has invalid timeout_classification")
    result_file = raw.get("result_file", "attempt-result.json")
    if not isinstance(result_file, str) or Path(result_file).is_absolute() or ".." in Path(result_file).parts:
        raise ControllerError(f"job {job_id} result_file must stay inside attempt_dir")
    depends_on = raw.get("depends_on", [])
    if not isinstance(depends_on, list) or not all(isinstance(item, str) for item in depends_on):
        raise ControllerError(f"job {job_id} depends_on must be a string array")
    return {
        "job_id": job_id,
        "title": str(raw.get("title") or job_id),
        "scope": str(raw.get("scope") or "repository"),
        "kind": str(raw.get("kind") or "local"),
        "state": "pending",
        "command": list(command),
        "cwd": str(cwd),
        "depends_on": list(depends_on),
        "max_attempts": max_attempts,
        "retry_backoff_seconds": retry_backoff_seconds,
        "timeout_seconds": timeout_seconds,
        "timeout_classification": timeout_classification,
        "next_eligible_at": None,
        "retry_exhausted": False,
        "failure_policy": {
            "default": default_failure,
            "exit_codes": normalized_exit_codes,
        },
        "result_file": result_file,
        "attempts": [],
        "result_links": [],
        "last_error": None,
        "continuation_command": None,
    }


def initialize_run(
    *,
    run_dir: Path,
    run_id: str,
    goal: str,
    jobs: Sequence[Mapping[str, Any]],
    repo_root: Path,
    source_guard_paths: Iterable[Path] = (),
) -> Path:
    if not run_id.strip() or any(character in run_id for character in "\\/:"):
        raise ControllerError("run_id must be non-empty and path-safe")
    if not goal.strip():
        raise ControllerError("goal must be non-empty")
    resolved_run_dir = run_dir.resolve()
    if resolved_run_dir.exists() and any(resolved_run_dir.iterdir()):
        raise ControllerError(f"overnight run directory is not empty: {resolved_run_dir}")
    resolved_run_dir.mkdir(parents=True, exist_ok=True)
    normalized_jobs = [_normalized_job(job, repo_root=repo_root) for job in jobs]
    seen = {job["job_id"] for job in normalized_jobs}
    if len(seen) != len(normalized_jobs):
        raise ControllerError("overnight plan contains duplicate job ids")
    for job in normalized_jobs:
        unknown = set(job["depends_on"]) - seen
        if unknown:
            raise ControllerError(
                f"job {job['job_id']} has unknown dependencies: {sorted(unknown)}"
            )
    dependency_map = {
        str(job["job_id"]): tuple(str(item) for item in job["depends_on"])
        for job in normalized_jobs
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(job_id: str) -> None:
        if job_id in visiting:
            raise ControllerError(f"overnight plan has a dependency cycle at {job_id}")
        if job_id in visited:
            return
        visiting.add(job_id)
        for dependency in dependency_map[job_id]:
            visit(dependency)
        visiting.remove(job_id)
        visited.add(job_id)

    for job_id in dependency_map:
        visit(job_id)
    guard: list[dict[str, Any]] = []
    for raw_path in source_guard_paths:
        path = raw_path.resolve()
        if not path.is_file():
            raise ControllerError(f"source guard path is not a file: {path}")
        guard.append({"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    state_path = resolved_run_dir / "overnight-state.yaml"
    created_at = utc_now()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "run_dir": str(resolved_run_dir),
        "repo_root": str(repo_root.resolve()),
        "goal": goal,
        "overall_status": "pending",
        "created_at": created_at,
        "updated_at": created_at,
        "queue": normalized_jobs,
        "current_work": None,
        "completed_work": [],
        "deferred_transient": [],
        "scope_blockers": [],
        "failed_infrastructure": [],
        "global_blocker": None,
        "continuation_commands": [],
        "actions": [],
        "source_guard": guard,
        "last_confirmed_safe_state": None,
    }
    _append_action(payload, action="run-initialized", details={"job_count": len(jobs)})
    _refresh_indexes(payload, state_path=state_path)
    _record_safe_state(payload)
    _write_json_atomic(state_path, payload)
    return state_path


def _append_action(
    payload: dict[str, Any],
    *,
    action: str,
    job_id: str | None = None,
    attempt_id: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    payload["actions"].append(
        {
            "sequence": len(payload["actions"]) + 1,
            "at": utc_now(),
            "action": action,
            "job_id": job_id,
            "attempt_id": attempt_id,
            "details": dict(details or {}),
        }
    )
    payload["updated_at"] = payload["actions"][-1]["at"]


def _record_safe_state(payload: dict[str, Any]) -> None:
    payload["last_confirmed_safe_state"] = {
        "at": utc_now(),
        "action_sequence": len(payload["actions"]),
        "current_work": payload.get("current_work"),
        "job_states": {
            job["job_id"]: job["state"] for job in payload.get("queue", [])
        },
        "completed_attempts": sum(
            attempt.get("status") == "completed"
            for job in payload.get("queue", [])
            for attempt in job.get("attempts", [])
        ),
    }


def _continuation_command(state_path: Path, *, job_id: str | None = None) -> str:
    command = f'"{sys.executable}" scripts/run_overnight_controller.py run --state "{state_path.resolve()}"'
    if job_id:
        return command + f' --only-job "{job_id}"'
    return command


def _refresh_indexes(payload: dict[str, Any], *, state_path: Path) -> None:
    queue = payload["queue"]
    payload["completed_work"] = [job["job_id"] for job in queue if job["state"] == "completed"]
    payload["deferred_transient"] = [
        {
            "job_id": job["job_id"],
            "next_eligible_at": job.get("next_eligible_at"),
            "attempt_count": len(job["attempts"]),
            "retry_exhausted": bool(job.get("retry_exhausted")),
            "last_error": job.get("last_error"),
        }
        for job in queue
        if job["state"] == "deferred-transient"
    ]
    payload["scope_blockers"] = [
        {"job_id": job["job_id"], "scope": job["scope"], "reason": job.get("last_error")}
        for job in queue
        if job["state"] == "blocked-scope"
    ]
    payload["failed_infrastructure"] = [
        {"job_id": job["job_id"], "reason": job.get("last_error")}
        for job in queue
        if job["state"] == "failed-infrastructure"
    ]
    by_id = {job["job_id"]: job for job in queue}
    executable = [
        job
        for job in queue
        if job["state"] in RETRYABLE_STATES
        and all(by_id[item]["state"] == "completed" for item in job["depends_on"])
        and len(job["attempts"]) < job["max_attempts"]
    ]
    commands: list[str] = []
    if executable or any(job["state"] == "running" for job in queue):
        commands.append(_continuation_command(state_path))
    for job in queue:
        if job["state"] in {"blocked-scope", "failed-infrastructure"} or (
            job["state"] == "deferred-transient" and job.get("retry_exhausted")
        ):
            commands.append(
                f'"{sys.executable}" scripts/run_overnight_controller.py retry '
                f'--state "{state_path.resolve()}" --job "{job["job_id"]}"'
            )
    payload["continuation_commands"] = commands
    for job in queue:
        if job["state"] == "deferred-transient" and job.get("retry_exhausted"):
            job["continuation_command"] = (
                f'"{sys.executable}" scripts/run_overnight_controller.py retry '
                f'--state "{state_path.resolve()}" --job "{job["job_id"]}"'
            )
        else:
            job["continuation_command"] = (
                _continuation_command(state_path, job_id=job["job_id"])
                if job["state"] in RETRYABLE_STATES
                else None
            )
    if payload.get("global_blocker"):
        payload["overall_status"] = "blocked-global"
    elif any(job["state"] == "running" for job in queue):
        payload["overall_status"] = "running"
    elif queue and all(job["state"] == "completed" for job in queue):
        payload["overall_status"] = "completed"
    elif executable:
        payload["overall_status"] = "work-remains"
    elif any(
        job["state"] == "deferred-transient" and job.get("retry_exhausted")
        for job in queue
    ):
        payload["overall_status"] = "completed-with-blockers"
    elif any(job["state"] in TERMINAL_JOB_STATES - {"completed"} for job in queue):
        payload["overall_status"] = "completed-with-blockers"
    else:
        payload["overall_status"] = "pending"


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> dict[str, Any]:
    details: dict[str, Any] = {"pid": process.pid, "platform": os.name}
    if process.poll() is not None:
        details["already_exited"] = True
        return details
    if os.name == "nt":
        try:
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
            )
            details["taskkill_return_code"] = completed.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            details["taskkill_error"] = f"{type(exc).__name__}: {exc}"
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except OSError as exc:
            details["terminate_error"] = f"{type(exc).__name__}: {exc}"
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            details["escalated_to_kill"] = True
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
        details["direct_kill_fallback"] = True
    details["return_code"] = process.returncode
    return details


@contextmanager
def _controller_lock(run_dir: Path) -> Iterator[None]:
    path = run_dir / ".controller.lock"
    token = uuid.uuid4().hex
    payload = {"pid": os.getpid(), "token": token, "created_at": utc_now()}
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
                pid = int(existing.get("pid", -1))
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise ControllerError(f"overnight controller lock is ambiguous: {path}") from exc
            if _process_exists(pid):
                raise ControllerError(f"overnight controller is already running with pid {pid}")
            stale = path.with_name(f".controller.lock.stale.{uuid.uuid4().hex}")
            try:
                os.replace(path, stale)
            except OSError as exc:
                raise ControllerError("cannot quarantine stale controller lock") from exc
            continue
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            break
    try:
        yield
    finally:
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing.get("token") == token and existing.get("pid") == os.getpid():
                path.unlink()
        except (OSError, json.JSONDecodeError):
            pass


class OvernightController:
    def __init__(self, state_path: Path):
        self.state_path = state_path.resolve()
        self.run_dir = self.state_path.parent
        self.state = load_state(self.state_path)

    def _save(self, *, safe: bool = True) -> None:
        _refresh_indexes(self.state, state_path=self.state_path)
        if safe:
            _record_safe_state(self.state)
        _write_json_atomic(self.state_path, self.state)

    def _job(self, job_id: str) -> dict[str, Any]:
        matches = [job for job in self.state["queue"] if job["job_id"] == job_id]
        if len(matches) != 1:
            raise ControllerError(f"unknown overnight job: {job_id}")
        return matches[0]

    def verify_source_guard(self) -> None:
        mismatches: list[dict[str, Any]] = []
        for item in self.state.get("source_guard", []):
            path = Path(item["path"])
            actual = _sha256(path) if path.is_file() else None
            if actual != item["sha256"]:
                mismatches.append(
                    {"path": str(path), "expected_sha256": item["sha256"], "actual_sha256": actual}
                )
        if mismatches:
            self.state["global_blocker"] = {
                "classification": "global-source-corruption",
                "at": utc_now(),
                "mismatches": mismatches,
            }
            _append_action(
                self.state,
                action="global-source-guard-failed",
                details={"mismatches": mismatches},
            )
            self._save()
            raise ControllerError("guarded source files changed during overnight run")

    def verify_attempt_integrity(self) -> None:
        mismatches: list[dict[str, Any]] = []
        for job in self.state["queue"]:
            for attempt in job["attempts"]:
                expected = attempt.get("artifact_sha256")
                if not isinstance(expected, Mapping):
                    continue
                for label, digest in expected.items():
                    raw_path = attempt.get(label)
                    path = Path(str(raw_path)) if raw_path else None
                    actual = _sha256(path) if path is not None and path.is_file() else None
                    if actual != digest:
                        mismatches.append(
                            {
                                "job_id": job["job_id"],
                                "attempt_id": attempt["attempt_id"],
                                "artifact": label,
                                "path": str(path) if path is not None else None,
                                "expected_sha256": digest,
                                "actual_sha256": actual,
                            }
                        )
        if mismatches:
            self.state["global_blocker"] = {
                "classification": "global-repository-defect",
                "at": utc_now(),
                "reason": "immutable attempt evidence changed",
                "mismatches": mismatches,
            }
            _append_action(
                self.state,
                action="attempt-integrity-failed",
                details={"mismatches": mismatches},
            )
            self._save()
            raise ControllerError("immutable overnight attempt evidence changed")

    def recover_interrupted_attempt(self) -> None:
        running = [job for job in self.state["queue"] if job["state"] == "running"]
        if not running:
            if self.state.get("current_work") is not None:
                self.state["current_work"] = None
                self._save()
            return
        if len(running) != 1:
            raise ControllerError("multiple overnight jobs are marked running")
        job = running[0]
        active_attempts = [item for item in job["attempts"] if item.get("status") == "running"]
        if len(active_attempts) != 1:
            raise ControllerError("running overnight job has ambiguous attempt state")
        attempt = active_attempts[0]
        child_pid = attempt.get("process_pid")
        if type(child_pid) is int and _process_exists(child_pid):
            raise ControllerError(
                f"interrupted controller child process is still running with pid {child_pid}"
            )
        attempt["status"] = "interrupted"
        attempt["finished_at"] = utc_now()
        attempt["classification"] = "transient"
        job["state"] = "deferred-transient"
        job["next_eligible_at"] = utc_now()
        job["retry_exhausted"] = len(job["attempts"]) >= job["max_attempts"]
        job["last_error"] = "controller process ended while attempt was running"
        self.state["current_work"] = None
        _append_action(
            self.state,
            action="interrupted-attempt-deferred",
            job_id=job["job_id"],
            attempt_id=attempt["attempt_id"],
            details={"rule": "retry creates a new immutable attempt"},
        )
        self._save()

    def retry(self, job_id: str) -> None:
        job = self._job(job_id)
        if job["state"] == "running":
            raise ControllerError("cannot retry a running job")
        if len(job["attempts"]) >= job["max_attempts"]:
            job["max_attempts"] = len(job["attempts"]) + 1
        previous = job["state"]
        job["state"] = "pending"
        job["next_eligible_at"] = None
        job["retry_exhausted"] = False
        job["last_error"] = None
        self.state["global_blocker"] = None
        _append_action(
            self.state,
            action="job-requeued",
            job_id=job_id,
            details={"previous_state": previous},
        )
        self._save()

    def _dependencies_completed(self, job: Mapping[str, Any]) -> bool:
        return all(self._job(job_id)["state"] == "completed" for job_id in job["depends_on"])

    def _eligible(self, job: Mapping[str, Any], *, now: datetime) -> bool:
        if job["state"] not in RETRYABLE_STATES:
            return False
        if len(job["attempts"]) >= job["max_attempts"]:
            return False
        if not self._dependencies_completed(job):
            return False
        next_eligible = job.get("next_eligible_at")
        return not next_eligible or parse_utc(str(next_eligible)) <= now

    def _next_job(self, *, only_job: str | None = None) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        candidates = self.state["queue"]
        if only_job is not None:
            candidates = [self._job(only_job)]
        return next((job for job in candidates if self._eligible(job, now=now)), None)

    def _attempt_dir(self, job: Mapping[str, Any]) -> tuple[str, Path]:
        ordinal = len(job["attempts"]) + 1
        attempt_id = f"attempt-{ordinal:03d}-{uuid.uuid4().hex}"
        path = self.run_dir / "attempts" / str(job["job_id"]) / attempt_id
        path.mkdir(parents=True, exist_ok=False)
        return attempt_id, path

    def _expanded_command(self, job: Mapping[str, Any], attempt_dir: Path) -> list[str]:
        replacements = {
            "{attempt_dir}": str(attempt_dir),
            "{run_dir}": str(self.run_dir),
            "{state_path}": str(self.state_path),
            "{repo_root}": str(self.state["repo_root"]),
        }
        result: list[str] = []
        for argument in job["command"]:
            expanded = argument
            for marker, value in replacements.items():
                expanded = expanded.replace(marker, value)
            result.append(expanded)
        return result

    def _classification(
        self,
        *,
        job: Mapping[str, Any],
        attempt_dir: Path,
        exit_code: int,
    ) -> tuple[str, dict[str, Any] | None]:
        result_path = attempt_dir / str(job["result_file"])
        result: dict[str, Any] | None = None
        if result_path.is_file():
            try:
                raw = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                return "infrastructure", {"error": f"invalid attempt-result.json: {exc}"}
            if not isinstance(raw, dict):
                return "infrastructure", {"error": "attempt result must be an object"}
            result = raw
            declared = raw.get("classification")
            if declared is not None:
                if declared not in RESULT_CLASSIFICATIONS:
                    return "infrastructure", {"error": "unknown attempt result classification"}
                if exit_code != 0 and declared == "completed":
                    return "infrastructure", {
                        "error": "non-zero process exit cannot declare completed"
                    }
                if exit_code == 0 and declared != "completed":
                    return str(declared), result
                if exit_code != 0:
                    return str(declared), result
        if exit_code == 0:
            return "completed", result
        policy = job["failure_policy"]
        return str(policy["exit_codes"].get(str(exit_code), policy["default"])), result

    def _apply_outcome(
        self,
        *,
        job: dict[str, Any],
        attempt: dict[str, Any],
        classification: str,
        result: Mapping[str, Any] | None,
    ) -> None:
        attempt["classification"] = classification
        attempt["result"] = dict(result or {})
        reason = str((result or {}).get("reason") or f"process exit code {attempt['exit_code']}")
        links = (result or {}).get("result_links", [])
        if isinstance(links, list):
            for link in links:
                if isinstance(link, str) and link not in job["result_links"]:
                    job["result_links"].append(link)
        if classification == "completed":
            job["state"] = "completed"
            job["next_eligible_at"] = None
            job["retry_exhausted"] = False
            job["last_error"] = None
            attempt["status"] = "completed"
        elif classification == "transient":
            job["last_error"] = reason
            attempt["status"] = "deferred-transient"
            if len(job["attempts"]) < job["max_attempts"]:
                job["state"] = "deferred-transient"
                job["retry_exhausted"] = False
                next_at = datetime.now(timezone.utc) + timedelta(
                    seconds=int(job["retry_backoff_seconds"])
                )
                job["next_eligible_at"] = next_at.isoformat().replace("+00:00", "Z")
            else:
                job["state"] = "deferred-transient"
                job["next_eligible_at"] = None
                job["retry_exhausted"] = True
        elif classification == "scope-blocker":
            job["state"] = "blocked-scope"
            job["next_eligible_at"] = None
            job["retry_exhausted"] = False
            job["last_error"] = reason
            attempt["status"] = "blocked-scope"
        elif classification == "infrastructure":
            job["state"] = "failed-infrastructure"
            job["next_eligible_at"] = None
            job["retry_exhausted"] = False
            job["last_error"] = reason
            attempt["status"] = "failed-infrastructure"
        elif classification in {
            "global-source-corruption",
            "global-repository-defect",
        }:
            job["state"] = "failed-infrastructure"
            job["next_eligible_at"] = None
            job["retry_exhausted"] = False
            job["last_error"] = reason
            attempt["status"] = "failed-infrastructure"
            self.state["global_blocker"] = {
                "classification": classification,
                "job_id": job["job_id"],
                "attempt_id": attempt["attempt_id"],
                "at": utc_now(),
                "reason": reason,
            }
        else:
            raise ControllerError(f"unsupported result classification: {classification}")

    def execute_job(self, job: dict[str, Any]) -> None:
        self.verify_source_guard()
        self.verify_attempt_integrity()
        attempt_id, attempt_dir = self._attempt_dir(job)
        command = self._expanded_command(job, attempt_dir)
        stdout_path = attempt_dir / "stdout.log"
        stderr_path = attempt_dir / "stderr.log"
        command_path = attempt_dir / "command.json"
        _write_json_atomic(command_path, {"command": command, "cwd": job["cwd"]})
        attempt = {
            "attempt_id": attempt_id,
            "attempt_dir": str(attempt_dir),
            "status": "running",
            "classification": None,
            "started_at": utc_now(),
            "finished_at": None,
            "duration_ms": None,
            "exit_code": None,
            "process_pid": None,
            "timed_out": False,
            "termination": None,
            "command_file": str(command_path),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "result_file": str(attempt_dir / job["result_file"]),
        }
        job["attempts"].append(attempt)
        job["state"] = "running"
        job["next_eligible_at"] = None
        self.state["current_work"] = job["job_id"]
        _append_action(
            self.state,
            action="attempt-started",
            job_id=job["job_id"],
            attempt_id=attempt_id,
            details={"attempt_dir": str(attempt_dir)},
        )
        self._save(safe=False)
        started = time.monotonic()
        environment = os.environ.copy()
        environment.setdefault("PYTHONUTF8", "1")
        environment.setdefault("PYTHONIOENCODING", "utf-8")
        timed_out = False
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                popen_options: dict[str, Any] = {}
                if os.name == "nt":
                    popen_options["creationflags"] = getattr(
                        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
                    )
                else:
                    popen_options["start_new_session"] = True
                process = subprocess.Popen(
                    command,
                    cwd=job["cwd"],
                    env=environment,
                    stdout=stdout,
                    stderr=stderr,
                    shell=False,
                    **popen_options,
                )
                attempt["process_pid"] = process.pid
                _append_action(
                    self.state,
                    action="child-process-started",
                    job_id=job["job_id"],
                    attempt_id=attempt_id,
                    details={"pid": process.pid},
                )
                self._save(safe=False)
                try:
                    exit_code = process.wait(timeout=job["timeout_seconds"])
                except subprocess.TimeoutExpired:
                    timed_out = True
                    attempt["timed_out"] = True
                    attempt["termination"] = _terminate_process_tree(process)
                    exit_code = process.returncode if process.returncode is not None else 124
        except OSError as exc:
            exit_code = 126
            stderr_path.write_text(
                f"{type(exc).__name__}: {exc}\n", encoding="utf-8", newline="\n"
            )
        attempt["finished_at"] = utc_now()
        attempt["duration_ms"] = max(0, round((time.monotonic() - started) * 1000))
        attempt["exit_code"] = exit_code
        if timed_out:
            classification = str(job["timeout_classification"])
            result = {
                "classification": classification,
                "reason": f"job timeout after {job['timeout_seconds']} seconds",
                "timeout_seconds": job["timeout_seconds"],
                "result_links": [str(attempt_dir)],
            }
        else:
            classification, result = self._classification(
                job=job,
                attempt_dir=attempt_dir,
                exit_code=exit_code,
            )
        self._apply_outcome(
            job=job,
            attempt=attempt,
            classification=classification,
            result=result,
        )
        attempt["artifact_sha256"] = {
            label: _sha256(Path(attempt[label]))
            for label in ("command_file", "stdout", "stderr", "result_file")
            if Path(attempt[label]).is_file()
        }
        self.state["current_work"] = None
        _append_action(
            self.state,
            action="attempt-finished",
            job_id=job["job_id"],
            attempt_id=attempt_id,
            details={
                "classification": classification,
                "state": job["state"],
                "exit_code": exit_code,
                "duration_ms": attempt["duration_ms"],
            },
        )
        self._save()

    def run(
        self,
        *,
        only_job: str | None = None,
        max_jobs: int | None = None,
        max_idle_seconds: int = 0,
    ) -> dict[str, Any]:
        if max_jobs is not None and max_jobs < 1:
            raise ControllerError("max_jobs must be positive when provided")
        if max_idle_seconds < 0:
            raise ControllerError("max_idle_seconds must be non-negative")
        with _controller_lock(self.run_dir):
            self.state = load_state(self.state_path)
            self.verify_attempt_integrity()
            self.recover_interrupted_attempt()
            executed = 0
            idle_started = time.monotonic()
            while not self.state.get("global_blocker"):
                job = self._next_job(only_job=only_job)
                if job is not None:
                    self.execute_job(job)
                    executed += 1
                    idle_started = time.monotonic()
                    if max_jobs is not None and executed >= max_jobs:
                        break
                    if only_job is not None:
                        break
                    continue
                deferred_future = [
                    job
                    for job in self.state["queue"]
                    if job["state"] == "deferred-transient"
                    and len(job["attempts"]) < job["max_attempts"]
                    and self._dependencies_completed(job)
                ]
                if (
                    deferred_future
                    and max_idle_seconds > 0
                    and time.monotonic() - idle_started < max_idle_seconds
                ):
                    time.sleep(min(1.0, max_idle_seconds - (time.monotonic() - idle_started)))
                    continue
                self._propagate_terminal_dependencies()
                break
            self._save()
        return self.state

    def _propagate_terminal_dependencies(self) -> None:
        changed = True
        while changed:
            changed = False
            for job in self.state["queue"]:
                if job["state"] not in RETRYABLE_STATES:
                    continue
                blockers = [
                    self._job(item)
                    for item in job["depends_on"]
                    if self._job(item)["state"] in {
                        "blocked-scope",
                        "failed-infrastructure",
                    }
                ]
                if not blockers:
                    continue
                infrastructure = any(
                    item["state"] == "failed-infrastructure" for item in blockers
                )
                job["state"] = (
                    "failed-infrastructure" if infrastructure else "blocked-scope"
                )
                job["next_eligible_at"] = None
                job["last_error"] = "blocked by terminal dependencies: " + ", ".join(
                    str(item["job_id"]) for item in blockers
                )
                _append_action(
                    self.state,
                    action="dependency-terminal-propagated",
                    job_id=job["job_id"],
                    details={
                        "dependencies": [item["job_id"] for item in blockers],
                        "state": job["state"],
                    },
                )
                changed = True


def render_summary(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Итог устойчивого ночного запуска",
        "",
        f"- Run ID: `{payload.get('run_id')}`",
        f"- Статус: `{payload.get('overall_status')}`",
        f"- Цель: {payload.get('goal')}",
        f"- Последнее безопасное состояние: `{(payload.get('last_confirmed_safe_state') or {}).get('at')}`",
        "",
        "## Очередь",
        "",
        "| Работа | Scope | Состояние | Попытки | Последняя ошибка |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for job in payload.get("queue", []):
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{job.get('job_id')}`",
                    str(job.get("scope")),
                    f"`{job.get('state')}`",
                    str(len(job.get("attempts", []))),
                    str(job.get("last_error") or "—").replace("|", "\\|"),
                )
            )
            + " |"
        )
    lines.extend(["", "## Команды продолжения", ""])
    commands = payload.get("continuation_commands", [])
    if commands:
        lines.extend(f"- `{command}`" for command in commands)
    else:
        lines.append("- Продолжение не требуется.")
    if payload.get("global_blocker"):
        lines.extend(
            [
                "",
                "## Глобальный blocker",
                "",
                "```json",
                json.dumps(payload["global_blocker"], ensure_ascii=False, indent=2),
                "```",
            ]
        )
    return "\n".join(lines) + "\n"
