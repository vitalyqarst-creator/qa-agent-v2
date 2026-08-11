from __future__ import annotations

import hashlib
import json
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

    def test_canonical_tc_must_route_to_review_and_keep_accepted_matrix_hash(self) -> None:
        validator = self.load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "01-sample"
            practical = root / "work" / "practical" / "sample"
            canonical = root / "test-cases" / "sample.md"
            handoff.mkdir(parents=True)
            practical.mkdir(parents=True)
            canonical.parent.mkdir(parents=True)
            matrix = practical / "test-design-matrix.md"
            matrix.write_text("# Matrix\n", encoding="utf-8")
            canonical.write_text("# Test cases\n", encoding="utf-8")
            digest = hashlib.sha256(matrix.read_bytes()).hexdigest()
            gate = practical / "controller-post-finalization.json"
            gate.write_text(
                json.dumps(
                    {
                        "review_subject_artifacts_by_scope": {
                            "01": {
                                "role": "test-design-matrix",
                                "source_path": matrix.resolve().as_posix(),
                                "sha256": digest,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            state = {
                "route_profile": "practical_v0_8",
                "scope_slug": "sample",
                "current_stage": "ft-test-case-writer",
                "stage_status": "ready-for-next-stage",
                "next_skill": "ft-test-case-writer",
                "writer_mode": "practical_v0_8_tc_after_matrix_accepted",
                "latest_artifacts": {
                    "test_design_matrix": matrix.relative_to(root).as_posix(),
                    "canonical_test_cases": canonical.relative_to(root).as_posix(),
                    "controller_post_finalization_gate": gate.relative_to(root).as_posix(),
                },
            }

            findings, _ = validator.validate_practical_tc_review_handoff(state, workflow, root)
            self.assertIn(
                "practical-workflow-canonical-tc-must-route-to-review",
                [item.id for item in findings],
            )

            state.update(
                {
                    "stage_status": "ready-for-review",
                    "next_skill": "ft-test-case-reviewer",
                    "review_mode": "tc_review",
                }
            )
            findings, checks = validator.validate_practical_tc_review_handoff(state, workflow, root)
            self.assertEqual([], findings)
            self.assertEqual("pass", checks[0].status)

            matrix.write_text("# Changed matrix\n", encoding="utf-8")
            findings, _ = validator.validate_practical_tc_review_handoff(state, workflow, root)
            self.assertIn(
                "practical-workflow-reviewed-matrix-hash-mismatch",
                [item.id for item in findings],
            )

            state.update(
                {
                    "stage_status": "ready-for-review",
                    "next_skill": "ft-test-case-reviewer",
                    "review_mode": "matrix_review",
                    "writer_mode": "practical_v0_8_matrix",
                    "matrix_review_status": "invalidated",
                    "matrix_revalidation_reason": "reviewed-matrix-hash-mismatch",
                    "current_round": 2,
                }
            )
            findings, checks = validator.validate_practical_tc_review_handoff(state, workflow, root)
            self.assertEqual([], findings)
            self.assertEqual("pass", checks[0].status)

            matrix.write_text("# Matrix\n", encoding="utf-8")
            findings, _ = validator.validate_practical_tc_review_handoff(state, workflow, root)
            self.assertIn(
                "practical-workflow-matrix-revalidation-not-justified",
                [item.id for item in findings],
            )


if __name__ == "__main__":
    unittest.main()
