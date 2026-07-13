# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-address-numeric-boundaries-shadow` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/33-prepared-pipeline-live-acceptance/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | Existing boundary candidate has 66 mixed obligations | Select five numeric field obligations | Keeps fixtures/oracles homogeneous and within 5–15 target | `scope-contract.md` | high | applied |
| `DEC-002` | 2 | `source-boundary` | Old compiled oracle omitted exact postal-index length | Rebuild from Final source normalization and BSR refs | Generic `digits-only` loses BSR 116/153 boundary | `source-row-inventory.md`; V1/V2 specs | high | applied |
| `DEC-003` | 3 | `validation` | V1 preflight selected character calibration | Do not run v1 live | Positive numeric obligations would be mislabeled negative calibration candidates | immutable V1 preflight package | high | applied |
| `DEC-004` | 4 | `gap` | Negative reaction has no oracle | Move uncertainty to separate gap-obligation in immutable v2 | Preserves gap without contaminating positive cases | `scope-coverage-gaps.md`; V2 package | high | applied |
| `DEC-005` | 5 | `routing` | V2 passed all quality/performance gates | Classify `quality-pass-performance-pass`, keep unpromoted | Independent review and deterministic gates agree | `live-acceptance-report.md`; `workflow-state.yaml` | high | applied |
