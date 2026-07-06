from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    NewTcDraftRevisionPlan,
    build_new_tc_draft_revision_plan,
    load_new_tc_draft_revision_plan,
    write_new_tc_draft_revision_plan,
    write_new_tc_draft_review,
)
from tests.test_new_tc_draft_review import build_review, setup_review_fixture


class NewTcDraftRevisionPlanTests(unittest.TestCase):
    def test_builds_revision_plan_from_review_and_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))

            plan = build_plan(root, bundle_path, proposal_path, review_path)

            self.assertEqual("pass-with-warnings", plan.plan_status)
            self.assertEqual(1, plan.revision_summary["revision_items_total"])
            self.assertEqual(1, plan.revision_summary["revise_count"])
            self.assertFalse(plan.ready_for_revised_draft_proposal)
            self.assertFalse(plan.canonical_write_allowed)
            self.assertTrue(plan.manual_review_required)

    def test_blocks_when_review_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, _review_path = setup_revision_fixture(Path(temp_dir))

            plan = build_plan(root, bundle_path, proposal_path, root / "work" / "missing-review.json")

            self.assertEqual("blocked", plan.plan_status)
            self.assertTrue(any("draft review is missing" in reason for reason in plan.blocking_reasons))

    def test_blocks_package_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))
            mutate_json(review_path, package_id="WPKG-OTHER")

            plan = build_plan(root, bundle_path, proposal_path, review_path)

            self.assertEqual("blocked", plan.plan_status)
            self.assertTrue(any("package_id mismatch" in reason for reason in plan.blocking_reasons))

    def test_one_revision_item_per_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))

            plan = build_plan(root, bundle_path, proposal_path, review_path)
            proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

            self.assertEqual(len(proposal["draft_test_cases"]), len(plan.revision_items))

    def test_required_fixes_are_copied_from_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))

            plan = build_plan(root, bundle_path, proposal_path, review_path)

            self.assertTrue(plan.revision_items[0].required_fixes)
            self.assertTrue(any("generic" in fix.lower() for fix in plan.revision_items[0].required_fixes))

    def test_rejected_drafts_are_not_marked_approved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))
            mutate_first_draft_review(review_path, review_status="reject", required_fixes=["Replace rejected draft."])

            plan = build_plan(root, bundle_path, proposal_path, review_path)

            self.assertEqual("replace", plan.revision_items[0].target_revision_status)
            self.assertEqual(1, plan.revision_summary["replace_count"])
            self.assertTrue(plan.deferred_or_rejected_actions)

    def test_medium_duplicate_risk_requires_differentiation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))

            plan = build_plan(root, bundle_path, proposal_path, review_path)

            self.assertEqual(1, plan.revision_summary["duplicate_risk_actions_count"])
            self.assertEqual("differentiate", plan.duplicate_risk_actions[0].action)
            self.assertFalse(plan.ready_for_revised_draft_proposal)

    def test_source_grounding_actions_include_source_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))

            plan = build_plan(root, bundle_path, proposal_path, review_path)

            self.assertEqual(1, plan.revision_summary["source_grounding_actions_count"])
            self.assertTrue(plan.source_grounding_actions[0].usable_facts)

    def test_writes_json_and_markdown_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))
            plan = build_plan(root, bundle_path, proposal_path, review_path)

            json_path, markdown_path = write_new_tc_draft_revision_plan(plan, root / "work")
            loaded = load_new_tc_draft_revision_plan(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, NewTcDraftRevisionPlan)
            self.assertEqual("new-tc-draft-revision-plan-WPKG-000001.json", json_path.name)
            self.assertIn("New TC Draft Revision Plan", markdown)
            self.assertIn("Planning-only artifact", markdown)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path = setup_revision_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            plan = build_plan(root, bundle_path, proposal_path, review_path)
            write_new_tc_draft_revision_plan(plan, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_revision_fixture(root: Path) -> tuple[Path, Path, Path, Path]:
    root, bundle_path, proposal_path = setup_review_fixture(root)
    review = build_review(root, bundle_path, proposal_path)
    review_path, _review_md_path = write_new_tc_draft_review(review, root / "work")
    return root, bundle_path, proposal_path, review_path


def build_plan(root: Path, bundle_path: Path, proposal_path: Path, review_path: Path) -> NewTcDraftRevisionPlan:
    work = root / "work"
    return build_new_tc_draft_revision_plan(
        package_id="WPKG-000001",
        draft_proposal_path=proposal_path,
        draft_review_path=review_path,
        context_bundle_path=bundle_path,
        test_cases_dir=root / "fts" / "Demo" / "test-cases",
        requirements_diff_path=work / "requirements-diff.old-to-new.json",
        impact_report_path=work / "impact-report.old-to-new.json",
        update_plan_path=work / "test-case-update-plan.old-to-new.json",
        old_registry_path=work / "requirements.old.jsonl",
        new_registry_path=work / "requirements.new.jsonl",
    )


def mutate_json(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mutate_first_draft_review(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["draft_reviews"][0].update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    unittest.main()
