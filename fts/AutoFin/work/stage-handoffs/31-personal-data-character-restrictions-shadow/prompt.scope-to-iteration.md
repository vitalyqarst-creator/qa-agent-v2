# Переход к следующей ft-test-case-iteration

## Цель этапа

Оптимизировать prepared `standard-required` route на том же scope `BSR 48`, `BSR 51`, `BSR 54`: снизить context, command count и token cost без потери 12/12 coverage, GAP-001 и независимого reviewer sign-off.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/workflow-state.yaml`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/iteration-summary.md`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/prompt.standard-context-optimization.md`.
- `work/review-cycles/personal-data-character-restrictions-shadow-v3-20260712/performance.json`.
- `work/review-cycles/personal-data-character-restrictions-shadow-v3-20260712/cycle-state.yaml`.

## Guardrails

- Сначала выполнить `agent-architecture-auditor`, затем продолжить через `ft-test-case-iteration`.
- Production baseline не читать как evidence, не изменять и не promoted.
- Не ослаблять GAP-001 и не выдумывать точную UI-реакцию.
- Новый live cycle запускать только после unit tests и validate-only replay.
- V3 использовать только как process/performance baseline, не как requirement source.
