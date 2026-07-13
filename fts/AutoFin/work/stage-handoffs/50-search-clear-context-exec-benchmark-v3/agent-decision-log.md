# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `search-clear-context-exec-benchmark-v1` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/49-search-clear-context-exec-benchmark-iteration/prompt.scope-to-iteration.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | V2 `F-001/F-002` | Create a new immutable V3; do not repair, resume or rebind V2 | Findings identify an upstream plan defect, not a transport-only defect | V3 cycle | high | applied |
| `DEC-002` | 2 | `contract` | Reset setup was implicit in V2 text | Raise current prepared contract to v6 with machine-readable execution semantics and state-change metadata | A language-only heuristic would be fragile and would not preserve the pre-action proof across stages | `prepared_package.py`; references | high | applied |
| `DEC-003` | 3 | `validation` | V2-like plans named page 2 / first row without relative-state proof | Block reset rows unless captured initial, changed setup, pre-action oracle and exact inequality relation are present | Prevents spending an LLM turn on a deterministically incomplete plan | `prepared_compiler.py`; compiler tests | high | applied |
| `DEC-004` | 4 | `validation` | Compiler is the primary producer but packages can be built by other callers | Add runner defense-in-depth state-change preflight | Missing reset classification must still stop before attempt creation | exec runner; runner tests | high | applied |
| `DEC-005` | 5 | `test-design` | Reviewer `F-001/F-002` | Rewrite PD-001..PD-004 relative to captured initial state and fixture-block when no differing state exists | Avoids invented exact defaults and removes page-2/first-row assumptions | V3 compiler inputs | high | applied |
| `DEC-006` | 6 | `validation` | Package and process regressions | Accept pre-live only after 237 clean target tests, validate-only and exec dry-run | Provides code, semantic-package and transport evidence | `pre-live-test-report.md` | high | applied |
| `DEC-007` | 7 | `routing` | Pre-live gates passed | Stop before live until checkpoint and separate authorization are pushed | Exactly-once live boundary remains mandatory | `pre-live-stop-gate.md` | high | applied |
| `DEC-008` | 8 | `authorization` | Checkpoint `934fb893...` matches origin | Authorize one V3 exec dispatcher only after this separate commit is pushed | User requested full V3 and all pre-live gates passed | `pre-live-authorization.md` | high | applied |
| `DEC-009` | 9 | `routing` | One authorised V3 dispatcher | Consume the authorization with exactly one exec invocation and do not retry after writer blocker | The terminal rule applies to any live outcome | V3 cycle evidence | high | applied |
| `DEC-010` | 10 | `validation` | Writer returned `blocked-input` before draft | Classify V3 as terminal process-contract blocker; reviewer must not start | Package v6 conflicts with embedded v5 eligibility and metadata omits the required digest | `live-blocker-analysis.md`; `stop-gate.md` | high | applied |
| `DEC-011` | 11 | `scope-boundary` | Writer blocker mentions profile eligibility | Preserve source, scope, V3 design rows and protected baselines unchanged | Evidence identifies technical protocol migration, not a domain or FT defect | `iteration-summary.md` | high | applied |
| `DEC-012` | 12 | `routing` | V3 authorization consumed | Route only to a new immutable V4 with centralized metadata and cross-contract regression | Editing/retrying V3 would invalidate immutable exactly-once evidence | `prompt.scope-to-iteration.md` | high | applied |
