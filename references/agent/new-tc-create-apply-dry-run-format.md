# Stage 9G New TC Create Apply Dry-Run Format

Stage 9G designs a controlled create apply dry-run for new canonical test cases.
It is a preview/design stage only.

Stage 9G must not:

- create canonical test-case markdown files
- edit files under `fts/AutoFin/test-cases`
- create backups
- create patch files
- create real apply reports
- run `--apply`
- use `git apply` or external patch tools
- authorize Stage 9H or any real apply

Human-readable Stage 9G reports should be written in Russian for AutoFin
workflow use. Field names remain stable English machine keys.

## Required Inputs

- `new-tc-revised-draft-proposal-<package_id>.json`
- `new-tc-revised-draft-review-<package_id>.json`
- `agent-decision-validation-<package_id>.json`
- `agent-decision-resolution-<package_id>.json`
- `manual-decision-matrix-<package_id>.json`
- `create-new-tc-context-bundle-<package_id>.json`
- read-only `fts/AutoFin/test-cases`

The CLI must stop before writing Stage 9G artifacts if canonical test-cases are
dirty.

## Output Files

- `new-tc-create-apply-dry-run-<package_id>.json`
- `new-tc-create-apply-dry-run-<package_id>.md`

No patch, backup, canonical TC, or apply report files are produced.

## Top-Level Fields

- `package_id`
- `dry_run_status`: `pass | pass-with-warnings | blocked`
- `source_revised_proposal_path`
- `source_revised_review_path`
- `dry_run_items`
- `excluded_candidates`
- `target_file_plan`
- `tc_id_plan`
- `traceability_plan`
- `collision_checks`
- `format_checks`
- `safety_checks`
- `rollback_plan`
- `stage_9h_readiness`
- `canonical_write_allowed`: always `false`
- `real_apply_authorized`: always `false`
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## CreateApplyDryRunItem

- `dry_run_item_id`
- `source_revised_draft_id`
- `proposed_tc_id`
- `target_file_path`
- `target_section`
- `planned_operation`: `create_new_file | append_to_existing_file | blocked`
- `dry_run_decision`: `dry_run_allowed | dry_run_allowed_with_warnings | blocked`
- `generated_markdown_preview`
- `traceability_refs`
- `req_uids`
- `source_req_ids`
- `source_evidence_refs`
- `source_agent_decision_row_id`
- `source_validation_result_id`
- `review_result`
- `review_warnings`
- `collision_risks`
- `format_warnings`
- `safety_warnings`
- `creates_or_edits_canonical_tc`: always `false`

## Candidate Eligibility

Use only revised candidates that:

- are present in the Stage 9E proposal
- have a Stage 9F review result of `approved` or `approved-with-warnings`
- have no failed Stage 9F safety checks
- include source decision and validation traceability
- include source draft ids
- include `req_uids` and source evidence refs

If `source_req_ids` are absent but `req_uids` and source evidence refs are
present, the item may remain in dry-run design as
`dry_run_allowed_with_warnings`; the builder must not fabricate source req ids.

## Target and Collision Rules

Stage 9G may plan `create_new_file` or `append_to_existing_file`, but it must not
write the file. It must block or warn for:

- duplicate proposed TC ids inside the dry-run
- proposed TC ids that already exist in canonical test-cases
- duplicate target filenames
- existing target files
- aggregate/index file targets
- ambiguous target section
- missing source traceability

Aggregate/index files, including `14-application-card.md`, must not be targeted.

## Markdown Preview

`generated_markdown_preview` is embedded only in the dry-run artifact. It must
include:

- TC ID
- title
- preconditions
- steps
- expected results
- traceability refs
- source evidence refs
- explicit `dry-run preview only` safety note

## Stage 9H Readiness

`stage_9h_readiness` may recommend a future Stage 9H design only when there are
no blocked dry-run items.

It must always include:

- `real_apply_authorized: false`
- `requires_explicit_user_approval: true`
- `requires_clean_git_status: true`
- `requires_no_blocked_dry_run_items: true`
- `requires_review_of_warnings: true`

Stage 9G never authorizes real apply. Stage 9H requires a separate explicit user
request.
