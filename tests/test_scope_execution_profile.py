from __future__ import annotations

import unittest

from test_case_agent.scope_execution_profile import (
    LEAN_PROFILE,
    STANDARD_PROFILE,
    ScopeExecutionProfileError,
    select_scope_execution_profile,
)


class ScopeExecutionProfileTests(unittest.TestCase):
    @staticmethod
    def _facts() -> dict[str, object]:
        return {
            "version": 1,
            "bounded_scope_kind": "single-section",
            "expected_testable_assertion_count": 10,
            "expected_tc_count": 14,
            "internal_package_count": 1,
            "has_heterogeneous_integrations": False,
            "has_large_dictionary": False,
            "mockups_ready": True,
        }

    @staticmethod
    def _rows(count: int) -> list[dict[str, object]]:
        return [
            {
                "source_row_id": f"SRC-{index + 1:03d}",
                "requirement_codes_hint": [f"BSR {263 + index}"],
            }
            for index in range(count)
        ]

    @classmethod
    def _rows_with_codes(
        cls,
        count: int,
        codes: range,
    ) -> list[dict[str, object]]:
        rows = cls._rows(count)
        for row in rows:
            row["requirement_codes_hint"] = []
        for index, code in enumerate(codes):
            rows[index % count]["requirement_codes_hint"].append(f"BSR {code}")
        return rows

    def test_h72_thirteen_rows_routes_standard_without_using_codes_as_tc_count(self) -> None:
        rows = self._rows_with_codes(13, range(263, 285))
        context = {
            "source_rows": rows,
            "scope_execution_facts": self._facts(),
        }

        profile = select_scope_execution_profile(context, contract_version=1)
        payload = profile.to_dict()

        self.assertEqual(STANDARD_PROFILE, profile.selected_profile)
        self.assertEqual("semantic-design-bridge-required", profile.route_action)
        self.assertEqual(22, payload["diagnostics"]["unique_requirement_code_count"])
        self.assertEqual([], payload["unknown_criteria"])
        self.assertEqual(
            ["source-row-limit-exceeded"],
            [item["code"] for item in payload["violations"]],
        )
        self.assertEqual(
            {"code": "source-row-limit-exceeded", "actual": 13, "limit": 12},
            payload["violations"][0],
        )

    def test_twelve_rows_at_all_limits_are_lean_eligible(self) -> None:
        context = {
            "source_rows": self._rows(12),
            "scope_execution_facts": self._facts(),
        }

        profile = select_scope_execution_profile(context, contract_version=1)

        self.assertTrue(profile.lean_eligible)
        self.assertEqual(LEAN_PROFILE, profile.selected_profile)
        self.assertEqual("invoke-lean-detailed-v1", profile.route_action)

    def test_requirement_code_count_is_diagnostic_only(self) -> None:
        rows = self._rows_with_codes(12, range(263, 285))
        context = {
            "source_rows": rows,
            "scope_execution_facts": self._facts(),
        }

        profile = select_scope_execution_profile(context, contract_version=1)

        self.assertEqual(LEAN_PROFILE, profile.selected_profile)
        self.assertGreater(profile.requirement_code_count, 14)
        self.assertEqual((), profile.violations)

    def test_missing_facts_route_standard_fail_closed(self) -> None:
        profile = select_scope_execution_profile(
            {"source_rows": self._rows(1)},
            contract_version=1,
        )

        self.assertEqual(STANDARD_PROFILE, profile.selected_profile)
        self.assertFalse(profile.lean_eligible)
        self.assertIn("expected_tc_count", profile.unknown_criteria)

    def test_empty_source_rows_are_rejected(self) -> None:
        with self.assertRaisesRegex(ScopeExecutionProfileError, "non-empty"):
            select_scope_execution_profile(
                {"source_rows": [], "scope_execution_facts": self._facts()},
                contract_version=1,
            )

    def test_explicit_ineligible_lean_routes_standard_fail_closed(self) -> None:
        profile = select_scope_execution_profile(
            {"source_rows": self._rows(13)},
            requested_profile=LEAN_PROFILE,
            contract_version=1,
        )

        self.assertEqual(STANDARD_PROFILE, profile.selected_profile)
        self.assertFalse(profile.lean_eligible)

    def test_required_null_facts_route_standard_fail_closed(self) -> None:
        facts = self._facts()
        facts["expected_tc_count"] = None
        facts["bounded_scope_kind"] = None
        facts["mockups_ready"] = None

        profile = select_scope_execution_profile(
            {"source_rows": self._rows(1), "scope_execution_facts": facts},
            contract_version=1,
        )

        self.assertEqual(STANDARD_PROFILE, profile.selected_profile)
        self.assertEqual(
            {"bounded_scope_kind", "expected_tc_count", "mockups_ready"},
            set(profile.unknown_criteria),
        )

    def test_zero_internal_packages_routes_standard(self) -> None:
        facts = self._facts()
        facts["internal_package_count"] = 0

        profile = select_scope_execution_profile(
            {"source_rows": self._rows(1), "scope_execution_facts": facts},
            contract_version=1,
        )

        self.assertEqual(STANDARD_PROFILE, profile.selected_profile)
        self.assertEqual(
            "internal-package-count-not-one",
            profile.violations[0]["code"],
        )

    def test_lean_profile_rejects_compact_contract_v2(self) -> None:
        with self.assertRaisesRegex(ScopeExecutionProfileError, "requires detailed"):
            select_scope_execution_profile(
                {
                    "source_rows": self._rows(1),
                    "scope_execution_facts": self._facts(),
                },
                requested_profile=LEAN_PROFILE,
                contract_version=2,
            )

    def test_explicit_v2_remains_available_as_standard_boundary(self) -> None:
        profile = select_scope_execution_profile(
            {"source_rows": self._rows(13)},
            requested_profile=STANDARD_PROFILE,
            contract_version=2,
        )

        self.assertEqual("invoke-standard-scope-boundary-v2", profile.route_action)
        self.assertTrue(profile.semantic_design_bridge_required)


if __name__ == "__main__":
    unittest.main()
