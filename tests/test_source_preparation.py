from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowExtractionSpec,
    build_source_row_baseline,
)
from test_case_agent.source_preparation import (
    FIELD_TABLE_SEMANTICS_PROFILE_VERSION,
    SOURCE_PREPARATION_CACHE_VERSION,
    SOURCE_ROLE_MANIFEST_BINDING_COMPATIBILITY,
    SourcePreparationError,
    prepare_bounded_scope_context,
)
from test_case_agent.review_cycle.prepared_compiler import (
    _SOURCE_SELECTION_ROLE_COMPATIBILITY,
)


XHTML_OPEN = '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
XHTML_CLOSE = "</body></html>"


class SourcePreparationTests(unittest.TestCase):
    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @classmethod
    def _fixture(cls, root: Path) -> dict[str, Path]:
        source = root / "fts" / "Demo" / "source"
        source.mkdir(parents=True, exist_ok=True)
        docx = source / "main.docx"
        xhtml = source / "main.xhtml"
        pdf = source / "main.pdf"
        notes = root / "fts" / "Demo" / "AGENT-NOTES.md"
        mockup = root / "fts" / "Demo" / "mockups" / "screen.png"
        mockup.parent.mkdir(parents=True, exist_ok=True)
        docx.write_bytes(b"docx-v1")
        pdf.write_bytes(b"pdf-v1")
        notes.write_text("package notes v1", encoding="utf-8")
        mockup.write_bytes(b"mockup-v1")
        xhtml.write_text(
            XHTML_OPEN
            + "<section><p>Контекст раздела</p><p>BSR 7. Система открывает форму.</p></section>"
            + XHTML_CLOSE,
            encoding="utf-8",
        )
        template_dir = root / "evals" / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        spec_path = template_dir / "source-row-extraction-spec.json"
        spec_payload = {
            "version": 1,
            "scope_slug": "demo-scope",
            "selected_xhtml": {
                "relative_path": "fts/Demo/source/main.xhtml",
                "sha256": cls._sha256(xhtml),
            },
            "namespaces": {"xhtml": "http://www.w3.org/1999/xhtml"},
            "regions": [
                {
                    "region_id": "REGION-SCOPE",
                    "source_context_class": "scope-local",
                    "selector": {
                        "kind": "container",
                        "container_xpath": "/xhtml:html/xhtml:body/xhtml:section[1]",
                    },
                }
            ],
        }
        spec_path.write_text(
            json.dumps(spec_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        spec = SourceRowExtractionSpec.from_dict(spec_payload)
        baseline = build_source_row_baseline(repo_root=root, spec=spec)
        target_locator = baseline.candidates[1].canonical_xpath
        rows = []
        for index, candidate in enumerate(baseline.candidates, start=1):
            target = index == 2
            rows.append(
                {
                    "source_row_id": f"SRC-{index:03d}",
                    "field_or_action": "Открытие формы" if target else "Контекст",
                    "source_ref": "BSR 7; DIT 8; PDF p.1" if target else "section",
                    "source_path": "fts/Demo/source/main.xhtml",
                    "source_locator": candidate.canonical_xpath,
                    "bounded_source_text": candidate.bounded_source_text,
                    "source_context_class": candidate.source_context_class,
                    "candidate_id": candidate.candidate_id,
                    "requirement_codes_hint": ["BSR 7", "DIT 8"] if target else [],
                    "in_scope_hint": "yes; target" if target else "no; context",
                }
            )
        context = {
            "version": 1,
            "ft_slug": "Demo",
            "scope_slug": "demo-scope",
            "main_ft_docx": "fts/Demo/source/main.docx",
            "main_ft_xhtml": "fts/Demo/source/main.xhtml",
            "main_ft_pdf": "fts/Demo/source/main.pdf",
            "package_notes": "fts/Demo/AGENT-NOTES.md",
            "source_row_extraction_spec": "evals/templates/source-row-extraction-spec.json",
            "source_row_baseline": "old-output/source-row-baseline.json",
            "scope_boundary": {
                "target": "Открытие формы",
                "include": ["BSR 7"],
                "exclude": ["Внутренние поля"],
            },
            "sources": [
                {
                    "path": "fts/Demo/source/main.docx",
                    "role": "main-ft-docx",
                    "manifest_binding": "semantic-source-of-truth",
                },
                {
                    "path": "fts/Demo/source/main.xhtml",
                    "role": "main-ft-xhtml",
                    "manifest_binding": "assertion-source",
                },
                {
                    "path": "fts/Demo/source/main.pdf",
                    "role": "main-ft-pdf",
                    "manifest_binding": "structural-visual-parity",
                },
                {
                    "path": "fts/Demo/AGENT-NOTES.md",
                    "role": "mandatory-package-context",
                    "manifest_binding": "supporting-material",
                },
            ],
            "mockups": [
                {
                    "path": "fts/Demo/mockups/screen.png",
                    "role": "mockup",
                    "manifest_binding": "mockup",
                }
            ],
            "mockup_locators": ["Figure 1: button"],
            "parity": [
                {
                    "requirement_code": "BSR 7",
                    "docx_locator": "table:1/row:1",
                    "xhtml_locator": target_locator,
                    "pdf_locator": "page:1",
                    "status": "matched",
                },
                {
                    "requirement_code": "DIT 8",
                    "docx_locator": "none_required",
                    "xhtml_locator": target_locator,
                    "pdf_locator": "page:1",
                    "status": "pdf-only",
                },
            ],
            "source_rows": rows,
        }
        template = template_dir / "context.json"
        template.write_text(
            json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return {
            "template": template,
            "spec": spec_path,
            "docx": docx,
            "xhtml": xhtml,
            "pdf": pdf,
            "notes": notes,
            "mockup": mockup,
        }

    @classmethod
    def _field_table_fixture(cls, root: Path) -> dict[str, Path]:
        paths = cls._fixture(root)
        paths["notes"].write_text(
            "В таблице столбец О означает обязательность, а Р — редактируемость.",
            encoding="utf-8",
        )
        paths["xhtml"].write_text(
            XHTML_OPEN
            + "<section><p>Контекст раздела</p>"
            + "<p>BSR 7. Система открывает форму.</p>"
            + "<table>"
            + "<tr><td>Название</td><td colspan='2'>О</td>"
            + "<td colspan='2'>Р</td><td>Тип</td></tr>"
            + "<tr><td colspan='2'>Поле</td><td colspan='2'>Да</td>"
            + "<td colspan='2'>Да</td><td>Строка</td></tr>"
            + "<tr><td colspan='2'>Корзина</td><td colspan='2'>Нет</td>"
            + "<td colspan='2'>Нет</td><td>Кнопка</td></tr>"
            + "</table></section>"
            + XHTML_CLOSE,
            encoding="utf-8",
        )
        spec_payload = json.loads(paths["spec"].read_text(encoding="utf-8"))
        spec_payload["selected_xhtml"]["sha256"] = cls._sha256(paths["xhtml"])
        paths["spec"].write_text(
            json.dumps(spec_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        baseline = build_source_row_baseline(
            repo_root=root,
            spec=SourceRowExtractionSpec.from_dict(spec_payload),
        )
        context = json.loads(paths["template"].read_text(encoding="utf-8"))
        rows = []
        for index, candidate in enumerate(baseline.candidates, start=1):
            is_requirement = index == 2
            rows.append(
                {
                    "source_row_id": f"SRC-{index:03d}",
                    "field_or_action": (
                        "Открытие формы" if is_requirement else "Контекст"
                    ),
                    "source_ref": "BSR 7; DIT 8" if is_requirement else "section",
                    "source_path": "fts/Demo/source/main.xhtml",
                    "source_locator": candidate.canonical_xpath,
                    "bounded_source_text": candidate.bounded_source_text,
                    "source_context_class": candidate.source_context_class,
                    "candidate_id": candidate.candidate_id,
                    "requirement_codes_hint": (
                        ["BSR 7", "DIT 8"] if is_requirement else []
                    ),
                    "in_scope_hint": (
                        "yes; target" if is_requirement else "no; context"
                    ),
                }
            )
        target_locator = baseline.candidates[1].canonical_xpath
        for item in context["parity"]:
            item["xhtml_locator"] = target_locator
        context["source_rows"] = rows
        context["source_table_column_semantics"] = [
            {
                "table_id": "DEMO-FIELDS",
                "header_source_row_id": "SRC-003",
                "target_source_row_ids": ["SRC-004"],
                "columns": [
                    {
                        "property": "requiredness",
                        "physical_column_index": 2,
                        "expected_header": "О",
                        "value_mapping": {"Да": "required", "Нет": "optional"},
                        "interpretation_source": "fts/Demo/AGENT-NOTES.md",
                        "interpretation_source_fragment": (
                            "столбец О означает обязательность"
                        ),
                    },
                    {
                        "property": "editability",
                        "physical_column_index": 3,
                        "expected_header": "Р",
                        "value_mapping": {"Да": "editable", "Нет": "read-only"},
                        "interpretation_source": "fts/Demo/AGENT-NOTES.md",
                        "interpretation_source_fragment": "Р — редактируемость",
                    },
                ],
            }
        ]
        paths["template"].write_text(
            json.dumps(context, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return paths

    @staticmethod
    def _prepare(root: Path, paths: dict[str, Path], suffix: str):
        return prepare_bounded_scope_context(
            repo_root=root,
            context_template=paths["template"],
            cache_dir=Path(".cache/source-preparation"),
            output_context=Path(f"out/context-{suffix}.json"),
            output_baseline=Path(f"out/baseline-{suffix}.json"),
        )

    def test_cold_build_and_warm_hit_preserve_pdf_only_code(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            cold = self._prepare(root, paths, "cold")
            with patch(
                "test_case_agent.source_preparation.build_source_row_baseline",
                side_effect=AssertionError("warm hit must not rebuild baseline"),
            ):
                warm = self._prepare(root, paths, "warm")

            self.assertFalse(cold.cache_hit)
            self.assertTrue(warm.cache_hit)
            self.assertEqual(cold.cache_key, warm.cache_key)
            self.assertEqual(cold.component_digests, warm.component_digests)
            prepared = json.loads((root / "out/context-warm.json").read_text(encoding="utf-8"))
            self.assertEqual(
                ["BSR 7", "DIT 8"], prepared["source_rows"][1]["requirement_codes_hint"]
            )
            self.assertEqual(
                {
                    "source_selection_sha256",
                    "xhtml_baseline_sha256",
                    "parity_sha256",
                    "mockup_inventory_sha256",
                    "bounded_context_sha256",
                },
                set(warm.component_digests),
            )

    def test_typed_field_table_metadata_is_exact_and_cache_stable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._field_table_fixture(root)
            cold = self._prepare(root, paths, "field-cold")
            warm = self._prepare(root, paths, "field-warm")
            prepared = json.loads(
                (root / "out/context-field-warm.json").read_text(encoding="utf-8")
            )
            field_row = prepared["source_rows"][3]
            button_row = prepared["source_rows"][4]

            self.assertFalse(cold.cache_hit)
            self.assertTrue(warm.cache_hit)
            self.assertEqual(cold.cache_key, warm.cache_key)
            self.assertEqual(
                "FP-SRC-004-REQUIREDNESS-REQUIRED",
                field_row["field_properties"]["requiredness"]["property_id"],
            )
            self.assertEqual(
                field_row["source_locator"] + "/*[2]",
                field_row["field_properties"]["requiredness"][
                    "source_cell_locator"
                ],
            )
            self.assertEqual(
                "FP-SRC-004-EDITABILITY-EDITABLE",
                field_row["field_properties"]["editability"]["property_id"],
            )
            self.assertEqual(4, len(field_row["physical_table_cells"]))
            self.assertNotIn("field_properties", button_row)
            manifest = json.loads(
                (
                    root
                    / ".cache/source-preparation"
                    / cold.cache_key
                    / "manifest.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(SOURCE_PREPARATION_CACHE_VERSION, manifest["version"])
            self.assertEqual(
                FIELD_TABLE_SEMANTICS_PROFILE_VERSION,
                manifest["profiles"]["field_table_semantics"],
            )

    def test_stale_field_table_contract_fails_closed(self) -> None:
        mutations = (
            (
                "header",
                lambda context: context["source_table_column_semantics"][0][
                    "columns"
                ][0].__setitem__("expected_header", "Р"),
                "header mismatch",
            ),
            (
                "value",
                lambda context: context["source_table_column_semantics"][0][
                    "columns"
                ][0].__setitem__("value_mapping", {"Нет": "optional"}),
                "unmapped requiredness value",
            ),
            (
                "notes",
                lambda context: context["source_table_column_semantics"][0][
                    "columns"
                ][0].__setitem__(
                    "interpretation_source_fragment", "несуществующее определение"
                ),
                "interpretation_source_fragment is stale",
            ),
        )
        for name, mutate, expected_error in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._field_table_fixture(root)
                context = json.loads(paths["template"].read_text(encoding="utf-8"))
                mutate(context)
                paths["template"].write_text(
                    json.dumps(context, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(SourcePreparationError, expected_error):
                    self._prepare(root, paths, f"stale-{name}")

    def test_each_source_class_change_invalidates_snapshot(self) -> None:
        for changed in ("docx", "pdf", "notes", "mockup", "xhtml", "spec"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._fixture(root)
                first = self._prepare(root, paths, "before")
                if changed in {"docx", "pdf", "notes", "mockup"}:
                    paths[changed].write_bytes(paths[changed].read_bytes() + b"-changed")
                elif changed == "xhtml":
                    paths["xhtml"].write_text(
                        paths["xhtml"].read_text(encoding="utf-8").replace(
                            "<section>", "<!-- changed --><section>"
                        ),
                        encoding="utf-8",
                    )
                    spec = json.loads(paths["spec"].read_text(encoding="utf-8"))
                    spec["selected_xhtml"]["sha256"] = self._sha256(paths["xhtml"])
                    paths["spec"].write_text(
                        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    refreshed = build_source_row_baseline(
                        repo_root=root,
                        spec=SourceRowExtractionSpec.from_dict(spec),
                    )
                    candidate_by_locator = {
                        item.canonical_xpath: item for item in refreshed.candidates
                    }
                    context = json.loads(paths["template"].read_text(encoding="utf-8"))
                    for row in context["source_rows"]:
                        row["candidate_id"] = candidate_by_locator[
                            row["source_locator"]
                        ].candidate_id
                    paths["template"].write_text(
                        json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                else:
                    spec = json.loads(paths["spec"].read_text(encoding="utf-8"))
                    spec["namespaces"]["extra"] = "urn:extra"
                    paths["spec"].write_text(
                        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                second = self._prepare(root, paths, "after")

                self.assertFalse(second.cache_hit)
                self.assertNotEqual(first.cache_key, second.cache_key)

    def test_json_key_order_does_not_change_cache_key(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            first = self._prepare(root, paths, "first")
            payload = json.loads(paths["template"].read_text(encoding="utf-8"))
            paths["template"].write_text(
                json.dumps(dict(reversed(list(payload.items()))), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            second = self._prepare(root, paths, "second")

            self.assertTrue(second.cache_hit)
            self.assertEqual(first.cache_key, second.cache_key)

    def test_corrupt_cache_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            first = self._prepare(root, paths, "first")
            manifest = root / ".cache" / "source-preparation" / first.cache_key / "manifest.json"
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["unexpected"] = True
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(SourcePreparationError, "fields mismatch"):
                self._prepare(root, paths, "second")

    def test_stale_candidate_binding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            context = json.loads(paths["template"].read_text(encoding="utf-8"))
            context["source_rows"][1]["candidate_id"] = "SRC-CAND-000000000000000000000000"
            paths["template"].write_text(
                json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            with self.assertRaisesRegex(SourcePreparationError, "stale candidate_id"):
                self._prepare(root, paths, "stale")

    def test_orphan_parity_locator_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            context = json.loads(paths["template"].read_text(encoding="utf-8"))
            context["parity"][1]["xhtml_locator"] = "/*/*[999]"
            context["source_rows"][1]["requirement_codes_hint"] = ["BSR 7"]
            context["source_rows"][1]["source_ref"] = "BSR 7"
            paths["template"].write_text(
                json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            with self.assertRaisesRegex(SourcePreparationError, "outside the current baseline"):
                self._prepare(root, paths, "orphan")

    def test_outputs_cannot_alias_inputs_or_each_other(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            with self.assertRaisesRegex(SourcePreparationError, "protected source"):
                prepare_bounded_scope_context(
                    repo_root=root,
                    context_template=paths["template"],
                    cache_dir=Path(".cache/source-preparation"),
                    output_context=Path("fts/Demo/source/main.xhtml"),
                    output_baseline=Path("out/baseline.json"),
                    allow_overwrite=True,
                )
            with self.assertRaisesRegex(SourcePreparationError, "must be different"):
                prepare_bounded_scope_context(
                    repo_root=root,
                    context_template=paths["template"],
                    cache_dir=Path(".cache/source-preparation"),
                    output_context=Path("out/same.json"),
                    output_baseline=Path("out/same.json"),
                    allow_overwrite=True,
                )

    def test_output_preflight_does_not_publish_context_with_stale_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            stale_baseline = root / "out" / "baseline.json"
            stale_baseline.parent.mkdir(parents=True)
            stale_baseline.write_text('{"stale":true}\n', encoding="utf-8")

            with self.assertRaisesRegex(SourcePreparationError, "output exists"):
                prepare_bounded_scope_context(
                    repo_root=root,
                    context_template=paths["template"],
                    cache_dir=Path(".cache/source-preparation"),
                    output_context=Path("out/context.json"),
                    output_baseline=Path("out/baseline.json"),
                )
            self.assertFalse((root / "out" / "context.json").exists())

    def test_unregistered_inline_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            context = json.loads(paths["template"].read_text(encoding="utf-8"))
            context["bounded_evidence_inline"] = {"docx": {"forged": True}}
            paths["template"].write_text(
                json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            with self.assertRaisesRegex(SourcePreparationError, "must match registered"):
                self._prepare(root, paths, "inline")

    def test_role_manifest_binding_matrix_matches_prepared_compiler(self) -> None:
        self.assertEqual(
            _SOURCE_SELECTION_ROLE_COMPATIBILITY,
            {
                role: set(bindings)
                for role, bindings in (
                    SOURCE_ROLE_MANIFEST_BINDING_COMPATIBILITY.items()
                )
            },
        )

    def test_invalid_source_or_mockup_manifest_binding_is_rejected(self) -> None:
        cases = (
            ("sources", 0, None, "manifest_binding is required"),
            ("sources", 0, "assertion-source", "role/manifest_binding mismatch"),
            ("mockups", 0, "supporting-material", "role/manifest_binding mismatch"),
        )
        for registry, index, binding, expected_error in cases:
            with self.subTest(registry=registry, binding=binding), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._fixture(root)
                context = json.loads(paths["template"].read_text(encoding="utf-8"))
                if binding is None:
                    context[registry][index].pop("manifest_binding")
                else:
                    context[registry][index]["manifest_binding"] = binding
                paths["template"].write_text(
                    json.dumps(context, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(SourcePreparationError, expected_error):
                    self._prepare(root, paths, f"invalid-{registry}-{index}")

    def test_compiler_compatible_not_used_bindings_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            context = json.loads(paths["template"].read_text(encoding="utf-8"))
            context["sources"][2]["manifest_binding"] = "not-used"
            context["mockups"][0]["manifest_binding"] = "not-used"
            paths["template"].write_text(
                json.dumps(context, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            result = self._prepare(root, paths, "not-used")

            self.assertFalse(result.cache_hit)

    def test_source_registry_and_historical_template_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._fixture(root)
            context = json.loads(paths["template"].read_text(encoding="utf-8"))
            context["sources"][1]["role"] = "support"
            context["sources"][1]["manifest_binding"] = "supporting-material"
            paths["template"].write_text(
                json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            with self.assertRaisesRegex(SourcePreparationError, "main_ft_xhtml"):
                self._prepare(root, paths, "role")

            paths = self._fixture(root)
            forbidden = root / "fts" / "Demo" / "work" / "stage-handoffs" / "1" / "context.json"
            forbidden.parent.mkdir(parents=True)
            forbidden.write_bytes(paths["template"].read_bytes())
            paths["template"] = forbidden
            with self.assertRaisesRegex(SourcePreparationError, "prior TC/handoff"):
                self._prepare(root, paths, "historical")


if __name__ == "__main__":
    unittest.main()
