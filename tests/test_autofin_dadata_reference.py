from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.prepared_compiler import (
    PreparedCompilerDiagnostic,
    compile_workflow_package,
)
from test_case_agent.review_cycle.obligation_gate import (
    materialize_draft_dictionary_projections,
    materialize_draft_reference_fixtures,
    validate_draft_obligation_coverage,
)
from test_case_agent.review_cycle.prepared_package import load_obligations
from test_case_agent.review_cycle.production_tc_gate import (
    validate_production_tc_content,
    validate_production_tc_draft,
)
from test_case_agent.review_cycle.source_model_adequacy import (
    evaluate_exact_length_adequacy,
)
from scripts.repair_autofin_client_addresses_v17_findings import (
    apply_review_finding_repairs,
)


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "AutoFin"
REFERENCE = FT_ROOT / "work" / "vendor-references" / "dadata-reference.md"
FMS_REFERENCE = (
    FT_ROOT / "work" / "vendor-references" / "dadata-fms-unit-reference.md"
)
DADATA_FIXTURE_ROOT = FT_ROOT / "work" / "vendor-references" / "dadata-fixtures"
DADATA_FIXTURE_CATALOG = (
    FT_ROOT / "work" / "vendor-references" / "dadata-fixture-catalog.md"
)
UI_NOTES = FT_ROOT / "work" / "ui-automation-prep" / "UI-AGENT-NOTES.md"
ADDRESS_CLARIFICATIONS = (
    FT_ROOT
    / "support"
    / "PostFinal-v2"
    / "client-addresses-approved-clarifications-v3.md"
)
PASSPORT_CLARIFICATIONS = (
    FT_ROOT
    / "support"
    / "PostFinal-v2"
    / "passport-current-and-previous-approved-clarifications.md"
)
ADDRESS_V11_CONFIG_ROOT = (
    ROOT
    / "evals"
    / "full-production-benchmark"
    / "configs"
    / "postfinal-v2-client-addresses-v11"
)
ADDRESS_V15_CONFIG_ROOT = (
    ROOT
    / "evals"
    / "full-production-benchmark"
    / "configs"
    / "postfinal-v2-client-addresses-v15"
)
ADDRESS_V16_CONFIG_ROOT = (
    ROOT
    / "evals"
    / "full-production-benchmark"
    / "configs"
    / "postfinal-v2-client-addresses-v16"
)
PASSPORT_CONFIG_ROOT = (
    ROOT
    / "evals"
    / "full-production-benchmark"
    / "configs"
    / "postfinal-v2-passport-current-and-previous-v4"
)
ADDRESS_REMEDIATION_HANDOFF = (
    FT_ROOT
    / "work"
    / "stage-handoffs"
    / "101-application-card-client-addresses-v17-complete-remediation"
)
ADDRESS_FIXTURE_HANDOFF = (
    FT_ROOT
    / "work"
    / "stage-handoffs"
    / "102-application-card-client-addresses-v19-dadata-fixture-contract"
)
ADDRESS_V17_SHADOW = (
    FT_ROOT
    / "test-cases"
    / "4.3-application-card-client-addresses-shadow-20260721-v17-complete-remediation.md"
)
ADDRESS_V18_CYCLE = (
    FT_ROOT
    / "work"
    / "review-cycles"
    / "application-card-client-addresses-v18-live-qualification-20260721"
)
ADDRESS_V22_CYCLE = (
    FT_ROOT
    / "work"
    / "review-cycles"
    / "application-card-client-addresses-v22-clean-20260721-turn-019f83f4"
)
ADDRESS_V23_CYCLE = (
    FT_ROOT
    / "work"
    / "review-cycles"
    / "application-card-client-addresses-v23-targeted-repair-20260721"
)
ADDRESS_V24_CYCLE = (
    FT_ROOT
    / "work"
    / "review-cycles"
    / "application-card-client-addresses-v24-two-case-repair-20260721"
)


class AutoFinDaDataReferenceTests(unittest.TestCase):
    def test_verified_positive_fixtures_are_exact_reproducible_and_secret_free(self) -> None:
        expected = {
            "FX-DADATA-ADDR-POS-001": {
                "suggestion": "г Самара, ул Авроры, д 7, кв 12",
                "components": {
                    "postal_code": "443017",
                    "region_with_type": "Самарская обл",
                    "city_with_type": "г Самара",
                    "street_with_type": "ул Авроры",
                    "house": "7",
                    "flat": "12",
                },
                "sha256": "1e889abe30cd94b7f83fd847167e9848472a4837bf2a88978c56f53e45b7058a",
            },
            "FX-DADATA-REGION-POS-001": {
                "suggestion": "Саратовская обл",
                "components": {"region_with_type": "Саратовская обл"},
                "sha256": "1a6cffc2b87187995bd90db4e4acbae13dbadc9812cf56a5aa2d0906d7d120d3",
            },
        }
        catalog = DADATA_FIXTURE_CATALOG.read_text(encoding="utf-8")

        for fixture_id, fixture_expected in expected.items():
            with self.subTest(fixture_id=fixture_id):
                response_path = DADATA_FIXTURE_ROOT / f"{fixture_id}.response.json"
                verification_path = DADATA_FIXTURE_ROOT / f"{fixture_id}.verification.json"
                response_bytes = response_path.read_bytes()
                response = json.loads(response_bytes)
                verification_text = verification_path.read_text(encoding="utf-8")
                verification = json.loads(verification_text)

                self.assertEqual(
                    fixture_expected["sha256"],
                    hashlib.sha256(response_bytes).hexdigest(),
                )
                self.assertEqual("verified", verification["status"])
                self.assertEqual(fixture_id, verification["fixture_id"])
                self.assertEqual(
                    fixture_expected["suggestion"],
                    verification["expected_response"]["exact_suggestion"],
                )
                self.assertEqual(
                    fixture_expected["components"],
                    verification["expected_response"]["exact_components"],
                )
                self.assertEqual(2, verification["verification"]["attempt_count"])
                self.assertTrue(verification["verification"]["all_http_200"])
                self.assertTrue(
                    verification["verification"]["all_responses_identical"]
                )
                suggestion = next(
                    item
                    for item in response["suggestions"]
                    if item["value"] == fixture_expected["suggestion"]
                )
                for component, value in fixture_expected["components"].items():
                    self.assertEqual(value, suggestion["data"][component])
                lowered = verification_text.lower()
                for forbidden_name in ("authorization", "api_key", "secret", "token"):
                    self.assertNotIn(forbidden_name, lowered)
                for env_name in ("DADATA_API_KEY", "DADATA_SECRET_KEY"):
                    secret_value = os.environ.get(env_name)
                    if secret_value:
                        self.assertNotIn(secret_value, verification_text)
                self.assertIn(f"`{fixture_id}`", catalog)
                self.assertIn(fixture_expected["sha256"], catalog)

    def test_verified_fms_fixture_is_exact_reproducible_and_secret_free(self) -> None:
        fixture_id = "FX-DADATA-FMS-POS-001"
        fixture_root = DADATA_FIXTURE_ROOT / fixture_id
        response_path = fixture_root / f"{fixture_id}.response.json"
        verification_path = fixture_root / f"{fixture_id}.verification.json"
        response_bytes = response_path.read_bytes()
        response = json.loads(response_bytes)
        verification_text = verification_path.read_text(encoding="utf-8")
        verification = json.loads(verification_text)

        self.assertEqual(
            "5575e4fbb9e28df33d8826a00580594eccde839bb6d625bfa84a6bf53d2bf90e",
            hashlib.sha256(response_bytes).hexdigest(),
        )
        self.assertEqual("verified", verification["status"])
        self.assertEqual(fixture_id, verification["fixture_id"])
        self.assertEqual(
            "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/fms_unit",
            verification["request"]["endpoint"],
        )
        self.assertEqual("772-053", verification["request"]["parameters"]["query"])
        self.assertEqual(
            "ОВД ЗЮЗИНО Г. МОСКВЫ",
            verification["expected_response"]["exact_suggestion"],
        )
        self.assertEqual(
            {
                "code": "772-053",
                "name": "ОВД ЗЮЗИНО Г. МОСКВЫ",
                "region_code": "77",
                "type": "2",
            },
            verification["expected_response"]["exact_components"],
        )
        self.assertEqual(2, verification["expected_response"]["minimum_suggestion_count"])
        self.assertEqual(2, verification["verification"]["attempt_count"])
        self.assertTrue(verification["verification"]["all_responses_identical"])
        self.assertTrue(
            verification["verification"]["all_minimum_suggestion_count_matched"]
        )
        self.assertGreaterEqual(len(response["suggestions"]), 2)
        exact = next(
            item
            for item in response["suggestions"]
            if item["value"] == "ОВД ЗЮЗИНО Г. МОСКВЫ"
        )
        for component, value in verification["expected_response"][
            "exact_components"
        ].items():
            self.assertEqual(value, exact["data"][component])

        persisted_text = response_path.read_text(encoding="utf-8") + verification_text
        lowered = persisted_text.lower()
        for forbidden_name in ("authorization", "api_key", "secret", "token"):
            self.assertNotIn(forbidden_name, lowered)
        for env_name in ("DADATA_API_KEY", "DADATA_SECRET_KEY"):
            secret_value = os.environ.get(env_name)
            if secret_value:
                self.assertNotIn(secret_value, persisted_text)

        catalog = DADATA_FIXTURE_CATALOG.read_text(encoding="utf-8")
        self.assertIn(f"`{fixture_id}`", catalog)
        self.assertIn(verification["response_sha256"], catalog)
        reference = FMS_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("`CLR-PASS-002`", reference)
        self.assertIn("`772-053`", reference)
        clarification = PASSPORT_CLARIFICATIONS.read_text(encoding="utf-8")
        self.assertIn("`CLR-PASS-002`", clarification)
        self.assertIn("Публичная документация DaData", clarification)

    def test_passport_profile_is_source_only_hash_bound_and_fresh(self) -> None:
        config_path = PASSPORT_CONFIG_ROOT / "shadow-benchmark-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        template = json.loads(
            (PASSPORT_CONFIG_ROOT / "bounded-context-template.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            "postfinal-v2-passport-current-and-previous-v4",
            config["benchmark_id"],
        )
        self.assertEqual(
            "work/stage-handoffs/114-application-card-passport-current-and-previous-postfinal-v2",
            config["outputs"]["handoff_dir"],
        )
        self.assertEqual(35, len(template["source_rows"]))
        self.assertEqual(31, len(template["parity"]))
        self.assertEqual(4, len(template["approved_clarifications"]))
        self.assertEqual(1, template["scope_execution_facts"]["internal_package_count"])
        self.assertEqual(49, config["semantic_sharding"]["max_semantic_weight"])
        issue_date_row = next(
            item for item in template["source_rows"] if item["source_row_id"] == "SRC-026"
        )
        self.assertEqual("Дата выдачи", issue_date_row["field_or_action"])
        binding = template["external_dictionary_bindings"][0]
        self.assertEqual("подразделения, выдавшие паспорт", binding["dictionary_name"])
        self.assertEqual(["SRC-023"], binding["source_row_ids"])
        self.assertEqual({"query": "772-053"}, binding["query_parameters"])
        model_inputs = [*config["source_files"]] + [
            item["path"] for item in config["scope_inputs"]
        ]
        for forbidden in ("test-cases/", "stage-handoffs/", "review-cycles/"):
            self.assertFalse(any(forbidden in item for item in model_inputs))
        serialized = json.dumps(template, ensure_ascii=False)
        self.assertNotIn("AutoFinPreFinal", serialized)
        self.assertNotIn("14-application-card-passport", serialized)
        for relative_path, expected_hash in config["expected_sha256"].items():
            self.assertEqual(
                expected_hash,
                hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest(),
                relative_path,
            )

    def test_verified_negative_fixture_is_reproducible_and_secret_free(self) -> None:
        response_path = DADATA_FIXTURE_ROOT / "FX-DADATA-ADDR-NEG-001.response.json"
        verification_path = (
            DADATA_FIXTURE_ROOT / "FX-DADATA-ADDR-NEG-001.verification.json"
        )
        response_bytes = response_path.read_bytes()
        verification_text = verification_path.read_text(encoding="utf-8")
        verification = json.loads(verification_text)

        self.assertEqual({"suggestions": []}, json.loads(response_bytes))
        self.assertEqual(
            "8e5e36d9bf781113e259d054939c9dfefe858cc0240844aa224405d7a69f482e",
            hashlib.sha256(response_bytes).hexdigest(),
        )
        self.assertEqual("verified", verification["status"])
        self.assertEqual("FX-DADATA-ADDR-NEG-001", verification["fixture_id"])
        self.assertEqual(
            "ZZZNOADDRESS7F3A9C2E20260721",
            verification["request"]["parameters"]["query"],
        )
        self.assertEqual(2, verification["verification"]["attempt_count"])
        self.assertTrue(verification["verification"]["all_http_200"])
        self.assertTrue(
            verification["verification"]["all_exact_empty_suggestions"]
        )
        for attempt in verification["verification"]["attempts"]:
            self.assertEqual(200, attempt["http_status"])
            self.assertTrue(attempt["exact_empty_suggestions"])
            self.assertEqual(verification["response_sha256"], attempt["response_sha256"])

        lowered = verification_text.lower()
        for forbidden_name in ("authorization", "api_key", "secret", "token"):
            self.assertNotIn(forbidden_name, lowered)
        for env_name in ("DADATA_API_KEY", "DADATA_SECRET_KEY"):
            secret_value = os.environ.get(env_name)
            if secret_value:
                self.assertNotIn(secret_value, verification_text)

        catalog = DADATA_FIXTURE_CATALOG.read_text(encoding="utf-8")
        self.assertIn("`FX-DADATA-ADDR-NEG-001`", catalog)
        self.assertIn("`verified-live-response`", catalog)
        self.assertIn(verification["response_sha256"], catalog)

    def test_fixture_lifecycle_is_verified_once_without_automatic_release_call(self) -> None:
        catalog = DADATA_FIXTURE_CATALOG.read_text(encoding="utf-8")
        canonical_format = (
            ROOT / "references" / "agent" / "fixture-catalog-format.md"
        ).read_text(encoding="utf-8")

        for text in (catalog, canonical_format):
            self.assertIn("`verified-once / revalidate-on-failure`", text)
            self.assertNotIn("recheck before release", text)
            self.assertNotIn("stale after 7 days", text)
            self.assertNotIn("recheck_before_release: true", text)
            self.assertNotIn("stale_after_days:", text)

        self.assertIn(
            "не выполняют автоматические live-вызовы DaData",
            catalog,
        )
        self.assertIn("Повторная live-проверка не является release-preflight gate", catalog)

        release_entrypoints = (
            ROOT / "scripts" / "run_lean_production_iteration.py",
            ROOT / "scripts" / "run_standard_production_iteration.py",
            ROOT / "scripts" / "codex_exec_review_cycle_runner.py",
            ROOT / "scripts" / "review_cycle_backend_dispatcher.py",
            ROOT / "test_case_agent" / "review_cycle" / "prepared_compiler.py",
        )
        for entrypoint in release_entrypoints:
            source = entrypoint.read_text(encoding="utf-8")
            with self.subTest(entrypoint=entrypoint.name):
                self.assertNotIn("verify_dadata_negative_fixture", source)
                self.assertNotIn("verify_dadata_positive_fixture", source)
                self.assertNotIn("DADATA_API_KEY", source)

    def test_v19_fixture_contract_rejects_old_shadow_and_accepts_offline_golden(self) -> None:
        old_result = validate_production_tc_draft(draft_path=ADDRESS_V17_SHADOW)
        old_finding_ids = {item["id"] for item in old_result.findings}

        self.assertFalse(old_result.passed)
        self.assertEqual(37, old_result.calibration_candidate_count)
        self.assertIn("production-dadata-dynamic-fixture", old_finding_ids)
        self.assertIn("production-dadata-fixture-binding-missing", old_finding_ids)
        self.assertIn("production-process-marker-in-title", old_finding_ids)

        golden_result = validate_production_tc_draft(
            draft_path=ADDRESS_FIXTURE_HANDOFF / "offline-golden-fragment.md"
        )
        self.assertTrue(golden_result.passed, golden_result.findings)
        self.assertEqual(2, golden_result.execution_ready_count)
        self.assertEqual(1, golden_result.calibration_candidate_count)
        self.assertEqual(
            "ft-first-reviewed-with-calibration-pending",
            golden_result.as_dict()["suite_readiness"],
        )

    def test_package_notes_conditionally_route_dadata_scopes(self) -> None:
        notes = (FT_ROOT / "AGENT-NOTES.md").read_text(encoding="utf-8")

        self.assertIn("work/vendor-references/dadata-reference.md", notes)
        self.assertIn("DOCX ФТ -> подтверждённые support/clarifications", notes)
        self.assertIn("vendor reference -> наблюдение UI", notes)
        self.assertIn("mismatch-ft-ui", notes)

    def test_reference_has_limited_dynamic_dictionary_authority_and_is_source_pinned(self) -> None:
        text = REFERENCE.read_text(encoding="utf-8")

        self.assertIn("`reference_kind`: `external-vendor-reference`", text)
        self.assertIn(
            "`authority_for_autofin_requirements`: `limited-user-confirmed`",
            text,
        )
        self.assertIn("`external-dynamic-dictionary`", text)
        self.assertIn("`from_bound=region`, `to_bound=region`", text)
        self.assertIn("`CLR-ADDR-004`", text)
        self.assertIn("`checked_at`: `2026-07-19`", text)
        for url in (
            "https://dadata.ru/api/suggest/address/",
            "https://dadata.ru/api/suggest/name/",
            "https://dadata.ru/api/suggest/fms_unit/",
            "https://dadata.ru/api/suggest/party/",
        ):
            self.assertIn(url, text)

    def test_reference_keeps_vendor_defaults_separate_from_autofin_contract(self) -> None:
        text = REFERENCE.read_text(encoding="utf-8")

        for anchor in (
            "`BSR 116`, `BSR 141`",
            "`BSR 118`, `BSR 143`",
            "`BSR 119`, `BSR 144`",
            "`BSR 94`",
            "`BSR 95`",
            "`BSR 265`",
            "`BSR 266`",
        ):
            self.assertIn(anchor, text)
        self.assertIn("calibration questions, а не готовые expected results", text)
        self.assertIn("Не считать текущее UI-поведение нормативным", text)

    def test_ui_notes_require_normal_path_and_evidence(self) -> None:
        text = UI_NOTES.read_text(encoding="utf-8")

        self.assertIn("vendor-references/dadata-reference.md", text)
        self.assertIn("normal UI path", text)
        self.assertIn("screenshot и trace", text)
        self.assertIn("FT-first baseline не перезаписывай", text)

    def test_bsr_324_excludes_only_internal_kladr_effect(self) -> None:
        text = ADDRESS_CLARIFICATIONS.read_text(encoding="utf-8")

        self.assertIn("`CLR-ADDR-005`", text)
        self.assertIn("Внутреннее заполнение kladr по BSR 324", text)
        self.assertIn("`not-applicable / out-of-project`", text)
        self.assertIn("раскладывание выбранного в DaData адреса", text)
        self.assertIn("остаётся testable", text)
        self.assertIn("не создаёт TC, активный coverage gap", text)

    def test_v11_context_keeps_visible_bsr_324_effect_and_excludes_kladr(self) -> None:
        template_path = ADDRESS_V11_CONFIG_ROOT / "bounded-context-template.json"
        template = json.loads(template_path.read_text(encoding="utf-8"))

        clarification_source = next(
            item for item in template["sources"] if item["role"] == "approved-clarification"
        )
        self.assertEqual(
            "fts/AutoFin/support/PostFinal-v2/client-addresses-approved-clarifications-v3.md",
            clarification_source["path"],
        )
        clarification = next(
            item
            for item in template["approved_clarifications"]
            if item["clarification_id"] == "CLR-ADDR-005"
        )
        self.assertEqual(["BSR 324"], clarification["requirement_codes"])
        self.assertEqual(
            hashlib.sha256(clarification["exact_answer"].encode("utf-8")).hexdigest(),
            clarification["exact_answer_sha256"],
        )
        dependency = next(
            item for item in template["expected_dependencies"] if item["name"] == "kladr"
        )
        self.assertEqual("scope-excluded", dependency["resolution"])
        self.assertEqual([], dependency["target_source_row_ids"])
        self.assertTrue(any("раскладывание" in item for item in template["scope_boundary"]["include"]))
        self.assertTrue(any("kladr" in item for item in template["scope_boundary"]["exclude"]))

    def test_v11_config_hash_binds_new_clarification_and_context(self) -> None:
        config = json.loads(
            (ADDRESS_V11_CONFIG_ROOT / "shadow-benchmark-config.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("postfinal-v2-client-addresses-v11", config["benchmark_id"])
        self.assertEqual(
            "support/PostFinal-v2/client-addresses-approved-clarifications-v3.md",
            config["scope_inputs"][0]["path"],
        )
        for relative_path, expected_hash in config["expected_sha256"].items():
            actual_hash = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(expected_hash, actual_hash, relative_path)

    def test_v15_clean_profile_uses_fresh_outputs_and_hash_bound_launch(self) -> None:
        config_path = ADDRESS_V15_CONFIG_ROOT / "shadow-benchmark-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual("postfinal-v2-client-addresses-v15", config["benchmark_id"])
        self.assertEqual(
            "work/stage-handoffs/96-application-card-client-addresses-v15",
            config["outputs"]["handoff_dir"],
        )
        self.assertEqual(
            "work/review-cycles/application-card-client-addresses-v15-20260720",
            config["outputs"]["cycle_dir"],
        )
        self.assertEqual(
            "test-cases/4.3-application-card-client-addresses-shadow-20260720-v15.md",
            config["outputs"]["final_artifact"],
        )
        for relative_path, expected_hash in config["expected_sha256"].items():
            actual_hash = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(expected_hash, actual_hash, relative_path)
        config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
        launch = (ADDRESS_V15_CONFIG_ROOT / "launch-new-session.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(config_hash, launch)
        self.assertNotIn("94-application-card-client-addresses-v14", launch)

    def test_v16_clean_profile_is_immutable_and_has_distinct_outputs(self) -> None:
        config_path = ADDRESS_V16_CONFIG_ROOT / "shadow-benchmark-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual("postfinal-v2-client-addresses-v16", config["benchmark_id"])
        self.assertEqual(
            "work/stage-handoffs/97-application-card-client-addresses-v16",
            config["outputs"]["handoff_dir"],
        )
        self.assertEqual(
            "work/review-cycles/application-card-client-addresses-v16-20260720",
            config["outputs"]["cycle_dir"],
        )
        self.assertEqual(
            "test-cases/4.3-application-card-client-addresses-shadow-20260720-v16.md",
            config["outputs"]["final_artifact"],
        )
        for relative_path, expected_hash in config["expected_sha256"].items():
            actual_hash = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(expected_hash, actual_hash, relative_path)
        config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
        for launch_name in ("launch-new-session.md", "launch-controller-session.md"):
            launch = (ADDRESS_V16_CONFIG_ROOT / launch_name).read_text(
                encoding="utf-8"
            )
            self.assertIn(config_hash, launch)
            self.assertIn("warm-cache", launch)
            self.assertNotIn("96-application-card-client-addresses-v15", launch)

    def test_address_boundary_remediation_has_distinct_exact_length_classes(self) -> None:
        report = evaluate_exact_length_adequacy(
            ADDRESS_REMEDIATION_HANDOFF / "source-assertions.json"
        )
        coverage = (
            ADDRESS_REMEDIATION_HANDOFF / "coverage-obligation-table.md"
        ).read_text(encoding="utf-8")

        self.assertTrue(report["passed"], report)
        self.assertEqual(2, report["rule_count"])
        for obligation_id in ("OBL-112", "OBL-113", "OBL-114"):
            self.assertIn(f"`{obligation_id}`", coverage)
        self.assertGreaterEqual(
            coverage.count("`ui-calibration-required`"),
            3,
        )
        review = json.loads(
            (ADDRESS_REMEDIATION_HANDOFF / "source-assertion-review.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("accepted", review["decision"])
        self.assertEqual(
            "7e25342fda6b9f48acea310fb11c8d04958aa49ec00e57afae47528a080ddd08",
            review["manifest_digest"],
        )

    def test_address_complete_remediation_is_blocked_before_writer_without_dadata_fixtures(self) -> None:
        review_cycles = FT_ROOT / "work" / "review-cycles"
        with tempfile.TemporaryDirectory(
            prefix="address-h101-compile-", dir=review_cycles
        ) as raw:
            cycle = Path(raw)
            with self.assertRaises(PreparedCompilerDiagnostic) as caught:
                compile_workflow_package(
                    workflow_state=ADDRESS_REMEDIATION_HANDOFF / "workflow-state.yaml",
                    repo_root=ROOT,
                    output_root=cycle / "prepared-input" / "WP-01",
                    package_id="WP-01",
                    attempt_root=cycle / "attempts" / "writer-r1" / "attempt-001",
                    expected_ft_slug="AutoFin",
                    section_id="4.3",
                )
            self.assertEqual(
                "external-dynamic-fixture-binding-missing",
                caught.exception.code,
            )

    def test_v18_saved_draft_has_only_the_real_tc105_obligation_finding(self) -> None:
        result = validate_draft_obligation_coverage(
            draft_path=(
                ADDRESS_V18_CYCLE
                / "attempts"
                / "writer-r1"
                / "attempt-001"
                / "stage-output"
                / "draft.md"
            ),
            obligations_path=(
                ADDRESS_V18_CYCLE
                / "prepared-input"
                / "WP-01"
                / "atomic-obligations.json"
            ),
            strict_runtime_contract=True,
        )
        primary_findings = [
            item
            for item in result.findings
            if item["id"] != "missing-testable-obligation-coverage"
        ]

        self.assertEqual(1, len(primary_findings), primary_findings)
        self.assertEqual("TC-105", primary_findings[0]["tc_id"])
        self.assertEqual(
            "observable-oracle-contract-mismatch",
            primary_findings[0]["id"],
        )

    def test_v22_saved_draft_offline_qualification_is_bounded_to_real_repairs(self) -> None:
        draft_path = (
            ADDRESS_V22_CYCLE
            / "attempts"
            / "writer-r1"
            / "attempt-001"
            / "stage-output"
            / "draft.md"
        )
        obligations_path = (
            ADDRESS_V22_CYCLE
            / "prepared-input"
            / "WP-01"
            / "atomic-obligations.json"
        )
        obligations = load_obligations(obligations_path)
        projected, _ = materialize_draft_reference_fixtures(
            draft_path.read_text(encoding="utf-8"), obligations
        )
        projected, _ = materialize_draft_dictionary_projections(
            projected, obligations
        )
        with tempfile.TemporaryDirectory(prefix="autofin-v22-offline-") as raw:
            projected_path = Path(raw) / "projected-v22.md"
            projected_path.write_text(projected, encoding="utf-8")
            obligation_result = validate_draft_obligation_coverage(
                draft_path=projected_path,
                obligations_path=obligations_path,
                strict_runtime_contract=True,
            )
        self.assertTrue(obligation_result.passed, obligation_result.findings)

        production_result = validate_production_tc_content(
            projected,
            checked_path="saved-v22-offline-projection",
            approved_runtime_aliases={
                "Адрес постоянной регистрации": "Адрес регистрации",
            },
        )
        actual_findings = sorted(
            (item["tc_id"], item["id"])
            for item in production_result.findings
        )
        self.assertEqual(
            [
                ("TC-010", "production-unobservable-address-decomposition"),
                ("TC-023", "production-nonconcrete-runtime-value"),
                ("TC-024", "production-internal-fixture-artifact-leak"),
                ("TC-048", "production-noncanonical-approved-alias"),
                ("TC-050", "production-noncanonical-approved-alias"),
                ("TC-051", "production-noncanonical-approved-alias"),
                ("TC-052", "production-noncanonical-approved-alias"),
                ("TC-053", "production-noncanonical-approved-alias"),
                ("TC-054", "production-noncanonical-approved-alias"),
                ("TC-055", "production-noncanonical-approved-alias"),
                ("TC-066", "production-unobservable-address-decomposition"),
                ("TC-080", "production-dadata-dynamic-fixture"),
                ("TC-080", "production-internal-fixture-artifact-leak"),
                ("TC-111", "production-internal-fixture-artifact-leak"),
                ("TC-111", "production-out-of-scope-diagnostic-leak"),
            ],
            actual_findings,
        )

    def test_v23_saved_draft_offline_qualification_includes_later_reviewer_findings(self) -> None:
        draft_path = (
            ADDRESS_V23_CYCLE
            / "attempts"
            / "writer-r1"
            / "attempt-001"
            / "stage-output"
            / "draft.md"
        )
        obligations_path = (
            ADDRESS_V23_CYCLE
            / "prepared-input"
            / "WP-01"
            / "atomic-obligations.json"
        )
        obligation_result = validate_draft_obligation_coverage(
            draft_path=draft_path,
            obligations_path=obligations_path,
            strict_runtime_contract=True,
        )
        self.assertTrue(obligation_result.passed, obligation_result.findings)

        production_result = validate_production_tc_draft(draft_path=draft_path)
        self.assertEqual(
            [
                ("TC-048", "production-calibration-question-missing"),
                ("TC-048", "production-process-marker-in-title"),
                ("TC-054", "production-calibration-question-missing"),
                ("TC-054", "production-non-reproducible-precondition"),
                ("TC-054", "production-process-marker-in-title"),
                ("TC-066", "production-unobservable-address-decomposition"),
                ("TC-080", "production-ambiguous-duplicate-execution-path"),
            ],
            sorted(
                (item["tc_id"], item["id"])
                for item in production_result.findings
            ),
        )

    def test_v24_saved_draft_offline_qualification_matches_reviewer_findings(self) -> None:
        draft_path = (
            ADDRESS_V24_CYCLE
            / "attempts"
            / "writer-r1"
            / "attempt-001"
            / "stage-output"
            / "draft.md"
        )
        obligations_path = (
            ADDRESS_V24_CYCLE
            / "prepared-input"
            / "WP-01"
            / "atomic-obligations.json"
        )
        obligation_result = validate_draft_obligation_coverage(
            draft_path=draft_path,
            obligations_path=obligations_path,
            strict_runtime_contract=True,
        )
        self.assertTrue(obligation_result.passed, obligation_result.findings)

        production_result = validate_production_tc_draft(draft_path=draft_path)
        self.assertEqual(
            [
                ("TC-066", "production-unobservable-address-decomposition"),
                ("TC-080", "production-ambiguous-duplicate-execution-path"),
            ],
            sorted(
                (item["tc_id"], item["id"])
                for item in production_result.findings
            ),
        )

    def test_v17_repair_binds_factual_address_branches_before_writer(self) -> None:
        original = json.loads(
            (
                FT_ROOT
                / "work"
                / "stage-handoffs"
                / "99-application-card-client-addresses-v16-source-review-repair"
                / "semantic-design.json"
            ).read_text(encoding="utf-8")
        )
        repaired = apply_review_finding_repairs(original)
        assertions = {
            assertion["assertion_id"]: assertion
            for source_design in repaired["source_designs"]
            for assertion in source_design["assertions"]
        }
        obligations = {
            item["obligation_id"]: item for item in repaired["obligations"]
        }

        for assertion_id in (
            "ASSERT-102",
            "ASSERT-103",
            "ASSERT-104",
            "ASSERT-105",
            "ASSERT-128",
        ):
            projection = json.dumps(assertions[assertion_id], ensure_ascii=False)
            self.assertIn("фактическ", projection.lower())
        for obligation_id in (
            "OBL-085",
            "OBL-086",
            "OBL-087",
            "OBL-088",
            "OBL-111",
        ):
            projection = json.dumps(obligations[obligation_id], ensure_ascii=False)
            self.assertIn("фактическ", projection.lower())
        self.assertIn("OBL-112", obligations)
        self.assertIn("OBL-113", obligations)
        self.assertIn("OBL-114", obligations)


if __name__ == "__main__":
    unittest.main()
