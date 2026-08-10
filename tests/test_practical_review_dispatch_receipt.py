from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK_ID = "019fda6b-f604-7130-80a5-8e0d1d7f5c7f"
CONTROLLER_ID = "019fda6b-f604-7130-80a5-8e0d7e3546a1"


class PracticalReviewDispatchReceiptTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "practical_review_dispatch_receipt.py"
        spec = importlib.util.spec_from_file_location(
            "practical_review_dispatch_receipt_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def launch_receipt(self, directory: Path, *, allowed: bool = True) -> Path:
        path = directory / "review-launch-preflight.json"
        path.write_text(json.dumps({"allowed": allowed}), encoding="utf-8")
        return path

    def test_binds_allowed_launch_to_separate_session_id(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            launch = self.launch_receipt(Path(tmp))
            result = helper.build_dispatch_receipt(
                launch_receipt=launch,
                reviewer_task_id=TASK_ID,
                reviewer_execution_surface="codex-thread",
                controller_task_id=CONTROLLER_ID,
            )

        self.assertTrue(result["allowed"], result["blocking_reasons"])
        self.assertEqual("dispatched", result["status"])
        self.assertEqual(TASK_ID, result["reviewer_task_or_session"])
        self.assertEqual(CONTROLLER_ID, result["controller_task_or_session"])

    def test_rejects_invalid_task_id_or_blocked_launch(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            launch = self.launch_receipt(Path(tmp), allowed=False)
            result = helper.build_dispatch_receipt(
                launch_receipt=launch,
                reviewer_task_id="reviewer-round-1",
                reviewer_execution_surface="codex-thread",
                controller_task_id=CONTROLLER_ID,
            )

        self.assertFalse(result["allowed"])
        self.assertIn("launch receipt is not allowed", result["blocking_reasons"])
        self.assertIn("reviewer session id", "\n".join(result["blocking_reasons"]))

    def test_rejects_subagent_execution_surface(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            launch = self.launch_receipt(Path(tmp))
            result = helper.build_dispatch_receipt(
                launch_receipt=launch,
                reviewer_task_id=TASK_ID,
                reviewer_execution_surface="codex-task",
                controller_task_id=CONTROLLER_ID,
            )

        self.assertFalse(result["allowed"])
        self.assertIn("codex-thread", "\n".join(result["blocking_reasons"]))

    def test_rejects_dispatch_when_current_controller_state_no_longer_matches_launch(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            launch = self.launch_receipt(Path(tmp))
            launch.write_text(
                json.dumps(
                    {
                        "allowed": True,
                        "repo_root": "C:/repo",
                        "ft_package_root": "C:/repo/fts/Sample",
                        "summary_path": "C:/repo/fts/Sample/work/practical-stage-summary.md",
                        "scope_ids": ["01"],
                        "review_mode": "matrix_review",
                    }
                ),
                encoding="utf-8",
            )
            original_verify = helper.review_preflight.verify_receipt
            helper.review_preflight.verify_receipt = lambda *_: [
                "receipt summary digest differs from current state"
            ]
            try:
                result = helper.build_dispatch_receipt(
                    launch_receipt=launch,
                    reviewer_task_id=TASK_ID,
                    reviewer_execution_surface="codex-thread",
                    controller_task_id=CONTROLLER_ID,
                )
            finally:
                helper.review_preflight.verify_receipt = original_verify

        self.assertFalse(result["allowed"])
        self.assertFalse(result["controller_state_verified"])
        self.assertIn("summary digest", "\n".join(result["blocking_reasons"]))

    def test_rejects_reviewer_dispatch_that_claims_the_controller_id(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            launch = self.launch_receipt(Path(tmp))
            result = helper.build_dispatch_receipt(
                launch_receipt=launch,
                reviewer_task_id=TASK_ID,
                reviewer_execution_surface="codex-thread",
                controller_task_id=TASK_ID,
            )

        self.assertFalse(result["allowed"])
        self.assertIn("must differ", "\n".join(result["blocking_reasons"]))

    def test_blocked_dispatch_does_not_persist_provisional_receipt(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            launch = self.launch_receipt(directory)
            output = directory / "review-dispatch.json"
            previous_argv = sys.argv
            try:
                sys.argv = [
                    "practical_review_dispatch_receipt.py",
                    "--launch-receipt",
                    str(launch),
                    "--reviewer-session-id",
                    "not-a-durable-thread-id",
                    "--reviewer-execution-surface",
                    "codex-thread",
                    "--output",
                    str(output),
                ]
                self.assertEqual(2, helper.main())
            finally:
                sys.argv = previous_argv

            self.assertFalse(output.exists())

    def test_dispatch_does_not_replace_prior_receipt(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            launch = self.launch_receipt(directory)
            output = directory / "review-dispatch.json"
            output.write_text("previous receipt\n", encoding="utf-8")
            previous_argv = sys.argv
            try:
                sys.argv = [
                    "practical_review_dispatch_receipt.py",
                    "--launch-receipt",
                    str(launch),
                    "--reviewer-session-id",
                    TASK_ID,
                    "--reviewer-execution-surface",
                    "codex-thread",
                    "--output",
                    str(output),
                ]
                with patch.dict("os.environ", {"CODEX_THREAD_ID": CONTROLLER_ID}):
                    self.assertEqual(2, helper.main())
            finally:
                sys.argv = previous_argv

            self.assertEqual("previous receipt\n", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
