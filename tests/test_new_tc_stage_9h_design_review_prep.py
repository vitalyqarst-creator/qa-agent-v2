from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.new_tc_stage_9h_design_review_prep import (
    NewTcStage9HDesignReviewPrepReport,
    build_new_tc_stage_9h_design_review_prep,
    load_new_tc_stage_9h_design_review_prep,
    write_new_tc_stage_9h_design_review_prep,
)


class NewTcStage9HDesignReviewPrepTests(unittest.TestCase):
    def test_builds_prep_and_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))

            report = build_report(fixture)

            self.assertEqual("pass-with-warnings", report.prep_status)
            self.assertFalse(report.real_apply_authorized)
            self.assertFalse(report.canonical_write_allowed)
            self.assertFalse(report.stage_9h_preparation_authorizes_real_apply)
            self.assertTrue(report.stage_9h_requires_explicit_user_approval)

    def test_classifies_warnings_and_item_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))

            report = build_report(fixture)

            classifications = {item["classification"] for item in report.warning_reviews}
            self.assertIn("requires_extra_source_grounding_before_apply", classifications)
            self.assertIn("non_blocking_ack_required", classifications)
            self.assertEqual("needs_extra_source_grounding", report.item_readiness_reviews[0]["apply_readiness"])

    def test_blocks_for_blocked_stage_9g_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            mutate(fixture["json"], lambda payload: payload["dry_run_items"][0].update({"dry_run_decision": "blocked"}))

            report = build_report(fixture)

            self.assertEqual("blocked", report.prep_status)
            self.assertIn("Stage 9G contains blocked dry-run items", report.blocking_reasons)

    def test_reviews_target_tc_and_aggregate_risks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))

            report = build_report(fixture)

            self.assertEqual("pass", report.target_file_plan_review["status"])
            self.assertEqual("pass", report.tc_id_collision_review["status"])
            self.assertEqual("pass", report.aggregate_target_risk_review["status"])

    def test_blocks_aggregate_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            mutate(
                fixture["json"],
                lambda payload: payload["target_file_plan"]["targets"][0].update(
                    {"target_file_path": "fts/AutoFin/test-cases/14-application-card.md"}
                ),
            )

            report = build_report(fixture)

            self.assertEqual("blocked", report.prep_status)
            self.assertEqual("failed", report.target_file_plan_review["status"])

    def test_write_and_load_without_backups_or_patches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = make_fixture(Path(temp_dir))
            report = build_report(fixture)

            json_path, md_path = write_new_tc_stage_9h_design_review_prep(report, fixture["root"])
            loaded = load_new_tc_stage_9h_design_review_prep(json_path)

            self.assertIsInstance(loaded, NewTcStage9HDesignReviewPrepReport)
            self.assertTrue(md_path.exists())
            self.assertFalse(list(fixture["root"].glob("*.patch")))
            self.assertFalse((fixture["root"] / "backups").exists())


def make_fixture(root: Path) -> dict[str, Path]:
    json_path = root / "new-tc-create-apply-dry-run-WPKG-000001.json"
    md_path = root / "new-tc-create-apply-dry-run-WPKG-000001.md"
    write_json(json_path, stage_9g_payload())
    md_path.write_text("# Stage 9G\n", encoding="utf-8")
    return {"root": root, "json": json_path, "md": md_path}


def build_report(fixture: dict[str, Path]) -> NewTcStage9HDesignReviewPrepReport:
    return build_new_tc_stage_9h_design_review_prep(
        package_id="WPKG-000001",
        stage_9g_json_path=fixture["json"],
        stage_9g_markdown_path=fixture["md"],
    )


def mutate(path: Path, mutator) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload)
    write_json(path, payload)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def stage_9g_payload() -> dict:
    return {
        "package_id": "WPKG-000001",
        "dry_run_status": "pass-with-warnings",
        "dry_run_items": [
            {
                "dry_run_item_id": "CDRY-001",
                "source_revised_draft_id": "REV-001",
                "proposed_tc_id": "TC-DEMO-NEW",
                "target_file_path": "fts/AutoFin/test-cases/new-tc-demo.md",
                "target_section": "new standalone test case file",
                "planned_operation": "create_new_file",
                "dry_run_decision": "dry_run_allowed_with_warnings",
                "generated_markdown_preview": "## TC-DEMO-NEW\n\n**Safety note:** dry-run preview only\n",
                "traceability_refs": ["REQ-DEMO-1"],
                "req_uids": ["REQ-DEMO-1"],
                "source_req_ids": [],
                "source_evidence_refs": ["REQ-DEMO-1", "node-1"],
                "source_agent_decision_row_id": "MDR-000012",
                "source_validation_result_id": "MDR-000012",
                "review_result": "approved-with-warnings",
                "review_warnings": ["manual review notes are present"],
                "collision_risks": [],
                "format_warnings": [
                    "source_req_ids are absent; req_uids and source evidence refs are retained without fabrication",
                    "Need source-backed navigation/action details before creating canonical TC for REQ-DEMO-1.",
                ],
                "safety_warnings": [],
                "creates_or_edits_canonical_tc": False,
            }
        ],
        "target_file_plan": {
            "planned_strategy_counts": {"create_new_file": 1},
            "targets": [
                {
                    "dry_run_item_id": "CDRY-001",
                    "proposed_tc_id": "TC-DEMO-NEW",
                    "target_file_path": "fts/AutoFin/test-cases/new-tc-demo.md",
                    "planned_operation": "create_new_file",
                    "target_section": "new standalone test case file",
                    "collision_risks": [],
                }
            ],
        },
        "tc_id_plan": {
            "proposed_tc_ids_total": 1,
            "unique_proposed_tc_ids_total": 1,
            "duplicate_proposed_tc_ids": [],
            "existing_tc_id_collisions": [],
            "existing_tc_id_collision_count": 0,
        },
        "safety_checks": [{"check_id": "real_apply_authorized_false", "status": "pass"}],
        "stage_9h_readiness": {
            "stage_9h_design_recommended": True,
            "real_apply_authorized": False,
            "requires_explicit_user_approval": True,
        },
        "canonical_write_allowed": False,
        "real_apply_authorized": False,
        "warnings": [
            "manual review notes are present",
            "source_req_ids are absent; req_uids and source evidence refs are retained without fabrication",
            "Need source-backed navigation/action details before creating canonical TC for REQ-DEMO-1.",
        ],
        "blocking_reasons": [],
    }


if __name__ == "__main__":
    unittest.main()
