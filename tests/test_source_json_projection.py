from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from docx import Document

from scripts.compare_docx_json_to_xhtml_baseline import _match_candidate
from test_case_agent.source_json_projection import build_docx_source_json


class SourceJsonProjectionTests(unittest.TestCase):
    @staticmethod
    def _sha256(path: Path) -> str:
        import hashlib

        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_scope_spec(
        self,
        *,
        repo_root: Path,
        xhtml: Path,
        scope_slug: str,
        section_index: int,
    ) -> Path:
        spec = {
            "version": 1,
            "scope_slug": scope_slug,
            "selected_xhtml": {
                "relative_path": "source/main.xhtml",
                "sha256": self._sha256(xhtml),
            },
            "namespaces": {"xhtml": "http://www.w3.org/1999/xhtml"},
            "regions": [
                {
                    "region_id": f"REGION-{section_index}",
                    "source_context_class": "scope-local",
                    "selector": {
                        "kind": "container",
                        "container_xpath": (
                            "/xhtml:html/xhtml:body/"
                            f"xhtml:section[{section_index}]"
                        ),
                    },
                }
            ],
        }
        path = repo_root / "specs" / scope_slug / "source-row-extraction-spec.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        return path

    def test_docx_projection_preserves_order_sections_and_table_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docx = root / "source" / "main.docx"
            docx.parent.mkdir(parents=True)
            document = Document()
            document.add_heading("4.3 Карточка заявки", level=1)
            document.add_paragraph("Перед таблицей.")
            table = document.add_table(rows=2, cols=2)
            table.cell(0, 0).text = "Поле"
            table.cell(0, 1).text = "Ограничение"
            table.cell(1, 0).text = "Фамилия"
            table.cell(1, 1).text = "Текстовые символы и дефис"
            document.save(docx)

            first = build_docx_source_json(docx, repo_root=root)
            second = build_docx_source_json(docx, repo_root=root)

        self.assertEqual(first["projection_sha256"], second["projection_sha256"])
        self.assertEqual("source/main.docx", first["source_path"])
        self.assertEqual(4, first["block_count"])
        self.assertEqual(
            ["heading-1", "paragraph", "table-row", "table-row"],
            [item["kind"] for item in first["blocks"]],
        )
        self.assertEqual(
            ["Фамилия", "Текстовые символы и дефис"],
            first["blocks"][3]["cells"],
        )
        self.assertEqual(
            ["4.3 Карточка заявки"],
            first["blocks"][3]["section_path"],
        )

    def test_xhtml_flat_row_matches_docx_json_table_delimited_row(self) -> None:
        match = _match_candidate(
            "Текст (string) Допустимое количество символов: 2000",
            [
                {
                    "block_id": "DOCX-BLOCK-000001",
                    "block_index": 1,
                    "kind": "table-row",
                    "locator": "/blocks/1",
                    "section_path": ["5. Ограничения"],
                    "text": "Текст (string) | Допустимое количество символов: 2000",
                }
            ],
        )

        self.assertEqual("normalized-exact", match["match_type"])
        self.assertEqual("DOCX-BLOCK-000001", match["matches"][0]["block_id"])

    def test_xhtml_spacing_noise_matches_docx_json_text(self) -> None:
        match = _match_candidate(
            "Длинный текст ( text ) Максимальный размер значения: ~2GB",
            [
                {
                    "block_id": "DOCX-BLOCK-000001",
                    "block_index": 1,
                    "kind": "table-row",
                    "locator": "/blocks/1",
                    "section_path": ["5. Ограничения"],
                    "text": "Длинный текст (text) | Максимальный размер значения: ~2GB",
                }
            ],
        )

        self.assertEqual("normalized-exact", match["match_type"])

    def test_xhtml_punctuation_spacing_noise_matches_docx_json_text(self) -> None:
        match = _match_candidate(
            "Y / N ; Да / Нет ; True / False",
            [
                {
                    "block_id": "DOCX-BLOCK-000001",
                    "block_index": 1,
                    "kind": "table-row",
                    "locator": "/blocks/1",
                    "section_path": ["5. Ограничения"],
                    "text": "Y / N; Да / Нет ; True / False",
                }
            ],
        )

        self.assertEqual("normalized-exact", match["match_type"])

    def test_docx_projection_carries_empty_numbered_cell_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docx = root / "source" / "main.docx"
            docx.parent.mkdir(parents=True)
            document = Document()
            table = document.add_table(rows=1, cols=1)
            cell = table.cell(0, 0)
            cell.text = ""
            numbered = cell.paragraphs[0]
            numbered.style = "List Number"
            cell.add_paragraph("Текст требования после пустого номера.")
            document.save(docx)

            projection = build_docx_source_json(docx, repo_root=root)

        self.assertEqual(1, projection["block_count"])
        self.assertEqual(
            "1. Текст требования после пустого номера.",
            projection["blocks"][0]["cells"][0],
        )

    def test_docx_projection_does_not_duplicate_carried_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docx = root / "source" / "main.docx"
            docx.parent.mkdir(parents=True)
            document = Document()
            table = document.add_table(rows=1, cols=1)
            cell = table.cell(0, 0)
            cell.text = ""
            numbered = cell.paragraphs[0]
            numbered.style = "List Number"
            cell.add_paragraph("1. Already materialized.")
            document.save(docx)

            projection = build_docx_source_json(docx, repo_root=root)

        self.assertEqual("1. Already materialized.", projection["blocks"][0]["cells"][0])

    def test_multi_scope_evaluator_accepts_clean_three_scope_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir(parents=True)
            docx = source / "main.docx"
            xhtml = source / "main.xhtml"
            document = Document()
            sections = [
                ("scope-a", "BSR 1", "Поле A отображается"),
                ("scope-b", "BSR 2", "Поле B редактируется"),
                ("scope-c", "BSR 3", "Кнопка C добавляет строку"),
            ]
            xhtml_body = []
            for index, (scope_slug, code, text) in enumerate(sections, start=1):
                heading = f"4.{index} {scope_slug}"
                document.add_heading(heading, level=2)
                table = document.add_table(rows=1, cols=2)
                table.cell(0, 0).text = code
                table.cell(0, 1).text = text
                xhtml_body.append(
                    "<section>"
                    f"<h2>{heading}</h2>"
                    f"<table><tr><td>{code}</td><td>{text}</td></tr></table>"
                    "</section>"
                )
            document.save(docx)
            xhtml.write_text(
                '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
                + "".join(xhtml_body)
                + "</body></html>",
                encoding="utf-8",
            )
            # Refresh specs after XHTML exists so their hash is correct.
            for index, (scope_slug, _code, _text) in enumerate(sections, start=1):
                self._write_scope_spec(
                    repo_root=root,
                    xhtml=xhtml,
                    scope_slug=scope_slug,
                    section_index=index,
                )

            output_json = root / "work" / "json-eval" / "summary.json"
            output_md = root / "work" / "json-eval" / "summary.md"
            script = Path(__file__).resolve().parents[1] / "scripts" / (
                "evaluate_docx_json_projection.py"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo-root",
                    str(root),
                    "--docx",
                    str(docx),
                    "--selected-xhtml",
                    str(xhtml),
                    "--spec-root",
                    str(root / "specs"),
                    "--output-json",
                    str(output_json),
                    "--output-md",
                    str(output_md),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            report = json.loads(output_json.read_text(encoding="utf-8"))
            markdown_report = output_md.read_text(encoding="utf-8")

        self.assertIn("candidate-for-controlled-production-switch", completed.stdout)
        self.assertEqual(
            "candidate-for-controlled-production-switch",
            report["summary"]["verdict"],
        )
        self.assertTrue(report["summary"]["production_switch_criteria_met"])
        self.assertEqual(3, report["summary"]["evaluated_scope_count"])
        self.assertEqual(0, report["summary"]["missing_candidate_count"])
        self.assertEqual(0, report["summary"]["order_violations"])
        self.assertIn("DOCX JSON Projection Evaluation", markdown_report)

    def test_multi_scope_evaluator_blocks_missing_json_projection_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir(parents=True)
            docx = source / "main.docx"
            xhtml = source / "main.xhtml"
            document = Document()
            document.add_heading("4.1 scope-a", level=2)
            table = document.add_table(rows=1, cols=2)
            table.cell(0, 0).text = "BSR 1"
            table.cell(0, 1).text = "Поле A отображается"
            document.save(docx)
            xhtml.write_text(
                '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
                "<section><h2>4.1 scope-a</h2>"
                "<table><tr><td>BSR 999</td><td>Другое поле</td></tr></table>"
                "</section></body></html>",
                encoding="utf-8",
            )
            self._write_scope_spec(
                repo_root=root,
                xhtml=xhtml,
                scope_slug="scope-a",
                section_index=1,
            )

            output_json = root / "work" / "json-eval" / "summary.json"
            script = Path(__file__).resolve().parents[1] / "scripts" / (
                "evaluate_docx_json_projection.py"
            )
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo-root",
                    str(root),
                    "--docx",
                    str(docx),
                    "--selected-xhtml",
                    str(xhtml),
                    "--spec-root",
                    str(root / "specs"),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            report = json.loads(output_json.read_text(encoding="utf-8"))

        self.assertEqual(
            "not-ready-for-production-replacement",
            report["summary"]["verdict"],
        )
        self.assertIn("less-than-three-real-scopes", report["summary"]["blockers"])
        self.assertIn("missing-xhtml-candidates", report["summary"]["blockers"])


if __name__ == "__main__":
    unittest.main()
