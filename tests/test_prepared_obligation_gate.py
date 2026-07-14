from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.obligation_gate import (
    materialize_draft_dictionary_projections,
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


if __name__ == "__main__":
    unittest.main()
