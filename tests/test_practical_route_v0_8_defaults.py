from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PracticalRouteV08DefaultsTests(unittest.TestCase):
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
        self.assertIn("If the accepted matrix review is absent, block TC review", reviewer)

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


if __name__ == "__main__":
    unittest.main()
