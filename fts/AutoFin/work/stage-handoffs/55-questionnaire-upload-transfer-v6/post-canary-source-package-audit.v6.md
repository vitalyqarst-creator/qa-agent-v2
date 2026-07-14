# Post-Canary Source-to-Package Audit V6

## Итог

Downstream transfer прошёл: writer сформировал 10 кейсов, reviewer подтвердил 11/11 подготовленных obligations. Однако это не доказывает полноту преобразования исходного ФТ в prepared package. Ручная сверка Final XHTML с package выявила два риска, поэтому benchmark draft нельзя считать production-ready.

## Наблюдения

| id | source | prepared result | risk | required remediation |
| --- | --- | --- | --- | --- |
| `SPA-V6-001` | `BSR 210`: `размер файла не более 40 МБ` | boundary зафиксирован как `41 943 040` и `41 943 041` байт | ФТ не определяет decimal/binary semantics; точное число байт выведено без source-backed convention | запрещать exact byte conversion без явной policy/source fixture; создать gap или использовать подтверждённую convention |
| `SPA-V6-002` | DOCX table 6 row 81 / XHTML row 134 содержит literal `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку` | obligation проверяет только generic `информационное поле отображается` | writer/reviewer не проверяют сохранение literal field text | source-row compiler должен переносить literal display text в atom/oracle либо явно фиксировать, почему это только locator |

## Почему Reviewer Это Не Поймал

Reviewer корректно проверил draft относительно immutable prepared obligations. Raw row semantics не были отдельным независимым входом его контракта. Следовательно, `accepted` означает корректный transfer package → draft, но не гарантирует source → package fidelity.

## Решение

- V6 сохраняется без ручного исправления как честное benchmark evidence.
- Promotion и повтор live запрещены.
- Следующая итерация начинается с deterministic source-to-package fidelity gates и regression fixtures для обоих классов риска.
