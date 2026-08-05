from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class RefreshPracticalStageSummaryTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "refresh_practical_stage_summary.py"
        spec = importlib.util.spec_from_file_location(
            "refresh_practical_stage_summary_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_summarize_validator_findings_ignores_summary_self_checks(self) -> None:
        helper = self.load_helper()

        result = helper.summarize_validator_findings(
            [
                {
                    "severity": "error",
                    "category": "practical-stage-summary",
                    "id": "practical-stage-summary-validator-warning-count-stale",
                },
                {
                    "severity": "warning",
                    "category": "coverage",
                    "id": "oracle-candidate-obligation-without-test-case",
                },
                {
                    "severity": "info",
                    "category": "source-quality",
                    "id": "source-quality-many-untitled-sections",
                },
            ]
        )

        self.assertEqual(result["validator_errors_count"], 0)
        self.assertEqual(result["validator_errors_evidence"], "not-applicable")
        self.assertEqual(result["validator_warnings_count"], 1)
        self.assertEqual(
            result["validator_warnings_evidence"],
            "oracle-candidate-obligation-without-test-case",
        )

    def test_detect_git_persistence_reports_gitignored_summary(self) -> None:
        helper = self.load_helper()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
            (root / ".gitignore").write_text("fts/*\n", encoding="utf-8")
            summary = (
                root
                / "fts"
                / "Partners"
                / "Partners-v1"
                / "work"
                / "practical-stage-summary.md"
            )
            summary.parent.mkdir(parents=True)
            summary.write_text("# Practical Stage Summary\n", encoding="utf-8")

            result = helper.detect_git_persistence(root, summary)

        self.assertEqual(result.value, "ignored-by-git")
        self.assertIn(".gitignore", result.evidence)
        self.assertIn("fts/*", result.evidence)

    def test_format_field_rows_outputs_copyable_summary_rows(self) -> None:
        helper = self.load_helper()
        refresh = helper.SummaryRefresh(
            validator_errors_count=0,
            validator_errors_evidence="not-applicable",
            validator_warnings_count=3,
            validator_warnings_evidence="warning-a; warning-b",
            git_persistence="ignored-by-git",
            git_persistence_evidence=".gitignore:1:fts/* fts/Partners/Partners-v1",
        )

        output = helper.format_field_rows(refresh)

        self.assertIn("| validator_errors_count | `0` |", output)
        self.assertIn("| validator_warnings_count | `3` |", output)
        self.assertIn("| git_persistence | `ignored-by-git` |", output)
        self.assertIn("warning-a; warning-b", output)


if __name__ == "__main__":
    unittest.main()
