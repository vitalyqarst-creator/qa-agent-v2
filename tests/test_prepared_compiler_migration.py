from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.migrate_prepared_compiler_contract import migrate
from test_case_agent.review_cycle.runtime import StageRuntimeError


class PreparedCompilerMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ft = self.root / "fts" / "demo"
        self.design = self.ft / "work" / "test-design" / "scope"
        self.design.mkdir(parents=True)
        (self.design / "atomic-requirements-ledger.md").write_text(
            """| atom_id | atomic_statement | coverage_status |
| --- | --- | --- |
| ATOM-001 | Отображается одно значение. | covered |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """| obligation_id | dimension | source_ref | linked_atom | coverage_status | linked_tc_or_gap | rationale |
| --- | --- | --- | --- | --- | --- | --- |
| CO-001 | single-selection | SRC-001 | ATOM-001 | covered | TC-001 | cardinality |
""",
            encoding="utf-8",
        )
        self.state = self.ft / "work" / "stage-handoffs" / "01-scope" / "compiler-input.yaml"
        self.state.parent.mkdir(parents=True)
        self.state.write_text(
            """ft_slug: demo
scope_slug: scope
latest_artifacts:
  atomic_requirements_ledger: work/test-design/scope/atomic-requirements-ledger.md
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_migrates_recognized_legacy_obligation_table(self) -> None:
        result = migrate(
            workflow_state=self.state,
            repo_root=self.root,
            expected_ft_slug="demo",
            write=True,
        )

        self.assertEqual(result["status"], "migrated")
        state_text = self.state.read_text(encoding="utf-8")
        self.assertIn("prepared_compiler_contract_version: 2", state_text)
        self.assertIn("coverage_obligation_table:", state_text)
        obligations = (self.design / "coverage-obligation-table.md").read_text(encoding="utf-8")
        self.assertIn("linked_atom_id", obligations)
        self.assertIn("OBL-001", obligations)

    def test_blocks_legacy_row_without_known_atom(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace("ATOM-001", "not_applicable"),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "no single known atom"):
            migrate(
                workflow_state=self.state,
                repo_root=self.root,
                expected_ft_slug="demo",
                write=False,
            )


if __name__ == "__main__":
    unittest.main()
