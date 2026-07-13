from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.prepared_compiler import (
    PreparedCompilerDiagnostic,
    compile_workflow_package,
)
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

| atom_id | source_property_id | source_ref | atomic_statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` |
| `ATOM-002` | `SRC-001.P02` | `GSR 2` | Неизвестен текст ошибки. | `gap` | `GAP-001` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- |
| `ATOM-001` | Проверить все значения. | Отображаются все и только значения DICT-001. | `TC-001` | `covered` |
| `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-values-shown` | Отображаются все и только значения DICT-001. | `GSR 1; SRC-001.P01; DICT-001` | `TC-001` | `covered` | `-` |
| `OBL-002` | `WP-01` | `SRC-001.P02` | `ATOM-002` | `expected-result` | `unknown-error-text` | Не создавать негативный кейс до уточнения. | `GSR 2; SRC-001.P02` | `GAP-001` | `gap` | `-` |
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
prepared_compiler_contract_version: 2
scope_slug: demo-scope
canonical_test_cases: test-cases/4.2-demo-scope.md
latest_artifacts:
  source_selection: work/stage-handoffs/01-demo/source-selection.md
  atomic_requirements_ledger: work/test-design/demo-scope/atomic-requirements-ledger.md
  coverage_obligation_table: work/test-design/demo-scope/coverage-obligation-table.md
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

    def configure_reset_plan(
        self,
        *,
        property_type: str,
        include_state_contract: bool,
        state_relation: str = "different-from-captured-initial",
    ) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace(
                "| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-values-shown` |",
                f"| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `{property_type}` | `clear-state` |",
            ),
            encoding="utf-8",
        )
        if not include_state_contract:
            return
        (self.design / "package-test-design-plan.md").write_text(
            f"""# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | coverage_class | initial_state_capture | changed_state_setup | pre_action_state_oracle | state_relation | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Нажать `Очистить` после подготовки изменённого состояния. | Состояние совпадает с зафиксированным исходным. | `changed-state` | `{property_type}` | Зафиксировать видимое исходное состояние. | Выбрать видимое состояние, отличное от зафиксированного исходного. | До `Очистить` видимое состояние отличается от зафиксированного исходного. | `{state_relation}` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

    def write_grouped_plan(
        self,
        *,
        shared_plan: bool = True,
        second_package: str = "WP-01",
        second_property: str = "SRC-001.P02",
        justification: str = "",
    ) -> None:
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | atomic_statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1` | Поле доступно для редактирования. | `covered` | `TC-GROUP-001` |
| `ATOM-002` | `SRC-001.P02` | `GSR 1` | Поле принимает строковое значение. | `covered` | `TC-GROUP-001` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            f"""# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `editability` | `editable` | Поле доступно для редактирования. | `GSR 1; SRC-001.P01` | `TC-GROUP-001` | `covered` | `{justification}` |
| `OBL-002` | `{second_package}` | `{second_property}` | `ATOM-002` | `field-property` | `string-value` | Поле принимает строковое значение. | `GSR 1; {second_property}` | `TC-GROUP-001` | `covered` | `{justification}` |
""",
            encoding="utf-8",
        )
        plan_rows = (
            "| `PLAN-001` | `WP-01` | `ATOM-001; ATOM-002` | Ввести значение `Тест`. | Значение `Тест` отображается. | `synthetic-valid-text:Тест` | `TC-GROUP-001` | `covered` |\n"
            if shared_plan
            else (
                "| `PLAN-001` | `WP-01` | `ATOM-001` | Ввести значение `Тест`. | Значение `Тест` отображается. | `synthetic-valid-text:Тест` | `TC-GROUP-001` | `covered` |\n"
                "| `PLAN-002` | `WP-01` | `ATOM-002` | Ввести значение `Строка`. | Значение `Строка` отображается. | `synthetic-valid-text:Строка` | `TC-GROUP-001` | `covered` |\n"
            )
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| design_item_id | package_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
"""
            + plan_rows,
            encoding="utf-8",
        )
        (self.design / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\nNo gaps.\n", encoding="utf-8"
        )

    def enable_decision_table(self, *, atom_001_tc: str = "TC-001") -> None:
        (self.design / "test-design-decision-table.md").write_text(
            f"""# Test Design Decision Table

| decision_id | linked_atom_id | planned_tc_or_gap |
| --- | --- | --- |
| `DD-001` | `ATOM-001` | `{atom_001_tc}` |
| `DD-002` | `ATOM-002` | `GAP-001` |
""",
            encoding="utf-8",
        )
        text = self.state.read_text(encoding="utf-8")
        text = text.replace(
            "  test_design_applicability_matrix: work/test-design/demo-scope/test-design-applicability-matrix.md\n",
            "  test_design_applicability_matrix: work/test-design/demo-scope/test-design-applicability-matrix.md\n"
            "  test_design_decision_table: work/test-design/demo-scope/test-design-decision-table.md\n",
        )
        self.state.write_text(text, encoding="utf-8")

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
        self.assertEqual(
            [(item.obligation_id, item.atom_id) for item in obligations.obligations],
            [("OBL-001", "ATOM-001"), ("OBL-002", "ATOM-002")],
        )
        self.assertEqual("TC-001", obligations.obligations[0].planned_test_case_id)
        self.assertEqual("", obligations.obligations[1].planned_test_case_id)
        self.assertEqual(obligations.obligations[0].dictionary_refs, ("DICT-001",))
        dictionary_requirement = obligations.obligations[0].dictionary_requirements[0]
        self.assertEqual("all-leaf-values", dictionary_requirement.coverage_mode)
        self.assertEqual(
            ["A", "B"],
            [item.value for item in dictionary_requirement.required_values],
        )
        self.assertEqual(obligations.obligations[1].gap_id, "GAP-001")
        instructions = (result.stage_package.parent / "stage-instructions.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("sandbox_policy: `read_only`", instructions)
        self.assertIn("command_budget: `0`", instructions)
        self.assertIn("runner alone materializes", instructions)
        source_evidence = (result.stage_package.parent / "source-evidence.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "- OBL-001: property=SRC-001.P01 | source=GSR 1; SRC-001.P01; DICT-001",
            source_evidence,
        )
        self.assertNotIn("## OBL-001", source_evidence)

    def test_preserves_bsr_and_dit_requirement_codes_in_obligation_source_refs(self) -> None:
        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_path.write_text(
            ledger_path.read_text(encoding="utf-8").replace(
                "`GSR 1; DICT-001`", "`BSR 32; DIT 7; DICT-001`"
            ),
            encoding="utf-8",
        )
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "`GSR 1; SRC-001.P01; DICT-001`",
                "`BSR 32; DIT 7; SRC-001.P01; DICT-001`",
            ),
            encoding="utf-8",
        )

        result = self.compile()

        obligation_path = self.root / next(
            item.path
            for item in load_prepared_package(result.stage_package, self.root).package_artifacts
            if item.kind == "atomic-obligations"
        )
        compiled = load_obligations(obligation_path).obligations[0]
        self.assertIn("BSR 32", compiled.source_refs)
        self.assertIn("DIT 7", compiled.source_refs)

    def test_blocks_v2_like_pagination_reset_without_changed_prestate_contract(self) -> None:
        self.configure_reset_plan(
            property_type="pagination-reset",
            include_state_contract=False,
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            self.compile()

        self.assertEqual(
            "state-change-precondition-incomplete",
            raised.exception.code,
        )
        self.assertIn(
            "pre_action_state_oracle",
            raised.exception.details[0]["missing_or_invalid_fields"],
        )

    def test_blocks_row_selection_reset_with_wrong_changed_state_relation(self) -> None:
        self.configure_reset_plan(
            property_type="row-selection-reset",
            include_state_contract=True,
            state_relation="same-as-captured-initial",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            self.compile()

        self.assertEqual(
            "state-change-precondition-incomplete",
            raised.exception.code,
        )
        self.assertIn(
            "state_relation=different-from-captured-initial",
            raised.exception.details[0]["missing_or_invalid_fields"],
        )

    def test_preserves_changed_prestate_contract_for_pagination_reset(self) -> None:
        self.configure_reset_plan(
            property_type="pagination-reset",
            include_state_contract=True,
        )

        result = self.compile()
        compiled = load_obligations(
            result.stage_package.parent / "atomic-obligations.json"
        ).obligations[0]

        self.assertEqual("reset-to-captured-initial", compiled.execution_semantics)
        self.assertEqual(
            "different-from-captured-initial",
            compiled.state_change.relation,
        )
        self.assertIn("Before the target action verify", compiled.test_intent)

    def test_preserves_changed_prestate_contract_for_row_selection_reset(self) -> None:
        self.configure_reset_plan(
            property_type="row-selection-reset",
            include_state_contract=True,
        )

        result = self.compile()
        compiled = load_obligations(
            result.stage_package.parent / "atomic-obligations.json"
        ).obligations[0]

        self.assertEqual("reset-to-captured-initial", compiled.execution_semantics)
        self.assertEqual(
            "different-from-captured-initial",
            compiled.state_change.relation,
        )

    def test_accepts_aligned_optional_decision_table_mapping(self) -> None:
        self.enable_decision_table()

        result = self.compile()

        self.assertEqual(result.obligation_count, 2)

    def test_blocks_stale_decision_table_mapping(self) -> None:
        self.enable_decision_table(atom_001_tc="TC-STALE-001")

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            self.compile()

        self.assertEqual(raised.exception.code, "tc-mapping-inconsistency")
        self.assertTrue(
            any(
                item["mapping_artifact_kind"] == "test-design-decision-table"
                and item["atom_id"] == "ATOM-001"
                for item in raised.exception.details
            )
        )

    def test_blocks_obligation_mapping_drift_from_ledger(self) -> None:
        path = self.design / "coverage-obligation-table.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("TC-001", "TC-STALE-001"),
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            self.compile()

        self.assertEqual(raised.exception.code, "tc-mapping-inconsistency")
        self.assertTrue(
            any(
                item["mapping_artifact_kind"] == "coverage-obligation-table"
                for item in raised.exception.details
            )
        )

    def test_blocks_plan_mapping_drift_from_ledger(self) -> None:
        path = self.design / "package-test-design-plan.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("TC-001", "TC-STALE-001"),
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            self.compile()

        self.assertEqual(raised.exception.code, "tc-mapping-inconsistency")
        self.assertTrue(
            any(
                item["mapping_artifact_kind"] == "package-test-design-plan"
                for item in raised.exception.details
            )
        )

    def test_embeds_mandatory_package_notes_in_prepared_evidence(self) -> None:
        (self.ft / "AGENT-NOTES.md").write_text(
            "# Package notes\n\nPACKAGE-NOTE-SENTINEL\n",
            encoding="utf-8",
        )

        result = self.compile()

        package = load_prepared_package(result.stage_package, self.root)
        evidence_path = self.root / next(
            item.path for item in package.package_artifacts if item.kind == "source-evidence"
        )
        evidence = evidence_path.read_text(encoding="utf-8")
        self.assertIn("## Mandatory package context", evidence)
        self.assertIn("fts/demo/AGENT-NOTES.md", evidence)
        self.assertIn("PACKAGE-NOTE-SENTINEL", evidence)

    def test_blocks_input_plan_without_concrete_fixture_before_package_build(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Ввести допустимое значение в поле. | Значение отображается в поле. | `valid-text` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("input-fixture-required", context.exception.code)
        self.assertEqual("ATOM-001", context.exception.details[0]["atom_id"])
        self.assertEqual("PLAN-001", context.exception.details[0]["id"])

    def test_accepts_input_plan_with_inline_synthetic_fixture(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Ввести синтетическое значение `Тест` в поле. | Значение `Тест` отображается в поле. | `synthetic-valid-text:Тест` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual("simple-field-property", result.execution_profile)

    def test_accepts_runtime_selected_provider_fixture_for_ft_first_draft(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Ввести синтетический префикс и выбрать фактически возвращённую подсказку с известным полом. | Видимое значение поля совпадает со значением выбранной подсказки. | `runtime-selected:provider-suggestion-with-known-gender` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual("simple-field-property", result.execution_profile)

    def test_blocks_environment_bound_fixture_before_package_build(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

- `FIX-001`: stand-registered application record.

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Ввести значение из `FIX-001`. | Значение отображается. | `fixture-id:FIX-001` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("environment-bound-fixture", context.exception.code)

    def test_blocks_generic_named_fixture_before_package_build(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Ввести значение из валидной заявки. | Значение отображается. | `fixture:валидная заявка` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("generic-execution-fixture", context.exception.code)

    def test_blocks_undefined_scenario_action_before_package_build(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        text = plan.read_text(encoding="utf-8").replace(
            "Проверить все значения.",
            "Попытаться продолжить сценарий.",
        )
        plan.write_text(text, encoding="utf-8")

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("undefined-execution-action", context.exception.code)

    def test_blocks_requiredness_oracle_without_evidence_capture(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        text = obligations.read_text(encoding="utf-8").replace(
            "| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` |",
            "| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `requiredness` |",
        ).replace(
            "Отображаются все и только значения DICT-001.",
            "Поле обязательно; точная UI-реакция не определена.",
        )
        obligations.write_text(text, encoding="utf-8")

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("non-observable-execution-oracle", context.exception.code)

    def test_obligation_intent_uses_only_its_exact_planned_tc_rows(self) -> None:
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | atomic_statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1` | Поле отображается и обязательно. | `covered` | `TC-001; TC-002` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `field-property` | `visible` | Поле отображается. | `GSR 1; SRC-001.P01` | `TC-001` | `covered` | `-` |
| `OBL-002` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `requiredness` | `required` | Evidence содержит control/action/empty/post-state/persistence. | `GSR 1; SRC-001.P01` | `TC-002` | `covered` | `-` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

- `FIX-001`: portable synthetic source-backed card with the target field present.

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Открыть карточку и проверить поле. | Поле отображается. | `n/a` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-001` | По `FIX-001` очистить поле и записать evidence. | Evidence записан. | `fixture-id:FIX-001` | `TC-002` | `covered` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\nNo gaps.\n", encoding="utf-8"
        )

        result = self.compile()
        obligations = load_obligations(
            result.stage_package.parent / "atomic-obligations.json"
        ).obligations

        self.assertEqual(
            [
                "Открыть карточку и проверить поле.",
                "По `FIX-001` очистить поле и записать evidence.",
            ],
            [item.test_intent for item in obligations],
        )

    def test_blocks_named_fixture_without_inline_contract(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | По `FIX-404` ввести значение. | Значение отображается. | `fixture-id:FIX-404` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("missing-fixture-contract", context.exception.code)

    def test_accepts_one_shared_plan_row_for_grouped_obligations(self) -> None:
        self.write_grouped_plan()

        result = self.compile()

        obligations = load_obligations(result.stage_package.parent / "atomic-obligations.json")
        self.assertEqual(
            ["TC-GROUP-001", "TC-GROUP-001"],
            [item.planned_test_case_id for item in obligations.obligations],
        )

    def test_rejects_accidental_shared_tc_id_without_one_shared_plan_row(self) -> None:
        self.write_grouped_plan(shared_plan=False)

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("invalid-planned-test-case-group", context.exception.code)
        self.assertIn("exactly one shared design-plan row", str(context.exception))

    def test_rejects_group_with_conflicting_fixture_rows(self) -> None:
        self.write_grouped_plan(shared_plan=False)

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        detail = context.exception.details[0]
        self.assertEqual("invalid-planned-test-case-group", context.exception.code)
        self.assertEqual("TC-GROUP-001", detail["planned_test_case_id"])

    def test_rejects_grouping_different_fields_without_justification(self) -> None:
        self.write_grouped_plan(second_property="SRC-002.P01")

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("invalid-planned-test-case-group", context.exception.code)
        self.assertIn("cross-field", str(context.exception))

    def test_rejects_grouping_different_packages_without_justification(self) -> None:
        self.write_grouped_plan(second_package="WP-02")

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("invalid-planned-test-case-group", context.exception.code)
        self.assertIn("cross-field or cross-package", str(context.exception))

    def test_allows_cross_field_group_with_explicit_justification(self) -> None:
        self.write_grouped_plan(
            second_property="SRC-002.P01",
            justification="grouping-justification: one observable scenario action",
        )

        result = self.compile()

        self.assertEqual(2, result.obligation_count)

    def test_fast_profile_keeps_strict_32k_compiled_evidence_limit(self) -> None:
        (self.ft / "AGENT-NOTES.md").write_text(
            "# Oversized notes\n\n" + ("X" * 34000),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "compiled evidence exceeds 32768 bytes for simple-field-property",
        ):
            self.compile()

    def test_standard_routing_package_allows_mandatory_context_up_to_48k(self) -> None:
        (self.ft / "AGENT-NOTES.md").write_text(
            "# Large mandatory notes\n\n" + ("X" * 34000),
            encoding="utf-8",
        )
        (self.design / "test-design-applicability-matrix.md").write_text(
            """# Test-design Applicability Matrix

| dimension | applicable |
| --- | --- |
| `field-property` | `yes` |
| `dependency` | `yes` |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual("standard-required", result.execution_profile)
        self.assertIn("dependency-state", result.unsupported_dimensions)
        instructions = (result.stage_package.parent / "stage-instructions.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("scenario: `writer.session_initial_draft`", instructions)
        self.assertIn("## Structured Standard Path", instructions)
        self.assertIn("command_budget: `0`", instructions)
        self.assertNotIn("## Fast Path", instructions)

    def test_blocks_testable_atom_without_plan_oracle(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace(
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

    def test_keeps_gap_linked_unclear_dimension_out_of_unsupported_route(self) -> None:
        matrix = self.design / "test-design-applicability-matrix.md"
        matrix.write_text(
            """| dimension | applicable | linked_atom_or_gap |
| --- | --- | --- |
| `default value` | `yes` | `ATOM-001` |
| `integration/API/internal effects` | `unclear` | `ATOM-002; GAP-001` |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.execution_profile, "simple-field-property")
        self.assertEqual(result.unsupported_dimensions, ())

    def test_loads_table_shaped_coverage_gap(self) -> None:
        gaps = self.design / "coverage-gaps.md"
        gaps.write_text(
            """| gap_id | source_ref | gap_statement | severity | downstream_handling |
| --- | --- | --- | --- | --- |
| `GAP-001` | `SRC-001; GSR 2` | Неизвестен текст ошибки. | `non-blocking` | Не создавать негативный кейс. |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.gap_count, 1)

    def test_routes_unclear_limited_dimension_to_standard(self) -> None:
        matrix = self.design / "test-design-applicability-matrix.md"
        matrix.write_text(
            "| dimension | applicable |\n| --- | --- |\n| `default value` | `unclear-limited` |\n",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.execution_profile, "standard-required")
        self.assertEqual(result.unsupported_dimensions, ("limited-default-oracle",))

    def test_loads_titled_gap_heading_with_field_value_table(self) -> None:
        gaps = self.design / "coverage-gaps.md"
        gaps.write_text(
            """## GAP-001 - Неизвестен Текст Ошибки

| field | value |
| --- | --- |
| source | `SRC-001; GSR 2` |
| statement | Неизвестен текст ошибки. |
| handling | Не создавать негативный кейс. |
| status | `non-blocking` |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.gap_count, 1)

    def test_preserves_non_blocking_constraint_gap_on_testable_atom(self) -> None:
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "| atom_id | source_property_id | source_ref | atomic_statement | coverage_status | covered_by_tc |",
                "| atom_id | source_property_id | source_ref | atomic_statement | coverage_status | covered_by_tc | constraint_gap_ids |",
            ).replace(
                "| --- | --- | --- | --- | --- | --- |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                1,
            ).replace(
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` |",
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` | `GAP-001` |",
            ).replace(
                "| `ATOM-002` | `SRC-001.P02` | `GSR 2` | Неизвестен текст ошибки. | `gap` | `GAP-001` |",
                "| `ATOM-002` | `SRC-001.P02` | `GSR 2` | Неизвестен текст ошибки. | `gap` | `GAP-001` | `-` |",
            ),
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.gap_count, 1)

    def test_blocks_missing_constraint_gap(self) -> None:
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "| atom_id | source_property_id | source_ref | atomic_statement | coverage_status | covered_by_tc |",
                "| atom_id | source_property_id | source_ref | atomic_statement | coverage_status | covered_by_tc | constraint_gap_ids |",
            ).replace(
                "| --- | --- | --- | --- | --- | --- |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                1,
            ).replace(
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` |",
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` | `GAP-999` |",
            ).replace(
                "| `ATOM-002` | `SRC-001.P02` | `GSR 2` | Неизвестен текст ошибки. | `gap` | `GAP-001` |",
                "| `ATOM-002` | `SRC-001.P02` | `GSR 2` | Неизвестен текст ошибки. | `gap` | `GAP-001` | `-` |",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "constraint gap is missing"):
            self.compile()

    def test_blocks_duplicate_workflow_key(self) -> None:
        self.state.write_text(
            self.state.read_text(encoding="utf-8") + "ft_slug: demo\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "duplicate workflow YAML key"):
            self.compile()

    def test_blocks_missing_compiler_contract_version(self) -> None:
        self.state.write_text(
            self.state.read_text(encoding="utf-8").replace(
                "prepared_compiler_contract_version: 2\n", ""
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "migrate_prepared_compiler_contract"):
            self.compile()

    def test_blocks_duplicate_coverage_obligation(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        lines = obligations.read_text(encoding="utf-8").splitlines()
        lines.append(lines[-1])
        obligations.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(StageRuntimeError, "duplicate coverage obligation OBL-002"):
            self.compile()

    def test_blocks_obligation_link_to_unknown_atom(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace("`ATOM-002`", "`ATOM-999`"),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "references unknown atom ATOM-999"):
            self.compile()

    def test_blocks_atom_without_coverage_obligation(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        lines = obligations.read_text(encoding="utf-8").splitlines()
        obligations.write_text(
            "\n".join(line for line in lines if "`OBL-002`" not in line) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            PreparedCompilerDiagnostic,
            "rows have no coverage obligation: ATOM-002",
        ) as caught:
            self.compile()

        self.assertEqual(caught.exception.code, "atom-without-obligation")
        self.assertEqual(caught.exception.details[0]["id"], "ATOM-002")
        self.assertEqual(caught.exception.details[0]["line"], 6)
        self.assertTrue(
            str(caught.exception.details[0]["artifact"]).endswith(
                "atomic-requirements-ledger.md"
            )
        )

    def test_evidence_qualified_atom_status_routes_standard(self) -> None:
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` |",
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; DICT-001` | Поле использует фиксированный список DICT-001. | `covered_with_fixture_evidence` | `TC-001` |",
            ),
            encoding="utf-8",
        )
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "| `PLAN-001` | `ATOM-001` | Проверить полный список значений. | Отображены все активные значения. | `TC-001` | `covered` |",
                "| `PLAN-001` | `ATOM-001` | Проверить полный список значений. | Отображены все активные значения. | `TC-001` | `covered_with_fixture_evidence` |",
            ),
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.execution_profile, "standard-required")
        self.assertIn("evidence-qualified-fixture-evidence", result.unsupported_dimensions)

    def test_compiled_evidence_deduplicates_atom_and_plan_rows(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        lines = obligations.read_text(encoding="utf-8").splitlines()
        first = next(line for line in lines if "`OBL-001`" in line)
        lines.append(first.replace("`OBL-001`", "`OBL-003`"))
        obligations.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = self.compile()
        evidence = (result.stage_package.parent / "source-evidence.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(evidence.count("- OBL-001:"), 1)
        self.assertEqual(evidence.count("- OBL-003:"), 1)
        self.assertEqual(evidence.count("- atom: ATOM-001"), 1)
        self.assertEqual(evidence.count("check=Проверить все значения."), 1)

    def test_blocks_atom_and_obligation_gap_mismatch(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace(
                "| `GAP-001` | `gap` |", "| `GAP-999` | `gap` |"
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "link different GAP ids"):
            self.compile()

    def test_ignores_closed_gap_rows(self) -> None:
        gaps = self.design / "coverage-gaps.md"
        gaps.write_text(
            gaps.read_text(encoding="utf-8")
            + """

| gap_id | status | source_ref | gap_statement | downstream_handling |
| --- | --- | --- | --- | --- |
| `GAP-002` | `closed-by-tc` | `SRC-001` | Historical limitation. | No action. |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.gap_count, 1)

    def test_expands_dictionary_child_hierarchy_into_evidence(self) -> None:
        inventory = self.design / "dictionary-inventory.md"
        inventory.write_text(
            """| dictionary_id | active_values |
| --- | --- |
| `DICT-001` | `DICT-001.CAT-001` |
| `DICT-001.CAT-001` | `A`; `B` |
""",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.dictionary_ref_count, 2)

    def test_compiles_full_dictionary_hierarchy_into_obligation_contract(self) -> None:
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "`dictionary-values-shown`",
                "`dictionary-hierarchy-shown`",
                1,
            ),
            encoding="utf-8",
        )
        inventory = self.design / "dictionary-inventory.md"
        inventory.write_text(
            """| dictionary_id | dictionary_name | active_values |
| --- | --- | --- |
| `DICT-001` | `Корневой справочник` | `DICT-101` |
| `DICT-101` | `Группа один` | `Значение A`; `Значение B` |
""",
            encoding="utf-8",
        )

        result = self.compile()
        package = load_prepared_package(result.stage_package, self.root)
        obligation_path = self.root / next(
            item.path
            for item in package.package_artifacts
            if item.kind == "atomic-obligations"
        )
        requirement = load_obligations(obligation_path).obligations[0].dictionary_requirements[0]

        self.assertEqual("full-hierarchy", requirement.coverage_mode)
        self.assertEqual(
            [
                ("group", ("DICT-001", "DICT-101"), "Группа один"),
                ("leaf", ("DICT-001", "DICT-101"), "Значение A"),
                ("leaf", ("DICT-001", "DICT-101"), "Значение B"),
            ],
            [
                (item.value_kind, item.hierarchy_path, item.value)
                for item in requirement.required_values
            ],
        )

    def test_preserves_source_backed_ui_calibration_without_gap(self) -> None:
        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_path.write_text(
            ledger_path.read_text(encoding="utf-8").replace(
                "| `covered` | `TC-001` |",
                "| `covered_with_ui_calibration` | `TC-001` |",
                1,
            ),
            encoding="utf-8",
        )

        result = self.compile()
        package = load_prepared_package(result.stage_package, self.root)
        obligation_path = self.root / next(
            item.path
            for item in package.package_artifacts
            if item.kind == "atomic-obligations"
        )
        obligation = load_obligations(obligation_path).obligations[0]

        self.assertEqual("ui-calibration-required", obligation.calibration_status)
        self.assertEqual((), obligation.constraint_gap_ids)

    def test_compiler_structures_exact_canonical_dictionary_values(self) -> None:
        inventory = self.design / "dictionary-inventory.md"
        inventory.write_text(
            """| dictionary_id | active_values |
| --- | --- |
| `DICT-001` | `Мужчина`; `Женщина` |
""",
            encoding="utf-8",
        )

        result = self.compile()
        evidence = (result.stage_package.parent / "source-evidence.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '"active_values":["Мужчина","Женщина"]',
            evidence,
        )
        self.assertNotIn('"active_values":[";"]', evidence)

    def test_blocks_punctuation_only_dictionary_values(self) -> None:
        inventory = self.design / "dictionary-inventory.md"
        inventory.write_text(
            "| dictionary_id | active_values |\n| --- | --- |\n| `DICT-001` | `;` |\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "malformed active values"):
            self.compile()

    def test_blocks_empty_dictionary_values(self) -> None:
        inventory = self.design / "dictionary-inventory.md"
        inventory.write_text(
            "| dictionary_id | active_values |\n| --- | --- |\n| `DICT-001` |  |\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "malformed active values"):
            self.compile()

    def test_blocks_malformed_dictionary_delimiters(self) -> None:
        inventory = self.design / "dictionary-inventory.md"
        inventory.write_text(
            "| dictionary_id | active_values |\n| --- | --- |\n| `DICT-001` | `A`;; `B` |\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(StageRuntimeError, "malformed active values"):
            self.compile()

    def test_routes_evidence_qualified_dimension_to_standard(self) -> None:
        matrix = self.design / "test-design-applicability-matrix.md"
        matrix.write_text(
            "| dimension | applicable |\n| --- | --- |\n| integration | yes_with_evidence |\n",
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.execution_profile, "standard-required")
        self.assertIn("evidence-qualified-evidence", result.unsupported_dimensions)
        self.assertIn("integration-persistence", result.unsupported_dimensions)

    def test_routes_navigation_obligation_to_standard_even_when_matrix_says_other(self) -> None:
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace(
                "`dictionary-source` | `dictionary-values-shown`",
                "`action-navigation` | `navigation-target-opened`",
            ),
            encoding="utf-8",
        )

        result = self.compile()

        self.assertEqual(result.execution_profile, "standard-required")
        self.assertIn("state-transition-or-navigation", result.unsupported_dimensions)

    def test_preserves_gap_child_of_covered_atom(self) -> None:
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "`GSR 1; DICT-001`", "`GSR 1; DICT-001; GAP-001`"
            ),
            encoding="utf-8",
        )
        obligations = self.design / "coverage-obligation-table.md"
        lines = obligations.read_text(encoding="utf-8").splitlines()
        lines.append(
            "| `OBL-003` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-closed-set` | Закрытость списка не доказана. | `GSR 1; SRC-001.P01` | `GAP-001` | `unclear` | `-` |"
        )
        obligations.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = self.compile()

        self.assertEqual(result.obligation_count, 3)
        self.assertEqual(result.gap_count, 1)


if __name__ == "__main__":
    unittest.main()
