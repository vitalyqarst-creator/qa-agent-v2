from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.obligation_gate import (
    materialize_draft_dictionary_projections,
    materialize_draft_reference_fixtures,
    validate_draft_obligation_coverage,
    validate_writer_dictionary_ownership,
)
from test_case_agent.review_cycle.prepared_package import (
    PreparedDictionaryRequirement,
    PreparedDictionaryValue,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
)
from test_case_agent.review_cycle.runtime import write_json_atomic


class PreparedObligationGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.draft = self.root / "draft.md"
        self.obligations_path = self.root / "atomic-obligations.json"
        obligations = PreparedObligationSet.create(
            package_id="pkg-gate",
            obligations=(
                PreparedObligation(
                    "ATOM-001", ("SRC-1",), "Statement 1", "Visible result 1", "Test 1",
                    "testable", "", (), "",
                ),
                PreparedObligation(
                    "ATOM-002", ("SRC-2",), "Statement 2", "Visible result 2", "Test 2",
                    "testable", "", (), "",
                ),
                PreparedObligation(
                    "ATOM-003", ("SRC-3",), "Internal state", "", "Record gap",
                    "gap", "GAP-001", (), "",
                ),
            ),
            coverage_gaps=(
                PreparedGap("GAP-001", ("SRC-3",), "Not observable", "Ask for API evidence", False),
            ),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

    def _validate(self, text: str):
        self.draft.write_text(text, encoding="utf-8")
        return validate_draft_obligation_coverage(
            draft_path=self.draft, obligations_path=self.obligations_path
        )

    def test_passes_when_every_testable_atom_is_traced(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001; SRC-1\n\n"
            "## TC-002\n**Traceability:** ATOM-002; SRC-2\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual(("ATOM-001", "ATOM-002"), result.covered_obligations)

    def test_reports_missing_unknown_and_non_testable_atoms(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, SRC-1, ATOM-003, ATOM-404\n"
        )
        finding_ids = {item["id"] for item in result.findings}
        self.assertFalse(result.passed)
        self.assertEqual(
            {
                "missing-testable-obligation-coverage",
                "unknown-atomic-obligation",
                "non-testable-obligation-used-as-test",
            },
            finding_ids,
        )

    def test_plain_atom_mentions_outside_traceability_do_not_count(self) -> None:
        result = self._validate("## TC-001\nNote: ATOM-001 and ATOM-002.\n")
        self.assertFalse(result.passed)
        self.assertEqual(2, len(result.findings))

    def test_set_level_gap_after_last_tc_is_not_absorbed(self) -> None:
        result = self._validate(
            "## TC-001\n"
            "### Шаги\n1. Проверить.\n"
            "**Трассировка:** ATOM-001, SRC-1, ATOM-002, SRC-2\n\n"
            "## Coverage gaps\n"
            "**Трассировка:** ATOM-003\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual("prepared-package-obligation-gate-v4", result.as_dict()["validator"])

    def test_bulleted_traceability_inside_tc_is_supported(self) -> None:
        result = self._validate(
            "## TC-001\n- **Трассировка:** ATOM-001; SRC-1\n\n"
            "## TC-002\n* **Traceability:** ATOM-002; SRC-2\n"
        )
        self.assertTrue(result.passed)

    def test_nested_headings_stay_inside_tc_and_parent_heading_ends_it(self) -> None:
        result = self._validate(
            "### TC-001\n"
            "#### Предусловия\nText.\n"
            "#### Traceability\n**Трассировка:** ATOM-001, SRC-1, ATOM-002, SRC-2\n\n"
            "## Неисполняемые границы покрытия\n"
            "**Трассировка:** ATOM-003\n"
        )
        self.assertTrue(result.passed)

    def test_next_tc_ends_previous_even_at_deeper_heading_level(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001; SRC-1\n\n"
            "### TC-002\n**Трассировка:** ATOM-002; SRC-2\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual(2, result.test_case_count)

    def test_headings_and_atoms_inside_fenced_code_are_ignored(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, SRC-1, ATOM-002, SRC-2\n\n"
            "```markdown\n## TC-FAKE\n**Трассировка:** ATOM-003\n```\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual(1, result.test_case_count)

    def test_real_gap_traceability_inside_tc_still_blocks(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, SRC-1, ATOM-002, SRC-2, ATOM-003\n"
        )
        self.assertFalse(result.passed)
        self.assertIn(
            "non-testable-obligation-used-as-test",
            {item["id"] for item in result.findings},
        )

    def test_v5_obligation_atom_pair_covers_testable_child_without_claiming_gap_child(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-v5-pair",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-1",),
                    atomic_statement="Visible behavior",
                    observable_oracle="Visible result",
                    test_intent="Verify behavior",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                ),
                PreparedObligation(
                    obligation_id="OBL-002",
                    atom_id="ATOM-001",
                    source_refs=("SRC-1",),
                    atomic_statement="Unobservable constraint",
                    observable_oracle="",
                    test_intent="Preserve gap",
                    coverage_status="gap",
                    gap_id="GAP-001",
                    dictionary_refs=(),
                    notes="",
                ),
            ),
            coverage_gaps=(
                PreparedGap("GAP-001", ("SRC-1",), "Not observable", "Preserve", False),
            ),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            "## TC-001\n**Трассировка:** OBL-001; ATOM-001; SRC-1\n"
        )

        self.assertTrue(result.passed)
        self.assertEqual(("OBL-001",), result.covered_obligations)

    def test_v5_atom_without_obligation_id_is_rejected(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-v5-pair",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-1",),
                    atomic_statement="Visible behavior",
                    observable_oracle="Visible result",
                    test_intent="Verify behavior",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate("## TC-001\n**Трассировка:** ATOM-001\n")

        self.assertFalse(result.passed)
        self.assertIn(
            "atom-without-prepared-obligation",
            {item["id"] for item in result.findings},
        )

    def test_set_level_unknown_atom_does_not_attach_to_last_tc(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, SRC-1, ATOM-002, SRC-2\n\n"
            "## Coverage gaps\n- **Трассировка:** ATOM-404\n"
        )
        self.assertTrue(result.passed)

    def test_v5_missing_source_ref_is_rejected_inside_linked_tc(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-v5-source",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01", "BSR 101"),
                    atomic_statement="Visible behavior",
                    observable_oracle="Visible result",
                    test_intent="Verify behavior",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            "## TC-001\n**Трассировка:** OBL-001; ATOM-001; SRC-001.P01\n"
        )

        self.assertFalse(result.passed)
        finding = next(
            item for item in result.findings
            if item["id"] == "missing-obligation-source-reference"
        )
        self.assertEqual("TC-001", finding["tc_id"])
        self.assertEqual(["BSR 101"], finding["missing_references"])

    def test_source_ref_in_wrong_tc_does_not_satisfy_obligation(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-v5-wrong-tc",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001", atom_id="ATOM-001",
                    source_refs=("SRC-001",), atomic_statement="One",
                    observable_oracle="One visible", test_intent="Test one",
                    coverage_status="testable", gap_id="", dictionary_refs=(), notes="",
                ),
                PreparedObligation(
                    obligation_id="OBL-002", atom_id="ATOM-002",
                    source_refs=("SRC-002",), atomic_statement="Two",
                    observable_oracle="Two visible", test_intent="Test two",
                    coverage_status="testable", gap_id="", dictionary_refs=(), notes="",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            "## TC-001\n**Трассировка:** OBL-001; ATOM-001; SRC-002\n\n"
            "## TC-002\n**Трассировка:** OBL-002; ATOM-002; SRC-001; SRC-002\n"
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "missing-obligation-source-reference",
            {item["id"] for item in result.findings},
        )

    def test_dictionary_ref_is_required_and_grouped_union_passes(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-v5-grouped",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001", atom_id="ATOM-001",
                    source_refs=("SRC-001",), atomic_statement="Dictionary value one",
                    observable_oracle="One visible", test_intent="Test one",
                    coverage_status="testable", gap_id="", dictionary_refs=("DICT-001",),
                    notes="", planned_test_case_id="TC-001",
                ),
                PreparedObligation(
                    obligation_id="OBL-002", atom_id="ATOM-002",
                    source_refs=("SRC-002", "BSR 202"), atomic_statement="Two",
                    observable_oracle="Two visible", test_intent="Test two",
                    coverage_status="testable", gap_id="", dictionary_refs=(), notes="",
                    planned_test_case_id="TC-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        missing_dictionary = self._validate(
            "## TC-001\n**Трассировка:** OBL-001; ATOM-001; SRC-001; "
            "OBL-002; ATOM-002; SRC-002; BSR 202\n"
        )
        self.assertFalse(missing_dictionary.passed)

        complete = self._validate(
            "## TC-001\n**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001; "
            "OBL-002; ATOM-002; SRC-002; BSR 202\n"
        )
        self.assertTrue(complete.passed)

    def test_exhaustive_dictionary_claim_requires_exact_leaf_projection(self) -> None:
        requirement = PreparedDictionaryRequirement(
            dictionary_id="DICT-001",
            coverage_mode="full-hierarchy",
            required_values=(
                PreparedDictionaryValue(
                    ("DICT-001", "DICT-101"),
                    "group",
                    "Группа один",
                ),
                PreparedDictionaryValue(
                    ("DICT-001", "DICT-101"),
                    "leaf",
                    "Значение один",
                ),
                PreparedDictionaryValue(
                    ("DICT-001", "DICT-101"),
                    "leaf",
                    "Значение два",
                ),
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-dictionary-projection",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001", "DICT-001"),
                    atomic_statement="Полный состав справочника отображается.",
                    observable_oracle="Отображаются все значения.",
                    test_intent="Сверить полный состав.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=("DICT-001",),
                    notes="",
                    planned_test_case_id="TC-DICT-001",
                    dictionary_requirements=(requirement,),
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())
        symbolic_only = (
            "## TC-DICT-001\n"
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001\n\n"
            "### Тестовые данные\n\n- Все значения DICT-001.\n\n"
            "### Шаги\n\n1. Проверить.\n"
        )

        missing = self._validate(symbolic_only)

        self.assertFalse(missing.passed)
        finding = next(
            item
            for item in missing.findings
            if item["id"] == "dictionary-projection-missing"
        )
        self.assertEqual("DICT-001", finding["dictionary_id"])
        self.assertEqual(3, len(finding["missing_values"]))

        projected, report = materialize_draft_dictionary_projections(
            symbolic_only,
            obligations,
        )
        complete = self._validate(projected)

        self.assertTrue(complete.passed)
        self.assertEqual(1, report["materialized_count"])
        self.assertIn("Значение два", projected)

        mutated = projected.replace(
            "- Значение `DICT-001 > DICT-101`: `Значение два`\n",
            "",
        )
        incomplete = self._validate(mutated)
        incomplete_finding = next(
            item
            for item in incomplete.findings
            if item["id"] == "dictionary-projection-incomplete"
        )
        self.assertEqual(
            ["Значение два"],
            [item["value"] for item in incomplete_finding["missing_values"]],
        )

    def test_reference_only_dictionary_does_not_require_value_projection(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-reference-only",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001", "DICT-001"),
                    atomic_statement="Выбор Другое открывает комментарий.",
                    observable_oracle="Комментарий отображается.",
                    test_intent="Выбрать Другое.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=("DICT-001",),
                    notes="",
                    planned_test_case_id="TC-DICT-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            "## TC-DICT-001\n"
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001\n"
        )

        self.assertTrue(result.passed)

    def test_multiple_exhaustive_dictionaries_are_validated_independently(self) -> None:
        requirements = (
            PreparedDictionaryRequirement(
                dictionary_id="DICT-001",
                coverage_mode="all-leaf-values",
                required_values=(
                    PreparedDictionaryValue(("DICT-001",), "leaf", "Значение один"),
                ),
            ),
            PreparedDictionaryRequirement(
                dictionary_id="DICT-002",
                coverage_mode="all-leaf-values",
                required_values=(
                    PreparedDictionaryValue(("DICT-002",), "leaf", "Значение два"),
                ),
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-two-dictionaries",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001",),
                    atomic_statement="Оба справочника отображаются полностью.",
                    observable_oracle="Доступны все значения обоих справочников.",
                    test_intent="Просмотреть оба поля.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=("DICT-001", "DICT-002"),
                    notes="",
                    planned_test_case_id="TC-DICT-001",
                    dictionary_requirements=requirements,
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())
        symbolic = (
            "## TC-DICT-001\n"
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001; DICT-002\n\n"
            "### Тестовые данные\n\n- Оба справочника.\n\n"
            "### Шаги\n\n1. Просмотреть оба поля.\n"
        )

        projected, _ = materialize_draft_dictionary_projections(symbolic, obligations)
        result = self._validate(projected)

        self.assertTrue(result.passed, result.findings)

    def test_stale_exhaustive_projection_is_removed_after_reference_only_recompile(self) -> None:
        exhaustive = PreparedDictionaryRequirement(
            dictionary_id="DICT-001",
            coverage_mode="all-leaf-values",
            required_values=(
                PreparedDictionaryValue(("DICT-001",), "leaf", "Первое"),
            ),
        )
        base = dict(
            obligation_id="OBL-001",
            atom_id="ATOM-001",
            source_refs=("SRC-001", "DICT-001"),
            atomic_statement="Поле отображается.",
            observable_oracle="Поле видно.",
            test_intent="Просмотреть поле.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=("DICT-001",),
            notes="",
            planned_test_case_id="TC-DICT-001",
        )
        old = PreparedObligationSet.create(
            package_id="pkg-old",
            obligations=(
                PreparedObligation(
                    **base,
                    dictionary_requirements=(exhaustive,),
                ),
            ),
            coverage_gaps=(),
        )
        symbolic = (
            "## TC-DICT-001\n"
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001\n\n"
            "### Тестовые данные\n\n- DICT-001.\n\n"
            "### Шаги\n\n1. Просмотреть поле.\n"
        )
        projected, _ = materialize_draft_dictionary_projections(symbolic, old)
        current = PreparedObligationSet.create(
            package_id="pkg-current",
            obligations=(
                PreparedObligation(
                    **base,
                    dictionary_requirements=(
                        PreparedDictionaryRequirement(
                            dictionary_id="DICT-001",
                            coverage_mode="reference-only",
                        ),
                    ),
                ),
            ),
            coverage_gaps=(),
        )

        cleaned, report = materialize_draft_dictionary_projections(
            projected, current
        )

        self.assertNotIn("runner-dictionary-projection:start", cleaned)
        self.assertEqual(0, report["materialized_count"])

    def test_reference_only_exact_fixture_blocks_generic_v4_replay(self) -> None:
        requirement = PreparedDictionaryRequirement(
            dictionary_id="DICT-001",
            coverage_mode="reference-only",
            fixture_values=(
                PreparedDictionaryValue(
                    ("DICT-001", "DICT-101"),
                    "group",
                    "Признаки алкоголика",
                ),
                PreparedDictionaryValue(
                    ("DICT-001", "DICT-101"),
                    "leaf",
                    "Запах алкоголя / перегара / сильный запах духов, перебивающий перегар",
                ),
                PreparedDictionaryValue(
                    ("DICT-001", "DICT-101"),
                    "leaf",
                    "Отечность, нездоровый цвет лица, синяки под глазами",
                ),
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-reference-fixture",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-013",
                    atom_id="ATOM-013",
                    source_refs=("SRC-003.P08", "DICT-001"),
                    atomic_statement="Можно одновременно выбрать несколько значений.",
                    observable_oracle="Оба checkbox остаются выбранными.",
                    test_intent="Последовательно выбрать два точных значения.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=("DICT-001",),
                    notes="",
                    planned_test_case_id="TC-VAMB-012",
                    dictionary_requirements=(requirement,),
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())
        generic_v4_replay = (
            "## TC-VAMB-012\n"
            "**Трассировка:** OBL-013; ATOM-013; SRC-003.P08; DICT-001\n\n"
            "### Тестовые данные\n\n- Два обычных значения из DICT-101.\n\n"
            "### Шаги\n\n1. Последовательно выбрать два обычных значения.\n\n"
            "### Итоговый ожидаемый результат\n\nОба checkbox остаются выбранными.\n"
        )

        rejected = self._validate(generic_v4_replay)

        self.assertFalse(rejected.passed)
        self.assertIn(
            "reference-fixture-projection-missing",
            {item["id"] for item in rejected.findings},
        )

        projected, report = materialize_draft_reference_fixtures(
            generic_v4_replay,
            obligations,
        )
        accepted = self._validate(projected)

        self.assertTrue(accepted.passed)
        self.assertEqual(1, report["materialized_count"])
        self.assertIn("Признаки алкоголика", projected)
        self.assertIn("Запах алкоголя / перегара", projected)

        incomplete_text = projected.replace(
            "- Значение fixture `DICT-001 > DICT-101`: "
            "`Отечность, нездоровый цвет лица, синяки под глазами`\n",
            "",
        )
        incomplete = self._validate(incomplete_text)
        self.assertIn(
            "reference-fixture-projection-incomplete",
            {item["id"] for item in incomplete.findings},
        )

    def test_dadata_reference_fixture_projection_uses_runtime_roles(self) -> None:
        requirement = PreparedDictionaryRequirement(
            dictionary_id="DICT-DADATA-ADDR-POS",
            coverage_mode="reference-only",
            fixture_values=(
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "FX-DADATA-ADDR-001"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "самара авроры 7 12"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "г Самара, ул Авроры, д 7, кв 12"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "443017"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "Самарская обл"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "Самара"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "Авроры"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "7"),
                PreparedDictionaryValue(("DICT-DADATA-ADDR-POS",), "leaf", "12"),
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-dadata-reference-fixture",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-003",
                    atom_id="ATOM-003",
                    source_refs=("SRC-003", "DICT-DADATA-ADDR-POS"),
                    atomic_statement="DaData возвращает точное предложение адреса.",
                    observable_oracle="Выбрано точное предложение адреса.",
                    test_intent="Выбрать точное предложение адреса.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=("DICT-DADATA-ADDR-POS",),
                    notes="",
                    planned_test_case_id="TC-003",
                    dictionary_requirements=(requirement,),
                ),
            ),
            coverage_gaps=(),
        )
        draft = (
            "## TC-003\n"
            "**Трассировка:** OBL-003; ATOM-003; SRC-003; DICT-DADATA-ADDR-POS\n\n"
            "### Тестовые данные\n\n- Адрес DaData.\n\n"
            "### Шаги\n\n1. Выбрать предложение DaData.\n"
        )

        projected, _ = materialize_draft_reference_fixtures(draft, obligations)

        self.assertIn("- Fixture DaData: `FX-DADATA-ADDR-001`.", projected)
        self.assertIn("- Запрос: `самара авроры 7 12`.", projected)
        self.assertIn(
            "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`.",
            projected,
        )
        self.assertIn("- Регион: `Самарская обл`.", projected)
        self.assertNotIn("Значение fixture", projected)

    def test_fms_reference_fixture_projection_is_accepted_as_complete(self) -> None:
        values = (
            "FX-DADATA-FMS-POS-001",
            "772-053",
            "ОВД ЗЮЗИНО Г. МОСКВЫ",
            "772-053",
            "ОВД ЗЮЗИНО Г. МОСКВЫ",
            "77",
            "2",
            "5575bdb90c1e51bddb27d168ca354813079620580e994208395e45de5ab7f90e",
        )
        requirement = PreparedDictionaryRequirement(
            dictionary_id="DICT-DADATA-FMS-POS-001",
            coverage_mode="reference-only",
            fixture_values=tuple(
                PreparedDictionaryValue(
                    (
                        "DICT-DADATA-FMS-POS-001",
                        f"DICT-DADATA-FMS-POS-001-VALUE-{index:02d}",
                    ),
                    "leaf",
                    value,
                )
                for index, value in enumerate(values, start=1)
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-dadata-fms-reference-fixture",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-030",
                    atom_id="ATOM-047",
                    source_refs=("SRC-019", "BSR 94"),
                    atomic_statement="DaData возвращает подразделение ФМС.",
                    observable_oracle="Точное подразделение отображается.",
                    test_intent="Ввести код и выбрать точное подразделение.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=("DICT-DADATA-FMS-POS-001",),
                    notes="",
                    planned_test_case_id="TC-030",
                    dictionary_requirements=(requirement,),
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())
        draft = (
            "## TC-030\n"
            "**Трассировка:** OBL-030; ATOM-047; SRC-019; BSR 94; "
            "DICT-DADATA-FMS-POS-001\n\n"
            "### Тестовые данные\n\n- DaData fixture.\n\n"
            "### Шаги\n\n1. Ввести код и выбрать точное подразделение.\n"
        )

        projected, _ = materialize_draft_reference_fixtures(draft, obligations)
        accepted = self._validate(projected)

        self.assertTrue(accepted.passed, accepted.findings)
        self.assertIn("- Код подразделения: `772-053`.", projected)
        self.assertIn("- Код региона: `77`.", projected)
        self.assertIn("- Тип подразделения: `2`.", projected)
        self.assertNotIn("- SHA-256 ответа fixture:", projected)

    def test_writer_dictionary_ownership_rejects_exhaustive_value_enumeration(self) -> None:
        requirement = PreparedDictionaryRequirement(
            dictionary_id="DICT-001",
            coverage_mode="all-leaf-values",
            required_values=(
                PreparedDictionaryValue(("DICT-001",), "leaf", "Первое значение"),
                PreparedDictionaryValue(("DICT-001",), "leaf", "Второе значение"),
                PreparedDictionaryValue(("DICT-001",), "leaf", "Третье значение"),
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-writer-dictionary-boundary",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001", "DICT-001"),
                    atomic_statement="Все значения доступны.",
                    observable_oracle="Отображается полный набор.",
                    test_intent="Сверить полный набор.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=("DICT-001",),
                    notes="",
                    planned_test_case_id="TC-DICT-001",
                    dictionary_requirements=(requirement,),
                ),
            ),
            coverage_gaps=(),
        )
        duplicated = (
            "## TC-DICT-001\n"
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001\n\n"
            "- Первое значение; Второе значение; Третье значение.\n"
        )
        symbolic = duplicated.replace(
            "Первое значение; Второе значение; Третье значение",
            "полный набор DICT-001",
        )

        rejected = validate_writer_dictionary_ownership(duplicated, obligations)
        accepted = validate_writer_dictionary_ownership(symbolic, obligations)

        self.assertFalse(rejected["passed"])
        self.assertEqual(1, rejected["finding_count"])
        self.assertEqual(
            "writer-owned-exhaustive-dictionary-values",
            rejected["findings"][0]["id"],
        )
        self.assertTrue(accepted["passed"])

        projected, _ = materialize_draft_dictionary_projections(symbolic, obligations)
        untrusted_marker = validate_writer_dictionary_ownership(projected, obligations)
        runner_owned = validate_writer_dictionary_ownership(
            projected,
            obligations,
            trusted_runner_projected_test_case_ids=("TC-DICT-001",),
        )
        self.assertFalse(untrusted_marker["passed"])
        self.assertTrue(runner_owned["passed"])

        projected_with_writer_duplication = projected.replace(
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001\n",
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; DICT-001\n"
            "- Первое значение; Второе значение.\n",
        )
        writer_owned = validate_writer_dictionary_ownership(
            projected_with_writer_duplication,
            obligations,
            trusted_runner_projected_test_case_ids=("TC-DICT-001",),
        )
        self.assertFalse(writer_owned["passed"])


class StrictPreparedObligationGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.draft = self.root / "draft.md"
        self.obligations_path = self.root / "atomic-obligations.json"
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-runtime",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01", "BSR 16"),
                    atomic_statement=(
                        "При вводе некорректного VIN и выполнении поиска "
                        "система показывает ошибку."
                    ),
                    observable_oracle="Сообщение об ошибке VIN отображается.",
                    test_intent="Ввести некорректный VIN и выполнить поиск.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

    def _case(
        self,
        *,
        tc_id: str = "TC-AMS-001",
        traceability: str = "OBL-001; ATOM-001; SRC-001.P01; BSR 16",
        preconditions: str = "- Открыта основная форма.",
        steps: str = (
            "1. Ввести некорректный VIN `123`.\n"
            "2. Нажать «Найти» и выполнить поиск."
        ),
        expected_result: str = (
            "После поиска система показывает "
            "сообщение об ошибке для VIN."
        ),
    ) -> str:
        return (
            f"## {tc_id}\n\n"
            f"**Трассировка:** {traceability}\n\n"
            "### Предусловия\n\n"
            f"{preconditions}\n\n"
            "### Тестовые данные\n\n"
            "- Некорректный VIN: `123`.\n\n"
            f"### Шаги\n\n{steps}\n\n"
            "### Итоговый ожидаемый результат\n\n"
            f"{expected_result}\n"
        )

    def _validate(self, text: str):
        self.draft.write_text(text, encoding="utf-8")
        return validate_draft_obligation_coverage(
            draft_path=self.draft,
            obligations_path=self.obligations_path,
            strict_runtime_contract=True,
        )

    def test_traceability_only_fails_even_if_fenced_code_has_valid_sections(self) -> None:
        result = self._validate(
            "## TC-AMS-001\n"
            "**Трассировка:** OBL-001; ATOM-001; SRC-001.P01; BSR 16\n\n"
            "```markdown\n"
            "### Предусловия\nНе требуется.\n"
            "### Тестовые данные\nНе требуется.\n"
            "### Шаги\n1. Ввести VIN.\n"
            "### Итоговый ожидаемый результат\n"
            "Ошибка отображается.\n```\n"
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "missing-runtime-section",
            {finding["id"] for finding in result.findings},
        )
        self.assertNotIn("OBL-001", result.covered_obligations)

    def test_obligation_in_wrong_planned_tc_fails(self) -> None:
        result = self._validate(self._case(tc_id="TC-AMS-999"))

        self.assertFalse(result.passed)
        self.assertIn(
            "planned-test-case-mismatch",
            {finding["id"] for finding in result.findings},
        )

    def test_wrong_executable_action_fails(self) -> None:
        result = self._validate(
            self._case(steps="1. Очистить поле VIN.")
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "action-contract-mismatch",
            {finding["id"] for finding in result.findings},
        )

    def test_negated_rejection_is_valid_acceptance_oracle(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-acceptance",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-041",
                    atom_id="ATOM-041",
                    source_refs=("SRC-041",),
                    atomic_statement="Поле принимает допустимое значение.",
                    observable_oracle="Значение принимается системой как допустимое.",
                    test_intent="Ввести допустимое значение в поле.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-041",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                tc_id="TC-041",
                traceability="OBL-041; ATOM-041; SRC-041",
                steps="1. Ввести допустимое значение в поле.",
                expected_result=(
                    "Введённое значение не отклонено системой как недопустимое."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_clear_or_do_not_fill_satisfies_leave_field_empty_action(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-empty-field",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-081",
                    atom_id="ATOM-081",
                    source_refs=("SRC-081",),
                    atomic_statement="Поле Регион может быть пустым.",
                    observable_oracle="Поле Регион остаётся пустым.",
                    test_intent="Оставить поле «Регион» пустым.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-081",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        for steps in (
            "1. Очистить поле «Регион».",
            "1. Продолжить, не заполняя поле «Регион».",
        ):
            with self.subTest(steps=steps):
                result = self._validate(
                    self._case(
                        tc_id="TC-081",
                        traceability="OBL-081; ATOM-081; SRC-081",
                        steps=steps,
                        expected_result="Поле «Регион» остаётся пустым.",
                    )
                )
                self.assertTrue(result.passed, result.findings)

    def test_disappears_and_is_absent_are_equivalent_oracles(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-disappearance",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-053",
                    atom_id="ATOM-070",
                    source_refs=("SRC-030", "BSR 137"),
                    atomic_statement="Подсказка исчезает после активации флажка.",
                    observable_oracle=(
                        "Подсказка «Укажите номер квартиры» исчезает с поля "
                        "«Адрес регистрации»."
                    ),
                    test_intent="Активировать флажок частного дома.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-053",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                tc_id="TC-053",
                traceability="OBL-053; ATOM-070; SRC-030; BSR 137",
                steps="1. Активировать флажок частного дома.",
                expected_result=(
                    "Подсказка «Укажите номер квартиры» отсутствует на поле "
                    "«Адрес регистрации»."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_not_activated_preserves_default_control_state(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-default-control",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-054",
                    atom_id="ATOM-071",
                    source_refs=("SRC-030",),
                    atomic_statement="Необязательный флажок можно не активировать.",
                    observable_oracle=(
                        "Необязательный логический элемент остаётся в заданном "
                        "значении по умолчанию «Нет» без обязательной активации."
                    ),
                    test_intent=(
                        "Field/block: Флажок частного дома; "
                        "Action contract: Не изменять значение по умолчанию «Нет» "
                        "флажка частного дома."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-054",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                tc_id="TC-054",
                traceability="OBL-054; ATOM-071; SRC-030",
                steps="1. Не активируя флажок, выполнить действие продолжения.",
                expected_result=(
                    "Значение «Нет» допускается без обязательной активации "
                    "флажка; зафиксировано отсутствие его активации."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_view_action_matches_view_intent(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-view",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Поле отображается.",
                    observable_oracle="Поле доступно для просмотра.",
                    test_intent="Просмотреть поле «Тип должности».",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Просмотреть поле «Тип должности».",
                expected_result="Поле доступно для просмотра.",
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_source_first_action_contract_isolated_from_conditions_and_fixture(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-source-first-action",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="В анкете отображается блок адресов.",
                    observable_oracle="На странице виден заголовок адресов.",
                    test_intent=(
                        "Field/block: Блок адресов; "
                        "Condition contract: Открыта анкета клиента.; "
                        "Action contract: Перейти к адресной части анкеты клиента.; "
                        "Design fixture: Открыть адресную часть и проверить заголовок.; "
                        "Check type: positive; Test data: Анкета клиента"
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Перейти к адресной части анкеты клиента.",
                expected_result="На странице виден заголовок адресов.",
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_action_contract_can_be_split_between_preconditions_and_steps(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-source-first-split-action",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Пустой обязательный регион не принимается.",
                    observable_oracle="Пустой регион не подтверждается как валидный.",
                    test_intent=(
                        "Field/block: Регион; "
                        "Action contract: Оставить регион пустым и попытаться "
                        "подтвердить адрес.; Check type: negative"
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                preconditions="1. Оставить поле «Регион» пустым.",
                steps="1. Попытаться подтвердить адрес.",
                expected_result="Пустой регион не подтверждается как валидный.",
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_switch_action_matches_set_values_in_two_modes(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-source-first-switch",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Поле видно в автоматическом и ручном режимах.",
                    observable_oracle="Поле видно при значениях «Нет» и «Да».",
                    test_intent=(
                        "Field/block: Адрес регистрации; "
                        "Condition contract: Переключатель доступен.; "
                        "Action contract: Открыть блок в автоматическом режиме.; "
                        "Переключить адрес регистрации в ручной режим.; "
                        "Design fixture: Проверить оба режима."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps=(
                    "1. Установить переключатель в значение «Нет».\n"
                    "2. Установить переключатель в значение «Да»."
                ),
                expected_result="Поле видно при значениях «Нет» и «Да».",
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_quoted_no_control_value_does_not_invert_positive_oracle(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-source-first-quoted-no",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement=(
                        "Поле видно как при автоматическом, так и при ручном вводе."
                    ),
                    observable_oracle=(
                        "Поле отображается при автоматическом вводе; то же поле "
                        "отображается при ручном вводе."
                    ),
                    test_intent=(
                        "Field/block: Адрес регистрации; "
                        "Condition contract: Переключатель доступен.; "
                        "Action contract: Проверить поле при автоматическом вводе.; "
                        "Переключить адрес регистрации в ручной режим."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps=(
                    "1. Проверить поле при значении переключателя «Нет».\n"
                    "2. Переключить адрес регистрации в ручной режим."
                ),
                expected_result=(
                    "Поле отображается при автоматическом вводе со значением "
                    "«Нет» и продолжает отображаться при ручном вводе со "
                    "значением «Да»."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_without_change_retention_phrase_does_not_invert_positive_oracle(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-source-first-retention-polarity",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Поле сохраняет выбранный регион.",
                    observable_oracle=(
                        "Значение региона предложено и сохранено в поле после выбора."
                    ),
                    test_intent="Найти и выбрать регион.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Найти и выбрать регион.",
                expected_result=(
                    "Значение региона предложено интерфейсом и сохранено в поле "
                    "после выбора без изменения."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_acceptance_oracle_cannot_be_reduced_to_display_only(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-source-first-acceptance",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Поле принимает шестизначный индекс.",
                    observable_oracle=(
                        "Поле принимает и отображает значение «660017»."
                    ),
                    test_intent="Ввести индекс «660017».",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        reduced = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Ввести индекс «660017».",
                expected_result="Поле отображает значение «660017».",
            )
        )
        preserved = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Ввести индекс «660017».",
                expected_result=(
                    "Поле принимает и отображает значение «660017»."
                ),
            )
        )

        self.assertFalse(reduced.passed)
        self.assertIn(
            "observable-oracle-contract-mismatch",
            {finding["id"] for finding in reduced.findings},
        )
        self.assertTrue(preserved.passed, preserved.findings)

    def test_apply_address_action_matches_entering_that_address(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-source-first-apply",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Признак не появляется для адреса с квартирой.",
                    observable_oracle="Флажок частного дома не отображается.",
                    test_intent=(
                        "Field/block: Частный дом; "
                        "Condition contract: Адрес не совпадает.; "
                        "Action contract: Применить несовпадающий фактический адрес с квартирой «2».; "
                        "Design fixture: Квартира указана."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Ввести несовпадающий фактический адрес с квартирой «2».",
                expected_result="Флажок частного дома не отображается.",
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_opposite_and_wrong_oracles_fail(self) -> None:
        examples = (
            (
                "Сообщение об ошибке VIN не отображается.",
                "oracle-polarity-mismatch",
            ),
            (
                "Поле VIN очищается.",
                "observable-oracle-contract-mismatch",
            ),
        )
        for expected_result, finding_id in examples:
            with self.subTest(expected_result=expected_result):
                result = self._validate(
                    self._case(expected_result=expected_result)
                )
                self.assertFalse(result.passed)
                self.assertIn(
                    finding_id,
                    {finding["id"] for finding in result.findings},
                )

    def test_comparative_bound_does_not_invert_positive_oracle(self) -> None:
        result = self._validate(
            self._case(
                expected_result=(
                    "При длине VIN не менее 3 символов сообщение об ошибке "
                    "для VIN отображается."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_selected_value_display_matches_field_retention_oracle(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-selection-retention",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Поле предлагает и сохраняет выбранное значение.",
                    observable_oracle=(
                        "То же значение предложено продуктом и сохранено в поле «Регион»."
                    ),
                    test_intent="Найти и выбрать значение в поле «Регион».",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Найти и выбрать значение в поле «Регион».",
                expected_result=(
                    "Значение предложено продуктом и после выбора отображается "
                    "в поле «Регион» с тем же текстом."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_selected_value_display_does_not_prove_reopen_persistence(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-selection-persistence",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01",),
                    atomic_statement="Значение сохраняется после повторного открытия.",
                    observable_oracle=(
                        "После повторного открытия то же значение сохранено в поле «Регион»."
                    ),
                    test_intent="Выбрать значение, сохранить и повторно открыть карточку.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                traceability="OBL-001; ATOM-001; SRC-001.P01",
                steps="1. Выбрать значение в поле «Регион».",
                expected_result=(
                    "После выбора значение отображается в поле «Регион» с тем же текстом."
                ),
            )
        )

        self.assertIn(
            "observable-oracle-contract-mismatch",
            {finding["id"] for finding in result.findings},
        )

    def test_lifecycle_intent_can_explicitly_combine_fill_and_reset(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-runtime",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01", "BSR 16"),
                    atomic_statement="После удаления заполненного блока новый блок пуст.",
                    observable_oracle="Поля нового блока пусты.",
                    test_intent=(
                        "Заполнить поля, удалить блок кнопкой «Корзина», затем "
                        "повторно добавить блок и проверить пустое состояние."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                steps=(
                    "1. Заполнить поля блока.\n"
                    "2. Нажать «Корзина» и удалить блок.\n"
                    "3. Повторно добавить блок и проверить его поля."
                ),
                expected_result="Поля нового блока пусты.",
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_matching_positive_oracle_allows_supplementary_negative_clause(self) -> None:
        obligations = PreparedObligationSet.create(
            package_id="pkg-strict-runtime",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-001.P01", "BSR 16"),
                    atomic_statement="Выбранный блок удаляется кнопкой «Корзина».",
                    observable_oracle="Выбранный блок-повторитель удалён.",
                    test_intent="Нажать кнопку-пиктограмму «Корзина» выбранного блока.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-AMS-001",
                ),
            ),
            coverage_gaps=(),
        )
        write_json_atomic(self.obligations_path, obligations.to_dict())

        result = self._validate(
            self._case(
                steps="1. Нажать кнопку-пиктограмму «Корзина» выбранного блока.",
                expected_result=(
                    "Выбранный блок-повторитель удалён; соответствующий доход "
                    "больше не отображается."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_oracle_in_steps_does_not_compensate_empty_final_expected(self) -> None:
        result = self._validate(
            self._case(
                steps=(
                    "1. Ввести некорректный VIN и выполнить поиск.\n"
                    "2. Убедиться, что сообщение об ошибке VIN отображается."
                ),
                expected_result="",
            )
        )

        finding_ids = {finding["id"] for finding in result.findings}
        self.assertFalse(result.passed)
        self.assertIn("empty-runtime-section", finding_ids)
        self.assertIn("observable-oracle-contract-mismatch", finding_ids)

    def test_only_preconditions_and_test_data_allow_not_applicable_placeholders(self) -> None:
        allowed = self._case().replace(
            "- Открыта основная форма.",
            "Не требуется.",
        ).replace(
            "- Некорректный VIN: `123`.",
            "Не применимо.",
        )
        allowed_result = self._validate(allowed)
        forbidden_result = self._validate(
            self._case(expected_result="Не применимо.")
        )

        self.assertTrue(allowed_result.passed, allowed_result.findings)
        self.assertIn(
            "forbidden-runtime-placeholder",
            {finding["id"] for finding in forbidden_result.findings},
        )

    def test_steps_require_a_numbered_executable_action(self) -> None:
        result = self._validate(
            self._case(
                steps="Ввести некорректный VIN и выполнить поиск."
            )
        )

        self.assertIn(
            "runtime-step-missing-numbered-action",
            {finding["id"] for finding in result.findings},
        )

    def test_extra_source_reference_fails_exact_traceability(self) -> None:
        result = self._validate(
            self._case(
                traceability=(
                    "OBL-001; ATOM-001; SRC-001.P01; BSR 16; SRC-UNRELATED"
                )
            )
        )

        finding = next(
            finding
            for finding in result.findings
            if finding["id"] == "strict-traceability-contract-mismatch"
        )
        self.assertEqual(["SRC-UNRELATED"], finding["unexpected_references"])

    def test_duplicate_obligation_across_test_cases_fails(self) -> None:
        duplicate = self._case(tc_id="TC-AMS-002")
        result = self._validate(self._case() + "\n" + duplicate)

        duplicate_findings = [
            finding
            for finding in result.findings
            if finding["id"] == "duplicate-obligation-coverage"
        ]
        self.assertFalse(result.passed)
        self.assertEqual(2, len(duplicate_findings))
        self.assertNotIn("OBL-001", result.covered_obligations)

    def test_full_runtime_contract_passes_without_verbatim_oracle(self) -> None:
        result = self._validate(self._case())

        self.assertTrue(result.passed, result.findings)
        self.assertEqual(("OBL-001",), result.covered_obligations)

    def test_crlf_and_unicode_whitespace_are_tolerated(self) -> None:
        text = self._case()
        text = text.replace("## TC-AMS-001", "##\u00a0TC-AMS-001")
        text = text.replace("### Тестовые данные", "###\u202fТестовые\u00a0данные")
        text = text.replace("**Трассировка:** ", "**Трассировка:**\u00a0")
        text = text.replace("1. Ввести", "1.\u202fВвести")
        text = text.replace("\n", "\r\n")

        result = self._validate(text)

        self.assertTrue(result.passed, result.findings)


if __name__ == "__main__":
    unittest.main()
