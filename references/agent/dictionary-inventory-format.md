# Dictionary Inventory Format

`dictionary-inventory.md` - обязательный split artifact для scope/package, где ФТ, source table или support workbook задает справочник, фиксированный перечень значений, теги или reference-list.

Цель artifact: сохранить извлеченные значения справочников в виде, который writer и reviewer могут читать без повторного поиска по XLSX/DOCX/PDF. Нельзя заменять полный справочник двумя примерными branch values из ФТ.

## Placement

Файл размещается рядом с другими split test-design artifacts:

`fts/<ft-slug>/work/test-design/<section-id>-<scope-slug>/dictionary-inventory.md`

Создавай или обновляй его после `source-table-normalization.md` и до `test-design-decision-table.md`, если normalization содержит `dictionary-source`, `amount-tags`, `tag-values`, `table-list`, `checkbox-list` или аналогичный reference-list property.

## Minimum Format

```md
# Dictionary Inventory

| dictionary_id | dictionary_name | source_file | source_location | extraction_status | active_values | archived_values | used_by_source_properties | gap_id | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DICT-001` | `Типы занятости` | `support/Наполнение справочников_v1.xlsx` | `sheet: Типы занятости; columns: Значение, Архивный` | `extracted` | `Работа по найму`; `Пенсионер (не работает)`; `Индивидуальный предприниматель`; `Собственник бизнеса`; `Частная практика / Самозанятый`; `Безработный` | `-` | `SRC-002.P04` | `-` | `Архивный = Нет` трактуется как active. |
```

## Columns

- `dictionary_id`: стабильный id `DICT-*`, который используется в `Test Design Decision Table`, `Coverage Obligation Table`, `Package Test Design Plan`, TC test data и reviewer findings.
- `dictionary_name`: точное имя справочника из ФТ/source/support.
- `source_file`: путь к source/support artifact внутри FT-пакета.
- `source_location`: sheet/table/page/row/columns или иной точный locator.
- `extraction_status`: `extracted | partial | missing | ambiguous | not-needed`.
- `active_values`: все активные значения, если они извлечены; для больших справочников допускается ссылка на отдельную секцию `## DICT-* Values`.
- `archived_values`: архивные/неактивные значения или `-`, если таких значений нет.
- `used_by_source_properties`: один или несколько `source_property_id` из `source-table-normalization.md`.
- `gap_id`: `GAP-*`, если значения не извлечены полностью или source не подтверждает closed-set поведение.
- `notes`: краткое правило интерпретации колонок source, например `Архивный = Нет`.

## Rules

- Один referenced dictionary/list в scope должен иметь одну строку inventory.
- `dictionary-source` normalization rows должны ссылаться на `dictionary_id` в TDDT/plan/TC, а не на неполный текст `значения из тестовых данных`.
- Если `extraction_status = extracted`, `active_values` не может быть пустым.
- Если источник дает колонку архивности/активности, разделяй active и archived values; не смешивай их в одной проверке.
- Если справочник найден, но закрытость перечня не следует из ФТ/source, покрывай отображение active values и фиксируй `GAP-*` только на closed-set/absence-of-extra-values.
- Если справочник не найден или source location неоднозначен, ставь `extraction_status = missing | ambiguous`, указывай `gap_id` и не придумывай значения.
- Branch-driver examples из ФТ можно использовать как test fixtures, но они не заменяют inventory полного справочника.

## Downstream Use

- `Test Design Decision Table`: для `property_type = dictionary-source` указывай `dictionary_id` в `oracle_source` или `decision_reason`; если inventory отсутствует, решение не может быть `standalone_tc` без `GAP-*`.
- `Coverage Obligation Table`: для справочников с извлеченными active values добавляй obligation `dictionary-values-shown`; для confirmed closed set добавляй obligation `dictionary-no-extra-values` или фиксируй `GAP-*`, если закрытость не доказана.
- `Package Test Design Plan`: `oracle_source` должен ссылаться на `DICT-*` и source locator, например `DICT-001; support workbook`.
- `TC-*`: test data должны перечислять все проверяемые active values или ссылаться на `DICT-*` с понятным источником; два примера допустимы только для отдельной dependency branch, а не для проверки справочника.

## Blocking Conditions

Не ставь `ready-for-review`, если:

- `source-table-normalization.md` содержит `dictionary-source` / reference-list property, но `dictionary-inventory.md` отсутствует;
- `dictionary-inventory.md` не имеет строки для referenced dictionary/list;
- `extraction_status = extracted`, но `active_values` пустой или содержит только примерные значения из ФТ;
- TDDT/plan/TC проверяет справочник без ссылки на `DICT-*` или `GAP-*`;
- active и archived values смешаны без отдельного oracle.
