# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001` | `ATOM-001` | `dictionary-source` | `dictionary-provenance` | Не заявлять состав справочника без идентифицированного source inventory. | `SRC-001` | `GAP-002` | `gap` | Точный справочник не задан. |
| `OBL-002` | `WP-01` | `SRC-001` | `ATOM-002` | `selection-cardinality` | `single-selection` | После второго выбора в виджете остаётся ровно одно выбранное значение. | `SRC-001` | `TC-WIDGET-SELECTION-TYPES-001` | `covered` | Проверка cardinality, не состава справочника. |
| `OBL-003` | `WP-01` | `SRC-002` | `ATOM-003` | `dictionary-source` | `dictionary-provenance` | Не заявлять состав справочника без идентифицированного source inventory. | `SRC-002` | `GAP-002` | `gap` | Точный справочник не задан. |
| `OBL-004` | `WP-01` | `SRC-002` | `ATOM-004` | `selection-cardinality` | `multiple-selection` | Два выбранных значения одновременно отображаются в виджете. | `SRC-002` | `TC-WIDGET-SELECTION-TYPES-002` | `covered` | Минимальная репрезентативная проверка multiple selection. |
| `OBL-005` | `WP-01` | `SRC-003` | `ATOM-005` | `default-value` | `visible-empty-default` | До первого ввода в виджете нет выбранного или заполненного значения. | `SRC-003` | `TC-WIDGET-SELECTION-TYPES-003` | `covered` | Только UI-наблюдение. |
| `OBL-006` | `WP-01` | `SRC-003` | `ATOM-006` | `persistence` | `internal-null-interpretation` | Не заявлять внутреннее `NULL` без API/DB/persistence evidence. | `SRC-003` | `GAP-001` | `unclear` | Внутреннее значение не наблюдается через UI. |
