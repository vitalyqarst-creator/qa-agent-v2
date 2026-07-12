# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/27-calculator-summary-final-source-rebase/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `promotion-block` | v9 diagnostic shape | Do not directly promote v9 | Semantic acceptance did not prove canonical IDs/Metadata | promotion findings | `high` | `applied` |
| `DEC-002` | 2 | `architecture` | missing production gate | Add explicit promotion contract and readiness report | Prevent diagnostic drafts from appearing promotion-ready | runner code/tests | `high` | `applied` |
| `DEC-003` | 3 | `terminal-immutability` | v10 timeout | Start v11 instead of replay | Partial review cannot authorize sign-off | v10/v11 cycles | `high` | `applied` |
| `DEC-004` | 4 | `correction-cap` | v11 Metadata/Priority drift | Use one fresh correction v12 | Drift was production-format evidence, not preference | strengthened contract | `high` | `applied` |
| `DEC-005` | 5 | `promotion` | v12 accepted and gate clean | Promote exact accepted bytes | Candidate and production SHA can be proven equal | promotion receipt | `high` | `applied` |
| `DEC-006` | 6 | `sign-off` | strict validator initially found six warnings | Fix split design artifacts and validator false positives before sign-off | signed-off requires zero warning/error findings | validator/tests | `high` | `applied` |
| `DEC-007` | 7 | `portability` | downstream handoff resolved ignored runtime-cycle paths | Preserve only the accepted cycle summary, reviewer findings and validator result as tracked handoff evidence | A clone must reproduce the next-stage inputs without publishing full runtime diagnostics | portable handoff evidence | `high` | `applied` |
| `DEC-008` | 8 | `windows-portability` | default clean clone failed with filename-too-long | Require `core.longpaths=true` and a short checkout root for the second PC | Rewriting historical snapshots is outside this handoff and would create larger risk | clean-clone verification | `high` | `applied` |
