from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    CreateNewTcContextBundle,
    TableSourceContext,
    build_create_new_tc_context_bundle,
    load_create_new_tc_context_bundle,
    write_create_new_tc_context_bundle,
)
from tests.test_ooxml_loader import build_table_docx_fixture


class CreateNewTcContextBundleTests(unittest.TestCase):
    def test_builds_bundle_for_create_new_candidate_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))

            bundle = build_bundle(root)

            self.assertEqual("pass-with-warnings", bundle.bundle_status)
            self.assertEqual("WPKG-000001", bundle.package_id)
            self.assertEqual("create_new_candidate", bundle.package_type)
            self.assertEqual(["PLAN-000001"], bundle.plan_item_ids)
            self.assertEqual(1, len(bundle.candidate_requirements))

    def test_blocks_when_package_id_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))

            bundle = build_bundle(root, package_id="WPKG-999999")

            self.assertEqual("blocked", bundle.bundle_status)
            self.assertTrue(any("not found" in reason for reason in bundle.blocking_reasons))

    def test_blocks_when_package_type_is_not_create_new_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir), package_type="manual_review")

            bundle = build_bundle(root)

            self.assertEqual("blocked", bundle.bundle_status)
            self.assertTrue(any("must be create_new_candidate" in reason for reason in bundle.blocking_reasons))

    def test_extracts_plan_item_impact_and_diff_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))

            candidate = build_bundle(root).candidate_requirements[0]

            self.assertEqual("PLAN-000001", candidate.plan_item_id)
            self.assertEqual("IMP-000001", candidate.impact_id)
            self.assertEqual("CHG-000001", candidate.diff_entry_id)
            self.assertEqual("behavior_modified", candidate.change_type)

    def test_extracts_candidate_requirements_from_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))

            candidate = build_bundle(root).candidate_requirements[0]

            self.assertEqual("REQ-DEMO-NEW", candidate.req_uid)
            self.assertEqual("BSR 10", candidate.source_req_id)
            self.assertEqual("editability", candidate.requirement_type)
            self.assertEqual("Client card", candidate.object)
            self.assertEqual("The client card field is editable.", candidate.expected_behavior)

    def test_table_source_context_model_round_trips(self) -> None:
        context = TableSourceContext(
            source_path="new.docx",
            source_version="new",
            table_id="table-1",
            row_index=2,
            column_index=1,
            header_cells=["Field", "Behavior"],
            row_cells=["Client card", "Editable"],
            cell_text="Editable",
            row_text="Client card | Editable",
            neighboring_rows=[],
            normalized_row_facts=["Client card is editable"],
            field_name_candidates=["Client card"],
            condition_candidates=["User opens client card"],
            expected_behavior_candidates=["Client card is editable"],
            action_candidates=["User opens client card"],
            confidence="high",
            warnings=[],
        )

        loaded = TableSourceContext.from_dict(context.to_dict())

        self.assertEqual(context.to_dict(), loaded.to_dict())

    def test_candidate_requirement_preserves_table_and_anchor_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))

            candidate = build_bundle(root).candidate_requirements[0]

            self.assertGreaterEqual(len(candidate.source_anchor_contexts), 1)
            self.assertGreaterEqual(len(candidate.table_source_contexts), 1)
            self.assertIsNotNone(candidate.enriched_source_facts)
            self.assertIn("table_source_context", candidate.enriched_source_facts.available_fact_sources)
            self.assertEqual("high", candidate.source_fact_confidence)
            self.assertTrue(any("fallback" in warning for context in candidate.table_source_contexts for warning in context.warnings))

    def test_candidate_requirement_includes_real_ooxml_table_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))
            source_docx = root / "new.docx"
            build_table_docx_fixture(source_docx)
            rewrite_new_registry_anchor(
                root / "work" / "requirements.new.jsonl",
                source_doc=str(source_docx),
                xpath="/w:document/w:body/w:tbl[1]/w:tr[2]/w:tc[2]/w:p[1]/w:r/w:t/text()",
            )

            candidate = build_bundle(root).candidate_requirements[0]
            table_context = candidate.table_source_contexts[0]

            self.assertEqual(["Field", "Expected result", "Action"], table_context.header_cells)
            self.assertEqual(["Client card", "Client card field is editable", "User opens client card"], table_context.row_cells)
            self.assertEqual(["Phone | Phone is displayed | User opens contacts"], table_context.neighboring_rows)
            self.assertFalse(any("fallback" in warning for warning in table_context.warnings))
            self.assertIn("Expected result: Client card field is editable", table_context.expected_behavior_candidates)

    def test_groups_requirements_with_explicit_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))

            group = build_bundle(root).candidate_groups[0]

            self.assertEqual(["REQ-DEMO-NEW"], group.candidate_req_uids)
            self.assertGreater(group.suggested_tc_count, 0)
            self.assertIn("Grouped by source anchor context", group.group_reason)
            self.assertTrue(group.requires_manual_review)

    def test_detects_possible_duplicate_existing_tc_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))

            bundle = build_bundle(root)

            self.assertEqual(1, len(bundle.duplicate_risks))
            self.assertEqual("TC-EXIST-001", bundle.duplicate_risks[0]["similar_tc_id"])
            self.assertEqual("high", bundle.duplicate_risks[0]["risk"])

    def test_recommends_draft_target_without_writing_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            bundle = build_bundle(root)

            self.assertGreaterEqual(len(bundle.recommended_draft_targets), 1)
            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))
            self.assertFalse((tc_path.parent / "create-new-tc-context-bundle-WPKG-000001.md").exists())

    def test_warns_on_missing_registry_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir), include_new_registry_entry=False)

            bundle = build_bundle(root)

            self.assertEqual("pass-with-warnings", bundle.bundle_status)
            self.assertTrue(
                any("registry entry missing" in warning for warning in bundle.candidate_requirements[0].warnings)
            )
            self.assertEqual(["REQ-DEMO-NEW"], bundle.registry_context["candidate_registry_entries_missing"])

    def test_json_and_markdown_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))
            bundle = build_bundle(root)

            json_path, markdown_path = write_create_new_tc_context_bundle(bundle, root / "work")
            loaded = load_create_new_tc_context_bundle(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, CreateNewTcContextBundle)
            self.assertEqual("create-new-tc-context-bundle-WPKG-000001.json", json_path.name)
            self.assertIn("No canonical test-case file was created", markdown)
            self.assertIn("## Candidate Requirements", markdown)

    def test_canonical_test_case_files_remain_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = setup_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            bundle = build_bundle(root)
            write_create_new_tc_context_bundle(bundle, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_fixture(
    root: Path,
    *,
    package_type: str = "create_new_candidate",
    include_new_registry_entry: bool = True,
) -> Path:
    work = root / "work"
    work.mkdir(parents=True)
    test_cases_dir = root / "fts" / "Demo" / "test-cases"
    test_cases_dir.mkdir(parents=True)
    (test_cases_dir / "scope.md").write_text(
        "\n".join(
            [
                "## TC-EXIST-001 Existing client card case",
                "**Title:** Existing client card editability",
                "**Traceability:** BSR 10",
                "**Steps:** Open the client card.",
                "**Expected result:** Client card field is editable.",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    write_json(
        work / "manual-update-packages.old-to-new.json",
        {
            "ft_slug": "Demo",
            "old_source_version": "old",
            "new_source_version": "new",
            "update_plan_path": str(work / "test-case-update-plan.old-to-new.json"),
            "created_at_utc": "2026-07-06T00:00:00Z",
            "created_by_tool": "tests",
            "packages": [
                {
                    "package_id": "WPKG-000001",
                    "package_type": package_type,
                    "file_path": None,
                    "test_case_ids": [],
                    "plan_item_ids": ["PLAN-000001"],
                    "impact_ids": ["IMP-000001"],
                    "change_ids": ["CHG-000001"],
                    "actions": [package_type],
                    "plan_items_count": 1,
                    "priority": "high",
                    "requires_manual_review": True,
                    "writer_allowed_operations": ["propose new TC drafts"],
                    "writer_forbidden_operations": ["Do not write canonical files"],
                    "rationale": [],
                    "warnings": [],
                }
            ],
            "summary": {"package_status": "pass-with-warnings"},
            "warnings": [],
            "blocking_reasons": [],
        },
    )
    write_json(
        work / "writer-package-tasks.old-to-new.json",
        {
            "ft_slug": "Demo",
            "old_source_version": "old",
            "new_source_version": "new",
            "manual_update_packages_path": str(work / "manual-update-packages.old-to-new.json"),
            "created_at_utc": "2026-07-06T00:00:00Z",
            "created_by_tool": "tests",
            "tasks": [
                {
                    "package_id": "WPKG-000001",
                    "task_file_name": "writer-package-task-WPKG-000001.md",
                    "package_type": package_type,
                    "file_path": None,
                    "affected_test_case_ids": [],
                    "plan_item_ids": ["PLAN-000001"],
                    "impact_ids": ["IMP-000001"],
                    "change_ids": ["CHG-000001"],
                    "actions": [package_type],
                    "plan_items_count": 1,
                    "large_package": False,
                    "safe_to_try_first": False,
                    "allowed_operations": ["propose new TC drafts"],
                    "forbidden_operations": ["Do not write canonical files"],
                    "scope_instruction": "Propose drafts only, do not write canonical files.",
                    "execution_notes": [],
                    "warnings": [],
                }
            ],
            "summary": {"task_status": "pass-with-warnings"},
            "warnings": [],
            "blocking_reasons": [],
        },
    )
    write_json(
        work / "test-case-update-plan.old-to-new.json",
        {
            "ft_slug": "Demo",
            "old_source_version": "old",
            "new_source_version": "new",
            "impact_report_path": str(work / "impact-report.old-to-new.json"),
            "test_cases_dir": str(test_cases_dir),
            "created_at_utc": "2026-07-06T00:00:00Z",
            "created_by_tool": "tests",
            "plan_items": [
                {
                    "plan_item_id": "PLAN-000001",
                    "impact_id": "IMP-000001",
                    "change_id": "CHG-000001",
                    "test_case_id": None,
                    "file_path": None,
                    "action": "create_new_candidate",
                    "apply_mode": "manual_only",
                    "old_refs": ["REQ-DEMO-OLD"],
                    "new_refs": ["REQ-DEMO-NEW", "BSR 10"],
                    "required_changes": ["create new TC candidate in later writer stage"],
                    "forbidden_changes": ["Do not create TC in Stage 6A"],
                    "rationale": ["impact action=create_new"],
                    "requires_manual_review": True,
                    "warnings": [],
                }
            ],
            "summary": {"plan_status": "pass-with-warnings"},
            "warnings": [],
            "blocking_reasons": [],
        },
    )
    write_json(
        work / "impact-report.old-to-new.json",
        {
            "ft_slug": "Demo",
            "old_source_version": "old",
            "new_source_version": "new",
            "requirements_diff_path": str(work / "requirements-diff.old-to-new.json"),
            "test_cases_dir": str(test_cases_dir),
            "created_at_utc": "2026-07-06T00:00:00Z",
            "created_by_tool": "tests",
            "impact_entries": [
                {
                    "impact_id": "IMP-000001",
                    "change_id": "CHG-000001",
                    "change_type": "behavior_modified",
                    "old_req_uid": "REQ-DEMO-OLD",
                    "new_req_uid": "REQ-DEMO-NEW",
                    "old_source_req_id": "BSR 9",
                    "new_source_req_id": "BSR 10",
                    "affected_test_cases": [],
                    "action": "create_new",
                    "priority": "high",
                    "rationale": ["no linked test case found"],
                    "requires_manual_review": True,
                    "warnings": [],
                }
            ],
            "summary": {"impact_status": "pass-with-warnings"},
            "warnings": [],
            "blocking_reasons": [],
        },
    )
    write_json(
        work / "requirements-diff.old-to-new.json",
        {
            "old_registry_path": str(work / "requirements.old.jsonl"),
            "new_registry_path": str(work / "requirements.new.jsonl"),
            "old_source_version": "old",
            "new_source_version": "new",
            "created_at_utc": "2026-07-06T00:00:00Z",
            "created_by_tool": "tests",
            "entries": [
                {
                    "change_id": "CHG-000001",
                    "change_type": "behavior_modified",
                    "old_req_uid": "REQ-DEMO-OLD",
                    "new_req_uid": "REQ-DEMO-NEW",
                    "old_source_req_id": "BSR 9",
                    "new_source_req_id": "BSR 10",
                    "new_requirement_type": "editability",
                    "new_status": "active",
                    "new_normalized_text": "Client card field is editable.",
                    "new_source_anchors": [
                        {
                            "source_doc": "new.docx",
                            "source_version": "new",
                            "part": "word/document.xml",
                            "xpath": "/w:document/w:body/w:tbl[1]/w:tr[2]/w:tc[1]",
                            "node_id": "node-1",
                            "value_type": "text",
                            "flags": ["table"],
                            "aggregate_kind": None,
                            "aggregate_confidence": None,
                        }
                    ],
                    "confidence": "medium",
                    "warnings": [],
                }
            ],
            "summary": {"diff_status": "pass-with-warnings"},
            "warnings": [],
            "blocking_reasons": [],
        },
    )
    write_registry(
        work / "requirements.old.jsonl",
        [
            registry_entry(
                req_uid="REQ-DEMO-OLD",
                source_req_id="BSR 9",
                source_version="old",
                expected_behavior="The old client card field behavior.",
            )
        ],
    )
    new_entries = []
    if include_new_registry_entry:
        new_entries.append(
            registry_entry(
                req_uid="REQ-DEMO-NEW",
                source_req_id="BSR 10",
                source_version="new",
                expected_behavior="The client card field is editable.",
            )
        )
    write_registry(work / "requirements.new.jsonl", new_entries)
    write_json(work / "source-manifest.old.json", {"source_version": "old", "manifest_status": "clean"})
    write_json(work / "source-manifest.new.json", {"source_version": "new", "manifest_status": "clean"})
    return root


def registry_entry(
    *,
    req_uid: str,
    source_req_id: str,
    source_version: str,
    expected_behavior: str,
) -> dict[str, object]:
    return {
        "req_uid": req_uid,
        "source_version": source_version,
        "source_req_id": source_req_id,
        "requirement_type": "editability",
        "object": "Client card",
        "condition": "User opens client card",
        "expected_behavior": expected_behavior,
        "source_text": expected_behavior,
        "normalized_text": expected_behavior,
        "source_anchors": [
            {
                "source_doc": f"{source_version}.docx",
                "source_version": source_version,
                "part": "word/document.xml",
                "xpath": "/w:document/w:body/w:tbl[1]/w:tr[2]/w:tc[1]",
                "node_id": "node-1",
                "value_type": "text",
                "flags": ["table"],
                "aggregate_kind": None,
                "aggregate_confidence": None,
            }
        ],
        "confidence": "high",
        "warnings": [],
    }


def build_bundle(root: Path, *, package_id: str = "WPKG-000001"):
    work = root / "work"
    return build_create_new_tc_context_bundle(
        package_id=package_id,
        manual_update_packages_path=work / "manual-update-packages.old-to-new.json",
        writer_package_tasks_path=work / "writer-package-tasks.old-to-new.json",
        update_plan_path=work / "test-case-update-plan.old-to-new.json",
        impact_report_path=work / "impact-report.old-to-new.json",
        requirements_diff_path=work / "requirements-diff.old-to-new.json",
        old_registry_path=work / "requirements.old.jsonl",
        new_registry_path=work / "requirements.new.jsonl",
        old_source_manifest_path=work / "source-manifest.old.json",
        new_source_manifest_path=work / "source-manifest.new.json",
        test_cases_dir=root / "fts" / "Demo" / "test-cases",
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_registry(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries),
        encoding="utf-8",
        newline="\n",
    )


def rewrite_new_registry_anchor(path: Path, *, source_doc: str, xpath: str) -> None:
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries[0]["source_anchors"][0]["source_doc"] = source_doc
    entries[0]["source_anchors"][0]["xpath"] = xpath
    path.write_text(
        "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    unittest.main()
