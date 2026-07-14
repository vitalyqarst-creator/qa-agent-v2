# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `questionnaire-upload-transfer-v8-prod-candidate` |
| stage | `ft-test-case-iteration` |
| started_from | `workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DL-001` | 1 | `routing` | `scope-gap-review.md` | Передать scope в prepared writer/reviewer iteration | Независимый reviewer подтвердил fidelity и non-blocking gap | `prompt.scope-to-iteration.md` | high | applied |
| `DL-002` | 2 | `test-design` | `unsupported_dimensions` package compiler | Использовать `standard-required` structured writer | File upload, boundaries, negative oracle и visibility не являются fast-eligible | `stage-package.json`; `dispatcher-config.v8.json` | high | applied |
| `DL-003` | 3 | `gap` | `GAP-QUT-001` | Не создавать exact-byte TC | ФТ не задаёт decimal/binary convention для 40 МБ | candidate и reviewer gate | risk: residual boundary ambiguity | applied |
| `DL-004` | 4 | `validation` | Повторная компиляция | Считать package immutable и current | `--reuse-if-current` вернул `reused` при том же attempt binding | `stage-package.json` SHA-256 | high | applied |
| `DL-005` | 5 | `routing` | Prod-candidate terminal gate | Разрешить один exec-only canary без retry и promotion | Так измеряются переносимость, качество и скорость без изменения baseline | `dispatcher-config.v8.json` | risk: live blocker stops iteration | applied |
| `DL-006` | 6 | `fallback` | Runner validate-only: `writer_command_budget must be >= 1` | Установить минимально допустимый budget `1` | Это configuration prerequisite runner; фактическое использование команд остаётся отдельным gate | `dispatcher-config.v8.json` | low | applied |
| `DL-007` | 7 | `validation` | Live terminal result | Принять canary как `accepted-not-promoted` | Separate exec sessions, reviewer accepted, deterministic gates passed | `live-result.v8.json` | high | applied |
| `DL-008` | 8 | `quality` | Manual inspection of immutable draft | Признать candidate quality gate passed без правок | Unique titles, 10/10 obligations, literal/gap fidelity and atomicity confirmed | `manual-quality-gate.v8.md` | high | applied |
| `DL-009` | 9 | `artifact-write` | Production performance report lacked session IDs | Всегда читать small runner lifecycle ledger для audit IDs | Session identity нужна в production; expensive per-attempt scans остаются benchmark-only | `review_cycle_backend_dispatcher.py`; test | high | applied |
| `DL-010` | 10 | `validation` | Regression and architecture gates | Оставить candidate promotion-ready | 1021 tests passed; architecture 0 findings | `architecture-audit.v8.md`; `terminal-stop-gate.v8.md` | high | applied |
| `DL-011` | 11 | `routing` | Explicit approval gate | Остановиться до production write | План требует отдельного человеческого разрешения; target отсутствует | `terminal-stop-gate.v8.md` | risk: pending approval | applied |
