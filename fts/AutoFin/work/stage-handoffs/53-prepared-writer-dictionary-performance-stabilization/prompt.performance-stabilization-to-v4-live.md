# Переход к V4 live benchmark

## Цель этапа

После pushed offline checkpoint выполнить условную последовательность V4 r1-r3 и получить median без изменения production.

## Входные артефакты

- `work/stage-handoffs/53-prepared-writer-dictionary-performance-stabilization/benchmark-protocol.v4.md`
- `work/stage-handoffs/53-prepared-writer-dictionary-performance-stabilization/pre-live-stop-gate.md`
- три dispatcher config и три immutable prepared package;
- hash-bound authorization artifact, созданный после checkpoint push.

## Обязательные действия

- Выполнить r1 ровно один раз.
- Проверить 13/13, ownership/completeness/calibration gates и protected hashes.
- Только при полном quality pass выполнить r2 и r3 по одному разу.
- Опубликовать все metrics и median, не выбирать лучший run.

## Ограничения

- Без retry, resume, fallback, repair, sharding и promotion.
- V3 и production baseline не изменять.
- При quality failure остановиться до следующего live.

## Ожидаемые выходы

- три либо меньше terminal live result по stop policy;
- median performance analysis;
- terminal stop gate и следующий offline/generalization prompt.

## Gate завершения

Все разрешённые runs терминальны, quality verdict честно отделён от performance verdict, production boundary подтверждён.
