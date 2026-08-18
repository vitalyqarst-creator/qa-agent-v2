from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.runtime_session_registry import load_registry, validate_topology
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_source.py
    from runtime_session_registry import load_registry, validate_topology


DIGEST_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
URL_RE = re.compile(r"https://www\.figma\.com/\S+")
PRIMARY_ROLES = {
    "semantic_primary",
    "machine_readable_primary",
    "visual_structural_crosscheck_only",
}
LOCAL_SECTIONS = ("primary_sources", "support_sources", "visual_sources")
REQUIRED_HANDOFF_FILES = ("source-selection.md", "workflow-state.yaml")


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


def validate(package_root: Path, handoff_dir: Path, allow_downstream: bool = False) -> list[str]:
    package_root = package_root.resolve()
    handoff_dir = handoff_dir.resolve()
    errors: list[str] = []
    errors.extend(validate_topology(package_root, "source-locator"))

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

    declared_selection = top.get("source_selection")
    expected_selection = selection_path.relative_to(repo_root).as_posix()
    if declared_selection != expected_selection:
        errors.append("workflow source_selection does not identify the current source-selection.md")

    registered_paths: set[str] = set()
    primary_roles: list[str] = []
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
            if not resolved.is_file():
                errors.append(f"{label}: registered file does not exist: {path_value}")
            if not role:
                errors.append(f"{label}: role is required")
            elif section == "primary_sources":
                primary_roles.append(role)
            if not digest or not DIGEST_RE.fullmatch(digest):
                errors.append(f"{label}: sha256 must be a 64-character digest")
            elif resolved.is_file() and sha256(resolved) != digest.casefold():
                errors.append(f"{label}: SHA-256 mismatch for {path_value}")
            if path_value not in selection:
                errors.append(f"{label}: path is absent from source-selection.md")
            if digest and digest not in selection:
                errors.append(f"{label}: digest is absent from source-selection.md")

    if set(primary_roles) != PRIMARY_ROLES or len(primary_roles) != len(PRIMARY_ROLES):
        errors.append("primary_sources must contain exactly one semantic DOCX, machine-readable XHTML and visual PDF role")

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

    for path_value in sorted(actual_inputs):
        package_relative = (repo_root / path_value).relative_to(package_root).as_posix()
        directory_reference = f"{Path(package_relative).parts[0]}/"
        directory_classification_allowed = directory_reference == "mockups/" and directory_reference in notes
        if (
            package_relative not in notes
            and Path(package_relative).name not in notes
            and not directory_classification_allowed
        ):
            errors.append(f"AGENT-NOTES.md does not classify input {package_relative}")

    figma_urls = {url.rstrip(".,") for url in URL_RE.findall(notes)}
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
    parser = argparse.ArgumentParser(description="Validate runtime source selection and source-stage cleanliness.")
    parser.add_argument("package_root", type=Path)
    parser.add_argument("handoff_dir", type=Path)
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
    errors = validate(
        args.package_root,
        args.handoff_dir,
        allow_downstream=args.support_update or args.resume_existing,
    )
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
