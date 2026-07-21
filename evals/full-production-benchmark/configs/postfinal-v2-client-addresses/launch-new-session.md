# Запуск независимого прогона блока «Адреса клиента»

## Готовый prompt для новой задачи Codex

```text
Выполни один независимый observational full-production benchmark scope
`application-card-client-addresses` («Блок „Адреса клиента“») по checked-in config:

evals/full-production-benchmark/configs/postfinal-v2-client-addresses.json

Это чистый FT-first прогон. Первым инструментальным действием root-turn прочитай
`turn_id` и `turn_started_at_unix_ms` из Codex request metadata строго по
`references/agent/full-process-timing-observation.md`. Вторым инструментальным
действием запусти bootstrap с `--execute`, подставив эти два значения:

.\.venv\Scripts\python.exe scripts\start_full_process_observation.py `
  --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses.json `
  --request-started-epoch-ms <turn_started_at_unix_ms> `
  --codex-turn-id <turn_id> `
  --execute

До terminal result writer/reviewer не читай старый canonical
`fts/AutoFin/test-cases/14-application-card-client-addresses.md`, другие файлы
`test-cases/`, старые `stage-handoffs/` и `review-cycles/`. Не передавай их
модельным стадиям. Не используй root-agent для ручного написания или исправления
кейсов. Не добавляй full DaData vendor reference в FT-first model context: в
этом benchmark допустимы только source registry и hash-bound inputs из config.

Выполни ровно один immutable attempt. При model/network outage, gate failure,
runner defect или source blocker сохрани фактический terminal status и артефакты;
не делай retry, fallback, code repair или ручную правку workflow-state внутри
benchmark. Для исправления потребуется отдельная development-задача и затем
новый clean run с новым output ID.

Успешный результат оставь shadow-кандидатом по пути из config. Существующий
canonical не перезаписывай и не продвигай поверх него. После signed-off разрешено
только отдельное post-run сравнение с baseline без передачи baseline writer-у или
reviewer-у. UI/DaData calibration — отдельная последующая задача после FT-first
sign-off и не входит в этот benchmark.

В финале сообщи terminal status, число кейсов, verdict reviewer, gate/promotion
status, пути timer/execution summary/shadow artifact и observed phase timing.
Полное `request-to-final` время не заявляй до `task_complete`; в следующем turn
выполни `reconcile-report` по пути timer из `bootstrap-receipt.json`.
```

## После завершения задачи

В следующем turn, когда появился `task_complete`, использовать фактический путь
`workflow-performance.json` из `bootstrap-receipt.json`:

```powershell
.\.venv\Scripts\python.exe scripts\workflow_wall_clock.py reconcile-report `
  --output <timer> `
  --json-output <run-dir>\timing-report.json `
  --markdown-output <run-dir>\timing-report.md
```

Если команда вернула `pending-task-complete` с кодом `3`, повторить её позднее;
timer при этом не изменяется.

## Преднамеренно не скрытые риски scope

- В зарегистрированных источниках нет полного перечня справочника регионов.
  Reviewer может честно зафиксировать coverage gap; значения нельзя выдумывать.
- `BSR 324` задаёт заполнение внутреннего `kladr`. Если наблюдаемый UI не даёт
  проверяемого oracle, это допустимый scope blocker для соответствующей проверки,
  а не повод исключить требование из трассировки.
- DaData-поведение вне ФТ и двух approved clarifications не является требованием
  AutoFin. Фактические UI-детали уточняются только на отдельной calibration-фазе.
