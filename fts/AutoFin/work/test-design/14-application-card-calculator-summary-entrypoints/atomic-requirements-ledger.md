# Atomic Requirements Ledger

| atom_id | package_id | source_property_id | req_id | source_row_id | atomic_statement | coverage_status | covered_by_tc | planned_tc_or_gap | gap_id | constraint_gap_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `WP-01` | `SP-001` | `BSR 35` | `SRC-001` | Виджет `Краткая информация с калькулятора` виден в карточке заявки всегда. | `covered` | `TC-ACCS-001` | `TC-ACCS-001` | `none_required:covered` | `-` |
| `ATOM-002` | `WP-01` | `SP-002` | `BSR 36` | `SRC-001` | Виджет отображает краткую информацию с этапа `Кредитный калькулятор`: `Сумма кредита, Р`, `VIN`, `Ставка, %`, `Платеж в месяц, Р`, `Срок, мес.`. | `covered` | `TC-ACCS-002` | `TC-ACCS-002` | `none_required:covered` | `-` |
| `ATOM-003` | `WP-01` | `SP-003` | `BSR 37` | `SRC-001` | При нажатии на виджет выполняется переход на этап `Кредитный калькулятор`. | `covered` | `TC-ACCS-003` | `TC-ACCS-003` | `none_required:covered` | `GAP-001` |
| `ATOM-004` | `WP-01` | `SP-004` | `BSR 38` | `SRC-002` | При нажатии на кнопку `Кредитный калькулятор` открывается окно `Кредитный калькулятор` с предзаполненными данными по заявке. | `covered` | `TC-ACCS-004` | `TC-ACCS-004` | `none_required:covered` | `GAP-001` |
