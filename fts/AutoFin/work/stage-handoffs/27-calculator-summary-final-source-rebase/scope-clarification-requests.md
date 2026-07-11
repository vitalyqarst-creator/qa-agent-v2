# Scope Clarification Requests

## Контекст

- `scope_slug`: `application-card-calculator-summary-entrypoints`
- Coverage gaps: `scope-coverage-gaps.md`

## Как Заполнять

- Заполняйте только `user_response`, `response_status`, `response_type`, `updated_at`.
- Не удаляйте `gap_id`.

## Clarification Requests

| gap_id | related_ft_reference | question | needed_for | blocking | requested_from | user_response | response_status | response_type | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | - | - | - | no | - | - | unanswered | not-provided | - |

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| `GAP-001` | `BSR 46`, `SRC-002`, prefilled application data | Ответ пользователя не заменит отсутствующее внешнее ФТ; gap является non-blocking design constraint. |

## Правила Использования Ответов

- Ответы не заменяют Final ФТ.
- Полный mapping может быть добавлен только после подключения проверяемого внешнего источника.
