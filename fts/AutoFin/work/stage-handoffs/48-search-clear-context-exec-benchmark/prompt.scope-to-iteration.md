# Search Clear Context Exec Benchmark Iteration

## Цель этапа

В новом immutable cycle выполнить обычный prepared-standard writer-reviewer benchmark по BSR 32 через verified `codex exec`.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/negative-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/requiredness-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/mockup-visual-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/prompt.scope-to-writer.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/workflow-state.yaml`
- `fts/AutoFin/AGENT-NOTES.md`

## Обязательные действия

- Compile immutable standard package from current-source H48 artifacts.
- Start one fresh structured writer and, only after deterministic gates, one fresh reviewer.
- Preserve four independent BSR 32 obligations/TC and unique names.
- Use backend `exec`, contract v2, no SDK fallback; collect duration/token metrics.
- Stop at `accepted-not-promoted` or first blocker; checkpoint and separate authorization required before live.

## Не делать

- Не использовать H19 drafts/test cases, reviewer rebind, retry/resume or assisted fallback.
- Не создавать or modify production test cases.
- Не расширять scope beyond BSR 32 or invent exact default values.

## Ожидаемые выходы

- Prepared package, validate-only/dry-run evidence, one writer/reviewer cycle, performance comparison and terminal stop gate.

## Gate завершения

Benchmark завершён после immutable terminal evidence, H48/H49 artifact validation, baseline boundary recheck and pushed terminal commit.
