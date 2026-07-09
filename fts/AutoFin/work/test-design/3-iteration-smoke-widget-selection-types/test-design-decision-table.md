# Test Design Decision Table

| decision_id | source_ref | condition_or_input | expected_observable_result | atom_refs | output |
| --- | --- | --- | --- | --- | --- |
| `TDDT-001` | `SRC-001` | User selects `SINGLE_VALUE_A`, then selects `SINGLE_VALUE_B` in a widget of type `Список`. | Only `SINGLE_VALUE_B` remains selected. | `ATOM-001`; `ATOM-002` | `TC-WIDGET-SELECTION-TYPES-001` |
| `TDDT-002` | `SRC-002` | User selects `MULTI_VALUE_A` and `MULTI_VALUE_B` in a widget of type `Список с множественным выбором`. | Both values are selected simultaneously. | `ATOM-003`; `ATOM-004` | `TC-WIDGET-SELECTION-TYPES-002` |
| `TDDT-003` | `SRC-003` | User opens a new widget before selecting or entering a value. | The widget has no visible selected or filled value. | `ATOM-005` | `TC-WIDGET-SELECTION-TYPES-003` |
| `TDDT-004` | `SRC-003` | Internal system interprets absent widget value as `NULL`. | No UI-only observable result is defined by selected sources. | `ATOM-006` | `GAP-001` |
