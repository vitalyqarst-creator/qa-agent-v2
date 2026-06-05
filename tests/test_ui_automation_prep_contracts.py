from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class UiAutomationPrepContractTests(unittest.TestCase):
    def test_skill_references_shared_formats_and_boundaries(self) -> None:
        content = (ROOT_DIR / "skills" / "ft-ui-automation-prep" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ui-automation-prep-format.md", content)
        self.assertIn("test-case-format.md", content)
        self.assertIn("traceability-rules.md", content)
        self.assertIn("skill-boundaries.md", content)

    def test_skill_protects_ft_first_baseline_and_scope_boundaries(self) -> None:
        content = (ROOT_DIR / "skills" / "ft-ui-automation-prep" / "SKILL.md").read_text(encoding="utf-8")
        lowered = content.lower()
        self.assertIn("`signed-off`", content)
        self.assertIn("не пересматривает scope", content)
        self.assertIn("не перезаписывай baseline signed-off набор тест-кейсов", lowered)
        self.assertIn("Не считай UI канонической заменой текста ФТ", content)
        self.assertIn("Не генерируй Playwright test specs", content)

    def test_reference_lists_statuses_and_automation_ready_fields(self) -> None:
        content = (ROOT_DIR / "references" / "qa" / "ui-automation-prep-format.md").read_text(encoding="utf-8")
        for token in (
            "`confirmed`",
            "`mismatch-ft-ui`",
            "`blocked-ui-unavailable`",
            "`blocked-access`",
            "`blocked-observability`",
            "`not-automatable-manual-only`",
            "`UI Verification Status`",
            "`UI Evidence`",
            "`Automation Notes`",
            "`FT/UI Divergence`",
        ):
            self.assertIn(token, content)

    def test_iteration_mentions_post_iteration_handoff(self) -> None:
        content = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`ft-ui-automation-prep`", content)
        self.assertIn("post-iteration вход", content)
        self.assertIn("automation-ready версии", content)


if __name__ == "__main__":
    unittest.main()
