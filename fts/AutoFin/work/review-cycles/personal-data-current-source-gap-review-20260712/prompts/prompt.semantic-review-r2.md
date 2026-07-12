# Semantic Review R2 Prompt

Review writer-r2 semantic revision for `application-card-client-personal-data`.

## Instruction Loading

Before domain work, run:

`python scripts/resolve_instruction_context.py --scenario reviewer.semantic_traceability_test_design --budget-report --fail-on-budget`

Read every selected required instruction file before reviewer decisions, and record resolver command, budget status and selected files in the reviewer session log.

## Required Inputs

- `AGENT-NOTES.md`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/cycle-state.yaml`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r2-draft.md`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/round-1-findings.md`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/round-1-traceability-matrix.md`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r2-response.md`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-session-log.writer-r2.md`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/agent-decision-log.writer-r2.md`
- `work/test-design/14-application-card-client-personal-data/`
- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/negative-oracle-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/requiredness-oracle-inventory.md`

## Review Focus

- Verify `SEM-001`..`SEM-005` closure.
- Confirm `ATOM-013` is covered by `TC-ACPD-047` and not by display-only `TC-ACPD-001`.
- Confirm stale requiredness mappings were corrected to `TC-ACPD-022`..`TC-ACPD-025` and `TC-ACPD-041`.
- Confirm `coverage-map.md` reflects 42 atoms, 47 draft TC, `SRC-001`..`SRC-011`, `BSR 47`..`BSR 77`.
- Confirm fixture `used_by` mappings match current draft numbering.

## Completion

Do not edit writer artifacts. Route according to `session-based-review-cycle-format.md`: pass to format review only if no error/warning findings and no traceability gaps remain; otherwise apply round-2 cap rules.
