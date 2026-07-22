from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.verify_dadata_positive_fixture import (
    DadataFixtureVerificationError,
    FMS_UNIT_ENDPOINT,
    PARTY_ENDPOINT,
    verify_positive_fixture,
)


class _Response:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")

    def getcode(self) -> int:
        return self.status


class PositiveDadataFixtureVerifierTests(unittest.TestCase):
    payload = {
        "suggestions": [
            {
                "value": "Саратовская обл",
                "unrestricted_value": "Саратовская обл",
                "data": {"region_with_type": "Саратовская обл"},
            }
        ]
    }

    def test_writes_token_free_immutable_evidence_after_two_identical_matches(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "fixture"
            calls: list[object] = []

            def opener(request: object, timeout: float) -> _Response:
                calls.append((request, timeout))
                return _Response(self.payload)

            receipt = verify_positive_fixture(
                query="Саратов",
                fixture_id="FX-DADATA-REGION-POS-001",
                expected_suggestion="Саратовская обл",
                expected_components={"region_with_type": "Саратовская обл"},
                output_dir=output,
                token="secret-token",
                request_parameters={
                    "from_bound": {"value": "region"},
                    "to_bound": {"value": "region"},
                },
                opener=opener,
                clock=lambda: datetime(2026, 7, 21, tzinfo=timezone.utc),
            )

            self.assertEqual(2, len(calls))
            self.assertTrue(receipt["verification"]["all_responses_identical"])
            snapshot = output / "FX-DADATA-REGION-POS-001.response.json"
            verification = output / "FX-DADATA-REGION-POS-001.verification.json"
            self.assertEqual(self.payload, json.loads(snapshot.read_text(encoding="utf-8")))
            evidence = verification.read_text(encoding="utf-8")
            self.assertNotIn("secret-token", evidence)
            self.assertEqual(receipt, json.loads(evidence))

    def test_rejects_component_mismatch_without_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "fixture"
            with self.assertRaisesRegex(
                DadataFixtureVerificationError, "components differ"
            ):
                verify_positive_fixture(
                    query="Саратов",
                    fixture_id="FX-DADATA-REGION-POS-001",
                    expected_suggestion="Саратовская обл",
                    expected_components={"region_with_type": "Другая область"},
                    output_dir=output,
                    token="token",
                    opener=lambda *_args, **_kwargs: _Response(self.payload),
                )
            self.assertFalse(output.exists())

    def test_suggestion_mismatch_reports_token_free_actual_values(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "fixture"
            with self.assertRaisesRegex(
                DadataFixtureVerificationError, "Саратовская обл"
            ):
                verify_positive_fixture(
                    query="Саратов",
                    fixture_id="FX-DADATA-REGION-POS-001",
                    expected_suggestion="Другая область",
                    expected_components={"region_with_type": "Другая область"},
                    output_dir=output,
                    token="token",
                    opener=lambda *_args, **_kwargs: _Response(self.payload),
                )
            self.assertFalse(output.exists())

    def test_rejects_changed_second_response(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "fixture"
            responses = [
                self.payload,
                {**self.payload, "metadata": "changed"},
            ]

            def opener(*_args: object, **_kwargs: object) -> _Response:
                return _Response(responses.pop(0))

            with self.assertRaisesRegex(
                DadataFixtureVerificationError, "changed between"
            ):
                verify_positive_fixture(
                    query="Саратов",
                    fixture_id="FX-DADATA-REGION-POS-001",
                    expected_suggestion="Саратовская обл",
                    expected_components={"region_with_type": "Саратовская обл"},
                    output_dir=output,
                    token="token",
                    opener=opener,
                )
            self.assertFalse(output.exists())

    def test_requires_new_output_directory_and_token(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            existing = Path(raw)
            with self.assertRaises(DadataFixtureVerificationError):
                verify_positive_fixture(
                    query="Саратов",
                    fixture_id="FX-DADATA-REGION-POS-001",
                    expected_suggestion="Саратовская обл",
                    expected_components={"region_with_type": "Саратовская обл"},
                    output_dir=existing,
                    token="token",
                    opener=lambda *_args, **_kwargs: _Response(self.payload),
                )
            missing = existing / "missing"
            with self.assertRaisesRegex(
                DadataFixtureVerificationError, "DADATA_API_KEY"
            ):
                verify_positive_fixture(
                    query="Саратов",
                    fixture_id="FX-DADATA-REGION-POS-001",
                    expected_suggestion="Саратовская обл",
                    expected_components={"region_with_type": "Саратовская обл"},
                    output_dir=missing,
                    token="",
                    opener=lambda *_args, **_kwargs: _Response(self.payload),
                )

    def test_supports_allowlisted_fms_multi_suggestion_fixture(self) -> None:
        payload = {
            "suggestions": [
                {
                    "value": "ОВД ЗЮЗИНО Г. МОСКВЫ",
                    "data": {
                        "code": "772-053",
                        "name": "ОВД ЗЮЗИНО Г. МОСКВЫ",
                        "region_code": "77",
                        "type": "2",
                    },
                },
                {
                    "value": "ОВД ЗЮЗИНО ПС УВД ЮЗАО Г. МОСКВЫ",
                    "data": {
                        "code": "772-053",
                        "name": "ОВД ЗЮЗИНО ПС УВД ЮЗАО Г. МОСКВЫ",
                        "region_code": "77",
                        "type": "2",
                    },
                },
            ]
        }
        requests: list[object] = []

        def opener(request: object, timeout: float) -> _Response:
            requests.append((request, timeout))
            return _Response(payload)

        with tempfile.TemporaryDirectory() as raw:
            receipt = verify_positive_fixture(
                query="772-053",
                fixture_id="FX-DADATA-FMS-POS-001",
                expected_suggestion="ОВД ЗЮЗИНО Г. МОСКВЫ",
                expected_components={
                    "code": "772-053",
                    "name": "ОВД ЗЮЗИНО Г. МОСКВЫ",
                    "region_code": "77",
                    "type": "2",
                },
                endpoint=FMS_UNIT_ENDPOINT,
                minimum_suggestion_count=2,
                output_dir=Path(raw) / "fixture",
                token="secret-token",
                opener=opener,
            )

        self.assertEqual(2, len(requests))
        self.assertEqual(FMS_UNIT_ENDPOINT, receipt["request"]["endpoint"])
        self.assertEqual(2, receipt["expected_response"]["minimum_suggestion_count"])
        self.assertTrue(
            receipt["verification"]["all_minimum_suggestion_count_matched"]
        )

    def test_supports_party_fixture_with_nested_status_and_opf(self) -> None:
        payload = {
            "suggestions": [
                {
                    "value": "ПАО СБЕРБАНК",
                    "data": {
                        "inn": "7707083893",
                        "state": {"status": "ACTIVE"},
                        "opf": {"short": "ПАО"},
                    },
                }
            ]
        }

        with tempfile.TemporaryDirectory() as raw:
            receipt = verify_positive_fixture(
                query="7707083893",
                fixture_id="FX-DADATA-PARTY-ACTIVE-001",
                expected_suggestion="ПАО СБЕРБАНК",
                expected_components={
                    "inn": "7707083893",
                    "state.status": "ACTIVE",
                    "opf.short": "ПАО",
                },
                endpoint=PARTY_ENDPOINT,
                output_dir=Path(raw) / "fixture",
                token="secret-token",
                opener=lambda *_args, **_kwargs: _Response(payload),
            )

        self.assertEqual(PARTY_ENDPOINT, receipt["request"]["endpoint"])
        self.assertEqual(
            "ACTIVE",
            receipt["expected_response"]["exact_components"]["state.status"],
        )


if __name__ == "__main__":
    unittest.main()
