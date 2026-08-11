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
TASK_ID = "019fda6b-f604-7130-80a5-8e0d1d7f5c7f"
CONTROLLER_ID = "019fda6b-f604-7130-80a5-8e0d7e3546a1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PracticalReviewFinalizationGuardTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "practical_review_finalization_guard.py"
        spec = importlib.util.spec_from_file_location(
            "practical_review_finalization_guard_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def load_recovery_helper(self):
        module_path = ROOT_DIR / "scripts" / "restore_practical_review_controller_state.py"
        spec = importlib.util.spec_from_file_location(
            "restore_practical_review_controller_state_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def make_fixture(
        self,
        *,
        review_mode: str = "tc_review",
        matrix_revalidation: bool = False,
    ) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo_root = Path(tmp.name)
        (repo_root / "versioned.txt").write_text("versioned\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
        subprocess.run(
            ["git", "-C", str(repo_root), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_root), "config", "user.name", "Test"], check=True
        )
        subprocess.run(["git", "-C", str(repo_root), "add", "versioned.txt"], check=True)
        subprocess.run(
            ["git", "-C", str(repo_root), "commit", "-qm", "fixture"], check=True
        )
        branch = subprocess.check_output(
            ["git", "-C", str(repo_root), "branch", "--show-current"],
            text=True,
            encoding="utf-8",
        ).strip()
        commit = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
        ).strip()
        ft_root = repo_root / "fts" / "Sample" / "Sample-v1"
        handoff = ft_root / "work" / "stage-handoffs" / "01-sample"
        handoff.mkdir(parents=True)
        workflow = handoff / "workflow-state.yaml"
        workflow.write_text(
            "\n".join(
                [
                    "ft_slug: Sample-v1",
                    "scope_slug: sample",
                    "current_stage: ft-test-case-writer"
                    if matrix_revalidation
                    else "current_stage: ft-test-case-reviewer",
                    "stage_status: ready-for-review"
                    if matrix_revalidation
                    else "stage_status: ready-for-next-stage",
                    "next_skill: ft-test-case-reviewer",
                    f"review_mode: {review_mode}",
                    f"current_round: {2 if matrix_revalidation else 1}",
                    "matrix_review_status: invalidated" if matrix_revalidation else "",
                    (
                        "matrix_revalidation_reason: reviewed-matrix-hash-mismatch"
                        if matrix_revalidation
                        else ""
                    ),
                    f"controller_task_or_session: {CONTROLLER_ID}",
                    "required_inputs: []",
                    "latest_artifacts:",
                    "  canonical_test_cases: test-cases/sample.md",
                    (
                        "  test_design_matrix: work/practical/sample/test-design-matrix.md"
                        if matrix_revalidation
                        else ""
                    ),
                    "open_questions: []",
                    "blocking_reasons: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        summary = ft_root / "work" / "practical-stage-summary.md"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text("# Сводка\n", encoding="utf-8")
        canonical = ft_root / "test-cases" / "sample.md"
        canonical.parent.mkdir(parents=True)
        canonical.write_text("# Test cases\n", encoding="utf-8")
        matrix = ft_root / "work" / "practical" / "sample" / "test-design-matrix.md"
        if matrix_revalidation:
            matrix.parent.mkdir(parents=True, exist_ok=True)
            matrix.write_text("# Matrix\n", encoding="utf-8")
        review_subject = matrix if review_mode == "matrix_review" else canonical
        review_subject_role = "test-design-matrix" if review_mode == "matrix_review" else "canonical-test-cases"
        verdict = "matrix-accepted" if review_mode == "matrix_review" else "tc-accepted"
        review_round = 2 if matrix_revalidation else 1
        receipt = ft_root / "work" / "practical" / "sample" / "review-launch-preflight.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        snapshot_dir = receipt.parent / "review-launch-preflight.controller-state"
        snapshot_dir.mkdir()
        summary_snapshot = snapshot_dir / "practical-stage-summary.md"
        workflow_snapshot = snapshot_dir / "workflow-state-01.yaml"
        summary_snapshot.write_bytes(summary.read_bytes())
        workflow_snapshot.write_bytes(workflow.read_bytes())
        snapshot_manifest = snapshot_dir / "manifest.json"
        snapshot_manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "controller_artifacts": {
                        "summary": {
                            "role": "practical-stage-summary",
                            "source_path": summary.resolve().as_posix(),
                            "snapshot_path": summary_snapshot.resolve().as_posix(),
                            "sha256": sha256(summary),
                        },
                        "workflow_state_by_scope": {
                            "01": {
                                "role": "workflow-state",
                                "source_path": workflow.resolve().as_posix(),
                                "snapshot_path": workflow_snapshot.resolve().as_posix(),
                                "sha256": sha256(workflow),
                            }
                        },
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        receipt.write_text(
            json.dumps(
                {
                    "allowed": True,
                    "repo_root": repo_root.resolve().as_posix(),
                    "ft_package_root": ft_root.resolve().as_posix(),
                    "review_mode": review_mode,
                    "scope_ids": ["01"],
                    "code_branch": branch,
                    "code_commit": commit,
                    "controller_artifact_hashes": {
                        "summary_sha256": sha256(summary),
                        "workflow_state_sha256_by_scope": {"01": sha256(workflow)},
                    },
                    "review_subject_artifacts_by_scope": {
                        "01": {
                            "role": review_subject_role,
                            "source_path": review_subject.resolve().as_posix(),
                            "sha256": sha256(review_subject),
                        }
                    },
                    "controller_artifact_snapshot": {
                        "schema_version": 1,
                        "directory": snapshot_dir.resolve().as_posix(),
                        "manifest": snapshot_manifest.resolve().as_posix(),
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        dispatch = receipt.parent / "review-dispatch.json"
        dispatch.write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "status": "dispatched",
                    "allowed": True,
                    "launch_receipt": receipt.resolve().as_posix(),
                    "launch_receipt_sha256": sha256(receipt),
                    "reviewer_task_or_session": TASK_ID,
                    "reviewer_execution_surface": "codex-thread",
                    "reviewer_thread_url_or_id": TASK_ID,
                    "controller_task_or_session": CONTROLLER_ID,
                    "controller_execution_surface": "codex-thread",
                    "controller_identity_verified": True,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        review = receipt.parent / (
            "test-design-matrix-review.final.md" if review_mode == "matrix_review" else "review-findings.final.md"
        )
        review.write_text(
            "\n".join(
                [
                    "## Verdict",
                    "",
                    f"`{verdict}`",
                    "",
                    "| Field | Value |",
                    "| --- | --- |",
                    "| scope_slug | `sample` |",
                    f"| review_mode | `{review_mode}` |",
                    f"| review_round | `{review_round}` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        independence = receipt.parent / "review-independence.final.md"
        independence.write_text(
            "\n".join(
                [
                    "| field | value |",
                    "| --- | --- |",
                    f"| reviewer_dispatch_receipt | `{dispatch.name}` |",
                    "| reviewer_was_separate_session | `yes` |",
                    "| reviewer_input_excluded_writer_transcript | `yes` |",
                    "| reviewer_input_excluded_writer_private_reasoning | `yes` |",
                    "| reviewer_modified_test_cases | `no` |",
                    "| independent_signoff_claim_allowed | `yes` |",
                    f"| review_mode | `{review_mode}` |",
                    f"| review_round | `{review_round}` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return repo_root, ft_root, summary, receipt, dispatch, review, independence

    def test_accepts_independent_review_without_controller_mutation(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertTrue(result["allowed"], result["blocking_reasons"])
        self.assertEqual("ready-for-controller-finalization", result["status"])
        self.assertEqual("tc-accepted", result["verdict"])
        self.assertEqual("accepted-local-publication-pending", result["next_controller_transition"])

    def test_matrix_revalidation_after_canonical_tcs_routes_to_tc_review(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture(
            review_mode="matrix_review",
            matrix_revalidation=True,
        )

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="matrix_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertTrue(result["allowed"], result["blocking_reasons"])
        self.assertEqual("matrix-revalidation-after-canonical-tcs", result["recovery_context"])
        self.assertEqual("tc-review required", result["next_controller_transition"])

    def test_blocks_when_reviewer_changed_controller_workflow(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        workflow = ft_root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
        workflow.write_text(workflow.read_text(encoding="utf-8") + "review_verdict: accepted\n", encoding="utf-8")

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertFalse(result["allowed"])
        self.assertIn("controller workflow-state changed", "\n".join(result["blocking_reasons"]))

    def test_blocks_when_launch_receipt_code_version_is_stale(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["code_commit"] = "0" * 40
        receipt.write_text(json.dumps(payload), encoding="utf-8")
        dispatch_payload = json.loads(dispatch.read_text(encoding="utf-8"))
        dispatch_payload["launch_receipt_sha256"] = sha256(receipt)
        dispatch.write_text(json.dumps(dispatch_payload), encoding="utf-8")

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertFalse(result["allowed"])
        self.assertIn(
            "review launch receipt code version differs from current checkout",
            "\n".join(result["blocking_reasons"]),
        )
        version_check = next(check for check in result["checks"] if check["id"] == "pinned-code-version")
        self.assertEqual("fail", version_check["status"])

    def test_blocks_when_review_subject_changed_after_launch(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        canonical = ft_root / "test-cases" / "sample.md"
        canonical.write_text("# Changed test cases\n", encoding="utf-8")

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertFalse(result["allowed"])
        self.assertIn("review subject changed", "\n".join(result["blocking_reasons"]))

    def test_accepts_heading_style_verdict(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertTrue(result["allowed"], result["blocking_reasons"])
        self.assertEqual("tc-accepted", result["verdict"])

    def test_blocks_review_submission_without_scope_metadata(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        review.write_text("## Verdict\n\n`tc-accepted`\n", encoding="utf-8")

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertFalse(result["allowed"])
        self.assertIn("review artifact lacks scope_slug", "\n".join(result["blocking_reasons"]))

    def test_explicit_recovery_restores_controller_snapshot(self) -> None:
        helper = self.load_helper()
        recovery = self.load_recovery_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        workflow = ft_root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
        summary.write_text("# Измененная сводка\n", encoding="utf-8")
        workflow.write_text("broken: yes\n", encoding="utf-8")

        recovery_result = recovery.build_recovery_result(
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            launch_receipt=receipt,
            restore=True,
        )
        finalization = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertTrue(recovery_result["allowed"], recovery_result["blocking_reasons"])
        self.assertTrue(recovery_result["restored"])
        self.assertEqual(["summary", "workflow:01"], recovery_result["changed_controller_targets_before_restore"])
        self.assertTrue(finalization["allowed"], finalization["blocking_reasons"])

    def test_blocks_non_session_review_dispatch(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        payload = json.loads(dispatch.read_text(encoding="utf-8"))
        payload["reviewer_execution_surface"] = "codex-task"
        dispatch.write_text(json.dumps(payload), encoding="utf-8")

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertFalse(result["allowed"])
        self.assertIn("separate Codex session", "\n".join(result["blocking_reasons"]))

    def test_blocks_dispatch_when_controller_identity_is_not_bound_to_workflow(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        payload = json.loads(dispatch.read_text(encoding="utf-8"))
        payload["controller_task_or_session"] = TASK_ID
        dispatch.write_text(json.dumps(payload), encoding="utf-8")

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertFalse(result["allowed"])
        self.assertIn("controller task/session id must differ", "\n".join(result["blocking_reasons"]))
        self.assertIn("workflow controller_task_or_session differs", "\n".join(result["blocking_reasons"]))

    def test_blocks_review_round_that_differs_from_workflow(self) -> None:
        helper = self.load_helper()
        repo_root, ft_root, summary, receipt, dispatch, review, independence = self.make_fixture()
        review.write_text(
            review.read_text(encoding="utf-8").replace("| review_round | `1` |", "| review_round | `2` |"),
            encoding="utf-8",
        )

        result = helper.build_finalization_packet(
            repo_root=repo_root,
            ft_package_root=ft_root,
            summary_path=summary,
            scope_ids=["01"],
            review_mode="tc_review",
            launch_receipt=receipt,
            dispatch_receipt=dispatch,
            review_artifact=review,
            independence_artifact=independence,
        )

        self.assertFalse(result["allowed"])
        self.assertIn("review_round differs", "\n".join(result["blocking_reasons"]))


if __name__ == "__main__":
    unittest.main()
