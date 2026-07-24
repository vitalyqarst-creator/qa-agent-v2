from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class StageHandoffContractTests(unittest.TestCase):
    def test_stage_handoff_references_define_hybrid_model(self) -> None:
        handoff = (ROOT_DIR / "references" / "agent" / "stage-handoff-model.md").read_text(encoding="utf-8")
        state = (ROOT_DIR / "references" / "agent" / "workflow-state-format.md").read_text(encoding="utf-8")
        prompt = (ROOT_DIR / "references" / "agent" / "next-step-prompt-format.md").read_text(encoding="utf-8")
        scope_contract = (ROOT_DIR / "references" / "agent" / "scope-contract-format.md").read_text(encoding="utf-8")
        scope_gaps = (ROOT_DIR / "references" / "agent" / "scope-coverage-gaps-format.md").read_text(encoding="utf-8")
        scope_execution = (ROOT_DIR / "references" / "agent" / "scope-execution-options-format.md").read_text(encoding="utf-8")
        scope_options = (ROOT_DIR / "references" / "agent" / "scope-options-format.md").read_text(encoding="utf-8")
        scope_selection_prompts = (ROOT_DIR / "references" / "agent" / "scope-selection-prompts-format.md").read_text(encoding="utf-8")
        self.assertIn("Design A / Hybrid Handoff", handoff)
        self.assertIn("`workflow-state.yaml`", handoff)
        self.assertIn("`scope-options.md`", handoff)
        self.assertIn("`final_traceability_matrix`", handoff)
        self.assertIn("`traceability_ref`", handoff)
        self.assertIn("`scope-selection-prompts.md`", handoff)
        self.assertIn("`scope-contract.md`", handoff)
        self.assertIn("`scope-coverage-gaps.md`", handoff)
        self.assertIn("`prompt.scope-gaps-to-reviewer.md`", handoff)
        self.assertIn("`prompt.scope-assertions-to-reviewer.md`", handoff)
        self.assertIn("`source-assertions.json`", handoff)
        self.assertIn("`current_stage`", state)
        self.assertIn("`stage_status`", state)
        self.assertIn("`next_skill`", state)
        self.assertIn("ready-for-gap-review", state)
        self.assertIn("prompt.scope-gaps-to-reviewer.md", state)
        self.assertIn("## Blocking Gap Gate", state)
        self.assertIn("accepted_risks", state)
        self.assertIn("## Цель этапа", prompt)
        self.assertIn("## Gate завершения", prompt)
        self.assertIn("## Контекст", scope_contract)
        self.assertIn("## Scope Identity", scope_contract)
        self.assertIn("минимум один package", scope_contract)
        self.assertIn("single_scope_with_internal_packages | split_into_external_scopes", scope_contract)
        self.assertIn("## Coverage Gaps", scope_gaps)
        self.assertIn("Accepted-risk Deferral", scope_gaps)
        self.assertIn("## Требуемые Уточнения", scope_gaps)
        self.assertIn("## Рекомендуемый Следующий Шаг", scope_execution)
        self.assertIn("## Вариант 1. Запуск Через Iteration", scope_execution)
        self.assertIn("optional helper artifact", scope_execution)
        self.assertIn("## Candidate Scope", scope_options)
        self.assertIn("`scope-options.md`", scope_options)
        self.assertIn("## Prompt Templates", scope_selection_prompts)
        self.assertIn("`scope-selection-prompts.md`", scope_selection_prompts)
        self.assertIn("`prompt.scope-assertions-to-reviewer.md`", scope_selection_prompts)
        self.assertIn("`source_assertion_review`", scope_selection_prompts)

    def test_locator_and_scope_analyzer_produce_stage_handoff_artifacts(self) -> None:
        locator = (ROOT_DIR / "skills" / "ft-source-locator" / "SKILL.md").read_text(encoding="utf-8")
        scope = (ROOT_DIR / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`source-selection.md`", locator)
        self.assertIn("`workflow-state.yaml`", locator)
        self.assertIn("`source-locator-session-log.md`", locator)
        self.assertIn("`manual-scope`", scope)
        self.assertIn("`agent-proposed-scope`", scope)
        self.assertIn("`scope-options.md`", scope)
        self.assertIn("`scope-selection-prompts.md`", scope)
        self.assertIn("`scope-contract.md`", scope)
        self.assertIn("`scope-coverage-gaps.md`", scope)
        self.assertIn("`scope-execution-options.md`", scope)
        self.assertIn("../../references/agent/scope-contract-format.md", scope)
        self.assertIn("../../references/agent/scope-coverage-gaps-format.md", scope)
        self.assertIn("../../references/agent/scope-execution-options-format.md", scope)
        self.assertIn("`prompt.scope-to-writer.md`", scope)
        self.assertIn("`prompt.scope-to-iteration.md`", scope)
        self.assertIn("`prompt.scope-gaps-to-reviewer.md`", scope)
        self.assertIn("не создавай handoff к writer", scope)

    def test_writer_reviewer_and_iteration_use_state_and_prompt_handoffs(self) -> None:
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        iteration = (ROOT_DIR / "skills" / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`prompt.writer-to-reviewer.round-N.md`", writer)
        self.assertIn("`stage_status: ready-for-review`", writer)
        self.assertIn("`prompt.reviewer-to-writer.round-N.md`", reviewer)
        self.assertIn("`prompt.reviewer-to-ui-prep.md`", reviewer)
        self.assertIn("`workflow-state.yaml`", iteration)
        self.assertIn("`stage-handoffs/`", iteration)

    def test_ui_automation_prep_requires_signed_off_state_handoff(self) -> None:
        ui_prep = (ROOT_DIR / "skills" / "ft-ui-automation-prep" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`prompt.reviewer-to-ui-prep.md`", ui_prep)
        self.assertIn("`stage_status: ready-for-next-stage`", ui_prep)
        self.assertIn("`next_skill: ft-ui-automation-prep`", ui_prep)


class ScopeToWriterPromptFormationTests(unittest.TestCase):
    def test_scope_to_writer_prompt_contract_carries_critical_writer_rules(self) -> None:
        prompt_format = (ROOT_DIR / "references" / "agent" / "next-step-prompt-format.md").read_text(encoding="utf-8")
        scope_skill = (ROOT_DIR / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(encoding="utf-8")

        for expected in [
            "Special Contract `prompt.scope-gaps-to-reviewer.md`",
            "Специальный Контракт `prompt.scope-to-writer.md`",
            "regression/baseline artifacts",
            "observable artifact",
            "stage_status: ready-for-review",
            "fresh-eval-run",
        ]:
            self.assertIn(expected, prompt_format)

        for expected in [
            "Правила Формирования `prompt.scope-to-writer.md`",
            "package-by-package writer-pass",
            "package ledger self-check",
            "Package Test Design Plan self-check",
            "observable artifact gate",
            "silently promote to `covered`",
        ]:
            self.assertIn(expected, scope_skill)


if __name__ == "__main__":
    unittest.main()
