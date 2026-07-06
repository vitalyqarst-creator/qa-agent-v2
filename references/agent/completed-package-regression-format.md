# Completed Package Regression Format

Completed package regression is a read-only validation stage for small packages that have already completed controlled traceability update apply and post-apply validation.

It must not run `--apply`, apply patches, call `git apply`, create test cases, or modify canonical test-case files.

## Workflow Position / Safety Link

This format is part of `references/agent/controlled-traceability-update-workflow.md`, stage 10. Stale writer proposals after final apply are warnings; unrelated dirty test-case files block regression and require separate user-directed isolation.

## Scope

The Stage 8D mini regression validates only the completed small packages:

- `WPKG-000002`
- `WPKG-000003`

It must not process `WPKG-000001`, `WPKG-000004`, or `WPKG-000005`.

## Output Files

- `completed-package-regression-WPKG-000002-WPKG-000003.json`
- `completed-package-regression-WPKG-000002-WPKG-000003.md`

## Check Model

`CompletedPackageRegressionCheck`:

- `check_id`
- `status`: `pass | warning | failed | blocked`
- `message`
- `details`

## Report Model

`CompletedPackageRegressionReport`:

- `regression_status`: `pass | pass-with-warnings | failed | blocked`
- `completed_packages`
- `validated_test_cases`
- `final_state_valid_count`
- `safe_for_next_stage_count`
- `old_refs_absent`
- `new_refs_present`
- `duplicate_req_refs_found`
- `regressions_found`
- `checks`
- `failed_checks`
- `warnings`
- `blocking_reasons`
- `git_state_summary`
- `input_paths`
- `created_at_utc`
- `created_by_tool`

## Status Rules

- `blocked`: required artifacts are missing or unparsable.
- `failed`: final state is invalid, old/intermediate refs remain, final refs are missing, duplicate `REQ-*` refs exist, or unrelated test-case files/TCs changed unexpectedly.
- `pass-with-warnings`: final state is valid but inherited warnings exist, proposals are now stale because the replacements are already complete, or git state is clean/baselined with nothing to commit.
- `pass`: final state is valid and no warnings, failed checks, or blockers exist.

## Required Validation

The regression validates:

- post-apply validation artifacts for both completed packages;
- current traceability lines in the expected TC blocks;
- absence of old/intermediate `REQ-*` refs;
- presence of final `REQ-*` refs;
- preservation of legacy refs;
- absence of duplicate `REQ-*` refs;
- update-plan consistency for completed old/new mappings;
- old and final `REQ-*` refs exist in the old or new requirements registry;
- completed writer proposals are treated as stale after final apply, not as current TC defects;
- git state is clean or limited to expected traceability changes for completed packages;
- no collateral changes to unrelated TC blocks in the target files.

Clean git state is acceptable when final state is valid.
