from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    TraceabilityBackfillProposal,
    build_traceability_backfill_proposal,
    load_traceability_backfill_proposal,
    write_traceability_backfill_proposal,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


class TraceabilityBackfillProposalTests(unittest.TestCase):
    def test_adds_missing_req_to_traceability_line_preview_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_lines=["**Traceability:** BSR 1, ATOM-1"])

            proposal = build_proposal(ctx)

            self.assertEqual("pass", proposal.proposal_status)
            self.assertEqual(["REQ-OLD"], proposal.backfill_changes[0].added_req_uids)
            self.assertIn("; REQ: REQ-OLD", proposal.backfill_changes[0].new_traceability_line)
            self.assertEqual(proposal.sha256_before, proposal.sha256_after)

    def test_does_not_duplicate_existing_req(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_lines=["**Traceability:** BSR 1; REQ: REQ-OLD"])

            proposal = build_proposal(ctx)

            self.assertEqual("pass-with-warnings", proposal.proposal_status)
            self.assertEqual("skipped", proposal.backfill_changes[0].status)
            self.assertEqual([], proposal.backfill_changes[0].added_req_uids)
            self.assertEqual(1, proposal.backfill_changes[0].new_traceability_line.count("REQ-OLD"))

    def test_does_not_remove_legacy_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_lines=["**Traceability:** BSR 1, ATOM-1, SRC-1"])

            proposal = build_proposal(ctx)

            new_line = proposal.backfill_changes[0].new_traceability_line
            self.assertIn("BSR 1", new_line)
            self.assertIn("ATOM-1", new_line)
            self.assertIn("SRC-1", new_line)
            self.assertIn("REQ-OLD", new_line)

    def test_does_not_change_steps_expected_or_test_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_lines=["**Traceability:** BSR 1"])

            proposal = build_proposal(ctx)

            proposed = proposal.proposed_tc_blocks["TC-001"]
            self.assertIn("1. Step mentions REQ-OLD but must not be edited.", proposed)
            self.assertIn("Expected mentions BSR 1 and stays unchanged.", proposed)
            self.assertIn("Data: REQ-OLD remains here.", proposed)
            self.assertEqual(1, proposed.count("; REQ: REQ-OLD"))

    def test_blocks_if_no_traceability_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_lines=[])

            proposal = build_proposal(ctx)

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("traceability line not found" in reason for reason in proposal.blocking_reasons))

    def test_blocks_if_duplicate_traceability_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(
                temp_dir,
                traceability_lines=["**Traceability:** BSR 1", "**Traceability:** ATOM-1"],
            )

            proposal = build_proposal(ctx)

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("multiple traceability lines" in reason for reason in proposal.blocking_reasons))

    def test_blocks_unlisted_tc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(
                temp_dir,
                traceability_lines=["**Traceability:** BSR 1"],
                writer_affected_test_case_ids=["TC-OTHER"],
            )

            proposal = build_proposal(ctx)

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("not listed in writer proposal" in reason for reason in proposal.blocking_reasons))

    def test_canonical_test_case_file_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_lines=["**Traceability:** BSR 1"])
            before = compute_file_sha256(ctx.tc_path)

            proposal = build_proposal(ctx)
            write_traceability_backfill_proposal(proposal, ctx.root)

            self.assertEqual(before, compute_file_sha256(ctx.tc_path))

    def test_json_markdown_and_patch_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_lines=["**Traceability:** BSR 1"])
            proposal = build_proposal(ctx)

            json_path, markdown_path, patch_path = write_traceability_backfill_proposal(proposal, ctx.root)
            loaded = load_traceability_backfill_proposal(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")
            patch = patch_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, TraceabilityBackfillProposal)
            self.assertIn("Traceability Backfill Proposal", markdown)
            self.assertIn("Preview-only traceability backfill patch", patch)
            self.assertIn("REQ-OLD", patch)


class Context:
    def __init__(
        self,
        *,
        root: Path,
        tc_path: Path,
        repair_strategy_path: Path,
        diagnostics_path: Path,
        proposal_path: Path,
    ) -> None:
        self.root = root
        self.tc_path = tc_path
        self.repair_strategy_path = repair_strategy_path
        self.diagnostics_path = diagnostics_path
        self.proposal_path = proposal_path


def build_proposal(ctx: Context) -> TraceabilityBackfillProposal:
    return build_traceability_backfill_proposal(
        package_id="WPKG-000003",
        repair_strategy_path=ctx.repair_strategy_path,
        diagnostics_path=ctx.diagnostics_path,
        proposal_paths=[ctx.proposal_path],
        test_cases_dir=ctx.tc_path.parent,
        workspace_root=ctx.root,
    )


def setup_context(
    temp_dir: str,
    *,
    traceability_lines: list[str],
    writer_affected_test_case_ids: list[str] | None = None,
) -> Context:
    root = Path(temp_dir)
    tc_path = root / "fts" / "demo-ft" / "test-cases" / "scope.md"
    tc_path.parent.mkdir(parents=True)
    traceability = "".join(f"{line}\n" for line in traceability_lines)
    tc_path.write_text(
        "## TC-001\n"
        "\n"
        f"{traceability}"
        "\n"
        "### Steps\n"
        "\n"
        "1. Step mentions REQ-OLD but must not be edited.\n"
        "\n"
        "### Expected Result\n"
        "\n"
        "Expected mentions BSR 1 and stays unchanged.\n"
        "\n"
        "### Test Data\n"
        "\n"
        "Data: REQ-OLD remains here.\n"
        "\n"
        "## TC-OTHER\n"
        "\n"
        "**Traceability:** BSR 999\n"
        "\n"
        "### Steps\n"
        "\n"
        "1. Unlisted TC must not change.\n",
        encoding="utf-8",
        newline="\n",
    )
    repair_strategy_path = root / "traceability-repair-strategy.old-v1-to-new-v1.json"
    diagnostics_path = root / "traceability-mismatch-diagnostics.old-v1-to-new-v1.json"
    proposal_path = root / "writer-dry-run-proposal-WPKG-000003.json"
    write_json(repair_strategy_path, repair_strategy_payload(tc_path))
    write_json(diagnostics_path, diagnostics_payload())
    write_json(
        proposal_path,
        writer_proposal_payload(
            tc_path,
            affected_test_case_ids=writer_affected_test_case_ids or ["TC-001"],
        ),
    )
    return Context(
        root=root,
        tc_path=tc_path,
        repair_strategy_path=repair_strategy_path,
        diagnostics_path=diagnostics_path,
        proposal_path=proposal_path,
    )


def repair_strategy_payload(tc_path: Path) -> dict:
    item = {
        "repair_item_id": "TRPAIR-000001",
        "package_id": "WPKG-000003",
        "test_case_id": "TC-001",
        "file_path": str(tc_path),
        "mismatch_type": "req_uid_generated_after_tc_creation",
        "current_traceability_line": "**Traceability:** BSR 1",
        "legacy_refs_present": ["BSR 1"],
        "missing_req_uids": ["REQ-OLD"],
        "candidate_req_uids_to_backfill": ["REQ-OLD"],
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
        "summary": {
            "strategy_status": "pass-with-warnings",
            "repair_items_total": 1,
            "confidence_counts": {"high": 1},
            "allowed_next_action_counts": {"create_backfill_proposal": 1},
        },
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


def writer_proposal_payload(tc_path: Path, *, affected_test_case_ids: list[str]) -> dict:
    return {
        "package_id": "WPKG-000003",
        "file_path": str(tc_path),
        "affected_test_case_ids": affected_test_case_ids,
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


if __name__ == "__main__":
    unittest.main()
