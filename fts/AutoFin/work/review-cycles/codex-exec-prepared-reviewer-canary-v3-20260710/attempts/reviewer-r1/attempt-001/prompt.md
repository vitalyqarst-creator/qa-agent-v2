# Codex exec prepared reviewer fast path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

```json
{
  "package_version": 2,
  "package_id": "autofin-widget-selection-prepared-v2",
  "ft_slug": "AutoFin",
  "scope_slug": "iteration-smoke-widget-selection-types",
  "section_id": "3",
  "execution_profile": "simple-field-property",
  "unsupported_dimensions": [],
  "reviewed_draft_sha256": "3f7fe6f82dac80384bf4eb54fdb764e59954fe06888375c83e5380f77c4048aa"
}
```

# Prepared Reviewer Runtime Profile

This is a technical execution profile inside the `ft-test-case-reviewer` phase. It introduces no new QA policy. The canonical full reviewer rubric remains authoritative for standard review; this projection contains only the checks applicable to an eligible immutable `simple-field-property` prepared package.

## Eligibility

Continue only when the embedded payload confirms:

- package version `2`;
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

- package_id: `autofin-widget-selection-prepared-v2`

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

## Atomic obligations

```json
{
  "coverage_gaps": [
    {
      "blocking": false,
      "gap_id": "GAP-PREP-001",
      "handling": "Сохранить как gap и запросить отдельный API/DB/persistence scope, если внутреннее представление нужно проверять.",
      "problem": "Внутренняя интерпретация пустого значения как NULL не имеет наблюдаемого артефакта в подтверждённом UI scope.",
      "source_refs": [
        "SRC-003"
      ]
    }
  ],
  "digest": "f3b031ddd4e3e468945532667e2283135f34e02cbb28a5fbaad4fb7697d3fd58",
  "obligations": [
    {
      "atomic_statement": "В виджете типа «Список» значения берутся из справочника и одновременно можно выбрать только одно значение.",
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
      "atomic_statement": "В виджете типа «Список с множественным выбором» значения берутся из справочника и можно выбрать несколько значений.",
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
      "atomic_statement": "Отсутствующее значение интерпретируется системой как NULL.",
      "coverage_status": "gap",
      "dictionary_refs": [],
      "gap_id": "GAP-PREP-001",
      "notes": "Save-flow, persistence, database and API behavior are out of scope.",
      "obligation_id": "ATOM-PREP-004",
      "observable_oracle": "",
      "source_refs": [
        "SRC-003"
      ],
      "test_intent": "Не создавать UI-тест без наблюдаемого API, DB или иного persistence evidence."
    }
  ],
  "package_id": "autofin-widget-selection-prepared-v2",
  "package_version": 2
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
    "validator": "prepared-package-obligation-gate-v1",
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

**Статус:** unsigned draft  
**package_id:** `autofin-widget-selection-prepared-v2`  
**Scope:** `3 / iteration-smoke-widget-selection-types`

## TC-PREP-001

**Название:** Ограничение одиночного выбора в виджете типа «Список»  
**Тип:** позитивный  
**Приоритет:** средний  
**package_id:** `autofin-widget-selection-prepared-v2`  
**Трассировка:** `ATOM-PREP-001`  
**Источник:** `SRC-001`

### Предусловия

1. Подготовлен runtime fixture, указывающий доступный экземпляр виджета типа «Список» и способ его открытия без предположения о конкретном экране или поле.
2. Для виджета в runtime fixture доступны как минимум два разных значения из связанного с ним справочника.
3. Исполнитель имеет доступ к runtime fixture и может выбирать доступные значения виджета.

### Тестовые данные

- `widget_fixture_single`: параметр runtime fixture для доступного виджета типа «Список».
- `dictionary_value_A`: первое доступное значение, фактически предоставленное справочником runtime fixture.
- `dictionary_value_B`: второе доступное значение, фактически предоставленное тем же справочником runtime fixture и отличающееся от `dictionary_value_A`.

### Шаги

1. Открыть экземпляр виджета, заданный параметром `widget_fixture_single`.
2. Открыть доступные для выбора значения виджета.
3. Выбрать `dictionary_value_A`.
4. Повторно открыть доступные для выбора значения виджета.
5. Выбрать `dictionary_value_B`.
6. Проверить текущее состояние выбранных значений виджета.

### Итоговый ожидаемый результат

После последовательного выбора двух разных доступных значений виджет содержит ровно одно выбранное значение.

### Постусловия

- В runtime fixture виджет находится в состоянии с одним выбранным значением; возврат fixture в исходное состояние выполняется штатным способом тестового контура, если он предусмотрен.

## TC-PREP-002

**Название:** Возможность множественного выбора в виджете типа «Список с множественным выбором»  
**Тип:** позитивный  
**Приоритет:** средний  
**package_id:** `autofin-widget-selection-prepared-v2`  
**Трассировка:** `ATOM-PREP-002`  
**Источник:** `SRC-002`

### Предусловия

1. Подготовлен runtime fixture, указывающий доступный экземпляр виджета типа «Список с множественным выбором» и способ его открытия без предположения о конкретном экране или поле.
2. Для виджета в runtime fixture доступны как минимум два разных значения из связанного с ним справочника.
3. Исполнитель имеет доступ к runtime fixture и может выбирать доступные значения виджета.

### Тестовые данные

- `widget_fixture_multi`: параметр runtime fixture для доступного виджета типа «Список с множественным выбором».
- `dictionary_value_A`: первое доступное значение, фактически предоставленное справочником runtime fixture.
- `dictionary_value_B`: второе доступное значение, фактически предоставленное тем же справочником runtime fixture и отличающееся от `dictionary_value_A`.

### Шаги

1. Открыть экземпляр виджета, заданный параметром `widget_fixture_multi`.
2. Открыть доступные для выбора значения виджета.
3. Выбрать `dictionary_value_A`.
4. Открыть доступные для выбора значения виджета повторно, если средство выбора закрылось после предыдущего действия.
5. Выбрать `dictionary_value_B`, не отменяя выбор `dictionary_value_A`.
6. Проверить текущее состояние выбранных значений виджета.

### Итоговый ожидаемый результат

После выбора двух разных доступных значений оба значения одновременно отображаются как выбранные.

### Постусловия

- В runtime fixture виджет находится в состоянии с двумя выбранными значениями; возврат fixture в исходное состояние выполняется штатным способом тестового контура, если он предусмотрен.

## TC-PREP-003

**Название:** Начальное пустое состояние нового виджета  
**Тип:** позитивный  
**Приоритет:** средний  
**package_id:** `autofin-widget-selection-prepared-v2`  
**Трассировка:** `ATOM-PREP-003`  
**Источник:** `SRC-003`

### Предусловия

1. Подготовлен runtime fixture, указывающий доступный новый экземпляр подходящего виджета и способ его открытия без предположения о конкретном экране или поле.
2. В экземпляре runtime fixture значение виджета ранее не выбиралось.
3. Исполнитель имеет доступ к runtime fixture.

### Тестовые данные

- `widget_fixture_empty`: параметр runtime fixture для нового экземпляра подходящего виджета, с которым ранее не выполнялось взаимодействие.

### Шаги

1. Открыть новый экземпляр runtime fixture, заданный параметром `widget_fixture_empty`.
2. Найти заданный виджет, не открывая средство выбора и не выбирая значение.
3. Проверить отображаемое состояние значения виджета.

### Итоговый ожидаемый результат

До первого взаимодействия с новым виджетом в нём отсутствует выбранное значение.

### Постусловия

- Значение виджета не изменено; отдельное восстановление состояния не требуется.

## Непокрываемое утверждение

- **gap_id:** `GAP-PREP-001`
- **Трассировка:** `ATOM-PREP-004`
- **Источник:** `SRC-003`
- **Статус покрытия:** `gap`; исполнимый тест-кейс не создаётся.
- **Причина:** внутренняя интерпретация отсутствующего значения как `NULL` не имеет наблюдаемого артефакта в подтверждённом UI scope; save-flow, API, БД и persistence находятся вне scope.
- **Дальнейшая обработка:** запросить отдельный API/DB/persistence scope, если требуется проверить внутреннее представление отсутствующего значения.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied atom, structured findings and a non-empty summary. Use only schema enum values. Do not emit commentary outside the final JSON object.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
