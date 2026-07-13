# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `stage-handoffs/45-personal-data-v8-reviewer-contract/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | H45 stop gate | Создать новый H46/V9, не изменяя V8 | V8 terminal и не допускает retry/resume | `workflow-state.yaml` | high | applied |
| `DEC-002` | 2 | `validation` | V8 dictionary projection blocker | Перенести active values в compiler-owned JSON projection | Повторный Markdown parsing превратил значения в punctuation-only payload | compiler/runner regressions | high | applied |
| `DEC-003` | 3 | `routing` | Source-correct V8 draft | Использовать reviewer-only hash-bound rebind без writer LLM | Реального TC defect нет; повтор writer создаст лишний риск и расход | V9 runner/config | high | applied |
| `DEC-004` | 4 | `artifact-write` | Generated V9 package/cycle | Писать generated outputs только canonical compiler/runner | Сохраняет digest/manifest fidelity | `prepared-input/`; live cycle | high | applied |
| `DEC-005` | 5 | `validation` | First compile exceeded evidence budget by 134 bytes | Удалить из structured projection только неиспользуемые reviewer metadata fields, лимит не повышать | Exact active values и canonical inventory сохранены | compiler; `package-preflight-report.v9.json` | high | applied |
| `DEC-006` | 6 | `routing` | Все pre-live gates прошли | Остановиться до checkpoint/push и отдельной authorization | Live boundary задан H45/V9 prompt | `pre-live-stop-gate.md` | high | applied |
| `DEC-007` | 7 | `authorization` | Checkpoint `7b0743f5` совпал с origin | Разрешить ровно один reviewer-only V9 dispatcher после отдельного push | Writer не нужен; все deterministic и production-boundary gates пройдены | `pre-live-authorization.md` | high | applied |
| `DEC-008` | 8 | `terminal-state` | Reviewer accepted 65/65 obligations | Закрыть V9 как `accepted-not-promoted` без повторов | Promotion была явно отключена; acceptance является требуемым V9 результатом | `live-result.v9.json`; `stop-gate.md` | high | applied |
| `DEC-009` | 9 | `routing` | Reviewer-only recovery успешен | Следующим проверять другой scope обычным writer-reviewer маршрутом | Повтор personal-data не докажет переносимость оптимизации; rebind не заменяет writer | `prompt.iteration-to-scope-rebase.md` | high | applied |
