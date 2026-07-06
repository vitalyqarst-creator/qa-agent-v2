from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    NewTcDraftReviewReport,
    build_new_tc_draft_review,
    load_new_tc_draft_review,
    write_new_tc_draft_proposal,
    write_new_tc_draft_review,
)
from tests.test_new_tc_draft_proposals import build_proposal, setup_bundle


class NewTcDraftReviewTests(unittest.TestCase):
    def test_reviews_valid_draft_only_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))

            report = build_review(root, bundle_path, proposal_path)

            self.assertEqual("approved-with-warnings", report.review_status)
            self.assertEqual(1, report.drafts_total)
            self.assertFalse(report.safe_for_controlled_create_apply)

    def test_blocks_when_proposal_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, _proposal_path = setup_review_fixture(Path(temp_dir))

            report = build_review(root, bundle_path, root / "work" / "missing.json")

            self.assertEqual("blocked", report.review_status)
            self.assertTrue(any("draft proposal is missing" in reason for reason in report.blocking_reasons))

    def test_rejects_if_canonical_write_allowed_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))
            mutate_proposal(proposal_path, canonical_write_allowed=True)

            report = build_review(root, bundle_path, proposal_path)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("canonical_write_allowed_false", report.failed_checks)
            self.assertFalse(report.canonical_write_allowed)

    def test_rejects_if_proposed_tc_ids_are_not_draft_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))
            mutate_first_draft(proposal_path, proposed_tc_id="TC-REAL-001")

            report = build_review(root, bundle_path, proposal_path)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("proposed_tc_ids_are_draft_only", report.failed_checks)

    def test_flags_drafts_missing_req_uid_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))
            mutate_first_draft(proposal_path, source_requirement_uids=[], traceability_refs=[], traceability_line="")

            report = build_review(root, bundle_path, proposal_path)
            draft_review = report.draft_reviews[0]

            self.assertEqual("failed", draft_review.traceability_status)
            self.assertIn("drafts_map_to_candidate_requirements", report.failed_checks)

    def test_flags_generic_placeholder_steps_as_needs_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))

            report = build_review(root, bundle_path, proposal_path)
            draft_review = report.draft_reviews[0]

            self.assertEqual("needs_revision", draft_review.review_status)
            self.assertTrue(any("generic placeholders" in issue for issue in draft_review.issues))
            self.assertFalse(report.safe_for_controlled_create_apply)

    def test_flags_unknown_req_uid_not_present_in_context_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))
            mutate_first_draft(proposal_path, source_requirement_uids=["REQ-UNKNOWN-1"], traceability_refs=["REQ-UNKNOWN-1"], traceability_line="REQ-UNKNOWN-1")

            report = build_review(root, bundle_path, proposal_path)
            draft_review = report.draft_reviews[0]

            self.assertEqual("failed", draft_review.traceability_status)
            self.assertTrue(any("unknown req_uid" in issue for issue in draft_review.issues))

    def test_flags_high_duplicate_risk_as_reject_or_defer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir), duplicate_risk="high")

            report = build_review(root, bundle_path, proposal_path)

            self.assertEqual(0, len(report.draft_reviews))
            self.assertEqual(1, report.deferred_drafts_count)
            self.assertFalse(report.safe_for_controlled_create_apply)

    def test_flags_missing_candidate_requirement_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))
            mutate_proposal(proposal_path, draft_test_cases=[])

            report = build_review(root, bundle_path, proposal_path)

            self.assertIn("all_candidate_requirements_accounted_for", report.failed_checks)

    def test_safe_for_controlled_create_apply_false_when_drafts_need_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))

            report = build_review(root, bundle_path, proposal_path)

            self.assertGreater(report.drafts_requiring_revision_count, 0)
            self.assertFalse(report.safe_for_controlled_create_apply)

    def test_writes_json_and_markdown_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))
            report = build_review(root, bundle_path, proposal_path)

            json_path, markdown_path = write_new_tc_draft_review(report, root / "work")
            loaded = load_new_tc_draft_review(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, NewTcDraftReviewReport)
            self.assertEqual("new-tc-draft-review-WPKG-000001.json", json_path.name)
            self.assertIn("New TC Draft Review", markdown)
            self.assertIn("Review-only artifact", markdown)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path = setup_review_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            report = build_review(root, bundle_path, proposal_path)
            write_new_tc_draft_review(report, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_review_fixture(root: Path, *, duplicate_risk: str = "medium") -> tuple[Path, Path, Path]:
    root, bundle_path = setup_bundle(root, duplicate_risk=duplicate_risk)
    proposal = build_proposal(root, bundle_path)
    proposal_path, _proposal_md_path = write_new_tc_draft_proposal(proposal, root / "work")
    return root, bundle_path, proposal_path


def build_review(root: Path, bundle_path: Path, proposal_path: Path):
    work = root / "work"
    return build_new_tc_draft_review(
        package_id="WPKG-000001",
        draft_proposal_path=proposal_path,
        context_bundle_path=bundle_path,
        test_cases_dir=root / "fts" / "Demo" / "test-cases",
        manual_update_packages_path=work / "manual-update-packages.old-to-new.json",
        writer_package_tasks_path=work / "writer-package-tasks.old-to-new.json",
        update_plan_path=work / "test-case-update-plan.old-to-new.json",
        impact_report_path=work / "impact-report.old-to-new.json",
        requirements_diff_path=work / "requirements-diff.old-to-new.json",
        old_registry_path=work / "requirements.old.jsonl",
        new_registry_path=work / "requirements.new.jsonl",
        workspace_root=root,
    )


def mutate_proposal(proposal_path: Path, **updates) -> None:
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload.update(updates)
    proposal_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mutate_first_draft(proposal_path: Path, **updates) -> None:
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["draft_test_cases"][0].update(updates)
    proposal_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    unittest.main()
