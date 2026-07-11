# Source Table Normalization

| source_property_id | source_row_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SP-001` | `SRC-001` | `WP-01` | Краткая информация с калькулятора | `visibility` | `always` | Виджет краткой информации виден всегда. | `BSR 43` | PDF page 15; DOCX row 002 | `high` | `none_required:covered` | `ATOM-001` |
| `SP-002` | `SRC-001` | `WP-01` | Краткая информация с калькулятора | `summary-content` | `calculator-stage-data-exists` | Виджет отображает параметры `Сумма кредита, Р`; `VIN`; `Ставка, %`; `Платеж в месяц, Р`; `Срок, мес.`. | `BSR 44` | PDF page 15; DOCX row 002 | `high` | `none_required:covered` | `ATOM-002` |
| `SP-003` | `SRC-001` | `WP-01` | Краткая информация с калькулятора | `widget-action` | `user-clicks-widget` | Нажатие на виджет выполняет переход на этап `Кредитный калькулятор`. | `BSR 45` | PDF page 15; DOCX row 002 | `high` | `GAP-001` for external calculator behavior | `ATOM-003` |
| `SP-004` | `SRC-002` | `WP-01` | Кредитный калькулятор | `button-action` | `user-clicks-button` | Нажатие на кнопку открывает окно `Кредитный калькулятор`. | `BSR 46` | PDF page 15; DOCX row 003 | `high` | `none_required:covered` | `ATOM-004` |
| `SP-005` | `SRC-002` | `WP-01` | Кредитный калькулятор | `prefill-presence` | `window-just-opened` | До пользовательского ввода в окне присутствуют предзаполненные данные по заявке. | `BSR 46` | PDF page 15; DOCX row 003 | `high` | `GAP-001` for exhaustive field set and mapping | `ATOM-005` |
| `SP-006` | `SRC-002` | `WP-01` | Кредитный калькулятор | `prefill-mapping` | `exact-field-mapping` | Состав полей и точный mapping к данным заявки в доступном ФТ не определены. | `BSR 46`; `GAP-001` | PDF page 15; DOCX row 003 | `high` | `GAP-001` | `ATOM-006` |
