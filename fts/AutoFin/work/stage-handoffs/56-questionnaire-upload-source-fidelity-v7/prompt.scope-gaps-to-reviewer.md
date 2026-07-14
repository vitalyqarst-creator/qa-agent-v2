# Prompt: Questionnaire Upload Source-Fidelity Gap Review V7

## Цель этапа

В режиме `scope_gap_review` проверить `GAP-QUT-001` и три fidelity bindings до любого writer/live этапа.

## Входные артефакты

- `../../../AGENT-NOTES.md`
- `workflow-state.yaml`
- `source-selection.md`
- `scope-contract.md`
- `source-parity-check.md`
- `source-row-inventory.md`
- `scope-coverage-gaps.md`
- `scope-clarification-requests.md`
- `negative-oracle-inventory.md`
- `compiler-inputs/questionnaire-upload-transfer-v7/source-to-package-fidelity.json`

## Обязательные действия

1. Подтвердить, что literal BSR 206 сохранен в atom/obligation/plan.
2. Подтвердить, что exact boundary BSR 210 не превращен в байты и остается `GAP-QUT-001`.
3. Проверить, что oversized `50 МБ` testable при обеих conventions и не выдается за product boundary.
4. Проверить сохранение 11 obligations и отсутствие draft/baseline изменений.
5. При успешном gap review подготовить `prompt.scope-to-writer.md`; при ошибке вернуть scope analyzer или установить `blocked-input`.

## Не делать

- Не писать, не переписывать и не review-ить test cases в режиме `scope_gap_review`.
- Не запускать writer/reviewer live.
- Не менять V6 package/draft и production baseline.
- Не закрывать gap догадкой.

## Ожидаемые выходы

- `scope-gap-review.md` с verdict по anchors, classification, clarification requests и routing readiness.
- Решение: оставить gap open либо закрыть только полученным source-backed ответом.

## Gate завершения

При отсутствии policy оставить workflow `ready-for-gap-review`; failed review возвращается в `ft-scope-analyzer` или `blocked-input`; live остается запрещен.
