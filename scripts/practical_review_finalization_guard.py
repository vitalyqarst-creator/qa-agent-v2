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
EXECUTION_SURFACES = {"codex-task", "codex-thread"}
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


def next_controller_transition(review_mode: str, verdict: str) -> str:
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

    reviewer_surface = markdown_field(independence_content, "reviewer_execution_surface")
    reviewer_task = markdown_field(independence_content, "reviewer_task_or_session")
    reviewer_thread = markdown_field(independence_content, "reviewer_thread_url_or_id")
    if reviewer_surface not in EXECUTION_SURFACES:
        blockers.append("review independence artifact lacks a Codex task/thread execution surface")
    if not TASK_ID_RE.fullmatch(reviewer_task):
        blockers.append("review independence artifact lacks a durable reviewer task/session id")
    if reviewer_task and reviewer_task not in reviewer_thread:
        blockers.append("reviewer thread id does not match reviewer task/session id")
    checks.append(
        FinalizationCheck(
            "reviewer-independence",
            "pass" if not any("reviewer" in item for item in blockers) else "fail",
            f"surface={reviewer_surface or '<missing>'}; task={reviewer_task or '<missing>'}",
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
        "launch_receipt": launch_receipt.resolve().as_posix(),
        "launch_receipt_sha256": sha256_file(launch_receipt) if launch_receipt.is_file() else "",
        "controller_artifact_snapshot": receipt.get("controller_artifact_snapshot", {}),
        "review_artifact": resolved_review.as_posix() if resolved_review else "",
        "review_artifact_sha256": sha256_file(resolved_review) if resolved_review else "",
        "independence_artifact": resolved_independence.as_posix() if resolved_independence else "",
        "independence_artifact_sha256": sha256_file(resolved_independence) if resolved_independence else "",
        "verdict": verdict,
        "reviewer_task_or_session": reviewer_task,
        "reviewer_execution_surface": reviewer_surface,
        "next_controller_transition": next_controller_transition(review_mode, verdict),
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
