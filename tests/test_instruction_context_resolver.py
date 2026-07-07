from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "resolve_instruction_context.py"
MANIFEST_PATH = ROOT_DIR / "references" / "agent" / "instruction-loading-manifest.md"

REQUIRED_SCENARIOS = {
    "source_locator.discovery",
    "writer.initial_draft.simple",
    "writer.initial_draft.table",
    "writer.initial_draft.ui",
    "writer.initial_draft.numeric",
    "writer.initial_draft.integration",
    "writer.revision_from_findings",
    "writer.remediation.style",
    "writer.remediation.validator_failure",
    "writer.session_initial_draft",
    "writer.session_semantic_revision",
    "writer.session_format_revision",
    "reviewer.full_existing_cases",
    "reviewer.scope_gap_review",
    "reviewer.structure_preflight",
    "reviewer.semantic_traceability_test_design",
    "reviewer.structure_format_final",
    "reviewer.semantic_regression",
    "scope.manual",
    "scope.agent_proposed",
    "iteration.full_loop",
    "ui_automation_prep.signed_off",
    "architecture.audit",
    "sdk_orchestration.review_cycle",
}


class InstructionContextResolverTests(unittest.TestCase):
    def run_resolver(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

    def resolve_json(self, *args: str) -> dict:
        result = self.run_resolver(*args, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_manifest_and_resolver_exist(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists())
        self.assertTrue(MANIFEST_PATH.exists())

    def test_list_scenarios_exposes_required_set(self) -> None:
        result = self.run_resolver("--list-scenarios")
        self.assertEqual(result.returncode, 0, result.stderr)
        for scenario_id in REQUIRED_SCENARIOS:
            self.assertIn(scenario_id, result.stdout)

    def test_writer_simple_context_has_required_core_and_budget(self) -> None:
        payload = self.resolve_json(
            "--phase",
            "writer",
            "--mode",
            "initial_draft",
            "--scope-profile",
            "simple",
        )
        paths = {item["path"] for item in payload["files"]}
        self.assertEqual("writer.initial_draft.simple", payload["scenario"])
        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("AGENTS.md", paths)
        self.assertIn("skills/README.md", paths)
        self.assertIn("skills/ft-test-case-writer/SKILL.md", paths)
        self.assertIn("references/agent/writer-runtime-workflow.md", paths)
        self.assertIn("references/agent/writer-runtime-contract.md", paths)
        self.assertIn("references/qa/test-case-runtime-format.md", paths)
        self.assertIn("references/qa/coverage-runtime-checklist.md", paths)
        writer_skill = ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md"
        self.assertLess(len(writer_skill.read_bytes()), 20 * 1024)
        self.assertEqual(len(paths), len(payload["files"]))

    def test_conditional_references_are_not_loaded_for_simple_writer(self) -> None:
        payload = self.resolve_json("--scenario", "writer.initial_draft.simple")
        paths = {item["path"] for item in payload["files"]}
        skipped = {item["path"] for item in payload["skipped"]}

        self.assertNotIn("references/agent/mockup-visual-inventory-format.md", paths)
        self.assertNotIn("references/qa/review-findings-format.md", paths)
        self.assertNotIn("references/qa/test-case-style-examples.md", paths)
        self.assertNotIn("references/agent/strict-debt-report-2026-05-25.md", paths)
        self.assertNotIn("references/agent/writer-output-format.md", paths)
        self.assertNotIn("references/agent/writer-process-workflow.md", paths)
        self.assertNotIn("references/agent/writer-table-workflow.md", paths)
        self.assertNotIn("references/agent/writer-revision-workflow.md", paths)
        self.assertNotIn("references/agent/writer-remediation-workflow.md", paths)
        self.assertNotIn("references/agent/test-design-depth-policy.md", paths)
        self.assertNotIn("references/agent/tc-set-optimization-format.md", paths)
        self.assertNotIn("references/qa/test-case-format.md", paths)
        self.assertNotIn("references/qa/coverage-checklist.md", paths)
        self.assertNotIn("references/agent/writer-quality-gate-format.md", paths)

        self.assertIn("references/agent/mockup-visual-inventory-format.md", skipped)
        self.assertIn("references/agent/writer-table-workflow.md", skipped)
        self.assertIn("references/agent/writer-revision-workflow.md", skipped)
        self.assertIn("references/agent/writer-remediation-workflow.md", skipped)
        self.assertIn("references/agent/test-design-depth-policy.md", skipped)
        self.assertIn("references/agent/tc-set-optimization-format.md", skipped)
        self.assertIn("references/qa/review-findings-format.md", skipped)
        self.assertIn("references/qa/test-case-style-examples.md", skipped)

    def test_table_writer_loads_table_artifacts_but_not_ui_or_revision(self) -> None:
        payload = self.resolve_json("--scenario", "writer.initial_draft.table")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/agent/writer-process-workflow.md", paths)
        self.assertIn("references/agent/writer-table-workflow.md", paths)
        self.assertIn("references/agent/source-row-inventory-format.md", paths)
        self.assertIn("references/agent/source-table-normalization-format.md", paths)
        self.assertIn("references/agent/source-normalization-diagnostic-format.md", paths)
        self.assertIn("references/agent/dictionary-inventory-format.md", paths)
        self.assertIn("references/agent/test-design-decision-table-format.md", paths)
        self.assertIn("references/agent/coverage-obligation-table-format.md", paths)
        self.assertIn("references/agent/writer-table-artifacts-format.md", paths)
        self.assertIn("references/agent/writer-quality-gate-format.md", paths)
        self.assertNotIn("references/agent/writer-output-format.md", paths)
        self.assertNotIn("references/agent/mockup-visual-inventory-format.md", paths)
        self.assertNotIn("references/qa/review-findings-format.md", paths)

    def test_ui_writer_loads_mockup_reference_but_not_table_or_revision(self) -> None:
        payload = self.resolve_json("--scenario", "writer.initial_draft.ui")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/agent/mockup-visual-inventory-format.md", paths)
        self.assertNotIn("references/agent/source-row-inventory-format.md", paths)
        self.assertNotIn("references/qa/review-findings-format.md", paths)
        self.assertNotIn("references/agent/writer-output-format.md", paths)

    def test_numeric_writer_loads_input_boundary_reference_only(self) -> None:
        payload = self.resolve_json("--scenario", "writer.initial_draft.numeric")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/qa/coverage-input-boundaries.md", paths)
        self.assertNotIn("references/qa/coverage-integration-async.md", paths)
        self.assertNotIn("references/qa/coverage-checklist.md", paths)

    def test_integration_writer_loads_integration_reference_only(self) -> None:
        payload = self.resolve_json("--scenario", "writer.initial_draft.integration")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/qa/coverage-integration-async.md", paths)
        self.assertNotIn("references/qa/coverage-input-boundaries.md", paths)
        self.assertNotIn("references/qa/coverage-checklist.md", paths)

    def test_revision_writer_loads_findings_contracts_but_not_table_or_ui(self) -> None:
        payload = self.resolve_json("--scenario", "writer.revision_from_findings")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/agent/writer-process-workflow.md", paths)
        self.assertIn("references/agent/writer-revision-workflow.md", paths)
        self.assertIn("references/agent/writer-revision-output-format.md", paths)
        self.assertIn("references/qa/review-findings-format.md", paths)
        self.assertIn("references/qa/traceability-matrix-format.md", paths)
        self.assertNotIn("references/agent/source-row-inventory-format.md", paths)
        self.assertNotIn("references/agent/mockup-visual-inventory-format.md", paths)

    def test_session_writer_context_loads_cycle_contracts(self) -> None:
        payload = self.resolve_json("--scenario", "writer.session_semantic_revision")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/agent/session-based-review-cycle-format.md", paths)
        self.assertIn("references/agent/codex-sdk-orchestration-format.md", paths)
        self.assertIn("references/agent/writer-revision-workflow.md", paths)
        self.assertIn("references/qa/review-findings-format.md", paths)
        self.assertNotIn("references/qa/test-case-style-examples.md", paths)

    def test_style_remediation_loads_full_format_and_examples(self) -> None:
        payload = self.resolve_json("--scenario", "writer.remediation.style")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/qa/test-case-format.md", paths)
        self.assertIn("references/qa/test-case-style-examples.md", paths)

    def test_validator_failure_loads_deep_quality_references(self) -> None:
        payload = self.resolve_json("--scenario", "writer.remediation.validator_failure")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/agent/writer-remediation-workflow.md", paths)
        self.assertIn("references/agent/writer-output-format.md", paths)
        self.assertIn("references/agent/writer-quality-gate-format.md", paths)
        self.assertIn("references/qa/test-case-format.md", paths)
        self.assertIn("references/qa/coverage-runtime-checklist.md", paths)
        self.assertNotIn("references/qa/coverage-checklist.md", paths)

    def test_source_locator_discovery_context_loads_locator_core(self) -> None:
        payload = self.resolve_json("--scenario", "source_locator.discovery")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("skills/ft-source-locator/SKILL.md", paths)
        self.assertIn("references/agent/source-selection-format.md", paths)
        self.assertNotIn("skills/ft-test-case-writer/SKILL.md", paths)

    def test_xhtml_source_selection_contract_loads_for_downstream_scenarios(self) -> None:
        for scenario_id in (
            "source_locator.discovery",
            "scope.manual",
            "writer.initial_draft.table",
            "reviewer.full_existing_cases",
            "iteration.full_loop",
        ):
            with self.subTest(scenario_id=scenario_id):
                payload = self.resolve_json("--scenario", scenario_id)
                paths = {item["path"] for item in payload["files"]}

                self.assertEqual("pass", payload["budget"]["status"])
                self.assertIn("references/agent/source-selection-format.md", paths)

    def test_clarification_question_policy_loads_for_scope_and_iteration(self) -> None:
        for scenario_id in ("scope.manual", "iteration.full_loop"):
            with self.subTest(scenario_id=scenario_id):
                payload = self.resolve_json("--scenario", scenario_id)
                paths = {item["path"] for item in payload["files"]}

                self.assertEqual("pass", payload["budget"]["status"])
                self.assertIn("references/agent/requirements-clarification-questioning-policy.md", paths)

    def test_reviewer_context_loads_reviewer_and_runtime_contracts(self) -> None:
        payload = self.resolve_json("--scenario", "reviewer.full_existing_cases")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("skills/ft-test-case-reviewer/SKILL.md", paths)
        self.assertIn("references/agent/reviewer-output-format.md", paths)
        self.assertIn("references/agent/package-test-design-plan-format.md", paths)
        self.assertIn("references/qa/test-design-review-rubric.md", paths)
        self.assertIn("references/agent/test-design-defect-taxonomy.md", paths)
        self.assertIn("references/agent/dictionary-inventory-format.md", paths)
        self.assertIn("references/qa/test-case-runtime-format.md", paths)
        self.assertIn("references/agent/session-log-format.md", paths)

    def test_session_reviewer_contexts_are_split_by_review_purpose(self) -> None:
        structure = self.resolve_json("--scenario", "reviewer.structure_preflight")
        semantic = self.resolve_json("--scenario", "reviewer.semantic_traceability_test_design")
        formatting = self.resolve_json("--scenario", "reviewer.structure_format_final")

        structure_paths = {item["path"] for item in structure["files"]}
        semantic_paths = {item["path"] for item in semantic["files"]}
        formatting_paths = {item["path"] for item in formatting["files"]}

        self.assertIn("references/agent/session-based-review-cycle-format.md", structure_paths)
        self.assertIn("references/qa/test-case-runtime-format.md", structure_paths)
        self.assertNotIn("references/qa/test-design-review-rubric.md", structure_paths)

        self.assertIn("references/qa/test-design-review-rubric.md", semantic_paths)
        self.assertIn("references/qa/traceability-matrix-format.md", semantic_paths)
        self.assertIn("references/agent/dictionary-inventory-format.md", semantic_paths)
        self.assertNotIn("references/qa/test-case-style-examples.md", semantic_paths)

        self.assertIn("references/qa/test-case-format.md", formatting_paths)
        self.assertIn("references/qa/test-case-style-examples.md", formatting_paths)

    def test_scope_gap_reviewer_context_loads_scope_gap_contracts(self) -> None:
        payload = self.resolve_json("--scenario", "reviewer.scope_gap_review")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("skills/ft-test-case-reviewer/SKILL.md", paths)
        self.assertIn("references/agent/session-based-review-cycle-format.md", paths)
        self.assertIn("references/agent/scope-contract-format.md", paths)
        self.assertIn("references/agent/scope-coverage-gaps-format.md", paths)
        self.assertIn("references/agent/scope-clarification-requests-format.md", paths)
        self.assertIn("references/agent/requirements-clarification-questioning-policy.md", paths)
        self.assertIn("references/qa/review-findings-format.md", paths)
        self.assertNotIn("references/qa/test-case-format.md", paths)
        self.assertNotIn("references/qa/test-case-style-examples.md", paths)

    def test_sdk_orchestration_context_loads_runner_contracts_only(self) -> None:
        payload = self.resolve_json("--scenario", "sdk_orchestration.review_cycle")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("references/agent/session-based-review-cycle-format.md", paths)
        self.assertIn("references/agent/codex-sdk-orchestration-format.md", paths)
        self.assertIn("references/agent/task-start-skill-routing-format.md", paths)
        self.assertNotIn("skills/ft-test-case-writer/SKILL.md", paths)
        self.assertNotIn("skills/ft-test-case-reviewer/SKILL.md", paths)

    def test_ui_automation_prep_context_loads_ui_contracts(self) -> None:
        payload = self.resolve_json("--scenario", "ui_automation_prep.signed_off")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("skills/ft-ui-automation-prep/SKILL.md", paths)
        self.assertIn("references/agent/ui-evidence-policy.md", paths)
        self.assertIn("references/qa/automation-ready-lifecycle.md", paths)
        self.assertIn("references/qa/ui-automation-prep-format.md", paths)
        self.assertNotIn("references/qa/test-case-format.md", paths)

    def test_architecture_audit_context_loads_routing_contract(self) -> None:
        payload = self.resolve_json("--scenario", "architecture.audit")
        paths = {item["path"] for item in payload["files"]}

        self.assertEqual("pass", payload["budget"]["status"])
        self.assertIn("skills/agent-architecture-auditor/SKILL.md", paths)
        self.assertIn("references/agent/task-start-skill-routing-format.md", paths)
        self.assertIn("references/agent/audit-output-format.md", paths)

    def test_all_manifest_budgets_pass(self) -> None:
        for scenario_id in REQUIRED_SCENARIOS:
            result = self.run_resolver(
                "--scenario",
                scenario_id,
                "--budget-report",
                "--fail-on-budget",
            )
            self.assertEqual(result.returncode, 0, f"{scenario_id}\n{result.stdout}\n{result.stderr}")

    def test_depth_policy_budget_regression_scenarios_pass(self) -> None:
        for scenario_id in (
            "writer.initial_draft.table",
            "reviewer.full_existing_cases",
            "iteration.full_loop",
        ):
            with self.subTest(scenario_id=scenario_id):
                result = self.run_resolver(
                    "--scenario",
                    scenario_id,
                    "--budget-report",
                    "--fail-on-budget",
                )
                self.assertEqual(result.returncode, 0, f"{scenario_id}\n{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main()
