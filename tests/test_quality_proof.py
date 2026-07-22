from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.quality_proof import (
    QualityProofContractError,
    load_quality_proof_manifest,
    run_quality_proof,
    summarize_quality_proof_outcome,
    write_quality_proof_result,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "evals" / "quick-quality-proof" / "manifest.json"
SAMPLE_NODEID = (
    "tests/quality_proof_fixtures/quality_proof_sample.py::test_sample_check_passes"
)


class QuickQualityProofTests(unittest.TestCase):
    def _payload(self, *, nodeid: str = SAMPLE_NODEID) -> dict[str, object]:
        return {
            "schema_version": 2,
            "proof_id": "sample-quality-proof",
            "description": "Синтетическая проверка runner.",
            "target_duration_seconds": 10,
            "hard_duration_ceiling_seconds": 30,
            "checks": [
                {
                    "id": "QP-001",
                    "risk": "runner-contract",
                    "nodeid": nodeid,
                }
            ],
        }

    @staticmethod
    def _write(path: Path, payload: dict[str, object]) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_checked_in_manifest_is_closed_and_fast(self) -> None:
        manifest = load_quality_proof_manifest(
            DEFAULT_MANIFEST,
            repo_root=PROJECT_ROOT,
        )

        self.assertEqual("quick-qualification-quality-v1", manifest.proof_id)
        self.assertEqual(20.0, manifest.target_duration_seconds)
        self.assertEqual(30.0, manifest.hard_duration_ceiling_seconds)
        self.assertEqual(75, len(manifest.checks))
        self.assertEqual(75, len({item.check_id for item in manifest.checks}))
        self.assertEqual(75, len({item.nodeid for item in manifest.checks}))
        self.assertTrue(all(item.nodeid.startswith("tests/") for item in manifest.checks))
        self.assertTrue(all("AutoFin" not in item.nodeid for item in manifest.checks))
        self.assertIn("не доказывает качество live-моделей", manifest.description)
        self.assertIn("не является свидетельством live reviewer", manifest.description)
        self.assertIn("не публикует canonical", manifest.description)
        required_nodeids = {
            "tests/test_source_qualified_run.py::SourceQualifiedRunTests::test_offline_run_is_source_qualified_and_preserves_canonical",
            "tests/test_scope_registry.py::ScopeRegistryTests::test_selected_scope_resolves_without_unrelated_missing_files",
            "tests/test_scope_compiler.py::ScopeCompilerTests::test_manifest_rejects_wrong_bucket_role_and_current_hash",
            "tests/test_scope_registry.py::ScopeRegistryTests::test_tc_prefix_is_required_strict_and_digest_bound",
            "tests/test_iteration_contract.py::IterationContractTests::test_writer_cannot_inject_unregistered_fixture_or_action_identifier",
            "tests/test_coverage_graph.py::CoverageGraphTests::test_authoritative_validator_covers_io_integrity_rules",
            "tests/test_immutable_iteration.py::ImmutableIterationTests::test_invalid_token_receipts_fail_closed",
            "tests/test_immutable_iteration.py::ImmutableIterationTests::test_deterministic_suite_skips_writer_and_calls_reviewer_once",
            "tests/test_promotion_adapter.py::PromotionAdapterTests::test_builds_and_reuses_minimal_eligibility_basis_without_publication",
            "tests/test_coverage_contract.py::CoverageContractTests::test_rejects_forged_obligation_semantic_fields",
            "tests/test_iteration_contract.py::IterationContractTests::test_writer_merge_revalidates_context_against_graph",
            "tests/test_test_design.py::TestDesignTests::test_design_context_cannot_inject_unregistered_ui_behavior",
            "tests/test_source_qualified_run.py::SourceQualifiedRunTests::test_presnapshot_canonical_mutation_cannot_rebase_protection",
            "tests/test_promotion_adapter.py::PromotionAdapterTests::test_requires_authentic_tool_free_reviewer_receipt",
            "tests/test_promotion_adapter.py::PromotionAdapterTests::test_rejects_incomplete_or_changed_canonical_baseline",
            "tests/test_derivation_compiler.py::DerivationCompilerTests::test_artifact_drift_fails_closed",
            "tests/test_derivation_compiler.py::DerivationCompilerTests::test_compiles_and_round_trips_without_manual_derivation",
        }
        self.assertTrue(
            required_nodeids.issubset({item.nodeid for item in manifest.checks})
        )

    def test_runner_executes_exact_selection_and_emits_json_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "manifest.json"
            result_path = root / "result.json"
            self._write(manifest_path, self._payload())

            result = run_quality_proof(manifest_path, repo_root=PROJECT_ROOT)
            write_quality_proof_result(result_path, result)
            persisted = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual("passed", result["status"])
        self.assertEqual("offline-pytest", result["execution_mode"])
        self.assertEqual(0, result["model_calls"])
        self.assertEqual(0, result["pytest_exit_code"])
        self.assertEqual(1, result["check_count"])
        self.assertEqual(1, result["counts"]["passed"])
        self.assertTrue(result["target_met"])
        self.assertTrue(result["hard_ceiling_met"])
        self.assertEqual("target-met", result["performance_status"])
        self.assertEqual("QP-001", result["checks"][0]["id"])
        self.assertEqual(SAMPLE_NODEID, result["checks"][0]["nodeid"])
        self.assertEqual("passed", result["checks"][0]["outcome"])
        self.assertEqual(result, persisted)

    def test_fresh_result_write_is_atomic_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_path = root / "result.json"
            first = {"status": "passed", "proof_id": "first"}
            second = {"status": "failed", "proof_id": "second"}

            write_quality_proof_result(result_path, first, require_fresh=True)
            with self.assertRaises(QualityProofContractError) as raised:
                write_quality_proof_result(result_path, second, require_fresh=True)

            persisted = json.loads(result_path.read_text(encoding="utf-8"))
            temporary_files = list(root.glob(".*.tmp"))

        self.assertEqual("quality-proof-output-exists", raised.exception.code)
        self.assertEqual(first, persisted)
        self.assertEqual([], temporary_files)

    def test_duplicate_ids_and_nodeids_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manifest_path = Path(temporary) / "manifest.json"
            payload = self._payload()
            payload["checks"] = [
                payload["checks"][0],
                payload["checks"][0],
            ]
            self._write(manifest_path, payload)

            with self.assertRaises(QualityProofContractError) as raised:
                load_quality_proof_manifest(manifest_path, repo_root=PROJECT_ROOT)

        self.assertEqual("quality-proof-duplicate", raised.exception.code)

    def test_arbitrary_paths_and_pytest_options_are_rejected(self) -> None:
        unsafe_nodeids = (
            "fts/AutoFin/test_source.py::test_mutates_source",
            "tests/../scripts/run_agent_architecture_audit.py::main",
            "tests/test_quality_proof.py::-k",
        )
        for index, nodeid in enumerate(unsafe_nodeids):
            with self.subTest(nodeid=nodeid), tempfile.TemporaryDirectory() as temporary:
                manifest_path = Path(temporary) / f"manifest-{index}.json"
                self._write(manifest_path, self._payload(nodeid=nodeid))

                with self.assertRaises(QualityProofContractError) as raised:
                    load_quality_proof_manifest(manifest_path, repo_root=PROJECT_ROOT)

                self.assertEqual("quality-proof-nodeid", raised.exception.code)

    def test_unknown_schema_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manifest_path = Path(temporary) / "manifest.json"
            payload = self._payload()
            payload["implicit_model_review"] = True
            self._write(manifest_path, payload)

            with self.assertRaises(QualityProofContractError) as raised:
                load_quality_proof_manifest(manifest_path, repo_root=PROJECT_ROOT)

        self.assertEqual("quality-proof-schema", raised.exception.code)

    def test_target_miss_is_diagnostic_but_hard_ceiling_is_a_gate(self) -> None:
        checks = ({"outcome": "passed"},)

        target_miss = summarize_quality_proof_outcome(
            pytest_exit_code=0,
            check_results=checks,
            duration_seconds=12,
            target_duration_seconds=10,
            hard_duration_ceiling_seconds=30,
        )
        hard_failure = summarize_quality_proof_outcome(
            pytest_exit_code=0,
            check_results=checks,
            duration_seconds=31,
            target_duration_seconds=10,
            hard_duration_ceiling_seconds=30,
        )

        self.assertEqual("passed", target_miss["status"])
        self.assertFalse(target_miss["target_met"])
        self.assertTrue(target_miss["hard_ceiling_met"])
        self.assertEqual("target-missed", target_miss["performance_status"])
        self.assertEqual("failed", hard_failure["status"])
        self.assertFalse(hard_failure["hard_ceiling_met"])
        self.assertEqual("hard-ceiling-exceeded", hard_failure["performance_status"])

    def test_hard_ceiling_must_exceed_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manifest_path = Path(temporary) / "manifest.json"
            payload = self._payload()
            payload["hard_duration_ceiling_seconds"] = 10
            self._write(manifest_path, payload)

            with self.assertRaises(QualityProofContractError) as raised:
                load_quality_proof_manifest(manifest_path, repo_root=PROJECT_ROOT)

        self.assertEqual("quality-proof-schema", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
