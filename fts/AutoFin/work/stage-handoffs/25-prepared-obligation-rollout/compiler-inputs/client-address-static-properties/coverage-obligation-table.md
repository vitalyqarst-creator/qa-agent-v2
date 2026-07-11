# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-001` | `ATOM-001` | `field-property` | `block-visible` | Блок `Адреса клиента` отображается в заявке. | `SRC-001`; `DOCX row 032` | `TC-CASP-001` | `covered` | Eval projection preserves the parent atom without adding behavior. |
| `OBL-002` | `WP-01` | `SRC-002.P01` | `ATOM-002` | `field-property` | `registration-address-visible` | `Адрес регистрации` видим всегда. | `BSR 107`; `DOCX row 033` | `TC-CASP-002` | `covered` | Static observable field property. |
| `OBL-003` | `WP-01` | `SRC-003.P01` | `ATOM-003` | `field-property` | `manual-toggle-visible` | Переключатель `Адрес регистрации / Ввести вручную` видим всегда. | `BSR 113`; `DOCX row 034` | `TC-CASP-003` | `covered` | Static observable field property. |
| `OBL-004` | `WP-01` | `SRC-003.P02` | `ATOM-004` | `default-state` | `manual-toggle-default-no` | Значение переключателя ручного ввода по умолчанию равно `Нет`. | `BSR 114`; `DOCX row 034` | `TC-CASP-004` | `covered` | Static observable default. |
| `OBL-005` | `WP-01` | `SRC-014.P01` | `ATOM-005` | `field-property` | `same-address-toggle-visible` | Признак совпадения фактического адреса с адресом регистрации видим всегда. | `BSR 130`; `DOCX row 045` | `TC-CASP-005` | `covered` | Static observable field property. |
| `OBL-006` | `WP-01` | `SRC-014.P02` | `ATOM-006` | `default-state` | `same-address-default-yes` | Значение признака совпадения адресов по умолчанию равно `Да`. | `BSR 131`; `DOCX row 045` | `TC-CASP-006` | `covered` | Static observable default. |
