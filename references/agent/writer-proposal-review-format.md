# Writer Proposal Review Format

Stage 8A reviews a writer dry-run traceability update proposal before any controlled apply step.

The review is read-only:

- it must not edit canonical test-case files;
- it must not apply preview patches;
- it must not run `--apply`;
- it must not create new test cases;
- it must not change writer/reviewer workflow.

## Workflow Position / Safety Link

This format is part of `references/agent/controlled-traceability-update-workflow.md`, stage 7. It assumes backfill has already made old generated `REQ-*` refs available in the traceability line.

## Inputs

- `writer-dry-run-proposal-<package-id>-after-backfill.json`
- optional matching Markdown and preview patch files
- `test-case-update-plan.<old>-to-<new>.json`
- `impact-report.<old>-to-<new>.json`
- `requirements-diff.<old>-to-<new>.json`
- old and new requirements registry JSONL files
- canonical `test-cases` directory

## Report

`WriterProposalReviewReport`:

- `package_id`
- `review_status`: `approved | approved-with-warnings | rejected | blocked`
- `safe_for_controlled_apply`
- `risk_level`: `low | medium | high`
- `checks`
- `failed_checks`
- `warnings`
- `blocking_reasons`
- `reviewer_recommendation`
- `input_paths`
- `git_state`
- `created_at_utc`
- `created_by_tool`

`WriterProposalReviewCheck`:

- `check_id`
- `status`: `pass | warning | failed | blocked`
- `message`
- `details`

## Required Checks

The review verifies:

- proposal metadata: package id, non-blocked status, proposed changes, empty missing information, manual review flag, risk level;
- scope: file-bound proposal, only listed TC IDs, no unrelated TC IDs;
- current file state: target file exists, current TC block matches proposal original block, current traceability line contains legacy refs and old backfilled `REQ-*` refs;
- patch safety: proposed block changes only traceability lines, not steps, expected result, test data, headings, package id, or other metadata;
- replacement correctness: old `REQ-*` refs are present before replacement, new `REQ-*` refs are present after replacement, old refs are removed only from the traceability line, legacy refs are preserved, no duplicate `REQ-*` refs remain;
- registry validation: old and new `REQ-*` refs exist in old or new requirements registry and use valid `REQ-AUTOFIN-*` format;
- update plan validation: proposal old/new ref mappings must match the corresponding plan item mappings;
- diff consistency: unified diff must match structured original/proposed TC blocks;
- git state recording: `git status --short`, `git diff`, and `git diff --cached` are recorded for the target file.

## Status Rules

- Any non-traceability-line change rejects the review.
- Any proposal touching TC IDs outside `affected_test_case_ids` rejects the review.
- Any old/new `REQ-*` mapping mismatch with the update plan rejects the review.
- Any missing registry entry for old or new `REQ-*` refs rejects the review.
- If the current traceability line does not contain required old backfilled `REQ-*` refs, the review is blocked.
- If all safety checks pass and only inherited warnings remain, the review is `approved-with-warnings`.
- `safe_for_controlled_apply=true` only when `review_status` is `approved` or `approved-with-warnings`.

Clean git state is acceptable when the current file already contains the backfilled refs required by the after-backfill proposal.
