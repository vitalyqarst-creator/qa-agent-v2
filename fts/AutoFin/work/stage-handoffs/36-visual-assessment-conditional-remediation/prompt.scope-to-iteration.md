# Character traceability rerun on gate v3

## Цель этапа

Повторить character-restriction canary на исправленном structured seed и `prepared-package-obligation-gate-v3`. Создать новый immutable package/cycle; V4 не изменять. После результата принять или отклонить controlled rollout для трёх проверенных profiles.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/mockup-visual-inventory.md`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/scope-selection.md`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/compiler-inputs/personal-data-character-restrictions/compiler-input.yaml`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/compiler-inputs/personal-data-character-restrictions/atomic-requirements-ledger.md`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/compiler-inputs/personal-data-character-restrictions/coverage-gaps.md`.
- `work/stage-handoffs/31-personal-data-character-restrictions-shadow/compiler-inputs/personal-data-character-restrictions/coverage-obligation-table.md`.
- `work/stage-handoffs/36-visual-assessment-conditional-remediation/remediation-summary.md`.
- `work/stage-handoffs/36-visual-assessment-conditional-remediation/gate-v3-cross-canary-report.md`.
- `work/stage-handoffs/36-visual-assessment-conditional-remediation/live-acceptance-report.md`.

## Guardrails

- Новый package id и cycle directory; V4 immutable.
- Validate-only должен подтвердить character profile, gate v3 и production boundary.
- Structured seed каждого TC обязан содержать union obligation `source_refs + dictionary_refs`.
- Запустить ровно один live canary, без SDK fallback, promotion и overwrite.
- Сравнить V5 с V4 по quality, duration, context и tokens.
- Rollout допускается только если character V5, numeric V2 и conditional V2 проходят gate v3.

## Ожидаемый выход

- Gate v3 pass для 12/12 character TC либо evidence-backed blocker.
- Итоговая трёхпрофильная rollout matrix.
- Явное решение: `controlled-rollout-ready` или `rollout-blocked`.
