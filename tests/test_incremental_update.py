from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from test_case_agent.incremental_update import (
    IncrementalUpdateError,
    run_incremental_update,
)


class IncrementalUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        self.old = self.repo / "old"
        self.new = self.repo / "new"
        self.old.mkdir()
        self.new.mkdir()
        self.canonical = self.repo / "test-cases" / "1-scope.md"
        self.canonical.parent.mkdir()
        self.case_one = (
            "## TC-001\n\n"
            "**Название:** Проверка первого требования\n"
            "**Трассировка:** ATOM-001; OBL-001; GSR 1\n\n"
            "### Шаги\n\n1. Выполнить действие.\n\n"
            "### Итоговый ожидаемый результат\n\nПервое правило выполняется.\n\n"
        )
        self.case_two = (
            "## TC-002\n\n"
            "**Название:** Проверка второго требования\n"
            "**Трассировка:** ATOM-002; OBL-002; GSR 2\n\n"
            "### Шаги\n\n1. Выполнить второе действие.\n\n"
            "### Итоговый ожидаемый результат\n\nВторое правило выполняется.\n"
        )
        self.canonical.write_text(
            "# Тест-кейсы\n\n" + self.case_one + self.case_two,
            encoding="utf-8",
            newline="\n",
        )
        self.traceability = self.repo / "traceability.md"
        self.traceability.write_text(
            "| ATOM | OBL | TC | Requirement |\n"
            "| --- | --- | --- | --- |\n"
            "| ATOM-001 | OBL-001 | TC-001 | GSR 1 |\n"
            "| ATOM-002 | OBL-002 | TC-002 | GSR 2 |\n",
            encoding="utf-8",
            newline="\n",
        )
        self.assertions = self.repo / "source-assertions.json"
        self.assertions.write_text(
            json.dumps(
                {
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-001",
                            "refs": ["ATOM-001", "OBL-001", "GSR 1"],
                        },
                        {
                            "assertion_id": "ASSERT-002",
                            "refs": ["ATOM-002", "OBL-002", "GSR 2"],
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.default_old_entities = [
            {
                "id": "REQ-ONE",
                "kind": "requirement",
                "statement": "GSR 1 Поле доступно пользователю.",
            },
            {
                "id": "REQ-TWO",
                "kind": "requirement",
                "statement": "GSR 2 Второе поле отображается.",
            },
        ]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_docx(path: Path, text: str) -> None:
        document = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
        )
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", document.encode("utf-8"))

    @staticmethod
    def _xhtml(entities: list[dict[str, object]]) -> str:
        rows: list[str] = []
        for item in entities:
            attributes = [
                f'data-entity-id="{item["id"]}"',
                f'data-entity-kind="{item.get("kind", "requirement")}"',
                f'data-statement="{item["statement"]}"',
            ]
            if item.get("field"):
                attributes.append(f'data-field-id="{item["field"]}"')
            if item.get("values"):
                attributes.append(
                    f'data-dictionary-values="{"|".join(item["values"])}"'
                )
            rows.append(f"<p {' '.join(attributes)}>{item['statement']}</p>")
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            "<h1>Раздел 1</h1>"
            + "".join(rows)
            + "</body></html>"
        )

    def _write_version(
        self,
        root: Path,
        entities: list[dict[str, object]],
        *,
        pdf_codes: str = "GSR 1 GSR 2",
        support: str = "shared support",
        xhtml: bool = True,
        docx_text: str | None = None,
    ) -> dict[str, object]:
        self._write_docx(
            root / "main.docx",
            docx_text
            if docx_text is not None
            else " ".join(str(item["statement"]) for item in entities),
        )
        if xhtml:
            (root / "main.xhtml").write_text(
                self._xhtml(entities), encoding="utf-8", newline="\n"
            )
        (root / "main.pdf").write_bytes(
            ("%PDF-1.4\n" + pdf_codes + "\n%%EOF\n").encode("utf-8")
        )
        (root / "support.md").write_text(support, encoding="utf-8")
        (root / "mockup.png").write_bytes(b"same-mockup")
        return {
            "id": root.name,
            "docx": str((root / "main.docx").relative_to(self.repo)),
            "xhtml": str((root / "main.xhtml").relative_to(self.repo)),
            "pdf": str((root / "main.pdf").relative_to(self.repo)),
            "support": [str((root / "support.md").relative_to(self.repo))],
            "mockups": [str((root / "mockup.png").relative_to(self.repo))],
        }

    def _writer(self, *, replacements=None, new_cases=None) -> Path:
        path = self.repo / f"writer-{len(list(self.repo.glob('writer-*.json'))) + 1}.json"
        path.write_text(
            json.dumps(
                {"cases": replacements or {}, "new_cases": new_cases or []},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def _run(
        self,
        old_entities: list[dict[str, object]],
        new_entities: list[dict[str, object]],
        *,
        old_pdf_codes: str = "GSR 1 GSR 2",
        new_pdf_codes: str = "GSR 1 GSR 2",
        old_support: str = "shared support",
        new_support: str = "shared support",
        writer: Path | None = None,
        new_xhtml: bool = True,
        new_docx_text: str | None = None,
        run_name: str = "run",
    ):
        old_version = self._write_version(
            self.old,
            old_entities,
            pdf_codes=old_pdf_codes,
            support=old_support,
        )
        new_version = self._write_version(
            self.new,
            new_entities,
            pdf_codes=new_pdf_codes,
            support=new_support,
            xhtml=new_xhtml,
            docx_text=new_docx_text,
        )
        config = {
            "schema_version": 1,
            "old_version": old_version,
            "new_version": new_version,
            "baseline": {
                "canonical_test_cases": str(self.canonical.relative_to(self.repo)),
                "traceability_matrix": str(self.traceability.relative_to(self.repo)),
                "source_assertions": str(self.assertions.relative_to(self.repo)),
            },
            "output": {
                "run_dir": run_name,
                "canonical_path": str(self.canonical.relative_to(self.repo)),
            },
            "release_mode": "shadow",
        }
        if writer is not None:
            config["writer_output"] = str(writer.relative_to(self.repo))
        config_path = self.repo / f"{run_name}.json"
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return run_incremental_update(repo_root=self.repo, config_path=config_path)

    @staticmethod
    def _classifications(run_dir: Path) -> list[str]:
        payload = json.loads(
            (run_dir / "change-classification.json").read_text(encoding="utf-8")
        )
        return [item["classification"] for item in payload["changes"]]

    def test_identical_v2_reuses_every_case_without_writer(self) -> None:
        before = self.canonical.read_bytes()
        result = self._run(self.default_old_entities, self.default_old_entities)
        self.assertEqual("shadow-accepted", result.status)
        self.assertEqual(0, result.writer_invocation_count)
        self.assertEqual(before, result.shadow_suite.read_bytes())
        manifest = json.loads(
            (result.run_dir / "unchanged-region-manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["all_byte_identical"])
        self.assertEqual(2, len(manifest["regions"]))

    def test_single_requiredness_change_modifies_only_owning_case(self) -> None:
        old = [
            {"id": "REQ-ONE", "kind": "table-row", "field": "field-one", "statement": "GSR 1 Поле необязательное."},
            self.default_old_entities[1],
        ]
        new = [
            {"id": "REQ-ONE", "kind": "table-row", "field": "field-one", "statement": "GSR 1 Поле обязательное."},
            self.default_old_entities[1],
        ]
        replacement = self.case_one.replace("Первое правило", "Обязательность поля")
        result = self._run(old, new, writer=self._writer(replacements={"TC-001": replacement}))
        self.assertEqual("shadow-accepted", result.status)
        self.assertIn("modified-behavior", self._classifications(result.run_dir))
        unchanged = json.loads(
            (result.run_dir / "unchanged-region-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(["TC-002"], [item["tc_id"] for item in unchanged["regions"]])

    def test_dictionary_value_addition_is_classified_separately(self) -> None:
        old = [
            {"id": "DICT-ONE", "kind": "dictionary", "statement": "GSR 1 Справочник статусов.", "values": ["A", "B"]},
            self.default_old_entities[1],
        ]
        new = [
            {"id": "DICT-ONE", "kind": "dictionary", "statement": "GSR 1 Справочник статусов.", "values": ["A", "B", "C"]},
            self.default_old_entities[1],
        ]
        result = self._run(
            old,
            new,
            writer=self._writer(replacements={"TC-001": self.case_one + "\n<!-- C -->\n"}),
        )
        self.assertIn("dictionary-changed", self._classifications(result.run_dir))

    def test_removed_field_retires_its_case(self) -> None:
        result = self._run(
            self.default_old_entities,
            [self.default_old_entities[1]],
        )
        self.assertIn("removed", self._classifications(result.run_dir))
        self.assertNotIn("## TC-001", result.shadow_suite.read_text(encoding="utf-8"))
        self.assertIn("## TC-002", result.shadow_suite.read_text(encoding="utf-8"))

    def test_added_requirement_creates_new_case_without_rewriting_old_cases(self) -> None:
        new_entities = [
            *self.default_old_entities,
            {"id": "REQ-THREE", "kind": "requirement", "statement": "GSR 3 Третье поле отображается."},
        ]
        new_case = (
            "## TC-003\n\n**Название:** Третье требование\n"
            "**Трассировка:** ATOM-003; OBL-003; GSR 3\n\n"
            "### Шаги\n\n1. Проверить поле.\n\n"
            "### Итоговый ожидаемый результат\n\nТретье поле отображается.\n"
        )
        result = self._run(
            self.default_old_entities,
            new_entities,
            new_pdf_codes="GSR 1 GSR 2 GSR 3",
            writer=self._writer(new_cases=[new_case]),
        )
        self.assertIn("added", self._classifications(result.run_dir))
        self.assertIn("## TC-003", result.shadow_suite.read_text(encoding="utf-8"))

    def test_requirement_move_without_semantic_change_reuses_cases(self) -> None:
        moved = list(reversed(self.default_old_entities))
        result = self._run(self.default_old_entities, moved)
        self.assertIn("moved", self._classifications(result.run_dir))
        unchanged = json.loads(
            (result.run_dir / "unchanged-region-manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(unchanged["all_byte_identical"])

    def test_requirement_code_change_preserves_tc_id_but_updates_traceability(self) -> None:
        changed = [
            {"id": "REQ-ONE", "kind": "requirement", "statement": "GSR 9 Поле доступно пользователю."},
            self.default_old_entities[1],
        ]
        replacement = self.case_one.replace("GSR 1", "GSR 9")
        result = self._run(
            self.default_old_entities,
            changed,
            old_pdf_codes="GSR 1 GSR 2",
            new_pdf_codes="GSR 9 GSR 2",
            writer=self._writer(replacements={"TC-001": replacement}),
        )
        self.assertIn("renumbered", self._classifications(result.run_dir))
        shadow = result.shadow_suite.read_text(encoding="utf-8")
        self.assertIn("## TC-001", shadow)
        self.assertIn("GSR 9", shadow)

    def test_shared_support_change_expands_recheck_to_all_cases(self) -> None:
        writer = self._writer(
            replacements={
                "TC-001": self.case_one + "\n<!-- support rechecked -->\n",
                "TC-002": self.case_two + "\n<!-- support rechecked -->\n",
            }
        )
        result = self._run(
            self.default_old_entities,
            self.default_old_entities,
            new_support="changed shared support",
            writer=writer,
        )
        self.assertIn("support-changed", self._classifications(result.run_dir))
        plan = (result.run_dir / "update-plan.md").read_text(encoding="utf-8")
        self.assertEqual(2, plan.count("`modify`"))

    def test_ambiguous_row_match_blocks_update_review(self) -> None:
        duplicates = [
            {"id": "DUP", "kind": "requirement", "statement": "Одинаковое правило."},
            {"id": "DUP", "kind": "requirement", "statement": "Одинаковое правило."},
        ]
        result = self._run(
            duplicates,
            duplicates,
            old_pdf_codes="",
            new_pdf_codes="",
        )
        self.assertEqual("review-failed", result.status)
        self.assertIn("ambiguous-match", self._classifications(result.run_dir))

    def test_missing_new_xhtml_blocks_before_diff(self) -> None:
        with self.assertRaisesRegex(IncrementalUpdateError, "new XHTML is missing"):
            self._run(
                self.default_old_entities,
                self.default_old_entities,
                new_xhtml=False,
            )

    def test_pdf_only_requirement_code_change_is_not_lost(self) -> None:
        no_codes = [
            {"id": "REQ-ONE", "kind": "requirement", "statement": "Поле доступно пользователю."},
            {"id": "REQ-TWO", "kind": "requirement", "statement": "Второе поле отображается."},
        ]
        replacement = self.case_one.replace("GSR 1", "GSR 9")
        result = self._run(
            no_codes,
            no_codes,
            old_pdf_codes="GSR 1 GSR 2",
            new_pdf_codes="GSR 9 GSR 2",
            writer=self._writer(replacements={"TC-001": replacement}),
        )
        changes = json.loads(
            (result.run_dir / "change-classification.json").read_text(encoding="utf-8")
        )["changes"]
        self.assertTrue(
            any(
                item["classification"] == "renumbered"
                and item["matched_by"] == "pdf-parity-only"
                for item in changes
            )
        )

    def test_single_change_proves_unaffected_case_byte_identity(self) -> None:
        changed = [
            {"id": "REQ-ONE", "kind": "requirement", "statement": "GSR 1 Поле недоступно пользователю."},
            self.default_old_entities[1],
        ]
        before_case_two = self.case_two.encode("utf-8")
        result = self._run(
            self.default_old_entities,
            changed,
            writer=self._writer(
                replacements={"TC-001": self.case_one.replace("доступно", "недоступно")}
            ),
        )
        manifest = json.loads(
            (result.run_dir / "unchanged-region-manifest.json").read_text(encoding="utf-8")
        )
        region = next(item for item in manifest["regions"] if item["tc_id"] == "TC-002")
        self.assertTrue(region["byte_identical"])
        self.assertEqual(region["old_sha256"], region["new_sha256"])
        self.assertIn(before_case_two, result.shadow_suite.read_bytes())

    def test_docx_change_missing_from_xhtml_blocks_reuse(self) -> None:
        result = self._run(
            self.default_old_entities,
            self.default_old_entities,
            new_docx_text="Изменённое поведение, которого нет в XHTML-проекции.",
        )
        self.assertEqual("review-failed", result.status)
        changes = json.loads(
            (result.run_dir / "change-classification.json").read_text(encoding="utf-8")
        )["changes"]
        self.assertTrue(
            any(
                item["matched_by"] == "docx-source-change-not-projected-by-xhtml"
                and item["classification"] == "ambiguous-match"
                for item in changes
            )
        )

    def test_publish_requires_independent_review_and_production_gate(self) -> None:
        old_version = self._write_version(self.old, self.default_old_entities)
        new_version = self._write_version(self.new, self.default_old_entities)
        config = {
            "schema_version": 1,
            "old_version": old_version,
            "new_version": new_version,
            "baseline": {
                "canonical_test_cases": str(self.canonical.relative_to(self.repo)),
                "traceability_matrix": str(self.traceability.relative_to(self.repo)),
                "source_assertions": str(self.assertions.relative_to(self.repo)),
            },
            "output": {
                "run_dir": "publish-without-review",
                "canonical_path": str(self.canonical.relative_to(self.repo)),
            },
            "release_mode": "publish",
        }
        config_path = self.repo / "publish-without-review.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        before = self.canonical.read_bytes()
        result = run_incremental_update(repo_root=self.repo, config_path=config_path)
        self.assertEqual("review-failed", result.status)
        self.assertEqual(before, self.canonical.read_bytes())
        review = json.loads(
            (result.run_dir / "update-review-result.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {
                "UPDATE-INDEPENDENT-REVIEW-MISSING",
                "UPDATE-PRODUCTION-GATES-NOT-CONFIGURED",
            },
            {item["id"] for item in review["findings"]},
        )


if __name__ == "__main__":
    unittest.main()
