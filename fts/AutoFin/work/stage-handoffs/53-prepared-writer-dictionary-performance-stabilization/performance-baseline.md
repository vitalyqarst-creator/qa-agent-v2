# Базовый профиль производительности V3

## Вывод

V3 достиг качества 13/13, но превысил цель продолжительности на 4 532 мс. Python orchestration не является bottleneck: 1 873 мс, или 1,48% runner wall time. Оптимизируется только подготовленная writer-сессия.

## Измеренные значения

| metric | V3 value | evidence |
| --- | ---: | --- |
| writer duration | 86 969 ms | `performance.v3.json` |
| reviewer duration | 37 563 ms | `performance.v3.json` |
| total stage duration | 124 532 ms | `performance.v3.json` |
| writer input tokens | 25 286 | `attempts/writer-r1/attempt-001/metrics.json` |
| writer output tokens | 4 278 | `attempts/writer-r1/attempt-001/metrics.json` |
| writer prompt | 46 350 bytes on disk | `attempts/writer-r1/attempt-001/prompt.md` |
| raw writer Markdown | 19 690 UTF-8 bytes | `writer-result.json.draft_markdown` |
| reviewer-visible draft | 34 525 UTF-8 bytes | `stage-output/draft.md` |
| runner dictionary projection | 14 466 UTF-8 bytes | two projection marker blocks |

## Доказанное дублирование

- `TC-VAMB-005` до materialization: 6 757 bytes и 3 Markdown bullets.
- После materialization: 14 423 bytes и 51 bullet.
- Writer самостоятельно перечислил полный `DICT-001`, после чего runner добавил точную иерархию повторно.
- `source-evidence.md` занимает 28 002 bytes, из них 9 417 bytes приходятся на девять полных `DICT-*` sections.

## Ограничение вывода

Один duration sample остаётся шумным наблюдением. V4 оценивается по median трёх сопоставимых запусков; качество должно пройти во всех запусках.
