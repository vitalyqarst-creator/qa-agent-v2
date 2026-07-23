from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowBaselineValidationError,
    SourceRowCandidateMapping,
    SourceRowExtractionSpec,
    build_source_row_baseline,
    load_source_row_baseline,
    resolve_xhtml_candidate_at_locator,
    resolve_xhtml_structural_contexts_at_locators,
    resolve_xhtml_table_cells_at_locators,
    validate_candidate_coverage,
    validate_source_row_baseline,
    validate_source_row_completeness,
    write_source_row_baseline,
)


XHTML_OPEN = '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
XHTML_CLOSE = "</body></html>"


class SourceRowBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.source_path = self.repo_root / "source" / "main.xhtml"
        self.source_path.parent.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_xhtml(self, body: str) -> None:
        self.source_path.write_text(
            XHTML_OPEN + body + XHTML_CLOSE,
            encoding="utf-8",
        )

    def _source_sha256(self) -> str:
        return hashlib.sha256(self.source_path.read_bytes()).hexdigest()

    def _spec(
        self,
        *,
        regions: list[dict[str, object]] | None = None,
    ) -> SourceRowExtractionSpec:
        return SourceRowExtractionSpec.from_dict(
            {
                "version": 1,
                "scope_slug": "sample-scope",
                "selected_xhtml": {
                    "relative_path": "source/main.xhtml",
                    "sha256": self._source_sha256(),
                },
                "namespaces": {"xhtml": "http://www.w3.org/1999/xhtml"},
                "regions": regions
                or [
                    {
                        "region_id": "REGION-SCOPE",
                        "source_context_class": "scope-local",
                        "selector": {
                            "kind": "container",
                            "container_xpath": "/*/*[1]",
                        },
                    }
                ],
            }
        )

    @staticmethod
    def _mappings(baseline) -> tuple[SourceRowCandidateMapping, ...]:
        return tuple(
            SourceRowCandidateMapping(
                source_row_id=f"SRC-{index:03d}",
                source_path=baseline.selected_xhtml.relative_path,
                source_locator=candidate.canonical_xpath,
                bounded_source_text=candidate.bounded_source_text,
                source_context_class=candidate.source_context_class,
                candidate_id=candidate.candidate_id,
            )
            for index, candidate in enumerate(baseline.candidates, start=1)
        )

    def assert_contract_error(self, code: str, callback) -> None:
        with self.assertRaises(SourceRowBaselineValidationError) as raised:
            callback()
        self.assertEqual(code, raised.exception.code)

    def test_deterministic_candidates_cover_nested_structures_without_double_counting(self) -> None:
        self._write_xhtml(
            "<section>"
            "<p>Повторяемый текст</p>"
            "<p>Повторяемый текст</p>"
            "<ul><li>Родитель<ul><li>Дочерний пункт</li></ul></li></ul>"
            "<table><tr><td><p>Строка таблицы</p>"
            "<ul><li>Пункт внутри строки</li></ul></td></tr></table>"
            "<h2>Заголовок</h2>"
            "</section>"
        )
        spec = self._spec(
            regions=[
                {
                    "region_id": "REGION-SCOPE",
                    "source_context_class": "scope-local",
                    "selector": {
                        "kind": "container",
                        "container_xpath": "/xhtml:html/xhtml:body/xhtml:section[1]",
                    },
                }
            ]
        )

        first = build_source_row_baseline(repo_root=self.repo_root, spec=spec)
        second = build_source_row_baseline(repo_root=self.repo_root, spec=spec)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(6, first.candidate_count)
        self.assertEqual(
            ["p", "p", "li", "li", "tr", "h2"],
            [item.element_kind for item in first.candidates],
        )
        self.assertEqual("Родитель", first.candidates[2].bounded_source_text)
        self.assertEqual("Дочерний пункт", first.candidates[3].bounded_source_text)
        self.assertEqual(
            "Строка таблицы Пункт внутри строки",
            first.candidates[4].bounded_source_text,
        )
        self.assertEqual(
            first.candidates[0].bounded_source_text,
            first.candidates[1].bounded_source_text,
        )
        self.assertNotEqual(
            first.candidates[0].candidate_id,
            first.candidates[1].candidate_id,
        )
        self.assertNotEqual(
            first.candidates[0].canonical_xpath,
            first.candidates[1].canonical_xpath,
        )

    def test_public_locator_resolver_exactly_reuses_candidate_text_ownership(self) -> None:
        self._write_xhtml(
            "<ul><li>Родитель <span>правило</span>"
            "<ul><li>Дочерний пункт</li></ul></li></ul>"
            "<table><tr><td><p>Строка таблицы</p>"
            "<ul><li>Пункт внутри строки</li></ul></td></tr></table>"
        )
        baseline = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(),
        )

        for candidate in baseline.candidates:
            with self.subTest(locator=candidate.canonical_xpath):
                resolved = resolve_xhtml_candidate_at_locator(
                    xhtml_path=self.source_path,
                    canonical_xpath=candidate.canonical_xpath,
                )
                self.assertEqual(candidate.canonical_xpath, resolved.canonical_xpath)
                self.assertEqual(candidate.element_kind, resolved.element_kind)
                self.assertEqual(
                    candidate.bounded_source_text,
                    resolved.bounded_source_text,
                )

        self.assert_contract_error(
            "candidate-owned-by-table-row",
            lambda: resolve_xhtml_candidate_at_locator(
                xhtml_path=self.source_path,
                canonical_xpath="/*/*[1]/*[2]/*[1]/*[1]/*[1]",
            ),
        )

    def test_table_cell_resolver_uses_physical_child_order_not_colspan(self) -> None:
        self._write_xhtml(
            "<table>"
            "<tr><td>Название</td><td colspan='2'>О</td><td colspan='2'>Р</td></tr>"
            "<tr><td colspan='2'>Поле</td><td colspan='2'>Да</td>"
            "<td colspan='2'>Нет</td></tr>"
            "</table>"
        )
        baseline = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(),
        )

        resolved = resolve_xhtml_table_cells_at_locators(
            xhtml_path=self.source_path,
            canonical_xpaths=[item.canonical_xpath for item in baseline.candidates],
        )

        self.assertEqual(2, len(resolved))
        for row_locator, expected_text in zip(
            resolved,
            (["Название", "О", "Р"], ["Поле", "Да", "Нет"]),
            strict=True,
        ):
            cells = resolved[row_locator]
            self.assertEqual([1, 2, 3], [item.physical_column_index for item in cells])
            self.assertEqual(expected_text, [item.bounded_source_text for item in cells])
            self.assertEqual(
                [row_locator + f"/*[{index}]" for index in range(1, 4)],
                [item.canonical_xpath for item in cells],
            )

    def test_structural_context_resolver_materializes_heading_and_exact_ancestry(self) -> None:
        self._write_xhtml(
            "<h1>Основной раздел</h1>"
            "<p>Вводный текст</p>"
            "<h2>Табличные правила</h2>"
            "<table><tbody><tr><td>Строка требования</td></tr></tbody></table>"
            "<h3>Списочные правила</h3>"
            "<ul><li>Пункт требования</li></ul>"
            "<h2>Следующий подраздел</h2>"
            "<p>Завершающий текст</p>"
        )
        baseline = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(),
        )
        by_text = {
            item.bounded_source_text: item for item in baseline.candidates
        }
        selected = (
            by_text["Основной раздел"],
            by_text["Строка требования"],
            by_text["Пункт требования"],
            by_text["Завершающий текст"],
        )

        resolved = resolve_xhtml_structural_contexts_at_locators(
            xhtml_path=self.source_path,
            canonical_xpaths=[item.canonical_xpath for item in selected],
        )

        heading = resolved[selected[0].canonical_xpath]
        self.assertEqual((), heading.section_path)
        table_row = resolved[selected[1].canonical_xpath]
        self.assertEqual(
            ("Основной раздел", "Табличные правила"),
            table_row.section_path,
        )
        self.assertEqual("/*/*[1]/*[4]", table_row.table_identity)
        self.assertEqual(
            [("table", "/*/*[1]/*[4]")],
            [
                (item.element_kind, item.canonical_xpath)
                for item in table_row.table_ancestry
            ],
        )
        self.assertEqual(
            [1, 2],
            [item.level for item in table_row.section_headings],
        )
        list_item = resolved[selected[2].canonical_xpath]
        self.assertEqual(
            ("Основной раздел", "Табличные правила", "Списочные правила"),
            list_item.section_path,
        )
        self.assertEqual(
            [("ul", "/*/*[1]/*[6]")],
            [
                (item.element_kind, item.canonical_xpath)
                for item in list_item.list_ancestry
            ],
        )
        following = resolved[selected[3].canonical_xpath]
        self.assertEqual(
            ("Основной раздел", "Следующий подраздел"),
            following.section_path,
        )
        self.assertIsNone(following.table_identity)

    def test_structural_context_resolver_rejects_empty_preceding_heading(self) -> None:
        self._write_xhtml("<h2></h2><p>Требование</p>")
        baseline = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(),
        )

        self.assert_contract_error(
            "empty-structural-heading",
            lambda: resolve_xhtml_structural_contexts_at_locators(
                xhtml_path=self.source_path,
                canonical_xpaths=[baseline.candidates[0].canonical_xpath],
            ),
        )

    def test_annotation_metadata_is_excluded_from_tr_li_p_and_locator_resolution(self) -> None:
        self._write_xhtml(
            '<p>До <span title="annotation">[ANNOTATION P]</span> После</p>'
            '<ul><li>Пункт <span class="note annotation_style_by_filter extra">'
            "[ANNOTATION LI]</span> сохранен</li></ul>"
            '<table><tr><td>Строка <span title="annotation">'
            "[ANNOTATION TR]</span> сохранена</td></tr></table>"
            '<div title="annotation"><p>Скрытый candidate</p></div>'
        )

        baseline = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(),
        )

        self.assertEqual(["p", "li", "tr"], [item.element_kind for item in baseline.candidates])
        self.assertEqual(
            ["До После", "Пункт сохранен", "Строка сохранена"],
            [item.bounded_source_text for item in baseline.candidates],
        )
        for candidate in baseline.candidates:
            with self.subTest(locator=candidate.canonical_xpath):
                resolved = resolve_xhtml_candidate_at_locator(
                    xhtml_path=self.source_path,
                    canonical_xpath=candidate.canonical_xpath,
                )
                self.assertEqual(candidate.bounded_source_text, resolved.bounded_source_text)

        self.assert_contract_error(
            "candidate-is-annotation-metadata",
            lambda: resolve_xhtml_candidate_at_locator(
                xhtml_path=self.source_path,
                canonical_xpath="/*/*[1]/*[4]/*[1]",
            ),
        )

    def test_ordinary_title_and_class_values_remain_visible(self) -> None:
        self._write_xhtml(
            '<p>Начало <span title="annotation-note">обычный title</span> '
            '<span title="Annotation">case-sensitive title</span> '
            '<span class="annotation_style_by_filter_extra">обычный class</span> '
            '<span class="Annotation_style_by_filter">case-sensitive class</span> конец</p>'
        )

        baseline = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(),
        )

        self.assertEqual(1, baseline.candidate_count)
        self.assertEqual(
            "Начало обычный title case-sensitive title обычный class "
            "case-sensitive class конец",
            baseline.candidates[0].bounded_source_text,
        )

    def test_annotation_change_preserves_ids_of_other_candidates(self) -> None:
        self._write_xhtml(
            "<p>Первый <span>метаданные</span></p><p>Второй стабильный</p>"
        )
        first = build_source_row_baseline(repo_root=self.repo_root, spec=self._spec())

        self._write_xhtml(
            '<p>Первый <span title="annotation">метаданные</span></p>'
            "<p>Второй стабильный</p>"
        )
        second = build_source_row_baseline(repo_root=self.repo_root, spec=self._spec())

        self.assertNotEqual(first.candidates[0].candidate_id, second.candidates[0].candidate_id)
        self.assertEqual(first.candidates[1].candidate_id, second.candidates[1].candidate_id)
        self.assertEqual(
            first.candidates[1].canonical_xpath,
            second.candidates[1].canonical_xpath,
        )
        self.assertNotEqual(first.digest, second.digest)
        self.assert_contract_error(
            "xpath-cardinality-mismatch",
            lambda: resolve_xhtml_candidate_at_locator(
                xhtml_path=self.source_path,
                canonical_xpath="/*/*[1]/*[99]",
            ),
        )

    def test_container_may_select_candidate_element_itself(self) -> None:
        self._write_xhtml("<table><tr><td>История 09.07.2026</td></tr></table>")
        spec = self._spec(
            regions=[
                {
                    "region_id": "REGION-HISTORY",
                    "source_context_class": "cross-referenced-constraints",
                    "selector": {
                        "kind": "container",
                        "container_xpath": "/*/*[1]/*[1]/*[1]",
                    },
                }
            ]
        )

        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=spec)

        self.assertEqual(1, baseline.candidate_count)
        self.assertEqual("tr", baseline.candidates[0].element_kind)
        self.assertEqual("История 09.07.2026", baseline.candidates[0].bounded_source_text)

    def test_contiguous_sibling_range_includes_every_candidate_between_boundaries(self) -> None:
        self._write_xhtml(
            "<p>До</p><p>Начало</p><ul><li>Середина</li></ul>"
            "<table><tr><td>Конец</td></tr></table><p>После</p>"
        )
        spec = self._spec(
            regions=[
                {
                    "region_id": "REGION-RANGE",
                    "source_context_class": "ancestor-and-section-preamble",
                    "selector": {
                        "kind": "contiguous-sibling-range",
                        "start_xpath": "/*/*[1]/*[2]",
                        "end_xpath": "/*/*[1]/*[4]",
                        "include_start": True,
                        "include_end": True,
                    },
                }
            ]
        )

        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=spec)

        self.assertEqual(
            ["Начало", "Середина", "Конец"],
            [item.bounded_source_text for item in baseline.candidates],
        )

    def test_overlapping_regions_fail_closed(self) -> None:
        self._write_xhtml("<section><p>Обязательство</p></section>")
        spec = self._spec(
            regions=[
                {
                    "region_id": "REGION-A",
                    "source_context_class": "scope-local",
                    "selector": {
                        "kind": "container",
                        "container_xpath": "/*/*[1]",
                    },
                },
                {
                    "region_id": "REGION-B",
                    "source_context_class": "scope-local",
                    "selector": {
                        "kind": "container",
                        "container_xpath": "/*/*[1]/*[1]",
                    },
                },
            ]
        )

        self.assert_contract_error(
            "overlapping-extraction-regions",
            lambda: build_source_row_baseline(repo_root=self.repo_root, spec=spec),
        )

    def test_source_row_mapping_requires_exact_locator_text_context_and_one_to_one_coverage(self) -> None:
        self._write_xhtml("<p>Первое</p><p>Второе</p>")
        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=self._spec())
        mappings = list(self._mappings(baseline))

        result = validate_candidate_coverage(
            baseline=baseline,
            source_row_mappings=[
                *mappings,
                SourceRowCandidateMapping(
                    source_row_id="SRC-SUPPORT",
                    source_path="support/note.md",
                    source_locator="section 1",
                    bounded_source_text="Вспомогательная строка",
                    source_context_class="cross-referenced-constraints",
                    candidate_id=None,
                ),
            ],
        )
        self.assertEqual(2, result.candidate_count)
        self.assertEqual(2, result.mapped_xhtml_source_row_count)
        self.assertEqual(1, result.non_xhtml_source_row_count)

        cases = (
            (
                "source-row-candidate-locator-mismatch",
                replace(mappings[0], source_locator="/*/*[99]"),
            ),
            (
                "source-row-candidate-text-mismatch",
                replace(mappings[0], bounded_source_text="Другой текст"),
            ),
            (
                "source-row-candidate-context-mismatch",
                replace(
                    mappings[0],
                    source_context_class="document-global-constraints",
                ),
            ),
        )
        for code, wrong_mapping in cases:
            with self.subTest(code=code):
                self.assert_contract_error(
                    code,
                    lambda wrong_mapping=wrong_mapping: validate_candidate_coverage(
                        baseline=baseline,
                        source_row_mappings=[wrong_mapping, mappings[1]],
                    ),
                )

    def test_missing_unknown_and_duplicate_candidate_mapping_fail_closed(self) -> None:
        self._write_xhtml("<p>Первое</p><p>Второе</p>")
        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=self._spec())
        mappings = list(self._mappings(baseline))

        self.assert_contract_error(
            "unmapped-source-candidates",
            lambda: validate_candidate_coverage(
                baseline=baseline,
                source_row_mappings=mappings[:1],
            ),
        )
        self.assert_contract_error(
            "unknown-candidate-mapping",
            lambda: validate_candidate_coverage(
                baseline=baseline,
                source_row_mappings=[
                    replace(mappings[0], candidate_id="SRC-CAND-" + "0" * 24),
                    mappings[1],
                ],
            ),
        )
        self.assert_contract_error(
            "duplicate-candidate-mapping",
            lambda: validate_candidate_coverage(
                baseline=baseline,
                source_row_mappings=[
                    mappings[0],
                    replace(
                        mappings[0],
                        source_row_id="SRC-DUPLICATE",
                    ),
                    mappings[1],
                ],
            ),
        )
        self.assert_contract_error(
            "duplicate-source-row-mapping",
            lambda: validate_candidate_coverage(
                baseline=baseline,
                source_row_mappings=[mappings[0], mappings[0], mappings[1]],
            ),
        )

    def test_non_xhtml_row_cannot_claim_candidate(self) -> None:
        self._write_xhtml("<p>Требование</p>")
        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=self._spec())
        candidate = baseline.candidates[0]
        mapping = SourceRowCandidateMapping(
            source_row_id="SRC-SUPPORT",
            source_path="support/note.md",
            source_locator="section 1",
            bounded_source_text="Требование",
            source_context_class="scope-local",
            candidate_id=candidate.candidate_id,
        )

        self.assert_contract_error(
            "non-xhtml-candidate-mapping",
            lambda: validate_candidate_coverage(
                baseline=baseline,
                source_row_mappings=[mapping],
            ),
        )

    def test_baseline_round_trip_and_completeness_result_expose_manifest_digests(self) -> None:
        self._write_xhtml("<p>Проверяемое обязательство</p>")
        spec = self._spec()
        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=spec)
        spec_path = self.repo_root / "source-row-extraction-spec.json"
        baseline_path = self.repo_root / "source-row-baseline.json"
        spec_path.write_text(
            json.dumps(spec.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        write_source_row_baseline(baseline_path, baseline)

        loaded = load_source_row_baseline(baseline_path)
        result = validate_source_row_completeness(
            repo_root=self.repo_root,
            extraction_spec_path=spec_path,
            baseline_path=baseline_path,
            source_row_mappings=self._mappings(loaded),
        )

        self.assertEqual(spec.digest, result.source_row_extraction_spec_digest)
        self.assertEqual(baseline.digest, result.source_row_baseline_digest)
        self.assertEqual(baseline.candidate_set_sha256, result.candidate_set_digest)
        self.assertEqual(1, result.candidate_count)

    def test_changed_spec_invalidates_old_baseline(self) -> None:
        self._write_xhtml("<p>Требование</p>")
        spec = self._spec()
        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=spec)
        changed_region = replace(
            spec.regions[0],
            source_context_class="document-global-constraints",
        )
        changed_spec = replace(spec, regions=(changed_region,))

        self.assert_contract_error(
            "stale-extraction-spec",
            lambda: validate_source_row_baseline(
                repo_root=self.repo_root,
                spec=changed_spec,
                baseline=baseline,
            ),
        )

    def test_change_outside_regions_preserves_candidate_identity(self) -> None:
        self._write_xhtml("<section><p>Требование</p></section><p>Вне scope 1</p>")
        regions = [
            {
                "region_id": "REGION-SCOPE",
                "source_context_class": "scope-local",
                "selector": {
                    "kind": "container",
                    "container_xpath": "/*/*[1]/*[1]",
                },
            }
        ]
        first = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(regions=regions),
        )

        self._write_xhtml("<section><p>Требование</p></section><p>Вне scope 2</p>")
        second = build_source_row_baseline(
            repo_root=self.repo_root,
            spec=self._spec(regions=regions),
        )

        self.assertEqual(
            [item.candidate_id for item in first.candidates],
            [item.candidate_id for item in second.candidates],
        )
        self.assertNotEqual(first.selected_xhtml.sha256, second.selected_xhtml.sha256)
        self.assertNotEqual(first.digest, second.digest)

    def test_new_requirement_candidate_invalidates_old_source_baseline_and_mapping(self) -> None:
        additions = {
            "p": "<p>Новое требование</p>",
            "li": "<ul><li>Новое требование</li></ul>",
            "tr": "<table><tr><td>Новое требование</td></tr></table>",
        }
        for kind, addition in additions.items():
            with self.subTest(kind=kind):
                self._write_xhtml("<p>Исходное требование</p>")
                old_spec = self._spec()
                old_baseline = build_source_row_baseline(
                    repo_root=self.repo_root,
                    spec=old_spec,
                )
                old_mappings = self._mappings(old_baseline)

                self._write_xhtml("<p>Исходное требование</p>" + addition)
                self.assert_contract_error(
                    "stale-selected-xhtml",
                    lambda: validate_source_row_baseline(
                        repo_root=self.repo_root,
                        spec=old_spec,
                        baseline=old_baseline,
                    ),
                )

                current_spec = self._spec()
                current_baseline = build_source_row_baseline(
                    repo_root=self.repo_root,
                    spec=current_spec,
                )
                self.assert_contract_error(
                    "unmapped-source-candidates",
                    lambda: validate_candidate_coverage(
                        baseline=current_baseline,
                        source_row_mappings=old_mappings,
                    ),
                )

    def test_unsafe_or_non_well_formed_xhtml_is_rejected(self) -> None:
        self.source_path.write_text(
            '<!DOCTYPE html [<!ENTITY injected "unsafe">]>'
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            "<p>&injected;</p></body></html>",
            encoding="utf-8",
        )
        spec = self._spec()
        self.assert_contract_error(
            "unsafe-xhtml-declaration",
            lambda: build_source_row_baseline(repo_root=self.repo_root, spec=spec),
        )

    def test_external_xhtml_doctype_is_stripped_without_network_resolution(self) -> None:
        self.source_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" '
            '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            "<p>Требование</p></body></html>",
            encoding="utf-8",
        )

        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=self._spec())

        self.assertEqual(1, baseline.candidate_count)
        self.assertEqual("Требование", baseline.candidates[0].bounded_source_text)

    def test_version_requires_json_integer_and_direct_mapping_is_validated(self) -> None:
        self._write_xhtml("<p>Требование</p>")
        payload = self._spec().to_dict()
        payload["version"] = 1.0
        self.assert_contract_error(
            "unsupported-extraction-spec-version",
            lambda: SourceRowExtractionSpec.from_dict(payload),
        )

        baseline = build_source_row_baseline(repo_root=self.repo_root, spec=self._spec())
        invalid_mapping = replace(
            self._mappings(baseline)[0],
            source_path="..\\outside.xhtml",
        )
        self.assert_contract_error(
            "invalid-relative-path",
            lambda: validate_candidate_coverage(
                baseline=baseline,
                source_row_mappings=[invalid_mapping],
            ),
        )

    def test_xpath_contract_rejects_descendant_or_text_predicate_selector(self) -> None:
        self._write_xhtml("<p>Требование</p>")
        for xpath in ("//xhtml:p", "/*/*[text()='Требование']"):
            with self.subTest(xpath=xpath):
                self.assert_contract_error(
                    "invalid-xpath" if xpath.startswith("//") else "unsupported-xpath",
                    lambda xpath=xpath: SourceRowExtractionSpec.from_dict(
                        {
                            "version": 1,
                            "scope_slug": "sample-scope",
                            "selected_xhtml": {
                                "relative_path": "source/main.xhtml",
                                "sha256": self._source_sha256(),
                            },
                            "regions": [
                                {
                                    "region_id": "REGION-SCOPE",
                                    "source_context_class": "scope-local",
                                    "selector": {
                                        "kind": "container",
                                        "container_xpath": xpath,
                                    },
                                }
                            ],
                        }
                    ),
                )


if __name__ == "__main__":
    unittest.main()
