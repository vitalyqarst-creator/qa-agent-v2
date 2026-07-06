from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    build_manual_decision_answer_pack,
    import_manual_decision_answer_pack,
    write_manual_decision_answer_pack,
    write_manual_decision_answer_pack_import_report,
)
from test_case_agent.manual_decision_answer_pack import CSV_COLUMNS
from tests.test_manual_decision_answer_validation import build_template, setup_answer_fixture
from test_case_agent.manual_decision_answer_validation import write_manual_decision_answer_template


class ManualDecisionAnswerPackTests(unittest.TestCase):
    def test_builds_answer_pack_from_stage_9d7_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))

            pack = build_pack(paths)

            self.assertEqual("pass-with-warnings", pack.pack_status)
            self.assertEqual("WPKG-000001", pack.package_id)
            self.assertGreater(len(pack.reviewer_rows), 0)

    def test_exports_csv_with_exactly_expected_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
            rows = read_csv(csv_path)

            self.assertEqual(CSV_COLUMNS, list(rows[0].keys()))

    def test_exports_csv_with_utf8_bom_for_excel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")

            self.assertEqual(b"\xef\xbb\xbf", csv_path.read_bytes()[:3])

    def test_csv_has_one_row_per_template_reviewer_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
            rows = read_csv(csv_path)

            self.assertEqual(len(pack.reviewer_rows), len(rows))

    def test_exported_editable_fields_are_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
            rows = read_csv(csv_path)

            for row in rows:
                for column in CSV_COLUMNS[CSV_COLUMNS.index("selected_option_id") :]:
                    self.assertEqual("", row[column])

    def test_no_selected_option_is_prefilled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
            rows = read_csv(csv_path)

            self.assertTrue(all(row["selected_option_id"] == "" for row in rows))

    def test_allowed_option_ids_preserved_per_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
            rows = read_csv(csv_path)
            by_row = {row.row_id: row.allowed_option_ids for row in pack.reviewer_rows}

            for row in rows:
                self.assertEqual(by_row[row["row_id"]], split_multi(row["allowed_option_ids"]))

    def test_markdown_contains_safety_rules_and_reviewer_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            md_path, _csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
            markdown = md_path.read_text(encoding="utf-8")

            self.assertIn("Safety Rules", markdown)
            self.assertIn("How To Fill Answers", markdown)
            self.assertIn("Существующие TC можно использовать только как evidence покрытия", markdown)

    def test_exported_option_labels_are_russian(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
            rows = read_csv(csv_path)

            self.assertIn("Создать отдельный новый TC", rows[0]["allowed_option_labels"])

    def test_schema_json_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack = build_pack(paths)

            _md_path, _csv_path, schema_path = write_manual_decision_answer_pack(pack, root / "work")
            schema = json.loads(schema_path.read_text(encoding="utf-8"))

            self.assertEqual(CSV_COLUMNS, schema["csv_columns"])
            self.assertIn("allowed_options_by_row", schema)

    def test_import_filled_csv_creates_reviewer_answers_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack, filled_csv = write_filled_pack(root, paths)

            report = import_pack(root, pack, filled_csv)

            self.assertEqual("pass", report.import_status)
            self.assertEqual(len(pack.reviewer_rows), report.imported_answers_count)
            self.assertTrue(Path(report.answers_output_path or "").exists())

    def test_import_rejects_unknown_row_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack, filled_csv = write_filled_pack(root, paths)
            append_csv_row(filled_csv, read_csv(filled_csv)[0] | {"row_id": "MDR-UNKNOWN"})

            report = import_pack(root, pack, filled_csv)

            self.assertEqual("blocked", report.import_status)
            self.assertIn("MDR-UNKNOWN", report.unknown_row_ids)

    def test_import_rejects_duplicate_row_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack, filled_csv = write_filled_pack(root, paths)
            append_csv_row(filled_csv, read_csv(filled_csv)[0])

            report = import_pack(root, pack, filled_csv)

            self.assertEqual("blocked", report.import_status)
            self.assertTrue(report.duplicate_row_ids)

    def test_import_rejects_selected_option_not_allowed_for_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack, filled_csv = write_filled_pack(root, paths)
            mutate_first_csv_row(filled_csv, selected_option_id="OPT-NOT-ALLOWED")

            report = import_pack(root, pack, filled_csv)

            self.assertEqual("blocked", report.import_status)
            self.assertTrue(report.invalid_option_rows)

    def test_import_preserves_source_evidence_and_existing_tc_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack, filled_csv = write_filled_pack(root, paths)

            report = import_pack(root, pack, filled_csv)
            payload = json.loads(Path(report.answers_output_path or "").read_text(encoding="utf-8"))

            self.assertEqual(["REQ-DEMO-001", "BSR 1"], payload["answers"][0]["source_evidence"])
            self.assertEqual(
                ["Existing TC was used only as coverage evidence"],
                payload["answers"][0]["existing_tc_review_notes"],
            )

    def test_import_does_not_authorize_stage_9e(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack, filled_csv = write_filled_pack(root, paths)

            report = import_pack(root, pack, filled_csv)

            self.assertFalse(report.stage_9e_authorized)

    def test_import_keeps_canonical_write_allowed_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            pack, filled_csv = write_filled_pack(root, paths)

            report = import_pack(root, pack, filled_csv)

            self.assertFalse(report.canonical_write_allowed)

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, paths = setup_pack_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")
            pack, filled_csv = write_filled_pack(root, paths)

            report = import_pack(root, pack, filled_csv)
            write_manual_decision_answer_pack_import_report(report, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_pack_fixture(root: Path) -> tuple[Path, dict[str, Path]]:
    root, matrix_path = setup_answer_fixture(root)
    template = build_template(matrix_path)
    template_path, _template_md = write_manual_decision_answer_template(template, root / "work")
    return root, {"matrix_path": matrix_path, "template_path": template_path}


def build_pack(paths: dict[str, Path]):
    return build_manual_decision_answer_pack(
        package_id="WPKG-000001",
        template_path=paths["template_path"],
        matrix_path=paths["matrix_path"],
    )


def write_filled_pack(root: Path, paths: dict[str, Path]):
    pack = build_pack(paths)
    _md_path, csv_path, _schema_path = write_manual_decision_answer_pack(pack, root / "work")
    rows = read_csv(csv_path)
    for row in rows:
        row["selected_option_id"] = split_multi(row["allowed_option_ids"])[0]
        row["reviewer_rationale"] = "Reviewer selected this option for draft-only future handling."
        row["source_evidence"] = "REQ-DEMO-001; BSR 1"
        row["existing_tc_review_notes"] = "Existing TC was used only as coverage evidence"
        row["business_clarification"] = "No extra clarification."
        row["no_new_tc_rationale"] = "No-new-TC rationale if needed."
        row["defer_reason"] = "Defer reason if needed."
        row["split_guidance"] = "Split guidance if needed."
        row["answered_by"] = "unit-test-reviewer"
        row["answered_at_utc"] = "2026-07-06T00:00:00Z"
    filled_csv = root / "work" / "manual-decision-reviewer-answer-pack-WPKG-000001.filled.csv"
    write_csv(filled_csv, rows)
    return pack, filled_csv


def import_pack(root: Path, pack, filled_csv: Path):
    return import_manual_decision_answer_pack(
        package_id="WPKG-000001",
        pack=pack,
        filled_csv_path=filled_csv,
        answers_output_path=root / "work" / "manual-decision-reviewer-answers-WPKG-000001.json",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def append_csv_row(path: Path, row: dict[str, str]) -> None:
    rows = read_csv(path)
    rows.append(row)
    write_csv(path, rows)


def mutate_first_csv_row(path: Path, **updates) -> None:
    rows = read_csv(path)
    rows[0].update(updates)
    write_csv(path, rows)


def split_multi(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


if __name__ == "__main__":
    unittest.main()
