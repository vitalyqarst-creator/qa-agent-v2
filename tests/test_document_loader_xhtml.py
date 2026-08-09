from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent import resolve_sections


XHTML_WITH_COMMENTS = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <!-- converter metadata must not become a requirement -->
  <body>
    <!-- comment before scope -->
    <h2>9.1 Меню управления партнерами</h2>
    <ul>
      <li>Группы компаний (ГК)</li>
      <!-- a list comment -->
      <li>Партнеры</li>
    </ul>
    <p>Меню отображает доступные разделы и переключает между ними.</p>
    <ol><li><h2>9.2 Следующая область</h2></li></ol>
  </body>
</html>
"""


class DocumentLoaderXhtmlTests(unittest.TestCase):
    def test_resolve_sections_extracts_xhtml_scope_and_discards_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "requirements.xhtml"
            source.write_text(XHTML_WITH_COMMENTS, encoding="utf-8")

            sections = resolve_sections(source, section_prefix="9.1")

        self.assertEqual(1, len(sections))
        section = sections[0]
        self.assertEqual("9.1", section.section_id)
        self.assertEqual("9.1 Меню управления партнерами", section.title)
        self.assertIn("- Группы компаний (ГК)", section.text)
        self.assertIn("- Партнеры", section.text)
        self.assertIn("Меню отображает доступные разделы", section.text)
        self.assertNotIn("converter metadata", section.text)
        self.assertNotIn("list comment", section.text)
        self.assertNotIn("9.2 Следующая область", section.text)


if __name__ == "__main__":
    unittest.main()
