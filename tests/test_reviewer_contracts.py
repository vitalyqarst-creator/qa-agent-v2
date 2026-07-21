from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReviewerContractTests(unittest.TestCase):
    def test_reviewer_skill_accepts_all_review_modes(self) -> None:
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`review_mode = full | traceability | structure | test-design`", reviewer)
        self.assertIn("`full` — канонический режим по умолчанию для direct review", reviewer)
        self.assertIn("Direct `full` не заменяет session-based sign-off", reviewer)

    def test_reviewer_skill_defines_session_based_modes(self) -> None:
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")

        for token in (
            "`scope_gap_review`",
            "`source_assertion_review`",
            "`structure_preflight`",
            "`semantic_traceability_test_design`",
            "`structure_format_final`",
            "`semantic_regression`",
            "scope-gap-review.md",
            "source-assertion-review.json",
            "structure_preflight -> semantic_traceability_test_design",
            "round-cap-reached",
        ):
            self.assertIn(token, reviewer)

    def test_reviewer_signoff_requires_validator_gate(self) -> None:
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        output_format = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")
        validator = (ROOT_DIR / "scripts" / "validate_agent_artifacts.py").read_text(encoding="utf-8")

        for token in (
            "validate_agent_artifacts.py --root <ft-package> --json",
            "split test-design artifacts",
        ):
            self.assertIn(token, reviewer)
            self.assertIn(token, output_format)

        self.assertIn("validator_checked: yes", reviewer)
        self.assertIn("**validator_checked:** yes", output_format)
        for token in (
            "missing full-valid fixture for negative transition",
            "requiredness without empty/marker check",
            "metadata behavior smell",
            "metadata cross-section conflict",
        ):
            self.assertIn(token, output_format)
        self.assertIn('"validator_checked"', validator)
        self.assertIn("REVIEWER_SIGNOFF_YES_FIELDS", validator)

    def test_reviewer_signoff_field_validation_requires_validator_checked(self) -> None:
        validator = load_validator_module()
        valid_fields = {
            "traceability_checked": "yes",
            "structure_checked": "yes",
            "test_case_grouping_checked": "yes",
            "test_case_numbering_checked": "yes",
            "test_design_checked": "yes",
            "applicability_dimensions_checked": "yes",
            "validator_checked": "yes",
            "blocking_findings_absent": "yes",
            "traceability_gaps_absent": "yes",
            "known_unclear_items": "none",
            "sign_off_rationale": "Final reviewer pass checked the current scope artifacts.",
        }

        self.assertEqual([], validator.reviewer_signoff_field_issues(valid_fields))

        missing_validator = dict(valid_fields)
        del missing_validator["validator_checked"]
        self.assertIn("missing:validator_checked", validator.reviewer_signoff_field_issues(missing_validator))

        failed_validator = dict(valid_fields)
        failed_validator["validator_checked"] = "no"
        self.assertIn("validator_checked=no", validator.reviewer_signoff_field_issues(failed_validator))

    def test_reviewer_skill_returns_findings_and_traceability_matrix(self) -> None:
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("structured findings artifact", reviewer)
        self.assertIn("при `traceability` и `full`", reviewer)
        self.assertIn("отдельный traceability matrix artifact", reviewer)
        self.assertIn("обязательный `.xlsx`-дубль", reviewer)

    def test_review_findings_format_defines_mode_specific_requirements(self) -> None:
        findings = (ROOT_DIR / "references" / "qa" / "review-findings-format.md").read_text(encoding="utf-8")
        self.assertIn("`review_mode`", findings)
        self.assertIn("`review_mode` = `traceability | structure | test-design`", findings)
        self.assertIn("Для `traceability` finding", findings)
        self.assertIn("Для `structure` finding", findings)
        self.assertIn("Для `test-design` finding", findings)
        self.assertIn("`coverage_gap`", findings)

    def test_traceability_matrix_format_defines_atomic_rows_and_statuses(self) -> None:
        matrix = (ROOT_DIR / "references" / "qa" / "traceability-matrix-format.md").read_text(encoding="utf-8")
        self.assertIn("Одна строка матрицы = одно атомарное утверждение", matrix)
        self.assertIn("`coverage_status` = `covered | gap | unclear`", matrix)
        self.assertIn("`gap` означает отсутствие покрытия", matrix)
        self.assertIn("`unclear` означает", matrix)

    def test_traceability_matrix_format_lists_required_columns(self) -> None:
        matrix = (ROOT_DIR / "references" / "qa" / "traceability-matrix-format.md").read_text(encoding="utf-8")
        for token in (
            "`atom_id`",
            "`req_id`",
            "`source_path`",
            "`atomic_statement`",
            "`field_or_block`",
            "`condition`",
            "`expected_behavior`",
            "`covered_by_tc`",
            "`coverage_status`",
            "`gap_note`",
        ):
            self.assertIn(token, matrix)

    def test_traceability_matrix_format_requires_xlsx_duplicate(self) -> None:
        matrix = (ROOT_DIR / "references" / "qa" / "traceability-matrix-format.md").read_text(encoding="utf-8")
        self.assertIn("дублирующая `.xlsx`-версия", matrix)
        self.assertIn("`round-N-traceability-matrix.xlsx`", matrix)
        self.assertIn("те же обязательные колонки и те же строки", matrix)
        self.assertIn("Markdown остается каноническим текстовым artifact", matrix)


    def test_reviewer_test_design_rubric_eval_cases_exist(self) -> None:
        evals = (ROOT_DIR / "evals" / "reviewer-test-design-rubric-cases.md").read_text(encoding="utf-8")
        for token in (
            "Eval Case 1 - ненаблюдаемый expected result",
            "Eval Case 2 - неподтвержденная точная UI-реакция",
            "Eval Case 3 - проверяемое действие спрятано в предусловиях",
            "Eval Case 4 - positive и negative ветки смешаны",
            "Eval Case 5 - отсутствует negative branch, но основной positive case есть",
            "Eval Case 6 - over-splitting эквивалентных значений списка",
            "Eval Case 7 - неподтвержденное missing behavior должно стать `unclear`",
            "Eval Case 8 - приемлемый кейс без finding",
            "Eval Case 9 - отсутствует pairwise table при 3+ факторах",
            "Eval Case 10 - high-risk access case имеет заниженный priority",
            "Eval Case 11 - расчетный кейс без calculation oracle",
            "Eval Case 12 - applicability matrix ссылается на TC, который не покрывает dimension",
        ):
            self.assertIn(token, evals)

        self.assertGreaterEqual(evals.count("**Expected Reviewer Output:**"), 12)
        self.assertIn("`severity`: `error`", evals)
        self.assertIn("`severity`: `warning`", evals)
        self.assertIn("Нет `test-design` finding.", evals)
        self.assertIn("пометить missing behavior как `unclear`", evals)
        self.assertIn("`coverage_dimension`: `pairwise`", evals)
        self.assertIn("`coverage_dimension`: `role-permission`", evals)
        self.assertIn("`coverage_dimension`: `calculation`", evals)
        self.assertIn("`coverage_dimension`: `api-server-validation`", evals)
        self.assertIn("Combinatorial Coverage Table", evals)
        self.assertIn("заниженный priority", evals)
        self.assertIn("calculation oracle", evals)
        self.assertIn("direct/API payload bypass", evals)


    def test_reviewer_requires_applicability_matrix_and_coverage_dimension(self) -> None:
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        rubric = (ROOT_DIR / "references" / "qa" / "test-design-review-rubric.md").read_text(encoding="utf-8")

        self.assertIn("Test-design applicability matrix", reviewer)
        self.assertIn("coverage_dimension", reviewer)
        self.assertIn("Ревью Test-design applicability matrix", rubric)
        self.assertIn("Test-design applicability matrix", rubric)
        self.assertIn("coverage_dimension", rubric)
        self.assertIn("реально проверяют именно эту dimension", rubric)
        self.assertIn("linked to a non-covering `TC-*`", reviewer)
        self.assertIn("set organization drift", rubric)
        self.assertIn("сквозной последовательностью", rubric)

    def test_reviewer_rubric_checks_pairwise_priority_and_calculation_oracles(self) -> None:
        rubric = (ROOT_DIR / "references" / "qa" / "test-design-review-rubric.md").read_text(encoding="utf-8")

        for token in (
            "Ревью Risk / Priority Map",
            "High-risk atoms присутствуют в map",
            "`risk_level = high`",
            "`required_priority = High`",
            "Расчетный тест-кейс не содержит formula/source reference",
            "High-risk atom не имеет `High` priority test case",
            "Если применим `pairwise`",
            "selected combinations",
            "`Приоритет` соответствует риску атома",
            "Расчетные кейсы содержат oracle",
            "rounding/precision/currency/unit",
        ):
            self.assertIn(token, rubric)

    def test_reviewer_rubric_blocks_canary_regression_smells(self) -> None:
        rubric = (ROOT_DIR / "references" / "qa" / "test-design-review-rubric.md").read_text(encoding="utf-8")

        for token in (
            "source-rule oracle",
            "по правилу видимости из источника",
            "Traceability fields contain placeholder elements",
            "`; \\`-\\`;`",
            "Editability TC does not name concrete old/new values",
            "Closed dictionary/list TC checks active values but does not verify absence of extra values",
            "Test-design-derived check",
            "nondeterministic-alternative-oracle",
            "executable-over-unresolved-mechanism",
            "ambiguous-ui-alias-step",
            "derived-setup-behavior-as-source",
            "символ отклонен или значение остается незаполненным/предыдущим",
            "`traceability-placeholder`",
            "`source-rule-oracle`",
            "`generic-editability`",
            "`derived-obligation-contamination`",
            "blocking for semantic sign-off",
        ):
            self.assertIn(token, rubric)


if __name__ == "__main__":
    unittest.main()
