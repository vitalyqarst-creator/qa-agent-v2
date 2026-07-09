# Coverage Obligation Table

| obligation_id | dimension | source_ref | linked_atom | coverage_status | linked_tc_or_gap | rationale |
| --- | --- | --- | --- | --- | --- | --- |
| `CO-001` | `list-composition` | `SRC-001` | `ATOM-001` | `covered` | `TC-WIDGET-SELECTION-TYPES-001` | Source requires dictionary values; exact dictionary content is fixture-specific and must be recorded during calibration. |
| `CO-002` | `single-selection` | `SRC-001` | `ATOM-002` | `covered` | `TC-WIDGET-SELECTION-TYPES-001` | Replacing the first selected value with the second proves one selected value remains. |
| `CO-003` | `list-composition` | `SRC-002` | `ATOM-003` | `covered` | `TC-WIDGET-SELECTION-TYPES-002` | Source requires dictionary values; exact dictionary content is fixture-specific and must be recorded during calibration. |
| `CO-004` | `multi-selection` | `SRC-002` | `ATOM-004` | `covered` | `TC-WIDGET-SELECTION-TYPES-002` | Two selected values are expected simultaneously. |
| `CO-005` | `default-value-visible-empty` | `SRC-003` | `ATOM-005` | `covered` | `TC-WIDGET-SELECTION-TYPES-003` | UI can show absence of a selected or filled value before user input. |
| `CO-006` | `internal-null-interpretation` | `SRC-003` | `ATOM-006` | `unclear` | `GAP-001` | Scope excludes persistence, DB, API and async artifacts, so internal `NULL` interpretation is not observable here. |
| `CO-007` | `persistence-after-save` | `scope-contract.md` | `not_applicable:scope-exclusion` | `not-applicable` | `none_required:scope-excludes-save-flow` | Save-flow and persistence are explicitly out of scope. |
| `CO-008` | `screen-specific-requiredness` | `scope-contract.md` | `not_applicable:scope-exclusion` | `not-applicable` | `none_required:scope-excludes-screen-rules` | Screen-specific requiredness and visibility are explicitly out of scope. |
