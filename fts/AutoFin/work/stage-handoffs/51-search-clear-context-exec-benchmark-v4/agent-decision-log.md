# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `search-clear-context-exec-benchmark-v1` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/prompt.scope-to-iteration.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | V3 terminal runtime-contract blocker | Create a new immutable V4; never retry or mutate V3 | V3 authorization is consumed and its attempt is audit evidence | V4 cycle/H51 | high | applied |
| `DEC-002` | 2 | `contract` | Static writer profile allowed only v5 | Make runner `PACKAGE_VERSION` the sole numeric source and reject numeric runtime-profile allowlists | Prevents future package/profile drift after a contract bump | runner; runtime profiles | high | applied |
| `DEC-003` | 3 | `contract` | Writer metadata omitted digest and metadata dicts were duplicated | Centralize package identity and project version/id/digest to writer and reviewer | One implementation reduces drift and gives both fresh roles the same validated identity | exec runner | high | applied |
| `DEC-004` | 4 | `validation` | V3 reached LLM before the mismatch was observed | Add profile and missing-digest regressions that stop before attempt creation | Protocol mismatches are deterministic and should not spend a live turn | runner tests | high | applied |
| `DEC-005` | 5 | `artifact-design` | V4 changes process transport, not requirement design | Reuse hash-bound H50 design inputs instead of duplicating unchanged domain rows | Keeps one current source for the corrected reset design while compiling a new package | V4 compiler input | high | applied |
| `DEC-006` | 6 | `validation` | Code and package pre-live results | Accept pre-live only after 254 target tests, explicit runtime identity, validate-only and exec dry-run pass | Covers implementation, prompt identity, semantic package and transport capability | `pre-live-test-report.md` | high | applied |
| `DEC-007` | 7 | `routing` | All pre-live gates passed | Stop before live until checkpoint and separate authorization are pushed | Preserves exactly-once boundary and prevents testing uncommitted code | `pre-live-stop-gate.md` | high | applied |
| `DEC-008` | 8 | `authorization` | Checkpoint `40641ad...` equals origin | Authorize one V4 exec dispatcher only after a separate authorization push | Checkpoint contains all tested runtime identity changes and immutable package | `pre-live-authorization.md` | high | applied |
| `DEC-009` | 9 | `routing` | Pushed one-shot authorization `e02a9f4...` | Consume it with exactly one V4 exec dispatcher and never retry | Authorization terminal rule applies to every outcome | V4 cycle evidence | high | applied |
| `DEC-010` | 10 | `validation` | Writer draft-ready and reviewer accepted 4/4 | Classify V4 as terminal `accepted-not-promoted`; keep draft unsigned and production unchanged | Semantic acceptance is proven, but promotion was outside authorization | `live-result.v4.json`; `stop-gate.md` | high | applied |
| `DEC-011` | 11 | `routing` | V4 tokens per obligation did not improve | Route to a new medium-scope selection instead of another small-scope repetition | Medium scope can test fixed-context amortization without conflating sharding | `prompt.iteration-to-medium-scope.md` | medium | applied |
