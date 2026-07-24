from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import patch

from PIL import Image

from test_case_agent.immutable_iteration import (
    ImmutableIterationError,
    MAX_REVIEWER_PROMPT_BYTES,
    _run_stage,
    _stage_prompt,
    run_immutable_iteration,
)
from test_case_agent.iteration_contract import (
    REVIEWER_FALSIFICATION_PROBES,
    build_runtime_writer_request,
    validate_suite,
    validate_writer_response,
)
from test_case_agent.reviewer_evidence import ReviewerEvidenceBasis, ReviewerEvidenceError
from test_case_agent.stage_backend import StageBackendError, StageResult
from test_case_agent.test_design import build_test_design_plan, render_test_cases
from tests.test_iteration_contract import _v2_pack, _writer_graph
from tests.test_test_design import _context, _graph


def _request(prompt: str) -> dict[str, Any]:
    return json.loads(prompt.split("REQUEST JSON:\n", 1)[1])


def _writer_response(graph) -> dict[str, Any]:
    plan = build_test_design_plan(graph, context=_context())
    card = plan.writer_cards[0]
    return {
        "schema_version": 1,
        "graph_digest": graph.digest,
        "cases": [
            {
                "case_key": card.case_key,
                "case_type": "позитивный",
                "subject_id": card.subject_id,
                "expected_result_id": card.expected_result_id,
                "fixture_ids": [
                    item.reference_id for item in card.fixture_references
                ],
                "data_ids": [item.reference_id for item in card.data_references],
                "step_ids": [item.reference_id for item in card.action_references],
            }
        ],
        "unresolved": [],
    }


def _accepted_review(graph, draft_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "graph_digest": graph.digest,
        "draft_sha256": draft_sha256,
        "decision": "accepted",
        "case_results": [
            {
                "case_key": case.case_key,
                "tc_id": case.tc_id,
                "obligation_id": case.obligation_ids[0],
                "status": (
                    "calibration-pending"
                    if case.status == "candidate-ui-calibration"
                    else "covered"
                ),
                "comment": "Проверка полностью покрывает обязательство.",
            }
            for case in graph.cases
        ],
        "findings": [],
        "summary": "Набор принят без замечаний.",
    }


def _passed_falsification(
    *,
    obligation_id: str,
    trigger_or_step: str,
    oracle: str,
    binding_role: str = "primary",
    binding_item_index: int = -1,
) -> dict[str, dict[str, str | int]]:
    return {
        probe: {
            "outcome": "passed",
            "detail": (
                f"The bound {probe} probe was checked against the named step "
                "and oracle; no concrete witness was found."
            ),
            "binding_role": binding_role,
            "obligation_id": obligation_id,
            "binding_item_index": binding_item_index,
            "trigger_or_step": trigger_or_step,
            "oracle": oracle,
        }
        for probe in REVIEWER_FALSIFICATION_PROBES
    }


class FixtureBackend:
    def __init__(
        self,
        *,
        review_decision: str = "accepted",
        mutate_on_stage: tuple[str, Path] | None = None,
        timeout_seconds: float | None = None,
        fail_on_stage: str | None = None,
        receipt_tokens: Any = None,
        bad_runtime_writer_response: bool = False,
        all_runtime_writer_unresolved: bool = False,
    ) -> None:
        self.calls: list[str] = []
        self.review_decision = review_decision
        self.mutate_on_stage = mutate_on_stage
        self.timeout_seconds = timeout_seconds
        self.fail_on_stage = fail_on_stage
        self.receipt_tokens = receipt_tokens
        self.bad_runtime_writer_response = bad_runtime_writer_response
        self.all_runtime_writer_unresolved = all_runtime_writer_unresolved
        self.images_by_stage: dict[str, tuple[Any, ...]] = {}

    def run_stage(
        self,
        *,
        stage: str,
        prompt: str,
        schema: Mapping[str, Any],
        artifact_dir: Path,
        images: tuple[Any, ...] = (),
    ) -> StageResult:
        del schema, artifact_dir
        self.calls.append(stage)
        self.images_by_stage[stage] = images
        if self.fail_on_stage == stage:
            raise StageBackendError(f"{stage} fixture outage")
        request = _request(prompt)
        if stage == "writer":
            cases = []
            if request.get("writer_mode") == "model-runtime-prose":
                if self.all_runtime_writer_unresolved:
                    payload = {
                        "schema_version": 1,
                        "writer_mode": "model-runtime-prose",
                        "graph_digest": request["graph_digest"],
                        "route_contract_ack": "runtime-prose-one-case-per-seed",
                        "cases": [],
                        "unresolved": [
                            {
                                "case_key": seed["case_key"],
                                "reason": (
                                    "Requested registered-card projection cannot "
                                    "be represented by the response schema."
                                ),
                            }
                            for seed in request["cases"]
                        ],
                    }
                    return StageResult(
                        payload=payload,
                        receipt={
                            "stage": stage,
                            "backend": "fixture-stage",
                            "attempts": 1,
                            "duration_ms": 1,
                            "tokens": {
                                "input_tokens": 10,
                                "output_tokens": 5,
                                "reasoning_tokens": 1,
                            },
                            "tool_event_count": 0,
                            "timeout_seconds": None,
                            "image_attachments": {
                                "count": len(images),
                                "bytes": sum(item.size_bytes for item in images),
                            },
                        },
                    )
                for seed in request["cases"]:
                    runtime = seed["seed_runtime"]
                    if self.bad_runtime_writer_response:
                        cases.append(
                            {
                                "case_key": seed["case_key"],
                                "tc_id": seed["tc_id"],
                                "title": "subject:4b12af7e368d24cd",
                                "case_type": seed["case_type"],
                                "preconditions": ["супруг/супруга", "иное"],
                                "test_data": list(runtime["test_data"]),
                                "steps": list(seed["runner_traceability"]),
                                "expected_result": runtime["expected_result"],
                                "postconditions": list(runtime["postconditions"]),
                                "calibration_question": runtime[
                                    "calibration_question"
                                ],
                            }
                        )
                        continue
                    cases.append(
                        {
                            "case_key": seed["case_key"],
                            "tc_id": seed["tc_id"],
                            "title": f"{runtime['title']} — уточнённый сценарий",
                            "case_type": seed["case_type"],
                            "preconditions": list(runtime["preconditions"]),
                            "test_data": list(runtime["test_data"]),
                            "steps": list(runtime["steps"]),
                            "expected_result": runtime["expected_result"],
                            "postconditions": list(runtime["postconditions"]),
                            "calibration_question": runtime[
                                "calibration_question"
                            ],
                        }
                    )
                payload = {
                    "schema_version": 1,
                    "writer_mode": "model-runtime-prose",
                    "graph_digest": request["graph_digest"],
                    "route_contract_ack": "runtime-prose-one-case-per-seed",
                    "cases": cases,
                    "unresolved": [],
                }
            else:
                for card in request["cards"]:
                    cases.append(
                        {
                            "case_key": card["case_key"],
                            "case_type": "позитивный",
                            "subject_id": card["subject_id"],
                            "expected_result_id": card["expected_result_id"],
                            "fixture_ids": [
                                item["reference_id"]
                                for item in card["fixture_references"]
                            ],
                            "data_ids": [
                                item["reference_id"]
                                for item in card["data_references"]
                            ],
                            "step_ids": [
                                item["reference_id"]
                                for item in card["action_references"]
                            ],
                        }
                    )
                payload = {
                    "schema_version": 1,
                    "graph_digest": request["graph_digest"],
                    "cases": cases,
                    "unresolved": [],
                }
        elif request["schema_version"] == 1:
            findings = []
            results = []
            for projection in request["cases"]:
                results.append(
                    {
                        "case_key": projection["case_key"],
                        "tc_id": projection["tc_id"],
                        "obligation_id": projection["obligation"]["obligation_id"],
                        "status": (
                            (
                                "calibration-pending"
                                if projection["status"]
                                == "candidate-ui-calibration"
                                else "covered"
                            )
                            if self.review_decision == "accepted"
                            else "incorrect"
                        ),
                        "comment": "Проверка выполнена по source-first проекции.",
                    }
                )
                if self.review_decision != "accepted":
                    findings.append(
                        {
                            "severity": "error",
                            "case_key": projection["case_key"],
                            "tc_id": projection["tc_id"],
                            "obligation_id": projection["obligation"][
                                "obligation_id"
                            ],
                            "message": "Кейс требует исправления.",
                        }
                    )
            payload = {
                "schema_version": 1,
                "graph_digest": request["graph_digest"],
                "draft_sha256": request["draft_sha256"],
                "decision": self.review_decision,
                "case_results": results,
                "findings": findings,
                "summary": "Независимая проверка завершена.",
            }
        else:
            pack = request["reviewer_evidence_pack"]
            graph_cases = {
                item["case_key"]: item
                for item in pack["normalized_projection"]["cases"]
            }
            chains_by_case: dict[str, list[dict[str, str]]] = {}
            for chain in pack["coverage_mapping"]:
                if chain["case_key"]:
                    chains_by_case.setdefault(chain["case_key"], []).append(chain)
            results = []
            findings = []
            for design in pack["test_cases"]["designs"]:
                case_key = design["case_key"]
                graph_case = graph_cases[case_key]
                chain = chains_by_case[case_key][0]
                results.append(
                    {
                        "case_key": case_key,
                        "tc_id": design["tc_id"],
                        "obligation_id": graph_case["obligation_ids"][0],
                        "status": (
                            (
                                "calibration-pending"
                                if graph_case["status"]
                                == "candidate-ui-calibration"
                                else "covered"
                            )
                            if self.review_decision == "accepted"
                            else "incorrect"
                        ),
                        "comment": "Проверка выполнена по EvidencePack v2.",
                        "falsification": _passed_falsification(
                            obligation_id=graph_case["obligation_ids"][0],
                            trigger_or_step=design["steps"][-1],
                            oracle=design["expected_result"],
                        ),
                    }
                )
                if self.review_decision != "accepted":
                    findings.append(
                        {
                            "severity": "error",
                            "finding_type": "test-case-defect",
                            "binding_role": "primary",
                            "falsification_probe": "",
                            "source_row_id": chain["source_row_id"],
                            "assertion_id": chain["assertion_id"],
                            "property_id": chain["property_id"],
                            "obligation_id": chain["obligation_id"],
                            "case_key": chain["case_key"],
                            "tc_id": chain["tc_id"],
                            "message": "Кейс требует исправления.",
                        }
                    )
            payload = {
                "schema_version": 2,
                "graph_digest": request["graph_digest"],
                "draft_sha256": request["draft_sha256"],
                "evidence_pack_sha256": request["evidence_pack_sha256"],
                "decision": self.review_decision,
                "case_results": results,
                "source_projection_findings": [],
                "test_case_findings": findings,
                "summary": "Независимая проверка EvidencePack v2 завершена.",
            }
        if self.mutate_on_stage is not None and self.mutate_on_stage[0] == stage:
            self.mutate_on_stage[1].write_text(
                "mutated by backend", encoding="utf-8"
            )
        return StageResult(
            payload=payload,
            receipt={
                "stage": stage,
                "backend": "fixture-stage",
                "attempts": 1,
                "duration_ms": 1,
                "tokens": (
                    self.receipt_tokens
                    if self.receipt_tokens is not None
                    else {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "reasoning_tokens": 1,
                    }
                ),
                "tool_event_count": 0,
                "timeout_seconds": None,
                "image_attachments": {
                    "count": len(images),
                    "bytes": sum(item.size_bytes for item in images),
                },
            },
        )


class TinyBackend:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run_stage(
        self,
        *,
        stage: str,
        prompt: str,
        schema: Mapping[str, Any],
        artifact_dir: Path,
        images: tuple[Any, ...] = (),
    ) -> StageResult:
        del prompt, schema, artifact_dir, images
        self.calls.append(stage)
        return StageResult(
            payload={"ok": True},
            receipt={
                "stage": stage,
                "backend": "tiny-fixture-stage",
                "attempts": 1,
                "duration_ms": 1,
                "tokens": "unavailable",
                "tool_event_count": 0,
                "timeout_seconds": None,
                "image_attachments": {"count": 0, "bytes": 0},
            },
        )


class ImmutableIterationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source" / "requirements.xhtml"
        self.source.parent.mkdir()
        self.source.write_text(
            "SOURCE-SENTINEL-DO-NOT-SEND-TO-MODEL", encoding="utf-8"
        )
        self.canonical = self.root / "test-cases" / "baseline.md"
        self.canonical.parent.mkdir()
        self.canonical.write_text(
            "CANONICAL-SENTINEL-DO-NOT-SEND-TO-MODEL", encoding="utf-8"
        )

    def run_engine(self, graph, output_name: str, **kwargs: Any):
        context = kwargs.pop("context", _context())
        return run_immutable_iteration(
            repo_root=self.root,
            graph=graph,
            context=context,
            output_dir=self.root / output_name,
            protected_source_paths=(self.source,),
            protected_canonical_paths=(self.canonical,),
            **kwargs,
        )

    def test_deterministic_suite_skips_writer_and_calls_reviewer_once(self) -> None:
        backend = FixtureBackend()

        result = self.run_engine(_graph(), "deterministic", backend=backend)

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual(["reviewer"], backend.calls)
        self.assertEqual(0, result.writer_model_calls)
        self.assertEqual(1, result.reviewer_model_calls)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertTrue(summary["suite_gate_passed"])
        self.assertTrue(summary["reviewer_accepted_zero_findings"])
        timing = summary["timing"]
        self.assertEqual(
            timing["total_wall_ns"],
            timing["phase_sum_ns"] + timing["unattributed_interphase_ns"],
        )
        writer, reviewer = summary["model_stages"]
        self.assertEqual("deterministic-zero-call", writer["backend"])
        self.assertEqual(0, writer["attempts"])
        self.assertEqual("unavailable", writer["response_sha256"])
        self.assertGreater(reviewer["input_artifacts"]["bytes"], 0)
        self.assertGreater(reviewer["output_artifacts"]["bytes"], 0)
        self.assertRegex(reviewer["response_sha256"], r"^[0-9a-f]{64}$")
        self.assertIsNone(reviewer["timeout_seconds"])
        self.assertEqual(
            "unavailable", summary["root_agent_token_usage"]["availability"]
        )
        self.assertEqual(
            "unavailable",
            summary["orchestration_token_usage"]["input_tokens"],
        )

    def test_model_runtime_prose_mode_calls_writer_for_deterministic_suite(self) -> None:
        backend = FixtureBackend()

        result = self.run_engine(
            _graph(),
            "model-runtime-prose",
            backend=backend,
            writer_mode="model-runtime-prose",
            mockup_label_aliases=(
                {
                    "canonical_ft_name": "Добавить контактное лицо",
                    "label_from_mockup": "+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО",
                },
            ),
        )

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual(["writer", "reviewer"], backend.calls)
        self.assertEqual(1, result.writer_model_calls)
        self.assertEqual(1, result.reviewer_model_calls)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual("immutable-model-runtime-prose", summary["mode"])
        self.assertEqual("model-runtime-prose", summary["writer_mode"])
        writer_request = json.loads(
            (result.output_dir / "writer-request.json").read_text(encoding="utf-8")
        )
        self.assertEqual("model-runtime-prose", writer_request["writer_mode"])
        self.assertTrue(
            writer_request["constraints"]["model_authors_runtime_prose"]
        )
        self.assertEqual(
            "+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО",
            writer_request["mockup_label_aliases"][0]["label_from_mockup"],
        )
        evidence = json.loads(
            (result.output_dir / "evidence-access-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("model-runtime-prose", evidence["writer_mode"])
        self.assertTrue(evidence["writer_model_authors_runtime_prose"])
        self.assertEqual(1, evidence["mockup_label_alias_count"])
        text = result.draft_path.read_text(encoding="utf-8")
        self.assertIn("— уточнённый сценарий", text)
        self.assertIn(_graph().cases[0].tc_id, text)

    def test_model_runtime_prose_prompt_and_request_exclude_legacy_projection_contract(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        request = build_runtime_writer_request(graph, plan)
        prompt = _stage_prompt("writer", request)
        serialized_request = json.dumps(request, ensure_ascii=False, sort_keys=True)

        self.assertIn("not the legacy registered-card projection route", prompt)
        self.assertIn("runtime-prose-one-case-per-seed", prompt)
        self.assertIn(
            "Return exactly one item in `cases` for every input seed case",
            prompt,
        )
        for legacy_phrase in (
            "registered subject",
            "expected-result, fixture, data",
            "ordered action identifiers",
            "Do not author case prose",
        ):
            self.assertNotIn(legacy_phrase, prompt)
        for legacy_field in (
            "subject_id",
            "expected_result_id",
            "fixture_ids",
            "data_ids",
            "step_ids",
        ):
            self.assertNotIn(f'"{legacy_field}"', serialized_request)

    def test_model_runtime_prose_bad_writer_output_stops_before_reviewer(self) -> None:
        backend = FixtureBackend(bad_runtime_writer_response=True)

        result = self.run_engine(
            _graph(),
            "model-runtime-bad-writer-output",
            backend=backend,
            writer_mode="model-runtime-prose",
        )

        self.assertEqual("blocked-contract", result.status)
        self.assertEqual(["writer"], backend.calls)
        self.assertEqual(1, result.writer_model_calls)
        self.assertEqual(0, result.reviewer_model_calls)
        self.assertFalse((result.output_dir / "reviewer-request.json").exists())
        self.assertFalse((result.output_dir / "shadow-test-cases.md").exists())
        diagnostic = json.loads(
            (result.output_dir / "failure-diagnostic.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("runtime writer leaked internal identifier", diagnostic["error"])
        self.assertIn("subject:", diagnostic["error"])

    def test_model_runtime_prose_all_unresolved_stops_before_reviewer_with_route_diagnostic(self) -> None:
        backend = FixtureBackend(all_runtime_writer_unresolved=True)

        result = self.run_engine(
            _graph(),
            "model-runtime-all-unresolved",
            backend=backend,
            writer_mode="model-runtime-prose",
        )

        self.assertEqual("blocked-contract", result.status)
        self.assertEqual(["writer"], backend.calls)
        self.assertEqual(1, result.writer_model_calls)
        self.assertEqual(0, result.reviewer_model_calls)
        self.assertFalse((result.output_dir / "reviewer-request.json").exists())
        self.assertFalse((result.output_dir / "shadow-test-cases.md").exists())
        diagnostic = json.loads(
            (result.output_dir / "failure-diagnostic.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("route failure: all input seed cases", diagnostic["error"])
        self.assertIn("one human-runtime output case per valid seed case", diagnostic["error"])

    def test_model_runtime_prose_design_support_contract_failure_skips_reviewer(self) -> None:
        backend = FixtureBackend()
        basis = ReviewerEvidenceBasis(  # type: ignore[arg-type]
            repo_root=self.root,
            compiled_scope=None,
            manifest=None,
            source_review_receipt=None,
            obligation_set=None,
            registered_files=(),
            mockup_files=(),
            basis_digest="unused-by-patched-builder",
            compiled_snapshot_sha256="unused-by-patched-builder",
            review_receipt_sha256="unused-by-patched-builder",
        )

        with patch(
            "test_case_agent.immutable_iteration.build_reviewer_evidence_pack",
            side_effect=ReviewerEvidenceError(
                "design-support-traceability-not-materialized",
                "TC-CUST-0123456789 traces sibling OBL-DELETE without a "
                "source-bound setup/action/cleanup action",
            ),
        ), patch.object(
            ReviewerEvidenceBasis,
            "to_document",
            return_value={
                "schema_version": 1,
                "contract": "test-only-evidence-basis",
            },
        ):
            result = self.run_engine(
                _graph(),
                "model-runtime-design-support-failure",
                backend=backend,
                writer_mode="model-runtime-prose",
                reviewer_evidence_basis=basis,
            )

        self.assertEqual("blocked-contract", result.status)
        self.assertEqual(["writer"], backend.calls)
        self.assertEqual(1, result.writer_model_calls)
        self.assertEqual(0, result.reviewer_model_calls)
        self.assertFalse((result.output_dir / "reviewer-request.json").exists())
        diagnostic = json.loads(
            (result.output_dir / "failure-diagnostic.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("design-support-traceability-not-materialized", diagnostic["error"])
        self.assertIn("source-bound setup/action/cleanup action", diagnostic["error"])

    def test_model_runtime_prose_changes_required_writes_revision_input(self) -> None:
        backend = FixtureBackend(review_decision="changes-required")

        result = self.run_engine(
            _graph(),
            "model-runtime-revision",
            backend=backend,
            writer_mode="model-runtime-prose",
            revision_findings={"previous_attempt": "attempt-001"},
        )

        self.assertEqual("review-changes-required", result.status)
        self.assertEqual(["writer", "reviewer"], backend.calls)
        revision = json.loads(
            (result.output_dir / "revision-input.json").read_text(encoding="utf-8")
        )
        self.assertEqual("model-runtime-prose", revision["writer_mode"])
        self.assertEqual("changes-required", revision["reviewer_decision"])
        self.assertEqual("start-new-immutable-attempt", revision["next_attempt_policy"])
        self.assertFalse(revision["old_test_cases_available"])
        self.assertEqual("revision_findings", revision["required_next_input"])
        writer_request = json.loads(
            (result.output_dir / "writer-request.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {"previous_attempt": "attempt-001"},
            writer_request["revision_findings"],
        )

    def test_calibration_candidate_is_successful_but_non_promotable(self) -> None:
        backend = FixtureBackend()
        graph = _graph(
            status="candidate-ui-calibration",
            trigger="Ввести значение в поле «Имя».",
            question="Какой точный UI-отклик отображается?",
        )

        result = self.run_engine(graph, "calibration-pending", backend=backend)

        self.assertEqual("accepted-with-calibration-pending", result.status)
        self.assertEqual(["reviewer"], backend.calls)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertTrue(summary["reviewer_accepted_zero_findings"])
        self.assertEqual(1, summary["calibration_pending_count"])
        self.assertFalse(summary["promotion_eligible"])
        self.assertEqual(
            "calibration-pending", summary["non_promotable_reason"]
        )
        request = json.loads(
            (result.output_dir / "reviewer-request.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            "calibration-pending",
            request["acceptance"]["calibration_candidate_result_status"],
        )
        prompt = (
            result.output_dir / "model-stages" / "reviewer-prompt.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("do not demand hypothetical", prompt)
        self.assertIn("before/after states", prompt)

    def test_precomputed_responses_run_fully_offline(self) -> None:
        graph = _writer_graph()
        plan = build_test_design_plan(graph, context=_context())
        writer_response = _writer_response(graph)
        writer_cases, unresolved = validate_writer_response(
            writer_response,
            graph=graph,
            plan=plan,
            context=_context(),
        )
        self.assertEqual((), unresolved)
        draft = render_test_cases(writer_cases, scope_title=_context().scope_title)
        gate = validate_suite(
            graph=graph,
            cases=writer_cases,
            markdown=draft,
            checked_path="offline-shadow.md",
        )
        self.assertTrue(gate.passed, gate.to_dict())
        reviewer_response = _accepted_review(graph, gate.draft_sha256)
        backend = FixtureBackend()

        result = self.run_engine(
            graph,
            "offline",
            backend=backend,
            writer_response=writer_response,
            reviewer_response=reviewer_response,
        )

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual([], backend.calls)
        self.assertEqual(0, result.writer_model_calls)
        self.assertEqual(0, result.reviewer_model_calls)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual(
            ["precomputed-response", "precomputed-response"],
            [item["backend"] for item in summary["model_stages"]],
        )

    def test_complex_writer_cannot_own_oracle_traceability_or_lifecycle(self) -> None:
        backend = FixtureBackend()
        graph = _writer_graph()

        result = self.run_engine(graph, "complex", backend=backend)

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual(["writer", "reviewer"], backend.calls)
        text = result.draft_path.read_text(encoding="utf-8")
        self.assertIn(graph.obligations[0].observable_oracle, text)
        self.assertIn("OBL-001", text)
        self.assertIn("ATOM-001", text)
        self.assertIn("Добавить удалённую тестовую строку повторно.", text)
        writer_prompt = (
            result.output_dir / "model-stages" / "writer-prompt.txt"
        ).read_text(encoding="utf-8")
        reviewer_prompt = (
            result.output_dir / "model-stages" / "reviewer-prompt.txt"
        ).read_text(encoding="utf-8")
        self.assertNotIn("SOURCE-SENTINEL", writer_prompt + reviewer_prompt)
        self.assertNotIn("CANONICAL-SENTINEL", writer_prompt + reviewer_prompt)
        evidence = json.loads(
            (result.output_dir / "evidence-access-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(evidence["canonical_file_content_in_model_context"])
        self.assertFalse(evidence["old_test_cases_in_model_context"])
        self.assertEqual(0, evidence["command_budget"])

    def test_blocked_card_stops_before_every_model_stage(self) -> None:
        backend = FixtureBackend()

        result = self.run_engine(
            _graph(fixtures=()),
            "blocked",
            backend=backend,
        )

        self.assertEqual("blocked-design", result.status)
        self.assertEqual([], backend.calls)
        self.assertFalse((result.output_dir / "shadow-test-cases.md").exists())
        self.assertTrue((result.output_dir / "blocked-cards.json").is_file())
        self.assertEqual(0, result.writer_model_calls)
        self.assertEqual(0, result.reviewer_model_calls)

    def test_engine_uses_full_authoritative_graph_integrity_validator(self) -> None:
        graph = _graph()
        graph = replace(
            graph,
            obligations=(
                replace(
                    graph.obligations[0],
                    coverage_status="mystery",
                    gap_id="GAP-404",
                ),
            ),
        )
        backend = FixtureBackend()

        result = self.run_engine(graph, "invalid-graph-integrity", backend=backend)

        self.assertEqual("blocked-contract", result.status)
        self.assertEqual([], backend.calls)
        diagnostic = json.loads(
            (result.output_dir / "failure-diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertIn("CG-INVALID-COVERAGE-STATUS", diagnostic["error"])

    def test_input_drift_after_writer_prevents_reviewer_and_acceptance(self) -> None:
        backend = FixtureBackend(mutate_on_stage=("writer", self.source))

        result = self.run_engine(_writer_graph(), "source-drift", backend=backend)

        self.assertEqual("blocked-input-drift", result.status)
        self.assertEqual(["writer"], backend.calls)
        self.assertEqual(1, result.writer_model_calls)
        self.assertEqual(0, result.reviewer_model_calls)
        self.assertTrue((result.output_dir / "input-drift.json").is_file())

    def test_review_changes_required_is_not_accepted_shadow(self) -> None:
        backend = FixtureBackend(review_decision="changes-required")

        result = self.run_engine(_graph(), "review-rejected", backend=backend)

        self.assertEqual("review-changes-required", result.status)
        self.assertNotEqual("accepted-shadow", result.status)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertFalse(summary["reviewer_accepted_zero_findings"])
        self.assertTrue(summary["suite_gate_passed"])

    def test_canonical_drift_during_reviewer_overrides_acceptance(self) -> None:
        backend = FixtureBackend(mutate_on_stage=("reviewer", self.canonical))

        result = self.run_engine(_graph(), "canonical-drift", backend=backend)

        self.assertEqual("blocked-input-drift", result.status)
        self.assertEqual(["reviewer"], backend.calls)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertFalse(summary["protected_inputs_unchanged"])
        self.assertFalse(summary["reviewer_accepted_zero_findings"])

    def test_failed_backend_call_is_counted_without_retry(self) -> None:
        backend = FixtureBackend(fail_on_stage="reviewer")

        result = self.run_engine(_graph(), "backend-outage", backend=backend)

        self.assertEqual("failed-infrastructure", result.status)
        self.assertEqual(["reviewer"], backend.calls)
        self.assertEqual(0, result.writer_model_calls)
        self.assertEqual(1, result.reviewer_model_calls)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        failed_receipt = summary["model_stages"][-1]
        self.assertEqual("reviewer", failed_receipt["stage"])
        self.assertEqual(1, failed_receipt["attempts"])
        self.assertEqual("unavailable", failed_receipt["tokens"])
        self.assertGreater(failed_receipt["input_artifacts"]["bytes"], 0)
        self.assertEqual("unavailable", failed_receipt["response_sha256"])
        self.assertEqual(
            "reviewer fixture outage",
            json.loads(
                (result.output_dir / "failure-diagnostic.json").read_text(
                    encoding="utf-8"
                )
            )["error"],
        )

    def test_precomputed_writer_is_rejected_for_zero_writer_plan(self) -> None:
        backend = FixtureBackend()

        result = self.run_engine(
            _graph(),
            "unexpected-writer-response",
            backend=backend,
            writer_response={
                "schema_version": 1,
                "graph_digest": _graph().digest,
                "cases": [],
                "unresolved": [],
            },
        )

        self.assertEqual("blocked-contract", result.status)
        self.assertEqual([], backend.calls)
        self.assertEqual(0, result.writer_model_calls)
        self.assertEqual(0, result.reviewer_model_calls)

    def test_backend_with_hard_timeout_is_rejected_without_call(self) -> None:
        backend = FixtureBackend(timeout_seconds=30)

        result = self.run_engine(_graph(), "timeout", backend=backend)

        self.assertEqual("blocked-contract", result.status)
        self.assertEqual([], backend.calls)
        diagnostic = json.loads(
            (result.output_dir / "failure-diagnostic.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("hard model timeout", diagnostic["error"])

    def test_oversized_reviewer_context_blocks_without_truncation_or_call(self) -> None:
        backend = FixtureBackend()

        with patch(
            "test_case_agent.immutable_iteration.MAX_REVIEWER_PROMPT_BYTES",
            1,
        ):
            result = self.run_engine(
                _graph(),
                "reviewer-context-too-large",
                backend=backend,
            )

        self.assertEqual("blocked-reviewer-context-too-large", result.status)
        self.assertEqual([], backend.calls)
        self.assertEqual(0, result.reviewer_model_calls)
        diagnostic = json.loads(
            (result.output_dir / "failure-diagnostic.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("decompose the external scope", diagnostic["safe_recovery"])
        self.assertFalse(
            (result.output_dir / "model-stages" / "reviewer-prompt.txt").exists()
        )

    def test_contact_person_sized_reviewer_prompt_fits_budget(self) -> None:
        target_prompt_bytes = 296_815
        request = {
            "schema_version": 2,
            "reviewer_evidence_pack": {"padding": ""},
        }
        base_size = len(_stage_prompt("reviewer", request).encode("utf-8"))
        request["reviewer_evidence_pack"]["padding"] = "x" * (
            target_prompt_bytes - base_size
        )
        prompt_size = len(_stage_prompt("reviewer", request).encode("utf-8"))
        self.assertEqual(target_prompt_bytes, prompt_size)
        self.assertLess(prompt_size, MAX_REVIEWER_PROMPT_BYTES)

        backend = TinyBackend()
        output_dir = self.root / "contact-person-sized-reviewer"
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
        }
        model_calls = 0

        def record_model_call() -> None:
            nonlocal model_calls
            model_calls += 1

        payload, receipt, called_model = _run_stage(
            stage="reviewer",
            request=request,
            schema=schema,
            output_dir=output_dir,
            repo_root=self.root,
            backend=backend,
            precomputed=None,
            on_model_call=record_model_call,
        )

        self.assertEqual({"ok": True}, payload)
        self.assertTrue(called_model)
        self.assertEqual(1, model_calls)
        self.assertEqual(["reviewer"], backend.calls)
        self.assertEqual(prompt_size, receipt["input_artifacts"]["prompt_bytes"])

    def test_v2_registered_mockup_is_forwarded_once_and_receipted(self) -> None:
        graph = _graph()
        mockup = self.root / "source" / "screen.png"
        mockup.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (3, 2), color=(31, 97, 173)).save(mockup)
        backend = FixtureBackend()
        basis = ReviewerEvidenceBasis(  # type: ignore[arg-type]
            repo_root=self.root,
            compiled_scope=None,
            manifest=None,
            source_review_receipt=None,
            obligation_set=None,
            registered_files=(),
            mockup_files=(),
            basis_digest="unused-by-patched-builder",
            compiled_snapshot_sha256="unused-by-patched-builder",
            review_receipt_sha256="unused-by-patched-builder",
        )

        class FakePack:
            def __init__(self, payload: dict[str, Any]) -> None:
                self.payload = payload

            def to_dict(self) -> dict[str, Any]:
                return json.loads(json.dumps(self.payload, ensure_ascii=False))

            @property
            def digest(self) -> str:
                rendered = json.dumps(
                    self.payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                return hashlib.sha256(rendered).hexdigest()

            @property
            def image_paths(self) -> tuple[Path, ...]:
                return (mockup.resolve(),)

        def fake_builder(
            _basis: Any,
            bound_graph: Any,
            cases: Any,
            markdown: str,
            draft_sha256: str,
            _acceptance: Any,
        ) -> FakePack:
            gate = type("GateBinding", (), {"draft_sha256": draft_sha256})()
            payload = _v2_pack(bound_graph, cases, gate, markdown)
            payload["identity"]["contract"] = "reviewer-evidence-pack-v2"
            payload["mockup_attachments"] = [
                {
                    "path": "source/screen.png",
                    "role": "scope-mockup",
                    "scope_id": "sample-scope",
                    "sha256": hashlib.sha256(mockup.read_bytes()).hexdigest(),
                    "size_bytes": mockup.stat().st_size,
                    "screen_description": "Контактное лицо",
                    "locators": [],
                }
            ]
            return FakePack(payload)

        with patch(
            "test_case_agent.immutable_iteration.build_reviewer_evidence_pack",
            side_effect=fake_builder,
        ), patch.object(
            ReviewerEvidenceBasis,
            "to_document",
            return_value={
                "schema_version": 1,
                "contract": "test-only-evidence-basis",
            },
        ):
            result = self.run_engine(
                graph,
                "v2-image-forwarding",
                backend=backend,
                reviewer_evidence_basis=basis,
            )

        self.assertEqual("accepted-shadow", result.status)
        self.assertEqual(["reviewer"], backend.calls)
        self.assertEqual(1, len(backend.images_by_stage["reviewer"]))
        self.assertEqual(mockup.resolve(), backend.images_by_stage["reviewer"][0].path)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        reviewer = summary["model_stages"][-1]
        self.assertEqual(
            {"count": 1, "bytes": mockup.stat().st_size},
            reviewer["image_attachments"],
        )

    def test_invalid_token_receipts_fail_closed(self) -> None:
        invalid = (
            {"input_tokens": -1},
            {"input_tokens": "10"},
            {"input_tokens": True},
            {},
            0,
        )
        for index, tokens in enumerate(invalid):
            with self.subTest(tokens=tokens):
                result = self.run_engine(
                    _graph(),
                    f"invalid-token-receipt-{index}",
                    backend=FixtureBackend(receipt_tokens=tokens),
                )
                self.assertEqual("blocked-contract", result.status)
                diagnostic = json.loads(
                    (result.output_dir / "failure-diagnostic.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertIn("token", diagnostic["error"])

    def test_zero_model_token_metrics_are_valid_numeric_measurements(self) -> None:
        result = self.run_engine(
            _graph(),
            "zero-token-metrics",
            backend=FixtureBackend(
                receipt_tokens={
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                }
            ),
        )

        self.assertEqual("accepted-shadow", result.status)
        summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
        reviewer = summary["model_stages"][-1]
        self.assertEqual(0, reviewer["token_usage"]["input_tokens"])
        self.assertEqual(
            "unavailable", summary["root_agent_token_usage"]["input_tokens"]
        )

    def test_existing_output_directory_cannot_be_reused(self) -> None:
        output = self.root / "already-exists"
        output.mkdir()

        with self.assertRaisesRegex(ImmutableIterationError, "must not exist"):
            self.run_engine(_graph(), "already-exists", backend=FixtureBackend())


if __name__ == "__main__":
    unittest.main()
