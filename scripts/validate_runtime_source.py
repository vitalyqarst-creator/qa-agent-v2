from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from scripts.runtime_io import configure_utf8_stdio
    from scripts.runtime_session_registry import load_registry, validate_topology
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_source.py
    from runtime_io import configure_utf8_stdio
    from runtime_session_registry import load_registry, validate_topology


DIGEST_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
FIGMA_URL_RE = re.compile(r"https://www\.figma\.com/[^\s`\"'<>]+")
URL_TRAILING_PUNCTUATION = ".,;:!?)]}"
LEGACY_PRIMARY_ROLES = {
    "semantic_primary",
    "machine_readable_primary",
    "visual_structural_crosscheck_only",
}
SEMANTIC_ROLE = "semantic_primary"
MACHINE_ROLE = "machine_readable_primary"
VISUAL_ROLE = "visual_structural_crosscheck_only"
LOCAL_SECTIONS = ("primary_sources", "support_sources", "visual_sources")
REQUIRED_HANDOFF_FILES = ("source-selection.md", "workflow-state.yaml")
NOTES_ROLE_PATTERNS = {
    SEMANTIC_ROLE: re.compile(
        r"(?im)^\s*[-*]?\s*(?:Основное|Каноническое)\s+ФТ[^`\n]*`([^`]+)`"
    ),
    MACHINE_ROLE: re.compile(
        r"(?im)^\s*[-*]?\s*Машиночитаем(?:ая|ое)\s+(?:версия|представление)[^`\n]*`([^`]+)`"
    ),
}


def scalar(value: str) -> str:
    result = value.strip()
    if len(result) >= 2 and result[0] == result[-1] and result[0] in {'"', "'"}:
        return result[1:-1]
    return result


def parse_top_level(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in content.splitlines():
        match = re.fullmatch(r"([A-Za-z0-9_]+):\s*(.*)", line)
        if match:
            values[match.group(1)] = scalar(match.group(2))
    return values


def parse_list(content: str, section: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    active = False
    current: dict[str, str] | None = None
    for line in content.splitlines():
        if re.fullmatch(rf"{re.escape(section)}:\s*", line):
            active = True
            current = None
            continue
        if active and line and not line.startswith(" "):
            break
        if not active:
            continue
        item = re.fullmatch(r"\s{2}-\s+([A-Za-z0-9_]+):\s*(.*)", line)
        if item:
            current = {item.group(1): scalar(item.group(2))}
            entries.append(current)
            continue
        field = re.fullmatch(r"\s{4}([A-Za-z0-9_]+):\s*(.*)", line)
        if field and current is not None:
            current[field.group(1)] = scalar(field.group(2))
    return entries


def repository_root(package_root: Path) -> Path | None:
    for candidate in (package_root.resolve(), *package_root.resolve().parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def resolve_registered_path(repo_root: Path, package_root: Path, value: str) -> tuple[Path | None, str | None]:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None, "registered path must be repository-relative without '..'"
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(package_root.resolve())
    except ValueError:
        return None, "registered path must stay inside the FT package"
    return resolved, None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def agent_notes_role_hints(package_root: Path, repo_root: Path) -> dict[str, str]:
    notes_path = package_root / "AGENT-NOTES.md"
    if not notes_path.is_file():
        return {}
    notes = notes_path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for role, pattern in NOTES_ROLE_PATTERNS.items():
        match = pattern.search(notes)
        if match is None:
            continue
        declared = Path(match.group(1).strip())
        resolved = declared if declared.is_absolute() else package_root / declared
        try:
            result[role] = resolved.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            continue
    return result


def input_inventory(package_root: Path) -> dict[str, object]:
    package_root = package_root.resolve()
    repo_root = repository_root(package_root)
    if repo_root is None:
        return {"valid": False, "errors": ["cannot locate repository root for source inventory"]}
    entries: list[dict[str, str]] = []
    for directory_name in ("source", "support", "mockups"):
        directory = package_root / directory_name
        if not directory.is_dir():
            continue
        for path in sorted(candidate for candidate in directory.rglob("*") if candidate.is_file()):
            entries.append(
                {
                    "path": path.relative_to(repo_root).as_posix(),
                    "sha256": sha256(path),
                    "input_section": directory_name,
                }
            )
    return {
        "valid": True,
        "inputs": entries,
        "agent_notes_role_hints": agent_notes_role_hints(package_root, repo_root),
    }


def role_tokens(value: str) -> set[str]:
    return {token.strip().casefold() for token in re.split(r"[+,]", value) if token.strip()}


def validate(package_root: Path, handoff_dir: Path, allow_downstream: bool = False) -> list[str]:
    package_root = package_root.resolve()
    handoff_dir = handoff_dir.resolve()
    errors: list[str] = []
    errors.extend(validate_topology(package_root, "source-locator"))

    expected_handoff_dir = package_root / "work" / "stage-handoffs" / f"00-{package_root.name}"
    if handoff_dir != expected_handoff_dir.resolve():
        errors.append(
            "source handoff directory must be "
            f"work/stage-handoffs/00-{package_root.name}; "
            "do not derive the source handoff name from the target scope"
        )

    missing = [name for name in REQUIRED_HANDOFF_FILES if not (handoff_dir / name).is_file()]
    errors.extend(f"missing source artifact: {name}" for name in missing)
    notes_path = package_root / "AGENT-NOTES.md"
    if not notes_path.is_file():
        errors.append("missing package AGENT-NOTES.md")
    if missing or not notes_path.is_file():
        return errors

    workflow_path = handoff_dir / "workflow-state.yaml"
    selection_path = handoff_dir / "source-selection.md"
    workflow = workflow_path.read_text(encoding="utf-8")
    selection = selection_path.read_text(encoding="utf-8")
    notes = notes_path.read_text(encoding="utf-8")
    top = parse_top_level(workflow)
    if top.get("stage") != "source-locator":
        errors.append("workflow stage must be source-locator")
    if top.get("status") != "completed":
        errors.append("source-locator workflow status must be completed")

    repo_root = repository_root(package_root)
    if repo_root is None:
        errors.append("cannot locate repository root for source validation")
        return errors
    notes_role_hints = agent_notes_role_hints(package_root, repo_root)

    declared_selection = top.get("source_selection")
    expected_selection = selection_path.relative_to(repo_root).as_posix()
    if declared_selection != expected_selection:
        errors.append("workflow source_selection does not identify the current source-selection.md")

    registered_paths: set[str] = set()
    primary_roles: list[str] = []
    registered_entries: list[tuple[str, dict[str, str], Path]] = []
    for section in LOCAL_SECTIONS:
        for index, entry in enumerate(parse_list(workflow, section), start=1):
            label = f"{section}[{index}]"
            path_value = entry.get("path")
            role = entry.get("role")
            digest = entry.get("sha256")
            if not path_value:
                errors.append(f"{label}: path is required")
                continue
            if path_value in registered_paths:
                errors.append(f"{label}: duplicate registered path {path_value}")
            registered_paths.add(path_value)
            resolved, path_error = resolve_registered_path(repo_root, package_root, path_value)
            if path_error:
                errors.append(f"{label}: {path_error}")
                continue
            assert resolved is not None
            relative_to_package = resolved.relative_to(package_root)
            input_directory = relative_to_package.parts[0] if relative_to_package.parts else ""
            allowed_sections = {
                "source": {"primary_sources", "visual_sources"},
                "support": {"support_sources"},
                "mockups": {"visual_sources"},
            }.get(input_directory)
            if allowed_sections is not None and section not in allowed_sections:
                expected = " or ".join(sorted(allowed_sections))
                errors.append(
                    f"{label}: files under {input_directory}/ must be registered in {expected}"
                )
            if not resolved.is_file():
                errors.append(f"{label}: registered file does not exist: {path_value}")
            if not role:
                errors.append(f"{label}: role is required")
            elif section == "primary_sources":
                primary_roles.append(role)
            if role and resolved.is_file():
                registered_entries.append((section, entry, resolved))
            if not digest or not DIGEST_RE.fullmatch(digest):
                errors.append(f"{label}: sha256 must be a 64-character digest")
            elif resolved.is_file() and sha256(resolved) != digest.casefold():
                errors.append(f"{label}: SHA-256 mismatch for {path_value}")
            if path_value not in selection:
                errors.append(f"{label}: path is absent from source-selection.md")
            if digest and digest not in selection:
                errors.append(f"{label}: digest is absent from source-selection.md")

    contract_version = top.get("source_contract_version", "1")
    if contract_version == "1":
        if set(primary_roles) != LEGACY_PRIMARY_ROLES or len(primary_roles) != len(LEGACY_PRIMARY_ROLES):
            errors.append("legacy primary_sources must contain semantic, machine-readable and visual roles")
    elif contract_version == "2":
        primary_entries = [entry for section, entry, _ in registered_entries if section == "primary_sources"]
        semantic_entries = [entry for entry in primary_entries if SEMANTIC_ROLE in role_tokens(entry.get("role", ""))]
        machine_entries = [entry for entry in primary_entries if MACHINE_ROLE in role_tokens(entry.get("role", ""))]
        visual_entries = [
            entry
            for _, entry, _ in registered_entries
            if VISUAL_ROLE in role_tokens(entry.get("role", ""))
        ]
        if len(semantic_entries) != 1:
            errors.append("source contract v2 requires exactly one canonical semantic_primary")
        if len(machine_entries) != 1:
            errors.append("source contract v2 requires exactly one machine_readable_primary")
        for role, declared_path in notes_role_hints.items():
            matching_entries = semantic_entries if role == SEMANTIC_ROLE else machine_entries
            if len(matching_entries) == 1 and matching_entries[0].get("path") != declared_path:
                errors.append(
                    f"AGENT-NOTES.md declares {declared_path} as {role}, but workflow registers "
                    f"{matching_entries[0].get('path') or '<missing>'}"
                )

        visual_decision = top.get("visual_crosscheck")
        if visual_decision not in {"required", "not_required"}:
            errors.append("source contract v2 requires visual_crosscheck: required or not_required")
        elif visual_decision == "required" and not visual_entries:
            errors.append("visual_crosscheck is required but no visual source is registered")
        elif visual_decision == "not_required":
            if visual_entries:
                errors.append("visual sources are registered while visual_crosscheck is not_required")
            if not top.get("visual_crosscheck_reason"):
                errors.append("visual_crosscheck_reason is required when visual cross-check is not required")

        if len(machine_entries) == 1:
            machine = machine_entries[0]
            machine_path, machine_error = resolve_registered_path(repo_root, package_root, machine.get("path", ""))
            if machine_error is None and machine_path is not None and machine_path.is_file():
                try:
                    ET.parse(machine_path)
                except (ET.ParseError, OSError) as exc:
                    errors.append(f"machine_readable_primary must be well-formed XML/XHTML: {exc}")
            origin = machine.get("origin")
            if origin not in {"canonical", "generated", "supplied"}:
                errors.append("machine_readable_primary origin must be canonical, generated or supplied")
            elif origin == "canonical":
                if len(semantic_entries) != 1 or machine.get("path") != semantic_entries[0].get("path"):
                    errors.append("canonical machine-readable source must be the semantic primary path")
            elif origin == "generated":
                derived_from = machine.get("derived_from")
                derived_digest = machine.get("derived_from_sha256")
                generator = machine.get("generator")
                if len(semantic_entries) == 1 and derived_from != semantic_entries[0].get("path"):
                    errors.append("generated machine-readable source must derive from semantic_primary")
                if not derived_digest or not DIGEST_RE.fullmatch(derived_digest):
                    errors.append("generated machine-readable source requires derived_from_sha256")
                elif len(semantic_entries) == 1:
                    semantic_path, semantic_error = resolve_registered_path(
                        repo_root, package_root, semantic_entries[0].get("path", "")
                    )
                    if semantic_error is None and semantic_path is not None and semantic_path.is_file():
                        if sha256(semantic_path) != derived_digest.casefold():
                            errors.append("generated machine-readable source derives from a different semantic hash")
                if not generator:
                    errors.append("generated machine-readable source requires a generator identifier")
    else:
        errors.append("source_contract_version must be 1 or 2")

    actual_inputs: set[str] = set()
    for directory_name in ("source", "support", "mockups"):
        directory = package_root / directory_name
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file():
                actual_inputs.add(path.relative_to(repo_root).as_posix())
    for path_value in sorted(actual_inputs - registered_paths):
        errors.append(f"local FT input is not registered: {path_value}")
    for path_value in sorted(registered_paths - actual_inputs):
        errors.append(f"registered local path is outside source/support/mockups: {path_value}")

    figma_urls = {
        url.rstrip(URL_TRAILING_PUNCTUATION)
        for url in FIGMA_URL_RE.findall(notes)
    }
    for url in figma_urls:
        if url not in workflow or url not in selection:
            errors.append("Figma URL from AGENT-NOTES.md is not registered in workflow and source selection")

    if not allow_downstream:
        allowed_work_files = {
            (package_root / "work" / "runtime-session-registry.json").resolve(),
            (package_root / "work" / "scope-clarification-requests.md").resolve(),
            selection_path,
            workflow_path,
        }
        work_root = package_root / "work"
        if work_root.is_dir():
            for path in work_root.rglob("*"):
                if path.is_file() and path.resolve() not in allowed_work_files:
                    errors.append(f"source stage created downstream or extra work artifact: {path.relative_to(package_root).as_posix()}")
        test_case_root = package_root / "test-cases"
        if test_case_root.is_dir():
            for path in test_case_root.rglob("*"):
                if path.is_file():
                    errors.append(f"source stage created a test-case artifact: {path.relative_to(package_root).as_posix()}")

    registry, registry_errors = load_registry(package_root)
    errors.extend(registry_errors)
    locator_time: datetime | None = None
    if registry is not None:
        locator = registry.get("source_locator")
        recorded_at = locator.get("recorded_at") if isinstance(locator, dict) else None
        if isinstance(recorded_at, str):
            try:
                locator_time = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append("source-locator recorded_at is not a valid UTC timestamp")
    repo_tmp = repo_root / "tmp"
    if not allow_downstream and locator_time is not None and repo_tmp.is_dir():
        threshold = locator_time.astimezone(timezone.utc).timestamp()
        for path in repo_tmp.rglob("*"):
            if path.is_file() and path.stat().st_mtime >= threshold:
                errors.append(f"source stage left a repository-local temporary file: {path.relative_to(repo_root).as_posix()}")
    return errors


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate runtime source selection and source-stage cleanliness.")
    parser.add_argument("package_root", type=Path)
    parser.add_argument("handoff_dir", type=Path, nargs="?")
    parser.add_argument(
        "--print-input-inventory",
        action="store_true",
        help="Print repo-relative input paths, computed SHA-256 values and explicit AGENT-NOTES role hints.",
    )
    parser.add_argument(
        "--support-update",
        action="store_true",
        help="Validate a late support-only registration without rejecting existing downstream artifacts.",
    )
    parser.add_argument(
        "--resume-existing",
        action="store_true",
        help="Revalidate an unchanged existing source selection while preserving downstream artifacts.",
    )
    args = parser.parse_args()
    if args.print_input_inventory:
        result = input_inventory(args.package_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("valid") else 1
    if args.handoff_dir is None:
        parser.error("handoff_dir is required unless --print-input-inventory is used")
    errors = validate(
        args.package_root,
        args.handoff_dir,
        allow_downstream=args.support_update or args.resume_existing,
    )
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
