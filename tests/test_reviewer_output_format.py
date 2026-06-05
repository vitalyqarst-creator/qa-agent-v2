from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class ReviewerOutputFormatTests(unittest.TestCase):
    def test_reviewer_output_reference_defines_canonical_artifacts(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")

        self.assertIn("round-N-findings.md", content)
        self.assertIn("round-N-traceability-matrix.md", content)
        self.assertIn("round-N-traceability-matrix.xlsx", content)
        self.assertIn("prompt.reviewer-to-writer.round-N.md", content)
        self.assertIn("prompt.reviewer-to-ui-prep.md", content)
        self.assertIn("stage_status: round-cap-reached", content)

    def test_reviewer_skill_links_to_reviewer_output_reference(self) -> None:
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        handoff = (ROOT_DIR / "references" / "agent" / "stage-handoff-model.md").read_text(encoding="utf-8")
        contracts = (ROOT_DIR / "references" / "agent" / "instruction-contract-index.md").read_text(encoding="utf-8")

        self.assertIn("reviewer-output-format.md", reviewer)
        self.assertIn("reviewer-output-format.md", handoff)
        self.assertIn("Reviewer output structure", contracts)

    def test_reviewer_output_reference_defines_sign_off_gate(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")

        self.assertIn("нет findings с `severity = error`", content)
        self.assertIn("нет findings с `severity = warning`", content)
        self.assertIn("traceability matrix не содержит `coverage_status = gap`", content)
        self.assertIn("Нельзя маршрутизировать `round-cap-reached` напрямую в `ft-ui-automation-prep`", content)

    def test_reviewer_output_forbids_not_signed_off_workflow_status(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        workflow = (ROOT_DIR / "references" / "agent" / "workflow-state-format.md").read_text(encoding="utf-8")

        for source in (content, reviewer, workflow):
            self.assertIn("not-signed-off", source)
            self.assertIn("ready-for-writer-revision", source)
            self.assertIn("round-cap-reached", source)
            self.assertIn("blocked-input", source)


    def test_reviewer_output_requires_sign_off_self_check(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Reviewer Sign-off Self-check", content)
        for token in (
            "`Reviewer Sign-off Self-check`",
            "**traceability_checked:**",
            "**structure_checked:**",
            "**test_case_grouping_checked:**",
            "**test_case_numbering_checked:**",
            "**test_design_checked:**",
            "**applicability_dimensions_checked:**",
            "**blocking_findings_absent:**",
            "**traceability_gaps_absent:**",
            "**known_unclear_items:**",
            "**sign_off_rationale:**",
        ):
            self.assertIn(token, content)

        self.assertIn("Reviewer Sign-off Self-check", reviewer)
        self.assertIn("sign_off_rationale", content)
        self.assertIn("Test-design applicability matrix", content)
        self.assertIn("applicable = yes", content)

    def test_reviewer_output_requires_round_cap_residual_risk(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")

        self.assertIn("## Final Residual Risk", content)
        for token in (
            "remaining_blocking_findings",
            "remaining_traceability_gaps",
            "remaining_coverage_gaps",
            "remaining_unclear_items",
            "decision_rationale",
            "next_action",
            "latest_artifacts",
            "final_findings",
            "final_traceability_matrix",
            "scope_coverage_gaps",
        ):
            self.assertIn(token, content)

    def test_reviewer_output_provides_terminal_output_copy_fill_snippets(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "reviewer-output-format.md").read_text(encoding="utf-8")

        for token in (
            "## Terminal Output Copy/Fill Snippets",
            "### Signed-off final output",
            "### Round-cap final output",
            "Applicability dimensions unresolved",
            "Review-cycle received `signed-off`",
            "Review-cycle stopped at `round-cap-reached`",
            "work/review-cycles/<scope-slug>/outputs/round-N-findings.md",
            "work/review-cycles/<scope-slug>/versions/signed-off",
        ):
            self.assertIn(token, content)


if __name__ == "__main__":
    unittest.main()
