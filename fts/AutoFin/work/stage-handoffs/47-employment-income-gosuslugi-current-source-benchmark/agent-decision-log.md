# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-employment-income-gosuslugi-benchmark` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/46-personal-data-v9-dictionary-projection-recovery/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | H46 successor prompt | Проверять employment/income/Gosuslugi как независимый benchmark scope | Условная логика и интеграции проверяют переносимость prepared pipeline | H47 | medium until source rebase | applied |
| `DEC-002` | 2 | `source-boundary` | H13 vs H20 source paths | Не использовать `AutoFinPreFinal` statements/anchors downstream | H20 явно отвергает старую source family; BSR mapping изменился | scope log; extraction plan | high | applied |
| `DEC-003` | 3 | `artifact-write` | Table-heavy current-source rebase | Объявить manifest-based write до row inventory | Требование scope skill и audit validator | scope log | high | applied |
| `DEC-004` | 4 | `fallback` | Nested extraction helper import failure | Добавить deterministic repo-root bootstrap и повторить только extraction | Сбой произошёл до чтения источника; повтор не является LLM/live retry | extraction helper; TF-001 | high | applied |
| `DEC-005` | 5 | `validation` | PDF keyword pages may omit continuation pages | Сохранять по одной соседней PDF странице вокруг query match | Employment table spans page boundaries; parity requires start/end context | `scope-candidates.json` | high | applied |
| `DEC-006` | 6 | `gap` | Current FT row names/conditions and support lists diverge | Остановить employment candidate до writer | Mockup cannot resolve business alias; choosing dictionary source silently is unsafe | `candidate-assessment.md`; `stop-gate.md` | high | applied |
| `DEC-007` | 7 | `routing` | Predeclared fallback is allowed when candidate package is incomplete | Перейти к current-source BSR 32 reset-context benchmark | Parity pass, no gaps, direct comparison with historical SDK timeout | H48 | high | applied |
| `DEC-008` | 8 | `artifact-write` | Candidate extraction duplicated whole sections/tables | Сохранить только bounded matched rows и matched block ranges | Уменьшает handoff volume без изменения source semantics | extraction helper/JSON | high | applied |
