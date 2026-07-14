# Prepared Source Evidence

- package_id: `questionnaire-upload-transfer-v6-r1`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v6-20260714/prepared-input/.questionnaire-upload-transfer-v6-r1.compiled-evidence.md`
- source_sha256: `b66f2b0ddf191d47e80b47bc9e9b347a1abfa9bde875c413164fdfbe44826b89`
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

- OBL-QUT-001: property=SRC-QUT-001.P01 | source=SRC-QUT-001`; `BSR 206 | required=same-as-atom | planned=TC-QUT-001 | status=covered
- atom: ATOM-001 | source=SRC-QUT-001.P01; BSR 206; SRC-QUT-001 | statement=Информационное поле отображается всегда. | coverage=covered

- plan: PLAN-QUT-001 | atoms=ATOM-001 | check=Открыть блок `Документы по заявке`. | expected=Информационное поле отображается. | planned=TC-QUT-001 | status=covered

- OBL-QUT-002: property=SRC-QUT-001.P02 | source=SRC-QUT-001`; `BSR 207 | required=Текст информационного поля нельзя изменить ручным вводом. | planned=TC-QUT-002 | status=covered
- atom: ATOM-002 | source=SRC-QUT-001.P02; BSR 207; SRC-QUT-001 | statement=Информационное поле не допускает ручного редактирования своего текста. | coverage=covered

- plan: PLAN-QUT-002 | atoms=ATOM-002 | check=Установить фокус на информационном поле и попытаться ввести `Тест`. | expected=Текст информационного поля не изменяется. | planned=TC-QUT-002 | status=covered

- OBL-QUT-003: property=SRC-QUT-002.P01 | source=SRC-QUT-002`; `BSR 208 | required=Поле добавления файла Анкета клиента отображается всегда. | planned=TC-QUT-003 | status=covered
- atom: ATOM-003 | source=SRC-QUT-002.P01; BSR 208; SRC-QUT-002 | statement=Поле добавления файла `Анкета клиента` отображается всегда. | coverage=covered

- plan: PLAN-QUT-003 | atoms=ATOM-003 | check=Открыть блок `Документы по заявке`. | expected=Поле добавления файла `Анкета клиента` отображается. | planned=TC-QUT-003 | status=covered

- OBL-QUT-004: property=SRC-QUT-002.P02 | source=SRC-QUT-002`; `BSR 209 | required=После выбора portable jpg через проводник файл добавлен. | planned=TC-QUT-004 | status=covered
- atom: ATOM-004 | source=SRC-QUT-002.P02; BSR 209; SRC-QUT-002 | statement=Документ можно добавить через открытие проводника по кнопке. | coverage=covered

- plan: PLAN-QUT-004 | atoms=ATOM-004; ATOM-005 | check=По кнопке открыть проводник и выбрать `FIXTURE-QUT-JPG`. | expected=Файл добавлен, отображается имя `questionnaire-valid.jpg`. | planned=TC-QUT-004 | status=covered

- OBL-QUT-005: property=SRC-QUT-002.P03 | source=SRC-QUT-002`; `BSR 211 | required=После добавления отображается точное имя выбранного файла. | planned=TC-QUT-004 | status=covered
- atom: ATOM-005 | source=SRC-QUT-002.P03; BSR 211; SRC-QUT-002 | statement=После добавления документа отображается имя прикреплённого файла. | coverage=covered

- OBL-QUT-006: property=SRC-QUT-002.P04 | source=SRC-QUT-002`; `BSR 209`; `BSR 211 | required=После Drag and Drop portable pdf файл добавлен и его имя отображается. | planned=TC-QUT-005 | status=covered
- atom: ATOM-006 | source=SRC-QUT-002.P04; BSR 209; SRC-QUT-002 | statement=Документ можно добавить через Drag and Drop. | coverage=covered

- plan: PLAN-QUT-005 | atoms=ATOM-006 | check=Перетащить `FIXTURE-QUT-PDF` в поле `Анкета клиента`. | expected=Файл добавлен, отображается имя `questionnaire-valid.pdf`. | planned=TC-QUT-005 | status=covered

- OBL-QUT-007: property=SRC-QUT-002.P05 | source=SRC-QUT-002`; `BSR 210 | required=В отдельных чистых итерациях jpg, png и pdf добавляются успешно. | planned=TC-QUT-006 | status=covered
- atom: ATOM-007 | source=SRC-QUT-002.P05; BSR 210; SRC-QUT-002 | statement=Поле принимает файлы форматов jpg, png и pdf. | coverage=covered

- plan: PLAN-QUT-006 | atoms=ATOM-007 | check=В трёх независимых чистых итерациях добавить через проводник `FIXTURE-QUT-JPG`, `FIXTURE-QUT-PNG`, `FIXTURE-QUT-PDF`. | expected=В каждой итерации выбранный файл добавляется. | planned=TC-QUT-006 | status=covered

- OBL-QUT-008: property=SRC-QUT-002.P06 | source=SRC-QUT-002`; `BSR 210 | required=Файл ровно 41 943 040 байт добавляется успешно. | planned=TC-QUT-007 | status=covered
- atom: ATOM-008 | source=SRC-QUT-002.P06; BSR 210; SRC-QUT-002 | statement=Файл размером ровно 40 МБ соответствует ограничению `не более 40 МБ`. | coverage=covered

- plan: PLAN-QUT-007 | atoms=ATOM-008 | check=Добавить через проводник `FIXTURE-QUT-PDF-40MB`. | expected=Файл размером ровно 41 943 040 байт добавляется. | planned=TC-QUT-007 | status=covered

- OBL-QUT-009: property=SRC-QUT-002.P07 | source=SRC-QUT-002`; `BSR 210 | required=Файл 41 943 041 байт не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`. | planned=TC-QUT-008 | status=covered
- atom: ATOM-009 | source=SRC-QUT-002.P07; BSR 210; SRC-QUT-002 | statement=Файл больше 40 МБ не загружается, отображается точный текст ошибки из ФТ. | coverage=covered

- plan: PLAN-QUT-008 | atoms=ATOM-009 | check=Добавить через проводник `FIXTURE-QUT-PDF-OVER40`. | expected=Файл не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`. | planned=TC-QUT-008 | status=covered

- OBL-QUT-010: property=SRC-QUT-002.P08 | source=SRC-QUT-002`; `BSR 210 | required=Файл txt не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`. | planned=TC-QUT-009 | status=covered
- atom: ATOM-010 | source=SRC-QUT-002.P08; BSR 210; SRC-QUT-002 | statement=Файл недопустимого формата не загружается, отображается точный текст ошибки из ФТ. | coverage=covered

- plan: PLAN-QUT-009 | atoms=ATOM-010 | check=Добавить через проводник `FIXTURE-QUT-TXT`. | expected=Файл не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`. | planned=TC-QUT-009 | status=covered

- OBL-QUT-011: property=SRC-QUT-002.P09 | source=SRC-QUT-002`; `BSR 210 | required=После попытки добавить второй файл отображается не более одного имени файла этого типа. | planned=TC-QUT-010 | status=covered
- atom: ATOM-011 | source=SRC-QUT-002.P09; BSR 210; SRC-QUT-002 | statement=После попытки добавить второй файл в типе документа остаётся не более одного файла. | coverage=covered

- plan: PLAN-QUT-010 | atoms=ATOM-011 | check=Добавить `FIXTURE-QUT-PDF-A`, затем через тот же picker попытаться добавить `FIXTURE-QUT-PDF-B`. | expected=После второго действия в поле отображается не более одного имени файла; способ replace/reject и сообщение не утверждаются. | planned=TC-QUT-010 | status=covered
