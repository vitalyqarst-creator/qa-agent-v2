from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_workflow_duplicates",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WorkflowStateDuplicateKeysTests(unittest.TestCase):
    def test_awaiting_user_scope_selection_is_a_valid_non_blocking_state(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "00-source-selection"
            handoff.mkdir(parents=True)
            (handoff / "scope-options.md").write_text("# Scope options\n", encoding="utf-8")
            (handoff / "scope-selection-prompts.md").write_text("# Prompts\n", encoding="utf-8")
            workflow_path = handoff / "workflow-state.yaml"
            workflow_path.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample",
                        "scope_slug: source-selection",
                        "current_stage: ft-scope-analyzer",
                        "stage_status: awaiting-user-scope-selection",
                        "current_round: 0",
                        "next_skill: ft-scope-analyzer",
                        "required_inputs: []",
                        "latest_artifacts:",
                        "  scope_options: work/stage-handoffs/00-source-selection/scope-options.md",
                        "  scope_selection_prompts: work/stage-handoffs/00-source-selection/scope-selection-prompts.md",
                        "open_questions:",
                        "  - Выбрать один scope.",
                        "blocking_reasons: []",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = validator.validate_workflow_state(workflow_path, root)

        finding_ids = {finding.id for finding in findings}
        self.assertNotIn("workflow-state-invalid-stage-status", finding_ids)
        self.assertNotIn("workflow-state-awaiting-user-scope-selection-invalid-routing", finding_ids)

    def test_duplicate_mapping_key_blocks_workflow_routing(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow_path = root / "workflow-state.yaml"
            workflow_path.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample",
                        "scope_slug: sample",
                        "current_stage: ft-test-case-writer",
                        "stage_status: blocked-quality-gate",
                        "current_round: 1",
                        "next_skill: ft-test-case-writer",
                        "required_inputs: []",
                        "latest_artifacts: {}",
                        "open_questions: []",
                        "blocking_reasons: []",
                        "blocking_reasons:",
                        "  - Повторяющийся ключ.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            findings, checks = validator.validate_workflow_state(workflow_path, root)

        self.assertIn(
            "workflow-state-duplicate-mapping-keys",
            {finding.id for finding in findings},
        )
        self.assertIn(
            "workflow-state-unique-mapping-keys",
            {check.name for check in checks if check.status == "fail"},
        )


if __name__ == "__main__":
    unittest.main()
