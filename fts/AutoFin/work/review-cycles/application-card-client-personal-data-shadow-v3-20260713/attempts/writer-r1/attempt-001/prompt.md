# Codex exec prepared writer structured path

The upstream package already applied the full source, scope and writer policy.
Use only the embedded Prepared Writer Runtime Profile below; do not load the full ft-test-case-writer skill or reread package/project reference files.
This stage is read-only. Do not call shell or file tools and do not create or modify workspace files.
Return the complete unsigned draft inside the schema-constrained final JSON object. The runner alone materializes and validates draft.md.
Do not read existing/generated test cases, earlier cycle artifacts or production test-cases as evidence.
If the embedded evidence is insufficient, return blocked-input with a precise reason. Do not open a full source in this mode.

<!-- PREPARED-STAGE-PAYLOAD:BEGIN -->
## Verified package metadata

```json
{
  "package_version": 5,
  "package_id": "application-card-client-personal-data-v3",
  "ft_slug": "AutoFin",
  "scope_slug": "application-card-client-personal-data",
  "section_id": "14",
  "execution_profile": "standard-required",
  "context_profile": "character-restriction-calibration",
  "unsupported_dimensions": [
    "dependency-state",
    "input-boundaries",
    "integration-persistence",
    "numeric-boundaries"
  ],
  "fallback_policy": "targeted-only"
}
```

# Prepared Writer Runtime Profile

This is the technical execution projection inside `ft-test-case-writer`. It introduces no new QA policy. Upstream source/scope preparation and the prepared compiler have already applied the canonical writer contracts; the fresh writer executes the allowlisted draft step from an immutable package.

## Eligibility

Continue only when the embedded payload confirms:

- package version `5` and valid package digest;
- `execution_profile = simple-field-property` or `standard-required`;
- an explicit context profile and unsupported dimensions;
- scope-local source evidence and atomic obligations;
- every testable obligation has a concrete intent, fixture and observable oracle;
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
9. Return `blocked-input` with empty `draft_markdown` and precise reasons when inline evidence is insufficient.

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

# Prepared Source Evidence

- package_id: `application-card-client-personal-data-v3`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/prepared-input/.application-card-client-personal-data-v3.compiled-evidence.md`
- source_sha256: `ec5a8937926db02b0d97798471c7d930ed0665ffaaedc3894c341da0d22402d4`
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

- OBL-001: property=SRC-001.P01 | source=SRC-001 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-001 | source=no_requirement_code:SRC-001 | statement=Блок `Персональные данные` отображается в карточке заявки. | coverage=covered

- plan: PLAN-001 | atoms=ATOM-001`; `ATOM-002`; `ATOM-007`; `ATOM-012 | check=Открыть карточку заявки и проверить блок и три поля. | expected=Блок и поля `Фамилия`, `Имя`, `Отчество` отображаются. | planned=TC-ACPD-001 | status=covered

- OBL-002: property=SRC-002.P01 | source=SRC-002`; `BSR 47 | required=same-as-atom | planned=TC-ACPD-001 | status=covered
- atom: ATOM-002 | source=BSR 47 | statement=Поле `Фамилия` отображается всегда. | coverage=covered

- OBL-003: property=SRC-002.P02 | source=SRC-002 | required=Для `Фамилия` обязательность задана колонкой `О=Да`; точная UI-реакция не определена. | planned=TC-ACPD-022 | status=covered
- atom: ATOM-003 | source=column О=Да | statement=Поле `Фамилия` является обязательным. | coverage=covered

- plan: PLAN-022 | atoms=ATOM-003 | check=Оставить `Фамилия` пустым при попытке продолжить сценарий. | expected=Обязательность задана ФТ; фактическую реакцию UI необходимо зафиксировать без её предопределения. | planned=TC-ACPD-022 | status=covered

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

- OBL-010: property=SRC-003.P02 | source=SRC-003 | required=Для `Имя` обязательность задана колонкой `О=Да`; точная UI-реакция не определена. | planned=TC-ACPD-023 | status=covered
- atom: ATOM-008 | source=column О=Да | statement=Поле `Имя` является обязательным. | coverage=covered

- plan: PLAN-023 | atoms=ATOM-008 | check=Оставить `Имя` пустым при попытке продолжить сценарий. | expected=Обязательность задана ФТ; фактическую реакцию UI необходимо зафиксировать без её предопределения. | planned=TC-ACPD-023 | status=covered

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

- OBL-017: property=SRC-004.P02 | source=SRC-004 | required=same-as-atom | planned=TC-ACPD-047 | status=covered
- atom: ATOM-013 | source=column О=Нет | statement=Поле `Отчество` не является обязательным. | coverage=covered

- plan: PLAN-047 | atoms=ATOM-013 | check=Оставить поле `Отчество` пустым при заполненных обязательных полях. | expected=Отсутствие значения в необязательном поле само по себе не нарушает его обязательность. | planned=TC-ACPD-047 | status=covered

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

- OBL-024: property=SRC-005.P02 | source=SRC-005`; `BSR 57 | required=После сохранения заявки поле `ID клиента` заполняется системой значением ID из АБС. | planned=TC-ACPD-010 | status=covered
- atom: ATOM-018 | source=BSR 57 | statement=Поле `ID клиента` заполняется автоматически системой ID клиента из АБС после сохранения заявки. | coverage=covered

- plan: PLAN-010 | atoms=ATOM-018 | check=Сохранить валидную заявку и наблюдать поле `ID клиента`. | expected=После сохранения поле заполняется ID клиента из АБС; техническая атрибуция не утверждается. | planned=TC-ACPD-010 | status=covered

- OBL-025: property=SRC-006.P01 | source=SRC-006`; `BSR 58`; `DICT-001 | required=Поле `Пол` отображается, редактируемо и использует активные значения `DICT-001`. | planned=TC-ACPD-011 | status=covered
- atom: ATOM-019 | source=BSR 58; column О=Да; DICT-001 | statement=Поле `Пол` отображается всегда, обязательно, редактируемо и использует справочник `Пол клиента`. | coverage=covered

- plan: PLAN-011 | atoms=ATOM-019 | check=Открыть переключатель `Пол`. | expected=Поле показывает полный активный перечень `Мужчина`, `Женщина` и доступно для выбора. | planned=TC-ACPD-011 | status=covered

- plan: PLAN-024 | atoms=ATOM-019 | check=Не выбирать значение в поле `Пол` при попытке продолжить сценарий. | expected=Обязательность задана ФТ; фактическую реакцию UI необходимо зафиксировать без её предопределения. | planned=TC-ACPD-024 | status=covered

- OBL-026: property=SRC-006.P01 | source=SRC-006`; `DICT-001 | required=Для `Пол` обязательность задана колонкой `О=Да`; точная UI-реакция не определена. | planned=TC-ACPD-024 | status=covered
- OBL-027: property=SRC-006.P02 | source=SRC-006`; `BSR 59 | required=После заполнения ФИО через подсказку DaData поле `Пол` обновляется данными DaData. | planned=TC-ACPD-012 | status=covered
- atom: ATOM-020 | source=BSR 59 | statement=Поле `Пол` должно обновляться данными DaData после заполнения ФИО через подсказку DaData. | coverage=covered

- plan: PLAN-012 | atoms=ATOM-020 | check=Выбрать подсказку DaData после заполнения ФИО. | expected=Поле `Пол` обновляется данными после выбора подсказки; provider-attribution не утверждается. | planned=TC-ACPD-012 | status=covered

- OBL-028: property=SRC-007.P01 | source=SRC-007`; `BSR 60 | required=`Дата рождения` отображается, обязательна, редактируема и имеет тип `Дата`. | planned=TC-ACPD-013 | status=covered
- atom: ATOM-021 | source=BSR 60; column О=Да | statement=Поле `Дата рождения` отображается всегда, обязательно, редактируемо и имеет тип `Дата`. | coverage=covered

- plan: PLAN-013 | atoms=ATOM-021 | check=Открыть поле `Дата рождения`. | expected=Поле отображается, редактируемо и имеет тип `Дата`. | planned=TC-ACPD-013 | status=covered

- plan: PLAN-025 | atoms=ATOM-021 | check=Оставить `Дата рождения` пустой при попытке продолжить сценарий. | expected=Обязательность задана ФТ; фактическую реакцию UI необходимо зафиксировать без её предопределения. | planned=TC-ACPD-025 | status=covered

- OBL-029: property=SRC-007.P01 | source=SRC-007`; `BSR 60 | required=Для `Дата рождения` обязательность задана колонкой `О=Да`; точная UI-реакция не определена. | planned=TC-ACPD-025 | status=covered
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
- OBL-048: property=SRC-009.P04 | source=SRC-009`; `BSR 68 | required=При `Клиент менял ФИО=Да` заполняется хотя бы одно поле группы предыдущей ФИО; точная UI-реакция не определена. | planned=TC-ACPD-041 | status=covered
- atom: ATOM-031 | source=BSR 68 | statement=Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО. | coverage=covered

- plan: PLAN-041 | atoms=ATOM-031`; `ATOM-036`; `ATOM-041 | check=Установить `Клиент менял ФИО=Да` и оставить три предыдущих ФИО-поля пустыми. | expected=При условии `Да` ФТ требует хотя бы одно заполненное поле; фактическая UI-реакция калибруется. | planned=TC-ACPD-041 | status=covered

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
- OBL-056: property=SRC-010.P04 | source=SRC-010`; `BSR 72 | required=При `Клиент менял ФИО=Да` заполняется хотя бы одно поле группы предыдущей ФИО; точная UI-реакция не определена. | planned=TC-ACPD-041 | status=covered
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
- OBL-064: property=SRC-011.P04 | source=SRC-011`; `BSR 76 | required=При `Клиент менял ФИО=Да` заполняется хотя бы одно поле группы предыдущей ФИО; точная UI-реакция не определена. | planned=TC-ACPD-041 | status=covered
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

## Verified obligation transport

The full atomic-obligations artifact is intentionally not repeated here. Its source-backed semantics are present above, its exact test-case mapping is present in the draft seed below, and the runner gates plus reviewer consume the immutable full artifact.

```json
{
  "artifact": "fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/prepared-input/application-card-client-personal-data-v3/atomic-obligations.json",
  "artifact_sha256": "813542a83464ec7dc8130d23877390552f2d690e6798719a1a8b48d51f78afd9",
  "obligation_count": 65,
  "coverage_status_counts": {
    "testable": 65
  },
  "coverage_gap_count": 3,
  "writer_semantics_source": "selected-source-evidence",
  "test_case_mapping_source": "runner-generated-draft-seed",
  "full_artifact_consumers": [
    "runner-gates",
    "reviewer"
  ]
}
```

## Draft seed template (not an existing output file)

Return a complete draft based on this template; the runner writes it after validating the JSON contract.
Do not copy seed sentinels or placeholders into draft_markdown.

```markdown
# Тест-кейсы

<!-- PREPARED-DRAFT-SEED: replace all [SEED:*] values before completion -->

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

[SEED:observable oracle] После сохранения заявки поле `ID клиента` заполняется системой значением ID из АБС.

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

[SEED:observable oracle] После заполнения ФИО через подсказку DaData поле `Пол` обновляется данными DaData.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

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

[SEED:observable oracle] `Дата рождения` отображается, обязательна, редактируема и имеет тип `Дата`.

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

[SEED:observable oracle] Для `Фамилия` обязательность задана колонкой `О=Да`; точная UI-реакция не определена.

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

[SEED:observable oracle] Для `Имя` обязательность задана колонкой `О=Да`; точная UI-реакция не определена.

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

[SEED:observable oracle] Для `Пол` обязательность задана колонкой `О=Да`; точная UI-реакция не определена.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

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

[SEED:observable oracle] Для `Дата рождения` обязательность задана колонкой `О=Да`; точная UI-реакция не определена.

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

[SEED:observable oracle] При `Клиент менял ФИО=Да` заполняется хотя бы одно поле группы предыдущей ФИО; точная UI-реакция не определена.

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

[SEED:observable oracle] Поле `Отчество` не является обязательным.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```
<!-- PREPARED-STAGE-PAYLOAD:END -->

Return exactly one JSON object and no commentary outside it.
Use status=draft-ready with a complete draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one blocking reason.
