# Structure Preflight R1 Prompt

Run `reviewer.structure_preflight` for the AutoFin session-based review cycle.

Instruction loading:

- Run `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget` before review decisions.
- Read every selected required instruction file from the resolver output.
- Record resolver command, budget status and selected files in the reviewer session output.

Scope:

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Section: `4.2. Меню «Заявки в системе»`
- Requirement id: `BSR 32`
- Active unsigned draft: `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-draft.md`
- Canonical test-case file after sign-off: `fts/AutoFin/test-cases/4.2-iteration-smoke-rerun-search-clear-context.md`
- Test-design directory: `fts/AutoFin/work/test-design/4.2-iteration-smoke-rerun-search-clear-context`
- Cycle state: `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/cycle-state.yaml`

Required inputs:

- `fts/AutoFin/AGENT-NOTES.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-coverage-gaps.md`
- `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-draft.md`
- `fts/AutoFin/work/test-design/4.2-iteration-smoke-rerun-search-clear-context`
- `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-response.md`
- `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-session-log.writer-r1.md`
- `fts/AutoFin/work/review-cycles/iteration-smoke-search-clear-context/outputs/agent-decision-log.writer-r1.md`

Review mode:

- Structure preflight only.
- Check parseability, required runtime fields, heading levels, canonical metadata fields, split artifact shape, required table columns, simple-YAML cycle state and active scoped validator profile.
- Do not perform semantic coverage review except where structure prevents reliable review.

Routing:

- If structure preflight passes, update `cycle-state.yaml` to `stage_status: semantic-review-ready`, `current_stage: semantic-review-r1`, `semantic_round: 1`, and active prompt for semantic review.
- If structure preflight blocks, update `cycle-state.yaml` to `stage_status: structure-preflight-blocked`, `current_stage: writer-structure-r1`, and create the writer remediation prompt.
