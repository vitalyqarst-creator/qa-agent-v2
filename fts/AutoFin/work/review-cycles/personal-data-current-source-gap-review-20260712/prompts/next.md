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

- Проверить boundaries `BSR 47–77`, XHTML/DOCX/PDF anchors и исключение recognition `BSR 78–83`.
- Проверить historical source/BSR shift и запрет использовать historical artifacts как requirement source.
- Проверить `GAP-001..003`, `SO-NEG-001..015`, `SO-REQ-001..005` и их downstream route.
- Проверить, что candidates создаются writer-ом и не требуют invented exact UI oracle.
- Проверить `WP-01/WP-02` и current-source iteration readiness.

## Не делать

- Не писать, не изменять и не review-ить тест-кейсы.
- Не использовать `AutoFinPreFinal.*` или historical signed-off как current evidence.
- Не расширять scope и не придумывать validation/integration behavior.

## Ожидаемые выходы

- Passed: scope gap findings/review artifacts и route к writer-r1.
- Failed: конкретный возврат в scope analyzer либо `blocked-input`.

## Gate завершения

Каждый gap и oracle obligation имеет корректный source anchor, classification и downstream handling; hidden blocker отсутствует.
