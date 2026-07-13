# Анализ V6 live blocker

## Вывод

V6 завершён со статусом `blocked-quality-gate`. Это не повтор V5 output-capacity blocker: новый shard-протокол успешно создал полный unsigned draft из четырёх независимых writer-сессий. Остановка произошла после merge, до reviewer.

## Что прошло

- Запущен ровно один dispatcher; retry/resume не выполнялись.
- Verified `codex exec` использован без fallback и с нулевым command budget.
- Созданы четыре разные backend session: `019f5a8a-bc15-7792-bd4d-f7849eada936`, `019f5a8b-cbe1-77c3-bc5f-afe14e3b6440`, `019f5a8d-0666-73a2-9d82-3b34f7f80161`, `019f5a8e-406f-7270-9754-cd13740035e9`.
- Все shard validators прошли; merge сохранил plan digest `54bd09aa80bae457f5283cebeacab13b51e3fc77d2cb926e4968a9d1b610e338`.
- Merged draft содержит `47` TC и покрывает все `65` obligations; structure, obligation и seed gates прошли.

## Что заблокировало цикл

Full-set quality gate нашёл `non-observable-expected-result` в `TC-ACPD-026`, `TC-ACPD-027`, `TC-ACPD-028`, `TC-ACPD-034`.

- В `TC-ACPD-026..028` expected result утверждает только несоответствие даты ограничению и сообщает, что UI-реакция будет откалибрована. Это не даёт исполнителю наблюдаемого pass/fail oracle.
- В `TC-ACPD-034` есть наблюдаемое утверждение о допустимости дефиса, но writer добавил в expected result ту же фразу о будущей UI-калибровке. Эта фраза не нужна для позитивной проверки и делает oracle неоднозначным.

Quality gate сработал по назначению: reviewer не должен получать draft, который нельзя однозначно исполнить.

## Корневая причина

Pre-live проверял output/context capacity, shard membership и deterministic merge, но не валидировал качество `observable_oracle` внутри prepared obligations/seed. Для трёх проверок дат package уже содержал формулировку «точная UI-реакция не определена», хотя помечал obligations как `testable`. Writer перенёс эту неоднозначность в кейсы. Для `TC-ACPD-034` runtime profile не объяснил достаточно явно, что calibration marker хранится в metadata и не должен подменять или дополнять наблюдаемый expected result.

Это архитектурный пробел между prepared package и live quality gate: известная неисполняемая форма была обнаружена после четырёх дорогих writer-сессий, хотя могла быть остановлена validate-only.

## Граница исправления

V6 immutable и не возобновляется. Следующая итерация должна:

1. Добавить pre-live oracle-quality gate для prepared obligations и seed.
2. Ввести точечный repair route: взять V6 merged draft только как unsigned draft input, сформировать hash-bound plan для четырёх TC и передать одной новой writer-сессии только соответствующие source-backed obligations.
3. Заменить только четыре секции, доказать byte-for-byte неизменность остальных `43` TC, затем повторить все full-set gates.
4. Запускать одного reviewer только после чистого full-set результата.

Generated V6 draft не является requirement evidence: источниками исправления остаются V6 prepared package, atomic obligations, source projection и coverage gaps.

## Telemetry

После terminal flush dispatcher опубликовал `performance.json` и `stage-metrics.ndjson` также для blocked outcome. Метрики четырёх writer-сессий полностью сохранены; telemetry blocker отсутствует.
