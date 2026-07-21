from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_release_bundle import ReleaseBundleError, build_release_bundle


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
        self.assertIn("scripts/review_cycle_backend_dispatcher.py", paths)
        self.assertIn("skills/ft-test-case-iteration/SKILL.md", paths)
        self.assertFalse(any(path.startswith("evals/") for path in paths))
        self.assertFalse(any(path.startswith("tests/") for path in paths))
        self.assertFalse(any(path.startswith("fts/") for path in paths))

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
        self.assertIn(
            "fts/AutoFin/work/vendor-references/dadata-fixture-catalog.md",
            paths,
        )
        self.assertIn(
            "fts/AutoFin/work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-POS-001.response.json",
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
