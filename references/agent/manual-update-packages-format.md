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

## Blocking Rules

Block package generation when:

- update plan file is missing;
- update plan cannot be parsed;
- update plan summary has `plan_status=blocked`;
- package generation would include no manual items and no candidates;
- duplicate `package_id` is detected;
- the same concrete `test_case_id/file_path/action` appears in conflicting packages.

When blocked, artifacts may still be written for diagnostics, but `packages` must be empty.

## Markdown Report

Markdown output must contain:

- `Summary`
- `Packages by File`
- `New TC Candidates`
- `Deprecated Candidates`
- `Manual Review Packages`
- `Do Not Touch Rules`

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
