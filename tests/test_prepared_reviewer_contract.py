from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from test_case_agent.review_cycle.prepared_package import PreparedObligation


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT_DIR / "scripts" / "codex_exec_review_cycle_runner.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location(
        "prepared_reviewer_contract_runner_under_test", RUNNER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner_module()


class PreparedReviewerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.draft = (
            "# Test cases\n\n"
            "## TC-PREP-001\n\n"
            "**Трассировка:** ATOM-001\n\n"
            "Concrete draft body.\n"
        )
        self.digest = hashlib.sha256(self.draft.encode("utf-8")).hexdigest()
        self.obligations = (
            PreparedObligation(
                obligation_id="ATOM-001",
                source_refs=("SRC-1",),
                atomic_statement="Visible behavior",
                observable_oracle="Visible result",
                test_intent="Verify visible result",
                coverage_status="testable",
                gap_id="",
                dictionary_refs=(),
                notes="",
            ),
            PreparedObligation(
                obligation_id="ATOM-002",
                source_refs=("SRC-2",),
                atomic_statement="Internal behavior without artifact",
                observable_oracle="No observable artifact",
                test_intent="Preserve as a gap",
                coverage_status="gap",
                gap_id="GAP-001",
                dictionary_refs=(),
                notes="",
            ),
        )
        self.payload = {
            "contract_version": 2,
            "decision": "accepted",
            "reviewed_draft_sha256": self.digest,
            "obligation_reviews": [
                {
                    "obligation_id": "ATOM-001",
                    "atom_id": "ATOM-001",
                    "verdict": "covered",
                    "test_case_ids": ["TC-PREP-001"],
                    "note": "The concrete observable result is covered.",
                },
                {
                    "obligation_id": "ATOM-002",
                    "atom_id": "ATOM-002",
                    "verdict": "gap-preserved",
                    "test_case_ids": [],
                    "note": "The internal behavior remains non-executable.",
                },
            ],
            "findings": [],
            "summary": "All eligible obligations are consistent.",
        }

    def parse(self, payload):
        return runner.parse_prepared_review_contract(
            json.dumps(payload, ensure_ascii=False),
            expected_obligations=self.obligations,
            expected_draft_sha256=self.digest,
            draft_text=self.draft,
        )

    def error_finding(self, atom_id: str = "ATOM-001") -> dict:
        return {
            "id": "REV-001",
            "severity": "error",
            "category": "coverage",
            "atom_ids": [atom_id],
            "test_case_ids": [],
            "problem": "The obligation is not correctly covered.",
            "required_change": "Correct the obligation coverage.",
        }

    def test_accepts_complete_atom_set(self) -> None:
        review = self.parse(self.payload)
        self.assertEqual("accepted", review.decision)
        self.assertEqual(2, len(review.obligation_reviews))

    def test_rejects_missing_atom(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["obligation_reviews"].pop()
        with self.assertRaisesRegex(runner.RunnerError, "obligation set mismatch"):
            self.parse(payload)

    def test_rejects_duplicate_atom(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["obligation_reviews"].append(
            copy.deepcopy(payload["obligation_reviews"][0])
        )
        with self.assertRaisesRegex(runner.RunnerError, "duplicate obligation ids"):
            self.parse(payload)

    def test_rejects_unknown_test_case(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["obligation_reviews"][0]["test_case_ids"] = ["TC-UNKNOWN-999"]
        with self.assertRaisesRegex(runner.RunnerError, "unknown test-case ids"):
            self.parse(payload)

    def test_runner_rejects_duplicate_test_case_ids_without_transport_unique_items(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["obligation_reviews"][0]["test_case_ids"] = [
            "TC-PREP-001",
            "TC-PREP-001",
        ]
        with self.assertRaisesRegex(runner.RunnerError, "must not contain duplicates"):
            self.parse(payload)

    def test_rejects_executable_test_case_for_preserved_gap(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["obligation_reviews"][1]["test_case_ids"] = ["TC-PREP-001"]
        with self.assertRaisesRegex(runner.RunnerError, "must not reference executable"):
            self.parse(payload)

    def test_rejects_accepted_with_error_finding(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["findings"] = [self.error_finding()]
        with self.assertRaisesRegex(runner.RunnerError, "accepted prepared review"):
            self.parse(payload)

    def test_rejects_changes_required_without_finding(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["decision"] = "changes-required"
        with self.assertRaisesRegex(runner.RunnerError, "requires at least one finding"):
            self.parse(payload)

    def test_rejects_blocking_verdict_without_linked_error(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["decision"] = "changes-required"
        payload["obligation_reviews"][0]["verdict"] = "incorrect"
        payload["findings"] = [self.error_finding("ATOM-002")]
        with self.assertRaisesRegex(runner.RunnerError, "requires an error finding"):
            self.parse(payload)


class SourceFirstReviewerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.draft = "# Test cases\n\n## TC-PREP-001\n\nBody.\n"
        self.draft_sha = hashlib.sha256(self.draft.encode("utf-8")).hexdigest()
        self.source_sha = "1" * 64
        self.obligation_sha = "2" * 64
        self.obligations = (
            PreparedObligation(
                obligation_id="OBL-001",
                atom_id="ATOM-001",
                source_refs=("SRC-001", "SRC-001B", "SRC-002"),
                atomic_statement="Source-backed behavior",
                observable_oracle="Visible result",
                test_intent="Perform action",
                coverage_status="testable",
                gap_id="",
                dictionary_refs=(),
                notes="",
                planned_test_case_id="TC-PREP-001",
            ),
        )
        self.payload = {
            "contract_version": 4,
            "decision": "accepted",
            "reviewed_draft_sha256": self.draft_sha,
            "reviewed_source_basis_sha256": self.source_sha,
            "reviewed_obligation_set_sha256": self.obligation_sha,
            "obligation_reviews": [
                {"obligation_id": "OBL-001", "verdict": "covered"}
            ],
            "dimension_reviews": [
                {
                    "dimension": "state-reset",
                    "verdict": "verified",
                    "source_refs": ["SRC-001", "SRC-001B"],
                    "note": "Source assertion and TC state transition match.",
                },
                {
                    "dimension": "input-boundaries",
                    "verdict": "verified",
                    "source_refs": ["SRC-002"],
                    "note": "The source-backed boundary is covered.",
                },
            ],
            "findings": [],
            "summary": "No source-model or TC exceptions.",
        }
        self.dimension_source_refs = {
            "input-boundaries": ("SRC-002",),
            "state-reset": ("SRC-001", "SRC-001B"),
        }

    def parse(self, payload):
        return runner.parse_prepared_review_contract(
            json.dumps(payload, ensure_ascii=False),
            expected_obligations=self.obligations,
            expected_draft_sha256=self.draft_sha,
            expected_source_basis_sha256=self.source_sha,
            expected_obligation_set_sha256=self.obligation_sha,
            expected_dimensions=("input-boundaries", "state-reset"),
            expected_dimension_source_refs=self.dimension_source_refs,
            draft_text=self.draft,
        )

    def test_accepts_compact_contract_with_exact_obligation_receipt(self) -> None:
        review = self.parse(self.payload)

        self.assertEqual(4, review.contract_version)
        self.assertEqual(1, len(review.obligation_reviews))
        self.assertEqual("OBL-001", review.obligation_reviews[0].obligation_id)
        self.assertEqual("verified", review.dimension_reviews[0].verdict)

    def test_schema_uses_transport_safe_anyof_and_complete_dimension_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "source-evidence.md"
            obligation_path = root / "atomic-obligations.json"
            source_path.write_text("source", encoding="utf-8")
            obligation_path.write_text("{}", encoding="utf-8")
            fake_runner = SimpleNamespace(
                _prepared_package=object(),
                _uses_source_first_contract=lambda: True,
                _source_first_dimension_source_refs=lambda: self.dimension_source_refs,
                _prepared_artifact=lambda kind: {
                    "source-evidence": source_path,
                    "atomic-obligations": obligation_path,
                }[kind],
            )

            schema = runner.CodexExecReviewCycleRunner._review_contract_schema(
                fake_runner,
                obligations_override=self.obligations,
            )

        variants = schema["properties"]["dimension_reviews"]["items"]["anyOf"]
        state_reset = next(
            item
            for item in variants
            if item["properties"]["dimension"]["const"] == "state-reset"
        )
        source_refs = state_reset["properties"]["source_refs"]
        self.assertEqual(
            ["SRC-001", "SRC-001B"],
            source_refs["items"]["enum"],
        )
        self.assertNotIn("const", source_refs)
        self.assertEqual(2, source_refs["minItems"])
        self.assertEqual(2, source_refs["maxItems"])
        self.assertNotIn("oneOf", json.dumps(schema, sort_keys=True))
        self.assertNotIn("uniqueItems", json.dumps(schema, sort_keys=True))

    def test_rejects_missing_obligation_receipt(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["obligation_reviews"] = []

        with self.assertRaisesRegex(runner.RunnerError, "non-empty array"):
            self.parse(payload)

    def test_rejects_obsolete_exception_only_v3(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["contract_version"] = 3
        payload.pop("obligation_reviews")

        with self.assertRaisesRegex(runner.RunnerError, "version 3 is obsolete"):
            self.parse(payload)

    def test_rejects_missing_dimension_and_wrong_source_hash(self) -> None:
        missing = copy.deepcopy(self.payload)
        missing["dimension_reviews"] = []
        with self.assertRaisesRegex(runner.RunnerError, "dimension set mismatch"):
            self.parse(missing)

        stale = copy.deepcopy(self.payload)
        stale["reviewed_source_basis_sha256"] = "3" * 64
        with self.assertRaisesRegex(runner.RunnerError, "source basis hash mismatch"):
            self.parse(stale)

    def test_accepted_cannot_hide_unsupported_dimension(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["dimension_reviews"][0]["verdict"] = "unsupported"

        with self.assertRaisesRegex(runner.RunnerError, "every dimension verified"):
            self.parse(payload)

    def test_dimension_source_refs_must_exist_in_bound_obligations(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["dimension_reviews"][0]["source_refs"] = ["BOGUS-NOT-IN-SOURCE"]

        with self.assertRaisesRegex(runner.RunnerError, "exact canonical"):
            self.parse(payload)

    def test_rejects_source_ref_bound_only_to_another_dimension(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["dimension_reviews"][0]["source_refs"] = ["SRC-002"]

        with self.assertRaisesRegex(runner.RunnerError, "exact canonical"):
            self.parse(payload)

    def test_rejects_dimension_receipt_that_omits_a_bound_source_ref(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["dimension_reviews"][0]["source_refs"] = ["SRC-001"]

        with self.assertRaisesRegex(runner.RunnerError, "exact canonical"):
            self.parse(payload)

    def test_rejects_missing_runner_owned_dimension_binding_map(self) -> None:
        with self.assertRaisesRegex(runner.RunnerError, "binding set mismatch"):
            runner.parse_prepared_review_contract(
                json.dumps(self.payload, ensure_ascii=False),
                expected_obligations=self.obligations,
                expected_draft_sha256=self.draft_sha,
                expected_source_basis_sha256=self.source_sha,
                expected_obligation_set_sha256=self.obligation_sha,
                expected_dimensions=("input-boundaries", "state-reset"),
                draft_text=self.draft,
            )

    def test_rejects_covered_when_planned_test_case_is_absent_from_draft(self) -> None:
        draft = "# Test cases\n\nNo materialized test case.\n"
        digest = hashlib.sha256(draft.encode("utf-8")).hexdigest()
        payload = copy.deepcopy(self.payload)
        payload["reviewed_draft_sha256"] = digest

        with self.assertRaisesRegex(runner.RunnerError, "absent from the reviewed draft"):
            runner.parse_prepared_review_contract(
                json.dumps(payload, ensure_ascii=False),
                expected_obligations=self.obligations,
                expected_draft_sha256=digest,
                expected_source_basis_sha256=self.source_sha,
                expected_obligation_set_sha256=self.obligation_sha,
                expected_dimensions=("input-boundaries", "state-reset"),
                expected_dimension_source_refs=self.dimension_source_refs,
                draft_text=draft,
            )

    def test_blocking_obligation_verdict_requires_linked_error(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["decision"] = "changes-required"
        payload["obligation_reviews"][0]["verdict"] = "incorrect"
        payload["dimension_reviews"][0]["verdict"] = "unsupported"
        payload["findings"] = [
            {
                "id": "REV-SOURCE-001",
                "severity": "error",
                "category": "source-model",
                "atom_ids": [],
                "test_case_ids": [],
                "problem": "Set-level issue does not identify the failed obligation.",
                "required_change": "Link the finding to ATOM-001.",
            }
        ]

        with self.assertRaisesRegex(runner.RunnerError, "requires an error finding"):
            self.parse(payload)

    def test_changes_required_allows_set_level_source_model_exception(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["decision"] = "changes-required"
        payload["dimension_reviews"][0]["verdict"] = "unsupported"
        payload["findings"] = [
            {
                "id": "REV-SOURCE-001",
                "severity": "error",
                "category": "source-model",
                "atom_ids": [],
                "test_case_ids": [],
                "problem": "The supplied source assertion has wrong polarity.",
                "required_change": "Rebuild and independently review the source model.",
            }
        ]

        review = self.parse(payload)

        self.assertEqual("changes-required", review.decision)
        self.assertEqual("source-model", review.findings[0].category)


if __name__ == "__main__":
    unittest.main()
