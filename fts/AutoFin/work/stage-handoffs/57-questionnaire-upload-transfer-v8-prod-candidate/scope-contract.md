# Scope Contract — Questionnaire Upload Transfer V8 Prod Candidate

## Контекст

- `ft_slug`: `AutoFin`
- `scope_slug`: `questionnaire-upload-transfer-v8-prod-candidate`
- внешний scope: текущий Final, `section-16`, блок `Документы по заявке`.
- внутренний package: информационный literal и desktop-загрузка файла `Анкета клиента`.
- режим: immutable production-candidate; до успешного gap review только offline validation.

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
| `SRC-QUT-002.P06` | `размер файла не более 40 МБ`; exact byte convention не задана. | `BSR 210` | `GAP-QUT-001`; obligation сохранена |
| `SRC-QUT-002.P07` | Файл больше 40 МБ отклоняется с точным сообщением ФТ. | `BSR 210` | `TC-QUT-007`; source-unit-only fixture |
| `SRC-QUT-002.P08` | Недопустимый формат отклоняется с тем же точным сообщением ФТ. | `BSR 210` | `TC-QUT-008` |
| `SRC-QUT-002.P09` | В каждом типе документа остаётся не более одного файла. | `BSR 210` | `TC-QUT-009` |

## Out Of Scope

- QR/`Прикрепить с телефона` branch из `BSR 209`.
- cross-document-type вывод нескольких имён из `BSR 211`.
- сохранение в электронном архиве Банка из `BSR 212`.
- остальные типы документов, просмотр/удаление/скачивание и UI stand.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-QUT-01` | literal + desktop file upload | `SRC-QUT-001; SRC-QUT-002` | `BSR 206–211`, кроме явно исключённых branches | explicit `ATOM -> OBL -> TC/GAP` + fidelity bindings | 11 obligations, 9 planned TC, 1 gap | `no` |

## Result Boundary

- сохранить 11 obligations: 10 testable и 1 gap obligation;
- `GAP-QUT-001` разрешено переносить downstream как открытый non-blocking gap;
- exact-boundary/just-over byte TC запрещены до source-backed convention;
- live writer/reviewer разрешаются только после повторного passed gap review и validate-only;
- promotion остаётся off до отдельного quality/promotion gate;
- `test-cases/16-questionnaire-upload-transfer-v8-prod-candidate.md` до promotion должен отсутствовать.
