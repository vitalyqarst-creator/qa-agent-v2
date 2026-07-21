from __future__ import annotations

import importlib.util
import hashlib
import io
import json
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path
from unittest import mock

from test_case_agent.review_cycle.prepared_package import (
    EvidenceInput,
    PreparedDictionaryRequirement,
    PreparedDictionaryValue,
    PreparedExecutionDependency,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
    PreparedPackageBuilder,
    PreparedReleaseStatus,
    PreparedStateChange,
    StageInstructionConfig,
    load_obligations,
)
from test_case_agent.review_cycle.source_assertions import (
    NO_REQUIRED_CHANGE,
    REVIEW_RECEIPT_VERSION,
    SOURCE_ASSERTIONS_MARKER,
    SOURCE_REVIEW_DIMENSIONS,
    ClauseEvidenceBinding,
    RequirementCodeBinding,
    ScopeBoundaryManifestContext,
    ScopeBoundaryExclusion,
    ScopeBoundaryReview,
    SourceAssertion,
    SourceAssertionReview,
    SourceAssertionReviewReceipt,
    SourceInventoryReview,
    build_source_assertion_manifest,
    render_embedded_source_assertion_contract,
    scope_boundary_source_locator,
)
from test_case_agent.review_cycle.dimension_bindings import (
    ReviewerDimensionSourceBindings,
    render_reviewer_dimension_source_bindings,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT_DIR / "scripts" / "codex_exec_review_cycle_runner.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("codex_exec_review_cycle_runner_under_test", RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner_module = load_runner_module()


class ScriptedExecutor:
    def __init__(self, *steps):
        self.steps = list(steps)
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        if not self.steps:
            raise AssertionError("Unexpected process execution")
        return self.steps.pop(0)(request)


class ConcurrentStageExecutor:
    supports_concurrent_execution = True

    def __init__(self, handler):
        self.handler = handler
        self.requests = []
        self.completion_order = []
        self.max_active = 0
        self._active = 0
        self._lock = threading.Lock()

    def execute(self, request):
        with self._lock:
            self.requests.append(request)
            self._active += 1
            self.max_active = max(self.max_active, self._active)
        try:
            return self.handler(request)
        finally:
            with self._lock:
                self._active -= 1
                self.completion_order.append(request.stage)


class StreamingSubprocessExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_targeted_repair_accepts_primary_and_derived_obligation_findings(self) -> None:
        expected = {
            "oracle-polarity-mismatch",
            "missing-testable-obligation-coverage",
            "production-forbidden-process-wording",
            "production-missing-numbered-action-step",
            "production-non-reproducible-precondition",
        }
        self.assertTrue(
            expected.issubset(runner_module.REPAIRABLE_QUALITY_FINDING_IDS)
        )
        self.assertEqual(
            14,
            runner_module.DEFAULT_PREPARED_TARGETED_REPAIR_MAX_TEST_CASES,
        )

    def request(
        self,
        code: str,
        *,
        # These positive-path defaults include Windows process scheduling and
        # interpreter startup; timeout-contract tests pass explicit 1s values.
        timeout_seconds: int | None = 15,
        idle_timeout_seconds: int | None = 10,
        command_budget: int = 5,
        progress_path: Path | None = None,
        first_artifact_deadline_seconds: int | None = None,
    ):
        return runner_module.ProcessRequest(
            stage="writer-r1",
            role="writer",
            command=(sys.executable, "-c", code),
            cwd=self.root,
            prompt="test prompt",
            timeout_seconds=timeout_seconds,
            idle_timeout_seconds=idle_timeout_seconds,
            command_budget=command_budget,
            stdout_path=self.root / "stdout.txt",
            stderr_path=self.root / "stderr.txt",
            progress_path=progress_path,
            progress_forbidden_marker=runner_module.SEED_MARKER,
            first_artifact_deadline_seconds=first_artifact_deadline_seconds,
        )

    def test_streams_jsonl_and_counts_started_commands(self) -> None:
        code = (
            "import json,sys; "
            "print(json.dumps({'type':'item.started','item':{'type':'command_execution'}}),flush=True); "
            "sys.stderr.write('diagnostic\\n'); sys.stderr.flush()"
        )
        result = runner_module.SubprocessExecutor().execute(self.request(code))

        self.assertEqual(0, result.exit_code, result)
        self.assertEqual(1, result.command_count)
        self.assertEqual("completed", result.termination_reason)
        self.assertIsNotNone(result.first_output_seconds)
        self.assertEqual(result.stdout, (self.root / "stdout.txt").read_text(encoding="utf-8"))
        self.assertEqual("diagnostic\n", (self.root / "stderr.txt").read_text(encoding="utf-8"))

    def test_stops_process_when_command_budget_is_exceeded(self) -> None:
        event = "{'type':'item.started','item':{'type':'command_execution'}}"
        code = (
            f"import json,time; print(json.dumps({event}),flush=True); "
            f"print(json.dumps({event}),flush=True); time.sleep(5)"
        )
        started = time.monotonic()
        result = runner_module.SubprocessExecutor().execute(
            self.request(code, command_budget=1)
        )

        self.assertTrue(result.command_budget_exceeded)
        self.assertEqual("command-budget-exceeded", result.termination_reason)
        self.assertEqual(2, result.command_count)
        self.assertLess(time.monotonic() - started, 4)

    def test_stops_idle_process_without_waiting_for_hard_timeout(self) -> None:
        code = "import time; print('started',flush=True); time.sleep(5)"
        started = time.monotonic()
        result = runner_module.SubprocessExecutor().execute(
            self.request(code, timeout_seconds=5, idle_timeout_seconds=1)
        )

        self.assertTrue(result.idle_timed_out)
        self.assertFalse(result.timed_out)
        self.assertEqual("idle-timeout", result.termination_reason)
        self.assertLess(time.monotonic() - started, 4)

    def test_disabled_idle_timeout_waits_for_hard_timeout(self) -> None:
        code = "import time; print('started',flush=True); time.sleep(5)"
        started = time.monotonic()
        result = runner_module.SubprocessExecutor().execute(
            self.request(code, timeout_seconds=1, idle_timeout_seconds=None)
        )

        self.assertTrue(result.timed_out)
        self.assertFalse(result.idle_timed_out)
        self.assertEqual("hard-timeout", result.termination_reason)
        self.assertLess(time.monotonic() - started, 4)

    def test_disabled_hard_and_idle_timeouts_allows_normal_completion(self) -> None:
        result = runner_module.SubprocessExecutor().execute(
            self.request(
                "print('completed', flush=True)",
                timeout_seconds=None,
                idle_timeout_seconds=None,
            )
        )

        self.assertEqual(0, result.exit_code, result)
        self.assertFalse(result.timed_out)
        self.assertFalse(result.idle_timed_out)
        self.assertEqual("completed", result.termination_reason)

    def test_stops_when_first_meaningful_artifact_deadline_is_missed(self) -> None:
        code = "import time; print('started',flush=True); time.sleep(5)"
        result = runner_module.SubprocessExecutor().execute(
            self.request(
                code,
                timeout_seconds=5,
                idle_timeout_seconds=1,
                progress_path=self.root / "draft.md",
                first_artifact_deadline_seconds=1,
            )
        )

        self.assertTrue(result.first_artifact_deadline_exceeded)
        self.assertFalse(result.idle_timed_out)
        self.assertEqual("first-artifact-deadline", result.termination_reason)

    def test_records_first_meaningful_artifact_write(self) -> None:
        code = (
            "import pathlib,time; time.sleep(.2); "
            "pathlib.Path('draft.md').write_text('complete draft',encoding='utf-8'); "
            "print('written',flush=True)"
        )
        result = runner_module.SubprocessExecutor().execute(
            self.request(
                code,
                progress_path=self.root / "draft.md",
                first_artifact_deadline_seconds=5,
            )
        )

        self.assertEqual(0, result.exit_code, result)
        self.assertEqual("completed", result.termination_reason)
        self.assertIsNotNone(result.first_artifact_seconds)
        self.assertLess(result.first_artifact_seconds, 5)


class ImmutableTerminalArtifactTests(unittest.TestCase):
    def test_matching_bytes_are_recovery_safe_but_conflicting_bytes_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "terminal.md"
            runner_module._write_immutable_atomic(path, b"accepted\n")
            runner_module._write_immutable_atomic(path, b"accepted\n")

            with self.assertRaises(runner_module.RunnerError):
                runner_module._write_immutable_atomic(path, b"conflict\n")

            self.assertEqual(b"accepted\n", path.read_bytes())

    def test_concurrent_destination_is_never_clobbered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "terminal.md"

            def competing_publish(_source, destination) -> None:
                Path(destination).write_bytes(b"competitor\n")
                raise FileExistsError(destination)

            with mock.patch.object(runner_module.os, "link", side_effect=competing_publish):
                with self.assertRaises(runner_module.RunnerError):
                    runner_module._write_immutable_atomic(path, b"candidate\n")

            self.assertEqual(b"competitor\n", path.read_bytes())


class FakeValidator:
    def __init__(self, *, passed: bool = True):
        self.passed = passed
        self.calls = []

    def validate(self, **kwargs):
        self.calls.append(kwargs)
        findings = () if self.passed else ({"id": "fake-validator-finding", "severity": "error"},)
        return runner_module.ValidationResult(
            passed=self.passed,
            findings=findings,
            checked_paths=(str(kwargs["draft_path"]),),
            validator="fake-deterministic-validator",
        )


class CodexExecReviewCycleRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tmp.name)
        self.ft_root = self.repo_root / "fts" / "demo-ft"
        self.cycle_dir = self.ft_root / "work" / "review-cycles" / "exec-prototype"
        self.writer_attempt = self.cycle_dir / "attempts" / "writer-r1" / "attempt-001"
        self.reviewer_attempt = self.cycle_dir / "attempts" / "reviewer-r1" / "attempt-001"
        self.draft_path = self.writer_attempt / "stage-output" / "draft.md"
        self.final_path = self.ft_root / "test-cases" / "1-demo-scope.md"
        self.source_path = self.ft_root / "source" / "main.xhtml"
        self.docx_path = self.ft_root / "source" / "main.docx"
        self.handoff_path = self.ft_root / "work" / "stage-handoffs" / "01-demo" / "scope-contract.md"
        self.coverage_gaps_path = (
            self.handoff_path.parent / "scope-coverage-gaps.md"
        )
        self.workflow_state_path = self.handoff_path.parent / "workflow-state.yaml"
        self.instruction_path = self.repo_root / "AGENTS.md"
        self.writer_runtime_instruction = self.repo_root / "writer-runtime.md"
        self.reviewer_runtime_instruction = self.repo_root / "reviewer-runtime.md"
        self.prepared_profile_path = (
            self.repo_root / "references" / "agent" / "prepared-writer-runtime-profile.md"
        )
        self.prepared_reviewer_profile_path = (
            self.repo_root / "references" / "agent" / "prepared-reviewer-runtime-profile.md"
        )
        self.source_path.parent.mkdir(parents=True)
        self.handoff_path.parent.mkdir(parents=True)
        self.coverage_gaps_path.parent.mkdir(parents=True, exist_ok=True)
        self.final_path.parent.mkdir(parents=True)
        self.source_path.write_text(
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            "<p>BSR 1. Source</p>"
            "<p>External ancestor context.</p>"
            "<p>External cross-reference context.</p>"
            "</body></html>\n",
            encoding="utf-8",
        )
        self.docx_path.write_bytes(b"docx-source")
        self.handoff_path.write_text("# Scope contract\n", encoding="utf-8")
        self.coverage_gaps_path.write_text(
            "# Coverage Gaps\n\nNo gaps.\n", encoding="utf-8"
        )
        self.workflow_state_path.write_text(
            "ft_slug: demo-ft\n"
            "scope_slug: demo-scope\n"
            "current_stage: ft-test-case-iteration\n"
            "stage_status: ready-for-review\n"
            "next_skill: ft-test-case-reviewer\n"
            "blocking_reasons: []\n",
            encoding="utf-8",
        )
        self.instruction_path.write_text("# Test instructions\n", encoding="utf-8")
        self.writer_runtime_instruction.write_text(
            "# Writer runtime\n\nUse canonical `## TC-*` headings.\n",
            encoding="utf-8",
        )
        self.reviewer_runtime_instruction.write_text(
            "# Reviewer runtime\n\nReview traceability and test design.\n",
            encoding="utf-8",
        )
        self.prepared_profile_path.parent.mkdir(parents=True)
        self.prepared_profile_path.write_text(
            "# Prepared Writer Runtime Profile\n\n"
            "Require runner-validated current metadata with `package_digest`.\n"
            "Production preconditions use inline numbered setup actions.\n"
            "Write the embedded seed immediately.\n",
            encoding="utf-8",
        )
        self.prepared_reviewer_profile_path.write_text(
            "# Prepared Reviewer Runtime Profile\n\n"
            "Require runner-validated current metadata with `package_digest`.\n"
            "Review only the embedded payload.\n",
            encoding="utf-8",
        )
        self.validator = FakeValidator()

    def resolve_instruction_context(self, *, root: Path, scenario_id: str):
        self.assertTrue(self.repo_root.samefile(root))
        role_path = (
            self.writer_runtime_instruction
            if scenario_id == "writer.session_initial_draft"
            else self.reviewer_runtime_instruction
        )
        return {
            "scenario": scenario_id,
            "budget": {
                "status": "pass",
                "total_kib": 1.0,
                "limit_kib": 10.0,
            },
            "files": [
                {"path": self.instruction_path.relative_to(self.repo_root).as_posix()},
                {"path": role_path.relative_to(self.repo_root).as_posix()},
            ],
            "missing": [],
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def process_result(
        *,
        exit_code: int | None = 0,
        stdout: str = "",
        stderr: str = "",
        timed_out: bool = False,
        launch_error: bool = False,
        command_count: int = 0,
        command_budget_exceeded: bool = False,
    ):
        return runner_module.ProcessResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            launch_error=launch_error,
            command_count=command_count,
            command_budget_exceeded=command_budget_exceeded,
            duration_seconds=0.25,
        )

    @staticmethod
    def json_event(message: str, *, session_id: str = "test-session") -> str:
        return "".join(
            (
                json.dumps(
                    {"type": "thread.started", "thread_id": session_id},
                    ensure_ascii=False,
                )
                + "\n",
                json.dumps(
                    {"type": "item.completed", "item": {"type": "agent_message", "text": message}},
                    ensure_ascii=False,
                )
                + "\n",
            )
        )

    def writer_step(
        self,
        *,
        create_draft: bool = True,
        draft_text: str | None = None,
        exit_code: int | None = 0,
        stdout: str | None = None,
        stderr: str = "",
        timed_out: bool = False,
    ):
        def step(_request):
            if create_draft:
                self.draft_path.parent.mkdir(parents=True, exist_ok=True)
                self.draft_path.write_text(
                    draft_text
                    or "# Test cases\n\n## TC-DEMO-001\n\n**Трассировка:** ATOM-001; SRC-1\n\nDraft body.\n",
                    encoding="utf-8",
                )
            return self.process_result(
                exit_code=exit_code,
                stdout=(
                    stdout
                    if stdout is not None
                    else self.json_event("writer completed", session_id="writer-session")
                ),
                stderr=stderr,
                timed_out=timed_out,
            )

        return step

    def reviewer_step(
        self,
        *,
        decision: str = "accepted",
        findings: str = "# Review findings\n\nNo blocking findings.",
        exit_code: int | None = 0,
        stdout: str | None = None,
        stderr: str = "",
        timed_out: bool = False,
        mutate_production: bool = False,
        mutate_draft: bool = False,
        commands=(),
    ):
        def step(_request):
            if mutate_production:
                guard_path = self.ft_root / "test-cases" / "guard.md"
                guard_path.write_text("reviewer mutation\n", encoding="utf-8")
            if mutate_draft:
                self.draft_path.write_text("reviewer changed the validated draft\n", encoding="utf-8")
            if (
                "prepared reviewer fast path" in _request.prompt
                or "prepared-standard reviewer" in _request.prompt
            ):
                schema = {}
                if "--output-schema-contract" in _request.command:
                    schema_path = Path(
                        _request.command[
                            _request.command.index("--output-schema-contract") + 1
                        ]
                    )
                    schema = json.loads(schema_path.read_text(encoding="utf-8"))
                contract_version = (
                    schema.get("properties", {})
                    .get("contract_version", {})
                    .get("const", 2)
                )
                prepared_findings = []
                verdict = "covered"
                if decision == "changes-required":
                    verdict = "incorrect"
                    prepared_findings = [
                        {
                            "id": "REV-001",
                            "severity": "error",
                            "category": "test-design",
                            "atom_ids": ["ATOM-001"],
                            "test_case_ids": ["TC-DEMO-001"],
                            "problem": findings,
                            "required_change": "Correct the affected test case.",
                        }
                    ]
                if contract_version == 4:
                    properties = schema["properties"]
                    dimension_receipts = []
                    for variant in (
                        properties["dimension_reviews"]
                        .get("items", {})
                        .get("anyOf", [])
                    ):
                        variant_properties = variant.get("properties", {})
                        dimension = variant_properties.get("dimension", {}).get(
                            "const", ""
                        )
                        allowed_refs = (
                            variant_properties.get("source_refs", {})
                            .get("items", {})
                            .get("enum", [])
                        )
                        if dimension and allowed_refs:
                            dimension_receipts.append((dimension, allowed_refs))
                    obligation_reviews = []
                    failure_assigned = False
                    for variant in (
                        properties["obligation_reviews"]
                        .get("items", {})
                        .get("anyOf", [])
                    ):
                        variant_properties = variant.get("properties", {})
                        obligation_ids = (
                            variant_properties.get("obligation_id", {}).get("enum", [])
                        )
                        allowed_verdicts = (
                            variant_properties.get("verdict", {}).get("enum", [])
                        )
                        success_verdict = (
                            "covered"
                            if "covered" in allowed_verdicts
                            else "gap-preserved"
                        )
                        failure_verdict = (
                            "incorrect"
                            if "incorrect" in allowed_verdicts
                            else "invented-coverage"
                        )
                        for obligation_id in obligation_ids:
                            use_failure = (
                                decision != "accepted" and not failure_assigned
                            )
                            obligation_reviews.append(
                                {
                                    "obligation_id": obligation_id,
                                    "verdict": (
                                        failure_verdict
                                        if use_failure
                                        else success_verdict
                                    ),
                                }
                            )
                            failure_assigned = failure_assigned or use_failure
                    payload = {
                        "contract_version": 4,
                        "decision": decision,
                        "reviewed_draft_sha256": hashlib.sha256(
                            self.draft_path.read_bytes()
                        ).hexdigest(),
                        "reviewed_source_basis_sha256": properties[
                            "reviewed_source_basis_sha256"
                        ]["const"],
                        "reviewed_obligation_set_sha256": properties[
                            "reviewed_obligation_set_sha256"
                        ]["const"],
                        "obligation_reviews": obligation_reviews,
                        "dimension_reviews": [
                            {
                                "dimension": dimension,
                                "verdict": (
                                    "verified"
                                    if decision == "accepted"
                                    else "unsupported"
                                ),
                                "source_refs": source_refs,
                                "note": "The routed dimension was reviewed source-first.",
                            }
                            for dimension, source_refs in dimension_receipts
                        ],
                        "findings": prepared_findings,
                        "summary": findings,
                    }
                else:
                    payload = {
                        "contract_version": 2,
                        "decision": decision,
                        "reviewed_draft_sha256": hashlib.sha256(
                            self.draft_path.read_bytes()
                        ).hexdigest(),
                        "obligation_reviews": [
                            {
                                "obligation_id": "ATOM-001",
                                "atom_id": "ATOM-001",
                                "verdict": verdict,
                                "test_case_ids": ["TC-DEMO-001"],
                                "note": (
                                    "The supplied draft was reviewed against the atom; GAP-001 preserved."
                                    if '"constraint_gap_ids"' in _request.prompt and "GAP-001" in _request.prompt
                                    else "The supplied draft was reviewed against the atom."
                                ),
                            }
                        ],
                        "findings": prepared_findings,
                        "summary": findings,
                    }
            else:
                payload = {"decision": decision, "findings_markdown": findings}
            contract = json.dumps(payload, ensure_ascii=False)
            generated_stdout = self.json_event(contract, session_id="reviewer-session")
            for index, command in enumerate(commands, start=1):
                generated_stdout += json.dumps(
                    {
                        "type": "item.started",
                        "item": {
                            "id": f"reviewer-command-{index}",
                            "type": "command_execution",
                            "command": command,
                        },
                    }
                ) + "\n"
            return self.process_result(
                exit_code=exit_code,
                stdout=(
                    stdout
                    if stdout is not None
                    else generated_stdout
                ),
                stderr=stderr,
                timed_out=timed_out,
            )

        return step

    def structured_writer_step(
        self,
        *,
        status: str = "draft-ready",
        draft_text: str | None = None,
        blocking_reasons=(),
        payload_override=None,
        command_count: int = 0,
        command_budget_exceeded: bool = False,
    ):
        def step(_request):
            payload = payload_override or {
                "contract_version": 1,
                "status": status,
                "draft_markdown": (
                    draft_text
                    or "# Test cases\n\n## TC-DEMO-001\n\n**Traceability:** ATOM-001; SRC-1\n\nDraft body.\n"
                )
                if status == "draft-ready"
                else "",
                "blocking_reasons": list(blocking_reasons),
            }
            return self.process_result(
                stdout=self.json_event(
                    json.dumps(payload, ensure_ascii=False),
                    session_id="writer-session",
                ),
                command_count=command_count,
                command_budget_exceeded=command_budget_exceeded,
            )

        return step

    @staticmethod
    def complete_test_case_section(index: int, *, expected: str | None = None) -> str:
        obligation_id = "ATOM-001" if index == 1 else f"OBL-{index:03d}"
        return f"""## TC-DEMO-{index:03d}

**Название:** Проверка видимого результата {index}
**Тип:** позитивный
**Приоритет:** средний
**package_id:** pkg-exec-001
**Трассировка:** {obligation_id}; ATOM-{index:03d}; SRC-1

### Предусловия

1. Авторизоваться в системе.
2. Открыть форму с полем {index}.

### Тестовые данные

- Значение: `value-{index}`.

### Шаги

1. Ввести `value-{index}` в поле {index}.

### Итоговый ожидаемый результат

{expected or f'Поле {index} визуально содержит `value-{index}`.'}

### Постусловия

- Дополнительная очистка не требуется.
"""

    def structured_shard_result(
        self,
        test_case_ids,
        *,
        session_id: str,
        exit_code: int | None = 0,
    ):
        payload = {
            "contract_version": 1,
            "status": "draft-ready",
            "draft_markdown": "\n\n".join(
                self.complete_test_case_section(
                    int(test_case_id.rsplit("-", 1)[1])
                )
                for test_case_id in test_case_ids
            ),
            "blocking_reasons": [],
        }
        return self.process_result(
            exit_code=exit_code,
            stdout=self.json_event(
                json.dumps(payload, ensure_ascii=False),
                session_id=session_id,
            ),
        )

    def prepared_reviewer_step_for_count(self, count: int):
        def step(_request):
            payload = {
                "contract_version": 2,
                "decision": "accepted",
                "reviewed_draft_sha256": hashlib.sha256(
                    self.draft_path.read_bytes()
                ).hexdigest(),
                "obligation_reviews": [
                    {
                        "obligation_id": (
                            "ATOM-001" if index == 1 else f"OBL-{index:03d}"
                        ),
                        "atom_id": f"ATOM-{index:03d}",
                        "verdict": "covered",
                        "test_case_ids": [f"TC-DEMO-{index:03d}"],
                        "note": f"Видимый результат {index} покрыт.",
                    }
                    for index in range(1, count + 1)
                ],
                "findings": [],
                "summary": "Точечно исправленный draft принят.",
            }
            return self.process_result(
                stdout=self.json_event(
                    json.dumps(payload, ensure_ascii=False),
                    session_id="reviewer-after-targeted-repair",
                )
            )

        return step

    def make_runner(
        self,
        executor,
        *,
        validator=None,
        promote_final: bool = False,
        promotion_dry_run: bool = False,
        allow_overwrite_final: bool = False,
        verified: bool = True,
    ):
        return runner_module.CodexExecReviewCycleRunner(
            repo_root=self.repo_root,
            ft_root=self.ft_root,
            cycle_dir=self.cycle_dir,
            final_path=self.final_path,
            source_files=[self.source_path],
            handoff_files=[self.handoff_path],
            command_config=runner_module.ExecCommandConfig(
                executable="codex-test",
                sandbox_flag="--sandbox-contract",
                writer_sandbox="writer-workspace-write",
                reviewer_sandbox="reviewer-read-only",
                working_directory_flag="--working-directory-contract",
                json_flag="--jsonl-contract",
                output_last_message_flag="--last-message-contract",
                extra_args=("--non-interactive-contract",),
                cli_contract_verified=verified,
            ),
            executor=executor,
            validator=validator or self.validator,
            timeout_seconds=5,
            promote_final=promote_final,
            promotion_dry_run=promotion_dry_run,
            allow_overwrite_final=allow_overwrite_final,
            instruction_context_resolver=self.resolve_instruction_context,
        )

    def build_prepared_package(
        self,
        *,
        execution_profile: str = "simple-field-property",
        unsupported_dimensions=(),
        forbidden_evidence_roots=("fts/demo-ft/test-cases",),
        instruction_attempt_root: Path | None = None,
        include_gap: bool = False,
        blocking_gap: bool = False,
        constraint_gap: bool = False,
        grouped_obligations: bool = False,
        out_of_order_planned_ids: bool = False,
        test_case_count: int = 1,
        first_observable_oracle: str = "The visible result matches the requirement.",
        first_execution_semantics: str = "direct",
        first_state_change: PreparedStateChange | None = None,
        dictionary_values: tuple[str, ...] = (),
        prepared_dictionary_values: tuple[PreparedDictionaryValue, ...] = (),
        reference_fixture_values: tuple[PreparedDictionaryValue, ...] = (),
        extra_prepared_obligations: tuple[PreparedObligation, ...] = (),
        extra_prepared_gaps: tuple[PreparedGap, ...] = (),
        structured_dictionary_evidence: bool = False,
        dictionary_coverage_mode: str = "reference-only",
        calibration_status: str = "none",
        source_first_contract: bool | str = False,
        source_first_risk: str = "high",
        source_first_polarity: str = "positive",
        execution_dependency: bool = False,
    ) -> Path:
        gap_evidence = (
            "\nGAP-001: exact mapping is unresolved.\n"
            if include_gap or blocking_gap or constraint_gap
            else ""
        )
        dictionary_evidence = ""
        if dictionary_values or prepared_dictionary_values or reference_fixture_values:
            evidence_values = dictionary_values or tuple(
                dict.fromkeys(
                    value.value
                    for value in (
                        *prepared_dictionary_values,
                        *reference_fixture_values,
                    )
                )
            )
            rendered_values = "; ".join(f"`{value}`" for value in evidence_values)
            if structured_dictionary_evidence:
                dictionary_evidence = (
                    "\n## DICT-001\n\n```json\n"
                    + json.dumps(
                        {
                            "dictionary_id": "DICT-001",
                            "dictionary_name": "Demo dictionary",
                            "source_file": "support/demo.md",
                            "source_location": "demo.gender",
                            "extraction_status": "extracted",
                            "active_values": list(evidence_values),
                            "archived_values": "none_required",
                            "used_by_source_properties": "SRC-1",
                            "gap_id": "none_required",
                            "notes": "Test dictionary.",
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n```\n"
                )
            else:
                dictionary_evidence = (
                    "\n## DICT-001\n\n"
                    "DICT-001 | Demo dictionary | support/demo.md | demo.gender | "
                    f"extracted | {rendered_values} | none_required | SRC-1 | "
                    "none_required | Test dictionary.\n"
                )
        source_first_requested = bool(source_first_contract)
        source_first_evidence = ""
        if source_first_requested:
            if execution_dependency:
                self.source_path.write_text(
                    '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
                    "<p>BSR 1. Source</p>"
                    "<p>BSR 2. Dependency-bound source</p>"
                    "<p>External ancestor context.</p>"
                    "<p>External cross-reference context.</p>"
                    "</body></html>\n",
                    encoding="utf-8",
                )
            self.coverage_gaps_path.write_text(
                (
                    "# Coverage Gaps\n\n## GAP-001\n\n"
                    + (
                        "**Impact:** `blocking`\n"
                        if blocking_gap
                        else "**Impact:** `non-blocking`\n"
                    )
                    + "| field | value |\n"
                    + "| --- | --- |\n"
                    + "| gap_id | GAP-001 |\n"
                    + "| affected_assertion_id | ASSERT-001 |\n"
                    + "| affected_atom_id | ATOM-001 |\n"
                    + "| status | open |\n"
                )
                if include_gap or blocking_gap or constraint_gap
                else (
                    "# Coverage Gaps\n\n## GAP-EXECUTION-001\n\n"
                    "**Impact:** `blocking`\n\n"
                    "| field | value |\n"
                    "| --- | --- |\n"
                    "| gap_id | GAP-EXECUTION-001 |\n"
                    "| affected_assertion_id | ASSERT-BLOCKED-001 |\n"
                    "| affected_atom_id | ATOM-BLOCKED-001 |\n"
                    "| execution_assertion_ids | ASSERT-BLOCKED-001 |\n"
                    "| execution_atom_ids | ATOM-BLOCKED-001 |\n"
                    "| execution_obligation_ids | OBL-BLOCKED-001 |\n"
                    "| blocks_ready_for_review | yes |\n"
                    "| status | open |\n"
                    if execution_dependency
                    else "# Coverage Gaps\n\nNo gaps.\n"
                )
                ,
                encoding="utf-8",
            )
            assertion_specs = [
                (
                    "OBL-001",
                    "ATOM-001",
                    "The requirement is observable.",
                    "Verify the visible result.",
                    first_observable_oracle,
                )
            ]
            assertion_specs.extend(
                (
                    item.obligation_id,
                    item.traceability_atom_id,
                    item.atomic_statement,
                    item.test_intent,
                    item.observable_oracle,
                )
                for item in extra_prepared_obligations
                if item.coverage_status == "testable"
            )
            assertion_specs.extend(
                (
                    f"OBL-{index:03d}",
                    f"ATOM-{index:03d}",
                    f"Observable property {index} is required.",
                    f"Verify visible result {index}.",
                    f"Visible result {index} is present.",
                )
                for index in range(2, test_case_count + 1)
            )
            if grouped_obligations or out_of_order_planned_ids:
                assertion_specs.append(
                    (
                        "OBL-002",
                        "ATOM-002",
                        "The same observable action proves a second property.",
                        "Verify both properties with one observable action.",
                        "The visible result matches the second property.",
                    )
                )
            unique_assertion_specs = tuple(
                {
                    obligation_id: (
                        obligation_id,
                        atom_id,
                        statement,
                        action,
                        oracle,
                    )
                    for obligation_id, atom_id, statement, action, oracle in assertion_specs
                }.values()
            )
            assertions = tuple(
                SourceAssertion(
                    assertion_id=f"ASSERT-{index:03d}",
                    source_path=self.source_path.relative_to(self.repo_root).as_posix(),
                    source_context_class="document-global-constraints",
                    locator="/*/*[1]/*[1]",
                    exact_source_text="BSR 1. Source",
                    canonical_statement=statement,
                    polarity=source_first_polarity,
                    semantic_disposition="testable",
                    execution_readiness="ready",
                    execution_readiness_rationale=NO_REQUIRED_CHANGE,
                    risk=source_first_risk,
                    condition_clauses=("The demo form is open.",),
                    action_clauses=(action,),
                    oracle_clauses=(oracle,),
                    requirement_codes=("BSR 1",),
                    requirement_code_bindings=(
                        RequirementCodeBinding(
                            "BSR 1", "SRC-1", "xhtml-row", "BSR 1"
                        ),
                    ),
                    clause_evidence_bindings=tuple(
                        ClauseEvidenceBinding(
                            clause_kind=kind,
                            clause_index=0,
                            source_row_id="SRC-1",
                            evidence_role=kind,
                            exact_source_fragment="BSR 1. Source",
                        )
                        for kind in ("condition", "action", "oracle")
                    ),
                    source_row_id="SRC-1",
                    atom_id=atom_id,
                    obligation_ids=(obligation_id,),
                    execution_dependency_gap_ids=(),
                    primary_gap_id=None,
                )
                for index, (
                    obligation_id,
                    atom_id,
                    statement,
                    action,
                    oracle,
                ) in enumerate(unique_assertion_specs, start=1)
            )
            if execution_dependency:
                assertions += (
                    SourceAssertion(
                        assertion_id="ASSERT-BLOCKED-001",
                        source_path=self.source_path.relative_to(
                            self.repo_root
                        ).as_posix(),
                        source_context_class="scope-local",
                        locator="/*/*[1]/*[2]",
                        exact_source_text="BSR 2. Dependency-bound source",
                        canonical_statement=(
                            "A second observable property requires a missing fixture."
                        ),
                        polarity="positive",
                        semantic_disposition="testable",
                        execution_readiness="dependency-blocked",
                        execution_readiness_rationale=(
                            "A reproducible fixture is not registered for execution."
                        ),
                        risk="high",
                        condition_clauses=("The demo form is open.",),
                        action_clauses=("Execute the second observable action.",),
                        oracle_clauses=("The second visible result is present.",),
                        requirement_codes=("BSR 2",),
                        requirement_code_bindings=(
                            RequirementCodeBinding(
                                "BSR 2", "SRC-2", "xhtml-row", "BSR 2"
                            ),
                        ),
                        clause_evidence_bindings=tuple(
                            ClauseEvidenceBinding(
                                clause_kind=kind,
                                clause_index=0,
                                source_row_id="SRC-2",
                                evidence_role=kind,
                                exact_source_fragment=(
                                    "BSR 2. Dependency-bound source"
                                ),
                            )
                            for kind in ("condition", "action", "oracle")
                        ),
                        source_row_id="SRC-2",
                        atom_id="ATOM-BLOCKED-001",
                        obligation_ids=("OBL-BLOCKED-001",),
                        execution_dependency_gap_ids=(
                            "GAP-EXECUTION-001",
                        ),
                        primary_gap_id=None,
                    ),
                )
            manifest = build_source_assertion_manifest(
                self.repo_root,
                scope_slug="demo-scope",
                coverage_gaps_path=self.coverage_gaps_path.relative_to(
                    self.repo_root
                ).as_posix(),
                source_paths=(self.source_path.relative_to(self.repo_root).as_posix(),),
                assertions=assertions,
                source_row_extraction_spec_digest="1" * 64,
                source_row_baseline_digest="2" * 64,
                source_row_candidate_count=(2 if execution_dependency else 1),
                source_row_candidate_ids={
                    "SRC-1": "SRC-CAND-" + "1" * 24,
                    **(
                        {"SRC-2": "SRC-CAND-" + "2" * 24}
                        if execution_dependency
                        else {}
                    ),
                },
                expected_source_row_ids=(
                    ("SRC-1", "SRC-2")
                    if execution_dependency
                    else ("SRC-1",)
                ),
            )
            receipt = SourceAssertionReviewReceipt(
                version=REVIEW_RECEIPT_VERSION,
                manifest_digest=manifest.digest,
                decision="accepted",
                source_inventory_review=SourceInventoryReview(
                    extraction_spec_digest=manifest.source_row_extraction_spec_digest,
                    baseline_digest=manifest.source_row_baseline_digest,
                    candidate_count=manifest.source_row_candidate_count,
                    mapped_source_row_count=manifest.source_row_candidate_count,
                    verdict="verified",
                    required_change=NO_REQUIRED_CHANGE,
                    note="Candidate baseline and source-row mapping were reviewed.",
                ),
                assertion_reviews=tuple(
                    SourceAssertionReview(
                        assertion_id=assertion.assertion_id,
                        approved_polarity=assertion.polarity,
                        approved_semantic_disposition="testable",
                        approved_execution_readiness=assertion.execution_readiness,
                        approved_risk=assertion.risk,
                        dimension_verdicts={
                            dimension: "verified"
                            for dimension in SOURCE_REVIEW_DIMENSIONS
                        },
                        verdict="verified",
                        required_change=NO_REQUIRED_CHANGE,
                        note="Checked against the exact XHTML source text.",
                    )
                    for assertion in assertions
                ),
                scope_boundary_review=ScopeBoundaryReview(
                    verdict="verified",
                    checked_context_classes=(
                        "document-global-constraints",
                        "ancestor-and-section-preamble",
                        "cross-referenced-constraints",
                    ),
                    reviewed_manifest_contexts=(
                        ScopeBoundaryManifestContext(
                            context_class="document-global-constraints",
                            source_row_id="SRC-1",
                        ),
                    ),
                    excluded_contexts=tuple(
                        ScopeBoundaryExclusion(
                            context_class=context_class,
                            source_path=manifest.sources[0].path,
                            source_sha256=manifest.sources[0].sha256,
                            source_locator=scope_boundary_source_locator(
                                manifest.sources[0].path,
                                exact_text,
                            ),
                            exact_source_text=exact_text,
                            reason=(
                                "Verified context is outside the manifest row registry."
                            ),
                        )
                        for context_class, exact_text in (
                            (
                                "ancestor-and-section-preamble",
                                "External ancestor context.",
                            ),
                            (
                                "cross-referenced-constraints",
                                "External cross-reference context.",
                            ),
                        )
                    ),
                    required_change=NO_REQUIRED_CHANGE,
                    note="Scope boundaries were checked against the full document.",
                ),
            )
            if source_first_contract == "empty":
                source_first_evidence = "\n<!-- SOURCE-ASSERTIONS-V3 -->\n"
            elif source_first_contract == "empty-current":
                source_first_evidence = f"\n{SOURCE_ASSERTIONS_MARKER}\n"
            else:
                source_first_evidence = (
                    "\n"
                    + render_embedded_source_assertion_contract(manifest, receipt)
                )
                if source_first_contract == "forged":
                    source_first_evidence = source_first_evidence.replace(
                        manifest.digest, "0" * 64, 1
                    )
            source_first_evidence += (
                "\n## Reviewer dimension source bindings\n\n"
                + render_reviewer_dimension_source_bindings(
                    ReviewerDimensionSourceBindings.create(
                        {
                            dimension: ("SRC-1",)
                            for dimension in unsupported_dimensions
                        }
                    )
                )
                + "\n"
            )
        self.handoff_path.write_text(
            "# Scope contract\n\nSRC-1: observable requirement.\n"
            + gap_evidence
            + dictionary_evidence
            + source_first_evidence,
            encoding="utf-8",
        )
        compiled_dictionary_values = (
            ()
            if dictionary_coverage_mode == "reference-only"
            else prepared_dictionary_values
            or tuple(
                PreparedDictionaryValue(("DICT-001",), "leaf", value)
                for value in dictionary_values
            )
        )
        prepared_obligations = [
            PreparedObligation(
                obligation_id=(
                    "OBL-001" if source_first_requested else "ATOM-001"
                ),
                atom_id="ATOM-001" if source_first_requested else "",
                source_refs=("SRC-1",),
                atomic_statement="The requirement is observable.",
                observable_oracle=first_observable_oracle,
                test_intent="Verify the visible result.",
                coverage_status="testable",
                gap_id="",
                dictionary_refs=(
                    ("DICT-001",)
                    if dictionary_values
                    or prepared_dictionary_values
                    or reference_fixture_values
                    else ()
                ),
                notes="",
                constraint_gap_ids=(("GAP-001",) if constraint_gap else ()),
                execution_semantics=first_execution_semantics,
                state_change=first_state_change,
                dictionary_requirements=(
                    (
                        PreparedDictionaryRequirement(
                            dictionary_id="DICT-001",
                            coverage_mode=dictionary_coverage_mode,
                            required_values=compiled_dictionary_values,
                            fixture_values=(
                                reference_fixture_values
                                if dictionary_coverage_mode == "reference-only"
                                else ()
                            ),
                        ),
                    )
                    if dictionary_values
                    or prepared_dictionary_values
                    or reference_fixture_values
                    else ()
                ),
                calibration_status=calibration_status,
                planned_test_case_id=(
                    "TC-GROUP-002"
                    if out_of_order_planned_ids
                    else "TC-GROUP-001"
                    if grouped_obligations
                    else "TC-DEMO-001"
                    if test_case_count > 1
                    or source_first_requested
                    or calibration_status != "none"
                    or dictionary_coverage_mode != "reference-only"
                    or reference_fixture_values
                    else ""
                ),
            )
        ]
        prepared_obligations.extend(extra_prepared_obligations)
        for index in range(2, test_case_count + 1):
            prepared_obligations.append(
                PreparedObligation(
                    obligation_id=f"OBL-{index:03d}",
                    atom_id=f"ATOM-{index:03d}",
                    source_refs=("SRC-1",),
                    atomic_statement=f"Observable property {index} is required.",
                    observable_oracle=f"Visible result {index} is present.",
                    test_intent=f"Verify visible result {index}.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id=f"TC-DEMO-{index:03d}",
                )
            )
        if grouped_obligations or out_of_order_planned_ids:
            prepared_obligations.append(
                PreparedObligation(
                    obligation_id="OBL-002",
                    atom_id="ATOM-002",
                    source_refs=("SRC-1",),
                    atomic_statement="The same observable action proves a second property.",
                    observable_oracle="The visible result matches the second property.",
                    test_intent="Verify both properties with one observable action.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-GROUP-001",
                )
            )
        prepared_gaps = []
        if constraint_gap:
            prepared_gaps.append(
                PreparedGap(
                    gap_id="GAP-001",
                    source_refs=("SRC-1",),
                    problem="Exact UI reaction is unresolved.",
                    handling="Keep the check as a UI calibration candidate.",
                    blocking=False,
                )
            )
        if include_gap or blocking_gap:
            prepared_obligations.append(
                PreparedObligation(
                    obligation_id="OBL-002",
                    atom_id="ATOM-002",
                    source_refs=("SRC-1", "GAP-001"),
                    atomic_statement="Exact mapping is unresolved.",
                    observable_oracle="",
                    test_intent="Preserve the unresolved mapping as a gap.",
                    coverage_status="gap",
                    gap_id="GAP-001",
                    dictionary_refs=(),
                    notes="",
                )
            )
            prepared_gaps.append(
                PreparedGap(
                    gap_id="GAP-001",
                    source_refs=("SRC-1",),
                    problem="Exact mapping is unresolved.",
                    handling="Do not invent executable coverage.",
                    blocking=blocking_gap,
                )
            )
        prepared_gaps.extend(extra_prepared_gaps)
        obligations = PreparedObligationSet.create(
            package_id="pkg-exec-001",
            obligations=tuple(prepared_obligations),
            coverage_gaps=tuple(prepared_gaps),
        )
        package_root = self.cycle_dir / "prepared-input" / "pkg-exec-001"
        bound_attempt = instruction_attempt_root or self.writer_attempt
        standard_route = execution_profile == "standard-required"
        PreparedPackageBuilder(self.repo_root).build(
            output_root=package_root,
            package_id="pkg-exec-001",
            ft_slug="demo-ft",
            scope_slug="demo-scope",
            section_id="1",
            source_registry=(
                (self.docx_path, "source-of-truth", "section 1"),
                (self.source_path, "machine-readable", "SRC-1"),
            ),
            evidence_inputs=(
                EvidenceInput(
                    self.handoff_path,
                    "Confirmed scope",
                    selectors=("SRC-1", "DICT-001")
                    if dictionary_values
                    else ("SRC-1",),
                    include_full=source_first_requested,
                    max_bytes=(128 * 1024 if source_first_requested else 8192),
                ),
            ),
            obligations=obligations,
            instructions=StageInstructionConfig(
                role="writer",
                scenario=(
                    "writer.session_initial_draft"
                    if standard_route
                    else "writer.session_prepared_initial_draft"
                ),
                output_path=(bound_attempt / "stage-output" / "draft.md")
                .relative_to(self.repo_root)
                .as_posix(),
                attempt_root=bound_attempt.relative_to(self.repo_root).as_posix(),
                sandbox_policy="workspace_write",
                timeout_seconds=900 if standard_route else 180,
                idle_timeout_seconds=180 if standard_route else 60,
                command_budget=80 if standard_route else 12,
            ),
            execution_profile=execution_profile,
            unsupported_dimensions=unsupported_dimensions,
            forbidden_evidence_roots=forbidden_evidence_roots,
            release_status=(
                PreparedReleaseStatus(
                    contract="prepared-package-release-status-v1",
                    output_mode="draft-with-blocking-gaps",
                    release_eligible=False,
                    blocking_gap_ids=("GAP-EXECUTION-001",),
                    execution_dependency_registry=(
                        PreparedExecutionDependency(
                            assertion_id="ASSERT-BLOCKED-001",
                            source_row_id="SRC-2",
                            atom_id="ATOM-BLOCKED-001",
                            obligation_ids=("OBL-BLOCKED-001",),
                            gap_ids=("GAP-EXECUTION-001",),
                            risk="high",
                            rationale=(
                                "A reproducible fixture is not registered for execution."
                            ),
                        ),
                    ),
                    excluded_execution_obligation_ids=("OBL-BLOCKED-001",),
                    unsigned_status="blocked-execution-dependencies",
                    release_blocking_finding_codes=(
                        "blocking-source-first-gap",
                        "source-execution-dependency-blocked",
                    ),
                )
                if execution_dependency
                else PreparedReleaseStatus(
                    contract="prepared-package-release-status-v1",
                    output_mode="draft-with-blocking-gaps",
                    release_eligible=False,
                    blocking_gap_ids=("GAP-001",),
                    execution_dependency_registry=(),
                    excluded_execution_obligation_ids=(),
                    unsigned_status="blocked-source-gaps",
                    release_blocking_finding_codes=(
                        "blocking-source-first-gap",
                    ),
                )
                if blocking_gap
                else (
                    PreparedReleaseStatus.release_default()
                    if source_first_requested
                    else PreparedReleaseStatus(
                        contract="prepared-package-release-status-v1",
                        output_mode="release",
                        release_eligible=False,
                        blocking_gap_ids=(),
                        execution_dependency_registry=(),
                        excluded_execution_obligation_ids=(),
                        unsigned_status="blocked-source-contract",
                        release_blocking_finding_codes=(
                            "legacy-source-contract",
                        ),
                    )
                )
            ),
            allow_blocking_primary_gaps=(blocking_gap or execution_dependency),
        )
        return package_root / "stage-package.json"

    def make_prepared_runner(
        self,
        executor,
        package_path: Path,
        *,
        promotion_contract_path: Path | None = None,
        writer_mode: str = "workspace",
        standard_writer_mode: str = "structured",
        repair_draft_path: Path | None = None,
        repair_findings_path: Path | None = None,
        reviewer_rebind_draft_path: Path | None = None,
        source_first_terminal_handoff_dir: Path | None = None,
        promote_final: bool = False,
    ):
        return runner_module.CodexExecReviewCycleRunner(
            repo_root=self.repo_root,
            ft_root=self.ft_root,
            cycle_dir=self.cycle_dir,
            final_path=self.final_path,
            source_files=[],
            handoff_files=[],
            prepared_package_path=package_path,
            prepared_repair_draft_path=repair_draft_path,
            prepared_repair_findings_path=repair_findings_path,
            prepared_reviewer_rebind_draft_path=reviewer_rebind_draft_path,
            source_first_terminal_handoff_dir=source_first_terminal_handoff_dir,
            promotion_contract_path=promotion_contract_path,
            promote_final=promote_final,
            prepared_fast_writer_mode=writer_mode,
            prepared_standard_writer_mode=standard_writer_mode,
            command_config=runner_module.ExecCommandConfig(
                executable="codex-test",
                sandbox_flag="--sandbox-contract",
                writer_sandbox="writer-workspace-write",
                reviewer_sandbox="reviewer-read-only",
                working_directory_flag="--working-directory-contract",
                json_flag="--jsonl-contract",
                output_last_message_flag="--last-message-contract",
                output_schema_flag="--output-schema-contract",
                cli_contract_verified=True,
            ),
            executor=executor,
            validator=self.validator,
            timeout_seconds=5,
            instruction_context_resolver=self.resolve_instruction_context,
        )

    def build_promotion_contract(
        self,
        *,
        required_requirement_ids=("BSR 1",),
        required_gap_ids=("GAP-001",),
    ) -> Path:
        accepted = self.ft_root / "work" / "accepted-candidate.md"
        accepted.parent.mkdir(parents=True, exist_ok=True)
        accepted.write_text("accepted semantic candidate\n", encoding="utf-8")
        contract = self.ft_root / "work" / "promotion-contract.json"
        contract.write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "canonical_test_cases": self.final_path.relative_to(self.repo_root).as_posix(),
                    "canonical_title": "Тест-кейсы: demo",
                    "ft_slug": "demo-ft",
                    "scope_slug": "demo-scope",
                    "section_id": "1",
                    "domain_package_id": "WP-01",
                    "test_design_dir": "fts/demo-ft/work/test-design/1-demo-scope",
                    "test_case_ids": ["TC-DEMO-001"],
                    "expected_priorities": {"TC-DEMO-001": "High"},
                    "required_requirement_ids": list(required_requirement_ids),
                    "required_sections": [
                        "Metadata", "Scope Boundaries", "Coverage Summary", "Coverage Gaps", "Test Cases"
                    ],
                    "required_gap_ids": list(required_gap_ids),
                    "accepted_candidate": accepted.relative_to(self.repo_root).as_posix(),
                    "accepted_candidate_sha256": hashlib.sha256(accepted.read_bytes()).hexdigest(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return contract

    def test_first_artifact_experiment_preserves_independent_writer_budgets(self) -> None:
        parser = runner_module.build_parser()

        self.assertEqual(900, parser.get_default("writer_timeout_seconds"))
        self.assertEqual(180, parser.get_default("writer_idle_timeout_seconds"))
        self.assertEqual(
            600,
            parser.get_default("writer_first_artifact_deadline_seconds"),
        )
        self.assertEqual(
            600,
            runner_module.CodexExecReviewCycleRunner.__dataclass_fields__[
                "writer_first_artifact_deadline_seconds"
            ].default,
        )
        self.assertEqual(
            "structured",
            parser.get_default("prepared_fast_writer_mode"),
        )
        self.assertEqual(
            "structured",
            parser.get_default("prepared_standard_writer_mode"),
        )
        self.assertEqual(
            3,
            parser.get_default("prepared_structured_writer_max_concurrency"),
        )
        self.assertEqual(
            3,
            runner_module.CodexExecReviewCycleRunner.__dataclass_fields__[
                "prepared_structured_writer_max_concurrency"
            ].default,
        )

    def test_prepared_writer_uses_embedded_runtime_limits_not_standard_defaults(self) -> None:
        package_path = self.build_prepared_package()
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        runner.validate_configuration()

        self.assertEqual((180, 60, 12), runner._stage_limits("writer"))

    def test_prepared_runtime_profile_rejects_numeric_package_allowlist_before_attempt(self) -> None:
        package_path = self.build_prepared_package()
        self.prepared_profile_path.write_text(
            "# Prepared Writer Runtime Profile\n\n"
            "Require package version `5` and `package_digest`.\n",
            encoding="utf-8",
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "must not hard-code package version numbers",
        ):
            runner.validate_configuration()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.writer_attempt.exists())

    def test_prepared_package_missing_digest_blocks_before_attempt(self) -> None:
        package_path = self.build_prepared_package()
        payload = json.loads(package_path.read_text(encoding="utf-8"))
        payload.pop("package_digest")
        package_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "Prepared stage package is invalid",
        ):
            runner.validate_configuration()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.writer_attempt.exists())

    def test_prepared_fast_path_uses_only_compact_package_artifacts(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.writer_step(), self.reviewer_step(decision="changes-required")
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("changes-required", result.status)
        writer_prompt = executor.requests[0].prompt
        self.assertIn("prepared writer fast path", writer_prompt)
        self.assertIn("PREPARED-STAGE-PAYLOAD:BEGIN", writer_prompt)
        self.assertIn("Prepared Writer Runtime Profile", writer_prompt)
        self.assertIn("inline numbered setup actions", writer_prompt)
        self.assertIn("ATOM-001", writer_prompt)
        self.assertIn("observable requirement", writer_prompt)
        self.assertIn("do not load the full ft-test-case-writer skill", writer_prompt)
        manifest = json.loads((self.writer_attempt / "stage-input.json").read_text(encoding="utf-8"))
        self.assertEqual("writer.session_prepared_initial_draft", manifest["scenario"])
        self.assertEqual(1, len(manifest["source_artifacts"]))
        self.assertTrue(manifest["source_artifacts"][0]["path"].endswith("source-evidence.md"))
        self.assertFalse(any(item["path"].endswith("main.xhtml") for item in manifest["source_artifacts"]))
        gate = json.loads((self.writer_attempt / "runner-output" / "obligation-gate.json").read_text(encoding="utf-8"))
        self.assertTrue(gate["passed"])
        overlap = json.loads(
            (self.writer_attempt / "runner-output" / "semantic-overlap-diagnostic.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("clean", overlap["status"])
        reviewer_command = executor.requests[1].command
        self.assertIn("--output-schema-contract", reviewer_command)
        schema_path = Path(
            reviewer_command[reviewer_command.index("--output-schema-contract") + 1]
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(2, schema["properties"]["contract_version"]["const"])
        self.assertIn("obligation_reviews", schema["required"])
        variants = schema["properties"]["obligation_reviews"]["items"]["anyOf"]
        self.assertEqual(1, len(variants))
        self.assertEqual(
            "ATOM-001",
            variants[0]["properties"]["obligation_id"]["const"],
        )
        self.assertEqual(
            ["covered", "incorrect", "missing"],
            variants[0]["properties"]["verdict"]["enum"],
        )
        serialized_schema = json.dumps(schema, sort_keys=True)
        self.assertNotIn("uniqueItems", serialized_schema)
        reviewer_manifest = json.loads(
            (self.reviewer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        self.assertEqual("reviewer.session_prepared_semantic", reviewer_manifest["scenario"])
        reviewer_prompt = executor.requests[1].prompt
        self.assertIn("PREPARED-REVIEW-PAYLOAD:BEGIN", reviewer_prompt)
        self.assertIn("Prepared Reviewer Runtime Profile", reviewer_prompt)
        self.assertIn("Immutable writer draft", reviewer_prompt)
        self.assertIn("Semantic overlap diagnostic", reviewer_prompt)
        self.assertIn("reviewed_draft_sha256", reviewer_prompt)
        self.assertIn(
            "do not load the full ft-test-case-reviewer skill", reviewer_prompt.lower()
        )
        self.assertNotIn("stage-package.json`", reviewer_prompt)
        self.assertLessEqual(
            len(reviewer_prompt.encode("utf-8")),
            runner_module.DEFAULT_PREPARED_REVIEWER_PROMPT_MAX_BYTES,
        )

    def test_semantic_overlap_diagnostic_is_non_blocking_and_names_duplicate_bodies(self) -> None:
        draft = self.repo_root / "overlap.md"
        draft.write_text(
            """# Тест-кейсы

## TC-001

**Название:** Проверка редактируемости поля
**Трассировка:** OBL-001; ATOM-001

### Шаги

1. Ввести строковое значение `Тест` в поле.

### Итоговый ожидаемый результат

Значение `Тест` отображается в поле.

## TC-002

**Название:** Проверка строкового типа поля
**Трассировка:** OBL-002; ATOM-002

### Шаги

1. Ввести значение `Тест` в поле.

### Итоговый ожидаемый результат

Значение `Тест` отображается в поле.
""",
            encoding="utf-8",
        )

        report = runner_module.build_semantic_overlap_diagnostic(draft)

        self.assertTrue(report["passed"])
        self.assertFalse(report["blocking"])
        self.assertEqual("overlap-detected", report["status"])
        self.assertEqual(["TC-001", "TC-002"], report["findings"][0]["test_case_ids"])

    def test_prepared_seed_groups_obligations_with_same_planned_test_case_id(self) -> None:
        package_path = self.build_prepared_package(grouped_obligations=True)
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        runner.validate_configuration()
        seed = runner._draft_seed_text()

        self.assertEqual(1, seed.count("## TC-GROUP-001"))
        self.assertIn("ATOM-001; SRC-1; OBL-002; ATOM-002", seed)

    def test_prepared_seed_orders_planned_test_case_ids_numerically(self) -> None:
        package_path = self.build_prepared_package(out_of_order_planned_ids=True)
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        runner.validate_configuration()
        seed = runner._draft_seed_text()

        self.assertLess(seed.index("## TC-GROUP-001"), seed.index("## TC-GROUP-002"))

    def test_source_first_seed_projects_negative_type_and_high_risk_priority(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            source_first_contract=True,
            source_first_polarity="negative",
            source_first_risk="high",
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        runner.validate_configuration()
        seed = runner._draft_seed_text()

        self.assertIn("**Тип:** негативный", seed)
        self.assertIn("**Приоритет:** высокий", seed)

    def test_source_first_seed_prefers_obligation_check_type_over_broad_assertion_polarity(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            source_first_contract=True,
            source_first_polarity="negative",
            source_first_risk="medium",
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        runner.validate_configuration()
        obligation = runner_module.load_obligations(
            runner._prepared_artifact("atomic-obligations")
        ).obligations[0]
        projected = replace(
            obligation,
            test_intent=obligation.test_intent + "; Check type: positive",
        )

        self.assertEqual(
            ("позитивный", "средний"),
            runner._source_first_seed_properties((projected,)),
        )

    def test_prepared_seed_contains_exact_reference_fixture_projection(self) -> None:
        fixtures = (
            PreparedDictionaryValue(
                ("DICT-001", "DICT-101"), "group", "Признаки алкоголика"
            ),
            PreparedDictionaryValue(
                ("DICT-001", "DICT-101"), "leaf", "Первое точное значение"
            ),
            PreparedDictionaryValue(
                ("DICT-001", "DICT-101"), "leaf", "Второе точное значение"
            ),
        )
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
            reference_fixture_values=fixtures,
            structured_dictionary_evidence=True,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        runner.validate_configuration()
        seed = runner._draft_seed_text()

        self.assertIn("runner-reference-fixture:start ATOM-001", seed)
        self.assertIn("Признаки алкоголика", seed)
        self.assertIn("Первое точное значение", seed)
        self.assertIn("Второе точное значение", seed)

    def test_runner_materializes_reference_fixture_before_reviewer(self) -> None:
        fixtures = (
            PreparedDictionaryValue(
                ("DICT-001", "DICT-101"), "group", "Признаки алкоголика"
            ),
            PreparedDictionaryValue(
                ("DICT-001", "DICT-101"), "leaf", "Первое точное значение"
            ),
            PreparedDictionaryValue(
                ("DICT-001", "DICT-101"), "leaf", "Второе точное значение"
            ),
        )
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
            reference_fixture_values=fixtures,
            structured_dictionary_evidence=True,
        )
        generic_v4_style = self.complete_test_case_section(1).replace(
            "ATOM-001; ATOM-001; SRC-1",
            "ATOM-001; SRC-1; DICT-001",
        ).replace(
            "- Значение: `value-1`.",
            "- Два обычных значения из DICT-101.",
        ).replace(
            "1. Ввести `value-1` в поле 1.",
            "1. Последовательно выбрать два обычных значения.",
        )
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text="# Тест-кейсы\n\n" + generic_v4_style),
            self.reviewer_step(),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        materialized = self.draft_path.read_text(encoding="utf-8")
        self.assertIn("runner-reference-fixture:start ATOM-001", materialized)
        self.assertIn("Первое точное значение", materialized)
        self.assertIn("Второе точное значение", materialized)
        projection_report = json.loads(
            (self.writer_attempt / "runner-output" / "dictionary-projection.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            1,
            projection_report["reference_fixtures"]["materialized_count"],
        )

    def test_prepared_writer_creates_absent_stage_owned_output_from_template(self) -> None:
        package_path = self.build_prepared_package()

        def assert_initial_file_state_and_write(request):
            seed = self.writer_attempt / "runner-input" / "draft-seed.md"
            self.assertTrue(seed.is_file())
            self.assertFalse(self.draft_path.exists())
            self.assertIn("output file does not exist", request.prompt)
            self.assertIn("Create it as the first file write", request.prompt)
            self.assertIn("do not use an update-only patch", request.prompt)
            return self.writer_step()(request)

        executor = ScriptedExecutor(
            assert_initial_file_state_and_write,
            self.reviewer_step(decision="accepted"),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertTrue(self.draft_path.is_file())
        self.assertTrue((self.writer_attempt / "runner-input" / "draft-seed.md").is_file())

    def test_prepared_structured_writer_returns_draft_without_workspace_write(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.structured_writer_step(),
            self.reviewer_step(decision="accepted"),
        )

        result = self.make_prepared_runner(
            executor,
            package_path,
            writer_mode="structured",
        ).run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertTrue(self.draft_path.is_file())
        writer_request = executor.requests[0]
        self.assertEqual(0, writer_request.command_budget)
        self.assertIsNone(writer_request.progress_path)
        self.assertIsNone(writer_request.first_artifact_deadline_seconds)
        self.assertIn("reviewer-read-only", writer_request.command)
        self.assertNotIn("writer-workspace-write", writer_request.command)
        self.assertIn("--output-schema-contract", writer_request.command)
        schema_path = Path(
            writer_request.command[
                writer_request.command.index("--output-schema-contract") + 1
            ]
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertNotIn("oneOf", schema)
        self.assertEqual(
            ["draft-ready", "blocked-input"],
            schema["properties"]["status"]["enum"],
        )
        manifest = json.loads(
            (self.writer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        self.assertEqual("read_only", manifest["sandbox_policy"])
        self.assertEqual([], manifest["allowed_write_roots"])
        draft_output = next(
            item for item in manifest["expected_outputs"] if item["kind"] == "test-case-draft"
        )
        self.assertEqual("runner", draft_output["producer"])
        events = (self.cycle_dir / "runner-events.ndjson").read_text(encoding="utf-8")
        self.assertIn("structured_writer_draft_materialized", events)

    def test_prepared_structured_writer_can_return_blocked_input(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.structured_writer_step(
                status="blocked-input",
                blocking_reasons=("ATOM-001 has insufficient inline evidence",),
            )
        )

        result = self.make_prepared_runner(
            executor,
            package_path,
            writer_mode="structured",
        ).run()

        self.assertEqual("blocked-input", result.status)
        self.assertFalse(self.draft_path.exists())
        self.assertEqual(1, len(executor.requests))
        state = (self.cycle_dir / "cycle-state.yaml").read_text(encoding="utf-8")
        self.assertIn('draft_test_cases: ""', state)

    def test_prepared_structured_writer_prompt_defers_environment_binding_to_ui_prep(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("integration-persistence",),
        )
        executor = ScriptedExecutor(
            self.structured_writer_step(),
            self.reviewer_step(),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        writer_prompt = executor.requests[0].prompt
        self.assertIn("runtime-selected integration response", writer_prompt)
        self.assertIn("Do not require a stand record ID", writer_prompt)
        self.assertIn("observable oracle without invention", writer_prompt)
        reviewer_prompt = executor.requests[1].prompt
        self.assertIn("runtime-selected integration response", reviewer_prompt)
        self.assertIn("stand-specific organization", reviewer_prompt)
        self.assertIn("does not by itself assert a blocked transition", reviewer_prompt)

    def test_prepared_structured_writer_rejects_invalid_contract(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.structured_writer_step(
                payload_override={
                    "contract_version": 1,
                    "status": "draft-ready",
                    "draft_markdown": "# Cases",
                    "blocking_reasons": [],
                    "output_path": "fts/demo-ft/test-cases/unsafe.md",
                }
            )
        )

        result = self.make_prepared_runner(
            executor,
            package_path,
            writer_mode="structured",
        ).run()

        self.assertEqual("blocked-invalid-output", result.status)
        self.assertFalse(self.draft_path.exists())
        self.assertFalse(self.final_path.exists())

    def test_prepared_structured_writer_stops_on_any_command(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.structured_writer_step(
                command_count=1,
                command_budget_exceeded=True,
            )
        )

        result = self.make_prepared_runner(
            executor,
            package_path,
            writer_mode="structured",
        ).run()

        self.assertEqual("blocked-command-budget", result.status)
        self.assertFalse(self.draft_path.exists())
        self.assertEqual(1, len(executor.requests))

    def test_prepared_structured_writer_rejects_file_change_event(self) -> None:
        package_path = self.build_prepared_package()

        def file_changing_writer(_request):
            payload = {
                "contract_version": 1,
                "status": "draft-ready",
                "draft_markdown": "# Cases\n\n## TC-DEMO-001\n\n**Traceability:** ATOM-001\n",
                "blocking_reasons": [],
            }
            stdout = self.json_event(
                json.dumps(payload),
                session_id="writer-session",
            )
            stdout += json.dumps(
                {"type": "item.completed", "item": {"type": "file_change"}}
            ) + "\n"
            return self.process_result(stdout=stdout)

        executor = ScriptedExecutor(file_changing_writer)
        result = self.make_prepared_runner(
            executor,
            package_path,
            writer_mode="structured",
        ).run()

        self.assertEqual("blocked-forbidden-workspace-change", result.status)
        self.assertFalse(self.draft_path.exists())
        self.assertEqual(1, len(executor.requests))

    def test_prepared_reviewer_prompt_budget_blocks_oversized_inline_handoff(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(self.writer_step())
        runner = self.make_prepared_runner(
            executor,
            package_path,
            standard_writer_mode="assisted",
        )
        runner.prepared_reviewer_prompt_max_bytes = 32

        with self.assertRaisesRegex(
            runner_module.RunnerError, "blocked-prepared-reviewer-prompt-budget"
        ):
            runner.run()

        self.assertEqual(1, len(executor.requests))

    def test_prepared_reviewer_uses_dedicated_runtime_limits_and_probe_allowlist(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.writer_step(),
            self.reviewer_step(commands=("python scripts/probe_environment.py",)),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        request = executor.requests[1]
        self.assertEqual(90, request.timeout_seconds)
        self.assertIsNone(request.idle_timeout_seconds)
        self.assertEqual(1, request.command_budget)
        report = json.loads(
            (self.reviewer_attempt / "runner-output" / "evidence-access-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(report["passed"])

    def test_prepared_reviewer_blocks_skill_read(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.writer_step(),
            self.reviewer_step(
                commands=("Get-Content skills/ft-test-case-reviewer/SKILL.md",)
            ),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-evidence-access", result.status)
        report = json.loads(
            (self.reviewer_attempt / "runner-output" / "evidence-access-report.json").read_text(
                encoding="utf-8"
            )
        )
        ids = {finding["id"] for finding in report["findings"]}
        self.assertIn("unapproved-prepared-stage-command", ids)

    def test_prepared_fast_path_blocks_before_reviewer_when_atom_is_uncovered(self) -> None:
        package_path = self.build_prepared_package()

        def uncovered_writer(_request):
            self.draft_path.parent.mkdir(parents=True, exist_ok=True)
            self.draft_path.write_text("# Cases\n\n## TC-DEMO-001\nNo traceability.\n", encoding="utf-8")
            return self.process_result(
                stdout=self.json_event("writer completed", session_id="writer-session")
            )

        executor = ScriptedExecutor(uncovered_writer)
        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-obligation-gate", result.status)
        self.assertEqual(1, len(executor.requests))
        gate = json.loads((self.writer_attempt / "runner-output" / "obligation-gate.json").read_text(encoding="utf-8"))
        self.assertFalse(gate["passed"])
        self.assertEqual("missing-testable-obligation-coverage", gate["findings"][0]["id"])

    def test_prepared_fast_path_rejects_unchanged_seed(self) -> None:
        package_path = self.build_prepared_package()

        def seed_only_writer(_request):
            self.draft_path.parent.mkdir(parents=True, exist_ok=True)
            seed = self.writer_attempt / "runner-input" / "draft-seed.md"
            self.draft_path.write_bytes(seed.read_bytes())
            return self.process_result(
                stdout=self.json_event("writer completed", session_id="writer-session")
            )

        executor = ScriptedExecutor(seed_only_writer)
        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-seed-gate", result.status)
        self.assertEqual(1, len(executor.requests))
        gate = json.loads(
            (self.writer_attempt / "runner-output" / "seed-gate.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(gate["passed"])
        self.assertIn("draft-seed-placeholder-remains", {item["id"] for item in gate["findings"]})

    def test_prepared_fast_path_blocks_forbidden_evidence_access(self) -> None:
        package_path = self.build_prepared_package()
        stdout = self.json_event("writer started", session_id="writer-session")
        stdout += json.dumps(
            {
                "type": "item.started",
                "item": {
                    "id": "forbidden-command",
                    "type": "command_execution",
                    "command": "Get-Content fts/demo-ft/test-cases/old.md",
                },
            }
        ) + "\n"
        executor = ScriptedExecutor(self.writer_step(stdout=stdout))

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-evidence-access", result.status)
        report = json.loads(
            (self.writer_attempt / "runner-output" / "evidence-access-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(report["passed"])
        self.assertEqual("forbidden-evidence-root-access", report["findings"][0]["id"])

    def test_prepared_fast_path_allows_writer_to_read_current_stage_output(self) -> None:
        package_path = self.build_prepared_package(
            forbidden_evidence_roots=("fts/demo-ft/work/review-cycles",),
        )
        stdout = self.json_event("writer started", session_id="writer-session")
        stdout += json.dumps(
            {
                "type": "item.started",
                "item": {
                    "id": "own-output-command",
                    "type": "command_execution",
                    "command": (
                        "Get-Content "
                        + self.draft_path.relative_to(self.repo_root).as_posix()
                    ),
                },
            }
        ) + "\n"
        executor = ScriptedExecutor(
            self.writer_step(stdout=stdout),
            self.reviewer_step(decision="accepted"),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        report = json.loads(
            (self.writer_attempt / "runner-output" / "evidence-access-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(report["passed"])

    def test_prepared_fast_path_rejects_tampered_package_before_exec(self) -> None:
        package_path = self.build_prepared_package()
        (package_path.parent / "source-evidence.md").write_text("tampered\n", encoding="utf-8")
        executor = ScriptedExecutor()

        with self.assertRaisesRegex(runner_module.RunnerError, "Prepared stage package is invalid"):
            self.make_prepared_runner(executor, package_path).run()
        self.assertEqual([], executor.requests)

    def test_prepared_fast_path_rejects_foreign_attempt_binding_before_exec(self) -> None:
        foreign_attempt = (
            self.ft_root
            / "work"
            / "review-cycles"
            / "foreign-cycle"
            / "attempts"
            / "writer-r1"
            / "attempt-001"
        )
        package_path = self.build_prepared_package(
            instruction_attempt_root=foreign_attempt,
        )
        executor = ScriptedExecutor()

        with self.assertRaisesRegex(runner_module.RunnerError, "attempt binding mismatch"):
            self.make_prepared_runner(executor, package_path).run()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.cycle_dir.joinpath("cycle-state.yaml").exists())

    def test_ineligible_prepared_profile_routes_to_standard_writer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-writer-required",
            unsupported_dimensions=("numeric-boundaries",),
        )
        executor = ScriptedExecutor()

        with self.assertRaisesRegex(runner_module.RunnerError, "route to standard writer"):
            self.make_prepared_runner(executor, package_path).run()
        self.assertEqual([], executor.requests)

    def test_writer_command_uses_configured_workspace_write_sandbox(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="changes-required"))
        self.make_runner(executor).run()

        command = executor.requests[0].command
        self.assertEqual(("codex-test", "exec"), command[:2])
        self.assertEqual("writer-workspace-write", command[command.index("--sandbox-contract") + 1])
        self.assertTrue(
            Path(command[command.index("--working-directory-contract") + 1]).samefile(self.repo_root)
        )
        self.assertIn("--jsonl-contract", command)
        self.assertIn("--last-message-contract", command)
        self.assertEqual("-", command[-1])

    def test_standard_path_routes_role_specific_instruction_files(self) -> None:
        writer_instruction = self.repo_root / "writer-instructions.md"
        reviewer_instruction = self.repo_root / "reviewer-instructions.md"
        writer_instruction.write_text("# Writer only\n", encoding="utf-8")
        reviewer_instruction.write_text("# Reviewer only\n", encoding="utf-8")
        executor = ScriptedExecutor(
            self.writer_step(),
            self.reviewer_step(decision="changes-required"),
        )
        cycle = self.make_runner(executor)
        cycle.writer_instruction_files = (writer_instruction,)
        cycle.reviewer_instruction_files = (reviewer_instruction,)

        cycle.run()

        writer_prompt = executor.requests[0].prompt
        reviewer_prompt = executor.requests[1].prompt
        self.assertIn("writer.session_initial_draft", writer_prompt)
        self.assertIn("--budget-report --fail-on-budget", writer_prompt)
        self.assertIn("writer-runtime.md", writer_prompt)
        self.assertNotIn("reviewer-runtime.md", writer_prompt)
        self.assertIn("writer-instructions.md", writer_prompt)
        self.assertNotIn("reviewer-instructions.md", writer_prompt)
        self.assertIn("reviewer.semantic_traceability_test_design", reviewer_prompt)
        self.assertIn("--budget-report --fail-on-budget", reviewer_prompt)
        self.assertIn("reviewer-runtime.md", reviewer_prompt)
        self.assertNotIn("writer-runtime.md", reviewer_prompt)
        self.assertIn("reviewer-instructions.md", reviewer_prompt)
        self.assertNotIn("writer-instructions.md", reviewer_prompt)
        writer_manifest = json.loads(
            (self.writer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        reviewer_manifest = json.loads(
            (self.reviewer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            any(
                item["path"].endswith("writer-instructions.md")
                for item in writer_manifest["instruction_artifacts"]
            )
        )
        self.assertTrue(
            any(
                item["path"].endswith("reviewer-instructions.md")
                for item in reviewer_manifest["instruction_artifacts"]
            )
        )

    def test_standard_path_automatically_routes_existing_package_notes_to_both_roles(self) -> None:
        package_notes = self.ft_root / "AGENT-NOTES.md"
        package_notes.write_text("# Mandatory package context\n", encoding="utf-8")
        executor = ScriptedExecutor(
            self.writer_step(),
            self.reviewer_step(decision="changes-required"),
        )

        cycle = self.make_runner(executor)
        cycle.run()

        self.assertIn("fts/demo-ft/AGENT-NOTES.md", executor.requests[0].prompt)
        self.assertIn("fts/demo-ft/AGENT-NOTES.md", executor.requests[1].prompt)
        writer_manifest = json.loads(
            (self.writer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        reviewer_manifest = json.loads(
            (self.reviewer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            any(
                item["path"].endswith("AGENT-NOTES.md")
                for item in writer_manifest["handoff_artifacts"]
            )
        )
        self.assertTrue(
            any(
                item["path"].endswith("AGENT-NOTES.md")
                for item in reviewer_manifest["handoff_artifacts"]
            )
        )

    def test_standard_path_blocks_before_session_when_instruction_budget_does_not_pass(self) -> None:
        executor = ScriptedExecutor()
        cycle = self.make_runner(executor)

        def near_limit_context(*, root: Path, scenario_id: str):
            result = self.resolve_instruction_context(root=root, scenario_id=scenario_id)
            result["budget"] = {
                "status": "near_limit",
                "total_kib": 9.5,
                "limit_kib": 10.0,
            }
            return result

        cycle.instruction_context_resolver = near_limit_context

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "Instruction context budget failed",
        ):
            cycle.run()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.cycle_dir.joinpath("cycle-state.yaml").exists())

    def test_prepared_standard_route_uses_compact_package_with_full_standard_context(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
        )
        executor = ScriptedExecutor(
            self.writer_step(),
            self.reviewer_step(decision="changes-required"),
        )

        runner = self.make_prepared_runner(
            executor,
            package_path,
            standard_writer_mode="assisted",
        )
        runner.reviewer_timeout_seconds = 450
        result = runner.run()

        self.assertEqual("changes-required", result.status)
        writer_prompt = executor.requests[0].prompt
        reviewer_prompt = executor.requests[1].prompt
        self.assertIn("prepared-standard writer", writer_prompt)
        self.assertIn("writer.session_initial_draft", writer_prompt)
        self.assertIn("writer-runtime.md", writer_prompt)
        self.assertNotIn("Prepared Writer Runtime Profile", writer_prompt)
        self.assertIn("## Atomic obligations", writer_prompt)
        self.assertNotIn("## Verified obligation transport", writer_prompt)
        self.assertIn("prepared-standard reviewer", reviewer_prompt)
        self.assertIn("reviewer.semantic_traceability_test_design", reviewer_prompt)
        self.assertIn("reviewer-runtime.md", reviewer_prompt)
        self.assertNotIn("Prepared Reviewer Runtime Profile", reviewer_prompt)
        self.assertIn("## Atomic obligations", reviewer_prompt)
        self.assertIn("## Calibration lifecycle", reviewer_prompt)
        self.assertNotIn("## Verified obligation review index", reviewer_prompt)
        self.assertEqual(300, executor.requests[1].idle_timeout_seconds)

        writer_manifest = json.loads(
            (self.writer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        reviewer_manifest = json.loads(
            (self.reviewer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        self.assertEqual("writer.session_initial_draft", writer_manifest["scenario"])
        self.assertEqual(
            "reviewer.semantic_traceability_test_design",
            reviewer_manifest["scenario"],
        )
        self.assertTrue(
            all(not item["path"].endswith("main.docx") for item in writer_manifest["source_artifacts"])
        )
        self.assertTrue(
            (self.writer_attempt / "runner-output" / "context-budget.json").is_file()
        )
        self.assertTrue(
            (self.reviewer_attempt / "runner-output" / "context-budget.json").is_file()
        )

    def test_prepared_standard_defaults_to_compact_structured_sessions(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
        )
        executor = ScriptedExecutor(
            self.structured_writer_step(),
            self.reviewer_step(),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        package_payload = json.loads(package_path.read_text(encoding="utf-8"))
        expected_version = f'"package_version": {runner_module.PACKAGE_VERSION}'
        expected_digest = f'"package_digest": "{package_payload["package_digest"]}"'
        self.assertIn(expected_version, executor.requests[0].prompt)
        self.assertIn(expected_digest, executor.requests[0].prompt)
        self.assertIn(expected_version, executor.requests[1].prompt)
        self.assertIn(expected_digest, executor.requests[1].prompt)
        self.assertEqual(0, executor.requests[0].command_budget)
        self.assertEqual("read_only", json.loads(
            (self.writer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )["sandbox_policy"])
        self.assertIn("Prepared Writer Runtime Profile", executor.requests[0].prompt)
        self.assertNotIn("writer-runtime.md", executor.requests[0].prompt)
        self.assertIn("## Verified obligation transport", executor.requests[0].prompt)
        self.assertNotIn("## Atomic obligations", executor.requests[0].prompt)
        self.assertIn("runner-generated-draft-seed", executor.requests[0].prompt)
        self.assertIn("Prepared Reviewer Runtime Profile", executor.requests[1].prompt)
        self.assertNotIn("reviewer-runtime.md", executor.requests[1].prompt)
        self.assertIn("## Verified obligation review index", executor.requests[1].prompt)
        self.assertNotIn("## Atomic obligations", executor.requests[1].prompt)
        self.assertIn("## Calibration lifecycle summary", executor.requests[1].prompt)
        self.assertIn('"semantic_evidence_source":"selected-source-evidence"', executor.requests[1].prompt)
        self.assertIn('"obligation_id":"ATOM-001"', executor.requests[1].prompt)
        self.assertTrue((self.writer_attempt / "artifact-graph.json").is_file())
        self.assertTrue((self.reviewer_attempt / "artifact-graph.json").is_file())
        graph = json.loads((self.writer_attempt / "artifact-graph.json").read_text(encoding="utf-8"))
        self.assertEqual("character-restriction-calibration", graph["context_profile"])
        self.assertEqual("read_only", graph["access_policy"]["sandbox"])
        self.assertTrue(all("lifecycle" in item for item in graph["input_nodes"]))
        self.assertTrue(all("consumers" in item for item in graph["output_nodes"]))

    def test_output_capacity_preflight_blocks_unsafe_one_shot_without_sharding(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 2
        runner.prepared_structured_writer_shard_size = 0

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "blocked-prepared-writer-output-capacity",
        ):
            runner.validate_configuration()

        self.assertFalse((self.cycle_dir / "writer-output-capacity-preflight.json").exists())
        self.assertFalse(self.writer_attempt.exists())

    def test_output_capacity_at_exact_limit_runs_one_writer_without_shards(self) -> None:
        test_case_count = 14
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=test_case_count,
        )
        draft = "# Тест-кейсы\n\n" + "\n\n".join(
            self.complete_test_case_section(index).strip()
            for index in range(1, test_case_count + 1)
        ) + "\n"
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=draft),
            self.prepared_reviewer_step_for_count(test_case_count),
        )
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_structured_writer_single_session_tc_limit = test_case_count
        runner.prepared_structured_writer_shard_size = test_case_count
        runner.prepared_structured_writer_max_shards = 1
        runner.prepared_structured_writer_max_concurrency = 1

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertEqual(
            [("writer-r1", "writer"), ("reviewer-r1", "reviewer")],
            [(request.stage, request.role) for request in executor.requests],
        )
        capacity = json.loads(
            (self.cycle_dir / "writer-output-capacity-preflight.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(capacity["passed"])
        self.assertEqual("single-session", capacity["mode"])
        self.assertEqual(test_case_count, capacity["test_case_count"])
        self.assertEqual(
            test_case_count, capacity["single_session_test_case_limit"]
        )
        self.assertEqual(test_case_count, capacity["configured_shard_size"])
        self.assertEqual(1, capacity["max_shards"])
        self.assertEqual(1, capacity["configured_max_concurrency"])
        self.assertEqual(0, capacity["shard_count"])
        self.assertEqual(0, capacity["wave_count"])
        self.assertEqual([], capacity["shards"])
        self.assertFalse((self.cycle_dir / "writer-shard-plan.json").exists())
        self.assertFalse(
            (self.cycle_dir / "attempts" / "writer-r1-shard-002").exists()
        )

    def test_output_capacity_above_limit_with_one_max_shard_fails_closed(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=15,
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 14
        runner.prepared_structured_writer_shard_size = 14
        runner.prepared_structured_writer_max_shards = 1
        runner.prepared_structured_writer_max_concurrency = 1

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            (
                "blocked-prepared-writer-output-capacity: "
                "test_case_count=15, single_session_limit=14, "
                "shard_size=14, max_shards=1"
            ),
        ):
            runner.validate_configuration()

        self.assertEqual([], executor.requests)
        self.assertFalse(
            (self.cycle_dir / "writer-output-capacity-preflight.json").exists()
        )
        self.assertFalse((self.cycle_dir / "writer-shard-plan.json").exists())
        self.assertFalse(self.writer_attempt.exists())

    def test_output_capacity_preflight_builds_disjoint_complete_shards(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 2
        runner.prepared_structured_writer_shard_size = 2

        report = runner.validate_only_report()
        capacity = report["writer_output_capacity"]

        self.assertTrue(report["writer_sharded"])
        self.assertTrue(capacity["passed"])
        self.assertTrue(capacity["union_complete"])
        self.assertTrue(capacity["disjoint"])
        self.assertEqual(2, capacity["shard_count"])
        self.assertEqual(3, capacity["test_case_count"])
        self.assertEqual(3, capacity["obligation_count"])
        self.assertEqual(
            ["TC-DEMO-001", "TC-DEMO-002"],
            capacity["shards"][0]["test_case_ids"],
        )
        self.assertEqual(
            ["TC-DEMO-003"], capacity["shards"][1]["test_case_ids"]
        )
        self.assertFalse(self.writer_attempt.exists())

    def test_reviewer_output_capacity_blocks_before_writer_live(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.prepared_structured_reviewer_obligation_limit = 2

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "blocked-prepared-reviewer-output-capacity",
        ):
            runner.validate_configuration()

        self.assertFalse(self.writer_attempt.exists())

    def test_prepared_oracle_quality_blocks_non_observable_oracle_before_attempt(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            first_observable_oracle="Точная UI-реакция не определена.",
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "blocked-prepared-oracle-quality",
        ):
            runner.validate_configuration()

        self.assertFalse(self.writer_attempt.exists())
        self.assertFalse(
            (self.cycle_dir / "prepared-oracle-quality-preflight.json").exists()
        )

    def test_prepared_oracle_quality_accepts_observable_evidence_record(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            first_observable_oracle=(
                "Создан evidence record: введённое значение, "
                "точное действие, видимое состояние поля и outcome."
            ),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        report = runner.validate_only_report()

        self.assertTrue(report["prepared_oracle_quality"]["passed"])
        self.assertEqual(
            1,
            report["prepared_oracle_quality"]["testable_obligations_checked"],
        )
        self.assertFalse(self.writer_attempt.exists())

    def test_prepared_state_change_blocks_reset_classification_without_contract(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("dependency-state",),
            first_observable_oracle=(
                "After Clear the visible state matches the captured initial state."
            ),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "blocked-prepared-state-change-quality",
        ):
            runner.validate_configuration()

        self.assertFalse(self.writer_attempt.exists())
        self.assertFalse(
            (self.cycle_dir / "prepared-state-change-preflight.json").exists()
        )

    def test_prepared_state_change_accepts_explicit_changed_prestate_contract(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("dependency-state",),
            first_observable_oracle=(
                "After Clear the visible state matches the captured initial state."
            ),
            first_execution_semantics="reset-to-captured-initial",
            first_state_change=PreparedStateChange(
                initial_state_capture="Capture the visible initial state.",
                changed_state_setup=(
                    "Choose a visible state different from the captured initial state."
                ),
                pre_action_state_oracle=(
                    "Before Clear the visible state differs from the captured initial state."
                ),
            ),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        report = runner.validate_only_report()

        self.assertTrue(report["prepared_state_change"]["passed"])
        self.assertEqual(
            1,
            report["prepared_state_change"]["reset_obligations_checked"],
        )
        self.assertFalse(self.writer_attempt.exists())

    def test_targeted_repair_replaces_only_findings_and_uses_fresh_sessions(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        prior_root = (
            self.ft_root
            / "work"
            / "review-cycles"
            / "prior-v6"
            / "attempts"
            / "writer-r1"
            / "attempt-001"
        )
        prior_draft = prior_root / "stage-output" / "draft.md"
        prior_draft.parent.mkdir(parents=True)
        prior_sections = [
            self.complete_test_case_section(
                1,
                expected="Точная UI-реакция не определена.",
            ),
            self.complete_test_case_section(2),
            self.complete_test_case_section(
                3,
                expected="Точная UI-реакция не определена.",
            ),
        ]
        prior_draft.write_text(
            "# Тест-кейсы\n\n" + "\n\n".join(prior_sections).rstrip() + "\n",
            encoding="utf-8",
        )
        findings_path = prior_root / "runner-output" / "quality-gate-bundle.json"
        findings_path.parent.mkdir(parents=True)
        findings_path.write_text(
            json.dumps(
                {
                    "passed": False,
                    "findings": [
                        {
                            "id": "observable-oracle-contract-mismatch",
                            "severity": "error",
                            "tc_id": "TC-DEMO-001",
                        },
                        {
                            "id": "non-observable-expected-result",
                            "severity": "error",
                            "test_case_ids": ["TC-DEMO-003"],
                        },
                        {
                            "id": "duplicate-title",
                            "severity": "error",
                            "test_case_ids": ["TC-DEMO-001", "TC-DEMO-003"],
                        },
                        {
                            "id": "production-unobservable-address-decomposition",
                            "severity": "error",
                            "tc_id": "TC-DEMO-001",
                            "obligation_id": "OBL-001",
                            "atom_id": "ATOM-001",
                            "message": (
                                "Capture the selected DaData components, reveal the "
                                "manual fields, and compare their visible values."
                            ),
                        },
                    ],
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        replacement = (
            ROOT_DIR
            / "evals"
            / "prepared-targeted-oracle-repair"
            / "20260713"
            / "corrected-repair-sections.md"
        ).read_text(encoding="utf-8")
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=replacement),
            self.prepared_reviewer_step_for_count(3),
        )
        runner = self.make_prepared_runner(
            executor,
            package_path,
            repair_draft_path=prior_draft,
            repair_findings_path=findings_path,
        )

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertEqual(2, len(executor.requests))
        self.assertEqual("writer-r1", executor.requests[0].stage)
        self.assertEqual("reviewer-r1", executor.requests[1].stage)
        self.assertIn("unsigned repair input only", executor.requests[0].prompt)
        self.assertIn("selected source-backed evidence", executor.requests[0].prompt)
        self.assertIn(
            "Mandatory repair acceptance contracts",
            executor.requests[0].prompt,
        )
        self.assertIn(
            '"finding_id":"production-unobservable-address-decomposition"',
            executor.requests[0].prompt,
        )
        self.assertIn(
            "Use one explicit address branch",
            executor.requests[0].prompt,
        )
        self.assertIn(
            "Capture the selected DaData components",
            executor.requests[0].prompt,
        )
        self.assertNotEqual(
            executor.requests[0].prompt,
            executor.requests[1].prompt,
        )
        capacity = json.loads(
            (self.cycle_dir / "writer-output-capacity-preflight.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("targeted-repair", capacity["mode"])
        self.assertEqual(
            ["TC-DEMO-001", "TC-DEMO-003"],
            capacity["target_test_case_ids"],
        )
        repair_plan = json.loads(
            (self.cycle_dir / "writer-targeted-repair-plan.json").read_text(
                encoding="utf-8"
            )
        )
        address_contract = next(
            item
            for item in repair_plan["repair_contracts"]
            if item["finding_id"]
            == "production-unobservable-address-decomposition"
        )
        self.assertEqual(["TC-DEMO-001"], address_contract["test_case_ids"])
        self.assertEqual("OBL-001", address_contract["obligation_id"])
        self.assertEqual("ATOM-001", address_contract["atom_id"])
        splice = json.loads(
            (self.writer_attempt / "runner-output" / "repair-splice.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(splice["passed"])
        self.assertTrue(splice["all_non_target_sections_byte_preserved"])
        preserved = next(
            item for item in splice["sections"] if item["test_case_id"] == "TC-DEMO-002"
        )
        self.assertEqual(preserved["source_sha256"], preserved["output_sha256"])
        self.assertFalse(self.final_path.exists())

    def test_targeted_repair_migrates_only_package_metadata_in_preserved_sections(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        prior_root = self.ft_root / "work" / "review-cycles" / "prior-v7"
        prior_draft = prior_root / "draft.md"
        prior_draft.parent.mkdir(parents=True)
        prior_sections = [
            self.complete_test_case_section(index).replace(
                "pkg-exec-001", "pkg-exec-v7"
            )
            for index in range(1, 4)
        ]
        prior_draft.write_text(
            "# Тест-кейсы\n\n" + "\n\n".join(prior_sections).rstrip() + "\n",
            encoding="utf-8",
        )
        findings_path = prior_root / "quality-gate-bundle.json"
        findings_path.write_text(
            json.dumps(
                {
                    "findings": [
                        {
                            "id": "non-observable-expected-result",
                            "severity": "error",
                            "test_case_ids": ["TC-DEMO-001", "TC-DEMO-003"],
                        }
                    ]
                }
            )
            + "\n",
            encoding="utf-8",
        )
        replacement = "\n\n".join(
            (self.complete_test_case_section(1), self.complete_test_case_section(3))
        )
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=replacement),
            self.prepared_reviewer_step_for_count(3),
        )
        runner = self.make_prepared_runner(
            executor,
            package_path,
            repair_draft_path=prior_draft,
            repair_findings_path=findings_path,
        )

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        splice = json.loads(
            (self.writer_attempt / "runner-output" / "repair-splice.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(splice["passed"])
        self.assertFalse(splice["all_non_target_sections_byte_preserved"])
        self.assertTrue(splice["all_non_target_test_semantics_preserved"])
        self.assertEqual(
            ["TC-DEMO-002"], splice["metadata_migrated_test_case_ids"]
        )
        preserved = next(
            item for item in splice["sections"] if item["test_case_id"] == "TC-DEMO-002"
        )
        self.assertFalse(preserved["byte_preserved"])
        self.assertTrue(preserved["semantic_body_preserved"])
        metadata_gate = json.loads(
            (self.writer_attempt / "runner-output" / "package-metadata-gate.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(metadata_gate["passed"])
        merged = self.draft_path.read_text(encoding="utf-8")
        self.assertNotIn("pkg-exec-v7", merged)
        self.assertEqual(3, merged.count("**package_id:** pkg-exec-001"))

    def test_prepared_package_metadata_gate_rejects_wrong_package_id(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        self.draft_path.parent.mkdir(parents=True)
        self.draft_path.write_text(
            "# Тест-кейсы\n\n"
            + self.complete_test_case_section(1).replace(
                "**package_id:** pkg-exec-001",
                "**package_id:** pkg-exec-v7",
            )
            + "\n",
            encoding="utf-8",
        )

        validation = runner._validate_draft_package_metadata()

        self.assertFalse(validation.passed)
        self.assertEqual("prepared-package-metadata-gate-v1", validation.validator)
        self.assertEqual("package-id-mismatch", validation.findings[0]["id"])
        self.assertEqual("pkg-exec-001", validation.findings[0]["expected_package_id"])
        self.assertEqual("pkg-exec-v7", validation.findings[0]["actual_package_id"])

    def test_targeted_repair_blocks_extra_test_case_before_reviewer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=2,
        )
        prior_root = self.ft_root / "work" / "review-cycles" / "prior-v6"
        prior_draft = prior_root / "draft.md"
        prior_draft.parent.mkdir(parents=True)
        prior_draft.write_text(
            "# Тест-кейсы\n\n"
            + "\n\n".join(
                (self.complete_test_case_section(1), self.complete_test_case_section(2))
            ).rstrip()
            + "\n",
            encoding="utf-8",
        )
        findings_path = prior_root / "quality-gate-bundle.json"
        findings_path.write_text(
            json.dumps(
                {
                    "findings": [
                        {
                            "id": "non-observable-expected-result",
                            "severity": "error",
                            "test_case_ids": ["TC-DEMO-001"],
                        }
                    ]
                }
            )
            + "\n",
            encoding="utf-8",
        )
        invalid_replacement = "\n\n".join(
            (self.complete_test_case_section(1), self.complete_test_case_section(2))
        )
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=invalid_replacement)
        )
        runner = self.make_prepared_runner(
            executor,
            package_path,
            repair_draft_path=prior_draft,
            repair_findings_path=findings_path,
        )

        result = runner.run()

        self.assertEqual("blocked-repair-gate", result.status)
        self.assertEqual(1, len(executor.requests))
        repair_validation = json.loads(
            (self.writer_attempt / "runner-output" / "repair-validator.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(repair_validation["passed"])
        self.assertIn(
            "writer-shard-test-case-set-mismatch",
            {item["id"] for item in repair_validation["findings"]},
        )

    def test_targeted_repair_rejects_input_hash_drift(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=2,
        )
        prior_root = self.ft_root / "work" / "review-cycles" / "prior-v6"
        prior_draft = prior_root / "draft.md"
        prior_draft.parent.mkdir(parents=True)
        prior_draft.write_text(
            "# Тест-кейсы\n\n"
            + "\n\n".join(
                (self.complete_test_case_section(1), self.complete_test_case_section(2))
            ).rstrip()
            + "\n",
            encoding="utf-8",
        )
        findings_path = prior_root / "quality-gate-bundle.json"
        findings_path.write_text(
            json.dumps(
                {
                    "findings": [
                        {
                            "id": "non-observable-expected-result",
                            "severity": "error",
                            "test_case_ids": ["TC-DEMO-001"],
                        }
                    ]
                }
            )
            + "\n",
            encoding="utf-8",
        )
        runner = self.make_prepared_runner(
            ScriptedExecutor(),
            package_path,
            repair_draft_path=prior_draft,
            repair_findings_path=findings_path,
        )
        runner.validate_configuration()
        prior_draft.write_text(
            prior_draft.read_text(encoding="utf-8") + "<!-- drift -->\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "repair source draft changed after preflight",
        ):
            runner._verify_repair_inputs()

    def test_reviewer_rebind_skips_writer_llm_and_preserves_test_semantics(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        prior_draft = (
            self.ft_root
            / "work"
            / "review-cycles"
            / "prior-v8"
            / "attempts"
            / "writer-r1"
            / "attempt-001"
            / "stage-output"
            / "draft.md"
        )
        prior_draft.parent.mkdir(parents=True)
        source_text = "# Тест-кейсы\n\n" + "\n\n".join(
            self.complete_test_case_section(index).replace(
                "pkg-exec-001", "pkg-exec-v8"
            )
            for index in range(1, 4)
        ).rstrip() + "\n"
        prior_draft.write_text(source_text, encoding="utf-8")
        source_sha256 = hashlib.sha256(prior_draft.read_bytes()).hexdigest()
        executor = ScriptedExecutor(self.prepared_reviewer_step_for_count(3))
        runner = self.make_prepared_runner(
            executor,
            package_path,
            reviewer_rebind_draft_path=prior_draft,
        )

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertEqual(1, len(executor.requests))
        self.assertEqual("reviewer", executor.requests[0].role)
        self.assertFalse((self.writer_attempt / "prompt.md").exists())
        self.assertFalse((self.writer_attempt / "metrics.json").exists())
        self.assertEqual(source_sha256, hashlib.sha256(prior_draft.read_bytes()).hexdigest())
        rebound = self.draft_path.read_text(encoding="utf-8")
        self.assertNotIn("pkg-exec-v8", rebound)
        self.assertEqual(3, rebound.count("**package_id:** pkg-exec-001"))
        report = json.loads(
            (self.cycle_dir / "reviewer-rebind.json").read_text(encoding="utf-8")
        )
        self.assertTrue(report["passed"])
        self.assertTrue(report["deterministic_gates_passed"])
        self.assertTrue(report["all_test_semantics_preserved"])
        self.assertFalse(report["writer_llm_started"])
        self.assertEqual(
            ["TC-DEMO-001", "TC-DEMO-002", "TC-DEMO-003"],
            report["metadata_migrated_test_case_ids"],
        )
        state = (self.cycle_dir / "cycle-state.yaml").read_text(encoding="utf-8")
        self.assertIn("writer_stage_status: skipped-reviewer-rebind", state)

    def test_reviewer_rebind_accepts_prior_runner_dictionary_projection(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            dictionary_values=("Первое значение", "Второе значение"),
            structured_dictionary_evidence=True,
            dictionary_coverage_mode="all-leaf-values",
        )
        source_text = (
            "# Тест-кейсы\n\n"
            + self.complete_test_case_section(1)
            .replace("SRC-1", "SRC-1; DICT-001")
            .replace("- Значение: `value-1`.", "- Полный набор DICT-001.")
        )
        projected, initial_report = (
            runner_module.materialize_draft_dictionary_projections(
                source_text,
                runner_module.load_obligations(
                    package_path.parent / "atomic-obligations.json"
                ),
            )
        )
        self.assertEqual(1, initial_report["materialized_count"])
        prior_draft = (
            self.ft_root
            / "work"
            / "review-cycles"
            / "prior-runner-projected"
            / "attempts"
            / "writer-r1"
            / "attempt-001"
            / "stage-output"
            / "draft.md"
        )
        prior_draft.parent.mkdir(parents=True)
        prior_draft.write_text(projected, encoding="utf-8")
        executor = ScriptedExecutor(self.prepared_reviewer_step_for_count(1))
        runner = self.make_prepared_runner(
            executor,
            package_path,
            reviewer_rebind_draft_path=prior_draft,
        )

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertEqual(1, len(executor.requests))
        self.assertEqual("reviewer", executor.requests[0].role)
        projection = json.loads(
            (self.writer_attempt / "runner-output" / "dictionary-projection.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(projection["writer_ownership"]["passed"])
        self.assertFalse(projection["draft_changed"])
        rebind = json.loads(
            (self.cycle_dir / "reviewer-rebind.json").read_text(encoding="utf-8")
        )
        self.assertFalse(rebind["writer_llm_started"])

    def test_reviewer_rebind_rejects_input_hash_drift(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=2,
        )
        prior_draft = (
            self.ft_root / "work" / "review-cycles" / "prior-v8" / "draft.md"
        )
        prior_draft.parent.mkdir(parents=True)
        prior_draft.write_text(
            "# Тест-кейсы\n\n"
            + "\n\n".join(
                (self.complete_test_case_section(1), self.complete_test_case_section(2))
            ).rstrip()
            + "\n",
            encoding="utf-8",
        )
        runner = self.make_prepared_runner(
            ScriptedExecutor(),
            package_path,
            reviewer_rebind_draft_path=prior_draft,
        )
        runner.validate_configuration()
        prior_draft.write_text(
            prior_draft.read_text(encoding="utf-8") + "<!-- drift -->\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "reviewer rebind source draft changed after preflight",
        ):
            runner._verify_reviewer_rebind_input()

    def test_reviewer_rebind_validate_only_starts_no_stage(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=2,
        )
        prior_draft = (
            self.ft_root / "work" / "review-cycles" / "prior-v8" / "draft.md"
        )
        prior_draft.parent.mkdir(parents=True)
        prior_draft.write_text(
            "# Тест-кейсы\n\n"
            + "\n\n".join(
                (self.complete_test_case_section(1), self.complete_test_case_section(2))
            ).rstrip()
            + "\n",
            encoding="utf-8",
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(
            executor,
            package_path,
            reviewer_rebind_draft_path=prior_draft,
        )

        report = runner.validate_only_report()

        self.assertEqual("runner.prepared_reviewer_rebind", report["writer_scenario"])
        self.assertFalse(report["writer_llm_required"])
        self.assertEqual(0, report["writer_command_budget"])
        self.assertEqual([], executor.requests)
        self.assertFalse((self.cycle_dir / "reviewer-rebind.json").exists())
        self.assertFalse(self.writer_attempt.exists())
        self.assertFalse(self.reviewer_attempt.exists())

    def test_reviewer_rebind_gate_failure_blocks_before_reviewer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=2,
        )
        prior_draft = (
            self.ft_root / "work" / "review-cycles" / "prior-v8" / "draft.md"
        )
        prior_draft.parent.mkdir(parents=True)
        prior_draft.write_text(
            "# Тест-кейсы\n\n"
            + "\n\n".join(
                (self.complete_test_case_section(1), self.complete_test_case_section(2))
            ).rstrip()
            + "\n",
            encoding="utf-8",
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(
            executor,
            package_path,
            reviewer_rebind_draft_path=prior_draft,
        )
        runner.validator = FakeValidator(passed=False)

        result = runner.run()

        self.assertEqual("blocked-validator", result.status)
        self.assertEqual([], executor.requests)
        report = json.loads(
            (self.cycle_dir / "reviewer-rebind.json").read_text(encoding="utf-8")
        )
        self.assertFalse(report["passed"])
        self.assertFalse(report["deterministic_gates_passed"])
        self.assertFalse(report["writer_llm_started"])
        self.assertEqual("blocked-validator", report["status"])

    def test_sharded_writer_uses_fresh_sessions_and_merges_before_reviewer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )

        def shard_step(test_case_ids, session_id):
            def step(_request):
                sections = []
                for test_case_id in test_case_ids:
                    index = int(test_case_id.rsplit("-", 1)[1])
                    obligation_id = "ATOM-001" if index == 1 else f"OBL-{index:03d}"
                    atom_id = f"ATOM-{index:03d}"
                    sections.append(
                        f"""## {test_case_id}

**Название:** Проверка видимого результата {index}
**Тип:** позитивный
**Приоритет:** средний
**package_id:** pkg-exec-001
**Трассировка:** {obligation_id}; {atom_id}; SRC-1

### Предусловия

1. Открыта тестовая форма {index}.

### Тестовые данные

- Значение: `value-{index}`.

### Шаги

1. Выполнить действие {index} со значением `value-{index}`.

### Итоговый ожидаемый результат

Отображается видимый результат {index}.

### Постусловия

- Дополнительная очистка не требуется.
"""
                    )
                payload = {
                    "contract_version": 1,
                    "status": "draft-ready",
                    "draft_markdown": "\n\n".join(sections),
                    "blocking_reasons": [],
                }
                return self.process_result(
                    stdout=self.json_event(
                        json.dumps(payload, ensure_ascii=False),
                        session_id=session_id,
                    )
                )

            return step

        def reviewer_step_for_three(_request):
            payload = {
                "contract_version": 2,
                "decision": "accepted",
                "reviewed_draft_sha256": hashlib.sha256(
                    self.draft_path.read_bytes()
                ).hexdigest(),
                "obligation_reviews": [
                    {
                        "obligation_id": "ATOM-001"
                        if index == 1
                        else f"OBL-{index:03d}",
                        "atom_id": f"ATOM-{index:03d}",
                        "verdict": "covered",
                        "test_case_ids": [f"TC-DEMO-{index:03d}"],
                        "note": f"Observable property {index} is covered.",
                    }
                    for index in range(1, 4)
                ],
                "findings": [],
                "summary": "Merged draft accepted.",
            }
            return self.process_result(
                stdout=self.json_event(
                    json.dumps(payload, ensure_ascii=False),
                    session_id="reviewer-after-merge",
                )
            )

        executor = ScriptedExecutor(
            shard_step(["TC-DEMO-001", "TC-DEMO-002"], "writer-shard-1"),
            shard_step(["TC-DEMO-003"], "writer-shard-2"),
            reviewer_step_for_three,
        )
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 2
        runner.prepared_structured_writer_shard_size = 2

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertEqual(3, len(executor.requests))
        self.assertEqual("writer-r1", executor.requests[0].stage)
        self.assertEqual("writer-r1-shard-002", executor.requests[1].stage)
        self.assertEqual("reviewer-r1", executor.requests[2].stage)
        package_metadata = json.loads(package_path.read_text(encoding="utf-8"))
        for request in executor.requests[:2]:
            self.assertIn(
                f'"package_digest":"{package_metadata["package_digest"]}"',
                request.prompt,
            )
            self.assertIn(
                f'"input_fingerprint":"{package_metadata["input_fingerprint"]}"',
                request.prompt,
            )
            self.assertIn(
                f'"execution_profile":"{package_metadata["execution_profile"]}"',
                request.prompt,
            )
            self.assertIn('"context_profile":"character-restriction-calibration"', request.prompt)
            self.assertIn('"unsupported_dimensions":["negative-oracle"]', request.prompt)
        self.assertIn("TC-DEMO-003", executor.requests[2].prompt)
        self.assertIn(
            "writer-shard-1",
            (self.writer_attempt / "runner-output" / "events.ndjson").read_text(
                encoding="utf-8"
            ),
        )
        self.assertIn(
            "writer-shard-2",
            (
                self.cycle_dir
                / "attempts"
                / "writer-r1-shard-002"
                / "attempt-001"
                / "runner-output"
                / "events.ndjson"
            ).read_text(encoding="utf-8"),
        )
        merged = self.draft_path.read_text(encoding="utf-8")
        self.assertEqual(1, merged.count("# Тест-кейсы"))
        self.assertEqual(3, merged.count("\n## TC-DEMO-"))
        plan = json.loads(
            (self.cycle_dir / "writer-shard-plan.json").read_text(encoding="utf-8")
        )
        self.assertTrue(plan["union_complete"])
        self.assertTrue(plan["disjoint"])
        merge = json.loads(
            (self.writer_attempt / "runner-output" / "shard-merge.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(3, merge["test_case_count"])
        self.assertFalse(self.final_path.exists())

    def test_structured_writer_shards_overlap_with_configured_cap(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=5,
        )
        stage_ids = {
            "writer-r1": ["TC-DEMO-001"],
            "writer-r1-shard-002": ["TC-DEMO-002"],
            "writer-r1-shard-003": ["TC-DEMO-003"],
            "writer-r1-shard-004": ["TC-DEMO-004"],
            "writer-r1-shard-005": ["TC-DEMO-005"],
        }
        barriers = {
            "writer-r1": threading.Barrier(2),
            "writer-r1-shard-002": None,
            "writer-r1-shard-003": threading.Barrier(2),
            "writer-r1-shard-004": None,
        }
        barriers["writer-r1-shard-002"] = barriers["writer-r1"]
        barriers["writer-r1-shard-004"] = barriers["writer-r1-shard-003"]
        reviewer_step = self.prepared_reviewer_step_for_count(5)

        def handler(request):
            if request.role == "reviewer":
                return reviewer_step(request)
            barrier = barriers.get(request.stage)
            if barrier is not None:
                barrier.wait(timeout=3)
            return self.structured_shard_result(
                stage_ids[request.stage],
                session_id=f"session-{request.stage}",
            )

        executor = ConcurrentStageExecutor(handler)
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 1
        runner.prepared_structured_writer_shard_size = 1
        runner.prepared_structured_writer_max_concurrency = 2

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertEqual(2, executor.max_active)
        plan = json.loads(
            (self.cycle_dir / "writer-shard-plan.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, plan["effective_max_concurrency"])
        self.assertEqual(3, plan["wave_count"])

    def test_out_of_order_shard_finish_keeps_plan_order_merge(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        stage_ids = {
            "writer-r1": ["TC-DEMO-001"],
            "writer-r1-shard-002": ["TC-DEMO-002"],
            "writer-r1-shard-003": ["TC-DEMO-003"],
        }
        second_finished = threading.Event()
        reviewer_step = self.prepared_reviewer_step_for_count(3)

        def handler(request):
            if request.role == "reviewer":
                return reviewer_step(request)
            if request.stage == "writer-r1":
                if not second_finished.wait(timeout=3):
                    raise AssertionError("second shard did not overlap primary shard")
                time.sleep(0.03)
            elif request.stage == "writer-r1-shard-002":
                second_finished.set()
            return self.structured_shard_result(
                stage_ids[request.stage],
                session_id=f"session-{request.stage}",
            )

        executor = ConcurrentStageExecutor(handler)
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 1
        runner.prepared_structured_writer_shard_size = 1
        runner.prepared_structured_writer_max_concurrency = 3

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertLess(
            executor.completion_order.index("writer-r1-shard-002"),
            executor.completion_order.index("writer-r1"),
        )
        expected = "# Тест-кейсы\n\n" + "\n\n".join(
            self.complete_test_case_section(index).strip()
            for index in range(1, 4)
        ) + "\n"
        self.assertEqual(expected, self.draft_path.read_text(encoding="utf-8"))
        merge = json.loads(
            (self.writer_attempt / "runner-output" / "shard-merge.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [
                "writer-r1",
                "writer-r1-shard-002",
                "writer-r1-shard-003",
            ],
            [item["stage"] for item in merge["shards"]],
        )

    def test_wave_one_failure_prevents_later_writer_shards(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=4,
        )
        first_wave_barrier = threading.Barrier(2)
        first_wave_ids = {
            "writer-r1": ["TC-DEMO-001"],
            "writer-r1-shard-002": ["TC-DEMO-002"],
        }

        def handler(request):
            if request.stage not in first_wave_ids:
                raise AssertionError(f"later wave was launched: {request.stage}")
            first_wave_barrier.wait(timeout=3)
            return self.structured_shard_result(
                first_wave_ids[request.stage],
                session_id=f"session-{request.stage}",
                exit_code=(7 if request.stage == "writer-r1-shard-002" else 0),
            )

        executor = ConcurrentStageExecutor(handler)
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 1
        runner.prepared_structured_writer_shard_size = 1
        runner.prepared_structured_writer_max_concurrency = 2

        result = runner.run()

        self.assertEqual("blocked-process-exit", result.status)
        self.assertEqual(
            {"writer-r1", "writer-r1-shard-002"},
            {request.stage for request in executor.requests},
        )
        self.assertFalse(
            runner.attempt_root("writer-r1-shard-003").exists()
        )

    def test_unknown_custom_executor_keeps_shards_serial(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        executor = ScriptedExecutor(
            lambda _request: self.structured_shard_result(
                ["TC-DEMO-001"], session_id="serial-writer-1"
            ),
            lambda _request: self.structured_shard_result(
                ["TC-DEMO-002"], session_id="serial-writer-2"
            ),
            lambda _request: self.structured_shard_result(
                ["TC-DEMO-003"], session_id="serial-writer-3"
            ),
            self.prepared_reviewer_step_for_count(3),
        )
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_structured_writer_single_session_tc_limit = 1
        runner.prepared_structured_writer_shard_size = 1
        runner.prepared_structured_writer_max_concurrency = 3

        result = runner.run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertEqual(
            [
                "writer-r1",
                "writer-r1-shard-002",
                "writer-r1-shard-003",
                "reviewer-r1",
            ],
            [request.stage for request in executor.requests],
        )
        plan = json.loads(
            (self.cycle_dir / "writer-shard-plan.json").read_text(encoding="utf-8")
        )
        self.assertFalse(plan["executor_supports_concurrent_execution"])
        self.assertEqual(1, plan["effective_max_concurrency"])

    def test_character_restriction_seed_and_lifecycle_preserve_constraint_gap(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=(
                "negative-oracle",
                "evidence-qualified-ui-calibration",
            ),
            constraint_gap=True,
            calibration_status="ui-calibration-required",
        )
        draft = """# Test cases

## TC-DEMO-001

**Название:** Отклонение цифры в поле Фамилия
**Трассировка:** ATOM-001; SRC-1; GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

Draft body.
"""
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=draft),
            self.reviewer_step(),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        seed = (self.writer_attempt / "runner-input" / "draft-seed.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("candidate-ui-calibration", seed)
        self.assertIn("**Требуется подтверждение:** [SEED:", seed)
        lifecycle = json.loads(
            (self.writer_attempt / "runner-output" / "calibration-lifecycle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("awaiting-ui-calibration", lifecycle["items"][0]["status"])
        self.assertFalse(lifecycle["items"][0]["regression_ready"])

    def test_mixed_atom_explicit_calibration_is_authoritative_per_obligation(self) -> None:
        executable = PreparedObligation(
            obligation_id="OBL-EXEC-001",
            atom_id="ATOM-001",
            source_refs=("SRC-1",),
            atomic_statement="The executable behavior remains source-backed.",
            observable_oracle="The executable visible result is present.",
            test_intent="Verify the executable visible result.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
            constraint_gap_ids=("GAP-001",),
            calibration_status="none",
            planned_test_case_id="TC-DEMO-002",
        )
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=(
                "negative-oracle",
                "evidence-qualified-ui-calibration",
            ),
            constraint_gap=True,
            calibration_status="ui-calibration-required",
            extra_prepared_obligations=(executable,),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()

        seed = runner._draft_seed_text()
        lifecycle = runner._build_calibration_lifecycle()

        candidate_section, executable_section = seed.split(
            "## TC-DEMO-002", 1
        )
        self.assertIn("## TC-DEMO-001", candidate_section)
        self.assertIn("candidate-ui-calibration", candidate_section)
        self.assertIn("**Coverage gap:** GAP-001", candidate_section)
        self.assertNotIn("candidate-ui-calibration", executable_section)
        self.assertNotIn("ui-calibration-required", executable_section)
        self.assertIn("**Coverage gap:** GAP-001", executable_section)
        self.assertEqual(1, lifecycle["open_count"])
        self.assertEqual("ATOM-001", lifecycle["items"][0]["obligation_id"])
        self.assertNotIn(
            "OBL-EXEC-001",
            {item["obligation_id"] for item in lifecycle["items"]},
        )

    def test_constraint_gap_calibration_fallback_is_legacy_only(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            constraint_gap=True,
            calibration_status="none",
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        obligations = load_obligations(
            runner._prepared_artifact("atomic-obligations")
        )
        obligation = obligations.obligations[0]

        self.assertFalse(
            runner._obligation_requires_ui_calibration(
                obligation,
                package_version=runner_module.EXPLICIT_OBLIGATION_CALIBRATION_PACKAGE_VERSION,
            )
        )
        self.assertTrue(
            runner._obligation_requires_ui_calibration(
                obligation,
                package_version=(
                    runner_module.EXPLICIT_OBLIGATION_CALIBRATION_PACKAGE_VERSION - 1
                ),
            )
        )

    def test_source_backed_calibration_without_gap_is_registered(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("evidence-qualified-ui-calibration",),
            calibration_status="ui-calibration-required",
        )
        draft = """# Test cases

## TC-DEMO-001

**Название:** Проверка обязательности выбора
**Трассировка:** ATOM-001; SRC-1
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

Draft body.
"""
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=draft),
            self.reviewer_step(),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        lifecycle = json.loads(
            (self.writer_attempt / "runner-output" / "calibration-lifecycle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(2, lifecycle["version"])
        self.assertEqual(1, lifecycle["open_count"])
        self.assertEqual([], lifecycle["items"][0]["constraint_gap_ids"])
        self.assertEqual("TC-DEMO-001", lifecycle["items"][0]["test_case_id"])
        self.assertEqual(
            "ui-calibration-required",
            lifecycle["items"][0]["calibration_status"],
        )

    def test_runner_materializes_exhaustive_dictionary_values_before_gates(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("table-parity",),
            dictionary_values=("Первое значение", "Второе значение"),
            structured_dictionary_evidence=True,
            dictionary_coverage_mode="all-leaf-values",
        )
        draft = """# Test cases

## TC-DEMO-001

**Название:** Полный состав справочника
**Трассировка:** ATOM-001; SRC-1; DICT-001

### Тестовые данные

- Все значения DICT-001.

### Шаги

1. Открыть список.

### Итоговый ожидаемый результат

Список отображается.
"""
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=draft),
            self.reviewer_step(),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        materialized = self.draft_path.read_text(encoding="utf-8")
        self.assertIn("Первое значение", materialized)
        self.assertIn("Второе значение", materialized)
        projection = json.loads(
            (self.writer_attempt / "runner-output" / "dictionary-projection.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(projection["draft_changed"])
        self.assertEqual(1, projection["materialized_count"])
        self.assertTrue(projection["writer_ownership"]["passed"])
        prompt = (self.writer_attempt / "prompt.md").read_text(encoding="utf-8")
        self.assertIn("runner_owned_dictionary_materializations", prompt)
        self.assertIn('"coverage_mode": "all-leaf-values"', prompt)
        context_budget = json.loads(
            (self.writer_attempt / "runner-output" / "context-budget.json").read_text(
                encoding="utf-8"
            )
        )
        context_projection = context_budget["dictionary_context_projection"]
        self.assertGreater(context_projection["dictionary_sections_compacted"], 0)
        self.assertGreater(context_projection["bytes_removed"], 0)
        obligation_gate = json.loads(
            (self.writer_attempt / "runner-output" / "obligation-gate.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(obligation_gate["passed"])

    def test_runner_blocks_writer_owned_exhaustive_dictionary_values(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("table-parity",),
            dictionary_values=("Первое значение", "Второе значение"),
            structured_dictionary_evidence=True,
            dictionary_coverage_mode="all-leaf-values",
        )
        draft = """# Test cases

## TC-DEMO-001

**Название:** Полный состав справочника
**Трассировка:** ATOM-001; SRC-1; DICT-001

### Тестовые данные

- `Первое значение`; `Второе значение`.

### Шаги

1. Открыть список.

### Итоговый ожидаемый результат

Список отображается.
"""
        executor = ScriptedExecutor(self.structured_writer_step(draft_text=draft))

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-dictionary-projection-ownership", result.status)
        self.assertEqual(1, len(executor.requests))
        projection = json.loads(
            (self.writer_attempt / "runner-output" / "dictionary-projection.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(projection["writer_ownership"]["passed"])
        self.assertEqual(
            "writer-owned-exhaustive-dictionary-values",
            projection["writer_ownership"]["findings"][0]["id"],
        )

    def test_quality_gate_blocks_lost_calibration_markers(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=(
                "negative-oracle",
                "evidence-qualified-ui-calibration",
            ),
            constraint_gap=True,
            calibration_status="ui-calibration-required",
        )
        executor = ScriptedExecutor(
            self.structured_writer_step(
                draft_text=(
                    "# Test cases\n\n## TC-DEMO-001\n\n"
                    "**Название:** Отклонение цифры\n"
                    "**Трассировка:** ATOM-001; SRC-1; GAP-001\n\nDraft body.\n"
                )
            )
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-quality-gate", result.status)
        report = json.loads(
            (self.writer_attempt / "runner-output" / "quality-gate-bundle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(report["passed"])
        self.assertIn("calibration-marker-missing", {item["id"] for item in report["findings"]})

    def test_quality_gate_blocks_alternative_execution_action(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
        )
        draft = """# Test cases

## TC-DEMO-001

**Название:** Скрытие зависимого списка
**Трассировка:** ATOM-001; SRC-1

### Предусловия

1. Открыта тестовая форма.

### Тестовые данные

- Значение `Нет`.

### Шаги

1. Установить или сохранить значение `Нет`.

### Итоговый ожидаемый результат

Зависимый список не отображается.
"""
        executor = ScriptedExecutor(self.structured_writer_step(draft_text=draft))

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-quality-gate", result.status)
        report = json.loads(
            (self.writer_attempt / "runner-output" / "quality-gate-bundle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(
            "ambiguous-execution-action",
            {item["id"] for item in report["findings"]},
        )

    def test_quality_gate_blocks_unqualified_duplicate_dictionary_value(self) -> None:
        duplicate_value = "Повторяющееся значение"
        prepared_values = (
            PreparedDictionaryValue(("DICT-001", "DICT-101"), "group", "Группа один"),
            PreparedDictionaryValue(("DICT-001", "DICT-101"), "leaf", duplicate_value),
            PreparedDictionaryValue(("DICT-001", "DICT-102"), "group", "Группа два"),
            PreparedDictionaryValue(("DICT-001", "DICT-102"), "leaf", duplicate_value),
        )
        reference_obligation = PreparedObligation(
            obligation_id="OBL-002",
            atom_id="ATOM-002",
            source_refs=("SRC-1", "DICT-001"),
            atomic_statement="Можно выбрать значение справочника.",
            observable_oracle="Выбранный checkbox остаётся выбранным.",
            test_intent="Выбрать повторяющееся значение.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=("DICT-001",),
            notes="",
            dictionary_requirements=(
                PreparedDictionaryRequirement("DICT-001", "reference-only"),
            ),
            planned_test_case_id="TC-DEMO-002",
        )
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
            dictionary_values=(duplicate_value,),
            prepared_dictionary_values=prepared_values,
            structured_dictionary_evidence=True,
            dictionary_coverage_mode="full-hierarchy",
            extra_prepared_obligations=(reference_obligation,),
        )
        draft = f"""# Test cases

## TC-DEMO-001

**Название:** Полный состав справочника
**Трассировка:** ATOM-001; SRC-1; DICT-001

### Тестовые данные

- Полный `DICT-001`.

### Шаги

1. Открыть список.

### Итоговый ожидаемый результат

Отображается полный справочник.

## TC-DEMO-002

**Название:** Выбор повторяющегося значения
**Трассировка:** OBL-002; ATOM-002; SRC-1; DICT-001

### Тестовые данные

- `{duplicate_value}`.

### Шаги

1. Выбрать checkbox `{duplicate_value}`.

### Итоговый ожидаемый результат

Выбранный checkbox остаётся выбранным.
"""
        executor = ScriptedExecutor(self.structured_writer_step(draft_text=draft))

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-quality-gate", result.status)
        report = json.loads(
            (self.writer_attempt / "runner-output" / "quality-gate-bundle.json").read_text(
                encoding="utf-8"
            )
        )
        finding = next(
            item
            for item in report["findings"]
            if item["id"] == "ambiguous-dictionary-value-path"
        )
        self.assertEqual("OBL-002", finding["obligation_id"])
        self.assertEqual(2, len(finding["candidate_paths"]))

    def test_execution_oracle_eval_rejects_v3_shapes_before_reviewer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
        )
        fixture = (
            Path(__file__).resolve().parents[1]
            / "evals"
            / "prepared-execution-oracle"
            / "20260713"
            / "v3-bad.md"
        ).read_text(encoding="utf-8")
        executor = ScriptedExecutor(self.structured_writer_step(draft_text=fixture))

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("blocked-quality-gate", result.status)
        self.assertEqual(1, len(executor.requests))
        report = json.loads(
            (self.writer_attempt / "runner-output" / "quality-gate-bundle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {
                "generic-execution-fixture",
                "undefined-execution-action",
                "non-observable-expected-result",
            },
            {item["id"] for item in report["findings"]},
        )

    def test_execution_oracle_eval_accepts_corrected_calibration_fixture(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=(
                "negative-oracle",
                "evidence-qualified-ui-calibration",
            ),
            constraint_gap=True,
        )
        fixture = (
            Path(__file__).resolve().parents[1]
            / "evals"
            / "prepared-execution-oracle"
            / "20260713"
            / "v4-corrected.md"
        ).read_text(encoding="utf-8")
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=fixture),
            self.reviewer_step(),
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("accepted-not-promoted", result.status)
        report = json.loads(
            (self.writer_attempt / "runner-output" / "quality-gate-bundle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(report["passed"])
        self.assertIn("execution-oracle-quality", report["checks"])

    def test_prepared_standard_context_budget_blocks_before_writer_session(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_standard_writer_context_max_bytes = 1

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "blocked-prepared-standard-context-budget",
        ):
            runner.run()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.cycle_dir.joinpath("cycle-state.yaml").exists())

    def test_prepared_standard_reviewer_context_budget_persists_blocked_state(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
        )
        executor = ScriptedExecutor(self.structured_writer_step())
        runner = self.make_prepared_runner(executor, package_path)
        runner.prepared_standard_reviewer_context_max_bytes = 1

        result = runner.run()

        self.assertEqual("blocked-reviewer-preflight", result.status)
        self.assertEqual(1, len(executor.requests))
        state = self.cycle_dir.joinpath("cycle-state.yaml").read_text(encoding="utf-8")
        self.assertIn("stage_status: blocked-input", state)
        self.assertIn("writer_stage_status: completed", state)
        self.assertIn("reviewer_stage_status: blocked-context-budget", state)
        self.assertIn("current_stage: reviewer-r1", state)
        report = json.loads(
            self.cycle_dir.joinpath("reviewer-context-budget.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(report["passed"])
        self.assertEqual("reviewer", report["role"])

    def test_prepared_standard_validate_only_reports_route_without_cycle_artifacts(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition-or-navigation",),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        report = runner.validate_only_report()

        self.assertEqual("validated", report["status"])
        self.assertEqual("prepared-standard", report["route"])
        self.assertEqual(
            "writer.session_prepared_standard_structured",
            report["writer_scenario"],
        )
        self.assertEqual(
            "reviewer.session_prepared_standard_semantic",
            report["reviewer_scenario"],
        )
        package_payload = json.loads(package_path.read_text(encoding="utf-8"))
        self.assertEqual(runner_module.PACKAGE_VERSION, report["package_version"])
        self.assertEqual(package_payload["package_id"], report["package_id"])
        self.assertEqual(package_payload["package_digest"], report["package_digest"])
        self.assertEqual(
            package_payload["package_digest"],
            report["runtime_identity"]["package_digest"],
        )
        self.assertEqual("runner-PACKAGE_VERSION", report["runtime_identity"]["version_source"])
        self.assertTrue(report["writer_context_budget"]["passed"])
        self.assertTrue(report["reviewer_schema_preflight"]["passed"])
        self.assertIn(
            "reviewer-output-schema",
            report["preflight_checks"],
        )
        self.assertFalse(report["cycle_artifacts_created"])
        self.assertFalse(self.cycle_dir.joinpath("cycle-state.yaml").exists())
        self.assertFalse(self.writer_attempt.exists())

    def test_source_first_constraint_gap_validate_only_uses_prepared_classification(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("evidence-qualified-ui-calibration",),
            constraint_gap=True,
            source_first_contract=True,
            source_first_risk="medium",
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)

        report = runner.validate_only_report()

        self.assertEqual("validated", report["status"])
        self.assertEqual("prepared-standard", report["route"])

    def test_prepared_review_schema_binds_verdict_enums_to_obligation_status(self) -> None:
        package_path = self.build_prepared_package(include_gap=True)
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()

        schema = runner._review_contract_schema()
        variants = schema["properties"]["obligation_reviews"]["items"]["anyOf"]

        self.assertEqual(2, len(variants))
        self.assertEqual(
            ["covered", "incorrect", "missing"],
            variants[0]["properties"]["verdict"]["enum"],
        )
        self.assertEqual(
            ["gap-preserved", "invented-coverage"],
            variants[1]["properties"]["verdict"]["enum"],
        )
        self.assertEqual(
            0,
            variants[1]["properties"]["test_case_ids"]["maxItems"],
        )
        self.assertEqual(
            r"^TC-[A-Za-z0-9][A-Za-z0-9_.-]*$",
            variants[0]["properties"]["test_case_ids"]["items"]["pattern"],
        )

    def test_generic_review_schema_restricts_all_testable_verdicts(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("negative-oracle",),
            test_case_count=3,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        runner._uses_generic_bounded_reviewer_schema = lambda: True

        schema = runner._review_contract_schema()
        item = schema["properties"]["obligation_reviews"]["items"]

        self.assertEqual(
            ["covered", "incorrect", "missing"],
            item["properties"]["verdict"]["enum"],
        )
        self.assertNotIn("invented-coverage", item["properties"]["verdict"]["enum"])
        self.assertEqual(
            ["ATOM-001", "OBL-002", "OBL-003"],
            item["properties"]["obligation_id"]["enum"],
        )

    def test_generic_review_schema_groups_mixed_status_verdicts(self) -> None:
        package_path = self.build_prepared_package(include_gap=True)
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        runner._uses_generic_bounded_reviewer_schema = lambda: True

        schema = runner._review_contract_schema()
        variants = schema["properties"]["obligation_reviews"]["items"]["anyOf"]

        self.assertEqual(["ATOM-001"], variants[0]["properties"]["obligation_id"]["enum"])
        self.assertEqual(
            ["covered", "incorrect", "missing"],
            variants[0]["properties"]["verdict"]["enum"],
        )
        self.assertEqual(["OBL-002"], variants[1]["properties"]["obligation_id"]["enum"])
        self.assertEqual(
            ["gap-preserved", "invented-coverage"],
            variants[1]["properties"]["verdict"]["enum"],
        )
        self.assertEqual(0, variants[1]["properties"]["test_case_ids"]["maxItems"])

    def test_standard_reviewer_projection_embeds_dictionary_active_values(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("dictionary",),
            dictionary_values=("Мужчина", "Женщина"),
            structured_dictionary_evidence=True,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()

        projection = json.loads(
            runner._prepared_standard_reviewer_semantic_projection()
        )

        self.assertEqual(
            [
                {
                    "dictionary_id": "DICT-001",
                    "dictionary_name": "Demo dictionary",
                    "source_file": "support/demo.md",
                    "source_location": "demo.gender",
                    "extraction_status": "extracted",
                    "active_values": ["Мужчина", "Женщина"],
                    "archived_values": "none_required",
                }
            ],
            projection["dictionary_evidence"],
        )

    def test_source_first_runtime_projection_is_digest_bound_and_semantically_exact(
        self,
    ) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()

        writer_text = runner._prepared_writer_source_evidence()
        writer_projection = json.loads(writer_text)
        reviewer_projection = json.loads(
            runner._prepared_shared_context_projection()
        )
        semantic_projection = json.loads(
            runner._prepared_standard_reviewer_semantic_projection()
        )
        writer_transport = json.loads(
            runner._prepared_structured_obligation_transport()
        )
        writer_metadata = runner._prepared_standard_metadata()

        self.assertEqual(writer_text, runner._prepared_writer_source_evidence())
        self.assertEqual(
            "prepared-digest-bound-source-evidence-projection-v1",
            writer_projection["contract"],
        )
        self.assertEqual("accepted", writer_projection["accepted_source_contract"]["review_decision"])
        self.assertEqual(
            runner._source_first_contract.manifest.digest,
            writer_projection["accepted_source_contract"]["manifest_digest"],
        )
        self.assertRegex(
            writer_projection["accepted_source_contract"]["review_receipt_sha256"],
            r"^[0-9a-f]{64}$",
        )
        self.assertEqual(["ASSERT-001"], writer_projection["selection"]["assertion_ids"])
        self.assertEqual(["OBL-001"], writer_projection["selection"]["obligation_ids"])
        assertion = writer_projection["assertions"][0]
        self.assertEqual("SRC-1", assertion["source_row_id"])
        self.assertEqual(
            "The requirement is observable.", assertion["canonical_statement"]
        )
        self.assertEqual(["The demo form is open."], assertion["condition_clauses"])
        self.assertEqual(["Verify the visible result."], assertion["action_clauses"])
        self.assertEqual(
            ["The visible result matches the requirement."],
            assertion["oracle_clauses"],
        )
        self.assertEqual(["BSR 1"], assertion["requirement_codes"])
        self.assertEqual("ready", assertion["execution_readiness"])
        self.assertEqual("OBL-001", assertion["obligation_bindings"][0]["obligation_id"])
        self.assertEqual("release", writer_metadata["output_mode"])
        self.assertTrue(writer_metadata["release_status"]["release_eligible"])
        transported = writer_transport["testable_obligations"][0]
        immutable = runner_module.load_obligations(
            runner._prepared_artifact("atomic-obligations")
        ).obligations[0]
        self.assertEqual(immutable.atomic_statement, transported["atomic_statement"])
        self.assertEqual(immutable.test_intent, transported["test_intent"])
        self.assertEqual(immutable.observable_oracle, transported["observable_oracle"])
        self.assertEqual(list(immutable.source_refs), transported["source_refs"])
        self.assertNotIn("Checked against the exact XHTML", writer_text)
        self.assertNotIn("Scope boundaries were checked", writer_text)
        self.assertNotIn("BSR 1. Source", writer_text)
        self.assertEqual(
            "reviewer-dimension-source-bindings-v1",
            reviewer_projection["reviewer_dimension_source_bindings"]["contract"],
        )
        self.assertEqual(
            {"state-transition": ["SRC-1"]},
            reviewer_projection["reviewer_dimension_source_bindings"]["bindings"],
        )
        compiled = semantic_projection["obligations"][0]
        self.assertEqual(immutable.atomic_statement, compiled["atomic_statement"])
        self.assertEqual(immutable.observable_oracle, compiled["observable_oracle"])
        self.assertEqual(immutable.test_intent, compiled["test_intent"])
        self.assertEqual(list(immutable.source_refs), compiled["source_refs"])
        self.assertEqual(
            writer_projection["accepted_source_contract"]["manifest_digest"],
            semantic_projection["source_contract_digest_summary"]["manifest_digest"],
        )

    def test_writer_transport_preserves_non_testable_context_gap_without_fake_tc(
        self,
    ) -> None:
        context_obligation = PreparedObligation(
            obligation_id="OBL-CONTEXT-001",
            atom_id="ATOM-CONTEXT-001",
            source_refs=("SRC-1",),
            atomic_statement="Context evidence is retained without executable behavior.",
            observable_oracle="",
            test_intent="Preserve the context evidence without creating a test case.",
            coverage_status="not-applicable",
            gap_id="",
            dictionary_refs=(),
            notes="Context-only authoritative boundary gap.",
            constraint_gap_ids=("GAP-CONTEXT-001",),
        )
        context_gap = PreparedGap(
            gap_id="GAP-CONTEXT-001",
            source_refs=("SRC-1",),
            problem="The contextual interpretation remains unresolved.",
            handling="Preserve the evidence and do not invent a test case.",
            blocking=False,
        )
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            extra_prepared_obligations=(context_obligation,),
            extra_prepared_gaps=(context_gap,),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()

        transport = json.loads(runner._prepared_structured_obligation_transport())
        self.assertEqual(1, len(transport["testable_obligations"]))
        self.assertEqual(
            ["GAP-CONTEXT-001"],
            [item["gap_id"] for item in transport["coverage_gaps"]],
        )
        self.assertEqual(
            [
                {
                    "obligation_id": "OBL-CONTEXT-001",
                    "atom_id": "ATOM-CONTEXT-001",
                    "coverage_status": "not-applicable",
                    "gap_id": "",
                    "constraint_gap_ids": ["GAP-CONTEXT-001"],
                }
            ],
            transport["coverage_gap_bindings"],
        )
        writer_payload = runner._prepared_writer_payload(structured=True)
        self.assertIn("GAP-CONTEXT-001", writer_payload)
        self.assertIn("OBL-CONTEXT-001", writer_payload)
        seed = runner._draft_seed_text()
        self.assertEqual(1, seed.count("\n## TC-"))
        self.assertNotIn("GAP-CONTEXT-001", seed)

    def test_source_first_external_artifact_freshness_is_rechecked_before_stage(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)
        runner.validate_configuration()
        self.coverage_gaps_path.write_text(
            self.coverage_gaps_path.read_text(encoding="utf-8")
            + "\n<!-- changed after preflight -->\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "stale-coverage-gaps-artifact-sha256",
        ):
            runner.run()

        self.assertEqual([], executor.requests)

    def test_source_first_writer_shard_projects_only_referenced_assertion(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            test_case_count=2,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()

        projection = json.loads(
            runner._prepared_writer_shard_evidence(
                {"obligation_ids": ["OBL-002"]}
            )
        )

        self.assertEqual(["OBL-002"], projection["selection"]["obligation_ids"])
        self.assertEqual(["ASSERT-002"], projection["selection"]["assertion_ids"])
        self.assertEqual(1, len(projection["assertions"]))
        self.assertEqual(
            "Observable property 2 is required.",
            projection["assertions"][0]["canonical_statement"],
        )
        self.assertNotIn("The requirement is observable.", json.dumps(projection))

    def test_source_first_reviewer_projection_uses_actual_draft_trace_ids(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            test_case_count=2,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        runner.draft_path.parent.mkdir(parents=True, exist_ok=True)
        runner.draft_path.write_text(
            "## TC-DEMO-002\n"
            "**Трассировка:** OBL-002; ATOM-002; SRC-1\n",
            encoding="utf-8",
        )

        projection = json.loads(runner._prepared_shared_context_projection())

        self.assertEqual(["OBL-002"], projection["selection"]["obligation_ids"])
        self.assertEqual(["ASSERT-002"], projection["selection"]["assertion_ids"])

    def test_source_first_reviewer_projection_rejects_unknown_draft_trace_id(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        runner.draft_path.parent.mkdir(parents=True, exist_ok=True)
        runner.draft_path.write_text(
            "## TC-DEMO-001\n"
            "**Трассировка:** OBL-001; ATOM-999; SRC-1\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "unknown draft trace IDs: ATOM-999",
        ):
            runner._prepared_shared_context_projection()

    def test_source_first_projection_fails_closed_on_artifact_digest_drift(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        runner._prepared_writer_source_evidence()
        evidence_path = runner._prepared_artifact("source-evidence")
        evidence_path.write_text(
            evidence_path.read_text(encoding="utf-8") + "\npost-validation drift\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "runtime projection artifact digest mismatch",
        ):
            runner._prepared_writer_source_evidence()

    def test_source_first_projection_fails_closed_on_missing_assertion_binding(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            test_case_count=2,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        original = runner._source_first_contract
        incomplete_manifest = replace(
            original.manifest,
            assertions=original.manifest.assertions[:1],
        )
        rebound_receipt = replace(
            original.review_receipt,
            manifest_digest=incomplete_manifest.digest,
        )
        runner._source_first_contract = runner_module.EmbeddedSourceAssertionContract(
            incomplete_manifest,
            rebound_receipt,
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "missing accepted source assertions for: OBL-002",
        ):
            runner._prepared_writer_source_evidence(
                obligation_ids=("OBL-002",)
            )

    def test_source_first_projection_byte_report_stays_under_explicit_budget(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            test_case_count=24,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()

        first = runner._prepared_writer_source_evidence()
        second = runner._prepared_writer_source_evidence()
        report = runner._source_evidence_projection_reports["writer"]
        reviewer_capacity = runner._build_reviewer_context_capacity_plan()

        self.assertEqual(first, second)
        self.assertTrue(report["passed"], report)
        self.assertEqual(24, report["selected_assertion_count"])
        self.assertEqual(
            runner_module.DEFAULT_PREPARED_WRITER_SOURCE_PROJECTION_MAX_BYTES,
            report["limit_bytes"],
        )
        self.assertLess(report["projected_bytes"], 48 * 1024)
        self.assertLess(
            report["projected_bytes"], report["original_source_evidence_bytes"]
        )
        self.assertRegex(report["projection_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            reviewer_capacity["shared_context_bytes"]
            + reviewer_capacity["semantic_projection_bytes"],
            reviewer_capacity["source_and_semantic_projection_bytes"],
        )
        self.assertGreaterEqual(
            reviewer_capacity["estimated_primary_context_bytes"],
            reviewer_capacity["source_and_semantic_projection_bytes"],
        )

    def test_package_context_projection_omits_irrelevant_dadata_notes(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("table-parity",),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        evidence_path = runner._prepared_artifact("source-evidence")
        evidence_path.write_text(
            """# Prepared Source Evidence

## Mandatory package context

# Package Notes: Demo

## Table abbreviations

- O means required.

## External context: DaData in UI

- DaData suggestions are reference-only context.

- OBL-001: property=SRC-1 | required=visible result | planned=TC-DEMO-001 | status=covered
""",
            encoding="utf-8",
        )

        writer_projection = runner._prepared_writer_source_evidence()
        reviewer_projection = runner._prepared_shared_context_projection()

        self.assertNotIn("suggestions are reference-only", writer_projection)
        self.assertNotIn("suggestions are reference-only", reviewer_projection)
        self.assertIn("Table abbreviations", writer_projection)
        self.assertIn("not applicable to selected scope", reviewer_projection)
        for role in ("writer", "reviewer"):
            report = runner._package_context_projection_reports[role]
            self.assertEqual(1, report["sections_compacted"])
            self.assertGreater(report["bytes_removed"], 0)

    def test_package_context_projection_retains_dadata_notes_for_dadata_scope(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("integration",),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        evidence_path = runner._prepared_artifact("source-evidence")
        evidence_path.write_text(
            """# Prepared Source Evidence

## Mandatory package context

# Package Notes: Demo

## External context: DaData in UI

- DaData suggestions are reference-only context.

- OBL-001: property=SRC-1 | required=DaData suggestion is visible | planned=TC-DEMO-001 | status=covered
""",
            encoding="utf-8",
        )

        writer_projection = runner._prepared_writer_source_evidence()
        reviewer_projection = runner._prepared_shared_context_projection()

        self.assertIn("suggestions are reference-only", writer_projection)
        self.assertIn("suggestions are reference-only", reviewer_projection)
        for role in ("writer", "reviewer"):
            report = runner._package_context_projection_reports[role]
            self.assertEqual(0, report["sections_compacted"])
            self.assertEqual("selected-scope-references-dadata", report["reason"])

    def test_standard_reviewer_projection_blocks_missing_dictionary_evidence(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("dictionary",),
            dictionary_values=("Мужчина", "Женщина"),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        evidence_path = runner._prepared_artifact("source-evidence")
        evidence = evidence_path.read_text(encoding="utf-8")
        evidence_path.write_text(evidence.split("## DICT-001", 1)[0], encoding="utf-8")
        obligations = runner_module.load_obligations(
            runner._prepared_artifact("atomic-obligations")
        ).obligations

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "Prepared dictionary evidence is missing or malformed: DICT-001",
        ):
            runner._prepared_dictionary_evidence_projection(obligations)

    def test_standard_reviewer_projection_blocks_punctuation_only_active_values(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("dictionary",),
            dictionary_values=(";",),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        obligations = runner_module.load_obligations(
            runner._prepared_artifact("atomic-obligations")
        ).obligations

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "no valid active values: DICT-001",
        ):
            runner._prepared_dictionary_evidence_projection(obligations)

    def test_standard_reviewer_projection_blocks_empty_structured_active_values(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("dictionary",),
            dictionary_values=("Мужчина", "Женщина"),
            structured_dictionary_evidence=True,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        evidence_path = runner._prepared_artifact("source-evidence")
        evidence_path.write_text(
            evidence_path.read_text(encoding="utf-8").replace(
                '"active_values":["Мужчина","Женщина"]',
                '"active_values":[]',
            ),
            encoding="utf-8",
        )
        obligations = runner_module.load_obligations(
            runner._prepared_artifact("atomic-obligations")
        ).obligations

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "no valid active values: DICT-001",
        ):
            runner._prepared_dictionary_evidence_projection(obligations)

    def test_standard_reviewer_projection_blocks_malformed_active_values(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("dictionary",),
            dictionary_values=("A`;; `B",),
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        obligations = runner_module.load_obligations(
            runner._prepared_artifact("atomic-obligations")
        ).obligations

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "no valid active values: DICT-001",
        ):
            runner._prepared_dictionary_evidence_projection(obligations)

    def test_legacy_prepared_promotion_is_rejected_before_writer(self) -> None:
        package_path = self.build_prepared_package(execution_profile="standard-required", unsupported_dimensions=("state-transition",))
        contract_path = self.build_promotion_contract()
        draft = """# Тест-кейсы: demo

## Metadata
| field | value |
| --- | --- |
| ft_slug | `demo-ft` |
| scope_slug | `demo-scope` |
| section_id | `1` |
| package_id | `WP-01` |
| test_design_dir | `fts/demo-ft/work/test-design/1-demo-scope` |

## Scope Boundaries
Bounded scope.

## Coverage Summary
ATOM-001 and BSR 1 are covered. GAP-001 is preserved.

## Coverage Gaps
GAP-001 remains open.

## Test Cases

## TC-DEMO-001
**package_id:** WP-01
**Приоритет:** High
**Трассировка:** ATOM-001; SRC-1
"""
        executor = ScriptedExecutor(
            self.writer_step(draft_text=draft),
            self.reviewer_step(decision="accepted"),
        )
        runner = self.make_prepared_runner(
            executor, package_path, promotion_contract_path=contract_path
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError, "bounded source-first assertion"
        ):
            runner.run()

        self.assertEqual([], executor.requests)

    def test_empty_source_first_marker_is_rejected_before_writer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract="empty",
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "legacy-embedded-source-contract-requires-rematerialization",
        ):
            runner.run()

        self.assertEqual([], executor.requests)

    def test_empty_current_source_first_marker_is_rejected_as_incomplete_before_writer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract="empty-current",
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "incomplete-embedded-source-contract",
        ):
            runner.run()

        self.assertEqual([], executor.requests)

    def test_forged_source_first_digest_is_rejected_before_writer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract="forged",
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(executor, package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "embedded-manifest-digest-mismatch",
        ):
            runner.run()

        self.assertEqual([], executor.requests)

    def test_legacy_prepared_promotion_cannot_bypass_source_model_with_diagnostic_shape(self) -> None:
        package_path = self.build_prepared_package(execution_profile="standard-required", unsupported_dimensions=("state-transition",))
        contract_path = self.build_promotion_contract()
        executor = ScriptedExecutor(self.writer_step())
        runner = self.make_prepared_runner(
            executor, package_path, promotion_contract_path=contract_path
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError, "legacy packages are review evidence only"
        ):
            runner.run()

        self.assertEqual([], executor.requests)

    def test_source_first_prepared_direct_promotion_is_rejected_before_writer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        contract_path = self.build_promotion_contract(
            required_requirement_ids=("SRC-1",),
            required_gap_ids=(),
        )
        executor = ScriptedExecutor()
        runner = self.make_prepared_runner(
            executor,
            package_path,
            promotion_contract_path=contract_path,
            promote_final=True,
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "Prepared/source-first direct promotion is disabled",
        ):
            runner.run()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.final_path.exists())

    def test_prepared_private_promote_method_cannot_bypass_posthoc_transaction(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        runner = self.make_prepared_runner(ScriptedExecutor(), package_path)
        runner.validate_configuration()
        runner.draft_path.parent.mkdir(parents=True, exist_ok=True)
        runner.draft_path.write_bytes(b"accepted candidate\n")
        draft_sha = hashlib.sha256(runner.draft_path.read_bytes()).hexdigest()

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "Prepared/source-first direct promotion is disabled",
        ):
            runner._promote({}, expected_draft_sha256=draft_sha)

        self.assertFalse(self.final_path.exists())

    def test_source_first_promotion_reaches_ready_state_with_compact_obligation_review(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        contract_path = self.build_promotion_contract(
            required_requirement_ids=("SRC-1",),
            required_gap_ids=(),
        )
        draft = """# Тест-кейсы: demo

## Metadata
| field | value |
| --- | --- |
| ft_slug | `demo-ft` |
| scope_slug | `demo-scope` |
| section_id | `1` |
| package_id | `WP-01` |
| test_design_dir | `fts/demo-ft/work/test-design/1-demo-scope` |

## Scope Boundaries
Bounded scope.

## Coverage Summary
OBL-001, ATOM-001 and SRC-1 are covered.

## Coverage Gaps
No gaps.

## Test Cases

## TC-DEMO-001
**Название:** Проверка видимого результата
**Тип:** позитивный
**package_id:** WP-01
**Приоритет:** High
**Трассировка:** OBL-001; ATOM-001; SRC-1

### Предусловия

Не требуются.

### Тестовые данные

Не требуется.

### Шаги

1. Verify the visible result.

### Итоговый ожидаемый результат

The page displays the exact value `DEMO-RESULT-001`.

### Постусловия

- Не применимо.
"""
        executor = ScriptedExecutor(
            self.writer_step(draft_text=draft),
            self.reviewer_step(decision="accepted"),
        )
        cycle = self.make_prepared_runner(
            executor,
            package_path,
            promotion_contract_path=contract_path,
        )

        result = cycle.run()

        self.assertEqual(
            "accepted-promotion-ready-not-promoted",
            result.status,
            result.blocking_reasons,
        )
        self.assertEqual(2, len(executor.requests))
        self.assertIn("contract_version 4", executor.requests[1].prompt)
        self.assertIn(
            "Do not mark it incorrect solely because the source does not define "
            "a confirmation, continuation or validation trigger",
            executor.requests[1].prompt,
        )
        self.assertIn(
            "reviewer-dimension-source-bindings-v1", executor.requests[1].prompt
        )
        schema = json.loads(cycle.reviewer_schema_path.read_text(encoding="utf-8"))
        dimension_variants = schema["properties"]["dimension_reviews"]["items"][
            "anyOf"
        ]
        self.assertEqual(
            ["state-transition"],
            [item["properties"]["dimension"]["const"] for item in dimension_variants],
        )
        self.assertEqual(
            ["SRC-1"],
            dimension_variants[0]["properties"]["source_refs"]["items"]["enum"],
        )
        findings = cycle.reviewer_findings_path.read_text(encoding="utf-8")
        self.assertIn("SHA-256 source basis", findings)
        self.assertIn("state-transition", findings)
        self.assertIn("## Reviewer Sign-off Self-check", findings)
        self.assertIn("**traceability_gaps_absent:** yes", findings)
        self.assertIn("**source_parity_checked:** not-applicable", findings)
        self.assertTrue(cycle.final_traceability_matrix_path.is_file())
        self.assertTrue(cycle.final_traceability_matrix_xlsx_path.is_file())
        runner_module.validate_traceability_matrix_pair(
            cycle.final_traceability_matrix_path,
            cycle.final_traceability_matrix_xlsx_path,
        )
        matrix_markdown = cycle.final_traceability_matrix_path.read_text(
            encoding="utf-8"
        )
        self.assertIn("| atom_id | req_id | source_path |", matrix_markdown)
        self.assertIn(
            "| ATOM-001 | BSR 1 |", matrix_markdown
        )
        self.assertIn("| TC-DEMO-001 | covered | not_applicable:covered |", matrix_markdown)
        prompt_path = self.handoff_path.parent / "prompt.reviewer-to-ui-prep.md"
        prompt = prompt_path.read_text(encoding="utf-8")
        for heading in (
            "## Цель этапа",
            "## Входные артефакты",
            "## Обязательные действия",
            "## Не делать",
            "## Ожидаемые выходы",
            "## Gate завершения",
        ):
            self.assertIn(heading, prompt)
        self.assertIn("pending-controlled-promotion", prompt)
        self.assertIn("через `latest_artifacts` этого workflow-state", prompt)
        self.assertNotIn("work/review-cycles/", prompt)
        self.assertIn(
            "Выполнить каждый уникальный `TC-*` из canonical test cases",
            prompt,
        )
        self.assertIn("`unclear`/`not-applicable` не исполнять", prompt)
        self.assertNotIn("удаления заполненного блока", prompt)
        normalized_review = json.loads(
            cycle.normalized_review_result_path.read_text(encoding="utf-8")
        )
        self.assertEqual(2, normalized_review["schema_version"])
        self.assertEqual(4, normalized_review["contract_version"])
        self.assertEqual("accepted", normalized_review["decision"])
        self.assertEqual(
            hashlib.sha256(cycle.draft_path.read_bytes()).hexdigest(),
            normalized_review["reviewed_draft_sha256"],
        )
        self.assertEqual(
            ["state-transition"],
            [item["dimension"] for item in normalized_review["dimension_reviews"]],
        )
        self.assertEqual(
            [{"obligation_id": "OBL-001", "verdict": "covered"}],
            normalized_review["obligation_reviews"],
        )

        promotion_seed = json.loads(
            cycle.promotion_basis_seed_path.read_text(encoding="utf-8")
        )
        self.assertEqual(2, promotion_seed["schema_version"])
        self.assertEqual("promotion-basis-seed", promotion_seed["artifact_kind"])
        self.assertEqual("builder-input-required", promotion_seed["status"])
        self.assertEqual("demo-scope", promotion_seed["scope_slug"])
        self.assertEqual(
            normalized_review["reviewed_draft_sha256"],
            promotion_seed["candidate"]["sha256"],
        )
        self.assertEqual(
            hashlib.sha256(cycle.normalized_review_result_path.read_bytes()).hexdigest(),
            promotion_seed["reviewer"]["sha256"],
        )
        self.assertEqual(
            normalized_review["reviewed_source_basis_sha256"],
            promotion_seed["source_basis"]["sha256"],
        )
        self.assertEqual(
            normalized_review["reviewed_obligation_set_sha256"],
            promotion_seed["obligation_set"]["sha256"],
        )
        self.assertEqual(
            "prepared-quality-gate-bundle-v1",
            promotion_seed["gate_reports"][0]["validator"],
        )
        self.assertEqual(
            self.final_path.relative_to(self.repo_root).as_posix(),
            promotion_seed["production_baseline"]["canonical_path"],
        )
        self.assertIsNone(
            promotion_seed["production_baseline"]["canonical_prior_sha256"]
        )
        self.assertIn(
            "workflow-state-signed-off-replacement",
            promotion_seed["missing_builder_inputs"],
        )
        for name, path in (
            ("final_traceability_matrix", cycle.final_traceability_matrix_path),
            (
                "final_traceability_matrix_xlsx",
                cycle.final_traceability_matrix_xlsx_path,
            ),
            ("handoff_prompt", prompt_path),
        ):
            binding = promotion_seed["available_builder_inputs"][name]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), binding["sha256"]
            )
        self.assertNotIn(
            "final-traceability-matrix", promotion_seed["missing_builder_inputs"]
        )
        self.assertNotIn(
            "final-traceability-matrix-xlsx",
            promotion_seed["missing_builder_inputs"],
        )
        self.assertNotIn(
            "reviewer-to-ui-prep-handoff-prompt",
            promotion_seed["missing_builder_inputs"],
        )
        state = cycle.state_path.read_text(encoding="utf-8")
        self.assertIn("normalized_review_result: work/review-cycles/", state)
        self.assertIn("promotion_basis_seed_status: builder-input-required", state)

    def test_source_first_traceability_preserves_not_applicable_manifest_atom(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        cycle = self.make_prepared_runner(ScriptedExecutor(), package_path)
        cycle.validate_configuration()
        self.assertIsNotNone(cycle._source_first_contract)
        source_contract = cycle._source_first_contract
        assert source_contract is not None
        base = source_contract.manifest.assertions[0]
        not_applicable = replace(
            base,
            assertion_id="ASSERT-NA-001",
            canonical_statement="Служебная строка не задает исполнимое поведение.",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=(),
            requirement_code_bindings=(),
            clause_evidence_bindings=(),
            atom_id="ATOM-NA-001",
            obligation_ids=(),
            disposition_rationale=(
                "Строка является контекстным заголовком и не содержит проверяемого правила."
            ),
        )
        source_contract = runner_module.EmbeddedSourceAssertionContract(
            manifest=replace(
                source_contract.manifest,
                assertions=(*source_contract.manifest.assertions, not_applicable),
            ),
            review_receipt=source_contract.review_receipt,
        )
        review = runner_module.ReviewContract(
            decision="accepted",
            contract_version=4,
            obligation_reviews=(
                runner_module.ObligationReview(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    verdict="covered",
                    test_case_ids=("TC-DEMO-001",),
                    note="accepted",
                ),
            ),
        )

        rows = runner_module.build_source_first_traceability_rows(
            source_contract,
            review,
        )

        self.assertEqual("ATOM-NA-001", rows[-1][0])
        self.assertEqual("SRC-1", rows[-1][1])
        self.assertEqual(
            "source-entity:document-global-constraints:SRC-1", rows[-1][4]
        )
        self.assertEqual(
            "not_covered:source-disposition-not-applicable", rows[-1][7]
        )
        self.assertEqual("not-applicable", rows[-1][8])
        self.assertIn("source_disposition:not-applicable", rows[-1][9])
        first = runner_module.render_source_first_traceability_xlsx(rows)
        second = runner_module.render_source_first_traceability_xlsx(rows)
        self.assertEqual(first, second)
        with zipfile.ZipFile(io.BytesIO(first), "r") as workbook:
            core_properties = workbook.read("docProps/core.xml")
        self.assertIn(
            b">2000-01-01T00:00:00Z</dcterms:modified>",
            core_properties,
        )

    def test_source_first_terminal_handoff_can_be_separate_from_source_handoff(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        terminal_handoff = (
            self.ft_root / "work" / "stage-handoffs" / "02-demo-terminal"
        )
        terminal_handoff.mkdir(parents=True)
        (terminal_handoff / "workflow-state.yaml").write_text(
            "ft_slug: demo-ft\n"
            "scope_slug: demo-scope\n"
            "section_id: '1'\n"
            "current_stage: ft-test-case-iteration\n"
            "stage_status: ready-for-review\n"
            "next_skill: ft-test-case-reviewer\n"
            "blocking_reasons: []\n"
            "latest_artifacts:\n"
            "  coverage_gaps: work/stage-handoffs/01-demo/scope-coverage-gaps.md\n",
            encoding="utf-8",
        )
        cycle = self.make_prepared_runner(
            ScriptedExecutor(),
            package_path,
            source_first_terminal_handoff_dir=terminal_handoff,
        )

        cycle.validate_configuration()

        handoff_dir, workflow_path = cycle._source_first_active_handoff()
        self.assertEqual(terminal_handoff.resolve(), handoff_dir)
        self.assertEqual(
            (terminal_handoff / "workflow-state.yaml").resolve(),
            workflow_path,
        )

    def test_blocking_source_gap_produces_reviewed_unsigned_draft_only(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            blocking_gap=True,
        )
        draft = """# Тест-кейсы: demo

## Metadata
| field | value |
| --- | --- |
| ft_slug | `demo-ft` |
| scope_slug | `demo-scope` |
| section_id | `1` |
| package_id | `WP-01` |
| test_design_dir | `fts/demo-ft/work/test-design/1-demo-scope` |

## Scope Boundaries
Bounded scope.

## Coverage Summary
OBL-001, ATOM-001 and SRC-1 are covered. OBL-002 is preserved as GAP-001.

## Coverage Gaps
GAP-001 remains blocking because the exact mapping is unresolved.

## Test Cases

## TC-DEMO-001
**Название:** Проверка видимого результата
**Тип:** позитивный
**package_id:** WP-01
**Приоритет:** High
**Трассировка:** OBL-001; ATOM-001; SRC-1

### Предусловия

Не требуются.

### Тестовые данные

Не требуется.

### Шаги

1. Verify the visible result.

### Итоговый ожидаемый результат

The page displays the exact value `DEMO-RESULT-001`.

### Постусловия

- Не применимо.
"""
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=draft),
            self.reviewer_step(decision="accepted"),
        )
        cycle = self.make_prepared_runner(executor, package_path)

        result = cycle.run()

        self.assertEqual("blocked-source-gaps", result.status)
        self.assertEqual(2, len(executor.requests))
        state = cycle.state_path.read_text(encoding="utf-8")
        self.assertIn("stage_status: blocked-input", state)
        self.assertIn("reviewer_stage_status: accepted", state)
        self.assertIn("accepted_terminal_state: false", state)
        self.assertIn("draft_or_unsigned: true", state)
        self.assertIn("promotion_status: blocked-source-gaps", state)
        self.assertIn("GAP-001", state)
        self.assertTrue(cycle.draft_path.is_file())
        self.assertTrue(cycle.normalized_review_result_path.is_file())
        self.assertFalse(cycle.promotion_basis_seed_path.exists())
        self.assertFalse(cycle.final_traceability_matrix_path.exists())
        self.assertFalse(cycle.final_traceability_matrix_xlsx_path.exists())
        self.assertFalse(
            (self.handoff_path.parent / "prompt.reviewer-to-ui-prep.md").exists()
        )
        self.assertFalse(self.final_path.exists())
        self.assertFalse((self.cycle_dir / "versions" / "signed-off").exists())

    def test_blocking_source_gap_rejects_promotion_before_model_calls(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            blocking_gap=True,
        )
        contract_path = self.build_promotion_contract(
            required_requirement_ids=("SRC-1",),
            required_gap_ids=("GAP-001",),
        )
        executor = ScriptedExecutor()
        cycle = self.make_prepared_runner(
            executor,
            package_path,
            promotion_contract_path=contract_path,
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError, "PROMO-BLOCKING-SOURCE-GAPS"
        ):
            cycle.run()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.final_path.exists())

    def test_execution_dependency_ready_subset_is_reviewed_but_remains_unsigned(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            execution_dependency=True,
        )
        draft = """# Тест-кейсы: demo

## Metadata
| field | value |
| --- | --- |
| ft_slug | `demo-ft` |
| scope_slug | `demo-scope` |
| section_id | `1` |
| package_id | `WP-01` |
| test_design_dir | `fts/demo-ft/work/test-design/1-demo-scope` |

## Scope Boundaries
Bounded ready subset.

## Coverage Summary
OBL-001, ATOM-001 and SRC-1 are covered. OBL-BLOCKED-001 is excluded by GAP-EXECUTION-001.

## Coverage Gaps
GAP-EXECUTION-001 remains blocking until its reproducible fixture is registered.

## Test Cases

## TC-DEMO-001
**Название:** Проверка видимого результата
**Тип:** позитивный
**package_id:** WP-01
**Приоритет:** High
**Трассировка:** OBL-001; ATOM-001; SRC-1

### Предусловия

Не требуются.

### Тестовые данные

Не требуется.

### Шаги

1. Verify the visible result.

### Итоговый ожидаемый результат

The page displays the exact value `DEMO-RESULT-001`.

### Постусловия

- Не применимо.
"""
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=draft),
            self.reviewer_step(decision="accepted"),
        )
        cycle = self.make_prepared_runner(executor, package_path)

        result = cycle.run()

        self.assertEqual("blocked-execution-dependencies", result.status)
        self.assertEqual(2, len(executor.requests))
        state = cycle.state_path.read_text(encoding="utf-8")
        self.assertIn("stage_status: blocked-input", state)
        self.assertIn("reviewer_stage_status: accepted", state)
        self.assertIn("accepted_terminal_state: false", state)
        self.assertIn("draft_or_unsigned: true", state)
        self.assertIn("promotion_status: blocked-execution-dependencies", state)
        self.assertIn("GAP-EXECUTION-001", state)
        self.assertTrue(cycle.normalized_review_result_path.is_file())
        self.assertFalse(cycle.promotion_basis_seed_path.exists())

    def test_execution_dependency_rejects_promotion_before_model_calls(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            execution_dependency=True,
        )
        contract_path = self.build_promotion_contract(
            required_requirement_ids=("SRC-1",),
            required_gap_ids=("GAP-EXECUTION-001",),
        )
        executor = ScriptedExecutor()
        cycle = self.make_prepared_runner(
            executor,
            package_path,
            promotion_contract_path=contract_path,
        )

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "PROMO-BLOCKED-EXECUTION-DEPENDENCIES",
        ):
            cycle.run()

        self.assertEqual([], executor.requests)

    def test_recomputed_package_cannot_omit_reviewed_execution_dependency(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
            execution_dependency=True,
        )
        payload = json.loads(package_path.read_text(encoding="utf-8"))
        payload["release_status"] = PreparedReleaseStatus.release_default().to_dict()
        without_digest = {
            key: value for key, value in payload.items() if key != "package_digest"
        }
        payload["package_digest"] = hashlib.sha256(
            json.dumps(
                without_digest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        package_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        executor = ScriptedExecutor()
        cycle = self.make_prepared_runner(executor, package_path)

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "execution registry does not exactly match",
        ):
            cycle.run()

        self.assertEqual([], executor.requests)

    def test_source_first_runtime_smell_blocks_before_reviewer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        draft = """# Тест-кейсы: demo

## Test Cases

## TC-DEMO-001
**Название:** Проверка видимого результата
**Тип:** позитивный
**Приоритет:** High
**package_id:** WP-01
**Трассировка:** OBL-001; ATOM-001; SRC-1

### Предусловия

1. Log in with runtime credentials.

### Тестовые данные

Не требуется.

### Шаги

1. Verify the visible result.

### Итоговый ожидаемый результат

The visible result matches the requirement.
"""
        executor = ScriptedExecutor(
            self.structured_writer_step(draft_text=draft),
            self.reviewer_step(decision="accepted"),
        )
        cycle = self.make_prepared_runner(executor, package_path)

        result = cycle.run()

        self.assertEqual("blocked-quality-gate", result.status)
        self.assertEqual(1, len(executor.requests))
        bundle = json.loads(cycle.quality_gate_bundle_path.read_text(encoding="utf-8"))
        finding_ids = {item["id"] for item in bundle["findings"]}
        self.assertIn("production-magic-credential-setup", finding_ids)
        self.assertEqual(
            hashlib.sha256(cycle.draft_path.read_bytes()).hexdigest(),
            bundle["draft_sha256"],
        )

    def test_standard_path_blocks_before_writer_when_reviewer_command_budget_cannot_read_inputs(self) -> None:
        executor = ScriptedExecutor()
        cycle = self.make_runner(executor)
        cycle.reviewer_command_budget = 10

        with self.assertRaisesRegex(
            runner_module.RunnerError,
            "Standard reviewer command budget is lower than its explicit input floor",
        ):
            cycle.run()

        self.assertEqual([], executor.requests)
        self.assertFalse(self.cycle_dir.joinpath("cycle-state.yaml").exists())

    def test_reviewer_command_uses_configured_read_only_sandbox_without_output_file(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="changes-required"))
        self.make_runner(executor).run()

        command = executor.requests[1].command
        self.assertEqual("reviewer-read-only", command[command.index("--sandbox-contract") + 1])
        self.assertNotIn("--last-message-contract", command)
        self.assertIn("write no files", executor.requests[1].prompt)
        self.assertNotIn("Prepared Reviewer Runtime Profile", executor.requests[1].prompt)

    def test_writer_stdout_stderr_and_json_events_are_captured(self) -> None:
        writer_stdout = self.json_event("writer trace")
        executor = ScriptedExecutor(
            self.writer_step(stdout=writer_stdout, stderr="writer diagnostic\n"),
            self.reviewer_step(decision="changes-required"),
        )
        self.make_runner(executor).run()

        outputs = self.writer_attempt / "runner-output"
        self.assertEqual(writer_stdout, (outputs / "stdout.txt").read_text(encoding="utf-8"))
        self.assertEqual("writer diagnostic\n", (outputs / "stderr.txt").read_text(encoding="utf-8"))
        self.assertEqual(writer_stdout, (outputs / "events.ndjson").read_text(encoding="utf-8"))
        status = json.loads((outputs / "stage-status.json").read_text(encoding="utf-8"))
        self.assertEqual("codex-test", status["command"][0])
        self.assertTrue(status["last_message"].endswith("stage-output/last-message.txt"))

    def test_reviewer_stdout_is_captured_and_runner_writes_findings(self) -> None:
        findings = "# Review findings\n\n- FINDING-001"
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="changes-required", findings=findings))
        result = self.make_runner(executor).run()

        outputs = self.reviewer_attempt / "runner-output"
        self.assertEqual("changes-required", result.status)
        self.assertTrue((outputs / "stdout.txt").read_text(encoding="utf-8").strip())
        self.assertEqual(findings + "\n", (outputs / "findings.md").read_text(encoding="utf-8"))
        contract = json.loads((outputs / "review-contract.json").read_text(encoding="utf-8"))
        self.assertEqual("changes-required", contract["decision"])
        self.assertEqual(1, contract["contract_version"])
        self.assertEqual(
            hashlib.sha256((findings + "\n").encode("utf-8")).hexdigest(),
            contract["findings_markdown_sha256"],
        )

    def test_writer_draft_stays_in_work_outputs_when_review_requires_changes(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="changes-required"))
        result = self.make_runner(executor, promote_final=True).run()

        self.assertEqual("changes-required", result.status)
        self.assertTrue(self.draft_path.exists())
        self.assertFalse(self.final_path.exists())
        self.assertTrue(self.draft_path.is_relative_to(self.ft_root / "work"))

    def test_final_artifact_is_promoted_only_after_accepted_terminal_state(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="accepted"))
        result = self.make_runner(executor, promote_final=True).run()

        self.assertEqual("signed-off", result.status)
        self.assertTrue(result.final_promoted)
        self.assertEqual(self.draft_path.read_bytes(), self.final_path.read_bytes())
        state = (self.cycle_dir / "cycle-state.yaml").read_text(encoding="utf-8")
        self.assertIn("accepted_terminal_state: true", state)
        self.assertIn("final_promoted: true", state)

    def test_accepted_review_is_not_promoted_without_explicit_promotion_enablement(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="accepted"))
        result = self.make_runner(executor, promote_final=False).run()

        self.assertEqual("accepted-not-promoted", result.status)
        self.assertFalse(result.final_promoted)
        self.assertFalse(self.final_path.exists())

    def test_promotion_dry_run_records_hash_destination_and_performs_no_write(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="accepted"))
        result = self.make_runner(executor, promotion_dry_run=True).run()

        self.assertEqual("accepted-promotion-dry-run", result.status)
        self.assertFalse(result.final_promoted)
        self.assertFalse(self.final_path.exists())
        report = json.loads(
            (self.cycle_dir / "promotion-dry-run.json").read_text(encoding="utf-8")
        )
        self.assertEqual("passed", report["status"])
        self.assertEqual(hashlib.sha256(self.draft_path.read_bytes()).hexdigest(), report["draft_sha256"])
        self.assertTrue(
            report["destination_path"].endswith(f"test-cases/{self.final_path.name}")
        )
        self.assertFalse(report["overwrite_allowed"])
        self.assertFalse(report["write_performed"])

    def test_promotion_dry_run_blocks_existing_destination(self) -> None:
        self.final_path.parent.mkdir(parents=True, exist_ok=True)
        self.final_path.write_text("existing\n", encoding="utf-8")
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="accepted"))
        result = self.make_runner(executor, promotion_dry_run=True).run()

        self.assertEqual("blocked-promotion-dry-run", result.status)
        self.assertEqual("existing\n", self.final_path.read_text(encoding="utf-8"))
        self.assertFalse((self.cycle_dir / "promotion-dry-run.json").exists())

    def test_promotion_dry_run_rejects_overwrite_override(self) -> None:
        runner = self.make_runner(
            ScriptedExecutor(), promotion_dry_run=True, allow_overwrite_final=True
        )
        with self.assertRaisesRegex(runner_module.RunnerError, "never permits overwrite"):
            runner.validate_configuration()

    def test_timeout_without_required_writer_artifact_blocks(self) -> None:
        executor = ScriptedExecutor(
            self.writer_step(create_draft=False, exit_code=None, timed_out=True, stderr="timeout\n")
        )
        result = self.make_runner(executor).run()

        self.assertEqual("blocked-timeout", result.status)
        self.assertEqual(1, len(executor.requests))
        status = json.loads(
            (self.writer_attempt / "runner-output" / "stage-status.json").read_text(encoding="utf-8")
        )
        self.assertTrue(status["timed_out"])
        self.assertIn("required draft is missing", status["reason"])

    def test_timeout_with_valid_writer_artifact_records_completed_with_progress(self) -> None:
        executor = ScriptedExecutor(
            self.writer_step(exit_code=None, timed_out=True),
            self.reviewer_step(decision="changes-required"),
        )
        result = self.make_runner(executor).run()

        self.assertEqual("changes-required", result.status)
        writer_status = json.loads(
            (self.writer_attempt / "runner-output" / "stage-status.json").read_text(encoding="utf-8")
        )
        self.assertEqual("completed-with-progress", writer_status["status"])
        self.assertTrue(writer_status["validator_passed"])

    def test_source_first_timeout_with_valid_draft_fails_closed_before_reviewer(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=("state-transition",),
            source_first_contract=True,
        )
        executor = ScriptedExecutor(
            self.writer_step(exit_code=None, timed_out=True),
        )
        cycle = self.make_prepared_runner(executor, package_path)

        result = cycle.run()

        self.assertEqual("blocked-timeout", result.status)
        self.assertEqual(1, len(executor.requests))
        writer_status = json.loads(
            (self.writer_attempt / "runner-output" / "stage-status.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(writer_status["timed_out"])
        self.assertIn("did not return a complete contract", writer_status["reason"])

    def test_missing_writer_output_blocks_with_actionable_reason(self) -> None:
        executor = ScriptedExecutor(self.writer_step(create_draft=False))
        result = self.make_runner(executor).run()

        self.assertEqual("blocked-missing-output", result.status)
        status = json.loads(
            (self.writer_attempt / "runner-output" / "stage-status.json").read_text(encoding="utf-8")
        )
        self.assertIn("required draft", status["reason"])
        self.assertIn("stage-output/draft.md", " ".join(status["blocking_reasons"]))

    def test_nonzero_writer_exit_blocks_and_references_captured_streams(self) -> None:
        executor = ScriptedExecutor(
            self.writer_step(create_draft=False, exit_code=7, stdout=self.json_event("partial"), stderr="fatal\n")
        )
        result = self.make_runner(executor).run()

        self.assertEqual("blocked-process-exit", result.status)
        status = json.loads(
            (self.writer_attempt / "runner-output" / "stage-status.json").read_text(encoding="utf-8")
        )
        self.assertEqual(7, status["exit_code"])
        self.assertTrue(status["stdout"].endswith("runner-output/stdout.txt"))
        self.assertTrue(status["stderr"].endswith("runner-output/stderr.txt"))

    def test_reviewer_production_mutation_blocks_promotion(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(mutate_production=True))
        result = self.make_runner(executor, promote_final=True).run()

        self.assertEqual("blocked-forbidden-production-change", result.status)
        self.assertFalse(result.final_promoted)
        self.assertFalse(self.final_path.exists())
        self.assertIn("guard.md", " ".join(result.blocking_reasons))

    def test_reviewer_draft_mutation_blocks_promotion(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(mutate_draft=True))
        result = self.make_runner(executor, promote_final=True).run()

        self.assertEqual("blocked-forbidden-input-change", result.status)
        self.assertFalse(result.final_promoted)
        self.assertFalse(self.final_path.exists())
        self.assertIn("draft changed", " ".join(result.blocking_reasons))

    def test_reviewer_missing_final_contract_blocks(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(stdout=""))
        result = self.make_runner(executor, promote_final=True).run()

        self.assertEqual("blocked-missing-output", result.status)
        self.assertFalse(self.final_path.exists())

    def test_reviewer_contract_rejects_unknown_fields(self) -> None:
        with self.assertRaisesRegex(runner_module.RunnerError, "exactly decision"):
            runner_module.parse_review_contract(
                json.dumps(
                    {
                        "decision": "accepted",
                        "findings_markdown": "# Review\n\nNo findings.",
                        "extra": "not allowed",
                    }
                )
            )

    def test_prepared_reviewer_contract_binds_hash_atoms_and_test_cases(self) -> None:
        draft = "# Cases\n\n## TC-PREP-001\n\n**Трассировка:** ATOM-001\n"
        digest = hashlib.sha256(draft.encode("utf-8")).hexdigest()
        obligation = PreparedObligation(
            obligation_id="ATOM-001",
            source_refs=("SRC-1",),
            atomic_statement="Statement",
            observable_oracle="Observable result",
            test_intent="Verify result",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
        )
        payload = {
            "contract_version": 2,
            "decision": "accepted",
            "reviewed_draft_sha256": digest,
            "obligation_reviews": [
                {
                    "obligation_id": "ATOM-001",
                    "atom_id": "ATOM-001",
                    "verdict": "covered",
                    "test_case_ids": ["TC-PREP-001"],
                    "note": "Condition and oracle are covered.",
                }
            ],
            "findings": [],
            "summary": "No blocking findings.",
        }

        review = runner_module.parse_prepared_review_contract(
            json.dumps(payload),
            expected_obligations=(obligation,),
            expected_draft_sha256=digest,
            draft_text=draft,
        )

        self.assertEqual(2, review.contract_version)
        self.assertEqual("accepted", review.decision)
        self.assertEqual("ATOM-001", review.obligation_reviews[0].obligation_id)
        self.assertEqual("ATOM-001", review.obligation_reviews[0].atom_id)

    def test_prepared_reviewer_contract_rejects_hash_mismatch(self) -> None:
        obligation = PreparedObligation(
            obligation_id="ATOM-001",
            source_refs=("SRC-1",),
            atomic_statement="Statement",
            observable_oracle="Observable result",
            test_intent="Verify result",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
        )
        payload = {
            "contract_version": 2,
            "decision": "accepted",
            "reviewed_draft_sha256": "0" * 64,
            "obligation_reviews": [],
            "findings": [],
            "summary": "No findings.",
        }

        with self.assertRaisesRegex(runner_module.RunnerError, "draft hash mismatch"):
            runner_module.parse_prepared_review_contract(
                json.dumps(payload),
                expected_obligations=(obligation,),
                expected_draft_sha256="1" * 64,
                draft_text="## TC-PREP-001\n",
            )

    def test_prepared_reviewer_contract_distinguishes_obligations_sharing_atom(self) -> None:
        draft = "# Cases\n\n## TC-PREP-001\n\n**Трассировка:** OBL-001; ATOM-001\n"
        digest = hashlib.sha256(draft.encode("utf-8")).hexdigest()
        obligations = (
            PreparedObligation(
                obligation_id="OBL-001",
                atom_id="ATOM-001",
                source_refs=("SRC-1",),
                atomic_statement="Visible behavior",
                observable_oracle="Visible result",
                test_intent="Verify result",
                coverage_status="testable",
                gap_id="",
                dictionary_refs=(),
                notes="",
            ),
            PreparedObligation(
                obligation_id="OBL-002",
                atom_id="ATOM-001",
                source_refs=("SRC-1",),
                atomic_statement="Unobservable constraint",
                observable_oracle="",
                test_intent="Preserve gap",
                coverage_status="gap",
                gap_id="GAP-001",
                dictionary_refs=(),
                notes="",
            ),
        )
        payload = {
            "contract_version": 2,
            "decision": "accepted",
            "reviewed_draft_sha256": digest,
            "obligation_reviews": [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "verdict": "covered",
                    "test_case_ids": ["TC-PREP-001"],
                    "note": "Visible obligation covered.",
                },
                {
                    "obligation_id": "OBL-002",
                    "atom_id": "ATOM-001",
                    "verdict": "gap-preserved",
                    "test_case_ids": [],
                    "note": "Constraint remains non-executable.",
                },
            ],
            "findings": [],
            "summary": "All obligations accounted for.",
        }

        review = runner_module.parse_prepared_review_contract(
            json.dumps(payload),
            expected_obligations=obligations,
            expected_draft_sha256=digest,
            draft_text=draft,
        )

        self.assertEqual(["OBL-001", "OBL-002"], [
            item.obligation_id for item in review.obligation_reviews
        ])

    def test_validator_failure_blocks_before_reviewer(self) -> None:
        executor = ScriptedExecutor(self.writer_step())
        validator = FakeValidator(passed=False)
        result = self.make_runner(executor, validator=validator, promote_final=True).run()

        self.assertEqual("blocked-validator", result.status)
        self.assertEqual(1, len(executor.requests))
        self.assertFalse(self.final_path.exists())
        report = json.loads(
            (self.writer_attempt / "runner-output" / "validator.json").read_text(encoding="utf-8")
        )
        self.assertFalse(report["passed"])

    def test_default_validator_reuses_existing_deterministic_structure_gate(self) -> None:
        self.draft_path.parent.mkdir(parents=True, exist_ok=True)
        self.draft_path.write_text(
            "\n".join(
                [
                    "# Test cases",
                    "",
                    "## TC-DEMO-001 Create document",
                    "",
                    "**Title:** Create document",
                    "**Type:** positive",
                    "**Priority:** high",
                    "**package_id:** WP-01",
                    "**Traceability:** REQ-001",
                    "",
                    "### Preconditions",
                    "- User is authorized.",
                    "",
                    "### Test Data",
                    "- Valid document.",
                    "",
                    "### Steps",
                    "1. Create the document.",
                    "",
                    "### Expected Result",
                    "Document is created.",
                    "",
                    "### Postconditions",
                    "- Document can be removed.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        validation = runner_module.ProjectDraftStructureValidator().validate(
            draft_path=self.draft_path,
            final_path=self.final_path,
            ft_root=self.ft_root,
            state_path=self.cycle_dir / "cycle-state.yaml",
        )

        self.assertTrue(validation.passed)
        self.assertEqual((), validation.findings)
        self.assertIn("evaluate_test_case_markdown_structure", validation.validator)

    def test_default_validator_rejects_unresolved_fixture_bindings(self) -> None:
        self.draft_path.parent.mkdir(parents=True, exist_ok=True)
        self.draft_path.write_text(
            """# Test cases

## Fixture Binding Catalog

| fixture_id | binding_field | status |
| --- | --- | --- |
| FIX-001 | screen_route | requires-binding |

## TC-DEMO-001 Create document

**Title:** Create document
**Type:** positive
**Priority:** high
**package_id:** WP-01
**Traceability:** REQ-001

### Preconditions
- Open the bound route.

### Test Data
- Bound fixture.

### Steps
1. Create the document.

### Expected Result
Document is created.

### Postconditions
- Document can be removed.
""",
            encoding="utf-8",
        )

        validation = runner_module.ProjectDraftStructureValidator().validate(
            draft_path=self.draft_path,
            final_path=self.final_path,
            ft_root=self.ft_root,
            state_path=self.cycle_dir / "cycle-state.yaml",
        )

        self.assertFalse(validation.passed)
        self.assertIn(
            "unresolved-execution-binding",
            {item["id"] for item in validation.findings},
        )

    def test_default_validator_rejects_self_blocked_writer_gate(self) -> None:
        findings = runner_module.ProjectDraftStructureValidator._execution_readiness_findings(
            "Итог Writer Quality Gate: `blocked`.\nExecution-ready test cases: `0/6`.\n"
        )

        self.assertEqual(
            {"writer-quality-gate-self-blocked", "no-execution-ready-test-cases"},
            {item["id"] for item in findings},
        )

    def test_default_validator_rejects_unresolved_angle_bracket_test_data(self) -> None:
        findings = runner_module.ProjectDraftStructureValidator._execution_readiness_findings(
            "### Тестовые данные\n\n- Идентификатор заявки: `<ID заявки>`.\n"
        )

        self.assertEqual(
            {"unresolved-test-data-placeholder"},
            {item["id"] for item in findings},
        )

    def test_default_validator_allows_named_reproducible_fixture(self) -> None:
        findings = runner_module.ProjectDraftStructureValidator._execution_readiness_findings(
            "### Тестовые данные\n\n- Fixture: `CALC-SUMMARY-01`, подготовленная по описанным условиям.\n"
        )

        self.assertEqual((), findings)

    def test_existing_final_is_not_overwritten_by_default(self) -> None:
        self.final_path.write_text("existing final\n", encoding="utf-8")
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="accepted"))
        result = self.make_runner(executor, promote_final=True).run()

        self.assertEqual("blocked-promotion", result.status)
        self.assertEqual("existing final\n", self.final_path.read_text(encoding="utf-8"))

    def test_unverified_cli_contract_is_rejected_before_process_execution(self) -> None:
        executor = ScriptedExecutor()
        with self.assertRaisesRegex(runner_module.RunnerError, "CLI contract is unverified"):
            self.make_runner(executor, verified=False).run()
        self.assertEqual([], executor.requests)

    def test_stale_runner_artifact_is_rejected_before_process_execution(self) -> None:
        self.draft_path.parent.mkdir(parents=True, exist_ok=True)
        self.draft_path.write_text("stale draft from an earlier attempt\n", encoding="utf-8")
        executor = ScriptedExecutor()

        with self.assertRaisesRegex(runner_module.RunnerError, "runner-owned artifacts"):
            self.make_runner(executor).run()

        self.assertEqual([], executor.requests)
        self.assertEqual(
            "stale draft from an earlier attempt\n",
            self.draft_path.read_text(encoding="utf-8"),
        )

    def test_each_stage_persists_v2_manifest_and_result_under_its_attempt(self) -> None:
        executor = ScriptedExecutor(
            self.writer_step(),
            self.reviewer_step(decision="changes-required"),
        )

        self.make_runner(executor).run()

        writer_manifest = json.loads(
            (self.writer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        writer_result = json.loads(
            (self.writer_attempt / "stage-result.json").read_text(encoding="utf-8")
        )
        reviewer_manifest = json.loads(
            (self.reviewer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        reviewer_result = json.loads(
            (self.reviewer_attempt / "stage-result.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, writer_manifest["contract_version"])
        self.assertEqual("workspace_write", writer_manifest["sandbox_policy"])
        self.assertEqual("draft-ready", writer_result["outcome"])
        self.assertEqual("writer-session", writer_result["backend_session_id"])
        self.assertEqual([], reviewer_manifest["allowed_write_roots"])
        self.assertTrue(
            any(item["path"].endswith("stage-output/draft.md") for item in reviewer_manifest["handoff_artifacts"])
        )
        self.assertEqual("changes-required", reviewer_result["outcome"])
        self.assertEqual("reviewer-session", reviewer_result["backend_session_id"])

    def test_success_without_backend_session_id_is_blocked_by_v2_contract(self) -> None:
        stdout_without_thread = json.dumps(
            {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}}
        ) + "\n"
        executor = ScriptedExecutor(self.writer_step(stdout=stdout_without_thread))

        result = self.make_runner(executor).run()

        self.assertEqual("blocked-contract", result.status)
        contract = json.loads(
            (self.writer_attempt / "stage-result.json").read_text(encoding="utf-8")
        )
        self.assertEqual("blocked", contract["outcome"])
        self.assertEqual("", contract["backend_session_id"])

    def test_reviewer_backend_session_must_differ_from_writer(self) -> None:
        same_session_review = self.json_event(
            json.dumps(
                {"decision": "accepted", "findings_markdown": "# Review\n\nNo findings."}
            ),
            session_id="writer-session",
        )
        executor = ScriptedExecutor(
            self.writer_step(),
            self.reviewer_step(stdout=same_session_review),
        )

        result = self.make_runner(executor).run()

        self.assertEqual("blocked-contract", result.status)
        self.assertFalse(self.final_path.exists())
        contract = json.loads(
            (self.reviewer_attempt / "stage-result.json").read_text(encoding="utf-8")
        )
        self.assertEqual("blocked", contract["outcome"])
        self.assertEqual("", contract["backend_session_id"])

    def test_exec_stages_write_latency_handoff_and_token_metrics(self) -> None:
        writer_stdout = self.json_event("writer complete", session_id="writer-metrics")
        writer_stdout += json.dumps(
            {
                "type": "turn.completed",
                "usage": {"input_tokens": 11, "output_tokens": 5, "total_tokens": 16},
            }
        ) + "\n"
        executor = ScriptedExecutor(
            self.writer_step(stdout=writer_stdout),
            self.reviewer_step(decision="changes-required"),
        )

        self.make_runner(executor).run()

        writer_metrics = json.loads(
            (self.writer_attempt / "metrics.json").read_text(encoding="utf-8")
        )
        ledger = (self.cycle_dir / "stage-metrics.ndjson").read_text(encoding="utf-8").splitlines()
        self.assertEqual("codex-exec", writer_metrics["backend"])
        self.assertEqual(16, writer_metrics["total_tokens"])
        self.assertGreater(writer_metrics["input_artifact_bytes"], 0)
        self.assertGreater(writer_metrics["output_artifact_bytes"], 0)
        self.assertEqual(2, len(ledger))


if __name__ == "__main__":
    unittest.main()
