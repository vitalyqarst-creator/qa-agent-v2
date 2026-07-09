# Requiredness Oracle Inventory

## Контекст

- `scope_slug`: `iteration-smoke-widget-selection-types`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `not_present` | `none` | `not_applicable` | `not_applicable` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-requiredness-in-selected-source` | `none_required:covered` | `none_required` | `Do not create requiredness TC from this scope unless a later source adds requiredness.` | `not_applicable` |

## Summary

- total_requiredness_obligations: `0`
- executable_tc: `0`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must not treat selected positive/default widget constraints as field requiredness.
- Writer must not cover requiredness through valid value selection for this scope.
