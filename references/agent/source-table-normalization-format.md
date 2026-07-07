# Source Table Normalization Format

`Source Table Normalization` — обязательный split artifact `work/test-design/<scope-slug>/source-table-normalization.md` перед `Test Design Decision Table`, `Coverage Obligation Table` и `Atomic Requirements Ledger`, если scope строится по таблицам полей, таблицам действий, XHTML/PDF/DOCX extraction или другому табличному источнику. Перед ним должен быть split artifact `source-row-inventory.md`, который доказывает, что все source rows внутри scope перечислены и не потеряны до атомаризации.

Цель секции — отделить восстановление требований из источника от test-design. Writer сначала должен превратить строку источника в чистое проверяемое утверждение, и только потом создавать `ATOM-*`.

## Source Legend And Abbreviation Check

Перед нормализацией табличного источника проверь сокращенные заголовки, условные обозначения, локальные коды и аббревиатуры, влияющие на test design.

- Не выводи смысл сокращения только по паттернам значений в строках.
- Если смысл влияет на test design и не подтвержден source/support/`AGENT-NOTES.md`, создай `GAP-*` типа `missing-source-definition`.
- Зависящие от неподтвержденной расшифровки normalization rows должны иметь `confidence = unclear` или `gap_id`; они не могут напрямую становиться `covered` atoms.

## Формат

Минимальная таблица:

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `SRC-001.P01` | `WP-01` | `...` | `visibility` | `...` | `...` | `GSR 1` | `PDF p.46, row ...` | `high` | `-` | `ATOM-001` |

Если одна source row содержит несколько буквенно-цифровых кодов требований или несколько самостоятельных свойств, добавь перед normalization секцию:

## Source Row Completeness Matrix

| source_row_id | source_requirement_codes | normalized_property_ids | linked_atoms | gap_ids | coverage_decision |
| --- | --- | --- | --- | --- | --- |
| `SRC-003` | `GSR 1; GSR 2; GSR 3; GSR 4` | `SRC-003.P01; SRC-003.P02; SRC-003.P03; SRC-003.P04` | `ATOM-001; ATOM-004` | `GAP-001; GAP-002` | `split-complete` |

## Правила

- Одна строка normalization table = одно очищенное свойство поля, действие, условие или ожидаемое поведение.
- Для table/list-heavy extraction используй XHTML как primary machine-readable source для восстановления rows/list items; DOCX подтверждает смысл требований, PDF сверяет структуру и коды.
- `source_property_id` — обязательная стабильная ссылка на одно нормализованное свойство внутри source row. Формат: `<source_row_id>.P##`, например `SRC-003.P01`.
- Нельзя переносить в `expected_behavior` заголовки таблиц, номера страниц, соседние поля, колонки `Название / Видимость / О / Р / Тип ввода поля / Тип значения / Примечание`.
- Перед использованием заголовков вроде `О` / `Р` выполни `Source Legend And Abbreviation Check`; без подтверждения это `GAP-*`, а не atom.
- Если extraction содержит соседнее поле или обрывок следующей строки, writer должен либо восстановить чистую строку по источнику, либо поставить `confidence = low` и связать строку с `GAP-*`.
- `confidence = high` допустим только когда `field_or_block`, `property`, `condition`, `expected_behavior`, `requirement_code` и `source_ref` восстановлены без противоречий.
- `confidence = medium` допустим для частично восстановленной строки, если pass/fail behavior все еще выводим из источника без домысливания.
- `confidence = low` или `confidence = unclear` всегда требует `gap_id`.
- `Atomic Requirements Ledger` должен ссылаться только на нормализованные строки с `confidence = high | medium` либо на `GAP-*`; строка normalization с `confidence = low | unclear` не может напрямую стать `covered` atom.
- Если source row содержит несколько независимых свойств, например visibility, requiredness, editability, default, format, boundary и integration behavior, writer обязан разделить ее на несколько normalization rows.
- Разделение требуется не только по разным `GSR`/`REQ`, но и по semantic property class. Нельзя оставлять в одной normalization row разные классы вроде `dictionary-source`, `min-boundary`, `max-boundary`, `numeric-format`, `exact-length`, `visibility`, `requiredness`, `editability`, `default-value`, `integration-prefill`, `action-created-optional-block`, `repeatable-block-lifecycle`, `checkbox-list`, `print-form-output`, даже если они записаны под одним requirement code или все ведут в `GAP-*`.
- Не дроби один source-backed `numeric-format` на искусственные property types для valid/invalid веток. `valid-digits`, `reject-letters`, `reject-spaces`, `reject-special-chars`, `reject-decimal-separator` и `reject-sign` являются `Coverage Obligation Table` classes одного `source_property_id`, а не отдельными normalization rows.
- Если один код или одна строка ФТ одновременно говорит “значение берется из справочника”, “минимум берется из каталога” и “максимум берется из каталога”, создай минимум три строки: dictionary source, min boundary source, max boundary source.
- Если source row содержит несколько `GSR`/`REQ`/локальных кодов, каждый код должен быть представлен отдельным `source_property_id`, кроме редкого случая, когда коды буквально описывают одно и то же проверяемое утверждение с одним condition и одним expected behavior. Такой случай нужно явно обосновать в `Source Row Completeness Matrix`.
- Если один requirement code содержит несколько самостоятельных утверждений, один и тот же `requirement_code` может повторяться в нескольких normalization rows с разными `source_property_id`.
- Каждая строка normalization должна быть связана с `linked_atoms` или `gap_id`. Нельзя оставлять нормализованное свойство без дальнейшего решения.
- Каждый `source_row_id` в normalization table должен существовать в `Source Row Inventory`.

Пример неправильной нормализации:

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-003` | `-` | `WP-01` | `Сумма на руки` | `numeric` | `-` | `Только числовые символы; max/min из каталога; может заполняться тегами` | `GSR 1; GSR 2; GSR 3; GSR 4` | `PDF p.46` | `high` | `-` | `ATOM-002` |

Почему неправильно: `GSR 1`, `GSR 2`, `GSR 3`, `GSR 4` имеют разные test-design решения и могут pass/fail независимо.

Пример правильной нормализации:

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-003` | `SRC-003.P01` | `WP-01` | `Сумма на руки` | `numeric-input` | `поле доступно` | `поле принимает только числовые символы` | `GSR 1` | `PDF p.46` | `high` | `-` | `ATOM-001` |
| `SRC-003` | `SRC-003.P02` | `WP-01` | `Сумма на руки` | `max-boundary` | `известен max из продуктового каталога` | `максимальное значение берется из продуктового каталога` | `GSR 2` | `PDF p.46` | `high` | `GAP-001` | `-` |
| `SRC-003` | `SRC-003.P03` | `WP-01` | `Сумма на руки` | `min-boundary` | `известен min из продуктового каталога` | `минимальное значение берется из продуктового каталога` | `GSR 3` | `PDF p.46` | `high` | `GAP-002` | `-` |
| `SRC-003` | `SRC-003.P04` | `WP-01` | `Сумма на руки` | `amount-tags` | `справочник тегов доступен` | `сумма может быть заполнена тегом` | `GSR 4` | `PDF p.46` | `high` | `-` | `ATOM-004` |

Пример неправильного разбиения с одним `GSR`, но несколькими property classes:

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-005` | `SRC-005.P05` | `WP-01` | `Срок кредитования` | `term_dictionary_and_bounds` | `catalog fixture required` | `значение берется из справочника; минимум и максимум берутся из продуктового каталога` | `GSR 9` | `PDF p.47` | `high` | `GAP-002` | `-` |

Почему неправильно: dictionary source, min boundary и max boundary имеют разные test-design решения. Даже если все три пока уходят в `GAP-*`, reviewer должен видеть три отдельных `source_property_id`.

## Blocking Defects

Writer не должен ставить `stage_status: ready-for-review`, если:

- split test-design artifacts содержат `Atomic Requirements Ledger`, построенный из табличного источника, но нет `source-table-normalization.md`;
- split test-design artifacts содержат `Source Table Normalization`, но нет `test-design-decision-table.md`, где для каждой `source_property_id` решено: standalone TC, covered by existing TC, gap/unclear, metadata-only, scenario-only или out of scope;
- split test-design artifacts содержат `Source Table Normalization` с `numeric-format`, `exact-length`, `amount-tags`, `action-created-optional-block`, `repeatable-block-lifecycle`, `checkbox-list`, `print-form-output`, `format-mask` или `default-mask`, но нет `coverage-obligation-table.md`, где свойство разложено на обязательные coverage classes;
- split test-design artifacts содержат `Source Table Normalization`, но нет `source-row-inventory.md`;
- normalization row ссылается на `source_row_id`, которого нет в `Source Row Inventory`;
- source row содержит несколько `GSR`/`REQ`, но нет `Source Row Completeness Matrix`;
- есть сокращения source, влияющие на test design, но нет `Source Legend And Abbreviation Check` или `GAP-*`;
- normalization row не содержит `source_property_id`;
- normalization row содержит несколько `GSR`/`REQ`, которые могут проверяться независимо;
- normalization row смешивает разные semantic property classes, например dictionary source + min boundary + max boundary, visibility + requiredness или format + boundary;
- количество in-scope `GSR`/`REQ` в `Source Row Inventory` больше количества связанных `source_property_id` в normalization;
- normalization row не связана ни с `ATOM-*`, ни с `GAP-*`;
- в normalization table есть строки `confidence = low | unclear` без `GAP-*`;
- в ledger или TC quote попали table-header residue, соседние поля или extraction-мусор;
- `coverage_status = covered` поставлен для atom, который ссылается на загрязненную или low-confidence source row.

## Diagnostic Artifact

Для короткой проверки нормализации до writer-pass используй отдельный файл `source-normalization-diagnostic.md` по формату [source-normalization-diagnostic-format.md](source-normalization-diagnostic-format.md).

Diagnostic-only run не должен создавать `Atomic Requirements Ledger`, `Package Test Design Plan`, `TC-*`, reviewer artifacts или `signed-off` state. Его задача - доказать, что выбранные source rows правильно разложены на `source_property_id` до генерации тест-кейсов.

Diagnostic artifact дополнительно требует `diagnostic_atom_status`, `source_column` и `source_text_fragment`. Не используй `GAP-900` как замену отсутствующего atom, не пиши `expected_behavior` вида `follows GSR N`, и не переноси integration/internal behavior без observable artifact или реального `GAP-*`.
