# Package Test Design Plan

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PD-001` | `WP-01` | `dictionary-source` | `SRC-001` | `ATOM-001` | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | `gap` | `dictionary-provenance` | `unidentified dictionary` | `none_required:gap` | `GAP-002` | `GAP-002` | `gap` |
| `PD-002` | `WP-01` | `selection-cardinality` | `SRC-001` | `ATOM-002` | Последовательно выбрать два разных доступных значения в single-select fixture. | `positive` | `single-selection` | `two distinct fixture values` | После второго выбора в виджете отображается ровно одно выбранное значение. | `FT4AutoFinFinal; SRC-001` | `TC-WIDGET-SELECTION-TYPES-001` | `covered` |
| `PD-003` | `WP-01` | `dictionary-source` | `SRC-002` | `ATOM-003` | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | `gap` | `dictionary-provenance` | `unidentified dictionary` | `none_required:gap` | `GAP-002` | `GAP-002` | `gap` |
| `PD-004` | `WP-01` | `selection-cardinality` | `SRC-002` | `ATOM-004` | Выбрать два разных доступных значения в multi-select fixture. | `positive` | `multiple-selection` | `two distinct fixture values` | Оба выбранных значения одновременно отображаются в виджете. | `FT4AutoFinFinal; SRC-002` | `TC-WIDGET-SELECTION-TYPES-002` | `covered` |
| `PD-005` | `WP-01` | `default-value` | `SRC-003` | `ATOM-005` | Проверить новый fixture-виджет до первого пользовательского ввода. | `positive` | `empty-default` | `new untouched widget` | В виджете отсутствует выбранное или заполненное значение. | `FT4AutoFinFinal; SRC-003` | `TC-WIDGET-SELECTION-TYPES-003` | `covered` |
| `PD-006` | `WP-01` | `persistence` | `SRC-003` | `ATOM-006` | Не заявлять внутреннее представление `NULL` без API/DB/persistence evidence. | `gap` | `internal-null` | `unobservable internal value` | `none_required:gap` | `GAP-001` | `GAP-001` | `unclear` |

## Representative Strategy

| strategy_id | target | selected_values | omitted_combinations | residual_risk |
| --- | --- | --- | --- | --- |
| `REP-001` | Single-select dictionary widget | `SINGLE_VALUE_A`; `SINGLE_VALUE_B` from one concrete fixture | Other values and widget instances | `GAP-002`; generic rule requires a concrete runtime fixture. |
| `REP-002` | Multi-select dictionary widget | `MULTI_VALUE_A`; `MULTI_VALUE_B` from one concrete fixture | Three-or-more values and other widgets | Two values are the minimum representative for plural selection. |
| `REP-003` | Empty default widget state | One new widget before input | Saved/reopened and internal storage state | Internal `NULL` remains `GAP-001`. |
