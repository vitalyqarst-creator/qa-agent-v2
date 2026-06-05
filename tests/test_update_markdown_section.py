from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "update_markdown_section.py"
ARTIFACT_WRITER_PATH = ROOT_DIR / "scripts" / "write_artifact_sections.py"


class UpdateMarkdownSectionTests(unittest.TestCase):
    def run_script(
        self,
        *args: str,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=str(ROOT_DIR),
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_creates_missing_file_from_content_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "artifact.md"
            body_file = Path(tmp_dir) / "body.md"
            body_file.write_text("Body row\n", encoding="utf-8")

            result = self.run_script(
                str(target),
                "--heading",
                "Package Test Design Plan",
                "--content-file",
                str(body_file),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "## Package Test Design Plan\n\nBody row\n",
            )

    def test_replaces_existing_section_and_preserves_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "artifact.md"
            body_file = Path(tmp_dir) / "body.md"
            target.write_text(
                "# Artifact\n\n## A\n\nold\n\n## B\n\nkeep\n",
                encoding="utf-8",
            )
            body_file.write_text("new\n", encoding="utf-8")

            result = self.run_script(
                str(target),
                "--heading",
                "A",
                "--content-file",
                str(body_file),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = target.read_text(encoding="utf-8")
            self.assertIn("# Artifact\n\n## A\n\nnew\n\n## B\n\nkeep\n", updated)
            self.assertNotIn("old", updated)

    def test_appends_missing_section_at_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "artifact.md"
            body_file = Path(tmp_dir) / "body.md"
            target.write_text("# Artifact\n\n## A\n\nold\n", encoding="utf-8")
            body_file.write_text("added\n", encoding="utf-8")

            result = self.run_script(
                str(target),
                "--heading",
                "B",
                "--content-file",
                str(body_file),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                target.read_text(encoding="utf-8").endswith("\n## B\n\nadded\n")
            )

    def test_reads_body_from_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "artifact.md"

            result = self.run_script(
                str(target),
                "--heading",
                "Writer Self-Check",
                "--stdin",
                input_text="- checked\n",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "## Writer Self-Check\n\n- checked\n",
            )

    def test_rejects_missing_content_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "artifact.md"

            result = self.run_script(str(target), "--heading", "A")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("one of the arguments", result.stderr)

class WriteArtifactSectionsTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ARTIFACT_WRITER_PATH), *args],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_writes_artifact_from_manifest_and_section_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target = base / "artifact.md"
            preamble = base / "preamble.md"
            section_a = base / "section-a.md"
            section_b = base / "section-b.md"
            manifest = base / "manifest.json"

            preamble.write_text("# Diagnostic\n\nMetadata", encoding="utf-8")
            section_a.write_text("| a | b |\n| --- | --- |\n| 1 | 2 |\n", encoding="utf-8")
            section_b.write_text("- checked\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "target_path": "artifact.md",
                        "preamble_file": "preamble.md",
                        "sections": [
                            {
                                "level": 2,
                                "heading": "Source Table Normalization",
                                "content_file": "section-a.md",
                            },
                            {
                                "level": 2,
                                "heading": "Self-check",
                                "content_file": "section-b.md",
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = self.run_script("--manifest", str(manifest))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "\n".join(
                    [
                        "# Diagnostic",
                        "",
                        "Metadata",
                        "",
                        "## Source Table Normalization",
                        "",
                        "| a | b |",
                        "| --- | --- |",
                        "| 1 | 2 |",
                        "",
                        "## Self-check",
                        "",
                        "- checked",
                        "",
                    ]
                ),
            )

    def test_dry_run_validates_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            section = base / "section.md"
            manifest = base / "manifest.json"
            target = base / "artifact.md"

            section.write_text("body\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "target_path": "artifact.md",
                        "sections": [
                            {
                                "level": 2,
                                "heading": "A",
                                "content_file": "section.md",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_script("--manifest", str(manifest), "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(target.exists())

    def test_rejects_missing_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest = Path(tmp_dir) / "manifest.json"
            manifest.write_text(
                json.dumps({"target_path": "artifact.md", "sections": []}),
                encoding="utf-8",
            )

            result = self.run_script("--manifest", str(manifest))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sections", result.stderr)


if __name__ == "__main__":
    unittest.main()
