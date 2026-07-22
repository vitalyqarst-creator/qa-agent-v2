from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from test_case_agent.coverage_graph import CoverageGraph
from test_case_agent.review_cycle.production_tc_gate import (
    validate_production_tc_content,
)
from test_case_agent.test_design import (
    DesignContext,
    DesignError,
    TestCaseDesign,
    TestDesignPlan,
    WriterCard,
    validate_design_context_for_graph,
)


class IterationContractError(ValueError):
    """Writer/reviewer output violates the runner-owned iteration contract."""


_DECISIONS = {"accepted", "changes-required", "blocked"}
_RESULT_STATUSES = {
    "calibration-pending",
    "covered",
    "not-covered",
    "incorrect",
}

REVIEWER_PROMPT_INSTRUCTION = (
    "Return JSON only. Independently check every projected source obligation "
    "against its bound test case. Review only projected conditions, actions, "
    "fixtures, and states; do not demand hypothetical or unprojected state axes. "
    "If the projection explicitly contains before/after states, missing coverage "
    "is a finding. Executable cases require status covered. "
    "candidate-ui-calibration cases require status calibration-pending and must "
    "be checked for honest pending classification, traceability, a concrete "
    "calibration question, and no invented oracle; non-executability alone is not "
    "a finding. Accepted requires every case's required status and zero findings, "
    "including warnings."
)


def reviewer_acceptance_contract() -> dict[str, Any]:
    """Return the single runner-owned acceptance policy sent to the reviewer."""

    return {
        "all_cases_must_have_required_status": True,
        "executable_result_status": "covered",
        "calibration_candidate_result_status": "calibration-pending",
        "accepted_requires_zero_findings": True,
        "calibration_review_checks": [
            "honest-pending-classification",
            "traceability",
            "concrete-calibration-question",
            "no-invented-oracle",
        ],
        "calibration_non_executability_alone_is_not_a_finding": True,
        "review_only_projected_behavior": True,
        "no_hypothetical_state_axes": True,
        "explicit_projected_before_after_states_must_be_covered": True,
        "old_test_cases_available": False,
    }


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _object(value: Any, path: str, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise IterationContractError(f"{path} must be an object")
    if set(value) != keys:
        raise IterationContractError(
            f"{path} fields differ; missing={sorted(keys - set(value))}, "
            f"unknown={sorted(set(value) - keys)}"
        )
    return value


def _one_line(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise IterationContractError(f"{path} must be non-empty single-line text")
    return value.strip()


def _strings(value: Any, path: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise IterationContractError(f"{path} must be a non-empty string array")
    return tuple(_one_line(item, f"{path}[{index}]") for index, item in enumerate(value))


def _case_traceability(graph: CoverageGraph, card: WriterCard) -> tuple[str, ...]:
    prop = next(item for item in graph.properties if item.property_id == card.property_id)
    values = [
        card.obligation_id,
        card.atom_id,
        prop.assertion_id,
        *card.requirement_codes,
    ]
    if card.source_oracle_id:
        values.append(card.source_oracle_id)
    return tuple(dict.fromkeys(item for item in values if item))


def build_writer_request(
    graph: CoverageGraph,
    plan: TestDesignPlan,
) -> dict[str, Any]:
    if plan.graph_digest != graph.digest:
        raise IterationContractError("design plan is not bound to this coverage graph")
    if plan.blocked_cards:
        raise IterationContractError("blocked cards must be resolved before writer")
    return {
        "schema_version": 1,
        "graph_digest": graph.digest,
        "cards": [item.to_dict() for item in plan.writer_cards],
        "constraints": {
            "one_case_per_card": True,
            "runner_owned_fields": [
                "tc_id",
                "traceability",
                "priority",
                "preconditions",
                "title",
                "test_data",
                "steps",
                "expected_result",
                "postconditions",
                "calibration_status",
            ],
            "structured_references_only": True,
            "no_model_authored_case_prose": True,
            "old_test_cases_available": False,
        },
    }


def writer_response_schema(
    cards: Sequence[WriterCard], graph_digest: str
) -> dict[str, Any]:
    case_keys = [item.case_key for item in cards]
    subject_ids = sorted({item.subject_id for item in cards})
    oracle_ids = sorted({item.expected_result_id for item in cards})
    fixture_ids = sorted(
        {ref.reference_id for item in cards for ref in item.fixture_references}
    )
    data_ids = sorted(
        {ref.reference_id for item in cards for ref in item.data_references}
    )
    action_ids = sorted(
        {ref.reference_id for item in cards for ref in item.action_references}
    )

    def registered_id(values: Sequence[str]) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": "string"}
        if values:
            schema["enum"] = list(values)
        return schema

    case = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": list(case_keys)},
            "case_type": {"type": "string", "enum": ["позитивный", "негативный"]},
            "subject_id": registered_id(subject_ids),
            "expected_result_id": registered_id(oracle_ids),
            "fixture_ids": {
                "type": "array",
                "items": registered_id(fixture_ids),
            },
            "data_ids": {
                "type": "array",
                "items": registered_id(data_ids),
            },
            "step_ids": {
                "type": "array",
                "items": registered_id(action_ids),
            },
        },
        "required": [
            "case_key",
            "case_type",
            "subject_id",
            "expected_result_id",
            "fixture_ids",
            "data_ids",
            "step_ids",
        ],
        "additionalProperties": False,
    }
    unresolved = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": list(case_keys)},
            "reason": {"type": "string"},
        },
        "required": ["case_key", "reason"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "graph_digest": {"type": "string", "enum": [graph_digest]},
            "cases": {"type": "array", "items": case},
            "unresolved": {"type": "array", "items": unresolved},
        },
        "required": ["schema_version", "graph_digest", "cases", "unresolved"],
        "additionalProperties": False,
    }


def validate_writer_response(
    response: Mapping[str, Any],
    *,
    graph: CoverageGraph,
    plan: TestDesignPlan,
    context: DesignContext,
) -> tuple[tuple[TestCaseDesign, ...], tuple[dict[str, str], ...]]:
    try:
        validate_design_context_for_graph(graph, context)
    except DesignError as exc:
        raise IterationContractError(f"writer design context is invalid: {exc}") from exc
    root = _object(
        response,
        "$",
        {"schema_version", "graph_digest", "cases", "unresolved"},
    )
    if root["schema_version"] != 1 or root["graph_digest"] != graph.digest:
        raise IterationContractError("writer response is not bound to this graph")
    cards = {item.case_key: item for item in plan.writer_cards}
    if plan.graph_digest != graph.digest or plan.blocked_cards:
        raise IterationContractError("writer cannot run for this design plan")
    raw_cases = root["cases"]
    raw_unresolved = root["unresolved"]
    if not isinstance(raw_cases, list) or not isinstance(raw_unresolved, list):
        raise IterationContractError("writer cases and unresolved must be arrays")
    seen: set[str] = set()
    designs: list[TestCaseDesign] = []
    unresolved: list[dict[str, str]] = []
    for index, raw in enumerate(raw_cases):
        item = _object(
            raw,
            f"$.cases[{index}]",
            {
                "case_key",
                "case_type",
                "subject_id",
                "expected_result_id",
                "fixture_ids",
                "data_ids",
                "step_ids",
            },
        )
        case_key = _one_line(item["case_key"], f"$.cases[{index}].case_key")
        if case_key not in cards or case_key in seen:
            raise IterationContractError(f"unknown or duplicate writer case_key: {case_key}")
        seen.add(case_key)
        card = cards[case_key]
        case_type = _one_line(item["case_type"], f"$.cases[{index}].case_type").casefold()
        if case_type not in {"позитивный", "негативный"}:
            raise IterationContractError(f"unsupported case_type for {case_key}")
        if item["subject_id"] != card.subject_id:
            raise IterationContractError(
                f"writer subject binding mismatch for {case_key}"
            )
        if item["expected_result_id"] != card.expected_result_id:
            raise IterationContractError(
                f"writer expected-result binding mismatch for {case_key}"
            )

        def exact_ids(field: str, references: Sequence[Any]) -> tuple[str, ...]:
            actual = _strings(
                item[field],
                f"$.cases[{index}].{field}",
                allow_empty=True,
            )
            expected = tuple(ref.reference_id for ref in references)
            if actual != expected:
                raise IterationContractError(
                    f"writer {field} binding mismatch for {case_key}; "
                    "only the ordered registered reference set is allowed"
                )
            return actual

        exact_ids("fixture_ids", card.fixture_references)
        exact_ids("data_ids", card.data_references)
        exact_ids("step_ids", card.action_references)
        test_data = tuple(ref.text for ref in card.data_references) or ("Не требуются.",)
        steps = tuple(ref.text for ref in card.action_references)
        if not steps:
            raise IterationContractError(
                f"writer card {case_key} has no registered source-backed action"
            )
        preconditions = list(context.base_preconditions)
        if card.condition_key != "always":
            condition = context.condition_preconditions.get(card.condition_key, "").strip()
            if not condition:
                raise IterationContractError(
                    f"missing runner-owned precondition for {card.condition_key}"
                )
            if not card.validation_trigger.strip():
                raise IterationContractError(
                    f"condition {card.condition_key} has no source-backed action trigger"
                )
            if condition.casefold() not in {
                item.strip().casefold() for item in preconditions
            }:
                preconditions.append(condition)
        postconditions = (
            (card.cleanup_strategy,)
            if card.cleanup_strategy.strip()
            else ("Не требуются.",)
        )
        designs.append(
            TestCaseDesign(
                case_key=case_key,
                tc_id=card.tc_id,
                status=card.status,
                title=card.runner_title,
                case_type=case_type,
                priority=(context.priorities or {}).get(case_key, "средний"),
                package_id=context.package_id,
                traceability=_case_traceability(graph, card),
                preconditions=tuple(preconditions or ["Не требуются."]),
                test_data=test_data,
                steps=steps,
                expected_result=card.observable_oracle,
                postconditions=postconditions,
                calibration_question=(
                    card.calibration_question
                    if card.status == "candidate-ui-calibration"
                    else ""
                ),
            )
        )
    for index, raw in enumerate(raw_unresolved):
        item = _object(raw, f"$.unresolved[{index}]", {"case_key", "reason"})
        case_key = _one_line(item["case_key"], f"$.unresolved[{index}].case_key")
        reason = _one_line(item["reason"], f"$.unresolved[{index}].reason")
        if case_key not in cards or case_key in seen:
            raise IterationContractError(
                f"unknown or duplicate unresolved case_key: {case_key}"
            )
        seen.add(case_key)
        unresolved.append({"case_key": case_key, "reason": reason})
    if seen != set(cards):
        raise IterationContractError(
            "writer omitted cases: " + ", ".join(sorted(set(cards) - seen))
        )
    return tuple(designs), tuple(unresolved)


@dataclass(frozen=True)
class SuiteGateReport:
    passed: bool
    graph_digest: str
    draft_sha256: str
    expected_case_count: int
    actual_case_count: int
    findings: tuple[str, ...]
    production_gate: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_suite(
    *,
    graph: CoverageGraph,
    cases: Sequence[TestCaseDesign],
    markdown: str,
    checked_path: str,
) -> SuiteGateReport:
    expected = {item.case_key: item for item in graph.cases}
    actual: dict[str, TestCaseDesign] = {}
    findings: list[str] = []
    for item in cases:
        if item.case_key in actual:
            findings.append(f"duplicate case_key: {item.case_key}")
            continue
        actual[item.case_key] = item
        source = expected.get(item.case_key)
        if source is None:
            findings.append(f"unknown case_key: {item.case_key}")
            continue
        if item.tc_id != source.tc_id:
            findings.append(f"stable TC-ID drift for {item.case_key}")
        if item.status != source.status:
            findings.append(f"case status drift for {item.case_key}")
        if set(source.obligation_ids) - set(item.traceability):
            findings.append(f"missing obligation traceability for {item.case_key}")
    for case_key in sorted(set(expected) - set(actual)):
        findings.append(f"missing case: {case_key}")
    production = validate_production_tc_content(markdown, checked_path=checked_path)
    production_payload = production.as_dict()
    accepted_conditions = {
        clause
        for prop in graph.properties
        for clause in prop.condition_clauses
    }
    condition_evidence_by_tc = {
        item.tc_id: {
            " ".join(precondition.split())[:280]
            for precondition in item.preconditions
            if precondition in accepted_conditions
        }
        for item in cases
    }
    remaining_production_findings = [
        item
        for item in production_payload["findings"]
        if not (
            item.get("id") == "production-non-reproducible-precondition"
            and item.get("evidence")
            in condition_evidence_by_tc.get(str(item.get("tc_id", "")), set())
        )
    ]
    production_payload["findings"] = remaining_production_findings
    production_payload["passed"] = not remaining_production_findings
    if remaining_production_findings:
        findings.append("production gate failed")
    return SuiteGateReport(
        passed=not findings,
        graph_digest=graph.digest,
        draft_sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        expected_case_count=len(expected),
        actual_case_count=len(actual),
        findings=tuple(findings),
        production_gate=production_payload,
    )


def build_reviewer_request(
    *,
    graph: CoverageGraph,
    cases: Sequence[TestCaseDesign],
    gate: SuiteGateReport,
) -> dict[str, Any]:
    if not gate.passed or gate.graph_digest != graph.digest:
        raise IterationContractError("reviewer may receive only a gate-passed suite")
    properties = {item.property_id: item for item in graph.properties}
    obligations = {item.obligation_id: item for item in graph.obligations}
    graph_cases = {item.case_key: item for item in graph.cases}
    projections: list[dict[str, Any]] = []
    for design in sorted(cases, key=lambda item: item.case_key):
        graph_case = graph_cases[design.case_key]
        obligation = obligations[graph_case.obligation_ids[0]]
        prop = properties[obligation.property_id]
        condition_precondition = ""
        if obligation.condition_key != "always":
            condition_precondition = (
                prop.condition_clauses[0]
                if len(prop.condition_clauses) == 1
                else prop.canonical_statement
            )
            if condition_precondition not in design.preconditions:
                raise IterationContractError(
                    f"{design.tc_id} omits exact condition {obligation.condition_key}"
                )
        projections.append(
            {
                "case_key": design.case_key,
                "tc_id": design.tc_id,
                "status": design.status,
                "source": {
                    "assertion_id": prop.assertion_id,
                    "property_kind": prop.property_kind,
                    "canonical_statement": prop.canonical_statement,
                    "requirement_codes": list(prop.requirement_codes),
                    "condition_clauses": list(prop.condition_clauses),
                },
                "obligation": {
                    "obligation_id": obligation.obligation_id,
                    "atom_id": obligation.atom_id,
                    "coverage_variant": obligation.coverage_variant,
                    "condition_key": obligation.condition_key,
                    "condition_precondition": condition_precondition,
                    "atomic_statement": obligation.atomic_statement,
                    "observable_oracle": obligation.observable_oracle,
                    "validation_trigger": obligation.validation_trigger,
                    "fixture_values": list(obligation.fixture_values),
                    "cleanup_strategy": obligation.cleanup_strategy,
                    "source_oracle_id": obligation.source_oracle_id,
                    "calibration_question": obligation.calibration_question,
                },
                "test_case": design.to_dict(),
            }
        )
    return {
        "schema_version": 1,
        "graph_digest": graph.digest,
        "draft_sha256": gate.draft_sha256,
        "cases": projections,
        "acceptance": reviewer_acceptance_contract(),
    }


def reviewer_response_schema(
    case_bindings: Sequence[tuple[str, str, str] | tuple[str, str, str, str]],
    *,
    graph_digest: str,
    draft_sha256: str,
) -> dict[str, Any]:
    case_keys = [item[0] for item in case_bindings]
    tc_ids = [item[1] for item in case_bindings]
    obligation_ids = [item[2] for item in case_bindings]
    result = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": case_keys},
            "tc_id": {"type": "string", "enum": tc_ids},
            "obligation_id": {"type": "string", "enum": obligation_ids},
            "status": {"type": "string", "enum": sorted(_RESULT_STATUSES)},
            "comment": {"type": "string"},
        },
        "required": ["case_key", "tc_id", "obligation_id", "status", "comment"],
        "additionalProperties": False,
    }
    finding = {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "case_key": {"type": "string", "enum": case_keys},
            "tc_id": {"type": "string", "enum": tc_ids},
            "obligation_id": {"type": "string", "enum": obligation_ids},
            "message": {"type": "string"},
        },
        "required": ["severity", "case_key", "tc_id", "obligation_id", "message"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "graph_digest": {"type": "string", "enum": [graph_digest]},
            "draft_sha256": {"type": "string", "enum": [draft_sha256]},
            "decision": {"type": "string", "enum": sorted(_DECISIONS)},
            "case_results": {"type": "array", "items": result},
            "findings": {"type": "array", "items": finding},
            "summary": {"type": "string"},
        },
        "required": [
            "schema_version",
            "graph_digest",
            "draft_sha256",
            "decision",
            "case_results",
            "findings",
            "summary",
        ],
        "additionalProperties": False,
    }


def validate_reviewer_response(
    response: Mapping[str, Any],
    *,
    graph: CoverageGraph,
    draft_sha256: str,
) -> tuple[bool, str]:
    root = _object(
        response,
        "$",
        {
            "schema_version",
            "graph_digest",
            "draft_sha256",
            "decision",
            "case_results",
            "findings",
            "summary",
        },
    )
    if (
        root["schema_version"] != 1
        or root["graph_digest"] != graph.digest
        or root["draft_sha256"] != draft_sha256
    ):
        raise IterationContractError("reviewer response is not bound to this draft")
    decision = _one_line(root["decision"], "$.decision")
    if decision not in _DECISIONS:
        raise IterationContractError(f"unsupported reviewer decision: {decision}")
    _one_line(root["summary"], "$.summary")
    expected: dict[str, tuple[str, str, str]] = {}
    obligations = {item.obligation_id: item for item in graph.obligations}
    for case in graph.cases:
        obligation_id = case.obligation_ids[0]
        if obligation_id not in obligations:  # pragma: no cover
            raise IterationContractError(f"graph case references unknown {obligation_id}")
        required_status = (
            "calibration-pending"
            if case.status == "candidate-ui-calibration"
            else "covered"
        )
        expected[case.case_key] = (case.tc_id, obligation_id, required_status)
    raw_results = root["case_results"]
    raw_findings = root["findings"]
    if not isinstance(raw_results, list) or not isinstance(raw_findings, list):
        raise IterationContractError("reviewer results and findings must be arrays")
    seen: set[str] = set()
    all_required_statuses = True
    for index, raw in enumerate(raw_results):
        item = _object(
            raw,
            f"$.case_results[{index}]",
            {"case_key", "tc_id", "obligation_id", "status", "comment"},
        )
        case_key = _one_line(item["case_key"], f"$.case_results[{index}].case_key")
        if case_key not in expected or case_key in seen:
            raise IterationContractError(
                f"reviewer has unknown or duplicate case_key: {case_key}"
            )
        seen.add(case_key)
        tc_id, obligation_id, required_status = expected[case_key]
        if item["tc_id"] != tc_id or item["obligation_id"] != obligation_id:
            raise IterationContractError(f"reviewer binding mismatch for {case_key}")
        status = _one_line(item["status"], f"$.case_results[{index}].status")
        if status not in _RESULT_STATUSES:
            raise IterationContractError(f"unsupported reviewer result status: {status}")
        if not isinstance(item["comment"], str):
            raise IterationContractError(f"reviewer comment for {case_key} must be text")
        all_required_statuses = all_required_statuses and status == required_status
    if seen != set(expected):
        raise IterationContractError(
            "reviewer omitted cases: " + ", ".join(sorted(set(expected) - seen))
        )
    for index, raw in enumerate(raw_findings):
        item = _object(
            raw,
            f"$.findings[{index}]",
            {"severity", "case_key", "tc_id", "obligation_id", "message"},
        )
        case_key = _one_line(item["case_key"], f"$.findings[{index}].case_key")
        if case_key not in expected:
            raise IterationContractError(f"finding references unknown case {case_key}")
        tc_id, obligation_id, _ = expected[case_key]
        if item["tc_id"] != tc_id or item["obligation_id"] != obligation_id:
            raise IterationContractError(f"finding binding mismatch for {case_key}")
        if item["severity"] not in {"error", "warning"}:
            raise IterationContractError(f"finding {index} has invalid severity")
        _one_line(item["message"], f"$.findings[{index}].message")
    accepted = (
        decision == "accepted"
        and all_required_statuses
        and not raw_findings
    )
    if decision == "accepted" and not accepted:
        raise IterationContractError(
            "accepted review requires every executable case covered, every "
            "calibration candidate calibration-pending, and zero findings"
        )
    if decision == "changes-required" and all_required_statuses and not raw_findings:
        raise IterationContractError("changes-required review has no bound reason")
    return accepted, decision


def request_sha256(request: Mapping[str, Any]) -> str:
    return _canonical_digest(request)
