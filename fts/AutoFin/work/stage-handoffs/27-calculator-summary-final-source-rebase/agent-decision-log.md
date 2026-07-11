# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/26-prepared-standard-calculator-summary/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | handoff 20 and handoff 26 | Use only `FT4AutoFinFinal` DOCX/XHTML/PDF as active evidence | Final family is selected and XHTML is mandatory; PreFinal mappings caused verified drift | handoff 27 | `high` | `applied` |
| `DEC-002` | 2 | `history-preservation` | signed-off handoff 05 and old review cycles | Create handoff 27 instead of rewriting historical snapshots | Historical signed-off evidence must remain auditable even when superseded | handoff 27 | `high` | `applied` |
| `DEC-003` | 3 | `inventory` | legacy BSR generator scans all artifacts | Correct the generator and regenerate against Final rather than manually swapping rows | Historical mentions are not proof of active source mapping | package BSR inventory and generator | `high` | `in-progress` |
| `DEC-004` | 4 | `scope-boundary` | Final rows for BSR 35–38 | Route them to `section-4.2-applications-menu-search`, not calculator-summary or generic card actions | Final XHTML/PDF and active source-row inventory identify Continue/Create application-list actions | scope contract and BSR inventory | `high` | `applied` |
| `DEC-005` | 5 | `inventory-risk` | BSR 43–46 also occur in active personal-data inventory | Flag multiple active mappings instead of rewriting personal-data artifacts in this scope | Cross-scope source rebase exceeds calculator iteration and must remain visible | package BSR inventory | `high` | `applied` |
