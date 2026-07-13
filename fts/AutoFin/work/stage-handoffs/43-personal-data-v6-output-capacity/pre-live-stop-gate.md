# V6 Pre-Live Stop Gate

## Разрешающие условия

- V6 package digest и attempt binding валидны.
- Output-capacity bad/corrected evals прошли.
- Shard union равен `47 TC / 65 obligations`, shards не пересекаются.
- Все writer/reviewer context и output estimates ниже заданных limits.
- Целевые `132` compiler/runner tests прошли.
- Dispatcher dry-run выбрал verified `exec` без fallback.
- FT-first baseline и V5 immutable evidence не изменены; production shadow отсутствует.
- Checkpoint-коммит создан.

## Обязательная остановка

После checkpoint разрешён ровно один V6 dispatcher. Любой process, contract, shard, merge, full-set gate, reviewer или production-boundary blocker завершает итерацию без retry, resume, смены transport и без изменения FT-first baseline.
