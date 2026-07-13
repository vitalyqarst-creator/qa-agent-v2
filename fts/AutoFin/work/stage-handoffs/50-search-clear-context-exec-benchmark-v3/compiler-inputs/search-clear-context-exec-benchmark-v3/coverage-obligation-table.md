# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001.P01` | `ATOM-001` | `filter-reset` | `clear-applied-filter` | После нажатия `Очистить` доказанно изменённое состояние фильтров совпадает с зафиксированным initial state. | `BSR 32; SRC-001; section 4.2; PDF page 8` | `TC-SCCB-001` | `covered` | Exact filter defaults are out of scope. |
| `OBL-002` | `WP-01` | `SRC-001.P02` | `ATOM-002` | `sorting-reset` | `clear-applied-sort` | После нажатия `Очистить` доказанно изменённое состояние сортировки совпадает с зафиксированным initial state. | `BSR 32; SRC-001; section 4.2; PDF page 8` | `TC-SCCB-002` | `covered` | Exact default sort is out of scope. |
| `OBL-003` | `WP-01` | `SRC-001.P03` | `ATOM-003` | `pagination-reset` | `clear-pagination-state` | После нажатия `Очистить` доказанно изменённое состояние постраничности совпадает с зафиксированным initial state. | `BSR 32; SRC-001; section 4.2; PDF page 8` | `TC-SCCB-003` | `covered` | Page size and exact row count are out of scope. |
| `OBL-004` | `WP-01` | `SRC-001.P04` | `ATOM-004` | `row-selection-reset` | `clear-selected-row-state` | После нажатия `Очистить` доказанно изменённое состояние выделения строк совпадает с зафиксированным initial state. | `BSR 32; SRC-001; section 4.2; PDF page 8` | `TC-SCCB-004` | `covered` | No backend persistence is asserted. |

## Notes

- No negative, requiredness, numeric, dictionary, integration or persistence obligation applies.
