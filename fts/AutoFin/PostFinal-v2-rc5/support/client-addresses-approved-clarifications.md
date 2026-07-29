# Подтверждённые уточнения: блок «Адреса клиента»

## Контекст

- `scope_slug`: `application-card-client-addresses`
- Основной ФТ: `source/PostFinal-v2/PostFinal-v2.docx`
- Границы: таблица 4, блок «Адреса клиента», `BSR 115–161`; связанное требование `BSR 324`.
- Статус: канонический `approved-clarification` source input для новых production/eval прогонов этого scope.

## Clarification Requests

| clarification_id | gap_id | scope_slug | requirement_codes | related_ft_reference | question | needed_for | blocking | requested_from | authority | user_response | response_status | response_type | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CLR-ADDR-001` | `GAP-ADDR-001` | `application-card-client-addresses` | BSR 118; BSR 119; BSR 143; BSR 144 | Таблица 4: адрес регистрации и адрес фактического места жительства, результат поиска DaData | Нужно ли различать «адрес не найден» и «адрес найден частично»? | Однозначная классификация результата DaData и границы негативных проверок | `yes` | `analyst` | `analyst` | «Нет, у нас или найден адрес в DaData, или не найден целиком». | `answered` | `analyst-confirmed` | `2026-06-26` |
| `CLR-ADDR-002` | `GAP-ADDR-002` | `application-card-client-addresses` | BSR 135 | Таблица 4: поле «Адрес регистрации» и ссылка «Адрес постоянной регистрации» | «Адрес постоянной регистрации» и «Адрес регистрации» — одно и то же поле? | Разрешение field dependency для условия видимости признака частного дома | `yes` | `user` | `user` | «Адрес постоянной регистрации» и «Адрес регистрации» — одно и то же поле. | `answered` | `user-confirmed` | `2026-07-19` |

## Provenance

| clarification_id | provenance |
| --- | --- |
| `CLR-ADDR-001` | Нормализовано из `fts/AutoFin/open-scope-coverage-gaps_ответы Соболева.md`, scope `09-application-card-client-addresses`, `GAP-001`; authority сохранён как `analyst`. |
| `CLR-ADDR-002` | Подтверждено пользователем 2026-07-19 в задаче подготовки независимого прогона блока «Адреса клиента». |

## Правила Использования Ответов

- `CLR-ADDR-001` не создаёт отдельное состояние «частично найден»: для требований `BSR 118–119` и `BSR 143–144` используются только найденный или не найденный целиком адрес.
- `CLR-ADDR-002` разрешает approved alias `Адрес постоянной регистрации -> Адрес регистрации`; второе UI-поле не создаётся.
- Оба ответа должны быть зарегистрированы с ролью `approved-clarification`, hash-bound и привязаны к точным clauses соответствующих assertions.
- Уточнения не задают trigger length, debounce, сортировку, fallback/retry или иное поведение DaData, отсутствующее в ФТ.
