from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_agent_artifacts as artifact_validator  # noqa: E402
import practical_review_preflight as review_preflight  # noqa: E402


SUMMARY_CATEGORY = "practical-stage-summary"


@dataclass(frozen=True)
class GitPersistence:
    value: str
    evidence: str


@dataclass(frozen=True)
class SummaryRefresh:
    validator_primary_command: str
    validator_primary_root: str
    validator_supplementary_command: str
    validator_findings_breakdown: str
    validator_errors_count: int
    validator_errors_evidence: str
    validator_warnings_count: int
    validator_warnings_evidence: str
    validator_info_count: int
    validator_info_evidence: str
    git_persistence: str
    git_persistence_evidence: str
    validator_scope_errors_count: int | None = None
    validator_scope_errors_evidence: str = "not-applicable"
    validator_external_errors_count: int | None = None
    validator_external_errors_evidence: str = "not-applicable"


def _relative_to_root(root: Path, path: Path) -> str:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def detect_git_persistence(root: Path, summary_path: Path) -> GitPersistence:
    root = root.resolve()
    summary_path = summary_path if summary_path.is_absolute() else root / summary_path
    rel = _relative_to_root(root, summary_path)

    ignored = _run_git(root, ["check-ignore", "-v", "--", rel])
    if ignored.returncode == 0:
        evidence = " ".join(ignored.stdout.strip().split())
        return GitPersistence("ignored-by-git", evidence or f"git check-ignore: {rel}")

    tracked = _run_git(root, ["ls-files", "--error-unmatch", "--", rel])
    if tracked.returncode == 0:
        return GitPersistence("tracked", f"git ls-files: {rel}")

    inside_worktree = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if inside_worktree.returncode != 0:
        return GitPersistence("not-applicable", "not a git worktree")

    return GitPersistence("not-applicable", f"not tracked and not ignored: {rel}")


def summarize_validator_findings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    counted = [
        finding
        for finding in findings
        if str(finding.get("category", "")) != SUMMARY_CATEGORY
    ]
    error_ids = sorted(
        {
            str(finding.get("id", "<missing-id>"))
            for finding in counted
            if finding.get("severity") == "error"
        }
    )
    warning_ids = sorted(
        {
            str(finding.get("id", "<missing-id>"))
            for finding in counted
            if finding.get("severity") == "warning"
        }
    )
    info_ids = sorted(
        {
            str(finding.get("id", "<missing-id>"))
            for finding in counted
            if finding.get("severity") == "info"
        }
    )
    return {
        "validator_errors_count": len(
            [finding for finding in counted if finding.get("severity") == "error"]
        ),
        "validator_errors_evidence": "; ".join(error_ids) if error_ids else "not-applicable",
        "validator_warnings_count": len(
            [finding for finding in counted if finding.get("severity") == "warning"]
        ),
        "validator_warnings_evidence": "; ".join(warning_ids)
        if warning_ids
        else "not-applicable",
        "validator_info_count": len(
            [finding for finding in counted if finding.get("severity") == "info"]
        ),
        "validator_info_evidence": "; ".join(info_ids) if info_ids else "not-applicable",
    }


def classify_validator_finding(finding: dict[str, Any]) -> str:
    finding_id = str(finding.get("id", "")).lower()
    category = str(finding.get("category", "")).lower()
    text = " ".join(
        str(finding.get(key, ""))
        for key in ("id", "category", "title", "details", "recommended_move")
    ).lower()

    if any(token in text for token in ("path-resolution", "root-selection", "wrong package root")):
        return "validator_path_resolution"
    if "profile path not found" in text or "path not found" in text:
        return "validator_path_resolution"
    if "test-case" in category or "test-case" in finding_id or finding_id.startswith("production-"):
        return "tc_quality"
    if any(
        token in category
        for token in (
            "workflow",
            "practical",
            "writer",
            "review",
            "matrix",
            "coverage",
            "dictionary",
            "session",
            "decision",
        )
    ):
        return "process_artifact"
    return "unrelated_repo"


def format_validator_findings_breakdown(findings: list[dict[str, Any]]) -> str:
    counts = {
        "tc_quality": 0,
        "process_artifact": 0,
        "validator_path_resolution": 0,
        "unrelated_repo": 0,
    }
    for finding in findings:
        if str(finding.get("category", "")) == SUMMARY_CATEGORY:
            continue
        if str(finding.get("severity", "")).lower() not in {"warning", "error"}:
            continue
        counts[classify_validator_finding(finding)] += 1
    return "; ".join(f"{name}={counts[name]}" for name in counts)


def build_refresh(
    root: Path,
    summary_path: Path,
    scope_ids: list[str] | None = None,
) -> SummaryRefresh:
    root = root.resolve()
    summary_abs = summary_path if summary_path.is_absolute() else root / summary_path
    primary_root = artifact_validator.ft_package_root_for_path(summary_abs) or root
    primary_root = primary_root.resolve()
    primary_root_display = _relative_to_root(root, primary_root)
    report = artifact_validator.validate(primary_root)
    validator_summary = summarize_validator_findings(report.get("findings", []))
    validator_findings_breakdown = format_validator_findings_breakdown(
        report.get("findings", [])
    )
    git_persistence = detect_git_persistence(root, summary_path)
    scope_error_count: int | None = None
    scope_error_evidence = "not-applicable"
    external_error_count: int | None = None
    external_error_evidence = "not-applicable"
    if scope_ids:
        descriptors, descriptor_issues = review_preflight.scope_descriptors(
            primary_root, scope_ids
        )
        if descriptor_issues:
            scope_error_count = len(descriptor_issues)
            scope_error_evidence = "; ".join(descriptor_issues)
            external_error_count = 0
        else:
            partition = review_preflight.partition_validator_errors(
                report.get("findings", []), descriptors, primary_root
            )
            scope_error_count = len(partition["scope_relevant"]) + len(
                partition["package_global"]
            )
            scope_error_evidence = "; ".join(
                partition["scope_relevant"] + partition["package_global"]
            ) or "not-applicable"
            external_error_count = len(partition["external"])
            external_error_evidence = "; ".join(partition["external"]) or "not-applicable"
    supplementary_command = (
        f"python scripts/validate_agent_artifacts.py --root {_relative_to_root(root, root)} --json"
        if root != primary_root
        else "not-run"
    )
    return SummaryRefresh(
        validator_primary_command=(
            f"python scripts/validate_agent_artifacts.py --root {primary_root_display} --json"
        ),
        validator_primary_root=primary_root.as_posix(),
        validator_supplementary_command=supplementary_command,
        validator_findings_breakdown=validator_findings_breakdown,
        validator_errors_count=int(validator_summary["validator_errors_count"]),
        validator_errors_evidence=str(validator_summary["validator_errors_evidence"]),
        validator_warnings_count=int(validator_summary["validator_warnings_count"]),
        validator_warnings_evidence=str(validator_summary["validator_warnings_evidence"]),
        validator_info_count=int(validator_summary["validator_info_count"]),
        validator_info_evidence=str(validator_summary["validator_info_evidence"]),
        git_persistence=git_persistence.value,
        git_persistence_evidence=git_persistence.evidence,
        validator_scope_errors_count=scope_error_count,
        validator_scope_errors_evidence=scope_error_evidence,
        validator_external_errors_count=external_error_count,
        validator_external_errors_evidence=external_error_evidence,
    )


def _cell(value: object) -> str:
    return str(value).replace("|", "/").replace("`", "'").strip()


def format_field_rows(refresh: SummaryRefresh) -> str:
    rows = [
        ("validator_primary_command", refresh.validator_primary_command),
        ("validator_primary_root", refresh.validator_primary_root),
        ("validator_supplementary_command", refresh.validator_supplementary_command),
        ("validator_findings_breakdown", refresh.validator_findings_breakdown),
        ("validator_errors_count", refresh.validator_errors_count),
        ("validator_errors_evidence", refresh.validator_errors_evidence),
        ("validator_warnings_count", refresh.validator_warnings_count),
        ("validator_warnings_evidence", refresh.validator_warnings_evidence),
        ("validator_info_count", refresh.validator_info_count),
        ("validator_info_evidence", refresh.validator_info_evidence),
        ("git_persistence", refresh.git_persistence),
        ("git_persistence_evidence", refresh.git_persistence_evidence),
    ]
    if refresh.validator_scope_errors_count is not None:
        rows.extend(
            [
                ("validator_scope_errors_count", refresh.validator_scope_errors_count),
                ("validator_scope_errors_evidence", refresh.validator_scope_errors_evidence),
                ("validator_external_errors_count", refresh.validator_external_errors_count),
                ("validator_external_errors_evidence", refresh.validator_external_errors_evidence),
            ]
        )
    return "\n".join(f"| {name} | `{_cell(value)}` |" for name, value in rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print fresh fields for practical-stage-summary.md."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--scope-id", action="append")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--print-fields", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    refresh = build_refresh(args.root, args.summary, args.scope_id)

    if args.as_json:
        print(json.dumps(asdict(refresh), ensure_ascii=False, indent=2))
    if args.print_fields or not args.as_json:
        print(format_field_rows(refresh))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
