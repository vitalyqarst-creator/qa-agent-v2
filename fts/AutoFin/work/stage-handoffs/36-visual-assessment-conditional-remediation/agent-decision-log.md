# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `visual-assessment-conditional-traceability-remediation` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/35-visual-assessment-conditional-canary/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `validation` | `FIND-COND-TRACE-001` | Add per-TC source/dictionary ref gate | Global draft search would allow wrong-TC false closure | gate v3 and tests | high | applied |
| `DEC-002` | 2 | `artifact-write` | Writer dropped refs from seed | Materialize refs in structured seed | Prevents predictable failure instead of only detecting it | runner seed renderer | high | applied |
| `DEC-003` | 3 | `validation` | V1 fixture | Require exact five findings | Proves remediation targets reproduced defect | `remediation-summary.md` | high | applied |
| `DEC-004` | 4 | `routing` | Tests and validate-only pass | Run one immutable V2 | Meets handoff stop-gate | V2 cycle | high | applied |
| `DEC-005` | 5 | `routing` | Character V4 fails gate v3 | Require character rerun before rollout | Old acceptance used blind gate v2 | next prompt | high | applied |
