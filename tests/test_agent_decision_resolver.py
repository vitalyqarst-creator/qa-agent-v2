from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    AgentDecisionResolution,
    build_agent_decision_resolution,
    load_agent_decision_resolution,
    write_agent_decision_resolution,
)
from tests.test_manual_decision_matrix import build_matrix, setup_matrix_fixture, write_json


class AgentDecisionResolverTests(unittest.TestCase):
    def test_builds_agent_decision_resolution_from_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertEqual("WPKG-000001", resolution.package_id)
            self.assertIn(resolution.resolution_status, {"pass", "pass-with-warnings"})
            self.assertEqual(len(load_json(matrix_path)["reviewer_decision_rows"]), len(resolution.agent_decisions))

    def test_produces_one_decision_per_matrix_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertEqual(
                len(load_json(matrix_path)["reviewer_decision_rows"]),
                resolution.decision_summary["rows_total"],
            )

    def test_does_not_require_reviewer_answers_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_agent_decision_resolution(
                package_id="WPKG-000001",
                matrix_path=matrix_path,
                decision_pack_path=paths["decision_pack_path"],
                residual_analysis_path=paths["residual_analysis_path"],
                draft_proposal_path=paths["draft_proposal_path"],
                draft_review_path=paths["draft_review_path"],
                draft_revision_plan_path=paths["draft_revision_plan_path"],
                context_bundle_path=paths["context_bundle_path"],
                improvement_plan_path=paths["improvement_plan_path"],
            )

            self.assertNotEqual("blocked", resolution.resolution_status)

    def test_does_not_write_reviewer_answers_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution = build_resolution(paths, matrix_path)

            write_agent_decision_resolution(resolution, root / "work")

            self.assertFalse(list((root / "work").glob("*reviewer*answers*.json")))

    def test_does_not_call_agent_decisions_reviewer_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution = build_resolution(paths, matrix_path)

            json_path, _md_path = write_agent_decision_resolution(resolution, root / "work")
            payload = json_path.read_text(encoding="utf-8")

            self.assertNotIn("reviewer_answers", payload)
            self.assertIn("agent_decisions", payload)

    def test_uses_agent_resolution_decision_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertTrue(all(item.decision_source == "agent_resolution" for item in resolution.agent_decisions))

    def test_keeps_canonical_write_allowed_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertFalse(resolution.canonical_write_allowed)
            self.assertFalse(resolution.stage_9e_gate["canonical_write_allowed"])

    def test_every_decision_keeps_creates_or_edits_canonical_tc_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertTrue(all(not item.creates_or_edits_canonical_tc for item in resolution.agent_decisions))

    def test_does_not_authorize_canonical_tc_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertFalse(resolution.safety_summary["any_decision_creates_or_edits_canonical_tc"])

    def test_marks_low_confidence_rows_as_human_or_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)
            low_confidence = [item for item in resolution.agent_decisions if item.confidence == "low"]

            self.assertTrue(low_confidence)
            self.assertTrue(
                all(item.decision_status in {"needs_human_review", "deferred"} for item in low_confidence)
            )

    def test_missing_action_or_oracle_does_not_enable_stage_9e(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertTrue(
                all(
                    item.decision_status in {"needs_human_review", "deferred"}
                    for item in resolution.agent_decisions
                    if item.source_fact_coverage.facts_missing
                )
            )

    def test_can_enable_stage_9e_draft_only_for_high_confidence_safe_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_single_safe_row(matrix_path, paths)

            resolution = build_resolution(paths, matrix_path)

            self.assertTrue(resolution.stage_9e_gate["stage_9e_allowed"])
            self.assertEqual(["MDR-SAFE"], resolution.stage_9e_gate["stage_9e_allowed_scope"]["row_ids"])
            self.assertTrue(resolution.stage_9e_gate["requires_draft_only_output"])

    def test_fills_missing_affected_drafts_from_req_to_draft_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_single_safe_row(matrix_path, paths)
            matrix = load_json(matrix_path)
            matrix["reviewer_decision_rows"][0]["affected_drafts"] = []
            matrix["decision_clusters"][0]["affected_draft_ids"] = []
            write_json(matrix_path, matrix)

            resolution = build_resolution(paths, matrix_path)
            decision = resolution.agent_decisions[0]

            self.assertEqual(["DRAFT-SAFE"], decision.affected_drafts)
            self.assertTrue(decision.draft_mapping_evidence)
            self.assertTrue(resolution.stage_9e_gate["stage_9e_allowed"])

    def test_keeps_stage_9e_disabled_when_draft_mapping_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_single_safe_row(matrix_path, paths)
            matrix = load_json(matrix_path)
            matrix["reviewer_decision_rows"][0]["affected_drafts"] = []
            matrix["decision_clusters"][0]["affected_draft_ids"] = []
            write_json(matrix_path, matrix)
            write_json(paths["draft_proposal_path"], {"package_id": "WPKG-000001", "draft_test_cases": []})

            resolution = build_resolution(paths, matrix_path)
            decision = resolution.agent_decisions[0]

            self.assertEqual([], decision.affected_drafts)
            self.assertFalse(resolution.stage_9e_gate["stage_9e_allowed"])
            self.assertIn("draft mapping is incomplete", decision.rationale)

    def test_allows_subset_stage_9e_scope_while_leaving_ambiguous_rows_out(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_safe_and_ambiguous_rows(matrix_path, paths)

            resolution = build_resolution(paths, matrix_path)

            self.assertTrue(resolution.stage_9e_gate["stage_9e_allowed"])
            self.assertEqual(["MDR-SAFE"], resolution.stage_9e_candidate_scope["row_ids"])
            self.assertIn("MDR-AMBIG", resolution.deferred_or_human_review_scope["row_ids"])

    def test_existing_tc_evidence_is_coverage_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertTrue(resolution.evidence_quality_summary["coverage_only_existing_tc_evidence"])
            for decision in resolution.agent_decisions:
                for evidence in decision.existing_tc_coverage_evidence:
                    self.assertEqual("coverage_comparison_only", evidence["evidence_role"])
                    self.assertFalse(evidence["used_as_business_rule_source"])

    def test_marks_unsafe_when_existing_tc_used_as_business_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            data = load_json(matrix_path)
            data["reviewer_decision_rows"][0]["evidence_summary"] = "existing TC used as business source"
            write_json(matrix_path, data)

            resolution = build_resolution(paths, matrix_path)

            self.assertEqual("unsafe", resolution.agent_decisions[0].decision_status)
            self.assertEqual("blocked", resolution.resolution_status)

    def test_stage_9e_gate_requires_draft_only_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))

            resolution = build_resolution(paths, matrix_path)

            self.assertTrue(resolution.stage_9e_gate["requires_draft_only_output"])

    def test_markdown_includes_stage_9e_gate_and_safety_statement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution = build_resolution(paths, matrix_path)

            json_path, markdown_path = write_agent_decision_resolution(resolution, root / "work")
            loaded = load_agent_decision_resolution(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, AgentDecisionResolution)
            self.assertIn("Stage 9E Gate", markdown)
            self.assertIn("Safety Statement", markdown)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            resolution = build_resolution(paths, matrix_path)
            write_agent_decision_resolution(resolution, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_resolution_fixture(root: Path) -> tuple[Path, dict[str, Path], Path]:
    root, paths = setup_matrix_fixture(root)
    matrix = build_matrix(paths, root)
    matrix_path, _markdown_path = write_json_matrix(root, matrix)
    return root, paths, matrix_path


def write_json_matrix(root: Path, matrix) -> tuple[Path, Path]:
    from test_case_agent import write_manual_decision_matrix

    return write_manual_decision_matrix(matrix, root / "work")


def build_resolution(paths: dict[str, Path], matrix_path: Path) -> AgentDecisionResolution:
    return build_agent_decision_resolution(
        package_id="WPKG-000001",
        matrix_path=matrix_path,
        answer_template_path=paths.get("answer_template_path"),
        answer_validation_path=paths.get("answer_validation_path"),
        decision_pack_path=paths["decision_pack_path"],
        residual_analysis_path=paths["residual_analysis_path"],
        draft_proposal_path=paths["draft_proposal_path"],
        draft_review_path=paths["draft_review_path"],
        draft_revision_plan_path=paths["draft_revision_plan_path"],
        context_bundle_path=paths["context_bundle_path"],
        improvement_plan_path=paths["improvement_plan_path"],
    )


def make_single_safe_row(matrix_path: Path, paths: dict[str, Path]) -> None:
    matrix = load_json(matrix_path)
    matrix["decision_clusters"] = [safe_cluster()]
    matrix["reviewer_decision_rows"] = [safe_row()]
    write_json(matrix_path, matrix)
    write_json(paths["context_bundle_path"], safe_context_bundle())
    write_json(paths["draft_proposal_path"], safe_draft_proposal())
    write_json(paths["residual_analysis_path"], {"package_id": "WPKG-000001", "requirement_gap_analyses": []})
    write_json(paths["decision_pack_path"], {"package_id": "WPKG-000001", "source_grounding_resolutions": []})


def make_safe_and_ambiguous_rows(matrix_path: Path, paths: dict[str, Path]) -> None:
    matrix = load_json(matrix_path)
    ambiguous = safe_row(row_id="MDR-AMBIG", cluster_id="SRC-AMBIG", draft_id="DRAFT-AMBIG", req_uid="REQ-AMBIG")
    matrix["decision_clusters"] = [safe_cluster(), safe_cluster(cluster_id="SRC-AMBIG")]
    matrix["reviewer_decision_rows"] = [safe_row(), ambiguous]
    write_json(matrix_path, matrix)
    payload = safe_context_bundle()
    payload["candidate_requirements"].append(
        {
            "req_uid": "REQ-AMBIG",
            "object": "Client field",
            "source_text": "Client field is shown.",
            "source_anchors": [{"part": "word/document.xml"}],
        }
    )
    write_json(paths["context_bundle_path"], payload)
    proposal = safe_draft_proposal()
    proposal["draft_test_cases"].append(
        {
            "draft_id": "DRAFT-AMBIG",
            "coverage_intent": "Client field is shown.",
            "source_grounding_profiles": [{"missing_facts": ["source-backed user action"]}],
        }
    )
    write_json(paths["draft_proposal_path"], proposal)
    write_json(
        paths["residual_analysis_path"],
        {
            "package_id": "WPKG-000001",
            "requirement_gap_analyses": [
                {"req_uid": "REQ-AMBIG", "missing_facts": ["source-backed user action"]}
            ],
        },
    )
    write_json(paths["decision_pack_path"], {"package_id": "WPKG-000001", "source_grounding_resolutions": []})


def safe_cluster(cluster_id: str = "SRC-SAFE") -> dict:
    return {
        "cluster_id": cluster_id,
        "cluster_type": "source_grounding",
        "priority": "P1",
        "affected_draft_ids": ["DRAFT-SAFE"],
        "affected_proposed_tc_ids": [],
        "affected_req_uids": ["REQ-SAFE"],
        "source_req_ids": [],
        "similar_existing_tc_refs": [],
        "evidence": ["source-backed object/action/oracle present"],
        "root_cause": "source facts available",
        "reviewer_question": "Resolve?",
        "allowed_decisions": [revise_option(), defer_option()],
        "recommended_default": None,
        "blocked_until_answered": True,
        "safety_notes": [],
    }


def safe_row(
    row_id: str = "MDR-SAFE",
    cluster_id: str = "SRC-SAFE",
    draft_id: str = "DRAFT-SAFE",
    req_uid: str = "REQ-SAFE",
) -> dict:
    return {
        "row_id": row_id,
        "cluster_id": cluster_id,
        "decision_required": "Resolve source-backed row.",
        "reviewer_prompt": "Resolve source-backed row.",
        "decision_options": [revise_option(), defer_option()],
        "option_effects": [],
        "affected_drafts": [draft_id],
        "affected_requirements": [req_uid],
        "evidence_summary": "safe source-backed row",
        "source_evidence_refs": [req_uid],
        "existing_tc_evidence_refs": [],
        "risk_level": "low",
        "required_reviewer_role": "qa",
        "is_blocking_for_revised_draft": True,
    }


def revise_option() -> dict:
    return {
        "option_id": "OPT-REVISE",
        "label": "Revise draft",
        "meaning": "Revise source-backed draft.",
        "allowed_next_action": "revise_draft",
        "requires_source_evidence": True,
        "requires_existing_tc_review": False,
        "creates_or_edits_canonical_tc": False,
        "notes": [],
    }


def defer_option() -> dict:
    return {
        "option_id": "OPT-DEFER",
        "label": "Defer",
        "meaning": "Defer unsafe row.",
        "allowed_next_action": "defer",
        "requires_source_evidence": False,
        "requires_existing_tc_review": False,
        "creates_or_edits_canonical_tc": False,
        "notes": [],
    }


def safe_context_bundle() -> dict:
    return {
        "package_id": "WPKG-000001",
        "candidate_requirements": [
            {
                "req_uid": "REQ-SAFE",
                "object": "Submit button",
                "source_text": "When user clicks Submit, the system shows success message.",
                "expected_behavior": "System shows success message.",
                "source_anchors": [{"part": "word/document.xml"}],
                "table_source_contexts": [
                    {
                        "row_cells": ["Submit button", "Yes", "Yes", "Button", "", "When user clicks Submit, the system shows success message."],
                        "action_candidates": ["click Submit"],
                        "expected_behavior_candidates": ["System shows success message."],
                    }
                ],
            }
        ],
    }


def safe_draft_proposal() -> dict:
    return {
        "package_id": "WPKG-000001",
        "draft_test_cases": [
            {
                "draft_id": "DRAFT-SAFE",
                "proposed_tc_id": "TC-SAFE",
                "source_requirement_uids": ["REQ-SAFE"],
                "coverage_intent": "When user clicks Submit, the system shows success message.",
                "source_grounding_profiles": [],
                "warnings": [],
            }
        ],
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
