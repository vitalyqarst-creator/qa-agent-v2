from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


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

    def test_reports_writer_quality_gate_block_without_reviewer_launch(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        workflow = ft_root / "work" / "stage-handoffs" / "01-sample-scope" / "workflow-state.yaml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8")
            .replace("stage_status: ready-for-next-stage", "stage_status: blocked-quality-gate")
            .replace("next_skill: ft-test-case-reviewer", "next_skill: ft-test-case-writer"),
            encoding="utf-8",
        )
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "matrix-review allowed", "matrix-review blocked"
            ),
            encoding="utf-8",
        )
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {"findings": []}
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertFalse(result["allowed"])
        self.assertEqual("blocked", result["status"])
        checks = {item["id"]: item["status"] for item in result["checks"]}
        self.assertEqual("blocked", checks["summary-contract"])
        self.assertEqual("blocked", checks["scope-routing"])
        self.assertIn(
            "Writer Quality Gate blocks reviewer launch",
            "\n".join(result["blocking_reasons"]),
        )
        self.assertNotIn(
            "summary next_stage_transition=matrix-review blocked",
            "\n".join(result["blocking_reasons"]),
        )

    def test_blocks_tc_reviewer_when_linked_prewrite_snapshot_is_invalid(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        workflow = ft_root / "work" / "stage-handoffs" / "01-sample-scope" / "workflow-state.yaml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8")
            .replace("review_mode: matrix_review", "review_mode: tc_review")
            .replace(
                "latest_artifacts: {}",
                "latest_artifacts:\n  pre_write_baseline_snapshot: work/review-cycles/sample-scope/versions/pre-write-r1",
            ),
            encoding="utf-8",
        )
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "matrix-review allowed", "tc-review allowed"
            ),
            encoding="utf-8",
        )
        snapshot = ft_root / "work" / "review-cycles" / "sample-scope" / "versions" / "pre-write-r1"
        snapshot.mkdir(parents=True)
        (snapshot / "snapshot-manifest.yaml").write_text("{}\n", encoding="utf-8")
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {"findings": []}
        try:
            with working_directory(root):
                result = helper.build_preflight(
                    repo_root=root,
                    ft_package_root=ft_root,
                    summary_path=summary,
                    scope_ids=["01"],
                    review_mode="tc_review",
                )
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertFalse(result["allowed"])
        self.assertIn("pre-write baseline snapshot is invalid", "\n".join(result["blocking_reasons"]))

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

    def test_receipt_reports_external_errors_separately_from_scope_blockers(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        other_handoff = ft_root / "work" / "stage-handoffs" / "02-other-scope"
        other_handoff.mkdir()
        (other_handoff / "workflow-state.yaml").write_text(
            "scope_slug: other-scope\n",
            encoding="utf-8",
        )
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {
            "findings": [
                {
                    "id": "workflow-state-stale",
                    "severity": "error",
                    "category": "workflow-state",
                    "path": "work/stage-handoffs/01-sample-scope/workflow-state.yaml",
                },
                {
                    "id": "other-scope-stale",
                    "severity": "error",
                    "category": "workflow-state",
                    "path": "work/stage-handoffs/02-other-scope/workflow-state.yaml",
                },
            ]
        }
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertFalse(result["allowed"])
        self.assertEqual(
            [
                "workflow-state-stale @ "
                "work/stage-handoffs/01-sample-scope/workflow-state.yaml"
            ],
            result["validator_error_partition"]["scope_relevant"],
        )
        self.assertEqual(
            [
                "other-scope-stale @ "
                "work/stage-handoffs/02-other-scope/workflow-state.yaml"
            ],
            result["validator_error_partition"]["external"],
        )
        details = {item["id"]: item["details"] for item in result["checks"]}
        self.assertIn("external_errors=1", details["package-validator"])

    def test_receipt_hash_binds_controller_owned_workflow(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {"findings": []}
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
        finally:
            helper.artifact_validator.validate = original_validate

        hashes = result["controller_artifact_hashes"]
        self.assertEqual(result["summary_sha256"], hashes["summary_sha256"])
        self.assertIn("01", hashes["workflow_state_sha256_by_scope"])

    def test_materializes_hash_bound_controller_recovery_snapshot(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {"findings": []}
        try:
            result = self.run_preflight(helper, root, ft_root, summary)
            receipt_path = ft_root / "work" / "practical" / "sample-scope" / "review-launch-preflight.json"
            materialized = helper.materialize_controller_snapshot(result, receipt_path)
            descriptors, issues = helper.scope_descriptors(ft_root, ["01"])
            targets, snapshot_issues = helper.verify_controller_snapshot(
                materialized,
                ft_package_root=ft_root,
                summary_path=summary,
                descriptors=descriptors,
            )
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertFalse(issues)
        self.assertFalse(snapshot_issues)
        self.assertEqual({"summary", "workflow:01"}, set(targets))
        self.assertTrue(Path(materialized["controller_artifact_snapshot"]["manifest"]).is_file())

    def test_check_only_runs_the_gate_without_creating_receipt_or_snapshot(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {"findings": []}
        try:
            with patch.object(
                sys,
                "argv",
                [
                    "practical_review_preflight.py",
                    "--repo-root",
                    str(root),
                    "--ft-package-root",
                    str(ft_root),
                    "--summary",
                    str(summary),
                    "--scope-id",
                    "01",
                    "--review-mode",
                    "matrix_review",
                    "--check-only",
                ],
            ), working_directory(root):
                self.assertEqual(0, helper.main())
        finally:
            helper.artifact_validator.validate = original_validate

        self.assertFalse(list(ft_root.rglob("review-launch-preflight*.json")))
        self.assertFalse(list(ft_root.rglob("*.controller-state")))

    def test_check_only_cannot_be_combined_with_receipt_modes(self) -> None:
        helper = self.load_helper()
        with patch.object(
            sys,
            "argv",
            [
                "practical_review_preflight.py",
                "--ft-package-root",
                "fixture",
                "--summary",
                "summary.md",
                "--scope-id",
                "01",
                "--review-mode",
                "matrix_review",
                "--check-only",
                "--output",
                "receipt.json",
            ],
        ), self.assertRaisesRegex(SystemExit, "mutually exclusive"):
            helper.main()

    def test_ignores_practical_artifact_error_owned_by_another_scope(self) -> None:
        helper = self.load_helper()
        _, root, ft_root, summary = self.make_repository()
        other_handoff = ft_root / "work" / "stage-handoffs" / "02-other-scope"
        other_handoff.mkdir()
        (other_handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "ft_slug: Sample-v1",
                    "scope_slug: other-scope",
                    "current_stage: ft-test-case-writer",
                    "stage_status: ready-for-review",
                    "next_skill: ft-test-case-reviewer",
                    "review_mode: tc_review",
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
        original_validate = helper.artifact_validator.validate
        helper.artifact_validator.validate = lambda _: {
            "findings": [
                {
                    "id": "review-findings-nonrussian-human-field",
                    "severity": "error",
                    "category": "language",
                    "path": "work/practical/other-scope/review-findings.md",
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
