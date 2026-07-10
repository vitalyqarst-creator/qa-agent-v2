from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence


WRITER_STAGE = "writer-r1"
REVIEWER_STAGE = "reviewer-r1"
RUNNER_EVENTS = "runner-events.ndjson"
REVIEW_DECISIONS = {"accepted", "changes-required"}


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


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    launch_error: bool = False
    duration_seconds: float = 0.0


class ProcessExecutor(Protocol):
    def execute(self, request: ProcessRequest) -> ProcessResult:
        ...


class SubprocessExecutor:
    def execute(self, request: ProcessRequest) -> ProcessResult:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(request.command),
                cwd=request.cwd,
                input=request.prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=request.timeout_seconds,
                check=False,
                env=self._utf8_environment(),
            )
            return ProcessResult(
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                duration_seconds=time.monotonic() - started,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessResult(
                exit_code=None,
                stdout=normalized_text(exc.stdout),
                stderr=normalized_text(exc.stderr),
                timed_out=True,
                duration_seconds=time.monotonic() - started,
            )
        except OSError as exc:
            return ProcessResult(
                exit_code=None,
                stderr=f"{type(exc).__name__}: {exc}",
                launch_error=True,
                duration_seconds=time.monotonic() - started,
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

    def build(self, *, role: str, cwd: Path, last_message_path: Path | None = None) -> tuple[str, ...]:
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
    executor: ProcessExecutor = field(default_factory=SubprocessExecutor)
    validator: DraftValidator = field(default_factory=ProjectDraftStructureValidator)
    timeout_seconds: int = 1800
    promote_final: bool = False
    allow_overwrite_final: bool = False

    def __post_init__(self) -> None:
        self.repo_root = self.repo_root.resolve()
        self.ft_root = self.ft_root.resolve()
        self.cycle_dir = self.cycle_dir.resolve()
        self.final_path = self.final_path.resolve()
        self.source_files = tuple(path.resolve() for path in self.source_files)
        self.handoff_files = tuple(path.resolve() for path in self.handoff_files)

    @property
    def outputs_dir(self) -> Path:
        return self.cycle_dir / "outputs"

    @property
    def stage_inputs_dir(self) -> Path:
        return self.cycle_dir / "stage-inputs"

    @property
    def state_path(self) -> Path:
        return self.cycle_dir / "cycle-state.yaml"

    @property
    def draft_path(self) -> Path:
        return self.outputs_dir / f"{WRITER_STAGE}-draft.md"

    @property
    def validator_path(self) -> Path:
        return self.outputs_dir / f"validator-{WRITER_STAGE}.json"

    @property
    def reviewer_findings_path(self) -> Path:
        return self.outputs_dir / f"{REVIEWER_STAGE}-findings.md"

    def _runner_owned_paths(self) -> tuple[Path, ...]:
        paths = [
            self.state_path,
            self.cycle_dir / RUNNER_EVENTS,
            self.stage_inputs_dir / f"{WRITER_STAGE}-prompt.md",
            self.stage_inputs_dir / f"{REVIEWER_STAGE}-prompt.md",
            self.draft_path,
            self.validator_path,
            self.reviewer_findings_path,
            self.outputs_dir / f"{WRITER_STAGE}-last-message.txt",
        ]
        for stage in (WRITER_STAGE, REVIEWER_STAGE):
            paths.extend(
                self.outputs_dir / f"{stage}-{suffix}"
                for suffix in (
                    "stdout.txt",
                    "stderr.txt",
                    "events.ndjson",
                    "stage-status.json",
                )
            )
        return tuple(paths)

    def validate_configuration(self) -> None:
        self.command_config.validate()
        if self.timeout_seconds < 1:
            raise RunnerError("timeout_seconds must be >= 1")
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
        if not self.source_files:
            raise RunnerError("At least one explicit source file is required")
        if not self.handoff_files:
            raise RunnerError("At least one explicit handoff file is required")
        for input_path in (*self.source_files, *self.handoff_files):
            if not input_path.is_file():
                raise RunnerError(f"Stage input does not exist: {input_path}")
            if not is_relative_to(input_path, self.ft_root):
                raise RunnerError(f"Stage input must be under the FT package: {input_path}")
        existing_runner_artifacts = [path for path in self._runner_owned_paths() if path.exists()]
        if existing_runner_artifacts:
            joined = ", ".join(relative_path(path, self.repo_root) for path in existing_runner_artifacts)
            raise RunnerError(
                "Cycle directory contains runner-owned artifacts from an earlier attempt; "
                "use a new cycle directory or an explicit recovery path instead of reusing stale outputs: "
                + joined
            )

    def run(self) -> CycleResult:
        self.validate_configuration()
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.stage_inputs_dir.mkdir(parents=True, exist_ok=True)
        production_before = self._production_snapshot()
        writer_prompt = self._writer_prompt()
        writer_prompt_path = self.stage_inputs_dir / f"{WRITER_STAGE}-prompt.md"
        writer_prompt_path.write_text(writer_prompt, encoding="utf-8")
        state = self._initial_state()
        self._write_state(state)
        append_event(self.cycle_dir, "cycle_started", backend="codex-exec")

        writer_result, writer_artifacts = self._run_stage(
            stage=WRITER_STAGE,
            role="writer",
            prompt=writer_prompt,
            last_message_path=self.outputs_dir / f"{WRITER_STAGE}-last-message.txt",
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
            status = "blocked-timeout" if writer_result.timed_out else "blocked-missing-output"
            reason = (
                "writer timed out and the required draft is missing"
                if writer_result.timed_out
                else "writer exited without the required draft"
            )
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

        draft_sha256 = sha256_file(self.draft_path)
        writer_status = "completed-with-progress" if writer_result.timed_out else "completed"
        self._write_stage_status(
            stage=WRITER_STAGE,
            role="writer",
            status=writer_status,
            result=writer_result,
            artifacts=writer_artifacts,
            reason=(
                "process timed out, but the required draft exists and deterministic validation passed"
                if writer_result.timed_out
                else "required draft exists and deterministic validation passed"
            ),
            validation=validation,
            draft_sha256=draft_sha256,
        )
        reviewer_prompt = self._reviewer_prompt()
        reviewer_prompt_path = self.stage_inputs_dir / f"{REVIEWER_STAGE}-prompt.md"
        reviewer_prompt_path.write_text(reviewer_prompt, encoding="utf-8")
        state.update(
            {
                "workflow_status": "reviewer-ready",
                "stage_status": "writer-draft-ready",
                "current_stage": REVIEWER_STAGE,
                "writer_stage_status": writer_status,
                "writer_draft_sha256": draft_sha256,
                "validator_report": relative_path(self.validator_path, self.ft_root),
                "active_transition_prompt": relative_path(
                    self.stage_inputs_dir / f"{REVIEWER_STAGE}-prompt.md", self.ft_root
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
        if reviewer_result.timed_out:
            return self._block_stage(
                state,
                stage=REVIEWER_STAGE,
                role="reviewer",
                result=reviewer_result,
                artifacts=reviewer_artifacts,
                status="blocked-timeout",
                reasons=["reviewer timed out; a partial review is not accepted as terminal sign-off"],
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
            "writer_draft_sha256": "",
            "reviewer_findings": "",
            "accepted_terminal_state": False,
            "final_promoted": False,
            "draft_or_unsigned": True,
            "promotion_status": "pending",
            "active_transition_prompt": relative_path(
                self.stage_inputs_dir / f"{WRITER_STAGE}-prompt.md", self.ft_root
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
        stdout_path = self.outputs_dir / f"{stage}-stdout.txt"
        stderr_path = self.outputs_dir / f"{stage}-stderr.txt"
        events_path = self.outputs_dir / f"{stage}-events.ndjson"
        command = self.command_config.build(
            role=role,
            cwd=self.repo_root,
            last_message_path=last_message_path,
        )
        request = ProcessRequest(
            stage=stage,
            role=role,
            command=command,
            cwd=self.repo_root,
            prompt=prompt,
            timeout_seconds=self.timeout_seconds,
        )
        append_event(
            self.cycle_dir,
            "stage_process_started",
            stage=stage,
            role=role,
            command=list(command),
        )
        result = self.executor.execute(request)
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        if self.command_config.json_flag:
            events_path.write_text(result.stdout, encoding="utf-8")
        artifacts = {
            "command": list(command),
            "stdout": relative_path(stdout_path, self.repo_root),
            "stderr": relative_path(stderr_path, self.repo_root),
            "events": relative_path(events_path, self.repo_root) if self.command_config.json_flag else "",
            "last_message": (
                relative_path(last_message_path, self.repo_root) if last_message_path is not None else ""
            ),
        }
        append_event(
            self.cycle_dir,
            "stage_process_finished",
            stage=stage,
            role=role,
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            launch_error=result.launch_error,
            stdout=artifacts["stdout"],
            stderr=artifacts["stderr"],
            events=artifacts["events"],
        )
        return result, artifacts

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
        status_path = self.outputs_dir / f"{stage}-stage-status.json"
        payload: dict[str, Any] = {
            "stage": stage,
            "role": role,
            "status": status,
            "reason": reason,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "launch_error": result.launch_error,
            "duration_seconds": round(result.duration_seconds, 3),
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
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--sandbox-flag", required=True)
    parser.add_argument("--writer-sandbox", required=True)
    parser.add_argument("--reviewer-sandbox", required=True)
    parser.add_argument("--working-directory-flag", required=True)
    parser.add_argument("--json-flag")
    parser.add_argument("--output-last-message-flag")
    parser.add_argument("--extra-arg", action="append", default=[])
    parser.add_argument("--cli-contract-verified", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
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
        command_config=ExecCommandConfig(
            executable=args.codex_command,
            sandbox_flag=args.sandbox_flag,
            writer_sandbox=args.writer_sandbox,
            reviewer_sandbox=args.reviewer_sandbox,
            working_directory_flag=args.working_directory_flag,
            json_flag=args.json_flag,
            output_last_message_flag=args.output_last_message_flag,
            extra_args=tuple(args.extra_arg),
            cli_contract_verified=args.cli_contract_verified,
        ),
        timeout_seconds=args.timeout_seconds,
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
