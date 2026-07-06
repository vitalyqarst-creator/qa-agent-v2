from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.agent_decision_validation import (
    build_agent_decision_validation_report,
    write_agent_decision_validation_report,
)
from test_case_agent.agent_decision_resolver import write_agent_decision_resolution
from test_case_agent.agent_driven_create_new_goal_report import (
    AgentDrivenCreateNewGoalReport,
    build_agent_driven_create_new_goal_report,
    load_agent_driven_create_new_goal_report,
    write_agent_driven_create_new_goal_report,
)
from tests.test_agent_decision_resolver import build_resolution, setup_resolution_fixture


class AgentDrivenCreateNewGoalReportTests(unittest.TestCase):
    def test_lists_executed_and_skipped_stages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")
            validation = build_agent_decision_validation_report(
                package_id="WPKG-000001",
                resolution_path=resolution_path,
                matrix_path=matrix_path,
                context_bundle_path=paths["context_bundle_path"],
                draft_proposal_path=paths["draft_proposal_path"],
                decision_pack_path=paths["decision_pack_path"],
                residual_analysis_path=paths["residual_analysis_path"],
            )
            write_agent_decision_validation_report(validation, root / "work")

            report = build_agent_driven_create_new_goal_report(
                package_id="WPKG-000001",
                work_dir=root / "work",
                git_status_test_cases=[],
                tests_run=[{"command": "python -m unittest tests.test_agent_decision_validation", "result": "OK"}],
            )

            self.assertTrue(any(item["stage"] == "Stage 9D.9" for item in report.executed_stages))
            self.assertTrue(any(item["stage"] == "Stage 9E" for item in report.skipped_stages))
            self.assertTrue(report.safety_confirmations["canonical_test_cases_clean"])

    def test_write_and_load_goal_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")
            validation = build_agent_decision_validation_report(
                package_id="WPKG-000001",
                resolution_path=resolution_path,
                matrix_path=matrix_path,
                context_bundle_path=paths["context_bundle_path"],
                draft_proposal_path=paths["draft_proposal_path"],
                decision_pack_path=paths["decision_pack_path"],
                residual_analysis_path=paths["residual_analysis_path"],
            )
            write_agent_decision_validation_report(validation, root / "work")
            report = build_agent_driven_create_new_goal_report(
                package_id="WPKG-000001",
                work_dir=root / "work",
                git_status_test_cases=[],
            )

            json_path, md_path = write_agent_driven_create_new_goal_report(report, root / "work")
            loaded = load_agent_driven_create_new_goal_report(json_path)
            markdown = md_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, AgentDrivenCreateNewGoalReport)
            self.assertIn("Skipped Stages", markdown)


if __name__ == "__main__":
    unittest.main()
