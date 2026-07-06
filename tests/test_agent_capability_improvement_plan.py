from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    AgentCapabilityImprovementPlan,
    build_agent_capability_improvement_plan,
    load_agent_capability_improvement_plan,
    write_agent_capability_improvement_plan,
    write_new_tc_revision_decision_pack,
)
from tests.test_new_tc_revision_decision_pack import build_pack, setup_decision_pack_fixture


class AgentCapabilityImprovementPlanTests(unittest.TestCase):
    def test_builds_improvement_plan_from_decision_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))

            plan = build_plan(root, decision_pack_path)

            self.assertEqual("pass-with-warnings", plan.plan_status)
            self.assertEqual("WPKG-000001", plan.package_id)
            self.assertGreaterEqual(len(plan.improvement_items), 6)

    def test_blocks_when_decision_pack_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "work").mkdir()

            plan = build_plan(root, root / "work" / "missing.json")

            self.assertEqual("blocked", plan.plan_status)
            self.assertTrue(any("decision pack is missing" in reason for reason in plan.blocking_reasons))

    def test_blocks_on_package_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))
            mutate_json(decision_pack_path, package_id="WPKG-OTHER")

            plan = build_plan(root, decision_pack_path)

            self.assertEqual("blocked", plan.plan_status)
            self.assertTrue(any("package_id mismatch" in reason for reason in plan.blocking_reasons))

    def test_produces_capability_finding_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))

            plan = build_plan(root, decision_pack_path)

            self.assertEqual(6, len(plan.capability_findings_summary))

    def test_produces_improvement_items_for_gap_and_partial_areas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))

            plan = build_plan(root, decision_pack_path)
            areas = {item.capability_area for item in plan.improvement_items}

            self.assertTrue(
                {
                    "source_grounding",
                    "draft_quality",
                    "manual_decision_flow",
                    "duplicate_risk_handling",
                    "replacement_strategy",
                }.issubset(areas)
            )

    def test_produces_safety_preservation_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))

            plan = build_plan(root, decision_pack_path)

            self.assertEqual(1, len(plan.safety_preservation_plan))
            self.assertIn("canonical_write_allowed=false", " ".join(plan.safety_preservation_plan[0].must_preserve))

    def test_prioritizes_gap_areas_higher_than_partial_areas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))

            plan = build_plan(root, decision_pack_path)
            by_area = {item.capability_area: item.priority for item in plan.improvement_items}

            self.assertEqual("P1", by_area["source_grounding"])
            self.assertEqual("P1", by_area["draft_quality"])
            self.assertEqual("P2", by_area["duplicate_risk_handling"])

    def test_does_not_mark_canonical_create_apply_as_next_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))

            plan = build_plan(root, decision_pack_path)

            self.assertNotIn("apply", plan.expected_next_stage.casefold())
            self.assertNotIn("controlled create", plan.expected_next_stage.casefold())
            self.assertIn("Implement Source Grounding", plan.expected_next_stage)

    def test_acceptance_criteria_are_measurable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))

            plan = build_plan(root, decision_pack_path)
            text = "\n".join(plan.acceptance_criteria)

            self.assertIn("Generic placeholder steps count is 0", text)
            self.assertIn("needs_manual_decision_count decreases from 16", text)

    def test_writes_json_and_markdown_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))
            plan = build_plan(root, decision_pack_path)

            json_path, markdown_path = write_agent_capability_improvement_plan(plan, root / "work")
            loaded = load_agent_capability_improvement_plan(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, AgentCapabilityImprovementPlan)
            self.assertEqual("agent-capability-improvement-plan-WPKG-000001.json", json_path.name)
            self.assertIn("Agent Capability Improvement Plan", markdown)
            self.assertIn("Safety Preservation Plan", markdown)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, decision_pack_path = setup_improvement_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            plan = build_plan(root, decision_pack_path)
            write_agent_capability_improvement_plan(plan, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_improvement_fixture(root: Path) -> tuple[Path, Path]:
    root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(root)
    pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
    decision_pack_path, _markdown_path = write_new_tc_revision_decision_pack(pack, root / "work")
    set_benchmark_capability_findings(decision_pack_path)
    return root, decision_pack_path


def build_plan(root: Path, decision_pack_path: Path) -> AgentCapabilityImprovementPlan:
    return build_agent_capability_improvement_plan(
        package_id="WPKG-000001",
        benchmark_name="Demo benchmark",
        decision_pack_path=decision_pack_path,
        draft_revision_plan_path=root / "work" / "new-tc-draft-revision-plan-WPKG-000001.json",
        draft_review_path=root / "work" / "new-tc-draft-review-WPKG-000001.json",
        draft_proposal_path=root / "work" / "new-tc-draft-proposal-WPKG-000001.json",
        context_bundle_path=root / "work" / "create-new-tc-context-bundle-WPKG-000001.json",
        test_cases_dir=root / "fts" / "Demo" / "test-cases",
    )


def mutate_json(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def set_benchmark_capability_findings(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    statuses = {
        "duplicate_risk_handling": "partial",
        "source_grounding": "gap",
        "draft_quality": "gap",
        "replacement_strategy": "partial",
        "manual_decision_flow": "gap",
        "safety_gate": "works",
    }
    for finding in payload["agent_capability_findings"]:
        area = finding["capability_area"]
        finding["status"] = statuses[area]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    unittest.main()
