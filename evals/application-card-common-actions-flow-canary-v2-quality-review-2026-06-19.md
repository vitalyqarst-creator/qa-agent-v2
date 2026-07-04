# Fresh canary v2 quality review: application card common actions

## Scope

- Date: `2026-06-19`
- FT package: `ft-2-OF_17`
- Review cycle: `fts/ft-2-OF_17/work/review-cycles/application-card-common-actions-flow-canary-v2/`
- Canonical test cases: `fts/ft-2-OF_17/test-cases/section-38-application-card-common-actions-flow-canary-v2.md`
- Split test design: `fts/ft-2-OF_17/work/test-design/section-38-application-card-common-actions-flow-canary-v2/`
- Runner command: `.venv\Scripts\python.exe scripts\codex_review_cycle_runner.py run-until-terminal --state fts\ft-2-OF_17\work\review-cycles\application-card-common-actions-flow-canary-v2\cycle-state.yaml --session-timeout-seconds -1`

## Result

The action-flow fresh canary reached terminal `signed-off`.

Key terminal evidence:

- `cycle-state.yaml`: `stage_status = signed-off`, `current_stage = semantic-regression-final`, `semantic_round = 1`.
- `codex_review_cycle_runner.py validate`: `valid = true`, no runnable next session, terminal validator gate checked.
- Runner chain: `5` sessions started and completed: `writer-r1`, `structure-preflight-r1`, `semantic-review-r1`, `format-review-final`, `semantic-regression-final`.
- Terminal validator gate: `scoped_findings_count = 1`, `blocking_unwaived_count = 0`, `unresolved_warning_error_count = 0`.

## Guardrail Regression Checks

The previous critical guardrail defects did not recur:

- `writer-quality-gate.md` references the current writer-stage scoped profile: `work/review-cycles/application-card-common-actions-flow-canary-v2/outputs/scoped-validator-profile.writer-r1.json`.
- No reviewer/future scoped profile is used as writer gate evidence.
- The writer did not invent PDF page refs or PDF-only requirement IDs; `GAP-001` remains a PDF extraction/parity guard.
- The writer did not invent edit-lock mechanics after status `Отказ клиента`; `ATOM-005` remains `unclear:GAP-002`.
- Duplicate `section-35` / `section-38` cancel rows are normalized without duplicate TC coverage.

## Test Design Quality

The result is a useful positive signal for action/dialog/status flows:

- `TC-ACAF-CV2-001`: opens the cancellation reason window via `Отменить заявку`.
- `TC-ACAF-CV2-002`: checks full active `DICT-001` cancellation reasons.
- `TC-ACAF-CV2-003`: verifies `Подтвердить` without reason shows `Выберите причину отказа`.
- `TC-ACAF-CV2-004`: verifies successful refusal with one active reason changes status to `Отказ клиента`.
- `TC-ACAF-CV2-005`: verifies modal `Отменить` returns to the application card without confirming refusal.
- `TC-ACAF-CV2-006`: verifies `История заявки` opens the history viewing window, without expanding into full `section-39`.

Semantic review R1 reported:

- atomic statements: `7`;
- covered: `6`;
- gap: `0`;
- unclear: `1` (`ATOM-005` / `GAP-002`);
- open semantic findings: `0`.

## Residual Risks

- `GAP-002` is real residual uncertainty, not a blocker: the source says further editing is forbidden after `Отказ клиента`, but does not define a visible UI oracle. The canary correctly avoided inventing disabled fields, hidden save buttons, error messages or backend checks.
- The scoped validator emits one `info` finding: `test-case-sparse-required-fields`. The TC set uses slim runtime fields, while reviewer confirmed required runtime sections and fields are present. This is non-blocking, but it means this canary is not as validator-clean as `history-editing-fresh-canary-v2`.
- Split artifacts use `## <Section>` headings rather than `# <Section>` in several files. This did not trigger a validator warning because the current guardrail catches adjacent duplicate headings, not heading level. If we want the written contract to mean strict top-level `#`, the validator should enforce heading level explicitly.

## Recommendation

Treat this as a positive but not perfect second canary:

- Agent quality improved enough to start a limited pilot on real scopes.
- Do not start full-document generation yet.
- Before scaling broadly, decide whether `test-case-sparse-required-fields` and split artifact heading level should remain informational or become writer-blocking format requirements.
