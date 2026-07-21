from __future__ import annotations

import hashlib
import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import run_standard_scope_bridge
from scripts.run_standard_scope_bridge import main
from test_case_agent.bounded_scope_boundary import recompute_bounded_context_sha256
from test_case_agent.lean_production import load_run, start_run
from test_case_agent.review_cycle.source_assertions import (
    MANIFEST_VERSION,
    RegisteredArtifact,
    RegisteredSource,
    SourceAssertion,
    SourceAssertionManifest,
    SourceRow,
)
from test_case_agent.semantic_design_bridge import prepared_context_sha256


def _option(arguments: list[str], name: str) -> Path:
    return Path(arguments[arguments.index(name) + 1])


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _source_manifest() -> SourceAssertionManifest:
    source_path = "source/main.xhtml"
    source_text = "Bound source context"
    row = SourceRow(
        source_row_id="SRC-001",
        source_path=source_path,
        source_locator="/*/*[1]",
        bounded_source_text=source_text,
        source_context_class="ancestor-and-section-preamble",
        candidate_id=f"SRC-CAND-{'1' * 24}",
    )
    assertion = SourceAssertion(
        assertion_id="ASSERT-001",
        source_path=source_path,
        source_context_class="ancestor-and-section-preamble",
        locator="/*/*[1]",
        exact_source_text=source_text,
        canonical_statement="Structural context is not executable.",
        polarity="neutral",
        semantic_disposition="not-applicable",
        execution_readiness="not-applicable",
        execution_readiness_rationale="none_required",
        risk="low",
        condition_clauses=(),
        action_clauses=(),
        oracle_clauses=(),
        requirement_codes=(),
        requirement_code_bindings=(),
        clause_evidence_bindings=(),
        source_row_id="SRC-001",
        atom_id="ATOM-001",
        obligation_ids=(),
        execution_dependency_gap_ids=(),
        primary_gap_id=None,
        disposition_rationale="Structural context only.",
    )
    return SourceAssertionManifest(
        version=MANIFEST_VERSION,
        scope_slug="demo",
        source_row_extraction_spec_digest="1" * 64,
        source_row_baseline_digest="2" * 64,
        source_row_candidate_count=1,
        coverage_gaps_artifact=RegisteredArtifact(
            path="coverage-gaps.md", sha256="3" * 64
        ),
        sources=(RegisteredSource(path=source_path, sha256="4" * 64),),
        source_rows=(row,),
        assertions=(assertion,),
    )


class StandardScopeBridgeRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.context = self.root / "context.json"
        self.image = self.root / "mockup.png"
        self.image.write_bytes(b"offline-mockup")
        self.xhtml = self.root / "main.xhtml"
        self.xhtml.write_text("<html>bounded source</html>", encoding="utf-8")
        self.clarification = self.root / "approved-clarification.md"
        self.clarification.write_text("approved clarification", encoding="utf-8")
        self.extraction_spec = self.root / "source-row-extraction-spec.json"
        _write_json(self.extraction_spec, {"version": 1})
        self.row_baseline = self.root / "source-row-baseline.json"
        _write_json(self.row_baseline, {"version": 1})
        _write_json(
            self.context,
            {
                "version": 1,
                "ft_slug": "Demo",
                "source_rows": [{"source_row_id": "SRC-001"}],
                "sources": [
                    {
                        "path": self.xhtml.relative_to(self.root).as_posix(),
                        "manifest_binding": "assertion-source",
                    },
                    {
                        "path": self.clarification.relative_to(self.root).as_posix(),
                        "manifest_binding": "approved-clarification",
                    },
                ],
                "source_row_extraction_spec": self.extraction_spec.relative_to(
                    self.root
                ).as_posix(),
                "source_row_baseline": self.row_baseline.relative_to(
                    self.root
                ).as_posix(),
                "mockups": [
                    {
                        "path": self.image.relative_to(self.root).as_posix(),
                    }
                ],
            },
        )
        prepared = json.loads(self.context.read_text(encoding="utf-8"))
        prepared["source_cache"] = {
            "component_digests": {
                "bounded_context_sha256": recompute_bounded_context_sha256(
                    prepared
                )
            }
        }
        _write_json(self.context, prepared)
        self.context_digest = prepared_context_sha256(
            prepared
        )
        self.runtime = self.root / "runtime"
        self.handoff = self.root / "fts" / "Demo" / "work" / "stage-handoffs" / "01-demo"
        self.timer = self.root / "timer.json"
        start_run(
            self.timer,
            ft_slug="Demo",
            scope_slug="demo",
            profile="standard-production",
            measurement_mode="observational",
        )
        self.calls: list[str] = []

    def arguments(self) -> list[str]:
        return [
            "--repo-root", str(self.root),
            "--context", str(self.context),
            "--runtime-dir", str(self.runtime),
            "--handoff-dir", str(self.handoff),
            "--timer", str(self.timer),
        ]

    def run_main(self, *, boundary=None, semantic=None, materializer=None) -> int:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return main(
                self.arguments(),
                boundary_runner=boundary or self.boundary,
                semantic_runner=semantic or self.semantic,
                materializer_runner=materializer or self.materializer,
            )

    def boundary(self, arguments) -> int:
        args = list(arguments)
        self.calls.append("boundary")
        self.assertIn("--contract-version", args)
        self.assertEqual("2", args[args.index("--contract-version") + 1])
        self.assertEqual(
            "standard-production",
            args[args.index("--scope-execution-profile") + 1],
        )
        self.assertEqual(
            "observational", args[args.index("--measurement-mode") + 1]
        )
        self.assertEqual(
            self.root.resolve(), _option(args, "--repo-root").resolve()
        )
        self.assertNotIn("--timeout-seconds", args)
        self.assertEqual(self.image.resolve(), _option(args, "--image").resolve())
        _write_json(
            _option(args, "--decision-output"),
            {"version": 2, "status": "ready"},
        )
        _write_json(
            _option(args, "--summary-output"),
            {
                "status": "completed",
                "decision": "ready",
                "model_invoked": True,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 10,
                    "total_tokens": 110,
                },
                "lifecycle": {
                    "runner_attempt_count": 1,
                    "runner_retry_count": 0,
                },
            },
        )
        return 0

    def semantic(self, arguments) -> int:
        args = list(arguments)
        self.calls.append("semantic")
        self.assertEqual(
            (
                self.runtime
                / "scope-analysis"
                / "scope-boundary-decision.json"
            ).resolve(),
            _option(args, "--scope-boundary-decision").resolve(),
        )
        self.assertEqual(
            "observational", args[args.index("--measurement-mode") + 1]
        )
        self.assertEqual(
            self.root.resolve(), _option(args, "--repo-root").resolve()
        )
        self.assertNotIn("--timeout-seconds", args)
        self.assertEqual(self.image.resolve(), _option(args, "--image").resolve())
        _write_json(
            _option(args, "--decision-output"),
            {"version": 3, "status": "ready"},
        )
        _write_json(
            _option(args, "--summary-output"),
            {
                "status": "completed",
                "decision": "ready",
                "model_invoked": True,
                "assertion_count": 1,
                "obligation_count": 1,
                "usage": {
                    "input_tokens": 200,
                    "output_tokens": 30,
                    "total_tokens": 230,
                },
                "lifecycle": {
                    "runner_attempt_count": 1,
                    "runner_retry_count": 0,
                },
            },
        )
        return 0

    def materializer(self, arguments) -> int:
        args = list(arguments)
        self.calls.append("materializer")
        handoff = _option(args, "--handoff-dir")
        handoff.mkdir(parents=True)
        (handoff / "workflow-state.yaml").write_text(
            "stage_status: ready-for-next-stage\n", encoding="utf-8"
        )
        boundary_artifact = handoff / "scope-boundary-decision.json"
        semantic_artifact = handoff / "semantic-design.json"
        boundary_artifact.write_bytes(
            _option(args, "--scope-boundary-decision").read_bytes()
        )
        semantic_artifact.write_bytes(
            _option(args, "--semantic-design").read_bytes()
        )
        manifest = _source_manifest()
        _write_json(handoff / "source-assertions.json", manifest.to_dict())
        manifest_digest = manifest.digest
        owner_token = args[args.index("--publication-owner-token") + 1]
        publication = {
            "status": "atomic-renamed",
            "final_handoff": "fts/Demo/work/stage-handoffs/01-demo",
        }
        readiness = {
            "status": "passed",
            "canonical_preflight": "source-reviewer.prepare_evidence_set",
            "published_manifest_digest": manifest_digest,
        }
        _write_json(
            handoff / "semantic-design-bridge-receipt.json",
            {
                "version": 1,
                "contract": "scope-v2-to-semantic-design-v1",
                "status": "verified",
                "materialization_status": "materialized",
                "prepared_context_sha256": self.context_digest,
                "publication_ownership_contract_version": 1,
                "publication_owner_token": owner_token,
                "source_assertion_manifest_digest": manifest_digest,
                "scope_boundary_artifact_sha256": hashlib.sha256(
                    boundary_artifact.read_bytes()
                ).hexdigest(),
                "semantic_design_artifact_sha256": hashlib.sha256(
                    semantic_artifact.read_bytes()
                ).hexdigest(),
                "publication": publication,
                "downstream_evidence_readiness": readiness,
            },
        )
        _write_json(
            _option(args, "--summary-output"),
            {
                "status": "completed",
                "handoff_dir": str(handoff),
                "bridge_receipt": {"status": "verified"},
                "publication": publication,
                "downstream_evidence_readiness": readiness,
            },
        )
        return 0

    def test_runs_each_standard_stage_once_and_records_separate_metrics(self) -> None:
        code = self.run_main()

        self.assertEqual(0, code)
        self.assertEqual(["boundary", "semantic", "materializer"], self.calls)
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("completed", summary["status"])
        self.assertEqual(2, summary["attempt_count"])
        self.assertEqual(2, summary["model_stage_count"])
        self.assertEqual(0, summary["retry_count"])
        self.assertEqual(0, summary["fallback_count"])
        self.assertTrue(self.handoff.is_dir())
        receipt = json.loads(
            (self.handoff / "semantic-design-bridge-receipt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            summary["publication_owner_token"],
            receipt["publication_owner_token"],
        )

        timing = load_run(self.timer)
        self.assertEqual(
            ["scope-analysis", "semantic-design", "scope-materialization"],
            [item["phase"] for item in timing["phases"]],
        )
        self.assertTrue(all(item["status"] == "completed" for item in timing["phases"]))
        self.assertEqual(
            110,
            timing["phases"][0]["metrics"]["usage"]["total_tokens"],
        )
        self.assertEqual(
            230,
            timing["phases"][1]["metrics"]["usage"]["total_tokens"],
        )
        self.assertEqual(
            4,
            timing["phases"][1]["metrics"]["input_artifacts"]["file_count"],
            "semantic timing must include the approved clarification actually read",
        )
        self.assertEqual(
            8,
            timing["phases"][2]["metrics"]["input_artifacts"]["file_count"],
            "materialization timing must include sources/spec/baseline/mockup files",
        )

    def test_blocked_semantic_design_stops_before_materialization(self) -> None:
        def blocked(arguments) -> int:
            args = list(arguments)
            self.calls.append("semantic")
            _write_json(
                _option(args, "--decision-output"),
                {"version": 3, "status": "blocked"},
            )
            _write_json(
                _option(args, "--summary-output"),
                {
                    "status": "completed",
                    "decision": "blocked",
                    "model_invoked": True,
                    "usage": {"total_tokens": 12},
                    "lifecycle": {
                        "runner_attempt_count": 1,
                        "runner_retry_count": 0,
                    },
                },
            )
            return 0

        code = self.run_main(semantic=blocked)

        self.assertEqual(3, code)
        self.assertEqual(["boundary", "semantic"], self.calls)
        self.assertFalse(self.handoff.exists())
        timing = load_run(self.timer)
        self.assertEqual("blocked", timing["phases"][-1]["status"])
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("blocked-input", summary["status"])
        self.assertEqual("semantic-design", summary["stopped_after"])
        self.assertEqual(2, summary["attempt_count"])
        self.assertEqual(0, summary["retry_count"])

    def test_materializer_failure_does_not_claim_published_handoff(self) -> None:
        def failed(arguments) -> int:
            args = list(arguments)
            self.calls.append("materializer")
            _write_json(
                _option(args, "--summary-output"),
                {"status": "failed", "error": "transaction rejected"},
            )
            return 2

        code = self.run_main(materializer=failed)

        self.assertEqual(2, code)
        self.assertEqual(["boundary", "semantic", "materializer"], self.calls)
        self.assertFalse(self.handoff.exists())
        timing = load_run(self.timer)
        self.assertEqual("terminal-failed", timing["phases"][-1]["status"])

    def test_published_handoff_is_authoritative_when_materializer_summary_is_missing(
        self,
    ) -> None:
        def published_without_summary(arguments) -> int:
            args = list(arguments)
            code = self.materializer(args)
            _option(args, "--summary-output").unlink()
            return code

        code = self.run_main(materializer=published_without_summary)

        self.assertEqual(0, code)
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(
            summary["scope_materialization"][
                "summary_recovered_from_published_handoff"
            ]
        )

    def test_missing_canonical_preflight_receipt_fails_closed(self) -> None:
        def missing_preflight(arguments) -> int:
            args = list(arguments)
            code = self.materializer(args)
            receipt_path = (
                _option(args, "--handoff-dir")
                / "semantic-design-bridge-receipt.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt.pop("downstream_evidence_readiness")
            _write_json(receipt_path, receipt)
            return code

        code = self.run_main(materializer=missing_preflight)

        self.assertEqual(2, code)

    def test_published_receipt_must_match_current_prepared_context(self) -> None:
        def wrong_digest(arguments) -> int:
            code = self.materializer(arguments)
            receipt_path = (
                _option(list(arguments), "--handoff-dir")
                / "semantic-design-bridge-receipt.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["prepared_context_sha256"] = "0" * 64
            _write_json(receipt_path, receipt)
            return code

        code = self.run_main(materializer=wrong_digest)

        self.assertEqual(2, code)
        self.assertTrue(self.handoff.is_dir())

    def test_published_receipt_identity_must_be_verified_materialized_v1(
        self,
    ) -> None:
        def invalid_identity(arguments) -> int:
            code = self.materializer(arguments)
            receipt_path = (
                _option(list(arguments), "--handoff-dir")
                / "semantic-design-bridge-receipt.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["status"] = "ready"
            _write_json(receipt_path, receipt)
            return code

        code = self.run_main(materializer=invalid_identity)

        self.assertEqual(2, code)

    def test_legacy_receipt_without_ownership_binding_is_rejected(self) -> None:
        def legacy_receipt(arguments) -> int:
            code = self.materializer(arguments)
            receipt_path = (
                _option(list(arguments), "--handoff-dir")
                / "semantic-design-bridge-receipt.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt.pop("publication_ownership_contract_version")
            receipt.pop("publication_owner_token")
            _write_json(receipt_path, receipt)
            return code

        code = self.run_main(materializer=legacy_receipt)

        self.assertEqual(2, code)

    def test_foreign_concurrent_handoff_is_not_recovered(self) -> None:
        def foreign_publication(arguments) -> int:
            self.materializer(arguments)
            receipt_path = (
                _option(list(arguments), "--handoff-dir")
                / "semantic-design-bridge-receipt.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["publication_owner_token"] = (
                "22222222-2222-4222-8222-222222222222"
            )
            _write_json(receipt_path, receipt)
            return 2

        code = self.run_main(materializer=foreign_publication)

        self.assertEqual(2, code)
        self.assertTrue(self.handoff.is_dir())

    def test_published_artifact_hash_mismatch_fails_closed(self) -> None:
        def tampered_artifact(arguments) -> int:
            code = self.materializer(arguments)
            artifact = (
                _option(list(arguments), "--handoff-dir")
                / "semantic-design.json"
            )
            artifact.write_text('{"tampered":true}\n', encoding="utf-8")
            return code

        code = self.run_main(materializer=tampered_artifact)

        self.assertEqual(2, code)

    def test_published_manifest_readiness_binding_mismatch_fails_closed(
        self,
    ) -> None:
        def wrong_manifest_digest(arguments) -> int:
            code = self.materializer(arguments)
            receipt_path = (
                _option(list(arguments), "--handoff-dir")
                / "semantic-design-bridge-receipt.json"
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["downstream_evidence_readiness"][
                "published_manifest_digest"
            ] = "b" * 64
            _write_json(receipt_path, receipt)
            return code

        code = self.run_main(materializer=wrong_manifest_digest)

        self.assertEqual(2, code)

    def test_published_manifest_content_tamper_fails_closed(self) -> None:
        def tampered_manifest(arguments) -> int:
            code = self.materializer(arguments)
            manifest_path = (
                _option(list(arguments), "--handoff-dir")
                / "source-assertions.json"
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["scope_slug"] = "tampered"
            _write_json(manifest_path, payload)
            return code

        code = self.run_main(materializer=tampered_manifest)

        self.assertEqual(2, code)

    def test_terminal_reporting_failure_does_not_invalidate_published_handoff(
        self,
    ) -> None:
        with patch.object(
            run_standard_scope_bridge,
            "_write_json_atomic",
            side_effect=OSError("terminal summary unavailable"),
        ):
            code = self.run_main()

        self.assertEqual(0, code)
        self.assertTrue(self.handoff.is_dir())

    def test_path_error_is_normalized_to_terminal_json(self) -> None:
        arguments = self.arguments()
        arguments[arguments.index("--context") + 1] = str(
            self.root.parent / "outside-context.json"
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(
                arguments,
                boundary_runner=self.boundary,
                semantic_runner=self.semantic,
                materializer_runner=self.materializer,
            )

        self.assertEqual(2, code)
        payload = json.loads(stderr.getvalue())
        self.assertEqual("terminal-failed", payload["status"])
        self.assertEqual([], self.calls)

    def test_lifecycle_failure_retains_measured_usage_and_attempts(self) -> None:
        def invalid_lifecycle(arguments) -> int:
            args = list(arguments)
            self.calls.append("semantic")
            _write_json(
                _option(args, "--decision-output"),
                {"version": 3, "status": "ready"},
            )
            _write_json(
                _option(args, "--summary-output"),
                {
                    "status": "completed",
                    "decision": "ready",
                    "model_invoked": True,
                    "usage": {"total_tokens": 345},
                    "lifecycle": {
                        "runner_attempt_count": 2,
                        "runner_retry_count": 1,
                    },
                },
            )
            return 0

        code = self.run_main(semantic=invalid_lifecycle)

        self.assertEqual(2, code)
        self.assertEqual(["boundary", "semantic"], self.calls)
        timing = load_run(self.timer)
        failed = timing["phases"][-1]
        self.assertEqual("terminal-failed", failed["status"])
        self.assertEqual(345, failed["metrics"]["usage"]["total_tokens"])
        self.assertEqual(
            2,
            failed["metrics"]["lifecycle"]["runner_attempt_count"],
        )
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(3, summary["attempt_count"])
        self.assertEqual(1, summary["retry_count"])
        self.assertEqual(2, summary["model_stage_count"])
        self.assertEqual(2, summary["semantic_design"]["lifecycle"]["runner_attempt_count"])

    def test_runner_exception_after_summary_retains_attempt_evidence(self) -> None:
        def failed_after_model_summary(arguments) -> int:
            args = list(arguments)
            self.calls.append("boundary")
            _write_json(
                _option(args, "--summary-output"),
                {
                    "status": "failed",
                    "decision": "blocked",
                    "model_invoked": True,
                    "usage": {"total_tokens": 55},
                    "lifecycle": {
                        "runner_attempt_count": 1,
                        "runner_retry_count": 0,
                    },
                },
            )
            raise RuntimeError("runner failed after persisting lifecycle")

        code = self.run_main(boundary=failed_after_model_summary)

        self.assertEqual(2, code)
        self.assertEqual(["boundary"], self.calls)
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("terminal-failed", summary["status"])
        self.assertEqual("RuntimeError", summary["error_type"])
        self.assertEqual(1, summary["attempt_count"])
        self.assertEqual(0, summary["retry_count"])
        self.assertEqual(1, summary["model_stage_count"])
        self.assertEqual(
            1,
            summary["scope_analysis"]["lifecycle"]["runner_attempt_count"],
        )

    def test_runner_exception_without_summary_marks_attempts_unknown(self) -> None:
        def failed_without_summary(_arguments) -> int:
            self.calls.append("boundary")
            raise RuntimeError("runner failed without lifecycle evidence")

        code = self.run_main(boundary=failed_without_summary)

        self.assertEqual(2, code)
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIsNone(summary["attempt_count"])
        self.assertIsNone(summary["retry_count"])

    def test_nonzero_model_result_still_enforces_lifecycle_contract(self) -> None:
        def retried_blocked(arguments) -> int:
            args = list(arguments)
            self.calls.append("boundary")
            _write_json(
                _option(args, "--summary-output"),
                {
                    "status": "completed",
                    "decision": "blocked",
                    "model_invoked": True,
                    "usage": {"total_tokens": 77},
                    "lifecycle": {
                        "runner_attempt_count": 2,
                        "runner_retry_count": 1,
                    },
                },
            )
            return 3

        code = self.run_main(boundary=retried_blocked)

        self.assertEqual(2, code)
        self.assertEqual(["boundary"], self.calls)
        self.assertFalse(self.handoff.exists())
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(2, summary["attempt_count"])
        self.assertEqual(1, summary["retry_count"])
        self.assertEqual(1, summary["model_stage_count"])
        self.assertEqual(
            2,
            summary["scope_analysis"]["lifecycle"]["runner_attempt_count"],
        )

    def test_premodel_blocked_result_accepts_zero_attempts(self) -> None:
        def premodel_blocked(arguments) -> int:
            args = list(arguments)
            self.calls.append("boundary")
            _write_json(
                _option(args, "--summary-output"),
                {
                    "status": "completed",
                    "decision": "blocked",
                    "model_invoked": False,
                    "lifecycle": {
                        "runner_attempt_count": 0,
                        "runner_retry_count": 0,
                    },
                },
            )
            return 3

        code = self.run_main(boundary=premodel_blocked)

        self.assertEqual(3, code)
        summary = json.loads(
            (self.runtime / "standard-scope-bridge-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(0, summary["attempt_count"])
        self.assertEqual(0, summary["retry_count"])
        self.assertEqual(0, summary["model_stage_count"])

    def test_invalid_ft_slug_creates_no_runtime_or_handoff_artifacts(self) -> None:
        payload = json.loads(self.context.read_text(encoding="utf-8"))
        payload["ft_slug"] = "C:"
        _write_json(self.context, payload)

        code = self.run_main()

        self.assertEqual(2, code)
        self.assertEqual([], self.calls)
        self.assertFalse(self.runtime.exists())
        self.assertFalse(self.handoff.exists())

    def test_nonempty_runtime_is_rejected_before_any_model_call(self) -> None:
        self.runtime.mkdir(parents=True)
        (self.runtime / "stale.txt").write_text("stale", encoding="utf-8")

        code = self.run_main()

        self.assertEqual(2, code)
        self.assertEqual([], self.calls)
        self.assertFalse(self.handoff.exists())


if __name__ == "__main__":
    unittest.main()
