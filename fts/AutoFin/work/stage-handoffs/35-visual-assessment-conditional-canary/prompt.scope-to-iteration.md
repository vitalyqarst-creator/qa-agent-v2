# Remediation source-ref preservation gate

## Цель этапа

Устранить false acceptance `FIND-COND-TRACE-001`: deterministic gates и compact reviewer должны отклонять draft, если соответствующий TC не сохраняет все обязательные source refs testable obligation. После исправления скомпилировать immutable conditional V2 и выполнить один повторный live canary.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`.
- `work/stage-handoffs/35-visual-assessment-conditional-canary/scope-contract.md`.
- `work/stage-handoffs/35-visual-assessment-conditional-canary/scope-coverage-gaps.md`.
- `work/stage-handoffs/35-visual-assessment-conditional-canary/scope-clarification-requests.md`.
- `work/stage-handoffs/35-visual-assessment-conditional-canary/source-parity-check.md`.
- `work/stage-handoffs/35-visual-assessment-conditional-canary/source-row-inventory.md`.
- `work/stage-handoffs/35-visual-assessment-conditional-canary/mockup-visual-inventory.md`.
- `work/stage-handoffs/35-visual-assessment-conditional-canary/traceability-gate-finding.md`.
- `work/review-cycles/visual-assessment-conditional-shadow-v1-20260713/cycle-state.yaml`.
- `work/review-cycles/visual-assessment-conditional-shadow-v1-20260713/prepared-input/visual-assessment-conditional-v1/atomic-obligations.json`.

## Guardrails

- Проверять refs внутри TC, соответствующего obligation; ref в другом TC не засчитывать.
- Не требовать TC для `gap`/`not-applicable` obligations.
- Сохранить поддержку grouped obligations без ослабления per-obligation traceability.
- Добавить unit tests для missing ref, wrong-TC ref, dictionary ref и полного pass.
- Не редактировать immutable V1 cycle.
- V2 создаётся только после tests; один live run, без SDK fallback/promotion/overwrite.

## Ожидаемый выход

- Gate возвращает blocking finding до reviewer на старом defective fixture.
- V2 draft содержит `OBL`, `ATOM`, `SRC`, `BSR` и `DICT` refs.
- Conditional canary получает quality/performance verdict без ручного override.
