# TC Set Optimization Review Format

`TC Set Optimization Review` - artifact or section created after `Package Test Design Plan` and before final canonical TC sign-off when required by `test-design-depth-policy.md`.

## Purpose

Проверить, что TC set одновременно не недопокрывает ФТ и не раздут лишними/дублирующими проверками. Optimization не удаляет source-backed obligations; спорные source-backed checks переводятся в `GAP-*`, accepted risk или `deep` classification.

## When Required

- Always for `coverage_depth_profile = deep`.
- For `standard` when TC count >= 15, plan rows >= 20, high-risk dimensions exist, or writer/reviewer marks over-testing risk.
- Not required for small `simple` scope unless explicit over-testing risk exists.

## Minimum Format

```md
## TC Set Optimization Review

| optimization_item | status | affected_tc_or_plan_rows | evidence | decision | required_action |
| --- | --- | --- | --- | --- | --- |
| `duplicate-checks` | `pass` | `TC-001`, `TC-002` | Проверки различаются по independent input class. | `keep` | none_required:pass |
| `excessive-fragmentation` | `fail` | `PD-010`, `PD-011` | Две строки проверяют один observable flow без независимого oracle. | `merge` | Объединить в один scenario TC или обосновать раздельность. |
```

## Columns

- `optimization_item`: one canonical item from the required list.
- `status`: `pass | fail | blocked | needs-rewrite`.
- `affected_tc_or_plan_rows`: concrete `TC-*`, `PD-*`, `ATOM-*`, `GAP-*` or `all`.
- `evidence`: source/design evidence, not a generic statement.
- `decision`: controlled decision from this format.
- `required_action`: concrete action; for pass use `none_required:pass`.

## Required Optimization Items

- `duplicate-checks`
- `excessive-fragmentation`
- `unsafe-merged-checks`
- `low-value-negative-cases`
- `missing-core-scenarios`
- `regression-candidate-selection`
- `deep-coverage-isolation`
- `manual-execution-cost`
- `risk-vs-effort-balance`

## Controlled Decisions

- `keep`
- `merge`
- `split`
- `convert-to-deep-coverage`
- `convert-to-gap`
- `remove-as-duplicate`
- `defer-with-accepted-risk`

## Rules

- Do not remove a required source-backed class only to reduce TC count.
- Do not merge independent pass/fail results into one TC unless the scenario grouping rule in `package-test-design-plan-format.md` is satisfied.
- Mark mandatory coverage separately from `deep`, `optional`, `regression-candidate`, and `blocked-by-gap`.
- Low-value negatives must be source-backed, risk-backed, or moved to `deep`/`optional`/accepted risk; otherwise remove as duplicate/noise.
- Manual execution cost is a design signal, not a reason to under-cover high-risk requirements.

## Reviewer Gate

Reviewer treats missing required optimization as a `tc-set-optimization` finding for `deep` and large/high-risk `standard` scopes. Failed optimization rows block sign-off unless converted to a traceable `GAP-*` or accepted risk.
