from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts import run_semantic_design_qualification


class SemanticDesignQualificationTests(unittest.TestCase):
    def test_fresh_runtime_invokes_standard_sharded_orchestrator(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = root / "context.json"
            boundary = root / "boundary.json"
            context.write_text("{}", encoding="utf-8")
            boundary.write_text("{}", encoding="utf-8")
            runtime = root / "qualification"
            stdout = StringIO()
            with patch.object(
                run_semantic_design_qualification,
                "_run_sharded_semantic_design",
                return_value=(0, {"status": "completed", "decision": "ready"}),
            ) as orchestrator, redirect_stdout(stdout):
                code = run_semantic_design_qualification.main(
                    [
                        "--repo-root",
                        str(root),
                        "--context",
                        str(context),
                        "--scope-boundary-decision",
                        str(boundary),
                        "--runtime-dir",
                        str(runtime),
                        "--semantic-shard-max-weight",
                        "24",
                        "--semantic-timeout-seconds",
                        "240",
                    ]
                )

        self.assertEqual(0, code)
        self.assertEqual("ready", json.loads(stdout.getvalue())["decision"])
        self.assertEqual(24, orchestrator.call_args.kwargs["max_semantic_weight"])
        self.assertEqual(240, orchestrator.call_args.kwargs["timeout_seconds"])
        self.assertEqual("on", orchestrator.call_args.kwargs["mode"])

    def test_existing_runtime_is_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = root / "context.json"
            boundary = root / "boundary.json"
            runtime = root / "qualification"
            context.write_text("{}", encoding="utf-8")
            boundary.write_text("{}", encoding="utf-8")
            runtime.mkdir()

            with self.assertRaisesRegex(FileExistsError, "fresh immutable path"):
                run_semantic_design_qualification.main(
                    [
                        "--repo-root",
                        str(root),
                        "--context",
                        str(context),
                        "--scope-boundary-decision",
                        str(boundary),
                        "--runtime-dir",
                        str(runtime),
                    ]
                )

    def test_targeted_shard_uses_fresh_projection_without_full_merge(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = root / "context.json"
            boundary = root / "boundary.json"
            runtime = root / "qualification"
            context.write_text("{}", encoding="utf-8")
            boundary.write_text("{}", encoding="utf-8")
            plan = {
                "shards": [
                    {
                        "shard_id": "semantic-shard-005",
                        "execution_mode": "model",
                    }
                ]
            }

            def model_runner(argv: list[str] | None = None) -> int:
                assert argv is not None
                summary_path = Path(argv[argv.index("--summary-output") + 1])
                summary_path.parent.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(
                    json.dumps(
                        {
                            "status": "completed",
                            "decision": "ready",
                            "model_invoked": True,
                            "lifecycle": {
                                "runner_attempt_count": 1,
                                "runner_retry_count": 0,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return 0

            stdout = StringIO()
            with (
                patch.object(
                    run_semantic_design_qualification,
                    "build_semantic_shard_plan",
                    return_value=plan,
                ),
                patch.object(
                    run_semantic_design_qualification,
                    "project_semantic_shard",
                    return_value=({}, {}),
                ),
                patch.object(
                    run_semantic_design_qualification,
                    "semantic_main",
                    side_effect=model_runner,
                ) as model,
                redirect_stdout(stdout),
            ):
                code = run_semantic_design_qualification.main(
                    [
                        "--repo-root",
                        str(root),
                        "--context",
                        str(context),
                        "--scope-boundary-decision",
                        str(boundary),
                        "--runtime-dir",
                        str(runtime),
                        "--target-shard-id",
                        "semantic-shard-005",
                        "--semantic-timeout-seconds",
                        "240",
                    ]
                )

        result = json.loads(stdout.getvalue())
        self.assertEqual(0, code)
        self.assertEqual(1, model.call_count)
        model_args = model.call_args.args[0]
        self.assertEqual(
            "240", model_args[model_args.index("--timeout-seconds") + 1]
        )
        self.assertFalse(
            result["targeted_qualification"]["full_design_qualified"]
        )
        self.assertFalse(result["targeted_qualification"]["merge_performed"])

    def test_targeted_shard_can_rebind_preferred_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context = root / "context.json"
            boundary = root / "boundary.json"
            preferred = root / "preferred-plan.json"
            runtime = root / "qualification"
            context.write_text("{}", encoding="utf-8")
            boundary.write_text("{}", encoding="utf-8")
            preferred.write_text("{}", encoding="utf-8")
            plan = {
                "shards": [
                    {
                        "shard_id": "semantic-shard-009",
                        "execution_mode": "model",
                    }
                ]
            }

            with (
                patch.object(
                    run_semantic_design_qualification,
                    "rebind_semantic_shard_plan_ownership",
                    return_value=plan,
                ) as rebind,
                patch.object(
                    run_semantic_design_qualification,
                    "project_semantic_shard",
                    return_value=({}, {}),
                ),
                patch.object(
                    run_semantic_design_qualification,
                    "semantic_main",
                    return_value=2,
                ),
                redirect_stdout(StringIO()),
            ):
                code = run_semantic_design_qualification.main(
                    [
                        "--repo-root",
                        str(root),
                        "--context",
                        str(context),
                        "--scope-boundary-decision",
                        str(boundary),
                        "--runtime-dir",
                        str(runtime),
                        "--target-shard-id",
                        "semantic-shard-009",
                        "--preferred-plan",
                        str(preferred),
                        "--semantic-shard-max-weight",
                        "25",
                    ]
                )

        self.assertEqual(2, code)
        self.assertEqual(1, rebind.call_count)
        self.assertEqual(25, rebind.call_args.kwargs["max_semantic_weight"])


if __name__ == "__main__":
    unittest.main()
