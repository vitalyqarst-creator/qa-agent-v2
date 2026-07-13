# Employment Candidate Stop Gate

## Статус

`STOP — candidate blocked before writer`

## Запрещено

- запускать employment writer/reviewer benchmark до уточнения `EMP-BLK-001/002`;
- переносить H13 rows/BSR/dictionaries из `AutoFinPreFinal`;
- считать mockup подтверждением alias между `Социальный статус` и `Тип занятости`;
- выбирать один из конфликтующих dictionary sets по догадке.

## Разрешённый fallback

Current-source `BSR 32` reset-context scope: прямое observable behavior, DOCX/XHTML/PDF parity `pass`, gaps отсутствуют, есть исторический 900-second SDK timeout для сравнения с новым exec pipeline.
