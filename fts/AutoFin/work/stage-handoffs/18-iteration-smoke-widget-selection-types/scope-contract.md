# Scope Contract

## Контекст

- FT-пакет: `fts/AutoFin`
- Основной FT DOCX: `source/FT4AutoFinFinal.docx`
- Main FT XHTML: `source/FT4AutoFinFinal.xhtml`
- XHTML extraction notes: selected table rows extracted from XHTML; DOCX confirms meaning.
- PDF для structural cross-check: `есть`, `source/FT4AutoFinFinal.pdf`
- `AGENT-NOTES.md`: `есть`

## Scope Identity

- `scope_slug`: `iteration-smoke-widget-selection-types`
- Рабочее название: `Ограничения выбора значений для UI-виджетов типа список`
- `source_path`: `source/FT4AutoFinFinal.docx`, section `3 Ограничения`
- Режим получения: `agent-proposed-scope -> confirmed`

## Что Входит В Scope

- Row `Список`: values come from a dictionary and only one value can be selected.
- Row `Список с множественным выбором`: values come from a dictionary and several values can be selected.
- Statement after the data type table: default widget values are absent and interpreted as `NULL`.

## Что Не Входит В Scope

- Other data type restrictions from section `3`.
- Screen-specific field visibility, requiredness, role model rules or dictionaries unless already present in selected rows.
- Save-flow, persistence, database storage, API or async behavior.
- Previous canary and generated test-case artifacts.

## Разрешенные Источники

| source | type | usage_rule |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Authoritative meaning for selected section `3` rows. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Primary row extraction source. |
| `source/FT4AutoFinFinal.pdf` | `pdf` | Structural cross-check only. |
| `AGENT-NOTES.md` | `package-notes` | Package context only; does not add requirements. |

## Scope Complexity Assessment

| factor | value | risk | note |
| --- | --- | --- | --- |
| fields_or_blocks | `3 source rows/statements` | `low` | No large table scope. |
| conditional_dependencies | `none in selected rows` | `low` | Do not add screen-specific conditions. |
| validation_domains | `dictionary selection; default empty value` | `medium` | Writer must avoid unsupported dictionary contents. |
| action_flows | `select one value; select several values; inspect default value` | `low` | No save action required by selected rows. |
| integrations_api_async | `none` | `low` | No API/async assertions in selected rows. |
| status_lifecycle | `none` | `low` | Not lifecycle/status scope. |
| expected_gaps_or_unclear | `fixture field may be implementation-dependent` | `medium` | Keep fixture dependency explicit if no concrete field is selected by source. |

Complexity decision:

- `single_scope_with_internal_packages`
- Обоснование: selected scope has three atomic source statements and does not require external split.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | UI widget value selection constraints | `SRC-001`, `SRC-002`, `SRC-003` | Single-select list, multi-select list, default empty/NULL widget state | `field-property coverage` | Canonical test cases and writer design artifacts for selected rows | `no` |

## Целевые Артефакты

- Канонический файл тест-кейсов: `fts/AutoFin/test-cases/3-iteration-smoke-widget-selection-types.md`
- Handoff-папка: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/`
- Review-cycle папка: `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/`

## Условия Старта Следующего Этапа

- Iteration uses `scope-contract.md`, `scope-coverage-gaps.md`, `source-parity-check.md`, `source-row-inventory.md`, `prompt.scope-to-iteration.md` and `cycle-state.yaml`.
- Writer must run through the session-based review cycle, not in this session.
- Scope is ready for iteration only while `source-selection.md` confirms `xhtml_available: yes`.

## Ограничения И Правила Интерпретации

- Не расширять scope.
- Не выдумывать конкретные справочники, значения, поля, сообщения или сохранение данных вне selected source rows.
- Existing generated test cases and canary artifacts are not source of truth or templates.
