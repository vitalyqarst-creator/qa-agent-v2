from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.agent_decision_validation import (
    AgentDecisionValidationReport,
    load_agent_decision_validation_report,
)
from test_case_agent.agent_decision_resolver import load_agent_decision_resolution

CREATED_BY_TOOL = "test_case_agent.agent_driven_create_new_goal_report"
GOAL_REPORT_PREFIX = "agent-driven-create-new-goal-report"
DEFAULT_PACKAGE_ID = "WPKG-000001"

GoalStatus = Literal["pass", "pass-with-warnings", "blocked", "partial"]


@dataclass(frozen=True)
class AgentDrivenCreateNewGoalReport:
    package_id: str
    goal_status: GoalStatus
    executed_stages: list[dict[str, Any]]
    skipped_stages: list[dict[str, Any]]
    stage_9d9_status: str | None
    stage_9e_status: str | None
    stage_9f_status: str | None
    stage_9e_summary: dict[str, Any]
    stage_9f_summary: dict[str, Any]
    original_resolver_gate: dict[str, Any]
    hardened_gate: dict[str, Any]
    created_artifacts: list[str]
    safety_confirmations: dict[str, bool]
    tests_run: list[dict[str, Any]]
    git_status_test_cases: list[str]
    recommended_next_action: str
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDrivenCreateNewGoalReport":
        return cls(
            package_id=str(data["package_id"]),
            goal_status=data["goal_status"],
            executed_stages=list(data.get("executed_stages") or []),
            skipped_stages=list(data.get("skipped_stages") or []),
            stage_9d9_status=data.get("stage_9d9_status"),
            stage_9e_status=data.get("stage_9e_status"),
            stage_9f_status=data.get("stage_9f_status"),
            stage_9e_summary=dict(data.get("stage_9e_summary") or {}),
            stage_9f_summary=dict(data.get("stage_9f_summary") or {}),
            original_resolver_gate=dict(data.get("original_resolver_gate") or {}),
            hardened_gate=dict(data.get("hardened_gate") or {}),
            created_artifacts=list(data.get("created_artifacts") or []),
            safety_confirmations=dict(data.get("safety_confirmations") or {}),
            tests_run=list(data.get("tests_run") or []),
            git_status_test_cases=list(data.get("git_status_test_cases") or []),
            recommended_next_action=str(data.get("recommended_next_action") or ""),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_agent_driven_create_new_goal_report(
    *,
    package_id: str,
    work_dir: Path,
    git_status_test_cases: list[str],
    tests_run: list[dict[str, Any]] | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> AgentDrivenCreateNewGoalReport:
    work_dir = Path(work_dir)
    resolution_path = work_dir / f"agent-decision-resolution-{package_id}.json"
    validation_path = work_dir / f"agent-decision-validation-{package_id}.json"
    stage_9e_path = work_dir / f"new-tc-revised-draft-proposal-{package_id}.json"
    stage_9f_path = work_dir / f"new-tc-revised-draft-review-{package_id}.json"

    resolution = load_agent_decision_resolution(resolution_path) if resolution_path.exists() else None
    validation = load_agent_decision_validation_report(validation_path) if validation_path.exists() else None
    stage_9e = _read_json(stage_9e_path)
    stage_9f = _read_json(stage_9f_path)
    stage_9e_summary = _stage_9e_summary(stage_9e)
    stage_9f_summary = _stage_9f_summary(stage_9f)

    executed = []
    skipped = []
    artifacts = []
    if resolution_path.exists():
        artifacts.extend([str(resolution_path), str(work_dir / f"agent-decision-resolution-{package_id}.md")])
    if validation:
        executed.append({"stage": "Stage 9D.9", "status": validation.validation_status})
        artifacts.extend([str(validation_path), str(work_dir / f"agent-decision-validation-{package_id}.md")])
    else:
        skipped.append({"stage": "Stage 9D.9", "reason": "validation artifact missing"})

    hardened_gate = validation.stage_9e_gate_hardened if validation else {}
    if stage_9e:
        executed.append({"stage": "Stage 9E", "status": stage_9e.get("proposal_status")})
        artifacts.extend([str(stage_9e_path), str(work_dir / f"new-tc-revised-draft-proposal-{package_id}.md")])
    else:
        reason = (
            "Stage 9E intentionally not created in this stage; hardened gate allows a future Stage 9E"
            if hardened_gate.get("stage_9e_allowed")
            else "hardened Stage 9D.9 gate did not allow Stage 9E"
        )
        skipped.append({"stage": "Stage 9E", "reason": reason})

    if stage_9f:
        executed.append({"stage": "Stage 9F", "status": stage_9f.get("review_status")})
        artifacts.extend([str(stage_9f_path), str(work_dir / f"new-tc-revised-draft-review-{package_id}.md")])
    else:
        skipped.append({"stage": "Stage 9F", "reason": "Stage 9E artifact was not created"})

    original_gate = resolution.stage_9e_gate if resolution else {}
    warnings = []
    blockers = []
    if validation and not hardened_gate.get("stage_9e_allowed"):
        blockers.extend(hardened_gate.get("stage_9e_blockers") or [])
        warnings.append("Stage 9E was skipped by hardened gate.")
    if git_status_test_cases:
        blockers.append("canonical test-cases directory is dirty")

    goal_status: GoalStatus = "pass"
    if blockers:
        goal_status = "partial"
    if validation and validation.validation_status in {"blocked", "rejected"}:
        goal_status = "partial"
    if not validation:
        goal_status = "blocked"

    recommended = _recommended_next_action(validation, stage_9e, stage_9f)
    return AgentDrivenCreateNewGoalReport(
        package_id=package_id,
        goal_status=goal_status,
        executed_stages=executed,
        skipped_stages=skipped,
        stage_9d9_status=validation.validation_status if validation else None,
        stage_9e_status=stage_9e.get("proposal_status") if stage_9e else None,
        stage_9f_status=stage_9f.get("review_status") if stage_9f else None,
        stage_9e_summary=stage_9e_summary,
        stage_9f_summary=stage_9f_summary,
        original_resolver_gate=original_gate,
        hardened_gate=hardened_gate,
        created_artifacts=artifacts,
        safety_confirmations={
            "canonical_write_allowed_false": not bool(
                (validation and validation.canonical_write_allowed)
                or (stage_9e and stage_9e.get("canonical_write_allowed"))
                or (stage_9f and stage_9f.get("canonical_write_allowed"))
            ),
            "canonical_test_cases_clean": not git_status_test_cases,
            "no_reviewer_answers_json_created": not list(work_dir.glob("*reviewer*answers*.json")),
            "stage_9e_not_created_unless_hardened_gate_allowed": bool(
                hardened_gate.get("stage_9e_allowed") or not stage_9e_path.exists()
            ),
        },
        tests_run=tests_run or [],
        git_status_test_cases=git_status_test_cases,
        recommended_next_action=recommended,
        warnings=warnings,
        blocking_reasons=blockers,
        created_at_utc=_utc_now(),
        created_by_tool=created_by_tool,
    )


def write_agent_driven_create_new_goal_report(
    report: AgentDrivenCreateNewGoalReport,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{GOAL_REPORT_PREFIX}-{report.package_id}.json"
    md_path = out_dir / f"{GOAL_REPORT_PREFIX}-{report.package_id}.md"
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    md_path.write_text(render_agent_driven_create_new_goal_report_markdown(report), encoding="utf-8-sig", newline="\n")
    return json_path, md_path


def load_agent_driven_create_new_goal_report(path: Path) -> AgentDrivenCreateNewGoalReport:
    return AgentDrivenCreateNewGoalReport.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def render_agent_driven_create_new_goal_report_markdown(report: AgentDrivenCreateNewGoalReport) -> str:
    lines = [
        f"# Agent-Driven Create-New Goal Report {report.package_id}",
        "",
        "## Summary",
        "",
        f"- goal_status: `{report.goal_status}`",
        f"- Stage 9D.9 status: `{report.stage_9d9_status}`",
        f"- Stage 9E status: `{report.stage_9e_status}`",
        f"- Stage 9F status: `{report.stage_9f_status}`",
        f"- Stage 9E candidates: `{report.stage_9e_summary.get('candidate_count', 0)}`",
        f"- Stage 9E blocked candidates: `{report.stage_9e_summary.get('blocked_candidate_count', 0)}`",
        f"- Stage 9F approved: `{report.stage_9f_summary.get('approved_count', 0)}`",
        f"- Stage 9F approved-with-warnings: `{report.stage_9f_summary.get('approved_with_warnings_count', 0)}`",
        f"- Stage 9F needs-revision: `{report.stage_9f_summary.get('needs_revision_count', 0)}`",
        f"- Stage 9F rejected: `{report.stage_9f_summary.get('rejected_count', 0)}`",
        f"- Original Stage 9E allowed: `{report.original_resolver_gate.get('stage_9e_allowed')}`",
        f"- Hardened Stage 9E allowed: `{report.hardened_gate.get('stage_9e_allowed')}`",
        "",
        "## Executed Stages",
        "",
    ]
    lines.extend(f"- {item['stage']}: `{item.get('status')}`" for item in report.executed_stages)
    lines.extend(["", "## Skipped Stages", ""])
    lines.extend(f"- {item['stage']}: {item.get('reason')}" for item in report.skipped_stages)
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            *[f"- `{artifact}`" for artifact in report.created_artifacts],
            "",
            "## Safety Confirmations",
            "",
            *[f"- {key}: `{value}`" for key, value in report.safety_confirmations.items()],
            "",
            "## Tests",
            "",
            *[
                f"- `{item.get('command')}` -> `{item.get('result')}`"
                for item in report.tests_run
            ],
            "",
            "## Git Status For Test-Cases",
            "",
        ]
    )
    if report.git_status_test_cases:
        lines.extend(f"- `{line}`" for line in report.git_status_test_cases)
    else:
        lines.append("- clean")
    lines.extend(
        [
            "",
            "## Recommended Next Action",
            "",
            report.recommended_next_action,
        ]
    )
    return "\n".join(lines) + "\n"


def _recommended_next_action(
    validation: AgentDecisionValidationReport | None,
    stage_9e: dict[str, Any],
    stage_9f: dict[str, Any],
) -> str:
    if stage_9f.get("review_status") in {"approved", "approved-with-warnings"}:
        return "Stage 9G - Controlled Create Apply Dry-Run Design."
    if stage_9f.get("review_status") == "needs-revision":
        return "Revise the Stage 9E draft proposal before any create-apply design."
    if stage_9e.get("proposal_status") == "blocked":
        return "Improve source grounding or agent decision resolver for rejected rows before Stage 9E."
    if validation and not validation.stage_9e_gate_hardened.get("stage_9e_allowed"):
        return "Do not run Stage 9E. Fix rejected agent decisions/source grounding, especially rejected Stage 9E candidate rows."
    if validation and validation.stage_9e_gate_hardened.get("stage_9e_allowed") and not stage_9e:
        return "Next safe step: run Stage 9E draft-only proposal for the hardened validated scope."
    return "Review generated artifacts and decide the next safe stage."


def _stage_9e_summary(stage_9e: dict[str, Any]) -> dict[str, Any]:
    if not stage_9e:
        return {}
    candidates = list(stage_9e.get("revised_draft_candidates") or [])
    return {
        "proposal_status": stage_9e.get("proposal_status"),
        "candidate_count": len(candidates),
        "blocked_candidate_count": sum(1 for item in candidates if item.get("candidate_status") == "blocked"),
        "draft_ready_count": sum(1 for item in candidates if item.get("candidate_status") == "draft-ready"),
        "canonical_write_allowed": bool(stage_9e.get("canonical_write_allowed")),
        "manual_review_required": bool(stage_9e.get("manual_review_required")),
        "hardened_scope_rows": list((stage_9e.get("stage_9e_scope") or {}).get("row_ids") or []),
    }


def _stage_9f_summary(stage_9f: dict[str, Any]) -> dict[str, Any]:
    if not stage_9f:
        return {}
    reviews = list(stage_9f.get("draft_reviews") or [])
    counts: dict[str, int] = {}
    for review in reviews:
        key = f"{review.get('review_result')}_count".replace("-", "_")
        counts[key] = counts.get(key, 0) + 1
    for key in ("approved_count", "approved_with_warnings_count", "needs_revision_count", "rejected_count"):
        counts.setdefault(key, 0)
    return {
        "review_status": stage_9f.get("review_status"),
        "draft_reviews_total": len(reviews),
        **counts,
        "stage_9g_readiness": dict(stage_9f.get("stage_9g_readiness") or {}),
        "canonical_write_allowed": bool(stage_9f.get("canonical_write_allowed")),
        "manual_review_required": bool(stage_9f.get("manual_review_required")),
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
