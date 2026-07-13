# Negative Oracle Inventory

## Контекст

- `scope_slug`: `search-clear-context-exec-benchmark-v1`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-NA-001` | `SRC-001` | search context reset | `other` | `none` | BSR 32 defines positive reset effects and introduces no invalid input class. | `not_derived` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-negative-class-in-selected-source` | `none_required:covered` | `none_required` | Do not invent invalid values or error feedback for this scope. | `not_applicable` |

## Summary

- total_negative_obligations: `0`
- executable_tc: `0`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must not derive negative validation cases from BSR 31 or other out-of-scope rows.
- A new negative test requires a source-backed invalid class and observable oracle.
