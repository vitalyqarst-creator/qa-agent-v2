# Requiredness Oracle Inventory

## Контекст

- `scope_slug`: `application-card-client-personal-data`.
- `scope_contract`: `scope-contract.md`.
- `scope_coverage_gaps`: `scope-coverage-gaps.md`.

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-001` | `SRC-002; column О=Да` | Фамилия | requiredness | Table 4 column О | empty-required-field | always | no | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-REQ-001 | GAP-002 | Как UI проверяет пустую фамилию? | Create atomic candidate TC. | Record marker/message/save effect. |
| `SO-REQ-002` | `SRC-003; column О=Да` | Имя | requiredness | Table 4 column О | empty-required-field | always | no | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-REQ-002 | GAP-002 | Как UI проверяет пустое имя? | Create atomic candidate TC. | Record marker/message/save effect. |
| `SO-REQ-003` | `SRC-006; column О=Да` | Пол | requiredness | Table 4 column О | empty-required-field | always | no | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-REQ-003 | GAP-002 | Как UI проверяет отсутствие пола? | Create atomic candidate TC. | Record marker/message/save effect. |
| `SO-REQ-004` | `SRC-007; column О=Да` | Дата рождения | requiredness | Table 4 column О | empty-required-field | always | no | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-REQ-004 | GAP-002 | Как UI проверяет пустую дату? | Create atomic candidate TC. | Record marker/message/save effect. |
| `SO-REQ-005` | `SRC-009..SRC-011; BSR 68/72/76` | Группа предыдущей ФИО | conditional-requiredness | at least one of three fields | condition-true-empty | changed-FIO=Да | no | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-REQ-005 | GAP-002 | Как UI проверяет полностью пустую группу? | Create one group candidate TC. | Record reaction and save effect. |

## Summary

- total_requiredness_obligations: `5`.
- executable_tc: `0`.
- candidate_tc_required: `5`.
- gap_required: `0`.
- clarification_required: `0`.

## Writer Handoff Rules

- Do not cover requiredness only through valid-value entry or visual assumptions from mockup.
- Create one candidate TC per `SO-REQ-*`; keep group requiredness atomic at group level.
- Preserve the non-required/condition-false paths as positive applicability checks, not negative candidates.
