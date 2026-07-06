from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.new_tc_revised_draft_proposal import (
    NewTcRevisedDraftProposal,
    build_new_tc_revised_draft_proposal,
    load_new_tc_revised_draft_proposal,
    write_new_tc_revised_draft_proposal,
)


class NewTcRevisedDraftProposalTests(unittest.TestCase):
    def test_gate_false_blocks_stage_9e(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir), stage_9e_allowed=False)

            proposal = build_proposal(fixture)

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertIn("hardened Stage 9D.9 gate does not allow Stage 9E", proposal.blocking_reasons)

    def test_uses_only_hardened_validated_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))

            proposal = build_proposal(fixture)

            self.assertEqual(["MDR-000012"], proposal.stage_9e_scope["row_ids"])
            self.assertTrue(proposal.revised_draft_candidates)
            self.assertEqual({"MDR-000012"}, {item.source_agent_decision_row_id for item in proposal.revised_draft_candidates})
            self.assertTrue(
                all(item.source_agent_decision_row_id != "MDR-DEFER" for item in proposal.revised_draft_candidates)
            )

    def test_creates_draft_only_candidates_and_keeps_canonical_file_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            before = fixture["tc_path"].read_text(encoding="utf-8")

            proposal = build_proposal(fixture)

            self.assertIn(proposal.proposal_status, {"pass", "pass-with-warnings"})
            self.assertFalse(proposal.canonical_write_allowed)
            self.assertTrue(proposal.manual_review_required)
            self.assertTrue(all(not item.creates_or_edits_canonical_tc for item in proposal.revised_draft_candidates))
            self.assertEqual(before, fixture["tc_path"].read_text(encoding="utf-8"))

    def test_missing_source_draft_is_blocked_without_inventing_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir), affected_drafts=["DRAFT-MISSING"])

            proposal = build_proposal(fixture)

            self.assertEqual("pass-with-warnings", proposal.proposal_status)
            self.assertEqual(1, len(proposal.revised_draft_candidates))
            candidate = proposal.revised_draft_candidates[0]
            self.assertEqual("blocked", candidate.candidate_status)
            self.assertEqual(["DRAFT-MISSING"], candidate.source_draft_ids)

    def test_write_and_load_without_reviewer_answers_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            proposal = build_proposal(fixture)

            json_path, md_path = write_new_tc_revised_draft_proposal(proposal, fixture["work_dir"])
            loaded = load_new_tc_revised_draft_proposal(json_path)

            self.assertIsInstance(loaded, NewTcRevisedDraftProposal)
            self.assertTrue(md_path.exists())
            self.assertFalse(list(fixture["work_dir"].glob("*reviewer*answers*.json")))


def build_proposal(fixture: dict[str, Path]) -> NewTcRevisedDraftProposal:
    return build_new_tc_revised_draft_proposal(
        package_id="WPKG-000001",
        validation_path=fixture["validation_path"],
        resolution_path=fixture["resolution_path"],
        draft_proposal_path=fixture["draft_proposal_path"],
        context_bundle_path=fixture["context_bundle_path"],
        test_cases_dir=fixture["test_cases_dir"],
    )


def make_fixture(
    root: Path,
    *,
    stage_9e_allowed: bool = True,
    affected_drafts: list[str] | None = None,
) -> dict[str, Path]:
    work_dir = root / "work"
    test_cases_dir = root / "fts" / "Demo" / "test-cases"
    work_dir.mkdir(parents=True)
    test_cases_dir.mkdir(parents=True)
    tc_path = test_cases_dir / "scope.md"
    tc_path.write_text("## TC-DEMO-001\n\n**Traceability:** LEGACY-1\n", encoding="utf-8")

    affected = affected_drafts or ["DRAFT-001"]
    validation_path = work_dir / "agent-decision-validation-WPKG-000001.json"
    resolution_path = work_dir / "agent-decision-resolution-WPKG-000001.json"
    draft_proposal_path = work_dir / "new-tc-draft-proposal-WPKG-000001.json"
    context_bundle_path = work_dir / "create-new-tc-context-bundle-WPKG-000001.json"

    write_json(validation_path, validation_payload(stage_9e_allowed))
    write_json(resolution_path, resolution_payload(affected))
    write_json(draft_proposal_path, draft_proposal_payload())
    write_json(context_bundle_path, context_bundle_payload())
    return {
        "work_dir": work_dir,
        "test_cases_dir": test_cases_dir,
        "tc_path": tc_path,
        "validation_path": validation_path,
        "resolution_path": resolution_path,
        "draft_proposal_path": draft_proposal_path,
        "context_bundle_path": context_bundle_path,
    }


def validation_payload(stage_9e_allowed: bool) -> dict:
    return {
        "package_id": "WPKG-000001",
        "validation_status": "pass-with-warnings",
        "source_resolution_path": "agent-decision-resolution-WPKG-000001.json",
        "source_artifacts": {},
        "validation_checks": [],
        "decision_validation_results": [
            validation_result("MDR-000012", True, "valid"),
            validation_result("MDR-DEFER", False, "deferred", action="defer"),
        ],
        "validated_stage_9e_scope": {
            "row_ids": ["MDR-000012"] if stage_9e_allowed else [],
            "actions": ["split_candidate"] if stage_9e_allowed else [],
        },
        "rejected_stage_9e_scope": {"row_ids": []},
        "human_review_scope": {"row_ids": []},
        "deferred_scope": {"row_ids": ["MDR-DEFER"]},
        "gate_hardening_summary": {},
        "stage_9e_gate_hardened": {
            "stage_9e_allowed": stage_9e_allowed,
            "stage_9e_blockers": [] if stage_9e_allowed else ["no validated rows"],
        },
        "readiness_after_validation": {},
        "safety_summary": {"canonical_write_allowed": False},
        "canonical_write_allowed": False,
        "manual_review_required": True,
        "input_paths": {},
        "warnings": [],
        "blocking_reasons": [],
        "created_at_utc": "2026-07-06T00:00:00Z",
        "created_by_tool": "test",
    }


def validation_result(row_id: str, eligible: bool, result: str, *, action: str = "split_candidate") -> dict:
    return {
        "row_id": row_id,
        "cluster_id": f"CL-{row_id}",
        "selected_allowed_next_action": action,
        "original_decision_status": "resolved",
        "original_confidence": "high",
        "original_confidence_score": 0.9,
        "original_requires_human_review": False,
        "validation_result": result,
        "stage_9e_eligible": eligible,
        "validated_stage_9e_action": action if eligible else None,
        "required_evidence_checks": [],
        "confidence_checks": [],
        "safety_checks": [],
        "traceability_checks": [],
        "coverage_checks": [],
        "duplicate_risk_checks": [],
        "split_candidate_checks": [],
        "draft_mapping_checks": [],
        "mapped_draft_ids": ["DRAFT-001"] if eligible else [],
        "draft_mapping_sources": [],
        "draft_mapping_confidence": "high" if eligible else None,
        "existing_tc_evidence_checks": [],
        "reasoning": "source-backed action and oracle validated",
        "blocking_reasons": [],
        "warnings": [],
    }


def resolution_payload(affected_drafts: list[str]) -> dict:
    return {
        "package_id": "WPKG-000001",
        "resolution_status": "pass-with-warnings",
        "benchmark_name": "demo",
        "source_artifacts": {},
        "agent_decisions": [
            decision_payload("MDR-000012", "split_candidate", "resolved", affected_drafts, ["REQ-DEMO-1"]),
            decision_payload("MDR-DEFER", "defer", "deferred", [], ["REQ-DEMO-2"]),
        ],
        "decision_summary": {},
        "stage_9e_candidate_scope": {"row_ids": ["MDR-000012"]},
        "deferred_or_human_review_scope": {"row_ids": ["MDR-DEFER"]},
        "evidence_quality_summary": {},
        "safety_summary": {"canonical_write_allowed": False},
        "readiness_after_agent_resolution": {},
        "stage_9e_gate": {"stage_9e_allowed": True},
        "canonical_write_allowed": False,
        "manual_review_required": True,
        "input_paths": {},
        "warnings": [],
        "blocking_reasons": [],
        "created_at_utc": "2026-07-06T00:00:00Z",
        "created_by_tool": "test",
    }


def decision_payload(row_id: str, action: str, status: str, drafts: list[str], reqs: list[str]) -> dict:
    return {
        "row_id": row_id,
        "cluster_id": f"CL-{row_id}",
        "cluster_type": "source_grounding",
        "selected_option_id": "OPT-SPLIT" if action == "split_candidate" else "OPT-DEFER",
        "selected_allowed_next_action": action,
        "decision_source": "agent",
        "decision_status": status,
        "confidence": "high",
        "confidence_score": 0.9,
        "confidence_reasons": ["source-backed"],
        "evidence": ["source-backed evidence"],
        "source_evidence_refs": reqs,
        "source_fact_coverage": {
            "has_source_backed_object": True,
            "has_source_backed_action": True,
            "has_source_backed_oracle": True,
            "has_source_backed_condition": True,
            "has_table_or_anchor_evidence": True,
            "has_real_table_context": True,
            "facts_used": ["object", "action", "oracle"],
            "facts_missing": [],
            "facts_ambiguous": [],
        },
        "existing_tc_coverage_evidence": [{"test_case_id": "TC-DEMO-OLD"}],
        "duplicate_risk_assessment": {
            "risk_level": "low",
            "similar_existing_tc_refs": ["TC-DEMO-OLD"],
            "coverage_overlap_summary": "existing TC covers another behavior only",
            "source_backed_difference": "new source-backed oracle",
            "existing_tc_used_only_as_coverage_evidence": True,
            "recommended_resolution": "split_candidate",
        },
        "missing_facts": [],
        "rationale": "source fact supports a distinct new draft",
        "normalized_effect": "split source-backed behavior",
        "affected_drafts": drafts,
        "affected_requirements": reqs,
        "draft_mapping_evidence": [],
        "requires_human_review": False,
        "enables_stage_9e_draft_only": action == "split_candidate",
        "creates_or_edits_canonical_tc": False,
        "safety_warnings": [],
        "blocking_reasons": [],
    }


def draft_proposal_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "proposal_status": "pass-with-warnings",
        "draft_test_cases": [
            {
                "draft_id": "DRAFT-001",
                "proposed_tc_id": "TC-DEMO-NEW",
                "title": "Demo source backed behavior",
                "source_requirement_uids": ["REQ-DEMO-1"],
                "source_req_ids": ["SRC-DEMO-1"],
                "duplicate_risk_notes": ["low risk after split"],
                "source_grounding_profiles": [
                    {
                        "req_uid": "REQ-DEMO-1",
                        "source_req_id": "SRC-DEMO-1",
                        "object": "Submit button",
                        "user_action": "click Submit",
                        "observable_expected_behavior": "system shows success message",
                        "condition": "client card is open",
                        "source_anchors": [{"node_id": "NODE-1", "xpath": "/w:document/w:body[1]"}],
                    }
                ],
            }
        ],
    }


def context_bundle_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "candidate_requirements": [
            {
                "req_uid": "REQ-DEMO-1",
                "source_req_id": "SRC-DEMO-1",
                "object": "Submit button",
                "expected_behavior": "system shows success message",
                "source_text": "Click Submit shows success message.",
                "source_anchors": [{"node_id": "NODE-1"}],
            }
        ],
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
