# Terminal Scoped Validator Gate Regression

## Purpose

This regression locks the lesson from `fts/ft-2-OF_16` canary v5:
a review cycle must not treat terminal `signed-off` as passed while current-scope
validator `warning` or `error` findings remain unclosed.

The gate is intentionally scoped. It must block active artifacts for the current
cycle, but it must not fail because of historical snapshots, scratch write
directories, or unrelated legacy scopes in the same FT package.

## Failure Signal

- Cycle: `ui-employment-canary-v5-expanded-regression`.
- Bad terminal state: `stage_status: signed-off`.
- Independent current-scope validator filter still reported warnings for:
  - canonical test-case file;
  - current split test-design artifacts;
  - current review-cycle outputs.
- Reviewer claimed `validator_checked: yes`, but did not enumerate and waive
  every current-scope warning with evidence.

## Must Catch

Runner validation must reject `signed-off` when all of these are true:

- `cycle-state.yaml` has `stage_status: signed-off`;
- `validate_agent_artifacts.py --root <ft-package> --json` reports at least one
  `severity = warning` or `severity = error`;
- the finding path belongs to the current canonical TC, current
  `work/test-design/<scope>/`, or current `work/review-cycles/<scope>/outputs/`;
- no structured waiver row exists in current cycle outputs.

Expected runner error shape:

```text
terminal signed-off has unwaived current-scope validator findings
```

## Structured Waiver

A finding may be treated as non-blocking only when a current cycle output
contains this heading and a matching table row:

```md
## Validator Warning Waivers

| finding_id | path | waiver_status | waiver_class | rationale | evidence |
| --- | --- | --- | --- | --- | --- |
| `test-case-requiredness-without-empty-or-marker-check` | `test-cases/example.md` | `false-positive` | `false-positive` | `<specific reviewer rationale>` | `<specific evidence>` |
```

Allowed `waiver_status` values:

- `false-positive`
- `accepted-nonblocking`
- `waived`

`rationale` and `evidence` must be concrete; placeholders such as `-`, `N/A`,
`none`, `todo`, and `<...>` are not acceptable.

`waiver_class` is mandatory. Allowed values are `false-positive`,
`validator-schema-lag`, `accepted-source-gap`, and `accepted-nonblocking-risk`.

## Scope Filter

The terminal gate must include:

- exact `canonical_test_cases`;
- files under `test_design_dir`;
- files under `work/review-cycles/<scope>/outputs/`.

The terminal gate must exclude:

- any path under `versions/`;
- any path under `_artifact_write/`;
- paths for unrelated scope slugs.

The same filter applies to runner-generated scoped validator profiles and
writer-ready/session-ready gates. A full validator JSON report may list warnings
inside historical `work/review-cycles/<scope>/versions/` snapshots, but those
warnings must not increment `unresolved_warning_error_count` or block the active
handoff unless the active canonical TC, active split test-design directory or
current cycle outputs contain the same finding.

## Pass Criteria

- `tests.test_codex_review_cycle_runner` has a test where an unwaived
  current-scope warning blocks `signed-off`.
- `tests.test_codex_review_cycle_runner` has a test where a structured waiver
  allows `signed-off`.
- `tests.test_codex_review_cycle_runner` has a test where snapshots, scratch
  paths, and unrelated scopes do not block the gate.
- `tests.test_codex_review_cycle_runner` has a test where writer-ready/session-ready
  gates exclude warnings from `versions/` snapshots.
- A manual validation of the v5 cycle fails with an unwaived current-scope
  warning count instead of accepting `signed-off`.

## Non-Goals

- Do not rewrite historical v5 test cases just to silence the warnings.
- Do not make root-level legacy package warnings block an unrelated active
  review cycle.
- Do not move domain validator rules into the runner; the runner only enforces
  terminal lifecycle gating around validator output.
