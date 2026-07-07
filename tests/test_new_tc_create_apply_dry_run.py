from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.new_tc_create_apply_dry_run import (
    NewTcCreateApplyDryRunReport,
    load_new_tc_create_apply_dry_run,
    write_new_tc_create_apply_dry_run,
)
from tests.test_new_tc_stage_9h_design_review_prep import stage_9g_payload, write_json


class NewTcCreateApplyDryRunTests(unittest.TestCase):
    def test_loads_stage_9g_report_and_preserves_no_apply_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "new-tc-create-apply-dry-run-WPKG-000001.json"
            write_json(path, stage_9g_payload())

            report = load_new_tc_create_apply_dry_run(path)

            self.assertIsInstance(report, NewTcCreateApplyDryRunReport)
            self.assertEqual("pass-with-warnings", report.dry_run_status)
            self.assertFalse(report.real_apply_authorized)
            self.assertFalse(report.canonical_write_allowed)
            self.assertEqual(1, len(report.dry_run_items))

    def test_writes_only_json_and_markdown_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.json"
            write_json(source, stage_9g_payload())
            report = load_new_tc_create_apply_dry_run(source)

            json_path, md_path = write_new_tc_create_apply_dry_run(report, root)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            self.assertFalse(list(root.glob("*.patch")))
            self.assertFalse((root / "backups").exists())


if __name__ == "__main__":
    unittest.main()
