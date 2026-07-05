# Writer Traceability Post-Apply Validation Format

Stage 8C validates a completed controlled writer traceability update apply. It is read-only.

The validator must not:

- run `--apply`;
- apply a patch;
- edit canonical test-case files;
- create new test cases;
- change writer/reviewer workflow.

## Inputs

- `writer-traceability-update-apply-<package-id>-after-backfill.json`
- `writer-dry-run-proposal-<package-id>-after-backfill.json`
- `writer-proposal-review-<package-id>-after-backfill.json`
- `test-case-update-plan.<old>-to-<new>.json`
- old and new requirements registry JSONL files
- canonical `test-cases` directory

## Report

`WriterTraceabilityPostApplyValidationReport`:

- `package_id`
- `validation_status`: `pass | pass-with-warnings | failed | blocked`
- `final_state_valid`
- `git_change_state`: `uncommitted_expected_change | final_state_already_baselined | unexpected_changes | missing_expected_final_state`
- `safe_to_commit`
- `safe_for_next_stage`
- `commit_action`: `commit_current_diff | nothing_to_commit | investigate`
- `file_path`
- `affected_test_case_ids`
- `checks`
- `failed_checks`
- `warnings`
- `blocking_reasons`
- `git_state`
- `input_paths`
- `created_at_utc`
- `created_by_tool`

`WriterTraceabilityPostApplyValidationCheck`:

- `check_id`
- `status`: `pass | warning | failed | blocked`
- `message`
- `details`

## Required Checks

The validator checks:

- apply report status: `applied`, `dry_run=false`, empty blocking reasons, expected applied change count, expected file count, backup path;
- scope: expected target file, expected TC IDs, no staged changes, no other changed test-case files;
- git diff: exactly one target hunk, changed hunk belongs to expected TC, changed lines are traceability lines only;
- traceability content: legacy refs preserved, new `REQ-*` refs present, old `REQ-*` refs absent, no duplicate `REQ-*` refs;
- registry: old and new `REQ-*` refs exist in old or new requirements registry;
- backup: backup exists, backup contains old traceability line, current file differs from backup only in expected traceability line.

## Git Change State

The validator separates final content correctness from git diff availability.

`uncommitted_expected_change`:

- exactly one changed test-case file is present;
- it is the expected target file;
- the target diff has one hunk;
- changed lines belong to the expected TC;
- changed lines are traceability lines only;
- no staged changes exist.

`final_state_already_baselined`:

- git status, target diff, and cached diff are clean;
- current file already contains the expected final traceability state;
- backup/current comparison still confirms the expected traceability-line-only replacement.

This state is not a failure. It means there is nothing to commit locally, but the pipeline may continue.

`missing_expected_final_state`:

- git is clean;
- current file does not contain the expected final traceability state.

`unexpected_changes`:

- git has changes outside the expected target file/TC/traceability line;
- staged changes exist;
- or the target diff does not match the expected traceability-line-only shape.

## Final State Valid

`final_state_valid=true` when all content checks pass:

- current traceability line contains required legacy refs;
- current traceability line contains new `REQ-*` refs;
- current traceability line does not contain old `REQ-*` refs;
- no duplicate `REQ-*` refs exist;
- old and new `REQ-*` refs exist in the requirements registries;
- backup exists;
- backup contains the old traceability line;
- backup/current comparison confirms only the expected traceability-line-only replacement.

## Safe To Commit

`safe_to_commit=true` only if all are true:

- `validation_status` is `pass` or `pass-with-warnings`;
- `git_change_state=uncommitted_expected_change`;
- `failed_checks=[]`;
- `blocking_reasons=[]`;
- no staged changes;
- only the expected test-case file has unstaged changes;
- the target diff has exactly one hunk;
- the hunk changes only the expected traceability line in the expected TC;
- backup/current comparison confirms the same expected traceability-line-only change.

If `git_change_state=final_state_already_baselined`, `safe_to_commit=false` and `commit_action=nothing_to_commit`; this is not a failure when `final_state_valid=true`.

`safe_for_next_stage=true` when `final_state_valid=true`, validation is not failed/blocked, and `git_change_state` is either `uncommitted_expected_change` or `final_state_already_baselined`.

Warnings inherited from upstream artifacts or clean-baselined final state may produce `pass-with-warnings`; they do not block `safe_for_next_stage` if all content checks pass.
