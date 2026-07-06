# Controlled Traceability Update Checklist

Use this checklist with `controlled-traceability-update-workflow.md`.

## Before Proposal

- Confirm the package is file-bound and not large.
- Confirm the target TC IDs are listed explicitly.
- If old generated `REQ-*` refs are missing, run mismatch diagnostics and repair strategy first.
- Do not edit canonical test-cases.

## Before Review

- Confirm proposal artifacts are preview-only.
- Confirm patch files were not applied.
- Confirm proposed changes are limited to listed TC traceability lines.
- Confirm legacy refs are preserved in proposed blocks.

## Before Dry-Run

- Confirm review status is `approved` or `approved-with-warnings`.
- Confirm `safe_for_controlled_apply=true`.
- Run dry-run without `--apply`.
- Do not use `--ack-warnings` unless the stage explicitly needs it for real apply.

## Before Real Apply

- Real apply must be explicitly requested.
- Use `--apply`.
- If review is `approved-with-warnings`, also use `--ack-warnings`.
- Use structured proposal data only.
- Do not use `git apply`, `patch`, shell text replacement, or manual edits.
- Confirm backup path will be under the work directory.

## After Apply

- Check `apply_status=applied`.
- Check `files_changed_count=1` for a single-file package.
- Confirm backup exists.
- Confirm only traceability lines in listed TC blocks changed.
- Confirm old refs are gone, new refs are present, legacy refs are preserved, and duplicate `REQ-*` refs are absent.

## Before Completed-Package Regression

- Confirm each completed package has post-apply validation.
- Confirm `final_state_valid=true`.
- Confirm `safe_for_next_stage=true`.
- Confirm dirty test-case files are only expected package files or the tree is clean.

## When Git Is Clean But Final State Is Valid

- Treat this as `final_state_already_baselined`.
- Do not fail solely because `git diff` is empty.
- Expect `safe_to_commit=false` and `commit_action=nothing_to_commit`.
- Continue only when `safe_for_next_stage=true`.

## When Unrelated Dirty Files Exist

- Stop completed-package regression.
- Triage the unrelated file separately.
- Do not auto-revert, stash, add, or commit.
- Resume regression only after the user explicitly isolates or resolves the unrelated change.
