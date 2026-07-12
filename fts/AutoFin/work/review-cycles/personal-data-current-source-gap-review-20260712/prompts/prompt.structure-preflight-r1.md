# Structure Preflight R1

Scenario: `reviewer.structure_preflight`.

Before review decisions, run:

`python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget`

Read every selected required instruction file from resolver output and record resolver command, budget status and selected files in `outputs/reviewer-session-log.structure-preflight-r1.md`.

## Inputs

- `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/atomic-requirements-ledger.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/traceability-matrix.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/traceability-matrix.xlsx`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/writer-quality-gate.md`
- `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-response.md`
- `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-session-log.writer-r1.md`
- `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/agent-decision-log.writer-r1.md`
- `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/scoped-validator-profile.writer-r1.json`
- `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/cycle-state.yaml`

## Review Boundary

Perform structure preflight only: parseability, required runtime fields, `package_id`, candidate status fields, split artifact shape and state transition readiness. Do not perform semantic coverage review and do not edit draft/canonical files.

## Expected Routing

If structure passes, update `cycle-state.yaml` to `current_stage: semantic-review-r1`, `stage_status: semantic-review-ready`, `semantic_round: 1`, and active prompt `prompts/prompt.semantic-review-r1.md`.
