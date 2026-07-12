# Переход к eval и live acceptance prepared pipeline

## Цель этапа

Выполнить оставшиеся блоки 11–12: репрезентативный eval corpus и затем отдельно разрешённый live V4 для character restrictions. Доказать качество и фактическое снижение времени/tokens.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`.
- `work/stage-handoffs/32-prepared-standard-pipeline-optimization/architecture-baseline.md`.
- `work/stage-handoffs/32-prepared-standard-pipeline-optimization/iteration-summary.md`.
- `work/stage-handoffs/32-prepared-standard-pipeline-optimization/validate-only-report.v4.json`.
- `work/stage-handoffs/32-prepared-standard-pipeline-optimization/dispatcher-config.v4.json`.
- `work/review-cycles/personal-data-character-restrictions-shadow-v4-20260712/prepared-input/personal-data-character-restrictions-v4/stage-package.json`.

## Guardrails

- Сначала сформировать immutable eval baselines для static, character restriction, boundary и conditional/integration profiles.
- Не запускать несколько live scopes одновременно; применять stop-gate после каждого.
- V4 запускать через dispatcher config только после проверки, что cycle содержит лишь prepared-input.
- SDK fallback и promotion запрещены.
- GAP-001, 12/12 obligations, unique titles, calibration lifecycle и production isolation обязательны.
- Сравнивать uncached tokens, context bytes, commands и duration; не маскировать стоимость cached tokens.
