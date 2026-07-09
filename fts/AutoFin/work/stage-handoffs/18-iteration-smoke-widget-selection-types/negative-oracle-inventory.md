# Negative Oracle Inventory

## Контекст

- `scope_slug`: `iteration-smoke-widget-selection-types`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `none` | Selected rows define positive selection capabilities and default empty state; they do not define invalid input classes. | `not_derived` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-negative-class-in-selected-source` | `none_required:covered` | `none_required` | `Do not create negative TC from this scope unless a later source adds invalid classes.` | `not_applicable` |

## Summary

- total_negative_obligations: `0`
- executable_tc: `0`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must not invent invalid values or UI reactions for the selected rows.
- If reviewer identifies a source-backed invalid class in the selected rows, it must be recorded as a new gap or candidate obligation before executable negative TC creation.
