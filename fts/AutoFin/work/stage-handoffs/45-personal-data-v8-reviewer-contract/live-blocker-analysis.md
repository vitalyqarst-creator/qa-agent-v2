# V8 Live Blocker Analysis

## Вывод

V8 терминально завершён как `changes-required`. Это не дефект тест-кейса и не ошибка source inventory: runner неверно преобразовал canonical Markdown-представление значений справочника в reviewer projection.

Retry/resume V8, повтор reviewer, смена transport и promotion не выполнялись.

## Что прошло

- Writer и reviewer работали в разных fresh read-only sessions.
- Writer вернул ровно 13 target TC; extra/missing sections отсутствуют.
- Runner мигрировал только `package_id` в 34 non-target секциях и доказал `all_non_target_test_semantics_preserved=true`.
- Metadata, structure, seed, obligation `65/65`, evidence-access, semantic-overlap и quality gates прошли.
- Reviewer вернул schema-valid contract: V7 verdict incompatibility не повторилась.
- 64 обязательства reviewer признал покрытыми; все исправленные V8 targets приняты.

## Что заблокировало sign-off

Reviewer получил structured projection:

```json
{"dictionary_id":"DICT-001","active_values":[";"]}
```

и поэтому корректно относительно своего payload отклонил `TC-ACPD-011`, где указаны `Мужчина` и `Женщина`.

Canonical inventory и compiled evidence при этом содержат:

```text
`Мужчина`; `Женщина`
```

Следовательно, reviewer finding `F-001` валиден как process outcome конкретного V8, но не подтверждает дефект draft или ФТ.

## Корневая причина

`_prepared_dictionary_evidence_projection()` извлекал значения регулярным выражением «текст между backticks». После canonical table parser строка ячейки имеет форму `Мужчина`; `Женщина`: внешние backticks уже сняты, а внутренние разделяют элементы. Регулярное выражение поэтому извлекло только текст между внутренними backticks — `;`.

Regression helper использовал другую форму с сохранёнными внешними backticks и ложно прошёл. Тест проверял искусственную строку, а не реально скомпилированный dictionary row.

## Архитектурный вывод

Передача DICT evidence была правильным решением, но повторный ad-hoc разбор Markdown в runner создал новый semantic transport defect. Следующий цикл должен использовать один canonical parser формата `active_values` или структурированные данные compiler-а и проверять, что projected values не пусты, не punctuation-only и точно равны inventory.

Повторная writer-сессия для исправления `TC-ACPD-011` не обоснована: сам TC source-correct, а reviewer принял остальные 64 obligations. Для быстрого recovery предпочтителен новый hash-bound reviewer-only rebind после исправления projection; fake/no-op TC repair использовать нельзя.
