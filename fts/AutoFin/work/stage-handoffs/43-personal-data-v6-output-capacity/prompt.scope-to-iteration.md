# Следующая итерация: V7 targeted oracle repair

## Цель этапа

Устранить V6 oracle-quality blocker без повторной генерации 43 корректных TC и без изменения FT-first baseline. Использовать skill `ft-test-case-iteration`.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/live-result.v6.json`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/prepared-input/application-card-client-personal-data-v6/stage-package.json`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/prepared-input/application-card-client-personal-data-v6/atomic-obligations.json`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/attempts/writer-r1/attempt-001/runner-output/quality-gate-bundle.json`

## Обязательные действия

1. Добавить prepared oracle-quality validate-only gate, который до live блокирует testable obligation/seed, если oracle лишь повторяет входное условие или переносит наблюдаемую реакцию на будущую калибровку.
2. Разделить обычный observable oracle и `candidate-ui-calibration` evidence record: второй фиксирует точное действие, данные, видимое состояние и outcome, не выдумывая сообщение или validation mechanism.
3. Добавить bad/corrected regression fixtures для `TC-ACPD-026`, `TC-ACPD-027`, `TC-ACPD-028`, `TC-ACPD-034`.
4. Реализовать hash-bound repair plan: одна fresh read-only/zero-command writer-сессия возвращает только четыре replacement sections; runner проверяет exact IDs, order, traceability и source projection.
5. Выполнить runner-owned splice с доказательством byte-for-byte неизменности остальных 43 секций, затем все full-set gates.
6. Создать новый H44/V7 package/cycle/attempt binding, прогнать negative/corrected evals и regression, создать checkpoint.
7. После checkpoint выполнить ровно один V7 dispatcher; reviewer запускается только после чистого repair и full-set gates.

## Не делать

- Не retry/resume V6 и не запускать reviewer на V6 draft.
- Не использовать V6 draft как requirement evidence: это только unsigned repair input.
- Не менять `fts/AutoFin/test-cases/14-application-card-client-personal-data.md`.
- Не создавать `fts/AutoFin/test-cases/14-prepared-shadow-application-card-client-personal-data.md` до reviewer sign-off и отдельного promotion decision.
- Не использовать стенд, runtime DaData, V1–V5 drafts или соседние scopes как requirement evidence.
- Не трогать пользовательские untracked diagnostics и `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md`.

## Ожидаемые выходы

- Prepared oracle preflight и regression evidence.
- Immutable V7 repair plan с exact input/output hashes.
- Один repaired unsigned draft из 47 TC, где изменены только четыре разрешённые секции.
- Full-set gate bundle; при его успехе — findings одного fresh reviewer.
- Terminal V7 workflow state без автоматической promotion.

## Gate завершения

Этап завершается либо `accepted-not-promoted` после чистых full-set gates и reviewer `accepted`, либо точным новым blocker с сохранёнными artifacts и без retry. FT-first baseline и production shadow должны остаться неизменными.
