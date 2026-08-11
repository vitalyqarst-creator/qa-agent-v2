"""One-pass, dependency-closed validator for practical v0.9.

Unlike the legacy profile helper, this command reads only the artefacts linked
from one compact workflow state.  The output file is written after validation
and is never considered an input of the same run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    PracticalV09Error,
    build_validator_report,
    load_workflow_state,
    relative_to_package,
    validate_scope,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate one compact practical v0.9 scope exactly once."
    )
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument(
        "--scope-manifest",
        type=Path,
        required=True,
        help="workflow-state.json for the active scope",
    )
    parser.add_argument("--output-profile", type=Path, required=True)
    parser.add_argument(
        "--exclude-output",
        type=Path,
        help="Optional explicit assertion that output-profile is not an input.",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Fail only when a finding has blocking=true.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    state_path = args.scope_manifest.resolve()
    output_path = args.output_profile.resolve()
    if not package_root.is_dir():
        raise PracticalV09Error(f"FT package root does not exist: {package_root}")
    try:
        output_path.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error("output-profile must be inside FT package root") from exc
    if args.exclude_output is not None and args.exclude_output.resolve() != output_path:
        raise PracticalV09Error("exclude-output must equal output-profile for the one-pass route")
    if not state_path.is_file():
        raise PracticalV09Error(f"scope-manifest does not exist: {state_path}")
    try:
        state_path.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error("scope-manifest must be inside FT package root") from exc
    # The output location is recorded in the only mutable control-plane file
    # before validation. validate_scope deliberately excludes this generated
    # report from its dependency closure, so a rerun is not a self-reference.
    state = load_workflow_state(state_path, package_root)
    current_output = state["artifacts"].get("validator_report")
    expected_output = relative_to_package(package_root, output_path)
    if current_output not in (None, "", "not-created", expected_output):
        raise PracticalV09Error(
            "workflow-state.json already binds a different validator_report; "
            "choose the recorded output path or update the scope deliberately"
        )
    state["artifacts"]["validator_report"] = expected_output
    write_json(state_path, state)
    context, findings = validate_scope(
        package_root=package_root,
        workflow_state_path=state_path,
    )
    if "validator_report" in context["input_hashes"]:
        raise PracticalV09Error("validator output cannot be part of its own input closure")
    report = build_validator_report(context, findings)
    write_json(output_path, report)
    compact = {
        "profile": output_path.relative_to(package_root).as_posix(),
        "scope_id": context["scope_id"],
        "scope_slug": context["scope_slug"],
        "blocking_count": report["summary"]["blocking_count"],
        "warnings_count": report["summary"]["warnings_count"],
        "clean": report["summary"]["clean"],
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    return 1 if args.require_clean and not report["summary"]["clean"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
