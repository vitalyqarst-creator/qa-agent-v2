## Negative Oracle Inventory

| scope_obligation_id | linked_atom | source_ref | field_or_block | negative_class | representative_invalid_value | oracle_status | decision | planned_tc_or_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-001` | `ATOM-005` | `SRC-002; BSR 48` | Фамилия | `digits` | `Иванов2` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-016` |
| `SO-NEG-002` | `ATOM-005` | `SRC-002; BSR 48` | Фамилия | `special-chars` | `Иванов@` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-017` |
| `SO-NEG-003` | `ATOM-010` | `SRC-003; BSR 51` | Имя | `digits` | `Иван2` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-018` |
| `SO-NEG-004` | `ATOM-010` | `SRC-003; BSR 51` | Имя | `special-chars` | `Иван@` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-019` |
| `SO-NEG-005` | `ATOM-015` | `SRC-004; BSR 54` | Отчество | `digits` | `Иванович2` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-020` |
| `SO-NEG-006` | `ATOM-015` | `SRC-004; BSR 54` | Отчество | `special-chars` | `Иванович@` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-021` |
| `SO-NEG-007` | `ATOM-022` | `SRC-007; BSR 61` | Дата рождения | `under-18` | `D-18y+1d` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-025` |
| `SO-NEG-008` | `ATOM-023` | `SRC-007; BSR 62` | Дата рождения | `future-date` | `D+1 calendar day` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-026` |
| `SO-NEG-009` | `ATOM-024` | `SRC-007; BSR 63` | Дата рождения | `older-than-100` | `D-100y-1d` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-027` |
| `SO-NEG-010` | `ATOM-030` | `SRC-009; BSR 67` | Предыдущая фамилия | `digits` | `Петрова2` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-034` |
| `SO-NEG-011` | `ATOM-030` | `SRC-009; BSR 67` | Предыдущая фамилия | `special-chars` | `Петрова@` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-035` |
| `SO-NEG-012` | `ATOM-035` | `SRC-010; BSR 71` | Предыдущее имя | `digits` | `Анна2` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-038` |
| `SO-NEG-013` | `ATOM-035` | `SRC-010; BSR 71` | Предыдущее имя | `special-chars` | `Анна@` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-039` |
| `SO-NEG-014` | `ATOM-040` | `SRC-011; BSR 75` | Предыдущее отчество | `digits` | `Ивановна2` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-043` |
| `SO-NEG-015` | `ATOM-040` | `SRC-011; BSR 75` | Предыдущее отчество | `special-chars` | `Ивановна@` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-044` |
