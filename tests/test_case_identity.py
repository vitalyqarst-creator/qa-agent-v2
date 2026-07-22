from __future__ import annotations

import inspect
import unittest

from test_case_agent.case_identity import (
    CaseIdentityError,
    assign_stable_ids,
    semantic_case_key,
    stable_tc_id,
)


def key(variant: str, *, condition: str = "always") -> str:
    return semantic_case_key(
        scope_slug="sample-scope",
        subject_key="customer.phone",
        property_kind="numeric-format",
        coverage_variant=variant,
        condition_key=condition,
    )


class StableCaseIdentityTests(unittest.TestCase):
    def test_reorder_does_not_change_ids(self) -> None:
        first = assign_stable_ids([key("valid"), key("letters")], prefix="SMP")
        second = assign_stable_ids([key("letters"), key("valid")], prefix="SMP")
        self.assertEqual(first, second)

    def test_insertion_does_not_renumber_existing_cases(self) -> None:
        original = assign_stable_ids([key("valid"), key("letters")], prefix="SMP")
        expanded = assign_stable_ids(
            [key("spaces"), key("valid"), key("letters")], prefix="SMP"
        )
        self.assertEqual(original[key("valid")], expanded[key("valid")])
        self.assertEqual(original[key("letters")], expanded[key("letters")])

    def test_requirement_renumber_and_display_wording_are_not_identity_inputs(self) -> None:
        identity_inputs = set(inspect.signature(semantic_case_key).parameters)
        self.assertTrue(
            {
                "requirement_code",
                "source_locator",
                "display_wording",
                "ordinal_position",
            }.isdisjoint(identity_inputs)
        )

    def test_changed_behavior_gets_a_new_id(self) -> None:
        before = key("accepted")
        after = key("rejected")
        self.assertNotEqual(
            stable_tc_id(prefix="SMP", case_key=before),
            stable_tc_id(prefix="SMP", case_key=after),
        )

    def test_conflicting_existing_registry_is_rejected(self) -> None:
        with self.assertRaisesRegex(CaseIdentityError, "conflicts"):
            assign_stable_ids(
                [key("valid")],
                prefix="SMP",
                existing={key("valid"): "TC-SMP-0000000000"},
            )

    def test_duplicate_semantic_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(CaseIdentityError, "duplicate"):
            assign_stable_ids([key("valid"), key("valid")], prefix="SMP")


if __name__ == "__main__":
    unittest.main()
