# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `prepared-widget-selection-live-canary-v11` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/22-prepared-live-canary-blocker/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `validation` | v10 evidence report | Allow reads only under exact current stage-output | Own output is not requirement evidence; sibling cycles remain forbidden | commit `eb31864` | high | applied |
| `DEC-002` | 2 | `context-budget` | full suite reviewer headroom failure | Exclude redundant `skills/README.md` only from already-routed prepared scenarios | Restores headroom without raising budget or removing global policy | instruction manifest | high | applied |
| `DEC-003` | 3 | `routing` | v11 writer final message | Accept `route-to-standard-writer` and stop the canary | Version and output conflicts must not be resolved by model discretion | live-canary-report.md | high | applied |
| `DEC-004` | 4 | `architecture` | package instructions bound to compiler cycle | Require target-cycle compilation and runner preflight | Preserves immutability and deterministic session input | eval candidate | high | deferred |

