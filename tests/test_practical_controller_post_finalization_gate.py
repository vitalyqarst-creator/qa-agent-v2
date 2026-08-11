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


class PracticalControllerPostFinalizationGateTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "practical_controller_post_finalization_gate.py"
        spec = importlib.util.spec_from_file_location(
            "practical_controller_post_finalization_gate_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def make_fixture(self) -> tuple[Path, Path, Path, Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        ft_root = Path(tmp.name) / "fts" / "Sample" / "Sample-v1"
        handoff = ft_root / "work" / "stage-handoffs" / "01-sample"
        practical = ft_root / "work" / "practical" / "sample"
        handoff.mkdir(parents=True)
        practical.mkdir(parents=True)
        matrix = practical / "test-design-matrix.md"
        matrix.write_text("# Matrix\n", encoding="utf-8")
        parity = handoff / "source-parity-check.md"
        parity.write_text("# Source parity\n\nOpen gaps/questions: `GAP-001`\n", encoding="utf-8")
        repair = handoff / "matrix-repair-summary.md"
        repair.write_text("# Repair\n\n`GAP-001` resolved by source clarification.\n", encoding="utf-8")
        workflow = handoff / "workflow-state.yaml"
        workflow.write_text(
            "\n".join(
                [
                    "ft_slug: Sample-v1",
                    "scope_slug: sample",
                    "current_stage: ft-test-case-reviewer",
                    "stage_status: ready-for-next-stage",
                    "next_skill: ft-test-case-writer",
                    "current_round: 1",
                    "latest_artifacts:",
                    "  matrix_repair_summary: work/stage-handoffs/01-sample/matrix-repair-summary.md",
                    "  source_parity_check: work/stage-handoffs/01-sample/source-parity-check.md",
                    "  test_design_matrix: work/practical/sample/test-design-matrix.md",
                    "open_questions: []",
                    "blocking_reasons: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        summary = ft_root / "work" / "practical-stage-summary.md"
        summary.write_text("# Сводка\n", encoding="utf-8")
        launch = practical / "review-launch-preflight.json"
        commit = subprocess.check_output(
            ["git", "-C", str(ROOT_DIR), "rev-parse", "HEAD"], text=True, encoding="utf-8"
        ).strip()
        branch = subprocess.check_output(
            ["git", "-C", str(ROOT_DIR), "branch", "--show-current"], text=True, encoding="utf-8"
        ).strip()
        review_subjects = {
            "01": {
                "role": "test-design-matrix",
                "source_path": matrix.resolve().as_posix(),
                "sha256": sha256(matrix),
            }
        }
        launch.write_text(
            json.dumps(
                {
                    "code_branch": branch,
                    "code_commit": commit,
                    "review_mode": "matrix_review",
                    "review_subject_artifacts_by_scope": review_subjects,
                }
            ),
            encoding="utf-8",
        )
        finalization = practical / "review-finalization.json"
        finalization.write_text(
            json.dumps(
                {
                    "allowed": True,
                    "scope_ids": ["01"],
                    "launch_receipt": launch.resolve().as_posix(),
                    "review_mode": "matrix_review",
                    "review_subject_artifacts_by_scope": review_subjects,
                }
            ),
            encoding="utf-8",
        )
        return ft_root, summary, launch, finalization, parity

    def test_blocks_writer_transition_when_resolved_gap_stays_open_in_parity(self) -> None:
        helper = self.load_helper()
        ft_root, summary, launch, finalization, _ = self.make_fixture()
        original_validate = helper.review_preflight.artifact_validator.validate
        helper.review_preflight.artifact_validator.validate = lambda _root: {"findings": []}
        try:
            result = helper.build_post_finalization_gate(
                repo_root=ROOT_DIR,
                ft_package_root=ft_root,
                summary_path=summary,
                scope_ids=["01"],
                launch_receipt=launch,
                finalization_packet=finalization,
            )
        finally:
            helper.review_preflight.artifact_validator.validate = original_validate

        self.assertFalse(result["allowed"])
        self.assertIn("closed gap remains active", "\n".join(result["blocking_reasons"]))

    def test_allows_reconciled_parity_and_blocks_changed_code(self) -> None:
        helper = self.load_helper()
        ft_root, summary, launch, finalization, parity = self.make_fixture()
        parity.write_text("# Source parity\n\nOpen gaps/questions: none\n", encoding="utf-8")
        original_validate = helper.review_preflight.artifact_validator.validate
        helper.review_preflight.artifact_validator.validate = lambda _root: {"findings": []}
        try:
            allowed = helper.build_post_finalization_gate(
                repo_root=ROOT_DIR,
                ft_package_root=ft_root,
                summary_path=summary,
                scope_ids=["01"],
                launch_receipt=launch,
                finalization_packet=finalization,
            )
            launch_payload = json.loads(launch.read_text(encoding="utf-8"))
            launch_payload["code_commit"] = "0" * 40
            launch.write_text(json.dumps(launch_payload), encoding="utf-8")
            blocked = helper.build_post_finalization_gate(
                repo_root=ROOT_DIR,
                ft_package_root=ft_root,
                summary_path=summary,
                scope_ids=["01"],
                launch_receipt=launch,
                finalization_packet=finalization,
            )
        finally:
            helper.review_preflight.artifact_validator.validate = original_validate

        self.assertTrue(allowed["allowed"], allowed["blocking_reasons"])
        self.assertFalse(blocked["allowed"])
        self.assertIn("pinned-code-version-changed", "\n".join(blocked["blocking_reasons"]))

    def test_requires_recovery_state_before_routing_revalidated_matrix_to_tc_review(self) -> None:
        helper = self.load_helper()
        ft_root, summary, launch, finalization, parity = self.make_fixture()
        parity.write_text("# Source parity\n\nOpen gaps/questions: none\n", encoding="utf-8")
        finalization_payload = json.loads(finalization.read_text(encoding="utf-8"))
        finalization_payload["next_controller_transition"] = "tc-review required"
        finalization.write_text(json.dumps(finalization_payload), encoding="utf-8")
        original_validate = helper.review_preflight.artifact_validator.validate
        helper.review_preflight.artifact_validator.validate = lambda _root: {"findings": []}
        try:
            result = helper.build_post_finalization_gate(
                repo_root=ROOT_DIR,
                ft_package_root=ft_root,
                summary_path=summary,
                scope_ids=["01"],
                launch_receipt=launch,
                finalization_packet=finalization,
            )
        finally:
            helper.review_preflight.artifact_validator.validate = original_validate

        self.assertFalse(result["allowed"])
        self.assertIn("tc-review recovery checkpoint", "\n".join(result["blocking_reasons"]))


if __name__ == "__main__":
    unittest.main()
