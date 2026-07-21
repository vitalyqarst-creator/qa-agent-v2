from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from test_case_agent.overnight_controller import (
    ControllerError,
    OvernightController,
    initialize_run,
    load_state,
    render_summary,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "overnight_job.py"


class OvernightControllerTests(unittest.TestCase):
    def _job(
        self,
        job_id: str,
        classification: str,
        *,
        depends_on: list[str] | None = None,
        max_attempts: int = 1,
        backoff: int = 0,
        exit_code: int = 0,
        timeout_seconds: int | None = None,
        timeout_classification: str = "infrastructure",
        sleep_seconds: float = 0,
    ) -> dict[str, object]:
        return {
            "job_id": job_id,
            "scope": job_id,
            "kind": "fixture",
            "depends_on": depends_on or [],
            "max_attempts": max_attempts,
            "retry_backoff_seconds": backoff,
            "command": [
                sys.executable,
                str(FIXTURE),
                "--attempt-dir",
                "{attempt_dir}",
                "--classification",
                classification,
                "--exit-code",
                str(exit_code),
                "--sleep-seconds",
                str(sleep_seconds),
            ],
            "timeout_seconds": timeout_seconds,
            "timeout_classification": timeout_classification,
        }

    def _state(self, directory: Path, jobs: list[dict[str, object]], guards=()) -> Path:
        return initialize_run(
            run_dir=directory / "run",
            run_id="test-run",
            goal="Проверить устойчивое продолжение очереди.",
            jobs=jobs,
            repo_root=ROOT,
            source_guard_paths=guards,
        )

    def test_scope_blocker_does_not_stop_later_independent_work(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [
                    self._job("blocked", "scope-blocker"),
                    self._job("next", "completed"),
                ],
            )
            payload = OvernightController(state_path).run()
            states = {job["job_id"]: job["state"] for job in payload["queue"]}
            self.assertEqual("blocked-scope", states["blocked"])
            self.assertEqual("completed", states["next"])
            self.assertEqual("completed-with-blockers", payload["overall_status"])
            self.assertEqual(["blocked"], [item["job_id"] for item in payload["scope_blockers"]])

    def test_transient_retry_uses_a_new_immutable_attempt_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [self._job("live", "transient", max_attempts=2)],
            )
            first = OvernightController(state_path).run(max_jobs=1)
            self.assertEqual("deferred-transient", first["queue"][0]["state"])
            first_attempt = first["queue"][0]["attempts"][0]
            first_command = Path(first_attempt["command_file"]).read_bytes()
            second = OvernightController(state_path).run(max_jobs=1)
            self.assertEqual("deferred-transient", second["queue"][0]["state"])
            self.assertTrue(second["queue"][0]["retry_exhausted"])
            self.assertEqual("completed-with-blockers", second["overall_status"])
            self.assertIn(" retry ", second["queue"][0]["continuation_command"])
            attempts = second["queue"][0]["attempts"]
            self.assertEqual(2, len(attempts))
            self.assertNotEqual(attempts[0]["attempt_id"], attempts[1]["attempt_id"])
            self.assertNotEqual(attempts[0]["attempt_dir"], attempts[1]["attempt_dir"])
            self.assertEqual(first_command, Path(attempts[0]["command_file"]).read_bytes())

    def test_interrupted_running_attempt_is_deferred_before_fresh_retry(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [self._job("interrupted", "completed", max_attempts=2)],
            )
            payload = load_state(state_path)
            attempt_dir = state_path.parent / "attempts" / "interrupted" / "attempt-001-fixed"
            attempt_dir.mkdir(parents=True)
            job = payload["queue"][0]
            job["state"] = "running"
            job["attempts"].append(
                {
                    "attempt_id": "attempt-001-fixed",
                    "attempt_dir": str(attempt_dir),
                    "status": "running",
                    "classification": None,
                }
            )
            payload["current_work"] = "interrupted"
            state_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            finished = OvernightController(state_path).run(max_jobs=1)
            attempts = finished["queue"][0]["attempts"]
            self.assertEqual("interrupted", attempts[0]["status"])
            self.assertEqual("completed", attempts[1]["status"])
            self.assertNotEqual(attempts[0]["attempt_dir"], attempts[1]["attempt_dir"])

    def test_global_source_guard_stops_before_command(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            guarded = directory / "source.xhtml"
            guarded.write_text("old", encoding="utf-8")
            state_path = self._state(
                directory,
                [self._job("guarded", "completed")],
                guards=(guarded,),
            )
            guarded.write_text("new", encoding="utf-8")
            with self.assertRaisesRegex(ControllerError, "guarded source files changed"):
                OvernightController(state_path).run()
            payload = load_state(state_path)
            self.assertEqual("blocked-global", payload["overall_status"])
            self.assertEqual([], payload["queue"][0]["attempts"])

    def test_retry_requeues_blocked_job_and_extends_attempt_budget(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [self._job("blocked", "scope-blocker")],
            )
            OvernightController(state_path).run()
            controller = OvernightController(state_path)
            controller.retry("blocked")
            payload = load_state(state_path)
            self.assertEqual("pending", payload["queue"][0]["state"])
            self.assertEqual(2, payload["queue"][0]["max_attempts"])

    def test_summary_contains_states_and_exact_continuation_commands(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [self._job("pending", "completed")],
            )
            payload = load_state(state_path)
            summary = render_summary(payload)
            self.assertIn("`pending`", summary)
            self.assertIn("--state", summary)
            self.assertIn(str(state_path.resolve()), summary)

    def test_nonzero_exit_cannot_self_declare_completed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [self._job("dishonest", "completed", exit_code=7)],
            )
            payload = OvernightController(state_path).run()
            self.assertEqual("failed-infrastructure", payload["queue"][0]["state"])
            self.assertIn(
                "non-zero process exit",
                payload["queue"][0]["attempts"][0]["result"]["error"],
            )

    def test_watchdog_terminates_hung_job_and_preserves_transient_classification(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [
                    self._job(
                        "hung-live",
                        "completed",
                        timeout_seconds=1,
                        timeout_classification="transient",
                        sleep_seconds=30,
                    )
                ],
            )
            payload = OvernightController(state_path).run()
            job = payload["queue"][0]
            self.assertEqual("deferred-transient", job["state"])
            self.assertTrue(job["retry_exhausted"])
            attempt = job["attempts"][0]
            self.assertTrue(attempt["timed_out"])
            self.assertEqual("transient", attempt["classification"])
            self.assertIn("job timeout after 1 seconds", job["last_error"])

    def test_terminal_dependency_is_propagated_without_pending_livelock(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [
                    self._job("scope", "scope-blocker"),
                    self._job("dependent", "completed", depends_on=["scope"]),
                    self._job("independent", "completed"),
                ],
            )
            payload = OvernightController(state_path).run()
            states = {job["job_id"]: job["state"] for job in payload["queue"]}
            self.assertEqual("blocked-scope", states["dependent"])
            self.assertEqual("completed", states["independent"])
            self.assertEqual("completed-with-blockers", payload["overall_status"])

    def test_finished_attempt_artifacts_are_hash_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            state_path = self._state(
                Path(raw),
                [self._job("guarded-attempt", "completed")],
            )
            payload = OvernightController(state_path).run()
            stdout = Path(payload["queue"][0]["attempts"][0]["stdout"])
            stdout.write_bytes(stdout.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ControllerError, "attempt evidence changed"):
                OvernightController(state_path).run()
            self.assertEqual(
                "blocked-global", load_state(state_path)["overall_status"]
            )

    def test_dependency_cycle_is_rejected_at_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(ControllerError, "dependency cycle"):
                self._state(
                    Path(raw),
                    [
                        self._job("one", "completed", depends_on=["two"]),
                        self._job("two", "completed", depends_on=["one"]),
                    ],
                )


if __name__ == "__main__":
    unittest.main()
