# Отчёт по structured prepared writer canary

Дата: 2026-07-12

Успешный cycle: `codex-exec-structured-writer-canary-20260712-02`

Baseline cycle: `codex-exec-dispatcher-canary-20260712-01`
Scope: один и тот же `simple-field-property` package class, 6 testable obligations

## Результат

- Dispatcher выбрал verified `codex exec`; SDK fallback не разрешался и не использовался.
- Writer запущен в `read-only` с command budget `0` и вернул schema-constrained JSON.
- Writer не выполнил команд и не создал file-change event.
- Runner атомарно материализовал `draft.md`, затем один раз запустил structure validator и существующие seed/obligation/evidence gates.
- Все 6 obligations покрыты; deterministic findings отсутствуют.
- Reviewer запущен в новой отдельной read-only сессии и вернул `accepted`.
- Итог: `accepted-not-promoted`; production target не создан.

## A/B метрики

| Показатель | Workspace baseline | Structured writer | Изменение |
| --- | ---: | ---: | ---: |
| Writer duration | 102.000 с | 34.766 с | −65.9% |
| Writer total tokens | 140 251 | 22 119 | −84.2% |
| Writer uncached input | 52 066 | 20 560 | −60.5% |
| Writer commands | 1 | 0 | −100% |
| Writer file changes | 1 | 0 | −100% |
| Полное время цикла | 122.469 с | 59.094 с | −51.8% |
| Total cycle tokens | 162 438 | 43 966 | −72.9% |
| Uncached cycle input | 73 474 | 41 752 | −43.2% |
| Validator invocations | 1 | 1 | без изменения |

Размер writer input artifacts почти не изменился: 65 202 -> 65 687 байт. Следовательно, основной выигрыш получен не за счёт удаления QA-контекста, а за счёт отказа от workspace interactions и повторной обработки контекста после них.

## Transport blocker и исправление

Первый structured cycle `...-01` был остановлен до генерации: API отверг корневой JSON Schema `oneOf`. Cycle не переиспользовался. Schema переведена на проверенное transport-compatible плоское подмножество, а условные инварианты `draft-ready` / `blocked-input` оставлены обязательной runner-side проверкой. Новый immutable cycle `...-02` прошёл.

## Решение об активации

Structured writer удовлетворил всем acceptance criteria и активирован как default только для `simple-field-property`. `standard-required` остаётся workspace writer. Legacy prepared-fast workspace mode доступен лишь через явный `--prepared-fast-writer-mode workspace`; malformed JSON, timeout, command attempt или validator failure не включают его автоматически.
