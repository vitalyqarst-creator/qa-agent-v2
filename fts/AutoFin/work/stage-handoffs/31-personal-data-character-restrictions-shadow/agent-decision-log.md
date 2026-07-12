# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `personal-data-character-restrictions-shadow` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/30-personal-data-static-properties-shadow/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | Handoff `30` recommends BSR 48/51/54 | Select only character restrictions for three current-FIO fields | Coherent standard-required scope without DaData | `scope-selection.md` | high | applied |
| `DEC-002` | 2 | `test-design` | FT allows text and `-`; oracle inventory separates digits and special chars | Create four independent classes per field | Prevents duplicate names and loss of negative classes | compiler inputs | high | applied |
| `DEC-003` | 3 | `gap-handling` | GAP-001 lacks exact UI rejection mechanics | Keep negative cases as UI-calibration candidates | Exact message/filter/highlight/save behavior cannot be inferred | `coverage-gaps.md`; draft | high | applied |
| `DEC-004` | 4 | `routing` | Compiler reports unsupported standard dimensions | Use `standard-required`; do not override to fast | Negative oracle needs full reviewer reasoning | prepared packages | high | applied |
| `DEC-005` | 5 | `validation` | V1/V2 command budgets below explicit floors | Preserve both blocked cycles and create V3 | Immutable-cycle contract forbids reuse | configs V1–V3 | high | applied |
| `DEC-006` | 6 | `promotion` | V3 reviewer accepted; UI oracle still open | Keep accepted draft unpromoted | Shadow evidence is not regression-ready baseline | V3 cycle state | high | applied |
| `DEC-007` | 7 | `performance` | V3 costs 1.69M tokens and 74 commands | Make standard context reduction the next architecture iteration | Correct output is too expensive for steady-state use | `iteration-summary.md`; next prompt | high | deferred |
