# Performance Analysis V4

## Итог

Общий V4 verdict не вычисляется: canary r1 не прошёл quality gate, поэтому r2/r3 корректно не запускались. Единственное наблюдение показывает ускорение writer и устранение exhaustive dictionary duplication, но принимать его как успешную оптимизацию нельзя из-за ошибки исполняемости одного кейса.

## Наблюдение r1

| metric | V3 accepted | V4 r1 | delta | gate |
| --- | ---: | ---: | ---: | --- |
| writer duration | 86 969 ms | 63 547 ms | -23 422 ms (-26,93%) | observation pass |
| reviewer duration | 37 563 ms | 38 344 ms | +781 ms (+2,08%) | observation |
| total stage duration | 124 532 ms | 101 891 ms | -22 641 ms (-18,18%) | single-run target pass |
| total tokens | 59 451 | 57 643 | -1 808 (-3,04%) | observation |
| uncached tokens / OBL | 3 110,31 | 4 045,92 | +935,61 (+30,08%) | fail; limit 3 421,34 |
| orchestration overhead | 1,48% | 4,15% | +2,67 pp | pass, <=15% |
| reviewer result | 13/13 | 12/13 + 1 incorrect | regression | quality fail |

## Что доказано

- Raw writer Markdown уменьшился с 19 690 до 13 210 bytes.
- Runner materialized exhaustive dictionaries ровно один раз: 47 hierarchy entries для OBL-006 и 39 leaf entries для OBL-007.
- Writer ownership gate прошёл: модель не перечислила exhaustive payload самостоятельно.
- OBL-008 и OBL-010 сохранили calibration lifecycle.
- Один вызов writer и один вызов reviewer выполнены через `exec`, без команд, file changes и fallback.

## Что не доказано

- Median performance отсутствует: один failed canary не заменяет три quality-passing runs.
- Устойчивое ускорение не подтверждено.
- Token efficiency ухудшилась и уже на единственном sample вышла за допустимый предел.

## Причина остановки

В TC-VAMB-012 writer заменил две точные fixture values из OBL-013/test_intent на фразу «два обычных значения». Точные значения присутствовали в writer prompt, поэтому это не source-loss и не побочный эффект удаления полного exhaustive payload. Это model adherence variance, которую текущий deterministic gate не обнаруживает до reviewer.
