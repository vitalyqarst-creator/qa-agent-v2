from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PracticalRouteV08DefaultsTests(unittest.TestCase):
    def load_validator(self):
        module_path = ROOT_DIR / "scripts" / "validate_agent_artifacts.py"
        spec = importlib.util.spec_from_file_location("validate_agent_artifacts_for_v08_tests", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_practical_route_runs_as_macro_stage_by_default(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.9.md").read_text(
            encoding="utf-8"
        )
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        skills = (ROOT_DIR / "skills" / "README.md").read_text(encoding="utf-8")
        routing = (ROOT_DIR / "references" / "agent" / "task-start-skill-routing-format.md").read_text(
            encoding="utf-8"
        )

        for content in (route, agents, skills, routing):
            self.assertIn("macro-stage", content)
            self.assertIn("accepted baseline", content)

        self.assertIn("условный matrix review", route)
        self.assertIn("ровно одна целевая writer revision", route)
        self.assertIn("final TC review", route)
        self.assertIn("one compact macro-stage", skills)
        self.assertIn("accepted baseline", routing)

    def test_scope_selection_is_compact_and_not_a_false_input_blocker(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        workflow = (ROOT_DIR / "references" / "agent" / "workflow-state-format.md").read_text(
            encoding="utf-8"
        )
        analyzer = (ROOT_DIR / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        prompts = (ROOT_DIR / "references" / "agent" / "scope-selection-prompts-format.md").read_text(
            encoding="utf-8"
        )
        scope_options = (ROOT_DIR / "references" / "agent" / "scope-options-format.md").read_text(
            encoding="utf-8"
        )

        for content in (route, workflow, analyzer, prompts):
            self.assertIn("awaiting-user-scope-selection", content)
        self.assertIn("The prompt contains only the FT package path", route)
        self.assertIn("the selected `scope_slug`", route)
        self.assertIn("не перечисляет route restrictions", prompts)
        self.assertNotIn("source_assertion_review", prompts)
        self.assertNotIn("source_assertion_review", scope_options)
        self.assertIn("formal_source_requirement_codes()", scope_options)

    def test_metadata_only_preserves_source_selection_creation_provenance(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        analyzer = (ROOT_DIR / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        source_selection = (ROOT_DIR / "references" / "agent" / "source-selection-format.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("source-selection.md` would otherwise retain stale code", route)
        self.assertIn("original creation record", route)
        self.assertIn("source-locator session receipt", route)
        self.assertIn("source-selection-format.md", analyzer)
        for expected in (
            "Сохрани `Создано` и `Создано кем`; добавь `Обновлено` и `Обновлено кем`",
            "agent-decision-log.md",
            "source-locator-session-log.md",
        ):
            self.assertIn(expected, source_selection)
        self.assertRegex(source_selection, r"ограниченное\s+обновление метаданных")

    def test_matrix_review_requires_stage_summary_before_next_prompt(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        routing = (ROOT_DIR / "references" / "agent" / "task-start-skill-routing-format.md").read_text(
            encoding="utf-8"
        )

        for content in (route, writer, reviewer, routing):
            self.assertIn("practical-stage-summary.md", content)
            self.assertIn("accepted", content)
            self.assertIn("round-cap", content)
            self.assertIn("next safe step", content)
            self.assertIn("next_stage_transition", content)

        self.assertIn("before sending the next prompt", route)
        self.assertIn("TC-with-status decision", routing)
        for expected in (
            "code_root",
            "ft_package_root",
            "artifact_write_root",
            "root_split_allowed",
            "validator_errors_classification",
            "validator_warnings_classification",
            "per_scope_next_stage_transitions",
            "production_tc_clean",
            "git_persistence",
            "source_restore_provenance",
            "source_restore_sha256",
        ):
            self.assertIn(expected, route)
            self.assertIn(expected, writer)

        self.assertIn("Detached HEAD", route)
        self.assertIn("exact expected commit", route)
        self.assertIn("validator-warning classification", routing)
        self.assertIn("production_tc_clean", routing)
        self.assertIn("fresh validator counts/evidence", routing)
        self.assertIn("inside the actual FT package root", routing)

    def test_round_cap_policy_prefers_explicit_status_tc_over_blocking_when_source_is_clear(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.9.md").read_text(
            encoding="utf-8"
        )
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        skills = (ROOT_DIR / "skills" / "README.md").read_text(encoding="utf-8")
        compact = (ROOT_DIR / "skills" / "ft-practical-route" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Противоречие источников", route)
        for content in (route, agents, compact):
            self.assertIn("candidate-ui-calibration", content)
            self.assertIn("needs-test-data", content)
            self.assertIn("blocked-observability", content)

        for content in (agents, compact):
            self.assertIn("source contradiction", content)

        self.assertIn("Source contradiction", skills)

        self.assertIn("непредставимое требование", route)
        self.assertIn("не выдумывай TC", agents)

    def test_scope_analyzer_requires_source_parity_before_practical_writer(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        analyzer = (ROOT_DIR / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for content in (route, analyzer):
            self.assertIn("source-parity-check.md", content)
            self.assertIn("before writer handoff", content)
            self.assertIn("blocked-input", content)

        self.assertIn("source-row-inventory.md", route)
        self.assertIn("source-row-inventory.md", analyzer)

    def test_practical_route_keeps_xlsx_optional(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        matrix_format = (ROOT_DIR / "references" / "qa" / "traceability-matrix-format.md").read_text(
            encoding="utf-8"
        )

        for content in (route, writer, reviewer, matrix_format):
            self.assertIn("practical_v0_8", content)
            self.assertIn("XLSX", content)

        self.assertIn("Do not create an XLSX duplicate in `practical_v0_8`", route)
        self.assertIn("do not create XLSX duplicates", writer)
        self.assertIn("не создавай `.xlsx`-дубль по умолчанию", reviewer)
        self.assertIn("`.xlsx`-дубль не является default", matrix_format)

    def test_writer_cannot_release_before_independent_review(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for content in (route, writer):
            self.assertIn("released-*", content)
            self.assertIn("signed-off", content)

        self.assertIn("before an independent reviewer pass", route)
        self.assertIn("before review", writer)
        self.assertIn("draft-ready-for-review", route)
        self.assertIn("review-ready", writer)

    def test_writer_cannot_create_tc_before_matrix_review(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("design-matrix-only pass", route)
        self.assertIn("Do not create, update or overwrite canonical test cases", route)
        self.assertIn("verdict `matrix-accepted`", route)
        self.assertIn("first writer invocation is always", writer)
        self.assertIn("do not create or modify", writer)
        self.assertIn("fail closed unless", writer)
        self.assertIn("This pass must run before canonical test-case writing", reviewer)
        self.assertIn("The only practical exception is a matching per-scope round-cap record", reviewer)

    def test_practical_route_caps_default_review_rounds(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.9.md").read_text(
            encoding="utf-8"
        )
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        skills = (ROOT_DIR / "skills" / "README.md").read_text(encoding="utf-8")
        compact = (ROOT_DIR / "skills" / "ft-practical-route" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        routing = (ROOT_DIR / "references" / "agent" / "task-start-skill-routing-format.md").read_text(
            encoding="utf-8"
        )

        for content in (route, skills, compact, routing):
            self.assertIn("final independent TC review", content)

        self.assertIn("Matrix review обязателен только", route)
        self.assertIn("final independent TC review", agents)
        self.assertIn("одна целевая writer revision", route)
        self.assertIn("one targeted revision", skills)
        self.assertIn("one targeted writer revision at most", routing)

    def test_practical_bounded_revision_requires_status_assertions_and_full_final_review(self) -> None:
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )
        writer = (ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        reviewer = (ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        revision = (ROOT_DIR / "references" / "agent" / "writer-revision-output-format.md").read_text(
            encoding="utf-8"
        )
        review_format = (ROOT_DIR / "references" / "qa" / "review-findings-format.md").read_text(
            encoding="utf-8"
        )

        for content in (route, writer):
            self.assertIn("Status Assertions", content)
            self.assertIn("Требуется подтверждение", content)

        self.assertIn("Status Assertions", revision)

        for content in (route, reviewer, review_format):
            self.assertIn("Review Focus", content)
            self.assertIn("full-scope", content)

    def test_session_based_cycle_is_not_default_practical_route(self) -> None:
        lifecycle = (
            ROOT_DIR / "references" / "agent" / "session-based-review-cycle-format.md"
        ).read_text(encoding="utf-8")
        route = (ROOT_DIR / "references" / "agent" / "practical-test-case-route-v0.8.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("not the default route for ordinary FT test-case writing", lifecycle)
        self.assertIn("explicit automated review-cycle", lifecycle)
        self.assertIn("without", route)
        self.assertIn("multi-session repair cycles", route)

    def test_validator_routes_matrix_review_without_tc_review_prompt(self) -> None:
        validator = self.load_validator()

        matrix_state = {
            "current_stage": "ft-test-case-writer",
            "stage_status": "ready-for-next-stage",
            "next_skill": "ft-test-case-reviewer",
            "current_round": 1,
            "review_mode": "matrix_review",
        }
        self.assertEqual(
            validator.expected_transition_prompt(matrix_state),
            "prompt.matrix-to-reviewer.md",
        )
        self.assertEqual(
            validator.transition_prompt_kind("prompt.matrix-to-reviewer.md"),
            "matrix-to-reviewer",
        )
        self.assertFalse(validator.is_ready_for_review_state(matrix_state))

        tc_state = {
            "current_stage": "ft-test-case-writer",
            "stage_status": "ready-for-review",
            "next_skill": "ft-test-case-reviewer",
            "current_round": 1,
            "review_mode": "tc_review",
        }
        self.assertEqual(
            validator.expected_transition_prompt(tc_state),
            "prompt.writer-to-reviewer.round-1.md",
        )
        self.assertTrue(validator.is_ready_for_review_state(tc_state))

    def test_practical_scope_writer_handoff_accepts_scope_brief_without_legacy_contract(self) -> None:
        validator = self.load_validator()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "fts" / "Sample" / "work" / "stage-handoffs" / "01-sample"
            handoff.mkdir(parents=True)
            for name in ("source-selection.md", "scope-coverage-gaps.md", "scope-brief.md"):
                (handoff / name).write_text(f"# {name}\n", encoding="utf-8")
            (handoff / "prompt.scope-to-writer.md").write_text(
                "\n".join(
                    [
                        "## Цель этапа",
                        "Подготовить матрицу тест-дизайна.",
                        "## Входные артефакты",
                        "- `source-selection.md`",
                        "- `scope-coverage-gaps.md`",
                        "- `scope-brief.md`",
                        "- `workflow-state.yaml`",
                        "## Обязательные действия",
                        "- Изучить входные артефакты.",
                        "## Не делать",
                        "- Не расширять границы scope.",
                        "## Ожидаемые выходы",
                        "- `test-design-matrix.md`.",
                        "## Gate завершения",
                        "Матрица создана.",
                    ]
                ),
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample",
                        "scope_slug: sample",
                        "route_profile: practical_v0_8",
                        "current_stage: ft-scope-analyzer",
                        "stage_status: ready-for-next-stage",
                        "next_skill: ft-test-case-writer",
                        "required_inputs:",
                        "  - source-selection.md",
                        "  - scope-coverage-gaps.md",
                        "  - scope-brief.md",
                        "latest_artifacts:",
                        "  active_transition_prompt: prompt.scope-to-writer.md",
                    ]
                ),
                encoding="utf-8",
            )

            report = validator.validate(root)

        finding_ids = {finding["id"] for finding in report["findings"]}
        self.assertNotIn("workflow-state-scope-analyzer-missing-handoff-artifacts", finding_ids)
        self.assertNotIn("prompt-format-missing-required-scope-inputs", finding_ids)


if __name__ == "__main__":
    unittest.main()
