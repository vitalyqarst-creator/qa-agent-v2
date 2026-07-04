# Fresh canary v2 quality review: section-40 history editing

## Scope

- Date: `2026-06-19`
- FT package: `ft-2-OF_17`
- Review cycle: `fts/ft-2-OF_17/work/review-cycles/history-editing-fresh-canary-v2/`
- Canonical test cases: `fts/ft-2-OF_17/test-cases/section-40-history-editing-fresh-canary-v2.md`
- Split test design: `fts/ft-2-OF_17/work/test-design/section-40-history-editing-fresh-canary-v2/`
- Runner command: `.venv\Scripts\python.exe scripts\codex_review_cycle_runner.py run-until-terminal --state fts\ft-2-OF_17\work\review-cycles\history-editing-fresh-canary-v2\cycle-state.yaml --session-timeout-seconds -1`

## Result

The fresh canary v2 reached terminal `signed-off`.

Key terminal evidence:

- `cycle-state.yaml`: `current_stage = signed-off`, `stage_status = signed-off`, `semantic_round = 2`.
- `codex_review_cycle_runner.py validate`: `valid = true`, `terminal_validator_gate.checked = true`, `scoped_findings_count = 0`, `blocking_unwaived_count = 0`.
- `semantic-regression-final-findings.md`: semantic regression passed; R2 matrix remains `12/12` covered, `gap = 0`, `unclear = 0`.
- `format-review-final-findings.md`: final format review passed; `10` test cases, `TC-HIST-001`..`TC-HIST-010`, all required fields present.

## Guardrail Regression Checks

The two defects from the previous `history-editing-fresh-canary` run did not recur in v2:

- Split artifacts use a single canonical top-level heading; no adjacent `# X` + `## X` duplicate wrapper heading was found in `work/test-design/section-40-history-editing-fresh-canary-v2/`.
- `writer-quality-gate.md` references the current writer-stage scoped profile: `work/review-cycles/history-editing-fresh-canary-v2/outputs/scoped-validator-profile.writer-r2.json`.
- No future reviewer profile, such as `scoped-validator-profile.structure-preflight-r1.json`, is used as writer gate evidence.

## Test Design Quality

The produced set is materially stronger than the previous fresh canary:

- `ATOM-001`..`ATOM-012` are all represented in `atomic-requirements-ledger.md` and covered by `TC-HIST-001`..`TC-HIST-010`.
- `GAP-001` remains an accepted non-blocking PDF extraction/parity risk and was not converted into a fake executable behavior.
- The reviewer closed the R1 semantic findings:
  - `ATOM-004`: simultaneous edit row-count check now uses a fixture-backed timestamp and exact field/value triplets.
  - `ATOM-008`..`ATOM-012`: table column visibility and sortability are covered by explicit table composition and sorting checks.
- Multi-column checks are grouped only where the scope contract allows one executable check for repeated table-column behavior.

## Residual Risks

- The full root validator report for `fts/ft-2-OF_17` still contains historical errors/warnings from older generated artifacts. This does not affect terminal v2 status because the scoped terminal gate reports zero active findings for `history-editing-fresh-canary-v2`.
- The outer shell wait hit a 2-hour timeout while the runner was still alive. The runner itself continued, kept heartbeat fresh, completed `semantic-regression-final`, released the lock and reached `signed-off`. This is a monitoring/runtime issue, not a canary quality failure.
- `TC-HIST-008` intentionally verifies all sortable table columns in one case. This is acceptable for manual FT coverage by current project rules, but UI automation prep may later split it into smaller automation-ready checks if execution ergonomics require it.

## Recommendation

Use `history-editing-fresh-canary-v2` as the current positive regression signal for the latest agent improvements. The next useful check should be a different scope shape, preferably an action/dialog flow rather than another compact table-only section, to test whether the same quality holds for state transitions and validation feedback.
