# Чистый full-production benchmark v13: «Блок “Адреса клиента”»

Выполни один новый независимый full-process observation benchmark для scope
`application-card-client-addresses` в пакете `fts/AutoFin`.

Используй project skill `ft-test-case-iteration` и его узкий маршрут
`production.checked_in_observation`. Конфигурация уже подготовлена и проверена:

```text
evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v13/shadow-benchmark-config.json
```

Ожидаемый SHA-256 конфигурации:

```text
c2632eb5dd733542c0a17f4fe14fea53414bb46e8fa5ae58817eb9fa76de5cfa
```

## Обязательные ограничения

- Это чистый benchmark, а не сессия разработки или отладки.
- Не изменяй код, инструкции, конфигурацию, source/support/mockups или validators.
- Не запускай `ft-source-locator` и отдельный root-level `ft-scope-analyzer`: schema-v2 executor сам проверяет source registry, роли, hashes, bounded context и dependency preflight.
- Не читай и не передавай writer/reviewer старые test cases, результаты v12, старые review cycles или canonical baseline.
- Не пиши тест-кейсы вручную внутри root-agent.
- Не используй retry, fallback, resume или продолжение v12.
- Не запускай `--validate-only`: конфигурация уже проверена до этой сессии.
- Semantic-design shards выполняй в штатном последовательном режиме; параллелизм не включай.
- Production wrapper должен быть вызван ровно один раз через checked-in executor.
- Если обнаружен hash mismatch, занятый output path, infrastructure failure или validator failure, сохрани terminal result и останови benchmark. Ничего не исправляй и не перезапускай в этой сессии.

Зарезервированные новые output paths:

```text
fts/AutoFin/work/stage-handoffs/93-application-card-client-addresses-v13
fts/AutoFin/work/review-cycles/application-card-client-addresses-v13-20260720
fts/AutoFin/test-cases/4.3-application-card-client-addresses-shadow-20260720-v13.md
```

Canonical baseline не перезаписывать:

```text
fts/AutoFin/test-cases/14-application-card-client-addresses.md
SHA-256: 3631d9e0a1abbb1773344bd70dadfbce67a5018bc3414fd7b138bbaed0674a28
```

## Запуск

1. Выполни обязательный environment probe по `AGENTS.md`.
2. Возьми фактические `request_started_epoch_ms` и `codex_turn_id` из metadata текущего Codex turn. Не подменяй их временем запуска команды.
3. Выполни ровно одну команду:

```powershell
python scripts/start_full_process_observation.py --repo-root . --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v13/shadow-benchmark-config.json --request-started-epoch-ms <ACTUAL_REQUEST_STARTED_EPOCH_MS> --codex-turn-id <ACTUAL_CODEX_TURN_ID> --request-start-source codex-request-metadata --execute
```

4. Дождись terminal result. Не запускай второй wrapper и не ремонтируй failed attempt.

## Критерии успешного результата

- route дошёл до writer;
- создан полный shadow-набор;
- независимый reviewer реально запущен и вернул `accepted`;
- production gates пройдены;
- promotion выполнен штатно;
- workflow/cycle state не исправлялся вручную;
- canonical baseline и исходные DOCX/XHTML/PDF не изменились;
- отчёт времени содержит фазы и не дублирует токены parent semantic-design и его шардов.

## Финальный отчёт

Кратко укажи:

- `benchmark_id`, observation directory и terminal status;
- полное наблюдаемое pre-final время и время каждой фазы;
- корректные input/output/reasoning tokens и число попыток по model stages;
- число semantic shards и их статусы;
- writer/reviewer attempts и reviewer verdict;
- результаты production gates и promotion;
- путь, SHA-256 и число тест-кейсов нового shadow-файла;
- подтверждение сохранности canonical и исходников;
- при неуспехе — точную фазу, error type, error text и пути к terminal artifacts.

Не называй benchmark успешным, если отсутствует хотя бы один из этапов writer,
reviewer acceptance, production gates или promotion. Полное пользовательское время
не выдумывай: если post-turn reconciliation ещё ожидает `task_complete`, укажи
pre-final observed window и статус reconciliation `pending`.
