from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.practical_review_input_snapshot import (
    create_snapshot,
    verify_snapshot,
    verify_target_checkout,
)
from test_case_agent.practical_v09 import sha256_file


class PracticalReviewInputSnapshotTests(unittest.TestCase):
    def make_manifest(self, root: Path) -> Path:
        source = root / "work" / "practical-v0.9" / "scope" / "test-design-matrix.md"
        source.parent.mkdir(parents=True)
        source.write_text("# Матрица\n", encoding="utf-8")
        manifest = root / "work" / "practical-v0.9" / "scope" / "matrix-review-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "inputs": [
                        {
                            "role": "test_design_matrix",
                            "path": "work/practical-v0.9/scope/test-design-matrix.md",
                            "sha256": sha256_file(source),
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return manifest

    def test_snapshot_carries_ignored_scope_input_to_another_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            source_root = Path(raw) / "source"
            target_root = Path(raw) / "target"
            manifest = self.make_manifest(source_root)
            target_root.mkdir()

            direct = verify_target_checkout(manifest_path=manifest, package_root=target_root)
            self.assertFalse(direct["allowed"])
            self.assertIn("missing:", direct["issues"][0])

            snapshot = source_root / "external-review-snapshot"
            created = create_snapshot(
                manifest_path=manifest,
                package_root=source_root,
                destination=snapshot,
            )
            self.assertTrue(created["allowed"])
            self.assertTrue((snapshot / "review-manifest.json").is_file())
            self.assertTrue((snapshot / "inputs" / "work" / "practical-v0.9" / "scope" / "test-design-matrix.md").is_file())
            self.assertTrue(verify_snapshot(manifest_path=manifest, snapshot_dir=snapshot)["allowed"])

    def test_snapshot_detects_changed_copy(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = self.make_manifest(root)
            snapshot = root / "snapshot"
            create_snapshot(manifest_path=manifest, package_root=root, destination=snapshot)
            copied = snapshot / "inputs" / "work" / "practical-v0.9" / "scope" / "test-design-matrix.md"
            copied.write_text("# Изменено\n", encoding="utf-8")
            result = verify_snapshot(manifest_path=manifest, snapshot_dir=snapshot)
            self.assertFalse(result["allowed"])
            self.assertIn("hash mismatch", "\n".join(result["issues"]))
