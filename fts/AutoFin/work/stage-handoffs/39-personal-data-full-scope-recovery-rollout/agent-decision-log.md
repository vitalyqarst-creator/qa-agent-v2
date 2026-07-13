# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | V1 `blocked-validator`; seed-order code fix `1efc0d2` | Create a new V2 cycle and package | Immutable attempt binding forbids replaying V1 | V2 cycle; handoff 39 | high | applied |
| `DEC-002` | 2 | `artifact-write` | Handoff 38 compiler inputs are complete and unchanged | Recompile directly without another AI preparation stage | Avoids the known 2.306M-token performance defect | V2 prepared package | high | applied |
| `DEC-003` | 3 | `validation` | Recovery stop gate | Require exact numeric seed check and validate-only before live | Prevents repeating the known failure | V2 preflight reports | high | applied |
| `DEC-004` | 4 | `execution` | Seed, tests, validate-only and exec capability all pass | Authorize exactly one V2 dispatcher live | Predeclared recovery gates are satisfied | V2 cycle | high | applied |
| `DEC-005` | 5 | `stop` | Reviewer context 183 402 > 131 072 after successful writer | Stop V2 without launching reviewer or replaying cycle | New real blocker satisfies the stop gate | V2 cycle; blocker report | high | applied |
| `DEC-006` | 6 | `test-design` | Full obligations and calibration lifecycle duplicate selected evidence | Keep source evidence/draft; replace duplicates with digest-bound exact indexes | Preserves semantic review inputs while restoring bounded transport | commit `15889ad`; remediation report | high | applied |
| `DEC-007` | 7 | `validation` | Pre-fix cycle state stayed writer-ready after reviewer preflight exception | Persist future reviewer preflight blockers and completed writer evidence in cycle state | Process status must not contradict immutable attempts | commit `15889ad`; regression test | high | applied |
| `DEC-008` | 8 | `routing` | Post-fix reviewer prompt passes offline but has no live decision | Require a new V3 immutable cycle; defer broader optimization | V2 cannot become accepted retroactively | `prompt.scope-to-iteration.md`; workflow state | high | applied |
| `DEC-009` | 9 | `integrity` | Independent audit found stale V2 cycle state contradicting completed writer evidence | Preserve immutable V2, publish a machine-readable quarantine warning and stop advertising the stale state as a normal latest artifact | Manual V2 repair would destroy raw defect evidence, while an unqualified state link could cause an unsafe resume | `v2-cycle-integrity-warning.yaml`; workflow state | high | applied |
