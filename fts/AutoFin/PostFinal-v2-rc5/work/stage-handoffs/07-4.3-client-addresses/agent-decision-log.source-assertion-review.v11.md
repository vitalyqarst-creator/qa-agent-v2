# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin/PostFinal-v2-rc5` |
| scope_slug | `4-3-client-addresses` |
| stage | `ft-test-case-reviewer` |
| started_from | `fts/AutoFin/PostFinal-v2-rc5/work/stage-handoffs/07-4.3-client-addresses/source-assertions.json` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `validation` | receipt v6 | Зафиксировать decision `accepted` | Независимый reviewer проверил `62` assertions; incorrect: `0` | `fts/AutoFin/PostFinal-v2-rc5/work/stage-handoffs/07-4.3-client-addresses/source-assertion-review.v11.json` | `high` | `applied` |
| `DEC-002` | 2 | `routing` | exact-digest source review | Передать workflow в `ft-test-case-iteration` | Маршрут определяется только валидированным receipt decision | `workflow-state.yaml` | `high` | `applied` |
