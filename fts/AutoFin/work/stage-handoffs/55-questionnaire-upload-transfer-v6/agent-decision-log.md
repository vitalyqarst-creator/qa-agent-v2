# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `questionnaire-upload-transfer-v6` |
| stage | `agent-architecture-auditor` |
| started_from | `work/stage-handoffs/54-reference-fixture-contract-v5/prompt.reference-fixture-v5-to-next.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | Current Final parity extraction | Использовать только `FT4AutoFinFinal.*` и BSR 206-212. | Legacy PreFinal BSR mapping конфликтует с текущим Final. | `source-selection.md`; `source-parity-check.md` | high | applied |
| `DEC-002` | 2 | `scope-boundary` | V6 transfer requirement | Выбрать desktop questionnaire upload clauses BSR 206-211; QR/archive/multi-type display отложить. | Новый bounded medium scope проверяет transfer без UI/async/persistence шума. | `scope-contract.md` | high | applied |
| `DEC-003` | 3 | `test-design` | BSR 210 count rule | Проверять только `не более одного`, не утверждать replace/reject/message mechanism. | FT задаёт count oracle, но не UI mechanism. | compiler design plan | high | applied |
| `DEC-004` | 4 | `architecture` | V5 context decomposition | Guarded-удаление только нерелевантного DaData note section. | Дублирование доказано exact prompt bytes; semantic evidence не сокращается. | code/tests; `context-decomposition.v6.*` | high | applied |
| `DEC-005` | 5 | `validation` | V5 active prompt | Добавить generic reference-only no-invention regression. | Package v8 не должен выводить fixture из всего dictionary без explicit plan labels. | compiler test | high | applied |
| `DEC-006` | 6 | `authorization` | User instruction `Выполняй v6` | Live возможен только после pushed checkpoint и separate immutable binding. | Сохраняет terminal one-shot discipline. | `pre-live-stop-gate.md` | high | applied |
| `DEC-007` | 7 | `validation` | Full offline gates | Разрешить переход к checkpoint, но не к live. | 1016 tests, scoped artifact audit и architecture audit прошли; package validated. | `pre-live-test-report.v6.md` | high | applied |
| `DEC-008` | 8 | `architecture` | Reviewer initially truncates shared evidence before obligation rendering | Проверять релевантность package-note section по полному evidence до reviewer-specific truncation. | Иначе reviewer мог бы ошибочно удалить DaData notes, если ссылка на DaData находилась в obligations после точки усечения. | code; writer/reviewer regressions | high | applied |
| `DEC-009` | 9 | `authorization` | Pushed checkpoint and immutable package identities | Связать один live invocation с checkpoint `5135c023...`, package/config hashes и zero-retry contract. | Исключает незаметную подмену входа и повтор результата после terminal outcome. | `pre-live-authorization.v6.md` | high | applied |
| `DEC-010` | 10 | `live-result` | One authorized dispatcher invocation | Принять `accepted-not-promoted` как terminal success и обнулить invocation budget. | Writer/reviewer завершились успешно; exit 1 вызван намеренно отключённым promotion. | `live-result.v6.json`; `terminal-stop-gate.v6.md` | high | applied |
| `DEC-011` | 11 | `quality-boundary` | Post-canary raw-source comparison | Не считать accepted draft production-ready из-за unit-semantics и literal-text fidelity risks. | Reviewer доказал package-to-draft transfer, но не независимую source-to-package fidelity. | `post-canary-source-package-audit.v6.md` | high | applied |
| `DEC-012` | 12 | `next-priority` | V6 quality/performance result | Следующую итерацию направить на source-to-package gates, не на дальнейшее сокращение context. | Prompt bytes существенно уменьшились, а upstream oracle loss теперь является более высоким риском. | `prompt.v6-to-next.md` | high | applied |
