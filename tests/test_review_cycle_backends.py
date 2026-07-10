from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from test_case_agent.review_cycle.backends import FreshThreadSdkBackend, start_fresh_sdk_thread
from test_case_agent.review_cycle.contracts import ExpectedOutput, StageInputManifest
from test_case_agent.review_cycle.runtime import StageRuntimeError, artifact_ref


@dataclass
class FakeTurn:
    id: str = "turn-1"
    status: str = "completed"
    final_response: str = "done"
    duration_ms: int = 7


class FakeThread:
    def __init__(self, thread_id: str):
        self.id = thread_id


class FakeClient:
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.start_calls = []
        self.closed = False

    def thread_start(self, **kwargs):
        self.start_calls.append(kwargs)
        return FakeThread(self.thread_id)

    def close(self):
        self.closed = True


class ReviewCycleBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.prompt = self.root / "work/review-cycles/demo/attempts/writer-r1/a1/prompt.md"
        self.instruction = self.root / "AGENTS.md"
        self.source = self.root / "fts/demo/source/main.xhtml"
        self.handoff = self.root / "fts/demo/work/handoff/scope.md"
        for path in (self.prompt, self.instruction, self.source, self.handoff):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(path.name + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def manifest(self, *, session_id: str = "logical-session-1") -> StageInputManifest:
        return StageInputManifest.create(
            cycle_id="demo",
            stage_id="writer-r1",
            attempt_id="a1",
            session_id=session_id,
            role="writer",
            scenario="writer.session_initial_draft",
            semantic_round=0,
            sandbox_policy="workspace_write",
            timeout_seconds=30,
            attempt_root="work/review-cycles/demo/attempts/writer-r1/a1",
            canonical_test_cases="fts/demo/test-cases/1-demo.md",
            prompt_artifact=artifact_ref(self.prompt, self.root, kind="prompt"),
            instruction_artifacts=[artifact_ref(self.instruction, self.root, kind="instruction")],
            source_artifacts=[artifact_ref(self.source, self.root, kind="source")],
            handoff_artifacts=[artifact_ref(self.handoff, self.root, kind="handoff")],
            expected_outputs=[
                ExpectedOutput(
                    path="work/review-cycles/demo/attempts/writer-r1/a1/output.md",
                    kind="draft",
                    producer="stage",
                )
            ],
            allowed_write_roots=["work/review-cycles/demo/attempts/writer-r1/a1"],
            forbidden_write_roots=["fts/demo/test-cases"],
        )

    def test_helper_has_no_resume_or_previous_thread_inputs(self) -> None:
        client = FakeClient("thread-1")
        thread = start_fresh_sdk_thread(
            client,
            cwd=str(self.root),
            sandbox="workspace-write",
            approval_mode="never",
            model=None,
        )
        self.assertEqual("thread-1", thread.id)
        self.assertEqual(1, len(client.start_calls))
        self.assertNotIn("previous_thread_id", client.start_calls[0])
        self.assertNotIn("resume", client.start_calls[0])

    def test_backend_creates_a_new_thread_for_each_stage(self) -> None:
        created = [FakeClient("thread-1"), FakeClient("thread-2")]
        clients = list(created)
        backend = FreshThreadSdkBackend(
            client_factory=lambda: clients.pop(0),
            turn_executor=lambda thread, prompt, manifest, cwd: FakeTurn(id=f"turn-{thread.id}"),
        )
        first = backend.execute(self.manifest(), prompt="first", cwd=self.root)
        second = backend.execute(
            self.manifest(session_id="logical-session-2"), prompt="second", cwd=self.root
        )
        self.assertEqual("thread-1", first.backend_session_id)
        self.assertEqual("thread-2", second.backend_session_id)
        self.assertTrue(all(client.closed for client in created))

    def test_duplicate_thread_id_is_returned_as_failed_evidence(self) -> None:
        clients = [FakeClient("thread-1"), FakeClient("thread-1")]
        backend = FreshThreadSdkBackend(
            client_factory=lambda: clients.pop(0),
            turn_executor=lambda thread, prompt, manifest, cwd: FakeTurn(),
        )
        backend.execute(self.manifest(), prompt="first", cwd=self.root)
        duplicate = backend.execute(
            self.manifest(session_id="logical-session-2"), prompt="second", cwd=self.root
        )
        self.assertIn("fresh stage session", duplicate.stderr)
        self.assertFalse(duplicate.launch_error)

    def test_missing_thread_id_is_launch_error(self) -> None:
        backend = FreshThreadSdkBackend(
            client_factory=lambda: FakeClient(""),
            turn_executor=lambda thread, prompt, manifest, cwd: FakeTurn(),
        )
        result = backend.execute(self.manifest(), prompt="stage", cwd=self.root)
        self.assertTrue(result.launch_error)
        self.assertIn("no thread id", result.stderr)

    def test_direct_helper_rejects_missing_thread_id(self) -> None:
        with self.assertRaisesRegex(StageRuntimeError, "no thread id"):
            start_fresh_sdk_thread(
                FakeClient(""),
                cwd=str(self.root),
                sandbox="workspace-write",
                approval_mode="never",
                model=None,
            )


if __name__ == "__main__":
    unittest.main()
