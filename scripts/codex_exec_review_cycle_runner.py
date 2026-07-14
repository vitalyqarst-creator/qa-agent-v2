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
from typing import Any, Callable, Protocol, Sequence

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
    PACKAGE_VERSION,
    STANDARD_EXECUTION_PROFILE,
    PreparedStagePackage,
    load_obligations,
    load_prepared_package,
)
from test_case_agent.review_cycle.obligation_gate import (
    materialize_draft_dictionary_projections,
    materialize_draft_reference_fixtures,
    reference_fixture_block,
    validate_draft_obligation_coverage,
    validate_writer_dictionary_ownership,
)
from test_case_agent.review_cycle.promotion_readiness import (
    PromotionContract,
    validate_promotion_readiness,
)
from test_case_agent.review_cycle.evidence_access import validate_evidence_access
from test_case_agent.review_cycle.attempts import format_attempt_id
from test_case_agent.review_cycle.orchestration import StageCompletionCoordinator
from scripts.resolve_instruction_context import resolve_instruction_context


WRITER_STAGE = "writer-r1"
REVIEWER_STAGE = "reviewer-r1"
RUNNER_EVENTS = "runner-events.ndjson"
REVIEW_DECISIONS = {"accepted", "changes-required"}
PREPARED_REVIEW_VERDICTS = {
    "covered",
    "missing",
    "incorrect",
    "gap-preserved",
    "invented-coverage",
}
REVIEW_FINDING_SEVERITIES = {"error", "warning", "info"}
REVIEW_FINDING_CATEGORIES = {
    "test-design",
    "expected-result",
    "coverage",
    "atomarity",
    "duplication",
    "scope",
}
ATTEMPT_ID = format_attempt_id(1)
SEED_MARKER = "PREPARED-DRAFT-SEED"
PREPARED_FAST_WRITER_MODES = {"structured", "workspace"}
DEFAULT_PREPARED_FAST_WRITER_MODE = "structured"
PREPARED_STANDARD_WRITER_MODES = {"structured", "assisted"}
DEFAULT_PREPARED_STANDARD_WRITER_MODE = "structured"
MAX_STRUCTURED_WRITER_DRAFT_BYTES = 128 * 1024
DEFAULT_PREPARED_REVIEWER_PROMPT_MAX_BYTES = 64 * 1024
DEFAULT_PREPARED_STANDARD_WRITER_CONTEXT_MAX_BYTES = 512 * 1024
DEFAULT_PREPARED_STANDARD_REVIEWER_CONTEXT_MAX_BYTES = 768 * 1024
DEFAULT_PREPARED_STRUCTURED_WRITER_SINGLE_SESSION_TC_LIMIT = 12
DEFAULT_PREPARED_STRUCTURED_WRITER_SHARD_SIZE = 12
DEFAULT_PREPARED_STRUCTURED_WRITER_MAX_SHARDS = 8
DEFAULT_PREPARED_TARGETED_REPAIR_MAX_TEST_CASES = 12
DEFAULT_PREPARED_STRUCTURED_REVIEWER_OBLIGATION_LIMIT = 100
MAX_ESTIMATED_STRUCTURED_REVIEWER_OUTPUT_BYTES = 64 * 1024
DEFAULT_STANDARD_WRITER_COMMAND_BUDGET = 80
DEFAULT_STANDARD_REVIEWER_COMMAND_BUDGET = 48
DEFAULT_STANDARD_WRITER_TIMEOUT_SECONDS = 900
DEFAULT_STANDARD_REVIEWER_TIMEOUT_SECONDS = 450
DEFAULT_STANDARD_WRITER_IDLE_TIMEOUT_SECONDS = 180
DEFAULT_STANDARD_REVIEWER_IDLE_TIMEOUT_SECONDS = 120
DEFAULT_PREPARED_STANDARD_REVIEWER_IDLE_TIMEOUT_SECONDS = 300
DEFAULT_STANDARD_WRITER_FIRST_ARTIFACT_DEADLINE_SECONDS = 600
STANDARD_COMMAND_BUDGET_RESERVE = 5
STANDARD_STAGE_SCENARIOS = {
    "writer": "writer.session_initial_draft",
    "reviewer": "reviewer.semantic_traceability_test_design",
}
GENERIC_EXECUTION_FIXTURE_RE = re.compile(
    r"(?:"
    r"значени\w*\s+заявк\w*[,;:]?\s+необходим\w*\s+для\s+(?:е[ёе]\s+)?сохран|"
    r"фио,?\s+для\s+котор\w*\s+доступн\w*\s+подсказк\w*|"
    r"дат\w*\s+в\s+допустим\w*\s+диапазон\w*|"
    r"values?\s+(?:needed|required)\s+to\s+save"
    r")",
    flags=re.IGNORECASE,
)
UNDEFINED_EXECUTION_ACTION_RE = re.compile(
    r"(?:"
    r"(?:попытаться|попытк\w*|продолжить)\s+(?:дальнейш\w*\s+)?сценар\w*|"
    r"attempt(?:\s+to)?\s+(?:continue|proceed)\s+(?:the\s+)?scenario"
    r")",
    flags=re.IGNORECASE,
)
AMBIGUOUS_EXECUTION_ACTION_RE = re.compile(
    r"(?:"
    r"(?:выбрать|установить|ввести|нажать|сохранить|открыть|закрыть|"
    r"перейти|очистить|заполнить)\s+или\s+"
    r"(?:выбрать|установить|ввести|нажать|сохранить|открыть|закрыть|"
    r"перейти|очистить|заполнить)|"
    r"(?:select|set|enter|click|save|open|close|navigate|clear|fill)\s+or\s+"
    r"(?:select|set|enter|click|save|open|close|navigate|clear|fill)"
    r")",
    flags=re.IGNORECASE,
)
ANY_DICTIONARY_GROUP_RE = re.compile(
    r"(?:в\s+люб\w*\s+групп\w*|any\s+(?:available\s+)?group)",
    flags=re.IGNORECASE,
)
NON_OBSERVABLE_EXPECTED_RESULT_RE = re.compile(
    r"(?:"
    r"(?:точн\w*|конкретн\w*)\s+ui[- ]реакц\w*\s+"
    r"(?:не\s+определ\w*|подлежит\s+калибровк\w*)|"
    r"предназначен\w*\s+для\s+ввод\w*\s+дат\w*|"
    r"сам\w*\s+по\s+себе\s+не\s+нарушает\s+требован\w*\s+обязательност\w*"
    r")",
    flags=re.IGNORECASE,
)
RESET_ACTION_RE = re.compile(
    r"(?:\bclear\b|\breset\b|очист\w*|сброс\w*)",
    flags=re.IGNORECASE,
)
CAPTURED_INITIAL_STATE_RE = re.compile(
    r"(?:captured\s+initial|зафиксирован\w*\s+(?:initial|исходн\w*)|"
    r"исходн\w*\s+состояни\w*)",
    flags=re.IGNORECASE,
)
REPAIRABLE_QUALITY_FINDING_IDS = {
    "ambiguous-dictionary-value-path",
    "ambiguous-execution-action",
    "generic-execution-fixture",
    "missing-branch-precondition",
    "undefined-execution-action",
    "non-observable-expected-result",
}
PACKAGE_ID_LINE_RE = re.compile(
    r"(?m)^\*\*package_id:\*\*\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*$"
)
PACKAGE_VERSION_LITERAL_RE = re.compile(
    r"\bpackage(?:_|\s+)version\b[^\r\n\d]{0,24}`?(\d+)`?",
    flags=re.IGNORECASE,
)
SHA256_HEX_RE = re.compile(r"[0-9a-f]{64}")

InstructionContextResolver = Callable[..., dict[str, Any]]


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


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_case_section_spans(text: str) -> list[tuple[str, int, int, str]]:
    matches = list(
        re.finditer(r"(?m)^##\s+(TC-[A-Za-z0-9][A-Za-z0-9_.-]*)\s*$", text)
    )
    return [
        (
            match.group(1),
            match.start(),
            matches[index + 1].start() if index + 1 < len(matches) else len(text),
            text[
                match.start() : (
                    matches[index + 1].start() if index + 1 < len(matches) else len(text)
                )
            ],
        )
        for index, match in enumerate(matches)
    ]


def markdown_subsection(section: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^###\s+{re.escape(heading)}\s*$\n(.*?)(?=^###\s+|\Z)",
        section,
    )
    return match.group(1).strip() if match else ""


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
    idle_timeout_seconds: int | None
    command_budget: int
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    progress_path: Path | None = None
    progress_forbidden_marker: str = ""
    first_artifact_deadline_seconds: int | None = None


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    idle_timed_out: bool = False
    command_budget_exceeded: bool = False
    first_artifact_deadline_exceeded: bool = False
    launch_error: bool = False
    duration_seconds: float = 0.0
    command_count: int = 0
    first_output_seconds: float | None = None
    first_artifact_seconds: float | None = None
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
        first_artifact_seconds: float | None = None
        last_output_at = started
        last_progress_signature: tuple[int, int] | None = None
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
                    if request.progress_path is not None and request.progress_path.is_file():
                        stat = request.progress_path.stat()
                        signature = (stat.st_mtime_ns, stat.st_size)
                        if signature != last_progress_signature:
                            last_progress_signature = signature
                            last_output_at = now
                        if first_artifact_seconds is None and stat.st_size > 0:
                            content = request.progress_path.read_text(
                                encoding="utf-8", errors="replace"
                            )
                            if (
                                not request.progress_forbidden_marker
                                or request.progress_forbidden_marker not in content
                            ):
                                first_artifact_seconds = now - started
                    if process.poll() is None:
                        if now - started >= request.timeout_seconds:
                            termination_reason = "hard-timeout"
                            break
                        if (
                            request.first_artifact_deadline_seconds is not None
                            and first_artifact_seconds is None
                            and now - started >= request.first_artifact_deadline_seconds
                        ):
                            termination_reason = "first-artifact-deadline"
                            break
                        if (
                            request.idle_timeout_seconds is not None
                            and (
                                request.progress_path is None
                                or first_artifact_seconds is not None
                            )
                            and now - last_output_at >= request.idle_timeout_seconds
                        ):
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
                first_artifact_deadline_exceeded=(
                    termination_reason == "first-artifact-deadline"
                ),
                duration_seconds=time.monotonic() - started,
                command_count=command_count,
                first_output_seconds=first_output_seconds,
                first_artifact_seconds=first_artifact_seconds,
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
        sandbox_override: str | None = None,
    ) -> tuple[str, ...]:
        sandbox = sandbox_override or (
            self.writer_sandbox if role == "writer" else self.reviewer_sandbox
        )
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


def _normalized_case_body(value: str) -> str:
    normalized_lines = []
    for raw_line in value.splitlines():
        line = re.sub(r"^\s*\d+[.)]\s*", "", raw_line.strip())
        line = re.sub(r"\s+", " ", line).strip().lower()
        line = re.sub(
            r"\b(?:строковое|текстовое|допустимое|синтетическое|string|text|valid|synthetic)\s+(?=значение\b|value\b)",
            "",
            line,
            flags=re.IGNORECASE,
        )
        if line:
            normalized_lines.append(line)
    return "\n".join(normalized_lines)


def _test_case_subsection(body: str, names: str) -> str:
    match = re.search(
        rf"(?ms)^###\s+(?:{names})\s*$\s*(.*?)(?=^###\s+|\Z)",
        body,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def build_semantic_overlap_diagnostic(draft_path: Path) -> dict[str, Any]:
    text = draft_path.read_text(encoding="utf-8")
    cases: list[dict[str, str]] = []
    for match in re.finditer(
        r"(?ms)^##\s+(TC-[A-Za-z0-9_.-]+)\s*$\s*(.*?)(?=^##\s+TC-[A-Za-z0-9_.-]+\s*$|\Z)",
        text,
    ):
        tc_id, body = match.groups()
        title_match = re.search(
            r"(?m)^\*\*(?:Название|Title):\*\*\s*(.+?)\s*$",
            body,
            flags=re.IGNORECASE,
        )
        trace_match = re.search(
            r"(?m)^\*\*(?:Трассировка|Traceability):\*\*\s*(.+?)\s*$",
            body,
            flags=re.IGNORECASE,
        )
        steps = _test_case_subsection(body, r"Шаги|Steps")
        expected = _test_case_subsection(
            body,
            r"Итоговый\s+ожидаемый\s+результат|Expected\s+result|Final\s+expected\s+result",
        )
        signature = (
            _normalized_case_body(steps),
            _normalized_case_body(expected),
        )
        if all(signature):
            cases.append(
                {
                    "tc_id": tc_id,
                    "title": title_match.group(1).strip() if title_match else "",
                    "traceability": trace_match.group(1).strip() if trace_match else "",
                    "signature": "\n---EXPECTED---\n".join(signature),
                }
            )
    grouped: dict[str, list[dict[str, str]]] = {}
    for item in cases:
        grouped.setdefault(item["signature"], []).append(item)
    findings = []
    for index, items in enumerate(
        (items for items in grouped.values() if len(items) > 1),
        start=1,
    ):
        findings.append(
            {
                "id": f"semantic-overlap-{index:03d}",
                "severity": "warning",
                "category": "duplication",
                "blocking": False,
                "test_case_ids": [item["tc_id"] for item in items],
                "titles": [item["title"] for item in items],
                "traceability": [item["traceability"] for item in items],
                "reason": "Test cases have identical normalized steps and final expected result.",
                "required_review": (
                    "Classify as a justified multi-obligation check or require consolidation; "
                    "unique titles alone are insufficient."
                ),
            }
        )
    return {
        "passed": True,
        "validator": "semantic-overlap-diagnostic-v1",
        "status": "overlap-detected" if findings else "clean",
        "blocking": False,
        "test_case_count": len(cases),
        "findings": findings,
        "checked_paths": [str(draft_path)],
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

    @staticmethod
    def _execution_readiness_findings(text: str) -> tuple[dict[str, Any], ...]:
        findings: list[dict[str, Any]] = []
        if re.search(r"\brequires-binding\b", text, flags=re.IGNORECASE):
            findings.append(
                {
                    "id": "unresolved-execution-binding",
                    "severity": "error",
                    "message": (
                        "Draft contains requires-binding fixture or dictionary values and is not "
                        "execution-ready. Bind concrete routes, fields and literals or preserve the "
                        "obligation as GAP/unclear before semantic review."
                    ),
                }
            )
        if re.search(
            r"(?:Итог\s+)?Writer\s+Quality\s+Gate\s*:\s*`?(?:blocked|fail)\b",
            text,
            flags=re.IGNORECASE,
        ):
            findings.append(
                {
                    "id": "writer-quality-gate-self-blocked",
                    "severity": "error",
                    "message": (
                        "Draft explicitly reports a blocked Writer Quality Gate and cannot advance "
                        "to semantic review."
                    ),
                }
            )
        if re.search(
            r"execution-ready\s+test\s+cases\s*:\s*`?0\s*/\s*[1-9]\d*",
            text,
            flags=re.IGNORECASE,
        ):
            findings.append(
                {
                    "id": "no-execution-ready-test-cases",
                    "severity": "error",
                    "message": (
                        "Draft explicitly reports zero execution-ready test cases and cannot claim "
                        "executable coverage."
                    ),
                }
            )
        placeholder_match = re.search(
            r"<\s*(?:ID|идентификатор|значение|данные|fixture|test[- ]?data)\b[^>\r\n]*>",
            text,
            flags=re.IGNORECASE,
        )
        if placeholder_match:
            findings.append(
                {
                    "id": "unresolved-test-data-placeholder",
                    "severity": "error",
                    "message": (
                        "Draft contains an unresolved angle-bracket test-data placeholder "
                        f"{placeholder_match.group(0)!r}. Bind a concrete value or a named "
                        "reproducible fixture before semantic review."
                    ),
                }
            )
        return tuple(findings)

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
        findings.extend(self._execution_readiness_findings(draft_path.read_text(encoding="utf-8")))
        return ValidationResult(
            passed=not findings,
            findings=tuple(findings),
            checked_paths=tuple(checked_paths),
            validator="codex_review_cycle_runner.evaluate_test_case_markdown_structure",
        )


@dataclass(frozen=True)
class ObligationReview:
    obligation_id: str
    atom_id: str
    verdict: str
    test_case_ids: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class ReviewFinding:
    finding_id: str
    severity: str
    category: str
    atom_ids: tuple[str, ...]
    test_case_ids: tuple[str, ...]
    problem: str
    required_change: str


@dataclass(frozen=True)
class ReviewContract:
    decision: str
    findings_markdown: str = ""
    contract_version: int = 1
    reviewed_draft_sha256: str = ""
    obligation_reviews: tuple[ObligationReview, ...] = ()
    findings: tuple[ReviewFinding, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class WriterContract:
    status: str
    draft_markdown: str
    blocking_reasons: tuple[str, ...] = ()
    contract_version: int = 1


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
    prepared_repair_draft_path: Path | None = None
    prepared_repair_findings_path: Path | None = None
    prepared_reviewer_rebind_draft_path: Path | None = None
    promotion_contract_path: Path | None = None
    instruction_files: Sequence[Path] = ()
    writer_instruction_files: Sequence[Path] = ()
    reviewer_instruction_files: Sequence[Path] = ()
    executor: ProcessExecutor = field(default_factory=SubprocessExecutor)
    validator: DraftValidator = field(default_factory=ProjectDraftStructureValidator)
    timeout_seconds: int = 1800
    writer_timeout_seconds: int | None = None
    reviewer_timeout_seconds: int | None = None
    prepared_reviewer_timeout_seconds: int = 90
    writer_idle_timeout_seconds: int = DEFAULT_STANDARD_WRITER_IDLE_TIMEOUT_SECONDS
    reviewer_idle_timeout_seconds: int = DEFAULT_STANDARD_REVIEWER_IDLE_TIMEOUT_SECONDS
    prepared_standard_reviewer_idle_timeout_seconds: int = (
        DEFAULT_PREPARED_STANDARD_REVIEWER_IDLE_TIMEOUT_SECONDS
    )
    writer_command_budget: int = DEFAULT_STANDARD_WRITER_COMMAND_BUDGET
    reviewer_command_budget: int = DEFAULT_STANDARD_REVIEWER_COMMAND_BUDGET
    prepared_reviewer_command_budget: int = 1
    prepared_fast_writer_mode: str = DEFAULT_PREPARED_FAST_WRITER_MODE
    prepared_standard_writer_mode: str = DEFAULT_PREPARED_STANDARD_WRITER_MODE
    writer_first_artifact_deadline_seconds: int = (
        DEFAULT_STANDARD_WRITER_FIRST_ARTIFACT_DEADLINE_SECONDS
    )
    prepared_reviewer_prompt_max_bytes: int = DEFAULT_PREPARED_REVIEWER_PROMPT_MAX_BYTES
    prepared_standard_writer_context_max_bytes: int = (
        DEFAULT_PREPARED_STANDARD_WRITER_CONTEXT_MAX_BYTES
    )
    prepared_standard_reviewer_context_max_bytes: int = (
        DEFAULT_PREPARED_STANDARD_REVIEWER_CONTEXT_MAX_BYTES
    )
    prepared_structured_writer_single_session_tc_limit: int = (
        DEFAULT_PREPARED_STRUCTURED_WRITER_SINGLE_SESSION_TC_LIMIT
    )
    prepared_structured_writer_shard_size: int = (
        DEFAULT_PREPARED_STRUCTURED_WRITER_SHARD_SIZE
    )
    prepared_structured_writer_max_shards: int = (
        DEFAULT_PREPARED_STRUCTURED_WRITER_MAX_SHARDS
    )
    prepared_targeted_repair_max_test_cases: int = (
        DEFAULT_PREPARED_TARGETED_REPAIR_MAX_TEST_CASES
    )
    prepared_structured_reviewer_obligation_limit: int = (
        DEFAULT_PREPARED_STRUCTURED_REVIEWER_OBLIGATION_LIMIT
    )
    promote_final: bool = False
    promotion_dry_run: bool = False
    allow_overwrite_final: bool = False
    instruction_context_resolver: InstructionContextResolver = resolve_instruction_context
    _manifests: dict[str, StageInputManifest] = field(default_factory=dict, init=False)
    _backend_session_ids: list[str] = field(default_factory=list, init=False)
    _prepared_package: PreparedStagePackage | None = field(default=None, init=False)
    _promotion_contract: PromotionContract | None = field(default=None, init=False)
    _draft_seed_sha256: str = field(default="", init=False)
    _standard_instruction_contexts: dict[str, tuple[Path, ...]] = field(
        default_factory=dict, init=False
    )
    _context_budget_reports: dict[str, dict[str, Any]] = field(
        default_factory=dict, init=False
    )
    _writer_dictionary_context_report: dict[str, Any] = field(
        default_factory=dict, init=False
    )
    _writer_output_capacity_plan: dict[str, Any] = field(default_factory=dict, init=False)
    _prepared_oracle_quality_plan: dict[str, Any] = field(default_factory=dict, init=False)
    _prepared_state_change_plan: dict[str, Any] = field(default_factory=dict, init=False)
    _prepared_repair_plan: dict[str, Any] = field(default_factory=dict, init=False)
    _prepared_reviewer_rebind_plan: dict[str, Any] = field(
        default_factory=dict, init=False
    )
    _reviewer_output_capacity_plan: dict[str, Any] = field(default_factory=dict, init=False)
    _reviewer_context_capacity_plan: dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.repo_root = self.repo_root.resolve()
        self.ft_root = self.ft_root.resolve()
        self.cycle_dir = self.cycle_dir.resolve()
        self.final_path = self.final_path.resolve()
        self.source_files = tuple(path.resolve() for path in self.source_files)
        self.handoff_files = tuple(path.resolve() for path in self.handoff_files)
        self.instruction_files = tuple(path.resolve() for path in self.instruction_files)
        self.writer_instruction_files = tuple(
            path.resolve() for path in self.writer_instruction_files
        )
        self.reviewer_instruction_files = tuple(
            path.resolve() for path in self.reviewer_instruction_files
        )
        if self.prepared_package_path is not None:
            self.prepared_package_path = self.prepared_package_path.resolve()
        if self.prepared_repair_draft_path is not None:
            self.prepared_repair_draft_path = self.prepared_repair_draft_path.resolve()
        if self.prepared_repair_findings_path is not None:
            self.prepared_repair_findings_path = self.prepared_repair_findings_path.resolve()
        if self.prepared_reviewer_rebind_draft_path is not None:
            self.prepared_reviewer_rebind_draft_path = (
                self.prepared_reviewer_rebind_draft_path.resolve()
            )
        if self.promotion_contract_path is not None:
            self.promotion_contract_path = self.promotion_contract_path.resolve()
        configured_instructions = tuple(path.resolve() for path in self.instruction_files)
        self.instruction_files = configured_instructions or ((self.repo_root / "AGENTS.md").resolve(),)
        package_notes = (self.ft_root / "AGENT-NOTES.md").resolve()
        if (
            self.prepared_package_path is None
            and package_notes.is_file()
            and package_notes not in self.handoff_files
            and package_notes not in self.source_files
        ):
            self.handoff_files = (*self.handoff_files, package_notes)

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
    def package_metadata_gate_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "package-metadata-gate.json"

    @property
    def semantic_overlap_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "semantic-overlap-diagnostic.json"

    @property
    def quality_gate_bundle_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "quality-gate-bundle.json"

    @property
    def calibration_lifecycle_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "calibration-lifecycle.json"

    @property
    def dictionary_projection_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "dictionary-projection.json"

    @property
    def promotion_readiness_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "promotion-readiness.json"

    @property
    def seed_gate_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "seed-gate.json"

    @property
    def evidence_access_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "evidence-access-report.json"

    @property
    def promotion_dry_run_path(self) -> Path:
        return self.cycle_dir / "promotion-dry-run.json"

    @property
    def draft_seed_path(self) -> Path:
        return self.attempt_root(WRITER_STAGE) / "runner-input" / "draft-seed.md"

    @property
    def reviewer_findings_path(self) -> Path:
        return self.runner_output_dir(REVIEWER_STAGE) / "findings.md"

    @property
    def reviewer_schema_path(self) -> Path:
        return self.attempt_root(REVIEWER_STAGE) / "review-contract.schema.json"

    @property
    def writer_schema_path(self) -> Path:
        return self.attempt_root(WRITER_STAGE) / "writer-contract.schema.json"

    @property
    def writer_result_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "writer-result.json"

    def writer_result_path_for(self, stage: str) -> Path:
        return self.runner_output_dir(stage) / "writer-result.json"

    def writer_shard_draft_path(self, stage: str) -> Path:
        return self.stage_output_dir(stage) / "shard.md"

    @property
    def writer_output_capacity_path(self) -> Path:
        return self.cycle_dir / "writer-output-capacity-preflight.json"

    @property
    def writer_shard_plan_path(self) -> Path:
        return self.cycle_dir / "writer-shard-plan.json"

    @property
    def prepared_oracle_quality_path(self) -> Path:
        return self.cycle_dir / "prepared-oracle-quality-preflight.json"

    @property
    def prepared_state_change_path(self) -> Path:
        return self.cycle_dir / "prepared-state-change-preflight.json"

    @property
    def prepared_repair_plan_path(self) -> Path:
        return self.cycle_dir / "writer-targeted-repair-plan.json"

    @property
    def reviewer_rebind_path(self) -> Path:
        return self.cycle_dir / "reviewer-rebind.json"

    @property
    def repair_draft_path(self) -> Path:
        return self.stage_output_dir(WRITER_STAGE) / "repair.md"

    @property
    def repair_validator_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "repair-validator.json"

    @property
    def repair_splice_path(self) -> Path:
        return self.runner_output_dir(WRITER_STAGE) / "repair-splice.json"

    @property
    def reviewer_evidence_access_path(self) -> Path:
        return self.runner_output_dir(REVIEWER_STAGE) / "evidence-access-report.json"

    def context_budget_path(self, stage: str) -> Path:
        return self.runner_output_dir(stage) / "context-budget.json"

    def artifact_graph_path(self, stage: str) -> Path:
        return self.attempt_root(stage) / "artifact-graph.json"

    def _runner_owned_paths(self) -> tuple[Path, ...]:
        paths = [
            self.state_path,
            self.cycle_dir / RUNNER_EVENTS,
            self.attempt_root(WRITER_STAGE),
            self.attempt_root(REVIEWER_STAGE),
            self.cycle_dir / "outputs",
            self.cycle_dir / "stage-inputs",
            self.writer_output_capacity_path,
            self.writer_shard_plan_path,
            self.prepared_oracle_quality_path,
            self.prepared_state_change_path,
            self.prepared_repair_plan_path,
            self.reviewer_rebind_path,
        ]
        return tuple(paths)

    def _standard_scenario(self, role: str) -> str:
        try:
            return STANDARD_STAGE_SCENARIOS[role]
        except KeyError as exc:
            raise RunnerError(f"Unsupported standard stage role: {role}") from exc

    def _is_prepared_fast(self) -> bool:
        return (
            self._prepared_package is not None
            and self._prepared_package.execution_profile == FAST_EXECUTION_PROFILE
        )

    def _is_prepared_standard(self) -> bool:
        return (
            self._prepared_package is not None
            and self._prepared_package.execution_profile == STANDARD_EXECUTION_PROFILE
        )

    def _uses_structured_prepared_writer(self) -> bool:
        return (
            self._is_prepared_fast()
            and self.prepared_fast_writer_mode == "structured"
        ) or (
            self._is_prepared_standard()
            and self.prepared_standard_writer_mode == "structured"
            and self._promotion_contract is None
        )

    def _uses_compact_prepared_reviewer(self) -> bool:
        return self._is_prepared_fast() or (
            self._is_prepared_standard()
            and self.prepared_standard_writer_mode == "structured"
        )

    def _uses_targeted_prepared_repair(self) -> bool:
        return bool(
            self._uses_structured_prepared_writer()
            and self.prepared_repair_draft_path is not None
            and self.prepared_repair_findings_path is not None
            and self._prepared_repair_plan.get("passed")
        )

    def _uses_prepared_reviewer_rebind(self) -> bool:
        return bool(
            self._uses_structured_prepared_writer()
            and self.prepared_reviewer_rebind_draft_path is not None
            and self._prepared_reviewer_rebind_plan.get("passed")
        )

    def _uses_generic_bounded_reviewer_schema(self) -> bool:
        return bool(
            self._uses_sharded_prepared_writer()
            or self._uses_targeted_prepared_repair()
            or self._uses_prepared_reviewer_rebind()
            or len(self._prepared_writer_groups())
            > self.prepared_structured_writer_single_session_tc_limit
        )

    def _prepared_writer_groups(self) -> list[tuple[str, list[Any]]]:
        obligations = load_obligations(self._prepared_artifact("atomic-obligations"))
        grouped: dict[str, list[Any]] = {}
        for index, obligation in enumerate(
            (item for item in obligations.obligations if item.coverage_status == "testable"),
            start=1,
        ):
            test_case_id = obligation.planned_test_case_id or f"TC-PREP-{index:03d}"
            grouped.setdefault(test_case_id, []).append(obligation)
        return sorted(grouped.items(), key=lambda item: self._test_case_id_sort_key(item[0]))

    def _build_prepared_oracle_quality_plan(self) -> dict[str, Any]:
        obligation_path = self._prepared_artifact("atomic-obligations")
        obligations = load_obligations(obligation_path)
        findings: list[dict[str, Any]] = []
        checked = 0
        for obligation in obligations.obligations:
            if obligation.coverage_status != "testable":
                continue
            checked += 1
            oracle = obligation.observable_oracle.strip()
            if not oracle:
                findings.append(
                    {
                        "id": "prepared-observable-oracle-missing",
                        "severity": "error",
                        "obligation_id": obligation.obligation_id,
                        "atom_id": obligation.traceability_atom_id,
                        "test_case_id": obligation.planned_test_case_id,
                    }
                )
            elif NON_OBSERVABLE_EXPECTED_RESULT_RE.search(oracle):
                findings.append(
                    {
                        "id": "prepared-non-observable-oracle",
                        "severity": "error",
                        "obligation_id": obligation.obligation_id,
                        "atom_id": obligation.traceability_atom_id,
                        "test_case_id": obligation.planned_test_case_id,
                        "oracle_sha256": sha256_text(oracle),
                    }
                )
        report: dict[str, Any] = {
            "passed": not findings,
            "validator": "prepared-observable-oracle-preflight-v1",
            "error_code": "" if not findings else "blocked-prepared-oracle-quality",
            "package_id": obligations.package_id,
            "atomic_obligations_sha256": sha256_file(obligation_path),
            "testable_obligations_checked": checked,
            "finding_count": len(findings),
            "affected_test_case_ids": list(
                dict.fromkeys(
                    str(item["test_case_id"])
                    for item in findings
                    if item.get("test_case_id")
                )
            ),
            "findings": findings,
        }
        report["preflight_digest"] = hashlib.sha256(
            json.dumps(
                report,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return report

    def _build_prepared_state_change_plan(self) -> dict[str, Any]:
        obligation_path = self._prepared_artifact("atomic-obligations")
        obligations = load_obligations(obligation_path)
        findings: list[dict[str, Any]] = []
        checked = 0
        for obligation in obligations.obligations:
            if obligation.coverage_status != "testable":
                continue
            semantic_text = " ".join(
                (
                    obligation.atomic_statement,
                    obligation.test_intent,
                    obligation.observable_oracle,
                )
            )
            likely_reset = bool(
                RESET_ACTION_RE.search(semantic_text)
                and CAPTURED_INITIAL_STATE_RE.search(semantic_text)
            )
            declared_reset = (
                obligation.execution_semantics == "reset-to-captured-initial"
            )
            if not likely_reset and not declared_reset:
                continue
            checked += 1
            if likely_reset and not declared_reset:
                findings.append(
                    {
                        "id": "prepared-state-change-classification-missing",
                        "severity": "error",
                        "obligation_id": obligation.obligation_id,
                        "atom_id": obligation.traceability_atom_id,
                        "test_case_id": obligation.planned_test_case_id,
                    }
                )
                continue
            state_change = obligation.state_change
            if state_change is None:
                findings.append(
                    {
                        "id": "prepared-state-change-contract-missing",
                        "severity": "error",
                        "obligation_id": obligation.obligation_id,
                        "atom_id": obligation.traceability_atom_id,
                        "test_case_id": obligation.planned_test_case_id,
                    }
                )
                continue
            if state_change.relation != "different-from-captured-initial":
                findings.append(
                    {
                        "id": "prepared-state-change-relation-invalid",
                        "severity": "error",
                        "obligation_id": obligation.obligation_id,
                        "atom_id": obligation.traceability_atom_id,
                        "test_case_id": obligation.planned_test_case_id,
                        "relation": state_change.relation,
                    }
                )
        report: dict[str, Any] = {
            "passed": not findings,
            "validator": "prepared-state-change-preflight-v1",
            "error_code": "" if not findings else "blocked-prepared-state-change-quality",
            "package_id": obligations.package_id,
            "atomic_obligations_sha256": sha256_file(obligation_path),
            "reset_obligations_checked": checked,
            "finding_count": len(findings),
            "affected_test_case_ids": list(
                dict.fromkeys(
                    str(item["test_case_id"])
                    for item in findings
                    if item.get("test_case_id")
                )
            ),
            "findings": findings,
        }
        report["preflight_digest"] = hashlib.sha256(
            json.dumps(
                report,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return report

    def _build_prepared_repair_plan(self) -> dict[str, Any]:
        if self.prepared_repair_draft_path is None or self.prepared_repair_findings_path is None:
            raise RunnerError("targeted repair requires both draft and findings inputs")
        for path, label in (
            (self.prepared_repair_draft_path, "repair draft"),
            (self.prepared_repair_findings_path, "repair findings"),
        ):
            if not path.is_file():
                raise RunnerError(f"Prepared {label} input does not exist: {path}")
            if not is_relative_to(path, self.ft_root):
                raise RunnerError(f"Prepared {label} input must be under the FT package")
            if is_relative_to(path, self.cycle_dir):
                raise RunnerError(f"Prepared {label} input must come from a prior immutable cycle")
        try:
            findings_payload = json.loads(
                self.prepared_repair_findings_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise RunnerError(f"Prepared repair findings are invalid JSON: {exc}") from exc
        raw_findings = findings_payload.get("findings")
        if not isinstance(raw_findings, list) or not raw_findings:
            raise RunnerError("Prepared repair findings must contain at least one finding")
        unsupported = sorted(
            {
                str(item.get("id", ""))
                for item in raw_findings
                if item.get("severity") == "error"
                and item.get("id") not in REPAIRABLE_QUALITY_FINDING_IDS
            }
        )
        if unsupported:
            raise RunnerError(
                "Prepared targeted repair does not support finding ids: "
                + ", ".join(unsupported)
            )
        finding_tc_ids = {
            str(test_case_id)
            for item in raw_findings
            if item.get("severity") == "error"
            and item.get("id") in REPAIRABLE_QUALITY_FINDING_IDS
            for test_case_id in (item.get("test_case_ids") or [])
        }
        groups = self._prepared_writer_groups()
        planned_ids = [test_case_id for test_case_id, _ in groups]
        target_ids = [test_case_id for test_case_id in planned_ids if test_case_id in finding_tc_ids]
        unknown_ids = sorted(finding_tc_ids - set(planned_ids))
        if unknown_ids:
            raise RunnerError(
                "Prepared repair findings reference unknown test cases: "
                + ", ".join(unknown_ids)
            )
        if not target_ids:
            raise RunnerError("Prepared targeted repair has no repairable test-case ids")
        if len(target_ids) > self.prepared_targeted_repair_max_test_cases:
            raise RunnerError(
                "blocked-prepared-targeted-repair-capacity: "
                f"target_count={len(target_ids)}, "
                f"limit={self.prepared_targeted_repair_max_test_cases}"
            )
        source_text = self.prepared_repair_draft_path.read_text(encoding="utf-8")
        spans = test_case_section_spans(source_text)
        actual_ids = [item[0] for item in spans]
        if actual_ids != planned_ids:
            raise RunnerError(
                "Prepared repair draft test-case set/order does not match the current package"
            )
        group_by_id = dict(groups)
        target_obligations = [
            obligation
            for test_case_id in target_ids
            for obligation in group_by_id[test_case_id]
        ]
        sections = [
            {
                "test_case_id": test_case_id,
                "sha256": sha256_text(section),
                "repair_target": test_case_id in finding_tc_ids,
            }
            for test_case_id, _, _, section in spans
        ]
        report: dict[str, Any] = {
            "passed": True,
            "validator": "prepared-targeted-repair-plan-v1",
            "package_id": self._prepared_package.package_id if self._prepared_package else "",
            "package_digest": self._prepared_package.package_digest if self._prepared_package else "",
            "source_draft": relative_path(self.prepared_repair_draft_path, self.repo_root),
            "source_draft_sha256": sha256_file(self.prepared_repair_draft_path),
            "source_findings": relative_path(self.prepared_repair_findings_path, self.repo_root),
            "source_findings_sha256": sha256_file(self.prepared_repair_findings_path),
            "full_test_case_count": len(planned_ids),
            "target_test_case_count": len(target_ids),
            "preserved_test_case_count": len(planned_ids) - len(target_ids),
            "target_test_case_ids": target_ids,
            "preserved_test_case_ids": [
                test_case_id for test_case_id in planned_ids if test_case_id not in finding_tc_ids
            ],
            "target_obligation_ids": [
                item.obligation_id for item in target_obligations
            ],
            "target_atom_ids": list(
                dict.fromkeys(item.traceability_atom_id for item in target_obligations)
            ),
            "allowed_finding_ids": sorted(REPAIRABLE_QUALITY_FINDING_IDS),
            "sections": sections,
        }
        report["plan_digest"] = hashlib.sha256(
            json.dumps(
                report,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return report

    def _repair_shard(self) -> dict[str, Any]:
        if not self._prepared_repair_plan.get("passed"):
            raise RunnerError("Prepared targeted repair plan is unavailable")
        return {
            "index": 1,
            "stage": WRITER_STAGE,
            "test_case_ids": list(self._prepared_repair_plan["target_test_case_ids"]),
            "obligation_ids": list(self._prepared_repair_plan["target_obligation_ids"]),
            "atom_ids": list(self._prepared_repair_plan["target_atom_ids"]),
            "digest": self._prepared_repair_plan["plan_digest"],
        }

    def _verify_repair_inputs(self) -> None:
        if not self._uses_targeted_prepared_repair():
            return
        assert self.prepared_repair_draft_path is not None
        assert self.prepared_repair_findings_path is not None
        if sha256_file(self.prepared_repair_draft_path) != self._prepared_repair_plan[
            "source_draft_sha256"
        ]:
            raise RunnerError("Prepared targeted repair source draft changed after preflight")
        if sha256_file(self.prepared_repair_findings_path) != self._prepared_repair_plan[
            "source_findings_sha256"
        ]:
            raise RunnerError("Prepared targeted repair findings changed after preflight")

    def _build_prepared_reviewer_rebind_plan(self) -> dict[str, Any]:
        path = self.prepared_reviewer_rebind_draft_path
        if path is None:
            raise RunnerError("prepared reviewer rebind requires a draft input")
        if not path.is_file():
            raise RunnerError(f"Prepared reviewer rebind draft does not exist: {path}")
        prior_cycles = self.ft_root / "work" / "review-cycles"
        if not is_relative_to(path, prior_cycles) or is_relative_to(path, self.cycle_dir):
            raise RunnerError(
                "Prepared reviewer rebind draft must come from a prior immutable review cycle"
            )
        source_text = path.read_text(encoding="utf-8")
        spans = test_case_section_spans(source_text)
        planned_ids = [test_case_id for test_case_id, _ in self._prepared_writer_groups()]
        actual_ids = [test_case_id for test_case_id, _, _, _ in spans]
        if actual_ids != planned_ids:
            raise RunnerError(
                "Prepared reviewer rebind draft test-case set/order does not match the current package"
            )
        sections: list[dict[str, Any]] = []
        source_package_ids: set[str] = set()
        for test_case_id, _, _, section in spans:
            package_ids = PACKAGE_ID_LINE_RE.findall(section)
            if len(package_ids) != 1:
                raise RunnerError(
                    "Prepared reviewer rebind source section must contain exactly one "
                    f"package_id: {test_case_id}"
                )
            source_package_ids.add(package_ids[0])
            normalized = PACKAGE_ID_LINE_RE.sub(
                "**package_id:** <PACKAGE_ID>", section, count=1
            )
            sections.append(
                {
                    "test_case_id": test_case_id,
                    "source_sha256": sha256_text(section),
                    "source_semantic_sha256": sha256_text(normalized),
                    "source_package_id": package_ids[0],
                }
            )
        report: dict[str, Any] = {
            "passed": True,
            "validator": "prepared-reviewer-rebind-plan-v1",
            "package_id": self._prepared_package.package_id if self._prepared_package else "",
            "package_digest": (
                self._prepared_package.package_digest if self._prepared_package else ""
            ),
            "source_draft": relative_path(path, self.repo_root),
            "source_draft_sha256": sha256_file(path),
            "source_package_ids": sorted(source_package_ids),
            "test_case_count": len(actual_ids),
            "test_case_ids": actual_ids,
            "sections": sections,
            "allowed_mutation": "per-test-case-package-id-only",
            "writer_llm_required": False,
        }
        report["plan_digest"] = hashlib.sha256(
            json.dumps(
                report,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return report

    def _verify_reviewer_rebind_input(self) -> None:
        if not self._uses_prepared_reviewer_rebind():
            return
        assert self.prepared_reviewer_rebind_draft_path is not None
        if sha256_file(self.prepared_reviewer_rebind_draft_path) != (
            self._prepared_reviewer_rebind_plan["source_draft_sha256"]
        ):
            raise RunnerError(
                "Prepared reviewer rebind source draft changed after preflight"
            )

    def _build_writer_output_capacity_plan(self) -> dict[str, Any]:
        groups = self._prepared_writer_groups()
        if self._prepared_repair_plan.get("passed"):
            target_ids = list(self._prepared_repair_plan["target_test_case_ids"])
            target_obligation_ids = list(
                self._prepared_repair_plan["target_obligation_ids"]
            )
            passed = len(target_ids) <= self.prepared_structured_writer_single_session_tc_limit
            return {
                "passed": passed,
                "validator": "prepared-structured-writer-output-capacity-v1",
                "error_code": ""
                if passed
                else "prepared-structured-writer-output-capacity-exceeded",
                "mode": "targeted-repair",
                "package_id": self._prepared_package.package_id if self._prepared_package else "",
                "atomic_obligations_sha256": sha256_file(
                    self._prepared_artifact("atomic-obligations")
                ),
                "test_case_count": len(target_ids),
                "full_test_case_count": len(groups),
                "obligation_count": len(target_obligation_ids),
                "single_session_test_case_limit": self.prepared_structured_writer_single_session_tc_limit,
                "configured_shard_size": self.prepared_structured_writer_shard_size,
                "max_shards": self.prepared_structured_writer_max_shards,
                "shard_count": 0,
                "union_complete": True,
                "disjoint": True,
                "full_seed_bytes": len(self._draft_seed_text().encode("utf-8")),
                "target_test_case_ids": target_ids,
                "plan_digest": self._prepared_repair_plan["plan_digest"],
                "shards": [],
            }
        obligation_count = sum(len(items) for _, items in groups)
        test_case_count = len(groups)
        limit = self.prepared_structured_writer_single_session_tc_limit
        shard_size = self.prepared_structured_writer_shard_size
        requires_sharding = test_case_count > limit
        shards: list[dict[str, Any]] = []
        if requires_sharding and shard_size > 0:
            for offset in range(0, test_case_count, shard_size):
                selected = groups[offset : offset + shard_size]
                test_case_ids = [test_case_id for test_case_id, _ in selected]
                selected_obligations = [item for _, items in selected for item in items]
                shard_payload = {
                    "index": len(shards) + 1,
                    "stage": (
                        WRITER_STAGE
                        if not shards
                        else f"{WRITER_STAGE}-shard-{len(shards) + 1:03d}"
                    ),
                    "test_case_ids": test_case_ids,
                    "obligation_ids": [item.obligation_id for item in selected_obligations],
                    "atom_ids": list(
                        dict.fromkeys(
                            item.traceability_atom_id for item in selected_obligations
                        )
                    ),
                }
                shard_payload["digest"] = hashlib.sha256(
                    json.dumps(
                        shard_payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()
                shards.append(shard_payload)
        shard_count = len(shards)
        planned_tc_ids = [test_case_id for test_case_id, _ in groups]
        planned_obligation_ids = [
            item.obligation_id for _, items in groups for item in items
        ]
        sharded_tc_ids = [
            test_case_id for shard in shards for test_case_id in shard["test_case_ids"]
        ]
        sharded_obligation_ids = [
            obligation_id for shard in shards for obligation_id in shard["obligation_ids"]
        ]
        union_complete = (
            not requires_sharding
            or (
                sharded_tc_ids == planned_tc_ids
                and sharded_obligation_ids == planned_obligation_ids
            )
        )
        disjoint = (
            len(sharded_tc_ids) == len(set(sharded_tc_ids))
            and len(sharded_obligation_ids) == len(set(sharded_obligation_ids))
        )
        passed = (
            not requires_sharding
            or (
                shard_size > 0
                and shard_size <= limit
                and shard_count <= self.prepared_structured_writer_max_shards
                and union_complete
                and disjoint
            )
        )
        report: dict[str, Any] = {
            "passed": passed,
            "validator": "prepared-structured-writer-output-capacity-v1",
            "error_code": "" if passed else "prepared-structured-writer-output-capacity-exceeded",
            "mode": "sharded" if requires_sharding and passed else "single-session",
            "package_id": self._prepared_package.package_id if self._prepared_package else "",
            "atomic_obligations_sha256": sha256_file(
                self._prepared_artifact("atomic-obligations")
            ),
            "test_case_count": test_case_count,
            "obligation_count": obligation_count,
            "single_session_test_case_limit": limit,
            "configured_shard_size": shard_size,
            "max_shards": self.prepared_structured_writer_max_shards,
            "shard_count": shard_count,
            "union_complete": union_complete,
            "disjoint": disjoint,
            "full_seed_bytes": len(self._draft_seed_text().encode("utf-8")),
            "shards": shards,
        }
        report["plan_digest"] = hashlib.sha256(
            json.dumps(
                report,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return report

    def _uses_sharded_prepared_writer(self) -> bool:
        return bool(
            self._uses_structured_prepared_writer()
            and not self._uses_prepared_reviewer_rebind()
            and self._writer_output_capacity_plan.get("passed")
            and self._writer_output_capacity_plan.get("mode") == "sharded"
        )

    def _build_reviewer_output_capacity_plan(self) -> dict[str, Any]:
        obligation_count = len(
            load_obligations(
                self._prepared_artifact("atomic-obligations")
            ).obligations
        )
        estimated_output_bytes = 2048 + obligation_count * 256
        schema_bytes = len(
            json.dumps(
                self._review_contract_schema(),
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        passed = (
            obligation_count <= self.prepared_structured_reviewer_obligation_limit
            and estimated_output_bytes <= MAX_ESTIMATED_STRUCTURED_REVIEWER_OUTPUT_BYTES
        )
        return {
            "passed": passed,
            "validator": "prepared-structured-reviewer-output-capacity-v1",
            "error_code": "" if passed else "prepared-structured-reviewer-output-capacity-exceeded",
            "obligation_count": obligation_count,
            "obligation_limit": self.prepared_structured_reviewer_obligation_limit,
            "estimated_output_bytes": estimated_output_bytes,
            "estimated_output_limit_bytes": MAX_ESTIMATED_STRUCTURED_REVIEWER_OUTPUT_BYTES,
            "output_schema_bytes": schema_bytes,
            "schema_mode": "generic-bounded-parser-verified"
            if self._uses_generic_bounded_reviewer_schema()
            else "exact-obligation-variants",
        }

    def _build_reviewer_context_capacity_plan(self) -> dict[str, Any]:
        shared_context_bytes = len(
            self._prepared_shared_context_projection().encode("utf-8")
        )
        semantic_projection_bytes = len(
            self._prepared_standard_reviewer_semantic_projection().encode("utf-8")
        )
        seed_bytes = len(self._draft_seed_text().encode("utf-8"))
        runtime_profile_bytes = self.prepared_reviewer_profile_path.stat().st_size
        rule_card_bytes = len(self._prepared_context_rule_card().encode("utf-8"))
        deterministic_payload_reserve_bytes = 16 * 1024
        estimated_primary_context_bytes = sum(
            (
                shared_context_bytes,
                semantic_projection_bytes,
                seed_bytes,
                runtime_profile_bytes * 2,
                rule_card_bytes,
                deterministic_payload_reserve_bytes,
            )
        )
        limit_bytes = self.prepared_standard_reviewer_context_max_bytes
        return {
            "passed": estimated_primary_context_bytes <= limit_bytes,
            "validator": "prepared-sharded-reviewer-context-capacity-v1",
            "error_code": ""
            if estimated_primary_context_bytes <= limit_bytes
            else "prepared-sharded-reviewer-context-capacity-exceeded",
            "estimate_basis": "full-seed-plus-semantic-projection-and-deterministic-reserve",
            "shared_context_bytes": shared_context_bytes,
            "semantic_projection_bytes": semantic_projection_bytes,
            "full_seed_bytes": seed_bytes,
            "runtime_profile_bytes_counted_twice": runtime_profile_bytes * 2,
            "rule_card_bytes": rule_card_bytes,
            "deterministic_payload_reserve_bytes": deterministic_payload_reserve_bytes,
            "estimated_primary_context_bytes": estimated_primary_context_bytes,
            "limit_bytes": limit_bytes,
        }

    def _prepared_context_profile(self) -> str:
        if self._prepared_package is None:
            return "legacy-standard"
        dimensions = set(self._prepared_package.unsupported_dimensions)
        if self._is_prepared_fast():
            return "simple-field-property"
        if dimensions & {
            "negative-oracle",
            "input-boundaries",
            "evidence-qualified-ui-calibration",
        }:
            return "character-restriction-calibration"
        if dimensions & {"numeric-boundaries", "date-boundaries", "numeric-or-date-boundaries"}:
            return "numeric-date-boundary"
        if any("integration" in item or "persistence" in item for item in dimensions):
            return "integration-persistence"
        if any("dependency" in item or "state" in item or "conditional" in item for item in dimensions):
            return "conditional-state"
        return "general-standard"

    def _prepared_role_instruction_paths(self, role: str) -> tuple[Path, ...]:
        if self._uses_compact_prepared_reviewer() and role == "reviewer":
            return (self.prepared_reviewer_profile_path,)
        if self._uses_structured_prepared_writer() and role == "writer":
            return (self.prepared_writer_profile_path,)
        return self._standard_instruction_paths(role)

    def _standard_instruction_paths(self, role: str) -> tuple[Path, ...]:
        cached = self._standard_instruction_contexts.get(role)
        if cached is not None:
            return cached

        scenario = self._standard_scenario(role)
        try:
            context = self.instruction_context_resolver(
                root=self.repo_root,
                scenario_id=scenario,
            )
        except (OSError, TypeError, ValueError) as exc:
            raise RunnerError(
                f"Instruction context resolver failed for {scenario}: {exc}"
            ) from exc

        if context.get("scenario") != scenario:
            raise RunnerError(
                "Instruction context resolver returned the wrong scenario: "
                f"expected {scenario}, got {context.get('scenario')}"
            )
        missing = tuple(str(item) for item in context.get("missing", ()))
        if missing:
            raise RunnerError(
                f"Instruction context for {scenario} has missing files: {', '.join(missing)}"
            )
        budget = context.get("budget", {})
        if budget.get("status") != "pass":
            raise RunnerError(
                f"Instruction context budget failed for {scenario}: "
                f"status={budget.get('status')}, total_kib={budget.get('total_kib')}, "
                f"limit_kib={budget.get('limit_kib')}"
            )

        resolved = [
            (self.repo_root / str(item["path"])).resolve()
            for item in context.get("files", ())
        ]
        configured = (
            self.writer_instruction_files
            if role == "writer"
            else self.reviewer_instruction_files
        )
        ordered: list[Path] = []
        seen: set[Path] = set()
        for path in (*self.instruction_files, *resolved, *configured):
            normalized = path.resolve()
            if normalized not in seen:
                seen.add(normalized)
                ordered.append(normalized)
        if not ordered:
            raise RunnerError(f"Instruction context for {scenario} resolved no files")
        result = tuple(ordered)
        self._standard_instruction_contexts[role] = result
        return result

    def _validate_standard_command_budgets(self) -> None:
        if self._is_prepared_standard() and self.prepared_standard_writer_mode == "structured":
            return
        prepared_input_count = 3 if self._is_prepared_standard() else 0
        writer_minimum = (
            len(self._standard_instruction_paths("writer"))
            + len(self.source_files)
            + len(self.handoff_files)
            + prepared_input_count
            + STANDARD_COMMAND_BUDGET_RESERVE
        )
        reviewer_minimum = (
            len(self._standard_instruction_paths("reviewer"))
            + len(self.source_files)
            + len(self.handoff_files)
            + prepared_input_count
            + 2  # validated draft and deterministic validator report
            + STANDARD_COMMAND_BUDGET_RESERVE
        )
        if self.writer_command_budget < writer_minimum:
            raise RunnerError(
                "Standard writer command budget is lower than its explicit input floor: "
                f"configured={self.writer_command_budget}, required>={writer_minimum}"
            )
        if self.reviewer_command_budget < reviewer_minimum:
            raise RunnerError(
                "Standard reviewer command budget is lower than its explicit input floor: "
                f"configured={self.reviewer_command_budget}, required>={reviewer_minimum}"
            )

    def validate_configuration(self) -> None:
        self.command_config.validate()
        if self.prepared_fast_writer_mode not in PREPARED_FAST_WRITER_MODES:
            raise RunnerError(
                "prepared_fast_writer_mode must be one of "
                f"{sorted(PREPARED_FAST_WRITER_MODES)}"
            )
        if self.prepared_standard_writer_mode not in PREPARED_STANDARD_WRITER_MODES:
            raise RunnerError(
                "prepared_standard_writer_mode must be one of "
                f"{sorted(PREPARED_STANDARD_WRITER_MODES)}"
            )
        if self.promote_final and self.promotion_dry_run:
            raise RunnerError("promotion and promotion dry-run are mutually exclusive")
        if self.promotion_dry_run and self.allow_overwrite_final:
            raise RunnerError("promotion dry-run never permits overwrite")
        if self.timeout_seconds < 1:
            raise RunnerError("timeout_seconds must be >= 1")
        for name in (
            "writer_idle_timeout_seconds",
            "reviewer_idle_timeout_seconds",
            "prepared_standard_reviewer_idle_timeout_seconds",
            "writer_command_budget",
            "reviewer_command_budget",
            "prepared_reviewer_command_budget",
            "writer_first_artifact_deadline_seconds",
            "prepared_reviewer_prompt_max_bytes",
            "prepared_standard_writer_context_max_bytes",
            "prepared_standard_reviewer_context_max_bytes",
            "prepared_structured_writer_single_session_tc_limit",
            "prepared_structured_writer_max_shards",
            "prepared_targeted_repair_max_test_cases",
            "prepared_structured_reviewer_obligation_limit",
        ):
            if getattr(self, name) < 1:
                raise RunnerError(f"{name} must be >= 1")
        if self.prepared_structured_writer_shard_size < 0:
            raise RunnerError("prepared_structured_writer_shard_size must be >= 0")
        for name in (
            "writer_timeout_seconds",
            "reviewer_timeout_seconds",
            "prepared_reviewer_timeout_seconds",
        ):
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
        if (self.prepared_repair_draft_path is None) != (
            self.prepared_repair_findings_path is None
        ):
            raise RunnerError(
                "targeted repair requires both --prepared-repair-draft and --prepared-repair-findings"
            )
        if self.prepared_repair_draft_path is not None and self.prepared_package_path is None:
            raise RunnerError("targeted repair is supported only for prepared routes")
        if (
            self.prepared_reviewer_rebind_draft_path is not None
            and self.prepared_package_path is None
        ):
            raise RunnerError("reviewer rebind is supported only for prepared routes")
        if (
            self.prepared_reviewer_rebind_draft_path is not None
            and self.prepared_repair_draft_path is not None
        ):
            raise RunnerError(
                "reviewer rebind and targeted repair are mutually exclusive"
            )
        if self.prepared_package_path is not None:
            if not self.command_config.output_schema_flag:
                raise RunnerError(
                    "Prepared reviewer requires a verified output-schema flag"
                )
            if self.source_files or self.handoff_files:
                raise RunnerError(
                    "Prepared routes must not mix raw source/handoff lists into the primary stage context"
                )
            if self.writer_instruction_files or self.reviewer_instruction_files:
                raise RunnerError(
                    "Prepared routes use runner-selected role instruction contexts"
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
            if self._prepared_package.package_version != PACKAGE_VERSION:
                dimensions = ", ".join(self._prepared_package.unsupported_dimensions) or "none"
                raise RunnerError(
                    "Prepared route requires the current package contract: "
                    f"package_version={self._prepared_package.package_version}, "
                    f"required_package_version={PACKAGE_VERSION}, "
                    f"profile={self._prepared_package.execution_profile}, "
                    f"unsupported_dimensions={dimensions}"
                )
            if self._is_prepared_fast() or self._uses_structured_prepared_writer():
                self._validate_prepared_runtime_profile(
                    self.prepared_writer_profile_path,
                    role="writer",
                )
            if self._uses_compact_prepared_reviewer():
                self._validate_prepared_runtime_profile(
                    self.prepared_reviewer_profile_path,
                    role="reviewer",
                )
            if self._is_prepared_fast() and self._prepared_package.unsupported_dimensions:
                raise RunnerError(
                    "Prepared fast path cannot declare unsupported dimensions"
                )
            if self._is_prepared_standard():
                if not self._prepared_package.unsupported_dimensions:
                    raise RunnerError(
                        "Prepared standard route requires explicit unsupported dimensions"
                    )
                declared_scenario = self._prepared_instruction_field("scenario")
                if declared_scenario != self._standard_scenario("writer"):
                    raise RunnerError(
                        "Prepared standard stage instructions must declare the standard writer scenario: "
                        f"declared={declared_scenario}, expected={self._standard_scenario('writer')}"
                    )
                self._prepared_role_instruction_paths("writer")
                self._prepared_role_instruction_paths("reviewer")
                self._validate_standard_command_budgets()
            elif not self._is_prepared_fast():
                dimensions = ", ".join(self._prepared_package.unsupported_dimensions) or "none"
                raise RunnerError(
                    "Prepared package execution profile is unsupported; route to standard writer: "
                    f"profile={self._prepared_package.execution_profile}, "
                    f"unsupported_dimensions={dimensions}"
                )
            self._validate_prepared_attempt_binding()
            self._prepared_oracle_quality_plan = (
                self._build_prepared_oracle_quality_plan()
            )
            if not self._prepared_oracle_quality_plan["passed"]:
                raise RunnerError(
                    "blocked-prepared-oracle-quality: "
                    f"finding_count={self._prepared_oracle_quality_plan['finding_count']}, "
                    "test_case_ids="
                    + ",".join(
                        self._prepared_oracle_quality_plan[
                            "affected_test_case_ids"
                        ]
                    )
                )
            self._prepared_state_change_plan = (
                self._build_prepared_state_change_plan()
            )
            if not self._prepared_state_change_plan["passed"]:
                raise RunnerError(
                    "blocked-prepared-state-change-quality: "
                    f"finding_count={self._prepared_state_change_plan['finding_count']}, "
                    "test_case_ids="
                    + ",".join(
                        self._prepared_state_change_plan[
                            "affected_test_case_ids"
                        ]
                    )
                )
            if self.prepared_repair_draft_path is not None:
                if not self._uses_structured_prepared_writer():
                    raise RunnerError(
                        "targeted repair requires a structured prepared writer"
                    )
                self._prepared_repair_plan = self._build_prepared_repair_plan()
            if self.prepared_reviewer_rebind_draft_path is not None:
                if not self._uses_structured_prepared_writer():
                    raise RunnerError(
                        "reviewer rebind requires a structured prepared route"
                    )
                self._prepared_reviewer_rebind_plan = (
                    self._build_prepared_reviewer_rebind_plan()
                )
        else:
            if not self.source_files:
                raise RunnerError("At least one explicit source file is required")
            if not self.handoff_files:
                raise RunnerError("At least one explicit handoff file is required")
            self._standard_instruction_paths("writer")
            self._standard_instruction_paths("reviewer")
            self._validate_standard_command_budgets()
        if self.promotion_contract_path is not None:
            if self.prepared_repair_draft_path is not None:
                raise RunnerError("targeted repair cannot be combined with promotion")
            if self.prepared_reviewer_rebind_draft_path is not None:
                raise RunnerError("reviewer rebind cannot be combined with promotion")
            if self._prepared_package is None:
                raise RunnerError("Promotion contract is supported only for prepared routes")
            if not is_relative_to(self.promotion_contract_path, self.ft_root):
                raise RunnerError("Promotion contract must be under the FT package")
            try:
                self._promotion_contract = PromotionContract.load(
                    self.promotion_contract_path, self.repo_root
                )
            except StageRuntimeError as exc:
                raise RunnerError(f"Promotion contract is invalid: {exc}") from exc
            contract = self._promotion_contract
            if contract.ft_slug != self._prepared_package.ft_slug:
                raise RunnerError("Promotion contract ft_slug does not match prepared package")
            if contract.scope_slug != self._prepared_package.scope_slug:
                raise RunnerError("Promotion contract scope_slug does not match prepared package")
            if contract.section_id != self._prepared_package.section_id:
                raise RunnerError("Promotion contract section_id does not match prepared package")
            if (self.repo_root / contract.canonical_test_cases).resolve() != self.final_path:
                raise RunnerError("Promotion contract canonical_test_cases does not match final artifact")
            obligations = load_obligations(self._prepared_artifact("atomic-obligations"))
            testable_count = sum(
                item.coverage_status == "testable" for item in obligations.obligations
            )
            if len(contract.test_case_ids) != testable_count:
                raise RunnerError(
                    "Promotion contract test_case_ids count does not match testable obligations"
                )
        elif self._prepared_package is not None and (self.promote_final or self.promotion_dry_run):
            raise RunnerError("Prepared promotion requires an explicit promotion contract")
        if self._uses_structured_prepared_writer():
            if not self._uses_prepared_reviewer_rebind():
                self._writer_output_capacity_plan = self._build_writer_output_capacity_plan()
                if not self._writer_output_capacity_plan["passed"]:
                    raise RunnerError(
                        "blocked-prepared-writer-output-capacity: "
                        f"test_case_count={self._writer_output_capacity_plan['test_case_count']}, "
                        f"single_session_limit={self.prepared_structured_writer_single_session_tc_limit}, "
                        f"shard_size={self.prepared_structured_writer_shard_size}, "
                        f"max_shards={self.prepared_structured_writer_max_shards}"
                    )
            self._reviewer_output_capacity_plan = (
                self._build_reviewer_output_capacity_plan()
            )
            if not self._reviewer_output_capacity_plan["passed"]:
                raise RunnerError(
                    "blocked-prepared-reviewer-output-capacity: "
                    f"obligation_count={self._reviewer_output_capacity_plan['obligation_count']}, "
                    f"obligation_limit={self.prepared_structured_reviewer_obligation_limit}, "
                    f"estimated_output_bytes={self._reviewer_output_capacity_plan['estimated_output_bytes']}"
                )
            if self._uses_generic_bounded_reviewer_schema() and self._is_prepared_standard():
                self._reviewer_context_capacity_plan = (
                    self._build_reviewer_context_capacity_plan()
                )
                if not self._reviewer_context_capacity_plan["passed"]:
                    raise RunnerError(
                        "blocked-prepared-reviewer-context-capacity: "
                        f"estimated_primary_context_bytes={self._reviewer_context_capacity_plan['estimated_primary_context_bytes']}, "
                        f"limit_bytes={self._reviewer_context_capacity_plan['limit_bytes']}"
                    )
        prepared_inputs = self._prepared_input_paths()
        instruction_inputs = (
            (
                *self._standard_instruction_paths("writer"),
                *self._standard_instruction_paths("reviewer"),
            )
            if self._prepared_package is None
            else (
                *self._prepared_role_instruction_paths("writer"),
                *self._prepared_role_instruction_paths("reviewer"),
            )
        )
        recovery_inputs = tuple(
            path
            for path in (
                self.prepared_reviewer_rebind_draft_path,
            )
            if path is not None
        )
        for input_path in (
            *instruction_inputs,
            *self.source_files,
            *self.handoff_files,
            *prepared_inputs,
            *recovery_inputs,
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
                "start a new immutable cycle instead of replaying stale outputs; prepared recovery "
                "must recompile a target-bound package for the new attempt: "
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

    def _prepared_instruction_field(self, field_name: str) -> str:
        instructions_path = self._prepared_artifact("stage-instructions")
        text = instructions_path.read_text(encoding="utf-8")
        matches = re.findall(
            rf"(?m)^- {re.escape(field_name)}: `([^`\r\n]+)`\s*$",
            text,
        )
        if len(matches) != 1:
            raise RunnerError(
                "Prepared stage instructions must declare exactly one "
                f"{field_name}: {relative_path(instructions_path, self.repo_root)}"
            )
        return matches[0].replace("\\", "/")

    def _prepared_instruction_int(self, field_name: str) -> int:
        raw = self._prepared_instruction_field(field_name)
        try:
            value = int(raw)
        except ValueError as exc:
            raise RunnerError(
                f"Prepared stage instruction {field_name} must be an integer"
            ) from exc
        if value < 1:
            raise RunnerError(
                f"Prepared stage instruction {field_name} must be positive"
            )
        return value

    def _validate_prepared_attempt_binding(self) -> None:
        expected_attempt = relative_path(self.attempt_root(WRITER_STAGE), self.repo_root)
        expected_output = relative_path(self.draft_path, self.repo_root)
        declared_attempt = self._prepared_instruction_field("attempt_root")
        declared_output = self._prepared_instruction_field("output_path")
        mismatches = []
        if declared_attempt != expected_attempt:
            mismatches.append(
                f"attempt_root declared={declared_attempt} expected={expected_attempt}"
            )
        if declared_output != expected_output:
            mismatches.append(
                f"output_path declared={declared_output} expected={expected_output}"
            )
        if mismatches:
            raise RunnerError(
                "Prepared stage package attempt binding mismatch; compile a new immutable "
                "package for the target cycle before launch: " + "; ".join(mismatches)
            )

    @property
    def prepared_writer_profile_path(self) -> Path:
        return self.repo_root / "references" / "agent" / "prepared-writer-runtime-profile.md"

    @property
    def prepared_reviewer_profile_path(self) -> Path:
        return self.repo_root / "references" / "agent" / "prepared-reviewer-runtime-profile.md"

    def _validate_prepared_runtime_profile(self, path: Path, *, role: str) -> None:
        if not path.is_file():
            raise RunnerError(f"Prepared {role} runtime profile is missing")
        profile = path.read_text(encoding="utf-8")
        hard_coded_versions = sorted(
            {match.group(1) for match in PACKAGE_VERSION_LITERAL_RE.finditer(profile)}
        )
        if hard_coded_versions:
            raise RunnerError(
                f"Prepared {role} runtime profile must not hard-code package version numbers; "
                f"PACKAGE_VERSION is runner-owned: found={','.join(hard_coded_versions)}"
            )
        if "`package_digest`" not in profile:
            raise RunnerError(
                f"Prepared {role} runtime profile must require runner-validated `package_digest`"
            )

    def _prepared_package_metadata(self) -> dict[str, Any]:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        package = self._prepared_package
        if package.package_version != PACKAGE_VERSION:
            raise RunnerError(
                "Prepared package metadata requires the current package contract: "
                f"package_version={package.package_version}, "
                f"required_package_version={PACKAGE_VERSION}"
            )
        if not SHA256_HEX_RE.fullmatch(package.package_digest):
            raise RunnerError("Prepared package metadata requires a valid package_digest")
        if not SHA256_HEX_RE.fullmatch(package.input_fingerprint):
            raise RunnerError("Prepared package metadata requires a valid input_fingerprint")
        return {
            "package_version": package.package_version,
            "package_id": package.package_id,
            "package_digest": package.package_digest,
            "input_fingerprint": package.input_fingerprint,
            "ft_slug": package.ft_slug,
            "scope_slug": package.scope_slug,
            "section_id": package.section_id,
            "execution_profile": package.execution_profile,
            "context_profile": self._prepared_context_profile(),
            "unsupported_dimensions": list(package.unsupported_dimensions),
        }

    def _prepared_standard_metadata(self, *, draft_sha256: str = "") -> dict[str, Any]:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        metadata: dict[str, Any] = {
            **self._prepared_package_metadata(),
            "writer_mode": self.prepared_standard_writer_mode,
            "draft_origin": (
                "runner-owned-reviewer-rebind"
                if self._uses_prepared_reviewer_rebind()
                else "writer-stage"
            ),
            "writer_llm_started": not self._uses_prepared_reviewer_rebind(),
            "fallback_policy": self._prepared_package.fallback_policy,
            "source_registry": [
                {
                    "path": item.path,
                    "role": item.role,
                    "locator": item.locator,
                    "sha256": item.sha256,
                }
                for item in self._prepared_package.source_registry
            ],
        }
        if draft_sha256:
            metadata["reviewed_draft_sha256"] = draft_sha256
        return metadata

    def _prepared_context_rule_card(self) -> str:
        profile = self._prepared_context_profile()
        rules = {
            "simple-field-property": (
                "Keep one observable field-property check per case and use only supplied fixtures.",
            ),
            "character-restriction-calibration": (
                "Keep each invalid class and field independent.",
                "Preserve every constraint_gap_ids marker. Independently preserve calibration_status=ui-calibration-required with ui-calibration-required and candidate-ui-calibration, even without a GAP.",
                "Do not choose a validation message, filtering, highlight, save or transition mechanism that the evidence does not define.",
            ),
            "numeric-date-boundary": (
                "Keep every supplied boundary point independent and preserve relative-date clock assumptions.",
                "Do not invent catalog limits, rounding or timezone behavior.",
            ),
            "integration-persistence": (
                "Separate trigger, observable response and persistence obligations.",
                "Treat a portable synthetic value or runtime-selected provider response with source-defined observable properties as a reproducible FT-first fixture.",
                "Do not require a stand record ID, locator, token, session or prerecorded provider response; return blocked-input only when the trigger or observable oracle cannot be derived without invention.",
            ),
            "conditional-state": (
                "Preserve branch preconditions and state transitions exactly as supplied.",
                "Do not infer inverse branches or persistence across transitions.",
            ),
            "general-standard": (
                "Apply the supplied obligation, fixture and oracle literally; do not broaden the scope.",
            ),
        }
        return "\n".join(
            [f"## Context profile: `{profile}`", "", *[f"- {item}" for item in rules[profile]]]
        )

    def _prepared_standard_writer_payload(self) -> str:
        lines = [
                "<!-- PREPARED-STANDARD-WRITER-PAYLOAD:BEGIN -->",
                "## Verified prepared-standard metadata",
                "",
                "```json",
                json.dumps(self._prepared_standard_metadata(), ensure_ascii=False, indent=2),
                "```",
                "",
                "## Selected source evidence",
                "",
                self._prepared_artifact("source-evidence").read_text(encoding="utf-8").strip(),
                "",
                "## Atomic obligations",
                "",
                "```json",
                self._prepared_artifact("atomic-obligations").read_text(encoding="utf-8").strip(),
                "```",
                "",
                "## Draft seed template (not an existing output file)",
                "",
                "Create the declared output as the first meaningful artifact. Replace every seed sentinel.",
                "",
                "```markdown",
                self._draft_seed_text().strip(),
                "```",
        ]
        if self._promotion_contract is not None:
            candidate = self.repo_root / self._promotion_contract.accepted_candidate
            lines.extend(
                [
                    "",
                    "## Promotion canonicalization contract",
                    "",
                    "The following accepted candidate is semantic baseline evidence, not requirement evidence. Preserve its accepted checks while converting the output to the exact canonical seed shape. Do not read its source path directly.",
                    "",
                    "```json",
                    json.dumps(
                        {
                            "canonical_test_cases": self._promotion_contract.canonical_test_cases,
                            "canonical_title": self._promotion_contract.canonical_title,
                            "domain_package_id": self._promotion_contract.domain_package_id,
                            "test_design_dir": self._promotion_contract.test_design_dir,
                            "test_case_ids": list(self._promotion_contract.test_case_ids),
                            "expected_priorities": dict(self._promotion_contract.expected_priorities),
                            "required_requirement_ids": list(self._promotion_contract.required_requirement_ids),
                            "accepted_candidate_sha256": self._promotion_contract.accepted_candidate_sha256,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    "```",
                    "",
                    "```markdown",
                    candidate.read_text(encoding="utf-8").strip(),
                    "```",
                ]
            )
        lines.append("<!-- PREPARED-STANDARD-WRITER-PAYLOAD:END -->")
        return "\n".join(lines)

    def _prepared_structured_obligation_transport(self) -> str:
        """Describe the verified obligation artifact without duplicating its full payload.

        Structured writers receive the source-backed obligation projection in
        source-evidence.md and the runner-generated test-case mapping in the draft
        seed.  Embedding atomic-obligations.json as well repeats the same semantic
        content and can make otherwise valid full-scope packages exceed the
        prepared-standard context budget.  The full artifact remains immutable and
        is consumed by the runner gates and reviewer.
        """
        artifact = self._prepared_artifact("atomic-obligations")
        obligations = load_obligations(artifact)
        status_counts: dict[str, int] = {}
        runner_owned_dictionary_materializations: list[dict[str, Any]] = []
        runner_owned_reference_fixtures: list[dict[str, Any]] = []
        for item in obligations.obligations:
            status_counts[item.coverage_status] = status_counts.get(item.coverage_status, 0) + 1
            for requirement in item.dictionary_requirements:
                if requirement.coverage_mode == "reference-only":
                    if requirement.fixture_values:
                        runner_owned_reference_fixtures.append(
                            {
                                "obligation_id": item.obligation_id,
                                "planned_test_case_id": item.planned_test_case_id,
                                "dictionary_id": requirement.dictionary_id,
                                "fixture_value_count": len(
                                    requirement.fixture_values
                                ),
                            }
                        )
                    continue
                runner_owned_dictionary_materializations.append(
                    {
                        "obligation_id": item.obligation_id,
                        "planned_test_case_id": item.planned_test_case_id,
                        "dictionary_id": requirement.dictionary_id,
                        "coverage_mode": requirement.coverage_mode,
                        "required_value_count": len(requirement.required_values),
                    }
                )
        return json.dumps(
            {
                "artifact": relative_path(artifact, self.repo_root),
                "artifact_sha256": sha256_file(artifact),
                "obligation_count": len(obligations.obligations),
                "coverage_status_counts": status_counts,
                "coverage_gap_count": len(obligations.coverage_gaps),
                "writer_semantics_source": "selected-source-evidence",
                "test_case_mapping_source": "runner-generated-draft-seed",
                "full_artifact_consumers": ["runner-gates", "reviewer"],
                "runner_owned_dictionary_materializations": (
                    runner_owned_dictionary_materializations
                ),
                "runner_owned_reference_fixtures": runner_owned_reference_fixtures,
            },
            ensure_ascii=False,
            indent=2,
        )

    def _prepared_standard_reviewer_obligation_index(self) -> str:
        """Return the exact reviewer contract index without repeated semantics."""
        artifact = self._prepared_artifact("atomic-obligations")
        obligations = load_obligations(artifact)
        items: list[dict[str, Any]] = []
        for item in obligations.obligations:
            entry: dict[str, Any] = {
                "obligation_id": item.obligation_id,
                "atom_id": item.traceability_atom_id,
                "coverage_status": item.coverage_status,
                "source_refs": list(item.source_refs),
            }
            if item.planned_test_case_id:
                entry["planned_test_case_id"] = item.planned_test_case_id
            if item.dictionary_refs:
                entry["dictionary_refs"] = list(item.dictionary_refs)
                entry["dictionary_requirements"] = [
                    {
                        "dictionary_id": requirement.dictionary_id,
                        "coverage_mode": requirement.coverage_mode,
                        "required_value_count": len(requirement.required_values),
                        "fixture_value_count": len(requirement.fixture_values),
                    }
                    for requirement in item.dictionary_requirements
                ]
            if item.gap_id:
                entry["gap_id"] = item.gap_id
            if item.constraint_gap_ids:
                entry["constraint_gap_ids"] = list(item.constraint_gap_ids)
            if item.calibration_status != "none":
                entry["calibration_status"] = item.calibration_status
            if item.execution_semantics != "direct":
                entry["execution_semantics"] = item.execution_semantics
            items.append(entry)
        return json.dumps(
            {
                "artifact": relative_path(artifact, self.repo_root),
                "artifact_sha256": sha256_file(artifact),
                "obligation_count": len(items),
                "coverage_gap_ids": [gap.gap_id for gap in obligations.coverage_gaps],
                "semantic_evidence_source": "selected-source-evidence",
                "obligations": items,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _prepared_standard_reviewer_semantic_projection(self) -> str:
        artifact = self._prepared_artifact("atomic-obligations")
        obligations = load_obligations(artifact)
        return json.dumps(
            {
                "artifact": relative_path(artifact, self.repo_root),
                "artifact_sha256": sha256_file(artifact),
                "obligation_count": len(obligations.obligations),
                "semantic_evidence_source": "selected-source-evidence",
                "coverage_gaps": [item.to_dict() for item in obligations.coverage_gaps],
                "dictionary_evidence": self._prepared_dictionary_evidence_projection(
                    obligations.obligations
                ),
                "obligations": [
                    {
                        "obligation_id": item.obligation_id,
                        "atom_id": item.traceability_atom_id,
                        "coverage_status": item.coverage_status,
                        "planned_test_case_id": item.planned_test_case_id,
                        "source_refs": list(item.source_refs),
                        "atomic_statement": item.atomic_statement,
                        "observable_oracle": item.observable_oracle,
                        "test_intent": item.test_intent,
                        "execution_semantics": item.execution_semantics,
                        "state_change": (
                            item.state_change.to_dict()
                            if item.state_change is not None
                            else None
                        ),
                        "dictionary_refs": list(item.dictionary_refs),
                        "gap_id": item.gap_id,
                        "constraint_gap_ids": list(item.constraint_gap_ids),
                    }
                    for item in obligations.obligations
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _prepared_dictionary_evidence_projection(
        self, obligations: Sequence[Any]
    ) -> list[dict[str, Any]]:
        referenced_ids = sorted(
            {
                dictionary_id
                for obligation in obligations
                for dictionary_id in obligation.dictionary_refs
            }
        )
        if not referenced_ids:
            return []
        evidence = self._prepared_artifact("source-evidence").read_text(encoding="utf-8")
        blocks: dict[str, str] = {}
        headings = list(
            re.finditer(r"(?m)^##\s+(DICT-[A-Za-z0-9._-]+)\s*$", evidence)
        )
        for index, match in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(evidence)
            blocks[match.group(1)] = evidence[match.end() : end].strip()
        projection: list[dict[str, Any]] = []
        columns = (
            "dictionary_id",
            "dictionary_name",
            "source_file",
            "source_location",
            "extraction_status",
            "active_values",
            "archived_values",
            "used_by_source_properties",
            "gap_id",
            "notes",
        )
        for dictionary_id in referenced_ids:
            block = blocks.get(dictionary_id, "")
            structured_match = re.search(
                r"```json\s*(\{.*?\})\s*```", block, flags=re.DOTALL
            )
            if structured_match is not None:
                try:
                    structured = json.loads(structured_match.group(1))
                except json.JSONDecodeError as exc:
                    raise RunnerError(
                        "Prepared dictionary evidence is missing or malformed: "
                        + dictionary_id
                    ) from exc
                if (
                    not isinstance(structured, dict)
                    or structured.get("dictionary_id") != dictionary_id
                ):
                    raise RunnerError(
                        "Prepared dictionary evidence is missing or malformed: "
                        + dictionary_id
                    )
                record = {
                    column: str(structured.get(column, "")) for column in columns
                }
                raw_active_values = structured.get("active_values")
                active_values = (
                    [value.strip() for value in raw_active_values]
                    if isinstance(raw_active_values, list)
                    and all(isinstance(value, str) for value in raw_active_values)
                    else []
                )
            else:
                # Compatibility only for immutable packages compiled before the
                # structured dictionary projection.  Canonical new packages use
                # the JSON record above and are never reparsed from Markdown.
                row = next(
                    (line.strip() for line in block.splitlines() if line.strip()),
                    "",
                )
                values = [value.strip() for value in row.split(" | ")]
                if len(values) != len(columns) or values[0].strip("`") != dictionary_id:
                    raise RunnerError(
                        "Prepared dictionary evidence is missing or malformed: "
                        + dictionary_id
                    )
                record = dict(zip(columns, values, strict=True))
                legacy_parts = re.split(r"\s*;\s*", record["active_values"].strip())
                active_values = []
                if legacy_parts and all(item.strip() for item in legacy_parts):
                    for raw in legacy_parts:
                        value = raw.strip().strip("`").strip()
                        if (
                            not value
                            or "`" in value
                            or not any(character.isalnum() for character in value)
                        ):
                            active_values = []
                            break
                        active_values.append(value)
            if (
                not active_values
                or len(active_values) != len(set(active_values))
                or any(
                    not value or not any(character.isalnum() for character in value)
                    for value in active_values
                )
            ):
                raise RunnerError(
                    "Prepared dictionary evidence has no valid active values: "
                    + dictionary_id
                )
            projection.append(
                {
                    "dictionary_id": dictionary_id,
                    "dictionary_name": record["dictionary_name"].strip("`"),
                    "source_file": record["source_file"].strip("`"),
                    "source_location": record["source_location"].strip("`"),
                    "extraction_status": record["extraction_status"].strip("`"),
                    "active_values": active_values,
                    "archived_values": record["archived_values"].strip("`"),
                }
            )
        return projection

    def _prepared_shared_context_projection(self) -> str:
        evidence = self._prepared_artifact("source-evidence").read_text(encoding="utf-8")
        first_obligation = re.search(r"(?m)^- OBL-[A-Za-z0-9_.-]+:", evidence)
        if first_obligation is None:
            return evidence.strip()
        return evidence[: first_obligation.start()].rstrip()

    def _prepared_writer_source_evidence(
        self,
        evidence: str | None = None,
        *,
        record_report: bool = False,
    ) -> str:
        """Keep dictionary identity in writer context without repeating leaf payloads."""

        source = evidence
        if source is None:
            source = self._prepared_artifact("source-evidence").read_text(
                encoding="utf-8"
            )
        headings = list(
            re.finditer(r"(?m)^##\s+(DICT-[A-Za-z0-9._-]+)\s*$", source)
        )
        if not headings:
            projected = source.strip()
            report = {
                "validator": "prepared-writer-dictionary-context-v1",
                "dictionary_sections_seen": 0,
                "dictionary_sections_compacted": 0,
                "original_bytes": len(source.encode("utf-8")),
                "projected_bytes": len(projected.encode("utf-8")),
                "bytes_removed": len(source.encode("utf-8"))
                - len(projected.encode("utf-8")),
            }
            if record_report:
                self._writer_dictionary_context_report = report
            return projected

        parts: list[str] = []
        cursor = 0
        compacted = 0
        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(source)
            parts.append(source[cursor : heading.start()])
            block = source[heading.end() : end]
            structured_match = re.search(
                r"```json\s*(\{.*?\})\s*```", block, flags=re.DOTALL
            )
            if structured_match is None:
                parts.append(source[heading.start() : end])
                cursor = end
                continue
            try:
                structured = json.loads(structured_match.group(1))
            except json.JSONDecodeError:
                parts.append(source[heading.start() : end])
                cursor = end
                continue
            dictionary_id = heading.group(1)
            active_values = structured.get("active_values")
            if (
                not isinstance(structured, dict)
                or structured.get("dictionary_id") != dictionary_id
                or not isinstance(active_values, list)
                or not all(isinstance(value, str) for value in active_values)
            ):
                parts.append(source[heading.start() : end])
                cursor = end
                continue
            summary = {
                "dictionary_id": dictionary_id,
                "dictionary_name": str(structured.get("dictionary_name") or ""),
                "source_file": str(structured.get("source_file") or ""),
                "source_location": str(structured.get("source_location") or ""),
                "extraction_status": str(structured.get("extraction_status") or ""),
                "active_value_count": len(active_values),
                "active_dictionary_ids": [
                    value
                    for value in active_values
                    if re.fullmatch(r"DICT-[A-Za-z0-9._-]+", value)
                ],
                "exact_value_transport": (
                    "omitted-from-writer-context; runner-gates-and-reviewer-use-immutable-evidence"
                ),
            }
            parts.extend(
                [
                    f"## {dictionary_id}\n\n",
                    "```json\n",
                    json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
                    "\n```\n\n",
                ]
            )
            compacted += 1
            cursor = end
        parts.append(source[cursor:])
        projected = "".join(parts).strip()
        original_bytes = len(source.encode("utf-8"))
        projected_bytes = len(projected.encode("utf-8"))
        report = {
            "validator": "prepared-writer-dictionary-context-v1",
            "dictionary_sections_seen": len(headings),
            "dictionary_sections_compacted": compacted,
            "original_bytes": original_bytes,
            "projected_bytes": projected_bytes,
            "bytes_removed": original_bytes - projected_bytes,
        }
        if record_report:
            self._writer_dictionary_context_report = report
        return projected

    def _prepared_standard_reviewer_calibration_summary(self) -> str:
        artifact = self.calibration_lifecycle_path
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        items = payload.get("items") or []
        status_counts: dict[str, int] = {}
        gap_ids: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "unspecified")
            status_counts[status] = status_counts.get(status, 0) + 1
            for gap_id in item.get("constraint_gap_ids") or []:
                if isinstance(gap_id, str) and gap_id not in gap_ids:
                    gap_ids.append(gap_id)
        return json.dumps(
            {
                "artifact": relative_path(artifact, self.repo_root),
                "artifact_sha256": sha256_file(artifact),
                "context_profile": payload.get("context_profile"),
                "open_count": payload.get("open_count"),
                "resolved_count": payload.get("resolved_count"),
                "status_counts": status_counts,
                "constraint_gap_ids": gap_ids,
                "per_obligation_mapping_source": "verified-obligation-review-index",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _prepared_standard_reviewer_payload(self) -> str:
        draft_sha256 = sha256_file(self.draft_path)
        gates = [
            self._prepared_gate_summary("structure", self.validator_path),
            self._prepared_gate_summary("seed", self.seed_gate_path),
            self._prepared_gate_summary("obligation", self.obligation_gate_path),
            self._prepared_gate_summary("semantic-overlap", self.semantic_overlap_path),
            self._prepared_gate_summary("writer-evidence-access", self.evidence_access_path),
            self._prepared_gate_summary("quality-bundle", self.quality_gate_bundle_path),
        ]
        if self.package_metadata_gate_path.is_file():
            gates.append(
                self._prepared_gate_summary(
                    "package-metadata", self.package_metadata_gate_path
                )
            )
        if self._promotion_contract is not None:
            gates.append(
                self._prepared_gate_summary("promotion-readiness", self.promotion_readiness_path)
            )
        return "\n".join(
            [
                "<!-- PREPARED-STANDARD-REVIEW-PAYLOAD:BEGIN -->",
                "## Verified prepared-standard review metadata",
                "",
                "```json",
                json.dumps(
                    self._prepared_standard_metadata(draft_sha256=draft_sha256),
                    ensure_ascii=False,
                    indent=2,
                ),
                "```",
                "",
                "## Selected source evidence",
                "",
                self._prepared_artifact("source-evidence").read_text(encoding="utf-8").strip(),
                "",
                "## Atomic obligations",
                "",
                "```json",
                self._prepared_artifact("atomic-obligations").read_text(encoding="utf-8").strip(),
                "```",
                "",
                "## Deterministic gate summaries",
                "",
                "```json",
                json.dumps(gates, ensure_ascii=False, indent=2),
                "```",
                "",
                "## Semantic overlap diagnostic (non-blocking, reviewer classification required)",
                "",
                "```json",
                self.semantic_overlap_path.read_text(encoding="utf-8").strip(),
                "```",
                "",
                "## Calibration lifecycle",
                "",
                "```json",
                self.calibration_lifecycle_path.read_text(encoding="utf-8").strip(),
                "```",
                "",
                "## Immutable writer draft",
                "",
                "```markdown",
                self.draft_path.read_text(encoding="utf-8").strip(),
                "```",
                "",
                "## Required final contract",
                "",
                "Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation, structured findings and a non-empty summary. Do not emit commentary outside the final JSON object.",
                "Verdict compatibility is strict: testable obligations use covered, missing or incorrect; gap/unclear obligations use gap-preserved or invented-coverage. Preserve non-blocking constraint gaps in the note without changing a testable obligation to gap-preserved.",
                "For every gap/unclear obligation, test_case_ids must be an empty array. Put its GAP-* identifier in note; GAP-* is not a test-case id.",
                "<!-- PREPARED-STANDARD-REVIEW-PAYLOAD:END -->",
            ]
        )

    def _enforce_prepared_standard_context_budget(
        self,
        *,
        role: str,
        prompt: str,
        stage: str | None = None,
    ) -> None:
        instruction_paths = self._prepared_role_instruction_paths(role)
        instruction_bytes = sum(path.stat().st_size for path in instruction_paths)
        prompt_bytes = len(prompt.encode("utf-8"))
        total_bytes = prompt_bytes + instruction_bytes
        limit_bytes = (
            self.prepared_standard_writer_context_max_bytes
            if role == "writer"
            else self.prepared_standard_reviewer_context_max_bytes
        )
        stage = stage or (WRITER_STAGE if role == "writer" else REVIEWER_STAGE)
        report = {
            "passed": total_bytes <= limit_bytes,
            "validator": "prepared-standard-context-budget-v1",
            "error_code": "" if total_bytes <= limit_bytes else "prepared-standard-context-budget-exceeded",
            "role": role,
            "scenario": self._standard_scenario(role),
            "prompt_bytes": prompt_bytes,
            "instruction_bytes": instruction_bytes,
            "primary_context_bytes": total_bytes,
            "limit_bytes": limit_bytes,
            "instruction_artifact_count": len(instruction_paths),
        }
        if role == "writer" and self._writer_dictionary_context_report:
            report["dictionary_context_projection"] = dict(
                self._writer_dictionary_context_report
            )
        self._context_budget_reports[stage] = report
        if not report["passed"]:
            raise RunnerError(
                "blocked-prepared-standard-context-budget: "
                f"role={role}, primary_context_bytes={total_bytes}, limit_bytes={limit_bytes}"
            )

    def _prepared_writer_payload(self, *, structured: bool = False) -> str:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        if not self.prepared_writer_profile_path.is_file():
            raise RunnerError("Prepared writer runtime profile is missing")
        profile = self.prepared_writer_profile_path.read_text(encoding="utf-8").strip()
        metadata = {
            **self._prepared_package_metadata(),
            "fallback_policy": self._prepared_package.fallback_policy,
        }
        lines = [
            "<!-- PREPARED-STAGE-PAYLOAD:BEGIN -->",
            "## Verified package metadata",
            "",
            "```json",
            json.dumps(metadata, ensure_ascii=False, indent=2),
            "```",
            "",
            profile,
            "",
            self._prepared_context_rule_card(),
            "",
        ]
        if not structured:
            lines.extend(
                [
                self._prepared_artifact("stage-instructions").read_text(encoding="utf-8").strip(),
                "",
                ]
            )
        lines.extend(
            [
                self._prepared_writer_source_evidence(
                    record_report=structured
                ),
                "",
            ]
        )
        if structured:
            lines.extend(
                [
                    "## Verified obligation transport",
                    "",
                    "The full atomic-obligations artifact is intentionally not repeated here. "
                    "Its source-backed semantics are present above, its exact test-case mapping "
                    "is present in the draft seed below, and the runner gates plus reviewer consume "
                    "the immutable full artifact.",
                    "",
                    "```json",
                    self._prepared_structured_obligation_transport(),
                    "```",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "## Atomic obligations",
                    "",
                    "```json",
                    self._prepared_artifact("atomic-obligations").read_text(encoding="utf-8").strip(),
                    "```",
                    "",
                ]
            )
        lines.extend(
            [
                "## Draft seed template (not an existing output file)",
                "",
            ]
        )
        if structured:
            lines.extend(
                [
                    "Return a complete draft based on this template; the runner writes it after validating the JSON contract.",
                    "Do not copy seed sentinels or placeholders into draft_markdown.",
                ]
            )
        else:
            lines.extend(
                [
                    "The declared output file does not exist at stage start. Create it as the first file write.",
                    "Use `Add File` or an equivalent atomic create; do not use an update-only patch against the absent output.",
                    "Use this inline seed only as a template and remove every seed sentinel in the created draft.",
                ]
            )
        lines.extend(
            [
                "",
                "```markdown",
                self._draft_seed_text().strip(),
                "```",
                "<!-- PREPARED-STAGE-PAYLOAD:END -->",
            ]
        )
        return "\n".join(lines)

    def _prepared_writer_shard_projection(self, shard: dict[str, Any]) -> str:
        obligation_set = load_obligations(self._prepared_artifact("atomic-obligations"))
        selected_ids = set(shard["obligation_ids"])
        selected = [
            item for item in obligation_set.obligations if item.obligation_id in selected_ids
        ]
        if {item.obligation_id for item in selected} != selected_ids:
            raise RunnerError("writer shard plan references unknown obligations")
        relevant_gap_ids = {
            gap_id
            for item in selected
            for gap_id in (item.gap_id, *item.constraint_gap_ids)
            if gap_id
        }
        gaps = [
            item.to_dict()
            for item in obligation_set.coverage_gaps
            if item.gap_id in relevant_gap_ids
        ]
        payload = {
            "package_version": obligation_set.package_version,
            "package_id": obligation_set.package_id,
            "source_artifact_sha256": sha256_file(
                self._prepared_artifact("atomic-obligations")
            ),
            "shard_digest": shard["digest"],
            "test_case_ids": list(shard["test_case_ids"]),
            "obligations": [
                item.to_dict(include_constraints=True, include_atom_id=True)
                for item in selected
            ],
            "coverage_gaps": gaps,
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    def _prepared_writer_shard_evidence(self, shard: dict[str, Any]) -> str:
        evidence = self._prepared_artifact("source-evidence").read_text(encoding="utf-8")
        first_obligation = re.search(r"(?m)^- OBL-[A-Za-z0-9_.-]+:", evidence)
        if first_obligation is None:
            return evidence.strip()
        shared = evidence[: first_obligation.start()].rstrip()
        selectors = set(shard["obligation_ids"]) | set(shard["test_case_ids"])
        obligation_set = load_obligations(self._prepared_artifact("atomic-obligations"))
        for item in obligation_set.obligations:
            if item.obligation_id not in selectors:
                continue
            selectors.update(item.dictionary_refs)
            selectors.update(item.constraint_gap_ids)
            if item.gap_id:
                selectors.add(item.gap_id)
        blocks = re.split(r"\n\s*\n", evidence[first_obligation.start() :].strip())
        selected_blocks = [block for block in blocks if any(value in block for value in selectors)]
        selected = "\n\n".join((shared, *selected_blocks)).strip()
        return self._prepared_writer_source_evidence(selected)

    def _writer_shard_prompt(self, shard: dict[str, Any]) -> str:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        stage = str(shard["stage"])
        prompt = "\n".join(
            [
                "# Codex exec prepared writer bounded shard",
                "",
                "This is one read-only shard of a runner-owned deterministic full-set plan.",
                "Use only the embedded runtime profile, selected evidence and exact obligation projection below.",
                "Do not call shell or file tools and do not create or modify workspace files.",
                "Return only the assigned `## TC-*` sections in the declared order. Do not add an H1 title, metadata, coverage summary or unassigned test case.",
                "Every assigned obligation_id and atom_id must appear in the traceability of its planned test case.",
                "Do not read previous cycles, generated drafts, production test cases or full sources.",
                "FT-first fixtures may be portable synthetic values, relative dates or runtime-selected integration responses with source-defined observable properties.",
                "Return blocked-input only when this shard's embedded evidence cannot define the test intent or observable oracle without invention.",
                "",
                self.prepared_writer_profile_path.read_text(encoding="utf-8").strip(),
                "",
                self._prepared_context_rule_card(),
                "",
                "## Verified shard metadata",
                "",
                "```json",
                json.dumps(
                    {
                        "package_id": self._prepared_package.package_id,
                        "stage": stage,
                        "shard_index": shard["index"],
                        "shard_count": self._writer_output_capacity_plan["shard_count"],
                        "shard_digest": shard["digest"],
                        "test_case_count": len(shard["test_case_ids"]),
                        "obligation_count": len(shard["obligation_ids"]),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "```",
                "",
                "## Selected source-backed evidence",
                "",
                self._prepared_writer_shard_evidence(shard),
                "",
                "## Exact shard obligation projection",
                "",
                "```json",
                self._prepared_writer_shard_projection(shard),
                "```",
                "",
                "## Shard draft seed",
                "",
                "Replace every seed placeholder. Return these sections only.",
                "",
                "```markdown",
                self._draft_seed_text(
                    test_case_ids=shard["test_case_ids"],
                    include_document_header=False,
                ).strip(),
                "```",
                "",
                "Return exactly one schema-constrained JSON object and no commentary outside it.",
                "Use status=draft-ready with the complete shard in draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one reason.",
                "",
            ]
        )
        if self._is_prepared_standard():
            self._enforce_prepared_standard_context_budget(
                role="writer", prompt=prompt, stage=stage
            )
        return prompt

    def _targeted_repair_input_sections(self) -> str:
        if not self._uses_targeted_prepared_repair():
            raise RunnerError("Prepared targeted repair is not active")
        assert self.prepared_repair_draft_path is not None
        target_ids = set(self._prepared_repair_plan["target_test_case_ids"])
        sections = [
            section.rstrip()
            for test_case_id, _, _, section in test_case_section_spans(
                self.prepared_repair_draft_path.read_text(encoding="utf-8")
            )
            if test_case_id in target_ids
        ]
        if len(sections) != len(target_ids):
            raise RunnerError("Prepared targeted repair source sections are incomplete")
        return "\n\n".join(sections)

    def _targeted_repair_prompt(self) -> str:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        shard = self._repair_shard()
        prompt = "\n".join(
            [
                "# Codex exec prepared writer targeted repair",
                "",
                "This is one fresh read-only repair session over a runner-owned hash-bound plan.",
                "Use only the selected source-backed evidence and obligation projection as requirement evidence.",
                "The prior generated sections below are unsigned repair input only; do not treat their wording as requirements.",
                "Do not call shell or file tools and do not create or modify workspace files.",
                "Return exactly the assigned `## TC-*` replacement sections in the declared order. Do not add an H1 or any unassigned test case.",
                "Preserve exact assigned OBL/ATOM traceability and coverage-gap lifecycle markers.",
                "Every final expected result must be observable. For a calibration candidate, define the evidence record produced by the exact action, input value, visible state and outcome without inventing a message, highlight, filtering mechanism, blocked save or transition.",
                "For a positive permitted-value check, state the exact visible field value; do not append that the UI reaction is undefined or deferred.",
                "Return blocked-input only when the selected evidence still cannot define an executable ordinary oracle or calibration evidence record without invention.",
                "",
                self.prepared_writer_profile_path.read_text(encoding="utf-8").strip(),
                "",
                self._prepared_context_rule_card(),
                "",
                "## Verified repair metadata",
                "",
                "```json",
                json.dumps(
                    {
                        "package_id": self._prepared_package.package_id,
                        "plan_digest": self._prepared_repair_plan["plan_digest"],
                        "source_draft_sha256": self._prepared_repair_plan[
                            "source_draft_sha256"
                        ],
                        "source_findings_sha256": self._prepared_repair_plan[
                            "source_findings_sha256"
                        ],
                        "target_test_case_ids": self._prepared_repair_plan[
                            "target_test_case_ids"
                        ],
                        "preserved_test_case_count": self._prepared_repair_plan[
                            "preserved_test_case_count"
                        ],
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "```",
                "",
                "## Selected source-backed evidence",
                "",
                self._prepared_writer_shard_evidence(shard),
                "",
                "## Exact repair obligation projection",
                "",
                "```json",
                self._prepared_writer_shard_projection(shard),
                "```",
                "",
                "## Prior unsigned sections to replace",
                "",
                "```markdown",
                self._targeted_repair_input_sections(),
                "```",
                "",
                "## Corrected source-backed repair seed",
                "",
                "Replace every seed placeholder and return these sections only.",
                "",
                "```markdown",
                self._draft_seed_text(
                    test_case_ids=shard["test_case_ids"],
                    include_document_header=False,
                ).strip(),
                "```",
                "",
                "Return exactly one schema-constrained JSON object and no commentary outside it.",
                "Use status=draft-ready with all replacement sections in draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one reason.",
                "",
            ]
        )
        if self._is_prepared_standard():
            self._enforce_prepared_standard_context_budget(
                role="writer", prompt=prompt, stage=WRITER_STAGE
            )
        return prompt

    def _draft_seed_text(
        self,
        *,
        test_case_ids: Sequence[str] | None = None,
        include_document_header: bool = True,
    ) -> str:
        grouped_testable = self._prepared_writer_groups()
        selected_ids = set(test_case_ids or ())
        if test_case_ids is not None:
            grouped_testable = [
                item for item in grouped_testable if item[0] in selected_ids
            ]
            actual_ids = {item[0] for item in grouped_testable}
            if actual_ids != selected_ids:
                raise RunnerError(
                    "writer shard seed references unknown test-case ids: "
                    + ", ".join(sorted(selected_ids - actual_ids))
                )
        testable = [item for _, group in self._prepared_writer_groups() for item in group]
        contract = self._promotion_contract
        if contract is not None and test_case_ids is not None:
            raise RunnerError("promotion contract does not support writer sharding")
        if contract is not None and len(grouped_testable) != len(testable):
            raise RunnerError(
                "promotion contract does not support grouped prepared obligations"
            )
        if contract is None and include_document_header:
            lines = [
                "# Тест-кейсы", "",
                f"<!-- {SEED_MARKER}: replace all [SEED:*] values before completion -->", "",
            ]
        elif contract is None:
            lines = []
        else:
            lines = [
                f"# {contract.canonical_title}", "",
                f"<!-- {SEED_MARKER}: replace all [SEED:*] values before completion -->", "",
                "## Metadata", "",
                "| field | value |", "| --- | --- |",
                f"| ft_slug | `{contract.ft_slug}` |",
                f"| scope_slug | `{contract.scope_slug}` |",
                f"| section_id | `{contract.section_id}` |",
                f"| package_id | `{contract.domain_package_id}` |",
                f"| test_design_dir | `{contract.test_design_dir}` |", "",
                "## Scope Boundaries", "", "[SEED:scope boundaries]", "",
                "## Coverage Summary", "",
                "| package_id | source_row_id | req_id | obligation_id | atom_id | test_case_id | coverage_status |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
            for tc_id, obligation in zip(contract.test_case_ids, testable, strict=True):
                source_row_id = next(
                    (value for value in obligation.source_refs if value.startswith("SRC-")), "n/a"
                )
                req_id = next(
                    (value for value in obligation.source_refs if re.fullmatch(r"(?:BSR|GSR|DIT)\s+\d+(?:\.\d+)*", value)),
                    "n/a",
                )
                lines.append(
                    f"| `{contract.domain_package_id}` | `{source_row_id}` | `{req_id}` | "
                    f"`{obligation.obligation_id}` | `{obligation.traceability_atom_id}` | "
                    f"`{tc_id}` | `covered` |"
                )
            lines.extend(["", "## Coverage Gaps", "", "[SEED:preserve required gaps]", "", "## Test Cases", ""])
        for index, (planned_tc_id, obligation_group) in enumerate(grouped_testable, start=1):
            obligation = obligation_group[0]
            tc_id = (
                contract.test_case_ids[index - 1]
                if contract is not None
                else planned_tc_id
            )
            traceability = "; ".join(
                dict.fromkeys(
                    value
                    for item in obligation_group
                    for value in (
                        item.obligation_id,
                        item.traceability_atom_id,
                        *item.source_refs,
                        *item.dictionary_refs,
                    )
                )
            )
            observable_oracles = "; ".join(
                dict.fromkeys(item.observable_oracle for item in obligation_group)
            )
            atom_label = "+".join(
                item.traceability_atom_id for item in obligation_group
            )
            constraint_gap_ids = tuple(
                dict.fromkeys(
                    gap_id
                    for item in obligation_group
                    for gap_id in item.constraint_gap_ids
                )
            )
            ui_calibration = any(
                self._obligation_requires_ui_calibration(item)
                for item in obligation_group
            )
            reference_fixture_projection = "\n\n".join(
                block
                for item in obligation_group
                if (block := reference_fixture_block(item))
            )
            lines.extend(
                [
                    f"## {tc_id}",
                    "",
                    f"**Название:** [SEED:title:{atom_label}]",
                    "**Тип:** " + ("негативный" if ui_calibration else "позитивный"),
                    (
                        f"**Приоритет:** {contract.expected_priorities[tc_id]}"
                        if contract is not None
                        else "**Приоритет:** средний"
                    ),
                    (
                        f"**package_id:** {contract.domain_package_id}"
                        if contract is not None
                        else "**package_id:** [SEED:package_id]"
                    ),
                    f"**Трассировка:** {traceability}",
                    *(
                        [
                            *(
                                [
                                    f"**Coverage gap:** {'; '.join(constraint_gap_ids)}"
                                ]
                                if constraint_gap_ids
                                else []
                            ),
                            "**Статус oracle:** ui-calibration-required",
                            "**Статус тест-кейса:** candidate-ui-calibration",
                        ]
                        if ui_calibration
                        else []
                    ),
                    "",
                    "### Предусловия",
                    "",
                    "1. [SEED:reproducible setup]",
                    "",
                    "### Тестовые данные",
                    "",
                    "- [SEED:concrete permitted data or parameter]",
                    *(
                        ["", reference_fixture_projection]
                        if reference_fixture_projection
                        else []
                    ),
                    "",
                    "### Шаги",
                    "",
                    "1. [SEED:user action]",
                    "",
                    "### Итоговый ожидаемый результат",
                    "",
                    f"[SEED:observable oracle] {observable_oracles}",
                    "",
                    "### Постусловия",
                    "",
                    "- [SEED:postcondition or explicit not-applicable reason]",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _test_case_id_sort_key(test_case_id: str) -> tuple[str, int, str]:
        match = re.fullmatch(r"(.+?)(\d+)", test_case_id)
        if match is None:
            return (test_case_id, -1, test_case_id)
        return (match.group(1), int(match.group(2)), test_case_id)

    def _build_calibration_lifecycle(self) -> dict[str, Any]:
        obligations = load_obligations(self._prepared_artifact("atomic-obligations"))
        items = []
        for item in obligations.obligations:
            if not self._obligation_requires_ui_calibration(item):
                continue
            items.append(
                {
                    "obligation_id": item.obligation_id,
                    "atom_id": item.traceability_atom_id,
                    "test_case_id": item.planned_test_case_id,
                    "constraint_gap_ids": list(item.constraint_gap_ids),
                    "calibration_status": "ui-calibration-required",
                    "status": "awaiting-ui-calibration",
                    "evidence_status": "not-collected",
                    "regression_ready": False,
                    "required_transition": "ui-evidence -> oracle-resolution -> reviewer-sign-off",
                }
            )
        return {
            "version": 2,
            "context_profile": self._prepared_context_profile(),
            "items": items,
            "open_count": len(items),
            "resolved_count": 0,
        }

    def _obligation_requires_ui_calibration(self, item: Any) -> bool:
        return item.calibration_status == "ui-calibration-required" or (
            bool(item.constraint_gap_ids)
            and self._prepared_context_profile()
            == "character-restriction-calibration"
        )

    def _build_quality_gate_bundle(self) -> dict[str, Any]:
        obligations = load_obligations(self._prepared_artifact("atomic-obligations"))
        draft = self.draft_path.read_text(encoding="utf-8")
        sections = {
            match.group(1): match.group(0)
            for match in re.finditer(
                r"(?ms)^##\s+(TC-[A-Za-z0-9_.-]+)\s*$((?:(?!^##\s+TC-).)*)",
                draft,
            )
        }
        findings: list[dict[str, Any]] = []
        dictionary_groups: dict[tuple[str, tuple[str, ...]], str] = {}
        dictionary_leaf_paths: dict[
            tuple[str, str], list[tuple[tuple[str, ...], str]]
        ] = {}
        for obligation in obligations.obligations:
            for requirement in obligation.dictionary_requirements:
                for value in (
                    *requirement.required_values,
                    *requirement.fixture_values,
                ):
                    identity = (requirement.dictionary_id, value.hierarchy_path)
                    if value.value_kind == "group":
                        dictionary_groups[identity] = value.value
                    elif value.value_kind == "leaf":
                        dictionary_leaf_paths.setdefault(
                            (requirement.dictionary_id, value.value.casefold()),
                            [],
                        ).append((value.hierarchy_path, value.value))
        ambiguous_dictionary_values = {
            key: tuple(dict.fromkeys(paths))
            for key, paths in dictionary_leaf_paths.items()
            if len({path for path, _ in paths}) > 1
        }
        titles: dict[str, list[str]] = {}
        for tc_id, section in sections.items():
            match = re.search(r"(?m)^\*\*Название:\*\*\s*(.+?)\s*$", section)
            if not match:
                continue
            normalized = re.sub(r"\s+", " ", match.group(1).strip()).casefold()
            titles.setdefault(normalized, []).append(tc_id)
        for duplicate_ids in titles.values():
            if len(duplicate_ids) > 1:
                findings.append(
                    {
                        "id": "duplicate-title",
                        "severity": "error",
                        "test_case_ids": duplicate_ids,
                    }
                )
        for tc_id, section in sections.items():
            test_data = markdown_subsection(section, "Тестовые данные")
            steps = markdown_subsection(section, "Шаги")
            expected = markdown_subsection(section, "Итоговый ожидаемый результат")
            if GENERIC_EXECUTION_FIXTURE_RE.search(test_data):
                findings.append(
                    {
                        "id": "generic-execution-fixture",
                        "severity": "error",
                        "test_case_ids": [tc_id],
                    }
                )
            if UNDEFINED_EXECUTION_ACTION_RE.search(steps):
                findings.append(
                    {
                        "id": "undefined-execution-action",
                        "severity": "error",
                        "test_case_ids": [tc_id],
                    }
                )
            if AMBIGUOUS_EXECUTION_ACTION_RE.search(steps):
                findings.append(
                    {
                        "id": "ambiguous-execution-action",
                        "severity": "error",
                        "test_case_ids": [tc_id],
                    }
                )
            if NON_OBSERVABLE_EXPECTED_RESULT_RE.search(expected):
                findings.append(
                    {
                        "id": "non-observable-expected-result",
                        "severity": "error",
                        "test_case_ids": [tc_id],
                    }
                )
        for obligation in obligations.obligations:
            if obligation.coverage_status != "testable":
                continue
            section = next(
                (
                    value
                    for value in sections.values()
                    if obligation.obligation_id in value
                    and obligation.traceability_atom_id in value
                ),
                "",
            )
            if not section:
                continue  # the obligation gate owns missing traceability
            for gap_id in obligation.constraint_gap_ids:
                if gap_id not in section:
                    findings.append(
                        {
                            "id": "constraint-gap-not-preserved",
                            "severity": "error",
                            "obligation_id": obligation.obligation_id,
                            "gap_id": gap_id,
                        }
                    )
            if self._obligation_requires_ui_calibration(obligation):
                for marker in (
                    "ui-calibration-required",
                    "candidate-ui-calibration",
                ):
                    if marker not in section:
                        findings.append(
                            {
                                "id": "calibration-marker-missing",
                                "severity": "error",
                                "obligation_id": obligation.obligation_id,
                                "marker": marker,
                            }
                        )
            for requirement in obligation.dictionary_requirements:
                if requirement.coverage_mode != "reference-only":
                    continue
                for (dictionary_id, _), paths in ambiguous_dictionary_values.items():
                    if dictionary_id != requirement.dictionary_id:
                        continue
                    value = paths[0][1]
                    if value.casefold() not in section.casefold():
                        continue
                    if ANY_DICTIONARY_GROUP_RE.search(section):
                        continue
                    qualifiers = {
                        qualifier
                        for path, _ in paths
                        for qualifier in (
                            path[-1],
                            dictionary_groups.get((dictionary_id, path), ""),
                        )
                        if qualifier
                    }
                    if any(
                        qualifier.casefold() in section.casefold()
                        for qualifier in qualifiers
                    ):
                        continue
                    findings.append(
                        {
                            "id": "ambiguous-dictionary-value-path",
                            "severity": "error",
                            "obligation_id": obligation.obligation_id,
                            "test_case_ids": [obligation.planned_test_case_id],
                            "dictionary_id": dictionary_id,
                            "value": value,
                            "candidate_paths": [list(path) for path, _ in paths],
                        }
                    )
        return {
            "passed": not findings,
            "validator": "prepared-quality-gate-bundle-v1",
            "context_profile": self._prepared_context_profile(),
            "test_case_count": len(sections),
            "checks": [
                "unique-titles",
                "constraint-gap-preservation",
                "ui-calibration-lifecycle-markers",
                "deterministic-structure",
                "obligation-traceability",
                "dictionary-value-completeness",
                "execution-action-unambiguity",
                "dictionary-value-path-unambiguity",
                "semantic-overlap",
                "evidence-access",
                "execution-oracle-quality",
            ],
            "findings": findings,
        }

    def _prepared_gate_summary(self, label: str, path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RunnerError(f"cannot load prepared reviewer gate {label}: {exc}") from exc
        if not isinstance(payload, dict):
            raise RunnerError(f"prepared reviewer gate {label} must be a JSON object")
        summary: dict[str, Any] = {
            "gate": label,
            "passed": payload.get("passed") is True,
            "validator": str(payload.get("validator") or ""),
            "findings_count": len(payload.get("findings") or []),
        }
        for key in (
            "test_case_count",
            "testable_obligations",
            "covered_obligations",
            "commands_checked",
            "fallback_authorizations",
        ):
            if key in payload:
                summary[key] = payload[key]
        return summary

    def _prepared_reviewer_payload(self) -> str:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        if not self.prepared_reviewer_profile_path.is_file():
            raise RunnerError("Prepared reviewer runtime profile is missing")
        draft_text = self.draft_path.read_text(encoding="utf-8")
        metadata = {
            **self._prepared_package_metadata(),
            "reviewed_draft_sha256": sha256_file(self.draft_path),
        }
        gates = [
            self._prepared_gate_summary("structure", self.validator_path),
            self._prepared_gate_summary("seed", self.seed_gate_path),
            self._prepared_gate_summary("obligation", self.obligation_gate_path),
            self._prepared_gate_summary("semantic-overlap", self.semantic_overlap_path),
            self._prepared_gate_summary("writer-evidence-access", self.evidence_access_path),
            self._prepared_gate_summary("quality-bundle", self.quality_gate_bundle_path),
        ]
        if self.package_metadata_gate_path.is_file():
            gates.append(
                self._prepared_gate_summary(
                    "package-metadata", self.package_metadata_gate_path
                )
            )
        if self._is_prepared_standard():
            obligation_heading = "## Verified obligation review index"
            obligation_note = (
                "The immutable full obligations artifact is identified by digest below. "
                "This compact projection contains every exact review-contract ID plus its source-backed "
                "statement, oracle, intent, reference and gap; the runner validates the final contract "
                "against the immutable artifact."
            )
            obligation_payload = self._prepared_standard_reviewer_semantic_projection()
            source_evidence = self._prepared_shared_context_projection()
            calibration_heading = "## Calibration lifecycle summary"
            calibration_payload = self._prepared_standard_reviewer_calibration_summary()
        else:
            obligation_heading = "## Atomic obligations"
            obligation_note = ""
            obligation_payload = self._prepared_artifact("atomic-obligations").read_text(
                encoding="utf-8"
            ).strip()
            source_evidence = self._prepared_artifact("source-evidence").read_text(
                encoding="utf-8"
            ).strip()
            calibration_heading = "## Calibration lifecycle"
            calibration_payload = self.calibration_lifecycle_path.read_text(
                encoding="utf-8"
            ).strip()
        return "\n".join(
            [
                "<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->",
                "## Verified review metadata",
                "",
                "```json",
                json.dumps(metadata, ensure_ascii=False, indent=2),
                "```",
                "",
                self.prepared_reviewer_profile_path.read_text(encoding="utf-8").strip(),
                "",
                self._prepared_context_rule_card(),
                "",
                "## Selected source evidence",
                "",
                source_evidence,
                "",
                obligation_heading,
                "",
                obligation_note,
                "" if obligation_note else "",
                "```json",
                obligation_payload,
                "```",
                "",
                "## Deterministic gate summaries",
                "",
                "```json",
                json.dumps(gates, ensure_ascii=False, indent=2),
                "```",
                "",
                "## Semantic overlap diagnostic (non-blocking, reviewer classification required)",
                "",
                "```json",
                self.semantic_overlap_path.read_text(encoding="utf-8").strip(),
                "```",
                "",
                calibration_heading,
                "",
                "```json",
                calibration_payload,
                "```",
                "",
                "## Immutable writer draft",
                "",
                "```markdown",
                draft_text.strip(),
                "```",
                "",
                "## Required final contract",
                "",
                "Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.",
                "Dictionary evidence in the verified obligation projection is authoritative. Before claiming that a DICT-* value is absent, compare it with the exact active_values array supplied there.",
                "<!-- PREPARED-REVIEW-PAYLOAD:END -->",
            ]
        )

    def _validate_draft_package_metadata(self) -> ValidationResult:
        if self._prepared_package is None:
            raise RunnerError("Prepared package is not loaded")
        expected = self._prepared_package.package_id
        findings: list[dict[str, Any]] = []
        for test_case_id, _, _, section in test_case_section_spans(
            self.draft_path.read_text(encoding="utf-8")
        ):
            values = PACKAGE_ID_LINE_RE.findall(section)
            if not values:
                findings.append(
                    {
                        "id": "package-id-missing",
                        "severity": "error",
                        "test_case_ids": [test_case_id],
                        "expected_package_id": expected,
                    }
                )
            elif len(values) > 1:
                findings.append(
                    {
                        "id": "package-id-duplicate",
                        "severity": "error",
                        "test_case_ids": [test_case_id],
                        "actual_package_ids": values,
                    }
                )
            elif values[0] != expected:
                findings.append(
                    {
                        "id": "package-id-mismatch",
                        "severity": "error",
                        "test_case_ids": [test_case_id],
                        "expected_package_id": expected,
                        "actual_package_id": values[0],
                    }
                )
        return ValidationResult(
            passed=not findings,
            findings=tuple(findings),
            checked_paths=(relative_path(self.draft_path, self.repo_root),),
            validator="prepared-package-metadata-gate-v1",
        )

    def _validate_draft_seed(self) -> ValidationResult:
        findings: list[dict[str, Any]] = []
        if not self.draft_seed_path.is_file() or sha256_file(self.draft_seed_path) != self._draft_seed_sha256:
            findings.append(
                {
                    "id": "draft-seed-input-changed",
                    "severity": "error",
                    "message": "Runner-owned draft seed changed during the writer stage.",
                }
            )
        draft = self.draft_path.read_text(encoding="utf-8")
        if SEED_MARKER in draft or "[SEED:" in draft:
            findings.append(
                {
                    "id": "draft-seed-placeholder-remains",
                    "severity": "error",
                    "message": "Draft still contains runner seed sentinels/placeholders.",
                }
            )
        if self.draft_path.read_bytes() == self.draft_seed_path.read_bytes():
            findings.append(
                {
                    "id": "draft-equals-seed",
                    "severity": "error",
                    "message": "Writer did not make a meaningful change to the draft seed.",
                }
            )
        return ValidationResult(
            passed=not findings,
            findings=tuple(findings),
            checked_paths=(str(self.draft_seed_path), str(self.draft_path)),
            validator="prepared-draft-seed-gate-v1",
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

    def _stage_limits(self, role: str) -> tuple[int, int | None, int]:
        if role == "writer":
            if self._uses_structured_prepared_writer():
                timeout = (
                    self._prepared_instruction_int("hard_timeout_seconds")
                    if self._is_prepared_fast()
                    else self.writer_timeout_seconds or self.timeout_seconds
                )
                idle_timeout = None
                command_budget = 0
            elif self._is_prepared_fast():
                timeout = self._prepared_instruction_int("hard_timeout_seconds")
                if not self._uses_structured_prepared_writer():
                    idle_timeout = self._prepared_instruction_int("idle_timeout_seconds")
                    command_budget = self._prepared_instruction_int("command_budget")
            else:
                timeout = self.writer_timeout_seconds or self.timeout_seconds
                idle_timeout = self.writer_idle_timeout_seconds
                command_budget = self.writer_command_budget
        else:
            if self._uses_compact_prepared_reviewer():
                timeout = (
                    self.prepared_reviewer_timeout_seconds
                    if self._is_prepared_fast()
                    else self.reviewer_timeout_seconds or self.timeout_seconds
                )
                idle_timeout = None
                command_budget = self.prepared_reviewer_command_budget
            else:
                timeout = self.reviewer_timeout_seconds or self.timeout_seconds
                idle_timeout = (
                    self.prepared_standard_reviewer_idle_timeout_seconds
                    if self._is_prepared_standard()
                    else self.reviewer_idle_timeout_seconds
                )
                command_budget = self.reviewer_command_budget
        return (
            timeout,
            min(idle_timeout, timeout) if idle_timeout is not None else None,
            command_budget,
        )

    def _run_structured_writer_shards(
        self,
        state: dict[str, Any],
    ) -> tuple[ProcessResult, dict[str, Any]] | CycleResult:
        shards = list(self._writer_output_capacity_plan.get("shards") or [])
        if not shards:
            raise RunnerError("sharded writer route has no shards")
        first_result: ProcessResult | None = None
        first_artifacts: dict[str, Any] | None = None
        seen_backend_ids: set[str] = set()
        evidence_reports: list[dict[str, Any]] = []
        for shard in shards:
            stage = str(shard["stage"])
            result, artifacts = self._run_stage(
                stage=stage,
                role="writer",
                prompt=self._writer_shard_prompt(shard),
                last_message_path=self.writer_result_path_for(stage),
            )
            evidence_access = validate_evidence_access(
                events_text=result.stdout,
                forbidden_roots=self._prepared_package.forbidden_evidence_roots,
                source_registry=self._prepared_package.source_registry,
                allowed_stage_roots=(
                    relative_path(self.stage_output_dir(stage), self.repo_root),
                ),
                reject_unlisted_commands=True,
                require_source_fallback_authorization=False,
            )
            evidence_path = self.runner_output_dir(stage) / "evidence-access-report.json"
            write_json(evidence_path, evidence_access.as_dict())
            evidence_reports.append(
                {
                    "stage": stage,
                    "path": relative_path(evidence_path, self.repo_root),
                    "passed": evidence_access.passed,
                }
            )
            if not evidence_access.passed:
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-evidence-access",
                    reasons=[
                        "prepared writer shard evidence-access gate reported findings",
                        relative_path(evidence_path, self.repo_root),
                    ],
                )
            if result.launch_error:
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-process-launch",
                    reasons=["writer shard process could not be started"],
                )
            if result.exit_code not in (None, 0):
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-process-exit",
                    reasons=[f"writer shard process exited with code {result.exit_code}"],
                )
            if file_change_count_from_events(result.stdout):
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-forbidden-workspace-change",
                    reasons=["read-only structured writer shard emitted a file-change event"],
                )
            if (
                result.timed_out
                or result.idle_timed_out
                or result.command_budget_exceeded
                or result.first_artifact_deadline_exceeded
            ):
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status=(
                        "blocked-command-budget"
                        if result.command_budget_exceeded
                        else "blocked-timeout"
                    ),
                    reasons=[
                        "structured writer shard attempted a command"
                        if result.command_budget_exceeded
                        else "structured writer shard did not return a complete contract within its runtime budget"
                    ],
                )
            message = self._reviewer_message(result.stdout)
            if not message.strip():
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-missing-output",
                    reasons=["structured writer shard completed without a final JSON contract"],
                )
            try:
                contract = parse_prepared_writer_contract(message)
            except RunnerError as exc:
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-invalid-output",
                    reasons=[str(exc)],
                )
            if contract.status == "blocked-input":
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-input",
                    reasons=list(contract.blocking_reasons),
                )
            path = self._materialize_writer_shard(stage, contract.draft_markdown)
            validation = self._validate_writer_shard(shard=shard, path=path)
            validation_path = self.runner_output_dir(stage) / "shard-validator.json"
            write_json(validation_path, validation.as_dict())
            if not validation.passed:
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-shard-validator",
                    reasons=[
                        "prepared writer shard validator reported findings",
                        relative_path(validation_path, self.repo_root),
                    ],
                )
            execution = artifacts.get("_execution")
            backend_id = (
                execution.backend_session_id
                if isinstance(execution, BackendStageExecution)
                else ""
            )
            session_issue = self._backend_session_issue(artifacts)
            if not session_issue and backend_id in seen_backend_ids:
                session_issue = (
                    "codex exec reused a backend session/thread id across writer shards: "
                    + backend_id
                )
            if session_issue:
                return self._block_stage(
                    state,
                    stage=stage,
                    role="writer",
                    result=result,
                    artifacts=artifacts,
                    status="blocked-contract",
                    reasons=[session_issue],
                )
            seen_backend_ids.add(backend_id)
            if stage == WRITER_STAGE:
                first_result = result
                first_artifacts = artifacts
            else:
                self._write_stage_status(
                    stage=stage,
                    role="writer",
                    status="completed",
                    result=result,
                    artifacts=artifacts,
                    reason="assigned writer shard passed its deterministic validator",
                    draft_sha256=sha256_file(path),
                )
                self._write_contract_result(
                    stage=stage,
                    role="writer",
                    outcome="draft-ready",
                    result=result,
                    artifacts=artifacts,
                )
        if first_result is None or first_artifacts is None:
            raise RunnerError("writer shard plan did not execute the primary writer stage")
        self._merge_writer_shards(shards)
        write_json(
            self.evidence_access_path,
            {
                "passed": True,
                "validator": "prepared-writer-shard-evidence-access-aggregate-v1",
                "shard_count": len(shards),
                "reports": evidence_reports,
                "findings": [],
            },
        )
        return first_result, first_artifacts

    def run(self) -> CycleResult:
        self.validate_configuration()
        production_before = self._production_snapshot()
        sharded_writer = self._uses_sharded_prepared_writer()
        repair_writer = self._uses_targeted_prepared_repair()
        reviewer_rebind = self._uses_prepared_reviewer_rebind()
        writer_prompt = "" if sharded_writer or reviewer_rebind else self._writer_prompt()
        state = self._initial_state()
        self._write_state(state)
        if self._prepared_oracle_quality_plan:
            write_json(
                self.prepared_oracle_quality_path,
                self._prepared_oracle_quality_plan,
            )
        if self._prepared_state_change_plan:
            write_json(
                self.prepared_state_change_path,
                self._prepared_state_change_plan,
            )
        if self._prepared_repair_plan:
            write_json(self.prepared_repair_plan_path, self._prepared_repair_plan)
        if self._writer_output_capacity_plan:
            write_json(
                self.writer_output_capacity_path,
                self._writer_output_capacity_plan,
            )
            if sharded_writer:
                write_json(self.writer_shard_plan_path, self._writer_output_capacity_plan)
        append_event(self.cycle_dir, "cycle_started", backend="codex-exec")

        if reviewer_rebind:
            writer_result = ProcessResult(
                exit_code=0,
                termination_reason="runner-owned-reviewer-rebind",
            )
            writer_artifacts = {
                "command": [],
                "stdout": "",
                "stderr": "",
                "events": "",
                "last_message": "",
                "_runner_owned_rebind": True,
            }
            self.draft_seed_path.parent.mkdir(parents=True, exist_ok=True)
            self.draft_seed_path.write_text(self._draft_seed_text(), encoding="utf-8")
            self._draft_seed_sha256 = sha256_file(self.draft_seed_path)
            try:
                self._materialize_prepared_reviewer_rebind()
            except RunnerError as exc:
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-reviewer-rebind",
                    reasons=[str(exc)],
                )
        elif sharded_writer:
            sharded_result = self._run_structured_writer_shards(state)
            if isinstance(sharded_result, CycleResult):
                return sharded_result
            writer_result, writer_artifacts = sharded_result
        else:
            writer_result, writer_artifacts = self._run_stage(
                stage=WRITER_STAGE,
                role="writer",
                prompt=writer_prompt,
                last_message_path=(
                    self.writer_result_path
                    if self._uses_structured_prepared_writer()
                    else self.stage_output_dir(WRITER_STAGE) / "last-message.txt"
                ),
            )
        if (
            self._prepared_package is not None
            and not sharded_writer
            and not reviewer_rebind
        ):
            evidence_access = validate_evidence_access(
                events_text=writer_result.stdout,
                forbidden_roots=self._prepared_package.forbidden_evidence_roots,
                source_registry=self._prepared_package.source_registry,
                allowed_stage_roots=(
                    relative_path(self.stage_output_dir(WRITER_STAGE), self.repo_root),
                ),
                reject_unlisted_commands=self._uses_structured_prepared_writer(),
                require_source_fallback_authorization=(
                    self._is_prepared_fast()
                    or self.prepared_standard_writer_mode == "assisted"
                ),
                allow_read_only_git_status_checks=(
                    self._is_prepared_standard()
                    and self.prepared_standard_writer_mode == "assisted"
                ),
                allowed_bounded_scan_roots=(
                    ("scripts",)
                    if self._is_prepared_standard()
                    and self.prepared_standard_writer_mode == "assisted"
                    else ()
                ),
            )
            write_json(self.evidence_access_path, evidence_access.as_dict())
            if not evidence_access.passed:
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-evidence-access",
                    reasons=[
                        "prepared evidence-access gate reported findings",
                        relative_path(self.evidence_access_path, self.repo_root),
                    ],
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

        if not reviewer_rebind and writer_result.launch_error:
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status="blocked-process-launch",
                reasons=["writer process could not be started"],
            )
        if not reviewer_rebind and writer_result.exit_code not in (None, 0):
            return self._block_stage(
                state,
                stage=WRITER_STAGE,
                role="writer",
                result=writer_result,
                artifacts=writer_artifacts,
                status="blocked-process-exit",
                reasons=[f"writer process exited with code {writer_result.exit_code}"],
            )
        if (
            self._uses_structured_prepared_writer()
            and not sharded_writer
            and not reviewer_rebind
        ):
            if file_change_count_from_events(writer_result.stdout):
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-forbidden-workspace-change",
                    reasons=[
                        "read-only structured writer emitted a file-change event"
                    ],
                )
            if (
                writer_result.timed_out
                or writer_result.idle_timed_out
                or writer_result.command_budget_exceeded
                or writer_result.first_artifact_deadline_exceeded
            ):
                reason = (
                    "structured writer attempted a command"
                    if writer_result.command_budget_exceeded
                    else "structured writer did not return a complete contract within its runtime budget"
                )
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status=(
                        "blocked-command-budget"
                        if writer_result.command_budget_exceeded
                        else "blocked-timeout"
                    ),
                    reasons=[reason],
                )
            writer_message = self._reviewer_message(writer_result.stdout)
            if not writer_message.strip():
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-missing-output",
                    reasons=["structured writer completed without a final JSON contract"],
                )
            try:
                writer_contract = parse_prepared_writer_contract(writer_message)
            except RunnerError as exc:
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-invalid-output",
                    reasons=[str(exc)],
                )
            if writer_contract.status == "blocked-input":
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-input",
                    reasons=list(writer_contract.blocking_reasons),
                )
            if repair_writer:
                try:
                    repair_validation = self._materialize_targeted_repair(
                        writer_contract.draft_markdown
                    )
                except RunnerError as exc:
                    return self._block_stage(
                        state,
                        stage=WRITER_STAGE,
                        role="writer",
                        result=writer_result,
                        artifacts=writer_artifacts,
                        status="blocked-repair-contract",
                        reasons=[str(exc)],
                    )
                if not repair_validation.passed:
                    return self._block_stage(
                        state,
                        stage=WRITER_STAGE,
                        role="writer",
                        result=writer_result,
                        artifacts=writer_artifacts,
                        status="blocked-repair-gate",
                        reasons=[
                            "prepared targeted repair validator reported findings",
                            relative_path(self.repair_validator_path, self.repo_root),
                        ],
                        validation=repair_validation,
                    )
            else:
                self._materialize_structured_writer_draft(writer_contract.draft_markdown)
        if not self.draft_path.is_file():
            if writer_result.command_budget_exceeded:
                status = "blocked-command-budget"
                reason = "writer exceeded the command budget and the required draft is missing"
            elif writer_result.idle_timed_out:
                status = "blocked-idle-timeout"
                reason = "writer produced no events within the idle budget and the required draft is missing"
            elif writer_result.first_artifact_deadline_exceeded:
                status = "blocked-first-artifact-deadline"
                reason = "writer did not create a meaningful draft before the first-artifact deadline"
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

        if self._prepared_package is not None:
            obligation_set = load_obligations(
                self._prepared_artifact("atomic-obligations")
            )
            draft_before_projection = self.draft_path.read_text(encoding="utf-8")
            writer_ownership = validate_writer_dictionary_ownership(
                draft_before_projection,
                obligation_set,
            )
            if not writer_ownership["passed"]:
                write_json(
                    self.dictionary_projection_path,
                    {
                        "version": 1,
                        "validator": "runner-owned-dictionary-projection-v1",
                        "materialized_count": 0,
                        "items": [],
                        "draft_changed": False,
                        "writer_ownership": writer_ownership,
                    },
                )
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-dictionary-projection-ownership",
                    reasons=[
                        "structured writer duplicated runner-owned exhaustive dictionary values",
                        relative_path(self.dictionary_projection_path, self.repo_root),
                    ],
                )
            reference_projected_draft, reference_fixture_report = (
                materialize_draft_reference_fixtures(
                    draft_before_projection,
                    obligation_set,
                )
            )
            projected_draft, projection_report = (
                materialize_draft_dictionary_projections(
                    reference_projected_draft,
                    obligation_set,
                )
            )
            projection_report["writer_ownership"] = writer_ownership
            projection_report["reference_fixtures"] = reference_fixture_report
            projection_report["draft_changed"] = (
                projected_draft != draft_before_projection
            )
            if projection_report["draft_changed"]:
                self.draft_path.write_text(projected_draft, encoding="utf-8")
            write_json(self.dictionary_projection_path, projection_report)
            if repair_writer or reviewer_rebind:
                package_metadata_validation = self._validate_draft_package_metadata()
                write_json(
                    self.package_metadata_gate_path,
                    package_metadata_validation.as_dict(),
                )
                if not package_metadata_validation.passed:
                    return self._block_stage(
                        state,
                        stage=WRITER_STAGE,
                        role="writer",
                        result=writer_result,
                        artifacts=writer_artifacts,
                        status="blocked-package-metadata-gate",
                        reasons=[
                            "prepared package metadata gate reported findings",
                            relative_path(self.package_metadata_gate_path, self.repo_root),
                        ],
                        validation=package_metadata_validation,
                    )
            seed_validation = self._validate_draft_seed()
            write_json(self.seed_gate_path, seed_validation.as_dict())
            if not seed_validation.passed:
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-seed-gate",
                    reasons=[
                        "prepared draft seed gate reported findings",
                        relative_path(self.seed_gate_path, self.repo_root),
                    ],
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

            semantic_overlap = build_semantic_overlap_diagnostic(self.draft_path)
            write_json(self.semantic_overlap_path, semantic_overlap)

            write_json(
                self.calibration_lifecycle_path,
                self._build_calibration_lifecycle(),
            )
            quality_bundle = self._build_quality_gate_bundle()
            write_json(self.quality_gate_bundle_path, quality_bundle)
            if not quality_bundle["passed"]:
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-quality-gate",
                    reasons=[
                        "prepared deterministic quality gate reported findings",
                        relative_path(self.quality_gate_bundle_path, self.repo_root),
                    ],
                    validation=validation,
                )
            if repair_writer:
                try:
                    self._verify_repair_inputs()
                except RunnerError as exc:
                    return self._block_stage(
                        state,
                        stage=WRITER_STAGE,
                        role="writer",
                        result=writer_result,
                        artifacts=writer_artifacts,
                        status="blocked-repair-contract",
                        reasons=[str(exc)],
                        validation=validation,
                    )

        if self._promotion_contract is not None:
            promotion_readiness = validate_promotion_readiness(
                draft_path=self.draft_path,
                contract=self._promotion_contract,
            )
            write_json(self.promotion_readiness_path, promotion_readiness.as_dict())
            if not promotion_readiness.passed:
                return self._block_stage(
                    state,
                    stage=WRITER_STAGE,
                    role="writer",
                    result=writer_result,
                    artifacts=writer_artifacts,
                    status="blocked-promotion-readiness",
                    reasons=[
                        "prepared promotion-readiness gate reported findings",
                        relative_path(self.promotion_readiness_path, self.repo_root),
                    ],
                    validation=validation,
                )

        writer_session_issue = (
            "" if reviewer_rebind else self._backend_session_issue(writer_artifacts)
        )
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
            or writer_result.first_artifact_deadline_exceeded
        )
        writer_status = (
            "skipped-reviewer-rebind"
            if reviewer_rebind
            else "completed-with-progress"
            if writer_interrupted
            else "completed"
        )
        if reviewer_rebind:
            rebind = json.loads(self.reviewer_rebind_path.read_text(encoding="utf-8"))
            rebind.update(
                {
                    "status": "validated-reviewer-ready",
                    "passed": True,
                    "deterministic_gates_passed": True,
                    "writer_llm_started": False,
                    "gate_artifacts": [
                        relative_path(path, self.repo_root)
                        for path in (
                            self.package_metadata_gate_path,
                            self.seed_gate_path,
                            self.validator_path,
                            self.obligation_gate_path,
                            self.semantic_overlap_path,
                            self.calibration_lifecycle_path,
                            self.dictionary_projection_path,
                            self.quality_gate_bundle_path,
                            self.evidence_access_path,
                        )
                    ],
                }
            )
            write_json(self.reviewer_rebind_path, rebind)
            append_event(
                self.cycle_dir,
                "prepared_reviewer_rebind_validated",
                draft_sha256=draft_sha256,
                writer_llm_started=False,
            )
        else:
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
        writer_completion_state = {
            "writer_stage_status": writer_status,
            "draft_test_cases": relative_path(self.draft_path, self.ft_root),
            "writer_draft_sha256": draft_sha256,
            "validator_report": relative_path(self.validator_path, self.ft_root),
            "obligation_gate_report": (
                relative_path(self.obligation_gate_path, self.ft_root)
                if self._prepared_package is not None
                else ""
            ),
            "semantic_overlap_diagnostic": (
                relative_path(self.semantic_overlap_path, self.ft_root)
                if self._prepared_package is not None
                else ""
            ),
            "quality_gate_bundle": (
                relative_path(self.quality_gate_bundle_path, self.ft_root)
                if self._prepared_package is not None
                else ""
            ),
            "calibration_lifecycle": (
                relative_path(self.calibration_lifecycle_path, self.ft_root)
                if self._prepared_package is not None
                else ""
            ),
            "dictionary_projection": (
                relative_path(self.dictionary_projection_path, self.ft_root)
                if self._prepared_package is not None
                else ""
            ),
            "seed_gate_report": (
                relative_path(self.seed_gate_path, self.ft_root)
                if self._prepared_package is not None
                else ""
            ),
            "evidence_access_report": (
                relative_path(self.evidence_access_path, self.ft_root)
                if self._prepared_package is not None
                else ""
            ),
            "reviewer_rebind_report": (
                relative_path(self.reviewer_rebind_path, self.ft_root)
                if reviewer_rebind
                else ""
            ),
        }
        try:
            reviewer_prompt = self._reviewer_prompt()
        except RunnerError as exc:
            if not str(exc).startswith("blocked-prepared-standard-context-budget"):
                raise
            report_path = self.cycle_dir / "reviewer-context-budget.json"
            report = self._context_budget_reports.get(REVIEWER_STAGE)
            if report is not None:
                write_json(report_path, report)
            state.update(writer_completion_state)
            state.update(
                {
                    "workflow_status": "blocked-reviewer-preflight",
                    "stage_status": "blocked-input",
                    "current_stage": REVIEWER_STAGE,
                    "reviewer_stage_status": "blocked-context-budget",
                    "reviewer_context_budget": (
                        relative_path(report_path, self.ft_root) if report is not None else ""
                    ),
                    "active_transition_prompt": "",
                    "blocking_reasons": [str(exc)],
                }
            )
            self._write_state(state)
            append_event(
                self.cycle_dir,
                "reviewer_preflight_blocked",
                status="blocked-context-budget",
                reason=str(exc),
                context_budget=(
                    relative_path(report_path, self.repo_root) if report is not None else ""
                ),
            )
            return self._result(state)
        state.update(writer_completion_state)
        state.update(
            {
                "workflow_status": "reviewer-ready",
                "stage_status": "writer-draft-ready",
                "current_stage": REVIEWER_STAGE,
                "active_transition_prompt": relative_path(
                    self.prompt_path(REVIEWER_STAGE), self.ft_root
                ),
            }
        )
        self._write_state(state)
        append_event(
            self.cycle_dir,
            (
                "reviewer_rebind_stage_completed"
                if reviewer_rebind
                else "writer_stage_completed"
            ),
            stage_status=writer_status,
        )

        reviewer_result, reviewer_artifacts = self._run_stage(
            stage=REVIEWER_STAGE,
            role="reviewer",
            prompt=reviewer_prompt,
            last_message_path=None,
        )
        if self._prepared_package is not None:
            reviewer_forbidden_roots = (
                (
                    *self._prepared_package.forbidden_evidence_roots,
                    "skills",
                    "references",
                    "prepared-input",
                    "attempts/writer-r1",
                )
                if self._uses_compact_prepared_reviewer()
                else (
                    *self._prepared_package.forbidden_evidence_roots,
                    "prepared-input",
                    "attempts/writer-r1",
                )
            )
            reviewer_access = validate_evidence_access(
                events_text=reviewer_result.stdout,
                forbidden_roots=reviewer_forbidden_roots,
                source_registry=self._prepared_package.source_registry,
                allowed_command_fragments=("python scripts/probe_environment.py",),
                reject_unlisted_commands=self._uses_compact_prepared_reviewer(),
                require_source_fallback_authorization=self._uses_compact_prepared_reviewer(),
                allow_read_only_git_status_checks=(
                    self._is_prepared_standard()
                    and self.prepared_standard_writer_mode == "assisted"
                ),
                allowed_bounded_scan_roots=(
                    ("scripts",)
                    if self._is_prepared_standard()
                    and self.prepared_standard_writer_mode == "assisted"
                    else ()
                ),
            )
            write_json(self.reviewer_evidence_access_path, reviewer_access.as_dict())
            if not reviewer_access.passed:
                return self._block_stage(
                    state,
                    stage=REVIEWER_STAGE,
                    role="reviewer",
                    result=reviewer_result,
                    artifacts=reviewer_artifacts,
                    status="blocked-evidence-access",
                    reasons=[
                        "prepared reviewer evidence-access gate reported findings",
                        relative_path(self.reviewer_evidence_access_path, self.repo_root),
                    ],
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
            if self._prepared_package is not None:
                review = parse_prepared_review_contract(
                    reviewer_message,
                    expected_obligations=load_obligations(
                        self._prepared_artifact("atomic-obligations")
                    ).obligations,
                    expected_draft_sha256=draft_sha256,
                    draft_text=self.draft_path.read_text(encoding="utf-8"),
                )
            else:
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

        findings_markdown = (
            render_prepared_review_findings(review)
            if review.contract_version == 2
            else review.findings_markdown
        )
        self.reviewer_findings_path.write_text(findings_markdown.rstrip() + "\n", encoding="utf-8")
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

        if self.promotion_dry_run:
            try:
                plan = self._promotion_plan(
                    production_before, expected_draft_sha256=draft_sha256
                )
            except RunnerError as exc:
                state["workflow_status"] = "blocked-promotion-dry-run"
                state["stage_status"] = "blocked-input"
                state["blocking_reasons"] = [str(exc)]
                self._write_state(state)
                append_event(self.cycle_dir, "promotion_dry_run_blocked", reason=str(exc))
                return self._result(state)
            write_json(self.promotion_dry_run_path, plan)
            state.update(
                {
                    "workflow_status": "accepted-promotion-dry-run",
                    "stage_status": "accepted-promotion-dry-run",
                    "promotion_status": "dry-run-passed",
                    "promotion_dry_run_report": relative_path(
                        self.promotion_dry_run_path, self.ft_root
                    ),
                    "blocking_reasons": ["promotion dry-run passed; production was not written"],
                }
            )
            self._write_state(state)
            append_event(self.cycle_dir, "promotion_dry_run_passed", **plan)
            return self._result(state)

        if not self.promote_final:
            status = (
                "accepted-promotion-ready-not-promoted"
                if self._promotion_contract is not None
                else "accepted-not-promoted"
            )
            state["workflow_status"] = status
            state["stage_status"] = status
            if self._promotion_contract is not None:
                state["promotion_readiness_report"] = relative_path(
                    self.promotion_readiness_path, self.ft_root
                )
                state["promotion_status"] = "ready-not-promoted"
            state["blocking_reasons"] = [
                "promotion is disabled; review the promotion-ready candidate before a controlled production write"
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

    def validate_only_report(self) -> dict[str, Any]:
        """Validate the first transition without creating cycle or attempt artifacts."""
        self.validate_configuration()
        if self._uses_prepared_reviewer_rebind():
            obligations = load_obligations(
                self._prepared_artifact("atomic-obligations")
            ).obligations
            self._prepared_dictionary_evidence_projection(obligations)
        elif self._uses_sharded_prepared_writer():
            for shard in self._writer_output_capacity_plan["shards"]:
                self._writer_shard_prompt(shard)
        else:
            self._writer_prompt()
        route = (
            "prepared-fast"
            if self._is_prepared_fast()
            else "prepared-standard"
            if self._is_prepared_standard()
            else "raw-standard"
        )
        report: dict[str, Any] = {
            "status": "validated",
            "route": route,
            "writer_scenario": (
                "runner.prepared_reviewer_rebind"
                if self._uses_prepared_reviewer_rebind()
                else (
                    "writer.session_prepared_targeted_repair"
                    if self._uses_targeted_prepared_repair()
                    else (
                        "writer.session_prepared_initial_draft"
                        if self._is_prepared_fast()
                        else (
                            "writer.session_prepared_standard_structured"
                            if self._uses_structured_prepared_writer()
                            else self._standard_scenario("writer")
                        )
                    )
                )
            ),
            "reviewer_scenario": (
                "reviewer.session_prepared_semantic"
                if self._is_prepared_fast()
                else (
                    "reviewer.session_prepared_standard_semantic"
                    if self._uses_compact_prepared_reviewer()
                    else self._standard_scenario("reviewer")
                )
            ),
            "final_artifact": relative_path(self.final_path, self.repo_root),
            "final_exists": self.final_path.exists(),
            "cycle_artifacts_created": False,
        }
        if self._prepared_package is not None:
            report.update(
                {
                    "package_version": self._prepared_package.package_version,
                    "package_id": self._prepared_package.package_id,
                    "package_digest": self._prepared_package.package_digest,
                    "input_fingerprint": self._prepared_package.input_fingerprint,
                    "execution_profile": self._prepared_package.execution_profile,
                    "unsupported_dimensions": list(
                        self._prepared_package.unsupported_dimensions
                    ),
                    "writer_context_budget": self._context_budget_reports.get(
                        WRITER_STAGE, {}
                    ),
                    "writer_shard_context_budgets": [
                        self._context_budget_reports[stage]
                        for stage in (
                            shard["stage"]
                            for shard in self._writer_output_capacity_plan.get(
                                "shards", []
                            )
                        )
                        if stage in self._context_budget_reports
                    ],
                    "writer_output_capacity": self._writer_output_capacity_plan,
                    "prepared_oracle_quality": self._prepared_oracle_quality_plan,
                    "prepared_state_change": self._prepared_state_change_plan,
                    "targeted_repair": self._prepared_repair_plan,
                    "writer_targeted_repair": self._uses_targeted_prepared_repair(),
                    "reviewer_rebind": self._prepared_reviewer_rebind_plan,
                    "writer_llm_required": not self._uses_prepared_reviewer_rebind(),
                    "reviewer_output_capacity": self._reviewer_output_capacity_plan,
                    "reviewer_context_capacity": self._reviewer_context_capacity_plan,
                    "writer_sharded": self._uses_sharded_prepared_writer(),
                    "prepared_fast_writer_mode": self.prepared_fast_writer_mode,
                    "prepared_standard_writer_mode": self.prepared_standard_writer_mode,
                    "context_profile": self._prepared_context_profile(),
                    "compact_reviewer": self._uses_compact_prepared_reviewer(),
                    "writer_sandbox_policy": (
                        "not-applicable-runner-owned-rebind"
                        if self._uses_prepared_reviewer_rebind()
                        else "read_only"
                        if self._uses_structured_prepared_writer()
                        else "workspace_write"
                    ),
                    "writer_command_budget": (
                        0
                        if self._uses_prepared_reviewer_rebind()
                        else self._stage_limits("writer")[2]
                    ),
                    "reviewer_command_budget": self._stage_limits("reviewer")[2],
                    "runtime_identity": {
                        "passed": True,
                        "validator": "prepared-runtime-identity-v1",
                        "version_source": "runner-PACKAGE_VERSION",
                        "package_version": self._prepared_package.package_version,
                        "package_id": self._prepared_package.package_id,
                        "package_digest": self._prepared_package.package_digest,
                        "input_fingerprint": self._prepared_package.input_fingerprint,
                        "writer_profile_numeric_allowlist": False,
                        "reviewer_profile_numeric_allowlist": False,
                    },
                    "preflight_checks": [
                        "package-digest",
                        "attempt-binding",
                        "profile-route",
                        "runtime-identity",
                        "instruction-allowlist",
                        "prepared-oracle-quality",
                        "prepared-state-change",
                        "targeted-repair-input-hashes",
                        "targeted-repair-test-case-set",
                        "reviewer-rebind-input-hash",
                        "reviewer-rebind-test-case-set",
                        "reviewer-rebind-semantic-preservation",
                        "structured-dictionary-projection",
                        "writer-dictionary-ownership",
                        "context-budget",
                        "output-capacity",
                        "reviewer-output-capacity",
                        "shard-union-disjointness",
                        "command-budget",
                        "sandbox-policy",
                        "production-boundary",
                    ],
                }
            )
        return report

    def _initial_state(self) -> dict[str, Any]:
        reviewer_rebind = self._uses_prepared_reviewer_rebind()
        return {
            "cycle_id": self.cycle_dir.name,
            "ft_slug": self.ft_root.name,
            "scope_slug": self.cycle_dir.name,
            "backend": "codex-exec",
            "workflow_status": (
                "reviewer-rebind-ready" if reviewer_rebind else "writer-ready"
            ),
            "stage_status": (
                "reviewer-rebind-ready" if reviewer_rebind else "scope-ready-for-writer"
            ),
            "current_stage": "reviewer-rebind" if reviewer_rebind else WRITER_STAGE,
            "semantic_round": 0,
            "max_semantic_rounds": 2,
            "writer_stage_status": (
                "skipped-reviewer-rebind" if reviewer_rebind else "pending"
            ),
            "reviewer_stage_status": "pending",
            "draft_test_cases": "",
            "canonical_test_cases": relative_path(self.final_path, self.ft_root),
            "validator_report": "",
            "obligation_gate_report": "",
            "semantic_overlap_diagnostic": "",
            "seed_gate_report": "",
            "evidence_access_report": "",
            "writer_draft_sha256": "",
            "reviewer_findings": "",
            "accepted_terminal_state": False,
            "final_promoted": False,
            "draft_or_unsigned": True,
            "promotion_status": "pending",
            "active_transition_prompt": (
                ""
                if reviewer_rebind
                else relative_path(self.prompt_path(WRITER_STAGE), self.ft_root)
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

    def _materialize_structured_writer_draft(self, draft_markdown: str) -> None:
        self.draft_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.draft_path.with_suffix(self.draft_path.suffix + ".tmp")
        if temporary.exists():
            raise RunnerError(
                "structured writer temporary draft already exists; recovery must be explicit"
            )
        try:
            temporary.write_text(draft_markdown.rstrip() + "\n", encoding="utf-8")
            temporary.replace(self.draft_path)
        finally:
            temporary.unlink(missing_ok=True)
        append_event(
            self.cycle_dir,
            "structured_writer_draft_materialized",
            draft=relative_path(self.draft_path, self.repo_root),
            draft_bytes=self.draft_path.stat().st_size,
            draft_sha256=sha256_file(self.draft_path),
        )

    def _materialize_prepared_reviewer_rebind(self) -> None:
        self._verify_reviewer_rebind_input()
        assert self.prepared_reviewer_rebind_draft_path is not None
        source_text = self.prepared_reviewer_rebind_draft_path.read_text(
            encoding="utf-8"
        )
        source_spans = test_case_section_spans(source_text)
        expected_package_id = self._prepared_package.package_id if self._prepared_package else ""
        prefix = source_text[: source_spans[0][1]] if source_spans else source_text
        chunks = [prefix]
        migrated_ids: list[str] = []
        for test_case_id, _, _, source_section in source_spans:
            source_package_ids = PACKAGE_ID_LINE_RE.findall(source_section)
            if len(source_package_ids) != 1:
                raise RunnerError(
                    "Prepared reviewer rebind source section must contain exactly one "
                    f"package_id: {test_case_id}"
                )
            rebound = PACKAGE_ID_LINE_RE.sub(
                f"**package_id:** {expected_package_id}", source_section, count=1
            )
            if source_package_ids[0] != expected_package_id:
                migrated_ids.append(test_case_id)
            chunks.append(rebound)
        self._materialize_structured_writer_draft("".join(chunks).rstrip() + "\n")
        output_sections = {
            test_case_id: section
            for test_case_id, _, _, section in test_case_section_spans(
                self.draft_path.read_text(encoding="utf-8")
            )
        }
        section_results: list[dict[str, Any]] = []
        semantics_preserved = True
        for source in self._prepared_reviewer_rebind_plan["sections"]:
            test_case_id = source["test_case_id"]
            output_section = output_sections.get(test_case_id, "")
            output_semantics = PACKAGE_ID_LINE_RE.sub(
                "**package_id:** <PACKAGE_ID>", output_section, count=1
            )
            semantic_sha256 = sha256_text(output_semantics)
            preserved = semantic_sha256 == source["source_semantic_sha256"]
            semantics_preserved = semantics_preserved and preserved
            section_results.append(
                {
                    **source,
                    "output_sha256": sha256_text(output_section),
                    "output_semantic_sha256": semantic_sha256,
                    "metadata_migrated": test_case_id in migrated_ids,
                    "semantic_body_preserved": preserved,
                }
            )
        payload = {
            **self._prepared_reviewer_rebind_plan,
            "status": "materialized-awaiting-gates",
            "output_draft": relative_path(self.draft_path, self.repo_root),
            "output_draft_sha256": sha256_file(self.draft_path),
            "metadata_migrated_test_case_ids": migrated_ids,
            "all_test_semantics_preserved": semantics_preserved,
            "sections": section_results,
            "deterministic_gates_passed": False,
        }
        write_json(self.reviewer_rebind_path, payload)
        if not semantics_preserved:
            raise RunnerError(
                "Prepared reviewer rebind changed test semantics outside package_id metadata"
            )
        write_json(
            self.evidence_access_path,
            {
                "passed": True,
                "validator": "prepared-reviewer-rebind-evidence-access-v1",
                "writer_llm_started": False,
                "source_draft": self._prepared_reviewer_rebind_plan["source_draft"],
                "source_draft_sha256": self._prepared_reviewer_rebind_plan[
                    "source_draft_sha256"
                ],
                "allowed_mutation": "per-test-case-package-id-only",
                "findings": [],
            },
        )
        append_event(
            self.cycle_dir,
            "prepared_reviewer_rebind_materialized",
            source_draft_sha256=self._prepared_reviewer_rebind_plan[
                "source_draft_sha256"
            ],
            output_draft_sha256=sha256_file(self.draft_path),
            metadata_migrated_test_case_ids=migrated_ids,
            writer_llm_started=False,
        )

    def _materialize_targeted_repair(self, draft_markdown: str) -> ValidationResult:
        path = self.repair_draft_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        if path.exists() or temporary.exists():
            raise RunnerError(
                "targeted repair output already exists; recovery must be explicit"
            )
        try:
            temporary.write_text(draft_markdown.rstrip() + "\n", encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        validation = self._validate_writer_shard(
            shard=self._repair_shard(),
            path=path,
        )
        write_json(self.repair_validator_path, validation.as_dict())
        if not validation.passed:
            return validation
        self._verify_repair_inputs()
        assert self.prepared_repair_draft_path is not None
        source_text = self.prepared_repair_draft_path.read_text(encoding="utf-8")
        source_spans = test_case_section_spans(source_text)
        replacement_spans = test_case_section_spans(path.read_text(encoding="utf-8"))
        replacement_by_id = {
            test_case_id: section.rstrip()
            for test_case_id, _, _, section in replacement_spans
        }
        target_ids = set(self._prepared_repair_plan["target_test_case_ids"])
        expected_package_id = self._prepared_package.package_id if self._prepared_package else ""
        metadata_migrated_test_case_ids: list[str] = []
        prefix = source_text[: source_spans[0][1]] if source_spans else source_text
        chunks = [prefix]
        for test_case_id, _, _, source_section in source_spans:
            if test_case_id not in target_ids:
                source_package_ids = PACKAGE_ID_LINE_RE.findall(source_section)
                if len(source_package_ids) != 1:
                    raise RunnerError(
                        "Prepared targeted repair source section must contain exactly one "
                        f"package_id: {test_case_id}"
                    )
                migrated_section = PACKAGE_ID_LINE_RE.sub(
                    f"**package_id:** {expected_package_id}",
                    source_section,
                    count=1,
                )
                if source_package_ids[0] != expected_package_id:
                    metadata_migrated_test_case_ids.append(test_case_id)
                chunks.append(migrated_section)
                continue
            trailing_match = re.search(r"(\s*)\Z", source_section)
            trailing = trailing_match.group(1) if trailing_match else ""
            chunks.append(replacement_by_id[test_case_id] + (trailing or "\n\n"))
        self._materialize_structured_writer_draft("".join(chunks).rstrip() + "\n")
        output_sections = {
            test_case_id: section
            for test_case_id, _, _, section in test_case_section_spans(
                self.draft_path.read_text(encoding="utf-8")
            )
        }
        section_results = []
        byte_preservation_passed = True
        semantic_preservation_passed = True
        for test_case_id, _, _, source_section in source_spans:
            output_section = output_sections.get(test_case_id, "")
            byte_preserved = sha256_text(source_section) == sha256_text(output_section)
            source_semantics = PACKAGE_ID_LINE_RE.sub(
                "**package_id:** <PACKAGE_ID>", source_section
            )
            output_semantics = PACKAGE_ID_LINE_RE.sub(
                "**package_id:** <PACKAGE_ID>", output_section
            )
            semantic_body_preserved = sha256_text(source_semantics) == sha256_text(
                output_semantics
            )
            preserved = test_case_id in target_ids or semantic_body_preserved
            if test_case_id not in target_ids and not byte_preserved:
                byte_preservation_passed = False
            if test_case_id not in target_ids and not semantic_body_preserved:
                semantic_preservation_passed = False
            section_results.append(
                {
                    "test_case_id": test_case_id,
                    "repair_target": test_case_id in target_ids,
                    "source_sha256": sha256_text(source_section),
                    "output_sha256": sha256_text(output_section),
                    "source_semantic_sha256": sha256_text(source_semantics),
                    "output_semantic_sha256": sha256_text(output_semantics),
                    "byte_preserved": byte_preserved,
                    "semantic_body_preserved": semantic_body_preserved,
                    "metadata_migrated": test_case_id
                    in metadata_migrated_test_case_ids,
                    "preserved": preserved,
                }
            )
        splice = {
            "passed": semantic_preservation_passed,
            "validator": "prepared-targeted-repair-splice-v2",
            "plan_digest": self._prepared_repair_plan["plan_digest"],
            "source_draft_sha256": self._prepared_repair_plan[
                "source_draft_sha256"
            ],
            "replacement_draft_sha256": sha256_file(path),
            "merged_draft_sha256": sha256_file(self.draft_path),
            "target_test_case_ids": list(
                self._prepared_repair_plan["target_test_case_ids"]
            ),
            "preserved_test_case_count": self._prepared_repair_plan[
                "preserved_test_case_count"
            ],
            "all_non_target_sections_byte_preserved": byte_preservation_passed,
            "all_non_target_test_semantics_preserved": semantic_preservation_passed,
            "metadata_migrated_test_case_ids": metadata_migrated_test_case_ids,
            "sections": section_results,
        }
        write_json(self.repair_splice_path, splice)
        if not semantic_preservation_passed:
            return ValidationResult(
                passed=False,
                findings=(
                    {
                        "id": "targeted-repair-non-target-section-changed",
                        "severity": "error",
                    },
                ),
                checked_paths=(relative_path(self.draft_path, self.repo_root),),
                validator="prepared-targeted-repair-splice-v2",
            )
        append_event(
            self.cycle_dir,
            "targeted_repair_spliced",
            plan_digest=self._prepared_repair_plan["plan_digest"],
            target_test_case_ids=self._prepared_repair_plan["target_test_case_ids"],
            preserved_test_case_count=self._prepared_repair_plan[
                "preserved_test_case_count"
            ],
            metadata_migrated_test_case_ids=metadata_migrated_test_case_ids,
            draft_sha256=sha256_file(self.draft_path),
        )
        return validation

    def _materialize_writer_shard(self, stage: str, draft_markdown: str) -> Path:
        path = self.writer_shard_draft_path(stage)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        if path.exists() or temporary.exists():
            raise RunnerError(
                f"writer shard output already exists; recovery must be explicit: {path}"
            )
        try:
            temporary.write_text(draft_markdown.rstrip() + "\n", encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return path

    def _validate_writer_shard(
        self,
        *,
        shard: dict[str, Any],
        path: Path,
    ) -> ValidationResult:
        text = path.read_text(encoding="utf-8")
        findings: list[dict[str, Any]] = []
        headings = re.findall(
            r"(?m)^##\s+(TC-[A-Za-z0-9][A-Za-z0-9_.-]*)\s*$", text
        )
        expected_ids = list(shard["test_case_ids"])
        if headings != expected_ids:
            findings.append(
                {
                    "id": "writer-shard-test-case-set-mismatch",
                    "severity": "error",
                    "message": f"expected={expected_ids}, actual={headings}",
                }
            )
        if re.search(r"(?m)^#\s+", text):
            findings.append(
                {
                    "id": "writer-shard-document-header-forbidden",
                    "severity": "error",
                    "message": "Shard output must contain only assigned H2 test-case sections.",
                }
            )
        if SEED_MARKER in text or "[SEED:" in text:
            findings.append(
                {
                    "id": "writer-shard-seed-placeholder-remains",
                    "severity": "error",
                    "message": "Shard output contains a seed sentinel or placeholder.",
                }
            )
        obligation_set = load_obligations(self._prepared_artifact("atomic-obligations"))
        by_tc: dict[str, list[Any]] = {}
        for item in obligation_set.obligations:
            if item.obligation_id in set(shard["obligation_ids"]):
                by_tc.setdefault(item.planned_test_case_id, []).append(item)
        sections = {
            match.group(1): match.group(2)
            for match in re.finditer(
                r"(?ms)^##\s+(TC-[A-Za-z0-9_.-]+)\s*$\s*(.*?)(?=^##\s+TC-[A-Za-z0-9_.-]+\s*$|\Z)",
                text,
            )
        }
        for test_case_id, obligations in by_tc.items():
            section = sections.get(test_case_id, "")
            for obligation in obligations:
                for reference in (
                    obligation.obligation_id,
                    obligation.traceability_atom_id,
                ):
                    if reference not in section:
                        findings.append(
                            {
                                "id": "writer-shard-traceability-missing",
                                "severity": "error",
                                "test_case_id": test_case_id,
                                "reference": reference,
                                "message": "Assigned obligation/atom is absent from the TC section.",
                            }
                        )
        return ValidationResult(
            passed=not findings,
            findings=tuple(findings),
            checked_paths=(relative_path(path, self.repo_root),),
            validator="prepared-writer-shard-v1",
        )

    def _merge_writer_shards(self, shards: Sequence[dict[str, Any]]) -> None:
        sections: list[str] = []
        for shard in shards:
            path = self.writer_shard_draft_path(str(shard["stage"]))
            if not path.is_file():
                raise RunnerError(f"writer shard output is missing: {path}")
            sections.append(path.read_text(encoding="utf-8").strip())
        self._materialize_structured_writer_draft(
            "# Тест-кейсы\n\n" + "\n\n".join(sections)
        )
        merge = {
            "passed": True,
            "validator": "prepared-writer-shard-merge-v1",
            "plan_digest": self._writer_output_capacity_plan["plan_digest"],
            "shard_count": len(shards),
            "test_case_count": self._writer_output_capacity_plan["test_case_count"],
            "obligation_count": self._writer_output_capacity_plan["obligation_count"],
            "merged_draft": relative_path(self.draft_path, self.repo_root),
            "merged_draft_sha256": sha256_file(self.draft_path),
            "shards": [
                {
                    "stage": shard["stage"],
                    "digest": shard["digest"],
                    "draft": relative_path(
                        self.writer_shard_draft_path(str(shard["stage"])), self.repo_root
                    ),
                    "draft_sha256": sha256_file(
                        self.writer_shard_draft_path(str(shard["stage"]))
                    ),
                }
                for shard in shards
            ],
        }
        write_json(self.runner_output_dir(WRITER_STAGE) / "shard-merge.json", merge)

    def _write_artifact_graph(self, manifest: StageInputManifest) -> None:
        def lifecycle(path: str, kind: str) -> str:
            if kind == "source":
                return "source"
            if "prepared-input" in path or kind in {"instruction", "handoff"}:
                return "prepared"
            if kind in {"review-findings", "quality-gate-bundle"}:
                return "reviewed"
            return "generated"

        input_nodes = []
        for group, artifacts in (
            ("prompt", (manifest.prompt_artifact,)),
            ("instruction", manifest.instruction_artifacts),
            ("source", manifest.source_artifacts),
            ("handoff", manifest.handoff_artifacts),
        ):
            for artifact in artifacts:
                input_nodes.append(
                    {
                        "path": artifact.path,
                        "sha256": artifact.sha256,
                        "kind": artifact.kind,
                        "group": group,
                        "lifecycle": lifecycle(artifact.path, artifact.kind),
                        "producer": "upstream" if group != "prompt" else "runner",
                        "consumers": [manifest.role, "runner"],
                    }
                )
        output_nodes = [
            {
                "path": item.path,
                "kind": item.kind,
                "lifecycle": lifecycle(item.path, item.kind),
                "producer": item.producer,
                "consumers": ["runner", "reviewer"] if manifest.role == "writer" else ["runner"],
                "required": item.required,
            }
            for item in manifest.expected_outputs
        ]
        payload: dict[str, Any] = {
            "version": 1,
            "cycle_id": manifest.cycle_id,
            "stage_id": manifest.stage_id,
            "role": manifest.role,
            "context_profile": self._prepared_context_profile(),
            "input_digest": manifest.input_digest,
            "input_nodes": input_nodes,
            "output_nodes": output_nodes,
            "access_policy": {
                "sandbox": manifest.sandbox_policy,
                "allowed_write_roots": list(manifest.allowed_write_roots),
                "forbidden_write_roots": list(manifest.forbidden_write_roots),
                "fallback_policy": (
                    self._prepared_package.fallback_policy
                    if self._prepared_package is not None
                    else "explicit-inputs-only"
                ),
            },
        }
        payload["graph_digest"] = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        write_json(self.artifact_graph_path(manifest.stage_id), payload)

    def _writer_prompt(self) -> str:
        if self._uses_targeted_prepared_repair():
            return self._targeted_repair_prompt()
        if self._uses_structured_prepared_writer() and self.prepared_package_path is not None:
            prompt = "\n".join(
                [
                    "# Codex exec prepared writer structured path",
                    "",
                    "The upstream package already applied the full source, scope and writer policy.",
                    "Use only the embedded Prepared Writer Runtime Profile below; do not load the full ft-test-case-writer skill or reread package/project reference files.",
                    "This stage is read-only. Do not call shell or file tools and do not create or modify workspace files.",
                    "Return the complete unsigned draft inside the schema-constrained final JSON object. The runner alone materializes and validates draft.md.",
                    "Do not read existing/generated test cases, earlier cycle artifacts or production test-cases as evidence.",
                    "FT-first boundary: a portable synthetic value, relative date or runtime-selected integration response with source-defined observable properties is a reproducible fixture. Do not require a stand record ID, locator, token, session or prerecorded provider response.",
                    "Return blocked-input only when the embedded evidence cannot define the test intent or observable oracle without invention. Do not open a full source in this mode.",
                    "",
                    self._prepared_writer_payload(structured=True),
                    "",
                    "Return exactly one JSON object and no commentary outside it.",
                    "Use status=draft-ready with a complete draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one blocking reason.",
                    "",
                ]
            )
            if self._is_prepared_standard():
                self._enforce_prepared_standard_context_budget(role="writer", prompt=prompt)
            return prompt
        if self._is_prepared_fast() and self.prepared_package_path is not None:
            return "\n".join(
                [
                    "# Codex exec prepared writer fast path",
                    "",
                    "The upstream package already applied the full source, scope and writer policy.",
                    "Use only the embedded Prepared Writer Runtime Profile below; do not load the full ft-test-case-writer skill or reread package/project reference files.",
                    "Do not read existing/generated test cases or earlier cycle artifacts as evidence.",
                    f"Write a structurally complete unsigned draft first and only to `{relative_path(self.draft_path, self.repo_root)}`.",
                    "That output file does not exist yet. Create it as your first file write; do not try to update it in place.",
                    "Do not write under a production test-cases directory and do not promote the draft.",
                    "Use registered full sources only for a single unresolved ATOM locator and record targeted_source_fallback.",
                    "",
                    self._prepared_writer_payload(),
                    "",
                    "Exit only after the draft file is fully written. A chat response without the file is a failed stage.",
                    "",
                ]
            )
        if self._is_prepared_standard() and self.prepared_package_path is not None:
            prompt = "\n".join(
                [
                    "# Codex exec prepared-standard writer stage contract",
                    "",
                    f"Instruction-loading scenario: `{self._standard_scenario('writer')}`.",
                    f"Run `python scripts/resolve_instruction_context.py --scenario {self._standard_scenario('writer')} --budget-report --fail-on-budget` and verify it matches the runner-selected files below.",
                    "Read every selected standard instruction file before making domain decisions.",
                    "The prepared package is a compact source-backed transport, not a fast semantic profile.",
                    "Use the verified inline projection as primary evidence. Do not repeat source discovery or broad document analysis.",
                    "A registered full source may be inspected only for a named OBL/ATOM whose inline evidence is insufficient; record the source path, locator and reason in the final summary.",
                    "Angle-bracket test-data placeholders are forbidden. Bind concrete values or a named reproducible fixture with explicit selection/setup conditions; return blocked if neither is source-safe.",
                    "A portable synthetic value, relative date or runtime-selected integration response with source-defined observable properties is source-safe; stand IDs, locators, tokens, sessions and prerecorded provider responses are deferred to UI-prep.",
                    "Do not use generated test cases, previous cycles or canary artifacts as requirement evidence.",
                    "Do not write under any production test-cases directory.",
                    f"Write the complete unsigned draft only to `{relative_path(self.draft_path, self.repo_root)}`.",
                    "",
                    "## Standard instruction files",
                    *[
                        f"- `{relative_path(path, self.repo_root)}`"
                        for path in self._standard_instruction_paths("writer")
                    ],
                    "",
                    self._prepared_standard_writer_payload(),
                    "",
                    "Exit only after the complete draft is written. A chat response without the file is a failed stage.",
                    "",
                ]
            )
            self._enforce_prepared_standard_context_budget(role="writer", prompt=prompt)
            return prompt
        return "\n".join(
            [
                "# Codex exec writer stage contract",
                "",
                f"Instruction-loading scenario: `{self._standard_scenario('writer')}`.",
                f"Run `python scripts/resolve_instruction_context.py --scenario {self._standard_scenario('writer')} --budget-report --fail-on-budget` and verify it matches the runner-selected files below.",
                "Read every selected instruction file before making domain decisions.",
                "Record the resolver command, passing budget and selected files in the stage evidence or final summary.",
                "",
                "Work only from the explicit source and handoff files below.",
                "Do not use previously generated test cases as requirement evidence.",
                "Do not write under any production test-cases directory.",
                f"Write the complete unsigned draft only to `{relative_path(self.draft_path, self.repo_root)}`.",
                "Do not promote or rename the draft to a final artifact.",
                "",
                "## Instruction files",
                *[
                    f"- `{relative_path(path, self.repo_root)}`"
                    for path in self._standard_instruction_paths("writer")
                ],
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
        if self._uses_compact_prepared_reviewer() and self.prepared_package_path is not None:
            prompt = "\n".join(
                [
                    (
                        "# Codex exec prepared reviewer fast path"
                        if self._is_prepared_fast()
                        else "# Codex exec prepared-standard reviewer compact path"
                    ),
                    "",
                    "The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.",
                    "Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.",
                    "This stage is read-only. Do not modify or create any workspace file.",
                    "No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.",
                    "",
                    self._prepared_reviewer_payload(),
                    "",
                ]
            )
            if self._is_prepared_standard():
                self._enforce_prepared_standard_context_budget(role="reviewer", prompt=prompt)
            else:
                prompt_bytes = len(prompt.encode("utf-8"))
                if prompt_bytes > self.prepared_reviewer_prompt_max_bytes:
                    raise RunnerError(
                        "blocked-prepared-reviewer-prompt-budget: "
                        f"prompt bytes {prompt_bytes} exceed {self.prepared_reviewer_prompt_max_bytes}; "
                        "route to standard reviewer or reduce the eligible scope"
                    )
            return prompt
        if self._is_prepared_standard() and self.prepared_package_path is not None:
            prompt = "\n".join(
                [
                    "# Codex exec prepared-standard reviewer stage contract",
                    "",
                    f"Instruction-loading scenario: `{self._standard_scenario('reviewer')}`.",
                    f"Run `python scripts/resolve_instruction_context.py --scenario {self._standard_scenario('reviewer')} --budget-report --fail-on-budget` and verify it matches the runner-selected files below.",
                    "Read every selected standard reviewer instruction file before making domain decisions.",
                    "This is a full standard semantic review over compact verified inputs, not the prepared fast reviewer profile.",
                    "This stage is read-only. Do not modify or create workspace files.",
                    "Use the inline source evidence first. Inspect a registered full source only for a named disputed OBL/ATOM and record the path, locator and reason in the final summary.",
                    "Do not read production test cases, previous cycles or generated artifacts as requirement evidence.",
                    "",
                    "## Standard instruction files",
                    *[
                        f"- `{relative_path(path, self.repo_root)}`"
                        for path in self._standard_instruction_paths("reviewer")
                    ],
                    "",
                    self._prepared_standard_reviewer_payload(),
                    "",
                ]
            )
            self._enforce_prepared_standard_context_budget(role="reviewer", prompt=prompt)
            return prompt
        return "\n".join(
            [
                "# Codex exec reviewer stage contract",
                "",
                f"Instruction-loading scenario: `{self._standard_scenario('reviewer')}`.",
                f"Run `python scripts/resolve_instruction_context.py --scenario {self._standard_scenario('reviewer')} --budget-report --fail-on-budget` and verify it matches the runner-selected files below.",
                "Read every selected instruction file before making domain decisions.",
                "Record the resolver command, passing budget and selected files in the final review summary.",
                "",
                "This stage is read-only. Do not modify any workspace file.",
                "Review only the explicit inputs listed below.",
                f"Writer draft: `{relative_path(self.draft_path, self.repo_root)}`",
                f"Deterministic validator report: `{relative_path(self.validator_path, self.repo_root)}`",
                "",
                "## Instruction files",
                *[
                    f"- `{relative_path(path, self.repo_root)}`"
                    for path in self._standard_instruction_paths("reviewer")
                ],
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
        context_budget = self._context_budget_reports.get(stage)
        if context_budget is not None:
            write_json(self.context_budget_path(stage), context_budget)
        if role == "writer":
            self.stage_output_dir(stage).mkdir(parents=True)
            if self._prepared_package is not None:
                self.draft_seed_path.parent.mkdir(parents=True, exist_ok=True)
                if not self.draft_seed_path.exists():
                    self.draft_seed_path.write_text(self._draft_seed_text(), encoding="utf-8")
                self._draft_seed_sha256 = sha256_file(self.draft_seed_path)
            if self._uses_structured_prepared_writer():
                if not self.writer_schema_path.exists():
                    write_json(self.writer_schema_path, self._writer_contract_schema())
        else:
            write_json(self.reviewer_schema_path, self._review_contract_schema())
        manifest = self._build_stage_manifest(stage=stage, role=role, prompt_path=prompt_path)
        store = StageArtifactStore(self.repo_root)
        try:
            store.write_manifest(StageAttemptPaths.from_manifest(self.repo_root, manifest), manifest)
        except StageRuntimeError as exc:
            raise RunnerError(f"cannot persist v2 stage manifest: {exc}") from exc
        self._manifests[stage] = manifest
        self._write_artifact_graph(manifest)

        stdout_path = self.runner_output_dir(stage) / "stdout.txt"
        stderr_path = self.runner_output_dir(stage) / "stderr.txt"
        events_path = self.runner_output_dir(stage) / "events.ndjson"
        command = self.command_config.build(
            role=role,
            cwd=self.repo_root,
            last_message_path=last_message_path,
            output_schema_path=(
                self.reviewer_schema_path
                if role == "reviewer"
                else self.writer_schema_path
                if self._uses_structured_prepared_writer()
                else None
            ),
            sandbox_override=(
                self.command_config.reviewer_sandbox
                if role == "writer" and self._uses_structured_prepared_writer()
                else None
            ),
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
            progress_path=(
                self.draft_path
                if role == "writer"
                and self._prepared_package
                and not self._uses_structured_prepared_writer()
                else None
            ),
            progress_forbidden_marker=(SEED_MARKER if role == "writer" else ""),
            first_artifact_deadline_seconds=(
                self.writer_first_artifact_deadline_seconds
                if role == "writer"
                and self._prepared_package
                and not self._uses_structured_prepared_writer()
                else None
            ),
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
            first_artifact_deadline_seconds=(
                self.writer_first_artifact_deadline_seconds
                if role == "writer"
                and self._prepared_package
                and not self._uses_structured_prepared_writer()
                else None
            ),
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
            timed_out=(
                result.timed_out
                or result.idle_timed_out
                or result.first_artifact_deadline_exceeded
            ),
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
            first_artifact_deadline_exceeded=result.first_artifact_deadline_exceeded,
            command_count=result.command_count,
            first_output_seconds=result.first_output_seconds,
            first_artifact_seconds=result.first_artifact_seconds,
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
            ExpectedOutput(
                path=relative_path(self.artifact_graph_path(stage), self.repo_root),
                kind="artifact-graph",
                producer="runner",
            ),
        ]
        if self._prepared_package is not None and self.prepared_package_path is not None:
            instruction_paths = list(self._prepared_role_instruction_paths(role))
            source_paths = [self._prepared_artifact("source-evidence")]
            handoff_paths = [
                self.prepared_package_path,
                self._prepared_artifact("atomic-obligations"),
            ]
            if (
                self._is_prepared_standard()
                and self.prepared_standard_writer_mode == "assisted"
            ):
                handoff_paths.append(self._prepared_artifact("stage-instructions"))
            if role == "writer":
                handoff_paths.append(self.draft_seed_path)
                if self._uses_structured_prepared_writer():
                    handoff_paths.append(self.writer_schema_path)
                if self._uses_targeted_prepared_repair():
                    assert self.prepared_repair_draft_path is not None
                    assert self.prepared_repair_findings_path is not None
                    handoff_paths.extend(
                        (
                            self.prepared_repair_draft_path,
                            self.prepared_repair_findings_path,
                        )
                    )
        else:
            instruction_paths = list(self._standard_instruction_paths(role))
            source_paths = list(self.source_files)
            handoff_paths = list(self.handoff_files)
        allowed_write_roots: list[str] = []
        if role == "writer" and (
            stage == WRITER_STAGE or not self._uses_sharded_prepared_writer()
        ):
            expected_outputs.extend(
                [
                    ExpectedOutput(
                        path=relative_path(self.draft_path, self.repo_root),
                        kind="test-case-draft",
                        producer=(
                            "runner" if self._uses_structured_prepared_writer() else "stage"
                        ),
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
                        path=relative_path(self.semantic_overlap_path, self.repo_root),
                        kind="semantic-overlap-diagnostic",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(self.quality_gate_bundle_path, self.repo_root),
                        kind="quality-gate-bundle",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(self.calibration_lifecycle_path, self.repo_root),
                        kind="calibration-lifecycle",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(self.dictionary_projection_path, self.repo_root),
                        kind="dictionary-projection",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(self.seed_gate_path, self.repo_root),
                        kind="seed-gate",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(self.evidence_access_path, self.repo_root),
                        kind="evidence-access-report",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(
                            (
                                self.writer_result_path_for(stage)
                                if self._uses_structured_prepared_writer()
                                else self.stage_output_dir(stage) / "last-message.txt"
                            ),
                            self.repo_root,
                        ),
                        kind=(
                            "writer-result"
                            if self._uses_structured_prepared_writer()
                            else "last-message"
                        ),
                        producer=(
                            "runner" if self._uses_structured_prepared_writer() else "stage"
                        ),
                        required=False,
                    ),
                ]
            )
            if not self._uses_structured_prepared_writer():
                allowed_write_roots.append(
                    relative_path(self.stage_output_dir(stage), self.repo_root)
                )
            uses_sharded_writer = getattr(
                self, "_uses_sharded_prepared_writer", lambda: False
            )()
            if uses_sharded_writer:
                expected_outputs.extend(
                    [
                        ExpectedOutput(
                            path=relative_path(
                                self.writer_shard_draft_path(stage), self.repo_root
                            ),
                            kind="writer-shard-draft",
                            producer="runner",
                        ),
                        ExpectedOutput(
                            path=relative_path(
                                self.runner_output_dir(stage) / "shard-validator.json",
                                self.repo_root,
                            ),
                            kind="writer-shard-validator",
                            producer="runner",
                        ),
                        ExpectedOutput(
                            path=relative_path(
                                self.runner_output_dir(stage) / "shard-merge.json",
                                self.repo_root,
                            ),
                            kind="writer-shard-merge",
                            producer="runner",
                        ),
                    ]
                )
            if self._uses_targeted_prepared_repair():
                expected_outputs.extend(
                    [
                        ExpectedOutput(
                            path=relative_path(self.repair_draft_path, self.repo_root),
                            kind="writer-targeted-repair",
                            producer="runner",
                        ),
                        ExpectedOutput(
                            path=relative_path(
                                self.repair_validator_path, self.repo_root
                            ),
                            kind="writer-targeted-repair-validator",
                            producer="runner",
                        ),
                        ExpectedOutput(
                            path=relative_path(self.repair_splice_path, self.repo_root),
                            kind="writer-targeted-repair-splice",
                            producer="runner",
                        ),
                        ExpectedOutput(
                            path=relative_path(
                                self.package_metadata_gate_path, self.repo_root
                            ),
                            kind="package-metadata-gate",
                            producer="runner",
                        ),
                    ]
                )
        elif role == "writer":
            expected_outputs.extend(
                [
                    ExpectedOutput(
                        path=relative_path(
                            self.writer_shard_draft_path(stage), self.repo_root
                        ),
                        kind="writer-shard-draft",
                        producer="runner",
                    ),
                    ExpectedOutput(
                        path=relative_path(
                            self.writer_result_path_for(stage), self.repo_root
                        ),
                        kind="writer-result",
                        producer="runner",
                        required=False,
                    ),
                    ExpectedOutput(
                        path=relative_path(
                            self.runner_output_dir(stage) / "shard-validator.json",
                            self.repo_root,
                        ),
                        kind="writer-shard-validator",
                        producer="runner",
                    ),
                    ExpectedOutput(
                        path=relative_path(
                            self.runner_output_dir(stage) / "evidence-access-report.json",
                            self.repo_root,
                        ),
                        kind="evidence-access-report",
                        producer="runner",
                    ),
                ]
            )
        else:
            handoff_paths.extend((self.draft_path, self.validator_path))
            if self._prepared_package is not None:
                handoff_paths.extend(
                    (
                        self.obligation_gate_path,
                        self.semantic_overlap_path,
                        self.quality_gate_bundle_path,
                        self.calibration_lifecycle_path,
                        self.dictionary_projection_path,
                        self.seed_gate_path,
                        self.evidence_access_path,
                    )
                )
                if self.package_metadata_gate_path.is_file():
                    handoff_paths.append(self.package_metadata_gate_path)
                if self.reviewer_rebind_path.is_file():
                    handoff_paths.append(self.reviewer_rebind_path)
            handoff_paths.append(self.reviewer_schema_path)
            expected_outputs.append(
                ExpectedOutput(
                    path=relative_path(self.reviewer_findings_path, self.repo_root),
                    kind="review-findings",
                    producer="runner",
                )
            )
            if self._prepared_package is not None:
                expected_outputs.append(
                    ExpectedOutput(
                        path=relative_path(
                            self.reviewer_evidence_access_path, self.repo_root
                        ),
                        kind="evidence-access-report",
                        producer="runner",
                        required=False,
                    )
                )
        if self._is_prepared_standard():
            expected_outputs.append(
                ExpectedOutput(
                    path=relative_path(self.context_budget_path(stage), self.repo_root),
                    kind="context-budget",
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
                    "writer.session_prepared_targeted_repair"
                    if self._uses_targeted_prepared_repair()
                    else (
                        "writer.session_prepared_initial_draft"
                        if self._is_prepared_fast()
                        else (
                            "writer.session_prepared_standard_structured"
                            if self._uses_structured_prepared_writer()
                            else self._standard_scenario("writer")
                        )
                    )
                )
                if role == "writer"
                else (
                    "reviewer.session_prepared_semantic"
                    if self._is_prepared_fast()
                    else (
                        "reviewer.session_prepared_standard_semantic"
                        if self._uses_compact_prepared_reviewer()
                        else self._standard_scenario("reviewer")
                    )
                )
            ),
            semantic_round=0,
            sandbox_policy=(
                "read_only"
                if role == "reviewer" or self._uses_structured_prepared_writer()
                else "workspace_write"
            ),
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

    def _writer_contract_schema(self) -> dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "contract_version",
                "status",
                "draft_markdown",
                "blocking_reasons",
            ],
            "properties": {
                "contract_version": {"type": "integer", "const": 1},
                "status": {
                    "type": "string",
                    "enum": ["draft-ready", "blocked-input"],
                },
                "draft_markdown": {
                    "type": "string",
                    "maxLength": MAX_STRUCTURED_WRITER_DRAFT_BYTES,
                },
                "blocking_reasons": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
            },
        }

    def _review_contract_schema(
        self,
        *,
        obligations_override: Sequence[Any] | None = None,
    ) -> dict[str, Any]:
        if self._prepared_package is not None:
            obligations = (
                list(obligations_override)
                if obligations_override is not None
                else load_obligations(
                    self._prepared_artifact("atomic-obligations")
                ).obligations
            )
            uses_generic_schema = getattr(
                self, "_uses_generic_bounded_reviewer_schema", lambda: False
            )()
            if uses_generic_schema:
                grouped_variants: list[dict[str, Any]] = []
                for is_testable in (True, False):
                    selected_ids = [
                        obligation.obligation_id
                        for obligation in obligations
                        if (obligation.coverage_status == "testable") is is_testable
                    ]
                    if not selected_ids:
                        continue
                    test_case_ids_schema: dict[str, Any] = {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": r"^TC-[A-Za-z0-9][A-Za-z0-9_.-]*$",
                        },
                    }
                    if not is_testable:
                        test_case_ids_schema["maxItems"] = 0
                    grouped_variants.append(
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "obligation_id",
                                "atom_id",
                                "verdict",
                                "test_case_ids",
                                "note",
                            ],
                            "properties": {
                                "obligation_id": {
                                    "type": "string",
                                    "enum": selected_ids,
                                },
                                "atom_id": {
                                    "type": "string",
                                    "pattern": r"^ATOM-[A-Za-z0-9._-]+$",
                                },
                                "verdict": {
                                    "type": "string",
                                    "enum": (
                                        ["covered", "incorrect", "missing"]
                                        if is_testable
                                        else ["gap-preserved", "invented-coverage"]
                                    ),
                                },
                                "test_case_ids": test_case_ids_schema,
                                "note": {"type": "string", "minLength": 1},
                            },
                        }
                    )
                obligation_review_item = (
                    grouped_variants[0]
                    if len(grouped_variants) == 1
                    else {"anyOf": grouped_variants}
                )
            else:
                variants: list[dict[str, Any]] = []
                for obligation in obligations:
                    is_testable = obligation.coverage_status == "testable"
                    test_case_ids_schema: dict[str, Any] = {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": r"^TC-[A-Za-z0-9][A-Za-z0-9_.-]*$",
                        },
                    }
                    if not is_testable:
                        test_case_ids_schema["maxItems"] = 0
                    variants.append(
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "obligation_id",
                                "atom_id",
                                "verdict",
                                "test_case_ids",
                                "note",
                            ],
                            "properties": {
                                "obligation_id": {
                                    "type": "string",
                                    "const": obligation.obligation_id,
                                },
                                "atom_id": {
                                    "type": "string",
                                    "const": obligation.traceability_atom_id,
                                },
                                "verdict": {
                                    "type": "string",
                                    "enum": (
                                        ["covered", "incorrect", "missing"]
                                        if is_testable
                                        else ["gap-preserved", "invented-coverage"]
                                    ),
                                },
                                "test_case_ids": test_case_ids_schema,
                                "note": {"type": "string", "minLength": 1},
                            },
                        }
                    )
                obligation_review_item = {"anyOf": variants}
            return {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "contract_version",
                    "decision",
                    "reviewed_draft_sha256",
                    "obligation_reviews",
                    "findings",
                    "summary",
                ],
                "properties": {
                    "contract_version": {"type": "integer", "const": 2},
                    "decision": {"type": "string", "enum": sorted(REVIEW_DECISIONS)},
                    "reviewed_draft_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "obligation_reviews": {
                        "type": "array",
                        "minItems": len(obligations),
                        "maxItems": len(obligations),
                        "items": obligation_review_item,
                    },
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "id",
                                "severity",
                                "category",
                                "atom_ids",
                                "test_case_ids",
                                "problem",
                                "required_change",
                            ],
                            "properties": {
                                "id": {"type": "string", "minLength": 1},
                                "severity": {
                                    "type": "string",
                                    "enum": sorted(REVIEW_FINDING_SEVERITIES),
                                },
                                "category": {
                                    "type": "string",
                                    "enum": sorted(REVIEW_FINDING_CATEGORIES),
                                },
                                "atom_ids": {
                                    "type": "array",
                                    "items": {"type": "string", "minLength": 1},
                                },
                                "test_case_ids": {
                                    "type": "array",
                                    "items": {"type": "string", "minLength": 1},
                                },
                                "problem": {"type": "string", "minLength": 1},
                                "required_change": {"type": "string", "minLength": 1},
                            },
                        },
                    },
                    "summary": {"type": "string", "minLength": 1},
                },
            }
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
            "first_artifact_deadline_exceeded": result.first_artifact_deadline_exceeded,
            "launch_error": result.launch_error,
            "duration_seconds": round(result.duration_seconds, 3),
            "command_count": result.command_count,
            "first_output_seconds": result.first_output_seconds,
            "first_artifact_seconds": result.first_artifact_seconds,
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
        if artifacts.get("_runner_owned_rebind"):
            payload = dict(self._prepared_reviewer_rebind_plan)
            if self.reviewer_rebind_path.is_file():
                try:
                    payload.update(
                        json.loads(self.reviewer_rebind_path.read_text(encoding="utf-8"))
                    )
                except json.JSONDecodeError:
                    pass
            payload.update(
                {
                    "status": status,
                    "passed": False,
                    "deterministic_gates_passed": False,
                    "blocking_reasons": list(reasons),
                    "writer_llm_started": False,
                }
            )
            if validation is not None:
                payload["blocking_validator"] = validation.validator
            write_json(self.reviewer_rebind_path, payload)
            state["workflow_status"] = status
            state["stage_status"] = "blocked-input"
            state["current_stage"] = "reviewer-rebind"
            state["writer_stage_status"] = "skipped-reviewer-rebind"
            state["reviewer_rebind_status"] = status
            state["blocking_reasons"] = list(reasons)
            state["active_transition_prompt"] = ""
            self._write_state(state)
            append_event(
                self.cycle_dir,
                "reviewer_rebind_blocked",
                status=status,
                reasons=list(reasons),
            )
            return self._result(state)
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
        self._promotion_plan(production_before, expected_draft_sha256=expected_draft_sha256)
        self.final_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.final_path.with_suffix(self.final_path.suffix + ".promotion-tmp")
        try:
            shutil.copyfile(self.draft_path, temporary_path)
            if sha256_file(temporary_path) != expected_draft_sha256:
                raise RunnerError("promotion copy hash differs from the validated writer draft")
            temporary_path.replace(self.final_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def _promotion_plan(
        self, production_before: dict[str, str], *, expected_draft_sha256: str
    ) -> dict[str, Any]:
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
        return {
            "status": "passed",
            "draft_path": relative_path(self.draft_path, self.repo_root),
            "draft_sha256": actual_draft_sha256,
            "destination_path": relative_path(self.final_path, self.repo_root),
            "destination_exists": self.final_path.exists(),
            "overwrite_allowed": False,
            "production_changes": [],
            "write_performed": False,
        }

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


def file_change_count_from_events(text: str) -> int:
    count = 0
    for raw_line in text.splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "file_change":
            count += 1
    return count


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


def parse_prepared_writer_contract(text: str) -> WriterContract:
    candidate = text.strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(\{.*\})\s*```",
        candidate,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        candidate = fenced.group(1)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise RunnerError(
            f"structured writer final output is not valid JSON: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise RunnerError("structured writer final output must be one JSON object")
    expected = {"contract_version", "status", "draft_markdown", "blocking_reasons"}
    if set(payload) != expected:
        missing = sorted(expected - set(payload))
        unknown = sorted(set(payload) - expected)
        raise RunnerError(
            "structured writer final output has invalid fields: "
            f"missing={missing}, unknown={unknown}"
        )
    if payload.get("contract_version") != 1:
        raise RunnerError("structured writer contract_version must be 1")
    status = payload.get("status")
    if status not in {"draft-ready", "blocked-input"}:
        raise RunnerError(
            "structured writer status must be draft-ready or blocked-input"
        )
    draft_markdown = payload.get("draft_markdown")
    if not isinstance(draft_markdown, str):
        raise RunnerError("structured writer draft_markdown must be a string")
    reasons = payload.get("blocking_reasons")
    if not isinstance(reasons, list) or any(
        not isinstance(item, str) or not item.strip() for item in reasons
    ):
        raise RunnerError(
            "structured writer blocking_reasons must be an array of non-empty strings"
        )
    normalized_reasons = tuple(item.strip() for item in reasons)
    if len(normalized_reasons) != len(set(normalized_reasons)):
        raise RunnerError("structured writer blocking_reasons must not contain duplicates")
    if status == "draft-ready":
        if not draft_markdown.strip():
            raise RunnerError("draft-ready structured writer contract requires draft_markdown")
        if normalized_reasons:
            raise RunnerError(
                "draft-ready structured writer contract requires empty blocking_reasons"
            )
        if len(draft_markdown.encode("utf-8")) > MAX_STRUCTURED_WRITER_DRAFT_BYTES:
            raise RunnerError(
                "structured writer draft_markdown exceeds the byte budget"
            )
    else:
        if draft_markdown:
            raise RunnerError(
                "blocked-input structured writer contract requires empty draft_markdown"
            )
        if not normalized_reasons:
            raise RunnerError(
                "blocked-input structured writer contract requires blocking_reasons"
            )
    return WriterContract(
        contract_version=1,
        status=str(status),
        draft_markdown=draft_markdown,
        blocking_reasons=normalized_reasons,
    )


def parse_review_contract(text: str) -> ReviewContract:
    payload = _review_contract_payload(text)
    if set(payload) != {"decision", "findings_markdown"}:
        raise RunnerError("reviewer final output must contain exactly decision and findings_markdown")
    decision = str(payload.get("decision") or "").strip()
    findings = payload.get("findings_markdown")
    if decision not in REVIEW_DECISIONS:
        raise RunnerError(f"reviewer decision must be one of {sorted(REVIEW_DECISIONS)}")
    if not isinstance(findings, str) or not findings.strip():
        raise RunnerError("reviewer findings_markdown must be a non-empty string")
    return ReviewContract(decision=decision, findings_markdown=findings)


def _review_contract_payload(text: str) -> dict[str, Any]:
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
    return payload


def _required_text(payload: dict[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RunnerError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _string_list(payload: dict[str, Any], key: str, context: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise RunnerError(f"{context}.{key} must be an array of non-empty strings")
    normalized = tuple(item.strip() for item in value)
    if len(normalized) != len(set(normalized)):
        raise RunnerError(f"{context}.{key} must not contain duplicates")
    return normalized


def parse_prepared_review_contract(
    text: str,
    *,
    expected_obligations: Sequence[Any],
    expected_draft_sha256: str,
    draft_text: str,
) -> ReviewContract:
    payload = _review_contract_payload(text)
    expected_fields = {
        "contract_version",
        "decision",
        "reviewed_draft_sha256",
        "obligation_reviews",
        "findings",
        "summary",
    }
    if set(payload) != expected_fields:
        raise RunnerError(
            "prepared reviewer final output must contain exactly contract_version, decision, "
            "reviewed_draft_sha256, obligation_reviews, findings and summary"
        )
    if payload.get("contract_version") != 2:
        raise RunnerError("prepared reviewer contract_version must equal 2")
    decision = _required_text(payload, "decision", "review")
    if decision not in REVIEW_DECISIONS:
        raise RunnerError(f"reviewer decision must be one of {sorted(REVIEW_DECISIONS)}")
    reviewed_hash = _required_text(payload, "reviewed_draft_sha256", "review")
    if reviewed_hash != expected_draft_sha256:
        raise RunnerError(
            "prepared reviewer draft hash mismatch: "
            f"expected {expected_draft_sha256}, got {reviewed_hash}"
        )

    raw_reviews = payload.get("obligation_reviews")
    if not isinstance(raw_reviews, list) or not raw_reviews:
        raise RunnerError("prepared reviewer obligation_reviews must be a non-empty array")
    reviews: list[ObligationReview] = []
    for index, item in enumerate(raw_reviews):
        context = f"obligation_reviews[{index}]"
        if not isinstance(item, dict) or set(item) != {
            "obligation_id",
            "atom_id",
            "verdict",
            "test_case_ids",
            "note",
        }:
            raise RunnerError(f"{context} has invalid fields")
        verdict = _required_text(item, "verdict", context)
        if verdict not in PREPARED_REVIEW_VERDICTS:
            raise RunnerError(f"{context}.verdict is not allowed: {verdict}")
        reviews.append(
            ObligationReview(
                obligation_id=_required_text(item, "obligation_id", context),
                atom_id=_required_text(item, "atom_id", context),
                verdict=verdict,
                test_case_ids=_string_list(item, "test_case_ids", context),
                note=_required_text(item, "note", context),
            )
        )

    expected_by_id = {item.obligation_id: item for item in expected_obligations}
    review_ids = [item.obligation_id for item in reviews]
    if len(review_ids) != len(set(review_ids)):
        raise RunnerError("prepared reviewer obligation_reviews contain duplicate obligation ids")
    if set(review_ids) != set(expected_by_id):
        missing = sorted(set(expected_by_id) - set(review_ids))
        unknown = sorted(set(review_ids) - set(expected_by_id))
        raise RunnerError(
            f"prepared reviewer obligation set mismatch: missing={missing}, unknown={unknown}"
        )
    for review in reviews:
        expected_atom_id = expected_by_id[review.obligation_id].traceability_atom_id
        if review.atom_id != expected_atom_id:
            raise RunnerError(
                "prepared reviewer obligation-to-atom mismatch: "
                f"obligation_id={review.obligation_id}, expected={expected_atom_id}, "
                f"got={review.atom_id}"
            )

    known_atom_ids = {
        item.traceability_atom_id for item in expected_obligations
    }

    known_tc_ids = set(
        re.findall(r"^##\s+(TC-[A-Za-z0-9][A-Za-z0-9_.-]*)\b", draft_text, flags=re.MULTILINE)
    )
    findings_payload = payload.get("findings")
    if not isinstance(findings_payload, list):
        raise RunnerError("prepared reviewer findings must be an array")
    findings: list[ReviewFinding] = []
    finding_ids: set[str] = set()
    for index, item in enumerate(findings_payload):
        context = f"findings[{index}]"
        required = {
            "id",
            "severity",
            "category",
            "atom_ids",
            "test_case_ids",
            "problem",
            "required_change",
        }
        if not isinstance(item, dict) or set(item) != required:
            raise RunnerError(f"{context} has invalid fields")
        finding_id = _required_text(item, "id", context)
        if finding_id in finding_ids:
            raise RunnerError("prepared reviewer findings contain duplicate ids")
        finding_ids.add(finding_id)
        severity = _required_text(item, "severity", context)
        category = _required_text(item, "category", context)
        if severity not in REVIEW_FINDING_SEVERITIES:
            raise RunnerError(f"{context}.severity is not allowed: {severity}")
        if category not in REVIEW_FINDING_CATEGORIES:
            raise RunnerError(f"{context}.category is not allowed: {category}")
        atom_ids = _string_list(item, "atom_ids", context)
        test_case_ids = _string_list(item, "test_case_ids", context)
        if set(atom_ids) - known_atom_ids:
            raise RunnerError(f"{context} references unknown atom ids")
        if set(test_case_ids) - known_tc_ids:
            raise RunnerError(f"{context} references unknown test-case ids")
        findings.append(
            ReviewFinding(
                finding_id=finding_id,
                severity=severity,
                category=category,
                atom_ids=atom_ids,
                test_case_ids=test_case_ids,
                problem=_required_text(item, "problem", context),
                required_change=_required_text(item, "required_change", context),
            )
        )

    blocking_atoms = {
        atom_id
        for finding in findings
        if finding.severity == "error"
        for atom_id in finding.atom_ids
    }
    for review in reviews:
        obligation = expected_by_id[review.obligation_id]
        if set(review.test_case_ids) - known_tc_ids:
            raise RunnerError(
                f"obligation review {review.obligation_id} references unknown test-case ids"
            )
        if obligation.coverage_status == "testable":
            if review.verdict not in {"covered", "missing", "incorrect"}:
                raise RunnerError(
                    f"testable obligation {review.obligation_id} has incompatible verdict {review.verdict}"
                )
            if review.verdict == "covered" and not review.test_case_ids:
                raise RunnerError(
                    f"covered obligation {review.obligation_id} must reference at least one test case"
                )
        else:
            if review.verdict not in {"gap-preserved", "invented-coverage"}:
                raise RunnerError(
                    f"non-testable obligation {review.obligation_id} has incompatible verdict {review.verdict}"
                )
            if review.verdict == "gap-preserved" and review.test_case_ids:
                raise RunnerError(
                    f"gap-preserved obligation {review.obligation_id} must not reference executable test cases"
                )
        if review.verdict in {"missing", "incorrect", "invented-coverage"} and (
            review.atom_id not in blocking_atoms
        ):
            raise RunnerError(
                f"blocking verdict for {review.atom_id} requires an error finding linked to the atom"
            )

    has_error = any(item.severity == "error" for item in findings)
    all_terminal_pass = all(
        review.verdict in {"covered", "gap-preserved"} for review in reviews
    )
    if decision == "accepted" and (has_error or not all_terminal_pass):
        raise RunnerError(
            "accepted prepared review requires only covered/gap-preserved verdicts and no error findings"
        )
    if decision == "changes-required" and not findings:
        raise RunnerError("changes-required prepared review requires at least one finding")

    return ReviewContract(
        decision=decision,
        contract_version=2,
        reviewed_draft_sha256=reviewed_hash,
        obligation_reviews=tuple(reviews),
        findings=tuple(findings),
        summary=_required_text(payload, "summary", "review"),
    )


def render_prepared_review_findings(review: ReviewContract) -> str:
    lines = [
        "# Результат prepared reviewer",
        "",
        f"- Решение: `{review.decision}`",
        f"- SHA-256 проверенного draft: `{review.reviewed_draft_sha256}`",
        "",
        "## Проверка обязательств",
        "",
    ]
    for item in review.obligation_reviews:
        tc_ids = ", ".join(f"`{value}`" for value in item.test_case_ids) or "нет"
        lines.append(
            f"- `{item.obligation_id}` -> `{item.atom_id}` — `{item.verdict}`; "
            f"test cases: {tc_ids}; {item.note}"
        )
    lines.extend(["", "## Findings", ""])
    if review.findings:
        for finding in review.findings:
            atom_ids = ", ".join(f"`{value}`" for value in finding.atom_ids) or "set-level"
            tc_ids = ", ".join(f"`{value}`" for value in finding.test_case_ids) or "нет"
            lines.extend(
                [
                    f"### {finding.finding_id}",
                    "",
                    f"- Severity: `{finding.severity}`",
                    f"- Category: `{finding.category}`",
                    f"- ATOM: {atom_ids}",
                    f"- Test cases: {tc_ids}",
                    f"- Проблема: {finding.problem}",
                    f"- Требуемое изменение: {finding.required_change}",
                    "",
                ]
            )
    else:
        lines.extend(["Blocking findings отсутствуют.", ""])
    lines.extend(["## Резюме", "", review.summary])
    return "\n".join(lines)


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
    parser.add_argument("--writer-instruction-file", action="append", default=[])
    parser.add_argument("--reviewer-instruction-file", action="append", default=[])
    parser.add_argument("--prepared-package")
    parser.add_argument("--prepared-repair-draft")
    parser.add_argument("--prepared-repair-findings")
    parser.add_argument("--prepared-reviewer-rebind-draft")
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
    parser.add_argument(
        "--writer-timeout-seconds",
        type=int,
        default=DEFAULT_STANDARD_WRITER_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--reviewer-timeout-seconds",
        type=int,
        default=DEFAULT_STANDARD_REVIEWER_TIMEOUT_SECONDS,
    )
    parser.add_argument("--prepared-reviewer-timeout-seconds", type=int, default=90)
    parser.add_argument(
        "--writer-idle-timeout-seconds",
        type=int,
        default=DEFAULT_STANDARD_WRITER_IDLE_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--reviewer-idle-timeout-seconds",
        type=int,
        default=DEFAULT_STANDARD_REVIEWER_IDLE_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--prepared-standard-reviewer-idle-timeout-seconds",
        type=int,
        default=DEFAULT_PREPARED_STANDARD_REVIEWER_IDLE_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--writer-command-budget",
        type=int,
        default=DEFAULT_STANDARD_WRITER_COMMAND_BUDGET,
    )
    parser.add_argument(
        "--reviewer-command-budget",
        type=int,
        default=DEFAULT_STANDARD_REVIEWER_COMMAND_BUDGET,
    )
    parser.add_argument("--prepared-reviewer-command-budget", type=int, default=1)
    parser.add_argument(
        "--prepared-fast-writer-mode",
        choices=sorted(PREPARED_FAST_WRITER_MODES),
        default=DEFAULT_PREPARED_FAST_WRITER_MODE,
    )
    parser.add_argument(
        "--prepared-standard-writer-mode",
        choices=sorted(PREPARED_STANDARD_WRITER_MODES),
        default=DEFAULT_PREPARED_STANDARD_WRITER_MODE,
    )
    parser.add_argument(
        "--writer-first-artifact-deadline-seconds",
        type=int,
        default=DEFAULT_STANDARD_WRITER_FIRST_ARTIFACT_DEADLINE_SECONDS,
    )
    parser.add_argument(
        "--prepared-reviewer-prompt-max-bytes",
        type=int,
        default=DEFAULT_PREPARED_REVIEWER_PROMPT_MAX_BYTES,
    )
    parser.add_argument(
        "--prepared-standard-writer-context-max-bytes",
        type=int,
        default=DEFAULT_PREPARED_STANDARD_WRITER_CONTEXT_MAX_BYTES,
    )
    parser.add_argument(
        "--prepared-standard-reviewer-context-max-bytes",
        type=int,
        default=DEFAULT_PREPARED_STANDARD_REVIEWER_CONTEXT_MAX_BYTES,
    )
    parser.add_argument(
        "--prepared-structured-writer-single-session-tc-limit",
        type=int,
        default=DEFAULT_PREPARED_STRUCTURED_WRITER_SINGLE_SESSION_TC_LIMIT,
    )
    parser.add_argument(
        "--prepared-structured-writer-shard-size",
        type=int,
        default=DEFAULT_PREPARED_STRUCTURED_WRITER_SHARD_SIZE,
    )
    parser.add_argument(
        "--prepared-structured-writer-max-shards",
        type=int,
        default=DEFAULT_PREPARED_STRUCTURED_WRITER_MAX_SHARDS,
    )
    parser.add_argument(
        "--prepared-targeted-repair-max-test-cases",
        type=int,
        default=DEFAULT_PREPARED_TARGETED_REPAIR_MAX_TEST_CASES,
    )
    parser.add_argument(
        "--prepared-structured-reviewer-obligation-limit",
        type=int,
        default=DEFAULT_PREPARED_STRUCTURED_REVIEWER_OBLIGATION_LIMIT,
    )
    parser.add_argument("--promote-final", action="store_true")
    parser.add_argument("--promotion-dry-run", action="store_true")
    parser.add_argument("--promotion-contract")
    parser.add_argument("--allow-overwrite-final", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
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
        prepared_repair_draft_path=(
            repo_root / args.prepared_repair_draft
            if args.prepared_repair_draft
            else None
        ),
        prepared_repair_findings_path=(
            repo_root / args.prepared_repair_findings
            if args.prepared_repair_findings
            else None
        ),
        prepared_reviewer_rebind_draft_path=(
            repo_root / args.prepared_reviewer_rebind_draft
            if args.prepared_reviewer_rebind_draft
            else None
        ),
        promotion_contract_path=(
            repo_root / args.promotion_contract if args.promotion_contract else None
        ),
        instruction_files=[repo_root / item for item in args.instruction_file],
        writer_instruction_files=[
            repo_root / item for item in args.writer_instruction_file
        ],
        reviewer_instruction_files=[
            repo_root / item for item in args.reviewer_instruction_file
        ],
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
        prepared_reviewer_timeout_seconds=args.prepared_reviewer_timeout_seconds,
        writer_idle_timeout_seconds=args.writer_idle_timeout_seconds,
        reviewer_idle_timeout_seconds=args.reviewer_idle_timeout_seconds,
        prepared_standard_reviewer_idle_timeout_seconds=(
            args.prepared_standard_reviewer_idle_timeout_seconds
        ),
        writer_command_budget=args.writer_command_budget,
        reviewer_command_budget=args.reviewer_command_budget,
        prepared_reviewer_command_budget=args.prepared_reviewer_command_budget,
        prepared_fast_writer_mode=args.prepared_fast_writer_mode,
        prepared_standard_writer_mode=args.prepared_standard_writer_mode,
        writer_first_artifact_deadline_seconds=args.writer_first_artifact_deadline_seconds,
        prepared_reviewer_prompt_max_bytes=args.prepared_reviewer_prompt_max_bytes,
        prepared_standard_writer_context_max_bytes=(
            args.prepared_standard_writer_context_max_bytes
        ),
        prepared_standard_reviewer_context_max_bytes=(
            args.prepared_standard_reviewer_context_max_bytes
        ),
        prepared_structured_writer_single_session_tc_limit=(
            args.prepared_structured_writer_single_session_tc_limit
        ),
        prepared_structured_writer_shard_size=(
            args.prepared_structured_writer_shard_size
        ),
        prepared_structured_writer_max_shards=(
            args.prepared_structured_writer_max_shards
        ),
        prepared_targeted_repair_max_test_cases=(
            args.prepared_targeted_repair_max_test_cases
        ),
        prepared_structured_reviewer_obligation_limit=(
            args.prepared_structured_reviewer_obligation_limit
        ),
        promote_final=args.promote_final,
        promotion_dry_run=args.promotion_dry_run,
        allow_overwrite_final=args.allow_overwrite_final,
    )
    try:
        if args.validate_only:
            print(json.dumps(runner.validate_only_report(), ensure_ascii=False))
            return 0
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
