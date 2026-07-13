# Следующая итерация после V5 transport blocker

## Goal

Продолжить `ft-test-case-iteration`, но до нового live устранить transport/output-capacity blocker: добавить deterministic output-budget preflight и новый bounded writer transport для 47 TC. Рекомендуемый target — несколько disjoint source-backed shards, отдельная свежая writer-сессия на shard, детерминированная проверка/merge и один новый reviewer после полного merge.

## Inputs

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-v5-source-first-recovery/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-v5-source-first-recovery/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-v5-source-first-recovery/performance-analysis.v5.md`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-v5-source-first-recovery/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v5-20260713/cycle-state.yaml`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v5-20260713/attempts/writer-r1/attempt-001/runner-output/writer-result.json`

## Guardrails

- Не запускать, не resume и не изменять V5; live quota уже израсходован.
- Не маскировать output-capacity как missing requirement input.
- Shards должны иметь непересекающиеся OBL/TC, полный union 65 obligations/47 TC и стабильный merge order.
- Каждый writer shard должен работать в новой сессии; reviewer стартует только после полного deterministic merge и всех gates.
- Не менять FT-first baseline и production shadow; не использовать V1–V5 drafts как requirement evidence.
- Перед V6 live обязательны bad/corrected capacity eval, full regression, package/hash/context/output preflight и новый checkpoint.
