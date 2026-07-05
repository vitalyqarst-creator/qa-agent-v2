from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    ManualUpdatePackagesReport,
    TestCaseUpdatePlan,
    UpdatePlanItem,
    build_manual_update_packages,
    load_manual_update_packages,
    write_manual_update_packages,
)


class ManualUpdatePackagesTests(unittest.TestCase):
    def test_update_existing_items_grouped_by_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(root, [make_item("PLAN-000001", "update_existing", tc_path)])

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual("pass-with-warnings", report.summary["package_status"])
            self.assertEqual(1, report.summary["packages_total"])
            package = report.packages[0]
            self.assertEqual("update_existing", package.package_type)
            self.assertEqual(str(tc_path), package.file_path)
            self.assertEqual(["TC-001"], package.test_case_ids)
            self.assertIn("review steps", package.writer_allowed_operations)

    def test_multiple_tc_in_same_file_become_one_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(
                root,
                [
                    make_item("PLAN-000001", "update_existing", tc_path, test_case_id="TC-001"),
                    make_item("PLAN-000002", "update_existing", tc_path, test_case_id="TC-002"),
                ],
            )

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual(1, len(report.packages))
            self.assertEqual(["TC-001", "TC-002"], report.packages[0].test_case_ids)
            self.assertEqual(2, report.summary["test_cases_affected_count"])

    def test_create_new_candidate_without_file_path_becomes_candidate_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, _tc_path = setup_root(temp_dir)
            plan_path = write_plan(
                root,
                [make_item("PLAN-000001", "create_new_candidate", None, test_case_id=None)],
            )

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual(1, len(report.packages))
            package = report.packages[0]
            self.assertEqual("create_new_candidate", package.package_type)
            self.assertIsNone(package.file_path)
            self.assertEqual([], package.test_case_ids)
            self.assertIn("propose new TC drafts", package.writer_allowed_operations)
            self.assertIn("do not write into canonical test-case files yet", package.writer_allowed_operations)

    def test_mark_deprecated_candidate_grouped_by_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(
                root,
                [make_item("PLAN-000001", "mark_deprecated_candidate", tc_path)],
            )

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual("mark_deprecated_candidate", report.packages[0].package_type)
            self.assertEqual(str(tc_path), report.packages[0].file_path)
            self.assertIn("propose deprecated marking", report.packages[0].writer_allowed_operations)
            self.assertIn("do not edit files yet", report.packages[0].writer_allowed_operations)

    def test_mixed_actions_in_same_file_create_mixed_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(
                root,
                [
                    make_item("PLAN-000001", "update_existing", tc_path, test_case_id="TC-001"),
                    make_item("PLAN-000002", "mark_deprecated_candidate", tc_path, test_case_id="TC-002"),
                ],
            )

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual(1, len(report.packages))
            self.assertEqual("mixed", report.packages[0].package_type)
            self.assertEqual(["mark_deprecated_candidate", "update_existing"], report.packages[0].actions)
            self.assertEqual(1, report.summary["mixed_package_count"])

    def test_keep_and_safe_auto_items_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(
                root,
                [
                    make_item("PLAN-000001", "keep", tc_path, apply_mode="safe_auto_candidate"),
                    make_item("PLAN-000002", "update_existing", tc_path),
                ],
            )

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual(1, len(report.packages))
            self.assertEqual(["PLAN-000002"], report.packages[0].plan_item_ids)

    def test_only_keep_items_block_package_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(
                root,
                [make_item("PLAN-000001", "keep", tc_path, apply_mode="safe_auto_candidate")],
                plan_status="pass",
            )

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual("blocked", report.summary["package_status"])
            self.assertEqual([], report.packages)
            self.assertTrue(any("no manual update items" in reason for reason in report.blocking_reasons))

    def test_blocked_update_plan_blocks_package_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(
                root,
                [make_item("PLAN-000001", "update_existing", tc_path)],
                plan_status="blocked",
                blocking_reasons=["upstream blocked"],
            )

            report = build_manual_update_packages(update_plan_path=plan_path)

            self.assertEqual("blocked", report.summary["package_status"])
            self.assertEqual([], report.packages)
            self.assertTrue(any("update plan summary is blocked" in reason for reason in report.blocking_reasons))

    def test_json_and_markdown_reports_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            plan_path = write_plan(root, [make_item("PLAN-000001", "update_existing", tc_path)])
            report = build_manual_update_packages(update_plan_path=plan_path)

            report_path, summary_path, markdown_path = write_manual_update_packages(report, root)
            loaded = load_manual_update_packages(report_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, ManualUpdatePackagesReport)
            self.assertEqual(1, len(loaded.packages))
            self.assertEqual(1, summary["packages_total"])
            self.assertIn("## Summary", markdown)
            self.assertIn("## Packages by File", markdown)
            self.assertIn("## New TC Candidates", markdown)
            self.assertIn("## Deprecated Candidates", markdown)
            self.assertIn("## Manual Review Packages", markdown)
            self.assertIn("## Do Not Touch Rules", markdown)

    def test_builder_does_not_modify_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_dir, tc_path = setup_root(temp_dir)
            before = tc_path.read_text(encoding="utf-8")
            plan_path = write_plan(root, [make_item("PLAN-000001", "update_existing", tc_path)])

            report = build_manual_update_packages(update_plan_path=plan_path)
            write_manual_update_packages(report, root)

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_root(temp_dir: str) -> tuple[Path, Path, Path]:
    root = Path(temp_dir)
    tc_dir = root / "fts" / "demo-ft" / "test-cases"
    tc_dir.mkdir(parents=True)
    tc_path = tc_dir / "scope.md"
    tc_path.write_text(
        "## TC-001\n**Traceability:** REQ-DEMO-OLD, BSR 1\n",
        encoding="utf-8",
        newline="\n",
    )
    return root, tc_dir, tc_path


def make_item(
    plan_item_id: str,
    action: str,
    file_path: Path | None,
    *,
    test_case_id: str | None = "TC-001",
    apply_mode: str = "manual_only",
) -> UpdatePlanItem:
    return UpdatePlanItem(
        plan_item_id=plan_item_id,
        impact_id=f"IMP-{plan_item_id[-6:]}",
        change_id=f"CHG-{plan_item_id[-6:]}",
        test_case_id=test_case_id,
        file_path=str(file_path) if file_path is not None else None,
        action=action,
        apply_mode=apply_mode,
        old_refs=["REQ-DEMO-OLD"],
        new_refs=["REQ-DEMO-NEW"],
        required_changes=["review steps"] if action == "update_existing" else [],
        forbidden_changes=["Do not rewrite entire file"],
        rationale=[f"impact action={action}"],
        requires_manual_review=apply_mode == "manual_only",
        warnings=[],
    )


def write_plan(
    root: Path,
    items: list[UpdatePlanItem],
    *,
    plan_status: str = "pass-with-warnings",
    blocking_reasons: list[str] | None = None,
) -> Path:
    plan_path = root / "test-case-update-plan.old-v1-to-new-v1.json"
    summary = {
        "plan_status": plan_status,
        "plan_items_total": len(items),
        "warnings": [],
        "blocking_reasons": blocking_reasons or [],
    }
    plan = TestCaseUpdatePlan(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        impact_report_path=str(root / "impact-report.old-v1-to-new-v1.json"),
        test_cases_dir=str(root / "fts" / "demo-ft" / "test-cases"),
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        plan_items=items,
        summary=summary,
        warnings=[],
        blocking_reasons=blocking_reasons or [],
    )
    plan_path.write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return plan_path


if __name__ == "__main__":
    unittest.main()
