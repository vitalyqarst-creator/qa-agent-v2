# Writer R1 Prompt

Run the writer stage for the confirmed AutoFin scope through the existing project rules.

Scope:

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-widget-selection-types`
- Section: `3 Ограничения`
- Canonical test-case file: `fts/AutoFin/test-cases/3-iteration-smoke-widget-selection-types.md`
- Test-design directory: `fts/AutoFin/work/test-design/3-iteration-smoke-widget-selection-types`

Required inputs:

- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-coverage-gaps.md`
- `fts/AutoFin/AGENT-NOTES.md`

Process constraints:

- This is a fresh iteration smoke run.
- Use existing skills/references/runtime rule cards/reviewer rubrics/validator gates/workflow contracts only.
- Do not use previous canary artifacts or old generated test cases as source of truth, structure template, wording template or test-design hint.
- Do not change agent-layer rules, validator, references or skills.
- Update `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml` before ending the session.
- Route to the next runner stage according to the session-based review cycle.
