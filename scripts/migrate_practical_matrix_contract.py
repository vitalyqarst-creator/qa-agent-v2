"""Perform an explicit, budget-preserving migration of an active v0.9 matrix.

The command never rewrites a matrix or canonical test cases.  It snapshots the
legacy inputs, changes only the workflow control plane, and makes the
subsequent content migration deliberate and reviewable.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    MIGRATABLE_MATRIX_CONTRACT_VERSIONS,
    MATRIX_CONTRACT_VERSION,
    PracticalV09Error,
    SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
    load_workflow_state,
    matrix_contract_version_from_path,
    relative_to_package,
    sha256_file,
    workflow_artifact_path,
    workflow_contract_migration,
    workflow_matrix_contract_version,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate an active practical v0.9 scope matrix contract without resetting review budgets."
    )
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--workflow-state", type=Path, required=True)
    parser.add_argument(
        "--action",
        choices=("plan", "start", "mark-matrix-ready", "complete-tc-sync"),
        default="plan",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        help="Required only with --action start; destination for immutable legacy input copies.",
    )
    parser.add_argument(
        "--explicit-user-authorization",
        action="store_true",
        help="Required only with --action start; confirms that a user authorized the active-scope migration.",
    )
    return parser.parse_args(argv)


def planned_artifacts(state: dict[str, object], package_root: Path) -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for key in ("source_package_manifest", "scope_obligations", "test_design_matrix", "canonical_test_cases"):
        path = workflow_artifact_path(state, package_root, key)
        if path is not None and path.is_file():
            items.append((key, path))
    return items


def render_plan(
    *, state: dict[str, object], package_root: Path, state_path: Path
) -> dict[str, object]:
    matrix_path = workflow_artifact_path(state, package_root, "test_design_matrix", required=True)
    assert matrix_path is not None
    tc_path = workflow_artifact_path(state, package_root, "canonical_test_cases")
    payload = {
        "schema_version": 1,
        "scope_id": state["scope_id"],
        "scope_slug": state["scope_slug"],
        "current_matrix_contract": workflow_matrix_contract_version(state),
        "actual_matrix_contract": matrix_contract_version_from_path(matrix_path),
        "target_matrix_contract": MATRIX_CONTRACT_VERSION,
        "current_phase": state["phase"],
        "review_budgets": {
            "matrix_revision_count": state["matrix_revision_count"],
            "tc_revision_count": state["tc_revision_count"],
        },
        "canonical_tc_sync_required": bool(tc_path and tc_path.is_file()),
        "snapshot_inputs": [
            {
                "role": role,
                "path": relative_to_package(package_root, path),
                "sha256": sha256_file(path),
            }
            for role, path in [("workflow_state", state_path), *planned_artifacts(state, package_root)]
        ],
        "next_action": "Нужно явное разрешение пользователя; затем start создаст snapshot и переведёт scope в matrix-migration.",
    }
    return payload


def require_legacy_matrix(state: dict[str, object], package_root: Path) -> Path:
    if workflow_contract_migration(state) is not None:
        raise PracticalV09Error("workflow-state.json: contract migration already exists")
    declared_contract = workflow_matrix_contract_version(state)
    if declared_contract not in MIGRATABLE_MATRIX_CONTRACT_VERSIONS:
        raise PracticalV09Error(
            "Contract migration can start only from a supported legacy matrix contract"
        )
    matrix_path = workflow_artifact_path(state, package_root, "test_design_matrix", required=True)
    assert matrix_path is not None
    if not matrix_path.is_file():
        raise PracticalV09Error("Contract migration requires an existing legacy matrix")
    if matrix_contract_version_from_path(matrix_path) != declared_contract:
        raise PracticalV09Error(
            "Contract migration requires a matrix whose schema matches the declared legacy contract"
        )
    if state["phase"] in {"accepted", "blocked"}:
        raise PracticalV09Error("Contract migration is allowed only for an active non-terminal scope")
    return matrix_path


def start_migration(
    *, state: dict[str, object], package_root: Path, state_path: Path, snapshot_dir: Path
) -> None:
    matrix_path = require_legacy_matrix(state, package_root)
    from_matrix_contract = workflow_matrix_contract_version(state)
    if snapshot_dir.exists():
        raise PracticalV09Error(f"Snapshot destination already exists: {snapshot_dir}")
    try:
        snapshot_dir.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error("snapshot-dir must be inside the FT package root") from exc
    snapshot_dir.mkdir(parents=True)
    inputs = [("workflow-state.json", state_path), ("test-design-matrix.md", matrix_path)]
    tc_path = workflow_artifact_path(state, package_root, "canonical_test_cases")
    if tc_path is not None and tc_path.is_file():
        inputs.append(("canonical-test-cases.md", tc_path))
    copied: list[dict[str, str]] = []
    for snapshot_name, source in inputs:
        target = snapshot_dir / snapshot_name
        shutil.copyfile(source, target)
        copied.append(
            {
                "source_path": relative_to_package(package_root, source),
                "snapshot_path": relative_to_package(package_root, target),
                "sha256": sha256_file(source),
            }
        )
    manifest_path = snapshot_dir / "migration-manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "scope_id": state["scope_id"],
            "scope_slug": state["scope_slug"],
            "from_matrix_contract": from_matrix_contract,
            "to_matrix_contract": MATRIX_CONTRACT_VERSION,
            "from_scenario_consolidation_contract": state["contract_versions"].get(
                "scenario_consolidation"
            ),
            "to_scenario_consolidation_contract": (
                SCENARIO_CONSOLIDATION_CONTRACT_VERSION
                if state["contract_versions"].get("scenario_consolidation") is not None
                else None
            ),
            "authorization": "explicit-user",
            "review_budgets_before_migration": {
                "matrix_revision_count": state["matrix_revision_count"],
                "tc_revision_count": state["tc_revision_count"],
            },
            "inputs": copied,
        },
    )
    versions = state["contract_versions"]
    assert isinstance(versions, dict)
    versions["matrix"] = MATRIX_CONTRACT_VERSION
    previous_consolidation_contract = versions.get("scenario_consolidation")
    if previous_consolidation_contract is not None:
        versions["scenario_consolidation"] = SCENARIO_CONSOLIDATION_CONTRACT_VERSION
    state["contract_migration"] = {
        "status": "active",
        "from_matrix_contract": from_matrix_contract,
        "to_matrix_contract": MATRIX_CONTRACT_VERSION,
        "authorization": "explicit-user",
        "snapshot_manifest": relative_to_package(package_root, manifest_path),
        "canonical_tc_sync_required": bool(tc_path and tc_path.is_file()),
        "review_budgets_before_migration": {
            "matrix_revision_count": state["matrix_revision_count"],
            "tc_revision_count": state["tc_revision_count"],
        },
    }
    if previous_consolidation_contract is not None:
        state["contract_migration"]["from_scenario_consolidation_contract"] = (
            previous_consolidation_contract
        )
        state["contract_migration"]["to_scenario_consolidation_contract"] = (
            SCENARIO_CONSOLIDATION_CONTRACT_VERSION
        )
    state["phase"] = "matrix-migration"
    state["next_action"] = (
        f"Перевести test-design-matrix.md из {from_matrix_contract} в {MATRIX_CONTRACT_VERSION}; "
        "не изменять canonical TC до matrix review."
    )
    state.setdefault("decision_notes", []).append(
        f"Явная contract migration {from_matrix_contract}→{MATRIX_CONTRACT_VERSION}: "
        "старые matrix/TC сохранены в snapshot; бюджеты review не сброшены."
    )
    write_json(state_path, state)


def mark_matrix_ready(*, state: dict[str, object], package_root: Path, state_path: Path) -> None:
    migration = workflow_contract_migration(state)
    if migration is None or migration["status"] != "active":
        raise PracticalV09Error("mark-matrix-ready requires an active contract migration")
    matrix_path = workflow_artifact_path(state, package_root, "test_design_matrix", required=True)
    assert matrix_path is not None
    if matrix_contract_version_from_path(matrix_path) != MATRIX_CONTRACT_VERSION:
        raise PracticalV09Error(
            f"Matrix is not yet materialized in {MATRIX_CONTRACT_VERSION} schema"
        )
    migration["status"] = "matrix-ready"
    state["phase"] = "matrix"
    state["next_action"] = "Провести scoped validation migrated matrix и обязательное независимое matrix review"
    write_json(state_path, state)


def complete_tc_sync(*, state: dict[str, object], package_root: Path, state_path: Path) -> None:
    migration = workflow_contract_migration(state)
    if migration is None or migration["status"] not in {"matrix-accepted", "completed"}:
        raise PracticalV09Error(
            "complete-tc-sync requires a matrix-accepted or previously completed contract migration"
        )
    tc_path = workflow_artifact_path(state, package_root, "canonical_test_cases", required=True)
    assert tc_path is not None
    if not tc_path.is_file():
        raise PracticalV09Error("Canonical test cases are required before completing TC synchronization")
    migration["status"] = "completed"
    # The required TC synchronization has just completed.  Keeping this gate
    # enabled would make every subsequent scoped validation fail before it can
    # validate the synchronized canonical test cases.  Allowing a completed
    # state makes this transition safe to retry when an older tool version
    # recorded status=completed without clearing the gate.
    migration["canonical_tc_sync_required"] = False
    state["phase"] = "review"
    state["next_action"] = "Провести scoped validation и независимое final TC review"
    state["final_verdict"] = "not-finalized"
    write_json(state_path, state)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    state_path = args.workflow_state.resolve()
    state = load_workflow_state(state_path, package_root)
    if args.action == "plan":
        print(json.dumps(render_plan(state=state, package_root=package_root, state_path=state_path), ensure_ascii=False, indent=2))
        return 0
    if args.action == "start":
        if not args.explicit_user_authorization:
            raise PracticalV09Error("start requires --explicit-user-authorization")
        if args.snapshot_dir is None:
            raise PracticalV09Error("start requires --snapshot-dir")
        start_migration(
            state=state,
            package_root=package_root,
            state_path=state_path,
            snapshot_dir=args.snapshot_dir.resolve(),
        )
        print("contract migration started")
        return 0
    if args.snapshot_dir is not None or args.explicit_user_authorization:
        raise PracticalV09Error("snapshot-dir and explicit-user-authorization are valid only with --action start")
    if args.action == "mark-matrix-ready":
        mark_matrix_ready(state=state, package_root=package_root, state_path=state_path)
    else:
        complete_tc_sync(state=state, package_root=package_root, state_path=state_path)
    print(args.action)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
