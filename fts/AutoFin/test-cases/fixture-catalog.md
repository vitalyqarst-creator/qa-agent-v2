# AutoFin Fixture Catalog

## Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| generated_on | `2026-07-04` |
| source_dir | `fts/AutoFin/test-cases` |
| excluded | `14-application-card.md` aggregate file to avoid duplicate fixture rows |

## Summary

- Source files scanned: `15`
- Test cases with fixture IDs or explicit test data: `244`
- Distinct fixture IDs: `30`

## Source File Coverage

| source_file | total_tc_headings | tc_with_fixture_or_test_data |
| --- | ---: | ---: |
| `14-application-card-calculator-summary-entrypoints.md` | 4 | 2 |
| `14-application-card-client-addresses.md` | 27 | 25 |
| `14-application-card-client-contacts-and-extra-info.md` | 27 | 16 |
| `14-application-card-client-personal-data.md` | 15 | 12 |
| `14-application-card-document-recognition-popup.md` | 8 | 2 |
| `14-application-card-documents-and-questionnaire-files.md` | 31 | 27 |
| `14-application-card-employment-income-gosuslugi.md` | 44 | 35 |
| `14-application-card-participants-coborrower-pledger.md` | 28 | 11 |
| `14-application-card-passport-current-and-previous.md` | 54 | 50 |
| `14-application-card-task-title-and-common-actions.md` | 5 | 2 |
| `14-application-card-visual-assessment-consents-checks.md` | 19 | 14 |
| `section-16-print-form-generation.md` | 16 | 16 |
| `section-17-universal-application-common-actions.md` | 1 | 0 |
| `section-18-visual-assessment-criteria.md` | 13 | 8 |
| `section-4.2-applications-menu-search.md` | 24 | 24 |

## Fixture ID Index

| fixture_id | used_by |
| --- | --- |
| `FIX-APP-01` | `TC-AMSR-001 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-02` | `TC-AMSR-001 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-03` | `TC-AMSR-002 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-003 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-016 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-017 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-018 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-019 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-024 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-04` | `TC-AMSR-005 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-019 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-05` | `TC-AMSR-006 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-06` | `TC-AMSR-007 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-07` | `TC-AMSR-008 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-DATE-01` | `TC-AMSR-009 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-KM-FREE` | `TC-AMSR-021 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-KM-OTHER` | `TC-AMSR-020 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-SORT-01` | `TC-AMSR-013 (section-4.2-applications-menu-search.md)` |
| `FIX-APP-TABLE-01` | `TC-AMSR-014 (section-4.2-applications-menu-search.md)` |
| `FIX-INVALID-FORMAT-01` | `TC-AMSR-015 (section-4.2-applications-menu-search.md)` |
| `FIX-NO-RESULT-01` | `TC-AMSR-004 (section-4.2-applications-menu-search.md)` |
| `FIX-PFG-ADDITIONAL-INCOME-TYPE` | `TC-AF-PFG-013 (section-16-print-form-generation.md)` |
| `FIX-PFG-ADDR-DIFFERENT` | `TC-AF-PFG-007 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-014 (section-16-print-form-generation.md)` |
| `FIX-PFG-ADDR-SAME` | `TC-AF-PFG-007 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-014 (section-16-print-form-generation.md)` |
| `FIX-PFG-BASE` | `TC-AF-PFG-001 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-003 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-004 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-011 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-012 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-016 (section-16-print-form-generation.md)` |
| `FIX-PFG-FIO-CHANGED` | `TC-AF-PFG-004 (section-16-print-form-generation.md)` |
| `FIX-PFG-INCOME-ALL` | `TC-AF-PFG-012 (section-16-print-form-generation.md)`<br>`TC-AF-PFG-013 (section-16-print-form-generation.md)` |
| `FIX-PFG-MARRIAGE` | `TC-AF-PFG-005 (section-16-print-form-generation.md)` |
| `FIX-PFG-NOT-WORKING-PENSIONER` | `TC-AF-PFG-008 (section-16-print-form-generation.md)` |
| `FIX-PFG-OPF` | `TC-AF-PFG-010 (section-16-print-form-generation.md)` |
| `FIX-PFG-PREV-PASSPORTS-5` | `TC-AF-PFG-015 (section-16-print-form-generation.md)` |
| `FIX-PFG-RELATION` | `TC-AF-PFG-009 (section-16-print-form-generation.md)` |
| `FIX-PFG-SOCIAL-STATUS` | `TC-AF-PFG-006 (section-16-print-form-generation.md)` |
| `FIX-PFG-WORKING` | `TC-AF-PFG-008 (section-16-print-form-generation.md)` |
| `FIX-ROLE-01` | `TC-AMSR-001 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-002 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-012 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-020 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-021 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-022 (section-4.2-applications-menu-search.md)`<br>`TC-AMSR-023 (section-4.2-applications-menu-search.md)` |
| `FX-001` | `TC-ACCEI-020 (14-application-card-client-contacts-and-extra-info.md)` |
| `FX-002` | `TC-ACCEI-021 (14-application-card-client-contacts-and-extra-info.md)` |

## Test Data By Source File

### `14-application-card-calculator-summary-entrypoints.md`

#### `TC-ACCS-002` - Отображение параметров краткой информации с этапа кредитного калькулятора

- Fixture IDs: none explicit

Test data:

```markdown
- Сумма кредита: `1500000 Р`.
- VIN: `XW8ZZZ61ZKG000001`.
- Ставка: `12,5 %`.
- Платеж в месяц: `35000 Р`.
- Срок: `60 мес`.
```

#### `TC-ACCS-004` - Открытие окна кредитного калькулятора с предзаполненными данными по заявке

- Fixture IDs: none explicit

Test data:

```markdown
- Заявка содержит VIN `XW8ZZZ61ZKG000001`.
- Заявка содержит сумму кредита `1500000 Р`.
```

### `14-application-card-client-addresses.md`

#### `TC-ACCA-001` - Отображение блока адресов клиента и поля адреса регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Заявка с доступной анкетой клиента.
```

#### `TC-ACCA-002` - Разложение найденного DaData адреса регистрации по ручным полям

- Fixture IDs: none explicit

Test data:

```markdown
Адрес, который DaData находит и который содержит регион, город, улицу, дом и квартиру.
```

#### `TC-ACCA-003` - Подсказка при ненайденном DaData адресе регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Адресная строка, для которой DaData не находит адрес.
```

#### `TC-ACCA-004` - Подсказка при адресе регистрации без квартиры

- Fixture IDs: none explicit

Test data:

```markdown
Адрес регистрации с регионом и домом, но без квартиры.
```

#### `TC-ACCA-005` - Значение по умолчанию переключателя ручного ввода адреса регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-006` - Автосборка адреса регистрации при ручном заполнении

- Fixture IDs: none explicit

Test data:

```markdown
Почтовый индекс `123456`, регион `Москва`, район `Тверской`, населенный пункт пустой, город `Москва`, улица `Тверская`, дом `1`, корпус `2`, квартира `3`.
```

#### `TC-ACCA-007` - Отображение ручных полей адреса регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-008` - Обязательность региона и дома в ручном адресе регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-009` - Маркеры условной обязательности населенного пункта и города адреса регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-010` - Допустимые числовые значения в ручных числовых полях адреса регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Почтовый индекс `123456`, корпус `2`, квартира `34`.
```

#### `TC-ACCA-011` - Подсказка о квартире в ручном адресе регистрации при невыбранном частном доме

- Fixture IDs: none explicit

Test data:

```markdown
Ручной адрес регистрации с регионом и домом, но без квартиры.
```

#### `TC-ACCA-012` - Отображение и default флажка частного дома для адреса регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Адрес регистрации без квартиры.
```

#### `TC-ACCA-013` - Снятие подсказки о квартире при отметке частного дома регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Адрес регистрации без квартиры.
```

#### `TC-ACCA-014` - Default совпадения фактического адреса с адресом регистрации

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-015` - Отображение фактического адреса при несовпадении с регистрацией

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-016` - Разложение найденного DaData фактического адреса по ручным полям

- Fixture IDs: none explicit

Test data:

```markdown
Фактический адрес, который DaData находит и который содержит регион, город, улицу, дом и квартиру.
```

#### `TC-ACCA-017` - Подсказка при ненайденном DaData фактическом адресе

- Fixture IDs: none explicit

Test data:

```markdown
Адресная строка, для которой DaData не находит адрес.
```

#### `TC-ACCA-018` - Подсказка при фактическом адресе без квартиры

- Fixture IDs: none explicit

Test data:

```markdown
Фактический адрес с регионом и домом, но без квартиры.
```

#### `TC-ACCA-019` - Отображение ручных полей фактического адреса

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-026` - Адрес из DaData заполняет kladr в модели данных

- Fixture IDs: none explicit

Test data:

```markdown
Адрес регистрации или фактического места жительства, найденный через DaData и содержащий известный код КЛАДР.
```

#### `TC-ACCA-020` - Автосборка фактического адреса при ручном заполнении

- Fixture IDs: none explicit

Test data:

```markdown
Почтовый индекс `654321`, регион `Красноярский край`, район пустой, населенный пункт пустой, город `Красноярск`, улица `Мира`, дом `10`, корпус пустой, квартира `20`.
```

#### `TC-ACCA-021` - Обязательность ключевых ручных полей фактического адреса

- Fixture IDs: none explicit

Test data:

```markdown
Новая или очищенная анкета клиента.
```

#### `TC-ACCA-022` - Допустимые числовые значения в ручных числовых полях фактического адреса

- Fixture IDs: none explicit

Test data:

```markdown
Квартира `45`, почтовый индекс `654321`.
```

#### `TC-ACCA-023` - Подсказка о квартире в ручном фактическом адресе при невыбранном частном доме

- Fixture IDs: none explicit

Test data:

```markdown
Ручной фактический адрес с регионом и домом, но без квартиры.
```

#### `TC-ACCA-024` - Отображение и default флажка частного дома для фактического адреса

- Fixture IDs: none explicit

Test data:

```markdown
Фактический адрес без квартиры.
```

### `14-application-card-client-contacts-and-extra-info.md`

#### `TC-ACCEI-003` - Редактируемость полей контактов и дополнительной информации кроме ИНН клиента

- Fixture IDs: none explicit

Test data:

```markdown
- Мобильный телефон: `9123456789`.
- E-mail: `client@example.test`.
- Кодовое слово: `Север`.
- Семейное положение: `Холост / не замужем`.
- Количество иждивенцев: `2`.
```

#### `TC-ACCEI-005` - Ввод 10 цифр и отображение шаблона +7 (9xx) xxx-xx-xx в поле Мобильный телефон

- Fixture IDs: none explicit

Test data:

```markdown
- Мобильный телефон: `9123456789`.
```

#### `TC-ACCEI-006` - Ввод одного e-mail адреса с символом @

- Fixture IDs: none explicit

Test data:

```markdown
- E-mail: `client@example.test`.
```

#### `TC-ACCEI-008` - UI-маркеры взаимной обязательности полей дополнительного телефона

- Fixture IDs: none explicit

Test data:

```markdown
- Тип телефона: `Мобильный` из `DICT-001`.
- Номер телефона: `9234567890`.
```

#### `TC-ACCEI-009` - Значения справочника Тип телефона

- Fixture IDs: none explicit

Test data:

```markdown
- Активные значения `DICT-001`: `Мобильный`, `Домашний`, `Рабочий`.
```

#### `TC-ACCEI-010` - Ввод 10 цифр и отображение шаблона +7 (9xx) xxx-xx-xx в номер дополнительного телефона

- Fixture IDs: none explicit

Test data:

```markdown
- Номер телефона: `9234567890`.
```

#### `TC-ACCEI-014` - Ввод текстовых значений с дефисом в ФИО контактного лица

- Fixture IDs: none explicit

Test data:

```markdown
- Фамилия: `Петров-Сидоров`.
- Имя: `Анна-Мария`.
- Отчество: `Игоревна`.
```

#### `TC-ACCEI-015` - Значения справочника Отношение к заявителю

- Fixture IDs: none explicit

Test data:

```markdown
- Активные значения `DICT-002`: `супруг/супруга`, `отец/мать`, `сестра/брат`, `теща/свекровь/тесть/свекр`, `сын/дочь`, `друг/знакомый/коллега`, `иное`.
```

#### `TC-ACCEI-016` - Отображение дополнительного текстового поля при отношении Иное

- Fixture IDs: none explicit

Test data:

```markdown
- Отношение к заявителю: `иное`.
```

#### `TC-ACCEI-017` - Ввод 10 цифр и отображение шаблона +7 (9xx) xxx-xx-xx в телефон контактного лица

- Fixture IDs: none explicit

Test data:

```markdown
- Телефон: `9345678901`.
```

#### `TC-ACCEI-018` - Ввод текущей даты в дату рождения контактного лица

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2026`.
```

#### `TC-ACCEI-020` - Ввод 12 цифр ИНН клиента и успешная верификация устанавливает ИНН проверен в Да

- Fixture IDs: `FX-001`

Test data:

```markdown
- ИНН клиента: `500100732259`.
```

#### `TC-ACCEI-021` - Неуспешная верификация ИНН делает кнопку Далее недоступной

- Fixture IDs: `FX-002`

Test data:

```markdown
- ИНН клиента: `111111111111`.
```

#### `TC-ACCEI-023` - Значения справочника Семейное положение

- Fixture IDs: none explicit

Test data:

```markdown
- Активные значения `DICT-003`: `Холост / не замужем`, `Женат / замужем`.
```

#### `TC-ACCEI-024` - Ввод числового значения в количество иждивенцев

- Fixture IDs: none explicit

Test data:

```markdown
- Количество иждивенцев: `2`.
```

#### `TC-ACCEI-026` - Автозаполнение ИНН клиента после заполнения идентифицирующих полей

- Fixture IDs: none explicit

Test data:

```markdown
- Дата выдачи паспорта: валидная дата из тестового набора.
```

### `14-application-card-client-personal-data.md`

#### `TC-ACPD-014` - Подсказки DaData для полей предыдущей ФИО

- Fixture IDs: none explicit

Test data:

```markdown
- Предыдущая фамилия для подсказки DaData: `Сидоров`.
- Предыдущее имя для подсказки DaData: `Иван`.
- Предыдущее отчество для подсказки DaData: `Петрович`.
```

#### `TC-ACPD-015` - Дата рождения раньше границы 100 лет не принимается

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения раньше границы `текущая дата - 100 лет`: `29.06.1926`.
```

#### `TC-ACPD-003` - Редактируемость основных полей персональных данных и read-only состояние ID клиента

- Fixture IDs: none explicit

Test data:

```markdown
- Фамилия: `Иванов`.
- Имя: `Петр`.
- Отчество: `Сергеевич`.
- Дата рождения: `30.06.2000`.
- Значение переключателя `Клиент менял ФИО`: `Да`.
```

#### `TC-ACPD-004` - Формат допустимого ввода текстовых значений с дефисом в текущую ФИО клиента

- Fixture IDs: none explicit

Test data:

```markdown
- Фамилия: `Иванов-Петров`.
- Имя: `Анна-Мария`.
- Отчество: `Сергеевна`.
```

#### `TC-ACPD-005` - Автоматическое заполнение ID клиента после сохранения заявки

- Fixture IDs: none explicit

Test data:

```markdown
- Черновая заявка без заполненного `ID клиента`.
```

#### `TC-ACPD-006` - Значения справочника Пол клиента

- Fixture IDs: none explicit

Test data:

```markdown
- Активные значения `DICT-001`: `Мужчина`, `Женщина`.
```

#### `TC-ACPD-007` - Обновление пола после заполнения ФИО через подсказку DaData

- Fixture IDs: none explicit

Test data:

```markdown
- ФИО для подсказки DaData: `Иванов Иван Иванович`.
- Ожидаемое значение `Пол` из `DICT-001`: `Мужчина`.
```

#### `TC-ACPD-008` - Ввод даты рождения на границе 18 лет

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения на границе `текущая дата - 18 лет`: `30.06.2008`.
```

#### `TC-ACPD-010` - Переключение признака Клиент менял ФИО между Да и Нет

- Fixture IDs: none explicit

Test data:

```markdown
- Значения переключателя: `Да`, `Нет`.
```

#### `TC-ACPD-011` - Отображение полей предыдущей ФИО при значении Да

- Fixture IDs: none explicit

Test data:

```markdown
- Значение `Клиент менял ФИО`: `Да`.
```

#### `TC-ACPD-012` - Скрытие полей предыдущей ФИО при значении Нет

- Fixture IDs: none explicit

Test data:

```markdown
- Значение `Клиент менял ФИО`: `Нет`.
```

#### `TC-ACPD-013` - Формат допустимого ввода текстовых значений с дефисом в предыдущую ФИО клиента

- Fixture IDs: none explicit

Test data:

```markdown
- Предыдущая фамилия: `Сидорова-Петрова`.
- Предыдущее имя: `Мария-Анна`.
- Предыдущее отчество: `Игоревна`.
```

### `14-application-card-document-recognition-popup.md`

#### `TC-AFDRP-003` - Состав раскрывающегося списка `Тип документа` в popup распознавания

- Fixture IDs: none explicit

Test data:

```markdown
Активные значения `DICT-001`: `ВУ`, `СНИЛС`, `Загран. паспорт`, `Паспорт`, `Анкета`.
```

#### `TC-AFDRP-008` - Распознавание документа при наличии файла запускает запрос и заполняет поля заявки

- Fixture IDs: none explicit

Test data:

```markdown
- Файл документа поддерживаемого формата: `recognition-passport.pdf`.
- Fixture распознавания возвращает значения для полей заявки, соответствующих выбранному типу документа.
```

### `14-application-card-documents-and-questionnaire-files.md`

#### `TC-AF-DOC-002` - Загрузка анкеты клиента через проводник в поддерживаемых форматах

- Fixture IDs: none explicit

Test data:

```markdown
Файлы: `client-questionnaire.jpg`, `client-questionnaire.png`, `client-questionnaire.pdf`.
```

#### `TC-AF-DOC-003` - Загрузка анкеты клиента через Drag and Drop

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `client-questionnaire-dnd.pdf`.
```

#### `TC-AF-DOC-004` - Прием анкеты клиента с размером файла не более 40 МБ

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `client-questionnaire-40mb.pdf`, размер файла не более 40 МБ.
```

#### `TC-AF-DOC-005` - Ошибка при загрузке анкеты клиента с файлом больше 40 МБ

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `client-questionnaire-41mb.pdf`, размер файла больше 40 МБ.
```

#### `TC-AF-DOC-006` - Загрузка паспорта клиента через проводник в поддерживаемых форматах

- Fixture IDs: none explicit

Test data:

```markdown
Файлы: `passport-client.jpg`, `passport-client.png`, `passport-client.pdf`.
```

#### `TC-AF-DOC-007` - Загрузка паспорта клиента через Drag and Drop

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `passport-client-dnd.pdf`.
```

#### `TC-AF-DOC-008` - Прием паспорта клиента с размером файла не более 40 МБ

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `passport-client-40mb.pdf`, размер файла не более 40 МБ.
```

#### `TC-AF-DOC-009` - Ошибка при загрузке паспорта клиента с неподдерживаемым форматом

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `passport-client.txt`.
```

#### `TC-AF-DOC-010` - Значение по умолчанию и список поля «Тип документа»

- Fixture IDs: none explicit

Test data:

```markdown
Ожидаемые значения `DICT-001`: `ВУ`, `СНИЛС`, `Загран. паспорт`.
```

#### `TC-AF-DOC-012` - Загрузка второго документа после выбора типа документа через проводник

- Fixture IDs: none explicit

Test data:

```markdown
Тип документа: `ВУ`; файл: `driver-license.pdf`.
```

#### `TC-AF-DOC-013` - Загрузка второго документа через Drag and Drop

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `driver-license-dnd.pdf`.
```

#### `TC-AF-DOC-014` - Ошибка при загрузке второго документа с файлом больше 40 МБ

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `driver-license-41mb.pdf`, размер файла больше 40 МБ.
```

#### `TC-AF-DOC-015` - Видимость поля «Серия» для выбранного типа документа

- Fixture IDs: none explicit

Test data:

```markdown
Значения типа документа: `ВУ`, `Загран. паспорт`.
```

#### `TC-AF-DOC-016` - Отсутствие поля «Серия» для типа документа СНИЛС

- Fixture IDs: none explicit

Test data:

```markdown
Значение типа документа: `СНИЛС`.
```

#### `TC-AF-DOC-017` - Ввод реквизитов второго документа в видимые поля

- Fixture IDs: none explicit

Test data:

```markdown
Номер: `345678`; дата выдачи: текущая календарная дата; кем выдан: `ОВД Тестового района`.
```

#### `TC-AF-DOC-018` - Запрет будущей даты выдачи второго документа

- Fixture IDs: none explicit

Test data:

```markdown
Дата выдачи: календарная дата позже текущей даты.
```

#### `TC-AF-DOC-019` - Просмотр прикрепленного документа через пиктограмму «глаз»

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `passport-client.pdf`.
```

#### `TC-AF-DOC-020` - Скрытие прикрепленного документа через пиктограмму «корзина»

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `passport-client.pdf`.
```

#### `TC-AF-DOC-023` - Отображение нескольких файлов анкеты клиента через запятую

- Fixture IDs: none explicit

Test data:

```markdown
Файлы: `client-questionnaire-page-1.pdf`, `client-questionnaire-page-2.pdf`.
```

#### `TC-AF-DOC-024` - Отображение нескольких файлов паспорта клиента через запятую

- Fixture IDs: none explicit

Test data:

```markdown
Файлы: `passport-client-page-1.pdf`, `passport-client-page-2.pdf`.
```

#### `TC-AF-DOC-025` - Отображение нескольких файлов второго документа через запятую

- Fixture IDs: none explicit

Test data:

```markdown
Тип документа: `ВУ`; файлы: `driver-license-page-1.pdf`, `driver-license-page-2.pdf`.
```

#### `TC-AF-DOC-026` - Ошибка при загрузке анкеты клиента с неподдерживаемым форматом

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `client-questionnaire.txt`.
```

#### `TC-AF-DOC-027` - Ошибка при загрузке второго документа с неподдерживаемым форматом

- Fixture IDs: none explicit

Test data:

```markdown
Файл: `driver-license.txt`.
```

#### `TC-AF-DOC-028` - Обязательность второго документа зависит от типа программы

- Fixture IDs: none explicit

Test data:

```markdown
Проверяемые варианты:
- программа не ГОС;
- программа ГОС;
- программа для инвалидов.
```

#### `TC-AF-DOC-029` - Анкета клиента сохраняется в электронном архиве после добавления файла

- Fixture IDs: none explicit

Test data:

```markdown
Файл `client-questionnaire-archive.pdf`, формат pdf, размер не более 40 МБ.
```

#### `TC-AF-DOC-030` - Паспорт клиента сохраняется в электронном архиве после добавления файла

- Fixture IDs: none explicit

Test data:

```markdown
Файл `passport-client-archive.pdf`, формат pdf, размер не более 40 МБ.
```

#### `TC-AF-DOC-031` - Второй документ сохраняется в электронном архиве после добавления файла

- Fixture IDs: none explicit

Test data:

```markdown
Файл `driver-license-archive.pdf`, формат pdf, размер не более 40 МБ.
```

### `14-application-card-employment-income-gosuslugi.md`

#### `TC-AFEIG-002` - Состав значений раскрывающегося списка социального статуса

- Fixture IDs: none explicit

Test data:

```markdown
Значения DICT-001: собственник бизнеса; ИП; работа по найму; пенсионер (не работает); самозанятый; военнослужащий.
```

#### `TC-AFEIG-003` - Поля работодателя отображаются для работы по найму

- Fixture IDs: none explicit

Test data:

```markdown
Социальный статус / тип занятости: работа по найму.
```

#### `TC-AFEIG-004` - Поля работодателя скрыты для пенсионера и самозанятого

- Fixture IDs: none explicit

Test data:

```markdown
Проверяемые значения: пенсионер (не работает); самозанятый.
```

#### `TC-AFEIG-005` - Рабочий телефон отображается для военнослужащего

- Fixture IDs: none explicit

Test data:

```markdown
Социальный статус / тип занятости: военнослужащий.
```

#### `TC-AFEIG-006` - Недействующая организация DaData блокирует переход далее

- Fixture IDs: none explicit

Test data:

```markdown
Организация из тестового контура DaData со статусом, отличным от «действующая».
```

#### `TC-AFEIG-007` - Выбор действующей организации DaData заполняет организационные поля

- Fixture IDs: none explicit

Test data:

```markdown
Действующая организация тестового контура DaData с известными значениями статуса организации, наименования, ОПФ, ИНН и фактического адреса.
```

#### `TC-AFEIG-008` - Состав значений ОПФ

- Fixture IDs: none explicit

Test data:

```markdown
Значения DICT-002: ООО; ПАО; АО (НАО); полное товарищество; товарищество на вере; хозяйственное партнерство; производственный кооператив; КФХ; ФГУП; ГУП; МУП; потребительский кооператив; общественная организация; общественное движение; ассоциация; союз; ТСН (ТСЖ); казачье общество; община коренных народов; нотариальная палата; адвокатская палата; фонд; учреждение; АНО; религиозная организация; госкорпорация; госкомпания; публично-правовая компания; ИП; глава КФХ; самозанятый; частнопрактикующее лицо; простое товарищество; инвестиционное товарищество; ПИФ; филиал иностранного юрлица.
```

#### `TC-AFEIG-009` - Состав значений типа должности

- Fixture IDs: none explicit

Test data:

```markdown
Значения DICT-003: Сотрудник/Рабочий/Ассистент; Индивидуальный предприниматель; Главный специалист/Руководитель среднего звена; Топ менеджер/Руководитель высшего звена; Эксперт/Старший или Ведущий специалист.
```

#### `TC-AFEIG-010` - Поле должности отображается и принимает текст

- Fixture IDs: none explicit

Test data:

```markdown
Должность: Менеджер.
```

#### `TC-AFEIG-011` - Дата начала работы в компании отображается для работы по найму

- Fixture IDs: none explicit

Test data:

```markdown
Дата начала работы: 01.02.2024.
```

#### `TC-AFEIG-012` - Начало общего трудового стажа принимает формат ММ.ГГГГ

- Fixture IDs: none explicit

Test data:

```markdown
Начало стажа: 05.2018.
```

#### `TC-AFEIG-013` - Рабочий телефон принимает 10 цифр и использует шаблон +7

- Fixture IDs: none explicit

Test data:

```markdown
Рабочий телефон: 9234567890.
```

#### `TC-AFEIG-014` - Основной среднемесячный доход принимает минимальную сумму X

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: 2000 при значении системной переменной `X = 2000`.
```

#### `TC-AFEIG-015` - Основной среднемесячный доход менее X показывает ошибку

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: 1999 при значении системной переменной `X = 2000`.
```

#### `TC-AFEIG-016` - Основной среднемесячный доход более 1 000 000 показывает предупреждение

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: 1000001.
```

#### `TC-AFEIG-017` - Корзина основной работы очищает поля подблока

- Fixture IDs: none explicit

Test data:

```markdown
Заполненные поля основной работы: организация, ОПФ, фактический адрес работы, рабочий телефон, тип должности, должность, дата начала работы, начало стажа, среднемесячный доход.
```

#### `TC-AFEIG-020` - Состав значений типа дохода

- Fixture IDs: none explicit

Test data:

```markdown
Значения DICT-004: Аренда; Пенсия; Дивиденды.
```

#### `TC-AFEIG-021` - Тип дополнительного дохода нельзя добавить повторно

- Fixture IDs: none explicit

Test data:

```markdown
Проверяемые значения: Пенсия; Аренда; Дивиденды.
```

#### `TC-AFEIG-022` - Дополнительный среднемесячный доход принимает числовое значение

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: 15000.
```

#### `TC-AFEIG-023` - Корзина дополнительного дохода удаляет блок-повторитель

- Fixture IDs: none explicit

Test data:

```markdown
Тип дохода: Аренда; среднемесячный доход: 15000.
```

#### `TC-AFEIG-025` - Для бумажного подтверждения отображается поле загрузки подтверждения дохода

- Fixture IDs: none explicit

Test data:

```markdown
Способ подтверждения дохода: Бумажное.
```

#### `TC-AFEIG-026` - Для Госуслуг отображается текст о QR-коде подтверждения доходов

- Fixture IDs: none explicit

Test data:

```markdown
Способ подтверждения дохода: Госуслуги.
```

#### `TC-AFEIG-028` - Подтверждение дохода загружается через проводник

- Fixture IDs: none explicit

Test data:

```markdown
Файл `income-proof.pdf`, формат pdf, размер не более 40 МБ.
```

#### `TC-AFEIG-029` - Подтверждение дохода загружается через Drag and Drop

- Fixture IDs: none explicit

Test data:

```markdown
Файл `income-proof-dnd.jpg`, формат jpg, размер не более 40 МБ.
```

#### `TC-AFEIG-030` - Некорректный файл подтверждения дохода показывает текст ошибки

- Fixture IDs: none explicit

Test data:

```markdown
Файл `income-proof.txt`.
```

#### `TC-AFEIG-031` - После загрузки отображается название файла подтверждения дохода

- Fixture IDs: none explicit

Test data:

```markdown
Файл `income-proof.pdf`, формат pdf, размер не более 40 МБ.
```

#### `TC-AFEIG-035` - Основной среднемесячный доход не принимает нечисловое значение

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: `abc`.
```

#### `TC-AFEIG-036` - Основной среднемесячный доход не принимает отрицательное значение

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: `-2000`.
```

#### `TC-AFEIG-037` - Основной среднемесячный доход принимает дробное значение через точку и отображает сотые

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: `66660.981`.
```

#### `TC-AFEIG-038` - Основной среднемесячный доход 1 000 000 не показывает предупреждение о превышении

- Fixture IDs: none explicit

Test data:

```markdown
Среднемесячный доход: 1000000.
```

#### `TC-AFEIG-040` - После загрузки нескольких файлов подтверждения дохода названия отображаются через запятую

- Fixture IDs: none explicit

Test data:

```markdown
Файлы `income-proof.pdf` и `tax-return.png`, форматы pdf/png, размер каждого файла не более 40 МБ.
```

#### `TC-AFEIG-041` - Рабочий телефон, должность и дата начала работы скрыты для пенсионера и самозанятого

- Fixture IDs: none explicit

Test data:

```markdown
Проверяемые значения: пенсионер (не работает); самозанятый.
```

#### `TC-AFEIG-042` - Файл подтверждения дохода размером более 40 МБ показывает текст ошибки

- Fixture IDs: none explicit

Test data:

```markdown
Файл `income-proof.pdf`, формат pdf, размер более 40 МБ.
```

#### `TC-AFEIG-043` - При выборе Госуслуг и сохранении заявки направляется запрос в сервис

- Fixture IDs: none explicit

Test data:

```markdown
Способ подтверждения дохода: Госуслуги.
```

#### `TC-AFEIG-044` - Подтверждение дохода сохраняется в электронном архиве после добавления файла

- Fixture IDs: none explicit

Test data:

```markdown
Файл `income-proof-archive.pdf`, формат pdf, размер не более 40 МБ.
```

### `14-application-card-participants-coborrower-pledger.md`

#### `TC-ACP-008` - Исключение FT-backed блоков и полей из окна залогодателя

- Fixture IDs: none explicit

Test data:

```markdown
Исключения по ФТ: `Краткая информация с калькулятора`; `Сведения о занятости`; `контактные лица`; `кодовое слово`; `СНИЛС (при прикреплении документа)`; `верификация ИНН ФЛ`; `семейное положение`; `количество иждивенцев`; `социальный статус`; `подтверждение дохода`.
```

#### `TC-ACP-012` - Доступность редактирования при выбранном участнике

- Fixture IDs: none explicit

Test data:

```markdown
Участник: `Иванов Иван Иванович`.
```

#### `TC-ACP-014` - Открытие окна редактирования с данными выбранного участника

- Fixture IDs: none explicit

Test data:

```markdown
Участник: тип `созаемщик`; ФИО `Иванов Иван Иванович`; паспорт `4512 123456`.
```

#### `TC-ACP-016` - Доступность корзины при выбранном участнике

- Fixture IDs: none explicit

Test data:

```markdown
Участник: `Иванов Иван Иванович`.
```

#### `TC-ACP-018` - Открытие подтверждения удаления участника

- Fixture IDs: none explicit

Test data:

```markdown
Участник: `Иванов Иван Иванович`.
```

#### `TC-ACP-019` - Удаление участника при подтверждении Да

- Fixture IDs: none explicit

Test data:

```markdown
Участник: `Иванов Иван Иванович`.
```

#### `TC-ACP-020` - Отмена удаления участника

- Fixture IDs: none explicit

Test data:

```markdown
Участник: `Иванов Иван Иванович`.
```

#### `TC-ACP-021` - Отображение типа участия в таблице участников

- Fixture IDs: none explicit

Test data:

```markdown
Участник 1: создан как `созаемщик`. Участник 2: создан как `залогодатель`.
```

#### `TC-ACP-022` - Отображение ФИО участника в таблице участников

- Fixture IDs: none explicit

Test data:

```markdown
ФИО участника: `Иванов Иван Иванович`.
```

#### `TC-ACP-023` - Отображение паспорта участника в таблице участников

- Fixture IDs: none explicit

Test data:

```markdown
Паспорт участника: `4512 123456`.
```

#### `TC-ACP-024` - Автозаполнение ID клиента участника после сохранения заявки

- Fixture IDs: none explicit

Test data:

```markdown
Участник: `Иванов Иван Иванович`. ID клиента из АБС: `ABS-COB-001`.
```

### `14-application-card-passport-current-and-previous.md`

#### `TC-ACPCP-003` - Редактируемость полей текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия: `1234`.
- Номер: `123456`.
- Код подразделения: `770001`.
- Кем выдан: `ГУ МВД России по г. Москве`.
- Дата выдачи: `30.06.2024`.
- Место рождения: `Г. МОСКВА`.
```

#### `TC-ACPCP-004` - Допустимый формат серии текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия: `1234`.
```

#### `TC-ACPCP-005` - Запрет трех одинаковых цифр подряд в серии текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия с тремя одинаковыми цифрами подряд: `1112`.
```

#### `TC-ACPCP-006` - Допустимый формат номера текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Номер: `123456`.
```

#### `TC-ACPCP-007` - Запрет шести одинаковых цифр подряд в номере текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Номер из шести одинаковых цифр: `111111`.
```

#### `TC-ACPCP-008` - Допустимый формат кода подразделения

- Fixture IDs: none explicit

Test data:

```markdown
- Код подразделения: `770001`.
```

#### `TC-ACPCP-009` - Маска отображения кода подразделения

- Fixture IDs: none explicit

Test data:

```markdown
- Код подразделения: `770001`.
```

#### `TC-ACPCP-010` - Режим выбора Кем выдан при ручном вводе подразделения Нет

- Fixture IDs: none explicit

Test data:

```markdown
- `Ввести вручную подразделение`: `Нет`.
```

#### `TC-ACPCP-011` - Предзаполнение Кем выдан по коду подразделения

- Fixture IDs: none explicit

Test data:

```markdown
- Код подразделения с доступной подсказкой DaData: `770001`.
```

#### `TC-ACPCP-014` - Переключение Ввести вручную подразделение

- Fixture IDs: none explicit

Test data:

```markdown
- Значения переключателя: `Да`, `Нет`.
```

#### `TC-ACPCP-015` - Ручное поле Кем выдан при значении Да

- Fixture IDs: none explicit

Test data:

```markdown
- `Ввести вручную подразделение`: `Да`.
```

#### `TC-ACPCP-016` - Пустое обязательное ручное поле Кем выдан

- Fixture IDs: none explicit

Test data:

```markdown
- `Ввести вручную подразделение`: `Да`.
- `Кем выдан`: пусто.
```

#### `TC-ACPCP-017` - Ввод строкового значения в ручное поле Кем выдан

- Fixture IDs: none explicit

Test data:

```markdown
- Кем выдан: `ГУ МВД России по г. Москве`.
```

#### `TC-ACPCP-018` - Допустимая дата выдачи текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Текущая дата стенда: `30.06.2026`.
- Дата выдачи: `01.07.2020`.
```

#### `TC-ACPCP-019` - Пустая обязательная дата выдачи текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Дата выдачи: пусто.
```

#### `TC-ACPCP-020` - Дата выдачи раньше 14-летия

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Дата_14: `30.06.2020`.
- Дата выдачи: `29.06.2020`.
```

#### `TC-ACPCP-021` - Дата выдачи на 14-летии

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Дата_14: `30.06.2020`.
- Текущая дата стенда: `30.06.2026`.
- Дата выдачи: `30.06.2020`.
```

#### `TC-ACPCP-022` - Паспорт до 20 лет действителен на Дата_20_90

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Текущая дата стенда: `28.09.2026` (`Дата_20_90`).
- Дата выдачи: `30.06.2020`.
```

#### `TC-ACPCP-023` - Дата выдачи на 20-летии входит в первый диапазон

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Дата_20: `30.06.2026`.
- Текущая дата стенда: `28.09.2026`.
- Дата выдачи: `30.06.2026`.
```

#### `TC-ACPCP-024` - Паспорт до 20 лет просрочен после Дата_20_90

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Текущая дата стенда: `29.09.2026` (`Дата_20_90 + 1 день`).
- Дата выдачи: `30.06.2020`.
```

#### `TC-ACPCP-025` - Дата выдачи на Дата_20_1 входит во второй диапазон

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Дата_20_1: `01.07.2026`.
- Текущая дата стенда: `28.09.2051`.
- Дата выдачи: `01.07.2026`.
```

#### `TC-ACPCP-026` - Паспорт после 20 лет действителен на Дата_45_90

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Текущая дата стенда: `28.09.2051` (`Дата_45_90`).
- Дата выдачи: `01.07.2026`.
```

#### `TC-ACPCP-027` - Дата выдачи перед 45-летием входит во второй диапазон

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Дата_45: `30.06.2051`.
- Текущая дата стенда: `28.09.2051`.
- Дата выдачи: `29.06.2051`.
```

#### `TC-ACPCP-028` - Паспорт после 20 лет просрочен после Дата_45_90

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Текущая дата стенда: `29.09.2051` (`Дата_45_90 + 1 день`).
- Дата выдачи: `01.07.2026`.
```

#### `TC-ACPCP-029` - Дата выдачи на 45-летии бессрочна

- Fixture IDs: none explicit

Test data:

```markdown
- Дата рождения: `30.06.2006`.
- Текущая дата стенда: `29.09.2051`.
- Дата выдачи: `30.06.2051`.
```

#### `TC-ACPCP-030` - Дата выдачи больше текущей даты

- Fixture IDs: none explicit

Test data:

```markdown
- Текущая дата стенда: `30.06.2026`.
- Дата выдачи: `01.07.2026`.
```

#### `TC-ACPCP-031` - Пустая дата выдачи текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Дата выдачи: пусто.
```

#### `TC-ACPCP-032` - Ввод места рождения

- Fixture IDs: none explicit

Test data:

```markdown
- Место рождения: `Г. МОСКВА`.
```

#### `TC-ACPCP-034` - Переключение Клиент менял паспорт

- Fixture IDs: none explicit

Test data:

```markdown
- Значения переключателя: `Да`, `Нет`.
```

#### `TC-ACPCP-035` - Автовыбор Клиент менял паспорт по дате выдачи менее трех лет назад

- Fixture IDs: none explicit

Test data:

```markdown
- Текущая дата стенда: `30.06.2026`.
- Дата выдачи текущего паспорта: `01.07.2023`.
```

#### `TC-ACPCP-036` - Отображение блока предыдущего паспорта при значении Да

- Fixture IDs: none explicit

Test data:

```markdown
- `Клиент менял паспорт`: `Да`.
```

#### `TC-ACPCP-037` - Скрытие блока предыдущего паспорта при значении Нет

- Fixture IDs: none explicit

Test data:

```markdown
- `Клиент менял паспорт`: `Нет`.
```

#### `TC-ACPCP-038` - Отображение кнопки Добавить паспорт

- Fixture IDs: none explicit

Test data:

```markdown
- `Клиент менял паспорт`: `Да`.
```

#### `TC-ACPCP-039` - Добавление последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- `Клиент менял паспорт`: `Да`.
```

#### `TC-ACPCP-040` - Отображение виджета Корзина для предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- `Клиент менял паспорт`: `Да`.
```

#### `TC-ACPCP-041` - Удаление блока предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- `Клиент менял паспорт`: `Да`.
- Добавлен блок предыдущего паспорта.
```

#### `TC-ACPCP-042` - Маркеры обязательности полей последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- `Клиент менял паспорт`: `Да`.
```

#### `TC-ACPCP-043` - Редактируемость полей последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия: `4321`.
- Номер: `654321`.
- Дата выдачи: `01.06.2020`.
```

#### `TC-ACPCP-044` - Допустимый формат серии последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия: `4321`.
```

#### `TC-ACPCP-045` - Запрет трех одинаковых цифр подряд в серии предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия с тремя одинаковыми цифрами подряд: `2223`.
```

#### `TC-ACPCP-046` - Допустимый формат номера последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Номер: `654321`.
```

#### `TC-ACPCP-047` - Запрет шести одинаковых цифр подряд в номере предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Номер из шести одинаковых цифр: `222222`.
```

#### `TC-ACPCP-048` - Ввод даты выдачи последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Дата выдачи предыдущего паспорта: `01.06.2020`.
```

#### `TC-ACPCP-049` - Числовой класс полей текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия: `1234`.
- Номер: `123456`.
- Код подразделения: `770001`.
```

#### `TC-ACPCP-050` - Числовой класс полей последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Серия: `4321`.
- Номер: `654321`.
```

#### `TC-ACPCP-051` - Запрет недопустимой длины и нечисловых символов в серии текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Проверяемые значения серии: `123`, `12345`, `12A4`, `12 4`, `+123`, `12.4`.
```

#### `TC-ACPCP-052` - Запрет недопустимой длины и нечисловых символов в номере текущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Проверяемые значения номера: `12345`, `1234567`, `12345A`, `123 45`, `+12345`, `123.45`.
```

#### `TC-ACPCP-053` - Запрет недопустимой длины и нечисловых символов в коде подразделения

- Fixture IDs: none explicit

Test data:

```markdown
- Проверяемые значения кода подразделения: `12345`, `1234567`, `12345A`, `123 45`, `+12345`, `123.45`.
```

#### `TC-ACPCP-054` - Запрет недопустимой длины и нечисловых символов в серии последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Проверяемые значения серии: `321`, `32109`, `32A1`, `32 1`, `+321`, `32.1`.
```

#### `TC-ACPCP-055` - Запрет недопустимой длины и нечисловых символов в номере последнего предыдущего паспорта

- Fixture IDs: none explicit

Test data:

```markdown
- Проверяемые значения номера: `65432`, `6543217`, `65432A`, `654 32`, `+65432`, `654.32`.
```

### `14-application-card-task-title-and-common-actions.md`

#### `TC-AF-CARD-002` - Заголовок карточки при редактировании существующей заявки

- Fixture IDs: none explicit

Test data:

```markdown
- Номер заявки: номер выбранной заявки из тестового контура.
```

#### `TC-AF-CARD-003` - Кнопка Далее проверяет готовность заявки и переводит на следующий этап

- Fixture IDs: none explicit

Test data:

```markdown
- Валидные значения для всех обязательных полей заявки.
- Набор обязательных документов по типу программы.
- Заполненная детализация доходов, если она требуется текущей заявке.
- `ИНН проверен = Да`.
- Выбранное предложение в кредитном калькуляторе.
```

### `14-application-card-visual-assessment-consents-checks.md`

#### `TC-ACVCC-003` - Отображение параметров визуальной оценки при выборе `Да`

- Fixture IDs: none explicit

Test data:

```markdown
- Значение поля `Визуальная информация`: `Да`.
```

#### `TC-ACVCC-004` - Checkbox-контролы для значений `Параметры визуальной оценки`

- Fixture IDs: none explicit

Test data:

```markdown
- Справочник `Параметры визуальной оценки`: полный состав групп и значений из `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md`.
```

#### `TC-ACVCC-005` - Отметка checkbox одного значения в `Параметры визуальной оценки`

- Fixture IDs: none explicit

Test data:

```markdown
- Любое значение списка `Параметры визуальной оценки` из Приложения 1, кроме `Другое (комментарий обязателен)`.
```

#### `TC-ACVCC-006` - Скрытие параметров визуальной оценки при значении `Нет`

- Fixture IDs: none explicit

Test data:

```markdown
- Значение поля `Визуальная информация`: `Нет`.
```

#### `TC-ACVCC-008` - Отображение виджета `Согласия` с полем `БКИ и персональные данные`

- Fixture IDs: none explicit

Test data:

```markdown
- Состав подблока `Согласия`: `APP2-CHECK-001` из `work/test-design/14-application-card/appendix-2-consents-checks-reference.md`.
```

#### `TC-ACVCC-010` - Проставление checkbox в поле `БКИ и персональные данные`

- Fixture IDs: none explicit

Test data:

```markdown
- Поле `БКИ и персональные данные`: подготовительное значение `Нет`, проверяемое значение `Да`.
```

#### `TC-ACVCC-011` - Отображение `FATCA/CRS проверка` и значение по умолчанию `Нет`

- Fixture IDs: none explicit

Test data:

```markdown
- Состав подблока `FATCA/CRS проверка`: `APP2-CHECK-002` из `work/test-design/14-application-card/appendix-2-consents-checks-reference.md`.
```

#### `TC-ACVCC-012` - Проставление checkbox `FATCA/CRS проверка`

- Fixture IDs: none explicit

Test data:

```markdown
- Поле `FATCA/CRS проверка`: `Да`.
```

#### `TC-ACVCC-013` - Отображение полей подблока `AML проверка`

- Fixture IDs: none explicit

Test data:

```markdown
- `Иностранное публичное должностное лицо`.
- `Должностное лицо публичной международной организации`.
- `Должностное лицо Российской Федерации, включенное в перечни должностей, определяемые Президентом Российской Федерации, а также назначаемое/освобождаемое от должности Президентом или Правительством Российской Федерации (РПДЛ)`.
- `Родственник ИПДЛ`.
- `Родственник МПДЛ`.
- `Родственник РПДЛ`.
```

#### `TC-ACVCC-014` - Значение по умолчанию `Нет` во всех полях `AML проверка`

- Fixture IDs: none explicit

Test data:

```markdown
- Поля подблока `AML проверка`: `APP2-CHECK-003` из `work/test-design/14-application-card/appendix-2-consents-checks-reference.md`.
```

#### `TC-ACVCC-015` - Проставление checkbox в поле подблока `AML проверка`

- Fixture IDs: none explicit

Test data:

```markdown
- Поле `Родственник РПДЛ`: `Да`.
```

#### `TC-ACVCC-016` - Появление комментария при выборе `Другое` в параметрах визуальной оценки

- Fixture IDs: none explicit

Test data:

```markdown
- Блок списка с checkbox `Другое (комментарий обязателен)`: любой отображенный блок 1-7 из Приложения 1.
```

#### `TC-ACVCC-017` - Сохранение введенного комментария при снятии и повторном выборе `Другое`

- Fixture IDs: none explicit

Test data:

```markdown
- Блок списка с checkbox `Другое (комментарий обязателен)`: любой отображенный блок 1-7 из Приложения 1.
- Значение поля `Комментарий`: `Тестовый комментарий`.
```

#### `TC-ACVCC-018` - Сообщение обязательности для пустого комментария при выбранном `Другое`

- Fixture IDs: none explicit

Test data:

```markdown
- Блок списка с checkbox `Другое (комментарий обязателен)`: любой отображенный блок 1-7 из Приложения 1.
- Значение поля `Комментарий`: пустое.
```

### `section-16-print-form-generation.md`

#### `TC-AF-PFG-001` - Автоматическое формирование заявления-анкеты по шаблону `Анкета клиента 04.02.2026.pdf`

- Fixture IDs: `FIX-PFG-BASE`

Test data:

```markdown
- Печатная форма: `Заявление-анкета на получение потребительского кредита`.
- Шаблон: `Анкета клиента 04.02.2026.pdf`.
```

#### `TC-AF-PFG-002` - Привязка шаблона к типу и точное соответствие тегов колонке `Тег`

- Fixture IDs: none explicit

Test data:

```markdown
- Oracle точного написания тегов: `FT4AutoFinFinal.docx`, section `4.4`, table 9, column `Тег`.
```

#### `TC-AF-PFG-003` - Заполнение блока `Параметры о кредите`

- Fixture IDs: `FIX-PFG-BASE`

Test data:

```markdown
- Теги блока: `<auto>`, `<loan_amount>`, `<monthly_payment>`, `<Loan term>`.
```

#### `TC-AF-PFG-004` - Заполнение персональных и паспортных данных заявителя

- Fixture IDs: `FIX-PFG-BASE`, `FIX-PFG-FIO-CHANGED`

Test data:

```markdown
- Теги персональных данных: `<last_name>`, `<first_name>`, `<middle_name>`, `<previous_last_name>`, `<previous_first_name>`, `<previous_middle_name>`, `<snils>`, `<code_word>`, `<inn>`.
- Теги действующего паспорта: `<serial_number>`, `<number>`, `<issue_date>`, `<issue_place>`.
- Тег иждивенцев: `<dependency>`.
```

#### `TC-AF-PFG-005` - Заполнение чек-бокса `Зарегистрированный брак`

- Fixture IDs: `FIX-PFG-MARRIAGE`

Test data:

```markdown
| case | значение `Семейное положение` | ожидаемый чек-бокс |
| --- | --- | --- |
| 1 | `женат/замужем` | `Да` |
| 2 | любое другое значение | `Нет` |
```

#### `TC-AF-PFG-006` - Заполнение чек-боксов `Социальный статус`

- Fixture IDs: `FIX-PFG-SOCIAL-STATUS`

Test data:

```markdown
Значения поля `Социальный статус`: `cобственник бизнеса/ИП`, `наемный работник`, `военнослужащий`, `пенсионер`, `самозанятый`.
```

#### `TC-AF-PFG-007` - Заполнение блока `Адрес фактического проживания`

- Fixture IDs: `FIX-PFG-ADDR-DIFFERENT`, `FIX-PFG-ADDR-SAME`

Test data:

```markdown
- Теги адреса: `<region_with_type>`, `<city_district>`, `<city>`, `<street>`, `<house>`, `<block>`, `<str>`, `<flat>`.
```

#### `TC-AF-PFG-008` - Заполнение блока `Контактная информация`

- Fixture IDs: `FIX-PFG-NOT-WORKING-PENSIONER`, `FIX-PFG-WORKING`

Test data:

```markdown
- Теги: `<mobile_phone>`, `<email>`, `<work_phone>`, `<home_phone>`.
```

#### `TC-AF-PFG-009` - Заполнение блока `Контактное лицо`

- Fixture IDs: `FIX-PFG-RELATION`

Test data:

```markdown
Значения поля `Отношение к заявителю`: `супруг/супруга`, `отец/мать`, `сестра/брат`, `теща/свекровь/тесть/свекр`, `сын/дочь`, `друг/знакомый/коллега`, `иное`.
```

#### `TC-AF-PFG-010` - Заполнение блока `Информация о работодателе`

- Fixture IDs: `FIX-PFG-OPF`

Test data:

```markdown
Значения поля `ОПФ`: `Гос. Предприятие (ГУП.ФГУП, МГУП, в/ч и пр.`, `ООО/АО`, `ИП`, `Прочее`.
```

#### `TC-AF-PFG-011` - Заполнение блока `Адрес местонахождения работодателя`

- Fixture IDs: `FIX-PFG-BASE`

Test data:

```markdown
- Теги адреса работодателя: `<region_with_type_job>`, `<city_district_job >`, `<city_job >`, `<street_job >`, `<house_job >`, `<block_job >`, `<str_job>`, `<office>`.
```

#### `TC-AF-PFG-012` - Заполнение блока `Сведения о доходе и должности заявителя`

- Fixture IDs: `FIX-PFG-BASE`, `FIX-PFG-INCOME-ALL`

Test data:

```markdown
- Теги: `<job_title>`, `<start_job_date>`, `<main_job_income>`, `<job_start>`, `<job_income>`.
```

#### `TC-AF-PFG-013` - Заполнение других регулярных доходов

- Fixture IDs: `FIX-PFG-ADDITIONAL-INCOME-TYPE`, `FIX-PFG-INCOME-ALL`

Test data:

```markdown
| тип дохода | ожидаемый чек-бокс | тег суммы |
| --- | --- | --- |
| `Аренда` | `Сдача в аренду квартиры` = `Да` | `<rent>` |
| `Пенсия` | `Пенсия` = `Да` | `<pension>` |
| `Дивиденды` | `Дивиденды` = `Да` | `<dividends>` |
```

#### `TC-AF-PFG-014` - Выбор адреса регистрации в блоке `Согласия на обработку ПДн`

- Fixture IDs: `FIX-PFG-ADDR-DIFFERENT`, `FIX-PFG-ADDR-SAME`

Test data:

```markdown
- `Тег 1`: `<region_with_type>`, `<city_district>`, `<city>`, `<street>`, `<house>`, `<block>`, `<str>`, `<flat>`.
- `Тег 2`: `<region_with_type_reg>`, `<city_district_reg>`, `<city_reg>`, `<street_reg>`, `<house_reg>`, `<block_reg>`, `<str_reg>`, `<flat_reg>`.
```

#### `TC-AF-PFG-015` - Заполнение кода подразделения и ранее выданных паспортов

- Fixture IDs: `FIX-PFG-PREV-PASSPORTS-5`

Test data:

```markdown
- Тег действующего паспорта: `<dep_code>`.
- Наборы тегов ранее выданных паспортов: `<serial_number_1>`..`<serial_number_5>`, `<number_1>`..`<number_5>`, `<issue_date_1>`..`<issue_date_5>`, `<issue_place_1>`..`<issue_place_5>`, `<dep_code_1>`..`<dep_code_5>`.
```

#### `TC-AF-PFG-016` - Отсутствие незаполненных или неизвестных тегов после генерации PDF

- Fixture IDs: `FIX-PFG-BASE`

Test data:

```markdown
- Перечень тегов: `DICT-PFG-001`.
```

### `section-18-visual-assessment-criteria.md`

#### `TC-VAC-003` - Выбор `Да` в поле `Визуальная информация` как условие показа параметров

- Fixture IDs: none explicit

Test data:

```markdown
Значение поля `Визуальная информация`: `Да`.
```

#### `TC-VAC-005` - Скрытие `Параметры визуальной оценки`, когда `Визуальная информация` не равна `Да`

- Fixture IDs: none explicit

Test data:

```markdown
Значение поля `Визуальная информация`: `Нет`.
```

#### `TC-VAC-006` - Состав списка `Параметры визуальной оценки` по `DICT-001`

- Fixture IDs: none explicit

Test data:

```markdown
Активные значения `DICT-001` из `work/test-design/section-18-visual-assessment-criteria/dictionary-inventory.md`.
```

#### `TC-VAC-007` - Checkbox-контролы для всех обычных значений критериев визуальной оценки

- Fixture IDs: none explicit

Test data:

```markdown
Все активные обычные значения `DICT-001` из `work/test-design/section-18-visual-assessment-criteria/dictionary-inventory.md`, кроме значений `Другое (комментарий обязателен)` и standalone comment-only rows.
```

#### `TC-VAC-009` - Отображение текстового поля при выборе `Другое`

- Fixture IDs: none explicit

Test data:

```markdown
Группа: `Сопровождение Клиента`; checkbox value: `Другое (комментарий обязателен)`.
```

#### `TC-VAC-011` - Отображение standalone `Комментарий` как отдельного поля ввода

- Fixture IDs: none explicit

Test data:

```markdown
Группы со standalone comment input: `Признаки алкоголика`, `Признаки наркомана`, `Прочие признаки (комментарий обязателен)`.
```

#### `TC-VAC-012` - Ввод текста в standalone поле `Комментарий`

- Fixture IDs: none explicit

Test data:

```markdown
Текст комментария: `Комментарий визуальной оценки алкоголика`.
```

#### `TC-VAC-013` - Выбор нескольких обычных критериев визуальной оценки

- Fixture IDs: none explicit

Test data:

```markdown
Группа: `Признаки алкоголика`; checkbox values: `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`, `Отечность, нездоровый цвет лица, синяки под глазами`.
```

### `section-4.2-applications-menu-search.md`

#### `TC-AMSR-001` - Первичная загрузка меню показывает активные заявки текущего автора

- Fixture IDs: `FIX-APP-01`, `FIX-APP-02`, `FIX-ROLE-01`

Test data:

```markdown
- `FIX-ROLE-01`
- `FIX-APP-01`
- `FIX-APP-02`
```

#### `TC-AMSR-002` - Поиск клиента по одному компоненту ФИО без учета регистра и по подстроке

- Fixture IDs: `FIX-APP-03`, `FIX-ROLE-01`

Test data:

```markdown
- `FIX-ROLE-01`
- `FIX-APP-03`
```

#### `TC-AMSR-003` - Поиск по комбинации полей фильтра

- Fixture IDs: `FIX-APP-03`

Test data:

```markdown
- `FIX-APP-03`
```

#### `TC-AMSR-004` - Сообщение при отсутствии результатов поиска

- Fixture IDs: `FIX-NO-RESULT-01`

Test data:

```markdown
- `FIX-NO-RESULT-01`
```

#### `TC-AMSR-005` - Поиск по мобильному телефону с нормализацией до 10 цифр без кода страны

- Fixture IDs: `FIX-APP-04`

Test data:

```markdown
- `FIX-APP-04`
```

#### `TC-AMSR-006` - Поиск по серии и номеру паспорта

- Fixture IDs: `FIX-APP-05`

Test data:

```markdown
- `FIX-APP-05`
```

#### `TC-AMSR-007` - Поиск по VIN из 17 допустимых символов

- Fixture IDs: `FIX-APP-06`

Test data:

```markdown
- `FIX-APP-06`
```

#### `TC-AMSR-008` - Поиск по полному и частичному номеру заявки

- Fixture IDs: `FIX-APP-07`

Test data:

```markdown
- `FIX-APP-07`
```

#### `TC-AMSR-009` - Поиск по диапазону дат заведения заявки

- Fixture IDs: `FIX-APP-DATE-01`

Test data:

```markdown
- `FIX-APP-DATE-01`
```

#### `TC-AMSR-010` - Default и reset множественного выбора статусов заявки

- Fixture IDs: none explicit

Test data:

```markdown
- `DICT-STATUS-01`
```

#### `TC-AMSR-011` - Фильтрация списка точек продаж с первого символа

- Fixture IDs: none explicit

Test data:

```markdown
- `DICT-POS-01`
```

#### `TC-AMSR-012` - Список автора заведения заявки использует справочник сотрудников с учетом ролевой модели

- Fixture IDs: `FIX-ROLE-01`

Test data:

```markdown
- `FIX-ROLE-01`
- `DICT-EMP-01`
```

#### `TC-AMSR-013` - Сортировка результатов по умолчанию по дате заведения заявки по убыванию

- Fixture IDs: `FIX-APP-SORT-01`

Test data:

```markdown
- `FIX-APP-SORT-01`
```

#### `TC-AMSR-014` - Состав и нередактируемость колонок таблицы `Заявки`

- Fixture IDs: `FIX-APP-TABLE-01`

Test data:

```markdown
- `FIX-APP-TABLE-01`
```

#### `TC-AMSR-015` - Форматная валидация заполненных фильтров перед поиском

- Fixture IDs: `FIX-INVALID-FORMAT-01`

Test data:

```markdown
- `FIX-INVALID-FORMAT-01`
```

#### `TC-AMSR-016` - Действие `Найти` отображает результаты в таблице `Заявки`

- Fixture IDs: `FIX-APP-03`

Test data:

```markdown
- `FIX-APP-03`
```

#### `TC-AMSR-017` - Действие `Очистить` сбрасывает состояние поиска

- Fixture IDs: `FIX-APP-03`

Test data:

```markdown
- `FIX-APP-03`
```

#### `TC-AMSR-018` - Кнопка `i` открывает popup с информацией о заявке

- Fixture IDs: `FIX-APP-03`

Test data:

```markdown
- `FIX-APP-03`
```

#### `TC-AMSR-019` - Доступность `Продолжить` зависит от выбора ровно одной строки

- Fixture IDs: `FIX-APP-03`, `FIX-APP-04`

Test data:

```markdown
- `FIX-APP-03`
- `FIX-APP-04`
```

#### `TC-AMSR-020` - Недоступность продолжения по заявке, привязанной к другому КМ

- Fixture IDs: `FIX-APP-KM-OTHER`, `FIX-ROLE-01`

Test data:

```markdown
- `FIX-ROLE-01`
- `FIX-APP-KM-OTHER`
```

#### `TC-AMSR-021` - Продолжение доступной заявки привязывает ее к текущему КМ

- Fixture IDs: `FIX-APP-KM-FREE`, `FIX-ROLE-01`

Test data:

```markdown
- `FIX-ROLE-01`
- `FIX-APP-KM-FREE`
```

#### `TC-AMSR-022` - Действие `Создать заявку` открывает пустую карточку заявки

- Fixture IDs: `FIX-ROLE-01`

Test data:

```markdown
- `FIX-ROLE-01`
```

#### `TC-AMSR-023` - Действие `Кредитный калькулятор` открывает пустой кредитный калькулятор

- Fixture IDs: `FIX-ROLE-01`

Test data:

```markdown
- `FIX-ROLE-01`
```

#### `TC-AMSR-024` - Двойной клик по строке открывает заявку в режиме просмотра

- Fixture IDs: `FIX-APP-03`

Test data:

```markdown
- `FIX-APP-03`
```
