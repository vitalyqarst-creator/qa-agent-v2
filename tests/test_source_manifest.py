from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    build_source_manifest,
    compute_file_sha256,
    load_source_manifest,
    write_source_manifest,
)
from tests.test_ooxml_loader import build_docx_fixture


ROOT_DIR = Path(__file__).resolve().parents[1]


class SourceManifestTests(unittest.TestCase):
    def test_manifest_builds_for_generated_docx_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "sample.docx"
            source_pdf = root / "sample.pdf"
            source_xhtml = root / "sample.xhtml"
            support = root / "support.txt"
            build_docx_fixture(source_docx)
            source_pdf.write_bytes(b"%PDF-1.4\n")
            source_xhtml.write_text("<html></html>", encoding="utf-8")
            support.write_text("support", encoding="utf-8")

            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="demo-v1",
                docx=source_docx,
                pdf=source_pdf,
                xhtml=source_xhtml,
                support_files=[support],
                out_dir=root / "requirements",
            )

            self.assertEqual("demo-ft", manifest.ft_slug)
            self.assertEqual("demo-v1", manifest.source_version)
            self.assertEqual("1.0", manifest.manifest_version)
            self.assertEqual("pass-with-warnings", manifest.ingestion_status)
            self.assertEqual([], manifest.blocking_reasons)
            self.assertEqual(str(source_docx), manifest.primary_docx)
            self.assertEqual(str(source_pdf), manifest.primary_pdf)
            self.assertEqual(str(source_xhtml), manifest.primary_xhtml)
            self.assertEqual(4, len(manifest.source_files))
            self.assertTrue(all(entry.exists for entry in manifest.source_files))
            self.assertTrue(all(entry.sha256 for entry in manifest.source_files))
            self.assertEqual("native_ooxml_zip_lxml", manifest.extraction_method)
            self.assertEqual("strict", manifest.parser_mode)
            self.assertIn("word/document.xml", manifest.ooxml_coverage_audit.xml_parts_extracted)
            self.assertEqual(
                sorted([str(source_docx), str(source_pdf), str(source_xhtml), str(support)]),
                manifest.clean_run_audit["files_read"],
            )
            self.assertEqual([], manifest.clean_run_audit["forbidden_files_detected_nearby"])
            self.assertEqual([], manifest.clean_run_audit["forbidden_files_in_inputs"])
            self.assertEqual([], manifest.clean_run_audit["forbidden_files_read"])
            self.assertTrue(manifest.clean_run_audit["clean_run_claim"])
            self.assertEqual("clean", manifest.clean_run_audit["clean_run_status"])

    def test_compute_file_sha256_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "source.txt"
            file_path.write_text("stable content", encoding="utf-8")

            expected = hashlib.sha256(b"stable content").hexdigest()

            self.assertEqual(expected, compute_file_sha256(file_path))
            self.assertEqual(compute_file_sha256(file_path), compute_file_sha256(file_path))

    def test_missing_primary_docx_blocks_ingestion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_docx = Path(temp_dir) / "missing.docx"

            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="missing-v1",
                docx=missing_docx,
                out_dir=Path(temp_dir) / "requirements",
            )

            self.assertEqual("blocked", manifest.ingestion_status)
            self.assertTrue(any("primary_docx is missing" in reason for reason in manifest.blocking_reasons))
            self.assertIsNone(manifest.ooxml_coverage_audit)
            self.assertFalse(manifest.coverage_audit_created)
            docx_entry = next(entry for entry in manifest.source_files if entry.role == "main_docx")
            self.assertFalse(docx_entry.exists)
            self.assertIsNone(docx_entry.sha256)

    def test_binary_parts_are_pass_with_warnings_not_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_docx = Path(temp_dir) / "sample.docx"
            build_docx_fixture(source_docx)

            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="binary-v1",
                docx=source_docx,
                out_dir=Path(temp_dir) / "requirements",
            )

            self.assertEqual("pass-with-warnings", manifest.ingestion_status)
            self.assertEqual([], manifest.blocking_reasons)
            self.assertTrue(
                any("Binary part seen but not content-extracted" in warning for warning in manifest.warnings)
            )
            self.assertGreaterEqual(manifest.ooxml_summary["binary_parts_seen"], 1)

    def test_write_source_manifest_writes_manifest_and_coverage_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "sample.docx"
            out_dir = root / "requirements"
            build_docx_fixture(source_docx)
            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="write-v1",
                docx=source_docx,
                out_dir=out_dir,
            )

            manifest_path = write_source_manifest(manifest, out_dir)
            coverage_path = out_dir / "source-coverage-audit.write-v1.json"

            self.assertTrue(manifest_path.exists())
            self.assertTrue(coverage_path.exists())
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            coverage_payload = json.loads(coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(str(coverage_path), manifest_payload["ooxml_coverage_audit_path"])
            self.assertTrue(manifest_payload["coverage_audit_created"])
            self.assertEqual("native_ooxml_zip_lxml", coverage_payload["extraction_method"])

    def test_load_source_manifest_reads_created_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "sample.docx"
            out_dir = root / "requirements"
            build_docx_fixture(source_docx)
            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="load-v1",
                docx=source_docx,
                out_dir=out_dir,
            )
            manifest_path = write_source_manifest(manifest, out_dir)

            loaded = load_source_manifest(manifest_path)

            self.assertEqual("demo-ft", loaded.ft_slug)
            self.assertEqual("load-v1", loaded.source_version)
            self.assertEqual("pass-with-warnings", loaded.ingestion_status)
            self.assertEqual(str(out_dir / "source-coverage-audit.load-v1.json"), loaded.ooxml_coverage_audit_path)
            self.assertIsNone(loaded.ooxml_coverage_audit)

    def test_cli_creates_manifest_and_coverage_audit_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "sample.docx"
            source_pdf = root / "sample.pdf"
            source_xhtml = root / "sample.xhtml"
            out_dir = root / "requirements"
            build_docx_fixture(source_docx)
            source_pdf.write_bytes(b"%PDF-1.4\n")
            source_xhtml.write_text("<html></html>", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT_DIR / "scripts" / "build_source_manifest.py"),
                    "--ft-slug",
                    "demo-ft",
                    "--source-version",
                    "cli-v1",
                    "--docx",
                    str(source_docx),
                    "--pdf",
                    str(source_pdf),
                    "--xhtml",
                    str(source_xhtml),
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
            manifest_path = out_dir / "source-manifest.cli-v1.json"
            coverage_path = out_dir / "source-coverage-audit.cli-v1.json"
            self.assertEqual(str(manifest_path), payload["manifest_path"])
            self.assertEqual(str(coverage_path), payload["coverage_audit_path"])
            self.assertEqual("pass-with-warnings", payload["ingestion_status"])
            self.assertTrue(manifest_path.exists())
            self.assertTrue(coverage_path.exists())
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(str(coverage_path), manifest_payload["ooxml_coverage_audit_path"])
            self.assertEqual(
                sorted([str(source_docx), str(source_pdf), str(source_xhtml)]),
                manifest_payload["clean_run_audit"]["files_read"],
            )
            self.assertIn(str(source_docx), payload["source_file_hashes"])

    def test_manifest_records_nearby_forbidden_file_as_contaminated_risk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "sample.docx"
            forbidden_file = root / "expected_answer.txt"
            build_docx_fixture(source_docx)
            forbidden_file.write_text("not read", encoding="utf-8")

            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="clean-v1",
                docx=source_docx,
                out_dir=root / "requirements",
            )

            self.assertEqual([str(source_docx)], manifest.clean_run_audit["files_read"])
            self.assertEqual([], manifest.clean_run_audit["forbidden_files_read"])
            self.assertEqual([], manifest.clean_run_audit["forbidden_files_in_inputs"])
            self.assertEqual([str(forbidden_file)], manifest.clean_run_audit["forbidden_files_detected_nearby"])
            self.assertFalse(manifest.clean_run_audit["clean_run_claim"])
            self.assertEqual("contaminated-risk", manifest.clean_run_audit["clean_run_status"])

    def test_manifest_records_forbidden_input_as_contaminated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_docx = root / "sample.docx"
            forbidden_support = root / "expected_answer.txt"
            build_docx_fixture(source_docx)
            forbidden_support.write_text("read for sha256", encoding="utf-8")

            manifest = build_source_manifest(
                ft_slug="demo-ft",
                source_version="contaminated-v1",
                docx=source_docx,
                support_files=[forbidden_support],
                out_dir=root / "requirements",
            )

            self.assertEqual(
                sorted([str(source_docx), str(forbidden_support)]),
                manifest.clean_run_audit["files_read"],
            )
            self.assertEqual([str(forbidden_support)], manifest.clean_run_audit["forbidden_files_in_inputs"])
            self.assertEqual([str(forbidden_support)], manifest.clean_run_audit["forbidden_files_read"])
            self.assertEqual([str(forbidden_support)], manifest.clean_run_audit["forbidden_files_detected_nearby"])
            self.assertFalse(manifest.clean_run_audit["clean_run_claim"])
            self.assertEqual("contaminated", manifest.clean_run_audit["clean_run_status"])


if __name__ == "__main__":
    unittest.main()
