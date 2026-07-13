# Search Clear Context V4 Live Entrypoint

## Цель Этапа

После подтверждённого checkpoint push и отдельной authorization выполнить ровно один fresh `codex exec` writer/reviewer V4 run и зафиксировать semantic verdict без promotion.

## Входные Артефакты

- `fts/AutoFin/AGENT-NOTES.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/live-result.v3.json`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/51-search-clear-context-exec-benchmark-v4/pre-live-test-report.md`
- `fts/AutoFin/work/stage-handoffs/51-search-clear-context-exec-benchmark-v4/pre-live-stop-gate.md`
- `fts/AutoFin/work/stage-handoffs/51-search-clear-context-exec-benchmark-v4/dispatcher-config.v4.json`
- `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v4-20260713/prepared-input/search-clear-context-exec-benchmark-v4/stage-package.json`
- Pushed checkpoint SHA and separate pushed `pre-live-authorization.md`.

## Ограничения

- One dispatcher invocation only; backend `exec`, verified contract v2, no SDK fallback.
- Fresh structured writer and, only after writer gates, fresh semantic reviewer.
- No retry, resume, rebind, assisted mode, production mutation or promotion.
- V2/V3 drafts are not requirement evidence.
- Any blocker is terminal and must produce a stop gate.

## После Запуска

- Verify writer/reviewer prompts carry the exact V4 version/id/digest identity.
- Verify all four reset TCs prove changed visible state before `Очистить`.
- Compare V2/V3/V4 latency, tokens and terminal quality.
- Recheck baseline hashes and absence of the promotion target.
- Persist terminal result, draft/findings links when present, and next routing prompt.
