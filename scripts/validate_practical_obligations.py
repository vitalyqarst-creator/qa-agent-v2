"""Validate v0.9 source obligations before a workflow state or matrix exists.

This is intentionally a stdout-only structural check.  It must not be called a
scoped-route validation: the canonical scoped validator is available only after
``workflow-state.json`` and the matrix have been frozen.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    PracticalV09Error,
    relative_to_package,
    validate_scope_obligations,
    validate_source_package_manifest,
)


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check source obligations before matrix creation for practical v0.9."
    )
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--source-package-manifest", type=Path, required=True)
    parser.add_argument("--scope-obligations", type=Path, required=True)
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Exit non-zero if at least one finding is blocking.",
    )
    return parser.parse_args(argv)


def ensure_inside(package_root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error(f"{label} must be inside FT package root") from exc
    if not resolved.is_file():
        raise PracticalV09Error(f"{label} does not exist: {resolved}")
    return resolved


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    if not package_root.is_dir():
        raise PracticalV09Error(f"FT package root does not exist: {package_root}")
    manifest_path = ensure_inside(package_root, args.source_package_manifest, "source-package-manifest")
    obligations_path = ensure_inside(package_root, args.scope_obligations, "scope-obligations")
    source_findings, _ = validate_source_package_manifest(manifest_path, package_root)
    obligation_findings, payload = validate_scope_obligations(
        obligations_path,
        package_root,
        manifest_path,
    )
    findings = [*source_findings, *obligation_findings]
    blocking_count = sum(1 for item in findings if item.blocking)
    scope = payload.get("scope") if isinstance(payload, dict) else {}
    result = {
        "check_type": "scope-obligations-structure",
        "scope_id": scope.get("id") if isinstance(scope, dict) else None,
        "scope_slug": scope.get("slug") if isinstance(scope, dict) else None,
        "source_package_manifest": relative_to_package(package_root, manifest_path),
        "scope_obligations": relative_to_package(package_root, obligations_path),
        "findings_count": len(findings),
        "blocking_count": blocking_count,
        "clean": blocking_count == 0,
        "note": (
            "Это предварительная проверка структуры обязательств; "
            "каноническая scoped validation маршрута ещё не запускалась."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.require_clean and blocking_count else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
