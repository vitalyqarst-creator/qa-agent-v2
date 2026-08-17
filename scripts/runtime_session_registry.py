from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


THREAD_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
SCOPE_PREFIX_RE = re.compile(r"^\d{2}-(?=(?:\d+(?:\.\d+)+[-_]|scope\b))", re.IGNORECASE)
PACKAGE_ROLE = "source-locator"
SCOPE_ROLES = ("scope-analyzer", "writer", "matrix-reviewer", "tc-reviewer")
STAGE_REQUIREMENTS = {
    "source-locator": (),
    "scope-analyzer": ("scope-analyzer",),
    "writer": ("scope-analyzer", "writer"),
    "matrix-reviewer": ("scope-analyzer", "writer", "matrix-reviewer"),
    "tc-reviewer": ("scope-analyzer", "writer", "matrix-reviewer", "tc-reviewer"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def registry_path(package_root: Path) -> Path:
    return package_root.resolve() / "work" / "runtime-session-registry.json"


def find_package_root(path: Path) -> Path | None:
    resolved = path.resolve()
    start = resolved if resolved.is_dir() else resolved.parent
    for candidate in (start, *start.parents):
        if (candidate / "AGENT-NOTES.md").is_file() and (candidate / "work").is_dir():
            return candidate
    return None


def canonical_scope(value: str) -> str:
    return SCOPE_PREFIX_RE.sub("", value.strip())


def session_record(thread_id: str, host_id: str) -> dict[str, str]:
    if not THREAD_ID_RE.fullmatch(thread_id):
        raise ValueError("session thread id must be a UUID returned by Codex create_thread")
    if not host_id.strip():
        raise ValueError("session host id must be returned by Codex create_thread")
    return {
        "session_type": "codex-thread",
        "session_id": thread_id,
        "host_id": host_id.strip(),
        "recorded_at": utc_now(),
    }


def load_registry(package_root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = registry_path(package_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"session-registry-read-error: {exc}"]
    if not isinstance(payload, dict):
        return None, ["session registry must be a JSON object"]
    return payload, []


def write_registry(package_root: Path, payload: dict[str, Any]) -> Path:
    path = registry_path(package_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def initialize_registry(package_root: Path, controller_thread_id: str, controller_host_id: str) -> Path:
    path = registry_path(package_root)
    controller = session_record(controller_thread_id, controller_host_id)
    if path.exists():
        payload, errors = load_registry(package_root)
        if errors:
            raise ValueError(errors[0])
        assert payload is not None
        existing = payload.get("controller")
        if not isinstance(existing, dict) or existing.get("session_id") != controller_thread_id:
            raise ValueError("FT package already belongs to another controller session")
        return path
    payload: dict[str, Any] = {
        "schema_version": 1,
        "controller": controller,
        "source_locator": None,
        "scopes": {},
    }
    return write_registry(package_root, payload)


def all_role_records(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    records: list[tuple[str, dict[str, Any]]] = []
    controller = payload.get("controller")
    if isinstance(controller, dict):
        records.append(("controller", controller))
    locator = payload.get("source_locator")
    if isinstance(locator, dict):
        records.append((PACKAGE_ROLE, locator))
    scopes = payload.get("scopes")
    if isinstance(scopes, dict):
        for scope, roles in scopes.items():
            if not isinstance(roles, dict):
                continue
            for role, record in roles.items():
                if isinstance(record, dict):
                    records.append((f"{scope}:{role}", record))
    return records


def record_role(
    package_root: Path,
    role: str,
    thread_id: str,
    host_id: str,
    scope: str | None = None,
) -> Path:
    payload, errors = load_registry(package_root)
    if errors:
        raise ValueError(errors[0])
    assert payload is not None
    record = session_record(thread_id, host_id)

    if role == PACKAGE_ROLE:
        if scope is not None:
            raise ValueError("source-locator is package-level and must not have a scope")
        current = payload.get("source_locator")
        target = payload
        key = "source_locator"
    elif role in SCOPE_ROLES:
        if not scope or not canonical_scope(scope):
            raise ValueError(f"{role} requires a non-empty scope")
        scope_key = canonical_scope(scope)
        scopes = payload.setdefault("scopes", {})
        if not isinstance(scopes, dict):
            raise ValueError("session registry scopes must be a JSON object")
        target = scopes.setdefault(scope_key, {})
        if not isinstance(target, dict):
            raise ValueError(f"session registry scope {scope_key} must be a JSON object")
        current = target.get(role.replace("-", "_"))
        key = role.replace("-", "_")
    else:
        raise ValueError(f"unsupported runtime role: {role}")

    if isinstance(current, dict):
        if current.get("session_id") != thread_id or current.get("host_id") != host_id.strip():
            raise ValueError(f"{role} is already assigned to another session; reuse the original session")
        return registry_path(package_root)

    for assigned_role, assigned in all_role_records(payload):
        if assigned.get("session_id") == thread_id:
            raise ValueError(f"session {thread_id} is already assigned to {assigned_role}")

    target[key] = record
    return write_registry(package_root, payload)


def validate_record(label: str, record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"missing session assignment for {label}"]
    if record.get("session_type") != "codex-thread":
        errors.append(f"{label} session_type must be codex-thread")
    session_id = record.get("session_id")
    if not isinstance(session_id, str) or not THREAD_ID_RE.fullmatch(session_id):
        errors.append(f"{label} session_id must be a top-level Codex thread UUID")
    host_id = record.get("host_id")
    if not isinstance(host_id, str) or not host_id.strip():
        errors.append(f"{label} host_id is required")
    return errors


def validate_topology(
    package_root: Path,
    through: str,
    scope: str | None = None,
    expected_role: str | None = None,
    expected_thread_id: str | None = None,
) -> list[str]:
    if through not in STAGE_REQUIREMENTS:
        return [f"unsupported session topology stage: {through}"]
    payload, load_errors = load_registry(package_root)
    if load_errors:
        return load_errors
    assert payload is not None
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("session registry schema_version must be 1")
    errors.extend(validate_record("controller", payload.get("controller")))
    errors.extend(validate_record(PACKAGE_ROLE, payload.get("source_locator")))

    scope_key = canonical_scope(scope or "")
    required_scope_roles = STAGE_REQUIREMENTS[through]
    scope_roles: dict[str, Any] = {}
    if required_scope_roles:
        if not scope_key:
            errors.append(f"stage {through} requires a scope")
        scopes = payload.get("scopes")
        if not isinstance(scopes, dict):
            errors.append("session registry scopes must be a JSON object")
        elif scope_key:
            candidate = scopes.get(scope_key)
            if not isinstance(candidate, dict):
                errors.append(f"missing session assignments for scope {scope_key}")
            else:
                scope_roles = candidate
        for role in required_scope_roles:
            errors.extend(validate_record(f"{scope_key}:{role}", scope_roles.get(role.replace("-", "_"))))

    seen: dict[str, str] = {}
    for label, record in all_role_records(payload):
        session_id = record.get("session_id")
        if not isinstance(session_id, str):
            continue
        if session_id in seen:
            errors.append(f"session {session_id} is reused by {seen[session_id]} and {label}")
        else:
            seen[session_id] = label

    if expected_role is not None or expected_thread_id is not None:
        if not expected_role or not expected_thread_id:
            errors.append("expected role and thread id must be provided together")
        else:
            if expected_role == PACKAGE_ROLE:
                expected_record = payload.get("source_locator")
            elif expected_role in SCOPE_ROLES and scope_key:
                expected_record = scope_roles.get(expected_role.replace("-", "_"))
            else:
                expected_record = None
                errors.append(f"unsupported expected role: {expected_role}")
            if isinstance(expected_record, dict) and expected_record.get("session_id") != expected_thread_id:
                errors.append(f"current thread is not registered as {expected_role}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Register and verify the practical runtime session topology.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--package-root", type=Path, required=True)
    init_parser.add_argument("--controller-thread-id", required=True)
    init_parser.add_argument("--controller-host-id", required=True)

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--package-root", type=Path, required=True)
    record_parser.add_argument("--role", choices=(PACKAGE_ROLE, *SCOPE_ROLES), required=True)
    record_parser.add_argument("--scope")
    record_parser.add_argument("--thread-id", required=True)
    record_parser.add_argument("--host-id", required=True)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--package-root", type=Path, required=True)
    verify_parser.add_argument("--through", choices=tuple(STAGE_REQUIREMENTS), required=True)
    verify_parser.add_argument("--scope")
    verify_parser.add_argument("--expected-role", choices=(PACKAGE_ROLE, *SCOPE_ROLES))
    verify_parser.add_argument("--expected-thread-id")

    args = parser.parse_args()
    try:
        if args.command == "init":
            path = initialize_registry(args.package_root, args.controller_thread_id, args.controller_host_id)
            print(json.dumps({"created": True, "path": str(path)}, ensure_ascii=False))
            return 0
        if args.command == "record":
            path = record_role(args.package_root, args.role, args.thread_id, args.host_id, args.scope)
            print(json.dumps({"recorded": True, "path": str(path)}, ensure_ascii=False))
            return 0
        errors = validate_topology(
            args.package_root,
            args.through,
            args.scope,
            args.expected_role,
            args.expected_thread_id,
        )
    except ValueError as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 1
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
