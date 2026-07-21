from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import start_full_process_observation
from test_case_agent.review_cycle.prepared_compiler import (
    _SOURCE_SELECTION_ROLE_COMPATIBILITY,
)


class FullProcessObservationBootstrapTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        ft_root = root / "fts" / "AutoFin"
        source_root = ft_root / "source" / "PostFinal-v2"
        source_root.mkdir(parents=True)
        for suffix in ("docx", "xhtml", "pdf"):
            (source_root / f"PostFinal-v2.{suffix}").write_bytes(suffix.encode("ascii"))
        support_root = ft_root / "support" / "PostFinal-v2"
        support_root.mkdir(parents=True)
        (support_root / "dictionary.md").write_text("dictionary\n", encoding="utf-8")
        (support_root / "clarification.md").write_text(
            "approved clarification\n", encoding="utf-8"
        )
        (ft_root / "AGENT-NOTES.md").write_text("package notes\n", encoding="utf-8")
        mockup_root = ft_root / "mockups" / "PostFinal-v2"
        mockup_root.mkdir(parents=True)
        (mockup_root / "screen.jpg").write_bytes(b"image")
        scripts = root / "scripts"
        scripts.mkdir()
        (scripts / "workflow_wall_clock.py").write_text("# recorder\n", encoding="utf-8")
        (scripts / "run_standard_production_iteration.py").write_text(
            "# wrapper\n", encoding="utf-8"
        )
        config = root / "evals" / "config.json"
        config.parent.mkdir()
        config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "benchmark_id": "postfinal-v2-employment-main-work",
                    "ft_root": "fts/AutoFin",
                    "ft_slug": "AutoFin",
                    "scope_slug": "employment-main-work",
                    "source_files": [
                        "source/PostFinal-v2/PostFinal-v2.docx",
                        "source/PostFinal-v2/PostFinal-v2.xhtml",
                        "source/PostFinal-v2/PostFinal-v2.pdf",
                    ],
                    "scope_inputs": [
                        {
                            "path": "support/PostFinal-v2/dictionary.md",
                            "role": "support",
                            "manifest_binding": "supporting-material",
                        },
                        {
                            "path": "support/PostFinal-v2/clarification.md",
                            "role": "approved-clarification",
                            "manifest_binding": "approved-clarification",
                        },
                        {
                            "path": "AGENT-NOTES.md",
                            "role": "mandatory-package-context",
                            "manifest_binding": "supporting-material",
                        },
                        {
                            "path": "mockups/PostFinal-v2/screen.jpg",
                            "role": "mockup",
                            "manifest_binding": "mockup",
                        },
                    ],
                    "observation_root": "work/full-process-observation",
                    "recorder_entrypoint": "scripts/workflow_wall_clock.py",
                    "production_wrapper": "scripts/run_standard_production_iteration.py",
                    "measurement_mode": "observational",
                }
            ),
            encoding="utf-8",
        )
        return config

    def test_resolve_plan_binds_autofin_and_exact_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=config,
                request_started_epoch_ms=1000,
                codex_turn_id="turn-001",
            )

            self.assertEqual("AutoFin", plan.ft_slug)
            self.assertEqual((root / "fts" / "AutoFin").resolve(), plan.ft_root)
            self.assertEqual(
                (
                    root
                    / "fts"
                    / "AutoFin"
                    / "work"
                    / "full-process-observation"
                    / "turn-001"
                    / "workflow-performance.json"
                ).resolve(),
                plan.timer,
            )
            self.assertEqual(
                (root / "scripts" / "workflow_wall_clock.py").resolve(),
                plan.recorder_entrypoint,
            )
            self.assertEqual(
                (root / "scripts" / "run_standard_production_iteration.py").resolve(),
                plan.production_wrapper,
            )
            self.assertEqual(4, len(plan.scope_inputs))
            self.assertEqual("support", plan.scope_inputs[0].role)
            self.assertEqual("approved-clarification", plan.scope_inputs[1].role)
            self.assertEqual("mandatory-package-context", plan.scope_inputs[2].role)
            self.assertEqual("mockup", plan.scope_inputs[3].role)
            components = {
                item["component"] for item in plan.routing_preflight_breakdown
            }
            self.assertEqual(
                {
                    "request-metadata-read",
                    "instruction-loading",
                    "environment-probe",
                    "workspace-check",
                    "ft-config-selection",
                    "source-registry-check",
                    "hash-verification",
                    "external-backend-wait",
                    "other-orchestration",
                },
                components,
            )
            breakdown = {
                item["component"]: item for item in plan.routing_preflight_breakdown
            }
            for component in (
                "request-metadata-read",
                "instruction-loading",
                "environment-probe",
            ):
                self.assertEqual("unavailable", breakdown[component]["duration_ms"])
                self.assertEqual(
                    "included-in-residual", breakdown[component]["status"]
                )

    def test_bootstrap_source_bindings_match_downstream_compiler_contract(self) -> None:
        configured = {
            role: binding
            for role, binding in start_full_process_observation.PRIMARY_SOURCE_BINDINGS.values()
        }
        configured.update(
            {
                role: binding_and_location[0]
                for role, binding_and_location in (
                    start_full_process_observation.SCOPE_INPUT_BINDINGS.items()
                )
            }
        )

        for role, binding in configured.items():
            self.assertIn(role, _SOURCE_SELECTION_ROLE_COMPATIBILITY)
            self.assertIn(binding, _SOURCE_SELECTION_ROLE_COMPATIBILITY[role])

    def test_rejects_ft_slug_inferred_from_document_name(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            payload["ft_slug"] = "postfinal-v2"
            config.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "does not match ft_root",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1000,
                    codex_turn_id="turn-001",
                )

    def test_rejects_incomplete_primary_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            (root / "fts" / "AutoFin" / "source" / "PostFinal-v2" / "PostFinal-v2.xhtml").unlink()

            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "configured source file does not exist",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1000,
                    codex_turn_id="turn-001",
                )

    def test_rejects_mismatched_primary_source_names(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            source_root = root / "fts" / "AutoFin" / "source" / "PostFinal-v2"
            mismatched = source_root / "Other.xhtml"
            mismatched.write_text("xhtml", encoding="utf-8")
            payload = json.loads(config.read_text(encoding="utf-8"))
            payload["source_files"][1] = "source/PostFinal-v2/Other.xhtml"
            config.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "must be matching files",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1000,
                    codex_turn_id="turn-001",
                )

    def test_rejects_missing_or_out_of_package_scope_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            payload["scope_inputs"][0]["path"] = "support/PostFinal-v2/missing.md"
            config.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "configured scope input does not exist",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1000,
                    codex_turn_id="turn-001",
                )

            outside = root / "fts" / "AutoFin" / "source" / "not-support.md"
            outside.write_text("not support\n", encoding="utf-8")
            payload["scope_inputs"][0]["path"] = "source/not-support.md"
            config.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "scope input role 'support' must stay under",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1000,
                    codex_turn_id="turn-001",
                )

    def test_start_invokes_exact_recorder_and_writes_bound_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=config,
                request_started_epoch_ms=1000,
                codex_turn_id="turn-001",
            )

            def recorder(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                output = Path(command[command.index("--output") + 1])
                output.parent.mkdir(parents=True)
                output.write_text(
                    json.dumps(
                        {
                            "status": "running",
                            "ft_slug": "AutoFin",
                            "scope_slug": "employment-main-work",
                            "measurement_coverage": "request-received",
                        }
                    ),
                    encoding="utf-8",
                )
                self.assertEqual(
                    str((root / "scripts" / "workflow_wall_clock.py").resolve()),
                    command[1],
                )
                self.assertEqual("AutoFin", command[command.index("--ft-slug") + 1])
                return subprocess.CompletedProcess(command, 0, "{}", "")

            with patch(
                "scripts.start_full_process_observation.subprocess.run",
                side_effect=recorder,
            ):
                receipt = start_full_process_observation.start_observation(plan)

            self.assertEqual("started", receipt["status"])
            self.assertEqual("AutoFin", receipt["ft_slug"])
            self.assertEqual(
                "scripts/run_standard_production_iteration.py",
                receipt["production_wrapper"],
            )
            self.assertEqual(
                ["--context", "--handoff-dir", "--cycle-dir", "--final-artifact"],
                receipt["production_wrapper_invocation"][
                    "required_dynamic_arguments"
                ],
            )
            self.assertEqual(4, len(receipt["scope_input_inventory"]))
            self.assertEqual(
                "supporting-material",
                receipt["scope_input_inventory"][0]["manifest_binding"],
            )
            self.assertEqual(
                "approved-clarification",
                receipt["scope_input_inventory"][1]["role"],
            )
            source_registry = {
                item["role"]: item["manifest_binding"]
                for item in receipt["source_inventory"]
            }
            self.assertEqual(
                {
                    "main-ft-docx": "semantic-source-of-truth",
                    "main-ft-xhtml": "assertion-source",
                    "main-ft-pdf": "structural-visual-parity",
                },
                source_registry,
            )
            self.assertTrue(plan.receipt.is_file())

    def test_checked_in_postfinal_profile_validates_current_repository(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = (
            repo_root
            / "evals"
            / "full-production-benchmark"
            / "configs"
            / "postfinal-v2-employment-main-work.json"
        )
        plan = start_full_process_observation.resolve_plan(
            repo_root=repo_root,
            config_path=config,
            request_started_epoch_ms=1,
            codex_turn_id="validation-only-test-profile",
        )

        self.assertEqual("AutoFin", plan.ft_slug)
        self.assertEqual(2, plan.schema_version)
        self.assertEqual(
            start_full_process_observation._sha256(config), plan.config_sha256
        )
        self.assertEqual((repo_root / "fts" / "AutoFin").resolve(), plan.ft_root)
        self.assertEqual(
            (repo_root / "scripts" / "workflow_wall_clock.py").resolve(),
            plan.recorder_entrypoint,
        )
        self.assertEqual(5, len(plan.scope_inputs))
        self.assertEqual(
            "fts/AutoFin/support/PostFinal-v2/АФБ справочники 26.06.26.md",
            plan.scope_inputs[0].path.relative_to(repo_root).as_posix(),
        )
        self.assertEqual("approved-clarification", plan.scope_inputs[1].role)
        self.assertEqual("mandatory-package-context", plan.scope_inputs[2].role)
        self.assertEqual("mockup", plan.scope_inputs[3].role)
        self.assertEqual("mockup", plan.scope_inputs[4].role)
        self.assertEqual(13, len(plan.expected_sha256))
        pinned = {
            path.relative_to(repo_root).as_posix(): digest
            for path, digest in plan.expected_sha256
        }
        self.assertEqual(
            {
                *(path.relative_to(repo_root).as_posix() for path in plan.source_files),
                *(
                    item.path.relative_to(repo_root).as_posix()
                    for item in plan.scope_inputs
                ),
                "evals/full-production-benchmark/configs/postfinal-v2-employment-main-work/bounded-context-template.json",
                "evals/full-production-benchmark/configs/postfinal-v2-employment-main-work/source-row-extraction-spec.json",
                "evals/lean-production-benchmark/h70/bounded-evidence-docx.json",
                "evals/lean-production-benchmark/h70/bounded-evidence-pdf.json",
                "evals/full-production-benchmark/configs/postfinal-v2-employment-main-work/bounded-evidence-xhtml-boundary.json",
            },
            set(pinned),
        )
        self.assertEqual(
            (
                repo_root
                / "evals"
                / "full-production-benchmark"
                / "configs"
                / "postfinal-v2-employment-main-work"
                / "bounded-context-template.json"
            ).resolve(),
            plan.context_template,
        )
        self.assertEqual(
            (
                repo_root
                / "fts"
                / "AutoFin"
                / "work"
                / "stage-handoffs"
                / "73-employment-main-work-one-command"
            ).resolve(),
            plan.handoff_dir,
        )
        payload = start_full_process_observation.plan_payload(plan)
        self.assertEqual(plan.config_sha256, payload["config_sha256"])
        self.assertEqual(pinned, payload["expected_sha256"])
        self.assertEqual([], payload["production_wrapper_invocation"]["required_dynamic_arguments"])
        self.assertEqual(2, len([
            item
            for item in payload["production_wrapper_invocation"]["fixed_arguments"]
            if item == "--image"
        ]))

    def test_checked_in_client_addresses_profile_is_source_only_and_shadowed(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = (
            repo_root
            / "evals"
            / "full-production-benchmark"
            / "configs"
            / "postfinal-v2-client-addresses.json"
        )
        plan = start_full_process_observation.resolve_plan(
            repo_root=repo_root,
            config_path=config,
            request_started_epoch_ms=1,
            codex_turn_id="validation-only-client-addresses-profile",
        )

        self.assertEqual(2, plan.schema_version)
        self.assertEqual("application-card-client-addresses", plan.scope_slug)
        self.assertEqual(3, len(plan.scope_inputs))
        self.assertEqual(
            ["approved-clarification", "mandatory-package-context", "mockup"],
            [item.role for item in plan.scope_inputs],
        )
        self.assertEqual(11, len(plan.expected_sha256))
        model_inputs = [
            path.relative_to(repo_root).as_posix()
            for path in plan.source_files
        ] + [
            item.path.relative_to(repo_root).as_posix()
            for item in plan.scope_inputs
        ]
        for forbidden in (
            "/test-cases/",
            "/stage-handoffs/",
            "/review-cycles/",
            "/vendor-references/",
        ):
            self.assertFalse(any(forbidden in f"/{path}" for path in model_inputs))
        self.assertEqual(
            "4.3-application-card-client-addresses-shadow-20260719.md",
            plan.final_artifact.name,
        )

        template = json.loads(plan.context_template.read_text(encoding="utf-8"))
        self.assertEqual(44, len(template["source_rows"]))
        self.assertEqual(48, len(template["parity"]))
        self.assertEqual(
            "Адрес регистрации",
            template["dependency_aliases"]["Адрес постоянной регистрации"],
        )
        provenance = template["dependency_alias_provenance"][
            "Адрес постоянной регистрации"
        ]
        self.assertEqual("CLR-ADDR-002", provenance)
        clarification = plan.scope_inputs[0].path.read_text(encoding="utf-8")
        self.assertIn("`CLR-ADDR-002`", clarification)
        self.assertIn("`user-confirmed`", clarification)
        alias_dependency = next(
            item
            for item in template["expected_dependencies"]
            if item["name"] == "Адрес постоянной регистрации"
        )
        self.assertEqual("approved-alias", alias_dependency["resolution"])
        self.assertEqual(["SRC-019"], alias_dependency["target_source_row_ids"])

    def test_client_addresses_v2_excludes_project_wide_type_constraints(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = (
            repo_root
            / "evals"
            / "full-production-benchmark"
            / "configs"
            / "postfinal-v2-client-addresses-v2.json"
        )
        plan = start_full_process_observation.resolve_plan(
            repo_root=repo_root,
            config_path=config,
            request_started_epoch_ms=1,
            codex_turn_id="validation-only-client-addresses-v2-profile",
        )

        self.assertEqual("postfinal-v2-client-addresses-v2", plan.benchmark_id)
        self.assertEqual(11, len(plan.expected_sha256))
        self.assertEqual(
            "client-addresses-approved-clarifications-v2.md",
            plan.scope_inputs[0].path.name,
        )
        self.assertEqual(
            "4.3-application-card-client-addresses-shadow-20260719-v2.md",
            plan.final_artifact.name,
        )

        template = json.loads(plan.context_template.read_text(encoding="utf-8"))
        type_section_rows = [
            item
            for item in template["source_rows"]
            if 4 <= int(item["source_row_id"].removeprefix("SRC-")) <= 15
        ]
        self.assertEqual(12, len(type_section_rows))
        self.assertTrue(
            all(
                item["in_scope_hint"]
                == "no; user-confirmed out-of-project section CLR-ADDR-003"
                for item in type_section_rows
            )
        )
        self.assertTrue(
            all("context_relation_required" not in item for item in type_section_rows)
        )
        dependency_names = {
            item["name"] for item in template["expected_dependencies"]
        }
        self.assertTrue(
            {
                "Ограничение типа Текст",
                "Ограничение типа Список",
                "Ограничение логического типа",
                "Значения по умолчанию NULL",
            }.isdisjoint(dependency_names)
        )
        clarification = next(
            item
            for item in template["approved_clarifications"]
            if item["clarification_id"] == "CLR-ADDR-003"
        )
        self.assertEqual("source-context", clarification["binding_scope"])
        self.assertEqual(
            [item["source_row_id"] for item in type_section_rows],
            clarification["source_row_ids"],
        )

    def test_client_addresses_v3_is_fresh_and_preserves_v2_scope_contract(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = (
            repo_root
            / "evals"
            / "full-production-benchmark"
            / "configs"
            / "postfinal-v2-client-addresses-v3.json"
        )
        plan = start_full_process_observation.resolve_plan(
            repo_root=repo_root,
            config_path=config,
            request_started_epoch_ms=1,
            codex_turn_id="validation-only-client-addresses-v3-profile",
        )

        self.assertEqual("postfinal-v2-client-addresses-v3", plan.benchmark_id)
        self.assertEqual(
            "79-application-card-client-addresses-one-command-v3",
            plan.handoff_dir.name,
        )
        self.assertEqual(
            "application-card-client-addresses-one-command-v3-20260719",
            plan.cycle_dir.name,
        )
        self.assertEqual(
            "4.3-application-card-client-addresses-shadow-20260719-v3.md",
            plan.final_artifact.name,
        )
        template = json.loads(plan.context_template.read_text(encoding="utf-8"))
        type_section_rows = [
            item
            for item in template["source_rows"]
            if 4 <= int(item["source_row_id"].removeprefix("SRC-")) <= 15
        ]
        self.assertEqual(12, len(type_section_rows))
        self.assertTrue(
            all(
                item["in_scope_hint"]
                == "no; user-confirmed out-of-project section CLR-ADDR-003"
                for item in type_section_rows
            )
        )
        self.assertFalse(plan.handoff_dir.exists())
        self.assertFalse(plan.cycle_dir.exists())
        self.assertFalse(plan.final_artifact.exists())


if __name__ == "__main__":
    unittest.main()
