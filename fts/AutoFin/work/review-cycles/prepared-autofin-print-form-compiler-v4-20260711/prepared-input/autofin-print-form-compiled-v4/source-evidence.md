# Prepared Source Evidence

- package_id: `autofin-print-form-compiled-v4`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-print-form-compiler-v4-20260711/prepared-input/.autofin-print-form-compiled-v4.compiled-evidence.md`
- source_sha256: `a3e41171e735749f0f6ede9a57c38c6aa9f8189433a756f685307dbc8c2e96bd`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## OBL-001

- obligation: OBL-001 | WP-01 | PFG-ATOM-001 | ATOM-001 | print-form-output | print-form-generated | Система формирует PDF заявления-анкеты на основании данных Клиента. | 4.4 paragraph; PDF p.36 | TC-AF-PFG-001 | covered | `GAP-003` ограничивает entrypoint, но не отменяет output obligation.
- atom: ATOM-001 | WP-01 | 4.4 paragraph; PDF p.36 | Система автоматически формирует печатную форму `Заявление-анкета на получение потребительского кредита` на основании данных о Клиенте из Системы. | TC-AF-PFG-001 | covered | GAP-003

- plan: PD-PFG-001 | WP-01 | generated-document | 4.4 paragraph; PDF p.36; GAP-001; GAP-003 | ATOM-001`; `ATOM-002 | Сформировать заявление-анкету и проверить используемый шаблон | positive | print-form-generated | FIX-PFG-BASE | PDF заявления-анкеты сформирован по шаблону `Анкета клиента 04.02.2026.pdf` | FT`; `PDF`; `GAP-001`; `GAP-003 | TC-AF-PFG-001 | covered

## OBL-002

- obligation: OBL-002 | WP-01 | PFG-ATOM-002 | ATOM-002 | print-form-output | template-selected | PDF сформирован по шаблону `Анкета клиента 04.02.2026.pdf`. | 4.4 document table; PDF p.36 | TC-AF-PFG-001 | covered | `GAP-001` сохраняет source-parity ограничение.
- atom: ATOM-002 | WP-01 | 4.4 document table; PDF p.36 | Для печатной формы используется шаблон `Анкета клиента 04.02.2026.pdf`. | TC-AF-PFG-001 | covered | GAP-001

- plan: PD-PFG-001 | WP-01 | generated-document | 4.4 paragraph; PDF p.36; GAP-001; GAP-003 | ATOM-001`; `ATOM-002 | Сформировать заявление-анкету и проверить используемый шаблон | positive | print-form-generated | FIX-PFG-BASE | PDF заявления-анкеты сформирован по шаблону `Анкета клиента 04.02.2026.pdf` | FT`; `PDF`; `GAP-001`; `GAP-003 | TC-AF-PFG-001 | covered

## OBL-003

- obligation: OBL-003 | WP-01 | PFG-ATOM-003 | ATOM-003 | configuration | template-type-binding | Не создавать executable check без наблюдаемого артефакта конфигурации. | 4.4 paragraph before tag table | GAP-006 | gap | Нет UI/API/файла настройки.
- atom: ATOM-003 | WP-01 | 4.4 paragraph before tag table | Шаблон привязан к типу, собранному на основе тегов из таблицы раздела `4.4`. | GAP-006 | gap | -

- plan: PD-PFG-003 | WP-01 | configuration | 4.4 paragraph before tag table | ATOM-003 | Проверить конфигурационную привязку шаблона к типу тегов | gap | missing configuration artifact | not_available | Проверяемый UI/API/файл настройки не указан в ФТ | GAP-006 | GAP-006 | gap

## OBL-004

- obligation: OBL-004 | WP-01 | PFG-ATOM-004 | ATOM-004 | print-form-output | placeholder-residue | В сформированном PDF нет остаточных плейсхолдеров `<...>`. | 4.4 paragraph before tag table | TC-AF-PFG-002 | covered | Точные имена тегов берутся из DOCX; `GAP-002`.
- atom: ATOM-004 | WP-01 | 4.4 paragraph before tag table | Теги в шаблоне называются так же, как в колонке `Тег`. | TC-AF-PFG-002 | covered | GAP-002

- plan: PD-PFG-002 | WP-01 | generated-document-mapping | 4.4 paragraph before tag table; GAP-002 | ATOM-004 | Проверить отсутствие незаполненных и неизвестных плейсхолдеров после генерации | negative | placeholder-residue | DICT-001 | В PDF нет остаточных тегов формата `<...>` | FT`; `DICT-001`; `GAP-002 | TC-AF-PFG-002 | covered

## OBL-005

- obligation: OBL-005 | WP-02 | PFG-ATOM-005 | ATOM-005 | print-form-output | credit-parameters-mapping | Параметры кредита и автомобиля в PDF соответствуют заявке. | 4.4 tag rows 1-4 | TC-AF-PFG-003 | covered | Фикстура задаётся как precondition; `GAP-005`.
- atom: ATOM-005 | WP-02 | 4.4 tag rows 1-4 | Теги блока `Параметры о кредите` заполняются данными автомобиля и кредита. | TC-AF-PFG-003 | covered | GAP-005

- plan: PD-PFG-004 | WP-02 | generated-document-mapping | 4.4 tag rows 1-4; GAP-005 | ATOM-005 | Проверить заполнение параметров кредита и автомобиля | positive | direct tag mapping | FIX-PFG-BASE | Значения блока параметров кредита соответствуют заявке | FT`; `GAP-005 | TC-AF-PFG-003 | covered

## OBL-006

- obligation: OBL-006 | WP-02 | PFG-ATOM-006 | ATOM-006 | print-form-output | identity-mapping | Персональные и паспортные данные в PDF соответствуют заявке. | 4.4 tag rows 5-19 | TC-AF-PFG-004 | covered | -
- atom: ATOM-006 | WP-02 | 4.4 tag rows 5-19 | Теги персональных, паспортных данных и прежних ФИО заполняются согласно описанию строк таблицы. | TC-AF-PFG-004 | covered | -

- plan: PD-PFG-005 | WP-02 | generated-document-mapping | 4.4 tag rows 5-19 | ATOM-006 | Проверить заполнение персональных, паспортных данных и прежних ФИО | positive | direct tag mapping | FIX-PFG-FIO-CHANGED | Персональные и паспортные теги заполнены значениями заявки | FT | TC-AF-PFG-004 | covered

## OBL-007

- obligation: OBL-007 | WP-02 | PFG-ATOM-007 | ATOM-007 | checkbox-list | marriage-branch | Для каждой ветки выставлен только ожидаемый чек-бокс брака. | 4.4 tag row 18 | TC-AF-PFG-005 | covered | `DICT-002` задаёт branch values.
- atom: ATOM-007 | WP-02 | 4.4 tag row 18 | Чек-бокс `Зарегистрированный брак` зависит от значения `Семейное положение`. | TC-AF-PFG-005 | covered | -

- plan: PD-PFG-006 | WP-02 | decision-table | 4.4 tag row 18 | ATOM-007 | Проверить ветки чек-бокса зарегистрированного брака | positive | condition branches | FIX-PFG-MARRIAGE-YES`; `FIX-PFG-MARRIAGE-NO`; `DICT-002 | Для каждой ветки выставлен только ожидаемый чек-бокс | FT`; `DICT-002 | TC-AF-PFG-005 | covered

## OBL-008

- obligation: OBL-008 | WP-02 | PFG-ATOM-008 | ATOM-008 | checkbox-list | social-status-branch | Для выбранного социального статуса выставлен соответствующий чек-бокс. | 4.4 tag row 20 | TC-AF-PFG-006 | covered | `DICT-003` задаёт branch values.
- atom: ATOM-008 | WP-02 | 4.4 tag row 20 | Чек-бокс социального статуса выставляется для выбранного значения социального статуса. | TC-AF-PFG-006 | covered | -

- plan: PD-PFG-007 | WP-02 | checkbox-list | 4.4 tag row 20 | ATOM-008 | Проверить чек-боксы социального статуса по значениям справочника | positive | active dictionary values | FIX-PFG-SOCIAL-STATUS`; `DICT-003 | Для выбранного социального статуса выставлен только соответствующий чек-бокс | FT`; `DICT-003 | TC-AF-PFG-006 | covered

## OBL-009

- obligation: OBL-009 | WP-02 | PFG-ATOM-009 | ATOM-009 | dependency | addresses-equal | При совпадении адресов теги и чек-бокс соответствуют equal-branch. | 4.4 tag rows 21-29 | TC-AF-PFG-007 | covered | condition=true
- atom: ATOM-009 | WP-02 | 4.4 tag rows 21-29 | Блок фактического адреса заполняется адресными тегами и чек-боксом совпадения с адресом регистрации. | TC-AF-PFG-007`; `TC-AF-PFG-008 | covered | -

- plan: PD-PFG-008A | WP-02 | dependency | 4.4 tag rows 21-29 | ATOM-009 | Проверить ветку совпадения фактического адреса с адресом регистрации | dependency | condition=true | FIX-PFG-ADDR-SAME | Адресные теги и чек-бокс соответствуют совпадающим адресам | FT | TC-AF-PFG-007 | covered

- plan: PD-PFG-008B | WP-02 | dependency | 4.4 tag rows 21-29 | ATOM-009 | Проверить ветку отличия фактического адреса от адреса регистрации | dependency | condition=false | FIX-PFG-ADDR-DIFFERENT | Адресные теги и чек-бокс соответствуют различающимся адресам | FT | TC-AF-PFG-008 | covered

## OBL-010

- obligation: OBL-010 | WP-02 | PFG-ATOM-009 | ATOM-009 | dependency | addresses-different | При различии адресов теги и чек-бокс соответствуют different-branch. | 4.4 tag rows 21-29 | TC-AF-PFG-008 | covered | condition=false
- atom: ATOM-009 | WP-02 | 4.4 tag rows 21-29 | Блок фактического адреса заполняется адресными тегами и чек-боксом совпадения с адресом регистрации. | TC-AF-PFG-007`; `TC-AF-PFG-008 | covered | -

- plan: PD-PFG-008A | WP-02 | dependency | 4.4 tag rows 21-29 | ATOM-009 | Проверить ветку совпадения фактического адреса с адресом регистрации | dependency | condition=true | FIX-PFG-ADDR-SAME | Адресные теги и чек-бокс соответствуют совпадающим адресам | FT | TC-AF-PFG-007 | covered

- plan: PD-PFG-008B | WP-02 | dependency | 4.4 tag rows 21-29 | ATOM-009 | Проверить ветку отличия фактического адреса от адреса регистрации | dependency | condition=false | FIX-PFG-ADDR-DIFFERENT | Адресные теги и чек-бокс соответствуют различающимся адресам | FT | TC-AF-PFG-008 | covered

## OBL-011

- obligation: OBL-011 | WP-02 | PFG-ATOM-010 | ATOM-010 | print-form-output | contacts-mapping | Мобильный телефон, email и домашний телефон в PDF соответствуют заявке. | 4.4 tag rows 30-31, 33 | TC-AF-PFG-009 | covered | -
- atom: ATOM-010 | WP-02 | 4.4 tag rows 30-31, 33 | Контактные теги мобильного телефона, email и домашнего телефона заполняются данными заявки. | TC-AF-PFG-009 | covered | -

- plan: PD-PFG-009A | WP-02 | generated-document-mapping | 4.4 tag rows 30-31, 33 | ATOM-010 | Проверить прямой маппинг мобильного телефона, email и домашнего телефона | positive | direct tag mapping | FIX-PFG-BASE | Контактные теги заполнены значениями заявки | FT | TC-AF-PFG-009 | covered

## OBL-012

- obligation: OBL-012 | WP-02 | PFG-ATOM-018 | ATOM-018 | dependency | work-phone-working | Для работающего клиента `<work_phone>` заполнен значением из заявки. | 4.4 tag row 32 | TC-AF-PFG-010 | covered | condition=true
- atom: ATOM-018 | WP-02 | 4.4 tag row 32 | `<work_phone>` заполняется только если клиент не является неработающим пенсионером. | TC-AF-PFG-010`; `TC-AF-PFG-011 | covered | -

- plan: PD-PFG-009B | WP-02 | dependency | 4.4 tag row 32 | ATOM-018 | Проверить вывод рабочего телефона для работающего клиента | dependency | condition=true | FIX-PFG-WORKING | `<work_phone>` заполнен рабочим телефоном из заявки | FT | TC-AF-PFG-010 | covered

- plan: PD-PFG-009C | WP-02 | dependency | 4.4 tag row 32 | ATOM-018 | Проверить отсутствие заполненного рабочего телефона для неработающего пенсионера | dependency | condition=false | FIX-PFG-NOT-WORKING-PENSIONER | `<work_phone>` не выводится как заполненное значение | FT | TC-AF-PFG-011 | covered

## OBL-013

- obligation: OBL-013 | WP-02 | PFG-ATOM-018 | ATOM-018 | dependency | work-phone-pensioner | Для неработающего пенсионера `<work_phone>` не выводится как заполненное значение. | 4.4 tag row 32 | TC-AF-PFG-011 | covered | condition=false
- atom: ATOM-018 | WP-02 | 4.4 tag row 32 | `<work_phone>` заполняется только если клиент не является неработающим пенсионером. | TC-AF-PFG-010`; `TC-AF-PFG-011 | covered | -

- plan: PD-PFG-009B | WP-02 | dependency | 4.4 tag row 32 | ATOM-018 | Проверить вывод рабочего телефона для работающего клиента | dependency | condition=true | FIX-PFG-WORKING | `<work_phone>` заполнен рабочим телефоном из заявки | FT | TC-AF-PFG-010 | covered

- plan: PD-PFG-009C | WP-02 | dependency | 4.4 tag row 32 | ATOM-018 | Проверить отсутствие заполненного рабочего телефона для неработающего пенсионера | dependency | condition=false | FIX-PFG-NOT-WORKING-PENSIONER | `<work_phone>` не выводится как заполненное значение | FT | TC-AF-PFG-011 | covered

## OBL-014

- obligation: OBL-014 | WP-02 | PFG-ATOM-011 | ATOM-011 | checkbox-list | contact-relation | Данные контактного лица и чек-бокс отношения соответствуют заявке. | 4.4 tag rows 34-39 | TC-AF-PFG-012 | covered | `DICT-004` задаёт branch values.
- atom: ATOM-011 | WP-02 | 4.4 tag rows 34-39 | Блок контактного лица заполняется ФИО, датой рождения, телефоном и чек-боксом отношения к заявителю. | TC-AF-PFG-012 | covered | -

- plan: PD-PFG-010 | WP-02 | checkbox-list | 4.4 tag rows 34-39 | ATOM-011 | Проверить чек-боксы отношения контактного лица к заявителю | positive | active dictionary values | FIX-PFG-RELATION`; `DICT-004 | Для выбранного отношения выставлен только соответствующий чек-бокс | FT`; `DICT-004 | TC-AF-PFG-012 | covered

## OBL-015

- obligation: OBL-015 | WP-03 | PFG-ATOM-012 | ATOM-012 | checkbox-list | employer-opf | ОПФ, наименование и ИНН работодателя отражены в PDF. | 4.4 tag rows 40-43 | TC-AF-PFG-013 | covered | `DICT-005` задаёт branch values.
- atom: ATOM-012 | WP-03 | 4.4 tag rows 40-43 | Блок работодателя заполняет чек-бокс ОПФ, наименование и ИНН работодателя. | TC-AF-PFG-013 | covered | -

- plan: PD-PFG-011 | WP-03 | checkbox-list | 4.4 tag rows 40-43 | ATOM-012 | Проверить чек-боксы ОПФ и данные работодателя | positive | active dictionary values | FIX-PFG-OPF`; `DICT-005 | ОПФ, наименование и ИНН работодателя отражены в PDF | FT`; `DICT-005 | TC-AF-PFG-013 | covered

## OBL-016

- obligation: OBL-016 | WP-03 | PFG-ATOM-013 | ATOM-013 | print-form-output | employer-address | Адрес работодателя в PDF соответствует заявке. | 4.4 tag rows 44-51 | TC-AF-PFG-014 | covered | -
- atom: ATOM-013 | WP-03 | 4.4 tag rows 44-51 | Адрес местонахождения работодателя заполняется тегами адреса работы. | TC-AF-PFG-014 | covered | -

- plan: PD-PFG-012 | WP-03 | generated-document-mapping | 4.4 tag rows 44-51 | ATOM-013 | Проверить заполнение адреса местонахождения работодателя | positive | direct tag mapping | FIX-PFG-BASE | Адресные теги работодателя заполнены значениями заявки | FT | TC-AF-PFG-014 | covered

## OBL-017

- obligation: OBL-017 | WP-03 | PFG-ATOM-014 | ATOM-014 | print-form-output | employment-income | Должность, дата нача работы, основной и общий доход в PDF соответствуют правилам таблицы. | 4.4 tag rows 52-54, 56 | TC-AF-PFG-015 | covered | -
- atom: ATOM-014 | WP-03 | 4.4 tag rows 52-54, 56 | Должность, дата начала работы, основной доход и общий доход выводятся по правилам таблицы. | TC-AF-PFG-015 | covered | -

- plan: PD-PFG-013 | WP-03 | generated-document-mapping | 4.4 tag rows 52-54, 56 | ATOM-014 | Проверить должность, дату начала работы, основной и общий доход | positive | direct and calculated income mapping | FIX-PFG-INCOME-ALL | Должность, дата начала работы, основной и общий доход заполнены по правилам таблицы | FT | TC-AF-PFG-015 | covered

## OBL-018

- obligation: OBL-018 | WP-03 | PFG-ATOM-015 | ATOM-015 | calculation | job-start-calculation | Не создавать executable calculation без раскрытого справочника и oracle. | 4.4 tag row 55 | GAP-004 | gap | Справочник `Стаж работы` не раскрыт.
- atom: ATOM-015 | WP-03 | 4.4 tag row 55 | `<job_start>` выводит начало общего трудового стажа по расчету через справочник `Стаж работы`. | GAP-004 | gap | -

- plan: PD-PFG-014 | WP-03 | calculation | 4.4 tag row 55 | ATOM-015 | Проверить расчет `<job_start>` через справочник `Стаж работы` | gap | missing dictionary/calculation oracle | DICT-007 | Справочник и расчетный oracle не раскрыты в ФТ | GAP-004 | GAP-004 | gap

## OBL-019

- obligation: OBL-019 | WP-03 | PFG-ATOM-016 | ATOM-016 | checkbox-list | additional-income | Тип дополнительного дохода определяет чек-бокс и сумму в PDF. | 4.4 tag rows 57-60 | TC-AF-PFG-016 | covered | `DICT-006` задаёт branch values.
- atom: ATOM-016 | WP-03 | 4.4 tag rows 57-60 | Чек-боксы и суммы других регулярных доходов зависят от типов дополнительных доходов. | TC-AF-PFG-016 | covered | -

- plan: PD-PFG-015 | WP-03 | checkbox-list | 4.4 tag rows 57-60 | ATOM-016 | Проверить чек-боксы и суммы дополнительных доходов | positive | active dictionary values | FIX-PFG-ADDITIONAL-INCOME-TYPE`; `DICT-006 | Для типа дохода выставлен соответствующий чек-бокс и сумма | FT`; `DICT-006 | TC-AF-PFG-016 | covered

## OBL-020

- obligation: OBL-020 | WP-04 | PFG-ATOM-017 | ATOM-017 | print-form-output | consent-address-passport | Блок согласий использует правильный адрес и данные действующего паспорта. | 4.4 tag rows 61-87 | TC-AF-PFG-017 | covered | Прямой и conditional mapping.
- atom: ATOM-017 | WP-04 | 4.4 tag rows 61-87 | Блок согласий заполняет адрес регистрации по правилу tag1/tag2, код подразделения действующего паспорта и данные ранее выданных паспортов 1-5. | TC-AF-PFG-017`; `TC-AF-PFG-018 | covered | -

- plan: PD-PFG-016 | WP-04 | generated-document-mapping | 4.4 tag rows 61-87 | ATOM-017 | Проверить адрес регистрации, код подразделения и блок согласий | positive | consent block mapping | FIX-PFG-ADDR-SAME`; `FIX-PFG-ADDR-DIFFERENT | Блок согласий использует правильную строку адреса и паспортные данные | FT | TC-AF-PFG-017 | covered

- plan: PD-PFG-017 | WP-04 | repeatable-block | 4.4 tag rows 62-87 | ATOM-017 | Проверить пять наборов ранее выданных паспортов | positive | repeatable passport blocks 1..5 | FIX-PFG-PREV-PASSPORTS-5 | Каждый набор ранее выданного паспорта заполнен в своем блоке | FT | TC-AF-PFG-018 | covered

## OBL-021

- obligation: OBL-021 | WP-04 | PFG-ATOM-017 | ATOM-017 | repeatable-block | previous-passports-1-5 | Каждый из пяти наборов ранее выданных паспортов заполнен в своём блоке. | 4.4 tag rows 62-87 | TC-AF-PFG-018 | covered | Пять repeatable slots.
- atom: ATOM-017 | WP-04 | 4.4 tag rows 61-87 | Блок согласий заполняет адрес регистрации по правилу tag1/tag2, код подразделения действующего паспорта и данные ранее выданных паспортов 1-5. | TC-AF-PFG-017`; `TC-AF-PFG-018 | covered | -

- plan: PD-PFG-016 | WP-04 | generated-document-mapping | 4.4 tag rows 61-87 | ATOM-017 | Проверить адрес регистрации, код подразделения и блок согласий | positive | consent block mapping | FIX-PFG-ADDR-SAME`; `FIX-PFG-ADDR-DIFFERENT | Блок согласий использует правильную строку адреса и паспортные данные | FT | TC-AF-PFG-017 | covered

- plan: PD-PFG-017 | WP-04 | repeatable-block | 4.4 tag rows 62-87 | ATOM-017 | Проверить пять наборов ранее выданных паспортов | positive | repeatable passport blocks 1..5 | FIX-PFG-PREV-PASSPORTS-5 | Каждый набор ранее выданного паспорта заполнен в своем блоке | FT | TC-AF-PFG-018 | covered

## GAP-001

source_refs: FT4AutoFinFinal.xhtml`, section `4.4`, document table row `Заявление-анкета на получение потребительского кредита`, column `Шаблон
В XHTML значение шаблона пустое, в PDF указано `Анкета клиента 04.02.2026.pdf`.
В тест-кейсах используется значение из PDF, потому что PDF явно содержит шаблон, а прежняя scope-clarification уже закрывала это как ожидаемое значение.

## GAP-002

source_refs: `FT4AutoFinFinal.xhtml`, tag table; `FT4AutoFinFinal.pdf`, pages 36-39
XHTML и PDF содержат визуальные/конвертационные пробелы внутри части тегов, например `<last_ n ame>`, `<code_ word >`, `< d ividends>`, `<serial_number _1 >`.
Точное написание тегов для oracle берется из `FT4AutoFinFinal.docx`, table 9, column `Тег`; XHTML остается приоритетным источником структуры и требований.

## GAP-003

source_refs: FT4AutoFinFinal.xhtml`, section `4.4
Раздел описывает формирование печатной формы и маппинг, но не задает UI-кнопку, API, роль, статус заявки или точку запуска генерации.
В шагах используется формулировка `сформировать печатную форму доступным в системе способом`; проверка UI entrypoint остается вне scope.

## GAP-004

source_refs: FT4AutoFinFinal.xhtml`, section `4.4`, tag row `<job_start>
Краткое описание указывает расчет `Дата (сегодня (Месяц.год)) - значение из справочника «Стаж работы»`, но раздел `4.4` не раскрывает справочник и oracle расчета.
`<job_start>` исключен из executable TC до появления расчетного oracle или раскрытого справочника `Стаж работы`. Остальные строки блока доходов покрыты `TC-AF-PFG-015`.

## GAP-005

source_refs: `FT4AutoFinFinal.xhtml`, section `4.4`, all mapping rows
Раздел `4.4` называет исходные поля анкеты, но не описывает, как создать все исходные состояния через UI.
Фикстуры задают требуемое состояние заявки; способ подготовки данных не проверяется в этом scope.

## GAP-006

source_refs: `FT4AutoFinFinal.xhtml`, section `4.4`, paragraph before tag table
ФТ требует, чтобы шаблон был привязан к типу, собранному на основе тегов, и настроен на основе этого типа.
Executable TC на конфигурационную привязку шаблона удален. Black-box риск неправильных тегов покрывается `TC-AF-PFG-002` через отсутствие незаполненных/неизвестных плейсхолдеров в сформированном PDF.

## DICT-002

DICT-002 | Семейное положение для чек-бокса `Зарегистрированный брак` | source/FT4AutoFinFinal.xhtml | 4.4`; row `Зарегистрированный брак | extracted | `женат/замужем`; `холост/не замужем` как представитель значения без зарегистрированного брака | none_required:not_applicable | ATOM-007`; `TC-AF-PFG-005 | none_required:extracted | ФТ задает позитивную ветку для `женат/замужем`; негативная ветка проверяется representative fixture для любого другого значения.

## DICT-003

DICT-003 | Социальный статус для чек-боксов печатной формы | source/FT4AutoFinFinal.xhtml | 4.4`; row `Социальный статус | extracted | cобственник бизнеса/ИП`; `наемный работник`; `военнослужащий`; `пенсионер`; `самозанятый | none_required:not_applicable | ATOM-008`; `TC-AF-PFG-006 | none_required:extracted | Значение `cобственник бизнеса/ИП` сохранено в написании источника.

## DICT-004

DICT-004 | Отношение к заявителю для чек-боксов печатной формы | source/FT4AutoFinFinal.xhtml | 4.4`; rows `Отношение к Заявителю | extracted | супруг/супруга`; `отец/мать`; `сестра/брат`; `теща/свекровь/тесть/свекр`; `сын/дочь`; `друг/знакомый/коллега`; `иное | none_required:not_applicable | ATOM-011`; `TC-AF-PFG-012 | none_required:extracted | Используется для одной параметризованной проверки однотипных чек-боксов.

## DICT-005

DICT-005 | ОПФ работодателя для чек-боксов печатной формы | source/FT4AutoFinFinal.xhtml | 4.4`; row `Организационно-правовая форма | extracted | Гос. Предприятие (ГУП.ФГУП, МГУП, в/ч и пр.`; `ООО/АО`; `ИП`; `Прочее | none_required:not_applicable | ATOM-012`; `TC-AF-PFG-013 | none_required:extracted | Значение `Гос. Предприятие...` сохранено как в источнике, включая незакрытую скобку.

## DICT-006

DICT-006 | Тип дополнительного дохода для чек-боксов печатной формы | source/FT4AutoFinFinal.xhtml | 4.4`; row `Другие регулярные доходы (в месяц), руб. | extracted | Аренда`; `Пенсия`; `Дивиденды | none_required:not_applicable | ATOM-016`; `TC-AF-PFG-016 | none_required:extracted | Используется вместе с суммами дополнительных доходов.
