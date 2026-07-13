from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

from test_case_agent.review_cycle.prepared_package import (
    EvidenceInput,
    PreparedDictionaryRequirement,
    PreparedDictionaryValue,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
    PreparedPackageBuilder,
    PreparedStateChange,
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
        idle_timeout_seconds: int | None = 2,
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
                first_artifact_deadline_seconds=2,
            )
        )

        self.assertEqual(0, result.exit_code)
        self.assertIsNotNone(result.first_artifact_seconds)
        self.assertLess(result.first_artifact_seconds, 2)


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
        self.final_path.parent.mkdir(parents=True)
        self.source_path.write_text("<html><body>Source</body></html>\n", encoding="utf-8")
        self.docx_path.write_bytes(b"docx-source")
        self.handoff_path.write_text("# Scope contract\n", encoding="utf-8")
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

1. Открыта тестовая форма {index}.

### Тестовые данные

- Значение: `value-{index}`.

### Шаги

1. Ввести `value-{index}` в поле {index}.

### Итоговый ожидаемый результат

{expected or f'Поле {index} визуально содержит `value-{index}`.'}

### Постусловия

- Дополнительная очистка не требуется.
"""

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
        constraint_gap: bool = False,
        grouped_obligations: bool = False,
        out_of_order_planned_ids: bool = False,
        test_case_count: int = 1,
        first_observable_oracle: str = "The visible result matches the requirement.",
        first_execution_semantics: str = "direct",
        first_state_change: PreparedStateChange | None = None,
        dictionary_values: tuple[str, ...] = (),
        structured_dictionary_evidence: bool = False,
        dictionary_coverage_mode: str = "reference-only",
        calibration_status: str = "none",
    ) -> Path:
        gap_evidence = (
            "\nGAP-001: exact mapping is unresolved.\n"
            if include_gap or constraint_gap
            else ""
        )
        dictionary_evidence = ""
        if dictionary_values:
            rendered_values = "; ".join(f"`{value}`" for value in dictionary_values)
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
                            "active_values": list(dictionary_values),
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
        self.handoff_path.write_text(
            "# Scope contract\n\nSRC-1: observable requirement.\n"
            + gap_evidence
            + dictionary_evidence,
            encoding="utf-8",
        )
        prepared_obligations = [
            PreparedObligation(
                obligation_id="ATOM-001",
                source_refs=("SRC-1",),
                atomic_statement="The requirement is observable.",
                observable_oracle=first_observable_oracle,
                test_intent="Verify the visible result.",
                coverage_status="testable",
                gap_id="",
                dictionary_refs=("DICT-001",) if dictionary_values else (),
                notes="",
                constraint_gap_ids=(("GAP-001",) if constraint_gap else ()),
                execution_semantics=first_execution_semantics,
                state_change=first_state_change,
                dictionary_requirements=(
                    (
                        PreparedDictionaryRequirement(
                            dictionary_id="DICT-001",
                            coverage_mode=dictionary_coverage_mode,
                            required_values=(
                                tuple(
                                    PreparedDictionaryValue(
                                        ("DICT-001",),
                                        "leaf",
                                        value,
                                    )
                                    for value in dictionary_values
                                )
                                if dictionary_coverage_mode != "reference-only"
                                else ()
                            ),
                        ),
                    )
                    if dictionary_values
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
                    or calibration_status != "none"
                    or dictionary_coverage_mode != "reference-only"
                    else ""
                ),
            )
        ]
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
        if include_gap:
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
                    blocking=False,
                )
            )
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
            promotion_contract_path=promotion_contract_path,
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

    def build_promotion_contract(self) -> Path:
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
                    "required_requirement_ids": ["BSR 1"],
                    "required_sections": [
                        "Metadata", "Scope Boundaries", "Coverage Summary", "Coverage Gaps", "Test Cases"
                    ],
                    "required_gap_ids": ["GAP-001"],
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
                            "id": "non-observable-expected-result",
                            "severity": "error",
                            "test_case_ids": ["TC-DEMO-001", "TC-DEMO-003"],
                        }
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

    def test_character_restriction_seed_and_lifecycle_preserve_constraint_gap(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=(
                "negative-oracle",
                "evidence-qualified-ui-calibration",
            ),
            constraint_gap=True,
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
        lifecycle = json.loads(
            (self.writer_attempt / "runner-output" / "calibration-lifecycle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("awaiting-ui-calibration", lifecycle["items"][0]["status"])
        self.assertFalse(lifecycle["items"][0]["regression_ready"])

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
        obligation_gate = json.loads(
            (self.writer_attempt / "runner-output" / "obligation-gate.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(obligation_gate["passed"])

    def test_quality_gate_blocks_lost_calibration_markers(self) -> None:
        package_path = self.build_prepared_package(
            execution_profile="standard-required",
            unsupported_dimensions=(
                "negative-oracle",
                "evidence-qualified-ui-calibration",
            ),
            constraint_gap=True,
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
        self.assertFalse(report["cycle_artifacts_created"])
        self.assertFalse(self.cycle_dir.joinpath("cycle-state.yaml").exists())
        self.assertFalse(self.writer_attempt.exists())

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

    def test_prepared_promotion_contract_produces_promotion_ready_terminal_state(self) -> None:
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

        result = runner.run()

        self.assertEqual("accepted-promotion-ready-not-promoted", result.status)
        self.assertTrue(runner.promotion_readiness_path.is_file())
        writer_prompt = executor.requests[0].prompt
        self.assertIn("Promotion canonicalization contract", writer_prompt)
        self.assertIn("TC-DEMO-001", writer_prompt)

    def test_prepared_promotion_contract_blocks_diagnostic_shape_before_reviewer(self) -> None:
        package_path = self.build_prepared_package(execution_profile="standard-required", unsupported_dimensions=("state-transition",))
        contract_path = self.build_promotion_contract()
        executor = ScriptedExecutor(self.writer_step())
        runner = self.make_prepared_runner(
            executor, package_path, promotion_contract_path=contract_path
        )

        result = runner.run()

        self.assertEqual("blocked-promotion-readiness", result.status)
        self.assertEqual(1, len(executor.requests))

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
