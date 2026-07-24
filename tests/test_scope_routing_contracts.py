from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class ScopeRoutingContractTests(unittest.TestCase):
    def test_scope_execution_options_requires_both_entrypoint_prompts(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "scope-execution-options-format.md").read_text(encoding="utf-8")

        self.assertIn("prompt.scope-to-writer.md", content)
        self.assertIn("prompt.scope-to-iteration.md", content)
        self.assertIn("ft-test-case-iteration` должен быть указан как рекомендуемый путь по умолчанию", content)
        self.assertIn("не заменяет `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`", content)

    def test_scope_analyzer_outputs_writer_and_iteration_prompts_after_source_first_route(self) -> None:
        scope = (ROOT_DIR / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT_DIR / "references" / "agent" / "scope-contract-format.md").read_text(encoding="utf-8")
        options = (ROOT_DIR / "references" / "agent" / "scope-options-format.md").read_text(encoding="utf-8")
        selection_prompts = (ROOT_DIR / "references" / "agent" / "scope-selection-prompts-format.md").read_text(encoding="utf-8")

        for content in (scope, options):
            self.assertIn("prompt.scope-to-writer.md", content)
            self.assertIn("prompt.scope-to-iteration.md", content)

        self.assertIn("один активный downstream `next_skill`", scope)
        self.assertIn("альтернативный user-facing entrypoint", scope)
        self.assertIn("prompt.scope-assertions-to-reviewer.md", contract)
        self.assertIn("source_assertion_review", contract)
        self.assertIn("после accepted source assertion review", contract)
        self.assertIn("prompt.scope-assertions-to-reviewer.md", selection_prompts)
        self.assertIn("source_assertion_review", selection_prompts)
        self.assertIn("не должен обещать `prompt.scope-to-writer.md`", selection_prompts)

    def test_iteration_prompt_is_not_replaced_by_execution_options(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "scope-execution-options-format.md").read_text(encoding="utf-8")

        self.assertIn("не заменяет `workflow-state.yaml`", content)
        self.assertIn("Не использовать этот файл как замену `prompt.scope-to-iteration.md`", content)


if __name__ == "__main__":
    unittest.main()
