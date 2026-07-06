from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from test_case_agent.new_tc_revision_decision_pack import (
    AgentCapabilityFinding,
    NewTcRevisionDecisionPack,
    load_new_tc_revision_decision_pack,
)

CREATED_BY_TOOL = "test_case_agent.agent_capability_improvement_plan"
IMPROVEMENT_PLAN_PREFIX = "agent-capability-improvement-plan"
DEFAULT_PACKAGE_ID = "WPKG-000001"
DEFAULT_BENCHMARK_NAME = "AutoFin WPKG-000001 create-new-candidate benchmark"

PlanStatus = Literal["pass", "pass-with-warnings", "blocked"]
CapabilityStatus = Literal["works", "partial", "gap"]
Priority = Literal["P0", "P1", "P2", "P3"]
ChangeType = Literal["instruction_update", "code_update", "test_update", "workflow_update", "no_change"]
InstructionUpdateType = Literal["add_section", "revise_section", "add_link", "no_change"]
CodeUpdateType = Literal["new_module", "revise_module", "no_change"]


@dataclass(frozen=True)
class CapabilityFindingSummary:
    capability_area: str
    current_status: CapabilityStatus
    evidence: dict[str, Any]
    impact_on_agent: str
    recommended_response: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_area": self.capability_area,
            "current_status": self.current_status,
            "evidence": self.evidence,
            "impact_on_agent": self.impact_on_agent,
            "recommended_response": self.recommended_response,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityFindingSummary":
        return cls(
            capability_area=str(data["capability_area"]),
            current_status=data["current_status"],
            evidence=dict(data.get("evidence") or {}),
            impact_on_agent=str(data["impact_on_agent"]),
            recommended_response=str(data["recommended_response"]),
        )


@dataclass(frozen=True)
class ImprovementItem:
    improvement_id: str
    capability_area: str
    priority: Priority
    problem_statement: str
    root_cause_hypothesis: str
    proposed_change_type: ChangeType
    proposed_change_summary: str
    target_files: list[str]
    expected_benefit: str
    risk: str
    dependencies: list[str]
    acceptance_criteria: list[str]
    out_of_scope: list[str]
    ready_for_implementation: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "improvement_id": self.improvement_id,
            "capability_area": self.capability_area,
            "priority": self.priority,
            "problem_statement": self.problem_statement,
            "root_cause_hypothesis": self.root_cause_hypothesis,
            "proposed_change_type": self.proposed_change_type,
            "proposed_change_summary": self.proposed_change_summary,
            "target_files": self.target_files,
            "expected_benefit": self.expected_benefit,
            "risk": self.risk,
            "dependencies": self.dependencies,
            "acceptance_criteria": self.acceptance_criteria,
            "out_of_scope": self.out_of_scope,
            "ready_for_implementation": self.ready_for_implementation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImprovementItem":
        return cls(
            improvement_id=str(data["improvement_id"]),
            capability_area=str(data["capability_area"]),
            priority=data["priority"],
            problem_statement=str(data["problem_statement"]),
            root_cause_hypothesis=str(data["root_cause_hypothesis"]),
            proposed_change_type=data["proposed_change_type"],
            proposed_change_summary=str(data["proposed_change_summary"]),
            target_files=list(data.get("target_files") or []),
            expected_benefit=str(data["expected_benefit"]),
            risk=str(data["risk"]),
            dependencies=list(data.get("dependencies") or []),
            acceptance_criteria=list(data.get("acceptance_criteria") or []),
            out_of_scope=list(data.get("out_of_scope") or []),
            ready_for_implementation=bool(data.get("ready_for_implementation")),
        )


@dataclass(frozen=True)
class InstructionUpdatePlan:
    target_file: str
    update_type: InstructionUpdateType
    reason: str
    proposed_section_title: str | None
    proposed_guidance_summary: str
    must_include_rules: list[str]
    must_not_include: list[str]
    priority: Priority

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_file": self.target_file,
            "update_type": self.update_type,
            "reason": self.reason,
            "proposed_section_title": self.proposed_section_title,
            "proposed_guidance_summary": self.proposed_guidance_summary,
            "must_include_rules": self.must_include_rules,
            "must_not_include": self.must_not_include,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstructionUpdatePlan":
        return cls(
            target_file=str(data["target_file"]),
            update_type=data["update_type"],
            reason=str(data["reason"]),
            proposed_section_title=data.get("proposed_section_title"),
            proposed_guidance_summary=str(data["proposed_guidance_summary"]),
            must_include_rules=list(data.get("must_include_rules") or []),
            must_not_include=list(data.get("must_not_include") or []),
            priority=data["priority"],
        )


@dataclass(frozen=True)
class CodeUpdatePlan:
    target_module: str
    update_type: CodeUpdateType
    reason: str
    proposed_behavior: list[str]
    interfaces_affected: list[str]
    backward_compatibility_notes: list[str]
    priority: Priority

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_module": self.target_module,
            "update_type": self.update_type,
            "reason": self.reason,
            "proposed_behavior": self.proposed_behavior,
            "interfaces_affected": self.interfaces_affected,
            "backward_compatibility_notes": self.backward_compatibility_notes,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeUpdatePlan":
        return cls(
            target_module=str(data["target_module"]),
            update_type=data["update_type"],
            reason=str(data["reason"]),
            proposed_behavior=list(data.get("proposed_behavior") or []),
            interfaces_affected=list(data.get("interfaces_affected") or []),
            backward_compatibility_notes=list(data.get("backward_compatibility_notes") or []),
            priority=data["priority"],
        )


@dataclass(frozen=True)
class TestUpdatePlan:
    target_test_file: str
    test_cases_to_add: list[str]
    regression_cases: list[str]
    fixture_requirements: list[str]
    priority: Priority

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_test_file": self.target_test_file,
            "test_cases_to_add": self.test_cases_to_add,
            "regression_cases": self.regression_cases,
            "fixture_requirements": self.fixture_requirements,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestUpdatePlan":
        return cls(
            target_test_file=str(data["target_test_file"]),
            test_cases_to_add=list(data.get("test_cases_to_add") or []),
            regression_cases=list(data.get("regression_cases") or []),
            fixture_requirements=list(data.get("fixture_requirements") or []),
            priority=data["priority"],
        )


@dataclass(frozen=True)
class SafetyPreservationPlan:
    safety_gate: str
    current_status: str
    must_preserve: list[str]
    tests_to_protect_gate: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "safety_gate": self.safety_gate,
            "current_status": self.current_status,
            "must_preserve": self.must_preserve,
            "tests_to_protect_gate": self.tests_to_protect_gate,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SafetyPreservationPlan":
        return cls(
            safety_gate=str(data["safety_gate"]),
            current_status=str(data["current_status"]),
            must_preserve=list(data.get("must_preserve") or []),
            tests_to_protect_gate=list(data.get("tests_to_protect_gate") or []),
            notes=list(data.get("notes") or []),
        )


@dataclass
class AgentCapabilityImprovementPlan:
    package_id: str
    benchmark_name: str
    plan_status: PlanStatus
    source_decision_pack_path: str
    capability_findings_summary: list[CapabilityFindingSummary]
    improvement_items: list[ImprovementItem]
    instruction_update_plan: list[InstructionUpdatePlan]
    code_update_plan: list[CodeUpdatePlan]
    test_update_plan: list[TestUpdatePlan]
    safety_preservation_plan: list[SafetyPreservationPlan]
    implementation_sequence: list[str]
    acceptance_criteria: list[str]
    non_goals: list[str]
    expected_next_stage: str
    input_paths: dict[str, str | None]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "benchmark_name": self.benchmark_name,
            "plan_status": self.plan_status,
            "source_decision_pack_path": self.source_decision_pack_path,
            "capability_findings_summary": [item.to_dict() for item in self.capability_findings_summary],
            "improvement_items": [item.to_dict() for item in self.improvement_items],
            "instruction_update_plan": [item.to_dict() for item in self.instruction_update_plan],
            "code_update_plan": [item.to_dict() for item in self.code_update_plan],
            "test_update_plan": [item.to_dict() for item in self.test_update_plan],
            "safety_preservation_plan": [item.to_dict() for item in self.safety_preservation_plan],
            "implementation_sequence": self.implementation_sequence,
            "acceptance_criteria": self.acceptance_criteria,
            "non_goals": self.non_goals,
            "expected_next_stage": self.expected_next_stage,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentCapabilityImprovementPlan":
        return cls(
            package_id=str(data["package_id"]),
            benchmark_name=str(data["benchmark_name"]),
            plan_status=data["plan_status"],
            source_decision_pack_path=str(data["source_decision_pack_path"]),
            capability_findings_summary=[
                CapabilityFindingSummary.from_dict(item) for item in data.get("capability_findings_summary", [])
            ],
            improvement_items=[ImprovementItem.from_dict(item) for item in data.get("improvement_items", [])],
            instruction_update_plan=[
                InstructionUpdatePlan.from_dict(item) for item in data.get("instruction_update_plan", [])
            ],
            code_update_plan=[CodeUpdatePlan.from_dict(item) for item in data.get("code_update_plan", [])],
            test_update_plan=[TestUpdatePlan.from_dict(item) for item in data.get("test_update_plan", [])],
            safety_preservation_plan=[
                SafetyPreservationPlan.from_dict(item) for item in data.get("safety_preservation_plan", [])
            ],
            implementation_sequence=list(data.get("implementation_sequence") or []),
            acceptance_criteria=list(data.get("acceptance_criteria") or []),
            non_goals=list(data.get("non_goals") or []),
            expected_next_stage=str(data["expected_next_stage"]),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


def build_agent_capability_improvement_plan(
    *,
    package_id: str,
    decision_pack_path: Path,
    benchmark_name: str = DEFAULT_BENCHMARK_NAME,
    draft_revision_plan_path: Path | None = None,
    draft_review_path: Path | None = None,
    draft_proposal_path: Path | None = None,
    context_bundle_path: Path | None = None,
    test_cases_dir: Path | None = None,
    instruction_surface_paths: list[Path] | None = None,
    created_by_tool: str = CREATED_BY_TOOL,
) -> AgentCapabilityImprovementPlan:
    input_paths = _input_paths(
        decision_pack_path=decision_pack_path,
        draft_revision_plan_path=draft_revision_plan_path,
        draft_review_path=draft_review_path,
        draft_proposal_path=draft_proposal_path,
        context_bundle_path=context_bundle_path,
        test_cases_dir=test_cases_dir,
    )
    for index, path in enumerate(instruction_surface_paths or [], start=1):
        input_paths[f"instruction_surface_{index:02d}"] = str(path)

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    pack: NewTcRevisionDecisionPack | None = None

    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"this improvement plan is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")
    if not Path(decision_pack_path).exists():
        blocking_reasons.append(f"decision pack is missing: {decision_pack_path}")
    else:
        try:
            pack = load_new_tc_revision_decision_pack(Path(decision_pack_path))
        except Exception as exc:  # noqa: BLE001 - plan reports parse failures.
            blocking_reasons.append(f"decision pack cannot be parsed: {decision_pack_path}: {exc}")
    for path in instruction_surface_paths or []:
        if not Path(path).exists():
            warnings.append(f"instruction surface is missing: {path}")

    if pack is not None and pack.package_id != package_id:
        blocking_reasons.append(f"decision pack package_id mismatch: {pack.package_id} != {package_id}")
    if pack is not None and not pack.agent_capability_findings:
        blocking_reasons.append("decision pack does not contain agent_capability_findings.")

    if blocking_reasons or pack is None:
        return _plan(
            package_id=package_id,
            benchmark_name=benchmark_name,
            source_decision_pack_path=str(decision_pack_path),
            input_paths=input_paths,
            warnings=warnings,
            blocking_reasons=_unique(blocking_reasons),
            created_by_tool=created_by_tool,
        )

    summaries = [_finding_summary(finding) for finding in pack.agent_capability_findings]
    improvement_items = _improvement_items(pack.agent_capability_findings)
    instruction_plan = _instruction_update_plan(pack.agent_capability_findings)
    code_plan = _code_update_plan(pack.agent_capability_findings)
    test_plan = _test_update_plan(pack.agent_capability_findings)
    safety_plan = _safety_preservation_plan(pack)
    return _plan(
        package_id=package_id,
        benchmark_name=benchmark_name,
        source_decision_pack_path=str(decision_pack_path),
        capability_findings_summary=summaries,
        improvement_items=improvement_items,
        instruction_update_plan=instruction_plan,
        code_update_plan=code_plan,
        test_update_plan=test_plan,
        safety_preservation_plan=safety_plan,
        input_paths=input_paths,
        warnings=_unique(warnings),
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_agent_capability_improvement_plan(
    plan: AgentCapabilityImprovementPlan,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{IMPROVEMENT_PLAN_PREFIX}-{plan.package_id}.json"
    markdown_path = out_dir / f"{IMPROVEMENT_PLAN_PREFIX}-{plan.package_id}.md"
    json_path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_agent_capability_improvement_plan_markdown(plan), encoding="utf-8", newline="\n")
    return json_path, markdown_path


def load_agent_capability_improvement_plan(path: Path) -> AgentCapabilityImprovementPlan:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Agent capability improvement plan root must be a JSON object.")
    return AgentCapabilityImprovementPlan.from_dict(payload)


def render_agent_capability_improvement_plan_markdown(plan: AgentCapabilityImprovementPlan) -> str:
    priority_counts = Counter(item.priority for item in plan.improvement_items)
    lines = [
        f"# Agent Capability Improvement Plan {plan.package_id}",
        "",
        "## Summary",
        "",
        f"- Plan status: `{plan.plan_status}`",
        f"- Benchmark: `{plan.benchmark_name}`",
        f"- Improvement items: `{len(plan.improvement_items)}`",
        f"- P0/P1/P2/P3: `{priority_counts.get('P0', 0)}` / `{priority_counts.get('P1', 0)}` / `{priority_counts.get('P2', 0)}` / `{priority_counts.get('P3', 0)}`",
        f"- Instruction updates: `{len(plan.instruction_update_plan)}`",
        f"- Code updates: `{len(plan.code_update_plan)}`",
        f"- Test updates: `{len(plan.test_update_plan)}`",
        f"- Safety preservation items: `{len(plan.safety_preservation_plan)}`",
        f"- Expected next stage: `{plan.expected_next_stage}`",
        "",
        "## Capability Findings",
        "",
        "| Area | Status | Impact | Response |",
        "| --- | --- | --- | --- |",
    ]
    for summary in plan.capability_findings_summary:
        lines.append(
            f"| `{summary.capability_area}` | `{summary.current_status}` | "
            f"{summary.impact_on_agent} | {summary.recommended_response} |"
        )
    lines.extend(["", "## Improvement Roadmap", ""])
    for item in plan.improvement_items:
        lines.append(f"### {item.improvement_id} {item.capability_area}")
        lines.append(f"- Priority: `{item.priority}`")
        lines.append(f"- Change type: `{item.proposed_change_type}`")
        lines.append(f"- Problem: {item.problem_statement}")
        lines.append(f"- Proposed change: {item.proposed_change_summary}")
        lines.append("- Target files:")
        _append_list(lines, item.target_files)
        lines.append("- Acceptance criteria:")
        _append_list(lines, item.acceptance_criteria)
        lines.append("")
    lines.extend(["## Instruction Update Plan", ""])
    for item in plan.instruction_update_plan:
        lines.append(f"- `{item.priority}` `{item.target_file}` `{item.update_type}`: {item.proposed_guidance_summary}")
    if not plan.instruction_update_plan:
        lines.append("- none")
    lines.extend(["", "## Code Update Plan", ""])
    for item in plan.code_update_plan:
        lines.append(f"- `{item.priority}` `{item.target_module}` `{item.update_type}`: {item.reason}")
    if not plan.code_update_plan:
        lines.append("- none")
    lines.extend(["", "## Test Update Plan", ""])
    for item in plan.test_update_plan:
        lines.append(f"- `{item.priority}` `{item.target_test_file}`: {', '.join(item.test_cases_to_add)}")
    if not plan.test_update_plan:
        lines.append("- none")
    lines.extend(["", "## Safety Preservation Plan", ""])
    for item in plan.safety_preservation_plan:
        lines.append(f"- `{item.safety_gate}` `{item.current_status}`")
        lines.append("  Must preserve:")
        for rule in item.must_preserve:
            lines.append(f"  - {rule}")
    if not plan.safety_preservation_plan:
        lines.append("- none")
    lines.extend(["", "## Implementation Sequence", ""])
    _append_numbered(lines, plan.implementation_sequence)
    lines.extend(["", "## Acceptance Criteria", ""])
    _append_list(lines, plan.acceptance_criteria)
    lines.extend(["", "## Non-Goals", ""])
    _append_list(lines, plan.non_goals)
    lines.extend(["", "## Warnings", ""])
    _append_list(lines, plan.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, plan.blocking_reasons)
    return "\n".join(lines).rstrip() + "\n"


def _plan(
    *,
    package_id: str,
    benchmark_name: str,
    source_decision_pack_path: str,
    input_paths: dict[str, str | None],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
    capability_findings_summary: list[CapabilityFindingSummary] | None = None,
    improvement_items: list[ImprovementItem] | None = None,
    instruction_update_plan: list[InstructionUpdatePlan] | None = None,
    code_update_plan: list[CodeUpdatePlan] | None = None,
    test_update_plan: list[TestUpdatePlan] | None = None,
    safety_preservation_plan: list[SafetyPreservationPlan] | None = None,
) -> AgentCapabilityImprovementPlan:
    capability_findings_summary = capability_findings_summary or []
    improvement_items = improvement_items or []
    instruction_update_plan = instruction_update_plan or []
    code_update_plan = code_update_plan or []
    test_update_plan = test_update_plan or []
    safety_preservation_plan = safety_preservation_plan or []
    if blocking_reasons:
        status: PlanStatus = "blocked"
    elif warnings or any(item.priority in {"P1", "P2"} for item in improvement_items):
        status = "pass-with-warnings"
    else:
        status = "pass"
    return AgentCapabilityImprovementPlan(
        package_id=package_id,
        benchmark_name=benchmark_name,
        plan_status=status,
        source_decision_pack_path=source_decision_pack_path,
        capability_findings_summary=capability_findings_summary,
        improvement_items=improvement_items,
        instruction_update_plan=instruction_update_plan,
        code_update_plan=code_update_plan,
        test_update_plan=test_update_plan,
        safety_preservation_plan=safety_preservation_plan,
        implementation_sequence=_implementation_sequence(),
        acceptance_criteria=_global_acceptance_criteria(),
        non_goals=_non_goals(),
        expected_next_stage="Stage 9D.3 - Implement Source Grounding and Draft Quality Improvements",
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def _finding_summary(finding: AgentCapabilityFinding) -> CapabilityFindingSummary:
    return CapabilityFindingSummary(
        capability_area=finding.capability_area,
        current_status=finding.status,
        evidence=finding.evidence,
        impact_on_agent=_impact_on_agent(finding),
        recommended_response=finding.recommendation,
    )


def _improvement_items(findings: list[AgentCapabilityFinding]) -> list[ImprovementItem]:
    result: list[ImprovementItem] = []
    for finding in findings:
        spec = _area_spec(finding.capability_area, finding.status)
        result.append(
            ImprovementItem(
                improvement_id=f"AIP-{len(result) + 1:06d}",
                capability_area=finding.capability_area,
                priority=spec["priority"],
                problem_statement=spec["problem"],
                root_cause_hypothesis=spec["root_cause"],
                proposed_change_type=spec["change_type"],
                proposed_change_summary=spec["summary"],
                target_files=spec["target_files"],
                expected_benefit=spec["benefit"],
                risk=spec["risk"],
                dependencies=spec["dependencies"],
                acceptance_criteria=spec["acceptance"],
                out_of_scope=_non_goals(),
                ready_for_implementation=finding.capability_area != "safety_gate" or finding.status != "works",
            )
        )
    return result


def _instruction_update_plan(findings: list[AgentCapabilityFinding]) -> list[InstructionUpdatePlan]:
    areas = {finding.capability_area: finding.status for finding in findings}
    plans = [
        InstructionUpdatePlan(
            target_file="references/agent/create-new-tc-context-bundle-format.md",
            update_type="revise_section",
            reason="source_grounding gap: source facts do not support executable draft steps.",
            proposed_section_title="Source Fact Extraction for Draftable Requirements",
            proposed_guidance_summary="Require object/screen/field, condition, user action, observable expected behavior and source anchors before draft readiness.",
            must_include_rules=[
                "If action or oracle is not source-backed, create a manual question or defer.",
                "Do not infer navigation or UI behavior from existing TC content.",
            ],
            must_not_include=["AutoFin-specific field hacks.", "Permission to create canonical TC."],
            priority="P1",
        ),
        InstructionUpdatePlan(
            target_file="references/agent/new-tc-draft-proposal-format.md",
            update_type="revise_section",
            reason="draft_quality gap: Stage 9B produced generic placeholder steps.",
            proposed_section_title="Draft Candidate Quality Floor",
            proposed_guidance_summary="Forbid placeholder steps and expected results in draft-only candidates.",
            must_include_rules=[
                "No 'Open screen identified by anchors' as a final draft step.",
                "No 'Set up source-backed condition' without naming the condition.",
                "No expected result unless expected_behavior is source-backed.",
            ],
            must_not_include=["Bypass review.", "Treat draft-only candidates as canonical TC."],
            priority="P1",
        ),
        InstructionUpdatePlan(
            target_file="references/agent/new-tc-revision-decision-pack-format.md",
            update_type="revise_section",
            reason="manual_decision_flow gap and duplicate_risk_handling partial.",
            proposed_section_title="Reviewer Decision Matrix",
            proposed_guidance_summary="Group manual questions by cluster, similar TC, source requirement and decision type.",
            must_include_rules=[
                "One matrix row per cluster-level decision where possible.",
                "Keep per-comparison details in JSON but summarize reviewer-facing choices.",
            ],
            must_not_include=["One ungrouped manual question per comparison in Markdown handoff."],
            priority="P2",
        ),
    ]
    if areas.get("replacement_strategy") in {"partial", "gap"}:
        plans.append(
            InstructionUpdatePlan(
                target_file="references/agent/new-tc-draft-revision-plan-format.md",
                update_type="revise_section",
                reason="replacement_strategy partial: rejected drafts need clearer source/duplicate gates.",
                proposed_section_title="Rejected Draft Replacement Gates",
                proposed_guidance_summary="Replacement must be rewrite_from_source, split, defer, or maybe_extend_existing_tc based on source and duplicate evidence.",
                must_include_rules=["Rejected draft must not be patched in place."],
                must_not_include=["Rewrite rejected draft from its own weak content."],
                priority="P2",
            )
        )
    plans.append(
        InstructionUpdatePlan(
            target_file="references/agent/controlled-traceability-update-workflow.md",
            update_type="no_change",
            reason="safety_gate works and must remain unchanged.",
            proposed_section_title=None,
            proposed_guidance_summary="Preserve no-write safety gates for planning/review stages.",
            must_include_rules=["canonical_write_allowed=false until explicit controlled apply/create stage."],
            must_not_include=["Any rule that enables apply from an improvement plan."],
            priority="P3",
        )
    )
    return plans


def _code_update_plan(findings: list[AgentCapabilityFinding]) -> list[CodeUpdatePlan]:
    areas = {finding.capability_area: finding.status for finding in findings}
    plans: list[CodeUpdatePlan] = []
    if areas.get("source_grounding") in {"gap", "partial"}:
        plans.append(
            CodeUpdatePlan(
                target_module="test_case_agent/create_new_tc_context_bundle.py",
                update_type="revise_module",
                reason="Extract richer source facts before draft generation.",
                proposed_behavior=[
                    "Extract object/screen/field, condition, user action and observable expected behavior separately.",
                    "Carry source anchors into candidate requirements used by draft generation.",
                    "Mark candidate as not draftable when action/oracle is missing.",
                ],
                interfaces_affected=["CandidateRequirement", "CreateNewTcContextBundle"],
                backward_compatibility_notes=["Additive fields or derived status should preserve existing JSON readers."],
                priority="P1",
            )
        )
    if areas.get("draft_quality") in {"gap", "partial"}:
        plans.append(
            CodeUpdatePlan(
                target_module="test_case_agent/new_tc_draft_proposals.py",
                update_type="revise_module",
                reason="Prevent generic placeholder draft candidates.",
                proposed_behavior=[
                    "Block or defer draft generation when concrete action or expected result is unavailable.",
                    "Emit manual questions instead of generic placeholder steps.",
                    "Count placeholder patterns in proposal summary.",
                ],
                interfaces_affected=["DraftTestCaseCandidate", "NewTcDraftProposal"],
                backward_compatibility_notes=["Keep canonical_write_allowed=false and draft-only IDs."],
                priority="P1",
            )
        )
    if areas.get("duplicate_risk_handling") in {"partial", "gap"}:
        plans.append(
            CodeUpdatePlan(
                target_module="test_case_agent/new_tc_revision_decision_pack.py",
                update_type="revise_module",
                reason="Improve duplicate comparison confidence and reviewer grouping.",
                proposed_behavior=[
                    "Score source_req_id, object, condition and expected_behavior overlap separately.",
                    "Attach confidence to likely_duplicate/maybe_extend/separate_new_tc decisions.",
                    "Create reviewer decision matrix by cluster.",
                ],
                interfaces_affected=["ExistingTcComparison", "DuplicateRiskCluster"],
                backward_compatibility_notes=["Keep existing decision enum values; add confidence fields if needed."],
                priority="P2",
            )
        )
    if areas.get("replacement_strategy") in {"partial", "gap"}:
        plans.append(
            CodeUpdatePlan(
                target_module="test_case_agent/new_tc_revision_decision_pack.py",
                update_type="revise_module",
                reason="Replacement strategy should combine source grounding and duplicate risk evidence.",
                proposed_behavior=[
                    "Allow rewrite_from_source only when source grounding is complete.",
                    "Route likely duplicates to maybe_extend_existing_tc.",
                    "Route missing source action/oracle to defer.",
                ],
                interfaces_affected=["ReplacementStrategy"],
                backward_compatibility_notes=["Do not change canonical test-case files or create draft content in decision stage."],
                priority="P2",
            )
        )
    return plans


def _test_update_plan(findings: list[AgentCapabilityFinding]) -> list[TestUpdatePlan]:
    return [
        TestUpdatePlan(
            target_test_file="tests/test_create_new_tc_context_bundle.py",
            test_cases_to_add=[
                "candidate extracts object condition action expected_behavior and anchors",
                "candidate is marked not draftable when action or oracle is missing",
            ],
            regression_cases=["Existing bundle JSON remains backward-compatible."],
            fixture_requirements=["Synthetic registry entries with complete and incomplete source facts."],
            priority="P1",
        ),
        TestUpdatePlan(
            target_test_file="tests/test_new_tc_draft_proposals.py",
            test_cases_to_add=[
                "proposal does not emit generic placeholder steps",
                "proposal defers when expected_behavior is missing",
            ],
            regression_cases=["canonical_write_allowed remains false.", "draft IDs remain DRAFT-* only."],
            fixture_requirements=["Candidate requirements with and without concrete action/oracle."],
            priority="P1",
        ),
        TestUpdatePlan(
            target_test_file="tests/test_new_tc_revision_decision_pack.py",
            test_cases_to_add=[
                "manual questions are grouped by duplicate-risk cluster",
                "duplicate comparison distinguishes likely duplicate from separate new TC",
                "rejected draft replacement depends on source grounding and duplicate risk",
            ],
            regression_cases=["safety_gate finding remains works when unresolved decisions block readiness."],
            fixture_requirements=["Synthetic similar TC blocks with matching and nonmatching source_req_id/object/expected result."],
            priority="P2",
        ),
    ]


def _safety_preservation_plan(pack: NewTcRevisionDecisionPack) -> list[SafetyPreservationPlan]:
    safety = next((finding for finding in pack.agent_capability_findings if finding.capability_area == "safety_gate"), None)
    return [
        SafetyPreservationPlan(
            safety_gate="planning_stages_do_not_write_canonical_test_cases",
            current_status=safety.status if safety else "unknown",
            must_preserve=[
                "canonical_write_allowed=false in proposal, review, revision-plan, decision-pack and improvement-plan stages.",
                "manual_review_required=true while unresolved decisions remain.",
                "ready_for_revised_draft_proposal=false when duplicate/source/manual decisions remain unresolved.",
                "No canonical TC creation or apply from improvement-plan stage.",
            ],
            tests_to_protect_gate=[
                "tests/test_new_tc_draft_proposals.py::test_canonical_write_allowed_is_false",
                "tests/test_new_tc_draft_review.py::test_safe_for_controlled_create_apply_false_when_drafts_need_revision",
                "tests/test_new_tc_revision_decision_pack.py::test_safety_gate_finding_works_when_unresolved_decisions_block_readiness",
                "tests/test_agent_capability_improvement_plan.py::test_does_not_mark_canonical_create_apply_as_next_stage",
            ],
            notes=["Do not loosen this gate to improve benchmark metrics."],
        )
    ]


def _area_spec(area: str, status: str) -> dict[str, Any]:
    specs: dict[str, dict[str, Any]] = {
        "source_grounding": {
            "priority": "P1",
            "problem": "Source grounding cannot support executable steps or observable expected results for the benchmark drafts.",
            "root_cause": "Candidate requirements do not reliably separate object, condition, user action, expected behavior and source anchors.",
            "change_type": "code_update",
            "summary": "Improve source fact extraction and draftability gates before draft generation.",
            "target_files": [
                "test_case_agent/create_new_tc_context_bundle.py",
                "references/agent/create-new-tc-context-bundle-format.md",
                "tests/test_create_new_tc_context_bundle.py",
            ],
            "benefit": "Fewer drafts blocked on missing action/oracle; no invented steps.",
            "risk": "Over-extraction could misclassify text as executable behavior; require conservative tests.",
            "dependencies": ["instruction update for source fact requirements"],
            "acceptance": [
                "unresolved_source_grounding_count decreases on AutoFin rerun",
                "no draft is marked ready without source-backed action and expected result",
            ],
        },
        "draft_quality": {
            "priority": "P1",
            "problem": "Draft candidates contain generic placeholder steps and no candidate is ready.",
            "root_cause": "Draft generation allows placeholders when source facts are incomplete.",
            "change_type": "code_update",
            "summary": "Forbid generic draft steps/oracles and defer candidates with missing concrete facts.",
            "target_files": [
                "test_case_agent/new_tc_draft_proposals.py",
                "test_case_agent/new_tc_draft_review.py",
                "references/agent/new-tc-draft-proposal-format.md",
                "tests/test_new_tc_draft_proposals.py",
            ],
            "benefit": "Draft-only proposals become useful reviewer input instead of placeholder artifacts.",
            "risk": "More candidates may be deferred until source extraction improves.",
            "dependencies": ["source_grounding"],
            "acceptance": [
                "generic placeholder steps count is 0",
                "needs_manual_decision_count decreases from benchmark baseline of 16 after rerun",
            ],
        },
        "manual_decision_flow": {
            "priority": "P2",
            "problem": "Manual decisions are too numerous for efficient reviewer action.",
            "root_cause": "Decision pack emits many comparison-level questions instead of a compact matrix.",
            "change_type": "workflow_update",
            "summary": "Aggregate questions by cluster, similar TC, source requirement and decision type.",
            "target_files": [
                "test_case_agent/new_tc_revision_decision_pack.py",
                "references/agent/new-tc-revision-decision-pack-format.md",
                "tests/test_new_tc_revision_decision_pack.py",
            ],
            "benefit": "Human reviewers can resolve fewer, clearer decisions.",
            "risk": "Over-aggregation can hide important per-TC differences; retain details in JSON.",
            "dependencies": ["duplicate_risk_handling"],
            "acceptance": [
                "manual_decisions_required count decreases substantially while detailed comparisons remain available",
                "Markdown contains reviewer-facing decision matrix",
            ],
        },
        "duplicate_risk_handling": {
            "priority": "P2",
            "problem": "Duplicate risks are clustered, but decisions still remain unresolved.",
            "root_cause": "Comparison heuristics lack confidence scoring across source_req_id, object, condition and expected behavior.",
            "change_type": "code_update",
            "summary": "Improve duplicate comparison heuristics and add confidence levels.",
            "target_files": [
                "test_case_agent/create_new_tc_context_bundle.py",
                "test_case_agent/new_tc_revision_decision_pack.py",
                "tests/test_new_tc_revision_decision_pack.py",
            ],
            "benefit": "Separate-new-TC vs maybe-extend decisions become more explainable.",
            "risk": "False certainty could create duplicate TC drafts; keep manual review for low confidence.",
            "dependencies": ["source_grounding"],
            "acceptance": [
                "duplicate-risk clusters remain compact",
                "synthetic duplicate/non-duplicate tests classify correctly with confidence",
            ],
        },
        "replacement_strategy": {
            "priority": "P2",
            "problem": "Rejected drafts have strategies, but none are allowed for replacement in the benchmark.",
            "root_cause": "Replacement strategy is blocked by unresolved source grounding and duplicate risk.",
            "change_type": "workflow_update",
            "summary": "Tie replacement mode explicitly to source grounding and duplicate-risk evidence.",
            "target_files": [
                "test_case_agent/new_tc_draft_revision_plan.py",
                "test_case_agent/new_tc_revision_decision_pack.py",
                "references/agent/new-tc-draft-revision-plan-format.md",
                "tests/test_new_tc_revision_decision_pack.py",
            ],
            "benefit": "Rejected drafts are safely rewritten from source, split, deferred or routed to existing TC extension.",
            "risk": "Premature replacement could preserve weak draft assumptions; forbid patch-in-place.",
            "dependencies": ["source_grounding", "duplicate_risk_handling"],
            "acceptance": [
                "rejected draft with valid source mapping gets rewrite_from_source",
                "likely duplicate rejected draft gets maybe_extend_existing_tc",
            ],
        },
        "safety_gate": {
            "priority": "P3",
            "problem": "Safety gate works and must not be loosened while improving quality.",
            "root_cause": "No defect found; this is a preservation item.",
            "change_type": "no_change",
            "summary": "Preserve no-write/no-apply behavior across planning and audit stages.",
            "target_files": [
                "test_case_agent/new_tc_draft_proposals.py",
                "test_case_agent/new_tc_draft_review.py",
                "test_case_agent/new_tc_revision_decision_pack.py",
                "tests/test_agent_capability_improvement_plan.py",
            ],
            "benefit": "Quality improvements cannot accidentally authorize canonical writes.",
            "risk": "None if preserved; do not rewrite working safety gates unnecessarily.",
            "dependencies": [],
            "acceptance": [
                "canonical_write_allowed remains false",
                "expected_next_stage is not controlled create/apply",
                "test-cases dir remains clean after planning stages",
            ],
        },
    }
    spec = specs.get(area, specs["safety_gate"]).copy()
    if status == "works" and area != "safety_gate":
        spec["priority"] = "P3"
        spec["change_type"] = "no_change"
        spec["summary"] = "No change required beyond regression coverage."
    return spec


def _impact_on_agent(finding: AgentCapabilityFinding) -> str:
    if finding.capability_area == "source_grounding":
        return "Draft writer cannot produce executable steps/oracles without inventing behavior."
    if finding.capability_area == "draft_quality":
        return "Draft proposal is safe but not useful enough for revised drafting."
    if finding.capability_area == "manual_decision_flow":
        return "Reviewer burden is too high for efficient benchmark iteration."
    if finding.capability_area == "duplicate_risk_handling":
        return "Duplicate review load is reduced, but decisions are still not resolved."
    if finding.capability_area == "replacement_strategy":
        return "Rejected drafts cannot be safely replaced until source/duplicate evidence improves."
    if finding.capability_area == "safety_gate":
        return "Safety gate correctly blocks unsafe readiness and writes."
    return "Observed capability requires follow-up."


def _implementation_sequence() -> list[str]:
    return [
        "Update instruction/format docs for source grounding and draft quality gates.",
        "Improve source-grounding extraction and draftability status.",
        "Improve draft generation so generic placeholder steps/oracles are deferred instead of emitted.",
        "Improve duplicate-risk comparison confidence and reviewer decision aggregation.",
        "Improve replacement strategy routing for rejected drafts.",
        "Rerun Stage 9B, 9C, 9D and 9D.1 on the AutoFin benchmark.",
        "Only after measurable improvement, consider a revised draft proposal stage.",
    ]


def _global_acceptance_criteria() -> list[str]:
    return [
        "Generic placeholder steps count is 0 in new draft proposals.",
        "unresolved_source_grounding_count decreases on AutoFin benchmark rerun.",
        "needs_manual_decision_count decreases from 16.",
        "Duplicate-risk clusters remain compact and comparison confidence is visible.",
        "Manual decisions are grouped into actionable reviewer matrix rows.",
        "Safety gate remains works.",
        "All unit tests pass.",
        "git status/diff for fts/AutoFin/test-cases remains unchanged by planning stages.",
    ]


def _non_goals() -> list[str]:
    return [
        "Do not create canonical TC in this improvement plan.",
        "Do not bypass manual review.",
        "Do not force readiness to true.",
        "Do not use existing TC as a source of business rules.",
        "Do not add AutoFin-specific hacks that do not generalize.",
        "Do not run --apply, git apply or patch application.",
    ]


def _input_paths(**paths: Path | None) -> dict[str, str | None]:
    return {key: (str(value) if value is not None else None) for key, value in paths.items()}


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


def _append_numbered(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("1. none")
        return
    for index, value in enumerate(values, start=1):
        lines.append(f"{index}. {value}")


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
