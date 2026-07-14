# V5 Canary Protocol

## Цель

Проверить, устраняет ли package v8 terminal blocker V4: exact values OBL-013 должны сохраниться без возврата exhaustive dictionary payload writer-у.

## Один сопоставимый запуск

- Fresh cycle `visual-assessment-medium-scope-benchmark-v5-20260714`.
- Backend `exec`, 13 obligations, 12 planned TC, те же runtime limits, что в V4-r1.
- Budget: один dispatcher invocation без retry, resume, repair, rebind, sharding, SDK fallback и promotion.

## Quality gates

- Deterministic reference-fixture gate проходит до reviewer.
- OBL-013 содержит обе exact source-backed fixture и корректный group path.
- Reviewer: 13/13 covered, incorrect = 0, error findings = 0.
- OBL-006/OBL-007 exhaustive materialization и ownership gates сохраняются.
- Validator invocations = 1; fallback = false; production target отсутствует.
- Три protected baseline SHA-256 неизменны.

## Performance

Duration/tokens публикуются как observation. Один V5 canary не доказывает устойчивую производительность и не разрешает выбирать лучший результат.

## Stop conditions

Любой deterministic/reviewer quality failure, package drift, fallback или baseline mutation завершает V5. Повтор в этой итерации запрещён.
