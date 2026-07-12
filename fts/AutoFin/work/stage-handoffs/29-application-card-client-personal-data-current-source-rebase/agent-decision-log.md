# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | source-boundary | FT source families | Select `FT4AutoFinFinal.docx/xhtml/pdf`; reject `AutoFinPreFinal.*`. | Current source family and mandatory XHTML exist. | scope/parity artifacts | risk:historical mappings stale | applied |
| `DEC-002` | 2 | scope-boundary | XHTML rows/codes | Bound scope to tr 56–66 / `BSR 47–77`. | First neighbor is recognition `BSR 78`. | scope-contract.md | high | applied |
| `DEC-003` | 3 | validation | Historical signed-off | Treat 15 cases as candidate baseline only. | Later additions lacked a complete new loop. | prompt.scope-to-iteration.md | high | applied |
| `DEC-004` | 4 | gap | Missing validation oracle | Use candidate calibration obligations. | Restriction exists, exact UI reaction does not. | oracle inventories; GAP-001/002 | high | applied |
| `DEC-005` | 5 | integration | DaData/ABS clauses | Cover visible success effect; separate technical attribution. | UI does not prove provider. | GAP-003 | medium | applied |
| `DEC-006` | 6 | source-boundary | Opened mockups | Use only for field/toggle mechanics. | Mockup is not a business source. | mockup-visual-inventory.md | high | applied |
