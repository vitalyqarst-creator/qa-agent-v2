from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class TraceabilityReferenceContractTests(unittest.TestCase):
    def test_traceability_matrix_requires_stable_atom_id(self) -> None:
        matrix = (ROOT_DIR / "references" / "qa" / "traceability-matrix-format.md").read_text(encoding="utf-8")
        self.assertIn("`atom_id`", matrix)
        self.assertIn("основным ключом связи между traceability matrix, review findings и writer response", matrix)
        self.assertIn("Findings по traceability должны ссылаться на строку матрицы через `traceability_ref = ATOM-*`", matrix)
        self.assertIn("| atom_id | req_id | source_path | atomic_statement", matrix)

    def test_review_findings_require_traceability_ref_for_traceability_mode(self) -> None:
        findings = (ROOT_DIR / "references" / "qa" / "review-findings-format.md").read_text(encoding="utf-8")
        self.assertIn("`traceability_ref`, если `review_mode = traceability`", findings)
        self.assertIn("`traceability_ref`: `ATOM-*`", findings)
        self.assertIn("Reviewer не должен возвращать `traceability` finding без `traceability_ref`", findings)
        self.assertIn("Writer response на `traceability` finding должен сохранять связь с исходным `traceability_ref`", findings)

    def test_writer_reviewer_and_iteration_use_traceability_ref(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        iteration = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("traceability_ref = ATOM-*", writer)
        self.assertIn("traceability_ref = ATOM-*", reviewer)
        self.assertIn("affected_traceability_refs", iteration)
        self.assertIn("закрытие traceability gaps проверяется по `traceability_ref` / `atom_id`", iteration)

    def test_reviewer_output_format_checks_traceability_ref_in_second_review(self) -> None:
        reviewer_output = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")
        self.assertIn("`traceability_ref` должен ссылаться на `atom_id`", reviewer_output)
        self.assertIn("Для каждого закрытого `traceability` finding reviewer должен проверить тот же `traceability_ref`", reviewer_output)


if __name__ == "__main__":
    unittest.main()
