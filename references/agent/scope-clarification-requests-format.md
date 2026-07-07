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
- `question_id`
- `related_ft_reference`
- `question_type`
- `priority`
- `blocking_level`
- `question`
- `answer_options`
- `needed_for`
- `impact_if_unanswered`
- `blocking`
- `requested_from`
- `answer_usage_rule`
- `duplicate_group`
- `user_response`
- `response_status`
- `response_type`
- `updated_at`

## Правила колонок

- `gap_id` — идентификатор из `scope-coverage-gaps.md`, например `GAP-001`.
- `question_id` — стабильный идентификатор вопроса, например `Q-001`; не переиспользуй его для другого смысла.
- `related_ft_reference` — краткая ссылка на утверждение ФТ: раздел, `GSR`, таблица/строка, поле/условие, `ATOM-*` или страница PDF.
- `question_type` — значение из `requirements-clarification-questioning-policy.md`.
- `priority` = `P0-blocker | P1-high | P2-medium | P3-low`.
- `blocking_level` = `blocks-scope-confirmation | blocks-writer-start | blocks-ready-for-review | blocks-sign-off | allows-limited-coverage | non-blocking`.
- `question` — конкретный вопрос, на который можно ответить без чтения всей истории чата.
- `answer_options` — варианты ответа, если ambiguity конечная; иначе `open`.
- `needed_for` — что станет возможным после ответа: полное покрытие требования, снятие ambiguity, уточнение тестовых данных.
- `impact_if_unanswered` — что останется непокрытым, заблокированным или ограниченным, если ответа не будет.
- `blocking` = `yes | no`; должно соответствовать impact gap-а.
- `requested_from` = `business-analyst | product-owner | system-analyst | developer | qa-lead | unknown`.
- `answer_usage_rule` — значение из `requirements-clarification-questioning-policy.md`.
- `duplicate_group` — общий ключ для дублей/связанных вопросов или `none`.
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

| question_id | gap_id | related_ft_reference | question_type | priority | blocking_level | question | answer_options | needed_for | impact_if_unanswered | blocking | requested_from | answer_usage_rule | duplicate_group | user_response | response_status | response_type | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q-001 | GAP-001 | `GSR 1`, поле `...`, `ATOM-001` | missing-validation-rule | P1-high | blocks-ready-for-review | Какое точное значение получает поле после сохранения? | open | Полное покрытие `GSR 1` | Expected result останется `unclear`, writer не может закрыть atom тест-кейсом. | yes | business-analyst | analyst-confirmation-enough | none | - | unanswered | not-provided | - |

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| GAP-002 | `GSR 2`, условие `...` | Ответ пользователя не нужен: gap фиксирует ограничение тест-дизайна, writer должен не домысливать правило. |

## Правила Использования Ответов

- Ответы в этом файле не заменяют основной ФТ.
- Writer может использовать `analyst-confirmed` или `product-confirmed` ответы как уточняющий вход, явно указав это в трассировке.
- `working-assumption` можно использовать только как ограниченную рабочую гипотезу и обязательно отмечать в assumptions / coverage gaps.
- Если ответ противоречит основному ФТ, приоритет остается у основного ФТ; противоречие фиксируется как gap.
- `working-assumption-only` не может стать expected result без accepted risk.
- `P0-blocker` / `P1-high` с `blocking_level = blocks-*` должны оставаться blocking до ответа или accepted risk.
```

## Что не включать

- полный текст coverage gaps;
- reviewer findings;
- writer response;
- process-status этапа вместо `workflow-state.yaml`;
- ответы без привязки к `GAP-*`.
