# Controller-start full-production benchmark v15: «Блок “Адреса клиента”»

Выполни лично один новый независимый full-process observation benchmark для scope
`application-card-client-addresses` в пакете `fts/AutoFin`.

Эта инструкция предназначена только для отдельной Codex-задачи, которую primary
user-turn создал через app thread API по явному поручению пользователя. Такой turn
честно измеряется как `controller-job-start`, а не как прямой user request.

Используй project skill `ft-test-case-iteration` и маршрут
`production.checked_in_observation`. Конфигурация:

```text
evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v15/shadow-benchmark-config.json
SHA-256: dfb7b760919a34ff399c53b5ed571ee172b2c8aed8c081d402137eab989ef0f3
```

## Root-only и clean-run ограничения

- Не вызывай `spawn_agent`, `create_thread` и любые другие средства делегации.
- Не изменяй код, инструкции, config, source/support/mockups или validators.
- Не запускай `ft-source-locator`, отдельный `ft-scope-analyzer`, разработку,
  `--validate-only`, retry, fallback или resume.
- Не читай FT, старые test cases, v14, review cycles или canonical baseline.
- Не пиши тест-кейсы вручную.
- Shards выполняй последовательно; UI calibration не запускай.
- Schema-v2 executor и production wrapper должны быть вызваны ровно один раз.
- При любом terminal failure сохрани результат и остановись без исправлений.

Зарезервированные outputs:

```text
fts/AutoFin/work/stage-handoffs/96-application-card-client-addresses-v15
fts/AutoFin/work/review-cycles/application-card-client-addresses-v15-20260720
fts/AutoFin/test-cases/4.3-application-card-client-addresses-shadow-20260720-v15.md
```

## Ограниченный pre-bootstrap preflight

До metadata выполни только следующее:

1. Объяви routing на `ft-test-case-iteration`.
2. Полностью прочитай корневой `AGENTS.md`, выбранный `SKILL.md`, этот launch-файл
   и сохранённый `environment-probe.json`.
3. Сверь доступный `environment_context` с saved probe. Новый
   `scripts/probe_environment.py` не запускай.

До metadata запрещены любые другие tool calls, model-вызовы, source discovery,
чтение FT/test cases/старых результатов и запись файлов.

## Атомарная metadata-bootstrap пара

После preflight через Node REPL прочитай raw metadata этого turn:

```javascript
nodeRepl.write(JSON.stringify(nodeRepl.requestMeta?.["x-codex-turn-metadata"]));
```

Требуй `thread_source = subagent`, непустой `turn_id` и целочисленный
`turn_started_at_unix_ms`. Это ожидаемая маркировка app-created controller job;
не вызывай fail-closed helper для прямого user turn и не меняй его код.

Следующим task action, без промежуточных tool calls, выполни ровно одну команду:

```powershell
python scripts/start_full_process_observation.py --repo-root . --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v15/shadow-benchmark-config.json --request-started-epoch-ms <ACTUAL_CONTROLLER_TURN_STARTED_EPOCH_MS> --codex-turn-id <ACTUAL_CONTROLLER_TURN_ID> --request-start-source controller-job-start --execute
```

Дождись terminal result. Не запускай второй wrapper и ничего не ремонтируй.

## Отчёт

Сообщи terminal status, observation directory, фазы, model tokens/attempts,
writer/reviewer verdict, production gates, promotion, shadow path/hash/TC count и
сохранность canonical/source. Явно укажи, что timing boundary —
`controller-job-start`, а request-to-final reconciliation — `not-applicable`.
Benchmark успешен только при writer, reviewer `accepted`, gates и promotion.
