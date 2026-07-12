# Dependency Matrix

| dependency_id | package_id | controlling_field | controlling_value | dependent_element | expected_state | linked_atoms | linked_tc_or_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DEP-001` | `WP-01` | `Клиент менял ФИО` | `Да` | `Предыдущая фамилия`; `Предыдущее имя`; `Предыдущее отчество` | `visible` | `ATOM-016` | `TC-ACPD-011` |
| `DEP-002` | `WP-01` | `Клиент менял ФИО` | `Нет` | `Предыдущая фамилия`; `Предыдущее имя`; `Предыдущее отчество` | `not visible` | `ATOM-017` | `TC-ACPD-012` |
| `DEP-003` | `WP-01` | `ФИО via DaData` | `selected suggestion` | `Пол` | `updated from DaData` | `ATOM-011` | `TC-ACPD-007`; `GAP-001` |
