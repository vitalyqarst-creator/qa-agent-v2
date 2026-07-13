# Personal Data V9 Reviewer Rebind

## Цель этапа

Завершить новый immutable H46/V9: передать reviewer точные structured `DICT-001` values и проверить source-correct V8 draft в одной fresh reviewer session без writer LLM.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/live-result.v8.json`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v8-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/stage-handoffs/46-personal-data-v9-dictionary-projection-recovery/workflow-state.yaml`

## Обязательные действия

1. Не возобновлять V8 и не запускать writer LLM.
2. Использовать новый V9 package с compiler-owned structured dictionary values.
3. Hash-bind V8 draft, мигрировать только per-TC `package_id` и доказать сохранение семантики всех 47 TC.
4. Повторить полный deterministic gate bundle.
5. После checkpoint и отдельной authorization запустить ровно один fresh reviewer.
6. Любой blocker завершает V9 без retry/resume/fallback.

## Ограничения

- FT-first baseline не изменять.
- Production shadow не создавать.
- Не трактовать V8 draft как requirement source.
- Не трогать пользовательские diagnostics и соседний addresses/contacts scope.

## Ожидаемый результат

`accepted-not-promoted` с точным `DICT-001 active_values = ["Мужчина", "Женщина"]` либо новый доказанный terminal blocker.

## Gate завершения

До live обязательны regression, validate-only, artifact validator, exec dry-run, checkpoint/push и отдельная authorization. После live повтор запрещён.
