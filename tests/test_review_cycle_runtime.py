from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.contracts import (
    ArtifactRef,
    ExpectedOutput,
    StageInputManifest,
    StageResult,
)
from test_case_agent.review_cycle.runtime import (
    StageArtifactStore,
    StageAttemptPaths,
    StageRuntimeError,
    artifact_ref,
    load_manifest,
    load_result,
    utc_timestamp,
)


class ReviewCycleRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.prompt = self.root / "work/review-cycles/demo/attempts/writer-r1/a1/prompt.md"
        self.instruction = self.root / "AGENTS.md"
        self.source = self.root / "fts/demo/source/main.xhtml"
        self.handoff = self.root / "fts/demo/work/handoff/scope.md"
        for path, content in (
            (self.prompt, "writer prompt\n"),
            (self.instruction, "instructions\n"),
            (self.source, "<html>source</html>\n"),
            (self.handoff, "# scope\n"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.output = self.prompt.parent / "outputs/draft.md"
        self.store = StageArtifactStore(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def manifest(self) -> StageInputManifest:
        return StageInputManifest.create(
            cycle_id="demo",
            stage_id="writer-r1",
            attempt_id="a1",
            session_id="session-writer-r1-a1",
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
                    path="work/review-cycles/demo/attempts/writer-r1/a1/outputs/draft.md",
                    kind="test-case-draft",
                    producer="stage",
                )
            ],
            allowed_write_roots=["work/review-cycles/demo/attempts/writer-r1/a1/outputs"],
            forbidden_write_roots=["fts/demo/test-cases"],
        )

    def test_store_writes_and_loads_immutable_manifest(self) -> None:
        manifest = self.manifest()
        paths = StageAttemptPaths.from_manifest(self.root, manifest)
        paths.attempt_root.mkdir(parents=True, exist_ok=True)

        written = self.store.write_manifest(paths, manifest)

        self.assertEqual(manifest, load_manifest(written))
        with self.assertRaisesRegex(StageRuntimeError, "immutable"):
            self.store.write_manifest(paths, manifest)

    def test_prepare_new_attempt_rejects_existing_root(self) -> None:
        manifest = self.manifest()
        self.assertTrue(self.prompt.parent.exists())
        with self.assertRaisesRegex(StageRuntimeError, "recovery must be explicit"):
            self.store.prepare_new_attempt(manifest)

    def test_manifest_input_hash_mismatch_is_blocking(self) -> None:
        manifest = self.manifest()
        self.source.write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(StageRuntimeError, "hash mismatch"):
            self.store.verify_manifest_inputs(manifest)

    def test_collect_outputs_hashes_only_declared_files(self) -> None:
        manifest = self.manifest()
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text("draft\n", encoding="utf-8")

        references = self.store.collect_declared_outputs(manifest)

        self.assertEqual(1, len(references))
        self.assertEqual("test-case-draft", references[0].kind)
        self.assertEqual(artifact_ref(self.output, self.root, kind="test-case-draft"), references[0])

    def test_missing_required_output_is_blocking(self) -> None:
        with self.assertRaisesRegex(StageRuntimeError, "required stage output is missing"):
            self.store.collect_declared_outputs(self.manifest())

    def test_result_round_trip_rechecks_artifact_hash(self) -> None:
        manifest = self.manifest()
        paths = StageAttemptPaths.from_manifest(self.root, manifest)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text("draft\n", encoding="utf-8")
        output_ref = artifact_ref(self.output, self.root, kind="test-case-draft")
        now = utc_timestamp()
        result = StageResult(
            contract_version=2,
            cycle_id=manifest.cycle_id,
            stage_id=manifest.stage_id,
            attempt_id=manifest.attempt_id,
            session_id=manifest.session_id,
            backend_session_id="backend-session-1",
            role=manifest.role,
            scenario=manifest.scenario,
            input_digest=manifest.input_digest,
            status="completed",
            outcome="draft-ready",
            output_artifacts=(output_ref,),
            started_at=now,
            finished_at=now,
            duration_ms=1,
            exit_code=0,
            timed_out=False,
            blocking_reasons=(),
        )

        written = self.store.write_result(paths, manifest, result)

        self.assertEqual(result, load_result(written))
        self.output.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(StageRuntimeError, "hash mismatch"):
            self.store.verify_artifact(output_ref)

    def test_artifact_outside_repository_is_rejected(self) -> None:
        outside = self.root.parent / "outside-stage-artifact.txt"
        outside.write_text("outside\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(StageRuntimeError, "outside repository"):
                artifact_ref(outside, self.root, kind="source")
        finally:
            outside.unlink(missing_ok=True)

    def test_artifact_reference_validation_is_preserved(self) -> None:
        invalid = ArtifactRef(path="../escape", sha256="0" * 64, kind="source")
        with self.assertRaises(Exception):
            self.store.verify_artifact(invalid)


if __name__ == "__main__":
    unittest.main()
