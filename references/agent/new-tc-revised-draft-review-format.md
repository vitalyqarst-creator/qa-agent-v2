# Stage 9F New TC Revised Draft Review Format

Stage 9F reviews the Stage 9E revised draft-only proposal. It does not create or
edit canonical test-cases and does not authorize real controlled create apply.

Human-readable Stage 9F reports should be written in Russian for AutoFin
workflow use. Field names remain stable English machine keys.

## Required Inputs

- `new-tc-revised-draft-proposal-<package_id>.json`
- `agent-decision-validation-<package_id>.json`
- `new-tc-draft-proposal-<package_id>.json`

The command must stop before review if canonical test-cases are dirty.

## Output Files

- `new-tc-revised-draft-review-<package_id>.json`
- `new-tc-revised-draft-review-<package_id>.md`

## Top-Level Fields

- `package_id`
- `review_status`: `approved | approved-with-warnings | needs-revision | rejected | blocked`
- `source_revised_proposal_path`
- `draft_reviews`
- `traceability_checks`
- `source_grounding_checks`
- `duplicate_risk_checks`
- `format_checks`
- `safety_checks`
- `stage_9g_readiness`
- `canonical_write_allowed`: always `false`
- `manual_review_required`: always `true`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## RevisedDraftReview

Each review item includes:

- `draft_id`
- `proposed_tc_id`
- `review_result`: `approved | approved-with-warnings | needs-revision | rejected`
- `checks`
- `source_grounding_result`
- `format_result`
- `traceability_result`
- `duplicate_risk_result`
- `safety_result`
- `issues`
- `required_fixes`
- `warnings`

## Required Review Checks

Stage 9F should verify:

- the proposal package id matches the requested package
- every candidate belongs to the hardened Stage 9E scope
- referenced source draft ids exist in the original Stage 9B proposal
- traceability refs / requirement ids are present
- source evidence refs are present
- steps and expected results are source-backed and non-placeholder
- canonical writes are disabled
- existing TC evidence is not used as a business-rule source
- duplicate risk is explicitly described

## Stage 9G Readiness

`stage_9g_readiness.recommended` may be `true` only when all reviewed drafts are
`approved` or `approved-with-warnings`.

Even when Stage 9G readiness is recommended:

- `stage_9g_readiness.authorizes_real_apply` must be `false`
- `stage_9g_readiness.canonical_tc_created` must be `false`
- `stage_9g_readiness.canonical_tc_modified` must be `false`

Stage 9F can recommend a future controlled create apply design/dry-run, but it
must not execute Stage 9G or any real apply.
