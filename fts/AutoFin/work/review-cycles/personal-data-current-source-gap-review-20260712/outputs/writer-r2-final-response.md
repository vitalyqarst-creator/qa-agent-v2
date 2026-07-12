Used `ft-test-case-writer` for the writer semantic revision.

Done:
- Added `TC-ACPD-047` in the unsigned R2 draft to cover `ATOM-013` / optional `Отчество`.
- Wrote the R2 draft to `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r2-draft.md`.
- Synchronized bounded test-design artifacts for the reviewed findings: atomic ledger, decision table, coverage map/metrics, fixtures, requiredness/source normalization, traceability, applicability, writer gates.
- Added R2 sidecar artifacts:
  - `outputs/writer-r2-response.md`
  - `outputs/writer-session-log.writer-r2.md`
  - `outputs/agent-decision-log.writer-r2.md`
  - `prompts/prompt.semantic-review-r2.md`
  - `outputs/scoped-validator-profile.writer-r2.json`
- Updated `cycle-state.yaml` to `current_stage: semantic-review-r2`, `stage_status: semantic-review-ready`, `semantic_round: 2`, with the active transition prompt set to `prompt.semantic-review-r2.md`.

Validation:
- Instruction resolver passed: `183.3 / 240.0 KiB`.
- `validate_agent_artifacts.py` completed and wrote `validator-report.writer-r2.latest.json`.
- `codex_review_cycle_runner.py validate --state ...cycle-state.yaml` passed with `valid: true`.

I did not modify the canonical production test case file. Promotion remains reviewer/runner-owned after sign-off. `git status` could not be used because Git rejected the workspace as dubious ownership under the current sandbox user, so I did not claim a clean working tree.