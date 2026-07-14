# Performance Analysis V8

## Итог

Prod-candidate canary уложился в оба acceptance budget:

- stage time: `95 391 ms` из `180 000 ms`;
- dispatcher wall: `100 969 ms`;
- model tokens: `49 505` из `75 000`;
- retries: `0`;
- writer/reviewer sessions: `2`, идентификаторы различаются;
- SDK fallback: не использовался.

## Разбивка

| Стадия | Duration | Input tokens | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: |
| writer | 62 141 ms | 21 867 | 3 181 | 25 048 |
| reviewer | 33 250 ms | 22 981 | 1 476 | 24 457 |
| total | 95 391 ms | 44 848 | 4 657 | 49 505 |

## Что Это Доказывает

- Небольшой FT scope можно передать writer и независимому reviewer менее чем за две минуты model-stage time.
- Уменьшенный prepared context сохранил 10/10 testable obligations и один non-blocking gap.
- Скорость генерации/review нельзя смешивать с полным regression suite: инженерные проверки заняли дольше, но не являются model generation time.

## Performance Debt

- Предшествующий независимый `scope_gap_review` занял около четырёх минут и `171 411` tokens. Это существенно дороже writer+reviewer canary и остаётся главным кандидатом на оптимизацию.
- Первичный production performance report терял `backend_session_ids`, потому что lifecycle events читались только в benchmark-profile. Агрегатор исправлен: production теперь читает только небольшой `runner-events.ndjson` для session IDs, сохраняя тяжёлые per-attempt scans выключенными.
- `reviewer.full_existing_cases`, `reviewer.semantic_traceability_test_design` и `writer.session_format_revision` имеют минимальный запас instruction budget около 15–17 KiB. Формального нарушения нет, но дальнейшее разрастание этих manifests рискованно.
