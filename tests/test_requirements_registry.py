from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_case_agent import (
    build_requirements_registry,
    build_source_manifest,
    load_requirements_registry,
    load_requirements_registry_jsonl,
    make_req_uid,
    write_requirements_registry,
    write_source_manifest,
)
from tests.test_ooxml_loader import EXPECTED_MARKERS, build_docx_fixture


ROOT_DIR = Path(__file__).resolve().parents[1]


class RequirementsRegistryTests(unittest.TestCase):
    def test_cli_creates_jsonl_and_summary_from_generated_docx_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = _write_manifest(root, source_version="cli-v1")
            out_dir = root / "requirements"

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT_DIR / "scripts" / "build_requirements_registry.py"),
                    "--source-manifest",
                    str(manifest_path),
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            registry_path = out_dir / "requirements.cli-v1.jsonl"
            summary_path = out_dir / "requirements-summary.cli-v1.json"
            self.assertEqual(str(registry_path), payload["registry_path"])
            self.assertEqual(str(summary_path), payload["summary_path"])
            self.assertTrue(registry_path.exists())
            self.assertTrue(summary_path.exists())
            entries = load_requirements_registry_jsonl(registry_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertGreater(len(entries), 0)
            self.assertEqual(len(entries), summary["entries_total"])
            self.assertEqual("pass-with-warnings", summary["registry_status"])
            self.assertEqual("scripts/build_requirements_registry.py", summary["created_by_tool"])
            self.assertEqual(
                str(out_dir / "source-coverage-audit.cli-v1.json"),
                summary["coverage_audit_path"],
            )
            self.assertTrue(all(entry.source_anchors for entry in entries))

    def test_req_uid_is_stable_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = _write_manifest(root, source_version="stable-v1")

            first = build_requirements_registry(manifest_path)
            second = build_requirements_registry(manifest_path)

            first_uids = [(entry.normalized_text, entry.req_uid) for entry in first.entries]
            second_uids = [(entry.normalized_text, entry.req_uid) for entry in second.entries]
            self.assertEqual(first_uids, second_uids)

    def test_same_manifest_maps_same_normalized_text_to_same_req_uid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = _write_manifest(root, source_version="same-text-v1")

            registry = build_requirements_registry(manifest_path)
            entry = registry.entries[0]

            self.assertEqual(
                entry.req_uid,
                make_req_uid(
                    entry.ft_slug,
                    entry.normalized_text,
                    source_req_id=entry.source_req_id,
                    requirement_type=entry.requirement_type,
                ),
            )

    def test_blocked_source_manifest_blocks_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing_docx = root / "missing.docx"
            out_dir = root / "requirements"
            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="blocked-v1",
                docx=missing_docx,
                out_dir=out_dir,
            )
            manifest_path = write_source_manifest(manifest, out_dir)

            registry = build_requirements_registry(manifest_path)
            registry_path, summary_path = write_requirements_registry(registry, out_dir)

            self.assertEqual([], registry.entries)
            self.assertTrue(registry_path.exists())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual("blocked", summary["registry_status"])
            self.assertEqual(0, summary["entries_total"])
            self.assertTrue(
                any("ingestion_status is blocked" in reason for reason in registry.blocking_reasons)
            )

    def test_missing_source_manifest_blocks_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            registry = build_requirements_registry(root / "missing-source-manifest.json")

            self.assertEqual("blocked", registry.extraction_summary["registry_status"])
            self.assertEqual([], registry.entries)
            self.assertTrue(
                any("source manifest is missing" in reason for reason in registry.blocking_reasons)
            )

    def test_contaminated_source_manifest_blocks_registry_without_reading_docx(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "sample.docx"
            forbidden_support = root / "expected_answer.txt"
            out_dir = root / "requirements"
            build_docx_fixture(source_docx)
            forbidden_support.write_text("answer", encoding="utf-8")
            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="contaminated-v1",
                docx=source_docx,
                support_files=[forbidden_support],
                out_dir=out_dir,
            )
            manifest_path = write_source_manifest(manifest, out_dir)

            with patch("test_case_agent.requirements_registry.load_ooxml_source") as mocked_load:
                registry = build_requirements_registry(manifest_path)

            mocked_load.assert_not_called()
            self.assertEqual([], registry.entries)
            self.assertEqual("blocked", registry.extraction_summary["registry_status"])
            self.assertTrue(
                any("clean_run_status is contaminated" in reason for reason in registry.blocking_reasons)
            )

    def test_aggregate_node_entry_gets_warning_and_non_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = _write_manifest(root, source_version="aggregate-v1")

            registry = build_requirements_registry(manifest_path)
            entry = _entry_containing(registry.entries, EXPECTED_MARKERS["split_run"])

            self.assertIsNotNone(entry)
            self.assertNotEqual("high", entry.confidence)
            self.assertTrue(any(anchor.value_type == "aggregate" for anchor in entry.source_anchors))
            self.assertTrue(
                any("Derived aggregate source node used" in warning for warning in entry.warnings)
            )

    def test_tracked_deletion_is_not_active_without_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = _write_manifest(root, source_version="tracked-v1")

            registry = build_requirements_registry(manifest_path)
            entry = _entry_containing(
                registry.entries,
                EXPECTED_MARKERS["tracked_delete"],
                required_flag="tracked_delete",
            )

            self.assertIsNotNone(entry)
            self.assertNotEqual("active", entry.status)
            self.assertTrue(any("Tracked deletion text" in warning for warning in entry.warnings))

    def test_hidden_text_gets_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = _write_manifest(root, source_version="hidden-v1")

            registry = build_requirements_registry(manifest_path)
            entry = _entry_containing(
                registry.entries,
                EXPECTED_MARKERS["hidden_text"],
                required_flag="hidden_text",
            )

            self.assertIsNotNone(entry)
            self.assertTrue(any("Hidden text source node" in warning for warning in entry.warnings))

    def test_comments_are_not_active_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = _write_manifest(root, source_version="comments-v1")

            registry = build_requirements_registry(manifest_path)
            entry = _entry_containing(registry.entries, EXPECTED_MARKERS["comment"])

            self.assertIsNotNone(entry)
            self.assertIn(entry.status, {"source_only", "unclear"})
            self.assertNotEqual("active", entry.status)

    def test_jsonl_can_be_loaded_back(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            out_dir = root / "requirements"
            manifest_path = _write_manifest(root, source_version="load-v1")
            registry = build_requirements_registry(manifest_path)

            registry_path, summary_path = write_requirements_registry(registry, out_dir)
            entries = load_requirements_registry_jsonl(registry_path)
            loaded_registry = load_requirements_registry(registry_path, summary_path)

            self.assertEqual(len(registry.entries), len(entries))
            self.assertEqual(len(entries), len(loaded_registry.entries))
            self.assertEqual("demo-ft", loaded_registry.ft_slug)

    def test_rule_based_active_requirement_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "requirements.docx"
            build_docx_fixture_with_text(
                source_docx,
                "BSR 115 Адрес регистрации обязателен, если Ввести вручную = Нет.",
            )
            out_dir = root / "requirements"
            manifest = build_source_manifest(
                ft_slug="AutoFin",
                source_version="active-v1",
                docx=source_docx,
                out_dir=out_dir,
            )
            manifest_path = write_source_manifest(manifest, out_dir)

            registry = build_requirements_registry(manifest_path)
            entry = _entry_containing(registry.entries, "Адрес регистрации")

            self.assertIsNotNone(entry)
            self.assertEqual("active", entry.status)
            self.assertEqual("requiredness", entry.requirement_type)
            self.assertEqual("BSR 115", entry.source_req_id)
            self.assertEqual(entry.normalized_text, entry.expected_behavior)


def _write_manifest(root: Path, *, source_version: str) -> Path:
    source_docx = root / "sample.docx"
    out_dir = root / "requirements"
    build_docx_fixture(source_docx)
    manifest = build_source_manifest(
        ft_slug="demo-ft",
        source_version=source_version,
        docx=source_docx,
        out_dir=out_dir,
    )
    return write_source_manifest(manifest, out_dir)


def _entry_containing(entries: list[object], text: str, required_flag: str | None = None) -> object:
    for entry in entries:
        if text in entry.normalized_text:
            if required_flag and not any(
                required_flag in anchor.flags for anchor in entry.source_anchors
            ):
                continue
            return entry
    raise AssertionError(f"entry containing {text!r} not found")


def build_docx_fixture_with_text(path: Path, text: str) -> None:
    import zipfile

    entries = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdOfficeDocument" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""",
        "word/document.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>
</w:document>""",
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in entries.items():
            archive.writestr(name, value)


if __name__ == "__main__":
    unittest.main()
