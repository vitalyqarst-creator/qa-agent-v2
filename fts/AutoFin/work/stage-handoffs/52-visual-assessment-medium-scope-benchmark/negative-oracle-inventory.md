# Negative Oracle Inventory

## Контекст

- `scope_slug`: `visual-assessment-medium-scope-benchmark`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-000` | `BSR 311-317; SRC-001-SRC-052` | selected visual-assessment scope | `other` | `not_applicable` | Source defines selection and requiredness, but no invalid format/value class. | `not_derived` | `not_applicable` | `FT` | `source-backed` | `not_applicable` | `not_applicable:no-source-backed-invalid-input-class` | `none_required:covered` | `none_required` | Do not create synthetic negative input classes. | `not_applicable` |

No format, length, date, e-mail, numeric, character-class or not-in-list invalid-input obligations are stated in the selected scope. Minimum selection and mandatory comment are classified only in `requiredness-oracle-inventory.md`.

## Summary

- total_negative_obligations: `0`
- executable_tc: `0`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Do not invent negative input classes for dictionary values or comment text.
- Preserve requiredness candidates from the separate requiredness inventory.
