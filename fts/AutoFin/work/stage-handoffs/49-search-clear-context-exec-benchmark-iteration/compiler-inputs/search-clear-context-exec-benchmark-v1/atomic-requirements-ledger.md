# Atomic Requirements Ledger

| atom_id | req_id | source_row_id | atomic_statement | source_ref | field_or_block | condition | expected_behavior | planned_tc_or_gap | coverage_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `BSR 32` | `SRC-001` | Нажатие `Очистить` очищает применённые фильтры поиска. | `section 4.2; XHTML table 5 row 47; PDF page 8` | search filters | at least one filter differs from initial state | Applied filter state is cleared to the captured initial state. | `TC-SCCB-001` | `covered` |
| `ATOM-002` | `BSR 32` | `SRC-001` | Нажатие `Очистить` очищает применённые сортировки. | `section 4.2; XHTML table 5 row 47; PDF page 8` | result sorting | sort state differs from initial state | Applied sort state is cleared to the captured initial state. | `TC-SCCB-002` | `covered` |
| `ATOM-003` | `BSR 32` | `SRC-001` | Нажатие `Очистить` очищает постраничность. | `section 4.2; XHTML table 5 row 47; PDF page 8` | result pagination | current page differs from initial page | Pagination is cleared to the captured initial state. | `TC-SCCB-003` | `covered` |
| `ATOM-004` | `BSR 32` | `SRC-001` | Нажатие `Очистить` очищает состояние выделения строк. | `section 4.2; XHTML table 5 row 47; PDF page 8` | selected result row | one row is selected | Row-selection state is cleared to the captured initial state. | `TC-SCCB-004` | `covered` |

## Ledger Notes

- Every atom is derived from the same current-source BSR 32 row but has one independent observable result.
- Exact default filter, sort and page values are not asserted; each case captures the initial state in the same session before creating a changed state.
