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
import shutil
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
CONTROLLER_SNAPSHOT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ScopeDescriptor:
    scope_id: str
    handoff_dir: Path
    scope_slug: str
    workflow_path: Path
    canonical_test_case_paths: tuple[str, ...]


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


def snapshot_directory_for_receipt(output_path: Path) -> Path:
    """Return the immutable controller-state snapshot location for a receipt."""

    return output_path.parent / f"{output_path.stem}.controller-state"


def _snapshot_target(
    *,
    role: str,
    source_path: Path,
    snapshot_path: Path,
) -> dict[str, str]:
    return {
        "role": role,
        "source_path": source_path.resolve().as_posix(),
        "snapshot_path": snapshot_path.resolve().as_posix(),
        "sha256": sha256_file(source_path),
    }


def materialize_controller_snapshot(
    receipt: dict[str, Any], output_path: Path) -> dict[str, Any]:
    """Copy controller-owned state before a separate reviewer starts.

    Hashes alone can detect an ownership violation but cannot recover from one.
    The snapshot is a controller artifact created alongside the launch receipt;
    reviewers must never edit it.  Reusing an existing matching snapshot keeps a
    repeated preflight invocation idempotent, while a mismatched directory fails
    closed instead of overwriting evidence from another review launch.
    """

    if receipt.get("allowed") is not True:
        return receipt

    ft_package_root = Path(str(receipt["ft_package_root"])).resolve()
    summary_path = Path(str(receipt["summary_path"])).resolve()
    hashes = receipt.get("controller_artifact_hashes")
    if not isinstance(hashes, dict) or not summary_path.is_file():
        raise ValueError("allowed receipt lacks controller artifact hashes or summary")

    descriptors, issues = scope_descriptors(
        ft_package_root,
        [str(value) for value in receipt.get("scope_ids", [])],
    )
    if issues:
        raise ValueError("cannot snapshot controller state: " + "; ".join(issues))

    output_path = output_path.resolve()
    snapshot_directory = snapshot_directory_for_receipt(output_path)
    manifest_path = snapshot_directory / "manifest.json"
    expected_workflow_hashes = hashes.get("workflow_state_sha256_by_scope")
    if not isinstance(expected_workflow_hashes, dict):
        raise ValueError("allowed receipt lacks workflow-state hashes")

    targets: dict[str, dict[str, Any]] = {
        "summary": _snapshot_target(
            role="practical-stage-summary",
            source_path=summary_path,
            snapshot_path=snapshot_directory / "practical-stage-summary.md",
        ),
        "workflow_state_by_scope": {},
    }
    for descriptor in descriptors:
        expected = str(expected_workflow_hashes.get(descriptor.scope_id) or "")
        actual = sha256_file(descriptor.workflow_path)
        if not expected or expected != actual:
            raise ValueError(
                f"controller workflow-state changed before snapshot for scope {descriptor.scope_id}"
            )
        targets["workflow_state_by_scope"][descriptor.scope_id] = _snapshot_target(
            role="workflow-state",
            source_path=descriptor.workflow_path,
            snapshot_path=snapshot_directory / f"workflow-state-{descriptor.scope_id}.yaml",
        )
    if str(hashes.get("summary_sha256") or "") != targets["summary"]["sha256"]:
        raise ValueError("controller practical-stage-summary changed before snapshot")

    manifest = {
        "schema_version": CONTROLLER_SNAPSHOT_SCHEMA_VERSION,
        "launch_receipt_path": output_path.as_posix(),
        "controller_artifacts": targets,
    }
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if snapshot_directory.exists():
        if not manifest_path.is_file() or manifest_path.read_text(encoding="utf-8") != rendered:
            raise FileExistsError(
                f"controller snapshot directory already exists with different contents: {snapshot_directory}"
            )
    else:
        snapshot_directory.mkdir(parents=True)
        try:
            for item in [targets["summary"], *targets["workflow_state_by_scope"].values()]:
                source = Path(item["source_path"])
                destination = Path(item["snapshot_path"])
                shutil.copyfile(source, destination)
            manifest_path.write_text(rendered, encoding="utf-8")
        except Exception:
            shutil.rmtree(snapshot_directory, ignore_errors=True)
            raise

    receipt = dict(receipt)
    receipt["controller_artifact_snapshot"] = {
        "schema_version": CONTROLLER_SNAPSHOT_SCHEMA_VERSION,
        "directory": snapshot_directory.as_posix(),
        "manifest": manifest_path.as_posix(),
    }
    return receipt


def verify_controller_snapshot(
    receipt: dict[str, Any],
    *,
    ft_package_root: Path,
    summary_path: Path,
    descriptors: Iterable[ScopeDescriptor],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Verify snapshot bytes and return restore targets keyed by source path."""

    snapshot_info = receipt.get("controller_artifact_snapshot")
    if not isinstance(snapshot_info, dict):
        return {}, ["review launch receipt lacks controller recovery snapshot"]
    try:
        snapshot_directory = Path(str(snapshot_info["directory"])).resolve()
        manifest_path = Path(str(snapshot_info["manifest"])).resolve()
    except (KeyError, TypeError, ValueError):
        return {}, ["review launch receipt has invalid controller recovery snapshot paths"]
    if not is_within(snapshot_directory, ft_package_root) or not is_within(manifest_path, snapshot_directory):
        return {}, ["controller recovery snapshot is outside FT package root"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, [f"cannot read controller recovery snapshot: {exc}"]
    if manifest.get("schema_version") != CONTROLLER_SNAPSHOT_SCHEMA_VERSION:
        return {}, ["controller recovery snapshot schema is unsupported"]
    artifacts = manifest.get("controller_artifacts")
    if not isinstance(artifacts, dict):
        return {}, ["controller recovery snapshot lacks artifact manifest"]
    expected_hashes = receipt.get("controller_artifact_hashes")
    if not isinstance(expected_hashes, dict):
        return {}, ["review launch receipt lacks controller artifact hashes"]

    expected_targets: dict[str, tuple[Path, str]] = {
        "summary": (summary_path.resolve(), str(expected_hashes.get("summary_sha256") or "")),
    }
    workflow_hashes = expected_hashes.get("workflow_state_sha256_by_scope")
    if not isinstance(workflow_hashes, dict):
        return {}, ["review launch receipt lacks workflow-state hashes"]
    for descriptor in descriptors:
        expected_targets[f"workflow:{descriptor.scope_id}"] = (
            descriptor.workflow_path.resolve(),
            str(workflow_hashes.get(descriptor.scope_id) or ""),
        )

    manifest_items: dict[str, Any] = {"summary": artifacts.get("summary")}
    workflows = artifacts.get("workflow_state_by_scope")
    if isinstance(workflows, dict):
        manifest_items.update({f"workflow:{key}": value for key, value in workflows.items()})

    targets: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for key, (expected_source, expected_hash) in expected_targets.items():
        item = manifest_items.get(key)
        if not isinstance(item, dict):
            issues.append(f"controller recovery snapshot lacks {key}")
            continue
        source_path = Path(str(item.get("source_path") or "")).resolve()
        snapshot_path = Path(str(item.get("snapshot_path") or "")).resolve()
        snapshot_hash = str(item.get("sha256") or "")
        if source_path != expected_source:
            issues.append(f"controller recovery snapshot source path mismatch for {key}")
        if not is_within(snapshot_path, snapshot_directory) or not snapshot_path.is_file():
            issues.append(f"controller recovery snapshot file is missing for {key}")
        elif not expected_hash or snapshot_hash != expected_hash or sha256_file(snapshot_path) != expected_hash:
            issues.append(f"controller recovery snapshot hash mismatch for {key}")
        targets[key] = {"source_path": source_path, "snapshot_path": snapshot_path, "sha256": expected_hash}
    return targets, issues


def code_version_gate_values(content: str) -> dict[str, str]:
    section = artifact_validator.extract_practical_stage_summary_section(content, "code_version_gate")
    if not section:
        return {}
    rows = artifact_validator.markdown_table_rows_from_text(section)
    if len(rows) < 2:
        return {}
    header = artifact_validator.normalize_practical_table_header(
        rows[0], artifact_validator.PRACTICAL_CODE_VERSION_GATE_HEADER_ALIASES
    )
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
        latest_artifacts = state.get("latest_artifacts")
        configured_canonical_paths: list[str] = []
        if isinstance(latest_artifacts, dict):
            configured_value = latest_artifacts.get("canonical_test_cases")
            if isinstance(configured_value, str):
                configured_canonical_paths.append(configured_value)
            elif isinstance(configured_value, list):
                configured_canonical_paths.extend(
                    item for item in configured_value if isinstance(item, str)
                )
        canonical_test_case_paths = {
            normalized_path(value).lstrip("./")
            for value in configured_canonical_paths
            if normalized_path(value)
        }
        canonical_test_case_paths.add(
            normalized_path(f"test-cases/{scope_slug}.md")
        )
        descriptors.append(
            ScopeDescriptor(
                scope_id=scope_id,
                handoff_dir=handoff_dir,
                scope_slug=scope_slug,
                workflow_path=workflow_path,
                canonical_test_case_paths=tuple(sorted(canonical_test_case_paths)),
            )
        )
    return descriptors, issues


def review_subject_artifacts(
    descriptors: Iterable[ScopeDescriptor],
    *,
    ft_package_root: Path,
    review_mode: str,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Resolve and hash the artifact which the reviewer is asked to assess.

    Controller state and review input have different ownership.  The former is
    snapshotted for recovery; the latter must remain byte-identical until the
    verdict is finalized.  Hashing the reviewed matrix or TC baseline prevents
    a later state update from treating a verdict for older content as current.
    """

    artifact_key = "test_design_matrix" if review_mode == "matrix_review" else "canonical_test_cases"
    artifact_role = "test-design-matrix" if review_mode == "matrix_review" else "canonical-test-cases"
    subjects: dict[str, dict[str, str]] = {}
    issues: list[str] = []
    for descriptor in descriptors:
        try:
            state = artifact_validator.parse_workflow_state(descriptor.workflow_path)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            issues.append(f"scope {descriptor.scope_id}: cannot resolve review subject: {exc}")
            continue
        latest = state.get("latest_artifacts")
        configured_values: list[str] = []
        if isinstance(latest, dict):
            value = latest.get(artifact_key)
            if isinstance(value, str):
                configured_values.append(value)
            elif isinstance(value, list):
                configured_values.extend(item for item in value if isinstance(item, str))
        conventional = (
            ft_package_root / "work" / "practical" / descriptor.scope_slug / "test-design-matrix.md"
            if review_mode == "matrix_review"
            else ft_package_root / "test-cases" / f"{descriptor.scope_slug}.md"
        )
        candidates: list[Path] = []
        for value in configured_values:
            resolved = artifact_validator.resolve_artifact_path(
                value, descriptor.workflow_path, ft_package_root, ft_package_root
            )
            if resolved is not None:
                candidates.append(resolved)
        candidates.append(conventional.resolve())
        subject = next(
            (candidate for candidate in candidates if candidate.is_file() and is_within(candidate, ft_package_root)),
            None,
        )
        if subject is None:
            issues.append(
                f"scope {descriptor.scope_id}: {artifact_role} is missing or outside FT package root"
            )
            continue
        subjects[descriptor.scope_id] = {
            "role": artifact_role,
            "source_path": subject.resolve().as_posix(),
            "sha256": sha256_file(subject),
        }
    return subjects, issues


def verify_review_subject_artifacts(
    receipt: dict[str, Any],
    *,
    descriptors: Iterable[ScopeDescriptor],
    ft_package_root: Path,
    review_mode: str,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Prove that review input still matches the launch receipt."""

    current, issues = review_subject_artifacts(
        descriptors, ft_package_root=ft_package_root, review_mode=review_mode
    )
    expected = receipt.get("review_subject_artifacts_by_scope")
    if not isinstance(expected, dict):
        return current, [*issues, "review launch receipt lacks hash-bound review subject artifacts"]
    for descriptor in descriptors:
        expected_item = expected.get(descriptor.scope_id)
        actual_item = current.get(descriptor.scope_id)
        if not isinstance(expected_item, dict) or actual_item is None:
            issues.append(f"scope {descriptor.scope_id}: review subject hash binding is missing")
            continue
        expected_path = str(expected_item.get("source_path") or "")
        expected_hash = str(expected_item.get("sha256") or "").casefold()
        if (
            expected_item.get("role") != actual_item["role"]
            or not expected_path
            or not paths_equal(expected_path, actual_item["source_path"])
            or expected_hash != actual_item["sha256"].casefold()
        ):
            issues.append(f"scope {descriptor.scope_id}: review subject changed after launch preflight")
    return current, issues


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
    normalized = normalized_path(path_text).lstrip("./")
    for descriptor in descriptors:
        handoff_relative = descriptor.handoff_dir.relative_to(ft_package_root).as_posix()
        practical_relative = (ft_package_root / "work" / "practical" / descriptor.scope_slug).relative_to(ft_package_root).as_posix()
        if normalized == normalized_path(handoff_relative) or normalized.startswith(f"{normalized_path(handoff_relative)}/"):
            return descriptor.scope_id
        if normalized == normalized_path(practical_relative) or normalized.startswith(f"{normalized_path(practical_relative)}/"):
            return descriptor.scope_id
        if normalized in descriptor.canonical_test_case_paths:
            return descriptor.scope_id
    handoff_match = re.search(r"(?:^|/)work/stage-handoffs/(\d{2})-", normalized)
    return handoff_match.group(1) if handoff_match else None


def validator_error_partition_key(
    finding: dict[str, Any],
    descriptors: list[ScopeDescriptor],
    ft_package_root: Path,
    summary_path: Path | None,
) -> str:
    """Classify a validator error without letting another scope block review.

    The exact summary passed to preflight is controller-owned current state.  A
    stale summary or handoff under another scope is external package debt, even
    when its validator category is ``practical-stage-summary``.  Orphaned
    practical artifacts are external as well: they need repair, but cannot make
    a clean selected scope endlessly wait for unrelated history.
    """

    requested_ids = {item.scope_id for item in descriptors}
    ownership_descriptors = all_scope_descriptors(ft_package_root)
    path_text = str(finding.get("path", ""))
    normalized = normalized_path(path_text).lstrip("./")
    if summary_path is not None:
        try:
            summary_relative = summary_path.resolve().relative_to(ft_package_root.resolve()).as_posix()
        except ValueError:
            summary_relative = ""
        if summary_relative and normalized == normalized_path(summary_relative):
            return "scope_relevant"

    owner_scope_id = scope_id_for_finding_path(
        path_text, ownership_descriptors, ft_package_root
    )
    if owner_scope_id in requested_ids:
        return "scope_relevant"
    if owner_scope_id is not None:
        return "external"
    if re.match(r"^work/(?:practical/[^/]+/|stage-handoffs/(?!00-)[^/]+/)", normalized):
        return "external"
    return "package_global"


def relevant_validator_errors(
    findings: Iterable[dict[str, Any]],
    descriptors: list[ScopeDescriptor],
    ft_package_root: Path,
    summary_path: Path | None,
) -> list[str]:
    issues: list[str] = []
    for finding in findings:
        if str(finding.get("severity", "")).casefold() != "error":
            continue
        finding_id = str(finding.get("id", "<missing-id>"))
        path_text = str(finding.get("path", ""))
        bucket = validator_error_partition_key(
            finding, descriptors, ft_package_root, summary_path
        )
        if bucket == "scope_relevant":
            owner_scope_id = scope_id_for_finding_path(
                path_text, all_scope_descriptors(ft_package_root), ft_package_root
            )
            owner_label = (
                f"current scope {owner_scope_id}"
                if owner_scope_id in {item.scope_id for item in descriptors}
                else "current stage summary"
            )
            issues.append(
                f"{finding_id}: {owner_label} error at {path_text or '<missing-path>'}"
            )
        elif bucket == "package_global":
            issues.append(
                f"{finding_id}: package-global or unclassified error at {path_text or '<missing-path>'}"
            )
    return issues


def partition_validator_errors(
    findings: Iterable[dict[str, Any]],
    descriptors: list[ScopeDescriptor],
    ft_package_root: Path,
    summary_path: Path | None = None,
) -> dict[str, list[str]]:
    """Separate current-scope errors from external package debt.

    A reviewer launch must fail closed on errors owned by the selected scope or
    by the package-level summary.  Errors owned by another numbered handoff are
    useful diagnostic context, but must not force a content repair in the
    selected scope.
    """

    result = {"scope_relevant": [], "external": [], "package_global": []}
    for finding in findings:
        if str(finding.get("severity", "")).casefold() != "error":
            continue
        finding_id = str(finding.get("id", "<missing-id>"))
        path_text = str(finding.get("path", ""))
        evidence = f"{finding_id} @ {path_text or '<missing-path>'}"
        bucket = validator_error_partition_key(
            finding, descriptors, ft_package_root, summary_path
        )
        result[bucket].append(evidence)
    return result


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
    review_subjects, review_subject_issues = review_subject_artifacts(
        descriptors,
        ft_package_root=ft_package_root,
        review_mode=review_mode,
    )
    blockers.extend(review_subject_issues)
    checks.append(
        PreflightCheck(
            "review-subject-hash",
            "pass" if not review_subject_issues else "fail",
            f"subjects={len(review_subjects)}; issues={len(review_subject_issues)}",
        )
    )
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
            matrix_review_status = str(state.get("matrix_review_status", "")).strip().casefold()
            if matrix_review_status and matrix_review_status != "matrix-accepted":
                transition_record, transition_issues = artifact_validator.practical_scope_transition_record_for_scope(
                    summary_content,
                    scope_id=descriptor.scope_id,
                    scope_slug=descriptor.scope_slug,
                )
                if transition_issues:
                    blockers.extend(
                        f"scope {descriptor.scope_id}: {issue}"
                        for issue in transition_issues
                    )
                elif transition_record is not None:
                    decision_issues = artifact_validator.practical_scope_transition_decision_issues(
                        transition_record
                    )
                    if decision_issues:
                        blockers.extend(
                            f"scope {descriptor.scope_id}: {issue}"
                            for issue in decision_issues
                        )
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
    validator_partition = partition_validator_errors(
        report.get("findings", []), descriptors, ft_package_root, summary_path
    )
    validator_issues = relevant_validator_errors(
        report.get("findings", []), descriptors, ft_package_root, summary_path
    )
    blockers.extend(validator_issues)
    checks.append(
        PreflightCheck(
            "package-validator",
            "pass" if not validator_issues else "fail",
            "errors="
            f"{sum(1 for item in report.get('findings', []) if item.get('severity') == 'error')}; "
            f"scope_relevant_errors={len(validator_partition['scope_relevant'])}; "
            f"external_errors={len(validator_partition['external'])}; "
            f"package_global_errors={len(validator_partition['package_global'])}",
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
        "controller_artifact_hashes": {
            "summary_sha256": sha256_file(summary_path) if summary_path.is_file() else "",
            "workflow_state_sha256_by_scope": {
                descriptor.scope_id: sha256_file(descriptor.workflow_path)
                for descriptor in descriptors
            },
        },
        "review_subject_artifacts_by_scope": review_subjects,
        "code_branch": current_branch,
        "code_commit": current_commit,
        "checks": [asdict(check) for check in checks],
        "validator_error_partition": validator_partition,
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
        "controller_artifact_hashes",
        "review_subject_artifacts_by_scope",
        "code_branch",
        "code_commit",
    )
    issues = [
        f"receipt {field} differs from current preflight"
        for field in expected_pairs
        if receipt.get(field) != current.get(field)
    ]
    try:
        ft_package_root = Path(str(current["ft_package_root"])).resolve()
        summary_path = Path(str(current["summary_path"])).resolve()
        descriptors, descriptor_issues = scope_descriptors(
            ft_package_root,
            [str(value) for value in current.get("scope_ids", [])],
        )
        issues.extend(descriptor_issues)
        if not descriptor_issues:
            _, snapshot_issues = verify_controller_snapshot(
                receipt,
                ft_package_root=ft_package_root,
                summary_path=summary_path,
                descriptors=descriptors,
            )
            issues.extend(snapshot_issues)
    except (KeyError, TypeError, ValueError) as exc:
        issues.append(f"cannot verify controller recovery snapshot: {exc}")
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
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run the launch gate without writing a receipt or controller snapshot.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected_modes = sum(
        bool(value) for value in (args.output, args.verify_receipt, args.check_only)
    )
    if selected_modes > 1:
        raise SystemExit(
            "error: --output, --verify-receipt and --check-only are mutually exclusive"
        )
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
    if args.output and result["allowed"]:
        output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
        if output_path.exists():
            result["allowed"] = False
            result["status"] = "blocked"
            result["blocking_reasons"].append(
                "review launch receipt already exists; do not replace a prior review attempt"
            )
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                result = materialize_controller_snapshot(result, output_path)
            except (OSError, ValueError) as exc:
                result["allowed"] = False
                result["status"] = "blocked"
                result["blocking_reasons"].append(
                    f"cannot materialize controller recovery snapshot: {exc}"
                )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output and result["allowed"]:
        output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
