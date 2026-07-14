# Atomic Requirements Ledger — Questionnaire Upload Transfer V8 Prod Candidate

## Ledger

| atom_id | package_id | source_property_id | source_ref | atomic_statement | property_type | coverage_status | covered_by_tc | planned_tc_or_gap | gap_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `WP-QUT-01` | `SRC-QUT-001.P01` | `BSR 206` | Буквальный текст `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку` отображается всегда. | `visibility` | `covered` | `TC-QUT-001` | `TC-QUT-001` | `none_required:covered` |
| `ATOM-002` | `WP-QUT-01` | `SRC-QUT-001.P02` | `BSR 207` | Информационное поле не допускает ручного редактирования своего текста. | `field-property` | `covered` | `TC-QUT-002` | `TC-QUT-002` | `none_required:covered` |
| `ATOM-003` | `WP-QUT-01` | `SRC-QUT-002.P01` | `BSR 208` | Поле добавления файла `Анкета клиента` отображается всегда. | `visibility` | `covered` | `TC-QUT-003` | `TC-QUT-003` | `none_required:covered` |
| `ATOM-004` | `WP-QUT-01` | `SRC-QUT-002.P02` | `BSR 209` | Документ можно добавить через открытие проводника по кнопке. | `file-upload` | `covered` | `TC-QUT-004` | `TC-QUT-004` | `none_required:covered` |
| `ATOM-005` | `WP-QUT-01` | `SRC-QUT-002.P03` | `BSR 211` | После добавления документа отображается имя прикреплённого файла. | `file-upload-result` | `covered` | `TC-QUT-004` | `TC-QUT-004` | `none_required:covered` |
| `ATOM-006` | `WP-QUT-01` | `SRC-QUT-002.P04` | `BSR 209` | Документ можно добавить через Drag and Drop. | `file-upload` | `covered` | `TC-QUT-005` | `TC-QUT-005` | `none_required:covered` |
| `ATOM-007` | `WP-QUT-01` | `SRC-QUT-002.P05` | `BSR 210` | Поле принимает файлы форматов jpg, png и pdf. | `equivalence` | `covered` | `TC-QUT-006` | `TC-QUT-006` | `none_required:covered` |
| `ATOM-008` | `WP-QUT-01` | `SRC-QUT-002.P06` | `BSR 210; GAP-QUT-001` | Точное граничное значение для `размер файла не более 40 МБ` нельзя задать без byte convention. | `boundary` | `gap` | `GAP-QUT-001` | `GAP-QUT-001` | `GAP-QUT-001` |
| `ATOM-009` | `WP-QUT-01` | `SRC-QUT-002.P07` | `BSR 210` | Ограничение `размер файла не более 40 МБ`: файл размером 50 МБ не загружается и отображается точный текст ошибки. | `negative-oracle` | `covered` | `TC-QUT-007` | `TC-QUT-007` | `none_required:covered` |
| `ATOM-010` | `WP-QUT-01` | `SRC-QUT-002.P08` | `BSR 210` | Файл недопустимого формата не загружается, отображается точный текст ошибки из ФТ. | `negative-oracle` | `covered` | `TC-QUT-008` | `TC-QUT-008` | `none_required:covered` |
| `ATOM-011` | `WP-QUT-01` | `SRC-QUT-002.P09` | `BSR 210` | После попытки добавить второй файл в типе документа остаётся не более одного файла. | `file-cardinality` | `covered` | `TC-QUT-009` | `TC-QUT-009` | `none_required:covered` |
