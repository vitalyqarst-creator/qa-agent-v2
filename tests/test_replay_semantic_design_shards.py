from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import replay_semantic_design_shards


class ReplaySemanticDesignShardsTests(unittest.TestCase):
    def test_replay_prefers_raw_model_output_and_falls_back_for_deterministic_shard(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            context = root / "context.json"
            boundary = root / "boundary.json"
            plan = root / "plan.json"
            shards = root / "shards"
            context.write_text("{}", encoding="utf-8")
            boundary.write_text("{}", encoding="utf-8")
            plan.write_text(
                json.dumps(
                    {
                        "shards": [
                            {"shard_id": "semantic-shard-001"},
                            {"shard_id": "semantic-shard-002"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            deterministic = shards / "semantic-shard-001"
            deterministic.mkdir(parents=True)
            (deterministic / "semantic-design.json").write_text(
                json.dumps({"kind": "deterministic"}), encoding="utf-8"
            )
            model = shards / "semantic-shard-002"
            model.mkdir()
            (model / "semantic-design.model-output.json").write_text(
                json.dumps({"kind": "raw-model"}), encoding="utf-8"
            )
            (model / "semantic-design.json").write_text(
                json.dumps({"kind": "stale-normalized"}), encoding="utf-8"
            )

            def normalize(payload, **_kwargs):
                return (
                    {**payload, "normalized": True},
                    {"repair_count": 1, "repairs": [{"rule": "test"}]},
                )

            merged = {
                "source_designs": [{"assertions": [{}, {}]}],
                "obligations": [{}, {}],
                "negative_oracles": [{}],
                "requiredness_oracles": [],
            }
            with (
                patch.object(
                    replay_semantic_design_shards,
                    "normalize_semantic_design_transport",
                    side_effect=normalize,
                ),
                patch.object(
                    replay_semantic_design_shards,
                    "load_approved_clarifications",
                    return_value=(),
                ),
                patch.object(
                    replay_semantic_design_shards,
                    "project_semantic_shard",
                    return_value=({}, {}),
                ),
                patch.object(
                    replay_semantic_design_shards,
                    "merge_semantic_shards",
                    return_value=(merged, {"status": "verified"}),
                ) as merge,
            ):
                report = replay_semantic_design_shards.replay_semantic_design_shards(
                    repo_root=root,
                    context_path=context,
                    boundary_path=boundary,
                    plan_path=plan,
                    shards_dir=shards,
                    merged_output_path=Path("merged.json"),
                )

            self.assertEqual("verified", report["status"])
            self.assertEqual(2, report["normalization_repair_count"])
            self.assertEqual(
                ["materialized-output", "raw-model-output"],
                [item["input_kind"] for item in report["shards"]],
            )
            self.assertEqual(2, report["merged_counts"]["assertions"])
            self.assertEqual("merged.json", report["merged_output"]["path"])
            self.assertTrue((root / "merged.json").is_file())
            outputs = merge.call_args.args[4]
            self.assertEqual("deterministic", outputs["semantic-shard-001"]["kind"])
            self.assertEqual("raw-model", outputs["semantic-shard-002"]["kind"])

    def test_replay_rejects_path_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            with self.assertRaisesRegex(ValueError, "escapes repository root"):
                replay_semantic_design_shards.replay_semantic_design_shards(
                    repo_root=root,
                    context_path=root.parent / "outside.json",
                    boundary_path=Path("boundary.json"),
                    plan_path=Path("plan.json"),
                    shards_dir=Path("shards"),
                )


if __name__ == "__main__":
    unittest.main()
