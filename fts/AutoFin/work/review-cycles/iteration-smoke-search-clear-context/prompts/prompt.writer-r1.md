# Writer R1 Prompt

Run the writer stage for the confirmed AutoFin scope through the existing project rules.

Scope:

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Section: `4.2. Меню «Заявки в системе»`
- Requirement id: `BSR 32`
- Canonical test-case file: `fts/AutoFin/test-cases/4.2-iteration-smoke-rerun-search-clear-context.md`
- Test-design directory: `fts/AutoFin/work/test-design/4.2-iteration-smoke-rerun-search-clear-context`

Required inputs:

- `fts/AutoFin/AGENT-NOTES.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-coverage-gaps.md`

Process constraints:

- This is a fresh iteration smoke rerun after the runner completion fix.
- Use only existing skills, references, runtime rule cards, reviewer rubrics, validator gates and workflow contracts.
- Do not use previous generated test cases, previous canary artifacts, previous smoke outputs or historical reviewer outputs as source of truth, structure template, wording template or test-design hint.
- Do not change agent-layer rules, validator, references or skills.
- Preserve `BSR 32` as the requirement id.
- Cover all behavior dimensions explicitly stated by the source: filters, sorting, pagination and row-selection state.
- Do not invent concrete filter fields, default sorting values, page size, messages, row counts, backend state, persistence or API effects.
- Update `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/cycle-state.yaml` before ending the session.
- Route to the next runner stage according to the session-based review cycle.

Expected writer outputs:

- Canonical test-case draft at `fts/AutoFin/test-cases/4.2-iteration-smoke-rerun-search-clear-context.md`
- Test-design artifacts under `fts/AutoFin/work/test-design/4.2-iteration-smoke-rerun-search-clear-context`
- Writer response, session log and decision log under `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/outputs`
- Next prompt for `structure-preflight-r1` under `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/prompts`
