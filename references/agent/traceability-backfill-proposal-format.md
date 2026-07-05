# Traceability Backfill Proposal Format

Stage 7F creates preview-only proposals for adding missing generated `REQ-*` refs to existing test-case traceability lines. It must not edit canonical test-case files, apply patches, run `--apply`, create new test cases, change writer/reviewer workflow, or perform silent `source_req_id` fallback.

## Inputs

- `traceability-repair-strategy.<old>-to-<new>.json`
- `traceability-mismatch-diagnostics.<old>-to-<new>.json`
- one or more `writer-dry-run-proposal-<package-id>.json`
- `fts/<ft-slug>/test-cases`

## Outputs

For each package:

- `traceability-backfill-proposal-<package-id>.json`
- `traceability-backfill-proposal-<package-id>.md`
- `traceability-backfill-proposal-<package-id>.patch`

Patch files are preview-only artifacts and must not be applied by Stage 7F.

## Proposal Fields

- `package_id`
- `proposal_status`: `pass`, `pass-with-warnings`, or `blocked`
- `file_path`
- `affected_test_case_ids`
- `repair_item_ids`
- `backfill_changes`
- `original_tc_blocks`
- `proposed_tc_blocks`
- `unified_diff_preview`
- `sha256_before`
- `sha256_after`
- `manual_review_required`: always `true`
- `risk_level`: `low`, `medium`, or `high`
- `input_paths`
- `created_at_utc`
- `created_by_tool`
- `warnings`
- `blocking_reasons`

`sha256_before` and `sha256_after` are hashes of the canonical test-case file. They must match because Stage 7F does not write canonical files.

## Backfill Change Fields

- `repair_item_id`
- `test_case_id`
- `added_req_uids`
- `supporting_source_req_ids`
- `old_traceability_line`
- `new_traceability_line`
- `status`: `proposed`, `skipped`, or `blocked`
- `rationale`

## Eligibility Rules

Stage 7F may use only repair items where:

- `package_id` matches the requested package;
- `allowed_next_action = create_backfill_proposal`;
- `confidence` is `high` or `medium`;
- `requires_manual_validation = true`;
- `candidate_req_uids_to_backfill` is not empty;
- `file_path` and `test_case_id` are concrete.

The package proposal is file-bound. If eligible items for one package target multiple files, the proposal must be blocked.

## Backfill Rules

- Read only the target test-case file.
- Extract and propose edits only for listed TC blocks.
- Find exactly one traceability line inside each listed TC block.
- Do not modify steps, expected results, test data, headings, or unrelated TC blocks.
- Do not remove legacy refs.
- Do not duplicate existing `REQ-*` refs.
- Do not insert `REQ-*` refs if the traceability line has no recognizable existing refs.
- Append missing refs at the end of the existing traceability line:

```text
; REQ: <REQ-1>, <REQ-2>
```

## Safety

- Canonical test-case files are not modified.
- Preview patches are written only to the work directory.
- `--apply` is not used.
- Manual validation is required before any future write stage.
