from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.test_data_sources import (
    TestDataPlanError,
    recommend_source,
    register_provider,
    validate_plan,
    validate_plan_file,
)


ROOT = Path(__file__).resolve().parents[1]
BINARY_FIXTURE_SCRIPT = ROOT / "scripts" / "create_binary_file_fixture.py"


def load_binary_fixture_module():
    spec = importlib.util.spec_from_file_location("binary_file_fixture_for_plan", BINARY_FIXTURE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        plan = {"contract_version": "test-data-source-plan-v2", "scope_slug": "sample",
                "matrix_sha256": "a" * 64, "items": [{"id": "TDP-001",
                "linked_scenarios": ["SCN-001"], "required_evidence": "neutral-format-value",
                "selected_source": "randomdatatools-synthetic",
                "selection_reason": "Нужно нейтральное значение e-mail",
                "materialization_status": "materialized"}]}
        errors = validate_plan(plan)
        self.assertTrue(any("fixture_id" in error for error in errors))
        self.assertTrue(any("snapshot_sha256" in error for error in errors))

    def test_provider_must_prove_requested_evidence(self) -> None:
        plan = {"contract_version": "test-data-source-plan-v2", "scope_slug": "sample",
                "matrix_sha256": "b" * 64, "items": [{"id": "TDP-001",
                "linked_scenarios": ["SCN-001"], "required_evidence": "business-valid-entity",
                "selected_source": "randomdatatools-synthetic", "selection_reason": "Проверка gate",
                "materialization_status": "blocked", "blocker": "Нужен provider"}]}
        self.assertTrue(any("не доказывает" in error for error in validate_plan(plan)))

    def test_materialized_data_must_bind_every_required_property(self) -> None:
        plan = {"contract_version": "test-data-source-plan-v2", "scope_slug": "sample",
                "matrix_sha256": "c" * 64, "items": [{"id": "TDP-001",
                "linked_scenarios": ["SCN-001"], "required_evidence": "source-literal",
                "required_properties": ["город=Красноярск"],
                "selected_source": "source-literal", "selection_reason": "Источник задаёт город",
                "materialization_status": "materialized", "fixture_id": "FX-SRC-CITY-001",
                "snapshot_path": "snapshot.json", "receipt_path": "receipt.json",
                "snapshot_sha256": "d" * 64, "evidence_bindings": []}]}
        self.assertTrue(any("evidence_bindings" in error for error in validate_plan(plan)))

    def test_dadata_semantic_gap_is_blocked_with_baq(self) -> None:
        plan = {"contract_version": "test-data-source-plan-v2", "scope_slug": "sample",
                "matrix_sha256": "e" * 64, "items": [{"id": "TDP-001",
                "linked_scenarios": ["SCN-001"], "required_evidence": "integration-response",
                "required_properties": ["фактический адрес"],
                "selected_source": "dadata-suggestions", "provider_context": "party",
                "required_capabilities": ["party.actual_address"],
                "selection_reason": "Проверяется автозаполнение адреса",
                "materialization_status": "blocked",
                "blocker": "BAQ-001: provider не возвращает отдельный фактический адрес"}]}
        self.assertEqual([], validate_plan(plan))

    def test_materialized_plan_verifies_snapshot_receipt_and_bound_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scope = Path(directory)
            snapshot = {"city": "Красноярск"}
            receipt = {"fixture_id": "FX-SRC-CITY-001", "status": "verified"}
            snapshot_path = scope / "snapshot.json"
            receipt_path = scope / "receipt.json"
            snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
            plan = {"contract_version": "test-data-source-plan-v2", "scope_slug": "sample",
                    "matrix_sha256": "f" * 64, "items": [{"id": "TDP-001",
                    "linked_scenarios": ["SCN-001"], "required_evidence": "source-literal",
                    "required_properties": ["город=Красноярск"],
                    "selected_source": "source-literal", "selection_reason": "Источник задаёт город",
                    "materialization_status": "materialized", "fixture_id": "FX-SRC-CITY-001",
                    "snapshot_path": "snapshot.json", "receipt_path": "receipt.json",
                    "snapshot_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
                    "evidence_bindings": [{"required_property": "город=Красноярск",
                    "evidence_path": "snapshot:/city", "verified_value": "Красноярск"}]}]}
            plan_path = scope / "test-data-source-plan.json"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_plan_file(plan_path))

            plan["items"][0]["evidence_bindings"][0]["verified_value"] = "Москва"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(any("verified_value" in error for error in validate_plan_file(plan_path)))

    def test_binary_fixture_plan_requires_supported_capabilities_and_receipt_values(self) -> None:
        binary_fixture = load_binary_fixture_module()
        with tempfile.TemporaryDirectory() as directory:
            scope = Path(directory)
            fixture_dir = scope / "test-data" / "FX-FILE-PNG-001"
            receipt = binary_fixture.create_binary_file_fixture(
                fixture_id="FX-FILE-PNG-001",
                file_format="png",
                size_bytes=1_024,
                output_dir=fixture_dir,
                purpose="Проверка файла",
            )
            plan = {"contract_version": "test-data-source-plan-v2", "scope_slug": "sample",
                    "matrix_sha256": "a" * 64, "items": [{"id": "TDP-001",
                    "linked_scenarios": ["SCN-001"], "required_evidence": "binary-file-artifact",
                    "required_properties": ["формат=png", "размер=1024 байта"],
                    "selected_source": "local-binary-fixture", "provider_context": "file",
                    "required_capabilities": ["file.png", "file.exact-size-bytes"],
                    "selection_reason": "Нужен воспроизводимый файл заданного размера",
                    "materialization_status": "materialized", "fixture_id": receipt["fixture_id"],
                    "snapshot_path": "test-data/FX-FILE-PNG-001/fixture.png",
                    "receipt_path": "test-data/FX-FILE-PNG-001/FX-FILE-PNG-001.receipt.json",
                    "snapshot_sha256": receipt["file"]["sha256"],
                    "evidence_bindings": [
                        {"required_property": "формат=png", "evidence_path": "receipt:/file/format", "verified_value": "png"},
                        {"required_property": "размер=1024 байта", "evidence_path": "receipt:/file/size_bytes", "verified_value": 1_024},
                    ]}]}
            plan_path = scope / "test-data-source-plan.json"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_plan_file(plan_path, repo_root=ROOT))


if __name__ == "__main__":
    unittest.main()
