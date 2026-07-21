import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.promotion_readiness import (
    PromotionContract,
    validate_promotion_readiness,
)


class PromotionReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.accepted = self.root / "accepted.md"
        self.accepted.write_text("accepted\n", encoding="utf-8")
        self.contract_path = self.root / "contract.json"
        self.contract_path.write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "canonical_test_cases": "fts/demo/test-cases/1-demo.md",
                    "canonical_title": "Тест-кейсы: demo",
                    "ft_slug": "demo",
                    "scope_slug": "demo-scope",
                    "section_id": "1",
                    "domain_package_id": "WP-01",
                    "test_design_dir": "fts/demo/work/test-design/1-demo",
                    "test_case_ids": ["TC-DEMO-001"],
                    "expected_priorities": {"TC-DEMO-001": "High"},
                    "required_requirement_ids": ["BSR 1"],
                    "required_sections": ["Metadata", "Coverage Summary", "Coverage Gaps", "Test Cases"],
                    "required_gap_ids": ["GAP-001"],
                    "accepted_candidate": "accepted.md",
                    "accepted_candidate_sha256": hashlib.sha256(self.accepted.read_bytes()).hexdigest(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_accepts_canonical_production_shape(self) -> None:
        contract = PromotionContract.load(self.contract_path, self.root)
        draft = self.root / "draft.md"
        draft.write_text(
            """# Тест-кейсы: demo

## Metadata
| field | value |
| --- | --- |
| ft_slug | `demo` |
| scope_slug | `demo-scope` |
| section_id | `1` |
| package_id | `WP-01` |
| test_design_dir | `fts/demo/work/test-design/1-demo` |

## Coverage Summary
GAP-001; BSR 1

## Coverage Gaps
GAP-001 preserved.

## Test Cases

## TC-DEMO-001
**package_id:** WP-01
**Приоритет:** High
""",
            encoding="utf-8",
        )
        self.assertTrue(validate_promotion_readiness(draft_path=draft, contract=contract).passed)

    def test_rejects_diagnostic_ids_and_missing_canonical_sections(self) -> None:
        contract = PromotionContract.load(self.contract_path, self.root)
        draft = self.root / "draft.md"
        draft.write_text("# Тест-кейсы\n\n## TC-PREP-001\n**package_id:** run-id\n", encoding="utf-8")
        report = validate_promotion_readiness(draft_path=draft, contract=contract)
        self.assertFalse(report.passed)
        ids = {item["id"] for item in report.findings}
        self.assertIn("temporary-test-case-id", ids)
        self.assertIn("canonical-test-case-ids-mismatch", ids)
        self.assertIn("missing-canonical-section", ids)

    def test_rejects_changed_accepted_candidate(self) -> None:
        self.accepted.write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(Exception, "SHA-256 mismatch"):
            PromotionContract.load(self.contract_path, self.root)

    def test_accepts_scope_without_coverage_gaps(self) -> None:
        payload = json.loads(self.contract_path.read_text(encoding="utf-8"))
        payload["required_gap_ids"] = []
        self.contract_path.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )

        contract = PromotionContract.load(self.contract_path, self.root)

        self.assertEqual((), contract.required_gap_ids)


if __name__ == "__main__":
    unittest.main()
