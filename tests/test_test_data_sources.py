from __future__ import annotations

import unittest

from test_case_agent.test_data_sources import TestDataPlanError, recommend_source, register_provider, validate_plan


class TestDataSourcesTest(unittest.TestCase):
    def test_selects_dadata_only_for_dadata_integration(self) -> None:
        self.assertEqual(recommend_source("integration-response", integration="DaData"),
                         "dadata-suggestions")

    def test_selects_synthetic_provider_for_neutral_format_only(self) -> None:
        self.assertEqual(recommend_source("neutral-format-value"), "randomdatatools-synthetic")
        with self.assertRaises(TestDataPlanError):
            recommend_source("business-valid-entity")

    def test_environment_state_is_not_replaced_by_external_provider(self) -> None:
        self.assertEqual(recommend_source("environment-state", integration="DaData"),
                         "test-environment-setup")

    def test_custom_provider_can_be_registered_without_route_change(self) -> None:
        register_provider("company-registry-x", evidence={"integration-response"},
                          adapter="scripts/verify_company_registry_x.py", integration="registry-x")
        self.assertEqual(recommend_source("integration-response", integration="registry-x"),
                         "company-registry-x")

    def test_materialized_item_requires_reproducible_evidence(self) -> None:
        plan = {"contract_version": "test-data-source-plan-v1", "scope_slug": "sample",
                "matrix_sha256": "a" * 64, "items": [{"id": "TDP-001",
                "linked_scenarios": ["SCN-001"], "required_evidence": "neutral-format-value",
                "selected_source": "randomdatatools-synthetic",
                "selection_reason": "Нужно нейтральное значение e-mail",
                "materialization_status": "materialized"}]}
        errors = validate_plan(plan)
        self.assertTrue(any("fixture_id" in error for error in errors))
        self.assertTrue(any("snapshot_sha256" in error for error in errors))

    def test_provider_must_prove_requested_evidence(self) -> None:
        plan = {"contract_version": "test-data-source-plan-v1", "scope_slug": "sample",
                "matrix_sha256": "b" * 64, "items": [{"id": "TDP-001",
                "linked_scenarios": ["SCN-001"], "required_evidence": "business-valid-entity",
                "selected_source": "randomdatatools-synthetic", "selection_reason": "Проверка gate",
                "materialization_status": "blocked", "blocker": "Нужен provider"}]}
        self.assertTrue(any("не доказывает" in error for error in validate_plan(plan)))


if __name__ == "__main__":
    unittest.main()
