"""Record the controller-owned proof of a separately created reviewer task."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    PracticalV09Error,
    build_review_session_attestation,
    relative_to_package,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record the actual separate Codex reviewer thread for practical v0.9."
    )
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--review-manifest", type=Path, required=True)
    parser.add_argument("--reviewer-thread-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    manifest_path = args.review_manifest.resolve()
    output = args.output.resolve()
    try:
        output.relative_to(package_root)
        manifest_path.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error(
            "review manifest and attestation output must be inside FT package root"
        ) from exc
    if output.exists():
        raise PracticalV09Error(
            f"Refusing to overwrite controller session attestation: {output}"
        )
    payload = build_review_session_attestation(
        package_root=package_root,
        manifest_path=manifest_path,
        reviewer_thread_id=args.reviewer_thread_id,
    )
    write_json(output, payload)
    print(relative_to_package(package_root, output))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
