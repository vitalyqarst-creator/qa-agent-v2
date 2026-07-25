from __future__ import annotations

import copy
import hashlib
import unittest
from dataclasses import replace

from test_case_agent.coverage_graph import CoverageCase, CoverageProperty
from test_case_agent.iteration_contract import (
    IterationContractError,
    REVIEWER_FALSIFICATION_PROBES,
    build_reviewer_request,
    build_runtime_writer_request,
    build_writer_request,
    reviewer_acceptance_contract,
    reviewer_deferred_test_case_findings,
    reviewer_prompt_instruction,
    reviewer_response_schema,
    runtime_writer_response_schema,
    validate_reviewer_response,
    validate_runtime_writer_response,
    validate_suite,
    validate_writer_response,
)
from test_case_agent.reviewer_evidence import build_design_support_mapping
from test_case_agent.strict_output_schema import (
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)
from test_case_agent.test_design import (
    DesignContext,
    build_test_design_plan,
    render_test_cases,
)
from tests.test_test_design import _context, _graph, _repeater_graph_and_context


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


def _runtime_writer_case(seed, **changes):  # type: ignore[no-untyped-def]
    payload = {
        "case_key": seed.case_key,
        "tc_id": seed.tc_id,
        "title": f"{seed.title} — модельная редакция",
        "case_type": seed.case_type,
        "preconditions": list(seed.preconditions),
        "test_data": list(seed.test_data),
        "steps": list(seed.steps),
        "expected_result": seed.expected_result,
        "postconditions": list(seed.postconditions),
        "calibration_question": seed.calibration_question,
    }
    payload.update(changes)
    return payload


def _runtime_writer_payload(graph, cases, unresolved=()):  # type: ignore[no-untyped-def]
    return {
        "schema_version": 1,
        "writer_mode": "model-runtime-prose",
        "graph_digest": graph.digest,
        "route_contract_ack": "runtime-prose-one-case-per-seed",
        "cases": list(cases),
        "unresolved": list(unresolved),
    }


def _multi_runtime_graph():
    graph = _graph()
    return replace(
        graph,
        obligations=(
            graph.obligations[0],
            replace(
                graph.obligations[0],
                obligation_id="OBL-002",
                atom_id="ATOM-002",
                atomic_statement="РџСЂРѕРІРµСЂРёС‚СЊ РѕС‡РёСЃС‚РєСѓ РїРѕР»СЏ В«РРјСЏВ».",
                observable_oracle="РџРѕР»Рµ В«РРјСЏВ» РЅРµ СЃРѕРґРµСЂР¶РёС‚ Р·РЅР°С‡РµРЅРёСЏ.",
                fixture_values=("РџРµС‚СЂ",),
            ),
        ),
        cases=(
            graph.cases[0],
            CoverageCase(
                case_key="customer|customer-name|clear-input|positive|always",
                tc_id="TC-CUST-9876543210",
                obligation_ids=("OBL-002",),
                status="executable",
            ),
        ),
    )


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


def _v2_pack(graph, cases, gate, markdown):  # type: ignore[no-untyped-def]
    prop = graph.properties[0]
    obligation = graph.obligations[0]
    case = graph.cases[0]
    pack = {
        "schema_version": 2,
        "identity": {
            "graph_digest": graph.digest,
            "draft_sha256": gate.draft_sha256,
        },
        "literal_source_evidence": [
            {
                "source_row_id": prop.source_row_id,
                "candidate_id": "SRC-CAND-111111111111111111111111",
                "source_path": "source/main.xhtml",
                "source_file_sha256": "1" * 64,
                "source_locator": "/*/*[1]",
                "row_identity": "/*/*[1]",
                "element_kind": "p",
                "table_identity": None,
                "table_ancestry": [],
                "section_path": [],
                "section_heading_evidence": [],
                "bounded_source_text": "Поле принимает только цифровые символы.",
            },
            {
                "source_row_id": "SRC-CONTEXT",
                "candidate_id": None,
                "source_path": "source/main.xhtml",
                "source_file_sha256": "1" * 64,
                "source_locator": "/*/*[2]",
                "row_identity": "/*/*[2]",
                "element_kind": "p",
                "table_identity": None,
                "table_ancestry": [],
                "section_path": [],
                "section_heading_evidence": [],
                "bounded_source_text": "Заголовок таблицы.",
            },
        ],
        "source_structure": {
            "selected_xhtml": {
                "relative_path": "source/main.xhtml",
                "sha256": "1" * 64,
            },
            "scope_definition": {
                "gap_ids": [],
                "source_set": {"pdf": None},
            },
            "docx_xhtml_pdf_parity": {
                "contract": "bounded-source-parity-v1",
                "status": "verified",
                "docx_xhtml": {
                    "status": "verified",
                    "literal_candidate_count": 1,
                    "matched_literal_candidate_count": 1,
                    "literal_xhtml_row_count": 2,
                    "matched_literal_xhtml_row_count": 2,
                    "unique_docx_unit_count": 2,
                    "row_matches": [
                        {
                            "candidate_id": "SRC-CAND-111111111111111111111111",
                            "source_row_id": prop.source_row_id,
                            "docx_matches": [
                                {
                                    "unit_kind": "paragraph",
                                    "paragraph_index": 1,
                                    "document_order": 1000,
                                }
                            ],
                        },
                    ],
                    "auxiliary_row_matches": [
                        {
                            "candidate_id": None,
                            "source_row_id": "SRC-CONTEXT",
                            "docx_matches": [
                                {
                                    "unit_kind": "paragraph",
                                    "paragraph_index": 2,
                                    "document_order": 2000,
                                }
                            ],
                        },
                    ],
                    "table_identity_matches": [],
                    "section_heading_match_count": 0,
                    "section_heading_matches": [],
                },
                "pdf_requirement_codes": {
                    "status": "not-registered",
                    "semantic_literal_rows": {
                        "status": "not-registered",
                        "literal_xhtml_row_count": 2,
                    },
                },
            },
        },
        "dictionaries": [],
        "coverage_gaps": {
            "artifact": {
                "role": "scope-coverage-gaps",
                "path": "work/coverage-gaps.md",
                "sha256": "0" * 64,
                "size_bytes": len("# Coverage gaps\n\nNo gaps.\n".encode("utf-8")),
            },
            "registered_gap_ids": [],
            "materialized_gap_ids": [],
            "content": "# Coverage gaps\n\nNo gaps.\n",
            "content_sha256": hashlib.sha256(
                "# Coverage gaps\n\nNo gaps.\n".encode("utf-8")
            ).hexdigest(),
            "status": "complete-literal-registered-artifact",
        },
        "mockup_attachments": [],
        "normalized_projection": graph.to_dict(),
        "test_cases": {
            "draft_sha256": gate.draft_sha256,
            "draft_markdown_included": False,
            "draft_markdown_omitted_reason": (
                "The gate-passed markdown is bound by identity.draft_sha256; "
                "reviewer receives structured designs."
            ),
            "designs": [item.to_dict() for item in cases],
        },
        "coverage_mapping": [
            {
                "source_row_id": prop.source_row_id,
                "assertion_id": prop.assertion_id,
                "property_id": prop.property_id,
                "obligation_id": obligation.obligation_id,
                "case_key": case.case_key,
                "tc_id": case.tc_id,
            },
            {
                "source_row_id": "SRC-CONTEXT",
                "assertion_id": "",
                "property_id": "",
                "obligation_id": "",
                "case_key": "",
                "tc_id": "",
            },
        ],
        "supporting_evidence_mapping": [],
        "design_support_mapping": [],
        "acceptance": reviewer_acceptance_contract(schema_version=2),
    }
    rows_by_id = {
        item["source_row_id"]: item for item in pack["literal_source_evidence"]
    }
    for row in rows_by_id.values():
        row["bounded_source_text_sha256"] = hashlib.sha256(
            row["bounded_source_text"].encode("utf-8")
        ).hexdigest()
    docx = pack["source_structure"]["docx_xhtml_pdf_parity"]["docx_xhtml"]
    for match in (*docx["row_matches"], *docx["auxiliary_row_matches"]):
        row = rows_by_id[match["source_row_id"]]
        for field in (
            "source_path",
            "source_file_sha256",
            "source_locator",
            "bounded_source_text_sha256",
            "element_kind",
        ):
            match[field] = row[field]
    return pack


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
                f"Проверка {probe} сопоставила указанный шаг и oracle; "
                "конкретный witness не найден."
            ),
            "binding_role": binding_role,
            "obligation_id": obligation_id,
            "binding_item_index": binding_item_index,
            "trigger_or_step": trigger_or_step,
            "oracle": oracle,
        }
        for probe in REVIEWER_FALSIFICATION_PROBES
    }


def _accepted_review_v2(graph, request):  # type: ignore[no-untyped-def]
    case = graph.cases[0]
    design = request["reviewer_evidence_pack"]["test_cases"]["designs"][0]
    return {
        "schema_version": 2,
        "graph_digest": graph.digest,
        "draft_sha256": request["draft_sha256"],
        "evidence_pack_sha256": request["evidence_pack_sha256"],
        "decision": "accepted",
        "case_results": [
            {
                "case_key": case.case_key,
                "tc_id": case.tc_id,
                "obligation_id": case.obligation_ids[0],
                "status": "covered",
                "comment": "Покрытие проверено по буквальному источнику.",
                "falsification": _passed_falsification(
                    obligation_id=case.obligation_ids[0],
                    trigger_or_step=design["steps"][-1],
                    oracle=design["expected_result"],
                ),
            }
        ],
        "source_projection_findings": [],
        "test_case_findings": [],
        "summary": "Набор принят.",
    }


def _v2_multi_case_request(graph, cases, gate, markdown, revision_review_scope=None):  # type: ignore[no-untyped-def]
    pack = _v2_pack(graph, cases, gate, markdown)
    prop = graph.properties[0]
    pack["coverage_mapping"] = [
        {
            "source_row_id": prop.source_row_id,
            "assertion_id": prop.assertion_id,
            "property_id": prop.property_id,
            "obligation_id": case.obligation_ids[0],
            "case_key": case.case_key,
            "tc_id": case.tc_id,
        }
        for case in graph.cases
    ]
    pack["coverage_mapping"].append(
        {
            "source_row_id": "SRC-CONTEXT",
            "assertion_id": "",
            "property_id": "",
            "obligation_id": "",
            "case_key": "",
            "tc_id": "",
        }
    )
    return build_reviewer_request(
        graph=graph,
        cases=cases,
        gate=gate,
        evidence_pack=pack,
        revision_review_scope=revision_review_scope,
    )


def _v2_review_for_request(graph, request, findings=()):  # type: ignore[no-untyped-def]
    graph_cases = {item.case_key: item for item in graph.cases}
    results = []
    for design in request["reviewer_evidence_pack"]["test_cases"]["designs"]:
        case = graph_cases[design["case_key"]]
        results.append(
            {
                "case_key": case.case_key,
                "tc_id": case.tc_id,
                "obligation_id": case.obligation_ids[0],
                "status": (
                    "calibration-pending"
                    if design.get("status") == "candidate-ui-calibration"
                    or case.status == "candidate-ui-calibration"
                    else "covered"
                ),
                "comment": "Reviewed against bound evidence.",
                "falsification": _passed_falsification(
                    obligation_id=case.obligation_ids[0],
                    trigger_or_step=design["steps"][-1],
                    oracle=design["expected_result"],
                ),
            }
        )
    return {
        "schema_version": 2,
        "graph_digest": graph.digest,
        "draft_sha256": request["draft_sha256"],
        "evidence_pack_sha256": request["evidence_pack_sha256"],
        "decision": "changes-required" if findings else "accepted",
        "case_results": results,
        "source_projection_findings": [],
        "test_case_findings": list(findings),
        "summary": "Reviewed.",
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

    def test_runtime_writer_request_uses_model_prose_contract_and_mockup_aliases(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())

        request = build_runtime_writer_request(
            graph,
            plan,
            mockup_label_aliases=(
                {
                    "canonical_ft_name": "Добавить контактное лицо",
                    "label_from_mockup": "+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО",
                },
            ),
        )

        self.assertEqual("model-runtime-prose", request["writer_mode"])
        self.assertEqual(1, len(request["cases"]))
        self.assertTrue(request["constraints"]["model_authors_runtime_prose"])
        self.assertTrue(request["constraints"]["use_label_from_mockup_for_runtime_text"])
        preconditions_contract = request["route_contract"]["preconditions_contract"]
        self.assertEqual("Не требуются.", preconditions_contract["empty_sentinel"])
        self.assertIn("Открыть карточку", preconditions_contract["allowed"])
        self.assertIn("Перейти в блок", preconditions_contract["allowed"])
        self.assertIn(
            "Открыта карточка ...",
            preconditions_contract["forbidden_state_only_examples"],
        )
        self.assertIn(
            "one exact source-backed UI control/action path",
            preconditions_contract["single_control_path_policy"],
        )
        self.assertIn("или", preconditions_contract["single_control_path_policy"])
        self.assertIn("/", preconditions_contract["single_control_path_policy"])
        self.assertIn(
            "Дважды нажать виджет `+` или кнопку `Добавить контактное лицо`.",
            preconditions_contract["forbidden_ambiguous_examples"],
        )
        self.assertIn(
            "Нажать кнопку «Добавить контактное лицо» два раза",
            preconditions_contract["repeated_action_policy"],
        )
        test_design_contract = request["route_contract"]["test_design_contract"]
        self.assertIn(
            "every exact backticked prepared value",
            test_design_contract["prepared_value_execution"],
        )
        self.assertIn(
            "поочередно вводить каждое значение",
            test_design_contract["prepared_value_execution"],
        )
        self.assertIn(
            "cleanup oracle",
            test_design_contract["cleanup_oracle_preservation"],
        )
        self.assertIn(
            "Проверить, что ... удалена",
            test_design_contract["cleanup_oracle_preservation"],
        )
        self.assertIn(
            "protected_runtime_fragments.cleanup_oracles",
            test_design_contract["cleanup_oracle_preservation"],
        )
        self.assertIn(
            "entrypoint_preconditions",
            test_design_contract["entrypoint_precondition_preservation"],
        )
        self.assertIn(
            "Do not omit or rephrase",
            test_design_contract["entrypoint_precondition_preservation"],
        )
        entrypoint_fragments = [
            fragment
            for case in request["cases"]
            for fragment in case["protected_runtime_fragments"][
                "entrypoint_preconditions"
            ]
        ]
        self.assertEqual(["Открыть карточку клиента."], entrypoint_fragments)
        cleanup_fragments = [
            fragment
            for case in request["cases"]
            for fragment in case["protected_runtime_fragments"][
                "cleanup_oracles"
            ]
        ]
        self.assertEqual([], cleanup_fragments)
        self.assertIn(
            "Immediate input or selection proves only current visible value",
            test_design_contract["no_persistence_without_commit"],
        )
        self.assertIn(
            "mask/template",
            test_design_contract["no_sibling_template_or_mask_oracle"],
        )
        self.assertIn(
            "always-visible/invariant seed",
            test_design_contract["bounded_invariant_language"],
        )
        self.assertIn("всегда", test_design_contract["bounded_invariant_language"])
        self.assertIn("постоянно", test_design_contract["bounded_invariant_language"])
        self.assertIn(
            "Do not combine acceptance of a valid value and rejection",
            test_design_contract["one_dominant_oracle_polarity_per_case"],
        )
        self.assertIn(
            "Use `негативный` for rejection",
            test_design_contract["case_type_consistency"],
        )
        self.assertIn(
            "whitespace",
            test_design_contract["input_restriction_classes"],
        )
        self.assertIn(
            "when the source explicitly constrains script/alphabet",
            test_design_contract["input_restriction_classes"],
        )
        self.assertIn(
            "Latin letters are valid",
            test_design_contract["input_restriction_classes"],
        )
        self.assertIn(
            "not greater than",
            test_design_contract["boundary_value_classes"],
        )
        self.assertIn(
            "current date + 1 day",
            test_design_contract["boundary_value_classes"],
        )
        self.assertIn(
            "Implementation observations",
            test_design_contract["unsupported_observation_policy"],
        )
        self.assertIn(
            "source-bound risk",
            test_design_contract["priority_policy"],
        )
        self.assertFalse(request["constraints"]["old_test_cases_available"])
        self.assertTrue(
            request["constraints"]["preserve_prepared_values_in_steps"]
        )
        self.assertEqual(
            "+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО",
            request["mockup_label_aliases"][0]["label_from_mockup"],
        )

    def test_runtime_writer_request_exposes_protected_cleanup_oracles(self) -> None:
        graph, context = _repeater_graph_and_context()
        plan = build_test_design_plan(graph, context=context)

        request = build_runtime_writer_request(graph, plan)

        cleanup_fragments = {
            case["case_key"]: case["protected_runtime_fragments"][
                "cleanup_oracles"
            ]
            for case in request["cases"]
        }
        add_key = "customer|customer-name|source-add-row|repeater-add|always"
        self.assertIn(
            "Проверить, что добавленная тестовая строка удалена",
            cleanup_fragments[add_key],
        )

    def test_runtime_writer_schema_accepts_exact_structured_prose_payload(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        schema = runtime_writer_response_schema([seed.case_key], graph.digest)
        payload = _runtime_writer_payload(graph, [_runtime_writer_case(seed)])

        validate_openai_strict_output_instance(payload, schema)

    def test_runtime_writer_cannot_change_tc_id_or_omit_cases(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        drift = _runtime_writer_payload(
            graph,
            [_runtime_writer_case(seed, tc_id="TC-DRIFT")],
        )

        with self.assertRaisesRegex(IterationContractError, "TC-ID drift"):
            validate_runtime_writer_response(
                drift,
                graph=graph,
                plan=plan,
                context=_context(),
            )

        omitted = _runtime_writer_payload(graph, [])
        with self.assertRaisesRegex(IterationContractError, "omitted cases"):
            validate_runtime_writer_response(
                omitted,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_blocks_all_cases_unresolved_as_route_failure(self) -> None:
        graph = _multi_runtime_graph()
        plan = build_test_design_plan(graph, context=_context())
        payload = _runtime_writer_payload(
            graph,
            [],
            unresolved=(
                {
                    "case_key": seed.case_key,
                    "reason": (
                        "Requested registered-card projection cannot be represented "
                        "by the response schema."
                    ),
                }
                for seed in plan.deterministic_cases
            ),
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "route failure: all input seed cases",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_accepts_multi_seed_model_runtime_response(self) -> None:
        graph = _multi_runtime_graph()
        plan = build_test_design_plan(graph, context=_context())
        payload = _runtime_writer_payload(
            graph,
            (
                _runtime_writer_case(
                    seed,
                    title=f"Runtime prose case {index}",
                )
                for index, seed in enumerate(plan.deterministic_cases, start=1)
            ),
        )

        designs, unresolved = validate_runtime_writer_response(
            payload,
            graph=graph,
            plan=plan,
            context=_context(),
        )

        self.assertEqual((), unresolved)
        self.assertEqual(2, len(designs))
        self.assertEqual(
            tuple(seed.case_key for seed in plan.deterministic_cases),
            tuple(design.case_key for design in designs),
        )

    def test_runtime_writer_must_execute_seed_prepared_values(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        valid_seed = replace(
            plan.deterministic_cases[0],
            case_type="позитивный",
            test_data=("Допустимое значение: `Иван-Петров`.",),
            steps=(
                "Ввести `Иван-Петров` в поле «Фамилия».",
                "Проверить, что поле «Фамилия» отображает значение `Иван-Петров`.",
            ),
            expected_result="Поле «Фамилия» отображает значение `Иван-Петров`.",
        )
        valid_plan = replace(plan, deterministic_cases=(valid_seed,))
        missing_valid_payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    valid_seed,
                    steps=["Проверить поле «Фамилия»."],
                )
            ],
        )
        with self.assertRaisesRegex(
            IterationContractError,
            "left seed prepared values unexecuted.*Иван-Петров",
        ):
            validate_runtime_writer_response(
                missing_valid_payload,
                graph=graph,
                plan=valid_plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_negated_rejection_positive_oracle(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = replace(
            plan.deterministic_cases[0],
            case_type="позитивный",
            test_data=("Допустимое значение: `Иван-Петров`.",),
            steps=(
                "Ввести `Иван-Петров` в поле «Фамилия».",
                "Проверить, что поле «Фамилия» отображает значение `Иван-Петров`.",
            ),
            expected_result="Поле «Фамилия» отображает значение `Иван-Петров`.",
        )
        valid_plan = replace(plan, deterministic_cases=(seed,))
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    steps=[
                        "Ввести `Иван-Петров` в поле «Фамилия».",
                        "Проверить, что значение `Иван-Петров` не отклоняется по правилу формата.",
                    ],
                    expected_result="Значение `Иван-Петров` не отклоняется по правилу формата.",
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "unsupported positive acceptance oracle",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=valid_plan,
                context=_context(),
            )

        seed = replace(
            plan.deterministic_cases[0],
            status="candidate-ui-calibration",
            case_type="негативный",
            test_data=(
                "Недопустимое значение: `Иванов1`.",
                "Недопустимое значение: `Иван Петров`.",
                "Недопустимое значение: `Иванов@`.",
            ),
            steps=(
                "Ввести `Иванов1` в поле «Фамилия».",
                "Зафиксировать фактический UI-отклик для значения `Иванов1`.",
                "Очистить поле «Фамилия».",
                "Ввести `Иван Петров` в поле «Фамилия».",
                "Зафиксировать фактический UI-отклик для значения `Иван Петров`.",
                "Очистить поле «Фамилия».",
                "Ввести `Иванов@` в поле «Фамилия».",
                "Зафиксировать фактический UI-отклик для значения `Иванов@`.",
            ),
            expected_result=(
                "Фактический UI-отклик для недопустимых значений зафиксирован "
                "без подмены ожидаемым сообщением."
            ),
            calibration_question=(
                "Какой точный UI-отклик подтверждает, что недопустимые значения "
                "не принимаются?"
            ),
        )
        plan = replace(plan, deterministic_cases=(seed,))
        valid_payload = _runtime_writer_payload(graph, [_runtime_writer_case(seed)])

        designs, unresolved = validate_runtime_writer_response(
            valid_payload,
            graph=graph,
            plan=plan,
            context=_context(),
        )

        self.assertEqual((), unresolved)
        self.assertEqual(seed.steps, designs[0].steps)

        invalid_payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    steps=[
                        "Ввести `Иванов1` в поле «Фамилия».",
                        "Зафиксировать фактический UI-отклик для значения `Иванов1`.",
                    ],
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "left seed prepared values unexecuted.*Иван Петров.*Иванов@",
        ):
            validate_runtime_writer_response(
                invalid_payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_must_preserve_seed_cleanup_oracle(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = replace(
            plan.deterministic_cases[0],
            postconditions=(
                "Для добавленной тестовой строки выполнить действие: "
                "Нажать кнопку `Корзина`. "
                "Проверить, что добавленная тестовая строка удалена.",
            ),
        )
        plan = replace(plan, deterministic_cases=(seed,))
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    postconditions=["Нажать кнопку `Корзина` в добавленной строке."],
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "removed seed cleanup oracle.*добавленная тестовая строка удалена",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_persistence_oracle_without_commit_action(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    preconditions=["Перейти к блоку `Контактные лица`."],
                    steps=[
                        "Ввести `Иван` в поле «Фамилия».",
                        "Проверить, что в поле установлено значение `Иван`.",
                    ],
                    expected_result=(
                        "Поле «Фамилия» доступно для редактирования и "
                        "сохраняет введённое значение `Иван`."
                    ),
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "unsupported persistence oracle.*commit, save, submit",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_unseeded_mask_template_oracle(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    expected_result=(
                        seed.expected_result.rstrip(".")
                        + " с учетом маски поля."
                    ),
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "unsupported mask/template oracle",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_unbounded_language_for_bounded_invariant(
        self,
    ) -> None:
        graph, context = _repeater_graph_and_context()
        plan = build_test_design_plan(graph, context=context)
        seed = next(
            item
            for item in plan.deterministic_cases
            if item.tc_id == "TC-CUST-0123456789"
        )
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    title="Постоянное отображение кнопки `Добавить`",
                    expected_result="Кнопка `Добавить` всегда отображается.",
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "overclaimed bounded invariant visibility",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=context,
            )

    def test_runtime_writer_returns_model_prose_but_runner_preserves_identity_and_traceability(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = {
            "schema_version": 1,
            "writer_mode": "model-runtime-prose",
            "graph_digest": graph.digest,
            "route_contract_ack": "runtime-prose-one-case-per-seed",
            "cases": [
                _runtime_writer_case(
                    seed,
                    title="Модельно написанный кейс",
                    steps=["Ввести `Иван` в поле «Имя»."],
                    expected_result="Поле «Имя» отображает значение `Иван`.",
                )
            ],
            "unresolved": [],
        }

        designs, unresolved = validate_runtime_writer_response(
            payload,
            graph=graph,
            plan=plan,
            context=_context(),
        )

        self.assertEqual((), unresolved)
        self.assertEqual(seed.case_key, designs[0].case_key)
        self.assertEqual(seed.tc_id, designs[0].tc_id)
        self.assertEqual(seed.traceability, designs[0].traceability)
        self.assertEqual("Модельно написанный кейс", designs[0].title)
        self.assertEqual(("Ввести `Иван` в поле «Имя».",), designs[0].steps)

    def test_runtime_writer_preserves_no_test_data_seed(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = replace(
            plan.deterministic_cases[0],
            test_data=("Не требуются.",),
        )
        plan = replace(plan, deterministic_cases=(seed,))
        self.assertEqual(("Не требуются.",), seed.test_data)
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    test_data=["Значение для проверки: `Иван`."],
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "changed no-test-data seed",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_nonconcrete_value_for_no_data_seed(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = replace(
            plan.deterministic_cases[0],
            test_data=("Не требуются.",),
        )
        plan = replace(plan, deterministic_cases=(seed,))
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    steps=[
                        "Нажать поле «Имя».",
                        "Выбрать любое доступное значение.",
                    ],
                    expected_result="Поле «Имя» отображает выбранное значение.",
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "non-concrete runtime value",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_accepts_action_oriented_preconditions(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    preconditions=[
                        "Открыть карточку клиента.",
                        "Открыть карточку `Заявка`.",
                        "Перейти в блок `Контактные лица`.",
                    ],
                )
            ],
        )

        designs, unresolved = validate_runtime_writer_response(
            payload,
            graph=graph,
            plan=plan,
            context=_context(),
        )

        self.assertEqual((), unresolved)
        self.assertEqual(
            (
                "Открыть карточку клиента.",
                "Открыть карточку `Заявка`.",
                "Перейти в блок `Контактные лица`.",
            ),
            designs[0].preconditions,
        )

    def test_runtime_writer_must_preserve_seed_entrypoint_preconditions(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    preconditions=["Нажать кнопку `Добавить контактное лицо`."],
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "removed seed entrypoint precondition",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_case_type_drift_and_rejection_oracle_mismatch(
        self,
    ) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        drift = _runtime_writer_payload(
            graph,
            [_runtime_writer_case(seed, case_type="негативный")],
        )

        with self.assertRaisesRegex(IterationContractError, "case_type drift"):
            validate_runtime_writer_response(
                drift,
                graph=graph,
                plan=plan,
                context=_context(),
            )

        rejection_oracle = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    expected_result="Поле показывает ошибку валидации и значение не сохраняется.",
                )
            ],
        )
        with self.assertRaisesRegex(
            IterationContractError,
            "positive case_type conflicts",
        ):
            validate_runtime_writer_response(
                rejection_oracle,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_accepts_positive_optionalness_no_error_oracle(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        optionalness_oracle = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    expected_result=(
                        "Ошибка обязательности для пустого поля «Отчество» "
                        "не отображается."
                    ),
                )
            ],
        )

        designs, unresolved = validate_runtime_writer_response(
            optionalness_oracle,
            graph=graph,
            plan=plan,
            context=_context(),
        )

        self.assertEqual((), unresolved)
        self.assertEqual(
            "Ошибка обязательности для пустого поля «Отчество» не отображается.",
            designs[0].expected_result,
        )

    def test_runtime_writer_rejects_mixed_valid_and_invalid_input_actions(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    steps=[
                        "Ввести недопустимое значение `1` в поле «Имя».",
                        "Ввести допустимое значение `Иван` в поле «Имя».",
                    ],
                    expected_result="Поле «Имя» отображает значение `Иван`.",
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "mixed positive/negative runtime prose",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_ambiguous_alternative_precondition(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    preconditions=[
                        "Перейти в блок `Контактные лица`.",
                        "Дважды нажать виджет `+` или кнопку `Добавить контактное лицо`.",
                    ],
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "ambiguous alternative control/action.*Дважды нажать виджет",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_accepts_exact_repeated_precondition(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    preconditions=[
                        "Открыть карточку клиента.",
                        "Перейти в блок `Контактные лица`.",
                        "Нажать кнопку «Добавить контактное лицо» два раза.",
                    ],
                )
            ],
        )

        designs, unresolved = validate_runtime_writer_response(
            payload,
            graph=graph,
            plan=plan,
            context=_context(),
        )

        self.assertEqual((), unresolved)
        self.assertEqual(
            (
                "Открыть карточку клиента.",
                "Перейти в блок `Контактные лица`.",
                "Нажать кнопку «Добавить контактное лицо» два раза.",
            ),
            designs[0].preconditions,
        )

    def test_runtime_writer_rejects_state_only_preconditions(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = _runtime_writer_payload(
            graph,
            [
                _runtime_writer_case(
                    seed,
                    preconditions=[
                        "Открыта карточка `Заявка`, блок `Контактные лица`.",
                    ],
                )
            ],
        )

        with self.assertRaisesRegex(
            IterationContractError,
            "non-reproducible precondition.*Открыта карточка",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_blocks_stale_label_when_mockup_alias_is_declared(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = {
            "schema_version": 1,
            "writer_mode": "model-runtime-prose",
            "graph_digest": graph.digest,
            "route_contract_ack": "runtime-prose-one-case-per-seed",
            "cases": [
                _runtime_writer_case(
                    seed,
                    steps=[
                        "Ввести `Иван` в поле «Имя».",
                        "Нажать кнопку «Добавить контактное лицо».",
                    ],
                )
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(IterationContractError, "mockup visible label drift"):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
                mockup_label_aliases=(
                    {
                        "canonical_ft_name": "Добавить контактное лицо",
                        "label_from_mockup": "+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО",
                    },
                ),
            )

        payload["cases"][0]["steps"] = [
            "Ввести `Иван` в поле «Имя».",
            "Нажать кнопку «+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО»."
        ]
        designs, unresolved = validate_runtime_writer_response(
            payload,
            graph=graph,
            plan=plan,
            context=_context(),
            mockup_label_aliases=(
                {
                    "canonical_ft_name": "Добавить контактное лицо",
                    "label_from_mockup": "+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО",
                },
            ),
        )
        self.assertEqual((), unresolved)
        self.assertEqual(
            (
                "Ввести `Иван` в поле «Имя».",
                "Нажать кнопку «+ ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО».",
            ),
            designs[0].steps,
        )

    def test_runtime_writer_rejects_internal_ids_in_human_runtime_fields(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = {
            "schema_version": 1,
            "writer_mode": "model-runtime-prose",
            "graph_digest": graph.digest,
            "route_contract_ack": "runtime-prose-one-case-per-seed",
            "cases": [
                _runtime_writer_case(
                    seed,
                    title="subject:4b12af7e368d24cd",
                    steps=[
                        "OBL-BSR-179-DEFAULT-HIDDEN",
                        "ATOM-012",
                        "ASSERT-012",
                        "SRC-ROW-006",
                        "BSR 179",
                    ],
                )
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(
            IterationContractError,
            "internal identifier in title.*subject:4b12af7e368d24cd",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

        payload["cases"][0]["title"] = "Проверка видимости поля"
        with self.assertRaisesRegex(
            IterationContractError,
            "internal identifier in steps.*OBL-BSR-179-DEFAULT-HIDDEN",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_value_only_preconditions(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = {
            "schema_version": 1,
            "writer_mode": "model-runtime-prose",
            "graph_digest": graph.digest,
            "route_contract_ack": "runtime-prose-one-case-per-seed",
            "cases": [
                _runtime_writer_case(
                    seed,
                    title="Проверка значения справочника",
                    preconditions=["супруг/супруга", "отец/мать"],
                    steps=["Выбрать значение `супруг/супруга` в списке."],
                )
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(
            IterationContractError,
            "non-reproducible precondition.*супруг/супруга",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

    def test_runtime_writer_rejects_reordered_entrypoint_preconditions(self) -> None:
        graph = _graph()
        graph = replace(
            graph,
            properties=(
                *graph.properties,
                CoverageProperty(
                    property_id="PROP-CARD-ENTRYPOINT",
                    assertion_id="ASSERT-CARD-ENTRYPOINT",
                    property_key="customer-card:entrypoint",
                    subject_key="customer-card",
                    property_kind="context",
                    source_row_id="SRC-CARD-ENTRYPOINT",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[0]/*[2]",
                    source_text_sha256="f" * 64,
                    canonical_statement="Открыть карточку `Заявка`.",
                    requirement_codes=(),
                    disposition="not-applicable",
                ),
                CoverageProperty(
                    property_id="PROP-BLOCK-ENTRYPOINT",
                    assertion_id="ASSERT-BLOCK-ENTRYPOINT",
                    property_key="contact-persons:block-entrypoint",
                    subject_key="contact-persons",
                    property_kind="context",
                    source_row_id="SRC-BLOCK-ENTRYPOINT",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[0]/*[3]",
                    source_text_sha256="f" * 64,
                    canonical_statement="Перейти к блоку `Контактные лица`.",
                    requirement_codes=(),
                    disposition="not-applicable",
                ),
            ),
        )
        context = replace(
            _context(),
            base_preconditions=(
                "Открыть карточку `Заявка`.",
                "Перейти к блоку `Контактные лица`.",
            ),
        )
        plan = build_test_design_plan(graph, context=context)
        seed = plan.deterministic_cases[0]
        payload = {
            "schema_version": 1,
            "writer_mode": "model-runtime-prose",
            "graph_digest": graph.digest,
            "route_contract_ack": "runtime-prose-one-case-per-seed",
            "cases": [
                _runtime_writer_case(
                    seed,
                    preconditions=[
                        "Перейти к блоку `Контактные лица`.",
                        "Открыть карточку `Заявка`.",
                    ],
                )
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(
            IterationContractError,
            "reordered seed entrypoint preconditions",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=context,
            )

    def test_runtime_writer_protects_in_block_entrypoint_precondition(self) -> None:
        graph = _graph()
        graph = replace(
            graph,
            properties=(
                *graph.properties,
                CoverageProperty(
                    property_id="PROP-IN-BLOCK-ENTRYPOINT",
                    assertion_id="ASSERT-IN-BLOCK-ENTRYPOINT",
                    property_key="contacts:block-entrypoint",
                    subject_key="contacts",
                    property_kind="context",
                    source_row_id="SRC-IN-BLOCK-ENTRYPOINT",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[0]/*[2]",
                    source_text_sha256="f" * 64,
                    canonical_statement="Перейти в блок `Контактные лица`.",
                    requirement_codes=(),
                    disposition="not-applicable",
                ),
            ),
        )
        context = replace(
            _context(),
            base_preconditions=("Перейти в блок `Контактные лица`.",),
        )
        plan = build_test_design_plan(graph, context=context)
        seed = plan.deterministic_cases[0]
        payload = {
            "schema_version": 1,
            "writer_mode": "model-runtime-prose",
            "graph_digest": graph.digest,
            "route_contract_ack": "runtime-prose-one-case-per-seed",
            "cases": [
                _runtime_writer_case(
                    seed,
                    preconditions=["Открыть раздел контактных лиц."],
                )
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(
            IterationContractError,
            "removed seed entrypoint precondition",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=context,
            )

    def test_runtime_writer_rejects_steps_without_user_action_or_check(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        seed = plan.deterministic_cases[0]
        payload = {
            "schema_version": 1,
            "writer_mode": "model-runtime-prose",
            "graph_digest": graph.digest,
            "route_contract_ack": "runtime-prose-one-case-per-seed",
            "cases": [
                _runtime_writer_case(
                    seed,
                    title="Проверка отображения поля",
                    preconditions=["Не требуются."],
                    steps=["Поле `Имя` отображается."],
                )
            ],
            "unresolved": [],
        }

        with self.assertRaisesRegex(
            IterationContractError,
            "omitted executable user action/check step",
        ):
            validate_runtime_writer_response(
                payload,
                graph=graph,
                plan=plan,
                context=_context(),
            )

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

    def test_suite_gate_requires_sequential_display_numbers(self) -> None:
        graph = _multi_runtime_graph()
        plan = build_test_design_plan(graph, context=_context())
        cases = plan.deterministic_cases
        markdown = render_test_cases(cases, scope_title="Данные клиента")
        missing_number_markdown = markdown.replace("**№:** 2\n", "", 1)

        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=missing_number_markdown,
            checked_path="shadow.md",
        )

        self.assertFalse(gate.passed)
        self.assertIn("display number missing or duplicated", " ".join(gate.findings))

    def test_suite_gate_requires_scope_entrypoint_preconditions(self) -> None:
        base_graph = _graph()
        graph = replace(
            base_graph,
            properties=(
                *base_graph.properties,
                CoverageProperty(
                    property_id="PROP-CARD-ENTRYPOINT",
                    assertion_id="ASSERT-CARD-ENTRYPOINT",
                    property_key="application-card:entrypoint",
                    subject_key="application-card",
                    property_kind="context",
                    source_row_id="SRC-CARD-ENTRYPOINT",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[0]/*[2]",
                    source_text_sha256="f" * 64,
                    canonical_statement="Открыть карточку `Заявка`.",
                    requirement_codes=(),
                    disposition="not-applicable",
                ),
                CoverageProperty(
                    property_id="PROP-BLOCK-ENTRYPOINT",
                    assertion_id="ASSERT-BLOCK-ENTRYPOINT",
                    property_key="contact-persons:block-entrypoint",
                    subject_key="contact-persons",
                    property_kind="context",
                    source_row_id="SRC-BLOCK-ENTRYPOINT",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[0]/*[3]",
                    source_text_sha256="f" * 64,
                    canonical_statement="Перейти к блоку `Контактные лица`.",
                    requirement_codes=(),
                    disposition="not-applicable",
                ),
            ),
        )
        context = replace(
            _context(),
            base_preconditions=(
                "Открыть карточку `Заявка`.",
                "Перейти к блоку `Контактные лица`.",
            ),
        )
        plan = build_test_design_plan(graph, context=context)
        broken_case = replace(
            plan.deterministic_cases[0],
            preconditions=("Перейти к блоку `Контактные лица`.",),
        )
        markdown = render_test_cases((broken_case,), scope_title=context.scope_title)

        gate = validate_suite(
            graph=graph,
            cases=(broken_case,),
            markdown=markdown,
            checked_path="shadow.md",
            context=context,
        )

        self.assertFalse(gate.passed)
        self.assertIn("scope entrypoint precondition missing", " ".join(gate.findings))

    def test_suite_gate_rejects_negated_rejection_positive_oracle(self) -> None:
        graph = _graph()
        plan = build_test_design_plan(graph, context=_context())
        case = replace(
            plan.deterministic_cases[0],
            case_type="позитивный",
            steps=(
                "Ввести `Иван-Петров` в поле «Имя».",
                "Проверить, что значение `Иван-Петров` не отклоняется по правилу формата.",
            ),
            expected_result="Значение `Иван-Петров` не отклоняется по правилу формата.",
        )
        markdown = render_test_cases((case,), scope_title="Данные клиента")

        gate = validate_suite(
            graph=graph,
            cases=(case,),
            markdown=markdown,
            checked_path="shadow.md",
        )

        self.assertFalse(gate.passed)
        self.assertIn("unsupported positive acceptance oracle", " ".join(gate.findings))

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

    def test_reviewer_v2_binds_complete_evidence_and_separate_findings(self) -> None:
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
        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=_v2_pack(graph, cases, gate, markdown),
        )
        schema = reviewer_response_schema(
            [
                (
                    graph.cases[0].case_key,
                    graph.cases[0].tc_id,
                    graph.cases[0].obligation_ids[0],
                    graph.cases[0].status,
                )
            ],
            graph_digest=graph.digest,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )

        self.assertEqual(2, request["schema_version"])
        self.assertIn(
            "только",
            request["reviewer_evidence_pack"]["literal_source_evidence"][0][
                "bounded_source_text"
            ],
        )
        self.assertNotIn("old_test_cases", request)
        test_cases = request["reviewer_evidence_pack"]["test_cases"]
        self.assertNotIn("draft_markdown", test_cases)
        self.assertEqual(gate.draft_sha256, test_cases["draft_sha256"])
        self.assertFalse(test_cases["draft_markdown_included"])
        acceptance = request["reviewer_evidence_pack"]["acceptance"]
        self.assertEqual(2, acceptance["reviewer_policy_version"])
        self.assertFalse(acceptance["review_only_projected_behavior"])
        self.assertTrue(acceptance["review_literal_source_against_projection"])
        self.assertTrue(
            acceptance["exclusive_allowed_set_requires_disallowed_class"]
        )
        self.assertTrue(
            acceptance[
                "exact_numeric_length_requires_length_boundaries_and_nonnumeric_class"
            ]
        )
        self.assertTrue(
            acceptance["repeater_lifecycle_expectations_are_source_bound"]
        )
        self.assertTrue(acceptance["registered_coverage_gaps_are_binding"])
        self.assertTrue(
            acceptance["supporting_source_bindings_must_be_reviewed"]
        )
        self.assertTrue(acceptance["design_support_chains_must_be_reviewed"])
        self.assertTrue(
            acceptance["source_bound_cleanup_restoration_is_allowed"]
        )
        self.assertTrue(
            acceptance["test_case_findings_require_exact_binding_role"]
        )
        self.assertTrue(acceptance["primary_coverage_mapping_is_one_per_case"])
        self.assertTrue(acceptance["adversarial_false_pass_check"])
        self.assertTrue(acceptance["adversarial_false_fail_check"])
        self.assertTrue(acceptance["failure_attribution_check"])
        self.assertTrue(acceptance["trigger_fidelity_check"])
        self.assertTrue(
            acceptance["probe_findings_require_concrete_witness"]
        )
        self.assertTrue(
            acceptance["probe_findings_require_same_chain_bound_finding"]
        )
        self.assertTrue(
            acceptance["related_probe_findings_may_share_same_case_root_finding"]
        )
        self.assertTrue(
            acceptance["per_probe_evidence_chain_binding_required"]
        )
        self.assertTrue(
            acceptance["per_probe_evidence_item_binding_required"]
        )
        self.assertTrue(
            acceptance[
                "artifact_proven_findings_do_not_require_hypothetical_witness"
            ]
        )
        self.assertTrue(acceptance["per_case_falsification_receipt_required"])
        self.assertFalse(
            acceptance["live_falsification_receipt_allows_not_recorded"]
        )
        self.assertTrue(acceptance["passed_falsification_requires_no_finding"])
        self.assertTrue(
            acceptance["finding_falsification_requires_real_bound_defect"]
        )
        self.assertTrue(
            acceptance["reviewer_must_not_block_when_no_defects_are_found"]
        )
        self.assertTrue(acceptance["one_oracle_polarity_per_case"])
        self.assertTrue(acceptance["positive_tc_must_not_expect_rejection"])
        self.assertTrue(
            acceptance["positive_field_current_value_oracle_is_supported"]
        )
        self.assertTrue(
            acceptance["commit_not_required_for_current_visible_value_only"]
        )
        self.assertTrue(
            acceptance["positive_field_display_must_not_claim_save_or_validation"]
        )
        self.assertTrue(acceptance["input_restrictions_require_equivalence_classes"])
        self.assertTrue(
            acceptance[
                "unsupported_alphabet_or_integration_observation_requires_gap"
            ]
        )
        self.assertTrue(acceptance["priority_must_follow_source_bound_risk"])
        self.assertTrue(
            acceptance["compact_reviewer_context_uses_structured_test_cases"]
        )
        self.assertTrue(
            acceptance["draft_markdown_bound_by_sha256_not_model_context"]
        )
        self.assertIn("never return only changed", reviewer_prompt_instruction(2))
        self.assertIn("one dominant oracle polarity", reviewer_prompt_instruction(2))
        self.assertIn("whitespace", reviewer_prompt_instruction(2))
        self.assertIn("alphabet/script", reviewer_prompt_instruction(2))
        self.assertIn("source_review_attestation", reviewer_prompt_instruction(2))
        self.assertIn("accepted clarification records", reviewer_prompt_instruction(2))
        self.assertIn("current date + 1 day", reviewer_prompt_instruction(2))
        self.assertIn("Latin letters are a supported positive representative", reviewer_prompt_instruction(2))
        self.assertIn("priority follows source-bound risk", reviewer_prompt_instruction(2))
        self.assertIn("Immediate field display after entering", reviewer_prompt_instruction(2))
        self.assertIn("Do not require a separate commit/validation trigger", reviewer_prompt_instruction(2))
        self.assertIn("current-value coverage", reviewer_prompt_instruction(2))
        self.assertIn("changes-required requires", reviewer_prompt_instruction(2))
        self.assertIn("draft_markdown is intentionally omitted", reviewer_prompt_instruction(2))
        self.assertIn("test_cases.designs", reviewer_prompt_instruction(2))
        self.assertIn("source-backed same-row delete action", reviewer_prompt_instruction(2))
        self.assertIn("do not require separate final-row lifecycle evidence", reviewer_prompt_instruction(2))
        self.assertIn("source_projection_findings", schema["properties"])
        self.assertIn("test_case_findings", schema["properties"])
        self.assertEqual(1, schema["properties"]["case_results"]["minItems"])
        self.assertEqual(1, schema["properties"]["case_results"]["maxItems"])
        falsification_schema = schema["properties"]["case_results"]["items"][
            "properties"
        ]["falsification"]
        self.assertEqual(
            set(REVIEWER_FALSIFICATION_PROBES),
            set(falsification_schema["required"]),
        )
        self.assertEqual(
            {"finding", "passed"},
            set(
                falsification_schema["properties"]["false_pass"]["properties"][
                    "outcome"
                ]["enum"]
            ),
        )
        self.assertEqual(
            {
                "outcome",
                "detail",
                "binding_role",
                "obligation_id",
                "binding_item_index",
                "trigger_or_step",
                "oracle",
            },
            set(falsification_schema["properties"]["false_pass"]["required"]),
        )
        finding_schema = schema["properties"]["test_case_findings"]["items"]
        self.assertIn("falsification_probe", finding_schema["required"])
        self.assertEqual(
            {"", *REVIEWER_FALSIFICATION_PROBES},
            set(finding_schema["properties"]["falsification_probe"]["enum"]),
        )
        finding_type_enum = set(finding_schema["properties"]["finding_type"]["enum"])
        for finding_type in (
            "case-type-expected-result-mismatch",
            "missing-equivalence-class",
            "unsupported-alphabet-assumption",
            "priority-risk-mismatch",
            "implementation-observation-as-baseline",
        ):
            self.assertIn(finding_type, finding_type_enum)

        accepted, decision = validate_reviewer_response(
            _accepted_review_v2(graph, request),
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertTrue(accepted)
        self.assertEqual("accepted", decision)

        missing_receipt = _accepted_review_v2(graph, request)
        del missing_receipt["case_results"][0]["falsification"]
        with self.assertRaisesRegex(
            IterationContractError,
            "fields differ",
        ):
            validate_reviewer_response(
                missing_receipt,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )

        unrecorded = _accepted_review_v2(graph, request)
        for probe_result in unrecorded["case_results"][0][
            "falsification"
        ].values():
            probe_result["outcome"] = "not-recorded"
            probe_result["detail"] = "Legacy v1 response did not record this probe."
        with self.assertRaisesRegex(
            IterationContractError,
            "live reviewer response cannot use not-recorded falsification",
        ):
            validate_reviewer_response(
                unrecorded,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )
        accepted, decision = validate_reviewer_response(
            unrecorded,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
            allow_legacy_unrecorded_falsification=True,
        )
        self.assertTrue(accepted)
        self.assertEqual("accepted", decision)

        orphan_probe_finding = _accepted_review_v2(graph, request)
        orphan_probe_finding["decision"] = "changes-required"
        false_pass = orphan_probe_finding["case_results"][0]["falsification"][
            "false_pass"
        ]
        false_pass["outcome"] = "finding"
        false_pass["detail"] = "A local-only value would pass without persistence."
        with self.assertRaisesRegex(
            IterationContractError,
            "has no bound test_case_finding",
        ):
            validate_reviewer_response(
                orphan_probe_finding,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )

        bound_probe_finding = _accepted_review_v2(graph, request)
        bound_probe_finding["decision"] = "changes-required"
        bound_probe_finding["case_results"][0]["falsification"]["false_pass"].update(
            {
                "outcome": "finding",
                "detail": (
                    "A defective implementation can acknowledge the action without "
                    "persisting the value, yet the case would still pass."
                ),
            }
        )
        chain = request["reviewer_evidence_pack"]["coverage_mapping"][0]
        bound_probe_finding["test_case_findings"] = [
            {
                "severity": "error",
                "finding_type": "test-case-defect",
                "binding_role": "primary",
                "falsification_probe": "false_pass",
                **chain,
                "message": (
                    "Expected result does not prove persistence after the action."
                ),
            }
        ]
        accepted, decision = validate_reviewer_response(
            bound_probe_finding,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

        same_chain_root_finding = copy.deepcopy(bound_probe_finding)
        same_chain_root_finding["case_results"][0]["falsification"][
            "failure_attribution"
        ].update(
            {
                "outcome": "finding",
                "detail": (
                    "The same missing persistence check also makes the failure "
                    "attribution ambiguous."
                ),
            }
        )
        same_chain_root_finding["case_results"][0]["falsification"][
            "trigger_fidelity"
        ].update(
            {
                "outcome": "finding",
                "detail": (
                    "The same root defect is exposed through the trigger/oracle "
                    "chain and is represented by one bound finding."
                ),
            }
        )
        same_chain_root_finding["test_case_findings"][0][
            "falsification_probe"
        ] = "trigger_fidelity"
        accepted, decision = validate_reviewer_response(
            same_chain_root_finding,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

        mismatched_probe = copy.deepcopy(bound_probe_finding)
        mismatched_probe["test_case_findings"][0][
            "falsification_probe"
        ] = "false_fail"
        with self.assertRaisesRegex(
            IterationContractError,
            "has no matching falsification outcome",
        ):
            validate_reviewer_response(
                mismatched_probe,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )

        fabricated_basis = _accepted_review_v2(graph, request)
        fabricated_basis["case_results"][0]["falsification"]["false_pass"][
            "trigger_or_step"
        ] = "Несуществующий шаг проверки."
        with self.assertRaisesRegex(
            IterationContractError,
            "is not bound to the reviewed case and obligation",
        ):
            validate_reviewer_response(
                fabricated_basis,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )

    def test_revision_reviewer_request_defers_unchanged_calibration_finding(self) -> None:
        graph = _multi_runtime_graph()
        plan = build_test_design_plan(graph, context=_context())
        cases = tuple(sorted(plan.deterministic_cases, key=lambda item: item.case_key))
        markdown = render_test_cases(cases, scope_title=_context().scope_title)
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        changed = cases[0]
        unchanged = cases[1]
        request = _v2_multi_case_request(
            graph,
            cases,
            gate,
            markdown,
            revision_review_scope={
                "schema_version": 1,
                "changed_case_keys": [changed.case_key],
                "unchanged_byte_identical_cases": [
                    {
                        "case_key": unchanged.case_key,
                        "tc_id": unchanged.tc_id,
                        "block_sha256": "a" * 64,
                        "previous_reviewer_disposition": {
                            "previous_result_status": "calibration-pending",
                            "previous_findings": [
                                {
                                    "severity": "warning",
                                    "finding_type": "expected-result-unsupported",
                                }
                            ],
                        },
                    }
                ],
            },
        )
        chain = next(
            item
            for item in request["reviewer_evidence_pack"]["coverage_mapping"]
            if item["case_key"] == unchanged.case_key
        )
        finding = {
            "severity": "error",
            "finding_type": "expected-result-unsupported",
            "binding_role": "primary",
            "falsification_probe": "",
            **chain,
            "message": "Unchanged calibration baseline still needs UI evidence.",
        }

        response = _v2_review_for_request(graph, request, findings=(finding,))
        accepted, decision = validate_reviewer_response(
            response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )

        self.assertTrue(accepted)
        self.assertEqual("accepted", decision)
        self.assertEqual(
            (finding,),
            reviewer_deferred_test_case_findings(response, request),
        )

    def test_revision_reviewer_request_keeps_changed_case_finding_blocking(self) -> None:
        graph = _multi_runtime_graph()
        plan = build_test_design_plan(graph, context=_context())
        cases = tuple(sorted(plan.deterministic_cases, key=lambda item: item.case_key))
        markdown = render_test_cases(cases, scope_title=_context().scope_title)
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        changed = cases[0]
        unchanged = cases[1]
        request = _v2_multi_case_request(
            graph,
            cases,
            gate,
            markdown,
            revision_review_scope={
                "schema_version": 1,
                "changed_case_keys": [changed.case_key],
                "unchanged_byte_identical_cases": [
                    {
                        "case_key": unchanged.case_key,
                        "tc_id": unchanged.tc_id,
                        "block_sha256": "a" * 64,
                    }
                ],
            },
        )
        chain = next(
            item
            for item in request["reviewer_evidence_pack"]["coverage_mapping"]
            if item["case_key"] == changed.case_key
        )
        response = _v2_review_for_request(
            graph,
            request,
            findings=(
                {
                    "severity": "error",
                    "finding_type": "cleanup-missing",
                    "binding_role": "primary",
                    "falsification_probe": "",
                    **chain,
                    "message": "Changed case still omits cleanup verification.",
                },
            ),
        )

        accepted, decision = validate_reviewer_response(
            response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )

        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

    def test_revision_reviewer_invalid_falsification_binding_still_fails(self) -> None:
        graph = _multi_runtime_graph()
        plan = build_test_design_plan(graph, context=_context())
        cases = tuple(sorted(plan.deterministic_cases, key=lambda item: item.case_key))
        markdown = render_test_cases(cases, scope_title=_context().scope_title)
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        changed = cases[0]
        unchanged = cases[1]
        request = _v2_multi_case_request(
            graph,
            cases,
            gate,
            markdown,
            revision_review_scope={
                "schema_version": 1,
                "changed_case_keys": [changed.case_key],
                "unchanged_byte_identical_cases": [
                    {
                        "case_key": unchanged.case_key,
                        "tc_id": unchanged.tc_id,
                        "block_sha256": "a" * 64,
                    }
                ],
            },
        )
        response = _v2_review_for_request(graph, request)
        response["case_results"][1]["falsification"]["false_pass"][
            "oracle"
        ] = "Paraphrased expected result that is not exact evidence text."

        with self.assertRaisesRegex(
            IterationContractError,
            "falsification basis.*is not bound",
        ):
            validate_reviewer_response(
                response,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )

    def test_normal_full_reviewer_mode_does_not_defer_unchanged_finding(self) -> None:
        graph = _multi_runtime_graph()
        plan = build_test_design_plan(graph, context=_context())
        cases = tuple(sorted(plan.deterministic_cases, key=lambda item: item.case_key))
        markdown = render_test_cases(cases, scope_title=_context().scope_title)
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        request = _v2_multi_case_request(graph, cases, gate, markdown)
        case = cases[1]
        chain = next(
            item
            for item in request["reviewer_evidence_pack"]["coverage_mapping"]
            if item["case_key"] == case.case_key
        )
        response = _v2_review_for_request(
            graph,
            request,
            findings=(
                {
                    "severity": "error",
                    "finding_type": "expected-result-unsupported",
                    "binding_role": "primary",
                    "falsification_probe": "",
                    **chain,
                    "message": "Full reviewer mode must keep this blocking.",
                },
            ),
        )

        accepted, decision = validate_reviewer_response(
            response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )

        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)
        self.assertEqual((), reviewer_deferred_test_case_findings(response, request))

    def test_reviewer_v2_prompt_requires_symmetric_falsification(self) -> None:
        prompt = reviewer_prompt_instruction(2)

        for token in (
            "defective implementation under source-consistent inputs and preconditions",
            "conforming to all supplied evidence",
            "invalid fixture or unrelated precondition",
            "exact source-backed trigger",
            "case_results.falsification",
            "exact binding_role, obligation_id",
            "binding_item_index (-1 for primary)",
            "bind trigger_or_step to an actual TC step",
            "Copy trigger_or_step and oracle exactly",
            "additional findings for the same probe",
            "same root defect affects multiple probes",
            "source-only validation trigger",
            "outcome=not-recorded",
            "Direct source, TC-design, digest, and binding defects",
            "do not manufacture a finding",
            "no test_case_finding is required for passed",
            "Never use outcome=finding to express contract uncertainty",
            "Do not return decision=blocked merely because a no-defect probe",
        ):
            self.assertIn(token, prompt)

        legacy_acceptance = reviewer_acceptance_contract(schema_version=1)
        self.assertNotIn("reviewer_policy_version", legacy_acceptance)
        self.assertNotIn("adversarial_false_pass_check", legacy_acceptance)

    def test_reviewer_v2_requires_complete_docx_and_nonregistered_pdf_rows(
        self,
    ) -> None:
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
        base = _v2_pack(graph, cases, gate, markdown)

        broken_packs = []
        missing_auxiliary = copy.deepcopy(base)
        missing_auxiliary["source_structure"]["docx_xhtml_pdf_parity"][
            "docx_xhtml"
        ]["auxiliary_row_matches"] = []
        broken_packs.append(missing_auxiliary)

        wrong_candidate_row = copy.deepcopy(base)
        wrong_candidate_row["source_structure"]["docx_xhtml_pdf_parity"][
            "docx_xhtml"
        ]["row_matches"][0]["source_row_id"] = "SRC-CONTEXT"
        broken_packs.append(wrong_candidate_row)

        wrong_total_count = copy.deepcopy(base)
        wrong_total_count["source_structure"]["docx_xhtml_pdf_parity"][
            "docx_xhtml"
        ]["matched_literal_xhtml_row_count"] = 1
        broken_packs.append(wrong_total_count)

        missing_semantic_status = copy.deepcopy(base)
        missing_semantic_status["source_structure"]["docx_xhtml_pdf_parity"][
            "pdf_requirement_codes"
        ] = {"status": "not-registered"}
        broken_packs.append(missing_semantic_status)

        forged_literal = copy.deepcopy(base)
        forged_row = forged_literal["literal_source_evidence"][0]
        forged_row["bounded_source_text"] = "FORGED"
        forged_row["bounded_source_text_sha256"] = hashlib.sha256(
            b"FORGED"
        ).hexdigest()
        forged_row["source_file_sha256"] = "f" * 64
        forged_literal["source_structure"]["selected_xhtml"]["sha256"] = (
            "f" * 64
        )
        broken_packs.append(forged_literal)

        for pack in broken_packs:
            with self.subTest(pack=pack):
                with self.assertRaisesRegex(
                    IterationContractError,
                    "complete bounded DOCX/XHTML/PDF parity proof",
                ):
                    build_reviewer_request(
                        graph=graph,
                        cases=cases,
                        gate=gate,
                        evidence_pack=pack,
                    )

    def test_reviewer_v2_registered_pdf_requires_every_literal_row(self) -> None:
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
        pack = _v2_pack(graph, cases, gate, markdown)
        pack["source_structure"]["scope_definition"]["source_set"]["pdf"] = {
            "path": "source/main.pdf"
        }
        semantic_rows = {
            "status": "verified",
            "literal_xhtml_row_count": 2,
            "matched_literal_xhtml_row_count": 2,
            "row_matches": [
                {"source_row_id": graph.properties[0].source_row_id},
                {"source_row_id": "SRC-CONTEXT"},
            ],
        }
        pack["source_structure"]["docx_xhtml_pdf_parity"][
            "pdf_requirement_codes"
        ] = {
            "status": "verified",
            "semantic_literal_rows": semantic_rows,
        }

        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=pack,
        )
        self.assertEqual(2, request["schema_version"])

        broken = copy.deepcopy(pack)
        broken_semantic = broken["source_structure"]["docx_xhtml_pdf_parity"][
            "pdf_requirement_codes"
        ]["semantic_literal_rows"]
        broken_semantic["row_matches"][1]["source_row_id"] = (
            graph.properties[0].source_row_id
        )
        with self.assertRaisesRegex(
            IterationContractError,
            "complete bounded DOCX/XHTML/PDF parity proof",
        ):
            build_reviewer_request(
                graph=graph,
                cases=cases,
                gate=gate,
                evidence_pack=broken,
            )

    def test_reviewer_v2_parity_excludes_registered_non_xhtml_support_rows(self) -> None:
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
        pack = _v2_pack(graph, cases, gate, markdown)
        pack["literal_source_evidence"].append(
            {
                "source_row_id": "SRC-SUPPORT-PDF",
                "candidate_id": None,
                "source_path": "support/context.pdf",
                "bounded_source_text": "Подтверждённый supporting context.",
            }
        )

        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=pack,
        )

        self.assertEqual(
            3,
            len(request["reviewer_evidence_pack"]["literal_source_evidence"]),
        )

    def test_reviewer_v2_can_reject_projection_for_row_without_obligation(self) -> None:
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
        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=_v2_pack(graph, cases, gate, markdown),
        )
        response = _accepted_review_v2(graph, request)
        response["decision"] = "changes-required"
        response["source_projection_findings"] = [
            {
                "severity": "error",
                "finding_type": "source-element-omitted",
                "source_row_id": "SRC-CONTEXT",
                "assertion_id": "",
                "property_id": "",
                "obligation_id": "",
                "case_key": "",
                "tc_id": "",
                "message": "Строка не получила нормализованной проекции.",
            }
        ]

        accepted, decision = validate_reviewer_response(
            response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

    def test_reviewer_v2_source_finding_can_bind_registered_supporting_edge(self) -> None:
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
        pack = _v2_pack(graph, cases, gate, markdown)
        primary = pack["coverage_mapping"][0]
        pack["supporting_evidence_mapping"] = [
            {
                **primary,
                "source_row_id": "SRC-CONTEXT",
                "source_path": "source/requirements.xhtml",
                "source_locator": "/*/*[1]",
                "evidence_role": "condition",
                "exact_source_fragment": "Заголовок таблицы.",
                "exact_source_fragment_sha256": "0" * 64,
                "primary_source_row_id": primary["source_row_id"],
            }
        ]
        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=pack,
        )
        response = _accepted_review_v2(graph, request)
        response["decision"] = "changes-required"
        response["source_projection_findings"] = [
            {
                "severity": "error",
                "finding_type": "literal-condition-lost",
                "source_row_id": "SRC-CONTEXT",
                "assertion_id": primary["assertion_id"],
                "property_id": primary["property_id"],
                "obligation_id": primary["obligation_id"],
                "case_key": primary["case_key"],
                "tc_id": primary["tc_id"],
                "message": "Supporting condition was lost in the projection.",
            }
        ]

        accepted, decision = validate_reviewer_response(
            response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )

        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

    def test_reviewer_schema_dedupes_obligation_enum_for_split_cases(self) -> None:
        schema = reviewer_response_schema(
            (
                ("case-a", "TC-A", "OBL-SHARED"),
                ("case-b", "TC-B", "OBL-SHARED"),
            ),
            graph_digest="a" * 64,
            draft_sha256="b" * 64,
        )

        validate_openai_strict_output_schema(schema)
        obligation_enum = schema["properties"]["case_results"]["items"][
            "properties"
        ]["obligation_id"]["enum"]
        self.assertEqual(["OBL-SHARED"], obligation_enum)

    def test_reviewer_v2_schema_requires_one_case_result_per_case(self) -> None:
        graph = _graph()
        graph = replace(
            graph,
            obligations=(
                graph.obligations[0],
                replace(
                    graph.obligations[0],
                    obligation_id="OBL-002",
                    atom_id="ATOM-002",
                    observable_oracle="В поле «Имя» отображается второе значение.",
                ),
            ),
            cases=(
                graph.cases[0],
                CoverageCase(
                    case_key="customer|customer-name|positive-input|second|always",
                    tc_id="TC-CUST-SECOND01",
                    obligation_ids=("OBL-002",),
                    status="executable",
                ),
            ),
        )
        plan = build_test_design_plan(graph, context=_context())
        cases = plan.deterministic_cases
        markdown = render_test_cases(cases, scope_title="Данные клиента")
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        pack = _v2_pack(graph, cases, gate, markdown)
        prop = graph.properties[0]
        obligations = {item.obligation_id: item for item in graph.obligations}
        pack["coverage_mapping"] = [
            {
                "source_row_id": prop.source_row_id,
                "assertion_id": prop.assertion_id,
                "property_id": prop.property_id,
                "obligation_id": obligations[case.obligation_ids[0]].obligation_id,
                "case_key": case.case_key,
                "tc_id": case.tc_id,
            }
            for case in graph.cases
        ]
        pack["coverage_mapping"].append(
            {
                "source_row_id": "SRC-CONTEXT",
                "assertion_id": "",
                "property_id": "",
                "obligation_id": "",
                "case_key": "",
                "tc_id": "",
            }
        )
        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=pack,
        )
        schema = reviewer_response_schema(
            [
                (
                    case.case_key,
                    case.tc_id,
                    case.obligation_ids[0],
                    case.status,
                )
                for case in graph.cases
            ],
            graph_digest=graph.digest,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )

        case_results_schema = schema["properties"]["case_results"]
        self.assertEqual(2, case_results_schema["minItems"])
        self.assertEqual(2, case_results_schema["maxItems"])

        incomplete_response = _accepted_review_v2(graph, request)
        incomplete_response["decision"] = "changes-required"
        incomplete_response["summary"] = "Only a changed case was returned."
        with self.assertRaisesRegex(ValueError, "fewer than minItems=2"):
            validate_openai_strict_output_instance(incomplete_response, schema)

    def test_reviewer_v2_test_finding_can_bind_repeater_design_support_role(self) -> None:
        from tests.test_test_design import _repeater_graph_and_context

        graph, context = _repeater_graph_and_context()
        cases = build_test_design_plan(graph, context=context).deterministic_cases
        markdown = render_test_cases(cases, scope_title="Данные клиента")
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        self.assertTrue(gate.passed, gate.to_dict())
        pack = _v2_pack(graph, cases, gate, markdown)
        source_rows = sorted({item.source_row_id for item in graph.properties})
        pack["literal_source_evidence"] = [
            {
                "source_row_id": source_row_id,
                "candidate_id": f"SRC-CAND-{index:024d}",
                "source_path": "source/main.xhtml",
                "source_file_sha256": "1" * 64,
                "source_locator": f"/*/*[{index}]",
                "row_identity": f"/*/*[{index}]",
                "element_kind": "p",
                "table_identity": None,
                "table_ancestry": [],
                "section_path": [],
                "section_heading_evidence": [],
                "bounded_source_text": f"Source row {source_row_id}.",
            }
            for index, source_row_id in enumerate(source_rows, start=1)
        ]
        for item in pack["literal_source_evidence"]:
            item["bounded_source_text_sha256"] = hashlib.sha256(
                item["bounded_source_text"].encode("utf-8")
            ).hexdigest()
        pack["source_structure"]["docx_xhtml_pdf_parity"]["docx_xhtml"] = {
            "status": "verified",
            "literal_candidate_count": len(source_rows),
            "matched_literal_candidate_count": len(source_rows),
            "literal_xhtml_row_count": len(source_rows),
            "matched_literal_xhtml_row_count": len(source_rows),
            "unique_docx_unit_count": len(source_rows),
            "row_matches": [
                {
                    "candidate_id": item["candidate_id"],
                    "source_row_id": item["source_row_id"],
                    "source_path": item["source_path"],
                    "source_file_sha256": item["source_file_sha256"],
                    "source_locator": item["source_locator"],
                    "bounded_source_text_sha256": item[
                        "bounded_source_text_sha256"
                    ],
                    "element_kind": item["element_kind"],
                    "docx_matches": [
                        {
                            "unit_kind": "paragraph",
                            "paragraph_index": index,
                            "document_order": index * 1000,
                        }
                    ],
                }
                for index, item in enumerate(
                    pack["literal_source_evidence"],
                    start=1,
                )
            ],
            "auxiliary_row_matches": [],
            "table_identity_matches": [],
            "section_heading_match_count": 0,
            "section_heading_matches": [],
        }
        pack["source_structure"]["docx_xhtml_pdf_parity"][
            "pdf_requirement_codes"
        ] = {
            "status": "not-registered",
            "semantic_literal_rows": {
                "status": "not-registered",
                "literal_xhtml_row_count": len(source_rows),
            },
        }
        properties = {item.property_id: item for item in graph.properties}
        obligations = {item.obligation_id: item for item in graph.obligations}
        pack["coverage_mapping"] = []
        for case in graph.cases:
            obligation = obligations[case.obligation_ids[0]]
            prop = properties[obligation.property_id]
            pack["coverage_mapping"].append(
                {
                    "source_row_id": prop.source_row_id,
                    "assertion_id": prop.assertion_id,
                    "property_id": prop.property_id,
                    "obligation_id": obligation.obligation_id,
                    "case_key": case.case_key,
                    "tc_id": case.tc_id,
                }
            )
        pack["design_support_mapping"] = build_design_support_mapping(graph, cases)

        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=pack,
        )
        bindings = [
            (case.case_key, case.tc_id, case.obligation_ids[0], case.status)
            for case in graph.cases
        ]
        schema = reviewer_response_schema(
            bindings,
            graph_digest=graph.digest,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        binding_roles = schema["properties"]["test_case_findings"]["items"][
            "properties"
        ]["binding_role"]["enum"]
        self.assertIn("design-support-setup", binding_roles)
        support = next(
            item
            for item in pack["design_support_mapping"]
            if item["support_role"] == "setup"
        )
        designs_by_case = {
            item["case_key"]: item for item in pack["test_cases"]["designs"]
        }
        response = {
            "schema_version": 2,
            "graph_digest": graph.digest,
            "draft_sha256": gate.draft_sha256,
            "evidence_pack_sha256": request["evidence_pack_sha256"],
            "decision": "changes-required",
            "case_results": [
                {
                    "case_key": case.case_key,
                    "tc_id": case.tc_id,
                    "obligation_id": case.obligation_ids[0],
                    "status": "covered",
                    "comment": "Проверено.",
                    "falsification": _passed_falsification(
                        obligation_id=case.obligation_ids[0],
                        trigger_or_step=designs_by_case[case.case_key]["steps"][-1],
                        oracle=designs_by_case[case.case_key]["expected_result"],
                    ),
                }
                for case in graph.cases
            ],
            "source_projection_findings": [],
            "test_case_findings": [
                {
                    "severity": "error",
                    "finding_type": "repeater-lifecycle-incomplete",
                    "binding_role": f"design-support-{support['support_role']}",
                    "falsification_probe": "",
                    **{
                        name: support[name]
                        for name in (
                            "source_row_id",
                            "assertion_id",
                            "property_id",
                            "obligation_id",
                            "case_key",
                            "tc_id",
                        )
                    },
                    "message": "Setup action does not establish the required rows.",
                }
            ],
            "summary": "Требуется исправление lifecycle.",
        }

        accepted, decision = validate_reviewer_response(
            response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

        probe_response = copy.deepcopy(response)
        support_obligation = obligations[support["obligation_id"]]
        support_case_result = next(
            item
            for item in probe_response["case_results"]
            if item["case_key"] == support["case_key"]
        )
        support_probe = support_case_result["falsification"]["failure_attribution"]
        support_probe.update(
            {
                "outcome": "finding",
                "binding_role": f"design-support-{support['support_role']}",
                "obligation_id": support["obligation_id"],
                "binding_item_index": support["item_index"],
                "trigger_or_step": support_obligation.validation_trigger,
                "oracle": support_obligation.observable_oracle,
                "detail": (
                    "The setup fixture can hide a failure in the selected supporting "
                    "obligation."
                ),
            }
        )
        probe_response["test_case_findings"][0][
            "falsification_probe"
        ] = "failure_attribution"
        accepted, decision = validate_reviewer_response(
            probe_response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

        same_case_root_finding = copy.deepcopy(probe_response)
        root_case_result = next(
            item
            for item in same_case_root_finding["case_results"]
            if item["case_key"] == support["case_key"]
        )
        root_case_result["falsification"]["false_pass"].update(
            {
                "outcome": "finding",
                "binding_role": "primary",
                "obligation_id": root_case_result["obligation_id"],
                "binding_item_index": -1,
                "trigger_or_step": designs_by_case[support["case_key"]]["steps"][-1],
                "oracle": designs_by_case[support["case_key"]]["expected_result"],
                "detail": (
                    "The same setup-root defect also creates a false-pass risk "
                    "on the primary chain."
                ),
            }
        )
        accepted, decision = validate_reviewer_response(
            same_case_root_finding,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)

        support_items = pack["design_support_mapping"]
        anchor_support, extra_support = next(
            (left, right)
            for left in support_items
            for right in support_items
            if left["case_key"] == right["case_key"]
            and (
                left["support_role"],
                left["obligation_id"],
                left["item_index"],
            )
            != (
                right["support_role"],
                right["obligation_id"],
                right["item_index"],
            )
        )
        multi_chain_response = copy.deepcopy(response)
        multi_case_result = next(
            item
            for item in multi_chain_response["case_results"]
            if item["case_key"] == anchor_support["case_key"]
        )
        anchor_obligation = obligations[anchor_support["obligation_id"]]
        multi_case_result["falsification"]["trigger_fidelity"].update(
            {
                "outcome": "finding",
                "binding_role": (
                    f"design-support-{anchor_support['support_role']}"
                ),
                "obligation_id": anchor_support["obligation_id"],
                "binding_item_index": anchor_support["item_index"],
                "trigger_or_step": anchor_support["materialized_text"],
                "oracle": anchor_obligation.observable_oracle,
                "detail": "Two registered support chains contain trigger defects.",
            }
        )
        multi_chain_response["test_case_findings"] = [
            {
                "severity": "error",
                "finding_type": "trigger-missing",
                "binding_role": f"design-support-{item['support_role']}",
                "falsification_probe": "trigger_fidelity",
                **{
                    name: item[name]
                    for name in (
                        "source_row_id",
                        "assertion_id",
                        "property_id",
                        "obligation_id",
                        "case_key",
                        "tc_id",
                    )
                },
                "message": f"Trigger defect in {item['support_role']} support.",
            }
            for item in (anchor_support, extra_support)
        ]
        accepted, decision = validate_reviewer_response(
            multi_chain_response,
            graph=graph,
            draft_sha256=gate.draft_sha256,
            reviewer_request=request,
        )
        self.assertFalse(accepted)
        self.assertEqual("changes-required", decision)
        self.assertNotEqual(
            anchor_support["materialized_text"],
            extra_support["materialized_text"],
        )
        cross_bound_basis = copy.deepcopy(multi_chain_response)
        cross_case_result = next(
            item
            for item in cross_bound_basis["case_results"]
            if item["case_key"] == anchor_support["case_key"]
        )
        cross_case_result["falsification"]["trigger_fidelity"][
            "trigger_or_step"
        ] = extra_support["materialized_text"]
        with self.assertRaisesRegex(
            IterationContractError,
            "is not bound to the reviewed case and obligation",
        ):
            validate_reviewer_response(
                cross_bound_basis,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )

        response["test_case_findings"][0]["binding_role"] = "primary"
        with self.assertRaisesRegex(IterationContractError, "evidence binding mismatch"):
            validate_reviewer_response(
                response,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=request,
            )

    def test_passed_probe_cannot_use_source_only_trigger_as_tc_basis(self) -> None:
        graph = _graph(trigger="Commit action")
        plan = build_test_design_plan(graph, context=_context())
        cases = plan.deterministic_cases
        markdown = render_test_cases(cases, scope_title="Данные клиента")
        gate = validate_suite(
            graph=graph,
            cases=cases,
            markdown=markdown,
            checked_path="shadow.md",
        )
        request = build_reviewer_request(
            graph=graph,
            cases=cases,
            gate=gate,
            evidence_pack=_v2_pack(graph, cases, gate, markdown),
        )
        source_trigger = graph.obligations[0].validation_trigger
        design_steps = request["reviewer_evidence_pack"]["test_cases"]["designs"][
            0
        ]["steps"]
        self.assertNotIn(source_trigger, design_steps)

        for probe in ("false_pass", "trigger_fidelity"):
            with self.subTest(probe=probe):
                response = _accepted_review_v2(graph, request)
                response["case_results"][0]["falsification"][probe][
                    "trigger_or_step"
                ] = source_trigger
                with self.assertRaisesRegex(
                    IterationContractError,
                    "is not bound to the reviewed case and obligation",
                ):
                    validate_reviewer_response(
                        response,
                        graph=graph,
                        draft_sha256=gate.draft_sha256,
                        reviewer_request=request,
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
