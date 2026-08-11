"""Apply the controller-owned transition from accepted matrix R2 to TC review.

The matrix reviewer is read-only.  Once its R2 finalization packet accepts a
matrix that was invalidated after canonical test cases existed, the controller
must perform one exact state transition: preserve the canonical suite and route
it to a fresh independent TC review.  This script owns that transition so a
controller cannot accidentally leave stale matrix-review prompts, statuses or
aliases behind.
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
import refresh_practical_stage_summary as summary_refresh  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_to_package(path: Path, package_root: Path) -> str:
    return path.resolve().relative_to(package_root.resolve()).as_posix()


def _state_matches_revalidation(state: dict[str, Any]) -> list[str]:
    expected = {
        "current_stage": "ft-test-case-writer",
        "stage_status": "ready-for-review",
        "next_skill": "ft-test-case-reviewer",
        "review_mode": "matrix_review",
        "matrix_review_status": "invalidated",
        "matrix_revalidation_reason": "reviewed-matrix-hash-mismatch",
    }
    issues = [
        f"{key}={state.get(key)!r}; expected {value!r}"
        for key, value in expected.items()
        if str(state.get(key) or "").strip() != value
    ]
    if str(state.get("current_round") or "").strip() != "2":
        issues.append(f"current_round={state.get('current_round')!r}; expected 2")
    return issues


def _resolve_tc_reviewer_prompt(
    state: dict[str, Any], workflow_path: Path, package_root: Path
) -> Path | None:
    values = [
        *review_preflight.artifact_validator.flatten_string_values(
            state.get("required_inputs")
        ),
        *review_preflight.artifact_validator.flatten_string_values(
            state.get("latest_artifacts")
        ),
    ]
    return review_preflight.artifact_validator.resolving_artifact_by_name(
        "prompt.tc-to-reviewer.md", values, workflow_path, package_root, package_root
    )


def _replace_summary_field(text: str, field: str, value: str) -> str:
    pattern = re.compile(
        rf"(?m)^\|\s*{re.escape(field)}\s*\|\s*`?[^|\n]*`?\s*\|\s*$"
    )
    replacement = f"| {field} | `{value}` |"
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError(f"practical stage summary lacks field {field}")
    return updated


def _replace_section(text: str, title: str, body: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(title)}\s*$.*?(?=^##\s+|\Z)"
    )
    replacement = f"## {title}\n\n{body.strip()}\n\n"
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError(f"practical stage summary lacks section {title}")
    return updated


def _update_scope_transition_rows(text: str, scope_ids: list[str]) -> str:
    for scope_id in scope_ids:
        pattern = re.compile(
            rf"(?m)^\|\s*`?{re.escape(scope_id)}`?\s*\|[^\n]*\|\s*$"
        )
        replacement = (
            f"| `{scope_id}` | `matrix-accepted` | `tc-review allowed` | "
            "`not-applicable` | `not-applicable` | "
            "Матрица повторно принята независимо; сохранённый набор тест-кейсов направлен на независимое ревью. |"
        )
        text, count = pattern.subn(replacement, text, count=1)
        if count != 1:
            raise ValueError(f"practical stage summary lacks scope transition row {scope_id}")
    return text


def transition_summary(
    summary_path: Path, scope_ids: list[str], finalization_path: Path
) -> str:
    text = summary_path.read_text(encoding="utf-8")
    for field, value in (
        ("summary_stage", "matrix-revalidation-finalized"),
        ("next_stage_transition", "tc-review allowed"),
        (
            "next_safe_step",
            "Запустить независимое TC-review сохранённого набора тест-кейсов в отдельной Codex-сессии.",
        ),
        ("review_launch_preflight_status", "not-run"),
        ("review_launch_preflight_evidence", "not-applicable"),
        ("review_launch_preflight_receipt", "not-applicable"),
        (
            "reporting_evidence",
            f"matrix revalidation finalization: `{finalization_path.name}`; TC review: `not-run`",
        ),
    ):
        text = _replace_summary_field(text, field, value)
    text = _update_scope_transition_rows(text, scope_ids)
    return _replace_section(
        text,
        "Действия текущего этапа",
        "\n".join(
            [
                "- Независимая повторная проверка матрицы завершилась с `matrix-accepted`.",
                "- Контроллер сохранил canonical набор тест-кейсов без изменений.",
                "- Следующий обязательный этап — независимое TC-review в отдельной Codex-сессии.",
            ]
        ),
    )


def build_transition(
    *,
    repo_root: Path,
    ft_package_root: Path,
    summary_path: Path,
    scope_ids: list[str],
    finalization_packet: Path,
) -> tuple[dict[str, Any], list[tuple[Path, dict[str, Any]]], str | None]:
    repo_root = repo_root.resolve()
    ft_package_root = ft_package_root.resolve()
    summary_path = summary_path.resolve()
    finalization_packet = finalization_packet.resolve()
    blockers: list[str] = []
    updates: list[tuple[Path, dict[str, Any]]] = []

    try:
        finalization = json.loads(finalization_packet.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        finalization = {}
        blockers.append(f"cannot read matrix revalidation finalization: {exc}")
    expected_finalization = {
        "allowed": True,
        "review_mode": "matrix_review",
        "recovery_context": "matrix-revalidation-after-canonical-tcs",
        "next_controller_transition": "tc-review required",
    }
    for key, expected in expected_finalization.items():
        if finalization.get(key) != expected:
            blockers.append(
                f"matrix revalidation finalization {key}={finalization.get(key)!r}; expected {expected!r}"
            )
    if finalization.get("scope_ids") != scope_ids:
        blockers.append("matrix revalidation finalization scope ids differ from requested scope ids")

    descriptors, descriptor_issues = review_preflight.scope_descriptors(
        ft_package_root, scope_ids
    )
    blockers.extend(descriptor_issues)
    if not descriptor_issues:
        _subjects, subject_issues = review_preflight.verify_review_subject_artifacts(
            finalization,
            descriptors=descriptors,
            ft_package_root=ft_package_root,
            review_mode="matrix_review",
        )
        blockers.extend(subject_issues)
    branch_rc, branch, branch_error = review_preflight.run_git(
        repo_root, "branch", "--show-current"
    )
    commit_rc, commit, commit_error = review_preflight.run_git(repo_root, "rev-parse", "HEAD")
    if (
        branch_rc != 0
        or commit_rc != 0
        or str(finalization.get("code_branch") or "").strip() != branch.strip()
        or str(finalization.get("code_commit") or "").casefold().strip()
        != commit.casefold().strip()
    ):
        blockers.append(
            "pinned-code-version-changed: finalization is not from the current checkout "
            f"(branch={branch or branch_error or '<missing>'}; commit={commit or commit_error or '<missing>'})"
        )

    for descriptor in descriptors:
        try:
            state = review_preflight.artifact_validator.parse_workflow_state(
                descriptor.workflow_path
            )
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            blockers.append(f"scope {descriptor.scope_id}: cannot read workflow state: {exc}")
            continue
        for issue in _state_matches_revalidation(state):
            blockers.append(f"scope {descriptor.scope_id}: {issue}")
        prompt_path = _resolve_tc_reviewer_prompt(
            state, descriptor.workflow_path, ft_package_root
        )
        if prompt_path is None or not prompt_path.is_file():
            blockers.append(
                f"scope {descriptor.scope_id}: prompt.tc-to-reviewer.md is missing from current handoff inputs"
            )
            continue
        latest = state.get("latest_artifacts")
        latest = dict(latest) if isinstance(latest, dict) else {}
        latest["active_transition_prompt"] = _relative_to_package(prompt_path, ft_package_root)
        latest["matrix_revalidation_finalization"] = _relative_to_package(
            finalization_packet, ft_package_root
        )
        latest["controller_finalization"] = _relative_to_package(
            finalization_packet, ft_package_root
        )
        # R1 is historical evidence, not the binding for the revalidated matrix.
        latest.pop("controller_post_finalization_gate", None)
        updated = dict(state)
        updated.update(
            {
                "current_stage": "ft-test-case-writer",
                "stage_status": "ready-for-review",
                "next_skill": "ft-test-case-reviewer",
                "review_mode": "tc_review",
                "current_round": 2,
                "matrix_review_status": "matrix-accepted",
                "matrix_revalidation_reason": "reviewed-matrix-hash-mismatch",
                "latest_artifacts": latest,
                "blocking_reasons": [],
            }
        )
        updates.append((descriptor.workflow_path, updated))

    summary_after: str | None = None
    if not summary_path.is_file():
        blockers.append("practical stage summary is missing")
    elif not blockers:
        try:
            summary_after = transition_summary(summary_path, scope_ids, finalization_packet)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            blockers.append(f"cannot materialize practical stage summary: {exc}")

    result = {
        "schema_version": 1,
        "status": "ready-to-apply" if not blockers else "blocked",
        "allowed": not blockers,
        "repo_root": repo_root.as_posix(),
        "ft_package_root": ft_package_root.as_posix(),
        "summary_path": summary_path.as_posix(),
        "scope_ids": scope_ids,
        "matrix_revalidation_finalization": finalization_packet.as_posix(),
        "code_branch": branch.strip() if branch_rc == 0 else "",
        "code_commit": commit.casefold().strip() if commit_rc == 0 else "",
        "transition": "matrix-revalidation-accepted-to-tc-review",
        "blocking_reasons": blockers,
    }
    return result, updates, summary_after


def apply_transition(
    *, updates: list[tuple[Path, dict[str, Any]]], summary_path: Path, summary_after: str
) -> None:
    for path, state in updates:
        path.write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
    summary_path.write_text(summary_after, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize accepted matrix revalidation as an independent TC-review handoff."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--scope-id", action="append", required=True)
    parser.add_argument("--review-finalization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scope_ids = list(dict.fromkeys(args.scope_id))
    result, updates, summary_after = build_transition(
        repo_root=args.repo_root,
        ft_package_root=args.ft_package_root,
        summary_path=args.summary,
        scope_ids=scope_ids,
        finalization_packet=args.review_finalization,
    )
    if args.apply and result["allowed"]:
        assert summary_after is not None
        summary_path = args.summary.resolve()
        original_workflows = {
            path: path.read_text(encoding="utf-8") for path, _state in updates
        }
        original_summary = summary_path.read_text(encoding="utf-8")
        try:
            apply_transition(
                updates=updates,
                summary_path=summary_path,
                summary_after=summary_after,
            )
            summary_refresh.refresh_summary_file(
                args.repo_root.resolve(), summary_path, scope_ids
            )
        except (OSError, UnicodeDecodeError, ValueError, RuntimeError) as exc:
            for path, content in original_workflows.items():
                path.write_text(content, encoding="utf-8")
            summary_path.write_text(original_summary, encoding="utf-8")
            result["allowed"] = False
            result["status"] = "blocked"
            result["blocking_reasons"].append(
                f"transition was rolled back because practical summary refresh failed: {exc}"
            )
        result["applied"] = result["allowed"]
    else:
        result["applied"] = False
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["allowed"] else 2


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
