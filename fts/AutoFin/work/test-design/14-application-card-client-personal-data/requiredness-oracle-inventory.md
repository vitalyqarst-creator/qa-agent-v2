## Requiredness Oracle Inventory

| scope_obligation_id | linked_atom | source_ref | field_or_group | required_when | oracle_status | decision | planned_tc_or_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-001` | `ATOM-003` | `SRC-002; column О=Да` | Фамилия | `always` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-022` |
| `SO-REQ-002` | `ATOM-008` | `SRC-003; column О=Да` | Имя | `always` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-023` |
| `SO-REQ-003` | `ATOM-019` | `SRC-006; column О=Да` | Пол | `always` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-024` |
| `SO-REQ-004` | `ATOM-021` | `SRC-007; column О=Да` | Дата рождения | `always` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-025` |
| `SO-REQ-005` | `ATOM-031; ATOM-036; ATOM-041` | `SRC-009..SRC-011; BSR 68/72/76` | Группа предыдущей ФИО | `Клиент менял ФИО=Да` | `ui-calibration-required` | `candidate_tc_required` | `TC-ACPD-041` |
