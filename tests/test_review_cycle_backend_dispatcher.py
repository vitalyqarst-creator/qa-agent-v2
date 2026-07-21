from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_cycle_backend_dispatcher.py"


def load_module():
    spec = importlib.util.spec_from_file_location("review_cycle_backend_dispatcher_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReviewCycleBackendDispatcherTests(unittest.TestCase):
    def capability(self, *, verified: bool, error: str = ""):
        module = load_module()
        return module.ExecCapability(
            command="codex",
            available=verified,
            verified=verified,
            returncode=0 if verified else 1,
            duration_ms=1,
            missing_flags=() if verified else ("--json",),
            error=error,
        )

    def test_auto_selects_exec_when_capability_is_verified(self) -> None:
        module = load_module()
        selection = module.select_backend("auto", self.capability(verified=True), allow_sdk_fallback=False)
        self.assertEqual("exec", selection.selected_backend)
        self.assertEqual(2, selection.contract_version)
        self.assertFalse(selection.fallback_used)

    def test_auto_blocks_instead_of_silent_sdk_fallback(self) -> None:
        module = load_module()
        with self.assertRaisesRegex(module.DispatcherError, "blocked-exec-runtime"):
            module.select_backend("auto", self.capability(verified=False), allow_sdk_fallback=False)

    def test_auto_uses_sdk_only_when_fallback_is_explicit(self) -> None:
        module = load_module()
        selection = module.select_backend("auto", self.capability(verified=False), allow_sdk_fallback=True)
        self.assertEqual("sdk", selection.selected_backend)
        self.assertEqual(1, selection.contract_version)
        self.assertTrue(selection.fallback_used)

    def test_exec_runner_command_enforces_verified_contract(self) -> None:
        module = load_module()
        command = module.runner_command(
            "exec",
            {"exec_runner_args": ["--ft-root", "fts/demo"]},
            repo_root=ROOT,
            exec_command="C:/codex.exe",
        )
        self.assertIn("codex_exec_review_cycle_runner.py", command[1])
        self.assertIn("--cli-contract-verified", command)
        self.assertIn("--codex-command", command)

    def test_exec_runner_command_forwards_direct_plugin_isolation_flags(self) -> None:
        module = load_module()
        command = module.runner_command(
            "exec",
            {"exec_runner_args": ["--ft-root", "fts/demo"]},
            repo_root=ROOT,
            exec_command="C:/codex.exe",
            exec_extra_args=(
                "--disable", "remote_plugin",
                "--disable", "plugins",
                "--disable", "apps",
            ),
        )

        self.assertEqual(3, command.count("--extra-arg=--disable"))
        self.assertIn("remote_plugin", command)
        self.assertIn("plugins", command)
        self.assertIn("apps", command)

    def test_exec_runner_command_rejects_different_configured_executable(self) -> None:
        module = load_module()

        with self.assertRaisesRegex(module.DispatcherError, "differs from the verified"):
            module.runner_command(
                "exec",
                {
                    "exec_runner_args": [
                        "--ft-root", "fts/demo",
                        "--codex-command", "C:/unverified.exe",
                    ]
                },
                repo_root=ROOT,
                exec_command="C:/verified.exe",
            )

    def test_exec_runner_command_rejects_unprobed_configurable_flag(self) -> None:
        module = load_module()

        with self.assertRaisesRegex(module.DispatcherError, "must be bound to --sandbox"):
            module.runner_command(
                "exec",
                {
                    "exec_runner_args": [
                        "--ft-root", "fts/demo",
                        "--sandbox-flag", "--bogus-sandbox",
                    ]
                },
                repo_root=ROOT,
                exec_command="C:/verified.exe",
            )

    def test_capability_probe_can_require_direct_image_flag(self) -> None:
        module = load_module()
        help_without_image = " ".join(module.REQUIRED_EXEC_HELP_FLAGS)
        completed = module.subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=help_without_image,
            stderr="",
        )
        with patch.object(module.subprocess, "run", return_value=completed):
            capability = module.probe_exec_capability(
                "codex",
                additional_required_flags=("--image",),
            )
        self.assertFalse(capability.verified)
        self.assertEqual(("--image",), capability.missing_flags)

    def test_exec_runner_command_binds_option_looking_flag_values(self) -> None:
        module = load_module()
        command = module.runner_command(
            "exec",
            {
                "exec_runner_args": [
                    "--sandbox-flag",
                    "--sandbox",
                    "--working-directory-flag",
                    "--cd",
                ]
            },
            repo_root=ROOT,
            exec_command="C:/codex.exe",
        )
        self.assertIn("--sandbox-flag=--sandbox", command)
        self.assertIn("--working-directory-flag=--cd", command)
        self.assertNotIn("--sandbox", command)
        self.assertNotIn("--cd", command)

    def test_config_rejects_cycle_dir_drift_before_execution(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "dispatcher.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "cycle_dir": "fts/demo/work/review-cycles/expected",
                        "exec_runner_args": [
                            "--cycle-dir",
                            "fts/demo/work/review-cycles/other",
                        ],
                        "sdk_runner_args": [],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(module.DispatcherError, "cycle_dir must exactly match"):
                module.load_config(path)

    def test_exec_preflight_uses_validate_only_and_surfaces_runner_failure(self) -> None:
        module = load_module()
        completed = module.subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout='{"status":"blocked-configuration","reason":"budget"}',
            stderr="",
        )

        with patch.object(module.subprocess, "run", return_value=completed) as mocked:
            with self.assertRaisesRegex(module.DispatcherError, "blocked-configuration-preflight"):
                module.preflight_exec_runner(["python", "runner.py"], repo_root=ROOT)

        self.assertEqual("--validate-only", mocked.call_args.args[0][-1])

    def test_production_profile_is_default_and_skips_benchmark_detail_scans(self) -> None:
        module = load_module()
        args = module.build_parser().parse_args(
            ["--selection-output", "selection.json", "--dry-run"]
        )
        self.assertEqual("production", args.run_profile)

        with tempfile.TemporaryDirectory() as tmp_dir:
            cycle = Path(tmp_dir)
            (cycle / "stage-metrics.ndjson").write_text(
                json.dumps({"duration_ms": 12, "input_tokens": 4}) + "\n",
                encoding="utf-8",
            )
            event = (
                cycle
                / "attempts"
                / "writer-r1"
                / "attempt-001"
                / "runner-output"
                / "events.ndjson"
            )
            event.parent.mkdir(parents=True)
            event.write_text(
                json.dumps(
                    {"type": "item.completed", "item": {"type": "command_execution"}}
                )
                + "\n",
                encoding="utf-8",
            )
            (cycle / "runner-events.ndjson").write_text(
                json.dumps(
                    {
                        "event": "stage_process_finished",
                        "backend_session_id": "session-production-1",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = module.summarize_exec_cycle(
                cycle,
                run_profile="production",
            )

        self.assertEqual("production", report["run_profile"])
        self.assertFalse(report["benchmark_details_included"])
        self.assertEqual([], report["stage_attribution"])
        self.assertEqual(["session-production-1"], report["backend_session_ids"])
        self.assertEqual(12, report["duration_ms_total"])

    def test_explicit_sdk_dry_run_skips_exec_capability_probe(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "selection.json"
            with patch.object(
                module,
                "resolve_verified_exec_capability",
            ) as resolver:
                code = module.main(
                    [
                        "--backend", "sdk",
                        "--selection-output", str(output),
                        "--dry-run",
                    ]
                )

        self.assertEqual(0, code)
        resolver.assert_not_called()

    def test_benchmark_profile_requires_performance_output(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config = root / "dispatcher.json"
            config.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "cycle_dir": "fts/demo/work/review-cycles/cycle",
                        "exec_runner_args": [],
                        "sdk_runner_args": [],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                module.DispatcherError,
                "--performance-output is required",
            ):
                module.main(
                    [
                        "--config",
                        str(config),
                        "--selection-output",
                        str(root / "selection.json"),
                        "--run-profile",
                        "benchmark",
                    ]
                )

    def test_timing_breakdown_separates_stage_and_orchestration_time(self) -> None:
        module = load_module()

        breakdown = module.build_timing_breakdown(
            capability_probe_ms=10,
            runner_preflight_ms=20,
            runner_wall_ms=1000,
            stage_execution_ms=850,
            reporting_ms=5,
            dispatcher_wall_ms=1040,
        )

        self.assertEqual(850, breakdown["stage_execution_ms"])
        self.assertEqual(150, breakdown["runner_orchestration_overhead_ms"])
        self.assertEqual(1040, breakdown["dispatcher_wall_ms"])

    def test_exec_performance_report_enforces_validator_budget(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp_dir:
            cycle = Path(tmp_dir)
            (cycle / "attempts" / "writer-r1" / "attempt-001" / "runner-output").mkdir(parents=True)
            (cycle / "attempts" / "writer-r1" / "attempt-001" / "runner-output" / "validator.json").write_text("{}", encoding="utf-8")
            (cycle / "stage-metrics.ndjson").write_text(
                json.dumps({"duration_ms": 10, "total_tokens": 20, "input_tokens": 15, "cached_input_tokens": 5, "input_artifact_bytes": 30, "output_artifact_bytes": 40}) + "\n",
                encoding="utf-8",
            )
            events = cycle / "attempts" / "writer-r1" / "attempt-001" / "runner-output" / "events.ndjson"
            events.write_text(
                "\n".join(
                    (
                        json.dumps({"type": "turn.started"}),
                        json.dumps({"type": "item.completed", "item": {"type": "agent_message"}}),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (cycle / "attempts" / "writer-r1" / "attempt-001" / "runner-output" / "context-budget.json").write_text(
                json.dumps(
                    {
                        "primary_context_bytes": 100,
                        "prompt_bytes": 40,
                        "instruction_bytes": 60,
                        "instruction_artifact_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            (cycle / "attempts" / "writer-r1" / "attempt-001" / "runner-output" / "obligation-gate.json").write_text(
                json.dumps({"test_case_count": 2, "testable_obligations": 2}),
                encoding="utf-8",
            )
            report = module.summarize_exec_cycle(cycle, validator_budget=1)
        self.assertTrue(report["validator_budget_passed"])
        self.assertEqual(1, report["validator_invocations"])
        self.assertEqual(20, report["total_tokens"])
        self.assertEqual(10, report["uncached_input_tokens_total"])
        self.assertEqual(1, report["stage_attribution"][0]["turns_started"])
        self.assertEqual(100, report["context_efficiency"]["primary_context_bytes_total"])
        self.assertEqual(5.0, report["context_efficiency"]["uncached_tokens_per_obligation"])
        self.assertEqual("benchmark", report["run_profile"])
        self.assertTrue(report["benchmark_details_included"])


if __name__ == "__main__":
    unittest.main()
