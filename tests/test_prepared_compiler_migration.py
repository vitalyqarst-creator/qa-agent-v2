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
            """| atom_id | source_row_id | requirement_codes | atomic_statement | coverage_status |
| --- | --- | --- | --- | --- |
| ATOM-001 | SRC-001.P01 | GSR 1 | Отображается одно значение. | covered |
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
        for name in (
            "source-row-inventory.md",
            "source-row-extraction-spec.json",
            "source-row-baseline.json",
            "coverage-gaps.md",
        ):
            (self.design / name).write_text("{}\n", encoding="utf-8")
        (self.design / "source-assertions.json").write_text(
            '{"version":4}\n', encoding="utf-8"
        )
        (self.design / "source-assertion-review.json").write_text(
            '{"version":6}\n', encoding="utf-8"
        )
        self.state = self.ft / "work" / "stage-handoffs" / "01-scope" / "compiler-input.yaml"
        self.state.parent.mkdir(parents=True)
        self.state.write_text(
            """ft_slug: demo
scope_slug: scope
latest_artifacts:
  atomic_requirements_ledger: work/test-design/scope/atomic-requirements-ledger.md
  source_row_inventory: work/test-design/scope/source-row-inventory.md
  source_row_extraction_spec: work/test-design/scope/source-row-extraction-spec.json
  source_row_baseline: work/test-design/scope/source-row-baseline.json
  source_assertions: work/test-design/scope/source-assertions.json
  source_assertion_review: work/test-design/scope/source-assertion-review.json
  coverage_gaps: work/test-design/scope/coverage-gaps.md
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
        self.assertIn("prepared_compiler_contract_version: 3", state_text)
        self.assertIn("coverage_obligation_table:", state_text)
        obligations = (self.design / "coverage-obligation-table.md").read_text(encoding="utf-8")
        self.assertIn("linked_atom_id", obligations)
        self.assertIn("source_row_id", obligations)
        self.assertIn("requirement_codes", obligations)
        self.assertIn("OBL-001", obligations)

    def test_blocks_migration_when_v3_ledger_traceability_columns_are_missing(self) -> None:
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            """| atom_id | atomic_statement | coverage_status |
| --- | --- | --- |
| ATOM-001 | Отображается одно значение. | covered |
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "missing v3 canonical columns"):
            migrate(
                workflow_state=self.state,
                repo_root=self.root,
                expected_ft_slug="demo",
                write=False,
            )

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

    def test_blocks_v3_migration_without_reviewed_source_artifacts(self) -> None:
        (self.design / "source-assertion-review.json").unlink()

        with self.assertRaisesRegex(
            StageRuntimeError, "migrator will not invent them"
        ):
            migrate(
                workflow_state=self.state,
                repo_root=self.root,
                expected_ft_slug="demo",
                write=False,
            )

    def test_blocks_legacy_manifest_and_receipt_versions(self) -> None:
        (self.design / "source-assertions.json").write_text(
            '{"version":2}\n', encoding="utf-8"
        )
        (self.design / "source-assertion-review.json").write_text(
            '{"version":4}\n', encoding="utf-8"
        )

        with self.assertRaisesRegex(StageRuntimeError, "rematerialized as v4"):
            migrate(
                workflow_state=self.state,
                repo_root=self.root,
                expected_ft_slug="demo",
                write=False,
            )


if __name__ == "__main__":
    unittest.main()
