# Codex exec prepared writer fast path

The upstream package already applied the full source, scope and writer policy.
Use only the embedded Prepared Writer Runtime Profile below; do not load the full ft-test-case-writer skill or reread package/project reference files.
Do not read existing/generated test cases or earlier cycle artifacts as evidence.
Write a structurally complete unsigned draft first and only to `fts/AutoFin/work/review-cycles/codex-exec-prepared-architecture-benchmark-01-20260710/attempts/writer-r1/attempt-001/stage-output/draft.md`.
Do not write under a production test-cases directory and do not promote the draft.
Use registered full sources only for a single unresolved ATOM locator and record targeted_source_fallback.

<!-- PREPARED-STAGE-PAYLOAD:BEGIN -->
## Verified package metadata

```json
{
  "package_version": 3,
  "package_id": "autofin-widget-selection-prepared-v3",
  "ft_slug": "AutoFin",
  "scope_slug": "iteration-smoke-widget-selection-types",
  "section_id": "3",
  "execution_profile": "simple-field-property",
  "unsupported_dimensions": [],
  "fallback_policy": "targeted-only"
}
```

# Prepared Writer Runtime Profile

This is a technical execution profile inside the `ft-test-case-writer` phase. It contains no new QA policy. Upstream source/scope preparation already applied the full writer contracts when it built the immutable package; the fresh prepared writer executes only the allowlisted draft step.

## Eligibility

Continue only when the embedded payload confirms:

- package version `3`;
- `execution_profile = simple-field-property`;
- empty `unsupported_dimensions`;
- exact output path and attempt root;
- scope-local evidence;
- testable `ATOM-*` with observable oracles and explicit non-testable gaps;
- draft seed and runtime limits.

Legacy/unclassified, table-parity, numeric-boundary, integration/persistence and dependency/state packages return `route-to-standard-writer`. Do not open a full source to bypass eligibility.

## Fast Execution

1. Run the required environment probe only when no saved probe is confirmed.
2. Do not reread package files or general writer references: the runner embeds their verified prepared projection in the prompt.
3. Immediately replace the draft seed at the declared output path; do not postpone the first write for additional design.
4. Create executable `TC-*` only for `coverage_status = testable` and implement the provided `test_intent` and `observable_oracle`.
5. Never turn `gap`, `unclear` or `not-applicable` into executable coverage.
6. Do not invent screens, fields, dictionaries, values, UI reactions, setup, API/DB effects or persistence.
7. Do not create split design artifacts, matrices, workflow state, logs or next-stage prompts. Runner and upstream package own them.
8. Finish after the complete unsigned draft is written. Reviewer and promotion belong to the runner.

## Quality Floor

- one TC covers one check and one main observable result;
- every TC has parseable runtime metadata, reproducible preconditions, concrete permitted data, numbered steps, final expected result and postconditions;
- traceability names an existing testable `ATOM-*`;
- placeholders and invented literals are forbidden;
- production `test-cases/` stays unchanged;
- draft must differ from the seed and contain no seed sentinel.

## Targeted Fallback

A registered full source may be opened only for one explicitly unresolved `ATOM-*` when the prompt allows fallback. Emit `targeted_source_fallback` with reason, source path and exact locator. Never scan a document. Insufficient evidence blocks the stage.

# Prepared Stage Instructions

- package_id: `autofin-widget-selection-prepared-v3`
- role: `writer`
- scenario: `writer.session_prepared_initial_draft`
- output_path: `fts/AutoFin/work/review-cycles/codex-exec-prepared-architecture-benchmark-01-20260710/attempts/writer-r1/attempt-001/stage-output/draft.md`
- attempt_root: `fts/AutoFin/work/review-cycles/codex-exec-prepared-architecture-benchmark-01-20260710/attempts/writer-r1/attempt-001`
- sandbox_policy: `workspace_write`
- hard_timeout_seconds: `180`
- idle_timeout_seconds: `60`
- command_budget: `8`

## Fast Path

1. Use the runner-embedded verified projection; do not reread package files in the stage.
2. Do not rerun source locator, scope analyzer, source parity, DOCX extraction or PDF rendering.
3. Write a structurally complete minimum output before optional refinement.
4. Keep output and scratch inside attempt_root.
5. Do not read generated test cases, earlier cycles or canary artifacts as evidence.

## Targeted Fallback

Use a registered full source only when one named ATOM/source locator is unresolved by the package.
Record targeted_source_fallback with the reason, source path and exact locator.
Do not scan a complete document or use external scratch paths. Return blocked if evidence stays insufficient.

# Prepared Source Evidence

- package_id: `autofin-widget-selection-prepared-v3`

## Confirmed scope boundaries

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-contract.md`
- source_sha256: `ad3637a95782f72d4a410d49439ea1a2d74aedc75bd350a12324282554c60022`
- selectors: `## Что Входит В Scope, ## Что Не Входит В Scope, ## Внутренние Рабочие Пакеты`

## Что Входит В Scope

- Row `Список`: values come from a dictionary and only one value can be selected.
- Row `Список с множественным выбором`: values come from a dictionary and several values can be selected.
- Statement after the data type table: default widget values are absent and interpreted as `NULL`.

## Что Не Входит В Scope

- Other data type restrictions from section `3`.
- Screen-specific field visibility, requiredness, role model rules or dictionaries unless already present in selected rows.
- Save-flow, persistence, database storage, API or async behavior.
- Previous canary and generated test-case artifacts.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | UI widget value selection constraints | `SRC-001`, `SRC-002`, `SRC-003` | Single-select list, multi-select list, default empty/NULL widget state | `field-property coverage` | Canonical test cases and writer design artifacts for selected rows | `no` |

## Selected source rows

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-row-inventory.md`
- source_sha256: `766b9ae812bbe0acb59bdc8faa7c6e39e46d4b82abdba710abf7bd4983003b9d`
- selectors: `## Source Row Inventory`

## Source Row Inventory

| source_row_id | source_anchor | docx_anchor | row_type | source_text | bsr_codes | downstream_decision |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | XHTML table row `Список` | DOCX section `3`, table row `Список` | `data-type-restriction` | `Значения из справочника. Возможен выбор только одного значения` | none | `candidate_tc_required` |
| `SRC-002` | XHTML table row `Список с множественным выбором` | DOCX section `3`, table row `Список с множественным выбором` | `data-type-restriction` | `Значения из справочника. Возможен выбор нескольких значения` | none | `candidate_tc_required` |
| `SRC-003` | XHTML paragraph after data type table | DOCX section `3`, paragraph after data type table | `default-value-rule` | `По умолчанию значения в виджетах отсутствуют и интерпретируются как NULL` | none | `candidate_tc_required` |

## Parity decision and limitations

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-parity-check.md`
- source_sha256: `65e3c7df70694598c2cca004c09bb008395bbf8f26d43336d1805e2e433cb43d`
- selectors: `## Structure Parity, ## Limitations`

## Structure Parity

| item | DOCX | XHTML | PDF | decision |
| --- | --- | --- | --- | --- |
| Section `3 Ограничения` | found | found | found | `pass` |
| Data type restrictions table | found | found | found on page 5 | `pass` |
| Row `Список` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Row `Список с множественным выбором` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Default widget values paragraph | found | found | found on page 5 | `pass` |

## Limitations

- PDF structural cross-check is sufficient for section/block presence, but row-level extraction is not clean enough to use as primary source.
- No discrepancy between DOCX and XHTML was found for the selected source rows.

## Preserved scope risk

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-coverage-gaps.md`
- source_sha256: `12ad20415578f0363bfcf377c531874edb113c6123312d63dbc599d92980e65c`
- selectors: `RISK-001`

## Non-Blocking Risks To Preserve

| risk_id | source_ref | risk | downstream_handling |
| --- | --- | --- | --- |
| `RISK-001` | `SRC-001`..`SRC-003` | Selected section defines generic widget constraints, not a concrete screen field. | Writer/reviewer must not invent unsupported field names or dictionary values; fixture needs must be explicit. |

## Negative oracle boundary

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/negative-oracle-inventory.md`
- source_sha256: `f199143a0e668f05aad5e3f6b07938e198e753040a7a928bfdeb1ac3bd9ff8f6`
- selectors: `SO-NEG-NA-001`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `none` | Selected rows define positive selection capabilities and default empty state; they do not define invalid input classes. | `not_derived` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-negative-class-in-selected-source` | `none_required:covered` | `none_required` | `Do not create negative TC from this scope unless a later source adds invalid classes.` | `not_applicable` |

## Requiredness oracle boundary

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/requiredness-oracle-inventory.md`
- source_sha256: `a35f1c41817890c86c8e1666d3ffb717c3042ef2da20384c855a03f66260a729`
- selectors: `SO-REQ-NA-001`

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `not_present` | `none` | `not_applicable` | `not_applicable` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-requiredness-in-selected-source` | `none_required:covered` | `none_required` | `Do not create requiredness TC from this scope unless a later source adds requiredness.` | `not_applicable` |

## Mandatory AutoFin package notes

- source_path: `fts/AutoFin/AGENT-NOTES.md`
- source_sha256: `a79deafdfce98e3156dc4cacaf518031c248983c3dadaa1c72544903420bdca8`
- selectors: `# Package Notes: AutoFin`

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

## Atomic obligations

```json
{
  "coverage_gaps": [
    {
      "blocking": false,
      "gap_id": "GAP-PREP-001",
      "handling": "Сохранить как gap; добавить DICT-* inventory и отдельные source-origin test cases, когда справочник и ожидаемый состав будут подтверждены.",
      "problem": "Выбранный scope не идентифицирует конкретные справочники и не содержит независимого inventory oracle для сравнения состава значений.",
      "source_refs": [
        "SRC-001",
        "SRC-002"
      ]
    },
    {
      "blocking": false,
      "gap_id": "GAP-PREP-002",
      "handling": "Сохранить как gap и запросить отдельный API/DB/persistence scope, если внутреннее представление нужно проверять.",
      "problem": "Внутренняя интерпретация пустого значения как NULL не имеет наблюдаемого артефакта в подтверждённом UI scope.",
      "source_refs": [
        "SRC-003"
      ]
    }
  ],
  "digest": "dec36827caf04826c10da47584152331addf3b9b06da36c113aee53bbeabb30c",
  "obligations": [
    {
      "atomic_statement": "В виджете типа «Список» одновременно можно выбрать только одно значение.",
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Конкретный экран и значения являются параметрами runtime fixture; RISK-001 запрещает придумывать их.",
      "obligation_id": "ATOM-PREP-001",
      "observable_oracle": "После последовательного выбора двух разных доступных значений виджет содержит ровно одно выбранное значение.",
      "source_refs": [
        "SRC-001"
      ],
      "test_intent": "Проверить ограничение одиночного выбора без предположений о конкретном справочнике или поле."
    },
    {
      "atomic_statement": "В виджете типа «Список с множественным выбором» можно одновременно выбрать несколько значений.",
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Конкретный экран и значения являются параметрами runtime fixture; RISK-001 запрещает придумывать их.",
      "obligation_id": "ATOM-PREP-002",
      "observable_oracle": "После выбора двух разных доступных значений оба значения одновременно отображаются как выбранные.",
      "source_refs": [
        "SRC-002"
      ],
      "test_intent": "Проверить возможность множественного выбора без предположений о конкретном справочнике или поле."
    },
    {
      "atomic_statement": "По умолчанию значение виджета отсутствует.",
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Проверка не подтверждает внутреннее представление NULL.",
      "obligation_id": "ATOM-PREP-003",
      "observable_oracle": "До первого взаимодействия с новым виджетом в нём отсутствует выбранное значение.",
      "source_refs": [
        "SRC-003"
      ],
      "test_intent": "Проверить видимое начальное пустое состояние подходящего виджета."
    },
    {
      "atomic_statement": "Значения виджета типа «Список» происходят из справочника.",
      "coverage_status": "gap",
      "dictionary_refs": [],
      "gap_id": "GAP-PREP-001",
      "notes": "Selected scope does not identify the dictionary or its expected contents.",
      "obligation_id": "ATOM-PREP-004",
      "observable_oracle": "",
      "source_refs": [
        "SRC-001"
      ],
      "test_intent": "Не заявлять проверку происхождения значений без идентифицированного справочника и независимого inventory oracle."
    },
    {
      "atomic_statement": "Значения виджета типа «Список с множественным выбором» происходят из справочника.",
      "coverage_status": "gap",
      "dictionary_refs": [],
      "gap_id": "GAP-PREP-001",
      "notes": "Selected scope does not identify the dictionary or its expected contents.",
      "obligation_id": "ATOM-PREP-005",
      "observable_oracle": "",
      "source_refs": [
        "SRC-002"
      ],
      "test_intent": "Не заявлять проверку происхождения значений без идентифицированного справочника и независимого inventory oracle."
    },
    {
      "atomic_statement": "Отсутствующее значение интерпретируется системой как NULL.",
      "coverage_status": "gap",
      "dictionary_refs": [],
      "gap_id": "GAP-PREP-002",
      "notes": "Save-flow, persistence, database and API behavior are out of scope.",
      "obligation_id": "ATOM-PREP-006",
      "observable_oracle": "",
      "source_refs": [
        "SRC-003"
      ],
      "test_intent": "Не создавать UI-тест без наблюдаемого API, DB или иного persistence evidence."
    }
  ],
  "package_id": "autofin-widget-selection-prepared-v3",
  "package_version": 3
}
```

## Draft seed

Replace every seed sentinel and write the result to the declared output path.

```markdown
# Тест-кейсы

<!-- PREPARED-DRAFT-SEED: replace all [SEED:*] values before completion -->

## TC-PREP-001

**Название:** [SEED:title:ATOM-PREP-001]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** ATOM-PREP-001

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После последовательного выбора двух разных доступных значений виджет содержит ровно одно выбранное значение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-002

**Название:** [SEED:title:ATOM-PREP-002]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** ATOM-PREP-002

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После выбора двух разных доступных значений оба значения одновременно отображаются как выбранные.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-003

**Название:** [SEED:title:ATOM-PREP-003]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** ATOM-PREP-003

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] До первого взаимодействия с новым виджетом в нём отсутствует выбранное значение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```
<!-- PREPARED-STAGE-PAYLOAD:END -->

Exit only after the draft file is fully written. A chat response without the file is a failed stage.
