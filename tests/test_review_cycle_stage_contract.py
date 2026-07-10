from __future__ import annotations

import unittest
from pathlib import Path

from test_case_agent.review_cycle import (
    CONTRACT_VERSION,
    ArtifactRef,
    ContractValidationError,
    ExpectedOutput,
    StageInputManifest,
    StageResult,
    ensure_new_session_id,
    resolve_transition,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
ROOT_DIR = Path(__file__).resolve().parents[1]


class ReviewCycleStageContractTests(unittest.TestCase):
    def artifact(self, path: str, kind: str = "source", digest: str = HASH_A) -> ArtifactRef:
        return ArtifactRef(path=path, sha256=digest, kind=kind)

    def writer_manifest(self) -> StageInputManifest:
        attempt_root = "fts/demo/work/review-cycles/scope/attempts/writer-r1/attempt-001"
        return StageInputManifest.create(
            cycle_id="cycle-001",
            stage_id="writer-r1",
            attempt_id="attempt-001",
            session_id="session-writer-001",
            role="writer",
            scenario="writer.session_initial_draft",
            semantic_round=0,
            sandbox_policy="workspace_write",
            timeout_seconds=3600,
            attempt_root=attempt_root,
            canonical_test_cases="fts/demo/test-cases/1-scope.md",
            prompt_artifact=self.artifact(f"{attempt_root}/stage-input.md", "prompt", HASH_B),
            instruction_artifacts=[
                self.artifact("references/agent/writer-runtime-contract.md", "instruction")
            ],
            source_artifacts=[self.artifact("fts/demo/source/main.xhtml")],
            handoff_artifacts=[
                self.artifact("fts/demo/work/stage-handoffs/01-scope/scope-contract.md", "handoff")
            ],
            expected_outputs=[
                ExpectedOutput(
                    path=f"{attempt_root}/writer-draft.md",
                    kind="writer-draft",
                    producer="stage",
                ),
                ExpectedOutput(
                    path=f"{attempt_root}/stage-status.json",
                    kind="stage-status",
                    producer="runner",
                ),
            ],
            allowed_write_roots=[attempt_root],
            forbidden_write_roots=["fts/demo/test-cases"],
        )

    def reviewer_manifest(self) -> StageInputManifest:
        attempt_root = "fts/demo/work/review-cycles/scope/attempts/reviewer-r1/attempt-001"
        return StageInputManifest.create(
            cycle_id="cycle-001",
            stage_id="reviewer-r1",
            attempt_id="attempt-001",
            session_id="session-reviewer-001",
            role="reviewer",
            scenario="reviewer.semantic_traceability_test_design",
            semantic_round=1,
            sandbox_policy="read_only",
            timeout_seconds=1800,
            attempt_root=attempt_root,
            canonical_test_cases="fts/demo/test-cases/1-scope.md",
            prompt_artifact=self.artifact(f"{attempt_root}/stage-input.md", "prompt", HASH_B),
            instruction_artifacts=[
                self.artifact("references/qa/test-design-review-rubric.md", "instruction")
            ],
            source_artifacts=[self.artifact("fts/demo/source/main.xhtml")],
            handoff_artifacts=[
                self.artifact(
                    "fts/demo/work/review-cycles/scope/outputs/writer-r1-draft.md",
                    "handoff",
                )
            ],
            expected_outputs=[
                ExpectedOutput(
                    path=f"{attempt_root}/reviewer-findings.md",
                    kind="reviewer-findings",
                    producer="runner",
                ),
                ExpectedOutput(
                    path=f"{attempt_root}/stage-status.json",
                    kind="stage-status",
                    producer="runner",
                ),
            ],
            allowed_write_roots=[],
            forbidden_write_roots=["fts/demo/test-cases"],
        )

    def writer_result(self, manifest: StageInputManifest) -> StageResult:
        return StageResult(
            contract_version=CONTRACT_VERSION,
            cycle_id=manifest.cycle_id,
            stage_id=manifest.stage_id,
            attempt_id=manifest.attempt_id,
            session_id=manifest.session_id,
            backend_session_id="backend-thread-writer-001",
            role=manifest.role,
            scenario=manifest.scenario,
            input_digest=manifest.input_digest,
            status="completed",
            outcome="draft-ready",
            output_artifacts=tuple(
                self.artifact(output.path, output.kind, HASH_C)
                for output in manifest.expected_outputs
            ),
            started_at="2026-07-10T08:00:00+00:00",
            finished_at="2026-07-10T08:01:00+00:00",
            duration_ms=60_000,
            exit_code=0,
            timed_out=False,
            blocking_reasons=(),
        )

    def test_manifest_round_trip_preserves_digest(self) -> None:
        manifest = self.writer_manifest()
        restored = StageInputManifest.from_dict(manifest.to_dict())
        self.assertEqual(manifest, restored)
        self.assertEqual(manifest.compute_digest(), manifest.input_digest)

    def test_canonical_reference_pins_v2_ownership_and_implementation(self) -> None:
        content = (
            ROOT_DIR / "references" / "agent" / "review-cycle-stage-contract-v2.md"
        ).read_text(encoding="utf-8")
        for token in (
            "contract_version: 2",
            "must not edit runner-owned orchestration state",
            "must never return `signed-off`",
            "test_case_agent/review_cycle/contracts.py",
            "test_case_agent/review_cycle/transitions.py",
            "The exec prototype persists this contract",
        ):
            self.assertIn(token, content)

    def test_manifest_rejects_digest_mismatch(self) -> None:
        payload = self.writer_manifest().to_dict()
        payload["timeout_seconds"] = 1
        with self.assertRaisesRegex(ContractValidationError, "input_digest"):
            StageInputManifest.from_dict(payload)

    def test_manifest_rejects_unknown_previous_session_context(self) -> None:
        payload = self.writer_manifest().to_dict()
        payload["previous_thread_id"] = "thread-old"
        with self.assertRaisesRegex(ContractValidationError, "unknown=previous_thread_id"):
            StageInputManifest.from_dict(payload)

    def test_manifest_rejects_non_array_artifact_groups(self) -> None:
        payload = self.writer_manifest().to_dict()
        payload["source_artifacts"] = "fts/demo/source/main.xhtml"
        with self.assertRaisesRegex(ContractValidationError, "must be a JSON array"):
            StageInputManifest.from_dict(payload)

    def test_manifest_rejects_path_traversal(self) -> None:
        payload = self.writer_manifest().to_dict()
        payload["source_artifacts"][0]["path"] = "../source/main.xhtml"
        with self.assertRaisesRegex(ContractValidationError, "cannot traverse"):
            StageInputManifest.from_dict(payload)

    def test_reviewer_manifest_is_read_only_and_runner_persists_outputs(self) -> None:
        manifest = self.reviewer_manifest()
        self.assertEqual("read_only", manifest.sandbox_policy)
        self.assertEqual((), manifest.allowed_write_roots)
        self.assertTrue(all(output.producer == "runner" for output in manifest.expected_outputs))

    def test_reviewer_manifest_rejects_stage_produced_file(self) -> None:
        payload = self.reviewer_manifest().to_dict()
        payload["expected_outputs"][0]["producer"] = "stage"
        payload["input_digest"] = "0" * 64
        with self.assertRaisesRegex(ContractValidationError, "reviewer outputs"):
            StageInputManifest.from_dict(payload)

    def test_manifest_rejects_runner_output_outside_attempt_root(self) -> None:
        payload = self.writer_manifest().to_dict()
        payload["expected_outputs"][1]["path"] = "fts/demo/source/stage-status.json"
        payload["input_digest"] = "0" * 64
        with self.assertRaisesRegex(ContractValidationError, "under attempt_root"):
            StageInputManifest.from_dict(payload)

    def test_canonical_test_case_must_be_protected_by_forbidden_root(self) -> None:
        payload = self.writer_manifest().to_dict()
        payload["forbidden_write_roots"] = ["fts/another/test-cases"]
        payload["input_digest"] = "0" * 64
        with self.assertRaisesRegex(ContractValidationError, "canonical_test_cases"):
            StageInputManifest.from_dict(payload)

    def test_writer_result_matches_manifest_and_required_outputs(self) -> None:
        manifest = self.writer_manifest()
        self.writer_result(manifest).validate_against(manifest)

    def test_result_rejects_missing_required_output(self) -> None:
        manifest = self.writer_manifest()
        result = self.writer_result(manifest)
        incomplete = StageResult(**{**result.__dict__, "output_artifacts": result.output_artifacts[:1]})
        with self.assertRaisesRegex(ContractValidationError, "missing required"):
            incomplete.validate_against(manifest)

    def test_result_rejects_manifest_identity_mismatch(self) -> None:
        manifest = self.writer_manifest()
        result = self.writer_result(manifest)
        mismatched = StageResult(**{**result.__dict__, "attempt_id": "attempt-002"})
        with self.assertRaisesRegex(ContractValidationError, "attempt_id"):
            mismatched.validate_against(manifest)

    def test_result_rejects_undeclared_output(self) -> None:
        manifest = self.writer_manifest()
        result = self.writer_result(manifest)
        extra = self.artifact(
            "fts/demo/work/review-cycles/scope/attempts/writer-r1/attempt-001/extra.md",
            "extra",
        )
        expanded = StageResult(
            **{**result.__dict__, "output_artifacts": (*result.output_artifacts, extra)}
        )
        with self.assertRaisesRegex(ContractValidationError, "undeclared"):
            expanded.validate_against(manifest)

    def test_stage_result_cannot_claim_signed_off(self) -> None:
        result = self.writer_result(self.writer_manifest())
        invalid = StageResult(**{**result.__dict__, "role": "reviewer", "outcome": "signed-off"})
        with self.assertRaisesRegex(ContractValidationError, "not allowed"):
            invalid.validate()

    def test_stage_result_rejects_non_array_blocking_reasons(self) -> None:
        payload = self.writer_result(self.writer_manifest()).to_dict()
        payload["blocking_reasons"] = "not-an-array"
        with self.assertRaisesRegex(ContractValidationError, "must be a JSON array"):
            StageResult.from_dict(payload)

    def test_result_rejects_reused_backend_session(self) -> None:
        manifest = self.writer_manifest()
        result = self.writer_result(manifest)
        with self.assertRaisesRegex(ContractValidationError, "fresh stage session"):
            result.validate_against(
                manifest,
                prior_backend_session_ids=[result.backend_session_id],
            )

    def test_empty_backend_session_is_allowed_only_for_blocked_launch(self) -> None:
        manifest = self.writer_manifest()
        blocked = StageResult(
            contract_version=CONTRACT_VERSION,
            cycle_id=manifest.cycle_id,
            stage_id=manifest.stage_id,
            attempt_id=manifest.attempt_id,
            session_id=manifest.session_id,
            backend_session_id="",
            role=manifest.role,
            scenario=manifest.scenario,
            input_digest=manifest.input_digest,
            status="blocked",
            outcome="blocked",
            output_artifacts=(),
            started_at="2026-07-10T08:00:00+00:00",
            finished_at="2026-07-10T08:00:01+00:00",
            duration_ms=1_000,
            exit_code=None,
            timed_out=False,
            blocking_reasons=("process launch failed",),
        )
        blocked.validate_against(manifest)

    def test_session_identity_helper_rejects_empty_and_reused_ids(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "stable identifier"):
            ensure_new_session_id("", [])
        with self.assertRaisesRegex(ContractValidationError, "fresh stage session"):
            ensure_new_session_id("backend-session-001", ["backend-session-001"])

    def test_boolean_numeric_fields_are_rejected(self) -> None:
        payload = self.writer_manifest().to_dict()
        payload["timeout_seconds"] = True
        payload["input_digest"] = "0" * 64
        with self.assertRaisesRegex(ContractValidationError, "positive integer"):
            StageInputManifest.from_dict(payload)

    def test_malformed_scalar_types_raise_contract_errors(self) -> None:
        manifest_payload = self.writer_manifest().to_dict()
        manifest_payload["role"] = []
        with self.assertRaisesRegex(ContractValidationError, "role must be"):
            StageInputManifest.from_dict(manifest_payload)

        result_payload = self.writer_result(self.writer_manifest()).to_dict()
        result_payload["outcome"] = []
        with self.assertRaisesRegex(ContractValidationError, "outcome="):
            StageResult.from_dict(result_payload)

        with self.assertRaisesRegex(ContractValidationError, "outcome must be"):
            resolve_transition(
                current_stage_status="writer-draft-ready",
                scenario="reviewer.structure_preflight",
                outcome=[],
                semantic_round=0,
            )

    def test_initial_writer_transition_is_runner_owned(self) -> None:
        decision = resolve_transition(
            current_stage_status="scope-ready-for-writer",
            scenario="writer.session_initial_draft",
            outcome="draft-ready",
            semantic_round=0,
        )
        self.assertEqual("writer-draft-ready", decision.next_stage_status)
        self.assertFalse(decision.terminal)

    def test_structure_reviewer_transition_is_allowlisted(self) -> None:
        accepted = resolve_transition(
            current_stage_status="writer-draft-ready",
            scenario="reviewer.structure_preflight",
            outcome="accepted",
            semantic_round=0,
        )
        changes = resolve_transition(
            current_stage_status="writer-draft-ready",
            scenario="reviewer.structure_preflight",
            outcome="changes-required",
            semantic_round=0,
        )
        self.assertEqual("semantic-review-ready", accepted.next_stage_status)
        self.assertEqual("structure-preflight-blocked", changes.next_stage_status)

    def test_second_semantic_round_changes_stop_at_round_cap(self) -> None:
        decision = resolve_transition(
            current_stage_status="semantic-review-ready",
            scenario="reviewer.semantic_traceability_test_design",
            outcome="changes-required",
            semantic_round=2,
        )
        self.assertEqual("round-cap-reached", decision.next_stage_status)
        self.assertTrue(decision.terminal)

    def test_signed_off_transition_requires_runner_terminal_gates(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "terminal gates"):
            resolve_transition(
                current_stage_status="format-review-ready",
                scenario="reviewer.structure_format_final",
                outcome="accepted",
                semantic_round=2,
            )
        decision = resolve_transition(
            current_stage_status="format-review-ready",
            scenario="reviewer.structure_format_final",
            outcome="accepted",
            semantic_round=2,
            terminal_gates_passed=True,
        )
        self.assertEqual("signed-off", decision.next_stage_status)
        self.assertTrue(decision.terminal_gates_required)

    def test_stage_outcome_signed_off_is_never_accepted(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "cannot return signed-off"):
            resolve_transition(
                current_stage_status="format-review-ready",
                scenario="reviewer.structure_format_final",
                outcome="signed-off",
                semantic_round=2,
                terminal_gates_passed=True,
            )


if __name__ == "__main__":
    unittest.main()
