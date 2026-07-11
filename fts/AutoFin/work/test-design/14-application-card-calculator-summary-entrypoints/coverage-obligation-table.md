# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SP-001` | `ATOM-001` | `field-property` | `visibility-always` | Виджет `Краткая информация с калькулятора` отображается в карточке заявки. | `SRC-001`; `BSR 35` | `TC-ACCS-001` | `covered` | Прямая visibility obligation. |
| `OBL-002` | `WP-01` | `SP-002` | `ATOM-002` | `table-list` | `calculator-summary-fields` | Виджет отображает пять перечисленных параметров калькулятора. | `SRC-001`; `BSR 36` | `TC-ACCS-002` | `covered` | Состав полей явно задан ФТ. |
| `OBL-003` | `WP-01` | `SP-003` | `ATOM-003` | `action-navigation` | `widget-navigation-target-opened` | Нажатие виджета открывает этап `Кредитный калькулятор`. | `SRC-001`; `BSR 37` | `TC-ACCS-003` | `covered` | `GAP-001` исключает внутреннее поведение калькулятора. |
| `OBL-004` | `WP-01` | `SP-004` | `ATOM-004` | `action-navigation` | `calculator-window-opened` | Кнопка `Кредитный калькулятор` открывает окно `Кредитный калькулятор`. | `SRC-002`; `BSR 38` | `TC-ACCS-004` | `covered` | Отдельная observable navigation obligation. |
| `OBL-005` | `WP-01` | `SP-005` | `ATOM-005` | `expected-result` | `calculator-prefill-mapping-unknown` | Точный состав и соответствие предзаполненных данных данным заявки не определены доступным ФТ. | `SRC-002`; `BSR 38`; `GAP-001` | `GAP-001` | `gap` | Не объявлять prefill mapping исполнимым покрытием без внешнего ФТ `Калькулятор`. |
