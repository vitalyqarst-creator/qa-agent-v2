# Отчёт о блокировке prepared reviewer live canary v3

## Итог

- Статус цикла: `blocked-process-exit`.
- Writer session: `019f4bf7-411d-7753-bffd-76326b0e2878`.
- Reviewer session: `019f4bf8-cd93-7052-bc25-83da5e38b0e8`.
- Writer и reviewer запускались в отдельных ephemeral-сессиях.
- Promotion был выключен; production-файл `test-cases/3-iteration-smoke-widget-selection-types.md` не создан.
- Существующие production test cases не изменялись.

## Подтверждённые улучшения

| показатель | результат |
| --- | ---: |
| prepared package | `15202 bytes`, `4` файла |
| prepared reviewer prompt | `25086 bytes`, меньше лимита `65536` |
| prepared reviewer instruction context | `69.1 KiB`, ранее `133.7 KiB` |
| writer first output | `0.328 s` |
| writer first meaningful artifact | `80.750 s` при deadline `90 s` |
| writer duration | `101.234 s` |
| writer commands | `3 / 8` |
| writer gates | structure, seed, obligation и evidence-access `passed` |
| reviewer duration до API failure | `4.375 s` |
| reviewer commands | `0 / 1` |
| reviewer evidence-access gate | `passed`, запрещённых чтений нет |

Inline reviewer handoff был сформирован корректно: runtime profile, selected evidence, atomic obligations, deterministic gate summaries, immutable draft и SHA-256 находились непосредственно в prompt. Reviewer не читал skill, references, package, source или production test cases.

## Реальный blocker

`codex exec --output-schema` завершился с HTTP `400`, `invalid_json_schema`, до semantic работы reviewer-а:

> In context=('properties', 'obligation_reviews', 'items', 'properties', 'test_case_ids'), 'uniqueItems' is not permitted.

Transport response-format schema не поддерживает JSON Schema keyword `uniqueItems`. Такое keyword также использовано в массивах `atom_ids` и `test_case_ids` findings. Это capability incompatibility, а не auth, timeout, command-budget, prompt-size, sandbox или semantic reviewer failure.

Runner уже проверяет дубли атомов, test-case ids и finding ids после получения результата. Поэтому `uniqueItems` не требуется для integrity: его можно убрать из transport schema, сохранив детерминированную duplicate validation в runner.

## Решение об остановке

Benchmark из трёх прогонов не выполнялся: live canary обнаружил реальный API/schema blocker, и повторные запуски с тем же schema гарантированно завершились бы тем же `400`.

Следующая узкая итерация должна:

1. удалить `uniqueItems` из response-format schema, не ослабляя runner-side duplicate checks;
2. добавить regression test на transport-compatible subset JSON Schema;
3. добавить дешёвый schema capability probe до запуска полного writer stage либо закешированный verified schema fixture;
4. повторить canary в новой immutable cycle-папке;
5. запускать benchmark только после валидного terminal reviewer contract.
