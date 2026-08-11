from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from codex_review_cycle_runner import (
    RunnerError,
    current_scope_validator_findings,
    infer_ft_root,
    relative_or_name,
    run_agent_artifact_validator,
    write_runner_scoped_validator_profile,
)
from validate_agent_artifacts import parse_workflow_state


SELF_PROFILE_FINDING_ID = "writer-quality-gate-scoped-validator-profile-invalid"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the artifact validator and write runner-generated scoped evidence for one workflow state."
    )
    parser.add_argument("--workflow-state", type=Path, required=True)
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Return exit status 1 when the active scope has unresolved warning/error findings.",
    )
    return parser.parse_args(argv)


def is_current_profile_self_finding(
    finding: object,
    *,
    profile_path: Path,
) -> bool:
    """Return true only for the validator's report about this profile itself.

    A scoped profile is intentionally read by the validator which produced it.
    If the profile records a real unresolved current-scope finding, the
    validator also reports that the profile is unresolved.  Feeding that
    derived report back into the same profile creates an infinite self-reference
    and hides the original finding.  Do not suppress any other finding: the
    persisted second validator run remains the authoritative gate.
    """

    if not isinstance(finding, dict) or finding.get("id") != SELF_PROFILE_FINDING_ID:
        return False
    evidence = finding.get("evidence")
    if not isinstance(evidence, list):
        return False
    profile_name = profile_path.name
    return any(
        profile_name in str(item)
        and (
            "profile-has-unresolved-current-scope-findings" in str(item)
            or "unresolved_warning_error_count=" in str(item)
        )
        for item in evidence
    )


def scoped_findings_without_current_profile_self_reference(
    validator_payload: dict[str, object],
    state: dict[str, object],
    state_path: Path,
    profile_path: Path,
) -> list[dict[str, object]]:
    """Keep real scoped findings while removing only this profile's echo."""

    scoped_findings = current_scope_validator_findings(validator_payload, state, state_path)
    return [
        finding
        for finding in scoped_findings
        if not is_current_profile_self_finding(finding, profile_path=profile_path)
    ]


def unresolved_warning_or_error_count(findings: list[dict[str, object]]) -> int:
    return sum(
        1
        for finding in findings
        if str(finding.get("severity") or "").strip().lower() in {"warning", "error"}
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    state_path = args.workflow_state.resolve()
    if not state_path.is_file():
        raise RunnerError(f"Workflow state does not exist: {state_path}")

    state = parse_workflow_state(state_path)
    latest_artifacts = state.get("latest_artifacts")
    if isinstance(latest_artifacts, dict):
        for key in ("canonical_test_cases", "test_design_dir"):
            if not str(state.get(key) or "").strip() and latest_artifacts.get(key):
                state[key] = latest_artifacts[key]
        if not str(state.get("test_design_dir") or "").strip():
            writer_gate = str(latest_artifacts.get("writer_quality_gate") or "").strip()
            if writer_gate:
                state["test_design_dir"] = Path(writer_gate).parent.as_posix()
    missing = [key for key in ("scope_slug", "current_stage") if not str(state.get(key) or "").strip()]
    if missing:
        raise RunnerError(
            f"Workflow state cannot produce scoped validator evidence; missing: {', '.join(missing)}"
        )

    ft_root = infer_ft_root(state_path)
    profile_path = (
        state_path.parent
        / "outputs"
        / f"scoped-validator-profile.{state['current_stage']}.json"
    )

    first_payload = run_agent_artifact_validator(ft_root)
    first_scoped_findings = scoped_findings_without_current_profile_self_reference(
        first_payload,
        state,
        state_path,
        profile_path,
    )
    profile_path = write_runner_scoped_validator_profile(
        state,
        state_path,
        first_payload,
        scoped_findings=first_scoped_findings,
    )

    # Validate the persisted profile once.  This catches an invalid runner
    # output while avoiding the profile's own derived warning as input data.
    second_payload = run_agent_artifact_validator(ft_root)
    scoped_findings = scoped_findings_without_current_profile_self_reference(
        second_payload,
        state,
        state_path,
        profile_path,
    )
    unresolved_count = unresolved_warning_or_error_count(scoped_findings)
    print(
        json.dumps(
            {
                "profile": relative_or_name(profile_path, ft_root),
                "scope_slug": state["scope_slug"],
                "current_stage": state["current_stage"],
                "unresolved_warning_error_count": unresolved_count,
                "clean": unresolved_count == 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if args.require_clean and unresolved_count else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunnerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
