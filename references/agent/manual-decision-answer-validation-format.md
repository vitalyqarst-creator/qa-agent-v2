# Manual Decision Answer Validation Format

Stage 9D.7 receives and validates reviewer answers for a manual decision matrix. It is not Stage 9E and does not create revised draft proposals.

This stage is read-only for canonical test cases. It may validate reviewer intent and normalize future draft-only actions, but it must not execute those actions.

## Inputs

- `manual-decision-matrix-<package_id>.json`
- optional `manual-decision-reviewer-answers-<package_id>.json`

If reviewer answers are missing, the stage must create an answer template and a validation artifact with `validation_status=awaiting_reviewer_answers`.

## Outputs

- `manual-decision-answer-template-<package_id>.json`
- `manual-decision-answer-template-<package_id>.md`
- `manual-decision-answer-validation-<package_id>.json`
- `manual-decision-answer-validation-<package_id>.md`

## Answer Template

Top-level fields:

- `package_id`
- `template_status`: `pass`, `pass-with-warnings`, or `blocked`
- `source_matrix_path`
- `reviewer_rows`
- `answer_schema_version`
- `instructions_for_reviewer`
- `allowed_option_catalog`
- `required_evidence_rules`
- `safety_rules`
- `canonical_write_allowed`: always false
- `manual_review_required`: true
- `stage_9e_authorized`: false
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

Each reviewer row must preserve allowed options from the matrix and provide empty answer placeholders. The template must not pre-select options or recommend unsafe defaults.

## Reviewer Answers

Expected reviewer answers file:

- `package_id`
- `matrix_id` or `source_matrix_path`
- `answer_schema_version`
- `answers`
- `answered_by`
- `answered_at_utc`
- `review_notes`

Each answer:

- `row_id`
- `cluster_id`
- `selected_option_id`
- `reviewer_rationale`
- `source_evidence`
- `existing_tc_review_notes`
- `business_clarification`
- `no_new_tc_rationale`
- `defer_reason`
- `split_guidance`
- `answered_by`
- `answered_at_utc`

## Validation

Top-level fields:

- `package_id`
- `validation_status`: `awaiting_reviewer_answers`, `pass`, `pass-with-warnings`, `blocked`, or `rejected`
- `source_matrix_path`
- `source_answers_path`
- `answer_rows_total`
- `answer_rows_valid`
- `answer_rows_missing`
- `answer_rows_rejected`
- `validated_answers`
- `missing_answers`
- `invalid_answers`
- `unsafe_answers`
- `normalized_reviewer_decisions`
- `readiness_after_answers`
- `stage_9e_gate`
- `canonical_write_allowed`: always false
- `manual_review_required`: true
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## Validation Rules

The validator must reject or block answers when:

- `package_id` does not match;
- a blocking matrix row has no answer;
- an answer references an unknown `row_id`;
- multiple answers target the same `row_id`;
- selected option is not allowed for the row;
- `reviewer_rationale` is missing;
- selected option requires source evidence and `source_evidence` is empty or not source-like;
- selected option requires existing TC review and notes do not explicitly state that the existing TC was used only as coverage evidence;
- no-new-TC, defer or split options lack their specific rationale fields;
- the answer implies direct canonical TC create/edit/apply;
- the answer uses existing TC text as a source of business rules.

`extend_existing_tc` is valid only as a future-stage reviewed action and must not directly edit canonical files.

## Stage 9E Gate

`stage_9e_allowed=true` only when:

- reviewer answers file exists;
- all blocking rows are answered;
- all answers are valid or valid-with-warnings;
- unsafe answers count is zero;
- at least one valid answer enables `revise_draft`, `replace_draft`, or `split_candidate`;
- source evidence requirements are satisfied;
- Stage 9E remains draft-only;
- canonical writes remain disabled.

Without reviewer answers:

- `validation_status=awaiting_reviewer_answers`
- `stage_9e_allowed=false`
- `readiness_after_answers.can_prepare_stage_9e_draft_only=false`
- `canonical_write_allowed=false`
- `manual_review_required=true`

## Markdown

Template markdown should include summary, reviewer instructions, safety rules, answer table, allowed option catalog, evidence rules and empty placeholders.

Validation markdown should include summary, missing/invalid/unsafe answers, validated answers, normalized decisions, Stage 9E gate, required next action and safety statement.
