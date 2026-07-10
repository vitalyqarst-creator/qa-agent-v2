from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

from test_case_agent.review_cycle.prepared_package import (
    EvidenceInput,
    PreparedObligation,
    PreparedObligationSet,
    PreparedPackageBuilder,
    StageInstructionConfig,
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


class StreamingSubprocessExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def request(
        self,
        code: str,
        *,
        timeout_seconds: int = 5,
        idle_timeout_seconds: int = 2,
        command_budget: int = 5,
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
        )

    def test_streams_jsonl_and_counts_started_commands(self) -> None:
        code = (
            "import json,sys; "
            "print(json.dumps({'type':'item.started','item':{'type':'command_execution'}}),flush=True); "
            "sys.stderr.write('diagnostic\\n'); sys.stderr.flush()"
        )
        result = runner_module.SubprocessExecutor().execute(self.request(code))

        self.assertEqual(0, result.exit_code)
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
        self.handoff_path = self.ft_root / "work" / "stage-handoffs" / "01-demo" / "scope-contract.md"
        self.instruction_path = self.repo_root / "AGENTS.md"
        self.source_path.parent.mkdir(parents=True)
        self.handoff_path.parent.mkdir(parents=True)
        self.final_path.parent.mkdir(parents=True)
        self.source_path.write_text("<html><body>Source</body></html>\n", encoding="utf-8")
        self.handoff_path.write_text("# Scope contract\n", encoding="utf-8")
        self.instruction_path.write_text("# Test instructions\n", encoding="utf-8")
        self.validator = FakeValidator()

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
    ):
        return runner_module.ProcessResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            launch_error=launch_error,
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
        exit_code: int | None = 0,
        stdout: str | None = None,
        stderr: str = "",
        timed_out: bool = False,
    ):
        def step(_request):
            if create_draft:
                self.draft_path.parent.mkdir(parents=True, exist_ok=True)
                self.draft_path.write_text(
                    "# Test cases\n\n## TC-DEMO-001\n\n**Трассировка:** ATOM-001\n\nDraft body.\n",
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
    ):
        def step(_request):
            if mutate_production:
                guard_path = self.ft_root / "test-cases" / "guard.md"
                guard_path.write_text("reviewer mutation\n", encoding="utf-8")
            if mutate_draft:
                self.draft_path.write_text("reviewer changed the validated draft\n", encoding="utf-8")
            contract = json.dumps(
                {"decision": decision, "findings_markdown": findings},
                ensure_ascii=False,
            )
            return self.process_result(
                exit_code=exit_code,
                stdout=(
                    stdout
                    if stdout is not None
                    else self.json_event(contract, session_id="reviewer-session")
                ),
                stderr=stderr,
                timed_out=timed_out,
            )

        return step

    def make_runner(
        self,
        executor,
        *,
        validator=None,
        promote_final: bool = False,
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
            allow_overwrite_final=allow_overwrite_final,
        )

    def build_prepared_package(self) -> Path:
        self.handoff_path.write_text("# Scope contract\n\nSRC-1: observable requirement.\n", encoding="utf-8")
        obligations = PreparedObligationSet.create(
            package_id="pkg-exec-001",
            obligations=(
                PreparedObligation(
                    obligation_id="ATOM-001",
                    source_refs=("SRC-1",),
                    atomic_statement="The requirement is observable.",
                    observable_oracle="The visible result matches the requirement.",
                    test_intent="Verify the visible result.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                ),
            ),
            coverage_gaps=(),
        )
        package_root = self.cycle_dir / "prepared-input" / "pkg-exec-001"
        PreparedPackageBuilder(self.repo_root).build(
            output_root=package_root,
            package_id="pkg-exec-001",
            ft_slug="demo-ft",
            scope_slug="demo-scope",
            section_id="1",
            source_registry=((self.source_path, "machine-readable", "SRC-1"),),
            evidence_inputs=(EvidenceInput(self.handoff_path, "Confirmed scope"),),
            obligations=obligations,
            instructions=StageInstructionConfig(
                role="writer",
                scenario="writer.session_prepared_initial_draft",
                output_path=self.draft_path.relative_to(self.repo_root).as_posix(),
                attempt_root=self.writer_attempt.relative_to(self.repo_root).as_posix(),
                sandbox_policy="workspace_write",
                timeout_seconds=180,
                idle_timeout_seconds=60,
                command_budget=12,
            ),
            forbidden_evidence_roots=("fts/demo-ft/test-cases",),
        )
        return package_root / "stage-package.json"

    def make_prepared_runner(self, executor, package_path: Path):
        return runner_module.CodexExecReviewCycleRunner(
            repo_root=self.repo_root,
            ft_root=self.ft_root,
            cycle_dir=self.cycle_dir,
            final_path=self.final_path,
            source_files=[],
            handoff_files=[],
            prepared_package_path=package_path,
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
        )

    def test_prepared_fast_path_uses_only_compact_package_artifacts(self) -> None:
        package_path = self.build_prepared_package()
        executor = ScriptedExecutor(
            self.writer_step(), self.reviewer_step(decision="changes-required")
        )

        result = self.make_prepared_runner(executor, package_path).run()

        self.assertEqual("changes-required", result.status)
        writer_prompt = executor.requests[0].prompt
        self.assertIn("prepared writer fast path", writer_prompt)
        self.assertIn("stage-package.json", writer_prompt)
        self.assertIn("source-evidence.md", writer_prompt)
        self.assertIn("atomic-obligations.json", writer_prompt)
        self.assertIn("stage-instructions.md", writer_prompt)
        self.assertNotIn("source/main.xhtml", writer_prompt)
        manifest = json.loads((self.writer_attempt / "stage-input.json").read_text(encoding="utf-8"))
        self.assertEqual("writer.session_prepared_initial_draft", manifest["scenario"])
        self.assertEqual(1, len(manifest["source_artifacts"]))
        self.assertTrue(manifest["source_artifacts"][0]["path"].endswith("source-evidence.md"))
        self.assertFalse(any(item["path"].endswith("main.xhtml") for item in manifest["source_artifacts"]))
        gate = json.loads((self.writer_attempt / "runner-output" / "obligation-gate.json").read_text(encoding="utf-8"))
        self.assertTrue(gate["passed"])
        reviewer_command = executor.requests[1].command
        self.assertIn("--output-schema-contract", reviewer_command)
        schema_path = Path(
            reviewer_command[reviewer_command.index("--output-schema-contract") + 1]
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        reviewer_manifest = json.loads(
            (self.reviewer_attempt / "stage-input.json").read_text(encoding="utf-8")
        )
        self.assertEqual("reviewer.session_prepared_semantic", reviewer_manifest["scenario"])

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

    def test_prepared_fast_path_rejects_tampered_package_before_exec(self) -> None:
        package_path = self.build_prepared_package()
        (package_path.parent / "source-evidence.md").write_text("tampered\n", encoding="utf-8")
        executor = ScriptedExecutor()

        with self.assertRaisesRegex(runner_module.RunnerError, "Prepared stage package is invalid"):
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

    def test_reviewer_command_uses_configured_read_only_sandbox_without_output_file(self) -> None:
        executor = ScriptedExecutor(self.writer_step(), self.reviewer_step(decision="changes-required"))
        self.make_runner(executor).run()

        command = executor.requests[1].command
        self.assertEqual("reviewer-read-only", command[command.index("--sandbox-contract") + 1])
        self.assertNotIn("--last-message-contract", command)
        self.assertIn("write no files", executor.requests[1].prompt)

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
