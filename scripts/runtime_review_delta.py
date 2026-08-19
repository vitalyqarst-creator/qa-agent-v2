from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.runtime_traceability import find_markdown_table
    from scripts.validate_runtime_matrix import COVERAGE_MODEL_HEADERS, REQUIRED_HEADERS
except ModuleNotFoundError:  # Direct invocation
    from runtime_traceability import find_markdown_table
    from validate_runtime_matrix import COVERAGE_MODEL_HEADERS, REQUIRED_HEADERS


DIGEST_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
TC_HEADING_RE = re.compile(r"(?m)^##\s+(TC-[^\r\n]+)\s*$")
SEMANTIC_STAGE_EXCLUDES = (
    "prompt.",
    "validator",
    "workflow-state",
    "agent-decision-log",
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_text(value: str) -> str:
    return digest_bytes(value.replace("\r\n", "\n").encode("utf-8"))


def canonical_digest(value: Any) -> str:
    return digest_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def matrix_artifact_index(content: str) -> dict[str, Any]:
    items: dict[str, str] = {}
    order: list[str] = []
    matrix = find_markdown_table(content, REQUIRED_HEADERS)
    if matrix is None or not matrix.rows:
        raise ValueError("matrix artifact has no required rows")
    for row in matrix.rows:
        item_id = row[matrix.index("ID")].strip()
        if not item_id or item_id in items:
            raise ValueError(f"matrix artifact contains an empty or duplicate item: {item_id!r}")
        items[item_id] = canonical_digest(list(row))
        order.append(item_id)

    model = find_markdown_table(content, COVERAGE_MODEL_HEADERS)
    if model is not None:
        for row in model.rows:
            item_id = row[model.index("Элемент покрытия")].strip()
            if not item_id or item_id in items:
                raise ValueError(f"matrix coverage model contains an empty or duplicate item: {item_id!r}")
            items[item_id] = canonical_digest(list(row))
            order.append(item_id)

    known = set(items)
    skeleton: list[str] = []
    for line in content.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            first = stripped.strip("|").split("|", 1)[0].strip()
            if first in known:
                skeleton.append(f"| <ITEM:{first}> |")
                continue
        skeleton.append(line)
    return {
        "items": items,
        "order": order,
        "structure_sha256": digest_text("\n".join(skeleton)),
    }


def tc_artifact_index(content: str) -> dict[str, Any]:
    matches = list(TC_HEADING_RE.finditer(content))
    if not matches:
        raise ValueError("TC artifact contains no TC headings")
    items: dict[str, str] = {}
    order: list[str] = []
    skeleton = [content[: matches[0].start()]]
    for index, match in enumerate(matches):
        item_id = match.group(1).strip()
        if item_id in items:
            raise ValueError(f"TC artifact contains duplicate heading {item_id}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        items[item_id] = digest_text(content[match.start() : end])
        order.append(item_id)
        skeleton.append(f"<ITEM:{item_id}>\n")
    return {
        "items": items,
        "order": order,
        "structure_sha256": digest_text("".join(skeleton)),
    }


def artifact_index(artifact: Path, kind: str) -> dict[str, Any]:
    content = artifact.read_text(encoding="utf-8")
    if kind == "matrix":
        return matrix_artifact_index(content)
    if kind == "tc":
        return tc_artifact_index(content)
    raise ValueError("review kind must be matrix or tc")


def semantic_input_files(package_root: Path, artifact: Path, kind: str, scope: str) -> list[Path]:
    candidates: set[Path] = set()
    notes = package_root / "AGENT-NOTES.md"
    if notes.is_file():
        candidates.add(notes)
    for directory_name in ("source", "support", "mockups"):
        directory = package_root / directory_name
        if directory.is_dir():
            candidates.update(path for path in directory.rglob("*") if path.is_file())

    clarifications = package_root / "work" / "scope-clarification-requests.md"
    if clarifications.is_file():
        candidates.add(clarifications)
    handoff = package_root / "work" / "stage-handoffs" / scope
    if handoff.is_dir():
        for path in handoff.rglob("*"):
            if not path.is_file() or any(part.startswith("_") for part in path.relative_to(handoff).parts):
                continue
            lowered = path.name.casefold()
            if lowered.endswith(".tmp") or "session-log" in lowered or any(
                lowered.startswith(prefix) for prefix in SEMANTIC_STAGE_EXCLUDES
            ):
                continue
            candidates.add(path)

    work = package_root / "work"
    if work.is_dir() and kind == "tc":
        candidates.update(path for path in work.rglob("fixture-catalog.json") if path.is_file())
        candidates.update(path for path in work.rglob("data-materialization.json") if path.is_file())
    for fixture_directory in (package_root / "fixtures", package_root / "work" / "fixtures"):
        if fixture_directory.is_dir():
            candidates.update(path for path in fixture_directory.rglob("*") if path.is_file())
    if kind == "tc":
        matrix = package_root / "work" / "practical" / scope / "test-design-matrix.md"
        if matrix.is_file():
            candidates.add(matrix)
    candidates.discard(artifact.resolve())
    return sorted((path.resolve() for path in candidates), key=lambda value: value.as_posix().casefold())


def semantic_input_hashes(package_root: Path, artifact: Path, kind: str, scope: str) -> dict[str, str]:
    result: dict[str, str] = {}
    resolved_root = package_root.resolve()
    for path in semantic_input_files(resolved_root, artifact, kind, scope):
        try:
            relative = path.relative_to(resolved_root).as_posix()
        except ValueError as exc:
            raise ValueError(f"semantic input escapes FT package: {path}") from exc
        result[relative] = digest_bytes(path.read_bytes())
    return result


def review_snapshot(package_root: Path, artifact: Path, kind: str, scope: str) -> dict[str, Any]:
    return {
        "artifact_index": artifact_index(artifact, kind),
        "semantic_input_hashes": semantic_input_hashes(package_root, artifact, kind, scope),
    }


def affected_items(findings: Any) -> tuple[set[str], list[str]]:
    items: set[str] = set()
    errors: list[str] = []
    if not isinstance(findings, list):
        return items, ["previous findings must be a list"]
    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            errors.append(f"previous finding {index} must be an object")
            continue
        values = finding.get("affected_items")
        if not isinstance(values, list) or not values or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            errors.append(f"previous finding {index} must contain non-empty affected_items")
            continue
        items.update(value.strip() for value in values)
    return items, errors


def validate_previous_review_evidence(
    package_root: Path,
    artifact: Path,
    previous: dict[str, Any],
    kind: str,
) -> list[str]:
    errors: list[str] = []
    if previous.get("schema_version") != 2:
        errors.append("delta re-review requires a schema v2 previous review")
    if previous.get("review_kind") != kind or previous.get("verdict") != f"{kind}-changes-required":
        errors.append("previous review is not a matching changes-required review")
    try:
        expected_artifact_path = artifact.resolve().relative_to(package_root.resolve()).as_posix()
    except ValueError:
        return errors + ["review artifact escapes FT package"]
    if previous.get("artifact_path") != expected_artifact_path:
        errors.append("previous review artifact_path differs from current artifact")
    previous_digest = previous.get("artifact_sha256")
    if not isinstance(previous_digest, str) or not DIGEST_RE.fullmatch(previous_digest):
        errors.append("previous review artifact_sha256 is invalid")
    elif previous_digest == digest_bytes(artifact.read_bytes()):
        errors.append("revision did not change artifact bytes")
    previous_index = previous.get("artifact_index")
    previous_semantic = previous.get("semantic_input_hashes")
    if not isinstance(previous_index, dict) or not isinstance(previous_semantic, dict):
        errors.append("previous review lacks a validated artifact/input snapshot")
    else:
        items = previous_index.get("items")
        order = previous_index.get("order")
        structure = previous_index.get("structure_sha256")
        if not isinstance(items, dict) or not items or not all(
            isinstance(key, str) and isinstance(value, str) and DIGEST_RE.fullmatch(value)
            for key, value in items.items()
        ):
            errors.append("previous review artifact item hashes are invalid")
        if not isinstance(order, list) or set(order) != set(items or {}):
            errors.append("previous review artifact item order is invalid")
        if not isinstance(structure, str) or not DIGEST_RE.fullmatch(structure):
            errors.append("previous review artifact structure hash is invalid")
        if not all(
            isinstance(path, str) and isinstance(value, str) and DIGEST_RE.fullmatch(value)
            for path, value in previous_semantic.items()
        ):
            errors.append("previous review semantic input hashes are invalid")

    dispatch_relative = previous.get("dispatch_path")
    dispatch_digest = previous.get("dispatch_sha256")
    if not isinstance(dispatch_relative, str) or Path(dispatch_relative).is_absolute() or ".." in Path(dispatch_relative).parts:
        errors.append("previous review dispatch_path is invalid")
        return errors
    dispatch_path = package_root / dispatch_relative
    if not dispatch_path.is_file():
        errors.append("previous review dispatch receipt is missing")
        return errors
    if not isinstance(dispatch_digest, str) or not DIGEST_RE.fullmatch(dispatch_digest):
        errors.append("previous review dispatch_sha256 is invalid")
    elif digest_bytes(dispatch_path.read_bytes()) != dispatch_digest.lower():
        errors.append("previous review dispatch SHA-256 mismatch")
    try:
        dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        errors.append("previous review dispatch receipt is unreadable")
        return errors
    if not isinstance(dispatch, dict):
        errors.append("previous review dispatch receipt must be an object")
    else:
        if dispatch.get("review_kind") != kind:
            errors.append("previous dispatch review kind mismatch")
        if dispatch.get("artifact_path") != expected_artifact_path:
            errors.append("previous dispatch artifact path mismatch")
        if dispatch.get("artifact_sha256") != previous_digest:
            errors.append("previous dispatch artifact SHA differs from review record")
        if dispatch.get("reviewer_session_id") != previous.get("reviewer_session_id"):
            errors.append("previous dispatch reviewer session differs from review record")
    return errors


def build_revision_manifest(
    package_root: Path,
    artifact: Path,
    previous_review_path: Path,
    kind: str,
    scope: str,
) -> dict[str, Any]:
    previous_raw = previous_review_path.read_bytes()
    previous = json.loads(previous_raw.decode("utf-8"))
    if not isinstance(previous, dict):
        raise ValueError("previous review must be a JSON object")
    return {
        "schema_version": 1,
        "review_kind": kind,
        "scope": scope,
        "previous_review_sha256": canonical_digest(previous),
        "previous_review_record": previous,
        **build_revision_manifest_from_record(package_root, artifact, previous, kind, scope),
    }


def validate_revision_manifest(
    package_root: Path,
    artifact: Path,
    manifest_path: Path,
    kind: str,
    scope: str,
) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"revision-manifest-read-error: {exc}"]
    if not isinstance(manifest, dict):
        return ["revision manifest must be a JSON object"]
    if manifest.get("schema_version") != 1:
        errors.append("revision manifest schema_version must be 1")
    if manifest.get("review_kind") != kind or manifest.get("scope") != scope:
        errors.append("revision manifest kind/scope mismatch")
    previous = manifest.get("previous_review_record")
    if not isinstance(previous, dict):
        return errors + ["revision manifest lacks previous_review_record"]
    if manifest.get("previous_review_sha256") != canonical_digest(previous):
        errors.append("revision manifest previous_review_sha256 is inconsistent")
    try:
        rebuilt = build_revision_manifest_from_record(package_root, artifact, previous, kind, scope)
    except ValueError as exc:
        return errors + [str(exc)]
    for key in (
        "review_mode",
        "previous_artifact_sha256",
        "current_artifact_sha256",
        "current_artifact_index",
        "current_semantic_input_hashes",
        "allowed_items",
        "changed_items",
        "unchanged_item_count",
        "changed_semantic_inputs",
        "fallback_reasons",
    ):
        if manifest.get(key) != rebuilt.get(key):
            errors.append(f"revision manifest field {key} is stale or inconsistent")
    if manifest.get("review_mode") not in {"full", "delta"}:
        errors.append("revision manifest review_mode must be full or delta")
    return errors


def build_revision_manifest_from_record(
    package_root: Path,
    artifact: Path,
    previous: dict[str, Any],
    kind: str,
    scope: str,
) -> dict[str, Any]:
    evidence_errors = validate_previous_review_evidence(package_root, artifact, previous, kind)
    if evidence_errors:
        raise ValueError(evidence_errors[0])
    previous_index = previous.get("artifact_index")
    previous_semantic = previous.get("semantic_input_hashes")
    if not isinstance(previous_index, dict) or not isinstance(previous_semantic, dict):
        raise ValueError("previous review lacks a validated artifact/input snapshot")
    current = review_snapshot(package_root, artifact, kind, scope)
    current_index = current["artifact_index"]
    old_items = previous_index.get("items")
    new_items = current_index.get("items")
    if not isinstance(old_items, dict) or not isinstance(new_items, dict):
        raise ValueError("artifact item indexes must be JSON objects")
    changed = sorted(key for key in set(old_items) | set(new_items) if old_items.get(key) != new_items.get(key))
    if not changed:
        raise ValueError("revision did not change any reviewable item")
    allowed, affected_errors = affected_items(previous.get("findings"))
    current_semantic = current["semantic_input_hashes"]
    changed_inputs = sorted(
        key for key in set(previous_semantic) | set(current_semantic) if previous_semantic.get(key) != current_semantic.get(key)
    )
    fallback_reasons = list(affected_errors)
    if changed_inputs:
        fallback_reasons.append("semantic-inputs-changed")
    if previous_index.get("structure_sha256") != current_index.get("structure_sha256"):
        fallback_reasons.append("artifact-structure-or-order-changed")
    if set(changed) - allowed:
        fallback_reasons.append("undeclared-items-changed")
    if allowed & {"*", "GLOBAL"}:
        fallback_reasons.append("global-finding")
    return {
        "review_mode": "delta" if not fallback_reasons else "full",
        "previous_artifact_sha256": previous.get("artifact_sha256"),
        "current_artifact_sha256": digest_bytes(artifact.read_bytes()),
        "current_artifact_index": current_index,
        "current_semantic_input_hashes": current_semantic,
        "allowed_items": sorted(allowed),
        "changed_items": changed,
        "unchanged_item_count": len(set(old_items) & set(new_items) - set(changed)),
        "changed_semantic_inputs": changed_inputs,
        "fallback_reasons": fallback_reasons,
    }


def write_revision_manifest(
    package_root: Path,
    artifact: Path,
    previous_review_path: Path,
    review_dir: Path,
    kind: str,
    scope: str,
) -> Path:
    payload = build_revision_manifest(package_root, artifact, previous_review_path, kind, scope)
    output = review_dir / f"{kind}-revision-manifest-{payload['current_artifact_sha256'][:12]}.json"
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != encoded:
        raise ValueError("existing revision manifest differs for the same artifact")
    review_dir.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
    return output


def enrich_review_record(package_root: Path, artifact: Path, record_path: Path, kind: str, scope: str) -> None:
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("review record must be a JSON object")
    dispatch_relative = record.get("dispatch_path")
    if not isinstance(dispatch_relative, str):
        raise ValueError("review record must contain dispatch_path before enrichment")
    dispatch = json.loads((package_root / dispatch_relative).read_text(encoding="utf-8"))
    snapshot = review_snapshot(package_root, artifact, kind, scope)
    record["schema_version"] = 2
    record.update(snapshot)
    record["review_mode"] = dispatch.get("review_mode", "full")
    if dispatch.get("revision_manifest_path"):
        record["revision_manifest_path"] = dispatch["revision_manifest_path"]
        record["revision_manifest_sha256"] = dispatch["revision_manifest_sha256"]
    else:
        record.pop("revision_manifest_path", None)
        record.pop("revision_manifest_sha256", None)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate bounded re-review evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enrich = subparsers.add_parser("enrich-review")
    enrich.add_argument("--package-root", type=Path, required=True)
    enrich.add_argument("--artifact", type=Path, required=True)
    enrich.add_argument("--review-record", type=Path, required=True)
    enrich.add_argument("--kind", choices=("matrix", "tc"), required=True)
    enrich.add_argument("--scope", required=True)

    verify = subparsers.add_parser("verify-manifest")
    verify.add_argument("--package-root", type=Path, required=True)
    verify.add_argument("--artifact", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--kind", choices=("matrix", "tc"), required=True)
    verify.add_argument("--scope", required=True)

    args = parser.parse_args()
    if args.command == "enrich-review":
        try:
            enrich_review_record(args.package_root, args.artifact, args.review_record, args.kind, args.scope)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"updated": False, "error": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps({"updated": True, "path": str(args.review_record)}, ensure_ascii=False))
        return 0

    errors = validate_revision_manifest(
        args.package_root, args.artifact, args.manifest, args.kind, args.scope
    )
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
