# Prepared Source Evidence

- package_id: `autofin-print-form-compiled-v3`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-print-form-compiler-v3-20260711/prepared-input/.autofin-print-form-compiled-v3.compiled-evidence.md`
- source_sha256: `71f1ee39b2de1361406772f8c9dcb624bfed222cc521eb274bd357aface731bc`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## ATOM-001

ATOM-001 | WP-01 | 4.4 paragraph; PDF p.36 | Система автоматически формирует печатную форму `Заявление-анкета на получение потребительского кредита` на основании данных о Клиенте из Системы. | TC-AF-PFG-001 | covered | GAP-003

- plan: PD-PFG-001 | WP-01 | generated-document | 4.4 paragraph; PDF p.36; GAP-001; GAP-003 | ATOM-001`; `ATOM-002 | Сформировать заявление-анкету и проверить используемый шаблон | positive | print-form-generated | FIX-PFG-BASE | PDF заявления-анкеты сформирован по шаблону `Анкета клиента 04.02.2026.pdf` | FT`; `PDF`; `GAP-001`; `GAP-003 | TC-AF-PFG-001 | covered

## ATOM-002

ATOM-002 | WP-01 | 4.4 document table; PDF p.36 | Для печатной формы используется шаблон `Анкета клиента 04.02.2026.pdf`. | TC-AF-PFG-001 | covered | GAP-001

- plan: PD-PFG-001 | WP-01 | generated-document | 4.4 paragraph; PDF p.36; GAP-001; GAP-003 | ATOM-001`; `ATOM-002 | Сформировать заявление-анкету и проверить используемый шаблон | positive | print-form-generated | FIX-PFG-BASE | PDF заявления-анкеты сформирован по шаблону `Анкета клиента 04.02.2026.pdf` | FT`; `PDF`; `GAP-001`; `GAP-003 | TC-AF-PFG-001 | covered

## ATOM-003

ATOM-003 | WP-01 | 4.4 paragraph before tag table | Шаблон привязан к типу, собранному на основе тегов из таблицы раздела `4.4`. | GAP-006 | gap | -

- plan: PD-PFG-003 | WP-01 | configuration | 4.4 paragraph before tag table | ATOM-003 | Проверить конфигурационную привязку шаблона к типу тегов | gap | missing configuration artifact | not_available | Проверяемый UI/API/файл настройки не указан в ФТ | GAP-006 | GAP-006 | gap

## ATOM-004

ATOM-004 | WP-01 | 4.4 paragraph before tag table | Теги в шаблоне называются так же, как в колонке `Тег`. | TC-AF-PFG-002 | covered | GAP-002

- plan: PD-PFG-002 | WP-01 | generated-document-mapping | 4.4 paragraph before tag table; GAP-002 | ATOM-004 | Проверить отсутствие незаполненных и неизвестных плейсхолдеров после генерации | negative | placeholder-residue | DICT-001 | В PDF нет остаточных тегов формата `<...>` | FT`; `DICT-001`; `GAP-002 | TC-AF-PFG-002 | covered

## ATOM-005

ATOM-005 | WP-02 | 4.4 tag rows 1-4 | Теги блока `Параметры о кредите` заполняются данными автомобиля и кредита. | TC-AF-PFG-003 | covered | GAP-005

- plan: PD-PFG-004 | WP-02 | generated-document-mapping | 4.4 tag rows 1-4; GAP-005 | ATOM-005 | Проверить заполнение параметров кредита и автомобиля | positive | direct tag mapping | FIX-PFG-BASE | Значения блока параметров кредита соответствуют заявке | FT`; `GAP-005 | TC-AF-PFG-003 | covered

## ATOM-006

ATOM-006 | WP-02 | 4.4 tag rows 5-19 | Теги персональных, паспортных данных и прежних ФИО заполняются согласно описанию строк таблицы. | TC-AF-PFG-004 | covered | -

- plan: PD-PFG-005 | WP-02 | generated-document-mapping | 4.4 tag rows 5-19 | ATOM-006 | Проверить заполнение персональных, паспортных данных и прежних ФИО | positive | direct tag mapping | FIX-PFG-FIO-CHANGED | Персональные и паспортные теги заполнены значениями заявки | FT | TC-AF-PFG-004 | covered

## ATOM-007

ATOM-007 | WP-02 | 4.4 tag row 18 | Чек-бокс `Зарегистрированный брак` зависит от значения `Семейное положение`. | TC-AF-PFG-005 | covered | -

- plan: PD-PFG-006 | WP-02 | decision-table | 4.4 tag row 18 | ATOM-007 | Проверить ветки чек-бокса зарегистрированного брака | positive | condition branches | FIX-PFG-MARRIAGE-YES`; `FIX-PFG-MARRIAGE-NO`; `DICT-002 | Для каждой ветки выставлен только ожидаемый чек-бокс | FT`; `DICT-002 | TC-AF-PFG-005 | covered

## ATOM-008

ATOM-008 | WP-02 | 4.4 tag row 20 | Чек-бокс социального статуса выставляется для выбранного значения социального статуса. | TC-AF-PFG-006 | covered | -

- plan: PD-PFG-007 | WP-02 | checkbox-list | 4.4 tag row 20 | ATOM-008 | Проверить чек-боксы социального статуса по значениям справочника | positive | active dictionary values | FIX-PFG-SOCIAL-STATUS`; `DICT-003 | Для выбранного социального статуса выставлен только соответствующий чек-бокс | FT`; `DICT-003 | TC-AF-PFG-006 | covered

## ATOM-009

ATOM-009 | WP-02 | 4.4 tag rows 21-29 | Блок фактического адреса заполняется адресными тегами и чек-боксом совпадения с адресом регистрации. | TC-AF-PFG-007`; `TC-AF-PFG-008 | covered | -

- plan: PD-PFG-008A | WP-02 | dependency | 4.4 tag rows 21-29 | ATOM-009 | Проверить ветку совпадения фактического адреса с адресом регистрации | dependency | condition=true | FIX-PFG-ADDR-SAME | Адресные теги и чек-бокс соответствуют совпадающим адресам | FT | TC-AF-PFG-007 | covered

- plan: PD-PFG-008B | WP-02 | dependency | 4.4 tag rows 21-29 | ATOM-009 | Проверить ветку отличия фактического адреса от адреса регистрации | dependency | condition=false | FIX-PFG-ADDR-DIFFERENT | Адресные теги и чек-бокс соответствуют различающимся адресам | FT | TC-AF-PFG-008 | covered

## ATOM-010

ATOM-010 | WP-02 | 4.4 tag rows 30-31, 33 | Контактные теги мобильного телефона, email и домашнего телефона заполняются данными заявки. | TC-AF-PFG-009 | covered | -

- plan: PD-PFG-009A | WP-02 | generated-document-mapping | 4.4 tag rows 30-31, 33 | ATOM-010 | Проверить прямой маппинг мобильного телефона, email и домашнего телефона | positive | direct tag mapping | FIX-PFG-BASE | Контактные теги заполнены значениями заявки | FT | TC-AF-PFG-009 | covered

## ATOM-018

ATOM-018 | WP-02 | 4.4 tag row 32 | `<work_phone>` заполняется только если клиент не является неработающим пенсионером. | TC-AF-PFG-010`; `TC-AF-PFG-011 | covered | -

- plan: PD-PFG-009B | WP-02 | dependency | 4.4 tag row 32 | ATOM-018 | Проверить вывод рабочего телефона для работающего клиента | dependency | condition=true | FIX-PFG-WORKING | `<work_phone>` заполнен рабочим телефоном из заявки | FT | TC-AF-PFG-010 | covered

- plan: PD-PFG-009C | WP-02 | dependency | 4.4 tag row 32 | ATOM-018 | Проверить отсутствие заполненного рабочего телефона для неработающего пенсионера | dependency | condition=false | FIX-PFG-NOT-WORKING-PENSIONER | `<work_phone>` не выводится как заполненное значение | FT | TC-AF-PFG-011 | covered

## ATOM-011

ATOM-011 | WP-02 | 4.4 tag rows 34-39 | Блок контактного лица заполняется ФИО, датой рождения, телефоном и чек-боксом отношения к заявителю. | TC-AF-PFG-012 | covered | -

- plan: PD-PFG-010 | WP-02 | checkbox-list | 4.4 tag rows 34-39 | ATOM-011 | Проверить чек-боксы отношения контактного лица к заявителю | positive | active dictionary values | FIX-PFG-RELATION`; `DICT-004 | Для выбранного отношения выставлен только соответствующий чек-бокс | FT`; `DICT-004 | TC-AF-PFG-012 | covered

## ATOM-012

ATOM-012 | WP-03 | 4.4 tag rows 40-43 | Блок работодателя заполняет чек-бокс ОПФ, наименование и ИНН работодателя. | TC-AF-PFG-013 | covered | -

- plan: PD-PFG-011 | WP-03 | checkbox-list | 4.4 tag rows 40-43 | ATOM-012 | Проверить чек-боксы ОПФ и данные работодателя | positive | active dictionary values | FIX-PFG-OPF`; `DICT-005 | ОПФ, наименование и ИНН работодателя отражены в PDF | FT`; `DICT-005 | TC-AF-PFG-013 | covered

## ATOM-013

ATOM-013 | WP-03 | 4.4 tag rows 44-51 | Адрес местонахождения работодателя заполняется тегами адреса работы. | TC-AF-PFG-014 | covered | -

- plan: PD-PFG-012 | WP-03 | generated-document-mapping | 4.4 tag rows 44-51 | ATOM-013 | Проверить заполнение адреса местонахождения работодателя | positive | direct tag mapping | FIX-PFG-BASE | Адресные теги работодателя заполнены значениями заявки | FT | TC-AF-PFG-014 | covered

## ATOM-014

ATOM-014 | WP-03 | 4.4 tag rows 52-54, 56 | Должность, дата начала работы, основной доход и общий доход выводятся по правилам таблицы. | TC-AF-PFG-015 | covered | -

- plan: PD-PFG-013 | WP-03 | generated-document-mapping | 4.4 tag rows 52-54, 56 | ATOM-014 | Проверить должность, дату начала работы, основной и общий доход | positive | direct and calculated income mapping | FIX-PFG-INCOME-ALL | Должность, дата начала работы, основной и общий доход заполнены по правилам таблицы | FT | TC-AF-PFG-015 | covered

## ATOM-015

ATOM-015 | WP-03 | 4.4 tag row 55 | `<job_start>` выводит начало общего трудового стажа по расчету через справочник `Стаж работы`. | GAP-004 | gap | -

- plan: PD-PFG-014 | WP-03 | calculation | 4.4 tag row 55 | ATOM-015 | Проверить расчет `<job_start>` через справочник `Стаж работы` | gap | missing dictionary/calculation oracle | DICT-007 | Справочник и расчетный oracle не раскрыты в ФТ | GAP-004 | GAP-004 | gap

## ATOM-016

ATOM-016 | WP-03 | 4.4 tag rows 57-60 | Чек-боксы и суммы других регулярных доходов зависят от типов дополнительных доходов. | TC-AF-PFG-016 | covered | -

- plan: PD-PFG-015 | WP-03 | checkbox-list | 4.4 tag rows 57-60 | ATOM-016 | Проверить чек-боксы и суммы дополнительных доходов | positive | active dictionary values | FIX-PFG-ADDITIONAL-INCOME-TYPE`; `DICT-006 | Для типа дохода выставлен соответствующий чек-бокс и сумма | FT`; `DICT-006 | TC-AF-PFG-016 | covered

## ATOM-017

ATOM-017 | WP-04 | 4.4 tag rows 61-87 | Блок согласий заполняет адрес регистрации по правилу tag1/tag2, код подразделения действующего паспорта и данные ранее выданных паспортов 1-5. | TC-AF-PFG-017`; `TC-AF-PFG-018 | covered | -

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
