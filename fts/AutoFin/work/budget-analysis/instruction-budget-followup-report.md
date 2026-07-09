# Instruction Budget Follow-up Report

## Scope

Branch: `audit/stabilize-testcase-agent-budget-optimization-followup`

Base commit: `be0559ccd2634d2f9afb63a677e7c585ec8b622a`

Final commit hash: see final pushed commit for this report. A committed file cannot reliably contain its own final hash without changing that hash.

No test-case artifacts were regenerated. The old independent-wide-canary remains a diagnostic failure fixture.

## Baseline Before

Baseline was captured before follow-up edits from `audit/stabilize-testcase-agent-budget-optimization`.

| scenario | before KiB | limit KiB | before headroom | before headroom % | selected groups |
|---|---:|---:|---:|---:|---|
| `iteration.full_loop` | 118.1 | 445.0 | 326.9 | 73.5 | `global_core`, `review_cycle_core`, `iteration_core`, `iteration_stage_summaries` |
| `writer.initial_draft.table` | 284.6 | 300.0 | 15.4 | 5.1 | `global_core`, `writer_core`, `quality_rule_cards`, `writer_process_artifacts`, `writer_table_artifacts` |
| `writer.remediation.validator_failure` | 276.3 | 292.0 | 15.7 | 5.4 | `global_core`, `writer_core`, `writer_validator_failure_deep` |
| `writer.remediation.style` | 164.9 | 180.0 | 15.1 | 8.4 | `global_core`, `writer_core`, `style_remediation` |
| `reviewer.semantic_traceability_test_design` | 266.8 | 290.0 | 23.2 | 8.0 | `global_core`, `review_cycle_core`, `reviewer_semantic_core`, `reviewer_process_artifacts` |
| `reviewer.structure_format_final` | 224.8 | 260.0 | 35.2 | 13.5 | `global_core`, `review_cycle_core`, `reviewer_structure_format_core`, `reviewer_process_artifacts` |

Baseline leakage candidates:

- `writer.initial_draft.table`: default-loaded optional/deep table artifacts such as `coverage-obligation-table-format.md`, `test-design-review-format.md`, risk/state/metrics templates and full `writer-quality-gate-format.md`.
- `writer.remediation.validator_failure`: default-loaded broad deep references at once, including `writer-output-format.md`, full `test-case-format.md`, full `writer-quality-gate-format.md` and defect taxonomy.
- `writer.remediation.style`: default-loaded long `test-case-style-examples.md`.

## After Optimization

| scenario | before KiB | after KiB | limit KiB | before headroom | after headroom | delta KiB | status |
|---|---:|---:|---:|---:|---:|---:|---|
| `iteration.full_loop` | 118.1 | 118.1 | 445.0 | 326.9 | 326.9 | 0.0 | pass |
| `writer.initial_draft.table` | 284.6 | 206.4 | 300.0 | 15.4 | 93.6 | -78.2 | pass |
| `writer.remediation.validator_failure` | 276.3 | 88.6 | 292.0 | 15.7 | 203.4 | -187.7 | pass |
| `writer.remediation.style` | 164.9 | 145.0 | 180.0 | 15.1 | 35.0 | -19.9 | pass |
| `reviewer.semantic_traceability_test_design` | 266.8 | 266.8 | 290.0 | 23.2 | 23.2 | 0.0 | pass |
| `reviewer.structure_format_final` | 224.8 | 224.8 | 260.0 | 35.2 | 35.2 | 0.0 | pass |

Full budget sweep after optimization: all manifest scenarios are `pass`; no `near_limit` and no `fail`.

## Changed Loading

Removed from default `writer.initial_draft.table` loading and moved to explicit deep/debug loading:

- `references/agent/coverage-obligation-table-format.md`
- `references/agent/test-design-coverage-metrics-format.md`
- `references/agent/fixture-catalog-format.md`
- `references/agent/risk-priority-map-format.md`
- `references/agent/state-model-coverage-format.md`
- `references/agent/experience-based-coverage-format.md`
- `references/agent/test-design-review-format.md`
- `references/agent/writer-quality-gate-format.md`

Removed from default `writer.remediation.validator_failure` loading and moved to `writer.remediation.validator_failure.deep_debug`:

- `references/agent/writer-output-format.md`
- `references/agent/writer-quality-gate-format.md`
- `references/agent/dictionary-inventory-format.md`
- `references/agent/test-design-defect-taxonomy.md`
- `references/qa/test-case-format.md`

Removed from default `writer.remediation.style` loading and moved to `writer.remediation.style.deep_examples`:

- `references/qa/test-case-style-examples.md`

## New Compact Files And Maps

- `references/agent/table-writer-runtime-checklist.md`
- `references/agent/validator-finding-remediation-map.md`
- `references/agent/style-remediation-checklist.md`
- `references/agent/deep-reference-loading-policy.md`

New explicit deep scenarios:

- `writer.initial_draft.table.deep_debug`
- `writer.remediation.validator_failure.deep_debug`
- `writer.remediation.style.deep_examples`

Existing scenario limits were not increased. New deep/debug scenarios have their own explicit budgets because they are not default runtime paths.

## Quality Preservation

QA rules remain protected by compact cards, remediation map, validator checks, tests, reviewer rubrics or deep references:

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

`iteration.full_loop` remains orchestration-only and stays below the 150 KiB acceptance ceiling.

## Remaining Budget Risks

No acceptance blocker remains.

Closest active default scenarios after follow-up:

- `source_locator.discovery`: 17.6 KiB headroom.
- `reviewer.full_existing_cases`: 20.0 KiB headroom.
- `writer.session_format_revision`: 23.0 KiB headroom.
- `reviewer.semantic_traceability_test_design`: 23.2 KiB headroom.

These are above the 15 KiB policy. Future additions should prefer compact cards/maps or explicit deep scenarios rather than growing default contexts.
