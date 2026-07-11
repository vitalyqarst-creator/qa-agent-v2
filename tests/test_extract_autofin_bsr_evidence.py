from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from docx import Document

from scripts.extract_autofin_bsr_evidence import code_pattern, extract_docx


class ExtractAutoFinBsrEvidenceTests(unittest.TestCase):
    def test_docx_semantic_row_can_be_matched_by_xhtml_anchor_without_bsr_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.docx"
            document = Document()
            table = document.add_table(rows=1, cols=2)
            table.rows[0].cells[0].text = "Calculator summary"
            table.rows[0].cells[1].text = "Semantic statement without code"
            document.save(path)

            matches = extract_docx(
                path,
                code_pattern([43]),
                {"Calculator summary"},
            )

        self.assertEqual(1, len(matches))
        self.assertEqual("Calculator summary", matches[0]["anchor"])


if __name__ == "__main__":
    unittest.main()
