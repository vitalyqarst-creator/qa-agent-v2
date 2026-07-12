# Prepared Source Evidence

- package_id: `personal-data-static-properties-v3`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/personal-data-static-properties-shadow-v3-20260712/prepared-input/.personal-data-static-properties-v3.compiled-evidence.md`
- source_sha256: `8184dc899939315946cdd636239fbc14c14596632a0fb257ae828e986e9abec9`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## Mandatory package context

source_path: fts/AutoFin/AGENT-NOTES.md

# Package Notes: AutoFin

## Сокращения В Таблицах UI-Полей

Статус: package-specific рабочее правило для AutoFin, добавленное по подтверждению пользователя и сверенное с аналогичными заметками в `fts/ft-2-OF_16/AGENT-NOTES.md`, `fts/ft-2-OF_17/AGENT-NOTES.md`, `fts/ft-2-OF_18/AGENT-NOTES.md`.

В таблицах описания свойств полей формы столбец `О` означает `Обязательность`, а столбец `Р` означает `Редактируемость`.

## Внешний Контекст: DaData На Интерфейсе

Источник и статус:

- Эта секция перенесена как справочный контекст из package notes `ft-2-OF_16`, `ft-2-OF_17`, `ft-2-OF_18`.
- В исходных заметках секция основана на публичной документации DaData, просмотренной `2026-06-03`.
- Это не источник новых требований ФТ и не замена основного ФТ/support-файлов AutoFin.
- Использовать только как справочный контекст для формулировки ручных UI-шагов и рисков, когда само ФТ AutoFin уже говорит, что поле интегрировано с DaData.
- Не добавлять в тест-кейсы поведение, которого нет в ФТ, support-файлах или подтвержденных UI evidence.

Официальные источники:

- `https://dadata.ru/api/suggest/` - общий API подсказок: помогает человеку быстро вводить корректные данные в формах; поддерживает ФИО, адреса, "Кем выдан паспорт" и другие справочники.
- `https://dadata.ru/api/suggest/address/` - подсказки по адресам: пользователь вводит часть адреса, сервис возвращает варианты; выбор конкретного адреса в API моделируется запросом `count = 1` по ранее возвращенному `unrestricted_value`.
- `https://dadata.ru/api/suggest/name/` - подсказки по ФИО: подсказывает ФИО одной строкой или отдельно фамилию, имя, отчество; может исправлять раскладку и определять пол, но не гарантирует автоматическую обработку без участия человека.
- `https://dadata.ru/api/suggest/fms_unit/` - подсказки "Кем выдан паспорт": поиск работает по коду подразделения и названию, результат содержит значение для списка, код подразделения и название подразделения.
- `https://support.dadata.ru/knowledge-bases/4/articles/7767-chto-schitaetsya-zaprosom-v-podskazkah` - виджет подсказок может отправлять запрос на каждый вводимый символ; количество запросов зависит от типа поля.

Практическая модель для ручных UI-шагов:

- Пользователь начинает вводить значение в поле, связанное с DaData.
- Интерфейс показывает список подсказок, если интеграция доступна и по введенному тексту есть варианты.
- Пользователь выбирает одну подсказку из списка; после выбора поле или связанные поля могут заполниться значениями из выбранной подсказки.
- Для паспортного подразделения подсказка может искаться по коду подразделения или названию подразделения.
- Для адреса выбранная подсказка может использоваться как источник разложения адреса на компоненты, если такое разложение прямо задано ФТ.
- Для ФИО подсказка может использоваться как ввод одной строкой или по отдельным частям ФИО, если такая форма прямо задана ФТ.

Ограничения для тест-дизайна:

- Не считать внутренние API-запросы, сохранение `kladr`, `esiaUserId`, `CorrelationId`, persistence/model changes или RabbitMQ/API effects покрытыми через UI без наблюдаемого артефакта.
- Не придумывать минимальное количество символов для запуска подсказок, debounce, порядок сортировки, точный вид dropdown, тексты ошибок DaData, fallback при недоступности сервиса или правила retry, если это не описано в ФТ/support/evidence.
- Не использовать публичную документацию DaData как основание менять обязательность, редактируемость, видимость, allowed values или expected results полей ФТ.
- Если UI-прогон показывает конкретное поведение виджета DaData, фиксировать это отдельно в UI evidence / UI-AGENT-NOTES и отличать от требований ФТ.

## OBL-001

- obligation: OBL-001 | property=SRC-002.P01 | source=`BSR 47`; XHTML row 57 | required=same-as-atom | planned=TC-PDSP-001 | status=covered

- atom: ATOM-001 | source=`SRC-002.P01`; XHTML row 57; DOCX table 6 row 4; BSR 47 | statement=Поле `Фамилия` отображается всегда. | coverage=covered

- plan: PLAN-001 | check=Открыть карточку заявки и проверить видимость поля `Фамилия`. | expected=Поле `Фамилия` отображается. | planned=TC-PDSP-001 | status=covered

## OBL-002

- obligation: OBL-002 | property=SRC-002.P02 | source=XHTML row 57; DOCX table 6 row 4 | required=same-as-atom | planned=TC-PDSP-002 | status=covered

- atom: ATOM-002 | source=`SRC-002.P02`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P02 | statement=Поле `Фамилия` является обязательным. | coverage=covered

- plan: PLAN-002 | check=Проверить признак обязательности поля `Фамилия`. | expected=Поле `Фамилия` обозначено обязательным. | planned=TC-PDSP-002 | status=covered

## OBL-003

- obligation: OBL-003 | property=SRC-002.P03 | source=XHTML row 57; DOCX table 6 row 4 | required=same-as-atom | planned=TC-PDSP-003 | status=covered

- atom: ATOM-003 | source=`SRC-002.P03`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P03 | statement=Поле `Фамилия` доступно для редактирования. | coverage=covered

- plan: PLAN-003 | check=Ввести синтетическое допустимое текстовое значение `Тест` в поле `Фамилия`. | expected=Значение `Тест` отображается в поле `Фамилия`. | planned=TC-PDSP-003 | status=covered

## OBL-004

- obligation: OBL-004 | property=SRC-002.P04 | source=XHTML row 57; DOCX table 6 row 4 | required=Поле `Фамилия` является полем ввода текста. | planned=TC-PDSP-004 | status=covered

- atom: ATOM-004 | source=`SRC-002.P04`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P04 | statement=Поле `Фамилия` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-004 | check=Проверить тип элемента управления `Фамилия`. | expected=`Фамилия` доступна как поле ввода текста. | planned=TC-PDSP-004 | status=covered

## OBL-005

- obligation: OBL-005 | property=SRC-002.P05 | source=XHTML row 57; DOCX table 6 row 4 | required=Поле `Фамилия` принимает строковое значение. | planned=TC-PDSP-005 | status=covered

- atom: ATOM-005 | source=`SRC-002.P05`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P05 | statement=Тип значения поля `Фамилия` — строка. | coverage=covered

- plan: PLAN-005 | check=Ввести синтетическое строковое значение `Тест` в поле `Фамилия`. | expected=Значение `Тест` отображается в поле `Фамилия`. | planned=TC-PDSP-005 | status=covered

## OBL-006

- obligation: OBL-006 | property=SRC-003.P01 | source=`BSR 50`; XHTML row 58 | required=same-as-atom | planned=TC-PDSP-006 | status=covered

- atom: ATOM-006 | source=`SRC-003.P01`; XHTML row 58; DOCX table 6 row 5; BSR 50 | statement=Поле `Имя` отображается всегда. | coverage=covered

- plan: PLAN-006 | check=Открыть карточку заявки и проверить видимость поля `Имя`. | expected=Поле `Имя` отображается. | planned=TC-PDSP-006 | status=covered

## OBL-007

- obligation: OBL-007 | property=SRC-003.P02 | source=XHTML row 58; DOCX table 6 row 5 | required=same-as-atom | planned=TC-PDSP-007 | status=covered

- atom: ATOM-007 | source=`SRC-003.P02`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P02 | statement=Поле `Имя` является обязательным. | coverage=covered

- plan: PLAN-007 | check=Проверить признак обязательности поля `Имя`. | expected=Поле `Имя` обозначено обязательным. | planned=TC-PDSP-007 | status=covered

## OBL-008

- obligation: OBL-008 | property=SRC-003.P03 | source=XHTML row 58; DOCX table 6 row 5 | required=same-as-atom | planned=TC-PDSP-008 | status=covered

- atom: ATOM-008 | source=`SRC-003.P03`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P03 | statement=Поле `Имя` доступно для редактирования. | coverage=covered

- plan: PLAN-008 | check=Ввести синтетическое допустимое текстовое значение `Тест` в поле `Имя`. | expected=Значение `Тест` отображается в поле `Имя`. | planned=TC-PDSP-008 | status=covered

## OBL-009

- obligation: OBL-009 | property=SRC-003.P04 | source=XHTML row 58; DOCX table 6 row 5 | required=Поле `Имя` является полем ввода текста. | planned=TC-PDSP-009 | status=covered

- atom: ATOM-009 | source=`SRC-003.P04`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P04 | statement=Поле `Имя` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-009 | check=Проверить тип элемента управления `Имя`. | expected=`Имя` доступно как поле ввода текста. | planned=TC-PDSP-009 | status=covered

## OBL-010

- obligation: OBL-010 | property=SRC-003.P05 | source=XHTML row 58; DOCX table 6 row 5 | required=Поле `Имя` принимает строковое значение. | planned=TC-PDSP-010 | status=covered

- atom: ATOM-010 | source=`SRC-003.P05`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P05 | statement=Тип значения поля `Имя` — строка. | coverage=covered

- plan: PLAN-010 | check=Ввести синтетическое строковое значение `Тест` в поле `Имя`. | expected=Значение `Тест` отображается в поле `Имя`. | planned=TC-PDSP-010 | status=covered

## OBL-011

- obligation: OBL-011 | property=SRC-004.P01 | source=`BSR 53`; XHTML row 59 | required=same-as-atom | planned=TC-PDSP-011 | status=covered

- atom: ATOM-011 | source=`SRC-004.P01`; XHTML row 59; DOCX table 6 row 6; BSR 53 | statement=Поле `Отчество` отображается всегда. | coverage=covered

- plan: PLAN-011 | check=Открыть карточку заявки и проверить видимость поля `Отчество`. | expected=Поле `Отчество` отображается. | planned=TC-PDSP-011 | status=covered

## OBL-012

- obligation: OBL-012 | property=SRC-004.P02 | source=XHTML row 59; DOCX table 6 row 6 | required=same-as-atom | planned=TC-PDSP-012 | status=covered

- atom: ATOM-012 | source=`SRC-004.P02`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P02 | statement=Поле `Отчество` не является обязательным. | coverage=covered

- plan: PLAN-012 | check=Проверить отсутствие признака обязательности поля `Отчество`. | expected=Поле `Отчество` не обозначено обязательным. | planned=TC-PDSP-012 | status=covered

## OBL-013

- obligation: OBL-013 | property=SRC-004.P03 | source=XHTML row 59; DOCX table 6 row 6 | required=same-as-atom | planned=TC-PDSP-013 | status=covered

- atom: ATOM-013 | source=`SRC-004.P03`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P03 | statement=Поле `Отчество` доступно для редактирования. | coverage=covered

- plan: PLAN-013 | check=Ввести синтетическое допустимое текстовое значение `Тест` в поле `Отчество`. | expected=Значение `Тест` отображается в поле `Отчество`. | planned=TC-PDSP-013 | status=covered

## OBL-014

- obligation: OBL-014 | property=SRC-004.P04 | source=XHTML row 59; DOCX table 6 row 6 | required=Поле `Отчество` является полем ввода текста. | planned=TC-PDSP-014 | status=covered

- atom: ATOM-014 | source=`SRC-004.P04`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P04 | statement=Поле `Отчество` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-014 | check=Проверить тип элемента управления `Отчество`. | expected=`Отчество` доступно как поле ввода текста. | planned=TC-PDSP-014 | status=covered

## OBL-015

- obligation: OBL-015 | property=SRC-004.P05 | source=XHTML row 59; DOCX table 6 row 6 | required=Поле `Отчество` принимает строковое значение. | planned=TC-PDSP-015 | status=covered

- atom: ATOM-015 | source=`SRC-004.P05`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P05 | statement=Тип значения поля `Отчество` — строка. | coverage=covered

- plan: PLAN-015 | check=Ввести синтетическое строковое значение `Тест` в поле `Отчество`. | expected=Значение `Тест` отображается в поле `Отчество`. | planned=TC-PDSP-015 | status=covered
