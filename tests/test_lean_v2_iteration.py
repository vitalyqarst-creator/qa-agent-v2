from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping
from unittest.mock import patch

from test_case_agent.lean_v2 import LeanV2ContractError, run_lean_v2_iteration
from test_case_agent.lean_v2.backend import (
    CodexExecStageBackend,
    LeanV2BackendError,
    StageResult,
)
from test_case_agent.lean_v2.engine import _reviewer_schema, _writer_schema
from scripts.openai_strict_output_schema import validate_openai_strict_output_schema
from scripts.resolve_instruction_context import resolve_instruction_context


class FixtureStageBackend:
    def __init__(
        self,
        *,
        unresolved: bool = False,
        trace_leak: bool = False,
        unexpected_writer_fields: bool = False,
        wrong_review_tc_id: bool = False,
        mutate_source: Path | None = None,
    ) -> None:
        self.calls: list[str] = []
        self.unresolved = unresolved
        self.trace_leak = trace_leak
        self.unexpected_writer_fields = unexpected_writer_fields
        self.wrong_review_tc_id = wrong_review_tc_id
        self.mutate_source = mutate_source

    @staticmethod
    def _request(prompt: str) -> dict[str, Any]:
        return json.loads(prompt.split("REQUEST JSON:\n", 1)[1])

    def run_stage(
        self,
        *,
        stage: str,
        prompt: str,
        schema: Mapping[str, Any],
        artifact_dir: Path,
    ) -> StageResult:
        del schema, artifact_dir
        self.calls.append(stage)
        request = self._request(prompt)
        if stage == "writer":
            card = request["cards"][0]
            if self.unresolved:
                payload = {
                    "schema_version": 1,
                    "packet_sha256": request["packet_sha256"],
                    "intents": [],
                    "unresolved_cards": [
                        {"card_id": card["card_id"], "reason": "Не хватает точного oracle."}
                    ],
                }
            else:
                title = "Ввод ИНН BSR 116" if self.trace_leak else "Ввод ИНН организации"
                payload = {
                    "schema_version": 1,
                    "packet_sha256": request["packet_sha256"],
                    "intents": [
                        {
                            "card_id": card["card_id"],
                            "title": title,
                            "type": "позитивный",
                            "test_data": ["ИНН: `7707083893`."],
                            "steps": ["Ввести `7707083893` в поле «ИНН»."],
                            "expected_result": "В поле «ИНН» отображается значение `7707083893`.",
                            **(
                                {"postconditions": ["Сохранить изменения."]}
                                if self.unexpected_writer_fields
                                else {}
                            ),
                        }
                    ],
                    "unresolved_cards": [],
                }
        else:
            test_case_by_card = {
                card_id: intent["test_case_id"]
                for intent in request["test_intents"]
                for card_id in intent["card_ids"]
            }
            payload = {
                "schema_version": 1,
                "decision": "accepted",
                "draft_sha256": request["draft_sha256"],
                "card_results": [
                    {
                        "card_id": card["card_id"],
                        "status": "covered",
                        "test_case_ids": [
                            "TC-WRONG-999"
                            if self.wrong_review_tc_id
                            else test_case_by_card[card["card_id"]]
                        ],
                        "comment": "Карточка покрыта одним исполнимым кейсом.",
                    }
                    for card in request["evidence_cards"]
                ],
                "findings": [],
                "summary": "Покрытие полное, blocking findings отсутствуют.",
            }
            if self.mutate_source is not None:
                self.mutate_source.write_bytes(b"changed-during-review")
        return StageResult(
            payload=payload,
            receipt={
                "stage": stage,
                "backend": "test-fixture",
                "attempts": 1,
                "duration_ms": 1,
                "tokens": "unavailable",
                "tool_event_count": 0,
                "timeout_seconds": None,
            },
        )


class LeanV2IterationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "source").mkdir()
        (self.root / "source" / "requirements.docx").write_bytes(b"docx-fixture")
        (self.root / "source" / "requirements.xhtml").write_text(
            "<html><body>fixture</body></html>", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _packet(self, obligations: list[dict[str, Any]]) -> Path:
        packet = {
            "schema_version": 1,
            "ft_slug": "synthetic-ft",
            "scope_slug": "employment-main-work",
            "section_id": "4.2",
            "package_id": "WP-01",
            "tc_prefix": "EMP",
            "base_preconditions": ["Открыть карточку заявки и блок сведений о работе."],
            "source_files": [
                {
                    "role": "docx",
                    "path": "source/requirements.docx",
                    "sha256": self._sha(self.root / "source" / "requirements.docx"),
                },
                {
                    "role": "xhtml",
                    "path": "source/requirements.xhtml",
                    "sha256": self._sha(self.root / "source" / "requirements.xhtml"),
                },
            ],
            "dictionaries": [
                {
                    "dictionary_id": "DICT-001",
                    "closed": True,
                    "values": ["Работа по найму", "ИП"],
                }
            ],
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "field_or_action": "Социальный статус",
                    "source_ref": "requirements.xhtml /table[1]/tr[1]",
                    "source_locator": "/table[1]/tr[1]",
                    "bounded_source_text": "Поле Социальный статус отображается в блоке.",
                    "requirement_codes": ["BSR 116"],
                    "obligations": obligations,
                }
            ],
        }
        path = self.root / "source-packet.json"
        path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
        return path

    def test_deterministic_only_route_skips_writer_and_accepts_shadow(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "visibility",
                    "priority": "высокий",
                    "inputs": {},
                },
                {
                    "obligation_id": "OBL-002",
                    "atom_id": "ATOM-002",
                    "template": "dictionary",
                    "priority": "высокий",
                    "inputs": {"dictionary_id": "DICT-001"},
                },
            ]
        )
        backend = FixtureStageBackend()

        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-1",
            backend=backend,
        )

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual(["reviewer"], backend.calls)
        self.assertEqual(2, result.test_case_count)
        draft = result.draft_path.read_text(encoding="utf-8")
        self.assertIn("TC-EMP-001", draft)
        self.assertIn("DICT-001", draft)
        gate = json.loads((self.root / "run-1" / "production-gate.json").read_text(encoding="utf-8"))
        self.assertTrue(gate["passed"], gate["findings"])
        access = json.loads(
            (self.root / "run-1" / "evidence-access-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(access["old_test_cases_in_context"])
        self.assertFalse(access["benchmark_context_in_context"])
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        writer_receipt = next(item for item in summary["model_stages"] if item["stage"] == "writer")
        self.assertEqual(0, writer_receipt["attempts"])
        self.assertEqual("unavailable", writer_receipt["tokens"])
        timing = summary["timing"]
        self.assertEqual(
            timing["total_wall_ms"],
            timing["phase_sum_ms"] + timing["unattributed_interphase_ms"],
        )

    def test_all_deterministic_template_families_pass_the_runtime_gate(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "default",
                    "priority": "средний",
                    "inputs": {"value": "Работа по найму"},
                },
                {
                    "obligation_id": "OBL-002",
                    "atom_id": "ATOM-002",
                    "template": "editability",
                    "priority": "средний",
                    "inputs": {
                        "initial_value": "Работа по найму",
                        "new_value": "ИП",
                    },
                },
                {
                    "obligation_id": "OBL-003",
                    "atom_id": "ATOM-003",
                    "template": "positive-input",
                    "priority": "средний",
                    "inputs": {"value": "ИП"},
                },
                {
                    "obligation_id": "OBL-004",
                    "atom_id": "ATOM-004",
                    "template": "calibration-negative",
                    "priority": "средний",
                    "inputs": {
                        "invalid_value": "###",
                        "missing_oracle_question": (
                            "Как интерфейс отклоняет значение `###` в поле "
                            "«Социальный статус»?"
                        ),
                    },
                },
                {
                    "obligation_id": "OBL-005",
                    "atom_id": "ATOM-005",
                    "template": "behavior",
                    "priority": "средний",
                    "inputs": {
                        "title": "Выбор социального статуса",
                        "type": "позитивный",
                        "test_data": ["Социальный статус: `ИП`."],
                        "steps": ["Выбрать `ИП` в поле «Социальный статус»."],
                        "expected_result": (
                            "В поле «Социальный статус» отображается значение `ИП`."
                        ),
                    },
                },
                {
                    "obligation_id": "OBL-006",
                    "atom_id": "ATOM-006",
                    "template": "optionalness",
                    "priority": "средний",
                    "inputs": {
                        "trigger_step": "Нажать кнопку «Продолжить».",
                        "missing_oracle_question": (
                            "Какой экран подтверждает успешное продолжение с пустым "
                            "необязательным полем «Социальный статус»?"
                        ),
                    },
                },
            ]
        )
        backend = FixtureStageBackend()

        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-all-templates",
            backend=backend,
        )

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual(["reviewer"], backend.calls)
        self.assertEqual(6, result.test_case_count)
        gate = json.loads(
            (self.root / "run-all-templates" / "production-gate.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(gate["passed"], gate["findings"])
        self.assertEqual(2, gate["calibration_candidate_count"])

    def test_complex_card_uses_one_writer_and_one_reviewer(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "complex",
                    "priority": "высокий",
                    "inputs": {
                        "writer_context": "Проверить ввод конкретного валидного ИНН организации."
                    },
                }
            ]
        )
        backend = FixtureStageBackend()

        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-2",
            backend=backend,
        )

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual(["writer", "reviewer"], backend.calls)
        draft = result.draft_path.read_text(encoding="utf-8")
        self.assertIn("`7707083893`", draft)
        self.assertIn("Открыть карточку заявки и блок сведений о работе.", draft)
        self.assertIn("### Постусловия\n\nНе требуются.", draft)

    def test_writer_cannot_override_runner_owned_lifecycle_fields(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "complex",
                    "priority": "высокий",
                    "inputs": {"writer_context": "Проверка ИНН."},
                }
            ]
        )

        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-writer-lifecycle-ownership",
            backend=FixtureStageBackend(unexpected_writer_fields=True),
        )

        self.assertEqual("blocked-contract", result.status)
        diagnostic = json.loads(
            (
                self.root
                / "run-writer-lifecycle-ownership"
                / "failure-diagnostic.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("runner-owned", diagnostic["error"])

    def test_unresolved_writer_card_stops_before_reviewer(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "complex",
                    "priority": "высокий",
                    "inputs": {"writer_context": "Неоднозначное поведение."},
                }
            ]
        )
        backend = FixtureStageBackend(unresolved=True)

        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-3",
            backend=backend,
        )

        self.assertEqual("blocked-writer-unresolved", result.status)
        self.assertEqual(["writer"], backend.calls)
        self.assertFalse((self.root / "run-3" / "reviewer-request.json").exists())

    def test_requiredness_without_oracle_remains_in_common_shadow_suite(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "requiredness",
                    "priority": "высокий",
                    "inputs": {
                        "trigger_step": "Нажать кнопку «Продолжить».",
                        "missing_oracle_question": (
                            "Как интерфейс показывает обязательность пустого поля "
                            "«Социальный статус»?"
                        ),
                    },
                }
            ]
        )
        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-4",
            backend=FixtureStageBackend(),
        )

        self.assertEqual("accepted-shadow", result.status)
        gate = json.loads((self.root / "run-4" / "production-gate.json").read_text(encoding="utf-8"))
        self.assertEqual(1, gate["calibration_candidate_count"])
        self.assertEqual("ft-first-reviewed-with-calibration-pending", gate["suite_readiness"])
        review_request = json.loads(
            (self.root / "run-4" / "reviewer-request.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(
            review_request["review_contract"]["calibration_candidates_allowed"]
        )
        self.assertEqual(
            "ft-first-reviewed-with-calibration-pending",
            review_request["review_contract"]["suite_readiness"],
        )
        self.assertIn(
            "Do not invent an exact UI oracle",
            review_request["review_contract"]["calibration_candidate_acceptance"],
        )

    def test_accepted_shadow_does_not_modify_existing_canonical(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "visibility",
                    "priority": "средний",
                    "inputs": {},
                }
            ]
        )
        canonical = self.root / "test-cases" / "4.2-employment-main-work.md"
        canonical.parent.mkdir()
        canonical.write_text("previous canonical\n", encoding="utf-8")

        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-5",
            backend=FixtureStageBackend(),
        )

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual("previous canonical\n", canonical.read_text(encoding="utf-8"))
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual(
            "disabled-until-compiler-v3-integration",
            summary["canonical_publication"],
        )

    def test_writer_cannot_own_traceability(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "complex",
                    "priority": "высокий",
                    "inputs": {"writer_context": "Проверка ИНН."},
                }
            ]
        )
        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-6",
            backend=FixtureStageBackend(trace_leak=True),
        )

        self.assertEqual("blocked-contract", result.status)
        self.assertFalse((self.root / "run-6" / "reviewer-request.json").exists())

    def test_reviewer_must_reference_the_actual_runner_assigned_tc(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "visibility",
                    "priority": "средний",
                    "inputs": {},
                }
            ]
        )
        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-review-binding",
            backend=FixtureStageBackend(wrong_review_tc_id=True),
        )

        self.assertEqual("blocked-contract", result.status)
        diagnostic = json.loads(
            (self.root / "run-review-binding" / "failure-diagnostic.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("actual test case", diagnostic["error"])

    def test_source_hash_drift_during_review_is_terminal_and_summarized(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "visibility",
                    "priority": "средний",
                    "inputs": {},
                }
            ]
        )
        source = self.root / "source" / "requirements.xhtml"
        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-source-drift",
            backend=FixtureStageBackend(mutate_source=source),
        )

        self.assertEqual("blocked-source-drift", result.status)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual("blocked-source-drift", summary["status"])
        self.assertIn("registered source changed", summary["error"])

    def test_output_directory_is_immutable(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "visibility",
                    "priority": "средний",
                    "inputs": {},
                }
            ]
        )
        output_dir = self.root / "run-immutable"
        first = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=output_dir,
            backend=FixtureStageBackend(),
        )
        self.assertEqual("accepted-shadow", first.status)

        with self.assertRaisesRegex(LeanV2ContractError, "fresh and empty"):
            run_lean_v2_iteration(
                repo_root=self.root,
                source_packet=packet,
                output_dir=output_dir,
                backend=FixtureStageBackend(),
            )

    def test_instruction_loading_is_conditional(self) -> None:
        lean = resolve_instruction_context(root=Path.cwd(), scenario_id="iteration.lean_v2")
        full = resolve_instruction_context(root=Path.cwd(), scenario_id="iteration.full_loop")
        lean_paths = {item["path"] for item in lean["files"]}
        full_paths = {item["path"] for item in full["files"]}

        self.assertIn("references/agent/lean-v2-iteration.md", lean_paths)
        self.assertNotIn("references/agent/lean-v2-iteration.md", full_paths)
        self.assertEqual("pass", lean["budget"]["status"])

    def test_live_stage_schemas_use_the_project_strict_subset(self) -> None:
        validate_openai_strict_output_schema(
            _writer_schema(["CARD-001"], "a" * 64)
        )
        validate_openai_strict_output_schema(
            _reviewer_schema(["CARD-001"], "b" * 64)
        )

    def test_codex_backend_uses_fresh_tool_free_structured_call_without_default_timeout(self) -> None:
        artifact_dir = self.root / "backend-artifacts"
        schema = _writer_schema(["CARD-001"], "a" * 64)
        payload = {
            "schema_version": 1,
            "packet_sha256": "a" * 64,
            "intents": [],
            "unresolved_cards": [{"card_id": "CARD-001", "reason": "Нет oracle."}],
        }
        resolution = SimpleNamespace(
            verified=True,
            selected_executable="C:/mock/codex.exe",
            disable_args=("--disable", "plugins", "--disable", "shell_tool"),
            duration_ms=7,
            selected=SimpleNamespace(version="codex-cli test"),
        )
        captured: dict[str, Any] = {}

        def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            captured["command"] = command
            captured["kwargs"] = kwargs
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text(json.dumps(payload), encoding="utf-8")
            stdout = json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                }
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        backend = CodexExecStageBackend()
        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability",
                return_value=resolution,
            ),
            patch("test_case_agent.stage_backend.subprocess.run", side_effect=fake_run),
        ):
            result = backend.run_stage(
                stage="writer",
                prompt="bounded prompt",
                schema=schema,
                artifact_dir=artifact_dir,
            )

        self.assertEqual(payload, result.payload)
        self.assertIsNone(captured["kwargs"]["timeout"])
        self.assertIn("--ephemeral", captured["command"])
        self.assertIn("--ignore-user-config", captured["command"])
        self.assertIn("read-only", captured["command"])
        self.assertEqual(0, result.receipt["tool_event_count"])
        self.assertEqual({"input_tokens": 10, "output_tokens": 5}, result.receipt["tokens"])
        self.assertGreater(result.receipt["input_artifacts"]["bytes"], 0)

    def test_codex_backend_rejects_tool_events(self) -> None:
        artifact_dir = self.root / "backend-tool-event"
        schema = _writer_schema(["CARD-001"], "a" * 64)
        payload = {
            "schema_version": 1,
            "packet_sha256": "a" * 64,
            "intents": [],
            "unresolved_cards": [{"card_id": "CARD-001", "reason": "Нет oracle."}],
        }
        resolution = SimpleNamespace(
            verified=True,
            selected_executable="C:/mock/codex.exe",
            disable_args=("--disable", "plugins"),
            duration_ms=1,
            selected=SimpleNamespace(version="codex-cli test"),
        )

        def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text(json.dumps(payload), encoding="utf-8")
            stdout = json.dumps(
                {"type": "item.completed", "item": {"type": "command_execution"}}
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability",
                return_value=resolution,
            ),
            patch("test_case_agent.stage_backend.subprocess.run", side_effect=fake_run),
        ):
            with self.assertRaisesRegex(LeanV2BackendError, "forbidden tool events"):
                CodexExecStageBackend().run_stage(
                    stage="writer",
                    prompt="bounded prompt",
                    schema=schema,
                    artifact_dir=artifact_dir,
                )

    def test_prepare_only_performs_no_model_stage(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "complex",
                    "priority": "средний",
                    "inputs": {"writer_context": "Сложное поведение."},
                }
            ]
        )
        backend = FixtureStageBackend()
        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-prepare-only",
            prepare_only=True,
            backend=backend,
        )

        self.assertEqual("prepared", result.status)
        self.assertEqual([], backend.calls)
        self.assertTrue((self.root / "run-prepare-only" / "writer-request.json").is_file())
        self.assertFalse((self.root / "run-prepare-only" / "shadow-test-cases.md").exists())

    def test_prepare_only_rejects_precomputed_model_responses(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "complex",
                    "priority": "средний",
                    "inputs": {"writer_context": "Сложное поведение."},
                }
            ]
        )
        fixture = self.root / "writer-response.json"
        fixture.write_text("{}", encoding="utf-8")

        with self.assertRaisesRegex(LeanV2ContractError, "prepare_only cannot"):
            run_lean_v2_iteration(
                repo_root=self.root,
                source_packet=packet,
                output_dir=self.root / "run-invalid-prepare-only",
                prepare_only=True,
                writer_response=fixture,
            )

        self.assertFalse((self.root / "run-invalid-prepare-only").exists())

    def test_prepare_only_blocks_non_reproducible_runner_preconditions_before_model(self) -> None:
        packet = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "complex",
                    "priority": "средний",
                    "inputs": {"writer_context": "Сложное поведение."},
                }
            ]
        )
        payload = json.loads(packet.read_text(encoding="utf-8"))
        payload["base_preconditions"] = [
            "На основной форме нажать «Создать», чтобы открыть новую карточку."
        ]
        packet.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        backend = FixtureStageBackend()

        result = run_lean_v2_iteration(
            repo_root=self.root,
            source_packet=packet,
            output_dir=self.root / "run-invalid-runner-preconditions",
            prepare_only=True,
            backend=backend,
        )

        self.assertEqual("blocked-contract", result.status)
        self.assertEqual([], backend.calls)
        diagnostic = json.loads(
            (
                self.root
                / "run-invalid-runner-preconditions"
                / "failure-diagnostic.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("not production-reproducible", diagnostic["error"])

    def test_missing_xhtml_blocks_before_run_directory_is_created(self) -> None:
        packet_path = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "visibility",
                    "priority": "средний",
                    "inputs": {},
                }
            ]
        )
        payload = json.loads(packet_path.read_text(encoding="utf-8"))
        payload["source_files"] = payload["source_files"][:1]
        packet_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(LeanV2ContractError, "missing roles: xhtml"):
            run_lean_v2_iteration(
                repo_root=self.root,
                source_packet=packet_path,
                output_dir=self.root / "run-invalid",
                backend=FixtureStageBackend(),
            )
        self.assertFalse((self.root / "run-invalid").exists())

    def test_source_registry_cannot_read_existing_test_cases(self) -> None:
        packet_path = self._packet(
            [
                {
                    "obligation_id": "OBL-001",
                    "atom_id": "ATOM-001",
                    "template": "visibility",
                    "priority": "средний",
                    "inputs": {},
                }
            ]
        )
        forbidden = self.root / "test-cases" / "old.docx"
        forbidden.parent.mkdir()
        forbidden.write_bytes(b"old-canonical")
        payload = json.loads(packet_path.read_text(encoding="utf-8"))
        payload["source_files"][0] = {
            "role": "docx",
            "path": "test-cases/old.docx",
            "sha256": self._sha(forbidden),
        }
        packet_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(LeanV2ContractError, "test-case/history"):
            run_lean_v2_iteration(
                repo_root=self.root,
                source_packet=packet_path,
                output_dir=self.root / "run-forbidden-source",
                backend=FixtureStageBackend(),
            )


if __name__ == "__main__":
    unittest.main()
