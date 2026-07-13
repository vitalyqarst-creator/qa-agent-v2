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
  "package_id": "personal-data-character-restrictions-v5",
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
  "reviewed_draft_sha256": "7da0cdb53f7fabc1eb7c17f2e4db449a0cf6424450930afc05eebd58ccbfc20c"
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

- package_id: `personal-data-character-restrictions-v5`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/personal-data-character-restrictions-shadow-v5-20260713/prepared-input/.personal-data-character-restrictions-v5.compiled-evidence.md`
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
  "digest": "f111f8de6a0b170fb30d6a3c871c3b43b2ef5d951b1a68018ad71d7fdd9a221a",
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
  "package_id": "personal-data-character-restrictions-v5",
  "package_version": 5
}
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
    "test_case_count": 12,
    "testable_obligations": 12,
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
      "OBL-012"
    ]
  },
  {
    "gate": "semantic-overlap",
    "passed": true,
    "validator": "semantic-overlap-diagnostic-v1",
    "findings_count": 0,
    "test_case_count": 12
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
    "test_case_count": 12
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
  "test_case_count": 12,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\personal-data-character-restrictions-shadow-v5-20260713\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle

```json
{
  "version": 1,
  "context_profile": "character-restriction-calibration",
  "items": [
    {
      "obligation_id": "OBL-003",
      "atom_id": "ATOM-003",
      "test_case_id": "TC-PDCR-003",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "status": "awaiting-ui-calibration",
      "evidence_status": "not-collected",
      "regression_ready": false,
      "required_transition": "ui-evidence -> oracle-resolution -> reviewer-sign-off"
    },
    {
      "obligation_id": "OBL-004",
      "atom_id": "ATOM-004",
      "test_case_id": "TC-PDCR-004",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "status": "awaiting-ui-calibration",
      "evidence_status": "not-collected",
      "regression_ready": false,
      "required_transition": "ui-evidence -> oracle-resolution -> reviewer-sign-off"
    },
    {
      "obligation_id": "OBL-007",
      "atom_id": "ATOM-007",
      "test_case_id": "TC-PDCR-007",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "status": "awaiting-ui-calibration",
      "evidence_status": "not-collected",
      "regression_ready": false,
      "required_transition": "ui-evidence -> oracle-resolution -> reviewer-sign-off"
    },
    {
      "obligation_id": "OBL-008",
      "atom_id": "ATOM-008",
      "test_case_id": "TC-PDCR-008",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "status": "awaiting-ui-calibration",
      "evidence_status": "not-collected",
      "regression_ready": false,
      "required_transition": "ui-evidence -> oracle-resolution -> reviewer-sign-off"
    },
    {
      "obligation_id": "OBL-011",
      "atom_id": "ATOM-011",
      "test_case_id": "TC-PDCR-011",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "status": "awaiting-ui-calibration",
      "evidence_status": "not-collected",
      "regression_ready": false,
      "required_transition": "ui-evidence -> oracle-resolution -> reviewer-sign-off"
    },
    {
      "obligation_id": "OBL-012",
      "atom_id": "ATOM-012",
      "test_case_id": "TC-PDCR-012",
      "constraint_gap_ids": [
        "GAP-001"
      ],
      "status": "awaiting-ui-calibration",
      "evidence_status": "not-collected",
      "regression_ready": false,
      "required_transition": "ui-evidence -> oracle-resolution -> reviewer-sign-off"
    }
  ],
  "open_count": 6,
  "resolved_count": 0
}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-PDCR-001

**Название:** Поле «Фамилия» принимает текстовое значение «Иванов»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-001; ATOM-001; SRC-002; SRC-002.P06

### Предусловия

1. Открыт интерфейс, в котором поле «Фамилия» доступно для ввода.

### Тестовые данные

- `Иванов`

### Шаги

1. Ввести `Иванов` в поле «Фамилия».

### Итоговый ожидаемый результат

Поле «Фамилия» принимает текстовое значение `Иванов`.

### Постусловия

- Не применимо: кейс проверяет ввод значения в поле.

## TC-PDCR-002

**Название:** Поле «Фамилия» принимает значение с дефисом «Иванов-Петров»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-002; ATOM-002; SRC-002; SRC-002.P06

### Предусловия

1. Открыт интерфейс, в котором поле «Фамилия» доступно для ввода.

### Тестовые данные

- `Иванов-Петров`

### Шаги

1. Ввести `Иванов-Петров` в поле «Фамилия».

### Итоговый ожидаемый результат

Поле «Фамилия» принимает текстовое значение `Иванов-Петров` с дефисом.

### Постусловия

- Не применимо: кейс проверяет ввод значения в поле.

## TC-PDCR-003

**Название:** Поле «Фамилия» не принимает значение с цифрой «Иванов2»
**Тип:** негативный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-003; ATOM-003; SRC-002; SRC-002.P06
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыт интерфейс, в котором поле «Фамилия» доступно для ввода.

### Тестовые данные

- `Иванов2`

### Шаги

1. Ввести `Иванов2` в поле «Фамилия» и зафиксировать фактический механизм отклонения.

### Итоговый ожидаемый результат

Цифра в значении `Иванов2` не принимается как допустимое значение поля «Фамилия». Конкретный механизм отклонения требует UI-калибровки.

### Постусловия

- Не применимо: кейс проверяет недопустимость вводимого значения.

## TC-PDCR-004

**Название:** Поле «Фамилия» не принимает значение с символом «@»
**Тип:** негативный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-004; ATOM-004; SRC-002; SRC-002.P06
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыт интерфейс, в котором поле «Фамилия» доступно для ввода.

### Тестовые данные

- `Иванов@`

### Шаги

1. Ввести `Иванов@` в поле «Фамилия» и зафиксировать фактический механизм отклонения.

### Итоговый ожидаемый результат

Символ `@` в значении `Иванов@` не принимается как допустимое значение поля «Фамилия». Конкретный механизм отклонения требует UI-калибровки.

### Постусловия

- Не применимо: кейс проверяет недопустимость вводимого значения.

## TC-PDCR-005

**Название:** Поле «Имя» принимает текстовое значение «Иван»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-005; ATOM-005; SRC-003; SRC-003.P06

### Предусловия

1. Открыт интерфейс, в котором поле «Имя» доступно для ввода.

### Тестовые данные

- `Иван`

### Шаги

1. Ввести `Иван` в поле «Имя».

### Итоговый ожидаемый результат

Поле «Имя» принимает текстовое значение `Иван`.

### Постусловия

- Не применимо: кейс проверяет ввод значения в поле.

## TC-PDCR-006

**Название:** Поле «Имя» принимает значение с дефисом «Анна-Мария»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-006; ATOM-006; SRC-003; SRC-003.P06

### Предусловия

1. Открыт интерфейс, в котором поле «Имя» доступно для ввода.

### Тестовые данные

- `Анна-Мария`

### Шаги

1. Ввести `Анна-Мария` в поле «Имя».

### Итоговый ожидаемый результат

Поле «Имя» принимает текстовое значение `Анна-Мария` с дефисом.

### Постусловия

- Не применимо: кейс проверяет ввод значения в поле.

## TC-PDCR-007

**Название:** Поле «Имя» не принимает значение с цифрой «Иван2»
**Тип:** негативный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-007; ATOM-007; SRC-003; SRC-003.P06
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыт интерфейс, в котором поле «Имя» доступно для ввода.

### Тестовые данные

- `Иван2`

### Шаги

1. Ввести `Иван2` в поле «Имя» и зафиксировать фактический механизм отклонения.

### Итоговый ожидаемый результат

Цифра в значении `Иван2` не принимается как допустимое значение поля «Имя». Конкретный механизм отклонения требует UI-калибровки.

### Постусловия

- Не применимо: кейс проверяет недопустимость вводимого значения.

## TC-PDCR-008

**Название:** Поле «Имя» не принимает значение с символом «@»
**Тип:** негативный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-008; ATOM-008; SRC-003; SRC-003.P06
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыт интерфейс, в котором поле «Имя» доступно для ввода.

### Тестовые данные

- `Иван@`

### Шаги

1. Ввести `Иван@` в поле «Имя» и зафиксировать фактический механизм отклонения.

### Итоговый ожидаемый результат

Символ `@` в значении `Иван@` не принимается как допустимое значение поля «Имя». Конкретный механизм отклонения требует UI-калибровки.

### Постусловия

- Не применимо: кейс проверяет недопустимость вводимого значения.

## TC-PDCR-009

**Название:** Поле «Отчество» принимает текстовое значение «Иванович»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-009; ATOM-009; SRC-004; SRC-004.P06

### Предусловия

1. Открыт интерфейс, в котором поле «Отчество» доступно для ввода.

### Тестовые данные

- `Иванович`

### Шаги

1. Ввести `Иванович` в поле «Отчество».

### Итоговый ожидаемый результат

Поле «Отчество» принимает текстовое значение `Иванович`.

### Постусловия

- Не применимо: кейс проверяет ввод значения в поле.

## TC-PDCR-010

**Название:** Поле «Отчество» принимает значение с дефисом «Иванович-Петрович»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-010; ATOM-010; SRC-004; SRC-004.P06

### Предусловия

1. Открыт интерфейс, в котором поле «Отчество» доступно для ввода.

### Тестовые данные

- `Иванович-Петрович`

### Шаги

1. Ввести `Иванович-Петрович` в поле «Отчество».

### Итоговый ожидаемый результат

Поле «Отчество» принимает текстовое значение `Иванович-Петрович` с дефисом.

### Постусловия

- Не применимо: кейс проверяет ввод значения в поле.

## TC-PDCR-011

**Название:** Поле «Отчество» не принимает значение с цифрой «Иванович2»
**Тип:** негативный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-011; ATOM-011; SRC-004; SRC-004.P06
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыт интерфейс, в котором поле «Отчество» доступно для ввода.

### Тестовые данные

- `Иванович2`

### Шаги

1. Ввести `Иванович2` в поле «Отчество» и зафиксировать фактический механизм отклонения.

### Итоговый ожидаемый результат

Цифра в значении `Иванович2` не принимается как допустимое значение поля «Отчество». Конкретный механизм отклонения требует UI-калибровки.

### Постусловия

- Не применимо: кейс проверяет недопустимость вводимого значения.

## TC-PDCR-012

**Название:** Поле «Отчество» не принимает значение с символом «@»
**Тип:** негативный
**Приоритет:** средний
**package_id:** personal-data-character-restrictions-v5
**Трассировка:** OBL-012; ATOM-012; SRC-004; SRC-004.P06
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыт интерфейс, в котором поле «Отчество» доступно для ввода.

### Тестовые данные

- `Иванович@`

### Шаги

1. Ввести `Иванович@` в поле «Отчество» и зафиксировать фактический механизм отклонения.

### Итоговый ожидаемый результат

Символ `@` в значении `Иванович@` не принимается как допустимое значение поля «Отчество». Конкретный механизм отклонения требует UI-калибровки.

### Постусловия

- Не применимо: кейс проверяет недопустимость вводимого значения.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
