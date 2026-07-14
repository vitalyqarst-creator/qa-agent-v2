# Scope Contract — Questionnaire Upload Transfer V7

## Контекст

- `ft_slug`: `AutoFin`
- `scope_slug`: `questionnaire-upload-transfer-v7`
- внешний scope: текущий Final, `section-16`, блок `Документы по заявке`.
- внутренний package: информационный literal и desktop-загрузка файла `Анкета клиента`.
- режим: offline source-to-package fidelity; без writer/reviewer live и без изменения baseline.

## In Scope

| source_property_id | source statement | requirement code | planned outcome |
| --- | --- | --- | --- |
| `SRC-QUT-001.P01` | `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку` отображается всегда. | `BSR 206` | `TC-QUT-001`; literal fidelity binding |
| `SRC-QUT-001.P02` | Поле является информационным; `Р = Нет`. | `BSR 207` | `TC-QUT-002` |
| `SRC-QUT-002.P01` | Поле добавления файла отображается всегда. | `BSR 208` | `TC-QUT-003` |
| `SRC-QUT-002.P02` | Добавление через открытие проводника по кнопке. | `BSR 209` | `TC-QUT-004` |
| `SRC-QUT-002.P03` | После добавления отображается имя файла. | `BSR 211` | `TC-QUT-004` |
| `SRC-QUT-002.P04` | Добавление через Drag and Drop. | `BSR 209` | `TC-QUT-005` |
| `SRC-QUT-002.P05` | Допустимые форматы: jpg, png, pdf. | `BSR 210` | `TC-QUT-006` |
| `SRC-QUT-002.P06` | `размер файла не более 40 МБ`; exact byte convention не задана. | `BSR 210` | `GAP-QUT-001`; obligation сохранен |
| `SRC-QUT-002.P07` | Файл больше 40 МБ отклоняется с точным сообщением ФТ. | `BSR 210` | `TC-QUT-007`; source-unit-only fixture |
| `SRC-QUT-002.P08` | Недопустимый формат отклоняется с тем же точным сообщением ФТ. | `BSR 210` | `TC-QUT-008` |
| `SRC-QUT-002.P09` | В каждом типе документа остаётся не более одного файла. | `BSR 210` | `TC-QUT-009` |

## Out Of Scope

- QR/`Прикрепить с телефона` branch из `BSR 209`.
- cross-document-type вывод нескольких имен из `BSR 211`.
- сохранение в электронном архиве Банка из `BSR 212`.
- остальные типы документов, просмотр/удаление/скачивание, production baseline и UI stand.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-QUT-01` | literal + desktop file upload | `SRC-QUT-001; SRC-QUT-002` | `BSR 206-211`, кроме явно исключенных branches | explicit `ATOM -> OBL -> TC/GAP` + fidelity bindings | 11 obligations, 9 planned TC, 1 gap | `no` |

## Result Boundary

- все 11 V6 source obligations сохранены: 10 testable и 1 gap obligation;
- package compile допустим только после deterministic fidelity gate;
- `test-cases/16-questionnaire-upload-transfer-v7.md` должен оставаться отсутствующим;
- V6 package/draft остаются immutable evidence и не изменяются.
