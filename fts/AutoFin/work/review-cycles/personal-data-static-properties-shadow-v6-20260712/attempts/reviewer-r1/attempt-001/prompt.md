# Codex exec prepared reviewer fast path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

```json
{
  "package_version": 5,
  "package_id": "personal-data-static-properties-v6",
  "ft_slug": "AutoFin",
  "scope_slug": "4.3-prepared-shadow-personal-data-static-properties",
  "section_id": "4.3",
  "execution_profile": "simple-field-property",
  "unsupported_dimensions": [],
  "reviewed_draft_sha256": "1b5ba42c3d8c093450cce7cdba597325e549de50517f2c68b9150a530d67744f"
}
```

# Prepared Reviewer Runtime Profile

This is a technical execution profile inside the `ft-test-case-reviewer` phase. It introduces no new QA policy. The canonical full reviewer rubric remains authoritative for standard review; this projection contains only the checks applicable to an eligible immutable `simple-field-property` prepared package.

## Eligibility

Continue only when the embedded payload confirms:

- package version `5`;
- `execution_profile = simple-field-property`;
- empty `unsupported_dimensions`;
- an immutable draft hash;
- scope-local evidence and atomic obligations;
- passed structure, seed, obligation and writer evidence-access gates.

Legacy/unclassified, table-parity, numeric-boundary, integration/persistence, dependency/state and other unsupported packages return `route-to-standard-reviewer`. Do not open full project instructions or sources to bypass eligibility.

## Review Procedure

1. Use only the verified inline payload. Do not reread the full reviewer skill, instruction manifest, package files, references, prior cycles, production test cases or full sources.
2. Review every supplied obligation exactly once, preserving its exact `obligation_id -> atom_id` pair, and bind the result to the supplied draft SHA-256.
3. For each `coverage_status = testable`, verify that linked `TC-*` steps and final expected result exercise the obligation condition and its concrete observable oracle.
4. For each `gap`, `unclear` or `not-applicable` obligation, verify that the draft does not claim executable coverage or invent the missing mechanism.
5. Reject invented screens, fields, literals, dictionaries, messages, statuses, UI reactions, API/DB effects, persistence or internal state.
6. Reject non-atomic cases, generic test data, placeholder steps, source-rule oracles and traceability that is present only nominally.
7. Classify every supplied semantic-overlap diagnostic group. Accept a shared body only when it is a justified observable multi-obligation check; otherwise return a `duplication` finding and require consolidation. Different titles do not justify identical steps and final expected results.
8. Return the exact structured review contract requested by the runner. Do not write files; the runner renders human-readable findings.

## Decision Floor

- `accepted` requires every obligation to have a consistent verdict, every testable obligation to be correctly covered, every non-testable obligation to stay non-executable, and no `error` finding.
- `changes-required` requires at least one concrete finding linked to a supplied `ATOM-*` or `TC-*` unless it is a set-level scope finding.
- A deterministic gate marked failed, a draft hash mismatch, an unknown atom/test-case id or insufficient inline evidence blocks trusted sign-off.

## Runtime Boundary

No shell command is needed to review the inline payload. If the runtime environment has not already been confirmed, one exact `python scripts/probe_environment.py` command is allowed. Any other command or workspace read violates the prepared fast path.

## Selected source evidence

# Prepared Source Evidence

- package_id: `personal-data-static-properties-v6`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/personal-data-static-properties-shadow-v6-20260712/prepared-input/.personal-data-static-properties-v6.compiled-evidence.md`
- source_sha256: `e329e561e79b093cad2d2d0713cc411eae50a39dee36ec5cc4e1ef33f231c320`
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

- obligation: OBL-001 | property=SRC-002.P01 | source=`BSR 47`; XHTML row 57 | required=same-as-atom | planned=TC-PDSP-001 | status=covered

- atom: ATOM-001 | source=`SRC-002.P01`; XHTML row 57; DOCX table 6 row 4; BSR 47 | statement=Поле `Фамилия` отображается всегда. | coverage=covered

- plan: PLAN-001 | check=Открыть карточку заявки и проверить видимость поля `Фамилия`. | expected=Поле `Фамилия` отображается. | planned=TC-PDSP-001 | status=covered

## OBL-002

- obligation: OBL-002 | property=SRC-002.P02 | source=XHTML row 57; DOCX table 6 row 4 | required=same-as-atom | planned=TC-PDSP-002 | status=covered

- atom: ATOM-002 | source=`SRC-002.P02`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P02 | statement=Поле `Фамилия` является обязательным. | coverage=covered

- plan: PLAN-002 | check=Проверить признак обязательности поля `Фамилия`. | expected=Поле `Фамилия` обозначено обязательным. | planned=TC-PDSP-002 | status=covered

## OBL-003

- obligation: OBL-003 | property=SRC-002.P03 | source=XHTML row 57; DOCX table 6 row 4 | required=same-as-atom | planned=TC-PDSP-003 | status=covered

- atom: ATOM-003 | source=`SRC-002.P03`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P03 | statement=Поле `Фамилия` доступно для редактирования. | coverage=covered

- plan: PLAN-003 | check=Ввести синтетическое допустимое строковое значение `Тест` в поле `Фамилия`. | expected=Значение `Тест` отображается в поле `Фамилия`. | planned=TC-PDSP-003 | status=covered

## OBL-004

- obligation: OBL-004 | property=SRC-002.P04 | source=XHTML row 57; DOCX table 6 row 4 | required=Поле `Фамилия` является полем ввода текста. | planned=TC-PDSP-004 | status=covered

- atom: ATOM-004 | source=`SRC-002.P04`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P04 | statement=Поле `Фамилия` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-004 | check=Проверить тип элемента управления `Фамилия`. | expected=`Фамилия` доступна как поле ввода текста. | planned=TC-PDSP-004 | status=covered

## OBL-005

- obligation: OBL-005 | property=SRC-002.P05 | source=XHTML row 57; DOCX table 6 row 4 | required=Поле `Фамилия` принимает строковое значение. | planned=TC-PDSP-003 | status=covered

- atom: ATOM-005 | source=`SRC-002.P05`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P05 | statement=Тип значения поля `Фамилия` — строка. | coverage=covered

- plan: PLAN-003 | check=Ввести синтетическое допустимое строковое значение `Тест` в поле `Фамилия`. | expected=Значение `Тест` отображается в поле `Фамилия`. | planned=TC-PDSP-003 | status=covered

## OBL-006

- obligation: OBL-006 | property=SRC-003.P01 | source=`BSR 50`; XHTML row 58 | required=same-as-atom | planned=TC-PDSP-005 | status=covered

- atom: ATOM-006 | source=`SRC-003.P01`; XHTML row 58; DOCX table 6 row 5; BSR 50 | statement=Поле `Имя` отображается всегда. | coverage=covered

- plan: PLAN-006 | check=Открыть карточку заявки и проверить видимость поля `Имя`. | expected=Поле `Имя` отображается. | planned=TC-PDSP-005 | status=covered

## OBL-007

- obligation: OBL-007 | property=SRC-003.P02 | source=XHTML row 58; DOCX table 6 row 5 | required=same-as-atom | planned=TC-PDSP-006 | status=covered

- atom: ATOM-007 | source=`SRC-003.P02`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P02 | statement=Поле `Имя` является обязательным. | coverage=covered

- plan: PLAN-007 | check=Проверить признак обязательности поля `Имя`. | expected=Поле `Имя` обозначено обязательным. | planned=TC-PDSP-006 | status=covered

## OBL-008

- obligation: OBL-008 | property=SRC-003.P03 | source=XHTML row 58; DOCX table 6 row 5 | required=same-as-atom | planned=TC-PDSP-007 | status=covered

- atom: ATOM-008 | source=`SRC-003.P03`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P03 | statement=Поле `Имя` доступно для редактирования. | coverage=covered

- plan: PLAN-008 | check=Ввести синтетическое допустимое строковое значение `Тест` в поле `Имя`. | expected=Значение `Тест` отображается в поле `Имя`. | planned=TC-PDSP-007 | status=covered

## OBL-009

- obligation: OBL-009 | property=SRC-003.P04 | source=XHTML row 58; DOCX table 6 row 5 | required=Поле `Имя` является полем ввода текста. | planned=TC-PDSP-008 | status=covered

- atom: ATOM-009 | source=`SRC-003.P04`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P04 | statement=Поле `Имя` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-009 | check=Проверить тип элемента управления `Имя`. | expected=`Имя` доступно как поле ввода текста. | planned=TC-PDSP-008 | status=covered

## OBL-010

- obligation: OBL-010 | property=SRC-003.P05 | source=XHTML row 58; DOCX table 6 row 5 | required=Поле `Имя` принимает строковое значение. | planned=TC-PDSP-007 | status=covered

- atom: ATOM-010 | source=`SRC-003.P05`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P05 | statement=Тип значения поля `Имя` — строка. | coverage=covered

- plan: PLAN-008 | check=Ввести синтетическое допустимое строковое значение `Тест` в поле `Имя`. | expected=Значение `Тест` отображается в поле `Имя`. | planned=TC-PDSP-007 | status=covered

## OBL-011

- obligation: OBL-011 | property=SRC-004.P01 | source=`BSR 53`; XHTML row 59 | required=same-as-atom | planned=TC-PDSP-009 | status=covered

- atom: ATOM-011 | source=`SRC-004.P01`; XHTML row 59; DOCX table 6 row 6; BSR 53 | statement=Поле `Отчество` отображается всегда. | coverage=covered

- plan: PLAN-011 | check=Открыть карточку заявки и проверить видимость поля `Отчество`. | expected=Поле `Отчество` отображается. | planned=TC-PDSP-009 | status=covered

## OBL-012

- obligation: OBL-012 | property=SRC-004.P02 | source=XHTML row 59; DOCX table 6 row 6 | required=same-as-atom | planned=TC-PDSP-010 | status=covered

- atom: ATOM-012 | source=`SRC-004.P02`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P02 | statement=Поле `Отчество` не является обязательным. | coverage=covered

- plan: PLAN-012 | check=Проверить отсутствие признака обязательности поля `Отчество`. | expected=Поле `Отчество` не обозначено обязательным. | planned=TC-PDSP-010 | status=covered

## OBL-013

- obligation: OBL-013 | property=SRC-004.P03 | source=XHTML row 59; DOCX table 6 row 6 | required=same-as-atom | planned=TC-PDSP-011 | status=covered

- atom: ATOM-013 | source=`SRC-004.P03`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P03 | statement=Поле `Отчество` доступно для редактирования. | coverage=covered

- plan: PLAN-013 | check=Ввести синтетическое допустимое строковое значение `Тест` в поле `Отчество`. | expected=Значение `Тест` отображается в поле `Отчество`. | planned=TC-PDSP-011 | status=covered

## OBL-014

- obligation: OBL-014 | property=SRC-004.P04 | source=XHTML row 59; DOCX table 6 row 6 | required=Поле `Отчество` является полем ввода текста. | planned=TC-PDSP-012 | status=covered

- atom: ATOM-014 | source=`SRC-004.P04`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P04 | statement=Поле `Отчество` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-014 | check=Проверить тип элемента управления `Отчество`. | expected=`Отчество` доступно как поле ввода текста. | planned=TC-PDSP-012 | status=covered

## OBL-015

- obligation: OBL-015 | property=SRC-004.P05 | source=XHTML row 59; DOCX table 6 row 6 | required=Поле `Отчество` принимает строковое значение. | planned=TC-PDSP-011 | status=covered

- atom: ATOM-015 | source=`SRC-004.P05`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P05 | statement=Тип значения поля `Отчество` — строка. | coverage=covered

- plan: PLAN-013 | check=Ввести синтетическое допустимое строковое значение `Тест` в поле `Отчество`. | expected=Значение `Тест` отображается в поле `Отчество`. | planned=TC-PDSP-011 | status=covered

## Atomic obligations

```json
{
  "coverage_gaps": [],
  "digest": "09ce5e72b4ed212b81d8c18d116535af203b4635f9fb7d91a5c409a023aa4d51",
  "obligations": [
    {
      "atom_id": "ATOM-001",
      "atomic_statement": "Поле `Фамилия` отображается всегда.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-001",
      "observable_oracle": "Поле `Фамилия` отображается всегда.",
      "planned_test_case_id": "TC-PDSP-001",
      "source_refs": [
        "SRC-002.P01"
      ],
      "test_intent": "Открыть карточку заявки и проверить видимость поля `Фамилия`."
    },
    {
      "atom_id": "ATOM-002",
      "atomic_statement": "Поле `Фамилия` является обязательным.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-002",
      "observable_oracle": "Поле `Фамилия` является обязательным.",
      "planned_test_case_id": "TC-PDSP-002",
      "source_refs": [
        "SRC-002.P02"
      ],
      "test_intent": "Проверить признак обязательности поля `Фамилия`."
    },
    {
      "atom_id": "ATOM-003",
      "atomic_statement": "Поле `Фамилия` доступно для редактирования.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-003",
      "observable_oracle": "Поле `Фамилия` доступно для редактирования.",
      "planned_test_case_id": "TC-PDSP-003",
      "source_refs": [
        "SRC-002.P03"
      ],
      "test_intent": "Ввести синтетическое допустимое строковое значение `Тест` в поле `Фамилия`."
    },
    {
      "atom_id": "ATOM-004",
      "atomic_statement": "Поле `Фамилия` реализовано как поле ввода текста.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-004",
      "observable_oracle": "Поле `Фамилия` является полем ввода текста.",
      "planned_test_case_id": "TC-PDSP-004",
      "source_refs": [
        "SRC-002.P04"
      ],
      "test_intent": "Проверить тип элемента управления `Фамилия`."
    },
    {
      "atom_id": "ATOM-005",
      "atomic_statement": "Тип значения поля `Фамилия` — строка.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-005",
      "observable_oracle": "Поле `Фамилия` принимает строковое значение.",
      "planned_test_case_id": "TC-PDSP-003",
      "source_refs": [
        "SRC-002.P05"
      ],
      "test_intent": "Ввести синтетическое допустимое строковое значение `Тест` в поле `Фамилия`."
    },
    {
      "atom_id": "ATOM-006",
      "atomic_statement": "Поле `Имя` отображается всегда.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-006",
      "observable_oracle": "Поле `Имя` отображается всегда.",
      "planned_test_case_id": "TC-PDSP-005",
      "source_refs": [
        "SRC-003.P01"
      ],
      "test_intent": "Открыть карточку заявки и проверить видимость поля `Имя`."
    },
    {
      "atom_id": "ATOM-007",
      "atomic_statement": "Поле `Имя` является обязательным.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-007",
      "observable_oracle": "Поле `Имя` является обязательным.",
      "planned_test_case_id": "TC-PDSP-006",
      "source_refs": [
        "SRC-003.P02"
      ],
      "test_intent": "Проверить признак обязательности поля `Имя`."
    },
    {
      "atom_id": "ATOM-008",
      "atomic_statement": "Поле `Имя` доступно для редактирования.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-008",
      "observable_oracle": "Поле `Имя` доступно для редактирования.",
      "planned_test_case_id": "TC-PDSP-007",
      "source_refs": [
        "SRC-003.P03"
      ],
      "test_intent": "Ввести синтетическое допустимое строковое значение `Тест` в поле `Имя`."
    },
    {
      "atom_id": "ATOM-009",
      "atomic_statement": "Поле `Имя` реализовано как поле ввода текста.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-009",
      "observable_oracle": "Поле `Имя` является полем ввода текста.",
      "planned_test_case_id": "TC-PDSP-008",
      "source_refs": [
        "SRC-003.P04"
      ],
      "test_intent": "Проверить тип элемента управления `Имя`."
    },
    {
      "atom_id": "ATOM-010",
      "atomic_statement": "Тип значения поля `Имя` — строка.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-010",
      "observable_oracle": "Поле `Имя` принимает строковое значение.",
      "planned_test_case_id": "TC-PDSP-007",
      "source_refs": [
        "SRC-003.P05"
      ],
      "test_intent": "Ввести синтетическое допустимое строковое значение `Тест` в поле `Имя`."
    },
    {
      "atom_id": "ATOM-011",
      "atomic_statement": "Поле `Отчество` отображается всегда.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-011",
      "observable_oracle": "Поле `Отчество` отображается всегда.",
      "planned_test_case_id": "TC-PDSP-009",
      "source_refs": [
        "SRC-004.P01"
      ],
      "test_intent": "Открыть карточку заявки и проверить видимость поля `Отчество`."
    },
    {
      "atom_id": "ATOM-012",
      "atomic_statement": "Поле `Отчество` не является обязательным.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-012",
      "observable_oracle": "Поле `Отчество` не является обязательным.",
      "planned_test_case_id": "TC-PDSP-010",
      "source_refs": [
        "SRC-004.P02"
      ],
      "test_intent": "Проверить отсутствие признака обязательности поля `Отчество`."
    },
    {
      "atom_id": "ATOM-013",
      "atomic_statement": "Поле `Отчество` доступно для редактирования.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-013",
      "observable_oracle": "Поле `Отчество` доступно для редактирования.",
      "planned_test_case_id": "TC-PDSP-011",
      "source_refs": [
        "SRC-004.P03"
      ],
      "test_intent": "Ввести синтетическое допустимое строковое значение `Тест` в поле `Отчество`."
    },
    {
      "atom_id": "ATOM-014",
      "atomic_statement": "Поле `Отчество` реализовано как поле ввода текста.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-014",
      "observable_oracle": "Поле `Отчество` является полем ввода текста.",
      "planned_test_case_id": "TC-PDSP-012",
      "source_refs": [
        "SRC-004.P04"
      ],
      "test_intent": "Проверить тип элемента управления `Отчество`."
    },
    {
      "atom_id": "ATOM-015",
      "atomic_statement": "Тип значения поля `Отчество` — строка.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-015",
      "observable_oracle": "Поле `Отчество` принимает строковое значение.",
      "planned_test_case_id": "TC-PDSP-011",
      "source_refs": [
        "SRC-004.P05"
      ],
      "test_intent": "Ввести синтетическое допустимое строковое значение `Тест` в поле `Отчество`."
    }
  ],
  "package_id": "personal-data-static-properties-v6",
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
    "validator": "prepared-package-obligation-gate-v2",
    "findings_count": 0,
    "test_case_count": 12,
    "testable_obligations": 15,
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
      "OBL-015"
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
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\personal-data-static-properties-shadow-v6-20260712\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-PDSP-001

**Название:** Отображение поля «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-001; ATOM-001

### Предусловия

1. Доступна заявка, карточку которой можно открыть.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть карточку заявки.

### Итоговый ожидаемый результат

Поле `Фамилия` отображается.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-002

**Название:** Обязательность поля «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-002; ATOM-002

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Проверить признак обязательности поля `Фамилия`.

### Итоговый ожидаемый результат

Поле `Фамилия` обозначено обязательным.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-003

**Название:** Редактирование строкового значения в поле «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-003; ATOM-003; OBL-005; ATOM-005

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Строковое значение: `Тест`.

### Шаги

1. Ввести значение `Тест` в поле `Фамилия`.

### Итоговый ожидаемый результат

Поле `Фамилия` доступно для редактирования, введённое строковое значение `Тест` отображается в поле.

### Постусловия

- Не требуются: сохранение введённого значения не проверяется.

## TC-PDSP-004

**Название:** Тип элемента управления поля «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-004; ATOM-004

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Проверить тип элемента управления `Фамилия`.

### Итоговый ожидаемый результат

Поле `Фамилия` доступно как поле ввода текста.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-005

**Название:** Отображение поля «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-006; ATOM-006

### Предусловия

1. Доступна заявка, карточку которой можно открыть.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть карточку заявки.

### Итоговый ожидаемый результат

Поле `Имя` отображается.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-006

**Название:** Обязательность поля «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-007; ATOM-007

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Проверить признак обязательности поля `Имя`.

### Итоговый ожидаемый результат

Поле `Имя` обозначено обязательным.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-007

**Название:** Редактирование строкового значения в поле «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-008; ATOM-008; OBL-010; ATOM-010

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Строковое значение: `Тест`.

### Шаги

1. Ввести значение `Тест` в поле `Имя`.

### Итоговый ожидаемый результат

Поле `Имя` доступно для редактирования, введённое строковое значение `Тест` отображается в поле.

### Постусловия

- Не требуются: сохранение введённого значения не проверяется.

## TC-PDSP-008

**Название:** Тип элемента управления поля «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-009; ATOM-009

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Проверить тип элемента управления `Имя`.

### Итоговый ожидаемый результат

Поле `Имя` доступно как поле ввода текста.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-009

**Название:** Отображение поля «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-011; ATOM-011

### Предусловия

1. Доступна заявка, карточку которой можно открыть.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть карточку заявки.

### Итоговый ожидаемый результат

Поле `Отчество` отображается.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-010

**Название:** Необязательность поля «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-012; ATOM-012

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Проверить отсутствие признака обязательности поля `Отчество`.

### Итоговый ожидаемый результат

Поле `Отчество` не обозначено обязательным.

### Постусловия

- Не требуются: данные не изменялись.

## TC-PDSP-011

**Название:** Редактирование строкового значения в поле «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-013; ATOM-013; OBL-015; ATOM-015

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Строковое значение: `Тест`.

### Шаги

1. Ввести значение `Тест` в поле `Отчество`.

### Итоговый ожидаемый результат

Поле `Отчество` доступно для редактирования, введённое строковое значение `Тест` отображается в поле.

### Постусловия

- Не требуются: сохранение введённого значения не проверяется.

## TC-PDSP-012

**Название:** Тип элемента управления поля «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** personal-data-static-properties-v6
**Трассировка:** OBL-014; ATOM-014

### Предусловия

1. Открыта карточка заявки.

### Тестовые данные

- Не требуются.

### Шаги

1. Проверить тип элемента управления `Отчество`.

### Итоговый ожидаемый результат

Поле `Отчество` доступно как поле ввода текста.

### Постусловия

- Не требуются: данные не изменялись.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
