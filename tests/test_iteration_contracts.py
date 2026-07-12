from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class IterationContractTests(unittest.TestCase):
    def test_writer_revision_mode_accepts_findings_and_matrix(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`revision_from_findings`", writer)
        self.assertIn("structured findings artifact", writer)
        self.assertIn("traceability matrix artifact", writer)
        self.assertIn("Обрабатывай findings с учетом `review_mode`", writer)

    def test_writer_revision_mode_describes_mode_specific_handoff(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`traceability` — закрывай gaps покрытия", writer)
        self.assertIn("`structure` — выравнивай шаблон, порядок, группировку и сквозную нумерацию", writer)
        self.assertIn("`test-design` — добавляй или корректируй", writer)

    def test_writer_and_iteration_describe_pdf_structure_cross_check(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        iteration = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("PDF-версия основного ФТ для сверки структуры", writer)
        self.assertIn("сверяй по ней структуру разделов", writer)
        self.assertIn("source-parity-check.md", iteration)
        self.assertIn("when DOCX and PDF are both available", iteration)

    def test_iteration_uses_session_based_reviewer_sequence(self) -> None:
        iteration = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        lifecycle = (ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md").read_text(encoding="utf-8")

        self.assertIn("session-based writer/reviewer cycle", iteration)
        self.assertIn("scripts/review_cycle_backend_dispatcher.py --backend auto", iteration)
        self.assertIn("SDK runner is an explicit v1 fallback", iteration)
        self.assertIn("structure_preflight", lifecycle)
        self.assertIn("semantic_traceability_test_design", lifecycle)
        self.assertIn("structure_format_final", lifecycle)
        self.assertIn("semantic_regression", lifecycle)

    def test_iteration_describes_sign_off_and_round_cap_gates(self) -> None:
        iteration = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        lifecycle = (ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md").read_text(encoding="utf-8")

        self.assertIn("Do not start final format review before semantic review passes", iteration)
        self.assertIn("Do not start a third semantic review round", iteration)
        self.assertIn("Do not route `round-cap-reached` or `blocked-input`", iteration)
        self.assertIn("no findings with `severity = error` or `severity = warning` remain", lifecycle)
        self.assertIn("traceability matrix has no `coverage_status = gap`", lifecycle)

    def test_iteration_preserves_writer_domain_rules_by_reference(self) -> None:
        iteration = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        manifest = (ROOT_DIR / "references" / "agent" / "instruction-loading-manifest.md").read_text(encoding="utf-8")

        self.assertIn("ft-test-case-writer", manifest)
        self.assertIn("writer_table_artifacts", manifest)
        self.assertIn("writer_revision_artifacts", manifest)
        self.assertIn("reviewer_semantic_core", manifest)
        self.assertIn("quality-feedback-loop.md", iteration)

    def test_review_cycle_requires_xlsx_traceability_duplicates(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer_output = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")

        self.assertIn("`.xlsx`-дубль traceability matrix", writer)
        self.assertIn("round-N-traceability-matrix.xlsx", reviewer_output)
        self.assertIn("work/review-cycles/<scope-slug>/outputs/", reviewer_output)
        self.assertIn("те же строки, колонки и значения", reviewer_output)


if __name__ == "__main__":
    unittest.main()
