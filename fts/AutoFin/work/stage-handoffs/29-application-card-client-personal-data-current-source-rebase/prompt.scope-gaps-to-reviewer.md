# Handoff Prompt

## Цель этапа

Провести pre-writer review gaps в режиме `scope_gap_review`. Не писать и не review-ить тест-кейсы.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/workflow-state.yaml`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/mockup-visual-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/negative-oracle-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/requiredness-oracle-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/final-bsr-evidence.json`
- `AGENT-NOTES.md`

## Обязательные действия

- Подтвердить boundaries `BSR 47–77` и исключение `BSR 78–83`.
- Проверить XHTML/DOCX/PDF anchors и historical BSR-shift risk.
- Проверить `GAP-001..003`, все `SO-NEG-*` и `SO-REQ-*`.
- Подтвердить, что non-blocking gaps допускают writer только через calibration candidates/limitations.
- Проверить два packages и downstream rules.

## Не делать

- Не писать, не исправлять и не review-ить тест-кейсы.
- Не использовать `AutoFinPreFinal.*`, historical design artifacts или canonical cases как requirement evidence.
- Не изобретать validation/integration behavior.

## Ожидаемые выходы

- Passed: `scope-gap-review.md`, verdict `passed`, готовность к current-source iteration.
- Failed: конкретные source-backed findings и возврат в scope analyzer либо `blocked-input`.

## Gate завершения

Все gaps имеют точные anchors, корректную blocking-классификацию и однозначный downstream route.
