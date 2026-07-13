# Протокол V2 Medium-Scope Benchmark

## Цель

Проверить исправленный prepared package v7 на том же H52 scope без изменения FT-first baseline и без использования старого draft как requirement evidence.

## Неизменяемая база сравнения

| Метрика | V1 |
| --- | ---: |
| Obligations / planned TC | 13 / 12 |
| Writer duration | 65594 ms |
| Reviewer duration | 43219 ms |
| Stage duration total | 108813 ms |
| Total tokens | 55198 |
| Uncached input tokens | 49970 |
| Uncached tokens per obligation | 3843.85 |
| Reviewer result | changes-required: 11 covered, 2 incorrect |

V1 semantic blocker: `prepared-dictionary-values-not-materialized` для `OBL-006` и `OBL-007`. V1 calibration lifecycle также потерял два source-backed кандидата без GAP.

## V2 Контракт

- package: `visual-assessment-medium-scope-benchmark-v2`, version `7`;
- cycle: `visual-assessment-medium-scope-benchmark-v2-20260713`;
- backend: только `exec`, без SDK fallback;
- run profile: `benchmark`;
- один fresh structured writer и один fresh semantic reviewer;
- один dispatcher invocation; retry/resume/rebind/assisted mode/sharding запрещены;
- production target должен оставаться отсутствующим;
- старый V1 draft и reviewer output используются только как comparison evidence.

## Hard Quality Gates

- 13/13 obligations получают допустимый verdict;
- `OBL-006` содержит полную иерархию `DICT-001`;
- `OBL-007` содержит все обязательные leaf-значения;
- `OBL-008` и `OBL-010` сохраняют calibration lifecycle без искусственного GAP;
- deterministic gates, evidence-access и reviewer acceptance проходят;
- FT-first baseline и production target не изменяются.

## Performance Targets

- stage duration total: менее 120 секунд;
- uncached input efficiency: менее 8000 tokens/obligation;
- validator invocations: не более 1;
- orchestration overhead: не более 15% runner wall time;
- reporting не должен влиять на quality gates.

## Stop Rule

Первый invocation завершает V2 run независимо от результата. Второй live cycle допустим только после отдельного checkpoint с одним доказанным исправлением и новой immutable authorization.
