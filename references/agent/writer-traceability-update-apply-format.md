# Writer Traceability Update Apply Format

Stage 8B is the controlled executor for a reviewed writer traceability update proposal.

Default mode is dry-run. Canonical test-case files are not edited unless the CLI is run with explicit `--apply`.

## Inputs

- `writer-dry-run-proposal-<package-id>-after-backfill.json`
- `writer-proposal-review-<package-id>-after-backfill.json`
- canonical `test-cases` directory
- output work directory

The executor uses structured proposal data only. It must not apply a patch with `git apply`, `patch`, or any shell patching command.

## Report

`WriterTraceabilityUpdateApplyReport`:

- `package_id`
- `apply_status`: `previewed | applied | skipped | blocked | failed`
- `dry_run`
- `file_path`
- `affected_test_case_ids`
- `applied_changes`
- `previewed_changes`
- `skipped_changes`
- `backup_path`
- `sha256_before`
- `sha256_after`
- `files_changed_count`
- `warnings`
- `blocking_reasons`
- `input_paths`
- `created_at_utc`
- `created_by_tool`

Each change records:

- `plan_item_id`
- `impact_id`
- `change_id`
- `test_case_id`
- `old_ref`
- `new_ref`
- `old_traceability_line`
- `new_traceability_line`
- `status`

## Dry-Run

If `--apply` is absent:

- the executor validates all safety gates;
- canonical test-case files are not modified;
- eligible replacements are reported in `previewed_changes`;
- `files_changed_count` must be `0`;
- no backup is created.

Dry-run may proceed for `approved-with-warnings` reviews without `--ack-warnings`.

## Real Apply

Real apply requires all of:

- explicit `--apply`;
- `review.safe_for_controlled_apply=true`;
- `review_status` is `approved` or `approved-with-warnings`;
- `failed_checks=[]`;
- proposal status is not `blocked`;
- concrete proposal `file_path`;
- current file SHA equals proposal `sha256_before`;
- proposal original TC blocks exactly match current file blocks;
- proposed changes touch only listed TC blocks;
- proposed changes touch only traceability lines;
- target file is inside the configured `test-cases` directory.

If `review_status=approved-with-warnings`, real apply also requires explicit `--ack-warnings`.

Before a real write, create:

`backups/writer-traceability-update-<package-id>-<suffix>/<filename>.bak`

The backup must contain the exact original file content.

## Post-Apply Validation

After a real write, the executor re-reads the file and verifies:

- only the expected structured proposal content was written;
- only listed TC blocks changed;
- only traceability lines changed;
- old `REQ-*` refs were replaced by new `REQ-*` refs;
- legacy refs are preserved;
- no duplicate `REQ-*` refs remain;
- unrelated TC blocks are unchanged.

If post-apply validation fails, the executor restores original content and reports `failed`.

## Blocking Rules

Block the run if:

- package id mismatches;
- proposal or review is missing or unparsable;
- review is unsafe;
- review has failed checks;
- real apply is requested for `approved-with-warnings` without `--ack-warnings`;
- current file does not contain the old `REQ-*` refs in the traceability line;
- current TC blocks differ from proposal `original_tc_blocks`;
- any non-traceability line would change;
- duplicate TC blocks are detected;
- target file is outside the configured `test-cases` directory.
