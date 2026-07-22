from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.openai_strict_output_schema import (
    OpenAIStrictOutputInstanceError,
    validate_openai_strict_output_instance,
)
from test_case_agent.bounded_scope_materializer import (
    materialize_semantic_design_bridge,
)
from test_case_agent.semantic_design_bridge import (
    APPLICABILITY_DIMENSIONS,
    SEMANTIC_DESIGN_CONTRACT,
    SEMANTIC_DESIGN_VERSION,
    SemanticDesignBridgeError,
    canonical_payload_sha256,
    load_approved_clarifications,
    normalize_semantic_design_source_property_transport,
    normalize_semantic_design_transport,
    semantic_design_completeness_diagnostics,
    semantic_design_minimum_obligation_count,
    semantic_design_transport_diagnostics,
    prepared_context_sha256,
    semantic_design_allows_canonical_transport_binding,
    semantic_design_prompt,
    semantic_design_output_schema,
    _validate_always_visibility_prestate_cardinality,
    _required_necessary_condition_negative_controls,
    _readd_lifecycle_setup_projections,
    _validate_necessary_condition_control_cardinality,
    _unsupported_executable_requiredness_candidate_projections,
    _validate_distinct_action_oracle_clauses,
    _necessary_control_missing_clause_evidence_projections,
    _clarification_condition_action_evidence_projections,
    _executable_negative_signal_evidence_projections,
    _collapsed_candidate_negative_oracle_projection,
    _collapsed_executable_negative_oracle_projection,
    _combined_calibration_allowed_class_projection,
    _canonicalize_declared_ui_calibration,
    _canonicalize_requiredness_calibration_candidate,
    _future_issue_date_save_block_projection,
    _inclusive_twentieth_birthday_projection,
    _load_verified_fixture_contracts,
    _materialize_distinct_editability_replacements,
    _materialize_concrete_reset_fixtures,
    _materialize_bare_requirement_definition_gaps,
    _materialize_missing_definition_gap_assertions,
    _materialize_range_ambiguity_gap_assertions,
    _remove_range_ambiguity_calibration_candidates,
    _materialize_missing_exact_length_boundaries,
    _materialize_service_availability_necessary_controls,
    _normalize_exact_length_acceptance_oracles,
    _normalize_inclusive_lower_bound_transport,
    _normalize_negative_candidate_known_violation,
    _normalize_unbacked_numeric_entry_persistence,
    _remove_behavior_codes_from_typed_editability,
    _reassign_dictionary_completeness_ownership,
    _restore_visibility_after_dictionary_ownership,
    _separate_explicit_range_rejection_branches,
    _clarification_exclusion_oracle_projections,
    _semantic_transport_header_projection,
    _dependency_transport_projections,
    _missing_scope_excluded_dependency_projection,
    _scope_excluded_na_link_projection,
    _source_signal_registry,
    _split_candidate_signal_from_incompatible_positive_chain,
    _split_visibility_code_from_typed_requiredness,
    _verified_party_fixture_clause_projection,
    _verified_fixture_clause_projection,
    validate_bridge_boundary,
    validate_semantic_input_preflight,
    validate_semantic_design_binding,
)
from test_case_agent.semantic_design_sharding import (
    SemanticDesignShardingError,
    materialize_non_testable_semantic_shard,
)


OWNER_TOKEN = "11111111-1111-4111-8111-111111111111"


class SemanticDesignBridgeTests(unittest.TestCase):
    def test_typed_editability_does_not_own_sibling_behavior_codes(self) -> None:
        payload = {
            "obligations": [
                {
                    "obligation_id": "OBL-EDIT",
                    "property_type": "editability",
                    "input_class": "value-replacement",
                },
                {
                    "obligation_id": "OBL-FORMAT",
                    "property_type": "phone-format",
                },
            ],
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-EDIT",
                            "semantic_disposition": "testable",
                            "obligation_ids": ["OBL-EDIT"],
                            "requirement_codes": ["BSR 1", "BSR 2"],
                            "requirement_code_evidence": [
                                {"requirement_code": "BSR 1"},
                                {"requirement_code": "BSR 2"},
                            ],
                        },
                        {
                            "assertion_id": "ASSERT-FORMAT",
                            "semantic_disposition": "testable",
                            "obligation_ids": ["OBL-FORMAT"],
                            "requirement_codes": ["BSR 1", "BSR 2"],
                        },
                    ],
                }
            ],
        }

        repairs = _remove_behavior_codes_from_typed_editability(payload)

        editability = payload["source_designs"][0]["assertions"][0]
        self.assertEqual([], editability["requirement_codes"])
        self.assertEqual([], editability["requirement_code_evidence"])
        self.assertEqual(
            ["remove-behavior-codes-from-typed-editability"],
            [item["rule"] for item in repairs],
        )

    def test_visibility_chain_is_restored_after_dictionary_duplication(self) -> None:
        row_text = (
            "Тип должности Да Да Раскрывающийся список "
            "Значение из справочника «Типы должности» "
            "BSR 274. Видимость: Да, если поле «Тип занятости» заполнено "
            "и значение ≠ «Пенсионер (не работает)», «Самозанятый»"
        )
        payload = {
            "obligations": [
                {
                    "obligation_id": "OBL-DICT",
                    "property_type": "editability",
                    "dictionary_coverage": "all-leaf-values",
                },
                {
                    "obligation_id": "OBL-VIS",
                    "property_type": "visibility",
                    "obligation_class": "dictionary-completeness",
                    "dictionary_coverage": "all-leaf-values",
                },
            ],
            "source_designs": [
                {
                    "source_row_id": "SRC-025",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-DICT",
                            "obligation_ids": ["OBL-DICT"],
                            "semantic_disposition": "testable",
                            "requirement_codes": [],
                        },
                        {
                            "assertion_id": "ASSERT-VIS",
                            "field_or_block": "Тип должности",
                            "obligation_ids": ["OBL-VIS"],
                            "semantic_disposition": "testable",
                            "requirement_codes": ["BSR 274"],
                            "canonical_statement": "Повтор полного справочника.",
                        },
                    ],
                }
            ],
        }
        context = {
            "dictionary_inventory": [
                {
                    "name": "Социальный статус",
                    "active_values": [
                        "работа по найму",
                        "пенсионер (не работает)",
                        "самозанятый",
                    ],
                }
            ],
            "source_rows": [
                {
                    "source_row_id": "SRC-020",
                    "bounded_source_text": (
                        "Социальный статус: работа по найму; "
                        "пенсионер (не работает); самозанятый"
                    ),
                },
                {
                    "source_row_id": "SRC-025",
                    "bounded_source_text": row_text,
                },
            ],
        }

        repairs = _restore_visibility_after_dictionary_ownership(payload, context)

        assertion = payload["source_designs"][0]["assertions"][1]
        obligation = payload["obligations"][1]
        self.assertEqual(
            ["Выбрать в поле «Социальный статус» значение «работа по найму»."],
            assertion["action_clauses"],
        )
        self.assertEqual(["Поле «Тип должности» отображается."], assertion["oracle_clauses"])
        self.assertEqual("none_required", obligation["dictionary_coverage"])
        self.assertEqual(
            ["restore-visibility-after-dictionary-ownership"],
            [item["rule"] for item in repairs],
        )

    def test_explicit_lower_and_upper_range_rejections_are_separate(self) -> None:
        row_text = (
            "Доход. Значения по умолчанию X = 2000, Y = 1 000 000 "
            "BSR 282. При попытке ввести сумму менее X при потере фокуса "
            "поле должно окрашиваться красным цветом и должна появляться "
            "подсказка «Введите сумму более X руб.» "
            "BSR 283. При попытке ввести сумму более Y при потере фокуса "
            "поле должно окрашиваться красным цветом и должна появляться "
            "подсказка «Перепроверьте доход»"
        )
        evidence = lambda code: {  # noqa: E731 - compact immutable fixture.
            "requirement_code": code,
            "source_row_id": "SRC-029",
        }
        payload = {
            "obligations": [
                {
                    "obligation_id": "OBL-UPPER",
                    "property_type": "range-validation",
                    "planned_tc_id": "TC-UPPER",
                },
                {
                    "obligation_id": "OBL-LOWER",
                    "property_type": "source-constraint-negative",
                    "planned_tc_id": "TC-LOWER",
                },
            ],
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-UPPER",
                            "field_or_block": "Доход",
                            "polarity": "negative",
                            "obligation_ids": ["OBL-UPPER"],
                            "requirement_codes": ["BSR 282", "BSR 283"],
                            "requirement_code_evidence": [
                                evidence("BSR 282"),
                                evidence("BSR 283"),
                            ],
                            "action_clauses": [
                                "Ввести «1999», затем отдельно «1000001»."
                            ],
                        },
                        {
                            "assertion_id": "ASSERT-LOWER",
                            "field_or_block": "Доход",
                            "polarity": "negative",
                            "obligation_ids": ["OBL-LOWER"],
                            "requirement_codes": ["BSR 281"],
                            "requirement_code_evidence": [evidence("BSR 281")],
                            "action_clauses": ["Ввести значение «1999»."],
                        },
                    ],
                }
            ],
            "negative_oracles": [
                {
                    "linked_obligation_id": "OBL-LOWER",
                    "requirement_codes": ["BSR 281"],
                },
                {
                    "linked_obligation_id": "OBL-UPPER",
                    "requirement_codes": ["BSR 283"],
                },
            ],
        }
        context = {
            "source_rows": [
                {"source_row_id": "SRC-029", "bounded_source_text": row_text}
            ]
        }

        repairs = _separate_explicit_range_rejection_branches(payload, context)

        upper, lower = payload["source_designs"][0]["assertions"]
        self.assertEqual(["BSR 283"], upper["requirement_codes"])
        self.assertIn("1000001", upper["action_clauses"][0])
        self.assertNotIn("1999", upper["action_clauses"][0])
        self.assertEqual(["BSR 281", "BSR 282"], lower["requirement_codes"])
        self.assertIn("Введите сумму более X руб.", lower["oracle_clauses"][0])
        self.assertEqual("executable_tc", payload["negative_oracles"][0]["decision"])
        self.assertEqual(
            ["separate-explicit-range-rejection-branches"],
            [item["rule"] for item in repairs],
        )

    def test_reset_lifecycle_reuses_exact_positive_scope_fixtures(self) -> None:
        payload = {
            "source_designs": [
                {
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-STATUS",
                            "field_or_block": "Социальный статус",
                            "polarity": "positive",
                            "action_clauses": ["Выбрать значение."],
                            "obligation_ids": ["OBL-STATUS"],
                        },
                        {
                            "assertion_id": "ASSERT-ORG",
                            "field_or_block": "ОПФ",
                            "polarity": "positive",
                            "action_clauses": [
                                "В поле «Наименование организации, ИНН» выбрать предложение."
                            ],
                            "obligation_ids": ["OBL-ORG"],
                        },
                        {
                            "assertion_id": "ASSERT-RESET",
                            "field_or_block": "Кнопка «Корзина» и поля",
                            "polarity": "positive",
                            "action_clauses": ["Нажать кнопку «Корзина»."],
                            "obligation_ids": ["OBL-RESET"],
                        },
                        {
                            "assertion_id": "ASSERT-TITLE-VISIBILITY",
                            "field_or_block": "Должность",
                            "polarity": "positive",
                            "action_clauses": ["Выбрать социальный статус."],
                            "obligation_ids": ["OBL-TITLE-VISIBILITY"],
                        },
                        {
                            "assertion_id": "ASSERT-TITLE",
                            "field_or_block": "Должность",
                            "polarity": "positive",
                            "action_clauses": ["Ввести должность."],
                            "obligation_ids": ["OBL-TITLE"],
                        },
                        {
                            "assertion_id": "ASSERT-READD",
                            "field_or_block": "Жизненный цикл блока",
                            "polarity": "positive",
                            "action_clauses": ["Удалить блок, затем добавить новый."],
                            "obligation_ids": ["OBL-READD"],
                        },
                    ]
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-STATUS",
                    "property_type": "editability",
                    "obligation_class": "typed-property",
                    "coverage_class": "typed-property",
                    "check_type": "positive",
                    "input_class": "dictionary-value",
                    "test_data": "работа по найму",
                },
                {
                    "obligation_id": "OBL-ORG",
                    "property_type": "integration",
                    "obligation_class": "integration",
                    "coverage_class": "requirements",
                    "check_type": "action-flow",
                    "input_class": "registered-fixture",
                    "test_data": (
                        "FX-DADATA-PARTY-ACTIVE-001; query=7707083893; "
                        "exact_suggestion=ПАО СБЕРБАНК; opf.short=ПАО; "
                        "address.value=г Москва, ул Вавилова, д 19; "
                        "state.status=ACTIVE"
                    ),
                },
                {
                    "obligation_id": "OBL-TITLE-VISIBILITY",
                    "property_type": "visibility",
                    "obligation_class": "conditional-visibility",
                    "coverage_class": "requirement",
                    "design_dimension": "conditional-visibility",
                    "check_type": "positive",
                    "input_class": "social-status",
                    "test_data": "работа по найму",
                },
                {
                    "obligation_id": "OBL-TITLE",
                    "property_type": "editability",
                    "obligation_class": "typed-property",
                    "coverage_class": "typed-property",
                    "design_dimension": "accessibility-ui",
                    "check_type": "positive",
                    "input_class": "text",
                    "test_data": "Инженер",
                },
                {
                    "obligation_id": "OBL-RESET",
                    "property_type": "clear-current-subblock",
                    "obligation_class": "reset",
                    "coverage_class": "state-change",
                    "test_data": "Набор допустимых непустых значений.",
                },
                {
                    "obligation_id": "OBL-READD",
                    "property_type": "repeatable-block-lifecycle",
                    "obligation_class": "readd-after-delete",
                    "coverage_class": "status-lifecycle",
                    "test_data": "Заполненный исходный блок",
                },
            ],
            "reset_lifecycle_bindings": [
                {
                    "obligation_id": "OBL-RESET",
                    "binding_kind": "reset",
                    "changed_state_setup": "Заполнить поля допустимыми значениями.",
                },
                {
                    "obligation_id": "OBL-READD",
                    "binding_kind": "readd-after-delete",
                    "changed_state_setup": "Удалить блок, затем добавить новый блок.",
                },
            ],
        }

        publication_input = copy.deepcopy(payload)
        repairs = _materialize_concrete_reset_fixtures(payload)

        obligations_by_id = {
            item["obligation_id"]: item for item in payload["obligations"]
        }
        reset_data = obligations_by_id["OBL-RESET"]["test_data"]
        readd_data = obligations_by_id["OBL-READD"]["test_data"]
        self.assertEqual(reset_data, readd_data)
        self.assertIn("Социальный статус=работа по найму", reset_data)
        self.assertIn(
            "Наименование организации, ИНН=Fixture DaData: "
            "FX-DADATA-PARTY-ACTIVE-001; Запрос: 7707083893; "
            "Точное предложение: ПАО СБЕРБАНК",
            reset_data,
        )
        self.assertIn("ОПФ=ПАО", reset_data)
        self.assertIn("Должность=Инженер", reset_data)
        self.assertNotIn("Должность=работа по найму", reset_data)
        self.assertIn(
            "Удалить блок, затем добавить новый блок.",
            payload["reset_lifecycle_bindings"][1]["changed_state_setup"],
        )
        self.assertEqual(4, len(repairs))

        published, receipt = normalize_semantic_design_source_property_transport(
            publication_input
        )
        published_by_id = {
            item["obligation_id"]: item for item in published["obligations"]
        }
        self.assertEqual(
            published_by_id["OBL-RESET"]["test_data"],
            published_by_id["OBL-READD"]["test_data"],
        )
        self.assertIn(
            "Точное предложение: ПАО СБЕРБАНК",
            published_by_id["OBL-RESET"]["test_data"],
        )
        self.assertTrue(
            any(
                item["rule"] == "bind-concrete-reset-filled-state-fixture"
                for item in receipt["repairs"]
            )
        )

    def test_exact_length_acceptance_does_not_claim_raw_rendering(self) -> None:
        payload = {
            "source_designs": [
                {
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-LENGTH",
                            "field_or_block": "Рабочий телефон",
                            "obligation_ids": ["OBL-LENGTH"],
                            "canonical_statement": "Сырое значение отображается.",
                            "oracle_clauses": [
                                "Поле принимает и отображает значение «9991234567»."
                            ],
                        }
                    ]
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-LENGTH",
                    "property_type": "exact-length",
                    "check_type": "positive",
                    "test_data": "9991234567",
                    "required_behavior": "Сырое значение отображается.",
                    "single_expected_behavior": "Сырое значение отображается.",
                }
            ],
        }

        repairs = _normalize_exact_length_acceptance_oracles(payload)

        assertion = payload["source_designs"][0]["assertions"][0]
        self.assertEqual(1, len(repairs))
        self.assertNotIn("отображ", assertion["oracle_clauses"][0].casefold())
        self.assertIn("ограничению длины 10 цифр", assertion["oracle_clauses"][0])

    def test_inclusive_lower_bound_is_separated_from_below_bound_rejection(self) -> None:
        statement = "BSR 281. Сумма не менее X и не более Y р."
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "requirement_codes": ["BSR 281", "BSR 282"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-BELOW",
                            "atom_id": "ATOM-BELOW",
                            "polarity": "negative",
                            "field_or_block": "Доход",
                            "obligation_ids": ["OBL-BELOW"],
                            "requirement_codes": ["BSR 282"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 282",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": "BSR 282. Менее X.",
                                }
                            ],
                            "action_clauses": ["Ввести «1999» и перевести фокус."],
                            "oracle_clauses": ["Отображается точная ошибка."],
                            "supporting_source_bindings": [],
                        },
                        {
                            "assertion_id": "ASSERT-EQUAL",
                            "atom_id": "ATOM-EQUAL",
                            "polarity": "negative",
                            "field_or_block": "Доход",
                            "obligation_ids": ["OBL-EQUAL"],
                            "requirement_codes": ["BSR 281"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 281",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": statement,
                                }
                            ],
                            "action_clauses": ["Ввести «2000»."],
                            "oracle_clauses": ["Требуется калибровка."],
                            "supporting_source_bindings": [],
                        },
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-BELOW",
                    "linked_atom_id": "ATOM-BELOW",
                    "check_type": "boundary",
                    "oracle_source": "BSR 282",
                    "planned_tc_id": "TC-BELOW",
                    "scope_obligation_ids": [],
                },
                {
                    "obligation_id": "OBL-EQUAL",
                    "linked_atom_id": "ATOM-EQUAL",
                    "check_type": "boundary",
                    "oracle_source": "not_found",
                    "planned_tc_id": "TC-EQUAL",
                    "scope_obligation_ids": ["SO-NEG-011"],
                },
            ],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-011",
                    "scope_obligation_id": "SO-NEG-011",
                    "source_row_id": "SRC-029",
                    "requirement_codes": ["BSR 281"],
                    "restriction_type": "lower-bound",
                    "source_statement": statement,
                    "negative_class": "equal-X-disputed",
                    "representative_invalid_value": "2000",
                    "decision": "candidate_tc_required",
                    "linked_atom_id": "ATOM-EQUAL",
                    "linked_obligation_id": "OBL-EQUAL",
                }
            ],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-029",
                    "bounded_source_text": statement + " X = 2000, Y = 1000000.",
                }
            ]
        }

        repairs = _normalize_inclusive_lower_bound_transport(payload, context)

        below, equal = payload["source_designs"][0]["assertions"]
        oracle = payload["negative_oracles"][0]
        self.assertEqual(1, len(repairs))
        self.assertEqual("positive", equal["polarity"])
        self.assertIn("включённой нижней границе", equal["oracle_clauses"][0])
        self.assertEqual(["BSR 281", "BSR 282"], below["requirement_codes"])
        self.assertEqual("1999", oracle["representative_invalid_value"])
        self.assertEqual("executable_tc", oracle["decision"])
        self.assertEqual("OBL-BELOW", oracle["linked_obligation_id"])

    def test_contradictory_allowed_range_becomes_ambiguous(self) -> None:
        statement = "BSR 281. Сумма не менее X и более Y р."
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "requirement_codes": ["BSR 281", "BSR 282"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-BELOW",
                            "atom_id": "ATOM-BELOW",
                            "polarity": "negative",
                            "field_or_block": "Доход",
                            "obligation_ids": ["OBL-BELOW"],
                            "requirement_codes": ["BSR 282"],
                            "requirement_code_evidence": [],
                            "action_clauses": ["Ввести «1999»."],
                            "oracle_clauses": ["Отображается ошибка."],
                        },
                        {
                            "assertion_id": "ASSERT-EQUAL",
                            "atom_id": "ATOM-EQUAL",
                            "polarity": "negative",
                            "semantic_disposition": "testable",
                            "execution_readiness": "ready",
                            "field_or_block": "Доход",
                            "obligation_ids": ["OBL-EQUAL"],
                            "requirement_codes": ["BSR 281"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 281",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": statement,
                                }
                            ],
                            "condition_clauses": ["X = 2000."],
                            "action_clauses": ["Ввести «2000»."],
                            "oracle_clauses": ["Требуется калибровка."],
                            "clause_evidence": [],
                            "supporting_source_bindings": [],
                            "disposition_rationale": "Требуется калибровка границы.",
                        },
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-BELOW",
                    "linked_atom_id": "ATOM-BELOW",
                    "check_type": "boundary",
                    "oracle_source": "BSR 282",
                    "planned_tc_id": "TC-BELOW",
                },
                {
                    "obligation_id": "OBL-EQUAL",
                    "linked_atom_id": "ATOM-EQUAL",
                    "check_type": "boundary",
                    "oracle_source": "not_found",
                    "planned_tc_id": "TC-EQUAL",
                },
            ],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-011",
                    "scope_obligation_id": "SO-NEG-011",
                    "source_row_id": "SRC-029",
                    "requirement_codes": ["BSR 281"],
                    "restriction_type": "lower-bound",
                    "source_statement": statement,
                    "negative_class": "equal-X-disputed",
                    "representative_invalid_value": "2000",
                    "decision": "candidate_tc_required",
                    "linked_atom_id": "ATOM-EQUAL",
                    "linked_obligation_id": "OBL-EQUAL",
                }
            ],
            "dependency_bindings": [],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-029",
                    "bounded_source_text": statement + " X = 2000, Y = 1000000.",
                }
            ]
        }
        boundary = {
            "gaps": [
                {
                    "gap_id": "GAP-SOURCE-RANGE-CONTRADICTION-SRC-029",
                    "gap_type": "ambiguity",
                    "source_row_ids": ["SRC-029"],
                    "exact_source_fragments": [statement],
                    "blocking": False,
                    "downstream_handling": "carry-to-source-model",
                }
            ]
        }

        repairs = _normalize_inclusive_lower_bound_transport(
            payload,
            context,
            boundary,
        )

        ambiguous = payload["source_designs"][0]["assertions"][1]
        self.assertEqual(1, len(repairs))
        self.assertEqual("ambiguous", ambiguous["semantic_disposition"])
        self.assertEqual("dependency-blocked", ambiguous["execution_readiness"])
        self.assertEqual([], ambiguous["obligation_ids"])
        self.assertEqual(["OBL-BELOW"], [item["obligation_id"] for item in payload["obligations"]])
        self.assertEqual("OBL-BELOW", payload["negative_oracles"][0]["linked_obligation_id"])

    def test_contradictory_range_gap_gets_own_non_executable_atom(self) -> None:
        lower = "BSR 281. Сумма не менее X и более Y р."
        upper = "BSR 283. При попытке ввести сумму более Y при потере фокуса"
        upper_with_oracle = (
            f"{upper} поле должно окрашиваться красным цветом и должна "
            "появляться подсказка «Перепроверьте доход»"
        )
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "requirement_codes": ["BSR 281", "BSR 282", "BSR 283"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-LOW",
                            "atom_id": "ATOM-LOW",
                            "semantic_disposition": "testable",
                            "canonical_statement": "Сумма ниже X отклоняется.",
                            "obligation_ids": ["OBL-LOW"],
                            "field_or_block": "Доход",
                            "source_reference": "SRC-029",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 281",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": lower,
                                }
                            ],
                        },
                        {
                            "assertion_id": "ASSERT-LOWER",
                            "atom_id": "ATOM-LOWER",
                            "semantic_disposition": "testable",
                            "field_or_block": "Доход",
                            "source_reference": "SRC-029",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 281",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": lower,
                                }
                            ],
                        },
                        {
                            "assertion_id": "ASSERT-UPPER",
                            "atom_id": "ATOM-UPPER",
                            "semantic_disposition": "testable",
                            "field_or_block": "Доход",
                            "source_reference": "SRC-029",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 283",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": upper_with_oracle,
                                }
                            ],
                        },
                    ],
                }
            ]
        }
        boundary = {
            "gaps": [
                {
                    "gap_id": "GAP-SOURCE-RANGE-CONTRADICTION-SRC-029",
                    "gap_type": "ambiguity",
                    "source_row_ids": ["SRC-029"],
                    "exact_source_fragments": [lower, upper],
                    "blocking": False,
                    "downstream_handling": "carry-to-source-model",
                }
            ]
        }

        repairs = _materialize_range_ambiguity_gap_assertions(payload, boundary)

        ambiguous = payload["source_designs"][0]["assertions"][-1]
        self.assertEqual("ambiguous", ambiguous["semantic_disposition"])
        self.assertEqual("dependency-blocked", ambiguous["execution_readiness"])
        self.assertEqual([], ambiguous["obligation_ids"])
        self.assertEqual("medium", ambiguous["risk"])
        self.assertEqual(1, len(repairs))
        self.assertEqual([], _materialize_range_ambiguity_gap_assertions(payload, boundary))

    def test_range_ambiguity_drops_direct_equal_boundary_calibration(self) -> None:
        lower = "BSR 281. Сумма не менее X и более Y р."
        upper = "BSR 283. При попытке ввести сумму более Y при потере фокуса"
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "requirement_codes": ["BSR 281", "BSR 282", "BSR 283"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-LOW",
                            "atom_id": "ATOM-LOW",
                            "semantic_disposition": "testable",
                            "canonical_statement": "Сумма ниже X отклоняется.",
                            "obligation_ids": ["OBL-LOW"],
                            "field_or_block": "Доход",
                            "source_reference": "SRC-029",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 281",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": lower,
                                }
                            ],
                        },
                        {
                            "assertion_id": "ASSERT-EQX",
                            "atom_id": "ATOM-EQX",
                            "semantic_disposition": "testable",
                            "canonical_statement": (
                                "Поведение суммы, равной X, требует калибровки."
                            ),
                            "condition_clauses": ["Вводимое значение равно X."],
                            "action_clauses": ["Ввести 2000."],
                            "oracle_clauses": ["Фактический исход фиксируется."],
                            "obligation_ids": ["OBL-EQX"],
                            "field_or_block": "Доход",
                            "source_reference": "SRC-029",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 281",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": lower,
                                }
                            ],
                        },
                        {
                            "assertion_id": "ASSERT-HIGH",
                            "atom_id": "ATOM-HIGH",
                            "semantic_disposition": "testable",
                            "canonical_statement": "Сумма выше Y отклоняется.",
                            "obligation_ids": ["OBL-HIGH"],
                            "field_or_block": "Доход",
                            "source_reference": "SRC-029",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 283",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": upper,
                                }
                            ],
                        },
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-LOW",
                    "planned_tc_id": "TC-LOW",
                    "property_type": "boundary",
                    "review_notes": "none_required",
                    "check_type": "negative",
                    "scope_obligation_ids": [],
                },
                {
                    "obligation_id": "OBL-EQX",
                    "planned_tc_id": "candidate:boundary-X",
                    "property_type": "disputed-boundary",
                    "obligation_class": "candidate",
                    "coverage_class": "contradiction",
                    "review_notes": "candidate-ui-calibration",
                    "check_type": "boundary",
                    "oracle_source": "BSR 281 versus BSR 282",
                    "scope_obligation_ids": [],
                },
                {
                    "obligation_id": "OBL-HIGH",
                    "planned_tc_id": "TC-HIGH",
                    "property_type": "boundary",
                    "review_notes": "none_required",
                    "check_type": "negative",
                    "scope_obligation_ids": [],
                },
            ],
            "negative_oracles": [],
            "requiredness_oracles": [],
            "reset_lifecycle_bindings": [],
            "dependency_bindings": [],
            "applicability": [
                {
                    "linked_atoms": ["ATOM-LOW", "ATOM-EQX", "ATOM-HIGH"],
                    "linked_test_cases": [
                        "TC-LOW",
                        "candidate:boundary-X",
                        "TC-HIGH",
                    ],
                }
            ],
        }
        boundary = {
            "gaps": [
                {
                    "gap_id": "GAP-SOURCE-RANGE-CONTRADICTION-SRC-029",
                    "gap_type": "ambiguity",
                    "source_row_ids": ["SRC-029"],
                    "exact_source_fragments": [lower, upper],
                    "blocking": False,
                    "downstream_handling": "carry-to-source-model",
                }
            ]
        }

        repairs = _remove_range_ambiguity_calibration_candidates(payload, boundary)

        self.assertEqual(
            ["OBL-LOW", "OBL-HIGH"],
            [item["obligation_id"] for item in payload["obligations"]],
        )
        self.assertEqual(
            ["ASSERT-LOW", "ASSERT-HIGH"],
            [item["assertion_id"] for item in payload["source_designs"][0]["assertions"]],
        )
        self.assertEqual(
            ["ATOM-LOW", "ATOM-HIGH"],
            payload["applicability"][0]["linked_atoms"],
        )
        self.assertEqual(
            ["TC-LOW", "TC-HIGH"],
            payload["applicability"][0]["linked_test_cases"],
        )
        self.assertEqual(
            "drop-range-ambiguity-ui-calibration-candidate",
            repairs[0]["rule"],
        )
        gap_repairs = _materialize_range_ambiguity_gap_assertions(payload, boundary)
        self.assertEqual(1, len(gap_repairs))
        self.assertEqual(
            "ambiguous",
            payload["source_designs"][0]["assertions"][-1]["semantic_disposition"],
        )

    def test_unbacked_numeric_entry_does_not_claim_persistence(self) -> None:
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-NUMERIC",
                            "semantic_disposition": "testable",
                            "polarity": "positive",
                            "field_or_block": "Доход",
                            "action_clauses": ["Ввести «50000»."],
                            "oracle_clauses": [
                                "Поле видно и сохраняет числовое значение «50000»."
                            ],
                            "obligation_ids": ["OBL-NUMERIC"],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-NUMERIC",
                    "required_behavior": "Значение сохраняется.",
                    "single_expected_behavior": "Значение сохраняется.",
                }
            ],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-029",
                    "bounded_source_text": "BSR 280. Только числовые символы.",
                }
            ]
        }

        repairs = _normalize_unbacked_numeric_entry_persistence(payload, context)

        self.assertEqual(1, len(repairs))
        oracle = payload["source_designs"][0]["assertions"][0]["oracle_clauses"][0]
        self.assertNotIn("сохран", oracle.casefold())
        self.assertIn("отображает введённое", oracle)

    def test_readd_setup_is_completed_from_explicit_assertion_action(self) -> None:
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-030",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-READD",
                            "obligation_ids": ["OBL-READD"],
                            "condition_clauses": [
                                "Существующий подблок заполнен непустыми значениями."
                            ],
                            "action_clauses": [
                                "Удалить заполненный подблок, затем добавить новый подблок."
                            ],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-READD",
                    "obligation_class": "readd-after-delete",
                    "coverage_class": "repeatable-block-lifecycle",
                }
            ],
            "reset_lifecycle_bindings": [
                {
                    "obligation_id": "OBL-READD",
                    "binding_kind": "readd-after-delete",
                    "initial_condition_index": 0,
                    "changed_state_setup": (
                        "Заполнить существующий подблок перед удалением."
                    ),
                }
            ],
        }

        projections = _readd_lifecycle_setup_projections(payload)

        self.assertEqual(1, len(projections))
        self.assertIn("Удалить", projections[0]["changed_state_setup"])
        self.assertIn("добавить новый", projections[0]["changed_state_setup"])

    def test_candidate_negative_signal_is_split_from_positive_typed_chain(
        self,
    ) -> None:
        statement = "BSR 280. Только числовые символы."
        clause_evidence = [
            {
                "clause_kind": kind,
                "clause_index": 0,
                "source_row_id": "SRC-029",
                "exact_source_fragment": statement,
            }
            for kind in ("condition", "action", "oracle")
        ]
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-029-EDIT",
                            "atom_id": "ATOM-SRC-029-EDIT",
                            "obligation_ids": ["OBL-SRC-029-EDIT"],
                            "field_or_block": "Численность сотрудников",
                            "polarity": "negative",
                            "source_property_id": (
                                "FP-SRC-029-EDITABILITY-EDITABLE"
                            ),
                            "requirement_codes": ["BSR 280"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 280",
                                    "source_row_id": "SRC-029",
                                    "exact_source_fragment": statement,
                                }
                            ],
                            "condition_clauses": ["Поле доступно."],
                            "action_clauses": ["Ввести значение 50000."],
                            "oracle_clauses": ["Значение можно изменить."],
                            "clause_evidence": clause_evidence,
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-SRC-029-EDIT",
                    "linked_atom_id": "ATOM-SRC-029-EDIT",
                    "source_property_id": "FP-SRC-029-EDITABILITY-EDITABLE",
                    "property_type": "editability",
                    "obligation_class": "ui-calibration-candidate",
                    "source_ref": "SRC-029",
                    "review_notes": "candidate-ui-calibration",
                    "design_dimension": "boundary",
                    "check_type": "negative",
                    "coverage_class": "invalid-numeric-format",
                    "input_class": "non-numeric",
                    "oracle_source": "not_found",
                    "test_data": "50A00",
                    "scope_obligation_ids": ["SO-NEG-010"],
                    "planned_tc_id": "candidate:SO-NEG-010",
                },
                {
                    "obligation_id": "OBL-SRC-029-FORMAT",
                    "linked_atom_id": "ATOM-SRC-029-FORMAT",
                    "source_property_id": "none_required",
                    "property_type": "format",
                    "source_ref": "SRC-029",
                    "review_notes": "none_required",
                    "design_dimension": "boundary",
                    "check_type": "positive",
                    "test_data": "50000",
                    "planned_tc_id": "TC-SRC-029-FORMAT",
                },
            ],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-010",
                    "source_row_id": "SRC-029",
                    "source_statement": statement,
                    "requirement_codes": ["BSR 280"],
                    "scope_obligation_id": "SO-NEG-010",
                    "restriction_type": "numeric",
                    "negative_class": "non-numeric",
                    "representative_invalid_value": "50A00",
                    "decision": "candidate_tc_required",
                    "oracle_status": "ui-calibration-required",
                    "linked_atom_id": "ATOM-SRC-029-EDIT",
                    "linked_obligation_id": "OBL-SRC-029-EDIT",
                }
            ],
        }

        repairs = _split_candidate_signal_from_incompatible_positive_chain(
            payload,
            {
                "source_rows": [
                    {
                        "source_row_id": "SRC-029",
                        "bounded_source_text": statement,
                    }
                ]
            },
        )

        self.assertEqual(1, len(repairs))
        original = payload["source_designs"][0]["assertions"][0]
        candidate = payload["source_designs"][0]["assertions"][1]
        self.assertEqual([], original["requirement_codes"])
        self.assertEqual(["BSR 280"], candidate["requirement_codes"])
        self.assertEqual("negative", candidate["polarity"])
        self.assertEqual("positive", original["polarity"])
        self.assertIn(
            "допускает только числовые символы",
            candidate["canonical_statement"],
        )
        self.assertIn(
            "способ отклонения или преобразования",
            candidate["canonical_statement"],
        )
        self.assertEqual(
            "none_required",
            candidate["source_property_id"],
        )
        self.assertEqual(
            "OBL-SIG-NEG-010",
            payload["negative_oracles"][0]["linked_obligation_id"],
        )
        candidate_obligation = next(
            item
            for item in payload["obligations"]
            if item["obligation_id"] == "OBL-SIG-NEG-010"
        )
        original_obligation = payload["obligations"][0]
        self.assertEqual("boundary", candidate_obligation["check_type"])
        self.assertEqual([], payload["obligations"][0]["scope_obligation_ids"])
        self.assertEqual("none_required", original_obligation["review_notes"])
        self.assertEqual("TC-SRC-029-EDIT", original_obligation["planned_tc_id"])
        self.assertEqual("positive", original_obligation["check_type"])
        self.assertEqual("50000", original_obligation["test_data"])
        self.assertEqual("typed-property", original_obligation["obligation_class"])

        replacement_repairs = _materialize_distinct_editability_replacements(payload)
        self.assertEqual(1, len(replacement_repairs))
        self.assertEqual(
            "initial=50000; replacement=60000",
            original_obligation["test_data"],
        )

        candidate["canonical_statement"] = "Ввести невалидное значение."
        candidate["oracle_clauses"] = ["Требуется UI-калибровка."]
        candidate_obligation["required_behavior"] = "Требуется UI-калибровка."
        candidate_obligation["single_expected_behavior"] = (
            "Требуется UI-калибровка."
        )
        normalized = _normalize_negative_candidate_known_violation(payload)
        self.assertEqual(1, len(normalized))
        self.assertIn(
            "не соответствует ограничению источника",
            candidate["oracle_clauses"][0],
        )
        self.assertIn(statement.rstrip("."), candidate["oracle_clauses"][0])
        self.assertIn(
            "способ отклонения или преобразования",
            candidate["oracle_clauses"][0],
        )

    def test_future_issue_date_clarification_preserves_save_block(self) -> None:
        answer = "Дата выдачи позже текущей даты блокирует сохранение."
        answer_sha = hashlib.sha256(answer.encode("utf-8")).hexdigest()
        projection = _future_issue_date_save_block_projection(
            {
                "semantic_disposition": "testable",
                "execution_readiness": "ready",
                "requirement_codes": ["BSR 101"],
                "oracle_clauses": ["Будущая дата не принимается."],
                "clarification_clause_bindings": [
                    {
                        "clarification_id": "CLR-PASS-003",
                        "clause_kind": "oracle",
                        "clause_index": 0,
                        "exact_answer_sha256": answer_sha,
                    }
                ],
            },
            [
                {
                    "clarification_id": "CLR-PASS-003",
                    "exact_answer": answer,
                    "exact_answer_sha256": answer_sha,
                }
            ],
        )
        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual(
            projection["oracle_clauses"],
            ["Сохранение формы блокируется для даты выдачи позже текущей даты."],
        )
        self.assertEqual(
            projection["obligation_fields"]["oracle_source"],
            "BSR 101 + CLR-PASS-003",
        )

    def test_verified_fixture_projection_uses_exact_suggestion(self) -> None:
        assertion = {
            "semantic_disposition": "testable",
            "obligation_ids": ["OBL-001"],
            "field_or_block": "Кем выдан — список DaData",
        }
        obligations = {
            "OBL-001": {
                "property_type": "multi-suggestion-selection",
                "test_data": "FX-DADATA-FMS-POS-001",
            }
        }
        projection = _verified_fixture_clause_projection(
            assertion,
            obligations,
            {
                "FX-DADATA-FMS-POS-001": {
                    "request_parameters": {"query": "772-053"},
                    "expected_response": {
                        "exact_suggestion": "ОВД ЗЮЗИНО Г. МОСКВЫ",
                        "minimum_suggestion_count": 2,
                    },
                }
            },
        )
        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertIn("ОВД ЗЮЗИНО Г. МОСКВЫ", projection["action_clauses"][0])
        self.assertIn("FX-DADATA-FMS-POS-001", projection["action_clauses"][0])
        self.assertIn("772-053", projection["condition_clauses"][0])

    def test_verified_fixture_loader_requires_matching_context_hash(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            relative = Path("work/FX-001.verification.json")
            path = root / relative
            path.parent.mkdir(parents=True)
            payload = {
                "fixture_id": "FX-001",
                "status": "verified",
                "request": {"parameters": {"query": "Q"}},
                "expected_response": {"exact_suggestion": "VALUE"},
                "response_sha256": "1" * 64,
            }
            raw = json.dumps(payload).encode("utf-8")
            path.write_bytes(raw)
            context = {
                "sources": [{"path": relative.as_posix()}],
                "source_cache": {
                    "input_fingerprints": [
                        {
                            "path": relative.as_posix(),
                            "role": "external-vendor-reference",
                            "sha256": hashlib.sha256(raw).hexdigest(),
                        }
                    ]
                },
            }
            contracts = _load_verified_fixture_contracts(context, root)
            self.assertIn("FX-001", contracts)
            context["source_cache"]["input_fingerprints"][0]["sha256"] = "0" * 64
            self.assertEqual(_load_verified_fixture_contracts(context, root), {})

    def test_verified_fixture_loader_binds_hash_matched_response_data(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            fixture_dir = Path("work/FX-PARTY-001")
            verification_relative = fixture_dir / "FX-PARTY-001.verification.json"
            response_relative = fixture_dir / "FX-PARTY-001.response.json"
            response = {
                "suggestions": [
                    {
                        "value": "ПАО СБЕРБАНК",
                        "data": {
                            "state": {"status": "ACTIVE"},
                            "opf": {"short": "ПАО"},
                            "address": {"value": "г Москва, ул Вавилова, д 19"},
                        },
                    }
                ]
            }
            response_raw = json.dumps(
                response, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            response_sha = hashlib.sha256(response_raw).hexdigest()
            verification = {
                "fixture_id": "FX-PARTY-001",
                "status": "verified",
                "request": {"parameters": {"query": "7707083893"}},
                "expected_response": {"exact_suggestion": "ПАО СБЕРБАНК"},
                "response_sha256": response_sha,
                "response_snapshot": response_relative.name,
            }
            verification_raw = json.dumps(
                verification, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            (root / fixture_dir).mkdir(parents=True)
            (root / response_relative).write_bytes(response_raw)
            (root / verification_relative).write_bytes(verification_raw)
            context = {
                "sources": [
                    {"path": verification_relative.as_posix()},
                    {"path": response_relative.as_posix()},
                ],
                "source_cache": {
                    "input_fingerprints": [
                        {
                            "path": verification_relative.as_posix(),
                            "role": "external-vendor-reference",
                            "sha256": hashlib.sha256(verification_raw).hexdigest(),
                        },
                        {
                            "path": response_relative.as_posix(),
                            "role": "external-vendor-reference",
                            "sha256": response_sha,
                        },
                    ]
                },
            }

            contracts = _load_verified_fixture_contracts(context, root)

        self.assertEqual(
            "г Москва, ул Вавилова, д 19",
            contracts["FX-PARTY-001"]["matched_data"]["address"]["value"],
        )
        self.assertEqual(
            "г Москва, ул Вавилова, д 19",
            contracts["FX-PARTY-001"]["expected_response"][
                "exact_components"
            ]["address.value"],
        )

    def test_dictionary_completeness_moves_from_visibility_to_selection(self) -> None:
        payload = {
            "source_designs": [
                {
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-VIS",
                            "field_or_block": "Тип должности",
                            "obligation_ids": ["OBL-VIS"],
                        },
                        {
                            "assertion_id": "ASSERT-EDIT",
                            "field_or_block": "Тип должности",
                            "obligation_ids": ["OBL-EDIT"],
                            "canonical_statement": "Поле редактируемо.",
                            "action_clauses": ["Выбрать значение."],
                            "oracle_clauses": ["Значение отображается."],
                        },
                    ]
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-VIS",
                    "source_ref": "SRC-001",
                    "property_type": "visibility",
                    "dictionary_refs": ["DICT-001"],
                    "dictionary_coverage": "all-leaf-values",
                },
                {
                    "obligation_id": "OBL-EDIT",
                    "source_ref": "SRC-001",
                    "property_type": "editability",
                    "dictionary_refs": ["DICT-001"],
                    "dictionary_coverage": "reference-only",
                },
            ],
            "dependency_bindings": [
                {
                    "kind": "dictionary",
                    "name": "Типы должности",
                    "linked_obligation_ids": ["OBL-EDIT"],
                }
            ],
        }

        repairs = _reassign_dictionary_completeness_ownership(
            payload,
            {
                "dictionary_inventory": [
                    {
                        "name": "Типы должности",
                        "source_path": "support/dictionaries.md",
                        "source_location": "section: positions",
                        "active_values": ["Сотрудник", "Руководитель"],
                    }
                ]
            },
        )

        self.assertEqual(1, len(repairs))
        visibility, selection = payload["obligations"]
        self.assertEqual([], visibility["dictionary_refs"])
        self.assertEqual("none_required", visibility["dictionary_coverage"])
        self.assertEqual("all-leaf-values", selection["dictionary_coverage"])
        self.assertEqual("dictionary-completeness", selection["obligation_class"])
        self.assertEqual("Сотрудник; Руководитель", selection["test_data"])
        assertion = payload["source_designs"][0]["assertions"][1]
        self.assertIn("Количество активных значений в списке: 2", assertion["oracle_clauses"][0])
        self.assertIn("«Сотрудник»", assertion["oracle_clauses"][0])

    def test_direct_dictionary_owner_materializes_full_inventory_in_action(self) -> None:
        payload = {
            "source_designs": [
                {
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-EDIT",
                            "field_or_block": "Тип должности",
                            "obligation_ids": ["OBL-EDIT"],
                            "canonical_statement": "Поле редактируемо.",
                            "action_clauses": ["Выбрать «Сотрудник»."],
                            "oracle_clauses": ["Значение сохранено."],
                        }
                    ]
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-EDIT",
                    "dictionary_refs": ["DICT-003"],
                    "dictionary_coverage": "all-leaf-values",
                    "test_data": "Все активные значения DICT-003",
                }
            ],
            "dictionaries": [
                {
                    "dictionary_id": "DICT-003",
                    "source_file": "support/dictionaries.md",
                    "source_location": "section: positions",
                    "active_values": ["Сотрудник", "Руководитель"],
                }
            ],
        }

        repairs = _reassign_dictionary_completeness_ownership(payload)

        self.assertEqual(1, len(repairs))
        self.assertEqual(
            "bind-direct-dictionary-owner-to-full-inventory",
            repairs[0]["rule"],
        )
        obligation = payload["obligations"][0]
        assertion = payload["source_designs"][0]["assertions"][0]
        self.assertEqual("Сотрудник; Руководитель", obligation["test_data"])
        self.assertIn("«Сотрудник»; «Руководитель»", assertion["action_clauses"][0])
        self.assertIn("Количество активных значений в списке: 2", assertion["oracle_clauses"][0])
        self.assertEqual([], _reassign_dictionary_completeness_ownership(payload))

    def test_duplicate_editability_uses_second_concrete_value(self) -> None:
        payload = {
            "source_designs": [
                {
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-FORMAT",
                            "field_or_block": "Рабочий телефон",
                            "obligation_ids": ["OBL-FORMAT"],
                        },
                        {
                            "assertion_id": "ASSERT-EDIT",
                            "field_or_block": "Рабочий телефон",
                            "obligation_ids": ["OBL-EDIT"],
                            "canonical_statement": "Поле редактируемо.",
                            "condition_clauses": ["Поле доступно."],
                            "action_clauses": ["Ввести 9991234567."],
                            "oracle_clauses": ["Номер отображается."],
                        },
                    ]
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-FORMAT",
                    "source_ref": "SRC-001",
                    "property_type": "format",
                    "design_dimension": "boundary",
                    "test_data": "9991234567",
                },
                {
                    "obligation_id": "OBL-EDIT",
                    "source_ref": "SRC-001",
                    "property_type": "editability",
                    "dictionary_refs": [],
                    "test_data": "9991234567",
                },
            ],
        }

        repairs = _materialize_distinct_editability_replacements(payload)

        self.assertEqual(1, len(repairs))
        obligation = payload["obligations"][1]
        self.assertEqual(
            "initial=9991234567; replacement=9123456789",
            obligation["test_data"],
        )
        assertion = payload["source_designs"][0]["assertions"][1]
        self.assertIn("Заменить", assertion["action_clauses"][0])
        self.assertIn("+7(912)-345-67-89", assertion["oracle_clauses"][0])

    def test_verified_party_fixture_projection_uses_exact_autofill_value(self) -> None:
        projection = _verified_party_fixture_clause_projection(
            {
                "semantic_disposition": "testable",
                "obligation_ids": ["OBL-001"],
                "field_or_block": "ОПФ",
            },
            {
                "OBL-001": {
                    "property_type": "integration-ui",
                    "input_class": "registered-fixture",
                }
            },
            {
                "FX-PARTY-001": {
                    "request_parameters": {"query": "7707083893"},
                    "expected_response": {"exact_suggestion": "ПАО СБЕРБАНК"},
                    "matched_data": {
                        "state": {"status": "ACTIVE"},
                        "opf": {"short": "ПАО"},
                        "address": {"value": "г Москва, ул Вавилова, д 19"},
                    },
                }
            },
        )

        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertIn("7707083893", projection["action_clauses"][0])
        self.assertIn("ПАО СБЕРБАНК", projection["action_clauses"][0])
        self.assertIn("«ПАО»", projection["oracle_clauses"][0])

    def test_liquidated_party_fixture_projection_is_negative(self) -> None:
        projection = _verified_party_fixture_clause_projection(
            {
                "semantic_disposition": "testable",
                "obligation_ids": ["OBL-001"],
                "field_or_block": "Наименование организации, ИНН",
                "canonical_statement": "Недействующая организация блокирует Далее.",
            },
            {"OBL-001": {"property_type": "integration-ui"}},
            {
                "FX-PARTY-LIQUIDATED-001": {
                    "request_parameters": {"query": "7733073764"},
                    "expected_response": {
                        "exact_suggestion": "ФОРМАД-ПЛАСТ ООО 7701"
                    },
                    "matched_data": {
                        "state": {"status": "LIQUIDATED"},
                        "opf": {"short": "ООО"},
                        "address": {"value": "г Москва"},
                    },
                }
            },
        )

        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual("negative", projection["polarity"])
        self.assertIn("7733073764", projection["action_clauses"][0])

    def test_verified_party_fixture_projection_uses_exact_address_value(self) -> None:
        assertion = {
                "semantic_disposition": "testable",
                "obligation_ids": ["OBL-001"],
                "field_or_block": "Фактический адрес работы",
                "canonical_statement": "Адрес автоматически заполняется после выбора организации.",
            }
        obligations = {"OBL-001": {"property_type": "ui-autofill"}}
        fixtures = {
                "FX-PARTY-001": {
                    "request_parameters": {"query": "7707083893"},
                    "expected_response": {"exact_suggestion": "ПАО СБЕРБАНК"},
                    "matched_data": {
                        "state": {"status": "ACTIVE"},
                        "opf": {"short": "ПАО"},
                        "address": {"value": "г Москва, ул Вавилова, д 19"},
                    },
                }
            }
        projection = _verified_party_fixture_clause_projection(
            assertion,
            obligations,
            fixtures,
        )

        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertIn("7707083893", projection["action_clauses"][0])
        self.assertIn("ПАО СБЕРБАНК", projection["action_clauses"][0])
        self.assertIn("г Москва, ул Вавилова, д 19", projection["oracle_clauses"][0])

        typed_assertion = copy.deepcopy(assertion)
        typed_assertion["source_property_id"] = (
            "FP-SRC-023-EDITABILITY-EDITABLE"
        )
        self.assertIsNone(
            _verified_party_fixture_clause_projection(
                typed_assertion,
                obligations,
                fixtures,
            )
        )

    def test_visibility_code_is_split_from_typed_requiredness(self) -> None:
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-032",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-078",
                            "atom_id": "ATOM-078",
                            "semantic_disposition": "testable",
                            "risk": "high",
                            "source_property_id": (
                                "FP-SRC-032-REQUIREDNESS-REQUIRED"
                            ),
                            "field_or_block": "Серия предыдущего паспорта",
                            "source_reference": "source/*[30]/*[2]",
                            "requirement_codes": ["BSR 110"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 110",
                                    "source_row_id": "SRC-032",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": (
                                        "BSR 110. Видимость: Да, если признак "
                                        "«Клиент менял паспорт» = «Да»."
                                    ),
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                }
                            ],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "obligation_ids": ["OBL-059"],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-059",
                    "package_id": "WP-01",
                    "planned_tc_id": "TC-059",
                }
            ],
        }
        repairs = _split_visibility_code_from_typed_requiredness(
            payload,
            {
                "source_rows": [
                    {
                        "source_row_id": "SRC-032",
                        "source_ref": "source/*[30]",
                        "field_or_action": "Серия предыдущего паспорта",
                    }
                ]
            },
        )
        self.assertEqual(len(repairs), 1)
        assertions = payload["source_designs"][0]["assertions"]
        self.assertEqual(assertions[0]["requirement_codes"], [])
        self.assertEqual(assertions[1]["requirement_codes"], ["BSR 110"])
        self.assertIn("отображается", assertions[1]["oracle_clauses"][0])
        self.assertEqual(payload["obligations"][-1]["property_type"], "conditional-visibility")

    def test_inclusive_twentieth_birthday_clarification_is_not_shortened(self) -> None:
        answer = (
            "Паспорт, выданный до или в день 20-летия, действителен до "
            "20-летия + 90 дней включительно."
        )
        answer_sha = hashlib.sha256(answer.encode("utf-8")).hexdigest()
        assertion = {
            "semantic_disposition": "testable",
            "execution_readiness": "ready",
            "canonical_statement": (
                "Паспорт, выданный в диапазоне от 14 лет до 20-летия, "
                "после допустимого срока признаётся просроченным."
            ),
            "condition_clauses": [
                "Дата выдачи находится от 14 лет до достижения 20-летнего "
                "возраста; текущая дата позже 20-летия плюс 90 календарных дней."
            ],
            "clarification_clause_bindings": [
                {
                    "clarification_id": "CLR-PASS-003",
                    "clause_kind": "condition",
                    "clause_index": 0,
                    "exact_answer_sha256": answer_sha,
                }
            ],
        }
        projection = _inclusive_twentieth_birthday_projection(
            assertion,
            [
                {
                    "clarification_id": "CLR-PASS-003",
                    "exact_answer": answer,
                    "exact_answer_sha256": answer_sha,
                }
            ],
        )
        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertIn("до или в день 20-летия", projection["canonical_statement"])
        self.assertIn(
            "до или в день 20-летия",
            projection["condition_clauses"][0],
        )
        self.assertIn(
            "20-летие + 91 календарный день",
            projection["obligation_fields"]["test_data"],
        )

    def test_bare_requirement_definition_gap_becomes_ambiguous(self) -> None:
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-001",
                            "atom_id": "ATOM-001",
                            "source_property_id": "none_required",
                            "semantic_disposition": "testable",
                            "requirement_codes": ["BSR 114"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 114",
                                    "exact_source_fragment": "BSR 114.",
                                }
                            ],
                            "obligation_ids": ["OBL-001"],
                        }
                    ],
                }
            ],
            "obligations": [
                {"obligation_id": "OBL-001", "planned_tc_id": "TC-001"}
            ],
            "dependency_bindings": [],
            "applicability": [],
            "negative_oracles": [],
            "requiredness_oracles": [],
        }
        context = {
            "source_rows": [
                {"source_row_id": "SRC-001", "bounded_source_text": "BSR 114."}
            ]
        }
        boundary = {
            "gaps": [
                {
                    "gap_id": "GAP-001",
                    "gap_type": "missing-source-definition",
                    "blocking": False,
                    "downstream_handling": "carry-to-source-model",
                    "source_row_ids": ["SRC-001"],
                    "exact_source_fragments": ["BSR 114."],
                }
            ]
        }
        repairs = _materialize_bare_requirement_definition_gaps(
            payload,
            context,
            boundary,
        )
        assertion = payload["source_designs"][0]["assertions"][0]
        self.assertEqual("ambiguous", assertion["semantic_disposition"])
        self.assertEqual("dependency-blocked", assertion["execution_readiness"])
        self.assertEqual([], assertion["obligation_ids"])
        self.assertEqual([], payload["obligations"])
        self.assertIn(
            "bind-bare-requirement-code-to-definition-gap",
            [item["rule"] for item in repairs],
        )
        self.assertEqual(
            [],
            _materialize_missing_definition_gap_assertions(payload, boundary),
        )
        self.assertEqual(
            1,
            len(payload["source_designs"][0]["assertions"]),
        )

    def test_declared_ui_calibration_cannot_remain_source_backed(self) -> None:
        assertion = {
            "semantic_disposition": "testable",
            "oracle_clauses": [
                "Значение «1112» не подтверждается как допустимое; "
                "точная UI-реакция подлежит калибровке."
            ],
            "obligation_ids": ["OBL-001"],
        }
        obligation = {
            "obligation_id": "OBL-001",
            "review_notes": "UI reaction calibration allowed",
            "oracle_source": "BSR 86",
            "required_behavior": "Не допустить значение.",
            "single_expected_behavior": "Значение не допускается.",
        }
        self.assertTrue(
            _canonicalize_declared_ui_calibration(
                assertion,
                {"OBL-001": obligation},
            )
        )
        self.assertEqual("candidate-ui-calibration", obligation["review_notes"])
        self.assertEqual("not_found", obligation["oracle_source"])
        self.assertIn(
            "точный UI-триггер и отклик требуют калибровки",
            assertion["oracle_clauses"][0],
        )
        self.assertEqual(
            assertion["oracle_clauses"][0],
            obligation["single_expected_behavior"],
        )

    def test_requiredness_calibration_candidate_drops_editability_branch(self) -> None:
        assertion = {
            "semantic_disposition": "testable",
            "source_property_id": "FP-SRC-029-REQUIREDNESS-REQUIRED",
            "field_or_block": "Среднемесячный доход",
            "obligation_ids": ["OBL-001"],
            "canonical_statement": "Поле обязательно и редактируемо.",
            "action_clauses": ["Оставить пустым, затем ввести «50000»."],
            "oracle_clauses": ["Пустое невалидно, затем отображается «50000»."],
        }
        obligation = {
            "property_type": "requiredness",
            "review_notes": "candidate-ui-calibration",
            "oracle_source": "not_found",
        }

        self.assertTrue(
            _canonicalize_requiredness_calibration_candidate(
                assertion,
                {"OBL-001": obligation},
            )
        )
        self.assertEqual(
            ["Оставить поле «Среднемесячный доход» пустым."],
            assertion["action_clauses"],
        )
        self.assertNotIn("50000", json.dumps(assertion, ensure_ascii=False))
        self.assertEqual("empty-value", obligation["input_class"])

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
    def _context(cls) -> dict[str, object]:
        context = {
            "version": 1,
            "package_id": "WP-01",
            "scope_slug": "employment-main-work",
            "scope_boundary": {
                "target": "Проверить основную работу.",
                "include": ["Выбор статуса.", "Очистка заполненного поля."],
                "exclude": ["Дополнительная работа."],
            },
            "mockup_locators": ["mockup:employment-main-work"],
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "field_or_action": "Контекст раздела",
                    "source_ref": "section 1",
                    "bounded_source_text": "Раздел 1. Сведения о занятости.",
                    "requirement_codes_hint": [],
                    "in_scope_hint": "no; section context",
                },
                {
                    "source_row_id": "SRC-002",
                    "field_or_action": "Статус",
                    "source_ref": "BSR 1",
                    "bounded_source_text": (
                        "BSR 1. Поле «Статус» заполняется по справочнику Статусы: "
                        "Активен, Неактивен. При выборе значения система сохраняет "
                        "выбранное значение."
                    ),
                    "requirement_codes_hint": ["BSR 1"],
                    "in_scope_hint": "yes; target behavior",
                },
                {
                    "source_row_id": "SRC-003",
                    "field_or_action": "Очистить",
                    "source_ref": "BSR 2",
                    "bounded_source_text": (
                        "BSR 2. Если поле заполнено изменённым значением, при нажатии "
                        "кнопки «Очистить» поле очищается и становится пустым."
                    ),
                    "requirement_codes_hint": ["BSR 2"],
                    "in_scope_hint": "yes; target behavior",
                },
            ],
            "sources": [
                {
                    "path": "source/main.xhtml",
                    "role": "main-ft-xhtml",
                    "manifest_binding": "assertion-source",
                }
            ],
            "dictionary_inventory": {
                "Статусы": ["Активен", "Неактивен"],
            },
        }
        return cls._bind_context(context)

    def test_collapsed_negative_branches_split_with_dependency_evidence(self) -> None:
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-AGE",
                    "bounded_source_text": (
                        "До 20 лет — один срок. После достижения 45-летнего "
                        "возраста — бессрочно."
                    ),
                }
            ]
        }
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-AGE",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-AGE",
                            "atom_id": "ATOM-AGE",
                            "obligation_ids": ["OBL-AGE"],
                            "condition_clauses": ["Возраст до 20.", "Возраст от 45."],
                            "action_clauses": ["Ввести дату 1.", "Ввести дату 2."],
                            "oracle_clauses": ["Срок 1.", "Срок бессрочный."],
                            "clause_evidence": [
                                {"clause_kind": "condition", "clause_index": 0, "source_row_id": "SRC-AGE", "exact_source_fragment": "До 20 лет"},
                                {"clause_kind": "action", "clause_index": 0, "source_row_id": "SRC-AGE", "exact_source_fragment": "До 20 лет"},
                                {"clause_kind": "oracle", "clause_index": 0, "source_row_id": "SRC-AGE", "exact_source_fragment": "один срок"},
                                {"clause_kind": "condition", "clause_index": 1, "source_row_id": "SRC-AGE", "exact_source_fragment": "бессрочно"},
                                {"clause_kind": "action", "clause_index": 1, "source_row_id": "SRC-AGE", "exact_source_fragment": "бессрочно"},
                                {"clause_kind": "oracle", "clause_index": 1, "source_row_id": "SRC-AGE", "exact_source_fragment": "бессрочно"},
                            ],
                            "clarification_clause_bindings": [],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-AGE",
                    "linked_atom_id": "ATOM-AGE",
                    "planned_tc_id": "TC-AGE",
                    "scope_obligation_ids": ["SO-AGE-1", "SO-AGE-2"],
                }
            ],
            "negative_oracles": [
                {
                    "decision": "executable_tc",
                    "scope_obligation_id": "SO-AGE-1",
                    "signal_id": "SIG-AGE-1",
                    "linked_atom_id": "ATOM-AGE",
                    "linked_obligation_id": "OBL-AGE",
                    "planned_tc_or_gap": "TC-AGE",
                    "restriction_type": "lower-bound",
                    "negative_class": "young",
                    "representative_invalid_value": "1",
                },
                {
                    "decision": "executable_tc",
                    "scope_obligation_id": "SO-AGE-2",
                    "signal_id": "SIG-AGE-2",
                    "linked_atom_id": "ATOM-AGE",
                    "linked_obligation_id": "OBL-AGE",
                    "planned_tc_or_gap": "TC-AGE",
                    "restriction_type": "upper-bound",
                    "negative_class": "old",
                    "representative_invalid_value": "2",
                },
            ],
            "dependency_bindings": [
                {
                    "source_row_ids": ["SRC-AGE"],
                    "exact_source_fragments": ["45-летнего возраста"],
                    "linked_assertion_ids": ["ASSERT-AGE"],
                    "linked_atom_ids": ["ATOM-AGE"],
                    "linked_obligation_ids": ["OBL-AGE"],
                }
            ],
            "reset_lifecycle_bindings": [],
        }

        projection = _collapsed_executable_negative_oracle_projection(
            payload,
            context=context,
        )

        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual(2, len(projection["new_assertions"]))
        second_evidence = projection["new_assertions"][1]["clause_evidence"]
        self.assertTrue(
            any(
                "45-летнего возраста" in item["exact_source_fragment"]
                for item in second_evidence
            )
        )
        self.assertEqual(
            ["ASSERT-AGE-SO-AGE-1", "ASSERT-AGE-SO-AGE-2"],
            projection["canonical_dependency_bindings"][0]["linked_assertion_ids"],
        )

    def test_mixed_calibration_and_executable_negative_branches_split(self) -> None:
        lower = "BSR 281. Сумма не менее X и более Y р."
        rejection = (
            "BSR 282. При попытке ввести сумму менее X при потере фокуса "
            "поле должно окрашиваться красным цветом и должна появляться "
            "подсказка «Введите сумму более X руб.»"
        )
        upper = (
            "BSR 283. При попытке ввести сумму более Y при потере фокуса "
            "поле должно окрашиваться красным цветом и должна появляться "
            "подсказка «Перепроверьте доход»"
        )
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-029",
                    "bounded_source_text": (
                        f"Доход. {lower} X = 2000, Y = 1000000 "
                        f"{rejection} {upper}"
                    ),
                }
            ]
        }
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-029",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-BOUND",
                            "atom_id": "ATOM-BOUND",
                            "obligation_ids": ["OBL-BOUND"],
                            "field_or_block": "Доход",
                            "source_property_id": "none_required",
                            "condition_clauses": ["X = 2000; Y = 1000000."],
                            "action_clauses": ["Проверить обе границы."],
                            "oracle_clauses": ["Проверить две реакции."],
                            "requirement_code_evidence": [
                                {"requirement_code": "BSR 281"},
                                {"requirement_code": "BSR 282"},
                                {"requirement_code": "BSR 283"},
                            ],
                            "clause_evidence": [
                                {"clause_kind": "condition", "clause_index": 0, "source_row_id": "SRC-029", "exact_source_fragment": "Сумма не менее X"},
                                {"clause_kind": "action", "clause_index": 0, "source_row_id": "SRC-029", "exact_source_fragment": "потере фокуса"},
                                {"clause_kind": "oracle", "clause_index": 0, "source_row_id": "SRC-029", "exact_source_fragment": "Перепроверьте доход"},
                            ],
                            "clarification_clause_bindings": [],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-BOUND",
                    "linked_atom_id": "ATOM-BOUND",
                    "source_property_id": "none_required",
                    "planned_tc_id": "TC-BSR-281-283",
                    "check_type": "boundary",
                    "scope_obligation_ids": ["SO-NEG-011", "SO-NEG-012"],
                }
            ],
            "negative_oracles": [
                {
                    "decision": "candidate_tc_required",
                    "oracle_status": "ui-calibration-required",
                    "scope_obligation_id": "SO-NEG-011",
                    "signal_id": "SIG-NEG-011",
                    "linked_atom_id": "ATOM-BOUND",
                    "linked_obligation_id": "OBL-BOUND",
                    "planned_tc_or_gap": "candidate:SO-NEG-011",
                    "restriction_type": "lower-bound",
                    "negative_class": "below-X",
                    "representative_invalid_value": "1999",
                    "source_row_id": "SRC-029",
                    "source_statement": lower,
                    "requirement_codes": ["BSR 281"],
                    "oracle_source": "not_found",
                },
                {
                    "decision": "executable_tc",
                    "oracle_status": "source-backed",
                    "scope_obligation_id": "SO-NEG-012",
                    "signal_id": "SIG-NEG-012",
                    "linked_atom_id": "ATOM-BOUND",
                    "linked_obligation_id": "OBL-BOUND",
                    "planned_tc_or_gap": "TC-BSR-283",
                    "restriction_type": "upper-bound",
                    "negative_class": "above-Y",
                    "representative_invalid_value": "1000001",
                    "source_row_id": "SRC-029",
                    "source_statement": upper,
                    "requirement_codes": ["BSR 283"],
                    "oracle_source": "BSR 283",
                },
            ],
            "dependency_bindings": [],
        }

        projection = _collapsed_candidate_negative_oracle_projection(
            payload,
            context=context,
            boundary={
                "gaps": [
                    {
                        "gap_id": "GAP-SOURCE-RANGE-CONTRADICTION-SRC-029",
                        "gap_type": "ambiguity",
                        "source_row_ids": ["SRC-029"],
                        "exact_source_fragments": [lower, upper],
                        "blocking": False,
                        "downstream_handling": "carry-to-source-model",
                    }
                ]
            },
        )

        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertTrue(projection["mixed_decisions"])
        self.assertEqual(
            ["TC-BSR-282", "TC-BSR-283"],
            [item["planned_tc_id"] for item in projection["new_obligations"]],
        )
        self.assertEqual(
            [["SO-NEG-011"], ["SO-NEG-012"]],
            [item["scope_obligation_ids"] for item in projection["new_obligations"]],
        )
        self.assertIn(
            "Перевести фокус с поля",
            projection["new_assertions"][1]["action_clauses"][0],
        )
        self.assertEqual(
            ["executable_tc", "executable_tc"],
            [item["decision"] for item in projection["new_oracles"]],
        )
        self.assertEqual(3, len(projection["new_assertions"]))
        self.assertEqual(
            "ambiguous",
            projection["new_assertions"][2]["semantic_disposition"],
        )
        self.assertEqual(
            ["BSR 283"],
            projection["new_assertions"][1]["requirement_codes"],
        )

    def test_combined_calibration_pair_splits_allowed_and_invalid_values(self) -> None:
        statement = (
            "BSR 111. Ограничение на формат: только 4 числовых символа. "
            "Не должно быть трёх одинаковых цифр подряд"
        )
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-032",
                    "bounded_source_text": f"Серия. {statement}",
                }
            ]
        }
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-032",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-FMT",
                            "atom_id": "ATOM-FMT",
                            "obligation_ids": ["OBL-FMT"],
                            "source_property_id": "none_required",
                            "field_or_block": "Серия паспорта",
                            "condition_clauses": ["Поле видно."],
                            "action_clauses": [
                                "Ввести допустимое «1234», затем недопустимое «1112»."
                            ],
                            "oracle_clauses": [
                                "«1234» принимается; реакция на «1112» требует UI-калибровки."
                            ],
                            "clause_evidence": [
                                {"clause_kind": "condition", "clause_index": 0, "source_row_id": "SRC-032", "exact_source_fragment": "Серия"},
                                {"clause_kind": "action", "clause_index": 0, "source_row_id": "SRC-032", "exact_source_fragment": "только 4 числовых символа"},
                                {"clause_kind": "oracle", "clause_index": 0, "source_row_id": "SRC-032", "exact_source_fragment": "трёх одинаковых цифр подряд"},
                            ],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-FMT",
                    "linked_atom_id": "ATOM-FMT",
                    "source_property_id": "none_required",
                    "planned_tc_id": "candidate:SO-NEG-004",
                    "check_type": "negative",
                    "test_data": "1234;1112",
                    "scope_obligation_ids": ["SO-NEG-004"],
                }
            ],
            "negative_oracles": [
                {
                    "decision": "candidate_tc_required",
                    "oracle_status": "ui-calibration-required",
                    "restriction_type": "format",
                    "negative_class": "three-identical-digits",
                    "scope_obligation_id": "SO-NEG-004",
                    "linked_atom_id": "ATOM-FMT",
                    "linked_obligation_id": "OBL-FMT",
                    "representative_invalid_value": "1112",
                    "source_statement": statement,
                }
            ],
            "dependency_bindings": [],
        }

        projection = _combined_calibration_allowed_class_projection(
            payload,
            context=context,
        )

        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual("1234", projection["positive_obligation"]["test_data"])
        self.assertEqual("positive", projection["positive_obligation"]["check_type"])
        self.assertEqual("1112", projection["negative_obligation"]["test_data"])
        self.assertNotIn(
            "1112",
            projection["positive_assertion"]["action_clauses"][0],
        )
        self.assertNotIn(
            "1234",
            projection["negative_assertion"]["action_clauses"][0],
        )

    def test_exact_length_projection_adds_concrete_n_minus_and_n_plus_candidates(
        self,
    ) -> None:
        source_text = (
            "Серия Да Да Поле ввода Текст BSR 85. Ограничение на формат: "
            "только 4 числовых символа. BSR 86. Не должно быть трех "
            "одинаковых цифр подряд"
        )
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-020",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-023",
                            "atom_id": "ATOM-023",
                            "obligation_ids": ["OBL-005"],
                            "semantic_disposition": "testable",
                            "polarity": "positive",
                            "risk": "high",
                            "condition_clauses": ["Поле отображается."],
                            "action_clauses": ["Ввести значение 1234."],
                            "oracle_clauses": ["Поле отображает «1234»."],
                            "requirement_codes": ["BSR 85"],
                            "requirement_code_evidence": [],
                            "clause_evidence": [
                                {
                                    "clause_kind": "condition",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-020",
                                    "exact_source_fragment": "Серия",
                                },
                                {
                                    "clause_kind": "action",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-020",
                                    "exact_source_fragment": "только 4 числовых символа",
                                },
                                {
                                    "clause_kind": "oracle",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-020",
                                    "exact_source_fragment": "только 4 числовых символа",
                                },
                            ],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "source_property_id": "none_required",
                            "field_or_block": "Серия",
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-005",
                    "package_id": "WP-01",
                    "linked_atom_id": "ATOM-023",
                    "source_property_id": "none_required",
                    "property_type": "format",
                    "obligation_class": "allowed-class",
                    "required_behavior": "Принять четыре цифры.",
                    "source_ref": "BSR 85",
                    "planned_tc_id": "TC-005",
                    "review_notes": "none_required",
                    "design_dimension": "boundary",
                    "planned_check": "Ввести 1234.",
                    "check_type": "positive",
                    "coverage_class": "requirement",
                    "input_class": "four-digits",
                    "single_expected_behavior": "1234 принято.",
                    "oracle_source": "BSR 85",
                    "test_data": "1234",
                    "dictionary_refs": [],
                    "dictionary_coverage": "none_required",
                    "scope_obligation_ids": [],
                }
            ],
            "applicability": [
                {
                    "dimension": "traceability",
                    "applicable": "yes",
                    "linked_atoms": ["ATOM-023"],
                    "linked_test_cases": ["TC-005"],
                },
                {
                    "dimension": "boundary",
                    "applicable": "yes",
                    "linked_atoms": ["ATOM-023"],
                    "linked_test_cases": ["TC-005"],
                },
            ],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-020",
                    "field_or_action": "Серия текущего паспорта",
                    "bounded_source_text": source_text,
                }
            ]
        }

        repairs = _materialize_missing_exact_length_boundaries(payload, context)

        assertions = payload["source_designs"][0]["assertions"]
        self.assertEqual(3, len(assertions))
        self.assertEqual(
            "Ввести значение «1234».",
            assertions[0]["action_clauses"][0],
        )
        self.assertEqual(
            ["123", "12340"],
            [payload["obligations"][index]["test_data"] for index in (1, 2)],
        )
        self.assertTrue(
            all(
                item["obligation_class"] == "candidate-ui-calibration"
                and item["oracle_source"] == "not_found"
                and item["scope_obligation_ids"] == []
                for item in payload["obligations"][1:]
            )
        )
        self.assertTrue(
            all(
                "фильтрация, сообщение, очистка и блокировка перехода не утверждаются"
                in item["oracle_clauses"][0]
                for item in assertions[1:]
            )
        )
        self.assertEqual(
            ["N-1", "N+1"],
            next(
                item["added_classes"]
                for item in repairs
                if item["rule"]
                == "materialize-exact-length-boundary-candidates"
            ),
        )
        self.assertEqual(
            3,
            len(payload["applicability"][1]["linked_atoms"]),
        )

        repeated = _materialize_missing_exact_length_boundaries(payload, context)
        self.assertEqual([], repeated)
        self.assertEqual(3, len(payload["source_designs"][0]["assertions"]))

    def test_phone_exact_length_projects_concrete_mask_and_separate_default(self) -> None:
        template_fragment = (
            "BSR 273. По умолчанию стоит шаблон с кодом страны "
            "«+7(xxx)-xxx-xx-xx»"
        )
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-024",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-032",
                            "atom_id": "ATOM-032",
                            "obligation_ids": ["OBL-015"],
                            "semantic_disposition": "testable",
                            "polarity": "positive",
                            "risk": "medium",
                            "condition_clauses": ["Поле отображается."],
                            "action_clauses": ["Ввести «9991234567»."],
                            "oracle_clauses": [
                                "Поле содержит значение в шаблоне «+7(xxx)-xxx-xx-xx»."
                            ],
                            "requirement_codes": ["BSR 272", "BSR 273"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 272",
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": (
                                        "BSR 272. Ограничение на формат: только 10 "
                                        "числовых символов."
                                    ),
                                },
                                {
                                    "requirement_code": "BSR 273",
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": template_fragment,
                                },
                            ],
                            "clause_evidence": [
                                {
                                    "clause_kind": "condition",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": "Рабочий телефон",
                                },
                                {
                                    "clause_kind": "action",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": "только 10 числовых символов",
                                },
                                {
                                    "clause_kind": "oracle",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": template_fragment,
                                },
                            ],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "source_property_id": "none_required",
                            "field_or_block": "Рабочий телефон",
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-015",
                    "package_id": "WP-01",
                    "linked_atom_id": "ATOM-032",
                    "source_property_id": "none_required",
                    "property_type": "format",
                    "obligation_class": "ui-behavior",
                    "required_behavior": "Принять десять цифр.",
                    "source_ref": "SRC-024",
                    "planned_tc_id": "TC-015",
                    "review_notes": "none_required",
                    "design_dimension": "boundary",
                    "planned_check": "Ввести десять цифр.",
                    "check_type": "positive",
                    "coverage_class": "requirements",
                    "input_class": "ten-digits",
                    "single_expected_behavior": "Номер принят в шаблоне.",
                    "oracle_source": "BSR 272-273",
                    "test_data": "9991234567",
                    "dictionary_refs": [],
                    "dictionary_coverage": "none_required",
                    "scope_obligation_ids": [],
                }
            ],
            "applicability": [
                {
                    "dimension": "traceability",
                    "applicable": "yes",
                    "linked_atoms": ["ATOM-032"],
                    "linked_test_cases": ["TC-015"],
                },
                {
                    "dimension": "boundary",
                    "applicable": "yes",
                    "linked_atoms": ["ATOM-032"],
                    "linked_test_cases": ["TC-015"],
                },
                {
                    "dimension": "accessibility-ui",
                    "applicable": "yes",
                    "linked_atoms": ["ATOM-032"],
                    "linked_test_cases": ["TC-015"],
                },
            ],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-024",
                    "field_or_action": "Рабочий телефон",
                    "bounded_source_text": (
                        "Рабочий телефон BSR 272. Ограничение на формат: только 10 "
                        f"числовых символов. {template_fragment}"
                    ),
                }
            ]
        }

        repairs = _materialize_missing_exact_length_boundaries(payload, context)

        assertions = payload["source_designs"][0]["assertions"]
        self.assertIn("+7(999)-123-45-67", assertions[0]["oracle_clauses"][0])
        template = next(
            item
            for item in assertions
            if item["assertion_id"] == "ASSERT-PHONE-TEMPLATE-SRC-024-1"
        )
        self.assertIn("+7(xxx)-xxx-xx-xx", template["oracle_clauses"][0])
        self.assertIn(
            "materialize-phone-default-template-chain",
            [item["rule"] for item in repairs],
        )
        self.assertEqual([], _materialize_missing_exact_length_boundaries(payload, context))

    def test_phone_mask_normalization_is_idempotent_and_keeps_exact_length_distinct(
        self,
    ) -> None:
        length_fragment = (
            "BSR 272. Ограничение на формат: только 10 числовых символов."
        )
        template_fragment = (
            "BSR 273. По умолчанию стоит шаблон с кодом страны "
            "«+7(xxx)-xxx-xx-xx»"
        )
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-024",
                    "requirement_codes": ["BSR 272", "BSR 273"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-EDIT",
                            "atom_id": "ATOM-EDIT",
                            "obligation_ids": ["OBL-EDIT"],
                            "semantic_disposition": "testable",
                            "polarity": "positive",
                            "condition_clauses": ["Поле отображается."],
                            "action_clauses": ["Ввести «9991234567»."],
                            "oracle_clauses": [
                                "Поле отображает телефон по шаблону."
                            ],
                            "requirement_codes": ["BSR 273"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 273",
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": template_fragment,
                                }
                            ],
                            "clause_evidence": [
                                {
                                    "clause_kind": "condition",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": "Рабочий телефон",
                                },
                                {
                                    "clause_kind": "action",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": "только 10 числовых символов",
                                },
                                {
                                    "clause_kind": "oracle",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": template_fragment,
                                },
                            ],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "source_property_id": (
                                "FP-SRC-024-EDITABILITY-EDITABLE"
                            ),
                            "field_or_block": "Рабочий телефон",
                        },
                        {
                            "assertion_id": "ASSERT-INVALID",
                            "atom_id": "ATOM-INVALID",
                            "obligation_ids": ["OBL-INVALID"],
                            "semantic_disposition": "testable",
                            "polarity": "negative",
                            "condition_clauses": ["Поле отображается."],
                            "action_clauses": ["Ввести «12345abcde»."],
                            "oracle_clauses": ["Значение не соответствует ограничению."],
                            "requirement_codes": ["BSR 272"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 272",
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": length_fragment,
                                }
                            ],
                            "clause_evidence": [],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "source_property_id": "none_required",
                            "field_or_block": "Рабочий телефон",
                        },
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-EDIT",
                    "linked_atom_id": "ATOM-EDIT",
                    "source_property_id": "FP-SRC-024-EDITABILITY-EDITABLE",
                    "property_type": "editability",
                    "required_behavior": "Номер отображается по шаблону.",
                    "planned_tc_id": "TC-EDIT",
                    "planned_check": "Ввести номер.",
                    "check_type": "positive",
                    "test_data": "9991234567",
                    "scope_obligation_ids": [],
                },
                {
                    "obligation_id": "OBL-INVALID",
                    "linked_atom_id": "ATOM-INVALID",
                    "source_property_id": "none_required",
                    "property_type": "format",
                    "required_behavior": "Нечисловое значение не соответствует ограничению.",
                    "planned_tc_id": "TC-INVALID",
                    "planned_check": "Ввести нечисловое значение.",
                    "check_type": "negative",
                    "test_data": "12345abcde",
                    "scope_obligation_ids": [],
                },
            ],
            "applicability": [],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-024",
                    "field_or_action": "Рабочий телефон",
                    "bounded_source_text": (
                        f"Рабочий телефон. {length_fragment} {template_fragment}"
                    ),
                }
            ]
        }

        first_repairs = _materialize_missing_exact_length_boundaries(
            payload,
            context,
        )
        assertions = payload["source_designs"][0]["assertions"]
        edit = next(item for item in assertions if item["assertion_id"] == "ASSERT-EDIT")
        exact = next(
            item
            for item in assertions
            if item["assertion_id"] == "ASSERT-XLB-SRC-024-1-EXACT"
        )
        self.assertEqual(["BSR 272", "BSR 273"], edit["requirement_codes"])
        self.assertEqual(
            ["BSR 272"],
            [
                item["requirement_code"]
                for item in exact["requirement_code_evidence"]
            ],
        )
        self.assertIn(
            "bind-phone-format-requirement-code-ownership",
            [item["rule"] for item in first_repairs],
        )
        self.assertNotIn("формате", exact["canonical_statement"].casefold())
        self.assertEqual([], _materialize_missing_exact_length_boundaries(payload, context))

        exact["canonical_statement"] = edit["canonical_statement"]
        exact["oracle_clauses"] = copy.deepcopy(edit["oracle_clauses"])
        exact_obligation = next(
            item
            for item in payload["obligations"]
            if item["obligation_id"] == exact["obligation_ids"][0]
        )
        exact_obligation["required_behavior"] = edit["oracle_clauses"][0]
        repair = _materialize_missing_exact_length_boundaries(payload, context)
        self.assertIn(
            "restore-distinct-phone-exact-length-chain",
            [item["rule"] for item in repair],
        )
        self.assertNotIn("формате", exact["canonical_statement"].casefold())

    def test_exact_length_projection_splits_n_from_typed_editability(self) -> None:
        statement = "BSR 272. Ограничение: только 10 числовых символов."
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-024",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-EDIT",
                            "atom_id": "ATOM-EDIT",
                            "obligation_ids": ["OBL-EDIT"],
                            "semantic_disposition": "testable",
                            "polarity": "positive",
                            "risk": "medium",
                            "condition_clauses": ["Поле доступно."],
                            "action_clauses": ["Ввести «9991234567»."],
                            "oracle_clauses": ["Значение отображается."],
                            "requirement_codes": [],
                            "requirement_code_evidence": [],
                            "clause_evidence": [
                                {
                                    "clause_kind": kind,
                                    "clause_index": 0,
                                    "source_row_id": "SRC-024",
                                    "exact_source_fragment": (
                                        "только 10 числовых символов"
                                    ),
                                }
                                for kind in ("condition", "action", "oracle")
                            ],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "source_property_id": (
                                "FP-SRC-024-EDITABILITY-EDITABLE"
                            ),
                            "field_or_block": "Рабочий телефон",
                        },
                        {
                            "assertion_id": "ASSERT-INVALID",
                            "atom_id": "ATOM-INVALID",
                            "obligation_ids": ["OBL-INVALID"],
                            "semantic_disposition": "testable",
                            "polarity": "negative",
                            "requirement_codes": ["BSR 272"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 272",
                                    "source_row_id": "SRC-024",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": statement,
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                }
                            ],
                        },
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-EDIT",
                    "linked_atom_id": "ATOM-EDIT",
                    "source_property_id": (
                        "FP-SRC-024-EDITABILITY-EDITABLE"
                    ),
                    "planned_tc_id": "TC-EDIT",
                },
                {
                    "obligation_id": "OBL-INVALID",
                    "linked_atom_id": "ATOM-INVALID",
                    "source_property_id": "none_required",
                    "planned_tc_id": "TC-INVALID",
                },
            ],
            "applicability": [
                {
                    "dimension": dimension,
                    "applicable": "yes",
                    "linked_atoms": ["ATOM-EDIT"],
                    "linked_test_cases": ["TC-EDIT"],
                }
                for dimension in ("traceability", "boundary")
            ],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-024",
                    "field_or_action": "Рабочий телефон",
                    "bounded_source_text": f"Рабочий телефон. {statement}",
                }
            ]
        }

        repairs = _materialize_missing_exact_length_boundaries(payload, context)

        added = payload["source_designs"][0]["assertions"][2:]
        self.assertEqual(3, len(added))
        self.assertEqual(
            ["N:9991234567", "N-1:999123456", "N+1:99912345670"],
            [item["input_class"] for item in payload["obligations"][2:]],
        )
        self.assertTrue(
            all(item["source_property_id"] == "none_required" for item in added)
        )
        self.assertTrue(
            all(item["requirement_codes"] == ["BSR 272"] for item in added)
        )
        self.assertIn(
            "materialize-exact-length-positive-chain",
            [item["rule"] for item in repairs],
        )

    @classmethod
    def _boundary(cls) -> dict[str, object]:
        context = cls._context()
        return {
            "version": 2,
            "status": "ready",
            "blocking_reason": "none_required",
            "scope_summary": "Проверяются выбор статуса и очистка изменённого поля.",
            "scope_boundary": copy.deepcopy(context["scope_boundary"]),
            "source_decisions": [
                {
                    "source_row_id": "SRC-001",
                    "disposition": "context",
                    "requirement_codes": [],
                    "rationale": "Строка задаёт только контекст целевого раздела.",
                },
                {
                    "source_row_id": "SRC-002",
                    "disposition": "included",
                    "requirement_codes": ["BSR 1"],
                    "rationale": "Строка задаёт проверяемое поведение поля.",
                },
                {
                    "source_row_id": "SRC-003",
                    "disposition": "included",
                    "requirement_codes": ["BSR 2"],
                    "rationale": "Строка задаёт проверяемое действие очистки.",
                },
            ],
            "dependencies": [
                {
                    "dependency_id": "DEP-001",
                    "kind": "field",
                    "name": "Статус",
                    "source_row_ids": ["SRC-002"],
                    "resolution": "declared",
                    "target_source_row_ids": ["SRC-002"],
                    "exact_source_fragments": ["Поле «Статус»"],
                    "gap_ids": [],
                    "blocking": False,
                    "rationale": "Поле явно определено целевой строкой.",
                }
            ],
            "gaps": [],
            "mockup_locators": copy.deepcopy(context["mockup_locators"]),
        }

    @staticmethod
    def _assertion(
        *,
        assertion_id: str,
        atom_id: str,
        property_id: str,
        field: str,
        source_ref: str,
        codes: list[str],
        conditions: list[str],
        actions: list[str],
        oracles: list[str],
        obligation_ids: list[str],
        evidence: list[dict[str, object]],
        requirement_evidence: list[dict[str, object]],
    ) -> dict[str, object]:
        return {
            "assertion_id": assertion_id,
            "canonical_statement": f"Проверяемое утверждение {assertion_id}.",
            "polarity": "positive",
            "semantic_disposition": "testable",
            "execution_readiness": "ready",
            "execution_readiness_rationale": "none_required",
            "risk": "medium",
            "condition_clauses": conditions,
            "action_clauses": actions,
            "oracle_clauses": oracles,
            "requirement_codes": codes,
            "requirement_code_evidence": requirement_evidence,
            "clause_evidence": evidence,
            "supporting_source_bindings": [],
            "clarification_clause_bindings": [],
            "atom_id": atom_id,
            "obligation_ids": obligation_ids,
            "disposition_rationale": "none_required",
            "source_property_id": property_id,
            "field_or_block": field,
            "source_reference": source_ref,
        }

    @classmethod
    def _design(cls) -> dict[str, object]:
        context = cls._context()
        boundary = cls._boundary()
        context_assertion = {
            "assertion_id": "ASSERT-001",
            "canonical_statement": "Строка задаёт контекст раздела.",
            "polarity": "neutral",
            "semantic_disposition": "not-applicable",
            "execution_readiness": "not-applicable",
            "execution_readiness_rationale": "none_required",
            "risk": "low",
            "condition_clauses": [],
            "action_clauses": [],
            "oracle_clauses": [],
            "requirement_codes": [],
            "requirement_code_evidence": [],
            "clause_evidence": [],
            "supporting_source_bindings": [],
            "clarification_clause_bindings": [],
            "atom_id": "ATOM-001",
            "obligation_ids": [],
            "disposition_rationale": "Строка не содержит самостоятельного поведения системы.",
            "source_property_id": "PROP-001",
            "field_or_block": "Контекст раздела",
            "source_reference": "section 1",
        }
        status_assertion = cls._assertion(
            assertion_id="ASSERT-002",
            atom_id="ATOM-002",
            property_id="PROP-002",
            field="Статус",
            source_ref="BSR 1",
            codes=["BSR 1"],
            conditions=["Поле «Статус»"],
            actions=["При выборе значения"],
            oracles=["система сохраняет выбранное значение"],
            obligation_ids=["OBL-001"],
            requirement_evidence=[
                {
                    "requirement_code": "BSR 1",
                    "source_row_id": "SRC-002",
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": "BSR 1.",
                    "evidence_source_path": "none_required",
                    "evidence_locator": "none_required",
                }
            ],
            evidence=[
                {
                    "clause_kind": "condition",
                    "clause_index": 0,
                    "source_row_id": "SRC-002",
                    "exact_source_fragment": "Поле «Статус»",
                },
                {
                    "clause_kind": "action",
                    "clause_index": 0,
                    "source_row_id": "SRC-002",
                    "exact_source_fragment": "При выборе значения",
                },
                {
                    "clause_kind": "oracle",
                    "clause_index": 0,
                    "source_row_id": "SRC-002",
                    "exact_source_fragment": "система сохраняет выбранное значение",
                },
            ],
        )
        reset_assertion = cls._assertion(
            assertion_id="ASSERT-003",
            atom_id="ATOM-003",
            property_id="PROP-003",
            field="Очистить",
            source_ref="BSR 2",
            codes=["BSR 2"],
            conditions=["поле заполнено изменённым значением"],
            actions=["при нажатии кнопки «Очистить»"],
            oracles=["поле очищается и становится пустым"],
            obligation_ids=["OBL-002"],
            requirement_evidence=[
                {
                    "requirement_code": "BSR 2",
                    "source_row_id": "SRC-003",
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": "BSR 2.",
                    "evidence_source_path": "none_required",
                    "evidence_locator": "none_required",
                }
            ],
            evidence=[
                {
                    "clause_kind": "condition",
                    "clause_index": 0,
                    "source_row_id": "SRC-003",
                    "exact_source_fragment": "поле заполнено изменённым значением",
                },
                {
                    "clause_kind": "action",
                    "clause_index": 0,
                    "source_row_id": "SRC-003",
                    "exact_source_fragment": "при нажатии кнопки «Очистить»",
                },
                {
                    "clause_kind": "oracle",
                    "clause_index": 0,
                    "source_row_id": "SRC-003",
                    "exact_source_fragment": "поле очищается и становится пустым",
                },
            ],
        )
        obligations = [
            {
                "obligation_id": "OBL-001",
                "package_id": "WP-01",
                "linked_atom_id": "ATOM-002",
                "source_property_id": "PROP-002",
                "property_type": "dictionary-selection",
                "obligation_class": "positive",
                "required_behavior": "Выбранное значение сохраняется.",
                "source_ref": "BSR 1",
                "planned_tc_id": "TC-001",
                "review_notes": "none_required",
                "design_dimension": "equivalence",
                "planned_check": "Выбрать каждое значение справочника.",
                "check_type": "positive",
                "coverage_class": "dictionary",
                "input_class": "all active values",
                "single_expected_behavior": "Выбранное значение сохранено.",
                "oracle_source": "BSR 1",
                "test_data": "Активен; Неактивен",
                "dictionary_refs": ["DICT-001"],
                "dictionary_coverage": "all-leaf-values",
                "scope_obligation_ids": [],
            },
            {
                "obligation_id": "OBL-002",
                "package_id": "WP-01",
                "linked_atom_id": "ATOM-003",
                "source_property_id": "PROP-003",
                "property_type": "reset",
                "obligation_class": "clear",
                "required_behavior": "Изменённое поле становится пустым.",
                "source_ref": "BSR 2",
                "planned_tc_id": "TC-002",
                "review_notes": "none_required",
                "design_dimension": "status-lifecycle",
                "planned_check": "Очистить поле после изменения значения.",
                "check_type": "action-flow",
                "coverage_class": "reset",
                "input_class": "changed visible value",
                "single_expected_behavior": "Поле становится пустым.",
                "oracle_source": "BSR 2",
                "test_data": "Изменённое значение",
                "dictionary_refs": [],
                "dictionary_coverage": "none_required",
                "scope_obligation_ids": [],
            },
        ]
        applicability = []
        applicability_links = {
            "traceability": (["ATOM-002", "ATOM-003"], ["TC-001", "TC-002"]),
            "status-lifecycle": (["ATOM-003"], ["TC-002"]),
            "equivalence": (["ATOM-002"], ["TC-001"]),
        }
        for dimension in APPLICABILITY_DIMENSIONS:
            linked_atoms, linked_test_cases = applicability_links.get(
                dimension,
                ([], []),
            )
            applicable = bool(linked_test_cases)
            applicability.append(
                {
                    "dimension": dimension,
                    "applicable": "yes" if applicable else "no",
                    "source_ref": "BSR 1" if applicable else "none_required",
                    "reason": (
                        "Есть трассируемая проверка выбора значения."
                        if applicable
                        else "Изолированно неприменимо к выбранному scope."
                    ),
                    "linked_atoms": linked_atoms,
                    "linked_test_cases": linked_test_cases,
                }
            )
        return {
            "version": SEMANTIC_DESIGN_VERSION,
            "contract": SEMANTIC_DESIGN_CONTRACT,
            "status": "ready",
            "blocking_reason": "none_required",
            "prepared_context_sha256": prepared_context_sha256(context),
            "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
            "scope_summary": boundary["scope_summary"],
            "included": copy.deepcopy(boundary["scope_boundary"]["include"]),
            "excluded": copy.deepcopy(boundary["scope_boundary"]["exclude"]),
            "mockup_locators": copy.deepcopy(boundary["mockup_locators"]),
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "boundary_disposition": "context",
                    "requirement_codes": [],
                    "assertions": [context_assertion],
                },
                {
                    "source_row_id": "SRC-002",
                    "boundary_disposition": "included",
                    "requirement_codes": ["BSR 1"],
                    "assertions": [status_assertion],
                },
                {
                    "source_row_id": "SRC-003",
                    "boundary_disposition": "included",
                    "requirement_codes": ["BSR 2"],
                    "assertions": [reset_assertion],
                },
            ],
            "obligations": obligations,
            "reset_lifecycle_bindings": [
                {
                    "obligation_id": "OBL-002",
                    "binding_kind": "reset",
                    "initial_condition_index": 0,
                    "changed_state_setup": (
                        "Установить видимое значение, отличное от исходного."
                    ),
                    "pre_action_state_oracle": (
                        "Убедиться, что изменённое значение видно до очистки."
                    ),
                    "state_relation": "different-from-captured-initial",
                }
            ],
            "dependency_bindings": [
                {
                    "dependency_id": "DEP-001",
                    "kind": "field",
                    "name": "Статус",
                    "source_row_ids": ["SRC-002"],
                    "resolution": "declared",
                    "target_source_row_ids": ["SRC-002"],
                    "exact_source_fragments": ["Поле «Статус»"],
                    "gap_ids": [],
                    "blocking": False,
                    "rationale": "Поле явно определено целевой строкой.",
                    "semantic_disposition": "bound",
                    "linked_assertion_ids": ["ASSERT-002"],
                    "linked_atom_ids": ["ATOM-002"],
                    "linked_obligation_ids": ["OBL-001"],
                    "mapping_rationale": (
                        "Зависимость поля связана с полной цепочкой проверки выбора."
                    ),
                }
            ],
            "dictionaries": [
                {
                    "dictionary_id": "DICT-001",
                    "dictionary_name": "Статусы",
                    "source_row_ids": ["SRC-002"],
                    "source_file": "source/main.xhtml",
                    "source_location": "BSR 1",
                    "extraction_status": "extracted",
                    "active_values": ["Активен", "Неактивен"],
                    "archived_values": [],
                    "gap_id": "none_required",
                    "notes": "Полный перечень из подготовленного контекста.",
                }
            ],
            "negative_oracles": [],
            "requiredness_oracles": [],
            "applicability": applicability,
        }

    def _validate(self, design: dict[str, object]) -> dict[str, object]:
        return validate_semantic_design_binding(
            self._context(),
            self._boundary(),
            design,
        )

    def test_minimal_complete_design_is_verified(self) -> None:
        receipt = self._validate(self._design())
        self.assertEqual("verified", receipt["status"])
        self.assertEqual(3, receipt["assertion_count"])
        self.assertEqual(2, receipt["planned_test_case_count"])
        self.assertEqual(1, receipt["state_change_obligation_count"])
        self.assertEqual(1, receipt["reset_lifecycle_binding_count"])

    def test_required_context_dependency_covers_every_target_row(self) -> None:
        context = self._context()
        context["source_rows"][0]["context_relation_required"] = True
        context["expected_dependencies"] = [
            {
                "kind": "other",
                "name": "Контекст раздела",
                "source_row_ids": ["SRC-001"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-002", "SRC-003"],
                "exact_source_fragments": ["Раздел 1"],
            }
        ]
        self._bind_context(context)
        boundary = self._boundary()
        boundary["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "other",
                "name": "Контекст раздела",
                "source_row_ids": ["SRC-001"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-002", "SRC-003"],
                "exact_source_fragments": ["Раздел 1"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Контекст явно связан с обеими целевыми строками.",
            }
        )
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        binding = copy.deepcopy(design["dependency_bindings"][0])
        binding.update(copy.deepcopy(boundary["dependencies"][1]))
        binding["semantic_disposition"] = "bound"
        binding["linked_assertion_ids"] = ["ASSERT-002", "ASSERT-003"]
        binding["linked_atom_ids"] = ["ATOM-002", "ATOM-003"]
        binding["linked_obligation_ids"] = ["OBL-001", "OBL-002"]
        binding["mapping_rationale"] = (
            "Контекст связан с полными цепочками обеих целевых строк."
        )
        design["dependency_bindings"].append(binding)
        for source_design in design["source_designs"][1:]:
            source_design["assertions"][0]["supporting_source_bindings"] = [
                {
                    "source_row_id": "SRC-001",
                    "evidence_role": "constraint",
                    "exact_source_fragment": "Раздел 1",
                }
            ]

        receipt = validate_semantic_design_binding(context, boundary, design)
        self.assertEqual("verified", receipt["status"])

        binding["linked_assertion_ids"] = ["ASSERT-002"]
        binding["linked_atom_ids"] = ["ATOM-002"]
        binding["linked_obligation_ids"] = ["OBL-001"]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "context relation does not cover target rows: SRC-003",
        ):
            validate_semantic_design_binding(context, boundary, design)

    def test_signal_registry_keeps_lower_upper_and_feedback_atomic(self) -> None:
        registry = _source_signal_registry(
            [
                {
                    "source_row_id": "SRC-001",
                    "bounded_source_text": (
                        "BSR 7. Значение от 1 до 10. При ошибке отображается сообщение."
                    ),
                }
            ],
            {"SRC-001": ["BSR 7"]},
        )
        self.assertEqual(
            ["lower-bound", "upper-bound", "feedback"],
            [item["restriction_type"] for item in registry["negative"]],
        )

    def test_prompt_forbids_primary_row_as_supporting_evidence(self) -> None:
        context = self._context()
        boundary = self._boundary()
        prompt = " ".join(semantic_design_prompt(context, boundary, []).split())
        self.assertIn(
            "never repeat the enclosing source_design.source_row_id",
            prompt,
        )
        self.assertIn(
            "source-context clarification that makes rows explicitly out-of-project",
            prompt,
        )
        self.assertIn("canonical clarification_clause_binding", prompt)
        self.assertIn("clause_kind=canonical is forbidden", prompt)
        self.assertIn(
            "Never copy an approved clarification answer into condition/action/oracle text",
            prompt,
        )
        self.assertIn("semantic_output_cardinality", prompt)
        self.assertIn("one generic assertion per source row is an invalid", prompt.lower())
        self.assertIn(
            "preserve a separate positive allowed-class ASSERT/ATOM/OBL/TC",
            prompt,
        )
        self.assertIn(
            "it is not replaced by an editability, visibility, requiredness or dependency check",
            prompt,
        )
        self.assertIn(
            "a direct vendor API request alone does not test that product field",
            prompt,
        )
        self.assertIn("not-A+B and A+not-B", prompt)
        self.assertIn("Do not claim the full only-if rule", prompt)
        self.assertIn("Видимость: Да, если A И если B", prompt)
        self.assertIn("For conditional visibility, the action sets the named trigger", prompt)
        self.assertIn("Never use requirement prose, table metadata", prompt)
        self.assertIn("Action and oracle clauses must never be textually identical", prompt)

    def test_testable_action_cannot_duplicate_observable_oracle(self) -> None:
        assertion = {
            "assertion_id": "ASSERT-RESULT-AS-ACTION",
            "semantic_disposition": "testable",
            "action_clauses": ["Адрес раскладывается по полям ручного ввода."],
            "oracle_clauses": ["Адрес раскладывается по полям ручного ввода."],
        }
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "action must name a trigger",
        ):
            _validate_distinct_action_oracle_clauses(assertion)
        assertion["action_clauses"] = [
            "Выбрать адрес из подсказок DaData в поле адреса клиента."
        ]
        _validate_distinct_action_oracle_clauses(assertion)

    def test_derived_negative_control_reuses_full_literal_rule_as_evidence(self) -> None:
        full_rule = "BSR 9. Эффект отображается только если признак = «Нет»."
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-009",
                    "bounded_source_text": full_rule,
                }
            ]
        }
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-009",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-NEG",
                            "semantic_disposition": "testable",
                            "polarity": "negative",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 9",
                                    "source_row_id": "SRC-009",
                                    "exact_source_fragment": full_rule,
                                }
                            ],
                            "clause_evidence": [
                                {
                                    "clause_kind": "condition",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-009",
                                    "exact_source_fragment": "признак = «Да»",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        projections = _necessary_control_missing_clause_evidence_projections(
            payload,
            context,
        )
        self.assertEqual(1, len(projections))
        self.assertEqual(
            full_rule,
            projections[0]["canonical_evidence"][0]["exact_source_fragment"],
        )

    def test_conjunctive_visibility_requires_one_negative_control_per_conjunct(
        self,
    ) -> None:
        fragment = (
            "BSR 146. Видимость: Да, если признак совпадения = «Нет» "
            "И если квартира не указана"
        )
        self.assertEqual(
            2,
            _required_necessary_condition_negative_controls(fragment),
        )
        self.assertEqual(
            1,
            _required_necessary_condition_negative_controls(
                "BSR 135. Отображается только если квартира не указана."
            ),
        )
        self.assertEqual(
            0,
            _required_necessary_condition_negative_controls(
                "BSR 123. Видимость: Да, если ручной ввод = «Да»."
            ),
        )

        def assertion(assertion_id: str, polarity: str) -> dict[str, object]:
            return {
                "assertion_id": assertion_id,
                "semantic_disposition": "testable",
                "polarity": polarity,
                "condition_clauses": [f"Состояние {assertion_id}"],
                "requirement_codes": ["BSR 146"],
                "requirement_code_evidence": [
                    {
                        "requirement_code": "BSR 146",
                        "exact_source_fragment": fragment,
                    }
                ],
            }

        assertions = [
            assertion("ASSERT-POS", "positive"),
            assertion("ASSERT-NEG-A", "negative"),
            assertion("ASSERT-NEG-B", "negative"),
        ]
        _validate_necessary_condition_control_cardinality("SRC-033", assertions)
        duplicated_conditions = copy.deepcopy(assertions)
        duplicated_conditions[1]["condition_clauses"] = copy.deepcopy(
            duplicated_conditions[0]["condition_clauses"]
        )
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "require distinct condition states",
        ):
            _validate_necessary_condition_control_cardinality(
                "SRC-033",
                duplicated_conditions,
            )
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "requires one positive assertion and 2 distinct negative control",
        ):
            _validate_necessary_condition_control_cardinality(
                "SRC-033",
                assertions[:-1],
            )

    def test_negative_business_case_keeps_polarity_with_service_outage_control(
        self,
    ) -> None:
        fragment = (
            "BSR 266. В случае, если организация является не действующей, Система "
            "отображает подсказку красным цветом «Организация не является "
            "действующей» и блокирует кнопку «Далее». Проверка должна действовать "
            "только если сервис DaData доступен"
        )
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-021",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-021-BSR",
                            "canonical_statement": "Недействующая организация блокируется.",
                            "polarity": "negative",
                            "semantic_disposition": "testable",
                            "execution_readiness": "ready",
                            "execution_readiness_rationale": "none_required",
                            "risk": "high",
                            "condition_clauses": [
                                "Социальный статус заполнен; сервис DaData доступен."
                            ],
                            "action_clauses": [
                                "В поле «Наименование организации, ИНН» ввести запрос "
                                "«7733073764» и выбрать точное предложение fixture."
                            ],
                            "oracle_clauses": [
                                "Показана подсказка «Организация не является действующей»; "
                                "кнопка «Далее» заблокирована."
                            ],
                            "requirement_codes": ["BSR 266"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 266",
                                    "source_row_id": "SRC-021",
                                    "exact_source_fragment": fragment,
                                }
                            ],
                            "clause_evidence": [],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "atom_id": "ATOM-SRC-021-BSR",
                            "obligation_ids": ["OBL-SRC-021-BSR"],
                            "disposition_rationale": "Проверяется наблюдаемый результат.",
                            "source_property_id": "none_required",
                            "field_or_block": "Наименование организации, ИНН",
                            "source_reference": "SRC-021",
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-SRC-021-BSR",
                    "package_id": "WP-01",
                    "linked_atom_id": "ATOM-SRC-021-BSR",
                    "source_property_id": "none_required",
                    "property_type": "integration-visible-behavior",
                    "obligation_class": "integration-action-flow",
                    "required_behavior": "Показать предупреждение.",
                    "source_ref": "SRC-021",
                    "planned_tc_id": "TC-SRC-021-BSR",
                    "review_notes": "none_required",
                    "design_dimension": "integration",
                    "planned_check": "Выбрать fixture.",
                    "check_type": "negative",
                    "coverage_class": "dadata-liquidated",
                    "input_class": "registered-fixture",
                    "single_expected_behavior": "Предупреждение и блокировка.",
                    "oracle_source": "BSR 266",
                    "test_data": "fixture; query=7733073764",
                    "dictionary_refs": [],
                    "dictionary_coverage": "none_required",
                    "scope_obligation_ids": [],
                }
            ],
        }

        repairs = _materialize_service_availability_necessary_controls(payload)

        self.assertEqual(1, len(repairs))
        assertions = payload["source_designs"][0]["assertions"]
        self.assertEqual("negative", assertions[0]["polarity"])
        self.assertEqual(2, len(assertions))
        self.assertIn("DaData недоступен", assertions[1]["condition_clauses"][0])
        self.assertEqual(
            "В поле «Наименование организации, ИНН» ввести запрос «7733073764».",
            assertions[1]["action_clauses"][0],
        )
        self.assertIn("не отображается", assertions[1]["oracle_clauses"][0])
        self.assertEqual(2, len(payload["obligations"]))
        _validate_necessary_condition_control_cardinality("SRC-021", assertions)
        self.assertEqual([], _materialize_service_availability_necessary_controls(payload))

    def test_unobservable_executable_requiredness_is_downgraded_to_candidate(
        self,
    ) -> None:
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-032",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-REQ",
                            "atom_id": "ATOM-REQ",
                            "polarity": "negative",
                            "semantic_disposition": "testable",
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-REQ",
                    "linked_atom_id": "ATOM-REQ",
                    "check_type": "negative",
                    "test_data": "Регион отсутствует; номер дома 1",
                }
            ],
            "requiredness_oracles": [
                {
                    "scope_obligation_id": "SO-REQ-002",
                    "linked_atom_id": "ATOM-REQ",
                    "linked_obligation_id": "OBL-REQ",
                    "field_or_block": "регион",
                    "restriction_type": "requiredness",
                    "marker_oracle_found": "no",
                    "empty_value_oracle_found": "partial",
                    "oracle_status": "source-backed",
                    "decision": "executable_tc",
                    "gap_id": "none_required",
                }
            ],
        }
        projections = _unsupported_executable_requiredness_candidate_projections(
            payload
        )
        self.assertEqual(1, len(projections))
        self.assertEqual(
            "candidate_tc_required",
            projections[0]["oracle_fields"]["decision"],
        )
        self.assertEqual(
            "not_found",
            projections[0]["obligation_fields"]["oracle_source"],
        )
        self.assertIn(
            "candidate-ui-calibration",
            projections[0]["oracle_fields"]["calibration_notes"],
        )
        self.assertEqual(
            "partial",
            projections[0]["oracle_fields"]["empty_value_oracle_found"],
        )

    def test_compound_requiredness_cannot_self_promote_without_visible_oracle(
        self,
    ) -> None:
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-032",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-REQ",
                            "atom_id": "ATOM-REQ",
                            "polarity": "negative",
                            "semantic_disposition": "testable",
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-REQ",
                    "linked_atom_id": "ATOM-REQ",
                    "check_type": "negative",
                    "test_data": "Регион отсутствует; номер дома 1",
                }
            ],
            "requiredness_oracles": [
                {
                    "signal_id": "SIG-REQ-002",
                    "scope_obligation_id": "SO-REQ-002",
                    "linked_atom_id": "ATOM-REQ",
                    "linked_obligation_id": "OBL-REQ",
                    "field_or_block": "регион",
                    "restriction_type": "requiredness",
                    "marker_oracle_found": "no",
                    "empty_value_oracle_found": "yes",
                    "oracle_status": "source-backed",
                    "decision": "executable_tc",
                    "gap_id": "none_required",
                }
            ],
        }
        source_only_requiredness = {
            "SO-REQ-002": {
                "scope_obligation_id": "SO-REQ-002",
                "source_binding": "compound-text-requirement",
                "requiredness_source": (
                    "Правило: обязательно должны быть введены регион и номер дома."
                ),
            }
        }
        projections = _unsupported_executable_requiredness_candidate_projections(
            payload,
            expected_signals_by_scope=source_only_requiredness,
        )
        self.assertEqual(1, len(projections))
        self.assertTrue(projections[0]["source_requires_calibration"])
        self.assertEqual(
            "candidate_tc_required",
            projections[0]["oracle_fields"]["decision"],
        )
        self.assertEqual(
            "partial",
            projections[0]["oracle_fields"]["empty_value_oracle_found"],
        )

        explicit_rejection = copy.deepcopy(source_only_requiredness)
        explicit_rejection["SO-REQ-002"]["requiredness_source"] = (
            "Регион обязателен; без региона адрес не сохраняется."
        )
        self.assertEqual(
            [],
            _unsupported_executable_requiredness_candidate_projections(
                payload,
                expected_signals_by_scope=explicit_rejection,
            ),
        )

    def test_v5_requirement_code_canonical_binding_is_excluded_from_transport(
        self,
    ) -> None:
        clarifications = [
            {
                "clarification_id": "CLR-ADDR-001",
                "binding_scope": "requirement-code",
                "requirement_codes": ["BSR 118", "BSR 119"],
                "source_row_ids": [],
            }
        ]
        self.assertFalse(
            semantic_design_allows_canonical_transport_binding(clarifications)
        )
        schema = semantic_design_output_schema(
            ["SRC-001", "SRC-002", "SRC-003"],
            allow_canonical_clarification_binding=False,
        )
        schema.pop("$schema")
        design = self._design()
        binding = {
            "clarification_id": "CLR-ADDR-001",
            "clause_kind": "canonical",
            "clause_index": 0,
            "requirement_codes": ["BSR 118", "BSR 119"],
            "exact_answer_sha256": (
                "3e8fd538a5085798d257df76e5842ffe9007ccbf3274dbcaa9ea24058a7486f9"
            ),
            "binding_scope": "requirement-code",
            "source_row_ids": [],
        }
        assertion = design["source_designs"][1]["assertions"][0]
        assertion["clarification_clause_bindings"] = [binding]

        with self.assertRaises(OpenAIStrictOutputInstanceError):
            validate_openai_strict_output_instance(design, schema)
        diagnostics = semantic_design_transport_diagnostics(design)
        self.assertIn(
            "clarification-canonical-binding-scope-invalid",
            [item["code"] for item in diagnostics["findings"]],
        )

        binding["clause_kind"] = "oracle"
        validate_openai_strict_output_instance(design, schema)

    def test_source_context_clarification_keeps_canonical_transport_slot(self) -> None:
        self.assertTrue(
            semantic_design_allows_canonical_transport_binding(
                [
                    {
                        "clarification_id": "CLR-CONTEXT-001",
                        "binding_scope": "source-context",
                        "requirement_codes": [],
                        "source_row_ids": ["SRC-001"],
                    }
                ]
            )
        )

    def test_transport_normalizer_repairs_only_provable_provenance_noise(self) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "semantic_disposition": "not-applicable",
                            "condition_clauses": [],
                            "action_clauses": [],
                            "oracle_clauses": [],
                            "obligation_ids": [],
                            "supporting_source_bindings": [
                                {"source_row_id": "SRC-001", "evidence_role": "definition"}
                            ],
                            "requirement_code_evidence": [
                                {
                                    "provenance_role": "xhtml-row",
                                    "evidence_source_path": "wrong.pdf",
                                    "evidence_locator": "page:1",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        normalized, receipt = normalize_semantic_design_transport(raw)
        assertion = normalized["source_designs"][0]["assertions"][0]
        self.assertEqual([], assertion["supporting_source_bindings"])
        evidence = assertion["requirement_code_evidence"][0]
        self.assertEqual("none_required", evidence["evidence_source_path"])
        self.assertEqual("none_required", evidence["evidence_locator"])
        self.assertEqual(3, receipt["repair_count"])
        original_evidence = raw["source_designs"][0]["assertions"][0][
            "requirement_code_evidence"
        ][0]
        self.assertEqual("wrong.pdf", original_evidence["evidence_source_path"])

    def test_transport_normalizer_recovers_v12_repeated_requirement_code_span(
        self,
    ) -> None:
        source_text = (
            "BSR 142. Правило: обязательно должны быть введены регион и номер дома. "
            "Если в адресе не указана квартира, поле подсвечивается красным и "
            "отображается подсказка: «Укажите номер квартиры или поставьте отметку "
            "о проживании в частном доме». BSR 143. Следующее требование."
        )
        fabricated = (
            "BSR 142. Если в адресе не указана квартира, поле подсвечивается "
            "красным и отображается подсказка: «Укажите номер квартиры или "
            "поставьте отметку о проживании в частном доме»."
        )
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-032",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-032-142-A",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 142",
                                    "source_row_id": "SRC-032",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": fabricated,
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-032",
                    "bounded_source_text": source_text,
                    "requirement_codes_hint": ["BSR 142", "BSR 143"],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        evidence = normalized["source_designs"][0]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"]
        self.assertEqual(
            source_text[: source_text.index(" BSR 143")],
            evidence,
        )
        self.assertIn(evidence, source_text)
        self.assertIn("BSR 142", evidence)
        self.assertEqual(fabricated, raw["source_designs"][0]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"])
        self.assertIn(
            "expand-repeated-requirement-code-to-literal-source-span",
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_leaves_ambiguous_repeated_code_evidence_blocking(
        self,
    ) -> None:
        body = "Если условие выполнено, отображается предупреждение."
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-010",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-010",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 10",
                                    "source_row_id": "SRC-010",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": f"BSR 10. {body}",
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-010",
                    "bounded_source_text": f"BSR 10. {body} Повтор: {body}",
                    "requirement_codes_hint": ["BSR 10"],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        self.assertEqual(raw, normalized)
        self.assertNotIn(
            "expand-repeated-requirement-code-to-literal-source-span",
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_expands_one_omitted_requirement_branch(self) -> None:
        source_text = (
            "BSR 100. Проверка срока: - До 14 лет — отказ. "
            "- От 14 лет — до 20 лет + 90 дней. "
            "- От 20 лет — до 45 лет + 90 дней. "
            "BSR 101. Дата не позже текущей."
        )
        fabricated = (
            "BSR 100. Проверка срока: - От 20 лет — до 45 лет "
            "+ 90 дней."
        )
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-026",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-026-EXP45",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 100",
                                    "source_row_id": "SRC-026",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": fabricated,
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-026",
                    "bounded_source_text": source_text,
                    "requirement_codes_hint": ["BSR 100", "BSR 101"],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        evidence = normalized["source_designs"][0]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"]
        self.assertEqual(source_text[: source_text.index(" BSR 101")], evidence)
        self.assertIn(evidence, source_text)
        self.assertIn(
            "expand-repeated-requirement-code-to-literal-source-span",
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_does_not_hide_testable_self_support(self) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "semantic_disposition": "testable",
                            "condition_clauses": ["condition"],
                            "action_clauses": ["action"],
                            "oracle_clauses": ["oracle"],
                            "obligation_ids": ["OBL-001"],
                            "supporting_source_bindings": [
                                {"source_row_id": "SRC-001", "evidence_role": "constraint"}
                            ],
                            "requirement_code_evidence": [],
                        }
                    ],
                }
            ]
        }
        normalized, receipt = normalize_semantic_design_transport(raw)
        self.assertEqual(
            raw["source_designs"][0]["assertions"][0]["supporting_source_bindings"],
            normalized["source_designs"][0]["assertions"][0][
                "supporting_source_bindings"
            ],
        )
        self.assertEqual(0, receipt["repair_count"])

    def test_transport_normalizer_rebinds_scope_exclusion_to_literal_visible_oracle(
        self,
    ) -> None:
        answer = "Внутреннее поле проверяется отдельно и исключено из проекта."
        context = {
            "approved_clarifications": [
                {
                    "clarification_id": "CLR-001",
                    "requirement_codes": ["BSR 7"],
                    "exact_answer": answer,
                }
            ],
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "bounded_source_text": (
                        "BSR 7. Если адрес выбран через DaData, то он раскладывается "
                        "по видимым полям, во внутренней модели заполняется код."
                    ),
                }
            ],
        }
        boundary = {
            "dependencies": [
                {
                    "resolution": "scope-excluded",
                    "source_row_ids": ["SRC-001"],
                }
            ]
        }
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-001",
                            "semantic_disposition": "testable",
                            "requirement_codes": ["BSR 7"],
                            "action_clauses": [
                                "то он раскладывается по видимым полям"
                            ],
                            "oracle_clauses": [answer],
                            "clause_evidence": [
                                {
                                    "clause_kind": "action",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-001",
                                    "exact_source_fragment": (
                                        "то он раскладывается по видимым полям"
                                    ),
                                },
                                {
                                    "clause_kind": "oracle",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-001",
                                    "exact_source_fragment": answer,
                                },
                            ],
                            "clarification_clause_bindings": [
                                {
                                    "clarification_id": "CLR-001",
                                    "binding_scope": "requirement-code",
                                    "clause_kind": "oracle",
                                    "clause_index": 0,
                                    "requirement_codes": ["BSR 7"],
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        projections = _clarification_exclusion_oracle_projections(
            raw,
            context,
            boundary,
        )

        self.assertEqual(1, len(projections))
        projection = projections[0]
        self.assertEqual(
            "то он раскладывается по видимым полям",
            projection["canonical_oracle"],
        )
        self.assertEqual(
            "то он раскладывается по видимым полям",
            projection["canonical_evidence"],
        )

    def test_transport_header_projection_rebinds_only_copy_fields(self) -> None:
        context = self._context()
        boundary = self._boundary()
        raw = self._design()
        raw["prepared_context_sha256"] = "0" * 64
        raw["scope_boundary_decision_sha256"] = "1" * 64
        raw["scope_summary"] = "stale"
        raw["included"] = ["stale"]
        raw["excluded"] = ["stale"]

        projection = _semantic_transport_header_projection(raw, context, boundary)

        self.assertIsNotNone(projection)
        self.assertEqual(
            {
                "prepared_context_sha256",
                "scope_boundary_decision_sha256",
                "scope_summary",
                "included",
                "excluded",
            },
            set(projection["changed_fields"]),
        )
        self.assertEqual(
            boundary["scope_summary"],
            projection["expected"]["scope_summary"],
        )
        self.assertEqual(
            boundary["scope_boundary"]["include"],
            projection["expected"]["included"],
        )

    def test_dependency_transport_projection_preserves_semantic_links(self) -> None:
        boundary = self._boundary()
        raw = self._design()
        binding = raw["dependency_bindings"][0]
        binding["rationale"] = "stale rationale"
        binding["resolution"] = "missing"
        original_links = list(binding["linked_assertion_ids"])

        projections = _dependency_transport_projections(raw, boundary)

        self.assertEqual(1, len(projections))
        projection = projections[0]
        self.assertEqual(
            {"rationale", "resolution"},
            set(projection["changed_fields"]),
        )
        self.assertNotIn("linked_assertion_ids", projection["canonical_fields"])
        self.assertEqual(original_links, binding["linked_assertion_ids"])

    def test_missing_scope_excluded_dependency_is_synthesized_without_links(self) -> None:
        boundary = self._boundary()
        boundary["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "other",
                "name": "internal-code",
                "source_row_ids": ["SRC-003"],
                "resolution": "scope-excluded",
                "target_source_row_ids": [],
                "exact_source_fragments": ["поле очищается"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Внутренняя проверка исключена подтверждённой границей scope.",
            }
        )
        raw = self._design()

        projection = _missing_scope_excluded_dependency_projection(raw, boundary)

        self.assertIsNotNone(projection)
        self.assertEqual(["DEP-002"], projection["missing_dependency_ids"])
        synthesized = projection["canonical_bindings"][1]
        self.assertEqual("not-applicable", synthesized["semantic_disposition"])
        self.assertEqual([], synthesized["linked_assertion_ids"])
        self.assertEqual([], synthesized["linked_atom_ids"])
        self.assertEqual([], synthesized["linked_obligation_ids"])

    def test_strict_schema_counts_synthesized_scope_excluded_dependency(self) -> None:
        context = self._context()
        boundary = self._boundary()
        boundary["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "other",
                "name": "internal-code",
                "source_row_ids": ["SRC-003"],
                "resolution": "scope-excluded",
                "target_source_row_ids": [],
                "exact_source_fragments": ["поле очищается"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Внутренняя проверка исключена подтверждённой границей scope.",
            }
        )
        raw = self._design()
        projection = _missing_scope_excluded_dependency_projection(raw, boundary)
        self.assertIsNotNone(projection)
        normalized = copy.deepcopy(raw)
        normalized["dependency_bindings"] = projection["canonical_bindings"]
        schema = semantic_design_output_schema(
            ["SRC-001", "SRC-002", "SRC-003"],
            require_ready=True,
            expected_dependency_count=len(boundary["dependencies"]),
        )
        schema.pop("$schema")
        validate_openai_strict_output_instance(normalized, schema)

    def test_scope_excluded_dependency_drops_only_matching_na_links(self) -> None:
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-NA-001",
                            "atom_id": "ATOM-NA-001",
                            "canonical_statement": (
                                "В модели должно заполняться поле kladr (код КЛАДР)."
                            ),
                            "semantic_disposition": "not-applicable",
                            "requirement_codes": [],
                            "obligation_ids": [],
                            "field_or_block": "kladr",
                        }
                    ],
                }
            ]
        }
        binding = {
            "resolution": "scope-excluded",
            "semantic_disposition": "not-applicable",
            "name": "kladr",
            "source_row_ids": ["SRC-001"],
            "exact_source_fragments": ["поле kladr (код КЛАДР)"],
            "linked_assertion_ids": ["ASSERT-NA-001"],
            "linked_atom_ids": ["ATOM-NA-001"],
            "linked_obligation_ids": [],
        }
        projection = _scope_excluded_na_link_projection(payload, binding)
        self.assertIsNotNone(projection)
        self.assertEqual([], projection["linked_assertion_ids"])
        self.assertEqual([], projection["linked_atom_ids"])

        payload["source_designs"][0]["assertions"][0][
            "semantic_disposition"
        ] = "testable"
        self.assertIsNone(_scope_excluded_na_link_projection(payload, binding))

    def test_included_row_scope_exclusion_requires_code_less_na_sibling(self) -> None:
        context = self._context()
        context["expected_dependencies"] = [
            {
                "kind": "other",
                "name": "internal-code",
                "source_row_ids": ["SRC-003"],
                "resolution": "scope-excluded",
                "target_source_row_ids": [],
                "exact_source_fragments": ["поле очищается"],
            }
        ]
        context["scope_boundary"]["exclude"].append("internal-code")
        self._bind_context(context)
        boundary = self._boundary()
        boundary["scope_boundary"]["exclude"].append("internal-code")
        boundary["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "other",
                "name": "internal-code",
                "source_row_ids": ["SRC-003"],
                "resolution": "scope-excluded",
                "target_source_row_ids": [],
                "exact_source_fragments": ["поле очищается"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Внутренняя проверка исключена подтверждённой границей scope.",
            }
        )
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["scope_boundary_decision_sha256"] = canonical_payload_sha256(boundary)
        design["excluded"] = copy.deepcopy(boundary["scope_boundary"]["exclude"])
        design["dependency_bindings"].append(
            {
                **copy.deepcopy(boundary["dependencies"][-1]),
                "semantic_disposition": "not-applicable",
                "linked_assertion_ids": [],
                "linked_atom_ids": [],
                "linked_obligation_ids": [],
                "mapping_rationale": (
                    "Внутренняя проверка исключена подтверждённой границей scope."
                ),
            }
        )

        diagnostics = semantic_design_completeness_diagnostics(
            context,
            boundary,
            design,
        )
        self.assertIn(
            "not-applicable-assertion-cardinality-shortfall",
            [item["code"] for item in diagnostics["findings"]],
        )

        design["source_designs"][2]["assertions"].append(
            {
                "assertion_id": "ASSERT-NA-003",
                "canonical_statement": (
                    "Внутренний эффект «поле очищается» исключён из текущего проекта."
                ),
                "polarity": "neutral",
                "semantic_disposition": "not-applicable",
                "execution_readiness": "not-applicable",
                "execution_readiness_rationale": "none_required",
                "risk": "low",
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "requirement_codes": [],
                "requirement_code_evidence": [],
                "clause_evidence": [],
                "supporting_source_bindings": [],
                "clarification_clause_bindings": [],
                "atom_id": "ATOM-NA-003",
                "obligation_ids": [],
                "disposition_rationale": (
                    "Эффект относится к отдельной внутренней проверке и не исполняется."
                ),
                "source_property_id": "none_required",
                "field_or_block": "internal-code",
                "source_reference": "BSR 2",
            }
        )
        receipt = validate_semantic_design_binding(context, boundary, design)
        self.assertEqual("verified", receipt["status"])

        design["source_designs"][2]["assertions"][0][
            "field_or_block"
        ] = "Очистить и записать internal-code"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "scope-excluded name leaked into testable field_or_block",
        ):
            validate_semantic_design_binding(context, boundary, design)

    def test_transport_normalizer_makes_empty_non_property_chain_explicit(self) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-001",
                            "atom_id": "ATOM-001",
                            "source_property_id": "",
                            "requirement_code_evidence": [],
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-001",
                    "linked_atom_id": "ATOM-001",
                    "source_property_id": "",
                }
            ],
        }

        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertEqual(
            "none_required",
            normalized["source_designs"][0]["assertions"][0][
                "source_property_id"
            ],
        )
        self.assertEqual(
            "none_required",
            normalized["obligations"][0]["source_property_id"],
        )
        self.assertEqual(
            {
                "make-non-property-assertion-explicit",
                "make-non-property-obligation-explicit",
            },
            {item["rule"] for item in receipt["repairs"]},
        )

    def test_always_visibility_requires_two_distinct_prestate_chains(self) -> None:
        assertion = {
            "assertion_id": "ASSERT-ALWAYS-001",
            "semantic_disposition": "testable",
            "condition_clauses": ["Default state"],
            "action_clauses": ["Observe the field"],
            "oracle_clauses": ["The field is visible"],
        }
        evidence = [
            {"exact_source_fragment": "BSR 1. Видимость-всегда."}
        ]

        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "two distinct source-backed pre-state chains",
        ):
            _validate_always_visibility_prestate_cardinality(assertion, evidence)

        assertion["condition_clauses"].append("Changed state")
        assertion["action_clauses"].append("Observe the field after the change")
        assertion["oracle_clauses"].append("The field remains visible")
        _validate_always_visibility_prestate_cardinality(assertion, evidence)

    def test_always_visibility_allows_same_oracle_in_distinct_prestates(self) -> None:
        assertion = {
            "assertion_id": "ASSERT-ALWAYS-DEPENDENCY",
            "semantic_disposition": "testable",
            "condition_clauses": [
                "Дата выдачи текущего паспорта менее трёх лет назад.",
                "Дата выдачи текущего паспорта не менее трёх лет назад.",
            ],
            "action_clauses": ["Открыть блок.", "Открыть блок."],
            "oracle_clauses": ["Переключатель виден.", "Переключатель виден."],
        }
        evidence = [{"exact_source_fragment": "BSR 103. Видимость-всегда."}]

        _validate_always_visibility_prestate_cardinality(assertion, evidence)

    def test_transport_normalizer_preserves_complete_dependency_backed_always_pair(
        self,
    ) -> None:
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-028",
                    "field_or_action": "Клиент менял паспорт",
                    "bounded_source_text": (
                        "Клиент менял паспорт Да, если дата выдачи текущего паспорта "
                        "менее 3х лет назад, в остальных случаях «нет» Да "
                        "Переключатель Логическое Да/Нет BSR 103. Видимость-всегда."
                    ),
                }
            ]
        }
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-028",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-028-VISIBLE-DEFAULT",
                            "semantic_disposition": "testable",
                            "condition_clauses": [
                                "Дата выдачи текущего паспорта менее трёх лет назад.",
                                "Дата выдачи текущего паспорта не менее трёх лет назад.",
                            ],
                            "action_clauses": ["Открыть блок.", "Открыть блок."],
                            "oracle_clauses": [
                                "Переключатель виден.",
                                "Переключатель виден.",
                            ],
                            "requirement_code_evidence": [
                                {
                                    "exact_source_fragment": (
                                        "BSR 103. Видимость-всегда."
                                    )
                                }
                            ],
                            "clause_evidence": [
                                {
                                    "clause_kind": "condition",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-028",
                                    "exact_source_fragment": (
                                        "дата выдачи текущего паспорта менее 3х лет назад"
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(raw, context=context)

        self.assertEqual(raw, normalized)
        self.assertNotIn(
            "canonicalize-always-visibility-direct-observation",
            {item["rule"] for item in receipt["repairs"]},
        )
        self.assertNotIn(
            "materialize-always-visibility-prestate-pair",
            {item["rule"] for item in receipt["repairs"]},
        )

    def test_executable_negative_signal_evidence_expands_literal_row_span(
        self,
    ) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] = (
            "BSR 1. Поле «Статус». Минимальное значение 14."
        )
        context = self._bind_context(context)
        boundary = self._boundary()
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-002",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-NEG-001",
                            "atom_id": "ATOM-NEG-001",
                            "obligation_ids": ["OBL-NEG-001"],
                            "clause_evidence": [
                                {
                                    "clause_kind": "condition",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-002",
                                    "exact_source_fragment": "Поле «Статус»",
                                }
                            ],
                            "requirement_code_evidence": [],
                            "supporting_source_bindings": [],
                        }
                    ],
                }
            ],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-001",
                    "scope_obligation_id": "SO-NEG-001",
                    "source_row_id": "SRC-002",
                    "requirement_codes": ["BSR 1"],
                    "restriction_type": "lower-bound",
                    "source_statement": "Минимальное значение 14",
                    "decision": "executable_tc",
                    "linked_atom_id": "ATOM-NEG-001",
                    "linked_obligation_id": "OBL-NEG-001",
                }
            ],
        }

        projections = _executable_negative_signal_evidence_projections(
            payload,
            context,
            boundary,
        )

        self.assertEqual(1, len(projections))
        evidence = projections[0]["canonical_evidence"][0][
            "exact_source_fragment"
        ]
        self.assertEqual(
            "Поле «Статус». Минимальное значение 14",
            evidence,
        )

    def test_transport_normalizer_materializes_source_backed_always_visibility_pair(
        self,
    ) -> None:
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-019",
                    "field_or_action": "Адрес регистрации",
                    "bounded_source_text": (
                        "Адрес регистрации Да, если признак «Ввести вручную»= «Нет». "
                        "BSR 115. Видимость-всегда. BSR 120. При ручном заполнении "
                        "поле автоматически заполняется значениями из полей."
                    ),
                }
            ]
        }
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-019",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-019-115",
                            "semantic_disposition": "testable",
                            "condition_clauses": ["Признак имеет значение «Нет»."],
                            "action_clauses": ["Проверить поле."],
                            "oracle_clauses": ["Поле видимо."],
                            "requirement_code_evidence": [
                                {
                                    "exact_source_fragment": (
                                        "BSR 115. Видимость-всегда."
                                    )
                                }
                            ],
                            "clause_evidence": [],
                        }
                    ],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        assertion = normalized["source_designs"][0]["assertions"][0]
        _validate_always_visibility_prestate_cardinality(
            assertion,
            assertion["requirement_code_evidence"],
        )
        self.assertEqual(2, len(assertion["condition_clauses"]))
        self.assertEqual(6, len(assertion["clause_evidence"]))
        self.assertIn(
            "materialize-always-visibility-prestate-pair",
            {item["rule"] for item in receipt["repairs"]},
        )

    def test_transport_normalizer_does_not_invent_always_visibility_states(
        self,
    ) -> None:
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "field_or_action": "Поле",
                    "bounded_source_text": "BSR 1. Видимость-всегда.",
                }
            ]
        }
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-001",
                            "semantic_disposition": "testable",
                            "condition_clauses": ["Одно состояние"],
                            "action_clauses": ["Проверить"],
                            "oracle_clauses": ["Видимо"],
                            "requirement_code_evidence": [
                                {
                                    "exact_source_fragment": (
                                        "BSR 1. Видимость-всегда."
                                    )
                                }
                            ],
                            "clause_evidence": [],
                        }
                    ],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        assertion = normalized["source_designs"][0]["assertions"][0]
        self.assertEqual(
            ["Открыта форма, содержащая элемент «Поле»."],
            assertion["condition_clauses"],
        )
        self.assertEqual(
            ["Проверить видимость элемента «Поле»."],
            assertion["action_clauses"],
        )
        self.assertEqual(
            ["Элемент «Поле» отображается."],
            assertion["oracle_clauses"],
        )
        self.assertNotIn(
            "materialize-always-visibility-prestate-pair",
            {item["rule"] for item in receipt["repairs"]},
        )
        self.assertIn(
            "canonicalize-always-visibility-direct-observation",
            {item["rule"] for item in receipt["repairs"]},
        )
        _validate_always_visibility_prestate_cardinality(
            assertion,
            assertion["requirement_code_evidence"],
            context["source_rows"][0],
        )

    def test_always_visibility_does_not_borrow_an_unrelated_toggle(self) -> None:
        assertion = {
            "assertion_id": "ASSERT-SERIES-VIS",
            "semantic_disposition": "testable",
            "condition_clauses": ["Открыт блок паспорта."],
            "action_clauses": ["Проверить поле серии."],
            "oracle_clauses": ["Поле серии видимо."],
        }
        evidence = [{"exact_source_fragment": "BSR 84. Видимость-всегда."}]
        source_row = {
            "bounded_source_text": (
                "Серия Да Да Поле ввода Текст Строка "
                "BSR 84. Видимость-всегда."
            )
        }

        _validate_always_visibility_prestate_cardinality(
            assertion,
            evidence,
            source_row,
        )

    def test_transport_normalizer_drops_redundant_pdf_parity_for_xhtml_code(
        self,
    ) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-019",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-019-115",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 115",
                                    "source_row_id": "SRC-019",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": "BSR 115. Видимость-всегда.",
                                    "evidence_source_path": "main.pdf",
                                    "evidence_locator": "page:20",
                                },
                                {
                                    "requirement_code": "BSR 115",
                                    "source_row_id": "SRC-019",
                                    "provenance_role": "pdf-parity",
                                    "exact_source_fragment": "none_required",
                                    "evidence_source_path": "main.pdf",
                                    "evidence_locator": "page:20",
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertEqual(1, diagnostics["repairable_count"])
        self.assertEqual(0, diagnostics["blocking_count"])
        evidence = normalized["source_designs"][0]["assertions"][0][
            "requirement_code_evidence"
        ]
        self.assertEqual(1, len(evidence))
        self.assertEqual("xhtml-row", evidence[0]["provenance_role"])
        self.assertEqual("none_required", evidence[0]["evidence_source_path"])
        self.assertEqual(
            [
                "drop-redundant-pdf-parity-for-xhtml-code",
                "clear-pdf-fields-for-xhtml-provenance",
                "clear-pdf-fields-for-xhtml-provenance",
            ],
            [item["rule"] for item in receipt["repairs"]],
        )
        self.assertEqual(2, len(raw["source_designs"][0]["assertions"][0][
            "requirement_code_evidence"
        ]))

    def test_transport_normalizer_leaves_ambiguous_duplicate_evidence_blocking(
        self,
    ) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-019",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-019-115",
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 115",
                                    "source_row_id": "SRC-019",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": "BSR 115. Первый фрагмент.",
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                },
                                {
                                    "requirement_code": "BSR 115",
                                    "source_row_id": "SRC-019",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": "BSR 115. Второй фрагмент.",
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertEqual(0, diagnostics["repairable_count"])
        self.assertEqual(1, diagnostics["blocking_count"])
        self.assertEqual(raw, normalized)
        self.assertEqual(0, receipt["repair_count"])

    def test_transport_normalizer_restricts_clarification_codes_to_assertion(
        self,
    ) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-019",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-019-118",
                            "requirement_codes": ["BSR 118"],
                            "clarification_clause_bindings": [
                                {
                                    "clarification_id": "CLR-ADDR-001",
                                    "binding_scope": "requirement-code",
                                    "requirement_codes": [
                                        "BSR 118",
                                        "BSR 119",
                                        "BSR 143",
                                        "BSR 144",
                                    ],
                                }
                            ],
                            "requirement_code_evidence": [],
                        }
                    ],
                }
            ]
        }

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertEqual(1, diagnostics["repairable_count"])
        self.assertEqual(
            ["BSR 119", "BSR 143", "BSR 144"],
            diagnostics["findings"][0]["outside_requirement_codes"],
        )
        binding = normalized["source_designs"][0]["assertions"][0][
            "clarification_clause_bindings"
        ][0]
        self.assertEqual(["BSR 118"], binding["requirement_codes"])
        self.assertEqual(
            ["restrict-clarification-codes-to-owning-assertion"],
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_does_not_empty_clarification_code_binding(
        self,
    ) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-019",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-019-118",
                            "requirement_codes": ["BSR 118"],
                            "clarification_clause_bindings": [
                                {
                                    "clarification_id": "CLR-ADDR-001",
                                    "binding_scope": "requirement-code",
                                    "requirement_codes": ["BSR 119"],
                                }
                            ],
                            "requirement_code_evidence": [],
                        }
                    ],
                }
            ]
        }

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertEqual(0, diagnostics["repairable_count"])
        self.assertEqual(1, diagnostics["blocking_count"])
        self.assertEqual(raw, normalized)
        self.assertEqual(0, receipt["repair_count"])

    def test_transport_normalizer_inherits_unique_clarification_code_from_sibling(
        self,
    ) -> None:
        context = self._context()
        context["approved_clarifications"] = [
            {
                "clarification_id": "CLR-ADDR-004",
                "requirement_codes": ["BSR 125", "BSR 150"],
            }
        ]
        donor_evidence = {
            "requirement_code": "BSR 125",
            "source_row_id": "SRC-022",
            "provenance_role": "xhtml-row",
            "exact_source_fragment": "BSR 125. Отображать: Да.",
            "evidence_source_path": "none_required",
            "evidence_locator": "none_required",
        }
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-022",
                    "requirement_codes": ["BSR 125"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-022-VIS",
                            "requirement_codes": ["BSR 125"],
                            "requirement_code_evidence": [donor_evidence],
                            "clarification_clause_bindings": [],
                        },
                        {
                            "assertion_id": "ASSERT-022-DADATA",
                            "requirement_codes": [],
                            "requirement_code_evidence": [],
                            "clarification_clause_bindings": [
                                {
                                    "clarification_id": "CLR-ADDR-004",
                                    "binding_scope": "requirement-code",
                                    "requirement_codes": [],
                                }
                            ],
                        },
                    ],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        repaired = normalized["source_designs"][0]["assertions"][1]
        self.assertEqual(["BSR 125"], repaired["requirement_codes"])
        self.assertEqual([donor_evidence], repaired["requirement_code_evidence"])
        self.assertEqual(
            ["BSR 125"],
            repaired["clarification_clause_bindings"][0]["requirement_codes"],
        )
        self.assertIn(
            "inherit-unique-clarification-code-from-sibling-evidence",
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_inherits_declared_unique_code_on_behavioral_sibling(
        self,
    ) -> None:
        context = self._context()
        context["approved_clarifications"] = [
            {
                "clarification_id": "CLR-ADDR-004",
                "requirement_codes": ["BSR 125"],
            }
        ]
        donor_evidence = {
            "requirement_code": "BSR 125",
            "source_row_id": "SRC-022",
            "provenance_role": "xhtml-row",
            "exact_source_fragment": "BSR 125. Видимость: Да.",
            "evidence_source_path": "none_required",
            "evidence_locator": "none_required",
        }
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-022",
                    "requirement_codes": ["BSR 125"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-022-VIS",
                            "requirement_codes": ["BSR 125"],
                            "requirement_code_evidence": [donor_evidence],
                            "clarification_clause_bindings": [],
                        },
                        {
                            "assertion_id": "ASSERT-022-DADATA",
                            "requirement_codes": [],
                            "requirement_code_evidence": [],
                            "clarification_clause_bindings": [
                                {
                                    "clarification_id": "CLR-ADDR-004",
                                    "binding_scope": "requirement-code",
                                    "requirement_codes": ["BSR 125"],
                                }
                            ],
                        },
                    ],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        repaired = normalized["source_designs"][0]["assertions"][1]
        self.assertEqual(["BSR 125"], repaired["requirement_codes"])
        self.assertEqual([donor_evidence], repaired["requirement_code_evidence"])
        self.assertIn(
            "inherit-unique-clarification-code-from-sibling-evidence",
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_keeps_ambiguous_clarification_code_blocking(
        self,
    ) -> None:
        context = self._context()
        context["approved_clarifications"] = [
            {
                "clarification_id": "CLR-ADDR-004",
                "requirement_codes": ["BSR 125", "BSR 150"],
            }
        ]
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-022",
                    "requirement_codes": ["BSR 125", "BSR 150"],
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-022-DADATA",
                            "requirement_codes": [],
                            "requirement_code_evidence": [],
                            "clarification_clause_bindings": [
                                {
                                    "clarification_id": "CLR-ADDR-004",
                                    "binding_scope": "requirement-code",
                                    "requirement_codes": [],
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        self.assertEqual(raw, normalized)
        self.assertEqual(0, receipt["repair_count"])

    def test_transport_normalizer_drops_only_provable_dependency_overlink(
        self,
    ) -> None:
        context = self._context()
        boundary = self._boundary()
        raw = self._design()
        binding = raw["dependency_bindings"][0]
        binding["linked_assertion_ids"].append("ASSERT-003")
        binding["linked_atom_ids"].append("ATOM-003")
        binding["linked_obligation_ids"].append("OBL-002")

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        finding = next(
            item
            for item in diagnostics["findings"]
            if item["code"] == "dependency-assertion-overlink"
        )
        self.assertEqual(["ASSERT-003"], finding["dropped_assertion_ids"])
        self.assertEqual(
            ["drop-dependency-overlinks-without-literal-evidence"],
            [
                item["rule"]
                for item in receipt["repairs"]
                if "dependency-overlink" in item["rule"]
            ],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(context, boundary, normalized)[
                "status"
            ],
        )

    def test_transport_normalizer_canonicalizes_closed_executable_oracle_alias(
        self,
    ) -> None:
        raw = {
            "source_designs": [],
            "obligations": [],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-001",
                    "decision": "executable_tc",
                    "oracle_status": "source-backed-executable",
                }
            ],
            "requiredness_oracles": [],
        }

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertEqual(1, diagnostics["repairable_count"])
        self.assertEqual(
            "oracle-status-noncanonical-alias",
            diagnostics["findings"][0]["code"],
        )
        self.assertEqual(
            "source-backed",
            normalized["negative_oracles"][0]["oracle_status"],
        )
        self.assertEqual(
            ["canonicalize-executable-oracle-status-alias"],
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_canonicalizes_source_signal_polarity(self) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-REQ",
                            "polarity": "positive",
                            "obligation_ids": ["OBL-REQ"],
                        },
                        {
                            "assertion_id": "ASSERT-OPT",
                            "polarity": "negative",
                            "obligation_ids": ["OBL-OPT"],
                        },
                    ],
                }
            ],
            "obligations": [],
            "negative_oracles": [],
            "requiredness_oracles": [
                {
                    "linked_obligation_id": "OBL-REQ",
                    "restriction_type": "requiredness",
                },
                {
                    "linked_obligation_id": "OBL-OPT",
                    "restriction_type": "optionality",
                },
            ],
        }

        normalized, receipt = normalize_semantic_design_transport(raw)

        assertions = normalized["source_designs"][0]["assertions"]
        self.assertEqual("negative", assertions[0]["polarity"])
        self.assertEqual("positive", assertions[1]["polarity"])
        self.assertEqual(
            2,
            sum(
                item["rule"] == "canonicalize-source-signal-polarity"
                for item in receipt["repairs"]
            ),
        )

    def test_transport_normalizer_does_not_reinterpret_unknown_oracle_status(
        self,
    ) -> None:
        raw = {
            "source_designs": [],
            "obligations": [],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-001",
                    "decision": "executable_tc",
                    "oracle_status": "probably-backed",
                }
            ],
            "requiredness_oracles": [],
        }

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertEqual(0, diagnostics["repairable_count"])
        self.assertEqual(raw, normalized)
        self.assertEqual(0, receipt["repair_count"])

    def test_transport_normalizer_materializes_runner_owned_oracle_scope_projection(
        self,
    ) -> None:
        raw = {
            "source_designs": [],
            "obligations": [
                {
                    "obligation_id": "OBL-POS-001",
                    "scope_obligation_ids": ["SO-NEG-001"],
                },
                {
                    "obligation_id": "OBL-NEG-001",
                    "scope_obligation_ids": ["SIG-NEG-001"],
                },
                {
                    "obligation_id": "OBL-POS-002",
                    "scope_obligation_ids": ["SO-NEG-002"],
                },
                {
                    "obligation_id": "OBL-NEG-002",
                    "scope_obligation_ids": ["SO-NEG-002"],
                }
            ],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-001",
                    "linked_obligation_id": "OBL-NEG-001",
                },
                {
                    "signal_id": "SIG-NEG-002",
                    "linked_obligation_id": "OBL-NEG-002",
                }
            ],
            "requiredness_oracles": [],
        }

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertIn(
            "obligation-oracle-scope-projection-mismatch",
            [item["code"] for item in diagnostics["findings"]],
        )
        self.assertEqual([], normalized["obligations"][0]["scope_obligation_ids"])
        self.assertEqual(
            ["SO-NEG-001"], normalized["obligations"][1]["scope_obligation_ids"]
        )
        self.assertEqual([], normalized["obligations"][2]["scope_obligation_ids"])
        self.assertEqual(
            ["SO-NEG-002"], normalized["obligations"][3]["scope_obligation_ids"]
        )
        self.assertIn(
            "bind-obligation-canonical-oracle-scope-ids",
            [item["rule"] for item in receipt["repairs"]],
        )
        self.assertEqual(3, receipt["repair_count"])

    def test_transport_normalizer_materializes_applicability_registry_projection(
        self,
    ) -> None:
        context = self._context()
        boundary = self._boundary()
        raw = self._design()
        traceability = next(
            item
            for item in raw["applicability"]
            if item["dimension"] == "traceability"
        )
        traceability.update(
            applicable="no",
            linked_atoms=[],
            linked_test_cases=[],
        )

        diagnostics = semantic_design_transport_diagnostics(raw)
        normalized, receipt = normalize_semantic_design_transport(raw)

        self.assertIn(
            "applicability-registry-projection-mismatch",
            [item["code"] for item in diagnostics["findings"]],
        )
        normalized_traceability = next(
            item
            for item in normalized["applicability"]
            if item["dimension"] == "traceability"
        )
        self.assertEqual("yes", normalized_traceability["applicable"])
        self.assertEqual(
            {item["planned_tc_id"] for item in normalized["obligations"]},
            set(normalized_traceability["linked_test_cases"]),
        )
        self.assertIn(
            "materialize-applicability-from-obligation-registry",
            [item["rule"] for item in receipt["repairs"]],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(context, boundary, normalized)[
                "status"
            ],
        )

    def test_transport_diagnostics_reports_missing_obligation_registry_items(
        self,
    ) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-019",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-SRC-019-118",
                            "obligation_ids": ["OBL-SRC-019-118"],
                        }
                    ],
                }
            ],
            "obligations": [],
        }

        diagnostics = semantic_design_transport_diagnostics(raw)

        self.assertEqual(1, diagnostics["blocking_count"])
        finding = diagnostics["findings"][0]
        self.assertEqual("obligation-registry-mismatch", finding["code"])
        self.assertEqual(
            ["OBL-SRC-019-118"],
            finding["missing_obligation_ids"],
        )

    def test_transport_diagnostics_aggregates_all_non_neutral_legacy_state_bindings(
        self,
    ) -> None:
        neutral = {
            "initial_state_capture": "none_required",
            "changed_state_setup": "none_required",
            "pre_action_state_oracle": "none_required",
            "state_relation": "none_required",
        }
        raw = {
            "source_designs": [],
            "obligations": [
                {"obligation_id": "OBL-001", **neutral},
                {
                    "obligation_id": "OBL-002",
                    **neutral,
                    "initial_state_capture": "source-condition:0",
                },
                {
                    "obligation_id": "OBL-003",
                    **neutral,
                    "changed_state_setup": "Prepare a changed visible value.",
                    "pre_action_state_oracle": "Observe it before the action.",
                    "state_relation": "different-from-captured-initial",
                },
            ],
        }

        diagnostics = semantic_design_transport_diagnostics(raw)

        findings = {item["code"]: item for item in diagnostics["findings"]}
        self.assertEqual(
            3,
            findings["legacy-obligation-state-fields"][
                "affected_obligation_count"
            ],
        )
        self.assertEqual(
            ["OBL-002", "OBL-003"],
            [
                item["obligation_id"]
                for item in findings["legacy-non-neutral-state-bindings"][
                    "affected_obligations"
                ]
            ],
        )

    def test_signal_registry_excludes_default_template_but_keeps_format_rule(
        self,
    ) -> None:
        registry = _source_signal_registry(
            [
                {
                    "source_row_id": "SRC-024",
                    "bounded_source_text": (
                        "BSR 272. Ограничение на формат: только 10 числовых символов. "
                        "BSR 273. По умолчанию стоит шаблон с кодом страны "
                        "«+7(xxx)-xxx-xx-xx»"
                    ),
                }
            ],
            {"SRC-024": ["BSR 272", "BSR 273"]},
        )

        self.assertEqual(
            [
                {
                    "signal_id": "SIG-NEG-001",
                    "scope_obligation_id": "SO-NEG-001",
                    "source_row_id": "SRC-024",
                    "source_ref": "",
                    "field_or_block": "",
                    "requirement_codes": ["BSR 272"],
                    "restriction_type": "format",
                    "literal_anchor": "формат",
                }
            ],
            registry["negative"],
        )

    def test_transport_normalizer_binds_signal_identity_to_source_row(self) -> None:
        raw = {
            "source_designs": [],
            "obligations": [],
            "dependency_bindings": [],
            "negative_oracles": [
                {
                    "signal_id": "SIG-NEG-001",
                    "source_row_id": "SRC-001",
                    "source_ref": "invented expanded reference",
                    "field_or_block": "invented field",
                }
            ],
            "requiredness_oracles": [],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "source_ref": "BSR 1",
                    "field_or_action": "Статус",
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        oracle = normalized["negative_oracles"][0]
        self.assertEqual("BSR 1", oracle["source_ref"])
        self.assertEqual("Статус", oracle["field_or_block"])
        self.assertEqual(
            [
                "bind-source-signal-row-identity",
                "bind-source-signal-row-identity",
            ],
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_transport_normalizer_preserves_compound_signal_target(self) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] = (
            "BSR 1. Поле «Статус» заполняется по справочнику Статусы: "
            "Активен, Неактивен. Обязательно должны быть введены регион и "
            "номер дома. При выборе значения система сохраняет выбранное значение."
        )
        self._bind_context(context)
        boundary = self._boundary()
        raw = {
            "source_designs": [],
            "obligations": [],
            "dependency_bindings": [],
            "negative_oracles": [],
            "requiredness_oracles": [
                {
                    "signal_id": "SIG-REQ-001",
                    "scope_obligation_id": "SO-REQ-001",
                    "source_row_id": "SRC-002",
                    "source_ref": "BSR 1",
                    "field_or_block": "регион",
                },
                {
                    "signal_id": "SIG-REQ-002",
                    "scope_obligation_id": "SO-REQ-002",
                    "source_row_id": "SRC-002",
                    "source_ref": "BSR 1",
                    "field_or_block": "номер дома",
                },
            ],
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
            boundary=boundary,
        )

        self.assertEqual(
            ["регион", "номер дома"],
            [
                item["field_or_block"]
                for item in normalized["requiredness_oracles"]
            ],
        )
        repaired_paths = {
            item["path"]
            for item in receipt["repairs"]
            if item["rule"] == "bind-source-signal-row-identity"
        }
        self.assertNotIn(
            "$.requiredness_oracles[0].field_or_block",
            repaired_paths,
        )
        self.assertNotIn(
            "$.requiredness_oracles[1].field_or_block",
            repaired_paths,
        )

    def test_transport_normalizer_repairs_double_wrapped_block_heading(self) -> None:
        raw = {
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-001",
                            "oracle_clauses": [
                                "Отображается заголовок «Блок «Адреса клиента»»."
                            ],
                        }
                    ],
                }
            ],
            "obligations": [],
            "dependency_bindings": [],
            "negative_oracles": [],
            "requiredness_oracles": [],
        }
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "bounded_source_text": "Блок «Адреса клиента»",
                }
            ]
        }

        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=context,
        )

        self.assertEqual(
            "Отображается блок «Адреса клиента».",
            normalized["source_designs"][0]["assertions"][0][
                "oracle_clauses"
            ][0],
        )
        self.assertIn(
            "canonicalize-double-wrapped-block-heading",
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_signal_registry_keeps_restrictive_template_rule(self) -> None:
        registry = _source_signal_registry(
            [
                {
                    "source_row_id": "SRC-001",
                    "bounded_source_text": (
                        "BSR 7. Введенное значение должно соответствовать "
                        "шаблону AA-999."
                    ),
                }
            ],
            {"SRC-001": ["BSR 7"]},
        )

        self.assertEqual(
            ["format"],
            [item["restriction_type"] for item in registry["negative"]],
        )
        self.assertEqual("шаблону", registry["negative"][0]["literal_anchor"])

    def test_signal_registry_splits_compound_text_requiredness_with_typed_cell(
        self,
    ) -> None:
        registry = _source_signal_registry(
            [
                {
                    "source_row_id": "SRC-019",
                    "source_ref": "BSR 115-120",
                    "field_or_action": "Адрес регистрации",
                    "bounded_source_text": (
                        "BSR 117. Правило: обязательно должн ы быть введен ы "
                        "регион и номер дома. Если квартира не указана."
                    ),
                    "field_properties": {
                        "requiredness": {
                            "normalized_value": "required",
                            "source_value": "Да, если признак «Ввести вручную» = «Нет»",
                            "property_id": "FP-SRC-019-REQUIREDNESS-REQUIRED",
                            "source_cell_locator": "/*/*[2]",
                        }
                    },
                }
            ],
            {"SRC-019": ["BSR 117"]},
        )

        self.assertEqual(3, len(registry["requiredness"]))
        typed, region, house = registry["requiredness"]
        self.assertEqual("typed-xhtml-cell", typed["source_binding"])
        self.assertEqual([], typed["requirement_codes"])
        self.assertEqual(
            ["регион", "номер дома"],
            [region["field_or_block"], house["field_or_block"]],
        )
        self.assertEqual(
            [["BSR 117"], ["BSR 117"]],
            [region["requirement_codes"], house["requirement_codes"]],
        )
        self.assertEqual(
            ["регион", "номер дома"],
            [region["literal_anchor"], house["literal_anchor"]],
        )
        self.assertTrue(
            all(
                item["source_binding"] == "compound-text-requirement"
                for item in (region, house)
            )
        )
        self.assertTrue(
            all(
                "обязательно должн ы быть введен ы регион и номер дома"
                in item["requiredness_source"]
                for item in (region, house)
            )
        )

    def test_optionality_is_positive_and_success_message_is_not_negative_feedback(
        self,
    ) -> None:
        registry = _source_signal_registry(
            [
                {
                    "source_row_id": "SRC-001",
                    "bounded_source_text": (
                        "BSR 7. Поле необязательное. Отображается сообщение об "
                        "успешном сохранении. При ошибке отображается сообщение об ошибке."
                    ),
                }
            ],
            {"SRC-001": ["BSR 7"]},
        )
        self.assertEqual(
            ["optionality"],
            [item["restriction_type"] for item in registry["requiredness"]],
        )
        self.assertTrue(
            any(
                item["restriction_type"] == "feedback"
                for item in registry["negative"]
            )
        )
        self.assertFalse(
            any(
                "успешном сохранении" in item["literal_anchor"]
                for item in registry["negative"]
            )
        )

        context = self._context()
        context["source_rows"][1]["bounded_source_text"] += (
            " Поле необязательное. Пустое значение допускается."
        )
        self._bind_context(context)
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        optional_assertion = self._assertion(
            assertion_id="ASSERT-004",
            atom_id="ATOM-004",
            property_id="PROP-004",
            field="Статус",
            source_ref="BSR 1",
            codes=["BSR 1"],
            conditions=["Поле «Статус»"],
            actions=["Оставить поле «Статус» пустым"],
            oracles=["Пустое значение допускается"],
            obligation_ids=["OBL-003"],
            requirement_evidence=[
                {
                    "requirement_code": "BSR 1",
                    "source_row_id": "SRC-002",
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": context["source_rows"][1][
                        "bounded_source_text"
                    ],
                    "evidence_source_path": "none_required",
                    "evidence_locator": "none_required",
                }
            ],
            evidence=[
                {
                    "clause_kind": "condition",
                    "clause_index": 0,
                    "source_row_id": "SRC-002",
                    "exact_source_fragment": "Поле «Статус»",
                },
                {
                    "clause_kind": "action",
                    "clause_index": 0,
                    "source_row_id": "SRC-002",
                    "exact_source_fragment": "Поле необязательное",
                },
                {
                    "clause_kind": "oracle",
                    "clause_index": 0,
                    "source_row_id": "SRC-002",
                    "exact_source_fragment": "Пустое значение допускается",
                },
            ],
        )
        design["source_designs"][1]["assertions"].append(optional_assertion)
        optional_obligation = copy.deepcopy(design["obligations"][0])
        optional_obligation.update(
            obligation_id="OBL-003",
            linked_atom_id="ATOM-004",
            source_property_id="PROP-004",
            property_type="optionality",
            obligation_class="empty-value-accepted",
            required_behavior="Пустое необязательное поле допускается.",
            planned_tc_id="TC-003",
            design_dimension="equivalence",
            planned_check="Оставить необязательное поле пустым.",
            check_type="positive",
            coverage_class="optionality",
            input_class="empty value",
            single_expected_behavior="Пустое значение принято.",
            test_data="Пустое значение",
            dictionary_refs=[],
            dictionary_coverage="none_required",
            scope_obligation_ids=["SO-REQ-001"],
        )
        design["obligations"].append(optional_obligation)
        design["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": ["BSR 1"],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-002",
                "source_ref": "BSR 1",
                "field_or_block": "Статус",
                "restriction_type": "optionality",
                "requiredness_source": "Поле необязательное.",
                "requiredness_class": "optional",
                "required_when": "not_applicable",
                "marker_oracle_found": "not_applicable",
                "empty_value_oracle_found": "yes",
                "oracle_source": "BSR 1",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": "TC-003",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "Сохранить отдельную позитивную проверку optionality.",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-004",
                "linked_obligation_id": "OBL-003",
            }
        ]
        applicability = {
            item["dimension"]: item for item in design["applicability"]
        }
        applicability["equivalence"]["linked_atoms"].append("ATOM-004")
        applicability["equivalence"]["linked_test_cases"].append("TC-003")
        applicability["traceability"]["linked_atoms"].append("ATOM-004")
        applicability["traceability"]["linked_test_cases"].append("TC-003")

        receipt = validate_semantic_design_binding(
            context,
            self._boundary(),
            design,
        )
        self.assertEqual("verified", receipt["status"])

        collapsed = copy.deepcopy(design)
        collapsed["requiredness_oracles"][0].update(
            linked_atom_id="ATOM-002",
            linked_obligation_id="OBL-001",
            planned_tc_or_gap="TC-001",
        )
        collapsed["obligations"][0]["scope_obligation_ids"] = ["SO-REQ-001"]
        collapsed["obligations"][2]["scope_obligation_ids"] = []
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "exact signal evidence in its owning assertion",
        ):
            validate_semantic_design_binding(
                context,
                self._boundary(),
                collapsed,
            )

    def test_standalone_bridge_rejects_forged_boundary_and_stale_context(self) -> None:
        for location in ("root", "source-decision", "disposition"):
            with self.subTest(location=location):
                boundary = self._boundary()
                if location == "root":
                    boundary["unexpected"] = True
                elif location == "source-decision":
                    boundary["source_decisions"][0]["unexpected"] = True
                else:
                    boundary["source_decisions"][1]["disposition"] = "context"
                with self.assertRaises(SemanticDesignBridgeError):
                    validate_bridge_boundary(self._context(), boundary)

        context = self._context()
        context["scope_boundary"]["target"] = "Подменённая граница."
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "bounded_context_sha256 mismatch",
        ):
            validate_bridge_boundary(context, self._boundary())

    def test_materializer_path_reuses_fail_closed_boundary_validation(self) -> None:
        scenarios: list[tuple[dict[str, object], dict[str, object]]] = []

        unknown = self._boundary()
        unknown["source_decisions"][0]["unexpected"] = True
        scenarios.append((self._context(), unknown))

        forged = self._boundary()
        forged["source_decisions"][1]["disposition"] = "context"
        scenarios.append((self._context(), forged))

        stale = self._context()
        stale["scope_boundary"]["target"] = "Подменённая граница."
        scenarios.append((stale, self._boundary()))

        for index, (context, boundary) in enumerate(scenarios):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as raw:
                handoff = Path(raw) / "handoff"
                with self.assertRaises(SemanticDesignBridgeError):
                    materialize_semantic_design_bridge(
                        repo_root=Path(raw),
                        context=context,
                        scope_boundary_decision=boundary,
                        semantic_design=self._design(),
                        approved_clarifications=(),
                        publication_owner_token=OWNER_TOKEN,
                        handoff_dir=handoff,
                    )
                self.assertFalse(handoff.exists())

    def test_strict_schema_rejects_unknown_root_and_nested_fields(self) -> None:
        schema = semantic_design_output_schema(["SRC-001", "SRC-002", "SRC-003"])
        schema.pop("$schema")
        requirement_binding = schema["properties"]["source_designs"]["items"][
            "properties"
        ]["assertions"]["items"]["properties"]["requirement_code_evidence"][
            "items"
        ]
        self.assertEqual(
            {
                "requirement_code",
                "source_row_id",
                "provenance_role",
                "exact_source_fragment",
                "evidence_source_path",
                "evidence_locator",
            },
            set(requirement_binding["required"]),
        )

        self.assertTrue(
            all(
                property_schema["type"] == "string"
                for property_schema in requirement_binding["properties"].values()
            )
        )
        for location in ("root", "nested"):
            with self.subTest(location=location):
                design = self._design()
                if location == "root":
                    design["unexpected"] = "rejected"
                else:
                    design["source_designs"][1]["assertions"][0][
                        "unexpected"
                    ] = "rejected"
                with self.assertRaises(OpenAIStrictOutputInstanceError):
                    validate_openai_strict_output_instance(design, schema)

    def test_release_author_schema_requires_ready_design(self) -> None:
        schema = semantic_design_output_schema(
            ["SRC-001", "SRC-002", "SRC-003"],
            require_ready=True,
            expected_minimum_obligation_count=2,
            expected_dependency_count=2,
            expected_dictionary_count=1,
            expected_negative_signal_count=4,
            expected_requiredness_signal_count=3,
        )
        self.assertEqual(["ready"], schema["properties"]["status"]["enum"])
        self.assertEqual(
            ["none_required"],
            schema["properties"]["blocking_reason"]["enum"],
        )
        expected_sizes = {
            "source_designs": 3,
            "dependency_bindings": 2,
            "dictionaries": 1,
            "negative_oracles": 4,
            "requiredness_oracles": 3,
            "applicability": len(APPLICABILITY_DIMENSIONS),
        }
        for field, size in expected_sizes.items():
            self.assertEqual(size, schema["properties"][field]["minItems"])
            self.assertEqual(size, schema["properties"][field]["maxItems"])
        self.assertEqual(2, schema["properties"]["obligations"]["minItems"])
        self.assertNotIn("maxItems", schema["properties"]["obligations"])
        assertions_schema = schema["properties"]["source_designs"]["items"][
            "properties"
        ]["assertions"]
        self.assertEqual(1, assertions_schema["minItems"])
        assertion_schema = assertions_schema["items"]["properties"]
        self.assertEqual(
            "string",
            assertion_schema["execution_readiness_rationale"]["type"],
        )
        self.assertIn(
            "ambiguous",
            assertion_schema["semantic_disposition"]["enum"],
        )
        self.assertIn(
            "dependency-blocked",
            assertion_schema["execution_readiness"]["enum"],
        )
        self.assertEqual(r".*\S.*", assertion_schema["atom_id"]["pattern"])

    def test_digest_drift_is_rejected(self) -> None:
        for field in (
            "prepared_context_sha256",
            "scope_boundary_decision_sha256",
        ):
            with self.subTest(field=field):
                design = self._design()
                design[field] = "f" * 64
                with self.assertRaisesRegex(SemanticDesignBridgeError, "digest mismatch"):
                    self._validate(design)

    def test_disposition_code_and_order_drift_are_rejected(self) -> None:
        mutations = {
            "disposition": lambda design: design["source_designs"][1].update(
                {"boundary_disposition": "context"}
            ),
            "code": lambda design: design["source_designs"][1].update(
                {"requirement_codes": []}
            ),
            "order": lambda design: design["source_designs"].__setitem__(
                slice(0, 2), list(reversed(design["source_designs"][:2]))
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                design = self._design()
                mutate(design)
                with self.assertRaises(SemanticDesignBridgeError):
                    self._validate(design)

    def test_included_na_only_and_context_testable_are_rejected(self) -> None:
        included_na = self._design()
        assertion = included_na["source_designs"][1]["assertions"][0]
        assertion.update(
            {
                "semantic_disposition": "not-applicable",
                "execution_readiness": "not-applicable",
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "clause_evidence": [],
                "obligation_ids": [],
                "disposition_rationale": "Строка ошибочно объявлена неприменимой целиком.",
            }
        )
        with self.assertRaisesRegex(SemanticDesignBridgeError, "included row cannot be N/A-only"):
            self._validate(included_na)

        context_testable = self._design()
        assertion = context_testable["source_designs"][0]["assertions"][0]
        assertion.update(
            {
                "semantic_disposition": "testable",
                "execution_readiness": "ready",
                "action_clauses": ["Раздел 1"],
                "oracle_clauses": ["Сведения о занятости"],
                "clause_evidence": [
                    {
                        "clause_kind": "action",
                        "clause_index": 0,
                        "source_row_id": "SRC-001",
                        "exact_source_fragment": "Раздел 1",
                    },
                    {
                        "clause_kind": "oracle",
                        "clause_index": 0,
                        "source_row_id": "SRC-001",
                        "exact_source_fragment": "Сведения о занятости",
                    },
                ],
                "obligation_ids": ["OBL-context"],
                "disposition_rationale": "none_required",
            }
        )
        with self.assertRaisesRegex(SemanticDesignBridgeError, "context/excluded row"):
            self._validate(context_testable)

    def test_missing_observation_interface_preserves_included_gap_without_fake_tc(
        self,
    ) -> None:
        context = self._context()
        context["expected_dependencies"] = [
            {
                "kind": "other",
                "name": "Очистить",
                "source_row_ids": ["SRC-003"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-003"],
                "exact_source_fragments": ["кнопки «Очистить»"],
            }
        ]
        self._bind_context(context)

        boundary = self._boundary()
        complete_fragment = str(context["source_rows"][2]["bounded_source_text"])
        boundary["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "other",
                "name": "Очистить",
                "source_row_ids": ["SRC-003"],
                "resolution": "source-provided",
                "target_source_row_ids": ["SRC-003"],
                "exact_source_fragments": ["кнопки «Очистить»"],
                "gap_ids": ["GAP-OBS-001"],
                "blocking": False,
                "rationale": "Источник определяет эффект, но не интерфейс его наблюдения.",
            }
        )
        boundary["gaps"] = [
            {
                "gap_id": "GAP-OBS-001",
                "gap_type": "missing-observation-interface",
                "source_row_ids": ["SRC-003"],
                "source_refs": ["BSR 2"],
                "exact_source_fragments": [complete_fragment],
                "blocking": False,
                "clarification_question": (
                    "Какой зарегистрированный интерфейс позволяет наблюдать эффект BSR 2?"
                ),
                "downstream_handling": "carry-to-source-model",
            }
        ]

        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        gap_assertion = design["source_designs"][2]["assertions"][0]
        gap_assertion.update(
            {
                "canonical_statement": (
                    "BSR 2 сохранён как непроверяемый эффект без интерфейса наблюдения."
                ),
                "semantic_disposition": "not-applicable",
                "execution_readiness": "not-applicable",
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "clause_evidence": [],
                "obligation_ids": [],
                "disposition_rationale": (
                    "Требование включено, но зарегистрированный интерфейс наблюдения отсутствует."
                ),
            }
        )
        design["obligations"] = [design["obligations"][0]]
        design["reset_lifecycle_bindings"] = []
        for row in design["applicability"]:
            row["linked_atoms"] = [
                value for value in row["linked_atoms"] if value != "ATOM-003"
            ]
            row["linked_test_cases"] = [
                value for value in row["linked_test_cases"] if value != "TC-002"
            ]
            if not row["linked_test_cases"]:
                row.update(
                    {
                        "applicable": "no",
                        "source_ref": "none_required",
                        "reason": "Изолированно неприменимо к исполнимой части scope.",
                    }
                )
        design["dependency_bindings"].append(
            {
                **copy.deepcopy(boundary["dependencies"][1]),
                "semantic_disposition": "gap-bound",
                "linked_assertion_ids": ["ASSERT-003"],
                "linked_atom_ids": ["ATOM-003"],
                "linked_obligation_ids": [],
                "mapping_rationale": (
                    "Зависимость сохранена через N/A ASSERT/ATOM и явный gap наблюдаемости."
                ),
            }
        )

        preflight = validate_semantic_input_preflight(context, boundary)
        self.assertEqual(
            1,
            semantic_design_minimum_obligation_count(preflight, boundary),
        )
        receipt = validate_semantic_design_binding(context, boundary, design)
        self.assertEqual("verified", receipt["status"])
        self.assertEqual(1, receipt["planned_test_case_count"])

        design["dependency_bindings"][1]["linked_obligation_ids"] = ["OBL-001"]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "gap-bound mapping requires.*no executable obligations",
        ):
            validate_semantic_design_binding(context, boundary, design)

    def test_literal_evidence_mismatch_is_rejected(self) -> None:
        design = self._design()
        design["source_designs"][1]["assertions"][0]["clause_evidence"][0][
            "exact_source_fragment"
        ] = "Несуществующий фрагмент"
        with self.assertRaisesRegex(SemanticDesignBridgeError, "absent from bounded row"):
            self._validate(design)

    def test_clarification_derived_action_reuses_literal_condition_evidence(self) -> None:
        context = {
            "source_rows": [
                {
                    "source_row_id": "SRC-025",
                    "bounded_source_text": (
                        "BSR 274. Видимость: Да, если поле «Тип занятости» "
                        "заполнено и значение ≠ «Пенсионер (не работает)»"
                    ),
                }
            ]
        }
        assertion = {
            "assertion_id": "ASSERT-SRC-025-VIS",
            "condition_clauses": [
                "Поле «Тип занятости» заполнено значением «работа по найму»."
            ],
            "action_clauses": [
                "Выбрать социальный статус «работа по найму»."
            ],
            "clause_evidence": [
                {
                    "clause_kind": "condition",
                    "clause_index": 0,
                    "source_row_id": "SRC-025",
                    "exact_source_fragment": "поле «Тип занятости» заполнено",
                },
                {
                    "clause_kind": "action",
                    "clause_index": 0,
                    "source_row_id": "SRC-025",
                    "exact_source_fragment": "работа по найму",
                },
            ],
            "clarification_clause_bindings": [
                {
                    "clarification_id": "CLR-EMP-001",
                    "clause_kind": "condition",
                    "clause_index": 0,
                    "requirement_codes": ["BSR 274"],
                    "exact_answer_sha256": "a" * 64,
                    "binding_scope": "requirement-code",
                    "source_row_ids": [],
                }
            ],
        }
        payload = {
            "source_designs": [
                {"source_row_id": "SRC-025", "assertions": [assertion]}
            ]
        }

        projections = _clarification_condition_action_evidence_projections(
            payload,
            context,
        )

        self.assertEqual(1, len(projections))
        self.assertEqual(
            "поле «Тип занятости» заполнено",
            projections[0]["canonical_evidence"][1]["exact_source_fragment"],
        )
        assertion["action_clauses"] = ["Открыть произвольный раздел «Настройки». "]
        self.assertEqual(
            [],
            _clarification_condition_action_evidence_projections(payload, context),
        )

    def test_same_row_multi_fragment_clause_evidence_is_merged_to_literal_span(
        self,
    ) -> None:
        context = self._context()
        boundary = self._boundary()
        design = self._design()
        assertion = design["source_designs"][1]["assertions"][0]
        assertion["clause_evidence"][2:3] = [
            {
                "clause_kind": "oracle",
                "clause_index": 0,
                "source_row_id": "SRC-002",
                "exact_source_fragment": "система сохраняет",
            },
            {
                "clause_kind": "oracle",
                "clause_index": 0,
                "source_row_id": "SRC-002",
                "exact_source_fragment": "выбранное значение",
            },
        ]

        diagnostics = semantic_design_transport_diagnostics(
            design,
            context=context,
            boundary=boundary,
        )
        normalized, receipt = normalize_semantic_design_transport(
            design,
            context=context,
            boundary=boundary,
        )

        self.assertIn(
            "same-row-multi-fragment-clause-evidence-alias",
            [item["code"] for item in diagnostics["findings"]],
        )
        normalized_evidence = normalized["source_designs"][1]["assertions"][0][
            "clause_evidence"
        ]
        self.assertEqual(3, len(normalized_evidence))
        self.assertEqual(
            "система сохраняет выбранное значение",
            normalized_evidence[2]["exact_source_fragment"],
        )
        self.assertIn(
            "merge-same-row-clause-evidence-span",
            [item["rule"] for item in receipt["repairs"]],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                normalized,
            )["status"],
        )

    def test_clause_evidence_requires_an_explicit_non_excluded_support_relation(
        self,
    ) -> None:
        design = self._design()
        assertion = design["source_designs"][1]["assertions"][0]
        assertion["clause_evidence"][1].update(
            source_row_id="SRC-003",
            exact_source_fragment="поле заполнено изменённым значением",
        )
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "explicitly declared non-excluded supporting row",
        ):
            self._validate(design)

        assertion["supporting_source_bindings"] = [
            {
                "source_row_id": "SRC-003",
                "evidence_role": "constraint",
                "exact_source_fragment": "поле заполнено изменённым значением",
            }
        ]
        receipt = self._validate(design)
        self.assertEqual("verified", receipt["status"])

        unrelated_support = self._design()
        unrelated_support["source_designs"][1]["assertions"][0][
            "supporting_source_bindings"
        ] = [
            {
                "source_row_id": "SRC-001",
                "evidence_role": "definition",
                "exact_source_fragment": "Раздел 1",
            }
        ]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "lacks an explicit boundary dependency or typed source-context",
        ):
            self._validate(unrelated_support)

        boundary = self._boundary()
        boundary["source_decisions"][0].update(
            disposition="excluded",
            rationale="Строка исключена в этой проверке provenance relation.",
        )
        excluded_support = self._design()
        excluded_support["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        excluded_support["source_designs"][0][
            "boundary_disposition"
        ] = "excluded"
        excluded_support["source_designs"][1]["assertions"][0][
            "supporting_source_bindings"
        ] = [
            {
                "source_row_id": "SRC-001",
                "evidence_role": "definition",
                "exact_source_fragment": "Раздел 1",
            }
        ]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "cannot declare excluded row SRC-001 as support",
        ):
            validate_semantic_design_binding(
                self._context(),
                boundary,
                excluded_support,
            )

    def test_xhtml_requirement_evidence_requires_sentinels_and_code_token(self) -> None:
        for field, value in (
            ("evidence_source_path", "source/main.pdf"),
            ("evidence_locator", "page:1"),
        ):
            with self.subTest(field=field):
                design = self._design()
                design["source_designs"][1]["assertions"][0][
                    "requirement_code_evidence"
                ][0][field] = value
                with self.assertRaisesRegex(
                    SemanticDesignBridgeError,
                    "none_required PDF evidence fields",
                ):
                    self._validate(design)

        context = self._context()
        context["source_rows"][1]["bounded_source_text"] += " BSR 10."
        self._bind_context(context)
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = "BSR 10."
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "literal requirement-code token",
        ):
            validate_semantic_design_binding(context, self._boundary(), design)

        duplicate = self._design()
        evidence = duplicate["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ]
        evidence.append(copy.deepcopy(evidence[0]))
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "cover assertion codes exactly",
        ):
            self._validate(duplicate)

        wrong_row = self._design()
        wrong_row["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["source_row_id"] = "SRC-003"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "owning source row",
        ):
            self._validate(wrong_row)

    def test_pdf_only_requirement_code_uses_exact_registered_parity_evidence(self) -> None:
        def fixture() -> tuple[dict[str, object], dict[str, object]]:
            context = self._context()
            context["source_rows"][1]["bounded_source_text"] = str(
                context["source_rows"][1]["bounded_source_text"]
            ).replace("BSR 1. ", "")
            context["main_ft_pdf"] = "source/main.pdf"
            context["sources"].append(
                {
                    "path": "source/main.pdf",
                    "role": "main-ft-pdf",
                    "manifest_binding": "structural-visual-parity",
                }
            )
            context["parity"] = [
                {
                    "requirement_code": "BSR 1",
                    "docx_locator": "none_required",
                    "xhtml_locator": "row:SRC-002",
                    "pdf_locator": "page:3",
                    "status": "pdf-only",
                }
            ]
            self._bind_context(context)
            design = self._design()
            design["prepared_context_sha256"] = prepared_context_sha256(context)
            design["source_designs"][1]["assertions"][0][
                "requirement_code_evidence"
            ][0].update(
                {
                    "provenance_role": "pdf-parity",
                    "exact_source_fragment": "none_required",
                    "evidence_source_path": "source/main.pdf",
                    "evidence_locator": "page:3",
                }
            )
            return context, design

        context, design = fixture()
        receipt = validate_semantic_design_binding(
            context,
            self._boundary(),
            design,
        )
        self.assertEqual("verified", receipt["status"])

        mutations = {
            "fragment": lambda context, binding: binding.update(
                {"exact_source_fragment": "BSR 1."}
            ),
            "pdf-path": lambda context, binding: binding.update(
                {"evidence_source_path": "source/other.pdf"}
            ),
            "locator-form": lambda context, binding: binding.update(
                {"evidence_locator": "pdf-page:3"}
            ),
            "parity-locator": lambda context, binding: binding.update(
                {"evidence_locator": "page:4"}
            ),
            "unregistered-role": lambda context, binding: context["sources"][-1].update(
                {"manifest_binding": "supporting-material"}
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                context, design = fixture()
                binding = design["source_designs"][1]["assertions"][0][
                    "requirement_code_evidence"
                ][0]
                mutate(context, binding)
                self._bind_context(context)
                design["prepared_context_sha256"] = prepared_context_sha256(context)
                with self.assertRaises(SemanticDesignBridgeError):
                    validate_semantic_design_binding(
                        context,
                        self._boundary(),
                        design,
                    )

    def test_orphan_atom_obligation_link_is_rejected(self) -> None:
        design = self._design()
        design["obligations"][0]["linked_atom_id"] = "ATOM-orphan"
        with self.assertRaisesRegex(SemanticDesignBridgeError, "linked_atom_id"):
            self._validate(design)

    def test_applicability_requires_exact_thirteen_dimensions(self) -> None:
        design = self._design()
        design["applicability"].pop()
        with self.assertRaisesRegex(SemanticDesignBridgeError, "exact 13 dimensions"):
            self._validate(design)

    def test_empty_non_testable_design_uses_not_applicable_traceability(self) -> None:
        context = {
            "version": 1,
            "package_id": "WP-99",
            "scope_slug": "context-only",
            "scope_boundary": {
                "target": "Сохранить структурный контекст.",
                "include": ["Контекст раздела без исполняемого поведения."],
                "exclude": ["Функциональные требования других разделов."],
            },
            "mockup_locators": [],
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "field_or_action": "Заголовок раздела",
                    "source_ref": "section 1",
                    "bounded_source_text": "Раздел 1. Структурный заголовок.",
                    "requirement_codes_hint": [],
                    "in_scope_hint": "no; context-only regression fixture",
                }
            ],
            "sources": [],
            "approved_clarifications": [],
            "source_table_column_semantics": [],
            "expected_dependencies": [],
            "dependency_aliases": {},
            "dependency_alias_provenance": {},
            "scope_execution_facts": {
                "version": 1,
                "bounded_scope_kind": "single-section",
                "expected_testable_assertion_count": 0,
                "expected_tc_count": 0,
                "internal_package_count": 1,
                "has_heterogeneous_integrations": False,
                "has_large_dictionary": False,
                "mockups_ready": True,
            },
        }
        self._bind_context(context)
        boundary = {
            "version": 2,
            "status": "ready",
            "blocking_reason": "none_required",
            "scope_summary": "Сохранён только структурный контекст раздела.",
            "scope_boundary": copy.deepcopy(context["scope_boundary"]),
            "source_decisions": [
                {
                    "source_row_id": "SRC-001",
                    "disposition": "context",
                    "requirement_codes": [],
                    "rationale": (
                        "Строка сохранена только как структурный контекст раздела."
                    ),
                }
            ],
            "dependencies": [],
            "gaps": [],
            "mockup_locators": [],
        }

        design, receipt = materialize_non_testable_semantic_shard(context, boundary)

        self.assertEqual("verified", receipt["status"])
        self.assertEqual([], design["obligations"])
        traceability = next(
            item
            for item in design["applicability"]
            if item["dimension"] == "traceability"
        )
        self.assertEqual("no", traceability["applicable"])
        self.assertEqual([], traceability["linked_atoms"])
        self.assertEqual([], traceability["linked_test_cases"])

    def test_non_testable_materializer_rejects_included_row(self) -> None:
        with self.assertRaisesRegex(
            SemanticDesignShardingError,
            "owns included rows",
        ):
            materialize_non_testable_semantic_shard(
                self._context(),
                self._boundary(),
            )

    def test_applicability_tc_must_exercise_declared_dimension(self) -> None:
        design = self._design()
        rows = {item["dimension"]: item for item in design["applicability"]}
        rows["accessibility-ui"].update(
            applicable="yes",
            source_ref="BSR 1",
            reason="Forged dimension link.",
            linked_atoms=["ATOM-002"],
            linked_test_cases=["TC-001"],
        )
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "accessibility-ui is not exercised",
        ):
            self._validate(design)

    def test_applicability_inverse_covers_every_pair_and_traceability_chain(
        self,
    ) -> None:
        missing_dimension = self._design()
        rows = {
            item["dimension"]: item for item in missing_dimension["applicability"]
        }
        rows["status-lifecycle"].update(
            applicable="no",
            source_ref="none_required",
            reason="Ошибочно пропущена применимая размерность.",
            linked_atoms=[],
            linked_test_cases=[],
        )
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "status-lifecycle must cover every compiled ATOM/TC pair",
        ):
            self._validate(missing_dimension)

        missing_trace = self._design()
        trace = next(
            item
            for item in missing_trace["applicability"]
            if item["dimension"] == "traceability"
        )
        trace["linked_atoms"] = ["ATOM-002"]
        trace["linked_test_cases"] = ["TC-001"]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "traceability applicability must cover every compiled ATOM/TC chain",
        ):
            self._validate(missing_trace)

        noncanonical = self._design()
        noncanonical["obligations"][1]["design_dimension"] = "action-flow"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "design_dimension is outside the allowed enum|must use one canonical",
        ):
            self._validate(noncanonical)

    def test_reset_requires_observed_changed_prestate(self) -> None:
        for field, value in (
            ("initial_condition_index", 99),
            ("changed_state_setup", "short"),
            ("pre_action_state_oracle", "short"),
            ("state_relation", "none_required"),
        ):
            with self.subTest(field=field):
                design = self._design()
                design["reset_lifecycle_bindings"][0][field] = value
                with self.assertRaises(SemanticDesignBridgeError):
                    self._validate(design)

    def test_context_reset_evidence_binds_to_included_reset_assertion(self) -> None:
        context = self._context()
        reset_fragment = (
            "Поле «Статус». Reset applies after the supporting action."
        )
        context["source_rows"][0]["bounded_source_text"] += f" {reset_fragment}"
        self._bind_context(context)
        boundary = self._boundary()
        boundary["dependencies"][0]["source_row_ids"] = ["SRC-001", "SRC-002"]
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        design["dependency_bindings"][0]["source_row_ids"] = [
            "SRC-001",
            "SRC-002",
        ]
        assertion = design["source_designs"][1]["assertions"][0]
        assertion["supporting_source_bindings"] = [
            {
                "source_row_id": "SRC-001",
                "evidence_role": "constraint",
                "exact_source_fragment": reset_fragment,
            }
        ]

        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "state-change evidence requires its own",
        ):
            validate_semantic_design_binding(
                context,
                boundary,
                design,
            )

        obligation = design["obligations"][0]
        obligation.update(
            property_type="reset",
            obligation_class="clear",
            coverage_class="reset",
        )
        design["reset_lifecycle_bindings"].append(
            {
                "obligation_id": "OBL-001",
                "binding_kind": "reset",
                "initial_condition_index": 0,
                "changed_state_setup": (
                    "Make the visible value differ from the captured value."
                ),
                "pre_action_state_oracle": (
                    "Observe the changed value before invoking reset."
                ),
                "state_relation": "different-from-captured-initial",
            }
        )
        receipt = validate_semantic_design_binding(
            context,
            boundary,
            design,
        )
        self.assertEqual("verified", receipt["status"])

    def test_each_reset_assertion_requires_its_own_guarded_obligation(self) -> None:
        design = self._design()
        duplicate = copy.deepcopy(design["source_designs"][2]["assertions"][0])
        duplicate.update(
            assertion_id="ASSERT-004",
            atom_id="ATOM-004",
            source_property_id="PROP-004",
            obligation_ids=["OBL-003"],
        )
        design["source_designs"][2]["assertions"].append(duplicate)
        obligation = copy.deepcopy(design["obligations"][1])
        obligation.update(
            obligation_id="OBL-003",
            linked_atom_id="ATOM-004",
            source_property_id="PROP-004",
            planned_tc_id="TC-003",
            property_type="action",
            obligation_class="positive",
            coverage_class="action-flow",
        )
        design["obligations"].append(obligation)

        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "ASSERT-004 state-change evidence requires its own",
        ):
            self._validate(design)

    def test_dictionary_extraction_and_obligation_coverage_are_required(self) -> None:
        value_drift = self._design()
        value_drift["dictionaries"][0]["active_values"] = ["Неизвестно"]
        with self.assertRaisesRegex(SemanticDesignBridgeError, "values drifted"):
            self._validate(value_drift)

        uncovered = self._design()
        uncovered["obligations"][0]["dictionary_refs"] = []
        uncovered["obligations"][0]["dictionary_coverage"] = "none_required"
        with self.assertRaisesRegex(SemanticDesignBridgeError, "every extracted dictionary"):
            self._validate(uncovered)

    def test_dictionary_obligation_must_share_its_source_evidence_chain(self) -> None:
        misbound = self._design()
        misbound["obligations"][0]["dictionary_refs"] = []
        misbound["obligations"][0]["dictionary_coverage"] = "none_required"
        misbound["obligations"][1]["dictionary_refs"] = ["DICT-001"]
        misbound["obligations"][1]["dictionary_coverage"] = "reference-only"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "outside its ASSERT->ATOM->OBL evidence chain",
        ):
            self._validate(misbound)

    def test_external_dynamic_dictionary_stays_dependency_only(self) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] = str(
            context["source_rows"][1]["bounded_source_text"]
        ).replace("по справочнику Статусы:", "по справочнику «Статусы»:")
        context.pop("dictionary_inventory")
        reference_path = "fts/demo/work/vendor-references/dadata-reference.md"
        context["sources"].append(
            {
                "path": reference_path,
                "role": "external-vendor-reference",
                "manifest_binding": "supporting-material",
            }
        )
        context["external_dictionary_bindings"] = [
            {
                "dictionary_name": "Статусы",
                "binding_type": "external-dynamic-dictionary",
                "provider": "DaData",
                "reference_path": reference_path,
                "reference_url": "https://example.test/dadata/statuses",
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
                "name": "Статусы",
                "source_row_ids": ["SRC-002"],
                "resolution": "external-dynamic",
                "target_source_row_ids": [],
                "exact_source_fragments": ["справочнику «Статусы»"],
            }
        ]
        self._bind_context(context)

        boundary = self._boundary()
        boundary["dependencies"].append(
            {
                "dependency_id": "DEP-002",
                "kind": "dictionary",
                "name": "Статусы",
                "source_row_ids": ["SRC-002"],
                "resolution": "external-dynamic",
                "target_source_row_ids": [],
                "exact_source_fragments": ["справочнику «Статусы»"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Значения поставляет авторитетный динамический API.",
            }
        )

        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["scope_boundary_decision_sha256"] = canonical_payload_sha256(boundary)
        design["dictionaries"] = []
        design["obligations"][0]["dictionary_refs"] = []
        design["obligations"][0]["dictionary_coverage"] = "reference-only"
        dynamic_assertion = design["source_designs"][1]["assertions"][0]
        dynamic_assertion["condition_clauses"].append("справочнику «Статусы»")
        dynamic_assertion["clause_evidence"].append(
            {
                "clause_kind": "condition",
                "clause_index": 1,
                "source_row_id": "SRC-002",
                "exact_source_fragment": "справочнику «Статусы»",
            }
        )
        design["dependency_bindings"].append(
            {
                **copy.deepcopy(boundary["dependencies"][1]),
                "semantic_disposition": "bound",
                "linked_assertion_ids": ["ASSERT-002"],
                "linked_atom_ids": ["ATOM-002"],
                "linked_obligation_ids": ["OBL-001"],
                "mapping_rationale": (
                    "Динамическая зависимость связана с проверкой выбора значения."
                ),
            }
        )

        diagnostics = semantic_design_transport_diagnostics(design)
        self.assertIn(
            "external-dynamic-static-coverage-alias",
            {item["code"] for item in diagnostics["findings"]},
        )
        normalized, repairs = normalize_semantic_design_transport(design)
        self.assertEqual(
            "none_required",
            normalized["obligations"][0]["dictionary_coverage"],
        )
        self.assertIn(
            "canonicalize-external-dynamic-dictionary-coverage",
            {item["rule"] for item in repairs["repairs"]},
        )
        receipt = validate_semantic_design_binding(context, boundary, normalized)
        self.assertEqual("verified", receipt["status"])
        self.assertEqual(0, receipt["dictionary_count"])

    def test_typed_clarification_must_validate_and_bind_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence = root / "clarification.md"
            evidence.write_text("authoritative answer", encoding="utf-8")
            context = self._context()
            context["sources"].append(
                {
                    "path": "clarification.md",
                    "role": "approved-clarification",
                    "manifest_binding": "approved-clarification",
                }
            )
            answer = "Статус выбирается только из полного справочника."
            record = {
                "clarification_id": "CLR-001",
                "gap_id": "GAP-001",
                "scope_slug": context["scope_slug"],
                "requirement_codes": ["BSR 1"],
                "authority": "user",
                "response_status": "answered",
                "response_type": "user-confirmed",
                "answered_at": "2026-07-17",
                "exact_answer": answer,
                "exact_answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
                "evidence_source_path": "clarification.md",
                "evidence_source_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                "binding_scope": "requirement-code",
                "source_row_ids": [],
            }
            context["approved_clarifications"] = [record]
            self._bind_context(context)
            clarifications = load_approved_clarifications(root, context)
            self.assertEqual("CLR-001", clarifications[0]["clarification_id"])

            design = self._design()
            design["prepared_context_sha256"] = prepared_context_sha256(context)
            design["source_designs"][1]["assertions"][0][
                "clarification_clause_bindings"
            ] = [
                {
                    "clarification_id": "CLR-001",
                    "clause_kind": "oracle",
                    "clause_index": 0,
                    "requirement_codes": ["BSR 1"],
                    "exact_answer_sha256": record["exact_answer_sha256"],
                    "binding_scope": "requirement-code",
                    "source_row_ids": [],
                }
            ]
            receipt = validate_semantic_design_binding(
                context,
                self._boundary(),
                design,
                clarifications=clarifications,
            )
            self.assertEqual(1, receipt["approved_clarification_count"])

            design["source_designs"][1]["assertions"][0][
                "clarification_clause_bindings"
            ][0]["exact_answer_sha256"] = "0" * 64
            with self.assertRaisesRegex(SemanticDesignBridgeError, "provenance mismatch"):
                validate_semantic_design_binding(
                    context,
                    self._boundary(),
                    design,
                    clarifications=clarifications,
                )

            malformed = copy.deepcopy(context)
            malformed["approved_clarifications"][0]["unexpected"] = True
            with self.assertRaisesRegex(SemanticDesignBridgeError, "invalid approved clarification"):
                load_approved_clarifications(root, malformed)

    def test_dependency_aliases_require_exact_clarification_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence = root / "clarification.md"
            evidence.write_text(
                "\n".join(
                    (
                        "# Approved clarification",
                        "",
                        "| clarification_id | gap_id | scope_slug | requirement_codes | related_ft_reference | question | needed_for | blocking | requested_from | authority | user_response | response_status | response_type | updated_at |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| `CLR-001` | `GAP-001` | `employment-main-work` | BSR 1 | BSR 1, поле «Статус» | Являются ли названия одним полем? | Разрешение alias | `yes` | `user` | `user` | «Тип занятости» — это то же поле, что «Статус». | `answered` | `user-confirmed` | `2026-07-18` |",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            context = self._context()
            context["sources"].append(
                {
                    "path": "clarification.md",
                    "role": "approved-clarification",
                    "manifest_binding": "approved-clarification",
                }
            )
            context["dependency_aliases"] = {
                "Тип занятости": "Статус",
            }
            context["dependency_alias_provenance"] = {
                "Тип занятости": "CLR-001",
            }
            self._bind_context(context)

            clarifications = load_approved_clarifications(root, context)

            self.assertEqual(["CLR-001"], [item["clarification_id"] for item in clarifications])

            cases = (
                (
                    "missing",
                    {},
                    "keys must exactly match",
                ),
                (
                    "extra",
                    {
                        "Тип занятости": "CLR-001",
                        "Лишний alias": "CLR-001",
                    },
                    "keys must exactly match",
                ),
                (
                    "unknown-id",
                    {"Тип занятости": "CLR-404"},
                    "references unknown approved clarification ids: CLR-404",
                ),
                (
                    "not-an-object",
                    [],
                    "dependency_alias_provenance must be an object",
                ),
            )
            for label, provenance, expected_error in cases:
                with self.subTest(label=label):
                    malformed = copy.deepcopy(context)
                    malformed["dependency_alias_provenance"] = provenance
                    self._bind_context(malformed)
                    with self.assertRaisesRegex(
                        SemanticDesignBridgeError,
                        expected_error,
                    ):
                        load_approved_clarifications(root, malformed)

    def test_exact_cleanup_clarification_requires_a_guarded_readd_lifecycle_tc(
        self,
    ) -> None:
        answer = "После удаления заполненного блока и последующего добавления нового, поля должны быть пустыми."
        clarification = {
            "clarification_id": "CLR-LIFECYCLE-001",
            "gap_id": "GAP-LIFECYCLE-001",
            "scope_slug": self._context()["scope_slug"],
            "requirement_codes": ["BSR 2"],
            "authority": "user",
            "response_status": "answered",
            "response_type": "user-confirmed",
            "answered_at": "2026-07-17",
            "exact_answer": answer,
            "exact_answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
            "evidence_source_path": "clarification.md",
            "evidence_source_sha256": hashlib.sha256(b"evidence").hexdigest(),
            "binding_scope": "requirement-code",
            "source_row_ids": [],
        }

        def fixture() -> dict[str, object]:
            design = self._design()
            lifecycle_assertion = self._assertion(
                assertion_id="ASSERT-004",
                atom_id="ATOM-004",
                property_id="PROP-004",
                field="Повторно добавленный блок",
                source_ref="BSR 2 + CLR-LIFECYCLE-001",
                codes=["BSR 2"],
                conditions=["Заполненный блок существует до удаления"],
                actions=["Удалить заполненный блок, затем добавить новый блок"],
                oracles=["Поля нового блока пустые"],
                obligation_ids=["OBL-003"],
                requirement_evidence=[
                    {
                        "requirement_code": "BSR 2",
                        "source_row_id": "SRC-003",
                        "provenance_role": "xhtml-row",
                        "exact_source_fragment": "BSR 2.",
                        "evidence_source_path": "none_required",
                        "evidence_locator": "none_required",
                    }
                ],
                evidence=[
                    {
                        "clause_kind": "condition",
                        "clause_index": 0,
                        "source_row_id": "SRC-003",
                        "exact_source_fragment": "поле заполнено изменённым значением",
                    },
                    {
                        "clause_kind": "action",
                        "clause_index": 0,
                        "source_row_id": "SRC-003",
                        "exact_source_fragment": "при нажатии кнопки «Очистить»",
                    },
                    {
                        "clause_kind": "oracle",
                        "clause_index": 0,
                        "source_row_id": "SRC-003",
                        "exact_source_fragment": "поле очищается и становится пустым",
                    },
                ],
            )
            lifecycle_assertion["clarification_clause_bindings"] = [
                {
                    "clarification_id": "CLR-LIFECYCLE-001",
                    "clause_kind": clause_kind,
                    "clause_index": 0,
                    "requirement_codes": ["BSR 2"],
                    "exact_answer_sha256": clarification["exact_answer_sha256"],
                    "binding_scope": "requirement-code",
                    "source_row_ids": [],
                }
                for clause_kind in ("condition", "action", "oracle")
            ]
            design["source_designs"][2]["assertions"].append(lifecycle_assertion)
            lifecycle_obligation = copy.deepcopy(design["obligations"][1])
            lifecycle_obligation.update(
                obligation_id="OBL-003",
                linked_atom_id="ATOM-004",
                source_property_id="PROP-004",
                property_type="repeatable-block-lifecycle",
                obligation_class="readd-after-delete",
                required_behavior=(
                    "После удаления заполненного блока новый блок имеет пустые поля."
                ),
                source_ref="CLR-LIFECYCLE-001",
                planned_tc_id="TC-003",
                review_notes="Точное правило подтверждено пользователем.",
                design_dimension="status-lifecycle",
                planned_check=(
                    "Заполнить блок, удалить его и добавить новый экземпляр."
                ),
                check_type="action-flow",
                coverage_class="repeatable-block-lifecycle",
                input_class="filled repeatable block",
                single_expected_behavior="Поля нового блока пустые.",
                oracle_source="CLR-LIFECYCLE-001",
                test_data="Заполненный исходный блок",
            )
            design["obligations"].append(lifecycle_obligation)
            design["reset_lifecycle_bindings"].append(
                {
                    "obligation_id": "OBL-003",
                    "binding_kind": "readd-after-delete",
                    "initial_condition_index": 0,
                    "changed_state_setup": (
                        "Удалить заполненный блок, затем добавить новый блок."
                    ),
                    "pre_action_state_oracle": (
                        "Убедиться, что исходный блок заполнен перед удалением."
                    ),
                    "state_relation": "different-from-captured-initial",
                }
            )
            applicability = {
                item["dimension"]: item for item in design["applicability"]
            }
            applicability["status-lifecycle"]["linked_atoms"].append("ATOM-004")
            applicability["status-lifecycle"]["linked_test_cases"].append("TC-003")
            applicability["traceability"]["linked_atoms"].append("ATOM-004")
            applicability["traceability"]["linked_test_cases"].append("TC-003")
            return design

        design = fixture()
        receipt = validate_semantic_design_binding(
            self._context(),
            self._boundary(),
            design,
            clarifications=[clarification],
        )
        self.assertEqual("verified", receipt["status"])

        unrelated = fixture()
        lifecycle = unrelated["source_designs"][2]["assertions"][1]
        reset = unrelated["source_designs"][2]["assertions"][0]
        reset["clarification_clause_bindings"] = lifecycle[
            "clarification_clause_bindings"
        ]
        lifecycle["clarification_clause_bindings"] = []
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "bound to unrelated assertion",
        ):
            validate_semantic_design_binding(
                self._context(),
                self._boundary(),
                unrelated,
                clarifications=[clarification],
            )

        unguarded = fixture()
        obligation = unguarded["obligations"][2]
        obligation.update(
            property_type="action",
            obligation_class="positive",
            coverage_class="action-flow",
        )
        unguarded["reset_lifecycle_bindings"] = [
            item
            for item in unguarded["reset_lifecycle_bindings"]
            if item["obligation_id"] != "OBL-003"
        ]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "separate guarded OBL/TC",
        ):
            validate_semantic_design_binding(
                self._context(),
                self._boundary(),
                unguarded,
                clarifications=[clarification],
            )

    def test_dependency_binding_must_preserve_authoritative_full_chain(self) -> None:
        design = self._design()
        receipt = self._validate(design)
        self.assertEqual(1, receipt["dependency_binding_count"])

        for field, replacement in (
            ("name", "Другой статус"),
            ("linked_atom_ids", ["ATOM-003"]),
            ("linked_obligation_ids", []),
        ):
            with self.subTest(field=field):
                drifted = copy.deepcopy(design)
                drifted["dependency_bindings"][0][field] = replacement
                with self.assertRaisesRegex(
                    SemanticDesignBridgeError,
                    "drifted|ASSERT->ATOM->OBL",
                ):
                    self._validate(drifted)

    def test_dependency_binding_requires_authoritative_fragment_evidence(self) -> None:
        design = self._design()
        unbound_fragment = copy.deepcopy(design)
        assertion = unbound_fragment["source_designs"][1]["assertions"][0]
        assertion["condition_clauses"] = ["При выборе значения"]
        assertion["clause_evidence"][0][
            "exact_source_fragment"
        ] = "При выборе значения"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "no exact dependency fragment evidence",
        ):
            self._validate(unbound_fragment)

    def test_oracle_registry_preserves_each_atomic_signal_and_scope_order(self) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] += (
            " Формат значения: только цифры. Поле обязательное."
        )
        self._bind_context(context)
        boundary = self._boundary()
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        assertion = design["source_designs"][1]["assertions"][0]
        assertion["requirement_code_evidence"][0][
            "exact_source_fragment"
        ] = context["source_rows"][1]["bounded_source_text"]
        obligation_template = design["obligations"][0]
        oracle_obligations = []
        for obligation_id, planned_tc_id, scope_id, obligation_class in (
            ("OBL-003", "TC-003", "SO-NEG-001", "invalid-format"),
            ("OBL-004", "TC-004", "SO-NEG-002", "invalid-numeric"),
            ("OBL-005", "TC-005", "SO-REQ-001", "empty-required"),
        ):
            obligation = copy.deepcopy(obligation_template)
            obligation.update(
                obligation_id=obligation_id,
                property_type="input-validation",
                obligation_class=obligation_class,
                required_behavior="Reject one independently identified invalid class.",
                planned_tc_id=planned_tc_id,
                design_dimension="boundary",
                planned_check="Execute one independently identified invalid class.",
                check_type="negative",
                coverage_class=obligation_class,
                input_class=obligation_class,
                single_expected_behavior="The source-backed oracle is observed.",
                test_data="one atomic invalid value",
                dictionary_refs=[],
                dictionary_coverage="none_required",
                scope_obligation_ids=[scope_id],
            )
            oracle_obligations.append(obligation)
            assertion["obligation_ids"].append(obligation_id)
        design["obligations"].extend(oracle_obligations)
        design["dependency_bindings"][0]["linked_obligation_ids"] = [
            "OBL-001",
            "OBL-003",
            "OBL-004",
            "OBL-005",
        ]
        applicability = {
            item["dimension"]: item for item in design["applicability"]
        }
        applicability["boundary"].update(
            applicable="yes",
            source_ref="BSR 1",
            reason="Три атомарные проверки граничных ограничений.",
            linked_atoms=["ATOM-002"],
            linked_test_cases=["TC-003", "TC-004", "TC-005"],
        )
        applicability["traceability"].update(
            linked_atoms=["ATOM-002", "ATOM-003"],
            linked_test_cases=[
                "TC-001",
                "TC-002",
                "TC-003",
                "TC-004",
                "TC-005",
            ],
        )
        design["negative_oracles"] = [
            {
                "signal_id": f"SIG-NEG-{index:03d}",
                "requirement_codes": ["BSR 1"],
                "scope_obligation_id": f"SO-NEG-{index:03d}",
                "source_row_id": "SRC-002",
                "source_ref": "BSR 1",
                "field_or_block": "Статус",
                "restriction_type": restriction_type,
                "negative_class": "invalid-value",
                "source_statement": "Формат значения: только цифры.",
                "representative_invalid_value": "A",
                "observable_oracle_found": "yes",
                "oracle_source": "BSR 1",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": f"TC-00{index + 2}",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "Сохранить точный сигнал и связанную цепочку.",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-002",
                "linked_obligation_id": f"OBL-00{index + 2}",
            }
            for index, restriction_type in ((1, "format"), (2, "numeric"))
        ]
        design["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": ["BSR 1"],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-002",
                "source_ref": "BSR 1",
                "field_or_block": "Статус",
                "restriction_type": "requiredness",
                "requiredness_source": "Поле обязательное.",
                "requiredness_class": "always-required",
                "required_when": "always",
                "marker_oracle_found": "yes",
                "empty_value_oracle_found": "yes",
                "oracle_source": "BSR 1",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": "TC-005",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "Сохранить точный сигнал и связанную цепочку.",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-002",
                "linked_obligation_id": "OBL-005",
            }
        ]
        receipt = validate_semantic_design_binding(context, boundary, design)
        self.assertEqual(2, receipt["negative_oracle_count"])
        self.assertEqual(1, receipt["requiredness_oracle_count"])

        missing = copy.deepcopy(design)
        missing["negative_oracles"].pop()
        with self.assertRaisesRegex(SemanticDesignBridgeError, "every eligible source signal"):
            validate_semantic_design_binding(context, boundary, missing)

        collapsed = copy.deepcopy(design)
        collapsed["negative_oracles"][1].update(
            linked_obligation_id="OBL-003",
            planned_tc_or_gap="TC-003",
        )
        with self.assertRaisesRegex(SemanticDesignBridgeError, "collapse independent"):
            validate_semantic_design_binding(context, boundary, collapsed)

        unobservable = copy.deepcopy(design)
        unobservable["negative_oracles"][0]["observable_oracle_found"] = "no"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "lacks an observable oracle",
        ):
            validate_semantic_design_binding(context, boundary, unobservable)

        missing_owner_anchor = copy.deepcopy(design)
        missing_owner_anchor["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = "BSR 1."
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "exact signal evidence in its owning assertion",
        ):
            validate_semantic_design_binding(
                context,
                boundary,
                missing_owner_anchor,
            )

        reordered = copy.deepcopy(design)
        reordered["requiredness_oracles"][0]["scope_obligation_id"] = "SO-REQ-999"
        with self.assertRaisesRegex(SemanticDesignBridgeError, "scope_obligation_id drifted"):
            validate_semantic_design_binding(context, boundary, reordered)

    def test_oracle_signal_codes_must_be_owned_and_multicode_ambiguity_blocks(
        self,
    ) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] += " Поле обязательное."
        self._bind_context(context)
        misbound = self._design()
        misbound["prepared_context_sha256"] = prepared_context_sha256(context)
        misbound["obligations"][1].update(
            check_type="negative",
            scope_obligation_ids=["SO-REQ-001"],
        )
        misbound["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": ["BSR 1"],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-002",
                "source_ref": "BSR 1",
                "field_or_block": "Статус",
                "restriction_type": "requiredness",
                "requiredness_source": "Поле обязательное.",
                "requiredness_class": "always-required",
                "required_when": "always",
                "marker_oracle_found": "yes",
                "empty_value_oracle_found": "yes",
                "oracle_source": "BSR 1",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": "TC-002",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "Не связывать сигнал с assertion другого требования.",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-003",
                "linked_obligation_id": "OBL-002",
            }
        ]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "requirement codes are not owned by its linked assertion",
        ):
            validate_semantic_design_binding(
                context,
                self._boundary(),
                misbound,
            )

        ambiguous_context = self._context()
        ambiguous_context["source_rows"][1]["bounded_source_text"] = (
            "Поле обязательное. BSR 9. Дополнительное правило. "
            + ambiguous_context["source_rows"][1]["bounded_source_text"]
        )
        ambiguous_context["source_rows"][1]["requirement_codes_hint"] = [
            "BSR 1",
            "BSR 9",
        ]
        self._bind_context(ambiguous_context)
        ambiguous_boundary = self._boundary()
        ambiguous_boundary["source_decisions"][1]["requirement_codes"] = [
            "BSR 1",
            "BSR 9",
        ]
        ambiguous = self._design()
        ambiguous["prepared_context_sha256"] = prepared_context_sha256(
            ambiguous_context
        )
        ambiguous["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            ambiguous_boundary
        )
        source_design = ambiguous["source_designs"][1]
        source_design["requirement_codes"] = ["BSR 1", "BSR 9"]
        assertion = source_design["assertions"][0]
        assertion["requirement_codes"] = ["BSR 1", "BSR 9"]
        assertion["requirement_code_evidence"][0][
            "exact_source_fragment"
        ] = ambiguous_context["source_rows"][1]["bounded_source_text"]
        assertion["requirement_code_evidence"].append(
            {
                "requirement_code": "BSR 9",
                "source_row_id": "SRC-002",
                "provenance_role": "xhtml-row",
                "exact_source_fragment": "BSR 9.",
                "evidence_source_path": "none_required",
                "evidence_locator": "none_required",
            }
        )
        ambiguous["obligations"][0].update(
            check_type="negative",
            scope_obligation_ids=["SO-REQ-001"],
        )
        ambiguous["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": [],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-002",
                "source_ref": "BSR 1",
                "field_or_block": "Статус",
                "restriction_type": "requiredness",
                "requiredness_source": "Поле обязательное.",
                "requiredness_class": "always-required",
                "required_when": "always",
                "marker_oracle_found": "yes",
                "empty_value_oracle_found": "yes",
                "oracle_source": "BSR 1",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": "TC-001",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "Сначала устранить неоднозначность кода требования.",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-002",
                "linked_obligation_id": "OBL-001",
            }
        ]
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "ambiguous requirement-code assignment",
        ):
            validate_semantic_design_binding(
                ambiguous_context,
                ambiguous_boundary,
                ambiguous,
            )

    def test_candidate_signal_codes_bind_from_unique_same_row_donor(self) -> None:
        context = self._context()
        row = context["source_rows"][1]
        row["bounded_source_text"] += " Формат значения: только цифры."
        self._bind_context(context)
        boundary = self._boundary()
        signal = _source_signal_registry(
            [row],
            {"SRC-002": ["BSR 1"]},
        )["negative"][0]
        payload = {
            "source_designs": [
                {
                    "source_row_id": "SRC-002",
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-DONOR",
                            "atom_id": "ATOM-DONOR",
                            "requirement_codes": ["BSR 1"],
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": "BSR 1",
                                    "source_row_id": "SRC-002",
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": "BSR 1.",
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                }
                            ],
                            "clause_evidence": [],
                        },
                        {
                            "assertion_id": "ASSERT-CANDIDATE",
                            "atom_id": "ATOM-CANDIDATE",
                            "requirement_codes": [],
                            "requirement_code_evidence": [],
                            "oracle_clauses": [
                                "Ограничение нарушено; точный UI-отклик требует "
                                "калибровки."
                            ],
                            "clause_evidence": [
                                {
                                    "clause_kind": "action",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-002",
                                    "exact_source_fragment": signal["literal_anchor"],
                                },
                                {
                                    "clause_kind": "oracle",
                                    "clause_index": 0,
                                    "source_row_id": "SRC-002",
                                    "exact_source_fragment": (
                                        "candidate-ui-calibration: точный UI-отклик "
                                        "не выдумывается."
                                    ),
                                }
                            ],
                        },
                    ],
                }
            ],
            "obligations": [],
            "negative_oracles": [
                {
                    **signal,
                    "decision": "candidate_tc_required",
                    "oracle_status": "ui-calibration-required",
                    "oracle_source": "not_found",
                    "source_statement": "Формат значения: только цифры.",
                    "linked_atom_id": "ATOM-CANDIDATE",
                    "linked_obligation_id": "OBL-CANDIDATE",
                }
            ],
            "requiredness_oracles": [],
        }
        diagnostics = semantic_design_transport_diagnostics(
            payload,
            context=context,
            boundary=boundary,
        )
        normalized, receipt = normalize_semantic_design_transport(
            payload,
            context=context,
            boundary=boundary,
        )
        candidate = normalized["source_designs"][0]["assertions"][1]
        self.assertIn(
            "candidate-signal-code-binding-missing",
            [item["code"] for item in diagnostics["findings"]],
        )
        self.assertIn(
            "negative-candidate-clause-evidence-alias",
            [item["code"] for item in diagnostics["findings"]],
        )
        self.assertEqual(["BSR 1"], candidate["requirement_codes"])
        self.assertEqual(
            ["BSR 1"],
            [
                item["requirement_code"]
                for item in candidate["requirement_code_evidence"]
            ],
        )
        self.assertIn(
            "bind-candidate-signal-codes-to-owning-assertion",
            [item["rule"] for item in receipt["repairs"]],
        )
        self.assertEqual(
            "Формат значения: только цифры.",
            candidate["clause_evidence"][1]["exact_source_fragment"],
        )
        self.assertIn(
            "bind-negative-candidate-clause-evidence-to-source-row",
            [item["rule"] for item in receipt["repairs"]],
        )

    def test_typed_cell_properties_are_code_less_atomic_and_post_validated(self) -> None:
        context = self._context()
        header = context["source_rows"][0]
        row = context["source_rows"][1]
        header["source_locator"] = "/*/*[1]"
        row["source_locator"] = "/*/*[2]"
        row["bounded_source_text"] = (
            "Статус Да Да BSR 9. Дополнительное правило. "
            + row["bounded_source_text"]
        )
        row["requirement_codes_hint"] = ["BSR 1", "BSR 9"]
        row["physical_table_cells"] = [
            {
                "physical_column_index": 1,
                "source_cell_locator": "/*/*[2]/*[1]",
                "element_kind": "td",
                "bounded_source_text": "Статус",
            },
            {
                "physical_column_index": 2,
                "source_cell_locator": "/*/*[2]/*[2]",
                "element_kind": "td",
                "bounded_source_text": "Да",
            },
            {
                "physical_column_index": 3,
                "source_cell_locator": "/*/*[2]/*[3]",
                "element_kind": "td",
                "bounded_source_text": "Да",
            },
        ]
        note_fragment = "О означает обязательность; Р означает редактируемость."
        row["field_properties"] = {
            "requiredness": {
                "property_id": "FP-SRC-002-REQUIREDNESS-REQUIRED",
                "table_id": "DEMO-TABLE",
                "physical_column_index": 2,
                "normalized_value": "required",
                "source_value": "Да",
                "source_cell_locator": "/*/*[2]/*[2]",
                "header_source_row_id": "SRC-001",
                "header_value": "О",
                "header_cell_locator": "/*/*[1]/*[2]",
                "interpretation_source": "source/main.xhtml",
                "interpretation_source_fragment": note_fragment,
            },
            "editability": {
                "property_id": "FP-SRC-002-EDITABILITY-EDITABLE",
                "table_id": "DEMO-TABLE",
                "physical_column_index": 3,
                "normalized_value": "editable",
                "source_value": "Да",
                "source_cell_locator": "/*/*[2]/*[3]",
                "header_source_row_id": "SRC-001",
                "header_value": "Р",
                "header_cell_locator": "/*/*[1]/*[3]",
                "interpretation_source": "source/main.xhtml",
                "interpretation_source_fragment": note_fragment,
            },
        }
        context["source_table_column_semantics"] = [
            {
                "table_id": "DEMO-TABLE",
                "header_source_row_id": "SRC-001",
                "target_source_row_ids": ["SRC-002"],
                "columns": [
                    {
                        "property": "requiredness",
                        "physical_column_index": 2,
                        "expected_header": "О",
                        "value_mapping": {"Да": "required", "Нет": "optional"},
                        "interpretation_source": "source/main.xhtml",
                        "interpretation_source_fragment": note_fragment,
                    },
                    {
                        "property": "editability",
                        "physical_column_index": 3,
                        "expected_header": "Р",
                        "value_mapping": {"Да": "editable", "Нет": "read-only"},
                        "interpretation_source": "source/main.xhtml",
                        "interpretation_source_fragment": note_fragment,
                    },
                ],
            }
        ]
        self._bind_context(context)
        boundary = self._boundary()
        boundary["source_decisions"][1]["requirement_codes"] = ["BSR 1", "BSR 9"]

        registry = _source_signal_registry(
            [row],
            {"SRC-002": ["BSR 1", "BSR 9"]},
        )
        self.assertEqual([], registry["requiredness"][0]["requirement_codes"])
        self.assertEqual(
            "typed-xhtml-cell",
            registry["requiredness"][0]["source_binding"],
        )
        self.assertEqual(
            "Да",
            registry["requiredness"][0]["requiredness_source"],
        )

        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["scope_boundary_decision_sha256"] = canonical_payload_sha256(boundary)
        source_design = design["source_designs"][1]
        source_design["requirement_codes"] = ["BSR 1", "BSR 9"]
        base_assertion = source_design["assertions"][0]
        base_assertion["requirement_codes"] = ["BSR 1", "BSR 9"]
        base_assertion["requirement_code_evidence"][0][
            "exact_source_fragment"
        ] = row["bounded_source_text"]
        base_assertion["requirement_code_evidence"].append(
            {
                "requirement_code": "BSR 9",
                "source_row_id": "SRC-002",
                "provenance_role": "xhtml-row",
                "exact_source_fragment": "BSR 9.",
                "evidence_source_path": "none_required",
                "evidence_locator": "none_required",
            }
        )

        def typed_assertion(
            assertion_id: str,
            atom_id: str,
            property_id: str,
            obligation_id: str,
        ) -> dict[str, object]:
            return self._assertion(
                assertion_id=assertion_id,
                atom_id=atom_id,
                property_id=property_id,
                field="Статус",
                source_ref="BSR 1",
                codes=[],
                conditions=["Да"],
                actions=["Изменить значение типизированного поля."],
                oracles=["Изменённое значение отображается в поле."],
                obligation_ids=[obligation_id],
                requirement_evidence=[],
                evidence=[
                    {
                        "clause_kind": kind,
                        "clause_index": 0,
                        "source_row_id": "SRC-002",
                        "exact_source_fragment": "Да",
                    }
                    for kind in ("condition", "action", "oracle")
                ],
            )

        source_design["assertions"].extend(
            [
                typed_assertion(
                    "ASSERT-004",
                    "ATOM-004",
                    "FP-SRC-002-REQUIREDNESS-REQUIRED",
                    "OBL-003",
                ),
                typed_assertion(
                    "ASSERT-005",
                    "ATOM-005",
                    "FP-SRC-002-EDITABILITY-EDITABLE",
                    "OBL-004",
                ),
            ]
        )
        obligation_template = copy.deepcopy(design["obligations"][0])
        typed_obligations = []
        for (
            obligation_id,
            atom_id,
            property_id,
            property_type,
            planned_tc_id,
            check_type,
            scope_ids,
        ) in (
            (
                "OBL-003",
                "ATOM-004",
                "FP-SRC-002-REQUIREDNESS-REQUIRED",
                "requiredness",
                "TC-003",
                "negative",
                ["SO-REQ-001"],
            ),
            (
                "OBL-004",
                "ATOM-005",
                "FP-SRC-002-EDITABILITY-EDITABLE",
                "editability",
                "TC-004",
                "positive",
                [],
            ),
        ):
            obligation = copy.deepcopy(obligation_template)
            obligation.update(
                obligation_id=obligation_id,
                linked_atom_id=atom_id,
                source_property_id=property_id,
                property_type=property_type,
                obligation_class=property_type,
                required_behavior=f"Проверить {property_id}.",
                planned_tc_id=planned_tc_id,
                planned_check=f"Выполнить {property_id}.",
                check_type=check_type,
                coverage_class=property_type,
                input_class=property_type,
                single_expected_behavior=f"Подтверждено {property_id}.",
                dictionary_refs=[],
                dictionary_coverage="none_required",
                scope_obligation_ids=scope_ids,
            )
            typed_obligations.append(obligation)
        design["obligations"].extend(typed_obligations)
        applicability = {item["dimension"]: item for item in design["applicability"]}
        applicability["equivalence"]["linked_atoms"].extend(["ATOM-004", "ATOM-005"])
        applicability["equivalence"]["linked_test_cases"].extend(["TC-003", "TC-004"])
        applicability["traceability"]["linked_atoms"].extend(["ATOM-004", "ATOM-005"])
        applicability["traceability"]["linked_test_cases"].extend(["TC-003", "TC-004"])
        design["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": [],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-002",
                "source_ref": "BSR 1",
                "field_or_block": "Статус",
                "restriction_type": "requiredness",
                "requiredness_source": "Да",
                "requiredness_class": "always-required",
                "required_when": "always",
                "marker_oracle_found": "yes",
                "empty_value_oracle_found": "yes",
                "oracle_source": "typed XHTML cell",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": "TC-003",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "Сохранить точную typed-cell привязку свойства.",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-004",
                "linked_obligation_id": "OBL-003",
            }
        ]

        placeholder = copy.deepcopy(design)
        placeholder["requiredness_oracles"][0][
            "requiredness_source"
        ] = "typed-xhtml-cell"
        diagnostics = semantic_design_transport_diagnostics(
            placeholder,
            context=context,
            boundary=boundary,
        )
        normalized, normalization_receipt = normalize_semantic_design_transport(
            placeholder,
            context=context,
            boundary=boundary,
        )
        self.assertIn(
            "typed-requiredness-source-placeholder",
            [item["code"] for item in diagnostics["findings"]],
        )
        self.assertEqual(
            "Да",
            normalized["requiredness_oracles"][0]["requiredness_source"],
        )
        self.assertIn(
            "bind-typed-requiredness-source-cell-value",
            [item["rule"] for item in normalization_receipt["repairs"]],
        )

        interpretation_alias = copy.deepcopy(design)
        interpretation_alias["source_designs"][1]["assertions"][1][
            "supporting_source_bindings"
        ] = [
            {
                "source_row_id": "SRC-001",
                "evidence_role": "definition",
                "exact_source_fragment": note_fragment,
            }
        ]
        alias_diagnostics = semantic_design_transport_diagnostics(
            interpretation_alias,
            context=context,
            boundary=boundary,
        )
        normalized_alias, alias_receipt = normalize_semantic_design_transport(
            interpretation_alias,
            context=context,
            boundary=boundary,
        )
        self.assertIn(
            "typed-interpretation-mislabeled-as-row-support",
            [item["code"] for item in alias_diagnostics["findings"]],
        )
        self.assertEqual(
            [],
            normalized_alias["source_designs"][1]["assertions"][1][
                "supporting_source_bindings"
            ],
        )
        self.assertIn(
            "drop-typed-interpretation-row-support-alias",
            [item["rule"] for item in alias_receipt["repairs"]],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                normalized_alias,
            )["status"],
        )

        receipt = validate_semantic_design_binding(context, boundary, design)
        self.assertEqual(1, receipt["requiredness_oracle_count"])

        header_supported = copy.deepcopy(design)
        for assertion in header_supported["source_designs"][1]["assertions"][1:]:
            assertion["supporting_source_bindings"] = [
                {
                    "source_row_id": "SRC-001",
                    "evidence_role": "property",
                    "exact_source_fragment": header["bounded_source_text"],
                }
            ]
        header_receipt = validate_semantic_design_binding(
            context,
            boundary,
            header_supported,
        )
        self.assertEqual("verified", header_receipt["status"])

        missing_typed_literal = copy.deepcopy(design)
        editability_assertion = missing_typed_literal["source_designs"][1][
            "assertions"
        ][2]
        for binding in editability_assertion["clause_evidence"]:
            binding["exact_source_fragment"] = "Статус"
        diagnostics = semantic_design_transport_diagnostics(
            missing_typed_literal,
            context=context,
            boundary=boundary,
        )
        repaired_typed_literal, typed_literal_receipt = (
            normalize_semantic_design_transport(
                missing_typed_literal,
                context=context,
                boundary=boundary,
            )
        )
        self.assertIn(
            "typed-property-literal-evidence-missing",
            [item["code"] for item in diagnostics["findings"]],
        )
        self.assertIn(
            "bind-typed-property-to-exact-source-cell-value",
            [item["rule"] for item in typed_literal_receipt["repairs"]],
        )
        repaired_fragments = [
            item["exact_source_fragment"]
            for item in repaired_typed_literal["source_designs"][1]["assertions"][2][
                "clause_evidence"
            ]
        ]
        self.assertIn("Статус Да Да", repaired_fragments)
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                repaired_typed_literal,
            )["status"],
        )
        repaired_again, repeated_receipt = normalize_semantic_design_transport(
            repaired_typed_literal,
            context=context,
            boundary=boundary,
        )
        self.assertEqual(repaired_typed_literal, repaired_again)
        self.assertNotIn(
            "bind-typed-property-to-exact-source-cell-value",
            [item["rule"] for item in repeated_receipt["repairs"]],
        )

        compressed = copy.deepcopy(design)
        compressed["source_designs"][1]["assertions"] = [
            compressed["source_designs"][1]["assertions"][0]
        ]
        diagnostics = semantic_design_completeness_diagnostics(
            context,
            boundary,
            compressed,
        )
        property_findings = [
            item
            for item in diagnostics["findings"]
            if item["code"] == "source-property-assertion-count-mismatch"
        ]
        self.assertEqual(2, len(property_findings))
        self.assertIn(
            "testable-assertion-cardinality-shortfall",
            [item["code"] for item in diagnostics["findings"]],
        )

        typed_candidate = copy.deepcopy(design)
        candidate_obligation = typed_candidate["obligations"][2]
        candidate_obligation.update(
            obligation_class="empty-required-candidate",
            required_behavior=(
                "Пустое обязательное значение не подтверждается как валидное; "
                "точный UI-отклик требует калибровки."
            ),
            planned_check="Оставить поле пустым.",
            coverage_class="requiredness-candidate",
            input_class="empty required value",
            single_expected_behavior=(
                "Точный UI-триггер и отклик фиксируются при калибровке."
            ),
            oracle_source="ui-calibration-required",
            test_data="Пустое значение",
        )
        typed_candidate["requiredness_oracles"][0].update(
            marker_oracle_found="no",
            empty_value_oracle_found="no",
            oracle_source="not_found",
            oracle_status="ui-calibration-required",
            decision="candidate_tc_required",
            planned_tc_or_gap="candidate:SO-REQ-001",
            analyst_question=(
                "Какое действие запускает проверку и какой точный UI-отклик "
                "отображается для пустого поля?"
            ),
            handoff_rule=(
                "Сохранить candidate TC и уточнить UI без блокировки остальных проверок."
            ),
            calibration_notes=(
                "candidate-ui-calibration: точный UI-отклик не выдуман."
            ),
        )
        marker_claim = copy.deepcopy(typed_candidate)
        marker_claim["requiredness_oracles"][0]["marker_oracle_found"] = "yes"
        diagnostics = semantic_design_transport_diagnostics(
            marker_claim,
            context=context,
            boundary=boundary,
        )
        normalized, normalization_receipt = normalize_semantic_design_transport(
            marker_claim,
            context=context,
            boundary=boundary,
        )
        self.assertIn(
            "typed-candidate-executable-marker-claim",
            [item["code"] for item in diagnostics["findings"]],
        )
        self.assertEqual(
            "no",
            normalized["requiredness_oracles"][0]["marker_oracle_found"],
        )
        self.assertIn(
            "clear-unbacked-typed-candidate-marker-claim",
            [item["rule"] for item in normalization_receipt["repairs"]],
        )
        candidate_receipt = validate_semantic_design_binding(
            context,
            boundary,
            typed_candidate,
        )
        self.assertEqual("verified", candidate_receipt["status"])
        self.assertEqual(1, candidate_receipt["requiredness_oracle_count"])

        boundary_candidate = copy.deepcopy(typed_candidate)
        boundary_candidate["obligations"][2]["check_type"] = "boundary"
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                boundary_candidate,
            )["status"],
        )

        optional_context = copy.deepcopy(context)
        optional_row = optional_context["source_rows"][1]
        optional_row["bounded_source_text"] = optional_row[
            "bounded_source_text"
        ].replace("Статус Да Да", "Статус Нет Да", 1)
        optional_row["physical_table_cells"][1]["bounded_source_text"] = "Нет"
        optional_row["field_properties"]["requiredness"].update(
            property_id="FP-SRC-002-REQUIREDNESS-OPTIONAL",
            normalized_value="optional",
            source_value="Нет",
        )
        optional_mapping = optional_context["source_table_column_semantics"][0][
            "columns"
        ][0]["value_mapping"]
        optional_mapping["Нет"] = "optional"
        self._bind_context(optional_context)
        optional_preflight = validate_semantic_input_preflight(
            optional_context,
            boundary,
        )
        optional_default = optional_preflight["requiredness_candidate_defaults"][0]
        self.assertEqual(
            "Оставить поле «Статус» пустым.",
            optional_default["fallback_action"],
        )
        self.assertNotIn("SRC-002", optional_default["analyst_question"])
        optional_candidate = copy.deepcopy(typed_candidate)
        optional_candidate["prepared_context_sha256"] = prepared_context_sha256(
            optional_context
        )
        optional_candidate["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = optional_row["bounded_source_text"]
        optional_assertion = optional_candidate["source_designs"][1]["assertions"][1]
        optional_assertion[
            "source_property_id"
        ] = "FP-SRC-002-REQUIREDNESS-OPTIONAL"
        for binding in optional_assertion["clause_evidence"]:
            if binding["exact_source_fragment"] == "Да":
                binding["exact_source_fragment"] = "Нет"
        optional_obligation = optional_candidate["obligations"][2]
        optional_obligation.update(
            source_property_id="FP-SRC-002-REQUIREDNESS-OPTIONAL",
            obligation_class="empty-optional-candidate",
            required_behavior=(
                "Пустое необязательное значение допускается; точный UI-триггер "
                "подтверждения требует калибровки."
            ),
            check_type="boundary",
            coverage_class="optionality-candidate",
        )
        optional_candidate["requiredness_oracles"][0].update(
            restriction_type="optionality",
            requiredness_source="Нет",
            requiredness_class="optional",
            required_when="never_required_by_typed_cell",
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                optional_context,
                boundary,
                optional_candidate,
            )["status"],
        )

        action_optional_context = copy.deepcopy(optional_context)
        action_optional_row = action_optional_context["source_rows"][1]
        action_optional_row["bounded_source_text"] += " Кнопка"
        action_optional_row["physical_table_cells"].append(
            {
                "physical_column_index": 4,
                "source_cell_locator": "/*/*[2]/*[4]",
                "element_kind": "td",
                "bounded_source_text": "Кнопка",
            }
        )
        self._bind_context(action_optional_context)
        action_preflight = validate_semantic_input_preflight(
            action_optional_context,
            boundary,
        )
        action_default = action_preflight["requiredness_candidate_defaults"][0]
        self.assertEqual("no-action-control", action_default["fallback_input_mode"])
        self.assertIn("Не нажимать", action_default["fallback_action"])
        self.assertNotIn("пуст", action_default["fallback_action"].casefold())

        action_candidate = copy.deepcopy(optional_candidate)
        action_candidate["prepared_context_sha256"] = prepared_context_sha256(
            action_optional_context
        )
        action_candidate["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = action_optional_row["bounded_source_text"]
        normalized_action, action_receipt = normalize_semantic_design_transport(
            action_candidate,
            context=action_optional_context,
            boundary=boundary,
        )
        self.assertIn(
            "bind-optional-action-control-to-no-action-contract",
            [item["rule"] for item in action_receipt["repairs"]],
        )
        action_obligation = normalized_action["obligations"][2]
        self.assertEqual("no-action", action_obligation["input_class"])
        self.assertIn("Не нажимать", action_obligation["test_data"])
        self.assertNotIn("пуст", action_obligation["planned_check"].casefold())
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                action_optional_context,
                boundary,
                normalized_action,
            )["status"],
        )

        read_only_action_context = copy.deepcopy(action_optional_context)
        read_only_action_row = read_only_action_context["source_rows"][1]
        read_only_action_row["bounded_source_text"] = read_only_action_row[
            "bounded_source_text"
        ].replace("Статус Нет Да", "Статус Нет Нет", 1)
        read_only_action_row["physical_table_cells"][2][
            "bounded_source_text"
        ] = "Нет"
        read_only_action_row["field_properties"]["editability"].update(
            property_id="FP-SRC-002-EDITABILITY-READ-ONLY",
            normalized_value="read-only",
            source_value="Нет",
        )
        self._bind_context(read_only_action_context)
        read_only_action_candidate = copy.deepcopy(action_candidate)
        read_only_action_candidate["prepared_context_sha256"] = (
            prepared_context_sha256(read_only_action_context)
        )
        read_only_action_candidate["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = read_only_action_row[
            "bounded_source_text"
        ]
        read_only_assertion = read_only_action_candidate["source_designs"][1][
            "assertions"
        ][2]
        read_only_assertion[
            "source_property_id"
        ] = "FP-SRC-002-EDITABILITY-READ-ONLY"
        for binding in read_only_assertion["clause_evidence"]:
            if binding["exact_source_fragment"] == "Да":
                binding["exact_source_fragment"] = "Нет"
        read_only_action_candidate["obligations"][3][
            "source_property_id"
        ] = "FP-SRC-002-EDITABILITY-READ-ONLY"
        normalized_read_only, read_only_receipt = (
            normalize_semantic_design_transport(
                read_only_action_candidate,
                context=read_only_action_context,
                boundary=boundary,
            )
        )
        self.assertIn(
            "canonicalize-read-only-action-control",
            [item["rule"] for item in read_only_receipt["repairs"]],
        )
        read_only_obligation = normalized_read_only["obligations"][3]
        self.assertEqual("direct-observation", read_only_obligation["input_class"])
        self.assertNotIn("ввести текст", read_only_obligation["planned_check"].casefold())
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                read_only_action_context,
                boundary,
                normalized_read_only,
            )["status"],
        )

        conflicting_typed_literal = copy.deepcopy(optional_candidate)
        conflicting_editability = conflicting_typed_literal["source_designs"][1][
            "assertions"
        ][2]
        for binding in conflicting_editability["clause_evidence"]:
            binding["exact_source_fragment"] = "Нет"
        normalized_conflict, conflict_receipt = normalize_semantic_design_transport(
            conflicting_typed_literal,
            context=optional_context,
            boundary=boundary,
        )
        self.assertNotIn(
            "bind-typed-property-to-exact-source-cell-value",
            [item["rule"] for item in conflict_receipt["repairs"]],
        )
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "lacks its exact typed-cell source value",
        ):
            validate_semantic_design_binding(
                optional_context,
                boundary,
                normalized_conflict,
            )

        binary_optional_context = copy.deepcopy(optional_context)
        binary_optional_row = binary_optional_context["source_rows"][1]
        binary_optional_row["bounded_source_text"] += (
            " Переключатель. Логическое Да/Нет. "
            "Значение по умолчанию «Нет»."
        )
        binary_optional_row["physical_table_cells"].extend(
            [
                {
                    "physical_column_index": 4,
                    "source_cell_locator": "/*/*[2]/*[4]",
                    "element_kind": "td",
                    "bounded_source_text": "Переключатель",
                },
                {
                    "physical_column_index": 5,
                    "source_cell_locator": "/*/*[2]/*[5]",
                    "element_kind": "td",
                    "bounded_source_text": "Логическое Да/Нет",
                },
                {
                    "physical_column_index": 6,
                    "source_cell_locator": "/*/*[2]/*[6]",
                    "element_kind": "td",
                    "bounded_source_text": "Значение по умолчанию «Нет»",
                },
            ]
        )
        self._bind_context(binary_optional_context)
        binary_registry = _source_signal_registry(
            [binary_optional_row],
            {"SRC-002": ["BSR 1", "BSR 9"]},
        )
        binary_signal = binary_registry["requiredness"][0]
        self.assertEqual("binary-logical-default", binary_signal["value_semantics"])
        self.assertEqual("Нет", binary_signal["default_value"])
        binary_preflight = validate_semantic_input_preflight(
            binary_optional_context,
            boundary,
        )
        binary_default = binary_preflight["requiredness_candidate_defaults"][0]
        self.assertEqual(
            "binary-logical-default",
            binary_default["fallback_input_mode"],
        )
        self.assertEqual("Нет", binary_default["source_backed_default_value"])
        self.assertNotIn("пуст", binary_default["fallback_action"].casefold())

        binary_candidate = copy.deepcopy(optional_candidate)
        binary_candidate["prepared_context_sha256"] = prepared_context_sha256(
            binary_optional_context
        )
        binary_candidate["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = binary_optional_row["bounded_source_text"]
        normalized_binary, binary_receipt = normalize_semantic_design_transport(
            binary_candidate,
            context=binary_optional_context,
            boundary=boundary,
        )
        self.assertIn(
            "bind-binary-optional-candidate-to-source-default",
            [item["rule"] for item in binary_receipt["repairs"]],
        )
        binary_obligation = normalized_binary["obligations"][2]
        binary_oracle = normalized_binary["requiredness_oracles"][0]
        self.assertEqual(
            "positive",
            normalized_binary["source_designs"][1]["assertions"][1]["polarity"],
        )
        self.assertEqual(
            "optionality-binary-default",
            binary_obligation["coverage_class"],
        )
        self.assertEqual(
            "Логическое значение по умолчанию «Нет»",
            binary_obligation["test_data"],
        )
        self.assertNotIn("пуст", binary_obligation["planned_check"].casefold())
        self.assertEqual("optional-binary-default", binary_oracle["requiredness_class"])
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                binary_optional_context,
                boundary,
                normalized_binary,
            )["status"],
        )

        conditional_context = copy.deepcopy(context)
        conditional_value = "Да, если применимо"
        conditional_row = conditional_context["source_rows"][1]
        conditional_row["bounded_source_text"] = conditional_row[
            "bounded_source_text"
        ].replace("Статус Да Да", f"Статус {conditional_value} Да", 1)
        conditional_row["physical_table_cells"][1][
            "bounded_source_text"
        ] = conditional_value
        conditional_row["field_properties"]["requiredness"][
            "source_value"
        ] = conditional_value
        value_mapping = conditional_context["source_table_column_semantics"][0][
            "columns"
        ][0]["value_mapping"]
        value_mapping[conditional_value] = value_mapping.pop("Да")
        self._bind_context(conditional_context)
        conditional_boundary = copy.deepcopy(boundary)
        conditional_candidate = copy.deepcopy(typed_candidate)
        conditional_candidate["prepared_context_sha256"] = (
            prepared_context_sha256(conditional_context)
        )
        conditional_candidate["scope_boundary_decision_sha256"] = (
            canonical_payload_sha256(conditional_boundary)
        )
        conditional_candidate["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = conditional_row["bounded_source_text"]
        conditional_candidate["requiredness_oracles"][0][
            "requiredness_source"
        ] = conditional_value
        for binding in conditional_candidate["source_designs"][1]["assertions"][1][
            "clause_evidence"
        ]:
            binding["exact_source_fragment"] = conditional_value
        conditional_candidate["obligations"][2]["check_type"] = "dependency"
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                conditional_context,
                conditional_boundary,
                conditional_candidate,
            )["status"],
        )

        binary_required_context = copy.deepcopy(conditional_context)
        binary_required_row = binary_required_context["source_rows"][1]
        binary_required_row["bounded_source_text"] += (
            " Переключатель. Логическое Да/Нет. "
            "Значение по умолчанию «Нет»."
        )
        binary_required_row["physical_table_cells"].extend(
            [
                {
                    "physical_column_index": 4,
                    "source_cell_locator": "/*/*[2]/*[4]",
                    "element_kind": "td",
                    "bounded_source_text": "Переключатель",
                },
                {
                    "physical_column_index": 5,
                    "source_cell_locator": "/*/*[2]/*[5]",
                    "element_kind": "td",
                    "bounded_source_text": "Логическое Да/Нет",
                },
                {
                    "physical_column_index": 6,
                    "source_cell_locator": "/*/*[2]/*[6]",
                    "element_kind": "td",
                    "bounded_source_text": "Значение по умолчанию «Нет»",
                },
            ]
        )
        self._bind_context(binary_required_context)
        binary_required_registry = _source_signal_registry(
            [binary_required_row],
            {"SRC-002": ["BSR 1", "BSR 9"]},
        )
        binary_required_signal = binary_required_registry["requiredness"][0]
        self.assertEqual("requiredness", binary_required_signal["restriction_type"])
        self.assertEqual(
            "binary-logical-default",
            binary_required_signal["value_semantics"],
        )
        binary_required_candidate = copy.deepcopy(conditional_candidate)
        binary_required_candidate["prepared_context_sha256"] = (
            prepared_context_sha256(binary_required_context)
        )
        binary_required_candidate["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = binary_required_row["bounded_source_text"]
        normalized_required, required_receipt = normalize_semantic_design_transport(
            binary_required_candidate,
            context=binary_required_context,
            boundary=conditional_boundary,
        )
        self.assertIn(
            "bind-binary-requiredness-candidate-to-source-default",
            [item["rule"] for item in required_receipt["repairs"]],
        )
        required_obligation = normalized_required["obligations"][2]
        required_oracle = normalized_required["requiredness_oracles"][0]
        self.assertEqual(
            "positive",
            normalized_required["source_designs"][1]["assertions"][1]["polarity"],
        )
        self.assertEqual("dependency", required_obligation["check_type"])
        self.assertEqual(
            "Логическое значение по умолчанию «Нет»",
            required_obligation["test_data"],
        )
        self.assertNotIn("пуст", required_obligation["planned_check"].casefold())
        self.assertEqual("required-binary-default", required_oracle["requiredness_class"])
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                binary_required_context,
                conditional_boundary,
                normalized_required,
            )["status"],
        )

        fallback_evidence_alias = copy.deepcopy(typed_candidate)
        fallback_assertion = fallback_evidence_alias["source_designs"][1][
            "assertions"
        ][1]
        fallback_action = "Оставить поле из SRC-002 пустым."
        fallback_oracle = (
            "Пустое обязательное значение не подтверждается как валидное; "
            "точный UI-триггер и отклик требуют калибровки."
        )
        fallback_assertion["action_clauses"] = [fallback_action]
        fallback_assertion["oracle_clauses"] = [fallback_oracle]
        for binding in fallback_assertion["clause_evidence"]:
            if binding["clause_kind"] == "action":
                binding["exact_source_fragment"] = fallback_action
            elif binding["clause_kind"] == "oracle":
                binding["exact_source_fragment"] = fallback_oracle
        diagnostics = semantic_design_transport_diagnostics(
            fallback_evidence_alias,
            context=context,
            boundary=boundary,
        )
        fallback_normalized, fallback_receipt = (
            normalize_semantic_design_transport(
                fallback_evidence_alias,
                context=context,
                boundary=boundary,
            )
        )
        self.assertIn(
            "candidate-fallback-clause-evidence-alias",
            [item["code"] for item in diagnostics["findings"]],
        )
        self.assertIn(
            "bind-candidate-fallback-clause-evidence-to-source-row",
            [item["rule"] for item in fallback_receipt["repairs"]],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                fallback_normalized,
            )["status"],
        )

        source_prefixed_unknown = copy.deepcopy(typed_candidate)
        source_prefixed_unknown["requiredness_oracles"][0]["oracle_source"] = (
            "BSR 1 specifies requiredness; exact UI reaction not_found"
        )
        source_prefixed_unknown["obligations"][2]["oracle_source"] = (
            "BSR 1; exact UI reaction not_found"
        )
        diagnostics = semantic_design_transport_diagnostics(
            source_prefixed_unknown,
            context=context,
            boundary=boundary,
        )
        normalized, normalization_receipt = normalize_semantic_design_transport(
            source_prefixed_unknown,
            context=context,
            boundary=boundary,
        )
        self.assertEqual(
            2,
            sum(
                item["code"] == "candidate-oracle-source-sentinel-alias"
                for item in diagnostics["findings"]
            ),
        )
        self.assertEqual(
            "not_found",
            normalized["requiredness_oracles"][0]["oracle_source"],
        )
        self.assertEqual(
            "not_found",
            normalized["obligations"][2]["oracle_source"],
        )
        self.assertEqual(
            2,
            sum(
                item["rule"]
                == "canonicalize-candidate-unknown-oracle-source"
                for item in normalization_receipt["repairs"]
            ),
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                normalized,
            )["status"],
        )

        obligation_only_alias = copy.deepcopy(typed_candidate)
        obligation_only_alias["obligations"][2]["oracle_source"] = (
            "typed XHTML requiredness; fallback SO-REQ-001"
        )
        obligation_only_normalized, obligation_only_receipt = (
            normalize_semantic_design_transport(
                obligation_only_alias,
                context=context,
                boundary=boundary,
            )
        )
        self.assertEqual(
            "not_found",
            obligation_only_normalized["obligations"][2]["oracle_source"],
        )
        self.assertEqual(
            1,
            sum(
                item["rule"]
                == "canonicalize-candidate-unknown-oracle-source"
                for item in obligation_only_receipt["repairs"]
            ),
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                obligation_only_normalized,
            )["status"],
        )

        russian_postfixed_denial_alias = copy.deepcopy(typed_candidate)
        russian_postfixed_denial_alias["requiredness_oracles"][0][
            "oracle_source"
        ] = "BSR 1 задаёт ограничение; точная UI-реакция не найдена."
        russian_postfixed_denial_normalized, _ = normalize_semantic_design_transport(
            russian_postfixed_denial_alias,
            context=context,
            boundary=boundary,
        )
        self.assertEqual(
            "not_found",
            russian_postfixed_denial_normalized["requiredness_oracles"][0][
                "oracle_source"
            ],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                russian_postfixed_denial_normalized,
            )["status"],
        )

        for source_only_alias in (
            "BSR 115-120",
            "typed XHTML requiredness cell",
        ):
            candidate_source_only_alias = copy.deepcopy(typed_candidate)
            candidate_source_only_alias["obligations"][2][
                "oracle_source"
            ] = source_only_alias
            candidate_source_only_normalized, _ = normalize_semantic_design_transport(
                candidate_source_only_alias,
                context=context,
                boundary=boundary,
            )
            self.assertEqual(
                "not_found",
                candidate_source_only_normalized["obligations"][2][
                    "oracle_source"
                ],
            )
            self.assertEqual(
                "verified",
                validate_semantic_design_binding(
                    context,
                    boundary,
                    candidate_source_only_normalized,
            )["status"],
        )

        candidate_state_canonicalization = copy.deepcopy(typed_candidate)
        candidate_state_canonicalization["requiredness_oracles"][0][
            "oracle_source"
        ] = "BSR 1 задаёт ограничение; точная UI-реакция отсутствует."
        candidate_state_normalized, _ = normalize_semantic_design_transport(
            candidate_state_canonicalization,
            context=context,
            boundary=boundary,
        )
        self.assertEqual(
            "not_found",
            candidate_state_normalized["requiredness_oracles"][0][
                "oracle_source"
            ],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                candidate_state_normalized,
            )["status"],
        )

        semantic_candidate_default_alias = copy.deepcopy(typed_candidate)
        semantic_candidate_default_alias["obligations"][2]["oracle_source"] = (
            "semantic_requiredness_candidate_defaults:SIG-REQ-001"
        )
        semantic_candidate_default_normalized, semantic_candidate_default_receipt = (
            normalize_semantic_design_transport(
                semantic_candidate_default_alias,
                context=context,
                boundary=boundary,
            )
        )
        self.assertEqual(
            "not_found",
            semantic_candidate_default_normalized["obligations"][2][
                "oracle_source"
            ],
        )
        self.assertIn(
            "canonicalize-candidate-unknown-oracle-source",
            [item["rule"] for item in semantic_candidate_default_receipt["repairs"]],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                semantic_candidate_default_normalized,
            )["status"],
        )

        calibration_required_alias = copy.deepcopy(typed_candidate)
        calibration_required_alias["obligations"][2]["oracle_source"] = (
            "BSR 1; UI calibration required"
        )
        calibration_required_normalized, _ = normalize_semantic_design_transport(
            calibration_required_alias,
            context=context,
            boundary=boundary,
        )
        self.assertEqual(
            "not_found",
            calibration_required_normalized["obligations"][2][
                "oracle_source"
            ],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                calibration_required_normalized,
            )["status"],
        )

        explicit_denial_alias = copy.deepcopy(typed_candidate)
        explicit_denial_alias["requiredness_oracles"][0]["oracle_source"] = (
            "BSR 1 defines the restriction but not the exact UI reaction."
        )
        explicit_denial_alias["obligations"][2]["oracle_source"] = (
            "BSR 1 restriction only"
        )
        explicit_denial_normalized, _ = normalize_semantic_design_transport(
            explicit_denial_alias,
            context=context,
            boundary=boundary,
        )
        self.assertEqual(
            "not_found",
            explicit_denial_normalized["requiredness_oracles"][0][
                "oracle_source"
            ],
        )
        self.assertEqual(
            "not_found",
            explicit_denial_normalized["obligations"][2]["oracle_source"],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                explicit_denial_normalized,
            )["status"],
        )

        russian_explicit_denial_alias = copy.deepcopy(typed_candidate)
        russian_explicit_denial_alias["requiredness_oracles"][0][
            "oracle_source"
        ] = "BSR 1 задаёт допустимый формат, но не точную UI-реакцию."
        russian_explicit_denial_alias["obligations"][2]["oracle_source"] = (
            "BSR 1; exact UI reaction not found"
        )
        russian_explicit_denial_normalized, _ = (
            normalize_semantic_design_transport(
                russian_explicit_denial_alias,
                context=context,
                boundary=boundary,
            )
        )
        self.assertEqual(
            "not_found",
            russian_explicit_denial_normalized["requiredness_oracles"][0][
                "oracle_source"
            ],
        )
        self.assertEqual(
            "verified",
            validate_semantic_design_binding(
                context,
                boundary,
                russian_explicit_denial_normalized,
            )["status"],
        )

        wrong_editability = copy.deepcopy(design)
        wrong_editability["source_designs"][1]["assertions"][2][
            "source_property_id"
        ] = "FP-SRC-002-EDITABILITY-READ-ONLY"
        wrong_editability["obligations"][3][
            "source_property_id"
        ] = "FP-SRC-002-EDITABILITY-READ-ONLY"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "EDITABILITY-EDITABLE must map to one distinct",
        ):
            validate_semantic_design_binding(
                context,
                boundary,
                wrong_editability,
            )

    def test_executable_requiredness_signal_requires_an_observable_oracle(self) -> None:
        context = self._context()
        context["source_rows"][1]["bounded_source_text"] += " required"
        self._bind_context(context)
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)
        design["source_designs"][1]["assertions"][0][
            "requirement_code_evidence"
        ][0]["exact_source_fragment"] = context["source_rows"][1][
            "bounded_source_text"
        ]
        design["obligations"][0].update(
            check_type="negative",
            scope_obligation_ids=["SO-REQ-001"],
        )
        design["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": ["BSR 1"],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-002",
                "source_ref": "BSR 1",
                "field_or_block": "Статус",
                "restriction_type": "requiredness",
                "requiredness_source": "required",
                "requiredness_class": "always-required",
                "required_when": "always",
                "marker_oracle_found": "no",
                "empty_value_oracle_found": "no",
                "oracle_source": "BSR 1",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": "TC-001",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "Keep one exact signal and chain.",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-002",
                "linked_obligation_id": "OBL-001",
            }
        ]

        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "lacks a marker or empty-value oracle",
        ):
            validate_semantic_design_binding(context, self._boundary(), design)

        candidate = copy.deepcopy(design)
        positive_obligation = candidate["obligations"][0]
        positive_obligation.update(
            check_type="positive",
            scope_obligation_ids=[],
        )
        candidate_obligation = copy.deepcopy(positive_obligation)
        candidate_obligation.update(
            obligation_id="OBL-003",
            property_type="requiredness",
            obligation_class="empty-required-candidate",
            required_behavior="Пустое обязательное поле не является валидным.",
            planned_tc_id="TC-003",
            design_dimension="boundary",
            planned_check="Оставить обязательное поле пустым.",
            check_type="negative",
            coverage_class="requiredness-candidate",
            input_class="empty required value",
            single_expected_behavior=(
                "Пустое значение не принято как валидное; механизм калибруется."
            ),
            oracle_source="ui-calibration-required",
            test_data="Пустое значение",
            dictionary_refs=[],
            dictionary_coverage="none_required",
            scope_obligation_ids=["SO-REQ-001"],
        )
        candidate["obligations"].append(candidate_obligation)
        candidate["source_designs"][1]["assertions"][0][
            "obligation_ids"
        ].append("OBL-003")
        candidate["dependency_bindings"][0]["linked_obligation_ids"] = [
            "OBL-001",
            "OBL-003",
        ]
        applicability = {
            item["dimension"]: item for item in candidate["applicability"]
        }
        applicability["boundary"].update(
            applicable="yes",
            source_ref="BSR 1",
            reason="Кандидат проверки пустого обязательного значения.",
            linked_atoms=["ATOM-002"],
            linked_test_cases=["TC-003"],
        )
        applicability["traceability"]["linked_test_cases"].append("TC-003")
        candidate["requiredness_oracles"][0].update(
            oracle_source="not_found",
            oracle_status="ui-calibration-required",
            decision="candidate_tc_required",
            planned_tc_or_gap="candidate:SO-REQ-001",
            analyst_question=(
                "Какой точный UI-отклик отображается при пустом обязательном поле?"
            ),
            handoff_rule=(
                "Проверить отклик в реальном UI до перевода кандидата в executable."
            ),
            calibration_notes=(
                "Статус тест-кейса: candidate-ui-calibration; точный oracle не выдуман."
            ),
            linked_obligation_id="OBL-003",
        )
        receipt = validate_semantic_design_binding(
            context,
            self._boundary(),
            candidate,
        )
        self.assertEqual("verified", receipt["status"])

        boundary_with_parent_gap = self._boundary()
        boundary_with_parent_gap["gaps"] = [
            {
                "gap_id": "GAP-UI-001",
                "gap_type": "ambiguity",
                "source_row_ids": ["SRC-002"],
                "source_refs": ["BSR 1"],
                "exact_source_fragments": ["required"],
                "blocking": False,
                "clarification_question": (
                    "Какой точный UI-механизм обязательности наблюдается?"
                ),
                "downstream_handling": "carry-to-source-model",
            }
        ]
        candidate_with_parent_gap = copy.deepcopy(candidate)
        candidate_with_parent_gap[
            "scope_boundary_decision_sha256"
        ] = canonical_payload_sha256(boundary_with_parent_gap)
        candidate_with_parent_gap["requiredness_oracles"][0][
            "gap_id"
        ] = "GAP-UI-001"
        receipt = validate_semantic_design_binding(
            context,
            boundary_with_parent_gap,
            candidate_with_parent_gap,
        )
        self.assertEqual("verified", receipt["status"])

        missing_marker = copy.deepcopy(candidate)
        missing_marker["requiredness_oracles"][0][
            "calibration_notes"
        ] = "Требуется проверить UI."
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "candidate-ui-calibration marker",
        ):
            validate_semantic_design_binding(
                context,
                self._boundary(),
                missing_marker,
            )

        already_observable = copy.deepcopy(candidate)
        already_observable["requiredness_oracles"][0][
            "marker_oracle_found"
        ] = "yes"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "already has an executable marker or empty-value oracle",
        ):
            validate_semantic_design_binding(
                context,
                self._boundary(),
                already_observable,
            )

        invented_obligation_oracle = copy.deepcopy(candidate)
        invented_obligation_oracle["obligations"][2]["oracle_source"] = "BSR 1"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "candidate obligation must not claim a backed exact oracle source",
        ):
            validate_semantic_design_binding(
                context,
                self._boundary(),
                invented_obligation_oracle,
            )

        missing_positive_companion = copy.deepcopy(candidate)
        missing_positive_companion["obligations"][0]["check_type"] = "negative"
        with self.assertRaisesRegex(
            SemanticDesignBridgeError,
            "must preserve a positive allowed-class TC",
        ):
            validate_semantic_design_binding(
                context,
                self._boundary(),
                missing_positive_companion,
            )

    def test_unbound_context_reset_does_not_create_executable_obligation(self) -> None:
        context = self._context()
        context["source_rows"][0]["bounded_source_text"] += (
            " После вне-scope действия значение очищается."
        )
        self._bind_context(context)
        design = self._design()
        design["prepared_context_sha256"] = prepared_context_sha256(context)

        receipt = validate_semantic_design_binding(context, self._boundary(), design)

        self.assertEqual(1, receipt["dictionary_count"])
        self.assertEqual(1, receipt["state_change_obligation_count"])

    def test_blocked_result_is_empty_and_never_materializable(self) -> None:
        blocked = self._design()
        blocked["status"] = "blocked"
        blocked["blocking_reason"] = "Требуется точный наблюдаемый oracle для выпуска."
        for name in (
            "source_designs",
            "obligations",
            "reset_lifecycle_bindings",
            "dependency_bindings",
            "dictionaries",
            "negative_oracles",
            "requiredness_oracles",
            "applicability",
        ):
            blocked[name] = []
        receipt = self._validate(blocked)
        self.assertEqual("blocked", receipt["status"])
        self.assertEqual(0, receipt["obligation_count"])
        with self.assertRaisesRegex(SemanticDesignBridgeError, "outside the allowed enum"):
            validate_semantic_design_binding(
                self._context(),
                self._boundary(),
                blocked,
                require_ready=True,
            )

        blocked["source_designs"] = self._design()["source_designs"]
        with self.assertRaisesRegex(SemanticDesignBridgeError, "partial semantic payload"):
            self._validate(blocked)


if __name__ == "__main__":
    unittest.main()
