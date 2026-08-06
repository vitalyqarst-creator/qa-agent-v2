from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class PracticalReviewPreflightTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "practical_review_preflight.py"
        spec = importlib.util.spec_from_file_location(
            "practical_review_preflight_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def make_repository(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Preflight Test"], cwd=root, check=True)
        (root / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "branch", "-M", "codex/preflight-fixture"], cwd=root, check=True)
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, text=True, stdout=subprocess.PIPE
        ).stdout.strip()

        ft_root = root / "fts" / "Sample" / "Sample-v1"
        handoff = ft_root / "work" / "stage-handoffs" / "01-sample-scope"
        handoff.mkdir(parents=True)
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "ft_slug: Sample-v1",
                    "scope_slug: sample-scope",
                    "current_stage: ft-test-case-writer",
                    "stage_status: ready-for-next-stage",
                    "next_skill: ft-test-case-reviewer",
                    "review_mode: matrix_review",
                    "current_round: 1",
                    "required_inputs: []",
                    "latest_artifacts: {}",
                    "open_questions: []",
                    "blocking_reasons: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        summary = ft_root / "work" / "practical-stage-summary.md"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(
            "\n".join(
                [
                    "# Practical Stage Summary",
                    "",
                    "## Summary",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    "| route_profile | `practical route v0.8.2` |",
                    "| summary_stage | `matrix-ready` |",
                    f"| code_root | `{root.as_posix()}` |",
                    f"| execution_working_directory | `{root.as_posix()}` |",
                    f"| ft_package_root | `{ft_root.as_posix()}` |",
                    f"| artifact_write_root | `{(ft_root / 'work').as_posix()}` |",
                    "| root_split_allowed | `no` |",
                    "| root_split_authority | `not-applicable` |",
                    "| next_stage_transition | `matrix-review allowed` |",
                    "| active_scope_ids | `01` |",
                    "",
                    "## Code Version Gate",
                    "",
                    "| field | expected | actual | result |",
                    "| --- | --- | --- | --- |",
                    "| branch | `codex/preflight-fixture` | `codex/preflight-fixture` | `pass` |",
                    f"| commit | `{commit}` | `{commit}` | `pass` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return tmp, root, ft_root, summary

    def run_preflight(self, helper, root: Path, ft_root: Path, summary: Path):
        with working_directory(root):
            return helper.build_preflight(
                repo_root=root,
                ft_package_root=ft_root,
                summary_path=summary,
                scope_ids=["01"],
                review_mode="matrix_review",
            )

    def test_allows_reviewer_launch_when_roots_version_and_scope_gate_match(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {"findings": []}
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertTrue(result["allowed"])
        self.assertEqual("allowed", result["status"])

    def test_blocks_reviewer_launch_for_current_scope_validator_error(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {
            "findings": [
                {
                    "id": "workflow-state-stale",
                    "severity": "error",
                    "category": "workflow-state",
                    "path": "work/stage-handoffs/01-sample-scope/workflow-state.yaml",
                }
            ]
        }
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertFalse(result["allowed"])
        self.assertIn("workflow-state-stale", "\n".join(result["blocking_reasons"]))

    def test_ignores_error_owned_by_another_scope_in_multi_scope_package(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {
            "findings": [
                {
                    "id": "workflow-state-stale",
                    "severity": "error",
                    "category": "workflow-state",
                    "path": "work/stage-handoffs/02-other-scope/workflow-state.yaml",
                }
            ]
        }
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertTrue(result["allowed"])

    def test_reviewer_receipt_verification_blocks_changed_commit(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {"findings": []}
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
            receipt = ft_root / "work" / "practical" / "sample-scope" / "review-launch-preflight.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(__import__("json").dumps(result), encoding="utf-8")
            changed = dict(result)
            changed["code_commit"] = "0" * 40
            issues = helper.verify_receipt(receipt, changed)
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertTrue(issues)
        self.assertIn("code_commit", "\n".join(issues))


if __name__ == "__main__":
    unittest.main()
