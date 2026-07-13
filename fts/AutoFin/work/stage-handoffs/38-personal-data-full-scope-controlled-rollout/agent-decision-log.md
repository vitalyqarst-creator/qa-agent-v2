# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/37-personal-data-character-restrictions-gate-v3/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `validation` | SEM-001/SEM-002 в старом draft/design mapping | Сверять точные множества TC по ledger, obligations, plan и decision table | Проверка только количества не обнаруживает stale mapping | commit `6c40fd2`; `mapping-consistency-report.md` | high | applied |
| `DEC-002` | 2 | `artifact-write` | Full package превышал evidence budget | Компактно проецировать OBL/plan evidence без повторов | Удаляется транспортное дублирование, а не requirement semantics | prepared package digest `ccdd820...6155` | high | applied |
| `DEC-003` | 3 | `routing` | Structured writer context 157 908 > 131 072 | Не дублировать полный obligations JSON в writer prompt | Source evidence и seed уже содержат writer semantics/mapping; full JSON остаётся у gates/reviewer | `validate-only-report.v1.json`; commit `1efc0d2` | high | applied |
| `DEC-004` | 4 | `execution` | Validate-only и regression gates pass | Запустить ровно один live cycle без fallback/promotion | Соответствует predeclared controlled rollout | `cycle-state.yaml`; `performance.json` | high | applied |
| `DEC-005` | 5 | `stop` | Writer structure validator: TC order not contiguous | Остановиться до reviewer и не переиспользовать cycle | Это реальный immutable-cycle blocker | `live-blocker-report.md`; `stop-gate.md` | high | applied |
| `DEC-006` | 6 | `bug-fix` | Writer сохранил порядок runner seed | Сортировать planned TC groups по numeric suffix до model call | Validator и seed теперь используют один порядок | commit `1efc0d2`; 117 tests | high | applied |
| `DEC-007` | 7 | `handoff` | Post-fix live ещё не выполнен | Требовать новый target-bound package/cycle | Нельзя задним числом объявить blocked cycle accepted | `prompt.scope-to-iteration.md` | high | applied |
