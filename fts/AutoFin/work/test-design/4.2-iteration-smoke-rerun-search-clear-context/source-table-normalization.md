# Source Table Normalization

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SRC-001 | SRC-001.P01 | WP-BSR32 | Контекст поиска | filter-reset | Нажата кнопка `Очистить` | Система очищает примененные фильтры. | BSR 32 | section 4.2; XHTML table_index=5; PDF page 8 | high | none_required:no_gap | ATOM-001 |
| SRC-001 | SRC-001.P02 | WP-BSR32 | Контекст поиска | sorting-reset | Нажата кнопка `Очистить` | Система очищает примененные сортировки. | BSR 32 | section 4.2; XHTML table_index=5; PDF page 8 | high | none_required:no_gap | ATOM-002 |
| SRC-001 | SRC-001.P03 | WP-BSR32 | Контекст поиска | pagination-reset | Нажата кнопка `Очистить` | Система очищает постраничность. | BSR 32 | section 4.2; XHTML table_index=5; PDF page 8 | high | none_required:no_gap | ATOM-003 |
| SRC-001 | SRC-001.P04 | WP-BSR32 | Контекст поиска | row-selection-reset | Нажата кнопка `Очистить` | Система очищает состояние выделения строк. | BSR 32 | section 4.2; XHTML table_index=5; PDF page 8 | high | none_required:no_gap | ATOM-004 |

## Normalization Notes

- Normalization keeps `BSR 32` literal for all four properties.
- No concrete filter field, default sorting value, page size, row count, message, persistence, backend state or API effect is added.
