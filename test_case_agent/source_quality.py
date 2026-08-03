from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from test_case_agent.models import Section

SourceQualityPolicy = Literal["compatible", "strict"]
SOURCE_QUALITY_POLICIES = {"compatible", "strict"}


@dataclass(frozen=True)
class SourceQualityIssue:
    issue_id: str
    severity: str
    details: str
    evidence: list[str]


def classify_source_quality_issue(
    issue: SourceQualityIssue,
    *,
    policy: SourceQualityPolicy = "compatible",
) -> str:
    if policy not in SOURCE_QUALITY_POLICIES:
        raise ValueError(f"Unsupported source quality policy: {policy}")

    if issue.issue_id == "source-quality-no-requirement-sections":
        return "warning"

    if policy == "strict":
        return issue.severity

    return "info"


def analyze_sections(
    sections: list[Section],
    *,
    max_chars: int,
    untitled_ratio_threshold: float = 0.75,
) -> list[SourceQualityIssue]:
    issues: list[SourceQualityIssue] = []
    non_preface = [section for section in sections if section.section_id != "preface"]
    if not non_preface:
        return [
            SourceQualityIssue(
                issue_id="source-quality-no-requirement-sections",
                severity="warning",
                details="No non-preface requirement sections were detected.",
                evidence=[],
            )
        ]

    untitled = [section for section in non_preface if section.section_id.startswith("section-")]
    if len(non_preface) >= 5 and len(untitled) / len(non_preface) >= untitled_ratio_threshold:
        issues.append(
            SourceQualityIssue(
                issue_id="source-quality-many-untitled-sections",
                severity="warning",
                details="Most sections were inferred from heading styles without numeric section ids.",
                evidence=[f"untitled={len(untitled)}", f"sections={len(non_preface)}"],
            )
        )

    oversized_blocks = [
        f"{section.section_id}:{len(block)}"
        for section in non_preface
        for block in section.content_blocks
        if len(block) > max_chars
    ]
    if oversized_blocks:
        issues.append(
            SourceQualityIssue(
                issue_id="source-quality-oversized-blocks",
                severity="warning",
                details="Some source blocks are larger than max_chars and require defensive splitting.",
                evidence=oversized_blocks[:10],
            )
        )

    numeric_sections = [
        section
        for section in non_preface
        if section.section_id[:1].isdigit()
    ]
    if not numeric_sections:
        issues.append(
            SourceQualityIssue(
                issue_id="source-quality-no-numeric-sections",
                severity="warning",
                details="No numeric section ids were detected; section filtering may be unreliable.",
                evidence=[section.section_id for section in non_preface[:10]],
            )
        )

    return issues
