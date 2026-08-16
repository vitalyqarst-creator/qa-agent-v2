# Исправление matrix после независимого review — 9.3.1 «Экран Партнёры»

**Статус этапа:** один полный пакет исправлений выполнен; ожидается проверка закрытия findings reviewer-сеансом `01a0098c-1835-77d3-a7b7-c76f2d5923fc`.

| Finding | Исправление | Затронутые артефакты |
| --- | --- | --- |
| 1. `SCN-001` объединял AS.3 и AS.4 | `SCN-001` оставлен только для AS.3; новый `SCN-002` отдельно проверяет двухуровневую структуру AS.4. | `test-design-matrix.md`, `test-data-source-plan.json` |
| 2. Ограничение статусов не разделяло объекты | Созданы `SCN-003` для партнёра и `SCN-004` для реквизитов; оба сохраняют честный статус `candidate-ui-calibration`. | `test-design-matrix.md`, `test-data-source-plan.json`, `fixture-catalog.md` |
| 3. Доступность команды смешивалась с переходом | Для партнёра и реквизитов разнесены intent доступности команды при наведении и intent изменения индикатора после перехода. | `test-design-matrix.md`, `test-data-source-plan.json` |
| 4. Ролевые права смешивались с post-transition видимостью; `SCN-003` дублировал lifecycle | Дублирующий старый `SCN-003` удалён. Права проверяются в `SCN-013`, `SCN-016`, `SCN-026`, `SCN-029`; post-transition видимость — в `SCN-015`, `SCN-018`, `SCN-028`, `SCN-031`. `SRC-04` перенесён в объектные lifecycle-строки. | `test-design-matrix.md`, `test-data-source-plan.json`, `fixture-catalog.md` |
| 5. `SCN-016` объединял AS.20–AS.22 | Созданы отдельные `SCN-019` (отображение реквизитов), `SCN-020` (единственный столбец) и `SCN-021` (заголовок и счётчик). | `test-design-matrix.md`, `test-data-source-plan.json`, `fixture-catalog.md` |
| 6. Для навигации не было доказуемого признака выбранного партнёра | `TDP-ENV-004` и `FX-ENV-PARTNER-001` требуют одинаковое отображаемое наименование или ID в общем списке и на экране реквизитов. Рисунок 3 зарегистрирован в `source-scope.md` как visual binding этого oracle. | `source-scope.md`, `test-design-matrix.md`, `test-data-source-plan.json`, `fixture-catalog.md` |

## Ограничения, сохранённые без изменений

- `SCN-005` и `SCN-006` остаются `blocked-observability`: для них не добавлялись неподтверждённые UI- или API-oracle.
- Все `TDP-*` остаются `blocked` до предоставления runtime-доступа, ролей и подготовленных сущностей. Это не подменено фиктивными literals или fixtures.
