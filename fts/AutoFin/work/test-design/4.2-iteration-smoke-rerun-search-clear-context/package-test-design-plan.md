# Package Test Design Plan

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PLAN-001 | WP-BSR32 | filters | BSR 32; SRC-001 | ATOM-001 | Проверить возврат измененного фильтра к initial/default state после `Очистить`. | positive-ui-action | reset | changed-filter-state | Фильтр сброшен к initial/default state. | source-backed | TC-BSR32-001 | covered |
| PLAN-002 | WP-BSR32 | sorting | BSR 32; SRC-001 | ATOM-002 | Проверить возврат примененной сортировки к initial/default state после `Очистить`. | positive-ui-action | reset | changed-sort-state | Сортировка сброшена к initial/default state. | source-backed | TC-BSR32-002 | covered |
| PLAN-003 | WP-BSR32 | pagination | BSR 32; SRC-001 | ATOM-003 | Проверить возврат измененной постраничности к initial/default state после `Очистить`. | positive-ui-action | reset | changed-pagination-state | Постраничность сброшена к initial/default state. | source-backed | TC-BSR32-003 | covered |
| PLAN-004 | WP-BSR32 | row-selection | BSR 32; SRC-001 | ATOM-004 | Проверить возврат выделения строк к initial/default state после `Очистить`. | positive-ui-action | reset | selected-row-state | Выделение строк сброшено к initial/default state. | source-backed | TC-BSR32-004 | covered |

## Plan Notes

- Each design row has one check type, one input class and one expected behavior.
- Exact default values are not used as oracle; the oracle is the observed initial/default UI state for the same session.
