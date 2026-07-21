# Чистый full-production benchmark v16: «Блок “Адреса клиента”»

Выполни лично один новый независимый full-process observation benchmark для scope
`application-card-client-addresses` в пакете `fts/AutoFin`.

## Root-only execution

Запуск обязан выполнить primary root-agent исходного пользовательского turn.
Запрещены делегация, `spawn_agent`, `create_thread`, retry, fallback, resume,
ручное написание тест-кейсов и исправления внутри benchmark.

Используй project skill `ft-test-case-iteration` и маршрут
`production.checked_in_observation`. Неизменяемая конфигурация:

```text
evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v16/shadow-benchmark-config.json
SHA-256: ade15bffc1ee62334b682b83a4d0762d6f2f92ef6a9cf06b58bbb5dbf35174e6
```

Не изменяй код, инструкции, config, source/support/mockups или validators. Не читай
и не передавай writer/reviewer старые test cases, v15, review cycles или canonical
baseline. Shards выполняй последовательно, UI calibration не запускай. Schema-v2
executor и production wrapper вызываются ровно один раз. Любой terminal failure
сохраняется без ремонта и повторного запуска.

Зарезервированные свежие outputs:

```text
fts/AutoFin/work/stage-handoffs/97-application-card-client-addresses-v16
fts/AutoFin/work/review-cycles/application-card-client-addresses-v16-20260720
fts/AutoFin/test-cases/4.3-application-card-client-addresses-shadow-20260720-v16.md
```

## Ограниченный pre-bootstrap preflight

До metadata только объяви routing, полностью прочитай корневой `AGENTS.md`,
выбранный `SKILL.md`, этот файл и сохранённый `environment-probe.json`, затем
сверь его с фактическим `environment_context`. Новый environment probe не запускай.
До metadata запрещены другие tool calls, source discovery, чтение FT/test cases,
model-вызовы и запись файлов.

## Атомарная metadata-bootstrap пара

Вызови напрямую MCP tool `mcp__node_repl__js` ровно один раз, без `tool_search`,
schema discovery и пробных команд. Аргумент `code`:

```javascript
var userMetadataV16 = await import("./scripts/read_codex_turn_metadata.mjs");
nodeRepl.write(JSON.stringify(userMetadataV16.readCodexTurnMetadata()));
```

Helper требует `thread_source = user`, настоящий `turn_id`, millisecond timestamp,
`source = codex-request-metadata` и `precision_ms = 1`.

Следующим task action, без промежуточных tool calls, выполни ровно одну команду:

```powershell
python scripts/start_full_process_observation.py --repo-root . --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v16/shadow-benchmark-config.json --request-started-epoch-ms <ACTUAL_REQUEST_STARTED_EPOCH_MS> --codex-turn-id <ACTUAL_CODEX_TURN_ID> --request-start-source codex-request-metadata --execute
```

Дождись terminal result. Не запускай второй wrapper и ничего не ремонтируй.

## Критерии и отчёт

Успех требует writer, полного shadow-набора, reviewer `accepted`, production gates
и штатной promotion без ручного исправления workflow state. Canonical и исходные
DOCX/XHTML/PDF должны остаться неизменными.

В отчёте укажи terminal status, observation directory, все фазы, model
tokens/attempts, writer/reviewer verdict, gates, promotion, shadow path/hash/TC
count и сохранность protected inputs. `source-preparation` классифицируй по
фактическому `cache_hit`; ожидается `warm-cache`, и его нельзя выдавать за cold
extraction time. Если `task_complete` ещё не reconciled, сообщи только pre-final
observed window и `pending`.
