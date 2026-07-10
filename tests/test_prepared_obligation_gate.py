from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.obligation_gate import validate_draft_obligation_coverage
from test_case_agent.review_cycle.prepared_package import (
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
            "## TC-001\n**Трассировка:** ATOM-001\n\n"
            "## TC-002\n**Traceability:** ATOM-002\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual(("ATOM-001", "ATOM-002"), result.covered_obligations)

    def test_reports_missing_unknown_and_non_testable_atoms(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, ATOM-003, ATOM-404\n"
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
            "**Трассировка:** ATOM-001, ATOM-002\n\n"
            "## Coverage gaps\n"
            "**Трассировка:** ATOM-003\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual("prepared-package-obligation-gate-v2", result.as_dict()["validator"])

    def test_bulleted_traceability_inside_tc_is_supported(self) -> None:
        result = self._validate(
            "## TC-001\n- **Трассировка:** ATOM-001\n\n"
            "## TC-002\n* **Traceability:** ATOM-002\n"
        )
        self.assertTrue(result.passed)

    def test_nested_headings_stay_inside_tc_and_parent_heading_ends_it(self) -> None:
        result = self._validate(
            "### TC-001\n"
            "#### Предусловия\nText.\n"
            "#### Traceability\n**Трассировка:** ATOM-001, ATOM-002\n\n"
            "## Неисполняемые границы покрытия\n"
            "**Трассировка:** ATOM-003\n"
        )
        self.assertTrue(result.passed)

    def test_next_tc_ends_previous_even_at_deeper_heading_level(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001\n\n"
            "### TC-002\n**Трассировка:** ATOM-002\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual(2, result.test_case_count)

    def test_headings_and_atoms_inside_fenced_code_are_ignored(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, ATOM-002\n\n"
            "```markdown\n## TC-FAKE\n**Трассировка:** ATOM-003\n```\n"
        )
        self.assertTrue(result.passed)
        self.assertEqual(1, result.test_case_count)

    def test_real_gap_traceability_inside_tc_still_blocks(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, ATOM-002, ATOM-003\n"
        )
        self.assertFalse(result.passed)
        self.assertIn(
            "non-testable-obligation-used-as-test",
            {item["id"] for item in result.findings},
        )

    def test_set_level_unknown_atom_does_not_attach_to_last_tc(self) -> None:
        result = self._validate(
            "## TC-001\n**Трассировка:** ATOM-001, ATOM-002\n\n"
            "## Coverage gaps\n- **Трассировка:** ATOM-404\n"
        )
        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
