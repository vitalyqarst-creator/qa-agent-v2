from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_case_agent import (
    TraceabilityBackfillApplyReport,
    apply_traceability_backfill_proposal,
    load_traceability_backfill_apply_report,
    write_traceability_backfill_apply_report,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


class TraceabilityBackfillApplyTests(unittest.TestCase):
    def test_dry_run_does_not_edit_file_and_reports_previewed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            before = ctx.tc_path.read_text(encoding="utf-8")

            report = run_apply(ctx)

            self.assertEqual("previewed", report.apply_status)
            self.assertTrue(report.dry_run)
            self.assertEqual(1, len(report.previewed_changes))
            self.assertEqual(0, report.files_changed_count)
            self.assertEqual(before, ctx.tc_path.read_text(encoding="utf-8"))

    def test_real_apply_without_ack_warnings_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            report = run_apply(ctx, dry_run=False, ack_warnings=False)

            self.assertEqual("blocked", report.apply_status)
            self.assertTrue(any("--ack-warnings" in reason for reason in report.blocking_reasons))
            self.assertNotIn("REQ-000001", ctx.tc_path.read_text(encoding="utf-8"))

    def test_real_apply_with_ack_edits_only_traceability_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            report = run_apply(ctx, dry_run=False, ack_warnings=True)
            content = ctx.tc_path.read_text(encoding="utf-8")

            self.assertEqual("applied", report.apply_status)
            self.assertEqual(1, report.files_changed_count)
            self.assertIn("**Traceability:** BSR 1; ATOM-1; REQ: REQ-000001", content)
            self.assertIn("1. Do one thing.", content)
            self.assertIn("Expected stays unchanged.", content)
            self.assertIn("Data stays unchanged.", content)

    def test_backup_is_created_before_real_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            original = ctx.tc_path.read_text(encoding="utf-8")

            report = run_apply(ctx, dry_run=False, ack_warnings=True)

            self.assertIsNotNone(report.backup_path)
            backup_path = Path(str(report.backup_path))
            self.assertTrue(backup_path.exists())
            self.assertEqual(original, backup_path.read_text(encoding="utf-8"))

    def test_blocks_if_sha_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            ctx.tc_path.write_text(ctx.tc_path.read_text(encoding="utf-8") + "\n<!-- drift -->\n", encoding="utf-8")

            report = run_apply(ctx)

            self.assertEqual("blocked", report.apply_status)
            self.assertTrue(any("current file SHA differs" in reason for reason in report.blocking_reasons))

    def test_blocks_if_original_tc_block_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            ctx.tc_path.write_text(
                ctx.tc_path.read_text(encoding="utf-8").replace("Expected stays unchanged.", "Expected drift."),
                encoding="utf-8",
            )
            set_proposal_sha(ctx, compute_file_sha256(ctx.tc_path))

            report = run_apply(ctx)

            self.assertEqual("blocked", report.apply_status)
            self.assertTrue(any("current TC block differs" in reason for reason in report.blocking_reasons))

    def test_blocks_if_proposal_changes_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, lambda data: replace_in_proposed_block(data, "1. Do one thing.", "1. Do another thing."))

            report = run_apply(ctx)

            self.assertEqual("blocked", report.apply_status)
            self.assertTrue(any("non-traceability lines" in reason for reason in report.blocking_reasons))

    def test_blocks_if_review_is_not_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_review(ctx, lambda data: data.update({"safe_for_controlled_apply": False}))

            report = run_apply(ctx)

            self.assertEqual("blocked", report.apply_status)
            self.assertTrue(any("safe_for_controlled_apply" in reason for reason in report.blocking_reasons))

    def test_blocks_if_review_failed_checks_not_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_review(ctx, lambda data: data.update({"failed_checks": ["patch_changes_only_traceability_lines"]}))

            report = run_apply(ctx)

            self.assertEqual("blocked", report.apply_status)
            self.assertTrue(any("failed_checks" in reason for reason in report.blocking_reasons))

    def test_post_apply_validation_catches_unrelated_tc_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            original = ctx.tc_path.read_text(encoding="utf-8")
            calls = {"count": 0}

            def bad_write(path: Path, content: str) -> None:
                calls["count"] += 1
                if calls["count"] == 1:
                    Path(path).write_text(content.replace("1. Other.", "1. Other changed."), encoding="utf-8", newline="\n")
                    return
                Path(path).write_text(content, encoding="utf-8", newline="\n")

            with patch("test_case_agent.traceability_backfill_apply._write_file_text", side_effect=bad_write):
                report = run_apply(ctx, dry_run=False, ack_warnings=True)

            self.assertEqual("failed", report.apply_status)
            self.assertTrue(any("post-apply" in reason for reason in report.blocking_reasons))
            self.assertEqual(original, ctx.tc_path.read_text(encoding="utf-8"))

    def test_json_and_markdown_apply_report_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            report = run_apply(ctx)

            json_path, markdown_path = write_traceability_backfill_apply_report(report, ctx.root)
            loaded = load_traceability_backfill_apply_report(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, TraceabilityBackfillApplyReport)
            self.assertIn("Traceability Backfill Apply", markdown)
            self.assertIn("Dry run", markdown)


class Context:
    def __init__(
        self,
        *,
        root: Path,
        tc_path: Path,
        proposal_path: Path,
        review_path: Path,
    ) -> None:
        self.root = root
        self.tc_path = tc_path
        self.proposal_path = proposal_path
        self.review_path = review_path


def setup_context(temp_dir: str) -> Context:
    root = Path(temp_dir)
    tc_path = root / "fts" / "demo-ft" / "test-cases" / "scope.md"
    tc_path.parent.mkdir(parents=True)
    tc_path.write_text(current_file_text(), encoding="utf-8", newline="\n")
    proposal_path = root / "traceability-backfill-proposal-WPKG-000003.json"
    review_path = root / "traceability-backfill-review-WPKG-000003.json"
    proposal = proposal_payload(tc_path)
    write_json(proposal_path, proposal)
    write_json(review_path, review_payload())
    return Context(root=root, tc_path=tc_path, proposal_path=proposal_path, review_path=review_path)


def run_apply(ctx: Context, *, dry_run: bool = True, ack_warnings: bool = False) -> TraceabilityBackfillApplyReport:
    return apply_traceability_backfill_proposal(
        package_id="WPKG-000003",
        backfill_proposal_path=ctx.proposal_path,
        backfill_review_path=ctx.review_path,
        test_cases_dir=ctx.tc_path.parent,
        out_dir=ctx.root,
        dry_run=dry_run,
        ack_warnings=ack_warnings,
        workspace_root=ctx.root,
    )


def current_file_text() -> str:
    return (
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
        "Expected stays unchanged.\n"
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
        "1. Other.\n"
    )


def proposed_tc_block() -> str:
    return (
        "## TC-001\n"
        "\n"
        "**Traceability:** BSR 1; ATOM-1; REQ: REQ-000001\n"
        "\n"
        "### Steps\n"
        "\n"
        "1. Do one thing.\n"
        "\n"
        "### Expected Result\n"
        "\n"
        "Expected stays unchanged.\n"
        "\n"
        "### Test Data\n"
        "\n"
        "Data stays unchanged.\n"
        "\n"
    )


def original_tc_block() -> str:
    return current_file_text().split("## TC-OTHER", 1)[0]


def proposal_payload(tc_path: Path) -> dict:
    sha = compute_file_sha256(tc_path)
    return {
        "package_id": "WPKG-000003",
        "proposal_status": "pass-with-warnings",
        "file_path": str(tc_path),
        "affected_test_case_ids": ["TC-001"],
        "repair_item_ids": ["TRPAIR-000001"],
        "backfill_changes": [
            {
                "repair_item_id": "TRPAIR-000001",
                "test_case_id": "TC-001",
                "added_req_uids": ["REQ-000001"],
                "supporting_source_req_ids": ["BSR 1"],
                "old_traceability_line": "**Traceability:** BSR 1; ATOM-1",
                "new_traceability_line": "**Traceability:** BSR 1; ATOM-1; REQ: REQ-000001",
                "status": "proposed",
                "rationale": ["preview-only backfill candidate"],
            }
        ],
        "original_tc_blocks": {"TC-001": original_tc_block()},
        "proposed_tc_blocks": {"TC-001": proposed_tc_block()},
        "unified_diff_preview": "",
        "sha256_before": sha,
        "sha256_after": sha,
        "manual_review_required": True,
        "risk_level": "medium",
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "warnings": [],
        "blocking_reasons": [],
    }


def review_payload() -> dict:
    return {
        "package_id": "WPKG-000003",
        "review_status": "approved-with-warnings",
        "safe_for_controlled_apply": True,
        "risk_level": "medium",
        "checks": [],
        "failed_checks": [],
        "warnings": ["inherited warning"],
        "blocking_reasons": [],
        "reviewer_recommendation": "safe for controlled apply after acknowledging warnings.",
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
    }


def mutate_proposal(ctx: Context, mutate: callable) -> None:
    data = json.loads(ctx.proposal_path.read_text(encoding="utf-8"))
    mutate(data)
    write_json(ctx.proposal_path, data)


def mutate_review(ctx: Context, mutate: callable) -> None:
    data = json.loads(ctx.review_path.read_text(encoding="utf-8"))
    mutate(data)
    write_json(ctx.review_path, data)


def replace_in_proposed_block(data: dict, old: str, new: str) -> None:
    data["proposed_tc_blocks"]["TC-001"] = data["proposed_tc_blocks"]["TC-001"].replace(old, new)


def set_proposal_sha(ctx: Context, sha: str) -> None:
    mutate_proposal(ctx, lambda data: data.update({"sha256_before": sha, "sha256_after": sha}))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    unittest.main()
