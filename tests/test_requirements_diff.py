from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    RequirementRegistryEntry,
    SourceAnchor,
    build_requirements_diff,
    compute_requirement_text_hash,
    compute_text_similarity,
    load_requirements_diff,
    make_req_uid,
    write_requirements_diff,
)


class RequirementsDiffTests(unittest.TestCase):
    def test_same_registry_vs_same_registry_produces_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            entry = make_entry("old-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")
            registry_path = write_registry(root, "old-v1", [entry])

            diff = build_requirements_diff(
                old_registry_path=registry_path,
                new_registry_path=registry_path,
            )

            self.assertEqual("pass", diff.summary["diff_status"])
            self.assertEqual(1, diff.summary["unchanged"])
            self.assertEqual("unchanged", diff.entries[0].change_type)

    def test_added_entry_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            common = make_entry("old-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")
            added = make_entry("new-v1", "BSR 2 Поле отображается.", source_req_id="BSR 2", requirement_type="visibility")
            old_path = write_registry(root, "old-v1", [common])
            new_path = write_registry(root, "new-v1", [replace_version(common, "new-v1"), added])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertEqual(1, diff.summary["added"])
            self.assertTrue(any(entry.change_type == "added" for entry in diff.entries))

    def test_deleted_entry_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            deleted = make_entry("old-v1", "BSR 2 Поле отображается.", source_req_id="BSR 2", requirement_type="visibility")
            common = make_entry("old-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")
            old_path = write_registry(root, "old-v1", [common, deleted])
            new_path = write_registry(root, "new-v1", [replace_version(common, "new-v1")])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertEqual(1, diff.summary["deleted"])
            self.assertTrue(any(entry.change_type == "deleted" for entry in diff.entries))

    def test_same_req_uid_changed_text_produces_modified_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            req_uid = "REQ-DEMO-SAMEUID"
            old_entry = make_entry("old-v1", "BSR 1 Поле обязательно.", req_uid=req_uid, source_req_id="BSR 1")
            new_entry = make_entry(
                "new-v1",
                "BSR 1 Поле обязательно для клиента.",
                req_uid=req_uid,
                source_req_id="BSR 1",
            )
            old_path = write_registry(root, "old-v1", [old_entry])
            new_path = write_registry(root, "new-v1", [new_entry])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertIn(
                diff.entries[0].change_type,
                {"behavior_modified", "text_changed_no_behavior_change"},
            )
            self.assertEqual(req_uid, diff.entries[0].old_req_uid)
            self.assertEqual(req_uid, diff.entries[0].new_req_uid)

    def test_same_semantic_fingerprint_changed_source_req_id_produces_renumbered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fingerprint = "requiredness|||поле обязательно."
            old_entry = make_entry(
                "old-v1",
                "Поле обязательно.",
                req_uid="REQ-DEMO-OLD",
                source_req_id="BSR 1",
                semantic_fingerprint=fingerprint,
            )
            new_entry = make_entry(
                "new-v1",
                "Поле обязательно.",
                req_uid="REQ-DEMO-NEW",
                source_req_id="BSR 99",
                semantic_fingerprint=fingerprint,
            )
            old_path = write_registry(root, "old-v1", [old_entry])
            new_path = write_registry(root, "new-v1", [new_entry])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertEqual("renumbered", diff.entries[0].change_type)

    def test_same_text_changed_source_anchor_produces_source_anchor_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_entry = make_entry("old-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1", xpath="/w:p[1]")
            new_entry = replace_version(old_entry, "new-v1", xpath="/w:p[7]")
            old_path = write_registry(root, "old-v1", [old_entry])
            new_path = write_registry(root, "new-v1", [new_entry])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertEqual("source_anchor_changed", diff.entries[0].change_type)

    def test_similar_text_fallback_produces_behavior_modified_with_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_entry = make_entry(
                "old-v1",
                "Поле адрес обязательно для клиента.",
                req_uid="REQ-DEMO-OLD",
                source_req_id=None,
            )
            new_entry = make_entry(
                "new-v1",
                "Поле телефон обязательно для клиента.",
                req_uid="REQ-DEMO-NEW",
                source_req_id=None,
            )
            self.assertGreaterEqual(
                compute_text_similarity(old_entry.normalized_text, new_entry.normalized_text),
                0.75,
            )
            old_path = write_registry(root, "old-v1", [old_entry])
            new_path = write_registry(root, "new-v1", [new_entry])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertEqual("behavior_modified", diff.entries[0].change_type)
            self.assertTrue(diff.entries[0].requires_manual_review)

    def test_split_candidate_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_entry = make_entry(
                "old-v1",
                "Поле адрес обязательно и доступно для редактирования.",
                req_uid="REQ-DEMO-OLD",
                source_req_id=None,
            )
            new_entries = [
                make_entry("new-v1", "Поле адрес обязательно.", req_uid="REQ-DEMO-NEW1", source_req_id=None),
                make_entry(
                    "new-v1",
                    "Поле адрес доступно для редактирования.",
                    req_uid="REQ-DEMO-NEW2",
                    source_req_id=None,
                    requirement_type="editability",
                ),
            ]
            old_path = write_registry(root, "old-v1", [old_entry])
            new_path = write_registry(root, "new-v1", new_entries)

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertGreaterEqual(diff.summary["split"], 1)
            self.assertTrue(any(entry.change_type == "split" and entry.requires_manual_review for entry in diff.entries))

    def test_merge_candidate_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_entries = [
                make_entry("old-v1", "Поле адрес обязательно.", req_uid="REQ-DEMO-OLD1", source_req_id=None),
                make_entry(
                    "old-v1",
                    "Поле адрес доступно для редактирования.",
                    req_uid="REQ-DEMO-OLD2",
                    source_req_id=None,
                    requirement_type="editability",
                ),
            ]
            new_entry = make_entry(
                "new-v1",
                "Поле адрес обязательно и доступно для редактирования.",
                req_uid="REQ-DEMO-NEW",
                source_req_id=None,
            )
            old_path = write_registry(root, "old-v1", old_entries)
            new_path = write_registry(root, "new-v1", [new_entry])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertGreaterEqual(diff.summary["merged"], 1)
            self.assertTrue(any(entry.change_type == "merged" and entry.requires_manual_review for entry in diff.entries))

    def test_duplicate_req_uid_blocks_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            duplicate_uid = "REQ-DEMO-DUPLICATE"
            old_path = write_registry(
                root,
                "old-v1",
                [
                    make_entry("old-v1", "BSR 1 Поле обязательно.", req_uid=duplicate_uid, source_req_id="BSR 1"),
                    make_entry("old-v1", "BSR 2 Поле обязательно.", req_uid=duplicate_uid, source_req_id="BSR 2"),
                ],
            )
            new_path = write_registry(root, "new-v1", [make_entry("new-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertEqual("blocked", diff.summary["diff_status"])
            self.assertEqual(0, diff.summary["entries_total"])
            self.assertTrue(any("duplicate req_uid" in reason for reason in diff.blocking_reasons))

    def test_duplicate_req_uid_passes_only_with_allow_duplicate_req_uid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            duplicate_uid = "REQ-DEMO-DUPLICATE"
            old_path = write_registry(
                root,
                "old-v1",
                [
                    make_entry("old-v1", "BSR 1 Поле обязательно.", req_uid=duplicate_uid, source_req_id="BSR 1"),
                    make_entry("old-v1", "BSR 2 Поле обязательно.", req_uid=duplicate_uid, source_req_id="BSR 2"),
                ],
            )
            new_path = write_registry(root, "new-v1", [make_entry("new-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")])

            diff = build_requirements_diff(
                old_registry_path=old_path,
                new_registry_path=new_path,
                allow_duplicate_req_uid=True,
            )

            self.assertNotEqual("blocked", diff.summary["diff_status"])
            self.assertTrue(diff.entries)
            self.assertTrue(any("Duplicate req_uid" in warning for warning in diff.warnings))

    def test_blocked_old_or_new_registry_summary_blocks_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_path = write_registry(
                root,
                "old-v1",
                [make_entry("old-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")],
                registry_status="blocked",
            )
            new_path = write_registry(root, "new-v1", [make_entry("new-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")])

            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            self.assertEqual("blocked", diff.summary["diff_status"])
            self.assertTrue(any("old registry summary is blocked" in reason for reason in diff.blocking_reasons))

    def test_json_diff_and_summary_can_be_loaded_back(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_path = write_registry(root, "old-v1", [make_entry("old-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")])
            new_path = write_registry(root, "new-v1", [make_entry("new-v1", "BSR 1 Поле обязательно.", source_req_id="BSR 1")])
            diff = build_requirements_diff(old_registry_path=old_path, new_registry_path=new_path)

            diff_path, summary_path = write_requirements_diff(diff, root)
            loaded = load_requirements_diff(diff_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

            self.assertEqual(len(diff.entries), len(loaded.entries))
            self.assertEqual(diff.summary["entries_total"], summary["entries_total"])
            self.assertEqual("old-v1", loaded.old_source_version)


def make_entry(
    source_version: str,
    text: str,
    *,
    req_uid: str | None = None,
    source_req_id: str | None = None,
    requirement_type: str = "requiredness",
    status: str = "active",
    semantic_fingerprint: str | None = None,
    xpath: str = "/w:document/w:body/w:p[1]/w:r/w:t/text()",
    node_id: str = "ooxml-node-000001",
    flags: list[str] | None = None,
    warnings: list[str] | None = None,
) -> RequirementRegistryEntry:
    normalized_text = text
    req_uid = req_uid or make_req_uid(
        "demo-ft",
        normalized_text,
        source_req_id=source_req_id,
        requirement_type=requirement_type,
    )
    semantic_fingerprint = semantic_fingerprint or f"{requirement_type}|||{normalized_text.casefold()}"
    return RequirementRegistryEntry(
        req_uid=req_uid,
        atom_id="ATOM-000001",
        source_version=source_version,
        ft_slug="demo-ft",
        source_req_id=source_req_id,
        source_row_id=None,
        section_id=None,
        scope_slug=None,
        package_id=None,
        requirement_type=requirement_type,
        object=None,
        condition=None,
        expected_behavior=normalized_text if status == "active" else None,
        source_text=text,
        normalized_text=normalized_text,
        source_anchors=[
            SourceAnchor(
                source_doc="source.docx",
                source_version=source_version,
                part="word/document.xml",
                xpath=xpath,
                node_id=node_id,
                value_type="text",
                flags=flags or [],
                aggregate_kind=None,
                aggregate_confidence=None,
            )
        ],
        semantic_fingerprint=semantic_fingerprint,
        text_hash=compute_requirement_text_hash(normalized_text),
        status=status,
        confidence="medium" if status == "active" else "low",
        warnings=warnings or [],
    )


def replace_version(
    entry: RequirementRegistryEntry,
    source_version: str,
    *,
    xpath: str | None = None,
) -> RequirementRegistryEntry:
    anchor = entry.source_anchors[0]
    return RequirementRegistryEntry(
        req_uid=entry.req_uid,
        atom_id=entry.atom_id,
        source_version=source_version,
        ft_slug=entry.ft_slug,
        source_req_id=entry.source_req_id,
        source_row_id=entry.source_row_id,
        section_id=entry.section_id,
        scope_slug=entry.scope_slug,
        package_id=entry.package_id,
        requirement_type=entry.requirement_type,
        object=entry.object,
        condition=entry.condition,
        expected_behavior=entry.expected_behavior,
        source_text=entry.source_text,
        normalized_text=entry.normalized_text,
        source_anchors=[
            SourceAnchor(
                source_doc=anchor.source_doc,
                source_version=source_version,
                part=anchor.part,
                xpath=xpath or anchor.xpath,
                node_id=anchor.node_id,
                value_type=anchor.value_type,
                flags=anchor.flags,
                aggregate_kind=anchor.aggregate_kind,
                aggregate_confidence=anchor.aggregate_confidence,
            )
        ],
        semantic_fingerprint=entry.semantic_fingerprint,
        text_hash=entry.text_hash,
        status=entry.status,
        confidence=entry.confidence,
        warnings=entry.warnings,
    )


def write_registry(
    root: Path,
    source_version: str,
    entries: list[RequirementRegistryEntry],
    *,
    registry_status: str = "pass",
) -> Path:
    registry_path = root / f"requirements.{source_version}.jsonl"
    summary_path = root / f"requirements-summary.{source_version}.json"
    registry_path.write_text(
        "".join(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n" for entry in entries),
        encoding="utf-8",
        newline="\n",
    )
    summary = {
        "ft_slug": "demo-ft",
        "source_version": source_version,
        "registry_status": registry_status,
        "entries_total": len(entries),
        "blocking_reasons": ["blocked for test"] if registry_status == "blocked" else [],
        "warnings": [],
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return registry_path


if __name__ == "__main__":
    unittest.main()
