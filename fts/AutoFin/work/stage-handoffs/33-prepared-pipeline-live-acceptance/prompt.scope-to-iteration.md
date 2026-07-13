# Переход к следующему prepared canary

## Цель этапа

После успешного V4 выбрать один следующий canary: сначала узкий numeric/date boundary package, затем отдельный conditional/integration package. Не использовать текущий 66-obligation mixed baseline как первый live boundary canary без предварительного сужения.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`.
- `work/stage-handoffs/33-prepared-pipeline-live-acceptance/eval-matrix.md`.
- `work/stage-handoffs/33-prepared-pipeline-live-acceptance/live-acceptance-report.md`.
- `work/stage-handoffs/33-prepared-pipeline-live-acceptance/stop-gate.md`.
- `work/review-cycles/personal-data-character-restrictions-shadow-v4-20260712/cycle-state.yaml`.

## Guardrails

- Сначала сузить boundary eval до 5–15 однородных obligations с подтвержденными fixtures/oracles.
- Создать новый immutable package и validate-only; V4 не переиспользовать.
- Запускать ровно один live canary и останавливаться при quality или performance miss.
- SDK fallback, promotion и production overwrite запрещены.
- Не смешивать generated drafts с requirement evidence.
