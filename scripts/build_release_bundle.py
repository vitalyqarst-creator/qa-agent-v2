from __future__ import annotations

import argparse
import fnmatch
import glob
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
RELEASE_MANIFEST_NAME = "release-manifest.json"


class ReleaseBundleError(RuntimeError):
    pass


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ReleaseBundleError("release manifest must be a schema v1 object")
    if payload.get("profile") not in {"qualification", "production"}:
        raise ReleaseBundleError("release profile must be qualification or production")
    for key in (
        "include",
        "exclude",
        "required_paths",
        "forbidden_prefixes",
        "forbidden_suffixes",
        "local_inputs",
    ):
        if not isinstance(payload.get(key), list):
            raise ReleaseBundleError(f"release manifest field {key} must be a list")
    return payload


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _resolve_files(root: Path, manifest: dict[str, Any]) -> tuple[Path, ...]:
    selected: dict[str, Path] = {}
    for pattern in manifest["include"]:
        if not isinstance(pattern, str) or not pattern:
            raise ReleaseBundleError("include patterns must be non-empty strings")
        for raw in glob.glob(pattern, root_dir=root, recursive=True, include_hidden=True):
            relative = Path(raw)
            candidate = (root / relative).resolve()
            try:
                normalized = candidate.relative_to(root).as_posix()
            except ValueError as exc:
                raise ReleaseBundleError(f"include escapes repository root: {raw}") from exc
            if not candidate.is_file() or candidate.is_symlink():
                continue
            if _matches(normalized, manifest["exclude"]):
                continue
            selected[normalized] = candidate
    paths = tuple(selected[key] for key in sorted(selected))
    normalized_paths = {path.relative_to(root).as_posix() for path in paths}
    missing = sorted(set(manifest["required_paths"]) - normalized_paths)
    if missing:
        raise ReleaseBundleError("required release paths are missing: " + ", ".join(missing))
    _validate_forbidden_paths(normalized_paths, manifest)
    return paths


def _validate_forbidden_paths(paths: Iterable[str], manifest: dict[str, Any]) -> None:
    violations: list[str] = []
    prefixes = tuple(str(item) for item in manifest["forbidden_prefixes"])
    suffixes = tuple(str(item).casefold() for item in manifest["forbidden_suffixes"])
    for path in paths:
        if any(path.startswith(prefix) for prefix in prefixes) or path.casefold().endswith(
            suffixes
        ):
            violations.append(path)
    if violations:
        raise ReleaseBundleError(
            "forbidden paths entered the release: " + ", ".join(sorted(violations))
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_local_inputs(
    root: Path,
    manifest: dict[str, Any],
    *,
    require_local_inputs: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in manifest["local_inputs"]:
        if not isinstance(item, dict):
            raise ReleaseBundleError("local_inputs entries must be objects")
        relative = item.get("path")
        expected = item.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ReleaseBundleError("local input requires path and sha256 strings")
        path = (root / relative).resolve()
        exists = path.is_file()
        actual = _sha256(path) if exists else None
        matched = actual == expected
        results.append(
            {
                "path": relative,
                "exists": exists,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "matched": matched,
            }
        )
        if require_local_inputs and not matched:
            raise ReleaseBundleError(f"local qualification input mismatch: {relative}")
    return results


def _bundle_receipt(
    root: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    files: Sequence[Path],
    local_inputs: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in files
    ]
    tree_material = "".join(
        f"{item['path']}\0{item['bytes']}\0{item['sha256']}\n" for item in entries
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "profile": manifest["profile"],
        "source_manifest": manifest_path.relative_to(root).as_posix(),
        "source_manifest_sha256": _sha256(manifest_path),
        "file_count": len(entries),
        "total_bytes": sum(item["bytes"] for item in entries),
        "tree_sha256": hashlib.sha256(tree_material).hexdigest(),
        "local_inputs": list(local_inputs),
        "files": entries,
    }


def build_release_bundle(
    *,
    root: Path,
    manifest_path: Path,
    output: Path | None,
    check_only: bool,
    require_local_inputs: bool,
) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    manifest = _load_manifest(manifest_path)
    files = _resolve_files(root, manifest)
    local_inputs = _validate_local_inputs(
        root,
        manifest,
        require_local_inputs=require_local_inputs,
    )
    receipt = _bundle_receipt(root, manifest_path, manifest, files, local_inputs)
    if check_only:
        return receipt
    if output is None:
        raise ReleaseBundleError("output is required unless --check-only is used")
    output = output.resolve()
    if output.exists():
        raise ReleaseBundleError(f"release output must be fresh: {output}")
    output.mkdir(parents=True)
    for source in files:
        relative = source.relative_to(root)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    (output / RELEASE_MANIFEST_NAME).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Build a deterministic release bundle.")
    result.add_argument("--root", type=Path, default=ROOT_DIR)
    result.add_argument("--manifest", type=Path, required=True)
    result.add_argument("--output", type=Path)
    result.add_argument("--check-only", action="store_true")
    result.add_argument("--require-local-inputs", action="store_true")
    result.add_argument("--list-paths", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    try:
        receipt = build_release_bundle(
            root=root,
            manifest_path=manifest_path,
            output=args.output,
            check_only=args.check_only or args.list_paths,
            require_local_inputs=args.require_local_inputs,
        )
    except (OSError, json.JSONDecodeError, ReleaseBundleError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    if args.list_paths:
        print("\n".join(item["path"] for item in receipt["files"]))
    else:
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
