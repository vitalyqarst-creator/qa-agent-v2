# Codex exec prepared writer fast path

The upstream package already applied the full source, scope and writer policy.
Use only the embedded Prepared Writer Runtime Profile below; do not load the full ft-test-case-writer skill or reread package/project reference files.
Do not read existing/generated test cases or earlier cycle artifacts as evidence.
Write a structurally complete unsigned draft first and only to `fts/AutoFin/work/review-cycles/codex-exec-prepared-widget-selection-live-v11-20260711/attempts/writer-r1/attempt-001/stage-output/draft.md`.
That output file does not exist yet. Create it as your first file write; do not try to update it in place.
Do not write under a production test-cases directory and do not promote the draft.
Use registered full sources only for a single unresolved ATOM locator and record targeted_source_fallback.

<!-- PREPARED-STAGE-PAYLOAD:BEGIN -->
## Verified package metadata

```json
{
  "package_version": 4,
  "package_id": "autofin-widget-selection-expanded-v2",
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
3. The declared output file does not exist at stage start and is stage-owned. Create it as the first file write with `Add File` or an equivalent atomic create; use the inline draft seed only as a template. Do not use an update-only patch against the absent output and do not postpone the first write for additional design.
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

- package_id: `autofin-widget-selection-expanded-v2`
- role: `writer`
- scenario: `writer.session_prepared_initial_draft`
- output_path: `fts/AutoFin/work/review-cycles/prepared-autofin-widget-selection-expanded-v2-20260711/attempts/writer-r1/attempt-001/stage-output/draft.md`
- attempt_root: `fts/AutoFin/work/review-cycles/prepared-autofin-widget-selection-expanded-v2-20260711/attempts/writer-r1/attempt-001`
- sandbox_policy: `workspace_write`
- hard_timeout_seconds: `180`
- idle_timeout_seconds: `60`
- command_budget: `12`

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

- package_id: `autofin-widget-selection-expanded-v2`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-widget-selection-expanded-v2-20260711/prepared-input/.autofin-widget-selection-expanded-v2.compiled-evidence.md`
- source_sha256: `3dfdccc44280c3b6364532fed6b07ed47b9eefb12d18fc1977acdd37286d55e6`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## OBL-001

- obligation: OBL-001 | WP-01 | SRC-001 | ATOM-001 | dictionary-source | dictionary-provenance | Не заявлять состав справочника без идентифицированного source inventory. | SRC-001 | GAP-002 | gap | Точный справочник не задан.
- atom: ATOM-001 | SRC-001 | no_requirement_code:SRC-001 | Виджет типа `Список` использует значения из справочника. | gap | GAP-002 | Scope не идентифицирует конкретный справочник и полный inventory значений.

- plan: PD-001 | WP-01 | dictionary-source | SRC-001 | ATOM-001 | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | gap | dictionary-provenance | unidentified dictionary | none_required:gap | GAP-002 | GAP-002 | gap

## OBL-002

- obligation: OBL-002 | WP-01 | SRC-001 | ATOM-002 | selection-cardinality | single-selection | После второго выбора в виджете остаётся ровно одно выбранное значение. | SRC-001 | TC-WIDGET-SELECTION-TYPES-001 | covered | Проверка cardinality, не состава справочника.
- atom: ATOM-002 | SRC-001 | no_requirement_code:SRC-001 | В виджете типа `Список` возможно выбрать только одно значение. | covered | TC-WIDGET-SELECTION-TYPES-001 | Проверяется заменой первого выбранного значения вторым.

- plan: PD-002 | WP-01 | selection-cardinality | SRC-001 | ATOM-002 | Последовательно выбрать два разных доступных значения в single-select fixture. | positive | single-selection | two distinct fixture values | После второго выбора в виджете отображается ровно одно выбранное значение. | FT4AutoFinFinal; SRC-001 | TC-WIDGET-SELECTION-TYPES-001 | covered

## OBL-003

- obligation: OBL-003 | WP-01 | SRC-002 | ATOM-003 | dictionary-source | dictionary-provenance | Не заявлять состав справочника без идентифицированного source inventory. | SRC-002 | GAP-002 | gap | Точный справочник не задан.
- atom: ATOM-003 | SRC-002 | no_requirement_code:SRC-002 | Виджет типа `Список с множественным выбором` использует значения из справочника. | gap | GAP-002 | Scope не идентифицирует конкретный справочник и полный inventory значений.

- plan: PD-003 | WP-01 | dictionary-source | SRC-002 | ATOM-003 | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | gap | dictionary-provenance | unidentified dictionary | none_required:gap | GAP-002 | GAP-002 | gap

## OBL-004

- obligation: OBL-004 | WP-01 | SRC-002 | ATOM-004 | selection-cardinality | multiple-selection | Два выбранных значения одновременно отображаются в виджете. | SRC-002 | TC-WIDGET-SELECTION-TYPES-002 | covered | Минимальная репрезентативная проверка multiple selection.
- atom: ATOM-004 | SRC-002 | no_requirement_code:SRC-002 | В виджете типа `Список с множественным выбором` возможно выбрать несколько значений. | covered | TC-WIDGET-SELECTION-TYPES-002 | Проверяется одновременным отображением двух выбранных значений.

- plan: PD-004 | WP-01 | selection-cardinality | SRC-002 | ATOM-004 | Выбрать два разных доступных значения в multi-select fixture. | positive | multiple-selection | two distinct fixture values | Оба выбранных значения одновременно отображаются в виджете. | FT4AutoFinFinal; SRC-002 | TC-WIDGET-SELECTION-TYPES-002 | covered

## OBL-005

- obligation: OBL-005 | WP-01 | SRC-003 | ATOM-005 | default-value | visible-empty-default | До первого ввода в виджете нет выбранного или заполненного значения. | SRC-003 | TC-WIDGET-SELECTION-TYPES-003 | covered | Только UI-наблюдение.
- atom: ATOM-005 | SRC-003 | no_requirement_code:SRC-003 | По умолчанию значения в виджетах отсутствуют. | covered | TC-WIDGET-SELECTION-TYPES-003 | Покрывается UI-наблюдением отсутствия выбранного или заполненного значения.

- plan: PD-005 | WP-01 | default-value | SRC-003 | ATOM-005 | Проверить новый fixture-виджет до первого пользовательского ввода. | positive | empty-default | new untouched widget | В виджете отсутствует выбранное или заполненное значение. | FT4AutoFinFinal; SRC-003 | TC-WIDGET-SELECTION-TYPES-003 | covered

## OBL-006

- obligation: OBL-006 | WP-01 | SRC-003 | ATOM-006 | persistence | internal-null-interpretation | Не заявлять внутреннее `NULL` без API/DB/persistence evidence. | SRC-003 | GAP-001 | unclear | Внутреннее значение не наблюдается через UI.
- atom: ATOM-006 | SRC-003 | no_requirement_code:SRC-003 | Отсутствующие значения в виджетах интерпретируются как `NULL`. | unclear | GAP-001 | Внутренняя интерпретация `NULL` не имеет разрешенного UI-only observable artifact в данном scope.

- plan: PD-006 | WP-01 | persistence | SRC-003 | ATOM-006 | Не заявлять внутреннее представление `NULL` без API/DB/persistence evidence. | gap | internal-null | unobservable internal value | none_required:gap | GAP-001 | GAP-001 | unclear

## GAP-001

source_refs: SRC-003; ATOM-006
The selected sources state that absent widget values are interpreted as `NULL`, but the confirmed scope excludes persistence, database, API and async artifacts that could observe internal null semantics.
Preserve for reviewer and future scope expansion; do not assert internal `NULL` in UI-only TC.

## GAP-002

source_refs: SRC-001; SRC-002; ATOM-001; ATOM-003
The selected scope does not identify concrete dictionaries or provide an independent complete inventory for source-origin assertions.
Preserve dictionary provenance as a gap; cardinality remains executable with two distinct fixture values.

## Atomic obligations

```json
{
  "coverage_gaps": [
    {
      "blocking": false,
      "gap_id": "GAP-001",
      "handling": "Preserve for reviewer and future scope expansion; do not assert internal `NULL` in UI-only TC.",
      "problem": "The selected sources state that absent widget values are interpreted as `NULL`, but the confirmed scope excludes persistence, database, API and async artifacts that could observe internal null semantics.",
      "source_refs": [
        "SRC-003",
        "ATOM-006"
      ]
    },
    {
      "blocking": false,
      "gap_id": "GAP-002",
      "handling": "Preserve dictionary provenance as a gap; cardinality remains executable with two distinct fixture values.",
      "problem": "The selected scope does not identify concrete dictionaries or provide an independent complete inventory for source-origin assertions.",
      "source_refs": [
        "SRC-001",
        "SRC-002",
        "ATOM-001",
        "ATOM-003"
      ]
    }
  ],
  "digest": "09729d3abb38d0e94febccbd20344b319f5b3223a0bc03858bc607826810835b",
  "obligations": [
    {
      "atomic_statement": "Виджет типа `Список` использует значения из справочника.",
      "constraint_gap_ids": [],
      "coverage_status": "gap",
      "dictionary_refs": [],
      "gap_id": "GAP-002",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-001",
      "observable_oracle": "",
      "source_refs": [
        "SRC-001"
      ],
      "test_intent": "Не заявлять состав справочника без идентифицированного source inventory."
    },
    {
      "atomic_statement": "В виджете типа `Список` возможно выбрать только одно значение.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-002",
      "observable_oracle": "После второго выбора в виджете остаётся ровно одно выбранное значение.",
      "source_refs": [
        "SRC-001"
      ],
      "test_intent": "Последовательно выбрать два разных доступных значения в single-select fixture."
    },
    {
      "atomic_statement": "Виджет типа `Список с множественным выбором` использует значения из справочника.",
      "constraint_gap_ids": [],
      "coverage_status": "gap",
      "dictionary_refs": [],
      "gap_id": "GAP-002",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-003",
      "observable_oracle": "",
      "source_refs": [
        "SRC-002"
      ],
      "test_intent": "Не заявлять состав справочника без идентифицированного source inventory."
    },
    {
      "atomic_statement": "В виджете типа `Список с множественным выбором` возможно выбрать несколько значений.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-004",
      "observable_oracle": "Два выбранных значения одновременно отображаются в виджете.",
      "source_refs": [
        "SRC-002"
      ],
      "test_intent": "Выбрать два разных доступных значения в multi-select fixture."
    },
    {
      "atomic_statement": "По умолчанию значения в виджетах отсутствуют.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-005",
      "observable_oracle": "До первого ввода в виджете нет выбранного или заполненного значения.",
      "source_refs": [
        "SRC-003"
      ],
      "test_intent": "Проверить новый fixture-виджет до первого пользовательского ввода."
    },
    {
      "atomic_statement": "Отсутствующие значения в виджетах интерпретируются как `NULL`.",
      "constraint_gap_ids": [],
      "coverage_status": "unclear",
      "dictionary_refs": [],
      "gap_id": "GAP-001",
      "notes": "Compiled from workflow-state canonical design artifacts.",
      "obligation_id": "OBL-006",
      "observable_oracle": "",
      "source_refs": [
        "SRC-003"
      ],
      "test_intent": "Не заявлять внутреннее `NULL` без API/DB/persistence evidence."
    }
  ],
  "package_id": "autofin-widget-selection-expanded-v2",
  "package_version": 4
}
```

## Draft seed template (not an existing output file)

The declared output file does not exist at stage start. Create it as the first file write.
Use `Add File` or an equivalent atomic create; do not use an update-only patch against the absent output.
Use this inline seed only as a template and remove every seed sentinel in the created draft.

```markdown
# Тест-кейсы

<!-- PREPARED-DRAFT-SEED: replace all [SEED:*] values before completion -->

## TC-PREP-001

**Название:** [SEED:title:OBL-002]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-002

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После второго выбора в виджете остаётся ровно одно выбранное значение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-002

**Название:** [SEED:title:OBL-004]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-004

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Два выбранных значения одновременно отображаются в виджете.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-PREP-003

**Название:** [SEED:title:OBL-005]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-005

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] До первого ввода в виджете нет выбранного или заполненного значения.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
```
<!-- PREPARED-STAGE-PAYLOAD:END -->

Exit only after the draft file is fully written. A chat response without the file is a failed stage.
