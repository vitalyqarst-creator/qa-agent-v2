from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.runtime_io import configure_utf8_stdio
    from scripts.runtime_review_delta import review_snapshot, validate_revision_manifest, write_revision_manifest
    from scripts.runtime_session_registry import (
        canonical_scope,
        record_role,
        required_skill_contract,
        validate_topology,
    )
except ModuleNotFoundError:  # Direct invocation: python scripts/runtime_review_dispatch.py
    from runtime_io import configure_utf8_stdio
    from runtime_review_delta import review_snapshot, validate_revision_manifest, write_revision_manifest
    from runtime_session_registry import canonical_scope, record_role, required_skill_contract, validate_topology


THREAD_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_to_package(path: Path, package_root: Path) -> str:
    resolved_root = package_root.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside FT package: {resolved_path}") from exc


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"dispatch-read-error: {exc}"]
    if not isinstance(payload, dict):
        return None, ["dispatch receipt must be a JSON object"]
    return payload, []


def validate_dispatch(
    package_root: Path,
    artifact: Path,
    review_prompt: Path,
    dispatch_path: Path,
    kind: str,
    expected_thread_id: str | None = None,
    require_current_assignment: bool = True,
) -> list[str]:
    errors: list[str] = []
    payload, load_errors = load_json(dispatch_path)
    if load_errors:
        return load_errors
    assert payload is not None

    schema_version = payload.get("schema_version")
    if schema_version not in {1, 2, 3}:
        errors.append("dispatch schema_version must be 1, 2, or 3")
    if payload.get("status") != "dispatched":
        errors.append("dispatch status must be dispatched")
    if payload.get("review_kind") != kind:
        errors.append(f"dispatch review_kind must be {kind}")
    if payload.get("controller_owned") is not True:
        errors.append("dispatch must be controller-owned")
    if payload.get("bootstrap_protocol") != "create-thread-then-controller-follow-up":
        errors.append("dispatch must use create-thread-then-controller-follow-up")

    dispatch_id = payload.get("dispatch_id")
    try:
        uuid.UUID(str(dispatch_id))
    except (ValueError, TypeError, AttributeError):
        errors.append("dispatch_id must be a UUID")

    expected_artifact_path = relative_to_package(artifact, package_root)
    if payload.get("artifact_path") != expected_artifact_path:
        errors.append("dispatch artifact_path does not match the checked artifact")
    artifact_digest = payload.get("artifact_sha256")
    if not artifact.is_file():
        errors.append(f"artifact does not exist: {artifact}")
    elif not isinstance(artifact_digest, str) or not DIGEST_RE.fullmatch(artifact_digest):
        errors.append("dispatch artifact_sha256 must be a 64-character SHA-256")
    elif artifact_digest.lower() != sha256(artifact):
        errors.append("dispatch is stale: artifact SHA-256 mismatch")

    expected_prompt_path = relative_to_package(review_prompt, package_root)
    if payload.get("review_prompt_path") != expected_prompt_path:
        errors.append("dispatch review_prompt_path does not match the operational prompt")
    prompt_digest = payload.get("review_prompt_sha256")
    if not review_prompt.is_file():
        errors.append(f"review prompt does not exist: {review_prompt}")
    elif not isinstance(prompt_digest, str) or not DIGEST_RE.fullmatch(prompt_digest):
        errors.append("dispatch review_prompt_sha256 must be a 64-character SHA-256")
    elif prompt_digest.lower() != sha256(review_prompt):
        errors.append("dispatch is stale: review prompt SHA-256 mismatch")

    if payload.get("reviewer_session_type") != "codex-thread":
        errors.append("dispatch reviewer_session_type must be codex-thread")
    thread_id = payload.get("reviewer_session_id")
    if not isinstance(thread_id, str) or not THREAD_ID_RE.fullmatch(thread_id):
        errors.append("dispatch reviewer_session_id must be a Codex thread UUID")
    elif expected_thread_id is not None and thread_id != expected_thread_id:
        errors.append("dispatch reviewer_session_id differs from the review record")
    host_id = payload.get("reviewer_host_id")
    if not isinstance(host_id, str) or not host_id.strip():
        errors.append("reviewer_host_id must be the non-empty host id returned by create_thread")
    dispatched_at = payload.get("dispatched_at")
    if not isinstance(dispatched_at, str) or not TIMESTAMP_RE.fullmatch(dispatched_at):
        errors.append("dispatched_at must use UTC YYYY-MM-DDTHH:MM:SSZ")
    if require_current_assignment:
        scope = canonical_scope(dispatch_path.parent.name)
        errors.extend(
            validate_topology(
                package_root,
                f"{kind}-reviewer",
                scope,
                f"{kind}-reviewer",
                thread_id if isinstance(thread_id, str) else None,
            )
        )
    if schema_version in {2, 3}:
        review_mode = payload.get("review_mode")
        if review_mode not in {"full", "delta"}:
            errors.append("dispatch review_mode must be full or delta")
        manifest_relative = payload.get("revision_manifest_path")
        manifest_digest = payload.get("revision_manifest_sha256")
        manifest_payload: dict[str, Any] | None = None
        if review_mode == "delta" and not isinstance(manifest_relative, str):
            errors.append("delta dispatch requires revision_manifest_path")
        if isinstance(manifest_relative, str):
            if Path(manifest_relative).is_absolute() or ".." in Path(manifest_relative).parts:
                errors.append("revision_manifest_path must be package-relative")
            else:
                manifest_path = (package_root / manifest_relative).resolve()
                if not manifest_path.is_file():
                    errors.append("revision manifest does not exist")
                elif not isinstance(manifest_digest, str) or not DIGEST_RE.fullmatch(manifest_digest):
                    errors.append("revision_manifest_sha256 must be a 64-character SHA-256")
                elif sha256(manifest_path) != manifest_digest.lower():
                    errors.append("revision manifest SHA-256 mismatch")
                else:
                    scope = canonical_scope(dispatch_path.parent.name)
                    errors.extend(
                        validate_revision_manifest(package_root, artifact, manifest_path, kind, scope)
                    )
                    try:
                        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        manifest_payload = None
                    if isinstance(manifest_payload, dict) and manifest_payload.get("review_mode") != review_mode:
                        errors.append("dispatch review_mode differs from revision manifest")
        round_value = payload.get("revision_cycle_round")
        purpose = payload.get("revision_purpose")
        expected_purpose = {0: "initial-review", 1: "bounded-revision", 2: "introduced-defect-correction"}.get(
            round_value
        )
        if expected_purpose is None or purpose != expected_purpose:
            errors.append("dispatch has invalid revision cycle metadata")
        if isinstance(manifest_relative, str) and isinstance(manifest_payload, dict):
            if manifest_payload.get("revision_cycle_round") != round_value:
                errors.append("dispatch revision round differs from revision manifest")
            if manifest_payload.get("revision_purpose") != purpose:
                errors.append("dispatch revision purpose differs from revision manifest")
    if schema_version == 3:
        inputs_relative = payload.get("review_inputs_path")
        inputs_digest = payload.get("review_inputs_sha256")
        if not isinstance(inputs_relative, str) or Path(inputs_relative).is_absolute() or ".." in Path(inputs_relative).parts:
            errors.append("schema v3 dispatch requires a package-relative review_inputs_path")
        else:
            inputs_path = package_root / inputs_relative
            if not inputs_path.is_file():
                errors.append("review input manifest does not exist")
            elif not isinstance(inputs_digest, str) or not DIGEST_RE.fullmatch(inputs_digest):
                errors.append("review_inputs_sha256 must be a 64-character SHA-256")
            elif sha256(inputs_path) != inputs_digest.lower():
                errors.append("review input manifest SHA-256 mismatch")
    return errors


def create_dispatch(
    package_root: Path,
    artifact: Path,
    review_prompt: Path,
    review_dir: Path,
    kind: str,
    reviewer_thread_id: str,
    reviewer_host_id: str,
    dispatched_at: str | None = None,
    previous_review: Path | None = None,
    reviewer_model: str | None = None,
    reviewer_thinking: str | None = None,
    review_inputs: Path | None = None,
) -> Path:
    if kind not in {"matrix", "tc"}:
        raise ValueError("review kind must be matrix or tc")
    if not THREAD_ID_RE.fullmatch(reviewer_thread_id):
        raise ValueError("reviewer thread id must be a UUID returned by Codex create_thread")
    if not reviewer_host_id.strip():
        raise ValueError("reviewer host id must be returned by Codex create_thread")
    if not artifact.is_file():
        raise ValueError(f"artifact does not exist: {artifact}")
    if not review_prompt.is_file():
        raise ValueError(f"review prompt does not exist: {review_prompt}")
    relative_to_package(review_dir, package_root)
    review_dir.mkdir(parents=True, exist_ok=True)

    scope = canonical_scope(review_dir.name)
    artifact_digest = sha256(artifact)
    manifest_path: Path | None = None
    review_mode = "full"
    revision_cycle_round = 0
    revision_purpose = "initial-review"
    if previous_review is not None:
        if not previous_review.is_file():
            raise ValueError(f"previous review does not exist: {previous_review}")
        manifest_path = write_revision_manifest(
            package_root,
            artifact,
            previous_review,
            review_dir,
            kind,
            scope,
        )
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        review_mode = manifest_payload["review_mode"]
        revision_cycle_round = manifest_payload["revision_cycle_round"]
        revision_purpose = manifest_payload["revision_purpose"]
    if review_inputs is not None:
        if not review_inputs.is_file():
            raise ValueError(f"review input manifest does not exist: {review_inputs}")
        relative_to_package(review_inputs, package_root)
    record_role(
        package_root,
        f"{kind}-reviewer",
        reviewer_thread_id,
        reviewer_host_id,
        scope,
        reviewer_model,
        reviewer_thinking,
    )
    output = review_dir / f"{kind}-review-dispatch-{artifact_digest[:12]}-{reviewer_thread_id[:8]}.json"
    stable_fields = {
        "schema_version": 3 if review_inputs is not None else 2,
        "status": "dispatched",
        "controller_owned": True,
        "bootstrap_protocol": "create-thread-then-controller-follow-up",
        "review_kind": kind,
        "artifact_path": relative_to_package(artifact, package_root),
        "artifact_sha256": artifact_digest,
        "review_prompt_path": relative_to_package(review_prompt, package_root),
        "review_prompt_sha256": sha256(review_prompt),
        "reviewer_session_type": "codex-thread",
        "reviewer_session_id": reviewer_thread_id,
        "reviewer_host_id": reviewer_host_id,
        "review_mode": review_mode,
        "revision_cycle_round": revision_cycle_round,
        "revision_purpose": revision_purpose,
    }
    if manifest_path is not None:
        stable_fields["revision_manifest_path"] = relative_to_package(manifest_path, package_root)
        stable_fields["revision_manifest_sha256"] = sha256(manifest_path)
    if review_inputs is not None:
        stable_fields["review_inputs_path"] = relative_to_package(review_inputs, package_root)
        stable_fields["review_inputs_sha256"] = sha256(review_inputs)
    if output.exists():
        existing, errors = load_json(output)
        if errors:
            raise ValueError(errors[0])
        assert existing is not None
        for key, value in stable_fields.items():
            if existing.get(key) != value:
                raise ValueError(f"existing dispatch differs in {key}; create a fresh reviewer thread")
        return output

    timestamp = dispatched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not TIMESTAMP_RE.fullmatch(timestamp):
        raise ValueError("dispatched_at must use UTC YYYY-MM-DDTHH:MM:SSZ")
    payload = {
        **stable_fields,
        "dispatch_id": str(uuid.uuid4()),
        "dispatched_at": timestamp,
    }
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return output


def write_stable_json(path: Path, payload: dict[str, Any]) -> Path:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise ValueError(f"existing controller-owned file differs: {path.name}")
    path.write_text(encoded, encoding="utf-8")
    return path


def prepare_review_package(
    package_root: Path,
    artifact: Path,
    review_dir: Path,
    kind: str,
    reviewer_thread_id: str,
    reviewer_host_id: str,
    dispatched_at: str | None = None,
    previous_review: Path | None = None,
    reviewer_model: str | None = None,
    reviewer_thinking: str | None = None,
) -> dict[str, str]:
    """Create the complete controller-owned transport package for one review."""

    package_root = package_root.resolve()
    artifact = artifact.resolve()
    review_dir = review_dir.resolve()
    relative_to_package(review_dir, package_root)
    review_dir.mkdir(parents=True, exist_ok=True)
    artifact_digest = sha256(artifact)
    scope = canonical_scope(review_dir.name)
    snapshot = review_snapshot(package_root, artifact, kind, scope)

    inputs_path = review_dir / f"{kind}-review-inputs-{artifact_digest[:12]}.json"
    inputs_payload = {
        "schema_version": 1,
        "review_kind": kind,
        "scope": scope,
        "artifact_path": relative_to_package(artifact, package_root),
        "artifact_sha256": artifact_digest,
        "semantic_input_hashes": snapshot["semantic_input_hashes"],
        "required_inputs": [
            relative_to_package(artifact, package_root),
            *snapshot["semantic_input_hashes"].keys(),
        ],
    }
    write_stable_json(inputs_path, inputs_payload)

    predicted_dispatch = review_dir / (
        f"{kind}-review-dispatch-{artifact_digest[:12]}-{reviewer_thread_id[:8]}.json"
    )
    predicted_scaffold = review_dir / f"{kind}-review-scaffold-{artifact_digest[:12]}.json"
    predicted_summary = review_dir / f"{kind}-review-scaffold-{artifact_digest[:12]}.md"
    prompt_path = review_dir / f"{kind}-review-prompt-{artifact_digest[:12]}.md"
    prompt = (
        f"Проведи независимое {kind} review текущего scope.\n\n"
        f"Controller-owned dispatch: `{relative_to_package(predicted_dispatch, package_root)}`.\n"
        f"Ограниченный input manifest: `{relative_to_package(inputs_path, package_root)}`.\n"
        f"Неизменяемый JSON scaffold: `{relative_to_package(predicted_scaffold, package_root)}`.\n"
        f"Неизменяемый Markdown scaffold: `{relative_to_package(predicted_summary, package_root)}`.\n\n"
        "Сначала выполни:\n\n"
        "```text\n"
        f'python scripts/runtime_review_dispatch.py verify-package --package-root "{package_root}" '
        f'--dispatch "{predicted_dispatch}" --reviewer-thread-id "{reviewer_thread_id}"\n'
        "```\n\n"
        "Полностью прочитай возвращённый reviewer skill. Используй только перечисленные inputs; "
        "расширяй их лишь при доказанной внешней зависимости и зафиксируй причину. Не изменяй "
        "controller-owned scaffolds: скопируй их машинные поля в canonical review JSON/Markdown, "
        "заполни содержательные поля и запусти штатный review validator.\n"
    )
    if prompt_path.exists() and prompt_path.read_text(encoding="utf-8") != prompt:
        raise ValueError(f"existing controller-owned file differs: {prompt_path.name}")
    prompt_path.write_text(prompt, encoding="utf-8")

    dispatch_path = create_dispatch(
        package_root,
        artifact,
        prompt_path,
        review_dir,
        kind,
        reviewer_thread_id,
        reviewer_host_id,
        dispatched_at,
        previous_review,
        reviewer_model,
        reviewer_thinking,
        review_inputs=inputs_path,
    )
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    reviewed_items = list(snapshot["artifact_index"]["order"])
    manifest_relative = dispatch.get("revision_manifest_path")
    if dispatch.get("review_mode") == "delta" and isinstance(manifest_relative, str):
        manifest = json.loads((package_root / manifest_relative).read_text(encoding="utf-8"))
        reviewed_items = list(manifest.get("changed_items", []))
    scaffold: dict[str, Any] = {
        "schema_version": 2,
        "review_kind": kind,
        "artifact_path": relative_to_package(artifact, package_root),
        "artifact_sha256": artifact_digest,
        "dispatch_path": relative_to_package(dispatch_path, package_root),
        "dispatch_sha256": sha256(dispatch_path),
        "reviewer_session_type": "codex-thread",
        "reviewer_session_id": reviewer_thread_id,
        "reviewed_at": "",
        "review_mode": dispatch["review_mode"],
        "revision_cycle_round": dispatch["revision_cycle_round"],
        "revision_purpose": dispatch["revision_purpose"],
        "artifact_index": snapshot["artifact_index"],
        "semantic_input_hashes": snapshot["semantic_input_hashes"],
        "reviewed_items": reviewed_items,
        "review_scope_complete": True,
        "verdict": "",
        "findings": [],
    }
    if isinstance(manifest_relative, str):
        scaffold["revision_manifest_path"] = manifest_relative
        scaffold["revision_manifest_sha256"] = dispatch["revision_manifest_sha256"]
        scaffold["review_quality_status"] = ""
    if kind == "matrix":
        scaffold["matrix_review_checklist_version"] = 3
        scaffold["matrix_review_checklist"] = {
            name: {"status": "", "evidence": []}
            for name in (
                "source-coverage",
                "formal-techniques",
                "uniqueness-lifecycle",
                "save-data-closure",
                "identity-provenance",
                "data-materializability",
                "reachability-oracles",
                "duplication-parameterization",
            )
        }
    else:
        total = len(snapshot["artifact_index"]["order"])
        scaffold["total_tc_count"] = total
        scaffold["reviewed_tc_count"] = len(reviewed_items)
    scaffold_path = predicted_scaffold
    write_stable_json(scaffold_path, scaffold)
    summary_path = predicted_summary
    summary = (
        f"# Независимое {kind} review\n\n"
        "## Verdict\n\n_[заполняет reviewer]_\n\n"
        "## Findings\n\n_[заполняет reviewer]_\n"
    )
    if kind == "tc":
        total = scaffold["total_tc_count"]
        checked = scaffold["reviewed_tc_count"]
        label = "Проверено изменённых TC" if dispatch["review_mode"] == "delta" else "Проверено TC"
        summary += f"\n{label}: {checked}/{total}\n"
    if summary_path.exists() and summary_path.read_text(encoding="utf-8") != summary:
        raise ValueError(f"existing controller-owned file differs: {summary_path.name}")
    summary_path.write_text(summary, encoding="utf-8")
    return {
        "review_prompt": str(prompt_path),
        "review_inputs": str(inputs_path),
        "dispatch": str(dispatch_path),
        "review_scaffold": str(scaffold_path),
        "summary_scaffold": str(summary_path),
    }


def main() -> int:
    configure_utf8_stdio()
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Create or verify a controller-owned runtime review dispatch receipt.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--package-root", type=Path, required=True)
    create_parser.add_argument("--artifact", type=Path, required=True)
    create_parser.add_argument("--review-prompt", type=Path, required=True)
    create_parser.add_argument("--review-dir", type=Path, required=True)
    create_parser.add_argument("--kind", choices=("matrix", "tc"), required=True)
    create_parser.add_argument("--reviewer-thread-id", required=True)
    create_parser.add_argument("--reviewer-host-id", required=True)
    create_parser.add_argument("--previous-review", type=Path)
    create_parser.add_argument("--reviewer-model")
    create_parser.add_argument("--reviewer-thinking")
    create_parser.add_argument("--review-inputs", type=Path)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--package-root", type=Path, required=True)
    prepare_parser.add_argument("--artifact", type=Path, required=True)
    prepare_parser.add_argument("--review-dir", type=Path, required=True)
    prepare_parser.add_argument("--kind", choices=("matrix", "tc"), required=True)
    prepare_parser.add_argument("--reviewer-thread-id", required=True)
    prepare_parser.add_argument("--reviewer-host-id", required=True)
    prepare_parser.add_argument("--previous-review", type=Path)
    prepare_parser.add_argument("--reviewer-model")
    prepare_parser.add_argument("--reviewer-thinking")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--package-root", type=Path, required=True)
    verify_parser.add_argument("--artifact", type=Path, required=True)
    verify_parser.add_argument("--review-prompt", type=Path, required=True)
    verify_parser.add_argument("--dispatch", type=Path, required=True)
    verify_parser.add_argument("--kind", choices=("matrix", "tc"), required=True)
    verify_parser.add_argument("--reviewer-thread-id")

    verify_package = subparsers.add_parser("verify-package")
    verify_package.add_argument("--package-root", type=Path, required=True)
    verify_package.add_argument("--dispatch", type=Path, required=True)
    verify_package.add_argument("--reviewer-thread-id", required=True)

    args = parser.parse_args()
    if args.command == "create":
        try:
            output = create_dispatch(
                args.package_root,
                args.artifact,
                args.review_prompt,
                args.review_dir,
                args.kind,
                args.reviewer_thread_id,
                args.reviewer_host_id,
                previous_review=args.previous_review,
                reviewer_model=args.reviewer_model,
                reviewer_thinking=args.reviewer_thinking,
                review_inputs=args.review_inputs,
            )
        except ValueError as exc:
            print(json.dumps({"created": False, "error": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps({"created": True, "path": str(output), "sha256": sha256(output)}, ensure_ascii=False))
        return 0

    if args.command == "prepare":
        try:
            outputs = prepare_review_package(
                args.package_root,
                args.artifact,
                args.review_dir,
                args.kind,
                args.reviewer_thread_id,
                args.reviewer_host_id,
                previous_review=args.previous_review,
                reviewer_model=args.reviewer_model,
                reviewer_thinking=args.reviewer_thinking,
            )
        except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            print(json.dumps({"created": False, "error": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps({"created": True, **outputs}, ensure_ascii=False))
        return 0

    if args.command == "verify-package":
        dispatch, load_errors = load_json(args.dispatch)
        if load_errors:
            print(json.dumps({"valid": False, "errors": load_errors}, ensure_ascii=False))
            return 1
        assert dispatch is not None
        try:
            artifact = (args.package_root / dispatch["artifact_path"]).resolve()
            prompt = (args.package_root / dispatch["review_prompt_path"]).resolve()
            kind = str(dispatch["review_kind"])
        except (KeyError, TypeError) as exc:
            print(json.dumps({"valid": False, "errors": [f"invalid dispatch: {exc}"]}, ensure_ascii=False))
            return 1
        errors = validate_dispatch(
            args.package_root,
            artifact,
            prompt,
            args.dispatch,
            kind,
            args.reviewer_thread_id,
        )
        result: dict[str, Any] = {"valid": not errors, "errors": errors}
        if not errors:
            result["required_skill"] = required_skill_contract(args.package_root, f"{kind}-reviewer")
            result["review_inputs"] = dispatch.get("review_inputs_path")
        print(json.dumps(result, ensure_ascii=False))
        return 0 if not errors else 1

    errors = validate_dispatch(
        args.package_root,
        args.artifact,
        args.review_prompt,
        args.dispatch,
        args.kind,
        args.reviewer_thread_id,
    )
    result: dict[str, Any] = {"valid": not errors, "errors": errors}
    if not errors:
        result["required_skill"] = required_skill_contract(args.package_root, f"{args.kind}-reviewer")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
