from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_case_agent import new_tc_create_apply_dry_run as dry_run_module
from test_case_agent.new_tc_create_apply_dry_run import (
    NewTcCreateApplyDryRunReport,
    build_new_tc_create_apply_dry_run,
    load_new_tc_create_apply_dry_run,
    write_new_tc_create_apply_dry_run,
)
from test_case_agent.new_tc_revised_draft_review import write_new_tc_revised_draft_review
from tests.test_new_tc_revised_draft_review import build_review, write_proposal_fixture
from tests.test_new_tc_revised_draft_proposal import make_fixture, write_json


class NewTcCreateApplyDryRunTests(unittest.TestCase):
    def test_builds_dry_run_from_stage_9e_9f_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))

            report = build_dry_run(fixture, proposal_path, review_path)

            self.assertIn(report.dry_run_status, {"pass", "pass-with-warnings"})
            self.assertEqual(1, len(report.dry_run_items))
            self.assertIn(report.dry_run_items[0].dry_run_decision, {"dry_run_allowed", "dry_run_allowed_with_warnings"})

    def test_blocks_if_stage_9f_review_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, _ = make_stage_9g_fixture(Path(temp_dir))

            report = build_dry_run(fixture, proposal_path, fixture["work_dir"] / "missing-review.json")

            self.assertEqual("blocked", report.dry_run_status)
            self.assertTrue(report.blocking_reasons)

    def test_uses_only_approved_or_approved_with_warnings_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))
            mutate_review(review_path, "needs-revision")

            report = build_dry_run(fixture, proposal_path, review_path)

            self.assertEqual("blocked", report.dry_run_status)
            self.assertEqual(0, len(report.dry_run_items))
            self.assertEqual(1, len(report.excluded_candidates))

    def test_does_not_write_canonical_files_backups_or_patches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))
            before_files = sorted(path.relative_to(fixture["test_cases_dir"]) for path in fixture["test_cases_dir"].rglob("*"))
            before_text = fixture["tc_path"].read_text(encoding="utf-8")

            report = build_dry_run(fixture, proposal_path, review_path)

            self.assertFalse(report.canonical_write_allowed)
            self.assertFalse(report.real_apply_authorized)
            self.assertEqual(before_text, fixture["tc_path"].read_text(encoding="utf-8"))
            self.assertEqual(before_files, sorted(path.relative_to(fixture["test_cases_dir"]) for path in fixture["test_cases_dir"].rglob("*")))
            self.assertFalse(list(fixture["work_dir"].glob("*.patch")))
            self.assertFalse(list(fixture["work_dir"].glob("backups")))

    def test_detects_duplicate_proposed_tc_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir), duplicate_candidate=True)

            report = build_dry_run(fixture, proposal_path, review_path)

            self.assertIn("TC-DEMO-NEW-MDR-000012", report.tc_id_plan["duplicate_proposed_tc_ids"])
            self.assertTrue(any(item.dry_run_decision == "blocked" for item in report.dry_run_items))

    def test_detects_existing_tc_id_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))
            mutate_candidate(proposal_path, lambda item: item.update({"proposed_tc_id": "TC-DEMO-001"}))
            mutate_review_tc_id(review_path, "TC-DEMO-001")

            report = build_dry_run(fixture, proposal_path, review_path)

            self.assertEqual(["TC-DEMO-001"], report.tc_id_plan["existing_tc_id_collisions"])
            self.assertEqual("blocked", report.dry_run_items[0].dry_run_decision)

    def test_blocks_aggregate_file_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))
            aggregate_path = fixture["test_cases_dir"] / "14-application-card.md"
            aggregate_path.write_text("assembled_from:\n- split.md\n\n## TC-AGG-001\n", encoding="utf-8")

            with patch.object(dry_run_module, "_target_file_for_candidate", return_value=aggregate_path):
                report = build_dry_run(fixture, proposal_path, review_path)

            self.assertTrue(any("aggregate" in risk for risk in report.dry_run_items[0].collision_risks))
            self.assertEqual("blocked", report.dry_run_items[0].dry_run_decision)

    def test_markdown_preview_is_artifact_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))
            report = build_dry_run(fixture, proposal_path, review_path)

            json_path, md_path = write_new_tc_create_apply_dry_run(report, fixture["work_dir"])
            loaded = load_new_tc_create_apply_dry_run(json_path)

            self.assertIsInstance(loaded, NewTcCreateApplyDryRunReport)
            self.assertTrue(md_path.exists())
            self.assertIn("dry-run preview only", loaded.dry_run_items[0].generated_markdown_preview)
            self.assertFalse((fixture["test_cases_dir"] / "new-tc-tc-demo-new-mdr-000012.md").exists())

    def test_requires_source_decision_and_validation_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))
            mutate_candidate(
                proposal_path,
                lambda item: item.update({"source_agent_decision_row_id": "", "source_validation_result_id": ""}),
            )

            report = build_dry_run(fixture, proposal_path, review_path)

            self.assertEqual("blocked", report.dry_run_items[0].dry_run_decision)
            self.assertTrue(report.dry_run_items[0].safety_warnings)

    def test_stage_9h_readiness_requires_explicit_user_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture, proposal_path, review_path = make_stage_9g_fixture(Path(temp_dir))

            report = build_dry_run(fixture, proposal_path, review_path)

            self.assertFalse(report.stage_9h_readiness["real_apply_authorized"])
            self.assertTrue(report.stage_9h_readiness["requires_explicit_user_approval"])
            self.assertTrue(report.stage_9h_readiness["requires_clean_git_status"])


def make_stage_9g_fixture(root: Path, *, duplicate_candidate: bool = False):
    fixture = make_fixture(root)
    proposal_path = write_proposal_fixture(fixture)
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    proposal["revised_draft_candidates"] = proposal["revised_draft_candidates"][:1]
    proposal["revised_draft_candidates"][0]["proposed_tc_id"] = "TC-DEMO-NEW-MDR-000012"
    if duplicate_candidate:
        duplicate = dict(proposal["revised_draft_candidates"][0])
        duplicate["draft_id"] = "REV-DUPLICATE"
        proposal["revised_draft_candidates"].append(duplicate)
    write_json(proposal_path, proposal)
    review = build_review(fixture, proposal_path)
    review_path, _ = write_new_tc_revised_draft_review(review, fixture["work_dir"])
    return fixture, proposal_path, review_path


def build_dry_run(fixture: dict[str, Path], proposal_path: Path, review_path: Path) -> NewTcCreateApplyDryRunReport:
    return build_new_tc_create_apply_dry_run(
        package_id="WPKG-000001",
        revised_proposal_path=proposal_path,
        revised_review_path=review_path,
        validation_path=fixture["validation_path"],
        resolution_path=fixture["resolution_path"],
        matrix_path=fixture["work_dir"] / "manual-decision-matrix-WPKG-000001.json",
        context_bundle_path=fixture["context_bundle_path"],
        test_cases_dir=fixture["test_cases_dir"],
    )


def mutate_candidate(path: Path, mutator) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload["revised_draft_candidates"][0])
    write_json(path, payload)


def mutate_review(path: Path, result: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["draft_reviews"][0]["review_result"] = result
    write_json(path, payload)


def mutate_review_tc_id(path: Path, proposed_tc_id: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["draft_reviews"][0]["proposed_tc_id"] = proposed_tc_id
    write_json(path, payload)


if __name__ == "__main__":
    unittest.main()
