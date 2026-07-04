# Test Case Update Apply Format

Stage 6B is a conservative controlled executor for a Stage 6A Test Case Update Plan.

It can apply only safe traceability-only updates. It must not perform semantic test updates, rewrite steps, rewrite expected results, rewrite test data, create new test cases, deprecate test cases, or apply manual-review items.

## Required Files

For `<old-version>` and `<new-version>`, the builder writes:

- `test-case-update-apply.<old-version>-to-<new-version>.json`
- `test-case-update-apply-summary.<old-version>-to-<new-version>.json`
- `test-case-update-apply.<old-version>-to-<new-version>.md`

Recommended package location:

```text
fts/<ft-slug>/requirements/test-case-update-apply.<old-version>-to-<new-version>.json
fts/<ft-slug>/requirements/test-case-update-apply-summary.<old-version>-to-<new-version>.json
fts/<ft-slug>/requirements/test-case-update-apply.<old-version>-to-<new-version>.md
```

## Dry-run First

Default mode is dry-run. The CLI writes report artifacts, but does not modify test-case files unless `--apply` is explicitly passed.

```bash
python scripts/apply_test_case_update_plan.py \
  --update-plan fts/AutoFin/requirements/test-case-update-plan.old-v1-to-new-v1.json \
  --test-cases-dir fts/AutoFin/test-cases \
  --out-dir fts/AutoFin/requirements
```

Actual write mode:

```bash
python scripts/apply_test_case_update_plan.py \
  --update-plan fts/AutoFin/requirements/test-case-update-plan.old-v1-to-new-v1.json \
  --test-cases-dir fts/AutoFin/test-cases \
  --out-dir fts/AutoFin/requirements \
  --apply
```

Optional inputs:

```bash
--update-plan-summary fts/AutoFin/requirements/test-case-update-plan-summary.old-v1-to-new-v1.json
--backup-dir fts/AutoFin/work/update-plan-backups/old-v1-to-new-v1
```

## Backup Policy

Before actual writes, Stage 6B creates backups for every file that will be changed.

Default backup location:

```text
<out-dir>/backups/<relative-test-case-file>.bak
```

If `--backup-dir` is passed, backups are written under that directory instead:

```text
<backup-dir>/<relative-test-case-file>.bak
```

`<relative-test-case-file>` is relative to `--test-cases-dir` when possible. The backup content must be the original file content before any Stage 6B modification.

If backup creation fails in `--apply` mode, the whole apply is blocked and no test-case files are written.

## Apply Result Item

```json
{
  "apply_item_id": "APPLY-000001",
  "plan_item_id": "PLAN-000001",
  "impact_id": "IMP-000001",
  "change_id": "CHG-000001",
  "test_case_id": "TC-001",
  "file_path": "fts/AutoFin/test-cases/14-client-addresses.md",
  "action": "traceability_update_only",
  "apply_mode": "safe_auto_candidate",
  "apply_status": "previewed",
  "before_sha256": "abc...",
  "after_sha256": "def...",
  "backup_path": null,
  "changed_lines": [3],
  "applied_changes": ["replace `BSR 115` -> `BSR 116`"],
  "skipped_reason": null,
  "warnings": []
}
```

Allowed `apply_status` values:

- `previewed`: dry-run found a safe traceability-only patch.
- `applied`: `--apply` wrote a safe traceability-only patch.
- `skipped_noop`: keep/no-op item or already matching traceability refs.
- `skipped_manual_only`: item requires manual handling.
- `skipped_blocked`: item is blocked.
- `skipped_unsafe`: item failed controlled-apply guardrails.
- `failed`: file write failed after backups were created.

## Apply Report

```json
{
  "ft_slug": "AutoFin",
  "old_source_version": "old-v1",
  "new_source_version": "new-v1",
  "update_plan_path": "fts/AutoFin/requirements/test-case-update-plan.old-v1-to-new-v1.json",
  "test_cases_dir": "fts/AutoFin/test-cases",
  "created_at_utc": "2026-07-04T00:00:00Z",
  "created_by_tool": "scripts/apply_test_case_update_plan.py",
  "dry_run": true,
  "apply_items": [],
  "summary": {},
  "warnings": [],
  "blocking_reasons": []
}
```

## Summary Shape

```json
{
  "apply_status": "pass",
  "dry_run": true,
  "plan_items_total": 2,
  "apply_items_total": 2,
  "applied": 0,
  "previewed": 1,
  "skipped_noop": 1,
  "skipped_manual_only": 0,
  "skipped_blocked": 0,
  "skipped_unsafe": 0,
  "failed": 0,
  "files_changed_count": 0,
  "files_changed": [],
  "backups_created": [],
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `apply_status` values:

- `pass`: executor completed without warnings, unsafe skips, blocked skips, failed items, or report blockers.
- `pass-with-warnings`: executor completed, but warnings or unsafe/blocked/failed items are present.
- `blocked`: executor did not proceed because an apply-level blocker was found.

## Controlled Apply Rules

Only `traceability_update_only` items with `apply_mode=safe_auto_candidate` may modify files.

The item must also satisfy all guardrails:

- `test_case_id` exists;
- `file_path` exists;
- item has no warnings;
- `required_changes` is exactly `["update traceability refs only"]`;
- `forbidden_changes` includes:
  - `Do not change steps`
  - `Do not change expected result`
  - `Do not change test data`

All other items are skipped:

- `keep` -> `skipped_noop`;
- `manual_only` -> `skipped_manual_only`;
- `blocked` -> `skipped_blocked`;
- unexpected safe-auto items -> `skipped_unsafe`.

## Traceability Patching Rules

The executor:

- locates the TC block by `## TC-*` or legacy `### TC-*`;
- requires exactly one matching TC block in the file;
- locates exactly one traceability line in that block;
- replaces only old refs from `plan_item.old_refs` with corresponding refs from `plan_item.new_refs`;
- uses boundary-aware replacement, so `BSR 1` does not rewrite `BSR 115`;
- refuses to append refs when no old refs are found;
- writes no line outside the traceability field.

Supported traceability labels:

- `**Трассировка:**`
- mojibake-compatible `**РўСЂР°СЃСЃРёСЂРѕРІРєР°:**`
- `**Traceability:**`

The executor must not alter semantic sections such as:

- `### Шаги`
- `### Итоговый ожидаемый результат`
- `### Тестовые данные`

## Blocking Rules

Block the entire apply when:

- update plan file is missing;
- update plan cannot be parsed;
- update plan summary has `plan_status=blocked`;
- test-cases directory is missing;
- duplicate safe traceability updates target the same `(test_case_id, file_path)` with conflicting `new_refs`;
- `--apply` is used but backup creation fails.

## Markdown Report

Markdown output must contain:

- `Summary`
- `Previewed / Applied Changes`
- `Skipped No-op`
- `Skipped Manual-only`
- `Skipped Unsafe`
- `Failed Items`
- `Files Changed`
- `Backups`

## Stage 6B Limits

- Do not update steps.
- Do not update expected result.
- Do not update test data.
- Do not create new TC.
- Do not deprecate TC.
- Do not apply manual-only items.
- Do not change writer/reviewer workflow.
