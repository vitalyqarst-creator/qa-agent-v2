# Controlled prepared pipeline rollout

## Goal

Применить structured prepared writer-reviewer pipeline к подтверждённому полному scope `application-card-client-personal-data` как к первому ограниченному rollout. Это не promotion уже созданных canary draft.

## Inputs

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/mockup-visual-inventory.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/negative-oracle-inventory.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/requiredness-oracle-inventory.md`.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/final-bsr-evidence.json`.
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/round-2-findings.md`.
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r2-draft.md` — только regression/defect evidence, не source evidence.
- `work/stage-handoffs/37-personal-data-character-restrictions-gate-v3/rollout-matrix.md`.
- `work/stage-handoffs/37-personal-data-character-restrictions-gate-v3/stop-gate.md`.
- `work/stage-handoffs/37-personal-data-character-restrictions-gate-v3/live-acceptance-report.md`.
- `work/stage-handoffs/37-personal-data-character-restrictions-gate-v3/agent-decision-log.md`.

## Guardrails

- Использовать только полный current-source scope `application-card-client-personal-data`; не смешивать его с соседними разделами.
- Character/numeric/conditional canary outputs использовать только как process evidence, не как source evidence для нового draft.
- Новый shadow cycle не снимает исторический `round-cap-reached` и не обходит SEM-001/SEM-002: compiler inputs должны явно устранить оба defect class до live.
- Создать новый immutable package/cycle и выполнить validate-only до live.
- Использовать structured mode, gate v3, verified exec; SDK fallback запрещён.
- Выполнить не более одного live writer-reviewer run.
- Не включать `--promote-final` и `--allow-overwrite-final`.
- Каждый TC обязан содержать полный union `source_refs + dictionary_refs` своих obligations.
- Сохранить gaps и не придумывать UI oracle.

## Acceptance

- Gate v3, quality bundle и semantic reviewer проходят без blocking findings.
- SEM-001 (`ATOM-025` traceability) и SEM-002 (stale decision-table mappings) не воспроизводятся в compiled package/draft.
- Production boundary остаётся неизменной.
- Performance telemetry сравнима с canary baseline; существенный drift объяснён.
- При blocker результат фиксируется как evidence, без повторного live-run в том же immutable cycle.
