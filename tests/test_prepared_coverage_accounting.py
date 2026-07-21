from __future__ import annotations

from dataclasses import dataclass
import unittest

from test_case_agent.review_cycle.coverage_accounting import (
    AcceptedRisk,
    ASSERTION_COVERAGE_FLOOR,
    BROAD_PRIMARY_GAP,
    CRITICAL_COVERAGE_FLOOR,
    HIGH_RISK_NONBLOCKING_GAP,
    NEW_GAP_DELTA,
    OVERALL_COVERAGE_FLOOR,
    TESTABLE_TO_GAP_REGRESSION,
    CoverageObligationMetadata,
    evaluate_coverage_accounting,
)


@dataclass(frozen=True)
class ObligationLike:
    obligation_id: str
    coverage_status: str
    gap_id: str = ""
    constraint_gap_ids: tuple[str, ...] = ()


def obligations(
    *,
    testable: int,
    gap: int = 0,
    unclear: int = 0,
    not_applicable: int = 0,
) -> list[ObligationLike]:
    result = [
        ObligationLike(f"OBL-T-{index:03d}", "testable")
        for index in range(1, testable + 1)
    ]
    result.extend(
        ObligationLike(f"OBL-G-{index:03d}", "gap", f"GAP-{index:03d}")
        for index in range(1, gap + 1)
    )
    result.extend(
        ObligationLike(f"OBL-U-{index:03d}", "unclear", f"GAP-U-{index:03d}")
        for index in range(1, unclear + 1)
    )
    result.extend(
        ObligationLike(f"OBL-NA-{index:03d}", "not-applicable")
        for index in range(1, not_applicable + 1)
    )
    return result


class PreparedCoverageAccountingTests(unittest.TestCase):
    def test_91_of_161_reports_descriptive_determinacy_without_blocking(self) -> None:
        result = evaluate_coverage_accounting(obligations(testable=91, gap=70))

        self.assertTrue(result.passed)
        self.assertEqual(161, result.counts.denominator)
        self.assertAlmostEqual(91 / 161, result.ratio)
        self.assertNotIn(OVERALL_COVERAGE_FLOOR, result.finding_codes)
        self.assertEqual("descriptive-only", result.to_dict()["determinacy_policy"])

    def test_legacy_diagnostic_can_explicitly_enforce_determinacy_floor(self) -> None:
        result = evaluate_coverage_accounting(
            obligations(testable=91, gap=70),
            enforce_determinacy_floors=True,
        )

        self.assertFalse(result.passed)
        self.assertIn(OVERALL_COVERAGE_FLOOR, result.blocking_finding_codes)
        self.assertEqual("release-floor", result.to_dict()["determinacy_policy"])

    def test_85_of_100_passes_default_overall_floor_and_excludes_not_applicable(self) -> None:
        result = evaluate_coverage_accounting(
            obligations(testable=85, gap=15, not_applicable=7)
        )

        self.assertTrue(result.passed)
        self.assertEqual(100, result.counts.denominator)
        self.assertEqual(7, result.counts.not_applicable)
        self.assertEqual(0.85, result.ratio)
        self.assertEqual([], result.to_dict()["blocking_finding_codes"])

    def test_assertion_floor_cannot_be_inflated_by_splitting_covered_obligations(self) -> None:
        result = evaluate_coverage_accounting(
            obligations(testable=20),
            assertion_coverage={
                "ASSERT-COVERED": "testable",
                "ASSERT-GAP": "gap",
            },
            enforce_determinacy_floors=True,
        )

        self.assertEqual(1.0, result.ratio)
        self.assertEqual(0.5, result.assertion_ratio)
        self.assertFalse(result.passed)
        self.assertIn(ASSERTION_COVERAGE_FLOOR, result.blocking_finding_codes)
        finding = next(
            item for item in result.findings if item.code == ASSERTION_COVERAGE_FLOOR
        )
        self.assertEqual(("ASSERT-GAP",), finding.assertion_ids)

    def test_assertion_floor_excludes_reviewed_not_applicable_assertions(self) -> None:
        result = evaluate_coverage_accounting(
            obligations(testable=1),
            assertion_coverage={
                "ASSERT-COVERED": "testable",
                "ASSERT-NA": "not-applicable",
            },
        )

        self.assertTrue(result.passed)
        self.assertEqual(1.0, result.assertion_ratio)
        self.assertEqual(1, result.assertion_counts.not_applicable)

    def test_critical_gap_fails_critical_floor_even_when_overall_floor_passes(self) -> None:
        values = obligations(testable=99, gap=1)
        result = evaluate_coverage_accounting(
            values,
            metadata={
                "OBL-G-001": CoverageObligationMetadata(critical=True, risk="high")
            },
        )

        self.assertFalse(result.passed)
        self.assertEqual(0.99, result.ratio)
        self.assertEqual(0.0, result.critical_ratio)
        self.assertIn(CRITICAL_COVERAGE_FLOOR, result.blocking_finding_codes)

    def test_high_risk_nonblocking_gap_fails_without_accepted_risk(self) -> None:
        result = evaluate_coverage_accounting(
            obligations(testable=99, gap=1),
            metadata={
                "OBL-G-001": {
                    "risk": "high",
                    "gap_blocking": False,
                }
            },
        )

        self.assertFalse(result.passed)
        self.assertIn(HIGH_RISK_NONBLOCKING_GAP, result.blocking_finding_codes)

    def test_high_risk_nonblocking_constraint_gap_is_accounted(self) -> None:
        value = ObligationLike(
            "OBL-T-001",
            "testable",
            constraint_gap_ids=("GAP-CONSTRAINT",),
        )
        result = evaluate_coverage_accounting(
            [value],
            metadata={"OBL-T-001": {"risk": "high"}},
            constraint_gap_blocking={"GAP-CONSTRAINT": False},
        )

        self.assertFalse(result.passed)
        self.assertIn(HIGH_RISK_NONBLOCKING_GAP, result.blocking_finding_codes)
        finding = next(
            item for item in result.findings if item.code == HIGH_RISK_NONBLOCKING_GAP
        )
        self.assertEqual(("GAP-CONSTRAINT",), finding.gap_ids)

        accepted = evaluate_coverage_accounting(
            [value],
            metadata={"OBL-T-001": {"risk": "high"}},
            constraint_gap_blocking={"GAP-CONSTRAINT": False},
            accepted_risks=(
                AcceptedRisk(
                    finding_code=HIGH_RISK_NONBLOCKING_GAP,
                    subject_id="GAP-CONSTRAINT",
                    rationale="The exact bounded constraint risk is accepted.",
                ),
            ),
        )
        self.assertTrue(accepted.passed)

    def test_constraint_gap_requires_explicit_blocking_classification(self) -> None:
        value = ObligationLike(
            "OBL-T-001",
            "testable",
            constraint_gap_ids=("GAP-CONSTRAINT",),
        )
        with self.assertRaisesRegex(ValueError, "explicit blocking classification"):
            evaluate_coverage_accounting([value])

    def test_shared_or_multi_assertion_primary_gap_is_forbidden(self) -> None:
        values = obligations(testable=98)
        values.extend(
            [
                ObligationLike("OBL-G-A", "gap", "GAP-BROAD"),
                ObligationLike("OBL-G-B", "gap", "GAP-BROAD"),
            ]
        )
        result = evaluate_coverage_accounting(values)

        self.assertFalse(result.passed)
        self.assertEqual(0.98, result.ratio)
        self.assertIn(BROAD_PRIMARY_GAP, result.blocking_finding_codes)
        finding = next(item for item in result.findings if item.code == BROAD_PRIMARY_GAP)
        self.assertEqual(("OBL-G-A", "OBL-G-B"), finding.obligation_ids)

    def test_narrow_low_risk_40_mb_gap_is_allowed_above_overall_floor(self) -> None:
        values = obligations(testable=9)
        values.append(ObligationLike("OBL-40MB", "gap", "GAP-40MB-BYTE-CONVENTION"))
        result = evaluate_coverage_accounting(
            values,
            metadata={
                "OBL-40MB": CoverageObligationMetadata(
                    risk="low",
                    gap_blocking=False,
                    assertion_count=1,
                )
            },
        )

        self.assertTrue(result.passed)
        self.assertEqual(0.9, result.ratio)
        self.assertEqual((), result.finding_codes)

    def test_testable_to_gap_regression_fails_without_corresponding_accepted_risk(self) -> None:
        baseline = obligations(testable=10)
        current = list(baseline)
        current[0] = ObligationLike("OBL-T-001", "gap", "GAP-REGRESSION")

        result = evaluate_coverage_accounting(
            current,
            baseline_obligations=baseline,
        )

        self.assertFalse(result.passed)
        self.assertIn(TESTABLE_TO_GAP_REGRESSION, result.blocking_finding_codes)
        self.assertNotIn(NEW_GAP_DELTA, result.finding_codes)

    def test_new_gap_delta_fails_without_corresponding_accepted_risk(self) -> None:
        baseline = obligations(testable=10)
        current = [
            *baseline,
            ObligationLike("OBL-NEW", "unclear", "GAP-NEW"),
        ]

        result = evaluate_coverage_accounting(
            current,
            baseline_obligations=baseline,
        )

        self.assertFalse(result.passed)
        self.assertGreater(result.ratio, 0.85)
        self.assertIn(NEW_GAP_DELTA, result.blocking_finding_codes)

    def test_accepted_risk_waives_only_matching_finding_and_subject(self) -> None:
        baseline = obligations(testable=100)
        current = list(baseline)
        current[0] = ObligationLike("OBL-T-001", "gap", "GAP-REGRESSION")
        metadata = {
            "OBL-T-001": CoverageObligationMetadata(
                risk="high",
                gap_blocking=False,
            )
        }
        high_risk_acceptance = AcceptedRisk(
            finding_code=HIGH_RISK_NONBLOCKING_GAP,
            subject_id="OBL-T-001",
            rationale="Named product owner accepted this bounded nonblocking risk.",
        )

        partially_accepted = evaluate_coverage_accounting(
            current,
            metadata=metadata,
            baseline_obligations=baseline,
            accepted_risks=(high_risk_acceptance,),
        )
        self.assertFalse(partially_accepted.passed)
        self.assertNotIn(
            HIGH_RISK_NONBLOCKING_GAP,
            partially_accepted.blocking_finding_codes,
        )
        self.assertIn(
            TESTABLE_TO_GAP_REGRESSION,
            partially_accepted.blocking_finding_codes,
        )

        fully_accepted = evaluate_coverage_accounting(
            current,
            metadata=metadata,
            baseline_obligations=baseline,
            accepted_risks=(
                high_risk_acceptance,
                AcceptedRisk(
                    finding_code=TESTABLE_TO_GAP_REGRESSION,
                    subject_id="OBL-T-001",
                    rationale="The changed source requirement is recorded and approved.",
                ),
            ),
        )
        self.assertTrue(fully_accepted.passed)
        self.assertEqual((), fully_accepted.blocking_finding_codes)
        self.assertEqual(
            {
                HIGH_RISK_NONBLOCKING_GAP,
                TESTABLE_TO_GAP_REGRESSION,
            },
            set(fully_accepted.finding_codes),
        )


if __name__ == "__main__":
    unittest.main()
