# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| stage | `ft-ui-automation-prep` |
| started_from | `work/stage-handoffs/28-calculator-summary-production-readiness/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DL-001` | 1 | `artifact-write` | signed-off baseline exists; automation-ready absent | Create initial automation-ready copy and keep production baseline read-only | Required lifecycle is baseline -> initial automation-ready -> UI run | `test-cases/automation-ready/14-application-card-calculator-summary-entrypoints.md` | `high` | `applied` |
| `DL-002` | 2 | `setup-profile` | no package UI notes or fixture setup path | Use a read-only environment-local restricted fixture profile | It is reachable through normal UI and contains all five summary positions | `work/ui-automation-prep/application-card-calculator-summary-entrypoints/runtime-setup-profile.md` | `risk:fixture-may-drift` | `applied` |
| `DL-003` | 3 | `ui-verdict` | summary visible; independent calculator stage unavailable | Confirm only TC-ACCS-001; block TC-ACCS-002 observability | Summary alone cannot prove correspondence to calculator-stage values | UI report and evidence index | `high` | `applied` |
| `DL-004` | 4 | `ui-verdict` | summary clicks do not navigate | Mark TC-ACCS-003 `mismatch-ft-ui` | Two normal UI click targets leave the fixture card open | UI report, screenshot and trace | `high` | `applied` |
| `DL-005` | 5 | `ui-verdict` | card lacks button; list action does not open window | Mark TC-ACCS-004 `mismatch-ft-ui` and TC-ACCS-005 `blocked-observability` | The expected window never becomes observable | UI report, screenshot and trace | `high` | `applied` |
| `DL-006` | 6 | `gap` | user instruction and signed-off accepted risk | Preserve `GAP-001` unchanged | UI evidence cannot define complete prefill set or exact mapping | automation-ready, report, workflow state | `high` | `applied` |
| `DL-007` | 7 | `security` | screenshots show personal/document/application data; trace/network may contain session/payload data | Publish no Playwright artifact and mark all evidence local restricted | Evidence publication would violate the closeout security gate | evidence index; report | `high` | `applied` |
| `DL-008` | 8 | `test-correction` | automation-ready contained restricted fixture literals and treated list action as fallback | Remove sensitive literals and do not treat list action as equivalent card path | Automation-ready must be reviewable, deterministic and FT-first | automation-ready; safe setup profile | `high` | `applied` |
| `DL-009` | 9 | `routing` | two blocked cases, two divergences, restricted evidence and no portable fixture | Keep final status `ui-prep-blocked`, `stage_status: blocked-input`, `next_skill: none` | Phase cannot be safely or reproducibly handed to automation | workflow; report; follow-up prompt | `high` | `applied` |
| `DL-010` | 10 | `process` | UI session log and next-step prompt were absent | Create stage-specific audit log and blocker follow-up prompt in existing numbered handoff | Avoid duplicate handoff while restoring auditability | handoff 28 | `high` | `applied` |
| `DL-011` | 11 | `validation` | scoped validator clean; fixture-dependent validator tests unavailable | Accept active artifact gate with 0 errors/warnings and 12 passing relevant tests; record missing fixture as separate debt | Do not expand this closeout into agent architecture repair | report; session log | `high` | `applied` |
| `DL-012` | 12 | `routing` | remediation HEAD adds stable evidence IDs and portability clarification but no fixture/runbook, working entrypoint or TC2/TC5 oracle path | Fail the controlled rerun gate and do not launch UI; retain both divergences as unresolved | Normal UI rerun cannot remove the recorded fixture/observability blockers and no owner evidence permits reclassification of divergences | workflow; report; evidence index; follow-up prompt | `high` | `applied` |
| `DL-013` | 13 | `ui-verdict` | no new normal UI evidence was collected | Preserve all five existing UI statuses and all existing evidence IDs | Status changes require a new UI run; old evidence IDs cannot identify new content | automation-ready; report; evidence index | `high` | `applied` |
| `DL-014` | 14 | `validation` | targeted tests pass; active validator has no error/warning; architecture audit has one unrelated budget warning | Accept the blocked checkpoint and disclose inherited package/architecture debt without expanding scope | Candidate artifacts satisfy their contracts; unrelated agent-layer and historical package findings are not blockers introduced by this change | report; session log | `high` | `applied` |
