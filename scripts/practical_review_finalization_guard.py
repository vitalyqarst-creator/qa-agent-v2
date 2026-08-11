"""Verify an independent practical review before controller-owned finalization.

The reviewer is deliberately read-only with respect to ``workflow-state.yaml``
and ``practical-stage-summary.md``.  This guard consumes the launch receipt and
the review outputs after the separate task completes.  It fails closed if the
reviewer changed controller-owned artifacts, then emits a small hash-bound
packet which the controller can use for its one deterministic state update.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import practical_review_preflight as review_preflight  # noqa: E402


REVIEW_MODES = {"matrix_review", "tc_review"}
EXECUTION_SURFACES = {"codex-thread"}
TASK_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


@dataclass(frozen=True)
class FinalizationCheck:
    id: str
    status: str
    details: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def resolve_inside_package(value: Path, ft_package_root: Path) -> Path | None:
    candidate = value.resolve() if value.is_absolute() else (ft_package_root / value).resolve()
    if not candidate.is_file() or not is_within(candidate, ft_package_root):
        return None
    return candidate


def markdown_field(content: str, field: str) -> str:
    escaped = re.escape(field)
    table_match = re.search(
        rf"(?mi)^\|\s*{escaped}\s*\|\s*`?([^`|\n]+)`?\s*\|",
        content,
    )
    if table_match:
        return table_match.group(1).strip()
    labelled_match = re.search(
        rf"(?mi)^\s*(?:\*\*)?{escaped}\s*:(?:\*\*)?\s*`?([^`\n]+)`?\s*$",
        content,
    )
    return labelled_match.group(1).strip() if labelled_match else ""


def normalized_verdict(content: str, review_mode: str) -> str:
    value = markdown_field(content, "verdict") or markdown_field(content, "Вердикт")
    if not value:
        match = re.search(r"(?mi)^\s*(?:\*\*)?(?:verdict|вердикт)(?:\*\*)?\s*[:—-]\s*`?([^`\n]+)`?", content)
        value = match.group(1).strip() if match else ""
    if not value:
        heading_match = re.search(
            r"(?mi)^#{1,6}\s*(?:verdict|вердикт)\s*$\s*^\s*`?([^`\n]+)`?\s*$",
            content,
        )
        value = heading_match.group(1).strip() if heading_match else ""
    normalized = value.casefold().strip().strip("`")
    if review_mode == "matrix_review":
        return normalized if normalized in {
            "matrix-accepted",
            "matrix-changes-required",
            "matrix-rejected",
        } else ""
    if normalized in {"tc-accepted", "accepted"}:
        return "tc-accepted"
    if normalized in {"tc-changes-required", "changes-required"}:
        return "tc-changes-required"
    return ""


def review_submission_issues(
    *,
    review_content: str,
    independence_content: str,
    descriptors: list[review_preflight.ScopeDescriptor],
    review_mode: str,
) -> list[str]:
    """Validate reviewer-owned metadata before controller finalization.

    The separate reviewer runs this guard without ``--output`` as a read-only
    self-check.  That makes malformed reviewer metadata fail in the reviewer
    session instead of forcing controller-side repair after a verdict.
    """

    issues: list[str] = []
    if not re.search(r"(?mi)^##\s*(?:verdict|вердикт)\s*$", review_content):
        issues.append("review artifact lacks canonical ## Verdict heading")

    expected_scope_slugs = {descriptor.scope_slug for descriptor in descriptors}
    scope_slug = markdown_field(review_content, "scope_slug")
    if not scope_slug:
        issues.append("review artifact lacks scope_slug")
    elif len(expected_scope_slugs) == 1 and scope_slug != next(iter(expected_scope_slugs)):
        issues.append("review artifact scope_slug differs from selected scope")
    elif len(expected_scope_slugs) > 1 and not expected_scope_slugs.issubset(
        {item.strip() for item in re.split(r"[,;]", scope_slug) if item.strip()}
    ):
        issues.append("review artifact scope_slug does not cover every selected scope")

    if markdown_field(review_content, "review_mode") != review_mode:
        issues.append("review artifact review_mode differs from selected mode")

    expected_rounds: set[str] = set()
    for descriptor in descriptors:
        try:
            state = review_preflight.artifact_validator.parse_workflow_state(descriptor.workflow_path)
        except (OSError, UnicodeDecodeError, ValueError):
            issues.append(f"scope {descriptor.scope_id}: cannot read workflow round for review contract")
            continue
        current_round = str(state.get("current_round") or "").strip()
        if current_round:
            expected_rounds.add(current_round)
    review_round = markdown_field(review_content, "review_round")
    if not review_round:
        issues.append("review artifact lacks review_round")
    elif expected_rounds and review_round not in expected_rounds:
        issues.append("review artifact review_round differs from current workflow round")

    required_independence = {
        "reviewer_dispatch_receipt": None,
        "reviewer_was_separate_session": "yes",
        "reviewer_input_excluded_writer_transcript": "yes",
        "reviewer_input_excluded_writer_private_reasoning": "yes",
        "reviewer_modified_test_cases": "no",
        "independent_signoff_claim_allowed": "yes",
        "review_mode": review_mode,
        "review_round": review_round,
    }
    for field, expected in required_independence.items():
        actual = markdown_field(independence_content, field)
        if expected is None:
            if not actual:
                issues.append(f"review independence artifact lacks {field}")
        elif actual.casefold() != expected.casefold():
            issues.append(f"review independence artifact {field} differs from review contract")
    return issues


def is_hash_proven_matrix_revalidation(
    descriptors: list[review_preflight.ScopeDescriptor],
    *,
    ft_package_root: Path,
    review_mode: str,
) -> bool:
    """Return whether this matrix review revalidates a preserved TC suite."""

    if review_mode != "matrix_review" or not descriptors:
        return False
    for descriptor in descriptors:
        try:
            state = review_preflight.artifact_validator.parse_workflow_state(descriptor.workflow_path)
        except (OSError, UnicodeDecodeError, ValueError):
            return False
        try:
            current_round = int(state.get("current_round") or 0)
        except (TypeError, ValueError):
            return False
        canonical_exists = False
        for candidate in descriptor.canonical_test_case_paths:
            candidate_path = Path(candidate)
            resolved_candidate = (
                candidate_path.resolve()
                if candidate_path.is_absolute()
                else (ft_package_root / candidate_path).resolve()
            )
            if resolved_candidate.is_file() and is_within(resolved_candidate, ft_package_root):
                canonical_exists = True
                break
        if not (
            canonical_exists
            and str(state.get("matrix_review_status") or "") == "invalidated"
            and str(state.get("matrix_revalidation_reason") or "")
            == "reviewed-matrix-hash-mismatch"
            and str(state.get("stage_status") or "") == "ready-for-review"
            and str(state.get("next_skill") or "") == "ft-test-case-reviewer"
            and str(state.get("review_mode") or "") == "matrix_review"
            and current_round == 2
        ):
            return False
    return True


def next_controller_transition(
    review_mode: str,
    verdict: str,
    *,
    matrix_revalidation_after_canonical_tcs: bool = False,
) -> str:
    if (
        matrix_revalidation_after_canonical_tcs
        and review_mode == "matrix_review"
        and verdict == "matrix-accepted"
    ):
        return "tc-review required"
    transitions = {
        ("matrix_review", "matrix-accepted"): "writer allowed",
        ("matrix_review", "matrix-changes-required"): "writer matrix-repair required",
        ("matrix_review", "matrix-rejected"): "writer blocked",
        ("tc_review", "tc-accepted"): "accepted-local-publication-pending",
        ("tc_review", "tc-changes-required"): "writer revision required",
    }
    return transitions.get((review_mode, verdict), "blocked-input")


def build_finalization_packet(
    *,
    repo_root: Path,
    ft_package_root: Path,
    summary_path: Path,
    scope_ids: list[str],
    review_mode: str,
    launch_receipt: Path,
    dispatch_receipt: Path,
    review_artifact: Path,
    independence_artifact: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ft_package_root = ft_package_root.resolve()
    summary_path = summary_path.resolve()
    checks: list[FinalizationCheck] = []
    blockers: list[str] = []

    try:
        receipt = json.loads(launch_receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        receipt = {}
        blockers.append(f"cannot read review launch receipt: {exc}")

    if receipt.get("allowed") is not True:
        blockers.append("review launch receipt is not allowed")
    if str(receipt.get("repo_root") or "") and not review_preflight.paths_equal(
        str(receipt.get("repo_root")), repo_root
    ):
        blockers.append("review launch receipt repo root differs from finalization repo root")
    if str(receipt.get("ft_package_root") or "") and not review_preflight.paths_equal(
        str(receipt.get("ft_package_root")), ft_package_root
    ):
        blockers.append("review launch receipt FT package root differs from finalization FT package root")
    if receipt.get("review_mode") != review_mode:
        blockers.append("review launch receipt mode differs from requested mode")
    if receipt.get("scope_ids") != scope_ids:
        blockers.append("review launch receipt scope ids differ from requested scope ids")

    # The controller may not finalize a verdict that was launched from a
    # different version-gated checkout.  The post-finalization gate also
    # checks this, but doing it here prevents a stale verdict from causing the
    # controller's otherwise permitted state/summary update in the first
    # place.
    receipt_branch = str(receipt.get("code_branch") or "").strip()
    receipt_commit = str(receipt.get("code_commit") or "").casefold().strip()
    branch_rc, current_branch, branch_error = review_preflight.run_git(
        repo_root, "branch", "--show-current"
    )
    commit_rc, current_commit, commit_error = review_preflight.run_git(
        repo_root, "rev-parse", "HEAD"
    )
    current_branch = current_branch.strip()
    current_commit = current_commit.casefold().strip()
    code_version_issues: list[str] = []
    if not receipt_branch or not receipt_commit:
        code_version_issues.append("review launch receipt lacks code branch or exact commit")
    elif branch_rc != 0 or commit_rc != 0:
        code_version_issues.append(
            "cannot determine current code version during review finalization: "
            f"branch={branch_error or '<missing>'}; commit={commit_error or '<missing>'}"
        )
    elif current_branch != receipt_branch or current_commit != receipt_commit:
        code_version_issues.append(
            "review launch receipt code version differs from current checkout: "
            f"launch branch={receipt_branch}, commit={receipt_commit}; "
            f"current branch={current_branch or '<missing>'}, "
            f"commit={current_commit or '<missing>'}"
        )
    blockers.extend(code_version_issues)
    checks.append(
        FinalizationCheck(
            "pinned-code-version",
            "pass" if not code_version_issues else "fail",
            (
                f"launch_branch={receipt_branch or '<missing>'}; "
                f"current_branch={current_branch or branch_error or '<missing>'}; "
                f"launch_commit={receipt_commit or '<missing>'}; "
                f"current_commit={current_commit or commit_error or '<missing>'}"
            ),
        )
    )

    resolved_dispatch = resolve_inside_package(dispatch_receipt, ft_package_root)
    dispatch: dict[str, Any] = {}
    if resolved_dispatch is None:
        blockers.append("review dispatch receipt is missing or outside FT package root")
    else:
        try:
            dispatch = json.loads(resolved_dispatch.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            blockers.append(f"cannot read review dispatch receipt: {exc}")
    if dispatch:
        dispatch_launch = Path(str(dispatch.get("launch_receipt") or ""))
        if not dispatch_launch or not review_preflight.paths_equal(dispatch_launch, launch_receipt):
            blockers.append("review dispatch receipt does not bind the selected launch receipt")
        if dispatch.get("launch_receipt_sha256") != sha256_file(launch_receipt):
            blockers.append("review dispatch receipt launch hash differs from selected launch receipt")
        if dispatch.get("allowed") is not True or dispatch.get("status") != "dispatched":
            blockers.append("review dispatch receipt is not dispatched")

    expected_hashes = receipt.get("controller_artifact_hashes")
    if not isinstance(expected_hashes, dict):
        blockers.append("review launch receipt lacks controller artifact hashes")
        expected_hashes = {}
    summary_hash = str(expected_hashes.get("summary_sha256") or "")
    current_summary_hash = sha256_file(summary_path) if summary_path.is_file() else ""
    if not summary_hash or summary_hash != current_summary_hash:
        blockers.append("controller practical-stage-summary changed during independent review")

    descriptors, descriptor_issues = review_preflight.scope_descriptors(ft_package_root, scope_ids)
    blockers.extend(descriptor_issues)
    matrix_revalidation_after_canonical_tcs = is_hash_proven_matrix_revalidation(
        descriptors,
        ft_package_root=ft_package_root,
        review_mode=review_mode,
    )
    review_subjects: dict[str, dict[str, str]] = {}
    if not descriptor_issues:
        review_subjects, review_subject_issues = review_preflight.verify_review_subject_artifacts(
            receipt,
            descriptors=descriptors,
            ft_package_root=ft_package_root,
            review_mode=review_mode,
        )
        blockers.extend(review_subject_issues)
    else:
        review_subject_issues = ["scope descriptors are unavailable"]
    checks.append(
        FinalizationCheck(
            "review-subject-hash",
            "pass" if not review_subject_issues else "fail",
            f"subjects={len(review_subjects)}; issues={len(review_subject_issues)}",
        )
    )
    snapshot_targets: dict[str, dict[str, Any]] = {}
    if not descriptor_issues:
        snapshot_targets, snapshot_issues = review_preflight.verify_controller_snapshot(
            receipt,
            ft_package_root=ft_package_root,
            summary_path=summary_path,
            descriptors=descriptors,
        )
        blockers.extend(snapshot_issues)
    checks.append(
        FinalizationCheck(
            "controller-recovery-snapshot",
            "pass"
            if not any("controller recovery snapshot" in item for item in blockers)
            else "fail",
            f"targets={len(snapshot_targets)}",
        )
    )
    workflow_hashes = expected_hashes.get("workflow_state_sha256_by_scope")
    if not isinstance(workflow_hashes, dict):
        blockers.append("review launch receipt lacks workflow-state hashes")
        workflow_hashes = {}
    for descriptor in descriptors:
        expected = str(workflow_hashes.get(descriptor.scope_id) or "")
        actual = sha256_file(descriptor.workflow_path)
        if not expected or expected != actual:
            blockers.append(
                f"scope {descriptor.scope_id}: controller workflow-state changed during independent review"
            )
    checks.append(
        FinalizationCheck(
            "controller-ownership",
            "pass" if not any("controller" in item for item in blockers) else "fail",
            f"scopes={', '.join(scope_ids)}",
        )
    )

    resolved_review = resolve_inside_package(review_artifact, ft_package_root)
    resolved_independence = resolve_inside_package(independence_artifact, ft_package_root)
    if resolved_review is None:
        blockers.append("review artifact is missing or outside FT package root")
    if resolved_independence is None:
        blockers.append("review independence artifact is missing or outside FT package root")
    review_content = resolved_review.read_text(encoding="utf-8") if resolved_review else ""
    independence_content = resolved_independence.read_text(encoding="utf-8") if resolved_independence else ""
    verdict = normalized_verdict(review_content, review_mode)
    if not verdict:
        blockers.append("review artifact lacks a canonical verdict for the selected review mode")
    submission_issues = review_submission_issues(
        review_content=review_content,
        independence_content=independence_content,
        descriptors=descriptors,
        review_mode=review_mode,
    )
    blockers.extend(submission_issues)
    checks.append(
        FinalizationCheck(
            "review-submission-contract",
            "pass" if not submission_issues else "fail",
            f"issues={len(submission_issues)}",
        )
    )

    reviewer_surface = str(dispatch.get("reviewer_execution_surface") or "").strip()
    reviewer_task = str(dispatch.get("reviewer_task_or_session") or "").strip()
    reviewer_thread = str(dispatch.get("reviewer_thread_url_or_id") or "").strip()
    controller_task = str(dispatch.get("controller_task_or_session") or "").strip()
    controller_surface = str(dispatch.get("controller_execution_surface") or "").strip()
    if dispatch.get("schema_version") != 3:
        blockers.append("review dispatch receipt must use controller-provenance schema v3")
    if dispatch.get("controller_identity_verified") is not True:
        blockers.append("review dispatch receipt does not verify controller session provenance")
    if not TASK_ID_RE.fullmatch(controller_task):
        blockers.append("review dispatch receipt lacks a durable controller task/session id")
    if controller_surface not in EXECUTION_SURFACES:
        blockers.append("review dispatch receipt lacks a controller Codex session execution surface")
    if reviewer_surface not in EXECUTION_SURFACES:
        blockers.append("review dispatch receipt lacks a separate Codex session execution surface")
    if not TASK_ID_RE.fullmatch(reviewer_task):
        blockers.append("review dispatch receipt lacks a durable reviewer task/session id")
    if controller_task and reviewer_task and controller_task.casefold() == reviewer_task.casefold():
        blockers.append("controller task/session id must differ from reviewer task/session id")
    if reviewer_task and reviewer_task not in reviewer_thread:
        blockers.append("review dispatch receipt thread id does not match reviewer task/session id")
    for descriptor in descriptors:
        try:
            state = review_preflight.artifact_validator.parse_workflow_state(
                descriptor.workflow_path
            )
        except (OSError, UnicodeDecodeError, ValueError):
            blockers.append(
                f"scope {descriptor.scope_id}: cannot verify controller task/session provenance"
            )
            continue
        workflow_controller = str(state.get("controller_task_or_session") or "").strip()
        if workflow_controller != controller_task:
            blockers.append(
                f"scope {descriptor.scope_id}: workflow controller_task_or_session differs from dispatch receipt"
            )
    for field, actual in (
        ("reviewer_task_or_session", markdown_field(independence_content, "reviewer_task_or_session")),
        ("reviewer_execution_surface", markdown_field(independence_content, "reviewer_execution_surface")),
        ("reviewer_thread_url_or_id", markdown_field(independence_content, "reviewer_thread_url_or_id")),
    ):
        if actual and actual != {"reviewer_task_or_session": reviewer_task, "reviewer_execution_surface": reviewer_surface, "reviewer_thread_url_or_id": reviewer_thread}[field]:
            blockers.append(f"review independence artifact {field} differs from controller dispatch receipt")
    if markdown_field(independence_content, "reviewer_was_separate_session").casefold() != "yes":
        blockers.append("review independence artifact does not confirm a separate reviewer session")
    if markdown_field(independence_content, "reviewer_modified_test_cases").casefold() != "no":
        blockers.append("review independence artifact does not confirm read-only test-case review")
    checks.append(
        FinalizationCheck(
            "reviewer-independence",
            "pass" if not any("reviewer" in item for item in blockers) else "fail",
            (
                f"controller={controller_task or '<missing>'}; "
                f"reviewer={reviewer_task or '<missing>'}; surface={reviewer_surface or '<missing>'}"
            ),
        )
    )

    return {
        "schema_version": 1,
        "status": "ready-for-controller-finalization" if not blockers else "blocked",
        "allowed": not blockers,
        "review_mode": review_mode,
        "scope_ids": scope_ids,
        "repo_root": repo_root.as_posix(),
        "ft_package_root": ft_package_root.as_posix(),
        "code_branch": current_branch if branch_rc == 0 else "",
        "code_commit": current_commit if commit_rc == 0 else "",
        "launch_receipt": launch_receipt.resolve().as_posix(),
        "launch_receipt_sha256": sha256_file(launch_receipt) if launch_receipt.is_file() else "",
        "dispatch_receipt": resolved_dispatch.as_posix() if resolved_dispatch else "",
        "dispatch_receipt_sha256": sha256_file(resolved_dispatch) if resolved_dispatch else "",
        "controller_artifact_snapshot": receipt.get("controller_artifact_snapshot", {}),
        "review_subject_artifacts_by_scope": review_subjects,
        "review_artifact": resolved_review.as_posix() if resolved_review else "",
        "review_artifact_sha256": sha256_file(resolved_review) if resolved_review else "",
        "independence_artifact": resolved_independence.as_posix() if resolved_independence else "",
        "independence_artifact_sha256": sha256_file(resolved_independence) if resolved_independence else "",
        "verdict": verdict,
        "reviewer_task_or_session": reviewer_task,
        "reviewer_execution_surface": reviewer_surface,
        "controller_task_or_session": controller_task,
        "controller_execution_surface": controller_surface,
        "recovery_context": (
            "matrix-revalidation-after-canonical-tcs"
            if matrix_revalidation_after_canonical_tcs
            else "not-applicable"
        ),
        "next_controller_transition": next_controller_transition(
            review_mode,
            verdict,
            matrix_revalidation_after_canonical_tcs=matrix_revalidation_after_canonical_tcs,
        ),
        "checks": [asdict(check) for check in checks],
        "blocking_reasons": blockers,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify independent practical review outputs before controller finalization."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--scope-id", action="append", required=True)
    parser.add_argument("--review-mode", choices=sorted(REVIEW_MODES), required=True)
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument("--dispatch-receipt", type=Path, required=True)
    parser.add_argument("--review-artifact", type=Path, required=True)
    parser.add_argument("--independence-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scope_ids = list(dict.fromkeys(args.scope_id))
    result = build_finalization_packet(
        repo_root=args.repo_root,
        ft_package_root=args.ft_package_root,
        summary_path=args.summary,
        scope_ids=scope_ids,
        review_mode=args.review_mode,
        launch_receipt=args.launch_receipt.resolve(),
        dispatch_receipt=args.dispatch_receipt,
        review_artifact=args.review_artifact,
        independence_artifact=args.independence_artifact,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
