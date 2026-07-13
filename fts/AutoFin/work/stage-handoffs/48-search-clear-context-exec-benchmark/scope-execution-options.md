# Execution Options For `search-clear-context-exec-benchmark-v1`

## Контекст

- FT-пакет: `fts/AutoFin`
- Scope: `search-clear-context-exec-benchmark-v1`
- Status: `confirmed`, current-source, promotion-disabled.

## Подтвержденные Входы

- H19 `source-selection.md`.
- H48 scope contract, parity, row inventory, empty gaps file, opened mockup inventory and workflow state.

## Рекомендуемый Следующий Шаг

`ft-test-case-iteration`: fresh standard writer + fresh reviewer через verified `codex exec`.

## Вариант 1. Запуск Через Iteration

Использовать `prompt.scope-to-iteration.md`; результатом должен быть terminal `accepted-not-promoted` либо точный blocker без retry.

## Вариант 2. Ручной Loop Через Writer И Reviewer

Допустим только через `prompt.scope-to-writer.md`, затем отдельный reviewer. Для benchmark не рекомендуется: ухудшает сопоставимость оркестрации.

## Обязательные Guardrails

- Не читать старый H19 draft/test cases.
- Не расширять BSR 32.
- Не использовать reviewer rebind.
- Не создавать promotion target.

## Ожидаемые Выходы По Выбранному Пути

- Prepared package, one writer attempt, deterministic gates, one reviewer attempt, performance report and terminal handoff.

## Что Этот Файл Не Делает

- Не меняет workflow status и не заменяет active prompt/state.
