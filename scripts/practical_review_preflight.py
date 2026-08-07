"""Fail-closed preflight for launching a practical-route reviewer task.

The practical route uses a separate Codex task for matrix and TC review.  This
script is deliberately run by the controller *before* ``create_thread`` and
again by the reviewer before it starts its read-only assessment.  It prevents a
reviewer task from silently using another checkout, branch or FT package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_agent_artifacts as artifact_validator  # noqa: E402
import practical_snapshot_preflight as snapshot_preflight  # noqa: E402


REVIEW_MODES = {"matrix_review", "tc_review"}
EXPECTED_TRANSITIONS = {
    "matrix_review": {"matrix-review allowed", "matrix-review conditional"},
    "tc_review": {"tc-review allowed", "tc-review conditional"},
}
BLOCKED_TRANSITIONS = {
    "matrix_review": "matrix-review blocked",
    "tc_review": "tc-review blocked",
}
SCOPE_ID_RE = re.compile(r"^\d{2}$")


@dataclass(frozen=True)
class ScopeDescriptor:
    scope_id: str
    handoff_dir: Path
    scope_slug: str
    workflow_path: Path


@dataclass(frozen=True)
class PreflightCheck:
    id: str
    status: str
    details: str


def run_git(root: Path, *args: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def normalized_path(value: str | Path) -> str:
    return str(value).strip().strip("`").replace("\\", "/").rstrip("/").casefold()


def paths_equal(left: str | Path, right: str | Path) -> bool:
    """Compare existing Windows paths without being confused by 8.3 aliases."""

    left_path = Path(str(left).strip().strip("`"))
    right_path = Path(str(right).strip().strip("`"))
    try:
        return left_path.samefile(right_path)
    except OSError:
        return normalized_path(left_path) == normalized_path(right_path)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_version_gate_values(content: str) -> dict[str, str]:
    section = artifact_validator.extract_markdown_section(content, "Code Version Gate")
    if not section:
        return {}
    rows = artifact_validator.markdown_table_rows_from_text(section)
    if len(rows) < 2:
        return {}
    header = artifact_validator.normalize_table_header(rows[0])
    if "field" not in header:
        return {}
    value_column = "actual" if "actual" in header else "value"
    if value_column not in header:
        return {}
    field_index = header.index("field")
    value_index = header.index(value_column)
    values: dict[str, str] = {}
    for row in rows[1:]:
        if field_index >= len(row) or value_index >= len(row):
            continue
        field = artifact_validator.normalize_markdown_field_name(row[field_index])
        value = artifact_validator.strip_markdown_code(row[value_index])
        if field:
            values[field] = value
    return values


def scope_descriptors(ft_package_root: Path, scope_ids: Iterable[str]) -> tuple[list[ScopeDescriptor], list[str]]:
    descriptors: list[ScopeDescriptor] = []
    issues: list[str] = []
    handoff_root = ft_package_root / "work" / "stage-handoffs"
    for scope_id in scope_ids:
        matches = sorted(path for path in handoff_root.glob(f"{scope_id}-*") if path.is_dir())
        if len(matches) != 1:
            issues.append(f"scope {scope_id}: handoff directories found={len(matches)}")
            continue
        handoff_dir = matches[0]
        workflow_path = handoff_dir / "workflow-state.yaml"
        if not workflow_path.is_file():
            issues.append(f"scope {scope_id}: workflow-state.yaml is missing")
            continue
        try:
            state = artifact_validator.parse_workflow_state(workflow_path)
        except UnicodeDecodeError:
            issues.append(f"scope {scope_id}: workflow-state.yaml is not UTF-8")
            continue
        scope_slug = str(state.get("scope_slug") or handoff_dir.name.split("-", 1)[1]).strip()
        if not scope_slug:
            issues.append(f"scope {scope_id}: scope_slug is missing")
            continue
        descriptors.append(
            ScopeDescriptor(
                scope_id=scope_id,
                handoff_dir=handoff_dir,
                scope_slug=scope_slug,
                workflow_path=workflow_path,
            )
        )
    return descriptors, issues


def all_scope_descriptors(ft_package_root: Path) -> list[ScopeDescriptor]:
    """Resolve every numbered scope so unrelated practical findings stay local."""

    handoff_root = ft_package_root / "work" / "stage-handoffs"
    if not handoff_root.is_dir():
        return []
    scope_ids = sorted(
        {
            match.group(1)
            for path in handoff_root.iterdir()
            if path.is_dir()
            for match in [re.match(r"(\d{2})-", path.name)]
            if match is not None
        }
    )
    descriptors, _ = scope_descriptors(ft_package_root, scope_ids)
    return descriptors


def scope_id_for_finding_path(path_text: str, descriptors: Iterable[ScopeDescriptor], ft_package_root: Path) -> str | None:
    normalized = path_text.replace("\\", "/").lstrip("./")
    for descriptor in descriptors:
        handoff_relative = descriptor.handoff_dir.relative_to(ft_package_root).as_posix()
        practical_relative = (ft_package_root / "work" / "practical" / descriptor.scope_slug).relative_to(ft_package_root).as_posix()
        if normalized == handoff_relative or normalized.startswith(f"{handoff_relative}/"):
            return descriptor.scope_id
        if normalized == practical_relative or normalized.startswith(f"{practical_relative}/"):
            return descriptor.scope_id
    handoff_match = re.search(r"(?:^|/)work/stage-handoffs/(\d{2})-", normalized)
    return handoff_match.group(1) if handoff_match else None


def relevant_validator_errors(
    findings: Iterable[dict[str, Any]],
    descriptors: list[ScopeDescriptor],
    ft_package_root: Path,
) -> list[str]:
    requested_ids = {item.scope_id for item in descriptors}
    ownership_descriptors = all_scope_descriptors(ft_package_root)
    issues: list[str] = []
    for finding in findings:
        if str(finding.get("severity", "")).casefold() != "error":
            continue
        finding_id = str(finding.get("id", "<missing-id>"))
        category = str(finding.get("category", ""))
        path_text = str(finding.get("path", ""))
        if category == "practical-stage-summary":
            issues.append(f"{finding_id}: practical-stage-summary gate failed")
            continue
        owner_scope_id = scope_id_for_finding_path(path_text, ownership_descriptors, ft_package_root)
        if owner_scope_id is None:
            issues.append(f"{finding_id}: package-global or unclassified error at {path_text or '<missing-path>'}")
        elif owner_scope_id in requested_ids:
            issues.append(f"{finding_id}: current scope {owner_scope_id} error at {path_text}")
    return issues


def build_preflight(
    *,
    repo_root: Path,
    ft_package_root: Path,
    summary_path: Path,
    scope_ids: list[str],
    review_mode: str,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ft_package_root = ft_package_root.resolve()
    summary_path = summary_path.resolve()
    checks: list[PreflightCheck] = []
    blockers: list[str] = []

    current_directory = Path.cwd().resolve()
    git_code, git_root, git_error = run_git(repo_root, "rev-parse", "--show-toplevel")
    if git_code != 0 or not paths_equal(git_root, repo_root):
        blockers.append("repo_root is not the current Git worktree root")
        checks.append(PreflightCheck("git-root", "fail", git_error or git_root or "Git root cannot be resolved"))
    elif current_directory != repo_root:
        blockers.append("execution working directory differs from repo_root")
        checks.append(PreflightCheck("execution-root", "fail", f"cwd={current_directory}; repo_root={repo_root}"))
    else:
        checks.append(PreflightCheck("execution-root", "pass", str(repo_root)))

    if not is_within(ft_package_root, repo_root):
        blockers.append("FT package root is outside repo_root")
        checks.append(PreflightCheck("ft-package-root", "fail", str(ft_package_root)))
    elif not summary_path.is_file() or not is_within(summary_path, ft_package_root):
        blockers.append("practical stage summary is missing or outside FT package root")
        checks.append(PreflightCheck("summary-path", "fail", str(summary_path)))
    else:
        checks.append(PreflightCheck("ft-package-root", "pass", str(ft_package_root)))

    summary_content = ""
    summary_fields: dict[str, str] = {}
    if summary_path.is_file():
        try:
            summary_content = summary_path.read_text(encoding="utf-8")
            summary_fields = artifact_validator.parse_markdown_key_value_fields(summary_content)
        except UnicodeDecodeError:
            blockers.append("practical stage summary is not UTF-8")
            checks.append(PreflightCheck("summary-readable", "fail", str(summary_path)))

    if summary_fields:
        summary_code_root = summary_fields.get("code_root", "")
        summary_execution_root = summary_fields.get("execution_working_directory", "")
        summary_ft_root = summary_fields.get("ft_package_root", "")
        summary_artifact_root = summary_fields.get("artifact_write_root", "")
        expected_transition = EXPECTED_TRANSITIONS[review_mode]
        transition = summary_fields.get("next_stage_transition", "").strip().casefold()
        active_scope_ids = {
            item.strip()
            for item in summary_fields.get("active_scope_ids", "").split(",")
            if item.strip()
        }
        if not paths_equal(summary_code_root, repo_root):
            blockers.append("summary code_root differs from executing repo_root")
        if not paths_equal(summary_execution_root, repo_root):
            blockers.append("summary execution_working_directory differs from executing repo_root")
        if not paths_equal(summary_ft_root, ft_package_root):
            blockers.append("summary ft_package_root differs from requested FT package root")
        if not summary_artifact_root or not is_within(Path(summary_artifact_root.strip("`")), ft_package_root):
            blockers.append("summary artifact_write_root is outside FT package root")
        if not set(scope_ids).issubset(active_scope_ids):
            blockers.append("requested scope ids are outside summary active_scope_ids")
        transition_is_explicitly_blocked = transition == BLOCKED_TRANSITIONS[review_mode]
        if transition not in expected_transition and not transition_is_explicitly_blocked:
            blockers.append(
                f"summary next_stage_transition={transition or '<missing>'}; expected one of {sorted(expected_transition)}"
            )
        checks.append(
            PreflightCheck(
                "summary-contract",
                "pass"
                if transition in expected_transition and not blockers
                else "blocked"
                if transition_is_explicitly_blocked
                else "fail",
                f"active_scope_ids={', '.join(sorted(active_scope_ids)) or '<missing>'}; transition={transition or '<missing>'}",
            )
        )

    branch_code, branch, branch_error = run_git(repo_root, "branch", "--show-current")
    head_code, commit, head_error = run_git(repo_root, "rev-parse", "HEAD")
    status_code, tracked_changes, status_error = run_git(repo_root, "status", "--porcelain=v1", "--untracked-files=no")
    version_values = code_version_gate_values(summary_content)
    expected_branch = version_values.get("branch") or version_values.get("code_branch") or ""
    expected_commit = (version_values.get("commit") or version_values.get("code_commit") or "").casefold()
    current_branch = branch if branch_code == 0 and branch else "detached HEAD"
    current_commit = commit.casefold() if head_code == 0 else ""
    if not expected_branch or not expected_commit:
        blockers.append("summary Code Version Gate lacks branch or exact commit")
    elif current_branch != expected_branch or current_commit != expected_commit:
        blockers.append(
            f"version gate mismatch: expected branch={expected_branch}, commit={expected_commit}; actual branch={current_branch}, commit={current_commit or '<missing>'}"
        )
    if status_code != 0:
        blockers.append(f"cannot determine tracked worktree state: {status_error}")
    elif tracked_changes:
        blockers.append("tracked code/instruction/config files are dirty before reviewer launch")
    checks.append(
        PreflightCheck(
            "version-gate",
            "pass" if not any("version gate" in item or "Code Version Gate" in item or "tracked code" in item for item in blockers) else "fail",
            f"branch={current_branch}; commit={current_commit or '<missing>'}; tracked_changes={'yes' if tracked_changes else 'no'}",
        )
    )

    descriptors, descriptor_issues = scope_descriptors(ft_package_root, scope_ids)
    blockers.extend(descriptor_issues)
    quality_gate_blocked_scope_ids: list[str] = []
    for descriptor in descriptors:
        state = artifact_validator.parse_workflow_state(descriptor.workflow_path)
        if (
            state.get("stage_status") == "blocked-quality-gate"
            and state.get("current_stage") == "ft-test-case-writer"
            and state.get("next_skill") == "ft-test-case-writer"
        ):
            quality_gate_blocked_scope_ids.append(descriptor.scope_id)
            blockers.append(
                f"scope {descriptor.scope_id}: Writer Quality Gate blocks reviewer launch"
            )
        elif state.get("next_skill") != "ft-test-case-reviewer":
            blockers.append(f"scope {descriptor.scope_id}: next_skill is not ft-test-case-reviewer")
        if str(state.get("review_mode", "")) != review_mode:
            blockers.append(
                f"scope {descriptor.scope_id}: review_mode={state.get('review_mode', '<missing>')}; expected={review_mode}"
            )
        if review_mode == "tc_review":
            latest = state.get("latest_artifacts")
            snapshot_value = ""
            if isinstance(latest, dict):
                snapshot_value = str(
                    latest.get("pre_write_baseline_snapshot")
                    or latest.get("pre_quality_gate_baseline_snapshot")
                    or ""
                ).strip()
            if snapshot_value:
                snapshot_path = artifact_validator.resolve_artifact_path(
                    snapshot_value,
                    descriptor.workflow_path,
                    repo_root,
                    ft_package_root,
                )
                if snapshot_path is None or not snapshot_path.is_dir():
                    blockers.append(f"scope {descriptor.scope_id}: pre-write baseline snapshot is missing")
                else:
                    snapshot_result = snapshot_preflight.verify_snapshot(snapshot_path, ft_package_root)
                    if snapshot_result.get("status") != "valid":
                        issues = "; ".join(str(item) for item in snapshot_result.get("issues", []))
                        blockers.append(
                            f"scope {descriptor.scope_id}: pre-write baseline snapshot is invalid: {issues or 'unknown issue'}"
                        )
    checks.append(
        PreflightCheck(
            "scope-routing",
            "pass"
            if not descriptor_issues and len(descriptors) == len(scope_ids) and not quality_gate_blocked_scope_ids
            else "blocked"
            if not descriptor_issues and len(descriptors) == len(scope_ids) and quality_gate_blocked_scope_ids
            else "fail",
            f"scopes={', '.join(scope_ids)}",
        )
    )

    report = artifact_validator.validate(ft_package_root)
    validator_issues = relevant_validator_errors(report.get("findings", []), descriptors, ft_package_root)
    blockers.extend(validator_issues)
    checks.append(
        PreflightCheck(
            "package-validator",
            "pass" if not validator_issues else "fail",
            f"errors={sum(1 for item in report.get('findings', []) if item.get('severity') == 'error')}; scope_relevant_errors={len(validator_issues)}",
        )
    )

    return {
        "schema_version": 1,
        "status": "allowed" if not blockers else "blocked",
        "allowed": not blockers,
        "review_mode": review_mode,
        "scope_ids": scope_ids,
        "repo_root": repo_root.as_posix(),
        "ft_package_root": ft_package_root.as_posix(),
        "summary_path": summary_path.as_posix(),
        "summary_sha256": sha256_file(summary_path) if summary_path.is_file() else "",
        "code_branch": current_branch,
        "code_commit": current_commit,
        "checks": [asdict(check) for check in checks],
        "blocking_reasons": blockers,
    }


def verify_receipt(receipt_path: Path, current: dict[str, Any]) -> list[str]:
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"cannot read launch preflight receipt: {exc}"]
    expected_pairs = (
        "allowed",
        "review_mode",
        "scope_ids",
        "repo_root",
        "ft_package_root",
        "summary_path",
        "summary_sha256",
        "code_branch",
        "code_commit",
    )
    issues = [
        f"receipt {field} differs from current preflight"
        for field in expected_pairs
        if receipt.get(field) != current.get(field)
    ]
    if receipt.get("allowed") is not True:
        issues.append("launch preflight receipt is not allowed")
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate practical reviewer launch roots, version and package gate.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--scope-id", action="append", required=True)
    parser.add_argument("--review-mode", choices=sorted(REVIEW_MODES), required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-receipt", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output and args.verify_receipt:
        raise SystemExit("error: --output and --verify-receipt are mutually exclusive")
    scope_ids = list(dict.fromkeys(args.scope_id))
    invalid_scope_ids = [scope_id for scope_id in scope_ids if not SCOPE_ID_RE.fullmatch(scope_id)]
    if invalid_scope_ids:
        raise SystemExit(f"error: invalid --scope-id values: {', '.join(invalid_scope_ids)}")
    result = build_preflight(
        repo_root=args.repo_root,
        ft_package_root=args.ft_package_root,
        summary_path=args.summary,
        scope_ids=scope_ids,
        review_mode=args.review_mode,
    )
    if args.verify_receipt:
        receipt_issues = verify_receipt(args.verify_receipt.resolve(), result)
        if receipt_issues:
            result["allowed"] = False
            result["status"] = "blocked"
            result["blocking_reasons"].extend(receipt_issues)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
