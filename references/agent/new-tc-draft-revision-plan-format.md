# New TC Draft Revision Plan Format

This artifact is a planning-only response to a reviewed draft-only new TC proposal.
It does not authorize canonical test-case creation or edits.

## Inputs

- `new-tc-draft-proposal-<package_id>.json`
- `new-tc-draft-review-<package_id>.json`
- `create-new-tc-context-bundle-<package_id>.json`
- optional supporting pipeline artifacts listed in `input_paths`
- canonical `test-cases` directory as read-only context

## Output Files

- `new-tc-draft-revision-plan-<package_id>.json`
- `new-tc-draft-revision-plan-<package_id>.md`

## Top-Level Fields

- `package_id` - package covered by the plan.
- `plan_status` - `pass`, `pass-with-warnings`, or `blocked`.
- `source_review_path` - Stage 9C review artifact used as the decision source.
- `source_proposal_path` - Stage 9B proposal artifact used as the draft source.
- `revision_items` - per-draft instructions for the next revised draft proposal.
- `duplicate_risk_actions` - explicit actions for duplicate-risk decisions.
- `source_grounding_actions` - source facts and missing facts that must guide revision.
- `coverage_actions` - candidate requirement coverage/accounting.
- `deferred_or_rejected_actions` - rejected or deferred drafts that must not be silently promoted.
- `revision_summary` - counts by target action and safety state.
- `ready_for_revised_draft_proposal` - true only when all required decisions are resolved.
- `canonical_write_allowed` - always false for this stage.
- `manual_review_required` - true for this stage.
- `warnings` and `blocking_reasons` - safety and input issues.

## Revision Item

Each item has:

- `draft_id`
- `proposed_tc_id`
- `current_review_status`
- `target_revision_status`: `revise`, `replace`, `defer`, or `keep_rejected`
- `priority`: `high`, `medium`, or `low`
- `required_fixes`
- `source_facts_to_use`
- `concrete_step_guidance`
- `expected_result_guidance`
- `test_data_guidance`
- `traceability_guidance`
- `duplicate_risk_guidance`
- `acceptance_criteria`
- `blocking_questions`
- `warnings`

Rejected drafts must be handled explicitly as `replace`, `defer`, or `keep_rejected`.
They must not be silently treated as approved.

## Duplicate Risk Action

Each duplicate-risk action records:

- `draft_id`
- `candidate_req_uid`
- `similar_tc_id`
- `similar_file_path`
- `risk`
- `action`: `differentiate`, `defer`, `maybe_extend_existing`, or `no_action`
- `rationale`
- `required_manual_decision`

Medium duplicate risk requires differentiation before a revised draft can be considered safe.
High duplicate risk requires deferral or an explicit decision to extend an existing TC.

## Safety Rules

- This stage is planning-only.
- It must not create or edit canonical test-case files.
- It must not modify the original Stage 9B proposal.
- It must not run `--apply`.
- It must not apply patches.
- It must not process packages outside the requested package.
- `canonical_write_allowed` must remain false.
