# Requiredness Oracle Inventory

## Контекст

- `scope_slug`: `visual-assessment-medium-scope-benchmark`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-001` | `BSR 316; SRC-003` | `Параметры визуальной оценки` | `conditional-requiredness` | `Должно быть выбрано хотя бы одно значение` | `condition-true-empty` | `Визуальная информация = Да` | `no` | `partial` | `FT` | `ui-calibration-required` | `candidate_tc_required` | `TC-VAMB-007` | `none_required:covered` | `none_required` | Create candidate TC; do not invent message/highlight/blocked action. | Record actual marker/message/highlight/transition or save effect during UI calibration. |
| `SO-REQ-002` | `BSR 317; SRC-009/019/024/030/036/043/050` | comment for selected `Другое` | `conditional-requiredness` | `поле ввода текста, обязательное для заполнения` | `condition-true-empty` | `Другое selected` | `no` | `partial` | `FT` | `ui-calibration-required` | `candidate_tc_required` | `TC-VAMB-009` | `none_required:covered` | `none_required` | Create candidate TC separate from display TC; preserve generic calibration expected result. | Record actual empty-comment reaction during UI calibration. |

## Summary

- total_requiredness_obligations: `2`
- executable_tc: `0`
- candidate_tc_required: `2`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Carry both `SO-REQ-*` into package evidence and the related TC metadata.
- Use `Статус oracle: ui-calibration-required` and `Статус тест-кейса: candidate-ui-calibration`.
- Do not assert exact UI messages, colors, filtering, clearing, disabled buttons, persistence or blocked transitions.
- Candidate requiredness does not block the FT-first draft and is not a substitute for UI automation preparation.
