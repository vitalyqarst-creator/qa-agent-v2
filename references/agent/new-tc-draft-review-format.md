# New TC Draft Review Format

Stage 9C reviews a Stage 9B draft-only new TC proposal. It is a review-only stage and does not authorize canonical test-case creation.

## Scope

The review applies to `create_new_candidate` packages such as `WPKG-000001`.

It must not:

- create canonical `.md` test-case files;
- edit existing canonical test-case files;
- apply patches;
- run `--apply`;
- perform controlled create apply;
- process completed traceability packages;
- process large or unlinked packages.

## Required Inputs

- `new-tc-draft-proposal-<package-id>.json`
- `new-tc-draft-proposal-<package-id>.md`
- `create-new-tc-context-bundle-<package-id>.json`
- `create-new-tc-context-bundle-<package-id>.md`
- canonical `fts/<ft-slug>/test-cases` directory, read-only
- supporting pipeline artifacts for traceability and source context review

## Output Artifacts

- `new-tc-draft-review-<package-id>.json`
- `new-tc-draft-review-<package-id>.md`

## JSON Model

Top-level `NewTcDraftReviewReport` fields:

- `package_id`
- `review_status`: `approved | approved-with-warnings | rejected | blocked`
- `safe_for_controlled_create_apply`
- `canonical_write_allowed`: always `false`
- `manual_review_required`: always `true`
- `drafts_total`
- `approved_drafts_count`
- `drafts_requiring_revision_count`
- `deferred_drafts_count`
- `rejected_drafts_count`
- `duplicate_risk_summary`
- `checks`
- `draft_reviews`
- `failed_checks`
- `warnings`
- `blocking_reasons`
- `reviewer_recommendation`
- `input_paths`
- `created_at_utc`
- `created_by_tool`

`DraftTestCaseReview` fields:

- `draft_id`
- `proposed_tc_id`
- `review_status`: `approved_for_create_proposal | needs_revision | defer | reject`
- `quality_score`: `low | medium | high`
- `duplicate_risk_level`
- `traceability_status`: `pass | warning | failed`
- `source_grounding_status`: `pass | warning | failed`
- `test_design_status`: `pass | warning | failed`
- `format_status`: `pass | warning | failed`
- `issues`
- `required_fixes`
- `review_notes`

## Review Rules

- Required artifacts must exist and parse.
- Package id must be `WPKG-000001`.
- Package type must be `create_new_candidate`.
- Proposal and context bundle must have no blocking reasons.
- `manual_review_required` must be `true`.
- `canonical_write_allowed` must be `false`.
- Proposed TC ids must be draft-only, for example `DRAFT-TC-WPKG-000001-*`.
- No draft may reference completed packages `WPKG-000002` / `WPKG-000003` or large/unlinked packages `WPKG-000004` / `WPKG-000005`.
- Each draft must preserve req uid, source req id when available, plan item id, impact id and change id traceability.
- Each draft req uid must exist in the context bundle candidate requirements.
- Generic placeholder steps must be marked `needs_revision`.
- Medium duplicate risk can remain `draft_with_warning`, but the draft cannot be considered ready for controlled create apply until a reviewer confirms differentiation.
- High duplicate risk should be deferred or rejected unless a later reviewed instruction provides source-backed differentiation.
- All candidate requirements must be drafted, deferred, or rejected with explicit reason.

## Status Rules

- `blocked`: required artifacts are missing or unparsable, package mismatch exists, or upstream proposal/bundle is blocked.
- `rejected`: serious safety violation exists, such as `canonical_write_allowed=true`, non-draft TC ids, or out-of-scope package processing.
- `approved-with-warnings`: proposal is safe as draft-only but one or more drafts need revision, duplicate-risk review, or source-grounding review.
- `approved`: all drafts are high/medium quality, source-grounded, non-duplicative, and ready for a later controlled create proposal.

`safe_for_controlled_create_apply` must be `false` unless every draft is approved for create proposal and there are no failed checks or blockers. Even then, Stage 9C does not itself authorize real apply.

## Markdown Expectations

The Markdown artifact must include:

- summary;
- duplicate risk summary;
- draft reviews with statuses, issues and required fixes;
- checks;
- warnings and blockers;
- explicit safety statement that no canonical TC was created or edited.
