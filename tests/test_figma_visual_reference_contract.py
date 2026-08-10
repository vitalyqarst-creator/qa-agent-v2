from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class FigmaVisualReferenceContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT_DIR / relative).read_text(encoding="utf-8")

    def test_figma_is_optional_visual_input_not_requirement_source(self) -> None:
        source_selection = self.read("references/agent/source-selection-format.md")
        agents = self.read("AGENTS.md")

        self.assertIn("Ссылки на Figma-дизайн", source_selection)
        self.assertIn("optional_visual_reference", source_selection)
        self.assertIn("ФТ остаётся источником поведения", source_selection)
        self.assertIn("Не сохраняй Figma token", source_selection)
        self.assertIn("локальные макеты и доступные Figma-узлы", agents)

    def test_locator_registers_figma_without_opening_or_scoping_it(self) -> None:
        locator = self.read("skills/ft-source-locator/SKILL.md")

        self.assertIn("figma-design-index.md", locator)
        self.assertIn("необязательные визуальные источники", locator)
        self.assertIn("не открывай scope", locator)

    def test_scope_uses_available_figma_but_optional_access_failure_is_not_blocking(self) -> None:
        scope = self.read("skills/ft-scope-analyzer/SKILL.md")

        self.assertIn("относящийся Figma-узел", scope)
        self.assertIn("недоступный `optional_visual_reference`", scope)
        self.assertIn("scope-brief.md", scope)

    def test_partners_package_registers_the_provided_figma_node(self) -> None:
        index = self.read("fts/Partners/Partners-v1/support/figma/figma-design-index.md")

        self.assertIn("FIGMA-PARTNERS-001", index)
        self.assertIn("node-id=390-5432", index)
        self.assertIn("`390:5432`", index)
        self.assertIn("optional_visual_reference", index)


if __name__ == "__main__":
    unittest.main()
