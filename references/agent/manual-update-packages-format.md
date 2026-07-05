# Manual Update Packages Format

Stage 7A converts a Test Case Update Plan into machine-checkable manual update work packages for a future writer/reviewer stage.

It does not edit, create, deprecate, rewrite, or delete test-case files. It does not apply updates.

## Required Files

For `<old-version>` and `<new-version>`, the builder writes:

- `manual-update-packages.<old-version>-to-<new-version>.json`
- `manual-update-packages-summary.<old-version>-to-<new-version>.json`
- `manual-update-packages.<old-version>-to-<new-version>.md`

## Package Shape

```json
{
  "package_id": "WPKG-000001",
  "package_type": "update_existing",
  "file_path": "fts/AutoFin/test-cases/14-client-addresses.md",
  "test_case_ids": ["TC-001", "TC-002"],
  "plan_item_ids": ["PLAN-000001", "PLAN-000002"],
  "impact_ids": ["IMP-000001"],
  "change_ids": ["CHG-000001"],
  "actions": ["update_existing"],
  "plan_items_count": 2,
  "priority": "high",
  "requires_manual_review": true,
  "writer_allowed_operations": [
    "update listed TC only",
    "review steps",
    "review expected result",
    "update traceability"
  ],
  "writer_forbidden_operations": [
    "Do not touch unlisted TC",
    "Do not rewrite entire file",
    "Do not reorder unrelated TC",
    "Do not change unrelated traceability",
    "Do not delete TC silently"
  ],
  "rationale": [],
  "warnings": []
}
```

Allowed `package_type` values:

- `update_existing`
- `create_new_candidate`
- `mark_deprecated_candidate`
- `manual_review`
- `mixed`

Allowed `priority` values:

- `high`
- `medium`
- `low`

## Grouping Rules

Stage 7A includes only manual work:

- include `manual_only` plan items except `keep`;
- exclude `keep`, no-op, and `safe_auto_candidate` items.

Grouping:

- concrete `file_path`: one package per file path;
- `create_new_candidate` with `file_path=null`: one candidate package;
- `mark_deprecated_candidate`: group by file path when linked to an existing TC;
- `manual_review`: group by file path when possible, otherwise into an unlinked manual-review package;
- if one file has multiple action types, `package_type=mixed`.

Registry, diff, impact, update-plan, and test-case files must not be modified by Stage 7A.

`packages_total` is the number of work packages, not the number of changes or plan items.
One package may contain many plan items when they target the same file or candidate bucket.
Package type counters such as `update_existing_count` count packages by package type.
`package_action_item_counts` counts eligible manual plan items by action.

## Writer Guardrails

All packages must include these forbidden operations:

- `Do not touch unlisted TC`
- `Do not rewrite entire file`
- `Do not reorder unrelated TC`
- `Do not change unrelated traceability`
- `Do not delete TC silently`

Action-specific allowed operations:

- `update_existing`: update listed TC only; review steps; review expected result; update traceability.
- `create_new_candidate`: propose new TC drafts; do not write into canonical test-case files yet.
- `mark_deprecated_candidate`: propose deprecated marking; do not edit files yet.
- `manual_review`: analyze ambiguity; do not apply automatic changes.
- `traceability_update_only` manual-only: update listed TC only; review traceability only; update traceability.

## Summary Shape

```json
{
  "package_status": "pass-with-warnings",
  "packages_total": 3,
  "files_affected_count": 2,
  "test_cases_affected_count": 4,
  "manual_plan_items_total": 7,
  "packaged_plan_items_total": 7,
  "unpackaged_plan_items_total": 0,
  "package_plan_item_counts": {
    "WPKG-000001": 4,
    "WPKG-000002": 2,
    "WPKG-000003": 1
  },
  "largest_package_plan_items_count": 4,
  "largest_package_ids": ["WPKG-000001"],
  "package_action_item_counts": {
    "update_existing": 4,
    "create_new_candidate": 1,
    "mark_deprecated_candidate": 0,
    "manual_review": 2,
    "traceability_update_only": 0
  },
  "create_new_candidate_count": 1,
  "mark_deprecated_candidate_count": 0,
  "update_existing_count": 1,
  "manual_review_count": 1,
  "mixed_package_count": 0,
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `package_status` values:

- `pass`
- `pass-with-warnings`
- `blocked`

Plan item coverage fields:

- `manual_plan_items_total`: manual-only non-`keep` plan items that must be represented by work packages.
- `packaged_plan_items_total`: sum of `plan_items_count` across all packages.
- `unpackaged_plan_items_total`: `manual_plan_items_total - packaged_plan_items_total`.
- `package_plan_item_counts`: per-package plan item counts.
- `largest_package_plan_items_count`: largest package size by plan items.
- `largest_package_ids`: package ids that have the largest package size.
- `package_action_item_counts`: manual plan items counted by action, not packages counted by type.

## Blocking Rules

Block package generation when:

- update plan file is missing;
- update plan cannot be parsed;
- update plan summary has `plan_status=blocked`;
- package generation would include no manual items and no candidates;
- any manual-only non-`keep` plan item is not assigned to a work package;
- duplicate `package_id` is detected;
- the same concrete `test_case_id/file_path/action` appears in conflicting packages.

When blocked, artifacts may still be written for diagnostics, but `packages` must be empty.
Unpackaged manual plan items are treated as `blocked` rather than `pass-with-warnings`,
because Stage 7A must not hide writer workload before the writer/update stage.

## Markdown Report

Markdown output must contain:

- `Summary`
- `Packages by File`
- `New TC Candidates`
- `Deprecated Candidates`
- `Manual Review Packages`
- `Do Not Touch Rules`

The summary must show manual, packaged, and unpackaged plan item totals and largest package
size. Package rows must show `plan_items_count`, TC count, and actions.

## CLI

```bash
python scripts/build_manual_update_packages.py \
  --update-plan fts/AutoFin/work/e2e-dry-run/<run>/test-case-update-plan.<old>-to-<new>.json \
  --out-dir fts/AutoFin/work/e2e-dry-run/<run>
```

## Stage 7A Limits

- Do not edit test-case files.
- Do not create new test-case files.
- Do not mark test cases deprecated in files.
- Do not run `--apply`.
- Do not change writer/reviewer workflow.
