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
OBLIGATION_REFERENCE = re.compile(r"\bOBL-[A-Za-z0-9._-]+\b")


def traceability_references(text: str) -> set[str]:
    return {
        item.strip().strip("`").strip()
        for item in re.split(r"[;,]", text)
        if item.strip().strip("`").strip()
    }


def missing_obligation_references(obligation: Any, traced_references: set[str]) -> tuple[str, ...]:
    required_references = tuple(
        dict.fromkeys((*obligation.source_refs, *obligation.dictionary_refs))
    )
    return tuple(
        reference for reference in required_references if reference not in traced_references
    )


def source_reference_finding(
    *, tc_id: str, obligation: Any, missing_references: tuple[str, ...]
) -> dict[str, Any]:
    return {
        "id": "missing-obligation-source-reference",
        "severity": "error",
        "tc_id": tc_id,
        "obligation_id": obligation.obligation_id,
        "atom_id": obligation.traceability_atom_id,
        "missing_references": list(missing_references),
        "message": (
            "TC traceability must preserve every source_refs and "
            "dictionary_refs value of its prepared obligation."
        ),
    }


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
            "validator": "prepared-package-obligation-gate-v3",
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
    obligations_by_id = {
        obligation.obligation_id: obligation for obligation in obligations.obligations
    }
    obligations_by_atom: dict[str, list[Any]] = {}
    for obligation in obligations.obligations:
        obligations_by_atom.setdefault(obligation.traceability_atom_id, []).append(obligation)
    testable = {
        obligation.obligation_id
        for obligation in obligations.obligations
        if obligation.coverage_status == "testable"
    }
    covered: set[str] = set()
    findings: list[dict[str, Any]] = []
    sections = test_case_sections(text)

    for tc_id, block in sections:
        trace_values = TRACEABILITY_FIELD.findall(without_fenced_blocks(block))
        trace_text = " ".join(trace_values)
        traced_references = traceability_references(trace_text)
        traced_atoms = set(ATOM_REFERENCE.findall(trace_text))
        traced_obligations = set(OBLIGATION_REFERENCE.findall(trace_text))
        for atom_id in sorted(traced_atoms):
            if atom_id not in obligations_by_atom:
                findings.append(
                    {
                        "id": "unknown-atomic-obligation",
                        "severity": "error",
                        "tc_id": tc_id,
                        "atom_id": atom_id,
                        "message": "TC references an ATOM that is absent from the prepared package.",
                    }
                )
        for obligation_id in sorted(traced_obligations):
            obligation = obligations_by_id.get(obligation_id)
            if obligation is None:
                findings.append(
                    {
                        "id": "unknown-prepared-obligation",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation_id,
                        "message": "TC references an OBL that is absent from the prepared package.",
                    }
                )
                continue
            atom_id = obligation.traceability_atom_id
            if atom_id not in traced_atoms:
                findings.append(
                    {
                        "id": "obligation-atom-pair-mismatch",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation_id,
                        "atom_id": atom_id,
                        "message": "TC must trace both the prepared obligation and its linked atom.",
                    }
                )
            elif obligation.coverage_status != "testable":
                findings.append(
                    {
                        "id": "non-testable-obligation-used-as-test",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation_id,
                        "atom_id": atom_id,
                        "coverage_status": obligation.coverage_status,
                        "message": "gap, unclear and not-applicable obligations cannot become executable TC coverage.",
                    }
                )
            else:
                missing_references = missing_obligation_references(
                    obligation, traced_references
                )
                if missing_references:
                    findings.append(
                        source_reference_finding(
                            tc_id=tc_id,
                            obligation=obligation,
                            missing_references=missing_references,
                        )
                    )
                covered.add(obligation_id)

        for atom_id in sorted(traced_atoms):
            linked = obligations_by_atom.get(atom_id, [])
            legacy = [item for item in linked if item.obligation_id == atom_id]
            if legacy:
                for obligation in legacy:
                    if obligation.coverage_status != "testable":
                        findings.append(
                            {
                                "id": "non-testable-obligation-used-as-test",
                                "severity": "error",
                                "tc_id": tc_id,
                                "obligation_id": obligation.obligation_id,
                                "atom_id": atom_id,
                                "coverage_status": obligation.coverage_status,
                                "message": "gap, unclear and not-applicable obligations cannot become executable TC coverage.",
                            }
                        )
                    else:
                        missing_references = missing_obligation_references(
                            obligation, traced_references
                        )
                        if missing_references:
                            findings.append(
                                source_reference_finding(
                                    tc_id=tc_id,
                                    obligation=obligation,
                                    missing_references=missing_references,
                                )
                            )
                        covered.add(obligation.obligation_id)
            elif linked and not any(
                item.obligation_id in traced_obligations for item in linked
            ):
                findings.append(
                    {
                        "id": "atom-without-prepared-obligation",
                        "severity": "error",
                        "tc_id": tc_id,
                        "atom_id": atom_id,
                        "message": "Current prepared-package TC traceability must name the linked OBL as well as the ATOM.",
                    }
                )

    for obligation_id in sorted(testable - covered):
        obligation = obligations_by_id[obligation_id]
        findings.append(
            {
                "id": "missing-testable-obligation-coverage",
                "severity": "error",
                "obligation_id": obligation_id,
                "atom_id": obligation.traceability_atom_id,
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
