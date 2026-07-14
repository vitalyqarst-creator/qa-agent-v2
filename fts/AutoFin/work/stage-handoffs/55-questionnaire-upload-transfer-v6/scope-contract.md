# Scope Contract — Questionnaire Upload Transfer V6

## Контекст

- `ft_slug`: `AutoFin`
- внешний scope: текущий Final, `section-16`, блок `Документы по заявке`.
- внутренний transfer package: информационное поле и desktop-загрузка файла `Анкета клиента`.
- цель: проверить переносимость prepared writer/reviewer на новый medium scope, не переписывая production baseline.

## In Scope

| source_property_id | source statement | requirement code | planned coverage |
| --- | --- | --- | --- |
| `SRC-QUT-001.P01` | Информационное поле отображается всегда. | `BSR 206` | отдельный TC |
| `SRC-QUT-001.P02` | Поле является информационным; `Р = Нет`. | `BSR 207`; DOCX/XHTML row property | отдельный TC |
| `SRC-QUT-002.P01` | Поле добавления файла отображается всегда. | `BSR 208` | отдельный TC |
| `SRC-QUT-002.P02` | Добавление через открытие проводника по кнопке. | `BSR 209` | отдельный TC |
| `SRC-QUT-002.P03` | После добавления отображается имя файла. | `BSR 211` | тот же observable upload result |
| `SRC-QUT-002.P04` | Добавление через Drag and Drop. | `BSR 209` | отдельный TC |
| `SRC-QUT-002.P05` | Допустимые форматы: jpg, png, pdf. | `BSR 210` | один parameterized TC |
| `SRC-QUT-002.P06` | Размер файла не более 40 МБ; точная граница 40 МБ допустима. | `BSR 210` | boundary TC |
| `SRC-QUT-002.P07` | Файл больше 40 МБ отклоняется с точным сообщением ФТ. | `BSR 210` | negative TC |
| `SRC-QUT-002.P08` | Недопустимый формат отклоняется с тем же точным сообщением ФТ. | `BSR 210` | negative TC |
| `SRC-QUT-002.P09` | В каждом типе документа остаётся не более одного файла. | `BSR 210` | count oracle без выдумывания UI-механизма |

## Out Of Scope

- QR/`Прикрепить с телефона` branch из `BSR 209` — отдельный async/integration package.
- фраза `Если файлов несколько... через запятую` из `BSR 211` — не включена: она требует cross-document-type setup, которого нет в этом внутреннем package.
- сохранение в электронном архиве Банка из `BSR 212` — отдельная persistence/observability задача.
- остальные документы, `Тип документа`, `Второй документ`, просмотр/удаление/скачивание.
- production test-case baseline и UI stand.

## Result Boundary

- expected: 11 atomic obligations, 10 unique TC titles, один writer и один independent reviewer.
- promotion: запрещён.
- final target: `fts/AutoFin/test-cases/16-questionnaire-upload-transfer-v6.md` должен оставаться отсутствующим.
