from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PracticalPostFinalizationGateValidatorTests(unittest.TestCase):
    def load_validator(self):
        module_path = ROOT_DIR / "scripts" / "validate_agent_artifacts.py"
        spec = importlib.util.spec_from_file_location(
            "validate_agent_artifacts_post_finalization_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_matrix_accepted_writer_transition_requires_controller_gate(self) -> None:
        validator = self.load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
            workflow.parent.mkdir(parents=True)
            state = {
                "route_profile": "practical_v0_8",
                "current_stage": "ft-test-case-reviewer",
                "stage_status": "ready-for-next-stage",
                "next_skill": "ft-test-case-writer",
                "writer_mode": "practical_v0_8_tc_after_matrix_accepted",
                "latest_artifacts": {},
            }

            findings, checks = validator.validate_practical_post_finalization_gate(
                state, workflow, root
            )

        self.assertEqual(["practical-workflow-post-finalization-gate-missing"], [item.id for item in findings])
        self.assertEqual("fail", checks[0].status)


if __name__ == "__main__":
    unittest.main()
