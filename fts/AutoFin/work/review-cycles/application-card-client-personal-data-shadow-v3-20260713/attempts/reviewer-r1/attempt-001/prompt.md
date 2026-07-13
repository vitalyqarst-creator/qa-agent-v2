# Codex exec prepared-standard reviewer compact path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

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
  "reviewed_draft_sha256": "1882b625c7c43aaa197c59834cd91fc848b57ee14bf4439c0a3f2eb0c63d8a12"
}
```

# Prepared Reviewer Runtime Profile

This is the technical execution projection inside `ft-test-case-reviewer`. It introduces no new QA policy. The immutable package, context rule card and deterministic gates materialize the applicable canonical reviewer rubric for both `simple-field-property` and `standard-required` scopes.

## Eligibility

Continue only when the payload confirms:

- current package version and immutable draft SHA-256;
- explicit execution/context profiles and unsupported dimensions;
- scope-local source evidence and atomic obligations;
- passed structure, seed, obligation, quality and evidence-access gates;
- semantic-overlap diagnostic and calibration lifecycle.

Return a blocking finding when the payload is insufficient or inconsistent. Do not open full project instructions, package files, production test cases, earlier cycles or full sources to bypass eligibility.

## Review Procedure

1. Review every supplied obligation exactly once and preserve its exact `obligation_id -> atom_id` pair and draft SHA-256.
2. For every testable obligation, verify that its linked TC performs the supplied condition/action with concrete data and reaches the supplied observable oracle.
3. For every gap, unclear or not-applicable obligation, verify that the draft does not invent executable coverage.
4. For every non-blocking constraint gap, verify that the linked TC preserves the `GAP-*` and does not choose an unspecified mechanism.
5. Apply the embedded context rule card: boundary points remain independent; invalid classes remain independent; branch preconditions and integration triggers remain explicit.
6. Reject invented screens, fields, literals, dictionary values, messages, statuses, UI reactions, API/DB effects, persistence or internal state.
7. Reject non-atomic cases, generic fixtures, placeholder steps, source-rule-only expected results, duplicate titles and nominal traceability.
8. Classify every semantic-overlap group. Accept a shared body only when the package explicitly groups one observable multi-obligation check.
9. For UI-calibration candidates, require `ui-calibration-required`, `candidate-ui-calibration`, the linked GAP and a neutral expected result that does not preselect filtering/message/highlight/save behavior.
10. Return exactly the structured review contract requested by the runner. Do not write files.

## Decision Floor

- `accepted` requires every obligation to have a compatible verdict, every testable obligation to be correctly covered, all gaps to be preserved and no error finding.
- `changes-required` requires at least one concrete finding linked to supplied ATOM/TC identifiers, unless it is a set-level scope finding.
- A failed deterministic gate, draft hash mismatch, unknown identifier, lost constraint gap or insufficient evidence prevents sign-off.

## Runtime Boundary

No command is needed. If runtime confirmation is absolutely required, only the explicitly allowlisted environment probe may be used. Any repository exploration or workspace mutation violates the compact prepared reviewer contract.

## Context profile: `character-restriction-calibration`

- Keep each invalid class and field independent.
- For obligations with constraint_gap_ids, preserve every GAP-* marker and label the case candidate-ui-calibration.
- Do not choose a validation message, filtering, highlight, save or transition mechanism that the evidence does not define.

## Selected source evidence

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

## Verified obligation review index

The immutable full obligations artifact is identified by digest below. Its semantic statements and oracles are supplied in selected source evidence; this index supplies every exact review-contract ID, status, reference and gap.

```json
{"artifact":"fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/prepared-input/application-card-client-personal-data-v3/atomic-obligations.json","artifact_sha256":"813542a83464ec7dc8130d23877390552f2d690e6798719a1a8b48d51f78afd9","obligation_count":65,"coverage_gap_ids":["GAP-001","GAP-002","GAP-003"],"semantic_evidence_source":"selected-source-evidence","obligations":[{"obligation_id":"OBL-001","atom_id":"ATOM-001","coverage_status":"testable","source_refs":["SRC-001","SRC-001.P01"],"planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-002","atom_id":"ATOM-002","coverage_status":"testable","source_refs":["SRC-002","SRC-002.P01"],"planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-003","atom_id":"ATOM-003","coverage_status":"testable","source_refs":["SRC-002","SRC-002.P02"],"planned_test_case_id":"TC-ACPD-022","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-004","atom_id":"ATOM-004","coverage_status":"testable","source_refs":["SRC-002","SRC-002.P03"],"planned_test_case_id":"TC-ACPD-002"},{"obligation_id":"OBL-005","atom_id":"ATOM-005","coverage_status":"testable","source_refs":["SRC-002","SRC-002.P04"],"planned_test_case_id":"TC-ACPD-003","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-006","atom_id":"ATOM-005","coverage_status":"testable","source_refs":["SRC-002","SRC-002.P04"],"planned_test_case_id":"TC-ACPD-016","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-007","atom_id":"ATOM-005","coverage_status":"testable","source_refs":["SRC-002","SRC-002.P04"],"planned_test_case_id":"TC-ACPD-017","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-008","atom_id":"ATOM-006","coverage_status":"testable","source_refs":["SRC-002","SRC-002.P05"],"planned_test_case_id":"TC-ACPD-004","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-009","atom_id":"ATOM-007","coverage_status":"testable","source_refs":["SRC-003","SRC-003.P01"],"planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-010","atom_id":"ATOM-008","coverage_status":"testable","source_refs":["SRC-003","SRC-003.P02"],"planned_test_case_id":"TC-ACPD-023","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-011","atom_id":"ATOM-009","coverage_status":"testable","source_refs":["SRC-003","SRC-003.P03"],"planned_test_case_id":"TC-ACPD-002"},{"obligation_id":"OBL-012","atom_id":"ATOM-010","coverage_status":"testable","source_refs":["SRC-003","SRC-003.P04"],"planned_test_case_id":"TC-ACPD-005","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-013","atom_id":"ATOM-010","coverage_status":"testable","source_refs":["SRC-003","SRC-003.P04"],"planned_test_case_id":"TC-ACPD-018","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-014","atom_id":"ATOM-010","coverage_status":"testable","source_refs":["SRC-003","SRC-003.P04"],"planned_test_case_id":"TC-ACPD-019","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-015","atom_id":"ATOM-011","coverage_status":"testable","source_refs":["SRC-003","SRC-003.P05"],"planned_test_case_id":"TC-ACPD-006","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-016","atom_id":"ATOM-012","coverage_status":"testable","source_refs":["SRC-004","SRC-004.P01"],"planned_test_case_id":"TC-ACPD-001"},{"obligation_id":"OBL-017","atom_id":"ATOM-013","coverage_status":"testable","source_refs":["SRC-004","SRC-004.P02"],"planned_test_case_id":"TC-ACPD-047"},{"obligation_id":"OBL-018","atom_id":"ATOM-014","coverage_status":"testable","source_refs":["SRC-004","SRC-004.P03"],"planned_test_case_id":"TC-ACPD-002"},{"obligation_id":"OBL-019","atom_id":"ATOM-015","coverage_status":"testable","source_refs":["SRC-004","SRC-004.P04"],"planned_test_case_id":"TC-ACPD-007","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-020","atom_id":"ATOM-015","coverage_status":"testable","source_refs":["SRC-004","SRC-004.P04"],"planned_test_case_id":"TC-ACPD-020","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-021","atom_id":"ATOM-015","coverage_status":"testable","source_refs":["SRC-004","SRC-004.P04"],"planned_test_case_id":"TC-ACPD-021","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-022","atom_id":"ATOM-016","coverage_status":"testable","source_refs":["SRC-004","SRC-004.P05"],"planned_test_case_id":"TC-ACPD-008","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-023","atom_id":"ATOM-017","coverage_status":"testable","source_refs":["SRC-005","SRC-005.P01"],"planned_test_case_id":"TC-ACPD-009"},{"obligation_id":"OBL-024","atom_id":"ATOM-018","coverage_status":"testable","source_refs":["SRC-005","SRC-005.P02"],"planned_test_case_id":"TC-ACPD-010","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-025","atom_id":"ATOM-019","coverage_status":"testable","source_refs":["SRC-006","SRC-006.P01","DICT-001"],"planned_test_case_id":"TC-ACPD-011","dictionary_refs":["DICT-001"],"constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-026","atom_id":"ATOM-019","coverage_status":"testable","source_refs":["SRC-006","SRC-006.P01","DICT-001"],"planned_test_case_id":"TC-ACPD-024","dictionary_refs":["DICT-001"],"constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-027","atom_id":"ATOM-020","coverage_status":"testable","source_refs":["SRC-006","SRC-006.P02"],"planned_test_case_id":"TC-ACPD-012","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-028","atom_id":"ATOM-021","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P01"],"planned_test_case_id":"TC-ACPD-013","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-029","atom_id":"ATOM-021","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P01"],"planned_test_case_id":"TC-ACPD-025","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-030","atom_id":"ATOM-022","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P02"],"planned_test_case_id":"TC-ACPD-014","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-031","atom_id":"ATOM-022","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P02"],"planned_test_case_id":"TC-ACPD-026","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-032","atom_id":"ATOM-023","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P03"],"planned_test_case_id":"TC-ACPD-027","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-033","atom_id":"ATOM-024","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P04"],"planned_test_case_id":"TC-ACPD-015","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-034","atom_id":"ATOM-024","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P04"],"planned_test_case_id":"TC-ACPD-028","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-035","atom_id":"ATOM-025","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P05"],"planned_test_case_id":"TC-ACPD-014","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-036","atom_id":"ATOM-025","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P05"],"planned_test_case_id":"TC-ACPD-015","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-037","atom_id":"ATOM-025","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P05"],"planned_test_case_id":"TC-ACPD-026","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-038","atom_id":"ATOM-025","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P05"],"planned_test_case_id":"TC-ACPD-027","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-039","atom_id":"ATOM-025","coverage_status":"testable","source_refs":["SRC-007","SRC-007.P05"],"planned_test_case_id":"TC-ACPD-028","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-040","atom_id":"ATOM-026","coverage_status":"testable","source_refs":["SRC-008","SRC-008.P01"],"planned_test_case_id":"TC-ACPD-029"},{"obligation_id":"OBL-041","atom_id":"ATOM-027","coverage_status":"testable","source_refs":["SRC-008","SRC-008.P02"],"planned_test_case_id":"TC-ACPD-030"},{"obligation_id":"OBL-042","atom_id":"ATOM-028","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P01"],"planned_test_case_id":"TC-ACPD-031"},{"obligation_id":"OBL-043","atom_id":"ATOM-028","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P01"],"planned_test_case_id":"TC-ACPD-032"},{"obligation_id":"OBL-044","atom_id":"ATOM-029","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P02"],"planned_test_case_id":"TC-ACPD-033"},{"obligation_id":"OBL-045","atom_id":"ATOM-030","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P03"],"planned_test_case_id":"TC-ACPD-034","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-046","atom_id":"ATOM-030","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P03"],"planned_test_case_id":"TC-ACPD-035","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-047","atom_id":"ATOM-030","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P03"],"planned_test_case_id":"TC-ACPD-036","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-048","atom_id":"ATOM-031","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P04"],"planned_test_case_id":"TC-ACPD-041","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-049","atom_id":"ATOM-032","coverage_status":"testable","source_refs":["SRC-009","SRC-009.P05"],"planned_test_case_id":"TC-ACPD-037","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-050","atom_id":"ATOM-033","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P01"],"planned_test_case_id":"TC-ACPD-031"},{"obligation_id":"OBL-051","atom_id":"ATOM-033","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P01"],"planned_test_case_id":"TC-ACPD-032"},{"obligation_id":"OBL-052","atom_id":"ATOM-034","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P02"],"planned_test_case_id":"TC-ACPD-033"},{"obligation_id":"OBL-053","atom_id":"ATOM-035","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P03"],"planned_test_case_id":"TC-ACPD-038","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-054","atom_id":"ATOM-035","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P03"],"planned_test_case_id":"TC-ACPD-039","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-055","atom_id":"ATOM-035","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P03"],"planned_test_case_id":"TC-ACPD-040","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-056","atom_id":"ATOM-036","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P04"],"planned_test_case_id":"TC-ACPD-041","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-057","atom_id":"ATOM-037","coverage_status":"testable","source_refs":["SRC-010","SRC-010.P05"],"planned_test_case_id":"TC-ACPD-042","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-058","atom_id":"ATOM-038","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P01"],"planned_test_case_id":"TC-ACPD-031"},{"obligation_id":"OBL-059","atom_id":"ATOM-038","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P01"],"planned_test_case_id":"TC-ACPD-032"},{"obligation_id":"OBL-060","atom_id":"ATOM-039","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P02"],"planned_test_case_id":"TC-ACPD-033"},{"obligation_id":"OBL-061","atom_id":"ATOM-040","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P03"],"planned_test_case_id":"TC-ACPD-043","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-062","atom_id":"ATOM-040","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P03"],"planned_test_case_id":"TC-ACPD-044","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-063","atom_id":"ATOM-040","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P03"],"planned_test_case_id":"TC-ACPD-045","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-064","atom_id":"ATOM-041","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P04"],"planned_test_case_id":"TC-ACPD-041","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-065","atom_id":"ATOM-042","coverage_status":"testable","source_refs":["SRC-011","SRC-011.P05"],"planned_test_case_id":"TC-ACPD-046","constraint_gap_ids":["GAP-003"]}]}
```

## Deterministic gate summaries

```json
[
  {
    "gate": "structure",
    "passed": true,
    "validator": "codex_review_cycle_runner.evaluate_test_case_markdown_structure",
    "findings_count": 0
  },
  {
    "gate": "seed",
    "passed": true,
    "validator": "prepared-draft-seed-gate-v1",
    "findings_count": 0
  },
  {
    "gate": "obligation",
    "passed": true,
    "validator": "prepared-package-obligation-gate-v3",
    "findings_count": 0,
    "test_case_count": 47,
    "testable_obligations": 65,
    "covered_obligations": [
      "OBL-001",
      "OBL-002",
      "OBL-003",
      "OBL-004",
      "OBL-005",
      "OBL-006",
      "OBL-007",
      "OBL-008",
      "OBL-009",
      "OBL-010",
      "OBL-011",
      "OBL-012",
      "OBL-013",
      "OBL-014",
      "OBL-015",
      "OBL-016",
      "OBL-017",
      "OBL-018",
      "OBL-019",
      "OBL-020",
      "OBL-021",
      "OBL-022",
      "OBL-023",
      "OBL-024",
      "OBL-025",
      "OBL-026",
      "OBL-027",
      "OBL-028",
      "OBL-029",
      "OBL-030",
      "OBL-031",
      "OBL-032",
      "OBL-033",
      "OBL-034",
      "OBL-035",
      "OBL-036",
      "OBL-037",
      "OBL-038",
      "OBL-039",
      "OBL-040",
      "OBL-041",
      "OBL-042",
      "OBL-043",
      "OBL-044",
      "OBL-045",
      "OBL-046",
      "OBL-047",
      "OBL-048",
      "OBL-049",
      "OBL-050",
      "OBL-051",
      "OBL-052",
      "OBL-053",
      "OBL-054",
      "OBL-055",
      "OBL-056",
      "OBL-057",
      "OBL-058",
      "OBL-059",
      "OBL-060",
      "OBL-061",
      "OBL-062",
      "OBL-063",
      "OBL-064",
      "OBL-065"
    ]
  },
  {
    "gate": "semantic-overlap",
    "passed": true,
    "validator": "semantic-overlap-diagnostic-v1",
    "findings_count": 0,
    "test_case_count": 47
  },
  {
    "gate": "writer-evidence-access",
    "passed": true,
    "validator": "prepared-evidence-access-gate-v1",
    "findings_count": 0,
    "commands_checked": 0,
    "fallback_authorizations": 0
  },
  {
    "gate": "quality-bundle",
    "passed": true,
    "validator": "prepared-quality-gate-bundle-v1",
    "findings_count": 0,
    "test_case_count": 47
  }
]
```

## Semantic overlap diagnostic (non-blocking, reviewer classification required)

```json
{
  "passed": true,
  "validator": "semantic-overlap-diagnostic-v1",
  "status": "clean",
  "blocking": false,
  "test_case_count": 47,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\application-card-client-personal-data-shadow-v3-20260713\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle summary

```json
{"artifact":"fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/attempts/writer-r1/attempt-001/runner-output/calibration-lifecycle.json","artifact_sha256":"7e6802456c2e5122e87838a071e1eab40dd67938f539ed2ebdbf2498bc6d5caa","context_profile":"character-restriction-calibration","open_count":45,"resolved_count":0,"status_counts":{"awaiting-ui-calibration":45},"constraint_gap_ids":["GAP-002","GAP-001","GAP-003"],"per_obligation_mapping_source":"verified-obligation-review-index"}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-ACPD-001

**Название:** Отображение блока и полей ФИО
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-001; ATOM-001; SRC-001; SRC-001.P01; OBL-002; ATOM-002; SRC-002; SRC-002.P01; OBL-009; ATOM-007; SRC-003; SRC-003.P01; OBL-016; ATOM-012; SRC-004; SRC-004.P01

### Предусловия

1. Доступна карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть карточку заявки.

### Итоговый ожидаемый результат

Отображается блок `Персональные данные` с полями `Фамилия`, `Имя` и `Отчество`.

### Постусловия

- Не применимо.

## TC-ACPD-002

**Название:** Редактирование полей ФИО
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-004; ATOM-004; SRC-002; SRC-002.P03; OBL-011; ATOM-009; SRC-003; SRC-003.P03; OBL-018; ATOM-014; SRC-004; SRC-004.P03

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иванов`; `Анна`; `Иванович`.

### Шаги

1. Ввести указанные значения в поля `Фамилия`, `Имя` и `Отчество`.

### Итоговый ожидаемый результат

Каждое из трёх полей принимает введённое значение.

### Постусловия

- Не применимо.

## TC-ACPD-003

**Название:** Ввод букв и дефиса в поле «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-005; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иванов-Петров`.

### Шаги

1. Ввести тестовое значение в поле `Фамилия`.

### Итоговый ожидаемый результат

Поле принимает значение, состоящее из текстовых символов и дефиса.

### Постусловия

- Не применимо.

## TC-ACPD-004

**Название:** Подсказки при вводе фамилии
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-008; ATOM-006; SRC-002; SRC-002.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Интеграция подсказок доступна, а по значению `Иван` имеются варианты.

### Тестовые данные

- `Иван`.

### Шаги

1. Начать ввод тестового значения в поле `Фамилия`.

### Итоговый ожидаемый результат

Для поля отображаются доступные пользователю подсказки; технический источник подсказок не подтверждается этим кейсом.

### Постусловия

- Не применимо.

## TC-ACPD-005

**Название:** Ввод букв и дефиса в поле «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-012; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Анна-Мария`.

### Шаги

1. Ввести тестовое значение в поле `Имя`.

### Итоговый ожидаемый результат

Поле принимает значение, состоящее из текстовых символов и дефиса.

### Постусловия

- Не применимо.

## TC-ACPD-006

**Название:** Подсказки при вводе имени
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-015; ATOM-011; SRC-003; SRC-003.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Интеграция подсказок доступна, а по значению `Анна` имеются варианты.

### Тестовые данные

- `Анна`.

### Шаги

1. Начать ввод тестового значения в поле `Имя`.

### Итоговый ожидаемый результат

Для поля отображаются доступные пользователю подсказки; технический источник подсказок не подтверждается этим кейсом.

### Постусловия

- Не применимо.

## TC-ACPD-007

**Название:** Ввод букв и дефиса в поле «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-019; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иванович-Петрович`.

### Шаги

1. Ввести тестовое значение в поле `Отчество`.

### Итоговый ожидаемый результат

Поле принимает значение, состоящее из текстовых символов и дефиса.

### Постусловия

- Не применимо.

## TC-ACPD-008

**Название:** Подсказки при вводе отчества
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-022; ATOM-016; SRC-004; SRC-004.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Интеграция подсказок доступна, а по значению `Иванович` имеются варианты.

### Тестовые данные

- `Иванович`.

### Шаги

1. Начать ввод тестового значения в поле `Отчество`.

### Итоговый ожидаемый результат

Для поля отображаются доступные пользователю подсказки; технический источник подсказок не подтверждается этим кейсом.

### Постусловия

- Не применимо.

## TC-ACPD-009

**Название:** Отображение и запрет ручного редактирования ID клиента
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-023; ATOM-017; SRC-005; SRC-005.P01

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Найти поле `ID клиента` и попытаться изменить его значение вручную.

### Итоговый ожидаемый результат

Поле `ID клиента` отображается и недоступно для ручного редактирования.

### Постусловия

- Не применимо.

## TC-ACPD-010

**Название:** Автозаполнение ID клиента после сохранения заявки
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-024; ATOM-018; SRC-005; SRC-005.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Подготовлена заявка, значения которой позволяют выполнить сохранение.

### Тестовые данные

- Значения заявки, необходимые для её сохранения.

### Шаги

1. Сохранить заявку.

### Итоговый ожидаемый результат

После сохранения в поле `ID клиента` отображается автоматически заполненное системой значение ID клиента из АБС; техническая атрибуция не проверяется.

### Постусловия

- Сохранённая заявка доступна для последующей работы.

## TC-ACPD-011

**Название:** Перечень и выбор значений поля «Пол»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-025; ATOM-019; SRC-006; SRC-006.P01; DICT-001
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Значения справочника: `Мужчина`, `Женщина`.

### Шаги

1. Открыть поле `Пол`.
2. Последовательно выбрать каждое значение справочника.

### Итоговый ожидаемый результат

Поле отображается и редактируемо; пользователю доступны полный активный перечень `Мужчина` и `Женщина`.

### Постусловия

- Не применимо.

## TC-ACPD-012

**Название:** Обновление пола после выбора подсказки ФИО
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-027; ATOM-020; SRC-006; SRC-006.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Интеграция подсказок доступна, а для вводимого ФИО имеется подсказка с данными пола.

### Тестовые данные

- ФИО, для которого доступна подсказка с данными пола.

### Шаги

1. Заполнить ФИО через доступную подсказку и выбрать её.

### Итоговый ожидаемый результат

После выбора подсказки значение поля `Пол` обновляется данными из выбранной подсказки; технический источник обновления не подтверждается этим кейсом.

### Постусловия

- Не применимо.

## TC-ACPD-013

**Название:** Отображение и редактирование даты рождения
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-028; ATOM-021; SRC-007; SRC-007.P01
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Дата в допустимом диапазоне.

### Шаги

1. Открыть поле `Дата рождения` и ввести допустимую дату.

### Итоговый ожидаемый результат

Поле `Дата рождения` отображается, доступно для редактирования и предназначено для ввода даты.

### Постусловия

- Не применимо.

## TC-ACPD-014

**Название:** Граница даты рождения D−18 лет
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-030; ATOM-022; SRC-007; SRC-007.P02; OBL-035; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Известна текущая дата приложения `D`.
2. Открыта карточка заявки.

### Тестовые данные

- Дата `D-18 лет`.

### Шаги

1. Ввести в поле `Дата рождения` дату `D-18 лет`.

### Итоговый ожидаемый результат

Дата на границе `D-18 лет` соответствует ограничению, вычисляемому относительно текущей даты приложения `D`.

### Постусловия

- Не применимо.

## TC-ACPD-015

**Название:** Граница даты рождения D−100 лет
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-033; ATOM-024; SRC-007; SRC-007.P04; OBL-036; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Известна текущая дата приложения `D`.
2. Открыта карточка заявки.

### Тестовые данные

- Дата `D-100 лет`.

### Шаги

1. Ввести в поле `Дата рождения` дату `D-100 лет`.

### Итоговый ожидаемый результат

Дата на границе `D-100 лет` соответствует ограничению, вычисляемому относительно текущей даты приложения `D`.

### Постусловия

- Не применимо.

## TC-ACPD-016

**Название:** Недопустимая цифра в поле «Фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-006; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иванов2`.

### Шаги

1. Ввести тестовое значение в поле `Фамилия`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Фамилия`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-017

**Название:** Недопустимый спецсимвол в поле «Фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-007; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иванов@`.

### Шаги

1. Ввести тестовое значение в поле `Фамилия`.

### Итоговый ожидаемый результат

Значение со спецсимволом, отличным от дефиса, не признаётся допустимым для поля `Фамилия`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-018

**Название:** Недопустимая цифра в поле «Имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-013; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иван2`.

### Шаги

1. Ввести тестовое значение в поле `Имя`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Имя`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-019

**Название:** Недопустимый спецсимвол в поле «Имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-014; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иван@`.

### Шаги

1. Ввести тестовое значение в поле `Имя`.

### Итоговый ожидаемый результат

Значение со спецсимволом, отличным от дефиса, не признаётся допустимым для поля `Имя`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-020

**Название:** Недопустимая цифра в поле «Отчество»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-020; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иванович2`.

### Шаги

1. Ввести тестовое значение в поле `Отчество`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Отчество`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-021

**Название:** Недопустимый спецсимвол в поле «Отчество»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-021; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Иванович@`.

### Шаги

1. Ввести тестовое значение в поле `Отчество`.

### Итоговый ожидаемый результат

Значение со спецсимволом, отличным от дефиса, не признаётся допустимым для поля `Отчество`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-022

**Название:** Обязательность поля «Фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-003; ATOM-003; SRC-002; SRC-002.P02
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта заявка, для которой доступна попытка продолжения сценария.

### Тестовые данные

- Пустое значение `Фамилия`.

### Шаги

1. Оставить поле `Фамилия` пустым и попытаться продолжить сценарий.

### Итоговый ожидаемый результат

Поле `Фамилия` является обязательным; конкретная UI-реакция на незаполненное поле подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-023

**Название:** Обязательность поля «Имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-010; ATOM-008; SRC-003; SRC-003.P02
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта заявка, для которой доступна попытка продолжения сценария.

### Тестовые данные

- Пустое значение `Имя`.

### Шаги

1. Оставить поле `Имя` пустым и попытаться продолжить сценарий.

### Итоговый ожидаемый результат

Поле `Имя` является обязательным; конкретная UI-реакция на незаполненное поле подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-024

**Название:** Обязательность поля «Пол»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-026; ATOM-019; SRC-006; SRC-006.P01; DICT-001
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта заявка, для которой доступна попытка продолжения сценария.

### Тестовые данные

- Пустое значение `Пол`.

### Шаги

1. Не выбирать значение в поле `Пол` и попытаться продолжить сценарий.

### Итоговый ожидаемый результат

Поле `Пол` является обязательным; конкретная UI-реакция на отсутствие выбора подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-025

**Название:** Обязательность поля «Дата рождения»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-029; ATOM-021; SRC-007; SRC-007.P01
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта заявка, для которой доступна попытка продолжения сценария.

### Тестовые данные

- Пустое значение `Дата рождения`.

### Шаги

1. Оставить поле `Дата рождения` пустым и попытаться продолжить сценарий.

### Итоговый ожидаемый результат

Поле `Дата рождения` является обязательным; конкретная UI-реакция на незаполненное поле подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-026

**Название:** Дата рождения позже D−18 лет
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-031; ATOM-022; SRC-007; SRC-007.P02; OBL-037; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Известна текущая дата приложения `D`.
2. Открыта карточка заявки.

### Тестовые данные

- Дата `D-18 лет + 1 день`.

### Шаги

1. Ввести тестовую дату в поле `Дата рождения`.

### Итоговый ожидаемый результат

Дата позже `D-18 лет` не соответствует ограничению, вычисляемому относительно текущей даты приложения `D`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-027

**Название:** Будущая дата рождения
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-032; ATOM-023; SRC-007; SRC-007.P03; OBL-038; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Известна текущая дата приложения `D`.
2. Открыта карточка заявки.

### Тестовые данные

- Дата `D+1 день`.

### Шаги

1. Ввести тестовую дату в поле `Дата рождения`.

### Итоговый ожидаемый результат

Дата больше текущей даты приложения `D` не соответствует ограничению; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-028

**Название:** Дата рождения раньше D−100 лет
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-034; ATOM-024; SRC-007; SRC-007.P04; OBL-039; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Известна текущая дата приложения `D`.
2. Открыта карточка заявки.

### Тестовые данные

- Дата `D-100 лет - 1 день`.

### Шаги

1. Ввести тестовую дату в поле `Дата рождения`.

### Итоговый ожидаемый результат

Дата раньше `D-100 лет` не соответствует ограничению, вычисляемому относительно текущей даты приложения `D`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-029

**Название:** Варианты переключателя «Клиент менял ФИО»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-040; ATOM-026; SRC-008; SRC-008.P01

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть переключатель `Клиент менял ФИО`.

### Итоговый ожидаемый результат

Поле отображается как переключатель с вариантами `Да` и `Нет`.

### Постусловия

- Не применимо.

## TC-ACPD-030

**Название:** Значение по умолчанию переключателя «Клиент менял ФИО»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-041; ATOM-027; SRC-008; SRC-008.P02

### Предусловия

1. Доступно создание новой карточки заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть новую карточку заявки.

### Итоговый ожидаемый результат

Значение переключателя `Клиент менял ФИО` по умолчанию равно `Нет`.

### Постусловия

- Не применимо.

## TC-ACPD-031

**Название:** Отображение предыдущих ФИО при значении «Да»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-042; ATOM-028; SRC-009; SRC-009.P01; OBL-050; ATOM-033; SRC-010; SRC-010.P01; OBL-058; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Клиент менял ФИО=Да`.

### Шаги

1. Установить значение `Да` в переключателе `Клиент менял ФИО`.

### Итоговый ожидаемый результат

Отображаются поля `Предыдущая фамилия`, `Предыдущее имя` и `Предыдущее отчество`.

### Постусловия

- Не применимо.

## TC-ACPD-032

**Название:** Скрытие предыдущих ФИО при значении «Нет»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-043; ATOM-028; SRC-009; SRC-009.P01; OBL-051; ATOM-033; SRC-010; SRC-010.P01; OBL-059; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- `Клиент менял ФИО=Нет`.

### Шаги

1. Установить значение `Нет` в переключателе `Клиент менял ФИО`.

### Итоговый ожидаемый результат

Поля `Предыдущая фамилия`, `Предыдущее имя` и `Предыдущее отчество` не отображаются.

### Постусловия

- Не применимо.

## TC-ACPD-033

**Название:** Редактирование предыдущих ФИО при значении «Да»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-044; ATOM-029; SRC-009; SRC-009.P02; OBL-052; ATOM-034; SRC-010; SRC-010.P02; OBL-060; ATOM-039; SRC-011; SRC-011.P02

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Петрова`; `Анна`; `Ивановна`.

### Шаги

1. Ввести указанные значения в поля предыдущей фамилии, имени и отчества.

### Итоговый ожидаемый результат

Все три отображённые поля предыдущей ФИО принимают ввод.

### Постусловия

- Не применимо.

## TC-ACPD-034

**Название:** Ввод букв и дефиса в поле «Предыдущая фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-045; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Петрова-Сидорова`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущая фамилия`.

### Итоговый ожидаемый результат

Поле принимает значение, состоящее из текстовых символов и дефиса.

### Постусловия

- Не применимо.

## TC-ACPD-035

**Название:** Недопустимая цифра в поле «Предыдущая фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-046; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Петрова2`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущая фамилия`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Предыдущая фамилия`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-036

**Название:** Недопустимый спецсимвол в поле «Предыдущая фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-047; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Петрова@`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущая фамилия`.

### Итоговый ожидаемый результат

Значение со спецсимволом, отличным от дефиса, не признаётся допустимым для поля `Предыдущая фамилия`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-037

**Название:** Подсказки при вводе предыдущей фамилии
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-049; ATOM-032; SRC-009; SRC-009.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.
3. Интеграция подсказок доступна, а по значению `Петрова` имеются варианты.

### Тестовые данные

- `Петрова`.

### Шаги

1. Начать ввод тестового значения в поле `Предыдущая фамилия`.

### Итоговый ожидаемый результат

Для поля отображаются доступные пользователю подсказки; технический источник подсказок не подтверждается этим кейсом.

### Постусловия

- Не применимо.

## TC-ACPD-038

**Название:** Ввод букв и дефиса в поле «Предыдущее имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-053; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Анна-Мария`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущее имя`.

### Итоговый ожидаемый результат

Поле принимает значение, состоящее из текстовых символов и дефиса.

### Постусловия

- Не применимо.

## TC-ACPD-039

**Название:** Недопустимая цифра в поле «Предыдущее имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-054; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Анна2`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущее имя`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Предыдущее имя`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-040

**Название:** Недопустимый спецсимвол в поле «Предыдущее имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-055; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Анна@`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущее имя`.

### Итоговый ожидаемый результат

Значение со спецсимволом, отличным от дефиса, не признаётся допустимым для поля `Предыдущее имя`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-041

**Название:** Заполнение группы предыдущей ФИО при значении «Да»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-048; ATOM-031; SRC-009; SRC-009.P04; OBL-056; ATOM-036; SRC-010; SRC-010.P04; OBL-064; ATOM-041; SRC-011; SRC-011.P04
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта заявка, для которой доступна попытка продолжения сценария.

### Тестовые данные

- `Клиент менял ФИО=Да`; пустые поля предыдущей ФИО.

### Шаги

1. Установить значение `Да` в переключателе `Клиент менял ФИО`.
2. Оставить поля `Предыдущая фамилия`, `Предыдущее имя` и `Предыдущее отчество` пустыми.
3. Попытаться продолжить сценарий.

### Итоговый ожидаемый результат

При значении `Клиент менял ФИО=Да` должно быть заполнено хотя бы одно поле группы предыдущей ФИО; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-042

**Название:** Подсказки при вводе предыдущего имени
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-057; ATOM-037; SRC-010; SRC-010.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.
3. Интеграция подсказок доступна, а по значению `Анна` имеются варианты.

### Тестовые данные

- `Анна`.

### Шаги

1. Начать ввод тестового значения в поле `Предыдущее имя`.

### Итоговый ожидаемый результат

Для поля отображаются доступные пользователю подсказки; технический источник подсказок не подтверждается этим кейсом.

### Постусловия

- Не применимо.

## TC-ACPD-043

**Название:** Ввод букв и дефиса в поле «Предыдущее отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-061; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Ивановна-Петровна`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущее отчество`.

### Итоговый ожидаемый результат

Поле принимает значение, состоящее из текстовых символов и дефиса.

### Постусловия

- Не применимо.

## TC-ACPD-044

**Название:** Недопустимая цифра в поле «Предыдущее отчество»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-062; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Ивановна2`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущее отчество`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Предыдущее отчество`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-045

**Название:** Недопустимый спецсимвол в поле «Предыдущее отчество»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-063; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.

### Тестовые данные

- `Ивановна@`.

### Шаги

1. Ввести тестовое значение в поле `Предыдущее отчество`.

### Итоговый ожидаемый результат

Значение со спецсимволом, отличным от дефиса, не признаётся допустимым для поля `Предыдущее отчество`; конкретная UI-реакция подлежит калибровке.

### Постусловия

- Не применимо.

## TC-ACPD-046

**Название:** Подсказки при вводе предыдущего отчества
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-065; ATOM-042; SRC-011; SRC-011.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта карточка заявки.
2. Для переключателя `Клиент менял ФИО` установлено значение `Да`.
3. Интеграция подсказок доступна, а по значению `Ивановна` имеются варианты.

### Тестовые данные

- `Ивановна`.

### Шаги

1. Начать ввод тестового значения в поле `Предыдущее отчество`.

### Итоговый ожидаемый результат

Для поля отображаются доступные пользователю подсказки; технический источник подсказок не подтверждается этим кейсом.

### Постусловия

- Не применимо.

## TC-ACPD-047

**Название:** Необязательность поля «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v3
**Трассировка:** OBL-017; ATOM-013; SRC-004; SRC-004.P02

### Предусловия

1. Открыта заявка, для которой доступна попытка продолжения сценария.

### Тестовые данные

- Пустое значение `Отчество`; заполненные обязательные поля заявки.

### Шаги

1. Оставить поле `Отчество` пустым и продолжить сценарий с заполненными обязательными полями.

### Итоговый ожидаемый результат

Отсутствие значения в поле `Отчество` само по себе не нарушает требование обязательности.

### Постусловия

- Не применимо.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
