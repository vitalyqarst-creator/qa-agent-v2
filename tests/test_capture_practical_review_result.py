from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_capture_module():
    spec = importlib.util.spec_from_file_location(
        "capture_practical_review_result",
        ROOT / "scripts" / "capture_practical_review_result.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CapturePracticalReviewResultTests(unittest.TestCase):
    def test_capture_preserves_reviewer_json_bytes_without_normalization(self) -> None:
        module = load_capture_module()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            submission = root / "reviewer-submission.json"
            payload = '{\n  "source_anchor": "Таблица 8, столбец Р"\n}\n'
            submission.write_bytes(payload.encode("utf-8"))
            output = root / "matrix-review-result.json"

            result = module.capture(submission=submission, output=output)

            self.assertEqual("captured", result["status"])
            self.assertEqual(submission.read_bytes(), output.read_bytes())
            with self.assertRaises(FileExistsError):
                module.capture(submission=submission, output=output)

    def test_capture_rejects_non_object_json_without_creating_result(self) -> None:
        module = load_capture_module()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            submission = root / "reviewer-submission.json"
            submission.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            output = root / "matrix-review-result.json"

            with self.assertRaises(ValueError):
                module.capture(submission=submission, output=output)
            self.assertFalse(output.exists())

    def test_capture_rejects_oversized_submission_without_creating_result(self) -> None:
        module = load_capture_module()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            submission = root / "reviewer-submission.json"
            submission.write_text(json.dumps({"payload": "x" * 128}), encoding="utf-8")
            output = root / "matrix-review-result.json"

            with self.assertRaisesRegex(ValueError, "exceeds compact receipt limit"):
                module.capture(submission=submission, output=output, max_bytes=64)
            self.assertFalse(output.exists())

    def test_reviewer_submission_preflight_uses_manifest_bound(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = root / "matrix-review-manifest.json"
            manifest.write_text(
                json.dumps(
                    {"reviewer_receipt_contract": {"max_bytes": 96}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            submission = root / "reviewer-submission.json"
            submission.write_text(json.dumps({"value": "ok"}), encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "scripts" / "validate_practical_review_submission.py"),
                "--manifest",
                str(manifest),
                "--submission",
                str(submission),
            ]
            completed = subprocess.run(
                command, text=True, capture_output=True, encoding="utf-8", errors="replace"
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertIn('"status": "valid"', completed.stdout)

            submission.write_text(json.dumps({"value": "x" * 128}), encoding="utf-8")
            completed = subprocess.run(
                command, text=True, capture_output=True, encoding="utf-8", errors="replace"
            )
            self.assertEqual(2, completed.returncode, completed.stdout + completed.stderr)
            self.assertIn("exceeds manifest limit", completed.stdout)
