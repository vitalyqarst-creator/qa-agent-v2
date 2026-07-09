# Fixture Catalog

| fixture_id | used_by | fixture_requirement | concrete_values_to_record | status |
| --- | --- | --- | --- | --- |
| `FIX-001` | `TC-WIDGET-SELECTION-TYPES-001` | A concrete UI widget of type `Список` backed by a dictionary with at least two active values. | `SINGLE_LIST_FIELD`; `SINGLE_VALUE_A`; `SINGLE_VALUE_B`; screen path/evidence. | `ui-calibration-required` |
| `FIX-002` | `TC-WIDGET-SELECTION-TYPES-002` | A concrete UI widget of type `Список с множественным выбором` backed by a dictionary with at least two active values. | `MULTI_LIST_FIELD`; `MULTI_VALUE_A`; `MULTI_VALUE_B`; screen path/evidence. | `ui-calibration-required` |
| `FIX-003` | `TC-WIDGET-SELECTION-TYPES-003` | A concrete widget visible in a new state before user input. | `EMPTY_WIDGET_FIELD`; screen path/evidence; proof that no user value was selected before observation. | `ui-calibration-required` |

## Fixture Guardrails

- Do not use previous generated test cases or canary artifacts to choose fixture fields.
- Do not invent dictionary contents; record concrete active values from the selected UI fixture during calibration.
- Do not use the candidate cases as proof of persistence, database storage, API behavior or internal `NULL` semantics.
