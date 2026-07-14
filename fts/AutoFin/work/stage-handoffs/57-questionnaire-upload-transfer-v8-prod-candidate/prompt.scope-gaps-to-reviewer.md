# Prompt: Questionnaire Upload Prod-Candidate Gap Review V8

## Цель этапа

В новой read-only сессии `ft-test-case-reviewer` режима `scope_gap_review` проверить source anchors, `GAP-QUT-001`, fidelity bindings и исправленный downstream routing до compile/live.

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
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/atomic-requirements-ledger.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/coverage-obligation-table.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/package-test-design-plan.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/test-design-applicability-matrix.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/source-to-package-fidelity.json`
- `../56-questionnaire-upload-source-fidelity-v7/scope-gap-review.md`

## Обязательные действия

1. Проверить anchors, classification и clarification request для `GAP-QUT-001`.
2. Подтвердить, что literal BSR 206 сохранён в atom/obligation/plan.
3. Подтвердить, что exact boundary BSR 210 не превращён в байты.
4. Подтвердить, что `50 МБ` является только заведомо oversized fixture.
5. Проверить 11 obligations, 10 testable obligations, 9 planned TC и отсутствие V8 draft/production target.
6. Проверить routing: открытый non-blocking `GAP-QUT-001` сохраняется downstream, exact-boundary TC запрещён, остальные obligations могут перейти в writer/iteration.

## Не делать

- Не писать и не review-ить test cases.
- Не закрывать `GAP-QUT-001` догадкой.
- Не запускать writer, reviewer cycle или promotion.
- Не менять H56 и production baseline.

## Ожидаемые выходы

- `scope-gap-review.md` с verdict `passed | needs-scope-revision | blocked-input`.
- reviewer session log и decision log.
- При `passed` — handoff к `prompt.scope-to-iteration.md` с сохранённым open non-blocking gap.

## Gate завершения

`passed` допустим, если source/gap/fidelity checks прошли и downstream явно сохраняет `GAP-QUT-001` без exact-byte TC. Failed review возвращает workflow в `ft-scope-analyzer` или `blocked-input`.
