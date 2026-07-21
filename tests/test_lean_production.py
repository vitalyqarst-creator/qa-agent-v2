from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_case_agent.lean_production import (
    FULL_PROCESS_PHASES,
    LeanProductionError,
    audit_handoff,
    build_timing_report,
    finish_phase,
    finish_run,
    reconcile_codex_turn,
    reconcile_external_elapsed,
    start_phase,
    start_run,
    terminalize_run,
    transition_phase,
)
from scripts import run_lean_production_iteration, workflow_wall_clock
from scripts.codex_exec_bounded_scope_analyzer import (
    ScopeAnalyzerError,
    StreamingExecResult,
    _parse_events,
    _validate_legacy_detailed_decision,
    analyze_dependency_gaps,
    main as bounded_scope_main,
    run_exec_streaming,
)
from test_case_agent.review_cycle.exec_backend import (
    ExecCapability,
    ExecCapabilityResolution,
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
)


class LeanProductionTests(unittest.TestCase):
    def test_source_review_reuse_persists_missing_local_summary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            review = root / "source-assertion-review.json"
            summary = root / "source-review-summary.json"
            review.write_text('{"decision":"accepted"}\n', encoding="utf-8")

            receipt = run_lean_production_iteration._persist_source_review_reuse_receipt(
                source_assertion_review=review,
                persisted_summary=summary,
            )

            self.assertTrue(summary.is_file())
            self.assertEqual(receipt, json.loads(summary.read_text(encoding="utf-8")))
            self.assertEqual("reused", receipt["status"])
            self.assertEqual(
                hashlib.sha256(review.read_bytes()).hexdigest(),
                receipt["reuse_evidence"]["source_assertion_review"]["sha256"],
            )

    def test_stage_timeout_policy_separates_observation_from_production(self) -> None:
        observational = SimpleNamespace(
            measurement_mode="observational",
            model_timeout_seconds=None,
            source_review_timeout_seconds=None,
            writer_timeout_seconds=None,
            reviewer_timeout_seconds=None,
        )
        production = SimpleNamespace(
            measurement_mode="production",
            model_timeout_seconds=None,
            source_review_timeout_seconds=None,
            writer_timeout_seconds=None,
            reviewer_timeout_seconds=None,
        )

        self.assertEqual(
            {"source_review": 0, "writer": 0, "reviewer": 0},
            run_lean_production_iteration._effective_stage_timeouts(observational),
        )
        self.assertEqual(
            {"source_review": 900, "writer": 600, "reviewer": 600},
            run_lean_production_iteration._effective_stage_timeouts(production),
        )

    def test_full_process_phase_contract_places_semantic_design_after_boundary(self) -> None:
        self.assertEqual(
            (
                "scope-analysis",
                "semantic-design",
                "scope-materialization",
                "source-review",
            ),
            FULL_PROCESS_PHASES[3:7],
        )

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

    @staticmethod
    def _h71_dependency_context() -> dict[str, object]:
        return {
            "version": 1,
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "field_or_action": "Социальный статус",
                    "source_ref": "BSR 263",
                    "bounded_source_text": (
                        "Социальный статус. Значение из справочника «Социальный статус»: "
                        "работа по найму; пенсионер (не работает); самозанятый. BSR 263."
                    ),
                },
                {
                    "source_row_id": "SRC-002",
                    "field_or_action": "Наименование организации, ИНН",
                    "source_ref": "BSR 264",
                    "bounded_source_text": (
                        "BSR 264. Видимость: поле «Тип занятости» заполнено."
                    ),
                },
                {
                    "source_row_id": "SRC-003",
                    "field_or_action": "Тип должности",
                    "source_ref": "BSR 274",
                    "bounded_source_text": (
                        "Значение из справочника «Типы должности». BSR 274. "
                        "Видимость: поле «Тип занятости» заполнено."
                    ),
                },
            ],
        }

    def test_h71_dependency_gate_blocks_missing_field_and_dictionary(self) -> None:
        result = analyze_dependency_gaps(self._h71_dependency_context())

        self.assertEqual("blocked-input", result["status"])
        self.assertEqual(2, result["blocking_gap_count"])
        self.assertEqual(
            ["undeclared-field-reference", "missing-dictionary-values"],
            [item["gap_type"] for item in result["gaps"]],
        )
        self.assertEqual("Тип занятости", result["gaps"][0]["referenced_entity"])
        self.assertEqual("Типы должности", result["gaps"][1]["referenced_entity"])

    def test_h71_dependency_gate_accepts_only_explicit_alias_and_dictionary_values(self) -> None:
        context = self._h71_dependency_context()
        context["dependency_aliases"] = {"Тип занятости": "Социальный статус"}
        context["dictionary_inventory"] = {
            "Типы должности": ["Руководитель", "Специалист"]
        }

        result = analyze_dependency_gaps(context)

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["gaps"])

    def test_dependency_gate_does_not_treat_global_type_examples_as_ui_fields(
        self,
    ) -> None:
        context = self._h71_dependency_context()
        context["dependency_aliases"] = {"Тип занятости": "Социальный статус"}
        context["dictionary_inventory"] = {
            "Типы должности": ["Руководитель", "Специалист"]
        }
        context["source_rows"].extend(
            [
                {
                    "source_row_id": "SRC-GLOBAL-DATE",
                    "field_or_action": "Ограничение типа Дата",
                    "source_ref": "global type constraints / date",
                    "source_context_class": "document-global-constraints",
                    "bounded_source_text": (
                        "При сохранении данных в поле \"Дата\" сдвиг по "
                        "часовому поясу не происходит."
                    ),
                },
                {
                    "source_row_id": "SRC-GLOBAL-DATETIME",
                    "field_or_action": "Ограничение типа Дата и время",
                    "source_ref": "global type constraints / datetime",
                    "source_context_class": "document-global-constraints",
                    "bounded_source_text": (
                        "При сохранении данных с поля «Дата и время» "
                        "применяется часовой пояс."
                    ),
                },
            ]
        )

        result = analyze_dependency_gaps(context)

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["gaps"])

    def test_dependency_gate_still_blocks_undeclared_scope_local_field(self) -> None:
        context = self._h71_dependency_context()
        context["source_rows"][1]["source_context_class"] = "scope-local"
        context["dictionary_inventory"] = {
            "Типы должности": ["Руководитель", "Специалист"]
        }

        result = analyze_dependency_gaps(context)

        self.assertEqual("blocked-input", result["status"])
        self.assertEqual(1, result["blocking_gap_count"])
        self.assertEqual("Тип занятости", result["gaps"][0]["referenced_entity"])

    def test_dependency_gate_still_checks_non_type_global_field_reference(self) -> None:
        context = self._h71_dependency_context()
        context["dependency_aliases"] = {"Тип занятости": "Социальный статус"}
        context["dictionary_inventory"] = {
            "Типы должности": ["Руководитель", "Специалист"]
        }
        context["source_rows"].append(
            {
                "source_row_id": "SRC-GLOBAL-CROSS-FIELD",
                "field_or_action": "Глобальное правило видимости",
                "source_ref": "global visibility rule",
                "source_context_class": "document-global-constraints",
                "bounded_source_text": (
                    "Правило применяется, если поле «Внешний статус» "
                    "заполнено."
                ),
            }
        )

        result = analyze_dependency_gaps(context)

        self.assertEqual("blocked-input", result["status"])
        self.assertEqual(1, result["blocking_gap_count"])
        self.assertEqual("Внешний статус", result["gaps"][0]["referenced_entity"])

    def test_h71_blocked_input_does_not_launch_model_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = root / "context.json"
            context.write_text(
                json.dumps(self._h71_dependency_context(), ensure_ascii=False),
                encoding="utf-8",
            )
            outputs = {
                "decision": root / "decision.json",
                "events": root / "events.ndjson",
                "stderr": root / "stderr.txt",
                "summary": root / "summary.json",
                "schema": root / "schema.json",
                "preflight": root / "preflight.json",
                "receipt": root / "terminal-receipt.json",
            }
            outputs["decision"].write_text('{"status":"stale-ready"}\n', encoding="utf-8")
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.subprocess.Popen"
            ) as popen:
                code = bounded_scope_main(
                    [
                        "--context", str(context),
                        "--decision-output", str(outputs["decision"]),
                        "--events-output", str(outputs["events"]),
                        "--stderr-output", str(outputs["stderr"]),
                        "--summary-output", str(outputs["summary"]),
                        "--schema-output", str(outputs["schema"]),
                        "--preflight-output", str(outputs["preflight"]),
                        "--terminal-receipt-output", str(outputs["receipt"]),
                        "--codex-command", "must-not-run",
                    ]
                )

            self.assertEqual(3, code)
            popen.assert_not_called()
            summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertEqual("blocked-input", summary["status"])
            self.assertFalse(summary["model_invoked"])
            self.assertFalse(outputs["decision"].exists())
            self.assertEqual("published", summary["terminal_receipt"])
            receipt = json.loads(outputs["receipt"].read_text(encoding="utf-8"))
            self.assertEqual("scope-dependency-gap-gate", receipt["stage"])

    def test_streaming_exec_preserves_partial_usage_and_stderr_on_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            command = [
                sys.executable,
                "-c",
                (
                    "import json,sys,time;"
                    "print(json.dumps({'type':'turn.completed','usage':"
                    "{'input_tokens':12,'output_tokens':3}}),flush=True);"
                    "print('partial-stderr',file=sys.stderr,flush=True);"
                    "time.sleep(30)"
                ),
            ]
            result = run_exec_streaming(
                command,
                prompt="",
                cwd=root,
                events_path=root / "events.ndjson",
                stderr_path=root / "stderr.txt",
                timeout_seconds=1,
                env=dict(os.environ),
            )

            self.assertTrue(result.timed_out)
            self.assertEqual(1, result.event_line_count)
            self.assertEqual(12, result.usage["input_tokens"])
            self.assertIn("turn.completed", (root / "events.ndjson").read_text(encoding="utf-8"))
            self.assertIn("partial-stderr", (root / "stderr.txt").read_text(encoding="utf-8"))

    def test_bounded_scope_timeout_summary_keeps_partial_usage_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = root / "context.json"
            context_payload = self._bind_context(
                {
                        "source_rows": [
                            {
                                "source_row_id": "SRC-001",
                                "field_or_action": "Поле A",
                                "source_ref": "BSR 1",
                                "bounded_source_text": "Поле A всегда видно. BSR 1.",
                            }
                        ],
                        "scope_execution_facts": {
                            "version": 1,
                            "bounded_scope_kind": "single-section",
                            "expected_testable_assertion_count": 1,
                            "expected_tc_count": 1,
                            "internal_package_count": 1,
                            "has_heterogeneous_integrations": False,
                            "has_large_dictionary": False,
                            "mockups_ready": True,
                        },
                }
            )
            context.write_text(
                json.dumps(context_payload, ensure_ascii=False),
                encoding="utf-8",
            )
            events = root / "events.ndjson"
            stderr = root / "stderr.txt"
            events.write_text('{"type":"turn.completed"}\n', encoding="utf-8")
            stderr.write_text("partial\n", encoding="utf-8")
            execution = StreamingExecResult(
                timed_out=True,
                return_code=-1,
                tool_event_count=0,
                event_line_count=1,
                usage={"input_tokens": 21, "output_tokens": 2},
                turn_started_ms=5,
                turn_started_count=1,
                stream_transport_error="stdout:closed-after-timeout",
                stream_complete=False,
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
            summary = root / "summary.json"
            receipt = root / "terminal-receipt.json"
            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.resolve_verified_exec_capability",
                    return_value=resolution,
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming",
                    return_value=execution,
                ),
            ):
                code = bounded_scope_main(
                    [
                        "--context", str(context),
                        "--decision-output", str(root / "decision.json"),
                        "--events-output", str(events),
                        "--stderr-output", str(stderr),
                        "--summary-output", str(summary),
                        "--schema-output", str(root / "schema.json"),
                        "--terminal-receipt-output", str(receipt),
                        "--codex-command", "mock-codex",
                        "--timeout-seconds", "1",
                    ]
                )

            self.assertEqual(2, code)
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual("terminal-failed", payload["status"])
            self.assertEqual("TimeoutError", payload["error_type"])
            self.assertEqual("model-result-wait-timeout", payload["error_category"])
            self.assertEqual(
                "stdout:closed-after-timeout",
                payload["lifecycle"]["cleanup"]["secondary_stream_error"],
            )
            self.assertEqual(21, payload["usage"]["input_tokens"])
            self.assertTrue(payload["partial_events_preserved"])
            self.assertTrue(payload["partial_stderr_preserved"])
            self.assertEqual("published", payload["terminal_receipt"])

    def test_bounded_scope_event_parser_rejects_tool_use(self) -> None:
        raw = "\n".join(
            (
                json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}),
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 12}}),
            )
        )

        tool_count, usage = _parse_events(raw)

        self.assertEqual(tool_count, 1)
        self.assertEqual(usage, {"input_tokens": 12})

    def test_bounded_scope_decision_requires_exact_rows_obligations_and_dimensions(self) -> None:
        dimensions = (
            "conditional-visibility",
            "scenario-use-case",
            "traceability",
            "accessibility-ui",
            "role-permission",
            "status-lifecycle",
            "equivalence",
            "boundary",
            "table-list",
            "integration",
            "async",
            "persistence",
            "security",
        )
        context = {"source_rows": [{"source_row_id": "SRC-001"}]}
        decision = {
            "source_decisions": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-001",
                            "atom_id": "ATOM-001",
                            "semantic_disposition": "testable",
                            "execution_readiness": "ready",
                            "execution_readiness_rationale": "none_required",
                            "obligation_ids": ["OBL-001"],
                        }
                    ],
                }
            ],
            "obligations": [
                {"obligation_id": "OBL-001", "planned_tc_id": "TC-001"}
            ],
            "applicability": [
                {
                    "dimension": item,
                    "applicable": "yes" if item in {"scenario-use-case", "traceability"} else "no",
                    "linked_atoms": ["ATOM-001"] if item in {"scenario-use-case", "traceability"} else [],
                    "linked_test_cases": ["TC-001"] if item in {"scenario-use-case", "traceability"} else [],
                }
                for item in dimensions
            ],
        }

        _validate_legacy_detailed_decision(decision, context)
        decision["obligations"] = []

        with self.assertRaisesRegex(ScopeAnalyzerError, "obligations"):
            _validate_legacy_detailed_decision(decision, context)

    def test_bounded_scope_decision_rejects_inconsistent_dimension_links(self) -> None:
        dimensions = (
            "conditional-visibility", "scenario-use-case", "traceability",
            "accessibility-ui", "role-permission", "status-lifecycle",
            "equivalence", "boundary", "table-list", "integration", "async",
            "persistence", "security",
        )
        context = {"source_rows": [{"source_row_id": "SRC-001"}]}
        decision = {
            "source_decisions": [{
                "source_row_id": "SRC-001",
                "assertions": [{
                    "assertion_id": "ASSERT-001",
                    "atom_id": "ATOM-001",
                    "semantic_disposition": "testable",
                    "execution_readiness": "ready",
                    "execution_readiness_rationale": "none_required",
                    "obligation_ids": ["OBL-001"],
                }],
            }],
            "obligations": [{"obligation_id": "OBL-001", "planned_tc_id": "TC-001"}],
            "applicability": [{
                "dimension": item,
                "applicable": "no",
                "linked_atoms": ["ATOM-001"] if item == "accessibility-ui" else [],
                "linked_test_cases": [],
            } for item in dimensions],
        }

        with self.assertRaisesRegex(ScopeAnalyzerError, "must not link"):
            _validate_legacy_detailed_decision(decision, context)

    def test_bounded_scope_decision_rejects_ui_visibility_as_accessibility(self) -> None:
        dimensions = (
            "conditional-visibility", "scenario-use-case", "traceability",
            "accessibility-ui", "role-permission", "status-lifecycle",
            "equivalence", "boundary", "table-list", "integration", "async",
            "persistence", "security",
        )
        context = {"source_rows": [{"source_row_id": "SRC-001"}]}
        decision = {
            "source_decisions": [{
                "source_row_id": "SRC-001",
                "assertions": [{
                    "assertion_id": "ASSERT-001",
                    "atom_id": "ATOM-001",
                    "semantic_disposition": "testable",
                    "execution_readiness": "ready",
                    "execution_readiness_rationale": "none_required",
                    "obligation_ids": ["OBL-001"],
                }],
            }],
            "obligations": [{
                "obligation_id": "OBL-001",
                "planned_tc_id": "TC-001",
                "property_type": "functional-ui-behavior",
                "design_dimension": "scenario-use-case",
            }],
            "applicability": [{
                "dimension": item,
                "applicable": "yes" if item in {"scenario-use-case", "traceability", "accessibility-ui"} else "no",
                "linked_atoms": ["ATOM-001"] if item in {"scenario-use-case", "traceability", "accessibility-ui"} else [],
                "linked_test_cases": ["TC-001"] if item in {"scenario-use-case", "traceability", "accessibility-ui"} else [],
            } for item in dimensions],
        }

        with self.assertRaisesRegex(ScopeAnalyzerError, "explicit accessibility obligation"):
            _validate_legacy_detailed_decision(decision, context)

    def test_timer_measures_full_wall_and_phase(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "performance.json"
            artifact = root / "handoff" / "workflow-state.yaml"
            artifact.parent.mkdir()
            artifact.write_text("stage_status: signed-off\n", encoding="utf-8")
            with patch("test_case_agent.lean_production.epoch_ms", side_effect=[1000, 1100, 1500, 2000]):
                start_run(output, ft_slug="Demo", scope_slug="small")
                start_phase(output, phase="scope")
                finish_phase(output, phase="scope", status="completed", metrics={"input_tokens": 10})
                payload = finish_run(
                    output,
                    status="signed-off",
                    test_case_count=2,
                    artifact_roots=[artifact.parent],
                )
            self.assertEqual(1000, payload["full_user_wall_ms"])
            self.assertEqual(400, payload["phases"][0]["duration_ms"])
            self.assertEqual(1, payload["persistent_artifacts"]["file_count"])
            self.assertEqual("within-target", payload["slo_status"])
            self.assertEqual(payload, json.loads(output.read_text(encoding="utf-8")))

    def test_timer_distinguishes_request_wall_from_instrumented_wall(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            with patch("test_case_agent.lean_production.epoch_ms", side_effect=[1000, 2000]):
                start_run(
                    output,
                    ft_slug="Demo",
                    scope_slug="small",
                    request_started_epoch_ms=500,
                )
                payload = finish_run(output, status="blocked-input", test_case_count=0)

            self.assertEqual("request-received", payload["measurement_coverage"])
            self.assertEqual(1500, payload["full_user_wall_ms"])
            self.assertEqual(1000, payload["instrumented_wall_ms"])
            self.assertEqual(500, payload["pre_timer_wall_ms"])

    def test_observational_timer_has_no_limits_and_does_not_claim_full_user_wall(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            with patch("test_case_agent.lean_production.epoch_ms", side_effect=[1000, 1500, 2000]):
                start_run(
                    output,
                    ft_slug="Demo",
                    scope_slug="small",
                    request_started_epoch_ms=500,
                    request_start_source="codex-request-metadata",
                    codex_turn_id="turn-1",
                    measurement_mode="observational",
                    end_anchor="response-ready",
                    initial_phase="routing-preflight",
                )
                transition_phase(
                    output,
                    phase="routing-preflight",
                    status="completed",
                    next_phase="final-reporting",
                )
                payload = finish_run(
                    output,
                    status="signed-off",
                    test_case_count=1,
                    active_phase="final-reporting",
                )

            self.assertIsNone(payload["target_wall_ms"])
            self.assertIsNone(payload["hard_wall_ms"])
            self.assertEqual("not-evaluated", payload["slo_status"])
            self.assertEqual(1500, payload["observed_window_ms"])
            self.assertIsNone(payload["full_user_wall_ms"])
            self.assertFalse(
                payload["observation"]["coverage"]["claimable_as_full_user_wall"]
            )
            self.assertEqual(0, payload["observation"]["totals"]["unattributed_ms"])
            self.assertEqual("host-request-to-response-ready", payload["observation"]["coverage"]["label"])

    def test_observational_report_exposes_gaps_tokens_and_artifact_volume(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "performance.json"
            source = root / "source.txt"
            result = root / "result.txt"
            source.write_text("source", encoding="utf-8")
            result.write_text("result", encoding="utf-8")
            stage_metrics = {
                "contract_version": 2,
                "cycle_id": "cycle",
                "stage_id": "writer-r1",
                "attempt_id": "attempt-001",
                "backend": "exec",
                "role": "writer",
                "scenario": "prepared",
                "outcome": "completed",
                "duration_ms": 250,
                "input_artifact_count": 2,
                "input_artifact_bytes": 100,
                "output_artifact_count": 1,
                "output_artifact_bytes": 50,
                "input_tokens": 40,
                "cached_input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 60,
            }
            with patch(
                "test_case_agent.lean_production.epoch_ms",
                side_effect=[1000, 1100, 1500, 2000],
            ):
                start_run(
                    output,
                    ft_slug="Demo",
                    scope_slug="small",
                    measurement_mode="observational",
                    end_anchor="response-ready",
                    codex_turn_id="turn-1",
                )
                start_phase(output, phase="writer-reviewer", input_artifact_roots=[source])
                finish_phase(
                    output,
                    phase="writer-reviewer",
                    status="completed",
                    metrics={
                        "stage_metrics": [stage_metrics],
                        "performance": {"stage_metrics": [stage_metrics]},
                        "current_run_projection": {
                            "contract_version": 1,
                            "kind": "writer-reviewer-current-run",
                            "cycle_id": "cycle",
                            "status": "measured",
                            "attempt_count": 1,
                            "retry_count": 0,
                            "token_usage": {
                                "input_tokens": 40,
                                "cached_input_tokens": 10,
                                "output_tokens": 20,
                                "total_tokens": 60,
                            },
                            "input_artifacts": {"file_count": 2, "bytes": 100},
                            "output_artifacts": {"file_count": 1, "bytes": 50},
                            "stage_metrics": [stage_metrics],
                            "evidence": {
                                "pre_writer_snapshot": [],
                                "post_writer_snapshot": [
                                    {
                                        "identity": {
                                            "stage_id": "writer-r1",
                                            "attempt_id": "attempt-001",
                                            "role": "writer",
                                        },
                                        "path": "cycle/attempts/writer-r1/attempt-001/metrics.json",
                                        "digest": "a" * 64,
                                    }
                                ],
                                "pre_writer_snapshot_digest": (
                                    run_lean_production_iteration._metric_snapshot_digest({})
                                ),
                                "ignored_preexisting_metric_count": 0,
                                "current_run_identities": [
                                    {
                                        "stage_id": "writer-r1",
                                        "attempt_id": "attempt-001",
                                        "role": "writer",
                                    }
                                ],
                            },
                        },
                    },
                    output_artifact_roots=[result],
                )
                payload = finish_run(output, status="signed-off", test_case_count=1)

            report = build_timing_report(payload)
            self.assertEqual(600, report["phase_totals"]["unattributed_ms"])
            self.assertEqual(2, len(report["phase_totals"]["gaps"]))
            self.assertEqual(60, report["phases"][0]["token_usage"]["total_tokens"])
            self.assertEqual(2, report["phases"][0]["input_artifacts"]["file_count"])
            self.assertEqual(1, len(report["model_stages"]))

    def test_timing_report_reconciles_extended_phases_and_preflight_components(self) -> None:
        stage = {
            "contract_version": 2,
            "cycle_id": "cycle",
            "stage_id": "reviewer-r1",
            "attempt_id": "attempt-001",
            "backend": "exec",
            "role": "reviewer",
            "scenario": "reviewer.test",
            "outcome": "accepted",
            "duration_ms": 300,
            "input_artifact_count": 3,
            "input_artifact_bytes": 120,
            "output_artifact_count": 2,
            "output_artifact_bytes": 80,
            "input_tokens": 40,
            "cached_input_tokens": 5,
            "output_tokens": 12,
            "reasoning_tokens": 7,
            "total_tokens": 52,
        }
        payload = {
            "profile": "overnight",
            "ft_slug": "Demo",
            "scope_slug": "scope",
            "status": "completed",
            "observed_window_ms": 1500,
            "phases": [
                {
                    "phase": "routing-preflight",
                    "status": "completed",
                    "started_epoch_ms": 0,
                    "finished_epoch_ms": 1000,
                    "duration_ms": 1000,
                    "metrics": {
                        "routing_preflight_breakdown": [
                            {
                                "component": "request-metadata-read",
                                "duration_ms": 100,
                                "status": "measured",
                            },
                            {
                                "component": "workspace-check",
                                "duration_ms": 200,
                                "status": "measured",
                            },
                        ]
                    },
                },
                {
                    "phase": "offline-verification",
                    "status": "completed",
                    "started_epoch_ms": 1000,
                    "finished_epoch_ms": 1500,
                    "duration_ms": 500,
                    "metrics": {"stage_metrics": [stage]},
                },
            ],
            "observation": {
                "run_id": "run",
                "mode": "observational",
                "coverage": {"label": "request-to-final"},
                "totals": {
                    "observed_window_ms": 1500,
                    "phase_sum_ms": 1500,
                    "phase_union_ms": 1500,
                    "phase_overlap_ms": 0,
                    "explicit_interphase_overlap_ms": 0,
                    "unattributed_ms": 0,
                    "reconciled_observed_window_ms": 1500,
                    "reconciliation_delta_ms": 0,
                },
                "external_observations": [],
            },
        }
        report = build_timing_report(payload)
        routing = report["phases"][0]["routing_preflight_breakdown"]
        self.assertTrue(routing["reconciled"])
        other = next(
            item
            for item in routing["components"]
            if item["component"] == "other-orchestration"
        )
        self.assertEqual(700, other["duration_ms"])
        self.assertEqual(7, report["model_stages"][0]["reasoning_tokens"])
        summary = report["model_stage_summaries"][0]
        self.assertEqual(1, summary["attempt_count"])
        self.assertEqual(3, summary["input_artifact_count"])
        self.assertEqual("unavailable", report["root_agent_token_usage"]["availability"])

    def test_timing_report_does_not_double_count_shard_usage_under_parent_aggregate(
        self,
    ) -> None:
        parent_usage = {
            "input_tokens": 100,
            "cached_input_tokens": 0,
            "output_tokens": 40,
        }
        payload = {
            "status": "terminal-failed",
            "phases": [
                {
                    "phase": "semantic-design",
                    "status": "terminal-failed",
                    "duration_ms": 1000,
                    "metrics": {
                        "usage": parent_usage,
                        "sharding": {
                            "shards": [
                                {
                                    "shard_id": "semantic-shard-001",
                                    "usage": {
                                        "input_tokens": 60,
                                        "cached_input_tokens": 0,
                                        "output_tokens": 25,
                                    },
                                },
                                {
                                    "shard_id": "semantic-shard-002",
                                    "usage": {
                                        "input_tokens": 40,
                                        "cached_input_tokens": 0,
                                        "output_tokens": 15,
                                    },
                                },
                            ]
                        },
                    },
                }
            ],
        }

        report = build_timing_report(payload)

        self.assertEqual(100, report["phases"][0]["token_usage"]["input_tokens"])
        self.assertEqual(40, report["phases"][0]["token_usage"]["output_tokens"])
        self.assertEqual(140, report["phases"][0]["token_usage"]["total_tokens"])
        self.assertEqual(140, report["known_token_usage"]["total_tokens"])

    def test_timing_report_projects_standard_runner_shards_as_model_stages(
        self,
    ) -> None:
        payload = {
            "status": "terminal-failed",
            "phases": [
                {
                    "phase": "semantic-design",
                    "status": "terminal-failed",
                    "duration_ms": 1000,
                    "metrics": {
                        "usage": {
                            "input_tokens": 100,
                            "cached_input_tokens": 10,
                            "output_tokens": 40,
                            "reasoning_output_tokens": 7,
                        },
                        "stage_summary": {
                            "model_invoked": True,
                            "duration_ms": 990,
                            "usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 10,
                                "output_tokens": 40,
                                "reasoning_output_tokens": 7,
                            },
                            "lifecycle": {
                                "runner_attempt_count": 2,
                                "runner_retry_count": 0,
                            },
                            "sharding": {
                                "shards": [
                                    {
                                        "shard_id": "semantic-shard-001",
                                        "model_invoked": False,
                                        "duration_ms": 10,
                                        "usage": {
                                            "input_tokens": 0,
                                            "output_tokens": 0,
                                        },
                                    },
                                    {
                                        "shard_id": "semantic-shard-002",
                                        "model_invoked": True,
                                        "duration_ms": 400,
                                        "usage": {
                                            "input_tokens": 60,
                                            "cached_input_tokens": 5,
                                            "output_tokens": 25,
                                            "reasoning_output_tokens": 3,
                                        },
                                        "lifecycle": {"runner_attempt_count": 1},
                                        "input_artifacts": {
                                            "file_count": 3,
                                            "bytes": 120,
                                        },
                                        "output_artifacts": {
                                            "file_count": 2,
                                            "bytes": 80,
                                        },
                                    },
                                    {
                                        "shard_id": "semantic-shard-003",
                                        "model_invoked": True,
                                        "duration_ms": 500,
                                        "usage": {
                                            "input_tokens": 40,
                                            "cached_input_tokens": 5,
                                            "output_tokens": 15,
                                            "reasoning_output_tokens": 4,
                                        },
                                        "lifecycle": {"runner_attempt_count": 1},
                                        "input_artifacts": {
                                            "file_count": 4,
                                            "bytes": 140,
                                        },
                                        "output_artifacts": {
                                            "file_count": 3,
                                            "bytes": 90,
                                        },
                                    },
                                ]
                            },
                        },
                    },
                }
            ],
        }

        report = build_timing_report(payload)

        phase = report["phases"][0]
        self.assertEqual(2, phase["model_attempt_count"])
        self.assertEqual(2, len(report["model_stages"]))
        self.assertEqual(100, phase["token_usage"]["input_tokens"])
        self.assertEqual(40, phase["token_usage"]["output_tokens"])
        self.assertEqual(
            7,
            sum(item["reasoning_tokens"] for item in report["model_stages"]),
        )
        self.assertEqual(
            ["semantic-shard-002", "semantic-shard-003"],
            [item["stage_id"] for item in report["model_stages"]],
        )
        self.assertEqual(3, report["model_stages"][0]["input_artifact_count"])

    @staticmethod
    def _stage_metric(
        *,
        cycle_id: str,
        stage_id: str,
        attempt_id: str,
        role: str,
        total_tokens: int,
    ) -> dict[str, object]:
        return {
            "contract_version": 2,
            "cycle_id": cycle_id,
            "stage_id": stage_id,
            "attempt_id": attempt_id,
            "backend": "exec",
            "role": role,
            "scenario": f"{role}.test",
            "outcome": "completed",
            "duration_ms": total_tokens,
            "input_artifact_count": 2,
            "input_artifact_bytes": total_tokens * 2,
            "output_artifact_count": 1,
            "output_artifact_bytes": total_tokens,
            "input_tokens": total_tokens - 1,
            "cached_input_tokens": 0,
            "output_tokens": 1,
            "total_tokens": total_tokens,
        }

    @staticmethod
    def _write_stage_metric(cycle: Path, payload: dict[str, object]) -> Path:
        path = (
            cycle
            / "attempts"
            / str(payload["stage_id"])
            / str(payload["attempt_id"])
            / "metrics.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _writer_report(
        projection: dict[str, object],
        *,
        stale_metric: dict[str, object],
    ) -> dict[str, object]:
        return build_timing_report(
            {
                "phases": [
                    {
                        "phase": "writer-reviewer",
                        "status": "completed",
                        "duration_ms": 100,
                        "metrics": {
                            "current_run_projection": projection,
                            "stage_metrics": [stale_metric],
                            "performance": {"stage_metrics": [stale_metric]},
                            "output_artifacts": {
                                "file_count": 999,
                                "bytes": 999999,
                            },
                        },
                    }
                ]
            }
        )

    def test_reviewer_rebind_requires_only_reviewer_metric(self) -> None:
        self.assertEqual(
            frozenset({"reviewer"}),
            run_lean_production_iteration._required_current_run_model_roles(
                validate_only=False,
                iteration_completed=True,
                reviewer_rebind=True,
            ),
        )
        self.assertEqual(
            frozenset({"writer", "reviewer"}),
            run_lean_production_iteration._required_current_run_model_roles(
                validate_only=False,
                iteration_completed=True,
                reviewer_rebind=False,
            ),
        )
        for validate_only, iteration_completed in ((True, True), (False, False)):
            with self.subTest(
                validate_only=validate_only,
                iteration_completed=iteration_completed,
            ):
                self.assertEqual(
                    frozenset(),
                    run_lean_production_iteration._required_current_run_model_roles(
                        validate_only=validate_only,
                        iteration_completed=iteration_completed,
                        reviewer_rebind=True,
                    ),
                )

    def test_writer_projection_ignores_stale_metric_when_no_current_attempt_exists(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            cycle = Path(raw) / "cycle"
            stale = self._stage_metric(
                cycle_id="cycle",
                stage_id="writer-r1",
                attempt_id="attempt-001",
                role="writer",
                total_tokens=900,
            )
            self._write_stage_metric(cycle, stale)
            before, before_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )
            after, after_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )

            projection = run_lean_production_iteration._project_current_run_stage_metrics(
                cycle_dir=cycle,
                preexisting=before,
                current=after,
                preexisting_error=before_error,
                current_error=after_error,
            )
            report = self._writer_report(projection, stale_metric=stale)

            self.assertEqual("unknown", projection["status"])
            self.assertIsNone(report["known_token_usage"]["total_tokens"])
            self.assertEqual([], report["model_stages"])
            self.assertIsNone(report["phases"][0]["output_artifacts"]["file_count"])

    def test_writer_projection_counts_only_fresh_metrics_not_stale_performance(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            cycle = Path(raw) / "cycle"
            stale = self._stage_metric(
                cycle_id="cycle",
                stage_id="writer-r1",
                attempt_id="attempt-001",
                role="writer",
                total_tokens=900,
            )
            self._write_stage_metric(cycle, stale)
            before, before_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )
            fresh_writer = self._stage_metric(
                cycle_id="cycle",
                stage_id="writer-r1",
                attempt_id="attempt-002",
                role="writer",
                total_tokens=30,
            )
            fresh_reviewer = self._stage_metric(
                cycle_id="cycle",
                stage_id="reviewer-r1",
                attempt_id="attempt-001",
                role="reviewer",
                total_tokens=40,
            )
            self._write_stage_metric(cycle, fresh_writer)
            self._write_stage_metric(cycle, fresh_reviewer)
            after, after_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )

            projection = run_lean_production_iteration._project_current_run_stage_metrics(
                cycle_dir=cycle,
                preexisting=before,
                current=after,
                preexisting_error=before_error,
                current_error=after_error,
                required_roles=frozenset({"writer", "reviewer"}),
            )
            projection["input_artifacts"] = {"file_count": -1, "bytes": 999999}
            projection["output_artifacts"] = {"file_count": 999, "bytes": -1}
            report = self._writer_report(projection, stale_metric=stale)

            self.assertEqual("measured", projection["status"])
            self.assertEqual(2, projection["attempt_count"])
            self.assertEqual(1, projection["retry_count"])
            self.assertEqual(70, report["known_token_usage"]["total_tokens"])
            self.assertEqual(2, len(report["model_stages"]))
            self.assertEqual(4, report["phases"][0]["input_artifacts"]["file_count"])
            self.assertEqual(2, report["phases"][0]["output_artifacts"]["file_count"])

    def test_writer_projection_does_not_publish_partial_token_sum_as_exact(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            cycle = Path(raw) / "cycle"
            before, before_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )
            writer = self._stage_metric(
                cycle_id="cycle",
                stage_id="writer-r1",
                attempt_id="attempt-001",
                role="writer",
                total_tokens=30,
            )
            writer["input_tokens"] = None
            writer["total_tokens"] = None
            reviewer = self._stage_metric(
                cycle_id="cycle",
                stage_id="reviewer-r1",
                attempt_id="attempt-001",
                role="reviewer",
                total_tokens=40,
            )
            self._write_stage_metric(cycle, writer)
            self._write_stage_metric(cycle, reviewer)
            after, after_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )

            projection = run_lean_production_iteration._project_current_run_stage_metrics(
                cycle_dir=cycle,
                preexisting=before,
                current=after,
                preexisting_error=before_error,
                current_error=after_error,
                required_roles=frozenset({"writer", "reviewer"}),
            )
            report = self._writer_report(projection, stale_metric=reviewer)

            self.assertEqual("measured", projection["status"])
            self.assertIsNone(projection["token_usage"]["input_tokens"])
            self.assertIsNone(projection["token_usage"]["total_tokens"])
            self.assertIsNone(report["phases"][0]["token_usage"]["total_tokens"])

    def test_timing_report_rejects_duplicate_or_evidence_mismatched_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            cycle = Path(raw) / "cycle"
            before, before_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )
            writer = self._stage_metric(
                cycle_id="cycle",
                stage_id="writer-r1",
                attempt_id="attempt-001",
                role="writer",
                total_tokens=30,
            )
            reviewer = self._stage_metric(
                cycle_id="cycle",
                stage_id="reviewer-r1",
                attempt_id="attempt-001",
                role="reviewer",
                total_tokens=40,
            )
            self._write_stage_metric(cycle, writer)
            self._write_stage_metric(cycle, reviewer)
            after, after_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )
            valid = run_lean_production_iteration._project_current_run_stage_metrics(
                cycle_dir=cycle,
                preexisting=before,
                current=after,
                preexisting_error=before_error,
                current_error=after_error,
                required_roles=frozenset({"writer", "reviewer"}),
            )
            duplicate = copy.deepcopy(valid)
            duplicate["stage_metrics"].append(copy.deepcopy(duplicate["stage_metrics"][0]))
            duplicate["attempt_count"] = 3
            mismatched = copy.deepcopy(valid)
            mismatched["evidence"]["current_run_identities"] = [
                mismatched["evidence"]["current_run_identities"][0]
            ]

            for label, projection in (
                ("duplicate", duplicate),
                ("evidence-mismatch", mismatched),
            ):
                with self.subTest(label=label):
                    report = self._writer_report(projection, stale_metric=reviewer)
                    phase = report["phases"][0]
                    self.assertEqual("unknown", phase["model_measurement_status"])
                    self.assertIsNone(phase["token_usage"]["total_tokens"])
                    self.assertIsNone(phase["input_artifacts"]["file_count"])
                    self.assertIsNone(phase["output_artifacts"]["bytes"])
                    self.assertEqual([], report["model_stages"])

    def test_writer_projection_is_unknown_after_metric_overwrite_or_deletion(self) -> None:
        for mutation in ("overwrite", "delete"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as raw:
                cycle = Path(raw) / "cycle"
                stale = self._stage_metric(
                    cycle_id="cycle",
                    stage_id="writer-r1",
                    attempt_id="attempt-001",
                    role="writer",
                    total_tokens=20,
                )
                path = self._write_stage_metric(cycle, stale)
                before, before_error = (
                    run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
                )
                if mutation == "overwrite":
                    overwritten = {**stale, "total_tokens": 21}
                    path.write_text(json.dumps(overwritten) + "\n", encoding="utf-8")
                else:
                    path.unlink()
                after, after_error = (
                    run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
                )

                projection = (
                    run_lean_production_iteration._project_current_run_stage_metrics(
                        cycle_dir=cycle,
                        preexisting=before,
                        current=after,
                        preexisting_error=before_error,
                        current_error=after_error,
                    )
                )

                self.assertEqual("unknown", projection["status"])
                self.assertIsNone(projection["attempt_count"])
                self.assertEqual([], projection["stage_metrics"])
                self.assertIn("deleted or overwritten", projection["measurement_error"])

    def test_writer_projection_accepts_only_explicit_snapshot_bound_zero_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            cycle = Path(raw) / "cycle"
            stale = self._stage_metric(
                cycle_id="cycle",
                stage_id="writer-r1",
                attempt_id="attempt-001",
                role="writer",
                total_tokens=500,
            )
            self._write_stage_metric(cycle, stale)
            before, before_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )
            after, after_error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )
            assert before is not None
            receipt = {
                "contract_version": 1,
                "kind": "writer-reviewer-current-run-reuse",
                "status": "reused",
                "cycle_id": "cycle",
                "attempt_count": 0,
                "retry_count": 0,
                "token_usage": {
                    "input_tokens": 0,
                    "cached_input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                },
                "pre_writer_snapshot_digest": (
                    run_lean_production_iteration._metric_snapshot_digest(before)
                ),
            }

            projection = run_lean_production_iteration._project_current_run_stage_metrics(
                cycle_dir=cycle,
                preexisting=before,
                current=after,
                preexisting_error=before_error,
                current_error=after_error,
                explicit_reuse_receipt=receipt,
            )
            report = self._writer_report(projection, stale_metric=stale)

            self.assertEqual("reused", projection["status"])
            self.assertEqual(0, projection["attempt_count"])
            self.assertEqual(0, projection["retry_count"])
            self.assertEqual(0, report["known_token_usage"]["total_tokens"])
            self.assertEqual([], report["model_stages"])
            self.assertEqual(0, report["phases"][0]["output_artifacts"]["file_count"])

    def test_writer_metric_snapshot_rejects_attempt_zero_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            cycle = Path(raw) / "cycle"
            invalid = self._stage_metric(
                cycle_id="cycle",
                stage_id="writer-r1",
                attempt_id="attempt-000",
                role="writer",
                total_tokens=10,
            )
            self._write_stage_metric(cycle, invalid)

            snapshot, error = (
                run_lean_production_iteration._snapshot_writer_reviewer_metrics(cycle)
            )

            self.assertIsNone(snapshot)
            self.assertIn("attempt_id is not canonical", str(error))

    def test_external_ui_reconciliation_is_append_only_and_claims_user_wall(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            with patch("test_case_agent.lean_production.epoch_ms", side_effect=[1000, 2000]):
                start_run(
                    output,
                    ft_slug="Demo",
                    scope_slug="small",
                    measurement_mode="observational",
                    end_anchor="response-ready",
                    codex_turn_id="turn-1",
                )
                finish_run(output, status="signed-off", test_case_count=1)

            first = reconcile_external_elapsed(
                output,
                elapsed_ms=2500,
                source="codex-ui-display",
                endpoint="ui-final",
                precision_ms=1000,
                claim_full_user_wall=True,
            )
            second = reconcile_external_elapsed(
                output,
                elapsed_ms=2500,
                source="codex-ui-display",
                endpoint="ui-final",
                precision_ms=1000,
                claim_full_user_wall=True,
            )
            exact = reconcile_external_elapsed(
                output,
                elapsed_ms=2450,
                source="codex-rollout-task-complete",
                endpoint="task-complete",
                precision_ms=1,
                turn_id="turn-1",
                claim_full_user_wall=True,
            )
            self.assertEqual(2500, first["full_user_wall_ms"])
            self.assertTrue(first["observation"]["coverage"]["claimable_as_full_user_wall"])
            self.assertEqual(1500, first["observation"]["external_observations"][0]["apparent_delta_ms"])
            self.assertEqual(1, len(second["observation"]["external_observations"]))
            self.assertEqual(2450, exact["full_user_wall_ms"])

    def test_codex_turn_reconciliation_reads_task_complete_without_message_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "performance.json"
            sessions = root / "sessions"
            sessions.mkdir()
            with patch("test_case_agent.lean_production.epoch_ms", side_effect=[1000, 2000]):
                start_run(
                    output,
                    ft_slug="Demo",
                    scope_slug="small",
                    measurement_mode="observational",
                    codex_turn_id="turn-1",
                    end_anchor="response-ready",
                    initial_phase="routing-preflight",
                )
                finish_run(
                    output,
                    status="signed-off",
                    test_case_count=1,
                    active_phase="routing-preflight",
                )
            started_event = {
                "timestamp": "1970-01-01T00:00:01.000Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "turn-1"},
            }
            token_event = {
                "timestamp": "1970-01-01T00:00:01.500Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {
                            "input_tokens": 100,
                            "cached_input_tokens": 80,
                            "cache_write_input_tokens": 0,
                            "output_tokens": 20,
                            "reasoning_output_tokens": 5,
                            "total_tokens": 120,
                        }
                    },
                },
            }
            complete_event = {
                "timestamp": "1970-01-01T00:00:04.200Z",
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "turn_id": "turn-1",
                    "duration_ms": 3200,
                    "started_at": 1,
                    "completed_at": 4,
                    "time_to_first_token_ms": 25,
                    "last_agent_message": "must not be copied",
                },
            }
            (sessions / "rollout.jsonl").write_text(
                "\n".join(
                    json.dumps(event, ensure_ascii=False)
                    for event in (started_event, token_event, complete_event)
                )
                + "\n",
                encoding="utf-8",
            )

            payload = reconcile_codex_turn(output, sessions_root=sessions)

            observation = payload["observation"]["external_observations"][0]
            self.assertEqual(3200, payload["full_user_wall_ms"])
            self.assertEqual(25, observation["time_to_first_token_ms"])
            self.assertNotIn("last_agent_message", observation)
            self.assertEqual(
                120,
                observation["root_agent_token_usage"]["by_phase"]["routing-preflight"][
                    "total_tokens"
                ],
            )

    def test_external_observation_needs_explicit_valid_claim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            with patch("test_case_agent.lean_production.epoch_ms", side_effect=[1000, 2000]):
                start_run(
                    output,
                    ft_slug="Demo",
                    scope_slug="small",
                    measurement_mode="observational",
                    codex_turn_id="turn-1",
                    end_anchor="pre-final-response",
                )
                finish_run(output, status="signed-off", test_case_count=1)

            passive = reconcile_external_elapsed(
                output,
                elapsed_ms=2500,
                source="user-note",
                endpoint="ui-final",
            )
            self.assertIsNone(passive["full_user_wall_ms"])
            self.assertFalse(
                passive["observation"]["coverage"]["claimable_as_full_user_wall"]
            )
            with self.assertRaisesRegex(LeanProductionError, "turn_id does not match"):
                reconcile_external_elapsed(
                    output,
                    elapsed_ms=2500,
                    source="codex-ui-display",
                    endpoint="ui-final",
                    turn_id="turn-2",
                    claim_full_user_wall=True,
                )
            with self.assertRaisesRegex(LeanProductionError, "cannot be shorter"):
                reconcile_external_elapsed(
                    output,
                    elapsed_ms=900,
                    source="codex-ui-display",
                    endpoint="ui-final",
                    turn_id="turn-1",
                    claim_full_user_wall=True,
                )

    def test_observational_cli_start_transition_finish_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            timer = root / "performance.json"
            report_json = root / "report.json"
            report_markdown = root / "report.md"
            stdout = io.StringIO()
            with (
                patch("test_case_agent.lean_production.epoch_ms", side_effect=[1000, 1500, 2000]),
                redirect_stdout(stdout),
            ):
                self.assertEqual(
                    0,
                    workflow_wall_clock.main(
                        [
                            "start",
                            "--output", str(timer),
                            "--ft-slug", "Demo",
                            "--scope-slug", "small",
                            "--measurement-mode", "observational",
                            "--end-anchor", "pre-final-response",
                            "--initial-phase", "routing-preflight",
                        ]
                    ),
                )
                self.assertEqual(
                    0,
                    workflow_wall_clock.main(
                        [
                            "transition",
                            "--output", str(timer),
                            "--phase", "routing-preflight",
                            "--status", "completed",
                            "--next-phase", "final-reporting",
                        ]
                    ),
                )
                self.assertEqual(
                    0,
                    workflow_wall_clock.main(
                        [
                            "finish",
                            "--output", str(timer),
                            "--status", "signed-off",
                            "--test-case-count", "1",
                            "--active-phase", "final-reporting",
                            "--compact",
                        ]
                    ),
                )
            with redirect_stdout(stdout):
                self.assertEqual(
                    0,
                    workflow_wall_clock.main(
                        [
                            "report",
                            "--output", str(timer),
                            "--json-output", str(report_json),
                            "--markdown-output", str(report_markdown),
                        ]
                    ),
                )
            payload = json.loads(timer.read_text(encoding="utf-8"))
            self.assertEqual("not-evaluated", payload["slo_status"])
            self.assertTrue(report_json.is_file())
            self.assertIn("Наблюдение полного времени", report_markdown.read_text(encoding="utf-8"))

    def test_reconcile_report_returns_pending_without_mutating_timer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sessions = root / "sessions"
            sessions.mkdir()
            timer = root / "performance.json"
            report_json = root / "timing-report.json"
            report_markdown = root / "timing-report.md"
            with patch(
                "test_case_agent.lean_production.epoch_ms",
                side_effect=[1000, 2000],
            ):
                start_run(
                    timer,
                    ft_slug="Demo",
                    scope_slug="small",
                    measurement_mode="observational",
                    codex_turn_id="turn-pending",
                    end_anchor="pre-final-response",
                )
                finish_run(timer, status="blocked-input", test_case_count=0)
            before = timer.read_bytes()
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = workflow_wall_clock.main(
                    [
                        "reconcile-report",
                        "--output", str(timer),
                        "--sessions-root", str(sessions),
                        "--json-output", str(report_json),
                        "--markdown-output", str(report_markdown),
                    ]
                )

            pending = json.loads(stdout.getvalue())
            self.assertEqual(3, code)
            self.assertEqual("pending-task-complete", pending["status"])
            self.assertEqual("turn-pending", pending["turn_id"])
            self.assertIsNone(pending["full_user_wall_ms"])
            self.assertFalse(pending["timer_mutated"])
            self.assertFalse(pending["reports_written"])
            self.assertEqual(before, timer.read_bytes())
            self.assertFalse(report_json.exists())
            self.assertFalse(report_markdown.exists())

    def test_reconcile_report_reconciles_and_writes_both_reports_once(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sessions = root / "sessions"
            sessions.mkdir()
            timer = root / "performance.json"
            report_json = root / "timing-report.json"
            report_markdown = root / "timing-report.md"
            with patch(
                "test_case_agent.lean_production.epoch_ms",
                side_effect=[1000, 2000],
            ):
                start_run(
                    timer,
                    ft_slug="Demo",
                    scope_slug="small",
                    measurement_mode="observational",
                    codex_turn_id="turn-complete",
                    end_anchor="pre-final-response",
                )
                finish_run(timer, status="signed-off", test_case_count=2)
            events = (
                {
                    "timestamp": "1970-01-01T00:00:01.000Z",
                    "type": "event_msg",
                    "payload": {"type": "task_started", "turn_id": "turn-complete"},
                },
                {
                    "timestamp": "1970-01-01T00:00:04.200Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "turn_id": "turn-complete",
                        "duration_ms": 3200,
                        "started_at": 1,
                        "completed_at": 4,
                        "time_to_first_token_ms": 25,
                    },
                },
            )
            rollout = sessions / "rollout.jsonl"
            rollout.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = workflow_wall_clock.main(
                    [
                        "reconcile-report",
                        "--output", str(timer),
                        "--sessions-root", str(sessions),
                        "--json-output", str(report_json),
                        "--markdown-output", str(report_markdown),
                    ]
                )

            self.assertEqual(0, code)
            report = json.loads(report_json.read_text(encoding="utf-8"))
            self.assertEqual(3200, report["full_user_wall_ms"])
            self.assertEqual(2, report["test_case_count"])
            self.assertIn(
                "Полное пользовательское время: `0:03.200`",
                report_markdown.read_text(encoding="utf-8"),
            )
            reconciled = json.loads(timer.read_text(encoding="utf-8"))
            self.assertEqual(3200, reconciled["full_user_wall_ms"])
            self.assertEqual(
                1,
                len(reconciled["observation"]["external_observations"]),
            )

            rollout.unlink()
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                repeated_code = workflow_wall_clock.main(
                    [
                        "reconcile-report",
                        "--output", str(timer),
                        "--sessions-root", str(root / "missing-sessions"),
                        "--json-output", str(report_json),
                        "--markdown-output", str(report_markdown),
                    ]
                )
            repeated = json.loads(timer.read_text(encoding="utf-8"))
            self.assertEqual(0, repeated_code)
            self.assertEqual(
                1,
                len(repeated["observation"]["external_observations"]),
            )

    def test_terminalize_closes_active_phase_and_records_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            with patch(
                "test_case_agent.lean_production.epoch_ms",
                side_effect=[1000, 1100, 1500],
            ):
                start_run(output, ft_slug="Demo", scope_slug="small")
                start_phase(output, phase="scope")
                payload = terminalize_run(
                    output,
                    status="terminal-failed",
                    error_type="TimeoutError",
                    error="scope timed out",
                )

            self.assertEqual("terminal-failed", payload["status"])
            self.assertEqual("terminal-failed", payload["phases"][0]["status"])
            self.assertEqual(400, payload["phases"][0]["duration_ms"])
            self.assertEqual("TimeoutError", payload["terminal"]["error_type"])

    def test_terminalize_can_use_exact_historical_completion_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            with patch(
                "test_case_agent.lean_production.epoch_ms",
                side_effect=[1000, 1100],
            ):
                start_run(
                    output,
                    ft_slug="AutoFin",
                    scope_slug="employment-main-work",
                    measurement_mode="observational",
                    request_started_epoch_ms=900,
                    codex_turn_id="turn-1",
                    initial_phase="routing-preflight",
                )
                payload = terminalize_run(
                    output,
                    status="terminal-failed",
                    error_type="root-model-capacity",
                    error="selected model is at capacity",
                    finished_epoch_ms=1500,
                )

            self.assertEqual(1500, payload["finished_epoch_ms"])
            self.assertEqual(600, payload["observed_window_ms"])
            self.assertEqual(600, payload["phases"][0]["duration_ms"])
            self.assertEqual(
                "root-model-capacity", payload["terminal"]["error_type"]
            )

    def test_terminalize_rejects_historical_boundary_before_active_phase(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            with patch(
                "test_case_agent.lean_production.epoch_ms",
                side_effect=[1000, 1200],
            ):
                start_run(output, ft_slug="AutoFin", scope_slug="employment-main-work")
                start_phase(output, phase="source-selection")
            with self.assertRaisesRegex(
                LeanProductionError, "cannot precede the workflow or an active phase"
            ):
                terminalize_run(
                    output,
                    status="terminal-failed",
                    error_type="root-model-capacity",
                    error="selected model is at capacity",
                    finished_epoch_ms=1100,
                )

    def test_cannot_finish_with_running_phase(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            start_run(output, ft_slug="Demo", scope_slug="small")
            start_phase(output, phase="scope")
            with self.assertRaises(LeanProductionError):
                finish_run(output, status="blocked", test_case_count=0)

    def test_cannot_finish_terminal_timer_twice(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "performance.json"
            start_run(output, ft_slug="Demo", scope_slug="small")
            finish_run(output, status="signed-off", test_case_count=1)
            first = json.loads(output.read_text(encoding="utf-8"))

            with self.assertRaisesRegex(LeanProductionError, "terminal workflow timer"):
                finish_run(output, status="signed-off", test_case_count=1)

            self.assertEqual(first, json.loads(output.read_text(encoding="utf-8")))

    def test_handoff_audit_rejects_process_noise(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            required = {
                "workflow-state.yaml",
                "source-selection.md",
                "scope-contract.md",
                "scope-coverage-gaps.md",
                "source-row-extraction-spec.json",
                "source-row-baseline.json",
                "source-row-inventory.md",
                "source-assertions.json",
                "atomic-requirements-ledger.md",
                "coverage-obligation-table.md",
                "package-test-design-plan.md",
                "test-design-applicability-matrix.md",
            }
            for name in required:
                (root / name).write_text("{}\n" if name.endswith(".json") else "# x\n", encoding="utf-8")
            self.assertEqual("pass", audit_handoff(root)["status"])
            (root / "scope-analyzer-session-log.md").write_text("# log\n", encoding="utf-8")
            result = audit_handoff(root)
            self.assertEqual("fail", result["status"])
            self.assertIn("scope-analyzer-session-log.md", result["forbidden_success_artifacts"])

    def test_one_command_iteration_needs_no_saved_dispatcher_config(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            ft = repo / "fts" / "Demo"
            handoff = ft / "work" / "stage-handoffs" / "01-small"
            cycle = ft / "work" / "review-cycles" / "small"
            handoff.mkdir(parents=True)
            keys = {
                "source_selection": "source-selection.md",
                "source_row_inventory": "source-row-inventory.md",
                "source_row_extraction_spec": "source-row-extraction-spec.json",
                "source_row_baseline": "source-row-baseline.json",
                "source_assertions": "source-assertions.json",
                "source_gate_validation": "source-gate-validation.json",
                "source_assertion_review": "source-assertion-review.json",
                "atomic_requirements_ledger": "atomic-requirements-ledger.md",
                "coverage_obligation_table": "coverage-obligation-table.md",
                "package_test_design_plan": "package-test-design-plan.md",
                "test_design_applicability_matrix": "test-design-applicability-matrix.md",
                "active_transition_prompt": "prompt.scope-assertions-to-reviewer.md",
            }
            for key, name in keys.items():
                if key == "source_assertion_review":
                    continue
                path = handoff / name
                if key == "source_assertions":
                    path.write_text(
                        '{"source_rows":[],"assertions":[]}\n',
                        encoding="utf-8",
                    )
                else:
                    path.write_text(
                        "{}\n" if path.suffix == ".json" else "# x\n",
                        encoding="utf-8",
                    )
            latest = "\n".join(
                f"  {key}: work/stage-handoffs/01-small/{name}"
                for key, name in keys.items()
            )
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Demo",
                        "scope_slug: small",
                        'section_id: "1"',
                        "current_stage: ft-test-case-iteration",
                        "stage_status: runnable",
                        "next_skill: ft-test-case-iteration",
                        "latest_artifacts:",
                        latest,
                        "blocking_reasons: []",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            compiled = SimpleNamespace(
                obligation_count=1,
                gap_count=0,
                cache_reused=False,
            )
            cycle.mkdir(parents=True)
            (cycle / "cycle-state.yaml").write_text(
                "\n".join(
                    [
                        "workflow_status: accepted-not-promoted",
                        "stage_status: accepted-not-promoted",
                        "current_stage: reviewer-r1",
                        "writer_stage_status: completed",
                        "reviewer_stage_status: accepted",
                        "accepted_terminal_state: true",
                        "final_promoted: false",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            codex_path = (repo / "tools" / "codex.exe").resolve()
            capability = ExecCapability(
                command=str(codex_path),
                available=True,
                verified=True,
                returncode=0,
                duration_ms=3,
                missing_flags=(),
                version="codex-cli test",
                resolved_command=str(codex_path),
            )
            resolution = ExecCapabilityResolution(
                requested_command="",
                probes=(capability,),
                selected=capability,
                disable_features=("remote_plugin", "plugins", "apps"),
            )
            unavailable = ExecCapability(
                command="codex",
                available=False,
                verified=False,
                returncode=None,
                duration_ms=1,
                missing_flags=("--json",),
                error="not available",
            )
            failed_resolution = ExecCapabilityResolution(
                requested_command="",
                probes=(unavailable,),
                selected=None,
                disable_features=("remote_plugin", "plugins", "apps"),
            )

            def source_review(argv):
                Path(argv[argv.index("--receipt-output") + 1]).write_text(
                    "{}\n", encoding="utf-8"
                )
                Path(argv[argv.index("--summary-output") + 1]).write_text(
                    '{"status":"accepted"}\n', encoding="utf-8"
                )
                return 0

            with (
                patch.object(
                    run_lean_production_iteration,
                    "resolve_verified_exec_capability",
                    return_value=failed_resolution,
                ),
                patch.object(
                    run_lean_production_iteration,
                    "source_review_main",
                ) as blocked_source,
                patch.object(
                    run_lean_production_iteration,
                    "review_cycle_main",
                ) as blocked_review,
            ):
                blocked_code = run_lean_production_iteration.main(
                    [
                        "--repo-root", str(repo),
                        "--workflow-state", str(workflow.relative_to(repo)),
                        "--cycle-dir", str(cycle.relative_to(repo)),
                        "--final-artifact", "fts/Demo/test-cases/1-small.md",
                    ]
                )
            self.assertEqual(2, blocked_code)
            blocked_source.assert_not_called()
            blocked_review.assert_not_called()

            with (
                patch.object(
                    run_lean_production_iteration,
                    "resolve_verified_exec_capability",
                    return_value=resolution,
                ) as resolver,
                patch.object(
                    run_lean_production_iteration,
                    "source_review_main",
                    side_effect=source_review,
                ) as source_review_call,
                patch.object(
                    run_lean_production_iteration,
                    "resolve_workflow_compiler_inputs",
                    return_value={"workflow_state": workflow},
                ),
                patch.object(run_lean_production_iteration, "compile_workflow_package", return_value=compiled),
                patch.object(run_lean_production_iteration, "review_cycle_main", return_value=0) as review,
                patch.object(run_lean_production_iteration, "promote_main", return_value=0),
            ):
                code = run_lean_production_iteration.main(
                    [
                        "--repo-root", str(repo),
                        "--workflow-state", str(workflow.relative_to(repo)),
                        "--cycle-dir", str(cycle.relative_to(repo)),
                        "--final-artifact", "fts/Demo/test-cases/1-small.md",
                    ]
                )
            self.assertEqual(0, code)
            runner_args = review.call_args.args[0]
            self.assertNotIn("--config", runner_args)
            self.assertIn("--prepared-package", runner_args)
            reviewer_context_limit_index = runner_args.index(
                "--prepared-standard-reviewer-context-max-bytes"
            )
            self.assertEqual(
                str(512 * 1024),
                runner_args[reviewer_context_limit_index + 1],
            )
            writer_context_limit_index = runner_args.index(
                "--prepared-standard-writer-context-max-bytes"
            )
            self.assertEqual(
                str(128 * 1024),
                runner_args[writer_context_limit_index + 1],
            )
            resolver.assert_called_once()
            self.assertIsNone(resolver.call_args.args[0])
            source_args = source_review_call.call_args.args[0]
            self.assertEqual(
                str(codex_path),
                source_args[source_args.index("--codex-command") + 1],
            )
            self.assertEqual(
                str(codex_path),
                runner_args[runner_args.index("--codex-command") + 1],
            )
            self.assertEqual(
                "900",
                source_args[source_args.index("--timeout-seconds") + 1],
            )
            self.assertEqual(
                "600",
                runner_args[runner_args.index("--writer-timeout-seconds") + 1],
            )
            self.assertEqual(
                "600",
                runner_args[runner_args.index("--reviewer-timeout-seconds") + 1],
            )
            self.assertEqual(
                "1",
                runner_args[
                    runner_args.index("--prepared-structured-writer-max-concurrency")
                    + 1
                ],
            )
            self.assertEqual(3, runner_args.count("--extra-arg=--disable"))
            for feature in ("remote_plugin", "plugins", "apps"):
                self.assertIn(f"--extra-arg={feature}", runner_args)
            self.assertNotIn("codex", source_args)
            self.assertNotIn("codex", runner_args)

            stale_writer_metric = self._stage_metric(
                cycle_id="small",
                stage_id="writer-r1",
                attempt_id="attempt-001",
                role="writer",
                total_tokens=700,
            )
            self._write_stage_metric(cycle, stale_writer_metric)
            (cycle / "performance.json").write_text(
                json.dumps(
                    {"stage_metrics": [stale_writer_metric], "total_tokens": 700}
                )
                + "\n",
                encoding="utf-8",
            )
            repeat_timer = repo / "repeat-performance.json"
            start_run(
                repeat_timer,
                ft_slug="Demo",
                scope_slug="small",
                measurement_mode="observational",
            )
            persisted_source_summary = cycle / "source-review-summary.json"
            persisted_before = persisted_source_summary.read_bytes()
            with (
                patch.object(
                    run_lean_production_iteration,
                    "resolve_verified_exec_capability",
                    return_value=resolution,
                ),
                patch.object(
                    run_lean_production_iteration,
                    "source_review_main",
                ) as repeated_source_review,
                patch.object(
                    run_lean_production_iteration,
                    "resolve_workflow_compiler_inputs",
                    return_value={"workflow_state": workflow},
                ),
                patch.object(
                    run_lean_production_iteration,
                    "compile_workflow_package",
                    return_value=compiled,
                ),
                patch.object(
                    run_lean_production_iteration,
                    "review_cycle_main",
                    return_value=0,
                ),
                patch.object(
                    run_lean_production_iteration,
                    "promote_main",
                    return_value=0,
                ),
            ):
                repeat_code = run_lean_production_iteration.main(
                    [
                        "--repo-root", str(repo),
                        "--workflow-state", str(workflow.relative_to(repo)),
                        "--cycle-dir", str(cycle.relative_to(repo)),
                        "--final-artifact", "fts/Demo/test-cases/1-small.md",
                        "--timer", str(repeat_timer),
                        "--defer-timer-finish",
                    ]
                )
            self.assertEqual(0, repeat_code)
            repeated_source_review.assert_not_called()
            self.assertEqual(persisted_before, persisted_source_summary.read_bytes())
            repeat_payload = json.loads(repeat_timer.read_text(encoding="utf-8"))
            source_phase = next(
                item
                for item in repeat_payload["phases"]
                if item["phase"] == "source-review"
            )
            reuse_summary = source_phase["metrics"]["summary"]
            self.assertEqual("reused", reuse_summary["status"])
            self.assertEqual(0, reuse_summary["attempt_count"])
            self.assertEqual(0, reuse_summary["retry_count"])
            writer_phase = next(
                item
                for item in repeat_payload["phases"]
                if item["phase"] == "writer-reviewer"
            )
            self.assertNotIn("performance", writer_phase["metrics"])
            self.assertEqual(
                "unknown",
                writer_phase["metrics"]["current_run_projection"]["status"],
            )
            self.assertEqual([], writer_phase["metrics"]["stage_metrics"])
            self.assertTrue(
                writer_phase["metrics"]["excluded_historical_performance"][
                    "excluded_from_current_run_projection"
                ]
            )
            repeat_report = build_timing_report(repeat_payload)
            repeat_writer = next(
                item
                for item in repeat_report["phases"]
                if item["phase"] == "writer-reviewer"
            )
            self.assertIsNone(repeat_writer["token_usage"]["total_tokens"])

    def test_one_command_iteration_rejects_cross_ft_paths_before_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            ft_a = repo / "fts" / "A"
            ft_b = repo / "fts" / "B"
            workflow_a = ft_a / "work" / "stage-handoffs" / "01-scope" / "workflow-state.yaml"
            workflow_a.parent.mkdir(parents=True)
            (ft_b / "work" / "review-cycles").mkdir(parents=True)
            workflow_a.write_text(
                "ft_slug: B\n"
                "scope_slug: scope\n"
                'section_id: "1"\n',
                encoding="utf-8",
            )
            with (
                patch.object(
                    run_lean_production_iteration,
                    "resolve_verified_exec_capability",
                ) as backend,
                patch.object(
                    run_lean_production_iteration,
                    "source_gate_main",
                ) as source_gate,
                patch.object(
                    run_lean_production_iteration,
                    "source_review_main",
                ) as source_review,
                patch.object(
                    run_lean_production_iteration,
                    "review_cycle_main",
                ) as review_cycle,
            ):
                code = run_lean_production_iteration.main(
                    [
                        "--repo-root", str(repo),
                        "--workflow-state", str(workflow_a),
                        "--cycle-dir", str(ft_b / "work" / "review-cycles" / "scope"),
                        "--final-artifact", str(ft_b / "test-cases" / "1-scope.md"),
                    ]
                )
            self.assertEqual(2, code)
            backend.assert_not_called()
            source_gate.assert_not_called()
            source_review.assert_not_called()
            review_cycle.assert_not_called()

    def test_one_command_iteration_rejects_cross_ft_cycle_and_final_before_backend(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            ft_a = repo / "fts" / "A"
            ft_b = repo / "fts" / "B"
            workflow = ft_a / "work" / "stage-handoffs" / "01-scope" / "workflow-state.yaml"
            workflow.parent.mkdir(parents=True)
            (ft_a / "work" / "review-cycles").mkdir(parents=True)
            (ft_b / "work" / "review-cycles").mkdir(parents=True)
            workflow.write_text(
                "ft_slug: A\n"
                "scope_slug: scope\n"
                'section_id: "1"\n',
                encoding="utf-8",
            )
            invalid_pairs = (
                (
                    ft_b / "work" / "review-cycles" / "scope",
                    ft_a / "test-cases" / "1-scope.md",
                ),
                (
                    ft_a / "work" / "review-cycles" / "scope",
                    ft_b / "test-cases" / "1-scope.md",
                ),
            )
            for cycle, final in invalid_pairs:
                with (
                    self.subTest(cycle=cycle, final=final),
                    patch.object(
                        run_lean_production_iteration,
                        "resolve_verified_exec_capability",
                    ) as backend,
                    patch.object(
                        run_lean_production_iteration,
                        "source_gate_main",
                    ) as source_gate,
                    patch.object(
                        run_lean_production_iteration,
                        "source_review_main",
                    ) as source_review,
                ):
                    code = run_lean_production_iteration.main(
                        [
                            "--repo-root", str(repo),
                            "--workflow-state", str(workflow),
                            "--cycle-dir", str(cycle),
                            "--final-artifact", str(final),
                        ]
                    )
                self.assertEqual(2, code)
                backend.assert_not_called()
                source_gate.assert_not_called()
                source_review.assert_not_called()

    def test_one_command_iteration_terminalizes_timer_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            timer = repo / "performance.json"
            start_run(timer, ft_slug="Demo", scope_slug="small")

            code = run_lean_production_iteration.main(
                [
                    "--repo-root", str(repo),
                    "--workflow-state", "fts/Demo/work/stage-handoffs/missing/workflow-state.yaml",
                    "--cycle-dir", "fts/Demo/work/review-cycles/missing",
                    "--final-artifact", "fts/Demo/test-cases/1-small.md",
                    "--timer", str(timer),
                ]
            )

            self.assertEqual(2, code)
            payload = json.loads(timer.read_text(encoding="utf-8"))
            self.assertEqual("blocked", payload["status"])
            self.assertIsInstance(payload["full_user_wall_ms"], int)
            self.assertEqual(0, payload["test_case_count"])

    def test_one_command_iteration_can_leave_caller_owned_timer_running_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            timer = repo / "performance.json"
            start_run(
                timer,
                ft_slug="Demo",
                scope_slug="small",
                measurement_mode="observational",
                end_anchor="response-ready",
            )

            code = run_lean_production_iteration.main(
                [
                    "--repo-root", str(repo),
                    "--workflow-state", "fts/Demo/work/stage-handoffs/missing/workflow-state.yaml",
                    "--cycle-dir", "fts/Demo/work/review-cycles/missing",
                    "--final-artifact", "fts/Demo/test-cases/1-small.md",
                    "--timer", str(timer),
                    "--defer-timer-finish",
                ]
            )

            self.assertEqual(2, code)
            payload = json.loads(timer.read_text(encoding="utf-8"))
            self.assertEqual("running", payload["status"])
            self.assertIsNone(payload["finished_epoch_ms"])


if __name__ == "__main__":
    unittest.main()
