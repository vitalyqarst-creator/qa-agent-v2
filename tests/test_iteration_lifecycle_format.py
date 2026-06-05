from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class IterationLifecycleFormatTests(unittest.TestCase):
    def test_session_based_lifecycle_reference_defines_canonical_states(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md").read_text(encoding="utf-8")

        self.assertIn("`signed-off`", content)
        self.assertIn("`round-cap-reached`", content)
        self.assertIn("`blocked-input`", content)
        self.assertIn("Max two semantic rounds", content)
        self.assertIn("UI automation prep can start only after `signed-off`", content)

    def test_session_based_lifecycle_reference_defines_required_artifacts(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md").read_text(encoding="utf-8")

        for token in (
            "work/review-cycles/<scope-slug>/cycle-state.yaml",
            "work/review-cycles/<scope-slug>/prompts/<prompt-file>.md",
            "work/review-cycles/<scope-slug>/versions/<snapshot-id>",
            "codex-session-map.yaml",
            "snapshot-manifest.yaml",
            "writer-r1",
            "structure-preflight-r1",
            "semantic-review-r1",
            "format-review-final",
            "semantic-regression-final",
        ):
            self.assertIn(token, content)

    def test_iteration_skill_links_to_session_based_lifecycle_reference(self) -> None:
        iteration = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        handoff = (ROOT_DIR / "references" / "agent" / "stage-handoff-model.md").read_text(encoding="utf-8")
        contracts = (ROOT_DIR / "references" / "agent" / "instruction-contract-index.md").read_text(encoding="utf-8")

        self.assertIn("session-based-review-cycle-format.md", iteration)
        self.assertIn("session-based-review-cycle-format.md", handoff)
        self.assertIn("Writer/reviewer cycle lifecycle", contracts)
        self.assertIn("session-based-review-cycle-format.md", contracts)

    def test_legacy_iteration_lifecycle_is_compatibility_only(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "iteration-lifecycle-format.md").read_text(encoding="utf-8")

        self.assertIn("compatibility-only", content)
        self.assertIn("Do not use this file as the source of truth for new runs", content)
        self.assertIn("work/review-cycles/<scope-slug>/cycle-state.yaml", content)


if __name__ == "__main__":
    unittest.main()
