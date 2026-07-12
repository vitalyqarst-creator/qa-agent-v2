# Codex exec prepared-standard writer stage contract

Instruction-loading scenario: `writer.session_initial_draft`.
Run `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` and verify it matches the runner-selected files below.
Read every selected standard instruction file before making domain decisions.
The prepared package is a compact source-backed transport, not a fast semantic profile.
Use the verified inline projection as primary evidence. Do not repeat source discovery or broad document analysis.
A registered full source may be inspected only for a named OBL/ATOM whose inline evidence is insufficient; record the source path, locator and reason in the final summary.
Angle-bracket test-data placeholders are forbidden. Bind concrete values or a named reproducible fixture with explicit selection/setup conditions; return blocked if neither is source-safe.
Do not use generated test cases, previous cycles or canary artifacts as requirement evidence.
Do not write under any production test-cases directory.
Write the complete unsigned draft only to `fts/AutoFin/work/review-cycles/personal-data-character-restrictions-shadow-v3-20260712/attempts/writer-r1/attempt-001/stage-output/draft.md`.

## Standard instruction files
- `AGENTS.md`
- `skills/README.md`
- `references/agent/session-based-review-cycle-format.md`
- `references/agent/codex-sdk-orchestration-format.md`
- `skills/ft-test-case-writer/SKILL.md`
- `references/agent/writer-runtime-workflow.md`
- `references/agent/writer-runtime-contract.md`
- `references/agent/negative-ui-calibration-policy.md`
- `references/qa/test-case-runtime-format.md`
- `references/qa/coverage-runtime-checklist.md`
- `references/qa/traceability-rules.md`
- `references/agent/runtime-quality-rule-cards.md`
- `references/agent/writer-process-workflow.md`
- `references/agent/workflow-state-format.md`
- `references/agent/session-log-format.md`
- `references/agent/agent-decision-log-format.md`
- `references/agent/writer-handoff-format.md`

<!-- PREPARED-STANDARD-WRITER-PAYLOAD:BEGIN -->
## Verified prepared-standard metadata

```json
{
  "package_version": 5,
  "package_id": "personal-data-character-restrictions-v3",
  "ft_slug": "AutoFin",
  "scope_slug": "4.3-prepared-shadow-personal-data-character-restrictions",
  "section_id": "4.3",
  "execution_profile": "standard-required",
  "unsupported_dimensions": [
    "equivalence-partitioning",
    "evidence-qualified-ui-calibration",
    "input-boundaries",
    "negative-oracle"
  ],
  "fallback_policy": "targeted-only",
  "source_registry": [
    {
      "path": "fts/AutoFin/source/FT4AutoFinFinal.docx",
      "role": "source-of-truth",
      "locator": "pinned by source-selection.md",
      "sha256": "c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b"
    },
    {
      "path": "fts/AutoFin/source/FT4AutoFinFinal.xhtml",
      "role": "machine-readable",
      "locator": "pinned by source-selection.md",
      "sha256": "cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66"
    },
    {
      "path": "fts/AutoFin/source/FT4AutoFinFinal.pdf",
      "role": "structural-cross-check",
      "locator": "pinned by source-selection.md",
      "sha256": "8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58"
    }
  ]
}
```

## Selected source evidence

# Prepared Source Evidence

- package_id: `personal-data-character-restrictions-v3`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/personal-data-character-restrictions-shadow-v3-20260712/prepared-input/.personal-data-character-restrictions-v3.compiled-evidence.md`
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
  "digest": "3bf16c406c98f3b3dc1c8d3be92097935db15546459f26baef827b38fbaf380a",
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
  "package_id": "personal-data-character-restrictions-v3",
  "package_version": 5
}
```

## Draft seed template (not an existing output file)

Create the declared output as the first meaningful artifact. Replace every seed sentinel.

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
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-003; ATOM-003

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
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-004; ATOM-004

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
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-007; ATOM-007

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
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-008; ATOM-008

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
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-011; ATOM-011

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
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-012; ATOM-012

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
<!-- PREPARED-STANDARD-WRITER-PAYLOAD:END -->

Exit only after the complete draft is written. A chat response without the file is a failed stage.
