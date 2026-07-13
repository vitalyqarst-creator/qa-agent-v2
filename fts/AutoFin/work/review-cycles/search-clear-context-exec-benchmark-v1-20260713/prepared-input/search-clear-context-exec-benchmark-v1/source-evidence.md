# Prepared Source Evidence

- package_id: `search-clear-context-exec-benchmark-v1`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v1-20260713/prepared-input/.search-clear-context-exec-benchmark-v1.compiled-evidence.md`
- source_sha256: `e4b5d656d71e578ea8c11d8184d839ef3da61bd24efe18f4f9219df1b5c4b6aa`
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

## Portable fixture contracts

- `FIX-SCCB-001`: environment has at least one available visible filter value that changes filter state.
- `FIX-SCCB-002`: results table contains at least one sortable header and one displayed row.
- `FIX-SCCB-003`: result set has at least two pages; otherwise `TC-SCCB-003` is not executable on that environment and must be reported as fixture-blocked, not reinterpreted.

- OBL-001: property=SRC-001.P01 | source=BSR 32; SRC-001; section 4.2; PDF page 8 | required=После нажатия `Очистить` изменённое состояние фильтров совпадает с зафиксированным initial state. | planned=TC-SCCB-001 | status=covered
- atom: ATOM-001 | source=BSR 32; SRC-001 | statement=Нажатие `Очистить` очищает применённые фильтры поиска. | coverage=covered

- plan: PD-001 | atoms=ATOM-001 | check=Capture initial filter state, choose one visible filter value, then click `Очистить`. | expected=Filter state equals the captured initial state. | planned=TC-SCCB-001 | status=covered

- OBL-002: property=SRC-001.P02 | source=BSR 32; SRC-001; section 4.2; PDF page 8 | required=После нажатия `Очистить` изменённое состояние сортировки совпадает с зафиксированным initial state. | planned=TC-SCCB-002 | status=covered
- atom: ATOM-002 | source=BSR 32; SRC-001 | statement=Нажатие `Очистить` очищает применённые сортировки. | coverage=covered

- plan: PD-002 | atoms=ATOM-002 | check=Capture initial sort state, click one sortable header until state changes, then click `Очистить`. | expected=Sort state equals the captured initial state. | planned=TC-SCCB-002 | status=covered

- OBL-003: property=SRC-001.P03 | source=BSR 32; SRC-001; section 4.2; PDF page 8 | required=После нажатия `Очистить` изменённое состояние постраничности совпадает с зафиксированным initial state. | planned=TC-SCCB-003 | status=covered
- atom: ATOM-003 | source=BSR 32; SRC-001 | statement=Нажатие `Очистить` очищает постраничность. | coverage=covered

- plan: PD-003 | atoms=ATOM-003 | check=Capture initial page, navigate to `page 2`, then click `Очистить`. | expected=Pagination state equals the captured initial state. | planned=TC-SCCB-003 | status=covered

- OBL-004: property=SRC-001.P04 | source=BSR 32; SRC-001; section 4.2; PDF page 8 | required=После нажатия `Очистить` состояние выделения строк совпадает с зафиксированным initial state. | planned=TC-SCCB-004 | status=covered
- atom: ATOM-004 | source=BSR 32; SRC-001 | statement=Нажатие `Очистить` очищает состояние выделения строк. | coverage=covered

- plan: PD-004 | atoms=ATOM-004 | check=Capture initial row-selection state, select the `first displayed row`, then click `Очистить`. | expected=Row-selection state equals the captured initial state. | planned=TC-SCCB-004 | status=covered
