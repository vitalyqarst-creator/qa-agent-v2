from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_case_agent.review_cycle import handoff_transition
from test_case_agent.review_cycle.handoff_transition import (
    ReviewHandoffTransitionError,
    transition_accepted_cycle_to_reviewer_handoff,
)


class ReviewHandoffTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cycle = self.root / "fts" / "demo" / "work" / "review-cycles" / "cycle-1"
        self.handoff = self.root / "fts" / "demo" / "work" / "stage-handoffs" / "01-demo"
        writer = self.cycle / "attempts" / "writer-r1" / "attempt-001" / "runner-output"
        reviewer = self.cycle / "attempts" / "reviewer-r1" / "attempt-001" / "runner-output"
        writer.mkdir(parents=True)
        reviewer.mkdir(parents=True)
        self.handoff.mkdir(parents=True)
        (self.cycle / "cycle-state.yaml").write_text(
            "workflow_status: accepted-not-promoted\n"
            "stage_status: accepted-not-promoted\n"
            "writer_stage_status: completed\n"
            "reviewer_stage_status: accepted\n"
            "accepted_terminal_state: true\n"
            "final_promoted: false\n",
            encoding="utf-8",
        )
        (self.cycle / "review-result.json").write_text(
            json.dumps({"scope_slug": "demo-scope", "decision": "accepted", "findings": []}),
            encoding="utf-8",
        )
        for path in (
            writer / "writer-gate-aggregate.json",
            writer / "evidence-access-report.json",
            reviewer / "evidence-access-report.json",
        ):
            path.write_text(json.dumps({"passed": True}), encoding="utf-8")
        prompt = self.handoff / "prompt.reviewer-to-ui-prep.md"
        prompt.write_text("# Handoff\n", encoding="utf-8")
        (self.cycle / "promotion-basis.seed.json").write_text(
            json.dumps(
                {
                    "scope_slug": "demo-scope",
                    "available_builder_inputs": {
                        "handoff_prompt": {
                            "path": prompt.relative_to(self.root).as_posix(),
                            "sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(),
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.workflow = self.handoff / "workflow-state.yaml"
        self.workflow.write_text(
            "ft_slug: demo\n"
            "scope_slug: demo-scope\n"
            "current_stage: ft-test-case-iteration\n"
            "stage_status: ready-for-next-stage\n"
            "next_skill: ft-test-case-iteration\n"
            "blocking_reasons: []\n",
            encoding="utf-8",
        )

    def test_transitions_only_process_status_and_is_idempotent(self) -> None:
        before = self.workflow.read_text(encoding="utf-8")

        result = transition_accepted_cycle_to_reviewer_handoff(
            repo_root=self.root,
            cycle_dir=self.cycle,
            handoff_dir=self.handoff,
        )
        reused = transition_accepted_cycle_to_reviewer_handoff(
            repo_root=self.root,
            cycle_dir=self.cycle,
            handoff_dir=self.handoff,
        )

        after = self.workflow.read_text(encoding="utf-8")
        self.assertEqual("transitioned", result["status"])
        self.assertEqual("reused", reused["status"])
        self.assertIn("stage_status: ready-for-review", after)
        self.assertIn("next_skill: ft-test-case-reviewer", after)
        self.assertEqual(
            before.replace("ready-for-next-stage", "ready-for-review").replace(
                "ft-test-case-iteration\nblocking_reasons",
                "ft-test-case-reviewer\nblocking_reasons",
            ),
            after,
        )

    def test_rejects_nonaccepted_cycle_without_mutation(self) -> None:
        cycle_state = self.cycle / "cycle-state.yaml"
        cycle_state.write_text(
            cycle_state.read_text(encoding="utf-8").replace(
                "reviewer_stage_status: accepted",
                "reviewer_stage_status: changes-required",
            ),
            encoding="utf-8",
        )
        before = self.workflow.read_bytes()

        with self.assertRaises(ReviewHandoffTransitionError):
            transition_accepted_cycle_to_reviewer_handoff(
                repo_root=self.root,
                cycle_dir=self.cycle,
                handoff_dir=self.handoff,
            )

        self.assertEqual(before, self.workflow.read_bytes())

    def test_interrupted_workflow_write_is_recoverable(self) -> None:
        real_write_atomic = handoff_transition._write_atomic

        def interrupt_workflow(path: Path, content: bytes) -> None:
            if path == self.workflow.resolve():
                raise OSError("simulated interrupted workflow write")
            real_write_atomic(path, content)

        with mock.patch.object(
            handoff_transition,
            "_write_atomic",
            side_effect=interrupt_workflow,
        ):
            with self.assertRaises(OSError):
                transition_accepted_cycle_to_reviewer_handoff(
                    repo_root=self.root,
                    cycle_dir=self.cycle,
                    handoff_dir=self.handoff,
                )

        self.assertIn("stage_status: ready-for-next-stage", self.workflow.read_text(encoding="utf-8"))
        self.assertTrue((self.cycle / "review-handoff-transition.json").is_file())

        recovered = transition_accepted_cycle_to_reviewer_handoff(
            repo_root=self.root,
            cycle_dir=self.cycle,
            handoff_dir=self.handoff,
        )

        self.assertEqual("transitioned", recovered["status"])
        self.assertIn("stage_status: ready-for-review", self.workflow.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
