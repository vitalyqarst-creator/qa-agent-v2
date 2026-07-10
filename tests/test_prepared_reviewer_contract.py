from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

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
                    "atom_id": "ATOM-001",
                    "verdict": "covered",
                    "test_case_ids": ["TC-PREP-001"],
                    "note": "The concrete observable result is covered.",
                },
                {
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
        with self.assertRaisesRegex(runner.RunnerError, "atom set mismatch"):
            self.parse(payload)

    def test_rejects_duplicate_atom(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["obligation_reviews"].append(
            copy.deepcopy(payload["obligation_reviews"][0])
        )
        with self.assertRaisesRegex(runner.RunnerError, "duplicate atom ids"):
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


if __name__ == "__main__":
    unittest.main()
