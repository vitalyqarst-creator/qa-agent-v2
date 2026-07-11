## Цель этапа

Перебазировать canonical scope artifacts `05-application-card-calculator-summary-entrypoints` с устаревшего `AutoFinPreFinal` на активный `FT4AutoFinFinal`, сохранив исправленную трассировку `BSR 43-46` и не меняя production test cases.

## Входные артефакты

- `../20-prepared-autofin-cross-scope/source-selection.md`
- `../05-application-card-calculator-summary-entrypoints/scope-contract.md`
- `../05-application-card-calculator-summary-entrypoints/source-parity-check.md`
- `../05-application-card-calculator-summary-entrypoints/source-row-inventory.md`
- `../05-application-card-calculator-summary-entrypoints/scope-coverage-gaps.md`
- `iteration-summary.md`
- `iteration-session-log.md`
- `agent-decision-log.md`
- `../../../../../evals/prepared-standard-route/20260711/calculator-summary-runtime-report.md`
- `../../review-cycles/codex-exec-prepared-standard-calculator-summary-preflight-v7-20260711/cycle-state.yaml`

## Обязательные действия

- Использовать `ft-scope-analyzer` и активный Final DOCX/XHTML/PDF source selection.
- Обновить canonical scope contract, source parity и row inventory без чтения historical cycle outputs как requirement evidence.
- Проверить `autofin-bsr-source-inventory.md` на конфликт `BSR 35-38` и `BSR 43-46`.
- Сохранить historical `_artifact_write` и review-cycle snapshots неизменными.
- После rebase вернуть handoff в `ft-test-case-iteration` для performance iteration по instruction loading.

## Не делать

- Не изменять fast eligibility.
- Не продвигать eval draft в production.
- Не заменять DOCX source of truth reviewer inference.

## Gate завершения

Scope rebase завершён, когда active handoff и test-design package используют один Final source selection, `BSR 43-46` подтверждены DOCX/XHTML/PDF parity, stale mappings перечислены как historical-only, а strict artifact validation не содержит warning/error.
