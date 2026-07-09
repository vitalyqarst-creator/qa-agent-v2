# Prompt: Scope To Iteration

## Goal

Run the existing session-based writer/reviewer cycle for the confirmed AutoFin scope `iteration-smoke-widget-selection-types`.

## Inputs

- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/negative-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/requiredness-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/workflow-state.yaml`
- `fts/AutoFin/AGENT-NOTES.md`

## Iteration State

- `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml`

## Guardrails

- Do not use previous canary artifacts or old generated test cases as source of truth or structure/template.
- Do not change agent-layer rules, validator, references or skills for this scope.
- Run writer and reviewer stages as separate SDK sessions through `scripts/run_cycle.ps1`.
- Maximum semantic review rounds: `2`.
- Do not create a final production TC manually if the live runner/SDK is unavailable.
