# Performance Analysis V5

## Итог

V5 устранил semantic blocker: exact OBL-013 fixture сохранена, deterministic gates прошли, reviewer принял 13/13 obligations без findings. Общая длительность ниже 120 секунд, но один canary не доказывает устойчивое ускорение, а uncached token efficiency остаётся хуже accepted V3.

## Сравнение

| metric | V3 accepted | V4 rejected canary | V5 accepted canary | V5 vs V3 | V5 vs V4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| writer duration | 86 969 ms | 63 547 ms | 72 687 ms | -16,42% | +14,38% |
| reviewer duration | 37 563 ms | 38 344 ms | 29 204 ms | -22,25% | -23,84% |
| total stage duration | 124 532 ms | 101 891 ms | 101 891 ms | -18,18% | 0% |
| total tokens | 59 451 | 57 643 | 57 771 | -2,83% | +0,22% |
| uncached tokens / OBL | 3 110,31 | 4 045,92 | 4 079,08 | +31,15% | +0,82% |
| orchestration overhead | 1,48% | 4,15% | 4,49% | +3,01 pp | +0,34 pp |
| reviewer result | 13/13 | 12/13 + 1 incorrect | 13/13 | equal quality | blocker removed |

## Что доказано

- Package v8 переносит bounded exact fixture без возврата exhaustive payload writer-у.
- OBL-013 прошёл deterministic gate и независимый reviewer с двумя точными значениями одной группы.
- OBL-006/OBL-007 сохранили 47 hierarchy и 39 leaf entries; writer ownership gate прошёл.
- Один writer и один reviewer выполнены в отдельных exec sessions без команд, file changes и fallback.
- FT-first baseline не изменён; accepted draft остался неповышенным benchmark artifact.

## Что не доказано

- Нет median нескольких quality-passing V5 runs; устойчивую latency оценить нельзя.
- Переносимость на новый реальный scope пока не проверена.
- Token efficiency не улучшилась: 4 079,08 uncached tokens/OBL выше V3 на 31,15% и выше ранее принятого лимита 3 421,34.

## Вывод

Архитектурная корректность V5 подтверждена. Следующая итерация должна проверять transfer на новом scope и сокращать повторный reviewer/context payload по измерениям; дальнейшая настройка только на этом benchmark рискует переобучить процесс под fixture.
