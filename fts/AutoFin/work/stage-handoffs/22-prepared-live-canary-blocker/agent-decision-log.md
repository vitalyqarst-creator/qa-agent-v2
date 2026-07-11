# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `prepared-widget-selection-live-canary` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/21-prepared-autofin-expanded-matrix/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | expanded matrix | Use widget selection for fast path and common actions for standard control | They are the smallest eligible and standard-required compiled packages | live canary plan | high | applied |
| `DEC-002` | 2 | `fallback` | WindowsApps CLI access denied | Use plugin-appserver CLI only after checking its local help contract | It is already used by prior repo live evidence and exposes every required flag | runner invocation | high | applied |
| `DEC-003` | 3 | `safety` | promotion-off canary | Do not pass promotion flags | The experiment must not mutate production test cases | cycle state | high | applied |
| `DEC-004` | 4 | `routing` | evidence-access gate failure | Stop before reviewer and standard control | Continuing would compare an incomplete fast arm and violate the live-blocker stop condition | live-canary-report.md | high | applied |
| `DEC-005` | 5 | `validation` | command `item_5` and gate source | Classify the blocker as a gate false positive, not evidence contamination | The only matched path is the current stage-owned draft under the required attempt root | eval candidate | high | applied |

