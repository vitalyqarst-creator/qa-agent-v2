from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts.resolve_instruction_context import load_manifest


ROOT_DIR = Path(__file__).resolve().parents[1]
ROUTING_PATH = ROOT_DIR / "references" / "agent" / "task-start-skill-routing-format.md"
ROUTING_RE = re.compile(
    r"<!--\s*task-start-skill-routing:v1\s*-->\s*```json\s*(.*?)\s*```",
    re.DOTALL,
)


def load_routing() -> dict:
    content = ROUTING_PATH.read_text(encoding="utf-8")
    match = ROUTING_RE.search(content)
    if not match:
        raise AssertionError("task-start-skill-routing:v1 JSON block not found")
    return json.loads(match.group(1))


class TaskStartSkillRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.routing = load_routing()
        self.routes = self.routing["routes"]
        self.route_by_id = {route["id"]: route for route in self.routes}
        self.manifest = load_manifest(ROOT_DIR)

    def test_routing_contract_exists_and_has_required_fields(self) -> None:
        self.assertTrue(ROUTING_PATH.exists())
        self.assertEqual(1, self.routing["version"])
        for field in (
            "task_type",
            "selected_skills",
            "skill_order",
            "selection_reason",
            "instruction_scenarios",
            "verification_gates",
        ):
            self.assertIn(field, self.routing["preflight_required_fields"])

    def test_user_facing_preflight_hides_internal_route_versions(self) -> None:
        content = ROUTING_PATH.read_text(encoding="utf-8")
        self.assertIn("Do not put internal route/profile", content)
        self.assertIn("internal route/profile", content)
        self.assertIn("names or versions", content)

    def test_route_ids_are_unique(self) -> None:
        route_ids = [route["id"] for route in self.routes]
        self.assertEqual(len(route_ids), len(set(route_ids)))

    def test_every_active_skill_is_routable(self) -> None:
        active_skills = {path.name for path in (ROOT_DIR / "skills").iterdir() if path.is_dir()}
        routed_skills = {skill for route in self.routes for skill in route["skill_chain"]}
        self.assertEqual(active_skills, routed_skills)

    def test_every_route_skill_exists(self) -> None:
        active_skills = {path.name for path in (ROOT_DIR / "skills").iterdir() if path.is_dir()}
        for route in self.routes:
            for skill in route["skill_chain"]:
                self.assertIn(skill, active_skills, route["id"])

    def test_every_manifest_scenario_is_routable(self) -> None:
        manifest_scenarios = {item["id"] for item in self.manifest["scenarios"]}
        routed_scenarios = {
            item["scenario"]
            for route in self.routes
            for item in route["instruction_scenarios"]
        }
        self.assertEqual(manifest_scenarios, routed_scenarios)

    def test_every_route_scenario_exists_in_manifest(self) -> None:
        manifest_scenarios = {item["id"] for item in self.manifest["scenarios"]}
        for route in self.routes:
            for item in route["instruction_scenarios"]:
                self.assertIn(item["scenario"], manifest_scenarios, route["id"])

    def test_golden_examples_match_routes(self) -> None:
        self.assertGreaterEqual(len(self.routing["golden_examples"]), 5)
        for example in self.routing["golden_examples"]:
            route = self.route_by_id[example["expected_route_id"]]
            self.assertEqual(example["expected_skill_chain"], route["skill_chain"])
            self.assertEqual(
                example["expected_instruction_scenarios"],
                [item["scenario"] for item in route["instruction_scenarios"]],
            )

    def test_representative_route_expectations(self) -> None:
        self.assertEqual(
            ["ft-practical-route"],
            self.route_by_id["test_cases.practical_v1"]["skill_chain"],
        )
        self.assertEqual(
            ["practical.v1"],
            [
                item["scenario"]
                for item in self.route_by_id["test_cases.practical_v1"][
                    "instruction_scenarios"
                ]
            ],
        )
        self.assertIn(
            "test-design-matrix.md is Russian and is accepted by a distinct top-level reviewer session before TC writing",
            self.route_by_id["test_cases.practical_v1"]["verification_gates"],
        )
        self.assertIn(
            "TC review is performed by a distinct top-level reviewer session",
            self.route_by_id["test_cases.practical_v1"]["verification_gates"],
        )
        self.assertIn(
            "one complete writer revision, one finding-closure check and at most one bounded micro-closure per phase",
            self.route_by_id["test_cases.practical_v1"]["verification_gates"],
        )
        self.assertEqual(
            ["practical.v0_9"],
            [
                item["scenario"]
                for item in self.route_by_id["test_cases.legacy_practical_v0_9"][
                    "instruction_scenarios"
                ]
            ],
        )
        self.assertEqual(
            ["writer.initial_draft.table"],
            [
                item["scenario"]
                for item in self.route_by_id["writer.initial_table"]["instruction_scenarios"]
            ],
        )
        self.assertEqual(
            ["architecture.audit"],
            [
                item["scenario"]
                for item in self.route_by_id["architecture.audit"]["instruction_scenarios"]
            ],
        )
        self.assertIn(
            "direct full review does not create an accepted practical baseline",
            self.route_by_id["reviewer.full_existing_cases"]["verification_gates"],
        )

if __name__ == "__main__":
    unittest.main()
