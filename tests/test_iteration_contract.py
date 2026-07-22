from __future__ import annotations

import unittest
from dataclasses import replace

from test_case_agent.iteration_contract import (
    IterationContractError,
    build_reviewer_request,
    build_writer_request,
    validate_reviewer_response,
    validate_suite,
    validate_writer_response,
)
from test_case_agent.test_design import (
    DesignContext,
    build_test_design_plan,
    render_test_cases,
)
from tests.test_test_design import _context, _graph


def _writer_graph():
    return _graph(
        kind="repeater-delete",
        fixtures=("Строка 2",),
        cleanup="Добавить удалённую тестовую строку повторно.",
    )


def _writer_case(plan, **changes):  # type: ignore[no-untyped-def]
    card = plan.writer_cards[0]
    payload = {
        "case_key": card.case_key,
        "case_type": "позитивный",
        "subject_id": card.subject_id,
        "expected_result_id": card.expected_result_id,
        "fixture_ids": [item.reference_id for item in card.fixture_references],
        "data_ids": [item.reference_id for item in card.data_references],
        "step_ids": [item.reference_id for item in card.action_references],
    }
    payload.update(changes)
    return payload


def _accepted_review(graph, draft_sha256: str):
    case = graph.cases[0]
    obligation_id = case.obligation_ids[0]
    return {
        "schema_version": 1,
        "graph_digest": graph.digest,
        "draft_sha256": draft_sha256,
        "decision": "accepted",
        "case_results": [
            {
                "case_key": case.case_key,
                "tc_id": case.tc_id,
                "obligation_id": obligation_id,
                "status": (
                    "calibration-pending"
                    if case.status == "candidate-ui-calibration"
                    else "covered"
                ),
                "comment": "Покрытие корректно.",
            }
        ],
        "findings": [],
        "summary": "Набор принят.",
    }


class IterationContractTests(unittest.TestCase):
    def test_writer_receives_only_complex_cards_and_runner_owned_contract(self) -> None:
        graph = _writer_graph()
        plan = build_test_design_plan(graph, context=_context())

        request = build_writer_request(graph, plan)

        self.assertEqual(len(request["cards"]), 1)
        self.assertNotIn("test_cases", request)
        self.assertFalse(request["constraints"]["old_test_cases_available"])
        self.assertIn("expected_result", request["constraints"]["runner_owned_fields"])

    def test_writer_cannot_change_oracle_ids_or_lifecycle(self) -> None:
        graph = _writer_graph()
        plan = build_test_design_plan(graph, context=_context())
        case_key = graph.cases[0].case_key
        response = {
            "schema_version": 1,
            "graph_digest": graph.digest,
            "cases": [
                {
                    **_writer_case(plan),
                    "expected_result": "Придуманный результат.",
                }
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(IterationContractError, "unknown=.*expected_result"):
            validate_writer_response(
                response,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_writer_cannot_inject_unregistered_fixture_or_action_identifier(self) -> None:
        graph = _writer_graph()
        plan = build_test_design_plan(graph, context=_context())
        response = {
            "schema_version": 1,
            "graph_digest": graph.digest,
            "cases": [
                _writer_case(
                    plan,
                    fixture_ids=["FIX-INVENTED"],
                    step_ids=["ACT-INVENTED"],
                )
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(IterationContractError, "fixture_ids binding mismatch"):
            validate_writer_response(
                response,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runner_merges_writer_case_with_exact_oracle_and_cleanup(self) -> None:
        graph = _writer_graph()
        plan = build_test_design_plan(graph, context=_context())
        response = {
            "schema_version": 1,
            "graph_digest": graph.digest,
            "cases": [_writer_case(plan)],
            "unresolved": [],
        }

        designs, unresolved = validate_writer_response(
            response,
            graph=graph,
            plan=plan,
            context=_context(),
        )

        self.assertEqual(unresolved, ())
        self.assertEqual(designs[0].title, graph.obligations[0].atomic_statement.rstrip("."))
        self.assertEqual(designs[0].steps, (graph.obligations[0].atomic_statement,))
        self.assertIn("`Строка 2`", designs[0].test_data[0])
        self.assertEqual(designs[0].expected_result, graph.obligations[0].observable_oracle)
        self.assertEqual(
            designs[0].postconditions,
            ("Добавить удалённую тестовую строку повторно.",),
        )
        self.assertEqual(designs[0].tc_id, graph.cases[0].tc_id)

    def test_writer_merge_revalidates_context_against_graph(self) -> None:
        graph = _writer_graph()
        plan = build_test_design_plan(graph, context=_context())
        response = {
            "schema_version": 1,
            "graph_digest": graph.digest,
            "cases": [_writer_case(plan)],
            "unresolved": [],
        }
        injected = replace(
            _context(),
            base_preconditions=("Открыть скрытую административную панель.",),
        )

        with self.assertRaisesRegex(
            IterationContractError, "writer design context is invalid"
        ):
            validate_writer_response(
                response,
                graph=graph,
                plan=plan,
                context=injected,
            )

    def test_suite_gate_rejects_stable_id_drift(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        case = replace(plan.deterministic_cases[0], tc_id="TC-CUST-9999999999")
        markdown = render_test_cases((case,), scope_title="Данные клиента")

        gate = validate_suite(
            graph=graph,
            cases=(case,),
            markdown=markdown,
            checked_path="shadow.md",
        )

        self.assertFalse(gate.passed)
        self.assertIn("stable TC-ID drift", gate.findings[0])

    def test_reviewer_request_is_compact_source_first_projection(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        cases = plan.deterministic_cases
        markdown = render_test_cases(cases, scope_title="Данные клиента")
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )

        request = build_reviewer_request(graph=graph, cases=cases, gate=gate)

        self.assertTrue(gate.passed, gate.to_dict())
        self.assertEqual(len(request["cases"]), 1)
        self.assertNotIn("draft", request)
        self.assertFalse(request["acceptance"]["old_test_cases_available"])
        self.assertTrue(request["acceptance"]["review_only_projected_behavior"])
        self.assertTrue(request["acceptance"]["no_hypothetical_state_axes"])
        self.assertTrue(
            request["acceptance"][
                "explicit_projected_before_after_states_must_be_covered"
            ]
        )

    def test_accepted_review_with_warning_is_rejected(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        markdown = render_test_cases(plan.deterministic_cases, scope_title="Данные клиента")
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        response = _accepted_review(graph, gate.draft_sha256)
        case = graph.cases[0]
        response["findings"] = [
            {
                "severity": "warning",
                "case_key": case.case_key,
                "tc_id": case.tc_id,
                "obligation_id": case.obligation_ids[0],
                "message": "Требуется уточнение.",
            }
        ]

        with self.assertRaisesRegex(IterationContractError, "zero findings"):
            validate_reviewer_response(
                response,
                graph=graph,
                draft_sha256=gate.draft_sha256,
            )

    def test_reviewer_finding_must_bind_exact_case(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        markdown = render_test_cases(plan.deterministic_cases, scope_title="Данные клиента")
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        response = _accepted_review(graph, gate.draft_sha256)
        response["decision"] = "changes-required"
        case = graph.cases[0]
        response["findings"] = [
            {
                "severity": "error",
                "case_key": case.case_key,
                "tc_id": "TC-CUST-FFFFFFFFFF",
                "obligation_id": case.obligation_ids[0],
                "message": "Ошибка.",
            }
        ]

        with self.assertRaisesRegex(IterationContractError, "binding mismatch"):
            validate_reviewer_response(
                response,
                graph=graph,
                draft_sha256=gate.draft_sha256,
            )

    def test_clean_review_is_accepted(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        markdown = render_test_cases(plan.deterministic_cases, scope_title="Данные клиента")
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=markdown,
            checked_path="shadow.md",
        )

        accepted, decision = validate_reviewer_response(
            _accepted_review(graph, gate.draft_sha256),
            graph=graph,
            draft_sha256=gate.draft_sha256,
        )

        self.assertTrue(accepted)
        self.assertEqual(decision, "accepted")

    def test_calibration_candidate_is_accepted_only_as_pending(self) -> None:
        graph = _graph(
            status="candidate-ui-calibration",
            trigger="Ввести значение в поле «Имя».",
            question="Какой точный UI-отклик отображается?",
        )
        plan = build_test_design_plan(graph, context=_context())
        markdown = render_test_cases(
            plan.deterministic_cases,
            scope_title="Данные клиента",
        )
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        self.assertTrue(gate.passed, gate.to_dict())
        response = _accepted_review(graph, gate.draft_sha256)

        accepted, decision = validate_reviewer_response(
            response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
        )

        self.assertTrue(accepted)
        self.assertEqual("accepted", decision)
        self.assertEqual(
            "calibration-pending",
            response["case_results"][0]["status"],
        )

        response["case_results"][0]["status"] = "covered"
        with self.assertRaisesRegex(
            IterationContractError,
            "calibration candidate calibration-pending",
        ):
            validate_reviewer_response(
                response,
                graph=graph,
                draft_sha256=gate.draft_sha256,
            )

    def test_executable_case_cannot_be_accepted_as_calibration_pending(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        markdown = render_test_cases(
            plan.deterministic_cases,
            scope_title="Данные клиента",
        )
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        response = _accepted_review(graph, gate.draft_sha256)
        response["case_results"][0]["status"] = "calibration-pending"

        with self.assertRaisesRegex(
            IterationContractError,
            "executable case covered",
        ):
            validate_reviewer_response(
                response,
                graph=graph,
                draft_sha256=gate.draft_sha256,
            )


if __name__ == "__main__":
    unittest.main()
