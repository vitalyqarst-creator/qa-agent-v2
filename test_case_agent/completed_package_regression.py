from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.test_case_update_plan import load_test_case_update_plan
from test_case_agent.writer_dry_run_proposals import TC_HEADING_RE, TRACEABILITY_LABELS, load_writer_dry_run_proposal
from test_case_agent.writer_proposal_review import load_writer_proposal_review
from test_case_agent.writer_traceability_post_apply_validation import (
    load_writer_traceability_post_apply_validation,
)
from test_case_agent.writer_traceability_update_apply import load_writer_traceability_update_apply_report

CREATED_BY_TOOL = "test_case_agent.completed_package_regression"
REGRESSION_PREFIX = "completed-package-regression"

CheckStatus = Literal["pass", "warning", "failed", "blocked"]
RegressionStatus = Literal["pass", "pass-with-warnings", "failed", "blocked"]

REQ_RE = re.compile(r"\bREQ-AUTOFIN-[A-Z0-9]+\b")
LEGACY_RE = re.compile(r"\b(?:ATOM-\d+|SRC-\d+|GAP-\d+|WP-\d+|DICT-[A-Z0-9-]+|BSR\s+\d+)\b")


@dataclass(frozen=True)
class CompletedPackageRegressionCheck:
    check_id: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompletedPackageRegressionCheck":
        return cls(
            check_id=str(data["check_id"]),
            status=data["status"],
            message=str(data["message"]),
            details=dict(data.get("details") or {}),
        )


@dataclass
class CompletedPackageRegressionReport:
    regression_status: RegressionStatus
    completed_packages: list[str]
    validated_test_cases: list[str]
    final_state_valid_count: int
    safe_for_next_stage_count: int
    old_refs_absent: bool
    new_refs_present: bool
    duplicate_req_refs_found: bool
    regressions_found: list[str]
    checks: list[CompletedPackageRegressionCheck]
    failed_checks: list[str]
    warnings: list[str]
    blocking_reasons: list[str]
    git_state_summary: dict[str, Any]
    input_paths: dict[str, Any]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "regression_status": self.regression_status,
            "completed_packages": self.completed_packages,
            "validated_test_cases": self.validated_test_cases,
            "final_state_valid_count": self.final_state_valid_count,
            "safe_for_next_stage_count": self.safe_for_next_stage_count,
            "old_refs_absent": self.old_refs_absent,
            "new_refs_present": self.new_refs_present,
            "duplicate_req_refs_found": self.duplicate_req_refs_found,
            "regressions_found": self.regressions_found,
            "checks": [check.to_dict() for check in self.checks],
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "git_state_summary": self.git_state_summary,
            "input_paths": self.input_paths,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompletedPackageRegressionReport":
        return cls(
            regression_status=data["regression_status"],
            completed_packages=list(data.get("completed_packages") or []),
            validated_test_cases=list(data.get("validated_test_cases") or []),
            final_state_valid_count=int(data.get("final_state_valid_count") or 0),
            safe_for_next_stage_count=int(data.get("safe_for_next_stage_count") or 0),
            old_refs_absent=bool(data.get("old_refs_absent")),
            new_refs_present=bool(data.get("new_refs_present")),
            duplicate_req_refs_found=bool(data.get("duplicate_req_refs_found")),
            regressions_found=list(data.get("regressions_found") or []),
            checks=[CompletedPackageRegressionCheck.from_dict(item) for item in data.get("checks", [])],
            failed_checks=list(data.get("failed_checks") or []),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            git_state_summary=dict(data.get("git_state_summary") or {}),
            input_paths=dict(data.get("input_paths") or {}),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


@dataclass(frozen=True)
class _CompletedPackageSpec:
    package_id: str
    file_path: str
    tc_ids: list[str]
    new_refs: list[str]
    old_refs: list[str]


DEFAULT_COMPLETED_PACKAGE_SPECS: tuple[_CompletedPackageSpec, ...] = (
    _CompletedPackageSpec(
        package_id="WPKG-000002",
        file_path="fts/AutoFin/test-cases/14-application-card-client-contacts-and-extra-info.md",
        tc_ids=["TC-ACCEI-012", "TC-ACCEI-013"],
        new_refs=["REQ-AUTOFIN-339239217ED5", "REQ-AUTOFIN-75E43AC628D5"],
        old_refs=["REQ-AUTOFIN-3D1FEBD741A1", "REQ-AUTOFIN-63CC9F1AC781"],
    ),
    _CompletedPackageSpec(
        package_id="WPKG-000003",
        file_path="fts/AutoFin/test-cases/section-4.2-applications-menu-search.md",
        tc_ids=["TC-AMSR-012"],
        new_refs=["REQ-AUTOFIN-FC1ED982E572", "REQ-AUTOFIN-DDBC8DCB97AF"],
        old_refs=["REQ-AUTOFIN-03B83DF07255", "REQ-AUTOFIN-EDDF1133C9DF"],
    ),
)


def build_completed_package_regression(
    *,
    work_dir: Path,
    test_cases_dir: Path,
    update_plan_path: Path,
    old_registry_path: Path,
    new_registry_path: Path,
    package_ids: list[str] | None = None,
    workspace_root: Path | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> CompletedPackageRegressionReport:
    workspace_root = Path.cwd() if workspace_root is None else Path(workspace_root)
    work_dir = Path(work_dir)
    test_cases_dir = Path(test_cases_dir)
    package_ids = package_ids or ["WPKG-000002", "WPKG-000003"]
    specs = [spec for spec in DEFAULT_COMPLETED_PACKAGE_SPECS if spec.package_id in set(package_ids)]
    input_paths = {
        "work_dir": str(work_dir),
        "test_cases_dir": str(test_cases_dir),
        "update_plan_path": str(update_plan_path),
        "old_registry_path": str(old_registry_path),
        "new_registry_path": str(new_registry_path),
        "packages": package_ids,
    }

    checks: list[CompletedPackageRegressionCheck] = []
    warnings: list[str] = []
    blocking_reasons: list[str] = []
    regressions_found: list[str] = []
    validation_reports: dict[str, Any] = {}
    proposals: dict[str, Any] = {}
    reviews: dict[str, Any] = {}
    applies: dict[str, Any] = {}

    for required_path, label in [
        (work_dir, "work dir"),
        (test_cases_dir, "test-cases dir"),
        (update_plan_path, "test-case update plan"),
        (old_registry_path, "old requirements registry"),
        (new_registry_path, "new requirements registry"),
    ]:
        if not Path(required_path).exists():
            blocking_reasons.append(f"{label} is missing: {required_path}")

    for spec in specs:
        paths = _artifact_paths(work_dir, spec.package_id)
        try:
            validation_reports[spec.package_id] = load_writer_traceability_post_apply_validation(paths["validation"])
            proposals[spec.package_id] = load_writer_dry_run_proposal(paths["proposal"])
            reviews[spec.package_id] = load_writer_proposal_review(paths["review"])
            applies[spec.package_id] = load_writer_traceability_update_apply_report(paths["apply"])
        except Exception as exc:  # noqa: BLE001 - report blockers instead of raising.
            blocking_reasons.append(f"{spec.package_id} artifacts cannot be loaded: {exc}")

    update_plan = None
    registry_refs: set[str] = set()
    if not blocking_reasons:
        try:
            update_plan = load_test_case_update_plan(update_plan_path)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"test-case update plan cannot be parsed: {exc}")
        try:
            registry_refs = _load_registry_refs(old_registry_path) | _load_registry_refs(new_registry_path)
        except Exception as exc:  # noqa: BLE001
            blocking_reasons.append(f"requirements registry cannot be parsed: {exc}")

    git_state_summary = _collect_git_state(workspace_root, test_cases_dir, [Path(spec.file_path) for spec in specs])
    if blocking_reasons:
        return _report(
            specs=specs,
            checks=checks,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            regressions_found=regressions_found,
            git_state_summary=git_state_summary,
            input_paths=input_paths,
            created_by_tool=created_by_tool,
        )

    assert update_plan is not None
    for spec in specs:
        validation = validation_reports[spec.package_id]
        proposal = proposals[spec.package_id]
        review = reviews[spec.package_id]
        apply_report = applies[spec.package_id]
        warnings.extend(validation.warnings)
        warnings.extend(proposal.warnings)
        warnings.extend(review.warnings)
        warnings.extend(apply_report.warnings)

        checks.extend(_validation_artifact_checks(spec, validation, proposal, review, apply_report))
        checks.extend(_current_file_checks(spec, workspace_root, test_cases_dir))
        checks.extend(_update_plan_checks(spec, update_plan))
        checks.extend(_registry_checks(spec, registry_refs))
        checks.extend(_proposal_regression_checks(spec, proposal))

    checks.extend(_collateral_checks(specs, workspace_root, test_cases_dir))
    checks.extend(_git_checks(specs, git_state_summary))

    for check in checks:
        if check.status in {"failed", "blocked"}:
            regressions_found.append(check.check_id)

    return _report(
        specs=specs,
        checks=checks,
        warnings=warnings,
        blocking_reasons=[],
        regressions_found=_unique(regressions_found),
        git_state_summary=git_state_summary,
        input_paths=input_paths,
        created_by_tool=created_by_tool,
    )


def write_completed_package_regression(
    report: CompletedPackageRegressionReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    package_suffix = "-".join(report.completed_packages)
    json_path = out_dir / f"{REGRESSION_PREFIX}-{package_suffix}.json"
    markdown_path = out_dir / f"{REGRESSION_PREFIX}-{package_suffix}.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_completed_package_regression_markdown(report), encoding="utf-8", newline="\n")
    return json_path, markdown_path


def load_completed_package_regression(path: Path) -> CompletedPackageRegressionReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Completed package regression root must be a JSON object.")
    return CompletedPackageRegressionReport.from_dict(payload)


def render_completed_package_regression_markdown(report: CompletedPackageRegressionReport) -> str:
    lines = [
        "# Completed Package Regression",
        "",
        "## Summary",
        "",
        f"- Regression status: `{report.regression_status}`",
        f"- Completed packages: `{', '.join(report.completed_packages)}`",
        f"- Validated test cases: `{', '.join(report.validated_test_cases)}`",
        f"- Final state valid count: `{report.final_state_valid_count}`",
        f"- Safe for next stage count: `{report.safe_for_next_stage_count}`",
        f"- Old refs absent: `{str(report.old_refs_absent).lower()}`",
        f"- New refs present: `{str(report.new_refs_present).lower()}`",
        f"- Duplicate REQ refs found: `{str(report.duplicate_req_refs_found).lower()}`",
        f"- Regressions found: `{', '.join(report.regressions_found) or 'none'}`",
        f"- Failed checks: `{', '.join(report.failed_checks) or 'none'}`",
        f"- Warnings count: `{len(report.warnings)}`",
        f"- Blocking reasons count: `{len(report.blocking_reasons)}`",
        "",
        "## Git State",
        "",
        f"- Changed test-case files: `{len(report.git_state_summary.get('changed_test_case_files', []))}`",
        f"- Staged changes empty: `{str(report.git_state_summary.get('cached_diff_empty')).lower()}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.checks:
        lines.append(f"- `{check.status}` `{check.check_id}`: {check.message}")
    if report.regressions_found:
        lines.extend(["", "## Regressions", ""])
        for item in report.regressions_found:
            lines.append(f"- `{item}`")
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in report.warnings:
            lines.append(f"- {warning}")
    if report.blocking_reasons:
        lines.extend(["", "## Blocking Reasons", ""])
        for reason in report.blocking_reasons:
            lines.append(f"- {reason}")
    lines.extend(["", "## Safety", ""])
    lines.append("- Regression is read-only.")
    lines.append("- No `--apply`, patch, `git apply`, or package execution is performed.")
    return "\n".join(lines).rstrip() + "\n"


def _artifact_paths(work_dir: Path, package_id: str) -> dict[str, Path]:
    suffix = f"{package_id}-after-backfill"
    return {
        "validation": work_dir / f"writer-traceability-post-apply-validation-{suffix}.json",
        "proposal": work_dir / f"writer-dry-run-proposal-{suffix}.json",
        "review": work_dir / f"writer-proposal-review-{suffix}.json",
        "apply": work_dir / f"writer-traceability-update-apply-{suffix}.json",
    }


def _validation_artifact_checks(spec: _CompletedPackageSpec, validation: Any, proposal: Any, review: Any, apply_report: Any) -> list[CompletedPackageRegressionCheck]:
    return [
        _check(f"{spec.package_id}.validation_final_state_valid", validation.final_state_valid is True, "post-apply validation final_state_valid is true."),
        _check(f"{spec.package_id}.validation_safe_for_next_stage", validation.safe_for_next_stage is True, "post-apply validation safe_for_next_stage is true."),
        _check(f"{spec.package_id}.validation_failed_checks_empty", not validation.failed_checks, "post-apply validation failed_checks is empty.", {"failed_checks": validation.failed_checks}),
        _check(f"{spec.package_id}.validation_blocking_reasons_empty", not validation.blocking_reasons, "post-apply validation blocking_reasons is empty.", {"blocking_reasons": validation.blocking_reasons}),
        _check(f"{spec.package_id}.validation_git_state_allowed", validation.git_change_state in {"final_state_already_baselined", "uncommitted_expected_change"}, "post-apply validation git_change_state is allowed.", {"git_change_state": validation.git_change_state}),
        _check(f"{spec.package_id}.proposal_package_matches", proposal.package_id == spec.package_id, "writer proposal package_id matches."),
        _check(f"{spec.package_id}.review_safe_for_apply", review.safe_for_controlled_apply is True, "writer review safe_for_controlled_apply is true."),
        _check(f"{spec.package_id}.apply_report_applied", apply_report.apply_status == "applied", "writer apply report status is applied."),
    ]


def _current_file_checks(spec: _CompletedPackageSpec, workspace_root: Path, test_cases_dir: Path) -> list[CompletedPackageRegressionCheck]:
    path = _resolve_file(spec.file_path, workspace_root)
    checks: list[CompletedPackageRegressionCheck] = []
    if not path.exists():
        return [_check(f"{spec.package_id}.target_file_exists", False, "target file exists.", {"file_path": spec.file_path}, blocked=True)]
    if not _is_relative_to(path, _resolve_file(test_cases_dir, workspace_root)):
        return [_check(f"{spec.package_id}.target_file_in_test_cases", False, "target file is inside test-cases dir.", {"file_path": spec.file_path}, blocked=True)]
    text = path.read_text(encoding="utf-8")
    blocks = _tc_blocks(text)
    for tc_id in spec.tc_ids:
        matches = blocks.get(tc_id, [])
        checks.append(_check(f"{spec.package_id}.{tc_id}.tc_block_once", len(matches) == 1, "expected TC block exists exactly once.", {"count": len(matches)}))
        if len(matches) != 1:
            continue
        line = _traceability_line(matches[0])
        checks.append(_check(f"{spec.package_id}.{tc_id}.traceability_line_once", bool(line), "expected TC has exactly one traceability line."))
        if not line:
            continue
        reqs = _req_refs(line)
        legacy_refs = _legacy_refs(line)
        checks.append(_check(f"{spec.package_id}.{tc_id}.new_refs_present", all(_contains_ref(line, ref) for ref in spec.new_refs), "final new REQ refs are present.", {"new_refs": spec.new_refs, "line": line}))
        checks.append(_check(f"{spec.package_id}.{tc_id}.old_refs_absent", not any(_contains_ref(line, ref) for ref in spec.old_refs), "old/intermediate REQ refs are absent.", {"old_refs": spec.old_refs, "line": line}))
        checks.append(_check(f"{spec.package_id}.{tc_id}.legacy_refs_preserved", bool(legacy_refs), "legacy refs are preserved.", {"legacy_refs": legacy_refs}))
        checks.append(_check(f"{spec.package_id}.{tc_id}.no_duplicate_req_refs", len(reqs) == len(set(reqs)), "traceability line has no duplicate REQ refs.", {"req_refs": reqs}))
    return checks


def _update_plan_checks(spec: _CompletedPackageSpec, update_plan: Any) -> list[CompletedPackageRegressionCheck]:
    expected_pairs = {(tc_id, old, new) for tc_id in spec.tc_ids for old, new in zip(spec.old_refs, spec.new_refs)}
    actual_pairs = set()
    bad_actions: list[str] = []
    for item in update_plan.plan_items:
        if item.test_case_id not in set(spec.tc_ids):
            continue
        for old_ref, new_ref in zip(item.old_refs, item.new_refs):
            pair = (item.test_case_id, old_ref, new_ref)
            if pair in expected_pairs:
                actual_pairs.add(pair)
                if item.action != "traceability_update_only":
                    bad_actions.append(item.plan_item_id)
    missing = sorted(expected_pairs - actual_pairs)
    return [
        _check(f"{spec.package_id}.update_plan_completed_mappings_match", not missing, "completed replacements match update plan.", {"missing_mappings": missing, "actual_mappings": sorted(actual_pairs)}),
        _check(f"{spec.package_id}.update_plan_actions_traceability_only", not bad_actions, "completed update-plan items are traceability_update_only.", {"bad_plan_item_ids": bad_actions}),
    ]


def _registry_checks(spec: _CompletedPackageSpec, registry_refs: set[str]) -> list[CompletedPackageRegressionCheck]:
    refs = [*spec.old_refs, *spec.new_refs]
    malformed = [ref for ref in refs if not REQ_RE.fullmatch(ref)]
    missing = [ref for ref in refs if ref.upper() not in registry_refs]
    return [
        _check(f"{spec.package_id}.registry_refs_exist", not missing, "old and final REQ refs exist in requirements registries.", {"missing_refs": missing}),
        _check(f"{spec.package_id}.registry_refs_well_formed", not malformed, "completed REQ refs are well formed.", {"malformed_refs": malformed}),
    ]


def _proposal_regression_checks(spec: _CompletedPackageSpec, proposal: Any) -> list[CompletedPackageRegressionCheck]:
    relevant_missing = [
        item for item in proposal.missing_information
        if any(tc_id in item for tc_id in spec.tc_ids)
    ]
    pending_old_refs = [
        change for change in proposal.proposed_changes
        if change.get("test_case_id") in set(spec.tc_ids)
        and change.get("old_ref") in set(spec.old_refs)
    ]
    stale = bool(pending_old_refs)
    return [
        _check(f"{spec.package_id}.proposal_no_completed_missing_information", not relevant_missing, "completed TCs do not have relevant missing_information.", {"missing_information": relevant_missing}),
        _check(f"{spec.package_id}.proposal_completed_changes_stale_only", not stale, "proposal still contains completed old->new changes and is now stale rather than a TC defect.", {"completed_changes": pending_old_refs}, warning=stale),
    ]


def _collateral_checks(specs: list[_CompletedPackageSpec], workspace_root: Path, test_cases_dir: Path) -> list[CompletedPackageRegressionCheck]:
    checks: list[CompletedPackageRegressionCheck] = []
    target_files = {_resolve_file(spec.file_path, workspace_root) for spec in specs}
    expected_tc_ids = {tc_id for spec in specs for tc_id in spec.tc_ids}
    completed_old_refs = {ref for spec in specs for ref in spec.old_refs}
    for path in target_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for tc_id, blocks in _tc_blocks(text).items():
            if tc_id in expected_tc_ids or len(blocks) != 1:
                continue
            line = _traceability_line(blocks[0])
            if not line:
                continue
            refs = _req_refs(line)
            unexpected_old_refs = sorted(ref for ref in refs if ref in completed_old_refs)
            duplicates = [ref for ref, count in Counter(refs).items() if count > 1]
            checks.append(_check(f"collateral.{tc_id}.no_intermediate_refs", not unexpected_old_refs, "unrelated TC does not contain completed intermediate refs.", {"refs": unexpected_old_refs, "file_path": str(path)}))
            checks.append(_check(f"collateral.{tc_id}.no_duplicate_req_refs", not duplicates, "unrelated TC has no duplicate REQ refs.", {"duplicates": duplicates, "file_path": str(path)}))
    checks.append(_check("collateral.no_unrequested_packages_processed", True, "WPKG-000001/WPKG-000004/WPKG-000005 are not processed by this regression."))
    return checks


def _git_checks(specs: list[_CompletedPackageSpec], git_state: dict[str, Any]) -> list[CompletedPackageRegressionCheck]:
    changed_files = list(git_state.get("changed_test_case_files") or [])
    target_files = {str(Path(spec.file_path)).replace("\\", "/") for spec in specs}
    unexpected = [path for path in changed_files if path not in target_files]
    return [
        _check("git.no_staged_changes", git_state.get("cached_diff_empty") is True, "no staged test-case changes are present.", {"cached_diff": git_state.get("cached_diff", "")}),
        _check("git.changed_files_expected_or_clean", not unexpected, "git state is clean or changed files are limited to completed package files.", {"changed_files": changed_files, "unexpected_changed_files": unexpected}),
    ]


def _report(
    *,
    specs: list[_CompletedPackageSpec],
    checks: list[CompletedPackageRegressionCheck],
    warnings: list[str],
    blocking_reasons: list[str],
    regressions_found: list[str],
    git_state_summary: dict[str, Any],
    input_paths: dict[str, Any],
    created_by_tool: str,
) -> CompletedPackageRegressionReport:
    completed_packages = [spec.package_id for spec in specs]
    validated_test_cases = [tc_id for spec in specs for tc_id in spec.tc_ids]
    failed_checks = [check.check_id for check in checks if check.status == "failed"]
    blocked_checks = [check.check_id for check in checks if check.status == "blocked"]
    blocking_reasons = _unique([*blocking_reasons, *blocked_checks])
    warnings = _unique([*warnings, *[check.check_id for check in checks if check.status == "warning"]])
    final_state_valid_count = sum(1 for check in checks if check.check_id.endswith(".validation_final_state_valid") and check.status == "pass")
    safe_for_next_stage_count = sum(1 for check in checks if check.check_id.endswith(".validation_safe_for_next_stage") and check.status == "pass")
    old_refs_absent = all(check.status == "pass" for check in checks if check.check_id.endswith(".old_refs_absent")) and bool(checks)
    new_refs_present = all(check.status == "pass" for check in checks if check.check_id.endswith(".new_refs_present")) and bool(checks)
    duplicate_req_refs_found = any(check.status != "pass" for check in checks if check.check_id.endswith(".no_duplicate_req_refs"))
    if blocking_reasons:
        status: RegressionStatus = "blocked"
    elif failed_checks or regressions_found:
        status = "failed"
    elif warnings:
        status = "pass-with-warnings"
    else:
        status = "pass"
    return CompletedPackageRegressionReport(
        regression_status=status,
        completed_packages=completed_packages,
        validated_test_cases=validated_test_cases,
        final_state_valid_count=final_state_valid_count,
        safe_for_next_stage_count=safe_for_next_stage_count,
        old_refs_absent=old_refs_absent,
        new_refs_present=new_refs_present,
        duplicate_req_refs_found=duplicate_req_refs_found,
        regressions_found=_unique(regressions_found),
        checks=checks,
        failed_checks=failed_checks,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        git_state_summary=git_state_summary,
        input_paths=input_paths,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _collect_git_state(workspace_root: Path, test_cases_dir: Path, target_files: list[Path]) -> dict[str, Any]:
    test_cases_git_path = _git_relative_path(workspace_root, _resolve_file(test_cases_dir, workspace_root))
    status = _run_git(workspace_root, ["status", "--short", "--", test_cases_git_path])
    cached_diff = _run_git(workspace_root, ["diff", "--cached", "--", test_cases_git_path])
    target_diffs = {}
    for file_path in target_files:
        git_path = _git_relative_path(workspace_root, _resolve_file(file_path, workspace_root))
        target_diffs[git_path] = _run_git(workspace_root, ["diff", "--", git_path])["stdout"]
    return {
        "status_short": status["stdout"],
        "changed_test_case_files": _changed_files_from_status(status["stdout"]),
        "cached_diff": cached_diff["stdout"],
        "cached_diff_empty": cached_diff["stdout"] == "",
        "target_diffs": target_diffs,
    }


def _tc_blocks(text: str) -> dict[str, list[str]]:
    lines = text.splitlines(keepends=True)
    headings: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line)
        if match:
            headings.append((match.group(2), index))
    result: dict[str, list[str]] = {}
    for offset, (tc_id, start) in enumerate(headings):
        end = headings[offset + 1][1] if offset + 1 < len(headings) else len(lines)
        result.setdefault(tc_id, []).append("".join(lines[start:end]))
    return result


def _traceability_line(block: str) -> str:
    lines = [line.strip() for line in block.splitlines() if _is_traceability_line(line)]
    return lines[0] if len(lines) == 1 else ""


def _is_traceability_line(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(label) for label in TRACEABILITY_LABELS) or (
        "REQ-AUTOFIN" in stripped and "Traceability" in stripped
    )


def _req_refs(line: str) -> list[str]:
    return [match.group(0).upper() for match in REQ_RE.finditer(line)]


def _legacy_refs(line: str) -> list[str]:
    return [match.group(0).upper().replace("  ", " ") for match in LEGACY_RE.finditer(line)]


def _contains_ref(line: str, ref: str) -> bool:
    normalized = ref.upper()
    return normalized in {_normalize_ref(item) for item in [*_req_refs(line), *_legacy_refs(line)]}


def _load_registry_refs(path: Path) -> set[str]:
    result: set[str] = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        req_uid = data.get("req_uid") if isinstance(data, dict) else None
        if req_uid:
            result.add(str(req_uid).upper())
    return result


def _resolve_file(path: str | Path, workspace_root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else workspace_root / value


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _git_relative_path(workspace_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace_root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _run_git(workspace_root: Path, args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", *args],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    return {
        "stdout": completed.stdout.rstrip("\n"),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def _changed_files_from_status(status: str) -> list[str]:
    result: list[str] = []
    for line in status.splitlines():
        if not line.strip():
            continue
        value = line[3:] if len(line) > 3 else line.strip()
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        result.append(value.replace("\\", "/"))
    return result


def _check(
    check_id: str,
    ok: bool,
    message: str,
    details: dict[str, Any] | None = None,
    *,
    warning: bool = False,
    blocked: bool = False,
) -> CompletedPackageRegressionCheck:
    if ok:
        status: CheckStatus = "pass"
    elif blocked:
        status = "blocked"
    elif warning:
        status = "warning"
    else:
        status = "failed"
    return CompletedPackageRegressionCheck(check_id=check_id, status=status, message=message, details=details or {})


def _normalize_ref(ref: str) -> str:
    return ref.upper().replace("  ", " ")


def _unique(values: list[str] | Any) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value)
        if text not in result:
            result.append(text)
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
