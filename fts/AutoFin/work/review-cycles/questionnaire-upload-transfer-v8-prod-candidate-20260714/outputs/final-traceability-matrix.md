# Final Traceability Matrix

| traceability_ref | atom_id | obligation_id | source_ref | coverage_status | covered_by_tc | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `TR-QUT-001` | `ATOM-001` | `OBL-QUT-001` | `SRC-QUT-001.P01; BSR 206` | `covered` | `TC-QUT-001` | Буквальный информационный текст сохранён. |
| `TR-QUT-002` | `ATOM-002` | `OBL-QUT-002` | `SRC-QUT-001.P02; BSR 207` | `covered` | `TC-QUT-002` | Проверен запрет ручного редактирования. |
| `TR-QUT-003` | `ATOM-003` | `OBL-QUT-003` | `SRC-QUT-002.P01; BSR 208` | `covered` | `TC-QUT-003` | Проверено постоянное отображение поля. |
| `TR-QUT-004` | `ATOM-004` | `OBL-QUT-004` | `SRC-QUT-002.P02; BSR 209` | `covered` | `TC-QUT-004` | Добавление через проводник. |
| `TR-QUT-005` | `ATOM-005` | `OBL-QUT-005` | `SRC-QUT-002.P03; BSR 211` | `covered` | `TC-QUT-004` | Отображение точного имени выбранного файла. |
| `TR-QUT-006` | `ATOM-006` | `OBL-QUT-006` | `SRC-QUT-002.P04; BSR 209; BSR 211` | `covered` | `TC-QUT-005` | Drag and Drop и отображение имени. |
| `TR-QUT-007` | `ATOM-007` | `OBL-QUT-007` | `SRC-QUT-002.P05; BSR 210` | `covered` | `TC-QUT-006` | JPG, PNG и PDF проверяются в чистых итерациях. |
| `TR-QUT-008` | `ATOM-008` | `OBL-QUT-008` | `SRC-QUT-002.P06; BSR 210` | `unclear` | `unclear:GAP-QUT-001` | `GAP-QUT-001` сохранён: точная byte-граница не определена ФТ. |
| `TR-QUT-009` | `ATOM-009` | `OBL-QUT-009` | `SRC-QUT-002.P07; BSR 210` | `covered` | `TC-QUT-007` | Portable oversize 50 МБ и точный текст ошибки. |
| `TR-QUT-010` | `ATOM-010` | `OBL-QUT-010` | `SRC-QUT-002.P08; BSR 210` | `covered` | `TC-QUT-008` | Недопустимый TXT и точный текст ошибки. |
| `TR-QUT-011` | `ATOM-011` | `OBL-QUT-011` | `SRC-QUT-002.P09; BSR 210` | `covered` | `TC-QUT-009` | Утверждается только наблюдаемое ограничение «не более одного файла». |
