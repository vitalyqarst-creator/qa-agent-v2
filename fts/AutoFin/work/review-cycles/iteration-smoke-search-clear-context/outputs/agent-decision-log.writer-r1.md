# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `iteration-smoke-search-clear-context` |
| stage | `ft-test-case-writer` |
| started_from | `work/review-cycles/iteration-smoke-search-clear-context/cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEC-001 | 1 | source-boundary | `source-selection.md`; active prompt | Use only `FT4AutoFinFinal` and active handoff inputs; exclude previous generated artifacts. | Active prompt explicitly forbids previous generated/canary/smoke/reviewer outputs as source/template. | `writer-session-log.writer-r1.md` | high | applied |
| DEC-002 | 2 | scope-boundary | `scope-contract.md` | Limit executable coverage to `BSR 32 / SRC-001`. | Scope contract excludes `BSR 31`, `BSR 33+` and exact defaults. | `source-row-inventory.md`; canonical TC | high | applied |
| DEC-003 | 3 | coverage | `scope-contract.md`; `source-parity-check.md` | Split `BSR 32` into four atoms for filters, sorting, pagination and row-selection state. | Source sentence contains four independent reset dimensions. | `atomic-requirements-ledger.md` | high | applied |
| DEC-004 | 4 | test-design | runtime TC rules | Write four TC instead of one combined scenario. | One TC should cover one check and one main expected result. | canonical TC | high | applied |
| DEC-005 | 5 | oracle | `scope-contract.md`; prompt constraints | Use observed initial/default UI state as reset oracle. | Exact filter fields, default sort, page size and row counts are not source-backed. | canonical TC; design plan | medium | applied |
| DEC-006 | 6 | artifact-write | `writer-process-workflow.md` | Use `apply_patch` for small explicit Markdown file creation. | Avoid PowerShell here-string/one-shot generation and keep writes reviewable. | all created artifacts | high | applied |
| DEC-007 | 7 | routing | `session-based-review-cycle-format.md` | Route to `structure-preflight-r1` with `writer-draft-ready` only after clean scoped validator gate. | Writer cannot start reviewer directly; runner uses `cycle-state.yaml`. | `cycle-state.yaml`; `prompt.structure-preflight-r1.md` | high | pending-validator |
