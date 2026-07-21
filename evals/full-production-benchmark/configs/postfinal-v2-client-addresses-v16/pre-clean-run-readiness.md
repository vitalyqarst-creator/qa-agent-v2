# Готовность clean benchmark v16

Статус: `ready-for-clean-run`.

Новый immutable schema-v2 запуск подготовлен для scope
`application-card-client-addresses`. Outputs v16 свободны; canonical test cases и
исходные DOCX/XHTML/PDF не изменены.

## Что исправлено после v15

- `scope_obligation_ids` теперь является runner-owned точной проекцией уже
  валидированных negative/requiredness oracle inventories. Strict semantic
  validator не ослаблен и повторно проверяет все связи.
- Добавлена регрессия на фактический дефект v15: positive obligations больше не
  наследуют `SO-NEG-*` отрицательных siblings.
- Добавлен универсальный offline replay сохранённых semantic shards с приоритетом
  raw model output, повторной нормализацией и строгим merge.
- Для controller-created задачи добавлен отдельный fail-closed metadata helper;
  launch задаёт один точный `mcp__node_repl__js` call без probe/schema discovery.
- Timing обязан показывать `warm-cache`/`cold-cache` по фактическому `cache_hit`.

## Доказательства до нового model-run

- Все 9 шардов v15 пересобраны офлайн: `44` source designs, `124` assertions,
  `106` obligations, `7` negative и `29` requiredness oracles.
- Строгий merge verified; две новые проекции устранены детерминированно и попали
  в audit receipt. Всего replay применил `170` зарегистрированных repairs.
- Deterministic materialization завершён атомарно; evidence readiness passed.
- Source assertion gate passed: `44` source rows, `124` assertions и `106`
  authenticated testable obligations.
- Дальнейший compile намеренно не имитировался: до него обязателен независимый
  source reviewer. Writer/reviewer/promotion остаются предметом clean v16 run.

Основные evidence:

- `fts/AutoFin/work/diagnostics/client-addresses-v15-semantic-replay-20260720/replay-report.json`
- `fts/AutoFin/work/diagnostics/client-addresses-v15-semantic-replay-20260720/materialization-summary.json`
- `fts/AutoFin/work/diagnostics/client-addresses-v15-semantic-replay-20260720/source-gate-validation.json`

## Локальные проверки

- Full project suite: `1537` основных тестов — passed, `1` skipped.
- Artifact validator: `393/393` passed во всех `7/7` shards.
- Дополнительные целевые наборы: `248` и `100` тестов — passed.
- `iteration.checked_in_observation`: `54.8/75.0 KiB`, headroom `20.2 KiB`.
- `iteration.full_loop`: `172.5 KiB`; сохранён отдельный строгий regression cap
  `<=175.0 KiB`, общий budget не повышался.
- Architecture audit: `63` checks, `0` findings.
- `git diff --check`: ошибок нет; имеются только существующие предупреждения
  Git о будущем LF→CRLF преобразовании.

## Новый запуск

Config:

```text
evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v16/shadow-benchmark-config.json
SHA-256: ade15bffc1ee62334b682b83a4d0762d6f2f92ef6a9cf06b58bbb5dbf35174e6
```

Свежие outputs:

```text
fts/AutoFin/work/stage-handoffs/97-application-card-client-addresses-v16
fts/AutoFin/work/review-cycles/application-card-client-addresses-v16-20260720
fts/AutoFin/test-cases/4.3-application-card-client-addresses-shadow-20260720-v16.md
```

Для прямой пользовательской сессии использовать `launch-new-session.md`; для
явно порученного автоматического controller-start — `launch-controller-session.md`.
Ожидается warm-cache source preparation: такой замер отражает повторный production
маршрут, но не первичное cold extraction time.

Готовность v16 не означает успех benchmark: он считается успешным только после
реальных writer, reviewer `accepted`, production gates и штатной promotion.
