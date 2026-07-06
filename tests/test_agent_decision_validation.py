from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_case_agent.agent_decision_validation import (
    AgentDecisionValidationReport,
    build_agent_decision_validation_report,
    load_agent_decision_validation_report,
    write_agent_decision_validation_report,
)
from test_case_agent.agent_decision_resolver import write_agent_decision_resolution
from tests.test_agent_decision_resolver import (
    build_resolution,
    load_json,
    make_safe_and_ambiguous_rows,
    make_single_safe_row,
    setup_resolution_fixture,
    write_json,
)


class AgentDecisionValidationTests(unittest.TestCase):
    def test_validates_agent_decision_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertIn(report.validation_status, {"pass", "pass-with-warnings", "rejected"})
            self.assertEqual("WPKG-000001", report.package_id)

    def test_recomputes_hardened_stage_9e_gate_independently(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_single_safe_row(matrix_path, paths)
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertTrue(report.stage_9e_gate_hardened["stage_9e_allowed"])
            self.assertEqual(["MDR-SAFE"], report.validated_stage_9e_scope["row_ids"])

    def test_rejects_candidate_with_requires_human_review_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_safe_and_ambiguous_rows(matrix_path, paths)
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            by_row = {item.row_id: item for item in report.decision_validation_results}
            self.assertIn(by_row["MDR-AMBIG"].validation_result, {"human-review-required", "deferred"})
            self.assertFalse(by_row["MDR-AMBIG"].stage_9e_eligible)

    def test_rejects_missing_source_object_action_or_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertTrue(
                any(
                    result.validation_result in {"human-review-required", "deferred", "rejected"}
                    and result.blocking_reasons
                    for result in report.decision_validation_results
                )
            )

    def test_rejects_existing_tc_as_business_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution = build_resolution(paths, matrix_path)
            first = resolution.agent_decisions[0]
            unsafe = replace(
                first,
                decision_status="unsafe",
                safety_warnings=["existing TC evidence appears to be used as a business-rule source"],
                blocking_reasons=["existing TC evidence appears to be used as a business-rule source"],
            )
            resolution = replace(resolution, agent_decisions=[unsafe] + resolution.agent_decisions[1:])
            resolution_path, _ = write_agent_decision_resolution(resolution, root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertEqual("unsafe", report.decision_validation_results[0].validation_result)

    def test_validates_split_candidate_only_with_source_backed_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)
            mdr_000012 = [item for item in report.decision_validation_results if item.row_id == "MDR-000012"]

            if mdr_000012:
                self.assertEqual("rejected", mdr_000012[0].validation_result)
                self.assertTrue(any("affected drafts" in reason for reason in mdr_000012[0].blocking_reasons))

    def test_split_candidate_with_mapped_drafts_can_pass_draft_existence_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_split_candidate_without_matrix_drafts(matrix_path, paths, include_mapping=True)
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)
            result = next(item for item in report.decision_validation_results if item.row_id == "MDR-SPLIT")
            checks = {check["check_id"]: check["status"] for check in result.split_candidate_checks}

            self.assertEqual("pass", checks["split_has_affected_drafts"])
            self.assertEqual("pass", checks["split_drafts_exist"])
            self.assertTrue(result.stage_9e_eligible)

    def test_validator_still_rejects_split_candidate_with_no_affected_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            make_split_candidate_without_matrix_drafts(matrix_path, paths, include_mapping=False)
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)
            result = next(item for item in report.decision_validation_results if item.row_id == "MDR-SPLIT")
            checks = {check["check_id"]: check["status"] for check in result.split_candidate_checks}

            self.assertEqual("failed", checks["split_has_affected_drafts"])
            self.assertFalse(result.stage_9e_eligible)

    def test_markdown_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")
            report = build_report(paths, matrix_path, resolution_path)

            json_path, markdown_path = write_agent_decision_validation_report(report, root / "work")
            loaded = load_agent_decision_validation_report(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, AgentDecisionValidationReport)
            self.assertIn("Hardened Gate", markdown)
            self.assertIn("Safety Statement", markdown)

    def test_keeps_canonical_writes_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths, matrix_path = setup_resolution_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")
            resolution_path, _ = write_agent_decision_resolution(build_resolution(paths, matrix_path), root / "work")

            report = build_report(paths, matrix_path, resolution_path)

            self.assertFalse(report.canonical_write_allowed)
            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def build_report(paths: dict[str, Path], matrix_path: Path, resolution_path: Path) -> AgentDecisionValidationReport:
    return build_agent_decision_validation_report(
        package_id="WPKG-000001",
        resolution_path=resolution_path,
        matrix_path=matrix_path,
        context_bundle_path=paths["context_bundle_path"],
        draft_proposal_path=paths["draft_proposal_path"],
        decision_pack_path=paths["decision_pack_path"],
        residual_analysis_path=paths["residual_analysis_path"],
    )


def make_split_candidate_without_matrix_drafts(
    matrix_path: Path,
    paths: dict[str, Path],
    *,
    include_mapping: bool,
) -> None:
    matrix = load_json(matrix_path)
    split_option = {
        "option_id": "OPT-SPLIT",
        "label": "Split candidate",
        "meaning": "Split source-backed behaviors.",
        "allowed_next_action": "split_candidate",
        "requires_source_evidence": True,
        "requires_existing_tc_review": False,
        "creates_or_edits_canonical_tc": False,
        "notes": [],
    }
    defer_option = {
        "option_id": "OPT-DEFER",
        "label": "Defer",
        "meaning": "Defer unsafe row.",
        "allowed_next_action": "defer",
        "requires_source_evidence": False,
        "requires_existing_tc_review": False,
        "creates_or_edits_canonical_tc": False,
        "notes": [],
    }
    matrix["decision_clusters"] = [
        {
            "cluster_id": "SRC-SPLIT",
            "cluster_type": "source_grounding",
            "priority": "P1",
            "affected_draft_ids": [],
            "affected_proposed_tc_ids": [],
            "affected_req_uids": ["REQ-SPLIT-1", "REQ-SPLIT-2"],
            "source_req_ids": [],
            "similar_existing_tc_refs": [],
            "evidence": ["source-backed split facts"],
            "root_cause": "multiple source facts available",
            "reviewer_question": "Split?",
            "allowed_decisions": [split_option, defer_option],
            "recommended_default": None,
            "blocked_until_answered": True,
            "safety_notes": [],
        }
    ]
    matrix["reviewer_decision_rows"] = [
        {
            "row_id": "MDR-SPLIT",
            "cluster_id": "SRC-SPLIT",
            "decision_required": "Split?",
            "reviewer_prompt": "Split?",
            "decision_options": [split_option, defer_option],
            "option_effects": [],
            "affected_drafts": [],
            "affected_requirements": ["REQ-SPLIT-1", "REQ-SPLIT-2"],
            "evidence_summary": "source-backed split facts",
            "source_evidence_refs": ["REQ-SPLIT-1", "REQ-SPLIT-2"],
            "existing_tc_evidence_refs": [],
            "risk_level": "low",
            "required_reviewer_role": "qa",
            "is_blocking_for_revised_draft": True,
        }
    ]
    write_json(matrix_path, matrix)
    write_json(
        paths["context_bundle_path"],
        {
            "package_id": "WPKG-000001",
            "candidate_requirements": [
                _source_backed_req("REQ-SPLIT-1"),
                _source_backed_req("REQ-SPLIT-2"),
            ],
        },
    )
    draft_test_cases = []
    if include_mapping:
        draft_test_cases = [
            {"draft_id": "DRAFT-SPLIT-1", "source_requirement_uids": ["REQ-SPLIT-1"], "coverage_intent": "split one"},
            {"draft_id": "DRAFT-SPLIT-2", "source_requirement_uids": ["REQ-SPLIT-2"], "coverage_intent": "split two"},
        ]
    write_json(paths["draft_proposal_path"], {"package_id": "WPKG-000001", "draft_test_cases": draft_test_cases})
    write_json(paths["residual_analysis_path"], {"package_id": "WPKG-000001", "requirement_gap_analyses": []})
    write_json(paths["decision_pack_path"], {"package_id": "WPKG-000001", "draft_decisions": []})


def _source_backed_req(req_uid: str) -> dict:
    return {
        "req_uid": req_uid,
        "object": "Submit button",
        "source_text": "When user clicks Submit, system shows success message.",
        "expected_behavior": "System shows success message.",
        "source_anchors": [{"part": "word/document.xml"}],
        "table_source_contexts": [
            {
                "row_cells": ["Submit button", "Yes", "Yes", "Button", "", "When user clicks Submit, system shows success message."],
                "action_candidates": ["click Submit"],
                "expected_behavior_candidates": ["System shows success message."],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
