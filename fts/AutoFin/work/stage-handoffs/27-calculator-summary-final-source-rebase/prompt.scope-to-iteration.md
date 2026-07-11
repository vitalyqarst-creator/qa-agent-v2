# Prompt: Final Calculator Scope To Iteration

Использовать только после passed `scope_gap_review`.

## Required Inputs

- `../20-prepared-autofin-cross-scope/source-selection.md`
- `scope-contract.md`
- `source-parity-check.md`
- `source-row-inventory.md`
- `scope-coverage-gaps.md`
- `scope-clarification-requests.md`
- `scope-gap-review.md`
- `workflow-state.yaml`
- `../../../AGENT-NOTES.md`

## Execution

- Skill: `ft-test-case-iteration`.
- Mode: fresh prepared-standard diagnostic run.
- Writer and reviewer must use separate new sessions.
- `package_id = WP-01` is mandatory for every ATOM/TC.
- Run package ledger, Package Test Design Plan and package TC self-check gates in order.
- Preserve `BSR 43–46`; reject `BSR 35–38` as calculator-summary traceability.
- Preserve `GAP-001` for exhaustive prefill mapping.
- Promotion is disabled; production path is read-only.

## Completion Gate

- Five testable obligations covered, exact-mapping gap preserved, reviewer accepted, production diff empty, session IDs distinct.
