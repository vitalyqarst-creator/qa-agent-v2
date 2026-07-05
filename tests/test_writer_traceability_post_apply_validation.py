from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    WriterTraceabilityPostApplyValidationReport,
    build_writer_traceability_post_apply_validation,
    load_writer_traceability_post_apply_validation,
    write_writer_traceability_post_apply_validation,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


OLD_REQ_1 = "REQ-AUTOFIN-111111111111"
OLD_REQ_2 = "REQ-AUTOFIN-333333333333"
NEW_REQ_1 = "REQ-AUTOFIN-222222222222"
NEW_REQ_2 = "REQ-AUTOFIN-444444444444"


class WriterTraceabilityPostApplyValidationTests(unittest.TestCase):
    def test_passes_expected_traceability_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            report = build_validation(ctx)

            self.assertEqual("pass", report.validation_status)
            self.assertTrue(report.safe_to_commit)
            self.assertEqual([], report.failed_checks)

    def test_fails_if_apply_report_not_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            mutate_json(ctx.apply_report_path, lambda data: data.update({"apply_status": "previewed", "dry_run": True}))

            report = build_validation(ctx)

            self.assertEqual("failed", report.validation_status)
            self.assertFalse(report.safe_to_commit)
            self.assertIn("apply_status_applied", report.failed_checks)
            self.assertIn("apply_dry_run_false", report.failed_checks)

    def test_fails_if_staged_changes_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            run_git(ctx.root, ["add", str(ctx.tc_path.relative_to(ctx.root)).replace("\\", "/")])

            report = build_validation(ctx)

            self.assertEqual("failed", report.validation_status)
            self.assertFalse(report.safe_to_commit)
            self.assertIn("no_staged_changes", report.failed_checks)

    def test_fails_if_other_test_case_file_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            other = ctx.test_cases_dir / "other.md"
            other.write_text("## TC-OTHER-FILE\n\n**Traceability:** BSR 2\n", encoding="utf-8", newline="\n")

            report = build_validation(ctx)

            self.assertEqual("failed", report.validation_status)
            self.assertFalse(report.safe_to_commit)
            self.assertIn("only_expected_test_case_file_changed", report.failed_checks)

    def test_fails_if_step_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            ctx.tc_path.write_text(
                ctx.tc_path.read_text(encoding="utf-8").replace("1. Do one thing.", "1. Do another thing."),
                encoding="utf-8",
                newline="\n",
            )

            report = build_validation(ctx)

            self.assertEqual("failed", report.validation_status)
            self.assertIn("git_diff_changes_only_traceability_line", report.failed_checks)
            self.assertIn("backup_current_diff_only_expected_traceability_line", report.failed_checks)

    def test_fails_if_traceability_content_wrong(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            ctx.tc_path.write_text(
                ctx.tc_path.read_text(encoding="utf-8").replace("BSR 1; ", "").replace(NEW_REQ_2, OLD_REQ_2),
                encoding="utf-8",
                newline="\n",
            )

            report = build_validation(ctx)

            self.assertEqual("failed", report.validation_status)
            self.assertIn("current_traceability_legacy_refs_preserved", report.failed_checks)
            self.assertIn("current_traceability_new_req_refs_present", report.failed_checks)
            self.assertIn("current_traceability_old_req_refs_absent", report.failed_checks)

    def test_fails_if_registry_missing_new_req(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            write_jsonl(ctx.new_registry_path, [{"req_uid": NEW_REQ_1}])

            report = build_validation(ctx)

            self.assertEqual("failed", report.validation_status)
            self.assertIn("new_req_refs_exist_in_registry", report.failed_checks)

    def test_fails_if_backup_missing_or_wrong(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            Path(ctx.backup_path).write_text(current_file_text(), encoding="utf-8", newline="\n")

            report = build_validation(ctx)

            self.assertEqual("failed", report.validation_status)
            self.assertIn("backup_contains_old_traceability_refs", report.failed_checks)

    def test_json_and_markdown_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            report = build_validation(ctx)

            json_path, markdown_path = write_writer_traceability_post_apply_validation(
                report,
                ctx.work_dir,
                artifact_suffix="after-backfill",
            )
            loaded = load_writer_traceability_post_apply_validation(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, WriterTraceabilityPostApplyValidationReport)
            self.assertIn("Writer Traceability Post-Apply Validation", markdown)
            self.assertIn("Safe to commit", markdown)
            self.assertTrue(json_path.name.endswith("after-backfill.json"))

    def test_validator_does_not_modify_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            before = compute_file_sha256(ctx.tc_path)

            report = build_validation(ctx)
            write_writer_traceability_post_apply_validation(report, ctx.work_dir, artifact_suffix="after-backfill")

            self.assertEqual(before, compute_file_sha256(ctx.tc_path))


class Context:
    def __init__(
        self,
        *,
        root: Path,
        work_dir: Path,
        test_cases_dir: Path,
        tc_path: Path,
        backup_path: Path,
        apply_report_path: Path,
        proposal_path: Path,
        review_path: Path,
        update_plan_path: Path,
        old_registry_path: Path,
        new_registry_path: Path,
    ) -> None:
        self.root = root
        self.work_dir = work_dir
        self.test_cases_dir = test_cases_dir
        self.tc_path = tc_path
        self.backup_path = backup_path
        self.apply_report_path = apply_report_path
        self.proposal_path = proposal_path
        self.review_path = review_path
        self.update_plan_path = update_plan_path
        self.old_registry_path = old_registry_path
        self.new_registry_path = new_registry_path


def setup_context(temp_dir: str) -> Context:
    root = Path(temp_dir)
    run_git(root, ["init"])
    run_git(root, ["config", "user.email", "tests@example.com"])
    run_git(root, ["config", "user.name", "Tests"])
    test_cases_dir = root / "fts" / "demo-ft" / "test-cases"
    work_dir = root / "fts" / "demo-ft" / "work"
    test_cases_dir.mkdir(parents=True)
    work_dir.mkdir(parents=True)
    tc_path = test_cases_dir / "scope.md"
    tc_path.write_text(backup_file_text(), encoding="utf-8", newline="\n")
    run_git(root, ["add", str(tc_path.relative_to(root)).replace("\\", "/")])
    run_git(root, ["commit", "-m", "baseline"])

    backup_path = work_dir / "backups" / "writer-traceability-update-WPKG-000003-after-backfill" / "scope.md.bak"
    backup_path.parent.mkdir(parents=True)
    backup_path.write_text(backup_file_text(), encoding="utf-8", newline="\n")
    tc_path.write_text(current_file_text(), encoding="utf-8", newline="\n")

    apply_report_path = work_dir / "writer-traceability-update-apply-WPKG-000003-after-backfill.json"
    proposal_path = work_dir / "writer-dry-run-proposal-WPKG-000003-after-backfill.json"
    review_path = work_dir / "writer-proposal-review-WPKG-000003-after-backfill.json"
    update_plan_path = work_dir / "test-case-update-plan.old-to-new.json"
    old_registry_path = work_dir / "requirements.old.jsonl"
    new_registry_path = work_dir / "requirements.new.jsonl"
    write_json(apply_report_path, apply_report_payload(tc_path, backup_path))
    write_json(proposal_path, proposal_payload(tc_path))
    write_json(review_path, review_payload())
    write_json(update_plan_path, {"plan_items": []})
    write_jsonl(old_registry_path, [{"req_uid": OLD_REQ_1}, {"req_uid": OLD_REQ_2}])
    write_jsonl(new_registry_path, [{"req_uid": NEW_REQ_1}, {"req_uid": NEW_REQ_2}])
    return Context(
        root=root,
        work_dir=work_dir,
        test_cases_dir=test_cases_dir,
        tc_path=tc_path,
        backup_path=backup_path,
        apply_report_path=apply_report_path,
        proposal_path=proposal_path,
        review_path=review_path,
        update_plan_path=update_plan_path,
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
    )


def build_validation(ctx: Context) -> WriterTraceabilityPostApplyValidationReport:
    return build_writer_traceability_post_apply_validation(
        package_id="WPKG-000003",
        apply_report_path=ctx.apply_report_path,
        writer_proposal_path=ctx.proposal_path,
        writer_review_path=ctx.review_path,
        update_plan_path=ctx.update_plan_path,
        old_registry_path=ctx.old_registry_path,
        new_registry_path=ctx.new_registry_path,
        test_cases_dir=ctx.test_cases_dir,
        workspace_root=ctx.root,
    )


def backup_file_text() -> str:
    return (
        "## TC-001\n"
        "\n"
        f"**Traceability:** BSR 1; ATOM-1; {OLD_REQ_1}, {OLD_REQ_2}\n"
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


def current_file_text() -> str:
    return backup_file_text().replace(f"{OLD_REQ_1}, {OLD_REQ_2}", f"{NEW_REQ_1}, {NEW_REQ_2}")


def original_tc_block() -> str:
    return backup_file_text().split("## TC-OTHER", 1)[0]


def proposed_tc_block() -> str:
    return current_file_text().split("## TC-OTHER", 1)[0]


def apply_report_payload(tc_path: Path, backup_path: Path) -> dict:
    return {
        "package_id": "WPKG-000003",
        "apply_status": "applied",
        "dry_run": False,
        "file_path": str(tc_path),
        "affected_test_case_ids": ["TC-001"],
        "applied_changes": [
            apply_change("PLAN-000001", OLD_REQ_1, NEW_REQ_1),
            apply_change("PLAN-000002", OLD_REQ_2, NEW_REQ_2),
        ],
        "previewed_changes": [],
        "skipped_changes": [],
        "backup_path": str(backup_path),
        "sha256_before": "old",
        "sha256_after": "new",
        "files_changed_count": 1,
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "warnings": [],
        "blocking_reasons": [],
    }


def apply_change(plan_item_id: str, old_ref: str, new_ref: str) -> dict:
    return {
        "plan_item_id": plan_item_id,
        "impact_id": plan_item_id.replace("PLAN", "IMP"),
        "change_id": plan_item_id.replace("PLAN", "CHG"),
        "test_case_id": "TC-001",
        "old_ref": old_ref,
        "new_ref": new_ref,
        "old_traceability_line": f"**Traceability:** BSR 1; ATOM-1; {OLD_REQ_1}, {OLD_REQ_2}",
        "new_traceability_line": f"**Traceability:** BSR 1; ATOM-1; {NEW_REQ_1}, {NEW_REQ_2}",
        "status": "applied",
    }


def proposal_payload(tc_path: Path) -> dict:
    return {
        "package_id": "WPKG-000003",
        "file_path": str(tc_path),
        "affected_test_case_ids": ["TC-001"],
        "source_plan_item_ids": ["PLAN-000001", "PLAN-000002"],
        "source_impact_ids": ["IMP-000001", "IMP-000002"],
        "source_change_ids": ["CHG-000001", "CHG-000002"],
        "proposal_status": "pass-with-warnings",
        "risk_level": "low",
        "manual_review_required": True,
        "proposed_changes": [
            proposed_change("PLAN-000001", OLD_REQ_1, NEW_REQ_1),
            proposed_change("PLAN-000002", OLD_REQ_2, NEW_REQ_2),
        ],
        "rationale": [],
        "missing_information": [],
        "original_tc_blocks": {"TC-001": original_tc_block()},
        "proposed_tc_blocks": {"TC-001": proposed_tc_block()},
        "unified_diff_preview": "",
        "sha256_before": "old",
        "sha256_after": "old",
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "warnings": [],
        "blocking_reasons": [],
    }


def proposed_change(plan_item_id: str, old_ref: str, new_ref: str) -> dict:
    return {
        "plan_item_id": plan_item_id,
        "impact_id": plan_item_id.replace("PLAN", "IMP"),
        "change_id": plan_item_id.replace("PLAN", "CHG"),
        "test_case_id": "TC-001",
        "change_type": "traceability_ref_replace",
        "old_ref": old_ref,
        "new_ref": new_ref,
        "status": "proposed",
    }


def review_payload() -> dict:
    return {
        "package_id": "WPKG-000003",
        "review_status": "approved-with-warnings",
        "safe_for_controlled_apply": True,
        "risk_level": "medium",
        "checks": [],
        "failed_checks": [],
        "warnings": [],
        "blocking_reasons": [],
        "reviewer_recommendation": "safe",
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "git_state": {},
    }


def mutate_json(path: Path, mutate: callable) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    write_json(path, data)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, entries: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries),
        encoding="utf-8",
        newline="\n",
    )


def run_git(root: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


if __name__ == "__main__":
    unittest.main()
