# Traceability Mismatch Diagnostics Format

Stage 7D explains why writer dry-run proposals could not find update-plan `old_refs` in current TC traceability lines.

It does not edit canonical test-case files. It does not apply patches. It does not run controlled apply.
It does not create test cases, change writer/reviewer workflow, or change impact/update-plan logic.

## Required Files

For `<old-version>` and `<new-version>`, the builder writes:

- `traceability-mismatch-diagnostics.<old-version>-to-<new-version>.json`
- `traceability-mismatch-diagnostics.<old-version>-to-<new-version>.md`

## Inputs

The diagnostic builder reads:

- one or more `writer-dry-run-proposal-<package_id>.json` files;
- `writer-package-tasks.<old>-to-<new>.json`;
- `manual-update-packages.<old>-to-<new>.json`;
- `test-case-update-plan.<old>-to-<new>.json`;
- `impact-report.<old>-to-<new>.json`;
- `requirements-diff.<old>-to-<new>.json`;
- the canonical `test-cases` directory.

For canonical test cases, the builder reads only the file paths referenced by analyzed file-bound proposals.

## Mismatch Shape

```json
{
  "package_id": "WPKG-000003",
  "test_case_id": "TC-AMSR-012",
  "file_path": "fts/AutoFin/test-cases/section-4.2-applications-menu-search.md",
  "plan_item_id": "PLAN-000194",
  "impact_id": "IMP-000192",
  "change_id": "CHG-000192",
  "action": "traceability_update_only",
  "old_refs": ["REQ-AUTOFIN-03B83DF07255", "BSR 28"],
  "new_refs": ["REQ-AUTOFIN-FC1ED982E572", "BSR 28"],
  "current_traceability_line": "**Трассировка:** ATOM-020; BSR 28; BSR 29",
  "parsed_refs_from_traceability_line": ["ATOM-020", "BSR 28", "BSR 29"],
  "missing_old_refs": ["REQ-AUTOFIN-03B83DF07255"],
  "refs_present_in_tc_but_not_in_plan": ["ATOM-020", "BSR 29"],
  "old_source_req_id": "BSR 28",
  "new_source_req_id": "BSR 28",
  "old_req_uid": "REQ-AUTOFIN-03B83DF07255",
  "new_req_uid": "REQ-AUTOFIN-FC1ED982E572",
  "impact_change_type": "source_anchor_changed",
  "diff_change_type": "source_anchor_changed",
  "mismatch_type": "req_uid_generated_after_tc_creation",
  "notes": []
}
```

Allowed `mismatch_type` values:

- `old_req_uid_not_present_in_tc`
- `source_req_id_not_present_in_tc`
- `tc_has_legacy_refs_only`
- `tc_has_no_traceability_refs`
- `impact_linked_by_tc_but_refs_absent`
- `req_uid_generated_after_tc_creation`
- `unknown`

## Classification Rules

- If `old_refs` contain generated `REQ-*` and TC traceability contains only legacy refs such as `BSR`, `GSR`, `ATOM`, `SRC`, `GAP`, or `DICT`, classify as `tc_has_legacy_refs_only` or `req_uid_generated_after_tc_creation`.
- If `old_source_req_id` exists but is absent from current TC traceability, classify as `source_req_id_not_present_in_tc`.
- If a traceability line exists but contains no recognizable refs, classify as `tc_has_no_traceability_refs`.
- If TC traceability contains refs but no old ref matches, classify as `impact_linked_by_tc_but_refs_absent` unless a more specific rule applies.
- Generated `REQ-*` absence with matching legacy source id usually means the req_uid was generated after the TC was authored.

## Summary Shape

```json
{
  "diagnostic_status": "pass-with-warnings",
  "mismatches_total": 6,
  "packages_analyzed": ["WPKG-000002", "WPKG-000003"],
  "test_cases_analyzed": ["TC-ACCEI-012", "TC-ACCEI-013", "TC-AMSR-012"],
  "mismatch_type_counts": {
    "req_uid_generated_after_tc_creation": 6
  },
  "old_ref_type_counts": {
    "bsr": 6,
    "req_uid": 6
  },
  "tc_ref_type_counts": {
    "atom": 6,
    "bsr": 18,
    "src": 10
  },
  "recommendations": [],
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `diagnostic_status` values:

- `pass`
- `pass-with-warnings`
- `blocked`

## Recommendations

Recommendations must answer:

- whether automatic traceability replacement is safe;
- whether existing TC traceability should be backfilled with generated `req_uid`;
- whether update plan should use source ids as a fallback for legacy TC traceability;
- whether impact linking needs more explainability;
- the next safe step.

## CLI

```bash
python scripts/inspect_traceability_mismatches.py \
  --proposal fts/AutoFin/work/e2e-dry-run/<run>/writer-dry-run-proposal-WPKG-000002.json \
  --proposal fts/AutoFin/work/e2e-dry-run/<run>/writer-dry-run-proposal-WPKG-000003.json \
  --writer-package-tasks fts/AutoFin/work/e2e-dry-run/<run>/writer-package-tasks.<old>-to-<new>.json \
  --manual-update-packages fts/AutoFin/work/e2e-dry-run/<run>/manual-update-packages.<old>-to-<new>.json \
  --update-plan fts/AutoFin/work/e2e-dry-run/<run>/test-case-update-plan.<old>-to-<new>.json \
  --impact-report fts/AutoFin/work/e2e-dry-run/<run>/impact-report.<old>-to-<new>.json \
  --requirements-diff fts/AutoFin/work/e2e-dry-run/<run>/requirements-diff.<old>-to-<new>.json \
  --test-cases-dir fts/AutoFin/test-cases \
  --out-dir fts/AutoFin/work/e2e-dry-run/<run>
```

## Stage 7D Limits

- Do not edit canonical test-case files.
- Do not create new test-case files.
- Do not apply patches.
- Do not run `--apply`.
- Do not change writer/reviewer workflow.
- Do not change impact/update-plan logic.
