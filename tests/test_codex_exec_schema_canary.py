from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.codex_exec_schema_canary import (
    SchemaCanaryError,
    canonical_json_bytes,
    deterministic_transport_instance,
    main,
    schema_keyword_inventory,
    transport_prompt,
)
from scripts.codex_exec_source_assertion_reviewer import SourceReviewerRunnerError
from scripts.openai_strict_output_schema import (
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)
from scripts.review_cycle_backend_dispatcher import ExecCapability
from test_case_agent.review_cycle.exec_backend import (
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
)


class CodexExecSchemaCanaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text("{}\n", encoding="utf-8")
        self.codex_path = self.root / "codex.exe"
        self.codex_path.write_bytes(b"test-codex")
        for relative in (
            "scripts/openai_strict_output_schema.py",
            "scripts/codex_exec_source_assertion_reviewer.py",
            "scripts/codex_exec_schema_canary.py",
            "scripts/review_cycle_backend_dispatcher.py",
            "test_case_agent/review_cycle/exec_backend.py",
            "test_case_agent/review_cycle/exec_events.py",
            "test_case_agent/review_cycle/schema_canary_contract.py",
            "test_case_agent/review_cycle/source_assertions.py",
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {relative}\n", encoding="utf-8")
        self.schema = {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ok"]}},
            "required": ["status"],
            "additionalProperties": False,
        }
        self.capability = ExecCapability(
            command="codex",
            available=True,
            verified=True,
            returncode=0,
            duration_ms=1,
            missing_flags=(),
            version="codex-cli test",
            resolved_command=str(self.codex_path.resolve()),
        )

    def args(self, output_dir: Path) -> list[str]:
        return [
            "--repo-root",
            str(self.root),
            "--manifest",
            str(self.manifest_path),
            "--output-dir",
            str(output_dir),
            "--qualification-id",
            "test-qualification",
            "--codex-command",
            "codex",
        ]

    def common_patches(self):
        return (
            patch(
                "scripts.codex_exec_schema_canary.load_source_assertion_manifest",
                return_value=SimpleNamespace(digest="a" * 64),
            ),
            patch(
                "scripts.codex_exec_schema_canary.receipt_schema",
                return_value=self.schema,
            ),
            patch(
                "scripts.codex_exec_schema_canary.validate_openai_strict_output_schema"
            ),
            patch(
                "scripts.codex_exec_schema_canary.resolve_exec_command",
                return_value=str(self.codex_path),
            ),
            patch(
                "scripts.codex_exec_schema_canary.probe_exec_capability",
                return_value=self.capability,
            ),
            patch(
                "scripts.codex_exec_schema_canary.codex_version",
                return_value="codex-cli test",
            ),
        )

    @staticmethod
    def completed_transport_result(command, kwargs, payload):
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(
            json.dumps(payload, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        Path(kwargs["events_path"]).write_text(
            "\n".join(
                (
                    '{"type":"thread.started"}',
                    '{"type":"turn.started"}',
                    '{"type":"turn.completed","usage":{}}',
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
        return 0, {"input_tokens": 10, "output_tokens": 2}, None

    def test_deterministic_fixture_is_repeatable_and_schema_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["ok", "blocked"]},
                "digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                "reviews": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "valid": {"type": "boolean"},
                        },
                        "required": ["id", "valid"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["status", "digest", "reviews"],
            "additionalProperties": False,
        }

        first = deterministic_transport_instance(schema)
        second = deterministic_transport_instance(schema)

        self.assertEqual(
            {
                "status": "ok",
                "digest": "0" * 64,
                "reviews": [
                    {"id": "transport-canary", "valid": False},
                    {"id": "transport-canary", "valid": False},
                ],
            },
            first,
        )
        self.assertEqual(first, second)
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))
        validate_openai_strict_output_schema(schema)
        validate_openai_strict_output_instance(first, schema)
        self.assertEqual(transport_prompt(first), transport_prompt(second))

    def test_schema_valid_but_non_exact_model_output_is_terminal_failure(self) -> None:
        output_dir = self.root / "non-exact-canary"
        self.schema["properties"]["status"]["enum"] = ["ok", "different"]

        def fake_run(command, **kwargs):
            return self.completed_transport_result(
                command,
                kwargs,
                {"status": "different"},
            )

        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            side_effect=fake_run,
        ) as run:
            self.assertEqual(2, main(self.args(output_dir)))

        run.assert_called_once()
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        terminal = json.loads(
            (output_dir / "qualification-terminal.json").read_text(encoding="utf-8")
        )
        self.assertEqual("failed", summary["status"])
        self.assertFalse(summary["qualification_passed"])
        self.assertIn("schema-valid but differs", summary["error"])
        self.assertEqual(1, summary["max_attempts"])
        self.assertEqual(0, summary["retry_count"])
        self.assertFalse(summary["retry_performed"])
        self.assertEqual(1, summary["model_call_invocation_count"])
        self.assertEqual(1, summary["model_session_count"])
        self.assertEqual("failed", terminal["status"])
        self.assertFalse(terminal["qualification_passed"])
        self.assertEqual(1, terminal["attempt_count"])
        self.assertEqual(1, terminal["max_attempts"])
        self.assertEqual(0, terminal["retry_count"])
        self.assertFalse(terminal["retry_performed"])
        self.assertEqual(
            hashlib.sha256(
                (output_dir / "canary-summary.json").read_bytes()
            ).hexdigest(),
            terminal["summary_sha256"],
        )

    def test_expected_fixture_mismatch_fails_preflight_without_reservation(self) -> None:
        output_dir = self.root / "preflight-failure"
        expected_path = self.root / "wrong-expected-instance.json"
        expected_path.write_text('{"status":"different"}\n', encoding="utf-8")
        args = [
            *self.args(output_dir),
            "--expected-instance",
            str(expected_path),
        ]
        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec"
        ) as run:
            with self.assertRaisesRegex(
                SchemaCanaryError,
                "provided expected transport fixture differs",
            ):
                main(args)

        run.assert_not_called()
        reservation = (
            self.root
            / "evals/schema-canary/qualification-registry"
            / "test-qualification.reserved.json"
        )
        self.assertFalse(reservation.exists())
        self.assertFalse(output_dir.exists())

    def test_success_after_latency_target_is_qualified_but_classified_slow(self) -> None:
        output_dir = self.root / "slow-canary"
        args = [
            *self.args(output_dir),
            "--timeout-seconds",
            "900",
            "--latency-target-seconds",
            "300",
        ]

        def fake_run(command, **kwargs):
            return self.completed_transport_result(command, kwargs, {"status": "ok"})

        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            side_effect=fake_run,
        ) as run, patch(
            "scripts.codex_exec_schema_canary.time.monotonic",
            side_effect=(100.0, 401.001),
        ):
            self.assertEqual(0, main(args))

        run.assert_called_once()
        self.assertEqual(900, run.call_args.kwargs["timeout_seconds"])
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        terminal = json.loads(
            (output_dir / "qualification-terminal.json").read_text(encoding="utf-8")
        )
        self.assertEqual("passed", summary["status"])
        self.assertTrue(summary["qualification_passed"])
        self.assertEqual(1, summary["max_attempts"])
        self.assertEqual(0, summary["retry_count"])
        self.assertFalse(summary["retry_performed"])
        self.assertGreater(summary["duration_ms"], 300_000)
        self.assertEqual("slow", summary["latency_class"])
        self.assertTrue(summary["latency_slo_breach"])
        self.assertEqual(900, summary["timeout_seconds"])
        self.assertEqual("qualified", terminal["status"])
        self.assertTrue(terminal["qualification_passed"])
        self.assertEqual(1, terminal["max_attempts"])
        self.assertEqual(0, terminal["retry_count"])
        self.assertFalse(terminal["retry_performed"])
        self.assertEqual("slow", terminal["latency_class"])
        self.assertTrue(terminal["latency_slo_breach"])

    def test_timeout_writes_terminal_metadata_and_reservation_blocks_retry(self) -> None:
        output_dir = self.root / "timeout-canary"
        args = [*self.args(output_dir), "--timeout-seconds", "900"]
        runtime_metadata = {
            "timeout_seconds": 900,
            "process_id": 4242,
            "timeout_triggered": True,
            "termination_required": True,
            "termination_method": "taskkill-tree",
            "termination_return_code": 0,
            "termination_error": None,
            "process_final_return_code": 1,
        }

        def fake_timeout(_command, **kwargs):
            Path(kwargs["events_path"]).write_text(
                '{"type":"thread.started"}\n{"type":"turn.started"}\n',
                encoding="utf-8",
            )
            Path(kwargs["stderr_path"]).write_text(
                "simulated timeout\n",
                encoding="utf-8",
            )
            kwargs["runtime_metadata"].update(runtime_metadata)
            raise SourceReviewerRunnerError("source reviewer timed out after 900s")

        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            side_effect=fake_timeout,
        ) as run:
            self.assertEqual(2, main(args))
            with self.assertRaisesRegex(SchemaCanaryError, "already attempted"):
                main(self.args(self.root / "retry-after-timeout"))

        run.assert_called_once()
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        terminal = json.loads(
            (output_dir / "qualification-terminal.json").read_text(encoding="utf-8")
        )
        reservation = json.loads(
            (
                self.root
                / "evals/schema-canary/qualification-registry"
                / "test-qualification.reserved.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual("failed", summary["status"])
        self.assertFalse(summary["qualification_passed"])
        self.assertEqual(1, summary["attempt_count"])
        self.assertEqual(1, summary["max_attempts"])
        self.assertEqual(0, summary["retry_count"])
        self.assertFalse(summary["retry_performed"])
        self.assertEqual(1, summary["model_call_invocation_count"])
        self.assertEqual(1, summary["model_session_count"])
        self.assertEqual(900, summary["timeout_seconds"])
        self.assertEqual(runtime_metadata, summary["runtime_metadata"])
        self.assertEqual("failed", terminal["status"])
        self.assertFalse(terminal["qualification_passed"])
        self.assertEqual(1, terminal["attempt_count"])
        self.assertEqual(1, terminal["max_attempts"])
        self.assertEqual(0, terminal["retry_count"])
        self.assertFalse(terminal["retry_performed"])
        self.assertEqual(1, terminal["model_call_invocation_count"])
        self.assertEqual(1, terminal["model_session_count"])
        self.assertEqual(runtime_metadata, terminal["runtime_metadata"])
        self.assertEqual("reserved", reservation["status"])
        self.assertEqual("test-qualification", reservation["qualification_id"])

    def test_passed_canary_records_exactly_one_nonsemantic_session(self) -> None:
        output_dir = self.root / "canary"

        def fake_run(command, **kwargs):
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text('{"status":"ok"}\n', encoding="utf-8")
            Path(kwargs["events_path"]).write_text(
                "\n".join(
                    (
                        '{"type":"thread.started"}',
                        '{"type":"turn.started"}',
                        '{"type":"turn.completed","usage":{}}',
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
            return 0, {"input_tokens": 10, "output_tokens": 2}, None

        patches = self.common_patches()
        with patches[0], patches[1], patches[2] as lint, patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            side_effect=fake_run,
        ) as run:
            self.assertEqual(0, main(self.args(output_dir)))

        lint.assert_called_once_with(self.schema)
        run.assert_called_once()
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual("passed", summary["status"])
        self.assertEqual(1, summary["attempt_count"])
        self.assertEqual(1, summary["model_call_invocation_count"])
        self.assertEqual(1, summary["model_session_count"])
        self.assertFalse(summary["semantic_review_performed"])
        self.assertFalse(summary["admissible_as_source_review"])
        self.assertEqual("test-qualification", summary["qualification_id"])
        self.assertEqual("codex-cli test", summary["codex_version"])
        self.assertEqual(
            "codex-exec-deterministic-exact-echo-pinned-v3",
            summary["runtime_profile"],
        )
        self.assertEqual(str(self.codex_path.resolve()), summary["codex_executable"])
        self.assertEqual(
            str(self.codex_path.resolve()),
            summary["backend_capability"]["selected_executable"],
        )
        self.assertEqual(
            list(MODEL_TOOL_ISOLATION_DISABLE_FEATURES),
            summary["backend_capability"]["disable_features"],
        )
        self.assertTrue(summary["transport_instance_schema_validated"])
        self.assertEqual(
            summary["untrusted_transport_instance_sha256"],
            hashlib.sha256(
                (output_dir / "untrusted-transport-instance.json").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            summary["stderr_sha256"],
            hashlib.sha256(b"").hexdigest(),
        )

    def test_failed_model_call_is_terminal_and_not_retried(self) -> None:
        output_dir = self.root / "failed-canary"
        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            return_value=(1, {}, None),
        ) as run:
            self.assertEqual(2, main(self.args(output_dir)))

        run.assert_called_once()
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual("failed", summary["status"])
        self.assertEqual(1, summary["attempt_count"])
        self.assertEqual(1, summary["model_call_invocation_count"])
        self.assertEqual(0, summary["model_session_count"])

    def test_image_generation_event_is_terminal_failure(self) -> None:
        output_dir = self.root / "image-generation-canary"

        def fake_run(command, **kwargs):
            return self.completed_transport_result(command, kwargs, {"status": "ok"})[:2] + (
                "image_generation",
            )

        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            side_effect=fake_run,
        ) as run:
            self.assertEqual(2, main(self.args(output_dir)))

        run.assert_called_once()
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual("failed", summary["status"])
        self.assertIn("forbidden tool event: image_generation", summary["error"])

    def test_exit_zero_with_schema_invalid_object_is_not_a_pass(self) -> None:
        output_dir = self.root / "invalid-instance-canary"

        def fake_run(command, **kwargs):
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text("{}\n", encoding="utf-8")
            Path(kwargs["events_path"]).write_text(
                "\n".join(
                    (
                        '{"type":"thread.started"}',
                        '{"type":"turn.started"}',
                        '{"type":"turn.completed","usage":{}}',
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
            return 0, {}, None

        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            side_effect=fake_run,
        ) as run:
            self.assertEqual(2, main(self.args(output_dir)))

        run.assert_called_once()
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual("failed", summary["status"])
        self.assertEqual(1, summary["model_session_count"])
        self.assertIn("does not satisfy exact output schema", summary["error"])

    def test_event_after_turn_completed_is_not_a_pass(self) -> None:
        output_dir = self.root / "late-event-canary"

        def fake_run(command, **kwargs):
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text('{"status":"ok"}\n', encoding="utf-8")
            Path(kwargs["events_path"]).write_text(
                "\n".join(
                    (
                        '{"type":"thread.started"}',
                        '{"type":"turn.started"}',
                        '{"type":"turn.completed","usage":{}}',
                        '{"type":"item.completed","item":{"type":"agent_message"}}',
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            Path(kwargs["stderr_path"]).write_text("", encoding="utf-8")
            return 0, {}, None

        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patch(
            "scripts.codex_exec_schema_canary.run_exec",
            side_effect=fake_run,
        ) as run:
            self.assertEqual(2, main(self.args(output_dir)))

        run.assert_called_once()
        summary = json.loads(
            (output_dir / "canary-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual("failed", summary["status"])
        self.assertIn("lifecycle order/boundary", summary["error"])

    def test_existing_output_directory_blocks_before_model_call(self) -> None:
        output_dir = self.root / "existing"
        output_dir.mkdir()
        with self.assertRaisesRegex(SchemaCanaryError, "retries and overwrites"):
            main(self.args(output_dir))

    def test_qualification_id_cannot_be_retried_in_another_directory(self) -> None:
        registry = self.root / "evals" / "schema-canary" / "qualification-registry"
        registry.mkdir(parents=True)
        (registry / "test-qualification.reserved.json").write_text(
            '{"status":"reserved"}\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(SchemaCanaryError, "already attempted"):
            main(self.args(self.root / "different-output"))
        self.assertFalse((self.root / "different-output").exists())

    def test_keyword_inventory_reports_schema_keywords(self) -> None:
        self.assertEqual(
            {
                "additionalProperties": 1,
                "enum": 1,
                "properties": 1,
                "required": 1,
                "type": 2,
            },
            schema_keyword_inventory(self.schema),
        )


if __name__ == "__main__":
    unittest.main()
