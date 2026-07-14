# Scope Coverage Gaps — Questionnaire Upload Transfer V8 Prod Candidate

## Контекст

- `scope_slug`: `questionnaire-upload-transfer-v8-prod-candidate`
- Основной FT: `source/FT4AutoFinFinal.docx`

## Summary

- Найдено gaps: `1`
- Blocking gaps: `0`
- Активный downstream: независимый `scope_gap_review`.

## GAP-QUT-001

**FT Reference:** `BSR 210; SRC-QUT-002.P06; DOCX table 6 row 82; XHTML row 135; размер файла не более 40 МБ`

**Problem:** ФТ не определяет, означает ли `40 МБ` decimal `MB` или binary `MiB`; точный размер boundary fixture в байтах нельзя вывести без source-backed policy.

**Impact:** `non-blocking`

**Handling:** Сохранить `ATOM-008` / `OBL-QUT-008` как отдельный gap; не создавать exact-boundary/just-over byte TC. Writer и reviewer могут обработать остальные 10 testable obligations при явном сохранении этого ограничения.

## Что Можно Покрывать Несмотря На Gap

- 10 testable obligations, включая заведомо oversized fixture `50 МБ`.

## Что Нельзя Домысливать

- точное число байт для `40 МБ` и just-over boundary;
- UI-механизм реакции на второй файл сверх source-backed count `не более одного`.
