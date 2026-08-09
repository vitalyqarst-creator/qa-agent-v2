from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "create_randomdatatools_synthetic_fixture.py"


def load_module():
    spec = importlib.util.spec_from_file_location("randomdatatools_fixture", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    status = 200

    def __init__(self, payload: dict[str, object]) -> None:
        self._body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit: int | None = None) -> bytes:
        return self._body


class RandomDataToolsSyntheticFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.payload = {
            "profile": {"email": "test.user@example.test", "phone": "+79991234567"},
            "full_name": "Тестовый Пользователь",
        }

    def test_creates_one_immutable_snapshot_with_selected_literals_and_hash(self) -> None:
        calls = []

        def opener(request, *, timeout):
            calls.append((request.full_url, request.get_method(), timeout))
            return FakeResponse(self.payload)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "FX-SYNTH-CONTACT-001"
            receipt = self.module.create_synthetic_fixture(
                fixture_id="FX-SYNTH-CONTACT-001",
                purpose="Проверка формата контактов",
                selected_paths={"email": "profile.email", "phone": "profile.phone"},
                required_paths=("full_name",),
                patterns_by_name={
                    "email": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                    "phone": r"^\+7\d{10}$",
                },
                output_dir=output_dir,
                opener=opener,
                clock=lambda: datetime(2026, 8, 9, tzinfo=timezone.utc),
            )
            snapshot = output_dir / "FX-SYNTH-CONTACT-001.response.json"
            receipt_file = output_dir / "FX-SYNTH-CONTACT-001.fixture.json"

            self.assertEqual([(self.module.ENDPOINT, "GET", 30.0)], calls)
            self.assertTrue(snapshot.exists())
            self.assertTrue(receipt_file.exists())
            self.assertEqual("generated", receipt["status"])
            self.assertEqual(1, receipt["generation"]["request_count"])
            self.assertFalse(receipt["lifecycle"]["runtime_live_calls_allowed"])
            self.assertEqual("test.user@example.test", receipt["selection"]["selected_values"]["email"])
            self.assertEqual(
                hashlib.sha256(snapshot.read_bytes()).hexdigest(), receipt["response_sha256"]
            )
            self.assertEqual(receipt, json.loads(receipt_file.read_text(encoding="utf-8")))

    def test_rejects_unmatched_pattern_without_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "FX-SYNTH-CONTACT-001"
            with self.assertRaisesRegex(self.module.SyntheticFixtureError, "does not satisfy"):
                self.module.create_synthetic_fixture(
                    fixture_id="FX-SYNTH-CONTACT-001",
                    purpose="Проверка формата контакта",
                    selected_paths={"email": "profile.email"},
                    patterns_by_name={"email": r"^\d+$"},
                    output_dir=output_dir,
                    opener=lambda *_args, **_kwargs: FakeResponse(self.payload),
                )
            self.assertFalse(output_dir.exists())

    def test_rejects_non_synthetic_fixture_id_before_live_call(self) -> None:
        opened = False

        def opener(*_args, **_kwargs):
            nonlocal opened
            opened = True
            return FakeResponse(self.payload)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(self.module.SyntheticFixtureError, "FX-SYNTH"):
                self.module.create_synthetic_fixture(
                    fixture_id="FX-DADATA-PARTY-001",
                    purpose="Проверка формата контакта",
                    selected_paths={"email": "profile.email"},
                    output_dir=Path(directory) / "fixture",
                    opener=opener,
                )
        self.assertFalse(opened)


if __name__ == "__main__":
    unittest.main()
