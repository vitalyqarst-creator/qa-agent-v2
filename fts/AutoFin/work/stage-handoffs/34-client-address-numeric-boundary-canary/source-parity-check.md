# Source Parity Check

## Контекст

- Активный комплект: `FT4AutoFinFinal.docx`, `FT4AutoFinFinal.xhtml`, `FT4AutoFinFinal.pdf`.
- Канонический полный parity artifact: `work/stage-handoffs/02-application-card-client-addresses-contacts/source-parity-check.md`.
- Canary-срез: Table 4 address rows, `BSR 116`, `BSR 124`, `BSR 126`, `BSR 151`, `BSR 153`.

## Результат

| проверка | результат |
| --- | --- |
| XHTML доступен и соответствует выбранному Final stem | `pass` |
| PDF подтверждает непрерывность адресных строк и BSR-кодов | `pass` |
| Все пять BSR сохранены в source-row inventory и normalization | `pass` |
| PDF используется только для structural cross-check | `pass` |
| Blocking parity issue | `none` |

## Ограничения

- Значение ограничения извлекается из XHTML/DOCX-backed normalization; PDF не добавляет новое поведение.
- Если live draft добавит negative feedback, которого нет в источнике, stop-gate считается нарушенным.
