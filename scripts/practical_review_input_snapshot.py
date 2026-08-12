"""Preflight or materialize immutable inputs for one practical v0.9 review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_review_input_snapshot import (
    PracticalV09Error,
    create_snapshot,
    verify_snapshot,
    verify_target_checkout,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ft-package-root", type=Path)
    parser.add_argument("--verify-target", type=Path)
    parser.add_argument("--create-snapshot", type=Path)
    parser.add_argument("--verify-snapshot", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = sum(bool(value) for value in (args.verify_target, args.create_snapshot, args.verify_snapshot))
    if selected != 1:
        raise SystemExit("error: provide exactly one of --verify-target, --create-snapshot or --verify-snapshot")
    try:
        if args.verify_target:
            result = verify_target_checkout(
                manifest_path=args.manifest,
                package_root=args.verify_target,
            )
        elif args.create_snapshot:
            if args.ft_package_root is None:
                raise PracticalV09Error("--ft-package-root is required with --create-snapshot")
            result = create_snapshot(
                manifest_path=args.manifest,
                package_root=args.ft_package_root,
                destination=args.create_snapshot,
            )
        else:
            result = verify_snapshot(
                manifest_path=args.manifest,
                snapshot_dir=args.verify_snapshot,
            )
    except (OSError, PracticalV09Error, ValueError) as exc:
        result = {"status": "blocked", "allowed": False, "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("allowed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
