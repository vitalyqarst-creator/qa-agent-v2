from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    ResidualSourceGroundingGapAnalysis,
    build_residual_source_grounding_gap_analysis,
    load_residual_source_grounding_gap_analysis,
    write_new_tc_revision_decision_pack,
    write_residual_source_grounding_gap_analysis,
)
from tests.test_new_tc_revision_decision_pack import build_pack, setup_decision_pack_fixture


class ResidualSourceGroundingGapAnalysisTests(unittest.TestCase):
    def test_builds_analysis_from_stage_9d3_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture)

            self.assertEqual("pass-with-warnings", analysis.analysis_status)
            self.assertEqual("WPKG-000001", analysis.package_id)
            self.assertEqual(1, len(analysis.draft_gap_analyses))

    def test_blocks_when_draft_proposal_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture, draft_proposal_path=fixture["work"] / "missing.json")

            self.assertEqual("blocked", analysis.analysis_status)
            self.assertTrue(any("draft proposal is missing" in reason for reason in analysis.blocking_reasons))

    def test_blocks_on_package_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture, package_id="WPKG-OTHER")

            self.assertEqual("blocked", analysis.analysis_status)
            self.assertTrue(any("scoped to WPKG-000001" in reason for reason in analysis.blocking_reasons))

    def test_produces_one_draft_gap_analysis_per_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture)
            proposal = json.loads(fixture["proposal_path"].read_text(encoding="utf-8"))

            self.assertEqual(len(proposal["draft_test_cases"]), len(analysis.draft_gap_analyses))

    def test_produces_one_requirement_gap_analysis_per_candidate_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture)
            bundle = json.loads(fixture["bundle_path"].read_text(encoding="utf-8"))

            self.assertEqual(len(bundle["candidate_requirements"]), len(analysis.requirement_gap_analyses))

    def test_classifies_source_fact_present_not_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))
            make_no_duplicate_no_table(fixture)
            mutate_first_candidate(
                fixture["bundle_path"],
                condition=None,
                source_anchors=[],
            )
            mutate_first_profile(
                fixture["proposal_path"],
                condition=None,
                user_action=None,
                source_anchors=[],
                missing_facts=["source-backed user action"],
            )
            write_registry(
                fixture["new_registry_path"],
                [
                    {
                        "req_uid": "REQ-DEMO-NEW",
                        "source_req_id": "BSR 10",
                        "condition": "User opens client card",
                        "object": "Client card",
                        "expected_behavior": "The client card field is editable.",
                        "source_text": "User opens client card and field is editable.",
                        "normalized_text": "User opens client card and field is editable.",
                    }
                ],
            )

            analysis = build_analysis(fixture)

            self.assertEqual("source_fact_present_not_extracted", analysis.requirement_gap_analyses[0].gap_classification)
            self.assertGreater(len(analysis.extractor_gap_findings), 0)

    def test_classifies_source_fact_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))
            make_no_duplicate_no_table(fixture)
            mutate_first_candidate(
                fixture["bundle_path"],
                object=None,
                condition=None,
                expected_behavior=None,
                source_text="",
                normalized_text="",
                source_anchors=[],
            )
            mutate_first_profile(
                fixture["proposal_path"],
                object=None,
                condition=None,
                user_action=None,
                observable_expected_behavior=None,
                source_text="",
                normalized_text="",
                source_anchors=[],
                has_concrete_object=False,
                has_concrete_condition=False,
                has_user_action=False,
                has_observable_expected_behavior=False,
                missing_facts=[
                    "specific object/field/screen",
                    "source-backed condition",
                    "source-backed user action",
                    "observable expected behavior",
                ],
            )
            write_registry(fixture["new_registry_path"], [])

            analysis = build_analysis(fixture)

            self.assertEqual("source_fact_absent", analysis.requirement_gap_analyses[0].gap_classification)
            self.assertGreater(len(analysis.source_absence_findings), 0)

    def test_detects_table_or_anchor_context_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))
            make_no_duplicate_no_table(fixture)
            mutate_first_candidate(
                fixture["bundle_path"],
                condition=None,
                source_anchors=[{"xpath": "/w:tbl[1]/w:tr[2]", "flags": ["table"]}],
            )

            analysis = build_analysis(fixture)

            self.assertEqual("table_or_anchor_context_needed", analysis.requirement_gap_analyses[0].gap_classification)
            self.assertGreater(len(analysis.aggregate_context_findings), 0)

    def test_detects_duplicate_risk_driven_manual_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture)

            self.assertTrue(
                any(item.gap_classification == "duplicate_risk_prevents_decision" for item in analysis.draft_gap_analyses)
            )
            self.assertGreater(len(analysis.duplicate_risk_blockers), 0)

    def test_does_not_mark_create_or_apply_as_next_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture)

            self.assertNotIn("apply", analysis.next_stage_recommendation.casefold())
            self.assertNotIn("create canonical", analysis.next_stage_recommendation.casefold())

    def test_keeps_safety_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))

            analysis = build_analysis(fixture)

            self.assertFalse(analysis.canonical_write_allowed)
            self.assertTrue(analysis.manual_review_required)

    def test_writes_json_and_markdown_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))
            analysis = build_analysis(fixture)

            json_path, markdown_path = write_residual_source_grounding_gap_analysis(analysis, fixture["work"])
            loaded = load_residual_source_grounding_gap_analysis(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, ResidualSourceGroundingGapAnalysis)
            self.assertEqual("residual-source-grounding-gap-analysis-WPKG-000001.json", json_path.name)
            self.assertIn("Residual Source Grounding Gap Analysis", markdown)
            self.assertIn("Safety Statement", markdown)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = setup_analysis_fixture(Path(temp_dir))
            tc_path = fixture["root"] / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            analysis = build_analysis(fixture)
            write_residual_source_grounding_gap_analysis(analysis, fixture["work"])

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_analysis_fixture(root: Path) -> dict[str, Path]:
    root, bundle_path, proposal_path, review_path, plan_path = setup_decision_pack_fixture(root)
    work = root / "work"
    pack = build_pack(root, bundle_path, proposal_path, review_path, plan_path)
    decision_pack_path, _ = write_new_tc_revision_decision_pack(pack, work)
    improvement_path = work / "agent-capability-improvement-plan-WPKG-000001.json"
    write_json(improvement_path, {"package_id": "WPKG-000001", "plan_status": "pass-with-warnings"})
    return {
        "root": root,
        "work": work,
        "bundle_path": bundle_path,
        "proposal_path": proposal_path,
        "review_path": review_path,
        "plan_path": plan_path,
        "decision_pack_path": decision_pack_path,
        "improvement_path": improvement_path,
        "old_registry_path": work / "requirements.old.jsonl",
        "new_registry_path": work / "requirements.new.jsonl",
    }


def build_analysis(fixture: dict[str, Path], **overrides):
    root = fixture["root"]
    work = fixture["work"]
    kwargs = {
        "package_id": "WPKG-000001",
        "draft_proposal_path": fixture["proposal_path"],
        "draft_review_path": fixture["review_path"],
        "draft_revision_plan_path": fixture["plan_path"],
        "decision_pack_path": fixture["decision_pack_path"],
        "improvement_plan_path": fixture["improvement_path"],
        "context_bundle_path": fixture["bundle_path"],
        "old_registry_path": fixture["old_registry_path"],
        "new_registry_path": fixture["new_registry_path"],
        "requirements_diff_path": work / "requirements-diff.old-to-new.json",
        "impact_report_path": work / "impact-report.old-to-new.json",
        "update_plan_path": work / "test-case-update-plan.old-to-new.json",
        "old_source_manifest_path": work / "source-manifest.old.json",
        "new_source_manifest_path": work / "source-manifest.new.json",
        "test_cases_dir": root / "fts" / "Demo" / "test-cases",
    }
    kwargs.update(overrides)
    return build_residual_source_grounding_gap_analysis(**kwargs)


def make_no_duplicate_no_table(fixture: dict[str, Path]) -> None:
    mutate_json(fixture["bundle_path"], duplicate_risks=[], existing_tc_similarity=[])
    proposal = json.loads(fixture["proposal_path"].read_text(encoding="utf-8"))
    for draft in proposal.get("draft_test_cases", []):
        for profile in draft.get("source_grounding_profiles", []):
            profile["source_anchors"] = []
    fixture["proposal_path"].write_text(
        json.dumps(proposal, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    pack = json.loads(fixture["decision_pack_path"].read_text(encoding="utf-8"))
    pack["duplicate_risk_clusters"] = []
    pack["manual_decisions_required"] = [
        item for item in pack.get("manual_decisions_required", []) if item.get("scope") != "duplicate_risk"
    ]
    for decision in pack.get("draft_decisions", []):
        decision["duplicate_risk_status"] = "resolved"
    fixture["decision_pack_path"].write_text(
        json.dumps(pack, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def mutate_json(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mutate_first_candidate(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["candidate_requirements"][0].update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mutate_first_profile(path: Path, **updates) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["draft_test_cases"][0]["source_grounding_profiles"][0].update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_registry(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    unittest.main()
