# Codex exec prepared reviewer fast path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

```json
{
  "package_version": 3,
  "package_id": "autofin-widget-selection-prepared-v3",
  "ft_slug": "AutoFin",
  "scope_slug": "iteration-smoke-widget-selection-types",
  "section_id": "3",
  "execution_profile": "simple-field-property",
  "unsupported_dimensions": [],
  "reviewed_draft_sha256": "1992ca5b48c3ac63bc8675adec54937d5c0ecd89e5c4ae0be9755f6c0daac495"
}
```

# Prepared Reviewer Runtime Profile

This is a technical execution profile inside the `ft-test-case-reviewer` phase. It introduces no new QA policy. The canonical full reviewer rubric remains authoritative for standard review; this projection contains only the checks applicable to an eligible immutable `simple-field-property` prepared package.

## Eligibility

Continue only when the embedded payload confirms:

- package version `3`;
- `execution_profile = simple-field-property`;
- empty `unsupported_dimensions`;
- an immutable draft hash;
- scope-local evidence and atomic obligations;
- passed structure, seed, obligation and writer evidence-access gates.

Legacy/unclassified, table-parity, numeric-boundary, integration/persistence, dependency/state and other unsupported packages return `route-to-standard-reviewer`. Do not open full project instructions or sources to bypass eligibility.

## Review Procedure

1. Use only the verified inline payload. Do not reread the full reviewer skill, instruction manifest, package files, references, prior cycles, production test cases or full sources.
2. Review every supplied obligation exactly once and bind the result to the supplied draft SHA-256.
3. For each `coverage_status = testable`, verify that linked `TC-*` steps and final expected result exercise the obligation condition and its concrete observable oracle.
4. For each `gap`, `unclear` or `not-applicable` obligation, verify that the draft does not claim executable coverage or invent the missing mechanism.
5. Reject invented screens, fields, literals, dictionaries, messages, statuses, UI reactions, API/DB effects, persistence or internal state.
6. Reject non-atomic cases, generic test data, placeholder steps, source-rule oracles and traceability that is present only nominally.
7. Return the exact structured review contract requested by the runner. Do not write files; the runner renders human-readable findings.

## Decision Floor

- `accepted` requires every obligation to have a consistent verdict, every testable obligation to be correctly covered, every non-testable obligation to stay non-executable, and no `error` finding.
- `changes-required` requires at least one concrete finding linked to a supplied `ATOM-*` or `TC-*` unless it is a set-level scope finding.
- A deterministic gate marked failed, a draft hash mismatch, an unknown atom/test-case id or insufficient inline evidence blocks trusted sign-off.

## Runtime Boundary

No shell command is needed to review the inline payload. If the runtime environment has not already been confirmed, one exact `python scripts/probe_environment.py` command is allowed. Any other command or workspace read violates the prepared fast path.

## Selected source evidence

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
    "test_case_count": 3,
    "testable_obligations": 3,
    "covered_obligations": [
      "ATOM-PREP-001",
      "ATOM-PREP-002",
      "ATOM-PREP-003"
    ]
  },
  {
    "gate": "writer-evidence-access",
    "passed": true,
    "validator": "prepared-evidence-access-gate-v1",
    "findings_count": 0,
    "commands_checked": 3,
    "fallback_authorizations": 0
  }
]
```

## Immutable writer draft

```markdown
# Тест-кейсы

**Статус набора:** unsigned draft  
**package_id:** `autofin-widget-selection-prepared-v3`  
**Scope:** `iteration-smoke-widget-selection-types`  
**Раздел ФТ:** `3`  
**targeted_source_fallback:** `not_used`

## Параметры runtime-фикстуры

- `FIXTURE-SINGLE`: зарегистрированная runtime-фикстура, предоставляющая исполнителю доступ к новому виджету типа «Список» в исходном состоянии; набор доступных значений виджета содержит как минимум два разных значения.
- `FIXTURE-MULTI`: зарегистрированная runtime-фикстура, предоставляющая исполнителю доступ к новому виджету типа «Список с множественным выбором» в исходном состоянии; набор доступных значений виджета содержит как минимум два разных значения.
- `VALUE-A`: первое доступное для выбора значение соответствующего виджета runtime-фикстуры.
- `VALUE-B`: второе доступное значение того же виджета, отличное от `VALUE-A`.

Конкретные экран, поле и значения определяются зарегистрированной runtime-фикстурой. Они не заданы выбранным scope и не подменяются придуманными литералами.

## TC-PREP-001

**Название:** Ограничение одиночного выбора в виджете типа «Список»  
**Тип:** позитивный  
**Приоритет:** средний  
**package_id:** `autofin-widget-selection-prepared-v3`  
**Трассировка:** `ATOM-PREP-001`  
**Источник:** `SRC-001`

### Предусловия

1. Исполнителю предоставлена `FIXTURE-SINGLE`.
2. Новый виджет типа «Список» из `FIXTURE-SINGLE` открыт в исходном состоянии.
3. В виджете доступны `VALUE-A` и `VALUE-B`.

### Тестовые данные

- Виджет: виджет типа «Список» из `FIXTURE-SINGLE`.
- Первое значение: `VALUE-A`.
- Второе значение: `VALUE-B`, отличное от `VALUE-A`.

### Шаги

1. Выбрать в виджете `VALUE-A`.
2. Выбрать в том же виджете `VALUE-B`.

### Итоговый ожидаемый результат

После последовательного выбора двух разных доступных значений виджет содержит ровно одно выбранное значение.

### Постусловия

- Проверка сохранения не выполняется: save-flow находится вне scope; runtime-фикстура освобождается по правилам тестового окружения.

## TC-PREP-002

**Название:** Одновременный выбор нескольких значений в виджете типа «Список с множественным выбором»  
**Тип:** позитивный  
**Приоритет:** средний  
**package_id:** `autofin-widget-selection-prepared-v3`  
**Трассировка:** `ATOM-PREP-002`  
**Источник:** `SRC-002`

### Предусловия

1. Исполнителю предоставлена `FIXTURE-MULTI`.
2. Новый виджет типа «Список с множественным выбором» из `FIXTURE-MULTI` открыт в исходном состоянии.
3. В виджете доступны `VALUE-A` и `VALUE-B`.

### Тестовые данные

- Виджет: виджет типа «Список с множественным выбором» из `FIXTURE-MULTI`.
- Первое значение: `VALUE-A`.
- Второе значение: `VALUE-B`, отличное от `VALUE-A`.

### Шаги

1. Выбрать в виджете `VALUE-A`.
2. Выбрать в том же виджете `VALUE-B`, не отменяя выбор `VALUE-A`.

### Итоговый ожидаемый результат

После выбора двух разных доступных значений оба значения одновременно отображаются как выбранные.

### Постусловия

- Проверка сохранения не выполняется: save-flow находится вне scope; runtime-фикстура освобождается по правилам тестового окружения.

## TC-PREP-003

**Название:** Исходное пустое состояние нового виджета  
**Тип:** позитивный  
**Приоритет:** средний  
**package_id:** `autofin-widget-selection-prepared-v3`  
**Трассировка:** `ATOM-PREP-003`  
**Источник:** `SRC-003`

### Предусловия

1. Исполнителю предоставлена `FIXTURE-SINGLE` или `FIXTURE-MULTI`.
2. Подготовлен новый виджет из выбранной runtime-фикстуры; со значением виджета ранее не взаимодействовали.

### Тестовые данные

- Проверяемый объект: новый виджет из выбранной runtime-фикстуры в исходном состоянии.

### Шаги

1. Открыть UI-контекст подготовленного нового виджета через runtime-фикстуру.
2. До взаимодействия с проверяемым виджетом осмотреть его текущее состояние.

### Итоговый ожидаемый результат

До первого взаимодействия с новым виджетом в нём отсутствует выбранное значение.

### Постусловия

- Состояние виджета не изменено; runtime-фикстура освобождается по правилам тестового окружения.

## Coverage gaps

### GAP-PREP-001

- **Статус:** non-blocking, executable TC не создаётся.
- **Трассировка:** `ATOM-PREP-004`, `ATOM-PREP-005`; источники `SRC-001`, `SRC-002`.
- **Пробел:** выбранный scope не идентифицирует конкретные справочники и не содержит независимого inventory oracle для проверки состава значений.
- **Обработка:** сохранить gap; добавить `DICT-*` inventory и отдельные source-origin тест-кейсы после подтверждения справочника и ожидаемого состава.

### GAP-PREP-002

- **Статус:** non-blocking, executable TC не создаётся.
- **Трассировка:** `ATOM-PREP-006`; источник `SRC-003`.
- **Пробел:** внутренняя интерпретация отсутствующего значения как `NULL` не имеет наблюдаемого артефакта в подтверждённом UI scope.
- **Обработка:** сохранить gap; для проверки внутреннего представления требуется отдельный API/DB/persistence scope.

## Не применимые классы проверок

- Негативные проверки не создаются: выбранные источники не определяют классы недопустимых значений и наблюдаемые негативные оракулы.
- Проверки обязательности не создаются: выбранные источники не задают обязательность, маркер обязательности или поведение пустого значения.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied atom, structured findings and a non-empty summary. Use only schema enum values. Do not emit commentary outside the final JSON object.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
