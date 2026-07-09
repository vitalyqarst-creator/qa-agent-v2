# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `iteration-smoke-widget-selection-types` |
| stage | `ft-source-locator / ft-scope-analyzer / ft-test-case-iteration` |
| started_from | `user request on branch audit/stabilize-testcase-agent-persistence-calibration-handoff` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `branch-preflight` | `git branch --show-current`, `git rev-parse HEAD`, `git status --short --branch` | Base branch accepted and work branch created. | Current branch matched required base; tracking branch existed; unrelated untracked files were present but not touched. | `scope-proposal.md` | `high` | `applied` |
| `DEC-002` | 2 | `source-boundary` | `fts/AutoFin/source/*`, `AGENT-NOTES.md` | Selected `FT4AutoFinFinal` DOCX/XHTML/PDF. | User explicitly requested `FT4AutoFinFinal`; XHTML exists and is mandatory. | `source-selection.md` | `high` | `applied` |
| `DEC-003` | 3 | `scope-boundary` | DOCX/XHTML section extraction, existing artifact names for contamination control | Selected section `3` widget selection constraints. | Small source-backed scope; not canary/save-flow; avoids application-card address/contact canary areas. | `scope-contract.md` | `medium` | `applied` |
| `DEC-004` | 4 | `routing` | `ft-test-case-iteration` skill | Routed to session-based runner. | User requested штатный writer/reviewer iteration; current session must not do writer/reviewer work manually. | `cycle-state.yaml` | `medium` | `applied` |
| `DEC-005` | 5 | `fallback` | Runner attempts without completion/state advancement | Marked cycle `blocked-input` and moved writer draft out of production `test-cases`. | Reviewer stages did not run; keeping a production final TC would misrepresent the process outcome. | `blocked-runner-report.md`; `writer-draft-from-interrupted-run.md` | `high` | `applied` |
