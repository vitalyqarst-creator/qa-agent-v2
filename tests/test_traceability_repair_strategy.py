from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    TraceabilityRepairStrategyReport,
    build_traceability_repair_strategy,
    load_traceability_repair_strategy,
    write_traceability_repair_strategy,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


class TraceabilityRepairStrategyTests(unittest.TestCase):
    def test_generated_req_uid_absent_becomes_backfill_candidate_not_auto_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, source_req_id="BSR 1", parsed_refs=["BSR 1"])

            report = build_strategy(ctx)

            self.assertEqual("pass-with-warnings", report.strategy_status)
            self.assertFalse(report.automatic_replacement_allowed)
            self.assertTrue(report.backfill_recommended)
            self.assertEqual(1, report.summary["repair_items_total"])
            self.assertEqual(["REQ-OLD"], report.repair_items[0].candidate_req_uids_to_backfill)
            self.assertEqual("create_backfill_proposal", report.repair_items[0].allowed_next_action)

    def test_legacy_source_req_id_supports_medium_or_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, source_req_id="BSR 1", parsed_refs=["BSR 1"])

            report = build_strategy(ctx)

            self.assertIn(report.repair_items[0].confidence, {"medium", "high"})
            self.assertEqual(["BSR 1"], report.repair_items[0].source_req_ids_supporting_candidate)

    def test_no_supporting_source_req_id_stays_manual_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, source_req_id=None, parsed_refs=["BSR 1"], old_refs=["REQ-OLD"])

            report = build_strategy(ctx)

            self.assertEqual("low", report.repair_items[0].confidence)
            self.assertEqual("manual_review_only", report.repair_items[0].allowed_next_action)
            self.assertEqual([], report.repair_items[0].candidate_req_uids_to_backfill)

    def test_automatic_replacement_is_false_for_missing_req_uid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, source_req_id="BSR 1", parsed_refs=["BSR 1"])

            report = build_strategy(ctx)

            self.assertFalse(report.automatic_replacement_allowed)

    def test_json_and_markdown_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, source_req_id="BSR 1", parsed_refs=["BSR 1"])
            report = build_strategy(ctx)

            json_path, markdown_path = write_traceability_repair_strategy(report, ctx.root)
            loaded = load_traceability_repair_strategy(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, TraceabilityRepairStrategyReport)
            self.assertEqual(1, loaded.summary["repair_items_total"])
            self.assertIn("Traceability Repair Strategy", markdown)
            self.assertIn("Backfill recommended", markdown)

    def test_canonical_test_case_file_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, source_req_id="BSR 1", parsed_refs=["BSR 1"])
            before = compute_file_sha256(ctx.tc_path)

            report = build_strategy(ctx)
            write_traceability_repair_strategy(report, ctx.root)

            self.assertEqual(before, compute_file_sha256(ctx.tc_path))


class Context:
    def __init__(
        self,
        *,
        root: Path,
        tc_path: Path,
        diagnostics_path: Path,
        proposal_path: Path,
        update_plan_path: Path,
        impact_report_path: Path,
        diff_path: Path,
        old_registry_path: Path,
        new_registry_path: Path,
    ) -> None:
        self.root = root
        self.tc_path = tc_path
        self.diagnostics_path = diagnostics_path
        self.proposal_path = proposal_path
        self.update_plan_path = update_plan_path
        self.impact_report_path = impact_report_path
        self.diff_path = diff_path
        self.old_registry_path = old_registry_path
        self.new_registry_path = new_registry_path


def build_strategy(ctx: Context) -> TraceabilityRepairStrategyReport:
    return build_traceability_repair_strategy(
        diagnostics_path=ctx.diagnostics_path,
        proposal_paths=[ctx.proposal_path],
        update_plan_path=ctx.update_plan_path,
        impact_report_path=ctx.impact_report_path,
        requirements_diff_path=ctx.diff_path,
        old_registry_path=ctx.old_registry_path,
        new_registry_path=ctx.new_registry_path,
    )


def setup_context(
    temp_dir: str,
    *,
    source_req_id: str | None,
    parsed_refs: list[str],
    old_refs: list[str] | None = None,
) -> Context:
    root = Path(temp_dir)
    tc_path = root / "fts" / "demo-ft" / "test-cases" / "scope.md"
    tc_path.parent.mkdir(parents=True)
    tc_path.write_text(
        "## TC-001\n\n"
        "**Traceability:** BSR 1\n\n"
        "### Steps\n\n"
        "1. Do one thing.\n",
        encoding="utf-8",
        newline="\n",
    )
    old_refs = old_refs if old_refs is not None else ["REQ-OLD", source_req_id or "BSR 1"]
    new_refs = ["REQ-NEW", source_req_id] if source_req_id else ["REQ-NEW"]
    current_traceability_line = "**Traceability:** " + ", ".join(parsed_refs) if parsed_refs else "**Traceability:**"
    diagnostics_path = root / "traceability-mismatch-diagnostics.old-v1-to-new-v1.json"
    proposal_path = root / "writer-dry-run-proposal-WPKG-000003.json"
    update_plan_path = root / "test-case-update-plan.old-v1-to-new-v1.json"
    impact_report_path = root / "impact-report.old-v1-to-new-v1.json"
    diff_path = root / "requirements-diff.old-v1-to-new-v1.json"
    old_registry_path = root / "requirements.old-v1.jsonl"
    new_registry_path = root / "requirements.new-v1.jsonl"

    write_json(diagnostics_path, diagnostics_payload(
        tc_path,
        current_traceability_line,
        parsed_refs,
        source_req_id,
        old_refs,
        new_refs,
    ))
    write_json(proposal_path, proposal_payload(tc_path))
    write_json(update_plan_path, update_plan_payload(tc_path, old_refs, new_refs))
    write_json(impact_report_path, impact_report_payload(tc_path, source_req_id))
    write_json(diff_path, diff_payload(source_req_id))
    write_jsonl(old_registry_path, [{"req_uid": "REQ-OLD", "source_req_id": source_req_id}])
    write_jsonl(new_registry_path, [{"req_uid": "REQ-NEW", "source_req_id": source_req_id}])
    return Context(
        root=root,
        tc_path=tc_path,
        diagnostics_path=diagnostics_path,
        proposal_path=proposal_path,
        update_plan_path=update_plan_path,
        impact_report_path=impact_report_path,
        diff_path=diff_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
    )


def diagnostics_payload(
    tc_path: Path,
    traceability_line: str,
    parsed_refs: list[str],
    source_req_id: str | None,
    old_refs: list[str],
    new_refs: list[str],
) -> dict:
    return {
        "old_source_version": "old-v1",
        "new_source_version": "new-v1",
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "input_paths": {},
        "mismatches": [
            {
                "package_id": "WPKG-000003",
                "test_case_id": "TC-001",
                "file_path": str(tc_path),
                "plan_item_id": "PLAN-000001",
                "impact_id": "IMP-000001",
                "change_id": "CHG-000001",
                "action": "traceability_update_only",
                "old_refs": old_refs,
                "new_refs": new_refs,
                "current_traceability_line": traceability_line,
                "parsed_refs_from_traceability_line": parsed_refs,
                "missing_old_refs": ["REQ-OLD"],
                "refs_present_in_tc_but_not_in_plan": [],
                "old_source_req_id": source_req_id,
                "new_source_req_id": source_req_id,
                "old_req_uid": "REQ-OLD",
                "new_req_uid": "REQ-NEW",
                "impact_change_type": "source_anchor_changed",
                "diff_change_type": "source_anchor_changed",
                "mismatch_type": "req_uid_generated_after_tc_creation",
                "notes": ["old generated req_uid is absent from current TC traceability."],
            }
        ],
        "summary": {"diagnostic_status": "pass-with-warnings", "mismatches_total": 1},
        "warnings": [],
        "blocking_reasons": [],
    }


def proposal_payload(tc_path: Path) -> dict:
    return {
        "package_id": "WPKG-000003",
        "file_path": str(tc_path),
        "affected_test_case_ids": ["TC-001"],
        "source_plan_item_ids": ["PLAN-000001"],
        "source_impact_ids": ["IMP-000001"],
        "source_change_ids": ["CHG-000001"],
        "proposal_status": "pass-with-warnings",
        "risk_level": "medium",
        "manual_review_required": True,
        "proposed_changes": [],
        "rationale": [],
        "missing_information": ["old ref not found"],
        "original_tc_blocks": {},
        "proposed_tc_blocks": {},
        "unified_diff_preview": "",
        "sha256_before": None,
        "sha256_after": None,
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "warnings": [],
        "blocking_reasons": [],
    }


def update_plan_payload(tc_path: Path, old_refs: list[str], new_refs: list[str]) -> dict:
    return {
        "ft_slug": "demo-ft",
        "old_source_version": "old-v1",
        "new_source_version": "new-v1",
        "impact_report_path": "impact-report.old-v1-to-new-v1.json",
        "test_cases_dir": str(tc_path.parent),
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "plan_items": [
            {
                "plan_item_id": "PLAN-000001",
                "impact_id": "IMP-000001",
                "change_id": "CHG-000001",
                "test_case_id": "TC-001",
                "file_path": str(tc_path),
                "action": "traceability_update_only",
                "apply_mode": "manual_only",
                "old_refs": old_refs,
                "new_refs": new_refs,
                "required_changes": [],
                "forbidden_changes": [],
                "rationale": [],
                "requires_manual_review": True,
                "warnings": [],
            }
        ],
        "summary": {"plan_status": "pass", "plan_items_total": 1},
        "warnings": [],
        "blocking_reasons": [],
    }


def impact_report_payload(tc_path: Path, source_req_id: str | None) -> dict:
    linked_source_req_ids = [source_req_id] if source_req_id else []
    return {
        "ft_slug": "demo-ft",
        "old_source_version": "old-v1",
        "new_source_version": "new-v1",
        "requirements_diff_path": "requirements-diff.old-v1-to-new-v1.json",
        "test_cases_dir": str(tc_path.parent),
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "impact_entries": [
            {
                "impact_id": "IMP-000001",
                "change_id": "CHG-000001",
                "change_type": "source_anchor_changed",
                "old_req_uid": "REQ-OLD",
                "new_req_uid": "REQ-NEW",
                "old_source_req_id": source_req_id,
                "new_source_req_id": source_req_id,
                "affected_test_cases": [
                    {
                        "test_case_id": "TC-001",
                        "file_path": str(tc_path),
                        "title": "Demo",
                        "linked_req_uids": [],
                        "linked_atom_ids": [],
                        "linked_source_req_ids": linked_source_req_ids,
                        "raw_traceability": ", ".join(linked_source_req_ids),
                        "parse_warnings": [],
                    }
                ],
                "action": "traceability_update_only",
                "priority": "low",
                "rationale": [],
                "requires_manual_review": True,
                "warnings": [],
            }
        ],
        "summary": {"impact_status": "pass"},
        "warnings": [],
        "blocking_reasons": [],
    }


def diff_payload(source_req_id: str | None) -> dict:
    return {
        "old_registry_path": "old.jsonl",
        "new_registry_path": "new.jsonl",
        "old_source_version": "old-v1",
        "new_source_version": "new-v1",
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "entries": [
            {
                "change_id": "CHG-000001",
                "change_type": "source_anchor_changed",
                "old_req_uid": "REQ-OLD",
                "new_req_uid": "REQ-NEW",
                "old_atom_id": None,
                "new_atom_id": None,
                "old_source_req_id": source_req_id,
                "new_source_req_id": source_req_id,
                "old_requirement_type": "validation",
                "new_requirement_type": "validation",
                "old_status": "active",
                "new_status": "active",
                "old_normalized_text": "old",
                "new_normalized_text": "new",
                "old_semantic_fingerprint": None,
                "new_semantic_fingerprint": None,
                "old_text_hash": None,
                "new_text_hash": None,
                "old_source_anchors": [],
                "new_source_anchors": [],
                "similarity_score": 1.0,
                "confidence": "high",
                "requires_manual_review": False,
                "reasons": [],
                "warnings": [],
            }
        ],
        "summary": {"diff_status": "pass"},
        "warnings": [],
        "blocking_reasons": [],
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, entries: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    unittest.main()
