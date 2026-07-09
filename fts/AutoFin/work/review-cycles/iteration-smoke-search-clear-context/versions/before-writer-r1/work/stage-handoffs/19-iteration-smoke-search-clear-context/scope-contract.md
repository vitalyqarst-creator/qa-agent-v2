# Scope Contract

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Section: `4.2. Меню «Заявки в системе»`
- Requirement ids: `BSR 32`
- Canonical test-case path after sign-off: `test-cases/4.2-iteration-smoke-rerun-search-clear-context.md`
- Test-design directory: `work/test-design/4.2-iteration-smoke-rerun-search-clear-context`

## Confirmed Source Boundary

In scope is the action-table row for button `«Очистить»`:

| source_row_id | req_id | button | business_need | action | expected behavior |
| --- | --- | --- | --- | --- | --- |
| `SRC-001` | `BSR 32` | `«Очистить»` | `Очистить контекст поиска` | `Нажатие` | Система очищает фильтры, сортировки, постраничность и состояние выделения строк. |

## Atomic Statements

| atom_id | req_id | atomic statement | coverage expectation |
| --- | --- | --- | --- |
| `ATOM-001` | `BSR 32` | Нажатие `«Очистить»` очищает примененные фильтры поиска. | Covered by an executable UI test or recorded as blocked if no UI fixture can create filtered state. |
| `ATOM-002` | `BSR 32` | Нажатие `«Очистить»` очищает примененные сортировки. | Covered by an executable UI test or recorded as blocked if sorting state cannot be observed. |
| `ATOM-003` | `BSR 32` | Нажатие `«Очистить»` очищает постраничность. | Covered by an executable UI test or recorded as blocked if pagination state cannot be observed. |
| `ATOM-004` | `BSR 32` | Нажатие `«Очистить»` очищает состояние выделения строк. | Covered by an executable UI test or recorded as blocked if row selection cannot be created. |

## Out Of Scope

- `BSR 31` search execution and validation of filled filters.
- `BSR 33` and `BSR 34` row information action.
- `BSR 35` and later row navigation/application-opening actions.
- Exact default values for sort and pagination beyond observable return to the default/initial UI state.

## Downstream Rules

- Writer must not invent concrete filter names or default values.
- Reviewer must verify that all four reset dimensions from `BSR 32` remain traceable.
- A final production artifact is valid only if the session-based runner reaches reviewer sign-off.
