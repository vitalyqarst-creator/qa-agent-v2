from __future__ import annotations

import unittest
from dataclasses import replace

from test_case_agent.coverage_graph import (
    CoverageCase,
    CoverageGraph,
    CoverageObligation,
    CoverageProperty,
)
from test_case_agent.review_cycle.production_tc_gate import validate_production_tc_content
from test_case_agent.iteration_contract import build_reviewer_request, validate_suite
from test_case_agent.test_design import (
    DesignContext,
    DesignError,
    build_test_design_plan,
    render_test_cases,
    validate_design_context_for_graph,
)


def _property(kind: str = "positive-input") -> CoverageProperty:
    return CoverageProperty(
        property_id="PROP-1",
        assertion_id="ASSERT-001",
        property_key="customer-name:input",
        subject_key="customer-name",
        property_kind=kind,
        source_row_id="SRC-001",
        source_path="requirements.xhtml",
        source_locator="/*/*[1]",
        source_text_sha256="a" * 64,
        canonical_statement="Поле «Имя» принимает значение.",
        requirement_codes=("BSR 1",),
        disposition="tc",
    )


def _obligation(
    *,
    kind: str = "positive-input",
    fixtures: tuple[str, ...] = ("Иван",),
    status: str = "executable",
    trigger: str = "",
    question: str = "",
    cleanup: str = "",
) -> CoverageObligation:
    atomic_statement = {
        "repeater-delete": "Удалить поле «Имя».",
        "repeater-add": "Добавить поле «Имя».",
        "state-change": "Изменить значение поля «Имя».",
        "cross-field-rule": "Проверить зависимость поля «Имя».",
    }.get(kind, "Ввести значение в поле «Имя».")
    return CoverageObligation(
        obligation_id="OBL-001",
        property_id="PROP-1",
        atom_id="ATOM-001",
        coverage_variant="positive",
        condition_key="always",
        atomic_statement=atomic_statement,
        observable_oracle="В поле «Имя» отображается введённое значение.",
        coverage_status="testable",
        requirement_codes=("BSR 1",),
        gap_id="",
        calibration_status=(
            "ui-calibration-required"
            if status == "candidate-ui-calibration"
            else "not-required"
        ),
        validation_trigger=trigger,
        cleanup_strategy=cleanup,
        source_oracle_id="SO-001" if status == "candidate-ui-calibration" else "",
        fixture_values=fixtures,
        calibration_question=question,
    )


def _graph(
    *,
    kind: str = "positive-input",
    fixtures: tuple[str, ...] = ("Иван",),
    status: str = "executable",
    trigger: str = "",
    question: str = "",
    cleanup: str = "",
) -> CoverageGraph:
    return CoverageGraph(
        schema_version=1,
        ft_slug="sample",
        scope_slug="customer",
        source_manifest_digest="b" * 64,
        obligation_set_digest="c" * 64,
        properties=(
            _property(kind),
            CoverageProperty(
                property_id="PROP-CONTEXT",
                assertion_id="ASSERT-CONTEXT",
                property_key="customer-card:open",
                subject_key="customer-card",
                property_kind="context",
                source_row_id="SRC-CONTEXT",
                source_path="requirements.xhtml",
                source_locator="/*/*[0]",
                source_text_sha256="d" * 64,
                canonical_statement="Открыть карточку клиента.",
                requirement_codes=(),
                disposition="not-applicable",
            ),
            CoverageProperty(
                property_id="PROP-SCOPE-TITLE",
                assertion_id="ASSERT-SCOPE-TITLE",
                property_key="customer-card:title",
                subject_key="customer-card",
                property_kind="context",
                source_row_id="SRC-SCOPE-TITLE",
                source_path="requirements.xhtml",
                source_locator="/*/*[0]/*[1]",
                source_text_sha256="e" * 64,
                canonical_statement="Данные клиента",
                requirement_codes=(),
                disposition="not-applicable",
            ),
        ),
        obligations=(
            _obligation(
                kind=kind,
                fixtures=fixtures,
                status=status,
                trigger=trigger,
                question=question,
                cleanup=cleanup,
            ),
        ),
        cases=(
            CoverageCase(
                case_key=f"customer|customer-name|{kind}|positive|always",
                tc_id="TC-CUST-0123456789",
                obligation_ids=("OBL-001",),
                status=status,
            ),
        ),
        gaps=(),
    )


def _context() -> DesignContext:
    return DesignContext(
        package_id="WP-01",
        scope_title="Данные клиента",
        base_preconditions=("Открыть карточку клиента.",),
        subject_labels={"customer-name": "поле «Имя»"},
        condition_preconditions={},
    )


def _repeater_graph_and_context() -> tuple[CoverageGraph, DesignContext]:
    graph = _graph(
        kind="visibility",
        fixtures=(),
        trigger="Открыть блок «Данные клиента».",
    )
    graph = replace(
        graph,
        properties=(
            replace(
                graph.properties[0],
                canonical_statement="Кнопка «Добавить» видима всегда.",
            ),
            CoverageProperty(
                property_id="PROP-ADD",
                assertion_id="ASSERT-ADD",
                property_key="customer-name:add-row",
                subject_key="customer-name",
                property_kind="source-add-row",
                source_row_id="SRC-001",
                source_path="requirements.xhtml",
                source_locator="/*/*[2]",
                source_text_sha256="9" * 64,
                canonical_statement=(
                    "Нажатие кнопки «Добавить» добавляет новую строку "
                    "с элементом «Корзина»."
                ),
                requirement_codes=("BSR 2",),
                disposition="tc",
                polarity="positive",
            ),
            CoverageProperty(
                property_id="PROP-DELETE",
                assertion_id="ASSERT-DELETE",
                property_key="customer-row:delete",
                subject_key="delete-control",
                property_kind="source-delete-row",
                source_row_id="SRC-DELETE",
                source_path="requirements.xhtml",
                source_locator="/*/*[3]",
                source_text_sha256="8" * 64,
                canonical_statement=(
                    "Элемент «Корзина» удаляет целевую строку."
                ),
                requirement_codes=("BSR 3",),
                disposition="tc",
                polarity="positive",
            ),
            *graph.properties[1:],
        ),
        obligations=(
            replace(
                graph.obligations[0],
                coverage_variant="always-visible",
                atomic_statement="Кнопка «Добавить» видима всегда.",
                observable_oracle="Кнопка «Добавить» отображается.",
            ),
            CoverageObligation(
                obligation_id="OBL-ADD",
                property_id="PROP-ADD",
                atom_id="ATOM-ADD",
                coverage_variant="repeater-add",
                condition_key="always",
                atomic_statement="Нажатие кнопки «Добавить» добавляет новую строку.",
                observable_oracle="Появляется новая строка с элементом «Корзина».",
                coverage_status="testable",
                requirement_codes=("BSR 2",),
                gap_id="",
                calibration_status="not-required",
                validation_trigger="Нажать «Добавить».",
                cleanup_strategy="",
                source_oracle_id="",
                fixture_values=(),
                calibration_question="",
            ),
            CoverageObligation(
                obligation_id="OBL-DELETE",
                property_id="PROP-DELETE",
                atom_id="ATOM-DELETE",
                coverage_variant="repeater-delete",
                condition_key="always",
                atomic_statement="Элемент «Корзина» удаляет целевую строку.",
                observable_oracle="Целевая строка удалена, другая строка остается.",
                coverage_status="testable",
                requirement_codes=("BSR 3",),
                gap_id="",
                calibration_status="not-required",
                validation_trigger="Нажать «Корзина» в целевой строке.",
                cleanup_strategy="",
                source_oracle_id="",
                fixture_values=(),
                calibration_question="",
            ),
        ),
        cases=(
            *graph.cases,
            CoverageCase(
                case_key="customer|customer-name|source-add-row|repeater-add|always",
                tc_id="TC-CUST-ADD0000001",
                obligation_ids=("OBL-ADD",),
                status="executable",
            ),
            CoverageCase(
                case_key="customer|delete-control|source-delete-row|repeater-delete|always",
                tc_id="TC-CUST-DEL0000001",
                obligation_ids=("OBL-DELETE",),
                status="executable",
            ),
        ),
    )
    context = replace(
        _context(),
        subject_labels={
            "customer-name": "кнопка «Добавить»",
            "delete-control": "элемент «Корзина»",
        },
    )
    return graph, context


class TestDesignTests(unittest.TestCase):
    def test_positive_input_is_deterministic_and_concrete(self) -> None:
        plan = build_test_design_plan(_graph(), context=_context())

        self.assertEqual(len(plan.deterministic_cases), 1)
        self.assertEqual(plan.writer_cards, ())
        self.assertEqual(plan.blocked_cards, ())
        case = plan.deterministic_cases[0]
        self.assertEqual(case.tc_id, "TC-CUST-0123456789")
        self.assertIn("`Иван`", case.test_data[0])
        self.assertEqual(
            case.expected_result,
            "В поле «Имя» отображается введённое значение.",
        )

    def test_unknown_property_is_explicit_writer_card(self) -> None:
        plan = build_test_design_plan(_graph(kind="cross-field-rule"), context=_context())

        self.assertEqual(plan.deterministic_cases, ())
        self.assertIn("unsupported deterministic", plan.writer_cards[0].writer_required_reason)

    def test_source_bound_generic_design_needs_no_writer_and_preserves_action(self) -> None:
        graph = _graph(
            kind="source-requiredness",
            fixtures=("Пустое значение",),
            trigger="Оставить поле «Имя» пустым.",
        )
        graph = replace(
            graph,
            properties=(replace(graph.properties[0], polarity="negative"), *graph.properties[1:]),
        )

        plan = build_test_design_plan(graph, context=_context())

        self.assertEqual((), plan.writer_cards)
        self.assertEqual((), plan.blocked_cards)
        self.assertEqual("негативный", plan.deterministic_cases[0].case_type)
        self.assertEqual(
            ("Оставить поле «Имя» пустым.",),
            plan.deterministic_cases[0].steps,
        )

    def test_source_editability_reuses_valid_same_subject_fixture(self) -> None:
        graph = _graph(
            kind="source-editability",
            fixtures=("Тест",),
            trigger="Ввести или изменить значение поля «Имя».",
        )
        graph = replace(
            graph,
            properties=(
                replace(graph.properties[0], polarity="positive"),
                CoverageProperty(
                    property_id="PROP-NAME-VALID",
                    assertion_id="ASSERT-NAME-VALID",
                    property_key="customer-name:valid-input",
                    subject_key="customer-name",
                    property_kind="positive-input",
                    source_row_id="SRC-VALID",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[2]",
                    source_text_sha256="9" * 64,
                    canonical_statement="Поле «Имя» принимает значение `Иван`.",
                    requirement_codes=("BSR 2",),
                    disposition="tc",
                    polarity="positive",
                ),
                *graph.properties[1:],
            ),
            obligations=(
                graph.obligations[0],
                CoverageObligation(
                    obligation_id="OBL-NAME-VALID",
                    property_id="PROP-NAME-VALID",
                    atom_id="ATOM-NAME-VALID",
                    coverage_variant="allowed-class",
                    condition_key="always",
                    atomic_statement="Поле «Имя» принимает значение `Иван`.",
                    observable_oracle="В поле «Имя» отображается значение `Иван`.",
                    coverage_status="testable",
                    requirement_codes=("BSR 2",),
                    gap_id="",
                    calibration_status="not-required",
                    validation_trigger="Ввести `Иван` в поле «Имя».",
                    cleanup_strategy="",
                    source_oracle_id="",
                    fixture_values=("Иван",),
                    calibration_question="",
                ),
            ),
        )

        case = build_test_design_plan(graph, context=_context()).deterministic_cases[0]

        self.assertIn("`Иван`", case.test_data[0])
        self.assertNotIn("`Тест`", case.test_data[0])
        self.assertIn("`Иван`", case.steps[0])

    def test_input_action_without_target_gets_typed_subject_wrapper(self) -> None:
        graph = _graph(
            kind="source-format",
            fixtures=("9123456789",),
            trigger="Ввести «9123456789».",
        )
        graph = replace(
            graph,
            properties=(
                replace(graph.properties[0], polarity="positive"),
                *graph.properties[1:],
            ),
        )

        plan = build_test_design_plan(graph, context=_context())

        self.assertEqual(
            (
                "В целевом элементе (поле «Имя») выполнить действие: "
                "Ввести «9123456789».",
            ),
            plan.deterministic_cases[0].steps,
        )
        self.assertIn(
            "Ввести «9123456789».",
            plan.deterministic_cases[0].steps[0],
        )

    def test_subject_label_can_bind_to_sibling_from_same_source_row(self) -> None:
        graph = _graph(
            kind="source-date-boundary",
            fixtures=("текущая дата",),
            trigger="Ввести зафиксированную текущую дату.",
        )
        graph = replace(
            graph,
            properties=(
                replace(
                    graph.properties[0],
                    canonical_statement="Текущая дата допускается.",
                ),
                CoverageProperty(
                    property_id="PROP-SIBLING",
                    assertion_id="ASSERT-SIBLING",
                    property_key="customer-name:visibility",
                    subject_key="customer-name",
                    property_kind="visibility",
                    source_row_id="SRC-001",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[1]",
                    source_text_sha256="f" * 64,
                    canonical_statement="Поле «Имя» отображается.",
                    requirement_codes=("BSR 1",),
                    disposition="tc",
                ),
                *graph.properties[1:],
            ),
        )

        validate_design_context_for_graph(graph, _context())

    def test_generated_titles_do_not_depend_on_russian_inflection(self) -> None:
        plan = build_test_design_plan(
            _graph(kind="visibility", fixtures=(), trigger="Открыть карточку."),
            context=_context(),
        )

        self.assertEqual(
            "Отображение: поле «Имя»",
            plan.deterministic_cases[0].title,
        )

    def test_hidden_before_visibility_observes_initial_state_before_transition(self) -> None:
        condition = "Кнопка «Добавить» ещё не нажата."
        graph = _graph(
            kind="visibility",
            fixtures=(),
            trigger="Нажать «Добавить».",
        )
        graph = replace(
            graph,
            properties=(
                replace(
                    graph.properties[0],
                    canonical_statement=(
                        "Поле «Имя» скрыто до добавления строки "
                        "и затем отображается."
                    ),
                    condition_clauses=(condition,),
                ),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    coverage_variant="visibility",
                    condition_key="condition:hidden-before",
                    atomic_statement=(
                        "Поле «Имя» скрыто до добавления строки "
                        "и затем отображается."
                    ),
                    observable_oracle="Поле «Имя» отображается после нажатия.",
                ),
            ),
        )
        context = replace(
            _context(),
            condition_preconditions={"condition:hidden-before": condition},
        )

        case = build_test_design_plan(graph, context=context).deterministic_cases[0]

        self.assertEqual(
            (
                "Проверить исходное состояние: Поле «Имя» скрыто до "
                "добавления строки.",
                "Нажать «Добавить».",
            ),
            case.steps,
        )

    def test_default_observes_initial_value_without_focus_or_interaction(self) -> None:
        condition = "Поле «Имя» только что отображено."
        graph = _graph(
            kind="default",
            fixtures=("Иван",),
            trigger="",
        )
        graph = replace(
            graph,
            properties=(
                replace(
                    graph.properties[0],
                    canonical_statement="По умолчанию в поле «Имя» показано «Иван».",
                    condition_clauses=(condition,),
                ),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    coverage_variant="default",
                    condition_key="condition:just-displayed",
                    atomic_statement="По умолчанию в поле «Имя» показано «Иван».",
                    observable_oracle="Отображается значение «Иван».",
                ),
            ),
        )
        context = replace(
            _context(),
            condition_preconditions={"condition:just-displayed": condition},
        )

        case = build_test_design_plan(graph, context=context).deterministic_cases[0]

        self.assertEqual(
            (
                "Не переводя фокус на поле «Имя» и не взаимодействуя с ним, "
                "проверить первоначальное значение: Отображается значение «Иван».",
            ),
            case.steps,
        )
        self.assertNotIn("Перевести фокус", case.steps[0])

    def test_default_with_cursor_oracle_clicks_field_before_observation(self) -> None:
        graph = _graph(
            kind="default",
            fixtures=("+7 (___) ___-__-__",),
            trigger="",
        )
        graph = replace(
            graph,
            properties=(
                replace(
                    graph.properties[0],
                    canonical_statement=(
                        "Для поля «Телефон» по умолчанию отображается шаблон; "
                        "при нажатии на поле курсор отображается внутри скобок."
                    ),
                ),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    atomic_statement=(
                        "Для поля «Телефон» по умолчанию отображается шаблон; "
                        "при нажатии на поле курсор отображается внутри скобок."
                    ),
                    observable_oracle=(
                        "Отображается шаблон `+7 (___) ___-__-__`, курсор расположен внутри скобок."
                    ),
                ),
            ),
        )
        context = replace(_context(), subject_labels={"customer-name": "Телефон"})

        case = build_test_design_plan(graph, context=context).deterministic_cases[0]

        self.assertEqual("Нажать на «Телефон».", case.steps[0])
        self.assertIn("курсор расположен внутри скобок", case.steps[1])

    def test_default_with_interaction_trigger_is_blocked_as_contract_drift(self) -> None:
        plan = build_test_design_plan(
            _graph(
                kind="default",
                fixtures=("Иван",),
                trigger="Перевести фокус в поле «Имя».",
            ),
            context=_context(),
        )

        self.assertEqual(0, len(plan.deterministic_cases))
        self.assertEqual(1, len(plan.blocked_cards))
        self.assertIn("initial-state", plan.blocked_cards[0].reason)

    def test_displayed_condition_replaces_invented_open_with_exact_observation(self) -> None:
        condition = "Отображается блок-повторитель «Клиенты»."
        graph = _graph(
            kind="visibility",
            fixtures=(),
            trigger="Открыть отображаемую строку клиента.",
        )
        graph = replace(
            graph,
            properties=(
                replace(
                    graph.properties[0],
                    canonical_statement=(
                        "Поле «Имя» отображается при отображении "
                        "блока-повторителя."
                    ),
                    condition_clauses=(condition,),
                ),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    coverage_variant="conditional-visibility",
                    condition_key="condition:repeater-displayed",
                    atomic_statement=(
                        "Поле «Имя» отображается при отображении "
                        "блока-повторителя."
                    ),
                    observable_oracle="В строке отображается поле «Имя».",
                ),
            ),
        )
        context = replace(
            _context(),
            condition_preconditions={"condition:repeater-displayed": condition},
        )

        case = build_test_design_plan(graph, context=context).deterministic_cases[0]

        self.assertEqual(
            (
                "Проверить наблюдаемое состояние: В строке отображается поле «Имя».",
            ),
            case.steps,
        )
        self.assertNotIn("Открыть отображаемую", case.steps[0])

    def test_always_visible_without_source_transition_is_blocked_for_classification(self) -> None:
        graph = _graph(
            kind="visibility",
            fixtures=(),
            trigger="Открыть блок «Данные клиента».",
        )
        graph = replace(
            graph,
            properties=(
                replace(
                    graph.properties[0],
                    canonical_statement="Поле «Имя» видимо всегда.",
                ),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    coverage_variant="always-visible",
                    atomic_statement="Поле «Имя» видимо всегда.",
                    observable_oracle="Поле «Имя» отображается.",
                ),
            ),
        )

        plan = build_test_design_plan(graph, context=_context())

        self.assertEqual((), plan.deterministic_cases)
        self.assertIn(
            "classify as calibration/gap",
            plan.blocked_cards[0].reason,
        )

    def test_always_visible_observes_before_and_after_same_subject_add(self) -> None:
        graph, context = _repeater_graph_and_context()
        plan = build_test_design_plan(graph, context=context)
        case = next(item for item in plan.deterministic_cases if item.tc_id == "TC-CUST-0123456789")

        self.assertEqual(
            (
                "Открыть блок «Данные клиента».",
                "Проверить исходное состояние: Кнопка «Добавить» отображается.",
                "Нажать «Добавить».",
                "Проверить состояние после перехода: Кнопка «Добавить» отображается.",
            ),
            case.steps,
        )
        self.assertIn("OBL-ADD", case.traceability)
        self.assertIn("ASSERT-ADD", case.traceability)
        self.assertIn("Нажать «Корзина»", case.postconditions[0])

    def test_repeater_mutations_use_ordinal_rows_and_source_cleanup(self) -> None:
        graph, context = _repeater_graph_and_context()

        plan = build_test_design_plan(graph, context=context)
        add_case = next(item for item in plan.deterministic_cases if item.tc_id == "TC-CUST-ADD0000001")
        delete_case = next(item for item in plan.deterministic_cases if item.tc_id == "TC-CUST-DEL0000001")

        self.assertEqual(("Нажать «Добавить».",), add_case.steps)
        self.assertTrue(all("Корзина" in item for item in add_case.postconditions))
        self.assertIn("первая по порядку", delete_case.test_data[0])
        self.assertIn("вторая по порядку", delete_case.test_data[1])
        self.assertEqual(2, delete_case.preconditions.count("Нажать «Добавить»."))
        self.assertIn("Для первой тестовой строки", delete_case.steps[0])
        self.assertIn("Корзина", delete_case.postconditions[0])
        self.assertNotIn("Не требуются.", add_case.postconditions)
        self.assertNotIn("Не требуются.", delete_case.postconditions)

    def test_contact_person_passive_conditions_become_executable_setup(self) -> None:
        graph, context = _repeater_graph_and_context()
        add_condition = (
            "Кнопка/виджет добавления контактного лица доступна в блоке "
            "`Контактные лица`."
        )
        delete_condition = (
            "В блоке `Контактные лица` отображается строка контактного "
            "лица с кнопкой `Корзина`."
        )
        family_condition = (
            "Поле `Фамилия` в блоке `Контактные лица` после действия "
            "добавления контактного лица."
        )
        graph = replace(
            graph,
            properties=(
                graph.properties[0],
                replace(
                    graph.properties[1],
                    property_kind="source-action",
                    condition_clauses=(add_condition,),
                ),
                replace(
                    graph.properties[2],
                    property_kind="source-action",
                    condition_clauses=(delete_condition,),
                ),
                CoverageProperty(
                    property_id="PROP-FAMILY",
                    assertion_id="ASSERT-FAMILY",
                    property_key="contact-person-family:source-format",
                    subject_key="contact-person-family",
                    property_kind="source-format",
                    source_row_id="SRC-FAMILY",
                    source_path="requirements.xhtml",
                    source_locator="/*/*[4]",
                    source_text_sha256="7" * 64,
                    canonical_statement=(
                        "Поле `Фамилия` в блоке `Контактные лица` "
                        "принимает текстовое значение."
                    ),
                    requirement_codes=("BSR 173",),
                    disposition="tc",
                    polarity="positive",
                    condition_clauses=(family_condition,),
                ),
                *graph.properties[3:],
            ),
            obligations=(
                graph.obligations[0],
                replace(
                    graph.obligations[1],
                    coverage_variant="repeatable-add",
                    condition_key="condition:add-available",
                ),
                replace(
                    graph.obligations[2],
                    coverage_variant="repeatable-delete",
                    condition_key="condition:delete-row-visible",
                ),
                CoverageObligation(
                    obligation_id="OBL-FAMILY",
                    property_id="PROP-FAMILY",
                    atom_id="ATOM-FAMILY",
                    coverage_variant="positive",
                    condition_key="condition:family-after-add",
                    atomic_statement=(
                        "Поле `Фамилия` в блоке `Контактные лица` "
                        "принимает текстовое значение."
                    ),
                    observable_oracle=(
                        "В поле `Фамилия` отображается введённое значение."
                    ),
                    coverage_status="testable",
                    requirement_codes=("BSR 173",),
                    gap_id="",
                    calibration_status="not-required",
                    validation_trigger="Ввести `Иванов` в поле `Фамилия`.",
                    cleanup_strategy="",
                    source_oracle_id="",
                    fixture_values=("Иванов",),
                    calibration_question="",
                ),
            ),
            cases=(
                *graph.cases,
                CoverageCase(
                    case_key=(
                        "contact-person|family|source-format|positive|"
                        "condition:family-after-add"
                    ),
                    tc_id="TC-CUST-FAMILY001",
                    obligation_ids=("OBL-FAMILY",),
                    status="executable",
                ),
            ),
        )
        context = replace(
            context,
            base_preconditions=(),
            subject_labels={
                **context.subject_labels,
                "contact-person-family": "Фамилия",
            },
            condition_preconditions={
                "condition:add-available": add_condition,
                "condition:delete-row-visible": delete_condition,
                "condition:family-after-add": family_condition,
            },
        )

        plan = build_test_design_plan(graph, context=context)
        markdown = render_test_cases(
            plan.deterministic_cases,
            scope_title=context.scope_title,
        )
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=markdown,
            checked_path="shadow.md",
        )

        self.assertTrue(gate.passed, gate.to_dict())
        self.assertNotIn(add_condition, markdown)
        self.assertNotIn(delete_condition, markdown)
        self.assertNotIn(family_condition, markdown)
        family_case = next(
            item for item in plan.deterministic_cases if item.tc_id == "TC-CUST-FAMILY001"
        )
        self.assertIn(
            "Перейти к блоку `Контактные лица`.",
            family_case.preconditions,
        )
        self.assertIn("Нажать «Добавить».", family_case.preconditions)

    def test_exact_condition_is_kept_in_reviewer_projection_not_runtime_setup(self) -> None:
        graph = _graph(trigger="Ввести значение в поле «Имя».")
        condition = "Поле «Имя» отображается."
        graph = replace(
            graph,
            properties=(
                replace(graph.properties[0], condition_clauses=(condition,)),
                *graph.properties[1:],
            ),
            obligations=(
                replace(graph.obligations[0], condition_key="condition:visible"),
            ),
        )
        context = replace(
            _context(),
            condition_preconditions={"condition:visible": condition},
        )
        plan = build_test_design_plan(graph, context=context)
        case = plan.deterministic_cases[0]
        self.assertNotIn(condition, case.preconditions)
        self.assertEqual(("Открыть карточку клиента.",), case.preconditions)
        markdown = render_test_cases((case,), scope_title=context.scope_title)
        gate = validate_suite(
            graph=graph,
            cases=(case,),
            markdown=markdown,
            checked_path="shadow.md",
        )
        self.assertTrue(gate.passed, gate.production_gate)
        reviewer = build_reviewer_request(graph=graph, cases=(case,), gate=gate)
        projected = reviewer["cases"][0]
        self.assertEqual([condition], projected["source"]["condition_clauses"])
        self.assertEqual(
            condition, projected["obligation"]["condition_precondition"]
        )

    def test_missing_fixture_never_becomes_placeholder(self) -> None:
        plan = build_test_design_plan(_graph(fixtures=()), context=_context())

        self.assertEqual(plan.deterministic_cases, ())
        self.assertEqual(plan.writer_cards, ())
        self.assertIn("concrete fixture", plan.blocked_cards[0].reason)

    def test_dictionary_owns_complete_fixture_set(self) -> None:
        plan = build_test_design_plan(
            _graph(kind="dictionary", fixtures=("Друг", "Коллега", "Родственник")),
            context=_context(),
        )

        case = plan.deterministic_cases[0]
        data = case.test_data[0]
        self.assertIn("`Друг`", data)
        self.assertIn("`Коллега`", data)
        self.assertIn("`Родственник`", data)
        self.assertIn("`Друг`", case.expected_result)
        self.assertIn("`Коллега`", case.expected_result)
        self.assertIn("`Родственник`", case.expected_result)

    def test_source_requiredness_materializes_empty_value_and_validation_action(self) -> None:
        graph = _graph(
            kind="source-requiredness",
            fixtures=(),
            trigger="Проверить обязательность поля «Имя».",
        )
        graph = replace(
            graph,
            properties=(replace(graph.properties[0], polarity="positive"), *graph.properties[1:]),
            obligations=(replace(graph.obligations[0], coverage_variant="required"),),
        )

        case = build_test_design_plan(graph, context=_context()).deterministic_cases[0]

        self.assertEqual("негативный", case.case_type)
        self.assertIn("оставить пустым", case.test_data[0])
        self.assertEqual(
            (
                "Оставить поле «Имя» пустым.",
                "Выполнить действие проверки/валидации для поле «Имя»: "
                "Проверить обязательность поля «Имя».",
            ),
            case.steps,
        )

    def test_phone_exact_length_case_materializes_negative_classes(self) -> None:
        graph = _graph(kind="positive-input", fixtures=("9991234567",))
        graph = replace(
            graph,
            properties=(
                replace(
                    graph.properties[0],
                    canonical_statement=(
                        "Поле «Телефон» допускает только 10 числовых символов."
                    ),
                ),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    observable_oracle="Допускаются только 10 числовых символов.",
                    validation_trigger="Ввести номер телефона.",
                ),
            ),
        )
        context = replace(_context(), subject_labels={"customer-name": "Телефон"})

        case = build_test_design_plan(graph, context=context).deterministic_cases[0]

        joined_data = "\n".join(case.test_data)
        joined_steps = "\n".join(case.steps)
        self.assertIn("9991234567", joined_data)
        self.assertIn("999123456", joined_data)
        self.assertIn("99912345678", joined_data)
        self.assertIn("99912A4567", joined_data)
        self.assertIn("999123456", joined_steps)
        self.assertIn("99912345678", joined_steps)
        self.assertIn("99912A4567", joined_steps)

    def test_requiredness_requires_explicit_trigger(self) -> None:
        plan = build_test_design_plan(
            _graph(kind="requiredness", fixtures=()),
            context=_context(),
        )
        self.assertEqual(plan.deterministic_cases, ())
        self.assertEqual(plan.writer_cards, ())
        self.assertIn("validation trigger", plan.blocked_cards[0].reason)

    def test_conditional_case_requires_typed_precondition(self) -> None:
        graph = _graph()
        graph = replace(
            graph,
            obligations=(replace(graph.obligations[0], condition_key="manual-mode"),),
        )
        with self.assertRaisesRegex(DesignError, "condition_preconditions"):
            build_test_design_plan(graph, context=_context())

    def test_design_context_cannot_inject_unregistered_ui_behavior(self) -> None:
        context = replace(
            _context(),
            base_preconditions=("Открыть скрытую административную панель.",),
        )
        with self.assertRaisesRegex(DesignError, "source-backed context statement"):
            build_test_design_plan(_graph(), context=context)

    def test_subject_label_must_be_source_backed_and_token_bounded(self) -> None:
        context = replace(
            _context(),
            subject_labels={"customer-name": "поле «Имя» администратора"},
        )
        with self.assertRaisesRegex(DesignError, "source-backed graph projection"):
            build_test_design_plan(_graph(), context=context)

    def test_design_context_rejects_unknown_subject_key(self) -> None:
        context = replace(
            _context(),
            subject_labels={
                "customer-name": "поле «Имя»",
                "invented-control": "кнопка «Удалить всё»",
            },
        )
        with self.assertRaisesRegex(DesignError, "unknown=.*invented-control"):
            build_test_design_plan(_graph(), context=context)

    def test_scope_title_must_be_source_backed(self) -> None:
        context = replace(_context(), scope_title="Скрытая административная панель")
        with self.assertRaisesRegex(DesignError, "scope_title"):
            build_test_design_plan(_graph(), context=context)

    def test_design_context_package_must_match_bound_obligations(self) -> None:
        with self.assertRaisesRegex(DesignError, "package_id"):
            validate_design_context_for_graph(
                _graph(),
                replace(_context(), package_id="WP-FORGED"),
                expected_package_id="WP-01",
            )

    def test_calibration_candidate_stays_in_same_suite_with_markers(self) -> None:
        plan = build_test_design_plan(
            _graph(
                kind="requiredness",
                fixtures=(),
                status="candidate-ui-calibration",
                trigger="Нажать «Продолжить».",
                question="Как система обозначает незаполненное обязательное поле?",
            ),
            context=_context(),
        )
        text = render_test_cases(
            plan.deterministic_cases,
            scope_title="Данные клиента",
        )

        self.assertIn("candidate-ui-calibration", text)
        self.assertIn("SO-001", text)
        self.assertIn("Нажать «Продолжить».", text)
        self.assertIn("Как система обозначает", text)

    def test_candidate_title_excludes_process_markers_and_note_becomes_question(self) -> None:
        graph = _graph(
            kind="source-exact-length",
            fixtures=("91234567890",),
            status="candidate-ui-calibration",
            trigger="Ввести «91234567890» в поле «Имя».",
            question=(
                "Точная UI-реакция требует candidate-ui-calibration; "
                "фильтрация и сообщение не утверждаются."
            ),
        )
        graph = replace(
            graph,
            properties=(
                replace(graph.properties[0], polarity="negative"),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    atomic_statement=(
                        "Значение «91234567890» не соответствует правилу точной "
                        "длины; точная UI-реакция требует калибровки."
                    ),
                    observable_oracle=(
                        "Значение не соответствует правилу точной длины; точный "
                        "способ отклонения требует UI-калибровки."
                    ),
                ),
            ),
        )

        plan = build_test_design_plan(graph, context=_context())
        case = plan.deterministic_cases[0]
        self.assertNotRegex(case.title.casefold(), r"калибр|candidate-ui")
        self.assertTrue(case.calibration_question.endswith("?"))
        self.assertIn("91234567890", case.calibration_question)
        text = render_test_cases((case,), scope_title="Данные клиента")
        report = validate_production_tc_content(text, checked_path="shadow.md")
        self.assertTrue(report.passed, report.as_dict())

    def test_candidate_title_does_not_split_requirement_reference_in_quotes(self) -> None:
        graph = _graph(
            kind="source-format",
            fixtures=("912345678",),
            status="candidate-ui-calibration",
            trigger="Ввести «912345678» в поле «Имя».",
            question="Какой точный UI-отклик возникает?",
        )
        graph = replace(
            graph,
            properties=(
                replace(graph.properties[0], polarity="negative"),
                *graph.properties[1:],
            ),
            obligations=(
                replace(
                    graph.obligations[0],
                    atomic_statement=(
                        "Поле «Имя»: значение не соответствует ограничению "
                        "источника «BSR 182. Только 10 символов». Точный способ "
                        "отклонения требует UI-калибровки."
                    ),
                    observable_oracle=(
                        "Значение не соответствует ограничению; точный UI-отклик "
                        "требует калибровки."
                    ),
                ),
            ),
        )

        case = build_test_design_plan(graph, context=_context()).deterministic_cases[0]

        self.assertIn("BSR 182. Только 10 символов»", case.title)
        self.assertEqual(case.title.count("«"), case.title.count("»"))
        self.assertNotRegex(case.title.casefold(), r"калибр|ui-отклик")

    def test_state_change_never_gets_default_no_cleanup_case(self) -> None:
        plan = build_test_design_plan(
            _graph(kind="repeater-delete", cleanup="Удалить созданную строку."),
            context=_context(),
        )
        self.assertEqual(plan.deterministic_cases, ())
        self.assertEqual(plan.writer_cards[0].cleanup_strategy, "Удалить созданную строку.")

    def test_rendered_simple_case_passes_production_gate(self) -> None:
        plan = build_test_design_plan(_graph(), context=_context())
        text = render_test_cases(plan.deterministic_cases, scope_title="Данные клиента")

        report = validate_production_tc_content(text, checked_path="shadow.md")
        self.assertTrue(report.passed, report.as_dict())

    def test_calibration_render_fails_without_question(self) -> None:
        plan = build_test_design_plan(_graph(), context=_context())
        case = replace(
            plan.deterministic_cases[0],
            status="candidate-ui-calibration",
            calibration_question="",
        )
        with self.assertRaisesRegex(DesignError, "without a question"):
            render_test_cases((case,), scope_title="Данные клиента")


if __name__ == "__main__":
    unittest.main()
