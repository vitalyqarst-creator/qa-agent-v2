# Запуск третьего immutable address benchmark

## Готовый prompt для новой задачи Codex

```text
Выполни один независимый observational full-production benchmark scope
`application-card-client-addresses` по checked-in config:

evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v3.json

Это новый immutable attempt после terminal-failed v2. Runner уже содержит
локально проверенные deterministic repairs только для доказуемого XHTML/PDF
transport duplication и распределения clarification codes по owning assertions.
Ready semantic schema также требует минимальную OBL-ёмкость по included rows;
строгий validator по-прежнему требует точного совпадения всех OBL bindings.

Весь раздел 5 «Ограничения по типам данных» и следующий общий default NULL
являются out-of-project: сохрани их строки только как not-applicable evidence,
не создавай для них testable assertions/ATOM/OBL/TC и не используй их как
context dependencies целевых полей. Локальные BSR 115-161 остаются в scope.

Первым инструментальным действием root-turn прочитай `turn_id` и
`turn_started_at_unix_ms` из Codex request metadata по
`references/agent/full-process-timing-observation.md`. Вторым инструментальным
действием запусти:

.\.venv\Scripts\python.exe scripts\start_full_process_observation.py `
  --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v3.json `
  --request-started-epoch-ms <turn_started_at_unix_ms> `
  --codex-turn-id <turn_id> `
  --execute

До terminal result writer/reviewer не читай старый canonical, другие test-cases,
старые handoff/review-cycle и model outputs, включая v1/v2 address benchmark.
Не используй root-agent для ручного написания кейсов. Не добавляй полный DaData
vendor reference в FT-first model context.

Выполни ровно один attempt. При любом terminal failure сохрани фактический статус
без retry, fallback, code repair и ручной правки workflow-state. Успешный результат
оставь shadow-кандидатом по пути из config; canonical не перезаписывай.

В финале сообщи terminal status, число кейсов, reviewer verdict, gate/promotion
status и пути timer/execution summary/shadow artifact. Полное request-to-final
время не заявляй до последующего reconcile-report.
```

Первый и второй неуспешные config/output ID повторно не использовать.
