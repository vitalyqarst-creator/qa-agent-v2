from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from test_case_agent.iteration_contract import (
    REVIEWER_PROMPT_INSTRUCTION,
    reviewer_acceptance_contract,
    reviewer_response_schema,
)
from test_case_agent.promotion_adapter import (
    PromotionAdapterBlocked,
    prepare_immutable_iteration_promotion,
)
from test_case_agent.review_cycle.runtime import sha256_path


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


class PromotionAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        self.ft = self.repo / "fts" / "demo"
        self.cycle = self.ft / "work" / "immutable" / "run-001"
        self.cycle.mkdir(parents=True)
        self.source = self.ft / "source" / "requirements.xhtml"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("<html>source</html>\n", encoding="utf-8")
        self.canonical = self.ft / "test-cases" / "4.1-existing.md"
        self.canonical.parent.mkdir(parents=True)
        self.canonical.write_text("# Existing canonical\n", encoding="utf-8")
        self.canonical_before = self.canonical.read_bytes()
        self.candidate = self.cycle / "shadow-test-cases.md"
        self.candidate.write_text("# Shadow candidate\n", encoding="utf-8")

        self.graph = {
            "schema_version": 1,
            "ft_slug": "demo",
            "scope_slug": "demo-scope",
            "source_manifest_digest": "a" * 64,
            "obligation_set_digest": "b" * 64,
            "properties": [],
            "obligations": [],
            "cases": [
                {
                    "case_key": "CASE-001",
                    "tc_id": "TC-001",
                    "obligation_ids": ["OBL-001"],
                    "status": "executable",
                }
            ],
            "gaps": [],
        }
        self.graph_digest = _canonical_digest(self.graph)
        _write_json(self.cycle / "coverage-graph.json", self.graph)
        _write_json(
            self.cycle / "suite-gate.json",
            {
                "schema_version": 1,
                "passed": True,
                "graph_digest": self.graph_digest,
                "draft_sha256": sha256_path(self.candidate),
                "expected_case_count": 1,
                "actual_case_count": 1,
                "findings": [],
            },
        )
        self.request = {
            "schema_version": 1,
            "graph_digest": self.graph_digest,
            "draft_sha256": sha256_path(self.candidate),
            "cases": [
                {
                    "case_key": "CASE-001",
                    "tc_id": "TC-001",
                    "status": "executable",
                    "source": {},
                    "obligation": {"obligation_id": "OBL-001"},
                    "test_case": {},
                }
            ],
            "acceptance": reviewer_acceptance_contract(),
        }
        _write_json(self.cycle / "reviewer-request.json", self.request)
        model_dir = self.cycle / "model-stages"
        model_dir.mkdir()
        prompt = (
            REVIEWER_PROMPT_INSTRUCTION
            + "\nREQUEST JSON:\n"
            + _canonical_bytes(self.request).decode("utf-8")
            + "\n"
        )
        (model_dir / "reviewer-prompt.txt").write_text(
            prompt,
            encoding="utf-8",
            newline="\n",
        )
        self.schema = reviewer_response_schema(
            (("CASE-001", "TC-001", "OBL-001", "executable"),),
            graph_digest=self.graph_digest,
            draft_sha256=sha256_path(self.candidate),
        )
        _write_json(model_dir / "reviewer-output-schema.json", self.schema)
        self.response = {
            "schema_version": 1,
            "graph_digest": self.graph_digest,
            "draft_sha256": sha256_path(self.candidate),
            "decision": "accepted",
            "case_results": [
                {
                    "case_key": "CASE-001",
                    "tc_id": "TC-001",
                    "obligation_id": "OBL-001",
                    "status": "covered",
                    "comment": "Покрыто.",
                }
            ],
            "findings": [],
            "summary": "Все проверки покрыты.",
        }
        _write_json(model_dir / "reviewer-response.json", self.response)
        self.writer_receipt = {
            "stage": "writer",
            "backend": "deterministic-zero-call",
            "attempts": 0,
            "response_sha256": "unavailable",
        }
        self.reviewer_receipt = self._reviewer_receipt()
        self._write_receipts()
        _write_json(
            self.cycle / "protected-inputs.receipt.json",
            {
                "schema_version": 1,
                "files": [
                    self._protected("source", self.source),
                    self._protected("canonical", self.canonical),
                ],
            },
        )

    def _rel(self, path: Path) -> str:
        return path.relative_to(self.repo).as_posix()

    def _protected(self, role: str, path: Path) -> dict[str, Any]:
        return {
            "role": role,
            "path": self._rel(path),
            "sha256": sha256_path(path),
            "size_bytes": path.stat().st_size,
        }

    def _reviewer_receipt(self) -> dict[str, Any]:
        model_dir = self.cycle / "model-stages"
        return {
            "stage": "reviewer",
            "backend": "codex-exec-tool-free",
            "attempts": 1,
            "timeout_seconds": None,
            "tool_event_count": 0,
            "request_sha256": _canonical_digest(self.request),
            "prompt_sha256": sha256_path(model_dir / "reviewer-prompt.txt"),
            "schema_sha256": sha256_path(model_dir / "reviewer-output-schema.json"),
            "response_sha256": sha256_path(model_dir / "reviewer-response.json"),
        }

    def _write_receipts(self, **summary_overrides: Any) -> None:
        stages = [self.writer_receipt, self.reviewer_receipt]
        _write_json(
            self.cycle / "model-stage-receipts.json",
            {"schema_version": 1, "stages": stages},
        )
        summary = {
            "schema_version": 1,
            "mode": "immutable-deterministic-first",
            "status": "accepted-shadow",
            "graph_digest": self.graph_digest,
            "draft": self._rel(self.candidate),
            "writer_model_calls": 0,
            "reviewer_model_calls": 1,
            "reviewer_decision": "accepted",
            "reviewer_accepted_zero_findings": True,
            "suite_gate_passed": True,
            "protected_inputs_unchanged": True,
            "canonical_publication": "not-performed",
            "promotion": "out-of-scope",
            "model_stages": stages,
        }
        summary.update(summary_overrides)
        _write_json(self.cycle / "iteration-summary.json", summary)

    def _rewrite_response(self) -> None:
        _write_json(self.cycle / "model-stages" / "reviewer-response.json", self.response)
        self.reviewer_receipt = self._reviewer_receipt()
        self._write_receipts()

    def prepare(self):
        return prepare_immutable_iteration_promotion(
            repo_root=self.repo,
            ft_root=self.ft,
            iteration_output_dir=self.cycle,
            scope_slug="demo-scope",
        )

    def test_builds_and_reuses_minimal_eligibility_basis_without_publication(self) -> None:
        result = self.prepare()

        self.assertEqual("eligible-built", result.status)
        self.assertEqual(self.canonical_before, self.canonical.read_bytes())
        self.assertEqual(sha256_path(result.basis_path), result.basis_sha256)
        self.assertEqual(sha256_path(self.candidate), result.candidate_sha256)
        self.assertEqual(
            {"test-cases/4.1-existing.md": sha256_path(self.canonical)},
            result.production_test_case_hashes,
        )
        basis = json.loads(result.basis_path.read_text(encoding="utf-8"))
        self.assertTrue(basis["eligible"])
        self.assertEqual("not-performed", basis["publication"])
        self.assertEqual(
            sha256_path(self.cycle / "model-stages" / "reviewer-response.json"),
            basis["reviewer_receipt"]["response_sha256"],
        )
        self.assertNotIn("cycle_state", json.dumps(basis))
        self.assertNotIn("traceability_matrix", json.dumps(basis))

        reused = self.prepare()
        self.assertEqual("eligible-reused", reused.status)
        self.assertEqual(result.basis_sha256, reused.basis_sha256)
        self.assertEqual(self.canonical_before, self.canonical.read_bytes())

    def test_requires_zero_writer_and_one_reviewer_call(self) -> None:
        for field, value in (("writer_model_calls", 1), ("reviewer_model_calls", 0)):
            with self.subTest(field=field):
                self._write_receipts(**{field: value})
                with self.assertRaisesRegex(PromotionAdapterBlocked, "iteration-not-eligible"):
                    self.prepare()
                self._write_receipts()

    def test_rejects_qualification_only_and_non_promotable_runs(self) -> None:
        for overrides in (
            {"qualification_only": True},
            {"promotion_eligible": False},
            {"non_promotable_reason": "fixture-test-hook"},
        ):
            with self.subTest(overrides=overrides):
                self._write_receipts(**overrides)
                with self.assertRaisesRegex(
                    PromotionAdapterBlocked, "qualification-not-promotable"
                ):
                    self.prepare()
                self._write_receipts()

    def test_rejects_accepted_suite_with_calibration_pending(self) -> None:
        self._write_receipts(
            status="accepted-with-calibration-pending",
            calibration_pending_count=1,
            promotion_eligible=False,
            non_promotable_reason="calibration-pending",
        )

        with self.assertRaisesRegex(PromotionAdapterBlocked, "calibration-pending"):
            self.prepare()

    def test_requires_authentic_tool_free_reviewer_receipt(self) -> None:
        invalid = {
            "backend": "fixture",
            "attempts": 0,
            "timeout_seconds": 30,
            "tool_event_count": 1,
        }
        for field, value in invalid.items():
            with self.subTest(field=field):
                original = self.reviewer_receipt[field]
                self.reviewer_receipt[field] = value
                self._write_receipts()
                with self.assertRaisesRegex(PromotionAdapterBlocked, "review-receipt-invalid"):
                    self.prepare()
                self.reviewer_receipt[field] = original
                self._write_receipts()

    def test_rejects_each_broken_reviewer_hash_binding(self) -> None:
        for field in (
            "request_sha256",
            "prompt_sha256",
            "schema_sha256",
            "response_sha256",
        ):
            with self.subTest(field=field):
                original = self.reviewer_receipt[field]
                self.reviewer_receipt[field] = "0" * 64
                self._write_receipts()
                with self.assertRaisesRegex(PromotionAdapterBlocked, "review-receipt-invalid"):
                    self.prepare()
                self.reviewer_receipt[field] = original
                self._write_receipts()

    def test_rejects_not_covered_or_finding_bearing_response_even_when_rehashed(self) -> None:
        self.response["case_results"][0]["status"] = "not-covered"
        self._rewrite_response()
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-response-not-accepted"):
            self.prepare()

        self.response["case_results"][0]["status"] = "covered"
        self.response["findings"] = [
            {
                "severity": "warning",
                "case_key": "CASE-001",
                "tc_id": "TC-001",
                "obligation_id": "OBL-001",
                "message": "Найдено замечание.",
            }
        ]
        self._rewrite_response()
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-response-not-accepted"):
            self.prepare()

    def test_rejects_candidate_graph_and_suite_drift(self) -> None:
        self.candidate.write_text("# Changed shadow\n", encoding="utf-8")
        with self.assertRaisesRegex(PromotionAdapterBlocked, "suite-gate-mismatch"):
            self.prepare()

        self.candidate.write_text("# Shadow candidate\n", encoding="utf-8")
        self.graph["ft_slug"] = "changed"
        _write_json(self.cycle / "coverage-graph.json", self.graph)
        with self.assertRaisesRegex(PromotionAdapterBlocked, "graph-mismatch"):
            self.prepare()

    def test_rejects_incomplete_or_changed_canonical_baseline(self) -> None:
        unprotected = self.ft / "test-cases" / "4.2-unprotected.md"
        unprotected.write_text("# Unprotected\n", encoding="utf-8")
        with self.assertRaisesRegex(
            PromotionAdapterBlocked, "incomplete-canonical-baseline"
        ):
            self.prepare()
        unprotected.unlink()

        self.canonical.write_text("# Changed canonical\n", encoding="utf-8")
        with self.assertRaisesRegex(PromotionAdapterBlocked, "protected-input-drift"):
            self.prepare()

    def test_conflicting_existing_basis_fails_closed(self) -> None:
        basis = self.cycle / "promotion-eligibility-basis.json"
        _write_json(basis, {"forged": True})

        with self.assertRaisesRegex(PromotionAdapterBlocked, "basis-conflict"):
            self.prepare()
        self.assertEqual(self.canonical_before, self.canonical.read_bytes())


if __name__ == "__main__":
    unittest.main()
