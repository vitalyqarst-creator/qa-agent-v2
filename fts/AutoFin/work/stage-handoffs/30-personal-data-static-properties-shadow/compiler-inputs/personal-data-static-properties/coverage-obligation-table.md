# Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SRC-002.P01` | `ATOM-001` | `field-property` | `surname-visible` | Поле `Фамилия` отображается всегда. | `BSR 47`; XHTML row 57 | `TC-PDSP-001` | `covered` | Static observable property. |
| `OBL-002` | `WP-01` | `SRC-002.P02` | `ATOM-002` | `requiredness` | `surname-required` | Поле `Фамилия` является обязательным. | XHTML row 57; DOCX table 6 row 4 | `TC-PDSP-002` | `covered` | Table property. |
| `OBL-003` | `WP-01` | `SRC-002.P03` | `ATOM-003` | `editability` | `surname-editable` | Поле `Фамилия` доступно для редактирования. | XHTML row 57; DOCX table 6 row 4 | `TC-PDSP-003` | `covered` | Table property. |
| `OBL-004` | `WP-01` | `SRC-002.P04` | `ATOM-004` | `field-property` | `surname-control-type` | Поле `Фамилия` является полем ввода текста. | XHTML row 57; DOCX table 6 row 4 | `TC-PDSP-004` | `covered` | Static control type. |
| `OBL-005` | `WP-01` | `SRC-002.P05` | `ATOM-005` | `field-property` | `surname-value-type` | Поле `Фамилия` принимает строковое значение. | XHTML row 57; DOCX table 6 row 4 | `TC-PDSP-005` | `covered` | Static value type; character restrictions excluded. |
| `OBL-006` | `WP-01` | `SRC-003.P01` | `ATOM-006` | `field-property` | `name-visible` | Поле `Имя` отображается всегда. | `BSR 50`; XHTML row 58 | `TC-PDSP-006` | `covered` | Static observable property. |
| `OBL-007` | `WP-01` | `SRC-003.P02` | `ATOM-007` | `requiredness` | `name-required` | Поле `Имя` является обязательным. | XHTML row 58; DOCX table 6 row 5 | `TC-PDSP-007` | `covered` | Table property. |
| `OBL-008` | `WP-01` | `SRC-003.P03` | `ATOM-008` | `editability` | `name-editable` | Поле `Имя` доступно для редактирования. | XHTML row 58; DOCX table 6 row 5 | `TC-PDSP-008` | `covered` | Table property. |
| `OBL-009` | `WP-01` | `SRC-003.P04` | `ATOM-009` | `field-property` | `name-control-type` | Поле `Имя` является полем ввода текста. | XHTML row 58; DOCX table 6 row 5 | `TC-PDSP-009` | `covered` | Static control type. |
| `OBL-010` | `WP-01` | `SRC-003.P05` | `ATOM-010` | `field-property` | `name-value-type` | Поле `Имя` принимает строковое значение. | XHTML row 58; DOCX table 6 row 5 | `TC-PDSP-010` | `covered` | Static value type; character restrictions excluded. |
| `OBL-011` | `WP-01` | `SRC-004.P01` | `ATOM-011` | `field-property` | `patronymic-visible` | Поле `Отчество` отображается всегда. | `BSR 53`; XHTML row 59 | `TC-PDSP-011` | `covered` | Static observable property. |
| `OBL-012` | `WP-01` | `SRC-004.P02` | `ATOM-012` | `requiredness` | `patronymic-optional` | Поле `Отчество` не является обязательным. | XHTML row 59; DOCX table 6 row 6 | `TC-PDSP-012` | `covered` | Table property. |
| `OBL-013` | `WP-01` | `SRC-004.P03` | `ATOM-013` | `editability` | `patronymic-editable` | Поле `Отчество` доступно для редактирования. | XHTML row 59; DOCX table 6 row 6 | `TC-PDSP-013` | `covered` | Table property. |
| `OBL-014` | `WP-01` | `SRC-004.P04` | `ATOM-014` | `field-property` | `patronymic-control-type` | Поле `Отчество` является полем ввода текста. | XHTML row 59; DOCX table 6 row 6 | `TC-PDSP-014` | `covered` | Static control type. |
| `OBL-015` | `WP-01` | `SRC-004.P05` | `ATOM-015` | `field-property` | `patronymic-value-type` | Поле `Отчество` принимает строковое значение. | XHTML row 59; DOCX table 6 row 6 | `TC-PDSP-015` | `covered` | Static value type; character restrictions excluded. |
