# Writer Dry-Run Proposal Format

Stage 7C creates one preview-only writer proposal from one safe writer package task.

It does not edit canonical test-case files. It does not create new canonical test cases.
It does not run controlled apply. It does not change writer/reviewer workflow.

## Required Files

For package `<package-id>`, the builder writes:

- `writer-dry-run-proposal-<package-id>.json`
- `writer-dry-run-proposal-<package-id>.md`
- `writer-dry-run-proposal-<package-id>.patch`

The `.patch` file is preview-only and must not be applied by Stage 7C.

## Allowed Scope

Stage 7C is intentionally narrow:

- only the explicitly allowed `package_id` may be processed;
- the first AutoFin target is `WPKG-000003`;
- the task must be file-bound;
- `affected_test_case_ids` must be non-empty;
- `large_package` must be `false`;
- `safe_to_try_first` must be `true`;
- unlinked, create-new, and large packages are blocked.

The builder may read task/update-plan/diff/impact artifacts, but it must read only the test-case
file referenced by `task.file_path`. It must extract only the listed TC blocks. Other TC blocks may
only be scanned for boundary and duplicate-heading detection; they must not be included in proposal
content or proposed changes.

## Proposal Shape

```json
{
  "package_id": "WPKG-000003",
  "file_path": "fts/AutoFin/test-cases/section-4.2-applications-menu-search.md",
  "affected_test_case_ids": ["TC-AMSR-012"],
  "source_plan_item_ids": ["PLAN-000194", "PLAN-000195"],
  "source_impact_ids": ["IMP-000192", "IMP-000193"],
  "source_change_ids": ["CHG-000192", "CHG-000193"],
  "proposal_status": "pass-with-warnings",
  "risk_level": "medium",
  "manual_review_required": true,
  "proposed_changes": [],
  "rationale": [],
  "missing_information": [],
  "original_tc_blocks": {
    "TC-AMSR-012": "## TC-AMSR-012\n..."
  },
  "proposed_tc_blocks": {
    "TC-AMSR-012": "## TC-AMSR-012\n..."
  },
  "unified_diff_preview": "",
  "sha256_before": "<sha256>",
  "sha256_after": "<sha256>",
  "input_paths": {},
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `proposal_status` values:

- `pass`
- `pass-with-warnings`
- `blocked`

Allowed `risk_level` values:

- `low`
- `medium`
- `high`

## Proposal Rules

- `proposed_changes` may contain only changes for `affected_test_case_ids`.
- Traceability-only changes are proposed only when the old ref is found inside a listed TC block.
- If the old ref is not found, the builder must not invent an insertion point; it records
  `missing_information` and leaves `proposed_changes` empty for that ref.
- If data is insufficient for an exact change, use `pass-with-warnings` or `blocked` and explain why.
- `original_tc_blocks` and `proposed_tc_blocks` must contain only listed TC IDs.
- `sha256_before` and `sha256_after` must match when Stage 7C completes successfully.

## Blocking Rules

Block proposal generation when:

- package id is not the explicitly allowed id;
- writer task is missing;
- writer task is unlinked;
- writer task is `create_new_candidate`;
- writer task is a large package;
- writer task is not `safe_to_try_first`;
- listed TC block is not found;
- listed TC block is duplicated;
- task file is outside `test_cases_dir`;
- task file is missing or unreadable.

When blocked, artifacts may still be written for diagnostics.

## CLI

```bash
python scripts/build_writer_dry_run_proposal.py \
  --package-id WPKG-000003 \
  --writer-package-task fts/AutoFin/work/e2e-dry-run/<run>/writer-package-task-WPKG-000003.md \
  --writer-package-tasks fts/AutoFin/work/e2e-dry-run/<run>/writer-package-tasks.<old>-to-<new>.json \
  --manual-update-packages fts/AutoFin/work/e2e-dry-run/<run>/manual-update-packages.<old>-to-<new>.json \
  --update-plan fts/AutoFin/work/e2e-dry-run/<run>/test-case-update-plan.<old>-to-<new>.json \
  --impact-report fts/AutoFin/work/e2e-dry-run/<run>/impact-report.<old>-to-<new>.json \
  --requirements-diff fts/AutoFin/work/e2e-dry-run/<run>/requirements-diff.<old>-to-<new>.json \
  --test-cases-dir fts/AutoFin/test-cases \
  --out-dir fts/AutoFin/work/e2e-dry-run/<run>
```

## Stage 7C Limits

- Do not edit canonical test-case files.
- Do not create new test-case files.
- Do not run `--apply`.
- Do not process large or unlinked packages.
- Do not change writer/reviewer workflow.
