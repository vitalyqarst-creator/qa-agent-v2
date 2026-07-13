# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/40-personal-data-v3-reviewer-recovery/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | Handoff 40 routes to V4 quality remediation | Continue `ft-test-case-iteration` | Scope/source are stable; failure is inside iteration design and enforcement | handoff 41 | high | applied |
| `DEC-002` | 2 | `architecture` | V3 passed deterministic gates but reviewer rejected execution detail | Add compiler and runner enforcement | Compiler should stop bad prepared inputs; runner must independently verify generated draft | code/tests/eval fixture | high | applied |
| `DEC-003` | 3 | `immutability` | Handoff 38 and V1-V3 are accepted audit evidence | Create new handoff 41 inputs and V4 cycle | Editing old snapshots would destroy provenance | contamination hashes | high | applied |
| `DEC-004` | 4 | `oracle-boundary` | Exact requiredness reaction and backend attribution remain gaps | Use concrete save action plus evidence-capture/calibration contracts without preselecting messages or mechanisms | Intended to make candidates executable while preserving `GAP-002/003`, but fixture content remained unresolved | remediated compiler inputs | medium | rejected-by-live |
| `DEC-005` | 5 | `compiler-mapping` | V4 compiled `OBL-028` with both TC-013 and TC-025 intents because both share ATOM-021 | Select viable plan rows by the obligation's exact planned TC token before fixture/action/intent processing | One atom may legitimately have several independent TC; mixing their actions makes each draft case non-atomic | compiler patch and focused test | high | applied |
| `DEC-006` | 6 | `immutability` | First built V4 package predates DEC-005 | Quarantine it and compile V4r1 instead of overwriting | Prepared artifacts are audit evidence even before live | integrity warning; V4r1 package | high | applied |
| `DEC-007` | 7 | `execution` | Eval, 124 tests, package/hash/seed, contexts, dispatcher and boundaries pass | Authorize exactly one V4r1 dispatcher live after checkpoint | Every pre-live condition is met; runner retains exact reviewer context enforcement | pre-live authorization | high | applied |
| `DEC-008` | 8 | `stop-gate` | Единственный V4r1 writer вернул `blocked-input` по двум нераскрытым fixtures | Остановить cycle без retry и reviewer | Это внешний execution input; продолжение потребовало бы выдумать стендовые данные | cycle state; writer result; stop gate | high | applied |
| `DEC-009` | 9 | `root-cause` | Compiler принял непустой fixture-ID, но не разрешил его в catalog | Следующая prevention-итерация должна проверять fixture catalog до package write/live | Один идентификатор не доказывает воспроизводимость; live потратил 38 071 input tokens на локально проверяемый blocker | blocker analysis; eval candidate | high | applied |
| `DEC-010` | 10 | `routing` | Для save и DaData нужны актуальные безопасные стендовые данные | Маршрутизировать в новый H42/V5 после регистрации fixtures; V4/V4r1 оставить immutable | Старый catalog generic/conditional и не подтверждает текущую доступность | fixture request; next-stage prompt | high | applied |
