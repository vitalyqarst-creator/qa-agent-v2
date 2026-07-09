# Scope Coverage Gaps

## Context

- FT package: `AutoFin`
- Scope slug: `iteration-smoke-widget-selection-types`
- Selected source rows: `SRC-001`, `SRC-002`, `SRC-003`

## Gap Inventory

No blocking `GAP-*` items are raised before writer start.

## Non-Blocking Risks To Preserve

| risk_id | source_ref | risk | downstream_handling |
| --- | --- | --- | --- |
| `RISK-001` | `SRC-001`..`SRC-003` | Selected section defines generic widget constraints, not a concrete screen field. | Writer/reviewer must not invent unsupported field names or dictionary values; fixture needs must be explicit. |

## BA Questions

None before writer start.
