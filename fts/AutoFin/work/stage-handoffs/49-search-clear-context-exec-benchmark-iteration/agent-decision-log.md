# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `search-clear-context-exec-benchmark-v1` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/48-search-clear-context-exec-benchmark/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | H48 validated scope | Keep only BSR 32 and four reset effects | Prevent scope drift and old-draft contamination | compiler inputs | high | applied |
| `DEC-002` | 2 | `test-design` | One source row has four independent results | Map four OBL to four ATOM and four unique TC ids | One case must assert one main expected result | ledger/obligation/plan | high | applied |
| `DEC-003` | 3 | `routing` | Reset changes current UI state | Require `standard-required` prepared route | State transition is outside fast-path eligibility | applicability matrix | high | applied |
| `DEC-004` | 4 | `artifact-write` | Immutable package and runtime evidence | Use only compiler and dispatcher for generated artifacts | Preserve digest and auditability | cycle package/attempts | high | applied |
| `DEC-005` | 5 | `authorization` | Live boundary from iteration plan | Require checkpoint push and separate authorization push | Prevent accidental duplicate live execution | pre-live gates | high | applied |
| `DEC-006` | 6 | `validation` | V1 package omitted `BSR 32` from structured source refs | Reject V1 before live and fix compiler token projection | Requirement codes must survive prepared transport | compiler regression; V1 package | high | applied |
| `DEC-007` | 7 | `immutability` | Compiler fix changes package content | Preserve V1 and compile a new V2 cycle | Existing prepared package must never be overwritten | V2 cycle | high | applied |
| `DEC-008` | 8 | `validation` | V2 pre-live evidence | Accept package as pre-live ready | 108 clean tests; validate-only and artifact gates pass | pre-live reports | high | applied |
| `DEC-009` | 9 | `routing` | Pre-live gate passed | Stop before live until checkpoint and separate authorization are pushed | Exactly-once boundary is mandatory | `pre-live-stop-gate.md` | high | applied |
| `DEC-010` | 10 | `authorization` | Checkpoint matches origin | Authorize exactly one V2 exec dispatcher after authorization push | All pre-live and production-boundary gates passed | `pre-live-authorization.md` | high | applied |
