# Impact Analysis Format

Impact Analysis maps a Requirements Diff to existing Markdown test cases and produces machine-checkable impact artifacts.

It does not update, rewrite, deprecate, or create test-case files. It is not final QA sign-off.

## Required Files

For `<old-version>` and `<new-version>`, the builder writes:

- `impact-report.<old-version>-to-<new-version>.json`
- `impact-report-summary.<old-version>-to-<new-version>.json`
- `impact-report.<old-version>-to-<new-version>.md`

Recommended package location:

```text
fts/<ft-slug>/requirements/impact-report.<old-version>-to-<new-version>.json
fts/<ft-slug>/requirements/impact-report-summary.<old-version>-to-<new-version>.json
fts/<ft-slug>/requirements/impact-report.<old-version>-to-<new-version>.md
```

## Test Case Link

```json
{
  "test_case_id": "TC-001",
  "file_path": "fts/AutoFin/test-cases/14-client-addresses.md",
  "title": "Проверка обязательности адреса",
  "linked_req_uids": ["REQ-AUTOFIN-ABC123"],
  "linked_atom_ids": ["ATOM-000001"],
  "linked_source_req_ids": ["BSR 115"],
  "raw_traceability": "REQ-AUTOFIN-ABC123; ATOM-000001; BSR 115",
  "parse_warnings": []
}
```

Parser rules:

- Read only Markdown files from `fts/<ft-slug>/test-cases/*.md`.
- Canonical TC heading is `## TC-*`.
- Legacy `### TC-*` is accepted with warning: `legacy TC heading level detected`.
- Title is read from `**Название:**`.
- Traceability is read from `**Трассировка:**`.
- Extract linked IDs:
  - `REQ-[A-Z0-9-]+`
  - `ATOM-[A-Z0-9-]+`
  - `BSR <number>`, `GSR <number>`, `REQ[- ]?<number>`, `ID <number>`
- Missing traceability adds warning and must not silently make a TC unaffected.

## Impact Entry

```json
{
  "impact_id": "IMP-000001",
  "change_id": "CHG-000001",
  "change_type": "behavior_modified",
  "old_req_uid": "REQ-AUTOFIN-OLD",
  "new_req_uid": "REQ-AUTOFIN-NEW",
  "old_source_req_id": "BSR 115",
  "new_source_req_id": "BSR 115",
  "affected_test_cases": [],
  "action": "create_new",
  "priority": "high",
  "rationale": ["change_type=behavior_modified", "no linked test case found"],
  "requires_manual_review": true,
  "warnings": [
    "behavior_modified change has no linked test cases; create new coverage candidate."
  ]
}
```

Allowed `action` values:

- `no_action`
- `update_existing`
- `create_new`
- `mark_deprecated`
- `manual_review`
- `traceability_update_only`
- `blocked_unlinked`

Allowed `priority` values:

- `high`
- `medium`
- `low`

## Impact Rules

- `unchanged` -> `no_action`.
- `text_changed_no_behavior_change` -> `traceability_update_only`.
- `source_anchor_changed` -> `traceability_update_only`.
- `renumbered` -> `traceability_update_only`, priority `medium`.
- `behavior_modified` with linked TC -> `update_existing`, priority `high`, manual review.
- `behavior_modified` without linked TC -> `create_new`, priority `high`, manual review. This Stage 5 policy avoids blocking the whole report but makes missing traceability explicit.
- `added` -> `create_new`; if already linked, `manual_review`.
- `deleted` with linked TC -> `mark_deprecated`, manual review.
- `deleted` without linked TC -> `no_action` with warning.
- `split` / `merged` -> `manual_review`, priority `high`.
- `unclear_match` -> `manual_review`, priority `medium`.
- If diff entry has `requires_manual_review=true`, the impact entry must also have `requires_manual_review=true`.

Linking uses any of:

- old/new `req_uid`
- old/new `atom_id`
- old/new `source_req_id`

If multiple TC match, include all matching TC links.

## Report Shape

```json
{
  "ft_slug": "AutoFin",
  "old_source_version": "autofin-prefinal-v1",
  "new_source_version": "autofin-final-v1",
  "requirements_diff_path": "fts/AutoFin/requirements/requirements-diff.autofin-prefinal-v1-to-autofin-final-v1.json",
  "test_cases_dir": "fts/AutoFin/test-cases",
  "created_at_utc": "2026-07-04T00:00:00Z",
  "created_by_tool": "scripts/build_impact_report.py",
  "impact_entries": [],
  "summary": {},
  "warnings": [],
  "blocking_reasons": []
}
```

## Summary Shape

```json
{
  "impact_status": "pass-with-warnings",
  "diff_entries_total": 5,
  "impact_entries_total": 5,
  "test_cases_scanned": 12,
  "test_case_files_scanned": 3,
  "affected_test_cases_count": 4,
  "actions": {
    "no_action": 1,
    "update_existing": 1,
    "create_new": 1,
    "mark_deprecated": 1,
    "manual_review": 1,
    "traceability_update_only": 0,
    "blocked_unlinked": 0
  },
  "requires_manual_review_count": 3,
  "unlinked_change_count": 1,
  "parse_warnings_count": 0,
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `impact_status` values:

- `pass`: report was built without warnings or manual-review flags.
- `pass-with-warnings`: report was built, but warnings or manual-review flags are present.
- `blocked`: report is not actionable because required inputs are missing or invalid.

## Blocking Rules

Block when:

- requirements diff file is missing;
- diff summary has `diff_status=blocked`;
- test-cases directory is missing;
- test-case parser cannot read files;
- duplicate TC IDs are detected;
- no test cases are parsed, unless `--allow-empty-test-cases` is passed.

## Markdown Report

Markdown output must contain:

- `Summary`
- `Actions by Type`
- `Affected Test Cases`
- `Requirements Needing New TC`
- `Deprecated Candidates`
- `Manual Review Required`
- `Unlinked Changes`
- `Parser Warnings`

## CLI

```bash
python scripts/build_impact_report.py \
  --requirements-diff fts/AutoFin/requirements/requirements-diff.autofin-prefinal-v1-to-autofin-final-v1.json \
  --test-cases-dir fts/AutoFin/test-cases \
  --out-dir fts/AutoFin/requirements
```

Optional inputs:

```bash
--requirements-diff-summary fts/AutoFin/requirements/requirements-diff-summary.autofin-prefinal-v1-to-autofin-final-v1.json
--allow-empty-test-cases
```

## Stage 5 Limits

- Do not edit test-case files.
- Do not create new test-case files.
- Do not update writer/reviewer workflow.
- Do not treat the report as final QA sign-off.
