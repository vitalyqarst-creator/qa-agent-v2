from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class SourceSelectionFormatTests(unittest.TestCase):
    def test_source_selection_reference_defines_required_contract(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "source-selection-format.md").read_text(encoding="utf-8")

        self.assertIn("source-selection.md", content)
        self.assertIn("selection_status", content)
        self.assertIn("selected | ambiguous | blocked-input", content)
        self.assertIn("Main FT Documents", content)
        self.assertIn("Structural Cross-Check PDF", content)
        self.assertIn("Source Quality", content)
        self.assertIn("Support Files And Mockups", content)
        self.assertIn("source-selection-missing-required-sections", content)
        self.assertIn("workflow-state-source-selection-not-selected", content)

    def test_source_locator_links_to_source_selection_reference(self) -> None:
        locator = (ROOT_DIR / "skills" / "ft-source-locator" / "SKILL.md").read_text(encoding="utf-8")
        handoff = (ROOT_DIR / "references" / "agent" / "stage-handoff-model.md").read_text(encoding="utf-8")
        contracts = (ROOT_DIR / "references" / "agent" / "instruction-contract-index.md").read_text(encoding="utf-8")

        self.assertIn("source-selection-format.md", locator)
        self.assertIn("session-log-format.md", locator)
        self.assertIn("source-locator-session-log.md", locator)
        self.assertIn("source-selection-format.md", handoff)
        self.assertIn("Source selection", contracts)
        self.assertIn("source-selection-format.md", contracts)

    def test_source_locator_prompt_uses_valid_skill_names(self) -> None:
        locator_prompt = (ROOT_DIR / "skills" / "ft-source-locator" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        scope_prompt = (ROOT_DIR / "skills" / "ft-scope-analyzer" / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("$ft-source-locator", locator_prompt)
        self.assertIn("$ft-scope-analyzer", locator_prompt)
        self.assertIn("source-locator-session-log.md", locator_prompt)
        self.assertIn("clean diagnostic", locator_prompt)
        self.assertIn("neighboring fts packages", locator_prompt)
        self.assertIn("$ft-scope-analyzer", scope_prompt)
        self.assertNotIn("Use -source-locator", locator_prompt)
        self.assertNotIn("Use -scope-analyzer", scope_prompt)

    def test_source_selection_does_not_replace_scope_contract(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "source-selection-format.md").read_text(encoding="utf-8")
        locator = (ROOT_DIR / "skills" / "ft-source-locator" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("не смешивать выбор FT-пакета с определением scope", content)
        self.assertIn("не должен создавать `scope-contract.md`", content)
        self.assertIn("Не создавай `scope-contract.md`", locator)

    def test_source_locator_defines_clean_diagnostic_isolation(self) -> None:
        locator = (ROOT_DIR / "skills" / "ft-source-locator" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Clean Diagnostic Isolation", locator)
        self.assertIn("работай только внутри выбранного `fts/<ft-slug>`", locator)
        self.assertIn("не открывай, не сравнивай и не копируй", locator)
        self.assertIn("Contamination Check", locator)


if __name__ == "__main__":
    unittest.main()
