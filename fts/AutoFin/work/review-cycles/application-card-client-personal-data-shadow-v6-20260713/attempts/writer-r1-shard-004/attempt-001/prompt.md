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
{"package_id":"application-card-client-personal-data-v6","stage":"writer-r1-shard-004","shard_index":4,"shard_count":4,"shard_digest":"65548a892c5b963cbf5987bbc47597b497a06771df6464e86d5f540f76a415e6","test_case_count":11,"obligation_count":13}
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

- OBL-017: property=SRC-004.P02 | source=SRC-004 | required=Save завершён; после повторного открытия `Отчество` пусто и не блокировало сохранение. | planned=TC-ACPD-047 | status=covered
- atom: ATOM-013 | source=column О=Нет | statement=Поле `Отчество` не является обязательным. | coverage=covered

- plan: PLAN-047 | atoms=ATOM-013 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Отчество` пустым, инициировать сохранение и открыть сохранённую заявку повторно. | expected=Сохранение завершено; после повторного открытия `Отчество` пусто и не блокировало сохранение. | planned=TC-ACPD-047 | status=covered

- OBL-046: property=SRC-009.P03 | source=SRC-009`; `BSR 67 | required=Значение с цифрой не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-035 | status=covered
- OBL-047: property=SRC-009.P03 | source=SRC-009`; `BSR 67 | required=Значение со спецсимволом кроме `-` не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-036 | status=covered
- OBL-048: property=SRC-009.P04 | source=SRC-009`; `BSR 68 | required=Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-041 | status=covered
- atom: ATOM-031 | source=BSR 68 | statement=Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО. | coverage=covered

- plan: PLAN-041 | atoms=ATOM-031`; `ATOM-036`; `ATOM-041 | check=По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, условие, пустая группа, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-041 | status=covered

- OBL-049: property=SRC-009.P05 | source=SRC-009`; `BSR 69 | required=Для `Предыдущая фамилия` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-037 | status=covered
- atom: ATOM-032 | source=BSR 69 | statement=Для поля `Предыдущая фамилия` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-037 | atoms=ATOM-032 | check=Начать ввод `Петрова` в поле `Предыдущая фамилия` при доступной интеграции. | expected=Подсказки DaData допускаются; отказ и provider-attribution не утверждаются. | planned=TC-ACPD-037 | status=covered

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

## GAP-002

## GAP-003

## Exact shard obligation projection

```json
{"package_version":5,"package_id":"application-card-client-personal-data-v6","source_artifact_sha256":"eac473e76b09fa7c951e575bd165475509ea4bc4f3f25c155fc7c576c7e1de16","shard_digest":"65548a892c5b963cbf5987bbc47597b497a06771df6464e86d5f540f76a415e6","test_case_ids":["TC-ACPD-037","TC-ACPD-038","TC-ACPD-039","TC-ACPD-040","TC-ACPD-041","TC-ACPD-042","TC-ACPD-043","TC-ACPD-044","TC-ACPD-045","TC-ACPD-046","TC-ACPD-047"],"obligations":[{"obligation_id":"OBL-017","source_refs":["SRC-004","SRC-004.P02"],"atomic_statement":"Поле `Отчество` не является обязательным.","observable_oracle":"Save завершён; после повторного открытия `Отчество` пусто и не блокировало сохранение.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Отчество` пустым, инициировать сохранение и открыть сохранённую заявку повторно.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts.","constraint_gap_ids":[],"atom_id":"ATOM-013","planned_test_case_id":"TC-ACPD-047"},{"obligation_id":"OBL-048","source_refs":["SRC-009","SRC-009.P04"],"atomic_statement":"Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО.","observable_oracle":"Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-031","planned_test_case_id":"TC-ACPD-041"},{"obligation_id":"OBL-049","source_refs":["SRC-009","SRC-009.P05"],"atomic_statement":"Для поля `Предыдущая фамилия` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Предыдущая фамилия` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Петрова` в поле `Предыдущая фамилия` при доступной интеграции.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-032","planned_test_case_id":"TC-ACPD-037"},{"obligation_id":"OBL-053","source_refs":["SRC-010","SRC-010.P03"],"atomic_statement":"В поле `Предыдущее имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"`Предыдущее имя` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Анна-Мария` в поле `Предыдущее имя`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-035","planned_test_case_id":"TC-ACPD-038"},{"obligation_id":"OBL-054","source_refs":["SRC-010","SRC-010.P03"],"atomic_statement":"В поле `Предыдущее имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.","test_intent":"Ввести `Анна2` в поле `Предыдущее имя`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-035","planned_test_case_id":"TC-ACPD-039"},{"obligation_id":"OBL-055","source_refs":["SRC-010","SRC-010.P03"],"atomic_statement":"В поле `Предыдущее имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.","test_intent":"Ввести `Анна@` в поле `Предыдущее имя`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-035","planned_test_case_id":"TC-ACPD-040"},{"obligation_id":"OBL-056","source_refs":["SRC-010","SRC-010.P04"],"atomic_statement":"Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО.","observable_oracle":"Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-036","planned_test_case_id":"TC-ACPD-041"},{"obligation_id":"OBL-057","source_refs":["SRC-010","SRC-010.P05"],"atomic_statement":"Для поля `Предыдущее имя` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Предыдущее имя` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Анна` в поле `Предыдущее имя` при доступной интеграции.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-037","planned_test_case_id":"TC-ACPD-042"},{"obligation_id":"OBL-061","source_refs":["SRC-011","SRC-011.P03"],"atomic_statement":"В поле `Предыдущее отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"`Предыдущее отчество` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Ивановна-Петровна` в поле `Предыдущее отчество`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-040","planned_test_case_id":"TC-ACPD-043"},{"obligation_id":"OBL-062","source_refs":["SRC-011","SRC-011.P03"],"atomic_statement":"В поле `Предыдущее отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.","test_intent":"Ввести `Ивановна2` в поле `Предыдущее отчество`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-040","planned_test_case_id":"TC-ACPD-044"},{"obligation_id":"OBL-063","source_refs":["SRC-011","SRC-011.P03"],"atomic_statement":"В поле `Предыдущее отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.","test_intent":"Ввести `Ивановна@` в поле `Предыдущее отчество`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-040","planned_test_case_id":"TC-ACPD-045"},{"obligation_id":"OBL-064","source_refs":["SRC-011","SRC-011.P04"],"atomic_statement":"Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО.","observable_oracle":"Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-041","planned_test_case_id":"TC-ACPD-041"},{"obligation_id":"OBL-065","source_refs":["SRC-011","SRC-011.P05"],"atomic_statement":"Для поля `Предыдущее отчество` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Предыдущее отчество` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Ивановна` в поле `Предыдущее отчество` при доступной интеграции.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-003.","constraint_gap_ids":["GAP-003"],"atom_id":"ATOM-042","planned_test_case_id":"TC-ACPD-046"}],"coverage_gaps":[{"gap_id":"GAP-001","source_refs":["SRC-002..SRC-004","SRC-007","SRC-009..SRC-011","ATOM-005","ATOM-010","ATOM-015","ATOM-022","ATOM-023","ATOM-024","ATOM-025","ATOM-030","ATOM-035","ATOM-040"],"problem":"`BSR 48, 51, 54, 61–63, 67, 71, 75`; `SRC-002..SRC-004`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Keep calibration candidates; do not invent a message, highlight, filtering, blocked save, or transition.","blocking":false},{"gap_id":"GAP-002","source_refs":["SRC-002","SRC-003","SRC-006","SRC-007","SRC-009..SRC-011","ATOM-003","ATOM-008","ATOM-019","ATOM-021","ATOM-031","ATOM-036","ATOM-041"],"problem":"Table 4 column `О`; `BSR 68, 72, 76`; `SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Preserve requiredness calibration candidates and do not infer a message or save behavior.","blocking":false},{"gap_id":"GAP-003","source_refs":["SRC-002..SRC-006","SRC-009..SRC-011","ATOM-006","ATOM-011","ATOM-016","ATOM-018","ATOM-020","ATOM-032","ATOM-037","ATOM-042"],"problem":"`BSR 49, 52, 55, 57, 59, 69, 73, 77`; `SRC-002..SRC-006`; `SRC-009..SRC-011`.","handling":"Cover only source-backed UI-visible success effects; retain the technical-attribution limitation.","blocking":false}]}
```

## Shard draft seed

Replace every seed placeholder. Return these sections only.

```markdown
## TC-ACPD-037

**Название:** [SEED:title:ATOM-032]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-049; ATOM-032; SRC-009; SRC-009.P05
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

[SEED:observable oracle] Для `Предыдущая фамилия` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-038

**Название:** [SEED:title:ATOM-035]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-053; ATOM-035; SRC-010; SRC-010.P03
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

[SEED:observable oracle] `Предыдущее имя` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-039

**Название:** [SEED:title:ATOM-035]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-054; ATOM-035; SRC-010; SRC-010.P03
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

[SEED:observable oracle] Значение с цифрой не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-040

**Название:** [SEED:title:ATOM-035]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-055; ATOM-035; SRC-010; SRC-010.P03
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

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-041

**Название:** [SEED:title:ATOM-031+ATOM-036+ATOM-041]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-048; ATOM-031; SRC-009; SRC-009.P04; OBL-056; ATOM-036; SRC-010; SRC-010.P04; OBL-064; ATOM-041; SRC-011; SRC-011.P04
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

[SEED:observable oracle] Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-042

**Название:** [SEED:title:ATOM-037]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-057; ATOM-037; SRC-010; SRC-010.P05
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

[SEED:observable oracle] Для `Предыдущее имя` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-043

**Название:** [SEED:title:ATOM-040]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-061; ATOM-040; SRC-011; SRC-011.P03
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

[SEED:observable oracle] `Предыдущее отчество` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-044

**Название:** [SEED:title:ATOM-040]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-062; ATOM-040; SRC-011; SRC-011.P03
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

[SEED:observable oracle] Значение с цифрой не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-045

**Название:** [SEED:title:ATOM-040]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-063; ATOM-040; SRC-011; SRC-011.P03
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

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-046

**Название:** [SEED:title:ATOM-042]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-065; ATOM-042; SRC-011; SRC-011.P05
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

[SEED:observable oracle] Для `Предыдущее отчество` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-047

**Название:** [SEED:title:ATOM-013]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-017; ATOM-013; SRC-004; SRC-004.P02

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Save завершён; после повторного открытия `Отчество` пусто и не блокировало сохранение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```

Return exactly one schema-constrained JSON object and no commentary outside it.
Use status=draft-ready with the complete shard in draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one reason.
