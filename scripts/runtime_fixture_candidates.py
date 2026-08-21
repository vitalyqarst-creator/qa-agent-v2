from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.runtime_io import configure_utf8_stdio
    from scripts.runtime_state import scalar_values
except ModuleNotFoundError:  # Direct invocation
    from runtime_io import configure_utf8_stdio
    from runtime_state import scalar_values


def _load_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def accepted_materialization(package_root: Path, scope: str) -> tuple[Path, dict[str, Any]] | None:
    state_path = package_root / "work" / "practical" / scope / "workflow-state.yaml"
    materialization_path = package_root / "work" / "test-data" / scope / "data-materialization.json"
    if not state_path.is_file() or not materialization_path.is_file():
        return None
    state = scalar_values(state_path.read_text(encoding="utf-8"))
    if state.get("matrix_status") != "accepted" or state.get("data_status") != "completed":
        return None
    payload = _load_object(materialization_path)
    if payload is None or payload.get("scope") != scope:
        return None
    return materialization_path, payload


def fixture_candidates(package_root: Path, current_scope: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    test_data_root = package_root / "work" / "test-data"
    if not test_data_root.is_dir():
        return candidates
    for scope_dir in sorted(test_data_root.iterdir(), key=lambda item: item.name.casefold()):
        if not scope_dir.is_dir() or scope_dir.name == current_scope:
            continue
        accepted = accepted_materialization(package_root, scope_dir.name)
        if accepted is None:
            continue
        materialization_path, payload = accepted
        roles = payload.get("bindings", payload.get("data_roles"))
        if not isinstance(roles, list):
            continue
        for role in roles:
            if not isinstance(role, dict):
                continue
            values = role.get("values")
            if not isinstance(values, dict) or not values:
                continue
            candidates.append(
                {
                    "source_scope": scope_dir.name,
                    "role_id": role.get("role_id"),
                    "source_type": role.get("source_type"),
                    "source_name": role.get("source_name"),
                    "fixture_id": role.get("fixture_id"),
                    "values": values,
                    "materialization_path": materialization_path.relative_to(package_root).as_posix(),
                }
            )
    return candidates


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="List reusable tester-facing values from accepted sibling scope materializations."
    )
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--scope", required=True, help="Current scope to exclude from candidates.")
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    print(
        json.dumps(
            {
                "package_root": str(package_root),
                "current_scope": args.scope,
                "candidates": fixture_candidates(package_root, args.scope),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
