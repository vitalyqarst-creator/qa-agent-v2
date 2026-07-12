# Negative Oracle Inventory

## Контекст

- `scope_slug`: `application-card-client-personal-data`.
- `scope_contract`: `scope-contract.md`.
- `scope_coverage_gaps`: `scope-coverage-gaps.md`.

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-001` | `SRC-002; BSR 48` | Фамилия | text-symbols | digits | only letters and `-` | `Иванов2` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-001 | GAP-001 | Как UI отклоняет цифру? | Create atomic candidate TC. | Record filtering/message/save effect. |
| `SO-NEG-002` | `SRC-002; BSR 48` | Фамилия | text-symbols | special-chars | only letters and `-` | `Иванов@` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-002 | GAP-001 | Как UI отклоняет символ? | Create atomic candidate TC. | Record filtering/message/save effect. |
| `SO-NEG-003` | `SRC-003; BSR 51` | Имя | text-symbols | digits | only letters and `-` | `Иван2` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-003 | GAP-001 | Как UI отклоняет цифру? | Create atomic candidate TC. | Record filtering/message/save effect. |
| `SO-NEG-004` | `SRC-003; BSR 51` | Имя | text-symbols | special-chars | only letters and `-` | `Иван@` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-004 | GAP-001 | Как UI отклоняет символ? | Create atomic candidate TC. | Record filtering/message/save effect. |
| `SO-NEG-005` | `SRC-004; BSR 54` | Отчество | text-symbols | digits | only letters and `-` | `Иванович2` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-005 | GAP-001 | Как UI отклоняет цифру? | Create atomic candidate TC. | Record filtering/message/save effect. |
| `SO-NEG-006` | `SRC-004; BSR 54` | Отчество | text-symbols | special-chars | only letters and `-` | `Иванович@` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-006 | GAP-001 | Как UI отклоняет символ? | Create atomic candidate TC. | Record filtering/message/save effect. |
| `SO-NEG-007` | `SRC-007; BSR 61` | Дата рождения | date-validity-window | under-18 | date cannot be later than today minus 18 years | `today-18y+1d` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-007 | GAP-001 | Как UI отклоняет дату младше 18 лет? | Create boundary candidate TC. | Record message/transition/save effect. |
| `SO-NEG-008` | `SRC-007; BSR 62` | Дата рождения | date-validity-window | future-date | date cannot exceed today | `tomorrow` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-008 | GAP-001 | Как UI отклоняет будущую дату? | Create atomic candidate TC. | Record priority if multiple rules fire. |
| `SO-NEG-009` | `SRC-007; BSR 63` | Дата рождения | date-validity-window | older-than-100 | date cannot be earlier than today minus 100 years | `today-100y-1d` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-009 | GAP-001 | Как UI отклоняет дату старше 100 лет? | Create boundary candidate TC. | Record message/transition/save effect. |
| `SO-NEG-010` | `SRC-009; BSR 67` | Предыдущая фамилия | text-symbols | digits | only letters and `-` | `Петрова2` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-010 | GAP-001 | Как UI отклоняет цифру? | Create atomic candidate TC. | condition changed-FIO=Да |
| `SO-NEG-011` | `SRC-009; BSR 67` | Предыдущая фамилия | text-symbols | special-chars | only letters and `-` | `Петрова@` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-011 | GAP-001 | Как UI отклоняет символ? | Create atomic candidate TC. | condition changed-FIO=Да |
| `SO-NEG-012` | `SRC-010; BSR 71` | Предыдущее имя | text-symbols | digits | only letters and `-` | `Анна2` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-012 | GAP-001 | Как UI отклоняет цифру? | Create atomic candidate TC. | condition changed-FIO=Да |
| `SO-NEG-013` | `SRC-010; BSR 71` | Предыдущее имя | text-symbols | special-chars | only letters and `-` | `Анна@` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-013 | GAP-001 | Как UI отклоняет символ? | Create atomic candidate TC. | condition changed-FIO=Да |
| `SO-NEG-014` | `SRC-011; BSR 75` | Предыдущее отчество | text-symbols | digits | only letters and `-` | `Ивановна2` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-014 | GAP-001 | Как UI отклоняет цифру? | Create atomic candidate TC. | condition changed-FIO=Да |
| `SO-NEG-015` | `SRC-011; BSR 75` | Предыдущее отчество | text-symbols | special-chars | only letters and `-` | `Ивановна@` | no | not_found | ui-calibration-required | candidate_tc_required | candidate:SO-NEG-015 | GAP-001 | Как UI отклоняет символ? | Create atomic candidate TC. | condition changed-FIO=Да |

## Summary

- total_negative_obligations: `15`.
- executable_tc: `0`.
- candidate_tc_required: `15`.
- gap_required: `0`.
- clarification_required: `0`.

## Writer Handoff Rules

- Carry every `SO-NEG-*` until mapped to a separate `ATOM-*` and calibration candidate TC.
- Candidate cases use `Статус тест-кейса: candidate-ui-calibration` and `Статус oracle: ui-calibration-required`.
- Do not invent exact message, highlight, filtering or save/transition result.
- Keep valid boundary acceptance cases separate from invalid candidates.
