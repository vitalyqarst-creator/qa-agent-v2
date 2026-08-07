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

    def test_binds_allowed_launch_to_controller_task_id(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            launch = self.launch_receipt(Path(tmp))
            result = helper.build_dispatch_receipt(
                launch_receipt=launch,
                reviewer_task_id=TASK_ID,
                reviewer_execution_surface="codex-task",
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
                reviewer_execution_surface="codex-task",
            )

        self.assertFalse(result["allowed"])
        self.assertIn("launch receipt is not allowed", result["blocking_reasons"])
        self.assertIn("reviewer task id", "\n".join(result["blocking_reasons"]))


if __name__ == "__main__":
    unittest.main()
