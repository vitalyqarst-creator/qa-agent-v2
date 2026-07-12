# Scope Clarification Requests

## Контекст

- `scope_slug`: `application-card-client-personal-data`.
- Coverage gaps: `scope-coverage-gaps.md`.

## Clarification Requests

| gap_id | related_ft_reference | question | needed_for | blocking | requested_from | user_response | response_status | response_type | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GAP-001` | `BSR 48/51/54/61–63/67/71/75` | Как UI отклоняет каждый invalid class: filtering, message, highlight, blocked save/transition? | Перевод calibration candidates в regression-ready cases. | `no` | analyst/UI evidence | - | pending | - | 2026-07-12 |
| `GAP-002` | Table 4 column О; `BSR 68/72/76` | Как UI проверяет пустые required fields и полностью пустую previous-FIO group? | Regression oracle requiredness. | `no` | analyst/UI evidence | - | pending | - | 2026-07-12 |
| `GAP-003` | `BSR 49/52/55/57/59/69/73/77` | Нужны ли failure/retry/fallback cases DaData/ABS и какой artifact подтверждает технический результат? | Integration negative coverage. | `no` | analyst/integration owner | - | pending | - | 2026-07-12 |

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| none | - | all gaps have requests |

## Правила Использования Ответов

- Ответ не заменяет FT; конфликт оставляет gap открытым.
- До ответа writer сохраняет calibration candidates и integration limitations.
