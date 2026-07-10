from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from test_case_agent.review_cycle.prepared_package import load_obligations


HEADING_LINE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
TC_TITLE = re.compile(r"^(TC-[A-Za-z0-9._-]+)\b")
FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
TRACEABILITY_FIELD = re.compile(
    r"(?im)^[ \t]*(?:[-+*][ \t]+)?\*\*(?:Трассировка|Traceability):\*\*[ \t]*(.+)$"
)
ATOM_REFERENCE = re.compile(r"\bATOM-[A-Za-z0-9._-]+\b")


@dataclass(frozen=True)
class MarkdownHeading:
    offset: int
    level: int
    title: str
    tc_id: str = ""


def markdown_headings(text: str) -> tuple[MarkdownHeading, ...]:
    headings: list[MarkdownHeading] = []
    offset = 0
    fence_char = ""
    fence_length = 0
    for line_with_end in text.splitlines(keepends=True):
        line = line_with_end.rstrip("\r\n")
        fence = FENCE_LINE.match(line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                fence_char = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = ""
                fence_length = 0
            offset += len(line_with_end)
            continue
        if not fence_char:
            match = HEADING_LINE.match(line)
            if match:
                title = match.group(2).strip()
                tc_match = TC_TITLE.match(title)
                headings.append(
                    MarkdownHeading(
                        offset=offset,
                        level=len(match.group(1)),
                        title=title,
                        tc_id=tc_match.group(1) if tc_match else "",
                    )
                )
        offset += len(line_with_end)
    return tuple(headings)


def test_case_sections(text: str) -> tuple[tuple[str, str], ...]:
    headings = markdown_headings(text)
    sections: list[tuple[str, str]] = []
    for index, heading in enumerate(headings):
        if not heading.tc_id:
            continue
        end = len(text)
        for following in headings[index + 1 :]:
            if following.tc_id or following.level <= heading.level:
                end = following.offset
                break
        sections.append((heading.tc_id, text[heading.offset:end]))
    return tuple(sections)


def without_fenced_blocks(text: str) -> str:
    lines: list[str] = []
    fence_char = ""
    fence_length = 0
    for line_with_end in text.splitlines(keepends=True):
        line = line_with_end.rstrip("\r\n")
        fence = FENCE_LINE.match(line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                fence_char = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = ""
                fence_length = 0
            continue
        if not fence_char:
            lines.append(line_with_end)
    return "".join(lines)


@dataclass(frozen=True)
class ObligationGateResult:
    passed: bool
    package_id: str
    test_case_count: int
    testable_obligations: int
    covered_obligations: tuple[str, ...]
    findings: tuple[dict[str, Any], ...]
    checked_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "validator": "prepared-package-obligation-gate-v2",
            "package_id": self.package_id,
            "test_case_count": self.test_case_count,
            "testable_obligations": self.testable_obligations,
            "covered_obligations": list(self.covered_obligations),
            "checked_paths": list(self.checked_paths),
            "findings": list(self.findings),
        }


def validate_draft_obligation_coverage(
    *,
    draft_path: Path,
    obligations_path: Path,
) -> ObligationGateResult:
    text = draft_path.read_text(encoding="utf-8")
    obligations = load_obligations(obligations_path)
    status_by_atom = {
        obligation.obligation_id: obligation.coverage_status
        for obligation in obligations.obligations
    }
    testable = {
        atom_id for atom_id, status in status_by_atom.items() if status == "testable"
    }
    covered: set[str] = set()
    findings: list[dict[str, Any]] = []
    sections = test_case_sections(text)

    for tc_id, block in sections:
        trace_values = TRACEABILITY_FIELD.findall(without_fenced_blocks(block))
        traced_atoms = set(ATOM_REFERENCE.findall(" ".join(trace_values)))
        for atom_id in sorted(traced_atoms):
            status = status_by_atom.get(atom_id)
            if status is None:
                findings.append(
                    {
                        "id": "unknown-atomic-obligation",
                        "severity": "error",
                        "tc_id": tc_id,
                        "atom_id": atom_id,
                        "message": "TC references an ATOM that is absent from the prepared package.",
                    }
                )
            elif status != "testable":
                findings.append(
                    {
                        "id": "non-testable-obligation-used-as-test",
                        "severity": "error",
                        "tc_id": tc_id,
                        "atom_id": atom_id,
                        "coverage_status": status,
                        "message": "gap, unclear and not-applicable obligations cannot become executable TC coverage.",
                    }
                )
            else:
                covered.add(atom_id)

    for atom_id in sorted(testable - covered):
        findings.append(
            {
                "id": "missing-testable-obligation-coverage",
                "severity": "error",
                "atom_id": atom_id,
                "message": "A testable prepared obligation has no TC traceability reference.",
            }
        )

    return ObligationGateResult(
        passed=not findings,
        package_id=obligations.package_id,
        test_case_count=len(sections),
        testable_obligations=len(testable),
        covered_obligations=tuple(sorted(covered)),
        findings=tuple(findings),
        checked_paths=(str(draft_path), str(obligations_path)),
    )
