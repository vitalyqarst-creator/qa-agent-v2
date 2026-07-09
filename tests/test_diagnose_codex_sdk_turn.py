from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT_DIR / "scripts" / "diagnose_codex_sdk_turn.py"


class DiagnoseCodexSdkTurnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fake_sdk_dir = self.root / "fake_sdk"
        self.fake_sdk_dir.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_fake_sdk(self, *, blocks: bool) -> None:
        run_body = (
            "        time.sleep(30)\n"
            "        return FakeTurn()\n"
            if blocks
            else "        return FakeTurn()\n"
        )
        (self.fake_sdk_dir / "openai_codex.py").write_text(
            "\n".join(
                [
                    "import time",
                    "",
                    "class Sandbox:",
                    "    read_only = 'read_only'",
                    "    workspace_write = 'workspace_write'",
                    "    full_access = 'full_access'",
                    "",
                    "class ApprovalMode:",
                    "    auto_review = 'auto_review'",
                    "    AUTO_REVIEW = 'auto_review'",
                    "    deny_all = 'deny_all'",
                    "    DENY_ALL = 'deny_all'",
                    "",
                    "class FakeTurn:",
                    "    id = 'fake-turn-1'",
                    "    status = 'completed'",
                    "    final_response = 'OK'",
                    "    duration_ms = 1",
                    "",
                    "class FakeThread:",
                    "    id = 'fake-thread-1'",
                    "    def set_name(self, name):",
                    "        self.name = name",
                    "    def run(self, *args, **kwargs):",
                    run_body.rstrip("\n"),
                    "",
                    "class Codex:",
                    "    def thread_start(self, **kwargs):",
                    "        return FakeThread()",
                    "    def close(self):",
                    "        pass",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def run_diagnostic(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(self.fake_sdk_dir)
            if not current_pythonpath
            else str(self.fake_sdk_dir) + os.pathsep + current_pythonpath
        )
        return subprocess.run(
            [sys.executable, str(DIAGNOSTIC), *args],
            cwd=ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

    @staticmethod
    def read_events(output_dir: Path) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (output_dir / "events.ndjson").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_timeout_records_real_thread_id_after_turn_started(self) -> None:
        self.write_fake_sdk(blocks=True)
        output_dir = self.root / "diag-timeout"

        result = self.run_diagnostic(
            "--cwd",
            str(self.root),
            "--prompt-text",
            "Reply OK only",
            "--sandbox-policy",
            "read_only",
            "--approval-mode",
            "auto_review",
            "--timeout-seconds",
            "1",
            "--output-dir",
            str(output_dir),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("timeout", payload["status"])
        self.assertEqual("fake-thread-1", payload["thread_id"])
        self.assertEqual("sdk-turn-timeout-after-turn-started", payload["timeout_phase"])
        event_names = [event["event"] for event in self.read_events(output_dir)]
        self.assertIn("thread_started", event_names)
        self.assertIn("turn_started", event_names)
        self.assertIn("turn_timeout", event_names)
        timeout_event = self.read_events(output_dir)[-1]
        self.assertEqual("fake-thread-1", timeout_event["thread_id"])
        self.assertTrue((output_dir / "timeout.md").exists())
        self.assertFalse((output_dir / "response.md").exists())

    def test_harness_does_not_touch_review_cycle_files(self) -> None:
        self.write_fake_sdk(blocks=False)
        tracked_files = {
            self.root / "cycle-state.yaml": "stage_status: blocked-input\n",
            self.root / "runner.lock.yaml": "pid: 123\n",
            self.root / "codex-session-map.yaml": "sessions: []\n",
        }
        for path, content in tracked_files.items():
            path.write_text(content, encoding="utf-8")

        result = self.run_diagnostic(
            "--cwd",
            str(self.root),
            "--prompt-text",
            "Reply OK only",
            "--sandbox-policy",
            "workspace_write",
            "--approval-mode",
            "auto_review",
            "--timeout-seconds",
            "5",
            "--output-dir",
            str(self.root / "diag-success"),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("completed", payload["status"])
        self.assertEqual("fake-thread-1", payload["thread_id"])
        for path, content in tracked_files.items():
            self.assertEqual(content, path.read_text(encoding="utf-8"))
        self.assertEqual("OK", (self.root / "diag-success" / "response.md").read_text(encoding="utf-8"))

    def test_missing_sdk_runtime_reports_blocked_runtime_status(self) -> None:
        output_dir = self.root / "diag-missing-runtime"

        result = self.run_diagnostic(
            "--cwd",
            str(self.root),
            "--prompt-text",
            "Reply OK only",
            "--sandbox-policy",
            "read_only",
            "--approval-mode",
            "auto_review",
            "--timeout-seconds",
            "5",
            "--output-dir",
            str(output_dir),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("blocked-sdk-runtime", payload["status"])
        self.assertEqual(2, payload["returncode"])
        run_payload = json.loads((output_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual("blocked-sdk-runtime", run_payload["status"])
        self.assertIn("openai-codex is not installed", run_payload["stderr_tail"])


if __name__ == "__main__":
    unittest.main()
