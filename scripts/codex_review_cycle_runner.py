"""Session-based writer/reviewer cycle runner.

This script validates and dry-runs the new Codex SDK orchestration contract for
test-case writer/reviewer work. It intentionally keeps domain decisions in
skills and references; the runner only enforces lifecycle gates, snapshots
artifacts, and selects the next session prompt.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.backends import start_fresh_sdk_thread


RUNNER_LOCK_FILE = "runner.lock.yaml"
RUNNER_EVENTS_FILE = "runner-events.ndjson"
COMPLETION_MANIFEST_SUFFIX = "-completion.yaml"
DEFAULT_STALE_LOCK_SECONDS = 1800
HEARTBEAT_INTERVAL_SECONDS = 30
TERMINAL_STATUSES = {"signed-off", "round-cap-reached", "blocked-input"}
REVIEWER_READ_ONLY_SCENARIOS = {
    "reviewer.scope_gap_review",
    "reviewer.structure_preflight",
    "reviewer.semantic_traceability_test_design",
    "reviewer.structure_format_final",
    "reviewer.semantic_regression",
}
BOUNDED_REVIEWER_SCENARIOS = {
    "reviewer.scope_gap_review",
    "reviewer.structure_format_final",
    "reviewer.semantic_regression",
}
AUTO_SESSION_TIMEOUT_SENTINEL = -1
DEFAULT_SESSION_TIMEOUT_SECONDS_BY_SCENARIO = {
    "scope.session_gap_review": 1800,
    "reviewer.scope_gap_review": 1800,
    "reviewer.structure_preflight": 1800,
    "reviewer.semantic_traceability_test_design": 1800,
    "reviewer.structure_format_final": 1800,
    "reviewer.semantic_regression": 1800,
    "writer.session_initial_draft": 3600,
    "writer.session_semantic_revision": 3600,
    "writer.session_format_revision": 3600,
    "writer.remediation.style": 3600,
    "writer.remediation.structure_preflight": 3600,
}
BLOCKING_VALIDATOR_SEVERITIES = {"error", "warning"}
VALIDATOR_WAIVER_STATUSES = {"waived", "false-positive", "accepted-nonblocking"}
VALIDATOR_WAIVER_CLASSES = {
    "false-positive",
    "validator-schema-lag",
    "accepted-source-gap",
    "accepted-nonblocking-risk",
}
VALIDATOR_WAIVER_HEADINGS = {
    "validator warning waivers",
    "validator finding waivers",
    "validator waivers",
}
PLACEHOLDER_VALUES = {"", "-", "n/a", "na", "none", "tbd", "todo", "<...>"}
PROCESS_ONLY_WAIVER_PATTERNS = (
    "pre-existing",
    "not introduced",
    "no regression",
    "format-only",
    "hash unchanged",
    "unchanged",
)
GAP_ID_PATTERN = re.compile(r"\bGAP-[A-Za-z0-9][A-Za-z0-9_-]*\b")
SESSION_READY_VALIDATOR_GATE_STATUSES = {"writer-draft-ready", "semantic-review-ready"}
SESSION_READY_BLOCKING_VALIDATOR_FINDING_IDS = {
    "artifact-write-strategy-unsafe-or-vague",
    "coverage-obligation-table-no-table",
    "source-row-inventory-no-table",
    "test-case-split-artifact-duplicated-sections",
    "test-design-review-missing-columns",
    "test-design-review-missing-required-items",
    "test-design-review-no-table",
    "test-design-review-unknown-items",
    "test-case-mixed-schema-duplicate-fields",
    "test-case-noncanonical-heading-level",
    "test-case-runtime-field-duplicated",
    "test-case-duplicated-source-reference-fields",
    "test-case-dictionary-reference-missing-from-traceability",
    "test-case-synthetic-requirement-quote-smell",
    "test-case-action-created-block-without-cleanup",
    "test-case-branch-oracle-not-distinct",
    "test-case-bundled-negative-input-classes",
    "test-case-negative-transition-without-valid-fixture-smell",
    "test-case-requiredness-without-empty-or-marker-check",
    "test-case-package-design-plan-missing-conditional-branch",
    "test-design-decision-table-executable-cross-section-conflict",
    "test-design-decision-table-gap-cross-section-conflict",
    "test-design-decision-table-gap-executable-behavior-smell",
    "test-design-decision-table-overbroad-gap-smell",
    "test-design-decision-table-standalone-without-tc-or-oracle",
    "test-design-decision-table-metadata-behavior-smell",
    "test-design-decision-table-metadata-cross-section-conflict",
    "test-design-applicability-matrix-linked-tc-dimension-mismatch",
    "coverage-obligation-table-duplicate-class",
    "coverage-obligation-table-invalid-status",
    "coverage-obligation-table-unknown-source-property",
    "source-normalization-combined-property-class-smell",
    "source-normalization-unmapped-property",
    "source-row-completeness-matrix-missing",
    "source-row-gsr-count-mismatch",
    "source-row-inventory-invalid-in-scope",
    "source-row-inventory-misses-normalized-source-row",
    "source-table-normalization-missing-columns",
    "test-case-action-treated-as-required-field-smell",
    "test-case-missing-package-id",
    "test-case-package-design-plan-many-rows-one-tc-smell",
    "test-case-package-design-plan-merged-numeric-class-row",
    "test-case-package-design-plan-merged-check-smell",
    "test-case-package-design-plan-missing-atoms",
    "test-case-package-design-plan-missing-columns",
    "test-case-package-design-plan-negative-without-positive-acceptance",
    "test-case-risk-priority-map-high-risk-without-high-test-case",
    "test-case-risk-priority-map-invalid-atom-id",
    "test-design-decision-table-invalid-decision",
    "test-design-decision-table-merged-numeric-class-decision",
    "test-design-decision-table-missing-columns",
    "test-design-review-failed",
    "test-design-review-invalid-blocks-value",
    "test-design-review-invalid-severity",
    "test-design-review-invalid-status",
    "writer-self-check-empty-section",
    "writer-quality-gate-failed",
    "writer-quality-gate-invalid-blocks-value",
    "writer-quality-gate-invalid-status",
    "writer-quality-gate-missing-columns",
    "writer-quality-gate-missing-required-items",
    "writer-quality-gate-scoped-validator-profile-invalid",
    "writer-quality-gate-contradicts-validator-profile",
}
VALIDATOR_NOT_RUN_PATTERNS = (
    "validator not run",
    "validator has not been run",
    "validator not executed",
    "validator was not run",
    "scoped validator not run",
    "scoped validator has not been run",
)
PROGRESS_ACCEPTED_TURN_STATUSES = {"interrupted"}
CHAIN_ACCEPTED_SESSION_STATUSES = {"completed", "completed-with-progress"}
PROGRESS_STATE_KEYS = (
    "current_stage",
    "stage_status",
    "semantic_round",
    "active_transition_prompt",
)
STATE_STRING_LIST_FIELDS = {
    "accepted_risks",
    "blocking_findings",
    "blocking_reasons",
    "latest_artifacts",
    "open_questions",
    "sessions",
}
POST_SESSION_ALLOWED_STAGE_STATUSES: dict[str, set[str]] = {
    "reviewer.scope_gap_review": {"scope-gap-review-passed", "scope-ready-for-writer"},
    "writer.session_initial_draft": {"writer-draft-ready"},
    "writer.remediation.structure_preflight": {"writer-draft-ready"},
    "writer.session_semantic_revision": {"semantic-review-ready"},
    "writer.session_format_revision": {"final-regression-ready"},
    "reviewer.structure_preflight": {"semantic-review-ready", "structure-preflight-blocked"},
    "reviewer.semantic_traceability_test_design": {
        "format-review-ready",
        "semantic-review-passed",
        "semantic-revision-needed",
    },
    "reviewer.semantic_regression": set(),
    "reviewer.structure_format_final": {"format-revision-needed", "final-regression-ready"},
}
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


@dataclass(frozen=True)
class ValidatorWaiver:
    finding_id: str
    path: str
    waiver_status: str
    waiver_class: str
    rationale: str
    evidence: str
    source_path: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.finding_id, self.path)


class RunnerError(RuntimeError):
    pass


def sandbox_policy_for_role_scenario(role: str, scenario: str) -> str:
    if role == "writer":
        return "workspace_write"
    if role != "reviewer":
        raise RunnerError(f"Unsupported session role for sandbox policy: {role}")
    if scenario in REVIEWER_READ_ONLY_SCENARIOS:
        return "read_only"
    raise RunnerError(f"Reviewer scenario has no explicit sandbox policy: {scenario}")


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
    top-level scalar keys and top-level lists. For runner-owned state files it
    also tolerates accidental one-level nested maps under list-like fields by
    collecting their scalar/list leaves into the top-level list. The canonical
    writer/reviewer contract remains simple YAML; this tolerance is recovery,
    not a broader artifact format.
    """

    result: dict[str, Any] = {}
    current_list_key: str | None = None

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith((" ", "\t")):
            if current_list_key is None:
                raise RunnerError(f"Unsupported YAML shape at {path}:{line_no}")
            if stripped.startswith("- "):
                item_text = stripped[2:].strip()
                result.setdefault(current_list_key, []).append(parse_scalar(item_text))
                continue
            if ":" in stripped and current_list_key in STATE_STRING_LIST_FIELDS:
                _, raw_value = stripped.split(":", 1)
                if raw_value.strip():
                    result.setdefault(current_list_key, []).append(parse_scalar(raw_value))
                continue
            raise RunnerError(f"Unsupported YAML shape at {path}:{line_no}")
            continue

        if stripped.startswith("- "):
            if current_list_key is None:
                raise RunnerError(f"Unsupported YAML line at {path}:{line_no}")
            item_text = stripped[2:].strip()
            result.setdefault(current_list_key, []).append(parse_scalar(item_text))
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

    normalize_simple_yaml_state(result)
    return result


def write_simple_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(render_simple_yaml(data), encoding="utf-8")


def normalize_simple_yaml_state(data: dict[str, Any]) -> None:
    for key in STATE_STRING_LIST_FIELDS:
        value = data.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            data[key] = [str(item) for item in value if str(item).strip()]
            continue
        if isinstance(value, dict):
            leaves: list[str] = []
            collect_scalar_leaves(value, leaves)
            data[key] = leaves


def collect_scalar_leaves(value: Any, leaves: list[str]) -> None:
    if isinstance(value, dict):
        for nested_value in value.values():
            collect_scalar_leaves(nested_value, leaves)
        return
    if isinstance(value, list):
        for item in value:
            collect_scalar_leaves(item, leaves)
        return
    text = str(value or "").strip()
    if text:
        leaves.append(text)


def unique_nonempty_strings(*groups: Any) -> list[str]:
    values: list[str] = []
    for group in groups:
        if group is None:
            continue
        if isinstance(group, (list, tuple, set)):
            candidates = group
        else:
            candidates = [group]
        for candidate in candidates:
            text = str(candidate or "").strip()
            if text and text not in values:
                values.append(text)
    return values


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


def child_timeout_diagnostics(
    cycle_dir: Path,
    *,
    stage: str,
    started_at_epoch: int,
) -> dict[str, Any]:
    event_path = cycle_dir / RUNNER_EVENTS_FILE
    thread_id = ""
    thread_started_epoch = ""
    turn_started_epoch = ""
    if event_path.exists():
        for raw_line in event_path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if str(event.get("stage") or "") != stage:
                continue
            try:
                event_ts = int(event.get("ts_epoch") or 0)
            except (TypeError, ValueError):
                event_ts = 0
            if event_ts < started_at_epoch:
                continue
            event_name = str(event.get("event") or "")
            if event_name == "thread_started":
                thread_id = str(event.get("thread_id") or thread_id)
                thread_started_epoch = event_ts
            elif event_name == "turn_started":
                thread_id = str(event.get("thread_id") or thread_id)
                turn_started_epoch = event_ts

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


def scoped_validator_profile_event_consistency(
    last_event: dict[str, Any] | None,
    *,
    ft_root: Path,
) -> dict[str, Any]:
    if not last_event or last_event.get("event") != "scoped_validator_profile_written":
        return {"checked": False, "reason": "last event is not scoped_validator_profile_written"}

    profile_ref = str(last_event.get("profile") or "")
    if not profile_ref:
        return {
            "checked": True,
            "consistent": False,
            "issues": ["profile field is missing in scoped_validator_profile_written event"],
        }

    profile_path = Path(profile_ref)
    if not profile_path.is_absolute():
        profile_path = ft_root / profile_path

    if not profile_path.exists():
        return {
            "checked": True,
            "consistent": False,
            "profile": str(profile_path),
            "issues": ["profile file referenced by event does not exist"],
        }

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "checked": True,
            "consistent": False,
            "profile": str(profile_path),
            "issues": ["profile file referenced by event is not valid JSON"],
        }

    event_unresolved = last_event.get("unresolved_warning_error_count")
    profile_unresolved = profile.get("unresolved_warning_error_count")
    issues: list[str] = []
    if event_unresolved != profile_unresolved:
        issues.append(
            "event unresolved_warning_error_count "
            f"({event_unresolved!r}) differs from profile unresolved_warning_error_count ({profile_unresolved!r})"
        )

    event_stage = str(last_event.get("stage") or "")
    profile_stage = str(profile.get("current_stage") or "")
    if event_stage and profile_stage and event_stage != profile_stage:
        issues.append(f"event stage ({event_stage!r}) differs from profile current_stage ({profile_stage!r})")

    return {
        "checked": True,
        "consistent": not issues,
        "profile": str(profile_path),
        "event_unresolved_warning_error_count": event_unresolved,
        "profile_unresolved_warning_error_count": profile_unresolved,
        "issues": issues,
    }


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


def normalize_artifact_path_text(value: Any) -> str:
    text = str(value or "").strip().strip("`").replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text.rstrip("/")


def non_placeholder_cell(value: str) -> bool:
    normalized = value.strip().strip("`").strip().lower()
    return normalized not in PLACEHOLDER_VALUES and not (
        normalized.startswith("<") and normalized.endswith(">")
    )


def path_is_under(path: str, directory: str) -> bool:
    directory = directory.rstrip("/")
    return bool(directory) and (path == directory or path.startswith(f"{directory}/"))


def is_snapshot_or_write_scratch_path(path: str) -> bool:
    parts = [part for part in path.split("/") if part]
    return "versions" in parts or "_artifact_write" in parts


def finding_belongs_to_current_scope(
    finding: dict[str, Any],
    state: dict[str, Any],
    state_path: Path,
) -> bool:
    path = normalize_artifact_path_text(finding.get("path"))
    if not path or is_snapshot_or_write_scratch_path(path):
        return False

    canonical = normalize_artifact_path_text(state.get("canonical_test_cases"))
    draft = normalize_artifact_path_text(state.get("draft_test_cases"))
    test_design_dir = normalize_artifact_path_text(state.get("test_design_dir"))
    ft_root = infer_ft_root(state_path)
    outputs_dir = relative_or_name(state_path.parent / "outputs", ft_root)

    return (
        path == canonical
        or path == draft
        or path_is_under(path, test_design_dir)
        or path_is_under(path, outputs_dir)
    )


def run_agent_artifact_validator(ft_root: Path) -> dict[str, Any]:
    script_path = Path(__file__).resolve().with_name("validate_agent_artifacts.py")
    root = script_path.parents[1]
    result = subprocess.run(
        [sys.executable, str(script_path), "--root", str(ft_root), "--json"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RunnerError(f"Agent artifact validator failed: {detail}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RunnerError("Agent artifact validator returned invalid JSON") from exc


def current_scope_validator_findings(
    validator_payload: dict[str, Any],
    state: dict[str, Any],
    state_path: Path,
) -> list[dict[str, Any]]:
    return [
        finding
        for finding in validator_payload.get("findings", [])
        if finding_belongs_to_current_scope(finding, state, state_path)
    ]


def write_runner_scoped_validator_profile(
    state: dict[str, Any],
    state_path: Path,
    validator_payload: dict[str, Any],
    *,
    scoped_findings: list[dict[str, Any]] | None = None,
) -> Path:
    ft_root = infer_ft_root(state_path)
    repo_root = Path(__file__).resolve().parents[1]
    validator_root = relative_or_name(ft_root, repo_root)
    stage = str(state.get("current_stage") or "current").strip() or "current"
    output_dir = state_path.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_path = output_dir / f"scoped-validator-profile.{stage}.json"
    if scoped_findings is None:
        scoped_findings = current_scope_validator_findings(validator_payload, state, state_path)
    unresolved_warning_errors = [
        finding
        for finding in scoped_findings
        if str(finding.get("severity") or "").lower() in BLOCKING_VALIDATOR_SEVERITIES
    ]
    payload = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": f"python scripts/validate_agent_artifacts.py --root {validator_root} --json",
        "scope_slug": state.get("scope_slug") or "",
        "canonical_test_cases": normalize_artifact_path_text(state.get("canonical_test_cases")),
        "test_design_dir": normalize_artifact_path_text(state.get("test_design_dir")),
        "current_stage": stage,
        "current_scope_findings": scoped_findings,
        "unresolved_warning_error_count": len(unresolved_warning_errors),
    }
    profile_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_runner_event(
        state_path.parent,
        "scoped_validator_profile_written",
        stage=stage,
        profile=relative_or_name(profile_path, ft_root),
        unresolved_warning_error_count=len(unresolved_warning_errors),
    )
    return profile_path


def default_writer_draft_test_cases_ref(state_path: Path, stage: str) -> str:
    ft_root = infer_ft_root(state_path)
    return relative_or_name(state_path.parent / "outputs" / f"{stage}-draft.md", ft_root)


def active_test_cases_ref(state: dict[str, Any], state_path: Path) -> str:
    draft_ref = normalize_artifact_path_text(state.get("draft_test_cases"))
    if draft_ref and str(state.get("stage_status") or "") != "signed-off":
        draft_path = resolve_artifact_path(draft_ref, infer_ft_root(state_path))
        if draft_path is not None and draft_path.exists():
            return draft_ref
    return normalize_artifact_path_text(state.get("canonical_test_cases"))


def active_test_cases_path(state: dict[str, Any], state_path: Path) -> Path:
    ft_root = infer_ft_root(state_path)
    active_ref = active_test_cases_ref(state, state_path)
    active_path = resolve_artifact_path(active_ref, ft_root)
    if active_path is None:
        raise RunnerError(f"Active test-case file does not exist: {active_ref}")
    return active_path


def table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return []
    return [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]


def is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def validator_waivers_from_markdown(
    text: str,
    *,
    source_path: str = "",
) -> dict[tuple[str, str], ValidatorWaiver]:
    waivers: dict[tuple[str, str], ValidatorWaiver] = {}
    in_section = False
    headers: list[str] = []
    for raw_line in text.splitlines():
        heading = raw_line.strip()
        if heading.startswith("## "):
            title = heading.lstrip("#").strip().lower()
            in_section = title in VALIDATOR_WAIVER_HEADINGS
            headers = []
            continue
        if not in_section:
            continue
        cells = table_cells(raw_line)
        if not cells or is_table_separator(cells):
            continue
        normalized_cells = [cell.strip().lower() for cell in cells]
        if "finding_id" in normalized_cells and "path" in normalized_cells:
            headers = normalized_cells
            continue
        if not headers or len(cells) < len(headers):
            continue
        row = {headers[index]: cells[index].strip() for index in range(len(headers))}
        finding_id = row.get("finding_id") or row.get("id") or row.get("validator_finding_id")
        path = row.get("path")
        status = (row.get("waiver_status") or row.get("status") or "").strip().lower()
        waiver_class = (row.get("waiver_class") or row.get("class") or "").strip().lower()
        rationale = row.get("rationale") or ""
        evidence = row.get("evidence") or ""
        if finding_id and path:
            waiver = ValidatorWaiver(
                finding_id=finding_id.strip().strip("`"),
                path=normalize_artifact_path_text(path),
                waiver_status=status,
                waiver_class=waiver_class,
                rationale=rationale.strip(),
                evidence=evidence.strip(),
                source_path=source_path,
            )
            waivers[waiver.key] = waiver
    return waivers


def collect_validator_waivers(cycle_dir: Path) -> dict[tuple[str, str], ValidatorWaiver]:
    output_dir = cycle_dir / "outputs"
    if not output_dir.exists():
        return {}
    waivers: dict[tuple[str, str], ValidatorWaiver] = {}
    for path in sorted(output_dir.glob("*.md")):
        waivers.update(
            validator_waivers_from_markdown(
                path.read_text(encoding="utf-8"),
                source_path=path.as_posix(),
            )
        )
    return waivers


def read_existing_artifact_text(ft_root: Path, artifact_path: str) -> str:
    resolved = resolve_artifact_path(artifact_path, ft_root)
    if not resolved or not resolved.exists() or not resolved.is_file():
        return ""
    try:
        return resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return resolved.read_text(encoding="utf-8", errors="ignore")


def markdown_section(text: str, title: str) -> str:
    match = re.search(rf"^##\s+{re.escape(title)}\s*$", text, flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+.+$", text[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end]


def writer_quality_gate_claims_scoped_validator_pass(text: str) -> bool:
    section = markdown_section(text, "Writer Quality Gate")
    if not section:
        return False
    headers: list[str] = []
    for line in section.splitlines():
        cells = table_cells(line)
        if not cells or is_table_separator(cells):
            continue
        normalized_cells = [cell.strip().lower() for cell in cells]
        if "gate_item" in normalized_cells and "status" in normalized_cells:
            headers = normalized_cells
            continue
        if not headers or len(cells) < len(headers):
            continue
        row = {headers[index]: cells[index].strip() for index in range(len(headers))}
        gate_item = (row.get("gate_item") or "").strip().strip("`")
        status = (row.get("status") or "").strip().strip("`").lower()
        if gate_item == "scoped-validator-findings" and status == "pass":
            return True
    return False


def writer_quality_gate_pass_artifacts(state: dict[str, Any], state_path: Path) -> list[str]:
    ft_root = infer_ft_root(state_path)
    candidates: list[tuple[str, str]] = []
    canonical = normalize_artifact_path_text(state.get("canonical_test_cases"))
    if canonical:
        candidates.append((canonical, read_existing_artifact_text(ft_root, canonical)))
    test_design_dir = normalize_artifact_path_text(state.get("test_design_dir"))
    if test_design_dir:
        gate_path = f"{test_design_dir}/writer-quality-gate.md"
        candidates.append((gate_path, read_existing_artifact_text(ft_root, gate_path)))
    return [
        artifact_path
        for artifact_path, text in candidates
        if text and writer_quality_gate_claims_scoped_validator_pass(text)
    ]


def collect_known_gap_ids(state: dict[str, Any], state_path: Path) -> set[str]:
    ft_root = infer_ft_root(state_path)
    text_parts = [json.dumps(state, ensure_ascii=False, default=str)]
    canonical = normalize_artifact_path_text(state.get("canonical_test_cases"))
    if canonical:
        text_parts.append(read_existing_artifact_text(ft_root, canonical))

    test_design_dir = normalize_artifact_path_text(state.get("test_design_dir"))
    resolved_test_design_dir = resolve_artifact_path(test_design_dir, ft_root)
    if resolved_test_design_dir and resolved_test_design_dir.exists():
        for path in sorted(resolved_test_design_dir.glob("*.md")):
            text_parts.append(path.read_text(encoding="utf-8", errors="ignore"))

    return set(GAP_ID_PATTERN.findall("\n".join(text_parts)))


def validator_waiver_invalid_reasons(
    waiver: ValidatorWaiver,
    *,
    known_gap_ids: set[str],
) -> list[str]:
    reasons: list[str] = []
    if waiver.waiver_status not in VALIDATOR_WAIVER_STATUSES:
        reasons.append("waiver_status is missing or unsupported")
    if waiver.waiver_class not in VALIDATOR_WAIVER_CLASSES:
        reasons.append("waiver_class is missing or unsupported")
    if not non_placeholder_cell(waiver.rationale):
        reasons.append("rationale is missing or placeholder")
    if not non_placeholder_cell(waiver.evidence):
        reasons.append("evidence is missing or placeholder")

    combined = f"{waiver.rationale}\n{waiver.evidence}"
    normalized_combined = combined.lower()
    if waiver.waiver_class == "accepted-source-gap":
        referenced_gaps = set(GAP_ID_PATTERN.findall(combined))
        if not referenced_gaps:
            reasons.append("accepted-source-gap waiver must cite GAP-*")
        elif not referenced_gaps.intersection(known_gap_ids):
            reasons.append("accepted-source-gap waiver must cite an existing GAP-*")

    if waiver.waiver_class == "validator-schema-lag":
        has_schema_mismatch = bool(
            re.search(
                r"schema|heuristic|validator\s+expects|expected\s+model|actual\s+model|models?\s+these|"
                r"schema\s+lag|validator-schema-lag",
                normalized_combined,
                flags=re.IGNORECASE,
            )
        )
        has_affected_refs = bool(
            re.search(r"\b(?:ATOM-\d{3,}|TC-[A-Za-z0-9_-]+|PDP-\d{3,}|PD-\d{3,})\b", combined)
        )
        has_counterevidence = bool(
            re.search(r"\bcovered\b|\blinked\b|\btraceability\b|coverage_status|no\s+open\s+findings", normalized_combined)
        )
        if not has_schema_mismatch:
            reasons.append("validator-schema-lag waiver must explain expected vs actual validator/schema model")
        if not has_affected_refs:
            reasons.append("validator-schema-lag waiver must cite affected ATOM/TC/PDP refs")
        if not has_counterevidence:
            reasons.append("validator-schema-lag waiver must cite coverage or reviewer counter-evidence")

    if waiver.waiver_class == "accepted-nonblocking-risk" and any(
        pattern in normalized_combined for pattern in PROCESS_ONLY_WAIVER_PATTERNS
    ):
        reasons.append(
            "pre-existing/no-regression/format-only rationale is not a valid standalone waiver"
        )

    return reasons


def terminal_signed_off_validator_gate(
    state: dict[str, Any],
    state_path: Path,
) -> dict[str, Any]:
    status = str(state.get("stage_status") or "")
    if status != "signed-off":
        return {
            "checked": False,
            "reason": f"stage_status is {status}, not signed-off",
        }

    ft_root = infer_ft_root(state_path)
    validator_payload = run_agent_artifact_validator(ft_root)
    findings = [
        finding
        for finding in validator_payload.get("findings", [])
        if finding_belongs_to_current_scope(finding, state, state_path)
    ]
    waivers = collect_validator_waivers(state_path.parent)
    known_gap_ids = collect_known_gap_ids(state, state_path)
    blocking: list[dict[str, Any]] = []
    waived: list[dict[str, Any]] = []
    invalid_waivers: list[dict[str, Any]] = []
    waived_by_class: dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("severity") or "").lower()
        if severity not in BLOCKING_VALIDATOR_SEVERITIES:
            continue
        finding_id = str(finding.get("id") or "")
        path = normalize_artifact_path_text(finding.get("path"))
        waiver = waivers.get((finding_id, path))
        if waiver:
            invalid_reasons = validator_waiver_invalid_reasons(
                waiver,
                known_gap_ids=known_gap_ids,
            )
            if invalid_reasons:
                invalid_waivers.append(
                    {
                        "id": finding_id,
                        "severity": finding.get("severity"),
                        "path": path,
                        "waiver_status": waiver.waiver_status,
                        "waiver_class": waiver.waiver_class,
                        "source_path": waiver.source_path,
                        "reasons": invalid_reasons,
                    }
                )
                continue
            waived.append(finding)
            waived_by_class[waiver.waiver_class] = waived_by_class.get(waiver.waiver_class, 0) + 1
        else:
            blocking.append(finding)

    return {
        "checked": True,
        "root": str(ft_root),
        "scoped_findings_count": len(findings),
        "blocking_unwaived_count": len(blocking),
        "waived_count": len(waived),
        "invalid_waivers_count": len(invalid_waivers),
        "waived_by_class": waived_by_class,
        "blocking_unwaived": [
            {
                "id": item.get("id"),
                "severity": item.get("severity"),
                "path": item.get("path"),
                "evidence": item.get("evidence"),
            }
            for item in blocking[:20]
        ],
        "invalid_waivers": invalid_waivers[:20],
    }


def enforce_terminal_signed_off_validator_gate(
    state: dict[str, Any],
    state_path: Path,
) -> dict[str, Any]:
    gate = terminal_signed_off_validator_gate(state, state_path)
    if gate.get("invalid_waivers_count"):
        first = gate["invalid_waivers"][0]
        reasons = ", ".join(first.get("reasons") or [])
        raise RunnerError(
            "terminal signed-off has invalid current-scope validator waivers: "
            f"{gate['invalid_waivers_count']} total; first={first.get('id')} "
            f"at {first.get('path')}; reasons={reasons}"
        )
    if gate.get("blocking_unwaived_count"):
        first = gate["blocking_unwaived"][0]
        raise RunnerError(
            "terminal signed-off has unwaived current-scope validator findings: "
            f"{gate['blocking_unwaived_count']} total; first={first.get('id')} "
            f"at {first.get('path')}"
        )
    return gate


def session_ready_validator_gate(
    state: dict[str, Any],
    state_path: Path,
) -> dict[str, Any]:
    status = str(state.get("stage_status") or "")
    if status not in SESSION_READY_VALIDATOR_GATE_STATUSES:
        return {
            "checked": False,
            "reason": f"stage_status is {status}, not a writer-ready reviewer handoff",
        }

    ft_root = infer_ft_root(state_path)
    validator_payload = run_agent_artifact_validator(ft_root)
    scoped_findings = current_scope_validator_findings(validator_payload, state, state_path)
    scoped_warning_errors = [
        finding
        for finding in scoped_findings
        if str(finding.get("severity") or "").lower() in BLOCKING_VALIDATOR_SEVERITIES
    ]
    scoped_validator_pass_artifacts = writer_quality_gate_pass_artifacts(state, state_path)
    if scoped_warning_errors and scoped_validator_pass_artifacts:
        first_actual = scoped_warning_errors[0]
        scoped_findings.insert(
            0,
            {
                "id": "writer-quality-gate-contradicts-validator-profile",
                "severity": "warning",
                "path": scoped_validator_pass_artifacts[0],
                "evidence": [
                    f"writer-quality-gate scoped-validator-findings=pass in {', '.join(scoped_validator_pass_artifacts[:3])}",
                    f"actual_current_scope_warning_error_count={len(scoped_warning_errors)}",
                    f"first_actual={first_actual.get('id')} at {first_actual.get('path')}",
                ],
            }
        )
    profile_path = write_runner_scoped_validator_profile(
        state,
        state_path,
        validator_payload,
        scoped_findings=scoped_findings,
    )
    blocking = [
        finding
        for finding in scoped_findings
        if str(finding.get("severity") or "").lower() in BLOCKING_VALIDATOR_SEVERITIES
    ]
    return {
        "checked": True,
        "root": str(ft_root),
        "scoped_validator_profile": relative_or_name(profile_path, ft_root),
        "scoped_findings_count": len(scoped_findings),
        "blocking_writer_ready_count": len(blocking),
        "blocking_writer_ready": [
            {
                "id": item.get("id"),
                "severity": item.get("severity"),
                "path": item.get("path"),
                "evidence": item.get("evidence"),
            }
            for item in blocking[:20]
        ],
    }


def enforce_session_ready_validator_gate(
    state: dict[str, Any],
    state_path: Path,
) -> dict[str, Any]:
    gate = session_ready_validator_gate(state, state_path)
    if gate.get("blocking_writer_ready_count"):
        first = gate["blocking_writer_ready"][0]
        raise RunnerError(
            "writer-ready state has current-scope blocking validator findings: "
            f"{gate['blocking_writer_ready_count']} total; first={first.get('id')} "
            f"at {first.get('path')}"
        )
    return gate


def blocked_input_validator_not_run_reasons(state: dict[str, Any]) -> list[str]:
    if str(state.get("stage_status") or "") != "blocked-input":
        return []
    current_stage = str(state.get("current_stage") or "")
    if not current_stage.startswith("writer"):
        return []
    reasons = state.get("blocking_reasons")
    if not isinstance(reasons, list):
        return []
    matches: list[str] = []
    for reason in reasons:
        text = str(reason or "")
        normalized = text.lower().replace("-", " ")
        if any(pattern in normalized for pattern in VALIDATOR_NOT_RUN_PATTERNS):
            matches.append(text)
    return matches


def enforce_blocked_input_validator_attempt_gate(state: dict[str, Any]) -> None:
    matches = blocked_input_validator_not_run_reasons(state)
    if matches:
        raise RunnerError(
            "writer blocked-input cannot be caused by missing post-write validator run; "
            f"first={matches[0]}"
        )


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


def validate_state(
    state: dict[str, Any],
    state_path: Path,
    *,
    enforce_validator_gates: bool = True,
) -> None:
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
    draft_ref = normalize_artifact_path_text(state.get("draft_test_cases"))
    draft = resolve_artifact_path(draft_ref, ft_root) if draft_ref else None
    draft_exists = draft is not None and draft.exists()
    if status not in PRE_WRITER_STATUSES and status != "blocked-input" and not canonical.exists() and not draft_exists:
        raise RunnerError(f"Canonical test-case file does not exist and no draft_test_cases exists: {canonical}")

    if status not in TERMINAL_STATUSES:
        prompt_path = state.get("active_transition_prompt")
        prompt = resolve_artifact_path(str(prompt_path), ft_root) if prompt_path else None
        if prompt is None or not prompt.exists():
            raise RunnerError(f"active_transition_prompt does not exist: {prompt_path}")

    enforce_blocked_input_validator_attempt_gate(state)
    if enforce_validator_gates:
        enforce_session_ready_validator_gate(state, state_path)


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
            sandbox_policy=sandbox_policy_for_role_scenario("reviewer", "reviewer.scope_gap_review"),
        )
    if status in {"scope-gap-review-passed", "scope-ready-for-writer"}:
        return NextSession(
            stage="writer-r1",
            role="writer",
            scenario="writer.session_initial_draft",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("writer", "writer.session_initial_draft"),
        )
    if status == "writer-draft-ready":
        return NextSession(
            stage="structure-preflight-r1",
            role="reviewer",
            scenario="reviewer.structure_preflight",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("reviewer", "reviewer.structure_preflight"),
        )
    if status == "structure-preflight-blocked":
        return NextSession(
            stage="writer-structure-r1",
            role="writer",
            scenario="writer.remediation.style",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("writer", "writer.remediation.style"),
        )
    if status == "semantic-review-ready":
        round_no = max(semantic_round, 1)
        return NextSession(
            stage=f"semantic-review-r{round_no}",
            role="reviewer",
            scenario="reviewer.semantic_traceability_test_design",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("reviewer", "reviewer.semantic_traceability_test_design"),
        )
    if status == "semantic-revision-needed":
        if semantic_round >= max_rounds:
            raise RunnerError("semantic round cap reached; do not start writer-r3")
        return NextSession(
            stage=f"writer-r{semantic_round + 1}",
            role="writer",
            scenario="writer.session_semantic_revision",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("writer", "writer.session_semantic_revision"),
        )
    if status in {"semantic-review-passed", "format-review-ready"}:
        return NextSession(
            stage="format-review-final",
            role="reviewer",
            scenario="reviewer.structure_format_final",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("reviewer", "reviewer.structure_format_final"),
        )
    if status == "format-revision-needed":
        return NextSession(
            stage="writer-format-final",
            role="writer",
            scenario="writer.session_format_revision",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("writer", "writer.session_format_revision"),
        )
    if status == "final-regression-ready":
        return NextSession(
            stage="semantic-regression-final",
            role="reviewer",
            scenario="reviewer.semantic_regression",
            prompt_path=prompt_path,
            sandbox_policy=sandbox_policy_for_role_scenario("reviewer", "reviewer.semantic_regression"),
        )
    raise RunnerError(f"No transition defined for status: {status}")


def diagnostic_session_for_current_stage(state: dict[str, Any]) -> NextSession | None:
    if str(state.get("stage_status") or "") != "blocked-input":
        return None
    stage = str(state.get("current_stage") or "").strip()
    prompt_path = str(state.get("active_transition_prompt") or "")
    if not stage:
        return None

    if stage == "scope-gap-review":
        role, scenario = "reviewer", "reviewer.scope_gap_review"
    elif stage == "writer-r1":
        role, scenario = "writer", "writer.session_initial_draft"
    elif re.fullmatch(r"writer-r\d+", stage):
        role, scenario = "writer", "writer.session_semantic_revision"
    elif stage == "writer-structure-r1":
        role, scenario = "writer", "writer.remediation.style"
    elif stage.startswith("structure-preflight"):
        role, scenario = "reviewer", "reviewer.structure_preflight"
    elif stage.startswith("semantic-review-r"):
        role, scenario = "reviewer", "reviewer.semantic_traceability_test_design"
    elif stage == "format-review-final":
        role, scenario = "reviewer", "reviewer.structure_format_final"
    elif stage == "writer-format-final":
        role, scenario = "writer", "writer.session_format_revision"
    elif stage == "semantic-regression-final":
        role, scenario = "reviewer", "reviewer.semantic_regression"
    else:
        return None

    return NextSession(
        stage=stage,
        role=role,
        scenario=scenario,
        prompt_path=prompt_path,
        sandbox_policy=sandbox_policy_for_role_scenario(role, scenario),
    )


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

    def is_snapshot_candidate(path: Path) -> bool:
        return path.is_file() and not is_snapshot_or_write_scratch_path(
            relative_or_name(path, ft_root)
        )

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
        files.extend(path for path in sorted(test_design_dir.rglob("*")) if is_snapshot_candidate(path))

    outputs_dir = state_path.parent / "outputs"
    if outputs_dir.exists():
        files.extend(path for path in sorted(outputs_dir.rglob("*")) if is_snapshot_candidate(path))

    latest_artifacts = state.get("latest_artifacts")
    if isinstance(latest_artifacts, list):
        for artifact in latest_artifacts:
            artifact_path = resolve_artifact_path(str(artifact), ft_root)
            if artifact_path and artifact_path.exists() and is_snapshot_candidate(artifact_path):
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


def load_openai_codex_runtime(*, required: tuple[str, ...] = ("Codex",)) -> Any:
    try:
        module = __import__("openai_codex", fromlist=list(required))
    except ImportError as exc:
        raise RunnerError(
            "openai-codex is not installed in this Python environment "
            f"({sys.executable}); run real SDK sessions with the project venv, "
            "for example `.venv\\Scripts\\python.exe scripts\\codex_review_cycle_runner.py ...`"
        ) from exc
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        raise RunnerError(
            "openai-codex runtime is incomplete in this Python environment "
            f"({sys.executable}); missing: {', '.join(missing)}"
        )
    return module


def ensure_openai_codex_runtime_available() -> None:
    load_openai_codex_runtime(required=("Codex", "Sandbox", "ApprovalMode"))


def sdk_sandbox(policy: str) -> Any:
    Sandbox = load_openai_codex_runtime(required=("Sandbox",)).Sandbox

    if policy == "read_only":
        return Sandbox.read_only
    if policy == "workspace_write":
        return Sandbox.workspace_write
    if policy == "full_access":
        return Sandbox.full_access
    raise RunnerError(f"Unsupported SDK sandbox policy: {policy}")


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


def structure_preflight_preferred_file_artifacts(
    state: dict[str, Any],
    state_path: Path,
) -> list[str]:
    latest_files: list[str] = []
    ft_root = infer_ft_root(state_path)
    for item in unique_nonempty_strings(
        state.get("canonical_test_cases"),
        state.get("latest_artifacts"),
    ):
        path = resolve_artifact_path(item, ft_root)
        if path is None or not path.is_file():
            continue
        name = path.name
        if "validator-report" in name or "structure-preflight" in name:
            continue
        if any(marker in name for marker in ("timeout-recovery", "completion", "recovery-decision")):
            continue
        latest_files.append(relative_or_name(path, ft_root))
    test_design_dir = resolve_artifact_path(str(state.get("test_design_dir") or ""), ft_root)
    if test_design_dir is not None and test_design_dir.is_dir():
        for name in ("writer-quality-gate.md", "test-design-review.md", "package-test-design-plan.md"):
            path = test_design_dir / name
            if path.exists():
                latest_files.append(relative_or_name(path, ft_root))
    return list(dict.fromkeys(latest_files))


def render_structure_preflight_runtime_contract(
    state: dict[str, Any],
    state_path: Path,
    next_session: NextSession,
) -> str:
    if next_session.scenario != "reviewer.structure_preflight":
        return ""

    latest_files = structure_preflight_preferred_file_artifacts(state, state_path)

    lines = [
        "Structure-preflight bounded runtime contract:",
        "- This stage is a blocking parseability/schema preflight only; do not perform semantic coverage review.",
        "- Do not recursively read directories. If a prompt or state field names a directory, list filenames only first.",
        "- From test-design directories, read only the smallest structure gate files needed, such as writer-quality-gate.md, test-design-review.md, or package-test-design-plan.md.",
        "- Do not read validator-report*.json or other large raw validator reports; use scoped-validator-profile.*.json as the validator evidence source.",
        "- If the required evidence is missing or too broad to inspect safely, record a structure-preflight blocker instead of expanding the search surface.",
    ]
    if latest_files:
        lines.append("- Prefer these exact file artifacts before considering any directory input:")
        lines.extend(f"  - {path}" for path in latest_files)
    return "\n".join(lines)


def prompt_text_for_structure_preflight_session(
    state: dict[str, Any],
    state_path: Path,
    next_session: NextSession,
    instruction_context: dict[str, Any],
) -> str:
    ft_root = infer_ft_root(state_path)
    cycle_dir = state_path.parent
    output_dir = cycle_dir / "outputs"
    prompt_path = resolve_artifact_path(next_session.prompt_path, ft_root)
    preferred_files = structure_preflight_preferred_file_artifacts(state, state_path)
    budget = instruction_context.get("budget", {})
    return "\n".join(
        [
            "Session-based structure-preflight stage.",
            f"cycle_id: {state.get('cycle_id')}",
            f"stage: {next_session.stage}",
            f"role: {next_session.role}",
            f"instruction_scenario: {next_session.scenario}",
            f"cycle_state: {state_path.resolve()}",
            f"ft_root: {ft_root.resolve()}",
            f"active_prompt_path: {prompt_path.resolve() if prompt_path else next_session.prompt_path}",
            "",
            "Slim runtime contract:",
            "- The runner already resolved the instruction context for reviewer.structure_preflight.",
            f"- Resolved context budget: {budget.get('status')} ({budget.get('total_kib')} / {budget.get('limit_kib')} KiB).",
            "- Do not rerun the instruction resolver and do not read the selected instruction files in this SDK turn.",
            "- Use the bounded checks and output paths below as the runtime contract for this preflight.",
            "- Do not recursively read directories and do not read validator-report*.json.",
            "- Do not perform semantic coverage review.",
            "- If structure evidence is missing or too broad to inspect safely, block with a structure finding instead of broadening the search.",
            "",
            "Exact review inputs:",
            *(f"- {path}" for path in preferred_files),
            "",
            "Structure checks:",
            "- Markdown parseability and duplicate wrapper headings.",
            "- Canonical TC runtime fields/sections and continuous TC numbering.",
            "- Required split artifact shape only for the bounded test-design files above.",
            "- Current writer-stage scoped validator evidence from scoped-validator-profile.*.json.",
            "",
            "Required outputs:",
            f"- {relative_or_name(output_dir / f'{next_session.stage}-findings.md', ft_root)}",
            f"- {relative_or_name(output_dir / f'reviewer-session-log.{next_session.stage}.md', ft_root)}",
            f"- {relative_or_name(output_dir / f'agent-decision-log.{next_session.stage}.md', ft_root)}",
            "",
            "State transition:",
            "- If structure passes, update cycle-state.yaml to stage_status: semantic-review-ready and keep semantic_round unchanged.",
            "- If structure blocks, update cycle-state.yaml to stage_status: structure-preflight-blocked and create a writer-structure remediation prompt.",
            "- Keep cycle-state.yaml in runner simple-YAML form with top-level scalar fields plus top-level string lists only.",
            "- Do not edit codex-session-map.yaml; it is owned by the SDK runner.",
        ]
    )


def apply_sdk_diagnostic_safety_contract(prompt: str, output_dir: Path) -> str:
    return "\n".join(
        [
            "Standalone SDK diagnostic safety contract.",
            f"diagnostic_output_dir: {output_dir.resolve()}",
            "- Do not edit cycle-state.yaml, runner.lock.yaml, codex-session-map.yaml, snapshots, or files under fts/.",
            "- If the embedded prompt asks for reviewer artifacts, write diagnostic copies only under diagnostic_output_dir/reviewer-artifacts/.",
            "- If the embedded prompt asks for a state transition, report the intended transition in response.md only.",
            "- This diagnostic turn must not mutate the review cycle.",
            "",
            prompt,
        ]
    )


def prompt_text_for_session(
    state: dict[str, Any],
    state_path: Path,
    next_session: NextSession,
) -> str:
    ft_root = infer_ft_root(state_path)
    prompt_path = resolve_artifact_path(next_session.prompt_path, ft_root)
    if prompt_path is None or not prompt_path.exists():
        raise RunnerError(f"Prompt file does not exist: {next_session.prompt_path}")
    prompt = prompt_path.read_text(encoding="utf-8")
    instruction_context = resolve_instruction_context_for_scenario(next_session.scenario)
    if next_session.scenario == "reviewer.structure_preflight":
        return prompt_text_for_structure_preflight_session(
            state,
            state_path,
            next_session,
            instruction_context,
        )
    runtime_contract = render_structure_preflight_runtime_contract(
        state,
        state_path,
        next_session,
    )
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
            (
                f"draft_test_cases: {resolve_artifact_path(default_writer_draft_test_cases_ref(state_path, next_session.stage), ft_root)}"
                if next_session.role == "writer"
                else f"active_test_cases: {active_test_cases_path(state, state_path)}"
            ),
            "",
            "Runner state contract:",
            "- cycle-state.yaml is the source of truth for this automated chain.",
            "- Before ending the session, update cycle-state.yaml to the next lifecycle status, semantic round and active transition prompt according to session-based-review-cycle-format.md.",
            "- Keep cycle-state.yaml in runner simple-YAML form: top-level scalar fields plus top-level string lists only. Do not write nested maps under latest_artifacts, blocking_reasons, blocking_findings, open_questions, accepted_risks or sessions; put rich detail in sidecar artifacts and list their paths.",
            "- If the active prompt below mentions workflow-state.yaml, update it only as compatibility; do not leave cycle-state.yaml stale.",
            "- Use session-based stage_status values from cycle-state.yaml, not legacy workflow-state.yaml status names.",
            "- Writer sessions must write unsigned test-case drafts to draft_test_cases and record `draft_test_cases: <path>` in cycle-state.yaml; do not create or update the canonical production test-cases file before reviewer sign-off.",
            "- Writer sessions must not set writer-draft-ready or semantic-review-ready while the current scoped validator profile has any error/warning finding; resolve the findings or route to blocked-input with evidence.",
            "- In session-based writer stages, prefer stage-specific output names such as outputs/writer-session-log.<stage>.md and outputs/agent-decision-log.<stage>.md; legacy writer-session-log.md is tolerated only as compatibility evidence.",
            "- Do not edit codex-session-map.yaml; it is owned by the SDK runner.",
            "",
            render_instruction_context_contract(next_session.scenario, instruction_context),
            "",
            runtime_contract,
            "" if runtime_contract else "",
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


TEST_CASE_HEADING_RE = re.compile(r"(?m)^##\s+(TC-[A-Za-z0-9_-]+)(?:\s+.*)?$")
NONCANONICAL_TEST_CASE_HEADING_RE = re.compile(r"(?m)^#{3,6}\s+(TC-[A-Za-z0-9_-]+)(?:\s+.*)?$")
TEST_CASE_ID_RE = re.compile(r"\bTC-[A-Za-z0-9_-]+\b")
MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"(?m)^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
RUNTIME_FIELD_PATTERNS = {
    "title": re.compile(r"(?im)^\s*\*\*(?:Title|\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435):\*\*"),
    "type": re.compile(r"(?im)^\s*\*\*(?:Type|\u0422\u0438\u043f):\*\*"),
    "priority": re.compile(r"(?im)^\s*\*\*(?:Priority|\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442):\*\*"),
    "package_id": re.compile(r"(?im)^\s*\*\*package_id:\*\*"),
    "traceability": re.compile(r"(?im)^\s*\*\*(?:Traceability|\u0422\u0440\u0430\u0441\u0441\u0438\u0440\u043e\u0432\u043a\u0430):\*\*"),
}
RUNTIME_SECTION_PATTERNS = {
    "preconditions": re.compile(r"(?im)^###\s+(?:Preconditions|\u041f\u0440\u0435\u0434\u0443\u0441\u043b\u043e\u0432\u0438\u044f)\s*$"),
    "test_data": re.compile(r"(?im)^###\s+(?:Test Data|\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435)\s*$"),
    "steps": re.compile(r"(?im)^###\s+(?:Steps|\u0428\u0430\u0433\u0438)\s*$"),
    "expected_result": re.compile(
        r"(?im)^###\s+(?:Expected Result|\u041e\u0436\u0438\u0434\u0430\u0435\u043c\u044b\u0439 "
        r"\u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442|\u0418\u0442\u043e\u0433\u043e\u0432\u044b\u0439 "
        r"\u043e\u0436\u0438\u0434\u0430\u0435\u043c\u044b\u0439 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442)\s*$"
    ),
    "postconditions": re.compile(r"(?im)^###\s+(?:Postconditions|\u041f\u043e\u0441\u0442\u0443\u0441\u043b\u043e\u0432\u0438\u044f)\s*$"),
}
REQUIRED_STRUCTURE_PREFLIGHT_DESIGN_FILES = (
    "writer-quality-gate.md",
    "test-design-review.md",
    "package-test-design-plan.md",
)
DETERMINISTIC_STRUCTURE_THREAD_ID = "deterministic-structure-preflight"


def make_structure_finding(
    finding_id: str,
    title: str,
    details: str,
    evidence: Sequence[str],
    recommended_action: str,
    *,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "title": title,
        "details": details,
        "evidence": list(evidence),
        "recommended_action": recommended_action,
    }


def split_test_case_blocks(markdown: str) -> list[tuple[str, str]]:
    matches = list(TEST_CASE_HEADING_RE.finditer(markdown))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        blocks.append((match.group(1), markdown[match.start() : end]))
    return blocks


def test_case_numeric_parts(tc_id: str) -> tuple[str, int, int] | None:
    match = re.match(r"^(.*?)(\d+)$", tc_id)
    if not match:
        return None
    numeric = match.group(2)
    return match.group(1), int(numeric), len(numeric)


def find_writer_scoped_validator_profile(state: dict[str, Any], state_path: Path) -> Path | None:
    ft_root = infer_ft_root(state_path)
    candidates: list[Path] = []
    for artifact in state.get("latest_artifacts") or []:
        if not isinstance(artifact, str):
            continue
        name = Path(artifact).name
        if name.startswith("scoped-validator-profile.") and name.endswith(".json"):
            candidates.append(resolve_artifact_path(artifact, ft_root))
    output_dir = state_path.parent / "outputs"
    if output_dir.exists():
        current_stage = str(state.get("current_stage") or "").strip()
        if current_stage:
            candidates.append(output_dir / f"scoped-validator-profile.{current_stage}.json")
        candidates.extend(sorted(output_dir.glob("scoped-validator-profile.writer*.json")))
        candidates.extend(sorted(output_dir.glob("scoped-validator-profile.structure-preflight*.json")))
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.exists():
            return candidate
    return None


def validate_scoped_writer_profile(
    state: dict[str, Any],
    state_path: Path,
    scope_slug: str,
) -> list[dict[str, Any]]:
    profile_path = find_writer_scoped_validator_profile(state, state_path)
    if profile_path is None:
        return [
            make_structure_finding(
                "structure-preflight-validator-profile-missing",
                "Writer scoped validator profile is missing",
                "No scoped-validator-profile for the current structure-preflight stage or preceding writer stage was found for the current scope.",
                ["outputs/scoped-validator-profile.<current-stage>.json", "outputs/scoped-validator-profile.writer*.json"],
                "Run the scoped validator for the current cycle state and attach the generated profile before structure preflight.",
            )
        ]
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [
            make_structure_finding(
                "structure-preflight-validator-profile-unreadable",
                "Writer scoped validator profile is not parseable",
                f"{profile_path.name} cannot be read as JSON: {exc}",
                [str(profile_path)],
                "Regenerate the scoped validator profile from runner validation.",
            )
        ]

    findings: list[dict[str, Any]] = []
    command = str(profile.get("command") or "")
    if "bootstrap before runner validate" in command or "must be overwritten" in command:
        findings.append(
            make_structure_finding(
                "structure-preflight-validator-profile-bootstrap",
                "Writer scoped validator profile is bootstrap evidence",
                "The profile was seeded as bootstrap evidence and is not valid proof of a clean writer stage.",
                [relative_or_name(profile_path, infer_ft_root(state_path))],
                "Replace it with a runner-generated scoped validator profile for the current writer stage.",
            )
        )
    profile_scope = str(profile.get("scope_slug") or "")
    if profile_scope and profile_scope != scope_slug:
        findings.append(
            make_structure_finding(
                "structure-preflight-validator-profile-scope-mismatch",
                "Writer scoped validator profile belongs to another scope",
                f"Profile scope_slug is {profile_scope!r}, expected {scope_slug!r}.",
                [relative_or_name(profile_path, infer_ft_root(state_path))],
                "Regenerate the scoped profile using this cycle state.",
            )
        )
    profile_stage = str(profile.get("current_stage") or "")
    allowed_profile_stages = ("writer", "structure-preflight")
    if profile_stage and not profile_stage.startswith(allowed_profile_stages):
        findings.append(
            make_structure_finding(
                "structure-preflight-validator-profile-stage-mismatch",
                "Scoped validator profile is not from a writer or structure-preflight stage",
                f"Profile current_stage is {profile_stage!r}; structure preflight requires post-writer scoped validator proof.",
                [relative_or_name(profile_path, infer_ft_root(state_path))],
                "Attach the scoped profile generated immediately after writer draft/remediation or for the deterministic structure-preflight state.",
            )
        )
    unresolved = profile.get("unresolved_warning_error_count")
    try:
        unresolved_count = int(unresolved)
    except (TypeError, ValueError):
        unresolved_count = -1
    if unresolved_count != 0:
        current_findings = profile.get("current_scope_findings") or []
        finding_ids = [
            str(item.get("id") or item.get("finding_id") or "")
            for item in current_findings
            if isinstance(item, dict)
        ]
        finding_ids = [item for item in finding_ids if item]
        details = f"unresolved_warning_error_count is {unresolved!r}; expected 0."
        if finding_ids:
            details += f" Current finding ids: {', '.join(finding_ids[:10])}."
        findings.append(
            make_structure_finding(
                "structure-preflight-validator-profile-has-unresolved-findings",
                "Writer scoped validator profile has unresolved warning/error findings",
                details,
                [relative_or_name(profile_path, infer_ft_root(state_path))],
                "Resolve or explicitly waive scoped validator findings before structure preflight.",
            )
        )
    return findings


def evaluate_test_case_markdown_structure(
    state: dict[str, Any],
    state_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    ft_root = infer_ft_root(state_path)
    active_ref = active_test_cases_ref(state, state_path)
    active_path = resolve_artifact_path(active_ref, ft_root)
    checked_paths = [active_ref or relative_or_name(active_path, ft_root)]
    if active_path is None or not active_path.exists():
        return (
            [
                make_structure_finding(
                    "structure-preflight-canonical-test-cases-missing",
                    "Active test case file is missing",
                    f"active test-case artifact points to {active_ref!r}, but the file does not exist.",
                    [active_ref],
                    "Create or restore draft_test_cases before reviewer preflight, or promote a signed-off canonical test-case file.",
                )
            ],
            checked_paths,
        )
    markdown = active_path.read_text(encoding="utf-8")
    findings: list[dict[str, Any]] = []
    noncanonical_headings = [match.group(1) for match in NONCANONICAL_TEST_CASE_HEADING_RE.finditer(markdown)]
    if noncanonical_headings:
        findings.append(
            make_structure_finding(
                "structure-preflight-test-case-noncanonical-heading-level",
                "Test cases use noncanonical heading level",
                f"TC headings must be level 2. Noncanonical headings: {', '.join(noncanonical_headings[:20])}.",
                [relative_or_name(active_path, ft_root)],
                "Rewrite every test case heading as '## TC-...'.",
            )
        )
    blocks = split_test_case_blocks(markdown)
    if not blocks:
        findings.append(
            make_structure_finding(
                "structure-preflight-test-case-blocks-missing",
                "No canonical test case blocks were found",
                "The canonical test case file must contain one or more '## TC-...' blocks.",
                [relative_or_name(active_path, ft_root)],
                "Add executable test case blocks with canonical TC IDs.",
            )
        )
        return findings, checked_paths

    tc_ids = [tc_id for tc_id, _block in blocks]
    duplicates = sorted({tc_id for tc_id in tc_ids if tc_ids.count(tc_id) > 1})
    if duplicates:
        findings.append(
            make_structure_finding(
                "structure-preflight-test-case-duplicate-ids",
                "Duplicate test case IDs were found",
                f"Duplicate TC IDs: {', '.join(duplicates)}.",
                [relative_or_name(active_path, ft_root)],
                "Deduplicate or renumber test case blocks so every TC ID is unique.",
            )
        )

    numeric_parts = [test_case_numeric_parts(tc_id) for tc_id in tc_ids]
    if any(part is None for part in numeric_parts):
        invalid = [tc_id for tc_id, part in zip(tc_ids, numeric_parts) if part is None]
        findings.append(
            make_structure_finding(
                "structure-preflight-test-case-id-not-numeric",
                "Test case IDs do not end with a numeric sequence",
                f"IDs without numeric suffix: {', '.join(invalid)}.",
                [relative_or_name(active_path, ft_root)],
                "Use stable IDs ending with a zero-padded numeric suffix.",
            )
        )
    else:
        prefixes = {part[0] for part in numeric_parts if part is not None}
        widths = {part[2] for part in numeric_parts if part is not None}
        numbers = [part[1] for part in numeric_parts if part is not None]
        expected_numbers = list(range(min(numbers), max(numbers) + 1))
        if len(prefixes) != 1 or len(widths) != 1 or numbers != expected_numbers:
            findings.append(
                make_structure_finding(
                    "structure-preflight-test-case-id-sequence-not-contiguous",
                    "Test case IDs are not a contiguous ordered sequence",
                    f"Actual IDs: {', '.join(tc_ids)}.",
                    [relative_or_name(active_path, ft_root)],
                    "Renumber test cases into one contiguous ordered sequence without gaps.",
                )
            )

    wrapper_headings = [
        heading.strip()
        for heading in re.findall(r"(?m)^##\s+(.+?)\s*$", markdown)
        if not heading.strip().startswith("TC-")
    ]
    duplicate_wrappers = sorted({heading for heading in wrapper_headings if wrapper_headings.count(heading) > 1})
    if duplicate_wrappers:
        findings.append(
            make_structure_finding(
                "structure-preflight-duplicate-wrapper-headings",
                "Duplicate wrapper headings were found",
                f"Duplicate non-TC H2 headings: {', '.join(duplicate_wrappers)}.",
                [relative_or_name(active_path, ft_root)],
                "Remove duplicate wrapper sections or merge their content.",
            )
        )

    for tc_id, block in blocks:
        missing = [
            name
            for name, pattern in {**RUNTIME_FIELD_PATTERNS, **RUNTIME_SECTION_PATTERNS}.items()
            if not pattern.search(block)
        ]
        if missing:
            findings.append(
                make_structure_finding(
                    "structure-preflight-test-case-runtime-field-missing",
                    f"{tc_id} is missing required runtime fields",
                    f"Missing fields/sections: {', '.join(missing)}.",
                    [f"{relative_or_name(active_path, ft_root)}#{tc_id}"],
                    "Add every required runtime field and section to this test case.",
                )
            )

    summary_match = re.search(r"(?im)^\|\s*executable_test_cases\s*\|\s*([^|]+)\|", markdown)
    if summary_match:
        summary_ids = TEST_CASE_ID_RE.findall(summary_match.group(1))
        if summary_ids and (summary_ids[0] != tc_ids[0] or summary_ids[-1] != tc_ids[-1]):
            findings.append(
                make_structure_finding(
                    "structure-preflight-coverage-summary-range-stale",
                    "Coverage Summary executable case range is stale",
                    f"Coverage Summary says {summary_ids[0]}..{summary_ids[-1]}, actual executable range is {tc_ids[0]}..{tc_ids[-1]}.",
                    [relative_or_name(active_path, ft_root)],
                    "Update Coverage Summary executable_test_cases to match the canonical TC range.",
                )
            )
    return findings, checked_paths


def evaluate_bounded_design_artifacts(
    state: dict[str, Any],
    state_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    ft_root = infer_ft_root(state_path)
    design_dir_ref = str(state.get("test_design_dir") or "")
    design_dir = resolve_artifact_path(design_dir_ref, ft_root)
    checked_paths: list[str] = []
    findings: list[dict[str, Any]] = []
    for file_name in REQUIRED_STRUCTURE_PREFLIGHT_DESIGN_FILES:
        artifact_path = design_dir / file_name
        checked_paths.append(relative_or_name(artifact_path, ft_root))
        if not artifact_path.exists():
            findings.append(
                make_structure_finding(
                    f"structure-preflight-design-artifact-missing-{file_name.removesuffix('.md')}",
                    "Required bounded test-design artifact is missing",
                    f"{file_name} was not found under test_design_dir.",
                    [relative_or_name(artifact_path, ft_root)],
                    "Regenerate the bounded writer design artifacts before structure preflight.",
                )
            )
            continue
        text = artifact_path.read_text(encoding="utf-8")
        if not text.strip() or not re.search(r"(?m)^#{1,3}\s+\S", text) or not MARKDOWN_TABLE_SEPARATOR_RE.search(text):
            findings.append(
                make_structure_finding(
                    f"structure-preflight-design-artifact-invalid-{file_name.removesuffix('.md')}",
                    "Required bounded test-design artifact has invalid markdown/table form",
                    f"{file_name} must be non-empty markdown with headings and at least one table.",
                    [relative_or_name(artifact_path, ft_root)],
                    "Rewrite the artifact in the expected bounded markdown/table format.",
                )
            )
    return findings, checked_paths


def evaluate_deterministic_structure_preflight(
    state: dict[str, Any],
    state_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    scope_slug = str(state.get("scope_slug") or "")
    findings: list[dict[str, Any]] = []
    checked_paths: list[str] = []
    tc_findings, tc_paths = evaluate_test_case_markdown_structure(state, state_path)
    design_findings, design_paths = evaluate_bounded_design_artifacts(state, state_path)
    profile_findings = validate_scoped_writer_profile(state, state_path, scope_slug)
    findings.extend(tc_findings)
    findings.extend(design_findings)
    findings.extend(profile_findings)
    checked_paths.extend(tc_paths)
    checked_paths.extend(design_paths)
    profile_path = find_writer_scoped_validator_profile(state, state_path)
    if profile_path:
        checked_paths.append(relative_or_name(profile_path, infer_ft_root(state_path)))
    return findings, unique_nonempty_strings(checked_paths)


def render_structure_preflight_findings(stage: str, findings: Sequence[dict[str, Any]], checked_paths: Sequence[str]) -> str:
    lines = [
        f"# Structure preflight findings: {stage}",
        "",
        f"status: {'blocked' if findings else 'passed'}",
        f"finding_count: {len(findings)}",
        "",
        "## Checked artifacts",
    ]
    lines.extend(f"- `{path}`" for path in checked_paths)
    lines.extend(["", "## Findings"])
    if not findings:
        lines.append("- none")
    for finding in findings:
        lines.extend(
            [
                f"### {finding['id']}",
                "",
                f"- severity: `{finding['severity']}`",
                f"- title: {finding['title']}",
                f"- details: {finding['details']}",
                "- evidence:",
            ]
        )
        lines.extend(f"  - `{item}`" for item in finding.get("evidence", []))
        lines.extend(["- recommended_action:", f"  - {finding['recommended_action']}", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_structure_preflight_session_log(
    stage: str,
    *,
    status_after: str,
    findings: Sequence[dict[str, Any]],
    checked_paths: Sequence[str],
    started_at_epoch: int,
    completed_at_epoch: int,
) -> str:
    lines = [
        f"# Reviewer session log: {stage}",
        "",
        "- execution_mode: `deterministic`",
        f"- stage_status_after: `{status_after}`",
        f"- started_at_epoch: `{started_at_epoch}`",
        f"- completed_at_epoch: `{completed_at_epoch}`",
        f"- finding_count: `{len(findings)}`",
        "",
        "## Deterministic checks",
        "- canonical TC markdown structure",
        "- TC ID uniqueness and contiguous sequence",
        "- duplicate wrapper headings",
        "- required runtime fields and sections",
        "- bounded test-design artifact presence and markdown/table form",
        "- writer-stage scoped validator profile validity",
        "- validator-report*.json intentionally ignored",
        "",
        "## Evidence",
    ]
    lines.extend(f"- `{path}`" for path in checked_paths)
    return "\n".join(lines).rstrip() + "\n"


def render_structure_preflight_decision_log(
    stage: str,
    *,
    status_after: str,
    findings: Sequence[dict[str, Any]],
    prompt_path: str,
) -> str:
    decision = "route to semantic review" if not findings else "block for writer structure remediation"
    lines = [
        f"# Agent decision log: {stage}",
        "",
        "## Decision",
        f"- decision: {decision}",
        f"- resulting_stage_status: `{status_after}`",
        f"- active_transition_prompt: `{prompt_path}`",
        "",
        "## Rationale",
        "- Structure preflight is a deterministic runner-owned gate.",
        "- Semantic quality remains delegated to the next SDK reviewer stage.",
        "- Blocking findings require writer remediation before semantic review.",
        "",
        "## Risks",
    ]
    if findings:
        lines.append("- Current draft is not structurally safe to route to semantic review.")
    else:
        lines.append("- Deterministic checks do not replace semantic traceability/test-design review.")
    return "\n".join(lines).rstrip() + "\n"


def render_writer_structure_prompt(stage: str, findings: Sequence[dict[str, Any]]) -> str:
    lines = [
        "# Writer structure remediation",
        "",
        f"Resolve deterministic structure-preflight blockers from `{stage}`.",
        "",
        "## Blocking findings",
    ]
    for finding in findings:
        lines.extend(
            [
                f"- `{finding['id']}`: {finding['title']}",
                f"  Evidence: {', '.join(f'`{item}`' for item in finding.get('evidence', []))}",
                f"  Action: {finding['recommended_action']}",
            ]
        )
    lines.extend(
        [
            "",
            "After remediation, update the writer artifacts and scoped validator profile, then return the cycle to writer-draft-ready.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_semantic_review_prompt(stage: str) -> str:
    return "\n".join(
        [
            "# Semantic traceability and test-design review",
            "",
            f"Structure preflight `{stage}` passed deterministically.",
            "Run reviewer.semantic_traceability_test_design against the current scope.",
            "Do not repeat runner-owned structure checks except where they affect semantic coverage.",
            "Write reviewer findings, session log, decision log and update cycle-state.yaml according to the session lifecycle.",
            "",
        ]
    )


BOUNDED_SEMANTIC_ALLOWED_FILES = (
    "package-test-design-plan.md",
    "atomic-requirements-ledger.md",
    "coverage-map.md",
    "test-design-decision-table.md",
    "test-design-applicability-matrix.md",
    "fixture-catalog.md",
    "dictionary-inventory.md",
)
BOUNDED_SEMANTIC_STAGE_STATUSES = {"semantic-revision-needed", "format-review-ready"}
BOUNDED_SEMANTIC_BLOCKING_SEVERITIES = {"error", "warning"}
BOUNDED_SEMANTIC_MATRIX_COLUMNS = (
    "atom_id",
    "source_ref",
    "coverage_status",
    "covered_by_tc",
    "notes",
)


def semantic_round_for_stage(stage: str) -> int:
    match = re.search(r"semantic-review-r(\d+)", stage)
    if not match:
        return 1
    return int(match.group(1))


def semantic_session_from_active_prompt(state: dict[str, Any]) -> NextSession | None:
    prompt_path = str(state.get("active_transition_prompt") or "")
    match = re.search(r"semantic-review-r(\d+)", prompt_path)
    if not match:
        return None
    return NextSession(
        stage=f"semantic-review-r{match.group(1)}",
        role="reviewer",
        scenario="reviewer.semantic_traceability_test_design",
        prompt_path=prompt_path,
        sandbox_policy="read_only",
    )


def bounded_semantic_artifact_paths(
    state: dict[str, Any],
    state_path: Path,
    *,
    cwd_base: Path | None = None,
) -> list[str]:
    ft_root = infer_ft_root(state_path)
    path_base = cwd_base or ft_root.parent.parent
    paths: list[str] = []
    canonical = resolve_artifact_path(str(state.get("canonical_test_cases") or ""), ft_root)
    if canonical is not None and canonical.exists():
        paths.append(relative_or_name(canonical, path_base))
    test_design_dir = resolve_artifact_path(str(state.get("test_design_dir") or ""), ft_root)
    if test_design_dir is not None and test_design_dir.is_dir():
        for file_name in BOUNDED_SEMANTIC_ALLOWED_FILES:
            path = test_design_dir / file_name
            if path.exists():
                paths.append(relative_or_name(path, path_base))
    return unique_nonempty_strings(paths)


def render_bounded_semantic_review_prompt(
    state: dict[str, Any],
    state_path: Path,
    next_session: NextSession,
    *,
    cwd_base: Path | None = None,
) -> str:
    allowed_files = bounded_semantic_artifact_paths(state, state_path, cwd_base=cwd_base)
    lines = [
        "# Bounded semantic traceability and test-design review",
        "",
        "This is a bounded read-only reviewer turn.",
        "Do not edit files. Do not update cycle-state.yaml. Do not create reviewer artifacts.",
        "Do not recursively read directories. Do not scan unrelated files. Read only the exact files listed below.",
        "",
        "## Stage",
        f"- stage: {next_session.stage}",
        f"- scenario: {next_session.scenario}",
        f"- cycle_id: {state.get('cycle_id') or ''}",
        f"- scope_slug: {state.get('scope_slug') or ''}",
        "",
        "## Allowed Files",
    ]
    lines.extend(f"- {path}" for path in allowed_files)
    lines.extend(["", "## Open Questions"])
    open_questions = unique_nonempty_strings(state.get("open_questions"))
    lines.extend(f"- {item}" for item in open_questions) if open_questions else lines.append("- none")
    lines.extend(["", "## Accepted Risks"])
    accepted_risks = unique_nonempty_strings(state.get("accepted_risks"))
    lines.extend(f"- {item}" for item in accepted_risks) if accepted_risks else lines.append("- none")
    lines.extend(
        [
            "",
            "## Required Output",
            "Return fenced JSON only. Do not include prose outside the JSON fence.",
            "Use this exact top-level shape:",
            "```json",
            "{",
            '  "coverage_summary": {',
            '    "executable_tc_count": 0,',
            '    "atoms_total": 0,',
            '    "atoms_covered": 0,',
            '    "gaps": []',
            "  },",
            '  "traceability_matrix_rows": [',
            '    {"atom_id": "ATOM-001", "source_ref": "SRC-001", "coverage_status": "covered", "covered_by_tc": "TC-001", "notes": ""}',
            "  ],",
            '  "findings": [',
            '    {"id": "SEM-001", "review_mode": "traceability", "severity": "warning", "category": "coverage", "test_case_id": "TC-001", "coverage_gap": "", "traceability_ref": "ATOM-001", "problem": "", "evidence": "", "required_change": "", "source_reference": "", "status": "open"}',
            "  ],",
            '  "human_summary": "",',
            '  "recommended_stage_status": "format-review-ready"',
            "}",
            "```",
            "",
            "Allowed recommended_stage_status values: semantic-revision-needed, format-review-ready.",
            "Use severity error or warning only for findings that must block progress.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def extract_fenced_json(text: str) -> dict[str, Any]:
    stripped = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    candidate = fence.group(1) if fence else stripped
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"Bounded semantic reviewer returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunnerError("Bounded semantic reviewer JSON must be an object")
    return payload


def normalize_bounded_semantic_response(payload: dict[str, Any]) -> dict[str, Any]:
    coverage_summary = payload.get("coverage_summary")
    if not isinstance(coverage_summary, dict):
        coverage_summary = {}
    rows = payload.get("traceability_matrix_rows")
    if not isinstance(rows, list):
        rows = []
    normalized_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized_row = dict(row)
        if not normalized_row.get("atom_id") and normalized_row.get("requirement_id"):
            normalized_row["atom_id"] = normalized_row["requirement_id"]
        if not normalized_row.get("source_ref") and normalized_row.get("requirement_summary"):
            normalized_row["source_ref"] = normalized_row["requirement_summary"]
        if not normalized_row.get("covered_by_tc") and normalized_row.get("covered_by_tc_ids"):
            normalized_row["covered_by_tc"] = normalized_row["covered_by_tc_ids"]
        if not normalized_row.get("notes"):
            notes = unique_nonempty_strings(
                normalized_row.get("evidence"),
                normalized_row.get("finding_ids"),
            )
            normalized_row["notes"] = "; ".join(notes)
        normalized_rows.append(normalized_row)
    findings = payload.get("findings")
    if not isinstance(findings, list):
        findings = []
    normalized_findings = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        normalized = dict(finding)
        if not normalized.get("problem") and normalized.get("title"):
            normalized["problem"] = normalized["title"]
        if not normalized.get("traceability_ref") and normalized.get("requirement_id"):
            normalized["traceability_ref"] = normalized["requirement_id"]
        if not normalized.get("test_case_id") and normalized.get("tc_ids"):
            tc_ids = normalized["tc_ids"]
            normalized["test_case_id"] = (
                ", ".join(str(item) for item in tc_ids)
                if isinstance(tc_ids, list)
                else str(tc_ids)
            )
        if not normalized.get("required_change") and normalized.get("recommendation"):
            normalized["required_change"] = normalized["recommendation"]
        normalized_findings.append(normalized)
    recommended = str(payload.get("recommended_stage_status") or "").strip()
    if recommended not in BOUNDED_SEMANTIC_STAGE_STATUSES:
        recommended = "semantic-revision-needed" if normalized_findings else "format-review-ready"
    if any(
        str(finding.get("severity") or "").lower() in BOUNDED_SEMANTIC_BLOCKING_SEVERITIES
        for finding in normalized_findings
    ):
        recommended = "semantic-revision-needed"
    return {
        "coverage_summary": coverage_summary,
        "traceability_matrix_rows": normalized_rows,
        "findings": normalized_findings,
        "human_summary": str(payload.get("human_summary") or "").strip(),
        "recommended_stage_status": recommended,
    }


def render_bounded_semantic_findings(stage: str, response: dict[str, Any]) -> str:
    findings = response["findings"]
    lines = [
        f"# Round {semantic_round_for_stage(stage)} Findings",
        "",
        "## Human Summary",
        response["human_summary"] or "No additional summary provided.",
        "",
        "## Coverage Summary",
    ]
    for key, value in response["coverage_summary"].items():
        lines.append(f"- `{key}`: {value}")
    if not response["coverage_summary"]:
        lines.append("- not provided")
    lines.extend(["", "## Findings"])
    if not findings:
        lines.append("- none")
    for index, finding in enumerate(findings, start=1):
        finding_id = str(finding.get("id") or f"SEM-{index:03d}")
        lines.extend(
            [
                f"### {finding_id}",
                "",
                f"- review_mode: `{finding.get('review_mode') or 'semantic'}`",
                f"- severity: `{finding.get('severity') or 'info'}`",
                f"- category: `{finding.get('category') or 'semantic-review'}`",
                f"- test_case_id: `{finding.get('test_case_id') or ''}`",
                f"- coverage_gap: `{finding.get('coverage_gap') or ''}`",
                f"- traceability_ref: `{finding.get('traceability_ref') or ''}`",
                f"- problem: {finding.get('problem') or ''}",
                f"- evidence: {finding.get('evidence') or ''}",
                f"- required_change: {finding.get('required_change') or ''}",
                f"- source_reference: `{finding.get('source_reference') or ''}`",
                f"- status: `{finding.get('status') or 'open'}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def matrix_cell(value: Any) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text.replace("|", "\\|")


def render_bounded_semantic_matrix(response: dict[str, Any]) -> str:
    lines = [
        "# Round Traceability Matrix",
        "",
        "| " + " | ".join(BOUNDED_SEMANTIC_MATRIX_COLUMNS) + " |",
        "| " + " | ".join("---" for _ in BOUNDED_SEMANTIC_MATRIX_COLUMNS) + " |",
    ]
    for row in response["traceability_matrix_rows"]:
        lines.append(
            "| "
            + " | ".join(matrix_cell(row.get(column)) for column in BOUNDED_SEMANTIC_MATRIX_COLUMNS)
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_bounded_semantic_matrix_xlsx(path: Path, rows: list[dict[str, Any]]) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RunnerError("openpyxl is required to write traceability matrix .xlsx artifacts") from exc
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "traceability"
    sheet.append(list(BOUNDED_SEMANTIC_MATRIX_COLUMNS))
    for row in rows:
        sheet.append([str(row.get(column) or "") for column in BOUNDED_SEMANTIC_MATRIX_COLUMNS])
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def render_bounded_semantic_session_log(
    next_session: NextSession,
    *,
    status_after: str,
    response: dict[str, Any] | None,
    checked_paths: Sequence[str],
    started_at_epoch: int,
    completed_at_epoch: int,
    thread_id: str,
    turn_id: str,
) -> str:
    lines = [
        f"# Reviewer session log: {next_session.stage}",
        "",
        "- execution_mode: `bounded-sdk`",
        f"- stage_status_after: `{status_after}`",
        f"- thread_id: `{thread_id}`",
        f"- turn_id: `{turn_id}`",
        f"- started_at_epoch: `{started_at_epoch}`",
        f"- completed_at_epoch: `{completed_at_epoch}`",
        "",
        "## Checked artifacts",
    ]
    lines.extend(f"- `{path}`" for path in checked_paths)
    if response is not None:
        lines.extend(
            [
                "",
                "## Result",
                f"- finding_count: `{len(response['findings'])}`",
                f"- recommended_stage_status: `{response['recommended_stage_status']}`",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_semantic_decision_log(
    next_session: NextSession,
    *,
    status_after: str,
    response: dict[str, Any] | None,
    prompt_path: str,
) -> str:
    blocker_count = 0
    if response is not None:
        blocker_count = sum(
            1
            for finding in response["findings"]
            if str(finding.get("severity") or "").lower() in BOUNDED_SEMANTIC_BLOCKING_SEVERITIES
        )
    return "\n".join(
        [
            f"# Agent decision log: {next_session.stage}",
            "",
            f"- decision: route to `{status_after}`",
            f"- blocking_finding_count: `{blocker_count}`",
            f"- active_transition_prompt: `{prompt_path}`",
            "",
            "## Rationale",
            "- Semantic review ran as a bounded read-only SDK turn.",
            "- Runner wrote reviewer artifacts and lifecycle state from the structured response.",
            "- Any error/warning finding blocks progress to writer revision.",
            "",
        ]
    )


def render_writer_semantic_prompt(next_session: NextSession, findings_path: str) -> str:
    round_no = semantic_round_for_stage(next_session.stage)
    return "\n".join(
        [
            f"# Writer semantic revision R{round_no + 1}",
            "",
            f"Resolve blocking semantic review findings from `{findings_path}`.",
            "Update canonical test cases and bounded test-design artifacts only where required by findings.",
            "Preserve traceability refs and explain any split/merge of TC or ATOM references in the writer response.",
            "",
        ]
    )


def render_structure_format_prompt(next_session: NextSession) -> str:
    return "\n".join(
        [
            "# Structure and format final review",
            "",
            f"Semantic review `{next_session.stage}` completed without blocking findings.",
            "Run reviewer.structure_format_final against the current scope.",
            "Verify final structure, formatting, numbering, grouping and reviewer sign-off prerequisites.",
            "",
        ]
    )


BOUNDED_REVIEWER_ALLOWED_STATUSES = {
    "reviewer.scope_gap_review": {"scope-gap-review-passed", "scope-ready-for-writer", "blocked-input"},
    "reviewer.structure_format_final": {"final-regression-ready", "format-revision-needed", "blocked-input"},
    "reviewer.semantic_regression": {"signed-off", "round-cap-reached", "blocked-input"},
}
BOUNDED_REVIEWER_PASS_STATUS = {
    "reviewer.scope_gap_review": "scope-ready-for-writer",
    "reviewer.structure_format_final": "final-regression-ready",
    "reviewer.semantic_regression": "signed-off",
}
BOUNDED_REVIEWER_FINDING_STATUS = {
    "reviewer.scope_gap_review": "blocked-input",
    "reviewer.structure_format_final": "format-revision-needed",
    "reviewer.semantic_regression": "round-cap-reached",
}


def bounded_reviewer_artifact_paths(
    state: dict[str, Any],
    state_path: Path,
    next_session: NextSession,
    *,
    cwd_base: Path | None = None,
) -> list[str]:
    ft_root = infer_ft_root(state_path)
    path_base = cwd_base or ft_root.parent.parent
    if next_session.scenario == "reviewer.scope_gap_review":
        repo_root = ft_root.parent.parent
        refs = unique_nonempty_strings(state.get("scope_review_inputs"))
        prompt_ref = normalize_artifact_path_text(state.get("active_transition_prompt"))
        prompt_path = resolve_artifact_path(prompt_ref, ft_root)
        if not refs and prompt_path is not None and prompt_path.is_file():
            prompt_text = prompt_path.read_text(encoding="utf-8")
            refs = unique_nonempty_strings(re.findall(r"`([^`\r\n]+)`", prompt_text))
        paths: list[str] = []
        if prompt_path is not None and prompt_path.is_file():
            paths.append(relative_or_name(prompt_path, path_base))
        for ref in refs:
            normalized = normalize_artifact_path_text(ref)
            candidate = repo_root / normalized if normalized.startswith("fts/") else ft_root / normalized
            if candidate.is_file():
                paths.append(relative_or_name(candidate, path_base))
        return unique_nonempty_strings(paths)

    paths: list[str] = []
    active_test_cases = active_test_cases_path(state, state_path)
    if active_test_cases.exists():
        paths.append(relative_or_name(active_test_cases, path_base))
    test_design_dir = resolve_artifact_path(str(state.get("test_design_dir") or ""), ft_root)
    if test_design_dir is not None and test_design_dir.is_dir():
        for path in sorted(test_design_dir.glob("*.md")):
            paths.append(relative_or_name(path, path_base))
    for artifact in unique_nonempty_strings(state.get("latest_artifacts")):
        path = resolve_artifact_path(artifact, ft_root)
        if path is not None and path.exists() and path.is_file():
            paths.append(relative_or_name(path, path_base))
    return unique_nonempty_strings(paths)


def render_bounded_reviewer_prompt(
    state: dict[str, Any],
    state_path: Path,
    next_session: NextSession,
    *,
    cwd_base: Path | None = None,
) -> str:
    allowed_files = bounded_reviewer_artifact_paths(
        state,
        state_path,
        next_session,
        cwd_base=cwd_base,
    )
    allowed_statuses = sorted(BOUNDED_REVIEWER_ALLOWED_STATUSES[next_session.scenario])
    lines = [
        "# Bounded reviewer stage",
        "",
        "This is a bounded read-only reviewer turn.",
        "Do not edit files. Do not update cycle-state.yaml. Do not create reviewer artifacts.",
        "Do not recursively read directories. Read only the exact files listed below.",
        "",
        "## Stage",
        f"- stage: {next_session.stage}",
        f"- scenario: {next_session.scenario}",
        f"- cycle_id: {state.get('cycle_id') or ''}",
        f"- scope_slug: {state.get('scope_slug') or ''}",
        "",
        "## Allowed Files",
    ]
    lines.extend(f"- {path}" for path in allowed_files) if allowed_files else lines.append("- none")
    lines.extend(
        [
            "",
            "## Required Output",
            "Return fenced JSON only. Do not include prose outside the JSON fence.",
            "Use this exact top-level shape:",
            "```json",
            "{",
            '  "findings": [',
            (
                '    {"id": "REV-001", "severity": "warning", "category": "scope-gap", '
                '"gap_id": "GAP-001", "problem": "", "evidence": "", "required_change": "", '
                '"source_reference": "", "status": "open"}'
                if next_session.scenario == "reviewer.scope_gap_review"
                else '    {"id": "REV-001", "severity": "warning", "category": "review", '
                '"test_case_id": "TC-001", "problem": "", "evidence": "", "required_change": "", '
                '"source_reference": "", "status": "open"}'
            ),
            "  ],",
            '  "human_summary": "",',
            f'  "recommended_stage_status": "{BOUNDED_REVIEWER_PASS_STATUS[next_session.scenario]}"',
            "}",
            "```",
            "",
            "Allowed recommended_stage_status values: " + ", ".join(allowed_statuses) + ".",
            "Use severity error or warning only for findings that must block progress.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def normalize_bounded_reviewer_response(
    payload: dict[str, Any],
    next_session: NextSession,
) -> dict[str, Any]:
    findings = payload.get("findings")
    if not isinstance(findings, list):
        findings = []
    normalized_findings = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        normalized = dict(finding)
        if not normalized.get("problem") and normalized.get("title"):
            normalized["problem"] = normalized["title"]
        if not normalized.get("required_change") and normalized.get("recommendation"):
            normalized["required_change"] = normalized["recommendation"]
        normalized_findings.append(normalized)

    recommended = str(payload.get("recommended_stage_status") or "").strip()
    allowed = BOUNDED_REVIEWER_ALLOWED_STATUSES[next_session.scenario]
    blocking = any(
        str(finding.get("severity") or "").lower() in BOUNDED_SEMANTIC_BLOCKING_SEVERITIES
        for finding in normalized_findings
    )
    if recommended not in allowed:
        recommended = (
            BOUNDED_REVIEWER_FINDING_STATUS[next_session.scenario]
            if normalized_findings
            else BOUNDED_REVIEWER_PASS_STATUS[next_session.scenario]
        )
    if blocking and recommended == BOUNDED_REVIEWER_PASS_STATUS[next_session.scenario]:
        recommended = BOUNDED_REVIEWER_FINDING_STATUS[next_session.scenario]
    return {
        "findings": normalized_findings,
        "human_summary": str(payload.get("human_summary") or "").strip(),
        "recommended_stage_status": recommended,
    }


def render_bounded_reviewer_findings(
    stage: str,
    response: dict[str, Any],
    *,
    scenario: str,
) -> str:
    lines = [
        f"# {stage} findings",
        "",
        "## Human Summary",
        response["human_summary"] or "No additional summary provided.",
        "",
        "## Findings",
    ]
    findings = response["findings"]
    if not findings:
        lines.append("- none")
    for index, finding in enumerate(findings, start=1):
        finding_id = str(finding.get("id") or f"REV-{index:03d}")
        lines.extend(
            [
                f"### {finding_id}",
                "",
                f"- severity: `{finding.get('severity') or 'info'}`",
                f"- category: `{finding.get('category') or 'review'}`",
                (
                    f"- gap_id: `{finding.get('gap_id') or ''}`"
                    if scenario == "reviewer.scope_gap_review"
                    else f"- test_case_id: `{finding.get('test_case_id') or ''}`"
                ),
                f"- problem: {finding.get('problem') or ''}",
                f"- evidence: {finding.get('evidence') or ''}",
                f"- required_change: {finding.get('required_change') or ''}",
                f"- source_reference: `{finding.get('source_reference') or ''}`",
                f"- status: `{finding.get('status') or 'open'}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_writer_initial_prompt_from_scope_review(next_session: NextSession, findings_path: str) -> str:
    return "\n".join(
        [
            "# Writer initial draft",
            "",
            f"Scope gap review `{next_session.stage}` completed. Use `{findings_path}` as reviewer handoff evidence.",
            "Create the initial FT-first test-case draft for the selected scope.",
            "",
        ]
    )


def render_writer_format_prompt(next_session: NextSession, findings_path: str) -> str:
    return "\n".join(
        [
            "# Writer final format revision",
            "",
            f"Resolve structure/format findings from `{findings_path}`.",
            "Do not make semantic redesign unless the finding explicitly routes back to semantic review.",
            "",
        ]
    )


def next_prompt_for_bounded_reviewer(
    state: dict[str, Any],
    state_path: Path,
    next_session: NextSession,
    status_after: str,
    findings_path: Path,
) -> Path:
    ft_root = infer_ft_root(state_path)
    prompt_dir = state_path.parent / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    if next_session.scenario == "reviewer.scope_gap_review":
        if status_after == "blocked-input":
            prompt = prompt_dir / "prompt.scope-gap-review-blocked.md"
            prompt.write_text(
                "\n".join(
                    [
                        "# Scope gap review blocked",
                        "",
                        f"Review findings: `{relative_or_name(findings_path, ft_root)}`.",
                        "Return to ft-scope-analyzer. Do not start writer.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            return prompt
        prompt = prompt_dir / "prompt.writer-r1.md"
        prompt.write_text(
            render_writer_initial_prompt_from_scope_review(
                next_session,
                relative_or_name(findings_path, ft_root),
            ),
            encoding="utf-8",
        )
        return prompt
    if next_session.scenario == "reviewer.structure_format_final":
        if status_after == "format-revision-needed":
            prompt = prompt_dir / "prompt.writer-format-final.md"
            prompt.write_text(
                render_writer_format_prompt(next_session, relative_or_name(findings_path, ft_root)),
                encoding="utf-8",
            )
            return prompt
        prompt = prompt_dir / "prompt.semantic-regression-final.md"
        prompt.write_text(
            "\n".join(
                [
                    "# Final semantic regression",
                    "",
                    "Run semantic_regression after final structure/format review.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return prompt
    existing = resolve_artifact_path(str(state.get("active_transition_prompt") or ""), ft_root)
    if existing is not None and existing.exists():
        return existing
    prompt = prompt_dir / "prompt.terminal.md"
    prompt.write_text("# Terminal reviewer stage\n\nNo next SDK prompt is required after terminal routing.\n", encoding="utf-8")
    return prompt


def write_bounded_semantic_invalid_response_artifact(
    output_dir: Path,
    stage: str,
    final_response: str,
    error: Exception,
) -> Path:
    path = output_dir / f"{stage}-invalid-response.md"
    path.write_text(
        "\n".join(
            [
                f"# {stage} invalid bounded semantic response",
                "",
                f"error: {type(error).__name__}: {error}",
                "",
                "## Raw response",
                "",
                final_response or "",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


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
    execution_mode: str = "sdk",
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
        "execution_mode": execution_mode,
        "sandbox_policy": next_session.sandbox_policy,
        "reviewer_write_exception": (
            next_session.role == "reviewer"
            and next_session.sandbox_policy == "workspace_write"
        ),
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


def completion_manifest_path_for_stage(state_path: Path, stage: str) -> Path:
    return state_path.parent / "outputs" / f"{stage}{COMPLETION_MANIFEST_SUFFIX}"


def run_codex_turn_with_timeout(
    thread: Any,
    prompt: str,
    *,
    cwd: str,
    sandbox: Any,
    approval_mode: Any,
    model: str | None,
    timeout_seconds: int | None,
) -> Any:
    if not timeout_seconds or timeout_seconds <= 0:
        return thread.run(
            prompt,
            cwd=cwd,
            sandbox=sandbox,
            approval_mode=approval_mode,
            model=model,
        )

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        thread.run,
        prompt,
        cwd=cwd,
        sandbox=sandbox,
        approval_mode=approval_mode,
        model=model,
    )
    wait_for_shutdown = True
    try:
        return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError:
        future.cancel()
        wait_for_shutdown = False
        raise
    finally:
        executor.shutdown(wait=wait_for_shutdown, cancel_futures=True)


def timeout_recovery_diagnostics(
    state_path: Path,
    state: dict[str, Any],
    next_session: NextSession,
) -> tuple[list[str], list[str]]:
    if next_session.role != "writer":
        return (["- non-writer session: artifact recovery is not supported."], ["non-writer timeout"])

    ft_root = infer_ft_root(state_path)
    output_dir = state_path.parent / "outputs"
    markdown: list[str] = []
    reasons: list[str] = []
    try:
        state_for_profile = load_simple_yaml(state_path)
    except RunnerError:
        state_for_profile = state
    profile_stage = writer_timeout_recovery_profile_stage(state_path, state_for_profile, next_session)
    expected_profile_name = f"scoped-validator-profile.{profile_stage}.json"

    writer_response = output_dir / f"{next_session.stage}-response.md"
    if existing_relative_artifact(writer_response, ft_root):
        markdown.append(f"- writer response: present (`{relative_or_name(writer_response, ft_root)}`)")
    else:
        markdown.append(f"- writer response: missing (`outputs/{next_session.stage}-response.md`)")
        reasons.append("writer response missing")

    profile_path = output_dir / expected_profile_name
    if not profile_path.exists():
        markdown.append(f"- scoped validator profile: missing (`outputs/{expected_profile_name}`)")
        markdown.append(
            "- recovery action: run `python scripts/validate_agent_artifacts.py --root <ft-root> --json` "
            "for this cycle and write the stage-appropriate scoped profile before resuming."
        )
        reasons.append(f"writer-timeout-recovery-missing-profile: outputs/{expected_profile_name}")
    else:
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            markdown.append(f"- scoped validator profile: invalid JSON (`{relative_or_name(profile_path, ft_root)}`)")
            reasons.append(f"writer-timeout-recovery-missing-profile: outputs/{expected_profile_name} invalid JSON")
        else:
            unresolved = profile.get("unresolved_warning_error_count")
            markdown.append(
                f"- scoped validator profile: present (`{relative_or_name(profile_path, ft_root)}`), "
                f"unresolved_warning_error_count={unresolved!r}"
            )
            try:
                unresolved_count = int(unresolved or 0)
            except (TypeError, ValueError):
                unresolved_count = 1
            if unresolved_count != 0:
                reasons.append(f"stage-appropriate scoped validator profile unresolved={unresolved!r}")

    next_review = next_writer_review_prompt(state_path, state, next_session)
    if next_review is None:
        markdown.append("- next review prompt: not applicable for this writer scenario")
        reasons.append("next review prompt not derivable")
    else:
        _, _, _, prompt_name = next_review
        prompt_path = state_path.parent / "prompts" / prompt_name
        if existing_relative_artifact(prompt_path, ft_root):
            markdown.append(f"- next review prompt: present (`{relative_or_name(prompt_path, ft_root)}`)")
        else:
            markdown.append(f"- next review prompt: missing (`prompts/{prompt_name}`)")
            reasons.append("next review prompt missing")

    return markdown, reasons


def recover_timed_out_session(
    state_path: Path,
    *,
    state_before: dict[str, Any],
    next_session: NextSession,
    thread_id: str,
    approval_mode: str,
    model: str | None,
    before_snapshot_id: str,
    after_snapshot_id: str,
    started_at_epoch: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    ft_root = infer_ft_root(state_path)
    completed_at = int(time.time())
    output_dir = state_path.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    timeout_output = output_dir / f"{next_session.stage}-timeout-recovery.md"
    diagnostic_lines, diagnostic_reasons = timeout_recovery_diagnostics(
        state_path,
        state_before,
        next_session,
    )
    timeout_output.write_text(
        "\n".join(
            [
                f"# {next_session.stage} timeout recovery",
                "",
                f"Session exceeded timeout_seconds={timeout_seconds}.",
                "Runner marked the review cycle as blocked-input to prevent repeating a possibly stale stage.",
                "",
                "## Artifact Recovery Diagnostics",
                "",
                *diagnostic_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )

    state_after = load_simple_yaml(state_path)
    state_after["stage_status"] = "blocked-input"
    state_after["current_stage"] = state_after.get("current_stage") or next_session.stage
    state_after["blocking_reasons"] = [
        f"{next_session.stage}: Codex SDK turn timed out after {timeout_seconds} seconds",
    ]
    if diagnostic_reasons:
        state_after["blocking_reasons"].append(
            f"{next_session.stage}: timeout artifact recovery did not continue: "
            + "; ".join(diagnostic_reasons[:4])
        )
    timeout_output_ref = relative_or_name(timeout_output, ft_root)
    state_after["latest_artifacts"] = unique_nonempty_strings(
        state_after.get("latest_artifacts"),
        timeout_output_ref,
    )
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)

    input_snapshot = relative_or_name(
        state_path.parent / "versions" / before_snapshot_id,
        ft_root,
    )
    output_snapshot = relative_or_name(
        state_path.parent / "versions" / after_snapshot_id,
        ft_root,
    )
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state_before,
        state_after=state_after,
        next_session=next_session,
        thread_id=thread_id,
        turn_id="",
        turn_status="timeout",
        session_status="failed",
        state_advanced=state_progress_marker(state_after) != state_progress_marker(state_before),
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=timeout_output,
        started_at_epoch=started_at_epoch,
        completed_at_epoch=completed_at,
        duration_ms=(completed_at - started_at_epoch) * 1000,
    )
    completion_manifest_ref = relative_or_name(completion_manifest_path, ft_root)
    state_after["latest_artifacts"] = unique_nonempty_strings(
        state_after.get("latest_artifacts"),
        completion_manifest_ref,
    )
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)
    after_manifest = snapshot_state(state_path, after_snapshot_id)
    append_session_record(
        state_path.parent / "codex-session-map.yaml",
        state_before,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "thread_id": thread_id,
            "turn_id": "",
            "turn_status": "timeout",
            "sandbox": next_session.sandbox_policy,
            "approval_mode": approval_mode,
            "model": model or "",
            "prompt": next_session.prompt_path,
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": timeout_output_ref,
            "completion_manifest": completion_manifest_ref,
            "started_at_epoch": started_at_epoch,
            "completed_at_epoch": completed_at,
            "duration_ms": (completed_at - started_at_epoch) * 1000,
            "state_advanced": True,
            "status": "failed",
            "abort_reason": f"timeout after {timeout_seconds} seconds",
        },
    )
    append_runner_event(
        state_path.parent,
        "session_timeout_recovered",
        stage=next_session.stage,
        thread_id=thread_id,
        timeout_seconds=timeout_seconds,
        completion_manifest=completion_manifest_ref,
    )
    return {
        "action": "recovered-timeout-session",
        "cycle_id": state_before["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "sdk",
        "thread_id": thread_id,
        "turn_id": "",
        "turn_status": "timeout",
        "session_status": "failed",
        "state_advanced": True,
        "final_response": str(timeout_output),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_snapshot_id,
        "output_snapshot": after_manifest["snapshot_id"],
    }


def recover_missing_completion_as_blocked(
    state_path: Path,
    *,
    state_before: dict[str, Any],
    next_session: NextSession,
    recovered_lock: dict[str, Any],
    approval_mode: str,
    model: str | None,
    before_snapshot_id: str,
    after_snapshot_id: str,
) -> dict[str, Any]:
    ft_root = infer_ft_root(state_path)
    completed_at = int(time.time())
    started_at = int(recovered_lock.get("started_at_epoch") or completed_at)
    output_dir = state_path.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    diagnostic_path = output_dir / f"{next_session.stage}-completion-missing.md"
    diagnostic_lines, diagnostic_reasons = timeout_recovery_diagnostics(
        state_path,
        state_before,
        next_session,
    )
    missing_manifest = relative_or_name(
        completion_manifest_path_for_stage(state_path, next_session.stage),
        ft_root,
    )
    diagnostic_path.write_text(
        "\n".join(
            [
                f"# {next_session.stage} completion missing",
                "",
                "blocker: blocked-runner-completion-missing",
                f"expected completion manifest: `{missing_manifest}`",
                "expected terminal events: `turn_finished`, `stage_completed`",
                "",
                "## Artifact Recovery Diagnostics",
                "",
                *diagnostic_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )

    state_after = load_simple_yaml(state_path)
    state_after["stage_status"] = "blocked-input"
    state_after["current_stage"] = next_session.stage
    state_after["blocking_reasons"] = [
        f"blocked-runner-completion-missing: {next_session.stage} has no completion manifest after stale lock recovery",
    ]
    if diagnostic_reasons:
        state_after["blocking_reasons"].append(
            f"{next_session.stage}: incomplete writer artifact recovery: "
            + "; ".join(diagnostic_reasons[:4])
        )
    state_after["blocking_findings"] = []
    state_after["active_transition_prompt"] = next_session.prompt_path
    diagnostic_ref = relative_or_name(diagnostic_path, ft_root)
    state_after["latest_artifacts"] = unique_nonempty_strings(
        state_after.get("latest_artifacts"),
        diagnostic_ref,
    )
    state_after["sessions"] = []
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)

    input_snapshot = relative_or_name(state_path.parent / "versions" / before_snapshot_id, ft_root)
    output_snapshot = relative_or_name(state_path.parent / "versions" / after_snapshot_id, ft_root)
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state_before,
        state_after=state_after,
        next_session=next_session,
        thread_id=str(recovered_lock.get("thread_id") or ""),
        turn_id="",
        turn_status="interrupted",
        session_status="failed",
        state_advanced=True,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=diagnostic_path,
        started_at_epoch=started_at,
        completed_at_epoch=completed_at,
        duration_ms=(completed_at - started_at) * 1000,
    )
    completion_ref = relative_or_name(completion_manifest_path, ft_root)
    state_after["latest_artifacts"] = unique_nonempty_strings(
        state_after.get("latest_artifacts"),
        completion_ref,
    )
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)
    after_manifest = snapshot_state(state_path, after_snapshot_id)
    append_session_record(
        state_path.parent / "codex-session-map.yaml",
        state_before,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "thread_id": str(recovered_lock.get("thread_id") or ""),
            "turn_id": "",
            "turn_status": "interrupted",
            "sandbox": next_session.sandbox_policy,
            "approval_mode": approval_mode,
            "model": model or "",
            "prompt": next_session.prompt_path,
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": diagnostic_ref,
            "completion_manifest": completion_ref,
            "started_at_epoch": started_at,
            "completed_at_epoch": completed_at,
            "duration_ms": (completed_at - started_at) * 1000,
            "state_advanced": True,
            "status": "failed",
            "abort_reason": "blocked-runner-completion-missing",
        },
    )
    append_runner_event(
        state_path.parent,
        "session_completion_missing_blocked",
        stage=next_session.stage,
        thread_id=str(recovered_lock.get("thread_id") or ""),
        completion_manifest=completion_ref,
        diagnostic=diagnostic_ref,
    )
    return {
        "action": "blocked-runner-completion-missing",
        "cycle_id": state_before["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "sdk",
        "thread_id": str(recovered_lock.get("thread_id") or ""),
        "turn_id": "",
        "turn_status": "interrupted",
        "session_status": "failed",
        "state_advanced": True,
        "final_response": str(diagnostic_path),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_snapshot_id,
        "output_snapshot": after_manifest["snapshot_id"],
    }


def read_child_payload(payload_path: Path) -> dict[str, Any] | None:
    if not payload_path.exists():
        return None
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def completed_payload_from_timed_out_state_progress(
    state_path: Path,
    *,
    state_before: dict[str, Any],
    next_session: NextSession,
    thread_id: str,
    approval_mode: str,
    model: str | None,
    before_snapshot_id: str,
    after_snapshot_id: str,
    started_at_epoch: int,
    timeout_seconds: int,
) -> dict[str, Any] | None:
    try:
        state_after = load_simple_yaml(state_path)
        validate_state(state_after, state_path)
        validate_post_session_state_transition(
            state_before,
            state_after,
            next_session,
            state_path,
        )
    except RunnerError:
        return None

    state_advanced = state_progress_marker(state_after) != state_progress_marker(state_before)
    if not state_advanced:
        return None

    ft_root = infer_ft_root(state_path)
    completed_at = int(time.time())
    output_dir = state_path.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    timeout_output = output_dir / f"{next_session.stage}-timeout-after-progress.md"
    timeout_output.write_text(
        "\n".join(
            [
                f"# {next_session.stage} timeout after progress",
                "",
                f"Session exceeded timeout_seconds={timeout_seconds}, but cycle-state.yaml advanced before recovery.",
                "Runner preserved the advanced state instead of overwriting it with blocked-input.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    after_manifest = snapshot_state(state_path, after_snapshot_id)
    input_snapshot = relative_or_name(
        state_path.parent / "versions" / before_snapshot_id,
        ft_root,
    )
    output_snapshot = relative_or_name(
        state_path.parent / "versions" / after_snapshot_id,
        ft_root,
    )
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state_before,
        state_after=state_after,
        next_session=next_session,
        thread_id=thread_id,
        turn_id="",
        turn_status="timeout",
        session_status="completed-with-progress",
        state_advanced=True,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=timeout_output,
        started_at_epoch=started_at_epoch,
        completed_at_epoch=completed_at,
        duration_ms=(completed_at - started_at_epoch) * 1000,
    )
    append_session_record(
        state_path.parent / "codex-session-map.yaml",
        state_before,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "thread_id": thread_id,
            "turn_id": "",
            "turn_status": "timeout",
            "sandbox": next_session.sandbox_policy,
            "approval_mode": approval_mode,
            "model": model or "",
            "prompt": next_session.prompt_path,
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": relative_or_name(timeout_output, ft_root),
            "completion_manifest": relative_or_name(completion_manifest_path, ft_root),
            "started_at_epoch": started_at_epoch,
            "completed_at_epoch": completed_at,
            "duration_ms": (completed_at - started_at_epoch) * 1000,
            "state_advanced": True,
            "status": "completed-with-progress",
            "timeout_seconds": timeout_seconds,
        },
    )
    append_runner_event(
        state_path.parent,
        "session_child_timeout_after_state_progress",
        stage=next_session.stage,
        thread_id=thread_id,
        timeout_seconds=timeout_seconds,
        completion_manifest=relative_or_name(completion_manifest_path, ft_root),
    )
    return {
        "action": "completed-session-after-timeout",
        "cycle_id": state_before["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "sdk",
        "thread_id": thread_id,
        "turn_id": "",
        "turn_status": "timeout",
        "session_status": "completed-with-progress",
        "state_advanced": True,
        "final_response": str(timeout_output),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_snapshot_id,
        "output_snapshot": after_manifest["snapshot_id"],
    }


def effective_session_timeout_seconds(
    next_session: NextSession,
    requested_timeout_seconds: int | None,
) -> int:
    if requested_timeout_seconds is None:
        return 0
    if requested_timeout_seconds == AUTO_SESSION_TIMEOUT_SENTINEL:
        return DEFAULT_SESSION_TIMEOUT_SECONDS_BY_SCENARIO.get(
            next_session.scenario,
            1800,
        )
    return max(0, int(requested_timeout_seconds))


def next_session_requires_sdk(next_session: NextSession | None) -> bool:
    return next_session is not None and next_session.scenario != "reviewer.structure_preflight"


def existing_relative_artifact(path: Path, ft_root: Path) -> str | None:
    if path.exists() and path.is_file() and path.stat().st_size > 0:
        return relative_or_name(path, ft_root)
    return None


def writer_timeout_artifact_candidates(
    state_path: Path,
    state: dict[str, Any],
    next_session: NextSession,
) -> list[str]:
    ft_root = infer_ft_root(state_path)
    output_dir = state_path.parent / "outputs"
    artifacts: list[str] = []

    canonical = resolve_artifact_path(str(state.get("canonical_test_cases") or ""), ft_root)
    if canonical and canonical.exists():
        artifacts.append(relative_or_name(canonical, ft_root))

    draft = resolve_artifact_path(str(state.get("draft_test_cases") or ""), ft_root)
    if draft and draft.exists():
        artifacts.append(relative_or_name(draft, ft_root))

    test_design_dir = resolve_artifact_path(str(state.get("test_design_dir") or ""), ft_root)
    if test_design_dir and test_design_dir.exists():
        artifacts.append(relative_or_name(test_design_dir, ft_root))

    profile_stage = writer_timeout_recovery_profile_stage(state_path, state, next_session)
    candidate_paths = [
        output_dir / f"{next_session.stage}-response.md",
        output_dir / f"{next_session.stage}-draft.md",
        output_dir / f"writer-session-log.{next_session.stage}.md",
        output_dir / "writer-session-log.md",
        output_dir / f"agent-decision-log.{next_session.stage}.md",
        output_dir / "agent-decision-log.md",
        output_dir / f"scoped-validator-profile.{next_session.stage}.json",
        output_dir / f"scoped-validator-profile.{profile_stage}.json",
    ]
    for path in candidate_paths:
        relative = existing_relative_artifact(path, ft_root)
        if relative:
            artifacts.append(relative)

    return list(dict.fromkeys(artifacts))


def writer_timeout_recovery_profile_stage(
    state_path: Path,
    state: dict[str, Any],
    next_session: NextSession,
) -> str:
    current_stage = str(state.get("current_stage") or "").strip()
    if current_stage and current_stage != next_session.stage:
        return current_stage
    next_review = next_writer_review_prompt(state_path, state, next_session)
    if next_review is not None:
        next_stage, _, _, _ = next_review
        next_profile = state_path.parent / "outputs" / f"scoped-validator-profile.{next_stage}.json"
        if next_profile.exists():
            return next_stage
    return next_session.stage


def next_writer_review_prompt(
    state_path: Path,
    state_before: dict[str, Any],
    next_session: NextSession,
) -> tuple[str, str, int, str] | None:
    prompt_dir = state_path.parent / "prompts"
    if next_session.scenario in {
        "writer.session_initial_draft",
        "writer.remediation.style",
        "writer.remediation.structure_preflight",
    }:
        prompt = prompt_dir / "prompt.structure-preflight-r1.md"
        return ("structure-preflight-r1", "writer-draft-ready", int(state_before.get("semantic_round") or 0), prompt.name)
    if next_session.scenario == "writer.session_semantic_revision":
        round_no = int(state_before.get("semantic_round") or 0) + 1
        prompt = prompt_dir / f"prompt.semantic-review-r{round_no}.md"
        return (f"semantic-review-r{round_no}", "semantic-review-ready", round_no, prompt.name)
    if next_session.scenario == "writer.session_format_revision":
        prompt = prompt_dir / "prompt.semantic-regression-final.md"
        return ("semantic-regression-final", "final-regression-ready", int(state_before.get("semantic_round") or 0), prompt.name)
    return None


def clean_scoped_validator_profile_for_stage(
    state_path: Path,
    state: dict[str, Any],
    stage: str,
) -> Path | None:
    profile_path = state_path.parent / "outputs" / f"scoped-validator-profile.{stage}.json"
    if not profile_path.exists():
        validator_payload = run_agent_artifact_validator(infer_ft_root(state_path))
        profile_path = write_runner_scoped_validator_profile(state, state_path, validator_payload)
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if int(profile.get("unresolved_warning_error_count") or 0) != 0:
        return None
    return profile_path


def clean_scoped_validator_profile_for_writer_timeout_recovery(
    state_path: Path,
    state: dict[str, Any],
    next_session: NextSession,
) -> Path | None:
    return clean_scoped_validator_profile_for_stage(
        state_path,
        state,
        writer_timeout_recovery_profile_stage(state_path, state, next_session),
    )


def completed_payload_from_timed_out_writer_artifact_progress(
    state_path: Path,
    *,
    state_before: dict[str, Any],
    next_session: NextSession,
    thread_id: str,
    approval_mode: str,
    model: str | None,
    before_snapshot_id: str,
    after_snapshot_id: str,
    started_at_epoch: int,
    timeout_seconds: int,
) -> dict[str, Any] | None:
    if next_session.role != "writer":
        return None

    state_current = load_simple_yaml(state_path)
    if state_progress_marker(state_current) != state_progress_marker(state_before):
        return None

    ft_root = infer_ft_root(state_path)
    output_dir = state_path.parent / "outputs"
    writer_response = output_dir / f"{next_session.stage}-response.md"
    if not existing_relative_artifact(writer_response, ft_root):
        return None

    profile_path = clean_scoped_validator_profile_for_writer_timeout_recovery(
        state_path,
        state_current,
        next_session,
    )
    if profile_path is None:
        return None

    next_review = next_writer_review_prompt(state_path, state_before, next_session)
    if next_review is None:
        return None
    next_stage, next_status, next_round, next_prompt_name = next_review
    next_prompt = state_path.parent / "prompts" / next_prompt_name
    if not existing_relative_artifact(next_prompt, ft_root):
        return None

    state_after = dict(state_current)
    state_after["current_stage"] = next_stage
    state_after["stage_status"] = next_status
    state_after["semantic_round"] = next_round
    state_after["active_transition_prompt"] = relative_or_name(next_prompt, ft_root)
    state_after["blocking_reasons"] = []
    state_after["blocking_findings"] = []
    latest = []
    if isinstance(state_current.get("latest_artifacts"), list):
        latest.extend(str(item) for item in state_current["latest_artifacts"])
    latest.extend(writer_timeout_artifact_candidates(state_path, state_after, next_session))
    latest.append(relative_or_name(next_prompt, ft_root))
    state_after["latest_artifacts"] = list(dict.fromkeys(latest))
    state_after["sessions"] = []
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)
    validate_post_session_state_transition(
        state_before,
        state_after,
        next_session,
        state_path,
    )

    completed_at = int(time.time())
    timeout_output = output_dir / f"{next_session.stage}-timeout-after-artifacts.md"
    timeout_output.write_text(
        "\n".join(
            [
                f"# {next_session.stage} timeout after artifact progress",
                "",
                f"Session exceeded timeout_seconds={timeout_seconds}, but writer artifacts were complete enough for the next review stage.",
                "Runner recovered to the next review stage because writer response, scoped validator profile and next prompt were present.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    state_after["latest_artifacts"] = list(
        dict.fromkeys(
            [*state_after["latest_artifacts"], relative_or_name(timeout_output, ft_root)]
        )
    )
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)

    after_manifest = snapshot_state(state_path, after_snapshot_id)
    input_snapshot = relative_or_name(
        state_path.parent / "versions" / before_snapshot_id,
        ft_root,
    )
    output_snapshot = relative_or_name(
        state_path.parent / "versions" / after_snapshot_id,
        ft_root,
    )
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state_before,
        state_after=state_after,
        next_session=next_session,
        thread_id=thread_id,
        turn_id="",
        turn_status="timeout",
        session_status="completed-with-progress",
        state_advanced=True,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=timeout_output,
        started_at_epoch=started_at_epoch,
        completed_at_epoch=completed_at,
        duration_ms=(completed_at - started_at_epoch) * 1000,
    )
    append_session_record(
        state_path.parent / "codex-session-map.yaml",
        state_before,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "thread_id": thread_id,
            "turn_id": "",
            "turn_status": "timeout",
            "sandbox": next_session.sandbox_policy,
            "approval_mode": approval_mode,
            "model": model or "",
            "prompt": next_session.prompt_path,
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": relative_or_name(timeout_output, ft_root),
            "completion_manifest": relative_or_name(completion_manifest_path, ft_root),
            "started_at_epoch": started_at_epoch,
            "completed_at_epoch": completed_at,
            "duration_ms": (completed_at - started_at_epoch) * 1000,
            "state_advanced": True,
            "status": "completed-with-progress",
            "timeout_seconds": timeout_seconds,
        },
    )
    append_runner_event(
        state_path.parent,
        "session_child_timeout_after_artifact_progress",
        stage=next_session.stage,
        thread_id=thread_id,
        timeout_seconds=timeout_seconds,
        scoped_validator_profile=relative_or_name(profile_path, ft_root),
        completion_manifest=relative_or_name(completion_manifest_path, ft_root),
    )
    return {
        "action": "completed-session-after-timeout",
        "cycle_id": state_before["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "sdk",
        "thread_id": thread_id,
        "turn_id": "",
        "turn_status": "timeout",
        "session_status": "completed-with-progress",
        "state_advanced": True,
        "final_response": str(timeout_output),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_snapshot_id,
        "output_snapshot": after_manifest["snapshot_id"],
    }


def completed_payload_from_incomplete_writer_artifact_progress(
    state_path: Path,
    *,
    state_before: dict[str, Any],
    next_session: NextSession,
    recovered_lock: dict[str, Any],
    approval_mode: str,
    model: str | None,
    before_snapshot_id: str,
    after_snapshot_id: str,
) -> dict[str, Any] | None:
    if next_session.role != "writer":
        return None

    state_current = load_simple_yaml(state_path)
    if state_progress_marker(state_current) != state_progress_marker(state_before):
        return None

    ft_root = infer_ft_root(state_path)
    output_dir = state_path.parent / "outputs"
    writer_response = output_dir / f"{next_session.stage}-response.md"
    if not existing_relative_artifact(writer_response, ft_root):
        return None

    profile_path = clean_scoped_validator_profile_for_writer_timeout_recovery(
        state_path,
        state_current,
        next_session,
    )
    if profile_path is None:
        return None

    next_review = next_writer_review_prompt(state_path, state_before, next_session)
    if next_review is None:
        return None
    next_stage, next_status, next_round, next_prompt_name = next_review
    next_prompt = state_path.parent / "prompts" / next_prompt_name
    if not existing_relative_artifact(next_prompt, ft_root):
        return None

    state_after = dict(state_current)
    state_after["current_stage"] = next_stage
    state_after["stage_status"] = next_status
    state_after["semantic_round"] = next_round
    state_after["active_transition_prompt"] = relative_or_name(next_prompt, ft_root)
    state_after["blocking_reasons"] = []
    state_after["blocking_findings"] = []
    latest: list[str] = []
    if isinstance(state_current.get("latest_artifacts"), list):
        latest.extend(str(item) for item in state_current["latest_artifacts"])
    latest.extend(writer_timeout_artifact_candidates(state_path, state_after, next_session))
    latest.append(relative_or_name(next_prompt, ft_root))
    state_after["latest_artifacts"] = list(dict.fromkeys(latest))
    state_after["sessions"] = []
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)
    validate_post_session_state_transition(state_before, state_after, next_session, state_path)

    completed_at = int(time.time())
    started_at = int(recovered_lock.get("started_at_epoch") or completed_at)
    diagnostic_path = output_dir / f"{next_session.stage}-completion-recovered-from-artifacts.md"
    diagnostic_path.write_text(
        "\n".join(
            [
                f"# {next_session.stage} completion recovered from artifacts",
                "",
                "Previous runner process ended before writing the completion manifest.",
                "Writer response, clean scoped validator profile and next review prompt were present, so the runner recovered the next state.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    state_after["latest_artifacts"] = list(
        dict.fromkeys(
            [*state_after["latest_artifacts"], relative_or_name(diagnostic_path, ft_root)]
        )
    )
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)

    after_manifest = snapshot_state(state_path, after_snapshot_id)
    input_snapshot = relative_or_name(state_path.parent / "versions" / before_snapshot_id, ft_root)
    output_snapshot = relative_or_name(state_path.parent / "versions" / after_snapshot_id, ft_root)
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state_before,
        state_after=state_after,
        next_session=next_session,
        thread_id=str(recovered_lock.get("thread_id") or ""),
        turn_id="",
        turn_status="interrupted",
        session_status="completed-with-progress",
        state_advanced=True,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=diagnostic_path,
        started_at_epoch=started_at,
        completed_at_epoch=completed_at,
        duration_ms=(completed_at - started_at) * 1000,
    )
    completion_ref = relative_or_name(completion_manifest_path, ft_root)
    append_session_record(
        state_path.parent / "codex-session-map.yaml",
        state_before,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "thread_id": str(recovered_lock.get("thread_id") or ""),
            "turn_id": "",
            "turn_status": "interrupted",
            "sandbox": next_session.sandbox_policy,
            "approval_mode": approval_mode,
            "model": model or "",
            "prompt": next_session.prompt_path,
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": relative_or_name(diagnostic_path, ft_root),
            "completion_manifest": completion_ref,
            "started_at_epoch": started_at,
            "completed_at_epoch": completed_at,
            "duration_ms": (completed_at - started_at) * 1000,
            "state_advanced": True,
            "status": "completed-with-progress",
            "abort_reason": "completion recovered from writer artifacts after stale lock",
        },
    )
    append_runner_event(
        state_path.parent,
        "session_incomplete_recovered_after_artifact_progress",
        stage=next_session.stage,
        thread_id=str(recovered_lock.get("thread_id") or ""),
        scoped_validator_profile=relative_or_name(profile_path, ft_root),
        completion_manifest=completion_ref,
    )
    return {
        "action": "completed-session-after-incomplete-run",
        "cycle_id": state_before["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "sdk",
        "thread_id": str(recovered_lock.get("thread_id") or ""),
        "turn_id": "",
        "turn_status": "interrupted",
        "session_status": "completed-with-progress",
        "state_advanced": True,
        "final_response": str(diagnostic_path),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_snapshot_id,
        "output_snapshot": after_manifest["snapshot_id"],
    }


def recover_incomplete_stage_after_stale_lock(
    state_path: Path,
    *,
    recovered_lock: dict[str, Any] | None,
    approval_mode: str,
    model: str | None,
    runner_lock: RunnerFileLock | None,
) -> dict[str, Any] | None:
    if not recovered_lock:
        return None
    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    next_session = next_session_for_state(state)
    if next_session is None:
        return None
    recovered_stage = str(recovered_lock.get("stage") or "")
    if recovered_stage and recovered_stage != next_session.stage:
        return None
    manifest_path = completion_manifest_path_for_stage(state_path, next_session.stage)
    if manifest_path.exists():
        return None

    before_snapshot_id = f"before-{next_session.stage}"
    after_snapshot_id = f"after-{next_session.stage}"
    if runner_lock is not None:
        runner_lock.update(
            stage=next_session.stage,
            scenario=next_session.scenario,
            thread_id=str(recovered_lock.get("thread_id") or ""),
            status="recovering-incomplete-stage",
        )
    artifact_payload = completed_payload_from_incomplete_writer_artifact_progress(
        state_path,
        state_before=state,
        next_session=next_session,
        recovered_lock=recovered_lock,
        approval_mode=approval_mode,
        model=model,
        before_snapshot_id=before_snapshot_id,
        after_snapshot_id=after_snapshot_id,
    )
    if artifact_payload is not None:
        return artifact_payload
    return recover_missing_completion_as_blocked(
        state_path,
        state_before=state,
        next_session=next_session,
        recovered_lock=recovered_lock,
        approval_mode=approval_mode,
        model=model,
        before_snapshot_id=before_snapshot_id,
        after_snapshot_id=after_snapshot_id,
    )


def run_deterministic_structure_preflight(
    state: dict[str, Any],
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    runner_lock: RunnerFileLock | None,
) -> dict[str, Any]:
    next_session = next_session_for_state(state)
    if next_session is None:
        raise RunnerError(f"No runnable next session for status {state['stage_status']}")
    if next_session.scenario != "reviewer.structure_preflight":
        raise RunnerError(f"Deterministic structure preflight cannot run {next_session.scenario}")

    ft_root = infer_ft_root(state_path)
    cycle_dir = state_path.parent
    output_dir = cycle_dir / "outputs"
    prompt_dir = cycle_dir / "prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    started_at = int(time.time())
    before_snapshot_id = f"before-{next_session.stage}"
    after_snapshot_id = f"after-{next_session.stage}"
    findings, checked_paths = evaluate_deterministic_structure_preflight(state, state_path)
    snapshot_state(state_path, before_snapshot_id)
    append_runner_event(
        cycle_dir,
        "deterministic_stage_started",
        stage=next_session.stage,
        scenario=next_session.scenario,
        execution_mode="deterministic",
    )
    if runner_lock is not None:
        runner_lock.update(
            stage=next_session.stage,
            scenario=next_session.scenario,
            thread_id=DETERMINISTIC_STRUCTURE_THREAD_ID,
            status="running-deterministic-stage",
        )

    status_after = "structure-preflight-blocked" if findings else "semantic-review-ready"

    findings_path = output_dir / f"{next_session.stage}-findings.md"
    session_log_path = output_dir / f"reviewer-session-log.{next_session.stage}.md"
    decision_log_path = output_dir / f"agent-decision-log.{next_session.stage}.md"
    prompt_path = (
        prompt_dir / "prompt.writer-structure-r1.md"
        if findings
        else prompt_dir / "prompt.semantic-review-r1.md"
    )
    prompt_text = (
        render_writer_structure_prompt(next_session.stage, findings)
        if findings
        else render_semantic_review_prompt(next_session.stage)
    )
    prompt_path.write_text(prompt_text, encoding="utf-8")

    findings_path.write_text(
        render_structure_preflight_findings(next_session.stage, findings, checked_paths),
        encoding="utf-8",
    )
    completed_at = int(time.time())
    session_log_path.write_text(
        render_structure_preflight_session_log(
            next_session.stage,
            status_after=status_after,
            findings=findings,
            checked_paths=checked_paths,
            started_at_epoch=started_at,
            completed_at_epoch=completed_at,
        ),
        encoding="utf-8",
    )
    decision_log_path.write_text(
        render_structure_preflight_decision_log(
            next_session.stage,
            status_after=status_after,
            findings=findings,
            prompt_path=relative_or_name(prompt_path, ft_root),
        ),
        encoding="utf-8",
    )

    completion_manifest_path = output_dir / f"{next_session.stage}{COMPLETION_MANIFEST_SUFFIX}"
    state_after = dict(state)
    state_after["current_stage"] = next_session.stage
    state_after["stage_status"] = status_after
    state_after["active_transition_prompt"] = relative_or_name(prompt_path, ft_root)
    state_after["blocking_findings"] = [str(finding["id"]) for finding in findings]
    state_after["blocking_reasons"] = (
        [f"{next_session.stage}: deterministic structure preflight found {len(findings)} blocker(s)."]
        if findings
        else []
    )
    deterministic_artifacts = [
        relative_or_name(findings_path, ft_root),
        relative_or_name(session_log_path, ft_root),
        relative_or_name(decision_log_path, ft_root),
        relative_or_name(prompt_path, ft_root),
        relative_or_name(completion_manifest_path, ft_root),
    ]
    latest: list[str] = []
    if isinstance(state.get("latest_artifacts"), list):
        latest.extend(str(item) for item in state["latest_artifacts"])
    latest.extend(deterministic_artifacts)
    state_after["latest_artifacts"] = unique_nonempty_strings(latest)
    state_after["sessions"] = []
    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)
    validate_post_session_state_transition(state, state_after, next_session, state_path)

    final_response_lines = [
        f"# {next_session.stage} deterministic result",
        "",
        f"stage_status: {status_after}",
        f"finding_count: {len(findings)}",
        f"findings: {relative_or_name(findings_path, ft_root)}",
        "",
    ]
    final_response_path = write_session_output(
        cycle_dir,
        next_session.stage,
        "\n".join(final_response_lines),
    )
    input_snapshot = relative_or_name(cycle_dir / "versions" / before_snapshot_id, ft_root)
    output_snapshot = relative_or_name(cycle_dir / "versions" / after_snapshot_id, ft_root)
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state,
        state_after=state_after,
        next_session=next_session,
        thread_id=DETERMINISTIC_STRUCTURE_THREAD_ID,
        turn_id="",
        turn_status="deterministic",
        session_status="completed",
        state_advanced=True,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=final_response_path,
        started_at_epoch=started_at,
        completed_at_epoch=completed_at,
        duration_ms=(completed_at - started_at) * 1000,
        execution_mode="deterministic",
    )

    after_manifest = snapshot_state(state_path, after_snapshot_id)
    append_session_record(
        cycle_dir / "codex-session-map.yaml",
        state,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "execution_mode": "deterministic",
            "thread_id": DETERMINISTIC_STRUCTURE_THREAD_ID,
            "turn_id": "",
            "turn_status": "deterministic",
            "sandbox": "none",
            "approval_mode": "none",
            "model": "",
            "prompt": next_session.prompt_path,
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": relative_or_name(final_response_path, ft_root),
            "completion_manifest": relative_or_name(completion_manifest_path, ft_root),
            "started_at_epoch": started_at,
            "completed_at_epoch": completed_at,
            "duration_ms": (completed_at - started_at) * 1000,
            "state_advanced": True,
            "status": "completed",
        },
    )
    append_runner_event(
        cycle_dir,
        "deterministic_stage_finished",
        stage=next_session.stage,
        scenario=next_session.scenario,
        execution_mode="deterministic",
        stage_status=status_after,
        finding_count=len(findings),
        completion_manifest=relative_or_name(completion_manifest_path, ft_root),
    )
    if runner_lock is not None:
        runner_lock.update(
            stage=next_session.stage,
            scenario=next_session.scenario,
            thread_id=DETERMINISTIC_STRUCTURE_THREAD_ID,
            status="deterministic-stage-completed",
        )

    return {
        "action": "completed-deterministic-session",
        "cycle_id": state["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "deterministic",
        "thread_id": DETERMINISTIC_STRUCTURE_THREAD_ID,
        "turn_id": "",
        "turn_status": "deterministic",
        "session_status": "completed",
        "state_advanced": True,
        "stage_status": status_after,
        "finding_count": len(findings),
        "final_response": str(final_response_path),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_snapshot_id,
        "output_snapshot": after_manifest["snapshot_id"],
        "cwd": cwd or "",
        "approval_mode": approval_mode,
        "model": model or "",
    }


def run_bounded_semantic_review_session(
    state: dict[str, Any],
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    runner_lock: RunnerFileLock | None,
    session_timeout_seconds: int | None,
) -> dict[str, Any]:
    next_session = next_session_for_state(state)
    if next_session is None:
        raise RunnerError(f"No runnable next session for status {state['stage_status']}")
    if next_session.scenario != "reviewer.semantic_traceability_test_design":
        raise RunnerError(f"Bounded semantic review cannot run {next_session.scenario}")

    effective_timeout = effective_session_timeout_seconds(next_session, session_timeout_seconds)
    ft_root = infer_ft_root(state_path)
    cycle_dir = state_path.parent
    output_dir = cycle_dir / "outputs"
    prompt_dir = cycle_dir / "prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    before_snapshot_id = f"before-{next_session.stage}"
    after_snapshot_id = f"after-{next_session.stage}"
    before_manifest = snapshot_state(state_path, before_snapshot_id)
    input_snapshot = relative_or_name(cycle_dir / "versions" / before_snapshot_id, ft_root)
    output_snapshot = relative_or_name(cycle_dir / "versions" / after_snapshot_id, ft_root)
    sdk_cwd = Path(cwd or Path.cwd())
    checked_paths = bounded_semantic_artifact_paths(state, state_path, cwd_base=sdk_cwd)
    prompt = render_bounded_semantic_review_prompt(
        state,
        state_path,
        next_session,
        cwd_base=sdk_cwd,
    )
    prompt_path = prompt_dir / f"prompt.{next_session.stage}.bounded.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    started_at = int(time.time())

    append_runner_event(
        cycle_dir,
        "bounded_semantic_stage_started",
        stage=next_session.stage,
        scenario=next_session.scenario,
        execution_mode="bounded-sdk",
        timeout_seconds=effective_timeout,
    )
    if runner_lock is not None:
        runner_lock.update(
            stage=next_session.stage,
            scenario=next_session.scenario,
            status="running-bounded-semantic-session",
        )

    Codex = load_openai_codex_runtime(required=("Codex",)).Codex
    codex = Codex()
    thread = None
    try:
        thread = start_fresh_sdk_thread(
            codex,
            cwd=cwd or str(Path.cwd()),
            sandbox=sdk_sandbox("read_only"),
            approval_mode=sdk_approval_mode(approval_mode),
            model=model,
        )
        try:
            thread.set_name(f"{state.get('cycle_id')}:{next_session.stage}:bounded")
        except Exception:
            pass
        append_runner_event(
            cycle_dir,
            "thread_started",
            stage=next_session.stage,
            scenario=next_session.scenario,
            thread_id=thread.id,
            execution_mode="bounded-sdk",
        )
        if runner_lock is not None:
            runner_lock.update(
                stage=next_session.stage,
                scenario=next_session.scenario,
                thread_id=thread.id,
                status="running-bounded-semantic-turn",
            )
        append_session_record(
            cycle_dir / "codex-session-map.yaml",
            state,
            {
                "stage": next_session.stage,
                "role": next_session.role,
                "scenario": next_session.scenario,
                "execution_mode": "bounded-sdk",
                "thread_id": thread.id,
                "turn_id": "",
                "turn_status": "",
                "sandbox": "read_only",
                "approval_mode": approval_mode,
                "model": model or "",
                "prompt": relative_or_name(prompt_path, ft_root),
                "input_snapshot": input_snapshot,
                "output_snapshot": "",
                "final_response": "",
                "started_at_epoch": started_at,
                "completed_at_epoch": "",
                "duration_ms": "",
                "status": "started",
            },
        )
        append_runner_event(
            cycle_dir,
            "turn_started",
            stage=next_session.stage,
            thread_id=thread.id,
            execution_mode="bounded-sdk",
        )
        try:
            turn = run_codex_turn_with_timeout(
                thread,
                prompt,
                cwd=cwd or str(Path.cwd()),
                sandbox=sdk_sandbox("read_only"),
                approval_mode=sdk_approval_mode(approval_mode),
                model=model,
                timeout_seconds=effective_timeout,
            )
        except concurrent.futures.TimeoutError:
            append_runner_event(
                cycle_dir,
                "turn_timeout",
                stage=next_session.stage,
                thread_id=thread.id,
                timeout_seconds=effective_timeout or "",
                execution_mode="bounded-sdk",
            )
            if runner_lock is not None:
                runner_lock.update(status="bounded-semantic-timeout-recovered")
            return recover_timed_out_session(
                state_path,
                state_before=state,
                next_session=next_session,
                thread_id=thread.id,
                approval_mode=approval_mode,
                model=model,
                before_snapshot_id=before_snapshot_id,
                after_snapshot_id=after_snapshot_id,
                started_at_epoch=started_at,
                timeout_seconds=effective_timeout,
            )
    finally:
        codex.close()

    completed_at = int(time.time())
    raw_response_path = output_dir / f"{next_session.stage}-response.json"
    final_response_text = str(getattr(turn, "final_response", "") or "")
    try:
        response_payload = normalize_bounded_semantic_response(extract_fenced_json(final_response_text))
        raw_response_path.write_text(
            json.dumps(response_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        status_after = response_payload["recommended_stage_status"]
        round_no = semantic_round_for_stage(next_session.stage)
        findings_path = output_dir / f"round-{round_no}-findings.md"
        matrix_md_path = output_dir / f"round-{round_no}-traceability-matrix.md"
        matrix_xlsx_path = output_dir / f"round-{round_no}-traceability-matrix.xlsx"
        findings_path.write_text(
            render_bounded_semantic_findings(next_session.stage, response_payload),
            encoding="utf-8",
        )
        matrix_md_path.write_text(render_bounded_semantic_matrix(response_payload), encoding="utf-8")
        write_bounded_semantic_matrix_xlsx(matrix_xlsx_path, response_payload["traceability_matrix_rows"])
        if status_after == "semantic-revision-needed":
            next_prompt = prompt_dir / f"prompt.writer-r{round_no + 1}.md"
            next_prompt.write_text(
                render_writer_semantic_prompt(
                    next_session,
                    relative_or_name(findings_path, ft_root),
                ),
                encoding="utf-8",
            )
        else:
            next_prompt = prompt_dir / "prompt.structure-format-final.md"
            next_prompt.write_text(render_structure_format_prompt(next_session), encoding="utf-8")
        session_log_path = output_dir / f"reviewer-session-log.{next_session.stage}.md"
        decision_log_path = output_dir / f"agent-decision-log.{next_session.stage}.md"
        session_log_path.write_text(
            render_bounded_semantic_session_log(
                next_session,
                status_after=status_after,
                response=response_payload,
                checked_paths=checked_paths,
                started_at_epoch=started_at,
                completed_at_epoch=completed_at,
                thread_id=thread.id,
                turn_id=turn.id,
            ),
            encoding="utf-8",
        )
        decision_log_path.write_text(
            render_bounded_semantic_decision_log(
                next_session,
                status_after=status_after,
                response=response_payload,
                prompt_path=relative_or_name(next_prompt, ft_root),
            ),
            encoding="utf-8",
        )
        state_after = dict(state)
        state_after["current_stage"] = next_session.stage
        state_after["stage_status"] = status_after
        state_after["semantic_round"] = round_no
        state_after["active_transition_prompt"] = relative_or_name(next_prompt, ft_root)
        state_after["blocking_findings"] = [
            str(finding.get("id") or "")
            for finding in response_payload["findings"]
            if str(finding.get("severity") or "").lower() in BOUNDED_SEMANTIC_BLOCKING_SEVERITIES
        ]
        state_after["blocking_reasons"] = (
            [f"{next_session.stage}: bounded semantic review found blocking findings."]
            if state_after["blocking_findings"]
            else []
        )
        semantic_artifacts = [
            relative_or_name(raw_response_path, ft_root),
            relative_or_name(findings_path, ft_root),
            relative_or_name(matrix_md_path, ft_root),
            relative_or_name(matrix_xlsx_path, ft_root),
            relative_or_name(session_log_path, ft_root),
            relative_or_name(decision_log_path, ft_root),
            relative_or_name(prompt_path, ft_root),
            relative_or_name(next_prompt, ft_root),
            relative_or_name(output_dir / f"{next_session.stage}{COMPLETION_MANIFEST_SUFFIX}", ft_root),
        ]
        state_after["latest_artifacts"] = unique_nonempty_strings(
            state.get("latest_artifacts"),
            semantic_artifacts,
        )
        state_after["sessions"] = []
        final_output_path = write_session_output(
            cycle_dir,
            next_session.stage,
            "\n".join(
                [
                    f"# {next_session.stage} bounded semantic result",
                    "",
                    f"stage_status: {status_after}",
                    f"finding_count: {len(response_payload['findings'])}",
                    f"findings: {relative_or_name(findings_path, ft_root)}",
                    "",
                ]
            ),
        )
    except Exception as exc:
        invalid_path = write_bounded_semantic_invalid_response_artifact(
            output_dir,
            next_session.stage,
            final_response_text,
            exc,
        )
        state_after = dict(state)
        state_after["current_stage"] = next_session.stage
        state_after["stage_status"] = "blocked-input"
        state_after["active_transition_prompt"] = next_session.prompt_path
        state_after["blocking_reasons"] = [f"{next_session.stage}: bounded semantic reviewer returned invalid JSON"]
        state_after["blocking_findings"] = []
        state_after["latest_artifacts"] = unique_nonempty_strings(
            state.get("latest_artifacts"),
            relative_or_name(invalid_path, ft_root),
            relative_or_name(raw_response_path, ft_root),
            relative_or_name(output_dir / f"{next_session.stage}{COMPLETION_MANIFEST_SUFFIX}", ft_root),
        )
        state_after["sessions"] = []
        raw_response_path.write_text(final_response_text, encoding="utf-8")
        final_output_path = invalid_path
        status_after = "blocked-input"

    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)
    validate_post_session_state_transition(state, state_after, next_session, state_path)
    turn_status = enum_value(turn.status)
    session_status = "completed" if status_after != "blocked-input" else "failed"
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state,
        state_after=state_after,
        next_session=next_session,
        thread_id=thread.id,
        turn_id=turn.id,
        turn_status=turn_status,
        session_status=session_status,
        state_advanced=True,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=final_output_path,
        started_at_epoch=started_at,
        completed_at_epoch=completed_at,
        duration_ms=getattr(turn, "duration_ms", "") or (completed_at - started_at) * 1000,
        execution_mode="bounded-sdk",
    )
    after_manifest = snapshot_state(state_path, after_snapshot_id)
    append_session_record(
        cycle_dir / "codex-session-map.yaml",
        state,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "execution_mode": "bounded-sdk",
            "thread_id": thread.id,
            "turn_id": turn.id,
            "turn_status": turn_status,
            "sandbox": "read_only",
            "approval_mode": approval_mode,
            "model": model or "",
            "prompt": relative_or_name(prompt_path, ft_root),
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": relative_or_name(final_output_path, ft_root),
            "completion_manifest": relative_or_name(completion_manifest_path, ft_root),
            "started_at_epoch": started_at,
            "completed_at_epoch": completed_at,
            "duration_ms": getattr(turn, "duration_ms", "") or (completed_at - started_at) * 1000,
            "state_advanced": True,
            "status": session_status,
        },
    )
    append_runner_event(
        cycle_dir,
        "bounded_semantic_stage_finished",
        stage=next_session.stage,
        scenario=next_session.scenario,
        execution_mode="bounded-sdk",
        stage_status=status_after,
        thread_id=thread.id,
        turn_id=turn.id,
        completion_manifest=relative_or_name(completion_manifest_path, ft_root),
    )
    if runner_lock is not None:
        runner_lock.update(status="bounded-semantic-stage-completed")
    return {
        "action": "completed-bounded-semantic-session",
        "cycle_id": state["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "bounded-sdk",
        "thread_id": thread.id,
        "turn_id": turn.id,
        "turn_status": turn_status,
        "session_status": session_status,
        "state_advanced": True,
        "stage_status": status_after,
        "final_response": str(final_output_path),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_manifest["snapshot_id"],
        "output_snapshot": after_manifest["snapshot_id"],
    }


def run_bounded_reviewer_session(
    state: dict[str, Any],
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    runner_lock: RunnerFileLock | None,
    session_timeout_seconds: int | None,
) -> dict[str, Any]:
    next_session = next_session_for_state(state)
    if next_session is None:
        raise RunnerError(f"No runnable next session for status {state['stage_status']}")
    if next_session.scenario not in BOUNDED_REVIEWER_SCENARIOS:
        raise RunnerError(f"Bounded reviewer cannot run {next_session.scenario}")

    effective_timeout = effective_session_timeout_seconds(next_session, session_timeout_seconds)
    ft_root = infer_ft_root(state_path)
    cycle_dir = state_path.parent
    output_dir = cycle_dir / "outputs"
    prompt_dir = cycle_dir / "prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    before_snapshot_id = f"before-{next_session.stage}"
    after_snapshot_id = f"after-{next_session.stage}"
    before_manifest = snapshot_state(state_path, before_snapshot_id)
    input_snapshot = relative_or_name(cycle_dir / "versions" / before_snapshot_id, ft_root)
    output_snapshot = relative_or_name(cycle_dir / "versions" / after_snapshot_id, ft_root)
    sdk_cwd = Path(cwd or Path.cwd())
    checked_paths = bounded_reviewer_artifact_paths(
        state,
        state_path,
        next_session,
        cwd_base=sdk_cwd,
    )
    prompt = render_bounded_reviewer_prompt(
        state,
        state_path,
        next_session,
        cwd_base=sdk_cwd,
    )
    prompt_path = prompt_dir / f"prompt.{next_session.stage}.bounded.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    started_at = int(time.time())

    append_runner_event(
        cycle_dir,
        "bounded_reviewer_stage_started",
        stage=next_session.stage,
        scenario=next_session.scenario,
        execution_mode="bounded-sdk",
        timeout_seconds=effective_timeout,
    )
    if runner_lock is not None:
        runner_lock.update(
            stage=next_session.stage,
            scenario=next_session.scenario,
            status="running-bounded-reviewer-session",
        )

    Codex = load_openai_codex_runtime(required=("Codex",)).Codex
    codex = Codex()
    thread = None
    try:
        thread = start_fresh_sdk_thread(
            codex,
            cwd=cwd or str(Path.cwd()),
            sandbox=sdk_sandbox("read_only"),
            approval_mode=sdk_approval_mode(approval_mode),
            model=model,
        )
        try:
            thread.set_name(f"{state.get('cycle_id')}:{next_session.stage}:bounded")
        except Exception:
            pass
        append_runner_event(
            cycle_dir,
            "thread_started",
            stage=next_session.stage,
            scenario=next_session.scenario,
            thread_id=thread.id,
            execution_mode="bounded-sdk",
        )
        if runner_lock is not None:
            runner_lock.update(
                stage=next_session.stage,
                scenario=next_session.scenario,
                thread_id=thread.id,
                status="running-bounded-reviewer-turn",
            )
        append_session_record(
            cycle_dir / "codex-session-map.yaml",
            state,
            {
                "stage": next_session.stage,
                "role": next_session.role,
                "scenario": next_session.scenario,
                "execution_mode": "bounded-sdk",
                "thread_id": thread.id,
                "turn_id": "",
                "turn_status": "",
                "sandbox": "read_only",
                "approval_mode": approval_mode,
                "model": model or "",
                "prompt": relative_or_name(prompt_path, ft_root),
                "input_snapshot": input_snapshot,
                "output_snapshot": "",
                "final_response": "",
                "started_at_epoch": started_at,
                "completed_at_epoch": "",
                "duration_ms": "",
                "status": "started",
            },
        )
        append_runner_event(
            cycle_dir,
            "turn_started",
            stage=next_session.stage,
            thread_id=thread.id,
            execution_mode="bounded-sdk",
        )
        try:
            turn = run_codex_turn_with_timeout(
                thread,
                prompt,
                cwd=cwd or str(Path.cwd()),
                sandbox=sdk_sandbox("read_only"),
                approval_mode=sdk_approval_mode(approval_mode),
                model=model,
                timeout_seconds=effective_timeout,
            )
        except concurrent.futures.TimeoutError:
            append_runner_event(
                cycle_dir,
                "turn_timeout",
                stage=next_session.stage,
                thread_id=thread.id,
                timeout_seconds=effective_timeout or "",
                execution_mode="bounded-sdk",
            )
            if runner_lock is not None:
                runner_lock.update(status="bounded-reviewer-timeout-recovered")
            return recover_timed_out_session(
                state_path,
                state_before=state,
                next_session=next_session,
                thread_id=thread.id,
                approval_mode=approval_mode,
                model=model,
                before_snapshot_id=before_snapshot_id,
                after_snapshot_id=after_snapshot_id,
                started_at_epoch=started_at,
                timeout_seconds=effective_timeout,
            )
    finally:
        codex.close()

    completed_at = int(time.time())
    raw_response_path = output_dir / f"{next_session.stage}-response.json"
    final_response_text = str(getattr(turn, "final_response", "") or "")
    try:
        response_payload = normalize_bounded_reviewer_response(
            extract_fenced_json(final_response_text),
            next_session,
        )
        raw_response_path.write_text(
            json.dumps(response_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        status_after = response_payload["recommended_stage_status"]
        findings_path = output_dir / f"{next_session.stage}-findings.md"
        findings_path.write_text(
            render_bounded_reviewer_findings(
                next_session.stage,
                response_payload,
                scenario=next_session.scenario,
            ),
            encoding="utf-8",
        )
        next_prompt = next_prompt_for_bounded_reviewer(
            state,
            state_path,
            next_session,
            status_after,
            findings_path,
        )
        session_log_path = output_dir / f"reviewer-session-log.{next_session.stage}.md"
        decision_log_path = output_dir / f"agent-decision-log.{next_session.stage}.md"
        session_log_path.write_text(
            render_bounded_semantic_session_log(
                next_session,
                status_after=status_after,
                response=response_payload,
                checked_paths=checked_paths,
                started_at_epoch=started_at,
                completed_at_epoch=completed_at,
                thread_id=thread.id,
                turn_id=turn.id,
            ),
            encoding="utf-8",
        )
        decision_log_path.write_text(
            render_bounded_semantic_decision_log(
                next_session,
                status_after=status_after,
                response=response_payload,
                prompt_path=relative_or_name(next_prompt, ft_root),
            ),
            encoding="utf-8",
        )
        state_after = dict(state)
        state_after["current_stage"] = next_session.stage
        state_after["stage_status"] = status_after
        state_after["active_transition_prompt"] = relative_or_name(next_prompt, ft_root)
        state_after["blocking_findings"] = [
            str(finding.get("id") or "")
            for finding in response_payload["findings"]
            if str(finding.get("severity") or "").lower() in BOUNDED_SEMANTIC_BLOCKING_SEVERITIES
        ]
        state_after["blocking_reasons"] = (
            [f"{next_session.stage}: bounded reviewer found blocking findings."]
            if state_after["blocking_findings"] and status_after != "signed-off"
            else []
        )
        reviewer_artifacts = [
            relative_or_name(raw_response_path, ft_root),
            relative_or_name(findings_path, ft_root),
            relative_or_name(session_log_path, ft_root),
            relative_or_name(decision_log_path, ft_root),
            relative_or_name(prompt_path, ft_root),
            relative_or_name(next_prompt, ft_root),
            relative_or_name(output_dir / f"{next_session.stage}{COMPLETION_MANIFEST_SUFFIX}", ft_root),
        ]
        state_after["latest_artifacts"] = unique_nonempty_strings(
            state.get("latest_artifacts"),
            reviewer_artifacts,
        )
        state_after["sessions"] = []
        final_output_path = write_session_output(
            cycle_dir,
            next_session.stage,
            "\n".join(
                [
                    f"# {next_session.stage} bounded reviewer result",
                    "",
                    f"stage_status: {status_after}",
                    f"finding_count: {len(response_payload['findings'])}",
                    f"findings: {relative_or_name(findings_path, ft_root)}",
                    "",
                ]
            ),
        )
    except Exception as exc:
        invalid_path = write_bounded_semantic_invalid_response_artifact(
            output_dir,
            next_session.stage,
            final_response_text,
            exc,
        )
        state_after = dict(state)
        state_after["current_stage"] = next_session.stage
        state_after["stage_status"] = "blocked-input"
        state_after["active_transition_prompt"] = next_session.prompt_path
        state_after["blocking_reasons"] = [f"{next_session.stage}: bounded reviewer returned invalid JSON"]
        state_after["blocking_findings"] = []
        state_after["latest_artifacts"] = unique_nonempty_strings(
            state.get("latest_artifacts"),
            relative_or_name(invalid_path, ft_root),
            relative_or_name(raw_response_path, ft_root),
            relative_or_name(output_dir / f"{next_session.stage}{COMPLETION_MANIFEST_SUFFIX}", ft_root),
        )
        state_after["sessions"] = []
        raw_response_path.write_text(final_response_text, encoding="utf-8")
        final_output_path = invalid_path
        status_after = "blocked-input"

    write_simple_yaml(state_path, state_after)
    validate_state(state_after, state_path)
    validate_post_session_state_transition(state, state_after, next_session, state_path)
    turn_status = enum_value(turn.status)
    session_status = "completed" if status_after != "blocked-input" else "failed"
    completion_manifest_path = write_completion_manifest(
        state_path,
        state_before=state,
        state_after=state_after,
        next_session=next_session,
        thread_id=thread.id,
        turn_id=turn.id,
        turn_status=turn_status,
        session_status=session_status,
        state_advanced=True,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        final_response=final_output_path,
        started_at_epoch=started_at,
        completed_at_epoch=completed_at,
        duration_ms=getattr(turn, "duration_ms", "") or (completed_at - started_at) * 1000,
        execution_mode="bounded-sdk",
    )
    after_manifest = snapshot_state(state_path, after_snapshot_id)
    append_session_record(
        cycle_dir / "codex-session-map.yaml",
        state,
        {
            "stage": next_session.stage,
            "role": next_session.role,
            "scenario": next_session.scenario,
            "execution_mode": "bounded-sdk",
            "thread_id": thread.id,
            "turn_id": turn.id,
            "turn_status": turn_status,
            "sandbox": "read_only",
            "approval_mode": approval_mode,
            "model": model or "",
            "prompt": relative_or_name(prompt_path, ft_root),
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "final_response": relative_or_name(final_output_path, ft_root),
            "completion_manifest": relative_or_name(completion_manifest_path, ft_root),
            "started_at_epoch": started_at,
            "completed_at_epoch": completed_at,
            "duration_ms": getattr(turn, "duration_ms", "") or (completed_at - started_at) * 1000,
            "state_advanced": True,
            "status": session_status,
        },
    )
    append_runner_event(
        cycle_dir,
        "bounded_reviewer_stage_finished",
        stage=next_session.stage,
        scenario=next_session.scenario,
        execution_mode="bounded-sdk",
        stage_status=status_after,
        thread_id=thread.id,
        turn_id=turn.id,
        completion_manifest=relative_or_name(completion_manifest_path, ft_root),
    )
    if runner_lock is not None:
        runner_lock.update(status="bounded-reviewer-stage-completed")
    return {
        "action": "completed-bounded-reviewer-session",
        "cycle_id": state["cycle_id"],
        "stage": next_session.stage,
        "role": next_session.role,
        "scenario": next_session.scenario,
        "execution_mode": "bounded-sdk",
        "thread_id": thread.id,
        "turn_id": turn.id,
        "turn_status": turn_status,
        "session_status": session_status,
        "state_advanced": True,
        "stage_status": status_after,
        "final_response": str(final_output_path),
        "completion_manifest": str(completion_manifest_path),
        "input_snapshot": before_manifest["snapshot_id"],
        "output_snapshot": after_manifest["snapshot_id"],
    }


def run_real_session_process_supervised(
    state: dict[str, Any],
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    runner_lock: RunnerFileLock | None,
    session_timeout_seconds: int,
) -> dict[str, Any]:
    next_session = next_session_for_state(state)
    if next_session is None:
        raise RunnerError(f"No runnable next session for status {state['stage_status']}")
    session_timeout_seconds = effective_session_timeout_seconds(
        next_session,
        session_timeout_seconds,
    )

    ft_root = infer_ft_root(state_path)
    run_cwd = cwd or str(Path.cwd())
    before_snapshot_id = f"before-{next_session.stage}"
    after_snapshot_id = f"after-{next_session.stage}"
    snapshot_state(state_path, before_snapshot_id)

    output_dir = state_path.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload_path = output_dir / f"{next_session.stage}-child-payload-{os.getpid()}.json"
    started_at = int(time.time())
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_run-session-child",
        "--state",
        str(state_path),
        "--payload-out",
        str(payload_path),
        "--approval-mode",
        approval_mode,
    ]
    if cwd:
        command.extend(["--cwd", cwd])
    if model:
        command.extend(["--model", model])

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    append_runner_event(
        state_path.parent,
        "session_child_started",
        stage=next_session.stage,
        timeout_seconds=session_timeout_seconds,
        payload=relative_or_name(payload_path, ft_root),
    )
    if runner_lock is not None:
        runner_lock.update(
            stage=next_session.stage,
            scenario=next_session.scenario,
            status="running-session-child",
        )

    process = subprocess.Popen(
        command,
        cwd=run_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    try:
        stdout, stderr = process.communicate(timeout=session_timeout_seconds)
    except subprocess.TimeoutExpired:
        completed_payload = read_child_payload(payload_path)
        process.kill()
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", "child process did not exit after kill"
        if completed_payload is None:
            completed_payload = read_child_payload(payload_path)
        timeout_diagnostics = child_timeout_diagnostics(
            state_path.parent,
            stage=next_session.stage,
            started_at_epoch=started_at,
        )
        diagnostic_thread_id = str(timeout_diagnostics.get("thread_id") or f"child-pid-{process.pid}")
        if runner_lock is not None and timeout_diagnostics.get("thread_id"):
            runner_lock.update(thread_id=diagnostic_thread_id)
        if completed_payload is not None:
            updated_state = load_simple_yaml(state_path)
            validate_state(updated_state, state_path)
            if state_progress_marker(updated_state) != state_progress_marker(state):
                validate_post_session_state_transition(
                    state,
                    updated_state,
                    next_session,
                    state_path,
                )
            append_runner_event(
                state_path.parent,
                "session_child_timeout_after_payload",
                stage=next_session.stage,
                child_pid=process.pid,
                timeout_seconds=session_timeout_seconds,
                payload=relative_or_name(payload_path, ft_root),
                child_timeout_phase=timeout_diagnostics["timeout_phase"],
                thread_id=diagnostic_thread_id,
                thread_started_epoch=timeout_diagnostics["thread_started_epoch"],
                turn_started_epoch=timeout_diagnostics["turn_started_epoch"],
                stdout_tail=(stdout or "")[-1000:],
                stderr_tail=(stderr or "")[-1000:],
            )
            if runner_lock is not None:
                runner_lock.update(status="session-child-completed-after-timeout")
            return completed_payload
        progress_payload = completed_payload_from_timed_out_state_progress(
            state_path,
            state_before=state,
            next_session=next_session,
            thread_id=diagnostic_thread_id,
            approval_mode=approval_mode,
            model=model,
            before_snapshot_id=before_snapshot_id,
            after_snapshot_id=after_snapshot_id,
            started_at_epoch=started_at,
            timeout_seconds=session_timeout_seconds,
        )
        if progress_payload is not None:
            if runner_lock is not None:
                runner_lock.update(status="session-child-progress-after-timeout")
            return progress_payload
        artifact_progress_payload = completed_payload_from_timed_out_writer_artifact_progress(
            state_path,
            state_before=state,
            next_session=next_session,
            thread_id=diagnostic_thread_id,
            approval_mode=approval_mode,
            model=model,
            before_snapshot_id=before_snapshot_id,
            after_snapshot_id=after_snapshot_id,
            started_at_epoch=started_at,
            timeout_seconds=session_timeout_seconds,
        )
        if artifact_progress_payload is not None:
            if runner_lock is not None:
                runner_lock.update(status="session-child-artifact-progress-after-timeout")
            return artifact_progress_payload
        append_runner_event(
            state_path.parent,
            "session_child_timeout",
            stage=next_session.stage,
            child_pid=process.pid,
            timeout_seconds=session_timeout_seconds,
            child_timeout_phase=timeout_diagnostics["timeout_phase"],
            thread_id=diagnostic_thread_id,
            thread_started_epoch=timeout_diagnostics["thread_started_epoch"],
            turn_started_epoch=timeout_diagnostics["turn_started_epoch"],
            stdout_tail=(stdout or "")[-1000:],
            stderr_tail=(stderr or "")[-1000:],
        )
        if runner_lock is not None:
            runner_lock.update(status="session-timeout-recovered")
        return recover_timed_out_session(
            state_path,
            state_before=state,
            next_session=next_session,
            thread_id=diagnostic_thread_id,
            approval_mode=approval_mode,
            model=model,
            before_snapshot_id=before_snapshot_id,
            after_snapshot_id=after_snapshot_id,
            started_at_epoch=started_at,
            timeout_seconds=session_timeout_seconds,
        )

    if process.returncode != 0:
        append_runner_event(
            state_path.parent,
            "session_child_failed",
            stage=next_session.stage,
            child_pid=process.pid,
            returncode=process.returncode,
            stdout_tail=(stdout or "")[-1000:],
            stderr_tail=(stderr or "")[-1000:],
        )
        detail = (stderr or stdout or "").strip()
        raise RunnerError(f"session child failed with exit code {process.returncode}: {detail}")

    if not payload_path.exists():
        raise RunnerError(f"session child did not write payload: {payload_path}")
    payload = read_child_payload(payload_path)
    if payload is None:
        raise RunnerError(f"session child wrote invalid payload JSON: {payload_path}")
    updated_state = load_simple_yaml(state_path)
    validate_state(updated_state, state_path)
    if state_progress_marker(updated_state) != state_progress_marker(state):
        validate_post_session_state_transition(
            state,
            updated_state,
            next_session,
            state_path,
        )
    append_runner_event(
        state_path.parent,
        "session_child_completed",
        stage=next_session.stage,
        child_pid=process.pid,
        payload=relative_or_name(payload_path, ft_root),
    )
    return payload


def run_real_session(
    state: dict[str, Any],
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    runner_lock: RunnerFileLock | None = None,
    session_timeout_seconds: int | None = None,
    process_supervised: bool = True,
) -> dict[str, Any]:
    next_session = next_session_for_state(state)
    if next_session is None:
        raise RunnerError(f"No runnable next session for status {state['stage_status']}")
    if next_session.scenario == "reviewer.structure_preflight":
        return run_deterministic_structure_preflight(
            state,
            state_path,
            cwd=cwd,
            approval_mode=approval_mode,
            model=model,
            runner_lock=runner_lock,
        )
    if next_session.scenario == "reviewer.semantic_traceability_test_design":
        return run_bounded_semantic_review_session(
            state,
            state_path,
            cwd=cwd,
            approval_mode=approval_mode,
            model=model,
            runner_lock=runner_lock,
            session_timeout_seconds=session_timeout_seconds,
        )
    if next_session.scenario in BOUNDED_REVIEWER_SCENARIOS:
        return run_bounded_reviewer_session(
            state,
            state_path,
            cwd=cwd,
            approval_mode=approval_mode,
            model=model,
            runner_lock=runner_lock,
            session_timeout_seconds=session_timeout_seconds,
        )
    effective_timeout = effective_session_timeout_seconds(
        next_session,
        session_timeout_seconds,
    )
    if effective_timeout > 0 and process_supervised:
        return run_real_session_process_supervised(
            state,
            state_path,
            cwd=cwd,
            approval_mode=approval_mode,
            model=model,
            runner_lock=runner_lock,
            session_timeout_seconds=effective_timeout,
        )

    Codex = load_openai_codex_runtime(required=("Codex",)).Codex

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
        thread = start_fresh_sdk_thread(
            codex,
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
            turn = run_codex_turn_with_timeout(
                thread,
                prompt,
                cwd=run_cwd,
                sandbox=sdk_sandbox(next_session.sandbox_policy),
                approval_mode=sdk_approval_mode(approval_mode),
                model=model,
                timeout_seconds=effective_timeout,
            )
        except concurrent.futures.TimeoutError:
            append_runner_event(
                state_path.parent,
                "turn_timeout",
                stage=next_session.stage,
                thread_id=thread.id,
                timeout_seconds=effective_timeout or "",
            )
            if runner_lock is not None:
                runner_lock.update(status="session-timeout-recovered")
            return recover_timed_out_session(
                state_path,
                state_before=state,
                next_session=next_session,
                thread_id=thread.id,
                approval_mode=approval_mode,
                model=model,
                before_snapshot_id=before_snapshot_id,
                after_snapshot_id=after_snapshot_id,
                started_at_epoch=started_at,
                timeout_seconds=effective_timeout,
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
    if state_advanced:
        validate_post_session_state_transition(
            state,
            updated_state,
            next_session,
            state_path,
        )
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


def validate_post_session_state_transition(
    state_before: dict[str, Any],
    state_after: dict[str, Any],
    next_session: NextSession,
    state_path: Path,
) -> None:
    del state_before, state_path
    status = str(state_after.get("stage_status") or "")
    if status in TERMINAL_STATUSES:
        return

    allowed = POST_SESSION_ALLOWED_STAGE_STATUSES.get(next_session.scenario)
    if allowed is None:
        return
    if status in allowed:
        return

    expected = ", ".join(sorted([*allowed, *TERMINAL_STATUSES]))
    raise RunnerError(
        f"Stage {next_session.stage} ({next_session.scenario}) produced invalid post-session "
        f"stage_status={status!r}; expected one of: {expected}"
    )


def run_until_terminal(
    state_path: Path,
    *,
    cwd: str | None,
    approval_mode: str,
    model: str | None,
    max_sessions: int,
    runner_lock: RunnerFileLock | None = None,
    session_timeout_seconds: int | None = None,
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
            gate = enforce_terminal_signed_off_validator_gate(state, state_path)
            return {
                "action": "completed-chain" if status in TERMINAL_STATUSES else "stopped-chain",
                "state": str(state_path),
                "final_status": status,
                "terminal": status in TERMINAL_STATUSES,
                "sessions_started": len(completed_sessions),
                "sessions": completed_sessions,
                "terminal_validator_gate": gate,
            }

        before_marker = state_progress_marker(state)
        session_kwargs: dict[str, Any] = {
            "cwd": cwd,
            "approval_mode": approval_mode,
            "model": model,
            "runner_lock": runner_lock,
        }
        if session_timeout_seconds:
            session_kwargs["session_timeout_seconds"] = session_timeout_seconds
        payload = run_real_session(state, state_path, **session_kwargs)
        completed_sessions.append(payload)
        updated_state = load_simple_yaml(state_path)
        validate_state(updated_state, state_path)
        state_advanced = state_progress_marker(updated_state) != before_marker
        if not state_advanced:
            raise RunnerError(
                f"cycle-state.yaml did not advance after {payload.get('stage')}; stopping to avoid repeating the same stage"
            )
        validate_post_session_state_transition(
            state,
            updated_state,
            next_session,
            state_path,
        )
        session_status = payload.get("session_status")
        if session_status is None:
            session_status = classify_session_status(
                str(payload.get("turn_status") or ""),
                state_advanced=state_advanced,
            )
        if session_status not in CHAIN_ACCEPTED_SESSION_STATUSES:
            if str(updated_state.get("stage_status") or "") in TERMINAL_STATUSES:
                gate = enforce_terminal_signed_off_validator_gate(updated_state, state_path)
                return {
                    "action": "completed-chain",
                    "state": str(state_path),
                    "final_status": str(updated_state.get("stage_status") or ""),
                    "terminal": True,
                    "sessions_started": len(completed_sessions),
                    "sessions": completed_sessions,
                    "terminal_validator_gate": gate,
                }
            raise RunnerError(
                f"Stage {payload.get('stage')} finished with turn_status={payload.get('turn_status')}; stopping chain"
            )

    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    status = str(state.get("stage_status") or "")
    next_session = next_session_for_state(state)
    if status in TERMINAL_STATUSES or next_session is None:
        gate = enforce_terminal_signed_off_validator_gate(state, state_path)
        return {
            "action": "completed-chain" if status in TERMINAL_STATUSES else "stopped-chain",
            "state": str(state_path),
            "final_status": status,
            "terminal": status in TERMINAL_STATUSES,
            "sessions_started": len(completed_sessions),
            "sessions": completed_sessions,
            "terminal_validator_gate": gate,
        }
    return {
        "action": "max-sessions-reached",
        "state": str(state_path),
        "final_status": status,
        "terminal": False,
        "sessions_started": len(completed_sessions),
        "sessions": completed_sessions,
        "next": next_session_summary(state),
        "note": f"max_sessions={max_sessions} reached before terminal status; rerun to continue from stage_status={status}",
    }


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


def blocked_timeout_recovery_contract(
    state_path: Path,
    state: dict[str, Any],
) -> dict[str, Any] | None:
    reasons = [str(item) for item in state.get("blocking_reasons") or []]
    if not any("timed out" in reason or "timeout" in reason for reason in reasons):
        return None
    writer_stage = ""
    for reason in reasons:
        if reason.startswith("writer"):
            writer_stage = reason.split(":", 1)[0]
            break
    if not writer_stage:
        return None
    prompt_path = str(state.get("active_transition_prompt") or "")
    profile_stage = str(state.get("current_stage") or writer_stage)
    profile_path = state_path.parent / "outputs" / f"scoped-validator-profile.{profile_stage}.json"
    ft_root = infer_ft_root(state_path)
    return {
        "blocked_reason": "writer-timeout-recovery",
        "timed_out_stage": writer_stage,
        "expected_profile": relative_or_name(profile_path, ft_root),
        "profile_exists": profile_path.exists(),
        "active_transition_prompt": prompt_path,
        "resume_starts_new_writer": False,
        "recovery_action": (
            "resolve scoped validator findings or regenerate the expected profile before resume; "
            "blocked-input has no runnable next session"
        ),
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
    last_event = last_runner_event(cycle_dir)
    payload["events"] = {
        "path": str(event_path),
        "exists": event_path.exists(),
        "last_event": last_event,
        "scoped_validator_profile_consistency": scoped_validator_profile_event_consistency(
            last_event,
            ft_root=ft_root,
        ),
    }

    output_dir = cycle_dir / "outputs"
    manifests = sorted(output_dir.glob(f"*{COMPLETION_MANIFEST_SUFFIX}")) if output_dir.exists() else []
    payload["completion_manifests"] = [relative_or_name(path, ft_root) for path in manifests]
    if state is not None:
        next_session = next_session_for_state(state)
        timeout_contract = blocked_timeout_recovery_contract(state_path, state)
        if timeout_contract is not None:
            payload["timeout_recovery_contract"] = timeout_contract
        if next_session is not None:
            expected_manifest = completion_manifest_path_for_stage(state_path, next_session.stage)
            next_review = (
                next_writer_review_prompt(state_path, state, next_session)
                if next_session.role == "writer"
                else None
            )
            payload["completion_contract"] = {
                "stage": next_session.stage,
                "role": next_session.role,
                "scenario": next_session.scenario,
                "expected_completion_manifest": relative_or_name(expected_manifest, ft_root),
                "completion_manifest_exists": expected_manifest.exists(),
                "expected_terminal_events": ["turn_finished", "stage_completed"],
                "actual_last_event": last_event,
                "missing": [] if expected_manifest.exists() else ["completion_manifest"],
                "recoverable_writer_next_state": (
                    {
                        "current_stage": next_review[0],
                        "stage_status": next_review[1],
                        "semantic_round": next_review[2],
                        "active_transition_prompt": f"work/review-cycles/{state.get('scope_slug')}/prompts/{next_review[3]}",
                    }
                    if next_review is not None
                    else None
                ),
            }

    status = str(payload.get("stage_status") or "")
    if status == "signed-off":
        payload["terminal_validator_gate"] = {
            "checked": False,
            "reason": "doctor does not run the full terminal validator gate; run `validate` or `run-until-terminal` to enforce signed-off quality gates",
        }
    scoped_validator_profile_consistency = payload["events"].get("scoped_validator_profile_consistency") or {}
    has_event_profile_drift = (
        scoped_validator_profile_consistency.get("checked") is True
        and scoped_validator_profile_consistency.get("consistent") is False
    )
    if not payload["state_valid"]:
        recommendation = "fix-state-before-running"
    elif lock.get("exists"):
        if lock.get("safe_to_recover"):
            recommendation = "resume-with---recover-stale-lock"
        elif lock.get("stale"):
            recommendation = "inspect-lock-pid-before-recovery"
        else:
            recommendation = "wait-for-active-runner-or-investigate-lock"
    elif has_event_profile_drift:
        recommendation = "inspect-event-profile-drift"
    elif status == "signed-off":
        recommendation = "run-validate-terminal-gate"
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


def build_recover_only_payload(
    state_path: Path,
    *,
    stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
) -> dict[str, Any]:
    state = load_simple_yaml(state_path)
    lock = lock_diagnostics(state_path, stale_lock_seconds=stale_lock_seconds)
    next_session = next_session_summary(state)
    if lock.get("exists"):
        recommendation = "inspect-lock-after-recovery"
    elif str(state.get("stage_status") or "") in TERMINAL_STATUSES:
        recommendation = "no-action-terminal-status"
    elif next_session is None:
        recommendation = "no-runnable-next-stage"
    elif isinstance(next_session, dict) and next_session.get("error"):
        recommendation = "fix-transition-before-running"
    else:
        recommendation = "run-next-stage"
    return {
        "action": "recovered-stale-lock",
        "state": str(state_path),
        "cycle_dir": str(state_path.parent),
        "cycle_id": state.get("cycle_id") or "",
        "ft_slug": state.get("ft_slug") or "",
        "scope_slug": state.get("scope_slug") or "",
        "current_stage": state.get("current_stage") or "",
        "stage_status": state.get("stage_status") or "",
        "semantic_round": state.get("semantic_round") or "",
        "next": next_session,
        "lock": lock,
        "recommendation": recommendation,
        "note": "recover-only archived a stale lock and did not run validator or start the next session",
    }


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
    gate = enforce_terminal_signed_off_validator_gate(state, state_path)
    payload = {
        "valid": True,
        "state": str(state_path),
        "next": build_dry_run_payload(state, state_path),
        "terminal_validator_gate": gate,
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
    if next_session_requires_sdk(next_session_for_state(state)):
        ensure_openai_codex_runtime_available()
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
            session_timeout_seconds=args.session_timeout_seconds,
        )
    if not payload.get("state_advanced"):
        raise RunnerError(
            f"cycle-state.yaml did not advance after {payload.get('stage')}; stopping to avoid repeating the same stage"
        )
    updated_state = load_simple_yaml(state_path)
    validate_state(updated_state, state_path)
    if payload.get("session_status") not in CHAIN_ACCEPTED_SESSION_STATUSES:
        if str(updated_state.get("stage_status") or "") not in TERMINAL_STATUSES:
            raise RunnerError(
                f"Stage {payload.get('stage')} finished with turn_status={payload.get('turn_status')}; stopping chain"
            )
    payload["terminal_validator_gate"] = enforce_terminal_signed_off_validator_gate(
        updated_state,
        state_path,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_run_session_child(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_simple_yaml(state_path)
    validate_state(state, state_path)
    payload = run_real_session(
        state,
        state_path,
        cwd=args.cwd,
        approval_mode=args.approval_mode,
        model=args.model,
        runner_lock=None,
        session_timeout_seconds=0,
        process_supervised=False,
    )
    payload_out = Path(args.payload_out)
    payload_out.parent.mkdir(parents=True, exist_ok=True)
    payload_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
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

    recovered_lock: dict[str, Any] | None = None
    if args.recover_stale_lock and (state_path.parent / RUNNER_LOCK_FILE).exists():
        recovered_lock = read_lock_file(state_path.parent / RUNNER_LOCK_FILE)
    with RunnerFileLock(
        state_path,
        command=args.command,
        stale_lock_seconds=args.stale_lock_seconds,
        recover_stale_lock=args.recover_stale_lock,
    ) as runner_lock:
        recovery_payload = recover_incomplete_stage_after_stale_lock(
            state_path,
            recovered_lock=recovered_lock,
            approval_mode=args.approval_mode,
            model=args.model,
            runner_lock=runner_lock,
        )
        if recovery_payload is not None:
            print(json.dumps(recovery_payload, ensure_ascii=False, indent=2))
            return 0
        if next_session_requires_sdk(next_session_for_state(load_simple_yaml(state_path))):
            ensure_openai_codex_runtime_available()
        payload = run_until_terminal(
            state_path,
            cwd=args.cwd,
            approval_mode=args.approval_mode,
            model=args.model,
            max_sessions=args.max_sessions,
            runner_lock=runner_lock,
            session_timeout_seconds=args.session_timeout_seconds,
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
    recovered_lock: dict[str, Any] | None = None
    if args.recover_stale_lock and (state_path.parent / RUNNER_LOCK_FILE).exists():
        recovered_lock = read_lock_file(state_path.parent / RUNNER_LOCK_FILE)
    if args.recover_only:
        diagnostics = lock_diagnostics(
            state_path,
            stale_lock_seconds=args.stale_lock_seconds,
        )
        if not diagnostics.get("exists"):
            raise RunnerError("recover-only requires an existing stale runner lock")
        with RunnerFileLock(
            state_path,
            command=args.command,
            stale_lock_seconds=args.stale_lock_seconds,
            recover_stale_lock=args.recover_stale_lock,
        ):
            pass
        payload = build_recover_only_payload(
            state_path,
            stale_lock_seconds=args.stale_lock_seconds,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    with RunnerFileLock(
        state_path,
        command=args.command,
        stale_lock_seconds=args.stale_lock_seconds,
        recover_stale_lock=args.recover_stale_lock,
    ) as runner_lock:
        recovery_payload = recover_incomplete_stage_after_stale_lock(
            state_path,
            recovered_lock=recovered_lock,
            approval_mode=args.approval_mode,
            model=args.model,
            runner_lock=runner_lock,
        )
        if recovery_payload is not None:
            print(json.dumps(recovery_payload, ensure_ascii=False, indent=2))
            return 0
        if next_session_requires_sdk(next_session_for_state(load_simple_yaml(state_path))):
            ensure_openai_codex_runtime_available()
        payload = run_until_terminal(
            state_path,
            cwd=args.cwd,
            approval_mode=args.approval_mode,
            model=args.model,
            max_sessions=args.max_sessions,
            runner_lock=runner_lock,
            session_timeout_seconds=args.session_timeout_seconds,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def prompt_for_sdk_diagnostic(
    state: dict[str, Any],
    state_path: Path,
    *,
    prompt_source: str,
    output_dir: Path,
) -> tuple[str, str, NextSession]:
    next_session = next_session_for_state(state) or diagnostic_session_for_current_stage(state)
    if prompt_source == "bounded-semantic":
        semantic_session = (
            next_session
            if next_session is not None
            and next_session.scenario == "reviewer.semantic_traceability_test_design"
            else semantic_session_from_active_prompt(state)
        )
        if semantic_session is None:
            raise RunnerError("bounded-semantic diagnostics require a semantic-review transition prompt")
        return (
            apply_sdk_diagnostic_safety_contract(
                render_bounded_semantic_review_prompt(
                    state,
                    state_path,
                    semantic_session,
                    cwd_base=Path.cwd(),
                ),
                output_dir,
            ),
            "bounded-semantic",
            semantic_session,
        )
    if next_session is None:
        raise RunnerError(f"No runnable next session for status {state['stage_status']}")
    if prompt_source == "minimal":
        return "Reply OK only", "minimal", next_session
    if prompt_source == "active":
        ft_root = infer_ft_root(state_path)
        prompt_path = resolve_artifact_path(next_session.prompt_path, ft_root)
        if prompt_path is None or not prompt_path.exists():
            raise RunnerError(f"Prompt file does not exist: {next_session.prompt_path}")
        return (
            apply_sdk_diagnostic_safety_contract(
                prompt_path.read_text(encoding="utf-8"),
                output_dir,
            ),
            str(prompt_path),
            next_session,
        )
    if prompt_source == "runner-composed":
        return (
            apply_sdk_diagnostic_safety_contract(
                prompt_text_for_session(state, state_path, next_session),
                output_dir,
            ),
            "runner-composed",
            next_session,
        )
    raise RunnerError(f"Unsupported prompt source: {prompt_source}")


def cmd_diagnose_sdk_turn(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    state = load_simple_yaml(state_path)
    validate_state(state, state_path, enforce_validator_gates=False)
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    import diagnose_codex_sdk_turn as sdk_diag

    output_dir = sdk_diag.ensure_output_dir(args.output_dir)
    prompt, prompt_source, next_session = prompt_for_sdk_diagnostic(
        state,
        state_path,
        prompt_source=args.prompt_source,
        output_dir=output_dir,
    )
    sandbox_policy = args.sandbox_policy or next_session.sandbox_policy
    diagnostic_kwargs = {
        "cwd": args.cwd or str(Path.cwd()),
        "prompt": prompt,
        "prompt_source": prompt_source,
        "sandbox_policy": sandbox_policy,
        "approval_mode": args.approval_mode,
        "model": args.model,
        "timeout_seconds": args.timeout_seconds,
        "output_dir": output_dir,
    }
    if args.dry_run:
        payload = sdk_diag.write_prompt_diagnostic(**diagnostic_kwargs)
        payload["action"] = "rendered-sdk-diagnostic-prompt"
    else:
        payload = sdk_diag.run_diagnostic(**diagnostic_kwargs)
        payload["action"] = "diagnosed-sdk-turn"
    payload["cycle_id"] = state.get("cycle_id") or ""
    payload["ft_slug"] = state.get("ft_slug") or ""
    payload["scope_slug"] = state.get("scope_slug") or ""
    payload["current_round"] = state.get("current_round") or 0
    payload["semantic_round"] = state.get("semantic_round") or 0
    payload["stage"] = next_session.stage
    payload["scenario"] = next_session.scenario
    payload["role"] = next_session.role
    payload["session_id"] = payload.get("thread_id") or ""
    response_path = output_dir / "response.md"
    if response_path.exists():
        response_text = response_path.read_text(encoding="utf-8", errors="replace")
        payload["final_response_summary"] = re.sub(r"\s+", " ", response_text).strip()[:500]
    sdk_diag.write_run_json(output_dir, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
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

    child = subparsers.add_parser("_run-session-child", help=argparse.SUPPRESS)
    child.add_argument("--state", required=True, help=argparse.SUPPRESS)
    child.add_argument("--payload-out", required=True, help=argparse.SUPPRESS)
    child.add_argument("--cwd", help=argparse.SUPPRESS)
    child.add_argument("--model", help=argparse.SUPPRESS)
    child.add_argument(
        "--approval-mode",
        choices=("auto_review", "deny_all"),
        default="auto_review",
        help=argparse.SUPPRESS,
    )
    child.set_defaults(func=cmd_run_session_child)

    doctor = subparsers.add_parser("doctor", help="Inspect runner state, lock and completion evidence")
    doctor.add_argument("--state", required=True, help="Path to cycle-state.yaml")
    doctor.add_argument(
        "--stale-lock-seconds",
        type=int,
        default=DEFAULT_STALE_LOCK_SECONDS,
        help=f"Seconds without heartbeat before a runner lock is considered stale. Default: {DEFAULT_STALE_LOCK_SECONDS}.",
    )
    doctor.set_defaults(func=cmd_doctor)

    diagnose = subparsers.add_parser(
        "diagnose-sdk-turn",
        help="Run a read-only standalone Codex SDK turn diagnostic for the next session",
    )
    diagnose.add_argument("--state", required=True, help="Path to cycle-state.yaml")
    diagnose.add_argument("--cwd", help="Working directory for the SDK thread")
    diagnose.add_argument("--model", help="Optional SDK model override")
    diagnose.add_argument(
        "--approval-mode",
        choices=("auto_review", "deny_all"),
        default="auto_review",
        help="Codex SDK approval mode. Default: auto_review.",
    )
    diagnose.add_argument(
        "--sandbox-policy",
        choices=("read_only", "workspace_write", "full_access"),
        help="Override SDK sandbox policy. Defaults to the next session policy.",
    )
    diagnose.add_argument(
        "--prompt-source",
        choices=("minimal", "active", "runner-composed", "bounded-semantic"),
        default="runner-composed",
        help="Prompt to diagnose. Default: runner-composed.",
    )
    diagnose.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
        help="Standalone diagnostic timeout. Default: 60.",
    )
    diagnose.add_argument("--output-dir", help="Diagnostic output directory")
    diagnose.add_argument(
        "--dry-run",
        action="store_true",
        help="Render prompt diagnostics only; do not start the SDK.",
    )
    diagnose.set_defaults(func=cmd_diagnose_sdk_turn)

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
        sub.add_argument(
            "--session-timeout-seconds",
            type=int,
            default=AUTO_SESSION_TIMEOUT_SENTINEL,
            help="Per-session SDK turn timeout. -1 uses stage defaults; 0 disables timeout recovery.",
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
    run_all.add_argument(
        "--session-timeout-seconds",
        type=int,
        default=AUTO_SESSION_TIMEOUT_SENTINEL,
        help="Per-session SDK turn timeout. -1 uses stage defaults; 0 disables timeout recovery.",
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
    resume.add_argument(
        "--recover-only",
        action="store_true",
        help="Archive a confirmed stale runner lock and stop without starting the next session.",
    )
    resume.add_argument(
        "--session-timeout-seconds",
        type=int,
        default=AUTO_SESSION_TIMEOUT_SENTINEL,
        help="Per-session SDK turn timeout. -1 uses stage defaults; 0 disables timeout recovery.",
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
