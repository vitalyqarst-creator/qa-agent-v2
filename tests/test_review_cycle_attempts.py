from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.attempts import (
    AttemptRecoveryError,
    StageAttemptLedger,
    format_attempt_id,
)
from test_case_agent.review_cycle.contracts import ExpectedOutput, StageInputManifest, StageResult
from test_case_agent.review_cycle.runtime import (
    StageArtifactStore,
    StageAttemptPaths,
    artifact_ref,
    utc_timestamp,
)


class ReviewCycleAttemptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cycle = self.root / "fts/demo/work/review-cycles/demo"
        self.instruction = self.root / "AGENTS.md"
        self.source = self.root / "fts/demo/source/main.xhtml"
        self.handoff = self.root / "fts/demo/work/handoff/scope.md"
        for path in (self.instruction, self.source, self.handoff):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(path.name + "\n", encoding="utf-8")
        self.store = StageArtifactStore(self.root)
        self.ledger = StageAttemptLedger(self.root, self.cycle)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_attempt(
        self,
        number: int,
        *,
        outcome: str = "blocked",
        backend_session_id: str = "thread-1",
    ) -> tuple[StageInputManifest, Path]:
        attempt_id = format_attempt_id(number)
        attempt_root = self.cycle / "attempts/writer-r1" / attempt_id
        prompt = attempt_root / "prompt.md"
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text("prompt\n", encoding="utf-8")
        output = attempt_root / "stage-output/draft.md"
        manifest = StageInputManifest.create(
            cycle_id="demo",
            stage_id="writer-r1",
            attempt_id=attempt_id,
            session_id=f"logical-{attempt_id}",
            role="writer",
            scenario="writer.session_initial_draft",
            semantic_round=0,
            sandbox_policy="workspace_write",
            timeout_seconds=30,
            attempt_root=attempt_root.relative_to(self.root).as_posix(),
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
            allowed_write_roots=[(attempt_root / "stage-output").relative_to(self.root).as_posix()],
            forbidden_write_roots=["fts/demo/test-cases"],
        )
        paths = StageAttemptPaths.from_manifest(self.root, manifest)
        self.store.write_manifest(paths, manifest)
        outputs = ()
        if outcome == "draft-ready":
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("draft\n", encoding="utf-8")
            outputs = (artifact_ref(output, self.root, kind="draft"),)
        now = utc_timestamp()
        result = StageResult(
            contract_version=2,
            cycle_id=manifest.cycle_id,
            stage_id=manifest.stage_id,
            attempt_id=manifest.attempt_id,
            session_id=manifest.session_id,
            backend_session_id=backend_session_id,
            role=manifest.role,
            scenario=manifest.scenario,
            input_digest=manifest.input_digest,
            status="blocked" if outcome == "blocked" else "completed",
            outcome=outcome,
            output_artifacts=outputs,
            started_at=now,
            finished_at=now,
            duration_ms=1,
            exit_code=None if outcome == "blocked" else 0,
            timed_out=outcome == "blocked",
            blocking_reasons=("timeout",) if outcome == "blocked" else (),
        )
        self.store.write_result(paths, manifest, result)
        return manifest, output

    def test_empty_ledger_plans_first_attempt(self) -> None:
        plan = self.ledger.plan_next("writer-r1")
        self.assertEqual("attempt-001", plan.attempt_id)
        self.assertEqual((), plan.prior_backend_session_ids)

    def test_incomplete_attempt_blocks_automatic_retry(self) -> None:
        root = self.cycle / "attempts/writer-r1/attempt-001"
        root.mkdir(parents=True)
        with self.assertRaisesRegex(AttemptRecoveryError, "manual reconciliation"):
            self.ledger.plan_next("writer-r1", retry_blocked=True)

    def test_blocked_attempt_requires_explicit_new_attempt_decision(self) -> None:
        self.write_attempt(1)
        with self.assertRaisesRegex(AttemptRecoveryError, "explicit retry_blocked"):
            self.ledger.plan_next("writer-r1")

        plan = self.ledger.plan_next("writer-r1", retry_blocked=True)

        self.assertEqual("attempt-002", plan.attempt_id)
        self.assertEqual("attempt-001", plan.recovery_from)
        self.assertEqual(("thread-1",), plan.prior_backend_session_ids)

    def test_successful_attempt_cannot_be_repeated(self) -> None:
        self.write_attempt(1, outcome="draft-ready")
        with self.assertRaisesRegex(AttemptRecoveryError, "must not be repeated"):
            self.ledger.plan_next("writer-r1", retry_blocked=True)

    def test_tampered_successful_output_makes_attempt_corrupt(self) -> None:
        _, output = self.write_attempt(1, outcome="draft-ready")
        output.write_text("tampered\n", encoding="utf-8")
        records = self.ledger.inspect("writer-r1")
        self.assertEqual("corrupt", records[0].state)
        self.assertIn("hash mismatch", records[0].reason)

    def test_reused_backend_session_id_makes_later_attempt_corrupt(self) -> None:
        self.write_attempt(1, backend_session_id="same-thread")
        self.write_attempt(2, backend_session_id="same-thread")
        records = self.ledger.inspect("writer-r1")
        self.assertEqual("blocked", records[0].state)
        self.assertEqual("corrupt", records[1].state)
        self.assertIn("fresh stage session", records[1].reason)

    def test_attempt_number_range_is_bounded(self) -> None:
        with self.assertRaises(AttemptRecoveryError):
            format_attempt_id(1000)


if __name__ == "__main__":
    unittest.main()
