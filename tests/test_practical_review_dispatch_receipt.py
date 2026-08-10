from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TASK_ID = "019fda6b-f604-7130-80a5-8e0d1d7f5c7f"


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
            )

        self.assertTrue(result["allowed"], result["blocking_reasons"])
        self.assertEqual("dispatched", result["status"])
        self.assertEqual(TASK_ID, result["reviewer_task_or_session"])

    def test_rejects_invalid_task_id_or_blocked_launch(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            launch = self.launch_receipt(Path(tmp), allowed=False)
            result = helper.build_dispatch_receipt(
                launch_receipt=launch,
                reviewer_task_id="reviewer-round-1",
                reviewer_execution_surface="codex-thread",
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
                )
            finally:
                helper.review_preflight.verify_receipt = original_verify

        self.assertFalse(result["allowed"])
        self.assertFalse(result["controller_state_verified"])
        self.assertIn("summary digest", "\n".join(result["blocking_reasons"]))


if __name__ == "__main__":
    unittest.main()
