from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class ExportPracticalBaselineTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "export_practical_baseline.py"
        spec = importlib.util.spec_from_file_location(
            "export_practical_baseline_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_exports_only_accepted_scope_baseline_and_receipts(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ft_root = root / "fts" / "Sample" / "Sample-v1"
            handoff = ft_root / "work" / "stage-handoffs" / "01-sample"
            practical = ft_root / "work" / "practical" / "sample"
            test_cases = ft_root / "test-cases" / "9.2-sample.md"
            handoff.mkdir(parents=True)
            practical.mkdir(parents=True)
            test_cases.parent.mkdir(parents=True)
            test_cases.write_text("# TC\n", encoding="utf-8")
            findings = practical / "review-findings.final.md"
            findings.write_text("**Вердикт:** `accepted`\n", encoding="utf-8")
            independence = practical / "review-independence.final.md"
            independence.write_text("# Независимость\n", encoding="utf-8")
            summary = ft_root / "work" / "practical-stage-summary.md"
            summary.write_text("# Сводка\n", encoding="utf-8")
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample-v1",
                        "scope_slug: sample",
                        "current_stage: ft-test-case-reviewer",
                        "stage_status: signed-off",
                        "next_skill: null",
                        "review_mode: tc_review",
                        "current_round: 1",
                        "final_independent_tc_review_status: accepted",
                        "required_inputs: []",
                        "latest_artifacts:",
                        "  canonical_test_cases: test-cases/9.2-sample.md",
                        "  final_tc_review_findings: work/practical/sample/review-findings.final.md",
                        "  final_tc_review_independence: work/practical/sample/review-independence.final.md",
                        "open_questions: []",
                        "blocking_reasons: []",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            output = root / "exports" / "sample.zip"

            result = helper.export_scope(
                ft_package_root=ft_root,
                scope_id="01",
                summary_path=summary,
                output_path=output,
            )

            self.assertEqual("exported", result["status"])
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("manifest.json", names)
                self.assertIn("test-cases/9.2-sample.md", names)
                manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual("practical-accepted-baseline", manifest["bundle_type"])
            self.assertEqual("01", manifest["scope_id"])


if __name__ == "__main__":
    unittest.main()
