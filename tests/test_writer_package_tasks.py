from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    ManualUpdatePackage,
    ManualUpdatePackagesReport,
    WriterPackageTasksReport,
    build_writer_package_tasks,
    load_writer_package_tasks,
    write_writer_package_tasks,
)


class WriterPackageTasksTests(unittest.TestCase):
    def test_one_task_per_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_path = setup_root(temp_dir)
            packages_path = write_packages_report(
                root,
                [
                    make_package("WPKG-000001", file_path="fts/demo-ft/test-cases/scope.md"),
                    make_package("WPKG-000002", package_type="create_new_candidate", file_path=None, test_case_ids=[]),
                ],
            )

            report = build_writer_package_tasks(manual_update_packages_path=packages_path)

            self.assertEqual("pass", report.summary["task_status"])
            self.assertEqual(2, len(report.tasks))
            self.assertEqual(2, report.summary["tasks_total"])

    def test_file_bound_package_includes_file_and_tc_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_path = setup_root(temp_dir)
            packages_path = write_packages_report(
                root,
                [
                    make_package(
                        "WPKG-000001",
                        file_path="fts/demo-ft/test-cases/scope.md",
                        test_case_ids=["TC-001", "TC-002"],
                    )
                ],
            )

            report = build_writer_package_tasks(manual_update_packages_path=packages_path)
            task = report.tasks[0]

            self.assertEqual("fts/demo-ft/test-cases/scope.md", task.file_path)
            self.assertEqual(["TC-001", "TC-002"], task.affected_test_case_ids)
            self.assertEqual("Update only listed TC, do not rewrite entire file.", task.scope_instruction)
            self.assertIn("Do not touch unlisted TC", task.forbidden_operations)
            self.assertIn("Do not rewrite entire file", task.forbidden_operations)

    def test_create_new_candidate_proposes_drafts_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_path = setup_root(temp_dir)
            packages_path = write_packages_report(
                root,
                [
                    make_package(
                        "WPKG-000001",
                        package_type="create_new_candidate",
                        actions=["create_new_candidate"],
                        file_path=None,
                        test_case_ids=[],
                    )
                ],
            )

            report = build_writer_package_tasks(manual_update_packages_path=packages_path)
            task = report.tasks[0]

            self.assertEqual("Propose drafts only, do not write canonical files.", task.scope_instruction)
            self.assertIn("Do not write canonical files", task.forbidden_operations)
            self.assertIn("Do not create new TC files in this stage", task.forbidden_operations)

    def test_unlinked_package_forbids_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_path = setup_root(temp_dir)
            packages_path = write_packages_report(
                root,
                [
                    make_package(
                        "WPKG-000001",
                        package_type="manual_review",
                        actions=["manual_review"],
                        file_path=None,
                        test_case_ids=[],
                    )
                ],
            )

            report = build_writer_package_tasks(manual_update_packages_path=packages_path)
            task = report.tasks[0]

            self.assertEqual("Analyze and classify, do not edit files.", task.scope_instruction)
            self.assertIn("Do not edit files", task.forbidden_operations)

    def test_large_package_is_marked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_path = setup_root(temp_dir)
            packages_path = write_packages_report(
                root,
                [
                    make_package(
                        "WPKG-000001",
                        file_path="fts/demo-ft/test-cases/scope.md",
                        plan_items_count=51,
                    )
                ],
            )

            report = build_writer_package_tasks(manual_update_packages_path=packages_path)
            task = report.tasks[0]

            self.assertTrue(task.large_package)
            self.assertIn("Recommend splitting before writer execution.", task.execution_notes)
            self.assertEqual(1, report.summary["large_package_tasks"])
            self.assertEqual(51, report.summary["largest_task_plan_items_count"])

    def test_json_and_markdown_tasks_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _tc_path = setup_root(temp_dir)
            packages_path = write_packages_report(
                root,
                [make_package("WPKG-000001", file_path="fts/demo-ft/test-cases/scope.md")],
            )
            report = build_writer_package_tasks(manual_update_packages_path=packages_path)

            report_path, summary_path, task_paths = write_writer_package_tasks(report, root)
            loaded = load_writer_package_tasks(report_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            task_markdown = task_paths[0].read_text(encoding="utf-8")

            self.assertIsInstance(loaded, WriterPackageTasksReport)
            self.assertEqual(1, len(loaded.tasks))
            self.assertEqual(1, summary["tasks_total"])
            self.assertEqual("writer-package-task-WPKG-000001.md", task_paths[0].name)
            self.assertIn("## Scope", task_markdown)
            self.assertIn("## Instruction", task_markdown)
            self.assertIn("Update only listed TC, do not rewrite entire file.", task_markdown)

    def test_builder_does_not_modify_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_path = setup_root(temp_dir)
            before = tc_path.read_text(encoding="utf-8")
            packages_path = write_packages_report(
                root,
                [make_package("WPKG-000001", file_path=str(tc_path))],
            )

            report = build_writer_package_tasks(manual_update_packages_path=packages_path)
            write_writer_package_tasks(report, root)

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_root(temp_dir: str) -> tuple[Path, Path]:
    root = Path(temp_dir)
    tc_dir = root / "fts" / "demo-ft" / "test-cases"
    tc_dir.mkdir(parents=True)
    tc_path = tc_dir / "scope.md"
    tc_path.write_text(
        "## TC-001\n**Traceability:** REQ-DEMO-OLD\n",
        encoding="utf-8",
        newline="\n",
    )
    return root, tc_path


def make_package(
    package_id: str,
    *,
    package_type: str = "update_existing",
    file_path: str | None,
    test_case_ids: list[str] | None = None,
    actions: list[str] | None = None,
    plan_items_count: int = 1,
) -> ManualUpdatePackage:
    plan_item_ids = [f"PLAN-{index:06d}" for index in range(1, plan_items_count + 1)]
    return ManualUpdatePackage(
        package_id=package_id,
        package_type=package_type,
        file_path=file_path,
        test_case_ids=test_case_ids if test_case_ids is not None else ["TC-001"],
        plan_item_ids=plan_item_ids,
        impact_ids=["IMP-000001"],
        change_ids=["CHG-000001"],
        actions=actions if actions is not None else [package_type],
        plan_items_count=plan_items_count,
        priority="high",
        requires_manual_review=True,
        writer_allowed_operations=["update listed TC only"],
        writer_forbidden_operations=["Do not touch unlisted TC", "Do not rewrite entire file"],
        rationale=["test package rationale"],
        warnings=[],
    )


def write_packages_report(
    root: Path,
    packages: list[ManualUpdatePackage],
    *,
    package_status: str = "pass-with-warnings",
) -> Path:
    packages_path = root / "manual-update-packages.old-v1-to-new-v1.json"
    summary = {
        "package_status": package_status,
        "packages_total": len(packages),
        "warnings": [],
        "blocking_reasons": [],
    }
    report = ManualUpdatePackagesReport(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        update_plan_path=str(root / "test-case-update-plan.old-v1-to-new-v1.json"),
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        packages=packages,
        summary=summary,
        warnings=[],
        blocking_reasons=[],
    )
    packages_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return packages_path


if __name__ == "__main__":
    unittest.main()
