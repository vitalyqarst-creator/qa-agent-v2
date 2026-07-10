from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.contracts import ExpectedOutput, StageInputManifest
from test_case_agent.review_cycle.orchestration import StageCompletionCoordinator
from test_case_agent.review_cycle.runtime import (
    BackendStageExecution,
    StageArtifactStore,
    StageAttemptPaths,
    StageRuntimeError,
    artifact_ref,
    utc_timestamp,
)


class ReviewCycleBackendMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.instruction = self.root / "AGENTS.md"
        self.source = self.root / "fts/demo/source/main.xhtml"
        self.handoff = self.root / "fts/demo/work/handoff/scope.md"
        for path in (self.instruction, self.source, self.handoff):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(path.name + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare(self, backend: str, *, create_output: bool = True):
        cycle = self.root / f"work/review-cycles/{backend}"
        attempt = cycle / "attempts/writer-r1/attempt-001"
        prompt = attempt / "prompt.md"
        output = attempt / "stage-output/draft.md"
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text("prompt\n", encoding="utf-8")
        if create_output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("draft\n", encoding="utf-8")
        manifest = StageInputManifest.create(
            cycle_id=backend,
            stage_id="writer-r1",
            attempt_id="attempt-001",
            session_id=f"logical-{backend}",
            role="writer",
            scenario="writer.session_initial_draft",
            semantic_round=0,
            sandbox_policy="workspace_write",
            timeout_seconds=30,
            attempt_root=attempt.relative_to(self.root).as_posix(),
            canonical_test_cases="fts/demo/test-cases/1-demo.md",
            prompt_artifact=artifact_ref(prompt, self.root, kind="prompt"),
            instruction_artifacts=[artifact_ref(self.instruction, self.root, kind="instruction")],
            source_artifacts=[artifact_ref(self.source, self.root, kind="source")],
            handoff_artifacts=[artifact_ref(self.handoff, self.root, kind="handoff")],
            expected_outputs=[
                ExpectedOutput(
                    path=output.relative_to(self.root).as_posix(),
                    kind="draft",
                    producer="stage",
                )
            ],
            allowed_write_roots=[(attempt / "stage-output").relative_to(self.root).as_posix()],
            forbidden_write_roots=["fts/demo/test-cases"],
        )
        StageArtifactStore(self.root).write_manifest(
            StageAttemptPaths.from_manifest(self.root, manifest), manifest
        )
        now = utc_timestamp()
        execution = BackendStageExecution(
            backend=backend,
            backend_session_id=f"thread-{backend}",
            started_at=now,
            finished_at=now,
            duration_ms=10,
            exit_code=0,
            usage={"total_tokens": 12} if backend == "sdk-fresh-thread" else None,
        )
        return cycle, attempt, manifest, execution

    def test_exec_and_sdk_evidence_use_the_same_completion_path(self) -> None:
        completed = []
        for backend in ("codex-exec", "sdk-fresh-thread"):
            cycle, _, manifest, execution = self.prepare(backend)
            completed.append(
                StageCompletionCoordinator(self.root, cycle).complete(
                    manifest,
                    execution,
                    outcome="draft-ready",
                )
            )
        self.assertEqual(["draft-ready", "draft-ready"], [item.result.outcome for item in completed])
        self.assertEqual(
            ["codex-exec", "sdk-fresh-thread"],
            [item.metrics.backend for item in completed],
        )
        self.assertTrue(all(item.result_path.is_file() for item in completed))
        self.assertTrue(all(item.metrics_path.is_file() for item in completed))

    def test_missing_required_output_blocks_both_backend_completions(self) -> None:
        for backend in ("codex-exec", "sdk-fresh-thread"):
            cycle, _, manifest, execution = self.prepare(backend, create_output=False)
            with self.assertRaisesRegex(StageRuntimeError, "required stage output is missing"):
                StageCompletionCoordinator(self.root, cycle).complete(
                    manifest,
                    execution,
                    outcome="draft-ready",
                )

    def test_blocked_result_may_persist_without_required_stage_output(self) -> None:
        cycle, _, manifest, execution = self.prepare("codex-exec", create_output=False)
        completed = StageCompletionCoordinator(self.root, cycle).complete(
            manifest,
            execution,
            outcome="blocked",
            blocking_reasons=("timeout",),
        )
        self.assertEqual("blocked", completed.result.status)
        self.assertEqual((), completed.result.output_artifacts)
        self.assertEqual("blocked", completed.metrics.outcome)
        self.assertEqual(0, completed.metrics.output_artifact_count)

    def test_prior_backend_session_id_is_rejected_for_nonblocked_result(self) -> None:
        cycle, _, manifest, execution = self.prepare("codex-exec")
        with self.assertRaisesRegex(StageRuntimeError, "fresh stage session"):
            StageCompletionCoordinator(self.root, cycle).complete(
                manifest,
                execution,
                outcome="draft-ready",
                prior_backend_session_ids=(execution.backend_session_id,),
            )

    def test_completion_is_immutable(self) -> None:
        cycle, _, manifest, execution = self.prepare("codex-exec")
        coordinator = StageCompletionCoordinator(self.root, cycle)
        coordinator.complete(manifest, execution, outcome="draft-ready")
        with self.assertRaisesRegex(StageRuntimeError, "immutable"):
            coordinator.complete(manifest, execution, outcome="draft-ready")

    def test_backend_cannot_mutate_a_declared_input_before_completion(self) -> None:
        cycle, _, manifest, execution = self.prepare("codex-exec")
        self.source.write_text("mutated source\n", encoding="utf-8")
        with self.assertRaisesRegex(StageRuntimeError, "hash mismatch"):
            StageCompletionCoordinator(self.root, cycle).complete(
                manifest,
                execution,
                outcome="draft-ready",
            )
        self.assertFalse((Path(self.root) / manifest.attempt_root / "stage-result.json").exists())


if __name__ == "__main__":
    unittest.main()
