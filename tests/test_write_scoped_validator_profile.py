from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_helper_module():
    spec = importlib.util.spec_from_file_location(
        "write_scoped_validator_profile_test",
        ROOT_DIR / "scripts" / "write_scoped_validator_profile.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WriteScopedValidatorProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.helper = load_helper_module()

    def test_writes_runner_generated_profile_from_actual_validator_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ft_root = Path(tmp) / "fts" / "Sample"
            state_path = ft_root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                "\n".join(
                    [
                        "scope_slug: sample",
                        "current_stage: ft-test-case-writer",
                        "latest_artifacts:",
                        "  canonical_test_cases: test-cases/9.1-sample.md",
                        "  writer_quality_gate: work/test-design/9.1-sample/writer-quality-gate.md",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            payload = {"findings": []}
            with patch.object(self.helper, "run_agent_artifact_validator", return_value=payload):
                exit_code = self.helper.main(["--workflow-state", str(state_path), "--require-clean"])

            self.assertEqual(0, exit_code)
            profile_path = state_path.parent / "outputs" / "scoped-validator-profile.ft-test-case-writer.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual("codex_review_cycle_runner", profile["generated_by"])
            self.assertEqual("test-cases/9.1-sample.md", profile["canonical_test_cases"])
            self.assertEqual("work/test-design/9.1-sample", profile["test_design_dir"])
            self.assertEqual([], profile["current_scope_findings"])
            self.assertEqual(0, profile["unresolved_warning_error_count"])
