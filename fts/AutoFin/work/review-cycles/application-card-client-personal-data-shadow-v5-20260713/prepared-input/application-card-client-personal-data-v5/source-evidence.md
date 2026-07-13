# Prepared Source Evidence

- package_id: `application-card-client-personal-data-v5`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v5-20260713/prepared-input/.application-card-client-personal-data-v5.compiled-evidence.md`
- source_sha256: `3c1de8c41be6ae1f3dc78288c8e004c4d1e3246a921a018f44760d024f98e11d`
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

- `FIX-ACPD-PORTABLE-SAVE-001`: открыть новую карточку действием создания заявки из BSR 38; заполнить in-scope поля синтетическими значениями `Фамилия=Иванов`, `Имя=Иван`, `Пол=Мужчина`, `Дата рождения=D-30y`, `Клиент менял ФИО=Нет`, кроме поля — цели конкретного кейса. Поля вне выбранного scope связываются с source-backed данными соответствующих scope при UI-prep. Существующий ID заявки, локатор и заранее сохранённая запись не требуются для FT-first draft.
- `FIX-ACPD-RUNTIME-DADATA-001`: ввести синтетический префикс `Иван`, выбрать из фактически возвращённых подсказок вариант с доступными составными частями ФИО и известным непустым полом; до выбора записать исходный `Пол`, после выбора сравнить видимый `Пол` со значением выбранной подсказки. Конкретный текст и порядок динамических подсказок заранее не фиксируются.

- OBL-001: property=SRC-001.P01 | source=SRC-001 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-001 | source=no_requirement_code:SRC-001 | statement=Блок `Персональные данные` отображается в карточке заявки. | coverage=covered

- plan: PLAN-001 | atoms=ATOM-001`; `ATOM-002`; `ATOM-007`; `ATOM-012 | check=Открыть карточку заявки и проверить блок и три поля. | expected=Блок и поля `Фамилия`, `Имя`, `Отчество` отображаются. | planned=TC-ACPD-001 | status=covered

- OBL-002: property=SRC-002.P01 | source=SRC-002`; `BSR 47 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-002 | source=BSR 47 | statement=Поле `Фамилия` отображается всегда. | coverage=covered

- OBL-003: property=SRC-002.P02 | source=SRC-002 | required=Evidence содержит control/action/empty `Фамилия`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-022 | status=covered
- atom: ATOM-003 | source=column О=Да | statement=Поле `Фамилия` является обязательным. | coverage=covered

- plan: PLAN-022 | atoms=ATOM-003 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Фамилия` пустой, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустая `Фамилия`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-022 | status=covered

- OBL-004: property=SRC-002.P03 | source=SRC-002 | required=Поле `Фамилия` доступно для редактирования. | planned=TC-ACPD-002 | status=covered
- atom: ATOM-004 | source=column Р=Да | statement=Поле `Фамилия` редактируемо. | coverage=covered

- plan: PLAN-002 | atoms=ATOM-004`; `ATOM-009`; `ATOM-014 | check=Указать валидные значения в три ФИО-поля. | expected=Каждое из трёх полей принимает ввод. | planned=TC-ACPD-002 | status=covered

- OBL-005: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Поле `Фамилия` допускает текстовые символы и символ `-`. | planned=TC-ACPD-003 | status=covered
- atom: ATOM-005 | source=BSR 48 | statement=В поле `Фамилия` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-003 | atoms=ATOM-005 | check=Ввести `Иванов-Петров` в поле `Фамилия`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-003 | status=covered

- plan: PLAN-016 | atoms=ATOM-005 | check=Ввести `Иванов2` в поле `Фамилия`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-016 | status=covered

- plan: PLAN-017 | atoms=ATOM-005 | check=Ввести `Иванов@` в поле `Фамилия`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-017 | status=covered

- OBL-006: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Значение с цифрой не является допустимым для `Фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-016 | status=covered
- OBL-007: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Значение со спецсимволом кроме `-` не является допустимым для `Фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-017 | status=covered
- OBL-008: property=SRC-002.P05 | source=SRC-002`; `BSR 49 | required=Для `Фамилия` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-004 | status=covered
- atom: ATOM-006 | source=BSR 49 | statement=Для поля `Фамилия` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-004 | atoms=ATOM-006 | check=Начать ввод `Иван` в поле `Фамилия` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-004 | status=covered

- OBL-009: property=SRC-003.P01 | source=SRC-003`; `BSR 50 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-007 | source=BSR 50 | statement=Поле `Имя` отображается всегда. | coverage=covered

- OBL-010: property=SRC-003.P02 | source=SRC-003 | required=Evidence содержит control/action/empty `Имя`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-023 | status=covered
- atom: ATOM-008 | source=column О=Да | statement=Поле `Имя` является обязательным. | coverage=covered

- plan: PLAN-023 | atoms=ATOM-008 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Имя` пустым, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустое `Имя`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-023 | status=covered

- OBL-011: property=SRC-003.P03 | source=SRC-003 | required=Поле `Имя` доступно для редактирования. | planned=TC-ACPD-002 | status=covered
- atom: ATOM-009 | source=column Р=Да | statement=Поле `Имя` редактируемо. | coverage=covered

- OBL-012: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Поле `Имя` допускает текстовые символы и символ `-`. | planned=TC-ACPD-005 | status=covered
- atom: ATOM-010 | source=BSR 51 | statement=В поле `Имя` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-005 | atoms=ATOM-010 | check=Ввести `Анна-Мария` в поле `Имя`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-005 | status=covered

- plan: PLAN-018 | atoms=ATOM-010 | check=Ввести `Иван2` в поле `Имя`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-018 | status=covered

- plan: PLAN-019 | atoms=ATOM-010 | check=Ввести `Иван@` в поле `Имя`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-019 | status=covered

- OBL-013: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Значение с цифрой не является допустимым для `Имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-018 | status=covered
- OBL-014: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Значение со спецсимволом кроме `-` не является допустимым для `Имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-019 | status=covered
- OBL-015: property=SRC-003.P05 | source=SRC-003`; `BSR 52 | required=Для `Имя` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-006 | status=covered
- atom: ATOM-011 | source=BSR 52 | statement=Для поля `Имя` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-006 | atoms=ATOM-011 | check=Начать ввод `Анна` в поле `Имя` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-006 | status=covered

- OBL-016: property=SRC-004.P01 | source=SRC-004`; `BSR 53 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-012 | source=BSR 53 | statement=Поле `Отчество` отображается всегда. | coverage=covered

- OBL-017: property=SRC-004.P02 | source=SRC-004 | required=Save завершён; после повторного открытия `Отчество` пусто и не блокировало сохранение. | planned=TC-ACPD-047 | status=covered
- atom: ATOM-013 | source=column О=Нет | statement=Поле `Отчество` не является обязательным. | coverage=covered

- plan: PLAN-047 | atoms=ATOM-013 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Отчество` пустым, инициировать сохранение и открыть сохранённую заявку повторно. | expected=Сохранение завершено; после повторного открытия `Отчество` пусто и не блокировало сохранение. | planned=TC-ACPD-047 | status=covered

- OBL-018: property=SRC-004.P03 | source=SRC-004 | required=Поле `Отчество` доступно для редактирования. | planned=TC-ACPD-002 | status=covered
- atom: ATOM-014 | source=column Р=Да | statement=Поле `Отчество` редактируемо. | coverage=covered

- OBL-019: property=SRC-004.P04 | source=SRC-004`; `BSR 54 | required=Поле `Отчество` допускает текстовые символы и символ `-`. | planned=TC-ACPD-007 | status=covered
- atom: ATOM-015 | source=BSR 54 | statement=В поле `Отчество` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-007 | atoms=ATOM-015 | check=Ввести `Иванович-Петрович` в поле `Отчество`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-007 | status=covered

- plan: PLAN-020 | atoms=ATOM-015 | check=Ввести `Иванович2` в поле `Отчество`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-020 | status=covered

- plan: PLAN-021 | atoms=ATOM-015 | check=Ввести `Иванович@` в поле `Отчество`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-021 | status=covered

- OBL-020: property=SRC-004.P04 | source=SRC-004`; `BSR 54 | required=Значение с цифрой не является допустимым для `Отчество`; механизм UI-отклонения не задан. | planned=TC-ACPD-020 | status=covered
- OBL-021: property=SRC-004.P04 | source=SRC-004`; `BSR 54 | required=Значение со спецсимволом кроме `-` не является допустимым для `Отчество`; механизм UI-отклонения не задан. | planned=TC-ACPD-021 | status=covered
- OBL-022: property=SRC-004.P05 | source=SRC-004`; `BSR 55 | required=Для `Отчество` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-008 | status=covered
- atom: ATOM-016 | source=BSR 55 | statement=Для поля `Отчество` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-008 | atoms=ATOM-016 | check=Начать ввод `Иванович` в поле `Отчество` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-008 | status=covered

- OBL-023: property=SRC-005.P01 | source=SRC-005`; `BSR 56 | required=`ID клиента` отображается всегда и недоступен для ручного редактирования. | planned=TC-ACPD-009 | status=covered
- atom: ATOM-017 | source=BSR 56; column Р=Нет | statement=Поле `ID клиента` отображается всегда и недоступно для ручного редактирования. | coverage=covered

- plan: PLAN-009 | atoms=ATOM-017 | check=Открыть карточку заявки и попытаться изменить `ID клиента`. | expected=`ID клиента` отображается и недоступен для ручного редактирования. | planned=TC-ACPD-009 | status=covered

- OBL-024: property=SRC-005.P02 | source=SRC-005`; `BSR 57 | required=После save видимый `ID клиента` изменился с пустого на непустой; значение записано, ABS-атрибуция не утверждается. | planned=TC-ACPD-010 | status=covered
- atom: ATOM-018 | source=BSR 57 | statement=Поле `ID клиента` заполняется автоматически системой ID клиента из АБС после сохранения заявки. | coverage=covered

- plan: PLAN-010 | atoms=ATOM-018 | check=По `FIX-ACPD-PORTABLE-SAVE-001` записать пустой `ID клиента`, инициировать сохранение заявки и записать новое видимое значение. | expected=После успешного сохранения видимый `ID клиента` изменился с пустого на непустой; ABS-атрибуция не утверждается. | planned=TC-ACPD-010 | status=covered

- OBL-025: property=SRC-006.P01 | source=SRC-006`; `BSR 58`; `DICT-001 | required=Поле `Пол` отображается, редактируемо и использует активные значения `DICT-001`. | planned=TC-ACPD-011 | status=covered
- atom: ATOM-019 | source=BSR 58; column О=Да; DICT-001 | statement=Поле `Пол` отображается всегда, обязательно, редактируемо и использует справочник `Пол клиента`. | coverage=covered

- plan: PLAN-011 | atoms=ATOM-019 | check=Открыть переключатель `Пол`. | expected=Поле показывает полный активный перечень `Мужчина`, `Женщина` и доступно для выбора. | planned=TC-ACPD-011 | status=covered

- plan: PLAN-024 | atoms=ATOM-019 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Пол` пустым, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустой `Пол`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-024 | status=covered

- OBL-026: property=SRC-006.P01 | source=SRC-006`; `DICT-001 | required=Evidence содержит control/action/empty `Пол`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-024 | status=covered
- OBL-027: property=SRC-006.P02 | source=SRC-006`; `BSR 59 | required=Видимый `Пол` совпал с expected fixture; до/после записаны, provider-attribution не утверждается. | planned=TC-ACPD-012 | status=covered
- atom: ATOM-020 | source=BSR 59 | statement=Поле `Пол` должно обновляться данными DaData после заполнения ФИО через подсказку DaData. | coverage=covered

- plan: PLAN-012 | atoms=ATOM-020 | check=По `FIX-ACPD-RUNTIME-DADATA-001` записать исходный `Пол`, ввести `Иван`, выбрать фактически возвращённую подсказку с известным полом и сравнить итоговый `Пол` со значением выбранной подсказки. | expected=После выбора подсказки видимый `Пол` совпадает с полом выбранной подсказки; до/после записаны, provider-attribution не утверждается. | planned=TC-ACPD-012 | status=covered

- OBL-028: property=SRC-007.P01 | source=SRC-007`; `BSR 60 | required=Поле видимо, редактируемо и отображает введённую логическую дату `D-30 лет`; формат/виджет не утверждаются. | planned=TC-ACPD-013 | status=covered
- atom: ATOM-021 | source=BSR 60; column О=Да | statement=Поле `Дата рождения` отображается всегда, обязательно, редактируемо и имеет тип `Дата`. | coverage=covered

- plan: PLAN-013 | atoms=ATOM-021 | check=Ввести вычисленную дату `D-30 лет`, прочитать отображённое логическое значение. | expected=Поле видимо, редактируемо и отображает ту же логическую дату; формат/виджет не утверждаются. | planned=TC-ACPD-013 | status=covered

- plan: PLAN-025 | atoms=ATOM-021 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Дата рождения` пустой, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустая `Дата рождения`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-025 | status=covered

- OBL-029: property=SRC-007.P01 | source=SRC-007`; `BSR 60 | required=Evidence содержит control/action/empty `Дата рождения`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-025 | status=covered
- OBL-030: property=SRC-007.P02 | source=SRC-007`; `BSR 61 | required=Дата `D-18 лет` соответствует верхней возрастной границе. | planned=TC-ACPD-014 | status=covered
- atom: ATOM-022 | source=BSR 61 | statement=Дата рождения не может быть позже чем `D-18 лет`. | coverage=covered

- plan: PLAN-014 | atoms=ATOM-022`; `ATOM-025 | check=Ввести дату `D-18 лет`. | expected=Дата на границе `D-18 лет` соответствует ограничению, вычисляемому от D. | planned=TC-ACPD-014 | status=covered

- plan: PLAN-026 | atoms=ATOM-022`; `ATOM-025 | check=Ввести дату `D-18 лет + 1 день`. | expected=Значение не соответствует границе D-18 лет; точная UI-реакция калибруется. | planned=TC-ACPD-026 | status=covered

- OBL-031: property=SRC-007.P02 | source=SRC-007`; `BSR 61 | required=Дата позже `D-18 лет` не соответствует ограничению; точная UI-реакция не определена. | planned=TC-ACPD-026 | status=covered
- OBL-032: property=SRC-007.P03 | source=SRC-007`; `BSR 62 | required=Дата больше текущей даты `D` не соответствует ограничению; точная UI-реакция не определена. | planned=TC-ACPD-027 | status=covered
- atom: ATOM-023 | source=BSR 62 | statement=Дата рождения не может быть больше текущей даты `D`. | coverage=covered

- plan: PLAN-027 | atoms=ATOM-023`; `ATOM-025 | check=Ввести дату `D+1 день`. | expected=Значение больше D не соответствует ограничению; точная UI-реакция калибруется. | planned=TC-ACPD-027 | status=covered

- OBL-033: property=SRC-007.P04 | source=SRC-007`; `BSR 63 | required=Дата `D-100 лет` соответствует нижней возрастной границе. | planned=TC-ACPD-015 | status=covered
- atom: ATOM-024 | source=BSR 63 | statement=Дата рождения не может быть меньше чем `D-100 лет`. | coverage=covered

- plan: PLAN-015 | atoms=ATOM-024`; `ATOM-025 | check=Ввести дату `D-100 лет`. | expected=Дата на границе `D-100 лет` соответствует ограничению, вычисляемому от D. | planned=TC-ACPD-015 | status=covered

- plan: PLAN-028 | atoms=ATOM-024`; `ATOM-025 | check=Ввести дату `D-100 лет - 1 день`. | expected=Значение раньше D-100 лет не соответствует ограничению; точная UI-реакция калибруется. | planned=TC-ACPD-028 | status=covered

- OBL-034: property=SRC-007.P04 | source=SRC-007`; `BSR 63 | required=Дата раньше `D-100 лет` не соответствует ограничению; точная UI-реакция не определена. | planned=TC-ACPD-028 | status=covered
- OBL-035: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Граница `D-18 лет` вычисляется относительно текущей даты приложения `D`. | planned=TC-ACPD-014 | status=covered
- atom: ATOM-025 | source=BSR 61-63 | statement=Границы даты рождения проверяются относительно текущей даты приложения `D`. | coverage=covered

- OBL-036: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Граница `D-100 лет` вычисляется относительно текущей даты приложения `D`. | planned=TC-ACPD-015 | status=covered
- OBL-037: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Проверка значения позже `D-18 лет` использует текущую дату приложения `D`. | planned=TC-ACPD-026 | status=covered
- OBL-038: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Проверка значения больше `D` использует текущую дату приложения `D`. | planned=TC-ACPD-027 | status=covered
- OBL-039: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Проверка значения раньше `D-100 лет` использует текущую дату приложения `D`. | planned=TC-ACPD-028 | status=covered
- OBL-040: property=SRC-008.P01 | source=SRC-008`; `BSR 64 | required=`Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`. | planned=TC-ACPD-029 | status=covered
- atom: ATOM-026 | source=BSR 64 | statement=Поле `Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`. | coverage=covered

- plan: PLAN-029 | atoms=ATOM-026 | check=Открыть переключатель `Клиент менял ФИО`. | expected=Переключатель отображается с вариантами `Да` и `Нет`. | planned=TC-ACPD-029 | status=covered

- OBL-041: property=SRC-008.P02 | source=SRC-008`; `BSR 65 | required=Значение по умолчанию `Клиент менял ФИО` равно `Нет`. | planned=TC-ACPD-030 | status=covered
- atom: ATOM-027 | source=BSR 65 | statement=Значение по умолчанию для `Клиент менял ФИО` равно `Нет`. | coverage=covered

- plan: PLAN-030 | atoms=ATOM-027 | check=Открыть новую карточку заявки. | expected=Значение `Клиент менял ФИО` по умолчанию равно `Нет`. | planned=TC-ACPD-030 | status=covered

- OBL-042: property=SRC-009.P01 | source=SRC-009`; `BSR 66 | required=`Предыдущая фамилия` отображается при `Клиент менял ФИО=Да`. | planned=TC-ACPD-031 | status=covered
- atom: ATOM-028 | source=BSR 66 | statement=Поле `Предыдущая фамилия` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`. | coverage=covered

- plan: PLAN-031 | atoms=ATOM-028`; `ATOM-033`; `ATOM-038 | check=Установить `Клиент менял ФИО=Да`. | expected=Три поля предыдущей ФИО отображаются. | planned=TC-ACPD-031 | status=covered

- plan: PLAN-032 | atoms=ATOM-028`; `ATOM-033`; `ATOM-038 | check=Установить `Клиент менял ФИО=Нет`. | expected=Три поля предыдущей ФИО не отображаются. | planned=TC-ACPD-032 | status=covered

- OBL-043: property=SRC-009.P01 | source=SRC-009`; `BSR 66 | required=`Предыдущая фамилия` не отображается при `Клиент менял ФИО=Нет`. | planned=TC-ACPD-032 | status=covered
- OBL-044: property=SRC-009.P02 | source=SRC-009 | required=`Предыдущая фамилия` редактируема при выполнении условия видимости. | planned=TC-ACPD-033 | status=covered
- atom: ATOM-029 | source=column Р=Да | statement=Поле `Предыдущая фамилия` редактируемо при выполнении условия видимости. | coverage=covered

- plan: PLAN-033 | atoms=ATOM-029`; `ATOM-034`; `ATOM-039 | check=При `Клиент менял ФИО=Да` указать валидные значения в три предыдущих ФИО-поля. | expected=Все три отображённые поля доступны для редактирования. | planned=TC-ACPD-033 | status=covered

- OBL-045: property=SRC-009.P03 | source=SRC-009`; `BSR 67 | required=`Предыдущая фамилия` допускает текстовые символы и символ `-`. | planned=TC-ACPD-034 | status=covered
- atom: ATOM-030 | source=BSR 67 | statement=В поле `Предыдущая фамилия` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-034 | atoms=ATOM-030 | check=Ввести `Петрова-Сидорова` в поле `Предыдущая фамилия`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-034 | status=covered

- plan: PLAN-035 | atoms=ATOM-030 | check=Ввести `Петрова2` в поле `Предыдущая фамилия`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-035 | status=covered

- plan: PLAN-036 | atoms=ATOM-030 | check=Ввести `Петрова@` в поле `Предыдущая фамилия`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-036 | status=covered

- OBL-046: property=SRC-009.P03 | source=SRC-009`; `BSR 67 | required=Значение с цифрой не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-035 | status=covered
- OBL-047: property=SRC-009.P03 | source=SRC-009`; `BSR 67 | required=Значение со спецсимволом кроме `-` не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-036 | status=covered
- OBL-048: property=SRC-009.P04 | source=SRC-009`; `BSR 68 | required=Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-041 | status=covered
- atom: ATOM-031 | source=BSR 68 | statement=Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО. | coverage=covered

- plan: PLAN-041 | atoms=ATOM-031`; `ATOM-036`; `ATOM-041 | check=По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, условие, пустая группа, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-041 | status=covered

- OBL-049: property=SRC-009.P05 | source=SRC-009`; `BSR 69 | required=Для `Предыдущая фамилия` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-037 | status=covered
- atom: ATOM-032 | source=BSR 69 | statement=Для поля `Предыдущая фамилия` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-037 | atoms=ATOM-032 | check=Начать ввод `Петрова` в поле `Предыдущая фамилия` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-037 | status=covered

- OBL-050: property=SRC-010.P01 | source=SRC-010`; `BSR 70 | required=`Предыдущее имя` отображается при `Клиент менял ФИО=Да`. | planned=TC-ACPD-031 | status=covered
- atom: ATOM-033 | source=BSR 70 | statement=Поле `Предыдущее имя` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`. | coverage=covered

- OBL-051: property=SRC-010.P01 | source=SRC-010`; `BSR 70 | required=`Предыдущее имя` не отображается при `Клиент менял ФИО=Нет`. | planned=TC-ACPD-032 | status=covered
- OBL-052: property=SRC-010.P02 | source=SRC-010 | required=`Предыдущее имя` редактируемо при выполнении условия видимости. | planned=TC-ACPD-033 | status=covered
- atom: ATOM-034 | source=column Р=Да | statement=Поле `Предыдущее имя` редактируемо при выполнении условия видимости. | coverage=covered

- OBL-053: property=SRC-010.P03 | source=SRC-010`; `BSR 71 | required=`Предыдущее имя` допускает текстовые символы и символ `-`. | planned=TC-ACPD-038 | status=covered
- atom: ATOM-035 | source=BSR 71 | statement=В поле `Предыдущее имя` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-038 | atoms=ATOM-035 | check=Ввести `Анна-Мария` в поле `Предыдущее имя`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-038 | status=covered

- plan: PLAN-039 | atoms=ATOM-035 | check=Ввести `Анна2` в поле `Предыдущее имя`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-039 | status=covered

- plan: PLAN-040 | atoms=ATOM-035 | check=Ввести `Анна@` в поле `Предыдущее имя`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-040 | status=covered

- OBL-054: property=SRC-010.P03 | source=SRC-010`; `BSR 71 | required=Значение с цифрой не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-039 | status=covered
- OBL-055: property=SRC-010.P03 | source=SRC-010`; `BSR 71 | required=Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-040 | status=covered
- OBL-056: property=SRC-010.P04 | source=SRC-010`; `BSR 72 | required=Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-041 | status=covered
- atom: ATOM-036 | source=BSR 72 | statement=Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО. | coverage=covered

- OBL-057: property=SRC-010.P05 | source=SRC-010`; `BSR 73 | required=Для `Предыдущее имя` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-042 | status=covered
- atom: ATOM-037 | source=BSR 73 | statement=Для поля `Предыдущее имя` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-042 | atoms=ATOM-037 | check=Начать ввод `Анна` в поле `Предыдущее имя` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-042 | status=covered

- OBL-058: property=SRC-011.P01 | source=SRC-011`; `BSR 74 | required=`Предыдущее отчество` отображается при `Клиент менял ФИО=Да`. | planned=TC-ACPD-031 | status=covered
- atom: ATOM-038 | source=BSR 74 | statement=Поле `Предыдущее отчество` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`. | coverage=covered

- OBL-059: property=SRC-011.P01 | source=SRC-011`; `BSR 74 | required=`Предыдущее отчество` не отображается при `Клиент менял ФИО=Нет`. | planned=TC-ACPD-032 | status=covered
- OBL-060: property=SRC-011.P02 | source=SRC-011 | required=`Предыдущее отчество` редактируемо при выполнении условия видимости. | planned=TC-ACPD-033 | status=covered
- atom: ATOM-039 | source=column Р=Да | statement=Поле `Предыдущее отчество` редактируемо при выполнении условия видимости. | coverage=covered

- OBL-061: property=SRC-011.P03 | source=SRC-011`; `BSR 75 | required=`Предыдущее отчество` допускает текстовые символы и символ `-`. | planned=TC-ACPD-043 | status=covered
- atom: ATOM-040 | source=BSR 75 | statement=В поле `Предыдущее отчество` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-043 | atoms=ATOM-040 | check=Ввести `Ивановна-Петровна` в поле `Предыдущее отчество`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-043 | status=covered

- plan: PLAN-044 | atoms=ATOM-040 | check=Ввести `Ивановна2` в поле `Предыдущее отчество`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-044 | status=covered

- plan: PLAN-045 | atoms=ATOM-040 | check=Ввести `Ивановна@` в поле `Предыдущее отчество`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-045 | status=covered

- OBL-062: property=SRC-011.P03 | source=SRC-011`; `BSR 75 | required=Значение с цифрой не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан. | planned=TC-ACPD-044 | status=covered
- OBL-063: property=SRC-011.P03 | source=SRC-011`; `BSR 75 | required=Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан. | planned=TC-ACPD-045 | status=covered
- OBL-064: property=SRC-011.P04 | source=SRC-011`; `BSR 76 | required=Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-041 | status=covered
- atom: ATOM-041 | source=BSR 76 | statement=Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО. | coverage=covered

- OBL-065: property=SRC-011.P05 | source=SRC-011`; `BSR 77 | required=Для `Предыдущее отчество` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-046 | status=covered
- atom: ATOM-042 | source=BSR 77 | statement=Для поля `Предыдущее отчество` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-046 | atoms=ATOM-042 | check=Начать ввод `Ивановна` в поле `Предыдущее отчество` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-046 | status=covered

## GAP-001

source_refs: SRC-002..SRC-004; SRC-007; SRC-009..SRC-011; ATOM-005; ATOM-010; ATOM-015; ATOM-022; ATOM-023; ATOM-024; ATOM-025; ATOM-030; ATOM-035; ATOM-040
`BSR 48, 51, 54, 61–63, 67, 71, 75`; `SRC-002..SRC-004`; `SRC-007`; `SRC-009..SRC-011`.
Keep calibration candidates; do not invent a message, highlight, filtering, blocked save, or transition.

## GAP-002

source_refs: SRC-002; SRC-003; SRC-006; SRC-007; SRC-009..SRC-011; ATOM-003; ATOM-008; ATOM-019; ATOM-021; ATOM-031; ATOM-036; ATOM-041
Table 4 column `О`; `BSR 68, 72, 76`; `SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011`.
Preserve requiredness calibration candidates and do not infer a message or save behavior.

## GAP-003

source_refs: SRC-002..SRC-006; SRC-009..SRC-011; ATOM-006; ATOM-011; ATOM-016; ATOM-018; ATOM-020; ATOM-032; ATOM-037; ATOM-042
`BSR 49, 52, 55, 57, 59, 69, 73, 77`; `SRC-002..SRC-006`; `SRC-009..SRC-011`.
Cover only source-backed UI-visible success effects; retain the technical-attribution limitation.

## DICT-001

DICT-001 | Пол клиента | support/АФБ справочники 26.06.26.md | mview.dictionaries.natural_person.gender_d | extracted | Мужчина`; `Женщина | none_required:no_archived_values | SRC-006`; `ATOM-019`; `TC-ACPD-011`; `TC-ACPD-024 | none_required:covered | Complete active values are preserved from the canonical inventory.
