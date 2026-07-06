from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.new_tc_revised_draft_proposal import write_new_tc_revised_draft_proposal
from test_case_agent.new_tc_revised_draft_review import (
    NewTcRevisedDraftReviewReport,
    build_new_tc_revised_draft_review,
    load_new_tc_revised_draft_review,
    write_new_tc_revised_draft_review,
)
from tests.test_new_tc_revised_draft_proposal import build_proposal, make_fixture, write_json


class NewTcRevisedDraftReviewTests(unittest.TestCase):
    def test_blocks_when_stage_9e_artifact_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))

            report = build_review(fixture, fixture["work_dir"] / "missing.json")

            self.assertEqual("blocked", report.review_status)
            self.assertTrue(report.blocking_reasons)

    def test_approves_or_warns_valid_stage_9e_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            proposal_path = write_proposal_fixture(fixture)

            report = build_review(fixture, proposal_path)

            self.assertIn(report.review_status, {"approved", "approved-with-warnings"})
            self.assertFalse(report.canonical_write_allowed)
            self.assertFalse(report.stage_9g_readiness["authorizes_real_apply"])

    def test_needs_revision_for_generic_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            proposal_path = write_proposal_fixture(fixture)
            mutate_candidate(proposal_path, lambda item: item["steps"].append("TBD"))

            report = build_review(fixture, proposal_path)

            self.assertEqual("needs-revision", report.review_status)
            self.assertTrue(any("no generic placeholders" in issue for review in report.draft_reviews for issue in review.issues))

    def test_needs_revision_for_row_outside_hardened_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            proposal_path = write_proposal_fixture(fixture)
            mutate_candidate(proposal_path, lambda item: item.update({"source_agent_decision_row_id": "MDR-OTHER"}))

            report = build_review(fixture, proposal_path)

            self.assertEqual("needs-revision", report.review_status)
            self.assertTrue(any("candidate row is in hardened validated scope" in issue for review in report.draft_reviews for issue in review.issues))

    def test_needs_revision_for_missing_source_backed_action_or_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            proposal_path = write_proposal_fixture(fixture)
            mutate_candidate(
                proposal_path,
                lambda item: item.update({"candidate_status": "blocked", "steps": [], "expected_results": []}),
            )

            report = build_review(fixture, proposal_path)

            self.assertEqual("needs-revision", report.review_status)
            self.assertTrue(any(review.source_grounding_result == "failed" for review in report.draft_reviews))

    def test_rejects_existing_tc_as_business_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            proposal_path = write_proposal_fixture(fixture)
            mutate_candidate(
                proposal_path,
                lambda item: item.update({"agent_decision_rationale": "existing TC is used as business source"}),
            )

            report = build_review(fixture, proposal_path)

            self.assertEqual("rejected", report.review_status)
            self.assertTrue(any(review.safety_result == "failed" for review in report.draft_reviews))

    def test_write_and_load_and_canonical_file_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            before = fixture["tc_path"].read_text(encoding="utf-8")
            proposal_path = write_proposal_fixture(fixture)
            report = build_review(fixture, proposal_path)

            json_path, md_path = write_new_tc_revised_draft_review(report, fixture["work_dir"])
            loaded = load_new_tc_revised_draft_review(json_path)

            self.assertIsInstance(loaded, NewTcRevisedDraftReviewReport)
            self.assertTrue(md_path.exists())
            self.assertEqual(before, fixture["tc_path"].read_text(encoding="utf-8"))


def write_proposal_fixture(fixture: dict[str, Path]) -> Path:
    proposal = build_proposal(fixture)
    json_path, _ = write_new_tc_revised_draft_proposal(proposal, fixture["work_dir"])
    return json_path


def build_review(fixture: dict[str, Path], proposal_path: Path) -> NewTcRevisedDraftReviewReport:
    return build_new_tc_revised_draft_review(
        package_id="WPKG-000001",
        revised_proposal_path=proposal_path,
        validation_path=fixture["validation_path"],
        source_draft_proposal_path=fixture["draft_proposal_path"],
        test_cases_dir=fixture["test_cases_dir"],
    )


def mutate_candidate(path: Path, mutator) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload["revised_draft_candidates"][0])
    write_json(path, payload)


if __name__ == "__main__":
    unittest.main()
