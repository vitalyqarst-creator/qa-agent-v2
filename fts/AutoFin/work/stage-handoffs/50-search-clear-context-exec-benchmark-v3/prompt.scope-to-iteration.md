# Search Clear Context V3 Live Entrypoint

## Цель Этапа

После подтверждённого checkpoint push и отдельной authorization выполнить ровно один fresh `codex exec` writer/reviewer V3 run и зафиксировать reviewer verdict без promotion.

## Входные Артефакты

- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/pre-live-test-report.md`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/pre-live-stop-gate.md`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/dispatcher-config.v3.json`
- `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v3-20260713/prepared-input/search-clear-context-exec-benchmark-v3/stage-package.json`
- Pushed checkpoint SHA and separate pushed `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/pre-live-authorization.md`.

## Ограничения

- One dispatcher invocation only.
- Backend `exec`; verified contract v2; no SDK fallback.
- Fresh structured writer and fresh semantic reviewer sessions.
- No retry, resume, rebind, assisted mode, production mutation or promotion.
- Any blocker is terminal and must produce a stop gate.

## После Запуска

- Compare V2 and V3 latency, token use and semantic findings.
- Verify that every reset TC proves a changed visible state before `Очистить`.
- Recheck baseline hashes and absence of the promotion target.
- Persist terminal result, findings/draft links and next routing prompt.
