from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


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
            report = module.summarize_exec_cycle(cycle, validator_budget=1)
        self.assertTrue(report["validator_budget_passed"])
        self.assertEqual(1, report["validator_invocations"])
        self.assertEqual(20, report["total_tokens"])
        self.assertEqual(10, report["uncached_input_tokens_total"])
        self.assertEqual(1, report["stage_attribution"][0]["turns_started"])


if __name__ == "__main__":
    unittest.main()
