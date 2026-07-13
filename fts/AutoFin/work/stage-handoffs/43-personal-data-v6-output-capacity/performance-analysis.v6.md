# V6 Performance Analysis

## Фактический расход

| metric | value |
| --- | ---: |
| dispatcher runs | 1 |
| writer sessions | 4 |
| reviewer sessions | 0 |
| wall time до terminal blocker | 305.527 s |
| сумма stage duration | 303625 ms |
| input tokens | 105980 |
| cached input tokens | 12544 |
| output tokens | 15433 |
| total tokens | 121413 |

## Оценка

Shard route решил V5 transport blocker и уложил каждый ответ в `3561–4096` output tokens. Однако четыре сессии повторно получали значительную общую часть контекста. Главная потеря этой попытки — не сам sharding, а отсутствие pre-live oracle-quality gate: четыре заранее обнаружимых finding были выявлены только после полной генерации.

Следующий экономичный маршрут — одна точечная repair-сессия для `TC-ACPD-026`, `TC-ACPD-027`, `TC-ACPD-028`, `TC-ACPD-034`, runner-owned splice и один reviewer полного набора. Повторная генерация остальных `43` TC неоправданна.

Dispatcher сохранил `performance.json` и `stage-metrics.ndjson` после terminal flush; blocked run имеет полный набор telemetry.
