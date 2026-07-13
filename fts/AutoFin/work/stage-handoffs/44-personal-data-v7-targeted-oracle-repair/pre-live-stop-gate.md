# V7 Pre-Live Stop Gate

## Разрешающие условия

- V7 package digest, attempt binding и `65/65` observable-oracle preflight валидны.
- Repair plan hash-привязан к V6 draft/findings и выбирает только `TC-ACPD-026/027/028/034`.
- Одна fresh repair writer session и один fresh full-set reviewer вмещаются в context/output limits.
- Regression покрывает bad oracle, extra TC, input drift и byte-preserving splice.
- Dispatcher dry-run выбрал verified `exec` без fallback.
- FT-first baseline неизменён; production shadow и V7 attempts отсутствуют.
- Checkpoint-коммит создан и отправлен в origin.

## Обязательная остановка

После checkpoint разрешён ровно один V7 dispatcher. Любой process, contract, repair, splice, full-set gate, reviewer или production-boundary blocker завершает итерацию без retry, resume, смены transport и без изменения FT-first baseline.
