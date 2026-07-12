# SDK baseline: application-card-client-personal-data

## Назначение

Baseline фиксирует стоимость SDK-цикла перед включением exec dispatcher. Источник метрик — `codex-session-map.yaml` и `runner-events.ndjson` цикла `personal-data-current-source-gap-review-20260712`.

## Метрики

| metric | value |
| --- | ---: |
| wall-clock от первого успешного scope review до terminal | `9245 s` (`154 min 05 s`) |
| backend threads started | `9` |
| scoped validator profile writes | `33` |
| writer R1 | `2979.110 s` |
| writer structure remediation | `772.016 s` |
| writer R2 | `1559.160 s` |
| executable draft TC | `47` |
| unique TC titles | `39` |
| semantic reviewer instruction context | `273.1 KiB / 290.0 KiB` |
| exact token usage | `not recorded by SDK v1 cycle` |

## Интерпретация

- Главная стоимость создавалась writer-сессиями и повторными validator gates.
- SDK baseline не содержит достоверного token ledger, поэтому exec сравнивается по фактически записанным `metrics.json` token fields.
- Новый exec canary должен использовать v2 immutable attempts, разные backend session ids, promotion dry-run и не более пяти validator reports за цикл.
