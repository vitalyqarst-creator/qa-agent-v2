# Переход к conditional/integration canary

## Цель этапа

Проверить standard structured pipeline на одном узком conditional-state пакете. Integration/persistence использовать только при наличии воспроизводимого fixture и наблюдаемого oracle; иначе выбрать UI-observable conditional scope.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`.
- `work/stage-handoffs/02-application-card-client-addresses-contacts/scope-contract.md`.
- `work/stage-handoffs/02-application-card-client-addresses-contacts/source-parity-check.md`.
- `work/stage-handoffs/34-client-address-numeric-boundary-canary/scope-contract.md`.
- `work/stage-handoffs/34-client-address-numeric-boundary-canary/scope-coverage-gaps.md`.
- `work/stage-handoffs/34-client-address-numeric-boundary-canary/source-parity-check.md`.
- `work/stage-handoffs/34-client-address-numeric-boundary-canary/source-row-inventory.md`.
- `work/stage-handoffs/33-prepared-pipeline-live-acceptance/eval-matrix.md`.
- `work/stage-handoffs/34-client-address-numeric-boundary-canary/live-acceptance-report.md`.
- `work/stage-handoffs/34-client-address-numeric-boundary-canary/agent-decision-log.md`.
- `work/review-cycles/client-address-numeric-boundary-shadow-v2-20260713/cycle-state.yaml`.

## Guardrails

- Выбрать 5–15 однородных obligations; не брать широкий mixed scope.
- До build явно проверить соответствие constraint-gap representation ожидаемому context profile.
- Создать новый immutable package и сначала выполнить validate-only.
- Запустить ровно один live canary и остановиться при любом quality/performance miss.
- SDK fallback, promotion и production overwrite запрещены.
- Не использовать generated drafts как requirement evidence.

## Ожидаемый выход

- Один accepted или evidence-backed blocked conditional canary.
- Сравнение fixed overhead с V4 и numeric V2.
- Отдельное решение, достаточно ли трёх профилей для controlled rollout.
