from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.contracts import ExpectedOutput, StageInputManifest, StageResult
from test_case_agent.review_cycle.metrics import (
    StageMetrics,
    StageMetricsRecorder,
    build_stage_metrics,
    summarize_metrics,
)
from test_case_agent.review_cycle.runtime import (
    BackendStageExecution,
    StageRuntimeError,
    artifact_ref,
    utc_timestamp,
)


class ReviewCycleMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cycle = self.root / "work/review-cycles/demo"
        self.attempt = self.cycle / "attempts/writer-r1/attempt-001"
        self.prompt = self.attempt / "prompt.md"
        self.instruction = self.root / "AGENTS.md"
        self.source = self.root / "fts/demo/source/main.xhtml"
        self.handoff = self.root / "fts/demo/work/handoff/scope.md"
        self.output = self.attempt / "stage-output/draft.md"
        for path, content in (
            (self.prompt, "prompt\n"),
            (self.instruction, "instruction\n"),
            (self.source, "source\n"),
            (self.handoff, "handoff\n"),
            (self.output, "draft\n"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def evidence(self):
        manifest = StageInputManifest.create(
            cycle_id="demo",
            stage_id="writer-r1",
            attempt_id="attempt-001",
            session_id="logical-session",
            role="writer",
            scenario="writer.session_initial_draft",
            semantic_round=0,
            sandbox_policy="workspace_write",
            timeout_seconds=30,
            attempt_root=self.attempt.relative_to(self.root).as_posix(),
            canonical_test_cases="fts/demo/test-cases/1-demo.md",
            prompt_artifact=artifact_ref(self.prompt, self.root, kind="prompt"),
            instruction_artifacts=[artifact_ref(self.instruction, self.root, kind="instruction")],
            source_artifacts=[artifact_ref(self.source, self.root, kind="source")],
            handoff_artifacts=[artifact_ref(self.handoff, self.root, kind="handoff")],
            expected_outputs=[
                ExpectedOutput(
                    path=self.output.relative_to(self.root).as_posix(),
                    kind="draft",
                    producer="stage",
                )
            ],
            allowed_write_roots=[(self.attempt / "stage-output").relative_to(self.root).as_posix()],
            forbidden_write_roots=["fts/demo/test-cases"],
        )
        now = utc_timestamp()
        result = StageResult(
            contract_version=2,
            cycle_id=manifest.cycle_id,
            stage_id=manifest.stage_id,
            attempt_id=manifest.attempt_id,
            session_id=manifest.session_id,
            backend_session_id="thread-1",
            role=manifest.role,
            scenario=manifest.scenario,
            input_digest=manifest.input_digest,
            status="completed",
            outcome="draft-ready",
            output_artifacts=(artifact_ref(self.output, self.root, kind="draft"),),
            started_at=now,
            finished_at=now,
            duration_ms=12,
            exit_code=0,
            timed_out=False,
            blocking_reasons=(),
        )
        execution = BackendStageExecution(
            backend="exec",
            backend_session_id="thread-1",
            started_at=now,
            finished_at=now,
            duration_ms=12,
            exit_code=0,
            usage={
                "input_tokens": 10,
                "output_tokens": 4,
                "reasoning_tokens": 2,
                "total_tokens": 14,
            },
        )
        return manifest, result, execution

    def test_build_metrics_counts_handoff_bytes_and_tokens(self) -> None:
        manifest, result, execution = self.evidence()
        metrics = build_stage_metrics(manifest, result, execution, repo_root=self.root)
        self.assertEqual(4, metrics.input_artifact_count)
        self.assertEqual(self.output.stat().st_size, metrics.output_artifact_bytes)
        self.assertEqual(14, metrics.total_tokens)
        self.assertEqual(2, metrics.reasoning_tokens)

    def test_legacy_metric_without_reasoning_tokens_remains_readable(self) -> None:
        metrics = build_stage_metrics(*self.evidence(), repo_root=self.root)
        legacy = metrics.to_dict()
        legacy.pop("reasoning_tokens")
        restored = StageMetrics.from_dict(legacy)
        self.assertIsNone(restored.reasoning_tokens)

    def test_recorder_writes_attempt_and_cycle_evidence(self) -> None:
        metrics = build_stage_metrics(*self.evidence(), repo_root=self.root)
        recorder = StageMetricsRecorder(self.cycle)
        path = recorder.record(self.attempt, metrics)
        self.assertTrue(path.is_file())
        self.assertEqual((metrics,), recorder.load())
        with self.assertRaisesRegex(StageRuntimeError, "immutable"):
            recorder.record(self.attempt, metrics)

    def test_summary_groups_latency_outcomes_and_optional_tokens(self) -> None:
        base = StageMetrics(
            contract_version=2,
            cycle_id="demo",
            stage_id="writer-r1",
            attempt_id="attempt-001",
            backend="exec",
            role="writer",
            scenario="writer.session_initial_draft",
            outcome="draft-ready",
            duration_ms=10,
            input_artifact_count=4,
            input_artifact_bytes=100,
            output_artifact_count=1,
            output_artifact_bytes=20,
            total_tokens=30,
        )
        blocked = StageMetrics(
            **{
                **base.to_dict(),
                "attempt_id": "attempt-002",
                "outcome": "blocked",
                "duration_ms": 30,
                "total_tokens": None,
            }
        )
        summary = summarize_metrics((base, blocked))["exec"]
        self.assertEqual(2, summary["stage_count"])
        self.assertEqual(1, summary["blocked_count"])
        self.assertEqual(10, summary["duration_ms_p50"])
        self.assertEqual(30, summary["duration_ms_p95"])
        self.assertEqual(30, summary["total_tokens"])

    def test_recorder_rejects_attempt_outside_cycle(self) -> None:
        metrics = build_stage_metrics(*self.evidence(), repo_root=self.root)
        with self.assertRaisesRegex(StageRuntimeError, "inside cycle root"):
            StageMetricsRecorder(self.cycle).record(self.root / "outside", metrics)


if __name__ == "__main__":
    unittest.main()
