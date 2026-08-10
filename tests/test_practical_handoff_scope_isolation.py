from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_scope_isolation",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PracticalHandoffScopeIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    def test_history_is_not_an_active_practical_controller_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            active = root / "fts" / "Sample" / "work" / "practical" / "scope-a" / "practical-stage-summary.md"
            historical = active.parent / "history" / "pre-acceptance" / "practical-stage-summary.md"
            active.parent.mkdir(parents=True)
            historical.parent.mkdir(parents=True)
            active.write_text("# active\n", encoding="utf-8")
            historical.write_text("# historical\n", encoding="utf-8")

            artifacts = self.validator.iter_practical_controller_artifacts(root)

            self.assertEqual(artifacts, [active])

    def test_practical_workflow_rejects_reference_to_other_scope_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ft_root = root / "fts" / "Sample"
            workflow = ft_root / "work" / "stage-handoffs" / "04-scope-a" / "workflow-state.yaml"
            workflow.parent.mkdir(parents=True)
            state = {"route_profile": "practical_v0_8", "scope_slug": "scope-a"}

            issues = self.validator.practical_active_artifact_reference_issues(
                state,
                workflow,
                root,
                ft_root,
                ["work/practical/scope-b/scope-brief.md"],
            )

            self.assertEqual(len(issues), 1)
            self.assertIn("expected_under=work/practical/scope-a/", issues[0])

    def test_russian_practical_matrix_labels_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix = root / "test-design-matrix.md"
            matrix.write_text(
                "\n".join(
                    [
                        "# Матрица тест-дизайна",
                        "",
                        "## Матрица применимости тест-дизайна",
                        "",
                        "| Измерение | Применимость | Ссылка на источник | Обоснование | Связанные атомы | Плановые тест-кейсы | Идентификатор GAP |",
                        "| --- | --- | --- | --- | --- | --- | --- |",
                        "| `traceability` | `yes` | `SRC-001` | Требование в scope. | `ATOM-001` | `TC-001` |  |",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_test_design_matrix_language(matrix, root)
            rows = self.validator.parsed_test_design_applicability_rows(matrix.read_text(encoding="utf-8"))

            self.assertEqual(findings, [])
            self.assertEqual(rows[0]["dimension"], "traceability")

    def test_check_only_status_requires_evidence_and_no_receipt(self) -> None:
        valid = {
            "review_launch_preflight_status": "check-only-allowed",
            "review_launch_preflight_receipt": "not-applicable",
            "review_launch_preflight_evidence": "practical_review_preflight.py --check-only; allowed=true",
        }
        invalid = dict(valid, review_launch_preflight_receipt="work/practical/scope/review-launch-preflight.json")

        self.assertEqual(self.validator.practical_stage_summary_preflight_status_issues(valid), [])
        self.assertIn(
            "check-only-allowed requires review_launch_preflight_receipt=not-applicable",
            self.validator.practical_stage_summary_preflight_status_issues(invalid),
        )


if __name__ == "__main__":
    unittest.main()
