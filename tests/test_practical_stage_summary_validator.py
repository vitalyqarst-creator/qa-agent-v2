from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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
        validator_raw_errors_count: int = 0,
        validator_summary_self_check_errors_count: int = 0,
        validator_summary_self_check_errors_evidence: str = "not-applicable",
        validator_errors_classification: str = "none",
        validator_errors_evidence: str = "not-applicable",
        validator_scope_errors_count: int | None = None,
        validator_scope_errors_evidence: str = "not-applicable",
        validator_external_errors_count: int | None = None,
        validator_external_errors_evidence: str = "not-applicable",
        validator_warnings_count: int = 0,
        validator_warnings_classification: str = "none",
        validator_warnings_evidence: str = "not-applicable",
        per_scope_next_stage_transitions: str = "not-applicable",
        production_tc_clean: str = "not-applicable",
        git_persistence: str = "not-applicable",
        rematerialization_mode: str = "not-applicable",
        rematerialization_basis: str = "not-applicable",
        reporting_evidence: str = "`workflow-state.yaml`; `practical-stage-summary.md`; `not-created`",
        validator_primary_command: str | None = None,
        validator_primary_root: str | None = None,
        source_restore_provenance: str = "not-applicable",
        source_restore_sha256: str = "not-applicable",
        active_scope_ids: str = "01",
        next_stage_transition: str = "writer allowed",
        summary_stage: str = "not-applicable",
        tc_review_snapshot: bool = False,
        link_summary: bool = True,
    ) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        code_root = code_root or base
        ft_root = ft_root or base / "fts" / "Sample"
        artifact_write_root = artifact_write_root or ft_root / "work"
        artifact_write_root.mkdir(parents=True, exist_ok=True)
        (ft_root / "AGENT-NOTES.md").parent.mkdir(parents=True, exist_ok=True)
        (ft_root / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
        source_dir = ft_root / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "Sample.docx").write_text("fake-docx", encoding="utf-8")
        (source_dir / "Sample.xhtml").write_text("<html></html>", encoding="utf-8")
        (source_dir / "Sample.pdf").write_text("fake-pdf", encoding="utf-8")
        validator_primary_command = validator_primary_command or (
            f'python scripts/validate_agent_artifacts.py --root "{ft_root}" --json'
        )
        validator_primary_root = validator_primary_root or str(ft_root)
        summary = artifact_write_root / "practical-stage-summary.md"
        summary_rows = [
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
                    f"| validator_raw_errors_count | `{validator_raw_errors_count}` |",
                    "| validator_summary_self_check_errors_count | "
                    f"`{validator_summary_self_check_errors_count}` |",
                    "| validator_summary_self_check_errors_evidence | "
                    f"`{validator_summary_self_check_errors_evidence}` |",
                    f"| validator_errors_classification | `{validator_errors_classification}` |",
                    f"| validator_errors_evidence | `{validator_errors_evidence}` |",
                    f"| validator_warnings_count | `{validator_warnings_count}` |",
                    f"| validator_warnings_classification | `{validator_warnings_classification}` |",
                    f"| validator_warnings_evidence | `{validator_warnings_evidence}` |",
                    f"| per_scope_next_stage_transitions | `{per_scope_next_stage_transitions}` |",
                    f"| production_tc_clean | `{production_tc_clean}` |",
                    f"| git_persistence | `{git_persistence}` |",
                    f"| rematerialization_mode | `{rematerialization_mode}` |",
                    f"| rematerialization_basis | `{rematerialization_basis}` |",
                    f"| reporting_evidence | {reporting_evidence} |",
                    f"| validator_primary_command | `{validator_primary_command}` |",
                    f"| validator_primary_root | `{validator_primary_root}` |",
                    "| source_row_counts | `not-applicable` |",
                    f"| source_restore_provenance | `{source_restore_provenance}` |",
                    f"| source_restore_sha256 | `{source_restore_sha256}` |",
                    f"| active_scope_ids | `{active_scope_ids}` |",
                    f"| next_stage_transition | `{next_stage_transition}` |",
                    "| next_safe_step | `Продолжить работу на следующем разрешенном этапе.` |",
                    f"| summary_stage | `{summary_stage}` |",
                    "",
                    "## Scope transitions",
                    "",
                    "| scope | verdict | next_stage_transition | source_contradiction | tc_with_status_decision | reason |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| sample | matrix-accepted | writer allowed | not-applicable | not-applicable | Матрица принята. |",
                    "",
                    "## Current stage actions",
                    "",
                    "- Подготовлен handoff текущего этапа.",
                    "",
                    "## Prior state context",
                    "",
                    "- Результаты предыдущих этапов здесь не повторяются.",
                    "",
                ]
        if validator_scope_errors_count is not None:
            summary_rows[12:12] = [
                f"| validator_scope_errors_count | `{validator_scope_errors_count}` |",
                f"| validator_scope_errors_evidence | `{validator_scope_errors_evidence}` |",
                f"| validator_external_errors_count | `{validator_external_errors_count}` |",
                f"| validator_external_errors_evidence | `{validator_external_errors_evidence}` |",
            ]
        summary.write_text(
            "\n".join(summary_rows),
            encoding="utf-8",
        )
        if tc_review_snapshot:
            practical = ft_root / "work" / "practical" / "sample"
            practical.mkdir(parents=True, exist_ok=True)
            (practical / "review-findings.md").write_text(
                "\n".join(
                    [
                        "# TC Review Findings",
                        "",
                        "## Verdict",
                        "",
                        "`tc-accepted`",
                        "",
                        "## Review Metadata",
                        "",
                        "| field | value |",
                        "| --- | --- |",
                        "| scope_slug | `sample` |",
                        "| review_mode | `tc_review` |",
                        "| review_round | `1` |",
                        "| reviewer_task_or_session | `task-001` |",
                        "| reviewer_execution_surface | `codex-task` |",
                        "",
                        "## Blocking Findings",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with summary.open("a", encoding="utf-8") as handle:
                handle.write(
                    "## TC Review Snapshot\n\n"
                    "| scope | verdict | blocking_finding_count | reviewer_task_or_session | reviewer_execution_surface |\n"
                    "| --- | --- | ---: | --- | --- |\n"
                    "| sample | tc-accepted | 0 | `task-001` | `codex-task` |\n"
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
        self.assertNotIn("practical-stage-summary-missing-operational-fields", ids)
        self.assertNotIn("practical-stage-summary-validator-warnings-unclassified", ids)
        self.assertNotIn("practical-stage-summary-validator-warning-count-stale", ids)
        self.assertNotIn("practical-stage-summary-validator-error-layers-missing", ids)
        self.assertNotIn("practical-stage-summary-current-prior-sections-missing", ids)
        self.assertNotIn("practical-stage-summary-primary-validator-root-invalid", ids)
        self.assertNotIn("practical-stage-summary-rematerialization-invalid", ids)
        self.assertNotIn("practical-stage-summary-reporting-evidence-invalid", ids)

    def test_matrix_review_ready_state_requires_pending_matrix_transition(self) -> None:
        root = self.make_package(
            next_stage_transition="matrix-review allowed",
            per_scope_next_stage_transitions="yes",
            summary_stage="matrix-authoring",
        )
        summary = root / "work" / "practical-stage-summary.md"
        text = summary.read_text(encoding="utf-8").replace(
            "| sample | matrix-accepted | writer allowed | not-applicable | not-applicable | Матрица принята. |",
            "| sample | matrix-created-pending-review | matrix-review allowed | no | not-applicable | Матрица подготовлена. |",
        )
        summary.write_text(text, encoding="utf-8")
        workflow = root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
        workflow.write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "current_stage: ft-test-case-writer",
                    "stage_status: ready-for-review",
                    "next_skill: ft-test-case-reviewer",
                    "review_mode: matrix_review",
                    "latest_artifacts:",
                    "  practical_stage_summary: work/practical-stage-summary.md",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        matrix = root / "work" / "practical" / "sample" / "test-design-matrix.md"
        matrix.parent.mkdir(parents=True)
        matrix.write_text("# Матрица тест-дизайна\n", encoding="utf-8")

        self.assertNotIn(
            "practical-stage-summary-matrix-review-state-mismatch",
            self.finding_ids(root),
        )

        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "matrix-created-pending-review", "matrix-not-created"
            ),
            encoding="utf-8",
        )

        self.assertIn(
            "practical-stage-summary-matrix-review-state-mismatch",
            self.finding_ids(root),
        )

    def test_ignores_immutable_controller_snapshot_summary(self) -> None:
        root = self.make_package()
        snapshot = (
            root
            / "work"
            / "practical"
            / "sample"
            / "review-launch-preflight-r1.controller-state"
            / "practical-stage-summary.md"
        )
        snapshot.parent.mkdir(parents=True)
        snapshot.write_text("# Historical snapshot\n", encoding="utf-8")

        ids = self.finding_ids(root)

        self.assertNotIn("practical-stage-summary-missing-root-consistency-fields", ids)

    def test_warns_when_summary_uses_legacy_completed_stage_section(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        text = summary.read_text(encoding="utf-8")
        text = text.replace("## Current stage actions", "## Completed In This Stage")
        text = text.replace("## Prior state context\n\n- Previous stages are not repeated here.\n\n", "")
        summary.write_text(text, encoding="utf-8")

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-current-prior-sections-missing", ids)

    def test_named_stage_requires_current_and_prior_state_sections(self) -> None:
        root = self.make_package(summary_stage="contract-only-status-repair")
        summary = root / "work" / "practical-stage-summary.md"
        text = summary.read_text(encoding="utf-8")
        text = text.replace("## Current stage actions\n\n- Подготовлен handoff текущего этапа.\n\n", "")
        text = text.replace("## Prior state context\n\n- Результаты предыдущих этапов здесь не повторяются.\n\n", "")
        summary.write_text(text, encoding="utf-8")

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-current-prior-sections-required", ids)

    def test_contract_only_status_repair_requires_per_scope_receipt(self) -> None:
        root = self.make_package(summary_stage="contract-only-status-repair")

        ids = self.finding_ids(root)

        self.assertIn("practical-contract-only-status-repair-receipt-invalid", ids)

    def test_contract_only_status_repair_accepts_complete_receipt(self) -> None:
        root = self.make_package(summary_stage="contract-only-status-repair")
        revision = root / "work" / "practical" / "sample" / "tc-revision-summary.md"
        revision.parent.mkdir(parents=True)
        revision.write_text(
            "\n".join(
                [
                    "# TC Revision Summary: sample",
                    "",
                    "## Status Assertions",
                    "",
                    "| tc_id | status_after_revision |",
                    "| --- | --- |",
                    "| `TC-SAMPLE-001` | `needs-test-data` |",
                    "",
                    "## Contract-only Repair",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    "| repair_type | `contract_only_status_repair` |",
                    "| semantic_change | `no` |",
                    "| affected_tc_ids | `TC-SAMPLE-001` |",
                    "| evidence | `writer-revision-summary-missing-status-assertions` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertNotIn("practical-contract-only-status-repair-receipt-invalid", ids)

    def test_contract_only_status_repair_rejects_semantic_change(self) -> None:
        root = self.make_package(summary_stage="contract-only-status-repair")
        revision = root / "work" / "practical" / "sample" / "tc-revision-summary.md"
        revision.parent.mkdir(parents=True)
        revision.write_text(
            "\n".join(
                [
                    "## Status Assertions",
                    "",
                    "| tc_id | status_after_revision |",
                    "| --- | --- |",
                    "| `TC-SAMPLE-001` | `needs-test-data` |",
                    "",
                    "## Contract-only Repair",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    "| repair_type | `contract_only_status_repair` |",
                    "| semantic_change | `yes` |",
                    "| affected_tc_ids | `TC-SAMPLE-001` |",
                    "| evidence | `writer-revision-summary-missing-status-assertions` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-contract-only-status-repair-receipt-invalid", ids)

    def test_rejects_conflicting_duplicate_validator_count(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        with summary.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n## Secondary Validator Report\n\n"
                "| field | value |\n"
                "| --- | --- |\n"
                "| errors_count | `1` |\n"
            )

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-validator-duplicate-count-mismatch", ids)

    def test_rejects_stale_validator_info_count(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        text = summary.read_text(encoding="utf-8").replace(
            "| validator_warnings_count | `0` |",
            "| validator_info_count | `1` |\n| validator_warnings_count | `0` |",
        )
        summary.write_text(text, encoding="utf-8")

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-validator-info-count-stale", ids)

    def test_rejects_raw_error_count_that_does_not_match_validator(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        text = summary.read_text(encoding="utf-8").replace(
            "| validator_raw_errors_count | `0` |",
            "| validator_raw_errors_count | `1` |",
        )
        summary.write_text(text, encoding="utf-8")

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-validator-raw-error-count-stale", ids)

    def test_rejects_missing_validator_error_layers(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        text = "\n".join(
            line
            for line in summary.read_text(encoding="utf-8").splitlines()
            if not any(
                field in line
                for field in (
                    "validator_raw_errors_count",
                    "validator_summary_self_check_errors_count",
                    "validator_summary_self_check_errors_evidence",
                )
            )
        )
        summary.write_text(text, encoding="utf-8")

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-validator-error-layers-missing", ids)

    def test_rejects_unexpected_zero_self_check_evidence(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_summary_self_check_errors_evidence=(
                    "summary-check @ work/practical/other/practical-stage-summary.md"
                )
            )
        )

        self.assertIn(
            "practical-stage-summary-validator-self-check-evidence-unexpected",
            ids,
        )

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

    def test_rejects_not_applicable_error_classification_when_errors_exist(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_errors_count=1,
                validator_errors_classification="not-applicable",
                next_stage_transition="writer blocked",
            )
        )

        self.assertIn("practical-stage-summary-validator-errors-unclassified", ids)

    def test_rejects_not_applicable_warning_classification_when_warnings_exist(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=1,
                validator_warnings_classification="not-applicable",
                next_stage_transition="writer conditional",
            )
        )

        self.assertIn("practical-stage-summary-validator-warnings-unclassified", ids)

    def test_rejects_primary_validator_root_outside_ft_package(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_primary_command="python scripts/validate_agent_artifacts.py --root . --json",
                validator_primary_root=".",
            )
        )

        self.assertIn("practical-stage-summary-primary-validator-root-invalid", ids)

    def test_rejects_metadata_only_without_unchanged_input_basis(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                rematerialization_mode="metadata-only",
                rematerialization_basis="Обновлена сводка без описания состояния входов.",
            )
        )

        self.assertIn("practical-stage-summary-rematerialization-invalid", ids)

    def test_rejects_check_only_reporting_without_not_created_marker(self) -> None:
        root = self.make_package(
            reporting_evidence="`workflow-state.yaml`; `practical-stage-summary.md`"
        )
        summary = root / "work" / "practical-stage-summary.md"
        text = summary.read_text(encoding="utf-8")
        text = text.replace(
            "| reporting_evidence | `workflow-state.yaml`; `practical-stage-summary.md` |",
            "| review_launch_preflight_status | `check-only-allowed` |\n"
            "| review_launch_preflight_receipt | `not-applicable` |\n"
            "| review_launch_preflight_evidence | `--check-only allowed` |\n"
            "| reporting_evidence | `workflow-state.yaml`; `practical-stage-summary.md` |",
        )
        summary.write_text(text, encoding="utf-8")

        self.assertIn(
            "practical-stage-summary-reporting-evidence-invalid",
            self.finding_ids(root),
        )

    def test_rejects_unconditional_writer_allowed_when_validator_errors_exist(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_errors_count=1,
                validator_errors_classification="pre-existing-unrelated",
                next_stage_transition="writer allowed",
            )
        )

        self.assertIn("practical-stage-summary-validator-errors-allow-writer-unconditionally", ids)

    def test_rejects_unproven_preexisting_error_partition(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_errors_count=2,
                validator_errors_classification="pre-existing-unrelated",
                validator_errors_evidence="`error-one`; `error-two`",
                next_stage_transition="writer blocked",
            )
        )

        self.assertIn(
            "practical-stage-summary-validator-error-partition-unverified",
            ids,
        )

    def test_accepts_proven_preexisting_error_partition(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_errors_count=2,
                validator_errors_classification="pre-existing-unrelated",
                validator_errors_evidence=(
                    "`workflow-state-invalid-status` @ "
                    "`work/stage-handoffs/02-other/workflow-state.yaml`; "
                    "`writer-quality-gate-failed` @ "
                    "`work/test-design/02-other/writer-quality-gate.md`"
                ),
                validator_scope_errors_count=0,
                validator_scope_errors_evidence="not-applicable",
                validator_external_errors_count=2,
                validator_external_errors_evidence=(
                    "`workflow-state-invalid-status` @ "
                    "`work/stage-handoffs/02-other/workflow-state.yaml`; "
                    "`writer-quality-gate-failed` @ "
                    "`work/test-design/02-other/writer-quality-gate.md`"
                ),
                next_stage_transition="writer blocked",
            )
        )

        self.assertNotIn(
            "practical-stage-summary-validator-error-partition-unverified",
            ids,
        )

    def test_rejects_unclassified_validator_warnings_before_writer(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=2,
                validator_warnings_classification="none",
                next_stage_transition="writer conditional",
                per_scope_next_stage_transitions="yes",
            )
        )

        self.assertIn("practical-stage-summary-validator-warnings-unclassified", ids)

    def test_rejects_conditional_writer_without_per_scope_transitions(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=1,
                validator_warnings_classification="blocking-for-scope",
                next_stage_transition="writer conditional",
                per_scope_next_stage_transitions="not-applicable",
            )
        )

        self.assertIn("practical-stage-summary-missing-per-scope-transitions", ids)

    def test_rejects_conditional_tc_review_without_per_scope_transitions(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=1,
                validator_warnings_classification="blocking-for-scope",
                next_stage_transition="tc-review conditional",
                per_scope_next_stage_transitions="not-applicable",
            )
        )

        self.assertIn("practical-stage-summary-missing-per-scope-transitions", ids)

    def test_rejects_unconditional_tc_review_for_scope_blocking_warnings(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=1,
                validator_warnings_classification="blocking-for-scope",
                next_stage_transition="tc-review allowed",
                per_scope_next_stage_transitions="yes",
                production_tc_clean="yes",
            )
        )

        self.assertIn("practical-stage-summary-validator-warnings-allow-writer-unconditionally", ids)

    def test_rejects_tc_review_without_clean_production_tc_proof(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                next_stage_transition="tc-review conditional",
                per_scope_next_stage_transitions="yes",
                production_tc_clean="not-applicable",
            )
        )

        self.assertIn("practical-stage-summary-production-tc-not-clean-for-review", ids)

    def test_rejects_tc_review_summary_without_current_scope_snapshot(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                summary_stage="release-grade-independent-tc-review",
                next_stage_transition="writer conditional",
                per_scope_next_stage_transitions="yes",
            )
        )

        self.assertIn("practical-stage-summary-tc-review-snapshot-missing", ids)

    def test_accepts_tc_review_summary_with_current_scope_snapshot(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                summary_stage="release-grade-independent-tc-review",
                next_stage_transition="writer conditional",
                per_scope_next_stage_transitions="yes",
                tc_review_snapshot=True,
            )
        )

        self.assertNotIn("practical-stage-summary-tc-review-snapshot-missing", ids)
        self.assertNotIn("practical-stage-summary-tc-review-snapshot-mismatch", ids)

    def test_rejects_tc_review_snapshot_with_stale_finding_count(self) -> None:
        root = self.make_package(
            summary_stage="release-grade-independent-tc-review",
            next_stage_transition="writer conditional",
            per_scope_next_stage_transitions="yes",
            tc_review_snapshot=True,
        )
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "| sample | tc-accepted | 0 | `task-001` | `codex-task` |",
                "| sample | tc-accepted | 1 | `task-001` | `codex-task` |",
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-tc-review-snapshot-mismatch", ids)

    def test_accepts_tc_review_snapshot_with_matching_blocking_finding_count(self) -> None:
        root = self.make_package(
            summary_stage="release-grade-independent-tc-review",
            next_stage_transition="writer conditional",
            per_scope_next_stage_transitions="yes",
            tc_review_snapshot=True,
        )
        review = root / "work" / "practical" / "sample" / "review-findings.md"
        review.write_text(
            review.read_text(encoding="utf-8")
            + "\n### FINDING-001\n\n**Severity:** error\n",
            encoding="utf-8",
        )
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "| sample | tc-accepted | 0 | `task-001` | `codex-task` |",
                "| sample | tc-accepted | 1 | `task-001` | `codex-task` |",
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertNotIn("practical-stage-summary-tc-review-snapshot-mismatch", ids)

    def test_rejects_tc_review_when_dirty_tc_warning_is_classified_as_expected(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=1,
                validator_warnings_classification="mixed",
                validator_warnings_evidence="test-case-split-artifact-duplicated-sections",
                next_stage_transition="tc-review conditional",
                per_scope_next_stage_transitions="yes",
                production_tc_clean="yes",
            )
        )

        self.assertIn("practical-stage-summary-tc-review-with-dirty-production-testcases", ids)

    def test_requires_git_persistence_field(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            "\n".join(
                line
                for line in summary.read_text(encoding="utf-8").splitlines()
                if not line.startswith("| git_persistence |")
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-missing-operational-fields", ids)

    def test_requires_explicit_active_scope_allowlist(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            "\n".join(
                line
                for line in summary.read_text(encoding="utf-8").splitlines()
                if not line.startswith("| active_scope_ids |")
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-missing-operational-fields", ids)

    def test_rejects_nonexplicit_active_scope_allowlist(self) -> None:
        ids = self.finding_ids(self.make_package(active_scope_ids="all"))

        self.assertIn("practical-stage-summary-invalid-active-scope-ids", ids)

    def test_rejects_not_applicable_active_scope_allowlist(self) -> None:
        ids = self.finding_ids(self.make_package(active_scope_ids="not-applicable"))

        self.assertIn("practical-stage-summary-invalid-active-scope-ids", ids)

    def test_rejects_active_scope_id_without_handoff_directory(self) -> None:
        ids = self.finding_ids(self.make_package(active_scope_ids="99"))

        self.assertIn("practical-stage-summary-active-scope-id-unresolved", ids)

    def test_rejects_english_human_prose_in_summary(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "Продолжить работу на следующем разрешенном этапе.",
                "Run the next writer revision after validation.",
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-nonrussian-human-prose", ids)

    def test_allows_unquoted_technical_identifiers_in_russian_summary_reason(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "Матрица принята.",
                "Ограничения зафиксированы в GAP-002, AS.37 и TC026.",
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertNotIn("practical-stage-summary-nonrussian-human-prose", ids)

    def test_rejects_invalid_git_persistence_field(self) -> None:
        ids = self.finding_ids(self.make_package(git_persistence="ordinary git maybe"))

        self.assertIn("practical-stage-summary-invalid-git-persistence", ids)

    def test_rejects_stale_validator_warning_count_in_summary(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=1,
                validator_warnings_classification="nonblocking-info",
                validator_warnings_evidence="not-applicable",
                next_stage_transition="writer conditional",
                per_scope_next_stage_transitions="yes",
            )
        )

        self.assertIn("practical-stage-summary-validator-warning-count-stale", ids)

    def test_rejects_stale_validator_finding_evidence_in_summary(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_evidence="source-quality-old-warning-id",
            )
        )

        self.assertIn("practical-stage-summary-validator-evidence-stale", ids)

    def test_rejects_round_cap_without_source_contradiction_classification(self) -> None:
        root = self.make_package(
            next_stage_transition="writer conditional",
            per_scope_next_stage_transitions="yes",
        )
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8")
            + "\n## Per-Scope Transitions\n\n"
            + "| Scope | status | safe_next_step |\n"
            + "| --- | --- | --- |\n"
            + "| scope-02 | round-cap-reached | explicit controller decision required |\n",
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-round-cap-missing-source-contradiction-classification", ids)
        self.assertIn("practical-stage-summary-round-cap-generic-controller-block", ids)

    def test_accepts_round_cap_with_status_policy_and_no_source_contradiction(self) -> None:
        root = self.make_package(
            next_stage_transition="writer conditional",
            per_scope_next_stage_transitions="yes",
        )
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8")
            + "\n## Per-Scope Transitions\n\n"
            + "| Scope | status | source_contradiction | tc_with_status_decision |\n"
            + "| --- | --- | --- | --- |\n"
            + "| scope-02 | round-cap-reached | source_contradiction: no | write with `needs-test-data` |\n",
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertNotIn("practical-stage-summary-round-cap-missing-source-contradiction-classification", ids)
        self.assertNotIn("practical-stage-summary-round-cap-generic-controller-block", ids)

    def test_rejects_active_scope_transition_with_prose_in_status_decision(self) -> None:
        root = self.make_package(
            next_stage_transition="tc-review conditional",
            per_scope_next_stage_transitions="yes",
        )
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "| sample | matrix-accepted | writer allowed | not-applicable | not-applicable | Матрица принята. |",
                "| sample | matrix-changes-required | tc-review conditional | no | TC-001 needs-test-data | Требуется выпуск с пометкой. |",
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-stage-summary-invalid-round-cap-decision", ids)

    def test_rejects_unconditional_writer_allowed_for_scope_blocking_warnings(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                validator_warnings_count=1,
                validator_warnings_classification="blocking-for-scope",
                next_stage_transition="writer allowed",
                per_scope_next_stage_transitions="yes",
            )
        )

        self.assertIn("practical-stage-summary-validator-warnings-allow-writer-unconditionally", ids)

    def test_requires_sha256_when_source_restore_is_reported(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                source_restore_provenance="restored from previous clean package",
                source_restore_sha256="missing",
            )
        )

        self.assertIn("practical-stage-summary-source-restore-sha256-missing", ids)

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

    def test_nested_package_summary_resolves_without_domain_level_index(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        nested_ft_root = base / "fts" / "Partners" / "Partners-v1"
        self.make_package(
            code_root=base,
            ft_root=nested_ft_root,
            artifact_write_root=nested_ft_root / "work",
        )

        ids = self.finding_ids(base / "fts" / "Partners")

        self.assertNotIn("practical-stage-summary-not-linked-from-workflow", ids)
        self.assertNotIn("workflow-state-active-transition-prompt-unresolved", ids)

    def test_rejects_domain_level_handoff_outside_nested_ft_package(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        domain_root = base / "fts" / "Partners"
        nested_ft_root = domain_root / "Partners-v1"
        self.make_package(
            code_root=base,
            ft_root=nested_ft_root,
            artifact_write_root=nested_ft_root / "work",
        )
        index_dir = domain_root / "work" / "stage-handoffs" / "00-partners-v1-package-index"
        index_dir.mkdir(parents=True, exist_ok=True)
        (index_dir / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "ft_slug: Partners",
                    "scope_slug: Partners-v1-package-index",
                    "current_stage: ft-test-case-reviewer",
                    "stage_status: blocked-input",
                    "current_round: 1",
                    "next_skill: none",
                    "required_inputs: []",
                    "latest_artifacts: {}",
                    "open_questions: []",
                    "blocking_reasons: []",
                ]
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(domain_root)

        self.assertIn("ft-domain-level-handoff-artifacts", ids)

    def test_practical_summary_requires_physical_source_package_files(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "fts" / "Partners" / "Partners-v1"
        root.mkdir(parents=True)
        (root / "test-cases").mkdir()
        summary = root / "work" / "practical-stage-summary.md"
        summary.parent.mkdir(parents=True)
        summary.write_text(
            "\n".join(
                [
                    "# Practical Stage Summary",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    f"| code_root | `{Path(tmp.name)}` |",
                    f"| ft_package_root | `{root}` |",
                    f"| artifact_write_root | `{root / 'work'}` |",
                    "| root_split_allowed | `no` |",
                    "| root_split_authority | `not-applicable` |",
                    "| validator_errors_count | `1` |",
                    "| validator_errors_classification | `next-stage-blocker` |",
                    "| validator_errors_evidence | `missing source package` |",
                    "| validator_warnings_count | `0` |",
                    "| validator_warnings_classification | `none` |",
                    "| validator_warnings_evidence | `not-applicable` |",
                    "| per_scope_next_stage_transitions | `not-applicable` |",
                    "| production_tc_clean | `not-applicable` |",
                    "| git_persistence | `not-applicable` |",
                    "| source_restore_provenance | `not-applicable` |",
                    "| source_restore_sha256 | `not-applicable` |",
                    "| next_stage_transition | `writer blocked` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        workflow = root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            "\n".join(
                [
                    "latest_artifacts:",
                    "  practical_stage_summary: work/practical-stage-summary.md",
                ]
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-route-source-package-incomplete", ids)

    def test_practical_v08_summary_requires_execution_working_directory(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        content = summary.read_text(encoding="utf-8").replace(
            "| code_root |",
            "| route_profile | `practical route v0.8.1` |\n| code_root |",
        )
        summary.write_text(content, encoding="utf-8")

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertIn(
            "practical-stage-summary-missing-execution-working-directory",
            {finding.id for finding in findings},
        )

    def test_practical_v08_summary_rejects_stale_code_commit(self) -> None:
        root = self.make_package()
        summary = root / "work" / "practical-stage-summary.md"
        stale_commit = "b" * 40
        current_commit = "a" * 40
        content = summary.read_text(encoding="utf-8").replace(
            "| code_root |",
            "| route_profile | `practical route v0.8.1` |\n"
            f"| execution_working_directory | `{root.parent.parent}` |\n"
            "| code_root |",
        )
        content += "\n".join(
            [
                "",
                "## Code Version Gate",
                "",
                "| field | expected | actual | status |",
                "| --- | --- | --- | --- |",
                f"| commit | `{stale_commit}` | `{stale_commit}` | `pass` |",
                "",
            ]
        )
        summary.write_text(content, encoding="utf-8")

        with patch.object(self.validator, "current_git_commit_for_code_root", return_value=current_commit):
            findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertIn(
            "practical-stage-summary-code-version-stale",
            {finding.id for finding in findings},
        )

    def test_rejects_stale_revision_aliases_against_active_prompt(self) -> None:
        root = self.make_package(
            summary_stage="scope01-writer-revision-r6-completed",
        )
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "Продолжить работу на следующем разрешенном этапе.",
                "Выполнить независимую проверку r5.",
            ),
            encoding="utf-8",
        )
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        prompt = handoff / "prompt.writer-to-reviewer.round-6.md"
        prompt.write_text("# Reviewer prompt\n", encoding="utf-8")
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "current_round: 5",
                    "active_transition_prompt: work/stage-handoffs/01-sample/prompt.writer-to-reviewer.round-6.md",
                    "latest_artifacts:",
                    "  practical_stage_summary: work/practical-stage-summary.md",
                ]
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertIn(
            "practical-stage-summary-revision-alias-stale",
            {finding.id for finding in findings},
        )

    def test_accepts_current_revision_aliases_against_active_prompt(self) -> None:
        root = self.make_package(
            summary_stage="scope01-writer-revision-r6-completed",
        )
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "Продолжить работу на следующем разрешенном этапе.",
                "Выполнить независимую проверку r6.",
            ),
            encoding="utf-8",
        )
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        prompt = handoff / "prompt.writer-to-reviewer.round-6.md"
        prompt.write_text("# Reviewer prompt\n", encoding="utf-8")
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "current_round: 6",
                    "active_transition_prompt: work/stage-handoffs/01-sample/prompt.writer-to-reviewer.round-6.md",
                    "latest_artifacts:",
                    "  practical_stage_summary: work/practical-stage-summary.md",
                ]
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertNotIn(
            "practical-stage-summary-revision-alias-stale",
            {finding.id for finding in findings},
        )

    def test_rejects_missing_current_round_when_active_prompt_has_revision(self) -> None:
        root = self.make_package(summary_stage="scope01-writer-revision-r6-completed")
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        prompt = handoff / "prompt.writer-to-reviewer.round-6.md"
        prompt.write_text("# Reviewer prompt\n", encoding="utf-8")
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "active_transition_prompt: work/stage-handoffs/01-sample/prompt.writer-to-reviewer.round-6.md",
                    "latest_artifacts:",
                    "  practical_stage_summary: work/practical-stage-summary.md",
                ]
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(
            root / "work" / "practical-stage-summary.md",
            root,
        )

        self.assertIn(
            "practical-stage-summary-revision-alias-stale",
            {finding.id for finding in findings},
        )

    def test_reads_active_revision_prompt_from_latest_artifacts(self) -> None:
        root = self.make_package(summary_stage="scope01-writer-revision-r6-completed")
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        prompt = handoff / "prompt.writer-to-reviewer.round-6.md"
        prompt.write_text("# Reviewer prompt\n", encoding="utf-8")
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "current_round: 5",
                    "latest_artifacts:",
                    "  active_transition_prompt: work/stage-handoffs/01-sample/prompt.writer-to-reviewer.round-6.md",
                    "  practical_stage_summary: work/practical-stage-summary.md",
                ]
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(
            root / "work" / "practical-stage-summary.md",
            root,
        )

        self.assertIn(
            "practical-stage-summary-revision-alias-stale",
            {finding.id for finding in findings},
        )

    def test_rejects_historical_revision_in_current_stage_actions(self) -> None:
        root = self.make_package(summary_stage="scope01-writer-revision-r6-completed")
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "- Подготовлен handoff текущего этапа.",
                "- Ограниченная доработка writer r5 завершена.",
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertIn(
            "practical-stage-summary-current-action-stale-round",
            {finding.id for finding in findings},
        )

    def test_accepts_current_revision_in_current_stage_actions(self) -> None:
        root = self.make_package(summary_stage="scope01-writer-revision-r6-completed")
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "- Подготовлен handoff текущего этапа.",
                "- Ограниченная доработка writer r6 завершена.",
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertNotIn(
            "practical-stage-summary-current-action-stale-round",
            {finding.id for finding in findings},
        )

    def test_rejects_allowed_preflight_not_recorded_in_controller_state(self) -> None:
        root = self.make_package(summary_stage="scope01-writer-revision-r6-completed")
        summary = root / "work" / "practical-stage-summary.md"
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        prompt = handoff / "prompt.writer-to-reviewer.round-6.md"
        prompt.write_text("# Reviewer prompt\n", encoding="utf-8")
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "current_round: 6",
                    "tc_review_gate_status: pending-review-launch-preflight",
                    "final_independent_tc_review_status: pending-launch-preflight-round-6",
                    "latest_artifacts:",
                    "  active_transition_prompt: work/stage-handoffs/01-sample/prompt.writer-to-reviewer.round-6.md",
                ]
            ),
            encoding="utf-8",
        )
        receipt = root / "work" / "practical" / "sample" / "review-launch-preflight-r6.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            '{"status":"allowed","allowed":true,"review_mode":"tc_review"}\n',
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertIn(
            "practical-stage-summary-allowed-preflight-unrecorded",
            {finding.id for finding in findings},
        )

    def test_accepts_allowed_preflight_recorded_in_controller_state(self) -> None:
        root = self.make_package(summary_stage="scope01-writer-revision-r6-completed")
        summary = root / "work" / "practical-stage-summary.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace(
                "| summary_stage | `scope01-writer-revision-r6-completed` |",
                "\n".join(
                    [
                        "| review_launch_preflight_status | `allowed` |",
                        "| review_launch_preflight_receipt | `work/practical/sample/review-launch-preflight-r6.json` |",
                        "| summary_stage | `scope01-writer-revision-r6-completed` |",
                    ]
                ),
            ),
            encoding="utf-8",
        )
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        prompt = handoff / "prompt.writer-to-reviewer.round-6.md"
        prompt.write_text("# Reviewer prompt\n", encoding="utf-8")
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "current_round: 6",
                    "tc_review_gate_status: preflight-allowed-round-6",
                    "final_independent_tc_review_status: ready-to-launch-round-6",
                    "review_launch_preflight_round_6: allowed",
                    "latest_artifacts:",
                    "  active_transition_prompt: work/stage-handoffs/01-sample/prompt.writer-to-reviewer.round-6.md",
                    "  review_launch_preflight: work/practical/sample/review-launch-preflight-r6.json",
                ]
            ),
            encoding="utf-8",
        )
        receipt = root / "work" / "practical" / "sample" / "review-launch-preflight-r6.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            '{"status":"allowed","allowed":true,"review_mode":"tc_review"}\n',
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertNotIn(
            "practical-stage-summary-allowed-preflight-unrecorded",
            {finding.id for finding in findings},
        )

    def test_completed_review_does_not_require_reviewer_dispatch_state(self) -> None:
        root = self.make_package(summary_stage="scope01-writer-revision-r6-pending")
        summary = root / "work" / "practical-stage-summary.md"
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        prompt = handoff / "prompt.reviewer-to-writer.round-6.md"
        prompt.write_text("# Writer prompt\n", encoding="utf-8")
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "scope_slug: sample",
                    "current_round: 6",
                    "stage_status: ready-for-writer-revision",
                    "tc_review_gate_status: final-review-changes-required",
                    "final_independent_tc_review_status: changes-required-round-6",
                    "latest_artifacts:",
                    "  active_transition_prompt: work/stage-handoffs/01-sample/prompt.reviewer-to-writer.round-6.md",
                ]
            ),
            encoding="utf-8",
        )
        receipt = root / "work" / "practical" / "sample" / "review-launch-preflight-r6.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            '{"status":"allowed","allowed":true,"review_mode":"tc_review"}\n',
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_practical_stage_summary(summary, root)

        self.assertNotIn(
            "practical-stage-summary-allowed-preflight-unrecorded",
            {finding.id for finding in findings},
        )


if __name__ == "__main__":
    unittest.main()
