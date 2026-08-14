"""Freeze compact v0.9 review inputs for a separate Codex reviewer session."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    PracticalV09Error,
    build_review_manifest,
    sha256_file,
    write_json,
)


def git_value(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo_root, check=True, text=True, capture_output=True, encoding="utf-8"
    )
    return completed.stdout.strip()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create one immutable practical v0.9 review manifest.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--workflow-state", type=Path, required=True)
    parser.add_argument("--review-mode", choices=("matrix", "test-cases"), required=True)
    parser.add_argument("--controller-thread-id", required=True)
    parser.add_argument("--contract-file", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    package_root = args.ft_package_root.resolve()
    output = args.output.resolve()
    try:
        output.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error("output must be inside FT package root") from exc
    if output.exists():
        raise PracticalV09Error(f"Refusing to overwrite immutable review manifest: {output}")
    try:
        ft_package_path = package_root.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise PracticalV09Error(
            "ft-package-root must be inside repo-root so the manifest can store a relative package path"
        ) from exc
    contract_files = [path.resolve() for path in args.contract_file]
    if any(not path.is_file() for path in contract_files):
        missing = [str(path) for path in contract_files if not path.is_file()]
        raise PracticalV09Error("Missing contract file(s): " + ", ".join(missing))
    contract_digest = sha256_file(contract_files[0]) if len(contract_files) == 1 else __import__("hashlib").sha256(
        "".join(sha256_file(path) for path in sorted(contract_files)).encode("ascii")
    ).hexdigest()
    payload = build_review_manifest(
        package_root=package_root,
        workflow_state_path=args.workflow_state.resolve(),
        review_mode=args.review_mode,
        controller_thread_id=args.controller_thread_id,
        code_branch=git_value(repo_root, "branch", "--show-current"),
        code_commit=git_value(repo_root, "rev-parse", "HEAD"),
        contract_digest=contract_digest,
        ft_package_path=ft_package_path,
        repo_root_path=str(repo_root),
        require_session_attestation=True,
    )
    write_json(output, payload)
    print(output.relative_to(package_root).as_posix())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PracticalV09Error, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
