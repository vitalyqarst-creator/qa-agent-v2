from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_stage_summary",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PracticalStageSummaryValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    def make_package(
        self,
        *,
        code_root: Path | None = None,
        ft_root: Path | None = None,
        artifact_write_root: Path | None = None,
        root_split_allowed: str = "no",
        root_split_authority: str = "not-applicable",
        validator_errors_count: int = 0,
        validator_errors_classification: str = "none",
        next_stage_transition: str = "writer allowed",
        link_summary: bool = True,
    ) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        code_root = code_root or base
        ft_root = ft_root or base / "fts" / "Sample"
        artifact_write_root = artifact_write_root or ft_root / "work"
        artifact_write_root.mkdir(parents=True, exist_ok=True)
        summary = artifact_write_root / "practical-stage-summary.md"
        summary.write_text(
            "\n".join(
                [
                    "# Practical Stage Summary",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    f"| code_root | `{code_root}` |",
                    f"| ft_package_root | `{ft_root}` |",
                    f"| artifact_write_root | `{artifact_write_root}` |",
                    f"| root_split_allowed | `{root_split_allowed}` |",
                    f"| root_split_authority | `{root_split_authority}` |",
                    f"| validator_errors_count | `{validator_errors_count}` |",
                    f"| validator_errors_classification | `{validator_errors_classification}` |",
                    f"| validator_errors_evidence | `not-applicable` |",
                    f"| next_stage_transition | `{next_stage_transition}` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        if link_summary:
            workflow = ft_root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
            workflow.parent.mkdir(parents=True, exist_ok=True)
            workflow.write_text(
                "\n".join(
                    [
                        "latest_artifacts:",
                        "  practical_stage_summary: work/practical-stage-summary.md",
                    ]
                ),
                encoding="utf-8",
            )
        return ft_root

    def finding_ids(self, root: Path) -> set[str]:
        report = self.validator.validate(root)
        return {finding["id"] for finding in report["findings"]}

    def test_accepts_linked_summary_with_consistent_roots_and_clean_validator(self) -> None:
        ids = self.finding_ids(self.make_package())

        self.assertNotIn("practical-stage-summary-missing-root-consistency-fields", ids)
        self.assertNotIn("practical-stage-summary-root-split-unapproved", ids)
        self.assertNotIn("practical-stage-summary-not-linked-from-workflow", ids)
        self.assertNotIn("practical-stage-summary-validator-errors-unclassified", ids)
        self.assertNotIn("practical-stage-summary-validator-errors-allow-writer-unconditionally", ids)

    def test_rejects_unapproved_split_between_code_and_ft_package_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ids = self.finding_ids(
                self.make_package(
                    code_root=base / "code",
                    ft_root=base / "data" / "fts" / "Sample",
                    artifact_write_root=base / "data" / "fts" / "Sample" / "work",
                    root_split_allowed="no",
                )
            )

        self.assertIn("practical-stage-summary-root-split-unapproved", ids)

    def test_accepts_explicitly_approved_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ids = self.finding_ids(
                self.make_package(
                    code_root=base / "code",
                    ft_root=base / "data" / "fts" / "Sample",
                    artifact_write_root=base / "data" / "fts" / "Sample" / "work",
                    root_split_allowed="yes",
                    root_split_authority="user-approved split-root run",
                )
            )

        self.assertNotIn("practical-stage-summary-root-split-unapproved", ids)

    def test_rejects_summary_not_linked_from_workflow_state(self) -> None:
        ids = self.finding_ids(self.make_package(link_summary=False))

        self.assertIn("practical-stage-summary-not-linked-from-workflow", ids)

    def test_rejects_unclassified_validator_errors_before_writer(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_errors_count=2,
                validator_errors_classification="none",
                next_stage_transition="writer conditional",
            )
        )

        self.assertIn("practical-stage-summary-validator-errors-unclassified", ids)

    def test_rejects_unconditional_writer_allowed_when_validator_errors_exist(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_errors_count=1,
                validator_errors_classification="pre-existing-unrelated",
                next_stage_transition="writer allowed",
            )
        )

        self.assertIn("practical-stage-summary-validator-errors-allow-writer-unconditionally", ids)

    def test_unresolved_explicit_active_prompt_reports_finding_without_crashing(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "fts" / "Sample"
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        handoff.mkdir(parents=True)
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "ft_slug: Sample",
                    "scope_slug: sample",
                    "current_stage: ft-test-case-writer",
                    "stage_status: ready-for-next-stage",
                    "current_round: 1",
                    "next_skill: ft-test-case-reviewer",
                    "review_mode: matrix_review",
                    "required_inputs: []",
                    "latest_artifacts:",
                    "  active_transition_prompt: missing-prompt.md",
                    "open_questions: []",
                    "blocking_reasons: []",
                ]
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("workflow-state-active-transition-prompt-unresolved", ids)


if __name__ == "__main__":
    unittest.main()
