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
{"package_id":"application-card-client-personal-data-v6","stage":"writer-r1-shard-002","shard_index":2,"shard_count":4,"shard_digest":"6f3c59c15ba59bd1eeaa3acf5a3206a65becb8fe92311623938a7031ddf5d09b","test_case_count":12,"obligation_count":14}
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

- OBL-003: property=SRC-002.P02 | source=SRC-002 | required=Evidence содержит control/action/empty `Фамилия`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-022 | status=covered
- atom: ATOM-003 | source=column О=Да | statement=Поле `Фамилия` является обязательным. | coverage=covered

- plan: PLAN-022 | atoms=ATOM-003 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Фамилия` пустой, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустая `Фамилия`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-022 | status=covered

- plan: PLAN-016 | atoms=ATOM-005 | check=Ввести `Иванов2` в поле `Фамилия`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-016 | status=covered

- plan: PLAN-017 | atoms=ATOM-005 | check=Ввести `Иванов@` в поле `Фамилия`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-017 | status=covered

- OBL-006: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Значение с цифрой не является допустимым для `Фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-016 | status=covered
- OBL-007: property=SRC-002.P04 | source=SRC-002`; `BSR 48 | required=Значение со спецсимволом кроме `-` не является допустимым для `Фамилия`; механизм UI-отклонения не задан. | planned=TC-ACPD-017 | status=covered
- OBL-008: property=SRC-002.P05 | source=SRC-002`; `BSR 49 | required=Для `Фамилия` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-004 | status=covered
- atom: ATOM-006 | source=BSR 49 | statement=Для поля `Фамилия` при интеграции DaData допускаются подсказки. | coverage=covered

- OBL-010: property=SRC-003.P02 | source=SRC-003 | required=Evidence содержит control/action/empty `Имя`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-023 | status=covered
- atom: ATOM-008 | source=column О=Да | statement=Поле `Имя` является обязательным. | coverage=covered

- plan: PLAN-023 | atoms=ATOM-008 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Имя` пустым, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустое `Имя`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-023 | status=covered

- plan: PLAN-018 | atoms=ATOM-010 | check=Ввести `Иван2` в поле `Имя`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-018 | status=covered

- plan: PLAN-019 | atoms=ATOM-010 | check=Ввести `Иван@` в поле `Имя`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-019 | status=covered

- OBL-013: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Значение с цифрой не является допустимым для `Имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-018 | status=covered
- OBL-014: property=SRC-003.P04 | source=SRC-003`; `BSR 51 | required=Значение со спецсимволом кроме `-` не является допустимым для `Имя`; механизм UI-отклонения не задан. | planned=TC-ACPD-019 | status=covered
- OBL-015: property=SRC-003.P05 | source=SRC-003`; `BSR 52 | required=Для `Имя` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-006 | status=covered
- atom: ATOM-011 | source=BSR 52 | statement=Для поля `Имя` при интеграции DaData допускаются подсказки. | coverage=covered

- plan: PLAN-020 | atoms=ATOM-015 | check=Ввести `Иванович2` в поле `Отчество`. | expected=Значение с цифрой не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-020 | status=covered

- plan: PLAN-021 | atoms=ATOM-015 | check=Ввести `Иванович@` в поле `Отчество`. | expected=Значение с `@` не признаётся допустимым; точная UI-реакция калибруется. | planned=TC-ACPD-021 | status=covered

- OBL-020: property=SRC-004.P04 | source=SRC-004`; `BSR 54 | required=Значение с цифрой не является допустимым для `Отчество`; механизм UI-отклонения не задан. | planned=TC-ACPD-020 | status=covered
- OBL-021: property=SRC-004.P04 | source=SRC-004`; `BSR 54 | required=Значение со спецсимволом кроме `-` не является допустимым для `Отчество`; механизм UI-отклонения не задан. | planned=TC-ACPD-021 | status=covered
- OBL-022: property=SRC-004.P05 | source=SRC-004`; `BSR 55 | required=Для `Отчество` допускаются подсказки DaData при доступной интеграции. | planned=TC-ACPD-008 | status=covered
- atom: ATOM-016 | source=BSR 55 | statement=Для поля `Отчество` при интеграции DaData допускаются подсказки. | coverage=covered

- OBL-025: property=SRC-006.P01 | source=SRC-006`; `BSR 58`; `DICT-001 | required=Поле `Пол` отображается, редактируемо и использует активные значения `DICT-001`. | planned=TC-ACPD-011 | status=covered
- atom: ATOM-019 | source=BSR 58; column О=Да; DICT-001 | statement=Поле `Пол` отображается всегда, обязательно, редактируемо и использует справочник `Пол клиента`. | coverage=covered

- plan: PLAN-024 | atoms=ATOM-019 | check=По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Пол` пустым, инициировать сохранение и записать screenshot/post-state/persistence. | expected=Evidence: действие сохранения, пустой `Пол`, видимое post-state и факт перехода/сохранения записаны; UI-механизм не предписывается. | planned=TC-ACPD-024 | status=covered

- OBL-026: property=SRC-006.P01 | source=SRC-006`; `DICT-001 | required=Evidence содержит control/action/empty `Пол`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-024 | status=covered
- OBL-027: property=SRC-006.P02 | source=SRC-006`; `BSR 59 | required=Видимый `Пол` совпал с expected fixture; до/после записаны, provider-attribution не утверждается. | planned=TC-ACPD-012 | status=covered
- atom: ATOM-020 | source=BSR 59 | statement=Поле `Пол` должно обновляться данными DaData после заполнения ФИО через подсказку DaData. | coverage=covered

- OBL-028: property=SRC-007.P01 | source=SRC-007`; `BSR 60 | required=Поле видимо, редактируемо и отображает введённую логическую дату `D-30 лет`; формат/виджет не утверждаются. | planned=TC-ACPD-013 | status=covered
- atom: ATOM-021 | source=BSR 60; column О=Да | statement=Поле `Дата рождения` отображается всегда, обязательно, редактируемо и имеет тип `Дата`. | coverage=covered

- plan: PLAN-013 | atoms=ATOM-021 | check=Ввести вычисленную дату `D-30 лет`, прочитать отображённое логическое значение. | expected=Поле видимо, редактируемо и отображает ту же логическую дату; формат/виджет не утверждаются. | planned=TC-ACPD-013 | status=covered

- OBL-029: property=SRC-007.P01 | source=SRC-007`; `BSR 60 | required=Evidence содержит control/action/empty `Дата рождения`/post-state/persistence; UI-механизм не предписывается. | planned=TC-ACPD-025 | status=covered
- OBL-030: property=SRC-007.P02 | source=SRC-007`; `BSR 61 | required=Дата `D-18 лет` соответствует верхней возрастной границе. | planned=TC-ACPD-014 | status=covered
- atom: ATOM-022 | source=BSR 61 | statement=Дата рождения не может быть позже чем `D-18 лет`. | coverage=covered

- plan: PLAN-014 | atoms=ATOM-022`; `ATOM-025 | check=Ввести дату `D-18 лет`. | expected=Дата на границе `D-18 лет` соответствует ограничению, вычисляемому от D. | planned=TC-ACPD-014 | status=covered

- OBL-033: property=SRC-007.P04 | source=SRC-007`; `BSR 63 | required=Дата `D-100 лет` соответствует нижней возрастной границе. | planned=TC-ACPD-015 | status=covered
- atom: ATOM-024 | source=BSR 63 | statement=Дата рождения не может быть меньше чем `D-100 лет`. | coverage=covered

- plan: PLAN-015 | atoms=ATOM-024`; `ATOM-025 | check=Ввести дату `D-100 лет`. | expected=Дата на границе `D-100 лет` соответствует ограничению, вычисляемому от D. | planned=TC-ACPD-015 | status=covered

- OBL-034: property=SRC-007.P04 | source=SRC-007`; `BSR 63 | required=Дата раньше `D-100 лет` не соответствует ограничению; точная UI-реакция не определена. | planned=TC-ACPD-028 | status=covered
- OBL-035: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Граница `D-18 лет` вычисляется относительно текущей даты приложения `D`. | planned=TC-ACPD-014 | status=covered
- atom: ATOM-025 | source=BSR 61-63 | statement=Границы даты рождения проверяются относительно текущей даты приложения `D`. | coverage=covered

- OBL-036: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Граница `D-100 лет` вычисляется относительно текущей даты приложения `D`. | planned=TC-ACPD-015 | status=covered
- OBL-037: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Проверка значения позже `D-18 лет` использует текущую дату приложения `D`. | planned=TC-ACPD-026 | status=covered
- OBL-038: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Проверка значения больше `D` использует текущую дату приложения `D`. | planned=TC-ACPD-027 | status=covered
- OBL-039: property=SRC-007.P05 | source=SRC-007`; `BSR 61-63 | required=Проверка значения раньше `D-100 лет` использует текущую дату приложения `D`. | planned=TC-ACPD-028 | status=covered
- OBL-040: property=SRC-008.P01 | source=SRC-008`; `BSR 64 | required=`Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`. | planned=TC-ACPD-029 | status=covered
- atom: ATOM-026 | source=BSR 64 | statement=Поле `Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`. | coverage=covered

## GAP-001

## GAP-002

## DICT-001

DICT-001 | Пол клиента | support/АФБ справочники 26.06.26.md | mview.dictionaries.natural_person.gender_d | extracted | Мужчина`; `Женщина | none_required:no_archived_values | SRC-006`; `ATOM-019`; `TC-ACPD-011`; `TC-ACPD-024 | none_required:covered | Complete active values are preserved from the canonical inventory.

## Exact shard obligation projection

```json
{"package_version":5,"package_id":"application-card-client-personal-data-v6","source_artifact_sha256":"eac473e76b09fa7c951e575bd165475509ea4bc4f3f25c155fc7c576c7e1de16","shard_digest":"6f3c59c15ba59bd1eeaa3acf5a3206a65becb8fe92311623938a7031ddf5d09b","test_case_ids":["TC-ACPD-013","TC-ACPD-014","TC-ACPD-015","TC-ACPD-016","TC-ACPD-017","TC-ACPD-018","TC-ACPD-019","TC-ACPD-020","TC-ACPD-021","TC-ACPD-022","TC-ACPD-023","TC-ACPD-024"],"obligations":[{"obligation_id":"OBL-003","source_refs":["SRC-002","SRC-002.P02"],"atomic_statement":"Поле `Фамилия` является обязательным.","observable_oracle":"Evidence содержит control/action/empty `Фамилия`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Фамилия` пустой, инициировать сохранение и записать screenshot/post-state/persistence.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-003","planned_test_case_id":"TC-ACPD-022"},{"obligation_id":"OBL-006","source_refs":["SRC-002","SRC-002.P04"],"atomic_statement":"В поле `Фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванов2` в поле `Фамилия`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-005","planned_test_case_id":"TC-ACPD-016"},{"obligation_id":"OBL-007","source_refs":["SRC-002","SRC-002.P04"],"atomic_statement":"В поле `Фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванов@` в поле `Фамилия`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-005","planned_test_case_id":"TC-ACPD-017"},{"obligation_id":"OBL-010","source_refs":["SRC-003","SRC-003.P02"],"atomic_statement":"Поле `Имя` является обязательным.","observable_oracle":"Evidence содержит control/action/empty `Имя`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Имя` пустым, инициировать сохранение и записать screenshot/post-state/persistence.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-008","planned_test_case_id":"TC-ACPD-023"},{"obligation_id":"OBL-013","source_refs":["SRC-003","SRC-003.P04"],"atomic_statement":"В поле `Имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Имя`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иван2` в поле `Имя`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-010","planned_test_case_id":"TC-ACPD-018"},{"obligation_id":"OBL-014","source_refs":["SRC-003","SRC-003.P04"],"atomic_statement":"В поле `Имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Имя`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иван@` в поле `Имя`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-010","planned_test_case_id":"TC-ACPD-019"},{"obligation_id":"OBL-020","source_refs":["SRC-004","SRC-004.P04"],"atomic_statement":"В поле `Отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Отчество`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванович2` в поле `Отчество`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-015","planned_test_case_id":"TC-ACPD-020"},{"obligation_id":"OBL-021","source_refs":["SRC-004","SRC-004.P04"],"atomic_statement":"В поле `Отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Отчество`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванович@` в поле `Отчество`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-015","planned_test_case_id":"TC-ACPD-021"},{"obligation_id":"OBL-026","source_refs":["SRC-006","SRC-006.P01","DICT-001"],"atomic_statement":"Поле `Пол` отображается всегда, обязательно, редактируемо и использует справочник `Пол клиента`.","observable_oracle":"Evidence содержит control/action/empty `Пол`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Пол` пустым, инициировать сохранение и записать screenshot/post-state/persistence.","coverage_status":"testable","gap_id":"","dictionary_refs":["DICT-001"],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-019","planned_test_case_id":"TC-ACPD-024"},{"obligation_id":"OBL-028","source_refs":["SRC-007","SRC-007.P01"],"atomic_statement":"Поле `Дата рождения` отображается всегда, обязательно, редактируемо и имеет тип `Дата`.","observable_oracle":"Поле видимо, редактируемо и отображает введённую логическую дату `D-30 лет`; формат/виджет не утверждаются.","test_intent":"Ввести вычисленную дату `D-30 лет`, прочитать отображённое логическое значение.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-002.","constraint_gap_ids":["GAP-002"],"atom_id":"ATOM-021","planned_test_case_id":"TC-ACPD-013"},{"obligation_id":"OBL-030","source_refs":["SRC-007","SRC-007.P02"],"atomic_statement":"Дата рождения не может быть позже чем `D-18 лет`.","observable_oracle":"Дата `D-18 лет` соответствует верхней возрастной границе.","test_intent":"Ввести дату `D-18 лет`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-022","planned_test_case_id":"TC-ACPD-014"},{"obligation_id":"OBL-033","source_refs":["SRC-007","SRC-007.P04"],"atomic_statement":"Дата рождения не может быть меньше чем `D-100 лет`.","observable_oracle":"Дата `D-100 лет` соответствует нижней возрастной границе.","test_intent":"Ввести дату `D-100 лет`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-024","planned_test_case_id":"TC-ACPD-015"},{"obligation_id":"OBL-035","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Граница `D-18 лет` вычисляется относительно текущей даты приложения `D`.","test_intent":"Ввести дату `D-18 лет`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-025","planned_test_case_id":"TC-ACPD-014"},{"obligation_id":"OBL-036","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Граница `D-100 лет` вычисляется относительно текущей даты приложения `D`.","test_intent":"Ввести дату `D-100 лет`.","coverage_status":"testable","gap_id":"","dictionary_refs":[],"notes":"Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.","constraint_gap_ids":["GAP-001"],"atom_id":"ATOM-025","planned_test_case_id":"TC-ACPD-015"}],"coverage_gaps":[{"gap_id":"GAP-001","source_refs":["SRC-002..SRC-004","SRC-007","SRC-009..SRC-011","ATOM-005","ATOM-010","ATOM-015","ATOM-022","ATOM-023","ATOM-024","ATOM-025","ATOM-030","ATOM-035","ATOM-040"],"problem":"`BSR 48, 51, 54, 61–63, 67, 71, 75`; `SRC-002..SRC-004`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Keep calibration candidates; do not invent a message, highlight, filtering, blocked save, or transition.","blocking":false},{"gap_id":"GAP-002","source_refs":["SRC-002","SRC-003","SRC-006","SRC-007","SRC-009..SRC-011","ATOM-003","ATOM-008","ATOM-019","ATOM-021","ATOM-031","ATOM-036","ATOM-041"],"problem":"Table 4 column `О`; `BSR 68, 72, 76`; `SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Preserve requiredness calibration candidates and do not infer a message or save behavior.","blocking":false}]}
```

## Shard draft seed

Replace every seed placeholder. Return these sections only.

```markdown
## TC-ACPD-013

**Название:** [SEED:title:ATOM-021]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-028; ATOM-021; SRC-007; SRC-007.P01
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

[SEED:observable oracle] Поле видимо, редактируемо и отображает введённую логическую дату `D-30 лет`; формат/виджет не утверждаются.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-014

**Название:** [SEED:title:ATOM-022+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-030; ATOM-022; SRC-007; SRC-007.P02; OBL-035; ATOM-025; SRC-007.P05
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

[SEED:observable oracle] Дата `D-18 лет` соответствует верхней возрастной границе.; Граница `D-18 лет` вычисляется относительно текущей даты приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-015

**Название:** [SEED:title:ATOM-024+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-033; ATOM-024; SRC-007; SRC-007.P04; OBL-036; ATOM-025; SRC-007.P05
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

[SEED:observable oracle] Дата `D-100 лет` соответствует нижней возрастной границе.; Граница `D-100 лет` вычисляется относительно текущей даты приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-016

**Название:** [SEED:title:ATOM-005]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-006; ATOM-005; SRC-002; SRC-002.P04
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

[SEED:observable oracle] Значение с цифрой не является допустимым для `Фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-017

**Название:** [SEED:title:ATOM-005]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-007; ATOM-005; SRC-002; SRC-002.P04
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

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-018

**Название:** [SEED:title:ATOM-010]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-013; ATOM-010; SRC-003; SRC-003.P04
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

[SEED:observable oracle] Значение с цифрой не является допустимым для `Имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-019

**Название:** [SEED:title:ATOM-010]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-014; ATOM-010; SRC-003; SRC-003.P04
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

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-020

**Название:** [SEED:title:ATOM-015]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-020; ATOM-015; SRC-004; SRC-004.P04
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

[SEED:observable oracle] Значение с цифрой не является допустимым для `Отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-021

**Название:** [SEED:title:ATOM-015]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-021; ATOM-015; SRC-004; SRC-004.P04
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

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-022

**Название:** [SEED:title:ATOM-003]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-003; ATOM-003; SRC-002; SRC-002.P02
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

[SEED:observable oracle] Evidence содержит control/action/empty `Фамилия`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-023

**Название:** [SEED:title:ATOM-008]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-010; ATOM-008; SRC-003; SRC-003.P02
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

[SEED:observable oracle] Evidence содержит control/action/empty `Имя`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-024

**Название:** [SEED:title:ATOM-019]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-026; ATOM-019; SRC-006; SRC-006.P01; DICT-001
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

[SEED:observable oracle] Evidence содержит control/action/empty `Пол`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```

Return exactly one schema-constrained JSON object and no commentary outside it.
Use status=draft-ready with the complete shard in draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one reason.
