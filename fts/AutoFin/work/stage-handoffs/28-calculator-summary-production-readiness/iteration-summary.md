# Итог первого production испытания calculator-summary

## Результат

- Prepared pipeline теперь различает semantic acceptance и production readiness.
- Terminal v10 сохранён как `blocked-timeout`; replay не выполнялся.
- v11 получил `accepted-promotion-ready-not-promoted`, но ручной gate обнаружил drift Metadata и Priority.
- Единственный correction round v12 исправил drift и завершился `accepted-promotion-ready-not-promoted` без findings.
- Production обновлён только после byte-equivalence проверки с принятым v12 SHA.
- Итоговый production SHA-256: `bb8b90d9b5e80482a486aa186247aae6031ea2ab21cdffce66f0598b3440b571`.

## Live sessions

| stage | backend_session_id | duration |
| --- | --- | ---: |
| v12 writer | `019f5407-a582-7b20-851d-4dc6c1e5f5cf` | `261.766 s` |
| v12 reviewer | `019f540b-a577-7913-bdce-1dfc140062d4` | `117.719 s` |
| total | separate sessions | `379.485 s` (`6 мин 19.485 с`) |

## Production content

- `TC-ACCS-001..005` покрывают пять testable obligations.
- `BSR 43–46` сохранены.
- `GAP-001` сохранён как non-blocking для полного состава и exact mapping prefill.
- `WP-01`, `test_design_dir`, canonical sections и priorities прошли machine gate.

## Validation

- Promotion-readiness: 0 findings.
- Reviewer: accepted, 0 findings.
- Production validator: 37 checks, 0 errors, 0 warnings, 0 info.
- Candidate/production byte equivalence: pass.
- Full regression: 511 tests passed (`1` skipped), validator shards `7/7` passed.
- Agent-layer regression: 400 tests passed (`1` skipped), validator shards `7/7` passed.
- Architecture audit: 59 checks, 0 findings.

## Reviewer Sign-off Self-check

| check | result |
| --- | --- |
| Traceability к BSR 43–46, OBL-001..005 и ATOM-001..005 | `pass` |
| Каноническая структура и Metadata | `pass` |
| Atomicity и grouping пяти testable obligations | `pass` |
| Нумерация `TC-ACCS-001..005` | `pass` |
| Test-design consistency | `pass` |
| Blocking findings | `0` |
| Traceability gaps | `GAP-001` сохранён как non-blocking accepted risk |

## Follow-up outside this scope

Package-wide personal-data inventory всё ещё содержит старое cross-scope присвоение BSR 43–46. Это отдельная source-rebase задача и не меняет signed-off calculator-summary baseline.

## Переносимость

Handoff содержит tracked-копии минимальных доказательств v12: итоговое состояние, reviewer findings и validator result. Следующий этап воспроизводим после чистого clone с включённой поддержкой длинных путей; полные runtime-логи и diagnostics намеренно не публикуются.

На Windows репозиторий содержит исторические snapshot-пути длиннее стандартного checkout-лимита. Проверенная команда клонирования:

```powershell
git -c core.longpaths=true clone https://github.com/vitalyqarst-creator/qa-agent-v2.git C:\src\qa-agent-v2
```

Короткий каталог `C:\src\qa-agent-v2` рекомендуется намеренно. Свежий clone с `core.longpaths=true` прошёл обе строгие проверки без локальных ignored runtime-файлов.
