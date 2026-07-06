# Stage 9E New TC Revised Draft Proposal Format

Stage 9E creates draft-only revised new-test-case candidates after the hardened
agent decision validation gate. It must not create, edit, or apply canonical
test-case files.

Human-readable Stage 9E reports should be written in Russian for AutoFin
workflow use. Field names remain stable English machine keys.

## Required Inputs

- `agent-decision-validation-<package_id>.json`
- `agent-decision-resolution-<package_id>.json`
- `new-tc-draft-proposal-<package_id>.json`
- `create-new-tc-context-bundle-<package_id>.json`

Optional supporting inputs may include draft review, revision plan, revision
decision pack, and residual source grounding analysis.

Stage 9E is allowed only when:

- `stage_9e_gate_hardened.stage_9e_allowed = true`
- canonical test-cases are clean before the command starts
- the builder uses only `validated_stage_9e_scope.row_ids`

Reviewer CSV/answer packs are not primary sources and must not be converted into
human approval artifacts by Stage 9E.

## Output Files

- `new-tc-revised-draft-proposal-<package_id>.json`
- `new-tc-revised-draft-proposal-<package_id>.md`

## Top-Level Fields

- `package_id`
- `proposal_status`: `pass | pass-with-warnings | blocked`
- `source_validation_path`
- `source_resolution_path`
- `source_draft_proposal_path`
- `hardened_scope_used`
- `revised_draft_candidates`
- `candidate_count`
- `blocked_candidate_count`
- `draft_ready_count`
- `canonical_write_allowed`: always `false`
- `manual_review_required`: always `true`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## RevisedDraftCandidate

Each candidate must include:

- `draft_id`
- `proposed_tc_id`
- `source_agent_decision_row_id`
- `source_validation_result_id`
- `source_action`
- `source_draft_ids`
- `candidate_status`: `draft-ready | draft-with-warnings | blocked`
- `title`
- `preconditions`
- `steps`
- `expected_results`
- `traceability_refs`
- `source_req_ids`
- `req_uids`
- `source_evidence_refs`
- `source_fact_summary`
- `agent_decision_rationale`
- `validation_rationale`
- `duplicate_risk_notes`
- `existing_tc_coverage_notes`
- `draft_quality_flags`
- `manual_review_notes`
- `creates_or_edits_canonical_tc`: always `false`

## Safety Rules

- Do not process rows outside `validated_stage_9e_scope.row_ids`.
- Do not process deferred, human-review, rejected, or non-Stage-9E rows.
- Do not invent source draft ids or requirement ids.
- Do not use existing TC content as a business-rule source.
- Existing TC evidence may only be used for duplicate/coverage comparison notes.
- Do not use generic executable placeholders such as `TBD`, `уточнить`, or
  `проверить корректность`.
- If source-backed action, object, or oracle is missing, the candidate must be
  `blocked`.
- Stage 9E must not write under `fts/AutoFin/test-cases`.
