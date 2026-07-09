# Package Test Design Plan

| package_id | scope_focus | source_refs | design_strategy | selected_coverage | omitted_coverage | residual_risk |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | Generic constraints for list-like widgets in section `3 Ограничения` | `SRC-001`; `SRC-002`; `SRC-003` | Candidate UI-calibration cases with explicit fixture parameters; no screen-specific field or dictionary value is invented. | Single-select replacement, multi-select simultaneous selection, visible empty default state. | Persistence, save/reopen, DB/API `NULL` proof, screen-specific field rules and exact dictionary composition outside selected fixture values. | `RISK-001`; `GAP-001` |

## Representative Strategy

| strategy_id | target | selected_values | omitted_combinations | residual_risk |
| --- | --- | --- | --- | --- |
| `REP-001` | Single-select dictionary widget | Two distinct active values from one concrete fixture dictionary: `SINGLE_VALUE_A`, `SINGLE_VALUE_B`. | Other dictionary values and other widget instances are omitted. | Generic section-level rule may require additional UI fixture runs per widget implementation. |
| `REP-002` | Multi-select dictionary widget | Two distinct active values from one concrete fixture dictionary: `MULTI_VALUE_A`, `MULTI_VALUE_B`. | Three-or-more selected values and other dictionary values are omitted. | Source says several values; two values are the minimal representative for plural selection. |
| `REP-003` | Empty default widget state | One concrete new widget before user input: `EMPTY_WIDGET_FIELD`. | Other widget types and saved/reopened states are omitted. | Internal `NULL` interpretation remains unproven without a permitted artifact. |
