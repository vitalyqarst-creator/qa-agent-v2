# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `personal-data-character-restrictions-gate-v3` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/36-visual-assessment-conditional-remediation/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `artifact-write` | V4 immutable, gate v3 replay has 12 findings | Compile new V5 package/cycle from unchanged character compiler inputs | Separates gate/seed remediation from requirement changes | `work/review-cycles/personal-data-character-restrictions-shadow-v5-20260713/` | high | applied |
| `DEC-002` | 2 | `validation` | V5 package compiled | Require validate-only before live | Confirms character route, budgets, sandbox and production boundary | `validate-only-report.v5.json` | high | applied |
| `DEC-003` | 3 | `fallback` | Compiler rejected parent `prepared-input` as output root | Retry with exact `<cycle>/prepared-input/<package-id>` root | The first command produced no package; corrected path matches compiler contract | `prepared-input/personal-data-character-restrictions-v5/` | high: failed invocation wrote no package | applied |
| `DEC-004` | 4 | `routing` | V5 gate, quality and review pass; numeric V2 and conditional V2 pass | Mark matrix `controlled-rollout-ready` | All three named profiles satisfy the predeclared acceptance gate | `rollout-matrix.md`; `stop-gate.md` | medium: three profiles do not prove production-wide safety | applied |
| `DEC-005` | 5 | `artifact-write` | Promotion disabled and production target absent | Preserve FT-first baseline and accepted draft as eval evidence only | Canary approval is not a production write contract | `live-acceptance-report.md`; `workflow-state.yaml` | high | applied |
