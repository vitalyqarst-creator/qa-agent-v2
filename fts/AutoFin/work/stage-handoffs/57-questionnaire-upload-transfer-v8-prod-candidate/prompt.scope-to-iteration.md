# Prompt: Run Questionnaire Upload V8 Prod-Candidate Iteration

## Цель этапа

Скомпилировать и запустить один immutable prepared writer/reviewer cycle для 9 planned TC в отдельных `codex exec` сессиях, не выполняя promotion автоматически.

## Входные артефакты

- `../../../AGENT-NOTES.md`
- `workflow-state.yaml`
- `source-selection.md`
- `scope-contract.md`
- `source-parity-check.md`
- `source-row-inventory.md`
- `scope-coverage-gaps.md`
- `scope-clarification-requests.md`
- `scope-gap-review.md`
- `negative-oracle-inventory.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/atomic-requirements-ledger.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/coverage-obligation-table.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/package-test-design-plan.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/test-design-applicability-matrix.md`
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/source-to-package-fidelity.json`

## Обязательные действия

1. Скомпилировать новый immutable prepared package и зафиксировать SHA-256.
2. Выполнить runner validate-only/dry-run до live.
3. Использовать verified `codex exec`; SDK fallback не разрешать.
4. Запустить ровно одну fresh structured writer session и одну fresh read-only reviewer session.
5. Проверить разные session IDs, fidelity/obligation/deterministic gates и reviewer verdict.
6. Остановиться на `accepted-not-promoted`, `blocked-input` или другом terminal blocker.
7. Собрать duration/token/session evidence и не скрывать превышение бюджета.

## Не делать

- Не закрывать `GAP-QUT-001` и не создавать exact-byte TC.
- Не retry/resume failed cycle и не переходить на SDK/workspace writer.
- Не исправлять draft вручную.
- Не создавать production target через автоматический promotion.
- Не использовать V6/V7 test cases как requirement evidence.

## Ожидаемые выходы

- immutable prepared package и package hash;
- cycle artifacts, writer/reviewer session IDs и performance report;
- unsigned candidate draft либо explicit blocker;
- reviewer verdict и deterministic gate bundle;
- promotion dry-run только после отдельного ручного quality gate.

## Gate завершения

Live canary принимается только при exec-only route, разных fresh sessions, нулевых blocking findings, сохранённом `GAP-QUT-001`, отсутствии exact-byte TC и неизменном production target.
