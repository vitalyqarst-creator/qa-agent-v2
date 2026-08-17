from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from scripts.runtime_review_dispatch import load_json as load_dispatch_json
from scripts.runtime_review_dispatch import validate_dispatch


THREAD_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
REVIEWED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
TC_HEADING_RE = re.compile(r"^##\s+TC-[^\r\n]+$", re.MULTILINE)
VERDICTS = {
    "matrix": {"matrix-accepted", "matrix-changes-required"},
    "tc": {"tc-accepted", "tc-changes-required"},
}


def load_record(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"review-record-read-error: {exc}"]
    if not isinstance(payload, dict):
        return None, ["review record must be a JSON object"]
    return payload, []


def validate(artifact: Path, record_path: Path, kind: str, require_accepted: bool = False) -> list[str]:
    errors: list[str] = []
    record, load_errors = load_record(record_path)
    if load_errors:
        return load_errors
    assert record is not None

    expected_record_name = f"{kind}-review.json"
    if record_path.name != expected_record_name:
        errors.append(f"review record must be named {expected_record_name}")
    summary_path = record_path.with_suffix(".md")
    if not summary_path.is_file():
        errors.append(f"human review summary does not exist: {summary_path.name}")

    if record.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if record.get("review_kind") != kind:
        errors.append(f"review_kind must be {kind}")
    declared_path = record.get("artifact_path")
    package_root: Path | None = None
    if not isinstance(declared_path, str) or not declared_path.strip():
        errors.append("artifact_path is required")
    else:
        normalized_artifact = artifact.resolve().as_posix().casefold()
        normalized_declared = Path(declared_path).as_posix().lstrip("./").casefold()
        if not normalized_artifact.endswith(normalized_declared):
            errors.append("artifact_path does not identify the checked artifact")
        elif Path(declared_path).is_absolute() or ".." in Path(declared_path).parts:
            errors.append("artifact_path must be package-relative")
        else:
            package_root = artifact.resolve()
            for _part in Path(declared_path).parts:
                package_root = package_root.parent

    if not artifact.is_file():
        errors.append(f"artifact does not exist: {artifact}")
    else:
        actual_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        declared_digest = record.get("artifact_sha256")
        if not isinstance(declared_digest, str) or not DIGEST_RE.fullmatch(declared_digest):
            errors.append("artifact_sha256 must be a 64-character SHA-256")
        elif declared_digest.lower() != actual_digest:
            errors.append("review is stale: artifact SHA-256 mismatch")

    if record.get("reviewer_session_type") != "codex-thread":
        errors.append("reviewer_session_type must be codex-thread")
    session_id = record.get("reviewer_session_id")
    if not isinstance(session_id, str) or not THREAD_ID_RE.fullmatch(session_id):
        errors.append("reviewer_session_id must be a top-level Codex thread UUID")
    reviewed_at = record.get("reviewed_at")
    if not isinstance(reviewed_at, str) or not REVIEWED_AT_RE.fullmatch(reviewed_at):
        errors.append("reviewed_at must use UTC YYYY-MM-DDTHH:MM:SSZ")

    verdict = record.get("verdict")
    if verdict not in VERDICTS[kind]:
        errors.append(f"invalid {kind} verdict")
    findings = record.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a JSON list")
    elif isinstance(verdict, str) and verdict.endswith("-accepted") and findings:
        errors.append("accepted verdict requires an empty findings list")
    elif isinstance(verdict, str) and verdict.endswith("-changes-required") and not findings:
        errors.append("changes-required verdict requires findings")
    if require_accepted and verdict != f"{kind}-accepted":
        errors.append(f"current artifact does not have {kind}-accepted verdict")

    if kind == "tc" and artifact.is_file():
        tc_count = len(TC_HEADING_RE.findall(artifact.read_text(encoding="utf-8")))
        if tc_count == 0:
            errors.append("canonical TC artifact contains no TC headings")
        if record.get("total_tc_count") != tc_count:
            errors.append(f"total_tc_count must equal canonical TC count: {tc_count}")
        if record.get("reviewed_tc_count") != tc_count:
            errors.append(f"reviewed_tc_count must prove full-set review: {tc_count}")
        if record.get("review_scope_complete") is not True:
            errors.append("review_scope_complete must be true for TC review")
        if summary_path.is_file():
            summary = summary_path.read_text(encoding="utf-8")
            if f"Проверено TC: {tc_count}/{tc_count}" not in summary:
                errors.append(f"human review summary must contain: Проверено TC: {tc_count}/{tc_count}")

    dispatch_relative = record.get("dispatch_path")
    dispatch_digest = record.get("dispatch_sha256")
    if not isinstance(dispatch_relative, str) or not dispatch_relative.strip():
        errors.append("dispatch_path is required")
    elif Path(dispatch_relative).is_absolute() or ".." in Path(dispatch_relative).parts:
        errors.append("dispatch_path must be package-relative")
    elif package_root is not None:
        dispatch_path = (package_root / dispatch_relative).resolve()
        try:
            dispatch_path.relative_to(package_root.resolve())
        except ValueError:
            errors.append("dispatch_path escapes the FT package")
        else:
            if not dispatch_path.is_file():
                errors.append(f"dispatch receipt does not exist: {dispatch_relative}")
            elif not isinstance(dispatch_digest, str) or not DIGEST_RE.fullmatch(dispatch_digest):
                errors.append("dispatch_sha256 must be a 64-character SHA-256")
            elif hashlib.sha256(dispatch_path.read_bytes()).hexdigest() != dispatch_digest.lower():
                errors.append("dispatch receipt SHA-256 mismatch")
            else:
                dispatch, dispatch_load_errors = load_dispatch_json(dispatch_path)
                if dispatch_load_errors:
                    errors.extend(dispatch_load_errors)
                else:
                    assert dispatch is not None
                    prompt_relative = dispatch.get("review_prompt_path")
                    if not isinstance(prompt_relative, str) or Path(prompt_relative).is_absolute() or ".." in Path(prompt_relative).parts:
                        errors.append("dispatch review_prompt_path must be package-relative")
                    else:
                        prompt_path = (package_root / prompt_relative).resolve()
                        errors.extend(
                            validate_dispatch(
                                package_root,
                                artifact,
                                prompt_path,
                                dispatch_path,
                                kind,
                                session_id if isinstance(session_id, str) else None,
                                require_current_assignment=False,
                            )
                        )
                        dispatched_at = dispatch.get("dispatched_at")
                        if isinstance(dispatched_at, str) and isinstance(reviewed_at, str) and reviewed_at < dispatched_at:
                            errors.append("reviewed_at precedes controller dispatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a hash-bound runtime review record.")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("review_record", type=Path)
    parser.add_argument("--kind", choices=("matrix", "tc"), required=True)
    parser.add_argument("--require-accepted", action="store_true")
    args = parser.parse_args()
    errors = validate(args.artifact, args.review_record, args.kind, args.require_accepted)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
