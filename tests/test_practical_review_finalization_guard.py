from __future__ import annotations

import hashlib
import importlib.util
import json
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

    def make_fixture(self) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo_root = Path(tmp.name)
        ft_root = repo_root / "fts" / "Sample" / "Sample-v1"
        handoff = ft_root / "work" / "stage-handoffs" / "01-sample"
        handoff.mkdir(parents=True)
        workflow = handoff / "workflow-state.yaml"
        workflow.write_text(
            "\n".join(
                [
                    "ft_slug: Sample-v1",
                    "scope_slug: sample",
                    "current_stage: ft-test-case-reviewer",
                    "stage_status: ready-for-next-stage",
                    "next_skill: ft-test-case-reviewer",
                    "review_mode: tc_review",
                    "current_round: 1",
                    f"controller_task_or_session: {CONTROLLER_ID}",
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
        summary.write_text("# Сводка\n", encoding="utf-8")
        receipt = ft_root / "work" / "practical" / "sample" / "review-launch-preflight.json"
        receipt.parent.mkdir(parents=True)
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
                    "review_mode": "tc_review",
                    "scope_ids": ["01"],
                    "controller_artifact_hashes": {
                        "summary_sha256": sha256(summary),
                        "workflow_state_sha256_by_scope": {"01": sha256(workflow)},
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
        review = receipt.parent / "review-findings.final.md"
        review.write_text(
            "\n".join(
                [
                    "## Verdict",
                    "",
                    "`tc-accepted`",
                    "",
                    "| Field | Value |",
                    "| --- | --- |",
                    "| scope_slug | `sample` |",
                    "| review_mode | `tc_review` |",
                    "| review_round | `1` |",
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
                    "| review_mode | `tc_review` |",
                    "| review_round | `1` |",
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
