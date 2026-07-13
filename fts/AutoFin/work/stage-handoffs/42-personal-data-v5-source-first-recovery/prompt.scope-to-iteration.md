# Продолжение Personal Data V5

## Goal

Продолжить `ft-test-case-iteration` для scope `application-card-client-personal-data`: после checkpoint выполнить ровно один verified-exec V5 writer/reviewer cycle и получить unsigned reviewed draft без изменения FT-first baseline.

## Inputs

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-v5-source-first-recovery/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-v5-source-first-recovery/source-first-boundary.md`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-v5-source-first-recovery/dadata-fio-contract.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v5-20260713/prepared-input/application-card-client-personal-data-v5/stage-package.json`

## Guardrails

- Использовать только immutable package `application-card-client-personal-data-v5`.
- После checkpoint разрешён ровно один dispatcher; на любом blocker остановиться без retry.
- Не включать SDK fallback, promotion или overwrite.
- Не изменять V4r1, `test-cases/14-application-card-client-personal-data.md`, production shadow и пользовательские untracked-файлы.
- Не использовать стендовые ID, локаторы и сохранённые ответы интеграции как условие написания FT-first draft.
