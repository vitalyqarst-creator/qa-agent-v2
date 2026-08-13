"""Verify a compact v0.9 review result and update the single workflow state."""

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
    load_workflow_state,
    relative_to_package,
    review_content_findings,
    sha256_file,
    triage_record_for_review,
    validate_review_triage_integrity,
    verify_review_result,
    workflow_controller_triage_enabled,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finalize a separate-session practical v0.9 review.")
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--workflow-state", type=Path, required=True)
    parser.add_argument("--review-manifest", type=Path, required=True)
    parser.add_argument("--review-result", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    state_path = args.workflow_state.resolve()
    state = load_workflow_state(state_path, package_root)
    result, findings = verify_review_result(
        package_root=package_root,
        manifest_path=args.review_manifest.resolve(),
        result_path=args.review_result.resolve(),
    )
    blocking = [item for item in findings if item.blocking]
    if blocking:
        rendered = ", ".join(item.id for item in blocking)
        raise PracticalV09Error("Review result cannot be finalized: " + rendered)
    review_mode = str(result.get("review_mode") or "")
    if review_mode not in {"matrix", "test-cases"}:
        raise PracticalV09Error("review-result.json has unsupported review_mode")
    effective_verdict = str(result["verdict"])
    content_findings = review_content_findings(result)
    if result["verdict"] == "changes-required" and content_findings:
        if workflow_controller_triage_enabled(state):
            triage_issues = [
                item.id
                for item in validate_review_triage_integrity(state, package_root)
                if item.blocking
            ]
            if triage_issues:
                raise PracticalV09Error(
                    "Controller triage is invalid: " + ", ".join(triage_issues)
                )
            triage = triage_record_for_review(
                state,
                review_mode=review_mode,
                review_result_path=args.review_result.resolve(),
            )
            assert triage is not None
            decisions = {
                str(item.get("finding_id")): item
                for item in triage["decisions"]
                if isinstance(item, dict)
            }
            accepted_content = [
                item for item in content_findings
                if decisions[str(item.get("id"))].get("disposition") == "accepted"
            ]
            if not accepted_content:
                effective_verdict = "approved"
            else:
                content_findings = accepted_content
    review_entry = {
        "mode": review_mode,
        "verdict": result["verdict"],
        "manifest": relative_to_package(package_root, args.review_manifest.resolve()),
        "result": relative_to_package(package_root, args.review_result.resolve()),
        "result_sha256": sha256_file(args.review_result.resolve()),
    }
    if effective_verdict != result["verdict"]:
        review_entry["effective_verdict"] = effective_verdict
    reviews = state.setdefault("reviews", [])
    if not isinstance(reviews, list):
        raise PracticalV09Error("workflow-state.json: reviews must be an array")
    reviews.append(review_entry)
    if effective_verdict == "approved":
        migration = state.get("contract_migration")
        if (
            review_mode == "matrix"
            and isinstance(migration, dict)
            and migration.get("status") == "matrix-ready"
        ):
            migration["status"] = "matrix-accepted"
            state["phase"] = "test-cases"
            state["next_action"] = (
                "Синхронизировать канонические ТК с матрицей после миграции, затем завершить миграцию контракта"
            )
            state["final_verdict"] = "not-finalized"
        else:
            state["phase"] = "test-cases" if review_mode == "matrix" else "accepted"
            state["next_action"] = "Написать тест-кейсы" if review_mode == "matrix" else "Завершить scope"
            state["final_verdict"] = "not-finalized" if review_mode == "matrix" else "approved"
    elif result["verdict"] == "changes-required":
        if review_mode == "test-cases":
            state["final_verdict"] = "changes-required"
        if not content_findings:
            state["phase"] = "matrix" if review_mode == "matrix" else "test-cases"
            state["next_action"] = (
                "Исправить неблокирующие замечания review без расходования "
                "содержательной доработки"
            )
        else:
            revision_key = "matrix_revision_count" if review_mode == "matrix" else "tc_revision_count"
            if state[revision_key] >= 1:
                state["phase"] = "blocked"
                stage_label = "матрицы" if review_mode == "matrix" else "тест-кейсов"
                state["next_action"] = (
                    f"Лимит одной содержательной доработки {stage_label} исчерпан; "
                    "требуется решение по scope"
                )
            else:
                state[revision_key] += 1
                state["phase"] = "matrix" if review_mode == "matrix" else "test-cases"
                state["next_action"] = "Выполнить одну целевую доработку по findings reviewer"
    else:
        state["phase"] = "blocked"
        state["next_action"] = "Получить внешнее уточнение по blocker reviewer"
        state["final_verdict"] = "blocked-input"
    write_json(state_path, state)
    print(state["next_action"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
