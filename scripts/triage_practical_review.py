"""Record a bounded controller triage for a changes-required practical review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    ALLOWED_EXECUTION_STATUSES,
    ALLOWED_TRIAGE_DISPOSITIONS,
    ALLOWED_TRIAGE_REJECTION_BASES,
    CONTROLLER_TRIAGE_CONTRACT_VERSION,
    PracticalV09Error,
    active_obligations,
    derived_execution_status,
    execution_contexts,
    execution_setups,
    load_workflow_state,
    package_relative_path,
    parse_matrix_rows,
    read_json,
    relative_to_package,
    review_content_findings,
    sha256_file,
    verify_review_result,
    workflow_artifact_path,
    workflow_controller_triage_enabled,
    workflow_controller_triage_version,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate controller decisions before practical review finalization."
    )
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--workflow-state", type=Path, required=True)
    parser.add_argument("--review-manifest", type=Path, required=True)
    parser.add_argument("--review-result", type=Path, required=True)
    parser.add_argument(
        "--review-session-attestation",
        type=Path,
        help="Controller-owned attestation recorded after creating the separate reviewer task.",
    )
    parser.add_argument(
        "--decisions-file",
        type=Path,
        required=True,
        help="Temporary UTF-8 JSON with review_result_sha256 and decisions.",
    )
    return parser.parse_args(argv)


def decision_map(payload: dict[str, Any], expected_ids: set[str]) -> dict[str, dict[str, Any]]:
    raw = payload.get("decisions")
    if not isinstance(raw, list):
        raise PracticalV09Error("decisions-file: decisions must be an array")
    mapped: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("finding_id"), str):
            raise PracticalV09Error(
                "decisions-file: every decision must contain string finding_id"
            )
        finding_id = item["finding_id"]
        if finding_id in mapped:
            raise PracticalV09Error(
                f"decisions-file: duplicate decision for {finding_id}"
            )
        mapped[finding_id] = item
    if set(mapped) != expected_ids:
        raise PracticalV09Error(
            "decisions-file: decisions must cover exactly content blocking findings; "
            f"expected={','.join(sorted(expected_ids)) or '-'}; "
            f"actual={','.join(sorted(mapped)) or '-'}"
        )
    return mapped


def require_common_decision_fields(decision: dict[str, Any]) -> None:
    anchors = decision.get("checked_anchors")
    if (
        decision.get("disposition") not in ALLOWED_TRIAGE_DISPOSITIONS
        or not isinstance(decision.get("rationale"), str)
        or len(decision["rationale"].strip()) < 16
        or not isinstance(anchors, list)
        or not anchors
        or not all(isinstance(anchor, str) and anchor.strip() for anchor in anchors)
    ):
        raise PracticalV09Error(
            "decisions-file: each decision requires disposition, rationale "
            "(at least 16 characters) and non-empty checked_anchors"
        )


def derived_status_for_scenarios(
    *,
    state: dict[str, Any],
    package_root: Path,
    scenario_ids: list[str],
) -> set[str]:
    matrix_path = workflow_artifact_path(state, package_root, "test_design_matrix", required=True)
    obligations_path = workflow_artifact_path(state, package_root, "scope_obligations", required=True)
    assert matrix_path is not None and obligations_path is not None
    rows, errors = parse_matrix_rows(matrix_path)
    if errors:
        raise PracticalV09Error("matrix cannot be used for controller triage: " + "; ".join(errors))
    rows_by_scenario = {
        row.get("Идентификатор сценария", ""): row
        for row in rows
        if row.get("Идентификатор сценария", "")
    }
    obligations = read_json(obligations_path)
    obligation_by_id = {
        str(item.get("id")): item for item in active_obligations(obligations)
    }
    setup_catalog = execution_setups(obligations)
    derived: set[str] = set()
    for scenario_id in scenario_ids:
        row = rows_by_scenario.get(scenario_id)
        if row is None:
            raise PracticalV09Error(
                f"status triage references absent scenario {scenario_id}"
            )
        obligation = obligation_by_id.get(row.get("Обязательство ФТ", ""))
        context_id = str(row.get("Контекст исполнения", "")).split(" ", 1)[0]
        contexts = {
            str(item.get("id")): item for item in execution_contexts(obligation or {})
        }
        context = contexts.get(context_id)
        if context is None:
            raise PracticalV09Error(
                f"status triage cannot resolve {scenario_id} context {context_id}"
            )
        expected = derived_execution_status(context, setup_catalog)
        if row.get("Статус исполнения", "").strip() != expected:
            raise PracticalV09Error(
                f"status triage requires the matrix to already use derived status "
                f"{expected} for {scenario_id}"
            )
        derived.add(expected)
    return derived


def status_assertion_values(
    *,
    review_finding: dict[str, Any],
    state: dict[str, Any],
    package_root: Path,
) -> tuple[str, set[str]]:
    assertion = review_finding.get("status_assertion")
    if not isinstance(assertion, dict):
        raise PracticalV09Error(
            "status decision requires reviewer finding.status_assertion"
        )
    claimed = assertion.get("required_status")
    scenario_ids = assertion.get("scenario_ids")
    if (
        claimed not in ALLOWED_EXECUTION_STATUSES
        or not isinstance(scenario_ids, list)
        or not scenario_ids
        or not all(isinstance(item, str) and item.startswith("SCN-") for item in scenario_ids)
    ):
        raise PracticalV09Error(
            "status_assertion requires allowed required_status and scenario_ids"
        )
    derived = derived_status_for_scenarios(
        state=state, package_root=package_root, scenario_ids=scenario_ids
    )
    return str(claimed), derived


def validate_rejection(
    *,
    decision: dict[str, Any],
    review_finding: dict[str, Any],
    state: dict[str, Any],
    package_root: Path,
) -> None:
    rejection = decision.get("rejection")
    if isinstance(rejection, dict) and rejection.get("basis") == "source-not-supported":
        raise PracticalV09Error(
            "source-not-supported нельзя автоматически отклонять в controller triage; "
            "зафиксируйте blocker или запросите явное решение по scope"
        )
    if (
        not isinstance(rejection, dict)
        or rejection.get("basis") not in ALLOWED_TRIAGE_REJECTION_BASES
    ):
        raise PracticalV09Error(
            "decisions-file: rejected finding requires rejection.basis"
        )
    basis = rejection["basis"]
    if basis == "execution-status-precedence":
        claimed, derived = status_assertion_values(
            review_finding=review_finding,
            state=state,
            package_root=package_root,
        )
        if claimed in derived:
            raise PracticalV09Error(
                "status rejection is invalid: reviewer asserted a status that "
                "matches the derived prerequisite status"
            )
    else:
        duplicate_of = rejection.get("duplicate_of")
        if not isinstance(duplicate_of, str) or not duplicate_of.strip():
            raise PracticalV09Error(
                "duplicate-finding rejection requires rejection.duplicate_of"
            )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    state_path = args.workflow_state.resolve()
    result_path = args.review_result.resolve()
    state = load_workflow_state(state_path, package_root)
    triage_contract_version = workflow_controller_triage_version(state)
    if triage_contract_version is None:
        raise PracticalV09Error(
            "workflow-state.json does not enable controller triage"
        )
    result, verification = verify_review_result(
        package_root=package_root,
        manifest_path=args.review_manifest.resolve(),
        result_path=result_path,
        review_session_attestation_path=(
            args.review_session_attestation.resolve()
            if args.review_session_attestation is not None
            else None
        ),
    )
    blockers = [item.id for item in verification if item.blocking]
    if blockers:
        raise PracticalV09Error(
            "review result cannot be triaged before integrity issues are fixed: "
            + ", ".join(blockers)
        )
    if result.get("verdict") != "changes-required":
        raise PracticalV09Error("controller triage is only valid for changes-required")
    content = review_content_findings(
        result, triage_contract_version=triage_contract_version
    )
    expected_ids = {str(item.get("id")) for item in content}
    if not expected_ids:
        raise PracticalV09Error(
            "review result has no content blocking findings to triage"
        )
    payload = read_json(args.decisions_file.resolve())
    expected_hash = sha256_file(result_path)
    if payload.get("review_result_sha256") != expected_hash:
        raise PracticalV09Error(
            "decisions-file review_result_sha256 does not match immutable review result"
        )
    decisions = decision_map(payload, expected_ids)
    findings_by_id = {str(item.get("id")): item for item in content}
    for finding_id, decision in decisions.items():
        require_common_decision_fields(decision)
        review_finding = findings_by_id[finding_id]
        if "status_assertion" in review_finding:
            claimed, derived = status_assertion_values(
                review_finding=review_finding,
                state=state,
                package_root=package_root,
            )
            if decision["disposition"] == "accepted" and claimed not in derived:
                raise PracticalV09Error(
                    "accepted status finding conflicts with the derived prerequisite "
                    "status; reject it with execution-status-precedence"
                )
        if decision["disposition"] == "rejected":
            validate_rejection(
                decision=decision,
                review_finding=review_finding,
                state=state,
                package_root=package_root,
            )
    existing = [
        item
        for item in state["review_triage"]
        if isinstance(item, dict)
        and item.get("review_mode") == result["review_mode"]
        and item.get("review_result_sha256") == expected_hash
    ]
    if existing:
        raise PracticalV09Error(
            "controller triage for this immutable review result already exists"
        )
    triage = state["review_triage"]
    assert isinstance(triage, list)
    triage.append(
        {
            "contract_version": triage_contract_version,
            "review_mode": result["review_mode"],
            "review_manifest": relative_to_package(
                package_root, args.review_manifest.resolve()
            ),
            "review_manifest_sha256": sha256_file(args.review_manifest.resolve()),
            "review_result": relative_to_package(package_root, result_path),
            "review_result_sha256": expected_hash,
            "decisions": [decisions[finding_id] for finding_id in sorted(decisions)],
        }
    )
    write_json(state_path, state)
    accepted = sum(
        1 for decision in decisions.values()
        if decision["disposition"] == "accepted"
    )
    print(f"controller triage recorded: accepted={accepted}; rejected={len(decisions) - accepted}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
