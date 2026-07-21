from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.stage_failure_contract import (
    SCHEMA_VERSION,
    StageFailureAlreadyExistsError,
    StageFailureContractError,
    StageFailureEnvelope,
    StageFailureReadError,
    StageFailureWriteError,
    find_first_failed_stage,
    read_stage_failure,
    write_stage_failure_exclusive,
)


def valid_payload() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": "compile-ready",
        "return_code": 2,
        "error_type": "WorkflowUpdateError",
        "error": "  Точная ошибка\nс кавычками: \"значение\"  ",
        "source": "h65/run_benchmark_once.py",
    }


class StageFailureContractTests(unittest.TestCase):
    def test_round_trip_preserves_exact_error_and_fields(self) -> None:
        failure = StageFailureEnvelope.create(
            stage="compile-ready",
            return_code=2,
            error_type="WorkflowUpdateError",
            error="  Точная ошибка\nс кавычками: \"значение\"  ",
            source="h65/run_benchmark_once.py",
        )
        self.assertEqual(valid_payload(), failure.to_dict())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stage-failure.json"
            write_stage_failure_exclusive(path, failure)
            loaded = read_stage_failure(path)

        self.assertEqual(failure, loaded)
        self.assertEqual(failure.error, loaded.error)

    def test_strict_validation_rejects_missing_unknown_version_and_invalid_values(self) -> None:
        cases: list[tuple[str, dict[str, object], str]] = []
        missing = valid_payload()
        missing.pop("error")
        cases.append(("missing", missing, "missing=error"))
        unknown = valid_payload()
        unknown["details"] = "not allowed"
        cases.append(("unknown", unknown, "unknown=details"))
        wrong_version = valid_payload()
        wrong_version["schema_version"] = SCHEMA_VERSION + 1
        cases.append(("version", wrong_version, "unsupported stage failure schema_version"))
        boolean_code = valid_payload()
        boolean_code["return_code"] = True
        cases.append(("boolean return code", boolean_code, "return_code must be an integer"))
        success_code = valid_payload()
        success_code["return_code"] = 0
        cases.append(("success return code", success_code, "must be nonzero"))
        blank_stage = valid_payload()
        blank_stage["stage"] = "  "
        cases.append(("blank stage", blank_stage, "stage must be a non-empty string"))
        non_string_error = valid_payload()
        non_string_error["error"] = {"message": "changed shape"}
        cases.append(("error shape", non_string_error, "error must be a string"))

        for label, payload, message in cases:
            with self.subTest(label=label), self.assertRaisesRegex(
                StageFailureContractError, message
            ):
                StageFailureEnvelope.from_dict(payload)

    def test_read_rejects_missing_malformed_and_non_object_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.json"
            with self.assertRaisesRegex(StageFailureReadError, "does not exist"):
                read_stage_failure(missing)

            malformed = root / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(StageFailureReadError, "cannot read"):
                read_stage_failure(malformed)

            array = root / "array.json"
            array.write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(StageFailureContractError, "must be a JSON object"):
                read_stage_failure(array)

    def test_exclusive_write_never_replaces_existing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "stage-failure.json"
            first = StageFailureEnvelope.from_dict(valid_payload())
            write_stage_failure_exclusive(path, first)
            original = path.read_bytes()

            replacement_payload = valid_payload()
            replacement_payload["error"] = "replacement must not win"
            replacement = StageFailureEnvelope.from_dict(replacement_payload)
            with self.assertRaisesRegex(
                StageFailureAlreadyExistsError, "already exists"
            ):
                write_stage_failure_exclusive(path, replacement)

            self.assertEqual(original, path.read_bytes())
            self.assertEqual([], list(root.glob("*.stage-failure-tmp")))
            self.assertEqual([], list(root.glob(".*.stage-failure-tmp")))

    def test_write_requires_existing_parent_and_does_not_create_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "absent"
            with self.assertRaisesRegex(StageFailureWriteError, "does not exist"):
                write_stage_failure_exclusive(
                    parent / "stage-failure.json",
                    StageFailureEnvelope.from_dict(valid_payload()),
                )
            self.assertFalse(parent.exists())

    def test_first_failed_stage_uses_finished_event_order(self) -> None:
        events = [
            {"event": "stage-started", "stage": "compile-ready"},
            {"event": "stage-finished", "stage": "source-reviewer", "return_code": 0},
            {"event": "stage-finished", "stage": "compile-ready", "return_code": 2},
            {"event": "stage-started", "stage": "prepared-compiler"},
            {"event": "orchestration-exception", "error_type": "RuntimeError"},
            {"event": "stage-finished", "stage": "prepared-compiler", "return_code": 1},
        ]

        failed = find_first_failed_stage(events)

        self.assertIsNotNone(failed)
        assert failed is not None
        self.assertEqual("compile-ready", failed.stage)
        self.assertEqual(2, failed.return_code)
        self.assertEqual(2, failed.event_index)

    def test_first_failed_stage_returns_none_without_nonzero_finished_event(self) -> None:
        self.assertIsNone(
            find_first_failed_stage(
                [
                    {"event": "stage-started", "stage": "prepared-compiler"},
                    {
                        "event": "stage-finished",
                        "stage": "source-reviewer",
                        "return_code": 0,
                    },
                ]
            )
        )

    def test_first_failed_stage_rejects_malformed_finished_event(self) -> None:
        with self.assertRaisesRegex(
            StageFailureContractError, r"events\[0\]\.return_code must be an integer"
        ):
            find_first_failed_stage(
                [
                    {
                        "event": "stage-finished",
                        "stage": "compile-ready",
                        "return_code": "2",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
