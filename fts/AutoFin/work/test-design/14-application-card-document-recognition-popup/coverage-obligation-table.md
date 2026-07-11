# Coverage Obligation Table

The table contains the complete prepared-stage obligation projection for the scope. It does not add numeric, length, mask, upload-format, generated-document or role obligations that are absent from row `015`.

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-001` | `WP-01` | `SP-001` | `ATOM-001` | `field-property` | `recognition-button-visible` | Кнопка `Распознать документ` видима всегда. | `BSR 78` | `TC-AFDRP-001` | `covered` | Базовая обязанность видимости. |
| `OBL-002` | `WP-01` | `SP-002` | `ATOM-002` | `action-navigation` | `recognition-popup-opened` | Нажатие `Распознать документ` открывает popup распознавания. | `BSR 79` | `TC-AFDRP-002` | `covered` | Переход состояния сохраняет standard routing. |
| `OBL-003` | `WP-01` | `SP-003` | `ATOM-003` | `list-or-dictionary-composition` | `document-types-listed` | В списке `Тип документа` доступны все и только активные значения `DICT-001`. | `BSR 79`; `DICT-001` | `TC-AFDRP-003` | `covered` | Состав справочника source-backed. |
| `OBL-004` | `WP-01` | `SP-003` | `ATOM-003` | `default-state` | `document-type-default-unknown` | Значение по умолчанию для `Тип документа` не определено источником. | `BSR 79`; `GAP-001` | `GAP-001` | `gap` | Не подменять gap предположением о пустом или выбранном значении. |
| `OBL-005` | `WP-01` | `SP-004` | `ATOM-004` | `file-upload` | `file-container-visible` | В popup отображается контейнер прикрепления файлов с drag-and-drop. | `BSR 79` | `TC-AFDRP-004` | `covered` | File-control obligation сохраняет standard routing. |
| `OBL-006` | `WP-01` | `SP-005` | `ATOM-005` | `field-property` | `popup-buttons-visible` | В popup отображаются кнопки `Отменить` и `Распознать`. | `BSR 80` | `TC-AFDRP-005` | `covered` | Source-defined control set. |
| `OBL-007` | `WP-01` | `SP-006` | `ATOM-006` | `action-navigation` | `popup-cancelled` | Нажатие `Отменить` закрывает popup. | `BSR 81` | `TC-AFDRP-006` | `covered` | Переход состояния сохраняет standard routing. |
| `OBL-008` | `WP-01` | `SP-007` | `ATOM-007` | `action-confirmation` | `missing-file-warning` | Нажатие `Распознать` без файлов показывает предупреждение `Отсутствуют файлы для распознавания`. | `BSR 82` | `TC-AFDRP-007` | `covered` | Точный observable oracle задан источником. |
| `OBL-009` | `WP-01` | `SP-008` | `ATOM-008` | `integration` | `recognition-request-and-fill` | При наличии файла отправляется запрос распознавания и заполняются только fixture-returned поля. | `BSR 83` | `TC-AFDRP-008` | `covered` | Требует fixture/stub request evidence и сохраняет standard routing. |
