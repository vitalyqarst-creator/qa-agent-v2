from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PracticalRouteV08ContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT_DIR / relative).read_text(encoding="utf-8")

    def test_reference_defines_default_practical_route_and_explicit_heavy_routes(self) -> None:
        content = self.read("references/agent/practical-test-case-route-v0.8.md")
        normalized_content = " ".join(content.split())
        self.assertIn("default route for ordinary FT test-case writing", content)
        self.assertIn("test-design-matrix.md", content)
        self.assertIn("Классы покрытия", content)
        self.assertIn("Column headers", content)
        self.assertIn("must be Russian", content)
        self.assertIn("source-assertions", content)
        self.assertIn("Use heavier routes only when the user explicitly asks", content)
        self.assertIn("must not propose or", content)
        self.assertIn("separate Codex task/session", content)
        self.assertIn("Matrix review gate", content)
        self.assertIn("design-matrix-only pass", content)
        self.assertIn("Do not create, update or overwrite canonical test cases", content)
        self.assertIn("test-design-matrix-review.md", content)
        self.assertIn("Macro-stage execution", content)
        self.assertIn("Do not stop for user confirmation", content)
        self.assertIn("one bounded TC revision", content)
        self.assertIn("fast path", content)
        self.assertIn("TC draft after accepted matrix", content)
        self.assertIn("Start only when `test-design-matrix-review.md` has verdict", content)
        for forbidden_default in (
            "benchmark",
            "sharding",
            "semantic bridge",
            "source-qualified immutable",
            "ft-agent run",
        ):
            self.assertIn(forbidden_default, content)

    def test_global_routing_makes_practical_route_the_default_for_writing(self) -> None:
        agents = self.read("AGENTS.md")
        skills = self.read("skills/README.md")

        self.assertIn("practical route v0.8", agents)
        self.assertIn("не являются default-маршрутом", agents)
        self.assertIn("New test-case suite, macro-stage default", skills)
        self.assertIn("practical route v0.8", skills)
        self.assertIn("separate-session", skills)
        self.assertIn("Explicit production shadow", skills)

    def test_writer_and_reviewer_do_not_require_heavy_process_for_practical_route(self) -> None:
        writer = self.read("skills/ft-test-case-writer/SKILL.md")
        reviewer = self.read("skills/ft-test-case-reviewer/SKILL.md")
        scope = self.read("skills/ft-scope-analyzer/SKILL.md")

        self.assertIn("practical_v0_8", writer)
        self.assertIn("test-design-matrix.md", writer)
        self.assertIn("practical_v0_8_matrix", writer)
        self.assertIn("practical_v0_8_tc_after_matrix_accepted", writer)
        self.assertIn("do not create or modify", writer)
        self.assertIn("test-design-matrix-review.md", writer)
        self.assertIn("do not create source assertions", writer)
        self.assertIn("practical_v0_8", reviewer)
        self.assertIn("matrix_review", reviewer)
        self.assertIn("tc_review", reviewer)
        self.assertIn("before canonical test-case writing", reviewer)
        self.assertIn("must not require source assertion receipts", reviewer)
        self.assertIn("review-independence.md", reviewer)
        self.assertIn("Re-derive coverage from FT DOCX/PDF/XHTML", reviewer)
        self.assertIn("route next to `ft-test-case-writer`", scope)
        self.assertIn("not to `source_assertion_review`", scope)

    def test_runtime_language_rule_allows_metadata_enums_but_not_agent_process_text(self) -> None:
        content = self.read("references/agent/practical-test-case-route-v0.8.md")
        self.assertIn("human-facing runtime text is Russian", content)
        self.assertIn("`Positive`, `Negative`, `High`, `Medium`, `Low`", content)
        self.assertIn("no phrases such as `source-backed`", content)
        self.assertIn("agent-process", content)
        self.assertIn("language in runtime test cases", content)

    def test_setup_data_must_respect_integration_backed_fields(self) -> None:
        route = self.read("references/agent/practical-test-case-route-v0.8.md")
        partners = self.read("fts/Partners/Partners-v1/test-cases/9.3-struktura-i-dubli-partnerov.md")
        catalog = self.read("fts/Partners/Partners-v1/work/vendor-references/dadata-fixture-catalog.md")

        self.assertIn("setup/precondition data must respect", route)
        self.assertIn("even when the integration itself is not the", route)
        self.assertIn("FX-DADATA-PARTY-ROMASHKA-A-001", partners)
        self.assertIn("FX-DADATA-PARTY-ROMASHKA-B-001", partners)
        self.assertNotIn("ООО Автотест 9.3", partners)
        self.assertIn("запрос `4909128502`", partners)
        self.assertIn("запрос `2622004340`", partners)
        self.assertIn("Response SHA-256", catalog)

    def test_v08_requires_coverage_class_decomposition_and_reviewer_independence(self) -> None:
        content = self.read("references/agent/practical-test-case-route-v0.8.md")
        normalized_content = " ".join(content.split())
        self.assertIn("Mandatory coverage class decomposition", content)
        self.assertIn("one sample invalid value", content)
        self.assertIn("coverage-class-catalog.md", content)
        self.assertIn("Requiredness classes must be split by input mechanism", content)
        self.assertIn("all required fields are empty", content)
        self.assertIn("text/name-like fields", content)
        self.assertIn("numeric ranges and amounts", content)
        self.assertIn("generated documents and mappings", content)
        self.assertIn("review-independence.md", content)
        self.assertIn("independent_signoff_claim_allowed", content)
        self.assertIn("`test-design-matrix.md` is reviewed as writer output", content)
        self.assertIn("canonical `TC-*` writing is gated by accepted matrix review", content)
        self.assertIn("separate reviewer Codex task/session", content)
        self.assertIn("sub-agent", content)
        self.assertIn("reviewer_execution_surface", content)
        self.assertIn("reviewer_thread_url_or_id", content)
        self.assertIn("cannot be the final reviewer verdict", content)
        self.assertIn("short human-readable title", content)
        self.assertIn("not the full prompt body", normalized_content)
        self.assertIn("root consistency", content)
        self.assertIn("validator_errors_count", content)
        self.assertIn("validator_warnings_count", content)
        self.assertIn("validator_info_count", content)
        self.assertIn("per_scope_next_stage_transitions", content)
        self.assertIn("production_tc_clean", content)
        self.assertIn("git_persistence", content)
        self.assertIn("practical-stage-summary-template.md", content)
        self.assertIn("refresh_practical_stage_summary.py", content)
        self.assertIn("commit/push will not persist", content)
        self.assertIn("git add -f", content)
        self.assertIn("Stale counts", content)
        self.assertIn("tc-review conditional", content)
        self.assertIn("source_contradiction: yes/no", content)
        self.assertIn("source_restore_sha256", content)

    def test_practical_stage_summary_template_pins_enum_fields(self) -> None:
        template = self.read("references/agent/practical-stage-summary-template.md")

        self.assertIn("practical route v0.8.1", template)
        self.assertIn("Enum fields must contain only the enum value", template)
        self.assertIn("writer allowed / writer conditional / writer blocked", template)
        self.assertIn("tc-review allowed / tc-review conditional / tc-review blocked", template)
        self.assertIn("tracked / ignored-by-git / mixed / not-applicable", template)
        self.assertIn("validator_info_count", template)
        self.assertIn("refresh_practical_stage_summary.py", template)
        self.assertIn("ordinary commit/push will not", template)
        self.assertIn("git add -f <paths>", template)

    def test_practical_matrix_uses_russian_user_facing_columns(self) -> None:
        content = self.read("references/agent/practical-test-case-route-v0.8.md")
        for expected in (
            "| Источник | Проверяемое утверждение | Измерение тест-дизайна | Классы покрытия | TC-ID | Статус | Примечания |",
            "user-facing artifact",
            "do not use English technical aliases",
            "tools may normalize the Russian columns",
        ):
            self.assertIn(expected, content)

    def test_coverage_class_catalog_pins_common_triggered_groups(self) -> None:
        content = self.read("references/qa/coverage-class-catalog.md")
        for expected in (
            "Activation rule",
            "`digits-only`",
            "text-only / name-like input",
            "exact length `N`",
            "min/max length",
            "Numeric ranges and amounts",
            "Dates and date/time",
            "Requiredness and conditional requiredness",
            "Dictionaries, closed lists, autocomplete and integrations",
            "File upload",
            "Repeatable blocks and child rows",
            "Uniqueness and duplicate checks",
            "Status and lifecycle",
            "Cross-field dependencies and combinations",
            "Generated documents and mappings",
        ):
            self.assertIn(expected, content)

        for expected in (
            "Latin letters",
            "Cyrillic letters",
            "spaces",
            "hyphen or sign",
            "decimal separator",
            "punctuation or special symbol",
        ):
            self.assertIn(expected, content)

    def test_requiredness_coverage_is_split_by_input_mechanism(self) -> None:
        content = self.read("references/qa/coverage-class-catalog.md")
        for expected in (
            "First split requiredness by input mechanism",
            "Do not create one generic",
            "user-entered required value",
            "dictionary/autocomplete required selection",
            "system-filled required value",
            "dependent autofilled required value",
            "readonly required value",
            "action-created/repeatable row required value",
            "If a test case lists several required fields",
            "every listed",
            "field must be exercised in the steps",
            "System-filled, autofilled and readonly fields must not be tested",
        ):
            self.assertIn(expected, content)

    def test_parameterized_tc_must_not_cross_ui_levels(self) -> None:
        tc_format = self.read("references/qa/test-case-format.md")
        route = self.read("references/agent/practical-test-case-route-v0.8.md")
        rule_cards = self.read("references/agent/runtime-quality-rule-cards.md")
        writer = self.read("skills/ft-test-case-writer/SKILL.md")
        reviewer = self.read("skills/ft-test-case-reviewer/SKILL.md")

        for expected in (
            "одинаковый стартовый экран",
            "UI-уровень",
            "Parent entity",
            "child entity",
            "партнеры в списке партнеров и реквизиты внутри карточки партнера",
        ):
            self.assertIn(expected, tc_format)

        for expected in (
            "same start screen",
            "UI level",
            "parent/child entities",
            "automation-readiness",
        ):
            self.assertIn(expected, route)
            self.assertIn(expected, writer)

        self.assertIn("R-PARAMETER-UI-LEVEL", rule_cards)
        self.assertIn("parameterized-tc-crosses-ui-levels", rule_cards)
        self.assertIn("non-atomic-parameterization", reviewer)

    def test_practical_writer_and_reviewer_load_coverage_class_catalog(self) -> None:
        manifest = self.read("references/agent/instruction-loading-manifest.md")
        writer = self.read("skills/ft-test-case-writer/SKILL.md")
        reviewer = self.read("skills/ft-test-case-reviewer/SKILL.md")

        self.assertIn("references/qa/coverage-class-catalog.md", manifest)
        self.assertIn("coverage-class-catalog.md", writer)
        self.assertIn("Классы покрытия", writer)
        self.assertIn("requiredness checks must be split by input mechanism", writer)
        self.assertIn("coverage-class-catalog.md", reviewer)
        self.assertIn("requiredness checks are", reviewer)
        self.assertIn("Russian", reviewer)
        self.assertIn("visible headers", reviewer)


if __name__ == "__main__":
    unittest.main()
