from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_snapshot_helper():
    spec = importlib.util.spec_from_file_location(
        "practical_snapshot_preflight_for_tests",
        ROOT_DIR / "scripts" / "practical_snapshot_preflight.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_snapshot_for_tests",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PracticalSnapshotPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.helper = load_snapshot_helper()

    def test_creates_verified_immutable_prewrite_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ft_root = Path(tmp) / "fts" / "Sample" / "Sample-v1"
            canonical = ft_root / "test-cases" / "9.2-status.md"
            matrix = ft_root / "work" / "practical" / "status" / "test-design-matrix.md"
            canonical.parent.mkdir(parents=True)
            matrix.parent.mkdir(parents=True)
            canonical.write_text("baseline test cases\n", encoding="utf-8")
            matrix.write_text("baseline matrix\n", encoding="utf-8")

            result = self.helper.create_snapshot(
                ft_package_root=ft_root,
                scope_slug="status",
                snapshot_id="pre-write-r1",
                sources=[canonical, matrix],
                reason="pre_quality_gate_baseline",
            )

            self.assertEqual("valid", result["status"])
            snapshot_dir = Path(str(result["snapshot_dir"]))
            manifest = json.loads((snapshot_dir / "snapshot-manifest.yaml").read_text(encoding="utf-8"))
            self.assertEqual("pre_write_baseline", manifest["snapshot_role"])
            self.assertEqual("valid", manifest["snapshot_status"])
            self.assertEqual(2, len(manifest["source_files"]))
            self.assertEqual(
                "baseline test cases\n",
                (snapshot_dir / "files" / "test-cases" / "9.2-status.md").read_text(encoding="utf-8"),
            )

            canonical.write_text("candidate test cases\n", encoding="utf-8")
            verification = self.helper.verify_snapshot(snapshot_dir, ft_root)
            self.assertEqual("valid", verification["status"])
            with self.assertRaises(FileExistsError):
                self.helper.create_snapshot(
                    ft_package_root=ft_root,
                    scope_slug="status",
                    snapshot_id="pre-write-r1",
                    sources=[canonical],
                    reason="retry",
                )

    def test_validator_does_not_treat_workflow_inside_snapshot_as_active(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            active = root / "fts" / "Sample" / "Sample-v1" / "work" / "stage-handoffs" / "01-scope" / "workflow-state.yaml"
            historical = root / "fts" / "Sample" / "Sample-v1" / "work" / "review-cycles" / "scope" / "versions" / "r0" / "workflow-state.yaml"
            active.parent.mkdir(parents=True)
            historical.parent.mkdir(parents=True)
            active.write_text("scope_slug: active\n", encoding="utf-8")
            historical.write_text("scope_slug: historical\n", encoding="utf-8")

            states = validator.iter_workflow_states(root)

            self.assertEqual([active], states)


if __name__ == "__main__":
    unittest.main()
