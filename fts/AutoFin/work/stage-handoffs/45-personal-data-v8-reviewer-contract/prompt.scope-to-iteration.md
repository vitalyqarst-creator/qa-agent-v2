# Personal Data V9 Dictionary Projection Recovery

## Цель этапа

В новом immutable H46/V9 устранить дефект DICT projection из V8 и провести независимый reviewer recovery без повторного написания source-correct тест-кейсов.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/live-result.v8.json`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v8-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v8-20260713/prepared-input/application-card-client-personal-data-v8/stage-package.json`

## Обязательные действия

1. Не изменять и не возобновлять V8.
2. Исправить DICT active-values parser по canonical semicolon-delimited Markdown format либо передавать compiler-owned structured values без повторного Markdown parsing.
3. Добавить regression на точную compiler-produced форму `` `Мужчина`; `Женщина` `` и отрицательные cases для punctuation-only, empty и malformed values.
4. Не создавать фиктивный repair finding для `TC-ACPD-011`: draft соответствует source inventory.
5. Реализовать и проверить новый reviewer-only hash-bound rebind: новый package/cycle, runner-owned package-id migration, полный deterministic gate bundle, fresh reviewer session, без writer LLM. Если безопасный route невозможен, остановиться с доказанным blocker до live.
6. Выполнить focused tests, validate-only, artifact validator, exec dry-run, checkpoint/push и отдельную authorization.
7. Допустить ровно один V9 dispatcher; любой blocker терминален.

## Ограничения

- V8 draft — unsigned recovery input, а не requirement source.
- Не изменять `fts/AutoFin/test-cases/14-application-card-client-personal-data.md`.
- Не создавать production shadow до reviewer `accepted` и отдельного promotion decision.
- Не трогать пользовательские untracked diagnostics и соседний addresses/contacts scope.

## Ожидаемый результат

Reviewer получает exact `DICT-001 active_values = ["Мужчина", "Женщина"]` и рассматривает неизменный source-correct draft в новой fresh session. Итог — `accepted-not-promoted` либо новый точный terminal blocker.

## Gate завершения

V9 не допускается к live, пока exact dictionary projection regression и безопасный reviewer-only rebind не прошли deterministic gates. После авторизации любой blocker терминален без повтора.
