from __future__ import annotations

from dataclasses import dataclass

from test_case_agent.review_cycle.contracts import ContractValidationError


@dataclass(frozen=True)
class TransitionDecision:
    current_stage_status: str
    scenario: str
    outcome: str
    next_stage_status: str
    terminal: bool = False
    terminal_gates_required: bool = False


_STATIC_RULES: dict[tuple[str, str, str], TransitionDecision] = {}


def _register(
    current: str,
    scenario: str,
    outcome: str,
    next_status: str,
    *,
    terminal: bool = False,
    terminal_gates_required: bool = False,
) -> None:
    key = (current, scenario, outcome)
    _STATIC_RULES[key] = TransitionDecision(
        current_stage_status=current,
        scenario=scenario,
        outcome=outcome,
        next_stage_status=next_status,
        terminal=terminal,
        terminal_gates_required=terminal_gates_required,
    )


for initial_status in ("scope-ready-for-writer", "scope-gap-review-passed"):
    _register(
        initial_status,
        "writer.session_initial_draft",
        "draft-ready",
        "writer-draft-ready",
    )
_register(
    "scope-ready-for-gap-review",
    "reviewer.scope_gap_review",
    "accepted",
    "scope-ready-for-writer",
)
_register(
    "scope-ready-for-gap-review",
    "reviewer.scope_gap_review",
    "changes-required",
    "blocked-input",
    terminal=True,
)
_register(
    "writer-draft-ready",
    "reviewer.structure_preflight",
    "accepted",
    "semantic-review-ready",
)
_register(
    "writer-draft-ready",
    "reviewer.structure_preflight",
    "changes-required",
    "structure-preflight-blocked",
)
_register(
    "structure-preflight-blocked",
    "writer.remediation.structure_preflight",
    "draft-ready",
    "writer-draft-ready",
)
_register(
    "semantic-review-ready",
    "reviewer.semantic_traceability_test_design",
    "accepted",
    "format-review-ready",
)
_register(
    "semantic-revision-needed",
    "writer.session_semantic_revision",
    "draft-ready",
    "semantic-review-ready",
)
_register(
    "format-review-ready",
    "reviewer.structure_format_final",
    "changes-required",
    "format-revision-needed",
)
_register(
    "format-review-ready",
    "reviewer.structure_format_final",
    "accepted",
    "signed-off",
    terminal=True,
    terminal_gates_required=True,
)
_register(
    "format-revision-needed",
    "writer.session_format_revision",
    "draft-ready",
    "final-regression-ready",
)
_register(
    "final-regression-ready",
    "reviewer.semantic_regression",
    "accepted",
    "signed-off",
    terminal=True,
    terminal_gates_required=True,
)
_register(
    "final-regression-ready",
    "reviewer.semantic_regression",
    "changes-required",
    "round-cap-reached",
    terminal=True,
)


def resolve_transition(
    *,
    current_stage_status: str,
    scenario: str,
    outcome: str,
    semantic_round: int,
    terminal_gates_passed: bool = False,
) -> TransitionDecision:
    for field_name, value in (
        ("current_stage_status", current_stage_status),
        ("scenario", scenario),
        ("outcome", outcome),
    ):
        if not isinstance(value, str) or not value:
            raise ContractValidationError(f"{field_name} must be non-empty text")
    if (
        isinstance(semantic_round, bool)
        or not isinstance(semantic_round, int)
        or not 0 <= semantic_round <= 2
    ):
        raise ContractValidationError("semantic_round must be an integer from 0 to 2")
    if not isinstance(terminal_gates_passed, bool):
        raise ContractValidationError("terminal_gates_passed must be boolean")
    if outcome == "signed-off":
        raise ContractValidationError(
            "LLM stages cannot return signed-off; only the runner may apply a gated terminal transition"
        )
    if outcome == "blocked":
        return TransitionDecision(
            current_stage_status=current_stage_status,
            scenario=scenario,
            outcome=outcome,
            next_stage_status="blocked-input",
            terminal=True,
        )
    if (
        current_stage_status == "semantic-review-ready"
        and scenario == "reviewer.semantic_traceability_test_design"
        and outcome == "changes-required"
    ):
        if semantic_round >= 2:
            return TransitionDecision(
                current_stage_status=current_stage_status,
                scenario=scenario,
                outcome=outcome,
                next_stage_status="round-cap-reached",
                terminal=True,
            )
        return TransitionDecision(
            current_stage_status=current_stage_status,
            scenario=scenario,
            outcome=outcome,
            next_stage_status="semantic-revision-needed",
        )
    key = (current_stage_status, scenario, outcome)
    decision = _STATIC_RULES.get(key)
    if decision is None:
        raise ContractValidationError(
            "No allowlisted v2 transition for "
            f"stage_status={current_stage_status!r}, scenario={scenario!r}, outcome={outcome!r}"
        )
    if decision.terminal_gates_required and not terminal_gates_passed:
        raise ContractValidationError(
            "terminal signed-off transition requires deterministic terminal gates to pass"
        )
    return decision
