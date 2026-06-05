from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class WriterOutputFormatTests(unittest.TestCase):
    def test_writer_output_reference_defines_canonical_artifacts(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "writer-output-format.md").read_text(encoding="utf-8")

        self.assertIn("fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md", content)
        self.assertIn("fts/<ft-slug>/work/test-design/<section-id>-<scope-slug>/", content)
        self.assertIn("Canonical Artifact Links", content)
        self.assertIn("atomic-requirements-ledger.md", content)
        self.assertIn("writer self-check", content)
        self.assertIn("round-N-writer-response.md", content)
        self.assertIn("stage_status: blocked-input", content)
        self.assertIn("accepted_risks", content)
        self.assertIn("Каждый подтвержденный scope должен иметь внутренние рабочие пакеты", content)
        self.assertIn("package ledger self-check", content)
        self.assertIn("Package Test Design Plan", content)
        self.assertIn("test-design-review.md", content)
        self.assertIn("package design-plan self-check", content)
        self.assertIn("Test Design Review", content)
        self.assertIn("человекочитаемые поля split artifacts", content)
        self.assertIn("русском языке", content)
        self.assertIn("package TC self-check", content)

    def test_writer_skill_links_to_writer_output_reference(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        handoff = (ROOT_DIR / "references" / "agent" / "stage-handoff-model.md").read_text(encoding="utf-8")
        contracts = (ROOT_DIR / "references" / "agent" / "instruction-contract-index.md").read_text(encoding="utf-8")

        self.assertIn("writer-output-format.md", writer)
        self.assertIn("writer-output-format.md", handoff)
        self.assertIn("Writer output structure", contracts)

    def test_test_design_review_format_requires_russian_human_text(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "test-design-review-format.md").read_text(encoding="utf-8")

        self.assertIn("## Язык Артефакта", content)
        self.assertIn("Человекочитаемые поля `evidence` и `required_action` пиши на русском языке", content)
        self.assertIn("Технические имена колонок", content)

    def test_writer_output_requires_test_design_applicability_matrix(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "writer-output-format.md").read_text(encoding="utf-8")
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Test-design Applicability Matrix", content)
        self.assertIn("| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |", content)
        self.assertIn("`applicable = yes`", content)
        self.assertIn("`applicable = unclear`", content)
        self.assertIn("`stage_status: ready-for-review`", content)
        self.assertIn("`stage_status: blocked-input`", content)
        self.assertIn("Test-design applicability matrix", writer)

    def test_writer_output_defines_pairwise_table_and_high_risk_self_check(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "writer-output-format.md").read_text(encoding="utf-8")

        for token in (
            "Risk / Priority Map",
            "| atom_id | coverage_dimension | impact | likelihood | risk_score | risk_level | risk_factors | source_ref | required_priority | linked_test_cases | gap_id | residual_risk_decision | rationale |",
            "`risk_level = high` requires `required_priority = High`",
            "Each high-risk atom must link to at least one `TC-*` with `Priority: High`",
            "Combinatorial Coverage Table",
            "Если `pairwise` применим",
            "factors and values",
            "selected combinations with explicit `coverage_strength = 2-way | 3-way | t-way`",
            "high-risk combinations",
            "excluded combinations",
            "high-risk atoms without `High` priority test case or blocking `coverage gap`",
            "missing or incomplete `Risk / Priority Map`",
            "applicable `pairwise` / `calculation` dimensions without required supporting table or oracle",
        ):
            self.assertIn(token, content)


if __name__ == "__main__":
    unittest.main()
