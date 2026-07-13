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
{"package_id":"application-card-client-personal-data-v6","stage":"writer-r1-shard-003","shard_index":3,"shard_count":4,"shard_digest":"ebda5ea4234cbbd39dd0b36825e5e169a53b6635eae1ef0f2e881e365492db75","test_case_count":12,"obligation_count":21}
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

- plan: PLAN-025 | atoms=ATOM-021 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Дата рождения` пустой, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустая `Дата рождения`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-025 | status=covered

- OBL-029: property=SRC-007.P01 | source=SRC-007`; `BSR 60 | required=Evidence содержит control/action/empty `Дата рождения`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-025 | status=covered
- OBL-030: property=SRC-007.P02 | source=SRC-007`; `BSR 61 | required=Дата `D-18 лет` соответствует верхней возрастной границе. | planned=TC-ACPD-014 | status=covered
- atom: ATOM-022 | source=BSR 61 | statement=Дата рождения не может быть позже чем `D-18 лет`. | coverage=covered

- plan: PLAN-026 | atoms=ATOM-022`; `ATOM-025 | check=Ввести дату `D-18 лет + 1 день`. | expected=Значение не соответствует границе D-18 лет; точная UI-реакция калибруется. | planned=TC-ACPD-026 | status=covered

- OBL-031: property=SRC-007.P02 | source=SRC-007`; `BSR 61 | required=Дата позже `D-18 лет` не соответствует ограничению; точная UI-реакция не определена. | planned=TC-ACPD-026 | status=covered
- OBL-032: property=SRC-007.P03 | source=SRC-007`; `BSR 62 | required=Дата больше текущей даты `D` не соответствует ограничению; точная UI-реакция не определена. | planned=TC-ACPD-027 | status=covered
- atom: ATOM-023 | source=BSR 62 | statement=Дата рождения не может быть больше текущей даты `D`. | coverage=covered

- plan: PLAN-027 | atoms=ATOM-023`; `ATOM-025 | check=Ввести дату `D+1 день`. | expected=Значение больше D не соответствует ограничению; точная UI-реакция калибруется. | planned=TC-ACPD-027 | status=covered

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

- OBL-050: property=SRC-010.P01 | source=SRC-010`; `BSR 70 | required=`Предыдущее имя` отображается при `Клиент менял ФИО=Да`. | planned=TC-ACPD-031 | status=covered
- atom: ATOM-033 | source=BSR 70 | statement=Поле `Предыдущее имя` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`. | coverage=covered

- OBL-051: property=SRC-010.P01 | source=SRC-010`; `BSR 70 | required=`Предыдущее имя` не отображается при `Клиент менял ФИО=Нет`. | planned=TC-ACPD-032 | status=covered
- OBL-052: property=SRC-010.P02 | source=SRC-010 | required=`Предыдущее имя` редактируемо при выполнении условия видимости. | planned=TC-ACPD-033 | status=covered
- atom: ATOM-034 | source=column Р=Да | statement=Поле `Предыдущее имя` редактируемо при выполнении условия видимости. | coverage=covered

- OBL-058: property=SRC-011.P01 | source=SRC-011`; `BSR 74 | required=`Предыдущее отчество` отображается при `Клиент менял ФИО=Да`. | planned=TC-ACPD-031 | status=covered
- atom: ATOM-038 | source=BSR 74 | statement=Поле `Предыдущее отчество` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`. | coverage=covered

- OBL-059: property=SRC-011.P01 | source=SRC-011`; `BSR 74 | required=`Предыдущее отчество` не отображается при `Клиент менял ФИО=Нет`. | planned=TC-ACPD-032 | status=covered
- OBL-060: property=SRC-011.P02 | source=SRC-011 | required=`Предыдущее отчество` редактируемо при выполнении условия видимости. | planned=TC-ACPD-033 | status=covered
- atom: ATOM-039 | source=column Р=Да | statement=Поле `Предыдущее отчество` редактируемо при выполнении условия видимости. | coverage=covered

## GAP-001

## GAP-002

## Exact shard obligation projection

```json
{"package_version":5,"package_id":"application-card-client-personal-data-v6","source_artifact_sha256":"eac473e76b09fa7c951e575bd165475509ea4bc4f3f25c155fc7c576c7e1de16","shard_digest":"ebda5ea4234cbbd39dd0b36825e5e169a53b6635eae1ef0f2e881e365492db75","test_case_ids":["TC-ACPD-025","TC-ACPD-026","TC-ACPD-027","TC-ACPD-028","TC-ACPD-029","TC-ACPD-030","TC-ACPD-031","TC-ACPD-032","TC-ACPD-033","TC-ACPD-034","TC-ACPD-035","TC-ACPD-036"],"obligations":[{"obligation_id":"OBL-029","source_refs":["SRC-007","SRC-007.P01"],"atomic_statement":"Поле `Дата рождения` отображается всегда, обязательно, редактируемо и имеет тип `Дата`.","observable_oracle":"Evidence содержит control/action/empty `Дата рождения`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Дата рождения` пустой, инициировать сохранение и записать screenshot/post-state/persistence.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-021","planned_test_case_id":"TC-ACPD-025"},{"obligation_id":"OBL-031","source_refs":["SRC-007","SRC-007.P02"],"atomic_statement":"Дата рождения не может быть позже чем `D-18 лет`.","observable_oracle":"Дата позже `D-18 лет` не соответствует ограничению; точная UI-реакция не определена.","test_intent":"Ввести дату `D-18 лет + 1 день`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-022","planned_test_case_id":"TC-ACPD-026"},{"obligation_id":"OBL-032","source_refs":["SRC-007","SRC-007.P03"],"atomic_statement":"Дата рождения не может быть больше текущей даты `D`.","observable_oracle":"Дата больше текущей даты `D` не соответствует ограничению; точная UI-реакция не определена.","test_intent":"Ввести дату `D+1 день`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-023","planned_test_case_id":"TC-ACPD-027"},{"obligation_id":"OBL-034","source_refs":["SRC-007","SRC-007.P04"],"atomic_statement":"Дата рождения не может быть меньше чем `D-100 лет`.","observable_oracle":"Дата раньше `D-100 лет` не соответствует ограничению; точная UI-реакция не определена.","test_intent":"Ввести дату `D-100 лет - 1 день`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-024","planned_test_case_id":"TC-ACPD-028"},{"obligation_id":"OBL-037","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Проверка значения позже `D-18 лет` использует текущую дату приложения `D`.","test_intent":"Ввести дату `D-18 лет + 1 день`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-025","planned_test_case_id":"TC-ACPD-026"},{"obligation_id":"OBL-038","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Проверка значения больше `D` использует текущую дату приложения `D`.","test_intent":"Ввести дату `D+1 день`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-025","planned_test_case_id":"TC-ACPD-027"},{"obligation_id":"OBL-039","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Проверка значения раньше `D-100 лет` использует текущую дату приложения `D`.","test_intent":"Ввести дату `D-100 лет - 1 день`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-025","planned_test_case_id":"TC-ACPD-028"},{"obligation_id":"OBL-040","source_refs":["SRC-008","SRC-008.P01"],"atomic_statement":"Поле `Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`.","observable_oracle":"`Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`.","test_intent":"Открыть переключатель `Клиент менял ФИО`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-026","planned_test_case_id":"TC-ACPD-029"},{"obligation_id":"OBL-041","source_refs":["SRC-008","SRC-008.P02"],"atomic_statement":"Значение по умолчанию для `Клиент менял ФИО` равно `Нет`.","observable_oracle":"Значение по умолчанию `Клиент менял ФИО` равно `Нет`.","test_intent":"Открыть новую карточку заявки.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-027","planned_test_case_id":"TC-ACPD-030"},{"obligation_id":"OBL-042","source_refs":["SRC-009","SRC-009.P01"],"atomic_statement":"Поле `Предыдущая фамилия` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущая фамилия` отображается при `Клиент менял ФИО=Да`.","test_intent":"Установить `Клиент менял ФИО=Да`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-028","planned_test_case_id":"TC-ACPD-031"},{"obligation_id":"OBL-043","source_refs":["SRC-009","SRC-009.P01"],"atomic_statement":"Поле `Предыдущая фамилия` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущая фамилия` не отображается при `Клиент менял ФИО=Нет`.","test_intent":"Установить `Клиент менял ФИО=Нет`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-028","planned_test_case_id":"TC-ACPD-032"},{"obligation_id":"OBL-044","source_refs":["SRC-009","SRC-009.P02"],"atomic_statement":"Поле `Предыдущая фамилия` редактируемо при выполнении условия видимости.","observable_oracle":"`Предыдущая фамилия` редактируема при выполнении условия видимости.","test_intent":"При `Клиент менял ФИО=Да` указать валидные значения в три предыдущих ФИО-поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-029","planned_test_case_id":"TC-ACPD-033"},{"obligation_id":"OBL-045","source_refs":["SRC-009","SRC-009.P03"],"atomic_statement":"В поле `Предыдущая фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"`Предыдущая фамилия` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Петрова-Сидорова` в поле `Предыдущая фамилия`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-030","planned_test_case_id":"TC-ACPD-034"},{"obligation_id":"OBL-046","source_refs":["SRC-009","SRC-009.P03"],"atomic_statement":"В поле `Предыдущая фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Петрова2` в поле `Предыдущая фамилия`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-030","planned_test_case_id":"TC-ACPD-035"},{"obligation_id":"OBL-047","source_refs":["SRC-009","SRC-009.P03"],"atomic_statement":"В поле `Предыдущая фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Петрова@` в поле `Предыдущая фамилия`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-030","planned_test_case_id":"TC-ACPD-036"},{"obligation_id":"OBL-050","source_refs":["SRC-010","SRC-010.P01"],"atomic_statement":"Поле `Предыдущее имя` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее имя` отображается при `Клиент менял ФИО=Да`.","test_intent":"Установить `Клиент менял ФИО=Да`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-033","planned_test_case_id":"TC-ACPD-031"},{"obligation_id":"OBL-051","source_refs":["SRC-010","SRC-010.P01"],"atomic_statement":"Поле `Предыдущее имя` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее имя` не отображается при `Клиент менял ФИО=Нет`.","test_intent":"Установить `Клиент менял ФИО=Нет`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-033","planned_test_case_id":"TC-ACPD-032"},{"obligation_id":"OBL-052","source_refs":["SRC-010","SRC-010.P02"],"atomic_statement":"Поле `Предыдущее имя` редактируемо при выполнении условия видимости.","observable_oracle":"`Предыдущее имя` редактируемо при выполнении условия видимости.","test_intent":"При `Клиент менял ФИО=Да` указать валидные значения в три предыдущих ФИО-поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-034","planned_test_case_id":"TC-ACPD-033"},{"obligation_id":"OBL-058","source_refs":["SRC-011","SRC-011.P01"],"atomic_statement":"Поле `Предыдущее отчество` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее отчество` отображается при `Клиент менял ФИО=Да`.","test_intent":"Установить `Клиент менял ФИО=Да`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-038","planned_test_case_id":"TC-ACPD-031"},{"obligation_id":"OBL-059","source_refs":["SRC-011","SRC-011.P01"],"atomic_statement":"Поле `Предыдущее отчество` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее отчество` не отображается при `Клиент менял ФИО=Нет`.","test_intent":"Установить `Клиент менял ФИО=Нет`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-038","planned_test_case_id":"TC-ACPD-032"},{"obligation_id":"OBL-060","source_refs":["SRC-011","SRC-011.P02"],"atomic_statement":"Поле `Предыдущее отчество` редактируемо при выполнении условия видимости.","observable_oracle":"`Предыдущее отчество` редактируемо при выполнении условия видимости.","test_intent":"При `Клиент менял ФИО=Да` указать валидные значения в три предыдущих ФИО-поля.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-039","planned_test_case_id":"TC-ACPD-033"}],"coverage_gaps":[{"gap_id":"GAP-001","source_refs":["SRC-002..SRC-004","SRC-007","SRC-009..SRC-011","ATOM-005","ATOM-010","ATOM-015","ATOM-022","ATOM-023","ATOM-024","ATOM-025","ATOM-030","ATOM-035","ATOM-040"],"problem":"`BSR 48, 51, 54, 61–63, 67, 71, 75`; `SRC-002..SRC-004`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Keep calibration candidates; do not invent a message, highlight, filtering, blocked save, or transition.","blocking":false},{"gap_id":"GAP-002","source_refs":["SRC-002","SRC-003","SRC-006","SRC-007","SRC-009..SRC-011","ATOM-003","ATOM-008","ATOM-019","ATOM-021","ATOM-031","ATOM-036","ATOM-041"],"problem":"Table 4 column `О`; `BSR 68, 72, 76`; `SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Preserve requiredness calibration candidates and do not infer a message or save behavior.","blocking":false}]}
```

## Shard draft seed

Replace every seed placeholder. Return these sections only.

```markdown
## TC-ACPD-025

**Название:** [SEED:title:ATOM-021]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-029; ATOM-021; SRC-007; SRC-007.P01
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

[SEED:observable oracle] Evidence содержит control/action/empty `Дата рождения`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-026

**Название:** [SEED:title:ATOM-022+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-031; ATOM-022; SRC-007; SRC-007.P02; OBL-037; ATOM-025; SRC-007.P05
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

[SEED:observable oracle] Дата позже `D-18 лет` не соответствует ограничению; точная UI-реакция не определена.; Проверка значения позже `D-18 лет` использует текущую дату приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-027

**Название:** [SEED:title:ATOM-023+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-032; ATOM-023; SRC-007; SRC-007.P03; OBL-038; ATOM-025; SRC-007.P05
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

[SEED:observable oracle] Дата больше текущей даты `D` не соответствует ограничению; точная UI-реакция не определена.; Проверка значения больше `D` использует текущую дату приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-028

**Название:** [SEED:title:ATOM-024+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-034; ATOM-024; SRC-007; SRC-007.P04; OBL-039; ATOM-025; SRC-007.P05
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

[SEED:observable oracle] Дата раньше `D-100 лет` не соответствует ограничению; точная UI-реакция не определена.; Проверка значения раньше `D-100 лет` использует текущую дату приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-029

**Название:** [SEED:title:ATOM-026]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-040; ATOM-026; SRC-008; SRC-008.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-030

**Название:** [SEED:title:ATOM-027]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-041; ATOM-027; SRC-008; SRC-008.P02

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение по умолчанию `Клиент менял ФИО` равно `Нет`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-031

**Название:** [SEED:title:ATOM-028+ATOM-033+ATOM-038]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-042; ATOM-028; SRC-009; SRC-009.P01; OBL-050; ATOM-033; SRC-010; SRC-010.P01; OBL-058; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущая фамилия` отображается при `Клиент менял ФИО=Да`.; `Предыдущее имя` отображается при `Клиент менял ФИО=Да`.; `Предыдущее отчество` отображается при `Клиент менял ФИО=Да`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-032

**Название:** [SEED:title:ATOM-028+ATOM-033+ATOM-038]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-043; ATOM-028; SRC-009; SRC-009.P01; OBL-051; ATOM-033; SRC-010; SRC-010.P01; OBL-059; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущая фамилия` не отображается при `Клиент менял ФИО=Нет`.; `Предыдущее имя` не отображается при `Клиент менял ФИО=Нет`.; `Предыдущее отчество` не отображается при `Клиент менял ФИО=Нет`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-033

**Название:** [SEED:title:ATOM-029+ATOM-034+ATOM-039]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-044; ATOM-029; SRC-009; SRC-009.P02; OBL-052; ATOM-034; SRC-010; SRC-010.P02; OBL-060; ATOM-039; SRC-011; SRC-011.P02

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущая фамилия` редактируема при выполнении условия видимости.; `Предыдущее имя` редактируемо при выполнении условия видимости.; `Предыдущее отчество` редактируемо при выполнении условия видимости.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-034

**Название:** [SEED:title:ATOM-030]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-045; ATOM-030; SRC-009; SRC-009.P03
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

[SEED:observable oracle] `Предыдущая фамилия` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-035

**Название:** [SEED:title:ATOM-030]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-046; ATOM-030; SRC-009; SRC-009.P03
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

[SEED:observable oracle] Значение с цифрой не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-036

**Название:** [SEED:title:ATOM-030]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-047; ATOM-030; SRC-009; SRC-009.P03
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

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```

Return exactly one schema-constrained JSON object and no commentary outside it.
Use status=draft-ready with the complete shard in draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one reason.
