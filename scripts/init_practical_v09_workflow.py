"""Initialize the only mutable state file of a compact v0.9 scope."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    ROUTE_VERSION,
    SOURCE_MANIFEST_RELATIVE_PATH,
    PracticalV09Error,
    package_relative_path,
    relative_to_package,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create workflow-state.json for practical v0.9.")
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--scope-slug", required=True)
    parser.add_argument("--source-package-manifest", type=Path, required=True)
    parser.add_argument("--scope-obligations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    output = args.output.resolve()
    if output.exists():
        raise PracticalV09Error(f"Refusing to overwrite workflow state: {output}")
    source_path = args.source_package_manifest.resolve()
    obligations_path = args.scope_obligations.resolve()
    for label, path in (("source-package-manifest", source_path), ("scope-obligations", obligations_path)):
        try:
            path.relative_to(package_root)
        except ValueError as exc:
            raise PracticalV09Error(f"{label} must be inside FT package root") from exc
        if not path.is_file():
            raise PracticalV09Error(f"{label} does not exist: {path}")
    if relative_to_package(package_root, source_path) != SOURCE_MANIFEST_RELATIVE_PATH:
        raise PracticalV09Error(
            "source-package-manifest must use the shared package-level path "
            f"{SOURCE_MANIFEST_RELATIVE_PATH}"
        )
    payload = {
        "route_version": ROUTE_VERSION,
        "scope_id": args.scope_id,
        "scope_slug": args.scope_slug,
        "phase": "scope",
        "next_action": "Создать матрицу тест-дизайна",
        "matrix_review_required": None,
        "contract_versions": {
            "route": ROUTE_VERSION,
            "source_package": "source-package-v1",
        },
        "artifacts": {
            "source_package_manifest": relative_to_package(package_root, source_path),
            "scope_obligations": relative_to_package(package_root, obligations_path),
            "test_design_matrix": "not-created",
            "canonical_test_cases": "not-created",
            "validator_report": "not-created",
        },
        "reviews": [],
        "decision_notes": [],
    }
    write_json(output, payload)
    print(relative_to_package(package_root, output))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
