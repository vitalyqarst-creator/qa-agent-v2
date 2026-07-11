from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.prepared_compiler import compile_workflow_package
from test_case_agent.review_cycle.prepared_package import load_prepared_package, load_obligations
from test_case_agent.review_cycle.runtime import StageRuntimeError


class PreparedWorkflowCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ft = self.root / "fts" / "demo"
        (self.ft / "source").mkdir(parents=True)
        (self.ft / "source" / "main.docx").write_bytes(b"docx")
        (self.ft / "source" / "main.xhtml").write_text("<html/>", encoding="utf-8")
        (self.ft / "source" / "main.pdf").write_bytes(b"pdf")
        (self.ft / "source" / "unselected.docx").write_bytes(b"other")
        (self.ft / "source" / "unselected.xhtml").write_text("<html/>", encoding="utf-8")
        self.design = self.ft / "work" / "test-design" / "demo-scope"
        self.design.mkdir(parents=True)
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` |
| `ATOM-002` | `SRC-001.P02` | `GSR 2` | Неизвестен текст ошибки. | `gap` | `GAP-001` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | status |
| --- | --- | --- | --- |
| `ATOM-001` | Проверить все значения. | Отображаются все и только значения DICT-001. | `covered` |
| `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `gap` |
""",
            encoding="utf-8",
        )
        (self.design / "dictionary-inventory.md").write_text(
            """# Dictionary Inventory

| dictionary_id | active_values |
| --- | --- |
| `DICT-001` | `A`; `B` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-gaps.md").write_text(
            """# Coverage Gaps

### GAP-001

**FT Reference:** `GSR 2; SRC-001.P02`
**Impact:** `non-blocking`
**Handling:** Запросить точный текст ошибки.
""",
            encoding="utf-8",
        )
        (self.design / "test-design-applicability-matrix.md").write_text(
            """# Test-design Applicability Matrix

| dimension | applicable |
| --- | --- |
| `field-property` | `yes` |
| `integration` | `no` |
""",
            encoding="utf-8",
        )
        self.state = self.ft / "work" / "stage-handoffs" / "01-demo" / "workflow-state.yaml"
        self.state.parent.mkdir(parents=True)
        (self.state.parent / "source-selection.md").write_text(
            """# Source Selection

| path | role |
| --- | --- |
| `source/main.docx` | `main-ft-docx` |
| `source/main.xhtml` | `main-ft-xhtml` |
| `source/main.pdf` | `main-ft-pdf` |

- xhtml_available: `yes`
- xhtml_matches_main_ft: `yes`
""",
            encoding="utf-8",
        )
        self.state.write_text(
            """ft_slug: demo
scope_slug: demo-scope
canonical_test_cases: test-cases/4.2-demo-scope.md
latest_artifacts:
  source_selection: work/stage-handoffs/01-demo/source-selection.md
  atomic_requirements_ledger: work/test-design/demo-scope/atomic-requirements-ledger.md
  package_test_design_plan: work/test-design/demo-scope/package-test-design-plan.md
  test_design_applicability_matrix: work/test-design/demo-scope/test-design-applicability-matrix.md
  dictionary_inventory: work/test-design/demo-scope/dictionary-inventory.md
  coverage_gaps: work/test-design/demo-scope/coverage-gaps.md
coverage_gaps:
  blocking: 0
  non_blocking: 1
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def compile(self):
        cycle = self.ft / "work" / "review-cycles" / "compiled-cycle"
        return compile_workflow_package(
            workflow_state=self.state,
            repo_root=self.root,
            output_root=cycle / "prepared-input" / "demo-package",
            package_id="demo-package",
            attempt_root=cycle / "attempts" / "writer-r1" / "attempt-001",
            expected_ft_slug="demo",
        )

    def test_compiles_obligations_gaps_dictionaries_and_sources(self) -> None:
        result = self.compile()
        self.assertEqual(result.obligation_count, 2)
        self.assertEqual(result.gap_count, 1)
        self.assertEqual(result.dictionary_ref_count, 1)
        self.assertEqual(result.section_id, "4.2")
        self.assertEqual(result.execution_profile, "simple-field-property")
        self.assertEqual(result.unsupported_dimensions, ())
        package = load_prepared_package(result.stage_package, self.root)
        roles = {item.role for item in package.source_registry}
        self.assertEqual(
            roles, {"source-of-truth", "machine-readable", "structural-cross-check"}
        )
        source_names = {Path(item.path).name for item in package.source_registry}
        self.assertEqual(source_names, {"main.docx", "main.xhtml", "main.pdf"})
        obligation_path = self.root / next(
            item.path for item in package.package_artifacts if item.kind == "atomic-obligations"
        )
        obligations = load_obligations(obligation_path)
        self.assertEqual(obligations.obligations[0].dictionary_refs, ("DICT-001",))
        self.assertEqual(obligations.obligations[1].gap_id, "GAP-001")

    def test_blocks_testable_atom_without_plan_oracle(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "Отображаются все и только значения DICT-001.", "none_required:blocked"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "semantic degradation: ATOM-001"):
            self.compile()

    def test_blocks_missing_dictionary_inventory_entry(self) -> None:
        (self.design / "dictionary-inventory.md").write_text(
            "| dictionary_id | active_values |\n| --- | --- |\n| `DICT-999` | `X` |\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "references missing DICT-001"):
            self.compile()

    def test_blocks_cross_package_ft_slug_switch(self) -> None:
        self.state.write_text(
            self.state.read_text(encoding="utf-8").replace("ft_slug: demo", "ft_slug: other"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "ft_slug mismatch"):
            self.compile()

    def test_blocks_output_outside_expected_ft_cycle(self) -> None:
        with self.assertRaisesRegex(StageRuntimeError, "prepared output escapes"):
            compile_workflow_package(
                workflow_state=self.state,
                repo_root=self.root,
                output_root=self.root / "outside" / "prepared-input" / "demo-package",
                package_id="demo-package",
                attempt_root=(
                    self.ft
                    / "work"
                    / "review-cycles"
                    / "compiled-cycle"
                    / "attempts"
                    / "writer-r1"
                    / "attempt-001"
                ),
                expected_ft_slug="demo",
            )

    def test_blocks_different_output_and_attempt_cycles(self) -> None:
        cycle = self.ft / "work" / "review-cycles"
        with self.assertRaisesRegex(StageRuntimeError, "same cycle"):
            compile_workflow_package(
                workflow_state=self.state,
                repo_root=self.root,
                output_root=cycle / "cycle-a" / "prepared-input" / "demo-package",
                package_id="demo-package",
                attempt_root=cycle / "cycle-b" / "attempts" / "writer-r1" / "attempt-001",
                expected_ft_slug="demo",
            )

    def test_blocks_unknown_coverage_status(self) -> None:
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace("`covered`", "`maybe`", 1),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "unsupported coverage_status"):
            self.compile()

    def test_routes_numeric_scope_out_of_fast_path(self) -> None:
        matrix = self.design / "test-design-applicability-matrix.md"
        matrix.write_text(
            "| dimension | applicable |\n| --- | --- |\n| `numeric` | `yes` |\n",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.execution_profile, "standard-required")
        self.assertEqual(result.unsupported_dimensions, ("numeric-boundaries",))
        package = load_prepared_package(result.stage_package, self.root)
        self.assertEqual(package.execution_profile, "standard-required")
        self.assertEqual(package.unsupported_dimensions, ("numeric-boundaries",))

    def test_blocks_duplicate_workflow_key(self) -> None:
        self.state.write_text(
            self.state.read_text(encoding="utf-8") + "ft_slug: demo\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "duplicate workflow YAML key"):
            self.compile()


if __name__ == "__main__":
    unittest.main()
