from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.verify_dadata_negative_fixture import (
    DadataFixtureVerificationError,
    ENDPOINT,
    verify_negative_fixture,
)


class _Response:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.status = status
        self._body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def getcode(self) -> int:
        return self.status

    def read(self) -> bytes:
        return self._body


class VerifyDadataNegativeFixtureTests(unittest.TestCase):
    def test_requires_token_before_network_or_output(self) -> None:
        called = False

        def opener(*_args: object, **_kwargs: object) -> _Response:
            nonlocal called
            called = True
            return _Response({"suggestions": []})

        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "evidence"
            with self.assertRaisesRegex(
                DadataFixtureVerificationError,
                "DADATA_API_KEY is unavailable",
            ):
                verify_negative_fixture(
                    query="candidate",
                    fixture_id="FX-DADATA-ADDR-NEG-001",
                    output_dir=output,
                    token="",
                    opener=opener,
                )
            self.assertFalse(called)
            self.assertFalse(output.exists())

    def test_rejects_nonempty_suggestions_without_writing(self) -> None:
        calls = 0

        def opener(*_args: object, **_kwargs: object) -> _Response:
            nonlocal calls
            calls += 1
            return _Response({"suggestions": [{"value": "match"}]})

        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "evidence"
            with self.assertRaisesRegex(
                DadataFixtureVerificationError,
                r"not exactly suggestions=\[\]",
            ):
                verify_negative_fixture(
                    query="candidate",
                    fixture_id="FX-DADATA-ADDR-NEG-001",
                    output_dir=output,
                    token="secret-for-test",
                    opener=opener,
                )
            self.assertEqual(1, calls)
            self.assertFalse(output.exists())

    def test_requires_at_least_two_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(
                DadataFixtureVerificationError,
                "attempts must be between 2 and 5",
            ):
                verify_negative_fixture(
                    query="candidate",
                    fixture_id="FX-DADATA-ADDR-NEG-001",
                    output_dir=Path(raw) / "evidence",
                    token="secret-for-test",
                    attempts=1,
                )

    def test_writes_token_free_evidence_after_two_exact_responses(self) -> None:
        requests = []
        moments = iter(
            [
                datetime(2026, 7, 21, 1, 2, 3, tzinfo=timezone.utc),
                datetime(2026, 7, 21, 1, 2, 4, tzinfo=timezone.utc),
            ]
        )

        def opener(request: object, **_kwargs: object) -> _Response:
            requests.append(request)
            return _Response({"suggestions": []})

        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "evidence"
            receipt = verify_negative_fixture(
                query="  impossible candidate  ",
                fixture_id="FX-DADATA-ADDR-NEG-001",
                output_dir=output,
                token="secret-for-test",
                opener=opener,
                clock=lambda: next(moments),
            )
            snapshot = output / "FX-DADATA-ADDR-NEG-001.response.json"
            verification = output / "FX-DADATA-ADDR-NEG-001.verification.json"
            expected_bytes = b'{"suggestions":[]}\n'

            self.assertEqual(2, len(requests))
            self.assertTrue(all(request.full_url == ENDPOINT for request in requests))
            self.assertTrue(
                all(
                    request.get_header("Authorization") == "Token secret-for-test"
                    for request in requests
                )
            )
            self.assertTrue(
                all(
                    request.data == b'{"query":"  impossible candidate  "}\n'
                    for request in requests
                )
            )
            self.assertEqual(expected_bytes, snapshot.read_bytes())
            self.assertEqual(
                hashlib.sha256(expected_bytes).hexdigest(),
                receipt["response_sha256"],
            )
            stored = verification.read_text(encoding="utf-8")
            self.assertNotIn("secret-for-test", stored)
            self.assertEqual(
                "  impossible candidate  ",
                json.loads(stored)["request"]["parameters"]["query"],
            )

    def test_refuses_existing_output_directory_before_network(self) -> None:
        called = False

        def opener(*_args: object, **_kwargs: object) -> _Response:
            nonlocal called
            called = True
            return _Response({"suggestions": []})

        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(
                DadataFixtureVerificationError,
                "new immutable directory",
            ):
                verify_negative_fixture(
                    query="candidate",
                    fixture_id="FX-DADATA-ADDR-NEG-001",
                    output_dir=Path(raw),
                    token="secret-for-test",
                    opener=opener,
                )
            self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
