# Limited pilot readiness report

## Purpose

Проверить, можно ли после свежих canary fixes переходить от canary-прогонов к ограниченному pilot на реальных scope-ах и затем к controlled batch написания тест-кейсов.

Проверка выполнена как retrospective pilot по уже существующим signed-off реальным scope-ам. Это полезный compatibility сигнал, но не заменяет live pilot: эти scope-ы были созданы до части текущих guardrails.

## Inputs

| scope | type | command |
| --- | --- | --- |
| `main-info-credit-parameters` | numeric/product parameters | `python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\main-info-credit-parameters\cycle-state.yaml` |
| `common-application-fields` | common UI field rules | `python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\common-application-fields\cycle-state.yaml` |
| `document-print-form-tags` | generated document / tag mapping | `python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\document-print-form-tags\cycle-state.yaml` |

## Initial Results

| scope | terminal validate result | first blocker | assessment |
| --- | --- | --- | --- |
| `main-info-credit-parameters` | failed | `split-artifact-redundant-section-heading` in active `work/test-design/2-1-1-1-1-1-2-main-info-credit-parameters/artifact-write-strategy.md`; `12` current-scope findings | Old signed-off scope does not satisfy current split-artifact shape guardrails. |
| `common-application-fields` | failed | `active-text-artifact-encoding-damage` in `work/review-cycles/common-application-fields/outputs/agent-decision-log.writer-format-final.md`; `4` current-scope findings | New encoding guard found real mojibake/question-mark damage in active final outputs. |
| `document-print-form-tags` | failed | `writer-quality-gate-scoped-validator-profile-invalid` in active canonical `test-cases/2-1-1-1-1-4-4-document-print-form-tags.md`; `1` current-scope finding | Older run still relies on invalid/stale scoped validator profile evidence. |

## Remediation Results

| scope | remediation | post-remediation terminal validation |
| --- | --- | --- |
| `main-info-credit-parameters` | Removed duplicate adjacent split-artifact headings in active `work/test-design/2-1-1-1-1-1-2-main-info-credit-parameters/*.md`; added missing `TDDT-013-U` gap decision for `ATOM-023 / GAP-004`; narrowed its `property_type` to `source-gap`. | `valid=true`; `terminal_validator_gate.checked=true`; `scoped_findings_count=1`; `blocking_unwaived_count=0`. |
| `common-application-fields` | Repaired active final writer/reviewer outputs containing question-mark damaged Russian field labels; restored `Цель`, `Ссылка на ФТ`, `Источник требования`, `Источник / цитата требования`, `Трассировка`; removed diagnostic question-mark marker. | `valid=true`; `terminal_validator_gate.checked=true`; `scoped_findings_count=2`; `blocking_unwaived_count=0`. |
| `document-print-form-tags` | Replaced writer gate evidence from reviewer-stage `scoped-validator-profile.semantic-review-r2.json` to runner-owned writer-stage `scoped-validator-profile.writer-structure-r1.json` with `unresolved_warning_error_count=0`. | `valid=true`; `terminal_validator_gate.checked=true`; `scoped_findings_count=5`; `blocking_unwaived_count=0`. |

## Interpretation

The retrospective pilot is intentionally stricter than the historical sign-off state. It showed that the latest guardrails are effective and that old signed-off scopes are not automatically reusable as evidence for current quality until they pass current terminal validation.

This is not a reason to weaken the validator. The failures are real classes of quality risk:

- malformed split artifacts can break section extraction and create ambiguous evidence;
- mojibake in final reviewer/writer artifacts can corrupt requirement evidence and traceability;
- invalid scoped validator profile references can make a writer gate claim `pass` without current runner-owned evidence.

After targeted remediation, all three selected real scopes pass current terminal validation. This is now a positive limited-pilot compatibility signal, with one caveat: it remains retrospective, not a newly generated live pilot.

## Stage 3 Status

Fresh canary status remains positive:

| canary | post-fix validation | evidence |
| --- | --- | --- |
| `document-print-form-tags-fresh-canary-v2` | passed | `valid=true`; terminal validator gate checked; `blocking_unwaived_count=0`; no new `active-text-artifact-encoding-damage` finding after reviewer artifact cleanup and validator guard. |

This canary supports `limited-pilot-ready`. Combined with the remediated retrospective pilot, it supports moving to controlled-batch preparation, but not unsupervised full-scale generation.

## Controlled Batch Protocol

Before any controlled batch, use this protocol:

1. Select `2-3` real scopes with confirmed `scope-contract.md`, source parity/source row inventory, and no FT slug/path mismatch.
2. For each selected scope, start a new session-based review-cycle or explicitly mark it as a migration run; do not reuse a historical signed-off state as proof.
3. Run through terminal with the sharded/long-timeout strategy already proven stable for artifact-validator and with SDK runtime preflight enabled.
4. After terminal state, run `codex_review_cycle_runner.py validate --state <cycle-state.yaml>`.
5. Score each scope with `evals/canary-quality-scorecard-2026-06-24.md`.
6. Manually sample the final canonical TC for passability and clarity before increasing batch size.
7. Treat any current-scope warning/error from the terminal validator gate as batch-blocking unless it has a narrow, documented waiver policy.

## Readiness Decision

Current status: `controlled-batch-prep-ready`.

Manual sampling evidence: `evals/limited-pilot-manual-sampling-2026-06-24.md`.

Required checks during controlled batch:

| priority | action | why |
| --- | --- | --- |
| P0 | Do not use old signed-off scopes as batch evidence unless they pass current terminal validation. | Historical sign-off predates current guardrails. |
| P0 | Keep `active-text-artifact-encoding-damage` and current-stage scoped profile checks batch-blocking. | These were real defects in retrospective pilot evidence. |
| P1 | Manually sample at least `2` TC per new scope before increasing batch size beyond controlled mode. | Retrospective compatibility is useful but weaker than fresh generation evidence. |

## Next Recommended Work

Run a small controlled batch of `2-3` new scopes. Do not revive `ui-employment-canary-v4-quality-regression` as a fresh pilot because that cycle has an FT slug/path mismatch (`ft-2-OF_16` inside `ft-2-OF_17`).
