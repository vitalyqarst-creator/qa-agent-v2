# Terminal Validator Waiver Quality Regression

## Purpose

This regression locks the lesson from `fts/ft-2-OF_16` canary v6:
terminal `signed-off` must not pass merely because every current-scope validator
warning has a table row. The waiver itself must explain a valid non-blocking
class with concrete evidence.

## Failure Signal

- Cycle: `ui-employment-canary-v6-terminal-gate-regression`.
- Bad terminal state: `stage_status: signed-off`.
- Runner validation reported `scoped_findings_count = 22`,
  `waived_count = 21`, and `blocking_unwaived_count = 0`.
- Reviewer used broad process rationales such as pre-existing/no regression,
  format-only changes, and unchanged hashes instead of proving that the
  validator finding was false positive, schema lag, source-gap backed, or an
  accepted non-blocking product risk.

## Must Catch

Runner validation must reject `signed-off` when a matching waiver row is present
but any of these are true:

- `waiver_class` is missing or unsupported;
- `rationale` or `evidence` is a placeholder;
- `waiver_class = accepted-source-gap` does not cite an existing `GAP-*`;
- `waiver_class = accepted-nonblocking-risk` relies on pre-existing,
  no-regression, format-only, unchanged, or hash-unchanged reasoning as the
  standalone justification.

Expected runner error shape:

```text
terminal signed-off has invalid current-scope validator waivers
```

## Structured Waiver

Allowed `waiver_class` values:

- `false-positive`
- `validator-schema-lag`
- `accepted-source-gap`
- `accepted-nonblocking-risk`

Required table:

```md
## Validator Warning Waivers

| finding_id | path | waiver_status | waiver_class | rationale | evidence |
| --- | --- | --- | --- | --- | --- |
| `validator-id` | `test-cases/example.md` | `waived` | `validator-schema-lag` | `<specific rationale>` | `<specific evidence>` |
```

## Pass Criteria

- A waiver without `waiver_class` blocks terminal `signed-off`.
- A process-only pre-existing/no-regression waiver blocks terminal `signed-off`.
- An `accepted-source-gap` waiver without an existing `GAP-*` blocks terminal
  `signed-off`.
- Gate output reports `invalid_waivers_count` and `waived_by_class`.
