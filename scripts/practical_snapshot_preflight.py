"""Create and verify immutable rollback snapshots for practical writer revisions.

The command is deliberately small: it snapshots only the package-relative
artifacts that a bounded writer revision is going to overwrite.  A snapshot is
published only after copied bytes match the pre-write source hashes; an existing
snapshot directory is never repaired or reused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path


SNAPSHOT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def resolve_sources(ft_package_root: Path, values: list[str]) -> list[Path]:
    sources: list[Path] = []
    for value in values:
        candidate = Path(value)
        source = candidate.resolve() if candidate.is_absolute() else (ft_package_root / candidate).resolve()
        if not source.is_file() or not is_within(source, ft_package_root):
            raise ValueError(f"source must be an existing file inside FT package: {value}")
        sources.append(source)
    if not sources:
        raise ValueError("at least one --source is required")
    if len({str(source).casefold() for source in sources}) != len(sources):
        raise ValueError("--source values must be unique")
    return sources


def snapshot_directory(ft_package_root: Path, scope_slug: str, snapshot_id: str) -> Path:
    if not SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise ValueError("snapshot id may contain only letters, digits, '.', '_' and '-'")
    if not scope_slug or Path(scope_slug).name != scope_slug:
        raise ValueError("scope slug must be a single path segment")
    return ft_package_root / "work" / "review-cycles" / scope_slug / "versions" / snapshot_id


def create_snapshot(
    *,
    ft_package_root: Path,
    scope_slug: str,
    snapshot_id: str,
    sources: list[Path],
    reason: str,
) -> dict[str, object]:
    destination = snapshot_directory(ft_package_root, scope_slug, snapshot_id)
    if destination.exists():
        raise FileExistsError(f"snapshot already exists and is immutable: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{snapshot_id}.tmp-", dir=destination.parent))
    try:
        records: list[dict[str, object]] = []
        for source in sources:
            source_relative = source.relative_to(ft_package_root).as_posix()
            copied_relative = Path("files") / Path(source_relative)
            copied = temporary / copied_relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            source_sha256 = sha256_file(source)
            shutil.copy2(source, copied)
            copied_sha256 = sha256_file(copied)
            if source_sha256 != copied_sha256:
                raise RuntimeError(f"snapshot copy hash mismatch for {source_relative}")
            records.append(
                {
                    "source_path": source_relative,
                    "snapshot_path": copied_relative.as_posix(),
                    "source_sha256_before_write": source_sha256,
                    "snapshot_sha256": copied_sha256,
                    "size_bytes": copied.stat().st_size,
                }
            )

        manifest: dict[str, object] = {
            "schema_version": 1,
            "snapshot_id": snapshot_id,
            "snapshot_role": "pre_write_baseline",
            "snapshot_status": "valid",
            "scope_slug": scope_slug,
            "reason": reason,
            "source_files": records,
        }
        # JSON is valid YAML and gives the verifier a dependency-free, exact format.
        (temporary / "snapshot-manifest.yaml").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return {
        "status": "valid",
        "snapshot_dir": destination.as_posix(),
        "manifest": (destination / "snapshot-manifest.yaml").as_posix(),
        "files": records,
    }


def verify_snapshot(snapshot_dir: Path, ft_package_root: Path) -> dict[str, object]:
    manifest_path = snapshot_dir / "snapshot-manifest.yaml"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "snapshot_dir": snapshot_dir.as_posix(), "issues": [str(exc)]}

    issues: list[str] = []
    if manifest.get("snapshot_role") != "pre_write_baseline":
        issues.append("snapshot_role must be pre_write_baseline")
    if manifest.get("snapshot_status") != "valid":
        issues.append("snapshot_status must be valid")
    records = manifest.get("source_files")
    if not isinstance(records, list) or not records:
        issues.append("source_files must be a non-empty list")
        records = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            issues.append(f"source_files[{index}] is not an object")
            continue
        source_path = record.get("source_path")
        snapshot_path = record.get("snapshot_path")
        source_hash = record.get("source_sha256_before_write")
        copied_hash = record.get("snapshot_sha256")
        if not all(isinstance(value, str) and value for value in (source_path, snapshot_path, source_hash, copied_hash)):
            issues.append(f"source_files[{index}] misses required hash/path fields")
            continue
        copied = (snapshot_dir / snapshot_path).resolve()
        if not is_within(copied, snapshot_dir) or not copied.is_file():
            issues.append(f"source_files[{index}] snapshot file is missing")
            continue
        actual_hash = sha256_file(copied)
        if actual_hash != copied_hash or actual_hash != source_hash:
            issues.append(f"source_files[{index}] hash does not equal pre-write source hash")
        if not is_within((ft_package_root / source_path).resolve(), ft_package_root):
            issues.append(f"source_files[{index}] source_path escapes FT package")

    return {
        "status": "valid" if not issues else "invalid",
        "snapshot_dir": snapshot_dir.as_posix(),
        "issues": issues,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or verify an immutable practical-route baseline snapshot.")
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--scope-slug")
    parser.add_argument("--snapshot-id")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--reason", default="pre_quality_gate_baseline")
    parser.add_argument("--verify", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ft_package_root = args.ft_package_root.resolve()
    if not ft_package_root.is_dir():
        raise SystemExit(f"error: FT package root does not exist: {ft_package_root}")
    try:
        if args.verify:
            result = verify_snapshot(args.verify.resolve(), ft_package_root)
        else:
            if not args.scope_slug or not args.snapshot_id:
                raise ValueError("--scope-slug and --snapshot-id are required when creating a snapshot")
            result = create_snapshot(
                ft_package_root=ft_package_root,
                scope_slug=args.scope_slug,
                snapshot_id=args.snapshot_id,
                sources=resolve_sources(ft_package_root, args.source),
                reason=args.reason,
            )
    except (OSError, ValueError, RuntimeError) as exc:
        result = {"status": "invalid", "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
