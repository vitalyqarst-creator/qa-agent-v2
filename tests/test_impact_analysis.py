from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    RequirementsDiff,
    RequirementsDiffEntry,
    build_impact_report,
    load_impact_report,
    parse_test_cases,
    write_impact_report,
)


class ImpactAnalysisTests(unittest.TestCase):
    def test_parse_canonical_tc_with_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tc_dir = Path(temp_dir) / "test-cases"
            tc_dir.mkdir()
            write_tc(
                tc_dir / "scope.md",
                "## TC-001\n**Название:** Проверка адреса\n**Трассировка:** REQ-DEMO-1, ATOM-000001, BSR 1\n",
            )

            parsed = parse_test_cases(tc_dir)

            self.assertEqual([], parsed.blocking_reasons)
            self.assertEqual(1, len(parsed.test_cases))
            self.assertEqual("TC-001", parsed.test_cases[0].test_case_id)
            self.assertEqual(["REQ-DEMO-1"], parsed.test_cases[0].linked_req_uids)
            self.assertEqual(["ATOM-000001"], parsed.test_cases[0].linked_atom_ids)
            self.assertEqual(["BSR 1"], parsed.test_cases[0].linked_source_req_ids)

    def test_parse_legacy_tc_heading_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tc_dir = Path(temp_dir) / "test-cases"
            tc_dir.mkdir()
            write_tc(tc_dir / "legacy.md", "### TC-LEGACY\n**Трассировка:** BSR 1\n")

            parsed = parse_test_cases(tc_dir)

            self.assertEqual(1, len(parsed.test_cases))
            self.assertIn("legacy TC heading level detected", parsed.test_cases[0].parse_warnings)

    def test_behavior_modified_with_linked_tc_updates_existing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** REQ-DEMO-OLD, BSR 1\n")
            diff_path = write_diff(
                root,
                [make_diff_entry("CHG-000001", "behavior_modified", old_req_uid="REQ-DEMO-OLD", old_source_req_id="BSR 1")],
            )

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("update_existing", report.impact_entries[0].action)
            self.assertEqual("high", report.impact_entries[0].priority)
            self.assertTrue(report.impact_entries[0].requires_manual_review)
            self.assertEqual(["TC-001"], [tc.test_case_id for tc in report.impact_entries[0].affected_test_cases])

    def test_behavior_modified_without_linked_tc_creates_new(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** BSR 99\n")
            diff_path = write_diff(
                root,
                [make_diff_entry("CHG-000001", "behavior_modified", old_req_uid="REQ-DEMO-OLD", old_source_req_id="BSR 1")],
            )

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("create_new", report.impact_entries[0].action)
            self.assertTrue(report.impact_entries[0].requires_manual_review)
            self.assertTrue(any("no linked test cases" in warning for warning in report.impact_entries[0].warnings))

    def test_added_creates_new(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** BSR 99\n")
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "added", new_req_uid="REQ-DEMO-NEW", new_source_req_id="BSR 2")])

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("create_new", report.impact_entries[0].action)
            self.assertEqual("high", report.impact_entries[0].priority)

    def test_deleted_with_linked_tc_marks_deprecated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** REQ-DEMO-OLD\n")
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "deleted", old_req_uid="REQ-DEMO-OLD")])

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("mark_deprecated", report.impact_entries[0].action)
            self.assertTrue(report.impact_entries[0].requires_manual_review)

    def test_unchanged_is_no_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** REQ-DEMO-1\n")
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "unchanged", old_req_uid="REQ-DEMO-1", new_req_uid="REQ-DEMO-1")])

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("no_action", report.impact_entries[0].action)
            self.assertFalse(report.impact_entries[0].requires_manual_review)

    def test_renumbered_is_traceability_update_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** BSR 1\n")
            diff_path = write_diff(
                root,
                [make_diff_entry("CHG-000001", "renumbered", old_source_req_id="BSR 1", new_source_req_id="BSR 2")],
            )

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("traceability_update_only", report.impact_entries[0].action)
            self.assertEqual("medium", report.impact_entries[0].priority)

    def test_source_anchor_changed_is_traceability_update_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** REQ-DEMO-1\n")
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "source_anchor_changed", old_req_uid="REQ-DEMO-1")])

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("traceability_update_only", report.impact_entries[0].action)

    def test_split_and_merged_are_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** REQ-DEMO-OLD\n")
            diff_path = write_diff(
                root,
                [
                    make_diff_entry("CHG-000001", "split", old_req_uid="REQ-DEMO-OLD", requires_manual_review=True),
                    make_diff_entry("CHG-000002", "merged", old_req_uid="REQ-DEMO-OLD", requires_manual_review=True),
                ],
            )

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual(["manual_review", "manual_review"], [entry.action for entry in report.impact_entries])
            self.assertTrue(all(entry.requires_manual_review for entry in report.impact_entries))

    def test_duplicate_tc_ids_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "a.md", "## TC-001\n**Трассировка:** BSR 1\n")
            write_tc(tc_dir / "b.md", "## TC-001\n**Трассировка:** BSR 2\n")
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "unchanged", old_source_req_id="BSR 1")])

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("blocked", report.summary["impact_status"])
            self.assertTrue(any("duplicate TC ids" in reason for reason in report.blocking_reasons))

    def test_missing_test_cases_dir_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "unchanged")])

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=root / "missing")

            self.assertEqual("blocked", report.summary["impact_status"])
            self.assertTrue(any("test-cases dir is missing" in reason for reason in report.blocking_reasons))

    def test_blocked_diff_summary_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** BSR 1\n")
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "unchanged")], diff_status="blocked")

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            self.assertEqual("blocked", report.summary["impact_status"])
            self.assertTrue(any("requirements diff summary is blocked" in reason for reason in report.blocking_reasons))

    def test_json_and_markdown_reports_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            write_tc(tc_dir / "scope.md", "## TC-001\n**Трассировка:** BSR 1\n")
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "unchanged", old_source_req_id="BSR 1")])
            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)

            report_path, summary_path, markdown_path = write_impact_report(report, root)
            loaded = load_impact_report(report_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertTrue(report_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertEqual(1, len(loaded.impact_entries))
            self.assertIn("## Summary", markdown)
            self.assertIn("## Actions by Type", markdown)

    def test_builder_does_not_modify_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, tc_dir = setup_root(temp_dir)
            test_case_path = tc_dir / "scope.md"
            original = "## TC-001\n**Трассировка:** REQ-DEMO-OLD\n"
            write_tc(test_case_path, original)
            diff_path = write_diff(root, [make_diff_entry("CHG-000001", "behavior_modified", old_req_uid="REQ-DEMO-OLD")])

            report = build_impact_report(requirements_diff_path=diff_path, test_cases_dir=tc_dir)
            write_impact_report(report, root)

            self.assertEqual(original, test_case_path.read_text(encoding="utf-8"))


def setup_root(temp_dir: str) -> tuple[Path, Path]:
    root = Path(temp_dir)
    tc_dir = root / "fts" / "demo-ft" / "test-cases"
    tc_dir.mkdir(parents=True)
    return root, tc_dir


def write_tc(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def make_diff_entry(
    change_id: str,
    change_type: str,
    *,
    old_req_uid: str | None = None,
    new_req_uid: str | None = None,
    old_atom_id: str | None = None,
    new_atom_id: str | None = None,
    old_source_req_id: str | None = None,
    new_source_req_id: str | None = None,
    requires_manual_review: bool = False,
) -> RequirementsDiffEntry:
    return RequirementsDiffEntry(
        change_id=change_id,
        change_type=change_type,
        old_req_uid=old_req_uid,
        new_req_uid=new_req_uid,
        old_atom_id=old_atom_id,
        new_atom_id=new_atom_id,
        old_source_req_id=old_source_req_id,
        new_source_req_id=new_source_req_id,
        old_requirement_type="requiredness",
        new_requirement_type="requiredness",
        old_status="active",
        new_status="active",
        old_normalized_text="old text",
        new_normalized_text="new text",
        old_semantic_fingerprint="old",
        new_semantic_fingerprint="new",
        old_text_hash="sha256:old",
        new_text_hash="sha256:new",
        old_source_anchors=[],
        new_source_anchors=[],
        similarity_score=0.8,
        confidence="medium",
        requires_manual_review=requires_manual_review,
        reasons=[],
        warnings=[],
    )


def write_diff(
    root: Path,
    entries: list[RequirementsDiffEntry],
    *,
    diff_status: str = "pass",
) -> Path:
    diff_path = root / "requirements-diff.old-v1-to-new-v1.json"
    summary_path = root / "requirements-diff-summary.old-v1-to-new-v1.json"
    summary = {
        "old_registry_path": "old.jsonl",
        "new_registry_path": "new.jsonl",
        "old_source_version": "old-v1",
        "new_source_version": "new-v1",
        "diff_status": diff_status,
        "entries_total": len(entries),
        "warnings": [],
        "blocking_reasons": ["blocked for test"] if diff_status == "blocked" else [],
    }
    diff = RequirementsDiff(
        old_registry_path="old.jsonl",
        new_registry_path="new.jsonl",
        old_source_version="old-v1",
        new_source_version="new-v1",
        created_at_utc="2026-07-04T00:00:00Z",
        created_by_tool="tests",
        entries=entries,
        summary=summary,
        warnings=[],
        blocking_reasons=[],
    )
    diff_path.write_text(
        json.dumps(diff.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return diff_path


if __name__ == "__main__":
    unittest.main()
