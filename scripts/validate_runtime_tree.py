from __future__ import annotations

import json
from pathlib import Path


FORBIDDEN_PATHS = (
    "evals",
    "release",
    "test_case_agent",
    "references/agent",
    "references/qa",
    "skills/ft-test-case-iteration",
    "skills/ft-ui-automation-prep",
    "skills/agent-architecture-auditor",
)
REQUIRED_PATHS = (
    "AGENTS.md",
    "skills/ft-source-locator/SKILL.md",
    "skills/ft-scope-analyzer/SKILL.md",
    "skills/ft-test-case-writer/SKILL.md",
    "skills/ft-test-case-reviewer/SKILL.md",
    "references/runtime/test-data-fixtures.md",
    "references/runtime/test-design-profiles.md",
    "references/runtime/test-design-matrix.md",
    "references/runtime/test-case-runtime.md",
    "references/runtime/review-record.md",
    "scripts/create_ft_package.py",
    "scripts/capture_dadata_fixture.py",
    "scripts/validate_fixture_catalog.py",
    "scripts/validate_runtime_tc.py",
    "scripts/validate_runtime_matrix.py",
    "scripts/validate_runtime_scope.py",
    "scripts/runtime_traceability.py",
    "scripts/validate_runtime_review.py",
    "scripts/runtime_review_dispatch.py",
)

REQUIRED_REFERENCE_CONSUMERS = {
    "AGENTS.md": ("references/runtime/test-design-profiles.md", "references/runtime/review-record.md"),
    "skills/ft-test-case-writer/SKILL.md": (
        "references/runtime/test-design-profiles.md",
        "references/runtime/review-record.md",
    ),
    "skills/ft-test-case-reviewer/SKILL.md": (
        "references/runtime/test-data-fixtures.md",
        "references/runtime/test-design-profiles.md",
        "references/runtime/review-record.md",
    ),
}


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in FORBIDDEN_PATHS:
        if (root / relative_path).exists():
            errors.append(f"forbidden runtime artifact exists: {relative_path}")
    for relative_path in REQUIRED_PATHS:
        if not (root / relative_path).is_file():
            errors.append(f"missing runtime artifact: {relative_path}")
    for relative_path, required_references in REQUIRED_REFERENCE_CONSUMERS.items():
        path = root / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for reference in required_references:
            if reference not in content:
                errors.append(f"runtime consumer {relative_path} does not load {reference}")
    matrix_reference = root / "references/runtime/test-design-matrix.md"
    if matrix_reference.is_file() and "dadata" in matrix_reference.read_text(encoding="utf-8").casefold():
        errors.append("generic test-design matrix reference contains provider-specific DaData rule")
    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        agents_content = agents_path.read_text(encoding="utf-8")
        for marker in ("create_thread", "send_message_to_thread", "wait_threads", "runtime_review_dispatch.py"):
            if marker not in agents_content:
                errors.append(f"AGENTS.md does not enforce controller-owned review dispatch via {marker}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
