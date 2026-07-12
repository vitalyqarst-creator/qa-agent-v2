# Codex exec prepared writer structured fast path

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
  "package_id": "personal-data-static-properties-v1",
  "ft_slug": "AutoFin",
  "scope_slug": "4.3-prepared-shadow-personal-data-static-properties",
  "section_id": "4.3",
  "execution_profile": "simple-field-property",
  "unsupported_dimensions": [],
  "fallback_policy": "targeted-only"
}
```

# Prepared Writer Runtime Profile

This is a technical execution profile inside the `ft-test-case-writer` phase. It contains no new QA policy. Upstream source/scope preparation already applied the full writer contracts when it built the immutable package; the fresh prepared writer executes only the allowlisted draft step.

## Eligibility

Continue only when the embedded payload confirms:

- package version `5`;
- `execution_profile = simple-field-property`;
- empty `unsupported_dimensions`;
- exact runner-owned output path and attempt root;
- scope-local evidence;
- testable `ATOM-*` with observable oracles and explicit non-testable gaps;
- draft seed and runtime limits.

Legacy/unclassified, table-parity, numeric-boundary, integration/persistence and dependency/state packages return `route-to-standard-writer`. Do not open a full source to bypass eligibility.

## Structured Fast Execution

1. Do not call the environment probe, shell or file tools. The runner already supplies the verified prepared projection and the structured mode has a zero-command budget.
2. Do not reread package files or general writer references: the runner embeds their verified prepared projection in the prompt.
3. Return one schema-constrained JSON object. For `draft-ready`, put the complete unsigned Markdown in `draft_markdown` and leave `blocking_reasons` empty. The runner alone atomically materializes `draft.md`.
4. Create executable `TC-*` only for `coverage_status = testable` and implement the provided `test_intent` and `observable_oracle`.
5. Never turn `gap`, `unclear` or `not-applicable` into executable coverage.
6. Do not invent screens, fields, dictionaries, values, UI reactions, setup, API/DB effects or persistence.
7. Do not create split design artifacts, matrices, workflow state, logs or next-stage prompts. Runner and upstream package own them.
8. Return `blocked-input` with an empty `draft_markdown` and precise `blocking_reasons` when inline evidence is insufficient. Reviewer and promotion belong to the runner.

## Explicit Legacy Workspace Mode

Use this mode only when the runner prompt explicitly selects `workspace`. The declared output is then stage-owned and absent at start: create it as the first file change from the inline seed, keep all writes under the declared stage-output root, use only an exact targeted fallback authorized by the prompt, and finish only after the complete draft is written. Never switch from structured mode to workspace mode inside a running attempt.

## Quality Floor

- one TC covers one check and one main observable result;
- every TC has parseable runtime metadata, reproducible preconditions, concrete permitted data, numbered steps, final expected result and postconditions;
- traceability names both the existing testable `OBL-*` and its linked `ATOM-*`;
- placeholders and invented literals are forbidden;
- the read-only writer performs no workspace mutation; production `test-cases/` stays unchanged;
- draft must differ from the seed and contain no seed sentinel.

## Targeted Fallback

Structured fast mode does not open registered full sources. Insufficient inline evidence returns `blocked-input` and routes to an explicitly selected standard writer. The legacy workspace mode retains targeted fallback only when the caller selects that mode explicitly; it is not a silent recovery path.

# Prepared Source Evidence

- package_id: `personal-data-static-properties-v1`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/personal-data-static-properties-shadow-20260712/prepared-input/.personal-data-static-properties-v1.compiled-evidence.md`
- source_sha256: `0a7ec8762836a08a63667bea5dbf44f4f27ef4c8f2b00ff982d43548d081e8c2`
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

- plan: PLAN-003 | check=Ввести допустимое текстовое значение в поле `Фамилия`. | expected=Введенное значение отображается в поле `Фамилия`. | planned=TC-PDSP-003 | status=covered

## OBL-004

- obligation: OBL-004 | property=SRC-002.P04 | source=XHTML row 57; DOCX table 6 row 4 | required=Поле `Фамилия` является полем ввода текста. | planned=TC-PDSP-004 | status=covered

- atom: ATOM-004 | source=`SRC-002.P04`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P04 | statement=Поле `Фамилия` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-004 | check=Проверить тип элемента управления `Фамилия`. | expected=`Фамилия` доступна как поле ввода текста. | planned=TC-PDSP-004 | status=covered

## OBL-005

- obligation: OBL-005 | property=SRC-002.P05 | source=XHTML row 57; DOCX table 6 row 4 | required=Поле `Фамилия` принимает строковое значение. | planned=TC-PDSP-005 | status=covered

- atom: ATOM-005 | source=`SRC-002.P05`; XHTML row 57; DOCX table 6 row 4; no_requirement_code:SRC-002.P05 | statement=Тип значения поля `Фамилия` — строка. | coverage=covered

- plan: PLAN-005 | check=Ввести строковое значение в поле `Фамилия`. | expected=Строковое значение отображается в поле. | planned=TC-PDSP-005 | status=covered

## OBL-006

- obligation: OBL-006 | property=SRC-003.P01 | source=`BSR 50`; XHTML row 58 | required=same-as-atom | planned=TC-PDSP-006 | status=covered

- atom: ATOM-006 | source=`SRC-003.P01`; XHTML row 58; DOCX table 6 row 5; BSR 50 | statement=Поле `Имя` отображается всегда. | coverage=covered

- plan: PLAN-006 | check=Открыть карточку заявки и проверить видимость поля `Имя`. | expected=Поле `Имя` отображается. | planned=TC-PDSP-006 | status=covered

## OBL-007

- obligation: OBL-007 | property=SRC-003.P02 | source=XHTML row 58; DOCX table 6 row 5 | required=same-as-atom | planned=TC-PDSP-007 | status=covered

- atom: ATOM-007 | source=`SRC-003.P02`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P02 | statement=Поле `Имя` является обязательным. | coverage=covered

- plan: PLAN-007 | check=Проверить признак обязательности поля `Имя`. | expected=Поле `Имя` обозначено обязательным. | planned=TC-PDSP-007 | status=covered

## OBL-008

- obligation: OBL-008 | property=SRC-003.P03 | source=XHTML row 58; DOCX table 6 row 5 | required=same-as-atom | planned=TC-PDSP-008 | status=covered

- atom: ATOM-008 | source=`SRC-003.P03`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P03 | statement=Поле `Имя` доступно для редактирования. | coverage=covered

- plan: PLAN-008 | check=Ввести допустимое текстовое значение в поле `Имя`. | expected=Введенное значение отображается в поле `Имя`. | planned=TC-PDSP-008 | status=covered

## OBL-009

- obligation: OBL-009 | property=SRC-003.P04 | source=XHTML row 58; DOCX table 6 row 5 | required=Поле `Имя` является полем ввода текста. | planned=TC-PDSP-009 | status=covered

- atom: ATOM-009 | source=`SRC-003.P04`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P04 | statement=Поле `Имя` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-009 | check=Проверить тип элемента управления `Имя`. | expected=`Имя` доступно как поле ввода текста. | planned=TC-PDSP-009 | status=covered

## OBL-010

- obligation: OBL-010 | property=SRC-003.P05 | source=XHTML row 58; DOCX table 6 row 5 | required=Поле `Имя` принимает строковое значение. | planned=TC-PDSP-010 | status=covered

- atom: ATOM-010 | source=`SRC-003.P05`; XHTML row 58; DOCX table 6 row 5; no_requirement_code:SRC-003.P05 | statement=Тип значения поля `Имя` — строка. | coverage=covered

- plan: PLAN-010 | check=Ввести строковое значение в поле `Имя`. | expected=Строковое значение отображается в поле. | planned=TC-PDSP-010 | status=covered

## OBL-011

- obligation: OBL-011 | property=SRC-004.P01 | source=`BSR 53`; XHTML row 59 | required=same-as-atom | planned=TC-PDSP-011 | status=covered

- atom: ATOM-011 | source=`SRC-004.P01`; XHTML row 59; DOCX table 6 row 6; BSR 53 | statement=Поле `Отчество` отображается всегда. | coverage=covered

- plan: PLAN-011 | check=Открыть карточку заявки и проверить видимость поля `Отчество`. | expected=Поле `Отчество` отображается. | planned=TC-PDSP-011 | status=covered

## OBL-012

- obligation: OBL-012 | property=SRC-004.P02 | source=XHTML row 59; DOCX table 6 row 6 | required=same-as-atom | planned=TC-PDSP-012 | status=covered

- atom: ATOM-012 | source=`SRC-004.P02`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P02 | statement=Поле `Отчество` не является обязательным. | coverage=covered

- plan: PLAN-012 | check=Проверить отсутствие признака обязательности поля `Отчество`. | expected=Поле `Отчество` не обозначено обязательным. | planned=TC-PDSP-012 | status=covered

## OBL-013

- obligation: OBL-013 | property=SRC-004.P03 | source=XHTML row 59; DOCX table 6 row 6 | required=same-as-atom | planned=TC-PDSP-013 | status=covered

- atom: ATOM-013 | source=`SRC-004.P03`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P03 | statement=Поле `Отчество` доступно для редактирования. | coverage=covered

- plan: PLAN-013 | check=Ввести допустимое текстовое значение в поле `Отчество`. | expected=Введенное значение отображается в поле `Отчество`. | planned=TC-PDSP-013 | status=covered

## OBL-014

- obligation: OBL-014 | property=SRC-004.P04 | source=XHTML row 59; DOCX table 6 row 6 | required=Поле `Отчество` является полем ввода текста. | planned=TC-PDSP-014 | status=covered

- atom: ATOM-014 | source=`SRC-004.P04`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P04 | statement=Поле `Отчество` реализовано как поле ввода текста. | coverage=covered

- plan: PLAN-014 | check=Проверить тип элемента управления `Отчество`. | expected=`Отчество` доступно как поле ввода текста. | planned=TC-PDSP-014 | status=covered

## OBL-015

- obligation: OBL-015 | property=SRC-004.P05 | source=XHTML row 59; DOCX table 6 row 6 | required=Поле `Отчество` принимает строковое значение. | planned=TC-PDSP-015 | status=covered

- atom: ATOM-015 | source=`SRC-004.P05`; XHTML row 59; DOCX table 6 row 6; no_requirement_code:SRC-004.P05 | statement=Тип значения поля `Отчество` — строка. | coverage=covered

- plan: PLAN-015 | check=Ввести строковое значение в поле `Отчество`. | expected=Строковое значение отображается в поле. | planned=TC-PDSP-015 | status=covered

## Atomic obligations

```json
{
  "coverage_gaps": [],
  "digest": "4df3eb9c69302ae44a5d82b2c4a2732308f0fad70d47a49159a23e1b36217a4b",
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
      "source_refs": [
        "SRC-002.P03"
      ],
      "test_intent": "Ввести допустимое текстовое значение в поле `Фамилия`."
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
      "source_refs": [
        "SRC-002.P05"
      ],
      "test_intent": "Ввести строковое значение в поле `Фамилия`."
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
      "source_refs": [
        "SRC-003.P03"
      ],
      "test_intent": "Ввести допустимое текстовое значение в поле `Имя`."
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
      "source_refs": [
        "SRC-003.P05"
      ],
      "test_intent": "Ввести строковое значение в поле `Имя`."
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
      "source_refs": [
        "SRC-004.P03"
      ],
      "test_intent": "Ввести допустимое текстовое значение в поле `Отчество`."
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
      "source_refs": [
        "SRC-004.P05"
      ],
      "test_intent": "Ввести строковое значение в поле `Отчество`."
    }
  ],
  "package_id": "personal-data-static-properties-v1",
  "package_version": 5
}
```

## Draft seed template (not an existing output file)

Return a complete draft based on this template; the runner writes it after validating the JSON contract.
Do not copy seed sentinels or placeholders into draft_markdown.

```markdown
# Тест-кейсы

<!-- PREPARED-DRAFT-SEED: replace all [SEED:*] values before completion -->

## TC-PREP-001

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

[SEED:observable oracle] Поле `Фамилия` отображается всегда.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-002

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

[SEED:observable oracle] Поле `Фамилия` является обязательным.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-003

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

[SEED:observable oracle] Поле `Фамилия` доступно для редактирования.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-004

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

[SEED:observable oracle] Поле `Фамилия` является полем ввода текста.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-005

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

[SEED:observable oracle] Поле `Фамилия` принимает строковое значение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-006

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

[SEED:observable oracle] Поле `Имя` отображается всегда.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-007

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

[SEED:observable oracle] Поле `Имя` является обязательным.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-008

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

[SEED:observable oracle] Поле `Имя` доступно для редактирования.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-009

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

[SEED:observable oracle] Поле `Имя` является полем ввода текста.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-010

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

[SEED:observable oracle] Поле `Имя` принимает строковое значение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-011

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

[SEED:observable oracle] Поле `Отчество` отображается всегда.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-012

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

[SEED:observable oracle] Поле `Отчество` не является обязательным.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-013

**Название:** [SEED:title:ATOM-013]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-013; ATOM-013

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Отчество` доступно для редактирования.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-014

**Название:** [SEED:title:ATOM-014]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-014; ATOM-014

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Отчество` является полем ввода текста.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-015

**Название:** [SEED:title:ATOM-015]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-015; ATOM-015

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Отчество` принимает строковое значение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```
<!-- PREPARED-STAGE-PAYLOAD:END -->

Return exactly one JSON object and no commentary outside it.
Use status=draft-ready with a complete draft_markdown and empty blocking_reasons, or status=blocked-input with empty draft_markdown and at least one blocking reason.
