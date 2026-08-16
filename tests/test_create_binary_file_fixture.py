from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "create_binary_file_fixture.py"


def load_module():
    spec = importlib.util.spec_from_file_location("binary_file_fixture", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BinaryFileFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()

    def test_creates_exact_size_receipted_binary_fixtures(self) -> None:
        expected_magic = {"jpg": b"\xff\xd8", "png": b"\x89PNG", "pdf": b"%PDF", "txt": b"x"}
        with tempfile.TemporaryDirectory() as directory:
            for file_format, magic in expected_magic.items():
                output_dir = Path(directory) / f"FX-FILE-{file_format.upper()}-001"
                receipt = self.module.create_binary_file_fixture(
                    fixture_id=f"FX-FILE-{file_format.upper()}-001",
                    file_format=file_format,
                    size_bytes=1_048_576,
                    output_dir=output_dir,
                    purpose="Проверка точного размера файла",
                    clock=lambda: datetime(2026, 8, 16, tzinfo=timezone.utc),
                )
                file_path = output_dir / receipt["file"]["path"]
                self.assertEqual(1_048_576, file_path.stat().st_size)
                self.assertTrue(file_path.read_bytes().startswith(magic))
                self.assertEqual(hashlib.sha256(file_path.read_bytes()).hexdigest(), receipt["file"]["sha256"])
                receipt_path = output_dir / f"{receipt['fixture_id']}.receipt.json"
                self.assertEqual(receipt, json.loads(receipt_path.read_text(encoding="utf-8")))
                self.assertFalse(receipt["generation"]["network_used"])
                if file_format in {"jpg", "png"}:
                    with Image.open(file_path) as image:
                        image.verify()

    def test_rejects_too_small_binary_file_without_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "FX-FILE-PNG-001"
            with self.assertRaisesRegex(self.module.BinaryFixtureError, "smaller than the minimum"):
                self.module.create_binary_file_fixture(
                    fixture_id="FX-FILE-PNG-001",
                    file_format="png",
                    size_bytes=1,
                    output_dir=output_dir,
                    purpose="Проверка ограничения",
                )
            self.assertFalse(output_dir.exists())

    def test_rejects_existing_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "FX-FILE-TXT-001"
            output_dir.mkdir()
            with self.assertRaisesRegex(self.module.BinaryFixtureError, "new immutable directory"):
                self.module.create_binary_file_fixture(
                    fixture_id="FX-FILE-TXT-001",
                    file_format="txt",
                    size_bytes=10,
                    output_dir=output_dir,
                    purpose="Проверка неизменяемости",
                )


if __name__ == "__main__":
    unittest.main()
