from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT_DIR / "skills"
REFERENCES_DIR = ROOT_DIR / "references"

EXPECTED_SKILLS = {
    "ft-source-locator",
    "ft-scope-analyzer",
    "ft-test-case-iteration",
    "ft-test-case-writer",
    "ft-test-case-reviewer",
    "ft-ui-automation-prep",
    "agent-architecture-auditor",
}

REQUIRED_AGENT_REFS = {
    "content-placement.md",
    "skill-boundaries.md",
    "duplication-policy.md",
    "maintenance-checklist.md",
    "audit-output-format.md",
    "quality-feedback-loop.md",
    "instruction-loading-manifest.md",
    "task-start-skill-routing-format.md",
    "writer-runtime-workflow.md",
    "writer-process-workflow.md",
    "writer-table-workflow.md",
    "writer-revision-workflow.md",
    "writer-remediation-workflow.md",
    "writer-runtime-contract.md",
    "writer-table-artifacts-format.md",
    "writer-handoff-format.md",
    "writer-revision-output-format.md",
    "session-based-review-cycle-format.md",
    "review-cycle-stage-contract-v2.md",
    "prepared-stage-package-format.md",
    "codex-sdk-orchestration-format.md",
}

REQUIRED_QA_REFS = {
    "test-case-format.md",
    "coverage-checklist.md",
    "traceability-rules.md",
    "review-findings-format.md",
    "traceability-matrix-format.md",
    "ui-automation-prep-format.md",
    "test-case-runtime-format.md",
    "coverage-runtime-checklist.md",
    "coverage-input-boundaries.md",
    "coverage-integration-async.md",
}


class AgentArchitectureTests(unittest.TestCase):
    def test_expected_skills_exist(self) -> None:
        actual = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
        self.assertEqual(EXPECTED_SKILLS, actual)

    def test_each_skill_has_required_files(self) -> None:
        for skill_name in EXPECTED_SKILLS:
            skill_dir = SKILLS_DIR / skill_name
            self.assertTrue((skill_dir / "SKILL.md").exists(), skill_name)
            self.assertTrue((skill_dir / "agents" / "openai.yaml").exists(), skill_name)

    def test_required_shared_references_exist(self) -> None:
        agent_files = {path.name for path in (REFERENCES_DIR / "agent").iterdir() if path.is_file()}
        qa_files = {path.name for path in (REFERENCES_DIR / "qa").iterdir() if path.is_file()}
        self.assertTrue(REQUIRED_AGENT_REFS.issubset(agent_files))
        self.assertTrue(REQUIRED_QA_REFS.issubset(qa_files))

    def test_repo_has_contributing_guide_and_test_runner_script(self) -> None:
        self.assertTrue((ROOT_DIR / "CONTRIBUTING.md").exists())
        self.assertTrue((ROOT_DIR / "scripts" / "run_tests.py").exists())

    def test_skills_index_lists_all_active_skills(self) -> None:
        content = (SKILLS_DIR / "README.md").read_text(encoding="utf-8")
        for skill_name in EXPECTED_SKILLS:
            self.assertIn(f"`{skill_name}`", content)

    def test_skills_index_mentions_script_first_audit_workflow(self) -> None:
        content = (SKILLS_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("script-first workflow", content)
        self.assertIn("audit_agent_architecture.py", content)
        self.assertIn("scripts/review_cycle_backend_dispatcher.py", content)
        self.assertIn("SDK используется только как явно выбранный fallback", content)
        self.assertIn("session-based-review-cycle-format.md", content)
        self.assertIn("codex-sdk-orchestration-format.md", content)

    def test_skills_index_and_agents_describe_full_reviewer_mode(self) -> None:
        skills_index = (SKILLS_DIR / "README.md").read_text(encoding="utf-8")
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("режиме `full`", skills_index)
        self.assertIn("`traceability` -> `structure` -> `test-design`", skills_index)
        self.assertIn("umbrella-reviewer", agents)
        self.assertIn("режиме `full`", agents)

    def test_agents_file_stays_policy_focused(self) -> None:
        content = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("## Рабочий процесс", content)
        self.assertNotIn("1. Найди", content)
        self.assertIn("## Маршрутизация", content)
        self.assertIn("не дублируй", content.lower())
        self.assertIn("agent-architecture-auditor", content)

    def test_agents_require_task_start_skill_disclosure(self) -> None:
        content = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Перед началом содержательной работы", content)
        self.assertIn("выбранный skill или цепочку skills", content)
        self.assertIn("не требует project skill-а", content)
        self.assertIn("task-start-skill-routing-format.md", content)
        self.assertIn("не отдельный этап согласования", content)

    def test_readme_and_contributing_document_canonical_test_command(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        contributing = (ROOT_DIR / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn(".\\.venv\\Scripts\\python.exe scripts/run_tests.py", readme)
        self.assertIn(".\\.venv\\Scripts\\python.exe -m unittest discover -s tests", readme)
        self.assertIn("artifact-validator-sharded", readme)
        self.assertIn("agent-layer-fast", readme)
        self.assertIn("Raw `unittest discover` не является каноническим", contributing)
        self.assertIn(".\\.venv\\Scripts\\python.exe scripts/run_tests.py", contributing)
        self.assertIn(".\\.venv\\Scripts\\python.exe -m unittest discover -s tests", contributing)
        self.assertIn("artifact-validator-sharded", contributing)
        self.assertIn("agent-layer-fast", contributing)
        self.assertIn(".\\.venv\\Scripts\\python.exe -m unittest", contributing)

    def test_writer_skill_uses_shared_references(self) -> None:
        content = (SKILLS_DIR / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../../references/agent/writer-runtime-workflow.md", content)
        self.assertIn("../../references/agent/writer-table-workflow.md", content)
        self.assertIn("../../references/agent/writer-revision-workflow.md", content)
        self.assertIn("../../references/agent/writer-remediation-workflow.md", content)
        self.assertIn("../../references/qa/test-case-format.md", content)
        self.assertIn("../../references/qa/review-findings-format.md", content)
        self.assertIn("../../references/qa/traceability-matrix-format.md", content)
        self.assertNotIn("references/test-case-format.md", content)
        self.assertNotIn("references/coverage-checklist.md", content)

    def test_writer_skill_stays_runtime_sized(self) -> None:
        content = (SKILLS_DIR / "ft-test-case-writer" / "SKILL.md").read_bytes()
        self.assertLess(len(content), 20 * 1024)

    def test_no_local_references_left_in_writer_skill(self) -> None:
        self.assertFalse((SKILLS_DIR / "ft-test-case-writer" / "references").exists())

    def test_reviewer_related_skills_describe_mode_based_contract(self) -> None:
        reviewer = (SKILLS_DIR / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        writer = (SKILLS_DIR / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        iteration = (SKILLS_DIR / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`review_mode = full | traceability | structure | test-design`", reviewer)
        self.assertIn("`scope_gap_review`", reviewer)
        self.assertIn("`structure_preflight`", reviewer)
        self.assertIn("`semantic_traceability_test_design`", reviewer)
        self.assertIn("`structure_format_final`", reviewer)
        self.assertIn("`semantic_regression`", reviewer)
        self.assertIn("`review_mode`", writer)
        self.assertIn("session-based writer/reviewer cycle", iteration)
        self.assertIn("structure preflight", iteration)
        self.assertIn("semantic review", iteration)

    def test_ft_process_skills_describe_pdf_structure_cross_check(self) -> None:
        locator = (SKILLS_DIR / "ft-source-locator" / "SKILL.md").read_text(encoding="utf-8")
        scope = (SKILLS_DIR / "ft-scope-analyzer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (SKILLS_DIR / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("PDF-версию основного ФТ для сверки структуры", locator)
        self.assertIn("PDF-версия основного ФТ", scope)
        self.assertIn("сверки структуры разделов", reviewer)

    def test_session_based_review_cycle_contract_is_wired(self) -> None:
        index = (REFERENCES_DIR / "agent" / "instruction-contract-index.md").read_text(
            encoding="utf-8"
        )
        routing = (REFERENCES_DIR / "agent" / "task-start-skill-routing-format.md").read_text(
            encoding="utf-8"
        )
        manifest = (REFERENCES_DIR / "agent" / "instruction-loading-manifest.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "Session-based review cycle, prepared stage packages, backend-independent stage contract",
            index,
        )
        self.assertIn("test_case_agent/review_cycle/contracts.py", index)
        self.assertIn("test_case_agent/review_cycle/transitions.py", index)
        self.assertIn("test_case_agent/review_cycle/orchestration.py", index)
        self.assertIn("tests/test_review_cycle_backend_matrix.py", index)
        self.assertIn("tests/test_review_cycle_stage_contract.py", index)
        self.assertIn("review-cycle-stage-contract-v2.md", index)
        self.assertIn("review_cycle.session_based", routing)
        self.assertIn("writer.session_initial_draft", manifest)
        self.assertIn("reviewer.scope_gap_review", manifest)
        self.assertIn("reviewer.scope_gap_review", routing)
        self.assertIn("reviewer.semantic_traceability_test_design", manifest)
        self.assertIn("sdk_orchestration.review_cycle", manifest)

    def test_auditor_skill_uses_script_first_workflow(self) -> None:
        content = (SKILLS_DIR / "agent-architecture-auditor" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("skills/agent-architecture-auditor/scripts/audit_agent_architecture.py", content)
        self.assertIn("Baseline audit", content)
        self.assertIn("Manual follow-up", content)
        self.assertIn("../../references/agent/audit-output-format.md", content)

    def test_quality_feedback_loop_is_wired(self) -> None:
        index = (REFERENCES_DIR / "agent" / "instruction-contract-index.md").read_text(encoding="utf-8")
        iteration = (SKILLS_DIR / "ft-test-case-iteration" / "SKILL.md").read_text(encoding="utf-8")
        skills_index = (SKILLS_DIR / "README.md").read_text(encoding="utf-8")
        candidate_readme = ROOT_DIR / "evals" / "candidates" / "README.md"

        self.assertIn("Quality feedback loop and eval candidates", index)
        self.assertIn("references/agent/quality-feedback-loop.md", index)
        self.assertIn("../../references/agent/quality-feedback-loop.md", iteration)
        self.assertIn("evals/candidates/YYYY-MM-DD-<failure-class>-<short-scope>.md", iteration)
        self.assertIn("../references/agent/quality-feedback-loop.md", skills_index)
        self.assertTrue(candidate_readme.exists())

    def test_run_tests_script_uses_controlled_discovery_for_full_suite(self) -> None:
        content = (ROOT_DIR / "scripts" / "run_tests.py").read_text(encoding="utf-8")
        self.assertIn("discover_test_modules", content)
        self.assertIn("EXCLUDED_FULL_DISCOVERY_MODULES", content)
        self.assertIn("run_full_tests", content)
        self.assertIn("run_agent_layer_tests", content)
        self.assertIn("AGENT_LAYER_FAST_MODULES", content)
        self.assertIn('"agent-layer"', content)
        self.assertIn('"agent-layer-fast"', content)
        self.assertIn('"architecture"', content)
        self.assertIn('"artifact-validator"', content)
        self.assertIn('"artifact-validator-sharded"', content)
        self.assertIn("ARTIFACT_VALIDATOR_MODULE", content)
        self.assertIn("DEFAULT_ARTIFACT_VALIDATOR_SHARDS", content)
        self.assertIn("--shard-index", content)
        self.assertIn("--shard-count", content)
        self.assertIn("tests.test_instruction_context_resolver", content)
        self.assertIn("tests.test_codex_review_cycle_runner", content)
        self.assertIn("tests.test_session_based_review_cycle_contracts", content)
        self.assertIn("tests.test_task_start_skill_routing", content)
        self.assertIn("audit_agent_architecture.py", content)
        self.assertIn('"--fail-on"', content)
        self.assertIn('"warning"', content)


if __name__ == "__main__":
    unittest.main()
