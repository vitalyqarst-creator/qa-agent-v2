# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `personal-data-static-properties-shadow` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | Parent scope contains 42 atoms and prior plan requires 5–15 obligations | Select 15 static properties for surname, name and patronymic | Coherent real 4.3 fragment within the requested size; validation and integrations remain explicitly excluded | `scope-selection.md` | high | applied |
| `DEC-002` | 2 | `source-boundary` | Current FT source selection and handoff `29` | Use FT4 DOCX/XHTML/PDF and package notes; do not use generated TC as evidence | Preserves current-source and contamination contracts | compiler inputs | high | applied |
| `DEC-003` | 3 | `routing` | Compiler result | Accept compiler-selected `simple-field-property` without override | No unsupported dimensions or gaps were reported | prepared package v1/v2 | high | applied |
| `DEC-004` | 4 | `validation` | First live writer returned `blocked-input` | Preserve blocked cycle and do not retry it | Immutable cycle rule; blocker is reproducible | cycle `personal-data-static-properties-shadow-20260712` | high | applied |
| `DEC-005` | 5 | `test-design` | Missing concrete valid values for six input checks | Materialize synthetic value `Тест` with BSR 48/51/54 as validity anchor | Adds test data, not new product behavior | `package-test-design-plan.md`; prepared package v2 | medium | applied |
| `DEC-006` | 6 | `routing` | Reviewer accepted v2 and promotion disabled | Keep result `accepted-not-promoted` | Eval cannot overwrite production baseline | cycle v2; `workflow-state.yaml` | high | applied |
| `DEC-007` | 7 | `quality` | Manual post-run comparison of case bodies | Record three editability/value-type overlap pairs as residual process finding | Unique titles alone do not prevent redundant executable cases | `iteration-summary.md` | risk:reviewer-blind-spot | deferred |
