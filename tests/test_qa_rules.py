from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class QaRulesTests(unittest.TestCase):
    def test_test_case_format_contains_atomicity_and_field_order_rules(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "test-case-format.md").read_text(encoding="utf-8")
        self.assertIn("Если тест-кейс можно разделить", content)
        self.assertIn("Не объединяй в одном тест-кейсе", content)
        self.assertIn("сначала проверка видимости поля", content)
        self.assertIn("затем проверка редактируемости поля", content)
        self.assertIn("потом атомарные позитивные проверки", content)
        self.assertIn("потом атомарные негативные проверки", content)
        self.assertIn("Правила организации набора", content)
        self.assertIn("группируй `TC-*` по функциональности", content)
        self.assertIn("Каждый `TC-*` должен иметь `package_id`", content)
        self.assertIn("не должен смешивать разные `package_id`", content)
        self.assertIn("Числовой суффикс `TC-*` должен быть сквозным", content)
        self.assertIn("не выполняй тихую перенумерацию", content)

    def test_coverage_checklist_contains_field_level_order_rule(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "coverage-checklist.md").read_text(encoding="utf-8")
        self.assertIn("Порядок проверок для конкретного поля", content)
        self.assertIn("проверка видимости поля", content)
        self.assertIn("проверка редактируемости поля", content)
        self.assertIn("атомарные позитивные проверки", content)
        self.assertIn("атомарные негативные проверки", content)

    def test_coverage_checklist_contains_high_risk_test_design_domains(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "coverage-checklist.md").read_text(encoding="utf-8")
        for token in (
            "Role / permission / status coverage",
            "role-permission",
            "status-lifecycle",
            "expected access",
            "Business status lifecycle coverage",
            "current_status x action -> expected_status / forbidden / unclear",
            "Decision table coverage",
            "conditions | allowed values | combination | expected behavior | atom_id | TC/gap",
            "Dependency matrix coverage",
            "controlling_value | dependent_field | visibility | required | editable/enabled",
        ):
            self.assertIn(token, content)

    def test_coverage_checklist_contains_data_and_flow_test_design_domains(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "coverage-checklist.md").read_text(encoding="utf-8")
        for token in (
            "Numeric input coverage",
            "`min-1`, `min`, `min+1`",
            "`max-1`, `max`, `max+1`",
            "Date/time coverage",
            "`start = end`",
            "`start > end`",
            "timezone",
            "Length boundary coverage",
            "`0/empty`",
            "emoji",
            "Persistence and navigation coverage",
            "browser back",
            "Scenario / use-case coverage",
            "scenario-use-case",
        ):
            self.assertIn(token, content)

    def test_coverage_checklist_contains_system_and_security_domains(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "coverage-checklist.md").read_text(encoding="utf-8")
        for token in (
            "Table/list coverage",
            "table-list",
            "exact/partial search",
            "pagination first/last/next/prev",
            "File upload/download coverage",
            "MIME mismatch",
            "remove/reupload",
            "Async / race condition coverage",
            "double click",
            "stale form",
            "Server-side validation / API bypass coverage",
            "api-server-validation",
            "direct request",
            "Integration coverage",
            "invalid mapping",
            "stale reference data",
            "Security-oriented negative coverage",
            "CSV/formula injection",
            "path traversal",
        ):
            self.assertIn(token, content)

    def test_coverage_checklist_contains_pairwise_and_calculation_oracle_rules(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "coverage-checklist.md").read_text(encoding="utf-8")
        for token in (
            "Combinatorial / pairwise coverage",
            "dimension `pairwise`",
            "| factor | values | source_ref | constraints / impossible combinations |",
            "| combination_id | factor_values | coverage_strength | reason | linked_atoms | TC/gap |",
            "coverage_strength = 2-way | 3-way | t-way",
            "high-risk combinations",
            "Расчетные сценарии и calculation oracle",
            "dimension `calculation`",
            "формулу или ссылку на формулу/правило расчета",
            "вручную вычисленный expected result",
            "rounding rule",
            "Не используй `расчет выполнен корректно`",
        ):
            self.assertIn(token, content)

    def test_test_case_format_contains_priority_and_calculation_oracle_rules(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "test-case-format.md").read_text(encoding="utf-8")
        for token in (
            "Правила приоритизации",
            "`High`: деньги, права доступа",
            "`Medium`: основные пользовательские сценарии",
            "`Low`: редкие UI-состояния",
            "high-risk domain",
            "formula/source reference",
            "входные значения и вручную вычисленный expected result",
        ):
            self.assertIn(token, content)

    def test_test_case_format_contains_observable_oracle_taxonomy(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "test-case-format.md").read_text(encoding="utf-8")
        for token in (
            "Классы Наблюдаемого Oracle",
            "`field-state`",
            "`transition-state`",
            "`save-state`",
            "`message-marker`",
            "`visibility-state`",
            "`list-state`",
            "Запрещено заменять oracle абстрактным verdict",
        ):
            self.assertIn(token, content)

    def test_test_case_runtime_format_contains_canary_regression_guards(self) -> None:
        runtime = (ROOT_DIR / "references" / "qa" / "test-case-runtime-format.md").read_text(encoding="utf-8")
        full = (ROOT_DIR / "references" / "qa" / "test-case-format.md").read_text(encoding="utf-8")
        gate = (ROOT_DIR / "references" / "agent" / "writer-quality-gate-format.md").read_text(encoding="utf-8")
        taxonomy = (ROOT_DIR / "references" / "agent" / "test-design-defect-taxonomy.md").read_text(encoding="utf-8")

        for token in (
            "source-rule oracle",
            "по правилу видимости из источника",
            "placeholder `-`",
            "Активировать элемент",
            "Изменить значение на тестовое значение",
            "все и только активные значения",
            "Test-design-derived checks",
            "v2 obligation",
            "Постусловия",
        ):
            self.assertIn(token, runtime)

        for token in (
            "Правила для editability TC",
            "Test-design Derived Checks",
            "placeholder `-`",
            "по правилу из источника",
            "все и только активные значения DICT-*",
        ):
            self.assertIn(token, full)

        for token in (
            "`tc-regression-smells`",
            "source-rule oracle",
            "generic editability steps",
            "derived-obligation",
        ):
            self.assertIn(token, gate)

        for defect_class in (
            "`traceability-placeholder`",
            "`source-rule-oracle`",
            "`generic-editability`",
            "`derived-obligation-contamination`",
            "`template-postcondition-noise`",
        ):
            self.assertIn(defect_class, taxonomy)

    def test_test_case_format_contains_field_level_input_restriction_rule(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "test-case-format.md").read_text(encoding="utf-8")
        for token in (
            "Если ФТ задает ограничение ввода или формата для конкретного поля",
            "enforcement на уровне самого поля",
            "`только N цифр`",
            "`максимальная длина`",
            "`точная длина`",
            "недопустимый символ не добавляется",
            "символ сверх максимальной или точной длины не добавляется",
            "Не проверяй field-level input restrictions через `Сохранить`, `Следующий шаг`",
            "`1234567`",
            "седьмая цифра `7` не добавляется",
        ):
            self.assertIn(token, content)

    def test_test_case_format_contains_intention_level_field_steps_rule(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "test-case-format.md").read_text(encoding="utf-8")
        examples = (ROOT_DIR / "references" / "qa" / "test-case-style-examples.md").read_text(encoding="utf-8")
        for token in (
            "Описывай действие в шагах на уровне намерения пользователя",
            "`Ввести <значение> в поле <название>`",
            "`Указать <дату> в поле <название>`",
            "`щелкнуть поле`",
            "`кликнуть поле`",
            "`нажать на поле`",
            "`набрать`",
            "`Активировать поле <название>`",
        ):
            self.assertIn(token, content)
        self.assertIn("## Шаги: mouse-specific ввод в поле", examples)
        self.assertIn("1. щелкнуть поле `Сумма на руки` и набрать `123`", examples)
        self.assertIn("1. Ввести `123` в поле `Сумма на руки`.", examples)

    def test_writer_and_reviewer_skills_reference_current_contracts(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("review-findings-format.md", writer)
        self.assertIn("traceability-matrix-format.md", writer)
        self.assertIn("не придумывай поведение, а выноси это в `coverage gaps`", writer)
        self.assertIn("`full`", reviewer)
        self.assertIn("`traceability`", reviewer)
        self.assertIn("`structure`", reviewer)
        self.assertIn("`test-design`", reviewer)
        self.assertIn("`traceability` или `full`", reviewer)
        self.assertIn("порядок `позитивные -> негативные`", reviewer)
        self.assertIn("сквозную нумерацию `TC-*`", reviewer)
        self.assertIn("Package Test Design Plan", reviewer)
        self.assertIn("test-case-forbidden-formulation-smell", writer)
        self.assertIn("test-case-abstract-oracle-smell", writer)
        self.assertIn("test-case-input-restriction-transition-oracle-smell", writer)
        self.assertIn("test-case-mechanical-field-step-smell", writer)

    def test_reviewer_describes_canonical_mode_order(self) -> None:
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Выполняет `traceability`, затем `structure`, затем `test-design`", reviewer)

    def test_traceability_rules_define_pdf_structure_cross_check(self) -> None:
        rules = (ROOT_DIR / "references" / "qa" / "traceability-rules.md").read_text(encoding="utf-8")
        self.assertIn("PDF-версия основного ФТ", rules)
        self.assertIn("structural cross-check", rules)
        self.assertIn("не как замена текста основного ФТ", rules)

    def test_traceability_rules_define_atomic_ledger_first_workflow(self) -> None:
        rules = (ROOT_DIR / "references" / "qa" / "traceability-rules.md").read_text(encoding="utf-8")
        checklist = (ROOT_DIR / "references" / "qa" / "coverage-checklist.md").read_text(encoding="utf-8")
        self.assertIn("Atomic Requirements Ledger", rules)
        self.assertIn("одна строка = одно атомарное утверждение", rules)
        self.assertIn("стабильный локальный идентификатор", rules)
        self.assertIn("atomic-ledger-first workflow", checklist)
        self.assertIn("writer self-check", checklist)

    def test_writer_and_reviewer_enforce_strong_prompt_behaviors(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        findings = (ROOT_DIR / "references" / "qa" / "review-findings-format.md").read_text(encoding="utf-8")
        self.assertIn("writer строит atomic requirements ledger", writer)
        self.assertIn("writer self-check", writer)
        self.assertIn("canonical fields", writer)
        self.assertIn("hallucinated assumptions", reviewer)
        self.assertIn("unsupported expected-result specificity", reviewer)
        self.assertIn("недопустимые enum-значения", findings)
        self.assertIn("blocking `structure` / `format` finding", findings)


    def test_test_case_example_warns_against_unsupported_ui_specificity(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "test-case-format.md").read_text(encoding="utf-8")
        self.assertIn("Example Specificity Warning", content)
        self.assertIn("exact red highlight", content)
        self.assertIn("coverage gap", content)
        self.assertIn("unclear", content)

    def test_review_findings_require_coverage_dimension_vocabulary(self) -> None:
        findings = (ROOT_DIR / "references" / "qa" / "review-findings-format.md").read_text(encoding="utf-8")
        for token in (
            "`coverage_dimension`",
            "role-permission",
            "status-lifecycle",
            "pairwise",
            "api-server-validation",
            "security",
            "async",
            "numeric",
            "date-time",
            "length",
            "persistence",
            "scenario-use-case",
            "table-list",
            "file-upload",
            "calculation",
        ):
            self.assertIn(token, findings)

    def test_scope_coverage_gaps_define_test_design_gap_fields(self) -> None:
        gaps = (ROOT_DIR / "references" / "agent" / "scope-coverage-gaps-format.md").read_text(encoding="utf-8")
        for token in (
            "Test-design Coverage Gap Fields",
            "`affected_test_design_dimension`",
            "`blocks_ready_for_review`",
            "`why_expected_result_not_derivable`",
            "**Affected Test-design Dimension:**",
            "**Blocks Ready For Review:**",
        ):
            self.assertIn(token, gaps)


if __name__ == "__main__":
    unittest.main()
