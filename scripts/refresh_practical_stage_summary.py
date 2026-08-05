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


SUMMARY_CATEGORY = "practical-stage-summary"


@dataclass(frozen=True)
class GitPersistence:
    value: str
    evidence: str


@dataclass(frozen=True)
class SummaryRefresh:
    validator_errors_count: int
    validator_errors_evidence: str
    validator_warnings_count: int
    validator_warnings_evidence: str
    git_persistence: str
    git_persistence_evidence: str


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
    }


def build_refresh(root: Path, summary_path: Path) -> SummaryRefresh:
    root = root.resolve()
    report = artifact_validator.validate(root)
    validator_summary = summarize_validator_findings(report.get("findings", []))
    git_persistence = detect_git_persistence(root, summary_path)
    return SummaryRefresh(
        validator_errors_count=int(validator_summary["validator_errors_count"]),
        validator_errors_evidence=str(validator_summary["validator_errors_evidence"]),
        validator_warnings_count=int(validator_summary["validator_warnings_count"]),
        validator_warnings_evidence=str(validator_summary["validator_warnings_evidence"]),
        git_persistence=git_persistence.value,
        git_persistence_evidence=git_persistence.evidence,
    )


def _cell(value: object) -> str:
    return str(value).replace("|", "/").replace("`", "'").strip()


def format_field_rows(refresh: SummaryRefresh) -> str:
    rows = [
        ("validator_errors_count", refresh.validator_errors_count),
        ("validator_errors_evidence", refresh.validator_errors_evidence),
        ("validator_warnings_count", refresh.validator_warnings_count),
        ("validator_warnings_evidence", refresh.validator_warnings_evidence),
        ("git_persistence", refresh.git_persistence),
        ("git_persistence_evidence", refresh.git_persistence_evidence),
    ]
    return "\n".join(f"| {name} | `{_cell(value)}` |" for name, value in rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print fresh fields for practical-stage-summary.md."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--print-fields", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    refresh = build_refresh(args.root, args.summary)

    if args.as_json:
        print(json.dumps(asdict(refresh), ensure_ascii=False, indent=2))
    if args.print_fields or not args.as_json:
        print(format_field_rows(refresh))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
