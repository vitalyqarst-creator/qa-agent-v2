from __future__ import annotations

import unittest
from pathlib import Path

from test_case_agent import (
    Section,
    analyze_sections,
    classify_source_quality_issue,
    preview_chunks,
)
from test_case_agent.chunking import split_section


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DOC = next(
    path for path in (ROOT_DIR / "fts").glob("*/source/*.docx") if not path.name.startswith("~$")
)


class SourceParsingQualityTests(unittest.TestCase):
    def test_split_section_never_exceeds_max_chars_for_oversized_block(self) -> None:
        section = Section(
            section_id="1.1",
            title="1.1 Large table",
            level=1,
            path=["1.1 Large table"],
            source_path=Path("source.docx"),
            content_blocks=["A" * 25],
        )

        chunks = split_section(section, max_chars=10)

        self.assertEqual([10, 10, 5], [len(chunk.text) for chunk in chunks])
        self.assertTrue(all(len(chunk.text) <= 10 for chunk in chunks))

    def test_split_section_rejects_nonpositive_max_chars(self) -> None:
        section = Section(
            section_id="1.1",
            title="1.1",
            level=1,
            path=["1.1"],
            source_path=Path("source.docx"),
            content_blocks=["text"],
        )

        with self.assertRaises(ValueError):
            split_section(section, max_chars=0)

    def test_analyze_sections_flags_many_untitled_sections(self) -> None:
        sections = [
            Section(
                section_id=f"section-{index}",
                title=f"Generated {index}",
                level=1,
                path=[f"Generated {index}"],
                source_path=Path("source.docx"),
                content_blocks=["text"],
            )
            for index in range(1, 6)
        ]

        issues = analyze_sections(sections, max_chars=100)

        self.assertIn("source-quality-many-untitled-sections", {issue.issue_id for issue in issues})
        self.assertIn("source-quality-no-numeric-sections", {issue.issue_id for issue in issues})

    def test_analyze_sections_flags_oversized_blocks(self) -> None:
        sections = [
            Section(
                section_id="1.1",
                title="1.1",
                level=1,
                path=["1.1"],
                source_path=Path("source.docx"),
                content_blocks=["A" * 101],
            )
        ]

        issues = analyze_sections(sections, max_chars=100)

        self.assertIn("source-quality-oversized-blocks", {issue.issue_id for issue in issues})

    def test_source_quality_policy_keeps_structural_risks_info_in_compatible_mode(self) -> None:
        issues = analyze_sections(
            [
                Section(
                    section_id="1.1",
                    title="1.1",
                    level=1,
                    path=["1.1"],
                    source_path=Path("source.docx"),
                    content_blocks=["A" * 101],
                )
            ],
            max_chars=100,
        )
        issue = next(item for item in issues if item.issue_id == "source-quality-oversized-blocks")

        self.assertEqual("info", classify_source_quality_issue(issue, policy="compatible"))
        self.assertEqual("warning", classify_source_quality_issue(issue, policy="strict"))

    def test_source_quality_policy_keeps_missing_requirements_as_warning(self) -> None:
        issue = analyze_sections([], max_chars=100)[0]

        self.assertEqual("warning", classify_source_quality_issue(issue, policy="compatible"))
        self.assertEqual("warning", classify_source_quality_issue(issue, policy="strict"))

    def test_preview_chunks_respects_max_chars_on_real_source(self) -> None:
        chunks = preview_chunks(SOURCE_DOC, max_sections=20, max_chars=12000)

        self.assertTrue(chunks)
        self.assertTrue(all(len(chunk.text) <= 12000 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
