"""Render the canonical, generated workflow-state example for practical v0.9."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import build_initial_workflow_state, write_json


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the generated workflow-state.json example for practical v0.9."
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def example_payload() -> dict[str, object]:
    return build_initial_workflow_state(
        scope_id="01",
        scope_slug="example-scope",
        source_package_manifest="work/practical-v0.9/source-package-manifest.json",
        scope_obligations="work/practical-v0.9/example-scope/scope-obligations.json",
        scope_clarification_requests=(
            "work/practical-v0.9/example-scope/scope-clarification-requests.md"
        ),
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    write_json(args.output.resolve(), example_payload())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
