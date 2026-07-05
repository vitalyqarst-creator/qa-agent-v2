from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    ImpactEntry,
    ImpactReport,
    TestCaseLink,
    build_test_case_update_plan,
    load_test_case_update_plan,
    write_test_case_update_plan,
)


class TestCaseUpdatePlanTests(unittest.TestCase):
    def test_no_action_maps_to_keep(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [make_impact_entry("no_action", [make_link(tc_path)])],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual("keep", plan.plan_items[0].action)
            self.assertEqual("safe_auto_candidate", plan.plan_items[0].apply_mode)
            self.assertEqual([], plan.plan_items[0].required_changes)
            self.assertEqual(
                ["Do not rewrite steps", "Do not rewrite expected result"],
                plan.plan_items[0].forbidden_changes,
            )

    def test_unlinked_no_action_entries_are_ignored_without_plan_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, _tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry("no_action", [], impact_id="IMP-000001"),
                    make_impact_entry("no_action", [], impact_id="IMP-000002", change_id="CHG-000002"),
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertNotEqual("blocked", plan.summary["plan_status"])
            self.assertEqual([], plan.plan_items)
            self.assertEqual(0, plan.summary["plan_items_total"])
            self.assertEqual(2, plan.summary["ignored_unlinked_no_action_count"])
            self.assertEqual(
                ["IMP-000001", "IMP-000002"],
                plan.summary["ignored_unlinked_no_action_impact_ids"],
            )

    def test_no_action_with_linked_test_case_still_creates_keep_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [make_impact_entry("no_action", [make_link(tc_path)], impact_id="IMP-000001")],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual(1, len(plan.plan_items))
            self.assertEqual("keep", plan.plan_items[0].action)
            self.assertEqual("TC-001", plan.plan_items[0].test_case_id)
            self.assertEqual(0, plan.summary["ignored_unlinked_no_action_count"])

    def test_multiple_create_new_candidates_without_tc_targets_do_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, _tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry("create_new", [], impact_id="IMP-000001", change_id="CHG-000001"),
                    make_impact_entry("create_new", [], impact_id="IMP-000002", change_id="CHG-000002"),
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertNotEqual("blocked", plan.summary["plan_status"])
            self.assertEqual(2, plan.summary["plan_items_total"])
            self.assertTrue(all(item.action == "create_new_candidate" for item in plan.plan_items))
            self.assertTrue(all(item.test_case_id is None and item.file_path is None for item in plan.plan_items))

    def test_traceability_update_without_parse_warnings_is_safe_auto_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [make_impact_entry("traceability_update_only", [make_link(tc_path)])],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual("traceability_update_only", plan.plan_items[0].action)
            self.assertEqual("safe_auto_candidate", plan.plan_items[0].apply_mode)
            self.assertFalse(plan.plan_items[0].requires_manual_review)
            self.assertEqual(["update traceability refs only"], plan.plan_items[0].required_changes)

    def test_traceability_update_with_parse_warnings_is_manual_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry(
                        "traceability_update_only",
                        [make_link(tc_path, parse_warnings=["legacy TC heading level detected"])],
                    )
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual("manual_only", plan.plan_items[0].apply_mode)
            self.assertTrue(plan.plan_items[0].requires_manual_review)
            self.assertIn("legacy TC heading level detected", plan.plan_items[0].warnings)

    def test_update_existing_is_manual_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry(
                        "update_existing",
                        [make_link(tc_path)],
                        requires_manual_review=True,
                    )
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual("update_existing", plan.plan_items[0].action)
            self.assertEqual("manual_only", plan.plan_items[0].apply_mode)
            self.assertTrue(plan.plan_items[0].requires_manual_review)
            self.assertEqual(
                ["review steps", "review expected result", "update traceability"],
                plan.plan_items[0].required_changes,
            )

    def test_create_new_is_candidate_and_does_not_write_tc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, _tc_path = setup_root(temp_dir)
            before_files = sorted(path.name for path in tc_dir.glob("*"))
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [make_impact_entry("create_new", [], requires_manual_review=True)],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)
            write_test_case_update_plan(plan, root)

            after_files = sorted(path.name for path in tc_dir.glob("*"))
            self.assertEqual(before_files, after_files)
            self.assertEqual("create_new_candidate", plan.plan_items[0].action)
            self.assertIsNone(plan.plan_items[0].test_case_id)
            self.assertIsNone(plan.plan_items[0].file_path)
            self.assertIn("Do not create TC in Stage 6A", plan.plan_items[0].forbidden_changes)

    def test_mark_deprecated_is_candidate_and_does_not_edit_tc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry(
                        "mark_deprecated",
                        [make_link(tc_path)],
                        requires_manual_review=True,
                    )
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)
            write_test_case_update_plan(plan, root)

            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))
            self.assertEqual("mark_deprecated_candidate", plan.plan_items[0].action)
            self.assertEqual("manual_only", plan.plan_items[0].apply_mode)
            self.assertIn("Do not edit TC in Stage 6A", plan.plan_items[0].forbidden_changes)

    def test_manual_review_stays_manual_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry(
                        "manual_review",
                        [make_link(tc_path)],
                        requires_manual_review=True,
                    )
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual("manual_review", plan.plan_items[0].action)
            self.assertEqual("manual_only", plan.plan_items[0].apply_mode)

    def test_blocked_impact_report_blocks_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, summary_path = write_impact(
                root,
                tc_dir,
                [make_impact_entry("update_existing", [make_link(tc_path)])],
                impact_status="blocked",
                blocking_reasons=["duplicate TC ids detected: TC-001"],
            )

            plan = build_test_case_update_plan(
                impact_report_path=impact_path,
                impact_summary_path=summary_path,
                test_cases_dir=tc_dir,
            )

            self.assertEqual("blocked", plan.summary["plan_status"])
            self.assertEqual([], plan.plan_items)
            self.assertTrue(any("duplicate TC ids" in reason for reason in plan.blocking_reasons))

    def test_missing_linked_file_blocks_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, _tc_path = setup_root(temp_dir)
            missing_path = tc_dir / "missing.md"
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [make_impact_entry("update_existing", [make_link(missing_path)])],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual("blocked", plan.summary["plan_status"])
            self.assertEqual([], plan.plan_items)
            self.assertTrue(any("affected test-case file is missing" in reason for reason in plan.blocking_reasons))

    def test_json_and_markdown_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [make_impact_entry("traceability_update_only", [make_link(tc_path)])],
            )
            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            plan_path, summary_path, markdown_path = write_test_case_update_plan(plan, root)
            loaded = load_test_case_update_plan(plan_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertTrue(plan_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertEqual(1, len(loaded.plan_items))
            self.assertEqual("safe_auto_candidate", loaded.plan_items[0].apply_mode)
            self.assertEqual(1, summary["safe_auto_candidates_count"])
            self.assertIn("## Summary", markdown)
            self.assertIn("## Safe Auto Candidates", markdown)
            self.assertIn("## Manual Updates Required", markdown)
            self.assertIn("## New TC Candidates", markdown)
            self.assertIn("## Deprecated Candidates", markdown)
            self.assertIn("## Traceability-only Updates", markdown)
            self.assertIn("## Blocked Items", markdown)
            self.assertIn("## Do Not Touch", markdown)

    def test_builder_does_not_modify_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            original = tc_path.read_text(encoding="utf-8")
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry(
                        "update_existing",
                        [make_link(tc_path)],
                        requires_manual_review=True,
                    )
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)
            write_test_case_update_plan(plan, root)

            self.assertEqual(original, tc_path.read_text(encoding="utf-8"))

    def test_inconsistent_duplicate_plan_items_block_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir, tc_path = setup_root(temp_dir)
            impact_path, _summary_path = write_impact(
                root,
                tc_dir,
                [
                    make_impact_entry("traceability_update_only", [make_link(tc_path)], impact_id="IMP-000001"),
                    make_impact_entry(
                        "traceability_update_only",
                        [make_link(tc_path)],
                        impact_id="IMP-000002",
                        requires_manual_review=True,
                    ),
                ],
            )

            plan = build_test_case_update_plan(impact_report_path=impact_path, test_cases_dir=tc_dir)

            self.assertEqual("blocked", plan.summary["plan_status"])
            self.assertEqual([], plan.plan_items)
            self.assertTrue(any("inconsistent duplicate plan items" in reason for reason in plan.blocking_reasons))


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


def make_link(
    file_path: Path,
    *,
    test_case_id: str = "TC-001",
    parse_warnings: list[str] | None = None,
) -> TestCaseLink:
    return TestCaseLink(
        test_case_id=test_case_id,
        file_path=str(file_path),
        title="Demo TC",
        linked_req_uids=["REQ-DEMO-OLD"],
        linked_atom_ids=["ATOM-000001"],
        linked_source_req_ids=["BSR 1"],
        raw_traceability="REQ-DEMO-OLD, BSR 1",
        parse_warnings=parse_warnings or [],
    )


def make_impact_entry(
    action: str,
    affected_test_cases: list[TestCaseLink],
    *,
    impact_id: str = "IMP-000001",
    change_id: str = "CHG-000001",
    requires_manual_review: bool = False,
) -> ImpactEntry:
    return ImpactEntry(
        impact_id=impact_id,
        change_id=change_id,
        change_type="renumbered" if action == "traceability_update_only" else "behavior_modified",
        old_req_uid="REQ-DEMO-OLD",
        new_req_uid="REQ-DEMO-NEW",
        old_source_req_id="BSR 1",
        new_source_req_id="BSR 2",
        affected_test_cases=affected_test_cases,
        action=action,
        priority="medium",
        rationale=[f"test impact action {action}"],
        requires_manual_review=requires_manual_review,
        warnings=[],
    )


def write_impact(
    root: Path,
    tc_dir: Path,
    entries: list[ImpactEntry],
    *,
    impact_status: str = "pass",
    blocking_reasons: list[str] | None = None,
) -> tuple[Path, Path]:
    impact_path = root / "impact-report.old-v1-to-new-v1.json"
    summary_path = root / "impact-report-summary.old-v1-to-new-v1.json"
    summary = {
        "impact_status": impact_status,
        "impact_entries_total": len(entries),
        "warnings": [],
        "blocking_reasons": blocking_reasons or [],
    }
    report = ImpactReport(
        ft_slug="demo-ft",
        old_source_version="old-v1",
        new_source_version="new-v1",
        requirements_diff_path=str(root / "requirements-diff.old-v1-to-new-v1.json"),
        test_cases_dir=str(tc_dir),
        created_at_utc="2026-07-04T00:00:00Z",
        created_by_tool="tests",
        impact_entries=entries,
        summary=summary,
        warnings=[],
        blocking_reasons=blocking_reasons or [],
    )
    impact_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return impact_path, summary_path


if __name__ == "__main__":
    unittest.main()
