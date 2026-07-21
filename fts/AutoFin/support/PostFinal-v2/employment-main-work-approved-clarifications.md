# Подтверждённые уточнения: «Сведения о занятости» / «Основная работа»

## Контекст

- `scope_slug`: `employment-main-work`
- Основной ФТ: `source/PostFinal-v2/PostFinal-v2.docx`
- Границы: таблица 4, блок «Сведения о занятости», подблок «Основная работа», `BSR 263–284`.
- Статус: канонический `approved-clarification` source input для новых production/eval прогонов этого scope.

## Как Заполнять

- Ответы ниже уже подтверждены пользователем; не изменять их как working assumptions.
- Если ответ заменён, прежнюю строку перевести в `superseded` и добавить новую строку с новым `CLR-*`.

## Clarification Requests

| clarification_id | gap_id | scope_slug | requirement_codes | related_ft_reference | question | needed_for | blocking | requested_from | authority | user_response | response_status | response_type | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CLR-EMP-001` | `GAP-EMP-001` | `employment-main-work` | BSR 264; BSR 267; BSR 269; BSR 271; BSR 274; BSR 275; BSR 276; BSR 277; BSR 279 | Таблица 4: поле «Социальный статус» и условия видимости по полю «Тип занятости» | «Тип занятости» — это то же поле, что «Социальный статус»? | Снятие ambiguity для условий видимости полей основной работы | `yes` | `user` | `user` | «Тип занятости» — это то же поле, что «Социальный статус». | `answered` | `user-confirmed` | `2026-07-18` |
| `CLR-EMP-002` | `GAP-EMP-002` | `employment-main-work` | BSR 284 | Таблица 4, кнопка «Корзина» подблока «Основная работа» | Какое состояние должны иметь поля после удаления заполненного блока и последующего добавления нового? | Отдельная lifecycle-проверка отсутствия переноса данных в новый блок | `yes` | `user` | `user` | После удаления заполненного блока и последующего добавления нового, поля должны быть пустыми. | `answered` | `user-confirmed` | `2026-07-18` |

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| `none` | `none` | Все зафиксированные в этом файле gaps имеют подтверждённые ответы. |

## Подтверждённые Source Inputs

| source_id | role | manifest_binding | semantic_purpose | path | source_location | applies_to | authority | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-SUPPORT-EMP-001` | `support` | `supporting-material` | `dictionary-source` | `fts/AutoFin/support/PostFinal-v2/АФБ справочники 26.06.26.md` | Секция «Тип должности»; колонки «Значение», «Внутренний код», «Архивный» | `BSR 274`; справочник «Типы должности» | `user` | `2026-07-18` |

## Правила Использования Ответов

- Ответ `CLR-EMP-001` разрешает approved alias `Тип занятости -> Социальный статус`; он не создаёт второе UI-поле.
- Ответ `CLR-EMP-002` требует отдельной lifecycle obligation и отдельного тест-кейса: заполнить блок, удалить его, добавить новый и проверить пустое состояние полей.
- Файл должен быть зарегистрирован в prepared context с ролью `approved-clarification`; exact answers должны быть hash-bound и привязаны к точным condition/action/oracle clauses.
- Справочник извлекается целиком из указанной секции: все пять активных значений, их внутренние коды и признак архивности. Неполные примеры не заменяют этот inventory.
