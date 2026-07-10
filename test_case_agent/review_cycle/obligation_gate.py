from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from test_case_agent.review_cycle.prepared_package import load_obligations


TC_HEADING = re.compile(r"(?m)^#{2,6}\s+(TC-[A-Za-z0-9._-]+)\b")
TRACEABILITY_FIELD = re.compile(
    r"(?im)^\*\*(?:Трассировка|Traceability):\*\*\s*(.+)$"
)
ATOM_REFERENCE = re.compile(r"\bATOM-[A-Za-z0-9._-]+\b")


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
            "validator": "prepared-package-obligation-gate-v1",
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
    headings = list(TC_HEADING.finditer(text))

    for index, heading in enumerate(headings):
        tc_id = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[heading.start() : end]
        trace_values = TRACEABILITY_FIELD.findall(block)
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
        test_case_count=len(headings),
        testable_obligations=len(testable),
        covered_obligations=tuple(sorted(covered)),
        findings=tuple(findings),
        checked_paths=(str(draft_path), str(obligations_path)),
    )
