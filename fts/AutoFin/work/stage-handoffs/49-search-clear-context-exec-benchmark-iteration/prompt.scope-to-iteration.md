# Search Clear Context State-Change Preflight Remediation

## Цель этапа

В новой immutable V3 iteration устранить process defect, из-за которого prepared plan допускает reset TC без доказанного changed pre-state, и только после чистого pre-live gate провести один fresh exec writer/reviewer run.

## Входные артефакты

- `fts/AutoFin/AGENT-NOTES.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/49-search-clear-context-exec-benchmark-iteration/live-result.v2.json`
- `fts/AutoFin/work/stage-handoffs/49-search-clear-context-exec-benchmark-iteration/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/49-search-clear-context-exec-benchmark-iteration/performance-analysis.v2.md`
- `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v2-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v2-20260713/attempts/reviewer-r1/attempt-001/runner-output/findings.md`

## Обязательные действия

- Добавить deterministic pre-live/state-change gate: для reset/state obligation mapped plan должен задавать state, отличный от captured initial, и observable проверку отличия до целевого действия.
- Добавить positive/negative regressions для pagination reset и row-selection reset; gate должен блокировать V2-like plan до LLM.
- Исправить upstream design rows `PD-003/PD-004`: выбирать состояние относительно captured initial, а не предполагать `page 2`/`first row` изменёнными.
- Скомпилировать новый V3 package; проверить `BSR 32` в 4/4 structured refs, standard route, oracle/context/output capacities and production boundary.
- После checkpoint push и отдельной authorization выполнить ровно один fresh writer/reviewer dispatcher; сравнить latency/tokens с V2.

## Не делать

- Не retry/resume/rebind V2 и не использовать V2 draft как requirement evidence.
- Не исправлять только Markdown draft без design-plan/process regression.
- Не добавлять неподтверждённые exact defaults или UI selection mechanics.
- Не использовать SDK fallback, assisted mode или promotion.

## Ожидаемые выходы

- Process regression и deterministic state-change preflight.
- Новый immutable V3 compiler/package/cycle evidence.
- Один fresh writer/reviewer verdict либо точный terminal blocker.
- Performance/quality comparison V2→V3 и неизменённые FT-first baselines.

## Gate завершения

Этап завершён только если V2-like incomplete setup блокируется до live, V3 package проходит pre-live gates, один authorised dispatcher завершён без fallback/retry, reviewer verdict зафиксирован, а production target и FT-first baselines не изменены.
