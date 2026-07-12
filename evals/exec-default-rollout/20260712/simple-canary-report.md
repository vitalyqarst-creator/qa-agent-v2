# Отчёт по exec-default canary

Дата: 2026-07-12

Cycle: `codex-exec-dispatcher-canary-20260712-01`

Scope profile: `simple-field-property`
Prepared package: v5, 6 testable obligations

## Результат

- Dispatcher в режиме `auto` выбрал проверенный `codex exec`, contract v2.
- SDK fallback не разрешался и не использовался.
- Writer завершил draft, deterministic gates прошли.
- Reviewer запущен в отдельной read-only сессии и принял draft.
- Итоговый process-status: `accepted-not-promoted`.
- Production target не существовал до запуска и не был создан.
- Non-zero exit code ожидаем: runner считает непродвинутый draft незавершённым production-результатом даже после reviewer acceptance.

## Метрики

| Показатель | Значение |
| --- | ---: |
| Полное время writer + reviewer | 122.469 с |
| Writer | 102.000 с |
| Reviewer | 20.469 с |
| Total tokens | 162 438 |
| Writer tokens | 140 251 |
| Reviewer tokens | 22 187 |
| Cached writer input tokens | 85 504 |
| Validator invocations | 1 из бюджета 5 |
| Backend sessions | 2, идентификаторы различаются |

Предыдущий подготовленный exec-canary того же класса занял около 120.0 с; текущий dispatcher-run отличается примерно на 2%, то есть новый слой выбора backend не дал заметной временной регрессии. SDK baseline для personal-data scope занял 9 245 с, но он содержал 47 тест-кейсов и другой набор стадий, поэтому это только исторический ориентир, а не корректное прямое сравнение скорости.

## Обнаруженные и исправленные проблемы

1. Значения CLI-флагов вида `--sandbox` нельзя передавать child parser отдельным токеном после `--sandbox-flag`. Dispatcher теперь связывает такие пары как `--sandbox-flag=--sandbox`; добавлен regression-тест.
2. Prepared promotion dry-run требует настоящий promotion contract. Для canary без утверждённого production-контракта выбран честный безопасный статус `accepted-not-promoted`, а не фиктивный контракт.

## Вывод

Canary подтверждает готовность verified exec backend быть default route для новых prepared cycles. SDK следует оставлять только явным диагностическим fallback. Следующий риск находится не в dispatcher, а в стоимости writer context: 140 251 токенов для шести простых obligations всё ещё много и требует отдельной оптимизации prepared writer payload.
