from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    TestCaseUpdatePlan,
    UpdatePlanItem,
    WriterPackageTask,
    WriterPackageTasksReport,
    WriterDryRunProposal,
    build_writer_dry_run_proposal,
    load_writer_dry_run_proposal,
    write_writer_dry_run_proposal,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


class WriterDryRunProposalTests(unittest.TestCase):
    def test_file_bound_small_task_creates_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("pass", proposal.proposal_status)
            self.assertEqual("low", proposal.risk_level)
            self.assertEqual(["TC-001"], proposal.affected_test_case_ids)
            self.assertEqual(1, len(proposal.proposed_changes))
            self.assertIn("REQ-NEW", proposal.proposed_tc_blocks["TC-001"])
            self.assertIn("REQ-OLD", proposal.original_tc_blocks["TC-001"])

    def test_unlinked_task_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, _tc_path = setup_root(temp_dir)
            tasks_path = write_tasks_report(
                root,
                make_task(None, affected_test_case_ids=[]),
            )

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("unlinked" in reason for reason in proposal.blocking_reasons))

    def test_large_package_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tasks_path = write_tasks_report(
                root,
                make_task(tc_path, large_package=True, safe_to_try_first=False, plan_items_count=51),
            )

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("large package" in reason for reason in proposal.blocking_reasons))

    def test_proposal_reads_only_listed_tc_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual(["TC-001"], list(proposal.original_tc_blocks))
            self.assertEqual(["TC-001"], list(proposal.proposed_tc_blocks))
            self.assertNotIn("TC-002", json.dumps(proposal.to_dict(), ensure_ascii=False))

    def test_canonical_test_case_file_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            before = compute_file_sha256(tc_path)
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )
            write_writer_dry_run_proposal(proposal, root)

            self.assertEqual(before, compute_file_sha256(tc_path))
            self.assertEqual(before, proposal.sha256_before)
            self.assertEqual(before, proposal.sha256_after)

    def test_patch_preview_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)
            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            json_path, markdown_path, patch_path = write_writer_dry_run_proposal(proposal, root)
            loaded = load_writer_dry_run_proposal(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")
            patch = patch_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, WriterDryRunProposal)
            self.assertIn("REQ-OLD", patch)
            self.assertIn("REQ-NEW", patch)
            self.assertIn("## Unified Diff Preview", markdown)

    def test_blocks_if_listed_tc_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tasks_path = write_tasks_report(
                root,
                make_task(tc_path, affected_test_case_ids=["TC-MISSING"]),
            )
            plan_path = write_update_plan(root, tc_dir, tc_path, test_case_id="TC-MISSING")

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("not found" in reason for reason in proposal.blocking_reasons))

    def test_blocks_if_duplicate_tc_block_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tc_path.write_text(
                "## TC-001\n**Traceability:** REQ-OLD\n\n"
                "## TC-001\n**Traceability:** REQ-OLD\n",
                encoding="utf-8",
                newline="\n",
            )
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("blocked", proposal.proposal_status)
            self.assertTrue(any("duplicate" in reason for reason in proposal.blocking_reasons))

    def test_old_ref_in_steps_does_not_create_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tc_path.write_text(
                "## TC-001\n"
                "\n"
                "**Traceability:** REQ-TRACE\n"
                "\n"
                "### Steps\n"
                "\n"
                "1. Use REQ-OLD only in a step.\n",
                encoding="utf-8",
                newline="\n",
            )
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("pass-with-warnings", proposal.proposal_status)
            self.assertEqual([], proposal.proposed_changes)
            self.assertIn("REQ-OLD only in a step", proposal.proposed_tc_blocks["TC-001"])
            self.assertTrue(any("not found in traceability line" in item for item in proposal.missing_information))

    def test_boundary_replacement_does_not_replace_bsr_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tc_path.write_text(
                "## TC-001\n"
                "\n"
                "**Traceability:** BSR 115\n",
                encoding="utf-8",
                newline="\n",
            )
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path, old_refs=["BSR 1"], new_refs=["BSR 2"])

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("pass-with-warnings", proposal.proposal_status)
            self.assertEqual([], proposal.proposed_changes)
            self.assertIn("BSR 115", proposal.proposed_tc_blocks["TC-001"])
            self.assertNotIn("BSR 215", proposal.proposed_tc_blocks["TC-001"])

    def test_no_traceability_line_adds_missing_info(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tc_path.write_text(
                "## TC-001\n"
                "\n"
                "### Steps\n"
                "\n"
                "1. Use REQ-OLD.\n",
                encoding="utf-8",
                newline="\n",
            )
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("pass-with-warnings", proposal.proposal_status)
            self.assertEqual([], proposal.proposed_changes)
            self.assertIn("traceability line not found in TC-001", proposal.missing_information)

    def test_duplicate_traceability_lines_do_not_create_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            tc_path.write_text(
                "## TC-001\n"
                "\n"
                "**Traceability:** REQ-OLD\n"
                "**Traceability:** REQ-OLD\n",
                encoding="utf-8",
                newline="\n",
            )
            tasks_path = write_tasks_report(root, make_task(tc_path))
            plan_path = write_update_plan(root, tc_dir, tc_path)

            proposal = build_writer_dry_run_proposal(
                package_id="WPKG-000003",
                writer_package_tasks_path=tasks_path,
                update_plan_path=plan_path,
                test_cases_dir=tc_dir,
                workspace_root=root,
            )

            self.assertEqual("pass-with-warnings", proposal.proposal_status)
            self.assertEqual([], proposal.proposed_changes)
            self.assertTrue(any("multiple traceability lines" in item for item in proposal.missing_information))


def setup_root(temp_dir: str) -> tuple[Path, Path, Path]:
    root = Path(temp_dir)
    tc_dir = root / "fts" / "demo-ft" / "test-cases"
    tc_dir.mkdir(parents=True)
    tc_path = tc_dir / "scope.md"
    tc_path.write_text(
        "## TC-001\n"
        "\n"
        "**Traceability:** REQ-OLD, BSR 1\n"
        "\n"
        "### Steps\n"
        "\n"
        "1. Do one thing.\n"
        "\n"
        "### Expected Result\n"
        "\n"
        "The result is visible.\n"
        "\n"
        "## TC-002\n"
        "\n"
        "**Traceability:** REQ-OTHER\n",
        encoding="utf-8",
        newline="\n",
    )
    return root, tc_dir, tc_path


def make_task(
    tc_path: Path | None,
    *,
    affected_test_case_ids: list[str] | None = None,
    large_package: bool = False,
    safe_to_try_first: bool = True,
    plan_items_count: int = 1,
) -> WriterPackageTask:
    return WriterPackageTask(
        package_id="WPKG-000003",
        task_file_name="writer-package-task-WPKG-000003.md",
        package_type="manual_review",
        file_path=str(tc_path) if tc_path is not None else None,
        affected_test_case_ids=affected_test_case_ids if affected_test_case_ids is not None else ["TC-001"],
        plan_item_ids=["PLAN-000001"],
        impact_ids=["IMP-000001"],
        change_ids=["CHG-000001"],
        actions=["traceability_update_only"],
        plan_items_count=plan_items_count,
        large_package=large_package,
        safe_to_try_first=safe_to_try_first,
        allowed_operations=["update listed TC only", "review traceability only"],
        forbidden_operations=["Do not touch unlisted TC", "Do not rewrite entire file"],
        scope_instruction="Update only listed TC, do not rewrite entire file.",
        execution_notes=["Limit review and proposed edits to the listed TC IDs."],
        warnings=[],
    )


def write_tasks_report(root: Path, task: WriterPackageTask) -> Path:
    path = root / "writer-package-tasks.old-v1-to-new-v1.json"
    report = WriterPackageTasksReport(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        manual_update_packages_path=str(root / "manual-update-packages.old-v1-to-new-v1.json"),
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        tasks=[task],
        summary={
            "task_status": "pass",
            "tasks_total": 1,
            "warnings": [],
            "blocking_reasons": [],
        },
        warnings=[],
        blocking_reasons=[],
    )
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def write_update_plan(
    root: Path,
    tc_dir: Path,
    tc_path: Path,
    *,
    test_case_id: str = "TC-001",
    old_refs: list[str] | None = None,
    new_refs: list[str] | None = None,
) -> Path:
    path = root / "test-case-update-plan.old-v1-to-new-v1.json"
    item = UpdatePlanItem(
        plan_item_id="PLAN-000001",
        impact_id="IMP-000001",
        change_id="CHG-000001",
        test_case_id=test_case_id,
        file_path=str(tc_path),
        action="traceability_update_only",
        apply_mode="manual_only",
        old_refs=old_refs if old_refs is not None else ["REQ-OLD"],
        new_refs=new_refs if new_refs is not None else ["REQ-NEW"],
        required_changes=["update traceability refs only"],
        forbidden_changes=["Do not change steps"],
        rationale=["behavior unchanged; traceability should be reviewed"],
        requires_manual_review=True,
        warnings=[],
    )
    plan = TestCaseUpdatePlan(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        impact_report_path=str(root / "impact-report.old-v1-to-new-v1.json"),
        test_cases_dir=str(tc_dir),
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        plan_items=[item],
        summary={
            "plan_status": "pass",
            "plan_items_total": 1,
            "warnings": [],
            "blocking_reasons": [],
        },
        warnings=[],
        blocking_reasons=[],
    )
    path.write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    unittest.main()
