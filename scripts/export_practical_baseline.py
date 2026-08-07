"""Export one accepted practical TC baseline into a hash-manifest ZIP bundle.

FT packages are often ignored by Git while they are being prepared locally.
This explicit export preserves the accepted canonical suite and its final review
evidence without staging unrelated package artifacts or rewriting the suite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import practical_review_preflight as review_preflight  # noqa: E402
import validate_agent_artifacts as artifact_validator  # noqa: E402


ACCEPTED_VALUES = {
    "accepted",
    "tc-accepted",
    "signed-off",
    "signed-off-local",
    "accepted-local-publication-pending",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_artifact(value: object, workflow_path: Path, ft_package_root: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return artifact_validator.resolve_artifact_path(
        value,
        workflow_path,
        ft_package_root,
        ft_package_root,
    )


def first_existing_artifact(
    latest: dict[str, Any],
    keys: tuple[str, ...],
    workflow_path: Path,
    ft_package_root: Path,
) -> Path | None:
    for key in keys:
        resolved = resolve_artifact(latest.get(key), workflow_path, ft_package_root)
        if resolved is not None and resolved.is_file():
            return resolved
    return None


def export_scope(
    *,
    ft_package_root: Path,
    scope_id: str,
    summary_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    ft_package_root = ft_package_root.resolve()
    summary_path = summary_path.resolve()
    descriptors, issues = review_preflight.scope_descriptors(ft_package_root, [scope_id])
    if issues or len(descriptors) != 1:
        raise ValueError("; ".join(issues) or "scope handoff is not uniquely resolvable")
    descriptor = descriptors[0]
    state = artifact_validator.parse_workflow_state(descriptor.workflow_path)
    status_candidates = [
        str(state.get(key, "")).casefold().strip()
        for key in (
            "final_independent_tc_review_status",
            "tc_review_status",
            "review_verdict",
            "tc_release_status",
        )
    ]
    if not any(value in ACCEPTED_VALUES for value in status_candidates):
        raise ValueError("scope does not record an accepted independent TC review")
    latest = state.get("latest_artifacts")
    if not isinstance(latest, dict):
        raise ValueError("workflow latest_artifacts is missing")
    canonical = first_existing_artifact(
        latest,
        ("canonical_test_cases", "canonical_tc", "test_cases"),
        descriptor.workflow_path,
        ft_package_root,
    )
    findings = first_existing_artifact(
        latest,
        ("final_tc_review_findings", "tc_review_findings", "review_findings"),
        descriptor.workflow_path,
        ft_package_root,
    )
    independence = first_existing_artifact(
        latest,
        ("final_tc_review_independence", "tc_review_independence", "review_independence"),
        descriptor.workflow_path,
        ft_package_root,
    )
    if canonical is None or findings is None or independence is None:
        raise ValueError("accepted scope lacks canonical TC, review findings or independence artifact")
    if not summary_path.is_file() or not review_preflight.is_within(summary_path, ft_package_root):
        raise ValueError("practical stage summary is missing or outside FT package root")
    if output_path.exists():
        raise FileExistsError(f"export bundle already exists: {output_path}")

    files = [canonical, findings, independence, descriptor.workflow_path, summary_path]
    manifest_files = [
        {
            "path": path.relative_to(ft_package_root).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in files
    ]
    manifest = {
        "schema_version": 1,
        "bundle_type": "practical-accepted-baseline",
        "ft_package_root_name": ft_package_root.name,
        "scope_id": scope_id,
        "scope_slug": descriptor.scope_slug,
        "files": manifest_files,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        for path in files:
            archive.write(path, arcname=path.relative_to(ft_package_root).as_posix())
    return {
        "status": "exported",
        "bundle": output_path.resolve().as_posix(),
        "scope_id": scope_id,
        "scope_slug": descriptor.scope_slug,
        "files": manifest_files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export an accepted practical TC baseline bundle.")
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = export_scope(
            ft_package_root=args.ft_package_root,
            scope_id=args.scope_id,
            summary_path=args.summary,
            output_path=args.output,
        )
    except (OSError, ValueError) as exc:
        result = {"status": "blocked", "reason": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "exported" else 2


if __name__ == "__main__":
    raise SystemExit(main())
