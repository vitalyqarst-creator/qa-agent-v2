from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    NewTcRevisionDecisionPack,
    build_new_tc_revision_decision_pack,
    load_new_tc_revision_decision_pack,
    write_new_tc_draft_revision_plan,
    write_new_tc_revision_decision_pack,
)
from tests.test_new_tc_draft_revision_plan import build_plan, setup_revision_fixture


class NewTcRevisionDecisionPackTests(unittest.TestCase):
    def test_builds_decision_pack_from_revision_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            self.assertEqual("pass-with-warnings", pack.decision_pack_status)
            self.assertEqual("WPKG-000001", pack.package_id)
            self.assertEqual(1, len(pack.draft_decisions))

    def test_blocks_when_revision_plan_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, _plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, root / "work" / "missing-plan.json")

            self.assertEqual("blocked", pack.decision_pack_status)
            self.assertTrue(any("revision plan is missing" in reason for reason in pack.blocking_reasons))

    def test_blocks_on_package_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            mutate_json(plan_path, package_id="WPKG-OTHER")

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            self.assertEqual("blocked", pack.decision_pack_status)
            self.assertTrue(any("package_id mismatch" in reason for reason in pack.blocking_reasons))

    def test_produces_one_draft_decision_per_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

            self.assertEqual(len(proposal["draft_test_cases"]), len(pack.draft_decisions))

    def test_clusters_duplicate_risk_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

            self.assertGreater(len(pack.duplicate_risk_clusters), 0)
            self.assertLessEqual(len(pack.duplicate_risk_clusters), len(plan["duplicate_risk_actions"]))

    def test_produces_source_grounding_resolutions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            self.assertEqual(1, len(pack.source_grounding_resolutions))
            self.assertTrue(pack.source_grounding_resolutions[0].usable_source_facts)

    def test_produces_replacement_strategies_for_rejected_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            mutate_first_revision_item(plan_path, target_revision_status="replace")

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            self.assertEqual(1, len(pack.replacement_strategies))

    def test_keeps_safety_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            self.assertFalse(pack.canonical_write_allowed)
            self.assertTrue(pack.manual_review_required)

    def test_does_not_mark_ready_when_duplicate_risk_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            self.assertFalse(pack.revised_draft_readiness.ready_for_revised_draft_proposal)
            self.assertGreater(pack.revised_draft_readiness.unresolved_duplicate_risk_count, 0)

    def test_does_not_mark_ready_when_source_grounding_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            mutate_first_candidate(bundle_path, expected_behavior=None)

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            self.assertFalse(pack.revised_draft_readiness.ready_for_revised_draft_proposal)
            self.assertGreater(pack.revised_draft_readiness.unresolved_source_grounding_count, 0)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            write_new_tc_revision_decision_pack(pack, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))

    def test_writes_json_and_markdown_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            json_path, markdown_path = write_new_tc_revision_decision_pack(pack, root / "work")
            loaded = load_new_tc_revision_decision_pack(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, NewTcRevisionDecisionPack)
            self.assertEqual("new-tc-revision-decision-pack-WPKG-000001.json", json_path.name)
            self.assertIn("New TC Revision Decision Pack", markdown)
            self.assertIn("Read-only decision-pack artifact", markdown)

    def test_agent_capability_findings_exist_in_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            payload = pack.to_dict()

            self.assertIn("agent_capability_findings", payload)
            self.assertEqual(6, len(payload["agent_capability_findings"]))

    def test_agent_capability_findings_cover_all_areas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            areas = {finding.capability_area for finding in pack.agent_capability_findings}

            self.assertEqual(
                {
                    "duplicate_risk_handling",
                    "source_grounding",
                    "draft_quality",
                    "replacement_strategy",
                    "manual_decision_flow",
                    "safety_gate",
                },
                areas,
            )

    def test_safety_gate_finding_works_when_unresolved_decisions_block_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            safety = finding_by_area(pack, "safety_gate")

            self.assertEqual("works", safety.status)
            self.assertFalse(pack.canonical_write_allowed)
            self.assertTrue(pack.manual_review_required)
            self.assertFalse(pack.revised_draft_readiness.ready_for_revised_draft_proposal)

    def test_duplicate_risk_finding_is_partial_or_works_when_clustered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            duplicate_first_duplicate_risk_action(plan_path)

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            duplicate = finding_by_area(pack, "duplicate_risk_handling")

            self.assertIn(duplicate.status, {"partial", "works"})
            self.assertLessEqual(
                duplicate.evidence["duplicate_risk_clusters_count"],
                duplicate.evidence["raw_duplicate_risk_actions_count"],
            )

    def test_draft_quality_not_works_when_all_drafts_need_manual_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))

            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
            quality = finding_by_area(pack, "draft_quality")

            if pack.revised_draft_readiness.needs_manual_decision_count == len(pack.draft_decisions):
                self.assertNotEqual("works", quality.status)

    def test_round_trip_preserves_agent_capability_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            json_path, _markdown_path = write_new_tc_revision_decision_pack(pack, root / "work")
            loaded = load_new_tc_revision_decision_pack(json_path)

            self.assertEqual(
                [finding.to_dict() for finding in pack.agent_capability_findings],
                [finding.to_dict() for finding in loaded.agent_capability_findings],
            )

    def test_markdown_includes_agent_capability_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(Path(temp_dir))
            pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)

            _json_path, markdown_path = write_new_tc_revision_decision_pack(pack, root / "work")
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIn("Agent Capability Findings", markdown)


def setup_decision_pack_fixture(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    root, bundle_path, proposal_path, review_path = setup_revision_fixture(root)
    plan = build_plan(root, bundle_path, proposal_path, review_path)
    plan_path, _plan_md_path = write_new_tc_draft_revision_plan(plan, root / "work")
    return root, bundle_path, proposal_path, review_path, plan_path


def build_pack(
    root: Path,
    bundle_path: Path,
    proposal_path: Path,
    review_path: Path,
    plan_path: Path,
) -> NewTcRevisionDecisionPack:
    work = root / "work"
    return build_new_tc_revision_decision_pack(
        package_id="WPKG-000001",
        revision_plan_path=plan_path,
        draft_review_path=review_path,
        draft_proposal_path=proposal_path,
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


def mutate_first_revision_item(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["revision_items"][0].update(updates)
    payload["revision_summary"]["replace_count"] = 1
    payload["revision_summary"]["revise_count"] = max(0, int(payload["revision_summary"].get("revise_count", 0)) - 1)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mutate_first_candidate(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["candidate_requirements"][0].update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def duplicate_first_duplicate_risk_action(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    duplicate = dict(payload["duplicate_risk_actions"][0])
    duplicate["similar_tc_id"] = f"{duplicate['similar_tc_id']}-ALT"
    payload["duplicate_risk_actions"].append(duplicate)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def finding_by_area(pack: NewTcRevisionDecisionPack, area: str):
    for finding in pack.agent_capability_findings:
        if finding.capability_area == area:
            return finding
    raise AssertionError(f"finding not found: {area}")


if __name__ == "__main__":
    unittest.main()
