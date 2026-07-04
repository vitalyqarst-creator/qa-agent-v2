# Coverage Obligation Table Format

`Coverage Obligation Table` - обязательный split artifact `work/test-design/<scope-slug>/coverage-obligation-table.md` для package-based scope, где `Source Table Normalization` содержит свойства с обязательными классами покрытия. Таблица создается после `Test Design Decision Table` и до `Atomic Requirements Ledger` / `Package Test Design Plan`.

Цель artifact - не дать writer-у считать одно атомарное свойство одним тестом, если само свойство требует набора независимых проверок. Например, `numeric-format` со смыслом "только числовые символы" не покрывается одним позитивным вводом `123` и одной проверкой буквы `A`: нужны отдельные обязательства для цифр, букв, пробелов, спецсимволов, десятичного разделителя и знака.

## Порядок В Writer Flow

1. `Source Row Inventory`
2. `Source Row Completeness Matrix`, если source row содержит несколько кодов/свойств
3. `Source Table Normalization`
4. `Test Design Decision Table`
5. `Coverage Obligation Table`
6. `Atomic Requirements Ledger`
7. `Package Test Design Plan`
8. `Test Design Review`
9. `TC-*`
10. `Writer Quality Gate`

## Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OBL-001 | WP-01 | SRC-002.P01 | ATOM-002 | numeric-format | valid-digits | Поле `Сумма на руки` принимает ввод, состоящий только из цифр. | GSR 1; section-19; PDF p.46 | TC-UI-MAIN-001 | covered | - |
| OBL-002 | WP-01 | SRC-002.P01 | ATOM-002 | numeric-format | reject-letters | Поле `Сумма на руки` не принимает буквы. | GSR 1; section-19; PDF p.46 | TC-UI-MAIN-002 | covered | - |
| OBL-003 | WP-01 | SRC-002.P01 | ATOM-002 | numeric-format | reject-spaces | Поле `Сумма на руки` не принимает пробелы как часть значения. | GSR 1; section-19; PDF p.46 | TC-UI-MAIN-171 | covered | - |
| OBL-004 | WP-01 | SRC-002.P01 | ATOM-002 | numeric-format | reject-special-chars | Поле `Сумма на руки` не принимает спецсимволы. | GSR 1; section-19; PDF p.46 | TC-UI-MAIN-172 | covered | - |
| OBL-005 | WP-01 | SRC-002.P01 | ATOM-002 | numeric-format | reject-decimal-separator | Поле `Сумма на руки` не принимает десятичный разделитель. | GSR 1; section-19; PDF p.46 | TC-UI-MAIN-173 | covered | - |
| OBL-006 | WP-01 | SRC-002.P01 | ATOM-002 | numeric-format | reject-sign | Поле `Сумма на руки` не принимает знак `+` или `-`. | GSR 1; section-19; PDF p.46 | TC-UI-MAIN-174 | covered | - |
| OBL-007 | WP-01 | SRC-002.P04 | ATOM-005 | amount-tags | dictionary-values-shown | Отображаются активные теги суммы из справочника, без лишних значений. | GSR 4; support workbook `Значения тегов по выбору суммы` | TC-UI-MAIN-169 | covered | - |
| OBL-008 | WP-01 | SRC-002.P04 | ATOM-005 | amount-tags | tag-selection-fills-field | Выбор тега суммы заполняет поле `Сумма на руки` соответствующим числовым значением. | GSR 4; support workbook `Значения тегов по выбору суммы` | TC-UI-MAIN-170 | covered | - |
| OBL-009 | WP-01 | SRC-010.P02 | ATOM-028 | format-mask | mask-pattern-applied | Поле `Код подразделения` отображает введенные цифры по маске `XXX-XXX`. | GSR 28 | TC-UI-MAIN-180 | covered | - |
| OBL-010 | WP-01 | SRC-010.P03 | ATOM-049 | default-mask | default-mask-visible | До ввода значения поле отображает default mask, если она явно задана source row. | GSR 49 | TC-UI-MAIN-181 | covered | - |
| OBL-011 | WP-01 | SRC-020.P01 | ATOM-037 | date-passport-validity | passport-before-14-rejected | Для даты выдачи до 14-летия отображается подсказка `Выдача паспорта предусмотрена с 14 лет`. | GSR 32; PDF p.49 | TC-UI-MAIN-182 | covered | - |
| OBL-012 | WP-02 | SRC-035.P02 | ATOM-067 | address-required-components | missing-apartment-or-private-house-hint | При отсутствии квартиры поле подсвечивается красным и отображается подсказка о квартире или частном доме. | GSR 60; PDF p.52 | TC-UI-MAIN-183 | covered | - |

## Статусы

`status` - закрытый enum: `covered | gap | unclear | blocked | not-applicable | n/a`.

Не используй `planned`, `pass`, `pass-with-gap`, `ok`, `yes` или локальные варианты. `Coverage Obligation Table` фиксирует итоговый routing obligation row после design decision: строка либо покрыта `TC-*`, либо указывает конкретный `GAP-*`, либо явно не применима. Намерение написать TC позже хранится в `planned_tc_or_gap`, но не в `status`.

## Обязательные Классы

Для `property_type = numeric-format`:

- `valid-digits` - позитивный ввод, состоящий только из цифр.
- `reject-letters` - буквы не принимаются.
- `reject-spaces` - пробелы не принимаются как часть значения.
- `reject-special-chars` - спецсимволы не принимаются.
- `reject-decimal-separator` - десятичные разделители не принимаются.
- `reject-sign` - знаки `+` / `-` не принимаются.

`numeric-format` не задает UI-механику сам по себе. Если ФТ говорит только “только числовые символы”, expected result не должен утверждать, что буква не появилась, была удалена, поле очистилось или значение автоформатировалось. Такие механики допустимы только при прямом source evidence; иначе фиксируй `GAP-*` / `unclear`.

Не создавай отдельный property type вроде `numeric-format-invalid`, `numeric-negative` или `non-digit-rejection` для обхода обязательных classes. Один source-backed `numeric-format` остается одним `source_property_id`; все required classes идут отдельными obligation rows. Если оракул или fixture для конкретного invalid class недоступен, эта obligation row все равно создается и ссылается на узкий `GAP-*`, а не на новый property type.

Для `property_type = amount-tags`:

- `dictionary-values-shown` - UI отображает значения из подтвержденного справочника.
- `tag-selection-fills-field` - выбор тега заполняет связанное поле правильным значением.

Для `property_type = format-mask`:

- `mask-pattern-applied` - значение отображается по заданному шаблону/маске, например `XXX-XXX`.

Для `property_type = default-mask`:

- `default-mask-visible` - default mask видима до ввода, если source явно задает такую обязанность.

Для `property_type = exact-length`:

- `exact-length-accepted` - значение длиной ровно `N` принимается.
- `shorter-rejected` - значение длиной `N-1` не проходит проверку точной длины.
- `longer-rejected` - значение длиной `N+1` не проходит проверку точной длины.

Если `exact-length` совмещен с правилом `только цифры` / `только символы класса X`, создавай также применимые строки `numeric-format` / `allowed-symbols`. Проверка `N-1` не покрывает `N+1`: слишком короткое и слишком длинное значение могут иметь разный observable oracle.

Для `property_type = action-created-optional-block`:

- `block-absent-before-action` - поля блока не отображаются до действия добавления, если это следует из source.
- `action-reveals-block` - действие `Добавить ...` отображает поля блока.
- `no-action-does-not-require-block` - если source не требует сам факт добавления, пользователь может продолжить без созданного блока при валидности остальных обязательных данных.
- `created-block-required-fields-enforced` - обязательные поля созданного блока проверяются только после создания блока.

Если source не определяет, обязателен ли сам факт добавления блока, создай `GAP-*` / `unclear`; не считай обязательность полей внутри созданного блока обязательностью добавления блока.

Для `property_type = repeatable-block-lifecycle`:

- `first-block-added` - первое действие добавляет первый блок.
- `second-block-independent` - повторное действие добавляет второй независимый блок, если повторяемость разрешена source.
- `delete-one-preserves-others` - удаление одного блока не удаляет другие созданные блоки.
- `delete-last-removes-block` - удаление последнего блока приводит к source-backed отсутствию/очистке блока или к `GAP-*`, если итоговое состояние не описано.
- `readd-after-delete-reset-or-gap` - повторное добавление после удаления проверяет source-backed reset/preserve behavior или фиксирует `GAP-*`.

Для `property_type = checkbox-list`:

- `list-visible-when-condition-true` - список отображается при source-backed условии.
- `list-hidden-when-condition-false` - список скрыт при обратной ветке, если она следует из source.
- `dictionary-values-shown` - значения списка соответствуют `DICT-*`.
- `no-selection-rejected` - отсутствие выбора блокирует действие, если список обязателен.
- `single-selection-accepted` - один выбранный чекбокс удовлетворяет обязательности.
- `multiple-selection-accepted` - несколько чекбоксов можно выбрать одновременно, если source задает multiple selection.
- `selection-can-be-cleared` - выбранный чекбокс можно снять, если source задает редактируемость/изменяемость списка.

Для `property_type = print-form-output`:

- `print-form-generated` - печатная форма/документ формируется или открывается.
- `print-form-content-mapping` - значения в документе соответствуют source-backed маппингу полей.

`print-form-generated` не покрывает `print-form-content-mapping`. Если source требует сформировать документ, но не задает состав/маппинг данных, создавай TC только на формирование и отдельный `GAP-*` на проверку содержимого.

Для `property_type = date-passport-validity`:

- `passport-before-14-rejected` - дата выдачи до 14-летия отклоняется с source-backed подсказкой.
- `passport-14-to-20-plus-45-window` - окно от 14 лет до 20 лет + 45 дней разложено на boundary/equivalence checks.
- `passport-20-plus-1-to-45-plus-45-window` - окно от 20 лет + 1 день до 45 лет + 45 дней разложено на boundary/equivalence checks.
- `passport-45-plus-indefinite-window` - бессрочность после 45 лет проверяется отдельным классом.

Для `property_type = date-validity-window`:

- `lower-boundary-accepted` - нижняя граница принимается.
- `upper-boundary-accepted` - верхняя граница принимается.
- `off-boundary-rejected` - значение за границей отклоняется с source-backed oracle или фиксируется узкий `GAP-*`.

Для видимых UI-behavior property types:

- `hint-behavior`: `hint-triggered`, `hint-cleared`.
- `validation-message`: `message-triggered`.
- `red-highlight`: `highlight-triggered`.
- `action-confirmation`: `confirmation-message-shown`, `confirmation-accept-continues`, `confirmation-cancel-stays`.
- `action-navigation`: `navigation-target-opened`.
- `address-required-components`: `region-and-house-required`, `missing-apartment-or-private-house-hint`.

Если конкретный класс нельзя проверить из-за отсутствия fixture, product/catalog condition, support workbook или UI evidence, строка все равно создается, но `planned_tc_or_gap` должен ссылаться на конкретный `GAP-*`, а `review_notes` должен объяснять блокер.

## Gate Правила

- Каждая obligation row с `status != not-applicable` должна иметь `TC-*` или `GAP-*`.
- Один `source_property_id` не должен иметь две строки с одинаковым `obligation_class`.
- Нельзя считать `numeric-format` покрытым, если отсутствует хотя бы один обязательный класс.
- Нельзя считать `format-mask` / `default-mask` покрытыми через numeric-only TC: нужен отдельный TC/GAP с oracle по видимой маске.
- Нельзя считать `amount-tags` покрытым только по факту наличия справочника: нужны отдельные проверки отображения значений и заполнения поля после выбора.
- Нельзя считать `exact-length` покрытым без отдельных строк `N`, `N-1` и `N+1` или узких `GAP-*` для непроверяемых классов.
- Нельзя считать action-created block покрытым только проверками обязательности его внутренних полей: нужна отдельная строка optionality/no-action или `GAP-*`.
- Нельзя считать repeatable block покрытым одним добавлением и одним удалением, если source разрешает несколько блоков: нужны независимость и lifecycle удаления.
- Нельзя считать checkbox-list покрытым только сверкой справочника: нужны ветки выбора/обязательности/multiple selection, когда они следуют из source.
- Нельзя считать формирование печатной формы покрытием корректности ее данных без source-backed content mapping.
- Нельзя отправлять все паспортное date-window правило в один `GAP-*`, если source/PDF содержит возрастные окна, граничные дни или тексты подсказок; gap допустим только для тестовых часов, фикстуры или неясной boundary convention.
- Нельзя отправлять видимую подсказку, сообщение, красную подсветку, подтверждение или переход в `metadata_only` / общий `gap_unclear` из-за отсутствующей интеграционной фикстуры. Видимая часть остается obligation row с `TC-*` или узким `GAP-*`.
- `Package Test Design Plan` должен строиться из obligation rows, а не напрямую из общего атома, если для `property_type` определены обязательные классы.
