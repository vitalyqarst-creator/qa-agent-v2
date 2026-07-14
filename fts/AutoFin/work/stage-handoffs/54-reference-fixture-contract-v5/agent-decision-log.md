# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `visual-assessment-medium-scope-benchmark-v5` |
| stage | `agent-architecture-auditor` |
| started_from | `work/stage-handoffs/53-prepared-writer-dictionary-performance-stabilization/prompt.v4-canary-to-reference-fixture-contract-v5.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `architecture` | V4 OBL-013 failure | Добавить first-class `fixture_values` только в package v8 | Prompt-only exact fixture transport оказался ненадёжным; v7 нельзя менять задним числом | `architecture-decision.md` | high | applied |
| `DEC-002` | 2 | `test-design` | Exhaustive ownership V4 уже работает | Не использовать `required_values` для reference-only | Иначе bounded fixture ошибочно станет exhaustive contract | code and format references | high | applied |
| `DEC-003` | 3 | `validation` | Exact plan values и dictionary hierarchy | Compiler выбирает только явно названные group/leaf labels | Не допускает выдумывание и случайный перенос всего словаря | compiler regression | high | applied |
| `DEC-004` | 4 | `validation` | Writer может обобщить fixture | Runner canonicalizes block и gate проверяет exact projection | Качество не зависит от соблюдения prose instruction | gate/runner regressions | high | applied |
| `DEC-005` | 5 | `validation` | Actual rejected V4 draft | Использовать его только как immutable negative replay | Ручная правка скрыла бы реальную регрессию | `offline-replay.v5.json` | high | applied |
| `DEC-006` | 6 | `authorization` | User instruction `Продолжай` | Live разрешать только после pushed offline checkpoint и отдельной hash binding | Сохраняет terminal stop discipline | `pre-live-stop-gate.md` | high | applied |
| `DEC-007` | 7 | `authorization` | Pushed offline checkpoint `25ba4a4` | Разрешить ровно один V5 dispatcher invocation | Одного canary достаточно для проверки semantic blocker; retry исказил бы результат | `pre-live-authorization.v5.md` | high | applied |
