"""Immutable transport for practical v0.9 review inputs.

Separate Codex sessions may open a worktree that does not include ignored or
uncommitted scope artefacts.  A review manifest already binds those artefacts
by SHA-256; this module either proves they exist in the designated target
checkout or makes one read-only, self-contained copy for the reviewer.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from test_case_agent.practical_v09 import PracticalV09Error, package_relative_path, read_json, sha256_file


SNAPSHOT_MANIFEST_FILENAME = "review-input-snapshot.json"
REVIEW_MANIFEST_FILENAME = "review-manifest.json"
SNAPSHOT_SCHEMA_VERSION = 1


def _review_inputs(manifest_path: Path) -> list[dict[str, str]]:
    manifest = read_json(manifest_path)
    inputs = manifest.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise PracticalV09Error("review manifest must contain a non-empty inputs array")
    normalized: list[dict[str, str]] = []
    for index, entry in enumerate(inputs, start=1):
        if not isinstance(entry, dict):
            raise PracticalV09Error(f"review manifest inputs[{index}] must be an object")
        role = str(entry.get("role") or "").strip()
        path = str(entry.get("path") or "").strip()
        digest = str(entry.get("sha256") or "").strip()
        if not role or not path or len(digest) != 64:
            raise PracticalV09Error(f"review manifest inputs[{index}] is incomplete")
        normalized.append({"role": role, "path": path, "sha256": digest})
    return normalized


def verify_target_checkout(*, manifest_path: Path, package_root: Path) -> dict[str, Any]:
    """Verify all manifest inputs before a reviewer is dispatched to a checkout."""
    inputs = _review_inputs(manifest_path)
    issues: list[str] = []
    for entry in inputs:
        target = package_relative_path(package_root, entry["path"], artifact="review manifest")
        if not target.is_file():
            issues.append(f"missing: {entry['path']}")
        elif sha256_file(target) != entry["sha256"]:
            issues.append(f"hash mismatch: {entry['path']}")
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "status": "allowed" if not issues else "blocked",
        "allowed": not issues,
        "review_manifest": manifest_path.resolve().as_posix(),
        "review_manifest_sha256": sha256_file(manifest_path),
        "target_package_root": package_root.resolve().as_posix(),
        "issues": issues,
    }


def create_snapshot(*, manifest_path: Path, package_root: Path, destination: Path) -> dict[str, Any]:
    """Copy exactly the hash-bound review inputs into one immutable directory."""
    verified = verify_target_checkout(manifest_path=manifest_path, package_root=package_root)
    if not verified["allowed"]:
        raise PracticalV09Error("cannot snapshot unavailable review inputs: " + "; ".join(verified["issues"]))
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"review input snapshot already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.tmp-", dir=destination.parent))
    try:
        raw_review_manifest = manifest_path.read_bytes()
        (temporary / REVIEW_MANIFEST_FILENAME).write_bytes(raw_review_manifest)
        if sha256_file(temporary / REVIEW_MANIFEST_FILENAME) != sha256_file(manifest_path):
            raise PracticalV09Error("copied review manifest hash mismatch")
        records: list[dict[str, str]] = []
        for entry in _review_inputs(manifest_path):
            source = package_relative_path(package_root, entry["path"], artifact="review manifest")
            copied_relative = Path("inputs") / Path(entry["path"])
            copied = temporary / copied_relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, copied)
            copied_hash = sha256_file(copied)
            if copied_hash != entry["sha256"]:
                raise PracticalV09Error(f"copy hash mismatch for {entry['path']}")
            records.append({
                "role": entry["role"],
                "source_path": entry["path"],
                "snapshot_path": copied_relative.as_posix(),
                "sha256": copied_hash,
            })
        snapshot_manifest = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "snapshot_role": "practical-review-inputs",
            "review_manifest_sha256": sha256_file(manifest_path),
            "review_manifest_path": REVIEW_MANIFEST_FILENAME,
            "inputs": records,
        }
        (temporary / SNAPSHOT_MANIFEST_FILENAME).write_text(
            json.dumps(snapshot_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return verify_snapshot(manifest_path=manifest_path, snapshot_dir=destination)


def verify_snapshot(*, manifest_path: Path, snapshot_dir: Path) -> dict[str, Any]:
    """Verify a transported snapshot against the original immutable manifest."""
    snapshot_dir = snapshot_dir.resolve()
    issues: list[str] = []
    try:
        payload = json.loads((snapshot_dir / SNAPSHOT_MANIFEST_FILENAME).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"schema_version": SNAPSHOT_SCHEMA_VERSION, "status": "blocked", "allowed": False, "issues": [str(exc)]}
    if payload.get("snapshot_role") != "practical-review-inputs":
        issues.append("snapshot_role must be practical-review-inputs")
    if payload.get("review_manifest_sha256") != sha256_file(manifest_path):
        issues.append("snapshot is bound to another review manifest")
    copied_manifest = snapshot_dir / str(payload.get("review_manifest_path") or "")
    if not copied_manifest.is_file():
        issues.append("snapshot review manifest is missing")
    elif sha256_file(copied_manifest) != sha256_file(manifest_path):
        issues.append("snapshot review manifest hash mismatch")
    expected = {(entry["role"], entry["path"]): entry for entry in _review_inputs(manifest_path)}
    records = payload.get("inputs")
    actual: set[tuple[str, str]] = set()
    if not isinstance(records, list):
        issues.append("snapshot inputs must be an array")
        records = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            issues.append(f"snapshot inputs[{index}] must be an object")
            continue
        role = str(record.get("role") or "")
        source_path = str(record.get("source_path") or "")
        key = (role, source_path)
        actual.add(key)
        expected_entry = expected.get(key)
        snapshot_path = str(record.get("snapshot_path") or "")
        copied = (snapshot_dir / snapshot_path).resolve()
        try:
            copied.relative_to(snapshot_dir)
        except ValueError:
            issues.append(f"snapshot inputs[{index}] escapes snapshot directory")
            continue
        if expected_entry is None:
            issues.append(f"unexpected snapshot input: {role}/{source_path}")
        elif not copied.is_file():
            issues.append(f"missing snapshot input: {source_path}")
        elif sha256_file(copied) != expected_entry["sha256"]:
            issues.append(f"hash mismatch in snapshot: {source_path}")
    missing = sorted(set(expected) - actual)
    issues.extend(f"missing snapshot record: {role}/{path}" for role, path in missing)
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "status": "allowed" if not issues else "blocked",
        "allowed": not issues,
        "review_manifest": manifest_path.resolve().as_posix(),
        "review_manifest_sha256": sha256_file(manifest_path),
        "snapshot_dir": snapshot_dir.as_posix(),
        "issues": issues,
    }
