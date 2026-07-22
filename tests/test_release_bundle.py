from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_release_bundle import ReleaseBundleError, build_release_bundle
from test_case_agent.source_qualified_run import load_source_qualified_run_config


ROOT = Path(__file__).resolve().parents[1]


class ReleaseBundleTests(unittest.TestCase):
    def test_autofin_originals_are_explicitly_local_only(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("fts/AutoFin/source/", ignore)
        self.assertIn("fts/AutoFin/mockups/", ignore)
        self.assertIn("fts/AutoFin/support/**/*.docx", ignore)
        self.assertIn("fts/AutoFin/support/**/*.pdf", ignore)
        self.assertIn("evals/sdk-turn-diagnostics/", ignore)
        self.assertIn("fts/AutoFin/test-cases/*shadow*.md", ignore)

    def test_production_profile_excludes_benchmarks_tests_and_ft_inputs(self) -> None:
        receipt = build_release_bundle(
            root=ROOT,
            manifest_path=ROOT / "release" / "production-manifest.json",
            output=None,
            check_only=True,
            require_local_inputs=False,
        )
        paths = {item["path"] for item in receipt["files"]}

        self.assertEqual("production", receipt["profile"])
        self.assertIn("test_case_agent/stage_backend.py", paths)
        self.assertIn("test_case_agent/derivation_compiler.py", paths)
        self.assertIn("references/agent/production-instruction-loading.md", paths)
        self.assertIn("references/agent/production-global-rules.md", paths)
        self.assertNotIn("AGENTS.md", paths)
        self.assertNotIn("references/agent/instruction-loading-manifest.md", paths)
        self.assertEqual(
            {
                "skills/ft-test-case-iteration/SKILL.md",
            },
            {path for path in paths if path.startswith("skills/")},
        )
        forbidden_paths = {
            "scripts/review_cycle_backend_dispatcher.py",
            "scripts/codex_exec_review_cycle_runner.py",
            "scripts/codex_review_cycle_runner.py",
            "scripts/run_cycle.ps1",
            "scripts/run_incremental_update_iteration.py",
            "scripts/run_lean_production_iteration.py",
            "scripts/run_overnight_controller.py",
            "scripts/run_standard_production_iteration.py",
            "scripts/run_standard_scope_bridge.py",
            "scripts/run_quick_quality_proof.py",
            "test_case_agent/quality_proof.py",
        }
        self.assertTrue(forbidden_paths.isdisjoint(paths))
        self.assertFalse(
            any(path.startswith("test_case_agent/lean_v2/") for path in paths)
        )
        self.assertFalse(any(path.startswith("evals/") for path in paths))
        self.assertFalse(any(path.startswith("tests/") for path in paths))
        self.assertFalse(any(path.startswith("fts/") for path in paths))
        self.assertLessEqual(receipt["file_count"], 55)
        self.assertLessEqual(
            sum(path.startswith("references/") for path in paths),
            10,
        )

    def test_production_iteration_skill_has_one_route_without_legacy_markers(self) -> None:
        skill = (ROOT / "skills/ft-test-case-iteration/SKILL.md").read_text(
            encoding="utf-8"
        )
        contract = (ROOT / "references/agent/lean-v2-iteration.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("ft-agent run", skill)
        self.assertIn('"schema_version": 2', skill)
        self.assertIn("accepted-shadow", skill)
        self.assertIn("ровно одному независимому reviewer", skill)
        self.assertNotIn("writer", skill.casefold())
        self.assertNotIn("writer", contract.casefold())
        self.assertIn("ровно одного независимого reviewer", contract)
        for forbidden in (
            "review_cycle_backend_dispatcher.py",
            "cycle-state.yaml",
            "run_incremental_update_iteration.py",
            "run_lean_production_iteration.py",
            "run_standard_production_iteration.py",
            "run_overnight_controller.py",
            "--backend",
            "prepared_fast_writer_mode",
            "prepared_standard_writer_mode",
        ):
            self.assertNotIn(forbidden, skill)

    def test_production_run_config_examples_match_public_schema_v2(self) -> None:
        instruction_paths = (
            ROOT / "skills" / "ft-test-case-iteration" / "SKILL.md",
            ROOT / "references" / "agent" / "lean-v2-iteration.md",
        )
        expected_fields = {
            "schema_version",
            "registry",
            "ft_root",
            "scope",
            "source_evidence",
            "obligations",
        }
        with tempfile.TemporaryDirectory(prefix="production-config-example-") as raw:
            for index, instruction_path in enumerate(instruction_paths):
                text = instruction_path.read_text(encoding="utf-8")
                match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
                self.assertIsNotNone(match, instruction_path)
                payload = json.loads(match.group(1))
                self.assertEqual(expected_fields, set(payload), instruction_path)
                config_path = Path(raw) / f"run-config-{index}.json"
                config_path.write_text(
                    json.dumps(payload, ensure_ascii=False),
                    encoding="utf-8",
                )
                loaded = load_source_qualified_run_config(config_path)
                self.assertEqual(2, loaded.schema_version)
                self.assertIsNone(loaded.derivations)
                self.assertIsNone(loaded.design_context)
                self.assertIsNone(loaded.ft_slug)

    def test_qualification_profile_keeps_curated_configs_not_raw_runs(self) -> None:
        receipt = build_release_bundle(
            root=ROOT,
            manifest_path=ROOT / "release" / "qualification-manifest.json",
            output=None,
            check_only=True,
            require_local_inputs=True,
        )
        paths = {item["path"] for item in receipt["files"]}

        self.assertEqual("qualification", receipt["profile"])
        self.assertTrue(
            any(
                path.startswith("evals/full-production-benchmark/configs/")
                for path in paths
            )
        )
        self.assertFalse(any("/diagnostics/" in path for path in paths))
        self.assertFalse(any(path.startswith("fts/AutoFin/source/") for path in paths))
        self.assertFalse(any(path.startswith("fts/AutoFin/mockups/") for path in paths))
        self.assertIn("scripts/run_quick_quality_proof.py", paths)
        self.assertIn("tests/test_quality_proof.py", paths)
        self.assertIn("evals/quick-quality-proof/manifest.json", paths)
        self.assertIn(
            "fts/AutoFin/work/vendor-references/dadata-fixture-catalog.md",
            paths,
        )
        self.assertIn(
            "fts/AutoFin/work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-POS-001.response.json",
            paths,
        )
        self.assertIn(
            "fts/AutoFin/work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-POS-001.verification.json",
            paths,
        )
        self.assertIn(
            "fts/AutoFin/work/vendor-references/dadata-fixtures/FX-DADATA-REGION-POS-001.response.json",
            paths,
        )
        self.assertIn(
            "fts/AutoFin/work/vendor-references/dadata-fixtures/FX-DADATA-REGION-POS-001.verification.json",
            paths,
        )
        self.assertTrue(
            any(
                item["path"].startswith("fts/AutoFin/mockups/")
                for item in receipt["local_inputs"]
            )
        )
        self.assertTrue(all(item["matched"] for item in receipt["local_inputs"]))

    def test_bundle_build_is_fresh_and_emits_hash_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="release-bundle-test-") as raw:
            output = Path(raw) / "production"
            receipt = build_release_bundle(
                root=ROOT,
                manifest_path=ROOT / "release" / "production-manifest.json",
                output=output,
                check_only=False,
                require_local_inputs=False,
            )
            stored = json.loads(
                (output / "release-manifest.json").read_text(encoding="utf-8")
            )

            self.assertEqual(receipt["tree_sha256"], stored["tree_sha256"])
            self.assertTrue((output / "test_case_agent").is_dir())
            self.assertFalse((output / "evals").exists())
            env = os.environ.copy()
            env["PYTHONPATH"] = str(output)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            help_result = subprocess.run(
                [sys.executable, "-m", "test_case_agent.cli", "--help"],
                cwd=output,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(0, help_result.returncode, help_result.stderr)
            self.assertIn("{run}", help_result.stdout)
            self.assertNotIn("quality-proof", help_result.stdout)

            for scenario in ("iteration.deterministic_production",):
                context_result = subprocess.run(
                    [
                        sys.executable,
                        "scripts/resolve_instruction_context.py",
                        "--root",
                        str(output),
                        "--manifest",
                        "references/agent/production-instruction-loading.md",
                        "--scenario",
                        scenario,
                        "--fail-on-budget",
                        "--json",
                    ],
                    cwd=output,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                self.assertEqual(0, context_result.returncode, context_result.stderr)
                context = json.loads(context_result.stdout)
                self.assertEqual("pass", context["budget"]["status"])
                self.assertEqual([], context["missing"])
                self.assertEqual(
                    {
                        "references/agent/production-global-rules.md",
                        "references/agent/runtime-environment-encoding-policy.md",
                        "skills/ft-test-case-iteration/SKILL.md",
                        "references/agent/lean-v2-iteration.md",
                        "references/agent/negative-ui-calibration-policy.md",
                    },
                    {item["path"] for item in context["files"]},
                )
                for item in context["files"]:
                    document = output / item["path"]
                    for target in re.findall(
                        r"\[[^]]+\]\(([^)]+)\)",
                        document.read_text(encoding="utf-8"),
                    ):
                        if "://" in target or target.startswith("#"):
                            continue
                        relative = target.split("#", 1)[0]
                        resolved = (document.parent / relative).resolve()
                        self.assertTrue(
                            resolved.is_file(),
                            f"broken production instruction link: "
                            f"{item['path']} -> {target}",
                        )
            for item in receipt["files"]:
                if not item["path"].endswith(".md"):
                    continue
                document = output / item["path"]
                for target in re.findall(
                    r"\[[^]]+\]\(([^)]+)\)",
                    document.read_text(encoding="utf-8"),
                ):
                    if "://" in target or target.startswith("#"):
                        continue
                    relative = target.split("#", 1)[0]
                    resolved = (document.parent / relative).resolve()
                    self.assertTrue(
                        resolved.is_file(),
                        f"broken production bundle link: "
                        f"{item['path']} -> {target}",
                    )
            with self.assertRaises(ReleaseBundleError):
                build_release_bundle(
                    root=ROOT,
                    manifest_path=ROOT / "release" / "production-manifest.json",
                    output=output,
                    check_only=False,
                    require_local_inputs=False,
                )


if __name__ == "__main__":
    unittest.main()
