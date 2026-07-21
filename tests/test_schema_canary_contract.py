from __future__ import annotations

import unittest

from scripts.codex_exec_schema_canary import CANARY_VERSION
from test_case_agent.review_cycle.schema_canary_contract import (
    SCHEMA_CANARY_SUMMARY_VERSION,
    SchemaCanarySummaryContractError,
    validate_schema_canary_summary,
)


class SchemaCanarySummaryContractTests(unittest.TestCase):
    def test_producer_public_alias_uses_the_canonical_version(self) -> None:
        self.assertEqual(SCHEMA_CANARY_SUMMARY_VERSION, CANARY_VERSION)

    qualification_id = "h65-source-review-v6"
    manifest_digest = "a" * 64
    manifest_sha256 = "b" * 64
    schema_sha256 = "c" * 64

    def valid_summary(self) -> dict[str, object]:
        return {
            "version": SCHEMA_CANARY_SUMMARY_VERSION,
            "status": "passed",
            "qualification_passed": True,
            "attempt_count": 1,
            "max_attempts": 1,
            "model_session_count": 1,
            "model_call_invocation_count": 1,
            "retry_count": 0,
            "retry_performed": False,
            "semantic_review_performed": False,
            "admissible_as_source_review": False,
            "qualification_id": self.qualification_id,
            "manifest_digest": self.manifest_digest,
            "manifest_sha256": self.manifest_sha256,
            "schema_sha256": self.schema_sha256,
            "producer_specific_diagnostic": {"preserved": True},
        }

    def validate(self, summary: object) -> None:
        validate_schema_canary_summary(
            summary,  # type: ignore[arg-type]
            expected_qualification_id=self.qualification_id,
            expected_manifest_digest=self.manifest_digest,
            expected_manifest_sha256=self.manifest_sha256,
            expected_schema_sha256=self.schema_sha256,
        )

    def test_accepts_v2_success_with_optional_documented_latency_classes(self) -> None:
        summaries = [self.valid_summary()]
        for latency_class in ("within-target", "slow"):
            summary = self.valid_summary()
            summary["latency_class"] = latency_class
            summaries.append(summary)

        for summary in summaries:
            with self.subTest(latency_class=summary.get("latency_class")):
                self.validate(summary)

    def test_rejects_missing_v1_v3_and_type_confused_version(self) -> None:
        cases = (
            ("missing", None),
            ("v1", 1),
            ("v3", 3),
            ("string", "2"),
            ("boolean", True),
        )
        for label, value in cases:
            summary = self.valid_summary()
            if value is None:
                del summary["version"]
            else:
                summary["version"] = value
            with self.subTest(label=label), self.assertRaisesRegex(
                SchemaCanarySummaryContractError,
                r"version (missing|mismatch|type mismatch)",
            ):
                self.validate(summary)

    def test_rejects_missing_or_type_confused_common_fields(self) -> None:
        cases = (
            ("attempt_count", None),
            ("attempt_count", True),
            ("qualification_passed", 1),
            ("retry_performed", 0),
            ("semantic_review_performed", 0),
            ("manifest_sha256", 7),
        )
        for field_name, value in cases:
            summary = self.valid_summary()
            if value is None:
                del summary[field_name]
            else:
                summary[field_name] = value
            with self.subTest(field_name=field_name, value=value), self.assertRaisesRegex(
                SchemaCanarySummaryContractError,
                field_name + r" (missing|type mismatch)",
            ):
                self.validate(summary)

    def test_rejects_non_success_attempt_and_retry_values(self) -> None:
        cases = (
            ("status", "failed"),
            ("qualification_passed", False),
            ("attempt_count", 2),
            ("max_attempts", 2),
            ("model_session_count", 0),
            ("model_call_invocation_count", 2),
            ("retry_count", 1),
            ("retry_performed", True),
            ("semantic_review_performed", True),
            ("admissible_as_source_review", True),
        )
        for field_name, value in cases:
            summary = self.valid_summary()
            summary[field_name] = value
            with self.subTest(field_name=field_name, value=value), self.assertRaisesRegex(
                SchemaCanarySummaryContractError,
                field_name + r" mismatch",
            ):
                self.validate(summary)

    def test_rejects_each_exact_binding_mismatch(self) -> None:
        for field_name in (
            "qualification_id",
            "manifest_digest",
            "manifest_sha256",
            "schema_sha256",
        ):
            summary = self.valid_summary()
            summary[field_name] = "different"
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                SchemaCanarySummaryContractError,
                field_name + r" mismatch",
            ):
                self.validate(summary)

    def test_rejects_unknown_or_type_confused_latency_class(self) -> None:
        for value in ("fast", "within_target", 1, True):
            summary = self.valid_summary()
            summary["latency_class"] = value
            with self.subTest(value=value), self.assertRaisesRegex(
                SchemaCanarySummaryContractError,
                r"latency_class (mismatch|type mismatch)",
            ):
                self.validate(summary)

    def test_rejects_non_object_payload_with_actionable_message(self) -> None:
        with self.assertRaisesRegex(
            SchemaCanarySummaryContractError,
            r"must be a JSON object; got list",
        ):
            self.validate([])


if __name__ == "__main__":
    unittest.main()
