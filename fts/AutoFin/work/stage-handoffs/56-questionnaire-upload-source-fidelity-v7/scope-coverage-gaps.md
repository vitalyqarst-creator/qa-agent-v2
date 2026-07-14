# Scope Coverage Gaps — Questionnaire Upload Transfer V7

## Контекст

- `scope_slug`: `questionnaire-upload-transfer-v7`
- Основной FT: `source/FT4AutoFinFinal.docx`

## Summary

- Найдено gaps: `1`
- Blocking gaps: `0`
- Активный downstream: `ft-test-case-reviewer` для gap review.

## GAP-QUT-001

**FT Reference:** `BSR 210; SRC-QUT-002.P06; DOCX table 6 row 82; XHTML row 135; размер файла не более 40 МБ`

**Problem:** ФТ не определяет, означает ли `40 МБ` decimal `MB` или binary `MiB`; точный размер boundary fixture в байтах нельзя вывести без дополнительной policy.

**Impact:** `non-blocking`

**Handling:** Сохранить `ATOM-008` / `OBL-QUT-008` как отдельный gap; не создавать точный boundary TC и не преобразовывать величину в байты. Закрыть только по source-backed policy или подтвержденной fixture convention.

## Что Можно Покрывать Несмотря На Gap

- 10 остальных obligations, включая заведомо oversized fixture `50 МБ`, остаются testable.

## Что Нельзя Домысливать

- точное число байт для `40 МБ` и just-over boundary;
- UI-механизм реакции на второй файл сверх source-backed count `не более одного`.
