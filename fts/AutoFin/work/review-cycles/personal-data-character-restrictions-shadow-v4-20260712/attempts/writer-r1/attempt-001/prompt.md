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
  "package_id": "personal-data-character-restrictions-v4",
  "ft_slug": "AutoFin",
  "scope_slug": "4.3-prepared-shadow-personal-data-character-restrictions",
  "section_id": "4.3",
  "execution_profile": "standard-required",
  "context_profile": "character-restriction-calibration",
  "unsupported_dimensions": [
    "equivalence-partitioning",
    "evidence-qualified-ui-calibration",
    "input-boundaries",
    "negative-oracle"
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

- package_id: `personal-data-character-restrictions-v4`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/personal-data-character-restrictions-shadow-v4-20260712/prepared-input/.personal-data-character-restrictions-v4.compiled-evidence.md`
- source_sha256: `739aa973be22ac37d94336d71697b958ad25ba1b025ded3188fdda8e3880405a`
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

- obligation: OBL-001 | property=SRC-002.P06 | source=`BSR 48`; XHTML row 57 | required=`Фамилия` принимает текстовое значение `Иванов`. | planned=TC-PDCR-001 | status=covered

- atom: ATOM-001 | source=`SRC-002`; XHTML row 57; DOCX table 6 row 4; BSR 48 | statement=Поле `Фамилия` допускает ввод текстовых символов. | coverage=covered

- plan: PLAN-001 | check=Ввести `Иванов` в поле `Фамилия`. | expected=Значение `Иванов` принимается полем `Фамилия`. | planned=TC-PDCR-001 | status=covered

## OBL-002

- obligation: OBL-002 | property=SRC-002.P06 | source=`BSR 48`; XHTML row 57 | required=`Фамилия` принимает текстовое значение `Иванов-Петров` с дефисом. | planned=TC-PDCR-002 | status=covered

- atom: ATOM-002 | source=`SRC-002`; XHTML row 57; DOCX table 6 row 4; BSR 48 | statement=Поле `Фамилия` допускает специальный символ `-` в текстовом значении. | coverage=covered

- plan: PLAN-002 | check=Ввести `Иванов-Петров` в поле `Фамилия`. | expected=Значение с дефисом принимается полем `Фамилия`. | planned=TC-PDCR-002 | status=covered

## OBL-003

- obligation: OBL-003 | property=SRC-002.P06 | source=BSR 48`; `SO-NEG-001 | required=Цифра в значении `Иванов2` не принимается как допустимое значение `Фамилия`. | planned=TC-PDCR-003 | status=covered

- atom: ATOM-003 | source=`SRC-002`; XHTML row 57; DOCX table 6 row 4; BSR 48 | statement=Поле `Фамилия` не допускает цифры. | coverage=covered_with_ui_calibration

- plan: PLAN-003 | check=Ввести `Иванов2` в поле `Фамилия` и зафиксировать фактический механизм отклонения. | expected=Значение с цифрой не признается допустимым; сообщение, фильтрация, подсветка или блокировка не предопределяются. | planned=TC-PDCR-003 | status=covered_with_ui_calibration

## OBL-004

- obligation: OBL-004 | property=SRC-002.P06 | source=BSR 48`; `SO-NEG-002 | required=Символ `@` в значении `Иванов@` не принимается как допустимое значение `Фамилия`. | planned=TC-PDCR-004 | status=covered

- atom: ATOM-004 | source=`SRC-002`; XHTML row 57; DOCX table 6 row 4; BSR 48 | statement=Поле `Фамилия` не допускает специальные символы, кроме `-`. | coverage=covered_with_ui_calibration

- plan: PLAN-004 | check=Ввести `Иванов@` в поле `Фамилия` и зафиксировать фактический механизм отклонения. | expected=Значение с `@` не признается допустимым; точная UI-реакция не предопределяется. | planned=TC-PDCR-004 | status=covered_with_ui_calibration

## OBL-005

- obligation: OBL-005 | property=SRC-003.P06 | source=`BSR 51`; XHTML row 58 | required=`Имя` принимает текстовое значение `Иван`. | planned=TC-PDCR-005 | status=covered

- atom: ATOM-005 | source=`SRC-003`; XHTML row 58; DOCX table 6 row 5; BSR 51 | statement=Поле `Имя` допускает ввод текстовых символов. | coverage=covered

- plan: PLAN-005 | check=Ввести `Иван` в поле `Имя`. | expected=Значение `Иван` принимается полем `Имя`. | planned=TC-PDCR-005 | status=covered

## OBL-006

- obligation: OBL-006 | property=SRC-003.P06 | source=`BSR 51`; XHTML row 58 | required=`Имя` принимает текстовое значение `Анна-Мария` с дефисом. | planned=TC-PDCR-006 | status=covered

- atom: ATOM-006 | source=`SRC-003`; XHTML row 58; DOCX table 6 row 5; BSR 51 | statement=Поле `Имя` допускает специальный символ `-` в текстовом значении. | coverage=covered

- plan: PLAN-006 | check=Ввести `Анна-Мария` в поле `Имя`. | expected=Значение с дефисом принимается полем `Имя`. | planned=TC-PDCR-006 | status=covered

## OBL-007

- obligation: OBL-007 | property=SRC-003.P06 | source=BSR 51`; `SO-NEG-003 | required=Цифра в значении `Иван2` не принимается как допустимое значение `Имя`. | planned=TC-PDCR-007 | status=covered

- atom: ATOM-007 | source=`SRC-003`; XHTML row 58; DOCX table 6 row 5; BSR 51 | statement=Поле `Имя` не допускает цифры. | coverage=covered_with_ui_calibration

- plan: PLAN-007 | check=Ввести `Иван2` в поле `Имя` и зафиксировать фактический механизм отклонения. | expected=Значение с цифрой не признается допустимым; точная UI-реакция не предопределяется. | planned=TC-PDCR-007 | status=covered_with_ui_calibration

## OBL-008

- obligation: OBL-008 | property=SRC-003.P06 | source=BSR 51`; `SO-NEG-004 | required=Символ `@` в значении `Иван@` не принимается как допустимое значение `Имя`. | planned=TC-PDCR-008 | status=covered

- atom: ATOM-008 | source=`SRC-003`; XHTML row 58; DOCX table 6 row 5; BSR 51 | statement=Поле `Имя` не допускает специальные символы, кроме `-`. | coverage=covered_with_ui_calibration

- plan: PLAN-008 | check=Ввести `Иван@` в поле `Имя` и зафиксировать фактический механизм отклонения. | expected=Значение с `@` не признается допустимым; точная UI-реакция не предопределяется. | planned=TC-PDCR-008 | status=covered_with_ui_calibration

## OBL-009

- obligation: OBL-009 | property=SRC-004.P06 | source=`BSR 54`; XHTML row 59 | required=`Отчество` принимает текстовое значение `Иванович`. | planned=TC-PDCR-009 | status=covered

- atom: ATOM-009 | source=`SRC-004`; XHTML row 59; DOCX table 6 row 6; BSR 54 | statement=Поле `Отчество` допускает ввод текстовых символов. | coverage=covered

- plan: PLAN-009 | check=Ввести `Иванович` в поле `Отчество`. | expected=Значение `Иванович` принимается полем `Отчество`. | planned=TC-PDCR-009 | status=covered

## OBL-010

- obligation: OBL-010 | property=SRC-004.P06 | source=`BSR 54`; XHTML row 59 | required=`Отчество` принимает текстовое значение `Иванович-Петрович` с дефисом. | planned=TC-PDCR-010 | status=covered

- atom: ATOM-010 | source=`SRC-004`; XHTML row 59; DOCX table 6 row 6; BSR 54 | statement=Поле `Отчество` допускает специальный символ `-` в текстовом значении. | coverage=covered

- plan: PLAN-010 | check=Ввести `Иванович-Петрович` в поле `Отчество`. | expected=Значение с дефисом принимается полем `Отчество`. | planned=TC-PDCR-010 | status=covered

## OBL-011

- obligation: OBL-011 | property=SRC-004.P06 | source=BSR 54`; `SO-NEG-005 | required=Цифра в значении `Иванович2` не принимается как допустимое значение `Отчество`. | planned=TC-PDCR-011 | status=covered

- atom: ATOM-011 | source=`SRC-004`; XHTML row 59; DOCX table 6 row 6; BSR 54 | statement=Поле `Отчество` не допускает цифры. | coverage=covered_with_ui_calibration

- plan: PLAN-011 | check=Ввести `Иванович2` в поле `Отчество` и зафиксировать фактический механизм отклонения. | expected=Значение с цифрой не признается допустимым; точная UI-реакция не предопределяется. | planned=TC-PDCR-011 | status=covered_with_ui_calibration

## OBL-012

- obligation: OBL-012 | property=SRC-004.P06 | source=BSR 54`; `SO-NEG-006 | required=Символ `@` в значении `Иванович@` не принимается как допустимое значение `Отчество`. | planned=TC-PDCR-012 | status=covered

- atom: ATOM-012 | source=`SRC-004`; XHTML row 59; DOCX table 6 row 6; BSR 54 | statement=Поле `Отчество` не допускает специальные символы, кроме `-`. | coverage=covered_with_ui_calibration

- plan: PLAN-012 | check=Ввести `Иванович@` в поле `Отчество` и зафиксировать фактический механизм отклонения. | expected=Значение с `@` не признается допустимым; точная UI-реакция не предопределяется. | planned=TC-PDCR-012 | status=covered_with_ui_calibration

## GAP-001

source_refs: SRC-002..SRC-004; ATOM-003; ATOM-004; ATOM-007; ATOM-008; ATOM-011; ATOM-012; OBL-003; OBL-004; OBL-007; OBL-008; OBL-011; OBL-012
Table 4; `BSR 48, 51, 54`.
Сохранить как coverage gap.

## Atomic obligations

```json
{
  "coverage_gaps": [
    {
      "blocking": false,
      "gap_id": "GAP-001",
      "handling": "Сохранить как coverage gap.",
      "problem": "Table 4; `BSR 48, 51, 54`.",
      "source_refs": [
        "SRC-002..SRC-004",
        "ATOM-003",
        "ATOM-004",
        "ATOM-007",
        "ATOM-008",
        "ATOM-011",
        "ATOM-012",
        "OBL-003",
        "OBL-004",
        "OBL-007",
        "OBL-008",
        "OBL-011",
        "OBL-012"
      ]
    }
  ],
  "digest": "a614fd649c397a1c0d43354426c8751a0a06f6f0900d3ac9c35585aec3a85c8e",
  "obligations": [
    {
      "atom_id": "ATOM-001",
      "atomic_statement": "Поле `Фамилия` допускает ввод текстовых символов.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-001",
      "observable_oracle": "`Фамилия` принимает текстовое значение `Иванов`.",
      "planned_test_case_id": "TC-PDCR-001",
      "source_refs": [
        "SRC-002",
        "SRC-002.P06"
      ],
      "test_intent": "Ввести `Иванов` в поле `Фамилия`."
    },
    {
      "atom_id": "ATOM-002",
      "atomic_statement": "Поле `Фамилия` допускает специальный символ `-` в текстовом значении.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-002",
      "observable_oracle": "`Фамилия` принимает текстовое значение `Иванов-Петров` с дефисом.",
      "planned_test_case_id": "TC-PDCR-002",
      "source_refs": [
        "SRC-002",
        "SRC-002.P06"
      ],
      "test_intent": "Ввести `Иванов-Петров` в поле `Фамилия`."
    },
    {
      "atom_id": "ATOM-003",
      "atomic_statement": "Поле `Фамилия` не допускает цифры.",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.",
      "obligation_id": "OBL-003",
      "observable_oracle": "Цифра в значении `Иванов2` не принимается как допустимое значение `Фамилия`.",
      "planned_test_case_id": "TC-PDCR-003",
      "source_refs": [
        "SRC-002",
        "SRC-002.P06"
      ],
      "test_intent": "Ввести `Иванов2` в поле `Фамилия` и зафиксировать фактический механизм отклонения."
    },
    {
      "atom_id": "ATOM-004",
      "atomic_statement": "Поле `Фамилия` не допускает специальные символы, кроме `-`.",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.",
      "obligation_id": "OBL-004",
      "observable_oracle": "Символ `@` в значении `Иванов@` не принимается как допустимое значение `Фамилия`.",
      "planned_test_case_id": "TC-PDCR-004",
      "source_refs": [
        "SRC-002",
        "SRC-002.P06"
      ],
      "test_intent": "Ввести `Иванов@` в поле `Фамилия` и зафиксировать фактический механизм отклонения."
    },
    {
      "atom_id": "ATOM-005",
      "atomic_statement": "Поле `Имя` допускает ввод текстовых символов.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-005",
      "observable_oracle": "`Имя` принимает текстовое значение `Иван`.",
      "planned_test_case_id": "TC-PDCR-005",
      "source_refs": [
        "SRC-003",
        "SRC-003.P06"
      ],
      "test_intent": "Ввести `Иван` в поле `Имя`."
    },
    {
      "atom_id": "ATOM-006",
      "atomic_statement": "Поле `Имя` допускает специальный символ `-` в текстовом значении.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-006",
      "observable_oracle": "`Имя` принимает текстовое значение `Анна-Мария` с дефисом.",
      "planned_test_case_id": "TC-PDCR-006",
      "source_refs": [
        "SRC-003",
        "SRC-003.P06"
      ],
      "test_intent": "Ввести `Анна-Мария` в поле `Имя`."
    },
    {
      "atom_id": "ATOM-007",
      "atomic_statement": "Поле `Имя` не допускает цифры.",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.",
      "obligation_id": "OBL-007",
      "observable_oracle": "Цифра в значении `Иван2` не принимается как допустимое значение `Имя`.",
      "planned_test_case_id": "TC-PDCR-007",
      "source_refs": [
        "SRC-003",
        "SRC-003.P06"
      ],
      "test_intent": "Ввести `Иван2` в поле `Имя` и зафиксировать фактический механизм отклонения."
    },
    {
      "atom_id": "ATOM-008",
      "atomic_statement": "Поле `Имя` не допускает специальные символы, кроме `-`.",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.",
      "obligation_id": "OBL-008",
      "observable_oracle": "Символ `@` в значении `Иван@` не принимается как допустимое значение `Имя`.",
      "planned_test_case_id": "TC-PDCR-008",
      "source_refs": [
        "SRC-003",
        "SRC-003.P06"
      ],
      "test_intent": "Ввести `Иван@` в поле `Имя` и зафиксировать фактический механизм отклонения."
    },
    {
      "atom_id": "ATOM-009",
      "atomic_statement": "Поле `Отчество` допускает ввод текстовых символов.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-009",
      "observable_oracle": "`Отчество` принимает текстовое значение `Иванович`.",
      "planned_test_case_id": "TC-PDCR-009",
      "source_refs": [
        "SRC-004",
        "SRC-004.P06"
      ],
      "test_intent": "Ввести `Иванович` в поле `Отчество`."
    },
    {
      "atom_id": "ATOM-010",
      "atomic_statement": "Поле `Отчество` допускает специальный символ `-` в текстовом значении.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-010",
      "observable_oracle": "`Отчество` принимает текстовое значение `Иванович-Петрович` с дефисом.",
      "planned_test_case_id": "TC-PDCR-010",
      "source_refs": [
        "SRC-004",
        "SRC-004.P06"
      ],
      "test_intent": "Ввести `Иванович-Петрович` в поле `Отчество`."
    },
    {
      "atom_id": "ATOM-011",
      "atomic_statement": "Поле `Отчество` не допускает цифры.",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.",
      "obligation_id": "OBL-011",
      "observable_oracle": "Цифра в значении `Иванович2` не принимается как допустимое значение `Отчество`.",
      "planned_test_case_id": "TC-PDCR-011",
      "source_refs": [
        "SRC-004",
        "SRC-004.P06"
      ],
      "test_intent": "Ввести `Иванович2` в поле `Отчество` и зафиксировать фактический механизм отклонения."
    },
    {
      "atom_id": "ATOM-012",
      "atomic_statement": "Поле `Отчество` не допускает специальные символы, кроме `-`.",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts. Non-blocking constraints: GAP-001.",
      "obligation_id": "OBL-012",
      "observable_oracle": "Символ `@` в значении `Иванович@` не принимается как допустимое значение `Отчество`.",
      "planned_test_case_id": "TC-PDCR-012",
      "source_refs": [
        "SRC-004",
        "SRC-004.P06"
      ],
      "test_intent": "Ввести `Иванович@` в поле `Отчество` и зафиксировать фактический механизм отклонения."
    }
  ],
  "package_id": "personal-data-character-restrictions-v4",
  "package_version": 5
}
```

## Draft seed template (not an existing output file)

Return a complete draft based on this template; the runner writes it after validating the JSON contract.
Do not copy seed sentinels or placeholders into draft_markdown.

```markdown
# Тест-кейсы

<!-- PREPARED-DRAFT-SEED: replace all [SEED:*] values before completion -->

## TC-PDCR-001

**Название:** [SEED:title:ATOM-001]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-001; ATOM-001

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Фамилия` принимает текстовое значение `Иванов`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-002

**Название:** [SEED:title:ATOM-002]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-002; ATOM-002

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Фамилия` принимает текстовое значение `Иванов-Петров` с дефисом.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-003

**Название:** [SEED:title:ATOM-003]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-003; ATOM-003
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

[SEED:observable oracle] Цифра в значении `Иванов2` не принимается как допустимое значение `Фамилия`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-004

**Название:** [SEED:title:ATOM-004]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-004; ATOM-004
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

[SEED:observable oracle] Символ `@` в значении `Иванов@` не принимается как допустимое значение `Фамилия`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-005

**Название:** [SEED:title:ATOM-005]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-005; ATOM-005

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Имя` принимает текстовое значение `Иван`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-006

**Название:** [SEED:title:ATOM-006]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-006; ATOM-006

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Имя` принимает текстовое значение `Анна-Мария` с дефисом.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-007

**Название:** [SEED:title:ATOM-007]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-007; ATOM-007
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

[SEED:observable oracle] Цифра в значении `Иван2` не принимается как допустимое значение `Имя`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-008

**Название:** [SEED:title:ATOM-008]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-008; ATOM-008
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

[SEED:observable oracle] Символ `@` в значении `Иван@` не принимается как допустимое значение `Имя`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-009

**Название:** [SEED:title:ATOM-009]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-009; ATOM-009

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Отчество` принимает текстовое значение `Иванович`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-010

**Название:** [SEED:title:ATOM-010]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-010; ATOM-010

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Отчество` принимает текстовое значение `Иванович-Петрович` с дефисом.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-011

**Название:** [SEED:title:ATOM-011]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-011; ATOM-011
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

[SEED:observable oracle] Цифра в значении `Иванович2` не принимается как допустимое значение `Отчество`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PDCR-012

**Название:** [SEED:title:ATOM-012]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-012; ATOM-012
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

[SEED:observable oracle] Символ `@` в значении `Иванович@` не принимается как допустимое значение `Отчество`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```
<!-- PREPARED-STAGE-PAYLOAD:END -->

Return exactly one JSON object and no commentary outside it.
Use status=draft-ready with a complete draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one blocking reason.
