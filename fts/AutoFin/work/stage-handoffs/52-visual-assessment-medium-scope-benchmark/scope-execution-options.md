# Execution Options For `visual-assessment-medium-scope-benchmark`

## Контекст

- FT-пакет: `fts/AutoFin`
- Scope status: confirmed current-source benchmark.
- Канонический state: `workflow-state.yaml`.

## Подтвержденные Входы

- `source-selection.md`, `scope-contract.md`, `source-parity-check.md`.
- `source-row-inventory.md`, `requiredness-oracle-inventory.md`, `mockup-visual-inventory.md`.
- `scope-coverage-gaps.md`, `prompt.scope-to-iteration.md`, `workflow-state.yaml`.

## Рекомендуемый Следующий Шаг

`ft-test-case-iteration` с отдельными fresh writer/reviewer sessions и promotion disabled.

## Вариант 1. Запуск Через Iteration

- Compile immutable package, run pre-live gates, checkpoint, separate one-shot authorization and exactly one exec dispatcher.

## Вариант 2. Ручной Loop Через Writer И Reviewer

- Допустим только как отдельная будущая задача; для benchmark не используется, потому что изменит сравниваемый процесс.

## Обязательные Guardrails

- No SDK fallback, sharding, retry, resume, rebind or production promotion.
- Stop before LLM on source/dictionary/oracle/identity/capacity blocker.

## Ожидаемые Выходы По Выбранному Пути

- Immutable prepared package, draft, semantic findings, performance evidence and terminal handoff.

## Что Этот Файл Не Делает

- Не разрешает live-запуск и не меняет process-status.
