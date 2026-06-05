from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNNER = ROOT_DIR / "scripts" / "codex_review_cycle_runner.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("codex_review_cycle_runner_under_test", RUNNER)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CodexReviewCycleRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ft_root = self.root / "fts" / "demo-ft"
        self.cycle_dir = self.ft_root / "work" / "review-cycles" / "section-scope"
        self.prompt_dir = self.cycle_dir / "prompts"
        self.test_design_dir = self.ft_root / "work" / "test-design" / "section-scope"
        self.test_case = self.ft_root / "test-cases" / "1-section-scope.md"
        self.state_path = self.cycle_dir / "cycle-state.yaml"

        self.prompt_dir.mkdir(parents=True)
        self.test_design_dir.mkdir(parents=True)
        self.test_case.parent.mkdir(parents=True)
        self.test_case.write_text("# Test cases\n\n## TC-001\n", encoding="utf-8")
        (self.prompt_dir / "next.md").write_text("Run next session", encoding="utf-8")
        (self.test_design_dir / "traceability.md").write_text("| atom | tc |\n", encoding="utf-8")
        (self.cycle_dir / "codex-session-map.yaml").write_text("sessions: []\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_state(
        self,
        *,
        status: str = "writer-draft-ready",
        semantic_round: int = 0,
        prompt: str = "work/review-cycles/section-scope/prompts/next.md",
    ) -> None:
        self.state_path.write_text(
            "\n".join(
                [
                    "cycle_id: cycle-demo",
                    "ft_slug: demo-ft",
                    "scope_slug: section-scope",
                    "canonical_test_cases: test-cases/1-section-scope.md",
                    "test_design_dir: work/test-design/section-scope",
                    "current_stage: writer-r1",
                    f"stage_status: {status}",
                    f"semantic_round: {semantic_round}",
                    "max_semantic_rounds: 2",
                    f"active_transition_prompt: {prompt}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def run_runner(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RUNNER), *args],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_validate_reports_next_structure_preflight_session(self) -> None:
        self.write_state()

        result = self.run_runner("validate", "--state", str(self.state_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual("reviewer.structure_preflight", payload["next"]["scenario"])
        self.assertEqual("structure-preflight-r1", payload["next"]["stage"])
        self.assertEqual("workspace_write", payload["next"]["sandbox_policy"])
        self.assertEqual(
            "reviewer.structure_preflight",
            payload["next"]["instruction_context"]["scenario"],
        )
        context_paths = {
            item["path"] for item in payload["next"]["instruction_context"]["files"]
        }
        self.assertIn("skills/ft-test-case-reviewer/SKILL.md", context_paths)
        self.assertIn("references/agent/session-based-review-cycle-format.md", context_paths)

    def test_start_dry_run_selects_semantic_revision_writer(self) -> None:
        self.write_state(status="semantic-revision-needed", semantic_round=1)

        result = self.run_runner("start", "--state", str(self.state_path), "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("start-session", payload["action"])
        self.assertEqual("writer", payload["role"])
        self.assertEqual("writer-r2", payload["stage"])
        self.assertEqual("writer.session_semantic_revision", payload["scenario"])
        self.assertEqual("workspace_write", payload["sandbox_policy"])
        self.assertEqual(
            "writer.session_semantic_revision",
            payload["instruction_context"]["scenario"],
        )

    def test_validate_accepts_unindented_top_level_list_items(self) -> None:
        self.write_state(status="semantic-revision-needed", semantic_round=1)
        self.state_path.write_text(
            self.state_path.read_text(encoding="utf-8")
            + "\n".join(
                [
                    "latest_artifacts:",
                    "- test-cases/1-section-scope.md",
                    "blocking_reasons:",
                    "- 'FINDING-001: generic expected result'",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_runner("validate", "--state", str(self.state_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual("writer-r2", payload["next"]["stage"])

    def test_start_dry_run_selects_scope_gap_review_before_writer(self) -> None:
        self.test_case.unlink()
        self.write_state(status="scope-ready-for-gap-review", semantic_round=0)

        result = self.run_runner("start", "--state", str(self.state_path), "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("reviewer", payload["role"])
        self.assertEqual("scope-gap-review", payload["stage"])
        self.assertEqual("reviewer.scope_gap_review", payload["scenario"])

    def test_start_dry_run_selects_initial_writer_after_scope_gap_review_passed(self) -> None:
        self.test_case.unlink()
        self.write_state(status="scope-gap-review-passed", semantic_round=0)

        result = self.run_runner("start", "--state", str(self.state_path), "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("writer", payload["role"])
        self.assertEqual("writer-r1", payload["stage"])
        self.assertEqual("writer.session_initial_draft", payload["scenario"])
        self.assertEqual("workspace_write", payload["sandbox_policy"])

    def test_start_dry_run_routes_structure_preflight_blocker_to_writer_remediation(self) -> None:
        self.write_state(status="structure-preflight-blocked", semantic_round=1)

        result = self.run_runner("start", "--state", str(self.state_path), "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("start-session", payload["action"])
        self.assertEqual("writer", payload["role"])
        self.assertEqual("writer-structure-r1", payload["stage"])
        self.assertEqual("writer.remediation.style", payload["scenario"])
        self.assertEqual("workspace_write", payload["sandbox_policy"])

    def test_start_dry_run_blocks_writer_after_second_semantic_round(self) -> None:
        self.write_state(status="semantic-revision-needed", semantic_round=2)

        result = self.run_runner("start", "--state", str(self.state_path), "--dry-run")

        self.assertEqual(result.returncode, 2)
        self.assertIn("semantic round cap reached", result.stderr)
        self.assertIn("do not start writer-r3", result.stderr)

    def test_snapshot_copies_canonical_state_and_design_artifacts(self) -> None:
        self.write_state(status="semantic-review-ready", semantic_round=1)

        result = self.run_runner(
            "snapshot",
            "--state",
            str(self.state_path),
            "--snapshot-id",
            "r1-before-review",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        snapshot_dir = self.cycle_dir / "versions" / "r1-before-review"
        snapshot_paths = {item["snapshot_path"] for item in payload["files"]}

        self.assertTrue((snapshot_dir / "snapshot-manifest.yaml").exists())
        self.assertIn("test-cases/1-section-scope.md", snapshot_paths)
        self.assertIn("work/review-cycles/section-scope/cycle-state.yaml", snapshot_paths)
        self.assertIn("work/review-cycles/section-scope/codex-session-map.yaml", snapshot_paths)
        self.assertIn("work/test-design/section-scope/traceability.md", snapshot_paths)

    def test_snapshot_includes_runner_output_artifacts_when_present(self) -> None:
        self.write_state(status="final-regression-ready", semantic_round=2)
        output_dir = self.cycle_dir / "outputs"
        output_dir.mkdir()
        (output_dir / "semantic-regression-final-final-response.md").write_text(
            "review response",
            encoding="utf-8",
        )

        result = self.run_runner(
            "snapshot",
            "--state",
            str(self.state_path),
            "--snapshot-id",
            "after-final-regression",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        snapshot_paths = {item["snapshot_path"] for item in payload["files"]}
        self.assertIn(
            "work/review-cycles/section-scope/outputs/semantic-regression-final-final-response.md",
            snapshot_paths,
        )

    def test_pre_writer_snapshot_skips_missing_canonical_test_case_file(self) -> None:
        self.test_case.unlink()
        self.write_state(status="scope-ready-for-gap-review", semantic_round=0)

        result = self.run_runner(
            "snapshot",
            "--state",
            str(self.state_path),
            "--snapshot-id",
            "before-scope-gap-review",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        snapshot_paths = {item["snapshot_path"] for item in payload["files"]}
        self.assertNotIn("test-cases/1-section-scope.md", snapshot_paths)
        self.assertIn("work/review-cycles/section-scope/cycle-state.yaml", snapshot_paths)

    def test_validate_rejects_snapshot_as_canonical_test_case(self) -> None:
        snapshot_case = (
            "work/review-cycles/section-scope/versions/r1/test-cases/1-section-scope.md"
        )
        (self.ft_root / snapshot_case).parent.mkdir(parents=True)
        (self.ft_root / snapshot_case).write_text("snapshot copy", encoding="utf-8")
        self.write_state(prompt="work/review-cycles/section-scope/prompts/next.md")
        content = self.state_path.read_text(encoding="utf-8").replace(
            "canonical_test_cases: test-cases/1-section-scope.md",
            f"canonical_test_cases: {snapshot_case}",
        )
        self.state_path.write_text(content, encoding="utf-8")

        result = self.run_runner("validate", "--state", str(self.state_path))

        self.assertEqual(result.returncode, 2)
        self.assertIn("must not point to a version snapshot", result.stderr)

    def test_run_until_terminal_dry_run_reports_first_stage_and_loop_intent(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        self.test_case.unlink()

        result = self.run_runner(
            "run-until-terminal",
            "--state",
            str(self.state_path),
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("dry-run-chain", payload["action"])
        self.assertEqual(12, payload["max_sessions"])
        self.assertEqual("writer-r1", payload["next"]["stage"])
        self.assertIn("first runnable stage", payload["note"])

    def test_run_until_terminal_reloads_state_until_terminal_status(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()
        calls: list[str] = []

        def fake_run_real_session(state, state_path, *, cwd, approval_mode, model, runner_lock=None):
            calls.append(state["stage_status"])
            updated = self.state_path.read_text(encoding="utf-8").replace(
                "stage_status: scope-ready-for-writer",
                "stage_status: signed-off",
            )
            self.state_path.write_text(updated, encoding="utf-8")
            return {
                "action": "completed-session",
                "stage": "writer-r1",
                "role": "writer",
                "scenario": "writer.session_initial_draft",
                "turn_status": "completed",
            }

        runner.run_real_session = fake_run_real_session
        payload = runner.run_until_terminal(
            self.state_path,
            cwd=None,
            approval_mode="auto_review",
            model=None,
            max_sessions=3,
        )

        self.assertEqual(["scope-ready-for-writer"], calls)
        self.assertEqual("completed-chain", payload["action"])
        self.assertEqual("signed-off", payload["final_status"])
        self.assertTrue(payload["terminal"])
        self.assertEqual(1, payload["sessions_started"])

    def test_run_until_terminal_accepts_terminal_after_last_allowed_session(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()

        def fake_run_real_session(state, state_path, *, cwd, approval_mode, model, runner_lock=None):
            updated = self.state_path.read_text(encoding="utf-8").replace(
                "stage_status: scope-ready-for-writer",
                "stage_status: signed-off",
            )
            self.state_path.write_text(updated, encoding="utf-8")
            return {
                "action": "completed-session",
                "stage": "writer-r1",
                "role": "writer",
                "scenario": "writer.session_initial_draft",
                "turn_status": "completed",
            }

        runner.run_real_session = fake_run_real_session
        payload = runner.run_until_terminal(
            self.state_path,
            cwd=None,
            approval_mode="auto_review",
            model=None,
            max_sessions=1,
        )

        self.assertEqual("completed-chain", payload["action"])
        self.assertEqual("signed-off", payload["final_status"])
        self.assertTrue(payload["terminal"])
        self.assertEqual(1, payload["sessions_started"])

    def test_run_until_terminal_rejects_completed_stage_without_state_progress(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()

        def fake_run_real_session(state, state_path, *, cwd, approval_mode, model, runner_lock=None):
            return {
                "action": "completed-session",
                "stage": "writer-r1",
                "role": "writer",
                "scenario": "writer.session_initial_draft",
                "turn_status": "completed",
            }

        runner.run_real_session = fake_run_real_session
        with self.assertRaisesRegex(runner.RunnerError, "did not advance"):
            runner.run_until_terminal(
                self.state_path,
                cwd=None,
                approval_mode="auto_review",
                model=None,
                max_sessions=3,
            )

    def test_run_until_terminal_accepts_interrupted_stage_when_state_advances(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()

        def fake_run_real_session(state, state_path, *, cwd, approval_mode, model, runner_lock=None):
            updated = self.state_path.read_text(encoding="utf-8").replace(
                "stage_status: scope-ready-for-writer",
                "stage_status: signed-off",
            )
            self.state_path.write_text(updated, encoding="utf-8")
            return {
                "action": "completed-session",
                "stage": "writer-r1",
                "role": "writer",
                "scenario": "writer.session_initial_draft",
                "turn_status": "interrupted",
                "session_status": "completed-with-progress",
            }

        runner.run_real_session = fake_run_real_session
        payload = runner.run_until_terminal(
            self.state_path,
            cwd=None,
            approval_mode="auto_review",
            model=None,
            max_sessions=1,
        )

        self.assertEqual("completed-chain", payload["action"])
        self.assertEqual("signed-off", payload["final_status"])
        self.assertTrue(payload["terminal"])
        self.assertEqual("completed-with-progress", payload["sessions"][0]["session_status"])

    def test_run_until_terminal_rejects_interrupted_stage_without_state_progress(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()

        def fake_run_real_session(state, state_path, *, cwd, approval_mode, model, runner_lock=None):
            return {
                "action": "completed-session",
                "stage": "writer-r1",
                "role": "writer",
                "scenario": "writer.session_initial_draft",
                "turn_status": "interrupted",
                "session_status": "failed",
            }

        runner.run_real_session = fake_run_real_session
        with self.assertRaisesRegex(runner.RunnerError, "did not advance"):
            runner.run_until_terminal(
                self.state_path,
                cwd=None,
                approval_mode="auto_review",
                model=None,
                max_sessions=1,
            )

    def test_classify_session_status_accepts_interrupted_only_with_progress(self) -> None:
        runner = load_runner_module()

        self.assertEqual(
            "completed-with-progress",
            runner.classify_session_status("interrupted", state_advanced=True),
        )
        self.assertEqual(
            "failed",
            runner.classify_session_status("interrupted", state_advanced=False),
        )
        self.assertEqual(
            "failed",
            runner.classify_session_status("failed", state_advanced=True),
        )

    def test_run_real_session_records_started_thread_before_sdk_run_exception(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()

        class FakeSandbox:
            read_only = "read_only"
            workspace_write = "workspace_write"
            full_access = "full_access"

        class FakeApprovalMode:
            auto_review = "auto_review"
            deny_all = "deny_all"

        class FakeThread:
            id = "thread-started-before-error"

            def set_name(self, name: str) -> None:
                self.name = name

            def run(self, *args, **kwargs):
                raise RuntimeError("sdk run failed")

        class FakeCodex:
            def thread_start(self, *args, **kwargs):
                return FakeThread()

            def close(self) -> None:
                pass

        old_module = sys.modules.get("openai_codex")
        sys.modules["openai_codex"] = type(
            "FakeOpenAICodex",
            (),
            {
                "Codex": FakeCodex,
                "Sandbox": FakeSandbox,
                "ApprovalMode": FakeApprovalMode,
            },
        )
        try:
            with self.assertRaisesRegex(RuntimeError, "sdk run failed"):
                runner.run_real_session(
                    runner.load_simple_yaml(self.state_path),
                    self.state_path,
                    cwd=None,
                    approval_mode="auto_review",
                    model=None,
                )
        finally:
            if old_module is None:
                sys.modules.pop("openai_codex", None)
            else:
                sys.modules["openai_codex"] = old_module

        session_map = (self.cycle_dir / "codex-session-map.yaml").read_text(encoding="utf-8")
        self.assertIn("thread_id: thread-started-before-error", session_map)
        self.assertIn("status: started", session_map)
        self.assertIn("status: failed", session_map)
        self.assertIn("error: RuntimeError", session_map)

    def test_run_real_session_records_completed_with_progress_for_interrupted_turn(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()

        class FakeSandbox:
            read_only = "read_only"
            workspace_write = "workspace_write"
            full_access = "full_access"

        class FakeApprovalMode:
            auto_review = "auto_review"
            deny_all = "deny_all"

        class FakeTurn:
            id = "turn-interrupted-after-progress"
            status = "interrupted"
            final_response = "stage wrote artifacts and advanced state"
            duration_ms = 123

        class FakeThread:
            id = "thread-interrupted-after-progress"

            def set_name(self, name: str) -> None:
                self.name = name

            def run(self, *args, **kwargs):
                updated = self_state_path.read_text(encoding="utf-8").replace(
                    "stage_status: scope-ready-for-writer",
                    "stage_status: signed-off",
                )
                self_state_path.write_text(updated, encoding="utf-8")
                return FakeTurn()

        class FakeCodex:
            def thread_start(self, *args, **kwargs):
                return FakeThread()

            def close(self) -> None:
                pass

        self_state_path = self.state_path
        old_module = sys.modules.get("openai_codex")
        sys.modules["openai_codex"] = type(
            "FakeOpenAICodex",
            (),
            {
                "Codex": FakeCodex,
                "Sandbox": FakeSandbox,
                "ApprovalMode": FakeApprovalMode,
            },
        )
        try:
            payload = runner.run_real_session(
                runner.load_simple_yaml(self.state_path),
                self.state_path,
                cwd=None,
                approval_mode="auto_review",
                model=None,
            )
        finally:
            if old_module is None:
                sys.modules.pop("openai_codex", None)
            else:
                sys.modules["openai_codex"] = old_module

        self.assertEqual("interrupted", payload["turn_status"])
        self.assertEqual("completed-with-progress", payload["session_status"])
        self.assertTrue(payload["state_advanced"])
        completion_manifest = self.cycle_dir / "outputs" / "writer-r1-completion.yaml"
        self.assertEqual(str(completion_manifest), payload["completion_manifest"])
        self.assertTrue(completion_manifest.exists())
        completion_content = completion_manifest.read_text(encoding="utf-8")
        self.assertIn("turn_status: interrupted", completion_content)
        self.assertIn("session_status: completed-with-progress", completion_content)
        self.assertIn("state_advanced: true", completion_content)

        event_path = self.cycle_dir / "runner-events.ndjson"
        self.assertTrue(event_path.exists())
        event_names = [
            json.loads(line)["event"]
            for line in event_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertIn("thread_started", event_names)
        self.assertIn("turn_finished", event_names)
        self.assertIn("stage_completed", event_names)

        snapshot_manifest = (
            self.cycle_dir / "versions" / "after-writer-r1" / "snapshot-manifest.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("work/review-cycles/section-scope/runner-events.ndjson", snapshot_manifest)
        self.assertIn(
            "work/review-cycles/section-scope/outputs/writer-r1-completion.yaml",
            snapshot_manifest,
        )
        session_map = (self.cycle_dir / "codex-session-map.yaml").read_text(encoding="utf-8")
        self.assertIn("turn_status: interrupted", session_map)
        self.assertIn("status: completed-with-progress", session_map)
        self.assertIn("state_advanced: true", session_map)
        self.assertIn("completion_manifest: work/review-cycles/section-scope/outputs/writer-r1-completion.yaml", session_map)

    def test_session_prompt_keeps_session_map_runner_owned(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()
        state = runner.load_simple_yaml(self.state_path)
        next_session = runner.next_session_for_state(state)

        prompt = runner.prompt_text_for_session(state, self.state_path, next_session)

        self.assertIn("Do not edit codex-session-map.yaml", prompt)

    def test_session_prompt_requires_instruction_context_loading(self) -> None:
        self.write_state(status="semantic-review-ready", semantic_round=1)
        runner = load_runner_module()
        state = runner.load_simple_yaml(self.state_path)
        next_session = runner.next_session_for_state(state)

        prompt = runner.prompt_text_for_session(state, self.state_path, next_session)

        self.assertIn("Instruction loading contract:", prompt)
        self.assertIn(
            "python scripts/resolve_instruction_context.py --scenario reviewer.semantic_traceability_test_design --budget-report --fail-on-budget",
            prompt,
        )
        self.assertIn("Read every selected required file", prompt)
        self.assertIn("references/agent/test-design-defect-taxonomy.md", prompt)
        self.assertIn("references/agent/package-test-design-plan-format.md", prompt)
        self.assertIn("record the resolver command, budget status, and selected files", prompt)

    def test_runner_lock_blocks_parallel_run_on_same_state(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()

        with runner.RunnerFileLock(self.state_path, command="run-until-terminal"):
            with self.assertRaisesRegex(runner.RunnerError, "active runner lock exists"):
                with runner.RunnerFileLock(self.state_path, command="run-until-terminal"):
                    pass

    def test_doctor_reports_terminal_state_without_lock(self) -> None:
        self.write_state(status="signed-off", semantic_round=2)

        result = self.run_runner("doctor", "--state", str(self.state_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("doctor", payload["action"])
        self.assertTrue(payload["state_valid"])
        self.assertFalse(payload["lock"]["exists"])
        self.assertEqual("no-action-terminal-status", payload["recommendation"])

    def test_resume_dry_run_reports_doctor_payload_without_instruction_resolution(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        self.test_case.unlink()

        result = self.run_runner("resume", "--state", str(self.state_path), "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("doctor", payload["action"])
        self.assertTrue(payload["state_valid"])
        self.assertEqual("writer-r1", payload["next"]["stage"])
        self.assertEqual("run-next-stage", payload["recommendation"])

    def test_doctor_reports_stale_dead_lock_as_recoverable(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        lock_path = self.cycle_dir / "runner.lock.yaml"
        lock_path.write_text(
            "\n".join(
                [
                    "version: 1",
                    "pid: 99999999",
                    "command: run-until-terminal",
                    f"state: {self.state_path}",
                    "started_at_epoch: 1",
                    "last_heartbeat_epoch: 1",
                    "stage: semantic-review-r1",
                    "scenario: reviewer.semantic_traceability_test_design",
                    "thread_id: stale-thread-id",
                    "status: running-session",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_runner(
            "doctor",
            "--state",
            str(self.state_path),
            "--stale-lock-seconds",
            "1",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["lock"]["exists"])
        self.assertTrue(payload["lock"]["stale"])
        self.assertFalse(payload["lock"]["pid_alive"])
        self.assertTrue(payload["lock"]["safe_to_recover"])
        self.assertEqual("resume-with---recover-stale-lock", payload["recommendation"])

    def test_runner_lock_recover_stale_lock_archives_and_records_abort(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()
        lock_path = self.cycle_dir / runner.RUNNER_LOCK_FILE
        lock_path.write_text(
            "\n".join(
                [
                    "version: 1",
                    "pid: 999999",
                    "command: run-until-terminal",
                    f"state: {self.state_path}",
                    "started_at_epoch: 1",
                    "last_heartbeat_epoch: 1",
                    "stage: semantic-review-r1",
                    "scenario: reviewer.semantic_traceability_test_design",
                    "thread_id: stale-thread-id",
                    "status: running-session",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        with runner.RunnerFileLock(
            self.state_path,
            command="run-until-terminal",
            stale_lock_seconds=0,
            recover_stale_lock=True,
        ) as lock:
            self.assertEqual(1, lock.stale_lock_seconds)
            self.assertTrue(lock_path.exists())

        archives = list(self.cycle_dir.glob("runner.lock.recovered-*.yaml"))
        self.assertEqual(1, len(archives))
        session_map = (self.cycle_dir / "codex-session-map.yaml").read_text(encoding="utf-8")
        self.assertIn("thread_id: stale-thread-id", session_map)
        self.assertIn("status: aborted", session_map)
        self.assertIn("abort_reason: stale runner lock recovered", session_map)
        self.assertIn("recovered_pid: 999999", session_map)
        self.assertIn("recovered_command: run-until-terminal", session_map)
        self.assertIn("recovered_status: running-session", session_map)
        self.assertIn("recovered_last_heartbeat_epoch: 1", session_map)
        events = [
            json.loads(line)["event"]
            for line in (self.cycle_dir / "runner-events.ndjson").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertIn("lock_recovered", events)
        self.assertIn("lock_acquired", events)
        self.assertIn("lock_released", events)

    def test_runner_lock_updates_stage_and_thread_heartbeat(self) -> None:
        self.write_state(status="scope-ready-for-writer", semantic_round=0)
        runner = load_runner_module()
        lock_path = self.cycle_dir / runner.RUNNER_LOCK_FILE

        with runner.RunnerFileLock(self.state_path, command="run-until-terminal") as lock:
            lock.update(
                stage="semantic-review-r1",
                scenario="reviewer.semantic_traceability_test_design",
                thread_id="thread-123",
            )
            lock_data = runner.load_simple_yaml(lock_path)
            self.assertEqual("semantic-review-r1", lock_data["stage"])
            self.assertEqual("thread-123", lock_data["thread_id"])

        self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
