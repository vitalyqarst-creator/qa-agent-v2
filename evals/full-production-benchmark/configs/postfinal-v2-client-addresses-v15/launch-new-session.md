# Чистый full-production benchmark v15: «Блок “Адреса клиента”»

Выполни один новый независимый full-process observation benchmark для scope
`application-card-client-addresses` в пакете `fts/AutoFin`.

## Root-only execution

Весь запуск обязан лично выполнить тот primary root-agent, который получил этот
пользовательский запрос. Запрещено передавать запуск subagent-у, worker-у,
дочерней задаче или другому Codex thread.

- не вызывай `spawn_agent`, `create_thread` или иные средства делегации;
- не проси отдельного агента читать metadata или выполнять bootstrap;
- пару metadata-bootstrap должен без промежуточных task actions выполнить один и
  тот же root-agent в исходном user turn;
- `thread_source = subagent` означает ошибку маршрутизации до benchmark, а не
  benchmark attempt: wrapper не вызывай и попроси пользователя повторить запуск
  в обычной новой основной сессии.

Используй project skill `ft-test-case-iteration` и его узкий маршрут
`production.checked_in_observation`. Неизменяемая конфигурация:

```text
evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v15/shadow-benchmark-config.json
```

Ожидаемый SHA-256 конфигурации:

```text
dfb7b760919a34ff399c53b5ed571ee172b2c8aed8c081d402137eab989ef0f3
```

## Обязательные ограничения

- Это чистый benchmark, а не сессия разработки или отладки.
- Не делегируй ни metadata-preflight, ни запуск schema-v2 executor.
- Не изменяй код, инструкции, конфигурацию, source/support/mockups или validators.
- Не запускай `ft-source-locator` и отдельный root-level `ft-scope-analyzer`: schema-v2 executor сам проверяет source registry, роли, hashes, bounded context и dependency preflight.
- Не читай и не передавай writer/reviewer старые test cases, результаты v14, старые review cycles или canonical baseline.
- Не пиши тест-кейсы вручную внутри root-agent.
- Не используй retry, fallback, resume или продолжение v14.
- Не запускай `--validate-only`: конфигурация проверена до чистовой сессии.
- Semantic-design shards и возможные source-review shards выполняй в штатном последовательном режиме; параллелизм не включай.
- Не переходи к `ft-ui-automation-prep` и не пытайся открыть стенд: UI-калибровка явно отложена пользователем и не входит в этот FT-first benchmark.
- Production wrapper должен быть вызван ровно один раз через checked-in executor.
- Если обнаружен hash mismatch, занятый output path, infrastructure failure или validator failure, сохрани terminal result и останови benchmark. Ничего не исправляй и не перезапускай в этой сессии.

Зарезервированные новые output paths:

```text
fts/AutoFin/work/stage-handoffs/96-application-card-client-addresses-v15
fts/AutoFin/work/review-cycles/application-card-client-addresses-v15-20260720
fts/AutoFin/test-cases/4.3-application-card-client-addresses-shadow-20260720-v15.md
```

Текущий signed-off canonical использовать только как защищённый post-run baseline:
не читать и не передавать его writer/reviewer, не перезаписывать в ходе benchmark.
Автоматическое сравнение допустимо только после terminal sign-off отдельным
evaluator-этапом вне этой clean benchmark-сессии.

```text
fts/AutoFin/test-cases/14-application-card-client-addresses.md
SHA-256: dc51b317ab4547576f1d72674a50445dbe9e81d03c26b2ede317f924c98020af
Тест-кейсов: 109
```

## Запуск

Среда этого компьютера уже проверена и сохранена в:

```text
evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v15/environment-probe.json
```

Используй этот saved probe по `AGENTS.md`; не запускай новый probe. Если
фактический `environment_context` новой сессии отличается, остановись с
`blocked-infrastructure`, не запускай benchmark.

### Ограниченный pre-bootstrap preflight

До metadata root-agent должен выполнить только обязательную подготовку:

- объявить routing на `ft-test-case-iteration`;
- полностью прочитать корневой `AGENTS.md`, выбранный `SKILL.md`, этот файл и
  сохранённый `environment-probe.json`;
- сверить фактический `environment_context` с сохранённым probe без нового
  shell-probe.

Эти чтения разрешены до создания timer и не являются нарушением измерения: timer
будет открыт задним числом от фактического `turn_started_at_unix_ms`, поэтому их
время войдёт в `routing-preflight`. До metadata запрещены любые другие действия:
делегация, model-вызовы, source discovery, чтение FT/test cases/старых результатов,
запись файлов и `--validate-only`.

### Атомарная пара metadata-bootstrap

После ограниченного pre-bootstrap preflight лично root-agent прочитай фактические
metadata текущего Codex turn через Node REPL:

```javascript
var timingMetadataModuleV15 = await import("./scripts/read_codex_turn_metadata.mjs");
nodeRepl.write(JSON.stringify(timingMetadataModuleV15.readCodexTurnMetadata()));
```

Helper fail-closed проверяет `thread_source = user`. В возвращённом payload должны
быть настоящий `turn_id`, `turn_started_at_unix_ms`, `source = codex-request-metadata`
и `precision_ms = 1`. Не подменяй их временем запуска команды.

Следующим task action, без других tool calls между metadata и bootstrap, выполни
ровно одну shell-команду:

```powershell
python scripts/start_full_process_observation.py --repo-root . --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v15/shadow-benchmark-config.json --request-started-epoch-ms <ACTUAL_REQUEST_STARTED_EPOCH_MS> --codex-turn-id <ACTUAL_CODEX_TURN_ID> --request-start-source codex-request-metadata --execute
```

Дождись terminal result. Не запускай второй wrapper и не ремонтируй failed attempt.

## Критерии успешного результата

- route дошёл до writer;
- создан полный shadow-набор;
- независимый reviewer реально запущен и вернул `accepted`;
- production gates пройдены;
- promotion выполнен штатно;
- workflow/cycle state не исправлялся вручную;
- canonical baseline и исходные DOCX/XHTML/PDF не изменились;
- отчёт времени содержит фазы и не дублирует токены parent semantic-design/source-review и их шардов.

## Финальный отчёт

Кратко укажи:

- `benchmark_id`, observation directory и terminal status;
- полное наблюдаемое pre-final время и время каждой фазы;
- корректные input/output/reasoning tokens и число попыток по model stages;
- число semantic-design и source-review shards и их статусы;
- writer/reviewer attempts и reviewer verdict;
- результаты production gates и promotion;
- путь, SHA-256 и число тест-кейсов нового shadow-файла;
- подтверждение сохранности canonical и исходников;
- при неуспехе — точную фазу, error type, error text и пути к terminal artifacts.

Не называй benchmark успешным, если отсутствует хотя бы один из этапов writer,
reviewer acceptance, production gates или promotion. Полное пользовательское время
не выдумывай: если post-turn reconciliation ещё ожидает `task_complete`, укажи
pre-final observed window и статус reconciliation `pending`.
