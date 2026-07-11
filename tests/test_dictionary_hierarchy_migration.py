from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.migrate_dictionary_hierarchy import migrate


class DictionaryHierarchyMigrationTests(unittest.TestCase):
    def test_splits_duplicate_ids_into_parent_and_children(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dictionary-inventory.md"
            path.write_text(
                """| dictionary_id | dictionary_name | source_file | source_location | extraction_status | active_values | archived_values | used_by_source_properties | gap_id | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DICT-001 | Group A | source/main.xhtml | Appendix 1 | extracted | A1; A2 | - | SRC-001 | - | first |
| DICT-001 | Group B | source/main.xhtml | Appendix 1 | extracted | B1 | - | SRC-001 | - | second |
""",
                encoding="utf-8",
            )

            result = migrate(
                inventory=path,
                dictionary_id="DICT-001",
                parent_name="Parent",
                write=True,
            )

            self.assertEqual(result["status"], "migrated")
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("| DICT-001 |"), 1)
            self.assertIn("DICT-101", text)
            self.assertIn("DICT-102", text)

    def test_normalizes_legacy_dot_child_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dictionary-inventory.md"
            path.write_text(
                """| dictionary_id | dictionary_name | source_file | source_location | extraction_status | active_values | archived_values | used_by_source_properties | gap_id | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DICT-001 | Parent | source/main.xhtml | Appendix 1 | extracted | DICT-001.CAT-001 | - | SRC-001 | - | parent |
| DICT-001.CAT-001 | Group A | source/main.xhtml | Appendix 1 | extracted | A1 | - | SRC-001 | - | child |
""",
                encoding="utf-8",
            )

            result = migrate(
                inventory=path,
                dictionary_id="DICT-001",
                parent_name="Parent",
                write=True,
            )

            self.assertEqual(result["status"], "normalized-child-ids")
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("DICT-001.CAT-", text)
            self.assertIn("DICT-101", text)


if __name__ == "__main__":
    unittest.main()
