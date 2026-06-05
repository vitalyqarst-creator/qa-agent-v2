# Формат `scope-clarification-requests.md`

`scope-clarification-requests.md` — conditional companion-артефакт к `scope-coverage-gaps.md` для вопросов пользователю или аналитику и фиксации ответов по конкретным coverage gaps.

## Назначение

- дать пользователю явное место для ответов на вопросы из `scope-coverage-gaps.md`;
- сохранить связь каждого вопроса с конкретным `GAP-*`;
- показать краткую привязку вопроса к конкретному утверждению ФТ без необходимости открывать полный gaps-файл;
- не смешивать стабильную карту gaps с интерактивными ответами;
- не превращать ответы пользователя в неявную замену текста ФТ.

## Расположение

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-clarification-requests.md` для новых handoff-папок

## Когда создавать

- создавай файл всегда, если в `scope-coverage-gaps.md` есть хотя бы один `GAP-*`;
- для каждого gap с `Needs User Input: yes` добавляй минимум одну строку в `Clarification Requests`;
- если по gap ответ пользователя не нужен, не добавляй строку-вопрос, но перечисли такой gap в `Gaps Without Requests` с причиной;
- если gaps нет, файл можно не создавать.

## Обязательные секции

- `## Контекст`
- `## Как Заполнять`
- `## Clarification Requests`
- `## Gaps Without Requests`
- `## Правила Использования Ответов`

## Обязательные колонки

- `gap_id`
- `related_ft_reference`
- `question`
- `needed_for`
- `blocking`
- `requested_from`
- `user_response`
- `response_status`
- `response_type`
- `updated_at`

## Правила колонок

- `gap_id` — идентификатор из `scope-coverage-gaps.md`, например `GAP-001`.
- `related_ft_reference` — краткая ссылка на утверждение ФТ: раздел, `GSR`, таблица/строка, поле/условие, `ATOM-*` или страница PDF.
- `question` — конкретный вопрос, на который можно ответить без чтения всей истории чата.
- `needed_for` — что станет возможным после ответа: полное покрытие требования, снятие ambiguity, уточнение тестовых данных.
- `blocking` = `yes | no`; должно соответствовать impact gap-а.
- `requested_from` = `user | analyst | product-owner | developer | unknown`.
- `user_response` — место для ответа. До заполнения оставляй пустым или ставь `-`.
- `response_status` = `unanswered | answered | superseded | rejected`.
- `response_type` = `not-provided | working-assumption | analyst-confirmed | product-confirmed | rejected`.
- `updated_at` — дата обновления в формате `YYYY-MM-DD` или `-`.

## Рекомендуемый шаблон

```md
## Контекст

- `scope_slug`: `...`
- Coverage gaps: `scope-coverage-gaps.md`

## Как Заполнять

- Заполняйте только колонки `user_response`, `response_status`, `response_type`, `updated_at`.
- Не удаляйте `gap_id`.
- Если ответ заменен более новым, установите `response_status = superseded` и добавьте новую строку с тем же `gap_id`.

## Clarification Requests

| gap_id | related_ft_reference | question | needed_for | blocking | requested_from | user_response | response_status | response_type | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GAP-001 | `GSR 1`, поле `...`, `ATOM-001` | Какое точное значение получает поле после сохранения? | Полное покрытие `GSR 1` | no | analyst | - | unanswered | not-provided | - |

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| GAP-002 | `GSR 2`, условие `...` | Ответ пользователя не нужен: gap фиксирует ограничение тест-дизайна, writer должен не домысливать правило. |

## Правила Использования Ответов

- Ответы в этом файле не заменяют основной ФТ.
- Writer может использовать `analyst-confirmed` или `product-confirmed` ответы как уточняющий вход, явно указав это в трассировке.
- `working-assumption` можно использовать только как ограниченную рабочую гипотезу и обязательно отмечать в assumptions / coverage gaps.
- Если ответ противоречит основному ФТ, приоритет остается у основного ФТ; противоречие фиксируется как gap.
```

## Что не включать

- полный текст coverage gaps;
- reviewer findings;
- writer response;
- process-status этапа вместо `workflow-state.yaml`;
- ответы без привязки к `GAP-*`.
