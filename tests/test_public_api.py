from __future__ import annotations

import unittest
import subprocess
import sys
from pathlib import Path

from test_case_agent import (
    InvalidSourceError,
    NoMatchingSectionsError,
    load_sections,
    preview_chunks,
    resolve_sections,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DOC = next(
    path for path in (ROOT_DIR / "fts").glob("*/source/*.docx") if not path.name.startswith("~$")
)


class PublicApiTests(unittest.TestCase):
    def test_load_sections_returns_sections(self) -> None:
        sections = load_sections(SOURCE_DOC)
        self.assertTrue(sections)
        self.assertTrue(any(section.section_id == "preface" for section in sections))

    def test_resolve_sections_filters_preface_and_limits_results(self) -> None:
        sections = resolve_sections(SOURCE_DOC, max_sections=2)
        self.assertTrue(sections)
        self.assertLessEqual(len(sections), 2)
        self.assertTrue(all(section.section_id != "preface" for section in sections))

    def test_preview_chunks_returns_chunks(self) -> None:
        chunks = preview_chunks(SOURCE_DOC, max_sections=1, max_chars=4000)
        self.assertTrue(chunks)
        self.assertTrue(all(chunk.text for chunk in chunks))

    def test_invalid_source_raises_explicit_error(self) -> None:
        with self.assertRaises(InvalidSourceError):
            load_sections(ROOT_DIR / "missing.docx")

    def test_missing_section_raises_explicit_error(self) -> None:
        with self.assertRaises(NoMatchingSectionsError):
            preview_chunks(SOURCE_DOC, section_prefix="999.999.999")

    def test_import_does_not_emit_pypdf_arc4_warning(self) -> None:
        result = subprocess.run(
            [sys.executable, "-W", "default", "-c", "import test_case_agent"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("ARC4 has been moved", result.stderr)


if __name__ == "__main__":
    unittest.main()
