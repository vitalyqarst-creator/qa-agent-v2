# Structure Preflight R1 Prompt

Run the `reviewer.structure_preflight` stage for the confirmed AutoFin scope.

## Goal

Check parseability and blocking format prerequisites only for the writer R1 draft. Do not perform semantic coverage review in this stage.

## Inputs

- `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml`
- `fts/AutoFin/test-cases/3-iteration-smoke-widget-selection-types.md`
- `fts/AutoFin/work/test-design/3-iteration-smoke-widget-selection-types/`
- `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/outputs/writer-r1-response.md`
- `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/outputs/writer-session-log.writer-r1.md`
- `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/outputs/agent-decision-log.writer-r1.md`
- `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/outputs/scoped-validator-profile.writer-r1.json`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-coverage-gaps.md`
- `fts/AutoFin/AGENT-NOTES.md`

## Guardrails

- Use session-based stage statuses from `cycle-state.yaml`.
- Reviewer must not edit the canonical test-case file.
- Structure preflight may route to `semantic-review-ready` or `structure-preflight-blocked` only.
- Do not convert candidate UI-calibration semantics into executable sign-off in this stage.
