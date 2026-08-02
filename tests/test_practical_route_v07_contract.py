from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PracticalRouteV07ContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT_DIR / relative).read_text(encoding="utf-8")

    def test_reference_defines_default_practical_route_and_explicit_heavy_routes(self) -> None:
        content = self.read("references/agent/practical-test-case-route-v0.7.md")
        self.assertIn("default route for ordinary FT test-case writing", content)
        self.assertIn("test-design-matrix.md", content)
        self.assertIn("coverage_classes", content)
        self.assertIn("source-assertions", content)
        self.assertIn("Use heavier routes only when the user explicitly asks", content)
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

        self.assertIn("practical route v0.7", agents)
        self.assertIn("не являются default-маршрутом", agents)
        self.assertIn("New test-case suite, default", skills)
        self.assertIn("practical route v0.7", skills)
        self.assertIn("Explicit production shadow", skills)

    def test_writer_and_reviewer_do_not_require_heavy_process_for_practical_route(self) -> None:
        writer = self.read("skills/ft-test-case-writer/SKILL.md")
        reviewer = self.read("skills/ft-test-case-reviewer/SKILL.md")
        scope = self.read("skills/ft-scope-analyzer/SKILL.md")

        self.assertIn("practical_v0_7", writer)
        self.assertIn("test-design-matrix.md", writer)
        self.assertIn("do not create source assertions", writer)
        self.assertIn("practical_v0_7", reviewer)
        self.assertIn("must not require source assertion receipts", reviewer)
        self.assertIn("review-independence.md", reviewer)
        self.assertIn("route next to `ft-test-case-writer`", scope)
        self.assertIn("not to `source_assertion_review`", scope)

    def test_runtime_language_rule_allows_metadata_enums_but_not_agent_process_text(self) -> None:
        content = self.read("references/agent/practical-test-case-route-v0.7.md")
        self.assertIn("human-facing runtime text is Russian", content)
        self.assertIn("`Positive`, `Negative`, `High`, `Medium`, `Low`", content)
        self.assertIn("no phrases such as `source-backed`", content)
        self.assertIn("agent-process", content)
        self.assertIn("language in runtime test cases", content)

    def test_v07_requires_coverage_class_decomposition_and_reviewer_independence(self) -> None:
        content = self.read("references/agent/practical-test-case-route-v0.7.md")
        self.assertIn("Mandatory coverage class decomposition", content)
        self.assertIn("one sample invalid value", content)
        self.assertIn("coverage-class-catalog.md", content)
        self.assertIn("text/name-like fields", content)
        self.assertIn("numeric ranges and amounts", content)
        self.assertIn("generated documents and mappings", content)
        self.assertIn("review-independence.md", content)
        self.assertIn("independent_signoff_claim_allowed", content)

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

    def test_practical_writer_and_reviewer_load_coverage_class_catalog(self) -> None:
        manifest = self.read("references/agent/instruction-loading-manifest.md")
        writer = self.read("skills/ft-test-case-writer/SKILL.md")
        reviewer = self.read("skills/ft-test-case-reviewer/SKILL.md")

        self.assertIn("references/qa/coverage-class-catalog.md", manifest)
        self.assertIn("coverage-class-catalog.md", writer)
        self.assertIn("coverage-class-catalog.md", reviewer)


if __name__ == "__main__":
    unittest.main()
