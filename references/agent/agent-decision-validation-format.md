# Agent Decision Validation Format

Stage 9D.9 validates `agent_decision_resolution` and independently hardens the Stage 9E gate. It does not create Stage 9E output, reviewer answers, canonical test-cases, patches, or apply reports.

## Output

- `agent-decision-validation-<package_id>.json`
- `agent-decision-validation-<package_id>.md`

## Main Object

`AgentDecisionValidationReport` fields:

- `package_id`
- `validation_status`: `pass | pass-with-warnings | blocked | rejected`
- `source_resolution_path`
- `source_artifacts`
- `validation_checks`
- `decision_validation_results`
- `validated_stage_9e_scope`
- `rejected_stage_9e_scope`
- `human_review_scope`
- `deferred_scope`
- `gate_hardening_summary`
- `stage_9e_gate_hardened`
- `readiness_after_validation`
- `safety_summary`
- `canonical_write_allowed`: always `false`
- `manual_review_required`
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## Decision Result

`AgentDecisionValidationResult` fields:

- `row_id`
- `cluster_id`
- `selected_allowed_next_action`
- `original_decision_status`
- `original_confidence`
- `original_confidence_score`
- `original_requires_human_review`
- `validation_result`: `valid | valid-with-warnings | rejected | unsafe | human-review-required | deferred`
- `stage_9e_eligible`
- `validated_stage_9e_action`
- `required_evidence_checks`
- `confidence_checks`
- `safety_checks`
- `traceability_checks`
- `coverage_checks`
- `duplicate_risk_checks`
- `split_candidate_checks`
- `existing_tc_evidence_checks`
- `reasoning`
- `blocking_reasons`
- `warnings`

## Hardened Gate

`stage_9e_gate_hardened` fields:

- `stage_9e_allowed`
- `stage_9e_allowed_scope`
- `stage_9e_rejected_scope`
- `stage_9e_blockers`
- `stage_9e_warnings`
- `stage_9e_safety_conditions`
- `canonical_write_allowed`: `false`
- `requires_draft_only_output`: `true`
- `requires_agent_decision_traceability`: `true`
- `requires_validation_traceability`: `true`
- `requires_no_human_review_rows_in_scope`: `true`
- `requires_no_deferred_rows_in_scope`: `true`
- `requires_no_low_confidence_rows_in_scope`: `true`
- `requires_no_unclassified_warnings_in_scope`: `true`

## Validation Rules

Reject or block when:

- package ids do not match;
- the resolution is missing or unparsable;
- `canonical_write_allowed=true`;
- agent decisions are missing;
- resolution row ids do not match matrix row ids;
- a decision uses reviewer/human approval terminology as its decision source;
- a Stage 9E candidate requires human review;
- a Stage 9E candidate confidence score is below `0.70`;
- a Stage 9E candidate lacks source-backed object, action, or observable oracle;
- a Stage 9E candidate lacks source refs;
- a Stage 9E candidate uses existing TC as a business-rule source;
- a Stage 9E candidate has safety warnings;
- a Stage 9E candidate implies canonical creation/edit/apply.

For `split_candidate`:

- affected requirements must be listed;
- affected drafts must be listed;
- affected drafts must exist in the source proposal;
- split boundaries must be source-backed by table/anchor evidence;
- split must not require invented action/oracle.

If `MDR-000012` is present in the resolver scope, the validation report must explicitly say whether it passed the hardened gate or was rejected from Stage 9E scope.
