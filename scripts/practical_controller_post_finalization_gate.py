"""Fail closed before a practical controller routes accepted review to writer.

This is intentionally controller-owned.  It is run after the controller has
applied the single state update allowed by ``practical_review_finalization_guard``
and refreshed the practical summary.  It makes four decisions deterministic:

* accepted review must originate from the same version-gated checkout;
* current-scope/package validation errors block the next writer stage;
* a resolved gap cannot remain listed as active source-parity debt;
* the emitted packet binds the now-current summary and workflows for the next
  controller prompt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import practical_review_preflight as review_preflight  # noqa: E402


GAP_ID_RE = re.compile(r"\bGAP-[A-Z0-9-]+\b", re.IGNORECASE)
RESOLVED_MARKER_RE = re.compile(r"\b(?:resolved|closed|removed)\b|закрыт|удален|удалён", re.IGNORECASE)
ACTIVE_GAP_MARKER_RE = re.compile(
    r"\b(?:open gaps?|semantic mismatches requiring gaps?)\b|открыт(?:ые|ая)?\s+(?:gap|gap[- ]|пробел)",
    re.IGNORECASE,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_scope_artifact(value: Any, workflow_path: Path, ft_package_root: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return review_preflight.artifact_validator.resolve_artifact_path(
        value,
        workflow_path,
        ft_package_root,
        ft_package_root,
    )


def gap_ids_on_marked_lines(path: Path, marker: re.Pattern[str]) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return set()
    return {
        gap_id.upper()
        for line in lines
        if marker.search(line)
        for gap_id in GAP_ID_RE.findall(line)
    }


def link_allowed_gate_output(
    *,
    ft_package_root: Path,
    scope_ids: list[str],
    output_path: Path,
) -> None:
    """Link an allowed controller packet atomically enough for the next stage.

    The packet is controller-owned.  Making the command perform this narrow
    alias update avoids a human/controller forgetting the final step after a
    successful gate and leaving a stale R1 packet active.
    """

    package_root = ft_package_root.resolve()
    output_path = output_path.resolve()
    try:
        output_relative = output_path.relative_to(package_root).as_posix()
    except ValueError as exc:
        raise ValueError("controller post-finalization output must be inside FT package root") from exc
    descriptors, issues = review_preflight.scope_descriptors(package_root, scope_ids)
    if issues:
        raise ValueError("cannot link controller gate: " + "; ".join(issues))
    originals: dict[Path, str] = {}
    try:
        for descriptor in descriptors:
            originals[descriptor.workflow_path] = descriptor.workflow_path.read_text(
                encoding="utf-8"
            )
            state = review_preflight.artifact_validator.parse_workflow_state(
                descriptor.workflow_path
            )
            latest = state.get("latest_artifacts")
            latest = dict(latest) if isinstance(latest, dict) else {}
            latest["controller_post_finalization_gate"] = output_relative
            state["latest_artifacts"] = latest
            descriptor.workflow_path.write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
    except Exception:
        for path, content in originals.items():
            path.write_text(content, encoding="utf-8")
        raise


def build_post_finalization_gate(
    *,
    repo_root: Path,
    ft_package_root: Path,
    summary_path: Path,
    scope_ids: list[str],
    launch_receipt: Path,
    finalization_packet: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ft_package_root = ft_package_root.resolve()
    summary_path = summary_path.resolve()
    blockers: list[str] = []
    checks: list[dict[str, str]] = []

    try:
        launch = json.loads(launch_receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        launch = {}
        blockers.append(f"cannot read review launch receipt: {exc}")
    try:
        finalization = json.loads(finalization_packet.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        finalization = {}
        blockers.append(f"cannot read review finalization packet: {exc}")

    if finalization.get("allowed") is not True:
        blockers.append("review finalization packet is not allowed")
    if finalization.get("scope_ids") != scope_ids:
        blockers.append("review finalization packet scope ids differ from requested scope ids")
    if not review_preflight.paths_equal(
        str(finalization.get("launch_receipt") or ""), launch_receipt
    ):
        blockers.append("review finalization packet does not bind the selected launch receipt")

    branch_rc, current_branch, branch_error = review_preflight.run_git(
        repo_root, "branch", "--show-current"
    )
    commit_rc, current_commit, git_error = review_preflight.run_git(repo_root, "rev-parse", "HEAD")
    current_branch = current_branch.strip()
    current_commit = current_commit.casefold()
    launch_branch = str(launch.get("code_branch") or "").strip()
    launch_commit = str(launch.get("code_commit") or "").casefold().strip()
    if (
        branch_rc != 0
        or commit_rc != 0
        or not current_branch
        or not launch_branch
        or not current_commit
        or not launch_commit
        or current_branch != launch_branch
        or current_commit != launch_commit
    ):
        blockers.append(
            "pinned-code-version-changed: rematerialize and launch a fresh independent review"
        )
    checks.append(
        {
            "id": "pinned-code-version",
            "status": "pass"
            if current_branch
            and launch_branch
            and current_commit
            and launch_commit
            and current_branch == launch_branch
            and current_commit == launch_commit
            else "fail",
            "details": (
                f"launch_branch={launch_branch or '<missing>'}; "
                f"current_branch={current_branch or branch_error or '<missing>'}; "
                f"launch_commit={launch_commit or '<missing>'}; "
                f"current_commit={current_commit or git_error or '<missing>'}"
            ),
        }
    )

    descriptors, descriptor_issues = review_preflight.scope_descriptors(ft_package_root, scope_ids)
    blockers.extend(descriptor_issues)
    review_mode = str(finalization.get("review_mode") or launch.get("review_mode") or "").strip()
    review_subjects: dict[str, dict[str, str]] = {}
    review_subject_issues: list[str] = []
    if review_mode not in review_preflight.REVIEW_MODES:
        review_subject_issues.append("review finalization packet has an unsupported review mode")
    elif not descriptor_issues:
        review_subjects, review_subject_issues = review_preflight.verify_review_subject_artifacts(
            launch,
            descriptors=descriptors,
            ft_package_root=ft_package_root,
            review_mode=review_mode,
        )
        if finalization.get("review_subject_artifacts_by_scope") != launch.get(
            "review_subject_artifacts_by_scope"
        ):
            review_subject_issues.append(
                "review finalization packet does not preserve launch review-subject hashes"
            )
    blockers.extend(review_subject_issues)
    checks.append(
        {
            "id": "review-subject-hash",
            "status": "pass" if not review_subject_issues else "fail",
            "details": f"subjects={len(review_subjects)}; issues={len(review_subject_issues)}",
        }
    )
    report = review_preflight.artifact_validator.validate(ft_package_root)
    partition = review_preflight.partition_validator_errors(
        report.get("findings", []), descriptors, ft_package_root, summary_path
    )
    relevant_errors = partition["scope_relevant"] + partition["package_global"]
    if relevant_errors:
        blockers.append(
            "current-scope-or-package validator errors remain after controller finalization: "
            + "; ".join(relevant_errors)
        )
    checks.append(
        {
            "id": "post-finalization-validator",
            "status": "pass" if not relevant_errors else "fail",
            "details": (
                f"scope_or_package_errors={len(relevant_errors)}; "
                f"external_errors={len(partition['external'])}"
            ),
        }
    )

    workflow_hashes: dict[str, str] = {}
    parity_issues: list[str] = []
    recovery_transition_issues: list[str] = []
    for descriptor in descriptors:
        workflow_hashes[descriptor.scope_id] = sha256_file(descriptor.workflow_path)
        try:
            state = review_preflight.artifact_validator.parse_workflow_state(descriptor.workflow_path)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            parity_issues.append(f"scope {descriptor.scope_id}: cannot read workflow state: {exc}")
            continue
        latest = state.get("latest_artifacts")
        latest = latest if isinstance(latest, dict) else {}
        repair_path = resolve_scope_artifact(
            latest.get("matrix_repair_summary"), descriptor.workflow_path, ft_package_root
        )
        parity_path = resolve_scope_artifact(
            latest.get("source_parity_check"), descriptor.workflow_path, ft_package_root
        )
        if repair_path is None or parity_path is None:
            continue
        resolved_gaps = gap_ids_on_marked_lines(repair_path, RESOLVED_MARKER_RE)
        active_gaps = gap_ids_on_marked_lines(parity_path, ACTIVE_GAP_MARKER_RE)
        stale_gaps = sorted(resolved_gaps & active_gaps)
        if stale_gaps:
            parity_issues.append(
                f"scope {descriptor.scope_id}: closed gap remains active in source-parity: {', '.join(stale_gaps)}"
            )
        if finalization.get("next_controller_transition") == "tc-review required":
            expected_recovery_state = {
                "current_stage": "ft-test-case-writer",
                "stage_status": "ready-for-review",
                "next_skill": "ft-test-case-reviewer",
                "review_mode": "tc_review",
                "matrix_review_status": "matrix-accepted",
            }
            for key, expected in expected_recovery_state.items():
                actual = str(state.get(key) or "").strip()
                if actual != expected:
                    recovery_transition_issues.append(
                        f"scope {descriptor.scope_id}: tc-review recovery checkpoint {key}="
                        f"{actual or '<missing>'}; expected {expected}"
                    )
            if str(state.get("current_round") or "").strip() != "2":
                recovery_transition_issues.append(
                    f"scope {descriptor.scope_id}: tc-review recovery checkpoint current_round="
                    f"{state.get('current_round') or '<missing>'}; expected 2"
                )
    blockers.extend(parity_issues)
    checks.append(
        {
            "id": "source-parity-gap-reconciliation",
            "status": "pass" if not parity_issues else "fail",
            "details": f"issues={len(parity_issues)}",
        }
    )
    blockers.extend(recovery_transition_issues)
    checks.append(
        {
            "id": "matrix-revalidation-to-tc-review-checkpoint",
            "status": "pass" if not recovery_transition_issues else "fail",
            "details": (
                "not-applicable"
                if finalization.get("next_controller_transition") != "tc-review required"
                else f"issues={len(recovery_transition_issues)}"
            ),
        }
    )

    return {
        "schema_version": 1,
        "status": "ready-for-next-stage" if not blockers else "blocked",
        "allowed": not blockers,
        "scope_ids": scope_ids,
        "repo_root": repo_root.as_posix(),
        "ft_package_root": ft_package_root.as_posix(),
        "summary_path": summary_path.as_posix(),
        "summary_sha256": sha256_file(summary_path) if summary_path.is_file() else "",
        "workflow_state_sha256_by_scope": workflow_hashes,
        "code_branch": current_branch,
        "code_commit": current_commit,
        "launch_receipt": launch_receipt.resolve().as_posix(),
        "launch_receipt_sha256": sha256_file(launch_receipt) if launch_receipt.is_file() else "",
        "review_finalization": finalization_packet.resolve().as_posix(),
        "review_finalization_sha256": sha256_file(finalization_packet) if finalization_packet.is_file() else "",
        "review_subject_artifacts_by_scope": review_subjects,
        "validator_error_partition": partition,
        "checks": checks,
        "blocking_reasons": blockers,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify practical controller state after independent review before next-stage routing."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--scope-id", action="append", required=True)
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument("--review-finalization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--link-output",
        action="store_true",
        help="Link an allowed gate packet from every selected workflow-state.yaml.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_post_finalization_gate(
        repo_root=args.repo_root,
        ft_package_root=args.ft_package_root,
        summary_path=args.summary,
        scope_ids=list(dict.fromkeys(args.scope_id)),
        launch_receipt=args.launch_receipt,
        finalization_packet=args.review_finalization,
    )
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.link_output and result["allowed"]:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            link_allowed_gate_output(
                ft_package_root=args.ft_package_root,
                scope_ids=list(dict.fromkeys(args.scope_id)),
                output_path=output,
            )
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            result["allowed"] = False
            result["status"] = "blocked"
            result["blocking_reasons"].append(
                f"allowed gate packet could not be linked from workflow state: {exc}"
            )
        else:
            result["workflow_linked"] = True
    else:
        result["workflow_linked"] = False
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
