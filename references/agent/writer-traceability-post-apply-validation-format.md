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
- `safe_to_commit`
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

## Safe To Commit

`safe_to_commit=true` only if all are true:

- `validation_status` is `pass` or `pass-with-warnings`;
- `failed_checks=[]`;
- `blocking_reasons=[]`;
- no staged changes;
- only the expected test-case file has unstaged changes;
- the target diff has exactly one hunk;
- the hunk changes only the expected traceability line in the expected TC;
- backup/current comparison confirms the same expected traceability-line-only change.

Warnings inherited from upstream artifacts may produce `pass-with-warnings`; they do not block `safe_to_commit` if all safety checks pass.
