# Terminal Stop Gate V4

## Status

`blocked-quality-r1`

## Выполнено

- r1 invocation budget израсходован ровно один раз.
- Reviewer: `changes-required`; OBL-013 = `incorrect`; F-001 severity = `error`.
- Production target отсутствует; три protected baseline SHA-256 неизменны.
- Fallback, retry, resume, rebind, repair, sharding и promotion не использовались.

## Закрытые бюджеты

- r1: terminal, budget = 0.
- r2: отозван из-за failed r1 quality gate, invocations = 0.
- r3: отозван из-за failed r1 quality gate, invocations = 0.

## Следующее разрешённое действие

Только offline-изменение процесса: first-class transport точных reference-only fixture values, их детерминированная вставка в seed либо pre-review fidelity gate, negative regression и новый immutable V5 package. Новый live требует отдельного checkpoint и authorization; V4 повторять нельзя.
