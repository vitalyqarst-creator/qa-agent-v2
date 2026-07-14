**FT Reference:** `BSR 210; SRC-QUT-002.P06; DOCX table 6 row 82; XHTML row 135; размер файла не более 40 МБ`

**Problem:** ФТ не определяет, означает ли `40 МБ` decimal `MB` или binary `MiB`; точный размер boundary fixture в байтах нельзя вывести без дополнительной policy.

**Impact:** `non-blocking`

**Handling:** Сохранить `ATOM-008` / `OBL-QUT-008` как отдельный gap; не создавать точный boundary TC и не преобразовывать величину в байты. Закрыть только по source-backed policy или подтвержденной fixture convention.
