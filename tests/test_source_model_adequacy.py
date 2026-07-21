from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_source_model_adequacy import main as validate_source_model_main
from test_case_agent.review_cycle.source_model_adequacy import (
    evaluate_exact_length_adequacy,
)


def _assertion(
    assertion_id: str,
    value: str,
    *,
    disposition: str = "testable",
    gap_id: str | None = None,
    statement: str = "",
) -> dict[str, object]:
    return {
        "assertion_id": assertion_id,
        "source_row_id": "SRC-001",
        "semantic_disposition": disposition,
        "primary_gap_id": gap_id,
        "canonical_statement": statement,
        "action_clauses": [f"Ввести значение «{value}»."] if value else [],
        "oracle_clauses": [],
        "requirement_codes": ["BSR 1"],
    }


class ExactLengthSourceModelAdequacyTests(unittest.TestCase):
    def manifest(self, assertions: list[dict[str, object]]) -> dict[str, object]:
        return {
            "source_rows": [
                {
                    "source_row_id": "SRC-001",
                    "bounded_source_text": (
                        "BSR 1. Ограничение: только 6 числовых символов."
                    ),
                }
            ],
            "assertions": assertions,
        }

    def test_distinct_n_minus_n_and_n_plus_one_pass(self) -> None:
        report = evaluate_exact_length_adequacy(
            self.manifest(
                [
                    _assertion("ASSERT-001", "123456"),
                    _assertion("ASSERT-002", "12345"),
                    _assertion("ASSERT-003", "1234567"),
                ]
            )
        )

        self.assertTrue(report["passed"], report)
        self.assertEqual(1, report["rule_count"])

    def test_cli_writes_fresh_report_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "manifest.json").write_text(
                json.dumps({"source_rows": [], "assertions": []}),
                encoding="utf-8",
            )
            (root / "coverage.md").write_text(
                "| obligation_id | linked_atom_id | required_behavior | property_type | obligation_class | source_ref | dictionary_refs | dictionary_coverage |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| OBL-001 | ATOM-001 | Показать поле | visibility | positive | BSR 1 | - | none |\n",
                encoding="utf-8",
            )
            (root / "plan.md").write_text(
                "| linked_atoms | status | test_data | input_class |\n"
                "| --- | --- | --- | --- |\n"
                "| ATOM-001 | planned | - | none |\n",
                encoding="utf-8",
            )
            argv = [
                "--repo-root",
                str(root),
                "--manifest",
                "manifest.json",
                "--coverage-obligation-table",
                "coverage.md",
                "--package-test-design-plan",
                "plan.md",
                "--output",
                "adequacy.json",
            ]

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, validate_source_model_main(argv))
            report = json.loads((root / "adequacy.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                self.assertEqual(2, validate_source_model_main(argv))

    def test_alphanumeric_value_does_not_replace_length_boundary(self) -> None:
        report = evaluate_exact_length_adequacy(
            self.manifest(
                [
                    _assertion("ASSERT-001", "123456"),
                    _assertion("ASSERT-002", "12345A"),
                ]
            )
        )

        self.assertFalse(report["passed"])
        self.assertEqual(["N-1", "N+1"], report["rules"][0]["missing_classes"])

    def test_narrow_class_specific_gaps_are_accepted(self) -> None:
        report = evaluate_exact_length_adequacy(
            self.manifest(
                [
                    _assertion("ASSERT-001", "123456"),
                    _assertion(
                        "ASSERT-002",
                        "",
                        disposition="ambiguous",
                        gap_id="GAP-001",
                        statement="UI-реакция для N-1 короче нормы неизвестна.",
                    ),
                    _assertion(
                        "ASSERT-003",
                        "",
                        disposition="ambiguous",
                        gap_id="GAP-002",
                        statement="UI-реакция для N+1 длиннее нормы неизвестна.",
                    ),
                ]
            )
        )

        self.assertTrue(report["passed"], report)


if __name__ == "__main__":
    unittest.main()
