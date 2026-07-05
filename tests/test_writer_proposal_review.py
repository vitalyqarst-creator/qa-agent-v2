from __future__ import annotations

import difflib
import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    WriterProposalReviewReport,
    build_writer_proposal_review,
    load_writer_proposal_review,
    write_writer_proposal_review,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


OLD_REQ = "REQ-AUTOFIN-111111111111"
NEW_REQ = "REQ-AUTOFIN-222222222222"


class WriterProposalReviewTests(unittest.TestCase):
    def test_approves_traceability_line_only_replacement(self) -> None:
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
            self.assertIn("no_steps_changed", report.failed_checks)

    def test_rejects_expected_result_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, lambda data: replace_in_proposed_block(data, "Result stays unchanged.", "Result changed."))

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("patch_changes_only_traceability_lines", report.failed_checks)
            self.assertIn("no_expected_result_changed", report.failed_checks)

    def test_rejects_unlisted_tc_touch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            def mutate(data: dict) -> None:
                data["original_tc_blocks"]["TC-OTHER"] = (
                    "## TC-OTHER\n\n**Traceability:** BSR 999\n\n### Steps\n\n1. Other.\n"
                )
                data["proposed_tc_blocks"]["TC-OTHER"] = (
                    "## TC-OTHER\n\n**Traceability:** BSR 999; REQ: REQ-AUTOFIN-333333333333\n\n### Steps\n\n1. Other.\n"
                )

            mutate_proposal(ctx, mutate)

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("patch_changes_only_listed_tc_blocks", report.failed_checks)
            self.assertIn("no_unrelated_tc_ids_touched", report.failed_checks)

    def test_rejects_unknown_new_req_uid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            unknown = "REQ-AUTOFIN-999999999999"
            mutate_proposal(ctx, replace_req(NEW_REQ, unknown))
            mutate_update_plan_new_ref(ctx, unknown)

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("old_new_req_refs_exist_in_registry", report.failed_checks)

    def test_rejects_update_plan_mapping_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_update_plan_new_ref(ctx, "REQ-AUTOFIN-333333333333")

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("update_plan_mapping_matches", report.failed_checks)

    def test_rejects_duplicate_req_refs_after_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, lambda data: replace_in_proposed_block(data, NEW_REQ, f"{NEW_REQ}, {NEW_REQ}"))

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("no_duplicate_req_refs_after_replacement", report.failed_checks)

    def test_requires_legacy_refs_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_proposal(ctx, lambda data: replace_in_proposed_block(data, "BSR 1; ", ""))

            report = build_review(ctx)

            self.assertEqual("rejected", report.review_status)
            self.assertIn("legacy_refs_preserved", report.failed_checks)

    def test_blocks_if_old_req_absent_from_current_traceability_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            ctx.tc_path.write_text(
                ctx.tc_path.read_text(encoding="utf-8").replace(f"; {OLD_REQ}", ""),
                encoding="utf-8",
                newline="\n",
            )

            report = build_review(ctx)

            self.assertEqual("blocked", report.review_status)
            self.assertIn("current_traceability_contains_old_req_refs", report.blocking_reasons)

    def test_json_and_markdown_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            report = build_review(ctx)

            json_path, markdown_path = write_writer_proposal_review(report, ctx.root, artifact_suffix="after-backfill")
            loaded = load_writer_proposal_review(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, WriterProposalReviewReport)
            self.assertIn("Writer Proposal Review", markdown)
            self.assertIn("Safe for controlled apply", markdown)
            self.assertTrue(json_path.name.endswith("after-backfill.json"))

    def test_canonical_test_case_file_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            before = compute_file_sha256(ctx.tc_path)

            report = build_review(ctx)
            write_writer_proposal_review(report, ctx.root, artifact_suffix="after-backfill")

            self.assertEqual(before, compute_file_sha256(ctx.tc_path))


class Context:
    def __init__(
        self,
        *,
        root: Path,
        tc_path: Path,
        writer_proposal_path: Path,
        writer_proposal_md_path: Path,
        writer_proposal_patch_path: Path,
        update_plan_path: Path,
        impact_report_path: Path,
        requirements_diff_path: Path,
        old_registry_path: Path,
        new_registry_path: Path,
    ) -> None:
        self.root = root
        self.tc_path = tc_path
        self.writer_proposal_path = writer_proposal_path
        self.writer_proposal_md_path = writer_proposal_md_path
        self.writer_proposal_patch_path = writer_proposal_patch_path
        self.update_plan_path = update_plan_path
        self.impact_report_path = impact_report_path
        self.requirements_diff_path = requirements_diff_path
        self.old_registry_path = old_registry_path
        self.new_registry_path = new_registry_path


def setup_context(temp_dir: str) -> Context:
    root = Path(temp_dir)
    tc_path = root / "fts" / "demo-ft" / "test-cases" / "scope.md"
    tc_path.parent.mkdir(parents=True)
    original_block = tc_block(old_req=OLD_REQ)
    tc_path.write_text(
        original_block
        + "## TC-OTHER\n\n"
        + "**Traceability:** BSR 999\n\n"
        + "### Steps\n\n"
        + "1. Other.\n",
        encoding="utf-8",
        newline="\n",
    )
    proposed_block = original_block.replace(OLD_REQ, NEW_REQ)
    writer_proposal_path = root / "writer-dry-run-proposal-WPKG-000003-after-backfill.json"
    writer_proposal_md_path = root / "writer-dry-run-proposal-WPKG-000003-after-backfill.md"
    writer_proposal_patch_path = root / "writer-dry-run-proposal-WPKG-000003-after-backfill.patch"
    update_plan_path = root / "test-case-update-plan.old-to-new.json"
    impact_report_path = root / "impact-report.old-to-new.json"
    requirements_diff_path = root / "requirements-diff.old-to-new.json"
    old_registry_path = root / "requirements.old.jsonl"
    new_registry_path = root / "requirements.new.jsonl"
    write_json(writer_proposal_path, writer_proposal_payload(tc_path, original_block, proposed_block))
    writer_proposal_md_path.write_text("# proposal\n", encoding="utf-8", newline="\n")
    writer_proposal_patch_path.write_text("# patch\n", encoding="utf-8", newline="\n")
    write_json(update_plan_path, update_plan_payload(tc_path))
    write_json(impact_report_path, {"impact_entries": []})
    write_json(requirements_diff_path, {"diff_entries": []})
    write_jsonl(old_registry_path, [{"req_uid": OLD_REQ}])
    write_jsonl(new_registry_path, [{"req_uid": NEW_REQ}])
    return Context(
        root=root,
        tc_path=tc_path,
        writer_proposal_path=writer_proposal_path,
        writer_proposal_md_path=writer_proposal_md_path,
        writer_proposal_patch_path=writer_proposal_patch_path,
        update_plan_path=update_plan_path,
        impact_report_path=impact_report_path,
        requirements_diff_path=requirements_diff_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
    )


def build_review(ctx: Context) -> WriterProposalReviewReport:
    return build_writer_proposal_review(
        package_id="WPKG-000003",
        writer_proposal_path=ctx.writer_proposal_path,
        writer_proposal_markdown_path=ctx.writer_proposal_md_path,
        writer_proposal_patch_path=ctx.writer_proposal_patch_path,
        update_plan_path=ctx.update_plan_path,
        impact_report_path=ctx.impact_report_path,
        requirements_diff_path=ctx.requirements_diff_path,
        old_registry_path=ctx.old_registry_path,
        new_registry_path=ctx.new_registry_path,
        test_cases_dir=ctx.tc_path.parent,
        workspace_root=ctx.root,
        record_git_state=False,
    )


def tc_block(*, old_req: str) -> str:
    return (
        "## TC-001\n"
        "\n"
        f"**Traceability:** BSR 1; ATOM-1; {old_req}\n"
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
    )


def writer_proposal_payload(tc_path: Path, original_block: str, proposed_block: str) -> dict:
    current_text = tc_path.read_text(encoding="utf-8").splitlines(keepends=True)
    original_lines = original_block.splitlines(keepends=True)
    proposed_text = [*proposed_block.splitlines(keepends=True), *current_text[len(original_lines):]]
    diff = "".join(difflib.unified_diff(
        current_text,
        proposed_text,
        fromfile=f"a/{tc_path}",
        tofile=f"b/{tc_path}",
    ))
    sha = compute_file_sha256(tc_path)
    return {
        "package_id": "WPKG-000003",
        "file_path": str(tc_path),
        "affected_test_case_ids": ["TC-001"],
        "source_plan_item_ids": ["PLAN-000001"],
        "source_impact_ids": ["IMP-000001"],
        "source_change_ids": ["CHG-000001"],
        "proposal_status": "pass",
        "risk_level": "low",
        "manual_review_required": True,
        "proposed_changes": [
            {
                "plan_item_id": "PLAN-000001",
                "impact_id": "IMP-000001",
                "change_id": "CHG-000001",
                "test_case_id": "TC-001",
                "change_type": "traceability_ref_replace",
                "old_ref": OLD_REQ,
                "new_ref": NEW_REQ,
                "status": "proposed",
            }
        ],
        "rationale": [],
        "missing_information": [],
        "original_tc_blocks": {"TC-001": original_block},
        "proposed_tc_blocks": {"TC-001": proposed_block},
        "unified_diff_preview": diff,
        "sha256_before": sha,
        "sha256_after": sha,
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "warnings": [],
        "blocking_reasons": [],
    }


def update_plan_payload(tc_path: Path) -> dict:
    return {
        "ft_slug": "demo-ft",
        "old_source_version": "old",
        "new_source_version": "new",
        "impact_report_path": "impact-report.old-to-new.json",
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
                "apply_mode": "safe_auto_candidate",
                "old_refs": [OLD_REQ],
                "new_refs": [NEW_REQ],
                "required_changes": [],
                "forbidden_changes": [],
                "rationale": [],
                "requires_manual_review": True,
                "warnings": [],
            }
        ],
        "summary": {},
        "warnings": [],
        "blocking_reasons": [],
    }


def mutate_proposal(ctx: Context, mutate: callable) -> None:
    data = json.loads(ctx.writer_proposal_path.read_text(encoding="utf-8"))
    mutate(data)
    data["unified_diff_preview"] = recompute_diff(ctx, data)
    ctx.writer_proposal_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def replace_in_proposed_block(data: dict, old: str, new: str) -> None:
    data["proposed_tc_blocks"]["TC-001"] = data["proposed_tc_blocks"]["TC-001"].replace(old, new)


def replace_req(old_req: str, new_req: str):
    def mutate(data: dict) -> None:
        replace_in_proposed_block(data, old_req, new_req)
        for change in data["proposed_changes"]:
            if change["new_ref"] == old_req:
                change["new_ref"] = new_req
    return mutate


def mutate_update_plan_new_ref(ctx: Context, new_ref: str) -> None:
    data = json.loads(ctx.update_plan_path.read_text(encoding="utf-8"))
    data["plan_items"][0]["new_refs"] = [new_ref]
    ctx.update_plan_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def recompute_diff(ctx: Context, proposal: dict) -> str:
    current_lines = ctx.tc_path.read_text(encoding="utf-8").splitlines(keepends=True)
    proposed_lines = list(current_lines)
    original_block = proposal["original_tc_blocks"]["TC-001"].splitlines(keepends=True)
    proposed_block = proposal["proposed_tc_blocks"]["TC-001"].splitlines(keepends=True)
    proposed_lines[0:len(original_block)] = proposed_block
    if "TC-OTHER" in proposal["proposed_tc_blocks"]:
        proposed_lines.extend(proposal["proposed_tc_blocks"]["TC-OTHER"].splitlines(keepends=True))
    return "".join(difflib.unified_diff(
        current_lines,
        proposed_lines,
        fromfile=f"a/{ctx.tc_path}",
        tofile=f"b/{ctx.tc_path}",
    ))


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
