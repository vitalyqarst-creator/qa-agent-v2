from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    NewTcDraftProposal,
    build_new_tc_draft_proposal,
    load_new_tc_draft_proposal,
    write_create_new_tc_context_bundle,
    write_new_tc_draft_proposal,
)
from tests.test_create_new_tc_context_bundle import build_bundle, setup_fixture


class NewTcDraftProposalTests(unittest.TestCase):
    def test_builds_draft_proposal_from_valid_create_new_context_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")

            proposal = build_proposal(root, bundle_path)

            self.assertEqual("pass-with-warnings", proposal.proposal_status)
            self.assertEqual("WPKG-000001", proposal.package_id)
            self.assertEqual("create_new_candidate", proposal.package_type)
            self.assertEqual(1, len(proposal.draft_test_cases))

    def test_blocks_when_bundle_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tc_dir = root / "fts" / "Demo" / "test-cases"
            tc_dir.mkdir(parents=True)

            proposal = build_proposal(root, root / "work" / "missing.json")

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("missing" in reason for reason in proposal.blocking_reasons))

    def test_blocks_when_bundle_has_blocking_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")
            mutate_bundle(bundle_path, blocking_reasons=["upstream bundle blocked"])

            proposal = build_proposal(root, bundle_path)

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("upstream bundle blocked" in reason for reason in proposal.blocking_reasons))

    def test_blocks_when_package_type_is_not_create_new_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")
            mutate_bundle(bundle_path, package_type="manual_review")

            proposal = build_proposal(root, bundle_path)

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("package_type" in reason for reason in proposal.blocking_reasons))

    def test_canonical_write_allowed_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")

            proposal = build_proposal(root, bundle_path)

            self.assertFalse(proposal.canonical_write_allowed)

    def test_manual_review_required_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")

            proposal = build_proposal(root, bundle_path)

            self.assertTrue(proposal.manual_review_required)
            self.assertTrue(proposal.draft_test_cases[0].requires_manual_review)

    def test_does_not_write_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            proposal = build_proposal(root, bundle_path)
            write_new_tc_draft_proposal(proposal, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))

    def test_creates_draft_ids_not_final_authoritative_tc_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")

            draft = build_proposal(root, bundle_path).draft_test_cases[0]

            self.assertTrue(draft.proposed_tc_id.startswith("DRAFT-TC-WPKG-000001-"))
            self.assertFalse(draft.proposed_tc_id.startswith("TC-"))

    def test_defers_high_duplicate_risk_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="high")

            proposal = build_proposal(root, bundle_path)

            self.assertEqual(0, len(proposal.draft_test_cases))
            self.assertEqual(1, len(proposal.deferred_groups))
            self.assertEqual("defer", proposal.duplicate_risk_decisions[0].decision)

    def test_preserves_traceability_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")

            draft = build_proposal(root, bundle_path).draft_test_cases[0]

            self.assertIn("REQ-DEMO-NEW", draft.source_requirement_uids)
            self.assertIn("BSR 10", draft.source_req_ids)
            self.assertIn("PLAN-000001", draft.plan_item_ids)
            self.assertIn("IMP-000001", draft.impact_ids)
            self.assertIn("CHG-000001", draft.change_ids)
            self.assertIn("REQ-DEMO-NEW", draft.traceability_line)

    def test_source_grounding_profile_detects_missing_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")
            mutate_first_candidate(bundle_path, object=None, condition=None, expected_behavior=None)

            draft = build_proposal(root, bundle_path).draft_test_cases[0]
            profile = draft.source_grounding_profiles[0]

            self.assertFalse(profile.has_concrete_object)
            self.assertFalse(profile.has_concrete_condition)
            self.assertFalse(profile.has_user_action)
            self.assertFalse(profile.has_observable_expected_behavior)
            self.assertIn("source-backed user action", profile.missing_facts)

    def test_draft_proposal_does_not_create_executable_draft_when_action_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")
            mutate_first_candidate(bundle_path, condition=None)

            draft = build_proposal(root, bundle_path).draft_test_cases[0]

            self.assertFalse(draft.is_executable_draft)
            self.assertTrue(draft.manual_questions)
            self.assertFalse(draft.contains_generic_placeholders)
            self.assertTrue(any("Resolve manual source-grounding question" in step for step in draft.steps))

    def test_generated_draft_does_not_use_generic_placeholder_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")

            draft = build_proposal(root, bundle_path).draft_test_cases[0]
            text = " ".join([*draft.steps, *draft.expected_results]).casefold()

            self.assertNotIn("open the screen or section identified by the source anchors", text)
            self.assertNotIn("set up the source-backed condition", text)
            self.assertNotIn("perform the user action needed to observe", text)

    def test_json_and_markdown_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")
            proposal = build_proposal(root, bundle_path)

            json_path, markdown_path = write_new_tc_draft_proposal(proposal, root / "work")
            loaded = load_new_tc_draft_proposal(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, NewTcDraftProposal)
            self.assertEqual("new-tc-draft-proposal-WPKG-000001.json", json_path.name)
            self.assertIn("Draft-only artifact", markdown)
            self.assertIn("DRAFT-TC-WPKG-000001-001", markdown)

    def test_existing_canonical_test_case_files_remain_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path = setup_bundle(Path(temp_dir), duplicate_risk="medium")
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            proposal = build_proposal(root, bundle_path)
            write_new_tc_draft_proposal(proposal, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_bundle(root: Path, *, duplicate_risk: str) -> tuple[Path, Path]:
    setup_fixture(root)
    bundle = build_bundle(root)
    bundle_path, _markdown_path = write_create_new_tc_context_bundle(bundle, root / "work")
    mutate_bundle(bundle_path, duplicate_risk=duplicate_risk)
    return root, bundle_path


def mutate_bundle(
    bundle_path: Path,
    *,
    duplicate_risk: str | None = None,
    package_type: str | None = None,
    blocking_reasons: list[str] | None = None,
) -> None:
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    if duplicate_risk is not None:
        for risk in payload["duplicate_risks"]:
            risk["risk"] = duplicate_risk
        for similarity in payload["existing_tc_similarity"]:
            similarity["risk"] = duplicate_risk
    if package_type is not None:
        payload["package_type"] = package_type
    if blocking_reasons is not None:
        payload["blocking_reasons"] = blocking_reasons
        payload["bundle_status"] = "blocked"
    bundle_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def mutate_first_candidate(bundle_path: Path, **updates) -> None:
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    payload["candidate_requirements"][0].update(updates)
    bundle_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_proposal(root: Path, bundle_path: Path):
    work = root / "work"
    return build_new_tc_draft_proposal(
        package_id="WPKG-000001",
        context_bundle_path=bundle_path,
        test_cases_dir=root / "fts" / "Demo" / "test-cases",
        manual_update_packages_path=work / "manual-update-packages.old-to-new.json",
        writer_package_tasks_path=work / "writer-package-tasks.old-to-new.json",
        update_plan_path=work / "test-case-update-plan.old-to-new.json",
        impact_report_path=work / "impact-report.old-to-new.json",
        requirements_diff_path=work / "requirements-diff.old-to-new.json",
        old_registry_path=work / "requirements.old.jsonl",
        new_registry_path=work / "requirements.new.jsonl",
    )


if __name__ == "__main__":
    unittest.main()
