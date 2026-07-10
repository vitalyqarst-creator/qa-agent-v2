from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.contracts import (
    CONTRACT_VERSION,
    ExpectedOutput,
    StageInputManifest,
)
from test_case_agent.review_cycle.runtime import (
    BackendStageExecution,
    StageArtifactStore,
    StageAttemptPaths,
    StageRuntimeError,
    artifact_ref,
    resolve_repository_path,
)
from test_case_agent.review_cycle.prepared_package import (
    FAST_EXECUTION_PROFILE,
    PreparedStagePackage,
    load_prepared_package,
)
from test_case_agent.review_cycle.obligation_gate import validate_draft_obligation_coverage
from test_case_agent.review_cycle.attempts import format_attempt_id
from test_case_agent.review_cycle.orchestration import StageCompletionCoordinator


WRITER_STAGE = "writer-r1"
REVIEWER_STAGE = "reviewer-r1"
RUNNER_EVENTS = "runner-events.ndjson"
REVIEW_DECISIONS = {"accepted", "changes-required"}
ATTEMPT_ID = format_attempt_id(1)


class RunnerError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalized_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def format_yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if not text or text != text.strip() or any(char in text for char in ":#[]{}\n\r\t"):
        return json.dumps(text, ensure_ascii=False)
    return text


def write_simple_yaml(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {format_yaml_scalar(item)}" for item in value)
        else:
            lines.append(f"{key}: {format_yaml_scalar(value)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_event(cycle_dir: Path, event: str, **fields: Any) -> None:
    payload = {"timestamp": utc_now(), "event": event, **fields}
    cycle_dir.mkdir(parents=True, exist_ok=True)
    with (cycle_dir / RUNNER_EVENTS).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


@dataclass(frozen=True)
class ProcessRequest:
    stage: str
    role: str
    command: tuple[str, ...]
    cwd: Path
    prompt: str
    timeout_seconds: int
    idle_timeout_seconds: int
    command_budget: int
    stdout_path: Path | None = None
    stderr_path: Path | None = None


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    idle_timed_out: bool = False
    command_budget_exceeded: bool = False
    launch_error: bool = False
    duration_seconds: float = 0.0
    command_count: int = 0
    first_output_seconds: float | None = None
    termination_reason: str = "completed"


class ProcessExecutor(Protocol):
    def execute(self, request: ProcessRequest) -> ProcessResult:
        ...


class SubprocessExecutor:
    def execute(self, request: ProcessRequest) -> ProcessResult:
        started = time.monotonic()
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        output_queue: queue.Queue[tuple[str, str | None]] = queue.Queue()
        process: subprocess.Popen[str] | None = None
        termination_reason = "completed"
        command_count = 0
        first_output_seconds: float | None = None
        last_output_at = started
        try:
            process = subprocess.Popen(
                list(request.command),
                cwd=request.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=self._utf8_environment(),
                bufsize=1,
            )
            assert process.stdin is not None
            assert process.stdout is not None
            assert process.stderr is not None
            try:
                process.stdin.write(request.prompt)
                process.stdin.close()
            except BrokenPipeError:
                pass

            def read_stream(name: str, handle) -> None:
                try:
                    for line in iter(handle.readline, ""):
                        output_queue.put((name, line))
                finally:
                    output_queue.put((name, None))

            threads = [
                threading.Thread(target=read_stream, args=("stdout", process.stdout), daemon=True),
                threading.Thread(target=read_stream, args=("stderr", process.stderr), daemon=True),
            ]
            for thread in threads:
                thread.start()

            stdout_handle = self._stream_file(request.stdout_path)
            stderr_handle = self._stream_file(request.stderr_path)
            active_streams = 2
            try:
                while active_streams:
                    now = time.monotonic()
                    if process.poll() is None:
                        if now - started >= request.timeout_seconds:
                            termination_reason = "hard-timeout"
                            break
                        if now - last_output_at >= request.idle_timeout_seconds:
                            termination_reason = "idle-timeout"
                            break
                    try:
                        stream_name, line = output_queue.get(timeout=0.05)
                    except queue.Empty:
                        continue
                    if line is None:
                        active_streams -= 1
                        continue
                    now = time.monotonic()
                    last_output_at = now
                    if first_output_seconds is None:
                        first_output_seconds = now - started
                    target = stdout_lines if stream_name == "stdout" else stderr_lines
                    target.append(line)
                    stream_handle = stdout_handle if stream_name == "stdout" else stderr_handle
                    if stream_handle is not None:
                        stream_handle.write(line)
                        stream_handle.flush()
                    if stream_name == "stdout" and self._is_command_started(line):
                        command_count += 1
                        if command_count > request.command_budget:
                            termination_reason = "command-budget-exceeded"
                            break
            finally:
                if stdout_handle is not None:
                    stdout_handle.close()
                if stderr_handle is not None:
                    stderr_handle.close()

            if termination_reason != "completed" and process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            for thread in threads:
                thread.join(timeout=1)
            process.stdout.close()
            process.stderr.close()
            while not output_queue.empty():
                stream_name, line = output_queue.get_nowait()
                if line is not None:
                    (stdout_lines if stream_name == "stdout" else stderr_lines).append(line)
            return ProcessResult(
                exit_code=(process.returncode if termination_reason == "completed" else None),
                stdout="".join(stdout_lines),
                stderr="".join(stderr_lines),
                timed_out=termination_reason == "hard-timeout",
                idle_timed_out=termination_reason == "idle-timeout",
                command_budget_exceeded=termination_reason == "command-budget-exceeded",
                duration_seconds=time.monotonic() - started,
                command_count=command_count,
                first_output_seconds=first_output_seconds,
                termination_reason=termination_reason,
            )
        except OSError as exc:
            if process is not None and process.poll() is None:
                process.kill()
            return ProcessResult(
                exit_code=None,
                stderr=f"{type(exc).__name__}: {exc}",
                launch_error=True,
                duration_seconds=time.monotonic() - started,
                termination_reason="launch-error",
            )

    @staticmethod
    def _stream_file(path: Path | None):
        if path is None:
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("w", encoding="utf-8")

    @staticmethod
    def _is_command_started(line: str) -> bool:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return False
        return (
            payload.get("type") == "item.started"
            and isinstance(payload.get("item"), dict)
            and payload["item"].get("type") == "command_execution"
        )

    @staticmethod
    def _utf8_environment() -> dict[str, str]:
        environment = os.environ.copy()
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        return environment


@dataclass(frozen=True)
class ExecCommandConfig:
    executable: str
    sandbox_flag: str
    writer_sandbox: str
    reviewer_sandbox: str
    working_directory_flag: str
    json_flag: str | None = None
    output_last_message_flag: str | None = None
    output_schema_flag: str | None = None
    extra_args: tuple[str, ...] = ()
    cli_contract_verified: bool = False

    def validate(self) -> None:
        if not self.cli_contract_verified:
            raise RunnerError(
                "codex exec CLI contract is unverified; probe help output and pass an explicitly verified flag set"
            )
        required = {
            "executable": self.executable,
            "sandbox_flag": self.sandbox_flag,
            "writer_sandbox": self.writer_sandbox,
            "reviewer_sandbox": self.reviewer_sandbox,
            "working_directory_flag": self.working_directory_flag,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise RunnerError(f"Missing codex exec command configuration: {', '.join(missing)}")
        if self.writer_sandbox == self.reviewer_sandbox:
            raise RunnerError("Writer and reviewer sandbox values must be distinct")

    def build(
        self,
        *,
        role: str,
        cwd: Path,
        last_message_path: Path | None = None,
        output_schema_path: Path | None = None,
    ) -> tuple[str, ...]:
        sandbox = self.writer_sandbox if role == "writer" else self.reviewer_sandbox
        command = [
            self.executable,
            "exec",
            *self.extra_args,
            self.sandbox_flag,
            sandbox,
            self.working_directory_flag,
            str(cwd),
        ]
        if self.json_flag:
            command.append(self.json_flag)
        if self.output_last_message_flag and last_message_path is not None:
            command.extend((self.output_last_message_flag, str(last_message_path)))
        if self.output_schema_flag and output_schema_path is not None:
            command.extend((self.output_schema_flag, str(output_schema_path)))
        command.append("-")
        return tuple(command)


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    findings: tuple[dict[str, Any], ...] = ()
    checked_paths: tuple[str, ...] = ()
    validator: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "validator": self.validator,
            "checked_paths": list(self.checked_paths),
            "findings": list(self.findings),
        }


class DraftValidator(Protocol):
    def validate(
        self,
        *,
        draft_path: Path,
        final_path: Path,
        ft_root: Path,
        state_path: Path,
    ) -> ValidationResult:
        ...


class ProjectDraftStructureValidator:
    """Reuse the SDK runner's deterministic Markdown structure checks without starting the SDK."""

    def validate(
        self,
        *,
        draft_path: Path,
        final_path: Path,
        ft_root: Path,
        state_path: Path,
    ) -> ValidationResult:
        try:
            import codex_review_cycle_runner as existing_runner
        except ModuleNotFoundError:
            from scripts import codex_review_cycle_runner as existing_runner

        state = {
            "stage_status": "writer-draft-ready",
            "draft_test_cases": relative_path(draft_path, ft_root),
            "canonical_test_cases": relative_path(final_path, ft_root),
        }
        findings, checked_paths = existing_runner.evaluate_test_case_markdown_structure(state, state_path)
        return ValidationResult(
            passed=not findings,
            findings=tuple(findings),
            checked_paths=tuple(checked_paths),
            validator="codex_review_cycle_runner.evaluate_test_case_markdown_structure",
        )


@dataclass(frozen=True)
class ReviewContract:
    decision: str
    findings_markdown: str


@dataclass(frozen=True)
class CycleResult:
    status: str
    final_promoted: bool
    state_path: Path
    draft_path: Path
    final_path: Path
    blocking_reasons: tuple[str, ...] = ()


@dataclass
class CodexExecReviewCycleRunner:
    repo_root: Path
    ft_root: Path
    cycle_dir: Path
    final_path: Path
    source_files: Sequence[Path]
    handoff_files: Sequence[Path]
    command_config: ExecCommandConfig
    prepared_package_path: Path | None = None
    instruction_files: Sequence[Path] = ()
    executor: ProcessExecutor = field(default_factory=SubprocessExecutor)
    validator: DraftValidator = field(default_factory=ProjectDraftStructureValidator)
    timeout_seconds: int = 1800
    writer_timeout_seconds: int | None = None
    reviewer_timeout_seconds: int | None = None
    writer_idle_timeout_seconds: int = 60
    reviewer_idle_timeout_seconds: int = 45
    writer_command_budget: int = 12
    reviewer_command_budget: int = 8
    promote_final: bool = False
    allow_overwrite_final: bool = False
    _manifests: dict[str, StageInputManifest] = field(default_factory=dict, init=False)
    _backend_session_ids: list[str] = field(default_factory=list, init=False)
    _prepared_package: PreparedStagePackage | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.repo_root = self.repo_root.resolve()
        self.ft_root = self.ft_root.resolve()
        self.cycle_dir = self.cycle_dir.resolve()
        self.final_path = self.final_path.resolve()
        self.source_files = tuple(path.resolve() for path in self.source_files)
        self.handoff_files = tuple(path.resolve() for path in self.handoff_files)
        if self.prepared_package_path is not None:
            self.prepared_package_path = self.prepared_package_path.resolve()
        configured_instructions = tuple(path.resolve() for path in self.instruction_files)
        self.instruction_files = configured_instructions or ((self.repo_root / "AGENTS.md").resolve(),)

    @property
    def attempts_dir(self) -> Path:
        return self.cycle_dir / "attempts"

    def attempt_root(self, stage: str) -> Path:
        return self.attempts_dir / stage / ATTEMPT_ID

    def stage_output_dir(self, stage: str) -> Path:
        return self.attempt_root(stage) / "stage-output"

    def runner_output_dir(self, stage: str) -> Path:
        return self.attempt_root(stage) / "runner-output"

    def prompt_path(self, stage: str) -> Path:
        return self.attempt_root(stage) / "prompt.md"

    def stage_status_path(self, stage: str) -> Path:
        return self.runner_output_dir(stage) / "stage-status.json"

    @property
    def state_path(self) -> Path:
        return self.cycle_dir / "cycle-state.yaml"

    @property
    def draft_path(self) -> Path:
        return self.stage_output_dir(WRITER_STAGE) / "draft.md"

    @property
    def validator_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "validator.json"

    @property
    def obligation_gate_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "obligation-gate.json"

    @property
    def reviewer_findings_path(self) -> Path:
        return self.runner_output_dir(REVIEWER_STAGE) / "findings.md"

    @property
    def reviewer_schema_path(self) -> Path:
        return self.attempt_root(REVIEWER_STAGE) / "review-contract.schema.json"

    def _runner_owned_paths(self) -> tuple[Path, ...]:
        paths = [
            self.state_path,
            self.cycle_dir / RUNNER_EVENTS,
            self.attempt_root(WRITER_STAGE),
            self.attempt_root(REVIEWER_STAGE),
            self.cycle_dir / "outputs",
            self.cycle_dir / "stage-inputs",
        ]
        return tuple(paths)

    def validate_configuration(self) -> None:
        self.command_config.validate()
        if self.timeout_seconds < 1:
            raise RunnerError("timeout_seconds must be >= 1")
        for name in (
            "writer_idle_timeout_seconds",
            "reviewer_idle_timeout_seconds",
            "writer_command_budget",
            "reviewer_command_budget",
        ):
            if getattr(self, name) < 1:
                raise RunnerError(f"{name} must be >= 1")
        for name in ("writer_timeout_seconds", "reviewer_timeout_seconds"):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise RunnerError(f"{name} must be >= 1 when set")
        if not self.ft_root.is_dir():
            raise RunnerError(f"FT root does not exist: {self.ft_root}")
        expected_work_root = self.ft_root / "work"
        if not is_relative_to(self.cycle_dir, expected_work_root):
            raise RunnerError(f"Cycle directory must be under {expected_work_root}")
        production_dir = (self.ft_root / "test-cases").resolve()
        if self.final_path.parent != production_dir or self.final_path.suffix.lower() != ".md":
            raise RunnerError(f"Final artifact must be a Markdown file directly under {production_dir}")
        if self.final_path.name.lower() == "readme.md":
            raise RunnerError("README.md cannot be used as the promoted final artifact")
        if self.prepared_package_path is not None:
            if not self.command_config.output_schema_flag:
                raise RunnerError(
                    "Prepared reviewer fast path requires a verified output-schema flag"
                )
            if self.source_files or self.handoff_files:
                raise RunnerError(
                    "Prepared fast path must not mix full source/handoff lists into the stage context"
                )
            if not is_relative_to(self.prepared_package_path, self.ft_root):
                raise RunnerError("Prepared stage package must be under the FT package")
            try:
                self._prepared_package = load_prepared_package(
                    self.prepared_package_path, self.repo_root
                )
            except StageRuntimeError as exc:
                raise RunnerError(f"Prepared stage package is invalid: {exc}") from exc
            if self._prepared_package.ft_slug != self.ft_root.name:
                raise RunnerError("Prepared stage package ft_slug does not match FT root")
            if (
                self._prepared_package.execution_profile != FAST_EXECUTION_PROFILE
                or self._prepared_package.unsupported_dimensions
            ):
                dimensions = ", ".join(self._prepared_package.unsupported_dimensions) or "none"
                raise RunnerError(
                    "Prepared fast path is ineligible; route to standard writer: "
                    f"profile={self._prepared_package.execution_profile}, "
                    f"unsupported_dimensions={dimensions}"
                )
        else:
            if not self.source_files:
                raise RunnerError("At least one explicit source file is required")
            if not self.handoff_files:
                raise RunnerError("At least one explicit handoff file is required")
        prepared_inputs = self._prepared_input_paths()
        for input_path in (
            *self.instruction_files,
            *self.source_files,
            *self.handoff_files,
            *prepared_inputs,
        ):
            if not input_path.is_file():
                raise RunnerError(f"Stage input does not exist: {input_path}")
            if not is_relative_to(input_path, self.repo_root):
                raise RunnerError(f"Stage input must be under the repository root: {input_path}")
        for input_path in (*self.source_files, *self.handoff_files):
            if not is_relative_to(input_path, self.ft_root):
                raise RunnerError(f"Source/handoff input must be under the FT package: {input_path}")
        existing_runner_artifacts = [path for path in self._runner_owned_paths() if path.exists()]
        if existing_runner_artifacts:
            joined = ", ".join(relative_path(path, self.repo_root) for path in existing_runner_artifacts)
            raise RunnerError(
                "Cycle directory contains runner-owned artifacts from an earlier attempt; "
                "use a new cycle directory or an explicit recovery path instead of reusing stale outputs: "
                + joined
            )

    def _prepared_input_paths(self) -> tuple[Path, ...]:
        if self._prepared_package is None or self.prepared_package_path is None:
            return ()
        artifacts = tuple(
            resolve_repository_path(item.path, self.repo_root)
            for item in self._prepared_package.package_artifacts
        )
        return (self.prepared_package_path, *artifacts)

    def _prepared_artifact(self, kind: str) -> Path:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        reference = next(
            (item for item in self._prepared_package.package_artifacts if item.kind == kind),
            None,
        )
        if reference is None:
            raise RunnerError(f"Prepared package does not contain {kind}")
        return resolve_repository_path(reference.path, self.repo_root)

    @property
    def prepared_writer_profile_path(self) -> Path:
        return self.repo_root / "references" / "agent" / "prepared-writer-runtime-profile.md"

    def _prepared_writer_payload(self) -> str:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        if not self.prepared_writer_profile_path.is_file():
            raise RunnerError("Prepared writer runtime profile is missing")
        metadata = {
            "package_version": self._prepared_package.package_version,
            "package_id": self._prepared_package.package_id,
            "ft_slug": self._prepared_package.ft_slug,
            "scope_slug": self._prepared_package.scope_slug,
            "section_id": self._prepared_package.section_id,
            "execution_profile": self._prepared_package.execution_profile,
            "unsupported_dimensions": list(self._prepared_package.unsupported_dimensions),
            "fallback_policy": self._prepared_package.fallback_policy,
        }
        return "\n".join(
            [
                "<!-- PREPARED-STAGE-PAYLOAD:BEGIN -->",
                "## Verified package metadata",
                "",
                "```json",
                json.dumps(metadata, ensure_ascii=False, indent=2),
                "```",
                "",
                self.prepared_writer_profile_path.read_text(encoding="utf-8").strip(),
                "",
                self._prepared_artifact("stage-instructions").read_text(encoding="utf-8").strip(),
                "",
                self._prepared_artifact("source-evidence").read_text(encoding="utf-8").strip(),
                "",
                "## Atomic obligations",
                "",
                "```json",
                self._prepared_artifact("atomic-obligations").read_text(encoding="utf-8").strip(),
                "```",
                "<!-- PREPARED-STAGE-PAYLOAD:END -->",
            ]
        )

    def _verify_prepared_package(self) -> None:
        if self.prepared_package_path is None:
            return
        try:
            self._prepared_package = load_prepared_package(
                self.prepared_package_path, self.repo_root
            )
        except StageRuntimeError as exc:
            raise RunnerError(f"Prepared stage package changed or became invalid: {exc}") from exc

    def _stage_limits(self, role: str) -> tuple[int, int, int]:
        if role == "writer":
            timeout = self.writer_timeout_seconds or self.timeout_seconds
            idle_timeout = self.writer_idle_timeout_seconds
            command_budget = self.writer_command_budget
        else:
            timeout = self.reviewer_timeout_seconds or self.timeout_seconds
            idle_timeout = self.reviewer_idle_timeout_seconds
            command_budget = self.reviewer_command_budget
        return timeout, min(idle_timeout, timeout), command_budget

    def run(self) -> CycleResult:
        self.validate_configuration()
        production_before = self._production_snapshot()
        writer_prompt = self._writer_prompt()
        state = self._initial_state()
        self._write_state(state)
        append_event(self.cycle_dir, "cycle_started", backend="codex-exec")

        writer_result, writer_artifacts = self._run_stage(
            stage=WRITER_STAGE,
            role="writer",
            prompt=writer_prompt,
            last_message_path=self.stage_output_dir(WRITER_STAGE) / "last-message.txt",
        )
        production_changes = self._production_changes(production_before)
        if production_changes:
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status="blocked-forbidden-production-change",
                reasons=["writer modified production test-cases", *production_changes],
            )

        if writer_result.launch_error:
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status="blocked-process-launch",
                reasons=["writer process could not be started"],
            )
        if writer_result.exit_code not in (None, 0):
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status="blocked-process-exit",
                reasons=[f"writer process exited with code {writer_result.exit_code}"],
            )
        if not self.draft_path.is_file():
            if writer_result.command_budget_exceeded:
                status = "blocked-command-budget"
                reason = "writer exceeded the command budget and the required draft is missing"
            elif writer_result.idle_timed_out:
                status = "blocked-idle-timeout"
                reason = "writer produced no events within the idle budget and the required draft is missing"
            elif writer_result.timed_out:
                status = "blocked-timeout"
                reason = "writer timed out and the required draft is missing"
            else:
                status = "blocked-missing-output"
                reason = "writer exited without the required draft"
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status=status,
                reasons=[reason, relative_path(self.draft_path, self.repo_root)],
            )

        validation = self.validator.validate(
            draft_path=self.draft_path,
            final_path=self.final_path,
            ft_root=self.ft_root,
            state_path=self.state_path,
        )
        write_json(self.validator_path, validation.as_dict())
        if not validation.passed:
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status="blocked-validator",
                reasons=["deterministic writer validator reported findings"],
                validation=validation,
            )

        if self._prepared_package is not None:
            obligation_gate = validate_draft_obligation_coverage(
                draft_path=self.draft_path,
                obligations_path=self._prepared_artifact("atomic-obligations"),
            )
            write_json(self.obligation_gate_path, obligation_gate.as_dict())
            if not obligation_gate.passed:
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-obligation-gate",
                    reasons=[
                        "prepared atomic obligation gate reported findings",
                        relative_path(self.obligation_gate_path, self.repo_root),
                    ],
                    validation=validation,
                )

        writer_session_issue = self._backend_session_issue(writer_artifacts)
        if writer_session_issue:
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status="blocked-contract",
                reasons=[writer_session_issue],
                validation=validation,
            )

        draft_sha256 = sha256_file(self.draft_path)
        writer_interrupted = (
            writer_result.timed_out
            or writer_result.idle_timed_out
            or writer_result.command_budget_exceeded
        )
        writer_status = "completed-with-progress" if writer_interrupted else "completed"
        self._write_stage_status(
            stage=WRITER_STAGE,
            role="writer",
            status=writer_status,
            result=writer_result,
            artifacts=writer_artifacts,
            reason=(
                "process was stopped by a runtime budget, but the required draft exists and deterministic validation passed"
                if writer_interrupted
                else "required draft exists and deterministic validation passed"
            ),
            validation=validation,
            draft_sha256=draft_sha256,
        )
        self._write_contract_result(
            stage=WRITER_STAGE,
            role="writer",
            outcome="draft-ready",
            result=writer_result,
            artifacts=writer_artifacts,
        )
        reviewer_prompt = self._reviewer_prompt()
        state.update(
            {
                "workflow_status": "reviewer-ready",
                "stage_status": "writer-draft-ready",
                "current_stage": REVIEWER_STAGE,
                "writer_stage_status": writer_status,
                "writer_draft_sha256": draft_sha256,
                "validator_report": relative_path(self.validator_path, self.ft_root),
                "obligation_gate_report": (
                    relative_path(self.obligation_gate_path, self.ft_root)
                    if self._prepared_package is not None
                    else ""
                ),
                "active_transition_prompt": relative_path(
                    self.prompt_path(REVIEWER_STAGE), self.ft_root
                ),
            }
        )
        self._write_state(state)
        append_event(self.cycle_dir, "writer_stage_completed", stage_status=writer_status)

        reviewer_result, reviewer_artifacts = self._run_stage(
            stage=REVIEWER_STAGE,
            role="reviewer",
            prompt=reviewer_prompt,
            last_message_path=None,
        )
        production_changes = self._production_changes(production_before)
        if production_changes:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-forbidden-production-change",
                reasons=["reviewer modified production test-cases", *production_changes],
            )
        if not self.draft_path.is_file():
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-forbidden-input-change",
                reasons=["writer draft disappeared during the read-only reviewer stage"],
            )
        reviewer_observed_draft_sha256 = sha256_file(self.draft_path)
        if reviewer_observed_draft_sha256 != draft_sha256:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-forbidden-input-change",
                reasons=[
                    "writer draft changed during the read-only reviewer stage",
                    f"expected sha256={draft_sha256}",
                    f"actual sha256={reviewer_observed_draft_sha256}",
                ],
            )
        if reviewer_result.launch_error:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-process-launch",
                reasons=["reviewer process could not be started"],
            )
        if reviewer_result.timed_out or reviewer_result.idle_timed_out:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-timeout",
                reasons=["reviewer timed out or became idle; a partial review is not accepted as terminal sign-off"],
            )
        if reviewer_result.command_budget_exceeded:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-command-budget",
                reasons=["reviewer exceeded the command budget; partial review is not accepted"],
            )
        if reviewer_result.exit_code != 0:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-process-exit",
                reasons=[f"reviewer process exited with code {reviewer_result.exit_code}"],
            )

        reviewer_message = self._reviewer_message(reviewer_result.stdout)
        if not reviewer_message.strip():
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-missing-output",
                reasons=["reviewer completed without a final review contract in stdout/events"],
            )
        try:
            review = parse_review_contract(reviewer_message)
        except RunnerError as exc:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-invalid-output",
                reasons=[str(exc)],
            )

        reviewer_session_issue = self._backend_session_issue(reviewer_artifacts)
        if reviewer_session_issue:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-contract",
                reasons=[reviewer_session_issue],
            )

        self.reviewer_findings_path.write_text(review.findings_markdown.rstrip() + "\n", encoding="utf-8")
        if review.decision == "changes-required":
            self._write_stage_status(
                stage=REVIEWER_STAGE,
                role="reviewer",
                status="changes-required",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                reason="reviewer returned actionable findings; no automatic writer retry is started",
            )
            self._write_contract_result(
                stage=REVIEWER_STAGE,
                role="reviewer",
                outcome="changes-required",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
            )
            state.update(
                {
                    "workflow_status": "changes-required",
                    "stage_status": "semantic-revision-needed",
                    "current_stage": REVIEWER_STAGE,
                    "reviewer_stage_status": "changes-required",
                    "reviewer_findings": relative_path(self.reviewer_findings_path, self.ft_root),
                    "blocking_reasons": ["reviewer returned changes-required"],
                }
            )
            self._write_state(state)
            append_event(self.cycle_dir, "cycle_stopped_for_review_findings")
            return self._result(state)

        self._write_stage_status(
            stage=REVIEWER_STAGE,
            role="reviewer",
            status="accepted",
            result=reviewer_result,
            artifacts=reviewer_artifacts,
            reason="reviewer returned a valid accepted terminal contract",
        )
        self._write_contract_result(
            stage=REVIEWER_STAGE,
            role="reviewer",
            outcome="accepted",
            result=reviewer_result,
            artifacts=reviewer_artifacts,
        )
        state.update(
            {
                "workflow_status": "accepted-awaiting-promotion",
                "stage_status": "accepted-awaiting-promotion",
                "current_stage": REVIEWER_STAGE,
                "reviewer_stage_status": "accepted",
                "reviewer_findings": relative_path(self.reviewer_findings_path, self.ft_root),
                "accepted_terminal_state": True,
                "blocking_reasons": [],
            }
        )
        self._write_state(state)
        append_event(self.cycle_dir, "reviewer_terminal_state_accepted")

        if not self.promote_final:
            state["workflow_status"] = "accepted-not-promoted"
            state["stage_status"] = "accepted-not-promoted"
            state["blocking_reasons"] = [
                "promotion is disabled; use a new cycle with explicit promotion enabled after reviewing this result"
            ]
            self._write_state(state)
            append_event(self.cycle_dir, "promotion_skipped")
            return self._result(state)

        try:
            self._promote(production_before, expected_draft_sha256=draft_sha256)
        except RunnerError as exc:
            state["workflow_status"] = "blocked-promotion"
            state["stage_status"] = "blocked-input"
            state["blocking_reasons"] = [str(exc)]
            self._write_state(state)
            append_event(self.cycle_dir, "promotion_blocked", reason=str(exc))
            return self._result(state)

        state.update(
            {
                "workflow_status": "signed-off",
                "stage_status": "signed-off",
                "final_promoted": True,
                "promotion_status": "completed",
                "draft_or_unsigned": False,
                "final_sha256": draft_sha256,
                "blocking_reasons": [],
            }
        )
        self._write_state(state)
        append_event(
            self.cycle_dir,
            "final_artifact_promoted",
            final_artifact=relative_path(self.final_path, self.ft_root),
        )
        return self._result(state)

    def _initial_state(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_dir.name,
            "ft_slug": self.ft_root.name,
            "scope_slug": self.cycle_dir.name,
            "backend": "codex-exec",
            "workflow_status": "writer-ready",
            "stage_status": "scope-ready-for-writer",
            "current_stage": WRITER_STAGE,
            "semantic_round": 0,
            "max_semantic_rounds": 2,
            "writer_stage_status": "pending",
            "reviewer_stage_status": "pending",
            "draft_test_cases": relative_path(self.draft_path, self.ft_root),
            "canonical_test_cases": relative_path(self.final_path, self.ft_root),
            "validator_report": "",
            "obligation_gate_report": "",
            "writer_draft_sha256": "",
            "reviewer_findings": "",
            "accepted_terminal_state": False,
            "final_promoted": False,
            "draft_or_unsigned": True,
            "promotion_status": "pending",
            "active_transition_prompt": relative_path(
                self.prompt_path(WRITER_STAGE), self.ft_root
            ),
            "blocking_reasons": [],
        }

    def _write_state(self, state: dict[str, Any]) -> None:
        write_simple_yaml(self.state_path, state)

    def _result(self, state: dict[str, Any]) -> CycleResult:
        reasons = tuple(str(item) for item in state.get("blocking_reasons", []))
        return CycleResult(
            status=str(state["workflow_status"]),
            final_promoted=bool(state.get("final_promoted")),
            state_path=self.state_path,
            draft_path=self.draft_path,
            final_path=self.final_path,
            blocking_reasons=reasons,
        )

    def _writer_prompt(self) -> str:
        if self._prepared_package is not None and self.prepared_package_path is not None:
            return "\n".join(
                [
                    "# Codex exec prepared writer fast path",
                    "",
                    "The upstream package already applied the full source, scope and writer policy.",
                    "Use only the embedded Prepared Writer Runtime Profile below; do not load the full ft-test-case-writer skill or reread package/project reference files.",
                    "Do not read existing/generated test cases or earlier cycle artifacts as evidence.",
                    f"Write a structurally complete unsigned draft first and only to `{relative_path(self.draft_path, self.repo_root)}`.",
                    "Do not write under a production test-cases directory and do not promote the draft.",
                    "Use registered full sources only for a single unresolved ATOM locator and record targeted_source_fallback.",
                    "",
                    self._prepared_writer_payload(),
                    "",
                    "Exit only after the draft file is fully written. A chat response without the file is a failed stage.",
                    "",
                ]
            )
        return "\n".join(
            [
                "# Codex exec writer stage contract",
                "",
                "Work only from the explicit source and handoff files below.",
                "Do not use previously generated test cases as requirement evidence.",
                "Do not write under any production test-cases directory.",
                f"Write the complete unsigned draft only to `{relative_path(self.draft_path, self.repo_root)}`.",
                "Do not promote or rename the draft to a final artifact.",
                "",
                "## Source files",
                *[f"- `{relative_path(path, self.repo_root)}`" for path in self.source_files],
                "",
                "## Handoff files",
                *[f"- `{relative_path(path, self.repo_root)}`" for path in self.handoff_files],
                "",
                "Exit only after the draft file is fully written. A chat response without the file is a failed stage.",
                "",
            ]
        )

    def _reviewer_prompt(self) -> str:
        if self._prepared_package is not None and self.prepared_package_path is not None:
            package_files = self._prepared_input_paths()
            return "\n".join(
                [
                    "# Codex exec prepared reviewer fast path",
                    "",
                    "This stage is read-only. Do not modify any workspace file.",
                    "Review only the verified package, draft and deterministic validator report listed below.",
                    *[f"- `{relative_path(path, self.repo_root)}`" for path in package_files],
                    f"- writer draft: `{relative_path(self.draft_path, self.repo_root)}`",
                    f"- validator: `{relative_path(self.validator_path, self.repo_root)}`",
                    f"- obligation gate: `{relative_path(self.obligation_gate_path, self.repo_root)}`",
                    f"- response schema: `{relative_path(self.reviewer_schema_path, self.repo_root)}`",
                    "",
                    "Return one JSON object in the final message and write no files:",
                    '{"decision":"accepted|changes-required","findings_markdown":"# Review findings\\n..."}',
                    "Use `accepted` only when every testable ATOM is correctly covered and no blocking finding remains.",
                    "",
                ]
            )
        return "\n".join(
            [
                "# Codex exec reviewer stage contract",
                "",
                "This stage is read-only. Do not modify any workspace file.",
                "Review only the explicit inputs listed below.",
                f"Writer draft: `{relative_path(self.draft_path, self.repo_root)}`",
                f"Deterministic validator report: `{relative_path(self.validator_path, self.repo_root)}`",
                "",
                "## Source files",
                *[f"- `{relative_path(path, self.repo_root)}`" for path in self.source_files],
                "",
                "## Handoff files",
                *[f"- `{relative_path(path, self.repo_root)}`" for path in self.handoff_files],
                "",
                "Return one JSON object in the final message and write no files:",
                '{"decision":"accepted|changes-required","findings_markdown":"# Review findings\\n..."}',
                "Use `accepted` only when no blocking finding remains.",
                "",
            ]
        )

    def _run_stage(
        self,
        *,
        stage: str,
        role: str,
        prompt: str,
        last_message_path: Path | None,
    ) -> tuple[ProcessResult, dict[str, Any]]:
        self._verify_prepared_package()
        attempt_root = self.attempt_root(stage)
        if attempt_root.exists():
            raise RunnerError(
                f"attempt root already exists; recovery must be explicit: {relative_path(attempt_root, self.repo_root)}"
            )
        attempt_root.mkdir(parents=True)
        prompt_path = self.prompt_path(stage)
        prompt_path.write_text(prompt, encoding="utf-8")
        self.runner_output_dir(stage).mkdir(parents=True)
        if role == "writer":
            self.stage_output_dir(stage).mkdir(parents=True)
        else:
            write_json(self.reviewer_schema_path, self._review_contract_schema())
        manifest = self._build_stage_manifest(stage=stage, role=role, prompt_path=prompt_path)
        store = StageArtifactStore(self.repo_root)
        try:
            store.write_manifest(StageAttemptPaths.from_manifest(self.repo_root, manifest), manifest)
        except StageRuntimeError as exc:
            raise RunnerError(f"cannot persist v2 stage manifest: {exc}") from exc
        self._manifests[stage] = manifest

        stdout_path = self.runner_output_dir(stage) / "stdout.txt"
        stderr_path = self.runner_output_dir(stage) / "stderr.txt"
        events_path = self.runner_output_dir(stage) / "events.ndjson"
        command = self.command_config.build(
            role=role,
            cwd=self.repo_root,
            last_message_path=last_message_path,
            output_schema_path=(self.reviewer_schema_path if role == "reviewer" else None),
        )
        timeout_seconds, idle_timeout_seconds, command_budget = self._stage_limits(role)
        request = ProcessRequest(
            stage=stage,
            role=role,
            command=command,
            cwd=self.repo_root,
            prompt=prompt,
            timeout_seconds=timeout_seconds,
            idle_timeout_seconds=idle_timeout_seconds,
            command_budget=command_budget,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        append_event(
            self.cycle_dir,
            "stage_process_started",
            stage=stage,
            role=role,
            command=list(command),
            contract_version=CONTRACT_VERSION,
            attempt_id=ATTEMPT_ID,
            manifest=relative_path(attempt_root / "stage-input.json", self.repo_root),
            timeout_seconds=timeout_seconds,
            idle_timeout_seconds=idle_timeout_seconds,
            command_budget=command_budget,
        )
        started_at = utc_now()
        result = self.executor.execute(request)
        finished_at = utc_now()
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        events_path.write_text(result.stdout if self.command_config.json_flag else "", encoding="utf-8")
        backend_session_id = backend_session_id_from_events(result.stdout)
        execution = BackendStageExecution(
            backend="codex-exec",
            backend_session_id=backend_session_id,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=max(0, round(result.duration_seconds * 1000)),
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            events=result.stdout if self.command_config.json_flag else "",
            timed_out=result.timed_out or result.idle_timed_out,
            launch_error=result.launch_error,
            usage=usage_from_events(result.stdout),
        )
        execution.validate()
        artifacts = {
            "command": list(command),
            "stdout": relative_path(stdout_path, self.repo_root),
            "stderr": relative_path(stderr_path, self.repo_root),
            "events": relative_path(events_path, self.repo_root) if self.command_config.json_flag else "",
            "last_message": (
                relative_path(last_message_path, self.repo_root) if last_message_path is not None else ""
            ),
            "_execution": execution,
        }
        append_event(
            self.cycle_dir,
            "stage_process_finished",
            stage=stage,
            role=role,
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            idle_timed_out=result.idle_timed_out,
            command_budget_exceeded=result.command_budget_exceeded,
            command_count=result.command_count,
            first_output_seconds=result.first_output_seconds,
            termination_reason=result.termination_reason,
            launch_error=result.launch_error,
            stdout=artifacts["stdout"],
            stderr=artifacts["stderr"],
            events=artifacts["events"],
            backend_session_id=backend_session_id,
        )
        return result, artifacts

    def _build_stage_manifest(
        self,
        *,
        stage: str,
        role: str,
        prompt_path: Path,
    ) -> StageInputManifest:
        attempt_root = self.attempt_root(stage)
        runner_output = self.runner_output_dir(stage)
        timeout_seconds, _, _ = self._stage_limits(role)
        expected_outputs = [
            ExpectedOutput(
                path=relative_path(runner_output / "stdout.txt", self.repo_root),
                kind="stdout",
                producer="runner",
            ),
            ExpectedOutput(
                path=relative_path(runner_output / "stderr.txt", self.repo_root),
                kind="stderr",
                producer="runner",
            ),
            ExpectedOutput(
                path=relative_path(runner_output / "events.ndjson", self.repo_root),
                kind="events",
                producer="runner",
            ),
            ExpectedOutput(
                path=relative_path(runner_output / "stage-status.json", self.repo_root),
                kind="stage-status",
                producer="runner",
            ),
        ]
        if self._prepared_package is not None and self.prepared_package_path is not None:
            instruction_paths = [*self.instruction_files, self._prepared_artifact("stage-instructions")]
            if role == "writer":
                instruction_paths.append(self.prepared_writer_profile_path)
            source_paths = [self._prepared_artifact("source-evidence")]
            handoff_paths = [
                self.prepared_package_path,
                self._prepared_artifact("atomic-obligations"),
            ]
        else:
            instruction_paths = list(self.instruction_files)
            source_paths = list(self.source_files)
            handoff_paths = list(self.handoff_files)
        allowed_write_roots: list[str] = []
        if role == "writer":
            expected_outputs.extend(
                [
                    ExpectedOutput(
                        path=relative_path(self.draft_path, self.repo_root),
                        kind="test-case-draft",
                        producer="stage",
                    ),
                    ExpectedOutput(
                        path=relative_path(self.validator_path, self.repo_root),
                        kind="validator-report",
                        producer="runner",
                    ),
                    ExpectedOutput(
                        path=relative_path(self.obligation_gate_path, self.repo_root),
                        kind="obligation-gate",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(
                            self.stage_output_dir(stage) / "last-message.txt", self.repo_root
                        ),
                        kind="last-message",
                        producer="stage",
                        required=False,
                    ),
                ]
            )
            allowed_write_roots.append(relative_path(self.stage_output_dir(stage), self.repo_root))
        else:
            handoff_paths.extend((self.draft_path, self.validator_path))
            if self._prepared_package is not None:
                handoff_paths.append(self.obligation_gate_path)
            handoff_paths.append(self.reviewer_schema_path)
            expected_outputs.append(
                ExpectedOutput(
                    path=relative_path(self.reviewer_findings_path, self.repo_root),
                    kind="review-findings",
                    producer="runner",
                )
            )
        return StageInputManifest.create(
            cycle_id=self.cycle_dir.name,
            stage_id=stage,
            attempt_id=ATTEMPT_ID,
            session_id=f"session-{stage}-{ATTEMPT_ID}",
            role=role,
            scenario=(
                (
                    "writer.session_prepared_initial_draft"
                    if self._prepared_package is not None
                    else "writer.session_initial_draft"
                )
                if role == "writer"
                else (
                    "reviewer.session_prepared_semantic"
                    if self._prepared_package is not None
                    else "reviewer.semantic_traceability_test_design"
                )
            ),
            semantic_round=0,
            sandbox_policy="workspace_write" if role == "writer" else "read_only",
            timeout_seconds=timeout_seconds,
            attempt_root=relative_path(attempt_root, self.repo_root),
            canonical_test_cases=relative_path(self.final_path, self.repo_root),
            prompt_artifact=artifact_ref(prompt_path, self.repo_root, kind="prompt"),
            instruction_artifacts=[
                artifact_ref(path, self.repo_root, kind="instruction")
                for path in instruction_paths
            ],
            source_artifacts=[
                artifact_ref(path, self.repo_root, kind="source") for path in source_paths
            ],
            handoff_artifacts=[
                artifact_ref(path, self.repo_root, kind="handoff") for path in handoff_paths
            ],
            expected_outputs=expected_outputs,
            allowed_write_roots=allowed_write_roots,
            forbidden_write_roots=[relative_path(self.ft_root / "test-cases", self.repo_root)],
        )

    @staticmethod
    def _review_contract_schema() -> dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["decision", "findings_markdown"],
            "properties": {
                "decision": {"type": "string", "enum": sorted(REVIEW_DECISIONS)},
                "findings_markdown": {"type": "string", "minLength": 1},
            },
        }

    def _write_stage_status(
        self,
        *,
        stage: str,
        role: str,
        status: str,
        result: ProcessResult,
        artifacts: dict[str, Any],
        reason: str,
        validation: ValidationResult | None = None,
        blocking_reasons: Sequence[str] = (),
        draft_sha256: str = "",
    ) -> Path:
        status_path = self.stage_status_path(stage)
        payload: dict[str, Any] = {
            "stage": stage,
            "role": role,
            "status": status,
            "reason": reason,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "idle_timed_out": result.idle_timed_out,
            "command_budget_exceeded": result.command_budget_exceeded,
            "launch_error": result.launch_error,
            "duration_seconds": round(result.duration_seconds, 3),
            "command_count": result.command_count,
            "first_output_seconds": result.first_output_seconds,
            "termination_reason": result.termination_reason,
            "command": artifacts["command"],
            "stdout": artifacts["stdout"],
            "stderr": artifacts["stderr"],
            "events": artifacts["events"],
            "last_message": artifacts["last_message"],
            "blocking_reasons": list(blocking_reasons),
        }
        if validation is not None:
            payload["validator_report"] = relative_path(self.validator_path, self.repo_root)
            payload["validator_passed"] = validation.passed
        if draft_sha256:
            payload["draft_sha256"] = draft_sha256
        write_json(status_path, payload)
        return status_path

    def _write_contract_result(
        self,
        *,
        stage: str,
        role: str,
        outcome: str,
        result: ProcessResult,
        artifacts: dict[str, Any],
        blocking_reasons: Sequence[str] = (),
    ) -> Path:
        manifest = self._manifests[stage]
        execution = artifacts.get("_execution")
        if not isinstance(execution, BackendStageExecution):
            raise RunnerError(f"missing backend execution evidence for {stage}")
        try:
            completed = StageCompletionCoordinator(self.repo_root, self.cycle_dir).complete(
                manifest,
                execution,
                outcome=outcome,
                blocking_reasons=blocking_reasons,
                prior_backend_session_ids=self._backend_session_ids,
            )
            result_path = completed.result_path
        except (StageRuntimeError, ValueError) as exc:
            raise RunnerError(f"invalid v2 stage result for {stage}: {exc}") from exc
        if outcome != "blocked" and execution.backend_session_id:
            self._backend_session_ids.append(execution.backend_session_id)
        return result_path

    def _backend_session_issue(self, artifacts: dict[str, Any]) -> str:
        execution = artifacts.get("_execution")
        if not isinstance(execution, BackendStageExecution):
            return "stage has no backend execution evidence"
        if not execution.backend_session_id:
            return "codex exec JSON events did not expose a backend session/thread id"
        if execution.backend_session_id in self._backend_session_ids:
            return (
                "codex exec reused a backend session/thread id across stages: "
                + execution.backend_session_id
            )
        return ""

    def _block_stage(
        self,
        state: dict[str, Any],
        *,
        stage: str,
        role: str,
        result: ProcessResult,
        artifacts: dict[str, Any],
        status: str,
        reasons: Sequence[str],
        validation: ValidationResult | None = None,
    ) -> CycleResult:
        self._write_stage_status(
            stage=stage,
            role=role,
            status=status,
            result=result,
            artifacts=artifacts,
            reason=reasons[0],
            validation=validation,
            blocking_reasons=reasons,
        )
        self._write_contract_result(
            stage=stage,
            role=role,
            outcome="blocked",
            result=result,
            artifacts=artifacts,
            blocking_reasons=reasons,
        )
        state["workflow_status"] = status
        state["stage_status"] = "blocked-input"
        state["current_stage"] = stage
        state[f"{role}_stage_status"] = status
        state["blocking_reasons"] = list(reasons)
        if validation is not None:
            state["validator_report"] = relative_path(self.validator_path, self.ft_root)
        self._write_state(state)
        append_event(self.cycle_dir, "stage_blocked", stage=stage, status=status, reasons=list(reasons))
        return self._result(state)

    def _production_snapshot(self) -> dict[str, str]:
        production_dir = self.ft_root / "test-cases"
        if not production_dir.exists():
            return {}
        return {
            relative_path(path, self.ft_root): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(production_dir.rglob("*.md"))
            if path.is_file()
        }

    def _production_changes(self, before: dict[str, str]) -> list[str]:
        after = self._production_snapshot()
        return sorted(
            path
            for path in set(before) | set(after)
            if before.get(path) != after.get(path)
        )

    def _promote(self, production_before: dict[str, str], *, expected_draft_sha256: str) -> None:
        changes = self._production_changes(production_before)
        if changes:
            raise RunnerError(
                "production test-cases changed before runner promotion: " + ", ".join(changes)
            )
        if self.final_path.exists() and not self.allow_overwrite_final:
            raise RunnerError(f"final artifact already exists and overwrite is disabled: {self.final_path}")
        if not self.draft_path.is_file():
            raise RunnerError("writer draft is missing before promotion")
        actual_draft_sha256 = sha256_file(self.draft_path)
        if actual_draft_sha256 != expected_draft_sha256:
            raise RunnerError(
                "writer draft changed after validation/review and cannot be promoted: "
                f"expected sha256={expected_draft_sha256}, actual sha256={actual_draft_sha256}"
            )
        self.final_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.final_path.with_suffix(self.final_path.suffix + ".promotion-tmp")
        try:
            shutil.copyfile(self.draft_path, temporary_path)
            if sha256_file(temporary_path) != expected_draft_sha256:
                raise RunnerError("promotion copy hash differs from the validated writer draft")
            temporary_path.replace(self.final_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def _reviewer_message(self, stdout: str) -> str:
        if not self.command_config.json_flag:
            return stdout
        messages: list[str] = []
        for raw_line in stdout.splitlines():
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            message = agent_message_from_event(event)
            if message:
                messages.append(message)
        return messages[-1] if messages else ""


def backend_session_id_from_events(text: str) -> str:
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or event.get("event") or "").lower()
        if event_type not in {
            "thread.started",
            "thread_started",
            "session.started",
            "session_started",
        }:
            continue
        for key in ("thread_id", "session_id", "id"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        thread = event.get("thread")
        if isinstance(thread, dict):
            value = thread.get("id")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def usage_from_events(text: str) -> dict[str, int] | None:
    aliases = {
        "input_tokens": ("input_tokens", "prompt_tokens"),
        "cached_input_tokens": ("cached_input_tokens", "cached_prompt_tokens"),
        "output_tokens": ("output_tokens", "completion_tokens"),
        "total_tokens": ("total_tokens",),
    }
    collected: dict[str, int] = {}
    for raw_line in text.splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            item = event.get("item")
            usage = item.get("usage") if isinstance(item, dict) else None
        if not isinstance(usage, dict):
            continue
        for canonical, candidates in aliases.items():
            for candidate in candidates:
                value = usage.get(candidate)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    collected[canonical] = value
                    break
    if "total_tokens" not in collected:
        input_tokens = collected.get("input_tokens")
        output_tokens = collected.get("output_tokens")
        if input_tokens is not None and output_tokens is not None:
            collected["total_tokens"] = input_tokens + output_tokens
    return collected or None


def agent_message_from_event(event: Any) -> str:
    if not isinstance(event, dict):
        return ""
    item = event.get("item")
    if isinstance(item, dict) and str(item.get("type") or "") in {"agent_message", "message"}:
        for key in ("text", "content", "message"):
            if isinstance(item.get(key), str):
                return item[key]
    message = event.get("message")
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        for key in ("text", "content"):
            if isinstance(message.get(key), str):
                return message[key]
    for key in ("response", "final_response", "output_text"):
        if isinstance(event.get(key), str):
            return event[key]
    return ""


def parse_review_contract(text: str) -> ReviewContract:
    candidate = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(\{.*\})\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"reviewer final output is not a valid JSON contract: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise RunnerError("reviewer final output must be one JSON object")
    if set(payload) != {"decision", "findings_markdown"}:
        raise RunnerError("reviewer final output must contain exactly decision and findings_markdown")
    decision = str(payload.get("decision") or "").strip()
    findings = payload.get("findings_markdown")
    if decision not in REVIEW_DECISIONS:
        raise RunnerError(f"reviewer decision must be one of {sorted(REVIEW_DECISIONS)}")
    if not isinstance(findings, str) or not findings.strip():
        raise RunnerError("reviewer findings_markdown must be a non-empty string")
    return ReviewContract(decision=decision, findings_markdown=findings)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prototype stage-per-process codex exec review-cycle runner. "
            "CLI flags must come from a local capability probe; unverified contracts are rejected."
        )
    )
    parser.add_argument("--ft-root", required=True)
    parser.add_argument("--cycle-dir", required=True)
    parser.add_argument("--final-artifact", required=True)
    parser.add_argument("--source-file", action="append", default=[])
    parser.add_argument("--handoff-file", action="append", default=[])
    parser.add_argument("--instruction-file", action="append", default=[])
    parser.add_argument("--prepared-package")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--sandbox-flag", required=True)
    parser.add_argument("--writer-sandbox", required=True)
    parser.add_argument("--reviewer-sandbox", required=True)
    parser.add_argument("--working-directory-flag", required=True)
    parser.add_argument("--json-flag")
    parser.add_argument("--output-last-message-flag")
    parser.add_argument("--output-schema-flag")
    parser.add_argument("--extra-arg", action="append", default=[])
    parser.add_argument("--cli-contract-verified", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--writer-timeout-seconds", type=int, default=180)
    parser.add_argument("--reviewer-timeout-seconds", type=int, default=120)
    parser.add_argument("--writer-idle-timeout-seconds", type=int, default=60)
    parser.add_argument("--reviewer-idle-timeout-seconds", type=int, default=45)
    parser.add_argument("--writer-command-budget", type=int, default=12)
    parser.add_argument("--reviewer-command-budget", type=int, default=8)
    parser.add_argument("--promote-final", action="store_true")
    parser.add_argument("--allow-overwrite-final", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path.cwd().resolve()
    runner = CodexExecReviewCycleRunner(
        repo_root=repo_root,
        ft_root=(repo_root / args.ft_root),
        cycle_dir=(repo_root / args.cycle_dir),
        final_path=(repo_root / args.final_artifact),
        source_files=[repo_root / item for item in args.source_file],
        handoff_files=[repo_root / item for item in args.handoff_file],
        prepared_package_path=(repo_root / args.prepared_package if args.prepared_package else None),
        instruction_files=[repo_root / item for item in args.instruction_file],
        command_config=ExecCommandConfig(
            executable=args.codex_command,
            sandbox_flag=args.sandbox_flag,
            writer_sandbox=args.writer_sandbox,
            reviewer_sandbox=args.reviewer_sandbox,
            working_directory_flag=args.working_directory_flag,
            json_flag=args.json_flag,
            output_last_message_flag=args.output_last_message_flag,
            output_schema_flag=args.output_schema_flag,
            extra_args=tuple(args.extra_arg),
            cli_contract_verified=args.cli_contract_verified,
        ),
        timeout_seconds=args.timeout_seconds,
        writer_timeout_seconds=args.writer_timeout_seconds,
        reviewer_timeout_seconds=args.reviewer_timeout_seconds,
        writer_idle_timeout_seconds=args.writer_idle_timeout_seconds,
        reviewer_idle_timeout_seconds=args.reviewer_idle_timeout_seconds,
        writer_command_budget=args.writer_command_budget,
        reviewer_command_budget=args.reviewer_command_budget,
        promote_final=args.promote_final,
        allow_overwrite_final=args.allow_overwrite_final,
    )
    try:
        result = runner.run()
    except RunnerError as exc:
        print(json.dumps({"status": "blocked-configuration", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(
        json.dumps(
            {
                "status": result.status,
                "final_promoted": result.final_promoted,
                "state": relative_path(result.state_path, repo_root),
                "draft": relative_path(result.draft_path, repo_root),
                "final": relative_path(result.final_path, repo_root),
                "blocking_reasons": list(result.blocking_reasons),
            },
            ensure_ascii=False,
        )
    )
    return 0 if result.status == "signed-off" else 2


if __name__ == "__main__":
    raise SystemExit(main())
