# V4 Benchmark Protocol

## Цель

Проверить, сокращает ли runner-owned exhaustive dictionary writer workload без регрессии качества и без изменения FT-first baseline.

## Сопоставимые запуски

- Три fresh cycle: `v4-r1`, `v4-r2`, `v4-r3`.
- Одинаковый package id, compiler input, source evidence, 13 obligations, 12 planned TC, runtime limits и backend `exec`.
- Различаются только cycle/attempt roots и backend session ids.
- Каждый cycle имеет budget ровно один dispatcher invocation, без retry, resume, rebind, repair, sharding, SDK fallback и promotion.

## Последовательность

1. Запустить `v4-r1` как canary.
2. Если writer gate, reviewer acceptance или production boundary не пройдены, остановить итерацию и не запускать `v4-r2/r3`.
3. При полном quality pass выполнить `v4-r2`, затем `v4-r3`.
4. Не выбирать лучший run; опубликовать все результаты и median.

## Quality Gates

- В каждом run reviewer покрывает 13/13 obligations, incorrect = 0, error findings = 0.
- Writer ownership gate проходит; raw writer output не перечисляет exhaustive values.
- Итоговая runner projection содержит 47 hierarchy entries для OBL-006 и 39 leaf entries для OBL-007.
- Calibration lifecycle сохраняет OBL-008 и OBL-010.
- Validator invocations = 1; fallback = false; commands/file changes = 0/0.
- Три protected baseline SHA-256 неизменны, production target отсутствует.

## Performance Verdict

- Главная метрика: median total stage duration трёх runs < 120 000 ms.
- Writer median должен быть ниже V3 writer duration 86 969 ms.
- Median uncached tokens per obligation не хуже V3 3 110,31 более чем на 10%.
- Orchestration overhead <= 15%.
- Single-run result публикуется как observation, но не определяет общий performance verdict.

## Stop Conditions

- Любая quality regression, package/input drift, baseline mutation или fallback — реальный blocker.
- Неуспех только duration target не разрешает retry; он переводит работу в offline prompt/model-profile analysis.
