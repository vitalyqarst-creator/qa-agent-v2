# V6 Pre-Live Authorization

## Решение

`AUTHORIZED — exactly one dispatcher`

## Выполненные условия

- Output-capacity preflight сформировал четыре непересекающихся writer shard: `12/12/12/11` TC.
- Полное объединение shard покрывает `47 TC / 65 obligations`; plan digest: `54bd09aa80bae457f5283cebeacab13b51e3fc77d2cb926e4968a9d1b610e338`.
- Writer и reviewer context/output estimates ниже настроенных limits.
- Целевой regression: `132 passed`; dispatcher dry-run выбрал verified `exec` без SDK fallback.
- V6 attempts отсутствуют; production shadow отсутствует.
- FT-first baseline SHA-256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.

## Checkpoint

- Commit: `ee4647c6757a70a24fda228ef88c1fa9651410b5`.
- Local и `origin/audit/application-card-personal-data-iteration` совпали до live-запуска.

## Stop rule

После этого checkpoint разрешён ровно один V6 dispatcher. Любой process, contract, shard, merge, full-set, reviewer или production-boundary blocker завершает итерацию без retry/resume, смены transport и изменения FT-first baseline.
