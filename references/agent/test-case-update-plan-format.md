# Test Case Update Plan Format

Stage 6A converts an Impact Report into a machine-checkable update plan for test-case maintenance.

It does not edit, create, rewrite, deprecate, or delete test-case files. It is a planning artifact for later manual/writer stages.

## Required Files

For `<old-version>` and `<new-version>`, the builder writes:

- `test-case-update-plan.<old-version>-to-<new-version>.json`
- `test-case-update-plan-summary.<old-version>-to-<new-version>.json`
- `test-case-update-plan.<old-version>-to-<new-version>.md`

Recommended package location:

```text
fts/<ft-slug>/requirements/test-case-update-plan.<old-version>-to-<new-version>.json
fts/<ft-slug>/requirements/test-case-update-plan-summary.<old-version>-to-<new-version>.json
fts/<ft-slug>/requirements/test-case-update-plan.<old-version>-to-<new-version>.md
```

## Update Plan Item

```json
{
  "plan_item_id": "PLAN-000001",
  "impact_id": "IMP-000001",
  "change_id": "CHG-000001",
  "test_case_id": "TC-001",
  "file_path": "fts/AutoFin/test-cases/14-client-addresses.md",
  "action": "traceability_update_only",
  "apply_mode": "safe_auto_candidate",
  "old_refs": ["REQ-AUTOFIN-OLD", "BSR 115"],
  "new_refs": ["REQ-AUTOFIN-NEW", "BSR 116"],
  "required_changes": ["update traceability refs only"],
  "forbidden_changes": [
    "Do not change steps",
    "Do not change expected result",
    "Do not change test data"
  ],
  "rationale": ["impact action=traceability_update_only"],
  "requires_manual_review": false,
  "warnings": []
}
```

Allowed `action` values:

- `keep`
- `update_existing`
- `traceability_update_only`
- `create_new_candidate`
- `mark_deprecated_candidate`
- `manual_review`
- `blocked`

Allowed `apply_mode` values:

- `manual_only`
- `safe_auto_candidate`
- `blocked`

## Plan Shape

```json
{
  "ft_slug": "AutoFin",
  "old_source_version": "autofin-prefinal-v1",
  "new_source_version": "autofin-final-v1",
  "impact_report_path": "fts/AutoFin/requirements/impact-report.autofin-prefinal-v1-to-autofin-final-v1.json",
  "test_cases_dir": "fts/AutoFin/test-cases",
  "created_at_utc": "2026-07-04T00:00:00Z",
  "created_by_tool": "scripts/build_test_case_update_plan.py",
  "plan_items": [],
  "summary": {},
  "warnings": [],
  "blocking_reasons": []
}
```

## Action Mapping

- Impact `no_action` -> plan `keep`.
  - `apply_mode=safe_auto_candidate`.
  - This is a no-op candidate only: it means an executor can safely do nothing.
  - `required_changes=[]`.
  - `forbidden_changes=["Do not rewrite steps", "Do not rewrite expected result"]`.
- Impact `traceability_update_only` -> plan `traceability_update_only`.
  - `apply_mode=safe_auto_candidate` only when linked affected test cases exist, the linked test case has no parse warnings, and the impact entry has `requires_manual_review=false`.
  - Otherwise `apply_mode=manual_only`.
  - `required_changes=["update traceability refs only"]`.
  - `forbidden_changes=["Do not change steps", "Do not change expected result", "Do not change test data"]`.
- Impact `update_existing` -> plan `update_existing`.
  - `apply_mode=manual_only`.
  - `required_changes=["review steps", "review expected result", "update traceability"]`.
  - `requires_manual_review=true`.
- Impact `create_new` -> plan `create_new_candidate`.
  - `test_case_id=null`, `file_path=null`.
  - `apply_mode=manual_only`.
  - Stage 6A must not create the TC.
- Impact `mark_deprecated` -> plan `mark_deprecated_candidate`.
  - `apply_mode=manual_only`.
  - Stage 6A must not edit or deprecate the TC.
- Impact `manual_review` -> plan `manual_review`.
  - `apply_mode=manual_only`.
- Impact `blocked_unlinked` -> plan `blocked`.
  - `apply_mode=blocked`.

## Summary Shape

```json
{
  "plan_status": "pass-with-warnings",
  "impact_entries_total": 5,
  "plan_items_total": 5,
  "actions": {
    "keep": 1,
    "update_existing": 1,
    "traceability_update_only": 1,
    "create_new_candidate": 1,
    "mark_deprecated_candidate": 1,
    "manual_review": 0,
    "blocked": 0
  },
  "apply_modes": {
    "manual_only": 3,
    "safe_auto_candidate": 2,
    "blocked": 0
  },
  "safe_auto_candidates_count": 2,
  "manual_only_count": 3,
  "blocked_items_count": 0,
  "requires_manual_review_count": 3,
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `plan_status` values:

- `pass`: plan built without warnings, manual-review items, or blocked items.
- `pass-with-warnings`: plan built, but warnings, manual-review items, or blocked items are present.
- `blocked`: plan is not actionable because required inputs are missing or invalid.

## Blocking Rules

Block the plan when:

- impact report file is missing;
- impact report cannot be parsed;
- impact report summary has `impact_status=blocked`;
- optional impact summary has `impact_status=blocked`;
- impact report has `blocking_reasons`;
- test-cases directory is missing;
- a linked affected TC file path does not exist;
- duplicate plan items for the same `(test_case_id, file_path, action)` have inconsistent operational instructions.

When the plan is blocked, generated artifacts may still be written for diagnostics, but `plan_items` must be empty and `blocking_reasons` must explain the blocker.

## Markdown Report

Markdown output must contain:

- `Summary`
- `Safe Auto Candidates`
- `Manual Updates Required`
- `New TC Candidates`
- `Deprecated Candidates`
- `Traceability-only Updates`
- `Blocked Items`
- `Do Not Touch`

## CLI

```bash
python scripts/build_test_case_update_plan.py \
  --impact-report fts/AutoFin/requirements/impact-report.autofin-prefinal-v1-to-autofin-final-v1.json \
  --test-cases-dir fts/AutoFin/test-cases \
  --out-dir fts/AutoFin/requirements
```

Optional input:

```bash
--impact-summary fts/AutoFin/requirements/impact-report-summary.autofin-prefinal-v1-to-autofin-final-v1.json
```

## Stage 6A Limits

- Do not edit test-case files.
- Do not create new test-case files.
- Do not deprecate test-case files.
- Do not update writer/reviewer workflow.
- Do not apply the plan.
