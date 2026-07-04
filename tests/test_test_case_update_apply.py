from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    TestCaseUpdatePlan,
    UpdatePlanItem,
    apply_test_case_update_plan,
    load_test_case_update_apply_report,
    write_test_case_update_apply_report,
    write_test_case_update_plan,
)


class TestCaseUpdateApplyTests(unittest.TestCase):
    def test_dry_run_does_not_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            plan_path, _summary_path = write_plan(root, tc_dir, [safe_traceability_item(tc_path)])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
            )

            self.assertTrue(report.dry_run)
            self.assertEqual("previewed", report.apply_items[0].apply_status)
            self.assertEqual(0, report.summary["files_changed_count"])
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_apply_modifies_only_traceability_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original_lines = tc_path.read_text(encoding="utf-8").splitlines()
            plan_path, _summary_path = write_plan(root, tc_dir, [safe_traceability_item(tc_path)])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )
            after_lines = tc_path.read_text(encoding="utf-8").splitlines()

            self.assertEqual("applied", report.apply_items[0].apply_status)
            self.assertIn("REQ-DEMO-NEW", after_lines[1])
            self.assertIn("BSR 2", after_lines[1])
            self.assertIn("BSR 115", after_lines[1])
            self.assertEqual(original_lines[0], after_lines[0])
            self.assertEqual(original_lines[2:], after_lines[2:])
            self.assertEqual([2], report.apply_items[0].changed_lines)

    def test_keep_item_is_skipped_noop_and_does_not_write_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            plan_path, _summary_path = write_plan(root, tc_dir, [keep_item(tc_path)])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertEqual("skipped_noop", report.apply_items[0].apply_status)
            self.assertEqual(report.apply_items[0].before_sha256, report.apply_items[0].after_sha256)
            self.assertEqual([], report.apply_items[0].changed_lines)
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_update_existing_manual_only_is_skipped_manual_only(self) -> None:
        self.assert_manual_only_action("update_existing")

    def test_create_new_candidate_is_skipped_manual_only(self) -> None:
        self.assert_manual_only_action("create_new_candidate", with_file=False)

    def test_mark_deprecated_candidate_is_skipped_manual_only(self) -> None:
        self.assert_manual_only_action("mark_deprecated_candidate")

    def test_blocked_item_is_skipped_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            plan_path, _summary_path = write_plan(root, tc_dir, [blocked_item(tc_path)])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertEqual("skipped_blocked", report.apply_items[0].apply_status)
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_unsafe_traceability_update_with_missing_old_ref_is_skipped_unsafe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir, traceability="REQ-OTHER, BSR 99")
            original = tc_path.read_text(encoding="utf-8")
            plan_path, _summary_path = write_plan(root, tc_dir, [safe_traceability_item(tc_path)])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertEqual("skipped_unsafe", report.apply_items[0].apply_status)
            self.assertIn("no old refs found", report.apply_items[0].skipped_reason or "")
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_multiple_tc_blocks_with_same_id_is_skipped_unsafe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = (
                "## TC-001\n"
                "**Traceability:** REQ-DEMO-OLD, BSR 1\n"
                "### Steps\n"
                "- first\n"
                "## TC-001\n"
                "**Traceability:** REQ-DEMO-OLD, BSR 1\n"
            )
            tc_path.write_text(original, encoding="utf-8", newline="\n")
            plan_path, _summary_path = write_plan(root, tc_dir, [safe_traceability_item(tc_path)])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertEqual("skipped_unsafe", report.apply_items[0].apply_status)
            self.assertIn("multiple TC blocks", report.apply_items[0].skipped_reason or "")
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_no_changes_outside_traceability_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            before_lines = tc_path.read_text(encoding="utf-8").splitlines()
            plan_path, _summary_path = write_plan(root, tc_dir, [safe_traceability_item(tc_path)])

            apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )
            after_lines = tc_path.read_text(encoding="utf-8").splitlines()

            changed_indexes = [
                index for index, (before, after) in enumerate(zip(before_lines, after_lines), start=1)
                if before != after
            ]
            self.assertEqual([2], changed_indexes)

    def test_backup_is_created_before_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            plan_path, _summary_path = write_plan(root, tc_dir, [safe_traceability_item(tc_path)])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            backup_path = Path(report.apply_items[0].backup_path or "")
            self.assertTrue(backup_path.exists())
            self.assertEqual(original, backup_path.read_text(encoding="utf-8"))
            self.assertEqual([str(backup_path)], report.summary["backups_created"])

    def test_blocked_plan_blocks_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            plan_path, summary_path = write_plan(
                root,
                tc_dir,
                [safe_traceability_item(tc_path)],
                plan_status="blocked",
                blocking_reasons=["plan blocked for test"],
            )

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                update_plan_summary_path=summary_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertEqual("blocked", report.summary["apply_status"])
            self.assertEqual([], report.apply_items)
            self.assertTrue(any("plan blocked for test" in reason for reason in report.blocking_reasons))
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_duplicate_conflicting_safe_updates_block_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            plan_path, _summary_path = write_plan(
                root,
                tc_dir,
                [
                    safe_traceability_item(tc_path, plan_item_id="PLAN-000001", new_refs=["REQ-DEMO-NEW", "BSR 2"]),
                    safe_traceability_item(tc_path, plan_item_id="PLAN-000002", new_refs=["REQ-DEMO-NEW", "BSR 3"]),
                ],
            )

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertEqual("blocked", report.summary["apply_status"])
            self.assertEqual([], report.apply_items)
            self.assertTrue(any("conflicting safe traceability updates" in reason for reason in report.blocking_reasons))
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_json_and_markdown_apply_report_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            plan_path, _summary_path = write_plan(root, tc_dir, [safe_traceability_item(tc_path)])
            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
            )

            report_path, summary_path, markdown_path = write_test_case_update_apply_report(report, root)
            loaded = load_test_case_update_apply_report(report_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertTrue(report_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertEqual(1, len(loaded.apply_items))
            self.assertEqual(1, summary["previewed"])
            self.assertIn("## Summary", markdown)
            self.assertIn("## Previewed / Applied Changes", markdown)
            self.assertIn("## Skipped No-op", markdown)
            self.assertIn("## Skipped Manual-only", markdown)
            self.assertIn("## Skipped Unsafe", markdown)
            self.assertIn("## Failed Items", markdown)
            self.assertIn("## Files Changed", markdown)
            self.assertIn("## Backups", markdown)

    def test_file_sha_changes_only_for_applied_traceability_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            manual_path = tc_dir / "manual.md"
            manual_original = "## TC-002\n**Traceability:** REQ-MANUAL-OLD, BSR 10\n### Steps\n- keep\n"
            manual_path.write_text(manual_original, encoding="utf-8", newline="\n")
            before_trace_sha = sha256_text(tc_path.read_text(encoding="utf-8"))
            before_manual_sha = sha256_text(manual_path.read_text(encoding="utf-8"))
            plan_path, _summary_path = write_plan(
                root,
                tc_dir,
                [
                    safe_traceability_item(tc_path),
                    manual_item("update_existing", manual_path, plan_item_id="PLAN-000002", test_case_id="TC-002"),
                ],
            )

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertNotEqual(before_trace_sha, sha256_text(tc_path.read_text(encoding="utf-8")))
            self.assertEqual(before_manual_sha, sha256_text(manual_path.read_text(encoding="utf-8")))
            self.assertEqual("applied", report.apply_items[0].apply_status)
            self.assertEqual("skipped_manual_only", report.apply_items[1].apply_status)

    def assert_manual_only_action(self, action: str, *, with_file: bool = True) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            item = manual_item(action, tc_path if with_file else None)
            plan_path, _summary_path = write_plan(root, tc_dir, [item])

            report = apply_test_case_update_plan(
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                out_dir=root,
                dry_run=False,
            )

            self.assertEqual("skipped_manual_only", report.apply_items[0].apply_status)
            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))


def setup_root(
    temp_dir: str,
    *,
    traceability: str = "REQ-DEMO-OLD, BSR 1, BSR 115",
) -> tuple[Path, Path, Path]:
    root = Path(temp_dir)
    tc_dir = root / "fts" / "demo-ft" / "test-cases"
    tc_dir.mkdir(parents=True)
    tc_path = tc_dir / "scope.md"
    tc_path.write_text(
        "\n".join(
            [
                "## TC-001",
                f"**Traceability:** {traceability}",
                "### Steps",
                "1. Open the form",
                "### Expected Result",
                "The form is visible",
                "### Test Data",
                "Client = demo",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    return root, tc_dir, tc_path


def safe_traceability_item(
    tc_path: Path,
    *,
    plan_item_id: str = "PLAN-000001",
    test_case_id: str = "TC-001",
    new_refs: list[str] | None = None,
) -> UpdatePlanItem:
    return UpdatePlanItem(
        plan_item_id=plan_item_id,
        impact_id="IMP-000001",
        change_id="CHG-000001",
        test_case_id=test_case_id,
        file_path=str(tc_path),
        action="traceability_update_only",
        apply_mode="safe_auto_candidate",
        old_refs=["REQ-DEMO-OLD", "BSR 1"],
        new_refs=new_refs or ["REQ-DEMO-NEW", "BSR 2"],
        required_changes=["update traceability refs only"],
        forbidden_changes=["Do not change steps", "Do not change expected result", "Do not change test data"],
        rationale=["test"],
        requires_manual_review=False,
        warnings=[],
    )


def keep_item(tc_path: Path) -> UpdatePlanItem:
    return UpdatePlanItem(
        plan_item_id="PLAN-000001",
        impact_id="IMP-000001",
        change_id="CHG-000001",
        test_case_id="TC-001",
        file_path=str(tc_path),
        action="keep",
        apply_mode="safe_auto_candidate",
        old_refs=["REQ-DEMO-OLD"],
        new_refs=["REQ-DEMO-OLD"],
        required_changes=[],
        forbidden_changes=["Do not rewrite steps", "Do not rewrite expected result"],
        rationale=["test"],
        requires_manual_review=False,
        warnings=[],
    )


def manual_item(
    action: str,
    tc_path: Path | None,
    *,
    plan_item_id: str = "PLAN-000001",
    test_case_id: str | None = "TC-001",
) -> UpdatePlanItem:
    return UpdatePlanItem(
        plan_item_id=plan_item_id,
        impact_id="IMP-000001",
        change_id="CHG-000001",
        test_case_id=test_case_id if tc_path is not None else None,
        file_path=str(tc_path) if tc_path is not None else None,
        action=action,
        apply_mode="manual_only",
        old_refs=["REQ-DEMO-OLD"],
        new_refs=["REQ-DEMO-NEW"],
        required_changes=["manual review required"],
        forbidden_changes=["Do not auto-apply changes"],
        rationale=["test"],
        requires_manual_review=True,
        warnings=[],
    )


def blocked_item(tc_path: Path) -> UpdatePlanItem:
    return UpdatePlanItem(
        plan_item_id="PLAN-000001",
        impact_id="IMP-000001",
        change_id="CHG-000001",
        test_case_id="TC-001",
        file_path=str(tc_path),
        action="blocked",
        apply_mode="blocked",
        old_refs=["REQ-DEMO-OLD"],
        new_refs=["REQ-DEMO-NEW"],
        required_changes=["resolve blocking reason before planning updates"],
        forbidden_changes=["Do not update test cases while blocked"],
        rationale=["test"],
        requires_manual_review=True,
        warnings=[],
    )


def write_plan(
    root: Path,
    tc_dir: Path,
    items: list[UpdatePlanItem],
    *,
    plan_status: str = "pass",
    blocking_reasons: list[str] | None = None,
) -> tuple[Path, Path]:
    action_keys = [
        "keep",
        "update_existing",
        "traceability_update_only",
        "create_new_candidate",
        "mark_deprecated_candidate",
        "manual_review",
        "blocked",
    ]
    apply_mode_keys = ["manual_only", "safe_auto_candidate", "blocked"]
    summary = {
        "plan_status": plan_status,
        "impact_entries_total": len(items),
        "plan_items_total": len(items),
        "actions": {key: sum(1 for item in items if item.action == key) for key in action_keys},
        "apply_modes": {key: sum(1 for item in items if item.apply_mode == key) for key in apply_mode_keys},
        "safe_auto_candidates_count": sum(1 for item in items if item.apply_mode == "safe_auto_candidate"),
        "manual_only_count": sum(1 for item in items if item.apply_mode == "manual_only"),
        "blocked_items_count": sum(1 for item in items if item.apply_mode == "blocked"),
        "requires_manual_review_count": sum(1 for item in items if item.requires_manual_review),
        "warnings": [],
        "blocking_reasons": blocking_reasons or [],
    }
    plan = TestCaseUpdatePlan(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        impact_report_path=str(root / "impact-report.old-v1-to-new-v1.json"),
        test_cases_dir=str(tc_dir),
        created_at_utc="2026-07-04T00:00:00Z",
        created_by_tool="tests",
        plan_items=items,
        summary=summary,
        warnings=[],
        blocking_reasons=blocking_reasons or [],
    )
    plan_path, summary_path, _markdown_path = write_test_case_update_plan(plan, root)
    return plan_path, summary_path


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    unittest.main()
