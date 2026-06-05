from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class SessionBasedReviewCycleContractTests(unittest.TestCase):
    def test_review_cycle_reference_defines_separate_session_lifecycle(self) -> None:
        content = (
            ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md"
        ).read_text(encoding="utf-8")

        for token in (
            "scope-gap-review -> writer-r1",
            "writer-r1 -> structure-preflight-r1 -> writer-structure-r1 if blocked -> structure-preflight-r1 -> semantic-review-r1",
            "writer-structure-r1",
            "writer-r2 -> semantic-review-r2",
            "format-review-final -> writer-format-final -> semantic-regression-final",
            "Max two semantic rounds",
            "never starts the reviewer",
            "cycle-state.yaml",
            "resolved instruction-loading scenario context",
            "resolve_instruction_context.py",
            "versions/<snapshot-id>/",
            "compatibility-only",
            "scope_gap_review",
        ):
            self.assertIn(token, content)

    def test_review_cycle_reference_lists_allowed_statuses_and_gates(self) -> None:
        content = (
            ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md"
        ).read_text(encoding="utf-8")

        for status in (
            "scope-ready-for-gap-review",
            "scope-gap-review-passed",
            "scope-ready-for-writer",
            "writer-draft-ready",
            "structure-preflight-blocked",
            "semantic-review-ready",
            "semantic-revision-needed",
            "semantic-review-passed",
            "format-review-ready",
            "format-revision-needed",
            "final-regression-ready",
            "signed-off",
            "round-cap-reached",
            "blocked-input",
        ):
            self.assertIn(status, content)

        self.assertIn("format review must not run before semantic review passes", content)
        self.assertIn("UI automation prep can start only after `signed-off`", content)

    def test_codex_sdk_reference_keeps_runner_out_of_domain_decisions(self) -> None:
        content = (
            ROOT_DIR / "references" / "agent" / "codex-sdk-orchestration-format.md"
        ).read_text(encoding="utf-8")

        for token in (
            "The SDK runner is not a domain-rule source",
            "must not decide whether reviewer findings are correct",
            "must not let writer start reviewer",
            "let writer or reviewer sessions edit `codex-session-map.yaml`",
            "codex-session-map.yaml",
            "`structure-preflight-*`: `workspace_write`",
            "`status: started` session record written before blocking on the SDK run",
            "runner.lock.yaml",
            "`--recover-stale-lock`",
            "A second runner on the same state must fail fast",
            "python scripts/codex_review_cycle_runner.py validate",
            "python scripts/codex_review_cycle_runner.py snapshot",
            "python scripts/codex_review_cycle_runner.py start --state <cycle-state.yaml> --dry-run",
            "python scripts/codex_review_cycle_runner.py start --state <cycle-state.yaml>",
            "python scripts/codex_review_cycle_runner.py run-until-terminal --state <cycle-state.yaml>",
            "`run-until-terminal` starts the next Codex thread",
            "Use `--max-sessions` as a loop safety limit",
            "Without `--dry-run`, `start` / `continue` starts a new Codex thread",
            "selected required instruction files from the resolver output",
            "must not sign off or route the cycle forward as semantically complete",
        ):
            self.assertIn(token, content)

    def test_old_full_loop_is_not_redefined_by_new_contracts(self) -> None:
        routing = (
            ROOT_DIR / "references" / "agent" / "task-start-skill-routing-format.md"
        ).read_text(encoding="utf-8")
        iteration_skill = (
            ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("iteration.full_loop", routing)
        self.assertIn("review_cycle.session_based", routing)
        self.assertIn("session-based-review-cycle-format.md", iteration_skill)
        self.assertIn("New runs must not create or update", iteration_skill)
        self.assertIn("work/review-loops", iteration_skill)
        self.assertIn("legacy-only historical evidence", iteration_skill)

    def test_canary_v3_preflight_defines_acceptance_and_runner_protocol(self) -> None:
        content = (
            ROOT_DIR / "work" / "quality-improvement-canary-v3-preflight.md"
        ).read_text(encoding="utf-8")

        for token in (
            "Recommended compact scope",
            "Mandatory Acceptance Criteria",
            "zero placeholder elements",
            "zero source-rule oracle phrases",
            "Editability TC contain concrete old/new values",
            "все и только активные значения",
            "Test-design-derived checks",
            "Reviewer semantic sign-off is blocked",
            "doctor --state",
            "resume --state <cycle-state.yaml> --dry-run",
            "run-until-terminal --state <cycle-state.yaml> --max-sessions 1",
            "Do not accept `signed-off` as sufficient evidence by itself",
        ):
            self.assertIn(token, content)


if __name__ == "__main__":
    unittest.main()
