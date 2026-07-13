# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/41-personal-data-v4-quality-remediation/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | H29 scope contract и gaps; V4r1 `blocked-input` | Не считать отсутствие стендового ID, locator-а или сохранённого ответа DaData blocker-ом FT-first writer-а | H29 разрешает writing при `GAP-001..003`; environment binding относится к UI-prep | `source-first-boundary.md` | high | applied |
| `DEC-002` | 2 | `test-design` | BSR 57–59; `AGENT-NOTES.md`; публичный Suggest FIO contract | Использовать синтетические и runtime-selected fixtures; не фиксировать динамический список/порядок подсказок | ФТ определяет trigger и observable UI effect, но не конкретную запись провайдера | `dadata-fio-contract.md`; V5 design plan | high | applied |
| `DEC-003` | 3 | `artifact-write` | V4r1 является audit evidence | Не переписывать H41/V4r1; создать отдельный H42/V5 snapshot | Сохраняется проверяемая история причины прежней блокировки | H42; V5 cycle | high | applied |
| `DEC-004` | 4 | `validation` | Compiler принимал environment-bound fixture и не переносил его определение в package | Блокировать явные environment-bound contracts, требовать inline definition и включать definition в source evidence | Writer должен получать тот же fixture contract, который прошёл compiler gate | `prepared_compiler.py`; regression tests | high | applied |
| `DEC-005` | 5 | `validation` | V4r1 state ссылался на отсутствующий draft | Заполнять `draft_test_cases` только после materialization | State не должен содержать dangling artifact alias | `codex_exec_review_cycle_runner.py`; regression test | high | applied |
| `DEC-006` | 6 | `routing` | 128 tests, compile, digest, seed, context и exec dry-run прошли | Разрешить ровно один V5 live dispatcher после checkpoint commit | Оставшийся риск проверяется новой writer/reviewer сессией; retry запрещён | `pre-live-authorization.md` | risk:live semantic blocker | applied |
