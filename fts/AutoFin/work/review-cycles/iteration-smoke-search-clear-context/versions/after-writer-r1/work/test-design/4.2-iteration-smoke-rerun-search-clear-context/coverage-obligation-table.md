# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OBL-001 | WP-BSR32 | SRC-001.P01 | ATOM-001 | filter-reset | clear-applied-filter | Нажатие `Очистить` очищает примененное значение фильтра. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-001 | covered | Exact filter fields and default values are intentionally not asserted. |
| OBL-002 | WP-BSR32 | SRC-001.P02 | ATOM-002 | sorting-reset | clear-applied-sort | Нажатие `Очистить` очищает примененную сортировку. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-002 | covered | Exact default sort is intentionally not asserted. |
| OBL-003 | WP-BSR32 | SRC-001.P03 | ATOM-003 | pagination-reset | clear-pagination-state | Нажатие `Очистить` очищает постраничность. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-003 | covered | Page size, page count and row count are intentionally not asserted. |
| OBL-004 | WP-BSR32 | SRC-001.P04 | ATOM-004 | row-selection-reset | clear-selected-row-state | Нажатие `Очистить` очищает состояние выделения строк. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-004 | covered | No persistence or backend state is asserted. |

## Notes

- No mandatory numeric, exact-length, dictionary, checkbox-list, repeated-block or generated-document classes apply to this scope.
