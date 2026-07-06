# Traceability Backfill Review Format

Stage 7G reviews preview-only traceability backfill proposals before any possible controlled apply. It must not edit canonical test-case files, apply patches, run `--apply`, or create new test cases.

## Workflow Position / Safety Link

This format is part of `references/agent/controlled-traceability-update-workflow.md`, stage 4. `safe_for_controlled_apply=true` is meaningful only under that workflow's hard safety rules.

## Inputs

- `traceability-backfill-proposal-<package-id>.json`
- `traceability-repair-strategy.<old>-to-<new>.json`
- `traceability-mismatch-diagnostics.<old>-to-<new>.json`
- old requirements registry JSONL
- new requirements registry JSONL
- `fts/<ft-slug>/test-cases`

The review reads the current canonical test-case file to verify hashes and block boundaries, but it does not write to it.

## Outputs

- `traceability-backfill-review-<package-id>.json`
- `traceability-backfill-review-<package-id>.md`

## Review Result Fields

- `package_id`
- `review_status`: `approved`, `approved-with-warnings`, `rejected`, or `blocked`
- `safe_for_controlled_apply`: `true` only when `review_status` is `approved` or `approved-with-warnings`
- `risk_level`: `low`, `medium`, or `high`
- `checks`
- `failed_checks`
- `warnings`
- `blocking_reasons`
- `reviewer_recommendation`
- `input_paths`
- `created_at_utc`
- `created_by_tool`

## Check Fields

Each `checks[]` entry contains:

- `check_id`
- `status`: `pass`, `warning`, `failed`, or `blocked`
- `message`
- `details`

## Required Checks

The reviewer must verify:

- proposal status is not `blocked`;
- `manual_review_required = true`;
- proposed changes are limited to listed TC blocks;
- changed lines are traceability lines only;
- steps, expected result, test data, headings, and unrelated TC blocks are not changed;
- legacy refs are preserved;
- added `REQ-*` refs are not duplicated;
- added `REQ-*` refs exist in the old or new requirements registry;
- added `REQ-*` refs match `candidate_req_uids_to_backfill` from the repair strategy;
- supporting `source_req_id` refs are present in the current traceability line;
- no unrelated TC IDs are touched;
- proposal `sha256_before` equals `sha256_after` and equals the current canonical file SHA.

## Status Rules

- Missing or unreadable input artifacts produce `review_status = blocked`.
- Any non-traceability line change produces `review_status = rejected`.
- Unknown added `REQ-*` refs produce `review_status = rejected`.
- Missing supporting `source_req_id` refs produce `review_status = rejected`.
- Inherited warnings with all safety checks passing produce `review_status = approved-with-warnings`.
- `safe_for_controlled_apply = true` only for `approved` or `approved-with-warnings`.

## Safety

- Stage 7G is review only.
- Canonical test-case files are not modified.
- Patch files are not applied.
- `--apply` is not used.
