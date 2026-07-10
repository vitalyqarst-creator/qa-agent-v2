# Prepared Source Evidence

- package_id: `autofin-widget-selection-prepared-v1`

## Package-specific notes

- source_path: `fts/AutoFin/AGENT-NOTES.md`
- source_sha256: `a79deafdfce98e3156dc4cacaf518031c248983c3dadaa1c72544903420bdca8`

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

## Confirmed scope contract

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-contract.md`
- source_sha256: `ad3637a95782f72d4a410d49439ea1a2d74aedc75bd350a12324282554c60022`

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

## Selected source rows

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-row-inventory.md`
- source_sha256: `766b9ae812bbe0acb59bdc8faa7c6e39e46d4b82abdba710abf7bd4983003b9d`

# Source Row Inventory

## Context

- FT package: `AutoFin`
- Scope slug: `iteration-smoke-widget-selection-types`
- Main source: `source/FT4AutoFinFinal.xhtml`
- Authoritative source: `source/FT4AutoFinFinal.docx`
- Section: `3 Ограничения`
- Table/block: `Ограничения по типам данных`

## Source Row Inventory

| source_row_id | source_anchor | docx_anchor | row_type | source_text | bsr_codes | downstream_decision |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | XHTML table row `Список` | DOCX section `3`, table row `Список` | `data-type-restriction` | `Значения из справочника. Возможен выбор только одного значения` | none | `candidate_tc_required` |
| `SRC-002` | XHTML table row `Список с множественным выбором` | DOCX section `3`, table row `Список с множественным выбором` | `data-type-restriction` | `Значения из справочника. Возможен выбор нескольких значения` | none | `candidate_tc_required` |
| `SRC-003` | XHTML paragraph after data type table | DOCX section `3`, paragraph after data type table | `default-value-rule` | `По умолчанию значения в виджетах отсутствуют и интерпретируются как NULL` | none | `candidate_tc_required` |

## Extraction Notes

- XHTML extraction was performed with `bs4` against `source/FT4AutoFinFinal.xhtml`.
- DOCX extraction was performed with `test_case_agent.resolve_sections()` against `source/FT4AutoFinFinal.docx`.
- PDF page 5 confirms the selected block but is not used as row-level evidence because extracted text is wrapped and partially split.

## DOCX XHTML PDF parity decision

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-parity-check.md`
- source_sha256: `65e3c7df70694598c2cca004c09bb008395bbf8f26d43336d1805e2e433cb43d`

# Source Parity Check

## Context

- FT package: `AutoFin`
- Scope slug: `iteration-smoke-widget-selection-types`
- DOCX: `source/FT4AutoFinFinal.docx`
- XHTML: `source/FT4AutoFinFinal.xhtml`
- PDF: `source/FT4AutoFinFinal.pdf`
- Checked scope: section `3 Ограничения`, selected rows `SRC-001`..`SRC-003`

## Structure Parity

| item | DOCX | XHTML | PDF | decision |
| --- | --- | --- | --- | --- |
| Section `3 Ограничения` | found | found | found | `pass` |
| Data type restrictions table | found | found | found on page 5 | `pass` |
| Row `Список` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Row `Список с множественным выбором` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Default widget values paragraph | found | found | found on page 5 | `pass` |

## Requirement Code Parity

| source_row_id | DOCX BSR | XHTML BSR | PDF BSR | decision |
| --- | --- | --- | --- | --- |
| `SRC-001` | none | none | none | `no_code_expected` |
| `SRC-002` | none | none | none | `no_code_expected` |
| `SRC-003` | none | none | none | `no_code_expected` |

## Limitations

- PDF structural cross-check is sufficient for section/block presence, but row-level extraction is not clean enough to use as primary source.
- No discrepancy between DOCX and XHTML was found for the selected source rows.

## Scope gaps and preserved risk

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-coverage-gaps.md`
- source_sha256: `12ad20415578f0363bfcf377c531874edb113c6123312d63dbc599d92980e65c`

# Scope Coverage Gaps

## Context

- FT package: `AutoFin`
- Scope slug: `iteration-smoke-widget-selection-types`
- Selected source rows: `SRC-001`, `SRC-002`, `SRC-003`

## Gap Inventory

No blocking `GAP-*` items are raised before writer start.

## Non-Blocking Risks To Preserve

| risk_id | source_ref | risk | downstream_handling |
| --- | --- | --- | --- |
| `RISK-001` | `SRC-001`..`SRC-003` | Selected section defines generic widget constraints, not a concrete screen field. | Writer/reviewer must not invent unsupported field names or dictionary values; fixture needs must be explicit. |

## BA Questions

None before writer start.

## Negative oracle boundary

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/negative-oracle-inventory.md`
- source_sha256: `f199143a0e668f05aad5e3f6b07938e198e753040a7a928bfdeb1ac3bd9ff8f6`

# Negative Oracle Inventory

## Контекст

- `scope_slug`: `iteration-smoke-widget-selection-types`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `none` | Selected rows define positive selection capabilities and default empty state; they do not define invalid input classes. | `not_derived` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-negative-class-in-selected-source` | `none_required:covered` | `none_required` | `Do not create negative TC from this scope unless a later source adds invalid classes.` | `not_applicable` |

## Summary

- total_negative_obligations: `0`
- executable_tc: `0`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must not invent invalid values or UI reactions for the selected rows.
- If reviewer identifies a source-backed invalid class in the selected rows, it must be recorded as a new gap or candidate obligation before executable negative TC creation.

## Requiredness oracle boundary

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/requiredness-oracle-inventory.md`
- source_sha256: `a35f1c41817890c86c8e1666d3ffb717c3042ef2da20384c855a03f66260a729`

# Requiredness Oracle Inventory

## Контекст

- `scope_slug`: `iteration-smoke-widget-selection-types`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `not_present` | `none` | `not_applicable` | `not_applicable` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-requiredness-in-selected-source` | `none_required:covered` | `none_required` | `Do not create requiredness TC from this scope unless a later source adds requiredness.` | `not_applicable` |

## Summary

- total_requiredness_obligations: `0`
- executable_tc: `0`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must not treat selected positive/default widget constraints as field requiredness.
- Writer must not cover requiredness through valid value selection for this scope.
