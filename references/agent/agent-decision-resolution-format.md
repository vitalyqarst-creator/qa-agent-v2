# Agent Decision Resolution Format

Stage 9D.8 creates an `agent_decision_resolution` artifact. It is an AI-generated decision proposal, not reviewer answers, not human approval, and not Stage 9E output.

## Scope

The resolver is read-only. It reads Stage 9D artifacts and writes:

- `agent-decision-resolution-<package_id>.json`
- `agent-decision-resolution-<package_id>.md`

It must not create canonical test-cases, revised draft proposals, apply reports, or reviewer answers JSON.

## Main Object

`AgentDecisionResolution` fields:

- `package_id`
- `resolution_status`: `pass | pass-with-warnings | blocked`
- `benchmark_name`
- `source_artifacts`
- `agent_decisions`
- `decision_summary`
- `stage_9e_candidate_scope`
- `deferred_or_human_review_scope`
- `evidence_quality_summary`
- `safety_summary`
- `readiness_after_agent_resolution`
- `stage_9e_gate`
- `canonical_write_allowed`: always `false`
- `manual_review_required`
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## Agent Decision

Each `AgentDecision` represents one row from the manual decision matrix.

Required fields:

- `row_id`
- `cluster_id`
- `cluster_type`
- `selected_option_id`
- `selected_allowed_next_action`
- `decision_source`: always `agent_resolution`
- `decision_status`: `resolved | resolved-with-warnings | needs_human_review | deferred | rejected | unsafe`
- `confidence`: `high | medium | low`
- `confidence_score`: `0.0..1.0`
- `confidence_reasons`
- `evidence`
- `source_evidence_refs`
- `source_fact_coverage`
- `existing_tc_coverage_evidence`
- `duplicate_risk_assessment`
- `missing_facts`
- `rationale`
- `normalized_effect`
- `affected_drafts`
- `affected_requirements`
- `requires_human_review`
- `enables_stage_9e_draft_only`
- `creates_or_edits_canonical_tc`: always `false`
- `safety_warnings`
- `blocking_reasons`

## Safety Rules

- Agent decisions must not be called reviewer answers, human decisions, or approved decisions.
- `decision_source` must be `agent_resolution`.
- Existing TC may be used only as coverage/comparison evidence.
- Existing TC must not be used as a source of business rules.
- Low-confidence rows must not enable Stage 9E.
- Rows with missing source-backed action or observable expected result must be routed to `needs_human_review`, `deferred`, or `request_source_clarification`.
- Stage 9E scope, if any, must be subset-based and draft-only.
- Canonical write remains disabled even when `stage_9e_allowed=true`.

## Stage 9E Gate

`stage_9e_gate` fields:

- `stage_9e_allowed`
- `stage_9e_allowed_scope`
- `stage_9e_blockers`
- `stage_9e_safety_conditions`
- `canonical_write_allowed`: `false`
- `requires_draft_only_output`: `true`
- `requires_agent_decision_traceability`: `true`
- `requires_no_low_confidence_rows`: `true`

Rows marked `needs_human_review`, `deferred`, `request_source_clarification`, or `no_new_tc_with_rationale` do not block a safe Stage 9E subset. They remain listed in `deferred_or_human_review_scope`.

## Markdown

The Markdown report must include:

1. Summary.
2. Decision policy used.
3. Decision summary table.
4. Agent decision table.
5. Duplicate-risk decisions.
6. Source-grounding decisions.
7. Defer/human-review decisions.
8. Stage 9E gate.
9. Safety statement.
10. Warnings and blocking reasons.
