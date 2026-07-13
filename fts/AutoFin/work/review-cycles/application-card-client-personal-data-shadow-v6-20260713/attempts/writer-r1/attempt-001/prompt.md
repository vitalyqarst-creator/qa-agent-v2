# Codex exec prepared writer bounded shard

This is one read-only shard of a runner-owned deterministic full-set plan.
Use only the embedded runtime profile, selected evidence and exact obligation projection below.
Do not call shell or file tools and do not create or modify workspace files.
Return only the assigned `## TC-*` sections in the declared order. Do not add an H1 title, metadata, coverage summary or unassigned test case.
Every assigned obligation_id and atom_id must appear in the traceability of its planned test case.
Do not read previous cycles, generated drafts, production test cases or full sources.
FT-first fixtures may be portable synthetic values, relative dates or runtime-selected integration responses with source-defined observable properties.
Return blocked-input only when this shard's embedded evidence cannot define the test intent or observable oracle without invention.

# Prepared Writer Runtime Profile

This is the technical execution projection inside `ft-test-case-writer`. It introduces no new QA policy. Upstream source/scope preparation and the prepared compiler have already applied the canonical writer contracts; the fresh writer executes the allowlisted draft step from an immutable package.

## Eligibility

Continue only when the embedded payload confirms:

- package version `5` and valid package digest;
- `execution_profile = simple-field-property` or `standard-required`;
- an explicit context profile and unsupported dimensions;
- scope-local source evidence and atomic obligations;
- every testable obligation has a concrete intent, a portable fixture contract and observable oracle;
- every unresolved or non-blocking constraint is linked to an explicit `GAP-*`;
- a runner-owned draft seed and schema-constrained output contract.

Return `blocked-input` when these conditions do not hold. Do not open project instructions or full sources to bypass eligibility.

## Structured Execution

1. Use only the embedded payload. Do not call the environment probe, shell, file, Git or search tools.
   This is a zero-command budget: the runner alone atomically materializes the returned draft.
2. Return one schema-constrained JSON object. For `draft-ready`, put the complete unsigned Markdown in `draft_markdown`; the runner atomically materializes `draft.md`.
3. Create executable `TC-*` only for `coverage_status = testable` and implement the supplied `test_intent`, concrete fixture and `observable_oracle`.
4. Preserve exact `OBL-* -> ATOM-* -> TC-*` traceability. Use a shared planned TC only when the package already groups those obligations.
5. Never turn `gap`, `unclear` or `not-applicable` into executable coverage.
6. Preserve every `constraint_gap_ids` marker in the linked TC. When the context profile requires UI calibration, label it `ui-calibration-required` and `candidate-ui-calibration`.
7. Do not invent screens, fields, dictionaries, values, messages, validation mechanisms, setup, API/DB effects, state transitions or persistence.
8. Keep one primary check and one main observable result per TC. Use unique titles that name the field/action and exact positive, boundary or invalid class.
9. A concrete FT-first fixture may be a synthetic value, relative date or runtime-selected integration response with source-defined observable properties. A stand record ID, locator, token, session or prerecorded provider response is not required until UI-prep.
10. Return `blocked-input` with empty `draft_markdown` and precise reasons only when inline evidence cannot define the test intent or observable oracle without invention.

## Assisted Fallback

`prepared-standard --prepared-standard-writer-mode assisted` is an explicit recovery route, never an automatic retry. It may use only manifest-listed instruction artifacts and a single targeted registered-source fallback for a named unresolved OBL/ATOM. Record the path, locator and reason. Broad discovery, production test cases, prior cycles and generated drafts remain forbidden.

## Quality Floor

- structurally complete Markdown with no seed sentinels or angle-bracket placeholders;
- reproducible preconditions and concrete permitted data;
- numbered user actions and one final observable expected result;
- exact requirement/OBL/ATOM traceability;
- unique IDs and titles;
- explicit calibration lifecycle for constraint gaps;
- no workspace mutation by the structured writer;
- no production write or promotion.

## Context profile: `character-restriction-calibration`

- Keep each invalid class and field independent.
- For obligations with constraint_gap_ids, preserve every GAP-* marker and label the case candidate-ui-calibration.
- Do not choose a validation message, filtering, highlight, save or transition mechanism that the evidence does not define.

## Verified shard metadata

```json
{"package_id":"application-card-client-personal-data-v6","stage":"writer-r1","shard_index":1,"shard_count":4,"shard_digest":"f6d1b274ff5788f924609f90bcd18e25572843423d743cd1d6ff5da603a8a90c","test_case_count":12,"obligation_count":17}
```

## Selected source-backed evidence

# Prepared Source Evidence

- package_id: `application-card-client-personal-data-v6`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/prepared-input/.application-card-client-personal-data-v6.compiled-evidence.md`
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

- OBL-004: property=SRC-002.P03 | source=SRC-002 | required=Поле `Фамилия` доступно для редактирования. | planned=TC-ACPD-002 | status=covered
- atom: ATOM-004 | source=column Р=Да | statement=Поле `Фамилия` редактируемо. | coverage=covered

- plan: PLAN-002 | atoms=ATOM-004`; `ATOM-009`; `ATOM-014 | check=Указать валидные значения в три ФИО-поля. | expected=Каждое из трёх полей принимает ввод. | planned=TC-ACPD-002 | status=covered

- OBL-005: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Поле `Фамилия` допускает текстовые символы и символ `-`. | planned=TC-ACPD-003 | status=covered
- atom: ATOM-005 | source=BSR 48 | statement=В поле `Фамилия` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-003 | atoms=ATOM-005 | check=Ввести `Иванов-Петров` в поле `Фамилия`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-003 | status=covered

- OBL-006: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Значение с цифрой не является допустимым для `Фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-016 | status=covered
- OBL-007: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Значение со спецсимволом кроме `-` не является допустимым для `Фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-017 | status=covered
- OBL-008: property=SRC-002.P05 | source=SRC-002`; `BSR 49 | required=Для `Фамилия` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-004 | status=covered
- atom: ATOM-006 | source=BSR 49 | statement=Для поля `Фамилия` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-004 | atoms=ATOM-006 | check=Начать ввод `Иван` в поле `Фамилия` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-004 | status=covered

- OBL-009: property=SRC-003.P01 | source=SRC-003`; `BSR 50 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-007 | source=BSR 50 | statement=Поле `Имя` отображается всегда. | coverage=covered

- OBL-011: property=SRC-003.P03 | source=SRC-003 | required=Поле `Имя` доступно для редактирования. | planned=TC-ACPD-002 | status=covered
- atom: ATOM-009 | source=column Р=Да | statement=Поле `Имя` редактируемо. | coverage=covered

- OBL-012: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Поле `Имя` допускает текстовые символы и символ `-`. | planned=TC-ACPD-005 | status=covered
- atom: ATOM-010 | source=BSR 51 | statement=В поле `Имя` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-005 | atoms=ATOM-010 | check=Ввести `Анна-Мария` в поле `Имя`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-005 | status=covered

- OBL-013: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Значение с цифрой не является допустимым для `Имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-018 | status=covered
- OBL-014: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Значение со спецсимволом кроме `-` не является допустимым для `Имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-019 | status=covered
- OBL-015: property=SRC-003.P05 | source=SRC-003`; `BSR 52 | required=Для `Имя` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-006 | status=covered
- atom: ATOM-011 | source=BSR 52 | statement=Для поля `Имя` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-006 | atoms=ATOM-011 | check=Начать ввод `Анна` в поле `Имя` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-006 | status=covered

- OBL-016: property=SRC-004.P01 | source=SRC-004`; `BSR 53 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-012 | source=BSR 53 | statement=Поле `Отчество` отображается всегда. | coverage=covered

- OBL-018: property=SRC-004.P03 | source=SRC-004 | required=Поле `Отчество` доступно для редактирования. | planned=TC-ACPD-002 | status=covered
- atom: ATOM-014 | source=column Р=Да | statement=Поле `Отчество` редактируемо. | coverage=covered

- OBL-019: property=SRC-004.P04 | source=SRC-004`; `BSR 54 | required=Поле `Отчество` допускает текстовые символы и символ `-`. | planned=TC-ACPD-007 | status=covered
- atom: ATOM-015 | source=BSR 54 | statement=В поле `Отчество` возможен ввод только текстовых символов и символа `-`. | coverage=covered

- plan: PLAN-007 | atoms=ATOM-015 | check=Ввести `Иванович-Петрович` в поле `Отчество`. | expected=Допустимое текстовое значение с `-` принимается полем. | planned=TC-ACPD-007 | status=covered

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

- OBL-026: property=SRC-006.P01 | source=SRC-006`; `DICT-001 | required=Evidence содержит control/action/empty `Пол`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-024 | status=covered
- OBL-027: property=SRC-006.P02 | source=SRC-006`; `BSR 59 | required=Видимый `Пол` совпал с expected fixture; до/после записаны, provider-attribution не утверждается. | planned=TC-ACPD-012 | status=covered
- atom: ATOM-020 | source=BSR 59 | statement=Поле `Пол` должно обновляться данными DaData после заполнения ФИО через подсказку DaData. | coverage=covered

- plan: PLAN-012 | atoms=ATOM-020 | check=По `FIX-ACPD-RUNTIME-DADATA-001` записать исходный `Пол`, ввести `Иван`, выбрать фактически возвращённую подсказку с известным полом и сравнить итоговый `Пол` со значением выбранной подсказки. | expected=После выбора подсказки видимый `Пол` совпадает с полом выбранной подсказки; до/после записаны, provider-attribution не утверждается. | planned=TC-ACPD-012 | status=covered

## GAP-001

## GAP-002

## GAP-003

## DICT-001

DICT-001 | Пол клиента | support/АФБ справочники 26.06.26.md | mview.dictionaries.natural_person.gender_d | extracted | Мужчина`; `Женщина | none_required:no_archived_values | SRC-006`; `ATOM-019`; `TC-ACPD-011`; `TC-ACPD-024 | none_required:covered | Complete active values are preserved from the canonical inventory.

## Exact shard obligation projection

```json
{"package_version":5,"package_id":"application-card-client-personal-data-v6","source_artifact_sha256":"eac473e76b09fa7c951e575bd165475509ea4bc4f3f25c155fc7c576c7e1de16","shard_digest":"f6d1b274ff5788f924609f90bcd18e25572843423d743cd1d6ff5da603a8a90c","test_case_ids":["TC-ACPD-001","TC-ACPD-002","TC-ACPD-003","TC-ACPD-004","TC-ACPD-005","TC-ACPD-006","TC-ACPD-007","TC-ACPD-008","TC-ACPD-009","TC-ACPD-010","TC-ACPD-011","TC-ACPD-012"],"obligations":[{"obligation_id":"OBL-001","source_refs":["SRC-001","SRC-001.P01"],"atomic_statement":"Блок `Персональные данные` отображается в карточке заявки.","observable_oracle":"Блок `Персональные данные` отображается в карточке заявки.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-001","planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-002","source_refs":["SRC-002","SRC-002.P01"],"atomic_statement":"Поле `Фамилия` отображается всегда.","observable_oracle":"Поле `Фамилия` отображается всегда.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-002","planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-004","source_refs":["SRC-002","SRC-002.P03"],"atomic_statement":"Поле `Фамилия` редактируемо.","observable_oracle":"Поле `Фамилия` доступно для редактирования.","test_intent":"Указать валидные значения в три ФИО-поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-004","planned_test_case_id":"TC-ACPD-002"},{"obligation_id":"OBL-005","source_refs":["SRC-002","SRC-002.P04"],"atomic_statement":"В поле `Фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Поле `Фамилия` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Иванов-Петров` в поле `Фамилия`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-005","planned_test_case_id":"TC-ACPD-003"},{"obligation_id":"OBL-008","source_refs":["SRC-002","SRC-002.P05"],"atomic_statement":"Для поля `Фамилия` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Фамилия` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Иван` в поле `Фамилия` при доступной интеграции.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-006","planned_test_case_id":"TC-ACPD-004"},{"obligation_id":"OBL-009","source_refs":["SRC-003","SRC-003.P01"],"atomic_statement":"Поле `Имя` отображается всегда.","observable_oracle":"Поле `Имя` отображается всегда.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-007","planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-011","source_refs":["SRC-003","SRC-003.P03"],"atomic_statement":"Поле `Имя` редактируемо.","observable_oracle":"Поле `Имя` доступно для редактирования.","test_intent":"Указать валидные значения в три ФИО-поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-009","planned_test_case_id":"TC-ACPD-002"},{"obligation_id":"OBL-012","source_refs":["SRC-003","SRC-003.P04"],"atomic_statement":"В поле `Имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Поле `Имя` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Анна-Мария` в поле `Имя`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-010","planned_test_case_id":"TC-ACPD-005"},{"obligation_id":"OBL-015","source_refs":["SRC-003","SRC-003.P05"],"atomic_statement":"Для поля `Имя` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Имя` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Анна` в поле `Имя` при доступной интеграции.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-011","planned_test_case_id":"TC-ACPD-006"},{"obligation_id":"OBL-016","source_refs":["SRC-004","SRC-004.P01"],"atomic_statement":"Поле `Отчество` отображается всегда.","observable_oracle":"Поле `Отчество` отображается всегда.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-012","planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-018","source_refs":["SRC-004","SRC-004.P03"],"atomic_statement":"Поле `Отчество` редактируемо.","observable_oracle":"Поле `Отчество` доступно для редактирования.","test_intent":"Указать валидные значения в три ФИО-поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-014","planned_test_case_id":"TC-ACPD-002"},{"obligation_id":"OBL-019","source_refs":["SRC-004","SRC-004.P04"],"atomic_statement":"В поле `Отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Поле `Отчество` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Иванович-Петрович` в поле `Отчество`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-015","planned_test_case_id":"TC-ACPD-007"},{"obligation_id":"OBL-022","source_refs":["SRC-004","SRC-004.P05"],"atomic_statement":"Для поля `Отчество` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Отчество` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Иванович` в поле `Отчество` при доступной интеграции.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-016","planned_test_case_id":"TC-ACPD-008"},{"obligation_id":"OBL-023","source_refs":["SRC-005","SRC-005.P01"],"atomic_statement":"Поле `ID клиента` отображается всегда и недоступно для ручного редактирования.","observable_oracle":"`ID клиента` отображается всегда и недоступен для ручного редактирования.","test_intent":"Открыть карточку заявки и попытаться изменить `ID клиента`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-017","planned_test_case_id":"TC-ACPD-009"},{"obligation_id":"OBL-024","source_refs":["SRC-005","SRC-005.P02"],"atomic_statement":"Поле `ID клиента` заполняется автоматически системой ID клиента из АБС после сохранения заявки.","observable_oracle":"После save видимый `ID клиента` изменился с пустого на непустой; значение записано, ABS-атрибуция не утверждается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` записать пустой `ID клиента`, инициировать сохранение заявки и записать новое видимое значение.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-018","planned_test_case_id":"TC-ACPD-010"},{"obligation_id":"OBL-025","source_refs":["SRC-006","SRC-006.P01","DICT-001"],"atomic_statement":"Поле `Пол` отображается всегда, обязательно, редактируемо и использует справочник `Пол клиента`.","observable_oracle":"Поле `Пол` отображается, редактируемо и использует активные значения `DICT-001`.","test_intent":"Открыть переключатель `Пол`.","coverage_status":"testable","gap_id":"","dictionary_refs":["DICT-001"],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-019","planned_test_case_id":"TC-ACPD-011"},{"obligation_id":"OBL-027","source_refs":["SRC-006","SRC-006.P02"],"atomic_statement":"Поле `Пол` должно обновляться данными DaData после заполнения ФИО через подсказку DaData.","observable_oracle":"Видимый `Пол` совпал с expected fixture; до/после записаны, provider-attribution не утверждается.","test_intent":"По `FIX-ACPD-RUNTIME-DADATA-001` записать исходный `Пол`, ввести `Иван`, выбрать фактически возвращённую подсказку с известным полом и сравнить итоговый `Пол` со значением выбранной подсказки.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-020","planned_test_case_id":"TC-ACPD-012"}],"coverage_gaps":[{"gap_id":"GAP-001","source_refs":["SRC-002..SRC-004","SRC-007","SRC-009..SRC-011","ATOM-005","ATOM-010","ATOM-015","ATOM-022","ATOM-023","ATOM-024","ATOM-025","ATOM-030","ATOM-035","ATOM-040"],"problem":"`BSR 48, 51, 54, 61–63, 67, 71, 75`; `SRC-002..SRC-004`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Keep calibration candidates; do not invent a message, highlight, filtering, blocked save, or transition.","blocking":false},{"gap_id":"GAP-002","source_refs":["SRC-002","SRC-003","SRC-006","SRC-007","SRC-009..SRC-011","ATOM-003","ATOM-008","ATOM-019","ATOM-021","ATOM-031","ATOM-036","ATOM-041"],"problem":"Table 4 column `О`; `BSR 68, 72, 76`; `SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Preserve requiredness calibration candidates and do not infer a message or save behavior.","blocking":false},{"gap_id":"GAP-003","source_refs":["SRC-002..SRC-006","SRC-009..SRC-011","ATOM-006","ATOM-011","ATOM-016","ATOM-018","ATOM-020","ATOM-032","ATOM-037","ATOM-042"],"problem":"`BSR 49, 52, 55, 57, 59, 69, 73, 77`; `SRC-002..SRC-006`; `SRC-009..SRC-011`.","handling":"Cover only source-backed UI-visible success effects; retain the technical-attribution limitation.","blocking":false}]}
```

## Shard draft seed

Replace every seed placeholder. Return these sections only.

```markdown
## TC-ACPD-001

**Название:** [SEED:title:ATOM-001+ATOM-002+ATOM-007+ATOM-012]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-001; ATOM-001; SRC-001; SRC-001.P01; OBL-002; ATOM-002; SRC-002; SRC-002.P01; OBL-009; ATOM-007; SRC-003; SRC-003.P01; OBL-016; ATOM-012; SRC-004; SRC-004.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Блок `Персональные данные` отображается в карточке заявки.; Поле `Фамилия` отображается всегда.; Поле `Имя` отображается всегда.; Поле `Отчество` отображается всегда.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-002

**Название:** [SEED:title:ATOM-004+ATOM-009+ATOM-014]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-004; ATOM-004; SRC-002; SRC-002.P03; OBL-011; ATOM-009; SRC-003; SRC-003.P03; OBL-018; ATOM-014; SRC-004; SRC-004.P03

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Фамилия` доступно для редактирования.; Поле `Имя` доступно для редактирования.; Поле `Отчество` доступно для редактирования.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-003

**Название:** [SEED:title:ATOM-005]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-005; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Фамилия` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-004

**Название:** [SEED:title:ATOM-006]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-008; ATOM-006; SRC-002; SRC-002.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Фамилия` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-005

**Название:** [SEED:title:ATOM-010]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-012; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Имя` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-006

**Название:** [SEED:title:ATOM-011]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-015; ATOM-011; SRC-003; SRC-003.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Имя` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-007

**Название:** [SEED:title:ATOM-015]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-019; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Отчество` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-008

**Название:** [SEED:title:ATOM-016]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-022; ATOM-016; SRC-004; SRC-004.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Отчество` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-009

**Название:** [SEED:title:ATOM-017]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-023; ATOM-017; SRC-005; SRC-005.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `ID клиента` отображается всегда и недоступен для ручного редактирования.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-010

**Название:** [SEED:title:ATOM-018]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-024; ATOM-018; SRC-005; SRC-005.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После save видимый `ID клиента` изменился с пустого на непустой; значение записано, ABS-атрибуция не утверждается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-011

**Название:** [SEED:title:ATOM-019]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-025; ATOM-019; SRC-006; SRC-006.P01; DICT-001
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Пол` отображается, редактируемо и использует активные значения `DICT-001`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-012

**Название:** [SEED:title:ATOM-020]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-027; ATOM-020; SRC-006; SRC-006.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Видимый `Пол` совпал с expected fixture; до/после записаны, provider-attribution не утверждается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```

Return exactly one schema-constrained JSON object and no commentary outside it.
Use status=draft-ready with the complete shard in draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one reason.
