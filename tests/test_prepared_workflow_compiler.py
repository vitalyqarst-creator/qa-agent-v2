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
        self.state = self.ft / "work" / "stage-handoffs" / "01-demo" / "workflow-state.yaml"
        self.state.parent.mkdir(parents=True)
        self.state.write_text(
            """ft_slug: demo
scope_slug: demo-scope
canonical_test_cases: test-cases/4.2-demo-scope.md
latest_artifacts:
  atomic_requirements_ledger: work/test-design/demo-scope/atomic-requirements-ledger.md
  package_test_design_plan: work/test-design/demo-scope/package-test-design-plan.md
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
        )

    def test_compiles_obligations_gaps_dictionaries_and_sources(self) -> None:
        result = self.compile()
        self.assertEqual(result.obligation_count, 2)
        self.assertEqual(result.gap_count, 1)
        self.assertEqual(result.dictionary_ref_count, 1)
        self.assertEqual(result.section_id, "4.2")
        package = load_prepared_package(result.stage_package, self.root)
        roles = {item.role for item in package.source_registry}
        self.assertEqual(roles, {"source-of-truth", "machine-readable"})
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


if __name__ == "__main__":
    unittest.main()
