from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.runtime_io import configure_utf8_stdio
except ModuleNotFoundError:  # Direct invocation
    from runtime_io import configure_utf8_stdio


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
REGISTRY_SCHEMA_VERSION = 4
SCOPE_HANDOFF_FILES = (
    "workflow-state.yaml",
    "scope-brief.md",
    "source-row-inventory.md",
    "coverage-gaps.md",
    "test-data-plan.md",
    "prompt.scope-to-writer.md",
)
ROLE_SKILL_PATHS = {
    "source-locator": "skills/ft-source-locator/SKILL.md",
    "scope-analyzer": "skills/ft-scope-analyzer/SKILL.md",
    "writer": "skills/ft-test-case-writer/SKILL.md",
    "matrix-reviewer": "skills/ft-test-case-reviewer/SKILL.md",
    "tc-reviewer": "skills/ft-test-case-reviewer/SKILL.md",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def registry_path(package_root: Path) -> Path:
    return package_root.resolve() / "work" / "runtime-session-registry.json"


def runtime_root(package_root: Path) -> Path | None:
    for candidate in (package_root.resolve(), *package_root.resolve().parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "scripts").is_dir():
            return candidate
    return None


def runtime_code_commit(package_root: Path) -> str:
    root = runtime_root(package_root)
    if root is None:
        return "unversioned"
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    commit = completed.stdout.strip().casefold()
    return commit if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", commit) else "unversioned"


def required_skill_contract(package_root: Path, role: str) -> dict[str, str]:
    relative_path = ROLE_SKILL_PATHS.get(role)
    if relative_path is None:
        raise ValueError(f"unsupported semantic role: {role}")
    root = runtime_root(package_root)
    if root is None:
        raise ValueError("runtime root with AGENTS.md and scripts was not found")
    path = root / relative_path
    if not path.is_file():
        raise ValueError(f"required role skill does not exist: {relative_path}")
    return {
        "path": relative_path,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def runtime_acknowledgement(package_root: Path) -> dict[str, str]:
    return {
        "code_commit": runtime_code_commit(package_root),
        "acknowledged_at": utc_now(),
    }


def package_input_baseline(package_root: Path) -> dict[str, str]:
    notes = package_root.resolve() / "AGENT-NOTES.md"
    if not notes.is_file():
        return {}
    return {"agent_notes_sha256": hashlib.sha256(notes.read_bytes()).hexdigest()}


def find_package_root(path: Path) -> Path | None:
    resolved = path.resolve()
    start = resolved if resolved.is_dir() else resolved.parent
    for candidate in (start, *start.parents):
        if (candidate / "AGENT-NOTES.md").is_file() and (candidate / "work").is_dir():
            return candidate
    return None


def canonical_scope(value: str) -> str:
    normalized = SCOPE_PREFIX_RE.sub("", value.strip())
    section = re.match(r"^(\d+(?:\.\d+)+)(?=$|[\s_-])", normalized)
    return section.group(1) if section else normalized


def session_record(
    thread_id: str,
    host_id: str,
    code_commit: str,
    model: str | None = None,
    thinking: str | None = None,
) -> dict[str, Any]:
    if not THREAD_ID_RE.fullmatch(thread_id):
        raise ValueError("session thread id must be a UUID returned by Codex create_thread")
    if not host_id.strip():
        raise ValueError("session host id must be returned by Codex create_thread")
    if bool(model) != bool(thinking):
        raise ValueError("explicit session profile requires both model and thinking")
    record: dict[str, Any] = {
        "session_type": "codex-thread",
        "session_id": thread_id,
        "host_id": host_id.strip(),
        "runtime_commit": code_commit,
        "recorded_at": utc_now(),
        "dispatch_profile": {"source": "default"},
    }
    if model and thinking:
        record["dispatch_profile"] = {
            "source": "explicit",
            "model": model.strip(),
            "thinking": thinking.strip(),
        }
    return record


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
    controller = session_record(controller_thread_id, controller_host_id, runtime_code_commit(package_root))
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
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "runtime": runtime_acknowledgement(package_root),
        "package_inputs": package_input_baseline(package_root),
        "controller": controller,
        "source_locator": None,
        "scopes": {},
    }
    return write_registry(package_root, payload)


def runtime_is_frozen(payload: dict[str, Any]) -> bool:
    """Return whether semantic work has started for this practical run."""

    if isinstance(payload.get("source_locator"), dict):
        return True
    scopes = payload.get("scopes")
    if not isinstance(scopes, dict):
        return False
    return any(
        isinstance(roles, dict) and any(isinstance(record, dict) for record in roles.values())
        for roles in scopes.values()
    )


def acknowledge_runtime(package_root: Path, controller_thread_id: str) -> Path:
    payload, errors = load_registry(package_root)
    if errors:
        raise ValueError(errors[0])
    assert payload is not None
    controller = payload.get("controller")
    if not isinstance(controller, dict) or controller.get("session_id") != controller_thread_id:
        raise ValueError("only the registered controller session may acknowledge a runtime update")
    runtime = payload.get("runtime")
    current_commit = runtime_code_commit(package_root)
    recorded_commit = runtime.get("code_commit") if isinstance(runtime, dict) else None
    if recorded_commit == current_commit and payload.get("schema_version") == REGISTRY_SCHEMA_VERSION:
        return registry_path(package_root)
    if runtime_is_frozen(payload):
        raise ValueError(
            "runtime is frozen after semantic work starts; create a new clean practical run "
            "for the updated agent-layer commit"
        )
    payload["schema_version"] = REGISTRY_SCHEMA_VERSION
    payload["runtime"] = runtime_acknowledgement(package_root)
    # Before the first semantic role starts, the same controller may reread an
    # updated contract. Keep its recorded runtime identity consistent with the
    # acknowledgement; downstream role records do not exist yet.
    controller["runtime_commit"] = current_commit
    controller["recorded_at"] = utc_now()
    return write_registry(package_root, payload)


def inherit_source_locator(package_root: Path, source_package_root: Path) -> Path:
    """Reuse an actual source-locator session record in a clean copy of the same FT package."""

    destination, destination_errors = load_registry(package_root)
    if destination_errors:
        raise ValueError(destination_errors[0])
    source, source_errors = load_registry(source_package_root)
    if source_errors:
        raise ValueError(source_errors[0])
    assert destination is not None and source is not None

    destination_contract_errors = validate_runtime_acknowledgement(package_root, destination)
    destination_contract_errors.extend(validate_record("controller", destination.get("controller")))
    if destination_contract_errors:
        raise ValueError(destination_contract_errors[0])

    source_record = source.get("source_locator")
    record_errors = validate_record(PACKAGE_ROLE, source_record)
    if record_errors:
        raise ValueError(record_errors[0])

    destination_inputs = package_input_baseline(package_root)
    source_inputs = package_input_baseline(source_package_root)
    if destination_inputs != source_inputs:
        raise ValueError(
            "source locator can be inherited only when AGENT-NOTES.md has the same SHA-256 in both packages"
        )
    if destination.get("package_inputs") != destination_inputs:
        raise ValueError("destination package input baseline is stale")
    if source.get("package_inputs") != source_inputs:
        raise ValueError("source package input baseline is stale")

    current = destination.get("source_locator")
    if isinstance(current, dict):
        if current == source_record:
            return registry_path(package_root)
        raise ValueError("destination package already has another source-locator session")

    source_session_id = source_record.get("session_id")
    for assigned_role, assigned in all_role_records(destination):
        if assigned.get("session_id") == source_session_id:
            raise ValueError(f"source-locator session is already assigned to {assigned_role}")

    # Preserve the original thread, host, runtime commit, timestamp and dispatch profile.
    destination["source_locator"] = dict(source_record)
    return write_registry(package_root, destination)


def scope_handoff(package_root: Path, scope: str) -> Path:
    scope_key = canonical_scope(scope)
    if not scope_key:
        raise ValueError("scope inheritance requires a non-empty scope")
    handoff_root = package_root.resolve() / "work" / "stage-handoffs"
    matches = [
        candidate
        for candidate in handoff_root.iterdir()
        if candidate.is_dir() and canonical_scope(candidate.name) == scope_key
    ] if handoff_root.is_dir() else []
    if len(matches) != 1:
        raise ValueError(f"expected exactly one scope handoff for {scope_key}, found {len(matches)}")
    return matches[0]


def normalized_text_sha256(path: Path) -> str:
    try:
        content = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"scope handoff file is not valid UTF-8: {path.name}") from exc
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def scope_input_hashes(package_root: Path, scope: str) -> dict[str, str]:
    handoff = scope_handoff(package_root, scope)
    inputs: dict[str, str] = {}
    for name in SCOPE_HANDOFF_FILES:
        path = handoff / name
        if not path.is_file():
            raise ValueError(f"scope handoff is incomplete: missing {name}")
        inputs[f"scope/{name}"] = normalized_text_sha256(path)
    clarifications = package_root.resolve() / "work" / "scope-clarification-requests.md"
    if not clarifications.is_file():
        raise ValueError("scope handoff is incomplete: missing work/scope-clarification-requests.md")
    inputs["work/scope-clarification-requests.md"] = normalized_text_sha256(clarifications)
    return inputs


def inherit_scope_analyzer(package_root: Path, source_package_root: Path, scope: str) -> Path:
    """Reuse the actual analyzer session only for a byte-identical completed scope handoff."""

    scope_key = canonical_scope(scope)
    if not scope_key:
        raise ValueError("scope inheritance requires a non-empty scope")
    destination, destination_errors = load_registry(package_root)
    if destination_errors:
        raise ValueError(destination_errors[0])
    source, source_errors = load_registry(source_package_root)
    if source_errors:
        raise ValueError(source_errors[0])
    assert destination is not None and source is not None

    destination_errors = validate_runtime_acknowledgement(package_root, destination)
    destination_errors.extend(validate_record("controller", destination.get("controller")))
    destination_errors.extend(validate_record(PACKAGE_ROLE, destination.get("source_locator")))
    if destination_errors:
        raise ValueError(destination_errors[0])

    source_locator = source.get("source_locator")
    source_locator_errors = validate_record(PACKAGE_ROLE, source_locator)
    if source_locator_errors:
        raise ValueError(source_locator_errors[0])
    if destination.get("source_locator") != source_locator:
        raise ValueError("scope analyzer can be inherited only after inheriting the same source-locator record")

    destination_inputs = package_input_baseline(package_root)
    source_inputs = package_input_baseline(source_package_root)
    if destination_inputs != source_inputs:
        raise ValueError(
            "scope analyzer can be inherited only when AGENT-NOTES.md has the same SHA-256 in both packages"
        )
    if destination.get("package_inputs") != destination_inputs:
        raise ValueError("destination package input baseline is stale")
    if source.get("package_inputs") != source_inputs:
        raise ValueError("source package input baseline is stale")

    destination_hashes = scope_input_hashes(package_root, scope_key)
    source_hashes = scope_input_hashes(source_package_root, scope_key)
    if destination_hashes != source_hashes:
        raise ValueError("scope analyzer can be inherited only for identical normalized scope handoff inputs")

    source_scopes = source.get("scopes")
    if not isinstance(source_scopes, dict):
        raise ValueError("source session registry scopes must be a JSON object")
    source_matches = [
        value
        for key, value in source_scopes.items()
        if canonical_scope(str(key)) == scope_key and isinstance(value, dict)
    ]
    if len(source_matches) != 1:
        raise ValueError(f"source registry must contain exactly one assignment for scope {scope_key}")
    source_record = source_matches[0].get("scope_analyzer")
    record_errors = validate_record(f"{scope_key}:scope-analyzer", source_record)
    if record_errors:
        raise ValueError(record_errors[0])

    destination_scopes = destination.setdefault("scopes", {})
    if not isinstance(destination_scopes, dict):
        raise ValueError("destination session registry scopes must be a JSON object")
    destination_matches = [
        (key, value)
        for key, value in destination_scopes.items()
        if canonical_scope(str(key)) == scope_key and isinstance(value, dict)
    ]
    if len(destination_matches) > 1:
        raise ValueError(f"multiple destination assignments resolve to canonical scope {scope_key}")
    if destination_matches:
        existing_key, target = destination_matches[0]
        if existing_key != scope_key:
            destination_scopes[scope_key] = destination_scopes.pop(existing_key)
    else:
        target = {}
        destination_scopes[scope_key] = target
    current = target.get("scope_analyzer")
    if isinstance(current, dict):
        if current == source_record:
            return registry_path(package_root)
        raise ValueError("destination scope already has another scope-analyzer session")

    source_session_id = source_record.get("session_id")
    for assigned_role, assigned in all_role_records(destination):
        if assigned.get("session_id") == source_session_id:
            raise ValueError(f"scope-analyzer session is already assigned to {assigned_role}")

    # Preserve the actual historical analyzer identity; only its immutable output is reused.
    target["scope_analyzer"] = dict(source_record)
    return write_registry(package_root, destination)


def validate_runtime_acknowledgement(package_root: Path, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        action = (
            "start a new clean practical run"
            if runtime_is_frozen(payload)
            else "reread the runtime contract and run acknowledge-runtime before semantic work"
        )
        errors.append(f"session registry runtime contract is stale; controller must {action}")
        return errors
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        return ["session registry has no acknowledged runtime contract"]
    recorded_commit = runtime.get("code_commit")
    current_commit = runtime_code_commit(package_root)
    if recorded_commit != current_commit:
        action = (
            "start a new clean practical run; an active run cannot change agent-layer commit"
            if runtime_is_frozen(payload)
            else "reread the runtime contract and run acknowledge-runtime before semantic work"
        )
        errors.append(
            f"runtime code commit changed from {recorded_commit!r} to {current_commit!r}; "
            f"controller must {action}"
        )
    package_inputs = payload.get("package_inputs")
    if isinstance(package_inputs, dict) and package_inputs.get("agent_notes_sha256"):
        current_inputs = package_input_baseline(package_root)
        if current_inputs.get("agent_notes_sha256") != package_inputs.get("agent_notes_sha256"):
            errors.append(
                "AGENT-NOTES.md changed after route initialization; it is an immutable package input, "
                "so start a new route instead of mutating it during source registration"
            )
    return errors


def validate_controller(package_root: Path, expected_thread_id: str) -> list[str]:
    payload, load_errors = load_registry(package_root)
    if load_errors:
        return load_errors
    assert payload is not None
    errors = validate_record("controller", payload.get("controller"))
    controller = payload.get("controller")
    if isinstance(controller, dict) and controller.get("session_id") != expected_thread_id:
        errors.append("current thread is not the registered controller")
    errors.extend(validate_runtime_acknowledgement(package_root, payload))
    return errors


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
    model: str | None = None,
    thinking: str | None = None,
) -> Path:
    payload, errors = load_registry(package_root)
    if errors:
        raise ValueError(errors[0])
    assert payload is not None
    runtime_errors = validate_runtime_acknowledgement(package_root, payload)
    if runtime_errors:
        raise ValueError(runtime_errors[0])
    current_commit = runtime_code_commit(package_root)
    record = session_record(thread_id, host_id, current_commit, model, thinking)
    migrated_scope_key = False

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
        legacy_keys = [key for key in scopes if canonical_scope(str(key)) == scope_key and key != scope_key]
        if len(legacy_keys) > 1 or (legacy_keys and scope_key in scopes):
            raise ValueError(f"multiple session assignments resolve to canonical scope {scope_key}")
        if legacy_keys:
            scopes[scope_key] = scopes.pop(legacy_keys[0])
            migrated_scope_key = True
        target = scopes.setdefault(scope_key, {})
        if not isinstance(target, dict):
            raise ValueError(f"session registry scope {scope_key} must be a JSON object")
        current = target.get(role.replace("-", "_"))
        key = role.replace("-", "_")
    else:
        raise ValueError(f"unsupported runtime role: {role}")

    if isinstance(current, dict):
        same_session = current.get("session_id") == thread_id and current.get("host_id") == host_id.strip()
        if current.get("runtime_commit") != current_commit:
            if same_session:
                raise ValueError(
                    f"{role} session was created for another runtime commit; create a fresh top-level session"
                )
        elif not same_session:
            raise ValueError(f"{role} is already assigned to another session; reuse the original session")
        elif current.get("dispatch_profile") != record.get("dispatch_profile"):
            raise ValueError(f"{role} session is already registered with another dispatch profile")
        else:
            return write_registry(package_root, payload) if migrated_scope_key else registry_path(package_root)

    for assigned_role, assigned in all_role_records(payload):
        if assigned.get("session_id") == thread_id:
            raise ValueError(f"session {thread_id} is already assigned to {assigned_role}")

    target[key] = record
    return write_registry(package_root, payload)


def validate_role_runtime(package_root: Path, label: str, record: Any) -> list[str]:
    if not isinstance(record, dict):
        return []
    recorded_commit = record.get("runtime_commit")
    current_commit = runtime_code_commit(package_root)
    if recorded_commit != current_commit:
        return [
            f"{label} session belongs to runtime commit {recorded_commit!r}, current commit is {current_commit!r}; "
            "controller must create and register a fresh top-level session for this role"
        ]
    return []


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
    profile = record.get("dispatch_profile")
    if not isinstance(profile, dict):
        errors.append(f"{label} dispatch_profile is required")
    else:
        source = profile.get("source")
        if source not in {"default", "explicit"}:
            errors.append(f"{label} dispatch_profile source must be default or explicit")
        if source == "explicit":
            if not isinstance(profile.get("model"), str) or not profile["model"].strip():
                errors.append(f"{label} explicit dispatch_profile requires model")
            if not isinstance(profile.get("thinking"), str) or not profile["thinking"].strip():
                errors.append(f"{label} explicit dispatch_profile requires thinking")
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
    errors.extend(validate_runtime_acknowledgement(package_root, payload))
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
            matches = [
                value
                for key, value in scopes.items()
                if canonical_scope(str(key)) == scope_key and isinstance(value, dict)
            ]
            if len(matches) > 1:
                errors.append(f"multiple session assignments resolve to canonical scope {scope_key}")
            candidate = matches[0] if len(matches) == 1 else None
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
            elif isinstance(expected_record, dict):
                errors.extend(validate_role_runtime(package_root, expected_role, expected_record))
    return errors


def main() -> int:
    configure_utf8_stdio()
    sys.stdout.reconfigure(encoding="utf-8")
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
    record_parser.add_argument("--model")
    record_parser.add_argument("--thinking")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--package-root", type=Path, required=True)
    verify_parser.add_argument("--through", choices=tuple(STAGE_REQUIREMENTS), required=True)
    verify_parser.add_argument("--scope")
    verify_parser.add_argument("--expected-role", choices=(PACKAGE_ROLE, *SCOPE_ROLES))
    verify_parser.add_argument("--expected-thread-id")

    controller_parser = subparsers.add_parser("controller-check")
    controller_parser.add_argument("--package-root", type=Path, required=True)
    controller_parser.add_argument("--expected-thread-id", required=True)

    acknowledge_parser = subparsers.add_parser("acknowledge-runtime")
    acknowledge_parser.add_argument("--package-root", type=Path, required=True)
    acknowledge_parser.add_argument("--controller-thread-id", required=True)

    inherit_parser = subparsers.add_parser("inherit-source")
    inherit_parser.add_argument("--package-root", type=Path, required=True)
    inherit_parser.add_argument("--from-package-root", type=Path, required=True)

    inherit_scope_parser = subparsers.add_parser("inherit-scope")
    inherit_scope_parser.add_argument("--package-root", type=Path, required=True)
    inherit_scope_parser.add_argument("--from-package-root", type=Path, required=True)
    inherit_scope_parser.add_argument("--scope", required=True)

    args = parser.parse_args()
    try:
        if args.command == "init":
            path = initialize_registry(args.package_root, args.controller_thread_id, args.controller_host_id)
            print(json.dumps({"created": True, "path": str(path)}, ensure_ascii=False))
            return 0
        if args.command == "record":
            path = record_role(
                args.package_root,
                args.role,
                args.thread_id,
                args.host_id,
                args.scope,
                args.model,
                args.thinking,
            )
            print(json.dumps({"recorded": True, "path": str(path)}, ensure_ascii=False))
            return 0
        if args.command == "acknowledge-runtime":
            path = acknowledge_runtime(args.package_root, args.controller_thread_id)
            print(json.dumps({"acknowledged": True, "path": str(path)}, ensure_ascii=False))
            return 0
        if args.command == "inherit-source":
            path = inherit_source_locator(args.package_root, args.from_package_root)
            print(json.dumps({"inherited": True, "path": str(path)}, ensure_ascii=False))
            return 0
        if args.command == "inherit-scope":
            path = inherit_scope_analyzer(args.package_root, args.from_package_root, args.scope)
            print(json.dumps({"inherited": True, "path": str(path)}, ensure_ascii=False))
            return 0
        if args.command == "controller-check":
            errors = validate_controller(args.package_root, args.expected_thread_id)
            print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
            return 0 if not errors else 1
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
    result: dict[str, Any] = {"valid": not errors, "errors": errors}
    if not errors and args.expected_role:
        result["required_skill"] = required_skill_contract(args.package_root, args.expected_role)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
