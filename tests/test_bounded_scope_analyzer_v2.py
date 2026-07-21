from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.codex_exec_bounded_scope_analyzer import (
    ScopeAnalyzerError,
    StreamingExecResult,
    _backend_protocol_errors,
    _error_category,
    _lifecycle_payload,
    _prompt,
    _validate_scope_context,
    _validate_decision,
    analyze_dependency_gaps,
    legacy_detailed_output_schema,
    main,
    output_schema,
    parser,
    run_exec_streaming,
)
from test_case_agent.bounded_scope_materializer import (
    BoundedScopeMaterializationError,
    materialize_bounded_scope,
)
from test_case_agent.bounded_scope_boundary import expected_dependency_inventory
from test_case_agent.review_cycle.exec_backend import (
    ExecCapability,
    ExecCapabilityResolution,
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
)


class BoundedScopeAnalyzerV2Tests(unittest.TestCase):
    @classmethod
    def _context(cls) -> dict[str, object]:
        context = {
            "version": 1,
            "package_id": "WP-01",
            "scope_boundary": {
                "target": "BSR 39: открыть пустое окно калькулятора.",
                "include": ["Нажатие кнопки и наблюдаемый результат."],
                "exclude": ["Внутреннее поведение ФТ «Калькулятор»."],
            },
            "mockup_locators": ["Figure 1: КРЕДИТНЫЙ КАЛЬКУЛЯТОР"],
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "field_or_action": "Контекст",
                    "source_ref": "section 4.2",
                    "bounded_source_text": "4.2. Меню «Заявки в системе»",
                    "requirement_codes_hint": [],
                    "in_scope_hint": "no; section context",
                },
                {
                    "source_row_id": "SRC-002",
                    "field_or_action": "Кредитный калькулятор",
                    "source_ref": "BSR 39",
                    "bounded_source_text": (
                        "BSR 39. При нажатии открывается окно «Кредитный калькулятор» "
                        "с незаполненными данными. Описание будет приведено в ФТ «Калькулятор»."
                    ),
                    "requirement_codes_hint": ["BSR 39"],
                    "in_scope_hint": "yes; target behavior",
                },
            ],
        }
        return cls._bind_context(context)

    @staticmethod
    def _bind_context(context: dict[str, object]) -> dict[str, object]:
        payload = copy.deepcopy(context)
        payload.pop("source_cache", None)
        payload.pop("source_row_baseline", None)
        digest = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        context["source_cache"] = {
            "component_digests": {"bounded_context_sha256": digest}
        }
        return context

    @classmethod
    def _decision(cls) -> dict[str, object]:
        context = cls._context()
        return {
            "version": 2,
            "status": "ready",
            "blocking_reason": "none_required",
            "scope_summary": "Проверяется только открытие пустого окна по BSR 39.",
            "scope_boundary": copy.deepcopy(context["scope_boundary"]),
            "source_decisions": [
                {
                    "source_row_id": "SRC-001",
                    "disposition": "context",
                    "requirement_codes": [],
                    "rationale": "Заголовок задаёт раздел для целевой строки.",
                },
                {
                    "source_row_id": "SRC-002",
                    "disposition": "included",
                    "requirement_codes": ["BSR 39"],
                    "rationale": "Строка содержит целевое действие и результат.",
                },
            ],
            "dependencies": [
                {
                    "dependency_id": "DEP-001",
                    "kind": "external-requirement",
                    "name": "ФТ «Калькулятор»",
                    "source_row_ids": ["SRC-002"],
                    "resolution": "scope-excluded",
                    "target_source_row_ids": [],
                    "exact_source_fragments": ["ФТ «Калькулятор»"],
                    "gap_ids": [],
                    "blocking": False,
                    "rationale": "Внутреннее поведение явно исключено, результат BSR 39 самодостаточен.",
                }
            ],
            "gaps": [],
            "mockup_locators": ["Figure 1: КРЕДИТНЫЙ КАЛЬКУЛЯТОР"],
        }

    @classmethod
    def _legacy_context_and_decision(
        cls,
    ) -> tuple[dict[str, object], dict[str, object]]:
        repo_root = Path(__file__).resolve().parents[1]
        context = json.loads(
            (
                repo_root
                / "evals"
                / "lean-production-benchmark"
                / "h68"
                / "bounded-scope-context.json"
            ).read_text(encoding="utf-8")
        )
        decision = json.loads(
            (
                repo_root
                / "evals"
                / "lean-production-benchmark"
                / "h68"
                / "golden-scope-decision.json"
            ).read_text(encoding="utf-8")
        )
        context["scope_execution_facts"] = {
            "version": 1,
            "bounded_scope_kind": "single-section",
            "expected_testable_assertion_count": 1,
            "expected_tc_count": 1,
            "internal_package_count": 1,
            "has_heterogeneous_integrations": False,
            "has_large_dictionary": False,
            "mockups_ready": True,
        }
        return cls._bind_context(context), decision

    def test_compact_scope_schema_excludes_design_contract(self) -> None:
        compact = json.dumps(output_schema(["SRC-001"]), ensure_ascii=False)
        legacy = json.dumps(legacy_detailed_output_schema(["SRC-001"]), ensure_ascii=False)

        for forbidden in ("assertions", "obligations", "applicability", "planned_tc_id"):
            self.assertNotIn(forbidden, compact)
        self.assertLess(len(compact), len(legacy))

    def test_compact_scope_accepts_source_complete_decision(self) -> None:
        _validate_decision(self._decision(), self._context())

    def test_compact_scope_standalone_validator_rejects_unknown_fields(self) -> None:
        for location in ("root", "source-decision", "dependency"):
            with self.subTest(location=location):
                decision = self._decision()
                if location == "root":
                    decision["unexpected"] = True
                elif location == "source-decision":
                    decision["source_decisions"][0]["unexpected"] = True
                else:
                    decision["dependencies"][0]["unexpected"] = True
                with self.assertRaisesRegex(ScopeAnalyzerError, "fields mismatch"):
                    _validate_decision(decision, self._context())

    def test_compact_scope_standalone_validator_rejects_forged_membership(self) -> None:
        decision = self._decision()
        decision["source_decisions"][1]["disposition"] = "context"

        with self.assertRaisesRegex(ScopeAnalyzerError, "yes in_scope_hint"):
            _validate_decision(decision, self._context())

        context = self._context()
        context["source_rows"][1]["in_scope_hint"] = "yesterday; forged prefix"
        self._bind_context(context)
        with self.assertRaisesRegex(ScopeAnalyzerError, "yes/no token"):
            _validate_decision(self._decision(), context)

    def test_compact_scope_prompt_preserves_source_precedence(self) -> None:
        prompt = _prompt(self._context())

        self.assertIn("DOCX inline evidence is semantic source of truth", prompt)
        self.assertIn("expected_dependency_inventory", prompt)
        self.assertIn("source_row_ids are the inventory rows", prompt)
        self.assertIn("declared requires every target row", prompt)

    def test_global_type_examples_are_not_field_dependencies(self) -> None:
        context = self._context()
        context["source_rows"].insert(
            0,
            {
                "source_row_id": "SRC-GLOBAL-DATE",
                "field_or_action": "Ограничение типа Дата",
                "source_ref": "global type constraints / date",
                "source_context_class": "document-global-constraints",
                "bounded_source_text": (
                    "При сохранении данных в поле \"Дата\" сдвиг по часовому "
                    "поясу не происходит."
                ),
                "requirement_codes_hint": [],
                "in_scope_hint": "no; applicable document-global context",
            },
        )
        self._bind_context(context)
        decision = self._decision()
        decision["source_decisions"].insert(
            0,
            {
                "source_row_id": "SRC-GLOBAL-DATE",
                "disposition": "context",
                "requirement_codes": [],
                "rationale": "Общее ограничение типа даты остаётся контекстом.",
            },
        )

        inventory = expected_dependency_inventory(context)

        self.assertNotIn(
            ("field", "дата"),
            {(item["kind"], item["name"].casefold()) for item in inventory},
        )
        _validate_decision(decision, context)

    def test_non_type_global_cross_field_reference_remains_a_dependency(self) -> None:
        context = self._context()
        context["source_rows"].append(
            {
                "source_row_id": "SRC-GLOBAL-VISIBILITY",
                "field_or_action": "Глобальное правило видимости",
                "source_ref": "global visibility rule",
                "source_context_class": "document-global-constraints",
                "bounded_source_text": "Правило применяется, если поле «Внешний статус» заполнено.",
                "requirement_codes_hint": [],
                "in_scope_hint": "no; applicable document-global context",
            }
        )

        inventory = expected_dependency_inventory(context)

        self.assertIn(
            ("field", "внешний статус"),
            {(item["kind"], item["name"].casefold()) for item in inventory},
        )

    def test_required_context_relation_is_explicit_and_target_bound(self) -> None:
        context = self._context()
        context["source_rows"][0]["context_relation_required"] = True
        self._bind_context(context)
        with self.assertRaisesRegex(
            ScopeAnalyzerError,
            "context_relation_required rows need explicit",
        ):
            _validate_scope_context(context)

        context["expected_dependencies"] = [
            {
                "kind": "other",
                "name": "Контекст раздела",
                "source_row_ids": ["SRC-001"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-002"],
                "exact_source_fragments": ["4.2. Меню"],
            }
        ]
        self._bind_context(context)
        decision = self._decision()
        decision["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "other",
                "name": "Контекст раздела",
                "source_row_ids": ["SRC-001"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-002"],
                "exact_source_fragments": ["4.2. Меню"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Явная связь контекста раздела с целевой строкой.",
            }
        )

        _validate_decision(decision, context)

        decision["dependencies"][1]["target_source_row_ids"] = []
        with self.assertRaisesRegex(
            ScopeAnalyzerError,
            "target_source_row_ids must match expected inventory",
        ):
            _validate_decision(decision, context)

    def test_field_dependency_cannot_bypass_binding_as_source_provided(self) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] = (
            "Поле «Кредитный калькулятор». "
            + context["source_rows"][1]["bounded_source_text"]
        )
        self._bind_context(context)
        decision = self._decision()
        decision["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "field",
                "name": "Кредитный калькулятор",
                "source_row_ids": ["SRC-002"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-002"],
                "exact_source_fragments": [
                    "Поле «Кредитный калькулятор»"
                ],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Попытка обойти exact declared binding.",
            }
        )

        with self.assertRaisesRegex(
            ScopeAnalyzerError,
            "field dependency cannot use source-provided",
        ):
            _validate_decision(decision, context)

    def test_dictionary_dependency_requires_bound_values_even_with_target_rows(
        self,
    ) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] += (
            " По справочнику регионов"
        )
        context["expected_dependencies"] = [
            {
                "kind": "dictionary",
                "name": "регионы",
                "source_row_ids": ["SRC-002"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-002"],
                "exact_source_fragments": ["По справочнику регионов"],
            }
        ]
        self._bind_context(context)

        preflight = analyze_dependency_gaps(context)

        self.assertEqual("blocked-input", preflight["status"])
        self.assertEqual(1, preflight["blocking_gap_count"])
        self.assertEqual(
            "missing-dictionary-values",
            preflight["gaps"][0]["gap_type"],
        )
        self.assertEqual("регионы", preflight["gaps"][0]["referenced_entity"])

        decision = self._decision()
        decision["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "dictionary",
                "name": "регионы",
                "source_row_ids": ["SRC-002"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-002"],
                "exact_source_fragments": ["По справочнику регионов"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Строка ссылается на справочник без значений.",
            }
        )
        with self.assertRaisesRegex(
            ScopeAnalyzerError,
            "dictionary dependency lacks bound values",
        ):
            _validate_decision(decision, context)

    def test_user_confirmed_external_dynamic_dictionary_is_source_bound(self) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] += (
            " По справочнику регионов"
        )
        context["sources"] = [
            {
                "path": "fts/demo/work/vendor-references/dadata-reference.md",
                "role": "external-vendor-reference",
                "manifest_binding": "supporting-material",
            }
        ]
        context["external_dictionary_bindings"] = [
            {
                "dictionary_name": "регионы",
                "binding_type": "external-dynamic-dictionary",
                "provider": "DaData",
                "reference_path": (
                    "fts/demo/work/vendor-references/dadata-reference.md"
                ),
                "reference_url": "https://example.test/dadata/regions",
                "source_row_ids": ["SRC-002"],
                "query_parameters": {
                    "from_bound": "region",
                    "to_bound": "region",
                },
                "authority": "user-confirmed",
                "authority_ref": "CLR-DEMO-001",
            }
        ]
        context["expected_dependencies"] = [
            {
                "kind": "dictionary",
                "name": "регионы",
                "source_row_ids": ["SRC-002"],
                "resolution": "external-dynamic",
                "target_source_row_ids": [],
                "exact_source_fragments": ["По справочнику регионов"],
            }
        ]
        self._bind_context(context)

        self.assertEqual("pass", analyze_dependency_gaps(context)["status"])

        decision = self._decision()
        decision["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "dictionary",
                "name": "регионы",
                "source_row_ids": ["SRC-002"],
                "resolution": "external-dynamic",
                "target_source_row_ids": [],
                "exact_source_fragments": ["По справочнику регионов"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Значения поставляет авторитетный динамический API.",
            }
        )
        _validate_decision(decision, context)

        forged = copy.deepcopy(decision)
        forged["dependencies"][1]["target_source_row_ids"] = ["SRC-002"]
        with self.assertRaisesRegex(
            ScopeAnalyzerError,
            "target_source_row_ids must match expected inventory",
        ):
            _validate_decision(forged, context)

        unbound = copy.deepcopy(context)
        unbound["external_dictionary_bindings"] = []
        self._bind_context(unbound)
        with self.assertRaisesRegex(
            ScopeAnalyzerError,
            "must match external-dynamic dictionary dependencies",
        ):
            _validate_decision(decision, unbound)

    def test_compact_scope_requires_exact_ordered_row_bijection(self) -> None:
        decision = self._decision()
        decision["source_decisions"].reverse()

        with self.assertRaisesRegex(ScopeAnalyzerError, "input order"):
            _validate_decision(decision, self._context())

    def test_compact_scope_rejects_requirement_code_drift(self) -> None:
        decision = self._decision()
        decision["source_decisions"][1]["requirement_codes"] = []

        with self.assertRaisesRegex(ScopeAnalyzerError, "requirement_codes_hint"):
            _validate_decision(decision, self._context())

    def test_compact_scope_rejects_nonliteral_dependency_evidence(self) -> None:
        decision = self._decision()
        decision["dependencies"][0]["exact_source_fragments"] = ["неизвестный фрагмент"]

        with self.assertRaisesRegex(ScopeAnalyzerError, "literal linked-row"):
            _validate_decision(decision, self._context())

    def test_compact_scope_requires_missing_dependency_gap(self) -> None:
        decision = self._decision()
        dependency = decision["dependencies"][0]
        dependency["resolution"] = "missing"
        dependency["blocking"] = True
        dependency["gap_ids"] = []

        with self.assertRaisesRegex(ScopeAnalyzerError, "must link a blocking gap"):
            _validate_decision(decision, self._context())

    def test_compact_scope_requires_complete_dependency_inventory(self) -> None:
        decision = self._decision()
        decision["dependencies"] = []

        with self.assertRaisesRegex(ScopeAnalyzerError, "expected_dependency_inventory"):
            _validate_decision(decision, self._context())

    def test_compact_scope_rejects_unapproved_alias_resolution(self) -> None:
        decision = self._decision()
        dependency = decision["dependencies"][0]
        dependency["resolution"] = "approved-alias"

        with self.assertRaisesRegex(ScopeAnalyzerError, "lacks an approved target"):
            _validate_decision(decision, self._context())

    def test_compact_scope_accepts_bound_missing_dependency_gap(self) -> None:
        decision = self._decision()
        dependency = decision["dependencies"][0]
        dependency["resolution"] = "missing"
        dependency["blocking"] = True
        dependency["gap_ids"] = ["GAP-001"]
        decision["status"] = "blocked"
        decision["blocking_reason"] = "Отсутствует внешний источник."
        decision["gaps"] = [
            {
                "gap_id": "GAP-001",
                "gap_type": "cross-ft-dependency",
                "source_row_ids": ["SRC-002"],
                "source_refs": ["BSR 39"],
                "exact_source_fragments": ["ФТ «Калькулятор»"],
                "blocking": True,
                "clarification_question": "Где доступен внешний ФТ?",
                "downstream_handling": "block-writer",
            }
        ]

        _validate_decision(decision, self._context())

        decision["gaps"][0]["source_refs"] = ["FAKE 999"]
        with self.assertRaisesRegex(ScopeAnalyzerError, "match linked context rows"):
            _validate_decision(decision, self._context())

    def test_resolved_dependency_accepts_only_observation_interface_gap(self) -> None:
        decision = self._decision()
        dependency = decision["dependencies"][0]
        dependency["gap_ids"] = ["GAP-OBS-001"]
        decision["gaps"] = [
            {
                "gap_id": "GAP-OBS-001",
                "gap_type": "missing-observation-interface",
                "source_row_ids": ["SRC-002"],
                "source_refs": ["BSR 39"],
                "exact_source_fragments": ["ФТ «Калькулятор»"],
                "blocking": False,
                "clarification_question": (
                    "Какой интерфейс позволяет наблюдать внутренний эффект?"
                ),
                "downstream_handling": "carry-to-source-model",
            }
        ]

        _validate_decision(decision, self._context())

        decision["gaps"][0]["gap_type"] = "ambiguity"
        with self.assertRaisesRegex(
            ScopeAnalyzerError,
            "resolved dependency may link only",
        ):
            _validate_decision(decision, self._context())

    def test_compact_scope_enforces_ready_blocked_consistency(self) -> None:
        decision = self._decision()
        decision["status"] = "blocked"
        decision["blocking_reason"] = "Источник неполон."

        with self.assertRaisesRegex(ScopeAnalyzerError, "requires a blocking gap"):
            _validate_decision(decision, self._context())

    def test_compact_scope_cannot_bypass_semantic_design_materializer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(
                BoundedScopeMaterializationError, "boundary-only"
            ):
                materialize_bounded_scope(
                    repo_root=Path(raw),
                    context={},
                    decision=self._decision(),
                    handoff_dir=Path(raw) / "handoff",
                )

    def test_compact_scope_detects_mutated_prepared_context(self) -> None:
        context = self._context()
        _validate_scope_context(context)
        context["scope_boundary"]["target"] = "Подменённая граница"

        with self.assertRaisesRegex(ScopeAnalyzerError, "bounded_context_sha256 mismatch"):
            _validate_scope_context(context)
        with self.assertRaisesRegex(ScopeAnalyzerError, "bounded_context_sha256 mismatch"):
            _validate_decision(self._decision(), context)

    def test_parser_exposes_repo_root_with_project_default(self) -> None:
        arguments = parser().parse_args(
            [
                "--context", "context.json",
                "--decision-output", "decision.json",
                "--events-output", "events.ndjson",
                "--stderr-output", "stderr.txt",
                "--summary-output", "summary.json",
                "--schema-output", "schema.json",
            ]
        )

        self.assertEqual(Path(__file__).resolve().parents[1], arguments.repo_root)

    def test_bridge_forwards_resolved_repo_root_to_clarification_loader(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context_path = root / "context.json"
            boundary_path = root / "boundary.json"
            context_path.write_text(
                json.dumps(self._context(), ensure_ascii=False),
                encoding="utf-8",
            )
            boundary_path.write_text(
                json.dumps(self._decision(), ensure_ascii=False),
                encoding="utf-8",
            )
            arguments = [
                "--repo-root", str(root / "."),
                "--context", str(context_path),
                "--scope-boundary-decision", str(boundary_path),
                "--decision-output", str(root / "semantic-design.json"),
                "--events-output", str(root / "events.ndjson"),
                "--stderr-output", str(root / "stderr.txt"),
                "--summary-output", str(root / "summary.json"),
                "--schema-output", str(root / "schema.json"),
                "--contract-version", "1",
                "--scope-execution-profile", "standard-production",
            ]

            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer."
                    "load_approved_clarifications",
                    side_effect=ScopeAnalyzerError("stop after forwarding"),
                ) as loader,
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming"
                ) as run_model,
            ):
                code = main(arguments)

        self.assertEqual(2, code)
        loader.assert_called_once()
        self.assertEqual(root.resolve(), loader.call_args.args[0])
        run_model.assert_not_called()

    def test_compact_scope_main_reports_only_scope_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context_path = root / "context.json"
            decision_path = root / "decision.json"
            summary_path = root / "summary.json"
            schema_path = root / "schema.json"
            context_path.write_text(
                json.dumps(
                    self._bind_context(self._context()), ensure_ascii=False
                ),
                encoding="utf-8",
            )
            execution = StreamingExecResult(
                return_code=0,
                timed_out=False,
                tool_event_count=0,
                event_line_count=2,
                usage={"input_tokens": 100, "output_tokens": 20},
            )
            capability = ExecCapability(
                command="mock-codex",
                available=True,
                verified=True,
                returncode=0,
                duration_ms=1,
                missing_flags=(),
                version="codex-cli test",
                resolved_command=str((root / "mock-codex.exe").resolve()),
            )
            resolution = ExecCapabilityResolution(
                requested_command="mock-codex",
                probes=(capability,),
                selected=capability,
                disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
            )
            captured: dict[str, object] = {}
            def execute(*_args, **_kwargs):
                captured["command"] = _args[0]
                captured["timeout_seconds"] = _kwargs["timeout_seconds"]
                decision_path.write_text(
                    json.dumps(self._decision(), ensure_ascii=False), encoding="utf-8"
                )
                return execution

            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.resolve_verified_exec_capability",
                    return_value=resolution,
                ) as resolver,
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming",
                    side_effect=execute,
                ),
            ):
                code = main(
                    [
                        "--context", str(context_path),
                        "--decision-output", str(decision_path),
                        "--events-output", str(root / "events.ndjson"),
                        "--stderr-output", str(root / "stderr.txt"),
                        "--summary-output", str(summary_path),
                        "--schema-output", str(schema_path),
                        "--codex-command", "mock-codex",
                        "--contract-version", "2",
                        "--measurement-mode", "observational",
                    ]
                )

            self.assertEqual(0, code)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(2, summary["contract_version"])
            self.assertEqual(
                {"included": 1, "context": 1, "excluded": 0},
                summary["source_disposition_counts"],
            )
            self.assertEqual(1, summary["dependency_count"])
            self.assertNotIn("assertion_count", summary)
            self.assertNotIn("obligation_count", summary)
            self.assertIsNone(captured["timeout_seconds"])
            self.assertIsNone(
                resolver.call_args.kwargs["total_timeout_seconds"]
            )
            self.assertIsNone(
                summary["execution_policy"]["backend_probe_timeout_seconds"]
            )
            command = list(captured["command"])
            self.assertEqual(
                len(MODEL_TOOL_ISOLATION_DISABLE_FEATURES),
                command.count("--disable"),
            )
            self.assertIn("remote_plugin", command)
            self.assertIn("plugins", command)
            self.assertIn("apps", command)
            self.assertIn("shell_tool", command)
            self.assertIn("browser_use", command)

    def test_unknown_output_fields_are_terminal_for_both_contracts_without_retry(
        self,
    ) -> None:
        cases = (
            (1, "root"),
            (1, "nested"),
            (2, "root"),
            (2, "nested"),
        )
        for contract_version, location in cases:
            with self.subTest(contract_version=contract_version, location=location):
                if contract_version == 1:
                    context, decision = self._legacy_context_and_decision()
                else:
                    context = self._bind_context(self._context())
                    decision = self._decision()
                if location == "root":
                    decision["unexpected_root"] = "must-be-rejected"
                elif contract_version == 1:
                    decision["source_decisions"][0]["assertions"][0][
                        "unexpected_nested"
                    ] = "must-be-rejected"
                else:
                    decision["source_decisions"][0][
                        "unexpected_nested"
                    ] = "must-be-rejected"

                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    context_path = root / "context.json"
                    decision_path = root / "decision.json"
                    summary_path = root / "summary.json"
                    context_path.write_text(
                        json.dumps(context, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    capability = ExecCapability(
                        command="mock-codex",
                        available=True,
                        verified=True,
                        returncode=0,
                        duration_ms=1,
                        missing_flags=(),
                        version="codex-cli test",
                        resolved_command=str((root / "mock-codex.exe").resolve()),
                    )
                    resolution = ExecCapabilityResolution(
                        requested_command="mock-codex",
                        probes=(capability,),
                        selected=capability,
                        disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
                    )

                    def execute(*_args, **_kwargs):
                        decision_path.write_text(
                            json.dumps(decision, ensure_ascii=False),
                            encoding="utf-8",
                        )
                        return StreamingExecResult(
                            return_code=0,
                            timed_out=False,
                            tool_event_count=0,
                            event_line_count=4,
                            usage={"input_tokens": 10, "output_tokens": 5},
                            process_spawn_ms=1,
                            process_spawn_count=1,
                            process_exit_ms=6,
                            thread_started_ms=2,
                            thread_started_count=1,
                            turn_started_ms=3,
                            turn_started_count=1,
                            model_result_received_ms=4,
                            model_result_count=1,
                            turn_completed_ms=5,
                            turn_completed_count=1,
                        )

                    with (
                        patch(
                            "scripts.codex_exec_bounded_scope_analyzer."
                            "resolve_verified_exec_capability",
                            return_value=resolution,
                        ),
                        patch(
                            "scripts.codex_exec_bounded_scope_analyzer."
                            "run_exec_streaming",
                            side_effect=execute,
                        ) as run_model,
                    ):
                        code = main(
                            [
                                "--context", str(context_path),
                                "--decision-output", str(decision_path),
                                "--events-output", str(root / "events.ndjson"),
                                "--stderr-output", str(root / "stderr.txt"),
                                "--summary-output", str(summary_path),
                                "--schema-output", str(root / "schema.json"),
                                "--codex-command", "mock-codex",
                                "--contract-version", str(contract_version),
                            ]
                        )
                    summary = json.loads(
                        summary_path.read_text(encoding="utf-8")
                    )

                self.assertEqual(2, code)
                run_model.assert_called_once()
                self.assertEqual("terminal-failed", summary["status"])
                self.assertEqual("result-contract", summary["error_category"])
                self.assertEqual("result-validate", summary["error_stage"])
                self.assertEqual(
                    "OpenAIStrictOutputInstanceError", summary["error_type"]
                )
                self.assertIn("unknown=", summary["error"])
                self.assertEqual(1, summary["lifecycle"]["runner_attempt_count"])
                self.assertEqual(0, summary["lifecycle"]["runner_retry_count"])

    def test_streaming_lifecycle_records_ordered_model_milestones_without_timeout(self) -> None:
        script = (
            "import json\n"
            "events=["
            "{'type':'thread.started','thread_id':'thread-test'},"
            "{'type':'turn.started'},"
            "{'type':'item.completed','item':{'type':'agent_message','text':'{}'}},"
            "{'type':'turn.completed','usage':{'input_tokens':3}}]\n"
            "for event in events: print(json.dumps(event), flush=True)\n"
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result = run_exec_streaming(
                [sys.executable, "-c", script],
                prompt="",
                cwd=root,
                events_path=root / "events.ndjson",
                stderr_path=root / "stderr.txt",
                timeout_seconds=None,
                env=dict(os.environ),
            )

        self.assertFalse(result.timed_out)
        self.assertTrue(result.stream_complete)
        self.assertEqual("thread-test", result.thread_id)
        self.assertEqual(1, result.thread_started_count)
        self.assertEqual(1, result.turn_started_count)
        self.assertEqual(1, result.model_result_count)
        self.assertEqual(1, result.turn_completed_count)
        self.assertEqual((1, 2, 3, 4), (
            result.thread_started_sequence,
            result.turn_started_sequence,
            result.model_result_sequence,
            result.turn_completed_sequence,
        ))
        self.assertLessEqual(result.thread_started_ms, result.turn_started_ms)
        self.assertLessEqual(result.turn_started_ms, result.model_result_received_ms)
        self.assertLessEqual(result.model_result_received_ms, result.turn_completed_ms)

    def test_streaming_wait_failure_preserves_post_spawn_lifecycle(self) -> None:
        class FailingWaitProcess:
            def __init__(self) -> None:
                self.stdin = io.StringIO()
                self.stdout = io.StringIO('{"type":"thread.started","thread_id":"t-1"}\n')
                self.stderr = io.StringIO()
                self.returncode: int | None = None
                self.pid = 1234

            def wait(self, timeout=None):
                self.returncode = 7
                raise RuntimeError("simulated wait failure")

            def poll(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.subprocess.Popen",
                return_value=FailingWaitProcess(),
            ):
                result = run_exec_streaming(
                    ["mock-codex", "exec", "-"],
                    prompt="prompt",
                    cwd=root,
                    events_path=root / "events.ndjson",
                    stderr_path=root / "stderr.txt",
                    timeout_seconds=None,
                    env={},
                )

        self.assertEqual(1, result.process_spawn_count)
        self.assertIsNotNone(result.process_spawn_ms)
        self.assertEqual("process-wait", result.runner_error_stage)
        self.assertEqual("RuntimeError", result.runner_error_type)
        self.assertIn("simulated wait failure", result.runner_error)
        self.assertEqual(1, result.thread_started_count)

    def test_thread_start_failure_is_cleaned_up_and_preserves_spawn(self) -> None:
        class SpawnedProcess:
            def __init__(self) -> None:
                self.stdin = io.StringIO()
                self.stdout = io.StringIO()
                self.stderr = io.StringIO()
                self.returncode: int | None = None
                self.pid = 1234
                self.killed = False

            def wait(self, timeout=None):
                return self.returncode

            def poll(self):
                return self.returncode

            def kill(self):
                self.killed = True
                self.returncode = -9

        process = SpawnedProcess()

        def terminate(target, **_kwargs):
            target.kill()

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.subprocess.Popen",
                    return_value=process,
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.threading.Thread.start",
                    side_effect=RuntimeError("thread start failed"),
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer._terminate_process",
                    side_effect=terminate,
                ) as terminate_mock,
            ):
                result = run_exec_streaming(
                    ["mock-codex", "exec", "-"],
                    prompt="prompt",
                    cwd=root,
                    events_path=root / "events.ndjson",
                    stderr_path=root / "stderr.txt",
                    timeout_seconds=None,
                    cleanup_timeout_seconds=0.05,
                    env={},
                )

        terminate_mock.assert_called_once()
        self.assertTrue(process.killed)
        self.assertEqual(1, result.process_spawn_count)
        self.assertIsNotNone(result.process_spawn_ms)
        self.assertIsNotNone(result.process_exit_ms)
        self.assertEqual("post-spawn-setup", result.runner_error_stage)
        self.assertEqual("RuntimeError", result.runner_error_type)
        self.assertIn("thread start failed", result.runner_error)
        self.assertEqual(0.05, result.cleanup_timeout_seconds)
        lifecycle = _lifecycle_payload(result, runner_attempt_count=1)
        self.assertEqual("observed", lifecycle["process_spawned"]["state"])
        self.assertEqual(
            "subprocess-popen-returned",
            lifecycle["process_spawned"]["evidence"],
        )

    def test_clean_exit_still_has_bounded_stream_cleanup(self) -> None:
        class BlockingStream:
            def __init__(self) -> None:
                self.release = threading.Event()

            def __iter__(self):
                return self

            def __next__(self):
                self.release.wait()
                raise StopIteration

            def close(self):
                return None

        class CleanExitProcess:
            def __init__(self) -> None:
                self.stdin = io.StringIO()
                self.stdout = BlockingStream()
                self.stderr = io.StringIO()
                self.returncode = 0
                self.pid = 1234

            def wait(self, timeout=None):
                return self.returncode

            def poll(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

        process = CleanExitProcess()
        holder: dict[str, object] = {}

        def invoke() -> None:
            try:
                holder["result"] = run_exec_streaming(
                    ["mock-codex", "exec", "-"],
                    prompt="prompt",
                    cwd=root,
                    events_path=root / "events.ndjson",
                    stderr_path=root / "stderr.txt",
                    timeout_seconds=None,
                    cleanup_timeout_seconds=0.05,
                    env={},
                )
            except Exception as exc:  # pragma: no cover - assertion reports it
                holder["error"] = exc

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.subprocess.Popen",
                return_value=process,
            ):
                caller = threading.Thread(target=invoke, daemon=True)
                caller.start()
                caller.join(timeout=0.75)
                returned_before_release = not caller.is_alive()
                process.stdout.release.set()
                caller.join(timeout=1.0)

        self.assertTrue(returned_before_release)
        self.assertFalse(caller.is_alive())
        self.assertNotIn("error", holder)
        result = holder["result"]
        self.assertIsInstance(result, StreamingExecResult)
        self.assertFalse(result.timed_out)
        self.assertEqual(0, result.return_code)
        self.assertIsNotNone(result.process_exit_ms)
        self.assertTrue(result.cleanup_timed_out)
        self.assertEqual(0.05, result.cleanup_timeout_seconds)
        self.assertFalse(result.stream_complete)
        self.assertIn("drain-thread-deadline-exceeded", result.stream_transport_error)

    def test_lifecycle_order_uses_event_sequence_when_timestamps_are_equal(self) -> None:
        events = "\n".join(
            (
                '{"type":"turn.started"}',
                '{"type":"thread.started","thread_id":"late-thread"}',
                '{"type":"turn.completed","usage":{}}',
                '{"type":"item.completed","item":{"type":"agent_message"}}',
            )
        ) + "\n"

        class ReorderedProcess:
            def __init__(self) -> None:
                self.stdin = io.StringIO()
                self.stdout = io.StringIO(events)
                self.stderr = io.StringIO()
                self.returncode: int | None = None
                self.pid = 1234

            def wait(self, timeout=None):
                self.returncode = 0
                return self.returncode

            def poll(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.subprocess.Popen",
                    return_value=ReorderedProcess(),
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.time.perf_counter_ns",
                    return_value=1_000_000,
                ),
            ):
                result = run_exec_streaming(
                    ["mock-codex", "exec", "-"],
                    prompt="prompt",
                    cwd=root,
                    events_path=root / "events.ndjson",
                    stderr_path=root / "stderr.txt",
                    timeout_seconds=1,
                    env={},
                )

        self.assertEqual(
            {0},
            {
                result.thread_started_ms,
                result.turn_started_ms,
                result.model_result_received_ms,
                result.turn_completed_ms,
            },
        )
        self.assertEqual(
            (2, 1, 4, 3),
            (
                result.thread_started_sequence,
                result.turn_started_sequence,
                result.model_result_sequence,
                result.turn_completed_sequence,
            ),
        )
        self.assertEqual(
            (
                "turn.started-before-thread.started",
                "turn.completed-before-model-result",
            ),
            result.lifecycle_violations,
        )
        self.assertEqual(result.lifecycle_violations, _backend_protocol_errors(result))

    def test_explicit_timeout_has_bounded_stream_cleanup(self) -> None:
        class BlockingStream:
            def __init__(self) -> None:
                self.release = threading.Event()

            def __iter__(self):
                return self

            def __next__(self):
                self.release.wait()
                raise StopIteration

            def close(self):
                return None

        class TimedOutProcess:
            def __init__(self) -> None:
                self.stdin = io.StringIO()
                self.stdout = BlockingStream()
                self.stderr = io.StringIO()
                self.returncode: int | None = None
                self.pid = 1234

            def wait(self, timeout=None):
                if self.returncode is None:
                    raise subprocess.TimeoutExpired("mock-codex", timeout)
                return self.returncode

            def poll(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

        process = TimedOutProcess()

        def terminate(target, **_kwargs):
            target.returncode = -9

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.subprocess.Popen",
                    return_value=process,
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer._terminate_process",
                    side_effect=terminate,
                ),
            ):
                result = run_exec_streaming(
                    ["mock-codex", "exec", "-"],
                    prompt="prompt",
                    cwd=root,
                    events_path=root / "events.ndjson",
                    stderr_path=root / "stderr.txt",
                    timeout_seconds=0.01,
                    cleanup_timeout_seconds=0.05,
                    env={},
                )
        process.stdout.release.set()

        self.assertTrue(result.timed_out)
        self.assertTrue(result.cleanup_timed_out)
        self.assertEqual(0.05, result.cleanup_timeout_seconds)
        self.assertFalse(result.stream_complete)
        self.assertIn("drain-thread-deadline-exceeded", result.stream_transport_error)

    def test_invalid_context_json_is_input_contract_not_result_parse(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context_path = root / "context.json"
            summary_path = root / "summary.json"
            context_path.write_text("{invalid", encoding="utf-8")
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming"
            ) as execute:
                code = main(
                    [
                        "--context", str(context_path),
                        "--decision-output", str(root / "decision.json"),
                        "--events-output", str(root / "events.ndjson"),
                        "--stderr-output", str(root / "stderr.txt"),
                        "--summary-output", str(summary_path),
                        "--schema-output", str(root / "schema.json"),
                    ]
                )
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(2, code)
        execute.assert_not_called()
        self.assertEqual("input-contract", summary["error_category"])
        self.assertEqual("input-load", summary["error_stage"])

    def test_profile_facts_tampering_is_rejected_before_routing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = self._context()
            context["scope_execution_facts"] = {
                "version": 1,
                "bounded_scope_kind": "single-section",
                "expected_testable_assertion_count": 1,
                "expected_tc_count": 1,
                "internal_package_count": 1,
                "has_heterogeneous_integrations": False,
                "has_large_dictionary": False,
                "mockups_ready": True,
            }
            self._bind_context(context)
            context["scope_execution_facts"]["expected_tc_count"] = 99
            context_path = root / "context.json"
            summary_path = root / "summary.json"
            context_path.write_text(
                json.dumps(context, ensure_ascii=False), encoding="utf-8"
            )
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming"
            ) as execute:
                code = main(
                    [
                        "--context", str(context_path),
                        "--decision-output", str(root / "decision.json"),
                        "--events-output", str(root / "events.ndjson"),
                        "--stderr-output", str(root / "stderr.txt"),
                        "--summary-output", str(summary_path),
                        "--schema-output", str(root / "schema.json"),
                        "--contract-version", "1",
                    ]
                )
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(2, code)
        execute.assert_not_called()
        self.assertEqual("context-binding", summary["error_stage"])
        self.assertEqual("input-contract", summary["error_category"])

    def test_non_object_model_json_is_result_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context_path = root / "context.json"
            decision_path = root / "decision.json"
            summary_path = root / "summary.json"
            context_path.write_text(
                json.dumps(self._bind_context(self._context()), ensure_ascii=False),
                encoding="utf-8",
            )
            capability = ExecCapability(
                command="mock-codex",
                available=True,
                verified=True,
                returncode=0,
                duration_ms=1,
                missing_flags=(),
                version="codex-cli test",
                resolved_command=str((root / "mock-codex.exe").resolve()),
            )
            resolution = ExecCapabilityResolution(
                requested_command="mock-codex",
                probes=(capability,),
                selected=capability,
                disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
            )

            def execute(*_args, **_kwargs):
                decision_path.write_text("[]\n", encoding="utf-8")
                return StreamingExecResult(
                    return_code=0,
                    timed_out=False,
                    tool_event_count=0,
                    event_line_count=0,
                    usage={},
                )

            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.resolve_verified_exec_capability",
                    return_value=resolution,
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming",
                    side_effect=execute,
                ),
            ):
                code = main(
                    [
                        "--context", str(context_path),
                        "--decision-output", str(decision_path),
                        "--events-output", str(root / "events.ndjson"),
                        "--stderr-output", str(root / "stderr.txt"),
                        "--summary-output", str(summary_path),
                        "--schema-output", str(root / "schema.json"),
                        "--contract-version", "2",
                    ]
                )
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(2, code)
        self.assertEqual("result-contract", summary["error_category"])
        self.assertEqual("result-validate", summary["error_stage"])
        self.assertIsNotNone(
            summary["lifecycle"]["model_invoked"]["observed_after_stage_start_ms"]
        )

    def test_timeout_taxonomy_distinguishes_pre_turn_model_wait_and_post_result(self) -> None:
        before_turn = StreamingExecResult(1, True, 0, 0, {})
        model_wait = StreamingExecResult(
            1,
            True,
            0,
            0,
            {},
            turn_started_count=1,
        )
        post_result = StreamingExecResult(
            1,
            True,
            0,
            0,
            {},
            turn_started_count=1,
            model_result_count=1,
        )

        self.assertEqual(
            "stage-timeout-before-turn",
            _error_category(
                TimeoutError(), error_stage="turn-start-wait", execution=before_turn
            ),
        )
        self.assertEqual(
            "model-result-wait-timeout",
            _error_category(
                TimeoutError(), error_stage="model-result-wait", execution=model_wait
            ),
        )
        self.assertEqual(
            "post-result-process-exit-timeout",
            _error_category(
                TimeoutError(),
                error_stage="post-result-process-exit",
                execution=post_result,
            ),
        )

    def test_backend_protocol_checks_all_duplicate_lifecycle_events(self) -> None:
        not_spawned = StreamingExecResult(0, False, 0, 0, {})
        self.assertEqual(0, not_spawned.process_spawn_count)
        not_spawned_lifecycle = _lifecycle_payload(
            not_spawned,
            runner_attempt_count=1,
        )
        self.assertEqual(
            "not-observed",
            not_spawned_lifecycle["process_spawned"]["state"],
        )
        self.assertIsNone(not_spawned_lifecycle["process_spawned"]["evidence"])
        execution = StreamingExecResult(
            0,
            False,
            0,
            0,
            {},
            thread_started_count=2,
            turn_started_count=2,
            model_result_count=2,
            turn_completed_count=2,
            lifecycle_violations=("model-result-before-turn.started",),
        )

        self.assertEqual(
            (
                "duplicate thread.started=2",
                "duplicate turn.started=2",
                "duplicate model-result=2",
                "duplicate turn.completed=2",
                "model-result-before-turn.started",
            ),
            _backend_protocol_errors(execution),
        )

    def test_standard_v1_profile_routes_without_launching_model(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            rows = []
            for index in range(13):
                rows.append(
                    {
                        "source_row_id": f"SRC-{index + 1:03d}",
                        "field_or_action": f"Field {index + 1}",
                        "source_ref": f"BSR {263 + index}",
                        "bounded_source_text": f"Field {index + 1}. BSR {263 + index}.",
                        "requirement_codes_hint": [],
                    }
                )
            for index, code_value in enumerate(range(263, 285)):
                rows[index % len(rows)]["requirement_codes_hint"].append(
                    f"BSR {code_value}"
                )
            for row in rows:
                codes = row["requirement_codes_hint"]
                row["source_ref"] = ", ".join(codes)
                row["bounded_source_text"] = (
                    f"{row['field_or_action']}. " + ". ".join(codes) + "."
                )
            facts = {
                "version": 1,
                "bounded_scope_kind": "single-section",
                "expected_testable_assertion_count": 10,
                "expected_tc_count": 14,
                "internal_package_count": 1,
                "has_heterogeneous_integrations": False,
                "has_large_dictionary": False,
                "mockups_ready": True,
            }
            context_path = root / "context.json"
            summary_path = root / "summary.json"
            profile_path = root / "profile.json"
            bound_context = self._bind_context(
                {"source_rows": rows, "scope_execution_facts": facts}
            )
            context_path.write_text(
                json.dumps(bound_context, ensure_ascii=False),
                encoding="utf-8",
            )
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming"
            ) as execute:
                code = main(
                    [
                        "--context", str(context_path),
                        "--decision-output", str(root / "decision.json"),
                        "--events-output", str(root / "events.ndjson"),
                        "--stderr-output", str(root / "stderr.txt"),
                        "--summary-output", str(summary_path),
                        "--schema-output", str(root / "schema.json"),
                        "--scope-execution-profile-output", str(profile_path),
                        "--contract-version", "1",
                    ]
                )

            self.assertEqual(4, code)
            execute.assert_not_called()
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual("route-required", summary["status"])
            self.assertFalse(summary["model_invoked"])
            self.assertEqual("standard-production", profile["selected_profile"])
            self.assertEqual(22, profile["diagnostics"]["unique_requirement_code_count"])
            self.assertEqual([], profile["unknown_criteria"])
            self.assertEqual(
                [
                    {
                        "code": "source-row-limit-exceeded",
                        "actual": 13,
                        "limit": 12,
                    }
                ],
                profile["violations"],
            )
            self.assertEqual(0, summary["lifecycle"]["runner_attempt_count"])

    def test_spawn_failure_does_not_claim_model_invocation_or_retry(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = self._context()
            context["scope_execution_facts"] = {
                "version": 1,
                "bounded_scope_kind": "single-section",
                "expected_testable_assertion_count": 1,
                "expected_tc_count": 1,
                "internal_package_count": 1,
                "has_heterogeneous_integrations": False,
                "has_large_dictionary": False,
                "mockups_ready": True,
            }
            self._bind_context(context)
            context_path = root / "context.json"
            summary_path = root / "summary.json"
            context_path.write_text(
                json.dumps(context, ensure_ascii=False), encoding="utf-8"
            )
            capability = ExecCapability(
                command="mock-codex",
                available=True,
                verified=True,
                returncode=0,
                duration_ms=1,
                missing_flags=(),
                version="codex-cli test",
                resolved_command=str((root / "mock-codex.exe").resolve()),
            )
            resolution = ExecCapabilityResolution(
                requested_command="mock-codex",
                probes=(capability,),
                selected=capability,
                disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
            )
            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.resolve_verified_exec_capability",
                    return_value=resolution,
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming",
                    side_effect=PermissionError("access denied"),
                ) as execute,
            ):
                code = main(
                    [
                        "--context", str(context_path),
                        "--decision-output", str(root / "decision.json"),
                        "--events-output", str(root / "events.ndjson"),
                        "--stderr-output", str(root / "stderr.txt"),
                        "--summary-output", str(summary_path),
                        "--schema-output", str(root / "schema.json"),
                        "--codex-command", "mock-codex",
                        "--contract-version", "1",
                    ]
                )

            self.assertEqual(2, code)
            execute.assert_called_once()
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual("process-spawn", summary["error_category"])
            self.assertFalse(summary["model_invoked"])
            self.assertEqual(1, summary["lifecycle"]["runner_attempt_count"])
            self.assertEqual(0, summary["lifecycle"]["runner_retry_count"])
            self.assertEqual(
                "not-observed", summary["lifecycle"]["process_spawned"]["state"]
            )

    def test_compact_scope_main_rejects_malformed_context_before_model(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = self._context()
            context.pop("scope_boundary")
            self._bind_context(context)
            context_path = root / "context.json"
            summary_path = root / "summary.json"
            context_path.write_text(
                json.dumps(context, ensure_ascii=False), encoding="utf-8"
            )
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming"
            ) as execute:
                code = main(
                    [
                        "--context", str(context_path),
                        "--decision-output", str(root / "decision.json"),
                        "--events-output", str(root / "events.ndjson"),
                        "--stderr-output", str(root / "stderr.txt"),
                        "--summary-output", str(summary_path),
                        "--schema-output", str(root / "schema.json"),
                        "--codex-command", "must-not-run",
                        "--contract-version", "2",
                    ]
                )

            self.assertEqual(2, code)
            execute.assert_not_called()
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual("terminal-failed", summary["status"])
            self.assertFalse(summary["model_invoked"])


if __name__ == "__main__":
    unittest.main()
