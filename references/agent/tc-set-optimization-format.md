# TC Set Optimization Review Format

Create `TC Set Optimization Review` after Package Test Design Plan and before final TC sign-off when required by `test-design-depth-policy.md`.

## When Required

- Always for `coverage_depth_profile = deep`.
- For `standard` when TC count >= 15, plan rows >= 20, high-risk dimensions exist, or over-testing risk is marked.
- Not required for small `simple` scope unless over-testing risk exists.

## Format

```md
## TC Set Optimization Review

| optimization_item | status | affected_tc_or_plan_rows | evidence | decision | required_action |
| --- | --- | --- | --- | --- | --- |
| `duplicate-checks` | `pass` | `TC-001`, `TC-002` | Checks differ by independent input class. | `keep` | none_required:pass |
| `excessive-fragmentation` | `fail` | `PD-010`, `PD-011` | Rows test one observable flow without independent oracle. | `merge` | Merge into one scenario TC or justify separate checks. |
```

Columns:

- `optimization_item`: one required item below.
- `status`: `pass | fail | blocked | needs-rewrite`.
- `affected_tc_or_plan_rows`: concrete `TC-*`, `PD-*`, `ATOM-*`, `GAP-*` or `all`.
- `evidence`: source/design evidence, not a generic statement.
- `decision`: one controlled decision below.
- `required_action`: concrete action; for pass use `none_required:pass`.

Required items: `duplicate-checks`, `excessive-fragmentation`, `unsafe-merged-checks`, `low-value-negative-cases`, `missing-core-scenarios`, `regression-candidate-selection`, `deep-coverage-isolation`, `manual-execution-cost`, `risk-vs-effort-balance`.

Controlled decisions: `keep`, `merge`, `split`, `convert-to-deep-coverage`, `convert-to-gap`, `remove-as-duplicate`, `defer-with-accepted-risk`.

Rules: do not remove source-backed coverage to reduce TC count; do not merge independent pass/fail results unless scenario grouping in `package-test-design-plan-format.md` is satisfied; label mandatory, `deep`, `optional`, `regression-candidate`, and `blocked-by-gap` coverage separately; low-value negatives need source/risk evidence or must move to `deep`/`optional`/accepted risk or be removed as duplicate/noise.
