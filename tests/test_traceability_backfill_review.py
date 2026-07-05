from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    TraceabilityBackfillReviewReport,
    build_traceability_backfill_proposal,
    build_traceability_backfill_review,
    load_traceability_backfill_review,
    write_traceability_backfill_proposal,
    write_traceability_backfill_review,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


class TraceabilityBackfillReviewTests(unittest.TestCase):
    def test_approves_traceability_line_only_append(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            report = build_review(ctx)

            self.assertEqual("approved", report.review_status)
            self.assertTrue(report.safe_for_controlled_apply)
            self.assertEqual([], report.failed_checks)

    def test_rejects_step_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, lambda data: replace_in_proposed_block(data, "1. Do one thing.", "1. Do another thing."))

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("patch_changes_only_traceability_lines", report.failed_checks)
            self.assertIn("no_steps_expected_test_data_headings_changed", report.failed_checks)

    def test_rejects_unknown_req_uid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, replace_req("REQ-000001", "REQ-UNKNOWN"))

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("added_req_refs_exist_in_registry", report.failed_checks)

    def test_rejects_unlisted_tc_touch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            def mutate(data: dict) -> None:
                data["original_tc_blocks"]["TC-OTHER"] = (
                    "## TC-OTHER\n\n**Traceability:** BSR 999\n\n### Steps\n\n1. Other.\n"
                )
                data["proposed_tc_blocks"]["TC-OTHER"] = (
                    "## TC-OTHER\n\n**Traceability:** BSR 999; REQ: REQ-000001\n\n### Steps\n\n1. Other.\n"
                )

            mutate_proposal(ctx, mutate)

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("patch_changes_only_listed_tc_blocks", report.failed_checks)
            self.assertIn("no_unrelated_tc_ids_touched", report.failed_checks)

    def test_rejects_duplicate_req_addition(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, lambda data: replace_in_proposed_block(data, "REQ-000001", "REQ-000001, REQ-000001"))

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("added_req_refs_not_duplicated", report.failed_checks)

    def test_requires_legacy_refs_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, lambda data: replace_in_proposed_block(data, "BSR 1; ", ""))

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("legacy_refs_preserved", report.failed_checks)

    def test_json_and_markdown_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            report = build_review(ctx)

            json_path, markdown_path = write_traceability_backfill_review(report, ctx.root)
            loaded = load_traceability_backfill_review(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, TraceabilityBackfillReviewReport)
            self.assertIn("Traceability Backfill Review", markdown)
            self.assertIn("Safe for controlled apply", markdown)

    def test_canonical_test_case_file_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            before = compute_file_sha256(ctx.tc_path)

            report = build_review(ctx)
            write_traceability_backfill_review(report, ctx.root)

            self.assertEqual(before, compute_file_sha256(ctx.tc_path))


class Context:
    def __init__(
        self,
        *,
        root: Path,
        tc_path: Path,
        backfill_proposal_path: Path,
        repair_strategy_path: Path,
        diagnostics_path: Path,
        old_registry_path: Path,
        new_registry_path: Path,
    ) -> None:
        self.root = root
        self.tc_path = tc_path
        self.backfill_proposal_path = backfill_proposal_path
        self.repair_strategy_path = repair_strategy_path
        self.diagnostics_path = diagnostics_path
        self.old_registry_path = old_registry_path
        self.new_registry_path = new_registry_path


def setup_context(temp_dir: str) -> Context:
    root = Path(temp_dir)
    tc_path = root / "fts" / "demo-ft" / "test-cases" / "scope.md"
    tc_path.parent.mkdir(parents=True)
    tc_path.write_text(
        "## TC-001\n"
        "\n"
        "**Traceability:** BSR 1; ATOM-1\n"
        "\n"
        "### Steps\n"
        "\n"
        "1. Do one thing.\n"
        "\n"
        "### Expected Result\n"
        "\n"
        "Result stays unchanged.\n"
        "\n"
        "### Test Data\n"
        "\n"
        "Data stays unchanged.\n"
        "\n"
        "## TC-OTHER\n"
        "\n"
        "**Traceability:** BSR 999\n"
        "\n"
        "### Steps\n"
        "\n"
        "1. Other.\n",
        encoding="utf-8",
        newline="\n",
    )
    repair_strategy_path = root / "traceability-repair-strategy.old-v1-to-new-v1.json"
    diagnostics_path = root / "traceability-mismatch-diagnostics.old-v1-to-new-v1.json"
    writer_proposal_path = root / "writer-dry-run-proposal-WPKG-000003.json"
    backfill_proposal_path = root / "traceability-backfill-proposal-WPKG-000003.json"
    old_registry_path = root / "requirements.old-v1.jsonl"
    new_registry_path = root / "requirements.new-v1.jsonl"
    write_json(repair_strategy_path, repair_strategy_payload(tc_path))
    write_json(diagnostics_path, diagnostics_payload())
    write_json(writer_proposal_path, writer_proposal_payload(tc_path))
    write_jsonl(old_registry_path, [{"req_uid": "REQ-000001", "source_req_id": "BSR 1"}])
    write_jsonl(new_registry_path, [{"req_uid": "REQ-000002", "source_req_id": "BSR 1"}])
    proposal = build_traceability_backfill_proposal(
        package_id="WPKG-000003",
        repair_strategy_path=repair_strategy_path,
        diagnostics_path=diagnostics_path,
        proposal_paths=[writer_proposal_path],
        test_cases_dir=tc_path.parent,
        workspace_root=root,
    )
    write_traceability_backfill_proposal(proposal, root)
    return Context(
        root=root,
        tc_path=tc_path,
        backfill_proposal_path=backfill_proposal_path,
        repair_strategy_path=repair_strategy_path,
        diagnostics_path=diagnostics_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
    )


def build_review(ctx: Context) -> TraceabilityBackfillReviewReport:
    return build_traceability_backfill_review(
        package_id="WPKG-000003",
        backfill_proposal_path=ctx.backfill_proposal_path,
        repair_strategy_path=ctx.repair_strategy_path,
        diagnostics_path=ctx.diagnostics_path,
        old_registry_path=ctx.old_registry_path,
        new_registry_path=ctx.new_registry_path,
        test_cases_dir=ctx.tc_path.parent,
        workspace_root=ctx.root,
    )


def mutate_proposal(ctx: Context, mutate: callable) -> None:
    data = json.loads(ctx.backfill_proposal_path.read_text(encoding="utf-8"))
    mutate(data)
    ctx.backfill_proposal_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def replace_in_proposed_block(data: dict, old: str, new: str) -> None:
    data["proposed_tc_blocks"]["TC-001"] = data["proposed_tc_blocks"]["TC-001"].replace(old, new)
    for change in data["backfill_changes"]:
        change["new_traceability_line"] = change["new_traceability_line"].replace(old, new)
    data["unified_diff_preview"] = data["unified_diff_preview"].replace(old, new)


def replace_req(old_req: str, new_req: str):
    def mutate(data: dict) -> None:
        replace_in_proposed_block(data, old_req, new_req)
        for change in data["backfill_changes"]:
            change["added_req_uids"] = [new_req if req == old_req else req for req in change["added_req_uids"]]
    return mutate


def repair_strategy_payload(tc_path: Path) -> dict:
    item = {
        "repair_item_id": "TRPAIR-000001",
        "package_id": "WPKG-000003",
        "test_case_id": "TC-001",
        "file_path": str(tc_path),
        "mismatch_type": "req_uid_generated_after_tc_creation",
        "current_traceability_line": "**Traceability:** BSR 1; ATOM-1",
        "legacy_refs_present": ["BSR 1", "ATOM-1"],
        "missing_req_uids": ["REQ-000001"],
        "candidate_req_uids_to_backfill": ["REQ-000001"],
        "source_req_ids_supporting_candidate": ["BSR 1"],
        "confidence": "high",
        "requires_manual_validation": True,
        "allowed_next_action": "create_backfill_proposal",
        "rationale": ["preview-only backfill candidate"],
        "warnings": [],
        "plan_item_id": "PLAN-000001",
        "impact_id": "IMP-000001",
        "change_id": "CHG-000001",
    }
    return {
        "old_source_version": "old-v1",
        "new_source_version": "new-v1",
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "input_paths": {},
        "strategy_status": "pass-with-warnings",
        "recommended_strategy": "mixed",
        "automatic_replacement_allowed": False,
        "backfill_recommended": True,
        "source_req_id_fallback_recommended": True,
        "affected_packages": ["WPKG-000003"],
        "affected_test_cases": ["TC-001"],
        "repair_items": [item],
        "summary": {"strategy_status": "pass-with-warnings"},
        "recommendations": [],
        "warnings": [],
        "blocking_reasons": [],
    }


def diagnostics_payload() -> dict:
    return {
        "old_source_version": "old-v1",
        "new_source_version": "new-v1",
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "input_paths": {},
        "mismatches": [],
        "summary": {"diagnostic_status": "pass-with-warnings", "mismatches_total": 1},
        "warnings": [],
        "blocking_reasons": [],
    }


def writer_proposal_payload(tc_path: Path) -> dict:
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
        "missing_information": [],
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
