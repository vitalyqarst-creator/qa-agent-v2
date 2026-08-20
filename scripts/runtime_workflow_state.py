from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.runtime_io import configure_utf8_stdio
    from scripts.runtime_session_registry import find_package_root
    from scripts.runtime_state import scalar_values
except ModuleNotFoundError:  # Direct invocation
    from runtime_io import configure_utf8_stdio
    from runtime_session_registry import find_package_root
    from runtime_state import scalar_values


MATRIX_STATUSES = {"review-pending", "changes-required", "accepted", "revision-exhausted"}
STATE_ORDER = (
    "role",
    "scope",
    "matrix_status",
    "test_design_matrix",
    "matrix_sha256",
    "matrix_data_plan",
    "matrix_review",
    "matrix_review_sha256",
    "revision_closure",
    "revision_closure_sha256",
    "data_status",
    "data_materialization",
    "test_case_status",
    "test_cases",
)


def validate_matrix_review(matrix: Path, review_path: Path) -> list[str]:
    try:
        from scripts.validate_runtime_review import validate
    except ModuleNotFoundError:  # Direct invocation
        from validate_runtime_review import validate
    return validate(matrix.resolve(), review_path.resolve(), "matrix")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_relative(path: Path, package_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(package_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes FT package: {path}") from exc


def load_review(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("review record must be a JSON object")
    return payload


def exhaustion_contract_errors(review: dict[str, Any], closure: str) -> list[str]:
    errors: list[str] = []
    if review.get("review_kind") != "matrix" or review.get("verdict") != "matrix-changes-required":
        errors.append("revision-exhausted requires a prior matrix-changes-required record")
    findings = review.get("findings")
    if not isinstance(findings, list) or not findings:
        return errors + ["prior matrix review has no findings"]
    finding_ids = [finding.get("id") for finding in findings if isinstance(finding, dict)]
    if not finding_ids or any(not isinstance(finding_id, str) for finding_id in finding_ids):
        errors.append("prior matrix findings require string IDs")
    else:
        missing = [finding_id for finding_id in finding_ids if finding_id not in closure]
        if missing:
            errors.append("revision closure omits findings: " + ", ".join(missing))
    residual_counts = [
        int(value)
        for value in re.findall(r"Остаточн[^:\n|]*:\s*\*{0,2}(\d+)", closure, re.IGNORECASE)
    ]
    if not residual_counts or not any(value > 0 for value in residual_counts):
        errors.append("revision-exhausted closure must declare at least one positive residual count")
    return errors


def write_state(path: Path, values: dict[str, str]) -> None:
    ordered_keys = [key for key in STATE_ORDER if key in values]
    ordered_keys.extend(sorted(set(values) - set(ordered_keys)))
    lines = []
    for key in ordered_keys:
        value = values[key]
        if key in {"scope", "test_design_matrix", "matrix_data_plan", "matrix_review", "revision_closure", "data_materialization", "test_cases"}:
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def state_context(matrix: Path) -> tuple[Path, Path, dict[str, str]]:
    package_root = find_package_root(matrix)
    if package_root is None:
        raise ValueError("cannot locate FT package root")
    expected = package_root / "work" / "practical" / matrix.parent.name / "test-design-matrix.md"
    if matrix.resolve() != expected.resolve():
        raise ValueError(f"matrix must be stored at {expected}")
    state_path = matrix.parent / "workflow-state.yaml"
    values = scalar_values(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    return package_root, state_path, values


def set_pending(matrix: Path) -> dict[str, str]:
    package_root, state_path, values = state_context(matrix)
    data_plan = matrix.parent / "matrix-data-plan.md"
    if not data_plan.is_file():
        raise ValueError("matrix-data-plan.md is required before review-pending")
    for key in (
        "matrix_review",
        "matrix_review_sha256",
        "revision_closure",
        "revision_closure_sha256",
        "data_materialization",
        "test_cases",
    ):
        values.pop(key, None)
    values.update(
        {
            "role": "writer",
            "scope": matrix.parent.name,
            "matrix_status": "review-pending",
            "test_design_matrix": package_relative(matrix, package_root),
            "matrix_sha256": digest(matrix),
            "matrix_data_plan": package_relative(data_plan, package_root),
            "data_status": "not-started",
            "test_case_status": "not-started",
        }
    )
    write_state(state_path, values)
    return values


def apply_review(matrix: Path, review_path: Path) -> dict[str, str]:
    state_errors = validate_state(matrix)
    if state_errors == ["matrix review SHA-256 mismatch"]:
        package_root, _state_path, values = state_context(matrix)
        current_review = package_root / values.get("matrix_review", "")
        if current_review.resolve() == review_path.resolve():
            state_errors = []
    if state_errors:
        raise ValueError("invalid pre-review workflow state: " + "; ".join(state_errors))
    errors = validate_matrix_review(matrix, review_path)
    if errors:
        raise ValueError("invalid current matrix review: " + "; ".join(errors))
    review = load_review(review_path)
    verdict = review.get("verdict")
    status = {"matrix-accepted": "accepted", "matrix-changes-required": "changes-required"}.get(verdict)
    if status is None:
        raise ValueError("review verdict is not a matrix verdict")
    package_root, state_path, values = state_context(matrix)
    for key in ("revision_closure", "revision_closure_sha256"):
        values.pop(key, None)
    values.update(
        {
            "matrix_status": status,
            "matrix_sha256": digest(matrix),
            "matrix_review": package_relative(review_path, package_root),
            "matrix_review_sha256": digest(review_path),
        }
    )
    write_state(state_path, values)
    return values


def set_exhausted(matrix: Path, previous_review_path: Path, closure_path: Path) -> dict[str, str]:
    state_errors = validate_state(matrix)
    if state_errors:
        raise ValueError("invalid pre-exhaustion workflow state: " + "; ".join(state_errors))
    review = load_review(previous_review_path)
    closure = closure_path.read_text(encoding="utf-8")
    exhaustion_errors = exhaustion_contract_errors(review, closure)
    if exhaustion_errors:
        raise ValueError("; ".join(exhaustion_errors))
    package_root, state_path, values = state_context(matrix)
    values.update(
        {
            "matrix_status": "revision-exhausted",
            "matrix_sha256": digest(matrix),
            "matrix_review": package_relative(previous_review_path, package_root),
            "matrix_review_sha256": digest(previous_review_path),
            "revision_closure": package_relative(closure_path, package_root),
            "revision_closure_sha256": digest(closure_path),
        }
    )
    write_state(state_path, values)
    return values


def validate_state(matrix: Path) -> list[str]:
    errors: list[str] = []
    try:
        package_root, _state_path, values = state_context(matrix)
    except (OSError, ValueError, UnicodeError) as exc:
        return [str(exc)]
    status = values.get("matrix_status")
    if status not in MATRIX_STATUSES:
        errors.append(f"unsupported matrix_status {status!r}")
    if values.get("matrix_sha256") != digest(matrix):
        errors.append("matrix_sha256 does not match current matrix")
    expected_values = {
        "role": "writer",
        "scope": matrix.parent.name,
        "test_design_matrix": package_relative(matrix, package_root),
    }
    for key, expected in expected_values.items():
        if values.get(key) != expected:
            errors.append(f"{key} must be {expected!r}")
    expected_plan = matrix.parent / "matrix-data-plan.md"
    if values.get("matrix_data_plan") != package_relative(expected_plan, package_root):
        errors.append("matrix_data_plan does not reference the writer-owned plan")
    if not expected_plan.is_file():
        errors.append("writer-owned matrix data plan is missing")
    if status in {"accepted", "changes-required"}:
        review_value = values.get("matrix_review", "")
        review_path = package_root / review_value
        if not review_path.is_file():
            errors.append("matrix review path is missing")
        elif values.get("matrix_review_sha256") != digest(review_path):
            errors.append("matrix review SHA-256 mismatch")
        else:
            review_errors = validate_matrix_review(matrix, review_path)
            errors.extend(review_errors)
            if not review_errors:
                expected_verdict = "matrix-accepted" if status == "accepted" else "matrix-changes-required"
                if load_review(review_path).get("verdict") != expected_verdict:
                    errors.append(f"matrix_status {status} requires verdict {expected_verdict}")
    if status == "revision-exhausted":
        resolved_paths: dict[str, Path] = {}
        for path_key, digest_key in (
            ("matrix_review", "matrix_review_sha256"),
            ("revision_closure", "revision_closure_sha256"),
        ):
            value = values.get(path_key, "")
            path = package_root / value
            if not path.is_file():
                errors.append(f"{path_key} path is missing")
            elif values.get(digest_key) != digest(path):
                errors.append(f"{path_key} SHA-256 mismatch")
            else:
                resolved_paths[path_key] = path
        if {"matrix_review", "revision_closure"}.issubset(resolved_paths):
            try:
                review = load_review(resolved_paths["matrix_review"])
                closure = resolved_paths["revision_closure"].read_text(encoding="utf-8")
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"invalid revision-exhausted evidence: {exc}")
            else:
                errors.extend(exhaustion_contract_errors(review, closure))
    return errors


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Maintain hash-bound writer workflow state.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    pending = subparsers.add_parser("pending")
    pending.add_argument("--matrix", type=Path, required=True)
    reviewed = subparsers.add_parser("apply-review")
    reviewed.add_argument("--matrix", type=Path, required=True)
    reviewed.add_argument("--review-record", type=Path, required=True)
    exhausted = subparsers.add_parser("exhausted")
    exhausted.add_argument("--matrix", type=Path, required=True)
    exhausted.add_argument("--previous-review", type=Path, required=True)
    exhausted.add_argument("--closure", type=Path, required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--matrix", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "pending":
            payload = set_pending(args.matrix.resolve())
        elif args.command == "apply-review":
            payload = apply_review(args.matrix.resolve(), args.review_record.resolve())
        elif args.command == "exhausted":
            payload = set_exhausted(
                args.matrix.resolve(), args.previous_review.resolve(), args.closure.resolve()
            )
        else:
            errors = validate_state(args.matrix.resolve())
            print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
            return 0 if not errors else 1
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 1
    print(json.dumps({"valid": True, "state": payload}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
