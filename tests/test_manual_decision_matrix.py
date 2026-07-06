from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    ManualDecisionMatrix,
    build_manual_decision_matrix,
    load_manual_decision_matrix,
    write_manual_decision_matrix,
)


class ManualDecisionMatrixTests(unittest.TestCase):
    def test_builds_matrix_from_stage_9d5a_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertEqual("pass-with-warnings", matrix.matrix_status)
            self.assertEqual("WPKG-000001", matrix.package_id)
            self.assertGreater(matrix.summary["raw_manual_findings_count"], 0)

    def test_blocks_when_decision_pack_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))
            paths["decision_pack_path"].unlink()

            matrix = build_matrix(paths, root)

            self.assertEqual("blocked", matrix.matrix_status)
            self.assertTrue(any("decision pack is missing" in reason for reason in matrix.blocking_reasons))

    def test_blocks_on_package_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))
            mutate_json(paths["decision_pack_path"], package_id="WPKG-OTHER")

            matrix = build_matrix(paths, root)

            self.assertEqual("blocked", matrix.matrix_status)
            self.assertTrue(any("package_id mismatch" in reason for reason in matrix.blocking_reasons))

    def test_produces_decision_clusters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertGreaterEqual(len(matrix.decision_clusters), 4)

    def test_produces_reviewer_decision_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertEqual(len(matrix.decision_clusters), len(matrix.reviewer_decision_rows))
            self.assertTrue(all(row.decision_options for row in matrix.reviewer_decision_rows))

    def test_compresses_raw_manual_findings_into_fewer_reviewer_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertGreater(matrix.summary["raw_manual_findings_count"], matrix.summary["reviewer_rows_count"])
            self.assertGreater(matrix.summary["estimated_reviewer_questions_reduction"], 0)

    def test_groups_duplicate_risk_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)
            cluster_types = {cluster.cluster_type for cluster in matrix.decision_clusters}

            self.assertIn("duplicate_risk", cluster_types)
            self.assertEqual(1, len(matrix.duplicate_risk_decision_groups))

    def test_groups_source_grounding_residual_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)
            cluster_types = {cluster.cluster_type for cluster in matrix.decision_clusters}

            self.assertIn("source_grounding", cluster_types)
            self.assertGreaterEqual(len(matrix.source_grounding_decision_groups), 1)

    def test_produces_allowed_decision_options(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)
            labels = {option.label for row in matrix.reviewer_decision_rows for option in row.decision_options}

            self.assertIn("Create separate new TC", labels)
            self.assertIn("Request source clarification", labels)

    def test_all_decision_options_do_not_create_or_edit_canonical_tc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertTrue(
                all(
                    option.creates_or_edits_canonical_tc is False
                    for row in matrix.reviewer_decision_rows
                    for option in row.decision_options
                )
            )

    def test_keeps_canonical_write_allowed_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertFalse(matrix.canonical_write_allowed)

    def test_keeps_manual_review_required_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertTrue(matrix.manual_review_required)

    def test_keeps_ready_for_revised_draft_proposal_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertFalse(matrix.ready_for_revised_draft_proposal_after_matrix)

    def test_does_not_mark_stage_9e_ready_without_reviewer_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))

            matrix = build_matrix(paths, root)

            self.assertFalse(matrix.readiness_impact.can_proceed_to_stage_9e_without_answers)

    def test_markdown_includes_reviewer_decision_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))
            matrix = build_matrix(paths, root)

            json_path, markdown_path = write_manual_decision_matrix(matrix, root / "work")
            loaded = load_manual_decision_matrix(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, ManualDecisionMatrix)
            self.assertEqual("manual-decision-matrix-WPKG-000001.json", json_path.name)
            self.assertIn("Reviewer Decision Matrix", markdown)
            self.assertIn("Compression Summary", markdown)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_matrix_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            matrix = build_matrix(paths, root)
            write_manual_decision_matrix(matrix, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_matrix_fixture(root: Path) -> tuple[Path, dict[str, Path]]:
    work = root / "work"
    tc_dir = root / "fts" / "Demo" / "test-cases"
    work.mkdir(parents=True)
    tc_dir.mkdir(parents=True)
    (tc_dir / "scope.md").write_text(
        "## TC-DEMO-001\n\n**Traceability:** BSR 1\n\n**Steps:** Open form.\n",
        encoding="utf-8",
        newline="\n",
    )
    paths = {
        "decision_pack_path": work / "new-tc-revision-decision-pack-WPKG-000001.json",
        "residual_analysis_path": work / "residual-source-grounding-gap-analysis-WPKG-000001.json",
        "improvement_plan_path": work / "agent-capability-improvement-plan-WPKG-000001.json",
        "draft_proposal_path": work / "new-tc-draft-proposal-WPKG-000001.json",
        "draft_review_path": work / "new-tc-draft-review-WPKG-000001.json",
        "draft_revision_plan_path": work / "new-tc-draft-revision-plan-WPKG-000001.json",
        "context_bundle_path": work / "create-new-tc-context-bundle-WPKG-000001.json",
        "final_registry_path": work / "requirements.autofin-final.jsonl",
        "requirements_diff_path": work / "requirements-diff.autofin-prefinal-to-autofin-final.json",
        "impact_report_path": work / "impact-report.autofin-prefinal-to-autofin-final.json",
        "update_plan_path": work / "test-case-update-plan.autofin-prefinal-to-autofin-final.json",
        "test_cases_dir": tc_dir,
    }
    write_json(paths["decision_pack_path"], decision_pack_payload())
    write_json(paths["residual_analysis_path"], residual_payload())
    write_json(paths["improvement_plan_path"], {"package_id": "WPKG-000001", "plan_status": "pass-with-warnings"})
    write_json(paths["draft_proposal_path"], {"package_id": "WPKG-000001", "draft_test_cases": []})
    write_json(paths["draft_review_path"], draft_review_payload())
    write_json(paths["draft_revision_plan_path"], draft_revision_plan_payload())
    write_json(paths["context_bundle_path"], context_bundle_payload())
    paths["final_registry_path"].write_text('{"req_uid":"REQ-DEMO-001"}\n', encoding="utf-8", newline="\n")
    write_json(paths["requirements_diff_path"], {"diff_status": "pass-with-warnings"})
    write_json(paths["impact_report_path"], {"impact_status": "pass-with-warnings"})
    write_json(paths["update_plan_path"], {"plan_status": "pass-with-warnings"})
    return root, paths


def build_matrix(paths: dict[str, Path], root: Path) -> ManualDecisionMatrix:
    return build_manual_decision_matrix(
        package_id="WPKG-000001",
        decision_pack_path=paths["decision_pack_path"],
        residual_analysis_path=paths["residual_analysis_path"],
        improvement_plan_path=paths["improvement_plan_path"],
        draft_proposal_path=paths["draft_proposal_path"],
        draft_review_path=paths["draft_review_path"],
        draft_revision_plan_path=paths["draft_revision_plan_path"],
        context_bundle_path=paths["context_bundle_path"],
        final_registry_path=paths["final_registry_path"],
        requirements_diff_path=paths["requirements_diff_path"],
        impact_report_path=paths["impact_report_path"],
        update_plan_path=paths["update_plan_path"],
        test_cases_dir=root / "fts" / "Demo" / "test-cases",
        benchmark_name="Demo benchmark",
    )


def decision_pack_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "decision_pack_status": "pass-with-warnings",
        "draft_decisions": [
            {
                "draft_id": "DRAFT-001",
                "proposed_tc_id": "TC-NEW-001",
                "decision": "needs_manual_decision",
                "decision_reason": "duplicate risk unresolved",
                "candidate_req_uids": ["REQ-DEMO-001"],
                "source_req_ids": ["BSR 1"],
                "manual_questions": ["Is separate TC needed?"],
            },
            {
                "draft_id": "DRAFT-002",
                "proposed_tc_id": "TC-NEW-002",
                "decision": "defer",
                "decision_reason": "source action missing",
                "candidate_req_uids": ["REQ-DEMO-002"],
                "source_req_ids": ["BSR 2"],
                "manual_questions": ["Should this be deferred?"],
            },
        ],
        "duplicate_risk_clusters": [
            {
                "cluster_id": "DRC-001",
                "draft_ids": ["DRAFT-001"],
                "candidate_req_uids": ["REQ-DEMO-001"],
                "similar_tc_ids": ["TC-DEMO-001"],
                "similar_file_paths": ["scope.md"],
                "risk": "medium",
                "cluster_action": "maybe_extend_existing_tc",
                "rationale": "similar object and expected behavior",
                "manual_decision_required": True,
                "comparison_required": True,
            }
        ],
        "existing_tc_comparisons": [],
        "source_grounding_resolutions": [
            {
                "draft_id": "DRAFT-002",
                "req_uid": "REQ-DEMO-002",
                "source_req_id": "BSR 2",
                "usable_source_facts": ["object: client card"],
                "missing_source_facts": ["source-backed user action", "observable expected behavior"],
                "manual_question": "What is the user action?",
            }
        ],
        "replacement_strategies": [
            {
                "draft_id": "DRAFT-003",
                "proposed_tc_id": "TC-NEW-003",
                "reason_for_replacement": "draft rejected",
                "candidate_req_uids": ["REQ-DEMO-003"],
                "replacement_mode": "rewrite_from_source",
                "required_source_facts": ["observable expected behavior"],
                "replacement_guidance": ["rewrite from source"],
                "manual_questions": ["Rewrite or split?"],
            }
        ],
        "manual_decisions_required": [
            {"scope": "draft", "id": "Q1", "question": "Is separate TC needed?"},
            {"scope": "draft", "id": "Q2", "question": "Should this be deferred?"},
            {"scope": "source", "id": "Q3", "question": "What is the user action?"},
            {"scope": "replacement", "id": "Q4", "question": "Rewrite or split?"},
            {"scope": "duplicate", "id": "Q5", "question": "Extend existing TC?"},
        ],
        "revised_draft_readiness": {
            "ready_for_revised_draft_proposal": False,
            "needs_manual_decision_count": 2,
        },
        "canonical_write_allowed": False,
        "manual_review_required": True,
    }


def residual_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "analysis_status": "pass-with-warnings",
        "summary": {"manual_decision_findings_count": 3},
        "requirement_gap_analyses": [
            {
                "req_uid": "REQ-DEMO-002",
                "source_req_id": "BSR 2",
                "missing_facts": ["source-backed user action", "observable expected behavior"],
                "available_source_fragments": ["object: client card"],
                "registry_evidence": ["table row 3"],
                "gap_classification": "source_fact_ambiguous",
                "has_object": True,
                "has_condition": True,
                "has_user_action": False,
                "has_expected_behavior": False,
            }
        ],
        "draft_gap_analyses": [],
        "manual_decision_findings": [
            {"req_uid": "REQ-DEMO-001", "classification": "duplicate_risk_prevents_decision", "recommended_action": "Resolve duplicate risk."},
            {"req_uid": "REQ-DEMO-002", "classification": "source_fact_ambiguous", "recommended_action": "Clarify user action."},
            {"req_uid": "REQ-DEMO-003", "classification": "manual_business_decision_required", "recommended_action": "Choose replacement mode."},
        ],
        "duplicate_risk_blockers": [
            {"req_uid": "REQ-DEMO-001", "classification": "duplicate_risk_prevents_decision", "recommended_action": "Compare with TC-DEMO-001."}
        ],
    }


def draft_review_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "review_status": "approved-with-warnings",
        "draft_reviews": [
            {
                "draft_id": "DRAFT-001",
                "issues": ["duplicate risk unresolved"],
                "required_fixes": ["resolve duplicate decision"],
            }
        ],
    }


def draft_revision_plan_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "revision_items": [
            {
                "draft_id": "DRAFT-001",
                "warnings": ["manual decision required before revision"],
            }
        ],
    }


def context_bundle_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "candidate_requirements": [
            {"req_uid": "REQ-DEMO-001", "source_req_id": "BSR 1"},
            {"req_uid": "REQ-DEMO-002", "source_req_id": "BSR 2"},
            {"req_uid": "REQ-DEMO-003", "source_req_id": "BSR 3"},
        ],
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mutate_json(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    write_json(path, payload)


if __name__ == "__main__":
    unittest.main()
