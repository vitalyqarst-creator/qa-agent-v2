# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `prepared-fast-standard-comparison` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/23-prepared-live-canary-contract-drift/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `validation` | standard v2 validator | Не ослаблять правило `## TC-*`; исправить instruction loading | `### TC-*` запрещён каноническим runtime format, а writer не получил обязательный файл | commit `464c82b` | high | applied |
| `DEC-002` | 2 | `routing` | instruction manifest contract | Разрешать standard writer/reviewer context до LLM и блокировать near-limit | Scenario без exact selected files нарушает SDK orchestration contract | standard runner preflight | high | applied |
| `DEC-003` | 3 | `runtime-budget` | standard v3 reviewer command exhaustion | Разделить standard и prepared budgets, добавить input floor | 33 standard inputs нельзя обслужить prepared budget | commit `f66e3ef` | high | applied |
| `DEC-004` | 4 | `source-boundary` | standard v4 FINDING-006 | Автоматически передавать существующий `AGENT-NOTES.md` обоим routes | Package notes обязательны по глобальному policy | commit `14aa96a` | high | applied |
| `DEC-005` | 5 | `coverage` | standard v4 vs prepared v13 | Считать неподтверждённые dictionary provenance и internal NULL semantics gaps | Unbound fixtures не являются исполнимым покрытием | prepared v13-v15 reviewer verdicts | high | applied |
| `DEC-006` | 6 | `routing` | common-actions compiler result | Не запускать prepared LLM при `state-transition-or-navigation` | Stateful action flow требует standard workflow | common-actions routing v1 | high | applied |
| `DEC-007` | 7 | `recovery` | v3/v4 runtime interruptions | Не resume/replay старый attempt; разрешить только deterministic timeout-with-progress | Partial reviewer output не является verdict, package attempt-bound | README; prepared package format | high | applied |
| `DEC-008` | 8 | `promotion` | v15 accepted reviewer | Выполнить только promotion dry-run | Проверяет destination/hash без production mutation | v15 `promotion-dry-run.json` | high | applied |
| `DEC-009` | 9 | `context-budget` | print-form matrix block after package notes | Сохранить 32 KiB fast cap, разрешить 48 KiB только standard routing package | Mandatory context не должен ломать routing; fast prompt остаётся bounded | commit `090f0c4` | high | applied |
| `DEC-010` | 10 | `validation` | cross-scope matrix | Не исправлять compiler через пропуск orphan atoms/invalid OBL ids | Это реальные upstream contract defects, а не noise | `iteration-summary.md` | high | blocked |
