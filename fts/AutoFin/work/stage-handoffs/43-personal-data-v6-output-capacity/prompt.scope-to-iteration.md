# Personal Data V6 controlled live iteration

## Goal

Продолжить `ft-test-case-iteration` для `application-card-client-personal-data` только из checkpoint-коммита H43.

## Inputs

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/pre-live-stop-gate.md`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/output-capacity-preflight.v6.json`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/dispatcher-config.v6.json`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/prepared-input/application-card-client-personal-data-v6/stage-package.json`

## Action

После проверки checkpoint SHA, package digest, отсутствия V6 attempts и production shadow запустить ровно один dispatcher с config V6. Runner обязан выполнить четыре fresh-session writer shard-а, deterministic merge, full-set gates и один fresh reviewer. При любом blocker остановиться без retry/resume/смены transport.

## Guardrails

- Не изменять FT-first baseline.
- Не создавать production shadow до reviewer `accepted` и controlled promotion decision; текущий config promotion не включает.
- Не использовать V1–V5 drafts, production cases, стенд или UI evidence как requirement evidence.
- Не обращаться к SDK fallback.

## Terminal Result

- успех: `accepted-not-promoted`, полный draft `47 TC`, reviewer accepted, production shadow отсутствует;
- допустимая остановка: точный live blocker с сохранёнными immutable attempt artifacts и без retry.
