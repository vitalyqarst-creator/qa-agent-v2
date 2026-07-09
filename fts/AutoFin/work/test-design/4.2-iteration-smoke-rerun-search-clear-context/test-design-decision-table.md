# Test Design Decision Table

| decision_id | package_id | source_property_id | linked_atom_id | property_type | decision | decision_reason | planned_tc_or_gap | oracle_source | must_be_executable | observable_oracle | testable_part | blocked_part | gap_admissibility | review_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TDDT-001 | WP-BSR32 | SRC-001.P01 | ATOM-001 | filter-reset | standalone_tc | Фильтр можно привести в измененное UI state и проверить возврат к зафиксированному initial/default state. | TC-BSR32-001 | BSR 32; SRC-001 | yes | Контрольный фильтр возвращен в initial/default state. | Сброс примененного фильтра. | none_required:covered | no_gap_required | low |
| TDDT-002 | WP-BSR32 | SRC-001.P02 | ATOM-002 | sorting-reset | standalone_tc | Сортировку можно применить и проверить возврат к зафиксированному initial/default state. | TC-BSR32-002 | BSR 32; SRC-001 | yes | Контрольная сортировка больше не является примененной; состояние равно initial/default. | Сброс примененной сортировки. | none_required:covered | no_gap_required | low |
| TDDT-003 | WP-BSR32 | SRC-001.P03 | ATOM-003 | pagination-reset | standalone_tc | Постраничность можно изменить переходом на другую доступную страницу и проверить возврат к initial/default state. | TC-BSR32-003 | BSR 32; SRC-001 | yes | Текущая страница возвращена к initial/default state. | Сброс постраничности. | none_required:covered | no_gap_required | medium:requires_multi_page_fixture |
| TDDT-004 | WP-BSR32 | SRC-001.P04 | ATOM-004 | row-selection-reset | standalone_tc | Выделение строки можно создать в UI и проверить отсутствие выделения после очистки. | TC-BSR32-004 | BSR 32; SRC-001 | yes | Контрольная строка больше не выделена; состояние равно initial/default. | Сброс выделения строки. | none_required:covered | no_gap_required | low |

## Decision Notes

- `BSR 31` search execution, validation of filter formats, `BSR 33+` row information/navigation actions and exact defaults remain out of scope.
- The TC set deliberately avoids exact default values and concrete filter names because they are not part of `BSR 32`.
