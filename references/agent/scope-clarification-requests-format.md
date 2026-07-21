# Формат `scope-clarification-requests.md`

`scope-clarification-requests.md` — conditional companion-артефакт к `scope-coverage-gaps.md` для вопросов пользователю или аналитику и фиксации ответов по конкретным coverage gaps.

## Назначение

- дать пользователю явное место для ответов на вопросы из `scope-coverage-gaps.md`;
- сохранить связь каждого вопроса с конкретным `GAP-*`;
- показать краткую привязку вопроса к конкретному утверждению ФТ без необходимости открывать полный gaps-файл;
- не смешивать стабильную карту gaps с интерактивными ответами;
- не превращать ответы пользователя в неявную замену текста ФТ.

## Расположение

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-clarification-requests.md`
  — рабочий companion к gaps текущего handoff;
- `fts/<ft-slug>/support/<source-version>/<scope-slug>-approved-clarifications.md`
  — переиспользуемый package/source input для новых clean runs, если в
  файле остались только строки `answered` с production-ready
  authority/type и стабильными `CLR-*`.

Package-level файл не является workflow state и не заменяет gaps текущего
run. В source registry его всегда регистрируют с `role = approved-clarification`
и `manifest_binding = approved-clarification`, а не как обычный support.

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

- `clarification_id`
- `gap_id`
- `scope_slug`
- `requirement_codes`
- `related_ft_reference`
- `question`
- `needed_for`
- `blocking`
- `requested_from`
- `authority`
- `user_response`
- `response_status`
- `response_type`
- `updated_at`

## Правила колонок

- `clarification_id` — стабильный уникальный `CLR-*`; одна точная версия ответа
  имеет один id.
- `gap_id` — идентификатор из `scope-coverage-gaps.md`, например `GAP-001`.
- `scope_slug` — точный scope, для которого получен ответ.
- `requirement_codes` — один или несколько точных кодов требований через `;`.
- `related_ft_reference` — краткая ссылка на утверждение ФТ: раздел, `GSR`, таблица/строка, поле/условие, `ATOM-*` или страница PDF.
- `question` — конкретный вопрос, на который можно ответить без чтения всей истории чата.
- `needed_for` — что станет возможным после ответа: полное покрытие требования, снятие ambiguity, уточнение тестовых данных.
- `blocking` = `yes | no`; должно соответствовать impact gap-а.
- `requested_from` = `user | analyst | product-owner | developer | unknown`.
- `authority` = `user | analyst | product-owner`; это фактический источник
  полученного ответа. Нельзя записывать пользователя как analyst/product-owner.
- `user_response` — место для ответа. До заполнения оставляй пустым или ставь `-`.
- `response_status` = `unanswered | answered | superseded | rejected`.
- `response_type` = `not-provided | working-assumption | user-confirmed |
  analyst-confirmed | product-confirmed | rejected`.
- `updated_at` — дата обновления в формате `YYYY-MM-DD` или `-`.

Production-ready semantics разрешено строить только из строки со
`response_status = answered` и согласованной парой authority/type:
`user/user-confirmed`, `analyst/analyst-confirmed` или
`product-owner/product-confirmed`. `working-assumption`, `rejected`,
`superseded`, `unanswered` и `not-provided` не являются утверждённым evidence.

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

| clarification_id | gap_id | scope_slug | requirement_codes | related_ft_reference | question | needed_for | blocking | requested_from | authority | user_response | response_status | response_type | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLR-001 | GAP-001 | application-search | GSR 1 | `GSR 1`, поле `...`, `ATOM-001` | Какое точное значение получает поле после сохранения? | Полное покрытие `GSR 1` | no | user | user | - | unanswered | not-provided | - |

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| GAP-002 | `GSR 2`, условие `...` | Ответ пользователя не нужен: gap фиксирует ограничение тест-дизайна, writer должен не домысливать правило. |

## Правила Использования Ответов

- Ответы в этом файле не заменяют основной ФТ.
- В source-first production workflow ответ сначала регистрируется в manifest v4
  как typed `clarifications[]`, hash-связывается через dedicated evidence role
  `approved-clarification` и привязывается к точным assertion clauses. Writer и
  reviewer получают его только из digest-bound compact projection, а не из
  свободного prose.
- Для использованного ответа соответствующий GAP остаётся в coverage-gaps
  artifact со `status = resolved` и точным
  `resolution = approved-clarification:<CLR-ID>`. В нём не остаётся активной
  ASSERT/ATOM/OBL execution chain.
- Один ответ, одновременно относящийся к нескольким кодам, остаётся одним
  `CLR-*`. Каждый assertion binding перечисляет только собственные локальные
  `requirement_codes`, а объединение всех bindings обязано в точности покрыть
  code set clarification.
- Изменение exact answer, authority, type, date, scope, gap, requirement codes
  или bytes файла делает manifest и независимый receipt stale.
- `working-assumption` можно использовать только как ограниченную рабочую гипотезу и обязательно отмечать в assumptions / coverage gaps.
- Если ответ противоречит основному ФТ, приоритет остается у основного ФТ; противоречие фиксируется как gap.
```

## Что не включать

- полный текст coverage gaps;
- reviewer findings;
- writer response;
- process-status этапа вместо `workflow-state.yaml`;
- ответы без привязки к `GAP-*`.
