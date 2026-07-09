# Instruction Budget Optimization Report

## Цель

Снизить runtime instruction budget без ослабления QA-гейтов. Оптимизация выполнена через manifest routing: full-loop стал orchestration-only, а детальные writer/reviewer/source правила остались в stage-specific сценариях.

## Before / After

| scenario | before KiB | after KiB | limit KiB | headroom KiB | delta KiB | status |
|---|---:|---:|---:|---:|---:|---|
| `iteration.full_loop` | 445.1 | 118.1 | 445.0 | 326.9 | -327.0 | pass |
| `writer.initial_draft.table` | 297.9 | 284.6 | 300.0 | 15.4 | -13.3 | pass |
| `writer.session_initial_draft` | 154.0 | 155.8 | 200.0 | 44.2 | +1.8 | pass |
| `reviewer.semantic_traceability_test_design` | 264.9 | 266.8 | 290.0 | 23.2 | +1.9 | pass |
| `reviewer.structure_format_final` | 244.0 | 224.7 | 260.0 | 35.3 | -19.3 | pass |
| `writer.remediation.validator_failure` | 276.3 | 276.3 | 292.0 | 15.7 | 0.0 | pass |
| `writer.session_format_revision` | 236.2 | 216.9 | 240.0 | 23.1 | -19.3 | pass |
| `reviewer.full_existing_cases` | 257.5 | 241.9 | 262.0 | 20.1 | -15.6 | pass |

Budget limits were not increased. Resolver now reports `headroom_kib`, `headroom_percent`, per-group totals and top files. `--fail-on-budget` fails both `fail` and `near_limit`; default minimum headroom is 15.0 KiB, and `iteration.full_loop` requires 30.0 KiB.

## Main Routing Changes

`iteration.full_loop` now loads only:

| group | KiB | role |
|---|---:|---|
| `iteration_core` | 67.7 | lifecycle, workflow state, handoff, session/decision logs |
| `review_cycle_core` | 24.7 | session-based review cycle and SDK orchestration |
| `global_core` | 21.9 | root/project routing context |
| `iteration_stage_summaries` | 3.7 | compact stage routing and high-risk QA rule cards |

Removed from full-loop required context and kept conditional/stage-specific:

- `source_locator_core`
- `scope_manual_core`
- `writer_core`
- `writer_process_artifacts`
- `writer_revision_artifacts`
- `reviewer_core`

This is the main saving: full-loop dispatch no longer carries all source/scope/writer/reviewer deep rules at once.

## Deep References Moved Out Of Default Runtime

No semantic rule was deleted. Heavy references were moved to narrower scenarios:

- `test-case-style-examples.md` is no longer loaded by `reviewer.structure_format_final` or `writer.session_format_revision`; it remains in `writer.remediation.style`.
- `test-design-defect-taxonomy.md` is no longer in default table writer artifacts; it remains in semantic reviewer and validator-failure remediation contexts.
- `package-test-design-plan-format.md` and `dictionary-inventory-format.md` were removed from broad `reviewer_core`; they remain in semantic/table/deep scenarios where the reviewer needs them.

## QA Gates Preserved

Compact runtime cards keep high-risk rules visible in default writer/reviewer sessions while detailed examples stay in validator tests/evals/deep references:

- `source-backed-input-restriction-gap-only`
- `test-case-ui-calibration-candidate-missing-concrete-invalid-value`
- `rolling-date-boundary-static-test-data`
- `test-case-overmerged-atoms-without-rationale`
- `test-case-excessive-atom-fan-in`
- `missing-representative-strategy`
- `production-setup-profile-reference`
- `test-case-generic-test-data-reference-smell`
- `test-case-generic-test-data-oracle-smell`
- `test-case-title-process-marker-smell`

Added validator coverage:

- `missing-representative-strategy`: warning when an artifact explicitly declares partial/sampled/representative coverage for similar fields but does not document representative/pairwise strategy or residual risk.

## Residual Risk

`writer.initial_draft.table` has 15.4 KiB headroom and `writer.remediation.style` has 15.1 KiB headroom. They pass the new minimum but are close to the threshold. Further savings should split heavy table/style references into narrower profile groups; deleting semantic gates would be the wrong trade-off.

## Verification Snapshot

Budget sweep after changes: all manifest scenarios are `pass`; no scenario is `near_limit` or `fail`.

Strict canary behavior was checked against the original independent-wide-canary gap fixture. The old artifact remains diagnostic evidence and is not rewritten. The v2 artifact validates with zero errors under strict canary flags.
