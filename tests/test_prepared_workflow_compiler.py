from __future__ import annotations

import json
import io
import hashlib
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_case_agent.review_cycle.prepared_compiler import (
    DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE,
    PreparedCompilerDiagnostic,
    _expected_source_assertion_rows,
    _compile_dictionary_requirement,
    _dedicated_exhaustive_dictionary_ids,
    _effective_dictionary_coverage_mode,
    _load_semantic_compiler_projection,
    _resolve_source_first_state_change,
    _unbound_reference_fixture_action_literals,
    _validate_semantic_projection_graph,
    _validate_source_selection_manifest_binding,
    compile_workflow_package,
    evaluate_reference_fixture_action_adequacy,
    markdown_tables,
    resolve_workflow_compiler_inputs,
)
from test_case_agent.review_cycle.prepared_package import (
    PreparedDictionaryRequirement,
    PreparedDictionaryValue,
    PreparedStateChange,
    load_obligations,
    load_prepared_package,
)
from test_case_agent.review_cycle.runtime import StageRuntimeError
from test_case_agent.review_cycle.dimension_bindings import (
    parse_reviewer_dimension_source_bindings,
)
from test_case_agent.review_cycle.source_assertions import (
    ApprovedClarification,
    ClarificationClauseBinding,
    NO_REQUIRED_CHANGE,
    REVIEW_RECEIPT_VERSION,
    SOURCE_REVIEW_DIMENSIONS,
    ClauseEvidenceBinding,
    RegisteredEvidenceSource,
    RegisteredArtifact,
    RequirementCodeBinding,
    ScopeBoundaryManifestContext,
    ScopeBoundaryExclusion,
    ScopeBoundaryReview,
    SourceAssertion,
    SourceAssertionContractError,
    SourceAssertionManifest,
    SourceAssertionReview,
    SourceAssertionReviewReceipt,
    SourceInventoryReview,
    build_source_assertion_manifest,
    parse_embedded_source_assertion_contract,
    scope_boundary_source_locator,
)
from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowExtractionSpec,
    build_source_row_baseline,
    write_source_row_baseline,
)
from test_case_agent.review_cycle import source_assertions as source_assertions_module
from test_case_agent.semantic_design_bridge import (
    APPLICABILITY_DIMENSIONS,
    canonical_payload_sha256,
)
from scripts.compile_prepared_stage_package import main as compile_cli_main


class PreparedWorkflowCompilerTests(unittest.TestCase):
    def test_reference_fixture_rejects_unbound_synthetic_action_literal(self) -> None:
        assertion = SimpleNamespace(
            exact_source_text="Если в DaData не найден адрес",
            exact_source_fragments=(),
            clause_evidence_bindings=(
                SimpleNamespace(exact_source_fragment="Если в DaData не найден адрес"),
            ),
            supporting_source_bindings=(),
            action_clauses=(
                "Ввести адрес «Несуществующая улица 999999».",
            ),
        )
        requirement = PreparedDictionaryRequirement(
            dictionary_id="DICT-DADATA-ADDR-001",
            coverage_mode="reference-only",
            fixture_values=(
                PreparedDictionaryValue(
                    ("DICT-DADATA-ADDR-001",),
                    "leaf",
                    "ZZZNOADDRESS7F3A9C2E20260721",
                ),
            ),
        )

        self.assertEqual(
            ("Несуществующая улица 999999",),
            _unbound_reference_fixture_action_literals(assertion, (requirement,)),
        )

    def test_reference_fixture_accepts_source_label_and_exact_fixture_literal(self) -> None:
        assertion = SimpleNamespace(
            exact_source_text="Поле «Адрес регистрации»; адрес не найден DaData",
            exact_source_fragments=(),
            clause_evidence_bindings=(),
            supporting_source_bindings=(),
            action_clauses=(
                "В поле «Адрес регистрации» ввести «ZZZNOADDRESS7F3A9C2E20260721».",
            ),
        )
        requirement = PreparedDictionaryRequirement(
            dictionary_id="DICT-DADATA-ADDR-001",
            coverage_mode="reference-only",
            fixture_values=(
                PreparedDictionaryValue(
                    ("DICT-DADATA-ADDR-001",),
                    "leaf",
                    "ZZZNOADDRESS7F3A9C2E20260721",
                ),
            ),
        )

        self.assertEqual(
            (),
            _unbound_reference_fixture_action_literals(assertion, (requirement,)),
        )

    def test_pre_review_reference_fixture_guard_reports_all_conflicts_in_one_batch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            coverage = root / "coverage.md"
            plan = root / "plan.md"
            dictionary = root / "dictionary.md"
            coverage.write_text(
                "| obligation_id | linked_atom_id | required_behavior | property_type | obligation_class | source_ref | dictionary_refs | dictionary_coverage |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| `OBL-001` | `ATOM-001` | Проверить DaData с `DICT-DADATA-ADDR-001`. | integration | suggestions | BSR 1 | `DICT-DADATA-ADDR-001` | `reference-only` |\n",
                encoding="utf-8",
            )
            plan.write_text(
                "| linked_atoms | status | test_data | input_class |\n"
                "| --- | --- | --- | --- |\n"
                "| `ATOM-001` | `covered` | `ZZZNOADDRESS7F3A9C2E20260721` | verified fixture |\n",
                encoding="utf-8",
            )
            dictionary.write_text(
                "| dictionary_id | active_values |\n"
                "| --- | --- |\n"
                "| `DICT-DADATA-ADDR-001` | `ZZZNOADDRESS7F3A9C2E20260721` |\n",
                encoding="utf-8",
            )
            manifest = {
                "assertions": [
                    {
                        "assertion_id": "ASSERT-001",
                        "atom_id": "ATOM-001",
                        "obligation_ids": ["OBL-001"],
                        "exact_source_text": "Если адрес не найден",
                        "exact_source_fragments": [],
                        "clause_evidence_bindings": [],
                        "supporting_source_bindings": [],
                        "action_clauses": ["Ввести «Несуществующая улица 999999»."],
                    },
                    {
                        "assertion_id": "ASSERT-002",
                        "atom_id": "ATOM-001",
                        "obligation_ids": ["OBL-001"],
                        "exact_source_text": "Если адрес не найден",
                        "exact_source_fragments": [],
                        "clause_evidence_bindings": [],
                        "supporting_source_bindings": [],
                        "action_clauses": ["Ввести «Другой выдуманный адрес 123»."],
                    },
                ]
            }

            report = evaluate_reference_fixture_action_adequacy(
                manifest,
                coverage_obligation_table=coverage,
                package_test_design_plan=plan,
                dictionary_inventory=dictionary,
            )

        self.assertFalse(report["passed"])
        self.assertEqual(2, report["checked_assertion_count"])
        self.assertEqual(2, report["conflict_count"])
        self.assertEqual(
            ["ASSERT-001", "ASSERT-002"],
            [item["assertion_id"] for item in report["conflicts"]],
        )

    def test_pre_review_reference_fixture_guard_accepts_exact_fixture_literal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            coverage = root / "coverage.md"
            plan = root / "plan.md"
            dictionary = root / "dictionary.md"
            coverage.write_text(
                "| obligation_id | linked_atom_id | required_behavior | property_type | obligation_class | source_ref | dictionary_refs | dictionary_coverage |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| `OBL-001` | `ATOM-001` | Проверить DaData. | integration | suggestions | BSR 1 | `DICT-DADATA-ADDR-001` | `reference-only` |\n",
                encoding="utf-8",
            )
            plan.write_text(
                "| linked_atoms | status | test_data | input_class |\n"
                "| --- | --- | --- | --- |\n"
                "| `ATOM-001` | `covered` | `ZZZNOADDRESS7F3A9C2E20260721` | verified fixture |\n",
                encoding="utf-8",
            )
            dictionary.write_text(
                "| dictionary_id | active_values |\n"
                "| --- | --- |\n"
                "| `DICT-DADATA-ADDR-001` | `ZZZNOADDRESS7F3A9C2E20260721` |\n",
                encoding="utf-8",
            )
            manifest = {
                "assertions": [
                    {
                        "assertion_id": "ASSERT-001",
                        "atom_id": "ATOM-001",
                        "obligation_ids": ["OBL-001"],
                        "exact_source_text": "Если адрес не найден",
                        "exact_source_fragments": [],
                        "clause_evidence_bindings": [],
                        "supporting_source_bindings": [],
                        "action_clauses": [
                            "Ввести «ZZZNOADDRESS7F3A9C2E20260721»."
                        ],
                    }
                ]
            }

            report = evaluate_reference_fixture_action_adequacy(
                manifest,
                coverage_obligation_table=coverage,
                package_test_design_plan=plan,
                dictionary_inventory=dictionary,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(1, report["checked_assertion_count"])
        self.assertEqual([], report["conflicts"])

    def test_source_first_compiler_surfaces_reference_fixture_action_conflict(self) -> None:
        self.enable_source_first_contract()

        with patch(
            "test_case_agent.review_cycle.prepared_compiler."
            "_unbound_reference_fixture_action_literals",
            return_value=("Несуществующая улица 999999",),
        ):
            with self.assertRaises(PreparedCompilerDiagnostic) as context:
                self.compile(cycle_name="reference-fixture-action-conflict")

        self.assertEqual(
            "source-action-reference-fixture-conflict",
            context.exception.code,
        )
        self.assertEqual(
            ["Несуществующая улица 999999"],
            context.exception.details[0]["conflicting_literals"],
        )
        self.assertEqual("ASSERT-001", context.exception.details[0]["assertion_id"])
        self.assertEqual("OBL-001", context.exception.details[0]["obligation_id"])

    def test_markdown_tables_preserve_escaped_pipe_inside_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.md"
            path.write_text(
                "| dimension | applicable | reason |\n"
                "| --- | --- | --- |\n"
                "| `integration` | `yes` | DaData found \\| not found |\n",
                encoding="utf-8",
            )

            self.assertEqual(
                [
                    {
                        "dimension": "integration",
                        "applicable": "yes",
                        "reason": "DaData found | not found",
                    }
                ],
                markdown_tables(path)[0],
            )

    def test_reference_fixture_does_not_match_short_value_inside_field_name(self) -> None:
        requirement = _compile_dictionary_requirement(
            dictionary_id="DICT-001",
            coverage_mode="reference-only",
            dictionary_rows={"DICT-001": {"dictionary_name": "Статусы"}},
            dictionary_active_values={
                "DICT-001": ("ИП", "работа по найму"),
            },
            reference_fixture_text=(
                "Проверить поле Тип должности. Test data: работа по найму"
            ),
        )

        self.assertEqual(
            ["работа по найму"],
            [item.value for item in requirement.fixture_values],
        )

    def test_dedicated_dictionary_obligation_owns_exhaustive_projection(self) -> None:
        rows = (
            {
                "property_type": "dictionary",
                "obligation_class": "dictionary-values",
                "dictionary_refs": "DICT-001",
                "source_ref": "SRC-001",
                "dictionary_coverage": "all-leaf-values",
            },
            {
                "property_type": "visibility",
                "obligation_class": "conditional-visibility",
                "dictionary_refs": "DICT-001",
                "source_ref": "SRC-002; DICT-001",
                "dictionary_coverage": "all-leaf-values",
            },
        )

        owners = _dedicated_exhaustive_dictionary_ids(rows)

        self.assertEqual(frozenset({"DICT-001"}), owners)
        self.assertEqual(
            "all-leaf-values",
            _effective_dictionary_coverage_mode(
                rows[0],
                dictionary_id="DICT-001",
                dedicated_exhaustive_dictionary_ids=owners,
            ),
        )
        self.assertEqual(
            "reference-only",
            _effective_dictionary_coverage_mode(
                rows[1],
                dictionary_id="DICT-001",
                dedicated_exhaustive_dictionary_ids=owners,
            ),
        )

    @staticmethod
    def _file_sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _verified_review(assertion: SourceAssertion) -> SourceAssertionReview:
        return SourceAssertionReview(
            assertion_id=assertion.assertion_id,
            approved_polarity=assertion.polarity,
            approved_semantic_disposition=assertion.semantic_disposition,
            approved_execution_readiness=assertion.execution_readiness,
            approved_risk=assertion.risk,
            dimension_verdicts={
                dimension: "verified" for dimension in SOURCE_REVIEW_DIMENSIONS
            },
            verdict="verified",
            required_change=NO_REQUIRED_CHANGE,
            note="Независимо сверено с XHTML.",
        )

    @staticmethod
    def _scope_boundary(manifest) -> ScopeBoundaryReview:
        reviewed = tuple(
            ScopeBoundaryManifestContext(
                context_class=row.source_context_class,
                source_row_id=row.source_row_id,
            )
            for row in manifest.source_rows
            if row.source_context_class
            in {
                "document-global-constraints",
                "ancestor-and-section-preamble",
                "cross-referenced-constraints",
            }
        )
        reviewed_classes = {item.context_class for item in reviewed}
        source = manifest.sources[0]
        external_contexts = {
            "document-global-constraints": "External document-global context.",
            "ancestor-and-section-preamble": "External ancestor context.",
            "cross-referenced-constraints": "External cross-reference context.",
        }
        return ScopeBoundaryReview(
            verdict="verified",
            checked_context_classes=(
                "document-global-constraints",
                "ancestor-and-section-preamble",
                "cross-referenced-constraints",
            ),
            reviewed_manifest_contexts=reviewed,
            excluded_contexts=tuple(
                ScopeBoundaryExclusion(
                    context_class=context_class,
                    source_path=source.path,
                    source_sha256=source.sha256,
                    source_locator=scope_boundary_source_locator(
                        source.path,
                        exact_text,
                    ),
                    exact_source_text=exact_text,
                    reason="Verified context is outside the manifest row registry.",
                )
                for context_class, exact_text in external_contexts.items()
                if context_class not in reviewed_classes
            ),
            required_change=NO_REQUIRED_CHANGE,
            note="Границы scope независимо сверены со всем документом.",
        )

    @staticmethod
    def _source_inventory_review(manifest) -> SourceInventoryReview:
        return SourceInventoryReview(
            extraction_spec_digest=manifest.source_row_extraction_spec_digest,
            baseline_digest=manifest.source_row_baseline_digest,
            candidate_count=manifest.source_row_candidate_count,
            mapped_source_row_count=sum(
                1 for row in manifest.source_rows if row.candidate_id is not None
            ),
            verdict="verified",
            required_change=NO_REQUIRED_CHANGE,
            note=(
                "Полнота extractor baseline и каждое сопоставление "
                "source-row независимо сверены."
            ),
        )

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
        (self.ft / "AGENT-NOTES.md").write_text(
            "Package-specific source interpretation.\n",
            encoding="utf-8",
        )
        (self.ft / "mockups").mkdir()
        (self.ft / "mockups" / "search-screen.png").write_bytes(b"mockup")
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
        self._write_source_selection()
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

    def _write_source_selection(self) -> None:
        rows = (
            ("source/main.docx", "main-ft-docx", "semantic-source-of-truth"),
            ("source/main.xhtml", "main-ft-xhtml", "assertion-source"),
            ("source/main.pdf", "main-ft-pdf", "structural-visual-parity"),
            ("AGENT-NOTES.md", "mandatory-package-context", "supporting-material"),
            ("mockups/search-screen.png", "mockup", "mockup"),
        )
        rendered_rows = "\n".join(
            "| `{path}` | `{role}` | `{sha256}` | `{manifest_binding}` |".format(
                path=relative_path,
                role=role,
                sha256=self._file_sha256(self.ft / Path(relative_path)),
                manifest_binding=manifest_binding,
            )
            for relative_path, role, manifest_binding in rows
        )
        (self.state.parent / "source-selection.md").write_text(
            "# Source Selection\n\n"
            "| path | role | sha256 | manifest_binding |\n"
            "| --- | --- | --- | --- |\n"
            + rendered_rows
            + "\n\n"
            "- xhtml_available: `yes`\n"
            "- xhtml_matches_main_ft: `yes`\n",
            encoding="utf-8",
        )

    @staticmethod
    def _source_first_external_evidence() -> dict[str, object]:
        return {
            "evidence_sources": (
                ("fts/demo/source/main.docx", "semantic-source-of-truth"),
                ("fts/demo/source/main.pdf", "structural-visual-parity"),
                ("fts/demo/AGENT-NOTES.md", "supporting-material"),
            ),
            "mockups": ((
                "fts/demo/mockups/search-screen.png",
                "Search screen",
                ("Search form",),
            ),),
        }

    def _materialize_source_row_contract(
        self,
        rows: tuple[dict[str, str | int], ...],
    ) -> tuple[SourceRowExtractionSpec, object, dict[str, str]]:
        selected_xhtml = self.ft / "source" / "main.xhtml"
        selected_relative_path = "fts/demo/source/main.xhtml"
        regions = []
        row_locators: dict[str, str] = {}
        for index, row in enumerate(rows, start=1):
            position = int(row["position"])
            locator = f"/*/*[1]/*[{position}]"
            source_row_id = str(row["source_row_id"])
            row_locators[source_row_id] = locator
            regions.append(
                {
                    "region_id": f"REG-{index:03d}",
                    "source_context_class": str(row["source_context_class"]),
                    "selector": {
                        "kind": "container",
                        "container_xpath": locator,
                    },
                }
            )
        spec = SourceRowExtractionSpec.from_dict(
            {
                "version": 1,
                "scope_slug": "demo-scope",
                "selected_xhtml": {
                    "relative_path": selected_relative_path,
                    "sha256": self._file_sha256(selected_xhtml),
                },
                "regions": regions,
            }
        )
        spec_path = self.design / "source-row-extraction-spec.json"
        spec_path.write_text(
            json.dumps(spec.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        baseline = build_source_row_baseline(repo_root=self.root, spec=spec)
        baseline_path = self.design / "source-row-baseline.json"
        write_source_row_baseline(baseline_path, baseline)
        candidates_by_locator = {
            item.canonical_xpath: item for item in baseline.candidates
        }
        candidate_ids = {
            source_row_id: candidates_by_locator[locator].candidate_id
            for source_row_id, locator in row_locators.items()
        }
        inventory_lines = [
            "# Source Row Inventory",
            "",
            (
                "| source_row_id | in_scope | source_path | source_locator | "
                "bounded_source_text | source_context_class | requirement_codes | "
                "candidate_id |"
            ),
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for row in rows:
            source_row_id = str(row["source_row_id"])
            inventory_lines.append(
                "| `{source_row_id}` | `{in_scope}` | {source_path} | {locator} | "
                "{bounded_source_text} | {source_context_class} | {requirement_codes} | "
                "`{candidate_id}` |".format(
                    source_row_id=source_row_id,
                    in_scope=row["in_scope"],
                    source_path=selected_relative_path,
                    locator=row_locators[source_row_id],
                    bounded_source_text=row["bounded_source_text"],
                    source_context_class=row["source_context_class"],
                    requirement_codes=row["requirement_codes"],
                    candidate_id=candidate_ids[source_row_id],
                )
            )
        (self.design / "source-row-inventory.md").write_text(
            "\n".join(inventory_lines) + "\n",
            encoding="utf-8",
        )
        return spec, baseline, candidate_ids

    def compile(
        self,
        *,
        reuse_if_current: bool = False,
        output_mode: str = "release",
        cycle_name: str = "compiled-cycle",
    ):
        cycle = self.ft / "work" / "review-cycles" / cycle_name
        return compile_workflow_package(
            workflow_state=self.state,
            repo_root=self.root,
            output_root=cycle / "prepared-input" / "demo-package",
            package_id="demo-package",
            attempt_root=cycle / "attempts" / "writer-r1" / "attempt-001",
            expected_ft_slug="demo",
            reuse_if_current=reuse_if_current,
            output_mode=output_mode,
        )

    def enable_source_fidelity(self, bindings: list[dict[str, object]]) -> Path:
        path = self.design / "source-to-package-fidelity.json"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "scope_slug": "demo-scope",
                    "bindings": bindings,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        state = self.state.read_text(encoding="utf-8")
        state = state.replace(
            "  test_design_applicability_matrix: work/test-design/demo-scope/test-design-applicability-matrix.md\n",
            "  test_design_applicability_matrix: work/test-design/demo-scope/test-design-applicability-matrix.md\n"
            "  source_to_package_fidelity: work/test-design/demo-scope/source-to-package-fidelity.json\n",
        )
        self.state.write_text(state, encoding="utf-8")
        return path

    def enable_source_first_contract(
        self,
        *,
        risk: str = "medium",
        execution_readiness: str = "ready",
    ) -> tuple[Path, Path]:
        execution_blocked = execution_readiness == "dependency-blocked"
        coverage_status = "blocked" if execution_blocked else "covered"
        planned_target = "GAP-EXECUTION-001" if execution_blocked else "TC-001"
        plan_status = "blocked" if execution_blocked else "covered"
        xhtml = self.ft / "source" / "main.xhtml"
        exact_source_text = (
            "GSR 1. Поле использует фиксированный список DICT-001."
        )
        xhtml.write_text(
            f"<html><body><p>{exact_source_text}</p>"
            "<p>External ancestor context.</p>"
            "<p>External cross-reference context.</p></body></html>\n",
            encoding="utf-8",
        )
        self._write_source_selection()
        (self.design / "atomic-requirements-ledger.md").write_text(
            f"""# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `{coverage_status}` | `{planned_target}` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            f"""# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- |
| `ATOM-001` | Открыть список значений поля. | Отображаются все и только значения DICT-001. | `{planned_target}` | `{plan_status}` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            f"""# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-values-shown` | Отображаются все и только значения DICT-001. | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | `{planned_target}` | `{coverage_status}` | `-` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\nNo gaps.\n", encoding="utf-8"
        )
        spec, baseline, candidate_ids = self._materialize_source_row_contract(
            (
                {
                    "source_row_id": "SRC-001.P01",
                    "in_scope": "yes",
                    "position": 1,
                    "bounded_source_text": exact_source_text,
                    "source_context_class": "document-global-constraints",
                    "requirement_codes": "GSR 1",
                },
            )
        )
        assertion = SourceAssertion(
            assertion_id="ASSERT-001",
            source_path="fts/demo/source/main.xhtml",
            source_context_class="document-global-constraints",
            locator="/*/*[1]/*[1]",
            exact_source_text=exact_source_text,
            canonical_statement="Поле использует фиксированный список DICT-001.",
            polarity="positive",
            semantic_disposition="testable",
            execution_readiness=execution_readiness,
            execution_readiness_rationale=(
                "Runtime dictionary fixture is not yet registered for execution."
                if execution_readiness == "dependency-blocked"
                else NO_REQUIRED_CHANGE
            ),
            risk=risk,
            condition_clauses=("Открыта форма с проверяемым полем.",),
            action_clauses=("Открыть список значений поля.",),
            oracle_clauses=(
                "Отображаются все и только значения DICT-001.",
            ),
            requirement_codes=("GSR 1",),
            requirement_code_bindings=(
                RequirementCodeBinding("GSR 1", "SRC-001.P01", "xhtml-row", "GSR 1"),
            ),
            clause_evidence_bindings=tuple(
                ClauseEvidenceBinding(
                    clause_kind=kind,
                    clause_index=0,
                    source_row_id="SRC-001.P01",
                    evidence_role=kind,
                    exact_source_fragment=exact_source_text,
                )
                for kind in ("condition", "action", "oracle")
            ),
            source_row_id="SRC-001.P01",
            atom_id="ATOM-001",
            obligation_ids=("OBL-001",),
            execution_dependency_gap_ids=(
                ("GAP-EXECUTION-001",)
                if execution_readiness == "dependency-blocked"
                else ()
            ),
            primary_gap_id=None,
        )
        if execution_readiness == "dependency-blocked":
            (self.design / "coverage-gaps.md").write_text(
                "# Coverage Gaps\n\n"
                "## GAP-EXECUTION-001\n\n"
                "**Impact:** `blocking`\n\n"
                "| field | value |\n"
                "| --- | --- |\n"
                "| gap_id | GAP-EXECUTION-001 |\n"
                "| execution_assertion_ids | ASSERT-001 |\n"
                "| execution_atom_ids | ATOM-001 |\n"
                "| execution_obligation_ids | OBL-001 |\n"
                "| blocks_ready_for_review | yes |\n"
                "| status | open |\n",
                encoding="utf-8",
            )
        manifest = build_source_assertion_manifest(
            self.root,
            scope_slug="demo-scope",
            coverage_gaps_path=(
                "fts/demo/work/test-design/demo-scope/coverage-gaps.md"
            ),
            source_paths=("fts/demo/source/main.xhtml",),
            assertions=(assertion,),
            source_row_extraction_spec_digest=spec.digest,
            source_row_baseline_digest=baseline.digest,
            source_row_candidate_count=baseline.candidate_count,
            source_row_candidate_ids=candidate_ids,
            expected_source_row_ids=("SRC-001.P01",),
            **self._source_first_external_evidence(),
        )
        assertions_path = self.design / "source-assertions.json"
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=(
                self._verified_review(assertion),
            ),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        review_path = self.design / "source-assertion-review.json"
        review_path.write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        state = self.state.read_text(encoding="utf-8").replace(
            "prepared_compiler_contract_version: 2",
            "prepared_compiler_contract_version: 3",
        )
        state = state.replace(
            "  coverage_gaps: work/test-design/demo-scope/coverage-gaps.md\n",
            "  coverage_gaps: work/test-design/demo-scope/coverage-gaps.md\n"
            "  source_row_inventory: work/test-design/demo-scope/source-row-inventory.md\n"
            "  source_row_extraction_spec: work/test-design/demo-scope/source-row-extraction-spec.json\n"
            "  source_row_baseline: work/test-design/demo-scope/source-row-baseline.json\n"
            "  source_assertions: work/test-design/demo-scope/source-assertions.json\n"
            "  source_assertion_review: work/test-design/demo-scope/source-assertion-review.json\n",
        )
        self.state.write_text(state, encoding="utf-8")
        return assertions_path, review_path

    def _refresh_semantic_bridge_receipt(self) -> Path:
        semantic_path = self.design / "semantic-design.json"
        boundary_path = self.design / "scope-boundary-decision.json"
        receipt_path = self.design / "semantic-design-bridge-receipt.json"
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
        manifest = SourceAssertionManifest.from_dict(
            json.loads((self.design / "source-assertions.json").read_text(encoding="utf-8"))
        )
        receipt = {
            "version": 1,
            "status": "verified",
            "contract": "scope-v2-to-semantic-design-v1",
            "materialization_status": "materialized",
            "prepared_context_sha256": semantic["prepared_context_sha256"],
            "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
            "semantic_design_decision_sha256": canonical_payload_sha256(semantic),
            "source_row_count": len(manifest.source_rows),
            "included_source_row_count": 1,
            "assertion_count": len(manifest.assertions),
            "testable_assertion_count": sum(
                item.semantic_disposition == "testable" for item in manifest.assertions
            ),
            "obligation_count": len(semantic["obligations"]),
            "dependency_binding_count": len(semantic["dependency_bindings"]),
            "planned_test_case_count": len(
                {item["planned_tc_id"] for item in semantic["obligations"]}
            ),
            "dictionary_count": len(semantic["dictionaries"]),
            "negative_oracle_count": len(semantic["negative_oracles"]),
            "requiredness_oracle_count": len(semantic["requiredness_oracles"]),
            "approved_clarification_count": len(manifest.clarifications),
            "state_change_obligation_count": 0,
            "source_assertion_manifest_digest": manifest.digest,
            "scope_boundary_artifact_sha256": self._file_sha256(boundary_path),
            "semantic_design_artifact_sha256": self._file_sha256(semantic_path),
            "downstream_evidence_readiness": {
                "status": "passed",
                "canonical_preflight": "source-reviewer.prepare_evidence_set",
                "published_manifest_digest": manifest.digest,
                "binding_count": 1,
                "bounded_extract_count": 0,
                "direct_image_attachment_count": 0,
            },
            "publication": {
                "status": "atomic-renamed",
                "final_handoff": self.design.relative_to(self.root).as_posix(),
            },
        }
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return receipt_path

    def enable_semantic_design_projection(self) -> Path:
        manifest = SourceAssertionManifest.from_dict(
            json.loads((self.design / "source-assertions.json").read_text(encoding="utf-8"))
        )
        assertion = manifest.assertions[0]
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes | dictionary_refs | dictionary_coverage | scope_obligation_ids | calibration_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `demo-package` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-values-shown` | Отображаются все и только значения DICT-001. | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | `TC-001` | `covered` | `-` | `DICT-001` | `all-leaf-values` | `none_required` | `none` |
""",
            encoding="utf-8",
        )
        dependency = {
            "dependency_id": "DEP-001",
            "kind": "dictionary",
            "name": "DICT-001",
            "source_row_ids": ["SRC-001.P01"],
            "resolution": "declared",
            "target_source_row_ids": ["SRC-001.P01"],
            "exact_source_fragments": ["DICT-001"],
            "gap_ids": [],
            "blocking": False,
            "rationale": "The fixed dictionary is declared by the accepted source row.",
        }
        boundary = {
            "version": 2,
            "status": "ready",
            "blocking_reason": "none_required",
            "scope_summary": "Проверяется состав фиксированного справочника поля.",
            "scope_boundary": {
                "target": "Поле со справочником DICT-001",
                "include": ["SRC-001.P01"],
                "exclude": [],
            },
            "source_decisions": [
                {
                    "source_row_id": "SRC-001.P01",
                    "disposition": "included",
                    "requirement_codes": ["GSR 1"],
                    "rationale": "Строка задаёт проверяемый состав справочника.",
                }
            ],
            "dependencies": [dependency],
            "gaps": [],
            "mockup_locators": [],
        }
        boundary_path = self.design / "scope-boundary-decision.json"
        boundary_path.write_text(
            json.dumps(boundary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        semantic = {
            "version": 4,
            "contract": "semantic-design-bridge-v2",
            "status": "ready",
            "blocking_reason": "none_required",
            "prepared_context_sha256": "1" * 64,
            "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
            "scope_summary": boundary["scope_summary"],
            "included": boundary["scope_boundary"]["include"],
            "excluded": boundary["scope_boundary"]["exclude"],
            "mockup_locators": [],
            "source_designs": [
                {
                    "source_row_id": assertion.source_row_id,
                    "boundary_disposition": "included",
                    "requirement_codes": list(assertion.requirement_codes),
                    "assertions": [
                        {
                            "assertion_id": assertion.assertion_id,
                            "canonical_statement": assertion.canonical_statement,
                            "polarity": assertion.polarity,
                            "semantic_disposition": "testable",
                            "execution_readiness": "ready",
                            "execution_readiness_rationale": NO_REQUIRED_CHANGE,
                            "risk": assertion.risk,
                            "condition_clauses": list(assertion.condition_clauses),
                            "action_clauses": list(assertion.action_clauses),
                            "oracle_clauses": list(assertion.oracle_clauses),
                            "requirement_codes": list(assertion.requirement_codes),
                            "requirement_code_evidence": [
                                item.to_dict()
                                for item in assertion.requirement_code_bindings
                            ],
                            "clause_evidence": [
                                item.to_dict() for item in assertion.clause_evidence_bindings
                            ],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "atom_id": assertion.atom_id,
                            "obligation_ids": list(assertion.obligation_ids),
                            "disposition_rationale": NO_REQUIRED_CHANGE,
                            "source_property_id": "SRC-001.P01",
                            "field_or_block": "Поле со справочником",
                            "source_reference": "GSR 1; SRC-001.P01; DICT-001",
                        }
                    ],
                }
            ],
            "obligations": [
                {
                    "obligation_id": "OBL-001",
                    "package_id": "demo-package",
                    "linked_atom_id": "ATOM-001",
                    "source_property_id": "SRC-001.P01",
                    "property_type": "dictionary-source",
                    "obligation_class": "dictionary-values-shown",
                    "required_behavior": "Отображаются все и только значения DICT-001.",
                    "source_ref": "GSR 1; SRC-001.P01; DICT-001",
                    "planned_tc_id": "TC-001",
                    "review_notes": "-",
                    "design_dimension": "traceability",
                    "planned_check": "Открыть список и сверить полный состав значений.",
                    "check_type": "positive",
                    "coverage_class": "source-backed",
                    "input_class": "dictionary-selection",
                    "single_expected_behavior": "Отображаются все и только значения DICT-001.",
                    "oracle_source": "Фиксированный перечень DICT-001 из ФТ.",
                    "test_data": "Все активные значения DICT-001: A, B.",
                    "dictionary_refs": ["DICT-001"],
                    "dictionary_coverage": "all-leaf-values",
                    "scope_obligation_ids": [],
                }
            ],
            "reset_lifecycle_bindings": [],
            "dependency_bindings": [
                {
                    **dependency,
                    "semantic_disposition": "bound",
                    "linked_assertion_ids": ["ASSERT-001"],
                    "linked_atom_ids": ["ATOM-001"],
                    "linked_obligation_ids": ["OBL-001"],
                    "mapping_rationale": "semantic-marker-alpha: full accepted assertion chain.",
                }
            ],
            "dictionaries": [
                {
                    "dictionary_id": "DICT-001",
                    "dictionary_name": "Тестовый справочник",
                    "source_row_ids": ["SRC-001.P01"],
                    "source_file": "fts/demo/source/main.xhtml",
                    "source_location": "GSR 1",
                    "extraction_status": "extracted",
                    "active_values": ["A", "B"],
                    "archived_values": [],
                    "gap_id": "none_required",
                    "notes": "Полный фиксированный перечень извлечён.",
                }
            ],
            "negative_oracles": [],
            "requiredness_oracles": [],
            "applicability": [
                {
                    "dimension": dimension,
                    "applicable": "yes" if dimension == "traceability" else "no",
                    "source_ref": "GSR 1; SRC-001.P01",
                    "reason": (
                        "Проверяется полная ASSERT->ATOM->OBL->TC трассировка."
                        if dimension == "traceability"
                        else "В выбранном atomic scope измерение не заявлено."
                    ),
                    "linked_atoms": ["ATOM-001"] if dimension == "traceability" else [],
                    "linked_test_cases": ["TC-001"] if dimension == "traceability" else [],
                }
                for dimension in APPLICABILITY_DIMENSIONS
            ],
        }
        semantic_path = self.design / "semantic-design.json"
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()
        state = self.state.read_text(encoding="utf-8").replace(
            "  source_assertion_review: work/test-design/demo-scope/source-assertion-review.json\n",
            "  source_assertion_review: work/test-design/demo-scope/source-assertion-review.json\n"
            "  semantic_design: work/test-design/demo-scope/semantic-design.json\n"
            "  scope_boundary_decision: work/test-design/demo-scope/scope-boundary-decision.json\n"
            "  semantic_design_bridge_receipt: work/test-design/demo-scope/semantic-design-bridge-receipt.json\n",
        )
        self.state.write_text(state, encoding="utf-8")
        return semantic_path

    def configure_semantic_requiredness_oracle(
        self,
        *,
        decision: str,
        parent_gap: bool = False,
    ) -> Path:
        semantic_path = self.design / "semantic-design.json"
        boundary_path = self.design / "scope-boundary-decision.json"
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
        scope_id = "SO-REQ-001"
        candidate = decision == "candidate_tc_required"
        semantic["obligations"][0]["scope_obligation_ids"] = [scope_id]
        semantic["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": ["GSR 1"],
                "scope_obligation_id": scope_id,
                "source_row_id": "SRC-001.P01",
                "source_ref": "GSR 1; SRC-001.P01",
                "field_or_block": "Поле со справочником",
                "restriction_type": "requiredness",
                "requiredness_source": "GSR 1",
                "requiredness_class": "always-required",
                "required_when": "always",
                "marker_oracle_found": "no" if candidate else "yes",
                "empty_value_oracle_found": "no" if candidate else "yes",
                "oracle_source": "not_found" if candidate else "GSR 1",
                "oracle_status": (
                    "ui-calibration-required" if candidate else "source-backed"
                ),
                "decision": decision,
                "planned_tc_or_gap": (
                    f"candidate:{scope_id}" if candidate else "TC-001"
                ),
                "gap_id": "GAP-UI-001" if parent_gap else "none_required",
                "analyst_question": (
                    "Какой точный UI-отклик отображается?"
                    if candidate
                    else "none_required"
                ),
                "handoff_rule": "Preserve the exact semantic oracle route.",
                "calibration_notes": (
                    "Статус тест-кейса: candidate-ui-calibration."
                    if candidate
                    else "none_required"
                ),
                "linked_atom_id": "ATOM-001",
                "linked_obligation_id": "OBL-001",
            }
        ]

        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_text = obligations_path.read_text(encoding="utf-8")
        old_tail = "`none_required` | `none` |"
        new_tail = (
            f"`{scope_id}` | `ui-calibration-required` |"
            if candidate
            else f"`{scope_id}` | `none` |"
        )
        if old_tail not in obligations_text:
            raise AssertionError("semantic obligation fixture lacks explicit calibration tail")
        obligations_path.write_text(
            obligations_text.replace(old_tail, new_tail, 1), encoding="utf-8"
        )

        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_lines = ledger_path.read_text(encoding="utf-8").splitlines()
        updated_ledger: list[str] = []
        for line in ledger_lines:
            if "`ATOM-001`" in line and candidate:
                line = line.replace("`covered`", "`covered_with_ui_calibration`", 1)
            if parent_gap:
                if line.startswith("| atom_id "):
                    line = line[:-1] + "| constraint_gap_ids |"
                elif line.startswith("| --- "):
                    line = line[:-1] + "| --- |"
                elif "`ATOM-001`" in line:
                    line = line[:-1] + "| `GAP-UI-001` |"
            updated_ledger.append(line)
        ledger_path.write_text("\n".join(updated_ledger) + "\n", encoding="utf-8")

        inventory_path = self.design / "requiredness-oracle-inventory.md"
        inventory_path.write_text(
            "| signal_id | scope_obligation_id | decision | gap_id |\n"
            "| --- | --- | --- | --- |\n"
            f"| SIG-REQ-001 | {scope_id} | {decision} | "
            + ("GAP-UI-001" if parent_gap else "none_required")
            + " |\n",
            encoding="utf-8",
        )
        state = self.state.read_text(encoding="utf-8")
        if "requiredness_oracle_inventory:" not in state:
            state = state.replace(
                "  semantic_design_bridge_receipt: work/test-design/demo-scope/semantic-design-bridge-receipt.json\n",
                "  semantic_design_bridge_receipt: work/test-design/demo-scope/semantic-design-bridge-receipt.json\n"
                "  requiredness_oracle_inventory: work/test-design/demo-scope/requiredness-oracle-inventory.md\n",
            )
            self.state.write_text(state, encoding="utf-8")

        if parent_gap:
            boundary["gaps"] = [
                {
                    "gap_id": "GAP-UI-001",
                    "gap_type": "ambiguity",
                    "source_row_ids": ["SRC-001.P01"],
                    "source_refs": ["GSR 1; SRC-001.P01; DICT-001"],
                    "exact_source_fragments": ["GSR 1"],
                    "blocking": False,
                    "clarification_question": "Какой точный UI-отклик отображается?",
                    "downstream_handling": "carry-to-source-model",
                }
            ]
            gaps_path = self.design / "coverage-gaps.md"
            gaps_path.write_text(
                "# Coverage Gaps\n\n"
                "### GAP-UI-001\n\n"
                "| field | value |\n"
                "| --- | --- |\n"
                "| gap_id | GAP-UI-001 |\n"
                "| impact | non-blocking |\n"
                "| blocking | no |\n"
                "| blocks_ready_for_review | no |\n"
                "| status | open |\n"
                "| source_row_ids | SRC-001.P01 |\n"
                "| source_refs | GSR 1; SRC-001.P01; DICT-001 |\n"
                "| requirement_codes | GSR 1 |\n"
                "| reason | Точный UI-отклик не определён. |\n"
                "| handling | carry-to-source-model |\n"
                "| affected_assertion_id | ASSERT-001 |\n"
                "| affected_atom_id | ATOM-001 |\n"
                "| execution_assertion_ids |  |\n"
                "| execution_atom_ids |  |\n"
                "| execution_obligation_ids |  |\n",
                encoding="utf-8",
            )
            manifest_path = self.design / "source-assertions.json"
            manifest = SourceAssertionManifest.from_dict(
                json.loads(manifest_path.read_text(encoding="utf-8"))
            )
            manifest = replace(
                manifest,
                coverage_gaps_artifact=RegisteredArtifact(
                    gaps_path.relative_to(self.root).as_posix(),
                    self._file_sha256(gaps_path),
                ),
            )
            manifest.validate(self.root)
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            review = SourceAssertionReviewReceipt(
                version=REVIEW_RECEIPT_VERSION,
                manifest_digest=manifest.digest,
                decision="accepted",
                assertion_reviews=tuple(
                    self._verified_review(item) for item in manifest.assertions
                ),
                source_inventory_review=self._source_inventory_review(manifest),
                scope_boundary_review=self._scope_boundary(manifest),
            )
            (self.design / "source-assertion-review.json").write_text(
                json.dumps(review.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        boundary_path.write_text(
            json.dumps(boundary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        semantic["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()
        return semantic_path

    def configure_semantic_context_only_gap(self) -> None:
        assertions_path = self.design / "source-assertions.json"
        review_path = self.design / "source-assertion-review.json"
        gaps_path = self.design / "coverage-gaps.md"
        manifest = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        )
        assertion = replace(
            manifest.assertions[0],
            polarity="neutral",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            clause_evidence_bindings=(),
            obligation_ids=(),
            disposition_rationale=(
                "Строка сохраняется только как контекстное evidence и не задаёт "
                "отдельный исполнимый результат."
            ),
        )
        gaps_path.write_text(
            "# Coverage Gaps\n\n"
            "### GAP-CONTEXT-001\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-CONTEXT-001 |\n"
            "| impact | non-blocking |\n"
            "| blocking | no |\n"
            "| blocks_ready_for_review | no |\n"
            "| status | open |\n"
            "| source_row_ids | SRC-001.P01 |\n"
            "| source_refs | GSR 1; SRC-001.P01; DICT-001 |\n"
            "| requirement_codes | GSR 1 |\n"
            "| reason | Требуется уточнить трактовку контекстной строки. |\n"
            "| handling | carry-to-source-model |\n"
            "| affected_assertion_id | ASSERT-001 |\n"
            "| affected_atom_id | ATOM-001 |\n"
            "| execution_assertion_ids |  |\n"
            "| execution_atom_ids |  |\n"
            "| execution_obligation_ids |  |\n",
            encoding="utf-8",
        )
        manifest = replace(
            manifest,
            coverage_gaps_artifact=RegisteredArtifact(
                gaps_path.relative_to(self.root).as_posix(),
                self._file_sha256(gaps_path),
            ),
            assertions=(assertion,),
        )
        manifest.validate(self.root)
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        review_path.write_text(
            json.dumps(
                SourceAssertionReviewReceipt(
                    version=REVIEW_RECEIPT_VERSION,
                    manifest_digest=manifest.digest,
                    decision="accepted",
                    assertion_reviews=(self._verified_review(assertion),),
                    source_inventory_review=self._source_inventory_review(manifest),
                    scope_boundary_review=self._scope_boundary(manifest),
                ).to_dict(),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc | constraint_gap_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P00` | `SRC-001.P00; SRC-001.P01; GSR 1; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `not-applicable` | `not-applicable` | `none_required` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- |
| `ATOM-001` | Не создавать исполнимый кейс. | `none_required:not-applicable` | `not-applicable` | `not-applicable` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes | dictionary_refs | dictionary_coverage | scope_obligation_ids | calibration_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-CONTEXT-001` | `demo-package` | `SRC-001.P00` | `ATOM-001` | `context` | `not-applicable-context` | Строка не задаёт отдельное поведение продукта. | `SRC-001.P00; SRC-001.P01; GSR 1; DICT-001` | `SRC-001.P01` | `GSR 1` | `not-applicable` | `not-applicable` | Контекст сохранён для полноты трассировки. | `none_required` |  | `none_required` | `none` |
""",
            encoding="utf-8",
        )

        boundary_path = self.design / "scope-boundary-decision.json"
        semantic_path = self.design / "semantic-design.json"
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        boundary["source_decisions"][0]["disposition"] = "context"
        boundary["dependencies"][0]["resolution"] = "scope-excluded"
        boundary["dependencies"][0]["rationale"] = (
            "The dependency belongs only to an excluded contextual source row."
        )
        boundary["gaps"] = [
            {
                "gap_id": "GAP-CONTEXT-001",
                "gap_type": "ambiguity",
                "source_row_ids": ["SRC-001.P01"],
                "source_refs": ["GSR 1; SRC-001.P01; DICT-001"],
                "exact_source_fragments": ["GSR 1"],
                "blocking": False,
                "clarification_question": (
                    "Как трактовать контекстную строку без создания тест-кейса?"
                ),
                "downstream_handling": "carry-to-source-model",
            }
        ]
        semantic["source_designs"][0]["boundary_disposition"] = "context"
        semantic_assertion = semantic["source_designs"][0]["assertions"][0]
        semantic_assertion.update(
            {
                "polarity": "neutral",
                "semantic_disposition": "not-applicable",
                "execution_readiness": "not-applicable",
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "clause_evidence": [],
                "obligation_ids": [],
                "disposition_rationale": assertion.disposition_rationale,
            }
        )
        semantic["obligations"] = []
        semantic["dependency_bindings"] = [
            {
                **boundary["dependencies"][0],
                "semantic_disposition": "not-applicable",
                "linked_assertion_ids": [],
                "linked_atom_ids": [],
                "linked_obligation_ids": [],
                "mapping_rationale": (
                    "The excluded contextual dependency owns no executable chain."
                ),
            }
        ]
        for item in semantic["applicability"]:
            item["applicable"] = "no"
            item["reason"] = "Контекстная строка не создаёт исполнимую проверку."
            item["linked_atoms"] = []
            item["linked_test_cases"] = []
        boundary_path.write_text(
            json.dumps(boundary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        semantic["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()

    def configure_semantic_mixed_gap(self) -> None:
        assertions_path = self.design / "source-assertions.json"
        review_path = self.design / "source-assertion-review.json"
        gaps_path = self.design / "coverage-gaps.md"
        manifest = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        )
        testable_assertion = manifest.assertions[0]
        context_assertion = replace(
            testable_assertion,
            assertion_id="ASSERT-CONTEXT-001",
            canonical_statement=(
                "Строка также сохраняется как контекст без отдельного поведения."
            ),
            polarity="neutral",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=(),
            requirement_code_bindings=(),
            clause_evidence_bindings=(),
            atom_id="ATOM-CONTEXT-001",
            obligation_ids=(),
            disposition_rationale=(
                "Контекстное утверждение не формулирует самостоятельный "
                "исполняемый результат."
            ),
        )
        gaps_path.write_text(
            "# Coverage Gaps\n\n"
            "### GAP-MIXED-001\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-MIXED-001 |\n"
            "| impact | non-blocking |\n"
            "| blocking | no |\n"
            "| blocks_ready_for_review | no |\n"
            "| status | open |\n"
            "| source_row_ids | SRC-001.P01 |\n"
            "| source_refs | GSR 1; SRC-001.P01; DICT-001 |\n"
            "| requirement_codes | GSR 1 |\n"
            "| reason | Одна строка содержит testable и context evidence. |\n"
            "| handling | carry-to-source-model |\n"
            "| affected_assertion_id | ASSERT-001; ASSERT-CONTEXT-001 |\n"
            "| affected_atom_id | ATOM-001; ATOM-CONTEXT-001 |\n"
            "| execution_assertion_ids |  |\n"
            "| execution_atom_ids |  |\n"
            "| execution_obligation_ids |  |\n",
            encoding="utf-8",
        )
        manifest = replace(
            manifest,
            coverage_gaps_artifact=RegisteredArtifact(
                gaps_path.relative_to(self.root).as_posix(),
                self._file_sha256(gaps_path),
            ),
            assertions=(testable_assertion, context_assertion),
        )
        manifest.validate(self.root)
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        review_path.write_text(
            json.dumps(
                SourceAssertionReviewReceipt(
                    version=REVIEW_RECEIPT_VERSION,
                    manifest_digest=manifest.digest,
                    decision="accepted",
                    assertion_reviews=(
                        self._verified_review(testable_assertion),
                        self._verified_review(context_assertion),
                    ),
                    source_inventory_review=self._source_inventory_review(manifest),
                    scope_boundary_review=self._scope_boundary(manifest),
                ).to_dict(),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc | constraint_gap_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` | `GAP-MIXED-001` |
| `ATOM-CONTEXT-001` | `SRC-001.P00` | `SRC-001.P00; SRC-001.P01` | `SRC-001.P01` | `none_required` | Строка также сохраняется как контекст без отдельного поведения. | `not-applicable` | `not-applicable` | `none_required` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes | dictionary_refs | dictionary_coverage | scope_obligation_ids | calibration_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `demo-package` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-values-shown` | Отображаются все и только значения DICT-001. | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | `TC-001` | `covered` | `-` | `DICT-001` | `all-leaf-values` | `none_required` | `none` |
| `OBL-CONTEXT-001` | `demo-package` | `SRC-001.P00` | `ATOM-CONTEXT-001` | `context` | `not-applicable-context` | Контекстное утверждение не создаёт тест-кейс. | `SRC-001.P00; SRC-001.P01` | `SRC-001.P01` | `none_required` | `not-applicable` | `not-applicable` | Контекст сохранён для полноты трассировки. | `none_required` |  | `none_required` | `none` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- |
| `ATOM-001` | Открыть список значений поля. | Отображаются все и только значения DICT-001. | `TC-001` | `covered` |
| `ATOM-CONTEXT-001` | Не создавать исполнимый кейс. | `none_required:not-applicable` | `not-applicable` | `not-applicable` |
""",
            encoding="utf-8",
        )

        boundary_path = self.design / "scope-boundary-decision.json"
        semantic_path = self.design / "semantic-design.json"
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        boundary["gaps"] = [
            {
                "gap_id": "GAP-MIXED-001",
                "gap_type": "ambiguity",
                "source_row_ids": ["SRC-001.P01"],
                "source_refs": ["GSR 1; SRC-001.P01; DICT-001"],
                "exact_source_fragments": ["GSR 1"],
                "blocking": False,
                "clarification_question": (
                    "Как трактовать общий контекст без расширения testable поведения?"
                ),
                "downstream_handling": "carry-to-source-model",
            }
        ]
        semantic["source_designs"][0]["assertions"].append(
            {
                "assertion_id": context_assertion.assertion_id,
                "canonical_statement": context_assertion.canonical_statement,
                "polarity": context_assertion.polarity,
                "semantic_disposition": "not-applicable",
                "execution_readiness": "not-applicable",
                "execution_readiness_rationale": NO_REQUIRED_CHANGE,
                "risk": context_assertion.risk,
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "requirement_codes": [],
                "requirement_code_evidence": [],
                "clause_evidence": [],
                "supporting_source_bindings": [],
                "clarification_clause_bindings": [],
                "atom_id": "ATOM-CONTEXT-001",
                "obligation_ids": [],
                "disposition_rationale": context_assertion.disposition_rationale,
                "source_property_id": "SRC-001.P00",
                "field_or_block": "Контекст строки",
                "source_reference": "SRC-001.P00; SRC-001.P01",
            }
        )
        boundary_path.write_text(
            json.dumps(boundary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        semantic["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()

    def bind_user_clarification_to_source_first_contract(self) -> None:
        assertions_path = self.design / "source-assertions.json"
        manifest = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        )
        exact_answer = (
            "Пользователь подтвердил отображение всех значений DICT-001."
        )
        answer_digest = hashlib.sha256(exact_answer.encode("utf-8")).hexdigest()
        clarification_id = "CLR-DEMO-001"
        gap_id = "GAP-DEMO-CLARIFICATION"
        clarification_path = self.design / "scope-clarification-requests.md"
        clarification_path.write_text(
            "\n".join(
                (
                    "# Scope clarifications",
                    "",
                    "| clarification_id | gap_id | scope_slug | requirement_codes | authority | user_response | response_status | response_type | updated_at |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    f"| {clarification_id} | {gap_id} | demo-scope | GSR 1 | user | {exact_answer} | answered | user-confirmed | 2026-07-15 |",
                    "",
                )
            ),
            encoding="utf-8",
        )
        gaps_path = self.design / "coverage-gaps.md"
        gaps_path.write_text(
            "# Coverage Gaps\n\n"
            f"## {gap_id}\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            f"| gap_id | {gap_id} |\n"
            "| status | resolved |\n"
            f"| resolution | approved-clarification:{clarification_id} |\n",
            encoding="utf-8",
        )
        clarification = ApprovedClarification(
            clarification_id=clarification_id,
            gap_id=gap_id,
            scope_slug="demo-scope",
            requirement_codes=("GSR 1",),
            authority="user",
            response_status="answered",
            response_type="user-confirmed",
            answered_at="2026-07-15",
            exact_answer=exact_answer,
            exact_answer_sha256=answer_digest,
            evidence_source_path=clarification_path.relative_to(self.root).as_posix(),
            evidence_source_sha256=self._file_sha256(clarification_path),
        )
        assertion = replace(
            manifest.assertions[0],
            clarification_clause_bindings=(
                ClarificationClauseBinding(
                    clarification_id=clarification_id,
                    clause_kind="oracle",
                    clause_index=0,
                    requirement_codes=("GSR 1",),
                    exact_answer_sha256=answer_digest,
                ),
            ),
        )
        manifest = replace(
            manifest,
            coverage_gaps_artifact=RegisteredArtifact(
                gaps_path.relative_to(self.root).as_posix(),
                self._file_sha256(gaps_path),
            ),
            assertions=(assertion,),
            clarifications=(clarification,),
            evidence_sources=(
                *manifest.evidence_sources,
                RegisteredEvidenceSource(
                    path=clarification.evidence_source_path,
                    sha256=clarification.evidence_source_sha256,
                    role="approved-clarification",
                ),
            ),
        )
        manifest.validate(self.root)
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=(self._verified_review(assertion),),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        (self.design / "source-assertion-review.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        selection_path = self.state.parent / "source-selection.md"
        selection = selection_path.read_text(encoding="utf-8")
        selection_row = (
            "| `work/test-design/demo-scope/scope-clarification-requests.md` | "
            "`approved-clarification` | `"
            + clarification.evidence_source_sha256
            + "` | `approved-clarification` |"
        )
        selection_path.write_text(
            selection.replace(
                "\n\n- xhtml_available:",
                "\n" + selection_row + "\n\n- xhtml_available:",
            ),
            encoding="utf-8",
        )

    def add_source_first_primary_gap(
        self,
        *,
        impact: str,
        gap_risk: str = "medium",
        assertion_gap_id: str = "GAP-PRIMARY",
    ) -> None:
        assertions_path = self.design / "source-assertions.json"
        first_assertion = SourceAssertion.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))["assertions"][0]
        )
        gap_source_text = "GSR 2. Поведение второго условия не определено."
        (self.ft / "source" / "main.xhtml").write_text(
            "<html><body>"
            f"<p>{first_assertion.exact_source_text}</p>"
            f"<p>{gap_source_text}</p>"
            "<p>External ancestor context.</p>"
            "<p>External cross-reference context.</p>"
            "</body></html>\n",
            encoding="utf-8",
        )
        self._write_source_selection()
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` |
| `ATOM-002` | `SRC-001.P02` | `GSR 2; SRC-001.P02` | `SRC-001.P02` | `GSR 2` | Поведение второго условия не определено. | `gap` | `GAP-PRIMARY` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- |
| `ATOM-001` | Открыть список значений поля. | Отображаются все и только значения DICT-001. | `TC-001` | `covered` |
| `ATOM-002` | Не создавать кейс до уточнения. | none_required:blocked | `GAP-PRIMARY` | `gap` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-values-shown` | Отображаются все и только значения DICT-001. | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | `TC-001` | `covered` | `-` |
| `OBL-002` | `WP-01` | `SRC-001.P02` | `ATOM-002` | `field-property` | `ambiguous-behavior` | Не создавать кейс до уточнения. | `GSR 2; SRC-001.P02` | `SRC-001.P02` | `GSR 2` | `GAP-PRIMARY` | `gap` | `-` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\n"
            "### GAP-PRIMARY\n\n"
            "**FT Reference:** `GSR 2; SRC-001.P02`\n"
            f"**Impact:** `{impact}`\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-PRIMARY |\n"
            "| affected_assertion_id | ASSERT-002 |\n"
            "| affected_atom_id | ATOM-002 |\n"
            "| status | open |\n"
            "**Handling:** Уточнить поведение.\n",
            encoding="utf-8",
        )
        spec, baseline, candidate_ids = self._materialize_source_row_contract(
            (
                {
                    "source_row_id": "SRC-001.P01",
                    "in_scope": "yes",
                    "position": 1,
                    "bounded_source_text": first_assertion.exact_source_text,
                    "source_context_class": "document-global-constraints",
                    "requirement_codes": "GSR 1",
                },
                {
                    "source_row_id": "SRC-001.P02",
                    "in_scope": "unclear",
                    "position": 2,
                    "bounded_source_text": gap_source_text,
                    "source_context_class": "scope-local",
                    "requirement_codes": "GSR 2",
                },
            )
        )
        gap_assertion = SourceAssertion(
            assertion_id="ASSERT-002",
            source_path="fts/demo/source/main.xhtml",
            source_context_class="scope-local",
            locator="/*/*[1]/*[2]",
            exact_source_text=gap_source_text,
            canonical_statement="Поведение второго условия не определено.",
            polarity="positive",
            semantic_disposition="ambiguous",
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Требуется уточнить поведение второго условия до исполнения."
            ),
            risk=gap_risk,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=("GSR 2",),
            requirement_code_bindings=(
                RequirementCodeBinding("GSR 2", "SRC-001.P02", "xhtml-row", "GSR 2"),
            ),
            clause_evidence_bindings=(),
            source_row_id="SRC-001.P02",
            atom_id="ATOM-002",
            obligation_ids=(),
            execution_dependency_gap_ids=(),
            primary_gap_id=assertion_gap_id,
            disposition_rationale=(
                "Источник прямо не определяет поведение второго условия."
            ),
        )
        manifest = build_source_assertion_manifest(
            self.root,
            scope_slug="demo-scope",
            coverage_gaps_path=(
                "fts/demo/work/test-design/demo-scope/coverage-gaps.md"
            ),
            source_paths=("fts/demo/source/main.xhtml",),
            assertions=(first_assertion, gap_assertion),
            source_row_extraction_spec_digest=spec.digest,
            source_row_baseline_digest=baseline.digest,
            source_row_candidate_count=baseline.candidate_count,
            source_row_candidate_ids=candidate_ids,
            expected_source_row_ids=("SRC-001.P01", "SRC-001.P02"),
            **self._source_first_external_evidence(),
        )
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=tuple(
                self._verified_review(item) for item in manifest.assertions
            ),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        (self.design / "source-assertion-review.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def add_ready_assertion_to_dependency_blocked_contract(self) -> None:
        assertions_path = self.design / "source-assertions.json"
        blocked_assertion = SourceAssertion.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))["assertions"][0]
        )
        ready_source_text = "GSR 2. После действия отображается подтверждение."
        xhtml_path = self.ft / "source" / "main.xhtml"
        xhtml_path.write_text(
            "<html><body>"
            f"<p>{blocked_assertion.exact_source_text}</p>"
            f"<p>{ready_source_text}</p>"
            "<p>External ancestor context.</p>"
            "<p>External cross-reference context.</p>"
            "</body></html>\n",
            encoding="utf-8",
        )
        self._write_source_selection()
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").rstrip()
            + "\n| `ATOM-002` | `SRC-001.P02` | `GSR 2; SRC-001.P02` | "
            "`SRC-001.P02` | `GSR 2` | После действия отображается "
            "подтверждение. | `covered` | `TC-002` |\n",
            encoding="utf-8",
        )
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").rstrip()
            + "\n| `ATOM-002` | Выполнить действие. | Отображается подтверждение. "
            "| `TC-002` | `covered` |\n",
            encoding="utf-8",
        )
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").rstrip()
            + "\n| `OBL-002` | `WP-01` | `SRC-001.P02` | `ATOM-002` | "
            "`field-property` | `positive-acceptance` | Отображается подтверждение. "
            "| `GSR 2; SRC-001.P02` | `SRC-001.P02` | `GSR 2` | `TC-002` "
            "| `covered` | `-` |\n",
            encoding="utf-8",
        )
        spec, baseline, candidate_ids = self._materialize_source_row_contract(
            (
                {
                    "source_row_id": "SRC-001.P01",
                    "in_scope": "yes",
                    "position": 1,
                    "bounded_source_text": blocked_assertion.exact_source_text,
                    "source_context_class": "document-global-constraints",
                    "requirement_codes": "GSR 1",
                },
                {
                    "source_row_id": "SRC-001.P02",
                    "in_scope": "yes",
                    "position": 2,
                    "bounded_source_text": ready_source_text,
                    "source_context_class": "scope-local",
                    "requirement_codes": "GSR 2",
                },
            )
        )
        ready_assertion = SourceAssertion(
            assertion_id="ASSERT-002",
            source_path="fts/demo/source/main.xhtml",
            source_context_class="scope-local",
            locator="/*/*[1]/*[2]",
            exact_source_text=ready_source_text,
            canonical_statement="После действия отображается подтверждение.",
            polarity="positive",
            semantic_disposition="testable",
            execution_readiness="ready",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            risk="medium",
            condition_clauses=("Открыта форма с доступным действием.",),
            action_clauses=("Выполнить действие.",),
            oracle_clauses=("Отображается подтверждение.",),
            requirement_codes=("GSR 2",),
            requirement_code_bindings=(
                RequirementCodeBinding(
                    "GSR 2", "SRC-001.P02", "xhtml-row", "GSR 2"
                ),
            ),
            clause_evidence_bindings=tuple(
                ClauseEvidenceBinding(
                    clause_kind=kind,
                    clause_index=0,
                    source_row_id="SRC-001.P02",
                    evidence_role=kind,
                    exact_source_fragment=ready_source_text,
                )
                for kind in ("condition", "action", "oracle")
            ),
            source_row_id="SRC-001.P02",
            atom_id="ATOM-002",
            obligation_ids=("OBL-002",),
            execution_dependency_gap_ids=(),
            primary_gap_id=None,
        )
        manifest = build_source_assertion_manifest(
            self.root,
            scope_slug="demo-scope",
            coverage_gaps_path=(
                "fts/demo/work/test-design/demo-scope/coverage-gaps.md"
            ),
            source_paths=("fts/demo/source/main.xhtml",),
            assertions=(blocked_assertion, ready_assertion),
            source_row_extraction_spec_digest=spec.digest,
            source_row_baseline_digest=baseline.digest,
            source_row_candidate_count=baseline.candidate_count,
            source_row_candidate_ids=candidate_ids,
            expected_source_row_ids=("SRC-001.P01", "SRC-001.P02"),
            **self._source_first_external_evidence(),
        )
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=tuple(
                self._verified_review(item) for item in manifest.assertions
            ),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        (self.design / "source-assertion-review.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def refresh_source_assertion_gap_binding(self) -> None:
        assertions_path = self.design / "source-assertions.json"
        manifest = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        )
        gaps_path = self.design / "coverage-gaps.md"
        manifest = replace(
            manifest,
            coverage_gaps_artifact=RegisteredArtifact(
                gaps_path.relative_to(self.root).as_posix(),
                self._file_sha256(gaps_path),
            ),
        )
        manifest.validate(self.root)
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=tuple(
                self._verified_review(item) for item in manifest.assertions
            ),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        (self.design / "source-assertion-review.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def add_second_assertion_to_primary_gap(self) -> None:
        assertions_path = self.design / "source-assertions.json"
        existing = tuple(
            SourceAssertion.from_dict(item)
            for item in json.loads(assertions_path.read_text(encoding="utf-8"))[
                "assertions"
            ]
        )
        third_source_text = "GSR 3. Поведение третьего условия не определено."
        xhtml_path = self.ft / "source" / "main.xhtml"
        xhtml_path.write_text(
            xhtml_path.read_text(encoding="utf-8").replace(
                "</body>", f"<p>{third_source_text}</p></body>"
            ),
            encoding="utf-8",
        )
        self._write_source_selection()
        rows = {
            "atomic-requirements-ledger.md": (
                "| `ATOM-003` | `SRC-001.P03` | `GSR 3; SRC-001.P03` | "
                "`SRC-001.P03` | `GSR 3` | Поведение третьего условия не "
                "определено. | `gap` | `GAP-PRIMARY` |"
            ),
            "package-test-design-plan.md": (
                "| `ATOM-003` | Не создавать кейс до уточнения. | "
                "none_required:blocked | `GAP-PRIMARY` | `gap` |"
            ),
            "coverage-obligation-table.md": (
                "| `OBL-003` | `WP-01` | `SRC-001.P03` | `ATOM-003` | "
                "`field-property` | `ambiguous-behavior` | Не создавать кейс до "
                "уточнения. | `GSR 3; SRC-001.P03` | `SRC-001.P03` | `GSR 3` | "
                "`GAP-PRIMARY` | `gap` | `-` |"
            ),
        }
        for name, row in rows.items():
            path = self.design / name
            path.write_text(
                path.read_text(encoding="utf-8").rstrip() + "\n" + row + "\n",
                encoding="utf-8",
            )
        gaps_path = self.design / "coverage-gaps.md"
        gaps_path.write_text(
            gaps_path.read_text(encoding="utf-8")
            .replace(
                "| affected_assertion_id | ASSERT-002 |",
                "| affected_assertion_id | ASSERT-002; ASSERT-003 |",
            )
            .replace(
                "| affected_atom_id | ATOM-002 |",
                "| affected_atom_id | ATOM-002; ATOM-003 |",
            ),
            encoding="utf-8",
        )
        spec, baseline, candidate_ids = self._materialize_source_row_contract(
            (
                {
                    "source_row_id": "SRC-001.P01",
                    "in_scope": "yes",
                    "position": 1,
                    "bounded_source_text": existing[0].exact_source_text,
                    "source_context_class": "document-global-constraints",
                    "requirement_codes": "GSR 1",
                },
                {
                    "source_row_id": "SRC-001.P02",
                    "in_scope": "unclear",
                    "position": 2,
                    "bounded_source_text": existing[1].exact_source_text,
                    "source_context_class": "scope-local",
                    "requirement_codes": "GSR 2",
                },
                {
                    "source_row_id": "SRC-001.P03",
                    "in_scope": "unclear",
                    "position": 5,
                    "bounded_source_text": third_source_text,
                    "source_context_class": "scope-local",
                    "requirement_codes": "GSR 3",
                },
            )
        )
        third = SourceAssertion(
            assertion_id="ASSERT-003",
            source_path="fts/demo/source/main.xhtml",
            source_context_class="scope-local",
            locator="/*/*[1]/*[5]",
            exact_source_text=third_source_text,
            canonical_statement="Поведение третьего условия не определено.",
            polarity="positive",
            semantic_disposition="ambiguous",
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Требуется уточнить поведение третьего условия до исполнения."
            ),
            risk="medium",
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=("GSR 3",),
            requirement_code_bindings=(
                RequirementCodeBinding("GSR 3", "SRC-001.P03", "xhtml-row", "GSR 3"),
            ),
            clause_evidence_bindings=(),
            source_row_id="SRC-001.P03",
            atom_id="ATOM-003",
            obligation_ids=(),
            execution_dependency_gap_ids=(),
            primary_gap_id="GAP-PRIMARY",
            disposition_rationale=(
                "Источник прямо не определяет поведение третьего условия."
            ),
        )
        manifest = build_source_assertion_manifest(
            self.root,
            scope_slug="demo-scope",
            coverage_gaps_path=(
                "fts/demo/work/test-design/demo-scope/coverage-gaps.md"
            ),
            source_paths=("fts/demo/source/main.xhtml",),
            assertions=(*existing, third),
            source_row_extraction_spec_digest=spec.digest,
            source_row_baseline_digest=baseline.digest,
            source_row_candidate_count=baseline.candidate_count,
            source_row_candidate_ids=candidate_ids,
            expected_source_row_ids=(
                "SRC-001.P01",
                "SRC-001.P02",
                "SRC-001.P03",
            ),
            **self._source_first_external_evidence(),
        )
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=tuple(
                self._verified_review(item) for item in manifest.assertions
            ),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        (self.design / "source-assertion-review.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def attach_source_first_constraint_gap(self, impact: str | None) -> None:
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc |",
                "| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc | constraint_gap_ids |",
            ).replace(
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                1,
            ).replace(
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` |",
                "| `ATOM-001` | `SRC-001.P01` | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `covered` | `TC-001` | `GAP-CONSTRAINT` |",
            ),
            encoding="utf-8",
        )
        impact_line = f"**Impact:** `{impact}`\n" if impact is not None else ""
        (self.design / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\n"
            "### GAP-CONSTRAINT\n\n"
            "**FT Reference:** `GSR 1; SRC-001.P01`\n"
            + impact_line
            + "| field | value |\n"
            + "| --- | --- |\n"
            + "| gap_id | GAP-CONSTRAINT |\n"
            + "| affected_assertion_id | ASSERT-001 |\n"
            + "| affected_atom_id | ATOM-001 |\n"
            + "| status | open |\n"
            + "**Handling:** Сохранить ограничение как constraint.\n",
            encoding="utf-8",
        )
        self.refresh_source_assertion_gap_binding()

    def convert_source_first_to_primary_gap(self, impact: str) -> None:
        exact_source_text = "GSR 1. Поле использует фиксированный список DICT-001."
        spec, baseline, candidate_ids = self._materialize_source_row_contract(
            (
                {
                    "source_row_id": "SRC-001.P01",
                    "in_scope": "unclear",
                    "position": 1,
                    "bounded_source_text": exact_source_text,
                    "source_context_class": "document-global-constraints",
                    "requirement_codes": "GSR 1",
                },
            )
        )
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P01` | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `gap` | `GAP-PRIMARY` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- |
| `ATOM-001` | Не создавать кейс до уточнения. | none_required:blocked | `GAP-PRIMARY` | `gap` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `dictionary-source` | `dictionary-values-shown` | Не создавать кейс до уточнения. | `GSR 1; SRC-001.P01; DICT-001` | `SRC-001.P01` | `GSR 1` | `GAP-PRIMARY` | `gap` | `-` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\n"
            "### GAP-PRIMARY\n\n"
            "**FT Reference:** `GSR 1; SRC-001.P01`\n"
            f"**Impact:** `{impact}`\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-PRIMARY |\n"
            "| affected_assertion_id | ASSERT-001 |\n"
            "| affected_atom_id | ATOM-001 |\n"
            "| status | open |\n"
            "**Handling:** Уточнить поведение.\n",
            encoding="utf-8",
        )
        assertion = SourceAssertion(
            assertion_id="ASSERT-001",
            source_path="fts/demo/source/main.xhtml",
            source_context_class="document-global-constraints",
            locator="/*/*[1]/*[1]",
            exact_source_text=exact_source_text,
            canonical_statement="Поле использует фиксированный список DICT-001.",
            polarity="positive",
            semantic_disposition="ambiguous",
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Требуется уточнить поведение фиксированного списка до исполнения."
            ),
            risk="medium",
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=("GSR 1",),
            requirement_code_bindings=(
                RequirementCodeBinding("GSR 1", "SRC-001.P01", "xhtml-row", "GSR 1"),
            ),
            clause_evidence_bindings=(),
            source_row_id="SRC-001.P01",
            atom_id="ATOM-001",
            obligation_ids=(),
            execution_dependency_gap_ids=(),
            primary_gap_id="GAP-PRIMARY",
            disposition_rationale=(
                "Источник не определяет проверяемое поведение фиксированного списка."
            ),
        )
        manifest = build_source_assertion_manifest(
            self.root,
            scope_slug="demo-scope",
            coverage_gaps_path=(
                "fts/demo/work/test-design/demo-scope/coverage-gaps.md"
            ),
            source_paths=("fts/demo/source/main.xhtml",),
            assertions=(assertion,),
            source_row_extraction_spec_digest=spec.digest,
            source_row_baseline_digest=baseline.digest,
            source_row_candidate_count=baseline.candidate_count,
            source_row_candidate_ids=candidate_ids,
            expected_source_row_ids=("SRC-001.P01",),
            **self._source_first_external_evidence(),
        )
        assertions_path = self.design / "source-assertions.json"
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=(
                self._verified_review(assertion),
            ),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        (self.design / "source-assertion-review.json").write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def configure_reset_plan(
        self,
        *,
        property_type: str,
        include_state_contract: bool,
        state_relation: str = "different-from-captured-initial",
        initial_state_capture: str = "Зафиксировать видимое исходное состояние.",
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
| `PLAN-001` | `ATOM-001` | Нажать `Очистить` после подготовки изменённого состояния. | Состояние совпадает с зафиксированным исходным. | `changed-state` | `{property_type}` | {initial_state_capture} | Выбрать видимое состояние, отличное от зафиксированного исходного. | До `Очистить` видимое состояние отличается от зафиксированного исходного. | `{state_relation}` | `TC-001` | `covered` |
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

    def test_semantic_bridge_projection_is_lossless_and_fingerprint_bound(self) -> None:
        self.enable_source_first_contract()
        semantic_path = self.enable_semantic_design_projection()

        first = self.compile(cycle_name="semantic-projection-a")
        first_package = load_prepared_package(first.stage_package, self.root)
        evidence = (first.stage_package.parent / "source-evidence.md").read_text(
            encoding="utf-8"
        )
        for marker in (
            "semantic-design-compiler-projection-v1",
            "semantic-marker-alpha",
            "scope_boundary_artifact",
            "bridge_receipt_artifact",
            "source-reviewer.prepare_evidence_set",
            "OBL-001",
        ):
            self.assertIn(marker, evidence)
        inputs = resolve_workflow_compiler_inputs(
            workflow_state=self.state,
            repo_root=self.root,
            expected_ft_slug="demo",
        )
        self.assertTrue(semantic_path.samefile(inputs["semantic_design"]))
        self.assertIn("scope_boundary_decision", inputs)
        self.assertIn("semantic_design_bridge_receipt", inputs)
        self.assertIn("selected_source_001", inputs)
        self.assertIn("workflow_state", inputs)

        payload = json.loads(semantic_path.read_text(encoding="utf-8"))
        payload["dependency_bindings"][0][
            "mapping_rationale"
        ] = "semantic-marker-beta"
        semantic_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()
        second = self.compile(cycle_name="semantic-projection-b")
        second_package = load_prepared_package(second.stage_package, self.root)
        self.assertNotEqual(
            first_package.input_fingerprint,
            second_package.input_fingerprint,
        )

    def test_semantic_bridge_projection_fails_closed_on_missing_or_mismatched_input(self) -> None:
        self.enable_source_first_contract()
        semantic_path = self.enable_semantic_design_projection()
        payload = json.loads(semantic_path.read_text(encoding="utf-8"))
        payload["obligations"][0]["package_id"] = "wrong-package"
        semantic_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()
        with self.assertRaisesRegex(StageRuntimeError, "compiled package_id"):
            self.compile(cycle_name="semantic-package-mismatch")

        semantic_path.unlink()
        with self.assertRaisesRegex(StageRuntimeError, "workflow artifact is missing"):
            self.compile(cycle_name="semantic-missing")

    def test_semantic_bridge_projection_rejects_stale_or_partial_receipt(self) -> None:
        self.enable_source_first_contract()
        semantic_path = self.enable_semantic_design_projection()
        payload = json.loads(semantic_path.read_text(encoding="utf-8"))
        payload["dependency_bindings"][0]["mapping_rationale"] = "unreceipted drift"
        semantic_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            StageRuntimeError,
            "semantic_design_artifact_sha256",
        ):
            self.compile(cycle_name="semantic-stale-receipt")

        self._refresh_semantic_bridge_receipt()
        receipt_path = self.design / "semantic-design-bridge-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        del receipt["downstream_evidence_readiness"]
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "canonical downstream evidence"):
            self.compile(cycle_name="semantic-partial-receipt")

    def test_semantic_design_requires_boundary_and_bridge_receipt(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        receipt_path = self.design / "semantic-design-bridge-receipt.json"
        receipt_path.unlink()
        with self.assertRaisesRegex(
            StageRuntimeError,
            "semantic-design-bridge-receipt.json",
        ):
            self.compile(cycle_name="semantic-missing-receipt")

    def test_semantic_bridge_projection_rejects_dependency_graph_drift(self) -> None:
        self.enable_source_first_contract()
        semantic_path = self.enable_semantic_design_projection()
        payload = json.loads(semantic_path.read_text(encoding="utf-8"))
        payload["dependency_bindings"][0]["linked_obligation_ids"] = ["OBL-BOGUS"]
        semantic_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()
        with self.assertRaisesRegex(StageRuntimeError, "full ASSERT->ATOM->OBL chain"):
            self.compile(cycle_name="semantic-dependency-drift")

    def test_semantic_bridge_projection_accepts_gap_bound_non_testable_dependency(self) -> None:
        self.enable_source_first_contract()
        semantic_path = self.enable_semantic_design_projection()
        manifest_path = self.design / "source-assertions.json"
        review_path = self.design / "source-assertion-review.json"
        gaps_path = self.design / "coverage-gaps.md"
        ledger_path = self.design / "atomic-requirements-ledger.md"
        boundary_path = self.design / "scope-boundary-decision.json"
        manifest = SourceAssertionManifest.from_dict(
            json.loads(manifest_path.read_text(encoding="utf-8"))
        )
        source_assertion = manifest.assertions[0]
        gap_assertion = SourceAssertion(
            assertion_id="ASSERT-002",
            source_path=source_assertion.source_path,
            source_context_class=source_assertion.source_context_class,
            locator=source_assertion.locator,
            exact_source_text=source_assertion.exact_source_text,
            canonical_statement=(
                "Внутренний идентификатор задан источником, но не имеет "
                "разрешённого интерфейса наблюдения."
            ),
            polarity="positive",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            risk="medium",
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=(),
            requirement_code_bindings=(),
            clause_evidence_bindings=(),
            source_row_id=source_assertion.source_row_id,
            atom_id="ATOM-002",
            obligation_ids=(),
            execution_dependency_gap_ids=(),
            primary_gap_id=None,
            disposition_rationale=(
                "GAP-001 сохраняет непроверяемый внутренний эффект без "
                "выдумывания интерфейса."
            ),
        )
        gaps_path.write_text(
            "# Coverage Gaps\n\n"
            "## GAP-001\n\n"
            "**Impact:** `non-blocking`\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-001 |\n"
            "| gap_type | missing-observation-interface |\n"
            "| source_row_ids | SRC-001.P01 |\n"
            "| affected_assertion_id | ASSERT-002 |\n"
            "| affected_atom_id | ATOM-002 |\n"
            "| risk | medium |\n"
            "| blocks_ready_for_review | no |\n"
            "| status | open |\n",
            encoding="utf-8",
        )
        updated_manifest = replace(
            manifest,
            coverage_gaps_artifact=RegisteredArtifact(
                path=manifest.coverage_gaps_artifact.path,
                sha256=hashlib.sha256(gaps_path.read_bytes()).hexdigest(),
            ),
            assertions=(*manifest.assertions, gap_assertion),
        )
        manifest_path.write_text(
            json.dumps(updated_manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        review = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=updated_manifest.digest,
            decision="accepted",
            assertion_reviews=(
                self._verified_review(source_assertion),
                self._verified_review(gap_assertion),
            ),
            source_inventory_review=self._source_inventory_review(updated_manifest),
            scope_boundary_review=self._scope_boundary(updated_manifest),
        )
        review_path.write_text(
            json.dumps(review.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        ledger_path.write_text(
            ledger_path.read_text(encoding="utf-8")
            + "| `ATOM-002` | `none_required` | `GSR 1` | `SRC-001.P01` | "
            f"`none_required` | {gap_assertion.canonical_statement} | "
            "`not-applicable` | `none_required` |\n",
            encoding="utf-8",
        )
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8")
            + "| `OBL-CONTEXT-001` | `demo-package` | `none_required` | "
            "`ATOM-002` | `context` | `not-applicable-context` | "
            f"{gap_assertion.canonical_statement} | `GSR 1` | `SRC-001.P01` | "
            "`none_required` | `not-applicable` | `not-applicable` | "
            "Explicit non-testable gap accounting. | `none_required` | "
            "`none_required` | `none_required` | `none` |\n",
            encoding="utf-8",
        )
        gap_dependency = {
            "dependency_id": "DEP-002",
            "kind": "other",
            "name": "internal-id",
            "source_row_ids": ["SRC-001.P01"],
            "resolution": "source-provided",
            "target_source_row_ids": ["SRC-001.P01"],
            "exact_source_fragments": ["фиксированный список DICT-001"],
            "gap_ids": ["GAP-001"],
            "blocking": False,
            "rationale": "Внутренний эффект не имеет интерфейса наблюдения.",
        }
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
        boundary["dependencies"].append(gap_dependency)
        boundary["gaps"] = [
            {
                "gap_id": "GAP-001",
                "gap_type": "missing-observation-interface",
                "source_row_ids": ["SRC-001.P01"],
                "source_refs": ["GSR 1"],
                "exact_source_fragments": ["фиксированный список DICT-001"],
                "blocking": False,
                "clarification_question": "Как наблюдать внутренний идентификатор?",
                "downstream_handling": "carry-to-source-model",
            }
        ]
        boundary_path.write_text(
            json.dumps(boundary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic["scope_boundary_decision_sha256"] = canonical_payload_sha256(
            boundary
        )
        semantic["source_designs"][0]["assertions"].append(
            {
                "assertion_id": gap_assertion.assertion_id,
                "canonical_statement": gap_assertion.canonical_statement,
                "polarity": gap_assertion.polarity,
                "semantic_disposition": gap_assertion.semantic_disposition,
                "execution_readiness": gap_assertion.execution_readiness,
                "execution_readiness_rationale": NO_REQUIRED_CHANGE,
                "risk": gap_assertion.risk,
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "requirement_codes": [],
                "requirement_code_evidence": [],
                "clause_evidence": [],
                "supporting_source_bindings": [],
                "clarification_clause_bindings": [],
                "atom_id": gap_assertion.atom_id,
                "obligation_ids": [],
                "disposition_rationale": gap_assertion.disposition_rationale,
                "source_property_id": "none_required",
                "field_or_block": "Внутренний идентификатор",
                "source_reference": "GSR 1",
            }
        )
        semantic["dependency_bindings"].append(
            {
                **gap_dependency,
                "semantic_disposition": "gap-bound",
                "linked_assertion_ids": ["ASSERT-002"],
                "linked_atom_ids": ["ATOM-002"],
                "linked_obligation_ids": [],
                "mapping_rationale": "GAP-001 связывает точную non-testable цепочку.",
            }
        )
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()

        result = self.compile(cycle_name="semantic-gap-bound-dependency")

        self.assertEqual("release", result.output_mode)

    def test_semantic_bridge_projection_rejects_oracle_graph_drift(self) -> None:
        self.enable_source_first_contract()
        semantic_path = self.enable_semantic_design_projection()
        payload = json.loads(semantic_path.read_text(encoding="utf-8"))
        payload["obligations"][0]["scope_obligation_ids"] = ["SO-NEG-001"]
        payload["negative_oracles"] = [
            {
                "signal_id": "SIG-NEG-001",
                "requirement_codes": ["GSR 1"],
                "scope_obligation_id": "SO-NEG-001",
                "source_row_id": "SRC-001.P01",
                "source_ref": "GSR 1; SRC-001.P01",
                "field_or_block": "Поле со справочником",
                "restriction_type": "dictionary-membership",
                "negative_class": "out-of-dictionary",
                "source_statement": "Поле использует фиксированный список DICT-001.",
                "representative_invalid_value": "C",
                "observable_oracle_found": "yes",
                "oracle_source": "Значение отсутствует в фиксированном перечне.",
                "oracle_status": "source-backed",
                "decision": "executable_tc",
                "planned_tc_or_gap": "TC-001",
                "gap_id": "none_required",
                "analyst_question": "none_required",
                "handoff_rule": "none_required",
                "calibration_notes": "none_required",
                "linked_atom_id": "ATOM-001",
                "linked_obligation_id": "OBL-BOGUS",
            }
        ]
        semantic_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        inventory = self.design / "negative-oracle-inventory.md"
        inventory.write_text(
            "| signal_id | scope_obligation_id |\n"
            "| --- | --- |\n"
            "| SIG-NEG-001 | SO-NEG-001 |\n",
            encoding="utf-8",
        )
        self.state.write_text(
            self.state.read_text(encoding="utf-8").replace(
                "  semantic_design_bridge_receipt: work/test-design/demo-scope/semantic-design-bridge-receipt.json\n",
                "  semantic_design_bridge_receipt: work/test-design/demo-scope/semantic-design-bridge-receipt.json\n"
                "  negative_oracle_inventory: work/test-design/demo-scope/negative-oracle-inventory.md\n",
            ),
            encoding="utf-8",
        )
        self._refresh_semantic_bridge_receipt()
        with self.assertRaisesRegex(StageRuntimeError, "unique known scope/OBL chain"):
            self.compile(cycle_name="semantic-oracle-drift")

    def test_semantic_candidate_without_gap_reaches_prepared_obligation(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_requiredness_oracle(
            decision="candidate_tc_required"
        )

        result = self.compile(cycle_name="semantic-candidate-no-gap")
        package = load_prepared_package(result.stage_package, self.root)
        obligations_path = self.root / next(
            item.path
            for item in package.package_artifacts
            if item.kind == "atomic-obligations"
        )
        obligation = load_obligations(obligations_path).obligations[0]

        self.assertEqual("ui-calibration-required", obligation.calibration_status)
        self.assertEqual((), obligation.constraint_gap_ids)

    def test_semantic_candidate_and_parent_gap_coexist_in_prepared_obligation(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_requiredness_oracle(
            decision="candidate_tc_required",
            parent_gap=True,
        )

        result = self.compile(cycle_name="semantic-candidate-parent-gap")
        package = load_prepared_package(result.stage_package, self.root)
        obligations_path = self.root / next(
            item.path
            for item in package.package_artifacts
            if item.kind == "atomic-obligations"
        )
        prepared = load_obligations(obligations_path)
        obligation = prepared.obligations[0]

        self.assertEqual("ui-calibration-required", obligation.calibration_status)
        self.assertEqual(("GAP-UI-001",), obligation.constraint_gap_ids)
        self.assertEqual("GAP-UI-001", prepared.coverage_gaps[0].gap_id)
        self.assertFalse(prepared.coverage_gaps[0].blocking)

    def test_semantic_context_only_gap_survives_compilation_without_fake_tc(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_context_only_gap()

        result = self.compile(cycle_name="semantic-context-only-gap")
        package = load_prepared_package(result.stage_package, self.root)
        obligations_path = self.root / next(
            item.path
            for item in package.package_artifacts
            if item.kind == "atomic-obligations"
        )
        prepared = load_obligations(obligations_path)

        self.assertEqual(1, len(prepared.obligations))
        obligation = prepared.obligations[0]
        self.assertEqual("OBL-CONTEXT-001", obligation.obligation_id)
        self.assertEqual("not-applicable", obligation.coverage_status)
        self.assertEqual("", obligation.planned_test_case_id)
        self.assertEqual("", obligation.gap_id)
        self.assertEqual(("GAP-CONTEXT-001",), obligation.constraint_gap_ids)
        self.assertEqual(1, len(prepared.coverage_gaps))
        self.assertEqual("GAP-CONTEXT-001", prepared.coverage_gaps[0].gap_id)
        self.assertFalse(prepared.coverage_gaps[0].blocking)
        self.assertEqual(
            0,
            sum(
                item.coverage_status == "testable"
                for item in prepared.obligations
            ),
        )

        evidence_text = next(
            (self.root / item.path).read_text(encoding="utf-8")
            for item in package.package_artifacts
            if item.kind == "source-evidence"
        )
        self.assertIn("## GAP-CONTEXT-001", evidence_text)
        self.assertIn("OBL-CONTEXT-001", evidence_text)
        self.assertIn("GAP-CONTEXT-001", evidence_text)

    def test_semantic_mixed_gap_links_testable_and_context_without_fake_tc(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_mixed_gap()

        result = self.compile(cycle_name="semantic-mixed-gap")
        package = load_prepared_package(result.stage_package, self.root)
        prepared = load_obligations(
            self.root
            / next(
                item.path
                for item in package.package_artifacts
                if item.kind == "atomic-obligations"
            )
        )
        by_id = {item.obligation_id: item for item in prepared.obligations}

        self.assertEqual({"OBL-001", "OBL-CONTEXT-001"}, set(by_id))
        self.assertEqual("testable", by_id["OBL-001"].coverage_status)
        self.assertEqual("TC-001", by_id["OBL-001"].planned_test_case_id)
        self.assertEqual(
            ("GAP-MIXED-001",), by_id["OBL-001"].constraint_gap_ids
        )
        self.assertEqual(
            "not-applicable", by_id["OBL-CONTEXT-001"].coverage_status
        )
        self.assertEqual("", by_id["OBL-CONTEXT-001"].planned_test_case_id)
        self.assertEqual(
            ("GAP-MIXED-001",),
            by_id["OBL-CONTEXT-001"].constraint_gap_ids,
        )
        self.assertEqual(1, len(prepared.coverage_gaps))
        self.assertEqual("GAP-MIXED-001", prepared.coverage_gaps[0].gap_id)
        self.assertEqual(
            1,
            sum(
                item.coverage_status == "testable"
                for item in prepared.obligations
            ),
        )

    def test_semantic_gap_exact_mapping_rejects_moved_affected_atom(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_context_only_gap()
        manifest = SourceAssertionManifest.from_dict(
            json.loads(
                (self.design / "source-assertions.json").read_text(encoding="utf-8")
            )
        )
        projection = _load_semantic_compiler_projection(
            repo_root=self.root,
            package_id="demo-package",
            semantic_design_path=self.design / "semantic-design.json",
            scope_boundary_path=self.design / "scope-boundary-decision.json",
            bridge_receipt_path=self.design / "semantic-design-bridge-receipt.json",
            negative_inventory_path=None,
            requiredness_inventory_path=None,
        )
        gaps_path = self.design / "coverage-gaps.md"
        gaps_path.write_text(
            gaps_path.read_text(encoding="utf-8").replace(
                "| affected_atom_id | ATOM-001 |",
                "| affected_atom_id | ATOM-MOVED-001 |",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "GAP-CONTEXT-001 affected ATOM set drifted",
        ):
            _validate_semantic_projection_graph(
                projection=projection,
                manifest=manifest,
                ledger_by_atom={
                    "ATOM-001": {
                        "coverage_status": "not-applicable",
                        "constraint_gap_ids": "none_required",
                    }
                },
                obligation_rows=(
                    {
                        "obligation_id": "OBL-CONTEXT-001",
                        "linked_atom_id": "ATOM-001",
                    },
                ),
                coverage_gaps_path=gaps_path,
            )

    def test_semantic_gap_exact_mapping_rejects_extra_constraint_atom(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_context_only_gap()
        manifest = SourceAssertionManifest.from_dict(
            json.loads(
                (self.design / "source-assertions.json").read_text(encoding="utf-8")
            )
        )
        projection = _load_semantic_compiler_projection(
            repo_root=self.root,
            package_id="demo-package",
            semantic_design_path=self.design / "semantic-design.json",
            scope_boundary_path=self.design / "scope-boundary-decision.json",
            bridge_receipt_path=self.design / "semantic-design-bridge-receipt.json",
            negative_inventory_path=None,
            requiredness_inventory_path=None,
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "GAP-CONTEXT-001 constraint ATOM set drifted",
        ):
            _validate_semantic_projection_graph(
                projection=projection,
                manifest=manifest,
                ledger_by_atom={
                    "ATOM-001": {
                        "coverage_status": "not-applicable",
                        "constraint_gap_ids": "none_required",
                    },
                    "ATOM-EXTRA-001": {
                        "coverage_status": "not-applicable",
                        "constraint_gap_ids": "GAP-CONTEXT-001",
                    },
                },
                obligation_rows=(
                    {
                        "obligation_id": "OBL-CONTEXT-001",
                        "linked_atom_id": "ATOM-001",
                    },
                ),
                coverage_gaps_path=self.design / "coverage-gaps.md",
            )

    def test_semantic_candidate_rejects_materialized_calibration_tamper(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_requiredness_oracle(
            decision="candidate_tc_required"
        )
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "`ui-calibration-required`", "`none`", 1
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "requires materialized calibration_status=ui-calibration-required",
        ):
            self.compile(cycle_name="semantic-candidate-calibration-tamper")

    def test_semantic_candidate_rejects_atom_coverage_tamper(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_requiredness_oracle(
            decision="candidate_tc_required"
        )
        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_path.write_text(
            ledger_path.read_text(encoding="utf-8").replace(
                "`covered_with_ui_calibration`", "`covered`", 1
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "coverage_status=covered_with_ui_calibration",
        ):
            self.compile(cycle_name="semantic-candidate-ledger-tamper")

    def test_semantic_executable_oracle_rejects_calibration_tamper(self) -> None:
        self.enable_source_first_contract()
        self.enable_semantic_design_projection()
        self.configure_semantic_requiredness_oracle(decision="executable_tc")
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "`none`", "`ui-calibration-required`", 1
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "executable oracle SIG-REQ-001 requires explicit materialized "
            "calibration_status=none",
        ):
            self.compile(cycle_name="semantic-executable-calibration-tamper")

    def test_compiler_reuses_only_identical_target_bound_package(self) -> None:
        original = self.compile()

        reused = self.compile(reuse_if_current=True)

        self.assertFalse(original.cache_reused)
        self.assertTrue(reused.cache_reused)
        original_package = load_prepared_package(original.stage_package, self.root)
        reused_package = load_prepared_package(reused.stage_package, self.root)
        self.assertEqual(
            original_package.input_fingerprint,
            reused_package.input_fingerprint,
        )

        plan_path = self.design / "package-test-design-plan.md"
        plan_path.write_text(
            plan_path.read_text(encoding="utf-8").replace(
                "Проверить все значения.",
                "Проверить все значения повторно.",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "stale prepared package cache"):
            self.compile(reuse_if_current=True)

    def test_v2_resolver_and_cache_ignore_declared_source_first_artifact(self) -> None:
        ignored = self.design / "source-assertions.json"
        ignored.write_text('{"unused":"alpha"}\n', encoding="utf-8")
        self.state.write_text(
            self.state.read_text(encoding="utf-8").replace(
                "  coverage_gaps: work/test-design/demo-scope/coverage-gaps.md\n",
                "  coverage_gaps: work/test-design/demo-scope/coverage-gaps.md\n"
                "  source_assertions: work/test-design/demo-scope/source-assertions.json\n",
            ),
            encoding="utf-8",
        )

        inputs = resolve_workflow_compiler_inputs(
            workflow_state=self.state,
            repo_root=self.root,
            expected_ft_slug="demo",
        )
        self.assertNotIn("source_assertions", inputs)
        first = self.compile(
            cycle_name="v2-ignored-source-first",
            reuse_if_current=True,
        )
        self.assertFalse(first.cache_reused)

        ignored.write_text('{"unused":"beta"}\n', encoding="utf-8")
        second = self.compile(
            cycle_name="v2-ignored-source-first",
            reuse_if_current=True,
        )
        self.assertTrue(second.cache_reused)

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

    def test_blocks_unbound_temporal_initial_state_claim_in_source_first_reset(self) -> None:
        assertions_path, _ = self.enable_source_first_contract()
        assertion = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        ).assertions[0]
        state_change = PreparedStateChange(
            initial_state_capture=(
                "После первого добавления оба поля нового блока пусты."
            ),
            changed_state_setup=(
                "Заполнить тип дохода значением `Аренда` и доход значением `1000`."
            ),
            pre_action_state_oracle="Оба заполненных значения видимы.",
            relation="different-from-captured-initial",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            _resolve_source_first_state_change(
                state_change=state_change,
                source_assertion=assertion,
                obligation_id="OBL-015",
                atom_id="ATOM-015",
                plan_path=self.design / "package-test-design-plan.md",
                plan_rows=({"design_item_id": "PD-014"},),
                repo_root=self.root,
            )

        self.assertEqual(
            "source-first-state-change-initial-binding-required",
            raised.exception.code,
        )

    def test_blocks_unbound_non_temporal_initial_state_claim_in_source_first_reset(self) -> None:
        assertions_path, _ = self.enable_source_first_contract()
        assertion = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        ).assertions[0]

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            _resolve_source_first_state_change(
                state_change=PreparedStateChange(
                    initial_state_capture="Оба поля нового блока пусты.",
                    changed_state_setup="Заполнить поля.",
                    pre_action_state_oracle="Заполненные значения видимы.",
                    relation="different-from-captured-initial",
                ),
                source_assertion=assertion,
                obligation_id="OBL-015",
                atom_id="ATOM-015",
                plan_path=self.design / "package-test-design-plan.md",
                plan_rows=({"design_item_id": "PD-014"},),
                repo_root=self.root,
            )

        self.assertEqual(
            "source-first-state-change-initial-binding-required",
            raised.exception.code,
        )

    def test_resolves_source_bound_initial_state_from_condition_clause(self) -> None:
        assertions_path, _ = self.enable_source_first_contract()
        assertion = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        ).assertions[0]
        temporal_claim = "После первого добавления оба поля нового блока пусты."
        assertion = replace(
            assertion,
            condition_clauses=(temporal_claim,),
        )

        resolved = _resolve_source_first_state_change(
            state_change=PreparedStateChange(
                initial_state_capture="source-condition:0",
                changed_state_setup="Заполнить поля.",
                pre_action_state_oracle="Заполненные значения видимы.",
                relation="different-from-captured-initial",
            ),
            source_assertion=assertion,
            obligation_id="OBL-015",
            atom_id="ATOM-015",
            plan_path=self.design / "package-test-design-plan.md",
            plan_rows=({"design_item_id": "PD-014"},),
            repo_root=self.root,
        )

        self.assertIsNotNone(resolved)
        self.assertEqual(temporal_claim, resolved.initial_state_capture)

    def test_compiler_resolves_source_first_reset_initial_state_binding(self) -> None:
        self.enable_source_first_contract()
        self.configure_reset_plan(
            property_type="pagination-reset",
            include_state_contract=True,
            initial_state_capture="source-condition:0",
        )

        result = self.compile()
        compiled = load_obligations(
            result.stage_package.parent / "atomic-obligations.json"
        ).obligations[0]

        self.assertEqual("reset-to-captured-initial", compiled.execution_semantics)
        self.assertEqual(
            "Открыта форма с проверяемым полем.",
            compiled.state_change.initial_state_capture,
        )

    def test_blocks_source_first_initial_state_binding_to_missing_condition(self) -> None:
        assertions_path, _ = self.enable_source_first_contract()
        assertion = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        ).assertions[0]

        with self.assertRaises(PreparedCompilerDiagnostic) as raised:
            _resolve_source_first_state_change(
                state_change=PreparedStateChange(
                    initial_state_capture="source-condition:9",
                    changed_state_setup="Заполнить поля.",
                    pre_action_state_oracle="Заполненные значения видимы.",
                    relation="different-from-captured-initial",
                ),
                source_assertion=assertion,
                obligation_id="OBL-015",
                atom_id="ATOM-015",
                plan_path=self.design / "package-test-design-plan.md",
                plan_rows=({"design_item_id": "PD-014"},),
                repo_root=self.root,
            )

        self.assertEqual(
            "source-first-state-change-initial-binding-invalid",
            raised.exception.code,
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

        self.assertEqual("release", result.output_mode)
        self.assertFalse(result.release_eligible)
        self.assertEqual((), result.blocking_gap_ids)
        self.assertEqual(
            ("legacy-source-contract",),
            result.release_blocking_finding_codes,
        )
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

- `FX-001`: portable synthetic source-backed card with the target field present.

| design_item_id | linked_atoms | planned_check | check_type | single_expected_behavior | input_class | test_data | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Открыть карточку и проверить поле. | `positive` | Поле отображается. | `n/a` | `none_required` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-001` | По `FX-001` очистить поле и записать evidence. | `negative` | Evidence записан. | `fixture-id:FX-001` | Целевое поле = `Тест` | `TC-002` | `covered` |
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
                "Открыть карточку и проверить поле.; Check type: positive",
                (
                    "По `FX-001` очистить поле и записать evidence.; "
                    "Check type: negative; "
                    "Fixture contract: - `FX-001`: portable synthetic source-backed "
                    "card with the target field present.; Test data: Целевое поле = `Тест`"
                ),
            ],
            [item.test_intent for item in obligations],
        )
        self.assertNotIn("FX-001", obligations[0].test_intent)

    def test_blocks_named_fixture_without_inline_contract(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | По `FX-404` ввести значение. | Значение отображается. | `fixture-id:FX-404` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("missing-fixture-contract", context.exception.code)

    def test_blocks_fx_contract_with_unnamed_other_required_controls(self) -> None:
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            """# Package Test Design Plan

- `FX-REQ-001`: целевое поле пусто; остальные видимые required controls имеют непустые значения.

| design_item_id | linked_atoms | planned_check | single_expected_behavior | input_class | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Использовать `FX-REQ-001` и нажать «Далее». | Целевое поле подсвечено. | `fixture-id:FX-REQ-001` | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | none_required:blocked | `n/a` | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as context:
            self.compile()

        self.assertEqual("generic-execution-fixture", context.exception.code)
        self.assertEqual("FX-REQ-001", context.exception.details[0]["fixture_id"])

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

    def test_blocks_noncanonical_prepared_output_layout_or_package_leaf(self) -> None:
        cycle = self.ft / "work" / "review-cycles" / "layout-cycle"
        attempt = cycle / "attempts" / "writer-r1" / "attempt-001"
        invalid_outputs = (
            cycle / "prepared-input" / "wrong-package",
            cycle / "prepared-input" / "demo-package" / "nested",
        )
        for index, output in enumerate(invalid_outputs):
            with self.subTest(index=index), self.assertRaisesRegex(
                StageRuntimeError,
                "prepared output must be under",
            ):
                compile_workflow_package(
                    workflow_state=self.state,
                    repo_root=self.root,
                    output_root=output,
                    package_id="demo-package",
                    attempt_root=attempt,
                    expected_ft_slug="demo",
                )

    def test_blocks_noncanonical_attempt_layout(self) -> None:
        cycle = self.ft / "work" / "review-cycles" / "layout-cycle"
        with self.assertRaisesRegex(StageRuntimeError, "attempt root must be under"):
            compile_workflow_package(
                workflow_state=self.state,
                repo_root=self.root,
                output_root=cycle / "prepared-input" / "demo-package",
                package_id="demo-package",
                attempt_root=(
                    cycle / "attempts" / "writer-r1" / "attempt-001" / "nested"
                ),
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

    def test_compiles_exact_reference_only_fixture_values_with_hierarchy(self) -> None:
        (self.design / "dictionary-inventory.md").write_text(
            """| dictionary_id | dictionary_name | active_values |
| --- | --- | --- |
| `DICT-001` | `Параметры визуальной оценки` | `DICT-101`; `DICT-102` |
| `DICT-101` | `Признаки алкоголика` | `Запах алкоголя`; `Отечность лица` |
| `DICT-102` | `Признаки другого состояния` | `Отечность лица`; `Иное значение` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | input_class | test_data | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | В группе `Признаки алкоголика` (`DICT-101`) последовательно выбрать `Запах алкоголя` и `Отечность лица`. | `two-values` | два явно названных значения `DICT-101` | Оба значения остаются выбранными. | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | `none_required` | `none_required` | none_required:blocked | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )
        obligation_table = self.design / "coverage-obligation-table.md"
        obligation_table.write_text(
            obligation_table.read_text(encoding="utf-8").replace(
                "`dictionary-values-shown`",
                "`selection-cardinality`",
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
        requirement = (
            load_obligations(obligation_path)
            .obligations[0]
            .dictionary_requirements[0]
        )

        self.assertEqual("reference-only", requirement.coverage_mode)
        self.assertEqual((), requirement.required_values)
        self.assertEqual(
            [
                ("group", ("DICT-001", "DICT-101"), "Признаки алкоголика"),
                ("leaf", ("DICT-001", "DICT-101"), "Запах алкоголя"),
                ("leaf", ("DICT-001", "DICT-101"), "Отечность лица"),
            ],
            [
                (item.value_kind, item.hierarchy_path, item.value)
                for item in requirement.fixture_values
            ],
        )

    def test_generic_reference_only_requirement_does_not_invent_fixture_values(self) -> None:
        (self.design / "dictionary-inventory.md").write_text(
            """| dictionary_id | dictionary_name | active_values |
| --- | --- | --- |
| `DICT-001` | `Корневой справочник` | `DICT-101` |
| `DICT-101` | `Группа один` | `Значение A`; `Значение B` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | input_class | test_data | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Открыть список `DICT-001` без выбора конкретного значения. | `none_required` | `DICT-001` | Список доступен для просмотра. | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | `none_required` | `none_required` | none_required:blocked | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )
        obligation_table = self.design / "coverage-obligation-table.md"
        obligation_table.write_text(
            obligation_table.read_text(encoding="utf-8").replace(
                "`dictionary-values-shown`",
                "`selection-cardinality`",
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
        requirement = (
            load_obligations(obligation_path)
            .obligations[0]
            .dictionary_requirements[0]
        )

        self.assertEqual("reference-only", requirement.coverage_mode)
        self.assertEqual((), requirement.required_values)
        self.assertEqual((), requirement.fixture_values)

    def test_rejects_dictionary_group_locator_lost_between_data_and_action(self) -> None:
        (self.design / "dictionary-inventory.md").write_text(
            """| dictionary_id | dictionary_name | active_values |
| --- | --- | --- |
| `DICT-001` | `Корневой справочник` | `DICT-101` |
| `DICT-101` | `Группа один` | `Значение A`; `Значение B` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| design_item_id | linked_atoms | planned_check | test_data | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-001` | `ATOM-001` | Последовательно выбрать два значения. | два значения `DICT-101` | Оба значения выбраны. | `TC-001` | `covered` |
| `PLAN-002` | `ATOM-002` | Не создавать негативный кейс. | `none_required` | none_required:blocked | `GAP-001` | `gap` |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual(
            "dictionary-group-locator-not-preserved",
            caught.exception.code,
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

    def test_obligation_level_calibration_overrides_plain_atom_status(self) -> None:
        obligations_path = self.design / "coverage-obligation-table.md"
        text = obligations_path.read_text(encoding="utf-8")
        text = text.replace(
            "| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |",
            "| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes | calibration_status |",
            1,
        ).replace(
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            1,
        ).replace(
            "| `TC-001` | `covered` | `-` |",
            "| `TC-001` | `covered` | `-` | `ui-calibration-required` |",
            1,
        ).replace(
            "| `GAP-001` | `gap` | `-` |",
            "| `GAP-001` | `gap` | `-` | `none` |",
            1,
        )
        obligations_path.write_text(text, encoding="utf-8")

        result = self.compile()
        package = load_prepared_package(result.stage_package, self.root)
        obligation_path = self.root / next(
            item.path
            for item in package.package_artifacts
            if item.kind == "atomic-obligations"
        )
        obligations = load_obligations(obligation_path).obligations

        self.assertEqual("ui-calibration-required", obligations[0].calibration_status)
        self.assertEqual("none", obligations[1].calibration_status)

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

    def test_preserves_literal_in_declared_projection_targets(self) -> None:
        literal = "Точный текст интерфейса"
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "Поле использует фиксированный список DICT-001.",
                f"Отображается {literal} и используется DICT-001.",
            ),
            encoding="utf-8",
        )
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace(
                "Отображаются все и только значения DICT-001.",
                f"Отображается {literal} и все значения DICT-001.",
            ),
            encoding="utf-8",
        )
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "Отображаются все и только значения DICT-001.",
                f"Отображается {literal} и все значения DICT-001.",
            ),
            encoding="utf-8",
        )
        self.enable_source_fidelity(
            [
                {
                    "binding_id": "FID-001",
                    "binding_kind": "literal",
                    "source_ref": "GSR 1",
                    "source_text": literal,
                    "atom_id": "ATOM-001",
                    "obligation_id": "OBL-001",
                    "handling": "preserve",
                    "required_targets": [
                        "atomic_statement",
                        "required_behavior",
                        "single_expected_behavior",
                    ],
                }
            ]
        )

        result = self.compile()
        evidence = (result.stage_package.parent / "source-evidence.md").read_text(
            encoding="utf-8"
        )

        self.assertIn('"binding_id":"FID-001"', evidence)

    def test_blocks_lost_literal_in_declared_projection_target(self) -> None:
        self.enable_source_fidelity(
            [
                {
                    "binding_id": "FID-001",
                    "binding_kind": "literal",
                    "source_ref": "GSR 1",
                    "source_text": "Поле использует фиксированный список DICT-001.",
                    "atom_id": "ATOM-001",
                    "obligation_id": "OBL-001",
                    "handling": "preserve",
                    "required_targets": ["atomic_statement", "required_behavior"],
                }
            ]
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual("source-fidelity-literal-missing", caught.exception.code)
        self.assertEqual(
            ["required_behavior"],
            caught.exception.details[0]["missing_targets"],
        )

    def test_accepts_explicit_literal_locator_only_decision(self) -> None:
        self.enable_source_fidelity(
            [
                {
                    "binding_id": "FID-001",
                    "binding_kind": "literal",
                    "source_ref": "GSR 1",
                    "source_text": "Служебный заголовок источника",
                    "atom_id": "ATOM-001",
                    "obligation_id": "OBL-001",
                    "handling": "locator-only",
                    "required_targets": [],
                    "decision_reason": "Текст является locator, а не наблюдаемым oracle.",
                }
            ]
        )

        result = self.compile()

        self.assertEqual(2, result.obligation_count)

    def test_blocks_exact_byte_conversion_without_source_policy(self) -> None:
        source_text = "не более 40 МБ"
        for name in (
            "atomic-requirements-ledger.md",
            "coverage-obligation-table.md",
            "package-test-design-plan.md",
        ):
            path = self.design / name
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Неизвестен текст ошибки.",
                    f"Размер файла {source_text} (41943040 байт).",
                ),
                encoding="utf-8",
            )
        self.enable_source_fidelity(
            [
                {
                    "binding_id": "FID-002",
                    "binding_kind": "unit",
                    "source_ref": "GSR 2",
                    "source_text": source_text,
                    "atom_id": "ATOM-002",
                    "obligation_id": "OBL-002",
                    "handling": "coverage-gap",
                    "required_targets": [
                        "atomic_statement",
                        "required_behavior",
                        "single_expected_behavior",
                    ],
                    "unit_value": 40,
                    "unit_symbol": "МБ",
                    "gap_id": "GAP-001",
                }
            ]
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual(
            "source-fidelity-unit-conversion-without-policy",
            caught.exception.code,
        )

    def test_accepts_source_backed_decimal_byte_policy(self) -> None:
        source_text = "не более 40 МБ"
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "Поле использует фиксированный список DICT-001.",
                f"Размер файла {source_text} (40000000 байт); DICT-001 сохраняется.",
            ),
            encoding="utf-8",
        )
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace(
                "Отображаются все и только значения DICT-001.",
                f"Размер файла {source_text} (40000000 байт); значения DICT-001 отображаются.",
            ),
            encoding="utf-8",
        )
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "Отображаются все и только значения DICT-001.",
                f"Размер файла {source_text} (40000000 байт); значения DICT-001 отображаются.",
            ),
            encoding="utf-8",
        )
        self.enable_source_fidelity(
            [
                {
                    "binding_id": "FID-003",
                    "binding_kind": "unit",
                    "source_ref": "GSR 1",
                    "source_text": source_text,
                    "atom_id": "ATOM-001",
                    "obligation_id": "OBL-001",
                    "handling": "decimal-bytes",
                    "required_targets": [
                        "atomic_statement",
                        "required_behavior",
                        "single_expected_behavior",
                    ],
                    "unit_value": 40,
                    "unit_symbol": "МБ",
                    "policy_source_ref": "GSR 9; source/policy.md: 1 МБ = 1000000 байт",
                    "byte_offset": 0,
                }
            ]
        )

        result = self.compile()

        self.assertEqual(2, result.obligation_count)

    def test_blocks_byte_value_that_conflicts_with_declared_policy(self) -> None:
        source_text = "не более 40 МБ"
        wrong_projection = f"Размер файла {source_text} (41943040 байт)."
        ledger = self.design / "atomic-requirements-ledger.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace(
                "Поле использует фиксированный список DICT-001.",
                wrong_projection + " Используется DICT-001.",
            ),
            encoding="utf-8",
        )
        obligations = self.design / "coverage-obligation-table.md"
        obligations.write_text(
            obligations.read_text(encoding="utf-8").replace(
                "Отображаются все и только значения DICT-001.",
                wrong_projection + " Значения DICT-001 отображаются.",
            ),
            encoding="utf-8",
        )
        plan = self.design / "package-test-design-plan.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "Отображаются все и только значения DICT-001.",
                wrong_projection + " Значения DICT-001 отображаются.",
            ),
            encoding="utf-8",
        )
        self.enable_source_fidelity(
            [
                {
                    "binding_id": "FID-004",
                    "binding_kind": "unit",
                    "source_ref": "GSR 1",
                    "source_text": source_text,
                    "atom_id": "ATOM-001",
                    "obligation_id": "OBL-001",
                    "handling": "decimal-bytes",
                    "required_targets": [
                        "atomic_statement",
                        "required_behavior",
                        "single_expected_behavior",
                    ],
                    "unit_value": 40,
                    "unit_symbol": "МБ",
                    "policy_source_ref": "GSR 9; source/policy.md: 1 МБ = 1000000 байт",
                    "byte_offset": 0,
                }
            ]
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual(
            "source-fidelity-byte-conversion-mismatch",
            caught.exception.code,
        )
        self.assertEqual(40_000_000, caught.exception.details[0]["expected_bytes"])

    def test_source_first_v4_binds_reviewed_assertion_into_prepared_obligation(self) -> None:
        self.enable_source_first_contract()

        result = self.compile()

        self.assertEqual("release", result.output_mode)
        self.assertTrue(result.release_eligible)
        self.assertEqual((), result.release_blocking_finding_codes)

        package = load_prepared_package(result.stage_package, self.root)
        evidence = next(
            item for item in package.package_artifacts if item.kind == "source-evidence"
        )
        evidence_text = (self.root / evidence.path).read_text(encoding="utf-8")
        obligations = load_obligations(
            next(
                self.root / item.path
                for item in package.package_artifacts
                if item.kind == "atomic-obligations"
            )
        )
        obligation = obligations.obligations[0]
        self.assertIn("SOURCE-ASSERTIONS-V4", evidence_text)
        self.assertIn("bounded-source-first-assertions-v4", evidence_text)
        self.assertIn('"assertion_reviews"', evidence_text)
        self.assertIn('"scope_boundary_review"', evidence_text)
        self.assertIn(
            '"source_refs":["SRC-001.P01","GSR 1","DICT-001"]',
            evidence_text,
        )
        self.assertEqual(
            {},
            parse_reviewer_dimension_source_bindings(evidence_text).as_mapping(),
        )
        embedded = parse_embedded_source_assertion_contract(
            evidence_text,
            self.root,
            expected_scope_slug="demo-scope",
            expected_obligation_ids=("OBL-001",),
        )
        self.assertIsNotNone(embedded)
        self.assertIn("Condition contract:", obligation.test_intent)
        self.assertEqual(
            "Отображаются все и только значения DICT-001.",
            obligation.observable_oracle,
        )

    def test_source_first_not_applicable_obligation_routes_property_source_refs_into_evidence(
        self,
    ) -> None:
        assertions_path, review_path = self.enable_source_first_contract()
        manifest = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        )
        assertion = replace(
            manifest.assertions[0],
            polarity="neutral",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            clause_evidence_bindings=(),
            obligation_ids=(),
            disposition_rationale=(
                "Строка задаёт контекст справочника и не формулирует "
                "отдельное поведение продукта."
            ),
        )
        manifest = replace(manifest, assertions=(assertion,))
        manifest.validate(self.root)
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        review_path.write_text(
            json.dumps(
                SourceAssertionReviewReceipt(
                    version=REVIEW_RECEIPT_VERSION,
                    manifest_digest=manifest.digest,
                    decision="accepted",
                    assertion_reviews=(self._verified_review(assertion),),
                    source_inventory_review=self._source_inventory_review(manifest),
                    scope_boundary_review=self._scope_boundary(manifest),
                ).to_dict(),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.design / "atomic-requirements-ledger.md").write_text(
            """# Atomic Requirements Ledger

| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001.P00` | `SRC-001.P00; SRC-001.P01; GSR 1; DICT-001` | `SRC-001.P01` | `GSR 1` | Поле использует фиксированный список DICT-001. | `not-applicable` | `not-applicable` |
""",
            encoding="utf-8",
        )
        (self.design / "package-test-design-plan.md").write_text(
            """# Package Test Design Plan

| linked_atoms | planned_check | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- |
| `ATOM-001` | Не создавать исполнимый кейс. | `none_required:not-applicable` | `not-applicable` | `not-applicable` |
""",
            encoding="utf-8",
        )
        (self.design / "coverage-obligation-table.md").write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P00` | `ATOM-001` | `context` | `not-applicable-context` | Строка не задаёт отдельное поведение продукта. | `SRC-001.P00; SRC-001.P01; GSR 1; DICT-001` | `SRC-001.P01` | `GSR 1` | `not-applicable` | `not-applicable` | Контекст сохранён для полноты трассировки. |
""",
            encoding="utf-8",
        )

        result = self.compile()

        package = load_prepared_package(result.stage_package, self.root)
        obligations = load_obligations(
            next(
                self.root / item.path
                for item in package.package_artifacts
                if item.kind == "atomic-obligations"
            )
        )
        obligation = obligations.obligations[0]
        self.assertEqual("not-applicable", obligation.coverage_status)
        self.assertEqual("", obligation.planned_test_case_id)
        self.assertEqual("", obligation.gap_id)
        self.assertIn("SRC-001.P00", obligation.source_refs)
        self.assertIn("SRC-001.P01", obligation.source_refs)

        evidence_text = next(
            (self.root / item.path).read_text(encoding="utf-8")
            for item in package.package_artifacts
            if item.kind == "source-evidence"
        )
        routing_json = (
            evidence_text.split("## Compiled obligation routing index", 1)[1]
            .split("```json", 1)[1]
            .split("```", 1)[0]
            .strip()
        )
        routing = json.loads(routing_json)
        self.assertEqual(1, len(routing))
        self.assertEqual("OBL-001", routing[0]["obligation_id"])
        self.assertEqual("not-applicable", routing[0]["coverage_status"])
        self.assertEqual(list(obligation.source_refs), routing[0]["source_refs"])

    def test_source_first_v4_resolved_clarification_is_traceable_but_not_active_gap(self) -> None:
        self.enable_source_first_contract()
        self.bind_user_clarification_to_source_first_contract()

        result = self.compile()

        self.assertTrue(result.release_eligible)
        self.assertEqual(0, result.gap_count)
        package = load_prepared_package(result.stage_package, self.root)
        obligations = load_obligations(
            next(
                self.root / item.path
                for item in package.package_artifacts
                if item.kind == "atomic-obligations"
            )
        )
        self.assertEqual((), obligations.coverage_gaps)
        self.assertIn("CLR-DEMO-001", obligations.obligations[0].source_refs)
        evidence_text = next(
            (self.root / item.path).read_text(encoding="utf-8")
            for item in package.package_artifacts
            if item.kind == "source-evidence"
        )
        embedded = parse_embedded_source_assertion_contract(
            evidence_text,
            self.root,
            expected_scope_slug="demo-scope",
            expected_obligation_ids=("OBL-001",),
        )
        self.assertIsNotNone(embedded)
        assert embedded is not None
        self.assertEqual(
            "GAP-DEMO-CLARIFICATION",
            embedded.manifest.clarifications[0].gap_id,
        )

    def test_source_first_v4_arbitrary_resolved_orphan_gap_is_rejected(self) -> None:
        self.enable_source_first_contract()
        gaps_path = self.design / "coverage-gaps.md"
        gaps_path.write_text(
            "# Coverage Gaps\n\n"
            "## GAP-ORPHAN-RESOLVED\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-ORPHAN-RESOLVED |\n"
            "| status | resolved |\n"
            "| resolution | prose-only |\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            SourceAssertionContractError,
            "orphan-coverage-gap",
        ):
            self.refresh_source_assertion_gap_binding()

    def test_source_first_v4_rejects_clarification_registry_mismatch(self) -> None:
        self.enable_source_first_contract()
        self.bind_user_clarification_to_source_first_contract()
        selection_path = self.state.parent / "source-selection.md"
        selection_path.write_text(
            selection_path.read_text(encoding="utf-8").replace(
                "`approved-clarification` |\n\n- xhtml_available:",
                "`not-used` |\n\n- xhtml_available:",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "source-selection manifest registry mismatch",
        ):
            self.compile()

    def test_source_first_v3_rejects_source_selection_registry_drift(self) -> None:
        self.enable_source_first_contract()
        selection = self.state.parent / "source-selection.md"
        original = selection.read_text(encoding="utf-8")
        xhtml = self.ft / "source" / "main.xhtml"
        alternate_xhtml = self.ft / "source" / "main.html"
        alternate_xhtml.write_bytes(xhtml.read_bytes())
        extra_context = self.ft / "EXTRA-CONTEXT.md"
        extra_context.write_text("Unselected context.\n", encoding="utf-8")
        xhtml_sha = self._file_sha256(xhtml)
        wrong_sha = "0" * 64 if xhtml_sha != "0" * 64 else "1" * 64
        variants = {
            "sha-change": original.replace(xhtml_sha, wrong_sha, 1),
            "xhtml-path-change": original.replace(
                "source/main.xhtml",
                "source/main.html",
                1,
            ),
            "used-context-omitted": "\n".join(
                line for line in original.splitlines() if "AGENT-NOTES.md" not in line
            )
            + "\n",
            "mockup-omitted": "\n".join(
                line for line in original.splitlines() if "mockups/search-screen.png" not in line
            )
            + "\n",
            "unexpected-context-added": original.replace(
                "\n\n- xhtml_available",
                "\n| `EXTRA-CONTEXT.md` | `mandatory-package-context` | `"
                + self._file_sha256(extra_context)
                + "` | `supporting-material` |\n\n- xhtml_available",
            ),
        }

        for label, payload in variants.items():
            with self.subTest(label=label):
                selection.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(
                    StageRuntimeError,
                    "source-selection manifest registry mismatch",
                ):
                    self.compile(cycle_name=f"source-registry-{label}")
        selection.write_text(original, encoding="utf-8")

    def test_source_first_v3_requires_sha_bound_selected_registry(self) -> None:
        self.enable_source_first_contract()
        selection = self.state.parent / "source-selection.md"
        selection.write_text(
            selection.read_text(encoding="utf-8").replace(
                "| path | role | sha256 | manifest_binding |",
                "| path | role | checksum | manifest_binding |",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "source registry with manifest_binding, path, role, sha256",
        ):
            self.compile(cycle_name="source-registry-missing-sha-column")

    def test_source_first_v3_rejects_unknown_selected_binding_role(self) -> None:
        self.enable_source_first_contract()
        selection = self.state.parent / "source-selection.md"
        selection.write_text(
            selection.read_text(encoding="utf-8").replace(
                "mandatory-package-context",
                "package-note",
                1,
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "unknown source-selection role requires manifest_binding=not-used: package-note",
        ):
            self.compile(cycle_name="source-registry-unknown-role")

    def test_source_first_v3_allows_explicit_not_used_unknown_role(self) -> None:
        self.enable_source_first_contract()
        unused = self.ft / "source" / "legacy-notes.txt"
        unused.write_text("Not selected for semantic review.\n", encoding="utf-8")
        selection = self.state.parent / "source-selection.md"
        selection.write_text(
            selection.read_text(encoding="utf-8").replace(
                "\n\n- xhtml_available",
                "\n| `source/legacy-notes.txt` | `main-ft-other` | `"
                + self._file_sha256(unused)
                + "` | `not-used` |\n\n- xhtml_available",
            ),
            encoding="utf-8",
        )

        result = self.compile(cycle_name="source-registry-not-used")

        package = load_prepared_package(result.stage_package, self.root)
        self.assertNotIn(
            "legacy-notes.txt",
            {Path(item.path).name for item in package.source_registry},
        )

    def test_source_first_v3_rejects_manifest_evidence_role_drift(self) -> None:
        assertions_path, review_path = self.enable_source_first_contract()
        original_payload = json.loads(assertions_path.read_text(encoding="utf-8"))
        expected_rows = _expected_source_assertion_rows(
            self.design / "source-row-inventory.md"
        )
        role_changes = {
            "semantic-source-of-truth": "supporting-material",
            "structural-visual-parity": "supporting-material",
        }

        for declared_role, replacement_role in role_changes.items():
            with self.subTest(declared_role=declared_role):
                payload = json.loads(json.dumps(original_payload))
                evidence = next(
                    item
                    for item in payload["evidence_sources"]
                    if item["role"] == declared_role
                )
                evidence["role"] = replacement_role
                manifest = SourceAssertionManifest.from_dict(payload)
                manifest.validate(self.root, expected_source_rows=expected_rows)
                assertions_path.write_text(
                    json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                receipt = SourceAssertionReviewReceipt(
                    version=REVIEW_RECEIPT_VERSION,
                    manifest_digest=manifest.digest,
                    decision="accepted",
                    assertion_reviews=tuple(
                        self._verified_review(item) for item in manifest.assertions
                    ),
                    source_inventory_review=self._source_inventory_review(manifest),
                    scope_boundary_review=self._scope_boundary(manifest),
                )
                review_path.write_text(
                    json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    StageRuntimeError,
                    "source-selection manifest registry mismatch",
                ):
                    self.compile(cycle_name=f"evidence-role-{declared_role}")

    def test_source_first_v3_rejects_support_as_assertion_source(self) -> None:
        self.enable_source_first_contract()
        support = self.ft / "support" / "values.md"
        support.parent.mkdir()
        support.write_text("Confirmed support literal.\n", encoding="utf-8")
        support_sha = self._file_sha256(support)
        selection = self.state.parent / "source-selection.md"
        selected_text = selection.read_text(encoding="utf-8").replace(
            "\n\n- xhtml_available",
            "\n| `support/values.md` | `support` | `"
            + support_sha
            + "` | `assertion-source` |\n\n- xhtml_available",
        )
        selection.write_text(selected_text, encoding="utf-8")
        with self.assertRaisesRegex(
            StageRuntimeError,
            "source-selection role/manifest_binding mismatch: support cannot use "
            "assertion-source",
        ):
            self.compile(cycle_name="support-assertion-source")

    def test_source_first_manifest_sources_are_hashed_once_per_compile(self) -> None:
        self.enable_source_first_contract()
        original_sha256_file = source_assertions_module.sha256_file

        with patch.object(
            source_assertions_module,
            "sha256_file",
            side_effect=original_sha256_file,
        ) as mocked_sha256_file:
            self.compile()

        source_path = (self.ft / "source" / "main.xhtml").resolve()
        source_calls = [
            call
            for call in mocked_sha256_file.call_args_list
            if Path(call.args[0]).resolve() == source_path
        ]
        self.assertEqual(1, len(source_calls))

    def test_source_first_inventory_requires_typed_row_registry_columns(self) -> None:
        self.enable_source_first_contract()
        inventory = self.design / "source-row-inventory.md"
        inventory.write_text(
            inventory.read_text(encoding="utf-8").replace(
                "bounded_source_text",
                "legacy_source_text",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "required Markdown table.*bounded_source_text",
        ):
            self.compile()

    def test_source_first_inventory_retains_no_scope_rows_in_expected_registry(self) -> None:
        self.enable_source_first_contract()
        inventory = self.design / "source-row-inventory.md"
        inventory.write_text(
            inventory.read_text(encoding="utf-8").rstrip()
            + "\n| `SRC-001.P02` | `no` | fts/demo/source/main.xhtml | GSR 2 | "
            "GSR 2. Внешняя строка не относится к scope. | document-global-constraints | GSR 2 | "
            "none_required |\n",
            encoding="utf-8",
        )

        expected_rows = _expected_source_assertion_rows(inventory)

        self.assertEqual(("SRC-001.P01", "SRC-001.P02"), tuple(
            item.source_row_id for item in expected_rows
        ))
        self.assertEqual("no", expected_rows[1].scope_disposition)

    def test_source_first_compiler_rejects_swapped_row_ids_against_inventory(self) -> None:
        assertions_path, review_path = self.enable_source_first_contract()
        self.add_source_first_primary_gap(impact="blocking")
        payload = json.loads(assertions_path.read_text(encoding="utf-8"))
        first_row_id = payload["source_rows"][0]["source_row_id"]
        second_row_id = payload["source_rows"][1]["source_row_id"]
        payload["source_rows"][0]["source_row_id"] = second_row_id
        payload["source_rows"][1]["source_row_id"] = first_row_id
        payload["assertions"][0]["source_row_id"] = second_row_id
        payload["assertions"][1]["source_row_id"] = first_row_id
        for binding in payload["assertions"][0]["requirement_code_bindings"]:
            binding["source_row_id"] = second_row_id
        for binding in payload["assertions"][0]["clause_evidence_bindings"]:
            binding["source_row_id"] = second_row_id
        for binding in payload["assertions"][1]["requirement_code_bindings"]:
            binding["source_row_id"] = first_row_id
        for binding in payload["assertions"][1]["clause_evidence_bindings"]:
            binding["source_row_id"] = first_row_id
        swapped_manifest = SourceAssertionManifest.from_dict(payload)
        swapped_manifest.validate(self.root)
        assertions_path.write_text(
            json.dumps(swapped_manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        swapped_receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=swapped_manifest.digest,
            decision="accepted",
            assertion_reviews=tuple(
                self._verified_review(item) for item in swapped_manifest.assertions
            ),
            source_inventory_review=self._source_inventory_review(swapped_manifest),
            scope_boundary_review=self._scope_boundary(swapped_manifest),
        )
        review_path.write_text(
            json.dumps(swapped_receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "source-row-registry-mismatch",
        ):
            self.compile(output_mode="draft-with-blocking-gaps")

    def test_testable_dependency_blocked_assertion_fails_as_readiness_diagnostic(self) -> None:
        self.enable_source_first_contract(execution_readiness="dependency-blocked")

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual(
            "source-execution-dependency-blocked",
            caught.exception.code,
        )
        self.assertIn("ASSERT-001", str(caught.exception))

    def test_dependency_blocked_draft_compiles_only_ready_subset(self) -> None:
        self.enable_source_first_contract(
            execution_readiness="dependency-blocked"
        )
        self.add_ready_assertion_to_dependency_blocked_contract()

        result = self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

        self.assertFalse(result.release_eligible)
        self.assertEqual(1, result.execution_dependency_count)
        self.assertEqual(("OBL-001",), result.excluded_execution_obligation_ids)
        package = load_prepared_package(result.stage_package, self.root)
        self.assertEqual(9, package.package_version)
        assert package.release_status is not None
        self.assertEqual(
            "blocked-execution-dependencies",
            package.release_status.unsigned_status,
        )
        self.assertEqual(
            "ASSERT-001",
            package.release_status.execution_dependency_registry[0].assertion_id,
        )
        obligations = load_obligations(
            next(
                self.root / item.path
                for item in package.package_artifacts
                if item.kind == "atomic-obligations"
            )
        )
        self.assertEqual(
            ["OBL-002"],
            [item.obligation_id for item in obligations.obligations],
        )
        self.assertEqual(
            ["ATOM-002"],
            [item.traceability_atom_id for item in obligations.obligations],
        )
        self.assertEqual((), obligations.coverage_gaps)

    def test_dependency_blocked_draft_rejects_all_blocked_scope(self) -> None:
        self.enable_source_first_contract(
            execution_readiness="dependency-blocked"
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

        self.assertEqual(
            "draft-no-ready-execution-assertions", caught.exception.code
        )

    def test_clean_source_first_scope_rejects_draft_mode(self) -> None:
        self.enable_source_first_contract()

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

        self.assertEqual("draft-without-blockers", caught.exception.code)

    def test_execution_dependency_blocked_obligation_cannot_route_to_tc(self) -> None:
        self.enable_source_first_contract(
            execution_readiness="dependency-blocked"
        )
        self.add_ready_assertion_to_dependency_blocked_contract()
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "| `GSR 1` | `GAP-EXECUTION-001` | `blocked` |",
                "| `GSR 1` | `TC-001` | `blocked` |",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "dependency-blocked source assertion must route every blocked obligation",
        ):
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

    def test_source_first_v3_compiler_rejects_legacy_review_receipt_v2(self) -> None:
        self.enable_source_first_contract()
        review_path = self.design / "source-assertion-review.json"
        payload = json.loads(review_path.read_text(encoding="utf-8"))
        payload["version"] = 2
        payload.pop("scope_boundary_review")
        review_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "legacy-review-receipt-requires-rereview",
        ):
            self.compile()

    def test_source_first_v3_compiler_rejects_legacy_review_receipt_v3(self) -> None:
        self.enable_source_first_contract()
        review_path = self.design / "source-assertion-review.json"
        payload = json.loads(review_path.read_text(encoding="utf-8"))
        payload["version"] = 3
        review_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "legacy-review-receipt-requires-rereview",
        ):
            self.compile()

    def test_source_first_traceability_rejects_source_row_prefix_collision(self) -> None:
        self.enable_source_first_contract()
        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_path.write_text(
            ledger_path.read_text(encoding="utf-8").replace(
                "SRC-001.P01",
                "SRC-001.P010",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "ledger source_row_id mismatch",
        ):
            self.compile()

    def test_source_first_traceability_rejects_requirement_code_prefix_collision(self) -> None:
        self.enable_source_first_contract()
        for artifact_name in (
            "atomic-requirements-ledger.md",
            "coverage-obligation-table.md",
        ):
            path = self.design / artifact_name
            path.write_text(
                path.read_text(encoding="utf-8").replace("GSR 1", "GSR 10"),
                encoding="utf-8",
            )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "ledger requirement_codes mismatch",
        ):
            self.compile()

    def test_source_first_rejects_extra_explicit_requirement_code(self) -> None:
        self.enable_source_first_contract()
        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_path.write_text(
            ledger_path.read_text(encoding="utf-8").replace(
                "| `SRC-001.P01` | `GSR 1` | Поле использует",
                "| `SRC-001.P01` | `GSR 1; GSR 2` | Поле использует",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "ledger requirement_codes mismatch",
        ):
            self.compile()

    def test_source_first_rejects_noncanonical_requirement_code_sentinels(self) -> None:
        self.enable_source_first_contract()
        ledger_path = self.design / "atomic-requirements-ledger.md"
        original = ledger_path.read_text(encoding="utf-8")
        variants = {
            "hyphen": ("-", "rejects placeholder sentinel"),
            "none": ("none", "rejects placeholder sentinel"),
            "not-applicable": ("not-applicable", "rejects placeholder sentinel"),
            "qualified-none-required": (
                "none_required:GSR 1",
                "rejects qualified none_required sentinels",
            ),
        }
        for label, (sentinel, expected_error) in variants.items():
            with self.subTest(label=label):
                ledger_path.write_text(
                    original.replace(
                        "| `SRC-001.P01` | `GSR 1` | Поле использует",
                        f"| `SRC-001.P01` | `{sentinel}` | Поле использует",
                    ),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(StageRuntimeError, expected_error):
                    self.compile(cycle_name=f"requirement-sentinel-{label}")
        ledger_path.write_text(original, encoding="utf-8")

    def test_source_first_rejects_obligation_requirement_code_drift(self) -> None:
        self.enable_source_first_contract()
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "| `SRC-001.P01` | `GSR 1` | `TC-001` |",
                "| `SRC-001.P01` | `GSR 1; GSR 2` | `TC-001` |",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "OBL-001 requirement_codes mismatch",
        ):
            self.compile()

    def test_source_first_rejects_inherited_obligation_source_property(self) -> None:
        self.enable_source_first_contract()
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "| `OBL-001` | `WP-01` | `SRC-001.P01` |",
                "| `OBL-001` | `WP-01` | `SRC-CLONED.P99` |",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError,
            "OBL-001 source_property_id mismatch",
        ):
            self.compile()

    def test_positive_076_rejects_inherited_negative_phone_partitions(self) -> None:
        assertions_path, review_path = self.enable_source_first_contract()
        manifest = SourceAssertionManifest.from_dict(
            json.loads(assertions_path.read_text(encoding="utf-8"))
        )
        assertion = replace(
            manifest.assertions[0],
            assertion_id="ASSERT-AMS-076",
            atom_id="ATOM-AMS-076",
            obligation_ids=("OBL-AMS-096",),
        )
        manifest = replace(manifest, assertions=(assertion,))
        manifest.validate(self.root)
        assertions_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=(self._verified_review(assertion),),
            source_inventory_review=self._source_inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        review_path.write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_path.write_text(
            ledger_path.read_text(encoding="utf-8").replace(
                "ATOM-001", "ATOM-AMS-076"
            ),
            encoding="utf-8",
        )
        plan_path = self.design / "package-test-design-plan.md"
        plan_path.write_text(
            """# Package Test Design Plan

| design_item_id | design_dimension | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PD-AMS-076` | `equivalence-boundary` | `ATOM-AMS-076` | Ввести девять цифр телефона и запустить проверку. | `negative` | `negative-equivalence-partition` | `negative:phone-nine-digits` | Значение не принимается как корректный телефон. | `TC-001` | `covered` |
""",
            encoding="utf-8",
        )
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            """# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | source_row_id | requirement_codes | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-AMS-096` | `WP-01` | `SRC-001.P01` | `ATOM-AMS-076` | `phone-format` | `negative-equivalence-partition` | Значение не принимается как корректный телефон. | `GSR 1; SRC-001.P01` | `SRC-001.P01` | `GSR 1` | `TC-001` | `covered` | Унаследовано при клонировании ATOM-076. |
""",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual(
            "source-assertion-polarity-design-mismatch",
            caught.exception.code,
        )
        self.assertEqual(
            {
                "positive-assertion-negative-obligation",
                "positive-assertion-negative-plan",
            },
            {item["kind"] for item in caught.exception.details},
        )

    def test_source_first_prepared_refs_ignore_free_text_extra_code(self) -> None:
        self.enable_source_first_contract()
        for artifact_name in (
            "atomic-requirements-ledger.md",
            "coverage-obligation-table.md",
        ):
            path = self.design / artifact_name
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "GSR 1; SRC-001.P01; DICT-001",
                    "GSR 1; GSR 999; SRC-001.P01; DICT-001",
                ),
                encoding="utf-8",
            )

        result = self.compile()
        obligations = load_obligations(
            result.stage_package.parent / "atomic-obligations.json"
        ).obligations

        self.assertEqual(
            ("SRC-001.P01", "GSR 1", "DICT-001"),
            obligations[0].source_refs,
        )

    def test_source_first_gap_requires_explicit_blocking_classification(self) -> None:
        self.enable_source_first_contract()
        self.attach_source_first_constraint_gap(None)

        with self.assertRaisesRegex(
            StageRuntimeError,
            "requires explicit blocking/non-blocking classification",
        ):
            self.compile()

    def test_source_first_constraint_gap_must_be_non_blocking(self) -> None:
        self.enable_source_first_contract()
        self.attach_source_first_constraint_gap("blocking")

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

        self.assertEqual("blocking-constraint-gap", caught.exception.code)

    def test_source_first_standard_package_cannot_carry_primary_blocking_gap(self) -> None:
        self.enable_source_first_contract()
        self.convert_source_first_to_primary_gap("blocking")
        (self.design / "test-design-applicability-matrix.md").write_text(
            "| dimension | applicable | source_ref |\n"
            "| --- | --- | --- |\n"
            "| `numeric` | `yes` | `GSR 1` |\n",
            encoding="utf-8",
        )

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual("blocking-source-first-gap", caught.exception.code)

    def test_draft_mode_requires_source_first_contract(self) -> None:
        with self.assertRaisesRegex(
            StageRuntimeError,
            "requires source-first compiler contract v3",
        ):
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

    def test_source_first_ambiguous_assertion_gap_must_reach_atom_obligation_chain(self) -> None:
        self.enable_source_first_contract()
        with self.assertRaisesRegex(
            SourceAssertionContractError,
            "primary-gap-unknown",
        ):
            self.add_source_first_primary_gap(
                impact="blocking",
                assertion_gap_id="GAP-DIFFERENT",
            )

    def test_ambiguous_assertion_cannot_hide_primary_gap_as_constraint(self) -> None:
        self.enable_source_first_contract()
        self.add_source_first_primary_gap(impact="blocking")
        ledger_path = self.design / "atomic-requirements-ledger.md"
        ledger_text = ledger_path.read_text(encoding="utf-8")
        ledger_text = ledger_text.replace(
            "| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc |",
            "| atom_id | source_property_id | source_ref | source_row_id | requirement_codes | atomic_statement | coverage_status | covered_by_tc | constraint_gap_ids |",
        ).replace(
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            1,
        ).replace(
            "| `TC-001` |",
            "| `TC-001` | - |",
        ).replace(
            "| `GAP-PRIMARY` |",
            "| `GAP-PRIMARY` | `GAP-CONSTRAINT` |",
        )
        ledger_path.write_text(ledger_text, encoding="utf-8")

        with self.assertRaisesRegex(
            StageRuntimeError,
            "constraint_gap_ids are allowed only on testable source assertions",
        ):
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

    def test_source_first_missing_primary_gap_is_contract_diagnostic(self) -> None:
        self.enable_source_first_contract()
        self.add_source_first_primary_gap(impact="blocking")
        (self.design / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\nNo registered gaps.\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            SourceAssertionContractError,
            "primary-gap-unknown",
        ):
            self.refresh_source_assertion_gap_binding()

    def test_source_first_draft_compiles_narrow_primary_blocking_gap(self) -> None:
        self.enable_source_first_contract()
        self.add_source_first_primary_gap(impact="blocking")

        result = self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

        self.assertEqual(DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE, result.output_mode)
        self.assertFalse(result.release_eligible)
        self.assertEqual(("GAP-PRIMARY",), result.blocking_gap_ids)
        self.assertIn(
            "blocking-source-first-gap",
            result.release_blocking_finding_codes,
        )
        self.assertNotIn(
            "overall-coverage-floor", result.release_blocking_finding_codes
        )
        self.assertNotIn(
            "assertion-coverage-floor", result.release_blocking_finding_codes
        )

        package = load_prepared_package(result.stage_package, self.root)
        evidence_path = next(
            self.root / item.path
            for item in package.package_artifacts
            if item.kind == "source-evidence"
        )
        evidence_text = evidence_path.read_text(encoding="utf-8")
        release_status = json.loads(
            evidence_text.split("## Compiler release status", 1)[1]
            .split("```json", 1)[1]
            .split("```", 1)[0]
        )
        self.assertEqual(
            DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE,
            release_status["output_mode"],
        )
        self.assertFalse(release_status["release_eligible"])
        self.assertEqual(["GAP-PRIMARY"], release_status["blocking_gap_ids"])
        self.assertEqual(
            1,
            release_status["coverage_accounting"]["counts"]["gap"],
        )
        self.assertEqual(
            "descriptive-only",
            release_status["coverage_accounting"]["determinacy_policy"],
        )
        self.assertTrue(release_status["draft_guard_accounting"]["passed"])

        obligations = load_obligations(
            next(
                self.root / item.path
                for item in package.package_artifacts
                if item.kind == "atomic-obligations"
            )
        )
        self.assertTrue(
            next(
                item for item in obligations.coverage_gaps
                if item.gap_id == "GAP-PRIMARY"
            ).blocking
        )

    def test_compile_cli_exposes_draft_release_status(self) -> None:
        self.enable_source_first_contract()
        self.add_source_first_primary_gap(impact="blocking")
        cycle = self.ft / "work" / "review-cycles" / "cli-draft-cycle"
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = compile_cli_main(
                [
                    "--repo-root",
                    str(self.root),
                    "--workflow-state",
                    self.state.relative_to(self.root).as_posix(),
                    "--output-root",
                    (
                        cycle / "prepared-input" / "demo-package"
                    ).relative_to(self.root).as_posix(),
                    "--package-id",
                    "demo-package",
                    "--attempt-root",
                    (
                        cycle / "attempts" / "writer-r1" / "attempt-001"
                    ).relative_to(self.root).as_posix(),
                    "--expected-ft-slug",
                    "demo",
                    "--output-mode",
                    DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE,
                ]
            )

        self.assertEqual(0, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE, payload["output_mode"])
        self.assertFalse(payload["release_eligible"])
        self.assertEqual(["GAP-PRIMARY"], payload["blocking_gap_ids"])
        self.assertIn(
            "blocking-source-first-gap",
            payload["release_blocking_finding_codes"],
        )

    def test_source_first_draft_requires_at_least_one_testable_obligation(self) -> None:
        self.enable_source_first_contract()
        self.convert_source_first_to_primary_gap("blocking")

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

        self.assertEqual(
            "draft-no-ready-execution-assertions", caught.exception.code
        )

    def test_source_first_release_reports_nonblocking_determinacy_without_ratio_gate(self) -> None:
        self.enable_source_first_contract()
        self.add_source_first_primary_gap(impact="non-blocking")

        result = self.compile()

        self.assertTrue(result.release_eligible)
        package = load_prepared_package(result.stage_package, self.root)
        evidence_path = next(
            self.root / item.path
            for item in package.package_artifacts
            if item.kind == "source-evidence"
        )
        release_status = json.loads(
            evidence_path.read_text(encoding="utf-8")
            .split("## Compiler release status", 1)[1]
            .split("```json", 1)[1]
            .split("```", 1)[0]
        )
        accounting = release_status["coverage_accounting"]
        self.assertEqual(0.5, accounting["ratio"])
        self.assertEqual("descriptive-only", accounting["determinacy_policy"])
        self.assertEqual([], accounting["blocking_finding_codes"])
        completeness = release_status["source_first_testable_completeness"]
        self.assertEqual("pass", completeness["status"])
        self.assertEqual(1.0, completeness["coverage_ratio"])

    def test_source_first_draft_does_not_relax_broad_primary_gap_guard(self) -> None:
        self.enable_source_first_contract()
        self.add_source_first_primary_gap(impact="blocking")
        self.add_second_assertion_to_primary_gap()

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile(output_mode=DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE)

        self.assertEqual("coverage-accounting-failed", caught.exception.code)
        self.assertIn("broad-primary-gap", str(caught.exception))

    def test_source_first_release_enforces_high_risk_nonblocking_guard(self) -> None:
        self.enable_source_first_contract(risk="high")
        self.attach_source_first_constraint_gap("non-blocking")

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual("coverage-accounting-failed", caught.exception.code)
        self.assertIn("high-risk-nonblocking-gap", str(caught.exception))

    def test_source_first_medium_risk_nonblocking_constraint_gap_compiles(self) -> None:
        self.enable_source_first_contract()
        self.attach_source_first_constraint_gap("non-blocking")

        result = self.compile()

        self.assertEqual(1, result.gap_count)
        package = load_prepared_package(result.stage_package, self.root)
        obligations = load_obligations(
            next(
                self.root / item.path
                for item in package.package_artifacts
                if item.kind == "atomic-obligations"
            )
        )
        self.assertEqual(
            ("GAP-CONSTRAINT",),
            obligations.obligations[0].constraint_gap_ids,
        )

    def test_source_first_high_risk_constraint_gap_is_not_silently_waived(self) -> None:
        self.enable_source_first_contract(risk="high")
        self.attach_source_first_constraint_gap("non-blocking")

        with self.assertRaises(PreparedCompilerDiagnostic) as caught:
            self.compile()

        self.assertEqual("coverage-accounting-failed", caught.exception.code)
        self.assertIn(
            "high-risk-nonblocking-gap",
            str(caught.exception),
        )

    def test_source_first_binds_each_routed_dimension_to_its_exact_source_refs(self) -> None:
        self.enable_source_first_contract()
        matrix = self.design / "test-design-applicability-matrix.md"
        matrix.write_text(
            """# Test-design Applicability Matrix

| dimension | applicable | source_ref |
| --- | --- | --- |
| `field-property` | `yes` | `SRC-001.P01` |
| `negative-oracle` | `yes` | `GSR 1` |
""",
            encoding="utf-8",
        )
        obligations_path = self.design / "coverage-obligation-table.md"
        obligations_path.write_text(
            obligations_path.read_text(encoding="utf-8").replace(
                "| `dictionary-source` |", "| `action-navigation` |", 1
            ),
            encoding="utf-8",
        )

        result = self.compile()
        evidence_text = (result.stage_package.parent / "source-evidence.md").read_text(
            encoding="utf-8"
        )
        bindings = parse_reviewer_dimension_source_bindings(
            evidence_text
        ).as_mapping()

        self.assertEqual(
            {"negative-oracle", "state-transition-or-navigation"}, set(bindings)
        )
        self.assertEqual(("GSR 1",), bindings["negative-oracle"])
        self.assertIn("SRC-001.P01", bindings["state-transition-or-navigation"])

    def test_source_first_blocks_unbound_applicability_dimension(self) -> None:
        self.enable_source_first_contract()
        (self.design / "test-design-applicability-matrix.md").write_text(
            """# Test-design Applicability Matrix

| dimension | applicable |
| --- | --- |
| `negative-oracle` | `yes` |
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            StageRuntimeError, "deterministic source_ref bindings"
        ):
            self.compile()

    def test_source_first_v3_rejects_stale_source_and_review_receipt(self) -> None:
        assertions_path, review_path = self.enable_source_first_contract()
        original_assertions = assertions_path.read_text(encoding="utf-8")
        original_source = (self.ft / "source" / "main.xhtml").read_text(
            encoding="utf-8"
        )
        (self.ft / "source" / "main.xhtml").write_text(
            "<html><body>changed</body></html>\n", encoding="utf-8"
        )
        with self.assertRaises(StageRuntimeError) as stale_source:
            self.compile()
        self.assertIn("stale-source-sha256", str(stale_source.exception))

        (self.ft / "source" / "main.xhtml").write_text(
            original_source,
            encoding="utf-8",
        )
        assertions_path.write_text(original_assertions, encoding="utf-8")
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["assertion_reviews"][0]["approved_polarity"] = "negative"
        review_path.write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(StageRuntimeError) as wrong_polarity:
            self.compile()
        self.assertIn("approved-polarity-mismatch", str(wrong_polarity.exception))


if __name__ == "__main__":
    unittest.main()
