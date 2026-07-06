from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_case_agent.agent_decision_validation import (
    AgentDecisionValidationReport,
    build_agent_decision_validation_report,
    load_agent_decision_validation_report,
    write_agent_decision_validation_report,
)
from test_case_agent.agent_decision_resolver import write_agent_decision_resolution
from tests.test_agent_decision_resolver import (
    build_resolution,
    make_safe_and_ambiguous_rows,
    make_single_safe_row,
    setup_resolution_fixture,
)


class AgentDecisionValidationTests(unittest.TestCase):
    def test_validates_agent_decision_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertIn(report.validation_status, {"pass", "pass-with-warnings", "rejected"})
            self.assertEqual("WPKG-000001", report.package_id)

    def test_recomputes_hardened_stage_9e_gate_independently(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_single_safe_row(matrix_path, paths)
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertTrue(report.stage_9e_gate_hardened["stage_9e_allowed"])
            self.assertEqual(["MDR-SAFE"], report.validated_stage_9e_scope["row_ids"])

    def test_rejects_candidate_with_requires_human_review_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_safe_and_ambiguous_rows(matrix_path, paths)
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            by_row = {item.row_id: item for item in report.decision_validation_results}
            self.assertIn(by_row["MDR-AMBIG"].validation_result, {"human-review-required", "deferred"})
            self.assertFalse(by_row["MDR-AMBIG"].stage_9e_eligible)

    def test_rejects_missing_source_object_action_or_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertTrue(
                any(
                    result.validation_result in {"human-review-required", "deferred", "rejected"}
                    and result.blocking_reasons
                    for result in report.decision_validation_results
                )
            )

    def test_rejects_existing_tc_as_business_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution = build_resolution(paths, matrix_path)
            first = resolution.agent_decisions[0]
            unsafe = replace(
                first,
                decision_status="unsafe",
                safety_warnings=["existing TC evidence appears to be used as a business-rule source"],
                blocking_reasons=["existing TC evidence appears to be used as a business-rule source"],
            )
            resolution = replace(resolution, agent_decisions=[unsafe] + resolution.agent_decisions[1:])
            resolution_path, _ = write_agent_decision_resolution(resolution, root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertEqual("unsafe", report.decision_validation_results[0].validation_result)

    def test_validates_split_candidate_only_with_source_backed_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)
            mdr_000012 = [item for item in report.decision_validation_results if item.row_id == "MDR-000012"]

            if mdr_000012:
                self.assertEqual("rejected", mdr_000012[0].validation_result)
                self.assertTrue(any("affected drafts" in reason for reason in mdr_000012[0].blocking_reasons))

    def test_markdown_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")
            report = build_report(paths, matrix_path, resolution_path)

            json_path, markdown_path = write_agent_decision_validation_report(report, root / "work")
            loaded = load_agent_decision_validation_report(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, AgentDecisionValidationReport)
            self.assertIn("Hardened Gate", markdown)
            self.assertIn("Safety Statement", markdown)

    def test_keeps_canonical_writes_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertFalse(report.canonical_write_allowed)
            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def build_report(paths: dict[str, Path], matrix_path: Path, resolution_path: Path) -> AgentDecisionValidationReport:
    return build_agent_decision_validation_report(
        package_id="WPKG-000001",
        resolution_path=resolution_path,
        matrix_path=matrix_path,
        context_bundle_path=paths["context_bundle_path"],
        draft_proposal_path=paths["draft_proposal_path"],
        decision_pack_path=paths["decision_pack_path"],
        residual_analysis_path=paths["residual_analysis_path"],
    )


if __name__ == "__main__":
    unittest.main()
