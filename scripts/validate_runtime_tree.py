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
    "references/runtime/test-design-matrix.md",
    "references/runtime/test-case-runtime.md",
    "scripts/create_ft_package.py",
    "scripts/capture_dadata_fixture.py",
    "scripts/validate_fixture_catalog.py",
    "scripts/validate_runtime_tc.py",
)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in FORBIDDEN_PATHS:
        if (root / relative_path).exists():
            errors.append(f"forbidden runtime artifact exists: {relative_path}")
    for relative_path in REQUIRED_PATHS:
        if not (root / relative_path).is_file():
            errors.append(f"missing runtime artifact: {relative_path}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
