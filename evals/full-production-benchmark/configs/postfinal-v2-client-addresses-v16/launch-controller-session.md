# Controller-start full-production benchmark v16: «Блок “Адреса клиента”»

Выполни лично один новый независимый full-process observation benchmark для scope
`application-card-client-addresses` в пакете `fts/AutoFin`.

Эта инструкция предназначена только для отдельной Codex-задачи, которую primary
user-turn создал через app thread API по явному поручению пользователя. Граница
времени честно маркируется как `controller-job-start`, а не как прямой user request.

Используй project skill `ft-test-case-iteration` и маршрут
`production.checked_in_observation`. Неизменяемая конфигурация:

```text
evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v16/shadow-benchmark-config.json
SHA-256: ade15bffc1ee62334b682b83a4d0762d6f2f92ef6a9cf06b58bbb5dbf35174e6
```

## Root-only и clean-run ограничения

- Не вызывай `spawn_agent`, `create_thread` и любые другие средства делегации.
- Не изменяй код, инструкции, config, source/support/mockups или validators.
- Не запускай отдельную разработку, `--validate-only`, retry, fallback или resume.
- Не читай FT, старые test cases, v15, review cycles или canonical baseline.
- Не пиши тест-кейсы вручную.
- Shards выполняй последовательно; UI calibration не запускай.
- Schema-v2 executor и production wrapper должны быть вызваны ровно один раз.
- При terminal failure сохрани результат и остановись без исправлений.

Зарезервированные свежие outputs:

```text
fts/AutoFin/work/stage-handoffs/97-application-card-client-addresses-v16
fts/AutoFin/work/review-cycles/application-card-client-addresses-v16-20260720
fts/AutoFin/test-cases/4.3-application-card-client-addresses-shadow-20260720-v16.md
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

Вызови напрямую MCP tool `mcp__node_repl__js` ровно один раз. Не выполняй
`tool_search`, schema discovery, пробные REPL-команды или shell-вызов. Передай ему
единственный обязательный аргумент `code` с таким JavaScript:

```javascript
var controllerMetadataV16 = await import("./scripts/read_codex_controller_turn_metadata.mjs");
nodeRepl.write(JSON.stringify(controllerMetadataV16.readCodexControllerTurnMetadata()));
```

Helper fail-closed требует `thread_source = subagent`, непустой `turn_id` и
целочисленный `turn_started_at_unix_ms`, а также возвращает
`source = controller-job-start`. Не используй user-turn helper и не проверяй поля
вручную.

Следующим task action, без промежуточных tool calls, выполни ровно одну команду:

```powershell
python scripts/start_full_process_observation.py --repo-root . --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v16/shadow-benchmark-config.json --request-started-epoch-ms <ACTUAL_CONTROLLER_TURN_STARTED_EPOCH_MS> --codex-turn-id <ACTUAL_CONTROLLER_TURN_ID> --request-start-source controller-job-start --execute
```

Дождись terminal result. Не запускай второй wrapper и ничего не ремонтируй.

## Отчёт

Сообщи terminal status, observation directory, фазы, model tokens/attempts,
writer/reviewer verdict, production gates, promotion, shadow path/hash/TC count и
сохранность canonical/source. `source-preparation` классифицируй по фактическому
`cache_hit`; ожидается `warm-cache`, и его нельзя называть cold extraction time.
Укажи, что timing boundary — `controller-job-start`, а request-to-final
reconciliation — `not-applicable`.

Benchmark успешен только при writer, reviewer `accepted`, gates и promotion.
