from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNNER = ROOT_DIR / "scripts" / "codex_review_cycle_runner.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("codex_review_cycle_runner_under_test", RUNNER)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_transition_matrix(content: str) -> dict[str, set[str]]:
    matrix: dict[str, set[str]] = {}
    in_section = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped == "## Post-Session Transition Matrix"
            continue
        if not in_section or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 2 or cells[0] in {"---", "scenario"}:
            continue
        scenario = cells[0].strip("`")
        statuses = {
            item.strip().strip("`")
            for item in cells[1].split(";")
            if item.strip()
        }
        matrix[scenario] = statuses
    return matrix


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
            "contract_version: 2",
            "runner-owned transitions",
            "must not edit `cycle-state.yaml`",
            "must never report `signed-off`",
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

    def test_runner_post_session_transition_matrix_matches_reference(self) -> None:
        content = (
            ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md"
        ).read_text(encoding="utf-8")
        runner = load_runner_module()

        self.assertEqual(
            runner.POST_SESSION_ALLOWED_STAGE_STATUSES,
            parse_transition_matrix(content),
        )

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
            "reviewer stages: `read_only`",
            "run as bounded read-only SDK turns",
            "the runner persists reviewer artifacts/state",
            "Python runtime containing `openai-codex`",
            "`status: started` session record written before blocking on the SDK run",
            "runner.lock.yaml",
            "`--recover-stale-lock`",
            "A second runner on the same state must fail fast",
            ".\\scripts\\run_cycle.ps1 validate",
            ".\\scripts\\run_cycle.ps1 snapshot",
            ".\\scripts\\run_cycle.ps1 start --state <cycle-state.yaml> --dry-run",
            ".\\scripts\\run_cycle.ps1 start --state <cycle-state.yaml>",
            ".\\scripts\\run_cycle.ps1 run-until-terminal --state <cycle-state.yaml>",
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
        preflight_path = ROOT_DIR / "work" / "quality-improvement-canary-v3-preflight.md"
        if not preflight_path.exists():
            self.skipTest("local canary v3 preflight artifact is not present")

        content = preflight_path.read_text(encoding="utf-8")

        for token in (
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

        for forbidden_pattern in (
            re.compile(r"Recommended\s+compact\s+scope", re.IGNORECASE),
            re.compile(r"target size:\s*about\s*\d+\s*-\s*\d+\s*executable TC", re.IGNORECASE),
            re.compile(r"within requested about\s*\d+\s*-\s*\d+\s*range", re.IGNORECASE),
        ):
            self.assertIsNone(forbidden_pattern.search(content))


if __name__ == "__main__":
    unittest.main()
