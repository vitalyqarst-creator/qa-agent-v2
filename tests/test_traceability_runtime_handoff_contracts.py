from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class TraceabilityRuntimeHandoffContractTests(unittest.TestCase):
    def test_workflow_state_defines_final_traceability_aliases(self) -> None:
        state = (ROOT_DIR / "references" / "agent" / "workflow-state-format.md").read_text(encoding="utf-8")
        self.assertIn("canonical aliases", state)
        self.assertIn("`final_findings`", state)
        self.assertIn("`final_traceability_matrix`", state)
        self.assertIn("`final_traceability_matrix_xlsx`", state)
        self.assertIn("`final_writer_response`", state)
        self.assertIn("--final-alias-policy strict", state)
        self.assertIn("remaining `gap` / `unclear` refs через `traceability_ref` / `atom_id`", state)
        self.assertIn("Reviewer-loop final state snippets", state)
        self.assertIn("signed-off -> UI prep", state)
        self.assertIn("round-cap-reached -> stop", state)

    def test_iteration_lifecycle_requires_traceability_closure(self) -> None:
        lifecycle = (ROOT_DIR / "references" / "agent" / "iteration-lifecycle-format.md").read_text(encoding="utf-8")
        self.assertIn("все новые или обновленные строки traceability matrix имеют стабильный `atom_id`", lifecycle)
        self.assertIn("все закрытые traceability findings проверены по `traceability_ref` / `atom_id`", lifecycle)
        self.assertIn("traceability closure", lifecycle)
        self.assertIn("remaining `gap` refs as `ATOM-*` or `coverage_gap:<short-id>`", lifecycle)
        self.assertIn("final aliases", lifecycle)

    def test_stage_handoff_model_uses_traceability_refs_for_new_matrices(self) -> None:
        handoff = (ROOT_DIR / "references" / "agent" / "stage-handoff-model.md").read_text(encoding="utf-8")
        self.assertIn("новых или обновленных traceability matrices", handoff)
        self.assertIn("findings и writer response связываются с matrix через `traceability_ref`", handoff)
        self.assertIn("final aliases в `latest_artifacts`", handoff)

    def test_reviewer_output_documents_legacy_matrix_handling(self) -> None:
        reviewer_output = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")
        self.assertIn("legacy matrix без `atom_id`", reviewer_output)
        self.assertIn("legacy-to-ATOM mapping", reviewer_output)
        self.assertIn("traceability closure по `traceability_ref` / `atom_id`", reviewer_output)

    def test_traceability_matrix_format_has_forward_only_legacy_rule(self) -> None:
        matrix = (ROOT_DIR / "references" / "qa" / "traceability-matrix-format.md").read_text(encoding="utf-8")
        self.assertIn("## Legacy Матрицы", matrix)
        self.assertIn("не нужно механически переписывать", matrix)
        self.assertIn("legacy traceability baseline", matrix)
        self.assertIn("новыми `ATOM-*`", matrix)


if __name__ == "__main__":
    unittest.main()
