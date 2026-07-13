# Анализ V7 live blocker

## Вывод

V7 завершён со статусом `blocked-invalid-output`. Targeted repair и все deterministic full-set gates прошли, но независимый reviewer вернул несовместимый verdict: для testable obligation `OBL-025` использован `invented-coverage`, хотя контракт разрешает только `covered`, `missing` или `incorrect`.

Это терминальный blocker конкретного V7 cycle. Retry, resume и смена transport не выполнялись.

## Что прошло

- Выполнен ровно один dispatcher через verified `codex exec`, contract v2, без fallback.
- Writer работал в отдельной fresh read-only session `019f5ad5-1550-7440-a6ed-cb077e0d8f10`.
- Writer вернул ровно `TC-ACPD-026`, `027`, `028`, `034`; extra/missing sections отсутствуют.
- Runner-owned splice создал draft SHA-256 `17c9bd80c2cff3d19939831f9d42503aebdbd10dc9268d98299896e98dbac23e` и доказал byte-for-byte сохранение остальных `43` секций.
- Structure, obligation `65/65`, evidence, semantic-overlap и execution-oracle quality gates прошли без findings.
- Reviewer запущен в другой fresh read-only session `019f5ad5-d0a4-79b1-ade3-4f05f6b9c449`.

## Что заблокировало цикл

Reviewer сформировал полный ответ с решением `changes-required`, но нарушил явное правило prompt/contract: testable `OBL-025` получил verdict `invented-coverage`. Generic bounded JSON schema допускает общий набор verdict-ов, а status-specific совместимость сейчас проверяется только parser-ом после дорогой reviewer-сессии. Parser правильно отклонил ответ и не создал reviewer sign-off.

Корневая причина — разрыв между generic schema и post-parse contract. Инструкция была явной, но одной текстовой инструкции оказалось недостаточно для гарантии structured output.

## Диагностические findings отклонённого ответа

Отклонённый ответ содержит `F-001..F-005`. Они не являются принятым reviewer-result и не дают право на promotion.

- `F-001` подтверждается draft: splice сохранил `package_id ...-v6` в 43 секциях, а четыре replacement-секции получили `...-v7`. Byte-preservation gate не учитывает обязательную канонизацию cycle metadata.
- `F-003`, `F-004` и `F-005` выглядят предметными: reviewer указал неисполняемый шаг в `TC-ACPD-012`, ненаблюдаемые старые oracle в `TC-ACPD-014/015` и отсутствующие ветвящие предусловия в кейсах предыдущего ФИО. Перед включением в новый repair plan их нужно повторно доказать по prepared evidence.
- `F-002` противоречит переданному evidence: раздел `## DICT-001` в `source-evidence.md` явно содержит значения `Мужчина` и `Женщина`. Этот finding нельзя переносить как подтверждённый дефект draft.

## Архитектурный вывод

Targeted repair решил V6 late-oracle проблему дешевле полной регенерации, но слишком узкий план сохранил унаследованные дефекты и versioned metadata. Следующая итерация не должна просто повторять reviewer. Нужен новый immutable V8 с тремя исправлениями до live:

1. Ограничить generic reviewer schema допустимыми verdict-ами на основании фактических coverage statuses; для пакета только с testable obligations schema не должна принимать `invented-coverage`.
2. Добавить deterministic package-id consistency gate и отделить runner-owned metadata migration от доказательства неизменности test semantics.
3. Передать dictionary values reviewer-у в однозначной структурированной projection и добавить regression, запрещающий утверждать отсутствие значения, которое присутствует в `DICT-001` evidence.

После этого source-backed verification должен определить полный bounded repair set по диагностическим `F-001/F-003/F-004/F-005`; `F-002` исключается, если новые evidence checks снова подтверждают значения справочника.
