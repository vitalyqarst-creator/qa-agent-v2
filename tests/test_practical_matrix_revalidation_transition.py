from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PracticalMatrixRevalidationTransitionTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "practical_matrix_revalidation_transition.py"
        spec = importlib.util.spec_from_file_location(
            "practical_matrix_revalidation_transition_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_builds_only_exact_r2_to_tc_review_transition(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            (root / "versioned.txt").write_text("v\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "versioned.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
            branch = subprocess.check_output(["git", "-C", str(root), "branch", "--show-current"], text=True).strip()
            commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
            ft_root = root / "fts" / "Sample" / "Sample-v1"
            handoff = ft_root / "work" / "stage-handoffs" / "01-sample"
            practical = ft_root / "work" / "practical" / "sample"
            handoff.mkdir(parents=True)
            practical.mkdir(parents=True)
            matrix = practical / "test-design-matrix.md"
            matrix.write_text("# Матрица\n", encoding="utf-8")
            canonical = ft_root / "test-cases" / "sample.md"
            canonical.parent.mkdir()
            canonical.write_text("# Тест-кейсы\n", encoding="utf-8")
            prompt = practical / "prompt.tc-to-reviewer.md"
            prompt.write_text("# Ревью\n", encoding="utf-8")
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample-v1",
                        "scope_slug: sample",
                        "current_stage: ft-test-case-writer",
                        "stage_status: ready-for-review",
                        "next_skill: ft-test-case-reviewer",
                        "review_mode: matrix_review",
                        "current_round: 2",
                        "matrix_review_status: invalidated",
                        "matrix_revalidation_reason: reviewed-matrix-hash-mismatch",
                        "required_inputs:",
                        "  - work/practical/sample/prompt.tc-to-reviewer.md",
                        "latest_artifacts:",
                        "  canonical_test_cases: test-cases/sample.md",
                        "  test_design_matrix: work/practical/sample/test-design-matrix.md",
                        "open_questions: []",
                        "blocking_reasons: []",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            summary = practical / "practical-stage-summary.md"
            summary.write_text(
                "\n".join(
                    [
                        "# Сводка практического этапа",
                        "",
                        "## Сводка",
                        "",
                        "| Поле | Значение |",
                        "| --- | --- |",
                        "| summary_stage | `matrix-revalidation-blocked` |",
                        "| next_stage_transition | `tc-review blocked` |",
                        "| next_safe_step | `old` |",
                        "| review_launch_preflight_status | `not-run` |",
                        "| review_launch_preflight_evidence | `not-applicable` |",
                        "| review_launch_preflight_receipt | `not-applicable` |",
                        "| reporting_evidence | `old` |",
                        "",
                        "## Переходы по областям",
                        "",
                        "| Область | Вердикт | Следующий переход | Противоречие источнику | Решение по TC со статусами | Причина |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| `01` | `blocked` | `writer blocked` | `not-applicable` | `not-applicable` | old |",
                        "",
                        "## Действия текущего этапа",
                        "\n- old\n",
                    ]
                ),
                encoding="utf-8",
            )
            finalization = practical / "controller-finalization-r2.json"
            finalization.write_text(
                json.dumps(
                    {
                        "allowed": True,
                        "scope_ids": ["01"],
                        "review_mode": "matrix_review",
                        "recovery_context": "matrix-revalidation-after-canonical-tcs",
                        "next_controller_transition": "tc-review required",
                        "code_branch": branch,
                        "code_commit": commit,
                        "review_subject_artifacts_by_scope": {
                            "01": {
                                "role": "test-design-matrix",
                                "source_path": matrix.resolve().as_posix(),
                                "sha256": sha256(matrix),
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result, updates, summary_after = helper.build_transition(
                repo_root=root,
                ft_package_root=ft_root,
                summary_path=summary,
                scope_ids=["01"],
                finalization_packet=finalization,
            )

        self.assertTrue(result["allowed"], result["blocking_reasons"])
        self.assertEqual(1, len(updates))
        state = updates[0][1]
        self.assertEqual("tc_review", state["review_mode"])
        self.assertEqual("matrix-accepted", state["matrix_review_status"])
        self.assertIn("active_transition_prompt", state["latest_artifacts"])
        self.assertIn("tc-review allowed", summary_after or "")


if __name__ == "__main__":
    unittest.main()
