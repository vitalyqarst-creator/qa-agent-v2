from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT_DIR / "evals" / "reviewer-process-golden-evals.md"


class ReviewerProcessGoldenEvalsTests(unittest.TestCase):
    def test_process_golden_eval_suite_exists(self) -> None:
        self.assertTrue(EVAL_PATH.exists())

    def test_process_golden_eval_suite_covers_known_failure_classes(self) -> None:
        content = EVAL_PATH.read_text(encoding="utf-8")

        for token in (
            "Eval Case GP-001 - Lost Requirement Code",
            "Eval Case GP-002 - Gap Promoted To Covered Without Artifact",
            "Eval Case GP-003 - Applicability Matrix Linked To Non-Covering TC",
            "Eval Case GP-004 - Unsupported UI Mechanism",
            "Eval Case GP-005 - Dictionary Closed Set Not Covered",
            "Eval Case GP-006 - Positive And Negative Branches Merged",
            "Eval Case GP-007 - False Gap Hiding Source-Backed Behavior",
            "`lost-requirement-code`",
            "`fake-internal-coverage`",
            "`applicability-linked-tc-drift`",
            "`unsupported-ui-mechanism`",
            "`dictionary-closed-set-missing`",
            "`positive-negative-merge`",
            "`false-gap`",
        ):
            self.assertIn(token, content)

    def test_process_golden_eval_suite_defines_strict_metrics_and_outputs(self) -> None:
        content = EVAL_PATH.read_text(encoding="utf-8")

        for token in (
            "`known_defect_recall`",
            "`blocking_miss_count`",
            "`incorrect_signoff`",
            "`finding_actionability`",
            "`false_positive_control`",
            "`counterexample_specificity`",
            "exact role/OBL/materialized-item/probe binding",
            "source-only basis",
            "`review_mode`: `traceability`",
            "`review_mode`: `test-design`",
            "`severity`: `error`",
            "`coverage_dimension`: `api-server-validation`",
            "`traceability_ref`: `ATOM-009`",
            "Run Report Template",
            "`verdict`: `pass | partial | fail`",
            "Concrete false-fail witness",
            "Adversarial falsification subset",
            "`AP-001`",
            "`AP-002`",
            "`AP-003`",
            "`AP-004`",
            "`AP-005`",
            "Eval Case 13",
            "Eval Case 14",
            "`clean_control_findings`",
        ):
            self.assertIn(token, content)

        self.assertGreaterEqual(content.count("**Expected Reviewer Output:**"), 7)


if __name__ == "__main__":
    unittest.main()
