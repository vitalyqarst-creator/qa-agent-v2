# Prompt: V6 transfer accepted -> source-to-package fidelity V7

Продолжи offline следующую итерацию.

1. Прочитай `workflow-state.yaml`, `live-result.v6.json`, `post-canary-source-package-audit.v6.md`, `performance-analysis.v6.md` и `terminal-stop-gate.v6.md`.
2. Не повторяй V6, не исправляй benchmark draft вручную и не выполняй promotion.
3. Добавь deterministic source-to-package fidelity gate: literal display text из выбранной source row должен попадать в atom/oracle либо иметь явное locator-only решение.
4. Добавь gate/regressions для unit semantics: `МБ` нельзя автоматически превращать в точное число байт без source-backed policy; ambiguity должна стать coverage gap или подтверждённой fixture convention.
5. Собери новую immutable package revision для того же source fragment только offline и докажи, что оба `SPA-V6-*` устранены без потери 11 obligations.
6. Сохрани guarded DaData projection; не сокращай obligations/oracles ради token target.
7. После full tests и architecture/artifact audit подготовь checkpoint. Новый live не запускать без отдельной hash-bound authorization.
