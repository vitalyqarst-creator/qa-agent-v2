from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    ImpactEntry,
    ImpactReport,
    RequirementsDiff,
    RequirementsDiffEntry,
    TestCaseLink,
    TestCaseUpdatePlan,
    TraceabilityMismatchDiagnosticsReport,
    UpdatePlanItem,
    WriterDryRunProposal,
    WriterPackageTask,
    WriterPackageTasksReport,
    build_traceability_mismatch_diagnostics,
    load_traceability_mismatch_diagnostics,
    write_traceability_mismatch_diagnostics,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


class TraceabilityMismatchDiagnosticsTests(unittest.TestCase):
    def test_bsr_only_traceability_with_req_old_ref_is_generated_req_uid_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_line="**Traceability:** BSR 1")

            report = build_report(ctx)

            self.assertEqual(1, report.summary["mismatches_total"])
            self.assertIn(
                report.mismatches[0].mismatch_type,
                {"tc_has_legacy_refs_only", "req_uid_generated_after_tc_creation"},
            )
            self.assertEqual(["REQ-OLD"], report.mismatches[0].missing_old_refs)
            self.assertEqual(["BSR 1"], report.mismatches[0].parsed_refs_from_traceability_line)

    def test_traceability_line_with_no_refs_is_classified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_line="**Traceability:** none")

            report = build_report(ctx)

            self.assertEqual(1, report.summary["mismatches_total"])
            self.assertEqual("tc_has_no_traceability_refs", report.mismatches[0].mismatch_type)
            self.assertEqual([], report.mismatches[0].parsed_refs_from_traceability_line)

    def test_old_ref_present_has_no_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_line="**Traceability:** REQ-OLD; BSR 1")

            report = build_report(ctx)

            self.assertEqual("pass", report.summary["diagnostic_status"])
            self.assertEqual(0, report.summary["mismatches_total"])
            self.assertEqual([], report.mismatches)

    def test_missing_traceability_line_is_warning_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_line=None)

            report = build_report(ctx)

            self.assertEqual("pass-with-warnings", report.summary["diagnostic_status"])
            self.assertEqual(1, report.summary["mismatches_total"])
            self.assertIsNone(report.mismatches[0].current_traceability_line)

    def test_json_and_markdown_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_line="**Traceability:** BSR 1")
            report = build_report(ctx)

            json_path, markdown_path = write_traceability_mismatch_diagnostics(report, ctx.root)
            loaded = load_traceability_mismatch_diagnostics(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, TraceabilityMismatchDiagnosticsReport)
            self.assertEqual(1, loaded.summary["mismatches_total"])
            self.assertIn("Traceability Mismatch Diagnostics", markdown)
            self.assertIn("Recommendations", markdown)

    def test_canonical_test_case_file_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir, traceability_line="**Traceability:** BSR 1")
            before = compute_file_sha256(ctx.tc_path)

            report = build_report(ctx)
            write_traceability_mismatch_diagnostics(report, ctx.root)

            self.assertEqual(before, compute_file_sha256(ctx.tc_path))


class Context:
    def __init__(
        self,
        *,
        root: Path,
        tc_dir: Path,
        tc_path: Path,
        proposal_path: Path,
        tasks_path: Path,
        manual_packages_path: Path,
        update_plan_path: Path,
        impact_report_path: Path,
        diff_path: Path,
    ) -> None:
        self.root = root
        self.tc_dir = tc_dir
        self.tc_path = tc_path
        self.proposal_path = proposal_path
        self.tasks_path = tasks_path
        self.manual_packages_path = manual_packages_path
        self.update_plan_path = update_plan_path
        self.impact_report_path = impact_report_path
        self.diff_path = diff_path


def setup_context(temp_dir: str, *, traceability_line: str | None) -> Context:
    root = Path(temp_dir)
    tc_dir = root / "fts" / "demo-ft" / "test-cases"
    tc_dir.mkdir(parents=True)
    tc_path = tc_dir / "scope.md"
    traceability = f"{traceability_line}\n\n" if traceability_line is not None else ""
    tc_path.write_text(
        "## TC-001\n"
        "\n"
        f"{traceability}"
        "### Steps\n"
        "\n"
        "1. Do one thing.\n",
        encoding="utf-8",
        newline="\n",
    )
    tasks_path = write_tasks(root, tc_path)
    update_plan_path = write_update_plan(root, tc_dir, tc_path)
    impact_report_path = write_impact_report(root, tc_dir)
    diff_path = write_diff(root)
    proposal_path = write_proposal(root, tc_path)
    manual_packages_path = root / "manual-update-packages.old-v1-to-new-v1.json"
    manual_packages_path.write_text('{"packages": []}\n', encoding="utf-8", newline="\n")
    return Context(
        root=root,
        tc_dir=tc_dir,
        tc_path=tc_path,
        proposal_path=proposal_path,
        tasks_path=tasks_path,
        manual_packages_path=manual_packages_path,
        update_plan_path=update_plan_path,
        impact_report_path=impact_report_path,
        diff_path=diff_path,
    )


def build_report(ctx: Context) -> TraceabilityMismatchDiagnosticsReport:
    return build_traceability_mismatch_diagnostics(
        proposal_paths=[ctx.proposal_path],
        writer_package_tasks_path=ctx.tasks_path,
        manual_update_packages_path=ctx.manual_packages_path,
        update_plan_path=ctx.update_plan_path,
        impact_report_path=ctx.impact_report_path,
        requirements_diff_path=ctx.diff_path,
        test_cases_dir=ctx.tc_dir,
        workspace_root=ctx.root,
    )


def write_tasks(root: Path, tc_path: Path) -> Path:
    path = root / "writer-package-tasks.old-v1-to-new-v1.json"
    task = WriterPackageTask(
        package_id="WPKG-000003",
        task_file_name="writer-package-task-WPKG-000003.md",
        package_type="manual_review",
        file_path=str(tc_path),
        affected_test_case_ids=["TC-001"],
        plan_item_ids=["PLAN-000001"],
        impact_ids=["IMP-000001"],
        change_ids=["CHG-000001"],
        actions=["traceability_update_only"],
        plan_items_count=1,
        large_package=False,
        safe_to_try_first=True,
        allowed_operations=["update listed TC only"],
        forbidden_operations=["Do not touch unlisted TC"],
        scope_instruction="Update only listed TC, do not rewrite entire file.",
        execution_notes=[],
        warnings=[],
    )
    report = WriterPackageTasksReport(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        manual_update_packages_path=str(root / "manual-update-packages.old-v1-to-new-v1.json"),
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        tasks=[task],
        summary={"task_status": "pass", "tasks_total": 1},
        warnings=[],
        blocking_reasons=[],
    )
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_update_plan(root: Path, tc_dir: Path, tc_path: Path) -> Path:
    path = root / "test-case-update-plan.old-v1-to-new-v1.json"
    item = UpdatePlanItem(
        plan_item_id="PLAN-000001",
        impact_id="IMP-000001",
        change_id="CHG-000001",
        test_case_id="TC-001",
        file_path=str(tc_path),
        action="traceability_update_only",
        apply_mode="manual_only",
        old_refs=["REQ-OLD", "BSR 1"],
        new_refs=["REQ-NEW", "BSR 1"],
        required_changes=["update traceability refs only"],
        forbidden_changes=["Do not change steps"],
        rationale=[],
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
        summary={"plan_status": "pass", "plan_items_total": 1},
        warnings=[],
        blocking_reasons=[],
    )
    path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_impact_report(root: Path, tc_dir: Path) -> Path:
    path = root / "impact-report.old-v1-to-new-v1.json"
    link = TestCaseLink(
        test_case_id="TC-001",
        file_path=str(tc_dir / "scope.md"),
        title="Demo",
        linked_req_uids=[],
        linked_atom_ids=[],
        linked_source_req_ids=["BSR 1"],
        raw_traceability="BSR 1",
        parse_warnings=[],
    )
    entry = ImpactEntry(
        impact_id="IMP-000001",
        change_id="CHG-000001",
        change_type="source_anchor_changed",
        old_req_uid="REQ-OLD",
        new_req_uid="REQ-NEW",
        old_source_req_id="BSR 1",
        new_source_req_id="BSR 1",
        affected_test_cases=[link],
        action="traceability_update_only",
        priority="low",
        rationale=[],
        requires_manual_review=True,
        warnings=[],
    )
    report = ImpactReport(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        requirements_diff_path=str(root / "requirements-diff.old-v1-to-new-v1.json"),
        test_cases_dir=str(tc_dir),
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        impact_entries=[entry],
        summary={"impact_status": "pass"},
        warnings=[],
        blocking_reasons=[],
    )
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_diff(root: Path) -> Path:
    path = root / "requirements-diff.old-v1-to-new-v1.json"
    entry = RequirementsDiffEntry(
        change_id="CHG-000001",
        change_type="source_anchor_changed",
        old_req_uid="REQ-OLD",
        new_req_uid="REQ-NEW",
        old_atom_id=None,
        new_atom_id=None,
        old_source_req_id="BSR 1",
        new_source_req_id="BSR 1",
        old_requirement_type="validation",
        new_requirement_type="validation",
        old_status="active",
        new_status="active",
        old_normalized_text="old",
        new_normalized_text="new",
        old_semantic_fingerprint=None,
        new_semantic_fingerprint=None,
        old_text_hash=None,
        new_text_hash=None,
        old_source_anchors=[],
        new_source_anchors=[],
        similarity_score=1.0,
        confidence="high",
        requires_manual_review=False,
        reasons=[],
        warnings=[],
    )
    report = RequirementsDiff(
        old_registry_path=str(root / "old.jsonl"),
        new_registry_path=str(root / "new.jsonl"),
        old_source_version="old-v1",
        new_source_version="new-v1",
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        entries=[entry],
        summary={"diff_status": "pass"},
        warnings=[],
        blocking_reasons=[],
    )
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_proposal(root: Path, tc_path: Path) -> Path:
    path = root / "writer-dry-run-proposal-WPKG-000003.json"
    proposal = WriterDryRunProposal(
        package_id="WPKG-000003",
        file_path=str(tc_path),
        affected_test_case_ids=["TC-001"],
        source_plan_item_ids=["PLAN-000001"],
        source_impact_ids=["IMP-000001"],
        source_change_ids=["CHG-000001"],
        proposal_status="pass-with-warnings",
        risk_level="medium",
        manual_review_required=True,
        proposed_changes=[],
        rationale=[],
        missing_information=["old ref not found"],
        original_tc_blocks={},
        proposed_tc_blocks={},
        unified_diff_preview="",
        sha256_before=None,
        sha256_after=None,
        input_paths={},
        created_at_utc="2026-07-05T00:00:00Z",
        created_by_tool="tests",
        warnings=[],
        blocking_reasons=[],
    )
    path.write_text(json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    unittest.main()
