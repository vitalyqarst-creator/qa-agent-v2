# Traceability Backfill Apply Format

Stage 7H is the first traceability backfill stage that can write canonical test-case files. Default mode is dry-run. A real write is allowed only with explicit `--apply`; if the review status is `approved-with-warnings`, real write also requires `--ack-warnings`.

## Workflow Position / Safety Link

This format is part of `references/agent/controlled-traceability-update-workflow.md`, stage 5. Real apply must follow `references/agent/controlled-traceability-update-checklist.md` and must use structured proposal data, not patch application.

## Inputs

- `traceability-backfill-proposal-<package-id>.json`
- `traceability-backfill-review-<package-id>.json`
- `fts/<ft-slug>/test-cases`

Stage 7H applies from structured proposal data, not from patch text.

## Outputs

- `traceability-backfill-apply-<package-id>.json`
- `traceability-backfill-apply-<package-id>.md`

For real apply only, a backup is created before writing:

```text
backups/traceability-backfill-<package-id>/<filename>.bak
```

## Apply Report Fields

- `package_id`
- `apply_status`: `previewed`, `applied`, `skipped`, `blocked`, or `failed`
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
- `input_paths`
- `created_at_utc`
- `created_by_tool`
- `warnings`
- `blocking_reasons`

## Controlled Apply Rules

- Dry-run is the default and must not edit canonical files.
- Real apply requires `--apply`.
- `approved-with-warnings` requires `--ack-warnings` for real apply.
- Review must have `safe_for_controlled_apply=true`.
- Review status must be `approved` or `approved-with-warnings`.
- Review `failed_checks` must be empty.
- Proposal status must not be `blocked`.
- Proposal file path must be concrete and inside the test-cases directory.
- Current file SHA must match `proposal.sha256_before`.
- Current listed TC blocks must match `proposal.original_tc_blocks` exactly.
- Proposed content may replace only listed TC blocks.
- Within listed TC blocks, only traceability lines may differ.
- Legacy refs must be preserved.
- Added `REQ-*` refs must be present after apply and must not be duplicated.
- No unrelated TC block may change.

## Write Method

The executor must not use `git apply`, `patch`, or shell-based patching. It must:

1. Read the target file.
2. Rebuild proposed file content from structured `proposed_tc_blocks`.
3. Re-run all safety checks.
4. In dry-run, write only the apply report.
5. In real apply, write a backup, write the proposed content, then re-read and validate.

If post-apply validation fails, the executor must restore the original content when possible and report `apply_status=failed`.

## CLI

Dry-run:

```bash
python scripts/apply_traceability_backfill_proposal.py \
  --package-id WPKG-000003 \
  --backfill-proposal fts/AutoFin/work/.../traceability-backfill-proposal-WPKG-000003.json \
  --backfill-review fts/AutoFin/work/.../traceability-backfill-review-WPKG-000003.json \
  --test-cases-dir fts/AutoFin/test-cases \
  --out-dir fts/AutoFin/work/...
```

Real apply:

```bash
python scripts/apply_traceability_backfill_proposal.py ... --apply --ack-warnings
```

Do not run real apply unless explicitly requested.
