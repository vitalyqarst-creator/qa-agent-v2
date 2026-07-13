# V4 live acceptance report

## Результат

- Cycle: `personal-data-character-restrictions-shadow-v4-20260712`.
- Backend: verified `codex exec`; SDK fallback не разрешался.
- Writer и reviewer: отдельные backend session IDs.
- Terminal state: `accepted-not-promoted`.
- Draft SHA-256: `576dc046f74f982e6e01d0f26221a4ace380324b446a2323a902aa71be0ff504`.
- Production target: отсутствует до и после запуска.

## Quality

- 12/12 obligations покрыты 12 атомарными TC.
- Все названия уникальны.
- Semantic overlap: `clean`.
- Quality bundle: `pass`, 0 findings.
- Reviewer: `accepted`, 0 blocking findings.
- Шесть negative cases сохраняют `GAP-001`, `ui-calibration-required`, `candidate-ui-calibration`.
- Calibration lifecycle: 6 open / 0 resolved; regression-ready остаётся false.
- Writer/reviewer evidence access: 0 команд, 0 fallback, 0 findings.

## Performance V3 -> V4

| metric | V3 | V4 | изменение |
| --- | ---: | ---: | ---: |
| Duration | 386907 ms | 84469 ms | −78.2% |
| Total tokens | 1690384 | 56267 | −96.7% |
| Uncached input | 208136 | 52374 | −74.8% |
| Input artifact bytes | 636190 | 199691 | −68.6% |
| Primary context bytes | 531083 | 95302 | −82.1% |
| Instruction artifacts | 36 | 2 | −94.4% |
| Command executions | 74 | 0 | −100% |
| File changes by stages | 2 | 0 | −100% |

Writer: 61.000 с / 24953 input / 2921 output tokens. Reviewer: 23.469 с / 27421 input / 972 output tokens.

## Вывод

Structured standard route решил измеренную проблему скорости и контекстного overhead на character-restriction scope без потери покрытия. Результат не разрешает GAP-001 и не является regression-ready до UI evidence и повторного sign-off.
