from __future__ import annotations

import argparse
import json
import re
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
    source_row_counts: str = "not-applicable"
    validator_scope_errors_count: int | None = None
    validator_scope_errors_evidence: str = "not-applicable"
    validator_external_errors_count: int | None = None
    validator_external_errors_evidence: str = "not-applicable"
    # The canonical routing count intentionally omits practical-stage-summary
    # self-checks to avoid a circular handoff gate. Keep the raw count visible
    # nevertheless, so a user can reconcile this summary with the validator CLI.
    validator_raw_errors_count: int = 0
    validator_summary_self_check_errors_count: int = 0
    validator_summary_self_check_errors_evidence: str = "not-applicable"


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


def routing_validator_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return findings that are eligible for a next-stage routing decision."""

    return [
        finding
        for finding in findings
        if str(finding.get("category", "")) != SUMMARY_CATEGORY
    ]


def summarize_validator_findings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    counted = routing_validator_findings(findings)
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


def summarize_validator_error_layers(
    findings: list[dict[str, Any]],
    summary_relative_path: str,
) -> dict[str, Any]:
    """Expose raw error output separately from routing-safe summary self-checks."""

    # Report-consistency findings are emitted only after each summary has already
    # been evaluated.  Feeding those generated ``validator-*`` findings back
    # into the refresh makes the declared count chase its own output instead of
    # reaching the same fixed point used by the validator's summary check.
    refresh_self_checks = {
        "practical-stage-summary-validator-error-count-invalid",
        "practical-stage-summary-validator-error-count-stale",
        "practical-stage-summary-validator-error-layers-missing",
        "practical-stage-summary-validator-error-layer-count-mismatch",
        "practical-stage-summary-validator-evidence-stale",
        "practical-stage-summary-validator-info-count-invalid",
        "practical-stage-summary-validator-info-count-stale",
        "practical-stage-summary-validator-raw-error-count-invalid",
        "practical-stage-summary-validator-raw-error-count-stale",
        "practical-stage-summary-validator-self-check-layer-invalid",
        "practical-stage-summary-validator-self-check-layer-missing",
        "practical-stage-summary-validator-self-check-layer-stale",
        "practical-stage-summary-validator-warning-count-invalid",
        "practical-stage-summary-validator-warning-count-stale",
    }
    def is_visible_to_target_summary(finding: dict[str, Any]) -> bool:
        finding_id = str(finding.get("id", ""))
        if finding_id not in refresh_self_checks:
            return True
        # The validator checks summaries in path order.  A target summary sees
        # consistency findings already emitted for preceding summaries, but not
        # its own or later findings.  Mirror that order here.
        finding_path = str(finding.get("path", "")).replace("\\", "/")
        return finding_path < summary_relative_path

    raw_errors = [
        finding
        for finding in findings
        if finding.get("severity") == "error" and is_visible_to_target_summary(finding)
    ]
    summary_self_checks = [
        finding
        for finding in raw_errors
        if str(finding.get("category", "")) == SUMMARY_CATEGORY
    ]

    def evidence(rows: list[dict[str, Any]]) -> str:
        items = sorted(
            {
                f"{finding.get('id', '<missing-id>')} @ {finding.get('path', '<missing-path>')}"
                for finding in rows
            }
        )
        return "; ".join(items) if items else "not-applicable"

    return {
        "validator_raw_errors_count": len(raw_errors),
        "validator_summary_self_check_errors_count": len(summary_self_checks),
        "validator_summary_self_check_errors_evidence": evidence(summary_self_checks),
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


def source_row_counts_for_scopes(ft_root: Path, scope_ids: list[str] | None) -> str:
    """Return source-row counts from the linked current inventories."""

    if not scope_ids:
        return "not-applicable"
    counts: list[str] = []
    handoff_root = ft_root / "work" / "stage-handoffs"
    for scope_id in scope_ids:
        handoffs = sorted(path for path in handoff_root.glob(f"{scope_id}-*") if path.is_dir())
        if len(handoffs) != 1:
            return "not-applicable"
        workflow_path = handoffs[0] / "workflow-state.yaml"
        try:
            state = artifact_validator.parse_workflow_state(workflow_path)
        except (FileNotFoundError, UnicodeDecodeError):
            return "not-applicable"
        inventory_paths = artifact_validator.workflow_artifact_paths_by_name(
            state,
            workflow_path,
            ft_root,
            ft_root,
            "source-row-inventory.md",
        )
        if len(inventory_paths) != 1:
            return "not-applicable"
        try:
            count = len(
                artifact_validator.parsed_source_row_inventory_rows(
                    inventory_paths[0].read_text(encoding="utf-8")
                )
            )
        except UnicodeDecodeError:
            return "not-applicable"
        counts.append(f"{scope_id}={count}")
    return "; ".join(counts)


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
    report_findings = report.get("findings", [])
    validator_summary = summarize_validator_findings(report_findings)
    validator_error_layers = summarize_validator_error_layers(
        report_findings,
        _relative_to_root(primary_root, summary_abs),
    )
    routing_findings = routing_validator_findings(report_findings)
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
                routing_findings, descriptors, primary_root, summary_abs
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
        source_row_counts=source_row_counts_for_scopes(primary_root, scope_ids),
        validator_scope_errors_count=scope_error_count,
        validator_scope_errors_evidence=scope_error_evidence,
        validator_external_errors_count=external_error_count,
        validator_external_errors_evidence=external_error_evidence,
        validator_raw_errors_count=int(validator_error_layers["validator_raw_errors_count"]),
        validator_summary_self_check_errors_count=int(
            validator_error_layers["validator_summary_self_check_errors_count"]
        ),
        validator_summary_self_check_errors_evidence=str(
            validator_error_layers["validator_summary_self_check_errors_evidence"]
        ),
    )


def _cell(value: object) -> str:
    return str(value).replace("|", "/").replace("`", "'").strip()


def format_field_rows(refresh: SummaryRefresh) -> str:
    rows = [
        ("validator_primary_command", refresh.validator_primary_command),
        ("validator_primary_root", refresh.validator_primary_root),
        ("validator_supplementary_command", refresh.validator_supplementary_command),
        ("validator_findings_breakdown", refresh.validator_findings_breakdown),
        ("validator_raw_errors_count", refresh.validator_raw_errors_count),
        ("validator_errors_count", refresh.validator_errors_count),
        (
            "validator_summary_self_check_errors_count",
            refresh.validator_summary_self_check_errors_count,
        ),
        (
            "validator_summary_self_check_errors_evidence",
            refresh.validator_summary_self_check_errors_evidence,
        ),
        ("validator_errors_evidence", refresh.validator_errors_evidence),
        ("validator_warnings_count", refresh.validator_warnings_count),
        ("validator_warnings_evidence", refresh.validator_warnings_evidence),
        ("validator_info_count", refresh.validator_info_count),
        ("validator_info_evidence", refresh.validator_info_evidence),
        ("git_persistence", refresh.git_persistence),
        ("git_persistence_evidence", refresh.git_persistence_evidence),
        ("source_row_counts", refresh.source_row_counts),
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


SUMMARY_FIELD_ROW_RE = re.compile(
    r"^\|\s*(?P<field>[a-z0-9_]+)\s*\|\s*`[^`]*`\s*\|\s*$",
    flags=re.MULTILINE,
)


def refreshed_field_rows(refresh: SummaryRefresh) -> dict[str, str]:
    """Return canonical Markdown rows keyed by practical-summary field name."""

    rows: dict[str, str] = {}
    for row in format_field_rows(refresh).splitlines():
        match = SUMMARY_FIELD_ROW_RE.fullmatch(row)
        if match is None:  # Defensive: format_field_rows is a local contract.
            raise ValueError(f"cannot parse generated summary row: {row}")
        rows[match.group("field")] = row
    return rows


def replace_refreshed_fields(summary_text: str, refresh: SummaryRefresh) -> str:
    """Replace every generated validator row without touching narrative fields.

    A stage summary contains controller decisions as well as derived validator
    evidence.  Only the latter is safe to update mechanically.  Fail closed if
    an expected field is absent instead of silently producing a partly stale
    handoff.
    """

    expected_rows = refreshed_field_rows(refresh)
    found_fields = {
        match.group("field") for match in SUMMARY_FIELD_ROW_RE.finditer(summary_text)
    }
    missing = sorted(set(expected_rows) - found_fields)
    if missing:
        raise ValueError(
            "practical stage summary misses generated fields: " + ", ".join(missing)
        )

    return SUMMARY_FIELD_ROW_RE.sub(
        lambda match: expected_rows.get(match.group("field"), match.group(0)),
        summary_text,
    )


def refresh_summary_file(
    root: Path,
    summary_path: Path,
    scope_ids: list[str] | None = None,
    *,
    max_passes: int = 3,
) -> bool:
    """Write validator-derived rows until their self-check reaches a fixed point.

    The validator checks the summary itself.  Therefore a first write can remove
    stale-summary findings and change the raw count once more.  A bounded fixed
    point prevents the controller from reporting the pre-write count as final.
    """

    if max_passes < 1:
        raise ValueError("max_passes must be positive")
    summary_abs = summary_path if summary_path.is_absolute() else root / summary_path
    summary_abs = summary_abs.resolve()
    changed = False
    for _ in range(max_passes):
        before = summary_abs.read_text(encoding="utf-8")
        after = replace_refreshed_fields(
            before, build_refresh(root, summary_abs, scope_ids)
        )
        if after == before:
            return changed
        summary_abs.write_text(after, encoding="utf-8")
        changed = True
    final = summary_abs.read_text(encoding="utf-8")
    expected = replace_refreshed_fields(
        final, build_refresh(root, summary_abs, scope_ids)
    )
    if expected != final:
        raise RuntimeError(
            "practical stage summary did not reach a stable validator refresh"
        )
    return changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print fresh fields for practical-stage-summary.md."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--scope-id", action="append")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--print-fields", action="store_true")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Update only generated validator fields and verify a stable result.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.write:
        refresh_summary_file(args.root, args.summary, args.scope_id)
    refresh = build_refresh(args.root, args.summary, args.scope_id)

    if args.as_json:
        print(json.dumps(asdict(refresh), ensure_ascii=False, indent=2))
    if args.print_fields or not args.as_json:
        print(format_field_rows(refresh))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
