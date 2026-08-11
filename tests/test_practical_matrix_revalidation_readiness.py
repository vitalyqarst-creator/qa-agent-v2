from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PracticalMatrixRevalidationReadinessTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "practical_matrix_revalidation_readiness.py"
        spec = importlib.util.spec_from_file_location(
            "practical_matrix_revalidation_readiness_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_selects_only_durable_saved_suite_gates(self) -> None:
        helper = self.load_helper()
        descriptor = helper.review_preflight.ScopeDescriptor(
            scope_id="01",
            handoff_dir=Path("fts/Sample/work/stage-handoffs/01-sample"),
            scope_slug="sample",
            workflow_path=Path("fts/Sample/work/stage-handoffs/01-sample/workflow-state.yaml"),
            canonical_test_case_paths=("test-cases/sample.md",),
        )
        report = {
            "findings": [
                {
                    "id": "workflow-state-ready-for-review-missing-handoff-source-rows",
                    "severity": "error",
                    "path": "fts/Sample/work/stage-handoffs/01-sample/workflow-state.yaml",
                    "details": "source rows are absent",
                },
                {
                    "id": "practical-workflow-reviewed-matrix-hash-mismatch",
                    "severity": "error",
                    "path": "fts/Sample/work/stage-handoffs/01-sample/workflow-state.yaml",
                    "details": "expected transitional finding",
                },
            ]
        }

        blockers = helper.canonical_suite_blockers(report, [descriptor])

        self.assertEqual(1, len(blockers))
        self.assertEqual(
            "workflow-state-ready-for-review-missing-handoff-source-rows",
            blockers[0]["id"],
        )


if __name__ == "__main__":
    unittest.main()
